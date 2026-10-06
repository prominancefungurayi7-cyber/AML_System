import sys,unittest,math
from pathlib import Path
from copy import deepcopy
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from test_stage10a_features import event,D,H
from stage13_robustness_improvement import extract_candidate_features

def last(events): return extract_candidate_features(events)[1][-1]

class Stage13Features(unittest.TestCase):
    def test_empty_and_reciprocal_window(self):
        np.testing.assert_array_equal(last([event(1)]),[0,0,-1,0,0,-1])
        rows=[event(1,-7*D,s='r',r='s'),event(2,-1,s='r',r='s'),event(3,0,s='s',r='r')]
        np.testing.assert_array_equal(last(rows)[:3],[1,0,0])

    def test_two_hop_chronology_ties_and_value_spread(self):
        rows=[event(1,0,s='r',r='m',amount=100),event(2,0,s='m',r='s',amount=400),event(3,1,s='s',r='r')]
        x=last(rows); self.assertEqual(x[1],1); self.assertAlmostEqual(x[2],math.log(4))
        rows[0]['transaction_id']='2'; rows[1]['transaction_id']='1'
        np.testing.assert_array_equal(last(rows)[:3],[0,0,-1])

    def test_pair_multiplicity_no_self_loop(self):
        rows=[event(1,0,s='r',r='m'),event(2,1,s='r',r='m'),event(3,2,s='m',r='s'),event(4,3,s='m',r='s'),event(5,4,s='s',r='r')]
        self.assertEqual(last(rows)[1],4)
        np.testing.assert_array_equal(last([event(1,0,s='s',r='s')])[:3],[0,0,-1])

    def test_cash_share_bucket_boundaries_and_cancellation(self):
        rows=[event(1,-24*H,kind='cash_out',aid='a'),event(2,-18*H,kind='cash_out',aid='a'),event(3,-12*H,kind='cash_out',aid='a'),event(4,-6*H,kind='cash_out',aid='a'),event(5,0,kind='cash_out',aid='a')]
        self.assertEqual(last(rows)[3],1); self.assertEqual(last(rows)[4],1)
        rows[-1]=event(5,0,kind='cash_in',aid='a')
        self.assertEqual(last(rows)[4],.5)
        rows[-1]=event(5,0,aid='a')
        self.assertEqual(last(rows)[3],.75); self.assertEqual(last(rows)[4],.75)

    def test_baseline_coverage_minima_and_disjoint_boundaries(self):
        rows=[event(1,-29*D,kind='cash_in',aid='a')]
        rows += [event(i+2,-(i+1)*D,kind='cash_out' if i<8 else 'wallet_to_wallet',aid='a',amount=100) for i in range(12)]
        rows += [event(20,0,kind='cash_out',aid='a',amount=100)]
        self.assertAlmostEqual(last(rows)[5],3.5)
        self.assertEqual(last([r for r in rows if r['transaction_id']!='1'])[5],-1)
        self.assertEqual(last([r for r in rows if r['transaction_id']!='13'])[5],-1)

    def test_prefix_future_current_and_private_metadata_independence(self):
        rows=[event(1,0,s='r',r='m',aid='a'),event(2,1,s='m',r='s',kind='cash_out',aid='a'),event(3,2,s='m',r='s',aid='a'),event(4,3,s='s',r='r',aid='a')]
        ids,x=extract_candidate_features(rows)
        _,extended=extract_candidate_features(rows+[event(5,3,s='r',r='s',aid='a'),event(6,1000,kind='cash_out',aid='a')])
        np.testing.assert_array_equal(x,extended[:4])
        altered=deepcopy(rows)
        for r in altered: r.update(decision_point_target='1',scenario_family='anything',campaign_id='private',risk_score='999')
        np.testing.assert_array_equal(x,extract_candidate_features(altered[::-1])[1])
        altered[-1]['amount_minor']='999999'
        np.testing.assert_array_equal(x[-1],last(altered)) # current W2W amount changes no candidate cash/graph value
        self.assertEqual(last([event(1)])[0],0) # fresh state on each extraction

if __name__=='__main__': unittest.main()
