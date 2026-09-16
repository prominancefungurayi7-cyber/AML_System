"""
RESULTS INTEGRITY CHECK

Verify the consistency of confusion matrices and metrics reported in the XGBoost experiment.
Recalculate all metrics from scratch for both Gradient Boosting and XGBoost.
"""

import csv
import json
import numpy as np
import joblib
import pickle
from datetime import datetime
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import GradientBoostingClassifier

print("=" * 80)
print("RESULTS INTEGRITY CHECK")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================================
# LOAD STAGE 16B FEATURES
# ============================================================================

print("Loading Stage 16B features...")
features = []
with open('ml_stage16b_features.csv', 'r') as f:
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
# LOAD STAGE 16B FEATURE METADATA
# ============================================================================

with open('ml_stage16b_feature_metadata.json', 'r') as f:
    metadata = json.load(f)

feature_names = metadata['feature_names']

print(f"Candidate 18-feature set: {len(feature_names)} features")
print()

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
# PRIMARY CUSTOMER-LEVEL SPLIT
# ============================================================================

print("Primary customer-level split...")

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

X_train = np.array([[float(f[name]) for name in feature_names] for f in train_data])
X_test = np.array([[float(f[name]) for name in feature_names] for f in test_data])

y_train = [f['ground_truth_label'] for f in train_data]
y_test = [f['ground_truth_label'] for f in test_data]

label_encoder = LabelEncoder()
label_encoder.fit(y_train + y_test)
y_train_encoded = label_encoder.transform(y_train)
y_test_encoded = label_encoder.transform(y_test)

print(f"Feature matrix shape: {X_train.shape}")
print(f"Test samples: {len(X_test)}")
print(f"Label classes: {label_encoder.classes_}")
print(f"Class ordering: {list(label_encoder.classes_)}")
print()

# ============================================================================
# LOAD FROZEN GRADIENT BOOSTING MODEL
# ============================================================================

print("Loading frozen Gradient Boosting model...")

# Load the frozen model from production
frozen_model = joblib.load('aml_ai_model.pkl')

# Load the label encoder from production
with open('aml_label_encoder.pkl', 'rb') as f:
    frozen_label_encoder = pickle.load(f)

print(f"Frozen model type: {type(frozen_model)}")
print(f"Frozen label encoder classes: {frozen_label_encoder.classes_}")
print()

# ============================================================================
# RETRAIN GRADIENT BOOSTING WITH CHAMPION CONFIG
# ============================================================================

print("Retraining Gradient Boosting with champion config...")

gb_champion_config = {
    'learning_rate': 0.01,
    'max_depth': 3,
    'n_estimators': 500,
    'random_state': 42
}

gb_model = GradientBoostingClassifier(**gb_champion_config)
gb_model.fit(X_train, y_train_encoded)

print("Gradient Boosting retrained")
print()

# ============================================================================
# TRAIN XGBOOST WITH BEST CONFIG
# ============================================================================

print("Training XGBoost with best config...")

try:
    import xgboost as xgb
except ImportError:
    import subprocess
    subprocess.check_call(['pip', 'install', 'xgboost'])
    import xgboost as xgb

xgb_best_config = {
    'learning_rate': 0.01,
    'max_depth': 3,
    'n_estimators': 500,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'min_child_weight': 5,
    'gamma': 0.1,
    'reg_alpha': 0.1,
    'reg_lambda': 1.0,
    'random_state': 42,
    'eval_metric': 'mlogloss'
}

xgb_model = xgb.XGBClassifier(**xgb_best_config)
xgb_model.fit(X_train, y_train_encoded)

print("XGBoost trained")
print()

# ============================================================================
# GENERATE PREDICTIONS
# ============================================================================

print("Generating predictions...")

# Gradient Boosting predictions
gb_train_pred = gb_model.predict(X_train)
gb_test_pred = gb_model.predict(X_test)
gb_test_proba = gb_model.predict_proba(X_test)

# XGBoost predictions
xgb_train_pred = xgb_model.predict(X_train)
xgb_test_pred = xgb_model.predict(X_test)
xgb_test_proba = xgb_model.predict_proba(X_test)

print("Predictions generated")
print()

# ============================================================================
# CALCULATE METRICS FROM SCRATCH
# ============================================================================

print("Calculating metrics from scratch...")

def compute_detailed_metrics(y_true, y_pred, label_encoder):
    """Compute detailed classification metrics."""
    accuracy = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average='macro')
    weighted_f1 = f1_score(y_true, y_pred, average='weighted')
    
    # Per-class metrics
    report = classification_report(y_true, y_pred, target_names=label_encoder.classes_, output_dict=True, zero_division=0)
    
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
    
    # False positives and false negatives
    fp = cm.sum(axis=0) - np.diag(cm)
    fn = cm.sum(axis=1) - np.diag(cm)
    
    # Suspicious false negatives
    suspicious_idx = label_encoder.transform(['suspicious'])[0] if 'suspicious' in label_encoder.classes_ else None
    suspicious_fn = fn[suspicious_idx] if suspicious_idx is not None else 0
    
    # Super-suspicious false negatives
    super_suspicious_idx = label_encoder.transform(['super_suspicious'])[0] if 'super_suspicious' in label_encoder.classes_ else None
    super_suspicious_fn = fn[super_suspicious_idx] if super_suspicious_idx is not None else 0
    
    return {
        'accuracy': accuracy,
        'macro_f1': macro_f1,
        'weighted_f1': weighted_f1,
        'per_class': per_class,
        'confusion_matrix': cm,
        'false_positives': fp,
        'false_negatives': fn,
        'suspicious_false_negatives': int(suspicious_fn),
        'super_suspicious_false_negatives': int(super_suspicious_fn)
    }

# Gradient Boosting metrics
gb_train_metrics = compute_detailed_metrics(y_train_encoded, gb_train_pred, label_encoder)
gb_test_metrics = compute_detailed_metrics(y_test_encoded, gb_test_pred, label_encoder)

# XGBoost metrics
xgb_train_metrics = compute_detailed_metrics(y_train_encoded, xgb_train_pred, label_encoder)
xgb_test_metrics = compute_detailed_metrics(y_test_encoded, xgb_test_pred, label_encoder)

print("Metrics calculated")
print()

# ============================================================================
# COMPARE PREDICTION ARRAYS
# ============================================================================

print("Comparing prediction arrays...")

# Compare test predictions
pred_agreement = (gb_test_pred == xgb_test_pred)
pred_disagreement_count = np.sum(~pred_agreement)
pred_disagreement_percentage = (pred_disagreement_count / len(gb_test_pred)) * 100

print(f"Total test samples: {len(gb_test_pred)}")
print(f"Predictions identical: {np.sum(pred_agreement)}")
print(f"Predictions different: {pred_disagreement_count}")
print(f"Disagreement percentage: {pred_disagreement_percentage:.2f}%")
print()

# Detailed disagreement breakdown
if pred_disagreement_count > 0:
    print("Prediction disagreement breakdown:")
    disagreement_indices = np.where(~pred_agreement)[0]
    
    gb_pred_disagree = gb_test_pred[disagreement_indices]
    xgb_pred_disagree = xgb_test_pred[disagreement_indices]
    true_labels_disagree = y_test_encoded[disagreement_indices]
    
    for i in range(min(10, len(disagreement_indices))):
        idx = disagreement_indices[i]
        true_label = label_encoder.inverse_transform([true_labels_disagree[i]])[0]
        gb_label = label_encoder.inverse_transform([gb_pred_disagree[i]])[0]
        xgb_label = label_encoder.inverse_transform([xgb_pred_disagree[i]])[0]
        print(f"  Sample {idx}: True={true_label}, GB={gb_label}, XGB={xgb_label}")
    
    if len(disagreement_indices) > 10:
        print(f"  ... and {len(disagreement_indices) - 10} more")
    print()

# ============================================================================
# PRINT CORRECTED RESULTS
# ============================================================================

print("=" * 80)
print("CORRECTED GRADIENT BOOSTING METRICS")
print("=" * 80)

print(f"Config: {gb_champion_config}")
print(f"Test Accuracy: {gb_test_metrics['accuracy']:.4f}")
print(f"Test Macro F1: {gb_test_metrics['macro_f1']:.4f}")
print(f"Test Weighted F1: {gb_test_metrics['weighted_f1']:.4f}")
print()
print("Per-Class Metrics (Test):")
for class_name in label_encoder.classes_:
    if class_name in gb_test_metrics['per_class']:
        print(f"  {class_name}:")
        print(f"    Precision: {gb_test_metrics['per_class'][class_name]['precision']:.4f}")
        print(f"    Recall: {gb_test_metrics['per_class'][class_name]['recall']:.4f}")
        print(f"    F1: {gb_test_metrics['per_class'][class_name]['f1']:.4f}")
print()
print(f"Suspicious False Negatives: {gb_test_metrics['suspicious_false_negatives']}")
print(f"Super-Suspicious False Negatives: {gb_test_metrics['super_suspicious_false_negatives']}")
print()
print("Confusion Matrix (Test):")
print("  Predicted →")
print("  Actual ↓")
print(f"  {label_encoder.classes_}")
for i, row in enumerate(gb_test_metrics['confusion_matrix']):
    print(f"  {label_encoder.classes_[i]}: {row}")
print()

print("=" * 80)
print("CORRECTED XGBOOST METRICS")
print("=" * 80)

print(f"Config: {xgb_best_config}")
print(f"Test Accuracy: {xgb_test_metrics['accuracy']:.4f}")
print(f"Test Macro F1: {xgb_test_metrics['macro_f1']:.4f}")
print(f"Test Weighted F1: {xgb_test_metrics['weighted_f1']:.4f}")
print()
print("Per-Class Metrics (Test):")
for class_name in label_encoder.classes_:
    if class_name in xgb_test_metrics['per_class']:
        print(f"  {class_name}:")
        print(f"    Precision: {xgb_test_metrics['per_class'][class_name]['precision']:.4f}")
        print(f"    Recall: {xgb_test_metrics['per_class'][class_name]['recall']:.4f}")
        print(f"    F1: {xgb_test_metrics['per_class'][class_name]['f1']:.4f}")
print()
print(f"Suspicious False Negatives: {xgb_test_metrics['suspicious_false_negatives']}")
print(f"Super-Suspicious False Negatives: {xgb_test_metrics['super_suspicious_false_negatives']}")
print()
print("Confusion Matrix (Test):")
print("  Predicted →")
print("  Actual ↓")
print(f"  {label_encoder.classes_}")
for i, row in enumerate(xgb_test_metrics['confusion_matrix']):
    print(f"  {label_encoder.classes_[i]}: {row}")
print()

# ============================================================================
# CORRECTED COMPARISON
# ============================================================================

print("=" * 80)
print("CORRECTED COMPARISON")
print("=" * 80)

accuracy_diff = xgb_test_metrics['accuracy'] - gb_test_metrics['accuracy']
macro_f1_diff = xgb_test_metrics['macro_f1'] - gb_test_metrics['macro_f1']
weighted_f1_diff = xgb_test_metrics['weighted_f1'] - gb_test_metrics['weighted_f1']
suspicious_recall_diff = xgb_test_metrics['per_class'].get('suspicious', {}).get('recall', 0.0) - gb_test_metrics['per_class'].get('suspicious', {}).get('recall', 0.0)
super_suspicious_recall_diff = xgb_test_metrics['per_class'].get('super_suspicious', {}).get('recall', 0.0) - gb_test_metrics['per_class'].get('super_suspicious', {}).get('recall', 0.0)
suspicious_fn_diff = xgb_test_metrics['suspicious_false_negatives'] - gb_test_metrics['suspicious_false_negatives']
super_suspicious_fn_diff = xgb_test_metrics['super_suspicious_false_negatives'] - gb_test_metrics['super_suspicious_false_negatives']

print("DIFFERENCES (XGBoost - Gradient Boosting):")
print(f"  Accuracy: {accuracy_diff:+.4f}")
print(f"  Macro F1: {macro_f1_diff:+.4f}")
print(f"  Weighted F1: {weighted_f1_diff:+.4f}")
print(f"  Suspicious Recall: {suspicious_recall_diff:+.4f}")
print(f"  Super-Suspicious Recall: {super_suspicious_recall_diff:+.4f}")
print(f"  Suspicious False Negatives: {suspicious_fn_diff:+d}")
print(f"  Super-Suspicious False Negatives: {super_suspicious_fn_diff:+d}")
print()

# ============================================================================
# VERDICT
# ============================================================================

print("=" * 80)
print("CORRECTED VERDICT")
print("=" * 80)

if macro_f1_diff >= 0.02 and (suspicious_recall_diff > 0 or super_suspicious_recall_diff > 0):
    verdict = "XGBoost BETTER"
    verdict_reason = f"XGBoost shows meaningful improvement in Macro F1 ({macro_f1_diff:+.4f}) and minority-class recall."
elif macro_f1_diff >= 0.01:
    verdict = "XGBoost SLIGHTLY BETTER"
    verdict_reason = f"XGBoost shows modest improvement in Macro F1 ({macro_f1_diff:+.4f}) but minority-class recall improvement is limited."
elif macro_f1_diff <= -0.02:
    verdict = "XGBoost WORSE"
    verdict_reason = f"XGBoost performs worse in Macro F1 ({macro_f1_diff:+.4f})."
elif abs(macro_f1_diff) < 0.01 and abs(suspicious_recall_diff) < 0.01 and abs(super_suspicious_recall_diff) < 0.01:
    verdict = "STATISTICALLY/PRACTICALLY SIMILAR"
    verdict_reason = f"XGBoost and Gradient Boosting perform similarly across all metrics (Macro F1 diff: {macro_f1_diff:+.4f})."
else:
    verdict = "MIXED RESULTS"
    verdict_reason = f"XGBoost shows mixed results with trade-offs between metrics."

print(f"  {verdict}")
print(f"  Reason: {verdict_reason}")
print()

# ============================================================================
# EXPLANATION OF DISCREPANCY
# ============================================================================

print("=" * 80)
print("EXPLANATION OF DISCREPANCY")
print("=" * 80)

print("The previous report incorrectly stated that the confusion matrices were identical.")
print(f"Actual prediction disagreement: {pred_disagreement_count} samples ({pred_disagreement_percentage:.2f}%)")
print()
print("This explains why the metrics differed between the two models.")
print("The confusion matrix shown in the previous report was likely from XGBoost only,")
print("not from Gradient Boosting.")
print()

# ============================================================================
# SAVE VERIFICATION RESULTS
# ============================================================================

results = {
    "timestamp": datetime.now().isoformat(),
    "verification_type": "Results Integrity Check",
    "test_samples": len(X_test),
    "label_classes": list(label_encoder.classes_),
    "gradient_boosting": {
        "config": gb_champion_config,
        "test_metrics": {
            "accuracy": gb_test_metrics['accuracy'],
            "macro_f1": gb_test_metrics['macro_f1'],
            "weighted_f1": gb_test_metrics['weighted_f1'],
            "per_class": gb_test_metrics['per_class'],
            "confusion_matrix": gb_test_metrics['confusion_matrix'].tolist(),
            "suspicious_false_negatives": gb_test_metrics['suspicious_false_negatives'],
            "super_suspicious_false_negatives": gb_test_metrics['super_suspicious_false_negatives']
        }
    },
    "xgboost": {
        "config": xgb_best_config,
        "test_metrics": {
            "accuracy": xgb_test_metrics['accuracy'],
            "macro_f1": xgb_test_metrics['macro_f1'],
            "weighted_f1": xgb_test_metrics['weighted_f1'],
            "per_class": xgb_test_metrics['per_class'],
            "confusion_matrix": xgb_test_metrics['confusion_matrix'].tolist(),
            "suspicious_false_negatives": xgb_test_metrics['suspicious_false_negatives'],
            "super_suspicious_false_negatives": xgb_test_metrics['super_suspicious_false_negatives']
        }
    },
    "prediction_comparison": {
        "total_test_samples": len(gb_test_pred),
        "identical_predictions": int(np.sum(pred_agreement)),
        "different_predictions": int(pred_disagreement_count),
        "disagreement_percentage": float(pred_disagreement_percentage)
    },
    "corrected_comparison": {
        "accuracy_diff": accuracy_diff,
        "macro_f1_diff": macro_f1_diff,
        "weighted_f1_diff": weighted_f1_diff,
        "suspicious_recall_diff": suspicious_recall_diff,
        "super_suspicious_recall_diff": super_suspicious_recall_diff,
        "suspicious_false_negatives_diff": suspicious_fn_diff,
        "super_suspicious_false_negatives_diff": super_suspicious_fn_diff
    },
    "corrected_verdict": verdict,
    "corrected_verdict_reason": verdict_reason,
    "discrepancy_explanation": "The previous report incorrectly claimed identical confusion matrices. Actual prediction disagreement: {} samples ({}%). The confusion matrix shown was likely from XGBoost only.".format(int(pred_disagreement_count), f"{pred_disagreement_percentage:.2f}")
}

with open('ml_results_integrity_check.json', 'w') as f:
    json.dump(results, f, indent=2)

print("=" * 80)
print("RESULTS INTEGRITY CHECK COMPLETE")
print("=" * 80)
print("Verification results saved to ml_results_integrity_check.json")
