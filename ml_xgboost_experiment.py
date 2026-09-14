"""
XGBOOST EXPERIMENT - MODEL IMPROVEMENT

Evaluate XGBoost as a candidate model against the current Gradient Boosting champion.
Uses the same 18-feature dataset, customer holdout, and evaluation methodology.
"""

import csv
import json
import numpy as np
from datetime import datetime
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
from sklearn.preprocessing import LabelEncoder

print("=" * 80)
print("XGBOOST EXPERIMENT - MODEL IMPROVEMENT")
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
print(f"Label classes: {label_encoder.classes_}")
print()

# ============================================================================
# LOAD CURRENT GRADIENT BOOSTING CHAMPION RESULTS
# ============================================================================

print("Loading current Gradient Boosting champion results...")
with open('ml_stage16b_model_results.json', 'r') as f:
    gb_champion_results = json.load(f)

gb_champion_metrics = gb_champion_results['gradient_boosting']['test_metrics']
gb_champion_config = gb_champion_results['gradient_boosting']['best_config']

print("Gradient Boosting Champion:")
print(f"  Config: {gb_champion_config}")
print(f"  Test Accuracy: {gb_champion_metrics['accuracy']:.4f}")
print(f"  Test Macro F1: {gb_champion_metrics['macro_f1']:.4f}")
print(f"  Suspicious Recall: {gb_champion_metrics['per_class'].get('suspicious', {}).get('recall', 0.0):.4f}")
print(f"  Super-Suspicious Recall: {gb_champion_metrics['per_class'].get('super_suspicious', {}).get('recall', 0.0):.4f}")
print()

# ============================================================================
# TRAIN XGBOOST WITH REGULARIZED BASELINE
# ============================================================================

print("Training XGBoost with regularized baseline...")

try:
    import xgboost as xgb
    print("XGBoost library available")
except ImportError:
    print("ERROR: XGBoost library not available. Installing...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'xgboost'])
    import xgboost as xgb
    print("XGBoost installed successfully")

# Sensible regularized XGBoost configurations
# Using conservative parameters to avoid overfitting
xgb_configs = [
    {
        'learning_rate': 0.1, 
        'max_depth': 5, 
        'n_estimators': 100, 
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'min_child_weight': 5,
        'gamma': 0.1,
        'reg_alpha': 0.1,
        'reg_lambda': 1.0,
        'random_state': 42,
        'eval_metric': 'mlogloss'
    },
    {
        'learning_rate': 0.05, 
        'max_depth': 4, 
        'n_estimators': 200, 
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'min_child_weight': 5,
        'gamma': 0.1,
        'reg_alpha': 0.1,
        'reg_lambda': 1.0,
        'random_state': 42,
        'eval_metric': 'mlogloss'
    },
    {
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
]

xgb_results = []

for i, config in enumerate(xgb_configs):
    print(f"  XGB Config {i+1}: learning_rate={config['learning_rate']}, max_depth={config['max_depth']}, n_estimators={config['n_estimators']}")
    
    xgb_model = xgb.XGBClassifier(**config)
    xgb_model.fit(X_train, y_train_encoded)
    
    xgb_train_pred = xgb_model.predict(X_train)
    xgb_test_pred = xgb_model.predict(X_test)
    
    xgb_train_macro_f1 = f1_score(y_train_encoded, xgb_train_pred, average='macro')
    xgb_test_macro_f1 = f1_score(y_test_encoded, xgb_test_pred, average='macro')
    
    xgb_results.append({
        'config': config,
        'train_macro_f1': xgb_train_macro_f1,
        'test_macro_f1': xgb_test_macro_f1,
        'train_test_gap': xgb_train_macro_f1 - xgb_test_macro_f1,
        'model': xgb_model
    })
    
    print(f"    Train Macro F1: {xgb_train_macro_f1:.4f}")
    print(f"    Test Macro F1: {xgb_test_macro_f1:.4f}")
    print(f"    Train/Test Gap: {xgb_train_macro_f1 - xgb_test_macro_f1:.4f}")

print()

# Select best XGB configuration (lowest train/test gap with competitive test performance)
best_xgb = min(xgb_results, key=lambda x: (x['train_test_gap'], -x['test_macro_f1']))
print(f"Best XGB Config: learning_rate={best_xgb['config']['learning_rate']}, max_depth={best_xgb['config']['max_depth']}, n_estimators={best_xgb['config']['n_estimators']}")
print(f"Best XGB Test Macro F1: {best_xgb['test_macro_f1']:.4f}")
print(f"Best XGB Train/Test Gap: {best_xgb['train_test_gap']:.4f}")
print()

# ============================================================================
# COMPUTE DETAILED METRICS FOR BEST XGBOOST
# ============================================================================

print("Computing detailed metrics for best XGBoost...")

def compute_detailed_metrics(y_true, y_pred, label_encoder):
    """Compute detailed classification metrics."""
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
        'confusion_matrix': cm.tolist(),
        'false_positives': fp.tolist(),
        'false_negatives': fn.tolist(),
        'suspicious_false_negatives': int(suspicious_fn),
        'super_suspicious_false_negatives': int(super_suspicious_fn)
    }

# Best XGB metrics
xgb_train_pred = best_xgb['model'].predict(X_train)
xgb_test_pred = best_xgb['model'].predict(X_test)
xgb_train_metrics = compute_detailed_metrics(y_train_encoded, xgb_train_pred, label_encoder)
xgb_test_metrics = compute_detailed_metrics(y_test_encoded, xgb_test_pred, label_encoder)

print("Detailed metrics computed")
print()

# ============================================================================
# PRINT XGBOOST RESULTS
# ============================================================================

print("XGBOOST RESULTS:")
print("-" * 80)

print("XGBoost (Best Config):")
print(f"  Config: learning_rate={best_xgb['config']['learning_rate']}, max_depth={best_xgb['config']['max_depth']}, n_estimators={best_xgb['config']['n_estimators']}")
print(f"  Train Accuracy: {xgb_train_metrics['accuracy']:.4f}")
print(f"  Test Accuracy: {xgb_test_metrics['accuracy']:.4f}")
print(f"  Train Macro F1: {xgb_train_metrics['macro_f1']:.4f}")
print(f"  Test Macro F1: {xgb_test_metrics['macro_f1']:.4f}")
print(f"  Train/Test Gap: {xgb_train_metrics['macro_f1'] - xgb_test_metrics['macro_f1']:.4f}")
print(f"  Test Weighted F1: {xgb_test_metrics['weighted_f1']:.4f}")
print()
print("Per-Class Metrics (Test):")
for class_name in label_encoder.classes_:
    if class_name in xgb_test_metrics['per_class']:
        print(f"  {class_name}:")
        print(f"    Precision: {xgb_test_metrics['per_class'][class_name]['precision']:.4f}")
        print(f"    Recall: {xgb_test_metrics['per_class'][class_name]['recall']:.4f}")
        print(f"    F1: {xgb_test_metrics['per_class'][class_name]['f1']:.4f}")
print()
print(f"  Suspicious False Negatives: {xgb_test_metrics['suspicious_false_negatives']}")
print(f"  Super-Suspicious False Negatives: {xgb_test_metrics['super_suspicious_false_negatives']}")
print()

print("Confusion Matrix (Test):")
print("  Predicted →")
print("  Actual ↓")
cm = np.array(xgb_test_metrics['confusion_matrix'])
print(f"  {label_encoder.classes_}")
for i, row in enumerate(cm):
    print(f"  {label_encoder.classes_[i]}: {row}")
print()

# ============================================================================
# DIRECT COMPARISON WITH GRADIENT BOOSTING CHAMPION
# ============================================================================

print("DIRECT COMPARISON: XGBoost vs Gradient Boosting Champion")
print("=" * 80)

print("Gradient Boosting Champion:")
print(f"  Config: {gb_champion_config}")
print(f"  Test Accuracy: {gb_champion_metrics['accuracy']:.4f}")
print(f"  Test Macro F1: {gb_champion_metrics['macro_f1']:.4f}")
print(f"  Test Weighted F1: {gb_champion_metrics['weighted_f1']:.4f}")
print(f"  Suspicious Recall: {gb_champion_metrics['per_class'].get('suspicious', {}).get('recall', 0.0):.4f}")
print(f"  Super-Suspicious Recall: {gb_champion_metrics['per_class'].get('super_suspicious', {}).get('recall', 0.0):.4f}")
print(f"  Suspicious False Negatives: {gb_champion_metrics['false_negatives'][label_encoder.transform(['suspicious'])[0]] if 'suspicious' in label_encoder.classes_ else 'N/A'}")
print(f"  Super-Suspicious False Negatives: {gb_champion_metrics['super_suspicious_false_negatives']}")
print()

print("XGBoost Candidate:")
print(f"  Config: learning_rate={best_xgb['config']['learning_rate']}, max_depth={best_xgb['config']['max_depth']}, n_estimators={best_xgb['config']['n_estimators']}")
print(f"  Test Accuracy: {xgb_test_metrics['accuracy']:.4f}")
print(f"  Test Macro F1: {xgb_test_metrics['macro_f1']:.4f}")
print(f"  Test Weighted F1: {xgb_test_metrics['weighted_f1']:.4f}")
print(f"  Suspicious Recall: {xgb_test_metrics['per_class'].get('suspicious', {}).get('recall', 0.0):.4f}")
print(f"  Super-Suspicious Recall: {xgb_test_metrics['per_class'].get('super_suspicious', {}).get('recall', 0.0):.4f}")
print(f"  Suspicious False Negatives: {xgb_test_metrics['suspicious_false_negatives']}")
print(f"  Super-Suspicious False Negatives: {xgb_test_metrics['super_suspicious_false_negatives']}")
print()

print("DIFFERENCES (XGBoost - GB Champion):")
print("-" * 80)
accuracy_diff = xgb_test_metrics['accuracy'] - gb_champion_metrics['accuracy']
macro_f1_diff = xgb_test_metrics['macro_f1'] - gb_champion_metrics['macro_f1']
weighted_f1_diff = xgb_test_metrics['weighted_f1'] - gb_champion_metrics['weighted_f1']
suspicious_recall_diff = xgb_test_metrics['per_class'].get('suspicious', {}).get('recall', 0.0) - gb_champion_metrics['per_class'].get('suspicious', {}).get('recall', 0.0)
super_suspicious_recall_diff = xgb_test_metrics['per_class'].get('super_suspicious', {}).get('recall', 0.0) - gb_champion_metrics['per_class'].get('super_suspicious', {}).get('recall', 0.0)
suspicious_fn_diff = xgb_test_metrics['suspicious_false_negatives'] - (gb_champion_metrics['false_negatives'][label_encoder.transform(['suspicious'])[0]] if 'suspicious' in label_encoder.classes_ else 0)
super_suspicious_fn_diff = xgb_test_metrics['super_suspicious_false_negatives'] - gb_champion_metrics['super_suspicious_false_negatives']

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

print("VERDICT:")
print("=" * 80)

# Determine verdict based on Macro F1 and minority-class recall
macro_f1_improvement = macro_f1_diff
suspicious_recall_improvement = suspicious_recall_diff
super_suspicious_recall_improvement = super_suspicious_recall_diff

# Meaningful improvement threshold: at least 0.02 (2 percentage points) in Macro F1
# AND improvement in minority-class recall
if macro_f1_improvement >= 0.02 and (suspicious_recall_improvement > 0 or super_suspicious_recall_improvement > 0):
    verdict = "XGBoost BETTER"
    verdict_reason = f"XGBoost shows meaningful improvement in Macro F1 ({macro_f1_improvement:+.4f}) and minority-class recall."
elif macro_f1_improvement >= 0.01:
    verdict = "XGBoost SLIGHTLY BETTER"
    verdict_reason = f"XGBoost shows modest improvement in Macro F1 ({macro_f1_improvement:+.4f}) but minority-class recall improvement is limited."
elif macro_f1_improvement <= -0.02:
    verdict = "XGBoost WORSE"
    verdict_reason = f"XGBoost performs worse in Macro F1 ({macro_f1_improvement:+.4f})."
elif abs(macro_f1_improvement) < 0.01 and abs(suspicious_recall_improvement) < 0.01 and abs(super_suspicious_recall_improvement) < 0.01:
    verdict = "STATISTICALLY/PRACTICALLY SIMILAR"
    verdict_reason = f"XGBoost and Gradient Boosting perform similarly across all metrics (Macro F1 diff: {macro_f1_improvement:+.4f})."
else:
    verdict = "MIXED RESULTS"
    verdict_reason = f"XGBoost shows mixed results with trade-offs between metrics."

print(f"  {verdict}")
print(f"  Reason: {verdict_reason}")
print()

# ============================================================================
# SAVE RESULTS
# ============================================================================

results = {
    "timestamp": datetime.now().isoformat(),
    "experiment_type": "XGBoost vs Gradient Boosting Champion",
    "total_features": len(feature_names),
    "feature_names": feature_names,
    "train_transactions": len(train_data),
    "test_transactions": len(test_data),
    "train_customers": len(train_customers),
    "test_customers": len(test_customers),
    "gradient_boosting_champion": {
        "config": gb_champion_config,
        "test_metrics": gb_champion_metrics
    },
    "xgboost_candidate": {
        "configs_tested": xgb_configs,
        "best_config": best_xgb['config'],
        "train_metrics": xgb_train_metrics,
        "test_metrics": xgb_test_metrics,
        "feature_importance": best_xgb['model'].feature_importances_.tolist()
    },
    "comparison": {
        "accuracy_diff": accuracy_diff,
        "macro_f1_diff": macro_f1_diff,
        "weighted_f1_diff": weighted_f1_diff,
        "suspicious_recall_diff": suspicious_recall_diff,
        "super_suspicious_recall_diff": super_suspicious_recall_diff,
        "suspicious_false_negatives_diff": suspicious_fn_diff,
        "super_suspicious_false_negatives_diff": super_suspicious_fn_diff
    },
    "verdict": verdict,
    "verdict_reason": verdict_reason
}

with open('ml_xgboost_experiment_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("=" * 80)
print("XGBOOST EXPERIMENT COMPLETE")
print("=" * 80)
print("Results saved to ml_xgboost_experiment_results.json")
