"""Live nonfinancial Redis/WebSocket verification; no payments or AML alerts created."""
import ast
import json
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from dotenv import load_dotenv
    load_dotenv(ROOT / '.env')
    from database import connect_db
    from users import STAFF_ACCOUNTS
    from werkzeug.security import check_password_hash
    from playwright.sync_api import sync_playwright
    import redis
    import os
    database_url = os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL')
    if not database_url:
        raise RuntimeError('Application database URL is not configured.')

    def snapshot():
        db = connect_db(database_url)
        try:
            db.connection.start_transaction(readonly=True)
            return {
                'transactions': dict(db.execute('SELECT COUNT(*) n,MAX(id) last_id FROM transactions').fetchone()),
                'alerts': dict(db.execute('SELECT COUNT(*) n,MAX(id) last_id FROM alerts').fetchone()),
                'balances': [tuple(r.values()) for r in db.execute('SELECT id,balance FROM users ORDER BY id').fetchall()],
            }
        finally:
            db.close()

    db = connect_db(database_url)
    try:
        db.connection.start_transaction(readonly=True)
        customer = dict(db.execute("SELECT username,id_number,password_hash FROM users WHERE username='demo'").fetchone())
    finally:
        db.close()
    # Reuse only the existing demo credential after verifying its stored hash.
    tree = ast.parse((ROOT / 'server.py').read_text(encoding='utf-8'))
    candidates = [n.args[0].value for n in ast.walk(tree)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                  and n.func.id == 'generate_password_hash' and n.args
                  and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str)]
    password = next((v for v in candidates if check_password_hash(customer['password_hash'], v)), None)
    if not password:
        raise RuntimeError('Existing demo credential unavailable; no credential or account was changed.')
    before = snapshot()
    r = redis.Redis.from_url(os.environ['REDIS_URL'], decode_responses=True)
    assert r.ping()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        contexts = []
        try:
            pages = {}
            for role, route in [('admin', '/admin'), ('compliance', '/compliance'), ('customer', '/customer')]:
                context = browser.new_context()
                contexts.append(context)
                account = next((name for name, a in STAFF_ACCOUNTS.items() if a['role'] == role), None)
                form = ({'login': account, 'password': STAFF_ACCOUNTS[account]['password']} if account else
                        {'login': customer['username'], 'password': password, 'id_number': customer['id_number']})
                result = context.request.post('http://127.0.0.1:5000/login', form=form, max_redirects=0)
                assert result.status in (302, 303), role + ' login failed'
                page = context.new_page()
                page.goto('http://127.0.0.1:5000' + route)
                page.wait_for_function('window.getAmlSocket && window.getAmlSocket()?.connected', timeout=20000)
                page.evaluate("window.__realtimeProbes=[]; window.getAmlSocket().on('realtime_probe', p => window.__realtimeProbes.push(p))")
                pages[role] = page
            nonce = str(uuid.uuid4())
            started = time.monotonic()
            r.publish('aml-events', json.dumps({'publisher': 'nonfinancial-verification', 'event': 'realtime_probe', 'data': {'nonce': nonce}}))
            for role in ('admin', 'compliance'):
                pages[role].wait_for_function('window.__realtimeProbes.length === 1', timeout=5000)
                assert pages[role].evaluate('window.__realtimeProbes[0].nonce') == nonce
            elapsed = round(1000 * (time.monotonic() - started))
            pages['customer'].wait_for_timeout(400)
            assert pages['customer'].evaluate('window.__realtimeProbes.length') == 0
            page = pages['admin']
            page.evaluate("window.showAmlNotification('Realtime verification', 'verification')")
            assert page.locator('.notification-toast').count() >= 1
            page.wait_for_timeout(4300)
            assert not page.locator('.notification-toast').filter(has_text='Realtime verification').count()
            page.context.set_offline(True)
            page.wait_for_function('!window.getAmlSocket().connected', timeout=15000)
            page.context.set_offline(False)
            page.wait_for_function('window.getAmlSocket()?.connected', timeout=20000)
            health = page.context.request.get('http://127.0.0.1:5000/health').json()
            assert health['primary_model'] == 'V4' and health['rules_enabled'] and health['realtime']['redis_connected']
            assert snapshot() == before, 'Financial snapshot changed during verification; investigate concurrent activity.'
            print(json.dumps({'redis': 'PASS', 'staff_event_delivery': 'PASS', 'customer_isolation': 'PASS',
                              'toast_4_seconds': 'PASS', 'browser_reconnect': 'PASS', 'financial_snapshot_unchanged': True,
                              'observed_staff_delivery_ms': elapsed, 'primary_model': 'V4', 'rules_enabled': True}))
        finally:
            for context in contexts:
                context.close()
            browser.close()


if __name__ == '__main__':
    main()
