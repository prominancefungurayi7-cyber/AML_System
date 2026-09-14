"""
STAGE 15K: FEATURE IMPORTANCE STABILITY

Compare feature importance between Stage 12 baseline and Stage 15 expanded features.
"""

import json
from datetime import datetime

print("=" * 80)
print("STAGE 15K: FEATURE IMPORTANCE STABILITY")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================================
# LOAD STAGE 15 MODEL RESULTS
# ============================================================================

print("Loading Stage 15 model results...")
with open('ml_stage15_model_results.json', 'r') as f:
    stage15_results = json.load(f)

print("Stage 15 results loaded")
print()

# ============================================================================
# LOAD STAGE 12 BASELINE RESULTS
# ============================================================================

print("Loading Stage 12 baseline results...")
with open('ml_stage12_model_results.json', 'r') as f:
    stage12_results = json.load(f)

print("Stage 12 baseline results loaded")
print()

# ============================================================================
# LOAD STAGE 15 FEATURE METADATA
# ============================================================================

print("Loading Stage 15 feature metadata...")
with open('ml_stage15_feature_metadata.json', 'r') as f:
    feature_metadata = json.load(f)

feature_names = feature_metadata['feature_names']

print("Feature metadata loaded")
print()

# ============================================================================
# EXTRACT FEATURE IMPORTANCE
# ============================================================================

print("Extracting feature importance...")

# Stage 15 feature importance
stage15_rf_importance = stage15_results['random_forest']['feature_importance']
stage15_gb_importance = stage15_results['gradient_boosting']['feature_importance']

# Stage 12 baseline feature importance
stage12_rf_importance = stage12_results['primary_split']['results'].get('random_forest', {}).get('feature_importance', [])
stage12_gb_importance = stage12_results['primary_split']['results'].get('gradient_boosting', {}).get('feature_importance', [])

print("Feature importance extracted")
print()

# ============================================================================
# ANALYZE FEATURE IMPORTANCE
# ============================================================================

print("Analyzing feature importance...")
print()

print("STAGE 15 TOP 10 FEATURES (Random Forest):")
print("-" * 80)

# Create list of (feature_name, importance) pairs
rf_importance_pairs = list(zip(feature_names, stage15_rf_importance))
rf_importance_pairs.sort(key=lambda x: x[1], reverse=True)

for i, (feature, importance) in enumerate(rf_importance_pairs[:10]):
    print(f"  {i+1:2}. {feature:40} {importance:.4f}")

print()

print("STAGE 15 TOP 10 FEATURES (Gradient Boosting):")
print("-" * 80)

gb_importance_pairs = list(zip(feature_names, stage15_gb_importance))
gb_importance_pairs.sort(key=lambda x: x[1], reverse=True)

for i, (feature, importance) in enumerate(gb_importance_pairs[:10]):
    print(f"  {i+1:2}. {feature:40} {importance:.4f}")

print()

# ============================================================================
# IDENTIFY DOMINANT NEW FEATURES
# ============================================================================

print("DOMINANT NEW FEATURES:")
print("-" * 80)

new_features = [
    'threshold_proximity_10k', 'threshold_proximity_5k', 'near_threshold_count_7d',
    'near_threshold_ratio_7d', 'amount_clustering_score', 'counterparty_diversity_7d',
    'counterparty_diversity_30d', 'pass_through_ratio_7d', 'rapid_counterparty_switch_count',
    'single_counterparty_dominance_7d', 'inbound_aggregation_7d', 'outbound_diversification_7d',
    'many_to_one_ratio_7d', 'concentration_index_7d', 'inbound_to_outbound_time_avg_7d',
    'same_day_pass_through_count_7d', 'funds_through_ratio_7d', 'velocity_score_7d',
    'amount_deviation_from_baseline_30d', 'frequency_deviation_from_baseline_30d',
    'counterparty_change_score_7d', 'rolling_behavioral_change_7d',
    'concurrent_suspicious_indicators', 'typology_aggregation_score', 'severity_index'
]

print("Random Forest - Top New Features:")
rf_new_importance = [(f, imp) for f, imp in rf_importance_pairs if f in new_features]
rf_new_importance.sort(key=lambda x: x[1], reverse=True)

for i, (feature, importance) in enumerate(rf_new_importance[:5]):
    print(f"  {i+1:2}. {feature:40} {importance:.4f}")

print()

print("Gradient Boosting - Top New Features:")
gb_new_importance = [(f, imp) for f, imp in gb_importance_pairs if f in new_features]
gb_new_importance.sort(key=lambda x: x[1], reverse=True)

for i, (feature, importance) in enumerate(gb_new_importance[:5]):
    print(f"  {i+1:2}. {feature:40} {importance:.4f}")

print()

# ============================================================================
# IDENTIFY UNSTABLE FEATURES
# ============================================================================

print("FEATURE IMPORTANCE STABILITY:")
print("-" * 80)

print("Comparing Random Forest vs Gradient Boosting importance:")

# Calculate correlation between RF and GB importance
import numpy as np

rf_imp_array = np.array(stage15_rf_importance)
gb_imp_array = np.array(stage15_gb_importance)

correlation = np.corrcoef(rf_imp_array, gb_imp_array)[0, 1]

print(f"  Correlation between RF and GB importance: {correlation:.4f}")

if correlation > 0.7:
    print("  HIGH STABILITY (correlation > 0.7)")
elif correlation > 0.5:
    print("  MODERATE STABILITY (correlation > 0.5)")
else:
    print("  LOW STABILITY (correlation <= 0.5)")

print()

# ============================================================================
# IDENTIFY FEATURES WITH NEGLIGIBLE IMPORTANCE
# ============================================================================

print("FEATURES WITH NEGLIGIBLE IMPORTANCE:")
print("-" * 80)

negligible_threshold = 0.01

rf_negligible = [(f, imp) for f, imp in rf_importance_pairs if imp < negligible_threshold]
gb_negligible = [(f, imp) for f, imp in gb_importance_pairs if imp < negligible_threshold]

print(f"Random Forest: {len(rf_negligible)} features with importance < 0.01")
for feature, importance in rf_negligible[:10]:
    print(f"  {feature:40} {importance:.4f}")

print()

print(f"Gradient Boosting: {len(gb_negligible)} features with importance < 0.01")
for feature, importance in gb_negligible[:10]:
    print(f"  {feature:40} {importance:.4f}")

print()

# ============================================================================
# SAVE RESULTS
# ============================================================================

results = {
    "timestamp": datetime.now().isoformat(),
    "stage15_rf_top_features": [(f, imp) for f, imp in rf_importance_pairs[:10]],
    "stage15_gb_top_features": [(f, imp) for f, imp in gb_importance_pairs[:10]],
    "stage15_rf_top_new_features": [(f, imp) for f, imp in rf_new_importance[:5]],
    "stage15_gb_top_new_features": [(f, imp) for f, imp in gb_new_importance[:5]],
    "rf_gb_correlation": correlation,
    "stability_level": "HIGH" if correlation > 0.7 else "MODERATE" if correlation > 0.5 else "LOW",
    "rf_negligible_count": len(rf_negligible),
    "gb_negligible_count": len(gb_negligible),
    "rf_negligible_features": [(f, imp) for f, imp in rf_negligible],
    "gb_negligible_features": [(f, imp) for f, imp in gb_negligible]
}

with open('ml_stage15_feature_importance_stability_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("=" * 80)
print("FEATURE IMPORTANCE STABILITY COMPLETE")
print("=" * 80)
print("Results saved to ml_stage15_feature_importance_stability_results.json")
