"""Guarded read/optional write check for the existing transaction-8 V4 error."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

from canonical_history import freshness
from canonical_history_store import assess
from ml_v4.stage4sa import coordinator
from ml_v4.stage4sa.harness import load_test_application
from ml_v4.test_binding import v1
import v4_retry
import v4_shadow

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'ml_v4/evidence/stage5c/retry_verification.json'
UUID = 'd441b7bb-43f6-11f1-a2d8-0a0027000005'
MODEL = ROOT / 'ml_v4/development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib'
MODEL_SHA = '555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18'
STAFF_ACCOUNT = 'S5C75dda2d36575S'
WALLETS = ('S5C75dda2d365750', 'S5C75dda2d365751')


def _protected(conn):
    items = {}
    for table, sql in {
        'financial': ('SELECT id,sender_account,receiver_account,amount,transaction_type,'
                      'client_request_id FROM transactions ORDER BY id'),
        'users': 'SELECT id,account_number,balance FROM users ORDER BY id',
        'canonical': 'SELECT * FROM canonical_mobile_money_events ORDER BY transaction_id',
        'capture': 'SELECT * FROM cmm_source_changes ORDER BY change_id',
        'original_results': 'SELECT * FROM v4_shadow_results ORDER BY transaction_id',
    }.items():
        rows = [dict(row) for row in conn.execute(sql).fetchall()]
        items[table] = hashlib.sha256(json.dumps(rows, sort_keys=True, default=str,
                                           separators=(',', ':')).encode()).hexdigest()
    return items


def preflight():
    if (os.environ.get('AML_PRIMARY_MODEL') != 'V4' or
            os.environ.get('V4_STAGE4T_EXPECTED_SERVER_UUID') != UUID or
            os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL') or
            os.environ.get('V4_SHADOW_ENABLED') == 'ON'):
        raise RuntimeError('Disposable V4 retry environment not pinned')
    p = v1.config(os.environ.get('V4_STAGE4T_TEST_DB_URL', ''))
    if p.hostname != '127.0.0.1' or p.port != 3306:
        raise RuntimeError('Only pinned local disposable MySQL allowed')
    if (hashlib.sha256(MODEL.read_bytes()).hexdigest() != MODEL_SHA or
            hashlib.sha256(coordinator.WORKER.read_bytes()).hexdigest() != coordinator.WORKER_SHA256):
        raise RuntimeError('Frozen model or isolated worker integrity changed')
    authority = v1.load_authority()
    if authority['server_uuid'] != UUID:
        raise RuntimeError('Test authority changed')
    conn = v1.connection(authority)
    try:
        v1._triggers(conn)
        v1._boundary(conn, authority)
        v4_retry.require_schema(conn)
        scope, current, previous = assess(conn, v1.SCOPE)
        if freshness(scope, current, previous) != 'COMPLETE_VERIFIED' or current['issues']:
            raise RuntimeError('History authority not fresh')
        counts = {table: conn.execute('SELECT COUNT(*) AS n FROM ' + table).fetchone()['n']
                  for table in ('transactions', 'canonical_mobile_money_events',
                                'cmm_source_changes', 'v4_shadow_results')}
        if tuple(counts.values()) != (8, 8, 16, 8):
            raise RuntimeError('Previously reconciled financial/history counts changed')
        row = conn.execute('SELECT ai_risk_level FROM transactions WHERE id=8').fetchone()
        original = v4_shadow.get(conn, 8)
        staff = conn.execute('SELECT id,role FROM users WHERE account_number=?',
                             (STAFF_ACCOUNT,)).fetchone()
        if (row is None or row['ai_risk_level'] != 'inference_error' or
                original is None or v4_shadow.validate(original, 8)['status'] != 'inference_error' or
                staff is None or staff['role'] != 'compliance'):
            raise RuntimeError('Transaction-8 error or staff identity changed')
        events = conn.execute('SELECT COUNT(*) AS n FROM v4_primary_attempt_events '
                              'WHERE transaction_id=8').fetchone()['n']
        if events:
            raise RuntimeError('Transaction-8 retry/closure already recorded; inspect manually')
        return {'counts': counts, 'staff_id': staff['id'],
                'source_revision': current['source_revision'],
                'protected_sha256': _protected(conn)}
    finally:
        conn.rollback()
        conn.close()


def run(apply=False):
    before = preflight()
    if not apply:
        return {'status': 'READ_ONLY_READY', 'database': v1.DATABASE,
                'server_uuid': UUID, 'counts': before['counts'],
                'source_revision': before['source_revision']}
    if os.environ.get('STAGE5C_RETRY_APPLY') != 'YES' or OUT.exists() or OUT.is_symlink():
        raise RuntimeError('Explicit one-time retry authorization or output guard unavailable')
    app = load_test_application()
    app.config['V4_RETRY_TEST_WORKER'] = coordinator.invoke_test
    app.config['V4_RETRY_TEST_VALIDATOR'] = coordinator.validate_test
    client = app.test_client()
    with client.session_transaction() as state:
        state['user_id'] = before['staff_id']
    case = client.get('/compliance/v4-error/8')
    if case.status_code != 200:
        raise RuntimeError('Staff V4 error case unavailable')
    key = str(uuid4())
    response = client.post('/compliance/v4-error/8/retry', data={
        'csrf_token': case.json['csrf_token'], 'request_key': key})
    if response.status_code != 200:
        raise RuntimeError('Guarded staff retry failed; inspect audit read-only')
    conn = v1.connection()
    try:
        if _protected(conn) != before['protected_sha256']:
            raise RuntimeError('Protected financial/source/original-result rows changed')
        events = [dict(row) for row in conn.execute(
            'SELECT event_kind,outcome,error_code,result_body,staff_user_id,request_key '
            'FROM v4_primary_attempt_events WHERE transaction_id=8 ORDER BY event_id').fetchall()]
        if ([row['event_kind'] for row in events] != ['STARTED', 'COMPLETED'] or
                any(row['staff_user_id'] != before['staff_id'] or row['request_key'] != key
                    for row in events)):
            raise RuntimeError('Retry audit event sequence changed')
        scope, current, previous = assess(conn, v1.SCOPE)
        if freshness(scope, current, previous) != 'COMPLETE_VERIFIED' or current['issues']:
            raise RuntimeError('Post-retry history not fresh')
        decision = conn.execute('SELECT ai_risk_level,risk_level FROM transactions WHERE id=8').fetchone()
        result = coordinator.validate_test(json.loads(events[-1]['result_body']), 8)
        if result['status'] == 'success' and decision['ai_risk_level'] != result['decision']:
            raise RuntimeError('Effective decision differs from audited V4 result')
        if result['status'] == 'inference_error' and decision['ai_risk_level'] != 'inference_error':
            raise RuntimeError('Failed retry was falsely classified')
        evidence = {'status': 'PASS', 'database': v1.DATABASE, 'transaction_id': 8,
                    'request_key': key, 'attempt_outcome': result['status'],
                    'prediction': result['prediction'],
                    'suspicious_probability': result['suspicious_probability'],
                    'effective_decision': decision['ai_risk_level'],
                    'history': 'COMPLETE_VERIFIED', 'original_error_preserved': True,
                    'protected_sha256': before['protected_sha256']}
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(evidence, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        return evidence
    finally:
        conn.rollback()
        conn.close()


if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('--apply', action='store_true')
    selected = args.parse_args()
    try:
        print(json.dumps(run(selected.apply), sort_keys=True))
    except Exception as exc:
        print('Disposable V4 retry verification stopped: ' + type(exc).__name__)
        raise SystemExit(1)
