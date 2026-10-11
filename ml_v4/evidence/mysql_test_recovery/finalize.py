"""Record offline recovery preparation without claiming a live MySQL result."""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def digest(relative):
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


paths = [
    'ml_v4/evidence/mysql_test_recovery/recover_partial.py',
    'ml_v4/evidence/mysql_test_recovery/run_local.ps1',
    'ml_v4/evidence/mysql_test_recovery/finalize.py',
    'ml_v4/reports/V4_MYSQL_TEST_RECOVERY_REPORT.md',
]
model = digest('ml_v4/development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib')
assert model == '555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18'
assert 'V4_STAGE4T_TEST_DB_URL' not in os.environ
assert not (ROOT / 'ml_v4/test_binding/.stage4t_authority.json').exists()

decision = {
    'decision': 'B — RECOVERY IMPLEMENTED; LOCAL EXECUTION REQUIRED',
    'current_mysql_state_verified': False,
    'mysql_connections_this_turn': 0,
    'mysql_writes_this_turn': 0,
    'financial_fixtures': 0,
    'v4_activated': False,
    'local_test_credentials_available': False,
    'genuine_test_authority_established': False,
    'frozen_model_sha256': model,
    'artifact_sha256': {path: digest(path) for path in paths},
}
(OUT / 'decision.json').write_text(
    json.dumps(decision, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print('Offline recovery preparation recorded; live MySQL recovery remains pending.')
