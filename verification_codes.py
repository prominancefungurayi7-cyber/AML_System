"""Short-lived, single-use codes for the local application's single process.

Only an opaque challenge identifier belongs in Flask's readable session cookie.
A restart expires pending challenges; users can request a new code.
"""
import secrets
import threading
import time


class VerificationCodes:
    def __init__(self, ttl=600, attempts=5, capacity=1024):
        self.ttl, self.attempts, self.capacity = ttl, attempts, capacity
        self._pending = {}
        self._lock = threading.Lock()

    def issue(self, purpose):
        now = time.monotonic()
        with self._lock:
            self._pending = {k: v for k, v in self._pending.items() if v[2] > now}
            if len(self._pending) >= self.capacity:
                raise RuntimeError("Verification requests are busy. Please try again later.")
            challenge = secrets.token_urlsafe(32)
            code = str(secrets.randbelow(900000) + 100000)
            self._pending[challenge] = (purpose, code, now + self.ttl, self.attempts)
            return challenge, code

    def discard(self, challenge):
        with self._lock:
            self._pending.pop(challenge, None)

    def consume(self, challenge, purpose, code):
        with self._lock:
            value = self._pending.pop(challenge, None)
            if value is None or value[2] <= time.monotonic() or value[0] != purpose:
                return False
            if secrets.compare_digest(value[1].encode(), str(code).encode()):
                return True
            if value[3] > 1:
                self._pending[challenge] = (*value[:3], value[3] - 1)
            return False
