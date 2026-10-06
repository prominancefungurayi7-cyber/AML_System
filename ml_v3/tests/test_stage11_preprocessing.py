import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from stage11_preprocessing import Stage11Preprocessor,MODES,HEAVY
from stage10a_contract import FEATURES

class PreprocessingTests(unittest.TestCase):
    def test_marker_specificity_and_train_only_transforms(self):
        x=np.ones((10,32)); x[:,0]=np.arange(10)+1; x[:,4]=np.arange(10)+1
        for i,f in enumerate(FEATURES):
            if f[7] is not None: x[0,i]=f[7]
        x[0,26]=-1; x[0,27]=-1; x[1,25]=-1; x[1,28]=-1
        for mode in MODES:
            p=Stage11Preprocessor(mode).fit(x); before=p.record(); z=p.transform(x)
            self.assertEqual(z.shape,(10,32))
            p.transform(np.full((2,32),99999.)); self.assertEqual(before,p.record())
            base=p._base(x)
            self.assertEqual(base[0,26],-1); self.assertEqual(base[0,27],-1)
            self.assertEqual(base[1,25],-1); self.assertEqual(base[1,28],-1)
            if mode in ('imputed','robust'):
                self.assertEqual(base[0,25],np.median(x[1:,25]))
                self.assertEqual(base[0,9],1.)
            else:
                self.assertEqual(base[0,25],-3.); self.assertEqual(base[0,9],-1.)
            self.assertTrue(set(p.bounds_)<=set(HEAVY))
            if mode in ('clipped','robust','robust_sentinel'):
                np.testing.assert_allclose(p.bounds_[0],[1.045,9.955])
                np.testing.assert_array_equal(p.bounds_[17],[1.,1.])

    def test_fixed_threshold_confusion_orientation(self):
        from run_stage11 import metrics
        result=metrics(np.array([0,0,1,1]),np.array([.1,.5,.49,.8]))
        self.assertEqual(result['confusion_matrix'],[[1,1],[1,1]])
        self.assertEqual(result['macro_f1'],.5)
        self.assertEqual(result['false_positive_rate'],.5)
        self.assertEqual(result['suspicious_recall'],.5)
        self.assertEqual(result['threshold'],.5)

if __name__=='__main__': unittest.main()
