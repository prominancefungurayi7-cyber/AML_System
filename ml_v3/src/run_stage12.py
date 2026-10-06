"""Preregistered Stage 12 diagnostics. No official feature or model changes."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'): os.environ.setdefault(key,'2')
import json,time,sys,platform,warnings
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import sklearn,joblib
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from threadpoolctl import threadpool_limits
from run_stage11 import load_matrices
from stage12_robustness import *

R=ROOT/'reports'; OLD=ROOT/'models/stage11_candidates'; OUT=ROOT/'models/stage12_diagnostics'
KEYS=('macro_f1','suspicious_precision','suspicious_recall','suspicious_f1','average_precision','roc_auc','false_positive_rate')
def read(name): return json.loads((R/name).read_text(encoding='utf-8'))
def save(name,value): write(R/('stage12_'+name+'.json'),value)
def utc(): return datetime.now(timezone.utc).isoformat()

def novelty(data,metas):
    result={}; decompositions={}
    for part,(x,y,ids) in data.items():
        m=metas[part]
        slices={'overall':np.ones(len(y),bool),'target_0':y==0,'target_1':y==1,
                'A1_positive':m['family']['A1'],'A2_positive':m['family']['A2'],
                'H7_target0':m['normal']['H7'],'H8_target0':m['normal']['H8'],'routine_target0':m['normal']['routine']}
        result[part]={k:stats(x[v,23],-1) for k,v in slices.items()}
    # Exact additive standardization among available observations, with fixed disjoint strata.
    for mode in ('target','origin_scenario_target'):
        tables={}
        for part,(x,y,ids) in data.items():
            rows=metas[part]['rows']; valid=x[:,23]!=-1
            labels=[str(int(t)) if mode=='target' else '|'.join((r['origin_cohort'],r['scenario_family'],str(int(t)))) for r,t in zip(rows,y)]
            table={}
            for label in sorted(set(labels)):
                selected=valid&np.array([s==label for s in labels]); n=int(selected.sum())
                table[label]={'available_count':n,'weight':n/int(valid.sum()),'mean':float(x[selected,23].mean()) if n else None}
            tables[part]=table
        composition=within=unmatched=0.
        for label in tables['train'].keys()|tables['validation'].keys():
            a=tables['train'].get(label,{'weight':0,'mean':None}); b=tables['validation'].get(label,{'weight':0,'mean':None})
            if a['mean'] is not None and b['mean'] is not None:
                composition+=(b['weight']-a['weight'])*a['mean']; within+=b['weight']*(b['mean']-a['mean'])
            else: unmatched+=(b['weight']*(b['mean'] or 0))-(a['weight']*(a['mean'] or 0))
        total=result['validation']['overall']['mean']-result['train']['overall']['mean']
        assert abs(total-composition-within-unmatched)<1e-12
        decompositions[mode]={'strata':tables,'composition_effect':composition,'within_stratum_effect':within,'unmatched_strata_effect':unmatched,'total_observed_mean_shift':total}
    return {'statistics':result,'decompositions':decompositions,'method':'Available-only means; exact disjoint-stratum standardization using Train stratum means and Validation weights. Overlapping family slices are descriptive, not additive. This is not causal adjustment.'}

def missingness(data,metas):
    result={}
    for part,(x,y,ids) in data.items():
        m=metas[part]; slices={'overall':np.ones(len(y),bool),'target_0':y==0,'target_1':y==1,**m['domain'],**m['normal']}
        result[part]={NAMES[i]:{'marker':FEATURES[i][7],'slices':{k:{z:v for z,v in stats(x[mask,i],FEATURES[i][7]).items() if z in ('support','missing_count','available_count','missing_rate','availability_rate')} for k,mask in slices.items()}} for i in MARKERS}
    return result

def univariate(data):
    result={}
    for part,(x,y,ids) in data.items():
        columns={}
        for i,f in enumerate(FEATURES):
            valid=np.ones(len(y),bool) if f[7] is None else x[:,i]!=f[7]
            groups={str(k):stats(x[y==k,i],f[7]) for k in (0,1)}
            overlap=[max(groups[k]['min'] for k in groups),min(groups[k]['max'] for k in groups)] if all(g['available_count'] for g in groups.values()) else None
            columns[f[0]]={'target_distributions':groups,'observed_range_overlap':overlap,
                'observed_auc_increasing_value':float(roc_auc_score(y[valid],x[valid,i])) if len(np.unique(y[valid]))==2 else None,
                'encoded_auc_increasing_value':float(roc_auc_score(y,x[:,i])),'available_support':int(valid.sum())}
        result[part]=columns
    return {'partitions':result,'interpretation':'Raw increasing-value AUC, never sign-selected or threshold-optimized. Observed AUC excludes only the documented marker and describes a different available subset. Encoded AUC includes markers. Nonmonotone associations can have low raw AUC; ranges do not exclude near separation.'}

def main():
    started=utc(); clock=time.monotonic()
    assert not OUT.exists() and not (R/'stage12_plan.json').exists(),'Preserve existing Stage 12 evidence; run in a fresh isolated development checkout.'
    before=read('stage12_protection_before.json'); assert compare(before,snapshot())['result']=='PASS'
    for name,digest in read('stage11_artifact_manifest.json').items(): assert sha(OLD/name)==digest,name
    data=load_matrices(); xt,yt,it=data['train']; xv,yv,iv=data['validation']
    reference=joblib.load(OLD/(REFERENCE+'.joblib'))
    params=reference.named_steps['model'].get_params(deep=False)
    assert params['random_state']==SEEDS[0] and params['early_stopping'] is False
    domains={d:[i for i,f in enumerate(FEATURES) if f[1]==d] for d in ('current','structuring','network','agent','coverage')}
    allcols=list(range(32))
    specs={'A':allcols,'B':[i for i in allcols if i!=22],'C':[i for i in allcols if i not in (22,23)],
           'D':[i for i in allcols if i not in domains['agent']], 'E':[i for i in allcols if i not in domains['network']],
           'F':[i for i in allcols if i not in domains['structuring']], 'G':domains['structuring'],'H':domains['network'],'I':domains['agent'],
           'J':[i for i in allcols if i not in domains['coverage']]}
    values=read('stage11_importance.json')[REFERENCE]['values']; ranking=sorted(NAMES,key=lambda n:(-abs(values[n]),n))
    smallparams=dict(max_iter=100,max_depth=3,max_leaf_nodes=7,min_samples_leaf=30,l2_regularization=2.,learning_rate=.07,early_stopping=False,random_state=SEEDS[0])
    plan={'saved_at_utc':utc(),'started_at_utc':started,'reference':REFERENCE,'threshold':.5,'seeds':SEEDS,
          'reference_estimator_parameters':params,'positive_training_weight':1.5,'negative_training_weight':1.,
          'ablations':{k:[NAMES[i] for i in v] for k,v in specs.items()},'tiny_feature_ranking':ranking,'tiny_feature_sizes':[1,2,3,5],
          'ranking_source':'Frozen Stage 11 reference absolute permutation AP importance; no Stage 12 ranking selection.',
          'missingness_classifier_parameters':smallparams,'missingness_classifier_weights':'unit weights',
          'dependence_rule':'Index=max(0, declines in Validation Macro F1, suspicious recall, suspicious F1, AP, increase in FPR). LOW <.02; MODERATE [.02,.05); HIGH [.05,.15); EXTREME >=.15. Deltas are removed minus full; rare-slice deltas reported separately.',
          'missingness_shortcut_rule':'Strong if Validation ROC-AUC >=.80 AND Macro F1 >=.70; moderate if ROC-AUC >=.70 OR Macro F1 >=.65; otherwise low. Descriptive heuristic, not proof of generator causality.',
          'fit_budget':20,'stability':'Five fresh clones at the five declared seeds and one additional same-seed repeat. No modification/refit of the saved reference. If seed-invariant, report repeated-fit reproducibility rather than independent stochastic robustness.',
          'diagnostic_metadata':'Frozen development ground truth/episode plans and type/channel projection from development transactions only; not passed to fit/predict. No history or feature extraction.',
          'low_support_flag':'Domain-only/overlap support <30 is low evidence; rare families always disclose counts.',
          'source_hashes':{n:sha(ROOT/'src'/n) for n in ('run_stage12.py','stage12_robustness.py')},
          'environment':{'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'numpy':np.__version__,'sklearn':sklearn.__version__,'threads':2}}
    save('plan',plan); OUT.mkdir(); (OUT/'README.md').write_text('Stage 12 diagnostic models only. No candidate promotion or official feature change. Train fits; fixed threshold 0.50.\n',encoding='utf-8')
    with threadpool_limits(limits=2): pt=reference.predict_proba(xt)[:,1]; pv=reference.predict_proba(xv)[:,1]
    saved=np.load(OLD/(REFERENCE+'_scores.npz'))
    replay={p:{'maximum_absolute_difference':float(np.max(np.abs(scores-saved[p]))),'predictions_identical':bool(np.array_equal(scores>=.5,saved[p]>=.5))} for p,scores in [('train',pt),('validation',pv)]}
    assert all(v['maximum_absolute_difference']<=1e-12 and v['predictions_identical'] for v in replay.values())
    metas={p:metadata(p,ids,y) for p,(x,y,ids) in data.items()}; meta=metas['validation']
    full=evaluate(xt,yt,xv,yv,pt,pv,meta)
    prior=next(c for c in read('stage11_candidate_results.json')['candidates'] if c['name']==REFERENCE)
    for part in ('train','validation'):
        assert full[part]==prior[part]
    for field,filename in [('domains','stage11_domain_recall.json'),('families','stage11_family_recall.json')]:
        old=read(filename)[REFERENCE]
        for code,v in full[field].items():
            assert all(old[code][k]==value for k,value in v.items()),(field,code)
    normalprior=read('stage11_normal_fpr.json')[REFERENCE]['target0_slices']
    for code,v in full['normal_fpr'].items(): assert all(normalprior[code][k]==value for k,value in v.items())
    save('reference_reproduction',{'result':'PASS','reference':REFERENCE,'replay':replay,'metrics_and_slices':full,'original_model_sha256':sha(OLD/(REFERENCE+'.joblib')),'original_scores_sha256':sha(OLD/(REFERENCE+'_scores.npz'))})
    print('Reference reproduced; preregistration saved; starting diagnostic fits.',flush=True)
    records={}; scores={}
    def fit(name,cols,seed=SEEDS[0],missing=False):
        xtrain=xt[:,cols]; xval=xv[:,cols]
        if missing:
            xtrain=np.column_stack([xt[:,i]==FEATURES[i][7] for i in cols]).astype(float)
            xval=np.column_stack([xv[:,i]==FEATURES[i][7] for i in cols]).astype(float)
        cfg=dict(smallparams if missing else params,random_state=seed)
        model=HistGradientBoostingClassifier(**cfg); begun=utc(); timer=time.monotonic()
        with warnings.catch_warnings(record=True) as caught,threadpool_limits(limits=2):
            warnings.simplefilter('always'); model.fit(xtrain,yt,sample_weight=None if missing else np.where(yt==1,1.5,1.))
            elapsed=time.monotonic()-timer; tr=model.predict_proba(xtrain)[:,1]; va=model.predict_proba(xval)[:,1]
        joblib.dump({'model':model,'columns':[NAMES[i] for i in cols],'missingness_only':missing,'markers':{NAMES[i]:FEATURES[i][7] for i in cols},'status':'DIAGNOSTIC ONLY'},OUT/(name+'.joblib'))
        np.savez_compressed(OUT/(name+'_scores.npz'),train=tr,validation=va)
        rec={'name':name,'started_at_utc':begun,'fit_seconds':elapsed,'seed':seed,'parameters':cfg,'columns':[NAMES[i] for i in cols],'warnings':[str(w.message) for w in caught],**evaluate(xt,yt,xv,yv,tr,va,meta)}
        records[name]=rec; scores[name]=(tr,va); save('fit_checkpoint',{'status':'running','fits':records})
        print(name,'Macro F1',round(rec['validation']['macro_f1'],6),'fit seconds',round(elapsed,3),flush=True)
        return rec
    ablations={'A':{'name':'A_saved_reference','columns':list(NAMES),'fit_seconds':0,'source':'Untouched saved reference reused, no refit',**full}}
    for key,cols in specs.items():
        if key!='A': ablations[key]=fit('ablation_'+key,cols)
    save('ablation_results',ablations)
    save('feature_dependence',{'preregistered_rule':plan['dependence_rule'],'growth_removed_B':dependence(full,ablations['B']),'growth_and_novelty_removed_C':dependence(full,ablations['C']),'all_ablations':{k:dependence(full,v) for k,v in ablations.items() if k!='A'}})
    tiny={str(n):fit('top_'+str(n),[NAMES.index(nm) for nm in ranking[:n]]) for n in (1,2,3,5)}
    save('small_feature_models',{'ranking':ranking,'models':tiny,'univariate':univariate(data)})
    miss=fit('missingness_only',MARKERS,missing=True); m=miss['validation']
    shortcut='strong' if m['roc_auc']>=.8 and m['macro_f1']>=.7 else 'moderate' if m['roc_auc']>=.7 or m['macro_f1']>=.65 else 'low'
    save('missingness_audit',{'feature_missingness':missingness(data,metas),'diagnostic_model':miss,'shortcut_signal':shortcut,'preregistered_rule':plan['missingness_shortcut_rule']})
    runs=[fit('seed_'+str(seed),allcols,seed) for seed in SEEDS]
    repeated=fit('same_seed_repeat',allcols,SEEDS[0])
    aggregates={k:{'mean':float(np.mean(a)),'std':float(np.std(a)),'min':float(np.min(a)),'max':float(np.max(a))} for k in KEYS for a in [[r['validation'][k] for r in runs]]}
    domainagg={d:{'mean':float(np.mean(a)),'std':float(np.std(a)),'min':float(np.min(a)),'max':float(np.max(a))} for d in meta['domain'] for a in [[r['domains'][d]['recall'] for r in runs]]}
    differences={r['name']:float(np.max(np.abs(scores[r['name']][1]-pv))) for r in runs+[repeated]}
    save('stability',{'seeds':SEEDS,'runs':runs,'same_seed_repeat':repeated,'validation_metric_summary':aggregates,'domain_summary':domainagg,'max_score_difference_from_saved_reference':differences,'seed_invariant_on_this_data':all(v==0 for v in differences.values()),'scope':'Same machine, library, data and thread limit. Exact equality here is repeated-fit reproducibility; not cross-platform or independent-population stability.'})
    save('agent_novelty_shift',novelty(data,metas))
    save('domain_independence',{k:v['domain_independence'] for k,v in ablations.items()})
    save('n3_diagnosis',error_diagnosis(xv,yv,pv,meta,'N3'))
    save('a4_diagnosis',error_diagnosis(xv,yv,pv,meta,'A4'))
    pred=pv>=.5
    hard={code:{'counts':fpr_slice(mask,pred),'fp_vs_tn':group_comparison(xv,mask&pred,mask&~pred),'categories':categories(meta,mask,pred,['transaction_type','channel','recipe','strength'])} for code in ('H1','H5') for mask in [meta['normal'][code]]}
    save('hard_negative_analysis',hard)
    comparators={}
    for name in (REFERENCE,'s11_27_random_forest','s11_15_xgboost','s11_08_gradient_boosting'):
        s=np.load(OLD/(name+'_scores.npz')); comparators[name]=evaluate(xt,yt,xv,yv,s['train'],s['validation'],meta)
    sparse={part:{code:recall_slice(metas[part]['family'][code],s>=.5) for code in ('S2','S4')} for part,s in [('train',pt),('validation',pv)]}
    save('comparator_robustness',{'models':comparators,'sparse_family_support_and_reference_recall':sparse,'no_new_comparator_fits':True})
    assert len(records)==20
    save('fit_checkpoint',{'status':'complete','fits':records,'fit_count':len(records),'started_at_utc':started,'completed_at_utc':utc(),'wall_seconds':time.monotonic()-clock})
    save('artifact_manifest',{p.name:sha(p) for p in OUT.iterdir() if p.is_file()})
    protection=compare(before,snapshot()); save('protection',protection); assert protection['result']=='PASS'
    print('Stage 12 diagnostics complete; protected files unchanged.',flush=True)

if __name__=='__main__': main()
