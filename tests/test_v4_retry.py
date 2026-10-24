"""Offline staff retry/closure contract; no MySQL or financial fixtures."""
import json
import sqlite3
from uuid import uuid4

import pytest

from tests.test_stage5a_v4_primary import connect, setup, success
import v4_primary
import v4_retry
import v4_shadow


@pytest.mark.parametrize('revision,issues,fresh,accepted', [
    ('expected', [], 'COMPLETE_VERIFIED', True),
    ('concurrent-new-revision', [], 'COMPLETE_VERIFIED', False),
    ('expected', ['capture missing'], 'COMPLETE_VERIFIED', False),
    ('expected', [], 'STALE', False),
])
def test_retry_checks_fresh_revision_after_worker(monkeypatch, revision, issues, fresh, accepted):
    calls = []
    class Connection:
        def rollback(self): calls.append('rollback')
        def execute(self, sql): calls.append(sql)
    monkeypatch.setattr('canonical_history_store.assess', lambda *_: (
        {}, {'source_revision': revision, 'issues': issues}, {}))
    monkeypatch.setattr('canonical_history.freshness', lambda *_: fresh)
    assert v4_retry._revision_still_verified(Connection(), 'expected') is accepted
    assert calls[0] == calls[-1] == 'rollback'
    assert 'START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY' in calls


def prepared(tmp_path):
    path = tmp_path / 'retry.db'
    setup(path)
    db = connect(path)
    db.execute('ALTER TABLE users ADD COLUMN role TEXT')
    db.execute("UPDATE users SET role='customer'")
    db.execute("INSERT INTO users (id,balance,role) VALUES (3,0,'compliance'),(4,0,'admin')")
    db.execute('CREATE TABLE v4_primary_attempt_events ('
               'event_id INTEGER PRIMARY KEY AUTOINCREMENT,transaction_id INTEGER NOT NULL,'
               'staff_user_id INTEGER NOT NULL,request_key TEXT NOT NULL,event_kind TEXT NOT NULL,'
               'recorded_at TEXT NOT NULL,outcome TEXT NOT NULL,error_code TEXT,'
               'result_body TEXT,reason TEXT,UNIQUE(transaction_id,request_key,event_kind))')
    db.execute("CREATE TRIGGER v4_retry_no_update BEFORE UPDATE ON v4_primary_attempt_events "
               "BEGIN SELECT RAISE(ABORT,'append only'); END")
    db.execute("CREATE TRIGGER v4_retry_no_delete BEFORE DELETE ON v4_primary_attempt_events "
               "BEGIN SELECT RAISE(ABORT,'append only'); END")
    db.commit()
    db.close()
    factory = lambda: connect(path)
    v4_primary.complete_committed(factory, 1,
                                  worker=lambda tx: v4_shadow.error(tx, 'INFERENCE_ERROR'))
    return path, factory


def rows(factory):
    db = factory()
    try:
        return [dict(row) for row in db.execute(
            'SELECT * FROM v4_primary_attempt_events ORDER BY event_id').fetchall()]
    finally:
        db.close()


def test_successful_retry_preserves_original_and_payment_and_creates_one_alert(tmp_path):
    _path, factory = prepared(tmp_path)
    before = factory()
    original = before.execute('SELECT body FROM v4_shadow_results WHERE transaction_id=1').fetchone()[0]
    balances = [r['balance'] for r in before.execute('SELECT balance FROM users WHERE id IN (1,2) ORDER BY id')]
    before.close()
    key = str(uuid4())
    notified = []
    output = v4_retry.retry(factory, 1, 3, key,
                            runner=lambda tx, _digest, _uuid: success(tx, .75),
                            notify=notified.append)
    assert output['status'] == 'success' and output['decision'] == 'suspicious_pattern'
    assert len(notified) == 1
    db = factory()
    assert db.execute('SELECT body FROM v4_shadow_results WHERE transaction_id=1').fetchone()[0] == original
    assert db.execute('SELECT ai_risk_level FROM transactions WHERE id=1').fetchone()[0] == 'suspicious_pattern'
    assert db.execute('SELECT COUNT(*) FROM alerts').fetchone()[0] == 1
    assert [r['balance'] for r in db.execute('SELECT balance FROM users WHERE id IN (1,2) ORDER BY id')] == balances
    db.close()
    audit = rows(factory)
    assert [r['event_kind'] for r in audit] == ['STARTED', 'COMPLETED']
    assert all(r['transaction_id'] == 1 and r['staff_user_id'] == 3 and r['request_key'] == key
               and r['recorded_at'] for r in audit)
    assert json.loads(audit[-1]['result_body'])['prediction'] == 1
    duplicate = v4_retry.retry(factory, 1, 3, key,
                               runner=lambda *_: pytest.fail('Duplicate worker execution'))
    assert duplicate['duplicate'] and len(rows(factory)) == 2
    with pytest.raises(v4_retry.RetryConflict):
        v4_retry.retry(factory, 1, 3, str(uuid4()), runner=lambda *_: pytest.fail('Worker ran'))


def test_failed_retry_stays_unresolved_and_new_explicit_attempt_is_separate(tmp_path):
    _path, factory = prepared(tmp_path)
    first = v4_retry.retry(factory, 1, 3, str(uuid4()),
                           runner=lambda tx, *_: v4_shadow.error(tx, 'HISTORY_INCOMPLETE'))
    assert first['status'] == 'inference_error' and first['error_code'] == 'HISTORY_INCOMPLETE'
    db = factory()
    assert db.execute('SELECT ai_risk_level FROM transactions WHERE id=1').fetchone()[0] == 'inference_error'
    db.close()
    second = v4_retry.retry(factory, 1, 4, str(uuid4()),
                            runner=lambda tx, *_: success(tx, .2))
    assert second['status'] == 'success' and second['decision'] == 'normal'
    assert [r['event_kind'] for r in rows(factory)] == ['STARTED', 'COMPLETED', 'STARTED', 'COMPLETED']


def test_malformed_worker_output_is_audited_as_error_without_prediction(tmp_path):
    _path, factory = prepared(tmp_path)
    output = v4_retry.retry(factory, 1, 3, str(uuid4()),
                            runner=lambda *_: {'status': 'success', 'prediction': 1})
    assert output['status'] == 'inference_error' and output['error_code'] == 'INFERENCE_ERROR'
    final = json.loads(rows(factory)[-1]['result_body'])
    assert final['prediction'] is None and final['suspicious_probability'] is None
    db = factory()
    assert db.execute('SELECT ai_risk_level FROM transactions WHERE id=1').fetchone()[0] == 'inference_error'
    db.close()


def test_staff_closure_is_audited_without_fabricating_decision(tmp_path):
    _path, factory = prepared(tmp_path)
    key = str(uuid4())
    closed = v4_retry.close(factory, 1, 4, key, 'Reviewed source and closed for manual follow-up')
    assert closed['status'] == 'closed'
    assert v4_retry.close(factory, 1, 4, key, 'Reviewed source and closed for manual follow-up')['duplicate']
    assert rows(factory)[0]['reason'] == 'Reviewed source and closed for manual follow-up'
    db = factory()
    assert db.execute('SELECT ai_risk_level FROM transactions WHERE id=1').fetchone()[0] == 'inference_error'
    db.close()
    with pytest.raises(v4_retry.RetryConflict, match='closed'):
        v4_retry.retry(factory, 1, 3, str(uuid4()), runner=lambda *_: pytest.fail('Worker ran'))


def test_customer_and_missing_schema_fail_closed(tmp_path):
    _path, factory = prepared(tmp_path)
    with pytest.raises(PermissionError):
        v4_retry.retry(factory, 1, 1, str(uuid4()), runner=lambda *_: pytest.fail('Worker ran'))
    assert not rows(factory)
    db = factory()
    db.execute('DROP TABLE v4_primary_attempt_events')
    db.commit()
    db.close()
    with pytest.raises(Exception):
        v4_retry.close(factory, 1, 3, str(uuid4()), 'Reviewed and closed manually')


def test_missing_append_only_trigger_blocks_staff_action(tmp_path):
    _path, factory = prepared(tmp_path)
    db = factory()
    db.execute('DROP TRIGGER v4_retry_no_delete')
    db.commit()
    db.close()
    with pytest.raises(RuntimeError, match='Append-only retry triggers'):
        v4_retry.retry(factory, 1, 3, str(uuid4()), runner=lambda *_: pytest.fail('Worker ran'))
    assert not rows(factory)


def test_concurrent_attempt_is_rejected_and_audit_is_append_only(tmp_path):
    _path, factory = prepared(tmp_path)
    def nested(tx, *_):
        with pytest.raises(v4_retry.RetryConflict, match='in progress'):
            v4_retry.retry(factory, tx, 4, str(uuid4()), runner=lambda *_: pytest.fail('Nested worker'))
        return v4_shadow.error(tx, 'RESOURCE_ERROR')
    v4_retry.retry(factory, 1, 3, str(uuid4()), runner=nested)
    assert len(rows(factory)) == 2
    db = factory()
    with pytest.raises(sqlite3.DatabaseError):
        db.execute("UPDATE v4_primary_attempt_events SET outcome='success'")
    db.rollback()
    with pytest.raises(sqlite3.DatabaseError):
        db.execute('DELETE FROM v4_primary_attempt_events')
    db.close()


def test_staff_can_close_an_interrupted_attempt_without_rerunning_payment(tmp_path):
    _path, factory = prepared(tmp_path)
    db = factory()
    v4_retry._insert(db, 1, 3, str(uuid4()), 'STARTED', 'started')
    db.commit()
    db.close()
    with pytest.raises(v4_retry.RetryConflict, match='lacks a completion'):
        v4_retry.retry(factory, 1, 3, str(uuid4()), runner=lambda *_: pytest.fail('Worker ran'))
    result = v4_retry.close(factory, 1, 4, str(uuid4()),
                            'Worker outcome unavailable; manual review retained')
    assert result['status'] == 'closed'
    assert [r['event_kind'] for r in rows(factory)] == ['STARTED', 'CLOSED']
