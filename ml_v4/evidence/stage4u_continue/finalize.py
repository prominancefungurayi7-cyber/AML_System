"""Record offline continuation status without connecting to MySQL."""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

def sha(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()

stage4u = json.loads((ROOT / 'ml_v4/evidence/stage4u/decision.json').read_text())
assert all(sha(name) == value for name, value in stage4u['new_artifact_sha256'].items())
stage4s = json.loads((ROOT / 'ml_v4/evidence/stage4s/verification.json').read_text())['hashes']
assert all(sha(name) == item['expected'] for name, item in stage4s.items())
assert not (ROOT / 'ml_v4/test_binding/.stage4t_authority.json').exists()
assert not os.environ.get('V4_STAGE4T_TEST_DB_URL')
assert not os.environ.get('V4_STAGE4T_EXPECTED_SERVER_UUID')
paths = ['ml_v4/evidence/stage4u_continue/live_checks.py',
         'ml_v4/evidence/stage4u_continue/run_local.ps1',
         'ml_v4/evidence/stage4u_continue/finalize.py',
         'ml_v4/reports/V4_STAGE4U_CONTINUATION_REPORT.md']
record = {'status': 'LOCAL_CREDENTIAL_BINDING_REQUIRED',
          'database_connection_attempted': False,
          'schema_installed': False,
          'test_authority_created': False,
          'live_preflight_completed': False,
          'stage4s_ready': False,
          'protected_stage4s_paths_exact': len(stage4s),
          'stage4u_artifacts_exact': len(stage4u['new_artifact_sha256']),
          'new_artifact_sha256': {name: sha(name) for name in paths}}
(OUT / 'offline_status.json').write_text(json.dumps(record, indent=2) + '\n')
print('OFFLINE: dedicated credentials absent; Stage4U artifacts and 524 inherited paths exact.')
