"""The Stage5C injected inference error must occur after history attestation."""
import hashlib
import json

import pytest

from ml_v4.test_binding import v1, worker
import canonical_history_store


class Connection:
    def __init__(self, events, row):
        self.events = events
        self.row = row
        self.last = ''

    def execute(self, sql, params=None):
        self.last = sql
        self.events.append(sql)
        return self

    def fetchone(self):
        if 'GET_LOCK' in self.last:
            return {'ok': 1}
        if 'canonical_mobile_money_events' in self.last:
            return self.row
        return None

    def fetchall(self):
        return [{'operation': 'SOURCE_INSERT'}, {'operation': 'CANONICAL_INSERT'}]

    def rollback(self):
        self.events.append('rollback')

    def commit(self):
        self.events.append('commit')

    def close(self):
        self.events.append('close')


@pytest.mark.parametrize('inject', [False, True])
def test_injected_failure_follows_attestation_and_commit(monkeypatch, inject):
    events = []
    row = {'transaction_id': 9, 'canonical_version': 'test'}
    digest = hashlib.sha256(json.dumps(row, sort_keys=True,
                                       separators=(',', ':')).encode()).hexdigest()
    monkeypatch.setattr(v1, 'load_authority', lambda: {'server_uuid': 'test-uuid'})
    monkeypatch.setattr(v1, 'connection', lambda _authority: Connection(events, row))
    monkeypatch.setattr(v1, 'identity', lambda *_: events.append('identity'))
    monkeypatch.setattr(v1, '_triggers', lambda *_: events.append('triggers'))
    monkeypatch.setattr(v1, '_boundary', lambda *_: events.append('boundary'))
    monkeypatch.setattr(canonical_history_store, 'attest',
                        lambda *_: events.append('attest') or {'status': 'COMPLETE_VERIFIED'})
    monkeypatch.setattr(v1, 'infer', lambda _tx: events.append('infer') or {'status': 'success'})
    monkeypatch.setenv('STAGE5C_EXECUTE', 'YES')
    monkeypatch.setenv('AML_PRIMARY_MODEL', 'V4')
    if inject:
        monkeypatch.setenv('STAGE5C_INJECT_POST_ATTEST_ERROR', 'YES')
    else:
        monkeypatch.delenv('STAGE5C_INJECT_POST_ATTEST_ERROR', raising=False)
    result = worker.run(9, digest, 'test-uuid')
    assert events.index('attest') < events.index('commit') < events.index('close')
    if inject:
        assert result['status'] == 'inference_error'
        assert 'infer' not in events
    else:
        assert result['status'] == 'success'
        assert events.index('close') < events.index('infer')


def test_stage5c_runner_uses_worker_fault_injection_not_coordinator_override():
    from pathlib import Path
    source = Path('ml_v4/stage5c/live_primary.py').read_text(encoding='utf-8')
    assert "os.environ['STAGE5C_INJECT_POST_ATTEST_ERROR'] = 'YES'" in source
    assert "evidence['history_after_inference_failure'] = _history(check)" in source
    assert 'coordinator.invoke_test =' not in source
