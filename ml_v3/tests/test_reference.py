"""Hand-verifiable examples for every frozen V3 predicate."""
import sys
import unittest
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from common import DAY,HOUR,Event
from reference import ReferenceEvaluator


def e(t,s='w',r='z',amount=10000,kind='wallet_to_wallet',agent='',wallet=None):
    if kind!='wallet_to_wallet': r=s
    wallet=(s if wallet is None else wallet) if agent else ''
    return Event(0,int(t),s,r,amount,kind,'agent' if agent else 'direct_wallet',
                 agent,wallet,{'cash_in':'outbound','cash_out':'inbound'}.get(kind,'none'))


def ordered(rows):
    return [replace(v,transaction_id=i+1) for i,(_,v) in enumerate(sorted(enumerate(rows),key=lambda kv:(kv[1].t,kv[0])))]


def run(rows):
    evaluator=ReferenceEvaluator()
    return [evaluator.step(v) for v in ordered(rows)]


def wb(): return [e(d*DAY) for d in (0,10,15,20,25,30)]
def ab(n=20,diverse=10):
    return [e(0,s='old',kind='cash_in',agent='g')]+[
        e((12+i*.6)*DAY,s=f'old{i%diverse}',kind='cash_in' if i%2 else 'cash_out',agent='g') for i in range(n)]


class Predicates(unittest.TestCase):
    def assertFamily(self,f,rows,expected=True):
        self.assertEqual(f in run(rows)[-1]['families'],expected)

    def test_s1(self):
        rows=[e(40*DAY-(3-i)*60_000_000,amount=a) for i,a in enumerate((18000,4000,4000,4000))]
        self.assertFamily('S1',wb()+rows)
        self.assertFamily('S1',wb()+rows[1:],False)
        self.assertFamily('S1',rows,False)
        rows[0]=replace(rows[0],amount=18001)
        self.assertFamily('S1',wb()+rows,False)

    def test_s2(self):
        rows=[e((38+i*.5)*DAY,amount=a) for i,a in enumerate((5250,5000,5000,5000))]
        self.assertFamily('S2',wb()+rows)
        self.assertFamily('S2',rows,False)
        rows[0]=replace(rows[0],amount=5251)
        self.assertFamily('S2',wb()+rows,False)

    def test_s3(self):
        rows=[e(40*DAY+i*HOUR/2) for i in range(6)]
        self.assertFamily('S3',wb()+rows)
        self.assertFamily('S3',wb()+rows[:-1],False)
        self.assertFamily('S3',rows,False)
        self.assertFamily('S3',wb()+[replace(x,t=40*DAY+i*HOUR//10) for i,x in enumerate(rows)],False)

    def test_s4(self):
        rows=[e((37+i*.5)*DAY,amount=a) for i,a in enumerate((700000,800000,10000,20000,1050000))]
        self.assertFamily('S4',wb()+rows)
        self.assertFamily('S4',rows,False)
        self.assertFamily('S4',wb()+rows[:-1]+[replace(rows[-1],amount=1050001)],False)

    def test_n1(self):
        base=[e(d*DAY,s='old',r='collector') for d in (0,15,20,25,30)]
        rows=[e(40*DAY+i,s=f's{i%3}',r='collector',amount=7500) for i in range(4)]
        self.assertFamily('N1',base+rows)
        self.assertFamily('N1',base+rows[:-1],False)
        self.assertFamily('N1',rows,False)
        self.assertFamily('N1',base+rows[:-1]+[replace(rows[-1],amount=7499)],False)

    def test_n2(self):
        rows=[e(40*DAY+i,r=f'r{i%3}',amount=7500) for i in range(4)]
        self.assertFamily('N2',wb()+rows)
        self.assertFamily('N2',wb()+rows[:-1],False)
        self.assertFamily('N2',rows,False)
        self.assertFamily('N2',wb()+rows[:-1]+[replace(rows[-1],amount=7499)],False)

    def test_n3(self):
        rows=[e(DAY,s='a',r='b'),e(2*DAY,s='b',r='c',amount=5000),e(3*DAY,s='c',r='a',amount=2500)]
        out=run(rows)
        self.assertNotIn('N3',out[0]['families']); self.assertNotIn('N3',out[1]['families'])
        self.assertIn('N3',out[2]['families'])
        self.assertFamily('N3',rows[:-1]+[replace(rows[-1],amount=2499)],False)
        self.assertFamily('N3',[replace(rows[1],t=0),rows[0],rows[-1]],False)
        expired=[replace(rows[0],t=0),rows[1],replace(rows[-1],t=7*DAY)]
        self.assertFamily('N3',expired,False)
        self.assertFamily('N3',expired[:-1]+[replace(expired[-1],t=7*DAY-1)])

    def test_n4(self):
        self.assertFamily('N4',[e(0,kind='cash_in',agent='g')],False)
        funding=e(0,s='payer',r='w',amount=10000)
        self.assertFamily('N4',[funding],False)
        partial=e(HOUR,amount=4999)
        self.assertFamily('N4',[funding,partial],False)
        exact=replace(partial,amount=5000)
        self.assertFamily('N4',[funding,exact])
        self.assertFamily('N4',[funding,exact,e(2*HOUR,amount=5001)],False)
        self.assertFamily('N4',[funding,replace(exact,t=DAY)],False)
        self.assertFamily('N4',[funding,replace(exact,t=DAY-1)])
        self.assertFamily('N4',[funding,e(HOUR,kind='cash_out',agent='g',amount=5000)])

    def test_a1(self):
        rows=[e(40*DAY+i,s=f'new{i}',kind='cash_in',agent='g') for i in range(6)]
        self.assertFamily('A1',ab(12,2)+rows)
        self.assertFamily('A1',ab(12,2)+rows[:-1],False)
        self.assertFamily('A1',rows,False)

    def test_a2(self):
        rows=[e(40*DAY+i,s=('x' if i<7 else 'y') if i<13 else f'other{i}',kind='cash_in',agent='g') for i in range(20)]
        self.assertFamily('A2',ab()+rows)
        self.assertFamily('A2',rows,False)
        rows[12]=replace(rows[12],sender='other12',receiver='other12',wallet='other12')
        self.assertFamily('A2',ab()+rows,False)

    def test_a3(self):
        rows=[e(40*DAY+i,s=f'new{i%3}',kind='cash_in',agent='g') for i in range(5)]
        self.assertFamily('A3',ab(12)+rows)
        self.assertFamily('A3',ab(12)+rows[:-1],False)
        self.assertFamily('A3',rows,False)

    def test_a4(self):
        rows=[e(40*DAY+i,s=f'x{i%3}',amount=8000 if i<5 else 10000,kind='cash_out' if i<5 else 'cash_in',agent='g') for i in range(6)]
        self.assertFamily('A4',ab(12)+rows)
        self.assertFamily('A4',rows,False)
        rows[0]=replace(rows[0],amount=7999)
        self.assertFamily('A4',ab(12)+rows,False)

    def test_equal_time_and_prefix_safety(self):
        rows=[e(0,s='a',r='b'),e(0,s='b',r='c'),e(0,s='c',r='a')]
        events=ordered(rows); evaluator=ReferenceEvaluator()
        prefix=[evaluator.step(v) for v in events[:2]]
        self.assertNotIn('N3',prefix[-1]['families'])
        self.assertIn('N3',evaluator.step(events[-1])['families'])
        self.assertEqual(prefix,run(rows)[:2])
        self.assertEqual(prefix,run(rows+[e(DAY,s='c',r='b')])[:2])
        with self.assertRaises(ValueError): evaluator.step(events[-1])

    def test_agent_assistance_uses_serviced_endpoint_not_float(self):
        rows=[e(40*DAY+i,s='source',r=f'new{i}',agent='g',wallet=f'new{i}') for i in range(6)]
        self.assertFamily('A1',ab(12,2)+rows)
        self.assertFamily('A4',ab(12,2)+rows,False)
        direct=[replace(v,agent='',wallet='',channel='direct_wallet') for v in rows]
        self.assertFamily('A1',ab(12,2)+direct,False)

    def test_coverage_boundary_and_strict_lower_window(self):
        base=[e(0,s='old',r='collector')]+[e(d*DAY,s='old',r='collector') for d in (1,2,3,4)]
        rows=[e(29*DAY,s=f's{i}',r='collector') for i in range(4)]
        self.assertFamily('N1',base+rows)
        self.assertFamily('N1',[replace(base[0],t=1)]+base[1:]+rows,False)
        s1=[e(40*DAY-HOUR),e(40*DAY-2),e(40*DAY-1),e(40*DAY)]
        self.assertFamily('S1',wb()+s1,False)


if __name__=='__main__': unittest.main()
