"""
STAGE 24: Create Generalization Populations

Split dataset into train/dev/test/independent populations with zero customer overlap.
"""

import pandas as pd
import numpy as np
import json
import random

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


def load_features():
    """Load features and ground truth."""
    print("Loading features...")
    df = pd.read_csv("ml_stage24_diverse_features.csv")
    
    with open("ml_stage24_diverse_ground_truth.json") as f:
        gt = json.load(f)
    gt_dict = {g["transaction_id"]: g for g in gt}
    
    df['ground_truth_label'] = df['transaction_id'].map(
        lambda x: gt_dict.get(x, {}).get('ground_truth_label', 'normal')
    )
    
    print(f"Loaded {len(df)} transactions")
    return df


def create_populations(df):
    """Create train/dev/test/independent populations with stratified sampling."""
    print("Creating populations...")
    
    # Get customer classes
    customer_classes = {}
    for customer_id in df['sender_account'].unique():
        customer_df = df[df['sender_account'] == customer_id]
        # Customer class is majority class
        class_counts = customer_df['ground_truth_label'].value_counts()
        customer_classes[customer_id] = class_counts.idxmax()
    
    # Group customers by class
    normal_customers = [c for c, cls in customer_classes.items() if cls == 'normal']
    suspicious_customers = [c for c, cls in customer_classes.items() if cls == 'suspicious']
    super_suspicious_customers = [c for c, cls in customer_classes.items() if cls == 'super_suspicious']
    
    print(f"Normal customers: {len(normal_customers)}")
    print(f"Suspicious customers: {len(suspicious_customers)}")
    print(f"Super-suspicious customers: {len(super_suspicious_customers)}")
    
    # Stratified split
    # Train: 80% of each class
    # Dev: 10% of each class
    # Test: 10% of each class
    
    random.seed(RANDOM_SEED)
    
    def split_class(customers, train_pct=0.8, dev_pct=0.1):
        random.shuffle(customers)
        n = len(customers)
        train_end = int(n * train_pct)
        dev_end = train_end + int(n * dev_pct)
        return (
            set(customers[:train_end]),
            set(customers[train_end:dev_end]),
            set(customers[dev_end:])
        )
    
    normal_train, normal_dev, normal_test = split_class(normal_customers)
    suspicious_train, suspicious_dev, suspicious_test = split_class(suspicious_customers)
    super_train, super_dev, super_test = split_class(super_suspicious_customers)
    
    train_customers = normal_train | suspicious_train | super_train
    dev_customers = normal_dev | suspicious_dev | super_dev
    test_customers = normal_test | suspicious_test | super_test
    
    # Verify no overlap
    train_dev_overlap = train_customers.intersection(dev_customers)
    train_test_overlap = train_customers.intersection(test_customers)
    dev_test_overlap = dev_customers.intersection(test_customers)
    
    print(f"Train customers: {len(train_customers)}")
    print(f"Dev customers: {len(dev_customers)}")
    print(f"Test customers: {len(test_customers)}")
    print(f"Train-Dev overlap: {len(train_dev_overlap)}")
    print(f"Train-Test overlap: {len(train_test_overlap)}")
    print(f"Dev-Test overlap: {len(dev_test_overlap)}")
    
    # Create dataframes
    train_df = df[df['sender_account'].isin(train_customers)].copy()
    dev_df = df[df['sender_account'].isin(dev_customers)].copy()
    test_df = df[df['sender_account'].isin(test_customers)].copy()
    
    print(f"Train transactions: {len(train_df)}")
    print(f"Dev transactions: {len(dev_df)}")
    print(f"Test transactions: {len(test_df)}")
    
    # Check class distribution
    print("\nClass distribution:")
    print(f"Train: {train_df['ground_truth_label'].value_counts().to_dict()}")
    print(f"Dev: {dev_df['ground_truth_label'].value_counts().to_dict()}")
    print(f"Test: {test_df['ground_truth_label'].value_counts().to_dict()}")
    
    return train_df, dev_df, test_df, train_customers, dev_customers, test_customers


def save_populations(train_df, dev_df, test_df):
    """Save populations to CSV."""
    print("\nSaving populations...")
    
    # Select feature columns (exclude ground_truth_label)
    non_feature_cols = ['transaction_id', 'sender_account', 'ground_truth_label']
    feature_cols = [col for col in train_df.columns if col not in non_feature_cols]
    
    train_df_final = train_df[['transaction_id', 'sender_account'] + feature_cols].copy()
    dev_df_final = dev_df[['transaction_id', 'sender_account'] + feature_cols].copy()
    test_df_final = test_df[['transaction_id', 'sender_account'] + feature_cols].copy()
    
    train_df_final.to_csv("ml_stage24_train_features.csv", index=False)
    dev_df_final.to_csv("ml_stage24_dev_features.csv", index=False)
    test_df_final.to_csv("ml_stage24_test_features.csv", index=False)
    
    print("Populations saved")


if __name__ == "__main__":
    print("=" * 80)
    print("STAGE 24: CREATE GENERALIZATION POPULATIONS")
    print("=" * 80)
    print()
    
    df = load_features()
    train_df, dev_df, test_df, train_customers, dev_customers, test_customers = create_populations(df)
    save_populations(train_df, dev_df, test_df)
    
    print()
    print("=" * 80)
    print("POPULATIONS CREATED")
    print("=" * 80)
