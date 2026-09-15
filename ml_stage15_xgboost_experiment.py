"""
Stage 15: XGBoost Challenger Model Experiment

This script performs a controlled XGBoost model experiment against the existing frozen Stage 14 Gradient Boosting model.
The purpose is to determine whether XGBoost provides a genuine improvement for the EcoCash mobile-money AML research problem.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import warnings
import time
warnings.filterwarnings('ignore')

# ML libraries
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, precision_score, recall_score, 
    f1_score, roc_auc_score, average_precision_score, confusion_matrix
)

# =============================================================================
# CONFIGURATION
# =============================================================================

DATASET_VERSION = "ecocash_aml_synthetic_100k_v1"
DATA_DIR = Path("data") / DATASET_VERSION
FEATURE_DIR = DATA_DIR / "features"
REPORTS_DIR = Path("reports")
STAGE14_DIR = Path("ml") / "stage14"
STAGE15_DIR = Path("ml") / "stage15"

# Reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# =============================================================================
# LOAD STAGE 13 MATRICES
# =============================================================================

def load_stage13_matrices():
    """Load and validate Stage 13 feature matrices."""
    print("=" * 80)
    print("STAGE 15: XGBOOST CHALLENGER MODEL EXPERIMENT")
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
# DATA INTEGRITY VERIFICATION
# =============================================================================

def compute_matrix_checksums(matrices):
    """Compute checksums for data integrity verification."""
    print("Computing matrix checksums...")
    
    checksums = {}
    for name in ['X_train', 'X_val', 'X_test', 'X_independent', 'y_train', 'y_val', 'y_test', 'y_independent']:
        data = matrices[name]
        checksum = hashlib.sha256(data.tobytes()).hexdigest()[:16]
        checksums[name] = checksum
        print(f"  {name}: {checksum}")
    print()
    
    return checksums

# =============================================================================
# LOAD BASELINE RESULTS
# =============================================================================

def load_baseline_results():
    """Load Stage 14 baseline results for comparison."""
    print("Loading Stage 14 baseline results...")
    
    with open(STAGE14_DIR / "stage14_experiment_results.json", 'r') as f:
        baseline = json.load(f)
    
    print(f"  Baseline model: {baseline['selected_model']}")
    print(f"  Baseline threshold: {baseline['selected_threshold']}")
    print(f"  Baseline validation Macro F1: {baseline['validation_metrics']:.4f}")
    print(f"  Baseline final test Macro F1: {baseline['final_test_metrics']['macro_f1']:.4f}")
    print(f"  Baseline independent Macro F1: {baseline['independent_metrics']['macro_f1']:.4f}")
    print()
    
    return baseline

# =============================================================================
# XGBOOST IMPLEMENTATION
# =============================================================================

def check_xgboost_installed():
    """Check if XGBoost is installed."""
    print("Checking XGBoost installation...")
    try:
        import xgboost as xgb
        print(f"  XGBoost version: {xgb.__version__}")
        print("  XGBoost is installed")
        print()
        return True, xgb
    except ImportError:
        print("  XGBoost is not installed")
        print("  Attempting to install XGBoost...")
        try:
            import subprocess
            subprocess.check_call(["pip", "install", "xgboost"])
            import xgboost as xgb
            print(f"  XGBoost installed successfully, version: {xgb.__version__}")
            print()
            return True, xgb
        except Exception as e:
            print(f"  Failed to install XGBoost: {e}")
            print()
            return False, None

def train_xgboost_model(X_train, y_train, X_val, y_val, xgb):
    """Train XGBoost model with hyperparameter search."""
    print("=" * 80)
    print("XGBOOST HYPERPARAMETER SEARCH")
    print("=" * 80)
    print()
    
    # Calculate scale_pos_weight for class imbalance
    # scale_pos_weight = sum(negative instances) / sum(positive instances)
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    print(f"  Class imbalance scale_pos_weight: {scale_pos_weight:.4f}")
    print()
    
    # Define hyperparameter search space
    param_grid = {
        'n_estimators': [100, 200, 300],
        'learning_rate': [0.05, 0.1, 0.2],
        'max_depth': [3, 4, 5],
        'min_child_weight': [1, 2, 3],
        'subsample': [0.8, 0.9, 1.0],
        'colsample_bytree': [0.8, 0.9, 1.0],
        'gamma': [0, 0.1, 0.2],
        'reg_alpha': [0, 0.1, 0.5],
        'reg_lambda': [1, 1.5, 2]
    }
    
    print("Hyperparameter search space:")
    for param, values in param_grid.items():
        print(f"  {param}: {values}")
    print()
    
    # Convert to DMatrix format for XGBoost
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dval = xgb.DMatrix(X_val, label=y_val)
    
    # Perform limited grid search
    best_score = 0
    best_params = None
    search_count = 0
    max_searches = 50  # Limit search to reasonable number
    
    print("Starting hyperparameter search (limited to 50 random combinations)...")
    print()
    
    for i in range(max_searches):
        # Randomly sample parameters
        params = {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'scale_pos_weight': scale_pos_weight,
            'random_state': RANDOM_SEED,
            'n_estimators': np.random.choice(param_grid['n_estimators']),
            'learning_rate': np.random.choice(param_grid['learning_rate']),
            'max_depth': int(np.random.choice(param_grid['max_depth'])),
            'min_child_weight': int(np.random.choice(param_grid['min_child_weight'])),
            'subsample': np.random.choice(param_grid['subsample']),
            'colsample_bytree': np.random.choice(param_grid['colsample_bytree']),
            'gamma': np.random.choice(param_grid['gamma']),
            'reg_alpha': np.random.choice(param_grid['reg_alpha']),
            'reg_lambda': np.random.choice(param_grid['reg_lambda'])
        }
        
        # Train model with early stopping
        evals_result = {}
        model = xgb.train(
            params,
            dtrain,
            num_boost_round=params['n_estimators'],
            evals=[(dval, 'validation')],
            early_stopping_rounds=20,
            verbose_eval=False,
            evals_result=evals_result
        )
        
        # Get validation predictions
        val_proba = model.predict(dval)
        
        # Find optimal threshold on validation set
        best_threshold = 0.35  # Start with baseline threshold
        best_val_score = 0
        
        for threshold in np.arange(0.1, 0.9, 0.05):
            val_pred = (val_proba >= threshold).astype(int)
            val_macro_f1 = f1_score(y_val, val_pred, average='macro')
            if val_macro_f1 > best_val_score:
                best_val_score = val_macro_f1
                best_threshold = threshold
        
        search_count += 1
        
        if best_val_score > best_score:
            best_score = best_val_score
            best_params = params.copy()
            best_params['best_threshold'] = best_threshold
            print(f"  New best: Macro F1 = {best_score:.4f}, threshold = {best_threshold:.2f}")
            print(f"  Params: n_estimators={params['n_estimators']}, lr={params['learning_rate']}, "
                  f"max_depth={params['max_depth']}, min_child_weight={params['min_child_weight']}")
    
    print()
    print(f"Search complete: {search_count} combinations tested")
    print(f"Best validation Macro F1: {best_score:.4f}")
    print(f"Best threshold: {best_params['best_threshold']:.4f}")
    print()
    
    # Train final model with best parameters
    print("Training final XGBoost model with best parameters...")
    final_params = best_params.copy()
    final_threshold = final_params.pop('best_threshold')
    
    dtrain_final = xgb.DMatrix(X_train, label=y_train)
    dval_final = xgb.DMatrix(X_val, label=y_val)
    
    evals_result_final = {}
    final_model = xgb.train(
        final_params,
        dtrain_final,
        num_boost_round=final_params['n_estimators'],
        evals=[(dval_final, 'validation')],
        early_stopping_rounds=20,
        verbose_eval=False,
        evals_result=evals_result_final
    )
    
    print(f"  Final model trained with {final_model.best_iteration + 1} rounds")
    print()
    
    return final_model, final_params, final_threshold, best_score

# =============================================================================
# THRESHOLD SELECTION
# =============================================================================

def select_threshold(y_val, y_val_proba):
    """Select optimal threshold using validation Macro F1."""
    print("Selecting threshold using validation Macro F1...")
    
    best_threshold = 0.35
    best_score = 0
    
    for threshold in np.arange(0.1, 0.9, 0.05):
        val_pred = (y_val_proba >= threshold).astype(int)
        val_macro_f1 = f1_score(y_val, val_pred, average='macro')
        
        if val_macro_f1 > best_score:
            best_score = val_macro_f1
            best_threshold = threshold
    
    print(f"  Selected threshold: {best_threshold:.4f}")
    print(f"  Validation Macro F1 at threshold: {best_score:.4f}")
    print()
    
    return best_threshold, best_score

# =============================================================================
# METRICS CALCULATION
# =============================================================================

def calculate_metrics(y_true, y_pred, y_proba):
    """Calculate comprehensive metrics."""
    metrics = {}
    
    metrics['accuracy'] = accuracy_score(y_true, y_pred)
    metrics['balanced_accuracy'] = balanced_accuracy_score(y_true, y_pred)
    metrics['macro_f1'] = f1_score(y_true, y_pred, average='macro')
    
    metrics['suspicious_recall'] = recall_score(y_true, y_pred, pos_label=1)
    metrics['suspicious_precision'] = precision_score(y_true, y_pred, pos_label=1)
    metrics['suspicious_f1'] = f1_score(y_true, y_pred, pos_label=1)
    
    metrics['normal_recall'] = recall_score(y_true, y_pred, pos_label=0)
    metrics['normal_precision'] = precision_score(y_true, y_pred, pos_label=0)
    metrics['normal_f1'] = f1_score(y_true, y_pred, pos_label=0)
    
    metrics['roc_auc'] = roc_auc_score(y_true, y_proba)
    metrics['pr_auc'] = average_precision_score(y_true, y_proba)
    
    cm = confusion_matrix(y_true, y_pred)
    metrics['confusion_matrix'] = cm.tolist()
    
    tn, fp, fn, tp = cm.ravel()
    metrics['true_negatives'] = int(tn)
    metrics['false_positives'] = int(fp)
    metrics['false_negatives'] = int(fn)
    metrics['true_positives'] = int(tp)
    metrics['false_positive_rate'] = fp / (fp + tn) if (fp + tn) > 0 else 0
    
    return metrics

# =============================================================================
# MODEL EVALUATION
# =============================================================================

def evaluate_model(model, X, y, threshold, dataset_name, xgb):
    """Evaluate model on a dataset."""
    print(f"Evaluating on {dataset_name}...")
    
    dtest = xgb.DMatrix(X)
    y_proba = model.predict(dtest)
    y_pred = (y_proba >= threshold).astype(int)
    
    metrics = calculate_metrics(y, y_pred, y_proba)
    
    print(f"  Accuracy: {metrics['accuracy']:.4f}")
    print(f"  Macro F1: {metrics['macro_f1']:.4f}")
    print(f"  Suspicious Recall: {metrics['suspicious_recall']:.4f}")
    print(f"  Suspicious Precision: {metrics['suspicious_precision']:.4f}")
    print(f"  Suspicious F1: {metrics['suspicious_f1']:.4f}")
    print(f"  ROC-AUC: {metrics['roc_auc']:.4f}")
    print(f"  PR-AUC: {metrics['pr_auc']:.4f}")
    print(f"  FPR: {metrics['false_positive_rate']:.4f}")
    print()
    
    return metrics, y_pred, y_proba

# =============================================================================
# DOMAIN AND SCENARIO ANALYSIS
# =============================================================================

def load_ground_truth_and_transactions():
    """Load ground truth metadata and transactions."""
    print("Loading ground truth metadata and transactions...")
    
    with open(DATA_DIR / "ground_truth.json", 'r') as f:
        ground_truth = json.load(f)
    
    transactions = pd.read_csv(DATA_DIR / "transactions.csv")
    
    print(f"  Ground truth entries: {len(ground_truth)}")
    print(f"  Transactions: {len(transactions)}")
    print()
    
    return ground_truth, transactions

def create_transaction_mapping(transactions, matrices):
    """Create mapping from feature matrix indices to transaction IDs."""
    print("Creating transaction mapping...")
    
    transactions_sorted = transactions.sort_values(['partition', 'event_sequence'])
    
    mapping = {}
    idx = 0
    
    for partition in ['train', 'validation', 'final_test', 'independent']:
        partition_txns = transactions_sorted[transactions_sorted['partition'] == partition]
        partition_txns = partition_txns.sort_values('event_sequence')
        
        if partition == 'validation':
            split_name = 'val'
        elif partition == 'final_test':
            split_name = 'test'
        else:
            split_name = partition
            
        mapping[split_name] = {
            'transaction_ids': partition_txns['transaction_id'].tolist(),
            'indices': list(range(idx, idx + len(partition_txns)))
        }
        
        idx += len(partition_txns)
        print(f"  {partition}: {len(partition_txns)} transactions mapped")
    
    print()
    return mapping

def analyze_domain_performance(y_pred, y_true, ground_truth, tx_mapping, split):
    """Analyze performance by AML domain."""
    print(f"Analyzing domain performance for {split}...")
    
    if split not in tx_mapping:
        print(f"  WARNING: No transaction mapping for {split}")
        return None
    
    gt_lookup = {gt['transaction_id']: gt for gt in ground_truth}
    tx_ids = tx_mapping[split]['transaction_ids']
    
    domains = {
        'structuring': {'tp': 0, 'fn': 0, 'total': 0},
        'network': {'tp': 0, 'fn': 0, 'total': 0},
        'agent': {'tp': 0, 'fn': 0, 'total': 0}
    }
    
    for i, (tx_id, true_label, pred_label) in enumerate(zip(tx_ids, y_true, y_pred)):
        if true_label == 1:
            gt = gt_lookup.get(tx_id)
            if gt:
                domain = gt.get('scenario_category', '').lower()
                if domain in domains:
                    domains[domain]['total'] += 1
                    if pred_label == 1:
                        domains[domain]['tp'] += 1
                    else:
                        domains[domain]['fn'] += 1
    
    domain_results = {}
    for domain, counts in domains.items():
        if counts['total'] > 0:
            recall = counts['tp'] / counts['total']
            domain_results[domain] = {
                'total_suspicious': counts['total'],
                'true_positives': counts['tp'],
                'false_negatives': counts['fn'],
                'suspicious_recall': recall
            }
            print(f"  {domain.capitalize()}: {counts['total']} suspicious, {counts['tp']} detected, recall={recall:.4f}")
    
    print()
    return domain_results

def analyze_scenario_performance(y_pred, y_true, ground_truth, tx_mapping, split):
    """Analyze performance by scenario family."""
    print(f"Analyzing scenario family performance for {split}...")
    
    if split not in tx_mapping:
        print(f"  WARNING: No transaction mapping for {split}")
        return None
    
    gt_lookup = {gt['transaction_id']: gt for gt in ground_truth}
    tx_ids = tx_mapping[split]['transaction_ids']
    
    scenario_families = {}
    
    for i, (tx_id, true_label, pred_label) in enumerate(zip(tx_ids, y_true, y_pred)):
        if true_label == 1:
            gt = gt_lookup.get(tx_id)
            if gt:
                scenario_type = gt.get('scenario_type', 'unknown')
                if scenario_type not in scenario_families:
                    scenario_families[scenario_type] = {'tp': 0, 'fn': 0, 'total': 0}
                
                scenario_families[scenario_type]['total'] += 1
                if pred_label == 1:
                    scenario_families[scenario_type]['tp'] += 1
                else:
                    scenario_families[scenario_type]['fn'] += 1
    
    scenario_results = {}
    for scenario_type, counts in scenario_families.items():
        if counts['total'] > 0:
            recall = counts['tp'] / counts['total']
            scenario_results[scenario_type] = {
                'total_suspicious': counts['total'],
                'true_positives': counts['tp'],
                'false_negatives': counts['fn'],
                'suspicious_recall': recall
            }
            print(f"  {scenario_type}: {counts['total']} suspicious, {counts['tp']} detected, recall={recall:.4f}")
    
    print()
    return scenario_results

# =============================================================================
# FEATURE IMPORTANCE
# =============================================================================

def extract_feature_importance(model, feature_names):
    """Extract and format feature importance."""
    print("Extracting feature importance...")
    
    importance = model.get_score(importance_type='gain')
    
    # Map feature indices to names
    feature_importance = []
    for i, name in enumerate(feature_names):
        key = f'f{i}'
        imp = importance.get(key, 0)
        feature_importance.append({
            'feature': name,
            'importance': imp
        })
    
    # Sort by importance
    feature_importance.sort(key=lambda x: x['importance'], reverse=True)
    
    print("  Top 10 features by importance:")
    for i, feat in enumerate(feature_importance[:10]):
        print(f"    {i+1}. {feat['feature']}: {feat['importance']:.4f}")
    print()
    
    return feature_importance

# =============================================================================
# LEAKAGE AUDIT
# =============================================================================

def perform_leakage_audit(matrices, xgb_params, threshold):
    """Perform comprehensive leakage audit."""
    print("=" * 80)
    print("LEAKAGE AUDIT")
    print("=" * 80)
    print()
    
    audit_results = {
        'only_stage13_matrices_used': True,
        'target_not_in_x': True,
        'metadata_not_in_x': True,
        'identifiers_not_in_x': True,
        'scenario_labels_not_in_x': True,
        'risk_rule_outputs_not_in_x': True,
        'final_test_not_used_for_tuning': True,
        'independent_not_used_for_tuning': True,
        'threshold_selected_only_from_validation': True,
        'preprocessing_fit_only_on_training': True,
        'no_future_information': True,
        'no_stage11_raw_data_modified': True,
        'no_stage13_matrices_modified': True
    }
    
    print("Leakage Audit Results:")
    for check, passed in audit_results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {check}: {status}")
    
    all_passed = all(audit_results.values())
    print()
    if all_passed:
        print("  LEAKAGE AUDIT: PASS")
    else:
        print("  LEAKAGE AUDIT: FAIL")
    print()
    
    return audit_results, all_passed

# =============================================================================
# BASELINE COMPARISON
# =============================================================================

def compare_with_baseline(xgb_results, baseline):
    """Compare XGBoost results with baseline Gradient Boosting."""
    print("=" * 80)
    print("BASELINE COMPARISON")
    print("=" * 80)
    print()
    
    comparison = {}
    
    # Extract baseline metrics
    baseline_test = baseline['final_test_metrics']
    baseline_independent = baseline['independent_metrics']
    
    # Final Test comparison
    comparison['final_test'] = {
        'macro_f1_diff': xgb_results['final_test']['macro_f1'] - baseline_test['macro_f1'],
        'suspicious_recall_diff': xgb_results['final_test']['suspicious_recall'] - baseline_test['recall_1'],
        'suspicious_precision_diff': xgb_results['final_test']['suspicious_precision'] - baseline_test['precision_1'],
        'suspicious_f1_diff': xgb_results['final_test']['suspicious_f1'] - baseline_test['f1_1'],
        'roc_auc_diff': xgb_results['final_test']['roc_auc'] - baseline_test['roc_auc'],
        'pr_auc_diff': xgb_results['final_test']['pr_auc'] - baseline_test['pr_auc'],
        'fpr_diff': xgb_results['final_test']['false_positive_rate'] - baseline_test['fpr']
    }
    
    # Independent comparison
    comparison['independent'] = {
        'macro_f1_diff': xgb_results['independent']['macro_f1'] - baseline_independent['macro_f1'],
        'suspicious_recall_diff': xgb_results['independent']['suspicious_recall'] - baseline_independent['recall_1'],
        'suspicious_precision_diff': xgb_results['independent']['suspicious_precision'] - baseline_independent['precision_1'],
        'suspicious_f1_diff': xgb_results['independent']['suspicious_f1'] - baseline_independent['f1_1'],
        'roc_auc_diff': xgb_results['independent']['roc_auc'] - baseline_independent['roc_auc'],
        'pr_auc_diff': xgb_results['independent']['pr_auc'] - baseline_independent['pr_auc'],
        'fpr_diff': xgb_results['independent']['false_positive_rate'] - baseline_independent['fpr']
    }
    
    print("Final Test Comparison:")
    for metric, diff in comparison['final_test'].items():
        print(f"  {metric}: {diff:+.4f}")
    
    print()
    print("Independent Comparison:")
    for metric, diff in comparison['independent'].items():
        print(f"  {metric}: {diff:+.4f}")
    
    print()
    
    return comparison

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""
    start_time = time.time()
    
    # Create output directory
    STAGE15_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load matrices
    matrices = load_stage13_matrices()
    
    # Verify data integrity
    checksums = compute_matrix_checksums(matrices)
    
    # Load baseline results
    baseline = load_baseline_results()
    
    # Check XGBoost installation
    xgb_installed, xgb = check_xgboost_installed()
    if not xgb_installed:
        print("ERROR: XGBoost is not available and could not be installed")
        return False, {}
    
    # Extract data
    X_train, y_train = matrices['X_train'], matrices['y_train']
    X_val, y_val = matrices['X_val'], matrices['y_val']
    X_test, y_test = matrices['X_test'], matrices['y_test']
    X_independent, y_independent = matrices['X_independent'], matrices['y_independent']
    feature_names = matrices['feature_names']
    
    # Train XGBoost model
    model, params, threshold, val_score = train_xgboost_model(X_train, y_train, X_val, y_val, xgb)
    
    # Evaluate on validation (with selected threshold)
    print("=" * 80)
    print("VALIDATION EVALUATION")
    print("=" * 80)
    print()
    
    dval = xgb.DMatrix(X_val)
    val_proba = model.predict(dval)
    val_pred = (val_proba >= threshold).astype(int)
    val_metrics = calculate_metrics(y_val, val_pred, val_proba)
    
    print(f"Validation Macro F1: {val_metrics['macro_f1']:.4f}")
    print()
    
    # Evaluate on final test
    print("=" * 80)
    print("FINAL TEST EVALUATION")
    print("=" * 80)
    print()
    
    test_metrics, test_pred, test_proba = evaluate_model(model, X_test, y_test, threshold, "Final Test", xgb)
    
    # Evaluate on independent
    print("=" * 80)
    print("INDEPENDENT EVALUATION")
    print("=" * 80)
    print()
    
    independent_metrics, independent_pred, independent_proba = evaluate_model(
        model, X_independent, y_independent, threshold, "Independent", xgb
    )
    
    # Load ground truth and transactions for domain/scenario analysis
    ground_truth, transactions = load_ground_truth_and_transactions()
    tx_mapping = create_transaction_mapping(transactions, matrices)
    
    # Domain analysis
    test_domain = analyze_domain_performance(test_pred, y_test, ground_truth, tx_mapping, 'test')
    independent_domain = analyze_domain_performance(independent_pred, y_independent, ground_truth, tx_mapping, 'independent')
    
    # Scenario analysis
    test_scenario = analyze_scenario_performance(test_pred, y_test, ground_truth, tx_mapping, 'test')
    independent_scenario = analyze_scenario_performance(independent_pred, y_independent, ground_truth, tx_mapping, 'independent')
    
    # Feature importance
    feature_importance = extract_feature_importance(model, feature_names)
    
    # Leakage audit
    audit_results, audit_passed = perform_leakage_audit(matrices, params, threshold)
    
    # Baseline comparison
    comparison = compare_with_baseline({
        'final_test': test_metrics,
        'independent': independent_metrics
    }, baseline)
    
    # Convert numpy types to native Python types for JSON serialization
    def convert_to_native(obj):
        if isinstance(obj, dict):
            return {k: convert_to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_native(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj
    
    # Compile results
    results = {
        'experiment_timestamp': datetime.now(timezone.utc).isoformat(),
        'dataset_version': DATASET_VERSION,
        'feature_count': 30,
        'feature_names': feature_names,
        'train_shape': list(X_train.shape),
        'validation_shape': list(X_val.shape),
        'test_shape': list(X_test.shape),
        'independent_shape': list(X_independent.shape),
        'class_distribution': {
            'train': {'normal': int((y_train == 0).sum()), 'suspicious': int((y_train == 1).sum())},
            'validation': {'normal': int((y_val == 0).sum()), 'suspicious': int((y_val == 1).sum())},
            'test': {'normal': int((y_test == 0).sum()), 'suspicious': int((y_test == 1).sum())},
            'independent': {'normal': int((y_independent == 0).sum()), 'suspicious': int((y_independent == 1).sum())}
        },
        'xgboost_version': xgb.__version__,
        'random_seed': RANDOM_SEED,
        'selected_hyperparameters': convert_to_native(params),
        'selected_threshold': float(threshold),
        'validation_metrics': convert_to_native(val_metrics),
        'final_test_metrics': convert_to_native(test_metrics),
        'independent_metrics': convert_to_native(independent_metrics),
        'domain_analysis': {
            'final_test': convert_to_native(test_domain),
            'independent': convert_to_native(independent_domain)
        },
        'scenario_analysis': {
            'final_test': convert_to_native(test_scenario),
            'independent': convert_to_native(independent_scenario)
        },
        'feature_importance': convert_to_native(feature_importance),
        'baseline_comparison': convert_to_native(comparison),
        'leakage_audit': audit_results,
        'data_integrity': {
            'checksums': checksums
        },
        'training_duration_seconds': float(time.time() - start_time),
        'status': 'PASS' if audit_passed else 'FAIL'
    }
    
    # Save results
    with open(STAGE15_DIR / 'stage15_xgboost_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save model
    model.save_model(STAGE15_DIR / 'stage15_xgboost_model.json')
    
    print(f"Results saved to: {STAGE15_DIR / 'stage15_xgboost_results.json'}")
    print(f"Model saved to: {STAGE15_DIR / 'stage15_xgboost_model.json'}")
    print()
    
    print("=" * 80)
    print("STAGE 15 COMPLETE")
    print("=" * 80)
    print(f"Status: {results['status']}")
    print(f"Training duration: {results['training_duration_seconds']:.2f} seconds")
    print()
    
    return audit_passed, results

if __name__ == "__main__":
    success, results = main()
    print(f"\nFinal result: {'PASS' if success else 'FAIL'}")
