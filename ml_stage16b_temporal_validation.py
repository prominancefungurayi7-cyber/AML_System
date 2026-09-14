"""
STAGE 16B-3: SECONDARY TEMPORAL VALIDATION

Perform temporal validation as secondary evaluation.
"""

import csv
import json
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import f1_score
from sklearn.preprocessing import LabelEncoder

print("=" * 80)
print("STAGE 16B-3: SECONDARY TEMPORAL VALIDATION")
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
# LOAD STAGE 11 DATASET FOR TIMESTAMPS
# ============================================================================

print("Loading Stage 11 dataset for timestamps...")
dataset = []
with open('ml_stage11_dataset.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        dataset.append(row)

print(f"Loaded {len(dataset)} transactions")
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
# MERGE FEATURES WITH GROUND TRUTH AND TIMESTAMPS
# ============================================================================

print("Merging features with ground truth and timestamps...")

gt_map = {str(gt['transaction_id']): gt for gt in ground_truth}
dataset_map = {str(d['transaction_id']): d for d in dataset}

merged_data = []
for feature in features:
    tx_id = str(feature['transaction_id'])
    if tx_id in gt_map and tx_id in dataset_map:
        merged = {**feature, **gt_map[tx_id], **dataset_map[tx_id]}
        merged_data.append(merged)

print(f"Merged {len(merged_data)} transactions")
print()

# ============================================================================
# TEMPORAL SPLIT (80% TRAIN / 20% TEST BY TRANSACTION TIME)
# ============================================================================

print("Temporal split (80% train / 20% test by transaction time)...")

# Sort by timestamp
merged_data.sort(key=lambda x: x['timestamp'])

split_index = int(len(merged_data) * 0.8)
train_data = merged_data[:split_index]
test_data = merged_data[split_index:]

print(f"Train transactions: {len(train_data)}")
print(f"Test transactions: {len(test_data)}")
print()

# ============================================================================
# PREPARE FEATURES AND LABELS
# ============================================================================

print("Preparing features and labels...")

X_train = np.array([[float(f[name]) for name in feature_names] for f in train_data])
X_test = np.array([[float(f[name]) for name in feature_names] for f in test_data])

y_train = [f['ground_truth_label'] for f in train_data]
y_test = [f['ground_truth_label'] for f in test_data]

label_encoder = LabelEncoder()
label_encoder.fit(y_train + y_test)
y_train_encoded = label_encoder.transform(y_train)
y_test_encoded = label_encoder.transform(y_test)

print(f"Feature matrix shape: {X_train.shape}")
print(f"Label classes: {label_encoder.classes_}")
print()

# ============================================================================
# TRAIN MODELS WITH BEST CONFIGURATIONS FROM PRIMARY VALIDATION
# ============================================================================

print("Training models with best configurations from primary validation...")

# Best RF config from primary validation
rf_config = {'max_depth': 6, 'min_samples_split': 20, 'min_samples_leaf': 10, 'random_state': 42, 'n_jobs': -1}
rf = RandomForestClassifier(n_estimators=100, **rf_config)
rf.fit(X_train, y_train_encoded)

rf_train_pred = rf.predict(X_train)
rf_test_pred = rf.predict(X_test)

rf_train_macro_f1 = f1_score(y_train_encoded, rf_train_pred, average='macro')
rf_test_macro_f1 = f1_score(y_test_encoded, rf_test_pred, average='macro')

print(f"Random Forest:")
print(f"  Train Macro F1: {rf_train_macro_f1:.4f}")
print(f"  Test Macro F1: {rf_test_macro_f1:.4f}")
print(f"  Train/Test Gap: {rf_train_macro_f1 - rf_test_macro_f1:.4f}")
print()

# Best GB config from primary validation
gb_config = {'learning_rate': 0.01, 'max_depth': 3, 'n_estimators': 500, 'random_state': 42}
gb = GradientBoostingClassifier(**gb_config)
gb.fit(X_train, y_train_encoded)

gb_train_pred = gb.predict(X_train)
gb_test_pred = gb.predict(X_test)

gb_train_macro_f1 = f1_score(y_train_encoded, gb_train_pred, average='macro')
gb_test_macro_f1 = f1_score(y_test_encoded, gb_test_pred, average='macro')

print(f"Gradient Boosting:")
print(f"  Train Macro F1: {gb_train_macro_f1:.4f}")
print(f"  Test Macro F1: {gb_test_macro_f1:.4f}")
print(f"  Train/Test Gap: {gb_train_macro_f1 - gb_test_macro_f1:.4f}")
print()

# ============================================================================
# SAVE TEMPORAL VALIDATION RESULTS
# ============================================================================

results = {
    "timestamp": datetime.now().isoformat(),
    "validation_type": "temporal",
    "split_method": "80% train / 20% test by transaction time",
    "train_transactions": len(train_data),
    "test_transactions": len(test_data),
    "random_forest": {
        "config": rf_config,
        "train_macro_f1": rf_train_macro_f1,
        "test_macro_f1": rf_test_macro_f1,
        "train_test_gap": rf_train_macro_f1 - rf_test_macro_f1
    },
    "gradient_boosting": {
        "config": gb_config,
        "train_macro_f1": gb_train_macro_f1,
        "test_macro_f1": gb_test_macro_f1,
        "train_test_gap": gb_train_macro_f1 - gb_test_macro_f1
    },
    "note": "Temporal split can contain customer overlap - this is a known limitation"
}

with open('ml_stage16b_temporal_validation_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("=" * 80)
print("SECONDARY TEMPORAL VALIDATION COMPLETE")
print("=" * 80)
print("Results saved to ml_stage16b_temporal_validation_results.json")
print()
print("NOTE: Temporal split can contain customer overlap - this is a known limitation")
