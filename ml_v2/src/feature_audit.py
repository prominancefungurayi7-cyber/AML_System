"""Model-free audit of persisted development feature matrices."""
import csv, json, math, statistics
from collections import Counter
from pathlib import Path
from contracts import ROOT, safe_path
from feature_pipeline import FEATURE_NAMES

def read_partition(folder):
    folder=safe_path(folder)
    with (folder/'X.csv').open(encoding='utf-8',newline='') as f: X=[[float(x) for x in row] for row in csv.reader(f)]
    with (folder/'y.csv').open(encoding='utf-8',newline='') as f: y=[int(row[0]) for row in csv.reader(f)]
    with (folder/'row_ids.csv').open(encoding='utf-8',newline='') as f:
        rows=list(csv.DictReader(f)); ids=[int(r['transaction_id']) for r in rows]
    names=json.loads((folder/'feature_names.json').read_text(encoding='utf-8'))
    return X,y,ids,names

def audit(features_root):
    root=safe_path(features_root); result={'result':'PASS','partitions':{},'failures':[],'warnings':[]}
    for partition,n in [('train',60000),('validation',15000)]:
        X,y,ids,names=read_partition(root/partition)
        def check(ok,name):
            if not ok: result['failures'].append(f'{partition}:{name}')
        check(len(X)==n and all(len(r)==30 for r in X),'shape'); check(len(y)==len(ids)==n,'aligned_rows')
        check(names==FEATURE_NAMES,'feature_order'); check(set(y)<={0,1},'binary_target'); check(len(set(ids))==n,'unique_ids')
        check(ids==sorted(ids),'row_order'); check(all(math.isfinite(v) for row in X for v in row),'finite')
        columns=list(map(list,zip(*X))); summaries=[]; constants=[]; near=[]; shortcuts=[]
        for name,col in zip(names,columns):
            count=Counter(col); mode_value,mode_count=count.most_common(1)[0]
            if len(count)==1: constants.append(name)
            if mode_count/len(col)>=.99: near.append({'feature':name,'value':mode_value,'fraction':mode_count/len(col)})
            normal=[v for v,t in zip(col,y) if t==0]; suspicious=[v for v,t in zip(col,y) if t==1]
            nz0=any(v!=0 for v in normal); nz1=any(v!=0 for v in suspicious)
            supported0={v for v,c in Counter(normal).items() if c>=10}; supported1={v for v,c in Counter(suspicious).items() if c>=10}
            exclusive0=sorted(supported0-supported1); exclusive1=sorted(supported1-supported0)
            shortcut={'feature':name,'nonzero_normal':nz0,'nonzero_suspicious':nz1,
                'nonzero_only_one_class':nz0!=nz1,
                'supported_exact_values_only_normal':exclusive0[:10],'supported_exact_values_only_suspicious':exclusive1[:10],
                'normal':{'min':min(normal),'median':statistics.median(normal),'max':max(normal),'mean':statistics.fmean(normal),'zero_fraction':normal.count(0.0)/len(normal)},
                'suspicious':{'min':min(suspicious),'median':statistics.median(suspicious),'max':max(suspicious),'mean':statistics.fmean(suspicious),'zero_fraction':suspicious.count(0.0)/len(suspicious)}}
            shortcuts.append(shortcut)
            summaries.append({'feature':name,'min':min(col),'max':max(col),'mean':statistics.fmean(col),'median':statistics.median(col),
                              'zero_fraction':col.count(0.0)/len(col),'distinct_values':len(count),'mode':mode_value,'mode_fraction':mode_count/len(col)})
        check(not constants,'constant_features'); check(not any(x['nonzero_only_one_class'] for x in shortcuts),'nonzero_class_shortcut')
        result['partitions'][partition]={'shape':[len(X),30],'target_counts':dict(Counter(y)),'nan_count':sum(math.isnan(v) for row in X for v in row),
            'infinity_count':sum(math.isinf(v) for row in X for v in row),'constant_features':constants,'near_constant_features':near,
            'summary':summaries,'shortcut_diagnostics':shortcuts}
    if result['failures']: result['result']='FAIL'
    return result
