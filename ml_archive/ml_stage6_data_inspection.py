"""
STAGE 6: Data Inspection and Label Alignment

Loads Stage 5 features and Stage 3 ground truth labels.
Verifies alignment, distribution, and temporal structure.
"""

import csv
import json
from datetime import datetime
from collections import Counter

print("=" * 80)
print("STAGE 6: DATA INSPECTION AND LABEL ALIGNMENT")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================================
# LOAD FEATURES
# ============================================================================

print("Loading Stage 5 features...")
with open("ml_stage5_features.csv", 'r') as f:
    reader = csv.DictReader(f)
    features = list(reader)

print(f"Loaded {len(features)} feature rows")
print(f"Feature count per row: {len(features[0])}")
print()

# ============================================================================
# LOAD GROUND TRUTH LABELS
# ============================================================================

print("Loading Stage 3 ground truth labels...")
with open("ml_stage3_ground_truth.json", 'r') as f:
    ground_truth = json.load(f)

print(f"Loaded {len(ground_truth)} label entries")
print()

# ============================================================================
# VERIFY ALIGNMENT
# ============================================================================

print("Verifying alignment between features and labels...")
print("-" * 80)

# Ground truth is a list of dicts with transaction_id
# Features are from CSV in the same order as Stage 3 dataset
# We need to verify the counts match

if len(features) == len(ground_truth):
    print(f"PASS: Feature count ({len(features)}) matches label count ({len(ground_truth)})")
else:
    print(f"FAIL: Feature count ({len(features)}) does not match label count ({len(ground_truth)})")
    print("This is a critical discrepancy - STOP and investigate")

print()

# ============================================================================
# EXAMINE LABEL DISTRIBUTION
# ============================================================================

print("Label distribution:")
print("-" * 80)

label_counts = Counter(entry["ground_truth_label"] for entry in ground_truth)
total_labels = len(ground_truth)

for label in ["normal", "suspicious", "super_suspicious"]:
    count = label_counts.get(label, 0)
    percentage = (count / total_labels) * 100 if total_labels > 0 else 0
    print(f"  {label}: {count} ({percentage:.1f}%)")

print()

# Expected distribution from Stage 3
expected = {
    "normal": 69.0,
    "suspicious": 21.6,
    "super_suspicious": 9.4
}

print("Expected distribution (from Stage 3):")
for label, expected_pct in expected.items():
    actual_pct = (label_counts.get(label, 0) / total_labels) * 100 if total_labels > 0 else 0
    diff = abs(actual_pct - expected_pct)
    status = "✓" if diff < 1.0 else "!"
    print(f"  {status} {label}: expected {expected_pct}%, actual {actual_pct:.1f}% (diff {diff:.1f}%)")

print()

# ============================================================================
# LOAD STAGE 3 DATASET FOR TEMPORAL ANALYSIS
# ============================================================================

print("Loading Stage 3 dataset for temporal analysis...")
with open("ml_stage3_dataset.csv", 'r') as f:
    reader = csv.DictReader(f)
    stage3_dataset = list(reader)

print(f"Loaded {len(stage3_dataset)} transactions from Stage 3 dataset")
print()

# ============================================================================
# EXAMINE TEMPORAL STRUCTURE
# ============================================================================

print("Temporal structure analysis:")
print("-" * 80)

timestamps = [tx["timestamp"] for tx in stage3_dataset]
timestamps_parsed = [datetime.fromisoformat(ts) for ts in timestamps]

min_date = min(timestamps_parsed)
max_date = max(timestamps_parsed)
date_range = (max_date - min_date).days

print(f"  Earliest transaction: {min_date}")
print(f"  Latest transaction: {max_date}")
print(f"  Date range: {date_range} days")
print()

# Check if timestamps are sorted
is_sorted = all(timestamps_parsed[i] <= timestamps_parsed[i+1] for i in range(len(timestamps_parsed)-1))
print(f"  Transactions sorted chronologically: {is_sorted}")
print()

# ============================================================================
# EXAMINE CUSTOMER DISTRIBUTION
# ============================================================================

print("Customer distribution:")
print("-" * 80)

customers = [tx["sender_account"] for tx in stage3_dataset]
unique_customers = len(set(customers))
print(f"  Unique customers: {unique_customers}")
print(f"  Total transactions: {len(customers)}")
print(f"  Avg transactions per customer: {len(customers) / unique_customers:.1f}")
print()

# ============================================================================
# FEATURE NAMES
# ============================================================================

print("Feature names (from Stage 5):")
print("-" * 80)
feature_names = list(features[0].keys())
for i, name in enumerate(feature_names, 1):
    print(f"  {i:2d}. {name}")

print()

print("=" * 80)
print("DATA INSPECTION COMPLETE")
print("=" * 80)
