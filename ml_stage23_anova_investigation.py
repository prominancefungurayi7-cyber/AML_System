"""
STAGE 23: ANOVA Investigation

Investigate why Stage 22 reported F=0.00 for all features.
This conflicts with previous feature signal findings.
"""

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.feature_selection import f_classif, mutual_info_classif
import json

def load_stage21_data():
    """Load Stage 21 data."""
    df = pd.read_csv("ml_stage21_chapter1_features.csv")
    
    with open("ml_stage21_diversity_improved_ground_truth.json") as f:
        gt = json.load(f)
    gt_dict = {g["transaction_id"]: g for g in gt}
    
    df['ground_truth_label'] = df['transaction_id'].map(
        lambda x: gt_dict.get(x, {}).get('ground_truth_label', 'normal')
    )
    
    return df

def investigate_anova(df):
    """Investigate ANOVA calculation."""
    print("Investigating ANOVA issue...")
    
    # Prepare features
    non_feature_cols = ['transaction_id', 'sender_account', 'ground_truth_label', 'transaction_type_sequence_last_3']
    feature_cols = [col for col in df.columns if col not in non_feature_cols]
    
    print(f"Number of features: {len(feature_cols)}")
    print(f"Number of samples: {len(df)}")
    
    # Check for constant features
    constant_features = []
    for col in feature_cols:
        if df[col].nunique() <= 1:
            constant_features.append(col)
    
    print(f"Constant features: {len(constant_features)}")
    if constant_features:
        print(f"  {constant_features}")
    
    # Check for NaN values
    nan_features = []
    for col in feature_cols:
        if df[col].isna().any():
            nan_features.append((col, df[col].isna().sum()))
    
    print(f"Features with NaN: {len(nan_features)}")
    if nan_features:
        print(f"  {nan_features[:5]}")
    
    # Try ANOVA with sklearn f_classif
    print("\nTrying sklearn f_classif...")
    X = df[feature_cols].fillna(0).values
    y = df['ground_truth_label'].values
    
    try:
        f_scores, p_values = f_classif(X, y)
        print(f"sklearn f_classif succeeded")
        print(f"F-scores: {f_scores[:10]}")
        print(f"P-values: {p_values[:10]}")
        
        # Count significant features
        significant = sum(p_values < 0.05)
        print(f"Significant features (p < 0.05): {significant}")
    except Exception as e:
        print(f"sklearn f_classif failed: {e}")
    
    # Try manual ANOVA for a few features
    print("\nTrying manual ANOVA for selected features...")
    selected_features = feature_cols[:5]
    
    for col in selected_features:
        normal_vals = df[df['ground_truth_label'] == 'normal'][col].dropna().values
        suspicious_vals = df[df['ground_truth_label'] == 'suspicious'][col].dropna().values
        super_suspicious_vals = df[df['ground_truth_label'] == 'super_suspicious'][col].dropna().values
        
        print(f"\nFeature: {col}")
        print(f"  Normal: n={len(normal_vals)}, mean={np.mean(normal_vals):.4f}, std={np.std(normal_vals):.4f}")
        print(f"  Suspicious: n={len(suspicious_vals)}, mean={np.mean(suspicious_vals):.4f}, std={np.std(suspicious_vals):.4f}")
        print(f"  Super-suspicious: n={len(super_suspicious_vals)}, mean={np.mean(super_suspicious_vals):.4f}, std={np.std(super_suspicious_vals):.4f}")
        
        try:
            f_stat, p_val = stats.f_oneway(normal_vals, suspicious_vals, super_suspicious_vals)
            print(f"  F-statistic: {f_stat:.4f}")
            print(f"  P-value: {p_val:.4f}")
        except Exception as e:
            print(f"  ANOVA failed: {e}")
    
    # Try mutual information
    print("\nTrying mutual information...")
    try:
        mi_scores = mutual_info_classif(X, y, discrete_features=False, random_state=42)
        print(f"Mutual information scores: {mi_scores[:10]}")
        print(f"Mean MI: {np.mean(mi_scores):.4f}")
    except Exception as e:
        print(f"Mutual information failed: {e}")

if __name__ == "__main__":
    print("=" * 80)
    print("STAGE 23: ANOVA INVESTIGATION")
    print("=" * 80)
    
    df = load_stage21_data()
    investigate_anova(df)
