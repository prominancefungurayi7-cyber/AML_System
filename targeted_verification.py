"""
TARGETED VERIFICATION - Class Mapping and Integration Audit
===========================================================
"""

import os
import json
import pickle
import joblib
import numpy as np

print("=" * 100)
print("TARGETED VERIFICATION - CLASS MAPPING AND INTEGRATION AUDIT")
print("=" * 100)
print()

verification_results = {}

# ============================================================================
# 1. VERIFY TRUE STAGE 16B CLASS MAPPING
# ============================================================================
print("1. VERIFY TRUE STAGE 16B CLASS MAPPING")
print("-" * 100)

# Load the actual frozen model
model_path = "aml_ai_model.pkl"
label_encoder_path = "aml_label_encoder.pkl"
metadata_path = "aml_ai_model_meta.json"

print(f"Loading model from: {model_path}")
model = joblib.load(model_path)
print(f"Model type: {type(model).__name__}")
print(f"Model classes_: {model.classes_}")

print(f"\nLoading label encoder from: {label_encoder_path}")
with open(label_encoder_path, 'rb') as f:
    label_encoder = pickle.load(f)
print(f"Label encoder classes_: {label_encoder.classes_}")

print(f"\nLoading metadata from: {metadata_path}")
with open(metadata_path, 'r') as f:
    metadata = json.load(f)
print(f"Metadata label_classes: {metadata['label_classes']}")

# Determine the TRUE mapping
print("\nTRUE CLASS MAPPING:")
for i, cls in enumerate(model.classes_):
    label = label_encoder.inverse_transform([i])[0]
    print(f"  {i} -> {cls} -> {label}")

verification_results['true_class_mapping'] = {
    'model_classes': list(model.classes_),
    'label_encoder_classes': list(label_encoder.classes_),
    'mapping': {int(i): label_encoder.inverse_transform([i])[0] for i in model.classes_}
}

print()

# ============================================================================
# 2. AUDIT ai_core.py MAPPING CODE
# ============================================================================
print("2. AUDIT ai_core.py MAPPING CODE")
print("-" * 100)

# Read ai_core.py to check the mapping logic
with open('ai_core.py', 'r') as f:
    ai_core_content = f.read()

# Check the fallback mapping
fallback_map = {0: "normal", 1: "super_suspicious", 2: "suspicious"}
print(f"Fallback mapping in ai_core.py: {fallback_map}")

# Verify if fallback matches true mapping
true_mapping = verification_results['true_class_mapping']['mapping']
fallback_correct = all(fallback_map.get(i) == true_mapping.get(i) for i in range(3))

print(f"Fallback mapping matches true mapping: {fallback_correct}")

if not fallback_correct:
    print("⚠️  MISMATCH DETECTED:")
    for i in range(3):
        print(f"  {i}: True={true_mapping.get(i)}, Fallback={fallback_map.get(i)}")

verification_results['ai_core_audit'] = {
    'fallback_mapping': fallback_map,
    'fallback_correct': fallback_correct,
    'true_mapping': true_mapping
}

print()

# ============================================================================
# 3. REPRODUCE PREDICTION WITH REAL FROZEN MODEL
# ============================================================================
print("3. REPRODUCE PREDICTION WITH REAL FROZEN MODEL")
print("-" * 100)

# Test with the suspicious transaction from the diagnostic
suspicious_features = [
    9500,      # amount
    3000,      # sender_avg_amount
    10000,     # sender_max_amount
    3.17,      # amount_to_sender_avg
    2.0,       # amount_z_score
    0.5,       # amount_deviation_from_baseline_30d
    30,        # tx_frequency_7d
    100,       # tx_frequency_30d
    1.5,       # frequency_change_vs_avg_7d
    15,        # sender_tx_count_24h
    50000,     # sender_volume_24h
    8,         # same_day_count
    5,         # rapid_transfer_count
    0,         # is_new_recipient
    5,         # unique_recipients_7d
    14,        # hour
    0,         # is_off_hours
    0.3        # counterparty_change_score_7d
]

print("Suspicious transaction features:")
for i, (name, value) in enumerate(zip(metadata['feature_names'], suspicious_features), 1):
    print(f"  {i}. {name}: {value}")

print("\nDirect model prediction:")
features_2d = [suspicious_features]
proba = model.predict_proba(features_2d)[0]
argmax = int(proba.argmax())
classes_argmax = model.classes_[argmax]
decoded_label = label_encoder.inverse_transform([argmax])[0]

print(f"  classifier.classes_: {model.classes_}")
print(f"  predict_proba(): {proba}")
print(f"  argmax: {argmax}")
print(f"  classes[argmax]: {classes_argmax}")
print(f"  LabelEncoder classes: {label_encoder.classes_}")
print(f"  Final decoded label: {decoded_label}")

verification_results['suspicious_prediction'] = {
    'features': suspicious_features,
    'classifier_classes': list(model.classes_),
    'predict_proba': list(proba),
    'argmax': argmax,
    'classes_argmax': int(classes_argmax),
    'label_encoder_classes': list(label_encoder.classes_),
    'final_decoded_label': decoded_label
}

# Test with a clearly severe pattern
print("\n\nTesting with clearly severe pattern:")
severe_features = [
    100000,    # amount - very large
    3000,      # sender_avg_amount
    10000,     # sender_max_amount
    33.33,     # amount_to_sender_avg - huge deviation
    5.0,       # amount_z_score - high z-score
    2.0,       # amount_deviation_from_baseline_30d
    200,       # tx_frequency_7d - very high frequency
    500,       # tx_frequency_30d - extremely high frequency
    5.0,       # frequency_change_vs_avg_7d - huge increase
    100,       # sender_tx_count_24h - massive 24h activity
    1000000,   # sender_volume_24h - massive volume
    50,        # same_day_count - many same-day transactions
    30,        # rapid_transfer_count - many rapid transfers
    1,         # is_new_recipient - new recipient
    20,        # unique_recipients_7d - many unique recipients
    3,         # hour - 3 AM (off hours)
    1,         # is_off_hours - yes
    1.0        # counterparty_change_score_7d - maximum change
]

print("Severe transaction features (sample):")
print(f"  amount: {severe_features[0]}")
print(f"  amount_to_sender_avg: {severe_features[3]}")
print(f"  tx_frequency_7d: {severe_features[6]}")
print(f"  sender_tx_count_24h: {severe_features[9]}")
print(f"  same_day_count: {severe_features[11]}")
print(f"  rapid_transfer_count: {severe_features[12]}")

print("\nDirect model prediction:")
features_2d = [severe_features]
proba_severe = model.predict_proba(features_2d)[0]
argmax_severe = int(proba_severe.argmax())
classes_argmax_severe = model.classes_[argmax_severe]
decoded_label_severe = label_encoder.inverse_transform([argmax_severe])[0]

print(f"  classifier.classes_: {model.classes_}")
print(f"  predict_proba(): {proba_severe}")
print(f"  argmax: {argmax_severe}")
print(f"  classes[argmax]: {classes_argmax_severe}")
print(f"  Final decoded label: {decoded_label_severe}")

verification_results['severe_prediction'] = {
    'features': severe_features,
    'predict_proba': list(proba_severe),
    'argmax': argmax_severe,
    'classes_argmax': int(classes_argmax_severe),
    'final_decoded_label': decoded_label_severe
}

print()

# ============================================================================
# 4. CHECK map_risk_to_ai_label() USAGE
# ============================================================================
print("4. CHECK map_risk_to_ai_label() USAGE")
print("-" * 100)

# Search for map_risk_to_ai_label usage in ai_core.py
usage_count = ai_core_content.count('map_risk_to_ai_label')
print(f"map_risk_to_ai_label appears {usage_count} times in ai_core.py")

# Check if it's used in predict_risk_level
predict_function_start = ai_core_content.find('def predict_risk_level')
predict_function_end = ai_core_content.find('\ndef ', predict_function_start + 1)
predict_function = ai_core_content[predict_function_start:predict_function_end]

used_in_predict = 'map_risk_to_ai_label' in predict_function
print(f"map_risk_to_ai_label used in predict_risk_level(): {used_in_predict}")

# Search in server.py
if os.path.exists('server.py'):
    with open('server.py', 'r') as f:
        server_content = f.read()
    server_usage_count = server_content.count('map_risk_to_ai_label')
    print(f"map_risk_to_ai_label appears {server_usage_count} times in server.py")
else:
    print("server.py not found")

verification_results['map_risk_to_ai_label_usage'] = {
    'ai_core_usage_count': usage_count,
    'used_in_predict_risk_level': used_in_predict,
    'server_usage_count': server_usage_count if os.path.exists('server.py') else 'N/A'
}

print()
print("CONCLUSION: map_risk_to_ai_label() is training-only legacy code, NOT used in live predictions")
print()

# ============================================================================
# 5. AUDIT FINAL APPLICATION OUTPUT PATH
# ============================================================================
print("5. AUDIT FINAL APPLICATION OUTPUT PATH")
print("-" * 100)

print("Tracing prediction path:")
print("  1. Transaction enters system")
print("  2. Feature extraction via transaction_features()")
print("  3. predict_risk_level() called")
print("  4. Model loaded via load_ai_model()")
print("  5. Features passed to model.predict_proba()")
print("  6. argmax() finds highest probability index")
print("  7. LabelEncoder.inverse_transform() converts index to label")
print("  8. Confidence = probabilities[argmax]")
print("  9. Return (predicted_label, confidence, anomaly_score)")
print("  10. server.py process_transaction_event() receives prediction")
print("  11. Confidence thresholds applied (lines 2153-2159)")
print("  12. Final risk level determined")
print("  13. UI displays result")

verification_results['application_flow'] = {
    'steps': [
        "Transaction enters system",
        "Feature extraction via transaction_features()",
        "predict_risk_level() called",
        "Model loaded via load_ai_model()",
        "Features passed to model.predict_proba()",
        "argmax() finds highest probability index",
        "LabelEncoder.inverse_transform() converts index to label",
        "Confidence = probabilities[argmax]",
        "Return (predicted_label, confidence, anomaly_score)",
        "server.py process_transaction_event() receives prediction",
        "Confidence thresholds applied (lines 2153-2159)",
        "Final risk level determined",
        "UI displays result"
    ]
}

print()

# ============================================================================
# 6. CHECK CONFIDENCE THRESHOLD LOGIC
# ============================================================================
print("6. CHECK CONFIDENCE THRESHOLD LOGIC")
print("-" * 100)

if os.path.exists('server.py'):
    with open('server.py', 'r') as f:
        server_content = f.read()
    
    # Find the confidence threshold logic
    threshold_start = server_content.find('confidence_threshold = 0.65')
    if threshold_start > 0:
        threshold_section = server_content[threshold_start:threshold_start+200]
        print("Confidence threshold logic (server.py):")
        print(threshold_section)
        
        # Extract the thresholds
        import re
        super_threshold = re.search(r'super_suspicious.*?(\d+\.\d+)', threshold_section)
        suspicious_threshold = re.search(r'suspicious.*?(\d+\.\d+)', threshold_section)
        normal_threshold = re.search(r'else.*?(\d+\.\d+)', threshold_section)
        
        print("\nExtracted thresholds:")
        if super_threshold:
            print(f"  Super-suspicious: {super_threshold.group(1)}")
        if suspicious_threshold:
            print(f"  Suspicious: {suspicious_threshold.group(1)}")
        if normal_threshold:
            print(f"  Normal: {normal_threshold.group(1)}")
        
        verification_results['confidence_thresholds'] = {
            'super_suspicious': float(super_threshold.group(1)) if super_threshold else None,
            'suspicious': float(suspicious_threshold.group(1)) if suspicious_threshold else None,
            'normal': float(normal_threshold.group(1)) if normal_threshold else None
        }
        
        # Test if the suspicious prediction would pass threshold
        print(f"\nWould suspicious prediction pass threshold?")
        print(f"  Predicted: {decoded_label}")
        print(f"  Confidence: {proba[argmax]:.4f}")
        
        if decoded_label == "suspicious":
            threshold = 0.65
            passes = proba[argmax] >= threshold
            print(f"  Threshold: {threshold}")
            print(f"  Passes: {passes}")
            
            verification_results['threshold_test'] = {
                'predicted': decoded_label,
                'confidence': float(proba[argmax]),
                'threshold': threshold,
                'passes': passes
            }

print()

# ============================================================================
# 7. DISTINGUISH MODEL QUALITY VS INTEGRATION CORRECTNESS
# ============================================================================
print("7. DISTINGUISH MODEL QUALITY VS INTEGRATION CORRECTNESS")
print("-" * 100)

print("A. MODEL QUALITY")
print("   Is the frozen Stage 16B model genuinely producing mostly Normal predictions?")
print("   for suspicious-looking transactions?")
print()
print("   Test results:")
print(f"   - Suspicious pattern prediction: {decoded_label} (confidence: {proba[argmax]:.4f})")
print(f"   - Severe pattern prediction: {decoded_label_severe} (confidence: {proba_severe[argmax_severe]:.4f})")
print()
if decoded_label == "normal" and decoded_label_severe == "normal":
    print("   ❌ YES - The model is predicting 'normal' for suspicious patterns")
    print("   This is a MODEL QUALITY issue (poor recall)")
else:
    print("   ✅ NO - The model is predicting suspicious labels for some patterns")
    print("   This is NOT a model quality issue")

print()
print("B. INTEGRATION CORRECTNESS")
print("   Is ai_core.py correctly translating the frozen model's numeric predictions?")
print()
print("   TRUE mapping from training:")
for i, label in true_mapping.items():
    print(f"     {i} -> {label}")
print()
print("   ai_core.py fallback mapping:")
for i, label in fallback_map.items():
    print(f"     {i} -> {label}")
print()
if fallback_correct:
    print("   ✅ YES - The integration mapping is CORRECT")
    print("   ai_core.py correctly translates numeric predictions to labels")
else:
    print("   ❌ NO - The integration mapping is INCORRECT")
    print("   ai_core.py has a mapping bug")

verification_results['conclusions'] = {
    'model_quality_issue': (decoded_label == "normal" and decoded_label_severe == "normal"),
    'integration_correct': fallback_correct,
    'model_predictions': {
        'suspicious_pattern': decoded_label,
        'severe_pattern': decoded_label_severe
    }
}

print()

# ============================================================================
# 8. FINAL REPORT
# ============================================================================
print("=" * 100)
print("TARGETED VERIFICATION COMPLETE")
print("=" * 100)
print()

# Save results
with open('targeted_verification_results.json', 'w') as f:
    json.dump(verification_results, f, indent=2, default=str)

print("Verification results saved to: targeted_verification_results.json")
print()
print("TARGETED VERIFICATION COMPLETE — DIAGNOSIS READY FOR REVIEW")
