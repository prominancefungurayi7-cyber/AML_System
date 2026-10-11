"""Offline contract checks; no MySQL connection, fixture, or model load."""
import json
import subprocess
from types import SimpleNamespace

import pytest

import v4_shadow as production
from ml_v4.stage4sa import coordinator, harness
from ml_v4.test_binding import v1


def success(tx=7, probability=.2, scope=v1.SCOPE):
    value = production.error(tx, 'CHECK')
    value.update(status='success', prediction=int(probability >= .5),
                 suspicious_probability=probability,
                 decision='suspicious_pattern' if probability >= .5 else 'normal',
                 error_code=None, history_status='COMPLETE_VERIFIED',
                 observation_scope=scope, scope_revision=1,
                 source_revision='a' * 64,
                 event_timestamp='2026-10-09T00:00:00.000000Z',
                 history_complete_through={'key': ['2026-10-09T00:00:00.000000Z', tx]})
    return value


def test_exact_test_scope_and_all_production_checks():
    assert coordinator.validate_test(success(), 7)['observation_scope'] == v1.SCOPE
    assert production.validate(success(scope='controlled-prototype-v1'), 7)['status'] == 'success'
    assert coordinator.validate_test(success(probability=.8), 7)['prediction'] == 1
    with pytest.raises(ValueError):
        coordinator.validate_test(success(scope='controlled-prototype-v1'), 7)
    with pytest.raises(ValueError):
        coordinator.validate_test(success(scope='other'), 7)
    with pytest.raises(ValueError):
        coordinator.validate_test(success(scope=None), 7)
    bad = success()
    bad['prediction'] = 1
    with pytest.raises(ValueError):
        coordinator.validate_test(bad, 7)
    bad = success()
    bad['suspicious_probability'] = float('nan')
    with pytest.raises(ValueError):
        coordinator.validate_test(bad, 7)


def test_fixed_test_worker_and_failure_handling(monkeypatch):
    monkeypatch.setattr(v1, 'load_authority', lambda: {'server_uuid': 'test-server'})
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout=json.dumps(success()).encode(), stderr=b'')
    monkeypatch.setattr(subprocess, 'run', run)
    assert coordinator.invoke_test(7, 'a' * 64, 'test-server')['status'] == 'success'
    assert str(coordinator.WORKER) in calls[0]
    assert all('shadow_integration/worker.py' not in part.replace('\\', '/') for part in calls[0])
    assert coordinator.invoke_test(7, 'a' * 64, 'wrong')['status'] == 'inference_error'
    assert len(calls) == 1
    approved_worker_hash = coordinator.WORKER_SHA256
    monkeypatch.setattr(coordinator, 'WORKER_SHA256', '0' * 64)
    assert coordinator.invoke_test(7, 'a' * 64, 'test-server')['error_code'] == 'MODEL_INTEGRITY'
    monkeypatch.setattr(coordinator, 'WORKER_SHA256', approved_worker_hash)
    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired('fixed-worker', 60)
    monkeypatch.setattr(subprocess, 'run', timeout)
    assert coordinator.invoke_test(7, 'a' * 64, 'test-server')['error_code'] == 'RESOURCE_ERROR'
    monkeypatch.setattr(subprocess, 'run', lambda *_a, **_k: SimpleNamespace(
        returncode=0, stdout=b'{"status":"success","status":"success"}', stderr=b''))
    assert coordinator.invoke_test(7, 'a' * 64, 'test-server')['status'] == 'inference_error'


def test_startup_source_is_pinned_and_database_conflict_fails(monkeypatch):
    assert harness.source_without_startup()
    url = 'mysql://v4_stage4t_runner:offline@127.0.0.1:3306/v4_stage4s_disposable'
    monkeypatch.setenv('V4_STAGE4T_TEST_DB_URL', url)
    monkeypatch.setenv('V4_STAGE4T_EXPECTED_SERVER_UUID',
                       'd441b7bb-43f6-11f1-a2d8-0a0027000005')
    monkeypatch.setenv('DATABASE_URL', 'mysql://aml:offline@127.0.0.1/aml')
    with pytest.raises(RuntimeError):
        harness.load_test_application()
    monkeypatch.delenv('DATABASE_URL')
    monkeypatch.setenv('V4_SHADOW_ENABLED', 'ON')
    with pytest.raises(RuntimeError):
        harness.load_test_application()
    monkeypatch.setenv('V4_SHADOW_ENABLED', 'OFF')
    monkeypatch.setenv('V4_STAGE4T_TEST_DB_URL', 'mysql://v4_stage4t_runner:offline@127.0.0.1/aml')
    with pytest.raises(v1.BindingError):
        harness.load_test_application()


def test_offline_application_load_has_no_startup_or_database_connection(monkeypatch):
    url = 'mysql://v4_stage4t_runner:offline@127.0.0.1:3306/v4_stage4s_disposable'
    monkeypatch.setenv('V4_STAGE4T_TEST_DB_URL', url)
    monkeypatch.setenv('V4_STAGE4T_EXPECTED_SERVER_UUID',
                       'd441b7bb-43f6-11f1-a2d8-0a0027000005')
    monkeypatch.delenv('DATABASE_URL', raising=False)
    monkeypatch.delenv('MYSQL_URL', raising=False)
    monkeypatch.setenv('V4_SHADOW_ENABLED', 'OFF')
    old_hook = production.after_commit
    try:
        app = harness.load_test_application()
        assert app.config['DATABASE'] == url
        assert app.config['TESTING'] is True
        assert app.config['MONITOR_STOP'] is True
        assert production.after_commit is coordinator.after_commit
        assert app.config['DATABASE_URL'] == url
        health = app.test_client().get('/health')
        assert health.status_code == 200
        assert health.json['database'] == v1.DATABASE
        assert 'offline' not in health.get_data(as_text=True)
        with pytest.raises(RuntimeError):
            app.run()
        with pytest.raises(RuntimeError):
            app.extensions['stage4sa_connection']('mysql://aml:offline@127.0.0.1/aml')
    finally:
        production.after_commit = old_hook
        monkeypatch.delenv('DATABASE_URL', raising=False)
        monkeypatch.delenv('MYSQL_URL', raising=False)


def test_post_commit_shadow_failure_does_not_raise(monkeypatch):
    monkeypatch.setattr(coordinator, 'process_test', lambda *_a: (_ for _ in ()).throw(RuntimeError()))
    messages = []
    app = SimpleNamespace(logger=SimpleNamespace(error=lambda *args: messages.append(args)))
    assert coordinator.after_commit(app, None, 7, None) is None
    assert len(messages) == 1


def test_missing_authority_fails_before_test_worker(monkeypatch):
    def unavailable():
        raise v1.BindingError('Missing test authority')
    monkeypatch.setattr(v1, 'load_authority', unavailable)
    monkeypatch.setattr(subprocess, 'run', lambda *_a, **_k: pytest.fail('Worker launched without authority'))
    result = coordinator.invoke_test(7, 'a' * 64, 'test-server')
    assert result['status'] == 'inference_error'
    assert result['prediction'] is None
    assert result['suspicious_probability'] is None
