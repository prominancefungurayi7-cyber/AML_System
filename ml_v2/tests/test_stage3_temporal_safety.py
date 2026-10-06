import copy, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from feature_pipeline import extract_rows

def event(i,time,s='a',r='b',amount=10000,kind='wallet_to_wallet',agent=''):
    cash=kind!='wallet_to_wallet'; wallet=s
    return {'transaction_id':str(i),'event_timestamp':time,'sender_wallet':wallet,'receiver_wallet':wallet if cash else r,'amount_minor':str(amount),'currency':'USD','transaction_type':kind,'channel':'agent' if agent else 'direct_wallet','agent_id':agent,'serviced_wallet':wallet if agent else '','agent_flow_direction':'outbound' if kind=='cash_in' else 'inbound' if kind=='cash_out' else 'none'}

class TemporalSafety(unittest.TestCase):
    def setUp(self):
        self.rows=[event(1,'2025-01-01T10:00:00.000000Z'),event(2,'2025-01-01T10:30:00.000000Z',amount=10400),event(3,'2025-01-02T10:00:00.000000Z')]
    def test_future_exclusion(self):
        X,_=extract_rows(self.rows); changed=copy.deepcopy(self.rows); changed[2]['amount_minor']='999999'; changed.append(event(4,'2025-02-01T00:00:00.000000Z'))
        Y,_=extract_rows(changed); self.assertEqual(X[:2],Y[:2])
    def test_current_exclusion_and_permitted_input(self):
        X,_=extract_rows(self.rows); changed=copy.deepcopy(self.rows); changed[1]['amount_minor']='900000'
        Y,_=extract_rows(changed)
        for j in [0,1,2,4,5,6,7,8,9,11,12,13,14,15]: self.assertEqual(X[1][j],Y[1][j])
        self.assertNotEqual(X[1][3],Y[1][3])
    def test_same_timestamp_lower_id_only(self):
        rows=[event(2,'2025-01-01T10:00:00.000000Z'),event(1,'2025-01-01T10:00:00.000000Z')]
        X,ids=extract_rows(rows); self.assertEqual(ids,[1,2]); self.assertEqual(X[0][0],0); self.assertEqual(X[1][0],1)
    def test_partition_and_metadata_independence(self):
        X,_=extract_rows(self.rows); other=[event(99,'2025-01-01T09:59:00.000000Z')]
        extract_rows(other)  # independent partition call cannot mutate retained state
        self.assertEqual(X,extract_rows(self.rows)[0])
        changed=copy.deepcopy(self.rows)
        for e in changed: e.update(target='1',primary_family='changed',signal_strength='strong',episode_id='x')
        self.assertEqual(X,extract_rows(changed)[0])

if __name__=='__main__': unittest.main()
