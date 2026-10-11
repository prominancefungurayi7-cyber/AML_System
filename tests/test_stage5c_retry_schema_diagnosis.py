"""Offline guards for interrupted disposable retry DDL diagnosis."""
from pathlib import Path

import pytest

from ml_v4.stage5c import inspect_retry_schema as diagnostic
from ml_v4.stage5c import migrate_retry_schema as migration


def test_mysql_failure_reports_step_code_and_sanitized_message():
    class DatabaseError(Exception):
        errno = 1142
        sqlstate = '42000'
        msg = 'CREATE denied; password=secret mysql://u:secret@localhost/db'

    record = migration.failure_record(
        migration.MigrationStepError('create_audit_table', DatabaseError()))
    assert record['operation'] == 'create_audit_table'
    assert record['mysql_errno'] == 1142
    assert record['mysql_sqlstate'] == '42000'
    assert 'CREATE denied' in record['mysql_message']
    assert 'secret' not in record['mysql_message']


def test_failure_step_is_captured_before_any_automatic_retry(monkeypatch):
    class DatabaseError(Exception):
        errno = 1005
        sqlstate = 'HY000'
        msg = 'Cannot create table'

    class Conn:
        def rollback(self):
            pass

        def close(self):
            pass

        def execute(self, sql):
            if sql.startswith('CREATE TABLE'):
                raise DatabaseError()
            pytest.fail('Unexpected SQL after failed DDL')

    monkeypatch.setenv('STAGE5C_SCHEMA_APPLY', 'YES')
    monkeypatch.setenv('V4_STAGE4T_EXPECTED_SERVER_UUID', migration.UUID)
    monkeypatch.setenv('V4_STAGE4T_TEST_DB_URL',
                       'mysql://v4_stage4t_runner:x@127.0.0.1:3306/v4_stage4s_disposable')
    monkeypatch.delenv('DATABASE_URL', raising=False)
    monkeypatch.delenv('MYSQL_URL', raising=False)
    monkeypatch.setattr(migration.v1, 'load_authority',
                        lambda: {'server_uuid': migration.UUID})
    monkeypatch.setattr(migration.v1, 'connection', lambda *_: Conn())
    monkeypatch.setattr(migration, 'preflight', lambda *_: {})
    with pytest.raises(migration.MigrationStepError) as failed:
        migration.run()
    assert failed.value.operation == 'create_audit_table'
    assert migration.failure_record(failed.value)['mysql_errno'] == 1005


def test_inspector_requires_pinned_disposable_binding(monkeypatch):
    monkeypatch.delenv('V4_STAGE4T_EXPECTED_SERVER_UUID', raising=False)
    monkeypatch.setattr(diagnostic.v1, 'connection',
                        lambda *_: pytest.fail('Database connection attempted'))
    with pytest.raises(RuntimeError, match='not pinned'):
        diagnostic.run()


def test_ddl_grants_are_scoped_and_read_only_launcher_has_no_apply():
    grants = ["GRANT USAGE ON *.* TO `v4_stage4t_runner`@`127.0.0.1`",
              "GRANT SELECT, INSERT, CREATE, REFERENCES, TRIGGER ON `v4_stage4s_disposable`.* TO `v4_stage4t_runner`@`127.0.0.1`"]
    assert diagnostic.ddl_grants(grants) == {
        'CREATE': True, 'REFERENCES': True, 'TRIGGER': True}
    script = (Path(__file__).resolve().parents[1] /
              'ml_v4/stage5c/run_inspect_retry_schema.ps1').read_text()
    assert 'run_retry_schema_migration' not in script
    assert 'inspect_retry_schema' in script
    assert 'v4_stage4s_disposable' in script
    assert ' -Apply' not in script
