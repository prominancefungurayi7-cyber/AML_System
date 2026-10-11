"""Read-only pinned inference-runtime check, run in the frozen interpreter."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml_v4.frozen_inference.service import runtime, sources, MODEL_SHA, THRESHOLD


def run():
    versions = runtime()
    sources()
    if THRESHOLD != 0.50:
        raise RuntimeError('Frozen threshold changed')
    return {'status': 'PASS', 'model_sha256': MODEL_SHA,
            'threshold': THRESHOLD, 'runtime': versions}


if __name__ == '__main__':
    try:
        print(json.dumps(run(), sort_keys=True))
    except Exception as exc:
        print('Pinned inference runtime check stopped: ' + type(exc).__name__)
        raise SystemExit(1)
