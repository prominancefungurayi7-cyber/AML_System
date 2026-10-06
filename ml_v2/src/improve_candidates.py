"""Stage 5 controlled Train/Validation search. Never loads holdout partitions."""
from __future__ import annotations
import json, platform, sys, time, warnings
from pathlib import Path
import joblib, numpy as np, sklearn
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
from contracts import ROOT, write_json
from feature_pipeline import FEATURE_NAMES
from model_metrics import metrics, positive_recall_slices, false_positive_slices
from train_candidates import load_matrix, validation_metadata, prep_for, probabilities
from run_stage4 import protected, v2_inputs

SEED=20260921
DOMAINS=['structuring','network','agent']
FAMILIES=['variable_fragment_burst','similar_amount_repetition','distributed_same_day_fragmentation','variable_near_threshold_history','many_to_one_collection','one_to_many_dispersion','reciprocal_relationship_cycle','wallet_pass_through','agent_wallet_growth','agent_wallet_concentration','agent_temporal_burst','agent_flow_imbalance']
NORMALS=['routine','H1','H2','H3','H4','H5','H6','H7','H8']

def specs():
    out=[]
    def add(family,prep,weight,**params): out.append({'name':f's5_{family}_{len(out):03d}','algorithm':family,'prep':prep,'weight':weight,'params':params})
    # Compact structural search followed by controlled weight sweeps.
    xstruct=[(2,5,.05,400,.85,.85,5,.1,.1),(3,3,.05,400,.85,.85,5,.1,.1),(4,5,.03,550,.8,.8,10,.5,.25),(5,8,.03,500,.75,.8,10,.5,.25),(3,1,.08,300,1,1,2,0,0),(6,12,.02,600,.7,.7,10,1,.5)]
    for depth,child,lr,n,sub,col,lam,alpha,gamma in xstruct:
        for weight in (1,3,5,88/12):
            add('xgboost','raw',weight,max_depth=depth,min_child_weight=child,learning_rate=lr,n_estimators=n,subsample=sub,colsample_bytree=col,reg_lambda=lam,reg_alpha=alpha,gamma=gamma)
    # Fill the middle of the weight range on the least complex XGBoost shapes.
    for weight in (2,4,6):
        for depth,child,lr,n,sub,col,lam,alpha,gamma in xstruct[:2]:
            add('xgboost','raw',weight,max_depth=depth,min_child_weight=child,learning_rate=lr,n_estimators=n,subsample=sub,colsample_bytree=col,reg_lambda=lam,reg_alpha=alpha,gamma=gamma)
    hstruct=[(.05,240,15,5,60,5),(.07,220,31,7,60,5),(.03,400,15,5,100,10),(.08,180,31,8,40,2),(.05,300,63,8,80,10)]
    for lr,n,leaves,depth,leaf,l2 in hstruct:
        for weight in (1,2,4,6): add('hist_gradient_boosting','clipped',weight,learning_rate=lr,max_iter=n,max_leaf_nodes=leaves,max_depth=depth,min_samples_leaf=leaf,l2_regularization=l2)
    gstruct=[(220,.05,2,20,10,.8),(300,.03,2,30,15,.85),(180,.07,3,20,10,.8),(350,.03,3,40,20,.75)]
    for n,lr,depth,split,leaf,sub in gstruct:
        for weight in (1,2,4,6): add('gradient_boosting','clipped',weight,n_estimators=n,learning_rate=lr,max_depth=depth,min_samples_split=split,min_samples_leaf=leaf,subsample=sub)
    for depth,leaf,split,features,weight in [(8,10,30,.5,2),(10,20,50,.5,4),(12,10,40,.7,4),(6,30,80,.5,6)]:
        add('random_forest','raw',weight,n_estimators=240,max_depth=depth,min_samples_leaf=leaf,min_samples_split=split,max_features=features)
    add('logistic_regression','robust',1,C=1,solver='newton-cholesky',max_iter=500)
    add('logistic_regression','robust',3,C=1,solver='newton-cholesky',max_iter=500)
    return out

def make_model(s,seed=SEED):
    p=s['params']; a=s['algorithm']; common={'random_state':seed}
    if a=='xgboost':
        from xgboost import XGBClassifier
        return XGBClassifier(**p,scale_pos_weight=s['weight'],objective='binary:logistic',eval_metric='logloss',tree_method='hist',n_jobs=1,**common)
    if a=='hist_gradient_boosting': return HistGradientBoostingClassifier(**p,**common)
    if a=='gradient_boosting': return GradientBoostingClassifier(**p,**common)
    if a=='random_forest': return RandomForestClassifier(**p,n_jobs=1,**common)
    if a=='logistic_regression': return LogisticRegression(**p,**common)
    raise ValueError(a)

def fit(s,A,y,seed=SEED):
    model=make_model(s,seed); kwargs={}
    if s['algorithm']!='xgboost' and s['weight']!=1:
        kwargs['sample_weight']=np.where(y==1,float(s['weight']),1.0)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always',ConvergenceWarning)
        model.fit(A,y,**kwargs)
    return model,[str(w.message) for w in caught if issubclass(w.category,ConvergenceWarning)]

def gap(train,valid):
    return {k:train[k]-valid[k] for k in ('macro_f1','suspicious_f1','suspicious_recall','roc_auc','average_precision')}

def evaluate(s,transformed,ytr,yv):
    A,B=transformed[s['prep']]; start=time.perf_counter(); model,warnings_=fit(s,A,ytr)
    tr=metrics(ytr,probabilities(model,A)); va=metrics(yv,probabilities(model,B))
    return {'spec':s,'train':tr,'validation':va,'gap':gap(tr,va),'training_seconds':time.perf_counter()-start,'convergence_warnings':warnings_},model

def main():
    before=protected(); inputs=v2_inputs(); started=time.perf_counter()
    Xtr,ytr,_=load_matrix('train'); Xv,yv,idv=load_matrix('validation')
    if Xtr.shape!=(60000,30) or Xv.shape!=(15000,30): raise ValueError('Unexpected development shape')
    metadata=validation_metadata(idv)
    prep={}; transformed={}
    for name in ('raw','clipped','robust'):
        pre=prep_for(name); transformed[name]=(pre.fit_transform(Xtr),pre.transform(Xv)); prep[name]=pre
    all_results=[]; specs_=specs(); shortlist=[]; models={}
    for i,s in enumerate(specs_,1):
        print(f'[{i}/{len(specs_)}] {s["name"]} {s["algorithm"]} weight={s["weight"]}',flush=True)
        row,model=evaluate(s,transformed,ytr,yv); all_results.append(row)
        score=row['validation']['macro_f1']
        if score>=.57 or (s['algorithm']=='logistic_regression' and not row['convergence_warnings']):
            shortlist.append(row); models[s['name']]=model
    ranked=sorted(shortlist,key=lambda r:r['validation']['macro_f1'],reverse=True)
    # Pareto-aware reporting: keep the best per family plus high recall, low FPR alternatives.
    selected={}
    for family in {r['spec']['algorithm'] for r in ranked}:
        rows=[r for r in ranked if r['spec']['algorithm']==family]
        if rows: selected[rows[0]['spec']['name']]=rows[0]
    for r in ranked:
        v=r['validation']
        if len(selected)>=12: break
        if v['suspicious_recall']>=.5 and v['false_positive_rate']<=.25 and r['gap']['macro_f1']<=.15: selected[r['spec']['name']]=r
    domains={}; hard={}; general={}; reproducibility={}; artifacts=[]
    for name,row in selected.items():
        s=row['spec']; model=models[name]; B=transformed[s['prep']][1]; pred=(probabilities(model,B)>=.5).astype(np.uint8)
        domains[name]={'domains':positive_recall_slices(yv,pred,metadata,'primary_domain',DOMAINS),'families':positive_recall_slices(yv,pred,metadata,'primary_family',FAMILIES)}
        hard[name]=false_positive_slices(yv,pred,metadata,NORMALS); general[name]={'train':row['train'],'validation':row['validation'],'train_minus_validation':row['gap']}
    # Refit strongest configurations twice and check two additional seeds.
    for row in ranked[:2]:
        s=row['spec']; A,B=transformed[s['prep']]; probs=[]; seed_metrics={}
        for seed in (SEED,SEED,SEED+1,SEED+2):
            m,w=fit(s,A,ytr,seed); p=probabilities(m,B); probs.append(p); seed_metrics[str(seed)]=metrics(yv,p)
        reproducibility[s['name']]={'max_abs_difference_same_seed':float(np.max(np.abs(probs[0]-probs[1]))),'predictions_identical_same_seed':bool(np.array_equal(probs[0]>=.5,probs[1]>=.5)),'seed_metrics':seed_metrics}
    model_dir=ROOT/'models/candidates'
    for name,row in selected.items():
        path=model_dir/f'{name}.joblib'
        if path.exists(): raise FileExistsError(path)
        joblib.dump({'model':models[name],'preprocessor':prep[row['spec']['prep']],'feature_names':FEATURE_NAMES,'threshold':.5,'configuration':row['spec'],'seed':SEED,'stage':5},path,compress=3)
        artifacts.append(path.relative_to(ROOT).as_posix())
    after=protected(); inputs_after=v2_inputs()
    protection={'result':'PASS' if before==after and inputs==inputs_after else 'FAIL','protected_file_count':len(before),'v2_input_file_count':len(inputs),'v1_application_changes':sorted(p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)),'v2_input_changes':sorted(p for p in inputs.keys()|inputs_after.keys() if inputs.get(p)!=inputs_after.get(p))}
    if protection['result']!='PASS': raise RuntimeError(f'Protection failed: {protection}')
    search={'stage':5,'seed':SEED,'threshold':.5,'configuration_count':len(specs_),'training_seconds':time.perf_counter()-started,'versions':{'python':platform.python_version(),'numpy':np.__version__,'sklearn':sklearn.__version__},'results':all_results,'reproducibility':reproducibility,'artifacts':artifacts}
    write_json(ROOT/'reports/stage5_search_results.json',search)
    write_json(ROOT/'reports/stage5_shortlist.json',{'selected':list(selected.values()),'ranked_eligible_names':[r['spec']['name'] for r in ranked]})
    write_json(ROOT/'reports/stage5_domain_results.json',domains); write_json(ROOT/'reports/stage5_hard_negative_results.json',hard)
    write_json(ROOT/'reports/stage5_generalization.json',general); write_json(ROOT/'reports/stage5_v1_protection.json',protection)
    print(json.dumps({'best':all_results and max(all_results,key=lambda r:r['validation']['macro_f1'])['spec']['name'],'protection':protection,'seconds':search['training_seconds']}),flush=True)

if __name__=='__main__': main()
