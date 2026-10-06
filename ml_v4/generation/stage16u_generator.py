"""Stage 16T challenge implementation; no production entry point in Stage 16U.

The caller supplies streams. This module never creates a salt, reads a dataset,
imports the evaluator, or chooses examples based on target outcomes.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone, timedelta

import numpy as np
from stage16r_contract import DAY, HOUR, FAMILIES, validate_event
from stage16r_generator import (
    Unit, ARCHETYPES, CONTEXT, base_amount, large_amount, bounded_shift, cents,
)

DATASET = 'mobile_money_v4_independent_challenge_1'
ARMS = ('reference_challenge', 'shifted_challenge')
STREAMS = ('entities', 'profiles', 'catchments', 'history', 'routine', 'episodes',
           'amounts', 'timestamps', 'transaction_ids', 'bootstrap', 'permutation')
BUDGET = dict(units=24, wallets=2400, agents=192, scored=48000, warmup=57600)
START = datetime(2028, 1, 1, tzinfo=timezone.utc)
SCORED_START = 56 * DAY
END = 236 * DAY
HARD_ORIGIN = {
    'S1': 'H1', 'S3': 'H1', 'S2': 'H2', 'S4': 'H3',
    'N1': 'H4', 'N2': 'H5', 'N4': 'H5', 'N3': 'H6',
    'A1': 'H7', 'A3': 'H7', 'A2': 'H8', 'A4': 'H8',
}


def counts(family, total, rng):
    if family not in FAMILIES or not 12 <= total <= 20:
        raise ValueError('Invalid family/episode size')
    if family == 'N3':
        v, k = int(rng.integers(2, 7)), int(rng.integers(0, 3))
        return v + k, {'V': v, 'K': k}
    return total - 2, {}


def split_budget(budget, rng):
    sizes = []
    while budget >= 12:
        size = int(rng.integers(12, min(20, budget) + 1))
        sizes.append(size)
        budget -= size
    return sizes, budget


def log_uniform(rng, lo, hi):
    return math.exp(float(rng.uniform(math.log(lo), math.log(hi))))


def fitting_start(rng, duration):
    """Sample every fitting microsecond while keeping the horizon end exclusive."""
    if type(duration) is not int or not 0 < duration < END - SCORED_START:
        raise ValueError('Episode duration does not fit scored horizon')
    return int(rng.integers(SCORED_START, END - duration + 1))


def validate_aggregate(units, *, arms=ARMS, units_per_arm=12, wallets_per_unit=100,
                       agents_per_unit=8, scored_per_unit=2000, warmup_per_unit=2400):
    """Check global unit, entity, transaction-ID and horizon isolation on completed outputs."""
    expected_arms = tuple(arms)
    if len(units) != len(expected_arms) * units_per_arm:
        raise ValueError('Wrong aggregate unit count')
    seen_slots, seen_entities, seen_transactions = set(), set(), set()
    totals = {arm: {'units': 0, 'scored': 0, 'warmup': 0} for arm in expected_arms}
    for record in units:
        arm, index = record['arm'], record['index']
        slot = (arm, index)
        if arm not in totals or type(index) is not int or not 0 <= index < units_per_arm or slot in seen_slots:
            raise ValueError('Invalid or duplicate arm/unit slot')
        seen_slots.add(slot)
        population, events = record['population'], record['events']
        wallets = {item['id'] for item in population['wallets']}
        agents = {item['id'] for item in population['agents']}
        if len(wallets) != wallets_per_unit or len(agents) != agents_per_unit:
            raise ValueError('Unit entity count mismatch')
        entities = wallets | agents
        if len(entities) != wallets_per_unit + agents_per_unit or seen_entities.intersection(entities):
            raise ValueError('Entity identity collision across units or arms')
        seen_entities.update(entities)
        if len(events) != scored_per_unit + warmup_per_unit:
            raise ValueError('Unit transaction count mismatch')
        if any(left.key >= right.key for left, right in zip(events, events[1:])):
            raise ValueError('Unit events are not strictly ordered')
        slot_ids = set()
        for event in events:
            validate_event(event)
            if event.transaction_id in slot_ids or event.transaction_id in seen_transactions:
                raise ValueError('Transaction ID collision across unit or arm')
            slot_ids.add(event.transaction_id)
            if event.sender_wallet not in wallets or event.receiver_wallet not in wallets:
                raise ValueError('Cross-unit or unknown wallet endpoint')
            if event.agent_id and event.agent_id not in agents:
                raise ValueError('Cross-unit or unknown agent endpoint')
            moment = datetime.fromisoformat(event.event_timestamp.replace('Z', '+00:00'))
            offset = moment - START
            elapsed = (offset.days * 86400 + offset.seconds) * 1_000_000 + offset.microseconds
            if not 0 <= elapsed < END:
                raise ValueError('Event outside declared full horizon')
            bucket = 'warmup' if elapsed < SCORED_START else 'scored'
            totals[arm][bucket] += 1
        seen_transactions.update(slot_ids)
        totals[arm]['units'] += 1
    if seen_slots != {(arm, i) for arm in expected_arms for i in range(units_per_arm)}:
        raise ValueError('Missing arm/unit slot')
    if any(value != units_per_arm * scored_per_unit for arm, value in ((a, totals[a]['scored']) for a in expected_arms)):
        raise ValueError('Aggregate scored event count mismatch')
    if any(value != units_per_arm * warmup_per_unit for arm, value in ((a, totals[a]['warmup']) for a in expected_arms)):
        raise ValueError('Aggregate warmup event count mismatch')
    return totals


class ChallengeUnit(Unit):
    """One isolated unit; inherited observable schema/population/accounting only.

    No method is called by the readiness runner to materialize a candidate unit.
    Production execution remains unavailable until independent custody is installed.
    """
    def __init__(self, arm, index, streams, archetypes=None):
        if arm not in ARMS or not 0 <= index < 12 or set(streams) != set(STREAMS):
            raise ValueError('Invalid challenge arm/unit/streams')
        if arm == ARMS[1] and (archetypes is None or len(archetypes) != 8):
            raise ValueError('Shifted archetypes must come from the frozen 96-agent allocation')
        self.arm = arm
        self.challenge_streams = streams
        aliases = dict(streams, background=streams['routine'], warmup=streams['history'])
        super().__init__('independent_evaluation' if arm == ARMS[1] else 'train',
                         index, independent_arch=archetypes, fixture_streams=aliases)
        # Preserve inherited draws and laws, translating scored offset 42 -> 56.
        for w in self.wallets:
            if w['activation']:
                w['activation'] += 14 * DAY
        for a in self.agents:
            for interval in a['shocks'] + a['acquisition']:
                interval['start'] += 14
                interval['end'] += 14
        self.cycles = {}

    def cycle(self, key, candidates, preferred=()):
        remaining = self.cycles.setdefault(key, [])
        remaining[:] = [x for x in remaining if x in candidates]
        if not remaining:
            remaining.extend(str(x) for x in self.rng['episodes'].permutation(candidates))
            if preferred:
                remaining.sort(key=lambda x: x not in preferred)
        if not remaining:
            raise RuntimeError('No active scheduling subject')
        return remaining.pop(0)

    def plan_challenge_episode(self, family, hard, total):
        r, rt = self.rng['episodes'], self.rng['timestamps']
        motif, graph = counts(family, total, r)
        variant = int(r.integers(0, 2)) if hard else None
        ranges = {'S1':(5/60,75/60), 'S2':(24,168), 'S3':(3,24),
                  'S4':(24,168), 'N1':(1,30), 'N2':(1,30), 'N3':(1,168),
                  'N4':(1,30), 'A1':(48,672), 'A2':(2,30), 'A3':(.25,3), 'A4':(2,30)}
        lo, hi = ranges[family]
        if hard and family == 'S1' and variant == 1: lo, hi = .75, 2
        if hard and family == 'A3' and variant == 1: lo, hi = .75, 3
        duration = int(rt.uniform(lo, hi) * HOUR)
        head, tail = float(rt.uniform(.05,.25)), float(rt.uniform(.05,.25))
        full = int((1 + head + tail) * duration)
        start = fitting_start(rt, full)
        ms, me = start + int(head * duration), start + int(head * duration) + duration
        times = sorted(int(x) for x in rt.integers(ms, me + 1, motif))
        times[0], times[-1] = ms, me
        if hard and family == 'S4':
            times = [ms + i * duration // (motif - 1) for i in range(motif)]
        if hard and family == 'S3':
            # Integer split convention: fair assignment of the odd remainder.
            split = motif // 2 + (int(r.integers(0,2)) if motif % 2 else 0)
            a, b = sorted(int(x) for x in rt.integers(ms, me + 1, 2))
            times = [a] * split + [b] * (motif - split)
        swap = False
        if family == 'N3':
            v = graph['V']
            primary = sorted(int(x) for x in rt.integers(ms, me + 1, v))
            primary[0], primary[-1] = ms, me
            swap = bool(r.random() < (.75 if hard else .5))
            if swap and v > 2:
                i, j = (int(x) for x in r.choice(v - 1, 2, replace=False))
                primary[i], primary[j] = primary[j], primary[i]
            times = primary + [int(rt.integers(ms, me)) for _ in range(graph['K'])]
        eid = f'{self.arm}:{self.index}:{len(self.episode_audit)}'
        plan = dict(id=eid, origin=f'hard_{family}' if hard else family, family=family,
                    hard=hard, hard_origin=HARD_ORIGIN[family] if hard else None,
                    variant=variant, E=total, M=motif, start=start,
                    motif_start=ms, motif_end=me, end=start+full,
                    strength=float(r.uniform(.1,.9)), swap_requested=swap, **graph)
        self.episode_audit.append(plan)
        for j, time in enumerate(times):
            self.plans.append(dict(t=time, episode=eid, role='motif', j=j, plan=plan))
        for _ in range(total - motif):
            role = str(r.choice(CONTEXT))
            low = me + 1 if role == 'post_motif_ordinary' else start
            self.plans.append(dict(t=int(rt.integers(low,start+full)), episode=eid,
                                   role='context', context_role=role, plan=plan))

    def schedule(self):
        if self.plans:
            raise RuntimeError('Unit already scheduled; no retry')
        r, rt = self.rng['episodes'], self.rng['timestamps']
        residual = 0
        for hard, budget in ((False,120), (True,30)):
            for family in FAMILIES:
                sizes, left = split_budget(budget,r)
                residual += left
                for size in sizes: self.plan_challenge_episode(family,hard,size)
        # Explicit 1200/400/800 warm-up allocation, each event counted once.
        history = self.rng['history']
        initial = [w['id'] for w in self.wallets if w['activation'] == 0]
        for kind, number, subjects in (
            ('wallet',1200,initial), ('network',400,initial),
            ('agent',800,[a['id'] for a in self.agents])):
            order = [str(x) for x in history.permutation(subjects)]
            for i in range(number):
                self.plans.append(dict(t=int(rt.integers(0,SCORED_START)), role='background',
                    episode=None, warmup_kind=kind, warmup_subject=order[i % len(order)]))
        routine = []
        rr = self.rng['routine']
        for w in self.wallets:
            if w['activation']:
                routine.append(dict(t=w['activation'],fixed_wallet=w['id'],activation=True))
            if w['recurring']:
                period = int(rr.choice([7,30])) * DAY
                phase = int(rt.integers(0,period))
                anchor = base_amount(self.rng['amounts'])
                for time in range(max(SCORED_START,w['activation'])+phase,END,period):
                    actual = time + int(rt.uniform(-12,12) * HOUR)
                    if max(SCORED_START,w['activation']) <= actual < END:
                        routine.append(dict(t=actual,fixed_wallet=w['id'],recurring_base=anchor))
        if len(routine) > 200 + residual:
            raise RuntimeError('Inherited recurring schedule exceeds fixed routine budget; no deletion or redraw')
        routine += [dict(t=int(rt.integers(SCORED_START,END))) for _ in range(200+residual-len(routine))]
        self.plans += [p | dict(role='background',episode=None) for p in routine]
        seen = set()
        for p in self.plans:
            ident = int(self.rng['transaction_ids'].integers(1,2**63))
            if ident in seen: raise RuntimeError('ID collision; retain failure')
            seen.add(ident); p['id'] = ident
        self.plans.sort(key=lambda p:(p['t'],p['id']))
        if len(self.plans) != 4400: raise RuntimeError('Fixed unit budget mismatch')
        self.residual = residual

    def episode_state(self,p):
        eid = p['episode']
        if eid in self.cache: return self.cache[eid]
        plan, time = p['plan'], p['t']
        f, hard, m = plan['family'], plan['hard'], plan['M']
        r, ra = self.rng['episodes'], self.rng['amounts']
        active = self.active(time)
        prefer = [w['id'] for w in self.wallets if w['profile']=='recurring_payment'] if hard and f=='S4' else []
        focal = self.cycle((plan['origin'],'wallet'),active,prefer)
        agent = self.cycle((plan['origin'],'agent'),[a['id'] for a in self.agents])
        breadth = int(r.integers(1,4) if hard and plan['variant']==0 and f in ('N1','N2','A3') else r.integers(2,9))
        pool = [w for w in active if w != focal]
        partners = [str(x) for x in r.choice(pool,breadth,replace=False)]
        if hard and plan['variant']==1 and f in ('N1','N2'):
            prior = sorted(self.relationships[focal].intersection(pool))
            if prior: partners = prior[:breadth]
        if f=='N3': partners = [str(x) for x in r.choice(pool,plan['V']-1,replace=False)]
        state = dict(focal=focal, agent=agent, partners=partners, repeat=float(r.uniform(.2,.9)),
                     concentration=float(r.uniform(.35,.95)), concentrated=int(r.integers(2,7)))
        if f=='A1':
            state.update(activity_interval=[plan['motif_start'],plan['motif_end']],
                         activity_factor=float(r.uniform(.8,2.5)))
        if f=='A2':
            prior = Counter(w for _,w in self.service_history[agent] if w in active)
            candidates = [w for w,_ in prior.most_common()] if hard else []
            candidates += [w for w in active if w not in candidates]
            state['concentration_wallets'] = candidates[:state['concentrated']] if hard and prior else [str(x) for x in r.choice(active,state['concentrated'],replace=False)]
        if f=='N3':
            vertices = [focal]+partners
            pairs = list(zip(vertices[:-1],vertices[1:]))+[(vertices[-1],vertices[0])]
            edge = int(r.integers(0,plan['V']-1))
            if plan['K']==1: pairs.append(pairs[edge])
            if plan['K']==2:
                other = self.choose([w for w in active if w not in vertices],stream='episodes')
                left,right = pairs[edge]; pairs += [(left,other),(other,right)]
            state['pairs'] = pairs
        if f=='A4':
            probability = float(r.uniform(.1,.9))
            prior = [direction for _,direction in self.cash_history[agent]]
            if hard and prior:
                probability = .5+abs(probability-.5)*(1 if prior.count('cash_out')>=len(prior)/2 else -1)
            state['directions'] = ['cash_out' if r.random()<probability else 'cash_in' for _ in range(m)]
        while True:
            if f=='S1':
                alpha = ra.uniform(.5,2,m)
                if hard and plan['variant']==0:
                    alpha = np.ones(m); alpha[int(r.integers(0,m))]=8
                values = (ra.dirichlet(alpha)*log_uniform(ra,100,1000)).tolist()
            elif f=='S2':
                prior = [value for _,value in self.activity_history[focal]]
                anchor = self.choose(prior,stream='amounts')/100 if hard and plan['variant']==0 and prior else log_uniform(ra,30,500)
                sd = float(ra.uniform(.005,.02) if ra.random()<.5 else ra.uniform(.02,.15))
                values = (anchor*ra.lognormal(0,sd,m)).tolist()
            elif f=='S4': values = [large_amount(ra) for _ in range(m)]
            elif f in ('N1','N2'): values = [log_uniform(ra,30,500) for _ in range(m)]
            elif f=='N3':
                values = [log_uniform(ra,30,500)]
                for _ in range(plan['V']-2): values.append(values[-1]*log_uniform(ra,.2,5))
                values.append(values[0]*float(ra.uniform(.2,1.4)))
                for _ in range(plan['K']): values.append(values[0]*log_uniform(ra,.2,5))
            elif f=='N4':
                funding = log_uniform(ra,30,1000)
                fraction = float(ra.uniform(.1,.6 if hard else 1.2))
                values = [funding]+(ra.dirichlet(np.ones(m-1))*funding*fraction).tolist()
            else:
                values = [base_amount(ra) for _ in range(m)]
                if f=='A4':
                    factor = float(ra.uniform(.5,2))
                    values = [v*(factor if d=='cash_out' else 1) for v,d in zip(values,state['directions'])]
            if self.independent: values = [bounded_shift(v) if f=='S4' else v*1.15 for v in values]
            if all(.01<=v<=15000 for v in values): break
            self.amount_rejections += 1
        state['amounts'] = [cents(v) for v in values]
        self.cache[eid] = state
        return state

    def make_event(self,p):
        # Resolve hand-scheduled warm-up roles through the same observable writer.
        p = dict(p)
        kind = p.get('warmup_kind')
        if kind:
            self.rng['background'] = self.challenge_streams['history']
            subject = p['warmup_subject']
            if kind in ('wallet','network'): p['fixed_wallet']=subject
            if kind in ('network','agent'):
                self.update_population(p['t'])
                focal = subject if kind=='network' else self.customer(subject,p['t'])
                fake = dict(id=f'fixture-history:{p["id"]}',family='N2' if kind=='network' else 'A3',
                            origin='warmup',hard=False,variant=None,M=1)
                p.update(episode=fake['id'],role='motif',j=0,plan=fake)
                self.cache[fake['id']] = dict(focal=focal,agent=subject if kind=='agent' else self.agent(p['t']),
                    partners=[self.counterparty(focal,p['t'])] if kind=='network' else [focal],
                    amounts=[self.ordinary_amount(p)])
        else: self.rng['background'] = self.challenge_streams['routine']
        # Parent writer recognizes H7 for observed-customer preference only.
        if p.get('plan',{}).get('hard') and p['plan']['family']=='A1' and p['plan']['variant']==0:
            p['plan']=dict(p['plan'],origin='H7')
        event, private = super().make_event(p)
        if kind:
            private.update(scenario_id=None,campaign_id=None,scenario_family=None,
                           origin='background',event_role=None,context_role=None,intended_onset=None)
            if p['episode']: self.cache.pop(p['episode'])
        event = replace(event,event_timestamp=(START+timedelta(microseconds=p['t'])).isoformat(timespec='microseconds').replace('+00:00','Z'))
        private['arm']=self.arm
        if p.get('plan', {}).get('hard'):
            private['origin'] = 'hard_' + p['plan']['hard_origin']
        return event,private


def production_entrypoint(*args, **kwargs):
    raise PermissionError('Stage 16U is preproduction. No independently provisioned custodian or generation authorization.')
