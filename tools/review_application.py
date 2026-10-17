"""Read-only local page review. Skips startup/seed/monitor; never serves a live app.

Run with the application virtualenv. --browser also needs Playwright and Edge.
All application SQL is restricted to SELECT/SHOW inside MySQL READ ONLY transactions.
Browser requests are fulfilled by Flask's test client; financial requests are blocked.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import sys
import types
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load_application():
    from dotenv import dotenv_values
    settings = dotenv_values(ROOT / '.env')
    url = os.environ.get('DATABASE_URL') or settings.get('DATABASE_URL') or settings.get('MYSQL_URL')
    if not url or urlsplit(url).path != '/aml' or urlsplit(url).hostname not in ('127.0.0.1', 'localhost'):
        raise RuntimeError('Expected the configured local aml database')
    os.environ.update(DATABASE_URL=url, MYSQL_URL=url, AML_PRIMARY_MODEL='V4',
                      AML_RULE_ENGINE_ENABLED='ON', SOCKETIO_ALLOWED_ORIGINS='http://127.0.0.1:5000')
    os.environ.pop('REDIS_URL', None)
    os.environ.pop('KAFKA_BOOTSTRAP_SERVERS', None)
    import database
    original = database.connect_db

    def readonly(candidate=None):
        if candidate not in (None, url):
            raise RuntimeError('Unexpected database target')
        db = original(url)
        db.connection.start_transaction(readonly=True)
        identity = db.execute('SELECT DATABASE() AS db, CURRENT_USER() AS principal, @@server_uuid AS uuid').fetchone()
        if identity != {'db': 'aml', 'principal': 'aml@127.0.0.1', 'uuid': 'd441b7bb-43f6-11f1-a2d8-0a0027000005'}:
            db.close()
            raise RuntimeError('Database identity mismatch')
        execute = db.execute
        def read(query, params=()):
            if query.lstrip().split(None, 1)[0].upper() not in ('SELECT', 'SHOW'):
                raise RuntimeError('Read-only review blocked a database write')
            return execute(query, params)
        db.execute = read
        db.executescript = lambda *_: (_ for _ in ()).throw(RuntimeError('DDL blocked'))
        db.commit = lambda: (_ for _ in ()).throw(RuntimeError('Commit blocked'))
        return db

    tree = ast.parse((ROOT / 'server.py').read_text(encoding='utf-8'))
    guards = dotenv = 0
    kept = []
    for node in tree.body:
        if isinstance(node, ast.If) and isinstance(node.test, ast.Compare) and isinstance(node.test.left, ast.Name) and node.test.left.id == '__name__':
            guards += 1
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'load_dotenv':
            dotenv += 1
            continue
        kept.append(node)
    assert (guards, dotenv) == (3, 2), 'Unrecognized startup structure'
    tree.body = kept
    module = types.ModuleType('readonly_review_server')
    module.__file__ = str(ROOT / 'server.py')
    sys.modules[module.__name__] = module
    def forbidden(*args, **kwargs):
        raise RuntimeError('Import-time DB access blocked')
    database.connect_db = forbidden
    try:
        exec(compile(tree, module.__file__, 'exec'), module.__dict__)
    finally:
        database.connect_db = original
    module._database_connect_db = readonly
    module.app.config.update(TESTING=True, SECRET_KEY=os.urandom(32), MONITOR_STOP=True)
    return module, readonly


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', action='store_true')
    args = parser.parse_args()
    module, readonly = load_application()
    app = module.app
    db = readonly()
    users = {role: dict(db.execute('SELECT id, username, role FROM users WHERE role=? ORDER BY id LIMIT 1', (role,)).fetchone()) for role in ('customer', 'admin', 'compliance')}
    alert = db.execute('SELECT id FROM alerts ORDER BY id LIMIT 1').fetchone()['id']
    def fingerprint():
        conn = readonly()
        state = {}
        for table in ('users', 'transactions', 'alerts', 'canonical_mobile_money_events', 'cmm_source_changes', 'cmm_history_attestations', 'v4_shadow_results', 'v4_primary_attempt_events'):
            rows = [dict(row) for row in conn.execute('SELECT * FROM ' + table).fetchall()]
            encoded = sorted(json.dumps(row, sort_keys=True, default=str) for row in rows)
            state[table] = {'rows': len(rows), 'sha256': hashlib.sha256('\n'.join(encoded).encode()).hexdigest()}
        conn.close()
        return state
    before = fingerprint()
    print('Database identity verified: aml / aml@127.0.0.1 / d441b7bb-43f6-11f1-a2d8-0a0027000005')
    print('Protected row counts:', {k: v['rows'] for k, v in before.items()})
    from canonical_history_store import assess
    from collections import Counter
    _, history, _ = assess(db, 'controlled-prototype-v1')
    history_ready = history['status'] == 'COMPLETE_VERIFIED' and not history['issues']
    print('V4 history gate:', history['status'])
    if not history_ready:
        print('History blockers:', dict(Counter(issue.get('code', 'UNKNOWN') for issue in history['issues'])))
    db.close()
    clients = {}
    results = []
    failures = []
    paths = {
        'anonymous': ['/login', '/register', '/forgot-password', '/health'],
        'customer': ['/customer', '/messages', '/api/unread-count', '/api/conversations', '/api/messageable-users'],
        'admin': ['/admin', '/reports', '/messages', '/api/v1/ai-model'],
        'compliance': ['/compliance', '/reports', '/compliance/alert/' + str(alert), '/api/v4-shadow/results', '/api/v4-shadow/results?errors=1', '/messages'],
    }
    for role, routes in paths.items():
        client = app.test_client()
        clients[role] = client
        if role in users:
            with client.session_transaction() as session:
                session.update(user_id=users[role]['id'], username=users[role]['username'], role=role,
                               auth_token=module.auth_sessions.create(users[role]['id'], 3600))
        for path in routes:
            response = client.get(path)
            passed = response.status_code == 200 and b'password_hash' not in response.data
            results.append(f'{role} {path}: {response.status_code}')
            if not passed:
                failures.append(results[-1])
    for role in ('anonymous', 'customer'):
        for path in ('/admin', '/compliance', '/reports', '/api/v4-shadow/results', '/stream'):
            response = clients[role].get(path)
            if response.status_code not in (302, 401, 403):
                failures.append(f'Access protection {role} {path}: {response.status_code}')
    health = clients['anonymous'].get('/health').json
    assert isinstance(health['database'], dict) and health['primary_model'] == 'V4'
    assert clients['admin'].get('/api/v1/ai-model').json['primary_model'] == 'V4'
    # Restored V4 generation requires the signed form and session CSRF token.
    # An empty POST must fail before any payment work.
    response = clients['admin'].post('/admin/generate-transactions')
    if response.status_code != 403:
        failures.append(f'Generation request protection: {response.status_code}')
    response = clients['admin'].get('/api/admin/generation')
    if response.status_code != 200 or not response.is_json:
        failures.append(f'Generation progress access: {response.status_code}')
    for role in ('anonymous', 'customer', 'compliance'):
        for path in ('/api/admin/generation', '/admin/generate-transactions'):
            response = (clients[role].get(path) if path.startswith('/api/')
                        else clients[role].post(path))
            if response.status_code not in (302, 401, 403):
                failures.append(f'Generation authorization {role} {path}: {response.status_code}')
    # Unsupported legacy generators and destructive maintenance remain blocked.
    for path in ('/admin/generate-structuring-scenario',
                 '/admin/generate-network-scenario', '/admin/generate-agent-scenario',
                 '/admin/clear-transactions'):
        response = clients['admin'].post(path)
        if response.status_code not in (409, 503):
            failures.append(f'V4 blocked operation {path}: {response.status_code}')
    response = clients['admin'].post('/admin/migrate-database', follow_redirects=True)
    if response.status_code != 200 or b'No migration was required' not in response.data:
        failures.append('V4 database maintenance verification did not pass')
    # Exercise actual socket authorization and private balance delivery without a network server.
    anonymous_socket = module.socketio.test_client(app, flask_test_client=clients['anonymous'])
    assert not anonymous_socket.is_connected()
    customer_socket = module.socketio.test_client(app, flask_test_client=clients['customer'])
    staff_socket = module.socketio.test_client(app, flask_test_client=clients['compliance'])
    assert customer_socket.is_connected() and staff_socket.is_connected()
    customer_socket.get_received()
    staff_socket.get_received()
    module.broadcast_event('review_probe', {'review': True})
    assert not any(e['name'] == 'review_probe' for e in customer_socket.get_received())
    assert any(e['name'] == 'review_probe' for e in staff_socket.get_received())
    conn = readonly()
    wallet = conn.execute('SELECT account_number FROM users WHERE id=?', (users['customer']['id'],)).fetchone()
    module.broadcast_user_balance(conn, wallet['account_number'])
    assert any(e['name'] == 'balance' for e in customer_socket.get_received())
    conn.close()
    customer_socket.disconnect()
    staff_socket.disconnect()
    print('PASS: anonymous socket denied; staff events restricted; private wallet balance delivered')
    print('\n'.join(results))
    if args.browser:
        from playwright.sync_api import sync_playwright
        out = ROOT / '.pytest_cache' / 'ui-review'
        out.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel='msedge', headless=True)
            for role, path in [('anonymous', '/login'), ('customer', '/customer'), ('admin', '/admin'), ('compliance', '/compliance'), ('compliance', '/reports'), ('compliance', '/compliance/alert/' + str(alert)), ('anonymous', '/register'), ('anonymous', '/forgot-password'), ('customer', '/messages')]:
                for width in (1440, 390):
                    context = browser.new_context(viewport={'width': width, 'height': 1000})
                    page = context.new_page()
                    errors = []
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    # No live sockets/presence, no external assets and no browser POSTs.
                    def route(request_route):
                        req = request_route.request
                        parsed = urlsplit(req.url)
                        if parsed.hostname != '127.0.0.1' or req.method != 'GET':
                            request_route.abort()
                            return
                        target = parsed.path + ('?' + parsed.query if parsed.query else '')
                        if target.startswith('/socket.io/'):
                            request_route.fulfill(status=503, body='Offline review')
                            return
                        response = clients[role].get(target)
                        request_route.fulfill(status=response.status_code, headers=dict(response.headers), body=response.data)
                    page.route('**/*', route)
                    page.goto('http://127.0.0.1:5000' + path, wait_until='networkidle')
                    baseline = page.get_by_text('Customer simulation baselines', exact=True)
                    if baseline.count():
                        baseline.click()
                        if page.evaluate('document.documentElement.scrollWidth > innerWidth + 1'):
                            failures.append(f'Expanded baseline table overflows at {width}px')
                    page.screenshot(path=str(out / f'{role}-{path.strip("/").replace("/", "-")}-{width}.png'), full_page=True)
                    if page.locator('.sidebar-item').count() and 'dashboard' in page.content():
                        for label in ('Transactions', 'Transaction Generation', 'Alerts', 'User Management', 'Watchlist', 'Activity Feed', 'Settings'):
                            button = page.get_by_role('button', name=label, exact=True)
                            if button.count():
                                if page.get_by_role('button', name='Toggle navigation').get_attribute('aria-expanded') != 'true':
                                    page.get_by_role('button', name='Toggle navigation').click()
                                button.click()
                                page.wait_for_timeout(80)
                                if page.evaluate('document.documentElement.scrollWidth > innerWidth + 1'):
                                    failures.append(f'Browser {role} section {label} overflows at {width}px')
                    overflow = page.evaluate('document.documentElement.scrollWidth > innerWidth + 1')
                    if errors or overflow:
                        failures.append(f'Browser {role} {path} {width}: errors={errors}, overflow={overflow}')
                    print(f'Browser {role} {path} {width}: {"FAIL" if errors or overflow else "PASS"}')
                    context.close()
            browser.close()
    after = fingerprint()
    if before != after:
        failures.append('Protected database contents changed during review')
    print('Protected database contents unchanged:', before == after)
    print('Failures:', failures)
    return 1 if failures else 0 if history_ready else 2


if __name__ == '__main__':
    raise SystemExit(main())
