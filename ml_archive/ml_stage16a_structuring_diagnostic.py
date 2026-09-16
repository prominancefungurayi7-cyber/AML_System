"""
Stage 16A: Structuring Detection Diagnostic Audit

This script performs a comprehensive diagnostic analysis of why the frozen 30-feature representation
and Stage 14 Gradient Boosting model have substantially weaker performance on the Structuring domain
than on Network and Agent domains.

This is a READ-ONLY diagnostic research stage. No model retraining, feature modification, or data changes.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import warnings
import pickle
from scipy import stats
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

DATASET_VERSION = "ecocash_aml_synthetic_100k_v1"
DATA_DIR = Path("data") / DATASET_VERSION
FEATURE_DIR = DATA_DIR / "features"
REPORTS_DIR = Path("reports")
STAGE14_DIR = Path("ml") / "stage14"
STAGE16A_DIR = Path("ml") / "stage16a"

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# =============================================================================
# LOAD DATA AND MODEL
# =============================================================================

def load_stage13_matrices():
    """Load Stage 13 feature matrices."""
    print("=" * 80)
    print("STAGE 16A: STRUCTURING DETECTION DIAGNOSTIC AUDIT")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()
    
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
    
    print(f"  Feature names: {len(feature_names)}")
    print()
    
    return {
        'X_train': X_train, 'y_train': y_train,
        'X_val': X_val, 'y_val': y_val,
        'X_test': X_test, 'y_test': y_test,
        'X_independent': X_independent, 'y_independent': y_independent,
        'feature_names': feature_names
    }

def load_frozen_model():
    """Load frozen Stage 14 model."""
    print("Loading frozen Stage 14 model...")
    
    with open(STAGE14_DIR / "stage14_frozen_model.pkl", 'rb') as f:
        frozen_dict = pickle.load(f)
    
    model = frozen_dict['model']
    threshold = frozen_dict['threshold']
    
    print(f"  Model type: {type(model).__name__}")
    print(f"  Threshold: {threshold}")
    print()
    
    return model, threshold

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
# STRUCTURING FEATURE AUDIT
# =============================================================================

def get_structuring_features():
    """Define the six structuring features."""
    return [
        'structuring_prior_tx_count_1h',
        'structuring_prior_value_sum_24h',
        'structuring_same_day_prior_tx_count',
        'structuring_repeated_amount_ratio_7d',
        'structuring_amount_cluster_dispersion_7d',
        'structuring_near_threshold_history_ratio_7d'
    ]

def analyze_feature_distributions(X, y, feature_names, structuring_features):
    """Analyze distributions of structuring features."""
    print("=" * 80)
    print("FEATURE SIGNAL ANALYSIS")
    print("=" * 80)
    print()
    
    # Get feature indices
    feature_indices = {name: i for i, name in enumerate(feature_names)}
    structuring_indices = [feature_indices[f] for f in structuring_features]
    
    feature_analysis = {}
    
    for feature_name, idx in zip(structuring_features, structuring_indices):
        print(f"Analyzing: {feature_name}")
        
        # Extract feature values
        normal_values = X[y == 0, idx]
        suspicious_values = X[y == 1, idx]
        
        # Calculate statistics
        stats_dict = {
            'normal': {
                'mean': float(np.mean(normal_values)),
                'median': float(np.median(normal_values)),
                'std': float(np.std(normal_values)),
                'min': float(np.min(normal_values)),
                'max': float(np.max(normal_values)),
                'q25': float(np.percentile(normal_values, 25)),
                'q75': float(np.percentile(normal_values, 75)),
                'zero_ratio': float(np.mean(normal_values == 0))
            },
            'suspicious': {
                'mean': float(np.mean(suspicious_values)),
                'median': float(np.median(suspicious_values)),
                'std': float(np.std(suspicious_values)),
                'min': float(np.min(suspicious_values)),
                'max': float(np.max(suspicious_values)),
                'q25': float(np.percentile(suspicious_values, 25)),
                'q75': float(np.percentile(suspicious_values, 75)),
                'zero_ratio': float(np.mean(suspicious_values == 0))
            }
        }
        
        # Calculate separation metrics
        # Cohen's d (effect size)
        pooled_std = np.sqrt((stats_dict['normal']['std']**2 + stats_dict['suspicious']['std']**2) / 2)
        cohens_d = abs(stats_dict['normal']['mean'] - stats_dict['suspicious']['mean']) / pooled_std if pooled_std > 0 else 0
        
        # Overlap coefficient
        normal_hist, normal_bins = np.histogram(normal_values, bins=50, density=True)
        suspicious_hist, suspicious_bins = np.histogram(suspicious_values, bins=50, density=True)
        overlap = np.sum(np.minimum(normal_hist, suspicious_hist))
        
        stats_dict['separation'] = {
            'cohens_d': float(cohens_d),
            'overlap_coefficient': float(overlap),
            'mean_difference': float(stats_dict['suspicious']['mean'] - stats_dict['normal']['mean'])
        }
        
        feature_analysis[feature_name] = stats_dict
        
        print(f"  Normal mean: {stats_dict['normal']['mean']:.4f}, std: {stats_dict['normal']['std']:.4f}")
        print(f"  Suspicious mean: {stats_dict['suspicious']['mean']:.4f}, std: {stats_dict['suspicious']['std']:.4f}")
        print(f"  Cohen's d: {cohens_d:.4f}")
        print(f"  Overlap: {overlap:.4f}")
        print()
    
    return feature_analysis

def analyze_scenario_feature_alignment(X, y, ground_truth, transactions, feature_names, structuring_features):
    """Analyze which features should respond to which structuring scenarios."""
    print("=" * 80)
    print("SCENARIO-LEVEL DIAGNOSTIC")
    print("=" * 80)
    print()
    
    # Get structuring scenario families
    structuring_scenarios = [
        'variable_fragment_burst',
        'similar_amount_repetition',
        'distributed_same_day_fragmentation',
        'variable_near_threshold_history'
    ]
    
    # Create transaction mapping
    transactions_sorted = transactions.sort_values(['partition', 'event_sequence'])
    
    # Get feature indices
    feature_indices = {name: i for i, name in enumerate(feature_names)}
    structuring_indices = [feature_indices[f] for f in structuring_features]
    
    # Create ground truth lookup
    gt_lookup = {gt['transaction_id']: gt for gt in ground_truth}
    
    # Combine all data for analysis
    X_all = np.vstack([X['X_train'], X['X_val'], X['X_test'], X['X_independent']])
    y_all = np.hstack([X['y_train'], X['y_val'], X['y_test'], X['y_independent']])
    
    # Get transaction IDs in order
    all_txns = []
    for partition in ['train', 'validation', 'final_test', 'independent']:
        partition_txns = transactions_sorted[transactions_sorted['partition'] == partition]
        partition_txns = partition_txns.sort_values('event_sequence')
        all_txns.extend(partition_txns['transaction_id'].tolist())
    
    scenario_analysis = {}
    
    for scenario_type in structuring_scenarios:
        print(f"Analyzing scenario: {scenario_type}")
        
        # Find transactions belonging to this scenario
        scenario_mask = []
        for tx_id in all_txns:
            gt = gt_lookup.get(tx_id)
            if gt and gt.get('scenario_type') == scenario_type and gt.get('ground_truth_label') == 1:
                scenario_mask.append(True)
            else:
                scenario_mask.append(False)
        
        scenario_mask = np.array(scenario_mask)
        
        if np.sum(scenario_mask) == 0:
            print(f"  No transactions found for this scenario")
            print()
            continue
        
        # Extract feature values for this scenario
        scenario_values = X_all[scenario_mask][:, structuring_indices]
        normal_values = X_all[~scenario_mask][:, structuring_indices]
        
        scenario_stats = {}
        for i, feature_name in enumerate(structuring_features):
            scenario_mean = float(np.mean(scenario_values[:, i]))
            normal_mean = float(np.mean(normal_values[:, i]))
            
            scenario_stats[feature_name] = {
                'scenario_mean': scenario_mean,
                'normal_mean': normal_mean,
                'difference': scenario_mean - normal_mean,
                'signal_strength': abs(scenario_mean - normal_mean) / (np.std(normal_values[:, i]) + 1e-10)
            }
        
        scenario_analysis[scenario_type] = scenario_stats
        
        print(f"  Transaction count: {np.sum(scenario_mask)}")
        for feature_name in structuring_features:
            stats = scenario_stats[feature_name]
            print(f"    {feature_name}: diff={stats['difference']:.4f}, signal={stats['signal_strength']:.4f}")
        print()
    
    return scenario_analysis

# =============================================================================
# FALSE NEGATIVE ANALYSIS
# =============================================================================

def analyze_false_negatives(model, threshold, X, y, ground_truth, transactions, feature_names, structuring_features):
    """Analyze structuring false negatives."""
    print("=" * 80)
    print("FALSE-NEGATIVE ANALYSIS")
    print("=" * 80)
    print()
    
    # Get predictions
    y_proba = model.predict_proba(X)[:, 1]
    y_pred = (y_proba >= threshold).astype(int)
    
    # Create transaction mapping
    transactions_sorted = transactions.sort_values(['partition', 'event_sequence'])
    
    # Get feature indices
    feature_indices = {name: i for i, name in enumerate(feature_names)}
    structuring_indices = [feature_indices[f] for f in structuring_features]
    
    # Create ground truth lookup
    gt_lookup = {gt['transaction_id']: gt for gt in ground_truth}
    
    # Get transaction IDs
    all_txns = []
    for partition in ['train', 'validation', 'final_test', 'independent']:
        partition_txns = transactions_sorted[transactions_sorted['partition'] == partition]
        partition_txns = partition_txns.sort_values('event_sequence')
        all_txns.extend(partition_txns['transaction_id'].tolist())
    
    # Analyze structuring false negatives
    structuring_scenarios = [
        'variable_fragment_burst',
        'similar_amount_repetition',
        'distributed_same_day_fragmentation',
        'variable_near_threshold_history'
    ]
    
    fn_analysis = {}
    
    for scenario_type in structuring_scenarios:
        print(f"Analyzing false negatives for: {scenario_type}")
        
        # Find false negatives for this scenario
        scenario_fn_mask = []
        scenario_values = []
        
        for i, (tx_id, true_label, pred_label, prob) in enumerate(zip(all_txns, y, y_pred, y_proba)):
            gt = gt_lookup.get(tx_id)
            if (gt and gt.get('scenario_type') == scenario_type and 
                gt.get('ground_truth_label') == 1 and pred_label == 0):
                scenario_fn_mask.append(True)
                scenario_values.append({
                    'transaction_id': tx_id,
                    'probability': float(prob),
                    'features': X[i, structuring_indices].tolist()
                })
            else:
                scenario_fn_mask.append(False)
        
        scenario_fn_mask = np.array(scenario_fn_mask)
        
        if len(scenario_values) == 0:
            print(f"  No false negatives found for this scenario")
            print()
            continue
        
        # Analyze false negative characteristics
        fn_array = np.array([v['features'] for v in scenario_values])
        fn_probs = np.array([v['probability'] for v in scenario_values])
        
        fn_stats = {
            'count': len(scenario_values),
            'mean_probability': float(np.mean(fn_probs)),
            'median_probability': float(np.median(fn_probs)),
            'feature_means': [float(np.mean(fn_array[:, i])) for i in range(len(structuring_features))],
            'feature_medians': [float(np.median(fn_array[:, i])) for i in range(len(structuring_features))]
        }
        
        fn_analysis[scenario_type] = fn_stats
        
        print(f"  False negative count: {len(scenario_values)}")
        print(f"  Mean probability: {fn_stats['mean_probability']:.4f}")
        print(f"  Median probability: {fn_stats['median_probability']:.4f}")
        print()
    
    return fn_analysis

# =============================================================================
# NORMAL HARD-NEGATIVE ANALYSIS
# =============================================================================

def analyze_normal_hard_negatives(model, threshold, X, y, ground_truth, transactions, feature_names, structuring_features):
    """Analyze normal transactions that resemble structuring behaviour."""
    print("=" * 80)
    print("NORMAL HARD-NEGATIVE ANALYSIS")
    print("=" * 80)
    print()
    
    # Get predictions
    y_proba = model.predict_proba(X)[:, 1]
    y_pred = (y_proba >= threshold).astype(int)
    
    # Get feature indices
    feature_indices = {name: i for i, name in enumerate(feature_names)}
    structuring_indices = [feature_indices[f] for f in structuring_features]
    
    # Extract normal transactions with high structuring-like features
    normal_mask = (y == 0)
    normal_values = X[normal_mask][:, structuring_indices]
    
    # Find normal transactions with high values on structuring features
    hard_negative_analysis = {}
    
    for i, feature_name in enumerate(structuring_features):
        feature_values = normal_values[:, i]
        
        # Define "high" as top 10% of normal transactions
        threshold_90 = np.percentile(feature_values, 90)
        high_feature_mask = feature_values >= threshold_90
        
        high_feature_count = np.sum(high_feature_mask)
        
        # Among these, how many are correctly classified as normal?
        high_feature_predictions = y_pred[normal_mask][high_feature_mask]
        correctly_classified = np.sum(high_feature_predictions == 0)
        
        hard_negative_analysis[feature_name] = {
            'high_feature_count': int(high_feature_count),
            'correctly_classified': int(correctly_classified),
            'misclassified_as_suspicious': int(high_feature_count - correctly_classified),
            'feature_threshold': float(threshold_90),
            'misclassification_rate': float((high_feature_count - correctly_classified) / high_feature_count) if high_feature_count > 0 else 0
        }
        
        print(f"  {feature_name}:")
        print(f"    High-feature normal transactions: {high_feature_count}")
        print(f"    Correctly classified: {correctly_classified}")
        print(f"    Misclassified as suspicious: {high_feature_count - correctly_classified}")
        print(f"    Misclassification rate: {hard_negative_analysis[feature_name]['misclassification_rate']:.4f}")
        print()
    
    return hard_negative_analysis

# =============================================================================
# FEATURE CORRELATION ANALYSIS
# =============================================================================

def analyze_feature_correlations(X, y, feature_names, structuring_features):
    """Analyze correlations among structuring features and with other features."""
    print("=" * 80)
    print("FEATURE CORRELATION/REDUNDANCY ANALYSIS")
    print("=" * 80)
    print()
    
    # Get feature indices
    feature_indices = {name: i for i, name in enumerate(feature_names)}
    structuring_indices = [feature_indices[f] for f in structuring_features]
    
    # Calculate correlation matrix for structuring features
    structuring_values = X[:, structuring_indices]
    structuring_corr = np.corrcoef(structuring_values.T)
    
    print("Structuring feature correlations:")
    for i, feat1 in enumerate(structuring_features):
        for j, feat2 in enumerate(structuring_features):
            if i < j:
                corr = structuring_corr[i, j]
                print(f"  {feat1} vs {feat2}: {corr:.4f}")
    print()
    
    # Calculate correlations with non-structuring features
    non_structuring_features = [f for f in feature_names if f not in structuring_features]
    non_structuring_indices = [feature_indices[f] for f in non_structuring_features]
    
    print("Structuring features most correlated with non-structuring features:")
    cross_correlations = {}
    
    for struct_feat, struct_idx in zip(structuring_features, structuring_indices):
        correlations = []
        for non_struct_feat, non_struct_idx in zip(non_structuring_features, non_structuring_indices):
            corr = np.corrcoef(X[:, struct_idx], X[:, non_struct_idx])[0, 1]
            correlations.append((non_struct_feat, abs(corr)))
        
        correlations.sort(key=lambda x: x[1], reverse=True)
        top_3 = correlations[:3]
        cross_correlations[struct_feat] = [(f, float(c)) for f, c in top_3]
        
        print(f"  {struct_feat}:")
        for feat, corr in top_3:
            print(f"    {feat}: {corr:.4f}")
    print()
    
    return {
        'structuring_correlations': structuring_corr.tolist(),
        'top_cross_correlations': cross_correlations
    }

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""
    
    # Create output directory
    STAGE16A_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load data
    matrices = load_stage13_matrices()
    model, threshold = load_frozen_model()
    ground_truth, transactions = load_ground_truth_and_transactions()
    
    # Combine data for analysis
    X_all = np.vstack([matrices['X_train'], matrices['X_val'], matrices['X_test'], matrices['X_independent']])
    y_all = np.hstack([matrices['y_train'], matrices['y_val'], matrices['y_test'], matrices['y_independent']])
    
    # Get structuring features
    structuring_features = get_structuring_features()
    
    # Feature signal analysis
    feature_analysis = analyze_feature_distributions(X_all, y_all, matrices['feature_names'], structuring_features)
    
    # Scenario-level diagnostic
    scenario_analysis = analyze_scenario_feature_alignment(matrices, y_all, ground_truth, transactions, matrices['feature_names'], structuring_features)
    
    # False negative analysis (using independent set for evaluation)
    fn_analysis = analyze_false_negatives(model, threshold, matrices['X_independent'], matrices['y_independent'], ground_truth, transactions, matrices['feature_names'], structuring_features)
    
    # Normal hard-negative analysis
    hn_analysis = analyze_normal_hard_negatives(model, threshold, X_all, y_all, ground_truth, transactions, matrices['feature_names'], structuring_features)
    
    # Feature correlation analysis
    correlation_analysis = analyze_feature_correlations(X_all, y_all, matrices['feature_names'], structuring_features)
    
    # Compile results
    results = {
        'audit_timestamp': datetime.now(timezone.utc).isoformat(),
        'dataset_version': DATASET_VERSION,
        'structuring_features': structuring_features,
        'feature_signal_analysis': feature_analysis,
        'scenario_analysis': scenario_analysis,
        'false_negative_analysis': fn_analysis,
        'normal_hard_negative_analysis': hn_analysis,
        'correlation_analysis': correlation_analysis,
        'baseline_performance': {
            'structuring_recall': 0.3075,
            'network_recall': 0.7425,
            'agent_recall': 0.5875
        }
    }
    
    # Save results
    with open(STAGE16A_DIR / 'stage16a_diagnostic_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Diagnostic results saved to: {STAGE16A_DIR / 'stage16a_diagnostic_results.json'}")
    print()
    
    print("=" * 80)
    print("STAGE 16A COMPLETE")
    print("=" * 80)
    print()
    
    return results

if __name__ == "__main__":
    results = main()
    print("Stage 16A diagnostic audit complete.")
