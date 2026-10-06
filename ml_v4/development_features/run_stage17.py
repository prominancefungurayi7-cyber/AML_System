"""One-time development extraction and audit. Never opens evaluation inputs."""
from pathlib import Path
import ast
import csv
import ctypes
import hashlib
import io
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
import numpy as np
from extractor import Extractor, NAMES, ROOT, SPEC
from stage16r_loader import development_path
from stage16r_contract import read_events

EVIDENCE=ROOT/'ml_v4/evidence/stage17'
MATRICES=ROOT/'ml_v4/development_features/matrices'
DTYPE=np.dtype([(name,'U16' if i==1 else '<f8') for i,name in enumerate(NAMES)])

def sha(path):
    with path.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def read(path): return json.loads((ROOT/path).read_text(encoding='utf-8'))

def write(name,data):
    with (EVIDENCE/name).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(data,f,indent=2,sort_keys=True,allow_nan=False); f.write('\n')

def peak_memory():
    class Counters(ctypes.Structure):
        _fields_=[('cb',ctypes.c_ulong),('PageFaultCount',ctypes.c_ulong)]+[(n,ctypes.c_size_t) for n in ['PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage']]
    p=Counters();p.cb=ctypes.sizeof(p)
    kernel=ctypes.WinDLL('kernel32');kernel.GetCurrentProcess.restype=ctypes.c_void_p
    fn=ctypes.WinDLL('psapi').GetProcessMemoryInfo
    fn.argtypes=[ctypes.c_void_p,ctypes.POINTER(Counters),ctypes.c_ulong]
    if not fn(kernel.GetCurrentProcess(),ctypes.byref(p),p.cb): raise OSError('Memory measurement failed')
    return p.PeakWorkingSetSize

def extract(warmup,scored):
    state=Extractor()
    for e in warmup: state.step(e)
    x=np.empty(len(scored),dtype=DTYPE)
    for i,e in enumerate(scored): x[i]=state.step(e)
    return x

def protection():
    expected=dict(read('ml_v4/evidence/stage16v/preservation_verification.json')['after'])
    for manifest in ['ml_v4/evidence/stage16v/stage16v_decision.json','ml_v4/evidence/stage16u/stage16u_decision.json']:
        expected.update(read(manifest)['artifact_sha256'])
        expected[manifest]=sha(ROOT/manifest)
    expected.update(read('experimental_v3/manifest.json')['sha256'])
    v1='ml/stage14/stage14_frozen_model.pkl'
    expected[v1]=read('ml_v4/design/amendments/v4_stage15a_manifest.json')['protection']['before'][v1]
    # Preserve every file in these explicitly public evidence directories.
    for stage in ['stage16r','stage16s','stage16t','stage16u','stage16v']:
        folder=ROOT/'ml_v4/evidence'/stage
        if folder.is_dir():
            for p in folder.iterdir():
                if p.is_file(): expected[p.relative_to(ROOT).as_posix()]=sha(p)
    for p in [ROOT/'ai_stage14_model.py',ROOT/'ai_stage13_features.py',ROOT/'templates/experimental_v3.html',ROOT/'experimental_v3/feature_schema.json',ROOT/'experimental_v3/manifest.json']:
        expected[p.relative_to(ROOT).as_posix()]=sha(p)
    manifest=read('ml_v4/evidence/stage16r/dataset_manifest.json')
    expected.update(manifest['design_sha256'])
    for part in ['train','validation']:
        for filename in ['transactions.csv','warmup_observables.csv','ground_truth.csv']:
            path=development_path(part,filename)
            expected[path.relative_to(ROOT).as_posix()]=manifest['development_sha256'][part][filename]
    for name,h in expected.items():
        # Refuse any future manifest change introducing private evaluation paths.
        if '/data/' in name and not name.startswith(('ml_v4/data/development/train/','ml_v4/data/development/validation/')):
            raise PermissionError(name)
        if sha(ROOT/name)!=h: raise ValueError('Frozen input hash mismatch: '+name)
    return expected

def quality(x):
    result={}
    for i,name in enumerate(NAMES):
        a=x[name]
        if i==1:
            cats,counts=np.unique(a,return_counts=True)
            assert set(cats)<= {'wallet_to_wallet','cash_in','cash_out'}
            result[name]={'dtype':str(a.dtype),'counts':dict(zip(cats.tolist(),counts.tolist()))}
            continue
        marker=SPEC['features'][i]['missing_semantics']
        if marker.startswith('-1'): missing=a==-1
        elif marker.startswith('-3'): missing=a==-3
        elif marker.startswith('NaN'): missing=np.isnan(a)
        else: missing=np.zeros(len(a),dtype=bool)
        assert not np.isinf(a).any()
        assert not np.isnan(a).any() or i==23
        v=a[~missing]
        result[name]={'dtype':str(a.dtype),'missing_count':int(missing.sum()),'missing_fraction':float(missing.mean()),
                      'valid_count':len(v),'valid_min':float(v.min()) if len(v) else None,'valid_max':float(v.max()) if len(v) else None,
                      'valid_quantiles':np.quantile(v,[0,.25,.5,.75,1]).tolist() if len(v) else None,
                      'constant_including_marker':len(np.unique(a))==1}
    duplicates=[]
    for i,n in enumerate(NAMES):
        if i==1:continue
        for j,m in enumerate(NAMES[:i]):
            if j!=1 and np.array_equal(x[n],x[m],equal_nan=True):duplicates.append([n,m])
    # Structured NaNs normalized for exact duplicate-row counting only, never in saved X.
    copy=x.copy();copy[NAMES[23]][np.isnan(copy[NAMES[23]])]=-np.inf
    return {'columns':result,'identical_column_pairs':duplicates,'duplicate_feature_rows':len(x)-len(np.unique(copy))}

def main():
    if EVIDENCE.exists() or MATRICES.exists(): raise FileExistsError('Stage17 outputs already exist; no overwrite')
    before=protection()
    EVIDENCE.mkdir(parents=True); MATRICES.mkdir(parents=True)
    write('development_authorization.json',{'scope':'Explicit user Stage17 development-only authorization supersedes earlier feature-work stop for Train/Validation only.',
        'allowed':['frozen implementation','hand fixtures','Train/Validation extraction and diagnostics'],
        'blocked':['training','threshold selection','challenge generation','quarantined evaluation access','Stage18 progression'],
        'custody_decision_unchanged':'Stage16V C; challenge progression blocked',
        'started_utc':datetime.now(timezone.utc).isoformat()})
    test=subprocess.run([sys.executable,'-B','-m','pytest','ml_v4/development_features/tests','-q','-p','no:cacheprovider'],cwd=ROOT,capture_output=True,text=True)
    result={'exit_code':test.returncode,'stdout':test.stdout,'stderr':test.stderr,'independent_expected_values':True,
        'external_independent_audit':False,'method':'Separately hand-calculated fixtures in same developer environment; no evaluator or shared compound rule oracle.',
        'initial_fixture_corrections':['A3/A4 hand baseline date corrected to fall inside baseline','NaN equality assertions made marker-aware; feature definitions unchanged']}
    write('independent_fixture_tests.json',result)
    if test.returncode: raise RuntimeError('Fixture gate failed')
    write('temporal_correctness_tests.json',{'status':'PASS','fixture_evidence':'independent_fixture_tests.json',
        'coverage':['strict prior full keys','1h and 24h open lower bounds','UTC midnight and calendar baseline','35d A1 exact age and 12-service support','graph chronology/1..5 edges','future append invariance','partition reset','incoming coverage and service roles'],
        '30_day_window':'No feature in frozen 40-field schema requires a 30-day window; none invented.'})
    write('feature_schema_audit.json',{'status':'PASS','feature_version':SPEC['feature_version'],'semantic_count':40,
        'ordered_names':NAMES,'numpy_dtype':DTYPE.descr,'definitions':SPEC['features'],'path_selection':SPEC['path_selection'],
        'one_hot':'NOT_APPLIED. Retain categorical transaction_type; no numeric category code or fitted transform. 42-column expansion deferred to explicitly frozen model preprocessing.',
        'rounding':'Exact integer/rational aggregation, float64 after computation; log summary float64. Exact rational path-spread ranking is order-equivalent to max absolute log ratio.'})
    audits={}; qualities={}; identities={}
    for part,n,w in [('train',60000,14400),('validation',15000,3600)]:
        warmup=read_events(development_path(part,'warmup_observables.csv'))
        scored=read_events(development_path(part,'transactions.csv'))
        assert len(scored)==n and len(warmup)==w and warmup[-1].key<scored[0].key
        rows=list(csv.DictReader(io.StringIO(development_path(part,'ground_truth.csv').read_text())))
        assert len(rows)==n and all(set(r)=={'transaction_id','ground_truth_label'} for r in rows)
        ids=[e.transaction_id for e in scored]
        assert ids==[int(r['transaction_id']) for r in rows]
        y=np.array([int(r['ground_truth_label']) for r in rows],dtype=np.uint8)
        assert set(y.tolist())=={0,1}
        started=time.perf_counter();x=extract(warmup,scored);elapsed=time.perf_counter()-started
        print(part+' extraction: '+str(round(elapsed,3))+' seconds',flush=True)
        replay_start=time.perf_counter();replay=extract(warmup,scored)
        replay_seconds=time.perf_counter()-replay_start
        assert all(np.array_equal(x[name],replay[name]) if name=='transaction_type' else np.array_equal(x[name],replay[name],equal_nan=True) for name in NAMES)
        left,right=io.BytesIO(),io.BytesIO();np.save(left,x,allow_pickle=False);np.save(right,replay,allow_pickle=False)
        assert left.getvalue()==right.getvalue()
        path=MATRICES/part;path.mkdir()
        np.save(path/'X.npy',x,allow_pickle=False);np.save(path/'y.npy',y,allow_pickle=False)
        with (path/'row_metadata.csv').open('x',encoding='utf-8',newline='') as f:
            writer=csv.writer(f,lineterminator='\n');writer.writerow(['row_index','transaction_id','event_timestamp'])
            writer.writerows((i,e.transaction_id,e.event_timestamp) for i,e in enumerate(scored))
        qualities[part]=quality(x)
        identities[part]={'wallets':{q for e in warmup+scored for q in (e.sender_wallet,e.receiver_wallet)},
            'agents':{e.agent_id for e in warmup+scored if e.agent_id},'ids':{e.transaction_id for e in warmup+scored}}
        audits[part]={'semantic_dimensions':[n,40],'numpy_storage_shape':list(x.shape),'warmup_rows':w,'label_shape':list(y.shape),
            'label_counts':{'0':int((y==0).sum()),'1':int((y==1).sum())},'original_order_and_label_alignment':'PASS',
            'extraction_seconds':elapsed,'replay_seconds':replay_seconds,'byte_identical_replay':True,'peak_process_working_set_bytes':peak_memory(),
            'artifacts':{p.relative_to(ROOT).as_posix():sha(p) for p in path.iterdir()}}
        del x,replay,warmup,scored
    for key in ['wallets','agents','ids']:assert not identities['train'][key]&identities['validation'][key]
    support=read('ml_v4/evidence/stage16s/development_support_review.json')
    for part in audits:
        audits[part]['family_support']={family:{k:row[k] for k in ['decision_points','minimum_objective','distinct_subjects','distinct_clusters']} for family,row in support['partitions'][part]['families'].items()}
    write('development_matrix_audit.json',{'status':'PASS','partitions':audits,'partition_entity_id_isolation':'PASS','python':platform.python_version(),'numpy':np.__version__,
        'storage':'Structured NPY, 40 named semantic fields; 39 float64 fields and one categorical Unicode field. Not an estimator-ready homogeneous array. No pickle needed.'})
    comparisons={}
    for name in NAMES:
        if name=='transaction_type':continue
        tr=qualities['train']['columns'][name];va=qualities['validation']['columns'][name]
        comparisons[name]={'validation_minus_train_missing_fraction':va['missing_fraction']-tr['missing_fraction'],
            'train_valid_quantiles':tr['valid_quantiles'],'validation_valid_quantiles':va['valid_quantiles']}
    write('feature_quality_audit.json',{'status':'PASS','partitions':qualities,'marker_aware_comparison':comparisons,
        'duplicate_rows_interpretation':'Repeated feature vectors allowed; IDs and original rows retained. No row deduplication or balancing.',
        'support_warning':'Nine family support failures remain; this stage cannot establish model learnability, full-family adequacy or independent evaluation.'})
    source=(ROOT/'ml_v4/development_features/extractor.py').read_text()
    imports=[ast.unparse(n) for n in ast.walk(ast.parse(source)) if isinstance(n,(ast.Import,ast.ImportFrom))]
    assert not any('evaluator' in s or 'generator' in s for s in imports)
    write('leakage_audit.json',{'status':'PASS','extractor_imports':imports,'input_interface':'Exact validated observable Event only',
        'no_truth_or_provenance_in_extractor':True,'y_join':'Runner reads frozen binary labels separately, checks exact IDs/order, never supplies labels to extractor',
        'identifier_columns_in_X':False,'direct_target_components':'Disclosed frozen B/C components retained; no full predicate trigger',
        'development_only_paths':True,'sealed_or_challenge_access':False,'tests':'private-field rejection, access enum rejection, history reset, future/identity invariance',
        'logical_separation_not_external_audit':True})
    after={p:sha(ROOT/p) for p in before}
    assert before==after
    write('preservation_verification.json',{'status':'PASS_WITH_HISTORICAL_SCOPE_LIMIT','before':before,'after':after,'changed_paths':[],
        'historical_gap':'Stage15A broad snapshot remains incomplete; missing archive not restored; old manifests not changed.',
        'sealed_bytes':'Not enumerated, opened or hashed','development_inputs':'Six exact observable/history/label hashes match Stage16R manifest.'})
    print('Stage17 extraction and audits finished; report/decision pending.',flush=True)

if __name__=='__main__':main()
