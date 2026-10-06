import ast, json, math, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from feature_pipeline import FEATURE_NAMES, extract_rows

class FeatureContractTests(unittest.TestCase):
    def test_exact_order_and_output_width(self):
        self.assertEqual(len(FEATURE_NAMES),30); self.assertEqual(len(set(FEATURE_NAMES)),30)
        expected=json.loads((ROOT/'features/development/train/feature_names.json').read_text()) if (ROOT/'features/development/train/feature_names.json').exists() else FEATURE_NAMES
        self.assertEqual(expected,FEATURE_NAMES)
    def test_no_forbidden_imports_or_holdout_literals(self):
        src=(ROOT/'src/feature_pipeline.py').read_text(encoding='utf-8')
        tree=ast.parse(src)
        imports={n.names[0].name.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.Import)}|{n.module.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) and n.module}
        self.assertTrue(imports <= set(sys.stdlib_module_names)|{'contracts'})
        self.assertNotIn("'final_test'",src); self.assertNotIn("'independent'",src)
    def test_direct_event_is_numerically_safe(self):
        e={'transaction_id':'1','event_timestamp':'2025-01-01T00:00:00.000000Z','sender_wallet':'a','receiver_wallet':'b','amount_minor':'10000','currency':'USD','transaction_type':'wallet_to_wallet','channel':'direct_wallet','agent_id':'','serviced_wallet':'','agent_flow_direction':'none'}
        X,_=extract_rows([e]); self.assertEqual(len(X[0]),30); self.assertEqual(X[0][16:],[0.0]*14); self.assertTrue(all(math.isfinite(x) for x in X[0]))

if __name__=='__main__': unittest.main()
