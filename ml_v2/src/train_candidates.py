"""Stage 4 Train/Validation candidate comparison at fixed threshold 0.50."""
from __future__ import annotations
import csv, json, platform, sys, time, warnings
from pathlib import Path
import joblib, numpy as np, sklearn
from sklearn.ensemble import RandomForestClassifier,GradientBoostingClassifier,HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.exceptions import ConvergenceWarning
from contracts import ROOT, load_development, safe_path, write_json
from feature_pipeline import FEATURE_NAMES
from preprocessing import TrainPreprocessor
from model_metrics import metrics,positive_recall_slices,false_positive_slices

SEED=20260921

def load_matrix(partition):
    folder=safe_path(ROOT/'features/development'/partition)
    with (folder/'X.csv').open(encoding='utf-8',newline='') as f: X=np.asarray([[float(x) for x in r] for r in csv.reader(f)],dtype=np.float64)
    with (folder/'y.csv').open(encoding='utf-8',newline='') as f: y=np.asarray([int(r[0]) for r in csv.reader(f)],dtype=np.uint8)
    with (folder/'row_ids.csv').open(encoding='utf-8',newline='') as f: ids=np.asarray([int(r['transaction_id']) for r in csv.DictReader(f)],dtype=np.uint64)
    names=json.loads((folder/'feature_names.json').read_text(encoding='utf-8'))
    if names!=FEATURE_NAMES or X.shape[1]!=30: raise ValueError('Frozen feature contract mismatch')
    return X,y,ids

def validation_metadata(ids):
    truth=load_development(ROOT/'data','validation','ground_truth'); by={int(r['transaction_id']):r for r in truth}
    return [by[int(i)] for i in ids]

def probabilities(model,X):
    if hasattr(model,'predict_proba'): return model.predict_proba(X)[:,1]
    return model.decision_function(X)

def importance(model,kind):
    if hasattr(model,'coef_'): values=np.abs(model.coef_[0]); measure='absolute_standardized_coefficient'
    elif hasattr(model,'feature_importances_'): values=model.feature_importances_; measure='impurity_or_gain_importance'
    else: return {'measure':'unsupported','ranking':[]}
    order=np.argsort(values)[::-1]
    return {'measure':measure,'top10':[{'feature':FEATURE_NAMES[i],'value':float(values[i])} for i in order[:10]],
            'top_feature_share':float(values[order[0]]/values.sum()) if values.sum() else 0.0}

def build_specs(xgb_available):
    specs=[]
    def add(algorithm,name,prep,params,weight='none',baseline=False): specs.append(dict(algorithm=algorithm,name=name,prep=prep,params=params,weight=weight,baseline=baseline))
    for prep in ('raw','robust'):
        add('logistic_regression',f'lr_{prep}_baseline',prep,{'C':1.0,'class_weight':None},baseline=True)
    for C in (.1,1.0,10.0):
        for weight in (None,'balanced'): add('logistic_regression',f'lr_robust_C{C}_{weight or "none"}','robust',{'C':C,'class_weight':weight})
    for prep in ('raw','clipped'):
        add('random_forest',f'rf_{prep}_baseline',prep,{'n_estimators':160,'max_depth':None,'min_samples_split':2,'min_samples_leaf':1,'max_features':'sqrt','class_weight':None},baseline=True)
        for weight in (None,'balanced_subsample'):
            add('random_forest',f'rf_{prep}_regularized_{weight or "none"}',prep,{'n_estimators':240,'max_depth':16,'min_samples_split':8,'min_samples_leaf':3,'max_features':'sqrt','class_weight':weight})
    for prep in ('raw','clipped'):
        add('gradient_boosting',f'gb_{prep}_baseline',prep,{'n_estimators':100,'learning_rate':.1,'max_depth':3,'min_samples_split':2,'min_samples_leaf':1,'subsample':1.0},baseline=True)
        for weight in ('none','balanced'):
            add('gradient_boosting',f'gb_{prep}_regularized_{weight}',prep,{'n_estimators':160,'learning_rate':.05,'max_depth':3,'min_samples_split':8,'min_samples_leaf':4,'subsample':.85},weight)
    for prep in ('raw','clipped'):
        add('hist_gradient_boosting',f'hgb_{prep}_baseline',prep,{'learning_rate':.1,'max_iter':120,'max_leaf_nodes':31,'max_depth':None,'min_samples_leaf':20,'l2_regularization':0.0,'class_weight':None},baseline=True)
        for weight in (None,'balanced'):
            add('hist_gradient_boosting',f'hgb_{prep}_regularized_{weight or "none"}',prep,{'learning_rate':.07,'max_iter':180,'max_leaf_nodes':31,'max_depth':10,'min_samples_leaf':30,'l2_regularization':1.0,'class_weight':weight})
    if xgb_available:
        for prep in ('raw','clipped'):
            add('xgboost',f'xgb_{prep}_baseline',prep,{'n_estimators':180,'learning_rate':.08,'max_depth':5,'min_child_weight':1,'subsample':1.0,'colsample_bytree':1.0,'reg_lambda':1.0,'reg_alpha':0.0,'scale_pos_weight':1.0},baseline=True)
            for weight in (1.0,88/12):
                add('xgboost',f'xgb_{prep}_regularized_{"balanced" if weight>1 else "none"}',prep,{'n_estimators':240,'learning_rate':.05,'max_depth':5,'min_child_weight':3,'subsample':.85,'colsample_bytree':.85,'reg_lambda':2.0,'reg_alpha':.05,'scale_pos_weight':weight})
    return specs

def make_model(spec):
    p=dict(spec['params']); a=spec['algorithm']
    if a=='logistic_regression': return LogisticRegression(max_iter=2000,solver='lbfgs',random_state=SEED,**p)
    if a=='random_forest': return RandomForestClassifier(random_state=SEED,n_jobs=1,**p)
    if a=='gradient_boosting': return GradientBoostingClassifier(random_state=SEED,**p)
    if a=='hist_gradient_boosting': return HistGradientBoostingClassifier(random_state=SEED,**p)
    if a=='xgboost':
        from xgboost import XGBClassifier
        return XGBClassifier(random_state=SEED,n_jobs=1,objective='binary:logistic',eval_metric='logloss',tree_method='hist',**p)
    raise ValueError(a)

def prep_for(name): return TrainPreprocessor(clip=name in ('clipped','robust'),scale=name=='robust')

def run(output_dir):
    overall_start=time.perf_counter()
    output_dir=safe_path(output_dir); output_dir.mkdir(parents=True,exist_ok=False)
    Xtr,ytr,idtr=load_matrix('train'); Xv,yv,idv=load_matrix('validation'); meta=validation_metadata(idv)
    if Xtr.shape!=(60000,30) or Xv.shape!=(15000,30): raise ValueError('Unexpected matrix shape')
    try:
        import xgboost; xgb_version=xgboost.__version__; xgb_available=True
    except Exception as exc: xgb_version=None; xgb_available=False; xgb_error=repr(exc)
    transformed={}; prep_objects={}
    for name in ('raw','clipped','robust'):
        pre=prep_for(name); transformed[name]=(pre.fit_transform(Xtr),pre.transform(Xv)); prep_objects[name]=pre
    results=[]; convergence=[]
    for number,spec in enumerate(build_specs(xgb_available),1):
        print(f"[{number}] {spec['name']}",flush=True); model=make_model(spec); A,B=transformed[spec['prep']]; start=time.perf_counter()
        kwargs={}
        if spec['algorithm']=='gradient_boosting' and spec['weight']=='balanced': kwargs['sample_weight']=compute_sample_weight('balanced',ytr)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always'); model.fit(A,ytr,**kwargs)
        elapsed=time.perf_counter()-start
        for w in caught:
            if issubclass(w.category,ConvergenceWarning): convergence.append({'configuration':spec['name'],'warning':str(w.message)})
        ptr=probabilities(model,A); pv=probabilities(model,B)
        row={**spec,'training_seconds':elapsed,'train_metrics':metrics(ytr,ptr),'validation_metrics':metrics(yv,pv),
             'importance':importance(model,spec['algorithm']),'warnings':[str(w.message) for w in caught]}
        results.append(row)
    best={}
    for algorithm in sorted({r['algorithm'] for r in results}):
        candidates=[r for r in results if r['algorithm']==algorithm]
        best[algorithm]=max(candidates,key=lambda r:(r['validation_metrics']['macro_f1'],r['validation_metrics']['suspicious_f1'],r['validation_metrics']['average_precision']))
    ranked=sorted(best.values(),key=lambda r:(r['validation_metrics']['macro_f1'],r['validation_metrics']['suspicious_f1'],r['validation_metrics']['average_precision']),reverse=True)
    shortlist=ranked[:2]; domains={}; hard={}; artifacts=[]
    for row in best.values():
        spec={k:row[k] for k in ('algorithm','name','prep','params','weight','baseline')}; pre=prep_objects[row['prep']]; model=make_model(spec); A,B=transformed[row['prep']]
        kwargs={'sample_weight':compute_sample_weight('balanced',ytr)} if row['algorithm']=='gradient_boosting' and row['weight']=='balanced' else {}
        model.fit(A,ytr,**kwargs); prob=probabilities(model,B); pred=(prob>=.5).astype(np.uint8)
        domains[row['name']]={'domains':positive_recall_slices(yv,pred,meta,'primary_domain',['structuring','network','agent']),
            'families':positive_recall_slices(yv,pred,meta,'primary_family',['variable_fragment_burst','similar_amount_repetition','distributed_same_day_fragmentation','variable_near_threshold_history','many_to_one_collection','one_to_many_dispersion','reciprocal_relationship_cycle','wallet_pass_through','agent_wallet_growth','agent_wallet_concentration','agent_temporal_burst','agent_flow_imbalance'])}
        hard[row['name']]=false_positive_slices(yv,pred,meta,['routine','H1','H2','H3','H4','H5','H6','H7','H8'])
        artifact=output_dir/f"{row['algorithm']}_best.joblib"; joblib.dump({'model':model,'preprocessor':pre,'feature_names':FEATURE_NAMES,'threshold':.5,'configuration':spec,'seed':SEED},artifact,compress=3); artifacts.append(artifact.name)
    # Selected configuration reproducibility: independently fit twice, exact prediction and probability comparison.
    selected=ranked[0]; spec={k:selected[k] for k in ('algorithm','name','prep','params','weight','baseline')}; A,B=transformed[selected['prep']]; repeated=[]
    for _ in range(2):
        model=make_model(spec); kwargs={'sample_weight':compute_sample_weight('balanced',ytr)} if spec['algorithm']=='gradient_boosting' and spec['weight']=='balanced' else {}; model.fit(A,ytr,**kwargs); p=probabilities(model,B); repeated.append((p,(p>=.5).astype(np.uint8),metrics(yv,p)))
    reproducible=bool(np.array_equal(repeated[0][1],repeated[1][1]) and np.allclose(repeated[0][0],repeated[1][0],rtol=0,atol=1e-12) and repeated[0][2]==repeated[1][2])
    preprocessing={name:prep.describe(FEATURE_NAMES) for name,prep in prep_objects.items()}
    versions={'python':platform.python_version(),'numpy':np.__version__,'scikit_learn':sklearn.__version__,'joblib':joblib.__version__,'xgboost':xgb_version}
    summary={'stage':4,'seed':SEED,'threshold':.5,'selection_metric':'validation_macro_f1','results':results,
        'best_by_algorithm':{k:v['name'] for k,v in best.items()},'ranking':[r['name'] for r in ranked],
        'primary_candidate':ranked[0]['name'],'secondary_candidate':ranked[1]['name'] if len(ranked)>1 else None,
        'preprocessing':preprocessing,'search_space':build_specs(xgb_available),'xgboost_available':xgb_available,
        'xgboost_unavailable_error':None if xgb_available else xgb_error,'convergence_warnings':convergence,
        'selected_reproducibility':{'result':'PASS' if reproducible else 'FAIL','predictions_identical':bool(np.array_equal(repeated[0][1],repeated[1][1])),
            'probabilities_max_abs_difference':float(np.max(np.abs(repeated[0][0]-repeated[1][0]))),'metrics_identical':repeated[0][2]==repeated[1][2]},
        'versions':versions,'artifacts':artifacts,'total_stage4_training_seconds':time.perf_counter()-overall_start}
    write_json(ROOT/'reports/stage4_candidate_results.json',summary); write_json(ROOT/'reports/stage4_domain_results.json',domains); write_json(ROOT/'reports/stage4_hard_negative_results.json',hard)
    return summary,domains,hard

if __name__=='__main__':
    result,_,_=run(ROOT/'models/candidates'); print(json.dumps({'primary':result['primary_candidate'],'secondary':result['secondary_candidate']},indent=2))
