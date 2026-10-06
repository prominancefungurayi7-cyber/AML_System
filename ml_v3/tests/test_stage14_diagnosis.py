import sys,unittest
from pathlib import Path
from datetime import datetime,timedelta,timezone
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from stage14_growth_diagnosis import primitives,summary,grid_bins,grid_codes
from stage10a_pipeline import extract

class DiagnosisTests(unittest.TestCase):
    def test_marker_and_quantile(self):
        s=summary([-1,0,1,2,3],-1)
        self.assertEqual(s['missing_count'],1); self.assertEqual(s['mean'],1.5)
        self.assertAlmostEqual(s['q99'],2.97)
        # Signed skews can legitimately equal -1.
        self.assertEqual(summary([-1,0,1])['available_count'],3)

    def test_frozen_train_bins(self):
        edges=grid_bins(np.array([-1.,0.,1.,2.,3.]),-1)
        saved=list(edges); codes=grid_codes(np.array([-1.,-100.,100.]),edges,-1)
        self.assertEqual(codes.tolist(),[-1,0,3]); self.assertEqual(edges,saved)

    def test_growth_coverage_and_tied_keys(self):
        now=datetime(2025,3,1,tzinfo=timezone.utc)
        def e(i,d,w):
            return dict(transaction_id=str(i),event_timestamp=(now+timedelta(days=d)).isoformat(),sender_wallet=w,receiver_wallet=w,
                        amount_minor='100',transaction_type='cash_in',agent_id='a',serviced_wallet=w)
        raw=[e(1,-35,'old')]+[e(i+2,-30+i,'old'+str(i%3)) for i in range(12)]+[e(20,0,'new1'),e(21,0,'new2')]
        ids,z=primitives(raw); _,x=extract(raw)
        self.assertTrue(np.array_equal(z[:,0],np.array(x)[:,22]))
        self.assertEqual(z[-1,3],2); self.assertEqual(z[-1,7],1)
        earlier=z.copy(); _,future=primitives(raw+[e(22,1,'future')])
        self.assertTrue(np.array_equal(earlier,future[:-1]))
        # Changing first observation to 34d makes feature ineligible at current.
        raw[0]=e(1,-34,'old'); _,z=primitives(raw)
        self.assertEqual(z[-1,0],-1); self.assertEqual(z[-1,9],1)

if __name__=='__main__': unittest.main()
