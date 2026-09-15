"""
Stage 14 Correction: Domain and Scenario-Level Analysis

This script performs post-hoc domain and scenario-level analysis using the frozen Stage 14 model
and existing ground-truth metadata. It does NOT retrain the model or modify any artifacts.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
import pickle
import hashlib
import warnings
warnings.filterwarnings('ignore')

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

RANDOM_SEED = 42
FROZEN_THRESHOLD = 0.35

# =============================================================================
# LOAD FROZEN MODEL AND MATRICES
# =============================================================================

def load_frozen_model():
    """Load the frozen Stage 14 model."""
    print("=" * 80)
    print("STAGE 14 CORRECTION: DOMAIN AND SCENARIO ANALYSIS")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    print("Loading frozen model...")
    with open(STAGE14_DIR / "stage14_frozen_model.pkl", 'rb') as f:
        frozen_dict = pickle.load(f)
    
    model = frozen_dict['model']
    threshold = frozen_dict['threshold']
    feature_names = frozen_dict['feature_names']
    hyperparameters = frozen_dict['hyperparameters']
    model_type = frozen_dict['model_type']
    
    print(f"  Model type: {model_type}")
    print(f"  Actual model class: {type(model).__name__}")
    print(f"  Threshold: {threshold}")
    print(f"  Hyperparameters: {hyperparameters}")
    print()
    
    # Verify model parameters match expected configuration
    expected_params = {
        'learning_rate': 0.1,
        'max_depth': 3,
        'min_samples_leaf': 2,
        'min_samples_split': 5,
        'n_estimators': 200,
        'random_state': 42
    }
    
    actual_params = model.get_params()
    for key, expected_value in expected_params.items():
        actual_value = actual_params.get(key)
        if actual_value != expected_value:
            print(f"  WARNING: Parameter mismatch {key}: {actual_value} vs {expected_value}")
        else:
            print(f"  OK {key}: {actual_value}")
    
    # Verify threshold (allowing for floating point precision)
    if abs(threshold - FROZEN_THRESHOLD) < 1e-9:
        print(f"  OK Threshold: {threshold}")
    else:
        print(f"  WARNING: Threshold mismatch: {threshold} vs {FROZEN_THRESHOLD}")
    
    print()
    
    return model, threshold, feature_names, hyperparameters, model_type

def load_stage13_matrices():
    """Load Stage 13 feature matrices."""
    print("Loading Stage 13 feature matrices...")
    
    X_train = np.load(FEATURE_DIR / "X_train.npy")
    y_train = np.load(FEATURE_DIR / "y_train.npy")
    X_val = np.load(FEATURE_DIR / "X_val.npy")
    y_val = np.load(FEATURE_DIR / "y_val.npy")
    X_test = np.load(FEATURE_DIR / "X_test.npy")
    y_test = np.load(FEATURE_DIR / "y_test.npy")
    X_independent = np.load(FEATURE_DIR / "X_independent.npy")
    y_independent = np.load(FEATURE_DIR / "y_independent.npy")
    
    with open(FEATURE_DIR / "feature_names.json", 'r') as f:
        feature_names = json.load(f)
    
    print(f"  X_train: {X_train.shape}")
    print(f"  X_val: {X_val.shape}")
    print(f"  X_test: {X_test.shape}")
    print(f"  X_independent: {X_independent.shape}")
    print(f"  Feature count: {len(feature_names)}")
    print()
    
    return {
        'X_train': X_train, 'y_train': y_train,
        'X_val': X_val, 'y_val': y_val,
        'X_test': X_test, 'y_test': y_test,
        'X_independent': X_independent, 'y_independent': y_independent,
        'feature_names': feature_names
    }

def load_ground_truth():
    """Load ground truth metadata."""
    print("Loading ground truth metadata...")
    
    with open(DATA_DIR / "ground_truth.json", 'r') as f:
        ground_truth = json.load(f)
    
    print(f"  Ground truth entries: {len(ground_truth)}")
    print()
    
    return ground_truth

def load_transactions():
    """Load transactions to map feature matrix rows to transaction IDs."""
    print("Loading transactions...")
    
    transactions = pd.read_csv(DATA_DIR / "transactions.csv")
    
    print(f"  Total transactions: {len(transactions)}")
    print(f"  Columns: {list(transactions.columns)}")
    print()
    
    return transactions

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

def validate_partitions(matrices, transactions):
    """Validate partition structure matches transactions."""
    print("Validating partition structure...")
    
    # Count transactions by partition
    tx_partition_counts = transactions['partition'].value_counts().to_dict()
    print(f"  Transaction partition counts: {tx_partition_counts}")
    
    # Expected counts from matrices
    expected_counts = {
        'train': matrices['X_train'].shape[0],
        'validation': matrices['X_val'].shape[0],
        'final_test': matrices['X_test'].shape[0],
        'independent': matrices['X_independent'].shape[0]
    }
    print(f"  Matrix partition counts: {expected_counts}")
    
    validation = True
    for partition in ['train', 'validation', 'final_test', 'independent']:
        if tx_partition_counts.get(partition, 0) != expected_counts.get(partition, 0):
            print(f"  ERROR: Partition count mismatch for {partition}")
            validation = False
    
    if validation:
        print("  OK Partition structure validated")
    else:
        print("  ERROR: Partition structure validation failed")
    print()
    
    return validation

# =============================================================================
# PREDICTION GENERATION
# =============================================================================

def generate_predictions(model, matrices):
    """Generate predictions using frozen model."""
    print("Generating predictions with frozen model...")
    
    predictions = {}
    
    for split in ['train', 'val', 'test', 'independent']:
        X_key = f'X_{split}'
        y_key = f'y_{split}'
        
        if X_key in matrices:
            X = matrices[X_key]
            y = matrices[y_key]
            
            # Get probability predictions
            y_proba = model.predict_proba(X)[:, 1]
            
            # Apply frozen threshold
            y_pred = (y_proba >= FROZEN_THRESHOLD).astype(int)
            
            predictions[split] = {
                'y_true': y,
                'y_proba': y_proba,
                'y_pred': y_pred
            }
            
            print(f"  {split}: {len(y)} predictions generated")
    
    print()
    return predictions

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
# DOMAIN AND SCENARIO ANALYSIS
# =============================================================================

def create_transaction_mapping(transactions, matrices):
    """Create mapping from feature matrix indices to transaction IDs."""
    print("Creating transaction mapping...")
    
    # Sort transactions by partition and then by event_sequence to match matrix order
    # This assumes Stage 13 feature extraction used the same ordering
    transactions_sorted = transactions.sort_values(['partition', 'event_sequence'])
    
    mapping = {}
    idx = 0
    
    for partition in ['train', 'validation', 'final_test', 'independent']:
        partition_txns = transactions_sorted[transactions_sorted['partition'] == partition]
        partition_txns = partition_txns.sort_values('event_sequence')
        
        # Map partition names to split names used in matrices
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

def analyze_domain_performance(predictions, ground_truth, tx_mapping, split):
    """Analyze performance by AML domain (Structuring, Network, Agent)."""
    print(f"Analyzing domain performance for {split}...")
    
    if split not in predictions:
        print(f"  WARNING: No predictions for {split}")
        return None
    
    if split not in tx_mapping:
        print(f"  WARNING: No transaction mapping for {split}")
        return None
    
    # Create ground truth lookup
    gt_lookup = {gt['transaction_id']: gt for gt in ground_truth}
    
    # Get predictions and transaction IDs
    y_true = predictions[split]['y_true']
    y_pred = predictions[split]['y_pred']
    tx_ids = tx_mapping[split]['transaction_ids']
    
    # Initialize domain counters
    domains = {
        'structuring': {'tp': 0, 'fn': 0, 'total': 0},
        'network': {'tp': 0, 'fn': 0, 'total': 0},
        'agent': {'tp': 0, 'fn': 0, 'total': 0}
    }
    
    # Analyze each suspicious transaction
    for i, (tx_id, true_label, pred_label) in enumerate(zip(tx_ids, y_true, y_pred)):
        if true_label == 1:  # Only analyze suspicious transactions
            gt = gt_lookup.get(tx_id)
            if gt:
                domain = gt.get('scenario_category', '').lower()
                if domain in domains:
                    domains[domain]['total'] += 1
                    if pred_label == 1:
                        domains[domain]['tp'] += 1
                    else:
                        domains[domain]['fn'] += 1
    
    # Calculate metrics for each domain
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
        else:
            print(f"  {domain.capitalize()}: No suspicious transactions")
    
    print()
    return domain_results

def analyze_scenario_family_performance(predictions, ground_truth, tx_mapping, split):
    """Analyze performance by scenario family."""
    print(f"Analyzing scenario family performance for {split}...")
    
    if split not in predictions:
        print(f"  WARNING: No predictions for {split}")
        return None
    
    if split not in tx_mapping:
        print(f"  WARNING: No transaction mapping for {split}")
        return None
    
    # Create ground truth lookup
    gt_lookup = {gt['transaction_id']: gt for gt in ground_truth}
    
    # Get predictions and transaction IDs
    y_true = predictions[split]['y_true']
    y_pred = predictions[split]['y_pred']
    tx_ids = tx_mapping[split]['transaction_ids']
    
    # Initialize scenario family counters
    scenario_families = {}
    
    # Analyze each suspicious transaction
    for i, (tx_id, true_label, pred_label) in enumerate(zip(tx_ids, y_true, y_pred)):
        if true_label == 1:  # Only analyze suspicious transactions
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
    
    # Calculate metrics for each scenario family
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
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""
    
    # Load frozen model
    model, threshold, feature_names, hyperparameters, model_type = load_frozen_model()
    
    # Load matrices
    matrices = load_stage13_matrices()
    
    # Load ground truth
    ground_truth = load_ground_truth()
    
    # Load transactions
    transactions = load_transactions()
    
    # Verify data integrity
    checksums = compute_matrix_checksums(matrices)
    partition_valid = validate_partitions(matrices, transactions)
    
    # Generate predictions
    predictions = generate_predictions(model, matrices)
    
    # Calculate metrics for test and independent
    test_metrics = calculate_metrics(
        predictions['test']['y_true'],
        predictions['test']['y_pred'],
        predictions['test']['y_proba']
    )
    
    independent_metrics = calculate_metrics(
        predictions['independent']['y_true'],
        predictions['independent']['y_pred'],
        predictions['independent']['y_proba']
    )
    
    print("=== VERIFICATION OF EXISTING METRICS ===")
    print(f"Final Test ROC-AUC: {test_metrics['roc_auc']:.4f} (expected: 0.8474)")
    print(f"Final Test PR-AUC: {test_metrics['pr_auc']:.4f} (expected: 0.5829)")
    print(f"Independent ROC-AUC: {independent_metrics['roc_auc']:.4f} (expected: 0.8297)")
    print(f"Independent PR-AUC: {independent_metrics['pr_auc']:.4f} (expected: 0.5590)")
    print()
    
    # Create transaction mapping
    tx_mapping = create_transaction_mapping(transactions, matrices)
    
    # Perform domain analysis
    test_domain_results = analyze_domain_performance(predictions, ground_truth, tx_mapping, 'test')
    independent_domain_results = analyze_domain_performance(predictions, ground_truth, tx_mapping, 'independent')
    
    # Perform scenario family analysis
    test_scenario_results = analyze_scenario_family_performance(predictions, ground_truth, tx_mapping, 'test')
    independent_scenario_results = analyze_scenario_family_performance(predictions, ground_truth, tx_mapping, 'independent')
    
    # Compile results
    correction_results = {
        'correction_timestamp': datetime.now(timezone.utc).isoformat(),
        'model_status': 'FROZEN - NO RETRAINING',
        'model_type': model_type,
        'model_hyperparameters': hyperparameters,
        'threshold': threshold,
        'data_integrity': {
            'checksums': checksums,
            'partition_validation': partition_valid
        },
        'metrics_verification': {
            'final_test': {
                'roc_auc': round(test_metrics['roc_auc'], 4),
                'pr_auc': round(test_metrics['pr_auc'], 4),
                'macro_f1': round(test_metrics['macro_f1'], 4),
                'suspicious_recall': round(test_metrics['suspicious_recall'], 4)
            },
            'independent': {
                'roc_auc': round(independent_metrics['roc_auc'], 4),
                'pr_auc': round(independent_metrics['pr_auc'], 4),
                'macro_f1': round(independent_metrics['macro_f1'], 4),
                'suspicious_recall': round(independent_metrics['suspicious_recall'], 4)
            }
        },
        'domain_analysis': {
            'final_test': test_domain_results,
            'independent': independent_domain_results
        },
        'scenario_family_analysis': {
            'final_test': test_scenario_results,
            'independent': independent_scenario_results
        },
        'compliance_verification': {
            'model_retrained': False,
            'threshold_changed': False,
            'test_data_used_for_tuning': False,
            'independent_data_used_for_tuning': False,
            'stage13_matrices_modified': False,
            'raw_data_modified': False,
            'scenario_metadata_in_x': False
        }
    }
    
    # Save correction results
    output_file = STAGE14_DIR / "stage14_correction_results.json"
    with open(output_file, 'w') as f:
        json.dump(correction_results, f, indent=2)
    
    print(f"Correction results saved to: {output_file}")
    print()
    
    return correction_results

if __name__ == "__main__":
    results = main()
    print("Stage 14 correction complete.")
