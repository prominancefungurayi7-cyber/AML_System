"""Finalize Stage4R documentation using saved evidence; no application imports."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REPORT = ROOT / 'ml_v4/reports/V4_INTEGRATION_STAGE4R_SHADOW_APPLICATION_REPORT.md'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

before = read(OUT / 'before_sha256.json')
changes = read(OUT / 'authorized_application_changes.json')
assert set(changes) == {'server.py', 'templates/compliance_dashboard.html'}
actual = {p: sha(ROOT / p) for p in before}
assert all(actual[p] == (changes[p]['after'] if p in changes else h) for p, h in before.items())
recovered = read(ROOT / 'ml_v4/evidence/integration_stage3r/missing_files.json')
assert len(recovered) == 12
assert all(sha(ROOT / p) == h for p, h in recovered.items())
assert read(OUT / 'stage3_parity.json') == read(ROOT / 'ml_v4/evidence/integration_stage3/parity.json')
assert '25 passed' in (OUT / 'shadow_tests.txt').read_text()
assert '54 passed' in (OUT / 'stage3_tests.txt').read_text()
write('preservation_verification.json', {
    'status': 'PASS', 'named_baseline_paths': len(before),
    'unchanged': len(before) - len(changes), 'authorized_application_changes': changes,
    'recovered_stage3_files': recovered, 'actual_sha256': actual,
    'sealed_content_accessed': False, 'scope': 'Explicit named paths only; not every file on disk.'})
sources = sorted(set(recovered) | {
    'v4_shadow.py', 'server.py', 'templates/compliance_dashboard.html',
    'static/v4-shadow.js', 'tests/test_v4_shadow.py', 'tests/v4_shadow_ui_test.cjs',
    'ml_v4/shadow_integration/worker.py', 'ml_v4/shadow_integration/manage.py',
    'ml_v4/shadow_integration/fixture_worker.py', 'ml_v4/shadow_integration/README.md'})
archive = OUT / 'approved_source_backup.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in sources:
        z.write(ROOT / p, p)
with zipfile.ZipFile(archive) as z:
    assert all(hashlib.sha256(z.read(p)).hexdigest() == sha(ROOT / p) for p in sources)
write('source_protection.json', {
    'source_control_inclusion_allowlist': sources,
    'sha256': {p: sha(ROOT / p) for p in sources},
    'backup_sha256': sha(archive), 'archive_entries_verified': True,
    'git_staged_or_committed': False, 'remote_publication': False,
    'excluded': ['model binaries', 'datasets', 'sealed evaluation', 'credentials', 'runtime environments'],
    'limitation': 'Local source redundancy; not an independent off-machine backup.'})
write('acceptance_summary.json', {
    'shadow_tests_passed': 25, 'stage3_tests_passed': 54,
    'stage3_parity_equal_to_original': True, 'fixed_examples': 128,
    'stage3_preservation_test_exceptions': sorted(changes),
    'four_forms': 'PASS: extracted Flask handler, isolated SQLite, real frozen model; legacy model stubbed',
    'mysql_schema_and_lock_checks': 'PASS',
    'complete_flask_mysql_model_e2e': 'NOT_RUN',
    'browser_visual_test': 'NOT_RUN; Node DOM representation checks passed',
    'new_fits': 0, 'live_predictions': 0, 'decision': 'B'})
assert REPORT.exists()
paths = sources + [str(REPORT.relative_to(ROOT)).replace('\\', '/')]
paths += [str(p.relative_to(ROOT)).replace('\\', '/') for p in OUT.iterdir() if p.is_file() and p.name != 'decision.json']
write('decision.json', {
    'decision': 'B — SHADOW INTEGRATION IMPLEMENTED; LIMITED APPLICATION WORK REMAINS',
    'shadow_default': 'OFF', 'full_mysql_e2e': 'NOT_RUN',
    'artifacts': {p: sha(ROOT / p) for p in sorted(set(paths))},
    'historical_reports_rewritten': False, 'new_fits': 0,
    'production_cutover': False, 'next_stage_started': False})
print(f'PASS: {len(before)-2} unchanged paths, 2 authorized changes, 12 exact recovered files; decision B.')
