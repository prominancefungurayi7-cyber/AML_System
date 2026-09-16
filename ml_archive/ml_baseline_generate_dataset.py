"""
Generate a dataset for baseline evaluation using existing transaction_simulation.py
This script uses the EXISTING implementation without modifications.
"""

import sys
import os
import json
import random
from datetime import datetime, timedelta, timezone

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transaction_simulation import (
    _simulation_plan,
    _simulation_transaction,
    NORMAL_TRANSACTION_SCENARIOS,
    SUSPICIOUS_TRANSACTION_SCENARIOS,
    SUPER_SUSPICIOUS_TRANSACTION_SCENARIOS,
    PROFILE_FEATURE_DEFAULTS
)

print("=" * 80)
print("STAGE 2: BASELINE DATASET GENERATION")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# Set random seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# Generate dataset
NUM_TRANSACTIONS = 10000  # Larger than training set for proper evaluation
print(f"Generating {NUM_TRANSACTIONS} transactions using existing generator...")
print()

# Create mock users for simulation
NUM_USERS = 100
users = []
for i in range(NUM_USERS):
    users.append({
        "id": i,
        "account_number": f"ACC{i:04d}",
        "balance": random.uniform(1000, 100000),
        "wealth_segment": random.choice(["average", "high", "ultra"])
    })

# Generate transaction labels
labels = _simulation_plan(NUM_TRANSACTIONS)

# Generate transactions
transactions = []
for label in labels:
    # Generate a single transaction
    tx_data = _simulation_transaction(label, users)[0]
    sender, recipient, tx_type, amount, timestamp, channel, description, reason, dest_country = tx_data
    
    # Build profile features
    profile = dict(PROFILE_FEATURE_DEFAULTS)
    
    # Simulate some historical data
    avg_amount = random.uniform(500, 5000)
    max_amount = avg_amount * random.uniform(2, 5)
    tx_count = random.randint(5, 100)
    
    profile.update({
        "sender_avg_amount": avg_amount,
        "sender_max_amount": max_amount,
        "sender_tx_count": tx_count,
        "amount_to_sender_avg": amount / avg_amount if avg_amount > 0 else 1.0,
        "amount_to_sender_max": amount / max_amount if max_amount > 0 else 1.0,
        "sender_tx_count_24h": random.randint(0, 10),
        "sender_volume_24h": random.uniform(0, 20000),
        "amount_to_sender_volume_24h": random.uniform(0, 2),
        "is_new_recipient": random.choice([0.0, 1.0]),
        "same_day_count": random.randint(0, 5),
        "same_day_total": random.uniform(0, 30000),
        "same_recipient_count": random.randint(0, 3),
        "rapid_transfer_count": random.randint(0, 5),
    })
    
    # Create transaction record
    transaction = {
        "id": len(transactions),
        "sender_account": sender["account_number"],
        "receiver_account": recipient["account_number"],
        "transaction_type": tx_type,
        "amount": amount,
        "timestamp": timestamp,
        "channel": channel,
        "description": description,
        "risk_level": label,  # Using label as risk_level for existing methodology
        "risk_score": random.uniform(10, 90),
        **profile
    }
    transactions.append(transaction)

print(f"Generated {len(transactions)} transactions")
print()

# Analyze dataset
print("DATASET STATISTICS:")
print("-" * 80)

# Count labels
label_counts = {"normal": 0, "suspicious": 0, "super_suspicious": 0}
for tx in transactions:
    risk_level = tx.get("risk_level", "normal")
    label = risk_level.lower()
    if label in label_counts:
        label_counts[label] += 1
    else:
        label_counts["normal"] += 1

print("Label distribution (from risk_level):")
for label, count in label_counts.items():
    pct = count / len(transactions) * 100
    print(f"  {label:20s}: {count:5d} ({pct:5.1f}%)")
print()

# Count unique accounts
accounts = set()
for tx in transactions:
    accounts.add(tx.get("sender_account", ""))
    accounts.add(tx.get("receiver_account", ""))
print(f"Unique accounts: {len(accounts)}")
print()

# Transaction types
tx_types = {}
for tx in transactions:
    ttype = tx.get("transaction_type", "unknown")
    tx_types[ttype] = tx_types.get(ttype, 0) + 1
print("Transaction types:")
for ttype, count in sorted(tx_types.items(), key=lambda x: x[1], reverse=True):
    pct = count / len(transactions) * 100
    print(f"  {ttype:15s}: {count:5d} ({pct:5.1f}%)")
print()

# Channels
channels = {}
for tx in transactions:
    channel = tx.get("channel", "online")
    channels[channel] = channels.get(channel, 0) + 1
print("Channels:")
for channel, count in sorted(channels.items(), key=lambda x: x[1], reverse=True):
    pct = count / len(transactions) * 100
    print(f"  {channel:15s}: {count:5d} ({pct:5.1f}%)")
print()

# Amount statistics
amounts = [tx.get("amount", 0) for tx in transactions]
print(f"Amount statistics:")
print(f"  Min: ${min(amounts):,.2f}")
print(f"  Max: ${max(amounts):,.2f}")
print(f"  Mean: ${sum(amounts)/len(amounts):,.2f}")
print(f"  Median: ${sorted(amounts)[len(amounts)//2]:,.2f}")
print()

# Save dataset
output_file = "ml_baseline_dataset.json"
print(f"Saving dataset to {output_file}...")
with open(output_file, 'w') as f:
    json.dump(transactions, f, indent=2)
print(f"Dataset saved ({len(transactions)} transactions)")
print()

# Save metadata
metadata = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "random_seed": RANDOM_SEED,
    "num_transactions": len(transactions),
    "num_unique_accounts": len(accounts),
    "label_distribution": label_counts,
    "transaction_types": tx_types,
    "channels": channels,
    "amount_stats": {
        "min": min(amounts),
        "max": max(amounts),
        "mean": sum(amounts)/len(amounts),
        "median": sorted(amounts)[len(amounts)//2]
    }
}

metadata_file = "ml_baseline_dataset_metadata.json"
print(f"Saving metadata to {metadata_file}...")
with open(metadata_file, 'w') as f:
    json.dump(metadata, f, indent=2)
print("Metadata saved")
print()

print("=" * 80)
print("DATASET GENERATION COMPLETE")
print("=" * 80)
