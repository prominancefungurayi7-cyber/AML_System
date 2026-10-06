"""Fixed-threshold binary metrics and development diagnostic slices."""
import numpy as np
from sklearn.metrics import (accuracy_score,balanced_accuracy_score,f1_score,precision_score,recall_score,
                             roc_auc_score,average_precision_score,confusion_matrix)

def metrics(y,prob,threshold=.5):
    y=np.asarray(y); prob=np.asarray(prob); pred=(prob>=threshold).astype(np.uint8)
    tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
    return {'accuracy':float(accuracy_score(y,pred)),'balanced_accuracy':float(balanced_accuracy_score(y,pred)),
        'macro_f1':float(f1_score(y,pred,average='macro')),'suspicious_precision':float(precision_score(y,pred,zero_division=0)),
        'suspicious_recall':float(recall_score(y,pred,zero_division=0)),'suspicious_f1':float(f1_score(y,pred,zero_division=0)),
        'normal_recall':float(recall_score(y,pred,pos_label=0,zero_division=0)),'roc_auc':float(roc_auc_score(y,prob)),
        'average_precision':float(average_precision_score(y,prob)),'false_positive_rate':float(fp/(fp+tn)),
        'confusion_matrix':[[int(tn),int(fp)],[int(fn),int(tp)]],'threshold':float(threshold)}

def positive_recall_slices(y,pred,metadata,key,values):
    out={}
    for value in values:
        idx=[i for i,m in enumerate(metadata) if y[i]==1 and m[key]==value]
        out[value]={'count':len(idx),'true_positives':int(sum(pred[i]==1 for i in idx)),
                    'recall':float(sum(pred[i]==1 for i in idx)/len(idx)) if idx else None}
    return out

def false_positive_slices(y,pred,metadata,values):
    out={}
    for value in values:
        idx=[i for i,m in enumerate(metadata) if y[i]==0 and m['normal_family']==value]
        fp=int(sum(pred[i]==1 for i in idx)); out[value]={'count':len(idx),'false_positives':fp,'false_positive_rate':float(fp/len(idx)) if idx else None}
    return out
