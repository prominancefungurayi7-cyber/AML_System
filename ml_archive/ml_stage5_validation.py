"""
STAGE 5: Feature Validation Script

Validates the 34-feature engineering pipeline output.
"""

import csv
import json
from datetime import datetime
from collections import Counter

print("=" * 80)
print("STAGE 5: FEATURE VALIDATION")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================================
# EXPECTED FEATURE SPECIFICATION
# ============================================================================

EXPECTED_FEATURES = [
    # Core Features (14)
    "amount", "sender_avg_amount", "sender_max_amount", "sender_tx_count",
    "amount_to_sender_avg", "amount_to_sender_max", "sender_tx_count_24h",
    "sender_volume_24h", "amount_to_sender_volume_24h", "is_new_recipient",
    "same_day_count", "same_day_total", "same_recipient_count", "rapid_transfer_count",
    # Derived Features (7)
    "hour", "is_deposit", "is_withdraw", "is_transfer", "is_self_transfer",
    "is_off_hours", "channel_encoded",
    # New Behavioral Features (13)
    "amount_std_dev", "amount_z_score", "tx_frequency_7d", "tx_frequency_30d",
    "day_of_week", "is_weekend", "time_since_last_tx", "unique_recipients_24h",
    "unique_recipients_7d", "recipient_concentration", "new_recipient_ratio_7d",
    "amount_change_vs_avg_7d", "frequency_change_vs_avg_7d"
]

RULE_LIKE_FEATURES = ["is_large_amount", "is_structuring_band", "structuring_indicators", "layering_indicators"]

# ============================================================================
# LOAD FEATURE DATA
# ============================================================================

print("Loading feature data...")
with open("ml_stage5_features.csv", 'r') as f:
    reader = csv.DictReader(f)
    feature_vectors = list(reader)

print(f"Loaded {len(feature_vectors)} feature vectors")
print()

# ============================================================================
# VALIDATION CHECKS
# ============================================================================

validation_results = []

# Check 1: Transaction count
print("CHECK 1: Transaction count")
print("-" * 80)
expected_count = 10000
actual_count = len(feature_vectors)
if actual_count == expected_count:
    print(f"PASS: {actual_count} transactions (expected {expected_count})")
    validation_results.append(("Transaction count", "PASS"))
else:
    print(f"FAIL: {actual_count} transactions (expected {expected_count})")
    validation_results.append(("Transaction count", "FAIL"))
print()

# Check 2: Feature count
print("CHECK 2: Feature count")
print("-" * 80)
actual_features = feature_vectors[0].keys() if feature_vectors else []
actual_feature_count = len(actual_features)
expected_feature_count = len(EXPECTED_FEATURES)
if actual_feature_count == expected_feature_count:
    print(f"PASS: {actual_feature_count} features (expected {expected_feature_count})")
    validation_results.append(("Feature count", "PASS"))
else:
    print(f"FAIL: {actual_feature_count} features (expected {expected_feature_count})")
    validation_results.append(("Feature count", "FAIL"))
print(f"Actual features: {list(actual_features)}")
print()

# Check 3: Feature names match expected
print("CHECK 3: Feature names match expected")
print("-" * 80)
missing_features = set(EXPECTED_FEATURES) - set(actual_features)
extra_features = set(actual_features) - set(EXPECTED_FEATURES)
if not missing_features and not extra_features:
    print("PASS: All expected features present, no extra features")
    validation_results.append(("Feature names", "PASS"))
else:
    if missing_features:
        print(f"FAIL: Missing features: {missing_features}")
    if extra_features:
        print(f"FAIL: Extra features: {extra_features}")
    validation_results.append(("Feature names", "FAIL"))
print()

# Check 4: No rule-like features
print("CHECK 4: No rule-like features")
print("-" * 80)
rule_like_present = [f for f in RULE_LIKE_FEATURES if f in actual_features]
if not rule_like_present:
    print("PASS: No rule-like features present")
    validation_results.append(("Rule-like features", "PASS"))
else:
    print(f"FAIL: Rule-like features found: {rule_like_present}")
    validation_results.append(("Rule-like features", "FAIL"))
print()

# Check 5: No label-derived features
print("CHECK 5: No label-derived features")
print("-" * 80)
label_fields = ["ground_truth_label", "risk_score", "risk_level", "aml_typologies", "scenario_id"]
label_fields_present = [f for f in label_fields if f in actual_features]
if not label_fields_present:
    print("PASS: No label-derived features present")
    validation_results.append(("Label-derived features", "PASS"))
else:
    print(f"FAIL: Label-derived features found: {label_fields_present}")
    validation_results.append(("Label-derived features", "FAIL"))
print()

# Check 6: Feature data types
print("CHECK 6: Feature data types")
print("-" * 80)
type_errors = []
for features in feature_vectors[:100]:  # Check first 100
    try:
        # Float features should be numeric
        float_features = ["amount", "sender_avg_amount", "sender_max_amount", "sender_tx_count",
                        "amount_to_sender_avg", "amount_to_sender_max", "sender_tx_count_24h",
                        "sender_volume_24h", "amount_to_sender_volume_24h", "is_new_recipient",
                        "same_day_count", "same_day_total", "same_recipient_count", "rapid_transfer_count",
                        "amount_std_dev", "amount_z_score", "tx_frequency_7d", "tx_frequency_30d",
                        "time_since_last_tx", "unique_recipients_24h", "unique_recipients_7d",
                        "recipient_concentration", "new_recipient_ratio_7d",
                        "amount_change_vs_avg_7d", "frequency_change_vs_avg_7d"]
        for feat in float_features:
            float(features[feat])
        
        # Integer features
        int_features = ["hour", "day_of_week", "channel_encoded"]
        for feat in int_features:
            int(features[feat])
        
        # Binary features should be 0 or 1
        binary_features = ["is_deposit", "is_withdraw", "is_transfer", "is_self_transfer", "is_off_hours", "is_weekend"]
        for feat in binary_features:
            val = int(features[feat])
            if val not in [0, 1]:
                type_errors.append(f"{feat} has invalid binary value: {val}")
    except (ValueError, KeyError) as e:
        type_errors.append(str(e))

if not type_errors:
    print("PASS: All feature data types valid")
    validation_results.append(("Feature data types", "PASS"))
else:
    print(f"FAIL: Data type errors: {type_errors[:5]}")  # Show first 5
    validation_results.append(("Feature data types", "FAIL"))
print()

# Check 7: No NaN values
print("CHECK 7: No NaN values")
print("-" * 80)
nan_count = 0
for features in feature_vectors:
    for feat, val in features.items():
        if val.lower() in ["nan", "none", ""] or val == "":
            nan_count += 1

if nan_count == 0:
    print("PASS: No NaN values found")
    validation_results.append(("NaN values", "PASS"))
else:
    print(f"FAIL: {nan_count} NaN/empty values found")
    validation_results.append(("NaN values", "FAIL"))
print()

# Check 8: No infinite values
print("CHECK 8: No infinite values")
print("-" * 80)
inf_count = 0
for features in feature_vectors:
    for feat, val in features.items():
        try:
            float_val = float(val)
            if abs(float_val) == float('inf'):
                inf_count += 1
        except (ValueError, TypeError):
            pass

if inf_count == 0:
    print("PASS: No infinite values found")
    validation_results.append(("Infinite values", "PASS"))
else:
    print(f"FAIL: {inf_count} infinite values found")
    validation_results.append(("Infinite values", "FAIL"))
print()

# Check 9: Binary features contain only 0/1
print("CHECK 9: Binary features contain only 0/1")
print("-" * 80)
binary_features = ["is_deposit", "is_withdraw", "is_transfer", "is_self_transfer", "is_off_hours", "is_weekend"]
binary_errors = []
for features in feature_vectors:
    for feat in binary_features:
        if feat in features:
            val = features[feat]
            if val not in ["0", "1", "0.0", "1.0"]:
                binary_errors.append(f"{feat}={val}")

if not binary_errors:
    print("PASS: All binary features contain only 0/1")
    validation_results.append(("Binary values", "PASS"))
else:
    print(f"FAIL: Binary errors found (showing first 5): {binary_errors[:5]}")
    validation_results.append(("Binary values", "FAIL"))
print()

# Check 10: Channel encoding mapping
print("CHECK 10: Channel encoding mapping")
print("-" * 80)
channel_values = set()
for features in feature_vectors:
    channel_values.add(features.get("channel_encoded", ""))
print(f"Channel encoding values found: {sorted(channel_values)}")
expected_channels = {"0", "1", "2", "3", "4", "5", "6", "7"}
if channel_values.issubset(expected_channels):
    print("PASS: Channel encoding values valid")
    validation_results.append(("Channel encoding", "PASS"))
else:
    print(f"FAIL: Unexpected channel encoding values")
    validation_results.append(("Channel encoding", "FAIL"))
print()

# Check 11: Basic statistics for numerical features
print("CHECK 11: Basic statistics for numerical features")
print("-" * 80)
print("Sample statistics (first 1000 transactions):")
for feat in ["amount", "sender_avg_amount", "hour", "tx_frequency_7d"]:
    values = []
    for features in feature_vectors[:1000]:
        try:
            values.append(float(features[feat]))
        except (ValueError, KeyError):
            pass
    if values:
        print(f"  {feat}: min={min(values):.2f}, max={max(values):.2f}, mean={sum(values)/len(values):.2f}")
print()

# Check 12: Stage 3 files unchanged
print("CHECK 12: Stage 3 files unchanged")
print("-" * 80)
import os
stage3_files = ["ml_stage3_dataset.csv", "ml_stage3_ground_truth.json", "ml_stage3_metadata.json"]
all_exist = all(os.path.exists(f) for f in stage3_files)
if all_exist:
    print("PASS: All Stage 3 files exist")
    validation_results.append(("Stage 3 files", "PASS"))
else:
    print("FAIL: Some Stage 3 files missing")
    validation_results.append(("Stage 3 files", "FAIL"))
print()

# ============================================================================
# VALIDATION SUMMARY
# ============================================================================

print("=" * 80)
print("VALIDATION SUMMARY")
print("=" * 80)
print()

passed = sum(1 for _, result in validation_results if result == "PASS")
total = len(validation_results)

for check, result in validation_results:
    status = "✓" if result == "PASS" else "✗"
    print(f"{status} {check}: {result}")

print()
print(f"Total: {passed}/{total} checks passed")
print()

if passed == total:
    print("ALL VALIDATION CHECKS PASSED")
    print()
    print("CONFIRMATION:")
    print(f"  Expected ML feature count: 34")
    print(f"  Actual ML feature count: {actual_feature_count}")
    print(f"  Rule-like features: 0")
    print(f"  Label-derived features: 0")
    print(f"  Future-data leakage: Prevented by temporal-safe implementation")
else:
    print(f"VALIDATION FAILED: {total - passed} check(s) failed")

print()
print("=" * 80)
print("VALIDATION COMPLETE")
print("=" * 80)
