"""Opaque, revocable login sessions; Redis shares idle expiry across instances."""
import secrets
import threading
import time


class AuthSessions:
    def __init__(self):
        self.local = {}
        self.lock = threading.Lock()

    def create(self, user_id, ttl, redis=None):
        token = secrets.token_urlsafe(32)
        if redis is not None:
            redis.set('aml:auth:' + token, str(user_id), ex=ttl)
        else:
            with self.lock:
                self.local = {k: v for k, v in self.local.items() if v[1] > time.time()}
                self.local[token] = (str(user_id), float("inf") if ttl is None else time.time() + ttl)
        return token

    def valid(self, token, user_id, ttl, touch=False, redis=None):
        if not token:
            return False
        if redis is not None:
            value = redis.get('aml:auth:' + token)
            if isinstance(value, bytes):
                value = value.decode()
            if value != str(user_id):
                return False
            return bool(redis.expire('aml:auth:' + token, ttl)) if touch and ttl is not None else True
        with self.lock:
            value = self.local.get(token)
            if not value or value[0] != str(user_id) or value[1] <= time.time():
                self.local.pop(token, None)
                return False
            if touch:
                self.local[token] = (value[0], float("inf") if ttl is None else time.time() + ttl)
            return True

    def revoke(self, token, redis=None):
        if token:
            if redis is not None:
                redis.delete('aml:auth:' + token)
            else:
                with self.lock:
                    self.local.pop(token, None)
