"""Start the local Redis-compatible broker for an interactive Windows launch."""

import os
import json
from pathlib import Path
import socket
import subprocess
import time
from urllib.request import urlopen


def _redis_responds():
    try:
        with socket.create_connection(("127.0.0.1", 6379), timeout=1) as connection:
            connection.settimeout(1)
            connection.sendall(b"*1\r\n$4\r\nPING\r\n")
            return connection.recv(32).startswith(b"+PONG\r\n")
    except OSError:
        return False


def configure_local_realtime(project_root):
    """Set local defaults and start Memurai before server imports initialize Redis."""
    if os.name != "nt":
        return

    try:
        with socket.create_connection(("127.0.0.1", 5000), timeout=1):
            occupied = True
    except OSError:
        occupied = False
    if occupied:
        try:
            with urlopen("http://127.0.0.1:5000/health", timeout=3) as response:
                health = json.load(response)
            if (health.get("service") == "epocash-aml"
                    and health.get("primary_model") == "V4"
                    and health.get("rules_enabled") is True
                    and health.get("realtime", {}).get("redis_connected") is True):
                print("EpoCash AML is already running at http://127.0.0.1:5000 (V4, rules and Redis ready).")
                raise SystemExit(0)
        except SystemExit:
            raise
        except Exception:
            pass
        raise SystemExit("Port 5000 is in use by a different or unhealthy service. Stop it before starting EpoCash AML.")

    os.environ.setdefault("AML_PRIMARY_MODEL", "V4")
    os.environ.setdefault("AML_RULE_ENGINE_ENABLED", "ON")
    os.environ.setdefault("SOCKETIO_ALLOWED_ORIGINS", "http://127.0.0.1:5000")
    os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/0")

    # An explicitly configured broker is managed by its operator.
    if os.environ["REDIS_URL"] != "redis://127.0.0.1:6379/0":
        return
    if _redis_responds():
        return

    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    executable = Path(program_files) / "Memurai" / "memurai.exe"
    if not executable.is_file():
        raise RuntimeError("Memurai is required for local real-time delivery: " + str(executable))

    state_dir = Path(project_root) / "data" / "local-redis"
    state_dir.mkdir(parents=True, exist_ok=True)
    config = state_dir / "memurai.conf"
    if not config.exists():
        config.write_text(
            'bind 127.0.0.1\nprotected-mode yes\nport 6379\n'
            'maxmemory 128mb\nmaxmemory-policy noeviction\n'
            'save ""\nappendonly no\nlogfile "memurai.log"\n',
            encoding="ascii",
        )
    subprocess.Popen(
        [str(executable), str(config)],
        cwd=state_dir,
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(20):
        if _redis_responds():
            return
        time.sleep(0.25)
    raise RuntimeError("Local Redis did not start; inspect data/local-redis/memurai.log")
