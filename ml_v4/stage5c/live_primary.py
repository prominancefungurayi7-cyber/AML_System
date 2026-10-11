"""Guarded disposable-only V4-primary Flask exercise; run through run_live_primary.ps1."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from time import perf_counter
from uuid import uuid4

from canonical_history import freshness
from canonical_history_store import assess
from ml_v4.stage4sa import coordinator
from ml_v4.stage4sa.harness import load_test_application
from ml_v4.test_binding import v1
from transaction_idempotency import require_schema

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'ml_v4/evidence/stage5c/live_primary.json'
REVIEW = ROOT / 'ml_v4/evidence/stage5c/interrupted_review.json'
MODEL = ROOT / 'ml_v4/development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib'
MODEL_SHA = '555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18'
UUID = 'd441b7bb-43f6-11f1-a2d8-0a0027000005'


def _count(db, table):
    return db.execute('SELECT COUNT(*) AS n FROM ' + table).fetchone()['n']


def _history(db):
    scope, current, previous = assess(db, v1.SCOPE)
    state = freshness(scope, current, previous)
    if state != 'COMPLETE_VERIFIED' or current['issues']:
        raise RuntimeError('History authority is stale or incomplete')
    return state


def _history_diagnosis(db):
    """Read-only assessment; expose staleness without granting inference authority."""
    scope, current, previous = assess(db, v1.SCOPE)
    return {
        'freshness': freshness(scope, current, previous),
        'current_status': current['status'],
        'current_issues': current['issues'],
        'current_source_revision': current['source_revision'],
        'current_canonical_event_ids': current['canonical_event_ids'],
        'current_observed_through_key': current['observed_through_key'],
        'attested_source_revision': previous['source_revision'] if previous else None,
        'attestation_id': previous['attestation_id'] if previous else None,
        'attestation_sequence': previous['sequence'] if previous else None,
        'attested_status': previous['status'] if previous else None,
        'scope_revision': scope['revision'],
    }


def preflight(*, allow_stale=False, attestation_review=False):
    execution_binding = (os.environ.get('STAGE5C_EXECUTE') == 'YES' and
                         os.environ.get('AML_PRIMARY_MODEL') == 'V4')
    review_binding = (attestation_review and allow_stale and
                      os.environ.get('STAGE5C_ATTEST_EXECUTE') == 'YES' and
                      not os.environ.get('STAGE5C_EXECUTE') and
                      not os.environ.get('AML_PRIMARY_MODEL'))
    if (not (review_binding if attestation_review else execution_binding) or
            os.environ.get('V4_SHADOW_ENABLED', 'OFF') == 'ON' or
            os.environ.get('V4_STAGE4T_EXPECTED_SERVER_UUID') != UUID or
            os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL')):
        raise RuntimeError('Isolated execution environment not pinned')
    parsed = v1.config(os.environ.get('V4_STAGE4T_TEST_DB_URL', ''))
    if parsed.hostname != '127.0.0.1' or parsed.port != 3306:
        raise RuntimeError('Only local disposable MySQL is allowed')
    if hashlib.sha256(MODEL.read_bytes()).hexdigest() != MODEL_SHA:
        raise RuntimeError('Frozen V4 model hash mismatch')
    if hashlib.sha256(coordinator.WORKER.read_bytes()).hexdigest() != coordinator.WORKER_SHA256:
        raise RuntimeError('Test worker hash mismatch')
    authority = v1.load_authority()
    if authority['server_uuid'] != UUID:
        raise RuntimeError('Authority server UUID mismatch')
    db = v1.connection(authority)
    try:
        observed = v1.identity(db, UUID)
        v1._triggers(db)
        v1._boundary(db, authority)
        history = _history_diagnosis(db)
        state = history['freshness']
        if not allow_stale and (state != 'COMPLETE_VERIFIED' or history['current_issues']):
            raise RuntimeError('History authority is stale or incomplete')
        require_schema(db)
        result_columns = [r['Field'] for r in db.execute(
            'SHOW COLUMNS FROM v4_shadow_results').fetchall()]
        if result_columns != ['transaction_id', 'model_version', 'feature_version',
                              'inference_id', 'status', 'prediction',
                              'suspicious_probability', 'threshold', 'decision',
                              'error_code', 'body', 'created_at']:
            raise RuntimeError('V4 result table schema mismatch')
        for tx in (1, 2, 3, 4):
            if db.execute('SELECT id FROM transactions WHERE id=?', (tx,)).fetchone() is None:
                raise RuntimeError('Earlier disposable transaction missing')
            if _count_for(db, 'canonical_mobile_money_events', tx) != 1 or _count_for(db, 'cmm_source_changes', tx) != 2:
                raise RuntimeError('Earlier canonical/capture history missing')
            stored = db.execute('SELECT body FROM v4_shadow_results WHERE transaction_id=?', (tx,)).fetchone()
            if stored is None or coordinator.validate_test(json.loads(stored['body']), tx)['status'] != 'success':
                raise RuntimeError('Earlier V4 result missing or invalid')
        counts = {table: _count(db, table) for table in
                  ('transactions', 'canonical_mobile_money_events', 'cmm_source_changes',
                   'v4_shadow_results', 'alerts', 'sar_reports', 'ctr_reports')}
        if (counts['transactions'] < 4 or counts['canonical_mobile_money_events'] < 4 or
                counts['cmm_source_changes'] < 8 or counts['v4_shadow_results'] < 4):
            raise RuntimeError('Disposable baseline shrank')
        return {'identity': observed, 'history': state,
                'history_assessment': history, 'counts': counts,
                'model_sha256': MODEL_SHA, 'idempotency_schema': 'verified'}
    finally:
        db.rollback()
        db.close()


def _count_for(db, table, tx):
    return db.execute('SELECT COUNT(*) AS n FROM ' + table + ' WHERE transaction_id=?',
                      (tx,)).fetchone()['n']


def inspect_prior(*, attestation_review=False):
    """Read only: reconcile every known Stage5C fixture group before new posts."""
    baseline = preflight(allow_stale=True, attestation_review=attestation_review)
    db = v1.connection()
    try:
        ctr_columns = [r['Field'] for r in db.execute('SHOW COLUMNS FROM ctr_reports').fetchall()]
        required = {'id', 'reference_number', 'account_number', 'total_amount',
                    'transaction_count', 'filing_date', 'status', 'filed_by', 'filed_at'}
        if not required.issubset(ctr_columns) or 'transaction_id' in ctr_columns:
            raise RuntimeError('CTR schema differs from account/date report contract')
        users = [dict(row) for row in db.execute(
            "SELECT id,account_number,role,balance FROM users WHERE account_number LIKE 'S5C%' "
            'ORDER BY account_number').fetchall()]
        if any(not re.fullmatch(r'S5C[0-9a-f]{12}[01S]', row['account_number']) for row in users):
            raise RuntimeError('Unknown Stage5C account naming; manual review required')
        groups = {}
        for row in users:
            groups.setdefault(row['account_number'][3:15], {})[row['account_number'][-1]] = row
        reviewed = []
        for run_id, members in sorted(groups.items()):
            if set(members) != {'0', '1', 'S'}:
                raise RuntimeError('Incomplete Stage5C fixture identity: ' + run_id)
            wallets = {members['0']['account_number'], members['1']['account_number']}
            tx_rows = [dict(row) for row in db.execute(
                'SELECT id,sender_account,receiver_account,amount,transaction_type,'
                'client_request_id,ai_risk_level,risk_level,ctr_required,sar_required '
                'FROM transactions WHERE sender_account IN (?,?) OR receiver_account IN (?,?) '
                'ORDER BY id', tuple(wallets) + tuple(wallets)).fetchall()]
            expected = {wallet: 20000.0 for wallet in wallets}
            tx_details = []
            for row in tx_rows:
                tx = row['id']
                if row['sender_account'] != members['0']['account_number'] or not row['client_request_id']:
                    raise RuntimeError('Unexpected transaction in Stage5C fixture group')
                operations = [r['operation'] for r in db.execute(
                    'SELECT operation FROM cmm_source_changes WHERE transaction_id=? '
                    'ORDER BY change_id', (tx,)).fetchall()]
                if (_count_for(db, 'canonical_mobile_money_events', tx) != 1 or
                        operations != ['SOURCE_INSERT', 'CANONICAL_INSERT']):
                    raise RuntimeError('Stage5C canonical/capture record incomplete')
                stored = db.execute('SELECT body FROM v4_shadow_results WHERE transaction_id=?',
                                    (tx,)).fetchone()
                if stored is None:
                    raise RuntimeError('Stage5C V4 result missing')
                result = coordinator.validate_test(json.loads(stored['body']), tx)
                if result['status'] not in ('success', 'inference_error') or row['ai_risk_level'] != result['decision']:
                    raise RuntimeError('Stage5C AML decision unresolved')
                amount = float(row['amount'])
                if row['transaction_type'] == 'transfer' and row['receiver_account'] in wallets:
                    expected[row['sender_account']] -= amount
                    expected[row['receiver_account']] += amount
                elif row['transaction_type'] == 'deposit' and row['receiver_account'] == row['sender_account']:
                    expected[row['sender_account']] += amount
                elif row['transaction_type'] == 'withdraw' and row['receiver_account'] == row['sender_account']:
                    expected[row['sender_account']] -= amount
                else:
                    raise RuntimeError('Unexpected Stage5C payment type')
                tx_details.append({'transaction_id': tx, 'request_id': row['client_request_id'],
                                   'type': row['transaction_type'], 'amount': amount,
                                   'ai_risk_level': row['ai_risk_level'],
                                   'prediction': result['prediction'],
                                   'probability': result['suspicious_probability'],
                                   'shadow_status': result['status'],
                                   'alerts': _count_for(db, 'alerts', tx),
                                   'canonical_rows': 1,
                                   'capture_operations': operations})
            for wallet in wallets:
                if abs(float(members[wallet[-1]]['balance']) - expected[wallet]) > .001:
                    raise RuntimeError('Stage5C wallet balance differs from committed payments')
            reviewed.append({'fixture_run': run_id, 'transactions': tx_details,
                             'wallet_balances': {wallet: float(members[wallet[-1]]['balance'])
                                                 for wallet in sorted(wallets)}})
        state = ('RECONCILED' if baseline['history'] == 'COMPLETE_VERIFIED' and
                 not baseline['history_assessment']['current_issues'] else 'UNRESOLVED')
        result = {'status': state, 'baseline': baseline, 'ctr_columns': ctr_columns,
                  'prior_runs': reviewed}
        result['fingerprint'] = hashlib.sha256(json.dumps(
            result, sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()
        return result
    finally:
        db.rollback()
        db.close()


def save_review():
    REVIEW.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = inspect_prior()
    except Exception as exc:
        REVIEW.write_text(json.dumps({
            'status': 'UNRESOLVED', 'error_type': type(exc).__name__,
            'reason': str(exc) if type(exc) is RuntimeError else None,
        }, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        raise
    REVIEW.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + '\n',
                      encoding='utf-8')
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    if result['status'] != 'RECONCILED':
        raise RuntimeError('Prior history remains unresolved; no new fixture may run')


def _test_processor(_factory, tx, _publish, runner=None):
    return coordinator.process_test(tx)


def _post(client, form):
    start = perf_counter()
    response = client.post('/customer/transaction', data=form, follow_redirects=False)
    return response.status_code, round((perf_counter() - start) * 1000, 2)


def run(rule_engine):
    evidence = {'status': 'INCOMPLETE', 'rule_engine': rule_engine, 'cases': []}
    try:
        current = inspect_prior()
        if not REVIEW.is_file() or REVIEW.is_symlink():
            raise RuntimeError('Read-only Stage5C inspection required before new fixtures')
        reviewed = json.loads(REVIEW.read_text(encoding='utf-8'))
        if (reviewed.get('status') != 'RECONCILED' or
                reviewed.get('fingerprint') != current['fingerprint']):
            raise RuntimeError('Prior-run inspection changed; repeat read-only review')
        evidence['prior_reconciliation'] = current
        evidence['preflight'] = current['baseline']
        app = load_test_application()
        module = sys.modules['stage4sa_server']
        if not app.testing or not module.v4_primary_enabled():
            raise RuntimeError('Isolated Flask V4-primary mode unavailable')
        module.set_rule_engine_enabled(rule_engine == 'on')
        if module._RULE_ENGINE_ENABLED != (rule_engine == 'on'):
            raise RuntimeError('Rule engine setting mismatch')
        app.config['V4_PRIMARY_CONNECTION_FACTORY'] = v1.connection
        app.config['V4_PRIMARY_TEST_PROCESSOR'] = _test_processor
        app.config['V4_PRIMARY_TEST_VALIDATOR'] = coordinator.validate_test
        # A Stage14 invocation during V4 mode is a hard test failure.
        stage14_calls = []
        def forbidden_stage14(*_args, **_kwargs):
            stage14_calls.append(1)
            raise RuntimeError('Stage14 fallback forbidden')
        module.get_stage14_model_service = forbidden_stage14
        notifications = []
        def observed_event(kind, payload):
            if kind in ('transaction', 'alert', 'ctr_report'):
                tx = payload.get('transaction_id') or payload.get('id')
                check = v1.connection()
                try:
                    row = check.execute('SELECT ai_risk_level FROM transactions WHERE id=?', (tx,)).fetchone()
                    if row is None or row['ai_risk_level'] == 'pending_v4':
                        raise RuntimeError('Notification before V4 decision commit')
                finally:
                    check.close()
            notifications.append(kind)
        module.broadcast_event = observed_event
        db = v1.connection()
        run_id = uuid4().hex[:12]
        wallets = [f'S5C{run_id}{i}' for i in range(2)]
        staff_account = f'S5C{run_id}S'
        try:
            for i, wallet in enumerate(wallets):
                db.execute('INSERT INTO users (username,password_hash,account_number,role,balance,kyc_status) '
                           'VALUES (?,?,?,?,?,?)', (f's5c_{run_id}_{i}', 'disabled-test-only',
                                                   wallet, 'customer', 20000, 'verified'))
            db.execute('INSERT INTO agents (agent_code,agent_name,status) VALUES (?,?,?)',
                       (f'S5C{run_id}', 'Stage5C synthetic agent', 'active'))
            db.execute('INSERT INTO users (username,password_hash,account_number,role,balance,kyc_status) '
                       'VALUES (?,?,?,?,?,?)', (f's5c_{run_id}_staff', 'disabled-test-only',
                                               staff_account, 'compliance', 0, 'verified'))
            db.commit()
            agent = db.execute('SELECT id FROM agents WHERE agent_code=?',
                               (f'S5C{run_id}',)).fetchone()['id']
            users = [db.execute('SELECT id FROM users WHERE account_number=?',
                                (wallet,)).fetchone()['id'] for wallet in wallets]
            staff_id = db.execute('SELECT id FROM users WHERE account_number=?',
                                  (staff_account,)).fetchone()['id']
        finally:
            db.close()
        client = app.test_client()
        with client.session_transaction() as session:
            session['user_id'] = users[0]
        forms = [
            ('wallet_transfer', dict(type='wallet_to_wallet', amount='10.50', channel='direct_wallet',
                                     agent_id='', serviced_wallet='', agent_flow_direction='none',
                                     recipient=wallets[1])),
            ('cash_in_ctr', dict(type='cash_in', amount='10000.00', channel='agent',
                                 agent_id=str(agent), serviced_wallet=wallets[0],
                                 agent_flow_direction='cash_in', recipient='')),
        ]
        for name, fields in forms:
            key = str(uuid4())
            form = dict(client_request_id=key, canonical_version='mobile_money.canonical.v1',
                        currency='USD', **fields)
            status, elapsed = _post(client, form)
            check = v1.connection()
            try:
                tx_row = check.execute('SELECT * FROM transactions WHERE sender_account=? AND client_request_id=?',
                                       (wallets[0], key)).fetchone()
                if tx_row is None:
                    raise RuntimeError('Flask transaction did not commit: ' + name)
                tx = tx_row['id']
                stored = check.execute('SELECT body FROM v4_shadow_results WHERE transaction_id=?',
                                       (tx,)).fetchone()
                result = coordinator.validate_test(json.loads(stored['body']), tx) if stored else None
                record = {'case': name, 'http_status': status, 'request_ms': elapsed,
                          'transaction_id': tx, 'ai_risk_level': tx_row['ai_risk_level'],
                          'risk_level': tx_row['risk_level'], 'rule_score': tx_row['rule_score'],
                          'ctr_required': tx_row['ctr_required'], 'sar_required': tx_row['sar_required'],
                          'canonical_rows': _count_for(check, 'canonical_mobile_money_events', tx),
                          'capture_rows': _count_for(check, 'cmm_source_changes', tx),
                          'alert_rows': _count_for(check, 'alerts', tx),
                          'ctr_required_observed': int(tx_row['ctr_required'] or 0),
                          'prediction': result['prediction'] if result else None,
                          'probability': result['suspicious_probability'] if result else None,
                          'scope': result['observation_scope'] if result else None,
                          'history_status': result['history_status'] if result else None,
                          'history_complete_through': result['history_complete_through'] if result else None,
                          'source_revision': result['source_revision'] if result else None,
                          'model_sha256': result['model_sha256'] if result else None,
                          'feature_version': result['feature_version'] if result else None,
                          'threshold': result['threshold'] if result else None,
                          'shadow_status': result['status'] if result else None}
                evidence['cases'].append(record)
                if (status not in (302, 303) or result is None or result['status'] != 'success' or
                        record['canonical_rows'] != 1 or record['capture_rows'] != 2 or
                        tx_row['ai_risk_level'] != result['decision']):
                    raise RuntimeError('V4 customer-primary result incomplete: ' + name)
                if name == 'cash_in_ctr' and record['ctr_required'] != 1:
                    raise RuntimeError('Independent transaction CTR flag missing')
                expected_alert = int(result['prediction'] == 1 or int(tx_row['rule_score'] or 0) >= 40)
                if record['alert_rows'] != expected_alert or bool(tx_row['sar_required']) != bool(expected_alert):
                    raise RuntimeError('AI/rule alert or SAR review flag mismatch')
            finally:
                check.rollback()
                check.close()
            if name == 'wallet_transfer':
                retry_status, retry_ms = _post(client, form)
                conflict_status, _ = _post(client, dict(form, amount='11.50'))
                evidence['idempotency'] = {'retry_http': retry_status, 'retry_ms': retry_ms,
                                           'changed_payload_http': conflict_status}
                if retry_status not in (302, 303) or conflict_status != 409:
                    raise RuntimeError('Request idempotency failed')
        failure_key = str(uuid4())
        failure_form = dict(client_request_id=failure_key,
                            canonical_version='mobile_money.canonical.v1',
                            type='wallet_to_wallet', amount='1.00', currency='USD',
                            channel='direct_wallet', agent_id='', serviced_wallet='',
                            agent_flow_direction='none', recipient=wallets[1])
        if os.environ.get('STAGE5C_INJECT_POST_ATTEST_ERROR'):
            raise RuntimeError('Inherited Stage5C worker fault injection is forbidden')
        os.environ['STAGE5C_INJECT_POST_ATTEST_ERROR'] = 'YES'
        try:
            failure_http, failure_ms = _post(client, failure_form)
        finally:
            os.environ.pop('STAGE5C_INJECT_POST_ATTEST_ERROR', None)
        check = v1.connection()
        try:
            failed = check.execute('SELECT id,ai_risk_level,risk_level FROM transactions '
                                   'WHERE sender_account=? AND client_request_id=?',
                                   (wallets[0], failure_key)).fetchone()
            if failed is None:
                raise RuntimeError('Injected inference failure reversed financial commit')
            failed_result = check.execute('SELECT body FROM v4_shadow_results WHERE transaction_id=?',
                                          (failed['id'],)).fetchone()
            body = coordinator.validate_test(json.loads(failed_result['body']), failed['id']) if failed_result else None
            if (failed['ai_risk_level'] != 'inference_error' or body is None or
                    body['status'] != 'inference_error'):
                raise RuntimeError('Inference failure was not explicit and persisted')
            evidence['inference_failure'] = {'transaction_id': failed['id'],
                                             'http_status': failure_http,
                                             'request_ms': failure_ms,
                                             'ai_risk_level': failed['ai_risk_level'],
                                             'risk_level': failed['risk_level'],
                                             'stored_status': body['status']}
            evidence['history_after_inference_failure'] = _history(check)
        finally:
            check.rollback()
            check.close()
        retry_http, retry_ms = _post(client, failure_form)
        evidence['inference_failure']['same_key_retry_http'] = retry_http
        evidence['inference_failure']['same_key_retry_ms'] = retry_ms
        if retry_http not in (302, 303):
            raise RuntimeError('Failed inference request retry duplicated or rejected payment')
        check = v1.connection()
        try:
            evidence['post_history'] = _history(check)
            evidence['balances'] = {w: float(check.execute(
                'SELECT balance FROM users WHERE account_number=?', (w,)).fetchone()['balance'])
                for w in wallets}
            if abs(evidence['balances'][wallets[0]] - 29988.50) > .001 or abs(
                    evidence['balances'][wallets[1]] - 20011.50) > .001:
                raise RuntimeError('Wallet balances differ from committed Flask payments')
            evidence['post_counts'] = {table: _count(check, table) for table in
                                       ('transactions', 'canonical_mobile_money_events',
                                        'cmm_source_changes', 'v4_shadow_results',
                                        'alerts', 'sar_reports', 'ctr_reports')}
            before = evidence['preflight']['counts']
            after = evidence['post_counts']
            if (after['transactions'] - before['transactions'] != 3 or
                    after['canonical_mobile_money_events'] - before['canonical_mobile_money_events'] != 3 or
                    after['cmm_source_changes'] - before['cmm_source_changes'] != 6 or
                    after['v4_shadow_results'] - before['v4_shadow_results'] != 3 or
                    after['sar_reports'] != before['sar_reports'] or
                    after['ctr_reports'] != before['ctr_reports']):
                raise RuntimeError('Financial, history, shadow or SAR counts differ')
        finally:
            check.rollback()
            check.close()
        evidence['notifications'] = notifications
        evidence['stage14_calls'] = len(stage14_calls)
        if stage14_calls:
            raise RuntimeError('Stage14 was invoked')
        if notifications.count('transaction') != 3:
            raise RuntimeError('Missing or duplicate committed transaction notifications')
        with client.session_transaction() as session:
            session['user_id'] = users[0]
        customer_api = client.get('/api/v4-shadow/results').status_code
        customer_dashboard = client.get('/compliance').status_code
        customer_socket = module.socketio.test_client(app, flask_test_client=client)
        try:
            customer_subscribe = customer_socket.emit('v4_shadow_subscribe', callback=True)
        finally:
            customer_socket.disconnect()
        with client.session_transaction() as session:
            session['user_id'] = staff_id
        staff_api = client.get('/api/v4-shadow/results').status_code
        staff_dashboard = client.get('/compliance').status_code
        staff_socket = module.socketio.test_client(app, flask_test_client=client)
        try:
            staff_subscribe = staff_socket.emit('v4_shadow_subscribe', callback=True)
        finally:
            staff_socket.disconnect()
        evidence['authorization'] = {'customer_api_http': customer_api,
                                     'customer_dashboard_http': customer_dashboard,
                                     'customer_socket': customer_subscribe,
                                     'staff_api_http': staff_api,
                                     'staff_dashboard_http': staff_dashboard,
                                     'staff_socket': staff_subscribe}
        if (customer_api != 403 or customer_dashboard not in (302, 303) or
                staff_api != 200 or staff_dashboard != 200 or
                customer_subscribe != {'ok': False} or staff_subscribe != {'ok': True}):
            raise RuntimeError('Dashboard or Socket.IO authorization failed')
        observed_classes = {case['prediction'] for case in evidence['cases']}
        evidence['classification_coverage'] = {'normal': 0 in observed_classes,
                                               'suspicious': 1 in observed_classes}
        if observed_classes != {0, 1}:
            evidence['status'] = 'PARTIAL'
            raise RuntimeError('Both model classes were not observed; predictions were not forced')
        evidence['status'] = 'EXECUTED'
    finally:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(evidence, indent=2, sort_keys=True, default=str) + '\n', encoding='utf-8')
    print(json.dumps({'status': evidence['status'], 'evidence': str(OUT),
                      'cases': evidence['cases']}, sort_keys=True, default=str))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--inspect-only', action='store_true')
    parser.add_argument('--start-new-after-review', action='store_true')
    parser.add_argument('--rule-engine', choices=('on', 'off'))
    args = parser.parse_args()
    try:
        if args.inspect_only and not args.execute and not args.start_new_after_review:
            save_review()
        elif (args.execute and args.start_new_after_review and not args.inspect_only
              and args.rule_engine):
            run(args.rule_engine)
        else:
            raise RuntimeError('Use read-only inspection first; explicit new-run flags required')
    except Exception as exc:
        reason = ': ' + str(exc) if type(exc) is RuntimeError else ''
        print('Stage5C live test stopped: ' + type(exc).__name__ + reason)
        raise SystemExit(1)
