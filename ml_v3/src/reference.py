"""Universal causal reference evaluator. Accepts observable Event objects only."""
from collections import Counter, defaultdict
from fractions import Fraction
from common import DAY, HOUR, Event, validate_event


def recent(rows,t,length): return [e for e in rows if t-length<e.t<=t]
def baseline(rows,t,length): return [e for e in rows if t-length-28*DAY<e.t<=t-length]
def median(values):
    a=sorted(values); n=len(a)
    return Fraction(a[n//2]) if n%2 else Fraction(a[n//2-1]+a[n//2],2)
def top2(rows):
    c=Counter(e.wallet for e in rows)
    return Fraction(sum(sorted(c.values(),reverse=True)[:2]),len(rows)) if rows else Fraction(0)
def skew(rows,value=True):
    a=sum(e.amount if value else 1 for e in rows if e.kind=='cash_out')
    b=sum(e.amount if value else 1 for e in rows if e.kind=='cash_in')
    return Fraction(a-b,a+b) if a+b else Fraction(0)


class ReferenceEvaluator:
    def __init__(self,wallets=None,agents=None):
        self.allowed_wallets=wallets; self.allowed_agents=agents
        self.activity=defaultdict(list); self.inflows=defaultdict(list)
        self.outflows=defaultdict(list); self.service=defaultdict(list)
        self.first_wallet={}; self.first_agent={}; self.last_key=None; self.ids=set()

    def _path(self,e):
        def search(node,nodes,path):
            if len(path)>=5: return None
            for h in self.outflows[node]:
                if not (e.t-7*DAY<h.t<=e.t) or (path and h.key<=path[-1].key): continue
                if path and not (path[-1].amount<=4*h.amount<=16*path[-1].amount): continue
                if h.receiver in nodes: continue
                new=path+[h]
                if h.receiver==e.sender:
                    first=new[0].amount
                    if first<=4*e.amount<=5*first: return new
                else:
                    result=search(h.receiver,nodes|{h.receiver},new)
                    if result: return result
            return None
        return search(e.receiver,{e.receiver},[])

    def step(self,e):
        if not isinstance(e,Event): raise TypeError('Only observable Event instances are accepted')
        validate_event(e,self.allowed_wallets,self.allowed_agents)
        if (self.last_key is not None and e.key<=self.last_key) or e.transaction_id in self.ids:
            raise ValueError('Duplicate ID or nonchronological stream')
        t=e.t; w=e.subject; prior=self.activity[w]; witness={}; eligible={}
        def ready(f,subject,rows,length,minimum,agent=False,start=None):
            first=(self.first_agent if agent else self.first_wallet).get(subject,t)
            lower=t-length-28*DAY if start is None else start
            ok=first<=lower and len(rows)>=minimum
            eligible[f]=ok; return ok
        def hit(f,subject,rows,base=(),facts=None):
            length=HOUR if f in ('S1','A3') else 7*DAY if f in ('S2','S4','A1') else DAY
            interval=None if f in ('N3','N4') else {'lower':t-length-28*DAY,'upper':t-length,'lower_inclusive':False,'upper_inclusive':True}
            if f=='S3': interval={'lower':t//DAY*DAY-28*DAY,'upper':t//DAY*DAY,'lower_inclusive':True,'upper_inclusive':False}
            witness[f]={'subject':subject,'event_ids':sorted({h.transaction_id for h in rows}),
                        'baseline_ids':sorted({h.transaction_id for h in base}),
                        'baseline_interval':interval,'facts':facts or {},'predicate_version':'stage8.r1'}
        r1=recent(prior,t,HOUR)+[e]; b1=baseline(prior,t,HOUR)
        if ready('S1',w,b1,HOUR,4):
            total=sum(h.amount for h in r1)
            if len(r1)>=4 and len({h.amount for h in r1})>=2 and total>=30000 and 5*max(h.amount for h in r1)<=3*total and len(r1)*672>=3*len(b1):
                hit('S1',w,r1,b1,{'sum_minor':total})
        r7=recent(prior,t,7*DAY)+[e]; b7=baseline(prior,t,7*DAY)
        similar=lambda h:abs(h.amount-e.amount)*20<=e.amount
        cluster=[h for h in r7 if similar(h)]; bcluster=[h for h in b7 if similar(h)]
        if ready('S2',w,b7,7*DAY,4) and len(cluster)>=4 and sum(h.amount for h in cluster)>=20000 and 5*len(cluster)>=3*len(r7) and 4*len(cluster)>=2*len(bcluster):
            hit('S2',w,r7,b7,{'cluster_ids':[h.transaction_id for h in cluster]})
        day=t//DAY*DAY; daily=[h for h in prior if day<=h.t<=t]+[e]
        bd=[h for h in prior if day-28*DAY<=h.t<day]
        counts=Counter(h.t//DAY for h in bd)
        mid=median([counts[day//DAY-k] for k in range(1,29)])
        if ready('S3',w,bd,0,4,start=day-28*DAY) and len(daily)>=6 and len({h.t//HOUR for h in daily})>=3 and sum(h.amount for h in daily)>=50000 and len(daily)>=2*max(1,mid):
            hit('S3',w,daily,bd)
        band=lambda h:700000<=h.amount<=1050000
        near=[h for h in r7 if band(h)]; bnear=[h for h in b7 if band(h)]
        if ready('S4',w,b7,7*DAY,4) and band(e) and len(r7)>=5 and len(near)>=3 and len({h.amount for h in near})>=2 and 5*len(near)>=2*len(r7) and 4*len(near)>=2*len(bnear):
            hit('S4',w,r7,b7)
        eligible['N1']=eligible['N2']=eligible['N3']=False
        if e.kind=='wallet_to_wallet':
            for f,subject,hist,other in [('N1',e.receiver,self.inflows[e.receiver],'sender'),('N2',e.sender,self.outflows[e.sender],'receiver')]:
                rr=recent(hist,t,DAY)+[e]; bb=baseline(hist,t,DAY)
                if ready(f,subject,bb,DAY,4) and len(rr)>=4 and len({getattr(h,other) for h in rr})>=3 and sum(h.amount for h in rr)>=30000 and len(rr)*28>=2*len(bb):
                    hit(f,subject,rr,bb)
            eligible['N3']=True; path=self._path(e)
            if path: hit('N3',e.sender,path+[e],facts={'path_ids':[h.transaction_id for h in path]})
        eligible['N4']=e.kind in ('wallet_to_wallet','cash_out')
        if eligible['N4']:
            inflow=recent(self.inflows[w],t,DAY)
            if inflow:
                anchor=inflow[0]; funding=inflow+[h for h in prior if h.kind=='cash_in' and h.key>=anchor.key]
                outward=[h for h in prior if h.kind in ('wallet_to_wallet','cash_out') and h.key>anchor.key]+[e]
                F=sum(h.amount for h in funding); O=sum(h.amount for h in outward)
                if F>=10000 and F<=2*O<=2*F and e.amount<=F-(O-e.amount):
                    hit('N4',w,funding+outward,facts={'anchor_id':anchor.transaction_id,'funding_minor':F,'outward_minor':O})
        for f in ('A1','A2','A3','A4'): eligible[f]=False
        if e.agent:
            a=e.agent; ah=self.service[a]
            ar7=recent(ah,t,7*DAY)+[e]; ab7=baseline(ah,t,7*DAY)
            wallets={h.wallet for h in ar7}; old={h.wallet for h in ab7}; new=wallets-old
            buckets=[len({h.wallet for h in ab7 if t-(14+7*k)*DAY<h.t<=t-(7+7*k)*DAY}) for k in range(4)]
            if ready('A1',a,ab7,7*DAY,12,agent=True) and len(wallets)>=6 and len(new)>=4 and 2*len(new)>=len(wallets) and 2*len(wallets)>=3*max(1,median(buckets)):
                hit('A1',a,ar7,ab7)
            ar24=recent(ah,t,DAY)+[e]; ab24=baseline(ah,t,DAY)
            a2ok=ready('A2',a,ab24,DAY,20,agent=True) and len({h.wallet for h in ab24})>=5
            eligible['A2']=a2ok
            if a2ok and len(ar24)>=8 and top2(ar24)>=Fraction(13,20) and top2(ar24)-top2(ab24)>=Fraction(1,5):
                hit('A2',a,ar24,ab24)
            ar1=recent(ah,t,HOUR)+[e]; ab1=baseline(ah,t,HOUR)
            if ready('A3',a,ab1,HOUR,12,agent=True) and len(ar1)>=5 and len({h.wallet for h in ar1})>=3 and len(ar1)*672>=3*len(ab1):
                hit('A3',a,ar1,ab1)
            cash=[h for h in ar24 if h.kind!='wallet_to_wallet']; bcash=[h for h in ab24 if h.kind!='wallet_to_wallet']
            a4ok=e.kind!='wallet_to_wallet' and ready('A4',a,ab24,DAY,12,agent=True) and len(bcash)>=8
            eligible['A4']=a4ok
            if a4ok and len(cash)>=6 and len({h.wallet for h in cash})>=3:
                v,c=skew(cash),skew(cash,False)
                if abs(v)>=Fraction(3,5) and abs(c)>=Fraction(1,2) and v*c>0 and abs(v-skew(bcash))>=Fraction(2,5):
                    hit('A4',a,cash,ab24)
        self.activity[w].append(e)
        for wallet in {e.sender,e.receiver}: self.first_wallet.setdefault(wallet,t)
        if e.kind=='wallet_to_wallet':
            self.inflows[e.receiver].append(e); self.outflows[e.sender].append(e)
        if e.agent:
            self.service[e.agent].append(e); self.first_agent.setdefault(e.agent,t)
        self.last_key=e.key; self.ids.add(e.transaction_id)
        return {'transaction_id':e.transaction_id,'decision_point_target':int(bool(witness)),
                'families':sorted(witness),'witnesses':witness,'baseline_eligibility':eligible}
