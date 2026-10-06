"""Finalize existing completed extraction evidence after report-only typo repair."""
from pathlib import Path
import ast
import hashlib
import json
import platform
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'ml_v4/evidence/stage21'
REPORT=ROOT/'ml_v4/reports/V4_STAGE21_FEATURE_IMPLEMENTATION_REPORT.md'

def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,data):
    with (OUT/name).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(data,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')

def main():
    if REPORT.exists() or (OUT/'stage21_decision.json').exists():raise FileExistsError('No overwrite')
    protected=read('preservation_before.json')['sha256']
    for name,h in protected.items():
        if '/evaluation/' in name:raise PermissionError(name)
        assert sha(ROOT/name)==h,name
    runner=ROOT/'ml_v4/development_features_v2/run_stage21.py'
    old=(OUT/'run_stage21_attempt1.py.txt').read_bytes()
    assert runner.read_bytes()==old.replace(b'np.__version__()',b'np.__version__')
    runtime=read('runtime_resources.json')
    for name,h in runtime['runtime_source_sha256'].items():
        assert sha(OUT/'run_stage21_attempt1.py.txt')==h if name.endswith('run_stage21.py') else sha(ROOT/name)==h
    replay=read('deterministic_replay.json')
    for part,n in [('train',60000),('validation',15000)]:
        folder=ROOT/'ml_v4/development_features_v2/matrices'/part
        original=ROOT/'ml_v4/development_features/matrices'/part
        x=np.load(folder/'X.npy',allow_pickle=False)
        a=np.load(original/'X.npy',allow_pickle=False)
        assert x.shape==a.shape==(n,) and len(x.dtype.names)==44
        assert x.dtype.names[:40]==a.dtype.names
        for name in a.dtype.names:
            assert x.dtype.fields[name][0]==a.dtype.fields[name][0]
            assert x[name].tobytes()==a[name].tobytes(),(part,name)
        assert sha(folder/'X.npy')==replay[part]['serialized_X_sha256']==replay[part]['replay_X_sha256']
        for name in ['y.npy','row_metadata.csv']:assert sha(folder/name)==sha(original/name)
    tests=read('independent_hand_fixtures.json')
    assert tests['exit_code']==0 and '69 passed' in tests['stdout']
    # Evaluate only the report's local f-string expression, not main() or any
    # extractor/import from the runner. Its inputs are saved resource evidence.
    tree=ast.parse(runner.read_text(encoding='utf-8'))
    expression=next(n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='report' for t in n.targets))
    report=eval(compile(ast.Expression(expression),str(runner),'eval'),{'__builtins__':{'len':len}}, {'VERSION':'v4.features.2.experimental.stage21.1','resources':runtime['partitions'],'platform':platform,'np':np,'protected':protected})
    note='''## Reporting-only correction

Both extractions, both serialized replays, all parity/alignment/quality checks and preservation completed successfully before the first runner stopped while formatting the report: it called the NumPy version string as a function. The original executed runner is retained in `run_stage21_attempt1.py.txt`; the corrected runner differs only by removing those call parentheses. No extractor, fixture, data, matrix or existing evidence was changed. Source-freeze hashes in execution evidence refer to the retained executed revision. A separate finalizer rechecked saved matrices, replay hashes, original40 bytes, labels and all protected hashes, then wrote this report without re-extraction or fitting. See [correction record](../evidence/stage21/report_completion_correction.json).

'''
    report=report.replace('## 8. Preservation and decision',note+'## 8. Preservation and decision')
    with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(report)
    save('report_completion_correction.json',{'initial_attempt':'Extraction and all audits completed; report construction failed before writing report/decision','error':"TypeError: 'str' object is not callable at np.__version__() in report formatting",'archived_executed_runner':'ml_v4/evidence/stage21/run_stage21_attempt1.py.txt','archived_sha256':sha(OUT/'run_stage21_attempt1.py.txt'),'corrected_runner_sha256':sha(runner),'only_change':'np.__version__() -> np.__version__ in report text','extractor_changed':False,'fixtures_changed':False,'matrices_changed':False,'reextraction':False,'fits':0,'final_verification':'69 tests recorded; all75000 first40 columns, saved replay X hashes, exact y/metadata and261 protected paths rechecked'})
    save('final_verification.json',{'status':'PASS','protected_count':len(protected),'changed_paths':[],'matrix_parity_rechecked_rows':75000,'serialized_replay_hashes_rechecked':True,'schema_fields':44,'expected_encoded_fields':46,'tests_passed':69,'new_fits':0,'report_only_correction_recorded':True})
    artifacts=[REPORT]+[ROOT/'ml_v4/development_features_v2'/n for n in ['extractor_v2.py','run_stage21.py','finalize_stage21.py','tests/test_stage21.py']]+list(OUT.iterdir())+[p for part in ['train','validation'] for p in (ROOT/'ml_v4/development_features_v2/matrices'/part).iterdir()]
    hashes={p.relative_to(ROOT).as_posix():sha(p) for p in artifacts if p.is_file()}
    save('stage21_decision.json',{'decision':'A — EXPERIMENTAL 44-FEATURE MATRICES COMPLETE AND VERIFIED','feature_version':'v4.features.2.experimental.stage21.1','semantic_fields':44,'numeric_columns_if_encoded':46,'training_authorized':False,'new_fits':0,'selected_preserved':'primary_XGB','comparator_preserved':'primary_HGB','sealed_access':False,'independent_readiness':False,'original40_parity':'PASS_ALL75000_ROWS','byte_replay':'PASS','protected_count':len(protected),'artifact_sha256':hashes,'report_completion_correction':'report_completion_correction.json','restrictions':'No automatic Stage22, model fit, threshold tune, schema promotion, independent evaluation or integration'})
    print(f'Stage21 finalized: {len(protected)} protected hashes; {len(hashes)} output hashes;75000 rows exact40 parity.')

if __name__=='__main__':main()
