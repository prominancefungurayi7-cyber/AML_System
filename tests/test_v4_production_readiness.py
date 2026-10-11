"""Offline guards for the read-only production checker."""
import pytest

from ml_v4 import production_readiness as readiness


def test_missing_or_conflicting_binding_stops_before_database(monkeypatch):
    for key in ('V4_READINESS_HOST', 'V4_READINESS_USER', 'V4_READINESS_PASSWORD',
                'V4_READINESS_UUID', 'V4_READINESS_PRINCIPAL'):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(RuntimeError, match='binding required'):
        readiness.binding()
    for key, value in {'V4_READINESS_HOST': 'db.example',
                       'V4_READINESS_USER': 'reader',
                       'V4_READINESS_PASSWORD': 'unused-test-secret',
                       'V4_READINESS_UUID': 'd441b7bb-43f6-11f1-a2d8-0a0027000005',
                       'V4_READINESS_PRINCIPAL': 'reader@localhost'}.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv('V4_STAGE4T_TEST_DB_URL', 'mysql://test@localhost/test')
    with pytest.raises(RuntimeError, match='Conflicting'):
        readiness.binding()


def test_identity_requires_exact_database_uuid_principal_and_select_grant():
    class Connection:
        def __init__(self, db='aml', uuid='pin', principal='reader@localhost', grant=True):
            self.db, self.uuid, self.principal, self.grant = db, uuid, principal, grant
        def execute(self, sql):
            self.sql = sql
            return self
        def fetchone(self):
            return {'db': self.db, 'server_uuid': self.uuid, 'principal': self.principal}
        def fetchall(self):
            return [{'grant': 'GRANT SELECT, INSERT, UPDATE ON `aml`.* TO `reader`@`localhost`'}] if self.grant else []
    pin = {'V4_READINESS_UUID': 'pin', 'V4_READINESS_PRINCIPAL': 'reader@localhost'}
    assert readiness.verify_identity(Connection(), pin)['db'] == 'aml'
    for conn in (Connection(db='v4_stage4s_disposable'), Connection(uuid='wrong'),
                 Connection(principal='other@localhost'), Connection(grant=False)):
        with pytest.raises(RuntimeError):
            readiness.verify_identity(conn, pin)


def test_readiness_never_attempts_connection_without_rule_policy(monkeypatch):
    for key in ('V4_READINESS_HOST', 'V4_READINESS_USER', 'V4_READINESS_PASSWORD',
                'V4_READINESS_UUID', 'V4_READINESS_PRINCIPAL'):
        monkeypatch.setenv(key, 'dummy')
    monkeypatch.setenv('V4_READINESS_UUID', 'd441b7bb-43f6-11f1-a2d8-0a0027000005')
    monkeypatch.setenv('V4_READINESS_PRINCIPAL', 'reader@localhost')
    for key in ('DATABASE_URL', 'MYSQL_URL', 'V4_STAGE4T_TEST_DB_URL',
                'AML_RULE_ENGINE_ENABLED', 'AML_PRIMARY_MODEL'):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv('SOCKETIO_ALLOWED_ORIGINS', 'https://aml.example.test')
    monkeypatch.setattr(readiness, 'MODEL_SHA', 'wrong')
    with pytest.raises(RuntimeError, match='model hash'):
        readiness.run()
    monkeypatch.setenv('SOCKETIO_ALLOWED_ORIGINS', '*')
    with pytest.raises(RuntimeError, match='HTTPS Socket.IO origins'):
        readiness.run()
