"""Nonfinancial post-commit history and inference ordering checks."""
import pytest

import v4_history_attestation
import v4_primary
import v4_shadow
from test_stage5a_v4_primary import connect, setup, success


def test_attestation_failure_preserves_committed_payment_and_pending_state(tmp_path):
    path = tmp_path / 'pending.db'
    setup(path)
    called = []
    def failed(_factory, _tx):
        called.append('attest')
        raise RuntimeError('history changed')
    with pytest.raises(RuntimeError, match='history changed'):
        v4_primary.complete_committed(lambda: connect(path), 1,
                                      worker=lambda _tx: called.append('worker'),
                                      attestor=failed)
    db = connect(path)
    assert called == ['attest']
    assert db.execute('SELECT ai_risk_level FROM transactions').fetchone()[0] == 'pending_v4'
    assert db.execute('SELECT COUNT(*) AS n FROM v4_shadow_results').fetchone()['n'] == 0
    assert [r['balance'] for r in db.execute('SELECT balance FROM users ORDER BY id')] == [489.5, 510.5]
    db.close()


def test_attestation_precedes_frozen_worker_and_no_balance_replay(tmp_path, monkeypatch):
    path = tmp_path / 'ordered.db'
    setup(path)
    calls = []
    def attestor(_factory, tx):
        calls.append(('attest', tx))
        return 'a' * 64
    def fake_assess(_conn, _scope):
        return {}, {'source_revision': 'a' * 64, 'issues': []}, {}
    monkeypatch.setattr('canonical_history_store.assess', fake_assess)
    monkeypatch.setattr('canonical_history.freshness', lambda *_: 'COMPLETE_VERIFIED')
    def worker(tx):
        calls.append(('infer', tx))
        return success(tx, .2)
    class SnapshotConnection:
        engine = 'sqlite'
        def __init__(self):
            self.db = connect(path)
        def execute(self, sql, params=()):
            if sql.startswith(('SET TRANSACTION ISOLATION LEVEL',
                               'START TRANSACTION WITH CONSISTENT SNAPSHOT')):
                return None
            return self.db.execute(sql, params)
        def __getattr__(self, name):
            return getattr(self.db, name)
    result = v4_primary.complete_committed(lambda: SnapshotConnection(), 1,
                                           worker=worker, attestor=attestor)
    assert result['status'] == 'success'
    assert calls == [('attest', 1), ('infer', 1)]
    db = connect(path)
    assert db.execute('SELECT COUNT(*) AS n FROM transactions').fetchone()['n'] == 1
    assert db.execute('SELECT COUNT(*) AS n FROM v4_shadow_results').fetchone()['n'] == 1
    assert [r['balance'] for r in db.execute('SELECT balance FROM users ORDER BY id')] == [489.5, 510.5]
    db.close()


def test_changed_source_revision_becomes_explicit_error(tmp_path):
    path = tmp_path / 'revision.db'
    setup(path)
    result = v4_shadow.process(lambda: connect(path), 1, lambda _: None,
                               runner=lambda tx: success(tx, .8),
                               expected_source_revision='b' * 64)
    assert result['status'] == 'inference_error'
    assert result['error_code'] == 'HISTORY_INCOMPLETE'
    assert result['prediction'] is None and result['suspicious_probability'] is None
    db = connect(path)
    assert db.execute('SELECT COUNT(*) AS n FROM transactions').fetchone()['n'] == 1
    db.close()


class _Connection:
    engine = 'mysql'
    def __init__(self):
        self.commits = 0
    def execute(self, statement, params=()):
        if statement.startswith('SELECT GET_LOCK'):
            return _Result({'acquired': 1})
        return _Result({})
    def rollback(self):
        pass
    def commit(self):
        self.commits += 1
    def close(self):
        pass


class _Result:
    def __init__(self, row):
        self.row = row
    def fetchone(self):
        return self.row


def test_attestation_rechecks_revision_after_commit(monkeypatch):
    conn = _Connection()
    scope = {'revision': 1}
    first = {'source_revision': 'a' * 64, 'status': 'COMPLETE_VERIFIED',
             'canonical_event_ids': [1], 'issues': []}
    second = {**first, 'source_revision': 'b' * 64}
    snapshots = iter([(scope, first, {}, 'configured-db-identity:aml@127.0.0.1'),
                      (scope, second, {}, 'configured-db-identity:aml@127.0.0.1')])
    monkeypatch.setattr(v4_history_attestation, '_snapshot', lambda *_: next(snapshots))
    monkeypatch.setattr(v4_history_attestation, 'freshness',
                        lambda _s, current, _p: 'UNKNOWN' if current is first else 'COMPLETE_VERIFIED')
    monkeypatch.setattr(v4_history_attestation, 'attest',
                        lambda *_: {'status': 'COMPLETE_VERIFIED', 'source_revision': 'a' * 64})
    with pytest.raises(RuntimeError, match='changed after attestation'):
        v4_history_attestation.refresh_committed(lambda: conn, 1)
    assert conn.commits == 1
