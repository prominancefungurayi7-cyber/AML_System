"""
STAGE 15G: MODEL VALIDATION

Train models using 57 features and compare with Stage 12 baseline (34 features).
"""

import csv
import json
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
from sklearn.preprocessing import LabelEncoder
import random

print("=" * 80)
print("STAGE 15G: MODEL VALIDATION")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================================
# LOAD STAGE 15 FEATURES
# ============================================================================

print("Loading Stage 15 features...")
features = []
with open('ml_stage15_features.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        features.append(row)

print(f"Loaded {len(features)} transactions")
print()

# ============================================================================
# LOAD STAGE 11 GROUND TRUTH
# ============================================================================

print("Loading Stage 11 ground truth...")
with open('ml_stage11_ground_truth.json', 'r') as f:
    ground_truth = json.load(f)

print(f"Loaded ground truth for {len(ground_truth)} transactions")
print()

# ============================================================================
# LOAD STAGE 12 PRIMARY SPLIT
# ============================================================================

print("Loading Stage 12 primary split...")
with open('ml_stage12_primary_split.json', 'r') as f:
    primary_split = json.load(f)

train_customers = set(primary_split['train_customer_ids'])
test_customers = set(primary_split['test_customer_ids'])

print(f"Train customers: {len(train_customers)}")
print(f"Test customers: {len(test_customers)}")
print()

# ============================================================================
# LOAD FEATURE METADATA
# ============================================================================

with open('ml_stage15_feature_metadata.json', 'r') as f:
    metadata = json.load(f)

feature_names = metadata['feature_names']

# ============================================================================
# MERGE FEATURES WITH GROUND TRUTH
# ============================================================================

print("Merging features with ground truth...")

gt_map = {str(gt['transaction_id']): gt for gt in ground_truth}

merged_data = []
for feature in features:
    tx_id = str(feature['transaction_id'])
    if tx_id in gt_map:
        merged = {**feature, **gt_map[tx_id]}
        merged_data.append(merged)

print(f"Merged {len(merged_data)} transactions")
print()

# ============================================================================
# SPLIT BY CUSTOMER
# ============================================================================

print("Splitting by customer...")

train_data = []
test_data = []

for data in merged_data:
    customer = data['sender_account']
    if customer in train_customers:
        train_data.append(data)
    elif customer in test_customers:
        test_data.append(data)

print(f"Train transactions: {len(train_data)}")
print(f"Test transactions: {len(test_data)}")
print()

# ============================================================================
# PREPARE FEATURES AND LABELS
# ============================================================================

print("Preparing features and labels...")

# Extract features
X_train = np.array([[float(f[name]) for name in feature_names] for f in train_data])
X_test = np.array([[float(f[name]) for name in feature_names] for f in test_data])

# Extract labels
y_train = [f['ground_truth_label'] for f in train_data]
y_test = [f['ground_truth_label'] for f in test_data]

# Encode labels
label_encoder = LabelEncoder()
label_encoder.fit(y_train + y_test)
y_train_encoded = label_encoder.transform(y_train)
y_test_encoded = label_encoder.transform(y_test)

print(f"Feature matrix shape: {X_train.shape}")
print(f"Label classes: {label_encoder.classes_}")
print()

# ============================================================================
# TRAIN RANDOM FOREST
# ============================================================================

print("Training Random Forest...")

rf = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    n_jobs=-1
)

rf.fit(X_train, y_train_encoded)

rf_train_pred = rf.predict(X_train)
rf_test_pred = rf.predict(X_test)

print("Random Forest training complete")
print()

# ============================================================================
# TRAIN GRADIENT BOOSTING
# ============================================================================

print("Training Gradient Boosting...")

gb = GradientBoostingClassifier(
    n_estimators=100,
    max_depth=5,
    learning_rate=0.1,
    random_state=42
)

gb.fit(X_train, y_train_encoded)

gb_train_pred = gb.predict(X_train)
gb_test_pred = gb.predict(X_test)

print("Gradient Boosting training complete")
print()

# ============================================================================
# COMPUTE METRICS
# ============================================================================

print("Computing metrics...")

def compute_metrics(y_true, y_pred, label_encoder):
    """Compute classification metrics."""
    accuracy = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average='macro')
    weighted_f1 = f1_score(y_true, y_pred, average='weighted')
    
    # Per-class metrics
    report = classification_report(y_true, y_pred, target_names=label_encoder.classes_, output_dict=True)
    
    per_class = {}
    for class_name in label_encoder.classes_:
        if class_name in report:
            per_class[class_name] = {
                'precision': report[class_name]['precision'],
                'recall': report[class_name]['recall'],
                'f1': report[class_name]['f1-score']
            }
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    
    # Suspicious recall
    suspicious_idx = label_encoder.transform(['suspicious'])[0] if 'suspicious' in label_encoder.classes_ else None
    super_suspicious_idx = label_encoder.transform(['super-suspicious'])[0] if 'super-suspicious' in label_encoder.classes_ else None
    
    suspicious_recall = per_class.get('suspicious', {}).get('recall', 0.0)
    super_suspicious_recall = per_class.get('super-suspicious', {}).get('recall', 0.0)
    
    return {
        'accuracy': accuracy,
        'macro_f1': macro_f1,
        'weighted_f1': weighted_f1,
        'per_class': per_class,
        'confusion_matrix': cm.tolist(),
        'suspicious_recall': suspicious_recall,
        'super_suspicious_recall': super_suspicious_recall
    }

rf_train_metrics = compute_metrics(y_train_encoded, rf_train_pred, label_encoder)
rf_test_metrics = compute_metrics(y_test_encoded, rf_test_pred, label_encoder)

gb_train_metrics = compute_metrics(y_train_encoded, gb_train_pred, label_encoder)
gb_test_metrics = compute_metrics(y_test_encoded, gb_test_pred, label_encoder)

print("Metrics computed")
print()

# ============================================================================
# LOAD STAGE 12 BASELINE RESULTS
# ============================================================================

print("Loading Stage 12 baseline results...")
with open('ml_stage12_model_results.json', 'r') as f:
    stage12_results = json.load(f)

print("Stage 12 baseline results loaded")
print()

# ============================================================================
# PRINT RESULTS
# ============================================================================

print("MODEL VALIDATION RESULTS:")
print("-" * 80)

print("Random Forest:")
print(f"  Train Accuracy: {rf_train_metrics['accuracy']:.4f}")
print(f"  Test Accuracy: {rf_test_metrics['accuracy']:.4f}")
print(f"  Train Macro F1: {rf_train_metrics['macro_f1']:.4f}")
print(f"  Test Macro F1: {rf_test_metrics['macro_f1']:.4f}")
print(f"  Train/Test Gap: {rf_train_metrics['macro_f1'] - rf_test_metrics['macro_f1']:.4f}")
print(f"  Suspicious Recall: {rf_test_metrics['suspicious_recall']:.4f}")
print(f"  Super-Suspicious Recall: {rf_test_metrics['super_suspicious_recall']:.4f}")
print()

print("Gradient Boosting:")
print(f"  Train Accuracy: {gb_train_metrics['accuracy']:.4f}")
print(f"  Test Accuracy: {gb_test_metrics['accuracy']:.4f}")
print(f"  Train Macro F1: {gb_train_metrics['macro_f1']:.4f}")
print(f"  Test Macro F1: {gb_test_metrics['macro_f1']:.4f}")
print(f"  Train/Test Gap: {gb_train_metrics['macro_f1'] - gb_test_metrics['macro_f1']:.4f}")
print(f"  Suspicious Recall: {gb_test_metrics['suspicious_recall']:.4f}")
print(f"  Super-Suspicious Recall: {gb_test_metrics['super_suspicious_recall']:.4f}")
print()

print("COMPARISON WITH STAGE 12 BASELINE:")
print("-" * 80)

print("Random Forest:")
rf_baseline = stage12_results['primary_split']['results'].get('random_forest', {})
rf_baseline_macro_f1 = rf_baseline.get('macro_f1', 0.0)
print(f"  Stage 12 Test Macro F1: {rf_baseline_macro_f1:.4f}")
print(f"  Stage 15 Test Macro F1: {rf_test_metrics['macro_f1']:.4f}")
print(f"  Improvement: {rf_test_metrics['macro_f1'] - rf_baseline_macro_f1:.4f}")
print()

print("Gradient Boosting:")
gb_baseline = stage12_results['primary_split']['results'].get('gradient_boosting', {})
gb_baseline_macro_f1 = gb_baseline.get('macro_f1', 0.0)
print(f"  Stage 12 Test Macro F1: {gb_baseline_macro_f1:.4f}")
print(f"  Stage 15 Test Macro F1: {gb_test_metrics['macro_f1']:.4f}")
print(f"  Improvement: {gb_test_metrics['macro_f1'] - gb_baseline_macro_f1:.4f}")
print()

# ============================================================================
# SAVE RESULTS
# ============================================================================

results = {
    "timestamp": datetime.now().isoformat(),
    "total_features": len(feature_names),
    "train_transactions": len(train_data),
    "test_transactions": len(test_data),
    "train_customers": len(train_customers),
    "test_customers": len(test_customers),
    "random_forest": {
        "train_metrics": rf_train_metrics,
        "test_metrics": rf_test_metrics,
        "feature_importance": rf.feature_importances_.tolist()
    },
    "gradient_boosting": {
        "train_metrics": gb_train_metrics,
        "test_metrics": gb_test_metrics,
        "feature_importance": gb.feature_importances_.tolist()
    },
    "stage12_baseline": {
        "random_forest_test_macro_f1": rf_baseline_macro_f1,
        "gradient_boosting_test_macro_f1": gb_baseline_macro_f1
    },
    "improvement": {
        "random_forest": rf_test_metrics['macro_f1'] - rf_baseline_macro_f1,
        "gradient_boosting": gb_test_metrics['macro_f1'] - gb_baseline_macro_f1
    }
}

with open('ml_stage15_model_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("=" * 80)
print("MODEL VALIDATION COMPLETE")
print("=" * 80)
print("Results saved to ml_stage15_model_results.json")
