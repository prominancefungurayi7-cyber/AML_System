import ast, sys, unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from preprocessing import TrainPreprocessor,CLIPPED_INDICES
from feature_pipeline import FEATURE_NAMES
from model_metrics import metrics

class Stage4Contract(unittest.TestCase):
    def test_clipping_and_scaler_fit_train_only(self):
        train=np.tile(np.arange(1,31,dtype=float),(100,1)); train[:,0]=np.arange(100)
        validation=np.tile(np.arange(1,31,dtype=float),(2,1)); validation[:,0]=[10000,-10000]
        pre=TrainPreprocessor(clip=True,scale=True).fit(train); before=(pre.lower.copy(),pre.upper.copy(),pre.scaler.center_.copy())
        transformed=pre.transform(validation)
        self.assertTrue(np.array_equal(before[0],pre.lower)); self.assertTrue(np.array_equal(before[1],pre.upper)); self.assertTrue(np.array_equal(before[2],pre.scaler.center_))
        self.assertTrue(np.isfinite(transformed).all())
    def test_bounded_features_not_clipped(self):
        bounded={3,5,9,10,11,12,13,15,21,22,23,25,28,29}
        self.assertFalse(bounded & set(CLIPPED_INDICES)); self.assertEqual(len(FEATURE_NAMES),30)
    def test_metric_definition_and_threshold(self):
        m=metrics([0,0,1,1],[.1,.6,.4,.9]); self.assertEqual(m['confusion_matrix'],[[1,1],[1,1]]); self.assertEqual(m['threshold'],.5); self.assertEqual(m['false_positive_rate'],.5)
    def test_no_holdout_or_application_access_in_training_source(self):
        source=(ROOT/'src/train_candidates.py').read_text(encoding='utf-8')
        self.assertNotIn("'final_test'",source); self.assertNotIn("'independent'",source)
        tree=ast.parse(source); forbidden={'server','ai_stage13_features','ai_stage14_model','database','alerts','aml_rules'}
        imported=set()
        for n in ast.walk(tree):
            if isinstance(n,ast.Import): imported.update(x.name.split('.')[0] for x in n.names)
            elif isinstance(n,ast.ImportFrom) and n.module: imported.add(n.module.split('.')[0])
        self.assertFalse(imported&forbidden)

if __name__=='__main__': unittest.main()
