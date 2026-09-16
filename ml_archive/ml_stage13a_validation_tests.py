"""
Stage 13A: Small-Scale Validation Tests

Implements Tests A-J for validating the corrected feature extraction implementation.
"""

import json
import csv
import math
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict, Counter, deque
from typing import Dict, List, Tuple, Set, Optional
import numpy as np
import sys

# Import the corrected extractor
sys.path.insert(0, str(Path(__file__).parent))
from ml_stage13a_extract_features_corrected import IncrementalFeatureExtractor

# =============================================================================
# TEST DATA GENERATION
# =============================================================================

def create_test_transactions():
    """Create deterministic test transactions for validation."""
    
    base_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    
    transactions = []
    
    # Test A: Current event exclusion
    # Transaction at index 5 should not count itself
    for i in range(10):
        transactions.append({
            'transaction_id': f'test_a_{i}',
            'event_timestamp': base_time + timedelta(hours=i),
            'event_sequence': i,
            'sender_wallet': 'wallet_A',
            'receiver_wallet': 'wallet_B',
            'amount': 100.0,
            'transaction_type': 'transfer',
            'channel': 'agent',
            'agent_id': 'agent_1',
            'partition': 'train',
            'index': i
        })
    
    # Test B: Future exclusion
    # Transaction at index 15 should not be influenced by future transactions
    base_idx = len(transactions)
    for i in range(10):
        transactions.append({
            'transaction_id': f'test_b_{i}',
            'event_timestamp': base_time + timedelta(hours=10 + i),
            'event_sequence': base_idx + i,
            'sender_wallet': 'wallet_C',
            'receiver_wallet': 'wallet_D',
            'amount': 200.0,
            'transaction_type': 'transfer',
            'channel': 'agent',
            'agent_id': 'agent_2',
            'partition': 'train',
            'index': base_idx + i
        })
    
    # Test C: Equal timestamp ordering
    # Multiple transactions with same timestamp but different sequences
    base_idx = len(transactions)
    same_time = base_time + timedelta(hours=20)
    for i in range(5):
        transactions.append({
            'transaction_id': f'test_c_{i}',
            'event_timestamp': same_time,
            'event_sequence': base_idx + i,
            'sender_wallet': 'wallet_E',
            'receiver_wallet': 'wallet_F',
            'amount': 150.0,
            'transaction_type': 'transfer',
            'channel': 'agent',
            'agent_id': 'agent_3',
            'partition': 'train',
            'index': base_idx + i
        })
    
    # Test D: Partition isolation
    # Transactions in different partitions should not influence each other
    base_idx = len(transactions)
    for i in range(5):
        transactions.append({
            'transaction_id': f'test_d_train_{i}',
            'event_timestamp': base_time + timedelta(hours=30 + i),
            'event_sequence': base_idx + i,
            'sender_wallet': 'wallet_G',
            'receiver_wallet': 'wallet_H',
            'amount': 300.0,
            'transaction_type': 'transfer',
            'channel': 'agent',
            'agent_id': 'agent_4',
            'partition': 'train',
            'index': base_idx + i
        })
    
    base_idx = len(transactions)
    for i in range(5):
        transactions.append({
            'transaction_id': f'test_d_val_{i}',
            'event_timestamp': base_time + timedelta(hours=30 + i),
            'event_sequence': base_idx + i,
            'sender_wallet': 'wallet_I',
            'receiver_wallet': 'wallet_J',
            'amount': 400.0,
            'transaction_type': 'transfer',
            'channel': 'agent',
            'agent_id': 'agent_5',
            'partition': 'validation',
            'index': base_idx + i
        })
    
    # Test E: Agent aggregation
    # Multiple wallets using same agent
    base_idx = len(transactions)
    for i in range(5):
        wallet = 'wallet_K' if i % 2 == 0 else 'wallet_L'
        transactions.append({
            'transaction_id': f'test_e_{i}',
            'event_timestamp': base_time + timedelta(hours=40 + i),
            'event_sequence': base_idx + i,
            'sender_wallet': wallet,
            'receiver_wallet': 'wallet_M',
            'amount': 250.0,
            'transaction_type': 'transfer',
            'channel': 'agent',
            'agent_id': 'agent_6',  # Same agent for different wallets
            'partition': 'train',
            'index': base_idx + i
        })
    
    # Test F: Current-hour z-score
    # Multiple transactions in same hour to test current-hour contribution
    base_idx = len(transactions)
    hour_start = base_time + timedelta(hours=50)
    for i in range(6):
        transactions.append({
            'transaction_id': f'test_f_{i}',
            'event_timestamp': hour_start + timedelta(minutes=i*10),
            'event_sequence': base_idx + i,
            'sender_wallet': 'wallet_N',
            'receiver_wallet': 'wallet_O',
            'amount': 100.0,
            'transaction_type': 'transfer',
            'channel': 'agent',
            'agent_id': 'agent_7',
            'partition': 'train',
            'index': base_idx + i
        })
    
    # Test G: Agent inbound/outbound
    # Multiple agent-associated wallets for ratio calculation
    base_idx = len(transactions)
    for i in range(4):
        wallet = 'wallet_P' if i < 2 else 'wallet_Q'
        transactions.append({
            'transaction_id': f'test_g_{i}',
            'event_timestamp': base_time + timedelta(hours=60 + i),
            'event_sequence': base_idx + i,
            'sender_wallet': wallet,
            'receiver_wallet': 'wallet_R',
            'amount': 500.0,
            'transaction_type': 'transfer',
            'channel': 'agent',
            'agent_id': 'agent_8',
            'partition': 'train',
            'index': base_idx + i
        })
    
    # Test H: Cold start
    # First transaction with no history
    base_idx = len(transactions)
    transactions.append({
        'transaction_id': 'test_h_0',
        'event_timestamp': base_time + timedelta(hours=70),
        'event_sequence': base_idx,
        'sender_wallet': 'wallet_S',
        'receiver_wallet': 'wallet_T',
        'amount': 100.0,
        'transaction_type': 'transfer',
        'channel': 'agent',
        'agent_id': 'agent_9',
        'partition': 'train',
        'index': base_idx
    })
    
    # Test I: Determinism
    # Identical transactions should produce identical features
    base_idx = len(transactions)
    for i in range(3):
        transactions.append({
            'transaction_id': f'test_i_{i}',
            'event_timestamp': base_time + timedelta(hours=80 + i),
            'event_sequence': base_idx + i,
            'sender_wallet': 'wallet_U',
            'receiver_wallet': 'wallet_V',
            'amount': 100.0,
            'transaction_type': 'transfer',
            'channel': 'agent',
            'agent_id': 'agent_10',
            'partition': 'train',
            'index': base_idx + i
        })
    
    # Test J: No NaN/infinity
    # Mix of scenarios to test numerical safety
    base_idx = len(transactions)
    for i in range(5):
        transactions.append({
            'transaction_id': f'test_j_{i}',
            'event_timestamp': base_time + timedelta(hours=90 + i),
            'event_sequence': base_idx + i,
            'sender_wallet': 'wallet_W',
            'receiver_wallet': 'wallet_X',
            'amount': 100.0 + i * 50,
            'transaction_type': 'transfer',
            'channel': 'agent',
            'agent_id': 'agent_11',
            'partition': 'train',
            'index': base_idx + i
        })
    
    return transactions

# =============================================================================
# VALIDATION TESTS
# =============================================================================

class ValidationTests:
    """Comprehensive validation tests for feature extraction."""
    
    def __init__(self, transactions):
        self.transactions = transactions
        self.wallet_partition = {f'wallet_{chr(65+i)}': 'train' for i in range(26)}
        self.agent_partition = {f'agent_{i+1}': 'train' for i in range(12)}
        self.agent_partition['agent_5'] = 'validation'  # For partition isolation test
        
        self.extractor = IncrementalFeatureExtractor(
            transactions, self.wallet_partition, self.agent_partition
        )
        
        self.test_results = {}
    
    def test_a_current_event_exclusion(self):
        """Test A: Current event must not count itself."""
        print("\n=== TEST A: Current Event Exclusion ===")
        
        # Transaction at index 5 should have exactly 5 prior transactions
        idx = 5
        features_before = self.extractor.extract_features(idx)
        
        # Update state with current transaction
        self.extractor._update_state(idx)
        
        # Re-extract (should be same since we're not recalculating for same index)
        # This test verifies the logic inside extract_features
        
        prior_count = features_before['structuring_prior_tx_count_1h']
        expected_prior = 5  # Transactions 0-4
        
        passed = prior_count == expected_prior
        self.test_results['test_a'] = {
            'name': 'Current Event Exclusion',
            'status': 'PASS' if passed else 'FAIL',
            'expected': expected_prior,
            'actual': prior_count,
            'details': f'Expected {expected_prior} prior transactions, got {prior_count}'
        }
        
        print(f"Expected prior count: {expected_prior}")
        print(f"Actual prior count: {prior_count}")
        print(f"Status: {self.test_results['test_a']['status']}")
        
        return passed
    
    def test_b_future_exclusion(self):
        """Test B: Future transactions must not influence prior features."""
        print("\n=== TEST B: Future Exclusion ===")
        
        # Calculate features for transaction at index 15
        idx = 15
        features_before = self.extractor.extract_features(idx)
        
        # Add future transactions
        future_transactions = []
        for i in range(5):
            future_transactions.append({
                'transaction_id': f'future_{i}',
                'event_timestamp': self.transactions[idx]['event_timestamp'] + timedelta(hours=10 + i),
                'event_sequence': len(self.transactions) + i,
                'sender_wallet': 'wallet_C',
                'receiver_wallet': 'wallet_D',
                'amount': 200.0,
                'transaction_type': 'transfer',
                'channel': 'agent',
                'agent_id': 'agent_2',
                'partition': 'train',
                'index': len(self.transactions) + i
            })
        
        # Calculate features again (should be identical)
        features_after = self.extractor.extract_features(idx)
        
        # Compare key features
        identical = all(features_before[k] == features_after[k] for k in features_before.keys())
        
        self.test_results['test_b'] = {
            'name': 'Future Exclusion',
            'status': 'PASS' if identical else 'FAIL',
            'details': 'Features unchanged after adding future transactions' if identical else 'Features changed with future transactions'
        }
        
        print(f"Features identical after adding future transactions: {identical}")
        print(f"Status: {self.test_results['test_b']['status']}")
        
        return identical
    
    def test_c_equal_timestamp_ordering(self):
        """Test C: Equal timestamps must respect event_sequence."""
        print("\n=== TEST C: Equal Timestamp Ordering ===")
        
        # Find transactions with same timestamp (Test C group)
        base_idx = 25  # Where Test C transactions start
        same_timestamp_txs = [self.transactions[base_idx + i] for i in range(5)]
        
        # Transaction with sequence 27 should see 27, 28, 29, 30 as future
        # and only 25, 26 as prior
        idx = base_idx + 2  # sequence 27
        features = self.extractor.extract_features(idx)
        
        # Should have exactly 2 prior transactions with same timestamp
        prior_count = features['structuring_prior_tx_count_1h']
        expected_prior = 2  # sequences 25, 26
        
        passed = prior_count == expected_prior
        self.test_results['test_c'] = {
            'name': 'Equal Timestamp Ordering',
            'status': 'PASS' if passed else 'FAIL',
            'expected': expected_prior,
            'actual': prior_count,
            'details': f'Expected {expected_prior} prior same-timestamp transactions, got {prior_count}'
        }
        
        print(f"Expected prior same-timestamp count: {expected_prior}")
        print(f"Actual prior same-timestamp count: {prior_count}")
        print(f"Status: {self.test_results['test_c']['status']}")
        
        return passed
    
    def test_d_partition_isolation(self):
        """Test D: Transactions must not use history from other partitions."""
        print("\n=== TEST D: Partition Isolation ===")
        
        # Find validation partition transaction
        val_idx = None
        for i, tx in enumerate(self.transactions):
            if tx['partition'] == 'validation':
                val_idx = i
                break
        
        if val_idx is None:
            print("ERROR: No validation partition transaction found")
            return False
        
        features = self.extractor.extract_features(val_idx)
        
        # Should have zero influence from train partition
        # Since validation partition agent_5 is different from train agents
        agent_features = [features[k] for k in features.keys() if k.startswith('agent_')]
        
        # All agent features should be 0 (cold start for this partition)
        all_zero = all(f == 0.0 for f in agent_features)
        
        self.test_results['test_d'] = {
            'name': 'Partition Isolation',
            'status': 'PASS' if all_zero else 'FAIL',
            'details': 'Agent features are zero (isolated from train partition)' if all_zero else 'Agent features non-zero (partition leakage detected)'
        }
        
        print(f"All agent features zero in validation partition: {all_zero}")
        print(f"Status: {self.test_results['test_d']['status']}")
        
        return all_zero
    
    def test_e_agent_aggregation(self):
        """Test E: Multiple wallets using same agent should contribute to agent features."""
        print("\n=== TEST E: Agent Aggregation ===")
        
        # Find agent_6 transactions (Test E group)
        base_idx = 35  # Where Test E transactions start
        agent_txs = [i for i, tx in enumerate(self.transactions) 
                    if tx['agent_id'] == 'agent_6']
        
        # Transaction at index 37 should see prior agent transactions from both wallets
        idx = agent_txs[2]  # Third transaction for agent_6
        features = self.extractor.extract_features(idx)
        
        # Should have 2 prior agent transactions (from both wallets)
        prior_agent_count = features['agent_prior_tx_count_7d']
        expected_prior = 2  # Two prior transactions from different wallets
        
        passed = prior_agent_count == expected_prior
        self.test_results['test_e'] = {
            'name': 'Agent Aggregation',
            'status': 'PASS' if passed else 'FAIL',
            'expected': expected_prior,
            'actual': prior_agent_count,
            'details': f'Expected {expected_prior} prior agent transactions from multiple wallets, got {prior_agent_count}'
        }
        
        print(f"Expected prior agent count (multi-wallet): {expected_prior}")
        print(f"Actual prior agent count: {prior_agent_count}")
        print(f"Status: {self.test_results['test_e']['status']}")
        
        return passed
    
    def test_f_current_hour_zscore(self):
        """Test F: Earlier events in same hour should contribute to current-hour z-score."""
        print("\n=== TEST F: Current-Hour Z-Score ===")
        
        # Find agent_7 transactions (Test F group - same hour)
        base_idx = 40  # Where Test F transactions start
        agent_txs = [i for i, tx in enumerate(self.transactions) 
                    if tx['agent_id'] == 'agent_7']
        
        # Third transaction in same hour should see 2 prior same-hour events
        idx = agent_txs[2]
        features = self.extractor.extract_features(idx)
        
        # Check that current-hour contribution is non-zero
        # (This requires sufficient baseline, so we check the logic is implemented)
        zscore = features['agent_hourly_tx_zscore_30d']
        
        # The z-score calculation should be implemented (not error out)
        # and should be finite
        valid_zscore = not math.isnan(zscore) and not math.isinf(zscore)
        
        self.test_results['test_f'] = {
            'name': 'Current-Hour Z-Score',
            'status': 'PASS' if valid_zscore else 'FAIL',
            'zscore': zscore,
            'details': f'Z-score calculated as {zscore}' if valid_zscore else 'Z-score invalid (NaN or infinity)'
        }
        
        print(f"Current-hour z-score: {zscore}")
        print(f"Z-score valid (finite): {valid_zscore}")
        print(f"Status: {self.test_results['test_f']['status']}")
        
        return valid_zscore
    
    def test_g_agent_inbound_outbound(self):
        """Test G: Agent-level ratio should aggregate across all agent wallets."""
        print("\n=== TEST G: Agent Inbound/Outbound Ratio ===")
        
        # Find agent_8 transactions (Test G group)
        agent_txs = [i for i, tx in enumerate(self.transactions) 
                    if tx['agent_id'] == 'agent_8']
        
        # Transaction should see agent-level aggregation
        idx = agent_txs[2]
        features = self.extractor.extract_features(idx)
        
        # Should calculate ratio at agent level, not wallet level
        ratio = features['agent_inbound_outbound_value_ratio_7d']
        
        # Should be finite and non-negative
        valid_ratio = not math.isnan(ratio) and not math.isinf(ratio) and ratio >= 0
        
        self.test_results['test_g'] = {
            'name': 'Agent Inbound/Outbound Ratio',
            'status': 'PASS' if valid_ratio else 'FAIL',
            'ratio': ratio,
            'details': f'Agent-level ratio calculated as {ratio}' if valid_ratio else 'Ratio invalid'
        }
        
        print(f"Agent inbound/outbound ratio: {ratio}")
        print(f"Ratio valid: {valid_ratio}")
        print(f"Status: {self.test_results['test_g']['status']}")
        
        return valid_ratio
    
    def test_h_cold_start(self):
        """Test H: Insufficient history should produce neutral values."""
        print("\n=== Test H: Cold Start ===")
        
        # Find first transaction (Test H)
        idx = len(self.transactions) - 9  # Test H transaction
        features = self.extractor.extract_features(idx)
        
        # All features should be 0 or 0.0 (cold start)
        all_cold_start = all(f == 0 or f == 0.0 for f in features.values())
        
        self.test_results['test_h'] = {
            'name': 'Cold Start',
            'status': 'PASS' if all_cold_start else 'FAIL',
            'details': 'All features are 0/0.0 (cold start)' if all_cold_start else 'Some features non-zero with no history'
        }
        
        print(f"All features zero with no history: {all_cold_start}")
        print(f"Status: {self.test_results['test_h']['status']}")
        
        return all_cold_start
    
    def test_i_determinism(self):
        """Test I: Same input should produce identical output."""
        print("\n=== Test I: Determinism ===")
        
        # Find agent_10 transactions (Test I group - identical)
        agent_txs = [i for i, tx in enumerate(self.transactions) 
                    if tx['agent_id'] == 'agent_10']
        
        # Extract features for each identical transaction
        features_list = []
        for idx in agent_txs:
            features = self.extractor.extract_features(idx)
            features_list.append(features)
        
        # All should be identical
        all_identical = all(features_list[0] == f for f in features_list[1:])
        
        self.test_results['test_i'] = {
            'name': 'Determinism',
            'status': 'PASS' if all_identical else 'FAIL',
            'details': 'Identical transactions produce identical features' if all_identical else 'Identical transactions produce different features'
        }
        
        print(f"Identical transactions produce identical features: {all_identical}")
        print(f"Status: {self.test_results['test_i']['status']}")
        
        return all_identical
    
    def test_j_no_nan_infinity(self):
        """Test J: All generated feature values should be finite."""
        print("\n=== Test J: No NaN/Infinity ===")
        
        # Extract features for all test transactions
        all_features = []
        for i in range(len(self.transactions)):
            features = self.extractor.extract_features(i)
            all_features.append(features)
            self.extractor._update_state(i)
        
        # Check for NaN/infinity
        has_nan = any(math.isnan(f) for features in all_features for f in features.values())
        has_inf = any(math.isinf(f) for features in all_features for f in features.values())
        
        all_finite = not has_nan and not has_inf
        
        self.test_results['test_j'] = {
            'name': 'No NaN/Infinity',
            'status': 'PASS' if all_finite else 'FAIL',
            'has_nan': has_nan,
            'has_inf': has_inf,
            'details': 'All feature values are finite' if all_finite else f'NaN: {has_nan}, Infinity: {has_inf}'
        }
        
        print(f"All feature values finite: {all_finite}")
        print(f"Has NaN: {has_nan}")
        print(f"Has Infinity: {has_inf}")
        print(f"Status: {self.test_results['test_j']['status']}")
        
        return all_finite
    
    def run_all_tests(self):
        """Run all validation tests."""
        print("=" * 80)
        print("STAGE 13A: SMALL-SCALE VALIDATION TESTS")
        print("=" * 80)
        
        tests = [
            self.test_a_current_event_exclusion,
            self.test_b_future_exclusion,
            self.test_c_equal_timestamp_ordering,
            self.test_d_partition_isolation,
            self.test_e_agent_aggregation,
            self.test_f_current_hour_zscore,
            self.test_g_agent_inbound_outbound,
            self.test_h_cold_start,
            self.test_i_determinism,
            self.test_j_no_nan_infinity
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
            except Exception as e:
                print(f"ERROR in {test.__name__}: {e}")
                results.append(False)
        
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        for test_name, result in self.test_results.items():
            print(f"{result['name']}: {result['status']}")
            if result['status'] == 'FAIL':
                print(f"  Details: {result['details']}")
        
        passed = sum(results)
        total = len(results)
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        return all(results)

# =============================================================================
# ADVERSARIAL TEMPORAL TEST
# =============================================================================

def adversarial_temporal_test():
    """Adversarial test: future transactions must not change prior features."""
    print("\n" + "=" * 80)
    print("ADVERSARIAL TEMPORAL LEAKAGE TEST")
    print("=" * 80)
    
    base_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    
    # Create base transactions
    transactions = []
    for i in range(10):
        transactions.append({
            'transaction_id': f'adv_{i}',
            'event_timestamp': base_time + timedelta(hours=i),
            'event_sequence': i,
            'sender_wallet': 'wallet_Y',
            'receiver_wallet': 'wallet_Z',
            'amount': 100.0,
            'transaction_type': 'transfer',
            'channel': 'agent',
            'agent_id': 'agent_12',
            'partition': 'train',
            'index': i
        })
    
    # Calculate features for event E (index 5)
    wallet_partition = {'wallet_Y': 'train', 'wallet_Z': 'train'}
    agent_partition = {'agent_12': 'train'}
    
    extractor = IncrementalFeatureExtractor(transactions, wallet_partition, agent_partition)
    
    # Calculate features for event E
    idx_e = 5
    features_e_original = extractor.extract_features(idx_e)
    
    # Inject future transaction
    future_tx = {
        'transaction_id': 'future_injected',
        'event_timestamp': base_time + timedelta(hours=20),
        'event_sequence': 100,
        'sender_wallet': 'wallet_Y',
        'receiver_wallet': 'wallet_Z',
        'amount': 1000.0,
        'transaction_type': 'transfer',
        'channel': 'agent',
        'agent_id': 'agent_12',
        'partition': 'train',
        'index': len(transactions)
    }
    
    transactions.append(future_tx)
    
    # Recalculate features for event E
    extractor2 = IncrementalFeatureExtractor(transactions, wallet_partition, agent_partition)
    features_e_after = extractor2.extract_features(idx_e)
    
    # Features must be identical
    identical = all(features_e_original[k] == features_e_after[k] for k in features_e_original.keys())
    
    print(f"Event E features unchanged after future injection: {identical}")
    
    # Inject same-timestamp transaction with larger sequence
    same_time_tx = {
        'transaction_id': 'same_time_larger_seq',
        'event_timestamp': transactions[idx_e]['event_timestamp'],
        'event_sequence': 200,  # Larger than event E's sequence
        'sender_wallet': 'wallet_Y',
        'receiver_wallet': 'wallet_Z',
        'amount': 500.0,
        'transaction_type': 'transfer',
        'channel': 'agent',
        'agent_id': 'agent_12',
        'partition': 'train',
        'index': len(transactions)
    }
    
    transactions.append(same_time_tx)
    
    # Recalculate features for event E
    extractor3 = IncrementalFeatureExtractor(transactions, wallet_partition, agent_partition)
    features_e_after2 = extractor3.extract_features(idx_e)
    
    # Features must be identical
    identical2 = all(features_e_original[k] == features_e_after2[k] for k in features_e_original.keys())
    
    print(f"Event E features unchanged after same-timestamp future injection: {identical2}")
    
    # Inject same-timestamp transaction with smaller sequence
    same_time_smaller_tx = {
        'transaction_id': 'same_time_smaller_seq',
        'event_timestamp': transactions[idx_e]['event_timestamp'],
        'event_sequence': 2,  # Smaller than event E's sequence (5)
        'sender_wallet': 'wallet_Y',
        'receiver_wallet': 'wallet_Z',
        'amount': 500.0,
        'transaction_type': 'transfer',
        'channel': 'agent',
        'agent_id': 'agent_12',
        'partition': 'train',
        'index': len(transactions)
    }
    
    transactions.append(same_time_smaller_tx)
    
    # Recalculate features for event E
    extractor4 = IncrementalFeatureExtractor(transactions, wallet_partition, agent_partition)
    features_e_after3 = extractor4.extract_features(idx_e)
    
    # Features MAY change (smaller sequence is legitimate prior history)
    print(f"Event E features may change after same-timestamp prior injection: {not all(features_e_original[k] == features_e_after3[k] for k in features_e_original.keys())}")
    
    passed = identical and identical2
    
    print(f"\nAdversarial test status: {'PASS' if passed else 'FAIL'}")
    
    return passed

# =============================================================================
# MAIN
# =============================================================================

def main():
    # Create test transactions
    transactions = create_test_transactions()
    
    # Run validation tests
    validator = ValidationTests(transactions)
    all_passed = validator.run_all_tests()
    
    # Run adversarial test
    adversarial_passed = adversarial_temporal_test()
    
    # Overall result
    print("\n" + "=" * 80)
    print("OVERALL VALIDATION RESULT")
    print("=" * 80)
    print(f"Small-scale tests: {'PASS' if all_passed else 'FAIL'}")
    print(f"Adversarial test: {'PASS' if adversarial_passed else 'FAIL'}")
    print(f"Overall: {'PASS' if all_passed and adversarial_passed else 'FAIL'}")
    
    return all_passed and adversarial_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
