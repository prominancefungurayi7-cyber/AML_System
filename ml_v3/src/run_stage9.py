"""Authorized Stage 9 generation, independent structural audit and sealing."""
from __future__ import annotations
import hashlib, json, shutil, tempfile, time
from pathlib import Path
from contracts import ROOT, safe_path, digest, write_json, partition_path, DEVELOPMENT, PARTITIONS
from generate_v3 import materialize, convert_truth, make_manifest, SEED
from reference_evaluator import evaluate_rows
from audit_v3 import audit

def hashes(folder): return {p.relative_to(folder).as_posix():digest(p) for p in sorted(folder.rglob('*')) if p.is_file()}
def development_hashes():
    paths=[]
    for name in ('data','ml','ml_archive','reports','tests','static','templates','scripts'):
        p=ROOT.parent/name
        if p.exists(): paths.extend(x for x in p.rglob('*') if x.is_file() and '__pycache__' not in x.parts)
    paths.extend(ROOT.parent.glob('*.py')); paths.extend(ROOT.parent.glob('*.txt')); paths.extend(ROOT.parent.glob('*.json'))
    # Explicit V2/V1/application paths only; no V2 raw-data or holdout walks.
    return {str(p.relative_to(ROOT.parent)):digest(p) for p in sorted(set(paths)) if p.is_file() and not str(p).startswith(str(ROOT/'data'))}

def main():
    if (ROOT/'data').exists() and any((ROOT/'data').iterdir()): raise FileExistsError('ml_v3/data exists')
    before=development_hashes(); start=time.perf_counter(); tmp=ROOT/'tmp'; tmp.mkdir(exist_ok=True)
    runs=[]
    with tempfile.TemporaryDirectory(prefix='v3_generation_',dir=tmp) as work:
        work=safe_path(work)
        for label in ('run_a','run_b'):
            run=materialize(work/label); summary=convert_truth(run); runs.append((run,summary))
            result=audit(run,evaluate_rows)
            if result['result']!='PASS':
                write_json(ROOT/'reports/V3_STAGE9_FAILED_AUDIT.json',result); raise RuntimeError(result['failures'])
        ha,hb=hashes(runs[0][0]),hashes(runs[1][0]); development_a={k:v for k,v in ha.items() if k.startswith('development/')}; development_b={k:v for k,v in hb.items() if k.startswith('development/')}
        if development_a!=development_b: raise RuntimeError('development reproducibility failed')
        shutil.copytree(runs[0][0],ROOT/'data',dirs_exist_ok=False)
        final=audit(ROOT/'data',evaluate_rows)
        if final['result']!='PASS': raise RuntimeError(final['failures'])
        certificate=make_manifest(ROOT/'data',runs[0][1])
        reproducibility={'result':'PASS','seed':SEED,'runs':2,'development_hashes_identical':True,'development_file_count':len(development_a),'full_temporary_hashes_identical':ha==hb,'evaluation_hashes_established_during_generation':True,'no_feature_extraction':True,'no_model_training':True}
    after=development_hashes(); protection={'result':'PASS' if before==after else 'FAIL','before_count':len(before),'after_count':len(after),'changed':[k for k in before.keys()|after.keys() if before.get(k)!=after.get(k)],'scope':'explicit application/V1/V2 source and development paths; prohibited old V2 holdout files excluded'}
    reports={'generation':{'dataset':'mobile_money_aml_synthetic_100k_v3','seed':SEED,'elapsed_seconds':time.perf_counter()-start,'rows':100000,'partitions':runs[0][1]},'audit':final,'reproducibility':reproducibility,'protection':protection,'certificate':certificate}
    # A completed run may be resumed after a report-writing interruption.
    # Remove only the five run-owned machine reports before their exclusive
    # writes; generated data and design files remain immutable.
    report_paths=[ROOT/'reports'/name for name in ('V3_STAGE9_GENERATION.json','V3_STAGE9_STRUCTURAL_AUDIT.json','V3_STAGE9_REPRODUCIBILITY.json','V3_STAGE9_HOLDOUT_SEAL.json','V3_STAGE9_PROTECTION.json')]
    for report_path in report_paths:
        if report_path.exists(): report_path.unlink()
    write_json(ROOT/'reports/V3_STAGE9_GENERATION.json',reports['generation']); write_json(ROOT/'reports/V3_STAGE9_STRUCTURAL_AUDIT.json',final); write_json(ROOT/'reports/V3_STAGE9_REPRODUCIBILITY.json',reproducibility); write_json(ROOT/'reports/V3_STAGE9_HOLDOUT_SEAL.json',certificate); write_json(ROOT/'reports/V3_STAGE9_PROTECTION.json',protection)
    if protection['result']!='PASS': raise RuntimeError('protected paths changed')
    print(json.dumps({'result':'PASS','elapsed_seconds':reports['generation']['elapsed_seconds'],'protection':protection},indent=2))
if __name__=='__main__': main()
