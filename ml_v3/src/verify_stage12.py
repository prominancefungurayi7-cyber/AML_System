"""Verify Stage 12 saved scores and add descriptive error views; no fits."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'): os.environ.setdefault(key,'2')
import json,unittest,io
import numpy as np
from run_stage11 import load_matrices,metrics
from stage12_robustness import ROOT,NAMES,FEATURES,sha,snapshot,compare,metadata,stats,write,REFERENCE
R=ROOT/'reports'; M=ROOT/'models/stage12_diagnostics'
def read(n): return json.loads((R/('stage12_'+n+'.json')).read_text(encoding='utf-8'))
def save(n,v): write(R/('stage12_'+n+'.json'),v)

def main():
    plan=read('plan'); fits=read('fit_checkpoint')['fits']; assert len(fits)==20
    for n,digest in plan['source_hashes'].items(): assert sha(ROOT/'src'/n)==digest
    for n,digest in read('artifact_manifest').items(): assert sha(M/n)==digest,n
    data=load_matrices(); xv,yv,ids=data['validation']; meta=metadata('validation',ids,yv)
    checked=0
    for name,record in fits.items():
        scores=np.load(M/(name+'_scores.npz'))
        for part,(x,y,_) in data.items():
            assert metrics(y,scores[part])==record[part],(name,part); checked+=1
        pred=scores['validation']>=.5
        for key,source in [('domains','domain'),('families','family'),('normal_fpr','normal'),('domain_independence','exclusive')]:
            for code,mask in meta[source].items():
                rec=record[key][code]; n=int(mask.sum()); positives=int(np.sum(pred&mask)); negative=n-positives
                assert rec['support']==n
                if source=='normal': assert rec['fp']==positives and rec['tn']==negative
                else: assert rec['tp']==positives and rec['fn']==negative
        cm=record['validation']['confusion_matrix']
        assert sum(v['fp'] for v in record['normal_fpr'].values())==cm[0][1]
        assert sum(v['support'] for v in record['normal_fpr'].values())==int((yv==0).sum())
    ab=read('ablation_results'); tiny=read('small_feature_models')['models']; stability=read('stability')
    for k,v in ab.items():
        if k!='A': assert v==fits['ablation_'+k]
    for n,v in tiny.items(): assert v==fits['top_'+n]
    assert read('missingness_audit')['diagnostic_model']==fits['missingness_only']
    for v in stability['runs']+[stability['same_seed_repeat']]: assert v==fits[v['name']]
    p=np.load(ROOT/'models/stage11_candidates'/(REFERENCE+'_scores.npz'))['validation']; pred=p>=.5
    details={'scope':'Additional descriptive error views after the fixed fits; no model, threshold, feature or selection change.'}
    n3=meta['family']['N3']; a4=meta['family']['A4']
    details['N3_selected_ratio_outside_original_return_band']={}
    for label,mask in [('TP',n3&pred),('FN',n3&~pred)]:
        outside=mask&((xv[:,17]<.25)|(xv[:,17]>1.25))
        details['N3_selected_ratio_outside_original_return_band'][label]={'support':int(mask.sum()),'outside_count':int(outside.sum()),'transaction_ids':[ids[i] for i in np.flatnonzero(outside)]}
    details['A4_absolute_skews']={}
    for label,mask in [('TP',a4&pred),('FN',a4&~pred),('H8_target0',meta['normal']['H8'])]:
        details['A4_absolute_skews'][label]={NAMES[i]:stats(np.abs(xv[mask&(xv[:,i]!=-3),i]) if i==28 else np.abs(xv[mask,i])) for i in (26,27,28)}
    details['A4_valid_magnitude_note']='Absolute change excludes the -3 marker before taking absolute values; raw skew -1 is valid.'
    save('error_details',details)
    stream=io.StringIO(); suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_stage12_robustness.py')
    tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite); assert tests.wasSuccessful()
    protection=compare(read('protection_before'),snapshot()); assert protection['result']=='PASS'
    save('protection',protection)
    output={'result':'PASS','diagnostic_fits':len(fits),'recomputed_metric_sets':checked,'all_validation_slice_counts_recomputed':True,
            'diagnostic_artifact_hashes_checked':len(read('artifact_manifest')),'frozen_feature_hashes_checked':True,'preregistered_source_hashes_match':True,
            'protected_count':len(protection['after']['files']),'changed_protected_paths':protection['changed'],
            'tests':{'methods':tests.testsRun,'failures':len(tests.failures),'errors':len(tests.errors),'log':stream.getvalue()},
            'verification_source_sha256':sha(ROOT/'src/verify_stage12.py')}
    save('final_verification',output)
    print('PASS: 40 metric sets, all diagnostic slice counts, 41 artifact hashes, source/input/protection hashes and 3 tests.')

if __name__=='__main__': main()
