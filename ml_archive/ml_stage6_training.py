"""
STAGE 6: Model Training and Evaluation

Implements chronological train/test split, cross-validation on training set,
and rigorous evaluation of multiple model candidates.
"""

import csv
import json
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)
import joblib

print("=" * 80)
print("STAGE 6: MODEL TRAINING AND EVALUATION")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================================
# LOAD DATA
# ============================================================================

print("Loading data...")
with open("ml_stage5_features.csv", 'r') as f:
    reader = csv.DictReader(f)
    features = list(reader)

with open("ml_stage3_ground_truth.json", 'r') as f:
    ground_truth = json.load(f)

with open("ml_stage3_dataset.csv", 'r') as f:
    reader = csv.DictReader(f)
    stage3_dataset = list(reader)

print(f"Loaded {len(features)} feature rows")
print(f"Loaded {len(ground_truth)} labels")
print(f"Loaded {len(stage3_dataset)} transactions from Stage 3")
print()

# ============================================================================
# ALIGN FEATURES WITH LABELS AND TIMESTAMPS
# ============================================================================

print("Aligning features with labels and timestamps...")
print("-" * 80)

# Stage 5 features are in the same order as Stage 3 dataset
# Align by position (both have 10,000 rows in same order)
combined_data = []
for i, feature_row in enumerate(features):
    label_entry = ground_truth[i]
    stage3_row = stage3_dataset[i]
    
    combined_data.append({
        "transaction_id": label_entry["transaction_id"],
        "timestamp": stage3_row["timestamp"],
        "label": label_entry["ground_truth_label"],
        **{k: float(v) for k, v in feature_row.items()}
    })

print(f"Aligned {len(combined_data)} transactions with labels and timestamps")
print()

# ============================================================================
# SORT CHRONOLOGICALLY
# ============================================================================

print("Sorting transactions chronologically...")
print("-" * 80)

combined_data.sort(key=lambda x: datetime.fromisoformat(x["timestamp"]))
print(f"Transactions sorted chronologically")
print()

# ============================================================================
# CHRONOLOGICAL TRAIN/TEST SPLIT
# ============================================================================

print("Performing chronological train/test split...")
print("-" * 80)

# Use 80% for training, 20% for testing (by date)
split_idx = int(len(combined_data) * 0.8)
train_data = combined_data[:split_idx]
test_data = combined_data[split_idx:]

train_start = datetime.fromisoformat(train_data[0]["timestamp"])
train_end = datetime.fromisoformat(train_data[-1]["timestamp"])
test_start = datetime.fromisoformat(test_data[0]["timestamp"])
test_end = datetime.fromisoformat(test_data[-1]["timestamp"])

print(f"Training set: {len(train_data)} transactions")
print(f"  Date range: {train_start.date()} to {train_end.date()}")
print(f"Test set: {len(test_data)} transactions")
print(f"  Date range: {test_start.date()} to {test_end.date()}")
print()

# Check for customer overlap
train_customers = set()
for tx in stage3_dataset:
    tx_id = int(tx["transaction_id"])
    if tx_id <= split_idx:
        train_customers.add(tx["sender_account"])

test_customers = set()
for tx in stage3_dataset:
    tx_id = int(tx["transaction_id"])
    if tx_id > split_idx:
        test_customers.add(tx["sender_account"])

customer_overlap = train_customers & test_customers
print(f"Customer overlap analysis:")
print(f"  Unique customers in train: {len(train_customers)}")
print(f"  Unique customers in test: {len(test_customers)}")
print(f"  Customers in both train and test: {len(customer_overlap)}")
print()

# ============================================================================
# EXTRACT FEATURES AND LABELS
# ============================================================================

print("Extracting features and labels...")
print("-" * 80)

FEATURE_NAMES = [
    "amount", "sender_avg_amount", "sender_max_amount", "sender_tx_count",
    "amount_to_sender_avg", "amount_to_sender_max", "sender_tx_count_24h",
    "sender_volume_24h", "amount_to_sender_volume_24h", "is_new_recipient",
    "same_day_count", "same_day_total", "same_recipient_count", "rapid_transfer_count",
    "hour", "is_deposit", "is_withdraw", "is_transfer", "is_self_transfer",
    "is_off_hours", "channel_encoded", "amount_std_dev", "amount_z_score",
    "tx_frequency_7d", "tx_frequency_30d", "day_of_week", "is_weekend",
    "time_since_last_tx", "unique_recipients_24h", "unique_recipients_7d",
    "recipient_concentration", "new_recipient_ratio_7d",
    "amount_change_vs_avg_7d", "frequency_change_vs_avg_7d"
]

X_train = np.array([[tx[feat] for feat in FEATURE_NAMES] for tx in train_data])
y_train = np.array([tx["label"] for tx in train_data])

X_test = np.array([[tx[feat] for feat in FEATURE_NAMES] for tx in test_data])
y_test = np.array([tx["label"] for tx in test_data])

print(f"X_train shape: {X_train.shape}")
print(f"y_train shape: {y_train.shape}")
print(f"X_test shape: {X_test.shape}")
print(f"y_test shape: {y_test.shape}")
print()

# ============================================================================
# CLASS DISTRIBUTION IN TRAIN/TEST
# ============================================================================

print("Class distribution:")
print("-" * 80)

def print_distribution(y, name):
    unique, counts = np.unique(y, return_counts=True)
    total = len(y)
    for label, count in zip(unique, counts):
        pct = (count / total) * 100
        print(f"  {name} {label}: {count} ({pct:.1f}%)")

print_distribution(y_train, "Train")
print_distribution(y_test, "Test")
print()

# ============================================================================
# PREPROCESSING (FIT ON TRAIN ONLY)
# ============================================================================

print("Preprocessing...")
print("-" * 80)

# Scale features (fit on train only)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("Features scaled using StandardScaler (fit on train only)")
print()

# ============================================================================
# BASELINE MODELS
# ============================================================================

print("=" * 80)
print("BASELINE MODELS")
print("=" * 80)
print()

# Baseline 1: Majority class
print("Baseline 1: Majority Class")
print("-" * 80)
majority_class = max(set(y_train), key=list(y_train).count)
y_pred_majority = np.array([majority_class] * len(y_test))
majority_acc = accuracy_score(y_test, y_pred_majority)
majority_f1_macro = f1_score(y_test, y_pred_majority, average='macro')
print(f"  Accuracy: {majority_acc:.4f}")
print(f"  Macro F1: {majority_f1_macro:.4f}")
print()

# Baseline 2: Logistic Regression
print("Baseline 2: Logistic Regression")
print("-" * 80)
log_reg = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
log_reg.fit(X_train_scaled, y_train)
y_pred_logreg = log_reg.predict(X_test_scaled)
logreg_acc = accuracy_score(y_test, y_pred_logreg)
logreg_f1_macro = f1_score(y_test, y_pred_logreg, average='macro')
logreg_f1_weighted = f1_score(y_test, y_pred_logreg, average='weighted')
print(f"  Accuracy: {logreg_acc:.4f}")
print(f"  Macro F1: {logreg_f1_macro:.4f}")
print(f"  Weighted F1: {logreg_f1_weighted:.4f}")
print()

# ============================================================================
# TREE-BASED MODELS
# ============================================================================

print("=" * 80)
print("TREE-BASED MODELS")
print("=" * 80)
print()

# Model 1: Random Forest
print("Model 1: Random Forest")
print("-" * 80)
rf = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    min_samples_leaf=3,
    min_samples_split=2,
    max_features='sqrt',
    class_weight='balanced_subsample',
    random_state=42
)

# Cross-validation on training set
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(rf, X_train_scaled, y_train, cv=cv, scoring='f1_macro')
print(f"  Cross-validation Macro F1: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

# Fit on full training set
rf.fit(X_train_scaled, y_train)

# Evaluate on test set
y_pred_rf = rf.predict(X_test_scaled)
rf_acc = accuracy_score(y_test, y_pred_rf)
rf_f1_macro = f1_score(y_test, y_pred_rf, average='macro')
rf_f1_weighted = f1_score(y_test, y_pred_rf, average='weighted')
print(f"  Test Accuracy: {rf_acc:.4f}")
print(f"  Test Macro F1: {rf_f1_macro:.4f}")
print(f"  Test Weighted F1: {rf_f1_weighted:.4f}")
print()

# Model 2: Gradient Boosting
print("Model 2: Gradient Boosting")
print("-" * 80)
gb = GradientBoostingClassifier(
    n_estimators=100,
    max_depth=5,
    learning_rate=0.1,
    random_state=42
)

# Cross-validation on training set
cv_scores_gb = cross_val_score(gb, X_train_scaled, y_train, cv=cv, scoring='f1_macro')
print(f"  Cross-validation Macro F1: {cv_scores_gb.mean():.4f} (+/- {cv_scores_gb.std():.4f})")

# Fit on full training set
gb.fit(X_train_scaled, y_train)

# Evaluate on test set
y_pred_gb = gb.predict(X_test_scaled)
gb_acc = accuracy_score(y_test, y_pred_gb)
gb_f1_macro = f1_score(y_test, y_pred_gb, average='macro')
gb_f1_weighted = f1_score(y_test, y_pred_gb, average='weighted')
print(f"  Test Accuracy: {gb_acc:.4f}")
print(f"  Test Macro F1: {gb_f1_macro:.4f}")
print(f"  Test Weighted F1: {gb_f1_weighted:.4f}")
print()

# ============================================================================
# DETAILED EVALUATION FOR BEST MODEL (Random Forest)
# ============================================================================

print("=" * 80)
print("DETAILED EVALUATION: RANDOM FOREST")
print("=" * 80)
print()

print("Classification Report:")
print(classification_report(y_test, y_pred_rf))
print()

print("Confusion Matrix:")
cm = confusion_matrix(y_test, y_pred_rf)
print(cm)
print()

# Per-class metrics
classes = ['normal', 'suspicious', 'super_suspicious']
print("Per-class metrics:")
print("-" * 80)
for i, class_name in enumerate(classes):
    precision = precision_score(y_test, y_pred_rf, labels=[class_name], average='micro')
    recall = recall_score(y_test, y_pred_rf, labels=[class_name], average='micro')
    f1 = f1_score(y_test, y_pred_rf, labels=[class_name], average='micro')
    support = np.sum(y_test == class_name)
    print(f"  {class_name}:")
    print(f"    Precision: {precision:.4f}")
    print(f"    Recall: {recall:.4f}")
    print(f"    F1: {f1:.4f}")
    print(f"    Support: {support}")
print()

# ============================================================================
# FEATURE IMPORTANCE
# ============================================================================

print("=" * 80)
print("FEATURE IMPORTANCE (Random Forest)")
print("=" * 80)
print()

importances = rf.feature_importances_
indices = np.argsort(importances)[::-1]

print("Feature ranking:")
for i, idx in enumerate(indices):
    print(f"  {i+1:2d}. {FEATURE_NAMES[idx]:30s} {importances[idx]:.4f}")
print()

# ============================================================================
# SAVE RESULTS
# ============================================================================

print("Saving results...")
results = {
    "timestamp": datetime.now().isoformat(),
    "train_samples": len(X_train),
    "test_samples": len(X_test),
    "train_date_range": {"start": str(train_start.date()), "end": str(train_end.date())},
    "test_date_range": {"start": str(test_start.date()), "end": str(test_end.date())},
    "customer_overlap": len(customer_overlap),
    "baseline_majority": {"accuracy": float(majority_acc), "macro_f1": float(majority_f1_macro)},
    "baseline_logreg": {"accuracy": float(logreg_acc), "macro_f1": float(logreg_f1_macro), "weighted_f1": float(logreg_f1_weighted)},
    "random_forest": {
        "cv_macro_f1_mean": float(cv_scores.mean()),
        "cv_macro_f1_std": float(cv_scores.std()),
        "test_accuracy": float(rf_acc),
        "test_macro_f1": float(rf_f1_macro),
        "test_weighted_f1": float(rf_f1_weighted)
    },
    "gradient_boosting": {
        "cv_macro_f1_mean": float(cv_scores_gb.mean()),
        "cv_macro_f1_std": float(cv_scores_gb.std()),
        "test_accuracy": float(gb_acc),
        "test_macro_f1": float(gb_f1_macro),
        "test_weighted_f1": float(gb_f1_weighted)
    },
    "feature_importance": {FEATURE_NAMES[i]: float(importances[i]) for i in range(len(FEATURE_NAMES))}
}

with open("ml_stage6_results.json", 'w') as f:
    json.dump(results, f, indent=2)

print("Results saved to ml_stage6_results.json")

# Save the best model
joblib.dump(rf, "ml_stage6_rf_model.pkl")
joblib.dump(scaler, "ml_stage6_scaler.pkl")
print("Model and scaler saved")
print()

print("=" * 80)
print("TRAINING AND EVALUATION COMPLETE")
print("=" * 80)
