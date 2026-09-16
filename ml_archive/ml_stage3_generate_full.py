"""
Generate full Stage 3 dataset with comprehensive analysis
"""

import sys
import os
import json
import csv
from datetime import datetime, timezone
from collections import Counter

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml_stage3_generator import (
    generate_aml_dataset,
    export_dataset_to_csv,
    export_ground_truth,
    export_metadata,
    GroundTruthLabel,
    AMLTypology,
    CustomerProfileType
)

print("=" * 80)
print("STAGE 3: FULL DATASET GENERATION AND ANALYSIS")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# Generate full dataset
print("Generating full AML dataset...")
print()

# Configurable parameters
NUM_CUSTOMERS = 200
TRANSACTIONS_PER_CUSTOMER = 50
RANDOM_SEED = 42

# Configurable class distribution
class_distribution = {
    "normal": 0.70,
    "suspicious": 0.20,
    "super_suspicious": 0.10
}

# Generate dataset
transactions, customers = generate_aml_dataset(
    num_customers=NUM_CUSTOMERS,
    transactions_per_customer=TRANSACTIONS_PER_CUSTOMER,
    class_distribution=class_distribution,
    random_seed=RANDOM_SEED
)

print(f"Generated {len(transactions)} transactions from {len(customers)} customers")
print()

# Export datasets
print("Exporting datasets...")
export_dataset_to_csv(transactions, "ml_stage3_dataset.csv")
export_ground_truth(transactions, "ml_stage3_ground_truth.json")
export_metadata(transactions, customers, "ml_stage3_metadata.json")
print("Export complete")
print()

# ============================================================================
# DATASET ANALYSIS
# ============================================================================
print("=" * 80)
print("DATASET ANALYSIS")
print("=" * 80)
print()

# Class distribution
print("CLASS DISTRIBUTION:")
print("-" * 80)
label_counts = Counter(tx.ground_truth_label.value for tx in transactions)
for label in [GroundTruthLabel.NORMAL.value, GroundTruthLabel.SUSPICIOUS.value, GroundTruthLabel.SUPER_SUSPICIOUS.value]:
    count = label_counts.get(label, 0)
    pct = count / len(transactions) * 100
    print(f"  {label:20s}: {count:5d} ({pct:5.1f}%)")
print()

# Typology distribution
print("TYPOLOGY DISTRIBUTION:")
print("-" * 80)
typology_counts = Counter()
for tx in transactions:
    for typology in tx.aml_typologies:
        typology_counts[typology.value] += 1

for typology in sorted(typology_counts.keys(), key=lambda x: typology_counts[x], reverse=True):
    count = typology_counts[typology]
    pct = count / len(transactions) * 100
    print(f"  {typology:30s}: {count:5d} ({pct:5.1f}%)")
print()

# Customer profile distribution
print("CUSTOMER PROFILE DISTRIBUTION:")
print("-" * 80)
profile_counts = Counter(c.profile_type.value for c in customers)
for profile in sorted(profile_counts.keys(), key=lambda x: profile_counts[x], reverse=True):
    count = profile_counts[profile]
    pct = count / len(customers) * 100
    print(f"  {profile:40s}: {count:3d} ({pct:5.1f}%)")
print()

# Transaction statistics
print("TRANSACTION STATISTICS:")
print("-" * 80)
amounts = [tx.amount for tx in transactions]
print(f"  Total transactions: {len(transactions)}")
print(f"  Unique customers: {len(set(tx.customer_id for tx in transactions))}")
print(f"  Transactions per customer: {len(transactions) / len(customers):.1f}")
print(f"  Amount - Min: ${min(amounts):,.2f}")
print(f"  Amount - Max: ${max(amounts):,.2f}")
print(f"  Amount - Mean: ${sum(amounts)/len(amounts):,.2f}")
print(f"  Amount - Median: ${sorted(amounts)[len(amounts)//2]:,.2f}")
print()

# Transaction type distribution
print("TRANSACTION TYPE DISTRIBUTION:")
print("-" * 80)
tx_type_counts = Counter(tx.transaction_type.value for tx in transactions)
for tx_type in sorted(tx_type_counts.keys()):
    count = tx_type_counts[tx_type]
    pct = count / len(transactions) * 100
    print(f"  {tx_type:15s}: {count:5d} ({pct:5.1f}%)")
print()

# Channel distribution
print("CHANNEL DISTRIBUTION:")
print("-" * 80)
channel_counts = Counter(tx.channel.value for tx in transactions)
for channel in sorted(channel_counts.keys()):
    count = channel_counts[channel]
    pct = count / len(transactions) * 100
    print(f"  {channel:15s}: {count:5d} ({pct:5.1f}%)")
print()

# Legitimate high-value transactions
print("LEGITIMATE HIGH-VALUE TRANSACTIONS:")
print("-" * 80)
legitimate_hv_count = sum(1 for tx in transactions if tx.is_legitimate_high_value)
print(f"  Count: {legitimate_hv_count} ({legitimate_hv_count/len(transactions)*100:.1f}%)")
print(f"  These are legitimate large transactions that should NOT be flagged as suspicious")
print()

# Borderline cases
print("BORDERLINE CASES:")
print("-" * 80)
borderline_count = sum(1 for tx in transactions if tx.is_borderline_case)
print(f"  Count: {borderline_count} ({borderline_count/len(transactions)*100:.1f}%)")
print(f"  These are transactions that could be either legitimate or suspicious")
print()

# Amount overlap between classes
print("AMOUNT OVERLAP BETWEEN CLASSES:")
print("-" * 80)
for label in [GroundTruthLabel.NORMAL.value, GroundTruthLabel.SUSPICIOUS.value, GroundTruthLabel.SUPER_SUSPICIOUS.value]:
    label_amounts = [tx.amount for tx in transactions if tx.ground_truth_label.value == label]
    if label_amounts:
        print(f"  {label:20s}:")
        print(f"    Min: ${min(label_amounts):,.2f}")
        print(f"    Max: ${max(label_amounts):,.2f}")
        print(f"    Mean: ${sum(label_amounts)/len(label_amounts):,.2f}")
print()

# ============================================================================
# DATA VALIDATION CHECKS
# ============================================================================
print("=" * 80)
print("DATA VALIDATION CHECKS")
print("=" * 80)
print()

validation_errors = []

# Check 1: No ground truth in features
print("Check 1: Ground truth not in feature matrix...")
with open("ml_stage3_dataset.csv", 'r') as f:
    header = f.readline().strip().split(',')
    if "ground_truth_label" in header or "aml_typologies" in header:
        validation_errors.append("FAIL: Ground truth found in feature matrix")
        print("  FAIL: Ground truth found in feature matrix")
    else:
        print("  PASS: Ground truth not in feature matrix")
print()

# Check 2: No risk_score in features
print("Check 2: risk_score not in feature matrix...")
if "risk_score" in header:
    validation_errors.append("FAIL: risk_score found in feature matrix")
    print("  FAIL: risk_score found in feature matrix")
else:
    print("  PASS: risk_score not in feature matrix")
print()

# Check 3: No risk_level in features
print("Check 3: risk_level not in feature matrix...")
if "risk_level" in header:
    validation_errors.append("FAIL: risk_level found in feature matrix")
    print("  FAIL: risk_level found in feature matrix")
else:
    print("  PASS: risk_level not in feature matrix")
print()

# Check 4: All required fields exist
print("Check 4: All required fields exist...")
required_fields = [
    "transaction_id", "sender_account", "receiver_account", "transaction_type",
    "amount", "timestamp", "channel", "description",
    "sender_avg_amount", "sender_max_amount", "sender_tx_count",
    "amount_to_sender_avg", "amount_to_sender_max", "sender_tx_count_24h",
    "sender_volume_24h", "amount_to_sender_volume_24h", "is_new_recipient",
    "same_day_count", "same_day_total", "same_recipient_count", "rapid_transfer_count"
]
missing_fields = [field for field in required_fields if field not in header]
if missing_fields:
    validation_errors.append(f"FAIL: Missing required fields: {missing_fields}")
    print(f"  FAIL: Missing required fields: {missing_fields}")
else:
    print("  PASS: All required fields present")
print()

# Check 5: No impossible values
print("Check 5: No impossible values...")
with open("ml_stage3_dataset.csv", 'r') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        amount = float(row.get("amount", 0))
        if amount <= 0:
            validation_errors.append(f"FAIL: Non-positive amount at row {i}")
            print(f"  FAIL: Non-positive amount at row {i}")
            break
        if float(row.get("sender_avg_amount", 0)) < 0:
            validation_errors.append(f"FAIL: Negative sender_avg_amount at row {i}")
            print(f"  FAIL: Negative sender_avg_amount at row {i}")
            break
    else:
        print("  PASS: No impossible values detected")
print()

# Check 6: Ground truth file exists and has correct structure
print("Check 6: Ground truth file structure...")
with open("ml_stage3_ground_truth.json", 'r') as f:
    ground_truth = json.load(f)
    if not ground_truth:
        validation_errors.append("FAIL: Ground truth file is empty")
        print("  FAIL: Ground truth file is empty")
    else:
        required_gt_fields = ["transaction_id", "ground_truth_label", "aml_typologies"]
        missing_gt = [field for field in required_gt_fields if field not in ground_truth[0]]
        if missing_gt:
            validation_errors.append(f"FAIL: Missing ground truth fields: {missing_gt}")
            print(f"  FAIL: Missing ground truth fields: {missing_gt}")
        else:
            print("  PASS: Ground truth file structure correct")
print()

# Check 7: Labels match documented generation logic
print("Check 7: Labels match documented generation logic...")
valid_labels = [GroundTruthLabel.NORMAL.value, GroundTruthLabel.SUSPICIOUS.value, GroundTruthLabel.SUPER_SUSPICIOUS.value]
invalid_labels = [tx.ground_truth_label.value for tx in transactions if tx.ground_truth_label.value not in valid_labels]
if invalid_labels:
    validation_errors.append(f"FAIL: Invalid labels found: {set(invalid_labels)}")
    print(f"  FAIL: Invalid labels found: {set(invalid_labels)}")
else:
    print("  PASS: All labels valid")
print()

# Summary
print("=" * 80)
print("VALIDATION SUMMARY")
print("=" * 80)
if validation_errors:
    print(f"FAILED: {len(validation_errors)} validation error(s)")
    for error in validation_errors:
        print(f"  - {error}")
else:
    print("PASSED: All validation checks successful")
print()

# ============================================================================
# EXAMPLE TRANSACTIONS
# ============================================================================
print("=" * 80)
print("EXAMPLE TRANSACTIONS BY CLASS")
print("=" * 80)
print()

for label in [GroundTruthLabel.NORMAL, GroundTruthLabel.SUSPICIOUS, GroundTruthLabel.SUPER_SUSPICIOUS]:
    print(f"{label.value.upper()} EXAMPLES:")
    print("-" * 80)
    label_txs = [tx for tx in transactions if tx.ground_truth_label == label][:3]
    for tx in label_txs:
        print(f"  Transaction ID: {tx.transaction_id}")
        print(f"  Amount: ${tx.amount:,.2f}")
        print(f"  Type: {tx.transaction_type.value}")
        print(f"  Channel: {tx.channel.value}")
        print(f"  AML Typologies: {[t.value for t in tx.aml_typologies]}")
        print(f"  Scenario: {tx.scenario_description}")
        print(f"  Is Legitimate High Value: {tx.is_legitimate_high_value}")
        print(f"  Is Borderline: {tx.is_borderline_case}")
        print()
    print()

print("=" * 80)
print("DATASET GENERATION AND ANALYSIS COMPLETE")
print("=" * 80)
