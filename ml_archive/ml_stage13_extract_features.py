"""
Stage 13: Exact 30-Feature Matrix Construction and Audit

This script constructs the authoritative feature matrix X[30] from the Stage 11
dataset according to the locked Stage 10B 30-feature specification.

CRITICAL:
- NO model training
- NO feature addition/removal
- NO specification changes
- STRICT temporal safety
- STRICT partition isolation
- EXACT Stage 10B formula compliance
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

SYNTHETIC_REPORTING_THRESHOLD = 10000  # From Stage 10C

# =============================================================================
# LOAD DATA
# =============================================================================

def load_data():
    """Load Stage 11 dataset files."""
    print("Loading Stage 11 dataset...")
    
    # Load transactions
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
    
    # Load ground truth
    with open(DATA_DIR / "ground_truth.json", 'r') as f:
        ground_truth = json.load(f)
    
    # Create label mapping
    labels = {gt['transaction_id']: gt['ground_truth_label'] for gt in ground_truth}
    
    # Load entity metadata
    with open(DATA_DIR / "entity_metadata.json", 'r') as f:
        entity_metadata = json.load(f)
    
    # Create partition mappings
    wallet_partition = {w['wallet_id']: w['partition'] for w in entity_metadata['wallets']}
    agent_partition = {a['agent_id']: a['partition'] for a in entity_metadata['agents']}
    
    print(f"  Loaded {len(transactions)} transactions")
    print(f"  Loaded {len(labels)} labels")
    print(f"  Loaded {len(wallet_partition)} wallet partitions")
    print(f"  Loaded {len(agent_partition)} agent partitions")
    print()
    
    return transactions, labels, wallet_partition, agent_partition

# =============================================================================
# FEATURE IMPLEMENTATION
# =============================================================================

class FeatureExtractor:
    """Implement all 30 Stage 10B features with exact formula compliance."""
    
    def __init__(self, transactions, wallet_partition, agent_partition):
        self.transactions = transactions
        self.wallet_partition = wallet_partition
        self.agent_partition = agent_partition
        
        # Build indices for efficient lookup
        self.tx_by_sequence = sorted(transactions, key=lambda tx: (tx['event_timestamp'], tx['event_sequence']))
        self.tx_index = {tx['transaction_id']: i for i, tx in enumerate(self.tx_by_sequence)}
        
        # Build wallet histories
        self.wallet_outbound_history = defaultdict(list)
        self.wallet_inbound_history = defaultdict(list)
        for tx in self.tx_by_sequence:
            self.wallet_outbound_history[tx['sender_wallet']].append(tx)
            self.wallet_inbound_history[tx['receiver_wallet']].append(tx)
        
        # Build agent histories
        self.agent_history = defaultdict(list)
        for tx in self.tx_by_sequence:
            if tx['agent_id']:
                self.agent_history[tx['agent_id']].append(tx)
    
    def get_prior_transactions(self, current_tx: Dict, window_hours: float = None, 
                              partition: str = None) -> List[Dict]:
        """Get prior transactions for current transaction respecting temporal and partition rules."""
        current_idx = self.tx_index[current_tx['transaction_id']]
        current_time = current_tx['event_timestamp']
        current_seq = current_tx['event_sequence']
        
        prior_txs = []
        for i in range(current_idx):
            tx = self.tx_by_sequence[i]
            
            # Temporal check: must be strictly earlier
            if tx['event_timestamp'] > current_time:
                continue
            if tx['event_timestamp'] == current_time and tx['event_sequence'] >= current_seq:
                continue
            
            # Partition check: must be same partition
            if partition and tx['partition'] != partition:
                continue
            
            # Window check
            if window_hours:
                time_diff = (current_time - tx['event_timestamp']).total_seconds() / 3600
                if time_diff > window_hours:
                    continue
            
            prior_txs.append(tx)
        
        return prior_txs
    
    # ========================================
    # STRUCTURING FEATURES (6)
    # ========================================
    
    def structuring_prior_tx_count_1h(self, tx: Dict) -> float:
        """Count sender's earlier outgoing transactions within 1 hour."""
        prior = self.get_prior_transactions(tx, window_hours=1, partition=tx['partition'])
        sender_prior = [p for p in prior if p['sender_wallet'] == tx['sender_wallet']]
        return len(sender_prior)
    
    def structuring_prior_value_sum_24h(self, tx: Dict) -> float:
        """Sum sender's earlier outgoing transaction values within 24 hours."""
        prior = self.get_prior_transactions(tx, window_hours=24, partition=tx['partition'])
        sender_prior = [p for p in prior if p['sender_wallet'] == tx['sender_wallet']]
        return sum(p['amount'] for p in sender_prior)
    
    def structuring_same_day_prior_tx_count(self, tx: Dict) -> float:
        """Count sender's earlier transactions on the same calendar day."""
        current_date = tx['event_timestamp'].date()
        prior = self.get_prior_transactions(tx, partition=tx['partition'])
        sender_prior = [p for p in prior if p['sender_wallet'] == tx['sender_wallet'] 
                       and p['event_timestamp'].date() == current_date]
        return len(sender_prior)
    
    def structuring_repeated_amount_ratio_7d(self, tx: Dict) -> float:
        """Share of prior amounts within 5% of current amount in 7 days."""
        prior = self.get_prior_transactions(tx, window_hours=24*7, partition=tx['partition'])
        sender_prior = [p for p in prior if p['sender_wallet'] == tx['sender_wallet']]
        
        if not sender_prior:
            return 0.0
        
        current_amount = tx['amount']
        threshold = 0.05 * max(current_amount, 1)
        
        matching = sum(1 for p in sender_prior 
                     if abs(p['amount'] - current_amount) <= threshold)
        
        return matching / len(sender_prior)
    
    def structuring_amount_cluster_dispersion_7d(self, tx: Dict) -> float:
        """Relative dispersion (std/mean) of prior amounts in 7 days."""
        prior = self.get_prior_transactions(tx, window_hours=24*7, partition=tx['partition'])
        sender_prior = [p for p in prior if p['sender_wallet'] == tx['sender_wallet']]
        
        if len(sender_prior) < 2:
            return 0.0
        
        amounts = [p['amount'] for p in sender_prior]
        mean_amt = sum(amounts) / len(amounts)
        
        if mean_amt == 0:
            return 0.0
        
        variance = sum((a - mean_amt) ** 2 for a in amounts) / len(amounts)
        std = math.sqrt(variance)
        
        return std / mean_amt
    
    def structuring_near_threshold_history_ratio_7d(self, tx: Dict) -> float:
        """Share of prior amounts in [9000, 10000) range in 7 days."""
        prior = self.get_prior_transactions(tx, window_hours=24*7, partition=tx['partition'])
        sender_prior = [p for p in prior if p['sender_wallet'] == tx['sender_wallet']]
        
        if not sender_prior:
            return 0.0
        
        threshold_lower = 0.90 * SYNTHETIC_REPORTING_THRESHOLD
        threshold_upper = SYNTHETIC_REPORTING_THRESHOLD
        
        near_threshold = sum(1 for p in sender_prior 
                          if threshold_lower <= p['amount'] < threshold_upper)
        
        return near_threshold / len(sender_prior)
    
    # ========================================
    # NETWORK FEATURES (10)
    # ========================================
    
    def network_outbound_counterparty_count_7d(self, tx: Dict) -> float:
        """Distinct receivers paid by sender in 7 days."""
        prior = self.get_prior_transactions(tx, window_hours=24*7, partition=tx['partition'])
        sender_prior = [p for p in prior if p['sender_wallet'] == tx['sender_wallet']]
        receivers = set(p['receiver_wallet'] for p in sender_prior)
        return len(receivers)
    
    def network_inbound_counterparty_count_7d(self, tx: Dict) -> float:
        """Distinct senders that paid receiver in 7 days."""
        prior = self.get_prior_transactions(tx, window_hours=24*7, partition=tx['partition'])
        receiver_prior = [p for p in prior if p['receiver_wallet'] == tx['receiver_wallet']]
        senders = set(p['sender_wallet'] for p in receiver_prior)
        return len(senders)
    
    def network_outbound_counterparty_entropy_30d(self, tx: Dict) -> float:
        """Entropy of sender's prior outbound receiver distribution in 30 days."""
        prior = self.get_prior_transactions(tx, window_hours=24*30, partition=tx['partition'])
        sender_prior = [p for p in prior if p['sender_wallet'] == tx['sender_wallet']]
        
        if not sender_prior:
            return 0.0
        
        # Group by receiver
        receiver_values = defaultdict(float)
        total_value = 0.0
        for p in sender_prior:
            receiver_values[p['receiver_wallet']] += p['amount']
            total_value += p['amount']
        
        if total_value == 0:
            return 0.0
        
        # Calculate entropy
        entropy = 0.0
        for value in receiver_values.values():
            p = value / total_value
            if p > 0:
                entropy -= p * math.log(p)
        
        return entropy
    
    def network_top_counterparty_value_share_30d(self, tx: Dict) -> float:
        """Largest receiver's share of sender's prior outbound value in 30 days."""
        prior = self.get_prior_transactions(tx, window_hours=24*30, partition=tx['partition'])
        sender_prior = [p for p in prior if p['sender_wallet'] == tx['sender_wallet']]
        
        if not sender_prior:
            return 0.0
        
        # Group by receiver
        receiver_values = defaultdict(float)
        total_value = 0.0
        for p in sender_prior:
            receiver_values[p['receiver_wallet']] += p['amount']
            total_value += p['amount']
        
        if total_value == 0:
            return 0.0
        
        max_value = max(receiver_values.values())
        return max_value / total_value
    
    def network_current_receiver_is_new(self, tx: Dict) -> float:
        """1 if current receiver absent from sender's prior outbound history."""
        prior = self.get_prior_transactions(tx, partition=tx['partition'])
        sender_prior = [p for p in prior if p['sender_wallet'] == tx['sender_wallet']]
        prior_receivers = set(p['receiver_wallet'] for p in sender_prior)
        
        return 1.0 if tx['receiver_wallet'] not in prior_receivers else 0.0
    
    def network_repeated_receiver_ratio_30d(self, tx: Dict) -> float:
        """Share of prior outbound to receivers seen at least twice in 30 days."""
        prior = self.get_prior_transactions(tx, window_hours=24*30, partition=tx['partition'])
        sender_prior = [p for p in prior if p['sender_wallet'] == tx['sender_wallet']]
        
        if not sender_prior:
            return 0.0
        
        # Count receiver frequencies
        receiver_freq = Counter(p['receiver_wallet'] for p in sender_prior)
        repeated_receivers = {r for r, c in receiver_freq.items() if c >= 2}
        
        repeated_count = sum(1 for p in sender_prior if p['receiver_wallet'] in repeated_receivers)
        
        return repeated_count / len(sender_prior)
    
    def network_reciprocal_flow_ratio_7d(self, tx: Dict) -> float:
        """Share of counterparties with both inbound and outbound flows in 7 days."""
        prior = self.get_prior_transactions(tx, window_hours=24*7, partition=tx['partition'])
        
        # Get outbound counterparties
        outbound_counterparties = set(p['receiver_wallet'] for p in prior 
                                     if p['sender_wallet'] == tx['sender_wallet'])
        
        # Get inbound counterparties
        inbound_counterparties = set(p['sender_wallet'] for p in prior 
                                     if p['receiver_wallet'] == tx['sender_wallet'])
        
        # Active counterparties
        active_counterparties = outbound_counterparties | inbound_counterparties
        
        if not active_counterparties:
            return 0.0
        
        # Counterparties with both directions
        reciprocal = outbound_counterparties & inbound_counterparties
        
        return len(reciprocal) / len(active_counterparties)
    
    def network_counterparty_set_change_7d(self, tx: Dict) -> float:
        """1 - Jaccard similarity between two prior 7-day receiver sets."""
        current_time = tx['event_timestamp']
        
        # Recent 7-day window (t-7d to t)
        recent_start = current_time - timedelta(days=7)
        prior_recent = [p for p in self.tx_by_sequence 
                      if p['event_timestamp'] >= recent_start
                      and p['event_timestamp'] < current_time
                      and p['event_sequence'] < tx['event_sequence']
                      and p['partition'] == tx['partition']
                      and p['sender_wallet'] == tx['sender_wallet']]
        
        # Prior 7-day window (t-14d to t-7d)
        prior_start = current_time - timedelta(days=14)
        prior_end = current_time - timedelta(days=7)
        prior_prior = [p for p in self.tx_by_sequence 
                      if p['event_timestamp'] >= prior_start
                      and p['event_timestamp'] < prior_end
                      and p['partition'] == tx['partition']
                      and p['sender_wallet'] == tx['sender_wallet']]
        
        recent_receivers = set(p['receiver_wallet'] for p in prior_recent)
        prior_receivers = set(p['receiver_wallet'] for p in prior_prior)
        
        if not recent_receivers and not prior_receivers:
            return 0.0
        
        # Jaccard similarity
        intersection = len(recent_receivers & prior_receivers)
        union = len(recent_receivers | prior_receivers)
        
        if union == 0:
            return 0.0
        
        jaccard = intersection / union
        return 1.0 - jaccard
    
    def network_pass_through_ratio_24h(self, tx: Dict) -> float:
        """Prior outbound value / prior inbound value in 24 hours."""
        prior = self.get_prior_transactions(tx, window_hours=24, partition=tx['partition'])
        
        outbound_value = sum(p['amount'] for p in prior if p['sender_wallet'] == tx['sender_wallet'])
        inbound_value = sum(p['amount'] for p in prior if p['receiver_wallet'] == tx['sender_wallet'])
        
        if inbound_value == 0:
            return 0.0
        
        return outbound_value / inbound_value
    
    def network_shared_counterparty_concentration_7d(self, tx: Dict) -> float:
        """Maximum second-order shared-neighbour share in 7 days."""
        prior = self.get_prior_transactions(tx, window_hours=24*7, partition=tx['partition'])
        
        # Build sender's counterparty set
        sender_counterparties = set()
        for p in prior:
            if p['sender_wallet'] == tx['sender_wallet']:
                sender_counterparties.add(p['receiver_wallet'])
            elif p['receiver_wallet'] == tx['sender_wallet']:
                sender_counterparties.add(p['sender_wallet'])
        
        if not sender_counterparties:
            return 0.0
        
        # For each counterparty, count shared neighbours
        max_shared = 0
        for counterparty in sender_counterparties:
            # Build counterparty's neighbour set
            counterparty_neighbours = set()
            for p in prior:
                if p['sender_wallet'] == counterparty:
                    counterparty_neighbours.add(p['receiver_wallet'])
                elif p['receiver_wallet'] == counterparty:
                    counterparty_neighbours.add(p['sender_wallet'])
            
            # Count shared
            shared = len(sender_counterparties & counterparty_neighbours)
            max_shared = max(max_shared, shared)
        
        return max_shared / max(len(sender_counterparties), 1)
    
    # ========================================
    # AGENT FEATURES (14)
    # ========================================
    
    def agent_prior_tx_count_1h(self, tx: Dict) -> float:
        """Earlier agent-attributed transactions in 1 hour."""
        if not tx['agent_id']:
            return 0.0
        
        prior = self.get_prior_transactions(tx, window_hours=1, partition=tx['partition'])
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        return len(agent_prior)
    
    def agent_prior_tx_count_7d(self, tx: Dict) -> float:
        """Earlier agent-attributed transactions in 7 days."""
        if not tx['agent_id']:
            return 0.0
        
        prior = self.get_prior_transactions(tx, window_hours=24*7, partition=tx['partition'])
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        return len(agent_prior)
    
    def agent_prior_value_sum_1h(self, tx: Dict) -> float:
        """Earlier agent-attributed value in 1 hour."""
        if not tx['agent_id']:
            return 0.0
        
        prior = self.get_prior_transactions(tx, window_hours=1, partition=tx['partition'])
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        return sum(p['amount'] for p in agent_prior)
    
    def agent_prior_value_sum_7d(self, tx: Dict) -> float:
        """Earlier agent-attributed value in 7 days."""
        if not tx['agent_id']:
            return 0.0
        
        prior = self.get_prior_transactions(tx, window_hours=24*7, partition=tx['partition'])
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        return sum(p['amount'] for p in agent_prior)
    
    def agent_unique_wallet_count_7d(self, tx: Dict) -> float:
        """Distinct wallets associated with agent in 7 days."""
        if not tx['agent_id']:
            return 0.0
        
        prior = self.get_prior_transactions(tx, window_hours=24*7, partition=tx['partition'])
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        wallets = set()
        for p in agent_prior:
            wallets.add(p['sender_wallet'])
            wallets.add(p['receiver_wallet'])
        
        return len(wallets)
    
    def agent_wallet_value_hhi_7d(self, tx: Dict) -> float:
        """Wallet value concentration at agent in 7 days (HHI)."""
        if not tx['agent_id']:
            return 0.0
        
        prior = self.get_prior_transactions(tx, window_hours=24*7, partition=tx['partition'])
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        if not agent_prior:
            return 0.0
        
        # Calculate wallet shares
        wallet_values = defaultdict(float)
        total_value = 0.0
        for p in agent_prior:
            wallet_values[p['sender_wallet']] += p['amount']
            total_value += p['amount']
        
        if total_value == 0:
            return 0.0
        
        # Calculate HHI
        hhi = 0.0
        for value in wallet_values.values():
            share = value / total_value
            hhi += share ** 2
        
        return hhi
    
    def agent_repeat_wallet_ratio_7d(self, tx: Dict) -> float:
        """Share of agent transactions involving repeated wallets in 7 days."""
        if not tx['agent_id']:
            return 0.0
        
        prior = self.get_prior_transactions(tx, window_hours=24*7, partition=tx['partition'])
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        if not agent_prior:
            return 0.0
        
        # Count wallet frequencies
        wallet_freq = Counter()
        for p in agent_prior:
            wallet_freq[p['sender_wallet']] += 1
            wallet_freq[p['receiver_wallet']] += 1
        
        repeated_wallets = {w for w, c in wallet_freq.items() if c >= 2}
        
        repeated_count = 0
        for p in agent_prior:
            if p['sender_wallet'] in repeated_wallets or p['receiver_wallet'] in repeated_wallets:
                repeated_count += 1
        
        return repeated_count / len(agent_prior)
    
    def agent_current_wallet_is_new(self, tx: Dict) -> float:
        """1 if current initiating wallet unseen in agent's prior history."""
        if not tx['agent_id']:
            return 0.0
        
        prior = self.get_prior_transactions(tx, partition=tx['partition'])
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        prior_wallets = set()
        for p in agent_prior:
            prior_wallets.add(p['sender_wallet'])
            prior_wallets.add(p['receiver_wallet'])
        
        return 1.0 if tx['sender_wallet'] not in prior_wallets else 0.0
    
    def agent_inbound_outbound_value_ratio_7d(self, tx: Dict) -> float:
        """Prior agent outbound value / inbound value in 7 days."""
        if not tx['agent_id']:
            return 0.0
        
        prior = self.get_prior_transactions(tx, window_hours=24*7, partition=tx['partition'])
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        outbound_value = sum(p['amount'] for p in agent_prior if p['sender_wallet'] == tx['sender_wallet'])
        inbound_value = sum(p['amount'] for p in agent_prior if p['receiver_wallet'] == tx['sender_wallet'])
        
        if inbound_value == 0:
            return 0.0
        
        return outbound_value / inbound_value
    
    def agent_high_value_event_share_7d(self, tx: Dict) -> float:
        """Share of prior agent events above 2x prior-30-day median."""
        if not tx['agent_id']:
            return 0.0
        
        # Get 30-day baseline (before current event)
        baseline_prior = self.get_prior_transactions(tx, window_hours=24*30, partition=tx['partition'])
        baseline_agent = [p for p in baseline_prior if p['agent_id'] == tx['agent_id']]
        
        if len(baseline_agent) < 3:
            return 0.0
        
        baseline_amounts = [p['amount'] for p in baseline_agent]
        baseline_median = statistics.median(baseline_amounts)
        
        # Get 7-day prior events
        prior = self.get_prior_transactions(tx, window_hours=24*7, partition=tx['partition'])
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        if not agent_prior:
            return 0.0
        
        threshold = 2 * baseline_median
        high_value_count = sum(1 for p in agent_prior if p['amount'] > threshold)
        
        return high_value_count / len(agent_prior)
    
    def agent_hourly_tx_zscore_30d(self, tx: Dict) -> float:
        """Deviation of current hour's count from prior 30-day hourly baseline."""
        if not tx['agent_id']:
            return 0.0
        
        current_time = tx['event_timestamp']
        current_hour_start = current_time.replace(minute=0, second=0, microsecond=0)
        
        # Get prior completed hours in 30 days
        baseline_prior = self.get_prior_transactions(tx, window_hours=24*30, partition=tx['partition'])
        baseline_agent = [p for p in baseline_prior if p['agent_id'] == tx['agent_id']]
        
        # Group by completed hour
        hourly_counts = defaultdict(int)
        for p in baseline_agent:
            hour_key = p['event_timestamp'].replace(minute=0, second=0, microsecond=0)
            if hour_key < current_hour_start:
                hourly_counts[hour_key] += 1
        
        if len(hourly_counts) < 7:
            return 0.0
        
        # Get current completed hour count
        current_hour_count = hourly_counts.get(current_hour_start, 0)
        
        # Calculate baseline statistics
        counts = list(hourly_counts.values())
        mean_count = sum(counts) / len(counts)
        
        if len(counts) < 2:
            return 0.0
        
        variance = sum((c - mean_count) ** 2 for c in counts) / len(counts)
        std_count = math.sqrt(variance)
        
        if std_count == 0:
            return 0.0
        
        return (current_hour_count - mean_count) / std_count
    
    def agent_hourly_value_zscore_30d(self, tx: Dict) -> float:
        """Deviation of current hour's value from prior 30-day hourly baseline."""
        if not tx['agent_id']:
            return 0.0
        
        current_time = tx['event_timestamp']
        current_hour_start = current_time.replace(minute=0, second=0, microsecond=0)
        
        # Get prior completed hours in 30 days
        baseline_prior = self.get_prior_transactions(tx, window_hours=24*30, partition=tx['partition'])
        baseline_agent = [p for p in baseline_prior if p['agent_id'] == tx['agent_id']]
        
        # Group by completed hour
        hourly_values = defaultdict(float)
        for p in baseline_agent:
            hour_key = p['event_timestamp'].replace(minute=0, second=0, microsecond=0)
            if hour_key < current_hour_start:
                hourly_values[hour_key] += p['amount']
        
        if len(hourly_values) < 7:
            return 0.0
        
        # Get current completed hour value
        current_hour_value = hourly_values.get(current_hour_start, 0)
        
        # Calculate baseline statistics
        values = list(hourly_values.values())
        mean_value = sum(values) / len(values)
        
        if len(values) < 2:
            return 0.0
        
        variance = sum((v - mean_value) ** 2 for v in values) / len(values)
        std_value = math.sqrt(variance)
        
        if std_value == 0:
            return 0.0
        
        return (current_hour_value - mean_value) / std_value
    
    def agent_burst_concentration_7d(self, tx: Dict) -> float:
        """Largest 15-minute bucket share of agent events in 7 days."""
        if not tx['agent_id']:
            return 0.0
        
        prior = self.get_prior_transactions(tx, window_hours=24*7, partition=tx['partition'])
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        if not agent_prior:
            return 0.0
        
        # Group by 15-minute buckets
        bucket_counts = defaultdict(int)
        for p in agent_prior:
            bucket_key = p['event_timestamp'].replace(minute=(p['event_timestamp'].minute // 15) * 15, 
                                                      second=0, microsecond=0)
            bucket_counts[bucket_key] += 1
        
        max_bucket = max(bucket_counts.values())
        
        return max_bucket / len(agent_prior)
    
    def agent_shared_wallet_flow_concentration_7d(self, tx: Dict) -> float:
        """Maximum common external counterparty share across agent wallets in 7 days."""
        if not tx['agent_id']:
            return 0.0
        
        prior = self.get_prior_transactions(tx, window_hours=24*7, partition=tx['partition'])
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        if not agent_prior:
            return 0.0
        
        # Get agent-associated wallets
        agent_wallets = set()
        for p in agent_prior:
            agent_wallets.add(p['sender_wallet'])
            agent_wallets.add(p['receiver_wallet'])
        
        if not agent_wallets:
            return 0.0
        
        # For each external counterparty, count linked agent wallets
        max_linked = 0
        external_counterparties = set()
        
        for p in agent_prior:
            if p['sender_wallet'] in agent_wallets and p['receiver_wallet'] not in agent_wallets:
                external_counterparties.add(p['receiver_wallet'])
            elif p['receiver_wallet'] in agent_wallets and p['sender_wallet'] not in agent_wallets:
                external_counterparties.add(p['sender_wallet'])
        
        for counterparty in external_counterparties:
            linked_wallets = set()
            for p in prior:
                if p['sender_wallet'] == counterparty and p['receiver_wallet'] in agent_wallets:
                    linked_wallets.add(p['receiver_wallet'])
                elif p['receiver_wallet'] == counterparty and p['sender_wallet'] in agent_wallets:
                    linked_wallets.add(p['sender_wallet'])
            
            max_linked = max(max_linked, len(linked_wallets))
        
        return max_linked / max(len(agent_wallets), 1)
    
    # ========================================
    # EXTRACT ALL FEATURES
    # ========================================
    
    def extract_features(self, tx: Dict) -> Dict[str, float]:
        """Extract all 30 features for a transaction."""
        features = {}
        
        # Structuring (6)
        features['structuring_prior_tx_count_1h'] = self.structuring_prior_tx_count_1h(tx)
        features['structuring_prior_value_sum_24h'] = self.structuring_prior_value_sum_24h(tx)
        features['structuring_same_day_prior_tx_count'] = self.structuring_same_day_prior_tx_count(tx)
        features['structuring_repeated_amount_ratio_7d'] = self.structuring_repeated_amount_ratio_7d(tx)
        features['structuring_amount_cluster_dispersion_7d'] = self.structuring_amount_cluster_dispersion_7d(tx)
        features['structuring_near_threshold_history_ratio_7d'] = self.structuring_near_threshold_history_ratio_7d(tx)
        
        # Network (10)
        features['network_outbound_counterparty_count_7d'] = self.network_outbound_counterparty_count_7d(tx)
        features['network_inbound_counterparty_count_7d'] = self.network_inbound_counterparty_count_7d(tx)
        features['network_outbound_counterparty_entropy_30d'] = self.network_outbound_counterparty_entropy_30d(tx)
        features['network_top_counterparty_value_share_30d'] = self.network_top_counterparty_value_share_30d(tx)
        features['network_current_receiver_is_new'] = self.network_current_receiver_is_new(tx)
        features['network_repeated_receiver_ratio_30d'] = self.network_repeated_receiver_ratio_30d(tx)
        features['network_reciprocal_flow_ratio_7d'] = self.network_reciprocal_flow_ratio_7d(tx)
        features['network_counterparty_set_change_7d'] = self.network_counterparty_set_change_7d(tx)
        features['network_pass_through_ratio_24h'] = self.network_pass_through_ratio_24h(tx)
        features['network_shared_counterparty_concentration_7d'] = self.network_shared_counterparty_concentration_7d(tx)
        
        # Agent (14)
        features['agent_prior_tx_count_1h'] = self.agent_prior_tx_count_1h(tx)
        features['agent_prior_tx_count_7d'] = self.agent_prior_tx_count_7d(tx)
        features['agent_prior_value_sum_1h'] = self.agent_prior_value_sum_1h(tx)
        features['agent_prior_value_sum_7d'] = self.agent_prior_value_sum_7d(tx)
        features['agent_unique_wallet_count_7d'] = self.agent_unique_wallet_count_7d(tx)
        features['agent_wallet_value_hhi_7d'] = self.agent_wallet_value_hhi_7d(tx)
        features['agent_repeat_wallet_ratio_7d'] = self.agent_repeat_wallet_ratio_7d(tx)
        features['agent_current_wallet_is_new'] = self.agent_current_wallet_is_new(tx)
        features['agent_inbound_outbound_value_ratio_7d'] = self.agent_inbound_outbound_value_ratio_7d(tx)
        features['agent_high_value_event_share_7d'] = self.agent_high_value_event_share_7d(tx)
        features['agent_hourly_tx_zscore_30d'] = self.agent_hourly_tx_zscore_30d(tx)
        features['agent_hourly_value_zscore_30d'] = self.agent_hourly_value_zscore_30d(tx)
        features['agent_burst_concentration_7d'] = self.agent_burst_concentration_7d(tx)
        features['agent_shared_wallet_flow_concentration_7d'] = self.agent_shared_wallet_flow_concentration_7d(tx)
        
        return features

# =============================================================================
# MAIN EXTRACTION
# =============================================================================

def main():
    print("=" * 80)
    print("STAGE 13: EXACT 30-FEATURE MATRIX CONSTRUCTION AND AUDIT")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Dataset Version: {DATASET_VERSION}")
    print()
    
    # Load data
    transactions, labels, wallet_partition, agent_partition = load_data()
    
    # Initialize feature extractor
    print("Initializing feature extractor...")
    extractor = FeatureExtractor(transactions, wallet_partition, agent_partition)
    print()
    
    # Extract features for all transactions
    print("Extracting features for all transactions...")
    all_features = []
    
    for i, tx in enumerate(transactions):
        if (i + 1) % 10000 == 0:
            print(f"  Progress: {i + 1} / {len(transactions)}")
        
        features = extractor.extract_features(tx)
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
    
    # Create output directory
    FEATURE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save complete feature matrix
    print("Saving feature matrices...")
    np.save(FEATURE_DIR / "X.npy", X)
    np.save(FEATURE_DIR / "y.npy", y)
    
    # Save feature names
    with open(FEATURE_DIR / "feature_names.json", 'w') as f:
        json.dump(feature_names, f, indent=2)
    
    print(f"  Saved to {FEATURE_DIR}")
    print()
    
    # Partition the data
    print("Creating partitioned feature matrices...")
    
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
    
    # Save partitioned matrices
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
    print()
    print("Generated files:")
    print(f"  {FEATURE_DIR / 'X.npy'}")
    print(f"  {FEATURE_DIR / 'y.npy'}")
    print(f"  {FEATURE_DIR / 'feature_names.json'}")
    print(f"  {FEATURE_DIR / 'X_train.npy'}")
    print(f"  {FEATURE_DIR / 'y_train.npy'}")
    print(f"  {FEATURE_DIR / 'X_val.npy'}")
    print(f"  {FEATURE_DIR / 'y_val.npy'}")
    print(f"  {FEATURE_DIR / 'X_test.npy'}")
    print(f"  {FEATURE_DIR / 'y_test.npy'}")
    print(f"  {FEATURE_DIR / 'X_independent.npy'}")
    print(f"  {FEATURE_DIR / 'y_independent.npy'}")
    print()
    
    return X, y, feature_names

if __name__ == "__main__":
    X, y, feature_names = main()
    print("Stage 13 feature extraction complete.")
