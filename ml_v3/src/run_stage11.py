"""Bounded Train-only fits and fixed-0.50 Validation comparison."""
import os
os.environ.setdefault('OMP_NUM_THREADS','2')
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
os.environ.setdefault('MKL_NUM_THREADS','2')
import json, time, warnings, platform, importlib, sys, math, re
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import sklearn
import joblib
from sklearn.pipeline import Pipeline
from sklearn.exceptions import ConvergenceWarning
from sklearn.inspection import permutation_importance
from sklearn.metrics import (accuracy_score,balanced_accuracy_score,f1_score,precision_recall_fscore_support,
                             confusion_matrix,roc_auc_score,average_precision_score)
from threadpoolctl import threadpool_limits
from contracts import load_development
from stage10a_contract import NAMES, FEATURES, VERSION
from stage11_preprocessing import Stage11Preprocessor, MODES
from stage11_models import SEED, configurations, build, sample_weights
from stage11_protection import ROOT, sha, snapshot, compare

R=ROOT/'reports'; M=ROOT/'models/stage11_candidates'; THRESHOLD=.50
EXPECTED={'train':{0:39781,1:20219},'validation':{0:9945,1:5055}}
FAMILY_NAMES=('variable_fragment_burst','similar_amount_repetition','distributed_same_day_fragmentation','variable_near_threshold_history',
 'many_to_one_collection','one_to_many_dispersion','reciprocal_relationship_cycle','wallet_pass_through',
 'agent_wallet_growth','agent_wallet_concentration','agent_temporal_burst','agent_flow_imbalance')
FAMILIES=dict(zip([p+str(i) for p in 'SNA' for i in range(1,5)],FAMILY_NAMES))

def save(name,obj):
    def clean(x):
        if isinstance(x,dict): return {k:clean(v) for k,v in x.items()}
        if isinstance(x,(tuple,list)): return [clean(v) for v in x]
        if isinstance(x,np.generic): return clean(x.item())
        if isinstance(x,float) and not math.isfinite(x): return str(x)
        return x
    p=R/name
    payload=json.dumps(clean(obj),indent=2,sort_keys=True,allow_nan=False)+'\n'
    temp=p.with_suffix('.json.tmp'); temp.write_text(payload,encoding='utf-8',newline='\n'); temp.replace(p)

def load_matrices():
    freeze=json.loads((R/'stage10a_contract_manifest.json').read_text())
    for n,digest in freeze['hashes'].items(): assert sha(ROOT/n)==digest,n
    repro=json.loads((R/'stage10a_reproducibility.json').read_text())
    assert json.loads((ROOT/'features/development/stage10a/version.json').read_text())['version']==VERSION
    result={}
    for part,expected in EXPECTED.items():
        p=ROOT/'features/development/stage10a'/part
        for n,digest in repro['runs']['run_a']['partitions'][part]['hashes'].items(): assert sha(p/n)==digest,n
        frame=pd.read_csv(p/'X.csv',float_precision='round_trip'); y=pd.read_csv(p/'y.csv')['decision_point_target'].to_numpy(dtype=int)
        ids=pd.read_csv(p/'row_ids.csv',dtype=str)['transaction_id'].tolist()
        assert frame.columns.tolist()==list(NAMES)==json.loads((p/'feature_names.json').read_text())
        x=frame.to_numpy(dtype=float)
        assert x.shape==(sum(expected.values()),32) and np.isfinite(x).all()
        assert dict(zip(*np.unique(y,return_counts=True)))==expected and len(set(ids))==len(ids)==len(y)
        result[part]=(x,y,ids)
    return result

def metrics(y,p):
    assert np.isfinite(p).all() and ((p>=0)&(p<=1)).all()
    pred=(p>=THRESHOLD).astype(int)
    cm=confusion_matrix(y,pred,labels=[0,1]); tn,fp,fn,tp=cm.ravel()
    precision,recall,f1,support=precision_recall_fscore_support(y,pred,labels=[0,1],zero_division=0)
    return dict(accuracy=float(accuracy_score(y,pred)),balanced_accuracy=float(balanced_accuracy_score(y,pred)),
        macro_f1=float(f1_score(y,pred,average='macro',zero_division=0)),
        suspicious_precision=float(precision[1]),suspicious_recall=float(recall[1]),suspicious_f1=float(f1[1]),
        normal_precision=float(precision[0]),normal_recall=float(recall[0]),normal_f1=float(f1[0]),
        roc_auc=float(roc_auc_score(y,p)),average_precision=float(average_precision_score(y,p)),
        false_positive_rate=float(fp/(fp+tn)),confusion_matrix=cm.tolist(),threshold=THRESHOLD)

def distribution(y,p):
    out={}
    for k in (0,1):
        values=p[y==k]; q=np.quantile(values,[0,.01,.05,.25,.5,.75,.95,.99,1])
        out[str(k)]={n:float(v) for n,v in zip(('min','q01','q05','q25','median','q75','q95','q99','max'),q)}
        out[str(k)].update(count=len(values),mean=float(values.mean()),std=float(values.std()))
    out['range_overlap']=[max(out['0']['min'],out['1']['min']),min(out['0']['max'],out['1']['max'])]
    out['middle_90_percent_overlap']=[max(out['0']['q05'],out['1']['q05']),min(out['0']['q95'],out['1']['q95'])]
    out['interpretation']='Reversed overlap endpoints mean no intersection. Score separation is not calibration; weighted scores are not asserted to be population probabilities.'
    return out

def recall_slice(mask,pred):
    n=int(mask.sum()); tp=int(pred[mask].sum())
    return dict(support=n,tp=tp,fn=n-tp,recall=tp/n if n else None)

def fpr_slice(mask,pred):
    n=int(mask.sum()); fp=int(pred[mask].sum())
    return dict(support=n,fp=fp,tn=n-fp,false_positive_rate=fp/n if n else None)

def diagnostic_metadata(ids,y):
    # All candidate probabilities have already been produced at this point.
    truth=load_development(ROOT/'data','validation','ground_truth')
    byid={r['transaction_id']:r for r in truth}; rows=[byid[i] for i in ids]
    assert np.array_equal(y,np.array([int(r['decision_point_target']) for r in rows]))
    evidence=[set(filter(None,r['evidence_families'].split(';'))) for r in rows]
    assert all(bool(s)==bool(t) for s,t in zip(evidence,y))
    family={code:np.array([name in s and target==1 for s,target in zip(evidence,y)]) for code,name in FAMILIES.items()}
    domain={name:np.logical_or.reduce([family[p+str(i)] for i in range(1,5)]) for p,name in [('S','structuring'),('N','network'),('A','agent')]}
    normal={'routine':np.array([r['origin_cohort']=='routine' and target==0 for r,target in zip(rows,y)])}
    for i in range(1,9): normal[f'H{i}']=np.array([r['scenario_family']==f'H{i}' and target==0 for r,target in zip(rows,y)])
    normal['campaign_member_target0']=np.array([r['origin_cohort']=='campaign_member' and target==0 for r,target in zip(rows,y)])
    # Available frozen subtype recipe metadata is used solely for diagnostics.
    plans=json.loads((ROOT/'data/development/validation/episode_plans.json').read_text())
    patterns={str(tid):str(e['pattern']) for e in plans['episodes'] for tid in e['transaction_ids']}
    subtype_keys=sorted({(r['scenario_family'],patterns[r['transaction_id']]) for r in rows if r['origin_cohort']=='hard_scenario' and r['transaction_id'] in patterns})
    for family_name,pattern in subtype_keys:
        normal[family_name+'/'+pattern]=np.array([target==0 and r['scenario_family']==family_name and patterns.get(r['transaction_id'])==pattern for r,target in zip(rows,y)])
    origins={origin:np.array([r['origin_cohort']==origin for r in rows]) for origin in ('routine','hard_scenario','campaign_member')}
    return domain,family,normal,origins

def importance(pipe,train_x,val_x,val_y):
    model=pipe.named_steps['model']; prep=pipe.named_steps['preprocessing']; extra={}
    if hasattr(model,'coef_'):
        robust=model.coef_[0]
        std_coef=robust*np.std(prep.transform(train_x),axis=0)
        scores=std_coef; kind='signed coefficient per Train SD of transformed input'
        extra={'robust_scaled_coefficients':dict(zip(NAMES,map(float,robust))),'intercept':float(model.intercept_[0])}
    elif hasattr(model,'feature_importances_'):
        scores=model.feature_importances_; kind='normalized gain' if model.__class__.__name__=='XGBClassifier' else 'impurity reduction'
    else:
        perm=permutation_importance(pipe,val_x,val_y,scoring='average_precision',n_repeats=3,random_state=SEED,max_samples=3000,n_jobs=1)
        scores=perm.importances_mean; kind='Validation permutation drop in average precision; 3 repeats, 3000-row subsamples'
        extra={'permutation_std':dict(zip(NAMES,map(float,perm.importances_std))),'caveat':'Descriptive Validation reuse; correlated features share signal and sparse families may be absent from the subsample. No feature selection.'}
    mass=np.abs(scores); total=float(mass.sum())
    shares={domain:float(sum(mass[i] for i,f in enumerate(FEATURES) if f[1]==domain)/total) if total else 0. for domain in ('current','structuring','network','agent','coverage')}
    missing_mass=float(sum(mass[i] for i,f in enumerate(FEATURES) if f[7] is not None)/total) if total else 0.
    extra.update(method=kind,values=dict(zip(NAMES,map(float,scores))),domain_absolute_mass=shares,
        top_feature=NAMES[int(np.argmax(mass))],top_feature_absolute_share=float(mass.max()/total) if total else 0.,
        current_amount_absolute_share=float(mass[0]/total) if total else 0.,marker_bearing_columns_absolute_share=missing_mass,
        missingness_caveat='Importance of a marker-bearing feature is not importance of missingness alone.',
        concentration_flag=bool(total and (mass.max()/total>.5 or max(shares.values())>.7)))
    if hasattr(model,'estimators_') and prep.mode in ('raw','clipped'):
        trees=np.asarray(model.estimators_,dtype=object).ravel(); count=0; isolated=0
        for tree in trees:
            for i,threshold in zip(tree.tree_.feature,tree.tree_.threshold):
                if i<0: continue
                count+=1; f=FEATURES[i]
                if f[7] is not None and f[7]<=threshold<f[5]: isolated+=1
        extra['sentinel_isolating_split_fraction']=isolated/count if count else 0.
        extra['sentinel_split_note']='Fraction of internal splits with threshold between sentinel and valid lower bound; unweighted structural diagnostic.'
    return extra

def main():
    start=time.monotonic(); before=json.loads((R/'stage11_protection_before.json').read_text())
    assert compare(before,snapshot())['result']=='PASS'
    resume='--resume' in sys.argv
    assert resume or not M.exists(),'Refuse to overwrite a prior Stage 11 experiment.'
    xgb_error=None
    try:
        xgb=importlib.import_module('xgboost'); xgb_version=xgb.__version__
    except (ImportError,OSError) as exc: xgb_version=None; xgb_error=repr(exc)
    specs=configurations(xgb_version is not None)
    assert len(specs)<=36
    plan={'seed':SEED,'threshold':THRESHOLD,'feature_version':VERSION,'configurations':specs,
          'frozen_at_utc':datetime.now(timezone.utc).isoformat(),
          'selection':'Highest Validation Macro F1 per converged model family, plus highest recall with FPR<=.10 and highest AP. Primary: highest Macro F1 with recall>=.70, FPR<=.10 and Train-Val Macro F1 gap<=.10 if available; otherwise highest Macro F1 flagged for tradeoff review. Domain/family diagnostics must qualify any recommendation.',
          'severe_gap_rule':'Train minus Validation >.10 Macro F1 or >.15 suspicious F1/recall/AP/ROC-AUC.',
          'runtime_environment':dict(python=sys.version,executable=sys.executable,platform=platform.platform(),numpy=np.__version__,pandas=pd.__version__,sklearn=sklearn.__version__,xgboost=xgb_version),
          'xgboost_unavailable_reason':xgb_error,
          'source_hashes':{p:sha(ROOT/'src'/p) for p in ('stage11_models.py','stage11_preprocessing.py','stage11_protection.py','run_stage11.py')}}
    if resume:
        original=json.loads((R/'stage11_search_plan.json').read_text())
        assert original['configurations']==specs and original['seed']==SEED and original['threshold']==THRESHOLD
        for n,digest in original['source_hashes'].items():
            if n!='run_stage11.py': assert sha(ROOT/'src'/n)==digest
        amendment={'reason':'Logging recovery encodes nonfinite estimator defaults as text and writes atomic checkpoints. Subsequent Random Forest replay differed only by floating-point parallel summation; require maximum score difference <=1e-12 AND identical fixed-0.50 predictions, recording actual differences. No model/preprocessing/grid/threshold change; saved fits reused.',
                   'original_runner_sha256':original['source_hashes']['run_stage11.py'],
                   'resumed_runner_sha256':sha(Path(__file__)), 'resumed_at_utc':datetime.now(timezone.utc).isoformat()}
        previous_path=R/'stage11_execution_amendment.json'
        if previous_path.exists():
            previous=json.loads(previous_path.read_text())
            amendment['previous_amendments']=previous.get('previous_amendments',[])+[{k:v for k,v in previous.items() if k!='previous_amendments'}]
        plan=original; plan['execution_amendment']=amendment
        save('stage11_execution_amendment.json',amendment)
    else: save('stage11_search_plan.json',plan)
    data=load_matrices(); xt,yt,_=data['train']; xv,yv,ids=data['validation']
    preprocessors={mode:Stage11Preprocessor(mode).fit(xt) for mode in MODES}
    transformed={mode:(p.transform(xt),p.transform(xv)) for mode,p in preprocessors.items()}
    save('stage11_preprocessing.json',{k:p.record() for k,p in preprocessors.items()})
    M.mkdir(parents=True,exist_ok=resume)
    (M/'README.md').write_text('# DEVELOPMENT CANDIDATE — NOT FINAL\n\nStage 11 candidates fitted on Train only. Fixed comparison threshold 0.50. No application integration. Do not load pickle/joblib files from untrusted sources.\n',encoding='utf-8')
    results=[]
    if resume:
        checkpoint=(R/'stage11_candidate_results.json').read_text()
        try:
            prior=json.loads(checkpoint)
            assert prior['status']=='running','Completed experiments cannot resume.'
            results=prior['candidates']
        except json.JSONDecodeError:
            preserved=R/'stage11_interrupted_checkpoint.txt'
            assert not preserved.exists()
            preserved.write_text(checkpoint,encoding='utf-8')
            pos=checkpoint.index('[',checkpoint.index('"candidates"'))+1; decoder=json.JSONDecoder()
            while True:
                pos0=pos
                while pos<len(checkpoint) and checkpoint[pos] in ' \r\n,': pos+=1
                try: item,end=decoder.raw_decode(checkpoint,pos)
                except json.JSONDecodeError: break
                results.append(item); pos=end
            for spec in specs[len(results):]:
                model_path=M/(spec['name']+'.joblib'); score_path=M/(spec['name']+'_scores.npz')
                if not model_path.exists() or not score_path.exists(): break
                pipe=joblib.load(model_path); saved=np.load(score_path); tail=checkpoint[pos0:]
                fit=re.search(r'"fit_seconds": ([0-9.]+)',tail); elapsed=re.search(r'"elapsed_seconds": ([0-9.]+)',tail)
                assert fit and elapsed
                results.append(dict(spec,train=metrics(yt,saved['train']),validation=metrics(yv,saved['validation']),
                    fit_seconds=float(fit.group(1)),elapsed_seconds=float(elapsed.group(1)),
                    warnings=['Original fit warning capture was not retained after metadata serialization interruption. Saved model/scores recovered; no convergence warning is available for this XGBoost fit.'],
                    converged=True,fitted_parameters=pipe.named_steps['model'].get_params(),n_iter=[]))
            save('stage11_candidate_results.json',{'status':'running','plan':plan,'candidates':results})
        print('Resuming after',len(results),'saved fits; unchanged grid.',flush=True)
    for spec in specs:
        if any(r['name']==spec['name'] for r in results): continue
        tick=time.monotonic(); row=dict(spec); mode=spec['preprocessing']; a,b=transformed[mode]
        model=build(spec,39781/20219); weights=sample_weights(spec,yt)
        with warnings.catch_warnings(record=True) as caught, threadpool_limits(limits=2):
            warnings.simplefilter('always')
            model.fit(a,yt,**({'sample_weight':weights} if weights is not None else {}))
            fit_seconds=time.monotonic()-tick
            pt=model.predict_proba(a)[:,1]; pv=model.predict_proba(b)[:,1]
        assert model.n_features_in_==32
        row.update(train=metrics(yt,pt),validation=metrics(yv,pv),fit_seconds=fit_seconds,
                   elapsed_seconds=time.monotonic()-tick,warnings=[str(w.message) for w in caught],
                   converged=not any(issubclass(w.category,ConvergenceWarning) for w in caught),
                   fitted_parameters=model.get_params(),n_iter=np.asarray(getattr(model,'n_iter_',[])).tolist())
        pipe=Pipeline([('preprocessing',preprocessors[mode]),('model',model)])
        joblib.dump(pipe,M/(spec['name']+'.joblib'),compress=3)
        np.savez_compressed(M/(spec['name']+'_scores.npz'),train=pt,validation=pv)
        results.append(row)
        save('stage11_candidate_results.json',{'status':'running','plan':plan,'candidates':results})
        print(spec['name'],mode,spec['weight'],'Val Macro F1',round(row['validation']['macro_f1'],4),'fit seconds',round(fit_seconds,1),flush=True)
    eligible=[r for r in results if r['converged']]
    assert eligible
    best=lambda rows,key='macro_f1':max(rows,key=lambda r:(r['validation'][key],r['validation']['suspicious_recall'],-r['validation']['false_positive_rate']))
    short={best([r for r in eligible if r['family']==f])['name'] for f in sorted({r['family'] for r in eligible})}
    safe=[r for r in eligible if r['validation']['false_positive_rate']<=.10]
    if safe: short.add(best(safe,'suspicious_recall')['name'])
    short.add(best(eligible,'average_precision')['name'])
    qualified=[r for r in safe if r['validation']['suspicious_recall']>=.70 and r['train']['macro_f1']-r['validation']['macro_f1']<=.10]
    primary=best(qualified or eligible); short.add(primary['name'])
    shortlist=sorted([r for r in results if r['name'] in short],key=lambda r:r['validation']['macro_f1'],reverse=True)
    # Predictions exist for every candidate before joining any diagnostic fields.
    domains,families,normals,origins=diagnostic_metadata(ids,yv)
    domain_results={}; family_results={}; normal_results={}; gaps={}; probabilities={}; importances={}
    for row in shortlist:
        name=row['name']; scores=np.load(M/(name+'_scores.npz')); pred=scores['validation']>=THRESHOLD
        domain_results[name]={k:recall_slice(mask,pred) for k,mask in domains.items()}
        family_results[name]={k:dict(family=FAMILIES[k],**recall_slice(mask,pred)) for k,mask in families.items()}
        normal_results[name]={'target0_slices':{k:fpr_slice(mask,pred) for k,mask in normals.items()},
            'origin_review_rates':{k:dict(support=int(mask.sum()),predicted_reviews=int(pred[mask].sum()),review_rate=float(pred[mask].mean())) for k,mask in origins.items()}}
        gap={key:row['train'][key]-row['validation'][key] for key in ('macro_f1','suspicious_f1','suspicious_recall','roc_auc','average_precision')}
        gap['severe_flag']=bool(gap['macro_f1']>.10 or any(gap[k]>.15 for k in gap if k!='macro_f1'))
        gaps[name]=gap
        probabilities[name]={'train':distribution(yt,scores['train']),'validation':distribution(yv,scores['validation'])}
        pipe=joblib.load(M/(name+'.joblib'))
        replay=pipe.predict_proba(xv)[:,1]
        difference=float(np.max(np.abs(replay-scores['validation'])))
        same_predictions=bool(np.array_equal(replay>=THRESHOLD,pred))
        row['artifact_reload']={'max_absolute_score_difference':difference,'score_tolerance':1e-12,
                                'fixed_threshold_predictions_identical':same_predictions}
        assert difference<=1e-12 and same_predictions
        with threadpool_limits(limits=2): importances[name]=importance(pipe,xt,xv,yv)
        print('Diagnostics complete:',name,flush=True)
    targets={'macro_f1':.80,'suspicious_recall':.70,'suspicious_f1':.70,'average_precision':.75,'false_positive_rate':.10}
    checks={k:(primary['validation'][k]<=v if k=='false_positive_rate' else primary['validation'][k]>=v) for k,v in targets.items()}
    domain_checks={k:domain_results[primary['name']][k]['recall']>=v for k,v in {'structuring':.65,'network':.70,'agent':.65}.items()}
    ignored=[k for k,v in family_results[primary['name']].items() if v['support'] and v['recall']<.20]
    decision='A' if all(checks.values()) and all(domain_checks.values()) and not ignored and not gaps[primary['name']]['severe_flag'] else 'B'
    # B denotes useful discrimination with deficiencies. We do not infer an
    # intrinsic data/representation limit from a compact search alone.
    if primary['validation']['roc_auc']<.65: decision='E'
    conclusion={'technical_execution':'PASS','decision':decision,'primary_development_reference':primary['name'],
                'highest_macro_f1':best(eligible)['name'],'quality_goals':targets,'quality_goals_met':checks,'domain_goals_met':domain_checks,
                'families_below_20_percent_recall':ignored,'primary_met_predeclared_tradeoff_filter':bool(qualified),
                'shortlisted_names':[r['name'] for r in shortlist],'selection':plan['selection'],
                'candidate_artifacts':'DEVELOPMENT CANDIDATE — NOT FINAL','fits':len(results),'configurations':len(specs),
                'runtime_seconds':(datetime.now(timezone.utc)-datetime.fromisoformat(plan['frozen_at_utc'])).total_seconds(),
                'resumed_process_seconds':time.monotonic()-start,'runtime_note':'Wall time from frozen plan includes logging interruption/recovery; summed fit times are recorded separately.',
                'no_refit_on_validation':True}
    protected=compare(before,snapshot())
    assert protected['result']=='PASS'
    save('stage11_protection.json',protected)
    for filename,obj in [('shortlist',dict(summary=conclusion,candidates=shortlist)),('domain_recall',domain_results),
             ('family_recall',family_results),('normal_fpr',normal_results),('generalization',gaps),
             ('probability_quality',probabilities),('importance',importances)]: save('stage11_'+filename+'.json',obj)
    save('stage11_candidate_results.json',{'status':'complete','plan':plan,'summary':conclusion,'candidates':results})
    save('stage11_artifact_manifest.json',{p.name:sha(p) for p in M.iterdir() if p.is_file()})
    print(json.dumps(conclusion),flush=True)

if __name__=='__main__': main()
