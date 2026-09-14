"""
STAGE 15E: SCENARIO OBSERVABILITY VALIDATION

Compare scenario observability between Stage 13 (34 features) and Stage 15 (57 features).
"""

import csv
import json
import numpy as np
from datetime import datetime
from scipy import stats

print("=" * 80)
print("STAGE 15E: SCENARIO OBSERVABILITY VALIDATION")
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
# LOAD STAGE 13 BASELINE RESULTS
# ============================================================================

print("Loading Stage 13 baseline results...")
with open('ml_stage13_scenario_analysis_results.json', 'r') as f:
    stage13_results = json.load(f)

print("Loaded Stage 13 baseline results")
print()

# ============================================================================
# LOAD FEATURE METADATA
# ============================================================================

with open('ml_stage15_feature_metadata.json', 'r') as f:
    metadata = json.load(f)

feature_names = metadata['feature_names']

# ============================================================================
# MERGE FEATURES WITH GROUND TRUTH
# ============================================================================

print("Merging features with ground truth...")

# Create mapping from transaction_id to ground truth
# Convert transaction_id to string for consistent matching
gt_map = {str(gt['transaction_id']): gt for gt in ground_truth}

# Merge
merged_data = []
for feature in features:
    tx_id = str(feature['transaction_id'])
    if tx_id in gt_map:
        merged = {**feature, **gt_map[tx_id]}
        merged_data.append(merged)

print(f"Merged {len(merged_data)} transactions")

if len(merged_data) == 0:
    print("DEBUG: Checking transaction_id formats...")
    print(f"First feature transaction_id: {features[0]['transaction_id']}")
    print(f"First ground truth transaction_id: {ground_truth[0]['transaction_id']}")
    print(f"Feature transaction_id type: {type(features[0]['transaction_id'])}")
    print(f"Ground truth transaction_id type: {type(ground_truth[0]['transaction_id'])}")

print()

# ============================================================================
# GROUP BY SCENARIO
# ============================================================================

print("Grouping by scenario...")

scenario_groups = {}
for data in merged_data:
    scenario_id = data['scenario_id']
    # Extract scenario type (before underscore)
    scenario_type = scenario_id.split('_')[0] if '_' in scenario_id else scenario_id
    if scenario_type not in scenario_groups:
        scenario_groups[scenario_type] = []
    scenario_groups[scenario_type].append(data)

print(f"Found {len(scenario_groups)} scenario types")
for scenario, data in scenario_groups.items():
    print(f"  {scenario}: {len(data)} transactions")

print()

# ============================================================================
# COMPUTE COHEN'S D FOR EACH SCENARIO VS NORMAL
# ============================================================================

print("Computing Cohen's d for each scenario vs normal...")

def compute_cohens_d(group1_values, group2_values):
    """Compute Cohen's d between two groups."""
    mean1 = np.mean(group1_values)
    mean2 = np.mean(group2_values)
    std1 = np.std(group1_values)
    std2 = np.std(group2_values)
    
    # Pooled standard deviation
    n1 = len(group1_values)
    n2 = len(group2_values)
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return abs(mean1 - mean2) / pooled_std

# Get normal group
normal_group = scenario_groups.get('normal', [])

if not normal_group:
    print("ERROR: No normal group found")
else:
    print(f"Normal group: {len(normal_group)} transactions")

print()

# Compute Cohen's d for each scenario
cohens_d_results = {}

for scenario, group in scenario_groups.items():
    if scenario == 'normal':
        continue
    
    print(f"Computing Cohen's d for {scenario} vs normal...")
    
    # Compute Cohen's d for each feature
    feature_cohens_d = {}
    
    for feature_name in feature_names:
        normal_values = [float(f[feature_name]) for f in normal_group]
        scenario_values = [float(f[feature_name]) for f in group]
        
        # Remove NaN/inf values
        normal_values = [v for v in normal_values if not np.isnan(v) and not np.isinf(v)]
        scenario_values = [v for v in scenario_values if not np.isnan(v) and not np.isinf(v)]
        
        if len(normal_values) > 0 and len(scenario_values) > 0:
            cohens_d = compute_cohens_d(normal_values, scenario_values)
            feature_cohens_d[feature_name] = cohens_d
    
    # Compute average Cohen's d across all features
    avg_cohens_d = np.mean(list(feature_cohens_d.values())) if feature_cohens_d else 0.0
    
    cohens_d_results[scenario] = {
        'avg_cohens_d': avg_cohens_d,
        'feature_cohens_d': feature_cohens_d,
        'transaction_count': len(group)
    }
    
    print(f"  Average Cohen's d: {avg_cohens_d:.4f}")

print()

# ============================================================================
# COMPARE WITH STAGE 13 BASELINE
# ============================================================================

print("Comparing with Stage 13 baseline...")
print()

# Map actual scenario types to expected scenario names
scenario_mapping = {
    'structuring': 'structuring',
    'layering': 'layering',
    'funnel': 'funnel',
    'rapid': 'rapid_movement',
    'behavioral': 'behavioral_change',
    'high': 'high_risk_country',
    'severe': 'multiple_typologies',  # Map severe to multiple_typologies for comparison
    'multiple': 'multiple_typologies'
}

stage13_baseline = {
    'structuring': 0.0,
    'layering': 0.2,
    'funnel': 0.0,
    'rapid_movement': 0.2,
    'behavioral_change': 0.0,
    'high_risk_country': 0.0,
    'multiple_typologies': 0.4
}

print("Scenario | Stage 13 Cohen's d | Stage 15 Cohen's d | Improvement")
print("-" * 70)

improvements = []

for actual_scenario, expected_scenario in scenario_mapping.items():
    if actual_scenario not in cohens_d_results:
        continue
    
    stage13_cohens_d = stage13_baseline.get(expected_scenario, 0.0)
    stage15_cohens_d = cohens_d_results[actual_scenario]['avg_cohens_d']
    improvement = stage15_cohens_d - stage13_cohens_d
    improvements.append((expected_scenario, stage13_cohens_d, stage15_cohens_d, improvement))
    
    improvement_str = "YES" if improvement > 0 else "NO"
    print(f"{expected_scenario:20} | {stage13_cohens_d:18.4f} | {stage15_cohens_d:18.4f} | {improvement_str}")

print()

# ============================================================================
# CLASSIFY OBSERVABILITY
# ============================================================================

print("OBSERVABILITY CLASSIFICATION:")
print("-" * 80)

def classify_observability(cohens_d):
    if cohens_d < 0.2:
        return "NONE"
    elif cohens_d < 0.5:
        return "WEAK"
    elif cohens_d < 0.8:
        return "MODERATE"
    else:
        return "STRONG"

print("Scenario | Stage 13 Observability | Stage 15 Observability | Improvement")
print("-" * 80)

for scenario, stage13_cohens_d, stage15_cohens_d, improvement in improvements:
    stage13_obs = classify_observability(stage13_cohens_d)
    stage15_obs = classify_observability(stage15_cohens_d)
    improvement_str = "YES" if stage15_obs != stage13_obs else "NO"
    print(f"{scenario:20} | {stage13_obs:22} | {stage15_obs:22} | {improvement_str}")

print()

# ============================================================================
# SAVE RESULTS
# ============================================================================

results = {
    "timestamp": datetime.now().isoformat(),
    "total_features": len(feature_names),
    "cohens_d_results": cohens_d_results,
    "stage13_baseline": stage13_baseline,
    "improvements": [
        {
            "scenario": scenario,
            "stage13_cohens_d": stage13_cohens_d,
            "stage15_cohens_d": stage15_cohens_d,
            "improvement": improvement,
            "stage13_observability": classify_observability(stage13_cohens_d),
            "stage15_observability": classify_observability(stage15_cohens_d)
        }
        for scenario, stage13_cohens_d, stage15_cohens_d, improvement in improvements
    ]
}

with open('ml_stage15_scenario_observability_results.json', 'w') as f:
    json.dump(results, f, indent=2)

# ============================================================================
# SAVE CSV
# ============================================================================

with open('ml_stage15_scenario_observability.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['scenario', 'stage13_cohens_d', 'stage15_cohens_d', 'improvement', 'stage13_observability', 'stage15_observability'])
    for scenario, stage13_cohens_d, stage15_cohens_d, improvement in improvements:
        writer.writerow([
            scenario,
            stage13_cohens_d,
            stage15_cohens_d,
            improvement,
            classify_observability(stage13_cohens_d),
            classify_observability(stage15_cohens_d)
        ])

print("=" * 80)
print("SCENARIO OBSERVABILITY VALIDATION COMPLETE")
print("=" * 80)
print("Results saved to ml_stage15_scenario_observability_results.json")
print("CSV saved to ml_stage15_scenario_observability.csv")
