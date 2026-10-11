"""Exercise the actual staff route functions without a database or server startup."""
import ast
from pathlib import Path
import hmac
import uuid
from functools import wraps

from flask import Flask, jsonify, redirect, request, session, url_for, flash

import v4_retry
import v4_shadow


def app_fixture(monkeypatch):
    app = Flask(__name__)
    app.secret_key = 'offline-route-only'
    app.add_url_rule('/login', endpoint='login', view_func=lambda: 'login')
    app.add_url_rule('/dashboard', endpoint='dashboard_redirect', view_func=lambda: 'dashboard')
    role = {'value': 'customer'}
    class DB:
        def execute(self, sql, params=()):
            self.sql = sql
            return self
        def fetchone(self):
            return {'id': 1, 'ai_risk_level': 'inference_error',
                    'risk_level': 'pending_review'}
        def fetchall(self):
            return []
    namespace = {'app': app, 'wraps': wraps, 'session': session,
                 'flash': flash, 'redirect': redirect, 'url_for': url_for,
                 'request': request, 'jsonify': jsonify, 'hmac': hmac, 'uuid': uuid,
                 'v4_primary_enabled': lambda: True,
                 'get_user_by_id': lambda _id: {'id': 3, 'role': role['value']},
                 'get_db': lambda: DB(), 'connect_db': lambda: None,
                 '_notify_v4_decision': lambda _result: None}
    source = (Path(__file__).resolve().parents[1] / 'server.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and
                node.name in ('login_required', 'v4_error_case', 'v4_error_action')]
    exec(compile(ast.Module(body=selected, type_ignores=[]), '<staff-routes>', 'exec'), namespace)
    monkeypatch.setattr(v4_retry, 'require_schema', lambda _db: None)
    monkeypatch.setattr(v4_shadow, 'get', lambda _db, _tx: {'status': 'inference_error',
                                                            'error_code': 'INFERENCE_ERROR'})
    return app, role


def test_customer_denied_and_staff_csrf_required(monkeypatch):
    app, role = app_fixture(monkeypatch)
    client = app.test_client()
    assert client.get('/compliance/v4-error/1').status_code == 302
    with client.session_transaction() as state:
        state['user_id'] = 3
    assert client.get('/compliance/v4-error/1').status_code == 302
    assert client.post('/compliance/v4-error/1/retry').status_code == 302
    role['value'] = 'compliance'
    case = client.get('/compliance/v4-error/1')
    assert case.status_code == 200
    token = case.json['csrf_token']
    assert client.post('/compliance/v4-error/1/retry', data={'csrf_token': 'wrong'}).status_code == 403
    calls = []
    monkeypatch.setattr(v4_retry, 'retry', lambda _factory, tx, staff, key, **_kw:
                        calls.append(('retry', tx, staff, key)) or {'status': 'inference_error'})
    monkeypatch.setattr(v4_retry, 'close', lambda _factory, tx, staff, key, reason:
                        calls.append(('close', tx, staff, key, reason)) or {'status': 'closed'})
    key = str(uuid.uuid4())
    assert client.post('/compliance/v4-error/1/retry', data={
        'csrf_token': token, 'request_key': key}).status_code == 200
    assert client.post('/compliance/v4-error/1/close', data={
        'csrf_token': token, 'request_key': str(uuid.uuid4()),
        'reason': 'Reviewed and closed manually'}).status_code == 200
    assert calls[0] == ('retry', 1, 3, key)
    assert calls[1][:3] == ('close', 1, 3)
