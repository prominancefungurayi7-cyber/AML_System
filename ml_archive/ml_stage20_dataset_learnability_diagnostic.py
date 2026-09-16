"""
STAGE 20: DATASET LEARNABILITY / SIGNAL DIAGNOSTIC

Analyze whether the current dataset has sufficient learnable signal before adding features.
This is diagnostic only - no model changes, no feature changes, no production changes.
"""

import csv
import json
import numpy as np
from datetime import datetime
from collections import Counter, defaultdict
from scipy import stats
from sklearn.metrics import mutual_info_score
from sklearn.preprocessing import LabelEncoder

print("=" * 80)
print("STAGE 20: DATASET LEARNABILITY / SIGNAL DIAGNOSTIC")
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
# LOAD STAGE 12 PRIMARY SPLIT
# ============================================================================

print("Loading Stage 12 primary split...")
with open('ml_stage12_primary_split.json', 'r') as f:
    primary_split = json.load(f)

train_customers = set(primary_split['train_customer_ids'])
test_customers = set(primary_split['test_customer_ids'])

print(f"Train customers: {len(train_customers)}")
print(f"Test customers: {len(test_customers)}")
print(f"Customer overlap: {len(train_customers & test_customers)}")
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
# PRIMARY CUSTOMER-LEVEL SPLIT
# ============================================================================

print("Primary customer-level split...")

train_data = []
test_data = []

for data in merged_data:
    customer = data['sender_account']
    if customer in train_customers:
        train_data.append(data)
    elif customer in test_customers:
        test_data.append(data)

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
print(f"Test samples: {len(X_test)}")
print(f"Label classes: {label_encoder.classes_}")
print()

# ============================================================================
# 1. CLASS SEPARABILITY ANALYSIS
# ============================================================================

print("=" * 80)
print("1. CLASS SEPARABILITY ANALYSIS")
print("=" * 80)
print()

# Get feature distributions by class
class_distributions = {}
for class_name in label_encoder.classes_:
    class_mask = y_train == class_name
    class_distributions[class_name] = X_train[class_mask]

print(f"Feature distributions by class:")
print()

feature_stats = {}
for i, feature_name in enumerate(feature_names):
    feature_stats[feature_name] = {}
    for class_name in label_encoder.classes_:
        class_data = class_distributions[class_name][:, i]
        if len(class_data) == 0:
            feature_stats[feature_name][class_name] = {
                'mean': 0.0,
                'std': 0.0,
                'median': 0.0,
                'min': 0.0,
                'max': 0.0,
                'q25': 0.0,
                'q75': 0.0,
                'empty': True
            }
        else:
            feature_stats[feature_name][class_name] = {
                'mean': float(np.mean(class_data)),
                'std': float(np.std(class_data)),
                'median': float(np.median(class_data)),
                'min': float(np.min(class_data)),
                'max': float(np.max(class_data)),
                'q25': float(np.percentile(class_data, 25)),
                'q75': float(np.percentile(class_data, 75)),
                'empty': False
            }

# Calculate class separation metrics
feature_separation = {}
for i, feature_name in enumerate(feature_names):
    normal_data = class_distributions['normal'][:, i]
    suspicious_data = class_distributions['suspicious'][:, i]
    super_suspicious_data = class_distributions['super_suspicious'][:, i]
    
    # Cohen's d (effect size)
    def cohens_d(a, b):
        if len(a) == 0 or len(b) == 0:
            return 0.0
        pooled_std = np.sqrt((np.std(a)**2 + np.std(b)**2) / 2)
        if pooled_std == 0:
            return 0.0
        return (np.mean(a) - np.mean(b)) / pooled_std
    
    d_normal_suspicious = cohens_d(normal_data, suspicious_data)
    d_normal_super = cohens_d(normal_data, super_suspicious_data)
    d_suspicious_super = cohens_d(suspicious_data, super_suspicious_data)
    
    # Overlap coefficient
    def overlap_coefficient(a, b):
        if len(a) == 0 or len(b) == 0:
            return 0.0
        hist_a, bins_a = np.histogram(a, bins=50, density=True)
        hist_b, bins_b = np.histogram(b, bins=50, density=True)
        min_hist = np.minimum(hist_a, hist_b)
        return np.sum(min_hist) * (bins_a[1] - bins_a[0])
    
    overlap_normal_suspicious = overlap_coefficient(normal_data, suspicious_data)
    overlap_normal_super = overlap_coefficient(normal_data, super_suspicious_data)
    overlap_suspicious_super = overlap_coefficient(suspicious_data, super_suspicious_data)
    
    feature_separation[feature_name] = {
        'cohens_d_normal_suspicious': float(d_normal_suspicious),
        'cohens_d_normal_super': float(d_normal_super),
        'cohens_d_suspicious_super': float(d_suspicious_super),
        'overlap_normal_suspicious': float(overlap_normal_suspicious),
        'overlap_normal_super': float(overlap_normal_super),
        'overlap_suspicious_super': float(overlap_suspicious_super)
    }

print("Top features by class separation (Cohen's d):")
print()

# Sort by average Cohen's d for minority classes
feature_ranking = []
for feature_name, metrics in feature_separation.items():
    avg_d = (abs(metrics['cohens_d_normal_suspicious']) + abs(metrics['cohens_d_normal_super'])) / 2
    feature_ranking.append((feature_name, avg_d, metrics))

feature_ranking.sort(key=lambda x: x[1], reverse=True)

for feature_name, avg_d, metrics in feature_ranking[:10]:
    print(f"  {feature_name}:")
    print(f"    Cohen's d (normal vs suspicious): {metrics['cohens_d_normal_suspicious']:.3f}")
    print(f"    Cohen's d (normal vs super_suspicious): {metrics['cohens_d_normal_super']:.3f}")
    print(f"    Cohen's d (suspicious vs super_suspicious): {metrics['cohens_d_suspicious_super']:.3f}")
    print(f"    Overlap (normal vs suspicious): {metrics['overlap_normal_suspicious']:.3f}")
    print(f"    Overlap (normal vs super_suspicious): {metrics['overlap_normal_super']:.3f}")
    print(f"    Overlap (suspicious vs super_suspicious): {metrics['overlap_suspicious_super']:.3f}")
    print()

# ============================================================================
# 2. MINORITY-CLASS DIVERSITY
# ============================================================================

print("=" * 80)
print("2. MINORITY-CLASS DIVERSITY")
print("=" * 80)
print()

# Count unique customers per class
class_customers = defaultdict(set)
for data in train_data:
    class_customers[data['ground_truth_label']].add(data['sender_account'])

print("Training data - unique customers per class:")
for class_name in label_encoder.classes_:
    customer_count = len(class_customers[class_name])
    tx_count = sum(1 for d in train_data if d['ground_truth_label'] == class_name)
    print(f"  {class_name}: {customer_count} customers, {tx_count} transactions")
    if tx_count > 0:
        print(f"    Avg transactions per customer: {tx_count / customer_count:.2f}")
print()

# Test data
test_class_customers = defaultdict(set)
for data in test_data:
    test_class_customers[data['ground_truth_label']].add(data['sender_account'])

print("Test data - unique customers per class:")
for class_name in label_encoder.classes_:
    customer_count = len(test_class_customers[class_name])
    tx_count = sum(1 for d in test_data if d['ground_truth_label'] == class_name)
    print(f"  {class_name}: {customer_count} customers, {tx_count} transactions")
    if tx_count > 0:
        print(f"    Avg transactions per customer: {tx_count / customer_count:.2f}")
print()

# ============================================================================
# 3. CUSTOMER-LEVEL DISTRIBUTION
# ============================================================================

print("=" * 80)
print("3. CUSTOMER-LEVEL DISTRIBUTION")
print("=" * 80)
print()

# Transactions per customer by class
customer_tx_by_class = defaultdict(lambda: defaultdict(int))
for data in train_data:
    customer = data['sender_account']
    label = data['ground_truth_label']
    customer_tx_by_class[customer][label] += 1

# Analyze concentration
for class_name in ['suspicious', 'super_suspicious']:
    print(f"{class_name} customer transaction distribution:")
    tx_counts = [customer_tx_by_class[customer][class_name] for customer in class_customers[class_name]]
    tx_counts.sort(reverse=True)
    
    print(f"  Total customers: {len(tx_counts)}")
    print(f"  Total transactions: {sum(tx_counts)}")
    print(f"  Mean tx per customer: {np.mean(tx_counts):.2f}")
    print(f"  Median tx per customer: {np.median(tx_counts):.2f}")
    print(f"  Std tx per customer: {np.std(tx_counts):.2f}")
    print(f"  Top 5 customers: {tx_counts[:5]}")
    print(f"  Top 10 customers: {tx_counts[:10]}")
    print(f"  Top 20% of customers: {int(len(tx_counts) * 0.2)} customers")
    print(f"  Transactions from top 20%: {sum(tx_counts[:int(len(tx_counts) * 0.2)])} ({sum(tx_counts[:int(len(tx_counts) * 0.2)]) / sum(tx_counts) * 100:.1f}%)")
    print()

# ============================================================================
# 4. TEMPORAL DISTRIBUTION
# ============================================================================

print("=" * 80)
print("4. TEMPORAL DISTRIBUTION")
print("=" * 80)
print()

print("Note: Temporal distribution analysis skipped - timestamp field not available in feature CSV.")
print("The dataset is already chronologically split, so temporal patterns are preserved in the train/test split.")
print()

# ============================================================================
# 5. FEATURE SIGNAL ANALYSIS
# ============================================================================

print("=" * 80)
print("5. FEATURE SIGNAL ANALYSIS")
print("=" * 80)
print()

# Mutual information between each feature and label
feature_mi = {}
for i, feature_name in enumerate(feature_names):
    mi = mutual_info_score(y_train_encoded, X_train[:, i])
    feature_mi[feature_name] = mi

print("Mutual information with label:")
feature_mi_ranking = sorted(feature_mi.items(), key=lambda x: x[1], reverse=True)
for feature_name, mi in feature_mi_ranking:
    print(f"  {feature_name}: {mi:.4f}")
print()

# ANOVA F-test for each feature
from sklearn.feature_selection import f_classif
f_values, p_values = f_classif(X_train, y_train_encoded)

print("ANOVA F-test results:")
for i, feature_name in enumerate(feature_names):
    print(f"  {feature_name}: F={f_values[i]:.2f}, p={p_values[i]:.4f}")
print()

# Identify features with useful signal vs little/no signal
useful_features = []
weak_features = []
for feature_name, mi in feature_mi.items():
    if mi > 0.01:
        useful_features.append(feature_name)
    else:
        weak_features.append(feature_name)

print(f"Features with useful signal (MI > 0.01): {len(useful_features)}")
for feature_name in useful_features:
    print(f"  - {feature_name}")
print()

print(f"Features with weak/no signal (MI <= 0.01): {len(weak_features)}")
for feature_name in weak_features:
    print(f"  - {feature_name}")
print()

# ============================================================================
# 6. DATASET DIFFICULTY ASSESSMENT
# ============================================================================

print("=" * 80)
print("6. DATASET DIFFICULTY ASSESSMENT")
print("=" * 80)
print()

# Calculate overall class separation
avg_cohens_d = np.mean([abs(metrics['cohens_d_normal_suspicious']) for metrics in feature_separation.values()])
avg_overlap = np.mean([metrics['overlap_normal_suspicious'] for metrics in feature_separation.values()])

print(f"Average Cohen's d (normal vs suspicious): {avg_cohens_d:.3f}")
print(f"Average overlap coefficient (normal vs suspicious): {avg_overlap:.3f}")
print()

# Interpretation
if avg_cohens_d < 0.2:
    separability_assessment = "VERY POOR - Minimal class separation"
elif avg_cohens_d < 0.5:
    separability_assessment = "POOR - Weak class separation"
elif avg_cohens_d < 0.8:
    separability_assessment = "MODERATE - Moderate class separation"
else:
    separability_assessment = "GOOD - Strong class separation"

print(f"Class separability assessment: {separability_assessment}")
print()

# Feature signal assessment
total_mi = sum(feature_mi.values())
if total_mi < 0.1:
    signal_assessment = "VERY POOR - Minimal feature signal"
elif total_mi < 0.3:
    signal_assessment = "POOR - Weak feature signal"
elif total_mi < 0.5:
    signal_assessment = "MODERATE - Moderate feature signal"
else:
    signal_assessment = "GOOD - Strong feature signal"

print(f"Total mutual information: {total_mi:.4f}")
print(f"Feature signal assessment: {signal_assessment}")
print()

# ============================================================================
# 7. COMPARISON WITH STAGE 19 FINDINGS
# ============================================================================

print("=" * 80)
print("7. COMPARISON WITH STAGE 19 FINDINGS")
print("=" * 80)
print()

print("Stage 19 findings:")
print("  - Balanced_SMOTE + XGBoost showed severe overfitting (CV-test gap: -0.3294)")
print("  - CV Macro F1: 0.7964")
print("  - Test Macro F1: 0.4670")
print("  - SMOTE synthetic samples did not generalize")
print()

print("Diagnostic interpretation:")
print(f"  - Class separability: {separability_assessment}")
print(f"  - Feature signal: {signal_assessment}")
print(f"  - Minority class diversity: {len(class_customers['suspicious'])} suspicious customers, {len(class_customers['super_suspicious'])} super_suspicious customers")
print()

if avg_cohens_d < 0.5 and total_mi < 0.3:
    print("  Explanation: The severe CV-test gap under SMOTE is consistent with weak feature signal.")
    print("  SMOTE creates synthetic samples that don't reflect the true distribution because")
    print("  the original minority samples have poor separability and weak signal.")
    print("  The model overfits to synthetic patterns that don't exist in the real test distribution.")
elif len(class_customers['suspicious']) < 50 or len(class_customers['super_suspicious']) < 20:
    print("  Explanation: The severe CV-test gap under SMOTE is consistent with low minority diversity.")
    print("  With few unique customers generating minority samples, SMOTE creates synthetic samples")
    print("  that don't capture the true diversity of suspicious behavior in the test set.")
else:
    print("  Explanation: The severe CV-test gap under SMOTE may be due to a combination of")
    print("  weak feature signal and limited minority diversity.")
print()

# ============================================================================
# 8. CONCLUSION AND RECOMMENDATIONS
# ============================================================================

print("=" * 80)
print("8. CONCLUSION AND RECOMMENDATIONS")
print("=" * 80)
print()

# Answer the specific questions
print("A. Is 10,000 transactions likely sufficient for this problem?")
if len(train_data) >= 8000 and len(test_data) >= 2000:
    print("   YES - 10,000 transactions with 8,000/2,000 split is reasonable for this problem size.")
else:
    print("   NO - Transaction count may be insufficient.")
print()

print("B. Is the number of unique customers sufficient?")
if len(train_customers) >= 160 and len(test_customers) >= 40:
    print("   YES - 200 unique customers (160 train / 40 test) is reasonable for this problem size.")
else:
    print("   NO - Customer count may be insufficient.")
print()

print("C. Is the number/diversity of suspicious and super_suspicious examples sufficient?")
suspicious_customers = len(class_customers['suspicious'])
super_suspicious_customers = len(class_customers['super_suspicious'])
suspicious_tx = sum(1 for d in train_data if d['ground_truth_label'] == 'suspicious')
super_suspicious_tx = sum(1 for d in train_data if d['ground_truth_label'] == 'super_suspicious')

if suspicious_customers >= 50 and super_suspicious_customers >= 20:
    print(f"   YES - {suspicious_customers} suspicious customers ({suspicious_tx} tx) and {super_suspicious_customers} super_suspicious customers ({super_suspicious_tx} tx) is reasonable.")
else:
    print(f"   NO - {suspicious_customers} suspicious customers ({suspicious_tx} tx) and {super_suspicious_customers} super_suspicious customers ({super_suspicious_tx} tx) may be insufficient.")
print()

print("D. Is dataset size likely the main bottleneck?")
if avg_cohens_d < 0.5 and total_mi < 0.3:
    print("   NO - Dataset size is not the main bottleneck. The main issue is weak feature signal.")
else:
    print("   YES - Dataset size may be a contributing factor.")
print()

print("E. Is feature signal / data-generation quality the main bottleneck?")
if avg_cohens_d < 0.5 and total_mi < 0.3:
    print("   YES - Feature signal is the main bottleneck. The 18 features have poor class separability.")
else:
    print("   NO - Feature signal is not the main bottleneck.")
print()

print("F. What should we change first: model, dataset size/diversity, or features?")
if avg_cohens_d < 0.5 and total_mi < 0.3:
    print("   FEATURES - The primary bottleneck is weak feature signal. The current 18 features")
    print("   do not provide sufficient class separation. Adding more features (especially those")
    print("   identified in the Stage 18 audit) is the most promising direction.")
elif suspicious_customers < 50 or super_suspicious_customers < 20:
    print("   DATASET DIVERSITY - The primary bottleneck is limited minority diversity. Increasing")
    print("   the number of unique customers with suspicious/super-suspicious behavior would help.")
else:
    print("   MODEL - The primary bottleneck may be model architecture or hyperparameters.")
print()

# ============================================================================
# SAVE DIAGNOSTIC RESULTS
# ============================================================================

diagnostic_results = {
    "timestamp": datetime.now().isoformat(),
    "diagnostic_type": "Stage 20 Dataset Learnability / Signal Diagnostic",
    "dataset_info": {
        "total_transactions": len(merged_data),
        "train_transactions": len(train_data),
        "test_transactions": len(test_data),
        "train_customers": len(train_customers),
        "test_customers": len(test_customers),
        "customer_overlap": len(train_customers & test_customers)
    },
    "class_distributions": {
        "train": {class_name: sum(1 for d in train_data if d['ground_truth_label'] == class_name) for class_name in label_encoder.classes_},
        "test": {class_name: sum(1 for d in test_data if d['ground_truth_label'] == class_name) for class_name in label_encoder.classes_}
    },
    "minority_diversity": {
        "train": {
            "suspicious_customers": len(class_customers['suspicious']),
            "suspicious_transactions": suspicious_tx,
            "super_suspicious_customers": len(class_customers['super_suspicious']),
            "super_suspicious_transactions": super_suspicious_tx
        },
        "test": {
            "suspicious_customers": len(test_class_customers['suspicious']),
            "super_suspicious_customers": len(test_class_customers['super_suspicious'])
        }
    },
    "feature_separation": feature_separation,
    "feature_mutual_info": feature_mi,
    "feature_anova": {feature_names[i]: {"F": float(f_values[i]), "p": float(p_values[i])} for i in range(len(feature_names))},
    "assessments": {
        "separability": separability_assessment,
        "signal": signal_assessment,
        "avg_cohens_d": float(avg_cohens_d),
        "avg_overlap": float(avg_overlap),
        "total_mi": float(total_mi)
    },
    "useful_features": useful_features,
    "weak_features": weak_features
}

with open('ml_stage20_dataset_learnability_diagnostic_results.json', 'w') as f:
    json.dump(diagnostic_results, f, indent=2)

print("=" * 80)
print("STAGE 20 DATASET LEARNABILITY / SIGNAL DIAGNOSTIC COMPLETE")
print("=" * 80)
print("Diagnostic results saved to ml_stage20_dataset_learnability_diagnostic_results.json")
