"""
Test Stage 16B model integration with ai_core.py
"""

import json
from ai_core import load_ai_model, predict_risk_level, get_model_metadata

print("=" * 80)
print("TESTING STAGE 16B MODEL INTEGRATION")
print("=" * 80)
print()

# ============================================================================
# TEST 1: Load Model
# ============================================================================

print("TEST 1: Loading model...")
bundle = load_ai_model()
if bundle is None:
    print("❌ FAILED: Could not load model")
else:
    print("✅ PASSED: Model loaded successfully")
    print(f"   Version: {bundle.get('version', 'unknown')}")
print()

# ============================================================================
# TEST 2: Get Model Metadata
# ============================================================================

print("TEST 2: Getting model metadata...")
metadata = get_model_metadata()
print(f"   Metadata: {json.dumps(metadata, indent=2)}")
print("✅ PASSED: Metadata retrieved")
print()

# ============================================================================
# TEST 3: Test Prediction
# ============================================================================

print("TEST 3: Testing prediction...")

# Create a test transaction with the 18 required features
test_transaction = {
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

predicted, confidence, anomaly_score = predict_risk_level(test_transaction)

if predicted is None:
    print("❌ FAILED: Prediction returned None")
else:
    print(f"✅ PASSED: Prediction successful")
    print(f"   Predicted: {predicted}")
    print(f"   Confidence: {confidence:.4f}")
    print(f"   Anomaly Score: {anomaly_score}")
print()

# ============================================================================
# TEST 4: Test Feature Extraction
# ============================================================================

print("TEST 4: Testing feature extraction...")
from ai_core import transaction_features

features = transaction_features(test_transaction)
print(f"   Feature count: {len(features)}")
print(f"   Expected: 18 features")

if len(features) == 18:
    print("✅ PASSED: Feature extraction returns 18 features")
    print(f"   Features: {features}")
else:
    print(f"❌ FAILED: Expected 18 features, got {len(features)}")
print()

print("=" * 80)
print("MODEL INTEGRATION TEST COMPLETE")
print("=" * 80)
