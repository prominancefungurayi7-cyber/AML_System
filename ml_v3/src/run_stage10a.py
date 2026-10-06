"""Freeze, test, independently serialize twice, audit and publish development only."""
import csv
import io
import json
import shutil
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

from contracts import load_development
from stage10a_contract import NAMES, VERSION, render_contract
from stage10a_pipeline import extract
from stage10a_audit import matrix_audit, oracle_audit, source_audit
from stage10a_protection import ROOT, PUBLIC, sha, snapshot, compare

REPORTS = ROOT/'reports'
EXPECTED = {'train': {0:39781,1:20219}, 'validation': {0:9945,1:5055}}
OUTPUT = ROOT/'features/development/stage10a'

def now(): return datetime.now(timezone.utc).isoformat()

def save(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,indent=2,sort_keys=True,allow_nan=False); f.write('\n')

def write_set(folder,data):
    folder.mkdir(parents=True)
    for name,header,rows in (
        ('X.csv',NAMES,data['X']),
        ('y.csv',['decision_point_target'],([v] for v in data['y'])),
        ('row_ids.csv',['transaction_id'],([v] for v in data['row_ids']))):
        with (folder/name).open('x',encoding='utf-8',newline='') as f:
            w=csv.writer(f,lineterminator='\n'); w.writerow(header); w.writerows(rows)
    save(folder/'feature_names.json',list(NAMES))
    return {name:sha(folder/name) for name in ('X.csv','y.csv','row_ids.csv','feature_names.json')}

def read_set(folder):
    def table(name):
        with (folder/name).open(encoding='utf-8',newline='') as f:
            reader=csv.reader(f); header=next(reader); return header,list(reader)
    names,x=table('X.csv'); yh,y=table('y.csv'); ih,ids=table('row_ids.csv')
    assert names==list(NAMES)==json.loads((folder/'feature_names.json').read_text())
    assert yh==['decision_point_target'] and ih==['transaction_id']
    return {'X':[[float(v) for v in r] for r in x], 'y':[int(r[0]) for r in y], 'row_ids':[r[0] for r in ids]}

def verify_development_inputs():
    manifest=json.loads((ROOT/'data/manifests/development_manifest.json').read_text())
    expected=manifest['file_hashes']
    assert len(expected)==14
    for name,digest in expected.items():
        assert name.startswith(('development/train/','development/validation/'))
        assert '..' not in Path(name).parts
        assert sha(ROOT/'data'/name)==digest,name
    return dict(expected)

class RecordedResult(unittest.TextTestResult):
    def startTest(self,test):
        self.test_names.append(test.id()); super().startTest(test)

def run_tests():
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_stage10a_features.py')
    log=io.StringIO()
    RecordedResult.test_names=[]
    result=unittest.TextTestRunner(stream=log,verbosity=2,resultclass=RecordedResult).run(suite)
    record={'result':'PASS' if result.wasSuccessful() else 'FAIL','tests_run':result.testsRun,
            'test_names':result.test_names,'failures':[(str(t),s) for t,s in result.failures],
            'errors':[(str(t),s) for t,s in result.errors],'log':log.getvalue(),
            'scope':'Synthetic exact hand cases; domains, path order, equal timestamps, funding expiry, disjoint baseline/count minima, future/current perturbation, metadata mutation, partition isolation and deterministic ordering.'}
    save(REPORTS/'stage10a_temporal_tests.json',record)
    assert result.wasSuccessful(),log.getvalue()
    return record

def freeze():
    path=REPORTS/'V3_STAGE10A_FEATURE_CONTRACT.md'
    with path.open('x',encoding='utf-8',newline='\n') as f: f.write(render_contract())
    names=['src/stage10a_contract.py','src/stage10a_pipeline.py','src/stage10a_audit.py',
           'src/stage10a_protection.py','src/run_stage10a.py','tests/test_stage10a_features.py',
           'design/V3_SCENARIO_ONSET_CONTRACT.md','design/V3_FEATURE_ARCHITECTURE_PROPOSAL.md',
           'reports/V3_STAGE10A_FEATURE_CONTRACT.md']
    manifest={'version':VERSION,'frozen_at_utc':now(),'original_count':32,'corrected_count':len(NAMES),
              'feature_order':list(NAMES),'hashes':{n:sha(ROOT/n) for n in names},
              'original_stage10_contract_hash_observed_now':sha(REPORTS/'V3_STAGE10_FEATURE_CONTRACT.md'),
              'historical_hash_caveat':'The original hash is observed during Stage 10A, not claimed as a historical pre-extraction commitment.',
              'reason':'Semantic repairs A-J and assisted-W2W subject correction, documented in the corrected contract; no outcome-driven selection.'}
    save(REPORTS/'stage10a_contract_manifest.json',manifest)
    return manifest

def main():
    started=time.monotonic()
    assert not OUTPUT.exists(),'Corrected output already exists; refuse to replace audit artifacts.'
    before=json.loads((REPORTS/'stage10a_protection_before.json').read_text())
    assert compare(before,snapshot())['result']=='PASS','Protected inputs changed since task start.'
    inputs=verify_development_inputs()
    public=[json.loads((ROOT.parent/p).read_text()) for p in PUBLIC]
    assert public[0]['private_manifest_commitment']==public[1]['private_manifest_commitment']
    tests=run_tests()
    manifest=freeze()
    print('Contract frozen; hand tests passed:',tests['tests_run'],flush=True)
    source=source_audit(ROOT/'src/stage10a_pipeline.py')
    stats={}; oracle={'source_review':source,'partitions':{}}
    repro={'version':VERSION,'contract_manifest_sha256':sha(REPORTS/'stage10a_contract_manifest.json'),
           'contract_frozen_at_utc':manifest['frozen_at_utc'],'runs':{},'partitions':{},'input_hashes':inputs}
    (ROOT/'tmp').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='stage10a_',dir=ROOT/'tmp') as scratch:
        scratch=Path(scratch)
        for run in ('run_a','run_b'):
            repro['runs'][run]={'started_at_utc':now(),'partitions':{}}
            assert repro['runs'][run]['started_at_utc']>manifest['frozen_at_utc']
            for part,expected in EXPECTED.items():
                tick=time.monotonic()
                transactions=load_development(ROOT/'data',part,'transactions')
                truth=load_development(ROOT/'data',part,'ground_truth')
                targets={str(int(r['transaction_id'])):int(r['decision_point_target']) for r in truth}
                assert len(targets)==len(truth)==sum(expected.values())
                ids,x=extract(transactions)
                assert set(ids)==set(targets)
                data={'row_ids':ids,'X':x,'y':[targets[i] for i in ids]}
                hashes=write_set(scratch/run/part,data)
                disk=read_set(scratch/run/part)
                assert disk==data,'Serialized round-trip differs.'
                repro['runs'][run]['partitions'][part]={'hashes':hashes,'seconds':time.monotonic()-tick,
                    'round_trip_equal':True,'targets_equal_frozen_ground_truth_by_id':True,
                    'ground_truth_file_sha256':inputs[f'development/{part}/ground_truth_v3.csv']}
                if run=='run_a':
                    stats[part]=matrix_audit(data,expected)
                    # Private evidence is read solely AFTER extraction for this
                    # audit. The extractor receives observable transactions only.
                    evidence={str(int(r['transaction_id'])):set(r['evidence_families'].split(';')) for r in truth}
                    families=[prefix+str(i) for prefix in ('S','N','A') for i in range(1,5)]
                    family_truth={f:[int(f in evidence[i]) for i in ids] for f in families}
                    oracle['partitions'][part]=oracle_audit(data,family_truth)
                else:
                    previous=read_set(scratch/'run_a'/part)
                    assert previous==disk
                    assert hashes==repro['runs']['run_a']['partitions'][part]['hashes']
                    repro['partitions'][part]={'row_order_equal':True,'feature_order_equal':True,
                        'numeric_values_equal':True,'targets_equal':True,'row_ids_equal':True,'all_file_hashes_equal':True}
                print(run,part,'serialized and checked',round(time.monotonic()-tick,2),'seconds',flush=True)
                del transactions,truth,targets,ids,x,data,disk
        assert all(v['result']=='PASS' for v in oracle['partitions'].values()),'Direct encoding audit failed.'
        assert inputs==verify_development_inputs()
        for name,digest in manifest['hashes'].items(): assert sha(ROOT/name)==digest,name
        protection=compare(before,snapshot())
        assert protection['result']=='PASS' and protection['public_commitment_unchanged']
        protection['frozen_development_manifest_comparison']='PASS (14 explicit files)'
        protection['public_certificate_agreement']=True
        protection['evaluation_access']='No evaluation directory enumerated or evaluation data byte opened by this runner. Only named public commitment certificates were read.'
        OUTPUT.mkdir()
        for part in EXPECTED:
            shutil.copytree(scratch/'run_a'/part,OUTPUT/part)
            assert read_set(OUTPUT/part)==read_set(scratch/'run_a'/part)
            assert {n:sha(OUTPUT/part/n) for n in repro['runs']['run_a']['partitions'][part]['hashes']}==repro['runs']['run_a']['partitions'][part]['hashes']
        save(OUTPUT/'version.json',{'version':VERSION,'contract_sha256':manifest['hashes']['reports/V3_STAGE10A_FEATURE_CONTRACT.md'],
                                 'status':'Stage 10A audited development matrices; model training not performed or authorized here.'})
    shift={}
    for name in NAMES:
        a=stats['train']['statistics'][name]; b=stats['validation']['statistics'][name]
        av,bv=a['observed_values'],b['observed_values']
        shift[name]={'train_observed_mean':av.get('mean'),'validation_observed_mean':bv.get('mean'),
                     'observed_mean_difference':bv['mean']-av['mean'] if av['count'] and bv['count'] else None,
                     'train_missing_fraction':a['missing_fraction'],'validation_missing_fraction':b['missing_fraction'],
                     'missing_fraction_difference':b['missing_fraction']-a['missing_fraction'],
                     'train_zero_fraction':a['all_values']['zero_fraction'],'validation_zero_fraction':b['all_values']['zero_fraction'],
                     'zero_fraction_difference':b['all_values']['zero_fraction']-a['all_values']['zero_fraction']}
    # Snapshot after publication too: protected originals must remain identical.
    protection_after=compare(before,snapshot())
    assert protection_after['result']=='PASS'
    protection['after']=protection_after['after']
    repro.update(result='PASS',finished_at_utc=now(),runtime_seconds=time.monotonic()-started,
                 corrected_contract_unchanged=True,published_directory='features/development/stage10a')
    oracle['result']='PASS'
    for name,obj in [('feature_statistics',stats),('shift_audit',shift),('oracle_leakage',oracle),
                     ('reproducibility',repro),('protection',protection)]:
        save(REPORTS/f'stage10a_{name}.json',obj)
    print('STAGE 10A machine audits PASS. Consolidated report pending.',flush=True)

if __name__=='__main__': main()
