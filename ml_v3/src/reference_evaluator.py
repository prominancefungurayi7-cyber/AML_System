from __future__ import annotations
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json

FAMILIES=('variable_fragment_burst','similar_amount_repetition','distributed_same_day_fragmentation','variable_near_threshold_history','many_to_one_collection','one_to_many_dispersion','reciprocal_relationship_cycle','wallet_pass_through','agent_wallet_growth','agent_wallet_concentration','agent_temporal_burst','agent_flow_imbalance')
PREDICATE_VERSION='v3_onset_contract_rev1'

def dt(x): return datetime.strptime(x,'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
def usd(e): return int(e['amount_minor'])/100.0
def key(e): return e['_key'] if '_key' in e else (dt(e['event_timestamp']),int(e['transaction_id']))
def etime(e): return key(e)[0]
def wallet_subject(e): return e['serviced_wallet'] if e['transaction_type']!='wallet_to_wallet' else e['sender_wallet']
def prior(rows,now,lo): return [h for h in rows if lo <= etime(h) and key(h) < key(now)]
def full_coverage(rows,now,days=28):
    return bool(rows) and etime(rows[0]) <= etime(now)-timedelta(days=days)
def median(xs):
    if not xs:return 0.0
    ys=sorted(xs); n=len(ys); return ys[n//2] if n%2 else (ys[n//2-1]+ys[n//2])/2
def ratio(a,b): return a/b if b else 0.0

def path_closing(outbound,sender,receiver,now):
    # Return a qualifying prior path, ordered by event key, or None.  The
    # adjacency map contains every prior wallet-to-wallet edge in the
    # partition, so an arbitrary intermediate path cannot be hidden by a
    # current-endpoint-only slice.
    cutoff=etime(now)-timedelta(days=7)
    adjacency=defaultdict(list)
    for start, values in outbound.items():
        adjacency[start].extend(e for e in values if key(e) < key(now) and etime(e) >= cutoff)
    for values in adjacency.values(): values.sort(key=key)
    def dfs(node,target,last_i,path,seen_nodes):
        if node==target and path: return path
        if len(path)>=5:return None
        for e in adjacency.get(node,()):
            if key(e)<=last_i or e['receiver_wallet'] in seen_nodes: continue
            q=dfs(e['receiver_wallet'],target,key(e),path+[e],seen_nodes|{e['receiver_wallet']})
            if q:return q
        return None
    # first edge starts at receiver; path nodes may end at sender.
    for e in adjacency.get(receiver,()):
        if e['receiver_wallet']==sender: continue
        q=dfs(e['receiver_wallet'],sender,key(e),[e],{receiver,e['receiver_wallet']})
        if q:
            vals=[usd(x) for x in q]
            if all(.25<=vals[j]/vals[j-1]<=4 for j in range(1,len(vals))) and .25<=usd(now)/vals[0]<=1.25: return q
    for e in adjacency.get(receiver,()):
        if e['sender_wallet']==receiver and e['receiver_wallet']==sender and .25<=usd(now)/usd(e)<=1.25:return [e]
    return None

def evaluate_rows(raw_rows, provenance=None):
    rows=[]
    for r in raw_rows:
        e=dict(r); e['_key']=(dt(e['event_timestamp']),int(e['transaction_id'])); rows.append(e)
    rows.sort(key=lambda x:x['_key'])
    wallet_hist=defaultdict(list); wallet_day_counts=defaultdict(Counter); inbound=defaultdict(list); outbound=defaultdict(list); agents=defaultdict(list)
    results=[]; onset_by_family={}; first_campaign_onset={}
    for event_index,e in enumerate(rows,1):
        if event_index % 10000 == 0: print(f'evaluator {event_index}/{len(rows)}',flush=True)
        now=e['_key']; w=wallet_subject(e); wh=wallet_hist[w]; t=now[0]
        fam=[]; witnesses={}; subjects={}
        # S1/S2/S4 wallet history, with explicit 28-day coverage.
        h1=prior(wh,e,t-timedelta(hours=1)); b1=[h for h in wh if t-timedelta(days=29)<=etime(h)<t-timedelta(hours=1)]
        if full_coverage(wh,e) and len(b1)>=4 and len(h1)>=4:
            vals=[usd(x) for x in h1]
            if len(set(vals))>=2 and sum(vals)>=300 and max(vals)<=.60*sum(vals) and len(h1)>=3*max(1,len(b1)/672): fam.append('variable_fragment_burst'); witnesses[fam[-1]]=[x['transaction_id'] for x in h1]
        h7=prior(wh,e,t-timedelta(days=7)); b7=[h for h in wh if t-timedelta(days=35)<=etime(h)<t-timedelta(days=7)]
        matching=[x for x in h7 if abs(usd(x)-usd(e))<=.05*usd(e)]
        bm=[x for x in b7 if abs(usd(x)-usd(e))<=.05*usd(e)]
        if full_coverage(wh,e) and len(bm)>=4 and len(h7)>=4 and len(matching)>=4 and sum(usd(x) for x in matching)>=200 and ratio(len(matching),len(h7))>=.60 and len(matching)>=2*max(1,len(bm)/4): fam.append('similar_amount_repetition'); witnesses[fam[-1]]=[x['transaction_id'] for x in matching]
        day=[x for x in wh+[e] if etime(x).date()==t.date() and key(x)<=key(e)]
        bd=[x for x in wh if t-timedelta(days=28)<=etime(x)<t and etime(x).date()!=t.date()]
        counts=[wallet_day_counts[w].get(t.date()-timedelta(days=i),0) for i in range(1,29)]
        if full_coverage(wh,e) and len(bd)>=4 and len(day)>=6 and len({etime(x).hour for x in day})>=3 and sum(usd(x) for x in day)>=500 and len(day)>=2*max(1,median(counts)): fam.append('distributed_same_day_fragmentation'); witnesses[fam[-1]]=[x['transaction_id'] for x in day]
        band=[x for x in h7+[e] if 7000<=usd(x)<=10500]; bb=[x for x in b7 if 7000<=usd(x)<=10500]
        if 7000<=usd(e)<=10500 and full_coverage(wh,e) and len(h7)+1>=5 and len(band)>=3 and len({usd(x) for x in band})>=2 and ratio(len(band),len(h7)+1)>=.4 and len(bb)>=4 and len(band)>=2*max(1,len(bb)/4): fam.append('variable_near_threshold_history'); witnesses[fam[-1]]=[x['transaction_id'] for x in band]
        # Network predicates.
        if e['transaction_type']=='wallet_to_wallet':
            rec=e['receiver_wallet']; snd=e['sender_wallet']; ri=[x for x in inbound[rec] if t-timedelta(hours=24)<=etime(x)<t]+[e]; rb=[x for x in inbound[rec] if t-timedelta(days=28)<=etime(x)<t-timedelta(hours=24)]
            if len(rb)>=4 and len(ri)>=4 and len({x['sender_wallet'] for x in ri})>=3 and sum(usd(x) for x in ri)>=300 and len(ri)>=2*max(1,len(rb)/28): fam.append('many_to_one_collection'); witnesses[fam[-1]]=[x['transaction_id'] for x in ri]
            so=[x for x in outbound[snd] if t-timedelta(hours=24)<=etime(x)<t]+[e]; sb=[x for x in outbound[snd] if t-timedelta(days=28)<=etime(x)<t-timedelta(hours=24)]
            if len(sb)>=4 and len(so)>=4 and len({x['receiver_wallet'] for x in so})>=3 and sum(usd(x) for x in so)>=300 and len(so)>=2*max(1,len(sb)/28): fam.append('one_to_many_dispersion'); witnesses[fam[-1]]=[x['transaction_id'] for x in so]
            path=path_closing(outbound,snd,rec,e)
            if path: fam.append('reciprocal_relationship_cycle'); witnesses[fam[-1]]=[x['transaction_id'] for x in path]+[e['transaction_id']]
        # N4 current outgoing event.
        if e['transaction_type']=='wallet_to_wallet' or e['transaction_type']=='cash_out':
            infl=[x for x in inbound[w] if t-timedelta(hours=24)<=etime(x)<t]
            if infl:
                tau=min(infl,key=key); funding=[x for x in inbound[w]+[x for x in wh if x['transaction_type']=='cash_in'] if key(x)>=key(tau) and key(x)<key(e)]
                before=[x for x in wh if key(x)>=key(tau) and key(x)<key(e) and (x['transaction_type']=='wallet_to_wallet' and x['sender_wallet']==w or x['transaction_type']=='cash_out')]
                current=usd(e); F=sum(usd(x) for x in funding); O=sum(usd(x) for x in before)+current
                if F>=100 and .50<=ratio(O,F)<=1.0 and current<=F-sum(usd(x) for x in before): fam.append('wallet_pass_through'); witnesses[fam[-1]]=[x['transaction_id'] for x in funding+before]+[e['transaction_id']]
        # Agent predicates.
        if e['agent_id']:
            ah=agents[e['agent_id']]; a7=[x for x in ah if t-timedelta(days=7)<=etime(x)<t]+[e]; ab=[x for x in ah if t-timedelta(days=35)<=etime(x)<t-timedelta(days=7)]
            bases=[set(x['serviced_wallet'] for x in ah if t-timedelta(days=7*i)<=etime(x)<t-timedelta(days=7*(i-1))) for i in range(2,6)]
            union=set().union(*bases); distinct=len(set(x['serviced_wallet'] for x in a7)); nov=len(set(x['serviced_wallet'] for x in a7)-union)
            if full_coverage(ah,e) and len(ab)>=12 and distinct>=6 and nov>=4 and ratio(nov,distinct)>=.5 and distinct>=1.5*max(1,median([len(x) for x in bases])): fam.append('agent_wallet_growth'); witnesses[fam[-1]]=[x['transaction_id'] for x in a7]
            a24=[x for x in ah if t-timedelta(hours=24)<=etime(x)<t]+[e]; base28=[x for x in ah if t-timedelta(days=28)<=etime(x)<t-timedelta(hours=24)]
            cc=Counter(x['serviced_wallet'] for x in a24); cb=Counter(x['serviced_wallet'] for x in base28); top=sum(sorted(cc.values(),reverse=True)[:2]); btop=ratio(sum(sorted(cb.values(),reverse=True)[:2]),len(base28))
            if full_coverage(ah,e) and len(base28)>=20 and len(set(x['serviced_wallet'] for x in base28))>=5 and len(a24)>=8 and ratio(top,len(a24))>=.65 and ratio(top,len(a24))-btop>=.2: fam.append('agent_wallet_concentration'); witnesses[fam[-1]]=[x['transaction_id'] for x in a24]
            a1=[x for x in ah if t-timedelta(hours=1)<=etime(x)<t]+[e]
            if full_coverage(ah,e) and len(ab)>=12 and len(a1)>=5 and len({x['serviced_wallet'] for x in a1})>=3 and len(a1)>=3*max(1,len(ab)/672): fam.append('agent_temporal_burst'); witnesses[fam[-1]]=[x['transaction_id'] for x in a1]
            if e['transaction_type'] in ('cash_in','cash_out'):
                c24=[x for x in ah if t-timedelta(hours=24)<=etime(x)<t and x['transaction_type'] in ('cash_in','cash_out')]+[e]; cb=[x for x in ah if t-timedelta(days=28)<=etime(x)<t-timedelta(hours=24) and x['transaction_type'] in ('cash_in','cash_out')]
                ci=sum(usd(x) for x in c24 if x['transaction_type']=='cash_in'); co=sum(usd(x) for x in c24 if x['transaction_type']=='cash_out'); bi=sum(usd(x) for x in cb if x['transaction_type']=='cash_in'); bo=sum(usd(x) for x in cb if x['transaction_type']=='cash_out'); vv=ratio(co-ci,co+ci); ccx=ratio(sum(x['transaction_type']=='cash_out' for x in c24)-sum(x['transaction_type']=='cash_in' for x in c24),len(c24)); bv=ratio(bo-bi,bo+bi)
                if full_coverage(ah,e) and len(cb)>=8 and len(ab)>=12 and len(c24)>=6 and len({x['serviced_wallet'] for x in c24})>=3 and abs(vv)>=.6 and abs(ccx)>=.5 and vv*ccx>0 and abs(vv-bv)>=.4: fam.append('agent_flow_imbalance'); witnesses[fam[-1]]=[x['transaction_id'] for x in c24]
        results.append({'event':e,'families':fam,'witnesses':witnesses})
        wallet_hist[w].append(e)
        wallet_day_counts[w][t.date()]+=1
        if e['transaction_type']=='wallet_to_wallet': inbound[e['receiver_wallet']].append(e); outbound[e['sender_wallet']].append(e)
        if e['agent_id']: agents[e['agent_id']].append(e)
    return results
