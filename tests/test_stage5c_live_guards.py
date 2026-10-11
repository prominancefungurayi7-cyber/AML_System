"""Offline checks for the guarded disposable Stage5C launcher."""
from pathlib import Path
import ast

import pytest

from ml_v4.stage5c import live_primary


def test_missing_local_binding_fails_before_any_database_access(monkeypatch):
    for key in ('STAGE5C_EXECUTE', 'AML_PRIMARY_MODEL', 'V4_STAGE4T_TEST_DB_URL',
                'V4_STAGE4T_EXPECTED_SERVER_UUID', 'DATABASE_URL', 'MYSQL_URL'):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(live_primary.v1, 'connection', lambda *_a: pytest.fail(
        'Database connection attempted without local binding'))
    with pytest.raises(RuntimeError, match='environment not pinned'):
        live_primary.preflight()


def test_runner_requires_execute_and_explicit_rule_setting():
    script = (Path(__file__).resolve().parents[1] /
              'ml_v4/stage5c/run_live_primary.ps1').read_text(encoding='utf-8')
    assert '[switch]$Execute' in script
    assert '[switch]$InspectOnly' in script
    assert '[switch]$StartNewAfterReview' in script
    assert "[ValidateSet('On','Off')]" in script
    assert 'Run -InspectOnly first' in script
    assert 'Read-Host' in script and '-AsSecureString' in script
    assert 'v4_stage4s_disposable' in script
    assert 'd441b7bb-43f6-11f1-a2d8-0a0027000005' in script
    assert 'Remove-Item Env:V4_STAGE4T_TEST_DB_URL' in script
    assert 'mysql_migration' not in script and 'ALTER TABLE' not in script


def test_generic_transaction_socket_event_is_staff_only(monkeypatch):
    from flask import Flask
    from flask_socketio import SocketIO
    from realtime import RealtimeBroker
    monkeypatch.delenv('REDIS_URL', raising=False)
    monkeypatch.delenv('KAFKA_BOOTSTRAP_SERVERS', raising=False)
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'offline-test-only'
    socket = SocketIO(app, async_mode='threading')
    unauthenticated = socket.test_client(app)
    try:
        broker = RealtimeBroker(app, socket)
        roles = {1: 'customer', 2: 'compliance', 3: 'admin'}
        broker.set_staff_authorizer(lambda user_id: roles.get(user_id) in ('compliance', 'admin'))
        assert not broker.add_staff_socket('customer-sid', 1)
        assert broker.add_staff_socket('staff-sid', 2)
        delivered = []
        monkeypatch.setattr(socket, 'emit', lambda name, body, **kw: delivered.append((name, kw.get('to'))))
        broker.publish('transaction', {'ai_risk_level': 'suspicious_pattern'})
        assert delivered == [('transaction', 'staff-sid')]
        assert not any(event['name'] == 'transaction' for event in unauthenticated.get_received())
        roles[2] = 'customer'
        broker.publish('alert', {'risk_level': 'high_risk'})
        assert delivered == [('transaction', 'staff-sid')]
        assert 'staff-sid' not in broker._staff_sockets
    finally:
        unauthenticated.disconnect()


def test_realtime_broker_fails_closed_without_staff_authorizer(monkeypatch):
    from flask import Flask
    from realtime import RealtimeBroker
    monkeypatch.delenv('REDIS_URL', raising=False)
    monkeypatch.delenv('KAFKA_BOOTSTRAP_SERVERS', raising=False)
    class Socket:
        def __init__(self):
            self.sent = []
        def emit(self, *args, **kwargs):
            self.sent.append((args, kwargs))
    socket = Socket()
    broker = RealtimeBroker(Flask(__name__), socket)
    assert not broker.add_staff_socket('sid', 7)
    broker.publish('transaction', {'account_number': 'private'})
    assert socket.sent == []
    broker.set_staff_authorizer(lambda _uid: (_ for _ in ()).throw(RuntimeError('auth unavailable')))
    broker._staff_sockets['sid'] = 7
    broker.publish('alert', {'risk_level': 'critical'})
    assert socket.sent == []


def test_stream_and_socket_staff_authorization_are_bound_to_current_role():
    source = (Path(__file__).resolve().parents[1] / 'server.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    stream = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                  and node.name == 'stream')
    assert any(isinstance(decorator, ast.Call) and
               isinstance(decorator.func, ast.Name) and decorator.func.id == 'login_required' and
               [arg.value for arg in decorator.args] == ['compliance', 'admin']
               for decorator in stream.decorator_list)
    assert 'broker.add_staff_socket(sid, user_id)' in source
    assert 'broker.remove_staff_socket(request.sid)' in source
    assert 'broker"].set_staff_authorizer(_current_staff_socket_user)' in source


def test_primary_monitor_skips_legacy_stage14_path():
    source = (Path(__file__).resolve().parents[1] / 'server.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    monitor = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                   and node.name == 'monitor_transactions')
    body = ast.get_source_segment(source, monitor)
    assert body.index('if v4_primary_enabled():') < body.index('process_transaction_event(')
    assert 'continue' in body[body.index('if v4_primary_enabled():'):
                              body.index('process_transaction_event(')]


def test_new_fixtures_require_matching_read_only_review(tmp_path, monkeypatch):
    current = {'status': 'RECONCILED', 'fingerprint': 'fresh', 'baseline': {'counts': {}}}
    monkeypatch.setattr(live_primary, 'inspect_prior', lambda: current)
    monkeypatch.setattr(live_primary, 'REVIEW', tmp_path / 'review.json')
    monkeypatch.setattr(live_primary, 'OUT', tmp_path / 'run.json')
    monkeypatch.setattr(live_primary, 'load_test_application', lambda: pytest.fail(
        'Flask fixture started without matching read-only review'))
    with pytest.raises(RuntimeError, match='inspection required'):
        live_primary.run('on')
    (tmp_path / 'review.json').write_text(
        '{"status":"RECONCILED","fingerprint":"stale"}', encoding='utf-8')
    with pytest.raises(RuntimeError, match='inspection changed'):
        live_primary.run('on')
