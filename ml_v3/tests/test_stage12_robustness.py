import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from stage12_robustness import stats,dependence,evaluate

class Stage12DiagnosticsTests(unittest.TestCase):
    def test_signed_observations_and_empty_missing_groups(self):
        result=stats([-3,-1,0,1],-3)
        self.assertEqual(result['available_count'],3)
        self.assertEqual(result['mean'],0)
        self.assertEqual(result['min'],-1)
        self.assertEqual(result['missing_rate'],.25)
        self.assertEqual(stats([-1,1])['missing_count'],0)
        self.assertNotIn('mean',stats([-3,-3],-3))
        self.assertIsNone(stats([],-1)['missing_rate'])

    def test_dependence_uses_worst_declared_change_not_precision(self):
        keys=('macro_f1','suspicious_precision','suspicious_recall','suspicious_f1','average_precision','roc_auc','false_positive_rate')
        base={'validation':dict.fromkeys(keys,0.),'domains':{},'families':{},'normal_fpr':{}}
        for increase,expected in [(0,'LOW'),(.019,'LOW'),(.02,'MODERATE'),(.05,'HIGH'),(.15,'EXTREME')]:
            removed={**base,'validation':{**base['validation'],'false_positive_rate':increase,'suspicious_precision':-.99}}
            self.assertEqual(dependence(base,removed)['classification'],expected)
        removed={**base,'validation':{**base['validation'],'average_precision':-.16,'macro_f1':.1}}
        self.assertEqual(dependence(base,removed)['classification'],'EXTREME')

    def test_overlapping_slices_and_threshold_tie(self):
        y=np.array([0,0,1,1]); p=np.array([.1,.5,.5,.1]); empty=np.zeros((4,1))
        domain=np.array([False,False,True,True]); only=np.array([False,False,True,False])
        meta={'domain':{'network':domain},'family':{'N3':domain},'normal':{'routine':y==0},'exclusive':{'network_only':only,'network_overlap':domain&~only}}
        result=evaluate(empty,y,empty,y,p,p,meta)
        self.assertEqual(result['validation']['confusion_matrix'],[[1,1],[1,1]])
        self.assertEqual(result['domain_independence']['network_only']['tp'],1)
        self.assertEqual(result['domain_independence']['network_overlap']['fn'],1)
        self.assertEqual(result['normal_fpr']['routine']['false_positive_rate'],.5)

if __name__=='__main__': unittest.main()
