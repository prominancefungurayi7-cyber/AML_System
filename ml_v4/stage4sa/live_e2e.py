"""Guarded local Stage4S-B run through the pinned Flask transaction handler."""
import json
import time
from pathlib import Path
from uuid import uuid4

from ml_v4.stage4sa.harness import load_test_application
from ml_v4.stage4sa.live_readiness import run as readiness
from ml_v4.test_binding import v1

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'ml_v4/evidence/stage4sb/live_e2e.json'


def count(db, table):
    return db.execute('SELECT COUNT(*) AS n FROM ' + table).fetchone()['n']


def run():
    # This is intentionally repeated immediately before the first write.
    readiness()
    db = v1.connection()
    run_id = uuid4().hex[:12]
    evidence = {'status': 'INCOMPLETE', 'database': v1.DATABASE,
                'server_uuid': v1.load_authority()['server_uuid'], 'cases': []}
    try:
        before = {t: count(db, t) for t in ('transactions', 'alerts', 'v4_shadow_results',
                                             'canonical_mobile_money_events', 'cmm_source_changes')}
        if any(before.values()):
            raise RuntimeError('Disposable financial/result ledger is not empty')
        app = load_test_application()
        client = app.test_client()
        wallets = [f'S4SB{run_id}{i}' for i in range(2)]
        for i, wallet in enumerate(wallets):
            db.execute('INSERT INTO users (username,password_hash,account_number,role,balance,kyc_status) '
                       'VALUES (?,?,?,?,?,?)', (f's4sb_{run_id}_{i}', 'disabled-test-only',
                                               wallet, 'customer', 1000, 'verified'))
        db.execute('INSERT INTO agents (agent_code,agent_name,status) VALUES (?,?,?)',
                   (f'S4SB{run_id}', 'Stage4S-B synthetic agent', 'active'))
        db.commit()
        agent = db.execute('SELECT id FROM agents WHERE agent_code=?',
                           (f'S4SB{run_id}',)).fetchone()['id']
        users = [db.execute('SELECT id FROM users WHERE account_number=?', (w,)).fetchone()['id']
                 for w in wallets]
        cases = [
            ('wallet_transfer', 'wallet_to_wallet', 'direct_wallet', '', '', 'none', wallets[1]),
            ('agent_transfer', 'wallet_to_wallet', 'agent', str(agent), wallets[0], 'none', wallets[1]),
            ('cash_in', 'cash_in', 'agent', str(agent), wallets[0], 'cash_in', ''),
            ('cash_out', 'cash_out', 'agent', str(agent), wallets[0], 'cash_out', ''),
        ]
        for name, tx_type, channel, aid, serviced, flow, recipient in cases:
            with client.session_transaction() as session:
                session['user_id'] = users[0]
            form = {'canonical_version': 'mobile_money.canonical.v1', 'type': tx_type,
                    'amount': '1.00', 'currency': 'USD', 'channel': channel,
                    'agent_id': aid, 'serviced_wallet': serviced,
                    'agent_flow_direction': flow, 'recipient': recipient}
            start = time.perf_counter()
            response = client.post('/customer/transaction', data=form, follow_redirects=False)
            elapsed = (time.perf_counter() - start) * 1000
            check = v1.connection()
            try:
                row = check.execute('SELECT MAX(id) AS id FROM transactions').fetchone()
                tx = row['id']
                canonical = check.execute('SELECT COUNT(*) AS n FROM canonical_mobile_money_events '
                                          'WHERE transaction_id=?', (tx,)).fetchone()['n'] if tx else 0
                shadow = check.execute('SELECT body FROM v4_shadow_results WHERE transaction_id=?',
                                       (tx,)).fetchone() if tx else None
                result = json.loads(shadow['body']) if shadow else None
                from canonical_history_store import assess
                from canonical_history import freshness
                scope, current, previous = assess(check, v1.SCOPE)
                history = freshness(scope, current, previous)
                evidence['cases'].append({'case': name, 'http_status': response.status_code,
                                          'transaction_id': tx, 'canonical_rows': canonical,
                                          'shadow_status': result.get('status') if result else None,
                                          'prediction': result.get('prediction') if result else None,
                                          'suspicious_probability': result.get('suspicious_probability') if result else None,
                                          'observation_scope': result.get('observation_scope') if result else None,
                                          'history_status': result.get('history_status') if result else None,
                                          'ledger_history_status': history,
                                          'request_plus_inference_ms': round(elapsed, 2)})
                if not (response.status_code in (302, 303) and canonical == 1 and result
                        and history == 'COMPLETE_VERIFIED'):
                    raise RuntimeError('Live transaction/canonical/shadow result incomplete: ' + name)
            finally:
                check.rollback()
                check.close()
        evidence['status'] = 'EXECUTED'
    finally:
        db.rollback()
        db.close()
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(evidence, indent=2, sort_keys=True) + '\n', encoding='utf-8')


if __name__ == '__main__':
    try:
        run()
    except Exception as exc:
        print('Stage4S-B stopped: ' + type(exc).__name__)
        raise SystemExit(1)
