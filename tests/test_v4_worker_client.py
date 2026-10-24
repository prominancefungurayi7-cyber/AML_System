import io
import json
import queue

import v4_shadow
import v4_worker_client as client


class Child:
    def __init__(self):
        self.stdin = io.BytesIO()
        self.stdout = io.BytesIO()
        self.killed = False

    def poll(self):
        return 1 if self.killed else None

    def kill(self):
        self.killed = True

    def wait(self, timeout):
        return 0


def test_reuses_worker_and_validates_transaction_identity(monkeypatch):
    child = Child()
    responses = queue.Queue()
    monkeypatch.setattr(client, '_child', child)
    monkeypatch.setattr(client, '_responses', responses)
    for tx in (11, 12):
        responses.put(json.dumps(v4_shadow.error(tx, 'HISTORY_INCOMPLETE')).encode())
        assert client.invoke(tx, 'a'*64, 'uuid')['transaction_id'] == str(tx)
    assert not child.killed
    assert len(child.stdin.getvalue().splitlines()) == 2
    responses.put(json.dumps(v4_shadow.error(99, 'HISTORY_INCOMPLETE')).encode())
    result = client.invoke(13, 'a'*64, 'uuid')
    assert result['status'] == 'inference_error'
    assert result['prediction'] is None
    assert child.killed


def test_timeout_kills_worker_and_returns_no_prediction(monkeypatch):
    child = Child()
    monkeypatch.setattr(client, '_child', child)
    monkeypatch.setattr(client, '_responses', queue.Queue())
    monkeypatch.setattr(v4_shadow, 'TIMEOUT', 0.01)
    result = client.invoke(11, 'a'*64, 'uuid')
    assert result['error_code'] == 'RESOURCE_ERROR'
    assert result['prediction'] is None
    assert child.killed
    assert client._child is None
