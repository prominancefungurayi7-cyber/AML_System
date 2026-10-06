"""Stage 12 descriptive helpers; frozen development inputs only."""
import csv,json
from collections import Counter
import numpy as np
from sklearn.metrics import roc_auc_score
from stage10a_contract import FEATURES,NAMES
from stage11_protection import ROOT,sha,snapshot as prior_snapshot,compare
from run_stage11 import FAMILIES,metrics,recall_slice,fpr_slice

REFERENCE='s11_09_hist_gradient_boosting'
SEEDS=[20260928,20260929,20260930,20261001,20261002]
MARKERS=[i for i,f in enumerate(FEATURES) if f[7] is not None]

def snapshot():
    out=prior_snapshot()
    directories=['ml_v3/models/stage11_candidates']
    for rel in directories:
        for p in (ROOT.parent/rel).rglob('*'):
            if p.is_file(): out['files'][p.relative_to(ROOT.parent).as_posix()]=sha(p)
    for folder,patterns in [('reports',['stage11_*','V3_STAGE11*']),('src',['*stage11*.py']),('tests',['*stage11*.py'])]:
        for pattern in patterns:
            for p in (ROOT/folder).glob(pattern):
                if p.is_file(): out['files'][p.relative_to(ROOT.parent).as_posix()]=sha(p)
    out['scope']+=directories+['ml_v3/reports: stage11_* and V3_STAGE11*','ml_v3/src and tests: *stage11*.py']
    return out

def write(path,value):
    def clean(v):
        if isinstance(v,dict): return {str(k):clean(x) for k,x in v.items()}
        if isinstance(v,(list,tuple)): return [clean(x) for x in v]
        if isinstance(v,np.ndarray): return clean(v.tolist())
        if isinstance(v,np.generic): return clean(v.item())
        return v
    payload=json.dumps(clean(value),indent=2,sort_keys=True,allow_nan=False)+'\n'
    tmp=path.with_suffix('.json.tmp'); tmp.write_text(payload,encoding='utf-8',newline='\n'); tmp.replace(path)

def stats(values,marker=None):
    values=np.asarray(values,dtype=float)
    mask=np.zeros(len(values),dtype=bool) if marker is None else values==marker
    available=values[~mask]
    out={'support':len(values),'available_count':len(available),'missing_count':int(mask.sum()),
         'missing_rate':float(mask.mean()) if len(mask) else None,'availability_rate':float((~mask).mean()) if len(mask) else None}
    if len(available):
        q=np.quantile(available,[0,.05,.25,.5,.75,.95,1])
        out.update(dict(zip(('min','q05','q25','median','q75','q95','max'),map(float,q))))
        out.update(mean=float(available.mean()),std=float(available.std()))
    return out

def distributions(x,mask):
    return {f[0]:stats(x[mask,i],f[7]) for i,f in enumerate(FEATURES)}

def metadata(part,ids,y):
    assert part in ('train','validation')
    folder=ROOT/'data/development'/part
    with (folder/'ground_truth_v3.csv').open(encoding='utf-8',newline='') as stream:
        byid={r['transaction_id']:r for r in csv.DictReader(stream)}
    rows=[dict(byid[i]) for i in ids]
    assert set(byid)==set(ids)
    assert np.array_equal(y,np.array([int(r['decision_point_target']) for r in rows]))
    evidence=[set(filter(None,r['evidence_families'].split(';'))) for r in rows]
    assert all(bool(e)==bool(t) for e,t in zip(evidence,y))
    family={k:np.array([v in e for e in evidence]) for k,v in FAMILIES.items()}
    domains={d:np.logical_or.reduce([family[p+str(i)] for i in range(1,5)]) for p,d in [('S','structuring'),('N','network'),('A','agent')]}
    multiplicity=sum(v.astype(int) for v in domains.values())
    exclusive={d+'_'+kind:mask & ((multiplicity==1) if kind=='only' else (multiplicity>1)) for d,mask in domains.items() for kind in ('only','overlap')}
    normals={key:np.array([t==0 and (r['origin_cohort']=='routine' if key=='routine' else r['origin_cohort']=='campaign_member' if key=='campaign_member_target0' else r['scenario_family']==key) for r,t in zip(rows,y)]) for key in ['routine','campaign_member_target0']+[f'H{i}' for i in range(1,9)]}
    plans=json.loads((folder/'episode_plans.json').read_text())['episodes']
    index={tid:i for i,tid in enumerate(ids)}
    episode={}; position={}
    for plan in plans:
        tids=sorted([str(tid) for tid in plan['transaction_ids'] if str(tid) in index],key=index.get)
        for j,tid in enumerate(tids,1): episode[tid]=plan; position[tid]=j
    # Only these two observable fields are projected for error diagnostics.
    with (folder/'transactions.csv').open(encoding='utf-8',newline='') as stream:
        observable={r['transaction_id']:(r['transaction_type'],r['channel']) for r in csv.DictReader(stream)}
    for i,r in enumerate(rows):
        tid=r['transaction_id']; p=episode.get(tid,{})
        r['recipe']=str(p.get('pattern','not recorded')); r['episode_position']=position.get(tid)
        r['strength']=r['scenario_strength'] or 'not recorded'
        r['transaction_type'],r['channel']=observable[tid]
        r['domain_count']=int(multiplicity[i]); r['family_count']=len(evidence[i])
        onset=r['own_family_onset_transaction_id']
        r['relative_own_onset_position']=position[tid]-position[onset] if onset in position and tid in position else None
        r['onset_scope']='Own private recipe onset only; not universal onset for every active family.'
    return dict(rows=rows,evidence=evidence,family=family,domain=domains,exclusive=exclusive,normal=normals)

def evaluate(xt,yt,xv,yv,pt,pv,meta):
    pred=pv>=.5
    return {'train':metrics(yt,pt),'validation':metrics(yv,pv),
            'domains':{k:recall_slice(v,pred) for k,v in meta['domain'].items()},
            'families':{k:recall_slice(v,pred) for k,v in meta['family'].items()},
            'normal_fpr':{k:fpr_slice(v,pred) for k,v in meta['normal'].items()},
            'domain_independence':{k:dict(**recall_slice(v,pred),low_support=bool(v.sum()<30)) for k,v in meta['exclusive'].items()}}

def dependence(full,removed):
    delta={k:removed['validation'][k]-full['validation'][k] for k in ('macro_f1','suspicious_precision','suspicious_recall','suspicious_f1','average_precision','roc_auc','false_positive_rate')}
    index=max(0.,*[-delta[k] for k in ('macro_f1','suspicious_recall','suspicious_f1','average_precision')],delta['false_positive_rate'])
    category='LOW' if index<.02 else 'MODERATE' if index<.05 else 'HIGH' if index<.15 else 'EXTREME'
    return dict(classification=category,dependence_index=index,metric_deltas=delta,
         domain_deltas={k:removed['domains'][k]['recall']-v['recall'] if v['recall'] is not None else None for k,v in full['domains'].items()},
         family_deltas={k:removed['families'][k]['recall']-v['recall'] if v['recall'] is not None else None for k,v in full['families'].items()},
         normal_fpr_deltas={k:removed['normal_fpr'][k]['false_positive_rate']-v['false_positive_rate'] if v['false_positive_rate'] is not None else None for k,v in full['normal_fpr'].items()})

def group_comparison(x,positive_group,negative_group):
    # Positive/negative here identify diagnostic groups, not model labels.
    a=distributions(x,positive_group); b=distributions(x,negative_group); contrasts={}
    for n in NAMES:
        av,bv=a[n],b[n]
        effect=None
        if av['available_count'] and bv['available_count']:
            scale=((av['std']**2+bv['std']**2)/2)**.5
            effect=(av['mean']-bv['mean'])/scale if scale else (0. if av['mean']==bv['mean'] else None)
        contrasts[n]={'standardized_mean_difference':effect,
                      'missing_rate_difference':av['missing_rate']-bv['missing_rate'] if av['support'] and bv['support'] else None}
    ranked=sorted(contrasts,key=lambda n:abs(contrasts[n]['standardized_mean_difference'] or 0.),reverse=True)
    return {'first_group':a,'second_group':b,'contrasts':contrasts,'features_ranked_by_absolute_standardized_mean_difference':ranked,
            'caveat':'Observed-value moments exclude column markers. Standardized mean differences are unadjusted associations, sensitive to outliers; overlapping/correlated features are not independent causal evidence.'}

def categories(meta,mask,pred,fields):
    out={}
    for field in fields:
        values=[str(r.get(field)) if r.get(field) is not None else 'not recorded' for r in meta['rows']]
        groups={}
        for value in sorted({v for v,m in zip(values,mask) if m}):
            selected=mask & np.array([v==value for v in values]); n=int(selected.sum()); hit=int(pred[selected].sum())
            groups[value]={'support':n,'predicted_positive':hit,'predicted_negative':n-hit,'positive_prediction_rate':hit/n if n else None}
        out[field]=groups
    return out

def error_diagnosis(x,y,p,meta,code):
    pred=p>=.5; mask=meta['family'][code]
    meta=dict(meta,rows=[dict(r,diagnosed_family_onset_position=r['relative_own_onset_position'] if r['scenario_family']==FAMILIES[code] else None) for r in meta['rows']])
    tp=mask&pred; fn=mask&~pred
    relevant=list(range(10,20))+[0,29,30,31] if code=='N3' else [20,21,22,23,24,25,26,27,28,31]
    out={'family':code,'support':int(mask.sum()),'tp':int(tp.sum()),'fn':int(fn.sum()),
         'feature_comparison':group_comparison(x,tp,fn),
         'recommended_feature_views':[NAMES[i] for i in relevant],
         'score_distributions':{'TP':stats(p[tp]),'FN':stats(p[fn])},
         'metadata_categories':categories(meta,mask,pred,['origin_cohort','scenario_family','strength','recipe','domain_count','family_count','episode_position','diagnosed_family_onset_position','transaction_type','channel']),
         'family_overlap':{k:recall_slice(mask&v,pred) for k,v in meta['family'].items()},
         'domain_overlap':{k:recall_slice(mask&v,pred) for k,v in meta['exclusive'].items()},
         'rows':[dict(transaction_id=r['transaction_id'],prediction=int(pred[i]),score=float(p[i]),
                     features={NAMES[j]:float(x[i,j]) for j in relevant},
                     evidence_families=sorted(meta['evidence'][i]),strength=r['strength'],recipe=r['recipe'],
                     episode_position=r['episode_position'],diagnosed_family_onset_position=r['diagnosed_family_onset_position']) for i,r in enumerate(meta['rows']) if mask[i]],
         'onset_limit':'Own-family onset position is only interpreted where the private scenario family matches the diagnosed family; metadata is descriptive, never model input.'}
    if code=='N3':
        out['path_length_strata']={str(k):recall_slice(mask&(x[:,16]==k),pred) for k in range(6)}
        out['cold_history']={n:recall_slice(mask&(x[:,i]<28),pred) for i,n in [(29,NAMES[29]),(30,NAMES[30])]}
    else:
        out['baseline_availability']={label:recall_slice(mask&(x[:,28]==-3 if label=='missing' else x[:,28]!=-3),pred) for label in ('missing','observed')}
        out['other_agent_overlap']=recall_slice(mask&(meta['family']['A1']|meta['family']['A2']|meta['family']['A3']),pred)
        out['no_other_agent_family']=recall_slice(mask&~(meta['family']['A1']|meta['family']['A2']|meta['family']['A3']),pred)
        out['hard_H8_similarity']=group_comparison(x,fn,meta['normal']['H8'])
    return out
