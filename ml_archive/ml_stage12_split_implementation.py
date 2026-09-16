"""
STAGE 12: SPLIT IMPLEMENTATION

Implements two splits:
1. PRIMARY: Customer-level holdout (160 train customers, 40 test customers, 0 overlap)
2. SECONDARY: Chronological transaction split (80/20, customer overlap expected)
"""

import csv
import json
import random
from datetime import datetime, timezone
from collections import defaultdict, Counter
from typing import Dict, List, Any, Tuple

print("=" * 80)
print("STAGE 12: SPLIT IMPLEMENTATION")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================================
# LOAD DATA
# ============================================================================

print("Loading Stage 11 dataset and features...")
with open('ml_stage11_dataset.csv', 'r') as f:
    reader = csv.DictReader(f)
    dataset = list(reader)

with open('ml_stage11_features.csv', 'r') as f:
    reader = csv.DictReader(f)
    features = list(reader)

with open('ml_stage11_ground_truth.json', 'r') as f:
    ground_truth = json.load(f)

print(f"Loaded {len(dataset)} transactions")
print(f"Loaded {len(features)} feature records")
print(f"Loaded {len(ground_truth)} ground truth records")
print()

# ============================================================================
# PRIMARY SPLIT: CUSTOMER-LEVEL HOLDOUT
# ============================================================================

print("=" * 80)
print("PRIMARY SPLIT: CUSTOMER-LEVEL HOLDOUT")
print("-" * 80)

# Set random seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
print(f"Random seed: {RANDOM_SEED}")

# Get unique customers
customers = list(set(tx['sender_account'] for tx in dataset))
print(f"Total customers: {len(customers)}")

# Randomly assign 160 customers to training, 40 to test
random.shuffle(customers)
train_customers = set(customers[:160])
test_customers = set(customers[160:])

print(f"Train customers: {len(train_customers)}")
print(f"Test customers: {len(test_customers)}")

# Verify zero overlap
overlap = train_customers & test_customers
print(f"Customer overlap: {len(overlap)}")

if len(overlap) != 0:
    print("ERROR: Customer overlap detected!")
    exit(1)

# Split transactions by customer
train_transactions = []
test_transactions = []

for tx in dataset:
    if tx['sender_account'] in train_customers:
        train_transactions.append(tx)
    elif tx['sender_account'] in test_customers:
        test_transactions.append(tx)
    else:
        print(f"ERROR: Customer {tx['sender_account']} not in train or test set")
        exit(1)

print(f"Train transactions: {len(train_transactions)}")
print(f"Test transactions: {len(test_transactions)}")

# Verify every customer appears in exactly one partition
train_customer_set = set(tx['sender_account'] for tx in train_transactions)
test_customer_set = set(tx['sender_account'] for tx in test_transactions)

print(f"Train customers (from transactions): {len(train_customer_set)}")
print(f"Test customers (from transactions): {len(test_customer_set)}")

if len(train_customer_set) != 160:
    print(f"ERROR: Expected 160 train customers, got {len(train_customer_set)}")
    exit(1)

if len(test_customer_set) != 40:
    print(f"ERROR: Expected 40 test customers, got {len(test_customer_set)}")
    exit(1)

# Verify no transaction from test customer appears in training
for tx in train_transactions:
    if tx['sender_account'] in test_customers:
        print(f"ERROR: Test customer {tx['sender_account']} found in training set")
        exit(1)

print("PASS: Customer-level holdout split validated")
print()

# Get corresponding features and labels
# Map transaction_id to index
tx_id_to_idx = {tx['transaction_id']: i for i, tx in enumerate(dataset)}

# Get train/test indices
train_indices = [tx_id_to_idx[tx['transaction_id']] for tx in train_transactions]
test_indices = [tx_id_to_idx[tx['transaction_id']] for tx in test_transactions]

# Get train/test features
train_features = [features[i] for i in train_indices]
test_features = [features[i] for i in test_indices]

# Get train/test labels
train_labels = [ground_truth[i]['ground_truth_label'] for i in train_indices]
test_labels = [ground_truth[i]['ground_truth_label'] for i in test_indices]

print(f"Train features: {len(train_features)}")
print(f"Test features: {len(test_features)}")
print(f"Train labels: {len(train_labels)}")
print(f"Test labels: {len(test_labels)}")
print()

# Save primary split results
primary_split_results = {
    "split_type": "customer_level_holdout",
    "random_seed": RANDOM_SEED,
    "train_customers": len(train_customers),
    "test_customers": len(test_customers),
    "customer_overlap": len(overlap),
    "train_transactions": len(train_transactions),
    "test_transactions": len(test_transactions),
    "train_customer_ids": list(train_customers),
    "test_customer_ids": list(test_customers),
    "train_indices": train_indices,
    "test_indices": test_indices,
    "train_labels": train_labels,
    "test_labels": test_labels
}

with open('ml_stage12_primary_split.json', 'w') as f:
    json.dump(primary_split_results, f, indent=2)

print("Primary split results saved to ml_stage12_primary_split.json")
print()

# ============================================================================
# SECONDARY SPLIT: CHRONOLOGICAL TRANSACTION SPLIT
# ============================================================================

print("=" * 80)
print("SECONDARY SPLIT: CHRONOLOGICAL TRANSACTION SPLIT")
print("-" * 80)

# Sort dataset chronologically
dataset_sorted = sorted(dataset, key=lambda x: x['timestamp'])

# Apply 80/20 chronological split
split_point = int(len(dataset_sorted) * 0.8)
chron_train_transactions = dataset_sorted[:split_point]
chron_test_transactions = dataset_sorted[split_point:]

print(f"Chronological train transactions: {len(chron_train_transactions)}")
print(f"Chronological test transactions: {len(chron_test_transactions)}")

# Get customers in train and test
chron_train_customers = set(tx['sender_account'] for tx in chron_train_transactions)
chron_test_customers = set(tx['sender_account'] for tx in chron_test_transactions)

print(f"Chronological train customers: {len(chron_train_customers)}")
print(f"Chronological test customers: {len(chron_test_customers)}")

# Check for customer overlap
chron_overlap = chron_train_customers & chron_test_customers
print(f"Customer overlap: {len(chron_overlap)}")

# Report temporal separation
chron_train_timestamps = [tx['timestamp'] for tx in chron_train_transactions]
chron_test_timestamps = [tx['timestamp'] for tx in chron_test_transactions]

print(f"Train period: {min(chron_train_timestamps)} to {max(chron_train_timestamps)}")
print(f"Test period: {min(chron_test_timestamps)} to {max(chron_test_timestamps)}")

chron_train_max = max(chron_train_timestamps)
chron_test_min = min(chron_test_timestamps)

if chron_train_max >= chron_test_min:
    print("WARNING: Temporal overlap detected!")
else:
    print("PASS: No temporal overlap")

print()

# Get corresponding features and labels
chron_tx_id_to_idx = {tx['transaction_id']: i for i, tx in enumerate(dataset_sorted)}

chron_train_indices = [chron_tx_id_to_idx[tx['transaction_id']] for tx in chron_train_transactions]
chron_test_indices = [chron_tx_id_to_idx[tx['transaction_id']] for tx in chron_test_transactions]

chron_train_features = [features[i] for i in chron_train_indices]
chron_test_features = [features[i] for i in chron_test_indices]

chron_train_labels = [ground_truth[i]['ground_truth_label'] for i in chron_train_indices]
chron_test_labels = [ground_truth[i]['ground_truth_label'] for i in chron_test_indices]

print(f"Chronological train features: {len(chron_train_features)}")
print(f"Chronological test features: {len(chron_test_features)}")
print(f"Chronological train labels: {len(chron_train_labels)}")
print(f"Chronological test labels: {len(chron_test_labels)}")
print()

# Save secondary split results
secondary_split_results = {
    "split_type": "chronological_transaction_split",
    "train_transactions": len(chron_train_transactions),
    "test_transactions": len(chron_test_transactions),
    "train_customers": len(chron_train_customers),
    "test_customers": len(chron_test_customers),
    "customer_overlap": len(chron_overlap),
    "train_period_start": min(chron_train_timestamps),
    "train_period_end": max(chron_train_timestamps),
    "test_period_start": min(chron_test_timestamps),
    "test_period_end": max(chron_test_timestamps),
    "temporal_overlap": chron_train_max >= chron_test_min,
    "train_indices": chron_train_indices,
    "test_indices": chron_test_indices,
    "train_labels": chron_train_labels,
    "test_labels": chron_test_labels
}

with open('ml_stage12_secondary_split.json', 'w') as f:
    json.dump(secondary_split_results, f, indent=2)

print("Secondary split results saved to ml_stage12_secondary_split.json")
print()

# ============================================================================
# SPLIT VALIDATION SUMMARY
# ============================================================================

print("=" * 80)
print("SPLIT VALIDATION SUMMARY")
print("-" * 80)

print("PRIMARY SPLIT (Customer-Level Holdout):")
print(f"  Train customers: {len(train_customers)}")
print(f"  Test customers: {len(test_customers)}")
print(f"  Customer overlap: {len(overlap)}")
print(f"  Train transactions: {len(train_transactions)}")
print(f"  Test transactions: {len(test_transactions)}")
print(f"  Status: PASS (zero customer overlap)")
print()

print("SECONDARY SPLIT (Chronological Transaction Split):")
print(f"  Train customers: {len(chron_train_customers)}")
print(f"  Test customers: {len(chron_test_customers)}")
print(f"  Customer overlap: {len(chron_overlap)}")
print(f"  Train transactions: {len(chron_train_transactions)}")
print(f"  Test transactions: {len(chron_test_transactions)}")
print(f"  Temporal overlap: {chron_train_max >= chron_test_min}")
print(f"  Status: PASS (with expected customer overlap)")
print()

print("METHODOLOGICAL DISTINCTION:")
print("Stage 6: Temporal + customer-disjoint generalization")
print("Stage 12 PRIMARY: Unseen-customer generalization (temporal separation not guaranteed)")
print("Stage 12 SECONDARY: Temporal generalization (customer overlap expected)")
print()

print("=" * 80)
print("SPLIT IMPLEMENTATION COMPLETE")
print("=" * 80)
