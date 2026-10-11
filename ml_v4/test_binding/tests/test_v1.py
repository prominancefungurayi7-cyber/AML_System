"""No database connection, model load or application startup."""
import json
from pathlib import Path
from urllib.parse import urlparse
import pytest

from ml_v4.test_binding import v1
from ml_v4.frozen_inference import cli


class FakeConnection:
    def __init__(self, db=v1.DATABASE, server='test-server', principal=v1.USER + '@localhost',
                 grants=None, scope=None, trigger_rows=None):
        self.db, self.server, self.principal = db, server, principal
        self.grants = grants if grants is not None else [
            'GRANT USAGE ON *.* TO `v4_stage4t_runner`@`localhost`',
            'GRANT ALL PRIVILEGES ON `v4_stage4s_disposable`.* TO `v4_stage4t_runner`@`localhost`']
        self.scope = scope
        self.trigger_rows = trigger_rows

    def execute(self, query, params=()):
        if 'SELECT DATABASE()' in query:
            return Cursor([dict(db=self.db, server_id=self.server, principal=self.principal)])
        if query == 'SHOW GRANTS':
            return Cursor([{'Grants for user': grant} for grant in self.grants])
        if 'FROM cmm_observation_scopes' in query and 'COUNT(*)' in query:
            return Cursor([{'n': 1}])
        if 'FROM cmm_observation_scopes' in query:
            return Cursor([{'body': json.dumps(self.scope)}] if self.scope else [])
        if 'information_schema.TRIGGERS' in query:
            return Cursor(self.trigger_rows or [])
        raise AssertionError(query)


class Cursor:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


def test_config_requires_dedicated_database_and_account():
    v1.config('mysql://v4_stage4t_runner:secret@localhost/v4_stage4s_disposable')
    for url in ('mysql://v4_stage4t_runner:secret@localhost/aml',
                'mysql://aml:secret@localhost/v4_stage4s_disposable',
                'sqlite:///v4_stage4s_disposable', '',
                'mysql://v4_stage4t_runner:secret@localhost/v4_stage4s_disposable?x=1'):
        with pytest.raises(v1.BindingError):
            v1.config(url)


def test_production_connector_rejects_test_database_before_connect():
    # Exercise the unchanged production guard alone, without connection imports.
    import ast
    tree = ast.parse(Path(cli.__file__).read_text())
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'connection')
    guard = next(n for n in function.body if isinstance(n, ast.If))
    code = compile(ast.fix_missing_locations(ast.Module(body=[guard], type_ignores=[])), cli.__file__, 'exec')
    with pytest.raises(ValueError):
        exec(code, {'p': urlparse('mysql://v4_stage4t_runner:secret@localhost/v4_stage4s_disposable'),
                    'ValueError': ValueError, '__builtins__': {}})


def test_grants_reject_global_or_other_database():
    assert v1.grants_ok(FakeConnection().grants)
    for grant in ('GRANT SELECT ON *.* TO `v4_stage4t_runner`@`localhost`',
                  'GRANT SELECT ON `aml`.* TO `v4_stage4t_runner`@`localhost`',
                  'GRANT ALL PRIVILEGES ON `v4_stage4s_disposable`.* TO `v4_stage4t_runner`@`localhost` WITH GRANT OPTION'):
        assert not v1.grants_ok([grant])


@pytest.mark.parametrize('change', [dict(db='aml'), dict(server='wrong'),
                                    dict(principal='aml@localhost'),
                                    dict(grants=['GRANT SELECT ON `aml`.* TO `v4_stage4t_runner`@`localhost`'])])
def test_identity_rejects_wrong_db_server_user_or_grants(change):
    with pytest.raises(v1.BindingError):
        v1.identity(FakeConnection(**change), 'test-server')


def test_pinned_boundary_rejects_wrong_or_missing(monkeypatch):
    import canonical_history_store
    immutable = dict(scope_id=v1.SCOPE, scope_version='prototype.observation.v1',
                     start_timestamp='2026-10-09T00:00:00.000000Z',
                     start_transaction_id_exclusive=0,
                     source_ledger='application.transactions+canonical_mobile_money_events',
                     canonical_version='mobile_money.canonical.v1',
                     preexisting_parent_ids=[], preexisting_change_ids=[])
    scope = dict(immutable, revision=1, verification_authority=v1.VERSION)
    authority = dict(boundary_digest=v1._digest(immutable))
    monkeypatch.setattr(canonical_history_store, 'current_scope', lambda c, s: c.scope)
    assert v1._boundary(FakeConnection(scope=scope), authority) == scope
    with pytest.raises(v1.BindingError):
        v1._boundary(FakeConnection(scope=dict(scope, start_transaction_id_exclusive=1)), authority)
    with pytest.raises(v1.BindingError):
        v1._boundary(FakeConnection(scope=None), authority)


def test_missing_capture_trigger_rejected():
    with pytest.raises(v1.BindingError):
        v1._triggers(FakeConnection(trigger_rows=[]))


def test_fails_before_network_without_local_authority(monkeypatch):
    monkeypatch.setattr(v1, 'AUTHORITY', Path('__stage4t_missing_authority__'))
    with pytest.raises(v1.BindingError):
        v1.load_authority()
    result = v1.infer(1)
    assert result['status'] == 'inference_error'
    assert result['prediction'] is None and result['suspicious_probability'] is None


def test_child_cannot_use_missing_authority(monkeypatch):
    from ml_v4.test_binding import worker
    monkeypatch.setattr(v1, 'AUTHORITY', Path('__stage4t_missing_authority__'))
    result = worker.run(1, '0' * 64, 'test-server')
    assert result['decision'] == 'inference_error'
    assert result['prediction'] is None and result['suspicious_probability'] is None
