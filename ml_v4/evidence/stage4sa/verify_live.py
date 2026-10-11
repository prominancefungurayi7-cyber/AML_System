"""Run the approved Stage4U live verifier with a new evidence location."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from ml_v4.evidence.stage4u_continue import live_checks

live_checks.OUT = Path(__file__).resolve().parent
if __name__ == '__main__':
    try:
        connection, _, _, _, _ = live_checks._connect()
        try:
            setting = connection.execute(
                'SELECT @@GLOBAL.log_bin_trust_function_creators AS allowed').fetchone()['allowed']
            if setting != 0:
                raise RuntimeError('Trigger-creation setting has not been restored OFF')
        finally:
            connection.rollback()
            connection.close()
        live_checks.verify()
    except Exception as exc:
        print('Fresh live verification stopped: ' + type(exc).__name__, file=sys.stderr)
        raise SystemExit(1)
