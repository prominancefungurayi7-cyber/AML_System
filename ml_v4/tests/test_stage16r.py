"""Hand-derived fixtures and implementation boundary tests; no production draw."""
import ast
import dataclasses
import math
from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'generation'))
from stage16r_contract import Event,DAY,HOUR,FAMILIES,timestamp,window,validate_event,event_from_row
from stage16r_evaluator import Evaluator,replay,return_path,cash_stats
from stage16r_generator import bounded_shift,cents,large_amount,motif_count,RANGES,MATCHES
from stage16r_loader import development_path


def event(t,ident,w='w',typ='cash_in',amount=10000,agent='a',receiver=None,serviced=None):
    if typ=='wallet_to_wallet':
        return Event(ident,timestamp(t),w,receiver or 'r',amount,'USD',typ,'agent' if agent else 'direct_wallet',agent,serviced or (w if agent else ''),'none')
    return Event(ident,timestamp(t),w,w,amount,'USD',typ,'agent',agent,w,typ)


def result(rows):
    return replay(sorted(rows,key=lambda e:e.key))[-1]


def baseline(count=4,agent='a',w='w'):
    return [event(0,1,w=w,agent=agent)]+[event(30*DAY+i,2+i,w=w,agent=agent) for i in range(count)]


class Predicates(unittest.TestCase):
    def test_structuring_positive_and_count_boundaries(self):
        fixtures={
            'S1':[event(50*DAY+i*60_000000,100+i,amount=a) for i,a in enumerate([7000,8000,9000,10000])],
            'S2':[event(47*DAY+i*DAY,100+i,amount=6000) for i in range(4)],
            'S3':[event(50*DAY+i*HOUR,100+i) for i in range(6)],
            'S4':[event(46*DAY+i*DAY,100+i,amount=a) for i,a in enumerate([800000,900000,600000,500000,800000])]
        }
        for family,recent in fixtures.items():
            with self.subTest(family=family):
                self.assertIn(family,result(baseline()+recent)['families'])
                self.assertNotIn(family,result(baseline(3)+recent)['families'])
        s1=fixtures['S1']
        self.assertNotIn('S1',result(baseline()+s1[1:])['families'])
        self.assertNotIn('S2',result(baseline()+fixtures['S2'][1:])['families'])
        self.assertNotIn('S3',result(baseline()+fixtures['S3'][1:])['families'])
        self.assertNotIn('S4',result(baseline()+fixtures['S4'][1:])['families'])

    def test_network_collection_dispersion(self):
        for family in ('N1','N2'):
            def row(t,i):
                return event(t,i,w='s'+str(i) if family=='N1' else 'w',receiver='w' if family=='N1' else 'r'+str(i),typ='wallet_to_wallet',agent='')
            old=[row(0,1)]+[row(30*DAY+i,2+i) for i in range(4)]
            recent=[row(50*DAY+i*HOUR,100+i) for i in range(4)]
            self.assertIn(family,result(old+recent)['families'])
            self.assertNotIn(family,result(old[:-1]+recent)['families'])

    def test_agent_a1_exact_35day_and_baseline(self):
        t=50*DAY
        old=[event(t-35*DAY,1,w='old')]
        for week,day in enumerate([20,27,34,41]):
            old += [event(day*DAY+j,10+week*3+j,w='b'+str(j)) for j in range(3)]
        recent=[event(t-5*DAY+i*DAY,100+i,w='new'+str(i)) for i in range(6)]
        self.assertIn('A1',result(old+recent)['families'])
        younger=[dataclasses.replace(old[0],event_timestamp=timestamp(t-35*DAY+1))]+old[1:]
        self.assertNotIn('A1',result(younger+recent)['families'])
        self.assertNotIn('A1',result(old[:-1]+recent)['families'])
        # First observation at lower boundary establishes age but not baseline count.
        state=Evaluator()
        for e in sorted(old+recent[:-1],key=lambda e:e.key): state.process(e)
        self.assertEqual(len(window(state.services['a'],t-35*DAY,t-7*DAY)),12)
        self.assertNotIn(old[0],window(state.services['a'],t-35*DAY,t-7*DAY))

    def test_a2_a3_a4(self):
        old=[event(0,1)] + [event(30*DAY+i,2+i,w='b'+str(i%10),typ='cash_in' if i%2 else 'cash_out') for i in range(20)]
        recent=[event(50*DAY+i*60_000000,100+i,w='r'+str(i%2) if i<6 else 'other'+str(i)) for i in range(8)]
        self.assertIn('A2',result(old+recent)['families'])
        self.assertNotIn('A2',result(old[:-1]+recent)['families'])
        burst=[event(50*DAY+i*60_000000,100+i,w='w'+str(i%3)) for i in range(5)]
        self.assertIn('A3',result(old[:13]+burst)['families'])
        self.assertNotIn('A3',result(old[:12]+burst)['families'])
        cash=[event(50*DAY+i*60_000000,100+i,w='w'+str(i%3),typ='cash_out' if i else 'cash_in') for i in range(6)]
        self.assertIn('A4',result(old[:13]+cash)['families'])
        self.assertNotIn('A4',result(old[:12]+cash)['families'])
        stats=cash_stats(cash)
        self.assertEqual((stats['in_count'],stats['out_count'],stats['in_value'],stats['out_value'],stats['distinct']),(1,5,10000,50000,3))
        self.assertEqual(stats['count_skew'],stats['value_skew'])

    def test_a4_assisted_roles(self):
        assisted=event(30*DAY,2,w='sender',receiver='receiver',typ='wallet_to_wallet',serviced='receiver')
        direct=event(30*DAY+1,3,w='sender',receiver='other',typ='wallet_to_wallet',agent='')
        state=Evaluator(); state.process(assisted); state.process(direct)
        self.assertEqual([x.serviced_wallet for x in state.services['a']],['receiver'])
        self.assertEqual(cash_stats(state.services['a'])['in_count'],0)
        self.assertEqual(cash_stats(state.services['a'])['value_skew'],0)

    def test_n4_funding_and_residual(self):
        funding=event(50*DAY,1,w='payer',receiver='w',typ='wallet_to_wallet',agent='')
        current=event(50*DAY+HOUR,2,typ='cash_out',amount=5000)
        self.assertIn('N4',result([funding,current])['families'])
        self.assertNotIn('N4',result([dataclasses.replace(funding,transaction_type='cash_in',sender_wallet='w',receiver_wallet='w',channel='agent',agent_id='a',serviced_wallet='w',agent_flow_direction='cash_in'),current])['families'])
        self.assertNotIn('N4',result([funding,dataclasses.replace(current,amount_minor=10001)])['families'])
        self.assertNotIn('N4',result([funding,dataclasses.replace(current,amount_minor=4999)])['families'])

    def test_n3_paths_and_amount_boundaries(self):
        for length in range(1,7):
            nodes=['r']+['v'+str(i) for i in range(length-1)]+['s']
            edges=[event(i*HOUR,10+i,w=a,receiver=b,typ='wallet_to_wallet',amount=10000,agent='') for i,(a,b) in enumerate(zip(nodes,nodes[1:]))]
            current=event(10*HOUR,100,w='s',receiver='r',typ='wallet_to_wallet',amount=2500,agent='')
            self.assertEqual(return_path(current,edges) is not None,length<=5)
            if length<=5:
                self.assertIsNotNone(return_path(dataclasses.replace(current,amount_minor=12500),edges))
                self.assertIsNone(return_path(dataclasses.replace(current,amount_minor=12501),edges))
                self.assertIsNone(return_path(dataclasses.replace(current,amount_minor=2499),edges))
        current=event(10*HOUR,100,w='s',receiver='r',typ='wallet_to_wallet',amount=10000,agent='')
        valid=[event(HOUR,1,w='r',receiver='x',typ='wallet_to_wallet',agent=''),event(2*HOUR,2,w='x',receiver='s',typ='wallet_to_wallet',agent='')]
        reverse=[dataclasses.replace(valid[0],event_timestamp=timestamp(3*HOUR)),valid[1]]
        self.assertIsNone(return_path(current,reverse))
        self.assertIsNone(return_path(current,[dataclasses.replace(valid[1],event_timestamp=timestamp(11*HOUR)),valid[0]]))
        self.assertIsNone(return_path(current,[]))
        repeated=[event(HOUR,1,w='r',receiver='x',amount=10000,typ='wallet_to_wallet',agent=''),event(2*HOUR,2,w='x',receiver='r',amount=30000,typ='wallet_to_wallet',agent=''),event(3*HOUR,3,w='r',receiver='s',amount=90000,typ='wallet_to_wallet',agent='')]
        self.assertIsNone(return_path(current,repeated))
        self.assertIsNotNone(return_path(current,repeated+valid))
        self.assertIsNone(return_path(current,[valid[0],dataclasses.replace(valid[1],amount_minor=40001)]))
        self.assertIsNotNone(return_path(current,[valid[0],dataclasses.replace(valid[1],amount_minor=40000)]))
        with self.assertRaises(ValueError): validate_event(dataclasses.replace(current,receiver_wallet='s'))

    def test_n3_equal_time_and_future(self):
        current=event(DAY,10,w='s',receiver='r',typ='wallet_to_wallet',agent='')
        prior=event(DAY,9,w='r',receiver='s',typ='wallet_to_wallet',agent='')
        self.assertIsNotNone(return_path(current,[prior]))
        self.assertIsNone(return_path(current,[dataclasses.replace(prior,transaction_id=11)]))
        self.assertIsNone(return_path(current,[dataclasses.replace(prior,event_timestamp=timestamp(DAY+1))]))

    def test_window_endpoints_current_once_and_partition_reset(self):
        current=event(50*DAY,100)
        lower=event(current.time-HOUR,1)
        upper=event(current.time,99)
        state=Evaluator(); state.process(lower); state.process(upper)
        answer=state.evaluate(current)
        self.assertEqual(len(state.activity['w']),2)
        state.observe(current)
        self.assertEqual(len(state.activity['w']),3)
        self.assertEqual(window([lower,upper],current.time-HOUR,current.time),[upper])
        self.assertIn(lower,window([lower],current.time-HOUR-28*DAY,current.time-HOUR))
        with self.assertRaises(ValueError): state.process(current)
        self.assertEqual(Evaluator().process(current)['ground_truth_label'],0)

    def test_future_and_provenance_independence(self):
        rows=baseline()+[event(50*DAY+i*60_000000,100+i) for i in range(5)]
        first=replay(rows)
        self.assertEqual(replay(rows+[event(51*DAY,200)] )[:len(rows)],first)
        self.assertEqual(replay(rows),first)
        row=dataclasses.asdict(rows[0]); row['origin']='malicious'
        with self.assertRaises(ValueError): event_from_row(row)
        with self.assertRaises(TypeError): Evaluator().process(row)

    def test_s3_midnight_and_calendar_translation(self):
        rows=baseline()+[event(50*DAY+i*HOUR,100+i) for i in range(6)]
        self.assertIn('S3',result(rows)['families'])
        next_day=event(51*DAY,200)
        self.assertNotIn('S3',result(rows+[next_day])['families'])
        translated=[dataclasses.replace(e,event_timestamp=timestamp(e.time+DAY)) for e in rows]
        self.assertEqual([x['families'] for x in replay(rows)],[x['families'] for x in replay(translated)])


class Contracts(unittest.TestCase):
    def test_motif_counts_and_hard_mapping(self):
        rng=np.random.Generator(np.random.PCG64DXSM(881601))
        for e in range(8,21):
            for family in FAMILIES:
                for _ in range(5):
                    m,g=motif_count(rng,family,e)
                    self.assertTrue(0<m<=e)
                    if family=='N3': self.assertEqual(m,g['V']+g['K'])
                    else: self.assertTrue(RANGES[family][0]<=m<=RANGES[family][1])
        self.assertEqual(set(MATCHES),{'H'+str(i) for i in range(1,9)})

    def test_amounts_conditional_shift_rounding(self):
        rng=np.random.Generator(np.random.PCG64DXSM(881602))
        # Nonproduction amount-only fixtures; never observable events or labels.
        values=[large_amount(rng) for _ in range(80)]
        self.assertTrue(all(5000<=x<=13000 for x in values))
        ordered=sorted(values)
        shifted=[bounded_shift(x) for x in ordered]
        self.assertEqual(shifted,sorted(shifted))
        self.assertTrue(all(5000<=x<=13000 for x in shifted))
        self.assertEqual(bounded_shift(5000),5000)
        self.assertEqual(bounded_shift(13000),13000)
        self.assertEqual(cents(5000.005),500001)
        self.assertAlmostEqual(bounded_shift(math.sqrt(5000*13000))/math.sqrt(5000*13000),1.15)

    def test_loader_fails_closed(self):
        for partition in ('final_test','independent_evaluation','../evaluation','Train','train/../final_test','*','train\\..\\evaluation'):
            with self.assertRaises(PermissionError): development_path(partition,'transactions.csv')
        for filename in ('../transactions.csv','private_provenance.json','X.csv','*'):
            with self.assertRaises(PermissionError): development_path('train',filename)

    def test_source_independence(self):
        base=Path(__file__).resolve().parents[1]/'generation'
        for name,forbidden in [('stage16r_generator.py',{'stage16r_evaluator','sklearn'}),('stage16r_evaluator.py',{'stage16r_generator','sklearn'})]:
            tree=ast.parse((base/name).read_text())
            imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
            self.assertFalse(set(imports)&forbidden)
        tree=ast.parse((base/'stage16r_evaluator.py').read_text())
        private={'scenario_id','scenario_family','campaign_id','origin','strength','archetype','profile','population_unit','activation_schedule','intended_onset','event_role','context_role'}
        self.assertFalse({n.attr for n in ast.walk(tree) if isinstance(n,ast.Attribute)}&private)

    def test_identity_renaming(self):
        rows=baseline()+[event(50*DAY+i*60_000000,100+i,w='w') for i in range(5)]
        renamed=[dataclasses.replace(e,sender_wallet='new_'+e.sender_wallet,receiver_wallet='new_'+e.receiver_wallet,serviced_wallet='new_'+e.serviced_wallet,agent_id='new_'+e.agent_id) for e in rows]
        self.assertEqual([r['families'] for r in replay(rows)],[r['families'] for r in replay(renamed)])

    def test_seal_primitive_on_non_dataset_bytes(self):
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'evaluation'))
        from stage16r_seal import protect,unprotect
        data=b'cryptographic implementation fixture; no dataset contents'
        sealed=protect(data)
        self.assertNotEqual(sealed,data)
        self.assertEqual(unprotect(sealed),data)


if __name__=='__main__': unittest.main(verbosity=2)
