"""Causal feature implementation of the Stage 8 architecture, revision 10A."""
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from statistics import median
from stage10a_contract import NAMES

DAY = timedelta(days=1)
HOUR = timedelta(hours=1)
PUBLIC_FIELDS = ('transaction_id','event_timestamp','sender_wallet','receiver_wallet',
                 'amount_minor','transaction_type','agent_id','serviced_wallet')

def prepare(rows):
    events=[]
    for raw in rows:
        e={k: raw[k] for k in PUBLIC_FIELDS}
        e['t']=datetime.fromisoformat(e['event_timestamp'].replace('Z','+00:00'))
        e['id']=int(e['transaction_id']); e['key']=(e['t'],e['id']); e['amount']=int(e['amount_minor'])
        if e['amount']<=0: raise ValueError('amount must be positive')
        e['w2w']=e['transaction_type']=='wallet_to_wallet'
        e['subject']=e['sender_wallet'] if e['w2w'] else e['serviced_wallet']
        if e['transaction_type'] not in ('wallet_to_wallet','cash_in','cash_out') or not e['subject']:
            raise ValueError('unsupported event or missing cash subject')
        if e['agent_id'] and not e['serviced_wallet']: raise ValueError('service needs a wallet')
        events.append(e)
    events.sort(key=lambda e:e['key'])
    if len({e['id'] for e in events}) != len(events): raise ValueError('duplicate transaction id')
    return events

def recent(history,e,L):
    return [x for x in history if e['t']-L < x['t'] and x['key'] < e['key']]

def baseline(history,e,L):
    return [x for x in history if e['t']-L-28*DAY < x['t'] <= e['t']-L and x['key'] < e['key']]

def covered(first,e,L):
    return first is not None and first <= e['t']-L-28*DAY

def coverage(first,e):
    return 0. if first is None else min(28.,(e['t']-first).total_seconds()/86400.)

def top2(events):
    counts=Counter(x['serviced_wallet'] for x in events)
    return sum(sorted(counts.values(),reverse=True)[:2])/len(events) if events else 0.

def cash_skew(events,count=False):
    cash=[x for x in events if x['transaction_type'] in ('cash_in','cash_out')]
    den=sum(1 if count else x['amount'] for x in cash)
    num=sum((1 if x['transaction_type']=='cash_out' else -1)*(1 if count else x['amount']) for x in cash)
    return num/den if den else 0.

def select_path(outbound,e):
    if not e['w2w'] or e['sender_wallet']==e['receiver_wallet']: return None
    sender,receiver=e['sender_wallet'],e['receiver_wallet']
    # Breadth-first by length, with deterministic final tie ordering.
    frontier=[(receiver,(),frozenset((receiver,)))]
    for length in range(1,6):
        next_frontier=[]; candidates=[]
        for node,path,seen in frontier:
            for edge in recent(outbound.get(node,()),e,7*DAY):
                target=edge['receiver_wallet']
                if target in seen or (path and edge['key']<=path[-1]['key']): continue
                new=path+(edge,)
                if target==sender: candidates.append(new)
                else: next_frontier.append((target,new,seen|{target}))
        if candidates:
            latest=max(p[0]['key'] for p in candidates)
            return min((p for p in candidates if p[0]['key']==latest),key=lambda p:tuple(x['key'] for x in p))
        frontier=next_frontier
        if not frontier: break
    return None

def extract(rows):
    wallet=defaultdict(list); incoming=defaultdict(list); outgoing=defaultdict(list); agent=defaultdict(list)
    first_wallet={}; first_agent={}; ids=[]; X=[]
    for e in prepare(rows):
        t=e['t']; w=e['subject']; sender=e['sender_wallet']; receiver=e['receiver_wallet']; aid=e['agent_id']
        wh=wallet[w]; ah=agent[aid] if aid else []
        r1=recent(wh,e,HOUR)+[e]; r24=recent(wh,e,DAY)+[e]; r7=recent(wh,e,7*DAY)+[e]
        day=[x for x in wh if x['t'].date()==t.date() and x['key']<e['key']]+[e]
        b1=baseline(wh,e,HOUR)
        values=[e['amount']/100.,int(e['transaction_type']=='cash_in'),int(e['transaction_type']=='cash_out'),
                len(r1),sum(x['amount'] for x in r24)/100.,len(day),len({x['t'].hour for x in day}),
                sum(100*abs(x['amount']-e['amount'])<=5*e['amount'] for x in r7)/len(r7),
                sum(700000<=x['amount']<=1050000 for x in r7)/len(r7),
                len(r1)/max(1,len(b1)/672) if covered(first_wallet.get(w),e,HOUR) and len(b1)>=4 else -1.]
        ri=recent(incoming[receiver],e,DAY)+([e] if e['w2w'] else [])
        ro=recent(outgoing[sender],e,DAY)+([e] if e['w2w'] else [])
        bi=baseline(incoming[receiver],e,DAY); bo=baseline(outgoing[sender],e,DAY)
        values.extend([len({x['sender_wallet'] for x in ri}),len(ri),
                       len(ri)/max(1,len(bi)/28) if covered(first_wallet.get(receiver),e,DAY) and len(bi)>=4 else -1.,
                       len({x['receiver_wallet'] for x in ro}),len(ro),
                       len(ro)/max(1,len(bo)/28) if covered(first_wallet.get(sender),e,DAY) and len(bo)>=4 else -1.])
        path=select_path(outgoing,e)
        values.extend([len(path) if path else 0,e['amount']/path[0]['amount'] if path else -1.])
        onward,age=0.,-1.
        if e['w2w'] or e['transaction_type']=='cash_out':
            anchors=recent(incoming[w],e,DAY)
            if anchors:
                anchor=min(anchors,key=lambda x:x['key'])
                funding=[x for x in incoming[w] if anchor['key']<=x['key']<e['key']]
                funding += [x for x in wh if x['transaction_type']=='cash_in' and anchor['key']<=x['key']<e['key']]
                outward=[x for x in wh if anchor['key']<x['key']<e['key'] and (x['w2w'] or x['transaction_type']=='cash_out')]
                onward=(sum(x['amount'] for x in outward)+e['amount'])/sum(x['amount'] for x in funding)
                age=(t-anchor['t']).total_seconds()/3600.
            else: onward=-1.
        values.extend([onward,age])
        ar1=recent(ah,e,HOUR)+([e] if aid else []); ar24=recent(ah,e,DAY)+([e] if aid else [])
        ar7=recent(ah,e,7*DAY)+([e] if aid else []); ab1=baseline(ah,e,HOUR); ab24=baseline(ah,e,DAY); ab7=baseline(ah,e,7*DAY)
        a_first=first_agent.get(aid)
        eligible1=bool(aid) and covered(a_first,e,HOUR) and len(ab1)>=12
        eligible7=bool(aid) and covered(a_first,e,7*DAY) and len(ab7)>=12
        eligible24=bool(aid) and covered(a_first,e,DAY)
        recent_set={x['serviced_wallet'] for x in ar7}; base_set={x['serviced_wallet'] for x in ab7}
        buckets=[{x['serviced_wallet'] for x in ab7 if t-(i+1)*7*DAY < x['t'] <= t-i*7*DAY} for i in range(1,5)]
        values.extend([len(ar1),len(ar1)/max(1,len(ab1)/672) if eligible1 else -1.,
                       len(recent_set)/max(1,median([len(b) for b in buckets])) if eligible7 else -1.,
                       len(recent_set-base_set)/len(recent_set) if eligible7 else -1.,
                       top2(ar24),top2(ar24)-top2(ab24) if eligible24 and len(ab24)>=20 and len({x['serviced_wallet'] for x in ab24})>=5 else -3.,
                       cash_skew(ar24),cash_skew(ar24,True),
                       cash_skew(ar24)-cash_skew(ab24) if eligible24 and len(ab24)>=12 and sum(x['transaction_type'] in ('cash_in','cash_out') for x in ab24)>=8 else -3.,
                       coverage(first_wallet.get(w),e),coverage(first_wallet.get(receiver),e),coverage(a_first,e)])
        assert len(values)==len(NAMES)
        ids.append(str(e['id'])); X.append([float(v) for v in values])
        # Append once, only after emission. Endpoint receipt establishes coverage.
        wallet[w].append(e)
        observed={sender,receiver} if e['w2w'] else {w}
        for entity in observed:
            if entity: first_wallet.setdefault(entity,t)
        if e['w2w']:
            incoming[receiver].append(e); outgoing[sender].append(e)
        if aid:
            agent[aid].append(e); first_agent.setdefault(aid,t)
    return ids,X
