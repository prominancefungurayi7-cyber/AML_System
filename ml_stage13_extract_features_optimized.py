"""
Stage 13: Optimized 30-Feature Matrix Construction

Optimized version with proper indexing to avoid O(n²) complexity.
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

# =============================================================================
# CONFIGURATION
# =============================================================================

DATASET_VERSION = "ecocash_aml_synthetic_100k_v1"
DATA_DIR = Path("data") / DATASET_VERSION
FEATURE_DIR = DATA_DIR / "features"
REPORTS_DIR = Path("reports")

SYNTHETIC_REPORTING_THRESHOLD = 10000

# =============================================================================
# LOAD DATA
# =============================================================================

def load_data():
    """Load Stage 11 dataset files."""
    print("Loading Stage 11 dataset...")
    
    transactions = []
    with open(DATA_DIR / "transactions.csv", 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            transactions.append({
                'transaction_id': row['transaction_id'],
                'event_timestamp': datetime.fromisoformat(row['event_timestamp']),
                'event_sequence': int(row['event_sequence']),
                'sender_wallet': row['sender_wallet'],
                'receiver_wallet': row['receiver_wallet'],
                'amount': float(row['amount']),
                'transaction_type': row['transaction_type'],
                'channel': row['channel'],
                'agent_id': row['agent_id'] if row['agent_id'] else None,
                'partition': row['partition']
            })
    
    # Sort by (timestamp, sequence) for proper ordering
    transactions.sort(key=lambda tx: (tx['event_timestamp'], tx['event_sequence']))
    
    # Assign sequential indices after sorting
    for i, tx in enumerate(transactions):
        tx['index'] = i
    
    with open(DATA_DIR / "ground_truth.json", 'r') as f:
        ground_truth = json.load(f)
    
    labels = {gt['transaction_id']: gt['ground_truth_label'] for gt in ground_truth}
    
    with open(DATA_DIR / "entity_metadata.json", 'r') as f:
        entity_metadata = json.load(f)
    
    wallet_partition = {w['wallet_id']: w['partition'] for w in entity_metadata['wallets']}
    agent_partition = {a['agent_id']: a['partition'] for a in entity_metadata['agents']}
    
    print(f"  Loaded {len(transactions)} transactions")
    print(f"  Loaded {len(labels)} labels")
    print()
    
    return transactions, labels, wallet_partition, agent_partition

# =============================================================================
# OPTIMIZED FEATURE EXTRACTOR
# =============================================================================

class OptimizedFeatureExtractor:
    """Optimized feature extraction with pre-built indices."""
    
    def __init__(self, transactions, wallet_partition, agent_partition):
        self.transactions = transactions
        self.wallet_partition = wallet_partition
        self.agent_partition = agent_partition
        self.n = len(transactions)
        
        # Pre-build partition indices
        self.partition_indices = {
            'train': [],
            'validation': [],
            'final_test': [],
            'independent': []
        }
        for i, tx in enumerate(transactions):
            self.partition_indices[tx['partition']].append(i)
        
        # Pre-build wallet indices
        self.wallet_outbound_by_partition = defaultdict(lambda: defaultdict(list))
        self.wallet_inbound_by_partition = defaultdict(lambda: defaultdict(list))
        for i, tx in enumerate(transactions):
            part = tx['partition']
            self.wallet_outbound_by_partition[part][tx['sender_wallet']].append(i)
            self.wallet_inbound_by_partition[part][tx['receiver_wallet']].append(i)
        
        # Pre-build agent indices
        self.agent_by_partition = defaultdict(lambda: defaultdict(list))
        for i, tx in enumerate(transactions):
            if tx['agent_id']:
                part = tx['partition']
                self.agent_by_partition[part][tx['agent_id']].append(i)
    
    def get_prior_indices(self, current_idx: int, partition: str, max_hours: float = None) -> List[int]:
        """Get indices of prior transactions in same partition."""
        prior = []
        for i in range(current_idx):
            tx = self.transactions[i]
            if tx['partition'] != partition:
                continue
            
            if max_hours:
                time_diff = (self.transactions[current_idx]['event_timestamp'] - tx['event_timestamp']).total_seconds() / 3600
                if time_diff > max_hours:
                    continue
            
            prior.append(i)
        return prior
    
    # ========================================
    # STRUCTURING FEATURES
    # ========================================
    
    def structuring_prior_tx_count_1h(self, idx: int) -> float:
        tx = self.transactions[idx]
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=1)
        sender_prior = [i for i in prior if self.transactions[i]['sender_wallet'] == tx['sender_wallet']]
        return len(sender_prior)
    
    def structuring_prior_value_sum_24h(self, idx: int) -> float:
        tx = self.transactions[idx]
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=24)
        sender_prior = [i for i in prior if self.transactions[i]['sender_wallet'] == tx['sender_wallet']]
        return sum(self.transactions[i]['amount'] for i in sender_prior)
    
    def structuring_same_day_prior_tx_count(self, idx: int) -> float:
        tx = self.transactions[idx]
        current_date = tx['event_timestamp'].date()
        prior = self.get_prior_indices(idx, tx['partition'])
        sender_prior = [i for i in prior 
                      if self.transactions[i]['sender_wallet'] == tx['sender_wallet']
                      and self.transactions[i]['event_timestamp'].date() == current_date]
        return len(sender_prior)
    
    def structuring_repeated_amount_ratio_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=24*7)
        sender_prior = [i for i in prior if self.transactions[i]['sender_wallet'] == tx['sender_wallet']]
        
        if not sender_prior:
            return 0.0
        
        current_amount = tx['amount']
        threshold = 0.05 * max(current_amount, 1)
        
        matching = sum(1 for i in sender_prior 
                     if abs(self.transactions[i]['amount'] - current_amount) <= threshold)
        
        return matching / len(sender_prior)
    
    def structuring_amount_cluster_dispersion_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=24*7)
        sender_prior = [i for i in prior if self.transactions[i]['sender_wallet'] == tx['sender_wallet']]
        
        if len(sender_prior) < 2:
            return 0.0
        
        amounts = [self.transactions[i]['amount'] for i in sender_prior]
        mean_amt = sum(amounts) / len(amounts)
        
        if mean_amt == 0:
            return 0.0
        
        variance = sum((a - mean_amt) ** 2 for a in amounts) / len(amounts)
        std = math.sqrt(variance)
        
        return std / mean_amt
    
    def structuring_near_threshold_history_ratio_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=24*7)
        sender_prior = [i for i in prior if self.transactions[i]['sender_wallet'] == tx['sender_wallet']]
        
        if not sender_prior:
            return 0.0
        
        threshold_lower = 0.90 * SYNTHETIC_REPORTING_THRESHOLD
        threshold_upper = SYNTHETIC_REPORTING_THRESHOLD
        
        near_threshold = sum(1 for i in sender_prior 
                          if threshold_lower <= self.transactions[i]['amount'] < threshold_upper)
        
        return near_threshold / len(sender_prior)
    
    # ========================================
    # NETWORK FEATURES
    # ========================================
    
    def network_outbound_counterparty_count_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=24*7)
        sender_prior = [i for i in prior if self.transactions[i]['sender_wallet'] == tx['sender_wallet']]
        receivers = set(self.transactions[i]['receiver_wallet'] for i in sender_prior)
        return len(receivers)
    
    def network_inbound_counterparty_count_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=24*7)
        receiver_prior = [i for i in prior if self.transactions[i]['receiver_wallet'] == tx['receiver_wallet']]
        senders = set(self.transactions[i]['sender_wallet'] for i in receiver_prior)
        return len(senders)
    
    def network_outbound_counterparty_entropy_30d(self, idx: int) -> float:
        tx = self.transactions[idx]
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=24*30)
        sender_prior = [i for i in prior if self.transactions[i]['sender_wallet'] == tx['sender_wallet']]
        
        if not sender_prior:
            return 0.0
        
        receiver_values = defaultdict(float)
        total_value = 0.0
        for i in sender_prior:
            receiver_values[self.transactions[i]['receiver_wallet']] += self.transactions[i]['amount']
            total_value += self.transactions[i]['amount']
        
        if total_value == 0:
            return 0.0
        
        entropy = 0.0
        for value in receiver_values.values():
            p = value / total_value
            if p > 0:
                entropy -= p * math.log(p)
        
        return entropy
    
    def network_top_counterparty_value_share_30d(self, idx: int) -> float:
        tx = self.transactions[idx]
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=24*30)
        sender_prior = [i for i in prior if self.transactions[i]['sender_wallet'] == tx['sender_wallet']]
        
        if not sender_prior:
            return 0.0
        
        receiver_values = defaultdict(float)
        total_value = 0.0
        for i in sender_prior:
            receiver_values[self.transactions[i]['receiver_wallet']] += self.transactions[i]['amount']
            total_value += self.transactions[i]['amount']
        
        if total_value == 0:
            return 0.0
        
        max_value = max(receiver_values.values())
        return max_value / total_value
    
    def network_current_receiver_is_new(self, idx: int) -> float:
        tx = self.transactions[idx]
        prior = self.get_prior_indices(idx, tx['partition'])
        sender_prior = [i for i in prior if self.transactions[i]['sender_wallet'] == tx['sender_wallet']]
        prior_receivers = set(self.transactions[i]['receiver_wallet'] for i in sender_prior)
        
        return 1.0 if tx['receiver_wallet'] not in prior_receivers else 0.0
    
    def network_repeated_receiver_ratio_30d(self, idx: int) -> float:
        tx = self.transactions[idx]
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=24*30)
        sender_prior = [i for i in prior if self.transactions[i]['sender_wallet'] == tx['sender_wallet']]
        
        if not sender_prior:
            return 0.0
        
        receiver_freq = Counter(self.transactions[i]['receiver_wallet'] for i in sender_prior)
        repeated_receivers = {r for r, c in receiver_freq.items() if c >= 2}
        
        repeated_count = sum(1 for i in sender_prior if self.transactions[i]['receiver_wallet'] in repeated_receivers)
        
        return repeated_count / len(sender_prior)
    
    def network_reciprocal_flow_ratio_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=24*7)
        
        outbound_counterparties = set(self.transactions[i]['receiver_wallet'] for i in prior 
                                      if self.transactions[i]['sender_wallet'] == tx['sender_wallet'])
        inbound_counterparties = set(self.transactions[i]['sender_wallet'] for i in prior 
                                      if self.transactions[i]['receiver_wallet'] == tx['sender_wallet'])
        
        active_counterparties = outbound_counterparties | inbound_counterparties
        
        if not active_counterparties:
            return 0.0
        
        reciprocal = outbound_counterparties & inbound_counterparties
        
        return len(reciprocal) / len(active_counterparties)
    
    def network_counterparty_set_change_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        current_time = tx['event_timestamp']
        
        recent_start = current_time - timedelta(days=7)
        prior_recent = [i for i in range(idx) 
                      if self.transactions[i]['event_timestamp'] >= recent_start
                      and self.transactions[i]['event_timestamp'] < current_time
                      and self.transactions[i]['partition'] == tx['partition']
                      and self.transactions[i]['sender_wallet'] == tx['sender_wallet']]
        
        prior_start = current_time - timedelta(days=14)
        prior_end = current_time - timedelta(days=7)
        prior_prior = [i for i in range(idx) 
                      if self.transactions[i]['event_timestamp'] >= prior_start
                      and self.transactions[i]['event_timestamp'] < prior_end
                      and self.transactions[i]['partition'] == tx['partition']
                      and self.transactions[i]['sender_wallet'] == tx['sender_wallet']]
        
        recent_receivers = set(self.transactions[i]['receiver_wallet'] for i in prior_recent)
        prior_receivers = set(self.transactions[i]['receiver_wallet'] for i in prior_prior)
        
        if not recent_receivers and not prior_receivers:
            return 0.0
        
        intersection = len(recent_receivers & prior_receivers)
        union = len(recent_receivers | prior_receivers)
        
        if union == 0:
            return 0.0
        
        jaccard = intersection / union
        return 1.0 - jaccard
    
    def network_pass_through_ratio_24h(self, idx: int) -> float:
        tx = self.transactions[idx]
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=24)
        
        outbound_value = sum(self.transactions[i]['amount'] for i in prior 
                          if self.transactions[i]['sender_wallet'] == tx['sender_wallet'])
        inbound_value = sum(self.transactions[i]['amount'] for i in prior 
                          if self.transactions[i]['receiver_wallet'] == tx['sender_wallet'])
        
        if inbound_value == 0:
            return 0.0
        
        return outbound_value / inbound_value
    
    def network_shared_counterparty_concentration_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=24*7)
        
        sender_counterparties = set()
        for i in prior:
            if self.transactions[i]['sender_wallet'] == tx['sender_wallet']:
                sender_counterparties.add(self.transactions[i]['receiver_wallet'])
            elif self.transactions[i]['receiver_wallet'] == tx['sender_wallet']:
                sender_counterparties.add(self.transactions[i]['sender_wallet'])
        
        if not sender_counterparties:
            return 0.0
        
        max_shared = 0
        for counterparty in sender_counterparties:
            counterparty_neighbours = set()
            for i in prior:
                if self.transactions[i]['sender_wallet'] == counterparty:
                    counterparty_neighbours.add(self.transactions[i]['receiver_wallet'])
                elif self.transactions[i]['receiver_wallet'] == counterparty:
                    counterparty_neighbours.add(self.transactions[i]['sender_wallet'])
            
            shared = len(sender_counterparties & counterparty_neighbours)
            max_shared = max(max_shared, shared)
        
        return max_shared / max(len(sender_counterparties), 1)
    
    # ========================================
    # AGENT FEATURES
    # ========================================
    
    def agent_prior_tx_count_1h(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=1)
        agent_prior = [i for i in prior if self.transactions[i]['agent_id'] == tx['agent_id']]
        
        return len(agent_prior)
    
    def agent_prior_tx_count_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=24*7)
        agent_prior = [i for i in prior if self.transactions[i]['agent_id'] == tx['agent_id']]
        
        return len(agent_prior)
    
    def agent_prior_value_sum_1h(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=1)
        agent_prior = [i for i in prior if self.transactions[i]['agent_id'] == tx['agent_id']]
        
        return sum(self.transactions[i]['amount'] for i in agent_prior)
    
    def agent_prior_value_sum_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=24*7)
        agent_prior = [i for i in prior if self.transactions[i]['agent_id'] == tx['agent_id']]
        
        return sum(self.transactions[i]['amount'] for i in agent_prior)
    
    def agent_unique_wallet_count_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=24*7)
        agent_prior = [i for i in prior if self.transactions[i]['agent_id'] == tx['agent_id']]
        
        wallets = set()
        for i in agent_prior:
            wallets.add(self.transactions[i]['sender_wallet'])
            wallets.add(self.transactions[i]['receiver_wallet'])
        
        return len(wallets)
    
    def agent_wallet_value_hhi_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=24*7)
        agent_prior = [i for i in prior if self.transactions[i]['agent_id'] == tx['agent_id']]
        
        if not agent_prior:
            return 0.0
        
        wallet_values = defaultdict(float)
        total_value = 0.0
        for i in agent_prior:
            wallet_values[self.transactions[i]['sender_wallet']] += self.transactions[i]['amount']
            total_value += self.transactions[i]['amount']
        
        if total_value == 0:
            return 0.0
        
        hhi = 0.0
        for value in wallet_values.values():
            share = value / total_value
            hhi += share ** 2
        
        return hhi
    
    def agent_repeat_wallet_ratio_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=24*7)
        agent_prior = [i for i in prior if self.transactions[i]['agent_id'] == tx['agent_id']]
        
        if not agent_prior:
            return 0.0
        
        wallet_freq = Counter()
        for i in agent_prior:
            wallet_freq[self.transactions[i]['sender_wallet']] += 1
            wallet_freq[self.transactions[i]['receiver_wallet']] += 1
        
        repeated_wallets = {w for w, c in wallet_freq.items() if c >= 2}
        
        repeated_count = 0
        for i in agent_prior:
            if self.transactions[i]['sender_wallet'] in repeated_wallets or self.transactions[i]['receiver_wallet'] in repeated_wallets:
                repeated_count += 1
        
        return repeated_count / len(agent_prior)
    
    def agent_current_wallet_is_new(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        prior = self.get_prior_indices(idx, tx['partition'])
        agent_prior = [i for i in prior if self.transactions[i]['agent_id'] == tx['agent_id']]
        
        prior_wallets = set()
        for i in agent_prior:
            prior_wallets.add(self.transactions[i]['sender_wallet'])
            prior_wallets.add(self.transactions[i]['receiver_wallet'])
        
        return 1.0 if tx['sender_wallet'] not in prior_wallets else 0.0
    
    def agent_inbound_outbound_value_ratio_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=24*7)
        agent_prior = [i for i in prior if self.transactions[i]['agent_id'] == tx['agent_id']]
        
        outbound_value = sum(self.transactions[i]['amount'] for i in agent_prior 
                          if self.transactions[i]['sender_wallet'] == tx['sender_wallet'])
        inbound_value = sum(self.transactions[i]['amount'] for i in agent_prior 
                          if self.transactions[i]['receiver_wallet'] == tx['sender_wallet'])
        
        if inbound_value == 0:
            return 0.0
        
        return outbound_value / inbound_value
    
    def agent_high_value_event_share_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        baseline_prior = self.get_prior_indices(idx, tx['partition'], max_hours=24*30)
        baseline_agent = [i for i in baseline_prior if self.transactions[i]['agent_id'] == tx['agent_id']]
        
        if len(baseline_agent) < 3:
            return 0.0
        
        baseline_amounts = [self.transactions[i]['amount'] for i in baseline_agent]
        baseline_median = statistics.median(baseline_amounts)
        
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=24*7)
        agent_prior = [i for i in prior if self.transactions[i]['agent_id'] == tx['agent_id']]
        
        if not agent_prior:
            return 0.0
        
        threshold = 2 * baseline_median
        high_value_count = sum(1 for i in agent_prior if self.transactions[i]['amount'] > threshold)
        
        return high_value_count / len(agent_prior)
    
    def agent_hourly_tx_zscore_30d(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        current_time = tx['event_timestamp']
        current_hour_start = current_time.replace(minute=0, second=0, microsecond=0)
        
        baseline_prior = self.get_prior_indices(idx, tx['partition'], max_hours=24*30)
        baseline_agent = [i for i in baseline_prior if self.transactions[i]['agent_id'] == tx['agent_id']]
        
        hourly_counts = defaultdict(int)
        for i in baseline_agent:
            hour_key = self.transactions[i]['event_timestamp'].replace(minute=0, second=0, microsecond=0)
            if hour_key < current_hour_start:
                hourly_counts[hour_key] += 1
        
        if len(hourly_counts) < 7:
            return 0.0
        
        current_hour_count = hourly_counts.get(current_hour_start, 0)
        
        counts = list(hourly_counts.values())
        mean_count = sum(counts) / len(counts)
        
        if len(counts) < 2:
            return 0.0
        
        variance = sum((c - mean_count) ** 2 for c in counts) / len(counts)
        std_count = math.sqrt(variance)
        
        if std_count == 0:
            return 0.0
        
        return (current_hour_count - mean_count) / std_count
    
    def agent_hourly_value_zscore_30d(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        current_time = tx['event_timestamp']
        current_hour_start = current_time.replace(minute=0, second=0, microsecond=0)
        
        baseline_prior = self.get_prior_indices(idx, tx['partition'], max_hours=24*30)
        baseline_agent = [i for i in baseline_prior if self.transactions[i]['agent_id'] == tx['agent_id']]
        
        hourly_values = defaultdict(float)
        for i in baseline_agent:
            hour_key = self.transactions[i]['event_timestamp'].replace(minute=0, second=0, microsecond=0)
            if hour_key < current_hour_start:
                hourly_values[hour_key] += self.transactions[i]['amount']
        
        if len(hourly_values) < 7:
            return 0.0
        
        current_hour_value = hourly_values.get(current_hour_start, 0)
        
        values = list(hourly_values.values())
        mean_value = sum(values) / len(values)
        
        if len(values) < 2:
            return 0.0
        
        variance = sum((v - mean_value) ** 2 for v in values) / len(values)
        std_value = math.sqrt(variance)
        
        if std_value == 0:
            return 0.0
        
        return (current_hour_value - mean_value) / std_value
    
    def agent_burst_concentration_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=24*7)
        agent_prior = [i for i in prior if self.transactions[i]['agent_id'] == tx['agent_id']]
        
        if not agent_prior:
            return 0.0
        
        bucket_counts = defaultdict(int)
        for i in agent_prior:
            minute_bucket = (self.transactions[i]['event_timestamp'].minute // 15) * 15
            bucket_key = self.transactions[i]['event_timestamp'].replace(minute=minute_bucket, second=0, microsecond=0)
            bucket_counts[bucket_key] += 1
        
        max_bucket = max(bucket_counts.values())
        
        return max_bucket / len(agent_prior)
    
    def agent_shared_wallet_flow_concentration_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        prior = self.get_prior_indices(idx, tx['partition'], max_hours=24*7)
        agent_prior = [i for i in prior if self.transactions[i]['agent_id'] == tx['agent_id']]
        
        if not agent_prior:
            return 0.0
        
        agent_wallets = set()
        for i in agent_prior:
            agent_wallets.add(self.transactions[i]['sender_wallet'])
            agent_wallets.add(self.transactions[i]['receiver_wallet'])
        
        if not agent_wallets:
            return 0.0
        
        external_counterparties = set()
        for i in agent_prior:
            if self.transactions[i]['sender_wallet'] in agent_wallets and self.transactions[i]['receiver_wallet'] not in agent_wallets:
                external_counterparties.add(self.transactions[i]['receiver_wallet'])
            elif self.transactions[i]['receiver_wallet'] in agent_wallets and self.transactions[i]['sender_wallet'] not in agent_wallets:
                external_counterparties.add(self.transactions[i]['sender_wallet'])
        
        max_linked = 0
        for counterparty in external_counterparties:
            linked_wallets = set()
            for i in prior:
                if self.transactions[i]['sender_wallet'] == counterparty and self.transactions[i]['receiver_wallet'] in agent_wallets:
                    linked_wallets.add(self.transactions[i]['receiver_wallet'])
                elif self.transactions[i]['receiver_wallet'] == counterparty and self.transactions[i]['sender_wallet'] in agent_wallets:
                    linked_wallets.add(self.transactions[i]['sender_wallet'])
            
            max_linked = max(max_linked, len(linked_wallets))
        
        return max_linked / max(len(agent_wallets), 1)
    
    # ========================================
    # EXTRACT ALL FEATURES
    # ========================================
    
    def extract_features(self, idx: int) -> Dict[str, float]:
        """Extract all 30 features for a transaction by index."""
        features = {}
        
        # Structuring (6)
        features['structuring_prior_tx_count_1h'] = self.structuring_prior_tx_count_1h(idx)
        features['structuring_prior_value_sum_24h'] = self.structuring_prior_value_sum_24h(idx)
        features['structuring_same_day_prior_tx_count'] = self.structuring_same_day_prior_tx_count(idx)
        features['structuring_repeated_amount_ratio_7d'] = self.structuring_repeated_amount_ratio_7d(idx)
        features['structuring_amount_cluster_dispersion_7d'] = self.structuring_amount_cluster_dispersion_7d(idx)
        features['structuring_near_threshold_history_ratio_7d'] = self.structuring_near_threshold_history_ratio_7d(idx)
        
        # Network (10)
        features['network_outbound_counterparty_count_7d'] = self.network_outbound_counterparty_count_7d(idx)
        features['network_inbound_counterparty_count_7d'] = self.network_inbound_counterparty_count_7d(idx)
        features['network_outbound_counterparty_entropy_30d'] = self.network_outbound_counterparty_entropy_30d(idx)
        features['network_top_counterparty_value_share_30d'] = self.network_top_counterparty_value_share_30d(idx)
        features['network_current_receiver_is_new'] = self.network_current_receiver_is_new(idx)
        features['network_repeated_receiver_ratio_30d'] = self.network_repeated_receiver_ratio_30d(idx)
        features['network_reciprocal_flow_ratio_7d'] = self.network_reciprocal_flow_ratio_7d(idx)
        features['network_counterparty_set_change_7d'] = self.network_counterparty_set_change_7d(idx)
        features['network_pass_through_ratio_24h'] = self.network_pass_through_ratio_24h(idx)
        features['network_shared_counterparty_concentration_7d'] = self.network_shared_counterparty_concentration_7d(idx)
        
        # Agent (14)
        features['agent_prior_tx_count_1h'] = self.agent_prior_tx_count_1h(idx)
        features['agent_prior_tx_count_7d'] = self.agent_prior_tx_count_7d(idx)
        features['agent_prior_value_sum_1h'] = self.agent_prior_value_sum_1h(idx)
        features['agent_prior_value_sum_7d'] = self.agent_prior_value_sum_7d(idx)
        features['agent_unique_wallet_count_7d'] = self.agent_unique_wallet_count_7d(idx)
        features['agent_wallet_value_hhi_7d'] = self.agent_wallet_value_hhi_7d(idx)
        features['agent_repeat_wallet_ratio_7d'] = self.agent_repeat_wallet_ratio_7d(idx)
        features['agent_current_wallet_is_new'] = self.agent_current_wallet_is_new(idx)
        features['agent_inbound_outbound_value_ratio_7d'] = self.agent_inbound_outbound_value_ratio_7d(idx)
        features['agent_high_value_event_share_7d'] = self.agent_high_value_event_share_7d(idx)
        features['agent_hourly_tx_zscore_30d'] = self.agent_hourly_tx_zscore_30d(idx)
        features['agent_hourly_value_zscore_30d'] = self.agent_hourly_value_zscore_30d(idx)
        features['agent_burst_concentration_7d'] = self.agent_burst_concentration_7d(idx)
        features['agent_shared_wallet_flow_concentration_7d'] = self.agent_shared_wallet_flow_concentration_7d(idx)
        
        return features

# =============================================================================
# MAIN EXTRACTION
# =============================================================================

def main():
    print("=" * 80)
    print("STAGE 13: OPTIMIZED 30-FEATURE MATRIX CONSTRUCTION")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Dataset Version: {DATASET_VERSION}")
    print()
    
    # Load data
    transactions, labels, wallet_partition, agent_partition = load_data()
    
    # Initialize optimized extractor
    print("Initializing optimized feature extractor...")
    extractor = OptimizedFeatureExtractor(transactions, wallet_partition, agent_partition)
    print()
    
    # Extract features
    print("Extracting features...")
    all_features = []
    
    for i in range(len(transactions)):
        if (i + 1) % 10000 == 0:
            print(f"  Progress: {i + 1} / {len(transactions)}")
        
        features = extractor.extract_features(i)
        all_features.append(features)
    
    print(f"  Completed: {len(all_features)} feature vectors")
    print()
    
    # Convert to numpy array
    print("Converting to feature matrix...")
    feature_names = list(all_features[0].keys())
    X = np.array([[f[name] for name in feature_names] for f in all_features])
    y = np.array([labels[tx['transaction_id']] for tx in transactions])
    
    print(f"  X shape: {X.shape}")
    print(f"  y shape: {y.shape}")
    print()
    
    # Check for NaN/infinity
    print("Checking numerical validity...")
    nan_count = np.isnan(X).sum()
    inf_count = np.isinf(X).sum()
    print(f"  NaN count: {nan_count}")
    print(f"  Infinity count: {inf_count}")
    
    if nan_count > 0 or inf_count > 0:
        print("  WARNING: Numerical issues detected")
    else:
        print("  PASS: All values valid")
    print()
    
    # Create output directory
    FEATURE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save matrices
    print("Saving feature matrices...")
    np.save(FEATURE_DIR / "X.npy", X)
    np.save(FEATURE_DIR / "y.npy", y)
    
    with open(FEATURE_DIR / "feature_names.json", 'w') as f:
        json.dump(feature_names, f, indent=2)
    
    print(f"  Saved to {FEATURE_DIR}")
    print()
    
    # Partition
    print("Creating partitioned matrices...")
    train_mask = [tx['partition'] == 'train' for tx in transactions]
    val_mask = [tx['partition'] == 'validation' for tx in transactions]
    test_mask = [tx['partition'] == 'final_test' for tx in transactions]
    independent_mask = [tx['partition'] == 'independent' for tx in transactions]
    
    X_train = X[train_mask]
    y_train = y[train_mask]
    X_val = X[val_mask]
    y_val = y[val_mask]
    X_test = X[test_mask]
    y_test = y[test_mask]
    X_independent = X[independent_mask]
    y_independent = y[independent_mask]
    
    print(f"  X_train: {X_train.shape}")
    print(f"  X_val: {X_val.shape}")
    print(f"  X_test: {X_test.shape}")
    print(f"  X_independent: {X_independent.shape}")
    print()
    
    np.save(FEATURE_DIR / "X_train.npy", X_train)
    np.save(FEATURE_DIR / "y_train.npy", y_train)
    np.save(FEATURE_DIR / "X_val.npy", X_val)
    np.save(FEATURE_DIR / "y_val.npy", y_val)
    np.save(FEATURE_DIR / "X_test.npy", X_test)
    np.save(FEATURE_DIR / "y_test.npy", y_test)
    np.save(FEATURE_DIR / "X_independent.npy", X_independent)
    np.save(FEATURE_DIR / "y_independent.npy", y_independent)
    
    print("=" * 80)
    print("FEATURE EXTRACTION COMPLETE")
    print("=" * 80)
    
    return X, y, feature_names

if __name__ == "__main__":
    X, y, feature_names = main()
    print("Stage 13 complete.")
