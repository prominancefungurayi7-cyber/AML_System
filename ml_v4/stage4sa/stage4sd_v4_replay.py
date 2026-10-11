"""Read-only frozen V4 replay against an existing disposable transaction."""
import hashlib
import json
import os
from pathlib import Path

from ml_v4.frozen_inference import service as frozen
from ml_v4.test_binding import v1

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'ml_v4/evidence/stage4sd/v4_readonly_replay.json'


def run():
    authority = v1.load_authority()
    if (authority['server_uuid'] != 'd441b7bb-43f6-11f1-a2d8-0a0027000005'
            or os.environ.get('V4_STAGE4T_EXPECTED_SERVER_UUID') != authority['server_uuid']):
        raise RuntimeError('Test server identity not pinned')
    path = ROOT / frozen.MODEL_PATH
    if hashlib.sha256(path.read_bytes()).hexdigest() != frozen.MODEL_SHA or frozen.THRESHOLD != .5:
        raise RuntimeError('Frozen V4 identity changed')
    db = v1.connection(authority)
    try:
        before = {name: db.execute('SELECT COUNT(*) AS n FROM ' + name).fetchone()['n']
                  for name in ('transactions', 'v4_shadow_results', 'alerts')}
        row = db.execute('SELECT body FROM v4_shadow_results WHERE transaction_id=?', (4,)).fetchone()
        if row is None:
            raise RuntimeError('Existing V4 result missing')
        stored = json.loads(row['body'])
        if stored['status'] != 'success' or stored['model_sha256'] != frozen.MODEL_SHA:
            raise RuntimeError('Existing V4 result invalid')
    finally:
        db.rollback()
        db.close()
    replay = v1.infer(4)
    if (replay['status'] != 'success' or replay['threshold'] != .5
            or replay['observation_scope'] != v1.SCOPE
            or replay['history_status'] != 'COMPLETE_VERIFIED'
            or replay['prediction'] != stored['prediction']
            or abs(replay['suspicious_probability'] - stored['suspicious_probability']) > 1e-12):
        raise RuntimeError('Read-only frozen V4 replay failed')
    db = v1.connection(authority)
    try:
        after = {name: db.execute('SELECT COUNT(*) AS n FROM ' + name).fetchone()['n']
                 for name in before}
        current = db.execute('SELECT body FROM v4_shadow_results WHERE transaction_id=?', (4,)).fetchone()
        if after != before or current is None or json.loads(current['body']) != stored:
            raise RuntimeError('Read-only replay changed persisted state')
    finally:
        db.rollback()
        db.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({'status': 'PASS', 'transaction_id': 4,
                               'model_sha256': frozen.MODEL_SHA, 'threshold': frozen.THRESHOLD,
                               'prediction': replay['prediction'],
                               'suspicious_probability': replay['suspicious_probability'],
                               'history_status': replay['history_status'],
                               'stored_prediction': stored['prediction'],
                               'stored_suspicious_probability': stored['suspicious_probability'],
                               'counts_unchanged': True, 'shadow_body_unchanged': True},
                              indent=2, sort_keys=True) + '\n', encoding='utf-8')


if __name__ == '__main__':
    try:
        run()
    except Exception as exc:
        print('Stage4S-D frozen replay stopped: ' + type(exc).__name__)
        raise SystemExit(1)
