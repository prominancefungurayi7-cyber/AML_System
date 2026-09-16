"""
Train the final Stage 16B model and save as pickle for system integration.
"""

import csv
import json
import pickle
import numpy as np
from datetime import datetime
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder

print("=" * 80)
print("TRAINING FINAL STAGE 16B MODEL FOR SYSTEM INTEGRATION")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================================
# LOAD STAGE 16B FEATURES
# ============================================================================

print("Loading Stage 16B features...")
features = []
with open('ml_stage16b_features.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        features.append(row)

print(f"Loaded {len(features)} transactions")
print()

# ============================================================================
# LOAD STAGE 11 GROUND TRUTH
# ============================================================================

print("Loading Stage 11 ground truth...")
with open('ml_stage11_ground_truth.json', 'r') as f:
    ground_truth = json.load(f)

print(f"Loaded ground truth for {len(ground_truth)} transactions")
print()

# ============================================================================
# LOAD STAGE 16B FEATURE METADATA
# ============================================================================

with open('ml_stage16b_feature_metadata.json', 'r') as f:
    metadata = json.load(f)

feature_names = metadata['feature_names']

print(f"Candidate 18-feature set: {len(feature_names)} features")
print()

# ============================================================================
# MERGE FEATURES WITH GROUND TRUTH
# ============================================================================

print("Merging features with ground truth...")

gt_map = {str(gt['transaction_id']): gt for gt in ground_truth}

merged_data = []
for feature in features:
    tx_id = str(feature['transaction_id'])
    if tx_id in gt_map:
        merged = {**feature, **gt_map[tx_id]}
        merged_data.append(merged)

print(f"Merged {len(merged_data)} transactions")
print()

# ============================================================================
# PREPARE FEATURES AND LABELS
# ============================================================================

print("Preparing features and labels...")

X = np.array([[float(f[name]) for name in feature_names] for f in merged_data])
y = [f['ground_truth_label'] for f in merged_data]

label_encoder = LabelEncoder()
label_encoder.fit(y)
y_encoded = label_encoder.transform(y)

print(f"Feature matrix shape: {X.shape}")
print(f"Label classes: {label_encoder.classes_}")
print()

# ============================================================================
# TRAIN FINAL MODEL WITH APPROVED CONFIGURATION
# ============================================================================

print("Training final model with approved configuration...")
print("Configuration: learning_rate=0.01, max_depth=3, n_estimators=500, random_state=42")

model = GradientBoostingClassifier(
    learning_rate=0.01,
    max_depth=3,
    n_estimators=500,
    random_state=42
)

model.fit(X, y_encoded)

print("Model training complete")
print()

# ============================================================================
# SAVE MODEL AS PICKLE
# ============================================================================

print("Saving model as pickle file...")

with open('aml_ai_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("Model saved to aml_ai_model.pkl")
print()

# ============================================================================
# UPDATE MODEL METADATA
# ============================================================================

print("Updating model metadata...")

model_metadata = {
    "model_type": "GradientBoostingClassifier",
    "configuration": {
        "learning_rate": 0.01,
        "max_depth": 3,
        "n_estimators": 500,
        "random_state": 42
    },
    "feature_count": 18,
    "feature_names": feature_names,
    "label_classes": label_encoder.classes_.tolist(),
    "training_timestamp": datetime.now().isoformat(),
    "stage": "16B",
    "metrics": {
        "macro_f1": 0.5015,
        "weighted_f1": 0.7344,
        "suspicious_recall": 0.2176,
        "super_suspicious_recall": 0.2540
    },
    "notes": "Stage 16B frozen model with 18-feature set"
}

with open('aml_ai_model_meta.json', 'w') as f:
    json.dump(model_metadata, f, indent=2)

print("Model metadata updated in aml_ai_model_meta.json")
print()

# ============================================================================
# SAVE LABEL ENCODER FOR INFERENCE
# ============================================================================

print("Saving label encoder for inference...")

with open('aml_label_encoder.pkl', 'wb') as f:
    pickle.dump(label_encoder, f)

print("Label encoder saved to aml_label_encoder.pkl")
print()

print("=" * 80)
print("FINAL STAGE 16B MODEL TRAINING AND SAVING COMPLETE")
print("=" * 80)
print("Model saved as: aml_ai_model.pkl")
print("Metadata saved as: aml_ai_model_meta.json")
print("Label encoder saved as: aml_label_encoder.pkl")
print()
print("Ready for system integration")
