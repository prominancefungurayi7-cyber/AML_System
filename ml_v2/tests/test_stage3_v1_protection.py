import ast, sys, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class V1Protection(unittest.TestCase):
    def test_stage3_sources_are_v2_local_and_do_not_import_application(self):
        forbidden={'server','ai_stage13_features','ai_stage14_model','alerts','aml_rules','database'}
        for file in [ROOT/'src/feature_pipeline.py',ROOT/'src/feature_audit.py',ROOT/'src/run_stage3.py']:
            self.assertTrue(file.resolve().is_relative_to(ROOT.resolve()))
            tree=ast.parse(file.read_text(encoding='utf-8'))
            imported=set()
            for node in ast.walk(tree):
                if isinstance(node,ast.Import): imported.update(x.name.split('.')[0] for x in node.names)
                elif isinstance(node,ast.ImportFrom) and node.module: imported.add(node.module.split('.')[0])
            self.assertFalse(imported & forbidden)
    def test_only_development_feature_roots_are_named(self):
        source=(ROOT/'src/run_stage3.py').read_text(encoding='utf-8')
        self.assertIn("ROOT/'features/development'",source)
        self.assertNotIn('features/holdout',source)

if __name__=='__main__': unittest.main()
