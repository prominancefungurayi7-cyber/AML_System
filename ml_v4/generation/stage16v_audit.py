"""Read-only named-input audit and nonsecret fixture runner; new evidence only."""
from pathlib import Path
import hashlib
import json
import platform
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'ml_v4/evidence/stage16v'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read(p):
    return json.loads((ROOT / p).read_text(encoding='utf-8'))

def save(name, value):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n')

def command(args):
    r = subprocess.run(args, cwd=ROOT, capture_output=True)
    return {'command': args, 'exit_code': r.returncode,
            'stdout': r.stdout.decode('utf-8', errors='replace'),
            'stderr': r.stderr.decode('utf-8', errors='replace')}

def main():
    manifests = [
        ('ml_v4/design/v4_stage15_verification.json', 'ml_v4/design'),
        ('ml_v4/design/amendments/v4_stage15a_manifest.json', 'ml_v4/design/amendments'),
        ('ml_v4/design/challenge/challenge_decision.json', 'ml_v4/design/challenge'),
        ('ml_v4/evidence/stage16u/stage16u_decision.json', '')]
    checks, before = {}, {}
    for manifest, base in manifests:
        before[manifest] = sha(ROOT / manifest)
        rows = {}
        for rel, expected in read(manifest)['artifact_sha256'].items():
            name = (Path(base) / rel).as_posix()
            actual = sha(ROOT / name)
            before[name] = actual
            rows[name] = {'expected': expected, 'actual': actual, 'matches': actual == expected}
        checks[manifest] = rows
    # Explicit public/source paths only. Never traverse an evaluation tree.
    for name in [
        'ml_v4/reports/V4_STAGE16R_DATASET_GENERATION_AUDIT.md',
        'ml_v4/reports/V4_STAGE16S_FAMILY_SUPPORT_REVIEW.md',
        'ml_v4/evidence/stage16r/holdout_public_certificate.json',
        'ml_v4/evidence/stage16r/preflight.json',
        'ml_v4/evidence/stage16s/stage16s_decision.json',
        'ml_v4/evidence/stage16s/holdout_boundary_verification.json',
        'ml_v4/generation/stage16r_generator.py',
        'ml_v4/generation/stage16r_evaluator.py',
        'server.py', 'experimental_v3/service.py', 'experimental_v3/web.py']:
        before[name] = sha(ROOT / name)
    ps = 'powershell.exe'
    observations = [command([ps, '-NoProfile', '-Command', c]) for c in [
        'whoami /all',
        'Get-LocalUser | Select-Object Name,Enabled,PrincipalSource | ConvertTo-Json',
        'Get-LocalGroupMember -Group Administrators | Select-Object Name,PrincipalSource | ConvertTo-Json',
        'Get-Acl . | Select-Object Owner,AccessToString | ConvertTo-Json',
        'Get-Service EventLog,WinRM -ErrorAction Continue | Select-Object Name,Status | ConvertTo-Json',
        'Get-Command Get-Secret,Get-SecretVault -ErrorAction SilentlyContinue | Select-Object Name,Source | ConvertTo-Json']]
    save('environment_audit.json', {'observations': observations,
        'scope': 'Local host only; no credentials, remote infrastructure or sealed paths inspected.',
        'dual_identity_access_tests': 'NOT_RUN: no independent custodian identity or endpoint supplied',
        'independent_admin_verified': False,
        'event_log_limit': 'Running EventLog does not demonstrate immutable or independently controlled logging.'})
    missing = 'ml_archive/models/aml_ai_model.pkl'
    expected = read('ml_v4/design/amendments/v4_stage15a_manifest.json')['protection']['before'][missing]
    blob = subprocess.run(['git', 'show', 'HEAD:' + missing], cwd=ROOT, capture_output=True)
    actual = hashlib.sha256(blob.stdout).hexdigest() if blob.returncode == 0 else None
    validator = command([sys.executable, '-B', 'ml_v4/design/amendments/validate_stage15a.py'])
    save('historical_snapshot_gap.json', {'path': missing, 'working_tree_exists': (ROOT / missing).exists(),
        'expected_sha256': expected, 'git_head_blob_sha256': actual,
        'git_blob_matches': actual == expected, 'git_exit_code': blob.returncode,
        'validator': validator, 'restoration_performed': False,
        'resolution': 'Exact archive bytes must be restored from a verified historical source in a complete preservation checkout; rerun the unchanged validator. A matching Git blob alone does not complete the full snapshot. No historical artifact or check was edited.'})
    fixture = ROOT / 'ml_v4/generation/stage16v_fixture.py'
    with tempfile.TemporaryDirectory(prefix='stage16v_nonsecret_') as td:
        db = str(Path(td) / 'fixture.sqlite')
        def call(op):
            return command([sys.executable, '-B', str(fixture), db, op])
        denied_unissued = call('consume')
        authorized = call('authorize')
        with ThreadPoolExecutor(max_workers=8) as pool:
            race = list(pool.map(call, ['consume'] * 8))
        reauthorize, replay = call('authorize'), call('consume')
        passed = (denied_unissued['stdout'].strip() == 'DENIED'
            and authorized['stdout'].strip() == 'ALLOWED'
            and sum(r['stdout'].strip() == 'ALLOWED' for r in race) == 1
            and sum(r['stdout'].strip() == 'DENIED' for r in race) == 7
            and reauthorize['stdout'].strip() == replay['stdout'].strip() == 'DENIED'
            and all(r['exit_code'] == 0 for r in [denied_unissued, authorized, *race, reauthorize, replay]))
        save('authorization_fixture.json', {'passed': passed, 'unissued': denied_unissued,
            'authorize': authorized, 'concurrent_separate_processes': race,
            'reauthorize_after_restart': reauthorize, 'consume_after_restart': replay,
            'production_authority': False, 'independent_append_only_log_verified': False,
            'limitation': 'SQLite transactions serialize consumption across process restarts. Developer deletion, database rollback and audit edits remain possible. No crash/power-loss, external identity or immutable-store claim. Temporary fixture contains no salt, entities or events.'})
        assert passed
    runtime = command([sys.executable, '-B', '-c', 'import sys,numpy,sqlite3; print(sys.version); print(numpy.__version__); print(sqlite3.sqlite_version)'])
    save('reproducibility_readiness.json', {'runtime': runtime, 'platform': platform.platform(),
        'python_executable_sha256': sha(Path(sys.executable)),
        'reference': {'python': '3.14.3', 'numpy': '2.4.3'},
        'production_environment_frozen': False,
        'required': ['Independently held artifact and wheel hashes, offline installation lock including transitive dependencies',
            'OS/runtime image digest, hardware, threads, locale, UTC, source and serialization hashes',
            'Run unchanged implementation fixtures in that image before source/environment freeze',
            'One authorized salt only after separate generation approval; same-salt byte replay inside custody'],
        'no_rng_or_candidate_schedule_instantiated': True})
    after = {name: sha(ROOT / name) for name in before}
    save('preservation_verification.json', {'manifest_checks': checks, 'before': before, 'after': after,
        'changed_paths': [n for n in before if before[n] != after[n]],
        'scope': 'Explicit design, report, public evidence, source and integration paths only. Existing dataset bytes and sealed contents not opened or hashed. Full historical snapshot remains incomplete.'})
    print(json.dumps({'fixture_passed': passed, 'protected_paths': len(before),
        'manifest_mismatches': sum(not r['matches'] for rows in checks.values() for r in rows.values()),
        'git_archive_matches': actual == expected, 'validator_exit': validator['exit_code']}))

if __name__ == '__main__':
    main()
