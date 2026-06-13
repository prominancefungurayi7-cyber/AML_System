import json
import os
from queue import Empty, Queue

from flask import Response

try:
    import redis
except ImportError:  # pragma: no cover
    redis = None

try:
    from kafka import KafkaProducer
except ImportError:  # pragma: no cover
    KafkaProducer = None


class RealtimeBroker:
    def __init__(self, app=None, socketio=None):
        self.app = app
        self.socketio = socketio
        self._subscribers = []
        self._redis_client = None
        self._kafka_producer = None
        self._init_brokers()

    def _init_brokers(self):
        redis_url = os.environ.get("REDIS_URL")
        if redis_url and redis is not None:
            try:
                self._redis_client = redis.from_url(redis_url, decode_responses=True)
                self._redis_client.ping()
            except Exception:
                self._redis_client = None

        kafka_bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS")
        if kafka_bootstrap and KafkaProducer is not None:
            try:
                self._kafka_producer = KafkaProducer(
                    bootstrap_servers=[server.strip() for server in kafka_bootstrap.split(",") if server.strip()],
                    value_serializer=lambda value: json.dumps(value).encode("utf-8"),
                )
            except Exception:
                self._kafka_producer = None

    def set_socketio(self, socketio):
        self.socketio = socketio

    def add_subscriber(self, queue):
        self._subscribers.append(queue)
        if self.app is not None:
            app_subscribers = self.app.config.setdefault("STREAM_SUBSCRIBERS", [])
            if queue not in app_subscribers:
                app_subscribers.append(queue)
        return queue

    def publish(self, event_name, payload):
        message = {"event": event_name, "data": payload}
        for subscriber in list(self._subscribers):
            try:
                subscriber.put_nowait(message)
            except Exception:
                pass

        app_subscribers = self.app.config.get("STREAM_SUBSCRIBERS", []) if self.app is not None else []
        for subscriber in list(app_subscribers):
            try:
                subscriber.put_nowait(message)
            except Exception:
                pass

        if self.socketio is not None:
            try:
                self.socketio.emit(event_name, payload, broadcast=True)
            except Exception:
                pass

        if self._redis_client is not None:
            try:
                self._redis_client.publish("aml-events", json.dumps(message))
            except Exception:
                pass

        if self._kafka_producer is not None:
            try:
                self._kafka_producer.send("aml-events", message)
            except Exception:
                pass

    def stream_response(self):
        queue = Queue()
        self.add_subscriber(queue)

        def generate():
            yield ": connected\n\n"
            while True:
                try:
                    message = queue.get(timeout=1)
                except Empty:
                    yield ": heartbeat\n\n"
                    continue
                yield f"event: {message['event']}\n"
                yield f"data: {json.dumps(message['data'])}\n\n"

        return Response(generate(), mimetype="text/event-stream")
