"""
Debug AI model predictions with suspicious transaction patterns.
"""

import json
from ai_core import load_ai_model, predict_risk_level, transaction_features

print("=" * 80)
print("DEBUGGING AI MODEL PREDICTIONS WITH SUSPICIOUS PATTERNS")
print("=" * 80)
print()

# ============================================================================
# TEST 1: Load Model
# ============================================================================

bundle = load_ai_model()
if bundle is None:
    print("❌ FAILED: Could not load model")
    exit(1)

print(f"✅ Model loaded (version: {bundle.get('version', 'unknown')})")
print()

# ============================================================================
# TEST 2: Test with Suspicious Transaction Patterns
# ============================================================================

test_transactions = [
    {
        "name": "Large Amount Transfer",
        "transaction_id": 1,
        "sender_account": "TEST001",
        "receiver_account": "TEST002",
        "amount": 50000.0,  # Very large amount
        "timestamp": "2026-09-02T12:00:00",
        "sender_avg_amount": 3000.0,
        "sender_max_amount": 10000.0,
        "sender_tx_count_24h": 5,
        "sender_volume_24h": 15000.0,
        "is_new_recipient": 1.0,  # New recipient
        "tx_frequency_7d": 10,
        "tx_frequency_30d": 45,
        "same_day_count": 5,  # Multiple same-day transactions
        "rapid_transfer_count": 3,  # Rapid transfers
        "unique_recipients_7d": 10,  # Many unique recipients
        "counterparty_change_score_7d": 0.9,  # High counterparty change
    },
    {
        "name": "Structuring Pattern",
        "transaction_id": 2,
        "sender_account": "TEST001",
        "receiver_account": "TEST003",
        "amount": 9500.0,  # Just below CTR threshold
        "timestamp": "2026-09-02T14:00:00",
        "sender_avg_amount": 3000.0,
        "sender_max_amount": 10000.0,
        "sender_tx_count_24h": 15,
        "sender_volume_24h": 50000.0,
        "is_new_recipient": 0.0,
        "tx_frequency_7d": 30,
        "tx_frequency_30d": 100,
        "same_day_count": 8,
        "rapid_transfer_count": 5,
        "unique_recipients_7d": 5,
        "counterparty_change_score_7d": 0.3,
    },
    {
        "name": "Off-Hours Large Transfer",
        "transaction_id": 3,
        "sender_account": "TEST001",
        "receiver_account": "TEST004",
        "amount": 25000.0,
        "timestamp": "2026-09-02T02:00:00",  # 2 AM - off hours
        "sender_avg_amount": 3000.0,
        "sender_max_amount": 10000.0,
        "sender_tx_count_24h": 2,
        "sender_volume_24h": 30000.0,
        "is_new_recipient": 1.0,
        "tx_frequency_7d": 5,
        "tx_frequency_30d": 20,
        "same_day_count": 1,
        "rapid_transfer_count": 0,
        "unique_recipients_7d": 2,
        "counterparty_change_score_7d": 0.5,
    },
    {
        "name": "High Velocity Pattern",
        "transaction_id": 4,
        "sender_account": "TEST001",
        "receiver_account": "TEST005",
        "amount": 10000.0,
        "timestamp": "2026-09-02T10:00:00",
        "sender_avg_amount": 3000.0,
        "sender_max_amount": 10000.0,
        "sender_tx_count_24h": 50,  # Very high frequency
        "sender_volume_24h": 200000.0,  # Very high volume
        "is_new_recipient": 0.0,
        "tx_frequency_7d": 100,
        "tx_frequency_30d": 300,
        "same_day_count": 20,
        "rapid_transfer_count": 10,
        "unique_recipients_7d": 15,
        "counterparty_change_score_7d": 0.8,
    },
]

print("Testing suspicious transaction patterns:")
print()

for i, tx in enumerate(test_transactions, 1):
    print(f"TEST {i}: {tx['name']}")
    print(f"  Amount: ${tx['amount']:,.2f}")
    print(f"  Same Day Count: {tx['same_day_count']}")
    print(f"  Rapid Transfer Count: {tx['rapid_transfer_count']}")
    print(f"  New Recipient: {tx['is_new_recipient']}")
    print(f"  24h Volume: ${tx['sender_volume_24h']:,.2f}")
    
    predicted, confidence, anomaly_score = predict_risk_level(tx)
    
    print(f"  Predicted: {predicted}")
    print(f"  Confidence: {confidence:.4f}")
    print(f"  Anomaly Score: {anomaly_score}")
    
    # Check confidence thresholds
    if predicted == "super_suspicious" and confidence < 0.55:
        print(f"  ⚠️  BELOW THRESHOLD: Confidence {confidence:.4f} < 0.55 (super_suspicious threshold)")
    elif predicted == "suspicious" and confidence < 0.65:
        print(f"  ⚠️  BELOW THRESHOLD: Confidence {confidence:.4f} < 0.65 (suspicious threshold)")
    elif predicted == "normal" and confidence < 0.75:
        print(f"  ⚠️  BELOW THRESHOLD: Confidence {confidence:.4f} < 0.75 (normal threshold)")
    
    print()

# ============================================================================
# TEST 3: Check Feature Extraction
# ============================================================================

print("Checking feature extraction for suspicious transaction:")
suspicious_tx = test_transactions[0]
features = transaction_features(suspicious_tx)
print(f"  Feature count: {len(features)}")
print(f"  Features: {features}")
print()

print("=" * 80)
print("DEBUG COMPLETE")
print("=" * 80)
