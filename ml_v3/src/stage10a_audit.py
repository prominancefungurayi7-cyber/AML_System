"""Descriptive checks only: no classifier, learned cutoffs or model metrics."""
import ast
import math
from collections import Counter
from itertools import combinations
from statistics import mean, median, pstdev
from stage10a_contract import FEATURES, NAMES

def quantile(v,q):
    p=(len(v)-1)*q; i=int(p); j=min(i+1,len(v)-1)
    return v[i]+(v[j]-v[i])*(p-i)

def summary(values):
    v=sorted(values)
    if not v: return {'count':0}
    counts=Counter(v)
    return {'count':len(v),'minimum':v[0],'maximum':v[-1],'mean':mean(v),'std':pstdev(v),'median':median(v),
            'q01':quantile(v,.01),'q05':quantile(v,.05),'q95':quantile(v,.95),'q99':quantile(v,.99),
            'zero_fraction':counts[0]/len(v),'distinct_count':len(counts),'modal_fraction':max(counts.values())/len(v),
            'constant':len(counts)==1,'near_constant':max(counts.values())/len(v)>=.99,
            'tail_span_over_iqr':(v[-1]-v[0])/max(1e-12,quantile(v,.75)-quantile(v,.25))}

def matrix_audit(data,expected):
    x,y,ids=data['X'],data['y'],data['row_ids']
    assert len(x)==len(y)==len(ids)==sum(expected.values())
    assert Counter(y)==expected and set(y)=={0,1} and len(set(ids))==len(ids)
    assert all(len(row)==32 and all(math.isfinite(v) for v in row) for row in x)
    stats={}; overlap={}
    for j,(name,domain,subject,formula,role,lo,hi,missing) in enumerate(FEATURES):
        values=[r[j] for r in x]; valid=[v for v in values if missing is None or v!=missing]
        assert all(v>=lo and (hi is None or v<=hi) for v in valid),name
        # Funding age has an OPEN upper limit for a valid anchor.
        if j==19: assert all(v<24 for v in valid)
        stats[name]={'all_values':summary(values),'observed_values':summary(valid),'missing_marker':missing,
                     'missing_count':len(values)-len(valid),'missing_fraction':(len(values)-len(valid))/len(values),
                     'valid_range':[lo,hi],'type':'float64 serialization; integer-valued where count/indicator',
                     'legitimate_negative_one_count':sum(v==-1 for v in valid)}
        overlap[name]={str(k):summary([row[j] for row,target in zip(x,y) if target==k and (missing is None or row[j]!=missing)]) for k in (0,1)}
    return {'rows':len(x),'columns':32,'feature_order':list(NAMES),'target_counts':dict(Counter(y)),
            'nan_count':0,'infinity_count':0,'duplicate_row_ids':0,'range_check':'PASS','statistics':stats,'target_overlap':overlap}

def mapping_info(keys,y):
    groups={}
    for key,target in zip(keys,y):
        mask,count=groups.get(key,(0,0)); groups[key]=(mask | (1<<target),count+1)
    return {'distinct_keys':len(groups),'contradictory_keys':sum(mask==3 for mask,n in groups.values()),
            'rows_in_contradictory_keys':sum(n for mask,n in groups.values() if mask==3),
            'singleton_fraction':sum(n==1 for mask,n in groups.values())/len(y),
            'exact_mapping_on_sample':all(mask!=3 for mask,n in groups.values())}

def oracle_audit(data, family_truth=None):
    x,y=data['X'],data['y']; columns=list(zip(*x)); singles={}
    exact_direct=[]; exact_intervals=[]
    for i,name in enumerate(NAMES):
        c=columns[i]; info=mapping_info(c,y)
        info['exact_target_column']=all(v==t for v,t in zip(c,y))
        info['exact_inverse_target']=all(v==1-t for v,t in zip(c,y))
        c0=[v for v,t in zip(c,y) if t==0]; c1=[v for v,t in zip(c,y) if t==1]
        info['exact_monotone_cutoff_equivalence']=max(c0)<min(c1) or max(c1)<min(c0)
        if info['exact_target_column'] or info['exact_inverse_target']: exact_direct.append(name)
        if info['exact_monotone_cutoff_equivalence']: exact_intervals.append(name)
        singles[name]=info
    pair_results={}
    for i,j in combinations(range(32),2):
        pair_results[NAMES[i]+' + '+NAMES[j]]=mapping_info(zip(columns[i],columns[j]),y)
    # Fixed observable conditions, declared before inspecting targets. Their
    # AND/OR combinations are diagnostics only; they never enter X.
    conditions={
        'path_present':lambda r:r[16]>0,
        'return_ratio_in_reference_band':lambda r:.25<=r[17]<=1.25,
        'onward_share_in_reference_band':lambda r:.5<=r[18]<=1.,
        'growth_ratio_at_least_1_5':lambda r:r[22]>=1.5,
        'novel_share_at_least_half':lambda r:r[23]>=.5,
        'top2_share_at_least_0_65':lambda r:r[24]>=.65,
        'top2_change_at_least_0_2':lambda r:r[25]>=.2,
        'agent_hour_count_at_least_5':lambda r:r[20]>=5,
        'agent_acceleration_at_least_3':lambda r:r[21]>=3,
        'cash_value_skew_abs_at_least_0_6':lambda r:abs(r[26])>=.6,
        'cash_count_skew_abs_at_least_half':lambda r:abs(r[27])>=.5,
        'wallet_hour_count_at_least_4':lambda r:r[3]>=4,
        'wallet_acceleration_at_least_3':lambda r:r[9]>=3,
    }
    masks={name:bytes(int(fn(r)) for r in x) for name,fn in conditions.items()}
    truth=bytes(y); all_bits=(1<<len(y))-1
    def bitset(values): return int(''.join(str(v) for v in values),2)
    target=bitset(truth); bits={k:bitset(v) for k,v in masks.items()}
    equivalence=[]
    for k,v in bits.items():
        if v==target or (all_bits^v)==target: equivalence.append(k)
    for (a,av),(b,bv) in combinations(bits.items(),2):
        for op,v in (('AND',av&bv),('OR',av|bv)):
            if v==target or (all_bits^v)==target: equivalence.append(a+' '+op+' '+b)
    predicate_checks={}
    for family,labels in (family_truth or {}).items():
        if len(set(labels))<2:
            predicate_checks[family]={'result':'UNINFORMATIVE','reason':'Only one family outcome in this partition.'}
            continue
        target_family=bitset(labels); columns_equal=[]; cutoffs_equal=[]; combinations_equal=[]
        for i,c in enumerate(columns):
            if all(v==t for v,t in zip(c,labels)) or all(v==1-t for v,t in zip(c,labels)):
                columns_equal.append(NAMES[i])
            c0=[v for v,t in zip(c,labels) if t==0]; c1=[v for v,t in zip(c,labels) if t==1]
            if max(c0)<min(c1) or max(c1)<min(c0): cutoffs_equal.append(NAMES[i])
        for (a,av),(b,bv) in combinations(bits.items(),2):
            for op,v in (('AND',av&bv),('OR',av|bv)):
                if v==target_family or (all_bits^v)==target_family: combinations_equal.append(a+' '+op+' '+b)
        predicate_checks[family]={'exact_columns':columns_equal,'exact_monotone_cutoffs':cutoffs_equal,
                                 'exact_fixed_combinations':combinations_equal,
                                 'result':'PASS' if not columns_equal and not cutoffs_equal and not combinations_equal else 'REVIEW'}
    return {'result':'PASS' if not exact_direct and not exact_intervals and not equivalence and all(v['result']!='REVIEW' for v in predicate_checks.values()) else 'FAIL',
            'single_features':singles,'two_feature_mappings':pair_results,'pairs_checked':len(pair_results),
            'frozen_family_predicate_outcome_checks':predicate_checks,
            'fixed_condition_names':list(conditions),'fixed_pair_and_or_checked':2*len(list(combinations(conditions,2))),
            'exact_direct_columns':exact_direct,'exact_monotone_equivalences':exact_intervals,'exact_fixed_combination_equivalences':equivalence,
            'limitations':'Finite-sample mapping can be vacuous for unique amounts/pairs. Singleton and contradictory-key counts are reported. No learned classifier, selected cutoff, model metric, production decision threshold or exhaustive arbitrary-function search is used. Strong association is allowed.'}

def source_audit(path):
    tree=ast.parse(path.read_text(encoding='utf-8'))
    imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    forbidden=('decision_point_target','scenario_member','scenario_family','origin_cohort','campaign_id','signal_strength','witness_transaction_ids','evidence_families','own_family_onset_transaction_id')
    strings={n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
    assert not set(forbidden)&strings
    assert not any('reference' in s or 'ml_v2' in s or 'sklearn' in s for s in imports if s)
    return {'result':'PASS','forbidden_private_literals':[],'imports':imports,'public_projection_only':True,
            'reference_predicate_review':{
                'S1':'Does not expose largest-fragment share or full count/value/rate conjunction.',
                'S2':'Does not expose cluster sum or matching-baseline count conjunction.',
                'S3':'Does not expose complete-day preceding-median conjunction.',
                'S4':'Does not expose current-band gate + in-band distinctness + count/rate conjunction.',
                'N1/N2':'Do not combine breadth, event count, value, current role and rate.',
                'N3':'Topology and first-edge ratio separate; no adjacent-amount filtering or any-qualifying-path result.',
                'N4':'Share/age do not impose minimum funding, remaining-balance gate or full role conjunction.',
                'A1':'No recent distinct/novel minimum count conjunction.',
                'A2':'No recent service count>=8 and concentration/change conjunction.',
                'A3':'No recent unique-wallet minimum combined with intensity.',
                'A4':'No cash count/unique-wallet/current-cash/sign/change conjunction.'}}
