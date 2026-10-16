"""Nonfinancial recovery parsing and read-only worker authority regressions."""
import hashlib
import json

import pytest

from tools.recover_local_v4_history import read_backup, sql_values


def test_pinned_backup_satisfies_unchanged_history_gate():
    columns, rows = read_backup()
    assert len(rows['transactions']) == 7800
    assert len(rows['alerts']) == 415
    assert len(rows['users']) == 18
    assert rows['cmm_source_changes'] == []
    assert 'password_hash' in columns['users']
    assert all(type(row['risk_score']) is float for row in rows['alerts'])
    assert all(type(row['balance']) is float for row in rows['users'])


def test_dump_literals_preserve_strings_and_reject_expressions():
    assert sql_values(r"(1,'a\'b','c\\d','line\nnext',NULL,0.01);") == [
        1, "a'b", 'c\\d', 'line\nnext', None, .01]
    for text in ('(1,NOW());', '(1); DELETE FROM users;', '(1),(2);'):
        with pytest.raises(ValueError):
            sql_values(text)


@pytest.mark.parametrize('grants,allowed', [
    (['GRANT USAGE ON *.* TO user', 'GRANT ALL PRIVILEGES ON `aml`.* TO user'], True),
    (['GRANT ALL PRIVILEGES ON *.* TO user'], False),
    (['GRANT SELECT ON `aml`.* TO user'], False),
    (['GRANT ALL PRIVILEGES ON `other`.* TO user'], False),
])
def test_readiness_understands_schema_all_without_allowing_global_privileges(grants, allowed):
    from ml_v4.production_readiness import verify_identity
    class Rows:
        def fetchone(self):
            return {'db': 'aml', 'server_uuid': 'fixture', 'principal': 'aml@127.0.0.1'}
        def fetchall(self):
            return [{'grant': grant} for grant in grants]
    class Connection:
        def execute(self, query):
            assert query.startswith(('SELECT ', 'SHOW '))
            return Rows()
    expected = {'V4_READINESS_UUID': 'fixture', 'V4_READINESS_PRINCIPAL': 'aml@127.0.0.1'}
    if allowed:
        assert verify_identity(Connection(), expected)['db'] == 'aml'
    else:
        with pytest.raises(RuntimeError):
            verify_identity(Connection(), expected)


@pytest.mark.parametrize('ready', [True, False])
def test_v4_startup_never_migrates_or_reseeds_and_stops_on_failed_gate(monkeypatch, ready):
    import ast
    from pathlib import Path
    import v4_primary
    tree = ast.parse(Path('server.py').read_text(encoding='utf-8'))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == 'initialize_startup')
    calls = []
    def gate(_factory):
        calls.append('readiness')
        if not ready:
            raise RuntimeError('History unavailable')
    monkeypatch.setattr(v4_primary, 'verify_startup', gate)
    def forbidden():
        pytest.fail('V4 startup attempted schema migration or account reseeding')
    namespace = {'v4_primary_enabled': lambda: True, 'connect_db': object(),
                 'init_db': forbidden, 'seed_demo_data': forbidden,
                 'ensure_ai_model_ready': lambda: calls.append('model'),
                 'ensure_background_monitor': lambda: calls.append('monitor')}
    exec(compile(ast.Module(body=[function], type_ignores=[]), 'server.py', 'exec'), namespace)
    if ready:
        namespace['initialize_startup']()
        assert calls == ['readiness', 'model', 'monitor']
    else:
        with pytest.raises(RuntimeError, match='History unavailable'):
            namespace['initialize_startup']()
        assert calls == ['readiness']


@pytest.mark.parametrize('authority,captures,ok', [
    ('configured-db-identity:aml@127.0.0.1', ['SOURCE_INSERT', 'CANONICAL_INSERT'], True),
    ('automatic-shadow-technical-reassessment', ['SOURCE_INSERT', 'CANONICAL_INSERT'], False),
    ('configured-db-identity:aml@127.0.0.1', ['SOURCE_INSERT'], False),
])
def test_worker_keeps_existing_authority_without_any_database_writes(monkeypatch, authority, captures, ok):
    from ml_v4.shadow_integration.worker import main
    import ml_v4.frozen_inference.service as service
    import ml_v4.frozen_inference.cli as cli
    import ml_v4.frozen_inference.history as history
    import canonical_history_store as store

    row = {'transaction_id': 1}
    digest = hashlib.sha256(json.dumps(row, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    events = []

    class Result:
        def __init__(self, rows):
            self.rows = rows
        def fetchone(self):
            return self.rows[0]
        def fetchall(self):
            return self.rows

    class Connection:
        def execute(self, sql, params=()):
            assert sql.startswith('SELECT '), 'Worker attempted a database write'
            if '@@server_uuid' in sql:
                return Result([{'uuid': 'fixture', 'principal': 'aml@127.0.0.1'}])
            if 'canonical_mobile_money_events' in sql:
                return Result([row])
            if 'cmm_source_changes' in sql:
                return Result([{'operation': value} for value in captures])
            raise AssertionError(sql)
        def rollback(self):
            events.append('rollback')
        def close(self):
            events.append('close')

    monkeypatch.setattr(service, 'runtime', lambda: None)
    monkeypatch.setattr(cli, 'connection', Connection)
    monkeypatch.setattr(history, 'verified_snapshot', lambda *_: events.append('verified_snapshot'))
    monkeypatch.setattr(store, 'current_scope', lambda *_: {'verification_authority': authority})
    monkeypatch.setattr(store, 'latest', lambda *_: {'verification_authority': authority})
    monkeypatch.setattr(store, 'attest', lambda *_: pytest.fail('Worker replaced the history authority'))
    monkeypatch.setattr(service, 'infer', lambda *_: events.append('infer') or {'status': 'success'})
    result = main(1, digest, 'fixture')
    assert events[:3] == ['verified_snapshot', 'rollback', 'close']
    if ok:
        assert result['status'] == 'success'
        assert events[-1] == 'infer'
    else:
        assert result['error_code'] == 'HISTORY_INCOMPLETE'
        assert result['prediction'] is None
        assert 'infer' not in events
