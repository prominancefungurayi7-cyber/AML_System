"""
STAGE 22: Independent Generalization Test Evaluation

Evaluate Stage 21 model on independent dataset to test generalization.
"""

import pandas as pd
import numpy as np
import json
import joblib
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import random

RANDOM_SEED = 42
random.seed(RANDOM_SEED)


def load_model_and_data():
    """Load Stage 21 model and independent dataset."""
    print("Loading model and independent dataset...")
    
    model = joblib.load("aml_ai_model_stage21.pkl")
    label_encoder = joblib.load("aml_label_encoder_stage21.pkl")
    
    df = pd.read_csv("ml_stage22_independent_features.csv")
    
    with open("ml_stage22_independent_ground_truth.json") as f:
        gt = json.load(f)
    gt_dict = {g["transaction_id"]: g for g in gt}
    
    df['ground_truth_label'] = df['transaction_id'].map(
        lambda x: gt_dict.get(x, {}).get('ground_truth_label', 'normal')
    )
    
    print(f"Loaded {len(df)} transactions")
    return model, label_encoder, df


def evaluate_on_independent_dataset(model, label_encoder, df):
    """Evaluate model on independent dataset."""
    print("\nEvaluating on independent dataset...")
    
    # Prepare features
    non_feature_cols = ['transaction_id', 'sender_account', 'ground_truth_label', 'transaction_type_sequence_last_3']
    feature_cols = [col for col in df.columns if col not in non_feature_cols]
    
    # Ensure feature order matches training
    # Load training metadata to get feature order
    with open("aml_ai_model_stage21_meta.json") as f:
        metadata = json.load(f)
    
    training_features = metadata['feature_names']
    
    # Align features
    available_features = [f for f in training_features if f in df.columns]
    missing_features = [f for f in training_features if f not in df.columns]
    
    print(f"Available features: {len(available_features)}")
    print(f"Missing features: {len(missing_features)}")
    if missing_features:
        print(f"Missing: {missing_features}")
    
    # Add missing features with zeros
    for f in missing_features:
        df[f] = 0.0
    
    X = df[training_features].values
    y = label_encoder.transform(df['ground_truth_label'].values)
    
    # Predict
    y_pred = model.predict(X)
    
    # Calculate metrics
    accuracy = accuracy_score(y, y_pred)
    precision_macro = precision_score(y, y_pred, average='macro')
    recall_macro = recall_score(y, y_pred, average='macro')
    f1_macro = f1_score(y, y_pred, average='macro')
    precision_weighted = precision_score(y, y_pred, average='weighted')
    recall_weighted = recall_score(y, y_pred, average='weighted')
    f1_weighted = f1_score(y, y_pred, average='weighted')
    
    # Per-class metrics
    class_names = label_encoder.classes_
    precision_per_class = precision_score(y, y_pred, average=None)
    recall_per_class = recall_score(y, y_pred, average=None)
    f1_per_class = f1_score(y, y_pred, average=None)
    
    # Confusion matrix
    conf_matrix = confusion_matrix(y, y_pred)
    
    # False negatives and false positives per class
    fn_per_class = []
    fp_per_class = []
    for i in range(len(class_names)):
        fn = conf_matrix[i].sum() - conf_matrix[i, i]
        fp = conf_matrix[:, i].sum() - conf_matrix[i, i]
        fn_per_class.append(int(fn))
        fp_per_class.append(int(fp))
    
    result = {
        'accuracy': float(accuracy),
        'precision_macro': float(precision_macro),
        'recall_macro': float(recall_macro),
        'f1_macro': float(f1_macro),
        'precision_weighted': float(precision_weighted),
        'recall_weighted': float(recall_weighted),
        'f1_weighted': float(f1_weighted),
        'precision_per_class': [float(p) for p in precision_per_class],
        'recall_per_class': [float(r) for r in recall_per_class],
        'f1_per_class': [float(f) for f in f1_per_class],
        'confusion_matrix': conf_matrix.tolist(),
        'false_negatives_per_class': fn_per_class,
        'false_positives_per_class': fp_per_class,
        'class_names': list(class_names)
    }
    
    print(f"Accuracy: {result['accuracy']:.4f}")
    print(f"Macro F1: {result['f1_macro']:.4f}")
    print(f"Weighted F1: {result['f1_weighted']:.4f}")
    print(f"Confusion matrix:\n{result['confusion_matrix']}")
    
    return result


if __name__ == "__main__":
    print("=" * 80)
    print("STAGE 22: INDEPENDENT GENERALIZATION TEST")
    print("=" * 80)
    
    model, label_encoder, df = load_model_and_data()
    results = evaluate_on_independent_dataset(model, label_encoder, df)
    
    # Save results
    with open('ml_stage22_independent_evaluation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\nIndependent evaluation results saved")
