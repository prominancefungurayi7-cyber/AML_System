"""Standalone, precommitted synthetic scenario generator. No application imports."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import random

from contracts import (ROOT, PARTITIONS, DEVELOPMENT, EVENT_FIELDS, TRUTH_FIELDS,
                      WALLET_FIELDS, AGENT_FIELDS, BASIS, safe_path, write_csv,
                      write_json, partition_path, digest)

DAY = 86400
START = datetime(2025, 1, 1, tzinfo=timezone.utc)


def stamp(seconds):
    return (START + timedelta(seconds=seconds)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')


def rng_for(seed, name):
    return random.Random(int.from_bytes(hashlib.sha256(f'{seed}:{name}'.encode()).digest(), 'big'))


def opaque(rng, prefix):
    return prefix + f'{rng.getrandbits(128):032x}'


def load_design():
    return tuple(json.loads((ROOT/'design'/f'{name}.json').read_text(encoding='utf-8'))
                 for name in ('allocation_manifest','scenario_manifest','dataset_schema'))


def assign_event_order(events):
    events.sort(key=lambda e:(e['event_timestamp'],e['_tie']))
    for i,event in enumerate(events,1):
        event['transaction_id']=event['event_sequence']=i


def pack_positive(quota, specs, rng):
    """Commit episode labels, strengths, lengths and block quotas before facts exist."""
    for attempt in range(1000):
        remaining = {(f,s):n for f in specs for s,n in quota['family_strength'].items()}
        plans = []
        failed = False
        for block, budget in enumerate(quota['positive_blocks']):
            while budget:
                options = []
                for (f,s), left in remaining.items():
                    lo, hi = specs[f]['min_events'], specs[f]['max_events']
                    lengths = [n for n in range(lo,min(hi,left,budget)+1)
                               if (left-n == 0 or left-n >= lo) and (budget-n == 0 or budget-n >= 4)]
                    if lengths:
                        options.append((f,s,lengths))
                if not options:
                    failed = True
                    break
                f,s,lengths = rng.choice(options)
                n = rng.choice(lengths)
                plans.append({'family':f,'strength':s,'size':n,'block':block,'target':1})
                remaining[f,s] -= n
                budget -= n
            if failed:
                break
        if not failed and not any(remaining.values()):
            return plans
    raise RuntimeError('Cannot pack complete positive episodes; no events emitted')


def lengths(total, lo, hi, rng):
    result = []
    while total:
        options = [n for n in range(lo,min(hi,total)+1) if total-n == 0 or total-n >= lo]
        if not options:
            raise ValueError('Infeasible complete episode budget')
        n = rng.choice(options)
        result.append(n)
        total -= n
    return result


def assign_categories(plans, budgets, rng):
    """Allocate exact category margins without deleting or truncating any event."""
    for family, counts in budgets.items():
        members = [p for p in plans if p['family'] == family]
        remaining = list(counts)
        for p in members:
            p['categories'] = []
            pattern = p['pattern']
            if pattern=='A4':
                dominant=rng.choice([c for c in (0,1) if remaining[c]>=2 and remaining[1-c]>=1])
                for c in (dominant,dominant,1-dominant):
                    p['categories'].append(c)
                    remaining[c]-=1
            required = 3 if pattern in ('N1','N2') else (2 if pattern in ('N3','N4') else 0)
            for _ in range(required):
                candidates = [i for i in (2,3) if remaining[i]]
                if not candidates:
                    raise ValueError('Insufficient graph edges in family allocation')
                c = rng.choices(candidates,weights=[remaining[i] for i in candidates])[0]
                p['categories'].append(c)
                remaining[c] -= 1
        pool = [i for i,n in enumerate(remaining) for _ in range(n)]
        rng.shuffle(pool)
        for p in members:
            n = p['size']-len(p['categories'])
            p['categories'].extend(pool[-n:] if n else [])
            if n:
                del pool[-n:]
            rng.shuffle(p['categories'])
        assert not pool


def amount(rng, independent=False):
    # Rejection sampling of the common support, no clipping point masses.
    if rng.random() < 0.25:
        value = rng.randint(100,2500000)
    else:
        while True:
            value = round(rng.lognormvariate(9.0 + (0.08 if independent else 0),1.6))
            if 100 <= value <= 2500000:
                break
    if rng.random() < 0.35:
        value = max(100, round(value/100)*100)
    return value


def generate(destination, seed=20260921):
    destination = safe_path(destination)
    if destination.exists():
        raise FileExistsError('Dataset destination already exists; version overwrite refused')
    allocation, scenarios, schema = load_design()
    # Files are written only once all plans and event facts have been constructed.
    all_events, all_truth, entities, all_plans, commitments = [], {}, {}, {}, {}
    tie_rng = rng_for(seed,'global-tie-keys')
    for partition in PARTITIONS:
        q = allocation['partitions'][partition]
        rng = rng_for(seed,partition)
        erng = rng_for(seed,partition+':entities')
        wallets, agents = [], []
        profiles = [p for p,n in zip(('personal','small_business','merchant','seasonal_income'),q['wallet_profiles']) for _ in range(n)]
        erng.shuffle(profiles)
        for profile in profiles:
            activation = erng.uniform(-365*DAY,-DAY) if erng.random() < .9 else erng.uniform(0,20*DAY)
            wallets.append(dict(zip(WALLET_FIELDS,[opaque(erng,'v2w_'),opaque(erng,'v2c_'),partition,profile,
                erng.choice(['lower','medium','higher']),scenarios['initial_liquidity']['wallet_minor'],stamp(activation)])))
        bands = [b for b,n in zip(('lower','medium','higher'),q['agent_bands']) for _ in range(n)]
        erng.shuffle(bands)
        for band in bands:
            agents.append(dict(zip(AGENT_FIELDS,[opaque(erng,'v2a_'),partition,band,
                scenarios['initial_liquidity']['agent_minor'],stamp(erng.uniform(-365*DAY,-DAY))])))
        entities[partition] = (wallets,agents)
        wallet_ids = [w['wallet_id'] for w in wallets]
        agent_ids = [a['agent_id'] for a in agents]
        agent_weights=[{'lower':.5,'medium':1,'higher':2}[a['activity_band']] for a in agents]
        activation = {w['wallet_id']:(datetime.strptime(w['activation_timestamp'],'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)-START).total_seconds() for w in wallets}
        service_history = defaultdict(list)

        def emit(t, sender, receiver, value, category, agent, truth, service_sender=False):
            handle = opaque(rng,'v2e_')
            kind = ['cash_in','cash_out','wallet_to_wallet','wallet_to_wallet'][category]
            if category < 2:
                receiver = sender
            serviced = (sender if category < 2 or service_sender or rng.random()<.5 else receiver) if category != 3 else ''
            agent = agent if category != 3 else ''
            event = dict(zip(EVENT_FIELDS,[0,0,stamp(t),sender,receiver,value,'USD',kind,
                'agent' if category != 3 else 'direct_wallet',agent,serviced,['outbound','inbound','none','none'][category]]))
            event.update(_partition=partition,_handle=handle,_tie=tie_rng.getrandbits(128))
            all_events.append(event)
            all_truth[handle] = dict(transaction_id=0,label_basis=BASIS,**truth)
            if agent:
                service_history[agent].append((t,serviced))
            return handle

        positive = pack_positive(q,scenarios['families'],rng)
        for p in positive:
            p['pattern'] = p['family']
        hard = []
        for family, counts in q['hard_categories'].items():
            for n in lengths(sum(counts),6,24,rng):
                choices = scenarios['hard_counterparts'][family].split('/')
                hard.append(dict(family=family,strength='',size=n,target=0,pattern=rng.choice(choices)))
        assign_categories(positive,q['family_categories'],rng)
        assign_categories(hard,q['hard_categories'],rng)
        # Allocate hard episodes to blocks, leaving routine events to fill exact normal margins.
        normal_left = q['normal_blocks'].copy()
        rng.shuffle(hard)
        for p in hard:
            available = [b for b in range(6) if normal_left[b] >= p['size'] + (q['wallets'] if b == 0 else 0)]
            if not available:
                raise ValueError('Normal block allocation infeasible')
            p['block'] = rng.choice(available)
            normal_left[p['block']] -= p['size']
        for p in positive+hard:
            p['episode_id'] = opaque(rng,'v2p_')
        # Serialize the immutable membership ledger before ANY observable event is emitted.
        commitment = [{k:p[k] for k in ('episode_id','family','strength','size','block','target','pattern')}
                      for p in positive+hard]
        commitments[partition] = {'membership':commitment,
            'sha256':hashlib.sha256(json.dumps(commitment,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
            'stage':'committed in memory before materializing event facts; no downstream scores'}
        routine_pool = [c for c,n in enumerate(q['routine_categories']) for _ in range(n)]
        rng.shuffle(routine_pool)
        routine_truth = dict(target=0,primary_domain='',primary_family='',episode_id='',normal_family='routine',
                             normal_episode_id='',signal_strength='',episode_phase='not_applicable')
        # Every wallet receives an observable baseline inside the event budget, after activation.
        for i,w in enumerate(wallet_ids):
            t = max(0,activation[w])+rng.uniform(1,3600)
            c = routine_pool.pop()
            other = rng.choice([x for x in wallet_ids if x != w and activation[x] <= t])
            emit(t,w,other,amount(rng,partition=='independent'),c,agent_ids[i % len(agent_ids)],routine_truth)
            normal_left[0] -= 1
        for b,n in enumerate(normal_left):
            for _ in range(n):
                t = b*30*DAY + rng.uniform(0,30*DAY-1)
                eligible = [w for w in wallet_ids if activation[w] <= t]
                s,r = rng.sample(eligible,2)
                emit(t,s,r,amount(rng,partition=='independent'),routine_pool.pop(),rng.choices(agent_ids,weights=agent_weights)[0],routine_truth)
        assert not routine_pool
        plans = positive+hard
        for p in plans:
            spec = scenarios['families'][p['pattern']]
            coordination = scenarios['strength_settings'][p['strength']]['coordination'] if p['target'] else rng.uniform(.1,.8)
            # All tiers share full support; intensity changes its sampling probabilities only.
            draw = rng.random() ** (0.7+coordination)
            duration = spec['min_seconds']+(spec['max_seconds']-spec['min_seconds'])*draw
            if partition == 'independent':
                duration = min(spec['max_seconds'],max(spec['min_seconds'],duration*rng.uniform(.85,1.15)))
            p['continuation_days'] = 0
            if p['pattern'] in ('S1','S3') and rng.random()<.25:
                limit = 3 if p['pattern']=='S1' else min(4,p['size']//6-1)
                p['continuation_days'] = rng.randint(1,limit) if limit else 0
                duration += p['continuation_days']*DAY
            p['duration'] = duration
            b = p['block']
            lo = b*30*DAY + (2*DAY if b==0 else 0)
            p['start'] = rng.uniform(lo,(b+1)*30*DAY-duration-1)
            p['coordination'] = coordination
        plans.sort(key=lambda p:(p['start'],p['episode_id']))
        for p in plans:
            n, pattern, t0 = p['size'],p['pattern'],p['start']
            eligible = [w for w in wallet_ids if activation[w]+3600 < t0]
            agent = rng.choices(agent_ids,weights=agent_weights)[0]
            # Actual preceding service facts, never future events, guide relationship roles.
            seen = {w for t,w in service_history[agent] if t < t0}
            center = rng.choice(eligible)
            candidates = [w for w in eligible if w != center]
            cats = p['categories']
            transfer_count = sum(c >= 2 for c in cats)
            counterpart_count = rng.randint(3,min(12,transfer_count)) if pattern in ('N1','N2') else rng.randint(3,min(12,len(candidates)))
            counterparts = rng.sample(candidates,counterpart_count)
            if pattern == 'A1':
                # "New or infrequently served": count preceding service events within 30 days.
                frequency = Counter(w for t,w in service_history[agent] if t0-30*DAY <= t < t0)
                candidates.sort(key=lambda w:(frequency[w],rng.random()))
                count = rng.randint(4,min(16,n-1))
                counterparts = candidates[:count]
            if pattern == 'A2':
                counterparts = rng.sample(candidates,rng.randint(2,min(6,n//2)))
            # Coherent entry, graph movement, exit; ordinary transfers never move agent float.
            if pattern.startswith('N'):
                cats.sort(key=lambda c:0 if c==0 else (2 if c==1 else 1))
            elif pattern in ('S1','S3'):
                # Complete cash phases; some episodes include both directions and transfers.
                first = rng.choice([0,1])
                cats.sort(key=lambda c:0 if c==first else (1 if c>=2 else 2))
            if pattern=='A4':
                dominant=rng.choice([c for c in (0,1) if cats.count(c)>=2 and cats.count(1-c)>=1])
                for c in (dominant,dominant,1-dominant):
                    cats.remove(c)
                cats[:0]=[dominant,dominant,1-dominant]
            values = [amount(rng,partition=='independent') for _ in range(n)]
            if pattern=='A4':
                # Count dominance is 2/3 in a committed opening cash portion; value
                # dominance varies independently within the shared 60--95% support.
                for _ in range(10000):
                    if .60<=(values[0]+values[1])/sum(values[:3])<=.95:
                        break
                    values[:3]=[amount(rng,partition=='independent') for _ in range(3)]
                else:
                    raise ValueError('Cannot schedule feasible directional portion')
            if pattern == 'S1':
                total = rng.randint(max(30000,n*100),min(6000000,n*2500000))
                for _ in range(1000):
                    weights = [rng.gammavariate(.8,1) for _ in range(n)]
                    values = [100+int((total-n*100)*w/sum(weights)) for w in weights]
                    values[-1] += total-sum(values)
                    if max(values)<=2500000:
                        break
                else:
                    raise ValueError('Cannot compose bounded fragment amounts')
            if pattern == 'S2':
                anchor = amount(rng,partition=='independent')
                variation = rng.choice([.015,.04,.07,.2])
                for i in range(n):
                    if rng.random()<.85:
                        for _ in range(1000):
                            v = round(anchor*rng.uniform(1-variation,1+variation))
                            if 100<=v<=2500000:
                                values[i]=v
                                break
            if pattern == 'S4':
                count = rng.randint(math.ceil(n*.25),math.floor(n*.60))
                selected = set(rng.sample(range(n),count))
                for i in range(n):
                    if i in selected:
                        values[i] = rng.randint(700000,1050000)
                    else:
                        while 700000<=values[i]<=1050000:
                            values[i]=amount(rng,partition=='independent')
            if pattern == 'N4':
                # One transfer supplies the transit wallet, then partial onward transfer/cash-out.
                funding_index = next(i for i,c in enumerate(cats) if c>=2)
                out_indices = [i for i in range(funding_index+1,n)]
                incoming = sum(values[:funding_index+1])
                ratio = rng.uniform(.50,.98)
                total_out = round(incoming*ratio)
                if total_out < len(out_indices)*100 or total_out > len(out_indices)*2500000:
                    # Structural feasibility only: rescale committed funding amounts, retain target.
                    values[:funding_index+1] = [10000]*(funding_index+1)
                    incoming = sum(values[:funding_index+1])
                    total_out = round(incoming*ratio)
                shares = [100+(total_out-len(out_indices)*100)//len(out_indices)]*len(out_indices)
                shares[-1] += total_out-sum(shares)
                for i,v in zip(out_indices,shares):
                    values[i]=v
            # Include both endpoints of the planned interval; interior gaps vary continuously.
            offsets = [0.0]+sorted(rng.random() for _ in range(n-2))+[1.0]
            if pattern in ('S1','S3','A3'):
                clusters = rng.randint(2,min(4,n//2))
                offsets = sorted((rng.randrange(clusters)+rng.random()*.2)/clusters for _ in range(n))
                low,high = offsets[0],offsets[-1]
                offsets = [(x-low)/(high-low) for x in offsets]
            if pattern=='S1' and p['continuation_days']:
                base = p['duration']-p['continuation_days']*DAY
                offsets = [x*base/p['duration'] for x in offsets[:-1]]+[1.0]
            if pattern=='S3' and p['continuation_days']:
                days=p['continuation_days']+1
                base=p['duration']-(days-1)*DAY
                daily=[n//days+(d<n%days) for d in range(days)]
                seconds=[]
                for d,count in enumerate(daily):
                    fractions=[0]+sorted(rng.random() for _ in range(count-2))+[1]
                    seconds.extend(d*DAY+x*base for x in fractions)
                offsets=[x/p['duration'] for x in seconds]
            # N3 edges form complete reciprocal pairs or cycles, never an open final fragment.
            cycle_edges = []
            if pattern == 'N3':
                for size in lengths(transfer_count,2,6,rng):
                    nodes = rng.sample(eligible,size)
                    cycle_edges.extend(zip(nodes,nodes[1:]+nodes[:1]))
            graph_index = 0
            event_handles = []
            concentration_count = rng.randint(max(2,math.ceil(n*.35)),max(2,math.floor(n*.85))) if pattern=='A2' else 0
            role_wallets = []
            for i,c in enumerate(cats):
                s,r = center,counterparts[i % len(counterparts)]
                if pattern == 'N1':
                    s,r = (counterparts[graph_index % len(counterparts)],center) if c>=2 else ((counterparts[i%len(counterparts)],)*2 if c==0 else (center,center))
                elif pattern == 'N2':
                    s,r = (center,counterparts[graph_index % len(counterparts)]) if c>=2 else ((center,center) if c==0 else (counterparts[i%len(counterparts)],)*2)
                elif pattern == 'N3':
                    s,r = cycle_edges[graph_index] if c>=2 else (center,center)
                elif pattern == 'N4':
                    s,r = (counterparts[0],center) if i==funding_index else (center,counterparts[(i+1)%len(counterparts)])
                elif pattern.startswith('A'):
                    if pattern=='A1':
                        s = counterparts[i%len(counterparts)] if i<n-1 else (rng.choice(sorted(seen)) if seen else center)
                    elif pattern=='A2':
                        s = counterparts[i%len(counterparts)] if i<concentration_count else rng.choice([w for w in eligible if w not in counterparts])
                    else:
                        s = rng.choice(eligible)
                    r = rng.choice([w for w in eligible if w!=s])
                if c>=2:
                    graph_index += 1
                t = t0+offsets[i]*p['duration']
                phase = 'early' if i<math.ceil(n*.25) else ('late' if i>=n-math.ceil(n*.25) else 'established')
                truth = dict(target=p['target'],primary_domain=scenarios['families'][p['family']]['domain'] if p['target'] else '',
                    primary_family=scenarios['families'][p['family']]['name'] if p['target'] else '',
                    episode_id=p['episode_id'] if p['target'] else '',normal_family='' if p['target'] else p['family'],
                    normal_episode_id='' if p['target'] else p['episode_id'],signal_strength=p['strength'],episode_phase=phase)
                event_handles.append(emit(t,s,r,values[i],c,agent,truth,pattern.startswith('A')))
                role_wallets.append(s)
            p['event_handles'] = event_handles
            p['agent_id'] = agent
            p['central_wallet'] = center
            p['role_wallets'] = role_wallets
        all_plans[partition] = plans
    assign_event_order(all_events)
    remap = {}
    for i,event in enumerate(all_events,1):
        all_truth[event['_handle']]['transaction_id']=i
        remap[event['_handle']]=i
    # Accounting is checked before any data write. No retrospective top-ups.
    balances = {w['wallet_id']:w['initial_balance_minor'] for ws,_ in entities.values() for w in ws}
    floats = {a['agent_id']:a['initial_float_minor'] for _,ags in entities.values() for a in ags}
    for e in all_events:
        s,r,v,a=e['sender_wallet'],e['receiver_wallet'],e['amount_minor'],e['agent_id']
        if e['transaction_type']=='cash_in':
            floats[a]-=v; balances[s]+=v
        elif e['transaction_type']=='cash_out':
            balances[s]-=v; floats[a]+=v
        else:
            balances[s]-=v; balances[r]+=v
        if min(balances[s],balances[r],floats.get(a,0))<0:
            raise ValueError('Accounting infeasible; no dataset written')
        if not 100<=v<=2500000:
            raise ValueError('Amount outside committed support')
    for partition in PARTITIONS:
        folder=partition_path(destination,partition)
        events=[e for e in all_events if e['_partition']==partition]
        write_csv(folder/'transactions.csv',EVENT_FIELDS,[{k:e[k] for k in EVENT_FIELDS} for e in events])
        write_csv(folder/'ground_truth.csv',TRUTH_FIELDS,[all_truth[e['_handle']] for e in events])
        ws,ags=entities[partition]
        write_csv(folder/'wallets.csv',WALLET_FIELDS,ws)
        write_csv(folder/'agents.csv',AGENT_FIELDS,ags)
        for p in all_plans[partition]:
            p['transaction_ids']=[remap[h] for h in p.pop('event_handles')]
        write_json(folder/'episode_plans.json',{'role':'generation_audit_only','episodes':all_plans[partition]})
        write_json(folder/'membership_commitment.json',commitments[partition])
        write_json(folder/'partition_role.json',{'partition':partition,'role':'development' if partition in DEVELOPMENT else 'HOLDOUT',
                    'training_allowed':partition in DEVELOPMENT,'feature_exploration_allowed':partition in DEVELOPMENT})
    hashes={p.relative_to(destination).as_posix():digest(p) for p in sorted(destination.rglob('*')) if p.is_file()}
    source_hashes={p.relative_to(ROOT).as_posix():digest(p) for p in sorted((ROOT/'src').glob('*.py'))}
    write_json(destination/'manifests/generation_manifest.json',{
        'dataset':allocation['dataset'],'schema_version':schema['version'],'generator_version':1,'seed':seed,
        'seed_streams':'SHA256(seed:partition), separate entity streams, label-independent global tie stream',
        'horizon_start':stamp(0),'horizon_end_exclusive':stamp(180*DAY),'monetary_unit':'USD cents',
        'partition_roles':{p:'development' if p in DEVELOPMENT else 'holdout' for p in PARTITIONS},
        'targets':allocation['partitions'],'actual_rows':{p:sum(e['_partition']==p for e in all_events) for p in PARTITIONS},
        'file_hashes':hashes,'source_hashes':source_hashes,
        'design_hashes':{p.name:digest(p) for p in sorted((ROOT/'design').glob('*.json'))},
        'independent_generation_specification_version':1,'audit_status':'pending independent structural audit',
        'custody':'user-approved software-level separation; not external custody or OS confinement'})
    return destination


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--seed',type=int,default=20260921)
    args=parser.parse_args()
    print(generate(args.output,args.seed))
