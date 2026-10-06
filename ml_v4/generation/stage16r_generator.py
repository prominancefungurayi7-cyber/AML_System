"""Fixed-law opportunity generator. Never imports or calls the target evaluator."""
from __future__ import annotations
import hashlib
import hmac
import math
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict,Counter
import numpy as np
from stage16r_contract import Event, DAY, HOUR, FAMILIES, timestamp, validate_event

DATASET='mobile_money_aml_synthetic_100k_v4'
SEED=2026092915
STREAMS='entities profiles catchments warmup background episodes amounts timestamps transaction_ids accounting'.split()
ARCHETYPES='low_volume_stable medium_volume_stable high_volume_urban_like growing_legitimate seasonal concentrated_repeat_customer broad_customer_base volatile_legitimate'.split()
PROFILES='low_frequency_personal regular_transfer cash_heavy recurring_payment high_activity collection_like dispersion_like'.split()
MATCHES={'H1':['S1','S3'],'H2':['S2'],'H3':['S4'],'H4':['N1'],'H5':['N2','N4'],'H6':['N3'],'H7':['A1','A3'],'H8':['A2','A4']}
RANGES={'S1':(4,12),'S2':(4,12),'S3':(6,16),'S4':(5,12),'N1':(4,12),'N2':(4,12),'N4':(2,20),'A1':(8,20),'A2':(8,20),'A3':(5,16),'A4':(8,20)}
CONTEXT=['baseline_compatible','interleaved_unrelated','relationship_maintenance','post_motif_ordinary']


def streams(partition,unit,salt=None):
    answer={}
    for stream in STREAMS:
        if salt is None:
            if partition not in ('train','validation'): raise PermissionError('Holdout requires custodian salt')
            digest=hashlib.sha256(f'{DATASET}|{SEED}|{partition}|{stream}/unit/{unit}'.encode()).digest()
        else:
            if partition not in ('final_test','independent_evaluation'): raise PermissionError('Salt only for evaluation')
            digest=hmac.new(salt,f'{DATASET}|{partition}|{stream}|{unit}'.encode(),hashlib.sha256).digest()
        answer[stream]=np.random.Generator(np.random.PCG64DXSM(int.from_bytes(digest[:16],'little')))
    return answer


def base_amount(rng):
    while True:
        x=float(rng.lognormal(math.log(35 if rng.random()<.9 else 1800),1))
        if .01<=x<=15000: return x


def large_amount(rng):
    while True:
        x=base_amount(rng)
        if 5000<=x<=13000: return x


def bounded_shift(x):
    if not 5000<=x<=13000: raise ValueError('Recipe amount outside support')
    if x in (5000,13000): return x
    u=(math.log(x)-math.log(5000))/math.log(13000/5000)
    y=math.exp(math.log(x)+4*math.log(1.15)*u*(1-u))
    if not 5000<=y<=13000: raise ArithmeticError('Bounded shift range failure')
    return y


def cents(x):
    return int((Decimal(repr(float(x)))*Decimal(100)).quantize(Decimal(1),rounding=ROUND_HALF_UP))


def motif_count(rng,family,e):
    if family=='N3':
        v=int(rng.integers(2,7)); k=int(rng.integers(0,min(2,e-v)+1))
        return v+k,{'V':v,'K':k}
    lo,hi=RANGES[family]
    return int(rng.integers(lo,min(e,hi)+1)),{}


def allocate(total,names,weights):
    divisor=sum(weights)
    counts={n:total*w//divisor for n,w in zip(names,weights)}
    remainder=total-sum(counts.values())
    ranked=sorted(range(len(names)),key=lambda i:(-(total*weights[i]%divisor),i))
    for i in ranked[:remainder]: counts[names[i]]+=1
    return counts


def truncated_weight(rng,median,sd,lo,hi):
    while True:
        x=float(rng.lognormal(math.log(median),sd))
        if lo<=x<=hi: return x


class Unit:
    def __init__(self,partition,index,salt=None,independent_arch=None,fixture_streams=None):
        self.partition,self.index=partition,index
        self.independent=partition=='independent_evaluation'
        self.rng=fixture_streams if fixture_streams is not None else streams(partition,index,salt)
        r=self.rng['profiles']; ent=self.rng['entities']
        profile_counts=[20,18,20,12,10,10,10] if self.independent else [25,20,15,15,10,8,7]
        profiles=[n for n,c in zip(PROFILES,profile_counts) for _ in range(c)]
        r.shuffle(profiles)
        late=set(int(x) for x in r.choice(100,10,replace=False))
        medians=dict(zip(PROFILES,[.5,1,1,1,2,1.5,1.5]))
        self.wallets=[]
        for i,name in enumerate(profiles):
            self.wallets.append({'id':ent.bytes(16).hex(),'profile':name,'weight':truncated_weight(r,medians[name],.7,.1,5),'activation':int(r.uniform(42,102)*DAY) if i in late else 0,'preferred_probability':float(r.uniform(.5,.85)),'recurring':name=='recurring_payment' or bool(r.random()<.2),'preferred':[]})
        self.by_wallet={w['id']:w for w in self.wallets}
        archetypes=list(independent_arch) if independent_arch is not None else list(ARCHETYPES)
        r.shuffle(archetypes)
        self.agents=[]
        for name in archetypes:
            j=ARCHETYPES.index(name)
            a={'id':ent.bytes(16).hex(),'archetype':name,'weight':truncated_weight(r,[.65,1,1.65,1,1,1,1.2,1][j],.6,.2,4),'repeat':float(np.clip(r.uniform([.8,.75,.65,.65,.7,.85,.55,.7][j]-.15,[.8,.75,.65,.65,.7,.85,.55,.7][j]+.15),.1,.95)),'retention':float(r.uniform(.8,.98)),'catchment':[],'shocks':[],'acquisition':[],'phase':float(r.uniform(0,2*math.pi)),'period':float(r.uniform(21,45)),'amplitude':float(r.uniform(.2,.5) if self.independent else r.uniform(.1,.4))}
            for _ in range(4 if name=='volatile_legitimate' else 2):
                cause=int(r.integers(0,5)); lo,hi=[(7,28),(1,3),(21,45),(1,7),(7,28)][cause]
                duration=float(r.uniform(lo,hi)); start=float(r.uniform(42,222-duration))
                ml,mh=[(1.1,2.2),(1.1,2),(.6,1.6),(1.1,2),(.6,1.8)][cause]
                a['shocks'].append({'cause':cause,'start':start,'end':start+duration,'factor':float(r.uniform(ml,mh)),'phase':float(r.uniform(0,2*math.pi))})
            if name=='growing_legitimate':
                for _ in range(2):
                    duration=float(r.uniform(14,42)); start=float(r.uniform(42,222-duration))
                    a['acquisition'].append({'start':start,'end':start+duration,'factor':float(r.uniform(1.1,1.8)),'repeat_drop':float(r.uniform(.05,.15))})
            self.agents.append(a)
        for j,a in enumerate(self.agents):
            for shock in a['shocks']:
                if shock['cause']==3: shock['source_agent']=self.agents[int(r.choice([k for k in range(8) if k!=j]))]['id']
        self.by_agent={a['id']:a for a in self.agents}
        self.week=-1
        self.service_history=defaultdict(list)
        self.cash_history=defaultdict(list)
        self.activity_history=defaultdict(list)
        self.relationships=defaultdict(set)
        self.cache={}
        self.plans=[]
        self.episode_audit=[]
        self.amount_rejections=0
        self.ledger_wallet={w['id']:100000000 for w in self.wallets}
        self.ledger_electronic={a['id']:200000000 for a in self.agents}
        self.ledger_cash=dict(self.ledger_electronic)
        self.min_inventory=100000000
        self.context_fallbacks=0

    def choose(self,items,weights=None,stream='background'):
        if not items: raise RuntimeError('Empty active candidate pool')
        p=None if weights is None else np.array(weights,dtype=float)/sum(weights)
        return items[int(self.rng[stream].choice(len(items),p=p))]

    def active(self,t):
        return [w['id'] for w in self.wallets if w['activation']<=t]

    def update_population(self,t):
        r=self.rng['catchments']
        # Process each weekly boundary at its own time, never at a later event's age.
        while self.week<t//(7*DAY):
            self.week+=1
            active=self.active(self.week*7*DAY)
            for a in self.agents:
                kept=[w for w in a['catchment'] if r.random()<a['retention']]
                pool=[w for w in active if w not in kept]
                a['catchment']=kept+[str(x) for x in r.choice(pool,20-len(kept),replace=False)]
            for w in self.wallets:
                if w['id'] not in active: continue
                kept=[x for x in w['preferred'] if x in active and r.random()<.95]
                pool=[x for x in active if x!=w['id'] and x not in kept]
                w['preferred']=kept+[str(x) for x in r.choice(pool,5-len(kept),replace=False)]
        for w in self.wallets:
            if w['activation']<=t and not w['preferred']:
                w['preferred']=[str(x) for x in r.choice([x for x in self.active(t) if x!=w['id']],5,replace=False)]

    def wallet(self,t,exclude=(),role=None):
        active=[x for x in self.active(t) if x not in exclude]
        weights=[self.by_wallet[x]['weight']*(1.5 if self.by_wallet[x]['profile']==role else 1) for x in active]
        return self.choose(active,weights)

    def counterparty(self,w,t):
        r=self.rng['background']; active=[x for x in self.active(t) if x!=w]
        pref=[x for x in self.by_wallet[w]['preferred'] if x in active]
        pool=pref if pref and r.random()<self.by_wallet[w]['preferred_probability'] else [x for x in active if x not in pref]
        return self.choose(pool or active,[self.by_wallet[x]['weight'] for x in (pool or active)])

    def agent_parameters(self,t):
        day=t/DAY; weights=[]; repeats=[]
        for a in self.agents:
            factor=1.; repeat=a['repeat']
            if a['archetype']=='seasonal': factor*=1+a['amplitude']*math.sin(2*math.pi*day/a['period']+a['phase'])
            for s in a['shocks']:
                if s['start']<=day<=s['end']:
                    if s['cause']==2:
                        factor*=(1+s['factor'])/2+(s['factor']-1)/2*math.sin(2*math.pi*(day-s['start'])/(s['end']-s['start'])+s['phase'])
                    elif s['cause']!=3: factor*=s['factor']
                    if s['cause']==0: repeat-=.1
                    if s['cause']==1: repeat+=.1
            for q in a['acquisition']:
                if q['start']<=day<=q['end']:
                    factor*=1+(q['factor']-1)*(day-q['start'])/(q['end']-q['start']); repeat-=q['repeat_drop']
                elif q['end']<day<q['end']+7: factor*=1+(q['factor']-1)*(1-(day-q['end'])/7)
            for eid,state in self.cache.items():
                if state['agent']==a['id'] and state.get('activity_interval') and state['activity_interval'][0]<=t<=state['activity_interval'][1]:
                    factor*=state['activity_factor']
            weights.append(a['weight']*min(3,max(.25,factor)))
            repeats.append(min(.95,max(.1,repeat)))
        # Customer migration transfers demand; it never creates unit demand.
        for j,a in enumerate(self.agents):
            for s in a['shocks']:
                if s['cause']==3 and s['start']<=day<=s['end']:
                    k=next(i for i,x in enumerate(self.agents) if x['id']==s['source_agent'])
                    transfer=max(0,min(weights[k]-.25*self.agents[k]['weight'],3*a['weight']-weights[j],max(0,(s['factor']-1)*weights[j])))
                    weights[k]-=transfer; weights[j]+=transfer
        return weights,repeats

    def agent(self,t):
        weights,_=self.agent_parameters(t)
        return self.choose([a['id'] for a in self.agents],weights)

    def customer(self,a,t,repeat=None):
        agent=self.by_agent[a]
        if repeat is None: repeat=self.agent_parameters(t)[1][self.agents.index(agent)]
        active=self.active(t)
        regular=[x for x in agent['catchment'] if x in active]
        # An active migration opportunity inherits the source agent's customers.
        for s in agent['shocks']:
            if s['cause']==3 and s['start']<=t/DAY<=s['end']:
                regular=list(dict.fromkeys(regular+self.by_agent[s['source_agent']]['catchment']))
        pool=regular if self.rng['background'].random()<repeat else [x for x in active if x not in regular]
        return self.choose(pool or active,[self.by_wallet[x]['weight'] for x in (pool or active)])

    def duration(self,f):
        r=self.rng['timestamps']
        lo,hi={'S1':(5/1440,1/24),'S2':(1,7),'S3':(3/24,20/24),'S4':(1,7),'N1':(1/24,1),'N2':(1/24,1),'N3':(1/24,7),'N4':(1/24,1),'A1':(2,28),'A2':(2/24,1),'A3':(.25/24,3/24),'A4':(2/24,1)}[f]
        return int(r.uniform(lo,hi)*DAY)

    def plan_episode(self,origin,e):
        r=self.rng['episodes']; rt=self.rng['timestamps']
        f=str(r.choice(MATCHES[origin])) if origin in MATCHES else origin
        m,graph=motif_count(r,f,e); contexts=e-m; d=self.duration(f)
        head,tail=(float(rt.uniform(.05,.25)),float(rt.uniform(.05,.25))) if contexts else (0.,0.)
        duration=int((1+head+tail)*d)
        start=int(rt.integers(42*DAY,222*DAY-duration))
        ms,me=start+int(head*d),start+int(head*d)+d
        times=np.sort(rt.integers(ms,me+1,m)).tolist()
        if m>1: times[0],times[-1]=ms,me
        if f=='S3':
            hours=int(r.integers(3,min(8,m,max(3,int(d/HOUR)+1))+1))
            points=np.linspace(ms,me,hours).astype('int64').tolist()
            times=sorted(points+[int(rt.integers(ms,me+1)) for _ in range(m-hours)])
            if origin=='H1':
                # Two occupied-hour opportunities spread across the motif interval.
                times=sorted([ms if j%2==0 else me for j in range(m)])
        if origin in ('H2','H3'):
            times=sorted(int(x) for x in np.linspace(ms,me,m))
        if f=='N3' and r.random()<(.8 if origin=='H6' else .2):
            v=graph['V']
            if v>2: times[0],times[1]=times[1],times[0]
        eid=f'{self.index}:{len(self.episode_audit)}'
        plan={'id':eid,'origin':origin,'family':f,'E':e,'M':m,'start':start,'motif_start':ms,'motif_end':me,'end':start+duration,'strength':float(r.uniform(.1,.9)),**graph}
        self.episode_audit.append(plan)
        for j,t in enumerate(times): self.plans.append({'t':t,'episode':eid,'role':'motif','j':j,'plan':plan})
        for _ in range(contexts):
            role=str(r.choice(CONTEXT))
            low=me+1 if role=='post_motif_ordinary' else start
            t=int(rt.integers(low,start+duration+1))
            self.plans.append({'t':t,'episode':eid,'role':'context','context_role':role,'plan':plan})

    def schedule(self):
        r=self.rng['episodes']; rt=self.rng['timestamps']; rb=self.rng['background']
        budgets=allocate(2000,FAMILIES,[2 if f in ('S2','S4','N3') else 1 for f in FAMILIES])
        budgets.update(allocate(1250 if self.independent else 1000,list(MATCHES),[1]*8))
        residual=0
        for origin,budget in budgets.items():
            while budget>=8:
                e=int(r.integers(8,min(20,budget)+1)); self.plan_episode(origin,e); budget-=e
            residual+=budget
        background_target=(1750 if self.independent else 2000)+residual
        normal=[]
        # Reserved cold-start observation is a background opportunity at its fixed activation time.
        for w in self.wallets:
            if w['activation']:
                normal.append({'t':w['activation'],'fixed_wallet':w['id'],'activation':True})
            if w['recurring']:
                period=int(rb.choice([7,30]))*DAY
                phase=int(rt.integers(0,period))
                base=base_amount(self.rng['amounts'])
                for time in range(w['activation']+phase,222*DAY,period):
                    t=time+int(rt.uniform(-12,12)*HOUR)
                    if max(0,w['activation'])<=t<222*DAY:
                        normal.append({'t':t,'fixed_wallet':w['id'],'recurring_base':base})
        warm=[p for p in normal if p['t']<42*DAY]; scored=[p for p in normal if p['t']>=42*DAY]
        if len(warm)>1200 or len(scored)>background_target: raise RuntimeError('Recurring opportunities exceed frozen background budget')
        warm += [{'t':int(rt.integers(0,42*DAY))} for _ in range(1200-len(warm))]
        scored += [{'t':int(rt.integers(42*DAY,222*DAY))} for _ in range(background_target-len(scored))]
        for p in warm+scored:
            self.plans.append(p | {'role':'background','episode':None})
        ids=set()
        for p in self.plans:
            ident=int(self.rng['transaction_ids'].integers(1,2**63))
            if ident in ids: raise RuntimeError('Transaction ID collision; no silent replacement')
            ids.add(ident); p['id']=ident
        self.plans.sort(key=lambda p:(p['t'],p['id']))
        if len(self.plans)!=6200: raise RuntimeError('Unit count mismatch')
        self.residual=residual

    def episode_state(self,p):
        eid=p['episode']
        if eid in self.cache: return self.cache[eid]
        plan=p['plan']; f=plan['family']; t=p['t']; r=self.rng['episodes']; ra=self.rng['amounts']
        focal=self.wallet(t,role='collection_like' if f=='N1' else 'dispersion_like' if f in ('N2','N4') else None)
        if plan['origin'] in ('H2','H3'):
            recurring=[w['id'] for w in self.wallets if w['activation']<=t and w['recurring']]
            focal=self.choose(recurring) if recurring else focal
        agent=self.agent(t)
        available=[w for w in self.active(t) if w!=focal]
        breadth=int(r.integers(2,9))
        if plan['origin']=='H4' or (plan['origin']=='H7' and f=='A3'): breadth=2
        partners=[str(x) for x in r.choice(available,breadth,replace=False)]
        if f=='N3': partners=[str(x) for x in r.choice(available,plan['V']-1,replace=False)]
        m=plan['M']
        # Frozen numerical support rejection of the entire related amount proposal.
        while True:
            amounts=[base_amount(ra) for _ in range(m)]
            if f=='S4': amounts=[large_amount(ra) for _ in range(m)]
            elif f=='S1':
                alpha=[1.]*m
                if plan['origin']=='H1': alpha[0]=8.
                amounts=(ra.dirichlet(alpha)*base_amount(ra)).tolist()
            elif f=='S2':
                prior=[value for time,value in self.activity_history[focal] if t-35*DAY<time<=t-7*DAY]
                anchor=self.choose(prior,stream='amounts')/100 if plan['origin']=='H2' and prior else base_amount(ra)
                sd=float(ra.uniform(.01,.15)); amounts=(anchor*ra.lognormal(0,sd,m)).tolist()
            elif f=='N3':
                for j in range(1,m): amounts[j]=amounts[j-1]*math.exp(float(ra.uniform(math.log(.15),math.log(5))))
            elif f=='N4':
                fraction=float(ra.uniform(.1,1.2)); amounts=[amounts[0]]+(ra.dirichlet([1.]*(m-1))*amounts[0]*fraction).tolist()
            if f=='A4':
                direction_factor=float(ra.uniform(.5,2))
                # Direction assignment is independent of amount sampling and held for this proposal.
                probability=float(r.uniform(.1,.9))
                history=[direction for time,direction in self.cash_history[agent] if t-28*DAY<time<t]
                if plan['origin']=='H8' and history:
                    out=sum(x=='cash_out' for x in history)
                    probability=.5+abs(probability-.5)*(1 if out>=len(history)/2 else -1)
                directions=['cash_out' if r.random()<probability else 'cash_in' for _ in range(m)]
                amounts=[x*(direction_factor if direction=='cash_out' else 1) for x,direction in zip(amounts,directions)]
            if self.independent: amounts=[bounded_shift(x) if f=='S4' else x*1.15 for x in amounts]
            if all(.01<=x<=15000 and 1<=cents(x)<=1500000 for x in amounts): break
            self.amount_rejections+=1
        amounts=[cents(x) for x in amounts]
        state={'focal':focal,'agent':agent,'partners':partners,'amounts':amounts,'repeat':float(r.uniform(.2,.9)),'concentration':float(r.uniform(.35,.90)),'concentrated':int(r.integers(2,7))}
        if f=='A1':
            state['activity_interval']=[plan['motif_start'],plan['motif_end']]
            state['activity_factor']=float(r.uniform(.8,2.5))
        if f=='A4': state['directions']=directions
        if f=='N3':
            vertices=[focal]+partners
            pairs=list(zip(vertices[:-1],vertices[1:]))+[(vertices[-1],vertices[0])]
            primary=int(r.integers(0,plan['V']-1))
            if plan['K']==1: pairs.append(pairs[primary])
            elif plan['K']==2:
                other=self.wallet(t,exclude=vertices); left,right=pairs[primary]; pairs += [(left,other),(other,right)]
            state['pairs']=pairs
        if f=='A2':
            regular=self.by_agent[agent]['catchment']
            prior=Counter(w for time,w in self.service_history[agent] if t-28*DAY<time<t)
            if plan['origin']=='H8' and len(prior)>=state['concentrated']:
                state['concentration_wallets']=[w for w,_ in prior.most_common(state['concentrated'])]
            else: state['concentration_wallets']=[str(x) for x in r.choice(regular,state['concentrated'],replace=False)]
        self.cache[eid]=state
        return state

    def ordinary_amount(self,p):
        r=self.rng['amounts']
        while True:
            x=p['recurring_base']*float(r.lognormal(0,.08)) if 'recurring_base' in p else base_amount(r)
            if self.independent: x*=1.15
            if .01<=x<=15000: return cents(x)
            self.amount_rejections+=1

    def make_event(self,p):
        t=p['t']; r=self.rng['background']; self.update_population(t)
        state=self.episode_state(p) if p['episode'] else None
        typ=None; sender=None; receiver=None; named_agent=None; serviced=None
        if p['role']=='motif':
            plan=p['plan']; f=plan['family']; j=p['j']; amount=state['amounts'][j]; focal=state['focal']
            if f in ('N1','N2'):
                other=state['partners'][j%len(state['partners'])]; sender,receiver=(other,focal) if f=='N1' else (focal,other); typ='wallet_to_wallet'
            elif f=='N3': sender,receiver=state['pairs'][j]; typ='wallet_to_wallet'
            elif f=='N4':
                if j==0: sender,receiver=self.counterparty(focal,t),focal; typ='wallet_to_wallet'
                else: sender=focal; typ='wallet_to_wallet' if r.random()<.5 else 'cash_out'
            elif f.startswith('A'):
                named_agent=state['agent']
                if f=='A1':
                    seen=[w for _,w in self.service_history[named_agent] if w in self.active(t)]
                    serviced=self.choose(sorted(set(seen))) if plan['origin']=='H7' and seen else self.customer(named_agent,t,state['repeat'])
                elif f=='A2': serviced=self.choose(state['concentration_wallets']) if r.random()<state['concentration'] else self.wallet(t,exclude=state['concentration_wallets'])
                else: serviced=state['partners'][j%len(state['partners'])]
                if f=='A4': typ=state['directions'][j]
                sender=serviced
            else: sender=focal
        else:
            amount=self.ordinary_amount(p)
            sender=p.get('fixed_wallet')
            if state:
                role=p['context_role']; sender=state['focal']
                if role=='interleaved_unrelated': sender=self.wallet(t,exclude=[sender])
                elif role=='relationship_maintenance':
                    candidates=sorted(self.relationships[sender].intersection(self.active(t)))
                    if candidates: receiver=self.choose(candidates)
                    else: self.context_fallbacks+=1
            if sender is None:
                named_agent=self.agent(t); sender=self.customer(named_agent,t)
        if sender is None: sender=self.wallet(t)
        if typ is None:
            probs=np.array([.45,.275,.275] if self.independent else [.5,.25,.25])
            profile=self.by_wallet[sender]['profile']
            if profile=='cash_heavy': probs[1:]*=1.5
            if profile=='regular_transfer': probs[0]*=1.5
            typ=str(r.choice(['wallet_to_wallet','cash_in','cash_out'],p=probs/probs.sum()))
        if typ=='wallet_to_wallet':
            if receiver is None: receiver=self.counterparty(sender,t)
            assisted=bool(named_agent and p['role']=='motif' and p['plan']['family'].startswith('A')) or r.random()<(.45 if self.independent else .35)
            if assisted:
                named_agent=named_agent or self.agent(t)
                if serviced:
                    other=receiver
                    sender,receiver=(serviced,other) if r.random()<.5 else (other,serviced)
                else: serviced=sender if r.random()<.5 else receiver
            else: named_agent,serviced='',''
            direction='none'; channel='agent' if assisted else 'direct_wallet'
        else:
            named_agent=named_agent or self.agent(t); serviced=serviced or sender
            sender=receiver=serviced; direction=typ; channel='agent'
        e=Event(p['id'],timestamp(t),sender,receiver,amount,'USD',typ,channel,named_agent,serviced,direction)
        validate_event(e)
        if any(self.by_wallet[x]['activation']>t for x in (sender,receiver)): raise RuntimeError('Pre-activation event')
        if typ=='wallet_to_wallet': self.ledger_wallet[sender]-=amount; self.ledger_wallet[receiver]+=amount
        elif typ=='cash_in': self.ledger_wallet[sender]+=amount; self.ledger_electronic[named_agent]-=amount; self.ledger_cash[named_agent]+=amount
        else: self.ledger_wallet[sender]-=amount; self.ledger_electronic[named_agent]+=amount; self.ledger_cash[named_agent]-=amount
        values=[self.ledger_wallet[sender],self.ledger_wallet[receiver]]+([self.ledger_electronic[named_agent],self.ledger_cash[named_agent]] if named_agent else [])
        if min(values)<0: raise RuntimeError('ACCOUNTING_CAPACITY_FAILURE; retain draw; no retry')
        self.min_inventory=min(self.min_inventory,min(values))
        if named_agent: self.service_history[named_agent].append((t,serviced))
        self.activity_history[e.subject].append((t,amount))
        if typ!='wallet_to_wallet': self.cash_history[named_agent].append((t,typ))
        if sender!=receiver: self.relationships[sender].add(receiver); self.relationships[receiver].add(sender)
        plan=p.get('plan',{})
        provenance={'transaction_id':e.transaction_id,'scenario_id':p['episode'],'scenario_family':plan.get('family'),'campaign_id':p['episode'],'origin':plan.get('origin','background'),'strength':plan.get('strength'),'archetype':self.by_agent[named_agent]['archetype'] if named_agent else None,'profile':self.by_wallet[e.subject]['profile'],'population_unit':self.index,'activation_schedule':self.by_wallet[e.subject]['activation'],'intended_onset':plan.get('motif_start'),'event_role':p['role'] if p['episode'] else None,'context_role':p.get('context_role')}
        return e,provenance

    def generate(self):
        self.schedule(); events=[]; provenance=[]
        for p in self.plans:
            e,meta=self.make_event(p); events.append(e); provenance.append(meta)
        return events,provenance,{'wallets':self.wallets,'agents':self.agents,'episodes':self.episode_audit,'residual_background':self.residual,'amount_rejections':self.amount_rejections,'context_fallbacks':self.context_fallbacks,'minimum_inventory_minor':self.min_inventory}


def generate_partition(name,units,salt=None):
    events=[]; provenance=[]; populations=[]
    independent=None
    if name=='independent_evaluation':
        independent=[a for a,n in zip(ARCHETYPES,[1,2,2,3,3,2,2,1]) for _ in range(n)]
        streams(name,0,salt)['profiles'].shuffle(independent)
    for i in range(units):
        unit=Unit(name,i,salt,independent[i*8:(i+1)*8] if independent else None)
        e,p,meta=unit.generate(); events+=e; provenance+=p; populations.append(meta)
    entities=[x['id'] for pop in populations for kind in ('wallets','agents') for x in pop[kind]]
    if len(entities)!=len(set(entities)) or len({e.transaction_id for e in events})!=len(events): raise RuntimeError('Partition ID collision')
    events.sort(key=lambda e:e.key)
    provenance.sort(key=lambda p:p['transaction_id'])
    return events,provenance,populations
