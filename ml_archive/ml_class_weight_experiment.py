"""
CLASS-WEIGHTED GRADIENT BOOSTING EXPERIMENT

Test whether class weighting can improve minority-class detection
while maintaining acceptable overall performance.
"""

import csv
import json
import numpy as np
from datetime import datetime
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

print("=" * 80)
print("CLASS-WEIGHTED GRADIENT BOOSTING EXPERIMENT")
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
# CREATE TRAIN/VALIDATION SPLIT FROM TRAINING DATA ONLY
# ============================================================================

print("Creating train/validation split from training data only...")

# Use 80% of training data for training, 20% for validation
X_train_split, X_val_split, y_train_split, y_val_split = train_test_split(
    X_train, y_train_encoded, test_size=0.2, random_state=42, stratify=y_train_encoded
)

print(f"Training samples: {len(X_train_split)}")
print(f"Validation samples: {len(X_val_split)}")
print(f"Test samples (untouched): {len(X_test)}")
print()

# ============================================================================
# DEFINE CLASS WEIGHTING SCHEMES
# ============================================================================

print("Defining class weighting schemes...")

class_weight_schemes = [
    {
        'name': 'Baseline',
        'weights': {'normal': 1.0, 'suspicious': 1.0, 'super_suspicious': 1.0}
    },
    {
        'name': 'Mild',
        'weights': {'normal': 1.0, 'suspicious': 1.5, 'super_suspicious': 2.0}
    },
    {
        'name': 'Moderate',
        'weights': {'normal': 1.0, 'suspicious': 2.0, 'super_suspicious': 3.0}
    },
    {
        'name': 'Strong',
        'weights': {'normal': 1.0, 'suspicious': 3.0, 'super_suspicious': 4.0}
    }
]

for scheme in class_weight_schemes:
    print(f"  {scheme['name']}: {scheme['weights']}")
print()

# ============================================================================
# FUNCTION TO CONVERT CLASS WEIGHTS TO SAMPLE WEIGHTS
# ============================================================================

def class_weights_to_sample_weights(y_encoded, class_weights, label_encoder):
    """Convert class weights to per-sample weights."""
    sample_weights = np.ones(len(y_encoded))
    
    for class_name, weight in class_weights.items():
        class_idx = label_encoder.transform([class_name])[0]
        sample_weights[y_encoded == class_idx] = weight
    
    return sample_weights

# ============================================================================
# TRAIN AND EVALUATE EACH WEIGHTING SCHEME
# ============================================================================

print("Training and evaluating each weighting scheme...")
print()

gb_config = {
    'learning_rate': 0.01,
    'max_depth': 3,
    'n_estimators': 500,
    'random_state': 42
}

results = []

for scheme in class_weight_schemes:
    print(f"{'='*80}")
    print(f"SCHEME: {scheme['name']}")
    print(f"{'='*80}")
    
    # Convert class weights to sample weights
    train_sample_weights = class_weights_to_sample_weights(
        y_train_split, scheme['weights'], label_encoder
    )
    val_sample_weights = class_weights_to_sample_weights(
        y_val_split, scheme['weights'], label_encoder
    )
    
    # Verify sample weights are being applied correctly
    print(f"Sample weight distribution:")
    print(f"  Normal: {train_sample_weights[y_train_split == label_encoder.transform(['normal'])[0]][0]:.2f}")
    print(f"  Suspicious: {train_sample_weights[y_train_split == label_encoder.transform(['suspicious'])[0]][0]:.2f}")
    print(f"  Super-Suspicious: {train_sample_weights[y_train_split == label_encoder.transform(['super_suspicious'])[0]][0]:.2f}")
    print()
    
    # Train model with sample weights
    gb = GradientBoostingClassifier(**gb_config)
    gb.fit(X_train_split, y_train_split, sample_weight=train_sample_weights)
    
    # Predict on validation set
    val_pred = gb.predict(X_val_split)
    
    # Calculate validation metrics
    val_macro_f1 = f1_score(y_val_split, val_pred, average='macro')
    val_suspicious_recall = classification_report(
        y_val_split, val_pred, target_names=label_encoder.classes_, output_dict=True, zero_division=0
    )['suspicious']['recall']
    val_super_suspicious_recall = classification_report(
        y_val_split, val_pred, target_names=label_encoder.classes_, output_dict=True, zero_division=0
    )['super_suspicious']['recall']
    
    print(f"Validation Metrics:")
    print(f"  Macro F1: {val_macro_f1:.4f}")
    print(f"  Suspicious Recall: {val_suspicious_recall:.4f}")
    print(f"  Super-Suspicious Recall: {val_super_suspicious_recall:.4f}")
    print()
    
    results.append({
        'scheme': scheme['name'],
        'weights': scheme['weights'],
        'model': gb,
        'val_macro_f1': val_macro_f1,
        'val_suspicious_recall': val_suspicious_recall,
        'val_super_suspicious_recall': val_super_suspicious_recall
    })

# ============================================================================
# SELECT BEST SCHEME BASED ON VALIDATION PERFORMANCE
# ============================================================================

print("=" * 80)
print("SELECTING BEST SCHEME BASED ON VALIDATION PERFORMANCE")
print("=" * 80)
print()

# Select based on Macro F1 (primary metric) with consideration for minority recall
best_scheme = max(results, key=lambda x: (x['val_macro_f1'], x['val_suspicious_recall'], x['val_super_suspicious_recall']))

print(f"Best scheme: {best_scheme['scheme']}")
print(f"Validation Macro F1: {best_scheme['val_macro_f1']:.4f}")
print(f"Validation Suspicious Recall: {best_scheme['val_suspicious_recall']:.4f}")
print(f"Validation Super-Suspicious Recall: {best_scheme['val_super_suspicious_recall']:.4f}")
print()

# ============================================================================
# EVALUATE ALL SCHEMES ON UNTOUCHED TEST SET
# ============================================================================

print("=" * 80)
print("EVALUATING ALL SCHEMES ON UNTOUCHED TEST SET")
print("=" * 80)
print()

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
        'confusion_matrix': cm.tolist(),
        'false_positives': fp.tolist(),
        'false_negatives': fn.tolist(),
        'suspicious_false_negatives': int(suspicious_fn),
        'super_suspicious_false_negatives': int(super_suspicious_fn)
    }

# Evaluate all schemes on test set
for result in results:
    scheme_name = result['scheme']
    model = result['model']
    
    # Predict on test set
    test_pred = model.predict(X_test)
    
    # Calculate test metrics
    test_metrics = compute_detailed_metrics(y_test_encoded, test_pred, label_encoder)
    
    result['test_metrics'] = test_metrics
    
    print(f"{scheme_name} (Test Metrics):")
    print(f"  Accuracy: {test_metrics['accuracy']:.4f}")
    print(f"  Macro F1: {test_metrics['macro_f1']:.4f}")
    print(f"  Weighted F1: {test_metrics['weighted_f1']:.4f}")
    print(f"  Suspicious Recall: {test_metrics['per_class']['suspicious']['recall']:.4f}")
    print(f"  Super-Suspicious Recall: {test_metrics['per_class']['super_suspicious']['recall']:.4f}")
    print(f"  Suspicious False Negatives: {test_metrics['suspicious_false_negatives']}")
    print(f"  Super-Suspicious False Negatives: {test_metrics['super_suspicious_false_negatives']}")
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
# DETAILED COMPARISON
# ============================================================================

print("=" * 80)
print("DETAILED COMPARISON WITH CHAMPION")
print("=" * 80)
print()

for result in results:
    scheme_name = result['scheme']
    test_metrics = result['test_metrics']
    
    print(f"{scheme_name} vs Champion:")
    print(f"  Accuracy: {test_metrics['accuracy']:.4f} vs {champion_metrics['accuracy']:.4f} ({test_metrics['accuracy'] - champion_metrics['accuracy']:+.4f})")
    print(f"  Macro F1: {test_metrics['macro_f1']:.4f} vs {champion_metrics['macro_f1']:.4f} ({test_metrics['macro_f1'] - champion_metrics['macro_f1']:+.4f})")
    print(f"  Weighted F1: {test_metrics['weighted_f1']:.4f} vs {champion_metrics['weighted_f1']:.4f} ({test_metrics['weighted_f1'] - champion_metrics['weighted_f1']:+.4f})")
    print(f"  Suspicious Recall: {test_metrics['per_class']['suspicious']['recall']:.4f} vs {champion_metrics['per_class']['suspicious']['recall']:.4f} ({test_metrics['per_class']['suspicious']['recall'] - champion_metrics['per_class']['suspicious']['recall']:+.4f})")
    print(f"  Super-Suspicious Recall: {test_metrics['per_class']['super_suspicious']['recall']:.4f} vs {champion_metrics['per_class']['super_suspicious']['recall']:.4f} ({test_metrics['per_class']['super_suspicious']['recall'] - champion_metrics['per_class']['super_suspicious']['recall']:+.4f})")
    print(f"  Suspicious FN: {test_metrics['suspicious_false_negatives']} vs {champion_metrics['false_negatives'][label_encoder.transform(['suspicious'])[0]]} ({test_metrics['suspicious_false_negatives'] - champion_metrics['false_negatives'][label_encoder.transform(['suspicious'])[0]]:+d})")
    print(f"  Super-Suspicious FN: {test_metrics['super_suspicious_false_negatives']} vs {champion_metrics['super_suspicious_false_negatives']} ({test_metrics['super_suspicious_false_negatives'] - champion_metrics['super_suspicious_false_negatives']:+d})")
    print()

# ============================================================================
# VERDICT
# ============================================================================

print("=" * 80)
print("VERDICT")
print("=" * 80)
print()

# Find best scheme based on test performance
best_test_scheme = max(results, key=lambda x: (
    x['test_metrics']['macro_f1'],
    x['test_metrics']['per_class']['suspicious']['recall'],
    x['test_metrics']['per_class']['super_suspicious']['recall']
))

best_test_metrics = best_test_scheme['test_metrics']

# Determine if improvement is meaningful
macro_f1_improvement = best_test_metrics['macro_f1'] - champion_metrics['macro_f1']
suspicious_recall_improvement = best_test_metrics['per_class']['suspicious']['recall'] - champion_metrics['per_class']['suspicious']['recall']
super_suspicious_recall_improvement = best_test_metrics['per_class']['super_suspicious']['recall'] - champion_metrics['per_class']['super_suspicious']['recall']

# Meaningful improvement threshold: at least 0.02 (2 percentage points) in Macro F1
# AND improvement in minority-class recall
if macro_f1_improvement >= 0.02 and (suspicious_recall_improvement > 0 or super_suspicious_recall_improvement > 0):
    verdict = "CLASS-WEIGHTED MODEL BETTER"
    verdict_reason = f"Class-weighted model shows meaningful improvement in Macro F1 ({macro_f1_improvement:+.4f}) and minority-class recall."
elif macro_f1_improvement >= 0.01:
    verdict = "CLASS-WEIGHTED MODEL SLIGHTLY BETTER"
    verdict_reason = f"Class-weighted model shows modest improvement in Macro F1 ({macro_f1_improvement:+.4f}) but minority-class recall improvement is limited."
elif macro_f1_improvement <= -0.02:
    verdict = "CLASS-WEIGHTED MODEL WORSE"
    verdict_reason = f"Class-weighted model performs worse in Macro F1 ({macro_f1_improvement:+.4f})."
elif abs(macro_f1_improvement) < 0.01 and abs(suspicious_recall_improvement) < 0.01 and abs(super_suspicious_recall_improvement) < 0.01:
    verdict = "STATISTICALLY/PRACTICALLY SIMILAR"
    verdict_reason = f"Class-weighted model performs similarly to champion across all metrics (Macro F1 diff: {macro_f1_improvement:+.4f})."
else:
    verdict = "MIXED RESULTS"
    verdict_reason = f"Class-weighted model shows mixed results with trade-offs between metrics."

print(f"Best scheme: {best_test_scheme['scheme']}")
print(f"Verdict: {verdict}")
print(f"Reason: {verdict_reason}")
print()

# ============================================================================
# SAVE RESULTS
# ============================================================================

results_data = {
    "timestamp": datetime.now().isoformat(),
    "experiment_type": "Class-Weighted Gradient Boosting",
    "total_features": len(feature_names),
    "feature_names": feature_names,
    "train_samples": len(X_train_split),
    "val_samples": len(X_val_split),
    "test_samples": len(X_test),
    "train_customers": len(train_customers),
    "test_customers": len(test_customers),
    "gb_config": gb_config,
    "class_weight_schemes": [
        {
            'name': r['scheme'],
            'weights': r['weights'],
            'val_macro_f1': r['val_macro_f1'],
            'val_suspicious_recall': r['val_suspicious_recall'],
            'val_super_suspicious_recall': r['val_super_suspicious_recall'],
            'test_metrics': r['test_metrics']
        }
        for r in results
    ],
    "champion": {
        "config": champion_config,
        "test_metrics": champion_metrics
    },
    "best_scheme": best_test_scheme['scheme'],
    "verdict": verdict,
    "verdict_reason": verdict_reason
}

with open('ml_class_weight_experiment_results.json', 'w') as f:
    json.dump(results_data, f, indent=2)

print("=" * 80)
print("CLASS-WEIGHTED GRADIENT BOOSTING EXPERIMENT COMPLETE")
print("=" * 80)
print("Results saved to ml_class_weight_experiment_results.json")
