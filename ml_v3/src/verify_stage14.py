"""Verify saved diagnostics without fitting or accessing evaluation data."""
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'): os.environ.setdefault(k,'2')
import io,unittest
import numpy as np
import joblib
from threadpoolctl import threadpool_limits
from run_stage11 import load_matrices,metrics
from stage14_growth_diagnosis import *

def main():
    plan=read(14,'plan'); assert sha(R/'stage14_plan.json')==(R/'stage14_plan.sha256').read_text().strip()
    for n,h in plan['source_hashes'].items(): assert sha(ROOT/'src'/n)==h,n
    for n,h in read(14,'artifact_manifest').items(): assert sha(ROOT/n)==h,n
    for n,h in read(14,'generator_audit')['source_hashes'].items(): assert sha(ROOT.parent/n)==h,n
    data=load_matrices(); meta={p:metadata(p,ids,y) for p,(x,y,ids) in data.items()}
    records=read(14,'family_removal'); assert set(records)=={'D1','D2','D3','D4'}
    log=read(14,'fit_log'); assert len(log)==5 and {v['name'] for v in log}=={'D1','D2','D3','D4','shuffle'}
    assert all(plan['saved_at_utc']<v['started_at_utc'] for v in log)
    count=0; reloads={}
    for name,record in records.items():
        saved=np.load(M/f'{name}_scores.npz'); bundle=joblib.load(M/f'{name}.joblib')
        assert list(bundle['feature_names'])==list(NAMES)
        expected_exclude=meta['train']['domain']['agent'] if name=='D4' else meta['train']['family'][{'D1':'A1','D2':'A2','D3':'A4'}[name]]
        assert np.array_equal(saved['fit_mask'],~expected_exclude)
        assert record['excluded_count']==int(expected_exclude.sum())
        for part,(x,y,ids) in data.items():
            assert metrics(y,saved[part])==record[part]; count+=1
            with threadpool_limits(limits=2): p=bundle['model'].predict_proba(x)[:,1]
            diff=float(np.max(abs(p-saved[part]))); assert diff<=1e-12 and np.array_equal(p>=.5,saved[part]>=.5)
            reloads[name+'_'+part]=diff
        y=data['train'][1]; assert metrics(y[saved['fit_mask']],saved['train'][saved['fit_mask']])==record['fit_subset_metrics']; count+=1
        pred=saved['validation']>=.5
        for dest,src in [('families','family'),('domains','domain'),('domain_independence','exclusive'),('normal_fpr','normal')]:
            for k,mask in meta['validation'][src].items():
                got=record[dest][k]; positive=int(pred[mask].sum()); assert got['support']==int(mask.sum())
                assert got['fp' if src=='normal' else 'tp']==positive
                assert got['tn' if src=='normal' else 'fn']==int(mask.sum())-positive
        assert sum(v['fp'] for v in record['normal_fpr'].values())==record['validation']['confusion_matrix'][0][1]
    distributions=read(14,'growth_distributions'); interactions=read(14,'interactions'); comparisons=read(14,'agent_feature_comparison')
    for part,(x,y,ids) in data.items():
        z=np.load(E/f'{part}_agent_primitives.npz'); assert list(z['row_ids'])==ids and list(z['columns'])==PRIMITIVES
        assert np.array_equal(z['values'][:,0],x[:,22]); assert np.array_equal(z['values'][:,10].astype(bool),meta[part]['family']['A1'])
        for k,mask in slices(y,meta[part]).items(): assert summary(x[mask,22],-1)==distributions[part][k]
        p=np.load(ROOT/'models/stage11_candidates/s11_09_hist_gradient_boosting_scores.npz')[part]
        assert metrics(y,p)==read(14,'reference_reproduction')[part]['metrics']; count+=1
        for i in range(20,29):
            v=comparisons[part][NAMES[i]]; assert power(y,x[:,i])==v['encoded_power']
            mask=np.ones(len(y),bool) if FEATURES[i][7] is None else x[:,i]!=FEATURES[i][7]
            assert power(y[mask],x[mask,i])==v['observed_power']
        m=meta[part]; negatives=m['normal']['H7']|m['normal']['H8']|m['normal']['routine']
        tasks={'overall':(np.ones(len(y),bool),y),'agent_only_vs_relevant_negatives':(m['exclusive']['agent_only']|negatives,m['exclusive']['agent_only'].astype(int))}
        for f in ('A1','A2','A4'): tasks[f+'_vs_relevant_negatives']=(m['family'][f]|negatives,m['family'][f].astype(int))
        top=np.load(ROOT/'models/stage12_diagnostics/top_1_scores.npz')[part]
        for name,(mask,target) in tasks.items():
            for view,v in [('encoded',mask),('available',mask&(x[:,22]!=-1)),('agent_present',mask&(z['values'][:,1]>=0))]:
                saved=read(14,'univariate_power')[part][name][view]
                assert power(target[v],x[v,22])==saved['raw_growth']
                assert metrics(target[v],top[v])==saved['saved_top1_classifier']; count+=1
        no_growth=np.load(ROOT/'models/stage12_diagnostics/ablation_B_scores.npz')[part]>=.5
        lost=(y==1)&(p>=.5)&~no_growth; gained=(y==1)&(p<.5)&no_growth
        fd=read(14,'family_dependence')[part]['overall']
        assert fd['lost']==int(lost.sum()) and fd['gained']==int(gained.sum())
        assert fd['lost_in_A1']==int((lost&m['family']['A1']).sum())
        assert fd['gained_in_A1']==int((gained&m['family']['A1']).sum())
        mismatch=z['values'][:,10]!=z['values'][:,11]
        assert np.all((z['values'][mismatch,1]>=28)&(z['values'][mismatch,1]<35))
        for n,v in interactions[part].items():
            i=NAMES.index(n); a=grid_codes(x[:,22],v['growth_edges'],-1); b=grid_codes(x[:,i],v['other_edges'],FEATURES[i][7])
            assert sum(row['support'] for row in v['rows'])==len(y)
            for row in v['rows']:
                mask=(a==row['growth_bin'])&(b==row['other_bin']); assert row['support']==int(mask.sum()) and row['positive']==int(y[mask].sum())
                if mask.any(): assert abs(row['reference_mean_score']-float(p[mask].mean()))<1e-14
    s=np.load(M/'shuffle_scores.npz'); yt=data['train'][1]; expected=np.random.default_rng(SEED).permutation(yt)
    assert np.array_equal(expected,s['shuffled_labels']); order=np.random.default_rng(SEED+1).permutation(len(yt))
    assert np.array_equal(s['fit_indices'],order[:48000]) and np.array_equal(s['test_indices'],order[48000:])
    model=joblib.load(M/'shuffle.joblib')['model']; record=read(14,'shuffle_test')
    for label,idx,score in [('fit','fit_indices','fit_scores'),('reserved_train_test','test_indices','test_scores')]:
        assert metrics(expected[s[idx]],s[score])==record[label]; count+=1
        with threadpool_limits(limits=2): replay=model.predict_proba(data['train'][0][s[idx]])[:,1]
        assert np.array_equal(replay,s[score])
    stream=io.StringIO(); suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_stage14_diagnosis.py')
    tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite); assert tests.wasSuccessful(),stream.getvalue()
    protection=compare(read(14,'protection_before'),snapshot()); assert protection['result']=='PASS'; save('protection',protection)
    required=['feature_contract','growth_distributions','family_dependence','negative_overlap','univariate_power','agent_feature_comparison','interactions','eligibility_analysis','generator_audit','proxy_risk','shuffle_test','family_removal','model_family_comparison','decision','protection']
    for n in required: read(14,n)
    save('final_verification',{'result':'PASS','new_fit_count':5,'family_removal_fits':4,'shuffle_fits':1,'recomputed_metric_sets':count,
        'recomputed_checks':['family/domain/normal slice counts','growth statistics including P99','all interaction supports/target counts/reference means','all agent univariate raw scores','shuffle permutation and split','saved primitives agree with official growth and frozen A1'],
        'model_reloads':reloads,'shuffle_reload_exact':True,'protected_files':len(protection['after']['files']),'changed_paths':protection['changed'],
        'artifact_hash_count':len(read(14,'artifact_manifest')),'plan_hash':sha(R/'stage14_plan.json'),
        'tests':{'methods':tests.testsRun,'failures':len(tests.failures),'errors':len(tests.errors),'log':stream.getvalue()},
        'evidence_hashes':{n:sha(R/f'stage14_{n}.json') for n in required},
        'source_hashes':{p.name:sha(p) for p in (ROOT/'src').glob('*stage14*.py')},'test_source_hash':sha(ROOT/'tests/test_stage14_diagnosis.py'),
        'limits':'No fit repeated during verification. Permutation importance not repeated; its recorded configuration and source are hashed. A1 primitive reconstruction is independent of the target materializer, but not a full audit of all predicates.'})
    print('PASS: five diagnostic reloads, metrics, descriptive counts, shuffle, source/artifact/protection hashes and three tests.')

if __name__=='__main__': main()
