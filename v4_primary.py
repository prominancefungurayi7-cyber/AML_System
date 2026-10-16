"""Post-commit V4 primary decision handoff.

The caller must commit the financial transaction and canonical event first and
mark its AI state ``pending_v4``. This module never invokes Stage13/Stage14.
"""
import v4_shadow
from alerts import create_alert_if_needed


class DecisionAlreadyApplied(ValueError):
    """Another post-commit caller has already finalized this payment's decision."""


def verify_database(connection):
    """Read existing local V4 schema/history gates without migration or writes."""
    from ml_v4.production_readiness import verify_identity, verify_history, verify_triggers
    from transaction_idempotency import require_schema
    from canonical_mobile_money_store import inspect
    from v4_history_attestation import SERVER_UUID
    import v4_retry
    verify_identity(connection, {'V4_READINESS_UUID': SERVER_UUID,
                                 'V4_READINESS_PRINCIPAL': 'aml@127.0.0.1'})
    require_schema(connection)
    v4_retry.require_schema(connection)
    if not inspect(connection)['exists']:
        raise RuntimeError('Canonical mobile-money schema unavailable')
    verify_triggers(connection)
    return verify_history(connection)


def verify_startup(connection_factory):
    """Validate the migrated local deployment without reseeding or running DDL."""
    import os
    import subprocess
    if os.environ.get('AML_RULE_ENGINE_ENABLED') != 'ON' or v4_shadow.enabled():
        raise RuntimeError('V4 primary requires independent rules ON and shadow OFF')
    connection = connection_factory()
    try:
        connection.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
        connection.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY')
        verify_database(connection)
    finally:
        connection.rollback()
        connection.close()
    subprocess.run([str(v4_shadow.PYTHON), '-B', '-c',
                    'from ml_v4.frozen_inference.service import FrozenModel; FrozenModel()'],
                   cwd=str(v4_shadow.ROOT), check=True, timeout=60, capture_output=True,
                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))


def _risk_level(score):
    if score >= 80:
        return 'critical'
    if score >= 60:
        return 'high_risk'
    if score >= 40:
        return 'suspicious'
    if score >= 25:
        return 'low'
    return 'normal'


def _decision(result, rule_score, prior_sar):
    """Use the frozen binary decision; preserve independent rule signals."""
    if result['status'] == 'success':
        suspicious = result['prediction'] == 1
        score = max(rule_score, 40 if suspicious else 0)
        level = _risk_level(score)
        confidence = (result['suspicious_probability'] if suspicious else
                      1.0 - result['suspicious_probability'])
        reason = ('V4 suspicious pattern' if suspicious else 'V4 normal pattern') + \
                 f" (probability: {result['suspicious_probability']:.2%}; threshold: 0.50)"
        return dict(risk_score=score, risk_level=level,
                    ai_risk_level=result['decision'], ai_confidence=confidence,
                    ai_reason=reason, description=reason,
                    sar_required=int(bool(prior_sar or suspicious or score >= 40)))
    # A committed payment cannot be undone here. Never classify a technical
    # failure as normal or infer a probability from fallback features.
    level = _risk_level(rule_score) if rule_score >= 40 else 'pending_review'
    reason = 'V4 inference unresolved: ' + result['error_code']
    return dict(risk_score=rule_score, risk_level=level,
                ai_risk_level='inference_error', ai_confidence=0.0,
                ai_reason=reason, description=reason,
                sar_required=int(bool(prior_sar or rule_score >= 40)))


def complete_committed(connection_factory, transaction_id, *, worker=None,
                       notify=None, processor=None, validator=None, attestor=None):
    """Route one committed canonical transaction to V4, then persist decision.

    The shadow result table is reused as the durable, deduplicated V4 inference
    record. It does not run a second AI model. Notifications follow the final
    decision commit. A repeated call does not repeat decision effects.
    """
    if type(transaction_id) is not int or transaction_id <= 0:
        raise ValueError('Invalid committed transaction ID')
    if v4_shadow.enabled():
        raise RuntimeError('V4 shadow mode must be OFF for primary decisions')
    check = connection_factory()
    try:
        row = check.execute('SELECT ai_risk_level FROM transactions WHERE id=?',
                            (transaction_id,)).fetchone()
        canonical = check.execute(
            'SELECT transaction_id FROM canonical_mobile_money_events WHERE transaction_id=?',
            (transaction_id,)).fetchone()
        if row is None or canonical is None:
            raise ValueError('Committed canonical transaction unavailable')
        if row['ai_risk_level'] != 'pending_v4':
            raise DecisionAlreadyApplied('Transaction is not awaiting a V4 primary decision')
    finally:
        check.rollback()
        check.close()

    # Production refreshes the existing verified history authority after the
    # financial commit and before the frozen worker opens its own snapshot.
    expected_revision = None
    if attestor is not None or (worker is None and processor is None):
        from v4_history_attestation import refresh_committed
        expected_revision = (attestor or refresh_committed)(
            connection_factory, transaction_id)
    process_result = processor or v4_shadow.process
    validate_result = validator or v4_shadow.validate
    kwargs = {'runner': worker}
    if expected_revision is not None and processor is None:
        kwargs['expected_source_revision'] = expected_revision
    result = process_result(connection_factory, transaction_id,
                            lambda _payload: None, **kwargs)
    if result is None:
        return {'status': 'pending', 'transaction_id': transaction_id}
    result = validate_result(result, transaction_id)
    connection = connection_factory()
    try:
        row = connection.execute(
            'SELECT sender_account,timestamp,rule_score,rules_triggered,sar_required,'
            'ai_risk_level FROM transactions WHERE id=?', (transaction_id,)).fetchone()
        if row is None:
            raise ValueError('V4 primary decision state changed')
        if row['ai_risk_level'] != 'pending_v4':
            raise DecisionAlreadyApplied('V4 primary decision state changed')
        decision = _decision(result, int(row['rule_score'] or 0), row['sar_required'])
        updated = connection.execute(
            'UPDATE transactions SET risk_score=?,risk_level=?,ai_risk_level=?,'
            'ai_confidence=?,ai_reason=?,description=?,sar_required=? '
            "WHERE id=? AND ai_risk_level='pending_v4'",
            (decision['risk_score'], decision['risk_level'],
             decision['ai_risk_level'], decision['ai_confidence'],
             decision['ai_reason'], decision['description'],
             decision['sar_required'], transaction_id))
        if updated.rowcount != 1:
            raise DecisionAlreadyApplied('Concurrent V4 decision already applied')
        alert_id = create_alert_if_needed(
            connection, transaction_id, row['sender_account'],
            decision['risk_score'], decision['risk_level'],
            decision['ai_reason'], row['rules_triggered'] or '[]', row['timestamp'],
            database_url=(getattr(connection, 'engine', None) or
                          getattr(getattr(connection, 'db', None), 'engine')) + '://')
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    output = {'status': result['status'], 'transaction_id': transaction_id,
              'decision': decision['ai_risk_level'], 'risk_level': decision['risk_level'],
              'alert_id': alert_id, 'error_code': result.get('error_code')}
    if notify is not None:
        try:
            notify(output)
        except Exception:
            pass
    return output
