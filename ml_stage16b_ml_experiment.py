"""
Stage 16B: Structuring Feature Expansion ML Experiment

This script trains and evaluates a Gradient Boosting model on the experimental 34-feature matrices
and compares it against the frozen Stage 14 baseline to determine whether the new features provide
genuine improvement in Structuring-domain detection.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
import warnings
import pickle
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, f1_score,
    precision_score, recall_score, roc_auc_score, average_precision_score,
    confusion_matrix
)
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

DATASET_VERSION = "ecocash_aml_synthetic_100k_v1"
DATA_DIR = Path("data") / DATASET_VERSION
FEATURE_STAGE16B_DIR = DATA_DIR / "features_stage16b"
REPORTS_DIR = Path("reports")
STAGE14_DIR = Path("ml") / "stage14"
STAGE16B_DIR = Path("ml") / "stage16b"

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# Stage 14 baseline configuration (starting point)
BASELINE_CONFIG = {
    'learning_rate': 0.1,
    'max_depth': 3,
    'min_samples_leaf': 2,
    'min_samples_split': 5,
    'n_estimators': 200,
    'random_state': 42
}

# =============================================================================
# LOAD DATA
# =============================================================================

def load_experimental_matrices():
    """Load experimental 34-feature matrices."""
    print("=" * 80)
    print("STAGE 16B: STRUCTURING FEATURE EXPANSION ML EXPERIMENT")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    print("Loading experimental 34-feature matrices...")
    
    X_train = np.load(FEATURE_STAGE16B_DIR / "X_train_34.npy")
    y_train = np.load(FEATURE_STAGE16B_DIR / "y_train_34.npy")
    X_val = np.load(FEATURE_STAGE16B_DIR / "X_val_34.npy")
    y_val = np.load(FEATURE_STAGE16B_DIR / "y_val_34.npy")
    X_test = np.load(FEATURE_STAGE16B_DIR / "X_test_34.npy")
    y_test = np.load(FEATURE_STAGE16B_DIR / "y_test_34.npy")
    X_independent = np.load(FEATURE_STAGE16B_DIR / "X_independent_34.npy")
    y_independent = np.load(FEATURE_STAGE16B_DIR / "y_independent_34.npy")
    
    print(f"  X_train_34 shape: {X_train.shape}")
    print(f"  X_val_34 shape: {X_val.shape}")
    print(f"  X_test_34 shape: {X_test.shape}")
    print(f"  X_independent_34 shape: {X_independent.shape}")
    print()
    
    return {
        'X_train': X_train, 'y_train': y_train,
        'X_val': X_val, 'y_val': y_val,
        'X_test': X_test, 'y_test': y_test,
        'X_independent': X_independent, 'y_independent': y_independent
    }

def load_baseline_results():
    """Load frozen Stage 14 baseline results."""
    print("Loading frozen Stage 14 baseline results...")
    
    with open(STAGE14_DIR / "stage14_correction_results.json", 'r') as f:
        baseline_results = json.load(f)
    
    # Normalize structure to match expected format with full metrics
    baseline_results['final_test_metrics'] = {
        'macro_f1': baseline_results['metrics_verification']['final_test']['macro_f1'],
        'suspicious_recall': baseline_results['metrics_verification']['final_test']['suspicious_recall'],
        'suspicious_precision': 0.5864,  # From Stage 14 report
        'suspicious_f1': 0.5515,  # From Stage 14 report
        'roc_auc': baseline_results['metrics_verification']['final_test']['roc_auc'],
        'pr_auc': baseline_results['metrics_verification']['final_test']['pr_auc'],
        'fpr': 0.0465  # From Stage 14 report
    }
    
    baseline_results['independent_metrics'] = {
        'macro_f1': baseline_results['metrics_verification']['independent']['macro_f1'],
        'suspicious_recall': baseline_results['metrics_verification']['independent']['suspicious_recall'],
        'suspicious_precision': 0.4940,  # From Stage 14 report
        'suspicious_f1': 0.5186,  # From Stage 14 report
        'roc_auc': baseline_results['metrics_verification']['independent']['roc_auc'],
        'pr_auc': baseline_results['metrics_verification']['independent']['pr_auc'],
        'fpr': 0.0762  # From Stage 14 report
    }
    
    print(f"  Baseline final test Macro F1: {baseline_results['final_test_metrics']['macro_f1']}")
    print(f"  Baseline independent Macro F1: {baseline_results['independent_metrics']['macro_f1']}")
    print()
    
    return baseline_results

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

# =============================================================================
# MODEL TRAINING
# =============================================================================

def train_model(X_train, y_train):
    """Train Gradient Boosting model with Stage 14 configuration."""
    print("Training experimental Gradient Boosting model...")
    print(f"  Configuration: {BASELINE_CONFIG}")
    
    model = GradientBoostingClassifier(**BASELINE_CONFIG)
    model.fit(X_train, y_train)
    
    print("  Model training complete")
    print()
    
    return model

def select_threshold(model, X_val, y_val):
    """Select threshold using validation set only."""
    print("Selecting threshold using validation set...")
    
    y_proba = model.predict_proba(X_val)[:, 1]
    
    # Evaluate threshold range
    thresholds = np.arange(0.1, 0.9, 0.05)
    best_threshold = 0.35  # Start with baseline threshold
    best_macro_f1 = 0.0
    
    for threshold in thresholds:
        y_pred = (y_proba >= threshold).astype(int)
        macro_f1 = f1_score(y_val, y_pred, average='macro')
        
        if macro_f1 > best_macro_f1:
            best_macro_f1 = macro_f1
            best_threshold = threshold
    
    print(f"  Selected threshold: {best_threshold:.4f}")
    print(f"  Validation Macro F1 at threshold: {best_macro_f1:.4f}")
    print()
    
    return best_threshold, best_macro_f1

# =============================================================================
# EVALUATION
# =============================================================================

def evaluate_model(model, threshold, X, y, set_name):
    """Evaluate model on a given dataset."""
    print(f"Evaluating on {set_name}...")
    
    y_proba = model.predict_proba(X)[:, 1]
    y_pred = (y_proba >= threshold).astype(int)
    
    # Calculate metrics
    accuracy = accuracy_score(y, y_pred)
    balanced_accuracy = balanced_accuracy_score(y, y_pred)
    macro_f1 = f1_score(y, y_pred, average='macro')
    
    suspicious_precision = precision_score(y, y_pred, pos_label=1)
    suspicious_recall = recall_score(y, y_pred, pos_label=1)
    suspicious_f1 = f1_score(y, y_pred, pos_label=1)
    
    normal_precision = precision_score(y, y_pred, pos_label=0)
    normal_recall = recall_score(y, y_pred, pos_label=0)
    normal_f1 = f1_score(y, y_pred, pos_label=0)
    
    roc_auc = roc_auc_score(y, y_proba)
    pr_auc = average_precision_score(y, y_proba)
    
    cm = confusion_matrix(y, y_pred)
    tn, fp, fn, tp = cm.ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    
    metrics = {
        'accuracy': float(accuracy),
        'balanced_accuracy': float(balanced_accuracy),
        'macro_f1': float(macro_f1),
        'suspicious_precision': float(suspicious_precision),
        'suspicious_recall': float(suspicious_recall),
        'suspicious_f1': float(suspicious_f1),
        'normal_precision': float(normal_precision),
        'normal_recall': float(normal_recall),
        'normal_f1': float(normal_f1),
        'roc_auc': float(roc_auc),
        'pr_auc': float(pr_auc),
        'fpr': float(fpr),
        'confusion_matrix': cm.tolist(),
        'true_negatives': int(tn),
        'false_positives': int(fp),
        'false_negatives': int(fn),
        'true_positives': int(tp)
    }
    
    print(f"  Accuracy: {accuracy:.4f}")
    print(f"  Macro F1: {macro_f1:.4f}")
    print(f"  Suspicious Recall: {suspicious_recall:.4f}")
    print(f"  Suspicious Precision: {suspicious_precision:.4f}")
    print(f"  ROC-AUC: {roc_auc:.4f}")
    print(f"  PR-AUC: {pr_auc:.4f}")
    print()
    
    return metrics

# =============================================================================
# DOMAIN/SCENARIO ANALYSIS
# =============================================================================

def analyze_domain_performance(model, threshold, X, y, ground_truth, transactions, set_name):
    """Analyze domain performance using frozen predictions."""
    print(f"Analyzing domain performance for {set_name}...")
    
    # Get predictions
    y_proba = model.predict_proba(X)[:, 1]
    y_pred = (y_proba >= threshold).astype(int)
    
    # Load feature manifest to get partition mapping
    with open(REPORTS_DIR / "stage16b_feature_manifest_2026-09-15.json", 'r') as f:
        manifest = json.load(f)
    
    # Create transaction mapping (simplified - use Stage 14 approach)
    transactions_sorted = transactions.sort_values(['partition', 'event_sequence'])
    
    # Get transactions for this set
    partition_map = {
        'validation': 'validation',
        'final_test': 'final_test',
        'independent': 'independent'
    }
    
    partition_name = partition_map.get(set_name, set_name)
    partition_txns = transactions_sorted[transactions_sorted['partition'] == partition_name]
    partition_txns = partition_txns.sort_values('event_sequence')
    
    # Create ground truth lookup
    gt_lookup = {gt['transaction_id']: gt for gt in ground_truth}
    
    # Get structuring scenarios
    structuring_scenarios = {
        'structuring': ['variable_fragment_burst', 'similar_amount_repetition', 
                       'distributed_same_day_fragmentation', 'variable_near_threshold_history'],
        'network': ['many_to_one_collection', 'one_to_many_dispersion', 
                  'reciprocal_relationship_cycle', 'wallet_pass_through'],
        'agent': ['agent_wallet_growth', 'agent_wallet_concentration', 
                 'agent_temporal_burst', 'agent_flow_imbalance']
    }
    
    domain_results = {}
    
    for domain, scenarios in structuring_scenarios.items():
        total_suspicious = 0
        true_positives = 0
        
        for txn_id, true_label, pred_label in zip(partition_txns['transaction_id'], y, y_pred):
            gt = gt_lookup.get(txn_id)
            if gt and gt.get('scenario_type') in scenarios and gt.get('ground_truth_label') == 1:
                total_suspicious += 1
                if pred_label == 1:
                    true_positives += 1
        
        if total_suspicious > 0:
            recall = true_positives / total_suspicious
        else:
            recall = 0.0
        
        domain_results[domain] = {
            'total_suspicious': total_suspicious,
            'true_positives': true_positives,
            'false_negatives': total_suspicious - true_positives,
            'suspicious_recall': recall
        }
        
        print(f"  {domain.capitalize()}: {true_positives}/{total_suspicious} = {recall:.4f}")
    
    print()
    
    return domain_results

# =============================================================================
# BASELINE COMPARISON
# =============================================================================

def compare_with_baseline(experimental_results, baseline_results):
    """Compare experimental model with baseline."""
    print("=" * 80)
    print("BASELINE COMPARISON")
    print("=" * 80)
    print()
    
    comparison = {}
    
    for set_name in ['final_test', 'independent']:
        print(f"{set_name.capitalize()} Comparison:")
        
        experimental_metrics = experimental_results[f'{set_name}_metrics']
        baseline_metrics = baseline_results[f'{set_name}_metrics']
        
        comparison[set_name] = {
            'macro_f1_diff': experimental_metrics['macro_f1'] - baseline_metrics['macro_f1'],
            'suspicious_recall_diff': experimental_metrics['suspicious_recall'] - baseline_metrics['suspicious_recall'],
            'suspicious_precision_diff': experimental_metrics['suspicious_precision'] - baseline_metrics['suspicious_precision'],
            'suspicious_f1_diff': experimental_metrics['suspicious_f1'] - baseline_metrics['suspicious_f1'],
            'roc_auc_diff': experimental_metrics['roc_auc'] - baseline_metrics['roc_auc'],
            'pr_auc_diff': experimental_metrics['pr_auc'] - baseline_metrics['pr_auc'],
            'fpr_diff': experimental_metrics['fpr'] - baseline_metrics['fpr']
        }
        
        for metric, diff in comparison[set_name].items():
            print(f"  {metric}: {diff:+.4f}")
        print()
    
    return comparison

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""
    
    # Create output directory
    STAGE16B_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load data
    matrices = load_experimental_matrices()
    baseline_results = load_baseline_results()
    ground_truth, transactions = load_ground_truth_and_transactions()
    
    # Train model
    model = train_model(matrices['X_train'], matrices['y_train'])
    
    # Select threshold
    threshold, val_macro_f1 = select_threshold(model, matrices['X_val'], matrices['y_val'])
    
    # Evaluate on all sets
    val_metrics = evaluate_model(model, threshold, matrices['X_val'], matrices['y_val'], "Validation")
    test_metrics = evaluate_model(model, threshold, matrices['X_test'], matrices['y_test'], "Final Test")
    independent_metrics = evaluate_model(model, threshold, matrices['X_independent'], matrices['y_independent'], "Independent")
    
    # Domain analysis
    test_domain = analyze_domain_performance(model, threshold, matrices['X_test'], matrices['y_test'], 
                                            ground_truth, transactions, "final_test")
    independent_domain = analyze_domain_performance(model, threshold, matrices['X_independent'], matrices['y_independent'], 
                                                    ground_truth, transactions, "independent")
    
    # Baseline comparison
    comparison = compare_with_baseline(
        {'final_test_metrics': test_metrics, 'independent_metrics': independent_metrics},
        baseline_results
    )
    
    # Compile results
    results = {
        'experiment_timestamp': datetime.now(timezone.utc).isoformat(),
        'dataset_version': DATASET_VERSION,
        'feature_count': 34,
        'model_config': BASELINE_CONFIG,
        'selected_threshold': float(threshold),
        'validation_metrics': val_metrics,
        'final_test_metrics': test_metrics,
        'independent_metrics': independent_metrics,
        'test_domain_analysis': test_domain,
        'independent_domain_analysis': independent_domain,
        'baseline_comparison': comparison,
        'baseline_threshold': baseline_results.get('threshold', 0.35)
    }
    
    # Save results
    with open(STAGE16B_DIR / 'stage16b_experiment_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save model
    model_artifact = {
        'model': model,
        'threshold': threshold,
        'feature_count': 34,
        'model_config': BASELINE_CONFIG,
        'random_seed': RANDOM_SEED
    }
    
    with open(STAGE16B_DIR / 'stage16b_expanded_model.pkl', 'wb') as f:
        pickle.dump(model_artifact, f)
    
    print(f"Results saved to: {STAGE16B_DIR / 'stage16b_experiment_results.json'}")
    print(f"Model saved to: {STAGE16B_DIR / 'stage16b_expanded_model.pkl'}")
    print()
    
    print("=" * 80)
    print("STAGE 16B ML EXPERIMENT COMPLETE")
    print("=" * 80)
    print()
    
    return results

if __name__ == "__main__":
    results = main()
    print("Stage 16B ML experiment complete.")
