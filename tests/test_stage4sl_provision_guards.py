"""Offline guards for recovery-only administrator provisioning."""
import pytest

from ml_v4.stage4sg.provision_recovery import (
    CREATE_DATABASE_SQL, CREATE_USER_SQL, GRANT_SQL, provision,
)
from ml_v4.stage4sg.recovery_guard import REQUIRED, UUID, grant_check


class FakeCursor:
    def __init__(self, *, uuid=UUID, schema_exists=False, account_exists=False):
        self.uuid = uuid
        self.schema_exists = schema_exists
        self.account_exists = account_exists
        self.calls = []
        self.last = ''

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        self.last = sql

    def fetchone(self):
        if 'CURRENT_USER()' in self.last:
            return {'uuid': self.uuid, 'principal': 'admin@localhost'}
        if 'information_schema.SCHEMATA' in self.last:
            return {'SCHEMA_NAME': 'v4_stage4sk_recovery'} if self.schema_exists else None
        if 'mysql.user' in self.last:
            return {'User': 'v4_stage4sk_restore'} if self.account_exists else None
        if '@@server_uuid' in self.last:
            return {'uuid': self.uuid}
        raise AssertionError(self.last)

    def fetchall(self):
        if self.last.startswith('SHOW GRANTS'):
            return [{'grant': 'GRANT USAGE ON *.* TO x'},
                    {'grant': 'GRANT ' + ', '.join(sorted(REQUIRED)) +
                     ' ON `v4_stage4sk_recovery`.* TO x'}]
        if self.last.startswith('SHOW FULL TABLES'):
            return []
        raise AssertionError(self.last)

    def close(self):
        pass


class FakeConnection:
    def __init__(self, **kwargs):
        self.fake = FakeCursor(**kwargs)

    def cursor(self, dictionary=False):
        assert dictionary
        return self.fake


@pytest.mark.parametrize('kwargs', [
    {'uuid': 'wrong'}, {'schema_exists': True}, {'account_exists': True},
])
def test_preexisting_state_or_wrong_server_blocks_before_ddl(kwargs):
    connection = FakeConnection(**kwargs)
    with pytest.raises(ValueError):
        provision(connection, 'long-secret-value-for-test')
    sql = [statement for statement, _ in connection.fake.calls]
    assert CREATE_DATABASE_SQL not in sql
    assert CREATE_USER_SQL not in sql
    assert GRANT_SQL not in sql


def test_exact_recovery_only_ddl_and_parameterized_password():
    connection = FakeConnection()
    password = 'long-secret-value-for-test'
    result = provision(connection, password)
    sql = [statement for statement, _ in connection.fake.calls]
    assert result['status'] == 'PROVISIONED_EMPTY_RECOVERY'
    assert [s for s in sql if s in (CREATE_DATABASE_SQL, CREATE_USER_SQL, GRANT_SQL)] == [
        CREATE_DATABASE_SQL, CREATE_USER_SQL, GRANT_SQL]
    assert all('`aml`' not in s and 'v4_stage4s_disposable' not in s for s in sql)
    assert all(password not in s for s in sql)
    assert (CREATE_USER_SQL, (password,)) in connection.fake.calls


def test_short_password_blocks_before_ddl():
    connection = FakeConnection()
    with pytest.raises(ValueError):
        provision(connection, 'short')
    assert CREATE_DATABASE_SQL not in [s for s, _ in connection.fake.calls]


def test_exact_grant_verification_rejects_even_scoped_extra_privilege():
    lines = ['GRANT USAGE ON *.* TO x',
             'GRANT ' + ', '.join(sorted(REQUIRED | {'CREATE VIEW'})) +
             ' ON `v4_stage4sk_recovery`.* TO x']
    with pytest.raises(ValueError, match='beyond exact'):
        grant_check(lines, exact=True)
