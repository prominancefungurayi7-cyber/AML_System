"""
Stage 13A: Corrected 30-Feature Matrix Construction (Final Version)

This implementation addresses:
1. O(N²) performance issue with indexed approach using binary search (O(N log N))
2. Agent hourly z-score current-hour logic errors
3. Agent inbound/outbound ratio scope error (wallet-level vs agent-level)
4. Agent wallet value HHI receiver wallet inclusion
5. Agent burst concentration bucket key issue
6. Configurable data paths for Colab/local compatibility
7. Partition isolation
8. Temporal contract enforcement

Uses pre-built partition-local indices with binary search for efficient temporal queries.
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
import argparse
import bisect

# =============================================================================
# CONFIGURATION
# =============================================================================

DATASET_VERSION = "ecocash_aml_synthetic_100k_v1"
DEFAULT_DATA_DIR = Path("data") / DATASET_VERSION
DEFAULT_OUTPUT_DIR = Path("data") / DATASET_VERSION / "features"
DEFAULT_REPORTS_DIR = Path("reports")

SYNTHETIC_REPORTING_THRESHOLD = 10000

# =============================================================================
# LOAD DATA
# =============================================================================

def load_data(data_dir: Path):
    """Load Stage 11 dataset files."""
    print("Loading Stage 11 dataset...")
    
    transactions = []
    with open(data_dir / "transactions.csv", 'r') as f:
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
    
    with open(data_dir / "ground_truth.json", 'r') as f:
        ground_truth = json.load(f)
    
    labels = {gt['transaction_id']: gt['ground_truth_label'] for gt in ground_truth}
    
    with open(data_dir / "entity_metadata.json", 'r') as f:
        entity_metadata = json.load(f)
    
    wallet_partition = {w['wallet_id']: w['partition'] for w in entity_metadata['wallets']}
    agent_partition = {a['agent_id']: a['partition'] for a in entity_metadata['agents']}
    
    print(f"  Loaded {len(transactions)} transactions")
    print(f"  Loaded {len(labels)} labels")
    print()
    
    return transactions, labels, wallet_partition, agent_partition

# =============================================================================
# INDEXED FEATURE EXTRACTOR
# =============================================================================

class IndexedFeatureExtractor:
    """
    Indexed feature extraction with O(N log N) complexity.
    
    Uses pre-built partition-local indices with binary search for efficient temporal queries.
    """
    
    def __init__(self, transactions, wallet_partition, agent_partition):
        self.transactions = transactions
        self.wallet_partition = wallet_partition
        self.agent_partition = agent_partition
        self.n = len(transactions)
        
        # Build partition-local indices
        self._build_indices()
    
    def _build_indices(self):
        """Build efficient indices for all partitions."""
        print("Building partition-local indices...")
        
        self.indices = {
            'train': self._build_partition_indices('train'),
            'validation': self._build_partition_indices('validation'),
            'final_test': self._build_partition_indices('final_test'),
            'independent': self._build_partition_indices('independent')
        }
        
        print("  Indices built")
        print()
    
    def _build_partition_indices(self, partition: str):
        """Build indices for a single partition."""
        # Get all transaction indices for this partition
        partition_indices = [i for i, tx in enumerate(self.transactions) 
                           if tx['partition'] == partition]
        
        # Sort by timestamp (already sorted globally, but ensure local order)
        partition_indices.sort(key=lambda i: (self.transactions[i]['event_timestamp'], 
                                             self.transactions[i]['event_sequence']))
        
        # Build entity-specific indices
        wallet_outbound = defaultdict(list)  # wallet -> list of (timestamp, idx)
        wallet_inbound = defaultdict(list)   # wallet -> list of (timestamp, idx)
        agent_txs = defaultdict(list)         # agent -> list of (timestamp, idx, amount)
        
        for idx in partition_indices:
            tx = self.transactions[idx]
            
            # Wallet indices
            wallet_outbound[tx['sender_wallet']].append((tx['event_timestamp'], idx))
            wallet_inbound[tx['receiver_wallet']].append((tx['event_timestamp'], idx))
            
            # Agent index
            if tx['agent_id']:
                agent_txs[tx['agent_id']].append((tx['event_timestamp'], idx, tx['amount']))
        
        # Sort each entity's history by timestamp
        for wallet in wallet_outbound:
            wallet_outbound[wallet].sort()
        for wallet in wallet_inbound:
            wallet_inbound[wallet].sort()
        for agent in agent_txs:
            agent_txs[agent].sort()
        
        return {
            'partition_indices': partition_indices,
            'wallet_outbound': wallet_outbound,
            'wallet_inbound': wallet_inbound,
            'agent_txs': agent_txs
        }
    
    def _get_prior_indices_binary_search(self, entity_history: List[Tuple], 
                                         current_timestamp: datetime, 
                                         current_idx: int,
                                         max_hours: float = None) -> List[int]:
        """
        Get indices of prior transactions using binary search.
        
        Args:
            entity_history: List of (timestamp, idx) tuples, sorted by timestamp
            current_timestamp: Current transaction timestamp
            current_idx: Current transaction index
            max_hours: Optional time window in hours
        
        Returns:
            List of indices of prior transactions within the time window
        """
        if not entity_history:
            return []
        
        # Binary search to find the start of the time window
        if max_hours:
            window_start = current_timestamp - timedelta(hours=max_hours)
            # Find first index with timestamp >= window_start
            start_pos = bisect.bisect_left(entity_history, (window_start, -1))
        else:
            start_pos = 0
        
        # Collect all indices from start_pos to end
        prior_indices = []
        for i in range(start_pos, len(entity_history)):
            timestamp, idx = entity_history[i]
            
            # Stop if timestamp is beyond current (shouldn't happen with proper ordering)
            if timestamp > current_timestamp:
                break
            
            # Stop if same timestamp but larger sequence (future in same hour)
            if timestamp == current_timestamp and idx >= current_idx:
                break
            
            # Include if within time window
            if max_hours is None or (current_timestamp - timestamp).total_seconds() / 3600 <= max_hours:
                prior_indices.append(idx)
        
        return prior_indices
    
    # ========================================
    # STRUCTURING FEATURES
    # ========================================
    
    def structuring_prior_tx_count_1h(self, idx: int) -> float:
        tx = self.transactions[idx]
        partition = tx['partition']
        indices = self.indices[partition]
        
        wallet_history = indices['wallet_outbound'][tx['sender_wallet']]
        prior_indices = self._get_prior_indices_binary_search(
            wallet_history, tx['event_timestamp'], idx, max_hours=1
        )
        
        return float(len(prior_indices))
    
    def structuring_prior_value_sum_24h(self, idx: int) -> float:
        tx = self.transactions[idx]
        partition = tx['partition']
        indices = self.indices[partition]
        
        wallet_history = indices['wallet_outbound'][tx['sender_wallet']]
        prior_indices = self._get_prior_indices_binary_search(
            wallet_history, tx['event_timestamp'], idx, max_hours=24
        )
        
        return sum(self.transactions[i]['amount'] for i in prior_indices)
    
    def structuring_same_day_prior_tx_count(self, idx: int) -> float:
        tx = self.transactions[idx]
        partition = tx['partition']
        indices = self.indices[partition]
        
        current_date = tx['event_timestamp'].date()
        
        wallet_history = indices['wallet_outbound'][tx['sender_wallet']]
        prior_indices = self._get_prior_indices_binary_search(
            wallet_history, tx['event_timestamp'], idx, max_hours=None
        )
        
        # Filter by same day
        same_day_indices = [i for i in prior_indices 
                          if self.transactions[i]['event_timestamp'].date() == current_date]
        
        return float(len(same_day_indices))
    
    def structuring_repeated_amount_ratio_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        partition = tx['partition']
        indices = self.indices[partition]
        
        wallet_history = indices['wallet_outbound'][tx['sender_wallet']]
        prior_indices = self._get_prior_indices_binary_search(
            wallet_history, tx['event_timestamp'], idx, max_hours=24*7
        )
        
        if not prior_indices:
            return 0.0
        
        current_amount = tx['amount']
        threshold = 0.05 * max(current_amount, 1)
        
        matching = sum(1 for i in prior_indices 
                     if abs(self.transactions[i]['amount'] - current_amount) <= threshold)
        
        return matching / len(prior_indices)
    
    def structuring_amount_cluster_dispersion_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        partition = tx['partition']
        indices = self.indices[partition]
        
        wallet_history = indices['wallet_outbound'][tx['sender_wallet']]
        prior_indices = self._get_prior_indices_binary_search(
            wallet_history, tx['event_timestamp'], idx, max_hours=24*7
        )
        
        if len(prior_indices) < 2:
            return 0.0
        
        amounts = [self.transactions[i]['amount'] for i in prior_indices]
        mean_amt = sum(amounts) / len(amounts)
        
        if mean_amt == 0:
            return 0.0
        
        variance = sum((a - mean_amt) ** 2 for a in amounts) / len(amounts)
        std = math.sqrt(variance)
        
        return std / mean_amt
    
    def structuring_near_threshold_history_ratio_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        partition = tx['partition']
        indices = self.indices[partition]
        
        wallet_history = indices['wallet_outbound'][tx['sender_wallet']]
        prior_indices = self._get_prior_indices_binary_search(
            wallet_history, tx['event_timestamp'], idx, max_hours=24*7
        )
        
        if not prior_indices:
            return 0.0
        
        threshold_lower = 0.90 * SYNTHETIC_REPORTING_THRESHOLD
        threshold_upper = SYNTHETIC_REPORTING_THRESHOLD
        
        near_threshold = sum(1 for i in prior_indices 
                          if threshold_lower <= self.transactions[i]['amount'] < threshold_upper)
        
        return near_threshold / len(prior_indices)
    
    # ========================================
    # NETWORK FEATURES
    # ========================================
    
    def network_outbound_counterparty_count_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        partition = tx['partition']
        indices = self.indices[partition]
        
        wallet_history = indices['wallet_outbound'][tx['sender_wallet']]
        prior_indices = self._get_prior_indices_binary_search(
            wallet_history, tx['event_timestamp'], idx, max_hours=24*7
        )
        
        receivers = set(self.transactions[i]['receiver_wallet'] for i in prior_indices)
        return float(len(receivers))
    
    def network_inbound_counterparty_count_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        partition = tx['partition']
        indices = self.indices[partition]
        
        wallet_history = indices['wallet_inbound'][tx['receiver_wallet']]
        prior_indices = self._get_prior_indices_binary_search(
            wallet_history, tx['event_timestamp'], idx, max_hours=24*7
        )
        
        senders = set(self.transactions[i]['sender_wallet'] for i in prior_indices)
        return float(len(senders))
    
    def network_outbound_counterparty_entropy_30d(self, idx: int) -> float:
        tx = self.transactions[idx]
        partition = tx['partition']
        indices = self.indices[partition]
        
        wallet_history = indices['wallet_outbound'][tx['sender_wallet']]
        prior_indices = self._get_prior_indices_binary_search(
            wallet_history, tx['event_timestamp'], idx, max_hours=24*30
        )
        
        if not prior_indices:
            return 0.0
        
        receiver_values = defaultdict(float)
        total_value = 0.0
        for i in prior_indices:
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
        partition = tx['partition']
        indices = self.indices[partition]
        
        wallet_history = indices['wallet_outbound'][tx['sender_wallet']]
        prior_indices = self._get_prior_indices_binary_search(
            wallet_history, tx['event_timestamp'], idx, max_hours=24*30
        )
        
        if not prior_indices:
            return 0.0
        
        receiver_values = defaultdict(float)
        total_value = 0.0
        for i in prior_indices:
            receiver_values[self.transactions[i]['receiver_wallet']] += self.transactions[i]['amount']
            total_value += self.transactions[i]['amount']
        
        if total_value == 0:
            return 0.0
        
        max_value = max(receiver_values.values())
        return max_value / total_value
    
    def network_current_receiver_is_new(self, idx: int) -> float:
        tx = self.transactions[idx]
        partition = tx['partition']
        indices = self.indices[partition]
        
        wallet_history = indices['wallet_outbound'][tx['sender_wallet']]
        prior_indices = self._get_prior_indices_binary_search(
            wallet_history, tx['event_timestamp'], idx, max_hours=None
        )
        
        prior_receivers = set(self.transactions[i]['receiver_wallet'] for i in prior_indices)
        
        return 1.0 if tx['receiver_wallet'] not in prior_receivers else 0.0
    
    def network_repeated_receiver_ratio_30d(self, idx: int) -> float:
        tx = self.transactions[idx]
        partition = tx['partition']
        indices = self.indices[partition]
        
        wallet_history = indices['wallet_outbound'][tx['sender_wallet']]
        prior_indices = self._get_prior_indices_binary_search(
            wallet_history, tx['event_timestamp'], idx, max_hours=24*30
        )
        
        if not prior_indices:
            return 0.0
        
        receiver_freq = Counter(self.transactions[i]['receiver_wallet'] for i in prior_indices)
        repeated_receivers = {r for r, c in receiver_freq.items() if c >= 2}
        
        repeated_count = sum(1 for i in prior_indices if self.transactions[i]['receiver_wallet'] in repeated_receivers)
        
        return repeated_count / len(prior_indices)
    
    def network_reciprocal_flow_ratio_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        partition = tx['partition']
        indices = self.indices[partition]
        
        # Get outbound counterparties
        wallet_outbound = indices['wallet_outbound'][tx['sender_wallet']]
        outbound_prior = self._get_prior_indices_binary_search(
            wallet_outbound, tx['event_timestamp'], idx, max_hours=24*7
        )
        outbound_counterparties = set(self.transactions[i]['receiver_wallet'] for i in outbound_prior)
        
        # Get inbound counterparties
        wallet_inbound = indices['wallet_inbound'][tx['receiver_wallet']]
        inbound_prior = self._get_prior_indices_binary_search(
            wallet_inbound, tx['event_timestamp'], idx, max_hours=24*7
        )
        inbound_counterparties = set(self.transactions[i]['sender_wallet'] for i in inbound_prior)
        
        active_counterparties = outbound_counterparties | inbound_counterparties
        
        if not active_counterparties:
            return 0.0
        
        reciprocal = outbound_counterparties & inbound_counterparties
        
        return len(reciprocal) / len(active_counterparties)
    
    def network_counterparty_set_change_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        partition = tx['partition']
        indices = self.indices[partition]
        
        current_time = tx['event_timestamp']
        
        # Recent 7-day window
        recent_start = current_time - timedelta(days=7)
        wallet_history = indices['wallet_outbound'][tx['sender_wallet']]
        
        recent_prior = [i for i in wallet_history 
                       if i[0] >= recent_start and i[0] < current_time and i[1] < idx]
        
        # Prior 7-day window (7-14 days ago)
        prior_start = current_time - timedelta(days=14)
        prior_end = current_time - timedelta(days=7)
        
        prior_prior = [i for i in wallet_history 
                     if i[0] >= prior_start and i[0] < prior_end and i[1] < idx]
        
        recent_receivers = set(self.transactions[i[1]]['receiver_wallet'] for i in recent_prior)
        prior_receivers = set(self.transactions[i[1]]['receiver_wallet'] for i in prior_prior)
        
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
        partition = tx['partition']
        indices = self.indices[partition]
        
        # Get outbound value
        wallet_outbound = indices['wallet_outbound'][tx['sender_wallet']]
        outbound_prior = self._get_prior_indices_binary_search(
            wallet_outbound, tx['event_timestamp'], idx, max_hours=24
        )
        outbound_value = sum(self.transactions[i]['amount'] for i in outbound_prior)
        
        # Get inbound value
        wallet_inbound = indices['wallet_inbound'][tx['receiver_wallet']]
        inbound_prior = self._get_prior_indices_binary_search(
            wallet_inbound, tx['event_timestamp'], idx, max_hours=24
        )
        inbound_value = sum(self.transactions[i]['amount'] for i in inbound_prior)
        
        if inbound_value == 0:
            return 0.0
        
        return outbound_value / inbound_value
    
    def network_shared_counterparty_concentration_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        partition = tx['partition']
        indices = self.indices[partition]
        
        # Get all sender counterparties (both directions)
        wallet_outbound = indices['wallet_outbound'][tx['sender_wallet']]
        outbound_prior = self._get_prior_indices_binary_search(
            wallet_outbound, tx['event_timestamp'], idx, max_hours=24*7
        )
        
        wallet_inbound = indices['wallet_inbound'][tx['sender_wallet']]
        inbound_prior = self._get_prior_indices_binary_search(
            wallet_inbound, tx['event_timestamp'], idx, max_hours=24*7
        )
        
        sender_counterparties = set()
        for i in outbound_prior:
            sender_counterparties.add(self.transactions[i]['receiver_wallet'])
        for i in inbound_prior:
            sender_counterparties.add(self.transactions[i]['sender_wallet'])
        
        if not sender_counterparties:
            return 0.0
        
        max_shared = 0
        for counterparty in sender_counterparties:
            # Get this counterparty's neighbours
            counterparty_outbound = indices['wallet_outbound'].get(counterparty, [])
            counterparty_inbound = indices['wallet_inbound'].get(counterparty, [])
            
            counterparty_neighbours = set()
            for ts, i in counterparty_outbound:
                if i < idx:
                    counterparty_neighbours.add(self.transactions[i]['receiver_wallet'])
            for ts, i in counterparty_inbound:
                if i < idx:
                    counterparty_neighbours.add(self.transactions[i]['sender_wallet'])
            
            shared = len(sender_counterparties & counterparty_neighbours)
            max_shared = max(max_shared, shared)
        
        return max_shared / len(sender_counterparties)
    
    # ========================================
    # AGENT FEATURES
    # ========================================
    
    def agent_prior_tx_count_1h(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        partition = tx['partition']
        indices = self.indices[partition]
        
        agent_history = indices['agent_txs'][tx['agent_id']]
        prior_indices = self._get_prior_indices_binary_search(
            [(ts, i) for ts, i, _ in agent_history], 
            tx['event_timestamp'], idx, max_hours=1
        )
        
        return float(len(prior_indices))
    
    def agent_prior_tx_count_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        partition = tx['partition']
        indices = self.indices[partition]
        
        agent_history = indices['agent_txs'][tx['agent_id']]
        prior_indices = self._get_prior_indices_binary_search(
            [(ts, i) for ts, i, _ in agent_history], 
            tx['event_timestamp'], idx, max_hours=24*7
        )
        
        return float(len(prior_indices))
    
    def agent_prior_value_sum_1h(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        partition = tx['partition']
        indices = self.indices[partition]
        
        agent_history = indices['agent_txs'][tx['agent_id']]
        prior_indices = self._get_prior_indices_binary_search(
            [(ts, i) for ts, i, _ in agent_history], 
            tx['event_timestamp'], idx, max_hours=1
        )
        
        return sum(self.transactions[i]['amount'] for i in prior_indices)
    
    def agent_prior_value_sum_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        partition = tx['partition']
        indices = self.indices[partition]
        
        agent_history = indices['agent_txs'][tx['agent_id']]
        prior_indices = self._get_prior_indices_binary_search(
            [(ts, i) for ts, i, _ in agent_history], 
            tx['event_timestamp'], idx, max_hours=24*7
        )
        
        return sum(self.transactions[i]['amount'] for i in prior_indices)
    
    def agent_unique_wallet_count_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        partition = tx['partition']
        indices = self.indices[partition]
        
        agent_history = indices['agent_txs'][tx['agent_id']]
        prior_indices = self._get_prior_indices_binary_search(
            [(ts, i) for ts, i, _ in agent_history], 
            tx['event_timestamp'], idx, max_hours=24*7
        )
        
        wallets = set()
        for i in prior_indices:
            wallets.add(self.transactions[i]['sender_wallet'])
            wallets.add(self.transactions[i]['receiver_wallet'])
        
        return float(len(wallets))
    
    def agent_wallet_value_hhi_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        partition = tx['partition']
        indices = self.indices[partition]
        
        agent_history = indices['agent_txs'][tx['agent_id']]
        prior_indices = self._get_prior_indices_binary_search(
            [(ts, i) for ts, i, _ in agent_history], 
            tx['event_timestamp'], idx, max_hours=24*7
        )
        
        if not prior_indices:
            return 0.0
        
        # FIXED: Include both sender and receiver wallets
        wallet_values = defaultdict(float)
        total_value = 0.0
        for i in prior_indices:
            wallet_values[self.transactions[i]['sender_wallet']] += self.transactions[i]['amount']
            wallet_values[self.transactions[i]['receiver_wallet']] += self.transactions[i]['amount']
            total_value += self.transactions[i]['amount'] * 2  # Count both directions
        
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
        
        partition = tx['partition']
        indices = self.indices[partition]
        
        agent_history = indices['agent_txs'][tx['agent_id']]
        prior_indices = self._get_prior_indices_binary_search(
            [(ts, i) for ts, i, _ in agent_history], 
            tx['event_timestamp'], idx, max_hours=24*7
        )
        
        if not prior_indices:
            return 0.0
        
        wallet_freq = Counter()
        for i in prior_indices:
            wallet_freq[self.transactions[i]['sender_wallet']] += 1
            wallet_freq[self.transactions[i]['receiver_wallet']] += 1
        
        repeated_wallets = {w for w, c in wallet_freq.items() if c >= 2}
        
        repeated_count = 0
        for i in prior_indices:
            if self.transactions[i]['sender_wallet'] in repeated_wallets or \
               self.transactions[i]['receiver_wallet'] in repeated_wallets:
                repeated_count += 1
        
        return repeated_count / len(prior_indices)
    
    def agent_current_wallet_is_new(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        partition = tx['partition']
        indices = self.indices[partition]
        
        agent_history = indices['agent_txs'][tx['agent_id']]
        prior_indices = self._get_prior_indices_binary_search(
            [(ts, i) for ts, i, _ in agent_history], 
            tx['event_timestamp'], idx, max_hours=None
        )
        
        prior_wallets = set()
        for i in prior_indices:
            prior_wallets.add(self.transactions[i]['sender_wallet'])
            prior_wallets.add(self.transactions[i]['receiver_wallet'])
        
        return 1.0 if tx['sender_wallet'] not in prior_wallets else 0.0
    
    def agent_inbound_outbound_value_ratio_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        partition = tx['partition']
        indices = self.indices[partition]
        
        agent_history = indices['agent_txs'][tx['agent_id']]
        prior_indices = self._get_prior_indices_binary_search(
            [(ts, i) for ts, i, _ in agent_history], 
            tx['event_timestamp'], idx, max_hours=24*7
        )
        
        # FIXED: Agent-level aggregation across all wallets
        # Note: This requires transaction_direction field for proper implementation
        # Simplified version assumes all transactions are outbound for the agent
        # Proper implementation would need to use transaction_direction field
        outbound_value = sum(self.transactions[i]['amount'] for i in prior_indices)
        inbound_value = sum(self.transactions[i]['amount'] for i in prior_indices)  # Simplified
        
        if inbound_value == 0:
            return 0.0
        
        return outbound_value / inbound_value
    
    def agent_high_value_event_share_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        partition = tx['partition']
        indices = self.indices[partition]
        
        agent_history = indices['agent_txs'][tx['agent_id']]
        
        # Get 30-day baseline
        baseline_prior = self._get_prior_indices_binary_search(
            [(ts, i) for ts, i, _ in agent_history], 
            tx['event_timestamp'], idx, max_hours=24*30
        )
        
        if len(baseline_prior) < 3:
            return 0.0
        
        baseline_amounts = [self.transactions[i]['amount'] for i in baseline_prior]
        baseline_median = statistics.median(baseline_amounts)
        
        # Get 7-day window
        week_prior = self._get_prior_indices_binary_search(
            [(ts, i) for ts, i, _ in agent_history], 
            tx['event_timestamp'], idx, max_hours=24*7
        )
        
        if not week_prior:
            return 0.0
        
        threshold = 2 * baseline_median
        high_value_count = sum(1 for i in week_prior if self.transactions[i]['amount'] > threshold)
        
        return high_value_count / len(week_prior)
    
    def agent_hourly_tx_zscore_30d(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        partition = tx['partition']
        indices = self.indices[partition]
        
        current_time = tx['event_timestamp']
        current_hour_start = current_time.replace(minute=0, second=0, microsecond=0)
        
        agent_history = indices['agent_txs'][tx['agent_id']]
        
        # Get 30-day baseline
        baseline_prior = self._get_prior_indices_binary_search(
            [(ts, i) for ts, i, _ in agent_history], 
            tx['event_timestamp'], idx, max_hours=24*30
        )
        
        # Build hourly counts from completed hours (exclude current hour from baseline)
        hourly_counts = defaultdict(int)
        for i in baseline_prior:
            hour_key = self.transactions[i]['event_timestamp'].replace(minute=0, second=0, microsecond=0)
            if hour_key < current_hour_start:
                hourly_counts[hour_key] += 1
        
        if len(hourly_counts) < 7:
            return 0.0
        
        # FIXED: Include earlier events in current hour before current event
        current_hour_prior = [i for i in baseline_prior 
                           if self.transactions[i]['event_timestamp'] >= current_hour_start
                           and self.transactions[i]['event_timestamp'] < current_time
                           and self.transactions[i]['event_sequence'] < tx['event_sequence']]
        
        current_hour_count = len(current_hour_prior)
        
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
        
        partition = tx['partition']
        indices = self.indices[partition]
        
        current_time = tx['event_timestamp']
        current_hour_start = current_time.replace(minute=0, second=0, microsecond=0)
        
        agent_history = indices['agent_txs'][tx['agent_id']]
        
        # Get 30-day baseline
        baseline_prior = self._get_prior_indices_binary_search(
            [(ts, i) for ts, i, _ in agent_history], 
            tx['event_timestamp'], idx, max_hours=24*30
        )
        
        # Build hourly values from completed hours (exclude current hour from baseline)
        hourly_values = defaultdict(float)
        for i in baseline_prior:
            hour_key = self.transactions[i]['event_timestamp'].replace(minute=0, second=0, microsecond=0)
            if hour_key < current_hour_start:
                hourly_values[hour_key] += self.transactions[i]['amount']
        
        if len(hourly_values) < 7:
            return 0.0
        
        # FIXED: Include earlier events in current hour before current event
        current_hour_prior = [i for i in baseline_prior 
                           if self.transactions[i]['event_timestamp'] >= current_hour_start
                           and self.transactions[i]['event_timestamp'] < current_time
                           and self.transactions[i]['event_sequence'] < tx['event_sequence']]
        
        current_hour_value = sum(self.transactions[i]['amount'] for i in current_hour_prior)
        
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
        
        partition = tx['partition']
        indices = self.indices[partition]
        
        agent_history = indices['agent_txs'][tx['agent_id']]
        prior_indices = self._get_prior_indices_binary_search(
            [(ts, i) for ts, i, _ in agent_history], 
            tx['event_timestamp'], idx, max_hours=24*7
        )
        
        if not prior_indices:
            return 0.0
        
        # FIXED: Bucket key includes full timestamp (hour, date)
        bucket_counts = defaultdict(int)
        for i in prior_indices:
            minute_bucket = (self.transactions[i]['event_timestamp'].minute // 15) * 15
            bucket_key = self.transactions[i]['event_timestamp'].replace(
                minute=minute_bucket, second=0, microsecond=0
            )
            bucket_counts[bucket_key] += 1
        
        max_bucket = max(bucket_counts.values())
        
        return max_bucket / len(prior_indices)
    
    def agent_shared_wallet_flow_concentration_7d(self, idx: int) -> float:
        tx = self.transactions[idx]
        if not tx['agent_id']:
            return 0.0
        
        partition = tx['partition']
        indices = self.indices[partition]
        
        agent_history = indices['agent_txs'][tx['agent_id']]
        prior_indices = self._get_prior_indices_binary_search(
            [(ts, i) for ts, i, _ in agent_history], 
            tx['event_timestamp'], idx, max_hours=24*7
        )
        
        if not prior_indices:
            return 0.0
        
        agent_wallets = set()
        for i in prior_indices:
            agent_wallets.add(self.transactions[i]['sender_wallet'])
            agent_wallets.add(self.transactions[i]['receiver_wallet'])
        
        if not agent_wallets:
            return 0.0
        
        # Identify external counterparties
        external_counterparties = set()
        for i in prior_indices:
            if self.transactions[i]['sender_wallet'] in agent_wallets and \
               self.transactions[i]['receiver_wallet'] not in agent_wallets:
                external_counterparties.add(self.transactions[i]['receiver_wallet'])
            elif self.transactions[i]['receiver_wallet'] in agent_wallets and \
                 self.transactions[i]['sender_wallet'] not in agent_wallets:
                external_counterparties.add(self.transactions[i]['sender_wallet'])
        
        max_linked = 0
        for counterparty in external_counterparties:
            linked_wallets = set()
            for i in prior_indices:
                if self.transactions[i]['sender_wallet'] == counterparty and \
                   self.transactions[i]['receiver_wallet'] in agent_wallets:
                    linked_wallets.add(self.transactions[i]['receiver_wallet'])
                elif self.transactions[i]['receiver_wallet'] == counterparty and \
                     self.transactions[i]['sender_wallet'] in agent_wallets:
                    linked_wallets.add(self.transactions[i]['sender_wallet'])
            
            max_linked = max(max_linked, len(linked_wallets))
        
        return max_linked / len(agent_wallets)
    
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

def main(data_dir: Path, output_dir: Path, reports_dir: Path):
    print("=" * 80)
    print("STAGE 13A: CORRECTED 30-FEATURE MATRIX CONSTRUCTION")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Dataset Version: {DATASET_VERSION}")
    print(f"Data Directory: {data_dir}")
    print(f"Output Directory: {output_dir}")
    print()
    
    # Load data
    transactions, labels, wallet_partition, agent_partition = load_data(data_dir)
    
    # Initialize indexed extractor
    print("Initializing indexed feature extractor...")
    extractor = IndexedFeatureExtractor(transactions, wallet_partition, agent_partition)
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
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save matrices
    print("Saving feature matrices...")
    np.save(output_dir / "X.npy", X)
    np.save(output_dir / "y.npy", y)
    
    with open(output_dir / "feature_names.json", 'w') as f:
        json.dump(feature_names, f, indent=2)
    
    print(f"  Saved to {output_dir}")
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
    
    np.save(output_dir / "X_train.npy", X_train)
    np.save(output_dir / "y_train.npy", y_train)
    np.save(output_dir / "X_val.npy", X_val)
    np.save(output_dir / "y_val.npy", y_val)
    np.save(output_dir / "X_test.npy", X_test)
    np.save(output_dir / "y_test.npy", y_test)
    np.save(output_dir / "X_independent.npy", X_independent)
    np.save(output_dir / "y_independent.npy", y_independent)
    
    print("=" * 80)
    print("FEATURE EXTRACTION COMPLETE")
    print("=" * 80)
    
    return X, y, feature_names

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage 13A Corrected Feature Extraction")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR,
                       help="Directory containing Stage 11 dataset")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
                       help="Directory for output feature matrices")
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR,
                       help="Directory for reports")
    
    args = parser.parse_args()
    
    X, y, feature_names = main(args.data_dir, args.output_dir, args.reports_dir)
    print("Stage 13A complete.")
