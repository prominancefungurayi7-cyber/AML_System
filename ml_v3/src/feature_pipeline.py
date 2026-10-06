"""Causal, partition-local V3 Stage 10 feature extraction.

This module contains no target or scenario access.  State is updated only
after the current row has been emitted, and all maps are created per call.
"""
from __future__ import annotations
import csv, json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from contracts import EVENT_FIELDS, TRUTH_FIELDS, load_development
from feature_contract import FEATURE_NAMES, MISSING_VALUE, AMOUNT_BAND_USD

DAY = timedelta(days=1)


def _dt(value):
    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)


def _prepare(rows):
    out=[]
    for row in rows:
        e=dict(row)
        e['_dt']=_dt(e['event_timestamp'])
        e['_key']=(e['_dt'], int(e['transaction_id']))
        e['_amount']=int(e['amount_minor'])/100.0
        e['_w2w']=e['transaction_type']=='wallet_to_wallet'
        e['_subject']=e['serviced_wallet'] or e['sender_wallet']
        out.append(e)
    return sorted(out,key=lambda x:x['_key'])


def _in_window(values, now, delta, inclusive=False):
    start=now-delta
    if inclusive:
        return [x for x in values if start <= x['_dt'] <= now]
    return [x for x in values if start <= x['_dt'] < now]


def _coverage(values, now):
    if not values:
        return 0.0
    first=min(x['_dt'] for x in values)
    return min(28.0, max(0.0, (now-first).total_seconds()/86400.0))


def _share(numerator, denominator):
    return numerator/denominator if denominator else 0.0


def _median(values):
    if not values:
        return 0.0
    values=sorted(values); n=len(values); m=n//2
    return values[m] if n%2 else (values[m-1]+values[m])/2.0


def _skew(values, field='_amount'):
    ins=[x for x in values if x['transaction_type']=='cash_in']
    outs=[x for x in values if x['transaction_type']=='cash_out']
    a=sum(x[field] if field=='_amount' else 1 for x in outs)
    b=sum(x[field] if field=='_amount' else 1 for x in ins)
    return (a-b)/(a+b) if a+b else 0.0


def _path(outbound, sender, receiver, now):
    """Select shortest prior receiver->sender path under the Stage 8 rule."""
    cutoff=now-timedelta(days=7)
    candidates=[]
    def visit(node, path, seen):
        if node==sender and path:
            candidates.append(path); return
        if len(path)>=5: return
        edges=[x for x in outbound.get(node,()) if cutoff <= x['_dt'] < now]
        edges.sort(key=lambda x:x['_key'])
        for edge in edges:
            nxt=edge['receiver_wallet']
            if nxt in seen: continue
            visit(nxt, path+[edge], seen|{nxt})
    visit(receiver, [], {receiver})
    if not candidates: return None
    candidates.sort(key=lambda p:(len(p), -p[0]['_key'][0].timestamp(), -p[0]['_key'][1], tuple(x['_key'] for x in p)))
    return candidates[0]


def _row_features(e, wallet_hist, entity_hist, inbound, outbound, agents):
    now=e['_dt']; subject=e['_subject']; wh=wallet_hist.get(subject,[])
    eh=entity_hist.get(subject,[]); current_wh=wh+[e]
    h1=_in_window(current_wh,now,timedelta(hours=1),True)
    h24=_in_window(current_wh,now,timedelta(hours=24),True)
    h7=_in_window(current_wh,now,timedelta(days=7),True)
    day=[x for x in current_wh if x['_dt'].date()==now.date() and x['_key']<=e['_key']]
    prior28=_in_window(wh,now,timedelta(days=28))
    current_amount=e['_amount']
    s5=_share(sum(abs(x['_amount']-current_amount)<=.05*current_amount for x in h7),len(h7))
    s6=_share(sum(AMOUNT_BAND_USD[0] <= x['_amount'] <= AMOUNT_BAND_USD[1] for x in h7),len(h7))
    q1=_coverage(eh,now)
    s7=len(h1)/max(1.0,len(prior28)/672.0) if q1>=28.0 else MISSING_VALUE

    # Network summaries use principal wallet endpoints, including current W2W
    # only in inclusive quantities.
    rec=e['receiver_wallet']; snd=e['sender_wallet']
    rh=entity_hist.get(rec,[]); receiver_in=list(inbound.get(rec,[])); sender_out=list(outbound.get(snd,[]))
    ri=[x for x in receiver_in if now-timedelta(hours=24)<=x['_dt']<now]
    so=[x for x in sender_out if now-timedelta(hours=24)<=x['_dt']<now]
    if e['_w2w']:
        ri=ri+[e]; so=so+[e]
    receiver_prior28=[x for x in receiver_in if now-timedelta(days=28)<=x['_dt']<now]
    sender_prior28=[x for x in sender_out if now-timedelta(days=28)<=x['_dt']<now]
    q2=_coverage(rh,now)
    n3=len(ri)/max(1.0,len(receiver_prior28)/28.0) if q2>=28.0 else MISSING_VALUE
    # Sender coverage is represented by the same observable entity history.
    sh=_coverage(entity_hist.get(snd,[]),now)
    n6=len(so)/max(1.0,len(sender_prior28)/28.0) if sh>=28.0 else MISSING_VALUE
    path=_path(outbound,snd,rec,now) if e['_w2w'] else None
    n7=len(path) if path else 0.0
    n8=current_amount/path[0]['_amount'] if path and path[0]['_amount'] else MISSING_VALUE

    # Observable pass-through state.  Only an outward current role can have
    # onward share; assisted W2W remains a principal wallet event here.
    outward=e['_w2w'] or e['transaction_type']=='cash_out'
    n9=0.0; n10=0.0
    if outward:
        prior_in=[x for x in inbound.get(snd,[]) if now-timedelta(hours=24)<=x['_dt']<now]
        prior_in += [x for x in wh if x['transaction_type']=='cash_in' and x['_dt']<now]
        anchor=min(prior_in,key=lambda x:x['_key']) if prior_in else None
        if anchor:
            funding=[x for x in inbound.get(snd,[])+[z for z in wh if z['transaction_type']=='cash_in'] if anchor['_key']<=x['_key']<e['_key']]
            previous=[x for x in wh if anchor['_key']<=x['_key']<e['_key'] and ((x['_w2w'] and x['sender_wallet']==snd) or x['transaction_type']=='cash_out')]
            F=sum(x['_amount'] for x in funding); O=sum(x['_amount'] for x in previous)+current_amount
            n9=O/F if F else MISSING_VALUE
            n10=max(0.0,(now-anchor['_dt']).total_seconds()/3600.0)
        else:
            n9=MISSING_VALUE; n10=MISSING_VALUE

    # Agent service state is separate from principal wallet cash state.
    aid=e['agent_id']; ah=agents.get(aid,[]) if aid else []
    service=[x for x in ah if x.get('serviced_wallet')]
    service_inclusive=service+([e] if aid and e.get('serviced_wallet') else [])
    a1=_in_window(service_inclusive,now,timedelta(hours=1),True) if aid else []
    a24=_in_window(service_inclusive,now,timedelta(hours=24),True) if aid else []
    a7=_in_window(service_inclusive,now,timedelta(days=7),True) if aid else []
    agent_prior28=_in_window(ah,now,timedelta(days=28)) if aid else []
    agent_cov=_coverage(ah,now) if aid else 0.0
    a2=len(a1)/max(1.0,len(agent_prior28)/672.0) if aid and agent_cov>=28.0 else MISSING_VALUE
    base_sets=[]
    for i in range(2,6):
        lo=now-timedelta(days=7*i); hi=now-timedelta(days=7*(i-1))
        base_sets.append({x['serviced_wallet'] for x in ah if x.get('serviced_wallet') and lo<=x['_dt']<hi})
    base_union=set().union(*base_sets) if base_sets else set()
    distinct_recent=len({x['serviced_wallet'] for x in a7})
    baseline_counts=[len(s) for s in base_sets]
    a3=distinct_recent/max(1.0,_median(baseline_counts)) if aid and agent_cov>=28.0 else MISSING_VALUE
    a4=_share(sum(x['serviced_wallet'] not in base_union for x in a7),len(a7)) if aid and agent_cov>=28.0 else MISSING_VALUE
    def top2_share(values):
        c=Counter(x['serviced_wallet'] for x in values if x.get('serviced_wallet'))
        return _share(sum(v for _,v in c.most_common(2)),len(values))
    a5=top2_share(a24) if aid else 0.0
    base28_service=[x for x in ah if now-timedelta(days=28)<=x['_dt']<now-timedelta(hours=24) and x.get('serviced_wallet')]
    a6=a5-top2_share(base28_service) if aid and agent_cov>=28.0 else MISSING_VALUE
    cash24=_in_window(ah+([e] if aid and e['transaction_type'] in ('cash_in','cash_out') else []),now,timedelta(hours=24),True) if aid else []
    cashbase=[x for x in ah if now-timedelta(days=28)<=x['_dt']<now-timedelta(hours=24)] if aid else []
    a7v=_skew(cash24); a8v=_skew(cash24,field='count')
    a9v=a7v-_skew(cashbase) if aid and agent_cov>=28.0 else MISSING_VALUE

    return [current_amount,float(e['transaction_type']=='cash_in'),float(e['transaction_type']=='cash_out'),
            float(len(h1)),sum(x['_amount'] for x in h24),float(len(day)),float(len({x['_dt'].hour for x in day})),s5,s6,s7,
            float(len({x['sender_wallet'] for x in ri})),float(len(ri)),n3,float(len({x['receiver_wallet'] for x in so})),float(len(so)),n6,n7,n8,n9,n10,
            float(len(a1)),a2,a3,a4,a5,a6,a7v,a8v,a9v,q1,q2,agent_cov]


def extract(rows):
    """Return ordered ``(row_ids, matrix)`` using only the supplied rows."""
    events=_prepare(rows)
    wallet_hist=defaultdict(list); entity_hist=defaultdict(list)
    inbound=defaultdict(list); outbound=defaultdict(list); agents=defaultdict(list)
    ids=[]; matrix=[]
    for e in events:
        ids.append(e['transaction_id'])
        matrix.append(_row_features(e,wallet_hist,entity_hist,inbound,outbound,agents))
        wallet_hist[e['_subject']].append(e)
        for wallet in {e['sender_wallet'],e['receiver_wallet'],e['_subject']}:
            if wallet: entity_hist[wallet].append(e)
        if e['_w2w']:
            inbound[e['receiver_wallet']].append(e); outbound[e['sender_wallet']].append(e)
        if e['agent_id']: agents[e['agent_id']].append(e)
    return ids,matrix


def extract_development(root):
    result={}
    for part in ('train','validation'):
        tx=load_development(root,part,'transactions')
        truth=load_development(root,part,'ground_truth')
        ids,x=extract(tx)
        y_by={r['transaction_id']:int(r['decision_point_target']) for r in truth}
        y=[y_by[i] for i in ids]
        result[part]={'row_ids':ids,'X':x,'y':y}
    return result


def write_matrices(root, matrices):
    for part,data in matrices.items():
        folder=Path(root)/'features'/'development'/part; folder.mkdir(parents=True,exist_ok=True)
        with (folder/'X.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.writer(f,lineterminator='\n'); w.writerow(FEATURE_NAMES); w.writerows(data['X'])
        with (folder/'y.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.writer(f,lineterminator='\n'); w.writerow(['decision_point_target']); w.writerows([[v] for v in data['y']])
        with (folder/'row_ids.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.writer(f,lineterminator='\n'); w.writerow(['transaction_id']); w.writerows([[v] for v in data['row_ids']])
        (folder/'feature_names.json').write_text(json.dumps(list(FEATURE_NAMES),indent=2)+'\n',encoding='utf-8')
