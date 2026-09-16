"""
STAGE 21: Model Training with Improved Dataset and Chapter 1 Features

This script trains a Gradient Boosting model using:
1. Diversity-improved dataset (50+ super-suspicious customers)
2. Chapter 1 justified features (cross-border, sequence, structuring)
3. Same customer holdout methodology (160 train / 40 test)
4. Chronological split
"""

import pandas as pd
import numpy as np
import json
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)
import joblib
import random
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Set random seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


def load_data(
    features_file: str = "ml_stage21_chapter1_features.csv",
    ground_truth_file: str = "ml_stage21_diversity_improved_ground_truth.json"
) -> Tuple[pd.DataFrame, Dict[int, Dict]]:
    """Load features and ground truth."""
    print(f"Loading features from {features_file}...")
    df = pd.read_csv(features_file)
    
    print(f"Loading ground truth from {ground_truth_file}...")
    with open(ground_truth_file, 'r') as f:
        ground_truth = json.load(f)
    
    # Convert ground truth to dict by transaction_id
    ground_truth_dict = {gt["transaction_id"]: gt for gt in ground_truth}
    
    print(f"Loaded {len(df)} transactions with ground truth")
    return df, ground_truth_dict


def merge_features_with_ground_truth(
    df: pd.DataFrame,
    ground_truth_dict: Dict[int, Dict]
) -> pd.DataFrame:
    """Merge features with ground truth labels."""
    print("Merging features with ground truth...")
    
    # Add ground truth label
    df['ground_truth_label'] = df['transaction_id'].map(
        lambda x: ground_truth_dict.get(x, {}).get('ground_truth_label', 'normal')
    )
    
    # Check for missing labels
    missing_labels = df[df['ground_truth_label'].isna()]
    if len(missing_labels) > 0:
        print(f"Warning: {len(missing_labels)} transactions missing ground truth")
    
    print(f"Merged {len(df)} transactions with labels")
    return df


def customer_holdout_split(
    df: pd.DataFrame,
    train_customers: int = 160,
    test_customers: int = 40,
    random_seed: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Perform customer-level holdout split."""
    print(f"Customer holdout split: {train_customers} train / {test_customers} test")
    
    # Get unique customers
    unique_customers = df['sender_account'].unique()
    print(f"Total unique customers: {len(unique_customers)}")
    
    # Randomly select train and test customers
    random.seed(random_seed)
    shuffled_customers = list(unique_customers)
    random.shuffle(shuffled_customers)
    
    train_customer_set = set(shuffled_customers[:train_customers])
    test_customer_set = set(shuffled_customers[train_customers:train_customers + test_customers])
    
    # Check for overlap
    overlap = train_customer_set.intersection(test_customer_set)
    if overlap:
        print(f"ERROR: Customer overlap detected: {overlap}")
        raise ValueError("Customer overlap between train and test")
    
    # Split data
    train_df = df[df['sender_account'].isin(train_customer_set)].copy()
    test_df = df[df['sender_account'].isin(test_customer_set)].copy()
    
    print(f"Train transactions: {len(train_df)}")
    print(f"Test transactions: {len(test_df)}")
    print(f"Customer overlap: {len(overlap)}")
    
    return train_df, test_df


def chronological_split(
    df: pd.DataFrame,
    train_ratio: float = 0.8
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Perform chronological split."""
    print(f"Chronological split: {train_ratio:.0%} train")
    
    # Sort by timestamp
    df_sorted = df.sort_values('timestamp').copy()
    
    # Split chronologically
    split_idx = int(len(df_sorted) * train_ratio)
    train_df = df_sorted.iloc[:split_idx].copy()
    test_df = df_sorted.iloc[split_idx:].copy()
    
    print(f"Train transactions: {len(train_df)}")
    print(f"Test transactions: {len(test_df)}")
    
    return train_df, test_df


def prepare_features_and_labels(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, LabelEncoder, List[str]]:
    """Prepare feature matrices and labels."""
    print("Preparing features and labels...")
    
    # Identify feature columns (exclude non-feature columns)
    non_feature_cols = ['transaction_id', 'sender_account', 'ground_truth_label']
    feature_cols = [col for col in train_df.columns if col not in non_feature_cols]
    
    # Handle categorical features (transaction_type_sequence_last_3)
    # For now, we'll drop it or encode it
    if 'transaction_type_sequence_last_3' in feature_cols:
        feature_cols.remove('transaction_type_sequence_last_3')
        print("Dropped transaction_type_sequence_last_3 (categorical)")
    
    print(f"Feature columns: {len(feature_cols)}")
    
    # Prepare feature matrices
    X_train = train_df[feature_cols].values
    X_test = test_df[feature_cols].values
    
    # Prepare labels
    y_train = train_df['ground_truth_label'].values
    y_test = test_df['ground_truth_label'].values
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_train_encoded = label_encoder.fit_transform(y_train)
    y_test_encoded = label_encoder.transform(y_test)
    
    print(f"Label classes: {list(label_encoder.classes_)}")
    print(f"Feature matrix shape: {X_train.shape}")
    print(f"Test samples: {len(X_test)}")
    
    return X_train, X_test, y_train_encoded, y_test_encoded, label_encoder, feature_cols


def train_gradient_boosting(
    X_train: np.ndarray,
    y_train: np.ndarray,
    random_seed: int = 42
) -> GradientBoostingClassifier:
    """Train Gradient Boosting classifier."""
    print("Training Gradient Boosting classifier...")
    
    model = GradientBoostingClassifier(
        learning_rate=0.01,
        max_depth=3,
        n_estimators=500,
        random_state=random_seed
    )
    
    model.fit(X_train, y_train)
    
    print("Model training complete")
    return model


def evaluate_model(
    model: GradientBoostingClassifier,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    label_encoder: LabelEncoder
) -> Dict[str, Any]:
    """Evaluate model performance."""
    print("Evaluating model...")
    
    # Predictions
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    # Metrics
    train_accuracy = accuracy_score(y_train, y_train_pred)
    test_accuracy = accuracy_score(y_test, y_test_pred)
    
    # Macro metrics
    test_precision_macro = precision_score(y_test, y_test_pred, average='macro')
    test_recall_macro = recall_score(y_test, y_test_pred, average='macro')
    test_f1_macro = f1_score(y_test, y_test_pred, average='macro')
    
    # Weighted metrics
    test_precision_weighted = precision_score(y_test, y_test_pred, average='weighted')
    test_recall_weighted = recall_score(y_test, y_test_pred, average='weighted')
    test_f1_weighted = f1_score(y_test, y_test_pred, average='weighted')
    
    # Per-class metrics
    class_names = label_encoder.classes_
    test_precision_per_class = precision_score(y_test, y_test_pred, average=None, labels=range(len(class_names)))
    test_recall_per_class = recall_score(y_test, y_test_pred, average=None, labels=range(len(class_names)))
    test_f1_per_class = f1_score(y_test, y_test_pred, average=None, labels=range(len(class_names)))
    
    # Confusion matrix
    conf_matrix = confusion_matrix(y_test, y_test_pred)
    
    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring='f1_macro')
    cv_mean = cv_scores.mean()
    cv_std = cv_scores.std()
    
    # Calculate false negatives for suspicious and super_suspicious
    suspicious_idx = list(class_names).index('suspicious')
    super_suspicious_idx = list(class_names).index('super_suspicious')
    
    suspicious_fn = conf_matrix[suspicious_idx].sum() - conf_matrix[suspicious_idx, suspicious_idx]
    super_suspicious_fn = conf_matrix[super_suspicious_idx].sum() - conf_matrix[super_suspicious_idx, super_suspicious_idx]
    
    results = {
        'train_accuracy': float(train_accuracy),
        'test_accuracy': float(test_accuracy),
        'test_precision_macro': float(test_precision_macro),
        'test_recall_macro': float(test_recall_macro),
        'test_f1_macro': float(test_f1_macro),
        'test_precision_weighted': float(test_precision_weighted),
        'test_recall_weighted': float(test_recall_weighted),
        'test_f1_weighted': float(test_f1_weighted),
        'test_precision_per_class': [float(p) for p in test_precision_per_class],
        'test_recall_per_class': [float(r) for r in test_recall_per_class],
        'test_f1_per_class': [float(f) for f in test_f1_per_class],
        'confusion_matrix': conf_matrix.tolist(),
        'cv_mean': float(cv_mean),
        'cv_std': float(cv_std),
        'cv_to_test_gap': float(cv_mean - test_f1_macro),
        'suspicious_false_negatives': int(suspicious_fn),
        'super_suspicious_false_negatives': int(super_suspicious_fn),
        'class_names': list(class_names)
    }
    
    print(f"Train Accuracy: {train_accuracy:.4f}")
    print(f"Test Accuracy: {test_accuracy:.4f}")
    print(f"Test Macro F1: {test_f1_macro:.4f}")
    print(f"Test Weighted F1: {test_f1_weighted:.4f}")
    print(f"CV Macro F1: {cv_mean:.4f} (+/- {cv_std:.4f})")
    print(f"CV-to-Test Gap: {cv_mean - test_f1_macro:.4f}")
    print(f"Suspicious False Negatives: {suspicious_fn}")
    print(f"Super-Suspicious False Negatives: {super_suspicious_fn}")
    
    return results


def save_model(
    model: GradientBoostingClassifier,
    label_encoder: LabelEncoder,
    feature_cols: List[str],
    results: Dict[str, Any],
    model_file: str = "aml_ai_model_stage21.pkl",
    encoder_file: str = "aml_label_encoder_stage21.pkl",
    metadata_file: str = "aml_ai_model_stage21_meta.json"
):
    """Save model and metadata."""
    print("Saving model and metadata...")
    
    # Save model
    joblib.dump(model, model_file)
    
    # Save label encoder
    joblib.dump(label_encoder, encoder_file)
    
    # Save metadata
    metadata = {
        'model_type': 'GradientBoostingClassifier',
        'model_params': model.get_params(),
        'feature_count': len(feature_cols),
        'feature_names': feature_cols,
        'label_classes': list(label_encoder.classes_),
        'random_seed': RANDOM_SEED,
        'results': results,
        'timestamp': datetime.now().isoformat()
    }
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Model saved to {model_file}")
    print(f"Label encoder saved to {encoder_file}")
    print(f"Metadata saved to {metadata_file}")


def save_results(results: Dict[str, Any], results_file: str = "ml_stage21_training_results.json"):
    """Save training results."""
    print(f"Saving results to {results_file}...")
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("Results saved")


if __name__ == "__main__":
    print("=" * 80)
    print("STAGE 21: MODEL TRAINING WITH IMPROVED DATASET AND CHAPTER 1 FEATURES")
    print("=" * 80)
    print()
    
    # Load data
    df, ground_truth_dict = load_data()
    
    # Merge with ground truth
    df = merge_features_with_ground_truth(df, ground_truth_dict)
    
    # Customer holdout split
    train_df, test_df = customer_holdout_split(df, train_customers=160, test_customers=40)
    
    # Note: Chronological split is preserved from dataset generation
    # No additional chronological split needed here
    
    # Prepare features and labels
    X_train, X_test, y_train, y_test, label_encoder, feature_cols = prepare_features_and_labels(
        train_df, test_df
    )
    
    # Train model
    model = train_gradient_boosting(X_train, y_train)
    
    # Evaluate model
    results = evaluate_model(model, X_train, y_train, X_test, y_test, label_encoder)
    
    # Save model and results
    save_model(model, label_encoder, feature_cols, results)
    save_results(results)
    
    print()
    print("=" * 80)
    print("MODEL TRAINING COMPLETE")
    print("=" * 80)
