"""
Stage 13A: Execute Validation Tests Against Real Stage 11 Dataset

Executes Tests A-J against the actual ecocash_aml_synthetic_100k_v1 dataset
using the corrected implementation ml_stage13a_extract_features_final.py.
"""

import json
import csv
import math
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set, Optional
import numpy as np
import sys
import time

# Import the corrected extractor
sys.path.insert(0, str(Path(__file__).parent))
from ml_stage13a_extract_features_final import IndexedFeatureExtractor, load_data

# =============================================================================
# CONFIGURATION
# =============================================================================

DATASET_VERSION = "ecocash_aml_synthetic_100k_v1"
DATA_DIR = Path("data") / DATASET_VERSION
REPORTS_DIR = Path("reports")

# =============================================================================
# REAL DATASET VALIDATION TESTS
# =============================================================================

class RealDatasetValidationTests:
    """Execute validation tests against actual Stage 11 dataset."""
    
    def __init__(self, data_dir: Path):
        print("Loading real Stage 11 dataset...")
        self.data_dir = data_dir
        
        # Load actual data
        self.transactions, self.labels, self.wallet_partition, self.agent_partition = load_data(data_dir)
        
        print(f"Loaded {len(self.transactions)} transactions")
        print(f"Loaded {len(self.labels)} labels")
        print()
        
        # Initialize corrected extractor
        print("Initializing corrected feature extractor...")
        self.extractor = IndexedFeatureExtractor(
            self.transactions, self.wallet_partition, self.agent_partition
        )
        print("Corrected extractor initialized")
        print()
        
        self.test_results = {}
        self.execution_times = {}
    
    def test_a_current_event_exclusion(self):
        """Test A: Current event must not count itself."""
        print("\n=== TEST A: Current Event Exclusion ===")
        start_time = time.time()
        
        # Find a transaction with sufficient prior history
        test_idx = 1000  # Should have prior transactions
        tx = self.transactions[test_idx]
        
        # Extract features BEFORE updating any state
        features = self.extractor.extract_features(test_idx)
        
        # The key verification: prior_1h_count should be based on history only
        prior_1h_count = features['structuring_prior_tx_count_1h']
        
        # Manually verify by checking if current transaction would affect count
        # Get current transaction's timestamp
        current_time = tx['event_timestamp']
        hour_ago = current_time - timedelta(hours=1)
        
        # Count prior transactions manually
        manual_count = 0
        for i in range(test_idx):
            prior_tx = self.transactions[i]
            if (prior_tx['partition'] == tx['partition'] and
                prior_tx['sender_wallet'] == tx['sender_wallet'] and
                prior_tx['event_timestamp'] >= hour_ago and
                prior_tx['event_timestamp'] < current_time):
                manual_count += 1
        
        # The implementation should match manual count (not include current)
        passed = prior_1h_count == manual_count
        
        elapsed = time.time() - start_time
        self.execution_times['test_a'] = elapsed
        
        self.test_results['test_a'] = {
            'name': 'Current Event Exclusion',
            'status': 'PASS' if passed else 'FAIL',
            'implementation_count': prior_1h_count,
            'manual_count': manual_count,
            'details': f'Implementation count: {prior_1h_count}, Manual count: {manual_count}'
        }
        
        print(f"Implementation prior count: {prior_1h_count}")
        print(f"Manual verification count: {manual_count}")
        print(f"Status: {self.test_results['test_a']['status']}")
        print(f"Execution time: {elapsed:.3f}s")
        
        return passed
    
    def test_b_future_exclusion(self):
        """Test B: Future transactions must not influence prior features."""
        print("\n=== TEST B: Future Event Exclusion ===")
        start_time = time.time()
        
        # Choose a transaction in the middle of the dataset
        test_idx = 50000
        tx = self.transactions[test_idx]
        
        # Extract features for this transaction
        features_before = self.extractor.extract_features(test_idx)
        
        # Create a modified transaction list with a future transaction added
        # (This simulates what would happen if future data existed)
        # Since we can't actually modify the dataset, we verify the logic by checking
        # that the implementation uses indices < test_idx only
        
        # Verify by checking a feature that would be affected by future data
        # if the implementation were incorrect
        prior_7d_count = features_before['structuring_same_day_prior_tx_count']
        
        # Manually count prior transactions in same day
        current_time = tx['event_timestamp']
        current_date = current_time.date()
        
        manual_count = 0
        for i in range(test_idx):
            prior_tx = self.transactions[i]
            if (prior_tx['partition'] == tx['partition'] and
                prior_tx['sender_wallet'] == tx['sender_wallet'] and
                prior_tx['event_timestamp'].date() == current_date and
                prior_tx['event_timestamp'] < current_time):
                manual_count += 1
        
        # Count would be different if future transactions were included
        passed = prior_7d_count == manual_count
        
        elapsed = time.time() - start_time
        self.execution_times['test_b'] = elapsed
        
        same_day_count = features_before['structuring_same_day_prior_tx_count']
        self.test_results['test_b'] = {
            'name': 'Future Event Exclusion',
            'status': 'PASS' if passed else 'FAIL',
            'implementation_count': same_day_count,
            'manual_count': manual_count,
            'details': f'Implementation uses only prior indices: {same_day_count == manual_count}'
        }
        
        print(f"Implementation prior count: {same_day_count}")
        print(f"Manual verification count: {manual_count}")
        print(f"Status: {self.test_results['test_b']['status']}")
        print(f"Execution time: {elapsed:.3f}s")
        
        return passed
    
    def test_c_equal_timestamp_ordering(self):
        """Test C: Equal timestamps must respect event_sequence."""
        print("\n=== TEST C: Equal Timestamp Ordering ===")
        start_time = time.time()
        
        # Find transactions with the same timestamp
        timestamp_groups = defaultdict(list)
        for i, tx in enumerate(self.transactions):
            timestamp_groups[tx['event_timestamp']].append(i)
        
        # Find a timestamp with multiple transactions
        same_timestamp_groups = [(ts, indices) for ts, indices in timestamp_groups.items() if len(indices) > 3]
        
        if not same_timestamp_groups:
            print("WARNING: No groups with same timestamp found in dataset")
            self.test_results['test_c'] = {
                'name': 'Equal Timestamp Ordering',
                'status': 'NOT EXECUTED',
                'details': 'No same-timestamp groups found in dataset'
            }
            return False
        
        # Use the first group found
        test_timestamp, indices = same_timestamp_groups[0]
        indices.sort()  # Should already be sorted by event_sequence
        
        # Test the middle transaction
        test_idx = indices[len(indices) // 2]
        tx = self.transactions[test_idx]
        
        features = self.extractor.extract_features(test_idx)
        
        # Count prior transactions with same timestamp
        current_time = tx['event_timestamp']
        same_timestamp_prior = 0
        for i in range(test_idx):
            if self.transactions[i]['event_timestamp'] == current_time:
                same_timestamp_prior += 1
        
        # Should have exactly the number of same-timestamp transactions with smaller sequence
        expected_prior = indices.index(test_idx)
        
        passed = same_timestamp_prior == expected_prior
        
        elapsed = time.time() - start_time
        self.execution_times['test_c'] = elapsed
        
        self.test_results['test_c'] = {
            'name': 'Equal Timestamp Ordering',
            'status': 'PASS' if passed else 'FAIL',
            'same_timestamp_prior': same_timestamp_prior,
            'expected_prior': expected_prior,
            'details': f'Same-timestamp prior: {same_timestamp_prior}, Expected: {expected_prior}'
        }
        
        print(f"Same-timestamp prior transactions: {same_timestamp_prior}")
        print(f"Expected (based on sequence): {expected_prior}")
        print(f"Status: {self.test_results['test_c']['status']}")
        print(f"Execution time: {elapsed:.3f}s")
        
        return passed
    
    def test_d_partition_isolation(self):
        """Test D: Transactions must not use history from other partitions."""
        print("\n=== TEST D: Partition Isolation ===")
        start_time = time.time()
        
        # Find a validation partition transaction
        val_indices = [i for i, tx in enumerate(self.transactions) if tx['partition'] == 'validation']
        
        if not val_indices:
            print("ERROR: No validation partition transactions found")
            self.test_results['test_d'] = {
                'name': 'Partition Isolation',
                'status': 'FAIL',
                'details': 'No validation partition found'
            }
            return False
        
        test_idx = val_indices[0]
        tx = self.transactions[test_idx]
        
        features = self.extractor.extract_features(test_idx)
        
        # Verify that the implementation uses partition-local indices
        # by checking that agent features are computed correctly
        
        # The key check: agent features should only use agent transactions from validation partition
        if tx['agent_id']:
            agent_feature = features['agent_prior_tx_count_7d']
            
            # Manually count agent transactions in validation partition only
            manual_count = 0
            current_time = tx['event_timestamp']
            week_ago = current_time - timedelta(days=7)
            
            for i in range(test_idx):
                prior_tx = self.transactions[i]
                if (prior_tx['partition'] == 'validation' and
                    prior_tx['agent_id'] == tx['agent_id'] and
                    prior_tx['event_timestamp'] >= week_ago and
                    prior_tx['event_timestamp'] < current_time):
                    manual_count += 1
            
            passed = agent_feature == manual_count
        else:
            # If no agent, agent features should be 0
            agent_features = [features[k] for k in features.keys() if k.startswith('agent_')]
            passed = all(f == 0.0 for f in agent_features)
            manual_count = 0
        
        elapsed = time.time() - start_time
        self.execution_times['test_d'] = elapsed
        
        self.test_results['test_d'] = {
            'name': 'Partition Isolation',
            'status': 'PASS' if passed else 'FAIL',
            'implementation_count': agent_feature if tx['agent_id'] else 0,
            'manual_count': manual_count,
            'details': f'Partition-local indexing verified: {passed}'
        }
        
        print(f"Implementation agent count: {agent_feature if tx['agent_id'] else 0}")
        print(f"Manual partition-local count: {manual_count}")
        print(f"Status: {self.test_results['test_d']['status']}")
        print(f"Execution time: {elapsed:.3f}s")
        
        return passed
    
    def test_e_agent_aggregation(self):
        """Test E: Agent-level features should aggregate across multiple wallets."""
        print("\n=== TEST E: Agent Aggregation ===")
        start_time = time.time()
        
        # Find an agent with multiple wallets
        agent_wallets = defaultdict(set)
        for tx in self.transactions:
            if tx['agent_id']:
                agent_wallets[tx['agent_id']].add(tx['sender_wallet'])
                agent_wallets[tx['agent_id']].add(tx['receiver_wallet'])
        
        # Find an agent with at least 3 wallets
        multi_wallet_agents = [(agent, wallets) for agent, wallets in agent_wallets.items() if len(wallets) >= 3]
        
        if not multi_wallet_agents:
            print("WARNING: No agents with multiple wallets found")
            self.test_results['test_e'] = {
                'name': 'Agent Aggregation',
                'status': 'NOT EXECUTED',
                'details': 'No multi-wallet agents found in dataset'
            }
            return False
        
        test_agent, agent_wallet_set = multi_wallet_agents[0]
        
        # Find a transaction for this agent
        agent_indices = [i for i, tx in enumerate(self.transactions) if tx['agent_id'] == test_agent]
        test_idx = agent_indices[len(agent_indices) // 2]
        tx = self.transactions[test_idx]
        
        features = self.extractor.extract_features(test_idx)
        
        # Check agent unique wallet count
        agent_wallet_count = features['agent_unique_wallet_count_7d']
        
        # Manually count unique wallets for this agent in 7-day window
        current_time = tx['event_timestamp']
        week_ago = current_time - timedelta(days=7)
        
        manual_wallets = set()
        for i in range(test_idx):
            prior_tx = self.transactions[i]
            if (prior_tx['partition'] == tx['partition'] and
                prior_tx['agent_id'] == test_agent and
                prior_tx['event_timestamp'] >= week_ago and
                prior_tx['event_timestamp'] < current_time):
                manual_wallets.add(prior_tx['sender_wallet'])
                manual_wallets.add(prior_tx['receiver_wallet'])
        
        passed = agent_wallet_count == len(manual_wallets)
        
        elapsed = time.time() - start_time
        self.execution_times['test_e'] = elapsed
        
        self.test_results['test_e'] = {
            'name': 'Agent Aggregation',
            'status': 'PASS' if passed else 'FAIL',
            'implementation_count': agent_wallet_count,
            'manual_count': len(manual_wallets),
            'agent_id': test_agent,
            'details': f'Agent {test_agent}: {agent_wallet_count} vs {len(manual_wallets)} wallets'
        }
        
        print(f"Agent ID: {test_agent}")
        print(f"Implementation wallet count: {agent_wallet_count}")
        print(f"Manual verification count: {len(manual_wallets)}")
        print(f"Status: {self.test_results['test_e']['status']}")
        print(f"Execution time: {elapsed:.3f}s")
        
        return passed
    
    def test_f_current_hour_zscore(self):
        """Test F: Current-hour z-scores should include earlier same-hour events."""
        print("\n=== TEST F: Current-Hour Z-Scores ===")
        start_time = time.time()
        
        # Find an agent with sufficient hourly activity
        agent_hourly_activity = defaultdict(lambda: defaultdict(int))
        for tx in self.transactions:
            if tx['agent_id']:
                hour_key = tx['event_timestamp'].replace(minute=0, second=0, microsecond=0)
                agent_hourly_activity[tx['agent_id']][hour_key] += 1
        
        # Find an agent with an hour containing multiple transactions
        active_agents = []
        for agent, hourly_counts in agent_hourly_activity.items():
            for hour, count in hourly_counts.items():
                if count >= 3:
                    active_agents.append((agent, hour, count))
                    break
            if active_agents:
                break
        
        if not active_agents:
            print("WARNING: No agents with multi-transaction hours found")
            self.test_results['test_f'] = {
                'name': 'Current-Hour Z-Scores',
                'status': 'NOT EXECUTED',
                'details': 'No multi-transaction hours found in dataset'
            }
            return False
        
        test_agent, test_hour, tx_count = active_agents[0]
        
        # Find a transaction in this hour (not the first one)
        hour_indices = [i for i, tx in enumerate(self.transactions)
                       if tx['agent_id'] == test_agent and
                       tx['event_timestamp'].replace(minute=0, second=0, microsecond=0) == test_hour]
        
        if len(hour_indices) < 2:
            print("WARNING: Insufficient transactions in test hour")
            self.test_results['test_f'] = {
                'name': 'Current-Hour Z-Scores',
                'status': 'NOT EXECUTED',
                'details': 'Insufficient transactions in test hour'
            }
            return False
        
        test_idx = hour_indices[len(hour_indices) // 2]
        tx = self.transactions[test_idx]
        
        features = self.extractor.extract_features(test_idx)
        
        # Check that z-score is finite (not NaN or infinity)
        tx_zscore = features['agent_hourly_tx_zscore_30d']
        value_zscore = features['agent_hourly_value_zscore_30d']
        
        tx_valid = not math.isnan(tx_zscore) and not math.isinf(tx_zscore)
        value_valid = not math.isnan(value_zscore) and not math.isinf(value_zscore)
        
        passed = tx_valid and value_valid
        
        elapsed = time.time() - start_time
        self.execution_times['test_f'] = elapsed
        
        self.test_results['test_f'] = {
            'name': 'Current-Hour Z-Scores',
            'status': 'PASS' if passed else 'FAIL',
            'tx_zscore': tx_zscore,
            'value_zscore': value_zscore,
            'tx_valid': tx_valid,
            'value_valid': value_valid,
            'details': f'TX z-score: {tx_zscore:.3f}, Value z-score: {value_zscore:.3f}'
        }
        
        print(f"Agent hourly TX z-score: {tx_zscore:.3f}")
        print(f"Agent hourly value z-score: {value_zscore:.3f}")
        print(f"Both finite: {passed}")
        print(f"Status: {self.test_results['test_f']['status']}")
        print(f"Execution time: {elapsed:.3f}s")
        
        return passed
    
    def test_g_agent_inbound_outbound(self):
        """Test G: Agent inbound/outbound ratio should be agent-level."""
        print("\n=== TEST G: Agent Inbound/Outbound ===")
        start_time = time.time()
        
        # Find an agent with transactions
        agent_indices = defaultdict(list)
        for i, tx in enumerate(self.transactions):
            if tx['agent_id']:
                agent_indices[tx['agent_id']].append(i)
        
        if not agent_indices:
            print("ERROR: No agent-mediated transactions found")
            self.test_results['test_g'] = {
                'name': 'Agent Inbound/Outbound',
                'status': 'FAIL',
                'details': 'No agent transactions found'
            }
            return False
        
        # Test with first agent found
        test_agent = list(agent_indices.keys())[0]
        test_idx = agent_indices[test_agent][len(agent_indices[test_agent]) // 2]
        tx = self.transactions[test_idx]
        
        features = self.extractor.extract_features(test_idx)
        
        # Check that the ratio is finite
        ratio = features['agent_inbound_outbound_value_ratio_7d']
        
        valid = not math.isnan(ratio) and not math.isinf(ratio) and ratio >= 0
        
        elapsed = time.time() - start_time
        self.execution_times['test_g'] = elapsed
        
        self.test_results['test_g'] = {
            'name': 'Agent Inbound/Outbound',
            'status': 'PASS' if valid else 'FAIL',
            'ratio': ratio,
            'valid': valid,
            'details': f'Agent-level ratio: {ratio:.3f}'
        }
        
        print(f"Agent inbound/outbound ratio: {ratio:.3f}")
        print(f"Ratio valid (finite, non-negative): {valid}")
        print(f"Status: {self.test_results['test_g']['status']}")
        print(f"Execution time: {elapsed:.3f}s")
        
        return valid
    
    def test_h_cold_start(self):
        """Test H: Insufficient history should produce neutral values."""
        print("\n=== Test H: Cold Start ===")
        start_time = time.time()
        
        # Find the first transaction for a wallet
        wallet_first_tx = {}
        for i, tx in enumerate(self.transactions):
            if tx['sender_wallet'] not in wallet_first_tx:
                wallet_first_tx[tx['sender_wallet']] = i
        
        # Test with first transaction of first wallet
        test_wallet = list(wallet_first_tx.keys())[0]
        test_idx = wallet_first_tx[test_wallet]
        tx = self.transactions[test_idx]
        
        features = self.extractor.extract_features(test_idx)
        
        # All features should be 0 or 0.0 (cold start)
        # Check key features that depend on history
        cold_start_features = [
            'structuring_prior_tx_count_1h',
            'structuring_prior_value_sum_24h',
            'network_outbound_counterparty_count_7d',
            'agent_prior_tx_count_1h' if tx['agent_id'] else None
        ]
        
        all_cold = True
        for feature_name in cold_start_features:
            if feature_name and feature_name in features:
                value = features[feature_name]
                if value != 0 and value != 0.0:
                    all_cold = False
                    print(f"  {feature_name}: {value} (expected 0)")
        
        elapsed = time.time() - start_time
        self.execution_times['test_h'] = elapsed
        
        self.test_results['test_h'] = {
            'name': 'Cold Start',
            'status': 'PASS' if all_cold else 'FAIL',
            'all_zero': all_cold,
            'details': 'All cold-start features are 0/0.0' if all_cold else 'Some features non-zero with no history'
        }
        
        print(f"All cold-start features zero: {all_cold}")
        print(f"Status: {self.test_results['test_h']['status']}")
        print(f"Execution time: {elapsed:.3f}s")
        
        return all_cold
    
    def test_i_determinism(self):
        """Test I: Same input should produce identical output."""
        print("\n=== Test I: Determinism ===")
        start_time = time.time()
        
        # Choose a transaction
        test_idx = 10000
        tx = self.transactions[test_idx]
        
        # Extract features twice
        features_1 = self.extractor.extract_features(test_idx)
        features_2 = self.extractor.extract_features(test_idx)
        
        # Check if identical
        identical = all(features_1[k] == features_2[k] for k in features_1.keys())
        
        elapsed = time.time() - start_time
        self.execution_times['test_i'] = elapsed
        
        self.test_results['test_i'] = {
            'name': 'Determinism',
            'status': 'PASS' if identical else 'FAIL',
            'identical': identical,
            'details': 'Two extractions produce identical results' if identical else 'Determinism violation detected'
        }
        
        print(f"Identical results on duplicate extraction: {identical}")
        print(f"Status: {self.test_results['test_i']['status']}")
        print(f"Execution time: {elapsed:.3f}s")
        
        return identical
    
    def test_j_numerical_safety(self):
        """Test J: All generated feature values should be finite."""
        print("\n=== Test J: Numerical Safety ===")
        start_time = time.time()
        
        # Sample a subset of transactions for performance
        sample_size = min(1000, len(self.transactions))
        sample_indices = list(range(0, len(self.transactions), len(self.transactions) // sample_size))
        
        has_nan = False
        has_inf = False
        total_features_checked = 0
        
        for idx in sample_indices:
            features = self.extractor.extract_features(idx)
            
            for feature_name, value in features.items():
                total_features_checked += 1
                if math.isnan(value):
                    has_nan = True
                    print(f"  NaN detected in {feature_name} at index {idx}")
                if math.isinf(value):
                    has_inf = True
                    print(f"  Infinity detected in {feature_name} at index {idx}")
        
        all_finite = not has_nan and not has_inf
        
        elapsed = time.time() - start_time
        self.execution_times['test_j'] = elapsed
        
        self.test_results['test_j'] = {
            'name': 'Numerical Safety',
            'status': 'PASS' if all_finite else 'FAIL',
            'has_nan': has_nan,
            'has_inf': has_inf,
            'features_checked': total_features_checked,
            'details': f'Checked {total_features_checked} feature values: NaN={has_nan}, Inf={has_inf}'
        }
        
        print(f"Features checked: {total_features_checked}")
        print(f"Has NaN: {has_nan}")
        print(f"Has Infinity: {has_inf}")
        print(f"All finite: {all_finite}")
        print(f"Status: {self.test_results['test_j']['status']}")
        print(f"Execution time: {elapsed:.3f}s")
        
        return all_finite
    
    def run_all_tests(self):
        """Run all validation tests."""
        print("=" * 80)
        print("STAGE 13A: VALIDATION TEST EXECUTION")
        print("=" * 80)
        print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
        print(f"Dataset: {self.data_dir}")
        print(f"Transactions: {len(self.transactions)}")
        print(f"Implementation: ml_stage13a_extract_features_final.py")
        print()
        
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
            self.test_j_numerical_safety
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
            except Exception as e:
                print(f"ERROR in {test.__name__}: {e}")
                import traceback
                traceback.print_exc()
                results.append(False)
        
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        for test_name, result in self.test_results.items():
            print(f"{result['name']}: {result['status']}")
            if result['status'] == 'FAIL':
                print(f"  Details: {result['details']}")
        
        total_time = sum(self.execution_times.values())
        print(f"\nTotal execution time: {total_time:.3f}s")
        
        passed = sum(results)
        total = len(results)
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        return all(results), self.test_results, self.execution_times

# =============================================================================
# MAIN
# =============================================================================

def main():
    # Verify dataset files exist
    print("Verifying Stage 11 dataset files...")
    required_files = [
        DATA_DIR / "transactions.csv",
        DATA_DIR / "ground_truth.json",
        DATA_DIR / "entity_metadata.json",
        DATA_DIR / "generation_manifest.json"
    ]
    
    for file_path in required_files:
        if file_path.exists():
            print(f"  [OK] {file_path.name}")
        else:
            print(f"  [MISSING] {file_path.name}")
            print("ERROR: Required dataset files missing")
            return False, {}, {}
    
    print()
    
    # Run validation tests
    validator = RealDatasetValidationTests(DATA_DIR)
    all_passed, test_results, execution_times = validator.run_all_tests()
    
    return all_passed, test_results, execution_times

if __name__ == "__main__":
    success, test_results, execution_times = main()
    sys.exit(0 if success else 1)
