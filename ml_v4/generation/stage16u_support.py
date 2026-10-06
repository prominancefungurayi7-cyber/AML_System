"""Challenge support audit on in-memory observables; never a sampling filter.

All detailed output belongs inside future custody. This module writes no files.
"""
from collections import Counter
from fractions import Fraction as Q
from stage16r_contract import DAY, HOUR, FAMILIES, median, window
from stage16r_evaluator import Evaluator, cash_stats, top2, total


def family_subject(event, family):
    if family.startswith('A'): return event.agent_id
    if family == 'N1': return event.receiver_wallet
    if family == 'N3': return (event.sender_wallet, event.receiver_wallet)
    return event.subject


def has_topology(event, edges):
    adjacency = {}
    for edge in edges:
        if event.time-7*DAY < edge.time <= event.time and edge.key < event.key:
            adjacency.setdefault(edge.sender_wallet, []).append(edge)
    def visit(node, seen, previous, depth):
        if depth == 5: return False
        for edge in adjacency.get(node, []):
            if edge.receiver_wallet in seen or (previous is not None and edge.key<=previous): continue
            if edge.receiver_wallet == event.sender_wallet: return True
            if visit(edge.receiver_wallet,seen|{edge.receiver_wallet},edge.key,depth+1): return True
        return False
    return visit(event.receiver_wallet,{event.receiver_wallet},None,0)


def boundary(state, e, family, truth):
    """Exact atomic boundary diagnostic, separate from universal labels."""
    if not truth['eligible'][family]: return dict(near=False, reason='ineligible')
    if family in truth['families']: return dict(near=False,reason='family_positive')
    if family == 'N3':
        top = has_topology(e,state.edges)
        return dict(near=top,reason='topology_with_all_monetary_paths_failing' if top else 'no_topology')
    atoms = []
    def lower(name, value, threshold, kind='ratio'):
        value, threshold = Q(value), Q(threshold)
        gap = 1 if kind=='count' else abs(threshold)/10
        atoms.append((name,value>=threshold,threshold-gap<=value<threshold))
    def upper(name, value, threshold):
        value, threshold = Q(value), Q(threshold)
        atoms.append((name,value<=threshold,threshold<value<=threshold*Q(11,10)))
    def condition(name, value): atoms.append((name,bool(value),False))
    t=e.time
    hist=state.services[e.agent_id] if family.startswith('A') else state.activity[e.subject]
    length=HOUR if family in ('S1','A3') else 7*DAY if family in ('S2','S4','A1') else DAY
    recent=window(hist,t-length,t)+[e]
    base=window(hist,t-length-28*DAY,t-length)
    if family=='S1':
        lower('count',len(recent),4,'count'); condition('variation',len({x.amount_minor for x in recent})>=2)
        lower('value',total(recent),30000); upper('maximum_share',Q(max(x.amount_minor for x in recent),total(recent)),Q(3,5))
        lower('acceleration',Q(len(recent))/max(1,Q(len(base),672)),3)
    elif family=='S2':
        cr=[x for x in recent if 20*abs(x.amount_minor-e.amount_minor)<=e.amount_minor]
        cb=[x for x in base if 20*abs(x.amount_minor-e.amount_minor)<=e.amount_minor]
        lower('similar_count',len(cr),4,'count'); lower('similar_value',total(cr),20000)
        lower('share',Q(len(cr),len(recent)),Q(3,5)); lower('growth',Q(len(cr))/max(1,Q(len(cb),4)),2)
    elif family=='S3':
        midnight=t//DAY*DAY
        recent=[x for x in hist if midnight<=x.time<=t]+[e]
        base=[x for x in hist if midnight-28*DAY<=x.time<midnight]
        days=Counter(x.time//DAY for x in base)
        lower('count',len(recent),6,'count'); lower('hours',len({x.time//HOUR for x in recent}),3,'count')
        lower('value',total(recent),50000)
        lower('growth',Q(len(recent))/max(1,median([days[midnight//DAY-i] for i in range(1,29)])),2)
    elif family=='S4':
        band=lambda x:700000<=x.amount_minor<=1050000
        cr=[x for x in recent if band(x)]; cb=[x for x in base if band(x)]
        atoms.append(('current_band',band(e),665000<=e.amount_minor<700000 or 1050000<e.amount_minor<=1102500))
        lower('count',len(recent),5,'count'); lower('band_count',len(cr),3,'count')
        condition('variation',len({x.amount_minor for x in cr})>=2)
        lower('share',Q(len(cr),len(recent)),Q(2,5)); lower('growth',Q(len(cr))/max(1,Q(len(cb),4)),2)
    elif family in ('N1','N2'):
        hist=state.incoming[e.receiver_wallet] if family=='N1' else state.outgoing[e.sender_wallet]
        recent=window(hist,t-DAY,t)+[e]; base=window(hist,t-29*DAY,t-DAY)
        opposite='sender_wallet' if family=='N1' else 'receiver_wallet'
        lower('count',len(recent),4,'count'); lower('distinct',len({getattr(x,opposite) for x in recent}),3,'count')
        lower('value',total(recent),30000); lower('growth',Q(len(recent))/max(1,Q(len(base),28)),2)
    elif family=='N4':
        anchor=min(window(state.incoming[e.subject],t-DAY,t),key=lambda x:x.key)
        funding=total([x for x in state.funding[e.subject] if anchor.key<=x.key<e.key])
        out=total([x for x in state.exits[e.subject] if anchor.key<x.key<e.key])
        lower('funding',funding,10000); lower('fraction',Q(out+e.amount_minor,funding),Q(1,2))
        upper('fraction_upper',Q(out+e.amount_minor,funding),1)
        # Keep the separately frozen residual comparison as its own atomic condition.
        upper('residual',e.amount_minor,funding-out)
    elif family=='A1':
        d=len({x.serviced_wallet for x in recent}); u=len({x.serviced_wallet for x in recent}-{x.serviced_wallet for x in base})
        med=median([len({x.serviced_wallet for x in window(hist,t-(14+7*i)*DAY,t-(7+7*i)*DAY)}) for i in range(4)])
        lower('distinct',d,6,'count'); lower('new',u,4,'count')
        lower('novelty',Q(u,d),Q(1,2)); lower('growth',Q(d)/max(1,med),Q(3,2))
    elif family=='A2':
        lower('count',len(recent),8,'count'); lower('top2',top2(recent),Q(13,20)); lower('change',top2(recent)-top2(base),Q(1,5))
    elif family=='A3':
        lower('count',len(recent),5,'count'); lower('distinct',len({x.serviced_wallet for x in recent}),3,'count')
        lower('acceleration',Q(len(recent))/max(1,Q(len(base),672)),3)
    elif family=='A4':
        rs,bs=cash_stats(recent),cash_stats(base)
        lower('count',rs['in_count']+rs['out_count'],6,'count'); lower('distinct',rs['distinct'],3,'count')
        lower('value_skew',abs(rs['value_skew']),Q(3,5)); lower('count_skew',abs(rs['count_skew']),Q(1,2))
        condition('sign_agreement',rs['value_skew']*rs['count_skew']>0)
        lower('change',abs(rs['value_skew']-bs['value_skew']),Q(2,5))
    failed=[a for a in atoms if not a[1]]
    return dict(near=len(failed)==1 and failed[0][2],reason='atomic_conditions',failed=[a[0] for a in failed])


def summarize(rows):
    n=len(rows)
    def maximum(key): return max(Counter(r[key] for r in rows).values(),default=0)/n if n else None
    return dict(rows=n,subjects=len({r['subject'] for r in rows}),clusters=len({r['cluster'] for r in rows}),
                units=len({r['unit'] for r in rows}),max_subject_share=maximum('subject'),
                max_unit_share=maximum('unit'),max_bin_share=maximum('bin'),
                bins=[sum(r['bin']==i for r in rows) for i in range(6)],
                arms={a:dict(rows=sum(r['arm']==a for r in rows),units=len({r['unit'] for r in rows if r['arm']==a}))
                      for a in ('reference_challenge','shifted_challenge')})


def assess(family_rows, hard_rows, boundary_rows, policy):
    """Full threshold evaluation; inputs are custodian audit records, not X."""
    result={}
    for f in FAMILIES:
        p=policy['family_objectives'][f]; q=policy['negative_objectives'][f]
        s,h,b=(summarize(mapping[f]) for mapping in (family_rows,hard_rows,boundary_rows))
        gates=dict(positive=s['rows']>=p['positive_decision_points'],subjects=s['subjects']>=p['distinct_subjects'],
            clusters=s['clusters']>=p['episode_or_background_clusters'],units=s['units']>=p['local_units'],
            temporal=sum(n>=p['minimum_positive_rows_in_each_of_at_least_4_fixed_30day_bins'] for n in s['bins'])>=4,
            subject_concentration=s['max_subject_share'] is not None and s['max_subject_share']<=p['max_subject_share'],
            unit_concentration=s['max_unit_share'] is not None and s['max_unit_share']<=p['max_unit_share'],
            bin_concentration=s['max_bin_share'] is not None and s['max_bin_share']<=p['max_30day_bin_share'],
            arms=all(a['rows']>=p['per_arm_positive_points'] and a['units']>=p['per_arm_units'] for a in s['arms'].values()),
            hard_rows=h['rows']>=q['union_target0_matched_hard_rows'],hard_subjects=h['subjects']>=q['distinct_subjects'],
            hard_units=h['units']>=q['local_units'],boundary_rows=b['rows']>=q['near_boundary_target0_rows'],
            boundary_units=b['units']>=q['near_boundary_units'])
        result[f]=dict(positive=s,hard=h,boundary=b,gates=gates,status='PASS' if all(gates.values()) else 'FAIL')
    return dict(families=result,status='PASS' if all(r['status']=='PASS' for r in result.values()) else 'FAIL',
                precision='NOT_EVALUATED_REQUIRES_FROZEN_MODEL_RESULTS')
