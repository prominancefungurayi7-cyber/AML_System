"""
STAGE 5: 34-Feature Engineering Pipeline

Implements the approved 34-feature specification from Stage 4.
Ensures temporal safety - no future data leakage.
"""

import csv
import json
import math
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Dict, List, Any, Tuple
import statistics

print("=" * 80)
print("STAGE 5: 34-FEATURE ENGINEERING PIPELINE")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================================
# FEATURE DEFINITIONS AND DOCUMENTATION
# ============================================================================

"""
FEATURE DEFINITIONS (34 total)

CORE FEATURES (14) - from Stage 3 dataset:
1. amount (float) - Raw transaction amount
2. sender_avg_amount (float) - Customer's average transaction amount from history
3. sender_max_amount (float) - Customer's maximum transaction amount from history
4. sender_tx_count (float) - Total number of customer's past transactions
5. amount_to_sender_avg (float) - Current amount / sender_avg_amount
6. amount_to_sender_max (float) - Current amount / sender_max_amount
7. sender_tx_count_24h (float) - Number of transactions in last 24 hours
8. sender_volume_24h (float) - Total volume in last 24 hours
9. amount_to_sender_volume_24h (float) - Current amount / sender_volume_24h
10. is_new_recipient (float) - 1.0 if recipient not seen before, 0.0 otherwise
11. same_day_count (float) - Number of transactions on same day (before current)
12. same_day_total (float) - Total amount on same day (before current)
13. same_recipient_count (float) - Number of transactions to same recipient in 24h
14. rapid_transfer_count (float) - Number of transfers within 10 minutes

DERIVED FEATURES (7):
15. hour (int) - Hour of day (0-23) from timestamp
16. is_deposit (binary) - 1 if transaction_type == "deposit", else 0
17. is_withdraw (binary) - 1 if transaction_type == "withdraw", else 0
18. is_transfer (binary) - 1 if transaction_type == "transfer", else 0
19. is_self_transfer (binary) - 1 if sender_account == receiver_account, else 0
20. is_off_hours (binary) - 1 if hour < 5 or hour >= 23, else 0
21. channel_encoded (int) - Channel mapping: online=0, mobile=1, atm=2, branch=3, card=4, ach=5, wire=6, swift=7

NEW BEHAVIORAL FEATURES (13):
22. amount_std_dev (float) - Standard deviation of customer's transaction amounts
23. amount_z_score (float) - (amount - sender_avg_amount) / amount_std_dev (0 if std_dev=0)
24. tx_frequency_7d (float) - Number of transactions in last 7 days (rolling window)
25. tx_frequency_30d (float) - Number of transactions in last 30 days (rolling window)
26. day_of_week (int) - Day of week (0=Monday, 6=Sunday) from timestamp
27. is_weekend (binary) - 1 if day_of_week >= 5, else 0
28. time_since_last_tx (float) - Hours since previous transaction (0 if first)
29. unique_recipients_24h (float) - Number of unique recipients in last 24 hours
30. unique_recipients_7d (float) - Number of unique recipients in last 7 days
31. recipient_concentration (float) - Concentration of transactions to top recipient in 7d (0-1)
32. new_recipient_ratio_7d (float) - Ratio of new recipients in last 7 days
33. amount_change_vs_avg_7d (float) - Difference between current amount and 7-day average
34. frequency_change_vs_avg_7d (float) - Difference between current frequency and 7-day average

TEMPORAL SAFETY RULES:
- All historical features use ONLY transactions with timestamp < current transaction timestamp
- Rolling windows (24h, 7d, 30d) are calculated from current timestamp backwards
- Current transaction is NOT included in historical calculations
- If insufficient history exists, use safe default values (0 or neutral)
"""

# Channel encoding mapping
CHANNEL_ENCODING = {
    "online": 0,
    "mobile": 1,
    "atm": 2,
    "branch": 3,
    "card": 4,
    "ach": 5,
    "wire": 6,
    "swift": 7
}

# Safe default values for features when history is insufficient
SAFE_DEFAULTS = {
    "sender_avg_amount": 0.0,
    "sender_max_amount": 0.0,
    "sender_tx_count": 0.0,
    "amount_to_sender_avg": 1.0,
    "amount_to_sender_max": 1.0,
    "sender_tx_count_24h": 0.0,
    "sender_volume_24h": 0.0,
    "amount_to_sender_volume_24h": 1.0,
    "is_new_recipient": 1.0,
    "same_day_count": 0.0,
    "same_day_total": 0.0,
    "same_recipient_count": 0.0,
    "rapid_transfer_count": 0.0,
    "amount_std_dev": 0.0,
    "amount_z_score": 0.0,
    "tx_frequency_7d": 0.0,
    "tx_frequency_30d": 0.0,
    "time_since_last_tx": 0.0,
    "unique_recipients_24h": 0.0,
    "unique_recipients_7d": 0.0,
    "recipient_concentration": 0.0,
    "new_recipient_ratio_7d": 0.0,
    "amount_change_vs_avg_7d": 0.0,
    "frequency_change_vs_avg_7d": 0.0,
}


# ============================================================================
# FEATURE EXTRACTION CLASS
# ============================================================================

class FeatureExtractor:
    """Extracts 34 features from Stage 3 dataset with temporal safety."""
    
    def __init__(self):
        self.customer_history = defaultdict(list)  # sender_account -> list of past transactions
        self.customer_recipients = defaultdict(set)  # sender_account -> set of recipients seen
    
    def parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse ISO timestamp to datetime object."""
        try:
            dt = datetime.fromisoformat(timestamp_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            return datetime.now(timezone.utc)
    
    def get_historical_transactions(self, sender_account: str, current_timestamp: datetime) -> List[Dict]:
        """Get all transactions for sender before current timestamp (temporal safety)."""
        history = self.customer_history[sender_account]
        # Filter to only transactions before current timestamp
        past_transactions = [
            tx for tx in history 
            if self.parse_timestamp(tx["timestamp"]) < current_timestamp
        ]
        return past_transactions
    
    def compute_core_features(self, transaction: Dict, past_transactions: List[Dict]) -> Dict[str, float]:
        """Compute 14 core features from Stage 3 dataset."""
        current_amount = float(transaction["amount"])
        current_timestamp = self.parse_timestamp(transaction["timestamp"])
        sender_account = transaction["sender_account"]
        receiver_account = transaction["receiver_account"]
        
        if not past_transactions:
            # First transaction - use safe defaults
            return {
                "amount": current_amount,
                "sender_avg_amount": SAFE_DEFAULTS["sender_avg_amount"],
                "sender_max_amount": SAFE_DEFAULTS["sender_max_amount"],
                "sender_tx_count": SAFE_DEFAULTS["sender_tx_count"],
                "amount_to_sender_avg": SAFE_DEFAULTS["amount_to_sender_avg"],
                "amount_to_sender_max": SAFE_DEFAULTS["amount_to_sender_max"],
                "sender_tx_count_24h": SAFE_DEFAULTS["sender_tx_count_24h"],
                "sender_volume_24h": SAFE_DEFAULTS["sender_volume_24h"],
                "amount_to_sender_volume_24h": SAFE_DEFAULTS["amount_to_sender_volume_24h"],
                "is_new_recipient": 1.0,  # First transaction to this recipient
                "same_day_count": SAFE_DEFAULTS["same_day_count"],
                "same_day_total": SAFE_DEFAULTS["same_day_total"],
                "same_recipient_count": SAFE_DEFAULTS["same_recipient_count"],
                "rapid_transfer_count": SAFE_DEFAULTS["rapid_transfer_count"],
            }
        
        # Compute historical statistics
        amounts = [float(tx["amount"]) for tx in past_transactions]
        sender_avg_amount = sum(amounts) / len(amounts) if amounts else 0.0
        sender_max_amount = max(amounts) if amounts else 0.0
        sender_tx_count = len(past_transactions)
        
        # 24-hour window
        cutoff_24h = current_timestamp - timedelta(hours=24)
        recent_24h = [
            tx for tx in past_transactions
            if self.parse_timestamp(tx["timestamp"]) >= cutoff_24h
        ]
        sender_tx_count_24h = len(recent_24h)
        sender_volume_24h = sum(float(tx["amount"]) for tx in recent_24h)
        
        # Same day
        current_date = current_timestamp.date()
        same_day_txs = [
            tx for tx in past_transactions
            if self.parse_timestamp(tx["timestamp"]).date() == current_date
        ]
        same_day_count = len(same_day_txs)
        same_day_total = sum(float(tx["amount"]) for tx in same_day_txs)
        
        # Same recipient in 24h
        same_recipient_count = len([
            tx for tx in recent_24h
            if tx["receiver_account"] == receiver_account
        ])
        
        # Rapid transfers (within 10 minutes)
        cutoff_10min = current_timestamp - timedelta(minutes=10)
        rapid_transfer_count = len([
            tx for tx in past_transactions
            if self.parse_timestamp(tx["timestamp"]) >= cutoff_10min
        ])
        
        # Is new recipient
        is_new_recipient = 1.0 if receiver_account not in self.customer_recipients[sender_account] else 0.0
        
        # Compute ratios (handle division by zero)
        amount_to_sender_avg = current_amount / max(sender_avg_amount, 1.0)
        amount_to_sender_max = current_amount / max(sender_max_amount, 1.0)
        amount_to_sender_volume_24h = current_amount / max(sender_volume_24h, 1.0)
        
        return {
            "amount": current_amount,
            "sender_avg_amount": sender_avg_amount,
            "sender_max_amount": sender_max_amount,
            "sender_tx_count": float(sender_tx_count),
            "amount_to_sender_avg": amount_to_sender_avg,
            "amount_to_sender_max": amount_to_sender_max,
            "sender_tx_count_24h": float(sender_tx_count_24h),
            "sender_volume_24h": sender_volume_24h,
            "amount_to_sender_volume_24h": amount_to_sender_volume_24h,
            "is_new_recipient": is_new_recipient,
            "same_day_count": float(same_day_count),
            "same_day_total": same_day_total,
            "same_recipient_count": float(same_recipient_count),
            "rapid_transfer_count": float(rapid_transfer_count),
        }
    
    def compute_derived_features(self, transaction: Dict) -> Dict[str, Any]:
        """Compute 7 derived features."""
        timestamp = self.parse_timestamp(transaction["timestamp"])
        hour = timestamp.hour
        transaction_type = transaction["transaction_type"]
        sender_account = transaction["sender_account"]
        receiver_account = transaction["receiver_account"]
        channel = transaction["channel"].lower()
        
        return {
            "hour": hour,
            "is_deposit": 1 if transaction_type == "deposit" else 0,
            "is_withdraw": 1 if transaction_type == "withdraw" else 0,
            "is_transfer": 1 if transaction_type == "transfer" else 0,
            "is_self_transfer": 1 if sender_account == receiver_account else 0,
            "is_off_hours": 1 if hour < 5 or hour >= 23 else 0,
            "channel_encoded": CHANNEL_ENCODING.get(channel, 0),
        }
    
    def compute_behavioral_features(self, transaction: Dict, past_transactions: List[Dict]) -> Dict[str, float]:
        """Compute 13 new behavioral features."""
        current_amount = float(transaction["amount"])
        current_timestamp = self.parse_timestamp(transaction["timestamp"])
        sender_account = transaction["sender_account"]
        
        if not past_transactions:
            # First transaction - use safe defaults
            return {
                "amount_std_dev": SAFE_DEFAULTS["amount_std_dev"],
                "amount_z_score": SAFE_DEFAULTS["amount_z_score"],
                "tx_frequency_7d": SAFE_DEFAULTS["tx_frequency_7d"],
                "tx_frequency_30d": SAFE_DEFAULTS["tx_frequency_30d"],
                "day_of_week": current_timestamp.weekday(),
                "is_weekend": 1 if current_timestamp.weekday() >= 5 else 0,
                "time_since_last_tx": SAFE_DEFAULTS["time_since_last_tx"],
                "unique_recipients_24h": SAFE_DEFAULTS["unique_recipients_24h"],
                "unique_recipients_7d": SAFE_DEFAULTS["unique_recipients_7d"],
                "recipient_concentration": SAFE_DEFAULTS["recipient_concentration"],
                "new_recipient_ratio_7d": SAFE_DEFAULTS["new_recipient_ratio_7d"],
                "amount_change_vs_avg_7d": SAFE_DEFAULTS["amount_change_vs_avg_7d"],
                "frequency_change_vs_avg_7d": SAFE_DEFAULTS["frequency_change_vs_avg_7d"],
            }
        
        amounts = [float(tx["amount"]) for tx in past_transactions]
        sender_avg_amount = sum(amounts) / len(amounts) if amounts else 0.0
        
        # Amount standard deviation
        amount_std_dev = statistics.stdev(amounts) if len(amounts) > 1 else 0.0
        
        # Z-score (handle division by zero)
        amount_z_score = 0.0
        if amount_std_dev > 0:
            amount_z_score = (current_amount - sender_avg_amount) / amount_std_dev
        
        # Rolling windows
        cutoff_7d = current_timestamp - timedelta(days=7)
        cutoff_30d = current_timestamp - timedelta(days=30)
        
        tx_7d = [tx for tx in past_transactions if self.parse_timestamp(tx["timestamp"]) >= cutoff_7d]
        tx_30d = [tx for tx in past_transactions if self.parse_timestamp(tx["timestamp"]) >= cutoff_30d]
        
        tx_frequency_7d = len(tx_7d)
        tx_frequency_30d = len(tx_30d)
        
        # Temporal features
        day_of_week = current_timestamp.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0
        
        # Time since last transaction
        last_tx = past_transactions[-1]
        last_tx_time = self.parse_timestamp(last_tx["timestamp"])
        time_since_last_tx = (current_timestamp - last_tx_time).total_seconds() / 3600.0  # hours
        
        # Recipient diversity
        cutoff_24h = current_timestamp - timedelta(hours=24)
        recipients_24h = set(tx["receiver_account"] for tx in tx_7d if self.parse_timestamp(tx["timestamp"]) >= cutoff_24h)
        recipients_7d = set(tx["receiver_account"] for tx in tx_7d)
        
        unique_recipients_24h = len(recipients_24h)
        unique_recipients_7d = len(recipients_7d)
        
        # Recipient concentration (proportion to top recipient in 7d)
        recipient_concentration = 0.0
        if tx_7d:
            recipient_counts = defaultdict(int)
            for tx in tx_7d:
                recipient_counts[tx["receiver_account"]] += 1
            if recipient_counts:
                max_count = max(recipient_counts.values())
                recipient_concentration = max_count / len(tx_7d)
        
        # New recipient ratio in 7d
        new_recipient_ratio_7d = 0.0
        if tx_7d:
            new_recipients = sum(
                1 for tx in tx_7d
                if tx["receiver_account"] not in self.customer_recipients[sender_account]
            )
            new_recipient_ratio_7d = new_recipients / len(tx_7d)
        
        # Behavioral change: amount vs 7-day average
        avg_7d = sum(float(tx["amount"]) for tx in tx_7d) / len(tx_7d) if tx_7d else sender_avg_amount
        amount_change_vs_avg_7d = current_amount - avg_7d
        
        # Behavioral change: frequency vs 7-day average
        # Calculate average daily frequency over past 30 days, then compare to 7-day frequency
        avg_daily_freq_30d = len(tx_30d) / 30.0 if tx_30d else 0.0
        avg_daily_freq_7d = len(tx_7d) / 7.0 if tx_7d else 0.0
        frequency_change_vs_avg_7d = avg_daily_freq_7d - avg_daily_freq_30d
        
        return {
            "amount_std_dev": amount_std_dev,
            "amount_z_score": amount_z_score,
            "tx_frequency_7d": float(tx_frequency_7d),
            "tx_frequency_30d": float(tx_frequency_30d),
            "day_of_week": day_of_week,
            "is_weekend": is_weekend,
            "time_since_last_tx": time_since_last_tx,
            "unique_recipients_24h": float(unique_recipients_24h),
            "unique_recipients_7d": float(unique_recipients_7d),
            "recipient_concentration": recipient_concentration,
            "new_recipient_ratio_7d": new_recipient_ratio_7d,
            "amount_change_vs_avg_7d": amount_change_vs_avg_7d,
            "frequency_change_vs_avg_7d": frequency_change_vs_avg_7d,
        }
    
    def extract_features(self, transaction: Dict) -> Dict[str, Any]:
        """Extract all 34 features for a single transaction."""
        sender_account = transaction["sender_account"]
        current_timestamp = self.parse_timestamp(transaction["timestamp"])
        
        # Get historical transactions (temporal safety: only past transactions)
        past_transactions = self.get_historical_transactions(sender_account, current_timestamp)
        
        # Compute feature groups
        core_features = self.compute_core_features(transaction, past_transactions)
        derived_features = self.compute_derived_features(transaction)
        behavioral_features = self.compute_behavioral_features(transaction, past_transactions)
        
        # Combine all features
        all_features = {**core_features, **derived_features, **behavioral_features}
        
        # Update customer history for future transactions (after computing features)
        self.customer_history[sender_account].append(transaction)
        self.customer_recipients[sender_account].add(transaction["receiver_account"])
        
        return all_features


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def load_stage3_dataset(csv_path: str) -> List[Dict]:
    """Load Stage 3 dataset from CSV."""
    transactions = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            transactions.append(row)
    return transactions

def process_dataset(transactions: List[Dict]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Process all transactions and extract 34 features."""
    # Sort transactions by timestamp to ensure temporal safety
    transactions_sorted = sorted(transactions, key=lambda tx: tx["timestamp"])
    
    extractor = FeatureExtractor()
    feature_vectors = []
    
    for transaction in transactions_sorted:
        features = extractor.extract_features(transaction)
        feature_vectors.append(features)
    
    # Get feature names from first transaction
    feature_names = list(feature_vectors[0].keys()) if feature_vectors else []
    
    return feature_vectors, feature_names

def export_features(feature_vectors: List[Dict[str, Any]], feature_names: List[str], output_path: str):
    """Export feature vectors to CSV."""
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=feature_names)
        writer.writeheader()
        for features in feature_vectors:
            writer.writerow(features)

def main():
    print("Loading Stage 3 dataset...")
    transactions = load_stage3_dataset("ml_stage3_dataset.csv")
    print(f"Loaded {len(transactions)} transactions")
    print()
    
    print("Processing transactions and extracting 34 features...")
    feature_vectors, feature_names = process_dataset(transactions)
    print(f"Extracted {len(feature_names)} features per transaction")
    print(f"Feature names: {feature_names}")
    print()
    
    print("Exporting features...")
    export_features(feature_vectors, feature_names, "ml_stage5_features.csv")
    print("Features exported to ml_stage5_features.csv")
    print()
    
    print("=" * 80)
    print("FEATURE EXTRACTION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
