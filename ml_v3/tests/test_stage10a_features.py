"""Manual examples: times in seconds, money in cents. No dataset access."""
import sys
import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from stage10a_pipeline import extract, prepare, recent, baseline
from stage10a_contract import NAMES

D=86400; H=3600
ZERO=datetime(2025,3,1,tzinfo=timezone.utc)

def event(i,t=0,s='w',r='z',amount=10000,kind='wallet_to_wallet',aid='',sw=None):
    cash=kind!='wallet_to_wallet'
    return dict(transaction_id=str(i),event_sequence=str(i),event_timestamp=(ZERO+timedelta(seconds=t)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                sender_wallet=s,receiver_wallet=s if cash else r,amount_minor=str(amount),currency='USD',transaction_type=kind,
                channel='agent' if aid else 'direct_wallet',agent_id=aid,serviced_wallet=(sw or s) if cash or aid else '',
                agent_flow_direction={'cash_in':'outbound','cash_out':'inbound'}.get(kind,'none'))

def row(events,tid=None):
    ids,x=extract(events)
    return x[-1 if tid is None else ids.index(str(tid))]

def agent_base(cash=False):
    events=[event(1,-40*D,s='old',kind='cash_in',aid='a')]
    for i in range(12):
        kind=('cash_out' if i%2 else 'cash_in') if cash else 'wallet_to_wallet'
        events.append(event(i+2,-(8+7*(i%4))*D-i,s='old',aid='a',kind=kind))
    return events

class Stage10A(unittest.TestCase):
    def test_isolated_and_no_history(self):
        x=row([event(1)])
        self.assertEqual(x[:10],[100.,0.,0.,1.,100.,1.,1.,1.,0.,-1.])
        self.assertEqual(x[10:20],[1.,1.,-1.,1.,1.,-1.,0.,-1.,-1.,-1.])
        self.assertEqual(x[29:],[0.,0.,0.])

    def test_burst_repetition_band_day(self):
        events=[event(1,0,amount=700000),event(2,H,amount=710000),event(3,2*H,amount=10000),event(4,2*H+60,amount=700000)]
        x=row(events)
        # Last 1h has two events; all four remain in the UTC day and 7d.
        self.assertEqual(x[3:9],[2.,21200.,4.,3.,.75,.75])

    def test_wallet_baseline_coverage_count_and_rate(self):
        base=[event(1,-30*D)]+[event(i+2,-2*D-i) for i in range(4)]
        self.assertEqual(row(base+[event(9)])[9],1.)
        self.assertEqual(row(base[:4]+[event(9)])[9],-1.)
        self.assertEqual(row(base[1:]+[event(9)])[9],-1.)
        # Recent activity cannot make a baseline with 3 observations eligible.
        self.assertEqual(row(base[:4]+[event(7,-10),event(8,-5),event(9)])[9],-1.)
        dense=[event(1,-30*D)]+[event(i+2,-2*H-i) for i in range(1344)]
        self.assertEqual(row(dense+[event(2000,-1),event(2001)])[9],1.)

    def test_baseline_exact_boundaries_all_streams(self):
        for L in (H,D,7*D):
            with self.subTest(L=L):
                es=prepare([event(1,-L-28*D),event(2,-L-28*D+1),event(3,-L),event(4,-L+1),event(5)])
                self.assertEqual([x['id'] for x in baseline(es[:-1],es[-1],timedelta(seconds=L))],[2,3])
                self.assertEqual([x['id'] for x in recent(es[:-1],es[-1],timedelta(seconds=L))],[4])

    def test_collection_dispersion(self):
        self.assertEqual(row([event(i,i,s=f's{i}',r='r') for i in range(1,5)])[10:12],[4.,4.])
        self.assertEqual(row([event(i,i,s='w',r=f'r{i}') for i in range(1,5)])[13:15],[4.,4.])

    def test_network_baseline_minimum_and_disjoint(self):
        for direction in ('in','out'):
            def tx(i,t): return event(i,t,s='source' if direction=='in' else 'w',r='w' if direction=='in' else 'dest')
            idx=12 if direction=='in' else 15
            base=[tx(1,-30*D)]+[tx(i+2,-2*D-i) for i in range(4)]
            self.assertEqual(row(base+[tx(9,0)])[idx],1.)
            self.assertEqual(row(base[:4]+[tx(8,-1),tx(9,0)])[idx],-1.)

    def test_paths_manual_eight_cases(self):
        cases=[
          ('valid',[event(1,1,'r','m',20000),event(2,2,'m','s'),event(3,3,'s','r',5000)],3,2.,.25),
          ('reversed',[event(1,1,'m','s'),event(2,2,'r','m'),event(3,3,'s','r')],3,0.,-1.),
          ('part_reversed',[event(1,1,'r','a'),event(2,2,'b','s'),event(3,3,'a','b'),event(4,4,'s','r')],4,0.,-1.),
          ('equal',[event(1,1,'r','m'),event(2,1,'m','s'),event(3,1,'s','r')],3,2.,1.),
          ('future',[event(1,1,'r','m'),event(3,3,'m','s'),event(2,2,'s','r')],2,0.,-1.),
          ('long',[event(i+1,i,f'n{i}',f'n{i+1}') for i in range(6)]+[event(7,7,'n6','n0')],7,0.,-1.),
          ('absent',[event(1,1,'a','b'),event(2,2,'s','r')],2,0.,-1.),
          ('reciprocal',[event(1,1,'r','s',20000),event(2,2,'s','r',5000)],2,1.,.25),
        ]
        for name,events,tid,length,ratio in cases:
            with self.subTest(name=name): self.assertEqual(row(events,tid)[16:18],[length,ratio])

    def test_path_boundaries_ties_simple_and_amount_independence(self):
        for age,expected in ((7*D,0.),(7*D-1,1.),(7*D+1,0.)):
            self.assertEqual(row([event(1,-age,'r','s'),event(2,0,'s','r')])[16],expected)
        # Latest first edge wins among paths of equal length; ratio 100/200=.5.
        self.assertEqual(row([event(1,-2,'r','s',10000),event(2,-1,'r','s',20000),event(3,0,'s','r')])[16:18],[1.,.5])
        # Unrestricted monetary summary, not the complete N3 money conjunction.
        self.assertEqual(row([event(1,-2,'r','m',100),event(2,-1,'m','s',100000),event(3,0,'s','r',200000)])[16:18],[2.,2000.])
        # Repeated-node route cannot yield a path to an otherwise unreachable s.
        self.assertEqual(row([event(1,-3,'r','m'),event(2,-2,'m','r'),event(3,0,'s','r')])[16],0.)

    def test_funding_boundary_manual(self):
        for age,share,hours in ((D-60,.5,(D-60)/H),(D,-1.,-1.),(D+1,-1.,-1.)):
            with self.subTest(age=age):
                x=row([event(1,-age,'payer','w'),event(2,0,amount=5000)])
                self.assertEqual(x[18:20],[share,hours])

    def test_funding_cash_only_and_future(self):
        # Frozen N4 requires a W2W anchor: Cash-In alone never creates it.
        for age in (0,D-60,D,D+1):
            self.assertEqual(row([event(1,-age,kind='cash_in',aid='a'),event(2,0,kind='cash_out',aid='a')])[18:20],[-1.,-1.])
        self.assertEqual(row([event(2,1,'payer','w'),event(1,0)],1)[18:20],[-1.,-1.])

    def test_multiple_anchors_and_cash_after_anchor(self):
        # F=100+50+50=200; O=50+50=100; first inbound 2h ago.
        es=[event(1,-2*H,'payer','w'),event(2,-H,'p2','w',5000),event(3,-H+1,amount=5000,kind='cash_in',aid='a'),event(4,-60,amount=5000),event(5,0,amount=5000)]
        self.assertEqual(row(es)[18:20],[.5,2.])
        # Expired cash predating the anchor is excluded.
        self.assertEqual(row([event(0,-10*D,kind='cash_in',aid='a')]+es)[18:20],[.5,2.])

    def test_current_funding_role(self):
        self.assertEqual(row([event(1,kind='cash_in',aid='a')])[18:20],[0.,-1.])
        self.assertEqual(row([event(1,s='payer',r='w')])[18:20],[-1.,-1.])

    def test_assisted_receiver_does_not_change_sender_subject(self):
        es=[event(1,-10,s='w',r='z'),event(2,0,s='w',r='z',aid='a',sw='z')]
        x=row(es)
        self.assertEqual(x[3],2.); self.assertEqual(x[20],1.)
        self.assertEqual(x[26:28],[0.,0.])

    def test_agent_distinct_novelty_repeated_visits(self):
        # Baseline has one distinct old wallet in each week. Recent has old/new,
        # with new visited three times: distinct novelty 1/2, NOT event rate 3/4.
        es=agent_base()+[event(20,-3,s='new',aid='a'),event(21,-2,s='new',aid='a'),event(22,-1,s='new',aid='a'),event(23,0,s='old',aid='a')]
        self.assertEqual(row(es)[22:24],[2.,.5])
        self.assertEqual(row(agent_base()+[event(20,0,s='old',aid='a')])[22:24],[1.,0.])

    def test_agent_baseline_counts_coverage_and_acceleration(self):
        base=agent_base(); current=event(20,0,s='new',aid='a')
        short_base=[event(1,-40*D,s='old',aid='a')]+[event(i+2,-2*D-i,s='old',aid='a') for i in range(12)]
        self.assertEqual(row(short_base+[current])[21],1.)
        self.assertEqual(row(short_base[:-1]+[event(19,-1,aid='a'),current])[21],-1.)
        self.assertEqual(row(base[:-1]+[current])[21:24],[-1.,-1.,-1.])
        self.assertEqual(row(base[1:]+[current])[22:24],[-1.,-1.])

    def test_baseline_full_coverage_exact_lower_boundary(self):
        for first,expected in ((-28*D-H,1.),(-28*D-H+1,-1.)):
            base=[event(1,first)]+[event(i+2,-2*D-i) for i in range(4)]
            self.assertEqual(row(base+[event(9)])[9],expected)

    def test_path_lexicographic_tie_and_five_edges(self):
        es=[event(1,-4,'r','a',20000),event(2,-3,'a','b'),event(3,-3,'a','c'),event(4,-2,'b','s'),event(5,-2,'c','s'),event(6,0,'s','r',5000)]
        from stage10a_pipeline import select_path
        from collections import defaultdict
        prepared=prepare(es); outgoing=defaultdict(list)
        for e in prepared[:-1]: outgoing[e['sender_wallet']].append(e)
        self.assertEqual([e['id'] for e in select_path(outgoing,prepared[-1])],[1,2,4])
        five=[event(i+1,i,f'n{i}',f'n{i+1}') for i in range(5)]+[event(6,6,'n5','n0')]
        self.assertEqual(row(five)[16:18],[5.,1.])

    def test_agent_concentration_diversification_and_change(self):
        base=[event(1,-40*D,s='old',aid='a')]+[event(i+2,-(i+2)*D,s=f'w{i%5}',aid='a') for i in range(20)]
        concentrated=[event(40+i,-10+i,s='new',aid='a') for i in range(4)]
        diversified=[event(40+i,-10+i,s=f'n{i}',aid='a') for i in range(4)]
        self.assertAlmostEqual(row(base+concentrated)[25],.6)
        self.assertEqual(row(base+concentrated)[24],1.)
        self.assertAlmostEqual(row(base+diversified)[25],.1)
        self.assertEqual(row(base+diversified)[24],.5)
        self.assertEqual(row(base[:-1]+concentrated)[25],-3.)
        one_wallet=[event(i+1,-(i+2)*D,s='same',aid='a') for i in range(25)]+[event(30,-40*D,s='same',aid='a')]
        self.assertEqual(row(one_wallet+concentrated)[25],-3.)

    def test_cash_direction_service_and_signed_missing(self):
        for kind,expected in (('cash_in',-1.),('cash_out',1.)):
            self.assertEqual(row([event(1,kind=kind,aid='a')])[26:28],[expected,expected])
        balanced=[event(1,-1,kind='cash_in',aid='a'),event(2,0,kind='cash_out',aid='a')]
        self.assertEqual(row(balanced)[26:29],[0.,0.,-3.])
        base=[event(1,-40*D,kind='cash_out',aid='a')]+[event(i+2,-(i+2)*D,kind='cash_out',aid='a') for i in range(12)]
        self.assertEqual(row(base+[event(30,-1,kind='cash_in',aid='a'),event(31,0,kind='cash_out',aid='a')])[28],-1.)
        seven_cash=[event(1,-40*D,aid='a')]+[event(i+2,-(i+2)*D,kind='cash_out' if i<7 else 'wallet_to_wallet',aid='a') for i in range(12)]
        self.assertEqual(row(seven_cash+[event(30,0,kind='cash_out',aid='a')])[28],-3.)

    def test_coverage_manual(self):
        for age,expected in ((0,0.),(H,1/24),(28*D,28.),(50*D,28.)):
            es=[event(1,-age,kind='cash_in',aid='a'),event(2,0,kind='cash_out',aid='a')]
            self.assertEqual(row(es)[29:],[expected,expected,expected])

    def test_equal_timestamp_all_families(self):
        es=[event(1,0,'payer','w',aid='a',sw='w'),event(2,0,amount=5000,kind='cash_out',aid='a'),event(3,0,'future','w',aid='a',sw='w')]
        x=row(es,2)
        self.assertEqual(x[3],1.)  # receipt is not structuring activity
        self.assertEqual(x[10:12],[1.,1.]); self.assertEqual(x[18:20],[.5,0.])
        self.assertEqual(x[20],2.); self.assertEqual(x[26:28],[1.,1.])
        self.assertEqual(row([event(1),event(2),event(3)],2)[3],2.)
        self.assertEqual(row([event(1,s='a',r='r'),event(2,s='b',r='r'),event(3,s='c',r='r')],2)[10:12],[2.,2.])
        self.assertEqual(row([event(1,r='a'),event(2,r='b'),event(3,r='c')],2)[13:15],[2.,2.])

    def test_recent_boundary_all_domains(self):
        # Exactly one hour old is excluded from both wallet and agent bursts.
        x=row([event(1,-H,aid='a'),event(2,-H+1,aid='a'),event(3,0,aid='a')])
        self.assertEqual([x[3],x[20]],[2.,2.])
        # Network 24h and wallet sum boundary.
        x=row([event(1,-D),event(2,-D+1),event(3)])
        self.assertEqual([x[4],x[11],x[14]],[200.,2.,2.])
        # 7d cluster and band exclude the exact lower boundary.
        x=row([event(1,-7*D,amount=900000),event(2,0,amount=10000)])
        self.assertEqual(x[7:9],[1.,0.])
        midnight=row([event(1,-1),event(2,0)])
        self.assertEqual(midnight[5:7],[1.,1.])

    def test_future_invariance_and_current_control_every_family(self):
        fixtures=[
          [event(1,-10,amount=10000),event(2,0,amount=20000)],
          [event(1,-2,'z','m'),event(2,-1,'m','w'),event(3,0)],
          [event(1,-2,'payer','w'),event(2,-1,kind='cash_in',aid='a'),event(3,0,kind='cash_out',aid='a')],
          agent_base(True)+[event(30,0,kind='cash_out',aid='a')]]
        amount_allowed={0,4,7,8,17,18,26,28}
        for f,events in enumerate(fixtures):
            with self.subTest(fixture=f):
                current=int(events[-1]['transaction_id']); original=row(events,current)
                future=event(999,0,s='w',r='z',amount=123456,aid='a')
                later=event(1000,D,s='w',r='z',amount=900000,aid='a')
                self.assertEqual(row(events+[future,later],current),original)
                future['amount_minor']='999999'; later['serviced_wallet']='new'
                self.assertEqual(row(events+[future,later],current),original)
                changed=deepcopy(events); changed[-1]['amount_minor']='700000'
                second=row(changed,current)
                for i in range(32):
                    if i not in amount_allowed: self.assertEqual(second[i],original[i],NAMES[i])

    def test_private_metadata_independence_all_families(self):
        events=agent_base()+[event(30,-1,'z','w',aid='a'),event(31,0)]
        mutated=deepcopy(events)
        for x in mutated:
            x.update(scenario_member=1,decision_point_target=1,campaign_id='secret',origin_cohort='any',signal_strength='strong',
                     evidence_families='N3',witness_transaction_ids='[9999]',own_family_onset_transaction_id=9999,scenario_family='S1',
                     campaign_onset_transaction_id=123,evidence_subjects='secret',scenario_strength='strong',predicate_version='unknown')
        self.assertEqual(extract(events),extract(mutated))

    def test_baseline_equal_timestamps_and_current_id_cutoff(self):
        # Both records at the closed baseline upper time are counted; a record
        # at the recent lower time belongs only to the preceding baseline.
        for L in (H,D,7*D):
            es=prepare([event(1,-L),event(2,-L),event(3,0),event(4,0)])
            self.assertEqual([e['id'] for e in baseline(es,es[2],timedelta(seconds=L))],[1,2])
            self.assertEqual(recent(es,es[2],timedelta(seconds=L)),[])
        es=prepare([event(1,0),event(2,0),event(3,0)])
        self.assertEqual([e['id'] for e in recent(es,es[1],timedelta(days=1))],[1])

    def test_exact_current_amount_effects_and_agent_burst(self):
        base=[event(1,-2,'z','m',20000),event(2,-1,'m','w',10000)]
        low=row(base+[event(3,0,amount=5000)])
        high=row(base+[event(3,0,amount=10000)])
        self.assertEqual(low[16:20],[2.,.25,.5,1/H])
        self.assertEqual(high[16:20],[2.,.5,1.,1/H])
        base=[event(1,-40*D,aid='a')]+[event(i+2,-2*D-i,aid='a') for i in range(12)]
        burst=[event(i+30,-4+i,s=f'w{i}',aid='a') for i in range(5)]
        self.assertEqual(row(base+burst)[20:22],[5.,5.])

    def test_partition_isolation_and_duplicate_ids(self):
        a=[event(1,-30*D),event(2,0)]; b=[event(1,0)]
        expected=extract(b); extract(a)
        self.assertEqual(extract(b),expected)
        with self.assertRaises(ValueError): extract([event(1),event(1,1)])

if __name__=='__main__': unittest.main()
