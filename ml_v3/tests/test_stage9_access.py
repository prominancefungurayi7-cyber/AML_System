import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from contracts import load_development, partition_path, safe_path


V3_ROOT = Path(__file__).resolve().parents[1]
ROOT = V3_ROOT / 'data'


class AccessContract(unittest.TestCase):
    def test_development_loader_reads_only_development(self):
        rows = load_development(ROOT, 'train', 'ground_truth')
        self.assertEqual(len(rows), 60000)
        self.assertEqual(load_development(ROOT, 'validation', 'transactions')[0]['transaction_id'], '2')

    def test_evaluation_partitions_are_denied(self):
        with self.assertRaises(PermissionError):
            load_development(ROOT, 'final_test', 'transactions')
        with self.assertRaises(PermissionError):
            load_development(ROOT, 'independent', 'ground_truth')

    def test_paths_cannot_escape_v3_root(self):
        with self.assertRaises(ValueError):
            safe_path(V3_ROOT.parent / 'ml_v2' / 'data')
        self.assertTrue(partition_path(ROOT, 'train').is_relative_to(ROOT))


if __name__ == '__main__':
    unittest.main()
