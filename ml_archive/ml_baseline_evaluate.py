"""
Baseline evaluation of existing AML AI model.
This script evaluates the existing model using two methodologies:
A. Existing reported-style evaluation (reproduce current methodology)
B. More honest diagnostic evaluation (proper train/test split)
"""

import sys
import os
import json
import random
import numpy as np
from datetime import datetime, timezone
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, precision_recall_fscore_support
)
import joblib

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_core import transaction_features, map_risk_to_ai_label, LABELS

print("=" * 80)
print("STAGE 2: BASELINE MODEL EVALUATION")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# Load dataset
print("Loading dataset...")
with open("ml_baseline_dataset.json", 'r') as f:
    transactions = json.load(f)
print(f"Loaded {len(transactions)} transactions")
print()

# Load model
print("Loading model...")
MODEL_PATH = "aml_ai_model.pkl"
bundle = joblib.load(MODEL_PATH)
classifier = bundle["classifier"]
anomaly_detector = bundle["anomaly_detector"]
print(f"Model loaded: {bundle.get('version', 'unknown')}")
print()

# ============================================================================
# EVALUATION A: Existing Reported-Style Evaluation
# ============================================================================
print("=" * 80)
print("EVALUATION A: EXISTING REPORTED-STYLE METHODOLOGY")
print("=" * 80)
print("This reproduces the existing training methodology:")
print("- No train/test split (evaluate on same data used for training)")
print("- Labels derived from rule engine via map_risk_to_ai_label()")
print()

# Prepare data using existing methodology
X = np.array([transaction_features(tx) for tx in transactions])
y_true = [map_risk_to_ai_label(tx.get("risk_level", "normal"), tx.get("risk_score", 0)) for tx in transactions]

print(f"Feature matrix shape: {X.shape}")
print(f"Label distribution:")
for label in LABELS:
    count = y_true.count(label)
    pct = count / len(y_true) * 100
    print(f"  {label:20s}: {count:5d} ({pct:5.1f}%)")
print()

# Predict using classifier
y_pred = classifier.predict(X)
y_pred_proba = classifier.predict_proba(X)

# Calculate metrics
accuracy = accuracy_score(y_true, y_pred)
precision = precision_score(y_true, y_pred, average='weighted')
recall = recall_score(y_true, y_pred, average='weighted')
f1 = f1_score(y_true, y_pred, average='weighted')
macro_f1 = f1_score(y_true, y_pred, average='macro')

print("Classification Metrics (Existing Methodology):")
print(f"  Accuracy:           {accuracy:.4f}")
print(f"  Precision (weighted): {precision:.4f}")
print(f"  Recall (weighted):    {recall:.4f}")
print(f"  F1-score (weighted):  {f1:.4f}")
print(f"  F1-score (macro):     {macro_f1:.4f}")
print()

# Per-class metrics
print("Per-Class Metrics:")
precision_per, recall_per, f1_per, support = precision_recall_fscore_support(y_true, y_pred, labels=LABELS)
for i, label in enumerate(LABELS):
    print(f"  {label}:")
    print(f"    Precision: {precision_per[i]:.4f}")
    print(f"    Recall:    {recall_per[i]:.4f}")
    print(f"    F1-score:  {f1_per[i]:.4f}")
    print(f"    Support:   {support[i]}")
print()

# Confusion matrix
cm = confusion_matrix(y_true, y_pred, labels=LABELS)
print("Confusion Matrix:")
print("                Predicted")
print("Actual          Normal  Suspicious  SuperSuspicious")
for i, label in enumerate(LABELS):
    print(f"{label:15s}  {cm[i,0]:6d}  {cm[i,1]:10d}  {cm[i,2]:14d}")
print()

# Calculate false positives and false negatives
fp = cm.sum(axis=0) - np.diag(cm)
fn = cm.sum(axis=1) - np.diag(cm)
print("False Positives (by class):")
for i, label in enumerate(LABELS):
    print(f"  {label:20s}: {fp[i]}")
print("False Negatives (by class):")
for i, label in enumerate(LABELS):
    print(f"  {label:20s}: {fn[i]}")
print()

# AML-specific metrics
suspicious_idx = LABELS.index("suspicious")
super_suspicious_idx = LABELS.index("super_suspicious")
suspicious_recall = recall_per[suspicious_idx]
super_suspicious_recall = recall_per[super_suspicious_idx]
print("AML-Specific Metrics:")
print(f"  Suspicious Recall:        {suspicious_recall:.4f}")
print(f"  Super-Suspicious Recall:  {super_suspicious_recall:.4f}")
print()

# ============================================================================
# EVALUATION B: More Honest Diagnostic Evaluation
# ============================================================================
print("=" * 80)
print("EVALUATION B: MORE HONEST DIAGNOSTIC METHODOLOGY")
print("=" * 80)
print("This uses proper train/test split:")
print("- 70% train, 30% test split")
print("- Random split (not customer-level due to current data structure)")
print("- Labels still derived from rule engine (limitation acknowledged)")
print()

# Set random seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# Shuffle data
indices = list(range(len(transactions)))
random.shuffle(indices)

# Split 70/30
split_idx = int(len(indices) * 0.70)
train_indices = indices[:split_idx]
test_indices = indices[split_idx:]

X_train = X[train_indices]
y_train = [y_true[i] for i in train_indices]
X_test = X[test_indices]
y_test = [y_true[i] for i in test_indices]

print(f"Train set: {len(X_train)} samples")
print(f"Test set:  {len(X_test)} samples")
print()

print("Train label distribution:")
for label in LABELS:
    count = y_train.count(label)
    pct = count / len(y_train) * 100
    print(f"  {label:20s}: {count:5d} ({pct:5.1f}%)")
print()

print("Test label distribution:")
for label in LABELS:
    count = y_test.count(label)
    pct = count / len(y_test) * 100
    print(f"  {label:20s}: {count:5d} ({pct:5.1f}%)")
print()

# Predict on test set using existing model (no retraining)
y_test_pred = classifier.predict(X_test)
y_test_pred_proba = classifier.predict_proba(X_test)

# Calculate metrics
test_accuracy = accuracy_score(y_test, y_test_pred)
test_precision = precision_score(y_test, y_test_pred, average='weighted')
test_recall = recall_score(y_test, y_test_pred, average='weighted')
test_f1 = f1_score(y_test, y_test_pred, average='weighted')
test_macro_f1 = f1_score(y_test, y_test_pred, average='macro')

print("Test Set Classification Metrics (Honest Evaluation):")
print(f"  Accuracy:           {test_accuracy:.4f}")
print(f"  Precision (weighted): {test_precision:.4f}")
print(f"  Recall (weighted):    {test_recall:.4f}")
print(f"  F1-score (weighted):  {test_f1:.4f}")
print(f"  F1-score (macro):     {test_macro_f1:.4f}")
print()

# Per-class metrics on test set
print("Test Set Per-Class Metrics:")
test_precision_per, test_recall_per, test_f1_per, test_support = precision_recall_fscore_support(y_test, y_test_pred, labels=LABELS)
for i, label in enumerate(LABELS):
    print(f"  {label}:")
    print(f"    Precision: {test_precision_per[i]:.4f}")
    print(f"    Recall:    {test_recall_per[i]:.4f}")
    print(f"    F1-score:  {test_f1_per[i]:.4f}")
    print(f"    Support:   {test_support[i]}")
print()

# Test set confusion matrix
test_cm = confusion_matrix(y_test, y_test_pred, labels=LABELS)
print("Test Set Confusion Matrix:")
print("                Predicted")
print("Actual          Normal  Suspicious  SuperSuspicious")
for i, label in enumerate(LABELS):
    print(f"{label:15s}  {test_cm[i,0]:6d}  {test_cm[i,1]:10d}  {test_cm[i,2]:14d}")
print()

# Test set false positives and false negatives
test_fp = test_cm.sum(axis=0) - np.diag(test_cm)
test_fn = test_cm.sum(axis=1) - np.diag(test_cm)
print("Test Set False Positives (by class):")
for i, label in enumerate(LABELS):
    print(f"  {label:20s}: {test_fp[i]}")
print("Test Set False Negatives (by class):")
for i, label in enumerate(LABELS):
    print(f"  {label:20s}: {test_fn[i]}")
print()

# AML-specific metrics on test set
test_suspicious_recall = test_recall_per[suspicious_idx]
test_super_suspicious_recall = test_recall_per[super_suspicious_idx]
print("Test Set AML-Specific Metrics:")
print(f"  Suspicious Recall:        {test_suspicious_recall:.4f}")
print(f"  Super-Suspicious Recall:  {test_super_suspicious_recall:.4f}")
print()

# ============================================================================
# FEATURE IMPORTANCE
# ============================================================================
print("=" * 80)
print("FEATURE IMPORTANCE")
print("=" * 80)

# Get feature names
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

# Get feature importance from RandomForest
rf_classifier = classifier.named_steps['classifier']
importances = rf_classifier.feature_importances_

# Sort by importance
indices = np.argsort(importances)[::-1]

print("Feature Importance (Random Forest):")
for i in range(len(importances)):
    idx = indices[i]
    print(f"  {i+1:2d}. {feature_names[idx]:30s} {importances[idx]:.4f}")
print()

# ============================================================================
# ANOMALY DETECTOR EVALUATION
# ============================================================================
print("=" * 80)
print("ANOMALY DETECTOR EVALUATION")
print("=" * 80)

# Get anomaly scores on test set
anomaly_scores = anomaly_detector.decision_function(X_test)

# Convert to binary predictions (anomaly if score < threshold)
threshold = np.percentile(anomaly_scores, 8)  # Using contamination=0.08
anomaly_pred = (anomaly_scores < threshold).astype(int)

# Since we don't have ground-truth anomaly labels, we can only report statistics
print("Anomaly Detector Statistics:")
print(f"  Mean anomaly score: {np.mean(anomaly_scores):.4f}")
print(f"  Std anomaly score: {np.std(anomaly_scores):.4f}")
print(f"  Min anomaly score: {np.min(anomaly_scores):.4f}")
print(f"  Max anomaly score: {np.max(anomaly_scores):.4f}")
print(f"  Threshold (8th percentile): {threshold:.4f}")
print(f"  Predicted anomalies: {np.sum(anomaly_pred)} ({np.sum(anomaly_pred)/len(anomaly_pred)*100:.1f}%)")
print()

# ============================================================================
# SAVE RESULTS
# ============================================================================
print("=" * 80)
print("SAVING RESULTS")
print("=" * 80)

results = {
    "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
    "dataset_size": len(transactions),
    "train_size": len(X_train),
    "test_size": len(X_test),
    "label_distribution": {label: y_true.count(label) for label in LABELS},
    
    "evaluation_a_existing_methodology": {
        "accuracy": float(accuracy),
        "precision_weighted": float(precision),
        "recall_weighted": float(recall),
        "f1_weighted": float(f1),
        "f1_macro": float(macro_f1),
        "per_class_precision": [float(p) for p in precision_per],
        "per_class_recall": [float(r) for r in recall_per],
        "per_class_f1": [float(f) for f in f1_per],
        "per_class_support": [int(s) for s in support],
        "confusion_matrix": cm.tolist(),
        "false_positives": [int(fp_val) for fp_val in fp],
        "false_negatives": [int(fn_val) for fn_val in fn],
        "suspicious_recall": float(suspicious_recall),
        "super_suspicious_recall": float(super_suspicious_recall),
    },
    
    "evaluation_b_honest_methodology": {
        "accuracy": float(test_accuracy),
        "precision_weighted": float(test_precision),
        "recall_weighted": float(test_recall),
        "f1_weighted": float(test_f1),
        "f1_macro": float(test_macro_f1),
        "per_class_precision": [float(p) for p in test_precision_per],
        "per_class_recall": [float(r) for r in test_recall_per],
        "per_class_f1": [float(f) for f in test_f1_per],
        "per_class_support": [int(s) for s in test_support],
        "confusion_matrix": test_cm.tolist(),
        "false_positives": [int(fp_val) for fp_val in test_fp],
        "false_negatives": [int(fn_val) for fn_val in test_fn],
        "suspicious_recall": float(test_suspicious_recall),
        "super_suspicious_recall": float(test_super_suspicious_recall),
    },
    
    "feature_importance": {
        feature_names[i]: float(importances[i]) for i in range(len(feature_names))
    },
    
    "anomaly_detector": {
        "mean_score": float(np.mean(anomaly_scores)),
        "std_score": float(np.std(anomaly_scores)),
        "min_score": float(np.min(anomaly_scores)),
        "max_score": float(np.max(anomaly_scores)),
        "threshold": float(threshold),
        "predicted_anomalies": int(np.sum(anomaly_pred)),
    },
    
    "limitations": [
        "Labels are derived from rule engine via map_risk_to_ai_label() - this is label leakage",
        "No customer-level splitting - same customer patterns may appear in train and test",
        "No temporal splitting - cannot assess generalization to future periods",
        "Synthetic data with artificial 70/20/10 distribution may not reflect reality",
        "Normal scenarios all small amounts - model may learn 'large = suspicious' artificially",
        "Anomaly detector cannot be properly evaluated without ground-truth anomaly labels"
    ]
}

with open("ml_baseline_results.json", 'w') as f:
    json.dump(results, f, indent=2)
print("Results saved to ml_baseline_results.json")
print()

print("=" * 80)
print("BASELINE EVALUATION COMPLETE")
print("=" * 80)
