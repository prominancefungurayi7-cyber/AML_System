"""Stage 4 orchestration with input and V1/application protection checks."""
import json, subprocess, sys, time
from pathlib import Path
from contracts import ROOT,digest,write_json
from train_candidates import run

def hashes(paths,base): return {p.relative_to(base).as_posix():digest(p) for p in sorted(set(paths)) if p.is_file()}
def protected():
    base=ROOT.parent; paths=list(base.glob('*.py'))+[base/'requirements.txt',base/'Dockerfile',base/'railway.json',base/'Procfile']
    for name in ('data','ml','ml_archive','reports','tests','static','templates'): paths += [p for p in (base/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += [p for p in base.glob('*.db') if p.is_file()]
    return hashes(paths,base)
def v2_inputs(): return hashes([p for d in (ROOT/'data',ROOT/'features') for p in d.rglob('*') if p.is_file()],ROOT)
def main():
    if (ROOT/'models/candidates').exists(): raise FileExistsError('Candidate directory exists; overwrite refused')
    for name in ('stage4_candidate_results.json','stage4_domain_results.json','stage4_hard_negative_results.json','stage4_v1_protection.json','stage4_tests.txt'):
        if (ROOT/'reports'/name).exists(): raise FileExistsError(name)
    before=protected(); inputs=v2_inputs()
    tests=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(ROOT/'tests'),'-p','test_stage4*.py','-v'],capture_output=True,text=True)
    print(tests.stdout+tests.stderr,flush=True)
    if tests.returncode: raise RuntimeError('Stage 4 contract tests failed')
    started=time.perf_counter(); summary,domains,hard=run(ROOT/'models/candidates'); elapsed=time.perf_counter()-started
    after=protected(); inputs_after=v2_inputs()
    protection={'result':'PASS' if before==after and inputs==inputs_after else 'FAIL','protected_file_count':len(before),'v2_input_file_count':len(inputs),
        'v1_application_changes':[p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)],
        'v2_input_changes':[p for p in inputs.keys()|inputs_after.keys() if inputs.get(p)!=inputs_after.get(p)]}
    write_json(ROOT/'reports/stage4_v1_protection.json',protection)
    with (ROOT/'reports/stage4_tests.txt').open('x',encoding='utf-8',newline='\n') as f: f.write(tests.stdout+tests.stderr)
    if protection['result']!='PASS': raise RuntimeError('Protection check failed')
    if summary['selected_reproducibility']['result']!='PASS': raise RuntimeError('Selected candidate is not reproducible')
    print(json.dumps({'primary':summary['primary_candidate'],'secondary':summary['secondary_candidate'],'elapsed_seconds':elapsed,'protection':'PASS'},indent=2),flush=True)
if __name__=='__main__': main()
