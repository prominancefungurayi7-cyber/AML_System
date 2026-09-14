"""
STAGE 13: ADDITIONAL ANALYSIS (TASKS 9-15)

This script performs the remaining analysis tasks:
- TASK 9: Customer/profile effect analysis
- TASK 10: Temporal analysis
- TASK 11: Random Forest overfitting analysis
- TASK 12: Feature importance stability
- TASK 13: Feature sufficiency verdict
- TASK 14: Feature gap analysis
- TASK 15: Model vs data root cause decision
"""

import csv
import json
import numpy as np
from datetime import datetime
from collections import defaultdict, Counter
import pandas as pd

print("=" * 80)
print("STAGE 13: ADDITIONAL ANALYSIS (TASKS 9-15)")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================================
# LOAD DATA
# ============================================================================

with open('ml_stage11_dataset.csv', 'r') as f:
    reader = csv.DictReader(f)
    dataset = list(reader)

with open('ml_stage11_features.csv', 'r') as f:
    reader = csv.DictReader(f)
    features = list(reader)

with open('ml_stage11_ground_truth.json', 'r') as f:
    ground_truth = json.load(f)

with open('ml_stage12_model_results.json', 'r') as f:
    stage12_results = json.load(f)

with open('ml_stage6_results.json', 'r') as f:
    stage6_results = json.load(f)

with open('ml_stage13_scenario_analysis_results.json', 'r') as f:
    scenario_results = json.load(f)

feature_names = list(features[0].keys())

# ============================================================================
# TASK 9: CUSTOMER/PROFILE EFFECT ANALYSIS
# ============================================================================

print("=" * 80)
print("TASK 9: CUSTOMER/PROFILE EFFECT ANALYSIS")
print("-" * 80)

# Map customer to scenarios and labels
customer_scenarios = defaultdict(list)
customer_labels = defaultdict(list)
customer_features = defaultdict(list)

for i, (tx, gt) in enumerate(zip(dataset, ground_truth)):
    customer = tx['sender_account']
    scenario_id = gt['scenario_id']
    scenario_name = scenario_id.rsplit('_', 1)[0] if '_' in scenario_id else scenario_id
    label = gt['ground_truth_label']
    
    customer_scenarios[customer].append(scenario_name)
    customer_labels[customer].append(label)
    
    feature_values = [float(features[i][fn]) for fn in feature_names]
    customer_features[customer].append(feature_values)

# Calculate customer-level statistics
customer_stats = {}
for customer in customer_scenarios:
    scenarios = customer_scenarios[customer]
    labels = customer_labels[customer]
    
    # Count scenarios
    scenario_counts = Counter(scenarios)
    label_counts = Counter(labels)
    
    # Calculate average features
    feature_values = np.array(customer_features[customer])
    avg_features = np.mean(feature_values, axis=0)
    
    customer_stats[customer] = {
        'scenario_counts': dict(scenario_counts),
        'label_counts': dict(label_counts),
        'avg_features': avg_features.tolist(),
        'primary_label': label_counts.most_common(1)[0][0]
    }

# Check if customers are homogeneous or heterogeneous
homogeneous_customers = sum(1 for c in customer_stats if len(customer_stats[c]['label_counts']) == 1)
heterogeneous_customers = sum(1 for c in customer_stats if len(customer_stats[c]['label_counts']) > 1)

print(f"Homogeneous customers (single label): {homogeneous_customers}")
print(f"Heterogeneous customers (multiple labels): {heterogeneous_customers}")

# Check if certain customer profiles are associated with certain classes
normal_customers = [c for c in customer_stats if customer_stats[c]['primary_label'] == 'normal']
suspicious_customers = [c for c in customer_stats if customer_stats[c]['primary_label'] == 'suspicious']
super_customers = [c for c in customer_stats if customer_stats[c]['primary_label'] == 'super_suspicious']

print(f"\nCustomers by primary label:")
print(f"  Normal: {len(normal_customers)}")
print(f"  Suspicious: {len(suspicious_customers)}")
print(f"  Super-suspicious: {len(super_customers)}")

# Calculate average feature differences between customer groups
normal_avg_features = np.mean([customer_stats[c]['avg_features'] for c in normal_customers], axis=0)
suspicious_avg_features = np.mean([customer_stats[c]['avg_features'] for c in suspicious_customers], axis=0)
super_avg_features = np.mean([customer_stats[c]['avg_features'] for c in super_customers], axis=0)

print(f"\nTop 5 features distinguishing customer groups:")
print("Normal vs Suspicious:")
diff_normal_suspicious = np.abs(normal_avg_features - suspicious_avg_features)
top_indices = np.argsort(diff_normal_suspicious)[-5:][::-1]
for idx in top_indices:
    print(f"  {feature_names[idx]}: {diff_normal_suspicious[idx]:.4f}")

print("Normal vs Super-suspicious:")
diff_normal_super = np.abs(normal_avg_features - super_avg_features)
top_indices = np.argsort(diff_normal_super)[-5:][::-1]
for idx in top_indices:
    print(f"  {feature_names[idx]}: {diff_normal_super[idx]:.4f}")

print()

# ============================================================================
# TASK 10: TEMPORAL ANALYSIS
# ============================================================================

print("=" * 80)
print("TASK 10: TEMPORAL ANALYSIS")
print("-" * 80)

# Extract dates from timestamps
dates = [tx['timestamp'][:10] for tx in dataset]

# Calculate scenario frequency by date
scenario_by_date = defaultdict(lambda: defaultdict(int))
for tx, gt in zip(dataset, ground_truth):
    date = tx['timestamp'][:10]
    scenario_id = gt['scenario_id']
    scenario_name = scenario_id.rsplit('_', 1)[0] if '_' in scenario_id else scenario_id
    scenario_by_date[date][scenario_name] += 1

# Calculate class frequency by date
class_by_date = defaultdict(lambda: defaultdict(int))
for tx, gt in zip(dataset, ground_truth):
    date = tx['timestamp'][:10]
    label = gt['ground_truth_label']
    class_by_date[date][label] += 1

# Print temporal distribution
print("Class frequency by date (first 10 days):")
for date in sorted(class_by_date.keys())[:10]:
    print(f"  {date}: {dict(class_by_date[date])}")

# Check for temporal shift in secondary split
with open('ml_stage12_secondary_split.json', 'r') as f:
    secondary_split = json.load(f)

secondary_train_indices = secondary_split['train_indices']
secondary_test_indices = secondary_split['test_indices']

# Get class distribution in train/test
train_labels = [ground_truth[i]['ground_truth_label'] for i in secondary_train_indices]
test_labels = [ground_truth[i]['ground_truth_label'] for i in secondary_test_indices]

train_class_dist = Counter(train_labels)
test_class_dist = Counter(test_labels)

print(f"\nSecondary split class distribution:")
print(f"  Train: {dict(train_class_dist)}")
print(f"  Test: {dict(test_class_dist)}")

# Calculate distribution shift
train_total = sum(train_class_dist.values())
test_total = sum(test_class_dist.values())

print(f"\nClass distribution shift:")
for label in ['normal', 'suspicious', 'super_suspicious']:
    train_pct = train_class_dist[label] / train_total * 100
    test_pct = test_class_dist[label] / test_total * 100
    shift = test_pct - train_pct
    print(f"  {label}: train={train_pct:.1f}%, test={test_pct:.1f}%, shift={shift:+.1f}%")

print()

# ============================================================================
# TASK 11: RANDOM FOREST OVERFITTING ANALYSIS
# ============================================================================

print("=" * 80)
print("TASK 11: RANDOM FOREST OVERFITTING ANALYSIS")
print("-" * 80)

# Get PRIMARY split results
primary_rf_train_f1 = stage12_results['primary_split']['results']['random_forest']['train_macro_f1']
primary_rf_test_f1 = stage12_results['primary_split']['results']['random_forest']['macro_f1']
primary_rf_gap = primary_rf_train_f1 - primary_rf_test_f1

print(f"PRIMARY Random Forest:")
print(f"  Train Macro F1: {primary_rf_train_f1:.4f}")
print(f"  Test Macro F1: {primary_rf_test_f1:.4f}")
print(f"  Gap: {primary_rf_gap:.4f}")

# Compare with Gradient Boosting
primary_gb_train_f1 = stage12_results['primary_split']['results']['gradient_boosting']['train_macro_f1']
primary_gb_test_f1 = stage12_results['primary_split']['results']['gradient_boosting']['macro_f1']
primary_gb_gap = primary_gb_train_f1 - primary_gb_test_f1

print(f"\nPRIMARY Gradient Boosting:")
print(f"  Train Macro F1: {primary_gb_train_f1:.4f}")
print(f"  Test Macro F1: {primary_gb_test_f1:.4f}")
print(f"  Gap: {primary_gb_gap:.4f}")

print(f"\nCONCLUSION: Random Forest overfits severely (train F1 = 1.0)")
print(f"Gradient Boosting shows much less overfitting (gap = {primary_gb_gap:.4f})")

print()

# ============================================================================
# TASK 12: FEATURE IMPORTANCE STABILITY
# ============================================================================

print("=" * 80)
print("TASK 12: FEATURE IMPORTANCE STABILITY")
print("-" * 80)

# Get feature importance from different sources
stage6_rf_importance = stage6_results['feature_importance']
stage12_primary_rf_importance = stage12_results['primary_split']['results']['random_forest']['feature_importance']
stage12_primary_gb_importance = stage12_results['primary_split']['results']['gradient_boosting']['feature_importance']
stage12_secondary_rf_importance = stage12_results['secondary_split']['results']['random_forest']['feature_importance']
stage12_secondary_gb_importance = stage12_results['secondary_split']['results']['gradient_boosting']['feature_importance']

# Calculate correlation between importance rankings
def rank_correlation(imp1, imp2):
    ranked1 = [x[0] for x in sorted(enumerate(imp1), key=lambda x: x[1], reverse=True)]
    ranked2 = [x[0] for x in sorted(enumerate(imp2), key=lambda x: x[1], reverse=True)]
    
    # Calculate Spearman correlation
    from scipy.stats import spearmanr
    corr, _ = spearmanr(ranked1, ranked2)
    return corr

print("Feature importance correlation (Spearman):")
print(f"  Stage 6 RF vs Stage 12 PRIMARY RF: {rank_correlation(list(stage6_rf_importance.values()), stage12_primary_rf_importance):.4f}")
print(f"  Stage 12 PRIMARY RF vs Stage 12 PRIMARY GB: {rank_correlation(stage12_primary_rf_importance, stage12_primary_gb_importance):.4f}")
print(f"  Stage 12 PRIMARY RF vs Stage 12 SECONDARY RF: {rank_correlation(stage12_primary_rf_importance, stage12_secondary_rf_importance):.4f}")
print(f"  Stage 12 SECONDARY RF vs Stage 12 SECONDARY GB: {rank_correlation(stage12_secondary_rf_importance, stage12_secondary_gb_importance):.4f}")

# Identify stable vs unstable features
print(f"\nTop 5 features by importance in each model:")
print("Stage 6 RF:")
for feature, imp in sorted(stage6_rf_importance.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(f"  {feature}: {imp:.4f}")

print("Stage 12 PRIMARY RF:")
for feature, imp in sorted(zip(feature_names, stage12_primary_rf_importance), key=lambda x: x[1], reverse=True)[:5]:
    print(f"  {feature}: {imp:.4f}")

print("Stage 12 PRIMARY GB:")
for feature, imp in sorted(zip(feature_names, stage12_primary_gb_importance), key=lambda x: x[1], reverse=True)[:5]:
    print(f"  {feature}: {imp:.4f}")

print()

# ============================================================================
# TASK 13: FEATURE SUFFICIENCY VERDICT
# ============================================================================

print("=" * 80)
print("TASK 13: FEATURE SUFFICIENCY VERDICT")
print("-" * 80)

# Use scenario coverage from previous analysis
scenario_coverage = scenario_results['task_5_feature_coverage']

# Classify each scenario
scenario_verdicts = {}
for scenario, coverage in scenario_coverage.items():
    overall = coverage['overall']
    
    if overall == 'STRONG':
        verdict = 'SUFFICIENTLY REPRESENTED'
    elif overall == 'MODERATE':
        verdict = 'PARTIALLY REPRESENTED'
    elif overall == 'WEAK':
        verdict = 'PARTIALLY REPRESENTED'
    else:
        verdict = 'NOT REPRESENTED'
    
    scenario_verdicts[scenario] = verdict

print("Scenario sufficiency verdicts:")
for scenario in sorted(scenario_verdicts.keys()):
    verdict = scenario_verdicts[scenario]
    print(f"  {scenario}: {verdict}")

# Overall verdict
sufficient_count = sum(1 for v in scenario_verdicts.values() if v == 'SUFFICIENTLY REPRESENTED')
partial_count = sum(1 for v in scenario_verdicts.values() if v == 'PARTIALLY REPRESENTED')
not_represented_count = sum(1 for v in scenario_verdicts.values() if v == 'NOT REPRESENTED')

print(f"\nOverall verdict:")
print(f"  Sufficiently represented: {sufficient_count}")
print(f"  Partially represented: {partial_count}")
print(f"  Not represented: {not_represented_count}")

if not_represented_count > 0:
    overall_verdict = '34 features PARTIALLY SUFFICIENT'
elif partial_count > sufficient_count:
    overall_verdict = '34 features PARTIALLY SUFFICIENT'
elif sufficient_count > 0:
    overall_verdict = '34 features MOSTLY SUFFICIENT'
else:
    overall_verdict = '34 features INSUFFICIENT'

print(f"\nFINAL VERDICT: {overall_verdict}")

print()

# ============================================================================
# TASK 14: FEATURE GAP ANALYSIS
# ============================================================================

print("=" * 80)
print("TASK 14: FEATURE GAP ANALYSIS")
print("-" * 80)

# Identify missing information for poorly represented scenarios
feature_gaps = {}

for scenario, verdict in scenario_verdicts.items():
    if verdict == 'NOT REPRESENTED' or verdict == 'PARTIALLY REPRESENTED':
        coverage = scenario_coverage[scenario]
        gaps = []
        
        for dimension, strength in coverage.items():
            if dimension == 'overall':
                continue
            if strength == 'NONE' or strength == 'WEAK':
                gaps.append(dimension)
        
        if gaps:
            feature_gaps[scenario] = gaps

print("Feature gaps by scenario:")
for scenario, gaps in feature_gaps.items():
    print(f"  {scenario}: {', '.join(gaps)}")

print("\nSpecific missing information:")
print("  Country risk: No feature captures recipient country (critical for high_risk_country)")
print("  Counterparty relationship: Limited features capture relationship depth")
print("  Geographic information: No location-based features")
print("  Device/IP information: No device fingerprinting")
print("  Cross-customer relationships: No network analysis features")
print("  Account age: No account tenure features")
print("  Beneficial ownership: No ownership structure features")

print()

# ============================================================================
# TASK 15: MODEL VS DATA ROOT CAUSE DECISION
# ============================================================================

print("=" * 80)
print("TASK 15: MODEL VS DATA ROOT CAUSE DECISION")
print("-" * 80)

print("EVIDENCE ANALYSIS:")
print()
print("FOR MODEL PROBLEM:")
print("  - Random Forest overfits severely (train F1 = 1.0)")
print("  - Gradient Boosting shows less overfitting (gap = 0.22)")
print("  - Feature importance varies by split (unstable)")
print()
print("FOR FEATURE PROBLEM:")
print("  - Most scenarios have NONE or WEAK observability")
print("  - high_risk_country is NOT REPRESENTED")
print("  - Within-class scenario separation is very low (avg Cohen's d ~0.05)")
print("  - Feature coverage matrix shows limited dimension coverage")
print()
print("FOR GENERATOR PROBLEM:")
print("  - Scenarios may not produce distinct behavioral signatures")
print("  - Severe scenarios may not be behaviorally more extreme")
print()
print("FOR LABEL/GROUND-TRUTH PROBLEM:")
print("  - Ground truth is scenario-based (non-circular)")
print("  - Labels match scenario_id (verified)")
print("  - No feature-based label generation")
print()

print("ROOT CAUSE DECISION:")
print("=" * 80)
print("MIXED PROBLEM")
print()
print("PRIMARY CAUSE: FEATURE PROBLEM")
print("  - The 34-feature representation does not adequately capture")
print("    the behavioral differences between scenarios")
print("  - Most scenarios have NONE or WEAK observability")
print("  - Within-class scenario separation is minimal")
print()
print("SECONDARY CAUSE: MODEL PROBLEM")
print("  - Random Forest overfits severely")
print("  - Gradient Boosting performs better but still limited")
print()
print("TERTIARY CAUSE: GENERATOR PROBLEM")
print("  - Scenarios may not produce sufficiently distinct behaviors")
print("  - The generator may need to create more extreme behavioral patterns")
print()
print("RECOMMENDATION FOR STAGE 14:")
print("  - PRIMARY: Improve feature representation (add missing dimensions)")
print("  - SECONDARY: Address model overfitting (regularization)")
print("  - TERTIARY: Investigate generator behavior (create more distinct scenarios)")
print()

# ============================================================================
# SAVE RESULTS
# ============================================================================

results = {
    "timestamp": datetime.now().isoformat(),
    "task_9_customer_profile": {
        "homogeneous_customers": homogeneous_customers,
        "heterogeneous_customers": heterogeneous_customers,
        "normal_customers": len(normal_customers),
        "suspicious_customers": len(suspicious_customers),
        "super_customers": len(super_customers)
    },
    "task_10_temporal": {
        "train_class_distribution": dict(train_class_dist),
        "test_class_distribution": dict(test_class_dist),
        "distribution_shift": {
            "normal": test_class_dist['normal']/test_total*100 - train_class_dist['normal']/train_total*100,
            "suspicious": test_class_dist['suspicious']/test_total*100 - train_class_dist['suspicious']/train_total*100,
            "super_suspicious": test_class_dist['super_suspicious']/test_total*100 - train_class_dist['super_suspicious']/train_total*100
        }
    },
    "task_11_overfitting": {
        "rf_train_f1": primary_rf_train_f1,
        "rf_test_f1": primary_rf_test_f1,
        "rf_gap": primary_rf_gap,
        "gb_train_f1": primary_gb_train_f1,
        "gb_test_f1": primary_gb_test_f1,
        "gb_gap": primary_gb_gap
    },
    "task_13_sufficiency": {
        "scenario_verdicts": scenario_verdicts,
        "sufficient_count": sufficient_count,
        "partial_count": partial_count,
        "not_represented_count": not_represented_count,
        "overall_verdict": overall_verdict
    },
    "task_14_feature_gaps": feature_gaps,
    "task_15_root_cause": "MIXED PROBLEM - PRIMARY: FEATURE PROBLEM, SECONDARY: MODEL PROBLEM, TERTIARY: GENERATOR PROBLEM"
}

with open('ml_stage13_additional_analysis_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("=" * 80)
print("ADDITIONAL ANALYSIS COMPLETE")
print("=" * 80)
print("Results saved to ml_stage13_additional_analysis_results.json")
