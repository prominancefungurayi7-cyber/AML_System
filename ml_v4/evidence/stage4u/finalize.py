"""Bind Stage4U documentation and preservation without database access."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

def sha(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()

stage4s = json.loads((ROOT / 'ml_v4/evidence/stage4s/verification.json').read_text())['hashes']
assert all(sha(name) == record['expected'] for name, record in stage4s.items())
stage4t = json.loads((ROOT / 'ml_v4/evidence/stage4t/decision.json').read_text())['artifact_sha256']
allowed = 'ml_v4/test_binding/v1.py'
assert all(sha(name) == expected for name, expected in stage4t.items() if name != allowed)
assert sha(allowed) != stage4t[allowed]
assert sha('ml_v4/development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib') == (
    '555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18')
review = json.loads((OUT / 'schema_review.json').read_text())
assert sha('ml_v4/evidence/stage4u/application_schema_only.sql') == review['schema_sha256']
sql = (OUT / 'application_schema_only.sql').read_text()
assert sql.count('CREATE TABLE ') == 10 and 'INSERT INTO' not in sql.upper()
assert 'DROP ' not in sql.upper()
service = subprocess.run(['sc.exe', 'query', 'MySQL80'], stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, timeout=5)
preflight = {
    'mysql80_service_running': service.returncode == 0 and 'RUNNING' in service.stdout,
    'dedicated_test_url_configured': bool(os.environ.get('V4_STAGE4T_TEST_DB_URL')),
    'expected_test_server_uuid_configured': bool(os.environ.get('V4_STAGE4T_EXPECTED_SERVER_UUID')),
    'admin_url_configured': bool(os.environ.get('V4_STAGE4U_ADMIN_URL')),
    'test_authority_file_exists': (ROOT / 'ml_v4/test_binding/.stage4t_authority.json').exists(),
    'mysql_connections_attempted': 0, 'mysql_writes': 0,
    'actual_test_database_identity_verified': False,
    'actual_test_grants_verified': False,
    'financial_fixtures_submitted': 0,
    'meaning': 'Service status and configuration presence only; no MySQL identity claim.'
}
(OUT / 'preflight.json').write_text(json.dumps(preflight, indent=2) + '\n')
assert not preflight['dedicated_test_url_configured']
assert not preflight['expected_test_server_uuid_configured']
assert not preflight['test_authority_file_exists']

new_paths = [
    'ml_v4/evidence/stage4u/build_schema.py',
    'ml_v4/evidence/stage4u/install_schema.py',
    'ml_v4/evidence/stage4u/application_schema_only.sql',
    'ml_v4/evidence/stage4u/schema_review.json',
    'ml_v4/evidence/stage4u/preflight.json',
    'ml_v4/evidence/stage4u/finalize.py',
    'ml_v4/reports/V4_STAGE4U_MYSQL_PROVISIONING_REPORT.md',
    allowed,
]
decision = {
    'decision': 'B — ADMINISTRATOR ACTION REQUIRED',
    'database_identity_verified': False,
    'test_authority_established': False,
    'mysql_connections': 0,
    'mysql_writes': 0,
    'new_predictions': 0,
    'new_fits': 0,
    'v4_activated': False,
    'protected_stage4s_paths_exact': len(stage4s),
    'stage4t_paths_unchanged_except': allowed,
    'adapter_before_sha256': stage4t[allowed],
    'adapter_after_sha256': sha(allowed),
    'new_artifact_sha256': {name: sha(name) for name in new_paths},
}
(OUT / 'decision.json').write_text(json.dumps(decision, indent=2) + '\n')
print('PASS: schema-only artifact; 524 preserved paths; one authorized test-adapter fix; no MySQL connection.')
