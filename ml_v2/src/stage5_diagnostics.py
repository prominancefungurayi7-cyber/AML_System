"""Train/Validation feature-group ablation for Stage 5 diagnosis only."""
from __future__ import annotations
import json, time
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from contracts import ROOT,write_json
from feature_pipeline import FEATURE_NAMES
from model_metrics import metrics,positive_recall_slices,false_positive_slices
from train_candidates import load_matrix,validation_metadata

GROUPS={'structuring':[i for i,n in enumerate(FEATURE_NAMES) if n.startswith('structuring_')],
        'network':[i for i,n in enumerate(FEATURE_NAMES) if n.startswith('network_')],
        'agent':[i for i,n in enumerate(FEATURE_NAMES) if n.startswith('agent_')]}

def main():
    if [len(GROUPS[x]) for x in ('structuring','network','agent')]!=[6,10,14]: raise ValueError('Frozen feature groups changed')
    Xtr,ytr,_=load_matrix('train'); Xv,yv,ids=load_matrix('validation'); meta=validation_metadata(ids)
    out={'purpose':'diagnostic-only; no feature change or production classifier','groups':{},'seed':20260921,'threshold':.5}
    for name,columns in {**GROUPS,'all_30':list(range(30))}.items():
        start=time.perf_counter(); model=HistGradientBoostingClassifier(learning_rate=.05,max_iter=240,max_leaf_nodes=15,max_depth=5,min_samples_leaf=60,l2_regularization=5,random_state=20260921)
        weights=np.where(ytr==1,3.0,1.0); model.fit(Xtr[:,columns],ytr,sample_weight=weights)
        tr=metrics(ytr,model.predict_proba(Xtr[:,columns])[:,1]); pv=model.predict_proba(Xv[:,columns])[:,1]; va=metrics(yv,pv); pred=(pv>=.5).astype(np.uint8)
        out['groups'][name]={'feature_names':[FEATURE_NAMES[i] for i in columns],'train':tr,'validation':va,
            'domain_recall':positive_recall_slices(yv,pred,meta,'primary_domain',['structuring','network','agent']),
            'hard_negative_fpr':false_positive_slices(yv,pred,meta,['routine','H1','H7']),
            'training_seconds':time.perf_counter()-start}
        print(name,va['macro_f1'],va['average_precision'],flush=True)
    write_json(ROOT/'reports/stage5_feature_domain_diagnostics.json',out)
if __name__=='__main__': main()
