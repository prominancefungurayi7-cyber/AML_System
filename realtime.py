"""
realtime.py — Real-time Event Broker Module

This module provides real-time event broadcasting for WebSocket/Redis/Kafka.
It handles cross-instance messaging, offline user queuing, and SSE streaming.

Classes:
    - RealtimeBroker: Real-time event broker for WebSocket/Redis/Kafka broadcasting
"""

import json
import os
import socket
import threading
import time
import uuid
from queue import Empty, Queue
from flask import Response

try:
    import redis
except ImportError:
    redis = None

try:
    from kafka import KafkaProducer
except ImportError:
    KafkaProducer = None


class RealtimeBroker:
    """Real-time event broker for WebSocket/Redis/Kafka broadcasting."""
    
    def __init__(self, app=None, socketio=None):
        self.app = app
        self.socketio = socketio
        self._staff_sockets = {}
        self._staff_authorizer = None
        self._socket_authorizer = None
        self._user_sockets = {}
        self._subscribers = []
        self._redis_client = None
        self._redis_pubsub = None
        self._kafka_producer = None
        self._instance_id = str(uuid.uuid4())
        self._redis_ready = threading.Event()
        self._publish_queue = Queue(maxsize=10000)
        self._init_brokers()
        self._start_redis_listener()

    def _init_brokers(self):
        """Initialize Redis and Kafka connections."""
        redis_url = os.environ.get("REDIS_URL")
        if redis_url and redis is not None:
            try:
                # redis-py expects numeric socket option constants, not their
                # string names. Windows does not expose every Linux setting.
                keepalive_options = {}
                for option_name, value in (
                    ("TCP_KEEPIDLE", 1),
                    ("TCP_KEEPINTVL", 1),
                    ("TCP_KEEPCNT", 3),
                ):
                    option = getattr(socket, option_name, None)
                    if option is not None:
                        keepalive_options[option] = value
                self._redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2.0,
                    socket_timeout=2.0,
                    socket_keepalive=True,
                    socket_keepalive_options=keepalive_options or None,
                )
                self._redis_client.ping()
                if self.app:
                    self.app.logger.info("RealtimeBroker connected to Redis")
            except Exception as e:
                if self.app:
                    self.app.logger.warning("Redis unavailable at startup; reconnecting in background (%s)", type(e).__name__)

        kafka_bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS")
        # Skip Kafka if not configured or set to localhost (won't work in cloud)
        if kafka_bootstrap and KafkaProducer is not None and "localhost" not in kafka_bootstrap and "127.0.0.1" not in kafka_bootstrap:
            try:
                self._kafka_producer = KafkaProducer(
                    bootstrap_servers=[server.strip() for server in kafka_bootstrap.split(",") if server.strip()],
                    api_version_auto_timeout_ms=100,
                    request_timeout_ms=200,
                    max_block_ms=200,
                    value_serializer=lambda value: json.dumps(value).encode("utf-8"),
                )
            except Exception:
                self._kafka_producer = None

    def redis_healthy(self):
        if self._redis_client is None or not self._redis_ready.is_set():
            return False
        try:
            return bool(self._redis_client.ping())
        except Exception:
            return False

    def _start_redis_listener(self):
        """Reconnect automatically, including when Redis starts after Flask."""
        if self._redis_client is None:
            return

        def listen():
            while True:
                pubsub = None
                try:
                    pubsub = self._redis_client.pubsub(ignore_subscribe_messages=False)
                    self._redis_pubsub = pubsub
                    pubsub.subscribe("aml-events")
                    while True:
                        raw = pubsub.get_message(timeout=1.0)
                        if not raw:
                            continue
                        if raw.get("type") == "subscribe":
                            self._redis_ready.set()
                            # Pub/Sub does not replay missed messages. Clients
                            # reconcile their view from the authorised HTTP page.
                            self._local_deliver("realtime_resync", {})
                            continue
                        if raw.get("type") != "message":
                            continue
                        try:
                            message = json.loads(raw["data"])
                            if not isinstance(message, dict):
                                continue
                            if message.get("publisher") == self._instance_id:
                                continue
                            event = message.get("event")
                            if event in ("connect", "disconnect", "heartbeat"):
                                continue
                            if event == "private_user_event":
                                data = message.get("data")
                                if isinstance(data, dict):
                                    self._local_private_deliver(data)
                                continue
                            self._local_deliver(event, message.get("data"))
                        except (ValueError, TypeError):
                            continue
                except Exception as exc:
                    if self.app:
                        self.app.logger.warning("Redis listener reconnecting (%s)", type(exc).__name__)
                finally:
                    self._redis_ready.clear()
                    if pubsub is not None:
                        pubsub.close()
                time.sleep(1)

        def publish_pending():
            while True:
                message = self._publish_queue.get()
                try:
                    self._redis_client.publish("aml-events", json.dumps(message))
                except Exception as exc:
                    if self.app:
                        self.app.logger.warning("Redis event delivery failed (%s); local delivery retained", type(exc).__name__)
                finally:
                    self._publish_queue.task_done()

        threading.Thread(target=listen, daemon=True, name="aml-redis-listener").start()
        threading.Thread(target=publish_pending, daemon=True, name="aml-redis-publisher").start()

    def _local_deliver(self, event_name, payload):
        """Deliver event locally to subscribers and SocketIO."""
        if not event_name:
            return
        message = {"event": event_name, "data": payload}
        delivered = set()
        app_subscribers = self.app.config.get("STREAM_SUBSCRIBERS", []) if self.app is not None else []
        for subscriber in list(self._subscribers) + list(app_subscribers):
            subscriber_id = id(subscriber)
            if subscriber_id in delivered:
                continue
            delivered.add(subscriber_id)
            try:
                subscriber.put_nowait(message)
            except Exception:
                pass
        
        # Flask-SocketIO's emit is safe to call from worker/background threads.
        # Starting a new OS thread for every event eventually exhausts resources
        # during sustained transaction activity and makes connected clients appear
        # to stop receiving updates.
        if self.socketio is not None:
            try:
                # Ordinary AML events include accounts, amounts and risk data.
                # Recheck the current staff role for every delivery.
                for sid, user_id in list(self._staff_sockets.items()):
                    if (self._staff_authorizer is None or not self._staff_authorizer(user_id)
                            or (self._socket_authorizer is not None and not self._socket_authorizer(sid))):
                        self._staff_sockets.pop(sid, None)
                        continue
                    self.socketio.emit(event_name, payload, to=sid)
                if self.app:
                    self.app.logger.info(f"SocketIO broadcast event: {event_name}")
            except Exception as e:
                if self.app:
                    self.app.logger.error(f"SocketIO broadcast failed for {event_name}: {e}")

    def set_socketio(self, socketio):
        """Set the SocketIO instance."""
        self.socketio = socketio

    def _local_private_deliver(self, envelope):
        username, event_name, payload = (envelope.get("username"), envelope.get("event"), envelope.get("data"))
        if isinstance(username, str) and username and event_name in {
            "new_message", "unread_update", "message_status", "messages_read",
            "user_typing", "user_stop_typing",
            "balance", "customer_refresh", "profile_updated",
        } and isinstance(payload, dict) and self.socketio is not None:
            authorizer = getattr(self, '_socket_authorizer', None)
            if authorizer is None:
                self.socketio.emit(event_name, payload, to=f"user:{username}")
            else:
                for sid, owner in list(self._user_sockets.items()):
                    if owner == username and authorizer(sid):
                        self.socketio.emit(event_name, payload, to=sid)

    def publish_private(self, username, event_name, payload):
        """Deliver a direct message event to authenticated user rooms on all instances."""
        envelope = {"username": username, "event": event_name, "data": payload}
        self._local_private_deliver(envelope)
        if self._redis_client is not None:
            try:
                self._publish_queue.put_nowait({"event": "private_user_event", "data": envelope,
                                                "publisher": self._instance_id})
            except Exception:
                if self.app:
                    self.app.logger.error("Redis private event queue full; stored history remains available")

    def set_staff_authorizer(self, authorizer):
        self._staff_authorizer = authorizer

    def set_socket_authorizer(self, authorizer):
        self._socket_authorizer = authorizer

    def add_user_socket(self, sid, username):
        self._user_sockets[sid] = username

    def add_staff_socket(self, sid, user_id):
        if self._staff_authorizer is not None and self._staff_authorizer(user_id):
            self._staff_sockets[sid] = user_id
            return True
        return False

    def remove_staff_socket(self, sid):
        self._staff_sockets.pop(sid, None)
        self._user_sockets.pop(sid, None)

    def add_subscriber(self, queue):
        """Add a queue as a subscriber."""
        self._subscribers.append(queue)
        if self.app is not None:
            app_subscribers = self.app.config.setdefault("STREAM_SUBSCRIBERS", [])
            if queue not in app_subscribers:
                app_subscribers.append(queue)
        return queue

    def remove_subscriber(self, queue):
        """Remove a queue from subscribers."""
        if queue in self._subscribers:
            self._subscribers.remove(queue)
        if self.app is not None:
            app_subscribers = self.app.config.get("STREAM_SUBSCRIBERS", [])
            if queue in app_subscribers:
                app_subscribers.remove(queue)

    def publish(self, event_name, payload):
        """Publish an event to all subscribers and external brokers."""
        # Skip publishing internal SocketIO events to Redis to prevent infinite loops
        if event_name in ['connect', 'disconnect', 'heartbeat']:
            if self.app:
                self.app.logger.info(f"Skipping Redis publish for internal event: {event_name}")
            self._local_deliver(event_name, payload)
            return

        message = {"event": event_name, "data": payload, "publisher": self._instance_id}
        if self.app:
            self.app.logger.info(f"RealtimeBroker.publish called for event: {event_name}")
        self._local_deliver(event_name, payload)

        # A single publisher preserves order without spawning a thread per event.
        if self._redis_client is not None:
            try:
                self._publish_queue.put_nowait(message)
            except Exception:
                if self.app:
                    self.app.logger.error("Redis event queue full; local delivery retained")

        if self._kafka_producer is not None:
            try:
                self._kafka_producer.send("aml-events", message)
            except Exception:
                pass

    def queue_for_offline_user(self, user_id, event_name, payload):
        """Queue message for offline user to deliver when they reconnect."""
        if self._redis_client is None:
            if self.app:
                self.app.logger.warning("Redis not available, cannot queue offline message")
            return
        
        try:
            offline_queue_key = f"offline_queue:user:{user_id}"
            message = {"event": event_name, "data": payload, "timestamp": int(time.time())}
            self._redis_client.lpush(offline_queue_key, json.dumps(message))
            self._redis_client.ltrim(offline_queue_key, 0, 99)  # Keep last 100 messages
            self._redis_client.expire(offline_queue_key, 86400)  # 24 hour TTL
            if self.app:
                self.app.logger.info(f"Queued event {event_name} for offline user {user_id}")
        except Exception as e:
            if self.app:
                self.app.logger.error(f"Failed to queue offline message for user {user_id}: {e}")

    def get_offline_queue(self, user_id):
        """Retrieve queued messages for user who just reconnected."""
        if self._redis_client is None:
            return []
        
        try:
            offline_queue_key = f"offline_queue:user:{user_id}"
            messages = self._redis_client.lrange(offline_queue_key, 0, -1)
            self._redis_client.delete(offline_queue_key)
            return [json.loads(msg) for msg in messages]
        except Exception as e:
            if self.app:
                self.app.logger.error(f"Failed to retrieve offline queue for user {user_id}: {e}")
            return []

    def stream_response(self, authorize=None):
        """Generate Server-Sent Events response for streaming."""
        queue = Queue()
        self.add_subscriber(queue)

        def allowed():
            try:
                return authorize is None or bool(authorize())
            except Exception:
                return False

        def generate():
            try:
                if not allowed():
                    return
                yield ": connected\n\n"
                while True:
                    try:
                        message = queue.get(timeout=1)
                    except Empty:
                        if not allowed():
                            return
                        yield ": heartbeat\n\n"
                        continue
                    if not allowed():
                        return
                    yield f"event: {message['event']}\ndata: {json.dumps(message['data'])}\n\n"
            finally:
                if queue in self._subscribers:
                    self._subscribers.remove(queue)
                if self.app is not None:
                    app_subscribers = self.app.config.get("STREAM_SUBSCRIBERS", [])
                    if queue in app_subscribers:
                        app_subscribers.remove(queue)

        return Response(generate(), mimetype="text/event-stream")
