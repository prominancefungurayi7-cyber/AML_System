"""
STAGE 15B: FEATURE IMPLEMENTATION

Implement the 57-feature specification (32 existing + 25 new).
Remove is_self_transfer (constant 0.0).
"""

import csv
import json
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Any

print("=" * 80)
print("STAGE 15B: FEATURE IMPLEMENTATION")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================================
# LOAD STAGE 11 DATASET
# ============================================================================

print("Loading Stage 11 dataset...")
transactions = []
with open('ml_stage11_dataset.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        transactions.append(row)

print(f"Loaded {len(transactions)} transactions")
print()

# ============================================================================
# LOAD STAGE 11 GROUND TRUTH
# ============================================================================

print("Loading Stage 11 ground truth...")
with open('ml_stage11_ground_truth.json', 'r') as f:
    ground_truth = json.load(f)

print(f"Loaded ground truth for {len(ground_truth)} transactions")
print()

# ============================================================================
# PARSE TIMESTAMPS AND SORT BY CUSTOMER
# ============================================================================

print("Parsing timestamps and sorting by customer...")

for tx in transactions:
    tx['timestamp'] = datetime.fromisoformat(tx['timestamp'].replace('Z', '+00:00'))

# Group by customer
customer_transactions = defaultdict(list)
for tx in transactions:
    customer_transactions[tx['sender_account']].append(tx)

# Sort each customer's transactions by timestamp
for customer in customer_transactions:
    customer_transactions[customer].sort(key=lambda x: x['timestamp'])

print(f"Processed {len(customer_transactions)} customers")
print()

# ============================================================================
# FEATURE IMPLEMENTATION
# ============================================================================

print("Implementing 57 features...")

def compute_features_for_transaction(tx: Dict[str, Any], historical: List[Dict[str, Any]]) -> Dict[str, float]:
    """Compute all 57 features for a single transaction."""
    
    features = {}
    
    # Get current transaction info
    current_time = tx['timestamp']
    current_amount = float(tx['amount'])
    tx_time = current_time
    tx_type = tx['transaction_type']
    
    # Filter historical transactions by time windows
    hist_7d = [h for h in historical if (current_time - h['timestamp']).days < 7]
    hist_30d = [h for h in historical if (current_time - h['timestamp']).days < 30]
    hist_14d = [h for h in historical if (current_time - h['timestamp']).days < 14]
    hist_24h = [h for h in historical if (current_time - h['timestamp']).total_seconds() < 86400]
    
    # ============================================================================
    # EXISTING FEATURES FROM STAGE 11 DATASET (20)
    # ============================================================================
    
    # Amount features (6)
    features['amount'] = current_amount
    features['sender_avg_amount'] = float(tx['sender_avg_amount'])
    features['sender_max_amount'] = float(tx['sender_max_amount'])
    features['sender_tx_count'] = int(tx['sender_tx_count'])
    features['amount_to_sender_avg'] = float(tx['amount_to_sender_avg'])
    features['amount_to_sender_max'] = float(tx['amount_to_sender_max'])
    
    # Velocity features (5)
    features['sender_tx_count_24h'] = int(tx['sender_tx_count_24h'])
    features['sender_volume_24h'] = float(tx['sender_volume_24h'])
    features['amount_to_sender_volume_24h'] = float(tx['amount_to_sender_volume_24h'])
    features['same_day_count'] = int(tx['same_day_count'])
    features['same_day_total'] = float(tx['same_day_total'])
    
    # Recipient features (4)
    features['is_new_recipient'] = float(tx['is_new_recipient'])
    features['same_recipient_count'] = int(tx['same_recipient_count'])
    features['rapid_transfer_count'] = int(tx['rapid_transfer_count'])
    features['new_recipient_ratio_7d'] = float(tx.get('new_recipient_ratio_7d', 0))
    
    # Timing features (3)
    features['hour'] = tx_time.hour
    features['day_of_week'] = tx_time.weekday()
    features['is_weekend'] = 1.0 if tx_time.weekday() >= 5 else 0.0
    
    # Transaction type features (3)
    features['is_deposit'] = 1.0 if tx_type == 'deposit' else 0.0
    features['is_withdraw'] = 1.0 if tx_type == 'withdraw' else 0.0
    features['is_transfer'] = 1.0 if tx_type == 'transfer' else 0.0
    
    # ============================================================================
    # ADDITIONAL EXISTING FEATURES (COMPUTED FROM HISTORICAL DATA)
    # ============================================================================
    
    # Frequency features (3)
    features['tx_frequency_7d'] = len(hist_7d)
    features['tx_frequency_30d'] = len(hist_30d)
    
    if len(hist_7d) > 0:
        freq_7d = features['tx_frequency_7d']
        prev_7d = len([h for h in hist_14d if (current_time - h['timestamp']).days >= 7])
        avg_freq = (freq_7d + prev_7d) / 2 if prev_7d > 0 else freq_7d
        features['frequency_change_vs_avg_7d'] = (freq_7d - avg_freq) / avg_freq if avg_freq > 0 else 0.0
    else:
        features['frequency_change_vs_avg_7d'] = 0.0
    
    # Recipient features (3)
    if len(hist_24h) > 0:
        receivers_24h = [h['receiver_account'] for h in hist_24h]
        features['unique_recipients_24h'] = len(set(receivers_24h))
    else:
        features['unique_recipients_24h'] = 0
    
    receivers_7d = [h['receiver_account'] for h in hist_7d]
    features['unique_recipients_7d'] = len(set(receivers_7d))
    
    # recipient_concentration: Herfindahl index
    if len(receivers_7d) > 0:
        receiver_counts = Counter(receivers_7d)
        total = len(receivers_7d)
        hhi = sum((count / total) ** 2 for count in receiver_counts.values())
        features['recipient_concentration'] = hhi
    else:
        features['recipient_concentration'] = 0.0
    
    # Amount features (3)
    if len(hist_7d) > 0:
        amounts_7d = [float(h['amount']) for h in hist_7d]
        features['amount_std_dev'] = np.std(amounts_7d)
        mean_amount = np.mean(amounts_7d)
        std_amount = np.std(amounts_7d)
        if std_amount > 0:
            features['amount_z_score'] = (current_amount - mean_amount) / std_amount
        else:
            features['amount_z_score'] = 0.0
        
        avg_amount_7d = mean_amount
        features['amount_change_vs_avg_7d'] = (current_amount - avg_amount_7d) / avg_amount_7d if avg_amount_7d > 0 else 0.0
    else:
        features['amount_std_dev'] = 0.0
        features['amount_z_score'] = 0.0
        features['amount_change_vs_avg_7d'] = 0.0
    
    # Timing features (2)
    features['is_off_hours'] = 1.0 if tx_time.hour < 9 or tx_time.hour > 17 else 0.0
    
    if len(historical) > 0:
        last_tx = historical[-1]
        features['time_since_last_tx'] = (current_time - last_tx['timestamp']).total_seconds()
    else:
        features['time_since_last_tx'] = 0.0
    
    # ============================================================================
    # NEW CANDIDATE FEATURES (25)
    # ============================================================================
    
    # STRUCTURING FEATURES (5)
    features['threshold_proximity_10k'] = abs(current_amount - 10000)
    features['threshold_proximity_5k'] = abs(current_amount - 5000)
    
    near_threshold_7d = [h for h in hist_7d if 8000 <= float(h['amount']) <= 12000]
    features['near_threshold_count_7d'] = len(near_threshold_7d)
    features['near_threshold_ratio_7d'] = len(near_threshold_7d) / len(hist_7d) if len(hist_7d) > 0 else 0.0
    
    if len(hist_7d) > 0:
        amounts_7d = [float(h['amount']) for h in hist_7d]
        features['amount_clustering_score'] = np.std(amounts_7d)
    else:
        features['amount_clustering_score'] = 0.0
    
    # LAYERING FEATURES (5)
    features['counterparty_diversity_7d'] = len(set([h['receiver_account'] for h in hist_7d]))
    features['counterparty_diversity_30d'] = len(set([h['receiver_account'] for h in hist_30d]))
    
    outbound_7d = [h for h in hist_7d if h['transaction_type'] in ['transfer', 'withdraw']]
    features['pass_through_ratio_7d'] = len(outbound_7d) / len(hist_7d) if len(hist_7d) > 0 else 0.0
    
    if len(hist_7d) > 0:
        switches = sum(1 for i in range(1, len(hist_7d)) if hist_7d[i]['receiver_account'] != hist_7d[i-1]['receiver_account'])
        features['rapid_counterparty_switch_count'] = switches
    else:
        features['rapid_counterparty_switch_count'] = 0
    
    if len(hist_7d) > 0:
        receiver_counts = Counter([h['receiver_account'] for h in hist_7d])
        features['single_counterparty_dominance_7d'] = max(receiver_counts.values()) / len(hist_7d)
    else:
        features['single_counterparty_dominance_7d'] = 0.0
    
    # FUNNEL FEATURES (4)
    inbound_7d = [h for h in hist_7d if h['transaction_type'] == 'deposit']
    features['inbound_aggregation_7d'] = len(inbound_7d) / len(hist_7d) if len(hist_7d) > 0 else 0.0
    features['outbound_diversification_7d'] = len(outbound_7d) / len(hist_7d) if len(hist_7d) > 0 else 0.0
    features['many_to_one_ratio_7d'] = features['single_counterparty_dominance_7d']
    
    if len(hist_7d) > 0:
        receiver_counts = Counter([h['receiver_account'] for h in hist_7d])
        total = len(hist_7d)
        hhi = sum((count / total) ** 2 for count in receiver_counts.values())
        features['concentration_index_7d'] = hhi
    else:
        features['concentration_index_7d'] = 0.0
    
    # RAPID MOVEMENT FEATURES (4)
    deposit_transfer_times = []
    for i, h in enumerate(hist_7d):
        if h['transaction_type'] == 'deposit':
            for j in range(i+1, min(i+5, len(hist_7d))):
                if hist_7d[j]['transaction_type'] == 'transfer':
                    time_diff = (hist_7d[j]['timestamp'] - h['timestamp']).total_seconds()
                    deposit_transfer_times.append(time_diff)
                    break
    
    if deposit_transfer_times:
        features['inbound_to_outbound_time_avg_7d'] = np.mean(deposit_transfer_times)
    else:
        features['inbound_to_outbound_time_avg_7d'] = 0.0
    
    same_day_pairs = 0
    for i, h in enumerate(hist_7d):
        if h['transaction_type'] == 'deposit':
            for j in range(i+1, min(i+5, len(hist_7d))):
                if hist_7d[j]['transaction_type'] == 'transfer':
                    if (hist_7d[j]['timestamp'] - h['timestamp']).days == 0:
                        same_day_pairs += 1
                    break
    features['same_day_pass_through_count_7d'] = same_day_pairs
    
    inbound_amount = sum(float(h['amount']) for h in inbound_7d)
    outbound_amount = sum(float(h['amount']) for h in outbound_7d)
    features['funds_through_ratio_7d'] = outbound_amount / inbound_amount if inbound_amount > 0 else 0.0
    
    if len(hist_7d) > 0:
        days_span = (current_time - hist_7d[0]['timestamp']).days
        if days_span > 0:
            features['velocity_score_7d'] = len(hist_7d) / days_span
        else:
            features['velocity_score_7d'] = 0.0
    else:
        features['velocity_score_7d'] = 0.0
    
    # BEHAVIORAL CHANGE FEATURES (4)
    if len(hist_30d) > 0:
        amounts_30d = [float(h['amount']) for h in hist_30d]
        mean_amount = np.mean(amounts_30d)
        std_amount = np.std(amounts_30d)
        if std_amount > 0:
            features['amount_deviation_from_baseline_30d'] = (current_amount - mean_amount) / std_amount
        else:
            features['amount_deviation_from_baseline_30d'] = 0.0
    else:
        features['amount_deviation_from_baseline_30d'] = 0.0
    
    current_freq = features['tx_frequency_30d']
    if len(hist_30d) > 0:
        hist_freq = len(hist_30d) / 30
        features['frequency_deviation_from_baseline_30d'] = (current_freq - hist_freq) / hist_freq if hist_freq > 0 else 0.0
    else:
        features['frequency_deviation_from_baseline_30d'] = 0.0
    
    current_7d_receivers = set([h['receiver_account'] for h in hist_7d])
    previous_7d_receivers = set([h['receiver_account'] for h in hist_14d if (current_time - h['timestamp']).days >= 7])
    if current_7d_receivers or previous_7d_receivers:
        intersection = len(current_7d_receivers & previous_7d_receivers)
        union = len(current_7d_receivers | previous_7d_receivers)
        features['counterparty_change_score_7d'] = intersection / union if union > 0 else 0.0
    else:
        features['counterparty_change_score_7d'] = 0.0
    
    if len(hist_14d) >= 14:
        current_7d_amounts = [float(h['amount']) for h in hist_7d]
        previous_7d_amounts = [float(h['amount']) for h in hist_14d if (current_time - h['timestamp']).days >= 7]
        if len(current_7d_amounts) > 0 and len(previous_7d_amounts) > 0:
            current_std = np.std(current_7d_amounts)
            previous_std = np.std(previous_7d_amounts)
            if previous_std > 0:
                features['rolling_behavioral_change_7d'] = current_std / previous_std
            else:
                features['rolling_behavioral_change_7d'] = 0.0
        else:
            features['rolling_behavioral_change_7d'] = 0.0
    else:
        features['rolling_behavioral_change_7d'] = 0.0
    
    # SEVERE FEATURES (3)
    suspicious_indicators = 0
    if features['near_threshold_count_7d'] > 2:
        suspicious_indicators += 1
    if features['counterparty_diversity_7d'] > 5:
        suspicious_indicators += 1
    if features['pass_through_ratio_7d'] > 0.7:
        suspicious_indicators += 1
    if features['same_day_pass_through_count_7d'] > 1:
        suspicious_indicators += 1
    if abs(features['amount_deviation_from_baseline_30d']) > 2:
        suspicious_indicators += 1
    features['concurrent_suspicious_indicators'] = suspicious_indicators
    
    structuring_score = 1.0 if features['near_threshold_count_7d'] > 2 else 0.0
    layering_score = 1.0 if features['counterparty_diversity_7d'] > 5 else 0.0
    funnel_score = 1.0 if features['concentration_index_7d'] > 0.5 else 0.0
    rapid_score = 1.0 if features['same_day_pass_through_count_7d'] > 1 else 0.0
    features['typology_aggregation_score'] = structuring_score + layering_score + funnel_score + rapid_score
    
    features['severity_index'] = (
        2.0 * structuring_score +
        2.0 * layering_score +
        2.0 * funnel_score +
        2.0 * rapid_score +
        1.0 * suspicious_indicators
    )
    
    return features

# ============================================================================
# EXTRACT FEATURES FOR ALL TRANSACTIONS
# ============================================================================

print("Extracting features for all transactions...")

all_features = []
feature_names = None

for customer, cust_txs in customer_transactions.items():
    historical = []
    
    for i, tx in enumerate(cust_txs):
        # Compute features using historical transactions (before current)
        features = compute_features_for_transaction(tx, historical)
        
        # Add metadata
        features['transaction_id'] = tx['transaction_id']
        features['sender_account'] = tx['sender_account']
        
        all_features.append(features)
        
        # Add current transaction to historical for next iteration
        historical.append(tx)
        
        if feature_names is None:
            feature_names = [k for k in features.keys() if k not in ['transaction_id', 'sender_account']]

print(f"Extracted features for {len(all_features)} transactions")
print(f"Total features: {len(feature_names)}")
print()

# ============================================================================
# SAVE FEATURES TO CSV
# ============================================================================

print("Saving features to CSV...")

with open('ml_stage15_features.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['transaction_id', 'sender_account'] + feature_names)
    writer.writeheader()
    writer.writerows(all_features)

print("Features saved to ml_stage15_features.csv")
print()

# ============================================================================
# SAVE FEATURE METADATA
# ============================================================================

metadata = {
    "timestamp": datetime.now().isoformat(),
    "total_features": len(feature_names),
    "feature_names": feature_names,
    "total_transactions": len(all_features),
    "total_customers": len(customer_transactions),
    "existing_features": 32,
    "new_features": 25,
    "removed_features": ["is_self_transfer"]
}

with open('ml_stage15_feature_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

print("Feature metadata saved to ml_stage15_feature_metadata.json")
print()

print("=" * 80)
print("FEATURE EXTRACTION COMPLETE")
print("=" * 80)
print(f"Total features: {len(feature_names)}")
print(f"Total transactions: {len(all_features)}")
