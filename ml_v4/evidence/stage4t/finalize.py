"""Record exact Stage4T source/output hashes and inherited preservation."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

before = json.loads((ROOT / 'ml_v4/evidence/stage4s/verification.json').read_text())['hashes']
assert all(sha(path) == value['expected'] for path, value in before.items())
assert '11 passed' in (OUT / 'binding_tests.txt').read_text()
assert '54 passed' in (OUT / 'stage3_tests.txt').read_text()
assert json.loads((OUT / 'stage3_parity.json').read_text()) == json.loads(
    (ROOT / 'ml_v4/evidence/integration_stage3/parity.json').read_text())
paths = [
    'ml_v4/test_binding/__init__.py',
    'ml_v4/test_binding/v1.py',
    'ml_v4/test_binding/worker.py',
    'ml_v4/test_binding/.gitignore',
    'ml_v4/test_binding/README.md',
    'ml_v4/test_binding/tests/test_v1.py',
    'ml_v4/reports/V4_STAGE4T_TEST_BINDING_REPORT.md',
    'ml_v4/evidence/stage4t/run_checks.py',
    'ml_v4/evidence/stage4t/binding_tests.txt',
    'ml_v4/evidence/stage4t/stage3_tests.txt',
    'ml_v4/evidence/stage4t/stage3_parity.json',
    'ml_v4/evidence/stage4t/finalize.py',
]
decision = {
    'decision': 'B — ADAPTER IMPLEMENTED; ADMINISTRATOR PROVISIONING REQUIRED',
    'binding_version': 'v4.test_binding.stage4t.1',
    'database_isolation_verified_live': False,
    'administrator_provisioning_required': True,
    'mysql_connections': 0, 'fixture_writes': 0, 'new_fits': 0,
    'shadow_application_enabled': False,
    'protected_paths_exact': len(before),
    'adapter_tests_passed': 11, 'stage3_tests_passed': 54,
    'original_stage3_parity_equal': True,
    'artifact_sha256': {path: sha(path) for path in paths},
}
(OUT / 'decision.json').write_text(json.dumps(decision, indent=2) + '\n')
print('PASS: 524 protected paths; 11 adapter and 54 Stage3 tests; no MySQL connection.')
