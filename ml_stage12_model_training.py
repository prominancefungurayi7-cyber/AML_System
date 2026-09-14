"""
STAGE 12: MODEL TRAINING

Trains models using Stage 6 methodology on both splits:
1. PRIMARY: Customer-level holdout (unseen-customer generalization)
2. SECONDARY: Chronological transaction split (temporal generalization)

Models:
- Majority Class baseline
- Logistic Regression
- Random Forest
- Gradient Boosting
"""

import json
import csv
import numpy as np
from datetime import datetime
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
from collections import Counter

print("=" * 80)
print("STAGE 12: MODEL TRAINING")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================================
# LOAD SPLIT DATA
# ============================================================================

print("Loading split data...")
with open('ml_stage12_primary_split.json', 'r') as f:
    primary_split = json.load(f)

with open('ml_stage12_secondary_split.json', 'r') as f:
    secondary_split = json.load(f)

with open('ml_stage11_features.csv', 'r') as f:
    reader = csv.DictReader(f)
    all_features = list(reader)

with open('ml_stage11_ground_truth.json', 'r') as f:
    all_labels = json.load(f)

print(f"Primary split: {len(primary_split['train_indices'])} train, {len(primary_split['test_indices'])} test")
print(f"Secondary split: {len(secondary_split['train_indices'])} train, {len(secondary_split['test_indices'])} test")
print()

import csv

# ============================================================================
# PREPARE DATA
# ============================================================================

def prepare_data(split_data):
    """Prepare feature matrices and label vectors for a split."""
    train_indices = split_data['train_indices']
    test_indices = split_data['test_indices']
    
    # Get features
    train_features = [all_features[i] for i in train_indices]
    test_features = [all_features[i] for i in test_indices]
    
    # Get labels
    train_labels = [all_labels[i]['ground_truth_label'] for i in train_indices]
    test_labels = [all_labels[i]['ground_truth_label'] for i in test_indices]
    
    # Convert to numpy arrays
    feature_names = list(all_features[0].keys())
    X_train = np.array([[float(tx[fn]) for fn in feature_names] for tx in train_features])
    X_test = np.array([[float(tx[fn]) for fn in feature_names] for tx in test_features])
    
    # Encode labels
    le = LabelEncoder()
    le.fit(train_labels + test_labels)
    y_train = le.transform(train_labels)
    y_test = le.transform(test_labels)
    
    return X_train, X_test, y_train, y_test, le, feature_names

print("Preparing data for primary split...")
X_train_primary, X_test_primary, y_train_primary, y_test_primary, le_primary, feature_names = prepare_data(primary_split)
print(f"Primary: X_train={X_train_primary.shape}, X_test={X_test_primary.shape}")

print("Preparing data for secondary split...")
X_train_secondary, X_test_secondary, y_train_secondary, y_test_secondary, le_secondary, feature_names = prepare_data(secondary_split)
print(f"Secondary: X_train={X_train_secondary.shape}, X_test={X_test_secondary.shape}")
print()

# ============================================================================
# TRAIN AND EVALUATE MODELS
# ============================================================================

def train_and_evaluate(X_train, X_test, y_train, y_test, split_name):
    """Train and evaluate all models on a split."""
    print(f"=" * 80)
    print(f"TRAINING ON {split_name}")
    print("-" * 80)
    
    # Scale features (fit on training only)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    results = {}
    
    # 1. Majority Class Baseline
    print("\n1. Majority Class Baseline")
    class_counts = Counter(y_train)
    majority_class = class_counts.most_common(1)[0][0]
    y_pred_majority = np.full(len(y_test), majority_class)
    
    results['majority_baseline'] = {
        'accuracy': accuracy_score(y_test, y_pred_majority),
        'macro_f1': f1_score(y_test, y_pred_majority, average='macro'),
        'weighted_f1': f1_score(y_test, y_pred_majority, average='weighted'),
        'confusion_matrix': confusion_matrix(y_test, y_pred_majority).tolist(),
        'predictions': y_pred_majority.tolist()
    }
    print(f"  Accuracy: {results['majority_baseline']['accuracy']:.4f}")
    print(f"  Macro F1: {results['majority_baseline']['macro_f1']:.4f}")
    
    # 2. Logistic Regression
    print("\n2. Logistic Regression")
    lr = LogisticRegression(max_iter=1000, random_state=42)
    lr.fit(X_train_scaled, y_train)
    y_pred_lr = lr.predict(X_test_scaled)
    y_pred_lr_train = lr.predict(X_train_scaled)
    
    results['logistic_regression'] = {
        'accuracy': accuracy_score(y_test, y_pred_lr),
        'macro_f1': f1_score(y_test, y_pred_lr, average='macro'),
        'weighted_f1': f1_score(y_test, y_pred_lr, average='weighted'),
        'train_accuracy': accuracy_score(y_train, y_pred_lr_train),
        'train_macro_f1': f1_score(y_train, y_pred_lr_train, average='macro'),
        'confusion_matrix': confusion_matrix(y_test, y_pred_lr).tolist(),
        'predictions': y_pred_lr.tolist()
    }
    print(f"  Test Accuracy: {results['logistic_regression']['accuracy']:.4f}")
    print(f"  Test Macro F1: {results['logistic_regression']['macro_f1']:.4f}")
    print(f"  Train Accuracy: {results['logistic_regression']['train_accuracy']:.4f}")
    print(f"  Train Macro F1: {results['logistic_regression']['train_macro_f1']:.4f}")
    
    # 3. Random Forest
    print("\n3. Random Forest")
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)
    y_pred_rf_train = rf.predict(X_train)
    
    results['random_forest'] = {
        'accuracy': accuracy_score(y_test, y_pred_rf),
        'macro_f1': f1_score(y_test, y_pred_rf, average='macro'),
        'weighted_f1': f1_score(y_test, y_pred_rf, average='weighted'),
        'train_accuracy': accuracy_score(y_train, y_pred_rf_train),
        'train_macro_f1': f1_score(y_train, y_pred_rf_train, average='macro'),
        'confusion_matrix': confusion_matrix(y_test, y_pred_rf).tolist(),
        'predictions': y_pred_rf.tolist(),
        'feature_importance': rf.feature_importances_.tolist()
    }
    print(f"  Test Accuracy: {results['random_forest']['accuracy']:.4f}")
    print(f"  Test Macro F1: {results['random_forest']['macro_f1']:.4f}")
    print(f"  Train Accuracy: {results['random_forest']['train_accuracy']:.4f}")
    print(f"  Train Macro F1: {results['random_forest']['train_macro_f1']:.4f}")
    
    # 4. Gradient Boosting
    print("\n4. Gradient Boosting")
    gb = GradientBoostingClassifier(n_estimators=100, random_state=42)
    gb.fit(X_train, y_train)
    y_pred_gb = gb.predict(X_test)
    y_pred_gb_train = gb.predict(X_train)
    
    results['gradient_boosting'] = {
        'accuracy': accuracy_score(y_test, y_pred_gb),
        'macro_f1': f1_score(y_test, y_pred_gb, average='macro'),
        'weighted_f1': f1_score(y_test, y_pred_gb, average='weighted'),
        'train_accuracy': accuracy_score(y_train, y_pred_gb_train),
        'train_macro_f1': f1_score(y_train, y_pred_gb_train, average='macro'),
        'confusion_matrix': confusion_matrix(y_test, y_pred_gb).tolist(),
        'predictions': y_pred_gb.tolist(),
        'feature_importance': gb.feature_importances_.tolist()
    }
    print(f"  Test Accuracy: {results['gradient_boosting']['accuracy']:.4f}")
    print(f"  Test Macro F1: {results['gradient_boosting']['macro_f1']:.4f}")
    print(f"  Train Accuracy: {results['gradient_boosting']['train_accuracy']:.4f}")
    print(f"  Train Macro F1: {results['gradient_boosting']['train_macro_f1']:.4f}")
    
    return results

# Train on primary split
print("\n" + "=" * 80)
primary_results = train_and_evaluate(X_train_primary, X_test_primary, y_train_primary, y_test_primary, "PRIMARY (CUSTOMER-DISJOINT)")

# Train on secondary split
print("\n" + "=" * 80)
secondary_results = train_and_evaluate(X_train_secondary, X_test_secondary, y_train_secondary, y_test_secondary, "SECONDARY (CHRONOLOGICAL)")

# ============================================================================
# DETAILED CLASS-WISE METRICS
# ============================================================================

def get_class_wise_metrics(y_true, y_pred, le):
    """Calculate class-wise precision, recall, F1."""
    class_names = le.classes_
    report = classification_report(y_true, y_pred, target_names=class_names, output_dict=True)
    
    metrics = {}
    for class_name in class_names:
        metrics[class_name] = {
            'precision': report[class_name]['precision'],
            'recall': report[class_name]['recall'],
            'f1': report[class_name]['f1-score'],
            'support': report[class_name]['support']
        }
    
    return metrics

print("\n" + "=" * 80)
print("CLASS-WISE METRICS")
print("-" * 80)

print("\nPRIMARY SPLIT (Customer-Disjoint):")
for model_name in ['logistic_regression', 'random_forest', 'gradient_boosting']:
    print(f"\n{model_name.upper()}:")
    y_pred = np.array(primary_results[model_name]['predictions'])
    class_metrics = get_class_wise_metrics(y_test_primary, y_pred, le_primary)
    for class_name in ['normal', 'suspicious', 'super_suspicious']:
        if class_name in class_metrics:
            metrics = class_metrics[class_name]
            print(f"  {class_name}: P={metrics['precision']:.4f}, R={metrics['recall']:.4f}, F1={metrics['f1']:.4f}")

print("\nSECONDARY SPLIT (Chronological):")
for model_name in ['logistic_regression', 'random_forest', 'gradient_boosting']:
    print(f"\n{model_name.upper()}:")
    y_pred = np.array(secondary_results[model_name]['predictions'])
    class_metrics = get_class_wise_metrics(y_test_secondary, y_pred, le_secondary)
    for class_name in ['normal', 'suspicious', 'super_suspicious']:
        if class_name in class_metrics:
            metrics = class_metrics[class_name]
            print(f"  {class_name}: P={metrics['precision']:.4f}, R={metrics['recall']:.4f}, F1={metrics['f1']:.4f}")

# ============================================================================
# SAVE RESULTS
# ============================================================================

all_results = {
    "timestamp": datetime.now().isoformat(),
    "primary_split": {
        "split_type": "customer_disjoint",
        "train_customers": 160,
        "test_customers": 40,
        "customer_overlap": 0,
        "results": primary_results
    },
    "secondary_split": {
        "split_type": "chronological",
        "train_customers": 200,
        "test_customers": 200,
        "customer_overlap": 200,
        "results": secondary_results
    },
    "feature_names": feature_names
}

with open('ml_stage12_model_results.json', 'w') as f:
    json.dump(all_results, f, indent=2)

print("\n" + "=" * 80)
print("MODEL TRAINING COMPLETE")
print("=" * 80)
print("Results saved to ml_stage12_model_results.json")
