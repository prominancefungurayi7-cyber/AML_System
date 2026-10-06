import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from reference_evaluator import FAMILIES, evaluate_rows


def event(i, second, sender, receiver):
    return {
        'transaction_id': str(i), 'event_sequence': str(i),
        'event_timestamp': f'2025-01-01T00:00:{second:02d}.000000Z',
        'sender_wallet': sender, 'receiver_wallet': receiver,
        'amount_minor': '1000', 'currency': 'USD',
        'transaction_type': 'wallet_to_wallet', 'channel': 'direct_wallet',
        'agent_id': '', 'serviced_wallet': '', 'agent_flow_direction': 'none',
    }


class UniversalEvaluator(unittest.TestCase):
    def test_all_contract_families_are_registered(self):
        self.assertEqual(len(FAMILIES), 12)
        self.assertEqual(len(set(FAMILIES)), 12)

    def test_n3_uses_an_arbitrary_prior_path(self):
        rows = [event(1, 1, 'receiver', 'mid1'), event(2, 2, 'mid1', 'mid2'),
                event(3, 3, 'mid2', 'sender'), event(4, 4, 'sender', 'receiver')]
        result = evaluate_rows(rows)
        self.assertIn('reciprocal_relationship_cycle', result[-1]['families'])

    def test_future_edges_do_not_label_an_earlier_event(self):
        rows = [event(1, 1, 'sender', 'receiver'), event(2, 2, 'receiver', 'mid'),
                event(3, 3, 'mid', 'sender')]
        result = evaluate_rows(rows)
        self.assertNotIn('reciprocal_relationship_cycle', result[0]['families'])


if __name__ == '__main__':
    unittest.main()
