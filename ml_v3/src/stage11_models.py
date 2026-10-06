"""Prespecified compact search; no adaptive Validation-driven expansion."""
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, HistGradientBoostingClassifier

SEED=20260928
THREADS=2

def configurations(xgb_available=True):
    base={
      'logistic':dict(C=1.,solver='lbfgs',max_iter=4000,tol=1e-5),
      'random_forest':dict(n_estimators=200,max_depth=12,min_samples_leaf=5,max_features=.7,n_jobs=THREADS),
      'gradient_boosting':dict(n_estimators=150,learning_rate=.07,max_depth=3,min_samples_leaf=10,subsample=1.),
      'hist_gradient_boosting':dict(max_iter=200,learning_rate=.07,max_leaf_nodes=31,max_depth=6,min_samples_leaf=20,l2_regularization=1.,early_stopping=False),
      'xgboost':dict(n_estimators=200,learning_rate=.07,max_depth=4,min_child_weight=5,subsample=.8,colsample_bytree=.8,reg_alpha=.05,reg_lambda=3.,tree_method='hist',n_jobs=THREADS,eval_metric='logloss')}
    if not xgb_available: del base['xgboost']
    tweaks={'random_forest':dict(n_estimators=250,max_depth=16,min_samples_leaf=10),
            'gradient_boosting':dict(n_estimators=200,max_depth=2,learning_rate=.05),
            'hist_gradient_boosting':dict(max_iter=250,max_leaf_nodes=15,max_depth=5,l2_regularization=3.),
            'xgboost':dict(n_estimators=250,max_depth=3,min_child_weight=10,reg_lambda=5.)}
    results=[]
    # First five fits are one simple unweighted baseline per family.
    for round_index in range(6):
        for family,params in base.items():
            params=dict(params); mode='robust' if family=='logistic' else 'raw'; weight='none'
            if round_index==1: weight='moderate'
            if round_index==2: weight='balanced'
            if family=='logistic':
                if round_index==3: params['C']=.1
                if round_index==4: params['C']=10.
                if round_index==5: mode='robust_sentinel'
            else:
                if round_index==3: mode='clipped'
                if round_index==4: mode='imputed'
                if round_index==5: params.update(tweaks[family])
            results.append(dict(name=f's11_{len(results)+1:02d}_{family}',family=family,preprocessing=mode,weight=weight,
                                phase='initial baseline' if round_index==0 else 'compact comparison',params=params))
    return results

def build(spec,balanced_ratio):
    params=dict(spec['params']); params['random_state']=SEED
    family=spec['family']
    if family=='logistic': return LogisticRegression(**params)
    if family=='random_forest':
        if spec['weight']=='balanced': params['class_weight']='balanced_subsample'
        return RandomForestClassifier(**params)
    if family=='gradient_boosting': return GradientBoostingClassifier(**params)
    if family=='hist_gradient_boosting': return HistGradientBoostingClassifier(**params)
    if family=='xgboost':
        from xgboost import XGBClassifier
        params['scale_pos_weight']={'none':1.,'moderate':1.5,'balanced':balanced_ratio}[spec['weight']]
        return XGBClassifier(**params)
    raise ValueError(family)

def sample_weights(spec,y):
    import numpy as np
    if spec['family']=='xgboost' or spec['weight']=='none' or (spec['family']=='random_forest' and spec['weight']=='balanced'): return None
    if spec['weight']=='moderate': return np.where(y==1,1.5,1.)
    counts=np.bincount(y); return len(y)/(2*counts[y])
