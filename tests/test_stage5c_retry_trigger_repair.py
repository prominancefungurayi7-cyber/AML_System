"""Offline tests for trigger-only completion after the partial MySQL DDL."""
from copy import deepcopy
from pathlib import Path

import pytest

from ml_v4.stage5c import repair_retry_triggers as repair


def reviewed_before():
    return {
        'status': 'READ_ONLY_INSPECTION',
        'identity': {'database': 'v4_stage4s_disposable',
                     'server_uuid': repair.UUID,
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
                   'primary_key': True, 'unique_index': True, 'staff_index': True,
                   'foreign_keys': True, 'checks': True,
                   'append_only_triggers': False},
        'current_source_revision': 'a' * 64,
    }


def test_connector_parses_each_repaired_trigger_as_one_statement():
    from mysql.connector._scripting import MySQLScriptSplitter
    for sql in repair.TRIGGER_SQL:
        assert len(MySQLScriptSplitter(sql.encode()).split_script()) == 1
        assert "FOR EACH ROW SIGNAL SQLSTATE '45000'" in sql
        assert 'BEGIN' not in sql and 'DELIMITER' not in sql
    reviewed = Path(repair.__file__).with_name('retry_audit_schema_disposable.sql').read_text()
    assert reviewed.count("FOR EACH ROW SIGNAL SQLSTATE '45000'") == 2


@pytest.mark.parametrize('change', [
    lambda d: d['actual_triggers'].append({'TRIGGER_NAME': 'v4_retry_no_update'}),
    lambda d: d.update(audit_row_count=1),
    lambda d: d['required_ddl_grants'].update(TRIGGER=False),
    lambda d: d['checks'].update(foreign_keys=False),
    lambda d: d.update(history_freshness='UNKNOWN'),
    lambda d: d['financial_history_counts'].update(transactions=9),
])
def test_repair_rejects_unreviewed_state(change):
    result = reviewed_before()
    change(result)
    with pytest.raises(RuntimeError, match='preconditions changed'):
        repair.guard_before(result)


def test_trigger_only_execution_and_postcheck(monkeypatch):
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
            if sql.startswith('SELECT GET_LOCK'):
                return self
            return self

        def fetchone(self):
            return {'acquired': 1}

        def rollback(self):
            pass

        def close(self):
            pass

    conn = Conn()
    views = iter([(before, {'a': 'b'}), (before, {'a': 'b'}),
                  (after, {'a': 'b'})])
    monkeypatch.setenv('STAGE5C_TRIGGER_REPAIR_APPLY', 'YES')
    monkeypatch.setenv('V4_STAGE4T_EXPECTED_SERVER_UUID', repair.UUID)
    monkeypatch.setenv('V4_STAGE4T_TEST_DB_URL',
                       'mysql://v4_stage4t_runner:x@127.0.0.1:3306/v4_stage4s_disposable')
    for key in ('DATABASE_URL', 'MYSQL_URL', 'V4_STAGE4SK_RECOVERY_DB_URL',
                'STAGE5C_SCHEMA_APPLY'):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(repair.v1, 'load_authority',
                        lambda: {'server_uuid': repair.UUID})
    monkeypatch.setattr(repair.v1, 'connection', lambda *_: conn)
    monkeypatch.setattr(repair, 'snapshot', lambda *_: next(views))
    result = repair.run()
    assert result['status'] == 'PASS'
    writes = [sql for sql in conn.sql if sql.startswith('CREATE')]
    assert writes == list(repair.TRIGGER_SQL)


def test_missing_authority_never_connects(monkeypatch):
    monkeypatch.delenv('STAGE5C_TRIGGER_REPAIR_APPLY', raising=False)
    monkeypatch.setattr(repair.v1, 'connection',
                        lambda *_: pytest.fail('Database connection attempted'))
    with pytest.raises(RuntimeError, match='authority required'):
        repair.run()


def test_launcher_requires_apply_and_is_disposable_only():
    script = Path(repair.__file__).with_name('run_repair_retry_triggers.ps1').read_text()
    assert 'if (-not $Apply)' in script
    assert 'v4_stage4s_disposable' in script
    assert 'repair_retry_triggers --apply' in script
    assert 'migrate_retry_schema' not in script
