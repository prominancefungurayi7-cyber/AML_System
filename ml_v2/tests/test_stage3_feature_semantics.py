import math, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from feature_pipeline import extract_rows
from test_stage3_temporal_safety import event

class Semantics(unittest.TestCase):
    def test_wallet_structuring_and_network_manual_values(self):
        rows=[event(1,'2025-01-01T10:00:00.000000Z','a','b',1000000),event(2,'2025-01-01T10:30:00.000000Z','a','b',1020000),event(3,'2025-01-01T11:00:00.000000Z','b','a',50000),event(4,'2025-01-01T11:15:00.000000Z','a','c',1000000)]
        X,ids=extract_rows(rows); f=X[3]
        self.assertEqual(ids[-1],4); self.assertEqual(f[0],1); self.assertEqual(f[1],20200); self.assertEqual(f[2],2)
        self.assertEqual(f[3],1); self.assertAlmostEqual(f[4],100/10100); self.assertEqual(f[5],1)
        self.assertEqual(f[6],1); self.assertEqual(f[7],0); self.assertAlmostEqual(f[8],0); self.assertEqual(f[9],1)
        self.assertEqual(f[10],1); self.assertEqual(f[11],1); self.assertEqual(f[12],1); self.assertEqual(f[14],20200/500)
    def test_cash_not_network_edge_and_agent_manual_values(self):
        rows=[event(1,'2025-01-01T10:00:00.000000Z','a','b',10000,'cash_in','g'),event(2,'2025-01-01T10:15:00.000000Z','a','b',20000,'cash_out','g'),event(3,'2025-01-01T10:30:00.000000Z','a','b',30000,'wallet_to_wallet','g'),event(4,'2025-01-01T10:45:00.000000Z','a','c',40000,'wallet_to_wallet','g')]
        X,_=extract_rows(rows); f=X[3]
        self.assertEqual(f[6],1); self.assertEqual(f[7],0); self.assertEqual(f[16],3); self.assertEqual(f[17],3)
        self.assertEqual(f[18],600); self.assertEqual(f[19],600); self.assertEqual(f[20],1); self.assertEqual(f[21],1)
        self.assertEqual(f[22],1); self.assertEqual(f[23],0); self.assertEqual(f[24],2); self.assertEqual(f[28],1/3)
    def test_hourly_zscore_manual(self):
        rows=[]
        for i in range(7): rows.append(event(i+1,f'2025-01-0{i+1}T0{i}:00:00.000000Z','a','b',(i+1)*10000,'cash_in','g'))
        rows += [event(8,'2025-01-08T12:05:00.000000Z','a','b',10000,'cash_in','g'),event(9,'2025-01-08T12:10:00.000000Z','a','b',10000,'cash_in','g')]
        X,_=extract_rows(rows); self.assertEqual(X[-1][26],0) # seven completed hours all count 1 => zero variance
        self.assertTrue(math.isfinite(X[-1][27])); self.assertEqual(X[-1][28],1/7)

if __name__=='__main__': unittest.main()
