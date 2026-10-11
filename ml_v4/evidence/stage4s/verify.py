"""Read-only source/integrity gate; no database or application imports."""
import ast
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

def read(p):
    return json.loads((ROOT / p).read_text(encoding='utf-8-sig'))

def digest(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()

expected = read('ml_v4/evidence/integration_stage4r/preservation_verification.json')['actual_sha256']
expected.update(read('ml_v4/evidence/integration_stage4r/decision.json')['artifacts'])
for p in ['ml_v4/evidence/integration_stage4r/decision.json']:
    expected[p] = digest(p)
results = {p: {'expected': h, 'actual': digest(p)} for p, h in sorted(expected.items())}
assert all(r['expected'] == r['actual'] for r in results.values()), 'Protected artifact mismatch'
recovered = read('ml_v4/evidence/integration_stage3r/missing_files.json')
assert all(digest(p) == h for p, h in recovered.items())
model = 'ml_v4/development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib'
assert digest(model) == '555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18'

# Execute only the parsed connector guard, with a synthetic URL and no imports,
# connection function, credentials, network access or application startup.
cli_path = 'ml_v4/frozen_inference/cli.py'
tree = ast.parse((ROOT / cli_path).read_text(encoding='utf-8-sig'))
function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'connection')
guard = next(n for n in function.body if isinstance(n, ast.If))
code = compile(ast.fix_missing_locations(ast.Module(body=[guard], type_ignores=[])), cli_path, 'exec')
rejected = False
try:
    exec(code, {'p': urlparse('mysql://127.0.0.1/v4_stage4s_disposable'), 'ValueError': ValueError, '__builtins__': {}})
except ValueError:
    rejected = True
assert rejected
history = (ROOT / 'ml_v4/frozen_inference/history.py').read_text()
assert "fetchone()['db']!='aml'" in history
assert 'integration_stage2a2/observation_boundary.json' in history
worker = (ROOT / 'ml_v4/shadow_integration/worker.py').read_text()
assert 'from ml_v4.frozen_inference.cli import connection' in worker
assert 'integration_stage2a2/observation_boundary.json' in worker
record = {
    'decision': 'C — ACTIVATION BLOCKED BY INTEGRATION FAILURE',
    'blocker': 'Approved connector/history gate and worker are bound to aml and original observation boundary; separate test database is rejected.',
    'connector_guard_test': 'PASS: actual parsed guard rejects synthetic separate database name before any connection',
    'database_isolation_established': False,
    'database_connections': 0, 'fixture_writes': 0, 'application_started': False,
    'new_predictions': 0, 'new_fits': 0, 'sealed_access': False,
    'regression_rerun': 'NOT_RUN: stopped at mandatory isolation gate',
    'recovered_files_exact': len(recovered),
    'protected_paths_verified': len(results), 'hashes': results,
    'scope': 'Explicit Stage4R inherited/current paths; no sealed tree enumeration.'}
(OUT / 'verification.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in record.items() if k != 'hashes'}))
