"""One explicitly approved $0.01 HTTP payment, with durable request ID and reconciliation.

Default displays existing evidence. --execute-approved-transfer runs only once;
an existing evidence file prevents another financial submission.
"""
import argparse
import ast
from decimal import Decimal
import json
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BASE = 'http://127.0.0.1:5000'
EVIDENCE = ROOT / 'data/local-v4-backups/controlled-v4-transfer.json'


def run():
    if EVIDENCE.exists():
        raise RuntimeError('Evidence already exists. Inspect its request ID; do not create another payment.')
    from dotenv import load_dotenv, dotenv_values
    load_dotenv(ROOT / '.env')
    from database import connect_db
    from users import STAFF_ACCOUNTS
    from werkzeug.security import check_password_hash
    from canonical_history_store import assess
    from canonical_history import freshness
    from v4_shadow import SHA
    from playwright.sync_api import sync_playwright
    url = dotenv_values(ROOT / '.env')['DATABASE_URL']

    def db():
        conn = connect_db(url)
        conn.connection.start_transaction(readonly=True)
        identity = conn.execute('SELECT DATABASE() db,CURRENT_USER() principal,@@server_uuid uuid').fetchone()
        from tools.recover_local_v4_history import IDENTITY
        if dict(identity) != IDENTITY:
            conn.close()
            raise RuntimeError('Local identity mismatch')
        return conn

    def snapshot():
        conn = db()
        try:
            return {'counts': {t: conn.execute('SELECT COUNT(*) n FROM ' + t).fetchone()['n']
                               for t in ('transactions', 'canonical_mobile_money_events',
                                         'v4_shadow_results', 'cmm_source_changes')},
                    'balances': {r['account_number']: str(r['balance'])
                                 for r in conn.execute('SELECT account_number,balance FROM users').fetchall()}}
        finally:
            conn.close()

    conn = db()
    try:
        customer = dict(conn.execute("SELECT * FROM users WHERE username='demo'").fetchone())
        receiver = dict(conn.execute("SELECT * FROM users WHERE username='user_low_1'").fetchone())
        alert = conn.execute('SELECT id FROM alerts ORDER BY id LIMIT 1').fetchone()['id']
        staff_hashes = {name: conn.execute('SELECT password_hash FROM users WHERE username=?',
                                          (name,)).fetchone()['password_hash'] for name in STAFF_ACCOUNTS}
    finally:
        conn.close()
    assert customer['account_number'] == 'ACC1003' and receiver['account_number'] == 'ACC1000'
    tree = ast.parse((ROOT / 'server.py').read_text(encoding='utf-8'))
    seed = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'seed_demo_data')
    password = next(n.args[0].value for n in ast.walk(seed)
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                    and n.func.id == 'generate_password_hash' and n.args
                    and isinstance(n.args[0], ast.Constant))
    assert check_password_hash(customer['password_hash'], password)
    assert all(check_password_hash(staff_hashes[name], account['password'])
               for name, account in STAFF_ACCOUNTS.items())
    checks = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='msedge', headless=True)
        try:
            contexts = {role: browser.new_context(base_url=BASE)
                        for role in ('anonymous', 'customer', 'admin', 'compliance')}
            clients = {role: context.request for role, context in contexts.items()}
            response = clients['customer'].post('/login', form={
                'login': customer['username'], 'id_number': customer['id_number'],
                'password': password}, max_redirects=0)
            assert response.status == 302
            for role, name in (('admin', 'Admin'), ('compliance', 'Compliance')):
                response = clients[role].post('/login', form={
                    'login': name, 'password': STAFF_ACCOUNTS[name]['password']}, max_redirects=0)
                assert response.status == 302
            for role, path in (('customer', '/customer'), ('compliance', '/compliance'),
                               ('compliance', '/compliance/alert/' + str(alert)),
                               ('compliance', '/reports'), ('admin', '/admin')):
                response = clients[role].get(path, max_redirects=0)
                assert response.status == 200, (role, path, response.status)
                checks[role + ' ' + path] = 'PASS'
            for role in ('anonymous', 'customer'):
                for path in ('/admin', '/compliance', '/reports', '/api/v4-shadow/results', '/stream'):
                    response = clients[role].get(path, max_redirects=0)
                    assert response.status in (302, 401, 403), (role, path, response.status)
            checks['protected_routes'] = 'PASS'
            response = clients['admin'].post('/admin/generate-transactions', max_redirects=0)
            assert response.status == 403, ('Generation request protection', response.status)
            checks['generation_request_protected'] = 'PASS'
            for path in ('/admin/generate-structuring-scenario',
                         '/admin/generate-network-scenario', '/admin/generate-agent-scenario',
                         '/admin/clear-transactions'):
                response = clients['admin'].post(path, max_redirects=0)
                assert response.status in (409, 503), (path, response.status)
            checks['legacy_batch_and_clear_blocked'] = 'PASS'
            health = clients['anonymous'].get('/health').json()
            assert health['primary_model'] == 'V4' and health['rules_enabled'] is True
            metadata = clients['admin'].get('/api/v1/ai-model').json()
            assert metadata['primary_model'] == 'V4'
            print('Live authentication, pages, authorization and V4/rule selection: PASS', flush=True)

            pages = {}
            for role in ('customer', 'compliance'):
                page = contexts[role].new_page()
                page.goto('/' + role)
                page.wait_for_function('window.getAmlSocket && window.getAmlSocket()?.connected')
                page.evaluate("""() => {
                    sessionStorage.setItem('v4VerificationEvents', '[]');
                    window.getAmlSocket().onAny((event) => {
                        const events = JSON.parse(sessionStorage.getItem('v4VerificationEvents'));
                        events.push(event);
                        sessionStorage.setItem('v4VerificationEvents', JSON.stringify(events));
                    });
                }""")
                reply = page.evaluate("""() => new Promise((resolve, reject) => {
                    const timer = setTimeout(() => reject(new Error('Subscription timeout')), 10000);
                    window.getAmlSocket().emit('v4_shadow_subscribe', response => {
                        clearTimeout(timer); resolve(response);
                    });
                })""")
                assert reply == {'ok': role == 'compliance'}
                pages[role] = page
            checks['staff_subscription_protected'] = 'PASS'

            before = snapshot()
            request_id = str(uuid.uuid4())
            plan = {'status': 'PREPARED', 'request_id': request_id, 'sender': 'ACC1003',
                    'receiver': 'ACC1000', 'amount': '0.01', 'before': before, 'checks': checks}
            with EVIDENCE.open('x') as stream:
                json.dump(plan, stream, indent=2)
            form = {'client_request_id': request_id, 'canonical_version': 'mobile_money.canonical.v1',
                    'type': 'wallet_to_wallet', 'amount': '0.01', 'currency': 'USD',
                    'channel': 'direct_wallet', 'agent_id': '', 'serviced_wallet': '',
                    'agent_flow_direction': 'none', 'recipient': 'ACC1000'}
            print('Submitting one approved $0.01 transfer; request ID ' + request_id, flush=True)
            response = clients['customer'].post('/customer/transaction', form=form,
                                                max_redirects=0, timeout=90000)
            plan['http_status'] = response.status
            conn = db()
            tx = conn.execute('SELECT id,amount,ai_risk_level,ai_reason,rule_score,rule_reason,risk_level '
                              'FROM transactions WHERE sender_account=? AND client_request_id=?',
                              ('ACC1003', request_id)).fetchone()
            conn.close()
            assert tx is not None, 'No payment row found; inspect before doing anything else'
            plan['transaction'] = dict(tx)
            EVIDENCE.write_text(json.dumps(plan, indent=2))
            after = snapshot()
            for account, original in before['balances'].items():
                expected = Decimal(original) + (Decimal('-.01') if account == 'ACC1003' else
                                                 Decimal('.01') if account == 'ACC1000' else Decimal(0))
                assert abs(Decimal(after['balances'][account]) - expected) < Decimal('.00000001'), account
            for table, increase in (('transactions', 1), ('canonical_mobile_money_events', 1),
                                    ('cmm_source_changes', 2)):
                assert after['counts'][table] == before['counts'][table] + increase
            plan.update(after=after, balance_reconciliation='PASS')
            conn = db()
            result = conn.execute('SELECT body FROM v4_shadow_results WHERE transaction_id=?',
                                  (tx['id'],)).fetchone()
            scope, history, previous = assess(conn, 'controlled-prototype-v1')
            conn.close()
            plan.update(history=freshness(scope, history, previous),
                        history_authority=previous['verification_authority'],
                        inference=json.loads(result['body']) if result else None)
            EVIDENCE.write_text(json.dumps(plan, indent=2))
            assert result and plan['inference']['status'] == 'success', \
                'Payment committed; inference unresolved. Retry inference only, never create another payment.'
            assert plan['inference']['model_sha256'] == SHA
            assert plan['inference']['source_revision'] == history['source_revision']
            assert plan['history'] == 'COMPLETE_VERIFIED'
            duplicate = clients['customer'].post('/customer/transaction', form=form, max_redirects=0)
            assert duplicate.status == 302
            assert snapshot() == after, 'Duplicate request changed payment/canonical state'
            plan['duplicate_request'] = 'PASS'
            pages['customer'].wait_for_timeout(1000)
            events = {role: page.evaluate("JSON.parse(sessionStorage.getItem('v4VerificationEvents'))")
                      for role, page in pages.items()}
            assert 'transaction' in events['compliance']
            assert not {'transaction', 'alert', 'v4_shadow_result'}.intersection(events['customer'])
            assert 'balance' in events['customer']
            plan['realtime'] = {'staff_transaction_received': True,
                                'customer_private_balance_received': True,
                                'customer_staff_events_received': False}
            visible = clients['compliance'].get('/api/v4-shadow/results').json()['results']
            assert any(r['transaction_id'] == str(tx['id']) and r['status'] == 'success' for r in visible)
            plan.update(compliance_result_visible='PASS', status='VERIFIED')
            EVIDENCE.write_text(json.dumps(plan, indent=2))
            print(json.dumps({k: plan[k] for k in ('status', 'transaction', 'inference', 'history',
                                                 'duplicate_request', 'realtime')}, indent=2), flush=True)
        finally:
            browser.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-approved-transfer', action='store_true')
    args = parser.parse_args()
    if args.execute_approved_transfer:
        run()
    elif EVIDENCE.exists():
        print(EVIDENCE.read_text())
    else:
        print('No controlled transfer evidence exists. No transaction was submitted.')
