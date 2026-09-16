"""
STAGE 17: CONTROLLED HYPERPARAMETER EXPERIMENT

Investigate whether Gradient Boosting can generalize better through
controlled hyperparameter tuning around the frozen champion configuration.
"""

import csv
import json
import numpy as np
from datetime import datetime
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score, StratifiedKFold

print("=" * 80)
print("STAGE 17: CONTROLLED HYPERPARAMETER EXPERIMENT")
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
print(f"Customer overlap: {len(train_customers & test_customers)}")
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
print()

# ============================================================================
# DEFINE HYPERPARAMETER CONFIGURATIONS
# ============================================================================

print("Defining hyperparameter configurations...")
print()

# Small, focused grid around the frozen champion
# Champion: learning_rate=0.01, max_depth=3, n_estimators=500, random_state=42

hyperparameter_configs = [
    # Champion (baseline)
    {
        'name': 'Champion_Baseline',
        'learning_rate': 0.01,
        'max_depth': 3,
        'n_estimators': 500,
        'subsample': 1.0,
        'min_samples_split': 2,
        'min_samples_leaf': 1,
        'random_state': 42
    },
    # Lower learning rate, more trees (reduce overfitting)
    {
        'name': 'Lower_LR_More_Trees',
        'learning_rate': 0.005,
        'max_depth': 3,
        'n_estimators': 700,
        'subsample': 1.0,
        'min_samples_split': 2,
        'min_samples_leaf': 1,
        'random_state': 42
    },
    # Higher learning rate, fewer trees (reduce underfitting)
    {
        'name': 'Higher_LR_Fewer_Trees',
        'learning_rate': 0.02,
        'max_depth': 3,
        'n_estimators': 300,
        'subsample': 1.0,
        'min_samples_split': 2,
        'min_samples_leaf': 1,
        'random_state': 42
    },
    # Shallower trees (reduce overfitting)
    {
        'name': 'Shallower_Trees',
        'learning_rate': 0.01,
        'max_depth': 2,
        'n_estimators': 500,
        'subsample': 1.0,
        'min_samples_split': 2,
        'min_samples_leaf': 1,
        'random_state': 42
    },
    # Deeper trees (reduce underfitting)
    {
        'name': 'Deeper_Trees',
        'learning_rate': 0.01,
        'max_depth': 4,
        'n_estimators': 500,
        'subsample': 1.0,
        'min_samples_split': 2,
        'min_samples_leaf': 1,
        'random_state': 42
    },
    # Subsampling (stochastic gradient boosting)
    {
        'name': 'Subsampling',
        'learning_rate': 0.01,
        'max_depth': 3,
        'n_estimators': 500,
        'subsample': 0.8,
        'min_samples_split': 2,
        'min_samples_leaf': 1,
        'random_state': 42
    },
    # More regularization (min_samples_split, min_samples_leaf)
    {
        'name': 'More_Regularization',
        'learning_rate': 0.01,
        'max_depth': 3,
        'n_estimators': 500,
        'subsample': 1.0,
        'min_samples_split': 10,
        'min_samples_leaf': 5,
        'random_state': 42
    },
    # Combined: lower LR + subsampling + regularization
    {
        'name': 'Combined_Regularized',
        'learning_rate': 0.005,
        'max_depth': 3,
        'n_estimators': 700,
        'subsample': 0.8,
        'min_samples_split': 10,
        'min_samples_leaf': 5,
        'random_state': 42
    }
]

for config in hyperparameter_configs:
    print(f"  {config['name']}:")
    for key, value in config.items():
        if key != 'name' and key != 'random_state':
            print(f"    {key}: {value}")
print()

# ============================================================================
# CROSS-VALIDATION ON TRAINING DATA ONLY
# ============================================================================

print("Performing cross-validation on training data only...")
print()

cv_results = []
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

for config in hyperparameter_configs:
    print(f"{'='*80}")
    print(f"CONFIG: {config['name']}")
    print(f"{'='*80}")
    
    # Extract hyperparameters (excluding name)
    hp = {k: v for k, v in config.items() if k != 'name'}
    
    # Create model
    gb = GradientBoostingClassifier(**hp)
    
    # Cross-validation on training data only
    cv_macro_f1_scores = cross_val_score(gb, X_train, y_train_encoded, cv=cv, scoring='f1_macro')
    
    cv_mean_macro_f1 = cv_macro_f1_scores.mean()
    cv_std_macro_f1 = cv_macro_f1_scores.std()
    
    print(f"CV Macro F1 scores: {cv_macro_f1_scores}")
    print(f"CV Mean Macro F1: {cv_mean_macro_f1:.4f}")
    print(f"CV Std Macro F1: {cv_std_macro_f1:.4f}")
    print()
    
    cv_results.append({
        'config': config,
        'hp': hp,
        'cv_mean_macro_f1': cv_mean_macro_f1,
        'cv_std_macro_f1': cv_std_macro_f1,
        'cv_scores': cv_macro_f1_scores
    })

# ============================================================================
# SELECT BEST CONFIGURATION BASED ON CV
# ============================================================================

print("=" * 80)
print("SELECTING BEST CONFIGURATION BASED ON CV")
print("=" * 80)
print()

# Select based on mean CV Macro F1
best_cv_result = max(cv_results, key=lambda x: x['cv_mean_macro_f1'])

print(f"Best CV configuration: {best_cv_result['config']['name']}")
print(f"CV Mean Macro F1: {best_cv_result['cv_mean_macro_f1']:.4f}")
print(f"CV Std Macro F1: {best_cv_result['cv_std_macro_f1']:.4f}")
print()

# ============================================================================
# TRAIN SELECTED CONFIGURATION ON FULL TRAINING DATA
# ============================================================================

print("Training selected configuration on full training data...")

best_config_name = best_cv_result['config']['name']
best_hp = best_cv_result['hp']

best_model = GradientBoostingClassifier(**best_hp)
best_model.fit(X_train, y_train_encoded)

print(f"Trained {best_config_name}")
print()

# ============================================================================
# EVALUATE ON UNTOUCHED TEST SET
# ============================================================================

print("Evaluating on untouched test set...")
print()

test_pred = best_model.predict(X_test)

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

test_metrics = compute_detailed_metrics(y_test_encoded, test_pred, label_encoder)

print(f"Test Accuracy: {test_metrics['accuracy']:.4f}")
print(f"Test Macro F1: {test_metrics['macro_f1']:.4f}")
print(f"Test Weighted F1: {test_metrics['weighted_f1']:.4f}")
print(f"Suspicious Recall: {test_metrics['per_class']['suspicious']['recall']:.4f}")
print(f"Super-Suspicious Recall: {test_metrics['per_class']['super_suspicious']['recall']:.4f}")
print(f"Suspicious False Negatives: {test_metrics['suspicious_false_negatives']}")
print(f"Super-Suspicious False Negatives: {test_metrics['super_suspicious_false_negatives']}")
print()

print("Confusion Matrix (Test):")
print("  Predicted →")
print("  Actual ↓")
print(f"  {label_encoder.classes_}")
for i, row in enumerate(test_metrics['confusion_matrix']):
    print(f"  {label_encoder.classes_[i]}: {row}")
print()

# ============================================================================
# LOAD CHAMPION RESULTS FOR COMPARISON
# ============================================================================

print("=" * 80)
print("LOADING CHAMPION RESULTS FOR COMPARISON")
print("=" * 80)
print()

with open('ml_stage16b_model_results.json', 'r') as f:
    champion_results = json.load(f)

champion_metrics = champion_results['gradient_boosting']['test_metrics']
champion_config = champion_results['gradient_boosting']['best_config']

print("Gradient Boosting Champion:")
print(f"  Config: {champion_config}")
print(f"  Test Accuracy: {champion_metrics['accuracy']:.4f}")
print(f"  Test Macro F1: {champion_metrics['macro_f1']:.4f}")
print(f"  Test Weighted F1: {champion_metrics['weighted_f1']:.4f}")
print(f"  Suspicious Recall: {champion_metrics['per_class']['suspicious']['recall']:.4f}")
print(f"  Super-Suspicious Recall: {champion_metrics['per_class']['super_suspicious']['recall']:.4f}")
print(f"  Suspicious False Negatives: {champion_metrics['false_negatives'][label_encoder.transform(['suspicious'])[0]]}")
print(f"  Super-Suspicious False Negatives: {champion_metrics['super_suspicious_false_negatives']}")
print()

# ============================================================================
# COMPARISON WITH CHAMPION
# ============================================================================

print("=" * 80)
print("COMPARISON WITH CHAMPION")
print("=" * 80)
print()

accuracy_diff = test_metrics['accuracy'] - champion_metrics['accuracy']
macro_f1_diff = test_metrics['macro_f1'] - champion_metrics['macro_f1']
weighted_f1_diff = test_metrics['weighted_f1'] - champion_metrics['weighted_f1']
suspicious_recall_diff = test_metrics['per_class']['suspicious']['recall'] - champion_metrics['per_class']['suspicious']['recall']
super_suspicious_recall_diff = test_metrics['per_class']['super_suspicious']['recall'] - champion_metrics['per_class']['super_suspicious']['recall']
suspicious_fn_diff = test_metrics['suspicious_false_negatives'] - champion_metrics['false_negatives'][label_encoder.transform(['suspicious'])[0]]
super_suspicious_fn_diff = test_metrics['super_suspicious_false_negatives'] - champion_metrics['super_suspicious_false_negatives']

print(f"{best_config_name} vs Champion:")
print(f"  Accuracy: {test_metrics['accuracy']:.4f} vs {champion_metrics['accuracy']:.4f} ({accuracy_diff:+.4f})")
print(f"  Macro F1: {test_metrics['macro_f1']:.4f} vs {champion_metrics['macro_f1']:.4f} ({macro_f1_diff:+.4f})")
print(f"  Weighted F1: {test_metrics['weighted_f1']:.4f} vs {champion_metrics['weighted_f1']:.4f} ({weighted_f1_diff:+.4f})")
print(f"  Suspicious Recall: {test_metrics['per_class']['suspicious']['recall']:.4f} vs {champion_metrics['per_class']['suspicious']['recall']:.4f} ({suspicious_recall_diff:+.4f})")
print(f"  Super-Suspicious Recall: {test_metrics['per_class']['super_suspicious']['recall']:.4f} vs {champion_metrics['per_class']['super_suspicious']['recall']:.4f} ({super_suspicious_recall_diff:+.4f})")
print(f"  Suspicious FN: {test_metrics['suspicious_false_negatives']} vs {champion_metrics['false_negatives'][label_encoder.transform(['suspicious'])[0]]} ({suspicious_fn_diff:+d})")
print(f"  Super-Suspicious FN: {test_metrics['super_suspicious_false_negatives']} vs {champion_metrics['super_suspicious_false_negatives']} ({super_suspicious_fn_diff:+d})")
print()

# ============================================================================
# VERDICT
# ============================================================================

print("=" * 80)
print("VERDICT")
print("=" * 80)
print()

# Determine if improvement is meaningful
if macro_f1_diff >= 0.02 and (suspicious_recall_diff > 0 or super_suspicious_recall_diff > 0):
    verdict = "NEW MODEL BETTER - PROMOTE"
    verdict_reason = f"New model shows meaningful improvement in Macro F1 ({macro_f1_diff:+.4f}) and minority-class recall."
elif macro_f1_diff >= 0.01:
    verdict = "NEW MODEL SLIGHTLY BETTER - NO PROMOTION"
    verdict_reason = f"New model shows modest improvement in Macro F1 ({macro_f1_diff:+.4f}) but does not meet 2% threshold."
elif macro_f1_diff <= -0.02:
    verdict = "NEW MODEL WORSE - KEEP CHAMPION"
    verdict_reason = f"New model performs worse in Macro F1 ({macro_f1_diff:+.4f})."
elif abs(macro_f1_diff) < 0.01 and abs(suspicious_recall_diff) < 0.01 and abs(super_suspicious_recall_diff) < 0.01:
    verdict = "STATISTICALLY/PRACTICALLY SIMILAR - KEEP CHAMPION"
    verdict_reason = f"New model performs similarly to champion across all metrics (Macro F1 diff: {macro_f1_diff:+.4f})."
else:
    verdict = "MIXED RESULTS - KEEP CHAMPION"
    verdict_reason = f"New model shows mixed results with trade-offs between metrics."

print(f"Best configuration: {best_config_name}")
print(f"Verdict: {verdict}")
print(f"Reason: {verdict_reason}")
print()

# ============================================================================
# SAVE RESULTS
# ============================================================================

results = {
    "timestamp": datetime.now().isoformat(),
    "experiment_type": "Stage 17: Controlled Hyperparameter Experiment",
    "total_features": len(feature_names),
    "feature_names": feature_names,
    "train_samples": len(X_train),
    "test_samples": len(X_test),
    "train_customers": len(train_customers),
    "test_customers": len(test_customers),
    "customer_overlap": len(train_customers & test_customers),
    "hyperparameter_configs": [
        {
            'name': r['config']['name'],
            'hp': r['hp'],
            'cv_mean_macro_f1': r['cv_mean_macro_f1'],
            'cv_std_macro_f1': r['cv_std_macro_f1'],
            'cv_scores': r['cv_scores'].tolist()
        }
        for r in cv_results
    ],
    "best_config": {
        'name': best_config_name,
        'hp': best_hp,
        'cv_mean_macro_f1': best_cv_result['cv_mean_macro_f1'],
        'cv_std_macro_f1': best_cv_result['cv_std_macro_f1']
    },
    "test_metrics": {
        'accuracy': test_metrics['accuracy'],
        'macro_f1': test_metrics['macro_f1'],
        'weighted_f1': test_metrics['weighted_f1'],
        'per_class': test_metrics['per_class'],
        'confusion_matrix': test_metrics['confusion_matrix'].tolist(),
        'suspicious_false_negatives': test_metrics['suspicious_false_negatives'],
        'super_suspicious_false_negatives': test_metrics['super_suspicious_false_negatives']
    },
    "champion": {
        'config': champion_config,
        'test_metrics': champion_metrics
    },
    "comparison": {
        'accuracy_diff': accuracy_diff,
        'macro_f1_diff': macro_f1_diff,
        'weighted_f1_diff': weighted_f1_diff,
        'suspicious_recall_diff': suspicious_recall_diff,
        'super_suspicious_recall_diff': super_suspicious_recall_diff,
        'suspicious_false_negatives_diff': suspicious_fn_diff,
        'super_suspicious_false_negatives_diff': super_suspicious_fn_diff
    },
    "verdict": verdict,
    "verdict_reason": verdict_reason
}

with open('ml_stage17_hyperparameter_experiment_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("=" * 80)
print("STAGE 17 HYPERPARAMETER EXPERIMENT COMPLETE")
print("=" * 80)
print("Results saved to ml_stage17_hyperparameter_experiment_results.json")
