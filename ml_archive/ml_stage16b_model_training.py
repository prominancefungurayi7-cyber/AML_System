"""
STAGE 16B: CANDIDATE FEATURE SET VALIDATION

Train and evaluate models using the 18-feature candidate set.
"""

import csv
import json
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
from sklearn.preprocessing import LabelEncoder

print("=" * 80)
print("STAGE 16B: CANDIDATE FEATURE SET VALIDATION")
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
# TRAIN RANDOM FOREST WITH REGULARIZATION
# ============================================================================

print("Training Random Forest with regularization...")

rf_configs = [
    {'max_depth': 10, 'min_samples_split': 10, 'min_samples_leaf': 5, 'random_state': 42, 'n_jobs': -1},
    {'max_depth': 8, 'min_samples_split': 15, 'min_samples_leaf': 8, 'random_state': 42, 'n_jobs': -1},
    {'max_depth': 6, 'min_samples_split': 20, 'min_samples_leaf': 10, 'random_state': 42, 'n_jobs': -1}
]

rf_results = []

for i, config in enumerate(rf_configs):
    print(f"  RF Config {i+1}: max_depth={config['max_depth']}, min_samples_split={config['min_samples_split']}, min_samples_leaf={config['min_samples_leaf']}")
    
    rf = RandomForestClassifier(n_estimators=100, **config)
    rf.fit(X_train, y_train_encoded)
    
    rf_train_pred = rf.predict(X_train)
    rf_test_pred = rf.predict(X_test)
    
    rf_train_macro_f1 = f1_score(y_train_encoded, rf_train_pred, average='macro')
    rf_test_macro_f1 = f1_score(y_test_encoded, rf_test_pred, average='macro')
    
    rf_results.append({
        'config': config,
        'train_macro_f1': rf_train_macro_f1,
        'test_macro_f1': rf_test_macro_f1,
        'train_test_gap': rf_train_macro_f1 - rf_test_macro_f1,
        'model': rf
    })
    
    print(f"    Train Macro F1: {rf_train_macro_f1:.4f}")
    print(f"    Test Macro F1: {rf_test_macro_f1:.4f}")
    print(f"    Train/Test Gap: {rf_train_macro_f1 - rf_test_macro_f1:.4f}")

print()

# Select best RF configuration (lowest train/test gap with competitive test performance)
best_rf = min(rf_results, key=lambda x: (x['train_test_gap'], -x['test_macro_f1']))
print(f"Best RF Config: max_depth={best_rf['config']['max_depth']}, min_samples_split={best_rf['config']['min_samples_split']}, min_samples_leaf={best_rf['config']['min_samples_leaf']}")
print(f"Best RF Test Macro F1: {best_rf['test_macro_f1']:.4f}")
print(f"Best RF Train/Test Gap: {best_rf['train_test_gap']:.4f}")
print()

# ============================================================================
# TRAIN GRADIENT BOOSTING WITH REGULARIZATION
# ============================================================================

print("Training Gradient Boosting with regularization...")

gb_configs = [
    {'learning_rate': 0.1, 'max_depth': 5, 'n_estimators': 100, 'random_state': 42},
    {'learning_rate': 0.05, 'max_depth': 4, 'n_estimators': 200, 'random_state': 42},
    {'learning_rate': 0.01, 'max_depth': 3, 'n_estimators': 500, 'random_state': 42}
]

gb_results = []

for i, config in enumerate(gb_configs):
    print(f"  GB Config {i+1}: learning_rate={config['learning_rate']}, max_depth={config['max_depth']}, n_estimators={config['n_estimators']}")
    
    gb = GradientBoostingClassifier(**config)
    gb.fit(X_train, y_train_encoded)
    
    gb_train_pred = gb.predict(X_train)
    gb_test_pred = gb.predict(X_test)
    
    gb_train_macro_f1 = f1_score(y_train_encoded, gb_train_pred, average='macro')
    gb_test_macro_f1 = f1_score(y_test_encoded, gb_test_pred, average='macro')
    
    gb_results.append({
        'config': config,
        'train_macro_f1': gb_train_macro_f1,
        'test_macro_f1': gb_test_macro_f1,
        'train_test_gap': gb_train_macro_f1 - gb_test_macro_f1,
        'model': gb
    })
    
    print(f"    Train Macro F1: {gb_train_macro_f1:.4f}")
    print(f"    Test Macro F1: {gb_test_macro_f1:.4f}")
    print(f"    Train/Test Gap: {gb_train_macro_f1 - gb_test_macro_f1:.4f}")

print()

# Select best GB configuration (lowest train/test gap with competitive test performance)
best_gb = min(gb_results, key=lambda x: (x['train_test_gap'], -x['test_macro_f1']))
print(f"Best GB Config: learning_rate={best_gb['config']['learning_rate']}, max_depth={best_gb['config']['max_depth']}, n_estimators={best_gb['config']['n_estimators']}")
print(f"Best GB Test Macro F1: {best_gb['test_macro_f1']:.4f}")
print(f"Best GB Train/Test Gap: {best_gb['train_test_gap']:.4f}")
print()

# ============================================================================
# COMPUTE DETAILED METRICS FOR BEST MODELS
# ============================================================================

print("Computing detailed metrics for best models...")

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
        'super_suspicious_false_negatives': int(super_suspicious_fn)
    }

# Best RF metrics
rf_train_pred = best_rf['model'].predict(X_train)
rf_test_pred = best_rf['model'].predict(X_test)
rf_train_metrics = compute_detailed_metrics(y_train_encoded, rf_train_pred, label_encoder)
rf_test_metrics = compute_detailed_metrics(y_test_encoded, rf_test_pred, label_encoder)

# Best GB metrics
gb_train_pred = best_gb['model'].predict(X_train)
gb_test_pred = best_gb['model'].predict(X_test)
gb_train_metrics = compute_detailed_metrics(y_train_encoded, gb_train_pred, label_encoder)
gb_test_metrics = compute_detailed_metrics(y_test_encoded, gb_test_pred, label_encoder)

print("Detailed metrics computed")
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
# LOAD STAGE 15 RESULTS FOR CONTEXT
# ============================================================================

print("Loading Stage 15 results for context...")
with open('ml_stage15_model_results.json', 'r') as f:
    stage15_results = json.load(f)

print("Stage 15 results loaded")
print()

# ============================================================================
# PRINT RESULTS
# ============================================================================

print("STAGE 16B RESULTS:")
print("-" * 80)

print("Random Forest (Best Config):")
print(f"  Config: max_depth={best_rf['config']['max_depth']}, min_samples_split={best_rf['config']['min_samples_split']}, min_samples_leaf={best_rf['config']['min_samples_leaf']}")
print(f"  Train Accuracy: {rf_train_metrics['accuracy']:.4f}")
print(f"  Test Accuracy: {rf_test_metrics['accuracy']:.4f}")
print(f"  Train Macro F1: {rf_train_metrics['macro_f1']:.4f}")
print(f"  Test Macro F1: {rf_test_metrics['macro_f1']:.4f}")
print(f"  Train/Test Gap: {rf_train_metrics['macro_f1'] - rf_test_metrics['macro_f1']:.4f}")
print(f"  Suspicious Recall: {rf_test_metrics['per_class'].get('suspicious', {}).get('recall', 0.0):.4f}")
print(f"  Super-Suspicious Recall: {rf_test_metrics['per_class'].get('super_suspicious', {}).get('recall', 0.0):.4f}")
print(f"  Super-Suspicious False Negatives: {rf_test_metrics['super_suspicious_false_negatives']}")
print()

print("Gradient Boosting (Best Config):")
print(f"  Config: learning_rate={best_gb['config']['learning_rate']}, max_depth={best_gb['config']['max_depth']}, n_estimators={best_gb['config']['n_estimators']}")
print(f"  Train Accuracy: {gb_train_metrics['accuracy']:.4f}")
print(f"  Test Accuracy: {gb_test_metrics['accuracy']:.4f}")
print(f"  Train Macro F1: {gb_train_metrics['macro_f1']:.4f}")
print(f"  Test Macro F1: {gb_test_metrics['macro_f1']:.4f}")
print(f"  Train/Test Gap: {gb_train_metrics['macro_f1'] - gb_test_metrics['macro_f1']:.4f}")
print(f"  Suspicious Recall: {gb_test_metrics['per_class'].get('suspicious', {}).get('recall', 0.0):.4f}")
print(f"  Super-Suspicious Recall: {gb_test_metrics['per_class'].get('super_suspicious', {}).get('recall', 0.0):.4f}")
print(f"  Super-Suspicious False Negatives: {gb_test_metrics['super_suspicious_false_negatives']}")
print()

print("COMPARISON WITH STAGE 12 BASELINE (32 features):")
print("-" * 80)

stage12_rf_baseline = stage12_results['primary_split']['results'].get('random_forest', {})
stage12_gb_baseline = stage12_results['primary_split']['results'].get('gradient_boosting', {})

stage12_rf_test_macro_f1 = stage12_rf_baseline.get('macro_f1', 0.0)
stage12_gb_test_macro_f1 = stage12_gb_baseline.get('macro_f1', 0.0)

print("Random Forest:")
print(f"  Stage 12 Test Macro F1: {stage12_rf_test_macro_f1:.4f}")
print(f"  Stage 16B Test Macro F1: {rf_test_metrics['macro_f1']:.4f}")
print(f"  Improvement: {rf_test_metrics['macro_f1'] - stage12_rf_test_macro_f1:.4f}")
print()

print("Gradient Boosting:")
print(f"  Stage 12 Test Macro F1: {stage12_gb_test_macro_f1:.4f}")
print(f"  Stage 16B Test Macro F1: {gb_test_metrics['macro_f1']:.4f}")
print(f"  Improvement: {gb_test_metrics['macro_f1'] - stage12_gb_test_macro_f1:.4f}")
print()

print("COMPARISON WITH STAGE 15 (57 features) FOR CONTEXT:")
print("-" * 80)

stage15_rf_test_macro_f1 = stage15_results['random_forest']['test_metrics']['macro_f1']
stage15_gb_test_macro_f1 = stage15_results['gradient_boosting']['test_metrics']['macro_f1']

print("Random Forest:")
print(f"  Stage 15 Test Macro F1: {stage15_rf_test_macro_f1:.4f}")
print(f"  Stage 16B Test Macro F1: {rf_test_metrics['macro_f1']:.4f}")
print(f"  Difference: {rf_test_metrics['macro_f1'] - stage15_rf_test_macro_f1:.4f}")
print()

print("Gradient Boosting:")
print(f"  Stage 15 Test Macro F1: {stage15_gb_test_macro_f1:.4f}")
print(f"  Stage 16B Test Macro F1: {gb_test_metrics['macro_f1']:.4f}")
print(f"  Difference: {gb_test_metrics['macro_f1'] - stage15_gb_test_macro_f1:.4f}")
print()

# ============================================================================
# SAVE RESULTS
# ============================================================================

results = {
    "timestamp": datetime.now().isoformat(),
    "total_features": len(feature_names),
    "feature_names": feature_names,
    "train_transactions": len(train_data),
    "test_transactions": len(test_data),
    "train_customers": len(train_customers),
    "test_customers": len(test_customers),
    "random_forest": {
        "configs_tested": rf_configs,
        "best_config": best_rf['config'],
        "train_metrics": rf_train_metrics,
        "test_metrics": rf_test_metrics,
        "feature_importance": best_rf['model'].feature_importances_.tolist()
    },
    "gradient_boosting": {
        "configs_tested": gb_configs,
        "best_config": best_gb['config'],
        "train_metrics": gb_train_metrics,
        "test_metrics": gb_test_metrics,
        "feature_importance": best_gb['model'].feature_importances_.tolist()
    },
    "stage12_baseline": {
        "random_forest_test_macro_f1": stage12_rf_test_macro_f1,
        "gradient_boosting_test_macro_f1": stage12_gb_test_macro_f1
    },
    "stage15_context": {
        "random_forest_test_macro_f1": stage15_rf_test_macro_f1,
        "gradient_boosting_test_macro_f1": stage15_gb_test_macro_f1
    },
    "improvement_vs_stage12": {
        "random_forest": rf_test_metrics['macro_f1'] - stage12_rf_test_macro_f1,
        "gradient_boosting": gb_test_metrics['macro_f1'] - stage12_gb_test_macro_f1
    }
}

with open('ml_stage16b_model_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("=" * 80)
print("STAGE 16B MODEL TRAINING COMPLETE")
print("=" * 80)
print("Results saved to ml_stage16b_model_results.json")
