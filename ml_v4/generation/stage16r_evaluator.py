"""V4 universal target. Accepts only validated observable Events.

No generator, provenance, features or prediction imports. All comparisons
are integer/rational. Output is emitted before observation state is updated.
"""
from collections import defaultdict, Counter
from fractions import Fraction as Q
from stage16r_contract import Event, DAY, HOUR, FAMILIES, median, window, validate_event


def total(events):
    return sum(e.amount_minor for e in events)


def top2(events):
    return Q(sum(sorted(Counter(e.serviced_wallet for e in events).values(), reverse=True)[:2]), len(events)) if events else Q(0)


def cash_stats(events):
    ins = [e for e in events if e.transaction_type == 'cash_in']
    outs = [e for e in events if e.transaction_type == 'cash_out']
    count, value = len(ins) + len(outs), total(ins) + total(outs)
    return {'in_count': len(ins), 'out_count': len(outs), 'in_value': total(ins), 'out_value': total(outs), 'count_skew': Q(len(outs)-len(ins), count) if count else Q(0), 'value_skew': Q(total(outs)-total(ins), value) if value else Q(0), 'distinct': len({e.serviced_wallet for e in ins+outs})}


def return_path(current, edges):
    """Existential simple chronological search; no path-count cap."""
    adjacency = defaultdict(list)
    for e in edges:
        if current.time - 7*DAY < e.time <= current.time and e.key < current.key:
            adjacency[e.sender_wallet].append(e)
    start, finish = current.receiver_wallet, current.sender_wallet
    def visit(node, seen, path):
        if len(path) == 5:
            return None
        for e in adjacency[node]:
            if e.receiver_wallet in seen or (path and e.key <= path[-1].key):
                continue
            if path and not Q(1,4) <= Q(e.amount_minor, path[-1].amount_minor) <= 4:
                continue
            first = path[0] if path else e
            new = path + [e]
            if e.receiver_wallet == finish:
                if Q(1,4) <= Q(current.amount_minor, first.amount_minor) <= Q(5,4):
                    return [x.transaction_id for x in new]
            else:
                found = visit(e.receiver_wallet, seen | {e.receiver_wallet}, new)
                if found:
                    return found
        return None
    return visit(start, {start}, [])


class Evaluator:
    def __init__(self):
        self.activity = defaultdict(list)
        self.participation = {}
        self.services = defaultdict(list)
        self.first_service = {}
        self.incoming = defaultdict(list)
        self.outgoing = defaultdict(list)
        self.funding = defaultdict(list)
        self.exits = defaultdict(list)
        self.edges = []
        self.previous = None
        self.ids = set()

    def evaluate(self, e):
        if type(e) is not Event:
            raise TypeError('Only observable Event objects accepted')
        validate_event(e)
        if e.transaction_id in self.ids or (self.previous is not None and e.key <= self.previous):
            raise ValueError('Duplicate ID or non-increasing stream')
        t, subject = e.time, e.subject
        flags = dict.fromkeys(FAMILIES, False)
        eligible = dict.fromkeys(FAMILIES, False)
        reasons = dict.fromkeys(FAMILIES, 'inapplicable')
        witnesses = {}
        def history(hist, first, length, minimum, code, distinct_min=0):
            base = window(hist, t-length-28*DAY, t-length)
            age = first is not None and first <= t-length-28*DAY
            counts = len(base) >= minimum and (not distinct_min or len({x.serviced_wallet for x in base}) >= distinct_min)
            eligible[code] = bool(age and counts)
            reasons[code] = 'eligible' if eligible[code] else 'coverage' if not age else 'baseline_support'
            recent = window(hist, t-length, t) + [e]
            return recent, base
        hist = self.activity[subject]
        first = self.participation.get(subject)
        r,b = history(hist,first,HOUR,4,'S1')
        flags['S1'] = eligible['S1'] and len(r)>=4 and len({x.amount_minor for x in r})>=2 and total(r)>=30000 and Q(max(x.amount_minor for x in r),total(r))<=Q(3,5) and Q(len(r))/max(1,Q(len(b),672))>=3
        r,b = history(hist,first,7*DAY,4,'S2')
        cr = [x for x in r if 20*abs(x.amount_minor-e.amount_minor)<=e.amount_minor]
        cb = [x for x in b if 20*abs(x.amount_minor-e.amount_minor)<=e.amount_minor]
        flags['S2'] = eligible['S2'] and len(cr)>=4 and total(cr)>=20000 and Q(len(cr),len(r))>=Q(3,5) and Q(len(cr))/max(1,Q(len(cb),4))>=2
        midnight = t//DAY*DAY
        br = [x for x in hist if midnight-28*DAY<=x.time<midnight]
        dr = [x for x in hist if midnight<=x.time<=t]+[e]
        eligible['S3'] = first is not None and first<=midnight-28*DAY and len(br)>=4
        reasons['S3'] = 'eligible' if eligible['S3'] else 'coverage_or_baseline_support'
        day_counts = Counter(x.time//DAY for x in br)
        flags['S3'] = eligible['S3'] and len(dr)>=6 and len({x.time//HOUR for x in dr})>=3 and total(dr)>=50000 and Q(len(dr))/max(1,median([day_counts[midnight//DAY-i] for i in range(1,29)]))>=2
        r,b = history(hist,first,7*DAY,4,'S4')
        band = lambda x: 700000<=x.amount_minor<=1050000
        rr,bb = [x for x in r if band(x)], [x for x in b if band(x)]
        flags['S4'] = eligible['S4'] and band(e) and len(r)>=5 and len(rr)>=3 and len({x.amount_minor for x in rr})>=2 and Q(len(rr),len(r))>=Q(2,5) and Q(len(rr))/max(1,Q(len(bb),4))>=2
        if e.transaction_type=='wallet_to_wallet':
            for code,who,direction,opposite in [('N1',e.receiver_wallet,self.incoming,'sender_wallet'),('N2',e.sender_wallet,self.outgoing,'receiver_wallet')]:
                r,b = history(direction[who],self.participation.get(who),DAY,4,code)
                flags[code] = eligible[code] and len(r)>=4 and len({getattr(x,opposite) for x in r})>=3 and total(r)>=30000 and Q(len(r))/max(1,Q(len(b),28))>=2
            eligible['N3']=True
            reasons['N3']='eligible_no_baseline'
            path = return_path(e, self.edges)
            flags['N3'] = path is not None
            if path: witnesses['N3']=path
        if e.transaction_type in ('wallet_to_wallet','cash_out'):
            anchors = window(self.incoming[subject],t-DAY,t)
            eligible['N4']=bool(anchors)
            reasons['N4']='eligible_anchor' if anchors else 'no_anchor'
            if anchors:
                anchor=min(anchors,key=lambda x:x.key)
                fund=[x for x in self.funding[subject] if anchor.key<=x.key<e.key]
                out=[x for x in self.exits[subject] if anchor.key<x.key<e.key]
                f,o = total(fund),total(out)
                flags['N4']=f>=10000 and Q(1,2)<=Q(o+e.amount_minor,f)<=1 and e.amount_minor<=f-o
                if flags['N4']: witnesses['N4']=[anchor.transaction_id]
        if e.agent_id:
            hist=self.services[e.agent_id]
            first=self.first_service.get(e.agent_id)
            r,b=history(hist,first,7*DAY,12,'A1')
            d=len({x.serviced_wallet for x in r})
            u=len({x.serviced_wallet for x in r}-{x.serviced_wallet for x in b})
            m=median([len({x.serviced_wallet for x in window(hist,t-(14+7*i)*DAY,t-(7+7*i)*DAY)}) for i in range(4)])
            flags['A1']=eligible['A1'] and d>=6 and u>=4 and Q(u,d)>=Q(1,2) and Q(d)/max(1,m)>=Q(3,2)
            r,b=history(hist,first,DAY,20,'A2',5)
            flags['A2']=eligible['A2'] and len(r)>=8 and top2(r)>=Q(13,20) and top2(r)-top2(b)>=Q(1,5)
            r,b=history(hist,first,HOUR,12,'A3')
            flags['A3']=eligible['A3'] and len(r)>=5 and len({x.serviced_wallet for x in r})>=3 and Q(len(r))/max(1,Q(len(b),672))>=3
            if e.transaction_type in ('cash_in','cash_out'):
                r,b=history(hist,first,DAY,12,'A4')
                bs,rs=cash_stats(b),cash_stats(r)
                eligible['A4'] = eligible['A4'] and bs['in_count']+bs['out_count']>=8
                if not eligible['A4']: reasons['A4']='coverage_or_baseline_cash_support'
                v,c=rs['value_skew'],rs['count_skew']
                flags['A4']=eligible['A4'] and rs['in_count']+rs['out_count']>=6 and rs['distinct']>=3 and abs(v)>=Q(3,5) and abs(c)>=Q(1,2) and v*c>0 and abs(v-bs['value_skew'])>=Q(2,5)
        return {'transaction_id':e.transaction_id,'ground_truth_label':int(any(flags.values())), 'families':[f for f in FAMILIES if flags[f]],'eligible':eligible,'reasons':reasons,'witnesses':witnesses}

    def observe(self,e):
        self.previous=e.key
        self.ids.add(e.transaction_id)
        for who in {e.sender_wallet,e.receiver_wallet}:
            self.participation.setdefault(who,e.time)
        self.activity[e.subject].append(e)
        if e.agent_id:
            self.first_service.setdefault(e.agent_id,e.time)
            self.services[e.agent_id].append(e)
        if e.transaction_type=='wallet_to_wallet':
            self.incoming[e.receiver_wallet].append(e)
            self.outgoing[e.sender_wallet].append(e)
            self.funding[e.receiver_wallet].append(e)
            self.exits[e.sender_wallet].append(e)
            self.edges.append(e)
        elif e.transaction_type=='cash_in': self.funding[e.subject].append(e)
        else: self.exits[e.subject].append(e)
        # Retain 35d event state plus first-observation scalars. Raw ledgers live separately.
        if len(self.ids)%128==0:
            low=e.time-35*DAY
            for table in (self.activity,self.services,self.incoming,self.outgoing,self.funding,self.exits):
                for who,items in table.items(): table[who]=[x for x in items if x.time>=low]
            self.edges=[x for x in self.edges if x.time>e.time-7*DAY]

    def process(self,e):
        answer=self.evaluate(e)
        self.observe(e)
        return answer


def replay(events):
    state=Evaluator()
    return [state.process(e) for e in events]
