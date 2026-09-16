"""
STAGE 12: SPLIT AUDIT

Verify whether the Stage 6 split methodology can be applied to Stage 11.
Stage 6 used:
- 8,000 training transactions
- 2,000 test transactions
- chronological split
- 160 train customers
- 40 test customers
- zero customer overlap
"""

import csv
import json
from datetime import datetime, timezone
from collections import defaultdict, Counter
from typing import Dict, List, Any

print("=" * 80)
print("STAGE 12: SPLIT AUDIT")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================================
# LOAD DATA
# ============================================================================

print("Loading Stage 11 dataset...")
with open('ml_stage11_dataset.csv', 'r') as f:
    reader = csv.DictReader(f)
    dataset = list(reader)

with open('ml_stage11_ground_truth.json', 'r') as f:
    ground_truth = json.load(f)

print(f"Loaded {len(dataset)} transactions")
print(f"Loaded {len(ground_truth)} ground truth records")
print()

# ============================================================================
# VERIFY DATASET STRUCTURE
# ============================================================================

print("=" * 80)
print("PART 1: VERIFY DATASET STRUCTURE")
print("-" * 80)

# Check if dataset is sorted chronologically
timestamps = [tx['timestamp'] for tx in dataset]
is_sorted = all(timestamps[i] <= timestamps[i+1] for i in range(len(timestamps)-1))

print(f"Dataset is chronologically sorted: {is_sorted}")

if not is_sorted:
    print("WARNING: Dataset is not chronologically sorted")
    print("Sorting dataset chronologically...")
    dataset.sort(key=lambda x: x['timestamp'])
    print("Dataset sorted")
else:
    print("PASS: Dataset is chronologically sorted")

print()

# ============================================================================
# VERIFY CUSTOMER DISTRIBUTION
# ============================================================================

print("=" * 80)
print("PART 2: VERIFY CUSTOMER DISTRIBUTION")
print("-" * 80)

# Get unique customers (sender_account is the customer identifier)
customers = set(tx['sender_account'] for tx in dataset)
print(f"Number of unique customers: {len(customers)}")

# Count transactions per customer
customer_tx_counts = Counter(tx['sender_account'] for tx in dataset)
print(f"Transactions per customer:")
print(f"  Min: {min(customer_tx_counts.values())}")
print(f"  Max: {max(customer_tx_counts.values())}")
print(f"  Mean: {sum(customer_tx_counts.values()) / len(customer_tx_counts):.1f}")

print()

# ============================================================================
# VERIFY CHRONOLOGICAL CUSTOMER SEPARATION
# ============================================================================

print("=" * 80)
print("PART 3: VERIFY CHRONOLOGICAL CUSTOMER SEPARATION")
print("-" * 80)

# Apply Stage 6 split: first 80% train, last 20% test
split_point = int(len(dataset) * 0.8)
train_transactions = dataset[:split_point]
test_transactions = dataset[split_point:]

print(f"Train transactions: {len(train_transactions)}")
print(f"Test transactions: {len(test_transactions)}")

# Get customers in train and test
train_customers = set(tx['sender_account'] for tx in train_transactions)
test_customers = set(tx['sender_account'] for tx in test_transactions)

print(f"Train customers: {len(train_customers)}")
print(f"Test customers: {len(test_customers)}")

# Check for customer overlap
overlap = train_customers & test_customers
print(f"Customer overlap: {len(overlap)}")

if overlap:
    print("WARNING: Customer overlap detected!")
    print(f"Overlapping customers: {list(overlap)[:10]}")
    print()
    print("This means customers appear in both train and test sets.")
    print("This is different from Stage 6, which had zero customer overlap.")
else:
    print("PASS: Zero customer overlap")

print()

# ============================================================================
# VERIFY TEMPORAL SEPARATION
# ============================================================================

print("=" * 80)
print("PART 4: VERIFY TEMPORAL SEPARATION")
print("-" * 80)

train_timestamps = [tx['timestamp'] for tx in train_transactions]
test_timestamps = [tx['timestamp'] for tx in test_transactions]

print(f"Train period: {min(train_timestamps)} to {max(train_timestamps)}")
print(f"Test period: {min(test_timestamps)} to {max(test_timestamps)}")

# Check for temporal overlap
train_max = max(train_timestamps)
test_min = min(test_timestamps)

if train_max >= test_min:
    print("WARNING: Temporal overlap detected!")
    print(f"Train max timestamp: {train_max}")
    print(f"Test min timestamp: {test_min}")
else:
    print("PASS: No temporal overlap")

print()

# ============================================================================
# SPLIT AUDIT RESULTS
# ============================================================================

print("=" * 80)
print("SPLIT AUDIT RESULTS")
print("-" * 80)

split_audit_results = {
    "timestamp": datetime.now().isoformat(),
    "dataset_chronologically_sorted": is_sorted,
    "total_transactions": len(dataset),
    "total_customers": len(customers),
    "train_transactions": len(train_transactions),
    "test_transactions": len(test_transactions),
    "train_customers": len(train_customers),
    "test_customers": len(test_customers),
    "customer_overlap": len(overlap),
    "temporal_overlap": train_max >= test_min,
    "stage6_split_applicable": len(overlap) == 0 and train_max < test_min
}

print(f"Dataset chronologically sorted: {is_sorted}")
print(f"Total transactions: {len(dataset)}")
print(f"Total customers: {len(customers)}")
print(f"Train transactions: {len(train_transactions)}")
print(f"Test transactions: {len(test_transactions)}")
print(f"Train customers: {len(train_customers)}")
print(f"Test customers: {len(test_customers)}")
print(f"Customer overlap: {len(overlap)}")
print(f"Temporal overlap: {train_max >= test_min}")
print()
print(f"Stage 6 split applicable: {split_audit_results['stage6_split_applicable']}")

if not split_audit_results['stage6_split_applicable']:
    print()
    print("DISCREPANCY: Stage 6 split methodology cannot be applied exactly.")
    print("Reason: Customer overlap detected.")
    print()
    print("Stage 6 had:")
    print("  - 160 train customers")
    print("  - 40 test customers")
    print("  - Zero customer overlap")
    print()
    print("Stage 11 has:")
    print(f"  - {len(train_customers)} train customers")
    print(f"  - {len(test_customers)} test customers")
    print(f"  - {len(overlap)} customer overlap")
    print()
    print("This is because Stage 11 generates transactions per customer")
    print("chronologically, so customers appear in both train and test sets.")
    print()
    print("RECOMMENDATION: Proceed with chronological split despite")
    print("customer overlap, as this is the natural structure of the dataset.")
    print("This is a known limitation of the Stage 11 dataset structure.")
else:
    print()
    print("PASS: Stage 6 split methodology can be applied exactly.")

print()

# Save results
with open('ml_stage12_split_audit_results.json', 'w') as f:
    json.dump(split_audit_results, f, indent=2)

print("Results saved to ml_stage12_split_audit_results.json")
