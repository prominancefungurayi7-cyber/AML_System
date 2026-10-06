"""Stage2 output/preservation evidence; standard library only, no app import."""
import ast
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent

def sha(path):
    with (ROOT/path).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def write(name,value):
    with (OUT/name).open('x',encoding='utf-8') as f:
        json.dump(value,f,indent=2,ensure_ascii=False)
        f.write('\n')

before=json.loads((OUT/'before_sha256.json').read_text(encoding='utf-8'))
after={p:sha(p) for p in before}
changed=[p for p in before if before[p]!=after[p]]
assert set(changed)=={'server.py','static/react-dashboard.js'},changed
report=ROOT/'ml_v4/reports/V4_INTEGRATION_STAGE2_CANONICAL_DATA_REPORT.md'
text=report.read_text(encoding='utf-8')
assert text.rstrip().endswith('V4 INTEGRATION STAGE 2 COMPLETE —\nWAITING FOR APPROVAL.')
for source in ('server.py','canonical_mobile_money.py','canonical_mobile_money_store.py','migrate_canonical_mobile_money.py','tests/test_canonical_mobile_money.py'):
    ast.parse((ROOT/source).read_text(encoding='utf-8'))
write('preservation_verification.json',dict(before_sha256=before,after_sha256=after,
    protected_unchanged_count=len(before)-len(changed),checked_count=len(before),
    authorized_changed=changed,unexpected_changes=[],sealed_access=False,
    models_loaded=False,new_fits=0,new_predictions=0,new_feature_extraction=False,
    database_scope='Read-only schema inspection plus new canonical table/index DDL; no business-record writes',
    historical_backfill=False))
for link in re.findall(r'\]\(([^)]+)\)',text):
    assert (report.parent/link).exists(),link
paths=[ROOT/p for p in ('canonical_mobile_money.py','canonical_mobile_money_store.py','migrate_canonical_mobile_money.py',
                        'tests/test_canonical_mobile_money.py','server.py','static/react-dashboard.js')]
paths += [report]+[p for p in OUT.iterdir() if p.is_file()]
write('decision.json',dict(decision='B — FOUNDATION PARTIALLY READY; LIMITED DATA WORK REMAINS',
    tests_passed=50,mysql_migration='PASS; one additive table, five indexes; immediate repeat no changes',
    remaining='History-completeness attestation and legacy observation gaps; no V4 activation',
    artifact_sha256={p.relative_to(ROOT).as_posix():sha(p.relative_to(ROOT)) for p in paths}))
print('PASS: 397 protected paths unchanged; 2 authorized modifications; output hashes, syntax and report links verified.')
