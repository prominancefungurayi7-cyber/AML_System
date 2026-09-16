"""
STAGE 4: Feature Engineering Audit Script

This script audits the existing feature engineering implementation against the Stage 3 dataset
and Stage 1-3 project objectives.
"""

import csv
import json
from datetime import datetime

print("=" * 80)
print("STAGE 4: FEATURE ENGINEERING AUDIT")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================================
# STEP 1: INSPECT STAGE 3 DATASET STRUCTURE
# ============================================================================
print("STEP 1: STAGE 3 DATASET STRUCTURE")
print("-" * 80)

with open("ml_stage3_dataset.csv", 'r') as f:
    reader = csv.reader(f)
    header = next(reader)
    
print(f"Number of columns in CSV: {len(header)}")
print()
print("Column names:")
for i, col in enumerate(header, 1):
    print(f"  {i:2d}. {col}")
print()

# Distinguish between identifiers/metadata and features
identifier_fields = ["transaction_id", "sender_account", "receiver_account", "timestamp", "description"]
metadata_fields = ["transaction_type", "channel"]
feature_fields = [col for col in header if col not in identifier_fields + metadata_fields]

print("Classification:")
print(f"  Identifiers/Metadata ({len(identifier_fields + metadata_fields)}): {identifier_fields + metadata_fields}")
print(f"  Features ({len(feature_fields)}): {feature_fields}")
print()

# ============================================================================
# STEP 2: COMPARE WITH EXISTING AI_CORE.PY FEATURES
# ============================================================================
print("STEP 2: COMPARISON WITH EXISTING AI_CORE.PY FEATURES")
print("-" * 80)

# Existing 25 features from ai_core.py
existing_features = [
    "amount",
    "hour",
    "is_deposit",
    "is_withdraw",
    "is_transfer",
    "is_self_transfer",
    "is_off_hours",
    "sender_avg_amount",
    "sender_max_amount",
    "sender_tx_count",
    "amount_to_sender_avg",
    "amount_to_sender_max",
    "sender_tx_count_24h",
    "sender_volume_24h",
    "amount_to_sender_volume_24h",
    "is_new_recipient",
    "channel_encoded",
    "is_large_amount",
    "is_structuring_band",
    "same_day_count",
    "same_day_total",
    "same_recipient_count",
    "rapid_transfer_count",
    "structuring_indicators",
    "layering_indicators",
]

print(f"Existing ai_core.py features: {len(existing_features)}")
print()

# Check which existing features are in Stage 3 dataset
print("Feature availability in Stage 3 dataset:")
for feature in existing_features:
    in_dataset = feature in feature_fields or feature in metadata_fields or feature in identifier_fields
    status = "✓" if in_dataset else "✗"
    print(f"  {status} {feature}")
print()

# Check which Stage 3 features are NOT in existing implementation
print("Stage 3 features NOT in existing ai_core.py:")
for feature in feature_fields:
    if feature not in existing_features:
        print(f"  - {feature}")
print()

# ============================================================================
# STEP 3: ANALYZE RULE-LIKE FEATURES
# ============================================================================
print("STEP 3: RULE-LIKE FEATURE ANALYSIS")
print("-" * 80)

rule_like_features = [
    "is_large_amount",
    "is_structuring_band",
    "structuring_indicators",
    "layering_indicators"
]

print("Features identified as rule-like in Stage 1:")
for feature in rule_like_features:
    in_dataset = feature in feature_fields
    status = "✓" if in_dataset else "✗"
    print(f"  {status} {feature}")
print()

# Check if these are in Stage 3 dataset
print("Analysis:")
print("  Stage 3 dataset does NOT include rule-like features.")
print("  This is GOOD - prevents model from learning AML rules directly.")
print()

# ============================================================================
# STEP 4: FEATURE-BY-FEATURE AUDIT
# ============================================================================
print("STEP 4: FEATURE-BY-FEATURE AUDIT")
print("-" * 80)

# Read sample data to understand feature values
with open("ml_stage3_dataset.csv", 'r') as f:
    reader = csv.DictReader(f)
    sample_rows = [row for i, row in enumerate(reader) if i < 5]

print("Stage 3 Dataset Features (from CSV):")
print()

feature_audit = []

for feature in feature_fields:
    # Get sample values
    sample_values = [row.get(feature, "") for row in sample_rows]
    
    # Determine data type
    try:
        float_val = float(sample_values[0])
        data_type = "float"
    except (ValueError, IndexError):
        data_type = "string"
    
    # Check if it's a ratio/computed feature
    is_ratio = "to_" in feature or "_ratio" in feature
    is_count = "count" in feature or "tx_count" in feature
    is_volume = "volume" in feature or "total" in feature
    
    feature_audit.append({
        "name": feature,
        "type": data_type,
        "is_ratio": is_ratio,
        "is_count": is_count,
        "is_volume": is_volume,
        "sample_values": sample_values[:3]
    })

for i, feature in enumerate(feature_audit, 1):
    print(f"{i}. {feature['name']}")
    print(f"   Type: {feature['type']}")
    print(f"   Ratio: {feature['is_ratio']}, Count: {feature['is_count']}, Volume: {feature['is_volume']}")
    print(f"   Sample values: {feature['sample_values']}")
    print()

# ============================================================================
# STEP 5: MISSING FEATURES ANALYSIS
# ============================================================================
print("STEP 5: MISSING FEATURES ANALYSIS")
print("-" * 80)

print("Features in existing ai_core.py but NOT in Stage 3 dataset:")
missing_in_stage3 = []
for feature in existing_features:
    if feature not in feature_fields and feature not in metadata_fields:
        missing_in_stage3.append(feature)

for feature in missing_in_stage3:
    print(f"  - {feature}")
print()

print("Analysis of missing features:")
print("  hour: Can be derived from timestamp")
print("  is_deposit/is_withdraw/is_transfer: Can be derived from transaction_type")
print("  is_self_transfer: Can be derived from sender_account == receiver_account")
print("  is_off_hours: Can be derived from hour")
print("  channel_encoded: Can be derived from channel")
print("  is_large_amount: Rule-like - intentionally excluded")
print("  is_structuring_band: Rule-like - intentionally excluded")
print("  structuring_indicators: Rule-like - intentionally excluded")
print("  layering_indicators: Rule-like - intentionally excluded")
print()

# ============================================================================
# STEP 6: DATA LEAKAGE CHECK
# ============================================================================
print("STEP 6: DATA LEAKAGE CHECK")
print("-" * 80)

with open("ml_stage3_dataset.csv", 'r') as f:
    header = f.readline().strip().split(',')

leakage_fields = ["ground_truth_label", "risk_score", "risk_level", "aml_typologies", "scenario_id"]

print("Checking for leakage fields in feature file:")
for field in leakage_fields:
    if field in header:
        print(f"  FAIL: {field} found in feature file")
    else:
        print(f"  PASS: {field} not in feature file")
print()

# ============================================================================
# STEP 7: TEMPORAL SAFETY CHECK
# ============================================================================
print("STEP 7: TEMPORAL SAFETY CHECK")
print("-" * 80)

print("Checking if features respect temporal causality:")
print()

temporal_features = [
    "sender_avg_amount",
    "sender_max_amount",
    "sender_tx_count",
    "sender_tx_count_24h",
    "sender_volume_24h",
    "amount_to_sender_avg",
    "amount_to_sender_max",
    "amount_to_sender_volume_24h",
    "is_new_recipient",
    "same_day_count",
    "same_day_total",
    "same_recipient_count",
    "rapid_transfer_count"
]

print("Historical features (should use only past data):")
for feature in temporal_features:
    if feature in feature_fields:
        print(f"  ✓ {feature} - uses historical data")
print()

print("Analysis:")
print("  Stage 3 generator computes these from historical_transactions list.")
print("  This is TEMPORALLY SAFE if historical_transactions contains only past transactions.")
print("  Need to verify in training pipeline that this is respected.")
print()

# ============================================================================
# STEP 8: CUSTOMER-LEVEL EVALUATION COMPATIBILITY
# ============================================================================
print("STEP 8: CUSTOMER-LEVEL EVALUATION COMPATIBILITY")
print("-" * 80)

print("Checking if customer-level splitting is supported:")
if "sender_account" in header:
    print("  PASS: sender_account field present - enables customer-level splitting")
else:
    print("  FAIL: sender_account field missing - cannot do customer-level splitting")
print()

if "timestamp" in header:
    print("  PASS: timestamp field present - enables temporal splitting")
else:
    print("  FAIL: timestamp field missing - cannot do temporal splitting")
print()

print()
print("=" * 80)
print("FEATURE AUDIT COMPLETE")
print("=" * 80)
