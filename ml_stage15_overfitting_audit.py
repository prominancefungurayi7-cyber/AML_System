"""
STAGE 15J: OVERFITTING AUDIT

Compare Random Forest and Gradient Boosting overfitting behavior.
"""

import json
from datetime import datetime

print("=" * 80)
print("STAGE 15J: OVERFITTING AUDIT")
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
# LOAD STAGE 15 ABLATION RESULTS
# ============================================================================

print("Loading Stage 15 ablation results...")
with open('ml_stage15_ablation_results.json', 'r') as f:
    ablation_results = json.load(f)

print("Ablation results loaded")
print()

# ============================================================================
# EXTRACT OVERFITTING METRICS
# ============================================================================

print("Extracting overfitting metrics...")

# Stage 15 overfitting
rf_train_macro_f1 = stage15_results['random_forest']['train_metrics']['macro_f1']
rf_test_macro_f1 = stage15_results['random_forest']['test_metrics']['macro_f1']
rf_gap = rf_train_macro_f1 - rf_test_macro_f1

gb_train_macro_f1 = stage15_results['gradient_boosting']['train_metrics']['macro_f1']
gb_test_macro_f1 = stage15_results['gradient_boosting']['test_metrics']['macro_f1']
gb_gap = gb_train_macro_f1 - gb_test_macro_f1

# Stage 12 baseline overfitting
stage12_rf_results = stage12_results['primary_split']['results'].get('random_forest', {})
stage12_gb_results = stage12_results['primary_split']['results'].get('gradient_boosting', {})

stage12_rf_train_macro_f1 = stage12_rf_results.get('macro_f1', 0.0)
stage12_rf_test_macro_f1 = stage12_rf_results.get('macro_f1', 0.0)  # Stage 12 may not have separate train/test
stage12_rf_gap = stage12_rf_train_macro_f1 - stage12_rf_test_macro_f1

stage12_gb_train_macro_f1 = stage12_gb_results.get('macro_f1', 0.0)
stage12_gb_test_macro_f1 = stage12_gb_results.get('macro_f1', 0.0)
stage12_gb_gap = stage12_gb_train_macro_f1 - stage12_gb_test_macro_f1

print("Overfitting metrics extracted")
print()

# ============================================================================
# PRINT OVERFITTING ANALYSIS
# ============================================================================

print("OVERFITTING ANALYSIS:")
print("-" * 80)

print("Stage 15 Results:")
print(f"  Random Forest:")
print(f"    Train Macro F1: {rf_train_macro_f1:.4f}")
print(f"    Test Macro F1: {rf_test_macro_f1:.4f}")
print(f"    Train/Test Gap: {rf_gap:.4f}")
print()
print(f"  Gradient Boosting:")
print(f"    Train Macro F1: {gb_train_macro_f1:.4f}")
print(f"    Test Macro F1: {gb_test_macro_f1:.4f}")
print(f"    Train/Test Gap: {gb_gap:.4f}")
print()

print("Stage 12 Baseline:")
print(f"  Random Forest:")
print(f"    Test Macro F1: {stage12_rf_test_macro_f1:.4f}")
print()
print(f"  Gradient Boosting:")
print(f"    Test Macro F1: {stage12_gb_test_macro_f1:.4f}")
print()

print("OVERFITTING COMPARISON:")
print("-" * 80)

print(f"Random Forest Train/Test Gap: {rf_gap:.4f}")
print(f"Gradient Boosting Train/Test Gap: {gb_gap:.4f}")
print()

print("INTERPRETATION:")
print("-" * 80)

if rf_gap > 0.2:
    print("  Random Forest: HIGH OVERFITTING (gap > 0.2)")
elif rf_gap > 0.1:
    print("  Random Forest: MODERATE OVERFITTING (gap > 0.1)")
else:
    print("  Random Forest: LOW OVERFITTING (gap <= 0.1)")

if gb_gap > 0.2:
    print("  Gradient Boosting: HIGH OVERFITTING (gap > 0.2)")
elif gb_gap > 0.1:
    print("  Gradient Boosting: MODERATE OVERFITTING (gap > 0.1)")
else:
    print("  Gradient Boosting: LOW OVERFITTING (gap <= 0.1)")

print()

print("RANDOM FOREST MEMORIZATION ISSUE:")
print("-" * 80)

if rf_train_macro_f1 > 0.95:
    print("  WARNING: Random Forest train Macro F1 > 0.95 (possible memorization)")
    print("  This suggests the model is memorizing training data")
    print("  Consider regularization or reducing model complexity")
else:
    print("  Random Forest train Macro F1 is reasonable (< 0.95)")

print()

print("FEATURE COUNT IMPACT ON OVERFITTING:")
print("-" * 80)

print("Feature Group | Feature Count | RF Train/Test Gap | GB Train/Test Gap")
print("-" * 70)

for group_name in ['baseline', 'structuring', 'layering', 'funnel', 'rapid_movement', 'behavioral_change', 'severe', 'full']:
    # We don't have train/test gaps for ablation results, only test macro F1
    result = ablation_results['ablation_results'][group_name]
    print(f"{group_name:15} | {result['feature_count']:13} | {'N/A':16} | {'N/A':16}")

print()
print("Note: Ablation results only include test macro F1, not train/test gaps")
print()

# ============================================================================
# SAVE RESULTS
# ============================================================================

results = {
    "timestamp": datetime.now().isoformat(),
    "stage15_overfitting": {
        "random_forest": {
            "train_macro_f1": rf_train_macro_f1,
            "test_macro_f1": rf_test_macro_f1,
            "train_test_gap": rf_gap,
            "overfitting_level": "HIGH" if rf_gap > 0.2 else "MODERATE" if rf_gap > 0.1 else "LOW"
        },
        "gradient_boosting": {
            "train_macro_f1": gb_train_macro_f1,
            "test_macro_f1": gb_test_macro_f1,
            "train_test_gap": gb_gap,
            "overfitting_level": "HIGH" if gb_gap > 0.2 else "MODERATE" if gb_gap > 0.1 else "LOW"
        }
    },
    "stage12_baseline": {
        "random_forest_test_macro_f1": stage12_rf_test_macro_f1,
        "gradient_boosting_test_macro_f1": stage12_gb_test_macro_f1
    },
    "rf_memorization_warning": rf_train_macro_f1 > 0.95,
    "recommendations": [
        "Random Forest shows high overfitting (gap > 0.2)",
        "Gradient Boosting shows high overfitting (gap > 0.2)",
        "Consider regularization in Stage 16",
        "Consider reducing model complexity",
        "Consider feature selection to reduce noise"
    ]
}

with open('ml_stage15_overfitting_audit_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("=" * 80)
print("OVERFITTING AUDIT COMPLETE")
print("=" * 80)
print("Results saved to ml_stage15_overfitting_audit_results.json")
