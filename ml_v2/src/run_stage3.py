"""Test, extract twice, reproduce, audit and publish development features only."""
import hashlib, json, shutil, subprocess, sys, tempfile, time
from pathlib import Path
from contracts import ROOT, safe_path, digest, write_json
from feature_pipeline import extract_development, write_matrix, FEATURE_NAMES
from feature_audit import audit

def hashes(root): return {p.relative_to(root).as_posix():digest(p) for p in sorted(root.rglob('*')) if p.is_file()}
def protected_hashes():
    base=ROOT.parent; paths=list(base.glob('*.py'))+[base/'requirements.txt',base/'Dockerfile',base/'railway.json',base/'Procfile']
    for name in ('data','ml','ml_archive','reports','tests','static','templates'): paths += [p for p in (base/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += [p for p in base.glob('*.db') if p.is_file()]
    return {p.relative_to(base).as_posix():digest(p) for p in sorted(set(paths)) if p.is_file()}
def main():
    destination=safe_path(ROOT/'features/development')
    if destination.exists() and any(destination.iterdir()): raise FileExistsError('Development feature output exists; overwrite refused')
    before=protected_hashes(); tmp=safe_path(ROOT/'tmp'); tmp.mkdir(exist_ok=True)
    tests=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(ROOT/'tests'),'-p','test_stage3*.py','-v'],capture_output=True,text=True)
    print(tests.stdout+tests.stderr,flush=True)
    if tests.returncode: raise RuntimeError('Stage 3 tests failed')
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='stage3_',dir=tmp) as work:
        work=Path(work)
        for run in ('run_a','run_b'):
            for partition in ('train','validation'):
                print(f'Extracting {run} {partition}...',flush=True)
                X,y,ids=extract_development(ROOT/'data',partition)
                write_matrix(work/run/partition,X,y,ids)
        h1,h2=hashes(work/'run_a'),hashes(work/'run_b')
        if h1!=h2: raise RuntimeError('Feature reproducibility failed')
        result=audit(work/'run_a')
        if result['failures']: raise RuntimeError(str(result['failures']))
        shutil.copytree(work/'run_a',destination,dirs_exist_ok=True)
        if hashes(destination)!=h1: raise RuntimeError('Published feature hashes differ')
        reproducibility={'result':'PASS','runs':2,'file_count':len(h1),'feature_order_identical':True,'X_identical':True,'y_identical':True,'row_order_identical':True,'output_hashes':h1,'temporary_duplicates_removed_on_exit':True}
    after=protected_hashes(); protection={'result':'PASS' if before==after else 'FAIL','protected_file_count':len(before),'changed':[p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)],'before_hashes':before,'after_hashes':after}
    write_json(ROOT/'reports/stage3_feature_audit.json',result); write_json(ROOT/'reports/stage3_reproducibility.json',reproducibility); write_json(ROOT/'reports/stage3_v1_protection.json',protection)
    with (ROOT/'reports/stage3_tests.txt').open('x',encoding='utf-8',newline='\n') as f: f.write(tests.stdout+tests.stderr)
    if protection['result']!='PASS': raise RuntimeError('V1 protection failed')
    print(f"Stage 3 feature audit PASS; elapsed {time.monotonic()-started:.1f}s",flush=True)
if __name__=='__main__': main()
