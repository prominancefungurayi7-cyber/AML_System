"""
STAGE 19: SMOTE + XGBoost EXPERIMENT

Test whether XGBoost + SMOTE can achieve better generalization than Gradient Boosting + SMOTE
and potentially outperform the frozen Gradient Boosting champion.
"""

import csv
import json
import numpy as np
from datetime import datetime
from collections import Counter
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score, StratifiedKFold
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier

print("=" * 80)
print("STAGE 19: SMOTE + XGBoost EXPERIMENT")
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
# PRE-SMOTE CLASS DISTRIBUTION
# ============================================================================

print("=" * 80)
print("PRE-SMOTE CLASS DISTRIBUTION (TRAINING DATA)")
print("=" * 80)
print()

pre_smote_distribution = Counter(y_train)
for class_name in label_encoder.classes_:
    count = pre_smote_distribution[class_name]
    percentage = (count / len(y_train)) * 100
    print(f"  {class_name}: {count} ({percentage:.2f}%)")
print()

# ============================================================================
# DEFINE SMOTE CONFIGURATIONS
# ============================================================================

print("Defining SMOTE configurations...")
print()

# Get class indices and counts for SMOTE sampling_strategy
normal_idx = label_encoder.transform(['normal'])[0]
super_suspicious_idx = label_encoder.transform(['super_suspicious'])[0]
suspicious_idx = label_encoder.transform(['suspicious'])[0]

# Get class counts
normal_count = pre_smote_distribution['normal']
super_suspicious_count = pre_smote_distribution['super_suspicious']
suspicious_count = pre_smote_distribution['suspicious']

smote_configs = [
    {
        'name': 'No_SMOTE_Baseline',
        'sampling_strategy': None,  # No SMOTE
        'random_state': 42
    },
    {
        'name': 'Balanced_SMOTE',
        'sampling_strategy': 'auto',  # Resample all classes to majority
        'random_state': 42,
        'k_neighbors': 5
    },
    {
        'name': 'Mild_SMOTE',
        'sampling_strategy': {
            normal_idx: normal_count,  # Keep normal as is
            suspicious_idx: int(normal_count * 0.5),  # Oversample suspicious to 50% of normal
            super_suspicious_idx: int(normal_count * 0.5)  # Oversample super_suspicious to 50% of normal
        },
        'random_state': 42,
        'k_neighbors': 5
    },
    {
        'name': 'Conservative_SMOTE',
        'sampling_strategy': {
            normal_idx: normal_count,  # Keep normal as is
            suspicious_idx: int(normal_count * 0.3),  # Oversample suspicious to 30% of normal
            super_suspicious_idx: int(normal_count * 0.3)  # Oversample super_suspicious to 30% of normal
        },
        'random_state': 42,
        'k_neighbors': 5
    }
]

for config in smote_configs:
    print(f"  {config['name']}:")
    print(f"    sampling_strategy: {config['sampling_strategy']}")
    if 'k_neighbors' in config:
        print(f"    k_neighbors: {config['k_neighbors']}")
print()

# ============================================================================
# XGBoost CONFIGURATION
# ============================================================================

xgb_config = {
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
    'eval_metric': 'mlogloss',
    'objective': 'multi:softprob',
    'num_class': 3
}

print("XGBoost configuration:")
for key, value in xgb_config.items():
    print(f"  {key}: {value}")
print()

# ============================================================================
# APPLY SMOTE AND TRAIN MODELS
# ============================================================================

print("Applying SMOTE and training XGBoost models...")
print()

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_results = []

for config in smote_configs:
    print(f"{'='*80}")
    print(f"CONFIG: {config['name']}")
    print(f"{'='*80}")
    
    # Apply SMOTE to training data only
    if config['sampling_strategy'] is None:
        # No SMOTE
        X_train_resampled = X_train
        y_train_resampled = y_train_encoded
        print("No SMOTE applied")
    else:
        # Apply SMOTE
        smote = SMOTE(
            sampling_strategy=config['sampling_strategy'],
            random_state=config['random_state'],
            k_neighbors=config.get('k_neighbors', 5)
        )
        X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train_encoded)
        print(f"SMOTE applied")
    
    # Post-SMOTE class distribution
    post_smote_distribution = Counter(label_encoder.inverse_transform(y_train_resampled))
    print("Post-SMOTE class distribution:")
    for class_name in label_encoder.classes_:
        count = post_smote_distribution[class_name]
        percentage = (count / len(y_train_resampled)) * 100
        print(f"  {class_name}: {count} ({percentage:.2f}%)")
    
    print(f"Total training samples after SMOTE: {len(X_train_resampled)}")
    print()
    
    # Cross-validation on resampled training data
    xgb = XGBClassifier(**xgb_config)
    
    # For SMOTE data, we need to use the resampled data for CV
    # But we must ensure we don't leak test data
    cv_macro_f1_scores = cross_val_score(xgb, X_train_resampled, y_train_resampled, cv=cv, scoring='f1_macro')
    
    cv_mean_macro_f1 = cv_macro_f1_scores.mean()
    cv_std_macro_f1 = cv_macro_f1_scores.std()
    
    print(f"CV Macro F1 scores: {cv_macro_f1_scores}")
    print(f"CV Mean Macro F1: {cv_mean_macro_f1:.4f}")
    print(f"CV Std Macro F1: {cv_std_macro_f1:.4f}")
    print()
    
    cv_results.append({
        'config': config,
        'post_smote_distribution': dict(post_smote_distribution),
        'total_samples': len(X_train_resampled),
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
best_config = best_cv_result['config']

# Apply SMOTE to full training data
if best_config['sampling_strategy'] is None:
    X_train_final = X_train
    y_train_final = y_train_encoded
else:
    smote = SMOTE(
        sampling_strategy=best_config['sampling_strategy'],
        random_state=best_config['random_state'],
        k_neighbors=best_config.get('k_neighbors', 5)
    )
    X_train_final, y_train_final = smote.fit_resample(X_train, y_train_encoded)

print(f"Training samples: {len(X_train_final)}")

best_model = XGBClassifier(**xgb_config)
best_model.fit(X_train_final, y_train_final)

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
# LOAD STAGE 18 SMOTE RESULTS FOR COMPARISON
# ============================================================================

print("=" * 80)
print("LOADING STAGE 18 SMOTE RESULTS FOR COMPARISON")
print("=" * 80)
print()

with open('ml_stage18_smote_experiment_results.json', 'r') as f:
    stage18_results = json.load(f)

stage18_metrics = stage18_results['test_metrics']
stage18_config = stage18_results['best_config']

print("Stage 18 Balanced_SMOTE + Gradient Boosting:")
print(f"  Config: {stage18_config['name']}")
print(f"  Test Accuracy: {stage18_metrics['accuracy']:.4f}")
print(f"  Test Macro F1: {stage18_metrics['macro_f1']:.4f}")
print(f"  Test Weighted F1: {stage18_metrics['weighted_f1']:.4f}")
print(f"  Suspicious Recall: {stage18_metrics['per_class']['suspicious']['recall']:.4f}")
print(f"  Super-Suspicious Recall: {stage18_metrics['per_class']['super_suspicious']['recall']:.4f}")
print(f"  Suspicious False Negatives: {stage18_metrics['suspicious_false_negatives']}")
print(f"  Super-Suspicious False Negatives: {stage18_metrics['super_suspicious_false_negatives']}")
print()

# ============================================================================
# COMPARISON WITH CHAMPION AND STAGE 18
# ============================================================================

print("=" * 80)
print("COMPARISON WITH CHAMPION AND STAGE 18")
print("=" * 80)
print()

accuracy_diff_champion = test_metrics['accuracy'] - champion_metrics['accuracy']
macro_f1_diff_champion = test_metrics['macro_f1'] - champion_metrics['macro_f1']
weighted_f1_diff_champion = test_metrics['weighted_f1'] - champion_metrics['weighted_f1']
suspicious_recall_diff_champion = test_metrics['per_class']['suspicious']['recall'] - champion_metrics['per_class']['suspicious']['recall']
super_suspicious_recall_diff_champion = test_metrics['per_class']['super_suspicious']['recall'] - champion_metrics['per_class']['super_suspicious']['recall']
suspicious_fn_diff_champion = test_metrics['suspicious_false_negatives'] - champion_metrics['false_negatives'][label_encoder.transform(['suspicious'])[0]]
super_suspicious_fn_diff_champion = test_metrics['super_suspicious_false_negatives'] - champion_metrics['super_suspicious_false_negatives']

accuracy_diff_stage18 = test_metrics['accuracy'] - stage18_metrics['accuracy']
macro_f1_diff_stage18 = test_metrics['macro_f1'] - stage18_metrics['macro_f1']
weighted_f1_diff_stage18 = test_metrics['weighted_f1'] - stage18_metrics['weighted_f1']
suspicious_recall_diff_stage18 = test_metrics['per_class']['suspicious']['recall'] - stage18_metrics['per_class']['suspicious']['recall']
super_suspicious_recall_diff_stage18 = test_metrics['per_class']['super_suspicious']['recall'] - stage18_metrics['per_class']['super_suspicious']['recall']
suspicious_fn_diff_stage18 = test_metrics['suspicious_false_negatives'] - stage18_metrics['suspicious_false_negatives']
super_suspicious_fn_diff_stage18 = test_metrics['super_suspicious_false_negatives'] - stage18_metrics['super_suspicious_false_negatives']

print(f"{best_config_name} vs Champion:")
print(f"  Accuracy: {test_metrics['accuracy']:.4f} vs {champion_metrics['accuracy']:.4f} ({accuracy_diff_champion:+.4f})")
print(f"  Macro F1: {test_metrics['macro_f1']:.4f} vs {champion_metrics['macro_f1']:.4f} ({macro_f1_diff_champion:+.4f})")
print(f"  Weighted F1: {test_metrics['weighted_f1']:.4f} vs {champion_metrics['weighted_f1']:.4f} ({weighted_f1_diff_champion:+.4f})")
print(f"  Suspicious Recall: {test_metrics['per_class']['suspicious']['recall']:.4f} vs {champion_metrics['per_class']['suspicious']['recall']:.4f} ({suspicious_recall_diff_champion:+.4f})")
print(f"  Super-Suspicious Recall: {test_metrics['per_class']['super_suspicious']['recall']:.4f} vs {champion_metrics['per_class']['super_suspicious']['recall']:.4f} ({super_suspicious_recall_diff_champion:+.4f})")
print(f"  Suspicious FN: {test_metrics['suspicious_false_negatives']} vs {champion_metrics['false_negatives'][label_encoder.transform(['suspicious'])[0]]} ({suspicious_fn_diff_champion:+d})")
print(f"  Super-Suspicious FN: {test_metrics['super_suspicious_false_negatives']} vs {champion_metrics['super_suspicious_false_negatives']} ({super_suspicious_fn_diff_champion:+d})")
print()

print(f"{best_config_name} vs Stage 18 Balanced_SMOTE + GB:")
print(f"  Accuracy: {test_metrics['accuracy']:.4f} vs {stage18_metrics['accuracy']:.4f} ({accuracy_diff_stage18:+.4f})")
print(f"  Macro F1: {test_metrics['macro_f1']:.4f} vs {stage18_metrics['macro_f1']:.4f} ({macro_f1_diff_stage18:+.4f})")
print(f"  Weighted F1: {test_metrics['weighted_f1']:.4f} vs {stage18_metrics['weighted_f1']:.4f} ({weighted_f1_diff_stage18:+.4f})")
print(f"  Suspicious Recall: {test_metrics['per_class']['suspicious']['recall']:.4f} vs {stage18_metrics['per_class']['suspicious']['recall']:.4f} ({suspicious_recall_diff_stage18:+.4f})")
print(f"  Super-Suspicious Recall: {test_metrics['per_class']['super_suspicious']['recall']:.4f} vs {stage18_metrics['per_class']['super_suspicious']['recall']:.4f} ({super_suspicious_recall_diff_stage18:+.4f})")
print(f"  Suspicious FN: {test_metrics['suspicious_false_negatives']} vs {stage18_metrics['suspicious_false_negatives']} ({suspicious_fn_diff_stage18:+d})")
print(f"  Super-Suspicious FN: {test_metrics['super_suspicious_false_negatives']} vs {stage18_metrics['super_suspicious_false_negatives']} ({super_suspicious_fn_diff_stage18:+d})")
print()

# ============================================================================
# CV-TO-TEST GAP ANALYSIS
# ============================================================================

cv_test_gap = best_cv_result['cv_mean_macro_f1'] - test_metrics['macro_f1']

print(f"CV-to-Test Gap Analysis:")
print(f"  CV Macro F1: {best_cv_result['cv_mean_macro_f1']:.4f}")
print(f"  Test Macro F1: {test_metrics['macro_f1']:.4f}")
print(f"  CV-Test Gap: {cv_test_gap:.4f}")
print()

# ============================================================================
# VERDICT
# ============================================================================

print("=" * 80)
print("VERDICT")
print("=" * 80)
print()

# Determine if improvement is meaningful
if macro_f1_diff_champion >= 0.02 and (suspicious_recall_diff_champion > 0 or super_suspicious_recall_diff_champion > 0):
    verdict = "NEW MODEL BETTER - PROMOTE"
    verdict_reason = f"New model shows meaningful improvement in Macro F1 ({macro_f1_diff_champion:+.4f}) and minority-class recall."
elif macro_f1_diff_champion >= 0.01:
    verdict = "NEW MODEL SLIGHTLY BETTER - NO PROMOTION"
    verdict_reason = f"New model shows modest improvement in Macro F1 ({macro_f1_diff_champion:+.4f}) but does not meet 2% threshold."
elif macro_f1_diff_champion <= -0.02:
    verdict = "NEW MODEL WORSE - KEEP CHAMPION"
    verdict_reason = f"New model performs worse in Macro F1 ({macro_f1_diff_champion:+.4f})."
elif abs(macro_f1_diff_champion) < 0.01 and abs(suspicious_recall_diff_champion) < 0.01 and abs(super_suspicious_recall_diff_champion) < 0.01:
    verdict = "STATISTICALLY/PRACTICALLY SIMILAR - KEEP CHAMPION"
    verdict_reason = f"New model performs similarly to champion across all metrics (Macro F1 diff: {macro_f1_diff_champion:+.4f})."
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
    "experiment_type": "Stage 19: SMOTE + XGBoost Experiment",
    "total_features": len(feature_names),
    "feature_names": feature_names,
    "train_samples": len(X_train),
    "test_samples": len(X_test),
    "train_customers": len(train_customers),
    "test_customers": len(test_customers),
    "customer_overlap": len(train_customers & test_customers),
    "pre_smote_distribution": dict(pre_smote_distribution),
    "smote_configs": [
        {
            'name': r['config']['name'],
            'sampling_strategy': {str(k): v for k, v in r['config']['sampling_strategy'].items()} if isinstance(r['config']['sampling_strategy'], dict) else r['config']['sampling_strategy'],
            'post_smote_distribution': r['post_smote_distribution'],
            'total_samples': r['total_samples'],
            'cv_mean_macro_f1': r['cv_mean_macro_f1'],
            'cv_std_macro_f1': r['cv_std_macro_f1'],
            'cv_scores': r['cv_scores'].tolist()
        }
        for r in cv_results
    ],
    "best_config": {
        'name': best_config_name,
        'sampling_strategy': {str(k): v for k, v in best_config['sampling_strategy'].items()} if isinstance(best_config['sampling_strategy'], dict) else best_config['sampling_strategy'],
        'post_smote_distribution': best_cv_result['post_smote_distribution'],
        'total_samples': best_cv_result['total_samples'],
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
    "stage18": {
        'config': stage18_config,
        'test_metrics': stage18_metrics
    },
    "comparison_champion": {
        'accuracy_diff': accuracy_diff_champion,
        'macro_f1_diff': macro_f1_diff_champion,
        'weighted_f1_diff': weighted_f1_diff_champion,
        'suspicious_recall_diff': suspicious_recall_diff_champion,
        'super_suspicious_recall_diff': super_suspicious_recall_diff_champion,
        'suspicious_false_negatives_diff': suspicious_fn_diff_champion,
        'super_suspicious_false_negatives_diff': super_suspicious_fn_diff_champion
    },
    "comparison_stage18": {
        'accuracy_diff': accuracy_diff_stage18,
        'macro_f1_diff': macro_f1_diff_stage18,
        'weighted_f1_diff': weighted_f1_diff_stage18,
        'suspicious_recall_diff': suspicious_recall_diff_stage18,
        'super_suspicious_recall_diff': super_suspicious_recall_diff_stage18,
        'suspicious_false_negatives_diff': suspicious_fn_diff_stage18,
        'super_suspicious_false_negatives_diff': super_suspicious_fn_diff_stage18
    },
    "cv_test_gap": cv_test_gap,
    "verdict": verdict,
    "verdict_reason": verdict_reason
}

with open('ml_stage19_smote_xgboost_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("=" * 80)
print("STAGE 19 SMOTE + XGBoost EXPERIMENT COMPLETE")
print("=" * 80)
print("Results saved to ml_stage19_smote_xgboost_results.json")
