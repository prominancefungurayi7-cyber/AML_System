"""Explicit protection scope. Never walk any data/evaluation directory."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ('ml_v3/data/manifests/evaluation_content_commitment.json',
          'ml_v3/reports/V3_STAGE9_HOLDOUT_SEAL.json')
DIRECTORIES = ('templates', 'static', 'scripts', 'tests', 'ml', 'ml_archive',
               'reports', 'ml_v2/src', 'ml_v2/tests', 'ml_v2/design', 'ml_v2/reports',
               'ml_v2/data/development', 'ml_v2/features/development',
               'ml_v3/design', 'ml_v3/data/development', 'ml_v3/features/development/train',
               'ml_v3/features/development/validation')

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def snapshot():
    base = ROOT.parent
    paths = set()
    for pattern in ('*.py', '*.json', '*.txt', '*.sql', '*.md', 'Dockerfile', 'Procfile', '.env*', '.gitignore'):
        paths.update(p for p in base.glob(pattern) if p.is_file())
    for rel in DIRECTORIES:
        folder = base / rel
        if folder.exists():
            paths.update(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts)
    paths.update(base/p for p in PUBLIC)
    paths.add(ROOT/'data/manifests/development_manifest.json')
    paths.update((ROOT/'reports').glob('*STAGE9*'))
    paths.update((ROOT/'reports').glob('*STAGE10_*'))
    paths.update((ROOT/'reports').glob('stage10_*.json'))
    for name in ('contracts.py', 'reference_evaluator.py', 'reference.py', 'generate_v3.py', 'run_stage9.py', 'audit_v3.py'):
        paths.add(ROOT/'src'/name)
    files = {p.relative_to(base).as_posix(): sha(p) for p in sorted(paths) if p.is_file()}
    return {'files': files, 'public': {p: files[p] for p in PUBLIC},
            'scope': list(DIRECTORIES),
            'excluded': 'All evaluation/holdout data and unpartitioned historical datasets; no claim to hash these prohibited bytes.'}

def compare(before, after):
    changed = [p for p in sorted(before['files'].keys() | after['files'].keys()) if before['files'].get(p) != after['files'].get(p)]
    return {'result': 'PASS' if not changed else 'FAIL', 'before': before, 'after': after, 'changed': changed,
            'public_commitment_unchanged': before['public'] == after['public']}

if __name__ == '__main__':
    p = ROOT/'reports/stage10a_protection_before.json'
    with p.open('x', encoding='utf-8') as f:
        json.dump(snapshot(), f, indent=2, sort_keys=True)
    print(p)
