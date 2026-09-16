"""
Stage 14: Machine Learning Model Training, Validation, Selection, and Evaluation

Trains and evaluates classical binary classifiers on the frozen Stage 13 feature matrices.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
import random
import warnings
warnings.filterwarnings('ignore')

# ML libraries
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, precision_score, recall_score, 
    f1_score, roc_auc_score, average_precision_score, confusion_matrix,
    classification_report
)
from sklearn.model_selection import ParameterGrid
import pickle

# =============================================================================
# CONFIGURATION
# =============================================================================

DATASET_VERSION = "ecocash_aml_synthetic_100k_v1"
DATA_DIR = Path("data") / DATASET_VERSION
FEATURE_DIR = DATA_DIR / "features"
REPORTS_DIR = Path("reports")
STAGE14_DIR = Path("ml") / "stage14"

# Reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# =============================================================================
# LOAD STAGE 13 MATRICES
# =============================================================================

def load_stage13_matrices():
    """Load and validate Stage 13 feature matrices."""
    print("=" * 80)
    print("STAGE 14: MODEL TRAINING AND EVALUATION")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Dataset Version: {DATASET_VERSION}")
    print()
    
    print("Loading Stage 13 feature matrices...")
    
    # Load matrices
    X_train = np.load(FEATURE_DIR / "X_train.npy")
    y_train = np.load(FEATURE_DIR / "y_train.npy")
    X_val = np.load(FEATURE_DIR / "X_val.npy")
    y_val = np.load(FEATURE_DIR / "y_val.npy")
    X_test = np.load(FEATURE_DIR / "X_test.npy")
    y_test = np.load(FEATURE_DIR / "y_test.npy")
    X_independent = np.load(FEATURE_DIR / "X_independent.npy")
    y_independent = np.load(FEATURE_DIR / "y_independent.npy")
    
    # Load feature names
    with open(FEATURE_DIR / "feature_names.json", 'r') as f:
        feature_names = json.load(f)
    
    print(f"  X_train: {X_train.shape}")
    print(f"  y_train: {y_train.shape}")
    print(f"  X_val: {X_val.shape}")
    print(f"  y_val: {y_val.shape}")
    print(f"  X_test: {X_test.shape}")
    print(f"  y_test: {y_test.shape}")
    print(f"  X_independent: {X_independent.shape}")
    print(f"  y_independent: {y_independent.shape}")
    print(f"  Feature names: {len(feature_names)}")
    print()
    
    return {
        'X_train': X_train, 'y_train': y_train,
        'X_val': X_val, 'y_val': y_val,
        'X_test': X_test, 'y_test': y_test,
        'X_independent': X_independent, 'y_independent': y_independent,
        'feature_names': feature_names
    }

# =============================================================================
# VALIDATE MATRICES
# =============================================================================

def validate_matrices(matrices):
    """Validate matrix shapes and feature order."""
    print("=== Validating Stage 13 Matrices ===")
    
    # Check shapes
    expected_shapes = {
        'X_train': (60000, 30),
        'y_train': (60000,),
        'X_val': (15000, 30),
        'y_val': (15000,),
        'X_test': (15000, 30),
        'y_test': (15000,),
        'X_independent': (10000, 30),
        'y_independent': (10000,)
    }
    
    shape_validation = True
    for name, expected_shape in expected_shapes.items():
        actual_shape = matrices[name].shape
        if actual_shape != expected_shape:
            print(f"  ERROR: {name} shape mismatch: {actual_shape} vs {expected_shape}")
            shape_validation = False
    
    # Check feature count
    feature_count = len(matrices['feature_names'])
    if feature_count != 30:
        print(f"  ERROR: Feature count mismatch: {feature_count} vs 30")
        shape_validation = False
    
    # Check feature uniqueness
    unique_features = len(set(matrices['feature_names']))
    if unique_features != 30:
        print(f"  ERROR: Duplicate features detected: {unique_features} unique vs 30 total")
        shape_validation = False
    
    # Check numerical safety
    nan_count = np.isnan(matrices['X_train']).sum()
    inf_count = np.isinf(matrices['X_train']).sum()
    
    if nan_count > 0 or inf_count > 0:
        print(f"  ERROR: Numerical issues in X_train: NaN={nan_count}, Inf={inf_count}")
        shape_validation = False
    
    # Check class distribution
    train_normal = (matrices['y_train'] == 0).sum()
    train_suspicious = (matrices['y_train'] == 1).sum()
    
    if train_normal != 52800 or train_suspicious != 7200:
        print(f"  ERROR: Train class distribution mismatch: normal={train_normal}, suspicious={train_suspicious}")
        shape_validation = False
    
    if shape_validation:
        print("  All matrix validations PASS")
    else:
        print("  Matrix validation FAILED")
    
    print()
    return shape_validation

# =============================================================================
# METRICS CALCULATION
# =============================================================================

def calculate_metrics(y_true, y_pred, y_proba=None):
    """Calculate comprehensive metrics."""
    metrics = {
        'accuracy': accuracy_score(y_true, y_pred),
        'balanced_accuracy': balanced_accuracy_score(y_true, y_pred),
        'precision_0': precision_score(y_true, y_pred, pos_label=0),
        'recall_0': recall_score(y_true, y_pred, pos_label=0),
        'f1_0': f1_score(y_true, y_pred, pos_label=0),
        'precision_1': precision_score(y_true, y_pred, pos_label=1),
        'recall_1': recall_score(y_true, y_pred, pos_label=1),
        'f1_1': f1_score(y_true, y_pred, pos_label=1),
        'macro_f1': f1_score(y_true, y_pred, average='macro'),
    }
    
    if y_proba is not None:
        try:
            metrics['roc_auc'] = roc_auc_score(y_true, y_proba)
            metrics['pr_auc'] = average_precision_score(y_true, y_proba)
        except:
            metrics['roc_auc'] = None
            metrics['pr_auc'] = None
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    metrics['confusion_matrix'] = cm.tolist()
    
    # Calculate FPR
    tn, fp, fn, tp = cm.ravel()
    metrics['fpr'] = fp / (fp + tn) if (fp + tn) > 0 else 0
    
    return metrics

# =============================================================================
# CANDIDATE MODELS
# =============================================================================

def train_logistic_regression(X_train, y_train, X_val, y_val):
    """Train Logistic Regression with hyperparameter search."""
    print("=== Training Logistic Regression ===")
    
    # Hyperparameter grid
    param_grid = {
        'C': [0.01, 0.1, 1.0, 10.0],
        'class_weight': [None, 'balanced'],
        'max_iter': [1000],
        'random_state': [RANDOM_SEED]
    }
    
    best_model = None
    best_score = -1
    best_params = None
    results = []
    
    for params in ParameterGrid(param_grid):
        model = LogisticRegression(**params)
        model.fit(X_train, y_train)
        
        y_val_pred = model.predict(X_val)
        y_val_proba = model.predict_proba(X_val)[:, 1]
        macro_f1 = f1_score(y_val, y_val_pred, average='macro')
        
        results.append({
            'params': params,
            'macro_f1': macro_f1,
            'metrics': calculate_metrics(y_val, y_val_pred, y_val_proba)
        })
        
        if macro_f1 > best_score:
            best_score = macro_f1
            best_model = model
            best_params = params
    
    print(f"  Best validation Macro F1: {best_score:.4f}")
    print(f"  Best params: {best_params}")
    print()
    
    return best_model, best_params, results

def train_random_forest(X_train, y_train, X_val, y_val):
    """Train Random Forest with hyperparameter search."""
    print("=== Training Random Forest ===")
    
    # Hyperparameter grid
    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [10, 20, None],
        'min_samples_split': [2, 5],
        'min_samples_leaf': [1, 2],
        'class_weight': [None, 'balanced'],
        'random_state': [RANDOM_SEED]
    }
    
    best_model = None
    best_score = -1
    best_params = None
    results = []
    
    for params in ParameterGrid(param_grid):
        model = RandomForestClassifier(**params)
        model.fit(X_train, y_train)
        
        y_val_pred = model.predict(X_val)
        y_val_proba = model.predict_proba(X_val)[:, 1]
        macro_f1 = f1_score(y_val, y_val_pred, average='macro')
        
        results.append({
            'params': params,
            'macro_f1': macro_f1,
            'metrics': calculate_metrics(y_val, y_val_pred, y_val_proba)
        })
        
        if macro_f1 > best_score:
            best_score = macro_f1
            best_model = model
            best_params = params
    
    print(f"  Best validation Macro F1: {best_score:.4f}")
    print(f"  Best params: {best_params}")
    print()
    
    return best_model, best_params, results

def train_gradient_boosting(X_train, y_train, X_val, y_val):
    """Train Gradient Boosting with hyperparameter search."""
    print("=== Training Gradient Boosting ===")
    
    # Hyperparameter grid
    param_grid = {
        'n_estimators': [100, 200],
        'learning_rate': [0.01, 0.1],
        'max_depth': [3, 5],
        'min_samples_split': [2, 5],
        'min_samples_leaf': [1, 2],
        'random_state': [RANDOM_SEED]
    }
    
    best_model = None
    best_score = -1
    best_params = None
    results = []
    
    for params in ParameterGrid(param_grid):
        model = GradientBoostingClassifier(**params)
        model.fit(X_train, y_train)
        
        y_val_pred = model.predict(X_val)
        y_val_proba = model.predict_proba(X_val)[:, 1]
        macro_f1 = f1_score(y_val, y_val_pred, average='macro')
        
        results.append({
            'params': params,
            'macro_f1': macro_f1,
            'metrics': calculate_metrics(y_val, y_val_pred, y_val_proba)
        })
        
        if macro_f1 > best_score:
            best_score = macro_f1
            best_model = model
            best_params = params
    
    print(f"  Best validation Macro F1: {best_score:.4f}")
    print(f"  Best params: {best_params}")
    print()
    
    return best_model, best_params, results

# =============================================================================
# THRESHOLD SELECTION
# =============================================================================

def select_threshold(y_val, y_val_proba):
    """Select optimal threshold based on validation Macro F1."""
    print("=== Selecting Decision Threshold ===")
    
    thresholds = np.arange(0.1, 0.9, 0.05)
    best_threshold = 0.5
    best_score = -1
    
    for threshold in thresholds:
        y_val_pred = (y_val_proba >= threshold).astype(int)
        macro_f1 = f1_score(y_val, y_val_pred, average='macro')
        
        if macro_f1 > best_score:
            best_score = macro_f1
            best_threshold = threshold
    
    print(f"  Selected threshold: {best_threshold:.2f}")
    print(f"  Validation Macro F1 at threshold: {best_score:.4f}")
    print()
    
    return best_threshold

# =============================================================================
# FINAL EVALUATION
# =============================================================================

def evaluate_frozen_model(model, threshold, X, y, dataset_name):
    """Evaluate frozen model on a dataset."""
    print(f"=== Evaluating on {dataset_name} ===")
    
    y_proba = model.predict_proba(X)[:, 1]
    y_pred = (y_proba >= threshold).astype(int)
    
    metrics = calculate_metrics(y, y_pred, y_proba)
    
    print(f"  Accuracy: {metrics['accuracy']:.4f}")
    print(f"  Balanced Accuracy: {metrics['balanced_accuracy']:.4f}")
    print(f"  Macro F1: {metrics['macro_f1']:.4f}")
    print(f"  Suspicious Recall: {metrics['recall_1']:.4f}")
    print(f"  Suspicious Precision: {metrics['precision_1']:.4f}")
    print(f"  Suspicious F1: {metrics['f1_1']:.4f}")
    print(f"  ROC-AUC: {metrics['roc_auc']:.4f}" if metrics['roc_auc'] else "ROC-AUC: N/A")
    print(f"  PR-AUC: {metrics['pr_auc']:.4f}" if metrics['pr_auc'] else "PR-AUC: N/A")
    print()
    
    return metrics

# =============================================================================
# FEATURE IMPORTANCE
# =============================================================================

def extract_feature_importance(model, feature_names, model_type):
    """Extract feature importance from model."""
    print("=== Extracting Feature Importance ===")
    
    if model_type == 'logistic_regression':
        importance = np.abs(model.coef_[0])
    elif model_type in ['random_forest', 'gradient_boosting']:
        importance = model.feature_importances_
    else:
        importance = None
    
    if importance is not None:
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        # Group by feature type
        structuring = importance_df[importance_df['feature'].str.startswith('structuring_')]
        network = importance_df[importance_df['feature'].str.startswith('network_')]
        agent = importance_df[importance_df['feature'].str.startswith('agent_')]
        
        print(f"  Top 10 features by importance:")
        for _, row in importance_df.head(10).iterrows():
            print(f"    {row['feature']}: {row['importance']:.4f}")
        
        print()
        
        return importance_df
    else:
        print("  Feature importance not available for this model type")
        return None

# =============================================================================
# MAIN EXPERIMENT
# =============================================================================

def main():
    # Create output directory
    STAGE14_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load matrices
    matrices = load_stage13_matrices()
    
    # Validate matrices
    if not validate_matrices(matrices):
        print("ERROR: Matrix validation failed. Stopping.")
        return False, {}
    
    # Extract data
    X_train, y_train = matrices['X_train'], matrices['y_train']
    X_val, y_val = matrices['X_val'], matrices['y_val']
    X_test, y_test = matrices['X_test'], matrices['y_test']
    X_independent, y_independent = matrices['X_independent'], matrices['y_independent']
    feature_names = matrices['feature_names']
    
    # Train candidate models
    print("=" * 80)
    print("TRAINING CANDIDATE MODELS")
    print("=" * 80)
    print()
    
    # Model 1: Logistic Regression
    lr_model, lr_params, lr_results = train_logistic_regression(X_train, y_train, X_val, y_val)
    
    # Model 2: Random Forest
    rf_model, rf_params, rf_results = train_random_forest(X_train, y_train, X_val, y_val)
    
    # Model 3: Gradient Boosting
    gb_model, gb_params, gb_results = train_gradient_boosting(X_train, y_train, X_val, y_val)
    
    # Model comparison
    print("=" * 80)
    print("MODEL COMPARISON (VALIDATION MACRO F1)")
    print("=" * 80)
    
    comparison = {
        'logistic_regression': lr_results[-1]['macro_f1'],
        'random_forest': rf_results[-1]['macro_f1'],
        'gradient_boosting': gb_results[-1]['macro_f1']
    }
    
    for model_name, score in comparison.items():
        print(f"  {model_name}: {score:.4f}")
    
    print()
    
    # Select best model
    best_model_name = max(comparison, key=comparison.get)
    print(f"Selected model: {best_model_name}")
    print()
    
    if best_model_name == 'logistic_regression':
        selected_model = lr_model
        selected_params = lr_params
        model_type = 'logistic_regression'
    elif best_model_name == 'random_forest':
        selected_model = rf_model
        selected_params = rf_params
        model_type = 'random_forest'
    else:
        selected_model = gb_model
        selected_params = gb_params
        model_type = 'gradient_boosting'
    
    # Select threshold
    y_val_proba = selected_model.predict_proba(X_val)[:, 1]
    selected_threshold = select_threshold(y_val, y_val_proba)
    
    # Freeze model configuration
    print("=" * 80)
    print("MODEL FROZEN")
    print("=" * 80)
    print(f"Model: {best_model_name}")
    print(f"Hyperparameters: {selected_params}")
    print(f"Threshold: {selected_threshold}")
    print()
    
    # Final test evaluation
    print("=" * 80)
    print("FINAL TEST EVALUATION")
    print("=" * 80)
    print()
    
    test_metrics = evaluate_frozen_model(selected_model, selected_threshold, X_test, y_test, "Final Test")
    
    # Independent evaluation
    print("=" * 80)
    print("INDEPENDENT EVALUATION")
    print("=" * 80)
    print()
    
    independent_metrics = evaluate_frozen_model(selected_model, selected_threshold, X_independent, y_independent, "Independent")
    
    # Feature importance
    importance_df = extract_feature_importance(selected_model, feature_names, model_type)
    
    # Save results
    results = {
        'dataset_version': DATASET_VERSION,
        'feature_count': 30,
        'feature_names': feature_names,
        'train_shape': X_train.shape,
        'validation_shape': X_val.shape,
        'test_shape': X_test.shape,
        'independent_shape': X_independent.shape,
        'class_distribution': {
            'train': {'normal': int((y_train == 0).sum()), 'suspicious': int((y_train == 1).sum())},
            'validation': {'normal': int((y_val == 0).sum()), 'suspicious': int((y_val == 1).sum())},
            'test': {'normal': int((y_test == 0).sum()), 'suspicious': int((y_test == 1).sum())},
            'independent': {'normal': int((y_independent == 0).sum()), 'suspicious': int((y_independent == 1).sum())}
        },
        'candidate_models': comparison,
        'selected_model': best_model_name,
        'selected_hyperparameters': str(selected_params),
        'selected_threshold': selected_threshold,
        'validation_metrics': comparison[best_model_name],
        'final_test_metrics': test_metrics,
        'independent_metrics': independent_metrics,
        'feature_importance': importance_df.to_dict('records') if importance_df is not None else None,
        'random_seed': RANDOM_SEED,
        'status': 'PASS'
    }
    
    # Save results
    with open(STAGE14_DIR / 'stage14_experiment_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save model
    with open(STAGE14_DIR / 'stage14_frozen_model.pkl', 'wb') as f:
        pickle.dump({
            'model': selected_model,
            'threshold': selected_threshold,
            'feature_names': feature_names,
            'hyperparameters': selected_params,
            'model_type': model_type
        }, f)
    
    print("=" * 80)
    print("STAGE 14 COMPLETE")
    print("=" * 80)
    
    return True, results

if __name__ == "__main__":
    success, results = main()
    print(f"\nFinal result: {'PASS' if success else 'FAIL'}")
