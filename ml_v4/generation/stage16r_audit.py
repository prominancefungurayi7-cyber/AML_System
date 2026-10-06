"""Independent ledger checks and descriptive development diagnostics. No fits."""
from __future__ import annotations
from collections import defaultdict,Counter
import csv
import io
import json
import statistics
import numpy as np
from stage16r_contract import DAY,FAMILIES,validate_event,event_csv,json_bytes
from stage16r_evaluator import replay


def partition_files(events,provenance,populations):
    truth=replay(events)
    scored=[e for e in events if e.time>=42*DAY]
    scored_truth=[t for e,t in zip(events,truth) if e.time>=42*DAY]
    out=io.StringIO(newline=''); writer=csv.writer(out,lineterminator='\n'); writer.writerow(['transaction_id','ground_truth_label'])
    writer.writerows((r['transaction_id'],r['ground_truth_label']) for r in scored_truth)
    files={'warmup_observables.csv':event_csv([e for e in events if e.time<42*DAY]),'transactions.csv':event_csv(scored),'ground_truth.csv':out.getvalue().encode(),'family_evidence.jsonl':b''.join((json.dumps(r,sort_keys=True,separators=(',',':'))+'\n').encode() for r in scored_truth),'private_provenance.json':json_bytes(provenance),'private_population.json':json_bytes(populations)}
    return files,scored_truth


def integrity(events,populations,units):
    wallet_units={w['id']:i for i,pop in enumerate(populations) for w in pop['wallets']}
    agent_units={a['id']:i for i,pop in enumerate(populations) for a in pop['agents']}
    activation={w['id']:w['activation'] for pop in populations for w in pop['wallets']}
    wallet={w:100000000 for w in wallet_units}; electronic={a:200000000 for a in agent_units}; cash=dict(electronic)
    initial=sum(wallet.values())+sum(electronic.values())
    ids=set(); full=set(); previous=None; minimum=100000000
    for e in events:
        validate_event(e)
        if e.transaction_id in ids or e in full: raise AssertionError('Duplicate event or ID')
        if previous is not None and e.key<=previous: raise AssertionError('Unsorted events')
        if not 0<=e.time<222*DAY: raise AssertionError('Time outside horizon')
        if wallet_units[e.sender_wallet]!=wallet_units[e.receiver_wallet]: raise AssertionError('Cross-unit edge')
        if e.agent_id and agent_units[e.agent_id]!=wallet_units[e.serviced_wallet]: raise AssertionError('Cross-unit service')
        if activation[e.sender_wallet]>e.time or activation[e.receiver_wallet]>e.time: raise AssertionError('Pre-activation event')
        previous=e.key; ids.add(e.transaction_id); full.add(e)
        if e.transaction_type=='wallet_to_wallet': wallet[e.sender_wallet]-=e.amount_minor; wallet[e.receiver_wallet]+=e.amount_minor
        elif e.transaction_type=='cash_in': wallet[e.subject]+=e.amount_minor; electronic[e.agent_id]-=e.amount_minor; cash[e.agent_id]+=e.amount_minor
        else: wallet[e.subject]-=e.amount_minor; electronic[e.agent_id]+=e.amount_minor; cash[e.agent_id]-=e.amount_minor
        values=[wallet[e.sender_wallet],wallet[e.receiver_wallet]]+([electronic[e.agent_id],cash[e.agent_id]] if e.agent_id else [])
        if min(values)<0: raise AssertionError('Negative inventory in independent ledger')
        minimum=min(minimum,min(values))
    if sum(wallet.values())+sum(electronic.values())!=initial: raise AssertionError('Electronic value not conserved')
    warm=sum(e.time<42*DAY for e in events)
    assert warm==1200*units and len(events)-warm==5000*units
    assert len(wallet)==100*units and len(electronic)==8*units
    first={}
    for e in events:
        for w in {e.sender_wallet,e.receiver_wallet}: first.setdefault(w,e.time)
    assert all(first[w]==activation[w] for w in wallet if activation[w]>0)
    return {'status':'PASS','scored_events':len(events)-warm,'warmup_events':warm,'wallets':len(wallet),'agents':len(electronic),'minimum_inventory_minor':minimum,'unique_ids':len(ids),'electronic_value_conserved':True,'schema_errors':0,'cross_unit_events':0,'cold_start_first_observation_exact':True}


def a1_primitives(events):
    """Separate reconstruction; does not consume saved truth or evaluator state."""
    first={}; histories=defaultdict(list); answer=[]
    for e in events:
        row={'transaction_id':e.transaction_id,'D':None,'U':None,'novelty':None,'M':None,'growth':None,'age_days':None,'baseline_services':None,'coverage_eligible':False,'baseline_eligible':False,'eligible':False}
        if e.agent_id:
            a=e.agent_id; t=e.time
            hist=histories[a]
            baseline=[(time,w) for time,w in hist if t-35*DAY<time<=t-7*DAY]
            recent={w for time,w in hist if t-7*DAY<time<=t}|{e.serviced_wallet}
            old={w for _,w in baseline}
            weeks=[len({w for time,w in hist if t-(14+7*k)*DAY<time<=t-(7+7*k)*DAY}) for k in range(4)]
            d=len(recent); u=len(recent-old); m=statistics.median(weeks)
            age=(t-first[a])/DAY if a in first else 0
            coverage=a in first and first[a]<=t-35*DAY
            eligible=coverage and len(baseline)>=12
            row.update(D=d,U=u,novelty=u/d,M=m,growth=d/max(1,m) if eligible else None,age_days=age,baseline_services=len(baseline),coverage_eligible=coverage,baseline_eligible=len(baseline)>=12,eligible=eligible)
            first.setdefault(a,t)
            histories[a]=[(time,w) for time,w in hist if time>=t-35*DAY]+[(t,e.serviced_wallet)]
        if e.time>=42*DAY: answer.append(row)
    return answer


def distribution(values):
    valid=np.array([x for x in values if x is not None],dtype=float)
    return {'n':len(values),'available':len(valid),'missing':len(values)-len(valid),'mean':float(valid.mean()) if len(valid) else None,'min':float(valid.min()) if len(valid) else None,'max':float(valid.max()) if len(valid) else None,'quantiles':dict(zip(['p01','p05','p25','p50','p75','p95','p99'],[float(x) for x in np.quantile(valid,[.01,.05,.25,.5,.75,.95,.99])])) if len(valid) else None}


def group_result(indices,y,flags):
    indices=np.array(indices,dtype=int)
    return {'total':len(indices),'target0':int((y[indices]==0).sum()),'target1':int(y[indices].sum()),'positive_fraction':float(y[indices].mean()) if len(indices) else None,'predicates':{f:int(flags[indices,j].sum()) for j,f in enumerate(FAMILIES)},'multi_family':int((flags[indices].sum(axis=1)>1).sum())}


def development_audit(name,events,provenance,populations,truth):
    scored=[e for e in events if e.time>=42*DAY]
    by_id={r['transaction_id']:r for r in provenance}; meta=[by_id[e.transaction_id] for e in scored]
    y=np.array([r['ground_truth_label'] for r in truth],dtype=np.int8)
    flags=np.array([[f in r['families'] for f in FAMILIES] for r in truth],dtype=bool)
    primitives=a1_primitives(events)
    assert len(primitives)==len(truth)
    assert all(p['eligible']==r['eligible']['A1'] for p,r in zip(primitives,truth))
    assert all((p['eligible'] and p['D']>=6 and p['U']>=4 and p['novelty']>=.5 and p['growth']>=1.5)==('A1' in r['families']) for p,r in zip(primitives,truth))
    def subject(e,f):
        return e.agent_id if f.startswith('A') else e.receiver_wallet if f=='N1' else e.subject
    def cluster(i):
        return 'episode:'+str(meta[i]['scenario_id']) if meta[i]['scenario_id'] is not None else f"background:{meta[i]['population_unit']}:{scored[i].time//DAY}"
    family={}
    minimum=1200 if name=='train' else 300
    for j,f in enumerate(FAMILIES):
        indices=np.flatnonzero(flags[:,j]).tolist()
        subjects=Counter(subject(scored[i],f) for i in indices)
        clusters=Counter(cluster(i) for i in indices)
        enough=len(indices)>=minimum and (name=='train' or (len(subjects)>=20 and len(clusters)>=30))
        family[f]={'decision_points':len(indices),'distinct_subjects':len(subjects),'distinct_clusters':len(clusters),'distinct_units':len({meta[i]['population_unit'] for i in indices}),'overlap':{other:int((flags[:,j]&flags[:,k]).sum()) for k,other in enumerate(FAMILIES)},'maximum_subject_share':max(subjects.values())/len(indices) if indices else None,'maximum_cluster_share':max(clusters.values())/len(indices) if indices else None,'minimum_objective':minimum,'status':'PASS' if enough else 'FAIL' if not indices else 'CONDITIONAL'}
    def grouped(key,values=None):
        groups=defaultdict(list)
        for i,row in enumerate(meta): groups[str(row[key])].append(i)
        if values:
            for value in values: groups.setdefault(value,[])
        return {g:group_result(ii,y,flags) for g,ii in sorted(groups.items())}
    hard={g:group_result([i for i,r in enumerate(meta) if r['origin']==g],y,flags) for g in ['H'+str(i) for i in range(1,9)]}
    background=group_result([i for i,r in enumerate(meta) if r['origin']=='background'],y,flags)
    agent_by_id={a['id']:a for pop in populations for a in pop['agents']}
    wallet_by_id={w['id']:w for pop in populations for w in pop['wallets']}
    archetype=grouped('archetype')
    for label,row in archetype.items(): row['agents']=sum(a['archetype']==label for a in agent_by_id.values())
    profile=grouped('profile')
    for label,row in profile.items(): row['wallets']=sum(w['profile']==label for w in wallet_by_id.values())
    positive_agents=Counter(e.agent_id for e,label in zip(scored,y) if label and e.agent_id)
    per_agent={a:group_result([i for i,e in enumerate(scored) if e.agent_id==a],y,flags) for a in agent_by_id}
    def growth_origin(e):
        if not e.agent_id: return False
        a=agent_by_id[e.agent_id]; day=e.time/DAY
        return any(q['start']<=day<=q['end'] for q in a['acquisition']) or any(s['cause'] in (0,4) and s['start']<=day<=s['end'] for s in a['shocks'])
    def boundary(p):
        if not p['eligible']: return False
        gates=[p['D']>=6,p['U']>=4,p['novelty']>=.5,p['growth']>=1.5]
        near=[p['D']==5,p['U']==3,.4<=p['novelty']<.5,1.25<=p['growth']<1.5]
        return sum(gates)==3 and any(n and not g for n,g in zip(near,gates))
    negatives={g:[i for i,r in enumerate(meta) if not y[i] and r['origin']==g] for g in ('H7','H8','background')}
    negatives['legitimate_growth']=[i for i,e in enumerate(scored) if not y[i] and growth_origin(e)]
    negatives['A1_near_boundary']=[i for i,p in enumerate(primitives) if not y[i] and boundary(p)]
    negatives['union']=sorted(set(i for rows in negatives.values() for i in rows))
    positive=np.flatnonzero(flags[:,8]).tolist()
    from sklearn.metrics import roc_auc_score,average_precision_score
    overlap={}
    fields=['D','U','novelty','M','growth','age_days','baseline_services']
    for group,negative in negatives.items():
        pos=[i for i in positive if primitives[i]['eligible']]; neg=[i for i in negative if primitives[i]['eligible']]
        yy=[1]*len(pos)+[0]*len(neg); values=[primitives[i]['growth'] for i in pos+neg]
        metrics={'roc_auc':float(roc_auc_score(yy,values)) if pos and neg else None,'average_precision':float(average_precision_score(yy,values)) if pos and neg else None,'subset_prevalence':len(pos)/(len(pos)+len(neg)) if pos or neg else None}
        low,high=np.quantile([primitives[i]['growth'] for i in neg],[.05,.95]) if neg else (None,None)
        overlap[group]={'A1_support':len(positive),'negative_support':len(negative),'eligible_A1':len(pos),'eligible_negative':len(neg),'negative_high_growth_count':sum(primitives[i]['growth']>=1.5 for i in neg),'A1_in_negative_middle90_fraction':sum(low<=primitives[i]['growth']<=high for i in pos)/len(pos) if pos and neg else None,'metrics':metrics,'A1':{f:distribution([primitives[i][f] for i in positive]) for f in fields},'negative':{f:distribution([primitives[i][f] for i in negative]) for f in fields},'eligibility':{'A1_coverage':sum(primitives[i]['coverage_eligible'] for i in positive),'A1_baseline_count':sum(primitives[i]['baseline_eligible'] for i in positive),'negative_coverage':sum(primitives[i]['coverage_eligible'] for i in negative),'negative_baseline_count':sum(primitives[i]['baseline_eligible'] for i in negative)},'A1_agents':len({scored[i].agent_id for i in pos}),'negative_agents':len({scored[i].agent_id for i in neg})}
        overlap[group]['age_strata']={}
        for lo,hi in [(35,60),(60,90),(90,120),(120,1000)]:
            pp=[i for i in pos if lo<=primitives[i]['age_days']<hi]; nn=[i for i in neg if lo<=primitives[i]['age_days']<hi]
            values=[primitives[i]['growth'] for i in pp+nn]; labels=[1]*len(pp)+[0]*len(nn)
            overlap[group]['age_strata'][f'{lo}..{hi}']={'positive':len(pp),'negative':len(nn),'roc_auc':float(roc_auc_score(labels,values)) if pp and nn else None,'average_precision':float(average_precision_score(labels,values)) if pp and nn else None}
    # Descriptive grouping only. Unique opaque IDs are not fitted as predictors.
    shortcut={}
    columns={'transaction_id_range':[e.transaction_id//(2**63//10+1) for e in scored],'transaction_id_last_digit':[e.transaction_id%10 for e in scored],'timestamp_30day_block':[(e.time-42*DAY)//(30*DAY) for e in scored],'amount_cents':[e.amount_minor%100 for e in scored],'channel':[e.channel for e in scored],'wallet_id':[e.subject for e in scored],'agent_id':[e.agent_id for e in scored]}
    for field in ('population_unit','profile','archetype','origin','scenario_family','event_role','context_role'):
        columns[field]=[str(p[field]) for p in meta]
    columns['strength_bin']=[int(p['strength']*10) if p['strength'] is not None else -1 for p in meta]
    for field,values in columns.items():
        groups=defaultdict(list)
        for i,value in enumerate(values): groups[str(value)].append(i)
        rows={g:{'n':len(ii),'target1':int(y[ii].sum()),'prevalence':float(y[ii].mean())} for g,ii in groups.items()}
        candidates={g:v for g,v in rows.items() if v['n']>=50 and (v['prevalence']<=.01 or v['prevalence']>=.99)}
        shortcut[field]={'groups':rows,'near_deterministic_supported_groups':candidates,'supported_pure_group_row_fraction':sum(v['n'] for v in candidates.values())/len(y)}
    domains=np.stack([flags[:,:4].any(axis=1),flags[:,4:8].any(axis=1),flags[:,8:].any(axis=1)],axis=1)
    design_audit=episode_audit(scored,meta,populations)
    return {'distribution':{'target0':int((y==0).sum()),'target1':int(y.sum()),'prevalence':float(y.mean()),'envelope_pass':.1<=float(y.mean())<=.45,'domains':dict(zip(['structuring','network','agent'],[int(x) for x in domains.sum(axis=0)])),'domain_only':dict(zip(['structuring','network','agent'],[int((domains[:,j]&(domains.sum(axis=1)==1)).sum()) for j in range(3)])),'multi_domain':int((domains.sum(axis=1)>1).sum())},'family_support':family,'hard_origins':hard,'background':background,'archetypes':archetype,'wallet_profiles':profile,'agent_concentration':{'per_agent':per_agent,'positives_per_agent':dict(positive_agents),'maximum_agent_positive_share':max(positive_agents.values())/sum(positive_agents.values()) if positive_agents else None},'a1_overlap':overlap,'a1_alignment_mismatches':0,'a1_all_origin_growth':group_result([i for i,e in enumerate(scored) if growth_origin(e)],y,flags),'shortcuts':shortcut,'amendment_implementation':design_audit},primitives


def episode_audit(scored,meta,populations):
    by_episode=defaultdict(list)
    for e,p in zip(scored,meta):
        if p['scenario_id'] is not None: by_episode[p['scenario_id']].append((e,p))
    failures=[]; roles=Counter(); origins=defaultdict(list); large={k:[] for k in ('S4','H3')}
    for pop in populations:
        for plan in pop['episodes']:
            rows=by_episode[plan['id']]
            motif=[(e,p) for e,p in rows if p['event_role']=='motif']
            context=[(e,p) for e,p in rows if p['event_role']=='context']
            if len(rows)!=plan['E'] or len(motif)!=plan['M'] or len(context)!=plan['E']-plan['M']: failures.append(plan['id'])
            if not 8<=plan['E']<=20 or not plan['M']<=plan['E']: failures.append(plan['id'])
            for e,p in rows:
                if not plan['start']<=e.time<=plan['end']: failures.append(plan['id'])
                if p['event_role']=='motif' and not plan['motif_start']<=e.time<=plan['motif_end']: failures.append(plan['id'])
                if p['context_role']=='post_motif_ordinary' and e.time<=plan['motif_end']: failures.append(plan['id'])
                roles[p['context_role'] or 'motif']+=1
            origins[plan['origin']].append({'E':plan['E'],'M':plan['M']})
            if plan['origin'] in large:
                large[plan['origin']]+=[e.amount_minor for e,_ in motif]
    assert not failures
    assert all(500000<=x<=1300000 for values in large.values() for x in values)
    return {'status':'PASS','episodes':sum(len(p['episodes']) for p in populations),'count_or_timing_failures':failures,'context_roles':dict(roles),'episode_count_distributions':{origin:{'E':dict(Counter(x['E'] for x in values)),'M':dict(Counter(x['M'] for x in values))} for origin,values in origins.items()},'large_amounts':{origin:distribution(values) for origin,values in large.items()},'S4_H3_conditional_sampler':'Same f=S4 implementation and shared large_amount function; amount-only fixtures use independent test streams','residual_background':sum(p['residual_background'] for p in populations)}
