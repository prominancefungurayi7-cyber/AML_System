"""Documentation evidence only. Never imports application or ML runtime modules."""
import ast
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REPORT = ROOT / 'ml_v4/reports/V4_INTEGRATION_STAGE1_READINESS_AUDIT.md'

def read(p):
    return json.loads((ROOT / p).read_text(encoding='utf-8'))

def sha(p):
    with (ROOT / p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def save(name, value):
    with (OUT / name).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')

def inventory():
    expected = read('ml_v4/evidence/stage23/preservation_verification.json')['after_sha256']
    expected.update(read('ml_v4/evidence/stage23/stage23_decision.json')['artifact_sha256'])
    for p, h in expected.items():
        assert sha(p) == h, 'Historical mismatch: ' + p
    files = set(expected)
    files.add('ml_v4/evidence/stage23/stage23_decision.json')
    # Nonrecursive application source roots, then only public UI trees.
    for pattern in ('*.py', '*.sql'):
        files.update(p.relative_to(ROOT).as_posix() for p in ROOT.glob(pattern))
    for directory in ('static', 'templates'):
        files.update(p.relative_to(ROOT).as_posix() for p in (ROOT / directory).rglob('*') if p.is_file())
    files.update(('Procfile', 'Dockerfile', 'requirements.txt', 'railway.json', 'README.md'))
    return {p: sha(p) for p in sorted(files)}

if sys.argv[1] == 'snapshot':
    before = inventory()
    save('before_sha256.json', before)
    freeze = read('ml_v4/evidence/stage23/development_candidate_freeze.json')
    checks = {key: {'path': v['path'], 'expected': v['sha256'], 'actual': sha(v['path'])}
              for key, v in freeze['artifacts'].items()}
    assert all(v['expected'] == v['actual'] for v in checks.values())
    save('freeze_verification.json', {'freeze': freeze['freeze_id'], 'checks': checks,
         'method': 'Byte hashing only; no deserialization or model execution',
         'historical_checks': 344, 'live_database_access': False})
    source_index = {}
    for p in before:
        if '/' not in p and p.endswith('.py'):
            tree = ast.parse((ROOT / p).read_text(encoding='utf-8-sig'))
            source_index[p] = [{'name': n.name, 'line': n.lineno, 'end_line': n.end_lineno,
                                'decorators': [ast.unparse(d) for d in n.decorator_list]}
                               for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
    save('application_source_index.json', source_index)
    spec = read('ml_v4/design/v4_feature_spec.json')
    rows = []
    for f in spec['features']:
        i = f['index']
        if i == 1:
            raw, db, gap, graph = 'amount_minor,currency', 'amount,currency', 'DOUBLE and unbounded input; exact cents/range not guaranteed', 'none'
        elif i == 2:
            raw, db, gap, graph = 'transaction_type,channel,agent_id,serviced_wallet,agent_flow_direction', 'transaction_type,channel,agent_id,sender_account,receiver_account', 'Cash roles and channel vocabulary ambiguous; two role fields absent', 'none'
        elif 19 <= i <= 22:
            raw, db, gap, graph = 'transaction_id,event_timestamp,sender_wallet,receiver_wallet,transaction_type,amount_minor', 'id,timestamp,sender_account,receiver_account,transaction_type,amount', 'Complete directed history, exact money and UTC keys unverified', 'All chronological simple W2W return paths, 1..5 prior edges; receiver to current sender; no amount filter'
        elif 13 <= i <= 18:
            raw, db, gap, graph = 'transaction_id,event_timestamp,sender_wallet,receiver_wallet,transaction_type', 'id,timestamp,sender_account,receiver_account,transaction_type', 'Directed canonical history and first-observation completeness unverified', 'Directed W2W incident edges; incoming receiver or outgoing sender'
        elif 25 <= i <= 38 or i == 40:
            raw, db, gap, graph = 'transaction_id,event_timestamp,agent_id,serviced_wallet,transaction_type,agent_flow_direction,amount_minor', 'id,timestamp,agent_id,transaction_type,amount plus NEW serviced_wallet,agent_flow_direction', 'Agent optional; serviced endpoint absent; no canonical service history', 'none; agent service history across wallets'
        else:
            raw, db, gap, graph = 'transaction_id,event_timestamp,sender_wallet,receiver_wallet,transaction_type,serviced_wallet,amount_minor', 'id,timestamp,sender_account,receiver_account,transaction_type,amount plus NEW serviced_wallet', 'Cash subject, exact money, complete UTC-keyed activity and first observation unverified', 'Prior W2W funding anchor plus subsequent cash/activity' if i in (23,24) else 'none; incoming W2W contributes observation age only'
        rows.append({**f, 'required_raw_fields': raw.split(','), 'database_fields': db,
                     'graph_history': graph, 'current_mysql_supply': 'Partial schema only; deployed records not inspected',
                     'additional_logic_required': 'Canonical validation plus frozen keyed replay/state; no legacy feature substitution',
                     'currently_computable': 'NOT VERIFIED for exact live inference', 'semantic_gap': gap})
    assert [x['name'] for x in rows] == freeze['semantic_order']
    save('feature_feasibility.json', {'scope': 'All Event fields required for validation even when a formula uses fewer; physical schema is source evidence, not live introspection', 'features': rows})
    lines = ['# Forty-feature feasibility matrix', '', 'Exact frozen order. All rows require the full validated Event envelope; listed raw fields are formula dependencies. Current MySQL supply is partial/unverified and no live feature is certified. Every row needs canonical keyed replay/state. See report for precise window endpoints, eligibility and cold-start semantics.', '', '| # / feature | Raw fields / database columns | Window / subject | Graph | Missingness / feasibility gap |', '| --- | --- | --- | --- | --- |']
    for r in rows:
        cells = [str(r['index'])+' '+r['name'], ', '.join(r['required_raw_fields'])+' / '+r['database_fields'], r['window']+' / '+r['entity'], r['graph_history'], r['missing_semantics']+'; '+r['semantic_gap']]
        lines.append('| '+' | '.join(x.replace('|','/') for x in cells)+' |')
    (OUT / 'feature_feasibility.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print('Snapshot complete:', len(before), 'protected paths; 40 feature definitions; all freeze references match.')
elif sys.argv[1] == 'finalize':
    before = read('ml_v4/evidence/integration_stage1/before_sha256.json')
    after = {p: sha(p) for p in before}
    changed = [p for p in before if before[p] != after[p]]
    assert not changed, changed
    text = REPORT.read_text(encoding='utf-8')
    assert text.rstrip().endswith('V4 INTEGRATION STAGE 1 COMPLETE —\nWAITING FOR APPROVAL.')
    assert len(read('ml_v4/evidence/integration_stage1/feature_feasibility.json')['features']) == 40
    save('preservation_verification.json', {'count': len(before), 'before_sha256': before, 'after_sha256': after,
         'changed': changed, 'sealed_bytes_excluded': True, 'live_database_access': False,
         'model_execution': False, 'application_imports': False, 'new_fits': 0,
         'historical_Stage15A_snapshot_gap': 'Unchanged; inherited broader archive gap not repaired'})
    artifacts = [p for p in OUT.iterdir() if p.is_file()] + [REPORT]
    save('decision.json', {'decision': 'D — V4 INTEGRATION BLOCKED BY INCOMPATIBLE DATA OR ARTIFACTS',
         'blocker': 'Current application data semantics incomplete/ambiguous; frozen artifacts match',
         'protected_count': len(before), 'implementation_authorized_by_report': False,
         'artifact_sha256': {p.relative_to(ROOT).as_posix(): sha(p.relative_to(ROOT)) for p in artifacts}})
    print('Final preservation PASS:', len(before), 'paths unchanged; decision D; documentation only.')
else:
    raise SystemExit('snapshot or finalize required')
