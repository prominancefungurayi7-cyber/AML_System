"""Nonfinancial delivery tests; no application startup or database access."""
from queue import Queue
from types import SimpleNamespace

from realtime import RealtimeBroker


class Sockets:
    def __init__(self):
        self.events = []

    def emit(self, event, payload, to=None):
        self.events.append((event, payload, to))


def broker(monkeypatch):
    monkeypatch.delenv('REDIS_URL', raising=False)
    monkeypatch.delenv('KAFKA_BOOTSTRAP_SERVERS', raising=False)
    sockets = Sockets()
    return RealtimeBroker(socketio=sockets), sockets


def test_staff_only_delivery_and_role_revocation(monkeypatch):
    b, sockets = broker(monkeypatch)
    staff = {1}
    b.set_staff_authorizer(lambda uid: uid in staff)
    assert b.add_staff_socket('staff', 1)
    assert not b.add_staff_socket('customer', 2)
    b.publish('alert', {'id': 9})
    assert sockets.events == [('alert', {'id': 9}, 'staff')]
    staff.clear()
    b.publish('alert', {'id': 10})
    assert len(sockets.events) == 1


def test_duplicate_subscriber_receives_one_event(monkeypatch):
    b, _ = broker(monkeypatch)
    q = Queue()
    b._subscribers = [q]
    b.app = SimpleNamespace(config={'STREAM_SUBSCRIBERS': [q]}, logger=SimpleNamespace(info=lambda *_: None))
    b.publish('transaction', {'id': 1})
    assert q.get_nowait()['data']['id'] == 1
    assert q.empty()


def test_health_requires_subscription_and_live_ping(monkeypatch):
    b, _ = broker(monkeypatch)
    b._redis_client = SimpleNamespace(ping=lambda: True)
    assert not b.redis_healthy()
    b._redis_ready.set()
    assert b.redis_healthy()
    def down():
        raise ConnectionError('offline')
    b._redis_client.ping = down
    assert not b.redis_healthy()


def test_local_delivery_survives_full_publish_queue(monkeypatch):
    b, sockets = broker(monkeypatch)
    b.set_staff_authorizer(lambda uid: True)
    b.add_staff_socket('staff', 1)
    b._redis_client = object()
    b._publish_queue = Queue(maxsize=1)
    b._publish_queue.put({})
    b.publish('alert', {'id': 1})
    assert sockets.events == [('alert', {'id': 1}, 'staff')]
