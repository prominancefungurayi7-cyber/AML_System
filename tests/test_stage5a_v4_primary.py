"""Offline post-commit V4-primary decision tests; no live MySQL or model fitting."""
import sqlite3

import pytest

from database import DatabaseAdapter
import v4_primary
import v4_shadow


def connect(path):
    raw = sqlite3.connect(path)
    raw.row_factory = sqlite3.Row
    raw.execute('PRAGMA foreign_keys=ON')
    return DatabaseAdapter(raw, 'sqlite')


def setup(path, *, rule_score=0):
    db = connect(path)
    db.execute('CREATE TABLE users (id INTEGER PRIMARY KEY,balance REAL)')
    db.execute('INSERT INTO users VALUES (1,489.5),(2,510.5)')
    db.execute('CREATE TABLE canonical_mobile_money_events (transaction_id INTEGER PRIMARY KEY)')
    db.execute('CREATE TABLE transactions (id INTEGER PRIMARY KEY,sender_account TEXT,'
               'timestamp TEXT,rule_score INTEGER,rules_triggered TEXT,sar_required INTEGER,'
               'ctr_required INTEGER,'
               'ai_risk_level TEXT,ai_confidence REAL,ai_reason TEXT,description TEXT,'
               'risk_score INTEGER,risk_level TEXT)')
    db.execute('CREATE TABLE alerts (id INTEGER PRIMARY KEY,transaction_id INTEGER UNIQUE,'
               'account_number TEXT,risk_score INTEGER,risk_level TEXT,reason TEXT,'
               'rules_triggered TEXT,status TEXT,timestamp TEXT)')
    v4_shadow.migrate(db)
    db.execute("INSERT INTO canonical_mobile_money_events VALUES (1)")
    db.execute('INSERT INTO transactions VALUES '
               "(1,'A','2026-10-09T00:00:00.000000Z',?,'[]',0,1,'pending_v4',0,"
               "'Awaiting V4','Awaiting V4',0,'pending_review')", (rule_score,))
    db.commit()
    db.close()


def success(tx, probability):
    result = v4_shadow.error(tx, 'INFERENCE_ERROR')
    result.update(status='success', prediction=int(probability >= .5),
                  suspicious_probability=probability,
                  decision='suspicious_pattern' if probability >= .5 else 'normal',
                  error_code=None, history_status='COMPLETE_VERIFIED',
                  observation_scope='controlled-prototype-v1',
                  source_revision='a' * 64, scope_revision=1,
                  event_timestamp='2026-10-09T00:00:00.000000Z',
                  history_complete_through={'key': ['2026-10-09T00:00:00.000000Z', 1]})
    return result


@pytest.mark.parametrize('probability,expected_alert', [(.20, 0), (.75, 1)])
def test_committed_v4_decision_and_alert_without_balance_effect(tmp_path, probability,
                                                              expected_alert):
    path = tmp_path / 'primary.db'
    setup(path)
    calls = []
    def worker(tx):
        independently_visible = connect(path)
        assert independently_visible.execute('SELECT transaction_id FROM '
                                             'canonical_mobile_money_events').fetchone()
        independently_visible.close()
        calls.append('v4')
        return success(tx, probability)
    notifications = []
    def published(payload):
        committed = connect(path)
        assert committed.execute('SELECT ai_risk_level FROM transactions').fetchone()[0] in (
            'normal', 'suspicious_pattern')
        committed.close()
        notifications.append(payload)
    result = v4_primary.complete_committed(lambda: connect(path), 1,
                                           worker=worker, notify=published)
    db = connect(path)
    row = db.execute('SELECT ai_risk_level,risk_level,sar_required,ctr_required FROM transactions').fetchone()
    assert row['ai_risk_level'] == ('suspicious_pattern' if expected_alert else 'normal')
    assert db.execute('SELECT COUNT(*) AS n FROM alerts').fetchone()['n'] == expected_alert
    assert db.execute('SELECT COUNT(*) AS n FROM v4_shadow_results').fetchone()['n'] == 1
    assert [r['balance'] for r in db.execute('SELECT balance FROM users ORDER BY id')] == [489.5, 510.5]
    assert row['sar_required'] == expected_alert
    assert row['ctr_required'] == 1
    assert result['status'] == 'success' and len(notifications) == 1
    assert calls == ['v4']
    db.close()


def test_inference_error_is_unresolved_without_v1_fallback_or_alert(tmp_path):
    path = tmp_path / 'failure.db'
    setup(path)
    events = []
    result = v4_primary.complete_committed(
        lambda: connect(path), 1,
        worker=lambda tx: v4_shadow.error(tx, 'INFERENCE_ERROR'),
        notify=events.append)
    db = connect(path)
    row = db.execute('SELECT ai_risk_level,risk_level,ai_confidence FROM transactions').fetchone()
    assert (row['ai_risk_level'], row['risk_level'], row['ai_confidence']) == (
        'inference_error', 'pending_review', 0)
    assert db.execute('SELECT COUNT(*) AS n FROM alerts').fetchone()['n'] == 0
    assert result['status'] == 'inference_error' and len(events) == 1
    db.close()


def test_terminal_error_is_immutable_and_payment_retry_cannot_reinfer(tmp_path):
    path = tmp_path / 'terminal-error.db'
    setup(path)
    factory = lambda: connect(path)
    first = v4_primary.complete_committed(factory, 1,
                                          worker=lambda tx: v4_shadow.error(tx, 'INFERENCE_ERROR'))
    assert first['status'] == 'inference_error'
    stored = connect(path)
    original = stored.execute('SELECT body FROM v4_shadow_results WHERE transaction_id=1').fetchone()[0]
    stored.close()
    reused = v4_shadow.process(factory, 1, lambda _payload: None,
                               runner=lambda _tx: pytest.fail('Terminal worker rerun'))
    assert reused['status'] == 'inference_error'
    with pytest.raises(ValueError, match='not awaiting'):
        v4_primary.complete_committed(factory, 1,
                                      worker=lambda _tx: pytest.fail('Payment decision rerun'))
    check = connect(path)
    assert check.execute('SELECT body FROM v4_shadow_results WHERE transaction_id=1').fetchone()[0] == original
    assert check.execute('SELECT ai_risk_level FROM transactions WHERE id=1').fetchone()[0] == 'inference_error'
    check.close()


def test_rule_alert_survives_v4_error(tmp_path):
    path = tmp_path / 'rules.db'
    setup(path, rule_score=60)
    v4_primary.complete_committed(lambda: connect(path), 1,
                                  worker=lambda tx: v4_shadow.error(tx, 'INFERENCE_ERROR'))
    db = connect(path)
    row = db.execute('SELECT ai_risk_level,risk_level,risk_score FROM transactions').fetchone()
    assert tuple(row) == ('inference_error', 'high_risk', 60)
    assert db.execute('SELECT COUNT(*) AS n FROM alerts').fetchone()['n'] == 1
    db.close()


def test_duplicate_completion_has_no_second_decision_or_notification(tmp_path):
    path = tmp_path / 'retry.db'
    setup(path)
    events = []
    factory = lambda: connect(path)
    v4_primary.complete_committed(factory, 1, worker=lambda tx: success(tx, .8),
                                  notify=events.append)
    with pytest.raises(v4_primary.DecisionAlreadyApplied, match='not awaiting'):
        v4_primary.complete_committed(factory, 1,
                                      worker=lambda tx: pytest.fail('duplicate inference'),
                                      notify=events.append)
    db = connect(path)
    assert db.execute('SELECT COUNT(*) AS n FROM alerts').fetchone()['n'] == 1
    assert len(events) == 1
    db.close()


def test_losing_concurrent_decision_update_is_not_an_inference_failure(tmp_path):
    from types import SimpleNamespace
    path = tmp_path / 'concurrent-completion.db'
    setup(path)
    calls = []
    class LostUpdate:
        def __init__(self):
            self.db = connect(path)
        def execute(self, sql, params=()):
            if sql.startswith('UPDATE transactions SET risk_score='):
                return SimpleNamespace(rowcount=0)
            return self.db.execute(sql, params)
        def __getattr__(self, name):
            return getattr(self.db, name)
    def factory():
        calls.append(1)
        return LostUpdate() if len(calls) == 3 else connect(path)
    notifications = []
    with pytest.raises(v4_primary.DecisionAlreadyApplied, match='Concurrent'):
        v4_primary.complete_committed(factory, 1, worker=lambda tx: success(tx, .8),
                                      notify=notifications.append)
    db = connect(path)
    assert db.execute('SELECT COUNT(*) FROM alerts').fetchone()[0] == 0
    assert db.execute('SELECT status FROM v4_shadow_results').fetchone()[0] == 'success'
    assert [r['balance'] for r in db.execute('SELECT balance FROM users ORDER BY id')] == [489.5, 510.5]
    assert not notifications
    db.close()


def test_rolled_back_source_never_routes_or_notifies(tmp_path):
    path = tmp_path / 'rolledback.db'
    setup(path)
    db = connect(path)
    db.execute('DELETE FROM transactions')
    db.execute('DELETE FROM canonical_mobile_money_events')
    db.commit()
    db.close()
    events = []
    with pytest.raises(ValueError, match='unavailable'):
        v4_primary.complete_committed(lambda: connect(path), 1,
                                      worker=lambda tx: pytest.fail('worker called'),
                                      notify=events.append)
    assert not events


def test_malformed_worker_output_fails_explicitly(tmp_path):
    path = tmp_path / 'malformed.db'
    setup(path)
    v4_primary.complete_committed(lambda: connect(path), 1, worker=lambda _tx: {'status': 'success'})
    db = connect(path)
    assert db.execute('SELECT ai_risk_level,risk_level FROM transactions').fetchone()[:] == (
        'inference_error', 'pending_review')
    assert db.execute('SELECT COUNT(*) FROM alerts').fetchone()[0] == 0
    db.close()


def test_decision_commit_failure_has_no_notification_or_false_normal(tmp_path):
    path = tmp_path / 'decision-rollback.db'
    setup(path)
    calls = []
    class BrokenCommit:
        def __init__(self):
            self.db = connect(path)
        def execute(self, *args):
            return self.db.execute(*args)
        def commit(self):
            raise RuntimeError('decision commit failed')
        def rollback(self):
            self.db.rollback()
        def close(self):
            self.db.close()
    def factory():
        calls.append(1)
        return BrokenCommit() if len(calls) == 3 else connect(path)
    notifications = []
    with pytest.raises(RuntimeError, match='decision commit failed'):
        v4_primary.complete_committed(factory, 1, worker=lambda tx: success(tx, .2),
                                      notify=notifications.append)
    db = connect(path)
    assert db.execute('SELECT ai_risk_level FROM transactions').fetchone()[0] == 'pending_v4'
    assert db.execute('SELECT COUNT(*) FROM alerts').fetchone()[0] == 0
    assert notifications == []
    db.close()


def test_shadow_mode_cannot_run_as_primary_simultaneously(tmp_path, monkeypatch):
    path = tmp_path / 'dual-mode.db'
    setup(path)
    monkeypatch.setenv('V4_SHADOW_ENABLED', 'ON')
    with pytest.raises(RuntimeError, match='shadow mode must be OFF'):
        v4_primary.complete_committed(lambda: connect(path), 1,
                                      worker=lambda tx: pytest.fail('worker called'))
