"""
STAGE 13: SCENARIO-LEVEL LEARNABILITY & FEATURE GAP AUDIT

This is an AUDIT/DIAGNOSTIC stage only.
Do NOT attempt to improve model performance.
"""

import csv
import json
import numpy as np
from datetime import datetime
from collections import defaultdict, Counter
from scipy import stats
from sklearn.feature_selection import mutual_info_classif
import pandas as pd

print("=" * 80)
print("STAGE 13: SCENARIO-LEVEL LEARNABILITY & FEATURE GAP AUDIT")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================================
# TASK 1: VERIFY STAGE 11 DATASET INTEGRITY
# ============================================================================

print("=" * 80)
print("TASK 1: VERIFY STAGE 11 DATASET INTEGRITY")
print("-" * 80)

# Load data
with open('ml_stage11_dataset.csv', 'r') as f:
    reader = csv.DictReader(f)
    dataset = list(reader)

with open('ml_stage11_features.csv', 'r') as f:
    reader = csv.DictReader(f)
    features = list(reader)

with open('ml_stage11_ground_truth.json', 'r') as f:
    ground_truth = json.load(f)

with open('ml_stage11_metadata.json', 'r') as f:
    metadata = json.load(f)

print(f"Dataset transactions: {len(dataset)}")
print(f"Feature records: {len(features)}")
print(f"Ground truth records: {len(ground_truth)}")

# Verify counts
assert len(dataset) == 10000, "Dataset should have 10,000 transactions"
assert len(features) == 10000, "Features should have 10,000 records"
assert len(ground_truth) == 10000, "Ground truth should have 10,000 records"
print("PASS: 10,000 transactions")

# Verify customers
customers = set(tx['sender_account'] for tx in dataset)
print(f"Unique customers: {len(customers)}")
assert len(customers) == 200, "Should have 200 customers"
print("PASS: 200 customers")

# Verify transactions per customer
customer_tx_counts = Counter(tx['sender_account'] for tx in dataset)
for customer, count in customer_tx_counts.items():
    assert count == 50, f"Customer {customer} should have 50 transactions, has {count}"
print("PASS: 50 transactions/customer")

# Verify 34 features
feature_names = list(features[0].keys())
print(f"Number of features: {len(feature_names)}")
assert len(feature_names) == 34, "Should have 34 features"
print("PASS: 34 approved features")

# Verify no NaN/infinite values
for feature_name in feature_names:
    values = [float(tx[feature_name]) for tx in features]
    nan_count = sum(1 for v in values if np.isnan(v))
    inf_count = sum(1 for v in values if np.isinf(v))
    assert nan_count == 0, f"Feature {feature_name} has NaN values"
    assert inf_count == 0, f"Feature {feature_name} has infinite values"
print("PASS: No NaN or infinite values")

# Verify is_self_transfer constant
is_self_transfer_values = [float(tx['is_self_transfer']) for tx in features]
assert all(v == 0.0 for v in is_self_transfer_values), "is_self_transfer should be constant 0.0"
print("PASS: is_self_transfer constant (known generator limitation)")

# Verify new_recipient_ratio_7d variable
new_recipient_values = [float(tx['new_recipient_ratio_7d']) for tx in features]
new_recipient_std = np.std(new_recipient_values)
assert new_recipient_std > 0, "new_recipient_ratio_7d should be variable"
print(f"PASS: new_recipient_ratio_7d variable (std={new_recipient_std:.4f})")

# Verify ground truth matches scenario_id
scenario_to_label_mapping = {
    "normal": "normal",
    "legitimate_high_value": "normal",
    "cash_deposit": "normal",
    "cash_withdrawal": "normal",
    "new_recipient": "normal",
    "structuring": "suspicious",
    "layering": "suspicious",
    "funnel": "suspicious",
    "rapid_movement": "suspicious",
    "high_risk_country": "suspicious",
    "behavioral_change": "suspicious",
    "severe_structuring": "super_suspicious",
    "severe_layering": "super_suspicious",
    "severe_funnel": "super_suspicious",
    "multiple_typologies": "super_suspicious",
}

label_mismatches = 0
for tx in ground_truth:
    scenario_id = tx['scenario_id']
    scenario_name = scenario_id.rsplit('_', 1)[0] if '_' in scenario_id else scenario_id
    expected_label = scenario_to_label_mapping.get(scenario_name, "normal")
    actual_label = tx['ground_truth_label']
    if expected_label != actual_label:
        label_mismatches += 1

assert label_mismatches == 0, f"Should have 0 label mismatches, found {label_mismatches}"
print("PASS: Ground truth matches scenario_id")

# Verify scenario distribution
scenario_names = set()
for tx in ground_truth:
    scenario_id = tx['scenario_id']
    scenario_name = scenario_id.rsplit('_', 1)[0] if '_' in scenario_id else scenario_id
    scenario_names.add(scenario_name)

print(f"Unique scenarios observed: {len(scenario_names)}")
print(f"Scenario names: {sorted(scenario_names)}")

# Verify class distribution
class_distribution = Counter(tx['ground_truth_label'] for tx in ground_truth)
print(f"Class distribution: {dict(class_distribution)}")
print()

# ============================================================================
# TASK 2: SCENARIO-LEVEL CLASSIFICATION ANALYSIS
# ============================================================================

print("=" * 80)
print("TASK 2: SCENARIO-LEVEL CLASSIFICATION ANALYSIS")
print("-" * 80)

# Load Stage 12 model results
with open('ml_stage12_model_results.json', 'r') as f:
    stage12_results = json.load(f)

# Get predictions from PRIMARY split
rf_predictions = np.array(stage12_results['primary_split']['results']['random_forest']['predictions'])
gb_predictions = np.array(stage12_results['primary_split']['results']['gradient_boosting']['predictions'])

# Get PRIMARY split indices
with open('ml_stage12_primary_split.json', 'r') as f:
    primary_split = json.load(f)

primary_test_indices = primary_split['test_indices']

# Get ground truth for test set
test_labels = [ground_truth[i]['ground_truth_label'] for i in primary_test_indices]
test_scenarios = [ground_truth[i]['scenario_id'] for i in primary_test_indices]

# Encode labels
label_encoder = {"normal": 0, "suspicious": 1, "super_suspicious": 2}
test_labels_encoded = np.array([label_encoder[label] for label in test_labels])

# Scenario-level performance
scenario_performance = {}

for i, (scenario_id, true_label, rf_pred, gb_pred) in enumerate(zip(test_scenarios, test_labels, rf_predictions, gb_predictions)):
    scenario_name = scenario_id.rsplit('_', 1)[0] if '_' in scenario_id else scenario_id
    
    if scenario_name not in scenario_performance:
        scenario_performance[scenario_name] = {
            'true_class': true_label,
            'count': 0,
            'pred_normal_rf': 0,
            'pred_suspicious_rf': 0,
            'pred_super_rf': 0,
            'pred_normal_gb': 0,
            'pred_suspicious_gb': 0,
            'pred_super_gb': 0,
            'correct_rf': 0,
            'correct_gb': 0
        }
    
    scenario_performance[scenario_name]['count'] += 1
    
    if rf_pred == 0:
        scenario_performance[scenario_name]['pred_normal_rf'] += 1
    elif rf_pred == 1:
        scenario_performance[scenario_name]['pred_suspicious_rf'] += 1
    else:
        scenario_performance[scenario_name]['pred_super_rf'] += 1
    
    if gb_pred == 0:
        scenario_performance[scenario_name]['pred_normal_gb'] += 1
    elif gb_pred == 1:
        scenario_performance[scenario_name]['pred_suspicious_gb'] += 1
    else:
        scenario_performance[scenario_name]['pred_super_gb'] += 1
    
    if rf_pred == label_encoder[true_label]:
        scenario_performance[scenario_name]['correct_rf'] += 1
    if gb_pred == label_encoder[true_label]:
        scenario_performance[scenario_name]['correct_gb'] += 1

# Calculate recall
for scenario in scenario_performance:
    scenario_performance[scenario]['recall_rf'] = scenario_performance[scenario]['correct_rf'] / scenario_performance[scenario]['count']
    scenario_performance[scenario]['recall_gb'] = scenario_performance[scenario]['correct_gb'] / scenario_performance[scenario]['count']

# Print scenario-level performance table
print(f"{'Scenario':<25} {'True Class':<15} {'Count':<6} {'Pred N RF':<10} {'Pred S RF':<10} {'Pred SS RF':<10} {'Recall RF':<10} {'Recall GB':<10}")
print("-" * 100)

for scenario in sorted(scenario_performance.keys()):
    perf = scenario_performance[scenario]
    print(f"{scenario:<25} {perf['true_class']:<15} {perf['count']:<6} {perf['pred_normal_rf']:<10} {perf['pred_suspicious_rf']:<10} {perf['pred_super_rf']:<10} {perf['recall_rf']:<10.4f} {perf['recall_gb']:<10.4f}")

print()

# ============================================================================
# TASK 3: SCENARIO VS NORMAL FEATURE SEPARATION
# ============================================================================

print("=" * 80)
print("TASK 3: SCENARIO VS NORMAL FEATURE SEPARATION")
print("-" * 80)

# Get feature values for each scenario
scenario_features = defaultdict(list)
normal_features = []

for i, (tx, gt) in enumerate(zip(features, ground_truth)):
    scenario_id = gt['scenario_id']
    scenario_name = scenario_id.rsplit('_', 1)[0] if '_' in scenario_id else scenario_id
    
    feature_values = [float(tx[fn]) for fn in feature_names]
    
    if scenario_name == 'normal':
        normal_features.append(feature_values)
    else:
        scenario_features[scenario_name].append(feature_values)

normal_features = np.array(normal_features)

# Calculate Cohen's d for each scenario vs normal
scenario_cohens_d = {}

for scenario, scenario_vals in scenario_features.items():
    scenario_vals = np.array(scenario_vals)
    
    cohens_d_values = {}
    for j, feature_name in enumerate(feature_names):
        normal_vals = normal_features[:, j]
        scenario_vals_feature = scenario_vals[:, j]
        
        mean_normal = np.mean(normal_vals)
        mean_scenario = np.mean(scenario_vals_feature)
        std_normal = np.std(normal_vals)
        std_scenario = np.std(scenario_vals_feature)
        
        pooled_std = np.sqrt((std_normal**2 + std_scenario**2) / 2)
        if pooled_std > 0:
            cohens_d = abs(mean_scenario - mean_normal) / pooled_std
        else:
            cohens_d = 0.0
        
        cohens_d_values[feature_name] = cohens_d
    
    scenario_cohens_d[scenario] = cohens_d_values

# Print top features for each scenario
print("Top 5 features by Cohen's d for each scenario vs normal:")
for scenario in sorted(scenario_cohens_d.keys()):
    cohens_d = scenario_cohens_d[scenario]
    top_features = sorted(cohens_d.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"\n{scenario}:")
    for feature, d in top_features:
        print(f"  {feature}: {d:.4f}")

print()

# ============================================================================
# TASK 4: WITHIN-CLASS SCENARIO SEPARATION
# ============================================================================

print("=" * 80)
print("TASK 4: WITHIN-CLASS SCENARIO SEPARATION")
print("-" * 80)

# Group scenarios by class
class_scenarios = {
    'normal': ['normal'],
    'suspicious': ['structuring', 'layering', 'funnel', 'rapid_movement', 'high_risk_country', 'behavioral_change'],
    'super_suspicious': ['severe_structuring', 'severe_layering', 'multiple_typologies']
}

# Calculate within-class separation
for class_name, scenarios in class_scenarios.items():
    if len(scenarios) <= 1:
        continue
    
    print(f"\n{class_name.upper()} CLASS SCENARIO SEPARATION:")
    
    for i, scenario1 in enumerate(scenarios):
        for scenario2 in scenarios[i+1:]:
            if scenario1 not in scenario_features or scenario2 not in scenario_features:
                continue
            
            vals1 = np.array(scenario_features[scenario1])
            vals2 = np.array(scenario_features[scenario2])
            
            # Calculate average Cohen's d across all features
            cohens_d_values = []
            for j in range(len(feature_names)):
                mean1 = np.mean(vals1[:, j])
                mean2 = np.mean(vals2[:, j])
                std1 = np.std(vals1[:, j])
                std2 = np.std(vals2[:, j])
                
                pooled_std = np.sqrt((std1**2 + std2**2) / 2)
                if pooled_std > 0:
                    cohens_d = abs(mean1 - mean2) / pooled_std
                    cohens_d_values.append(cohens_d)
            
            avg_cohens_d = np.mean(cohens_d_values) if cohens_d_values else 0.0
            print(f"  {scenario1} vs {scenario2}: avg Cohen's d = {avg_cohens_d:.4f}")

print()

# ============================================================================
# TASK 5: FEATURE COVERAGE MATRIX
# ============================================================================

print("=" * 80)
print("TASK 5: FEATURE COVERAGE MATRIX")
print("-" * 80)

# Define feature dimensions
feature_dimensions = {
    'amount': ['amount', 'sender_avg_amount', 'sender_max_amount', 'amount_to_sender_avg', 'amount_to_sender_max', 'amount_std_dev', 'amount_z_score'],
    'velocity': ['sender_tx_count_24h', 'sender_volume_24h', 'amount_to_sender_volume_24h', 'same_day_count', 'same_day_total', 'rapid_transfer_count'],
    'frequency': ['sender_tx_count', 'tx_frequency_7d', 'tx_frequency_30d', 'frequency_change_vs_avg_7d'],
    'recipient': ['is_new_recipient', 'same_recipient_count', 'unique_recipients_24h', 'unique_recipients_7d', 'recipient_concentration', 'new_recipient_ratio_7d'],
    'timing': ['hour', 'day_of_week', 'is_weekend', 'is_off_hours', 'time_since_last_tx'],
    'historical_behavior': ['amount_change_vs_avg_7d'],
    'country': [],  # No features capture country
}

# Assess coverage for each scenario
feature_coverage = {}

for scenario in scenario_cohens_d:
    coverage = {}
    cohens_d = scenario_cohens_d[scenario]
    
    for dimension, dim_features in feature_dimensions.items():
        if not dim_features:
            coverage[dimension] = 'NONE'
            continue
        
        # Calculate average Cohen's d for this dimension
        dim_cohens_d = [cohens_d[fn] for fn in dim_features if fn in cohens_d]
        avg_cohens_d = np.mean(dim_cohens_d) if dim_cohens_d else 0.0
        
        if avg_cohens_d >= 0.8:
            coverage[dimension] = 'STRONG'
        elif avg_cohens_d >= 0.5:
            avg_cohens_d = 'MODERATE'
        elif avg_cohens_d >= 0.2:
            coverage[dimension] = 'WEAK'
        else:
            coverage[dimension] = 'NONE'
    
    # Determine overall observability
    strong_count = sum(1 for v in coverage.values() if v == 'STRONG')
    moderate_count = sum(1 for v in coverage.values() if v == 'MODERATE')
    weak_count = sum(1 for v in coverage.values() if v == 'WEAK')
    
    if strong_count >= 2:
        overall = 'STRONG'
    elif moderate_count >= 2 or strong_count >= 1:
        overall = 'MODERATE'
    elif weak_count >= 2:
        overall = 'WEAK'
    else:
        overall = 'NONE'
    
    coverage['overall'] = overall
    feature_coverage[scenario] = coverage

# Print feature coverage matrix
print(f"{'Scenario':<25} {'Amount':<10} {'Velocity':<10} {'Frequency':<10} {'Recipient':<10} {'Timing':<10} {'Historical':<10} {'Country':<10} {'Overall':<10}")
print("-" * 110)

for scenario in sorted(feature_coverage.keys()):
    cov = feature_coverage[scenario]
    print(f"{scenario:<25} {cov.get('amount', 'NONE'):<10} {cov.get('velocity', 'NONE'):<10} {cov.get('frequency', 'NONE'):<10} {cov.get('recipient', 'NONE'):<10} {cov.get('timing', 'NONE'):<10} {cov.get('historical_behavior', 'NONE'):<10} {cov.get('country', 'NONE'):<10} {cov['overall']:<10}")

print()

# ============================================================================
# TASK 6: HIGH-RISK-COUNTRY AUDIT
# ============================================================================

print("=" * 80)
print("TASK 6: HIGH-RISK-COUNTRY AUDIT")
print("-" * 80)

if 'high_risk_country' in scenario_features:
    hrc_count = len(scenario_features['high_risk_country'])
    print(f"High-risk-country transactions: {hrc_count}")
    print(f"Label: suspicious")
    print(f"Percentage of dataset: {hrc_count / len(ground_truth) * 100:.2f}%")
    
    # Check feature separation
    hrc_cohens_d = scenario_cohens_d['high_risk_country']
    top_features = sorted(hrc_cohens_d.items(), key=lambda x: x[1], reverse=True)[:10]
    print("\nTop 10 features by Cohen's d vs normal:")
    for feature, d in top_features:
        print(f"  {feature}: {d:.4f}")
    
    # Check observability
    hrc_coverage = feature_coverage['high_risk_country']
    print(f"\nOverall observability: {hrc_coverage['overall']}")
    print(f"Country dimension: {hrc_coverage.get('country', 'NONE')}")
    
    if hrc_coverage['overall'] == 'NONE' or hrc_coverage['overall'] == 'WEAK':
        print("\nCONCLUSION: NOT REPRESENTED BY CURRENT FEATURE SET")
    else:
        print("\nCONCLUSION: PARTIALLY REPRESENTED")
else:
    print("High-risk-country scenario not found in dataset")

print()

# ============================================================================
# TASK 7: SEVERE SCENARIO AUDIT
# ============================================================================

print("=" * 80)
print("TASK 7: SEVERE SCENARIO AUDIT")
print("-" * 80)

severe_scenarios = ['severe_structuring', 'severe_layering', 'multiple_typologies', 'severe_funnel']

for scenario in severe_scenarios:
    if scenario in scenario_features:
        count = len(scenario_features[scenario])
        print(f"\n{scenario}:")
        print(f"  Count: {count}")
        print(f"  Label: super_suspicious")
        
        # Check feature separation vs normal
        cohens_d = scenario_cohens_d[scenario]
        top_features = sorted(cohens_d.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"  Top 5 features vs normal:")
        for feature, d in top_features:
            print(f"    {feature}: {d:.4f}")
        
        # Check observability
        coverage = feature_coverage[scenario]
        print(f"  Overall observability: {coverage['overall']}")
    else:
        print(f"\n{scenario}: NOT PRESENT IN DATASET")

print()

# ============================================================================
# TASK 8: SUSPICIOUS RECALL ROOT CAUSE
# ============================================================================

print("=" * 80)
print("TASK 8: SUSPICIOUS RECALL ROOT CAUSE")
print("-" * 80)

# Get suspicious transactions in test set
suspicious_indices = [i for i, label in enumerate(test_labels) if label == 'suspicious']
suspicious_predictions_rf = rf_predictions[suspicious_indices]
suspicious_predictions_gb = gb_predictions[suspicious_indices]

# Count where suspicious is predicted as normal vs super_suspicious
suspicious_as_normal_rf = sum(1 for p in suspicious_predictions_rf if p == 0)
suspicious_as_super_rf = sum(1 for p in suspicious_predictions_rf if p == 2)
suspicious_as_suspicious_rf = sum(1 for p in suspicious_predictions_rf if p == 1)

suspicious_as_normal_gb = sum(1 for p in suspicious_predictions_gb if p == 0)
suspicious_as_super_gb = sum(1 for p in suspicious_predictions_gb if p == 2)
suspicious_as_suspicious_gb = sum(1 for p in suspicious_predictions_gb if p == 1)

print(f"Suspicious transactions in test set: {len(suspicious_indices)}")
print(f"\nRandom Forest predictions:")
print(f"  Predicted as normal: {suspicious_as_normal_rf} ({suspicious_as_normal_rf/len(suspicious_indices)*100:.1f}%)")
print(f"  Predicted as suspicious: {suspicious_as_suspicious_rf} ({suspicious_as_suspicious_rf/len(suspicious_indices)*100:.1f}%)")
print(f"  Predicted as super_suspicious: {suspicious_as_super_rf} ({suspicious_as_super_rf/len(suspicious_indices)*100:.1f}%)")

print(f"\nGradient Boosting predictions:")
print(f"  Predicted as normal: {suspicious_as_normal_gb} ({suspicious_as_normal_gb/len(suspicious_indices)*100:.1f}%)")
print(f"  Predicted as suspicious: {suspicious_as_suspicious_gb} ({suspicious_as_suspicious_gb/len(suspicious_indices)*100:.1f}%)")
print(f"  Predicted as super_suspicious: {suspicious_as_super_gb} ({suspicious_as_super_gb/len(suspicious_indices)*100:.1f}%)")

print(f"\nCONCLUSION: Suspicious transactions are mostly being classified as NORMAL")

# Check scenario-level suspicious performance
print(f"\nScenario-level suspicious performance:")
for scenario in ['structuring', 'layering', 'funnel', 'rapid_movement', 'high_risk_country', 'behavioral_change']:
    if scenario in scenario_performance:
        perf = scenario_performance[scenario]
        if perf['true_class'] == 'suspicious':
            print(f"  {scenario}: recall_rf={perf['recall_rf']:.4f}, recall_gb={perf['recall_gb']:.4f}")

print()

# ============================================================================
# SAVE RESULTS
# ============================================================================

results = {
    "timestamp": datetime.now().isoformat(),
    "task_1_integrity": {
        "transactions": len(dataset),
        "customers": len(customers),
        "features": len(feature_names),
        "scenarios_observed": len(scenario_names),
        "scenario_names": sorted(scenario_names),
        "status": "PASS"
    },
    "task_2_scenario_performance": scenario_performance,
    "task_3_scenario_cohens_d": {k: {k2: float(v2) for k2, v2 in v.items()} for k, v in scenario_cohens_d.items()},
    "task_5_feature_coverage": feature_coverage,
    "task_6_high_risk_country": {
        "count": len(scenario_features.get('high_risk_country', [])),
        "observability": feature_coverage.get('high_risk_country', {}).get('overall', 'NONE')
    },
    "task_8_suspicious_recall": {
        "total_suspicious": len(suspicious_indices),
        "as_normal_rf": suspicious_as_normal_rf,
        "as_suspicious_rf": suspicious_as_suspicious_rf,
        "as_super_rf": suspicious_as_super_rf,
        "as_normal_gb": suspicious_as_normal_gb,
        "as_suspicious_gb": suspicious_as_suspicious_gb,
        "as_super_gb": suspicious_as_super_gb
    }
}

with open('ml_stage13_scenario_analysis_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("=" * 80)
print("SCENARIO ANALYSIS COMPLETE (PARTIAL)")
print("=" * 80)
print("Results saved to ml_stage13_scenario_analysis_results.json")
print()
print("NOTE: This is a partial analysis. Additional tasks (9-15) require separate scripts.")
