"""Offline guards for administrator-only completion of disposable audit triggers."""
from copy import deepcopy
from pathlib import Path

import pytest

from ml_v4.stage5c import admin_repair_retry_triggers as admin_repair


def reviewed_before():
    return {
        'status': 'READ_ONLY_INSPECTION',
        'identity': {'database': 'v4_stage4s_disposable',
                     'server_uuid': admin_repair.UUID,
                     'principal': 'v4_stage4t_runner@127.0.0.1'},
        'server_version': '8.0.46', 'state': 'PARTIAL_DDL_OR_SCHEMA_MISMATCH',
        'actual_triggers': [], 'audit_row_count': 0,
        'parent_id_types': {'transactions': 'bigint', 'users': 'bigint'},
        'financial_history_counts': {'transactions': 8,
                                     'canonical_mobile_money_events': 8,
                                     'cmm_source_changes': 16,
                                     'v4_shadow_results': 8},
        'current_history_status': 'COMPLETE_VERIFIED',
        'history_issues': [], 'history_freshness': 'COMPLETE_VERIFIED',
        'required_ddl_grants': {'CREATE': True, 'REFERENCES': True, 'TRIGGER': True},
        'checks': {'table_innodb': True, 'columns_order': True, 'column_types': True,
                   'nullable_fields': True, 'request_key_ascii_bin': True,
                   'event_id_auto_increment': True, 'primary_key': True,
                   'index_names': True, 'unique_index': True, 'staff_index': True,
                   'foreign_keys': True, 'checks': True,
                   'append_only_triggers': False},
        'current_source_revision': 'a' * 64,
    }


def test_admin_requires_existing_super_and_disposable_trigger():
    grants = ["GRANT USAGE ON *.* TO 'operator'@'localhost'",
              "GRANT TRIGGER ON `v4_stage4s_disposable`.* TO 'operator'@'localhost'"]
    assert not admin_repair.admin_grants_ok(grants)
    grants.append("GRANT SUPER ON *.* TO 'operator'@'localhost'")
    assert admin_repair.admin_grants_ok(grants)
    assert not admin_repair.admin_grants_ok([
        "GRANT SUPER ON *.* TO 'operator'@'localhost'",
        "GRANT TRIGGER ON `aml`.* TO 'operator'@'localhost'"])


def test_admin_connection_policy_rejects_changed_global_trust():
    class Conn:
        def execute(self, sql):
            if sql.startswith('SELECT DATABASE()'):
                return self
            return self

        def fetchone(self):
            return {'db': 'v4_stage4s_disposable',
                    'server_uuid': admin_repair.UUID,
                    'principal': 'operator@localhost', 'version': '8.0.46',
                    'log_bin': 1, 'trust': 1}

    with pytest.raises(RuntimeError, match='binary-log policy'):
        admin_repair.verify_admin(Conn(), 'operator')


def test_admin_run_creates_only_two_disposable_triggers(monkeypatch):
    before = reviewed_before()
    after = deepcopy(before)
    after['state'] = 'COMPLETE'
    after['checks']['append_only_triggers'] = True
    after['actual_triggers'] = [{'TRIGGER_NAME': 'v4_retry_no_update'},
                                {'TRIGGER_NAME': 'v4_retry_no_delete'}]

    class Conn:
        def __init__(self):
            self.sql = []

        def execute(self, sql, params=()):
            self.sql.append(sql)
            return self

        def fetchone(self):
            return {'acquired': 1}

        def fetchall(self):
            return [{'TRIGGER_NAME': 'v4_retry_no_update',
                     'DEFINER': 'v4_stage4t_runner@127.0.0.1'},
                    {'TRIGGER_NAME': 'v4_retry_no_delete',
                     'DEFINER': 'v4_stage4t_runner@127.0.0.1'}]

        def rollback(self):
            pass

        def close(self):
            pass

    restricted = Conn()
    administrator = Conn()
    views = iter([(before, {'rows': 'same'}), (before, {'rows': 'same'}),
                  (after, {'rows': 'same'})])
    monkeypatch.setenv('STAGE5C_ADMIN_TRIGGER_APPLY', 'YES')
    monkeypatch.setenv('STAGE5C_ADMIN_USER', 'operator')
    monkeypatch.setenv('V4_STAGE4T_EXPECTED_SERVER_UUID', admin_repair.UUID)
    monkeypatch.setenv('V4_STAGE4T_TEST_DB_URL',
                       'mysql://v4_stage4t_runner:x@127.0.0.1:3306/v4_stage4s_disposable')
    for key in ('DATABASE_URL', 'MYSQL_URL', 'V4_STAGE4SK_RECOVERY_DB_URL',
                'STAGE5C_SCHEMA_APPLY', 'STAGE5C_TRIGGER_REPAIR_APPLY'):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(admin_repair.v1, 'load_authority',
                        lambda: {'server_uuid': admin_repair.UUID})
    monkeypatch.setattr(admin_repair.v1, 'connection', lambda *_: restricted)
    monkeypatch.setattr(admin_repair, 'admin_connection', lambda *_: administrator)
    monkeypatch.setattr(admin_repair, 'verify_admin',
                        lambda *_: {'principal': 'operator@localhost', 'trust': 0})
    monkeypatch.setattr(admin_repair.repair, 'snapshot', lambda *_: next(views))
    result = admin_repair.run()
    assert result['status'] == 'PASS'
    writes = [sql for sql in administrator.sql if sql.startswith('CREATE')]
    assert len(writes) == 2
    assert all(sql.startswith("CREATE DEFINER='v4_stage4t_runner'@'127.0.0.1' TRIGGER ")
               for sql in writes)
    assert all('v4_stage4s_disposable.v4_primary_attempt_events' in sql for sql in writes)
    assert not any(sql.startswith(('SET GLOBAL', 'GRANT', 'DROP', 'ALTER'))
                   for sql in administrator.sql)


def test_missing_apply_never_connects(monkeypatch):
    monkeypatch.delenv('STAGE5C_ADMIN_TRIGGER_APPLY', raising=False)
    monkeypatch.setattr(admin_repair.v1, 'connection',
                        lambda *_: pytest.fail('Database connection attempted'))
    with pytest.raises(RuntimeError, match='authority required'):
        admin_repair.run()


def test_launcher_uses_two_secure_prompts_and_no_global_setting():
    script = Path(admin_repair.__file__).with_name(
        'run_admin_repair_retry_triggers.ps1').read_text()
    assert script.count('-AsSecureString') == 2
    assert 'STAGE5C_ADMIN_PASSWORD' in script
    assert 'admin_repair_retry_triggers --apply' in script
    assert 'SET GLOBAL' not in script and 'GRANT ' not in script
