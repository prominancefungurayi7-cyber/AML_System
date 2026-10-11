"""Guard the disposable retry command before any local write."""
from pathlib import Path

import pytest

from ml_v4.stage5c import verify_retry
from ml_v4.stage5c import migrate_retry_schema


def test_missing_binding_prevents_database_access(monkeypatch):
    for key in ('AML_PRIMARY_MODEL', 'V4_STAGE4T_EXPECTED_SERVER_UUID',
                'V4_STAGE4T_TEST_DB_URL'):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(verify_retry.v1, 'connection',
                        lambda *_: pytest.fail('Database connection attempted'))
    with pytest.raises(RuntimeError, match='not pinned'):
        verify_retry.preflight()


def test_read_only_mode_cannot_load_flask_or_submit_action(monkeypatch):
    monkeypatch.setattr(verify_retry, 'preflight', lambda: {
        'counts': {'transactions': 8}, 'source_revision': 'a' * 64})
    monkeypatch.setattr(verify_retry, 'load_test_application',
                        lambda: pytest.fail('Flask action loaded in read-only mode'))
    assert verify_retry.run(False)['status'] == 'READ_ONLY_READY'
    script = (Path(__file__).resolve().parents[1] /
              'ml_v4/stage5c/run_retry_verification.ps1').read_text(encoding='utf-8')
    assert '[switch]$Apply' in script
    assert "if ($Apply) { $env:STAGE5C_RETRY_APPLY = 'YES' }" in script
    assert 'v4_stage4s_disposable' in script and 'v4_stage4t_runner' in script


def test_schema_migration_requires_explicit_disposable_binding(monkeypatch):
    monkeypatch.delenv('STAGE5C_SCHEMA_APPLY', raising=False)
    monkeypatch.setattr(migrate_retry_schema.v1, 'connection',
                        lambda *_: pytest.fail('Database connection attempted'))
    with pytest.raises(RuntimeError, match='Explicit disposable schema authority'):
        migrate_retry_schema.run()
    ddl = migrate_retry_schema.SQL.read_text(encoding='utf-8')
    assert 'CREATE TABLE v4_stage4s_disposable.v4_primary_attempt_events' in ddl
    assert 'v4_retry_no_update' in ddl and 'v4_retry_no_delete' in ddl
    assert 'production aml' in ddl and 'CREATE DATABASE' not in ddl
    launcher = (Path(__file__).resolve().parents[1] /
                'ml_v4/stage5c/run_retry_schema_migration.ps1').read_text(encoding='utf-8')
    assert 'if (-not $Apply)' in launcher and 'v4_stage4s_disposable' in launcher
