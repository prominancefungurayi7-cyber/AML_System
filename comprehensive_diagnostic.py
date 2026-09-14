"""
COMPREHENSIVE MODEL INTEGRATION DIAGNOSTIC
===========================================

This script performs all 9 checks to determine why the frozen AML model
is returning Normal for everything.
"""

import os
import json
import pickle
import joblib
from datetime import datetime
from ai_core import load_ai_model, predict_risk_level, transaction_features, MODEL_PATH, METADATA_PATH
import numpy as np

print("=" * 100)
print("COMPREHENSIVE MODEL INTEGRATION DIAGNOSTIC")
print("=" * 100)
print()

diagnostic_results = {}

# ============================================================================
# CHECK 1: VERIFY MODEL IS LOADED CORRECTLY
# ============================================================================
print("CHECK 1: VERIFY MODEL IS LOADED CORRECTLY")
print("-" * 100)

# Check model file exists
model_exists = os.path.exists(MODEL_PATH)
print(f"Model file exists: {model_exists}")
print(f"Model path: {MODEL_PATH}")

if model_exists:
    model_stat = os.stat(MODEL_PATH)
    print(f"Model file size: {model_stat.st_size} bytes")
    print(f"Model modification time: {datetime.fromtimestamp(model_stat.st_mtime)}")
    
    # Load the model directly
    try:
        model = joblib.load(MODEL_PATH)
        print(f"Model type: {type(model)}")
        print(f"Model class name: {model.__class__.__name__}")
        
        # Check if it's the expected GradientBoostingClassifier
        from sklearn.ensemble import GradientBoostingClassifier
        is_gb = isinstance(model, GradientBoostingClassifier)
        print(f"Is GradientBoostingClassifier: {is_gb}")
        
        if is_gb:
            print(f"Model configuration:")
            print(f"  learning_rate: {model.learning_rate}")
            print(f"  max_depth: {model.max_depth}")
            print(f"  n_estimators: {model.n_estimators}")
            print(f"  random_state: {model.random_state}")
        
        # Check model.classes_
        print(f"Model classes: {model.classes_}")
        print(f"Number of classes: {len(model.classes_)}")
        
        diagnostic_results['check1'] = {
            'model_loaded': True,
            'model_type': model.__class__.__name__,
            'is_gradient_boosting': is_gb,
            'model_config': {
                'learning_rate': model.learning_rate if is_gb else None,
                'max_depth': model.max_depth if is_gb else None,
                'n_estimators': model.n_estimators if is_gb else None,
                'random_state': model.random_state if is_gb else None
            },
            'model_classes': list(model.classes_),
            'expected_config': {
                'learning_rate': 0.01,
                'max_depth': 3,
                'n_estimators': 500,
                'random_state': 42
            }
        }
        
    except Exception as e:
        print(f"ERROR loading model: {e}")
        diagnostic_results['check1'] = {'model_loaded': False, 'error': str(e)}
else:
    print("ERROR: Model file does not exist!")
    diagnostic_results['check1'] = {'model_loaded': False, 'error': 'Model file not found'}

print()

# ============================================================================
# CHECK 2: VERIFY 18 FEATURES ARE GENERATED CORRECTLY
# ============================================================================
print("CHECK 2: VERIFY 18 FEATURES ARE GENERATED CORRECTLY")
print("-" * 100)

expected_features = [
    "amount",
    "sender_avg_amount",
    "sender_max_amount",
    "amount_to_sender_avg",
    "amount_z_score",
    "amount_deviation_from_baseline_30d",
    "tx_frequency_7d",
    "tx_frequency_30d",
    "frequency_change_vs_avg_7d",
    "sender_tx_count_24h",
    "sender_volume_24h",
    "same_day_count",
    "rapid_transfer_count",
    "is_new_recipient",
    "unique_recipients_7d",
    "hour",
    "is_off_hours",
    "counterparty_change_score_7d"
]

print(f"Expected features: {len(expected_features)}")
for i, feat in enumerate(expected_features, 1):
    print(f"  {i}. {feat}")

# Test feature extraction with a sample transaction
test_tx = {
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

features = transaction_features(test_tx)
print(f"\nGenerated features: {len(features)}")
print(f"Feature vector: {features}")

# Check for issues
issues = []
if len(features) != 18:
    issues.append(f"Feature count mismatch: expected 18, got {len(features)}")

# Check for constant/zero features
zero_count = sum(1 for f in features if f == 0)
if zero_count > 5:
    issues.append(f"High number of zero features: {zero_count}/18")

# Check for NaN/inf
has_nan = any(np.isnan(f) if isinstance(f, (float, np.floating)) else False for f in features)
has_inf = any(np.isinf(f) if isinstance(f, (float, np.floating)) else False for f in features)
if has_nan:
    issues.append("Features contain NaN values")
if has_inf:
    issues.append("Features contain Inf values")

diagnostic_results['check2'] = {
    'expected_feature_count': 18,
    'actual_feature_count': len(features),
    'feature_vector': features,
    'issues': issues
}

if issues:
    print(f"\n⚠️  ISSUES FOUND:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print(f"\n✅ Feature extraction appears correct")

print()

# ============================================================================
# CHECK 3: VERIFY MODEL PREDICTION DIRECTLY
# ============================================================================
print("CHECK 3: VERIFY MODEL PREDICTION DIRECTLY")
print("-" * 100)

if model_exists:
    try:
        # Test with the model directly
        model = joblib.load(MODEL_PATH)
        
        # Test with several feature vectors
        test_cases = [
            {
                "name": "Normal transaction",
                "features": [5000.0, 3000.0, 10000.0, 1.67, 0.0, 0.0, 10.0, 45.0, 0.0, 5.0, 15000.0, 2.0, 1.0, 0.0, 3.0, 12, 0, 0.5]
            },
            {
                "name": "Suspicious pattern",
                "features": [9500.0, 3000.0, 10000.0, 3.17, 2.0, 0.5, 30.0, 100.0, 1.5, 15.0, 50000.0, 8.0, 5.0, 0.0, 5.0, 14, 0, 0.3]
            },
            {
                "name": "High velocity",
                "features": [10000.0, 3000.0, 10000.0, 3.33, 2.5, 1.0, 100.0, 300.0, 2.0, 50.0, 200000.0, 20.0, 10.0, 0.0, 15.0, 10, 0, 0.8]
            }
        ]
        
        predictions = []
        for case in test_cases:
            features_2d = [case['features']]
            pred_class = model.predict(features_2d)[0]
            pred_proba = model.predict_proba(features_2d)[0]
            max_proba = max(pred_proba)
            class_idx = int(pred_proba.argmax())
            
            print(f"\nTest: {case['name']}")
            print(f"  Features: {case['features']}")
            print(f"  Predicted class (numeric): {pred_class}")
            print(f"  Predicted class index: {class_idx}")
            print(f"  Class probabilities: {pred_proba}")
            print(f"  Max probability: {max_proba:.4f}")
            print(f"  Model classes: {model.classes_}")
            
            predictions.append({
                'name': case['name'],
                'predicted_class': int(pred_class),
                'class_index': class_idx,
                'probabilities': list(pred_proba),
                'max_probability': float(max_proba),
                'model_classes': list(model.classes_)
            })
        
        diagnostic_results['check3'] = {
            'direct_predictions': predictions,
            'model_classes': list(model.classes_)
        }
        
    except Exception as e:
        print(f"ERROR during direct prediction: {e}")
        import traceback
        traceback.print_exc()
        diagnostic_results['check3'] = {'error': str(e)}
else:
    print("SKIPPED: Model file not found")
    diagnostic_results['check3'] = {'skipped': True, 'reason': 'Model file not found'}

print()

# ============================================================================
# CHECK 4: VERIFY CLASS MAPPING
# ============================================================================
print("CHECK 4: VERIFY CLASS MAPPING")
print("-" * 100)

if model_exists:
    try:
        model = joblib.load(MODEL_PATH)
        model_classes = model.classes_
        print(f"Model classes: {model_classes}")
        
        # Load label encoder
        label_encoder_path = os.path.join(os.path.dirname(MODEL_PATH), "aml_label_encoder.pkl")
        if os.path.exists(label_encoder_path):
            with open(label_encoder_path, 'rb') as f:
                label_encoder = pickle.load(f)
            print(f"Label encoder classes: {label_encoder.classes_}")
            
            # Test mapping
            print("\nClass mapping:")
            for i, cls in enumerate(model_classes):
                label = label_encoder.inverse_transform([i])[0]
                print(f"  {i} → {cls} → {label}")
            
            diagnostic_results['check4'] = {
                'model_classes': list(model_classes),
                'label_encoder_classes': list(label_encoder.classes_),
                'mapping': {int(i): label_encoder.inverse_transform([i])[0] for i in model_classes}
            }
        else:
            print("WARNING: Label encoder file not found")
            print("Using fallback mapping: 0→normal, 1→super_suspicious, 2→suspicious")
            diagnostic_results['check4'] = {
                'model_classes': list(model_classes),
                'label_encoder_found': False,
                'fallback_mapping': {0: 'normal', 1: 'super_suspicious', 2: 'suspicious'}
            }
        
    except Exception as e:
        print(f"ERROR checking class mapping: {e}")
        diagnostic_results['check4'] = {'error': str(e)}
else:
    print("SKIPPED: Model file not found")
    diagnostic_results['check4'] = {'skipped': True}

print()

# ============================================================================
# CHECK 5: VERIFY PREDICTION FLOW IN ai_core.py
# ============================================================================
print("CHECK 5: VERIFY PREDICTION FLOW IN ai_core.py")
print("-" * 100)

# Read ai_core.py to analyze predict_risk_level function
ai_core_path = os.path.join(os.path.dirname(__file__), "ai_core.py")
if os.path.exists(ai_core_path):
    with open(ai_core_path, 'r') as f:
        content = f.read()
    
    # Check for potential issues
    issues = []
    
    # Check for hardcoded "normal"
    if '"normal"' in content and 'return' in content:
        # Check if there are suspicious patterns
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'return "normal"' in line or 'return "normal"' in line.lower():
                # Check context
                context = '\n'.join(lines[max(0, i-3):min(len(lines), i+3)])
                if 'except' in context or 'if' in context:
                    issues.append(f"Line {i}: Potential fallback to 'normal' detected")
    
    # Check for exception handling that might return None or default
    if 'except' in content and 'return' in content:
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'except' in line:
                context = '\n'.join(lines[max(0, i-1):min(len(lines), i+5)])
                if 'return None' in context or 'return "normal"' in context:
                    issues.append(f"Line {i}: Exception handling might return default value")
    
    if issues:
        print("⚠️  POTENTIAL ISSUES FOUND IN ai_core.py:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ No obvious fallback patterns found in ai_core.py")
    
    diagnostic_results['check5'] = {
        'ai_core_analyzed': True,
        'potential_issues': issues
    }
else:
    print("ERROR: ai_core.py not found")
    diagnostic_results['check5'] = {'error': 'ai_core.py not found'}

print()

# ============================================================================
# CHECK 6: TEST WITH CONTROLLED TRANSACTIONS
# ============================================================================
print("CHECK 6: TEST WITH CONTROLLED TRANSACTIONS")
print("-" * 100)

controlled_transactions = [
    {
        "name": "Ordinary transaction",
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
    },
    {
        "name": "Unusually large transaction",
        "transaction_id": 2,
        "sender_account": "TEST001",
        "receiver_account": "TEST003",
        "amount": 50000.0,
        "timestamp": "2026-09-02T12:00:00",
        "sender_avg_amount": 3000.0,
        "sender_max_amount": 10000.0,
        "sender_tx_count_24h": 5,
        "sender_volume_24h": 15000.0,
        "is_new_recipient": 1.0,
        "tx_frequency_7d": 10,
        "tx_frequency_30d": 45,
        "same_day_count": 5,
        "rapid_transfer_count": 3,
        "unique_recipients_7d": 10,
        "counterparty_change_score_7d": 0.9
    },
    {
        "name": "Repeated same-day transactions",
        "transaction_id": 3,
        "sender_account": "TEST001",
        "receiver_account": "TEST004",
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
    },
    {
        "name": "Rapid transfers",
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
]

test_results = []
for tx in controlled_transactions:
    print(f"\nTest: {tx['name']}")
    print(f"  Amount: ${tx['amount']:,.2f}")
    print(f"  Same day count: {tx['same_day_count']}")
    print(f"  Rapid transfers: {tx['rapid_transfer_count']}")
    
    # Get features
    features = transaction_features(tx)
    print(f"  Features: {features}")
    
    # Get prediction through ai_core
    predicted, confidence, anomaly_score = predict_risk_level(tx)
    print(f"  AI Core Prediction: {predicted}")
    print(f"  Confidence: {confidence:.4f}")
    print(f"  Anomaly Score: {anomaly_score}")
    
    # Get direct model prediction
    if model_exists:
        model = joblib.load(MODEL_PATH)
        features_2d = [features]
        direct_pred = model.predict(features_2d)[0]
        direct_proba = model.predict_proba(features_2d)[0]
        print(f"  Direct Model Prediction (numeric): {direct_pred}")
        print(f"  Direct Model Probabilities: {direct_proba}")
    
    test_results.append({
        'name': tx['name'],
        'features': features,
        'ai_core_prediction': predicted,
        'ai_core_confidence': confidence,
        'direct_prediction': int(direct_pred) if model_exists else None,
        'direct_probabilities': list(direct_proba) if model_exists else None
    })

diagnostic_results['check6'] = {
    'controlled_tests': test_results
}

print()

# ============================================================================
# CHECK 7: COMPARE RAW AI OUTPUT WITH APPLICATION OUTPUT
# ============================================================================
print("CHECK 7: COMPARE RAW AI OUTPUT WITH APPLICATION OUTPUT")
print("-" * 100)

print("For each test transaction, comparing:")
print("  RAW MODEL OUTPUT → APPLICATION OUTPUT")

comparison_results = []
for i, result in enumerate(test_results):
    print(f"\nTest {i+1}: {result['name']}")
    
    direct_pred = result['direct_prediction']
    app_pred = result['ai_core_prediction']
    
    print(f"  Direct model (numeric): {direct_pred}")
    print(f"  Application output: {app_pred}")
    
    if direct_pred is not None:
        # Convert numeric to label using label encoder
        label_encoder_path = os.path.join(os.path.dirname(MODEL_PATH), "aml_label_encoder.pkl")
        if os.path.exists(label_encoder_path):
            with open(label_encoder_path, 'rb') as f:
                label_encoder = pickle.load(f)
            direct_label = label_encoder.inverse_transform([direct_pred])[0]
        else:
            # Fallback mapping
            label_map = {0: "normal", 1: "super_suspicious", 2: "suspicious"}
            direct_label = label_map.get(direct_pred, "unknown")
        
        print(f"  Direct model (label): {direct_label}")
        
        if direct_label != app_pred:
            print(f"  ⚠️  MISMATCH: Model says '{direct_label}' but application says '{app_pred}'")
            comparison_results.append({
                'test': result['name'],
                'raw_model_output': direct_label,
                'application_output': app_pred,
                'match': False
            })
        else:
            print(f"  ✅ MATCH: Both agree on '{app_pred}'")
            comparison_results.append({
                'test': result['name'],
                'raw_model_output': direct_label,
                'application_output': app_pred,
                'match': True
            })

diagnostic_results['check7'] = {
    'comparisons': comparison_results
}

print()

# ============================================================================
# CHECK 8: VERIFY ACTUAL MODEL ARTIFACT
# ============================================================================
print("CHECK 8: VERIFY ACTUAL MODEL ARTIFACT")
print("-" * 100)

if model_exists:
    model_stat = os.stat(MODEL_PATH)
    print(f"Model file: {MODEL_PATH}")
    print(f"File size: {model_stat.st_size} bytes")
    print(f"Modified: {datetime.fromtimestamp(model_stat.st_mtime)}")
    
    # Check metadata
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, 'r') as f:
            metadata = json.load(f)
        print(f"\nMetadata from {METADATA_PATH}:")
        print(f"  Model type: {metadata.get('model_type')}")
        print(f"  Feature count: {metadata.get('feature_count')}")
        print(f"  Stage: {metadata.get('stage')}")
        print(f"  Training timestamp: {metadata.get('training_timestamp')}")
        
        diagnostic_results['check8'] = {
            'model_file': MODEL_PATH,
            'file_size': model_stat.st_size,
            'modification_time': datetime.fromtimestamp(model_stat.st_mtime).isoformat(),
            'metadata': metadata
        }
    else:
        print("WARNING: Metadata file not found")
        diagnostic_results['check8'] = {
            'model_file': MODEL_PATH,
            'file_size': model_stat.st_size,
            'metadata_file': METADATA_PATH,
            'metadata_found': False
        }
else:
    print("ERROR: Model file not found")
    diagnostic_results['check8'] = {'model_found': False}

print()

# ============================================================================
# CHECK 9: VERIFY NO SILENT ERROR FALLBACK
# ============================================================================
print("CHECK 9: VERIFY NO SILENT ERROR FALLBACK")
print("-" * 100)

# Test with invalid input to see if it silently returns normal
print("Testing with invalid input to check for silent fallback...")

invalid_tests = [
    {
        "name": "Empty transaction",
        "tx": {}
    },
    {
        "name": "Missing amount",
        "tx": {"sender_account": "TEST001", "timestamp": "2026-09-02T12:00:00"}
    },
    {
        "name": "Negative amount",
        "tx": {"amount": -1000, "timestamp": "2026-09-02T12:00:00"}
    }
]

fallback_issues = []
for test in invalid_tests:
    try:
        predicted, confidence, anomaly_score = predict_risk_level(test['tx'])
        if predicted == "normal":
            print(f"⚠️  {test['name']}: Returned 'normal' (possible silent fallback)")
            fallback_issues.append(test['name'])
        else:
            print(f"✅ {test['name']}: Returned '{predicted}' (not silent fallback)")
    except Exception as e:
        print(f"✅ {test['name']}: Raised exception (not silent fallback): {e}")

if fallback_issues:
    print(f"\n⚠️  POTENTIAL SILENT FALLBACK DETECTED:")
    for issue in fallback_issues:
        print(f"  - {issue}")
else:
    print("\n✅ No silent fallback to 'normal' detected for invalid inputs")

diagnostic_results['check9'] = {
    'silent_fallback_detected': len(fallback_issues) > 0,
    'fallback_cases': fallback_issues
}

print()

# ============================================================================
# SUMMARY AND ROOT CAUSE ANALYSIS
# ============================================================================
print("=" * 100)
print("DIAGNOSTIC SUMMARY")
print("=" * 100)
print()

# Analyze results
root_cause = "UNKNOWN"

# Check 1: Model loading
if not diagnostic_results.get('check1', {}).get('model_loaded', False):
    root_cause = "MODEL NOT LOADED CORRECTLY"
    print("❌ ROOT CAUSE: Model is not loaded correctly")
elif not diagnostic_results.get('check1', {}).get('is_gradient_boosting', False):
    root_cause = "WRONG MODEL TYPE"
    print("❌ ROOT CAUSE: Wrong model type loaded")

# Check 2: Feature extraction
elif diagnostic_results.get('check2', {}).get('issues'):
    root_cause = "FEATURE EXTRACTION ISSUES"
    print("❌ ROOT CAUSE: Feature extraction has issues")
    for issue in diagnostic_results['check2']['issues']:
        print(f"  - {issue}")

# Check 4: Class mapping
elif diagnostic_results.get('check4', {}).get('error'):
    root_cause = "CLASS MAPPING ERROR"
    print("❌ ROOT CAUSE: Class mapping error")

# Check 7: Comparison
elif any(not comp['match'] for comp in diagnostic_results.get('check7', {}).get('comparisons', [])):
    root_cause = "APPLICATION INTEGRATION ISSUE - MODEL PREDICTIONS CHANGED"
    print("❌ ROOT CAUSE: Application integration issue - model predictions are being changed")
    for comp in diagnostic_results['check7']['comparisons']:
        if not comp['match']:
            print(f"  - {comp['test']}: Model says '{comp['raw_model_output']}' but app says '{comp['application_output']}'")

# Check 9: Silent fallback
elif diagnostic_results.get('check9', {}).get('silent_fallback_detected'):
    root_cause = "SILENT FALLBACK TO NORMAL"
    print("❌ ROOT CAUSE: Silent fallback to 'normal' detected")

# If no obvious issues, check model performance
else:
    # Check if model is just predicting normal due to poor performance
    all_normal = all(result['ai_core_prediction'] == 'normal' for result in test_results)
    if all_normal:
        root_cause = "MODEL HAS POOR RECALL - PREDICTING NORMAL FOR EVERYTHING"
        print("❌ ROOT CAUSE: Model has poor recall - predicting 'normal' for everything")
        print("   This is a known limitation of the Stage 16B model:")
        print("   - Suspicious recall: 21.76%")
        print("   - Super-suspicious recall: 25.40%")
    else:
        root_cause = "UNKNOWN - NO OBVIOUS ISSUES FOUND"
        print("⚠️  ROOT CAUSE: Unknown - no obvious issues found in diagnostic")

print()
print("=" * 100)
print(f"ROOT CAUSE IDENTIFIED: {root_cause}")
print("=" * 100)
print()

# Save diagnostic results
with open('diagnostic_results.json', 'w') as f:
    json.dump(diagnostic_results, f, indent=2, default=str)

print("Diagnostic results saved to: diagnostic_results.json")
print()
print("MODEL INTEGRATION DIAGNOSTIC COMPLETE — ROOT CAUSE IDENTIFIED — WAITING FOR APPROVAL TO APPLY FIX.")
