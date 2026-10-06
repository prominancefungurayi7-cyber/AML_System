"""Stage 14 diagnostics. Observable primitives never become model columns."""
import csv, json
from collections import defaultdict
from statistics import median
import numpy as np
from scipy.stats import spearmanr, pearsonr
from sklearn.metrics import roc_auc_score, average_precision_score
from stage10a_contract import NAMES, FEATURES
from stage10a_pipeline import prepare, DAY
from stage12_robustness import stats, write, metadata, evaluate
from stage13_robustness_improvement import snapshot as previous_snapshot
from stage11_protection import ROOT, sha, compare

R=ROOT/'reports'; M=ROOT/'models/stage14_diagnostics'; E=ROOT/'evidence/stage14'
SEED=20260928

def read(stage,name):
    return json.loads((R/f'stage{stage}_{name}.json').read_text(encoding='utf-8'))

def save(name,value): write(R/f'stage14_{name}.json',value)

def snapshot():
    result=previous_snapshot()
    for folder,patterns in [('reports',('stage13_*','V3_STAGE13*')),('src',('*stage13*.py',)),('tests',('*stage13*.py',))]:
        for pattern in patterns:
            for p in (ROOT/folder).glob(pattern):
                if p.is_file(): result['files'][p.relative_to(ROOT.parent).as_posix()]=sha(p)
    for rel in ('models/stage13_candidates','evidence/stage13'):
        for p in (ROOT/rel).rglob('*'):
            if p.is_file(): result['files'][p.relative_to(ROOT.parent).as_posix()]=sha(p)
    # Explicit sources inspected for this diagnosis, including the inherited materializer.
    for rel in ('ml_v2/src/dataset_generator.py','ml_v3/src/generate_v3.py','ml_v3/src/reference_evaluator.py','ml_v3/src/reference.py'):
        result['files'][rel]=sha(ROOT.parent/rel)
    result['scope']+=['Stage 13 report/source/test patterns and isolated model/evidence directories','explicit development generator and evaluator source files']
    return result

def summary(values,marker=None):
    out=stats(values,marker)
    a=np.asarray(values); a=a if marker is None else a[a!=marker]
    out['q99']=float(np.quantile(a,.99)) if len(a) else None
    return out

def power(y,s):
    y=np.asarray(y); s=np.asarray(s)
    out={'support':len(y),'positive':int(y.sum()),'negative':int(len(y)-y.sum()),'prevalence':float(y.mean()) if len(y) else None}
    out.update(roc_auc=float(roc_auc_score(y,s)) if len(np.unique(y))==2 else None,
               average_precision=float(average_precision_score(y,s)) if len(np.unique(y))==2 else None)
    return out

def slices(y,m):
    return dict(overall=np.ones(len(y),bool),target0=y==0,target1=y==1,
                agent_only=m['exclusive']['agent_only'],multi_domain=sum(v.astype(int) for v in m['domain'].values())>1,
                **m['normal'],**{k:m['family'][k] for k in ('A1','A2','A3','A4')})

def correlation(a,b):
    if len(a)<2 or np.std(a)==0 or np.std(b)==0: return {'support':len(a),'pearson':None,'spearman':None}
    return {'support':len(a),'pearson':float(pearsonr(a,b).statistic),'spearman':float(spearmanr(a,b).statistic)}

def overlap(a,b):
    a=np.asarray(a); b=np.asarray(b); a=a[a!=-1]; b=b[b!=-1]
    if not len(a) or not len(b): return {'positive_available':len(a),'negative_available':len(b)}
    aq=np.quantile(a,[.05,.95]); bq=np.quantile(b,[.05,.95])
    lo=max(a.min(),b.min()); hi=min(a.max(),b.max())
    return dict(positive_available=len(a),negative_available=len(b),positive_mean=float(a.mean()),negative_mean=float(b.mean()),
        positive_in_negative_middle90=float(np.mean((a>=bq[0])&(a<=bq[1]))),negative_in_positive_middle90=float(np.mean((b>=aq[0])&(b<=aq[1]))),
        range_overlap=[float(lo),float(hi)] if lo<=hi else None,
        positive_at_or_above_existing_A1_ratio=float(np.mean(a>=1.5)),negative_at_or_above_existing_A1_ratio=float(np.mean(b>=1.5)),
        rank_auc=power(np.r_[np.ones(len(a)),np.zeros(len(b))],np.r_[a,b])['roc_auc'])

PRIMITIVES=['growth','agent_observation_age_days','baseline_services','recent_distinct','baseline_median','new_distinct','novelty',
            'eligible_feature','implemented_ratio','implemented_eligible','implemented_A1','written_A1','other_A1_gates',
            'bucket1','bucket2','bucket3','bucket4']

def primitives(raw):
    """Independently reconstruct only agent/A1 diagnostics; never call target materialization."""
    hist=defaultdict(list); first={}; ids=[]; output=[]
    for e in prepare(raw):
        aid=e['agent_id']; t=e['t']; values=[-1.,-1.,0.,0.,0.,0.,-1.,0.,-1.,0.,0.,0.,0.,0.,0.,0.,0.]
        if aid:
            h=hist[aid]
            r=[x for x in h if t-7*DAY<x['t']]+[e]
            b=[x for x in h if t-35*DAY<x['t']<=t-7*DAY]
            buckets=[len({x['serviced_wallet'] for x in b if t-(i+1)*7*DAY<x['t']<=t-i*7*DAY}) for i in range(1,5)]
            wallets={x['serviced_wallet'] for x in r}; old={x['serviced_wallet'] for x in b}
            n=len(wallets); new=len(wallets-old); med=median(buckets)
            age=(t-first[aid]).total_seconds()/86400 if aid in first else 0.
            ready=aid in first and first[aid]<=t-35*DAY and len(b)>=12
            growth=n/max(1,med) if ready else -1.
            other=n>=6 and new>=4 and new/n>=.5
            # Frozen generator imports reference_evaluator.py: closed lower bounds,
            # timestamp-only recent upper bound, and only 28d observed coverage.
            ir=[x for x in h if t-7*DAY<=x['t']<t]+[e]
            ib=[x for x in h if t-35*DAY<=x['t']<t-7*DAY]
            ibuckets=[{x['serviced_wallet'] for x in h if t-7*i*DAY<=x['t']<t-7*(i-1)*DAY} for i in range(2,6)]
            iw={x['serviced_wallet'] for x in ir}; inu=len(iw-set().union(*ibuckets))
            imed=median([len(v) for v in ibuckets]); ig=len(iw)/max(1,imed)
            iready=aid in first and first[aid]<=t-28*DAY and len(ib)>=12
            ihit=iready and len(iw)>=6 and inu>=4 and inu/len(iw)>=.5 and ig>=1.5
            values=[growth,age,len(b),n,med,new,new/n,float(ready),ig,float(iready),float(ihit),float(ready and other and growth>=1.5),float(other),*buckets]
            hist[aid].append(e); first.setdefault(aid,t)
        ids.append(str(e['id'])); output.append(values)
    return ids,np.asarray(output,float)

def grid_bins(x,marker):
    a=x if marker is None else x[x!=marker]
    return list(map(float,np.unique(np.quantile(a,[.25,.5,.75])))) if len(a) else []

def grid_codes(x,edges,marker):
    z=np.searchsorted(edges,x,side='right')
    if marker is not None: z=np.where(x==marker,-1,z)
    return z
