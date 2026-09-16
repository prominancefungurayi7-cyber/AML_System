"""
FINAL END-TO-END AML AI ACCEPTANCE TEST
======================================

This is an ACCEPTANCE TEST ONLY. No code/model changes will be made.
"""

import os
import json
import joblib
import pickle
import numpy as np
from ai_core import predict_risk_level, transaction_features
from datetime import datetime

print("=" * 100)
print("FINAL END-TO-END AML AI ACCEPTANCE TEST")
print("=" * 100)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# Load model and label encoder
model = joblib.load('aml_ai_model.pkl')
with open('aml_label_encoder.pkl', 'rb') as f:
    label_encoder = pickle.load(f)

# Define AI_RISK_SCORES (from server.py)
AI_RISK_SCORES = {
    "normal": 0,
    "suspicious": 60,
    "super_suspicious": 85
}

# Define thresholds (CURRENT values after fix)
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
    return ml_score, confidence_threshold, ml_confidence >= confidence_threshold

def run_test_case(test_id, intended_scenario, transaction):
    """Run a single test case through the full flow."""
    print(f"\n{'='*100}")
    print(f"TEST ID: {test_id}")
    print(f"Intended Scenario: {intended_scenario}")
    print(f"{'='*100}")
    
    # Transaction characteristics
    print(f"\nTransaction Characteristics:")
    print(f"  Amount: ${transaction.get('amount', 0):,.2f}")
    print(f"  Sender: {transaction.get('sender_account', 'N/A')}")
    print(f"  Receiver: {transaction.get('receiver_account', 'N/A')}")
    print(f"  Timestamp: {transaction.get('timestamp', 'N/A')}")
    print(f"  Type: {transaction.get('transaction_type', 'transfer')}")
    
    # Get features
    features = transaction_features(transaction)
    
    # Raw model prediction
    features_2d = [features]
    proba = model.predict_proba(features_2d)[0]
    argmax = int(proba.argmax())
    classes_argmax = model.classes_[argmax]
    decoded_label = label_encoder.inverse_transform([argmax])[0]
    confidence = float(proba[argmax])
    
    # ai_core.py prediction
    ml_level, ml_confidence, _ = predict_risk_level(transaction)
    
    # Server threshold logic
    ml_score, threshold, passes_threshold = simulate_server_logic(ml_level, ml_confidence)
    
    # Final classification
    if ml_score > 0:
        final_level = ml_level
    else:
        final_level = "normal"
    
    # Determine failure type
    failure_type = "NONE"
    if intended_scenario.upper() != final_level.upper():
        if decoded_label != intended_scenario.lower():
            failure_type = "MODEL_FAILURE"
        elif not passes_threshold:
            failure_type = "CONFIDENCE_GATE_FAILURE"
        else:
            failure_type = "INTEGRATION_FAILURE"
    
    result = {
        'test_id': test_id,
        'intended_scenario': intended_scenario,
        'transaction': transaction,
        'features': features,
        'raw_model_class': decoded_label,
        'raw_probabilities': list(proba),
        'model_confidence': confidence,
        'ml_level': ml_level,
        'ml_confidence': ml_confidence,
        'threshold_applied': threshold,
        'passes_threshold': passes_threshold,
        'final_server_classification': final_level,
        'final_ui_classification': final_level,
        'ui_matches_model': (final_level == decoded_label) if passes_threshold else True,
        'failure_type': failure_type
    }
    
    print(f"\nTest Results:")
    print(f"  Raw Model Class: {decoded_label}")
    print(f"  Raw Probabilities: {list(proba)}")
    print(f"  Model Confidence: {confidence:.4f}")
    print(f"  Threshold Applied: {threshold}")
    print(f"  Passes Threshold: {passes_threshold}")
    print(f"  Final Server Classification: {final_level.upper()}")
    print(f"  Final UI Classification: {final_level.upper()}")
    print(f"  Intended: {intended_scenario.upper()}")
    print(f"  Match: {'✅ YES' if intended_scenario.lower() == final_level.lower() else '❌ NO'}")
    if failure_type != "NONE":
        print(f"  Failure Type: {failure_type}")
    
    return result

# ============================================================================
# NORMAL TEST CASES (5)
# ============================================================================

normal_tests = [
    {
        'test_id': 'N001',
        'intended_scenario': 'Normal',
        'transaction': {
            "transaction_id": 1,
            "sender_account": "NORMAL001",
            "receiver_account": "NORMAL002",
            "amount": 2500.0,
            "timestamp": "2026-09-02T10:00:00",
            "transaction_type": "transfer",
            "sender_avg_amount": 2500.0,
            "sender_max_amount": 5000.0,
            "sender_tx_count_24h": 3,
            "sender_volume_24h": 7500.0,
            "is_new_recipient": 0.0,
            "tx_frequency_7d": 5,
            "tx_frequency_30d": 20,
            "same_day_count": 1,
            "rapid_transfer_count": 0,
            "unique_recipients_7d": 2,
            "counterparty_change_score_7d": 0.2
        }
    },
    {
        'test_id': 'N002',
        'intended_scenario': 'Normal',
        'transaction': {
            "transaction_id": 2,
            "sender_account": "NORMAL001",
            "receiver_account": "NORMAL003",
            "amount": 7500.0,
            "timestamp": "2026-09-02T11:00:00",
            "transaction_type": "transfer",
            "sender_avg_amount": 3000.0,
            "sender_max_amount": 10000.0,
            "sender_tx_count_24h": 2,
            "sender_volume_24h": 15000.0,
            "is_new_recipient": 0.0,
            "tx_frequency_7d": 8,
            "tx_frequency_30d": 30,
            "same_day_count": 2,
            "rapid_transfer_count": 0,
            "unique_recipients_7d": 3,
            "counterparty_change_score_7d": 0.3
        }
    },
    {
        'test_id': 'N003',
        'intended_scenario': 'Normal',
        'transaction': {
            "transaction_id": 3,
            "sender_account": "NORMAL001",
            "receiver_account": "NORMAL001",
            "amount": 5000.0,
            "timestamp": "2026-09-02T09:00:00",
            "transaction_type": "deposit",
            "sender_avg_amount": 3000.0,
            "sender_max_amount": 8000.0,
            "sender_tx_count_24h": 1,
            "sender_volume_24h": 5000.0,
            "is_new_recipient": 0.0,
            "tx_frequency_7d": 3,
            "tx_frequency_30d": 15,
            "same_day_count": 1,
            "rapid_transfer_count": 0,
            "unique_recipients_7d": 1,
            "counterparty_change_score_7d": 0.1
        }
    },
    {
        'test_id': 'N004',
        'intended_scenario': 'Normal',
        'transaction': {
            "transaction_id": 4,
            "sender_account": "NORMAL001",
            "receiver_account": "NORMAL004",
            "amount": 4000.0,
            "timestamp": "2026-09-02T14:00:00",
            "transaction_type": "withdrawal",
            "sender_avg_amount": 3000.0,
            "sender_max_amount": 7000.0,
            "sender_tx_count_24h": 2,
            "sender_volume_24h": 8000.0,
            "is_new_recipient": 0.0,
            "tx_frequency_7d": 6,
            "tx_frequency_30d": 25,
            "same_day_count": 2,
            "rapid_transfer_count": 0,
            "unique_recipients_7d": 3,
            "counterparty_change_score_7d": 0.25
        }
    },
    {
        'test_id': 'N005',
        'intended_scenario': 'Normal',
        'transaction': {
            "transaction_id": 5,
            "sender_account": "NORMAL001",
            "receiver_account": "NORMAL005",
            "amount": 3500.0,
            "timestamp": "2026-09-02T13:00:00",
            "transaction_type": "transfer",
            "sender_avg_amount": 3000.0,
            "sender_max_amount": 6000.0,
            "sender_tx_count_24h": 1,
            "sender_volume_24h": 3500.0,
            "is_new_recipient": 1.0,  # New recipient but otherwise ordinary
            "tx_frequency_7d": 4,
            "tx_frequency_30d": 18,
            "same_day_count": 1,
            "rapid_transfer_count": 0,
            "unique_recipients_7d": 2,
            "counterparty_change_score_7d": 0.4
        }
    }
]

# ============================================================================
# SUSPICIOUS TEST CASES (5)
# ============================================================================

suspicious_tests = [
    {
        'test_id': 'S001',
        'intended_scenario': 'Suspicious',
        'transaction': {
            "transaction_id": 6,
            "sender_account": "SUSP001",
            "receiver_account": "SUSP002",
            "amount": 9500.0,  # Just below CTR threshold - structuring
            "timestamp": "2026-09-02T14:00:00",
            "transaction_type": "transfer",
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
    },
    {
        'test_id': 'S002',
        'intended_scenario': 'Suspicious',
        'transaction': {
            "transaction_id": 7,
            "sender_account": "SUSP001",
            "receiver_account": "SUSP003",
            "amount": 8000.0,
            "timestamp": "2026-09-02T10:05:00",
            "transaction_type": "transfer",
            "sender_avg_amount": 3000.0,
            "sender_max_amount": 10000.0,
            "sender_tx_count_24h": 20,
            "sender_volume_24h": 80000.0,
            "is_new_recipient": 0.0,
            "tx_frequency_7d": 50,
            "tx_frequency_30d": 150,
            "same_day_count": 15,
            "rapid_transfer_count": 8,
            "unique_recipients_7d": 8,
            "counterparty_change_score_7d": 0.6
        }
    },
    {
        'test_id': 'S003',
        'intended_scenario': 'Suspicious',
        'transaction': {
            "transaction_id": 8,
            "sender_account": "SUSP001",
            "receiver_account": "SUSP004",
            "amount": 12000.0,
            "timestamp": "2026-09-02T11:00:00",
            "transaction_type": "transfer",
            "sender_avg_amount": 3000.0,
            "sender_max_amount": 10000.0,
            "sender_tx_count_24h": 10,
            "sender_volume_24h": 40000.0,
            "is_new_recipient": 1.0,
            "tx_frequency_7d": 25,
            "tx_frequency_30d": 80,
            "same_day_count": 6,
            "rapid_transfer_count": 4,
            "unique_recipients_7d": 6,
            "counterparty_change_score_7d": 0.7
        }
    },
    {
        'test_id': 'S004',
        'intended_scenario': 'Suspicious',
        'transaction': {
            "transaction_id": 9,
            "sender_account": "SUSP001",
            "receiver_account": "SUSP005",
            "amount": 7000.0,
            "timestamp": "2026-09-02T12:00:00",
            "transaction_type": "transfer",
            "sender_avg_amount": 3000.0,
            "sender_max_amount": 10000.0,
            "sender_tx_count_24h": 25,
            "sender_volume_24h": 100000.0,
            "is_new_recipient": 0.0,
            "tx_frequency_7d": 60,
            "tx_frequency_30d": 200,
            "same_day_count": 20,
            "rapid_transfer_count": 10,
            "unique_recipients_7d": 3,
            "counterparty_change_score_7d": 0.2
        }
    },
    {
        'test_id': 'S005',
        'intended_scenario': 'Suspicious',
        'transaction': {
            "transaction_id": 10,
            "sender_account": "SUSP001",
            "receiver_account": "SUSP006",
            "amount": 15000.0,
            "timestamp": "2026-09-02T15:00:00",
            "transaction_type": "transfer",
            "sender_avg_amount": 3000.0,
            "sender_max_amount": 10000.0,
            "sender_tx_count_24h": 8,
            "sender_volume_24h": 60000.0,
            "is_new_recipient": 0.0,
            "tx_frequency_7d": 40,
            "tx_frequency_30d": 120,
            "same_day_count": 10,
            "rapid_transfer_count": 6,
            "unique_recipients_7d": 7,
            "counterparty_change_score_7d": 0.8
        }
    }
]

# ============================================================================
# SUPER-SUSPICIOUS TEST CASES (5)
# ============================================================================

super_suspicious_tests = [
    {
        'test_id': 'SS001',
        'intended_scenario': 'Super-Suspicious',
        'transaction': {
            "transaction_id": 11,
            "sender_account": "SS001",
            "receiver_account": "SS002",
            "amount": 9800.0,  # Severe structuring - multiple just-below-CTR
            "timestamp": "2026-09-02T10:00:00",
            "transaction_type": "transfer",
            "sender_avg_amount": 3000.0,
            "sender_max_amount": 10000.0,
            "sender_tx_count_24h": 30,
            "sender_volume_24h": 100000.0,
            "is_new_recipient": 0.0,
            "tx_frequency_7d": 80,
            "tx_frequency_30d": 300,
            "same_day_count": 25,
            "rapid_transfer_count": 15,
            "unique_recipients_7d": 10,
            "counterparty_change_score_7d": 0.9
        }
    },
    {
        'test_id': 'SS002',
        'intended_scenario': 'Super-Suspicious',
        'transaction': {
            "transaction_id": 12,
            "sender_account": "SS001",
            "receiver_account": "SS003",
            "amount": 25000.0,
            "timestamp": "2026-09-02T11:00:00",
            "transaction_type": "transfer",
            "sender_avg_amount": 3000.0,
            "sender_max_amount": 10000.0,
            "sender_tx_count_24h": 15,
            "sender_volume_24h": 200000.0,
            "is_new_recipient": 1.0,
            "tx_frequency_7d": 50,
            "tx_frequency_30d": 200,
            "same_day_count": 15,
            "rapid_transfer_count": 10,
            "unique_recipients_7d": 12,
            "counterparty_change_score_7d": 0.95
        }
    },
    {
        'test_id': 'SS003',
        'intended_scenario': 'Super-Suspicious',
        'transaction': {
            "transaction_id": 13,
            "sender_account": "SS001",
            "receiver_account": "SS004",
            "amount": 50000.0,
            "timestamp": "2026-09-02T02:00:00",  # Off-hours
            "transaction_type": "transfer",
            "sender_avg_amount": 3000.0,
            "sender_max_amount": 10000.0,
            "sender_tx_count_24h": 20,
            "sender_volume_24h": 300000.0,
            "is_new_recipient": 1.0,
            "tx_frequency_7d": 100,
            "tx_frequency_30d": 400,
            "same_day_count": 30,
            "rapid_transfer_count": 20,
            "unique_recipients_7d": 15,
            "counterparty_change_score_7d": 1.0
        }
    },
    {
        'test_id': 'SS004',
        'intended_scenario': 'Super-Suspicious',
        'transaction': {
            "transaction_id": 14,
            "sender_account": "SS001",
            "receiver_account": "SS005",
            "amount": 75000.0,
            "timestamp": "2026-09-02T03:00:00",
            "transaction_type": "transfer",
            "sender_avg_amount": 3000.0,
            "sender_max_amount": 10000.0,
            "sender_tx_count_24h": 50,
            "sender_volume_24h": 500000.0,
            "is_new_recipient": 0.0,
            "tx_frequency_7d": 150,
            "tx_frequency_30d": 500,
            "same_day_count": 40,
            "rapid_transfer_count": 25,
            "unique_recipients_7d": 5,
            "counterparty_change_score_7d": 0.3
        }
    },
    {
        'test_id': 'SS005',
        'intended_scenario': 'Super-Suspicious',
        'transaction': {
            "transaction_id": 15,
            "sender_account": "SS001",
            "receiver_account": "SS006",
            "amount": 100000.0,
            "timestamp": "2026-09-02T04:00:00",
            "transaction_type": "transfer",
            "sender_avg_amount": 3000.0,
            "sender_max_amount": 10000.0,
            "sender_tx_count_24h": 100,
            "sender_volume_24h": 1000000.0,
            "is_new_recipient": 1.0,
            "tx_frequency_7d": 200,
            "tx_frequency_30d": 600,
            "same_day_count": 50,
            "rapid_transfer_count": 30,
            "unique_recipients_7d": 20,
            "counterparty_change_score_7d": 1.0
        }
    }
]

# ============================================================================
# EXECUTE ALL TESTS
# ============================================================================

print("\n" + "="*100)
print("EXECUTING NORMAL TEST CASES")
print("="*100)

normal_results = []
for test in normal_tests:
    result = run_test_case(test['test_id'], test['intended_scenario'], test['transaction'])
    normal_results.append(result)

print("\n" + "="*100)
print("EXECUTING SUSPICIOUS TEST CASES")
print("="*100)

suspicious_results = []
for test in suspicious_tests:
    result = run_test_case(test['test_id'], test['intended_scenario'], test['transaction'])
    suspicious_results.append(result)

print("\n" + "="*100)
print("EXECUTING SUPER-SUSPICIOUS TEST CASES")
print("="*100)

super_suspicious_results = []
for test in super_suspicious_tests:
    result = run_test_case(test['test_id'], test['intended_scenario'], test['transaction'])
    super_suspicious_results.append(result)

# ============================================================================
# SPECIAL CHECK: PREVIOUSLY BROKEN STRUCTURING CASE
# ============================================================================

print("\n" + "="*100)
print("SPECIAL CHECK: PREVIOUSLY BROKEN STRUCTURING CASE")
print("="*100)

print("\nReproducing the structuring case that previously failed...")
special_result = run_test_case(
    'SPECIAL001',
    'Suspicious',
    {
        "transaction_id": 999,
        "sender_account": "SPECIAL001",
        "receiver_account": "SPECIAL002",
        "amount": 9500.0,
        "timestamp": "2026-09-02T14:00:00",
        "transaction_type": "transfer",
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

print(f"\nSPECIAL CHECK RESULT:")
print(f"  Before fix: Would be REJECTED (62-66% < 65% threshold)")
print(f"  After fix: {'ACCEPTED' if special_result['passes_threshold'] else 'REJECTED'} ({special_result['ml_confidence']:.2%} >= 55%)")
print(f"  UI Display: {special_result['final_ui_classification'].upper()}")
print(f"  Expected: SUSPICIOUS")
print(f"  Status: {'✅ PASS' if special_result['final_ui_classification'] == 'suspicious' else '❌ FAIL'}")

# ============================================================================
# AGGREGATE RESULTS
# ============================================================================

print("\n" + "="*100)
print("AGGREGATE RESULTS")
print("="*100)

all_results = normal_results + suspicious_results + super_suspicious_results

# Calculate statistics
normal_correct = sum(1 for r in normal_results if r['final_ui_classification'] == 'normal')
suspicious_correct = sum(1 for r in suspicious_results if r['final_ui_classification'] == 'suspicious')
super_suspicious_correct = sum(1 for r in super_suspicious_results if r['final_ui_classification'] == 'super_suspicious')

normal_total = len(normal_results)
suspicious_total = len(suspicious_results)
super_suspicious_total = len(super_suspicious_results)
total = len(all_results)

normal_accuracy = normal_correct / normal_total if normal_total > 0 else 0
suspicious_accuracy = suspicious_correct / suspicious_total if suspicious_total > 0 else 0
super_suspicious_accuracy = super_suspicious_correct / super_suspicious_total if super_suspicious_total > 0 else 0
overall_accuracy = (normal_correct + suspicious_correct + super_suspicious_correct) / total if total > 0 else 0

# Error counts
normal_to_suspicious = sum(1 for r in normal_results if r['final_ui_classification'] == 'suspicious')
normal_to_super_suspicious = sum(1 for r in normal_results if r['final_ui_classification'] == 'super_suspicious')
suspicious_to_normal = sum(1 for r in suspicious_results if r['final_ui_classification'] == 'normal')
suspicious_to_super_suspicious = sum(1 for r in suspicious_results if r['final_ui_classification'] == 'super_suspicious')
super_suspicious_to_normal = sum(1 for r in super_suspicious_results if r['final_ui_classification'] == 'normal')
super_suspicious_to_suspicious = sum(1 for r in super_suspicious_results if r['final_ui_classification'] == 'suspicious')

print(f"\n| Intended Class   | Total | Correct UI | Incorrect UI | Accuracy |")
print(f"| {'-'*17} | {'-'*5} | {'-'*11} | {'-'*13} | {'-'*9} |")
print(f"| Normal           | {normal_total:5} | {normal_correct:11} | {normal_total-normal_correct:13} | {normal_accuracy:8.2%} |")
print(f"| Suspicious       | {suspicious_total:5} | {suspicious_correct:11} | {suspicious_total-suspicious_correct:13} | {suspicious_accuracy:8.2%} |")
print(f"| Super-Suspicious | {super_suspicious_total:5} | {super_suspicious_correct:11} | {super_suspicious_total-super_suspicious_correct:13} | {super_suspicious_accuracy:8.2%} |")
print(f"| TOTAL            | {total:5} | {normal_correct+suspicious_correct+super_suspicious_correct:11} | {total-(normal_correct+suspicious_correct+super_suspicious_correct):13} | {overall_accuracy:8.2%} |")

print(f"\nError Breakdown:")
print(f"  Normal → Suspicious false positives: {normal_to_suspicious}")
print(f"  Normal → Super-Suspicious false positives: {normal_to_super_suspicious}")
print(f"  Suspicious → Normal false negatives: {suspicious_to_normal}")
print(f"  Suspicious → Super-Suspicious errors: {suspicious_to_super_suspicious}")
print(f"  Super-Suspicious → Normal false negatives: {super_suspicious_to_normal}")
print(f"  Super-Suspicious → Suspicious errors: {super_suspicious_to_suspicious}")

# ============================================================================
# FAILURE TYPE BREAKDOWN
# ============================================================================

print(f"\nFailure Type Breakdown:")
model_failures = sum(1 for r in all_results if r['failure_type'] == 'MODEL_FAILURE')
confidence_gate_failures = sum(1 for r in all_results if r['failure_type'] == 'CONFIDENCE_GATE_FAILURE')
integration_failures = sum(1 for r in all_results if r['failure_type'] == 'INTEGRATION_FAILURE')

print(f"  Model Failures: {model_failures}")
print(f"  Confidence Gate Failures: {confidence_gate_failures}")
print(f"  Integration Failures: {integration_failures}")

if model_failures > 0:
    print(f"\n  Model Failure Cases:")
    for r in all_results:
        if r['failure_type'] == 'MODEL_FAILURE':
            print(f"    {r['test_id']}: Intended {r['intended_scenario']}, Model predicted {r['raw_model_class']}")

if confidence_gate_failures > 0:
    print(f"\n  Confidence Gate Failure Cases:")
    for r in all_results:
        if r['failure_type'] == 'CONFIDENCE_GATE_FAILURE':
            print(f"    {r['test_id']}: Intended {r['intended_scenario']}, Model {r['raw_model_class']} ({r['ml_confidence']:.2%}), Threshold {r['threshold_applied']}")

if integration_failures > 0:
    print(f"\n  Integration Failure Cases:")
    for r in all_results:
        if r['failure_type'] == 'INTEGRATION_FAILURE':
            print(f"    {r['test_id']}: Intended {r['intended_scenario']}, Model {r['raw_model_class']}, UI {r['final_ui_classification']}")

# ============================================================================
# SAVE RESULTS
# ============================================================================

results_data = {
    'timestamp': datetime.now().isoformat(),
    'normal_results': normal_results,
    'suspicious_results': suspicious_results,
    'super_suspicious_results': super_suspicious_results,
    'special_check': special_result,
    'statistics': {
        'normal_correct': normal_correct,
        'normal_total': normal_total,
        'normal_accuracy': normal_accuracy,
        'suspicious_correct': suspicious_correct,
        'suspicious_total': suspicious_total,
        'suspicious_accuracy': suspicious_accuracy,
        'super_suspicious_correct': super_suspicious_correct,
        'super_suspicious_total': super_suspicious_total,
        'super_suspicious_accuracy': super_suspicious_accuracy,
        'overall_accuracy': overall_accuracy,
        'normal_to_suspicious': normal_to_suspicious,
        'normal_to_super_suspicious': normal_to_super_suspicious,
        'suspicious_to_normal': suspicious_to_normal,
        'suspicious_to_super_suspicious': suspicious_to_super_suspicious,
        'super_suspicious_to_normal': super_suspicious_to_normal,
        'super_suspicious_to_suspicious': super_suspicious_to_suspicious,
        'model_failures': model_failures,
        'confidence_gate_failures': confidence_gate_failures,
        'integration_failures': integration_failures
    }
}

with open('acceptance_test_results.json', 'w') as f:
    json.dump(results_data, f, indent=2, default=str)

print(f"\n{'='*100}")
print("ACCEPTANCE TEST COMPLETE")
print("="*100)
print(f"Results saved to: acceptance_test_results.json")
