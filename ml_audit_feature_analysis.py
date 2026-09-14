"""
Temporary script to analyze feature extraction and training methodology for audit purposes.
This script will NOT modify anything - only read and analyze.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_core import transaction_features, map_risk_to_ai_label, PROFILE_FEATURE_DEFAULTS, CHANNEL_ENCODING, LABELS

print("=" * 80)
print("AML AI MODEL AUDIT - FEATURE AND TRAINING ANALYSIS")
print("=" * 80)
print()

# Analyze feature extraction
print("FEATURE EXTRACTION ANALYSIS:")
print("-" * 80)

# Create a sample transaction to see what features are extracted
sample_transaction = {
    "amount": 5000.0,
    "transaction_type": "transfer",
    "sender_account": "ACC123",
    "receiver_account": "ACC456",
    "timestamp": "2026-09-01T14:30:00+00:00",
    "channel": "online",
    "sender_avg_amount": 2000.0,
    "sender_max_amount": 10000.0,
    "sender_tx_count": 50,
    "amount_to_sender_avg": 2.5,
    "amount_to_sender_max": 0.5,
    "sender_tx_count_24h": 5,
    "sender_volume_24h": 15000.0,
    "amount_to_sender_volume_24h": 0.33,
    "is_new_recipient": 1.0,
    "same_day_count": 3,
    "same_day_total": 12000.0,
    "same_recipient_count": 1,
    "rapid_transfer_count": 2,
}

features = transaction_features(sample_transaction)

print(f"Number of features: {len(features)}")
print()
print("Feature list:")
feature_names = [
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

for i, (name, value) in enumerate(zip(feature_names, features)):
    print(f"  {i+1:2d}. {name:30s} = {value}")

print()

# Analyze label mapping
print("LABEL MAPPING ANALYSIS:")
print("-" * 80)
print("Function: map_risk_to_ai_label(risk_level, risk_score)")
print()

test_cases = [
    ("normal", 10),
    ("normal", 30),
    ("low", 20),
    ("suspicious", 45),
    ("suspicious", 65),
    ("medium", 50),
    ("high_risk", 70),
    ("critical", 85),
    ("super_suspicious", 90),
]

for risk_level, risk_score in test_cases:
    label = map_risk_to_ai_label(risk_level, risk_score)
    print(f"  risk_level='{risk_level:20s}', risk_score={risk_score:3d} -> label='{label}'")

print()

# Analyze channel encoding
print("CHANNEL ENCODING:")
print("-" * 80)
for channel, code in CHANNEL_ENCODING.items():
    print(f"  {channel:15s} -> {code}")

print()

# Analyze profile feature defaults
print("PROFILE FEATURE DEFAULTS:")
print("-" * 80)
for key, value in PROFILE_FEATURE_DEFAULTS.items():
    print(f"  {key:30s} = {value}")

print()

# Analyze label classes
print("LABEL CLASSES:")
print("-" * 80)
print(f"Classes: {LABELS}")

print()
print("=" * 80)
print("FEATURE AND TRAINING ANALYSIS COMPLETE")
print("=" * 80)
