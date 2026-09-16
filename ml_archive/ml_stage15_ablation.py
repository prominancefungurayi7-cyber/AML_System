"""
STAGE 15I: FEATURE ABLATION

Run controlled group-level comparisons to determine which feature groups are responsible for improvements.
"""

import csv
import json
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import f1_score
from sklearn.preprocessing import LabelEncoder

print("=" * 80)
print("STAGE 15I: FEATURE ABLATION")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================================
# LOAD STAGE 15 FEATURES
# ============================================================================

print("Loading Stage 15 features...")
features = []
with open('ml_stage15_features.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        features.append(row)

print(f"Loaded {len(features)} transactions")
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
# LOAD STAGE 12 PRIMARY SPLIT
# ============================================================================

print("Loading Stage 12 primary split...")
with open('ml_stage12_primary_split.json', 'r') as f:
    primary_split = json.load(f)

train_customers = set(primary_split['train_customer_ids'])
test_customers = set(primary_split['test_customer_ids'])

print(f"Train customers: {len(train_customers)}")
print(f"Test customers: {len(test_customers)}")
print()

# ============================================================================
# LOAD FEATURE METADATA
# ============================================================================

with open('ml_stage15_feature_metadata.json', 'r') as f:
    metadata = json.load(f)

feature_names = metadata['feature_names']

# ============================================================================
# DEFINE FEATURE GROUPS
# ============================================================================

print("Defining feature groups...")

# Existing features (32)
existing_features = [
    'amount', 'sender_avg_amount', 'sender_max_amount', 'sender_tx_count',
    'amount_to_sender_avg', 'amount_to_sender_max', 'sender_tx_count_24h',
    'sender_volume_24h', 'amount_to_sender_volume_24h', 'same_day_count',
    'same_day_total', 'is_new_recipient', 'same_recipient_count',
    'rapid_transfer_count', 'new_recipient_ratio_7d', 'hour', 'day_of_week',
    'is_weekend', 'is_deposit', 'is_withdraw', 'is_transfer',
    'tx_frequency_7d', 'tx_frequency_30d', 'frequency_change_vs_avg_7d',
    'unique_recipients_24h', 'unique_recipients_7d', 'recipient_concentration',
    'amount_std_dev', 'amount_z_score', 'amount_change_vs_avg_7d',
    'is_off_hours', 'time_since_last_tx'
]

# New feature groups
structuring_features = [
    'threshold_proximity_10k', 'threshold_proximity_5k', 'near_threshold_count_7d',
    'near_threshold_ratio_7d', 'amount_clustering_score'
]

layering_features = [
    'counterparty_diversity_7d', 'counterparty_diversity_30d', 'pass_through_ratio_7d',
    'rapid_counterparty_switch_count', 'single_counterparty_dominance_7d'
]

funnel_features = [
    'inbound_aggregation_7d', 'outbound_diversification_7d', 'many_to_one_ratio_7d',
    'concentration_index_7d'
]

rapid_movement_features = [
    'inbound_to_outbound_time_avg_7d', 'same_day_pass_through_count_7d',
    'funds_through_ratio_7d', 'velocity_score_7d'
]

behavioral_change_features = [
    'amount_deviation_from_baseline_30d', 'frequency_deviation_from_baseline_30d',
    'counterparty_change_score_7d', 'rolling_behavioral_change_7d'
]

severe_features = [
    'concurrent_suspicious_indicators', 'typology_aggregation_score', 'severity_index'
]

feature_groups = {
    'baseline': existing_features,
    'structuring': existing_features + structuring_features,
    'layering': existing_features + layering_features,
    'funnel': existing_features + funnel_features,
    'rapid_movement': existing_features + rapid_movement_features,
    'behavioral_change': existing_features + behavioral_change_features,
    'severe': existing_features + severe_features,
    'full': feature_names
}

print(f"Defined {len(feature_groups)} feature groups")
for group_name, group_features in feature_groups.items():
    print(f"  {group_name}: {len(group_features)} features")

print()

# ============================================================================
# MERGE FEATURES WITH GROUND TRUTH
# ============================================================================

print("Merging features with ground truth...")

gt_map = {str(gt['transaction_id']): gt for gt in ground_truth}

merged_data = []
for feature in features:
    tx_id = str(feature['transaction_id'])
    if tx_id in gt_map:
        merged = {**feature, **gt_map[tx_id]}
        merged_data.append(merged)

print(f"Merged {len(merged_data)} transactions")
print()

# ============================================================================
# SPLIT BY CUSTOMER
# ============================================================================

print("Splitting by customer...")

train_data = []
test_data = []

for data in merged_data:
    customer = data['sender_account']
    if customer in train_customers:
        train_data.append(data)
    elif customer in test_customers:
        test_data.append(data)

print(f"Train transactions: {len(train_data)}")
print(f"Test transactions: {len(test_data)}")
print()

# ============================================================================
# PREPARE LABELS
# ============================================================================

print("Preparing labels...")

y_train = [f['ground_truth_label'] for f in train_data]
y_test = [f['ground_truth_label'] for f in test_data]

label_encoder = LabelEncoder()
label_encoder.fit(y_train + y_test)
y_train_encoded = label_encoder.transform(y_train)
y_test_encoded = label_encoder.transform(y_test)

print(f"Label classes: {label_encoder.classes_}")
print()

# ============================================================================
# RUN ABLATION EXPERIMENTS
# ============================================================================

print("Running ablation experiments...")

ablation_results = {}

for group_name, group_features in feature_groups.items():
    print(f"\nTraining with {group_name} features ({len(group_features)} features)...")
    
    # Extract features for this group
    X_train = np.array([[float(f[name]) for name in group_features if name in f] for f in train_data])
    X_test = np.array([[float(f[name]) for name in group_features if name in f] for f in test_data])
    
    # Train Random Forest
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train_encoded)
    rf_test_pred = rf.predict(X_test)
    rf_test_macro_f1 = f1_score(y_test_encoded, rf_test_pred, average='macro')
    
    # Train Gradient Boosting
    gb = GradientBoostingClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42
    )
    gb.fit(X_train, y_train_encoded)
    gb_test_pred = gb.predict(X_test)
    gb_test_macro_f1 = f1_score(y_test_encoded, gb_test_pred, average='macro')
    
    ablation_results[group_name] = {
        'feature_count': len(group_features),
        'random_forest_test_macro_f1': rf_test_macro_f1,
        'gradient_boosting_test_macro_f1': gb_test_macro_f1
    }
    
    print(f"  RF Test Macro F1: {rf_test_macro_f1:.4f}")
    print(f"  GB Test Macro F1: {gb_test_macro_f1:.4f}")

print()

# ============================================================================
# PRINT ABLATION RESULTS
# ============================================================================

print("ABLATION RESULTS:")
print("-" * 80)

print("Feature Group | Feature Count | RF Test Macro F1 | GB Test Macro F1 | RF Improvement | GB Improvement")
print("-" * 100)

baseline_rf = ablation_results['baseline']['random_forest_test_macro_f1']
baseline_gb = ablation_results['baseline']['gradient_boosting_test_macro_f1']

for group_name in ['baseline', 'structuring', 'layering', 'funnel', 'rapid_movement', 'behavioral_change', 'severe', 'full']:
    result = ablation_results[group_name]
    rf_improvement = result['random_forest_test_macro_f1'] - baseline_rf
    gb_improvement = result['gradient_boosting_test_macro_f1'] - baseline_gb
    
    print(f"{group_name:15} | {result['feature_count']:13} | {result['random_forest_test_macro_f1']:16.4f} | {result['gradient_boosting_test_macro_f1']:16.4f} | {rf_improvement:14.4f} | {gb_improvement:14.4f}")

print()

# ============================================================================
# SAVE RESULTS
# ============================================================================

results = {
    "timestamp": datetime.now().isoformat(),
    "feature_groups": feature_groups,
    "ablation_results": ablation_results,
    "baseline_rf": baseline_rf,
    "baseline_gb": baseline_gb
}

with open('ml_stage15_ablation_results.json', 'w') as f:
    json.dump(results, f, indent=2)

# ============================================================================
# SAVE CSV
# ============================================================================

with open('ml_stage15_ablation_results.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['feature_group', 'feature_count', 'rf_test_macro_f1', 'gb_test_macro_f1', 'rf_improvement', 'gb_improvement'])
    for group_name in ['baseline', 'structuring', 'layering', 'funnel', 'rapid_movement', 'behavioral_change', 'severe', 'full']:
        result = ablation_results[group_name]
        rf_improvement = result['random_forest_test_macro_f1'] - baseline_rf
        gb_improvement = result['gradient_boosting_test_macro_f1'] - baseline_gb
        writer.writerow([
            group_name,
            result['feature_count'],
            result['random_forest_test_macro_f1'],
            result['gradient_boosting_test_macro_f1'],
            rf_improvement,
            gb_improvement
        ])

print("=" * 80)
print("FEATURE ABLATION COMPLETE")
print("=" * 80)
print("Results saved to ml_stage15_ablation_results.json")
print("CSV saved to ml_stage15_ablation_results.csv")
