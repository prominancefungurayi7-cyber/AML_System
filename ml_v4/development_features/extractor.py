"""Frozen v4.features.1. Observable inputs only; no evaluator dependency."""
from collections import defaultdict, deque, Counter
from fractions import Fraction
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'ml_v4/generation'))
from stage16r_contract import Event, DAY, HOUR, validate_event

SPEC = json.loads((ROOT / 'ml_v4/design/v4_feature_spec.json').read_text(encoding='utf-8'))
NAMES = tuple(f['name'] for f in SPEC['features'])

def median(values):
    a = sorted(values)
    n = len(a)
    return Fraction(a[n//2]) if n % 2 else Fraction(a[n//2-1] + a[n//2], 2)

def distinct(rows):
    return {e.serviced_wallet for e in rows}

def top2(rows):
    return Fraction(sum(sorted(Counter(e.serviced_wallet for e in rows).values(), reverse=True)[:2]), len(rows)) if rows else Fraction(0)

def skew(rows):
    incoming = sum(e.amount_minor for e in rows if e.transaction_type == 'cash_in')
    outgoing = sum(e.amount_minor for e in rows if e.transaction_type == 'cash_out')
    return Fraction(outgoing-incoming, outgoing+incoming) if outgoing+incoming else Fraction(0)

class Extractor:
    def __init__(self):
        self.activity = defaultdict(deque)
        self.incoming = defaultdict(deque)
        self.outgoing = defaultdict(deque)
        self.services = defaultdict(deque)
        self.first_wallet = {}
        self.first_agent = {}
        self.ids = set()
        self.last = None

    def history(self, table, key, t):
        rows = table[key]
        while rows and rows[0].time <= t-35*DAY:
            rows.popleft()
        return list(rows)

    def step(self, e):
        if type(e) is not Event:
            raise TypeError('Only validated observable Event records permitted')
        validate_event(e)
        if e.transaction_id in self.ids or (self.last is not None and e.key <= self.last):
            raise ValueError('Duplicate ID or nonincreasing full key')
        t, w, a = e.time, e.subject, e.agent_id
        wh = self.history(self.activity, w, t)
        ah = self.history(self.services, a, t) if a else []
        def window(rows, lag):
            return [r for r in rows if r.time > t-lag]
        def baseline(rows, lag):
            return [r for r in rows if t-lag-28*DAY < r.time <= t-lag]
        def eligible(first, lower, rows, minimum):
            return first is not None and first <= lower and len(rows) >= minimum
        wf = self.first_wallet.get(w)
        af = self.first_agent.get(a)
        wr = window(wh,HOUR)+[e]
        wb = baseline(wh,HOUR)
        seven = window(wh,7*DAY)+[e]
        similar = [r for r in seven if 20*abs(r.amount_minor-e.amount_minor) <= e.amount_minor]
        midnight = t//DAY*DAY
        today = [r for r in wh if r.time >= midnight]+[e]
        days = [r for r in wh if midnight-28*DAY <= r.time < midnight]
        bins = Counter((midnight-r.time-1)//DAY for r in days)
        f = [e.amount_minor, e.transaction_type, len(wr), sum(r.amount_minor for r in wr),
             Fraction(max(r.amount_minor for r in wr),sum(r.amount_minor for r in wr)),
             Fraction(len(wr))/max(1,Fraction(len(wb),672)) if eligible(wf,t-HOUR-28*DAY,wb,4) else -1,
             len(similar),Fraction(len(similar),len(seven)),len(today),len({r.time//HOUR for r in today}),
             Fraction(len(today))/max(1,median([bins[k] for k in range(28)])) if eligible(wf,midnight-28*DAY,days,4) else -1,
             sum(700000 <= r.amount_minor <= 1050000 for r in seven)]
        is_w2w = e.transaction_type == 'wallet_to_wallet'
        for table, endpoint, opposite in ((self.incoming,e.receiver_wallet,'sender_wallet'),(self.outgoing,e.sender_wallet,'receiver_wallet')):
            if is_w2w:
                hist = self.history(table,endpoint,t)
                recent, base = window(hist,DAY)+[e], baseline(hist,DAY)
                f.extend([len(recent),len({getattr(r,opposite) for r in recent}),
                    Fraction(len(recent))/max(1,Fraction(len(base),28)) if eligible(self.first_wallet.get(endpoint),t-29*DAY,base,4) else -1])
            else:
                f.extend([0,0,-1])
        # Enumerate every chronological simple path; amounts never filter topology.
        count, minlen, selected = 0, None, None
        if is_w2w:
            def visit(node, vertices, path):
                nonlocal count,minlen,selected
                if len(path) >= 5:
                    return
                for edge in self.history(self.outgoing,node,t):
                    if edge.time <= t-7*DAY or (path and edge.key <= path[-1].key) or edge.receiver_wallet in vertices:
                        continue
                    route = path+[edge]
                    if edge.receiver_wallet == e.sender_wallet:
                        count += 1
                        minlen = min(minlen or len(route),len(route))
                        spread = max([Fraction(1)]+[max(Fraction(y.amount_minor,x.amount_minor),Fraction(x.amount_minor,y.amount_minor)) for x,y in zip(route,route[1:])])
                        rank = (spread,len(route),tuple(x.key for x in route))
                        if selected is None or rank < selected[0]:
                            selected = (rank,route[0].amount_minor)
                    else:
                        visit(edge.receiver_wallet,vertices|{edge.receiver_wallet},route)
            visit(e.receiver_wallet,{e.receiver_wallet},[])
        f.extend([minlen if count else -1,count,math.log(float(selected[0][0])) if count else -1,
                  Fraction(e.amount_minor,selected[1]) if count else -1])
        inc = window(self.history(self.incoming,w,t),DAY)
        if e.transaction_type in ('wallet_to_wallet','cash_out') and inc:
            anchor = inc[0]
            funding = sum(r.amount_minor for r in inc if r.key >= anchor.key)+sum(r.amount_minor for r in wh if r.transaction_type == 'cash_in' and r.key >= anchor.key)
            outward = sum(r.amount_minor for r in wh if r.key > anchor.key and r.transaction_type in ('wallet_to_wallet','cash_out'))
            f.extend([Fraction(outward+e.amount_minor,funding),funding-outward])
        else:
            f.extend([-1,float('nan')])
        ar7 = window(ah,7*DAY)+([e] if a else [])
        ab7 = baseline(ah,7*DAY)
        ar24 = window(ah,DAY)+([e] if a else [])
        ab24 = baseline(ah,DAY)
        ar1 = window(ah,HOUR)+([e] if a else [])
        ab1 = baseline(ah,HOUR)
        D = len(distinct(ar7))
        U = len(distinct(ar7)-distinct(ab7))
        weeks = [len(distinct([r for r in ab7 if t-(k+2)*7*DAY < r.time <= t-(k+1)*7*DAY])) for k in range(4)]
        gate1 = eligible(af,t-35*DAY,ab7,12)
        gate2 = eligible(af,t-29*DAY,ab24,20) and len(distinct(ab24)) >= 5
        cash = [r for r in ar24 if r.transaction_type in ('cash_in','cash_out')]
        bcash = [r for r in ab24 if r.transaction_type in ('cash_in','cash_out')]
        f.extend([Fraction(D)/max(1,median(weeks)) if gate1 else -1,D,U if gate1 else -1,Fraction(U,D) if gate1 else -1,
                  top2(ar24),top2(ar24)-top2(ab24) if gate2 else -3,
                  Fraction(len(ar1))/max(1,Fraction(len(ab1),672)) if eligible(af,t-HOUR-28*DAY,ab1,12) else -1,
                  len(distinct(ar1)),sum(r.transaction_type=='cash_in' for r in cash),sum(r.transaction_type=='cash_out' for r in cash),
                  sum(r.amount_minor for r in cash if r.transaction_type=='cash_in'),sum(r.amount_minor for r in cash if r.transaction_type=='cash_out'),len(distinct(cash)),
                  skew(cash)-skew(bcash) if eligible(af,t-29*DAY,ab24,12) and len(bcash)>=8 else -3,
                  min(Fraction(35),Fraction(t-wf,DAY)) if wf is not None else 0,
                  min(Fraction(35),Fraction(t-af,DAY)) if af is not None else 0])
        assert len(f)==40
        # Emit computed values before recording current observation.
        result = tuple(v if i==1 else float(v) for i,v in enumerate(f))
        self.activity[w].append(e)
        for wallet in {e.sender_wallet,e.receiver_wallet}:
            self.first_wallet.setdefault(wallet,t)
        if is_w2w:
            self.incoming[e.receiver_wallet].append(e)
            self.outgoing[e.sender_wallet].append(e)
        if a:
            self.services[a].append(e)
            self.first_agent.setdefault(a,t)
        self.ids.add(e.transaction_id)
        self.last=e.key
        return result
