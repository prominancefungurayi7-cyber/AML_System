"""
INTEGRATION TEST - Threshold Fix Verification
============================================
Test the confidence threshold fix by simulating the application flow.
"""

import os
import json
import joblib
import pickle
import numpy as np
from ai_core import predict_risk_level, transaction_features

print("=" * 100)
print("INTEGRATION TEST - THRESHOLD FIX VERIFICATION")
print("=" * 100)
print()

# Load model to get direct predictions
model = joblib.load('aml_ai_model.pkl')
with open('aml_label_encoder.pkl', 'rb') as f:
    label_encoder = pickle.load(f)

# Define AI_RISK_SCORES (from server.py)
AI_RISK_SCORES = {
    "normal": 0,
    "suspicious": 60,
    "super_suspicious": 85
}

# Define thresholds (NEW values after fix)
THRESHOLDS = {
    "super_suspicious": 0.55,
    "suspicious": 0.55,  # CHANGED from 0.65
    "normal": 0.75
}

def simulate_server_logic(ml_level, ml_confidence):
    """Simulate the server.py threshold logic."""
    confidence_threshold = 0.65  # default
    if ml_level == "super_suspicious":
        confidence_threshold = 0.55
    elif ml_level == "suspicious":
        confidence_threshold = 0.55  # NEW VALUE
    else:
        confidence_threshold = 0.75
    
    ml_score = AI_RISK_SCORES.get(ml_level, 0) if ml_confidence >= confidence_threshold else 0
    return ml_score, confidence_threshold

def test_transaction(name, transaction):
    """Test a transaction through the full flow."""
    print(f"\n{'='*100}")
    print(f"TEST: {name}")
    print(f"{'='*100}")
    
    # Transaction characteristics
    print(f"\nTransaction Characteristics:")
    print(f"  Amount: ${transaction.get('amount', 0):,.2f}")
    print(f"  Sender: {transaction.get('sender_account', 'N/A')}")
    print(f"  Receiver: {transaction.get('receiver_account', 'N/A')}")
    print(f"  Timestamp: {transaction.get('timestamp', 'N/A')}")
    
    # Get features
    features = transaction_features(transaction)
    print(f"\n18-Feature Vector:")
    for i, (name_feat, value) in enumerate(zip([
        "amount", "sender_avg_amount", "sender_max_amount", "amount_to_sender_avg",
        "amount_z_score", "amount_deviation_from_baseline_30d", "tx_frequency_7d",
        "tx_frequency_30d", "frequency_change_vs_avg_7d", "sender_tx_count_24h",
        "sender_volume_24h", "same_day_count", "rapid_transfer_count", "is_new_recipient",
        "unique_recipients_7d", "hour", "is_off_hours", "counterparty_change_score_7d"
    ], features), 1):
        print(f"  {i}. {name_feat}: {value}")
    
    # Raw model prediction
    features_2d = [features]
    proba = model.predict_proba(features_2d)[0]
    argmax = int(proba.argmax())
    classes_argmax = model.classes_[argmax]
    decoded_label = label_encoder.inverse_transform([argmax])[0]
    
    print(f"\nRaw Model Prediction:")
    print(f"  classifier.classes_: {list(model.classes_)}")
    print(f"  predict_proba(): {list(proba)}")
    print(f"  argmax: {argmax}")
    print(f"  classes[argmax]: {classes_argmax}")
    print(f"  Decoded label: {decoded_label}")
    
    # ai_core.py prediction
    ml_level, ml_confidence, _ = predict_risk_level(transaction)
    
    print(f"\nai_core.py Prediction:")
    print(f"  ml_level: {ml_level}")
    print(f"  ml_confidence: {ml_confidence:.4f}")
    
    # Server threshold logic
    ml_score, threshold = simulate_server_logic(ml_level, ml_confidence)
    
    print(f"\nServer Threshold Logic:")
    print(f"  Predicted level: {ml_level}")
    print(f"  Confidence: {ml_confidence:.4f}")
    print(f"  Threshold applied: {threshold}")
    print(f"  Passes threshold: {ml_confidence >= threshold}")
    print(f"  ml_score: {ml_score}")
    
    # Final classification
    if ml_score > 0:
        final_level = ml_level
    else:
        final_level = "normal"
    
    print(f"\nFinal Classification:")
    print(f"  UI Display: {final_level.upper()}")
    
    return {
        'name': name,
        'ml_level': ml_level,
        'ml_confidence': ml_confidence,
        'threshold': threshold,
        'passes_threshold': ml_confidence >= threshold,
        'ml_score': ml_score,
        'final_level': final_level
    }

# ============================================================================
# TEST 1: Normal Transaction
# ============================================================================
test1 = test_transaction(
    "Normal Transaction",
    {
        "transaction_id": 1,
        "sender_account": "TEST001",
        "receiver_account": "TEST002",
        "amount": 5000.0,
        "timestamp": "2026-09-02T12:00:00",
        "sender_avg_amount": 3000.0,
        "sender_max_amount": 10000.0,
        "sender_tx_count_24h": 5,
        "sender_volume_24h": 15000.0,
        "is_new_recipient": 0.0,
        "tx_frequency_7d": 10,
        "tx_frequency_30d": 45,
        "same_day_count": 2,
        "rapid_transfer_count": 1,
        "unique_recipients_7d": 3,
        "counterparty_change_score_7d": 0.5
    }
)

# ============================================================================
# TEST 2: Structuring/Suspicious Transaction (THE KEY TEST)
# ============================================================================
test2 = test_transaction(
    "Structuring/Suspicious Transaction (62.4% confidence)",
    {
        "transaction_id": 2,
        "sender_account": "TEST001",
        "receiver_account": "TEST003",
        "amount": 9500.0,
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
        "counterparty_change_score_7d": 0.3
    }
)

# ============================================================================
# TEST 3: Severe/Super-Suspicious Transaction
# ============================================================================
test3 = test_transaction(
    "Severe/Super-Suspicious Transaction",
    {
        "transaction_id": 3,
        "sender_account": "TEST001",
        "receiver_account": "TEST004",
        "amount": 100000.0,
        "timestamp": "2026-09-02T03:00:00",
        "sender_avg_amount": 3000.0,
        "sender_max_amount": 10000.0,
        "sender_tx_count_24h": 100,
        "sender_volume_24h": 1000000.0,
        "is_new_recipient": 1.0,
        "tx_frequency_7d": 200,
        "tx_frequency_30d": 500,
        "same_day_count": 50,
        "rapid_transfer_count": 30,
        "unique_recipients_7d": 20,
        "counterparty_change_score_7d": 1.0
    }
)

# ============================================================================
# TEST 4: Rapid-Transfer/High-Velocity Transaction
# ============================================================================
test4 = test_transaction(
    "Rapid-Transfer/High-Velocity Transaction",
    {
        "transaction_id": 4,
        "sender_account": "TEST001",
        "receiver_account": "TEST005",
        "amount": 10000.0,
        "timestamp": "2026-09-02T10:00:00",
        "sender_avg_amount": 3000.0,
        "sender_max_amount": 10000.0,
        "sender_tx_count_24h": 50,
        "sender_volume_24h": 200000.0,
        "is_new_recipient": 0.0,
        "tx_frequency_7d": 100,
        "tx_frequency_30d": 300,
        "same_day_count": 20,
        "rapid_transfer_count": 10,
        "unique_recipients_7d": 15,
        "counterparty_change_score_7d": 0.8
    }
)

# ============================================================================
# TEST 5: Additional Representative Transaction
# ============================================================================
test5 = test_transaction(
    "Large Amount New Recipient",
    {
        "transaction_id": 5,
        "sender_account": "TEST001",
        "receiver_account": "TEST006",
        "amount": 25000.0,
        "timestamp": "2026-09-02T16:00:00",
        "sender_avg_amount": 3000.0,
        "sender_max_amount": 10000.0,
        "sender_tx_count_24h": 3,
        "sender_volume_24h": 30000.0,
        "is_new_recipient": 1.0,
        "tx_frequency_7d": 5,
        "tx_frequency_30d": 20,
        "same_day_count": 1,
        "rapid_transfer_count": 0,
        "unique_recipients_7d": 2,
        "counterparty_change_score_7d": 0.5
    }
)

# ============================================================================
# SUMMARY
# ============================================================================
print(f"\n{'='*100}")
print("TEST SUMMARY")
print(f"{'='*100}")

results = [test1, test2, test3, test4, test5]

normal_count = sum(1 for r in results if r['final_level'] == 'normal')
suspicious_count = sum(1 for r in results if r['final_level'] == 'suspicious')
super_suspicious_count = sum(1 for r in results if r['final_level'] == 'super_suspicious')

print(f"\nFinal Classifications:")
print(f"  Normal: {normal_count}")
print(f"  Suspicious: {suspicious_count}")
print(f"  Super-Suspicious: {super_suspicious_count}")

print(f"\nDetailed Results:")
for r in results:
    print(f"\n  {r['name']}:")
    print(f"    Model Prediction: {r['ml_level']} ({r['ml_confidence']:.2%})")
    print(f"    Threshold: {r['threshold']}")
    print(f"    Passes: {r['passes_threshold']}")
    print(f"    Final UI: {r['final_level'].upper()}")

print(f"\n{'='*100}")
print("KEY VERIFICATION")
print(f"{'='*100}")
print(f"\nStructuring case (62.4% suspicious):")
print(f"  Before fix: Would be REJECTED (62.4% < 65%)")
print(f"  After fix: {'ACCEPTED' if test2['passes_threshold'] else 'REJECTED'} (62.4% >= 55%)")
print(f"  UI Display: {test2['final_level'].upper()}")
print(f"  Expected: SUSPICIOUS")
print(f"  Status: {'✅ PASS' if test2['final_level'] == 'suspicious' else '❌ FAIL'}")

print(f"\nNormal transaction check:")
print(f"  Model Prediction: {test1['ml_level']} ({test1['ml_confidence']:.2%})")
print(f"  Threshold: {test1['threshold']}")
print(f"  Passes: {test1['passes_threshold']}")
print(f"  UI Display: {test1['final_level'].upper()}")
print(f"  Expected: NORMAL")
print(f"  Status: {'✅ PASS' if test1['final_level'] == 'normal' else '❌ FAIL - False positive'}")

print(f"\n{'='*100}")
print("INTEGRATION TEST COMPLETE")
print(f"{'='*100}")
