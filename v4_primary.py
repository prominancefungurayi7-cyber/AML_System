"""Post-commit V4 primary decision handoff.

The caller must commit the financial transaction and canonical event first and
mark its AI state ``pending_v4``. This module never invokes Stage13/Stage14.
"""
import v4_shadow
from queue import Queue, Empty, Full
import threading
from alerts import create_alert_if_needed

# Pending database rows remain the durable queue across restarts. This bounded
# hint gives interactive payments priority over a large simulation backlog.
_interactive = Queue(maxsize=128)
_generated = Queue(maxsize=5000)
_wake = threading.Event()


def enqueue_committed(transaction_id):
    try:
        _interactive.put_nowait(transaction_id)
    except Full:
        pass
    _wake.set()


def next_interactive():
    try:
        return _interactive.get_nowait()
    except Empty:
        return None


def enqueue_generated(transaction_ids):
    for transaction_id in transaction_ids:
        try:
            _generated.put_nowait(transaction_id)
        except Full:
            break  # Database pending rows remain the durable recovery queue.
    _wake.set()


def next_generated():
    try:
        return _generated.get_nowait()
    except Empty:
        return None


def wait_for_work(seconds):
    _wake.wait(seconds)
    _wake.clear()


SCORING_POLICY = {'ai_weight': 0.70, 'rule_weight': 0.30}
SCORING_POLICY_VERSION = 'v4.risk.ai70.rules30.v1'
_REVIEW_LEVELS = ('normal', 'low', 'suspicious', 'high_risk', 'critical')


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
    """Weight V4 probability most heavily and retain independent review flags."""
    if result['status'] == 'success':
        suspicious = result['prediction'] == 1
        model_risk = 100.0 * result['suspicious_probability']
        score = round(SCORING_POLICY['ai_weight'] * model_risk +
                      SCORING_POLICY['rule_weight'] * rule_score, 2)
        level = max((_risk_level(score), _risk_level(rule_score),
                     'suspicious' if suspicious else 'normal'),
                    key=_REVIEW_LEVELS.index)
        confidence = (result['suspicious_probability'] if suspicious else
                      1.0 - result['suspicious_probability'])
        reason = ('V4 suspicious pattern' if suspicious else 'V4 normal pattern') + \
                 f" (probability: {result['suspicious_probability']:.2%})"
        description = (
            f'Operational risk index {score:.2f}/100: 70% V4 suspicious-probability '
            f'risk ({model_risk:.2f}/100) + 30% independent rule score '
            f'({rule_score:.2f}/100). Policy: {SCORING_POLICY_VERSION}. '
            f'{reason}. Review level: {level}; independent AI or rule findings '
            'may require review regardless of the combined index.')
        return dict(risk_score=score, risk_level=level,
                    ai_risk_level=result['decision'], ai_confidence=confidence,
                    ai_reason=reason, description=description,
                    sar_required=int(bool(prior_sar or suspicious or
                                          rule_score >= 40 or score >= 40)))
    # A committed payment cannot be undone here. Never classify a technical
    # failure as normal or infer a probability from fallback features.
    level = _risk_level(rule_score) if rule_score >= 40 else 'pending_review'
    reason = 'V4 inference unresolved: ' + result['error_code']
    return dict(risk_score=rule_score, risk_level=level,
                ai_risk_level='inference_error', ai_confidence=0.0,
                ai_reason=reason,
                description=reason + '. The recorded score is rule-only; no weighted AI result is available.',
                sar_required=int(bool(prior_sar or rule_score >= 40)))


def _persist_alert(connection, transaction_id, row, decision):
    """Synchronise assessment fields while preserving an existing case's work."""
    existing = connection.execute('SELECT id FROM alerts WHERE transaction_id=?',
                                  (transaction_id,)).fetchone()
    rules = row['rules_triggered'] or '[]'
    if existing is not None:
        connection.execute(
            'UPDATE alerts SET risk_score=?,risk_level=?,reason=?,rules_triggered=? WHERE id=?',
            (decision['risk_score'], decision['risk_level'], decision['description'],
             rules, existing['id']))
        return existing['id']
    return create_alert_if_needed(
        connection, transaction_id, row['sender_account'], decision['risk_score'],
        decision['risk_level'], decision['description'], rules, row['timestamp'],
        database_url=(getattr(connection, 'engine', None) or
                      getattr(getattr(connection, 'db', None), 'engine')) + '://')


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
        alert_id = _persist_alert(connection, transaction_id, row, decision)
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
