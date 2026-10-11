"""Record offline Stage4S-A artifacts without claiming live MySQL readiness."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


paths = [
    'ml_v4/stage4sa/__init__.py',
    'ml_v4/stage4sa/coordinator.py',
    'ml_v4/stage4sa/harness.py',
    'ml_v4/stage4sa/live_readiness.py',
    'ml_v4/stage4sa/run_local.ps1',
    'ml_v4/stage4sa/tests/test_harness.py',
    'ml_v4/evidence/stage4sa/verify_live.py',
    'ml_v4/evidence/stage4sa/finalize.py',
    'ml_v4/reports/STAGE4S_A_HARNESS_REPAIR.md',
]
assert sha('server.py') == 'd2598a8042c4a8e6869d58cf613478b160f8bdb41948529549842f96bff6a4e0'
assert sha('ml_v4/test_binding/v1.py') == '4ec57bbdc3f1b0f203f86ab4c723ebdd04029ee001d7164ab1e14aebc83a42dc'
assert sha('ml_v4/test_binding/worker.py') == '50d36d6408267b4768901690c76570705dfaec556f431266c61eb1b8d7422bc5'
model = sha('ml_v4/development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib')
assert model == '555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18'
decision = {
    'decision': 'A — TEST HARNESS READY FOR LOCAL LIVE CHECKS',
    'mysql_connections_this_stage': 0,
    'financial_fixtures_this_stage': 0,
    'new_predictions': 0,
    'new_fits': 0,
    'v4_activated': False,
    'local_live_readiness': 'NOT_RUN_CREDENTIALS_UNAVAILABLE',
    'offline_stage4sa_tests_passed': 5,
    'existing_stage4r_tests_passed': 25,
    'existing_stage4t_tests_passed': 11,
    'inherited_protected_hashes_verified': 524,
    'frozen_model_sha256': model,
    'new_artifact_sha256': {path: sha(path) for path in paths},
}
(OUT / 'decision.json').write_text(
    json.dumps(decision, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print('Stage4S-A offline decision recorded; live checks remain pending.')
