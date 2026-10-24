"""Guarded, resumable nonfinancial recovery for the supervisor-feedback fixes.

Uses the existing append-only staff retry mechanism. Never creates payments,
changes balances, alters canonical history, or overwrites original V4 results.
"""
import hashlib
import json
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ml_v4.frozen_inference.cli import connection
from v4_history_attestation import SERVER_UUID
import v4_primary
import v4_retry

CHECKPOINT = ROOT / 'instance' / 'supervisor_feedback_recovery.json'


def digest(rows):
    return hashlib.sha256(json.dumps([dict(row) for row in rows], sort_keys=True,
                                     separators=(',', ':'), default=str).encode()).hexdigest()


def protected(conn, ids):
    return dict(
        payments=digest(conn.execute('SELECT id,sender_account,receiver_account,amount,transaction_type,'
            'currency,channel,timestamp,status,agent_id,client_request_id FROM transactions ORDER BY id').fetchall()),
        wallets=digest(conn.execute('SELECT id,account_number,balance FROM users ORDER BY id').fetchall()),
        canonical=digest(conn.execute('SELECT * FROM canonical_mobile_money_events ORDER BY transaction_id').fetchall()),
        captures=digest(conn.execute('SELECT * FROM cmm_source_changes ORDER BY change_id').fetchall()),
        originals=digest(conn.execute('SELECT * FROM v4_shadow_results WHERE transaction_id IN (' +
            ','.join('?' for _ in ids) + ') ORDER BY transaction_id', tuple(ids)).fetchall()))


def snapshot(ids=None):
    conn = connection()
    try:
        conn.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY')
        identity = dict(conn.execute('SELECT DATABASE() db,@@server_uuid uuid,CURRENT_USER() principal').fetchone())
        if identity != dict(db='aml', uuid=SERVER_UUID, principal='aml@127.0.0.1'):
            raise RuntimeError('Local database identity changed')
        staff = conn.execute("SELECT id FROM users WHERE username='Admin' AND role='admin'").fetchone()
        if not staff:
            raise RuntimeError('Existing administrator unavailable')
        if ids is None:
            v4_primary.verify_database(conn)
            ids = [row['id'] for row in conn.execute("SELECT t.id FROM transactions t "
                "JOIN canonical_mobile_money_events c ON c.transaction_id=t.id "
                "JOIN v4_shadow_results v ON v.transaction_id=t.id "
                "WHERE t.ai_risk_level='inference_error' AND v.status='inference_error' "
                "AND v.error_code IN ('RESOURCE_ERROR','HISTORY_INCOMPLETE') ORDER BY t.id").fetchall()]
        if not ids or len(ids) > 53:
            raise RuntimeError('Expected recovery scope changed; no wider retry permitted')
        return identity, staff['id'], ids, protected(conn, ids)
    finally:
        conn.rollback()
        conn.close()


def save(state):
    CHECKPOINT.parent.mkdir(exist_ok=True)
    temporary = CHECKPOINT.with_suffix('.tmp')
    temporary.write_text(json.dumps(state, indent=2), encoding='utf-8')
    temporary.replace(CHECKPOINT)


def main():
    if '--apply' not in sys.argv:
        identity, staff, ids, hashes = snapshot()
        print(json.dumps(dict(mode='read-only', database=identity, staff_user_id=staff,
                              candidates=ids, protected=hashes)), flush=True)
        return
    if CHECKPOINT.exists():
        state = json.loads(CHECKPOINT.read_text(encoding='utf-8'))
    else:
        identity, staff, ids, hashes = snapshot()
        state = dict(database=identity, staff_user_id=staff, protected=hashes,
                     actions=[dict(transaction_id=tx, request_key=str(uuid.uuid4())) for tx in ids])
        save(state)
    ids = [action['transaction_id'] for action in state['actions']]
    for index, action in enumerate(state['actions'], 1):
        identity, staff, _, hashes = snapshot(ids)
        if identity != state['database'] or staff != state['staff_user_id'] or hashes != state['protected']:
            raise RuntimeError('Protected source or balances changed. Stopped without replaying payments.')
        if action.get('result', {}).get('status') == 'success':
            continue
        result = v4_retry.retry(connection, action['transaction_id'], staff, action['request_key'])
        action['result'] = result
        save(state)
        print(json.dumps(dict(completed=index, total=len(ids), **result)), flush=True)
        if result['status'] != 'success':
            raise RuntimeError('Audited retry did not succeed; stopped for inspection')
    _, _, _, hashes = snapshot(ids)
    if hashes != state['protected']:
        raise RuntimeError('Protected source or balances changed during verification')
    state['protected_data_unchanged'] = True
    save(state)
    print(json.dumps(dict(successes=len(ids), protected_data_unchanged=True)), flush=True)


if __name__ == '__main__':
    main()
