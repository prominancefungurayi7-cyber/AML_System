"""Small causal checks for the Stage 7 descriptive rules."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from run_stage7 import cycle_exists, relevant_cycle_exists, current_closes_cycle, evidence


class Stage7CausalChecks(unittest.TestCase):
    def test_cycle_can_be_completed_by_current_edge(self):
        prior=[('a','b'),('b','c')]
        current={'sender_wallet':'c','receiver_wallet':'a','transaction_type':'wallet_to_wallet'}
        self.assertFalse(cycle_exists(prior))
        self.assertTrue(current_closes_cycle(prior,current))
        self.assertFalse(relevant_cycle_exists(prior,current))

    def test_unrelated_prior_cycle_is_not_current_endpoint_evidence(self):
        prior=[('a','b'),('b','a')]
        current={'sender_wallet':'c','receiver_wallet':'d','transaction_type':'wallet_to_wallet'}
        self.assertTrue(cycle_exists(prior))
        self.assertFalse(relevant_cycle_exists(prior,current))
        self.assertFalse(current_closes_cycle(prior,current))

    def test_first_episode_event_has_no_prior_episode_motif(self):
        current={'sender_wallet':'a','receiver_wallet':'b','transaction_type':'wallet_to_wallet'}
        self.assertEqual(evidence('reciprocal_relationship_cycle',[],current),'none')
        self.assertEqual(evidence('many_to_one_collection',[],current),'none')


if __name__=='__main__': unittest.main()
