import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from feature_pipeline import extract


START=datetime(2025,1,1,tzinfo=timezone.utc)


def ev(i, minutes, sender='w', receiver='z', amount=10000, kind='wallet_to_wallet', agent='', serviced=''):
    t=START+timedelta(minutes=minutes)
    return {'transaction_id':str(i),'event_sequence':str(i),'event_timestamp':t.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'sender_wallet':sender,'receiver_wallet':receiver,'amount_minor':str(amount),'currency':'USD',
            'transaction_type':kind,'channel':'agent' if agent else 'direct_wallet','agent_id':agent,
            'serviced_wallet':serviced,'agent_flow_direction':'none'}


class Stage10Features(unittest.TestCase):
    def test_current_and_structuring_quantities(self):
        ids,x=extract([ev(1,0,amount=10000),ev(2,10,amount=10000),ev(3,20,amount=9900)])
        self.assertEqual(ids,['1','2','3']); self.assertEqual(x[-1][0],99.0)
        self.assertEqual(x[-1][3],3.0); self.assertEqual(x[-1][5],3.0); self.assertGreater(x[-1][7],.5)

    def test_cash_and_history_coverage(self):
        _,x=extract([ev(1,0,kind='cash_in',sender='w',receiver='w',amount=5000),ev(2,60,kind='cash_out',sender='w',receiver='w',amount=2000)])
        self.assertEqual(x[-1][2],1.0); self.assertGreaterEqual(x[-1][19],0.0); self.assertGreater(x[-1][29],0.0)
        _,cold=extract([ev(1,0)])
        self.assertEqual(cold[0][29],0.0); self.assertEqual(cold[0][30],0.0)

    def test_network_collection_dispersion_and_paths(self):
        collection=[ev(i,i*10,sender=f's{i}',receiver='r') for i in range(1,5)] + [ev(5,50,sender='s5',receiver='r')]
        _,x=extract(collection); self.assertEqual(x[-1][10],5.0); self.assertEqual(x[-1][11],5.0)
        dispersion=[ev(i,i*10,sender='s',receiver=f'r{i}') for i in range(1,5)] + [ev(5,50,sender='s',receiver='r5')]
        _,x=extract(dispersion); self.assertEqual(x[-1][13],5.0); self.assertEqual(x[-1][14],5.0)
        path=[ev(1,1,sender='r',receiver='m1'),ev(2,2,sender='m1',receiver='m2'),ev(3,3,sender='m2',receiver='s'),ev(4,4,sender='s',receiver='r')]
        _,x=extract(path); self.assertEqual(x[-1][16],3.0); self.assertGreater(x[-1][17],0.0)
        open_path=path[:-1]+[ev(4,4,sender='s',receiver='other')]
        _,x=extract(open_path); self.assertEqual(x[-1][16],0.0)

    def test_pass_through_roles(self):
        rows=[ev(1,0,sender='payer',receiver='w',amount=10000),ev(2,30,sender='w',receiver='out',amount=4000)]
        _,x=extract(rows); self.assertGreaterEqual(x[-1][18],0.0); self.assertGreater(x[-1][19],0.0)
        _,x=extract([ev(1,0,sender='w',receiver='w',kind='cash_in',amount=10000)])
        self.assertEqual(x[-1][18],0.0)

    def test_agent_service_population_concentration_burst_and_cash_direction(self):
        rows=[ev(i,i*5,sender=f's{i}',receiver=f'w{i}',agent='a',serviced=f'w{i}') for i in range(1,6)]
        _,x=extract(rows); self.assertEqual(x[-1][20],5.0); self.assertGreaterEqual(x[-1][24],0.0)
        cash=[ev(1,0,sender='a',receiver='a',kind='cash_in',agent='a',serviced='w',amount=5000),
              ev(2,10,sender='a',receiver='a',kind='cash_out',agent='a',serviced='w',amount=1000)]
        _,x=extract(cash); self.assertLess(x[-1][26],0.0)
        balanced=cash+[ev(3,20,sender='a',receiver='a',kind='cash_out',agent='a',serviced='w',amount=4000)]
        _,x=extract(balanced); self.assertAlmostEqual(x[-1][26],0.0)

    def test_insufficient_vs_adequate_baseline(self):
        few=[ev(1,0),ev(2,10),ev(3,20)]
        _,x=extract(few); self.assertEqual(x[-1][9],-1.0)
        many=[ev(i,i*24*60,sender='w',receiver='z') for i in range(1,31)]
        _,x=extract(many); self.assertGreaterEqual(x[-1][29],28.0); self.assertGreaterEqual(x[-1][9],0.0)


if __name__=='__main__': unittest.main()
