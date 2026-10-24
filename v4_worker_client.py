"""Bounded, serialized requests to a reusable isolated V4 interpreter."""
import atexit
import json
import queue
import subprocess
import threading

_lock = threading.Lock()
_child = None
_responses = None


def close():
    global _child, _responses
    child, _child = _child, None
    _responses = None
    if child is not None:
        if child.poll() is None:
            child.kill()
        child.wait(timeout=5)
        child.stdin.close()
        child.stdout.close()


def _start():
    global _child, _responses
    import v4_shadow as shadow
    child = subprocess.Popen(
        [str(shadow.PYTHON), '-I', '-B', str(shadow.LAUNCHER), '--serve'],
        cwd=str(shadow.ROOT), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, shell=False,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    responses = queue.Queue(maxsize=1)
    _child, _responses = child, responses

    def read():
        try:
            while True:
                line = child.stdout.readline(shadow.MAX_OUTPUT + 1)
                if not line or len(line) > shadow.MAX_OUTPUT:
                    responses.put_nowait(None)
                    return
                responses.put_nowait(line)
        except (OSError, ValueError, queue.Full):
            if child.poll() is None:
                child.kill()
    threading.Thread(target=read, daemon=True).start()


def invoke(tx, source_digest, server_uuid):
    import v4_shadow as shadow
    if type(tx) is not int or not 0 < tx < 2**63:
        return shadow.error(tx, 'INVALID_EVENT')
    with _lock:
        try:
            if _child is None or _child.poll() is not None:
                close()
                _start()
            payload = json.dumps(dict(transaction_id=tx, source_digest=source_digest,
                                      server_uuid=server_uuid)).encode() + b'\n'
            _child.stdin.write(payload)
            _child.stdin.flush()
            line = _responses.get(timeout=shadow.TIMEOUT)
            if line is None:
                raise ValueError('Worker ended without a result')
            return shadow.validate(json.loads(line), tx)
        except queue.Empty:
            close()
            return shadow.error(tx, 'RESOURCE_ERROR')
        except (OSError, ValueError, TypeError, KeyError):
            close()
            return shadow.error(tx, 'INFERENCE_ERROR')


atexit.register(close)
