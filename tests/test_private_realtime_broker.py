"""Direct-message Redis envelopes stay in the intended authenticated room."""
from queue import Queue

from realtime import RealtimeBroker


def test_private_room_delivery_and_remote_envelope():
    class Socket:
        def __init__(self):
            self.calls = []
        def emit(self, event, data, to):
            self.calls.append((event, data, to))

    local, remote = RealtimeBroker.__new__(RealtimeBroker), RealtimeBroker.__new__(RealtimeBroker)
    local.socketio, remote.socketio = Socket(), Socket()
    local._redis_client = object()
    local._publish_queue = Queue()
    local._instance_id = 'one'
    local.app = None
    local.publish_private('Compliance', 'new_message', {'id': 17, 'content': 'Stored message'})
    assert local.socketio.calls == [('new_message', {'id': 17, 'content': 'Stored message'}, 'user:Compliance')]
    packet = local._publish_queue.get_nowait()
    assert packet['event'] == 'private_user_event' and packet['publisher'] == 'one'
    remote._local_private_deliver(packet['data'])
    assert remote.socketio.calls == local.socketio.calls
    remote._local_private_deliver({'username': 'Compliance', 'event': 'alert', 'data': {'id': 17}})
    assert len(remote.socketio.calls) == 1
