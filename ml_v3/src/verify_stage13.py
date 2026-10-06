"""Independent saved-artifact verification; no fitting or feature regeneration."""
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'): os.environ.setdefault(k,'2')
import io,json,unittest
import numpy as np
import joblib
from threadpoolctl import threadpool_limits
from run_stage11 import load_matrices,metrics
from stage12_robustness import metadata
from stage13_robustness_improvement import ROOT,sha,compare,snapshot,write,NEW_NAMES
from run_stage13 import representations,selection
R=ROOT/'reports'; M=ROOT/'models/stage13_candidates'; E=ROOT/'evidence/stage13'
def read(n): return json.loads((R/('stage13_'+n+'.json')).read_text(encoding='utf-8'))

def main():
    plan=read('plan'); assert sha(R/'stage13_plan.json')==(R/'stage13_plan.sha256').read_text().strip()
    for n,h in plan['source_hashes'].items(): assert sha(ROOT/'src'/n)==h,n
    assert sha(ROOT/'tests/test_stage13_features.py')==plan['test_source_sha256']
    results=read('candidate_results'); assert results['status']=='complete' and results['new_fit_count']==plan['new_fit_count']==15
    records=results['candidates']; assert len(records)==18
    assert plan['saved_at_utc']<min(v['started_at_utc'] for v in records.values() if not v['reuse'])
    manifest=read('artifact_manifest')
    for p,h in manifest.items(): assert sha(ROOT/p)==h,p
    data=load_matrices(); mats={}
    for part,(x,y,ids) in data.items():
        f=np.load(E/(part+'_candidate_features.npz')); assert list(f['row_ids'])==ids and list(f['feature_names'])==NEW_NAMES
        assert f['X'].shape==(len(y),6) and np.isfinite(f['X']).all()
        mats[part]=np.column_stack((x,f['X'])); assert np.array_equal(mats[part][:,:32],x)
    meta=metadata('validation',data['validation'][2],data['validation'][1]); max_diffs={}; count=0
    for name,rec in records.items():
        saved=np.load(M/(name+'_scores.npz'))
        for part,(_,y,ids) in data.items(): assert metrics(y,saved[part])==rec[part]; count+=1
        pred=saved['validation']>=.5
        for dest,source in [('domains','domain'),('families','family'),('normal_fpr','normal'),('domain_independence','exclusive')]:
            for label,mask in meta[source].items():
                n=int(mask.sum()); tp=int(np.sum(pred&mask)); v=rec[dest][label]
                assert v['support']==n and v['fp' if source=='normal' else 'tp']==tp and v['tn' if source=='normal' else 'fn']==n-tp
        multi=sum(v.astype(int) for v in meta['domain'].values())>1
        assert rec['domain_independence']['multi_domain']['tp']==int(np.sum(pred&multi))
        assert sum(v['fp'] for v in rec['normal_fpr'].values())==rec['validation']['confusion_matrix'][0][1]
        if not rec['reuse']:
            bundle=joblib.load(M/(name+'.joblib')); assert bundle['columns']==rec['columns']; cols=representations()[rec['representation']]
            with threadpool_limits(limits=2): replay=bundle['model'].predict_proba(mats['validation'][:,cols])[:,1]
            delta=float(np.max(np.abs(replay-saved['validation']))); assert delta<=1e-12 and np.array_equal(replay>=.5,pred)
            max_diffs[name]=delta
    deps=read('growth_dependence'); imps=read('feature_concentration')
    assert read('selection_decision')==selection(records,deps,imps,records['hgb_R0'])
    stream=io.StringIO(); suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_stage13_features.py')
    test=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite); assert test.wasSuccessful()
    protection=compare(read('protection_before'),snapshot()); assert protection['result']=='PASS'
    write(R/'stage13_protection.json',protection)
    write(R/'stage13_final_verification.json',{'result':'PASS','new_fits':15,'total_records_including_reused':18,'recomputed_metric_sets':count,
          'all_slice_counts_recomputed':True,'new_model_reload_max_differences':max_diffs,'artifact_hash_count':len(manifest),
          'plan_hash_and_frozen_source_hashes_match':True,'official_feature_hashes_and_values_unchanged':True,'selection_recomputed':True,
          'tests':{'methods':test.testsRun,'failures':len(test.failures),'errors':len(test.errors),'log':stream.getvalue()},
          'protected_files':len(protection['after']['files']),'protected_changes':protection['changed'],'verification_source_sha256':sha(ROOT/'src/verify_stage13.py')})
    print('PASS: saved metrics, slices, model reloads, plan/artifact/protected hashes, selection and feature tests.')

if __name__=='__main__': main()
