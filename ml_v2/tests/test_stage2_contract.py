"""Contract and adversarial guard checks, without importing the application."""
import ast
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from contracts import ROOT, safe_path, write_json, load_development
from dataset_generator import generate, pack_positive, rng_for, load_design, assign_event_order


class Stage2Contract(unittest.TestCase):
    def test_equal_timestamp_order_does_not_consult_labels(self):
        events=[{'event_timestamp':'2025-01-01T00:00:00.000000Z','_tie':t,'target':label} for t,label in [(7,0),(3,1),(5,0)]]
        assign_event_order(events)
        self.assertEqual([e['_tie'] for e in events],[3,5,7])
        self.assertEqual([e['transaction_id'] for e in events],[1,2,3])
        for e in events: e['target']=1-e['target']
        assign_event_order(events)
        self.assertEqual([e['_tie'] for e in events],[3,5,7])

    def test_reject_outside_paths(self):
        for path in (ROOT.parent/'server.py', ROOT/'../data/probe.csv',ROOT):
            with self.assertRaises(ValueError): safe_path(path)

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as temp:
            p=Path(temp)/'record.json'
            write_json(p,{'first':1})
            with self.assertRaises(FileExistsError): write_json(p,{'second':2})
            with self.assertRaises(FileExistsError): generate(Path(temp))
            self.assertEqual(json.loads(p.read_text()),{'first':1})

    def test_holdout_and_path_injection_denied_before_io(self):
        for partition in ('final_test','independent','../holdout/final_test','train/../../holdout/independent','TRAIN'):
            with self.assertRaises(PermissionError): load_development(ROOT/'data',partition)
        with self.assertRaises(ValueError): load_development(ROOT/'data','train','../ground_truth')

    def test_all_positive_episodes_complete_across_seeds(self):
        allocation,scenario,_=load_design()
        for seed in (1,7,20260921):
            for p,q in allocation['partitions'].items():
                plans=pack_positive(q,scenario['families'],rng_for(seed,p))
                self.assertEqual(sum(x['size'] for x in plans),q['suspicious'])
                for b,n in enumerate(q['positive_blocks']):
                    self.assertEqual(sum(x['size'] for x in plans if x['block']==b),n)
                for x in plans:
                    self.assertGreaterEqual(x['size'],scenario['families'][x['family']]['min_events'])

    def test_no_application_or_ml_imports(self):
        allowed=set(sys.stdlib_module_names)|{'contracts','dataset_generator','dataset_audit','prepare_design'}
        for file in (ROOT/'src').glob('*.py'):
            tree=ast.parse(file.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):
                    self.assertTrue(all(x.name.split('.')[0] in allowed for x in node.names),str(file))
                if isinstance(node,ast.ImportFrom) and node.module:
                    self.assertIn(node.module.split('.')[0],allowed,str(file))

    def test_junction_or_symlink_escape_rejected(self):
        # A real junction is created on Windows without administrator privileges.
        import os
        import subprocess
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as temp:
            link=Path(temp)/'escape'
            if os.name=='nt':
                result=subprocess.run(['cmd','/c','mklink','/J',str(link),str(ROOT.parent)],capture_output=True)
                if result.returncode: self.skipTest('Junction creation unavailable')
            else:
                link.symlink_to(ROOT.parent,target_is_directory=True)
            try:
                with self.assertRaises(ValueError): safe_path(link/'server.py')
            finally:
                if os.name=='nt': link.rmdir()
                else: link.unlink()


if __name__=='__main__': unittest.main()
