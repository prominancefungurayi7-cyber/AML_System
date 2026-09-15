"""
ai_stage13_features.py — Stage 13 Feature Service for Live EcoCash Application

This module implements the authoritative Stage 13 30-feature extraction adapted
for the live MySQL database schema.

Based on authoritative implementation in ml_stage13_extract_features.py

CRITICAL:
- NO model training
- NO feature addition/removal
- STRICT temporal safety using (timestamp, id) ordering
- EXACT Stage 13 formula compliance
- Current transaction excluded from history
- Future transactions excluded
"""

import math
import statistics
from datetime import datetime, timedelta, timezone
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Stage 10C synthetic reporting threshold
SYNTHETIC_REPORTING_THRESHOLD = 10000


class Stage13FeatureService:
    """
    Live Stage 13 feature service adapted for MySQL database schema.
    
    Uses existing database structure:
    - transactions.id as event_sequence (auto-incrementing, monotonic)
    - transactions.sender_account as sender_wallet
    - transactions.receiver_account as receiver_wallet
    - transactions.agent_id for agent relationship
    - transactions.timestamp for temporal ordering
    """
    
    def __init__(self, db_adapter):
        """
        Initialize feature service with database adapter.
        
        Args:
            db_adapter: DatabaseAdapter instance for MySQL queries
        """
        self.db = db_adapter
        
        # Cache for transaction history to optimize repeated queries
        self._history_cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    def _get_prior_transactions(self, current_tx: Dict, window_hours: float = None) -> List[Dict]:
        """
        Get prior transactions for current transaction respecting temporal rules.
        
        Temporal contract: (timestamp, id) < (current_timestamp, current_id)
        
        Args:
            current_tx: Current transaction dict with id, timestamp, sender_account, receiver_account
            window_hours: Optional time window in hours
            
        Returns:
            List of prior transaction dicts
        """
        current_id = current_tx['id']
        current_timestamp = current_tx['timestamp']
        
        # Parse timestamp
        try:
            current_time = datetime.fromisoformat(current_timestamp.replace('Z', '+00:00'))
        except:
            logger.error(f"Invalid timestamp format: {current_timestamp}")
            return []
        
        # Build query with temporal constraints
        # Use ? placeholders for SQLite compatibility
        if window_hours:
            time_limit = current_time - timedelta(hours=window_hours)
            query = """
                SELECT id, sender_account, receiver_account, amount, 
                       timestamp, transaction_type, agent_id
                FROM transactions
                WHERE (timestamp < ? OR (timestamp = ? AND id < ?))
                  AND timestamp >= ?
                ORDER BY timestamp, id
            """
            params = (current_timestamp, current_timestamp, current_id, time_limit.isoformat())
        else:
            query = """
                SELECT id, sender_account, receiver_account, amount, 
                       timestamp, transaction_type, agent_id
                FROM transactions
                WHERE (timestamp < ? OR (timestamp = ? AND id < ?))
                ORDER BY timestamp, id
            """
            params = (current_timestamp, current_timestamp, current_id)
        
        cursor = self.db.execute(query, params)
        prior_txs = []
        for row in cursor:
            # Handle both dict-like and tuple-like cursor results
            if hasattr(row, 'keys'):
                # sqlite3.Row or dict-like cursor
                prior_txs.append({
                    'id': row['id'],
                    'sender_account': row['sender_account'],
                    'receiver_account': row['receiver_account'],
                    'amount': row['amount'],
                    'timestamp': row['timestamp'],
                    'transaction_type': row['transaction_type'],
                    'agent_id': row['agent_id']
                })
            else:
                # Tuple-like cursor, use positional indexing
                prior_txs.append({
                    'id': row[0],
                    'sender_account': row[1],
                    'receiver_account': row[2],
                    'amount': row[3],
                    'timestamp': row[4],
                    'transaction_type': row[5],
                    'agent_id': row[6]
                })
        
        return prior_txs
    
    def generate_features(self, current_tx: Dict) -> List[float]:
        """
        Generate exactly 30 Stage 13 features for the current transaction.
        
        Args:
            current_tx: Current transaction dict with required fields
            
        Returns:
            List of 30 float features in frozen order
        """
        try:
            features = []
            
            # Structuring Features (6)
            features.append(self._structuring_prior_tx_count_1h(current_tx))
            features.append(self._structuring_prior_value_sum_24h(current_tx))
            features.append(self._structuring_same_day_prior_tx_count(current_tx))
            features.append(self._structuring_repeated_amount_ratio_7d(current_tx))
            features.append(self._structuring_amount_cluster_dispersion_7d(current_tx))
            features.append(self._structuring_near_threshold_history_ratio_7d(current_tx))
            
            # Network Features (10)
            features.append(self._network_outbound_counterparty_count_7d(current_tx))
            features.append(self._network_inbound_counterparty_count_7d(current_tx))
            features.append(self._network_outbound_counterparty_entropy_30d(current_tx))
            features.append(self._network_top_counterparty_value_share_30d(current_tx))
            features.append(self._network_current_receiver_is_new(current_tx))
            features.append(self._network_repeated_receiver_ratio_30d(current_tx))
            features.append(self._network_reciprocal_flow_ratio_7d(current_tx))
            features.append(self._network_counterparty_set_change_7d(current_tx))
            features.append(self._network_pass_through_ratio_24h(current_tx))
            features.append(self._network_shared_counterparty_concentration_7d(current_tx))
            
            # Agent Features (14)
            features.append(self._agent_prior_tx_count_1h(current_tx))
            features.append(self._agent_prior_tx_count_7d(current_tx))
            features.append(self._agent_prior_value_sum_1h(current_tx))
            features.append(self._agent_prior_value_sum_7d(current_tx))
            features.append(self._agent_unique_wallet_count_7d(current_tx))
            features.append(self._agent_wallet_value_hhi_7d(current_tx))
            features.append(self._agent_repeat_wallet_ratio_7d(current_tx))
            features.append(self._agent_current_wallet_is_new(current_tx))
            features.append(self._agent_inbound_outbound_value_ratio_7d(current_tx))
            features.append(self._agent_high_value_event_share_7d(current_tx))
            features.append(self._agent_hourly_tx_zscore_30d(current_tx))
            features.append(self._agent_hourly_value_zscore_30d(current_tx))
            features.append(self._agent_burst_concentration_7d(current_tx))
            features.append(self._agent_shared_wallet_flow_concentration_7d(current_tx))
            
            # Validate all features are finite and convert to float
            for i, f in enumerate(features):
                if not isinstance(f, (int, float)) or math.isnan(f) or math.isinf(f):
                    logger.error(f"Invalid feature at index {i}: {f}")
                    features[i] = 0.0
                else:
                    features[i] = float(f)  # Ensure all are floats
            
            return features
            
        except Exception as e:
            logger.error(f"Error generating features: {e}")
            # Return neutral defaults on error
            return [0.0] * 30
    
    # ========================================
    # STRUCTURING FEATURES (6)
    # ========================================
    
    def _structuring_prior_tx_count_1h(self, tx: Dict) -> float:
        """Count sender's earlier outgoing transactions within 1 hour."""
        prior = self._get_prior_transactions(tx, window_hours=1)
        sender_prior = [p for p in prior if p['sender_account'] == tx['sender_account']]
        return float(len(sender_prior))
    
    def _structuring_prior_value_sum_24h(self, tx: Dict) -> float:
        """Sum sender's earlier outgoing transaction values within 24 hours."""
        prior = self._get_prior_transactions(tx, window_hours=24)
        sender_prior = [p for p in prior if p['sender_account'] == tx['sender_account']]
        return float(sum(p['amount'] for p in sender_prior))
    
    def _structuring_same_day_prior_tx_count(self, tx: Dict) -> float:
        """Count sender's earlier transactions on the same calendar day."""
        try:
            current_time = datetime.fromisoformat(tx['timestamp'].replace('Z', '+00:00'))
            current_date = current_time.date()
        except:
            return 0.0
        
        prior = self._get_prior_transactions(tx)
        sender_prior = [p for p in prior if p['sender_account'] == tx['sender_account']]
        
        same_day_count = 0
        for p in sender_prior:
            try:
                p_time = datetime.fromisoformat(p['timestamp'].replace('Z', '+00:00'))
                if p_time.date() == current_date:
                    same_day_count += 1
            except:
                continue
        
        return float(same_day_count)
    
    def _structuring_repeated_amount_ratio_7d(self, tx: Dict) -> float:
        """Share of prior amounts within 5% of current amount in 7 days."""
        prior = self._get_prior_transactions(tx, window_hours=24*7)
        sender_prior = [p for p in prior if p['sender_account'] == tx['sender_account']]
        
        if not sender_prior:
            return 0.0
        
        current_amount = tx['amount']
        threshold = 0.05 * max(current_amount, 1)
        
        matching = sum(1 for p in sender_prior 
                     if abs(p['amount'] - current_amount) <= threshold)
        
        return matching / len(sender_prior)
    
    def _structuring_amount_cluster_dispersion_7d(self, tx: Dict) -> float:
        """Relative dispersion (std/mean) of prior amounts in 7 days."""
        prior = self._get_prior_transactions(tx, window_hours=24*7)
        sender_prior = [p for p in prior if p['sender_account'] == tx['sender_account']]
        
        if len(sender_prior) < 2:
            return 0.0
        
        amounts = [p['amount'] for p in sender_prior]
        mean_amt = sum(amounts) / len(amounts)
        
        if mean_amt == 0:
            return 0.0
        
        variance = sum((a - mean_amt) ** 2 for a in amounts) / len(amounts)
        std = math.sqrt(variance)
        
        return std / mean_amt
    
    def _structuring_near_threshold_history_ratio_7d(self, tx: Dict) -> float:
        """Share of prior amounts in [9000, 10000) range in 7 days."""
        prior = self._get_prior_transactions(tx, window_hours=24*7)
        sender_prior = [p for p in prior if p['sender_account'] == tx['sender_account']]
        
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
    
    def _network_outbound_counterparty_count_7d(self, tx: Dict) -> float:
        """Distinct receivers paid by sender in 7 days."""
        prior = self._get_prior_transactions(tx, window_hours=24*7)
        sender_prior = [p for p in prior if p['sender_account'] == tx['sender_account']]
        receivers = set(p['receiver_account'] for p in sender_prior)
        return float(len(receivers))
    
    def _network_inbound_counterparty_count_7d(self, tx: Dict) -> float:
        """Distinct senders that paid receiver in 7 days."""
        prior = self._get_prior_transactions(tx, window_hours=24*7)
        receiver_prior = [p for p in prior if p['receiver_account'] == tx['receiver_account']]
        senders = set(p['sender_account'] for p in receiver_prior)
        return float(len(senders))
    
    def _network_outbound_counterparty_entropy_30d(self, tx: Dict) -> float:
        """Entropy of sender's prior outbound receiver distribution in 30 days."""
        prior = self._get_prior_transactions(tx, window_hours=24*30)
        sender_prior = [p for p in prior if p['sender_account'] == tx['sender_account']]
        
        if not sender_prior:
            return 0.0
        
        # Group by receiver
        receiver_values = defaultdict(float)
        total_value = 0.0
        for p in sender_prior:
            receiver_values[p['receiver_account']] += p['amount']
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
    
    def _network_top_counterparty_value_share_30d(self, tx: Dict) -> float:
        """Largest receiver's share of sender's prior outbound value in 30 days."""
        prior = self._get_prior_transactions(tx, window_hours=24*30)
        sender_prior = [p for p in prior if p['sender_account'] == tx['sender_account']]
        
        if not sender_prior:
            return 0.0
        
        # Group by receiver
        receiver_values = defaultdict(float)
        total_value = 0.0
        for p in sender_prior:
            receiver_values[p['receiver_account']] += p['amount']
            total_value += p['amount']
        
        if total_value == 0:
            return 0.0
        
        max_value = max(receiver_values.values())
        return max_value / total_value
    
    def _network_current_receiver_is_new(self, tx: Dict) -> float:
        """1 if current receiver absent from sender's prior outbound history."""
        prior = self._get_prior_transactions(tx)
        sender_prior = [p for p in prior if p['sender_account'] == tx['sender_account']]
        prior_receivers = set(p['receiver_account'] for p in sender_prior)
        
        return 1.0 if tx['receiver_account'] not in prior_receivers else 0.0
    
    def _network_repeated_receiver_ratio_30d(self, tx: Dict) -> float:
        """Share of prior outbound to receivers seen at least twice in 30 days."""
        prior = self._get_prior_transactions(tx, window_hours=24*30)
        sender_prior = [p for p in prior if p['sender_account'] == tx['sender_account']]
        
        if not sender_prior:
            return 0.0
        
        # Count receiver frequencies
        receiver_freq = Counter(p['receiver_account'] for p in sender_prior)
        repeated_receivers = {r for r, c in receiver_freq.items() if c >= 2}
        
        repeated_count = sum(1 for p in sender_prior if p['receiver_account'] in repeated_receivers)
        
        return repeated_count / len(sender_prior)
    
    def _network_reciprocal_flow_ratio_7d(self, tx: Dict) -> float:
        """Share of counterparties with both inbound and outbound flows in 7 days."""
        prior = self._get_prior_transactions(tx, window_hours=24*7)
        
        # Get outbound counterparties
        outbound_counterparties = set(p['receiver_account'] for p in prior 
                                     if p['sender_account'] == tx['sender_account'])
        
        # Get inbound counterparties
        inbound_counterparties = set(p['sender_account'] for p in prior 
                                     if p['receiver_account'] == tx['receiver_account'])
        
        # Active counterparties
        active_counterparties = outbound_counterparties | inbound_counterparties
        
        if not active_counterparties:
            return 0.0
        
        # Counterparties with both directions
        reciprocal = outbound_counterparties & inbound_counterparties
        
        return len(reciprocal) / len(active_counterparties)
    
    def _network_counterparty_set_change_7d(self, tx: Dict) -> float:
        """1 - Jaccard similarity between two prior 7-day receiver sets."""
        try:
            current_time = datetime.fromisoformat(tx['timestamp'].replace('Z', '+00:00'))
        except:
            return 0.0
        
        # Recent 7-day window (t-7d to t)
        recent_start = current_time - timedelta(days=7)
        query_recent = """
            SELECT receiver_account
            FROM transactions
            WHERE sender_account = ?
              AND (timestamp < ? OR (timestamp = ? AND id < ?))
              AND timestamp >= ?
            ORDER BY timestamp, id
        """
        cursor_recent = self.db.execute(query_recent, (
            tx['sender_account'], tx['timestamp'], tx['timestamp'], tx['id'], recent_start.isoformat()
        ))
        recent_receivers = set()
        for row in cursor_recent:
            if hasattr(row, 'keys'):
                recent_receivers.add(row['receiver_account'])
            else:
                recent_receivers.add(row[0])
        
        # Prior 7-day window (t-14d to t-7d)
        prior_start = current_time - timedelta(days=14)
        prior_end = current_time - timedelta(days=7)
        query_prior = """
            SELECT receiver_account
            FROM transactions
            WHERE sender_account = ?
              AND (timestamp < ? OR (timestamp = ? AND id < ?))
              AND timestamp >= ?
              AND timestamp < ?
            ORDER BY timestamp, id
        """
        cursor_prior = self.db.execute(query_prior, (
            tx['sender_account'], tx['timestamp'], tx['timestamp'], tx['id'], 
            prior_start.isoformat(), prior_end.isoformat()
        ))
        prior_receivers = set()
        for row in cursor_prior:
            if hasattr(row, 'keys'):
                prior_receivers.add(row['receiver_account'])
            else:
                prior_receivers.add(row[0])
        
        if not recent_receivers and not prior_receivers:
            return 0.0
        
        # Jaccard similarity
        intersection = len(recent_receivers & prior_receivers)
        union = len(recent_receivers | prior_receivers)
        
        if union == 0:
            return 0.0
        
        jaccard = intersection / union
        return 1.0 - jaccard
    
    def _network_pass_through_ratio_24h(self, tx: Dict) -> float:
        """Prior outbound value / prior inbound value in 24 hours."""
        prior = self._get_prior_transactions(tx, window_hours=24)
        
        outbound_value = sum(p['amount'] for p in prior if p['sender_account'] == tx['sender_account'])
        inbound_value = sum(p['amount'] for p in prior if p['receiver_account'] == tx['sender_account'])
        
        if inbound_value == 0:
            return 0.0
        
        return outbound_value / inbound_value
    
    def _network_shared_counterparty_concentration_7d(self, tx: Dict) -> float:
        """Maximum second-order shared-neighbour share in 7 days."""
        prior = self._get_prior_transactions(tx, window_hours=24*7)
        
        # Build sender's counterparty set
        sender_counterparties = set()
        for p in prior:
            if p['sender_account'] == tx['sender_account']:
                sender_counterparties.add(p['receiver_account'])
            elif p['receiver_account'] == tx['sender_account']:
                sender_counterparties.add(p['sender_account'])
        
        if not sender_counterparties:
            return 0.0
        
        # For each counterparty, count shared neighbours
        max_shared = 0
        for counterparty in sender_counterparties:
            # Build counterparty's neighbour set
            counterparty_neighbours = set()
            for p in prior:
                if p['sender_account'] == counterparty:
                    counterparty_neighbours.add(p['receiver_account'])
                elif p['receiver_account'] == counterparty:
                    counterparty_neighbours.add(p['sender_account'])
            
            # Count shared
            shared = len(sender_counterparties & counterparty_neighbours)
            max_shared = max(max_shared, shared)
        
        return max_shared / max(len(sender_counterparties), 1)
    
    # ========================================
    # AGENT FEATURES (14)
    # ========================================
    
    def _agent_prior_tx_count_1h(self, tx: Dict) -> float:
        """Earlier agent-attributed transactions in 1 hour."""
        if not tx.get('agent_id'):
            return 0.0
        
        prior = self._get_prior_transactions(tx, window_hours=1)
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        return float(len(agent_prior))
    
    def _agent_prior_tx_count_7d(self, tx: Dict) -> float:
        """Earlier agent-attributed transactions in 7 days."""
        if not tx.get('agent_id'):
            return 0.0
        
        prior = self._get_prior_transactions(tx, window_hours=24*7)
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        return float(len(agent_prior))
    
    def _agent_prior_value_sum_1h(self, tx: Dict) -> float:
        """Earlier agent-attributed value in 1 hour."""
        if not tx.get('agent_id'):
            return 0.0
        
        prior = self._get_prior_transactions(tx, window_hours=1)
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        return sum(p['amount'] for p in agent_prior)
    
    def _agent_prior_value_sum_7d(self, tx: Dict) -> float:
        """Earlier agent-attributed value in 7 days."""
        if not tx.get('agent_id'):
            return 0.0
        
        prior = self._get_prior_transactions(tx, window_hours=24*7)
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        return sum(p['amount'] for p in agent_prior)
    
    def _agent_unique_wallet_count_7d(self, tx: Dict) -> float:
        """Distinct wallets associated with agent in 7 days."""
        if not tx.get('agent_id'):
            return 0.0
        
        prior = self._get_prior_transactions(tx, window_hours=24*7)
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        wallets = set()
        for p in agent_prior:
            wallets.add(p['sender_account'])
            wallets.add(p['receiver_account'])
        
        return float(len(wallets))
    
    def _agent_wallet_value_hhi_7d(self, tx: Dict) -> float:
        """Wallet value concentration at agent in 7 days (HHI)."""
        if not tx.get('agent_id'):
            return 0.0
        
        prior = self._get_prior_transactions(tx, window_hours=24*7)
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        if not agent_prior:
            return 0.0
        
        # Calculate wallet shares
        wallet_values = defaultdict(float)
        total_value = 0.0
        for p in agent_prior:
            wallet_values[p['sender_account']] += p['amount']
            total_value += p['amount']
        
        if total_value == 0:
            return 0.0
        
        # Calculate HHI
        hhi = 0.0
        for value in wallet_values.values():
            share = value / total_value
            hhi += share ** 2
        
        return hhi
    
    def _agent_repeat_wallet_ratio_7d(self, tx: Dict) -> float:
        """Ratio of repeated wallets for agent in 7 days."""
        if not tx.get('agent_id'):
            return 0.0
        
        prior = self._get_prior_transactions(tx, window_hours=24*7)
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        if not agent_prior:
            return 0.0
        
        # Count wallet frequencies
        wallet_freq = Counter()
        for p in agent_prior:
            wallet_freq[p['sender_account']] += 1
            wallet_freq[p['receiver_account']] += 1
        
        repeated_wallets = {w for w, c in wallet_freq.items() if c >= 2}
        
        repeated_count = 0
        for p in agent_prior:
            if p['sender_account'] in repeated_wallets:
                repeated_count += 1
            if p['receiver_account'] in repeated_wallets:
                repeated_count += 1
        
        return repeated_count / (2 * len(agent_prior))
    
    def _agent_current_wallet_is_new(self, tx: Dict) -> float:
        """1 if wallet never seen before by agent."""
        if not tx.get('agent_id'):
            return 0.0
        
        prior = self._get_prior_transactions(tx)
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        prior_wallets = set()
        for p in agent_prior:
            prior_wallets.add(p['sender_account'])
            prior_wallets.add(p['receiver_account'])
        
        current_wallet = tx['sender_account']
        return 1.0 if current_wallet not in prior_wallets else 0.0
    
    def _agent_inbound_outbound_value_ratio_7d(self, tx: Dict) -> float:
        """Inbound/outbound value ratio for agent in 7 days."""
        if not tx.get('agent_id'):
            return 0.0
        
        prior = self._get_prior_transactions(tx, window_hours=24*7)
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        if not agent_prior:
            return 0.0
        
        # Calculate inbound vs outbound
        inbound_value = 0.0
        outbound_value = 0.0
        for p in agent_prior:
            if p['receiver_account'] == tx['sender_account']:  # Inbound to current wallet
                inbound_value += p['amount']
            else:
                outbound_value += p['amount']
        
        if outbound_value == 0:
            return 0.0
        
        return inbound_value / outbound_value
    
    def _agent_high_value_event_share_7d(self, tx: Dict) -> float:
        """Share of agent transactions ≥$5000 in 7 days."""
        if not tx.get('agent_id'):
            return 0.0
        
        prior = self._get_prior_transactions(tx, window_hours=24*7)
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        if not agent_prior:
            return 0.0
        
        high_value_count = sum(1 for p in agent_prior if p['amount'] >= 5000)
        
        return high_value_count / len(agent_prior)
    
    def _agent_hourly_tx_zscore_30d(self, tx: Dict) -> float:
        """Z-score of hourly transaction count in 30 days."""
        if not tx.get('agent_id'):
            return 0.0
        
        prior = self._get_prior_transactions(tx, window_hours=24*30)
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        if len(agent_prior) < 2:
            return 0.0
        
        # Calculate hourly counts
        hourly_counts = defaultdict(int)
        for p in agent_prior:
            try:
                p_time = datetime.fromisoformat(p['timestamp'].replace('Z', '+00:00'))
                hour_key = p_time.hour
                hourly_counts[hour_key] += 1
            except:
                continue
        
        if not hourly_counts:
            return 0.0
        
        counts = list(hourly_counts.values())
        mean_count = statistics.mean(counts)
        std_count = statistics.stdev(counts) if len(counts) > 1 else 0
        
        if std_count == 0:
            return 0.0
        
        try:
            current_time = datetime.fromisoformat(tx['timestamp'].replace('Z', '+00:00'))
            current_hour_count = hourly_counts.get(current_time.hour, 0)
            return (current_hour_count - mean_count) / std_count
        except:
            return 0.0
    
    def _agent_hourly_value_zscore_30d(self, tx: Dict) -> float:
        """Z-score of hourly value in 30 days."""
        if not tx.get('agent_id'):
            return 0.0
        
        prior = self._get_prior_transactions(tx, window_hours=24*30)
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        if len(agent_prior) < 2:
            return 0.0
        
        # Calculate hourly values
        hourly_values = defaultdict(float)
        for p in agent_prior:
            try:
                p_time = datetime.fromisoformat(p['timestamp'].replace('Z', '+00:00'))
                hour_key = p_time.hour
                hourly_values[hour_key] += p['amount']
            except:
                continue
        
        if not hourly_values:
            return 0.0
        
        values = list(hourly_values.values())
        mean_value = statistics.mean(values)
        std_value = statistics.stdev(values) if len(values) > 1 else 0
        
        if std_value == 0:
            return 0.0
        
        try:
            current_time = datetime.fromisoformat(tx['timestamp'].replace('Z', '+00:00'))
            current_hour_value = hourly_values.get(current_time.hour, 0)
            return (current_hour_value - mean_value) / std_value
        except:
            return 0.0
    
    def _agent_burst_concentration_7d(self, tx: Dict) -> float:
        """Burst concentration metric for agent in 7 days."""
        if not tx.get('agent_id'):
            return 0.0
        
        prior = self._get_prior_transactions(tx, window_hours=24*7)
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        if len(agent_prior) < 2:
            return 0.0
        
        # Calculate time gaps
        timestamps = []
        for p in agent_prior:
            try:
                p_time = datetime.fromisoformat(p['timestamp'].replace('Z', '+00:00'))
                timestamps.append(p_time)
            except:
                continue
        
        if len(timestamps) < 2:
            return 0.0
        
        timestamps.sort()
        gaps = []
        for i in range(1, len(timestamps)):
            gap = (timestamps[i] - timestamps[i-1]).total_seconds()
            gaps.append(gap)
        
        if not gaps:
            return 0.0
        
        # Concentration = proportion of gaps < 1 hour
        short_gaps = sum(1 for g in gaps if g < 3600)
        return short_gaps / len(gaps)
    
    def _agent_shared_wallet_flow_concentration_7d(self, tx: Dict) -> float:
        """Shared wallet flow concentration for agent in 7 days."""
        if not tx.get('agent_id'):
            return 0.0
        
        prior = self._get_prior_transactions(tx, window_hours=24*7)
        agent_prior = [p for p in prior if p['agent_id'] == tx['agent_id']]
        
        if not agent_prior:
            return 0.0
        
        # Calculate wallet value shares
        wallet_values = defaultdict(float)
        total_value = 0.0
        for p in agent_prior:
            wallet_values[p['sender_account']] += p['amount']
            total_value += p['amount']
        
        if total_value == 0:
            return 0.0
        
        # Calculate concentration (max share)
        max_share = max(wallet_values.values()) / total_value
        return max_share


# Feature names in frozen order
FEATURE_NAMES = [
    "structuring_prior_tx_count_1h",
    "structuring_prior_value_sum_24h",
    "structuring_same_day_prior_tx_count",
    "structuring_repeated_amount_ratio_7d",
    "structuring_amount_cluster_dispersion_7d",
    "structuring_near_threshold_history_ratio_7d",
    
    "network_outbound_counterparty_count_7d",
    "network_inbound_counterparty_count_7d",
    "network_outbound_counterparty_entropy_30d",
    "network_top_counterparty_value_share_30d",
    "network_current_receiver_is_new",
    "network_repeated_receiver_ratio_30d",
    "network_reciprocal_flow_ratio_7d",
    "network_counterparty_set_change_7d",
    "network_pass_through_ratio_24h",
    "network_shared_counterparty_concentration_7d",
    
    "agent_prior_tx_count_1h",
    "agent_prior_tx_count_7d",
    "agent_prior_value_sum_1h",
    "agent_prior_value_sum_7d",
    "agent_unique_wallet_count_7d",
    "agent_wallet_value_hhi_7d",
    "agent_repeat_wallet_ratio_7d",
    "agent_current_wallet_is_new",
    "agent_inbound_outbound_value_ratio_7d",
    "agent_high_value_event_share_7d",
    "agent_hourly_tx_zscore_30d",
    "agent_hourly_value_zscore_30d",
    "agent_burst_concentration_7d",
    "agent_shared_wallet_flow_concentration_7d"
]
