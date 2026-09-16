"""
STAGE 7: Root-Cause Analysis / Feature Signal Audit

Comprehensive diagnostic analysis to understand why the 34-feature representation performs poorly.
"""

import csv
import json
import numpy as np
import pandas as pd
from datetime import datetime
from scipy import stats
from sklearn.metrics import f1_score, accuracy_score
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import mutual_info_classif
from sklearn.neighbors import NearestNeighbors
import joblib

print("=" * 80)
print("STAGE 7: ROOT-CAUSE ANALYSIS / FEATURE SIGNAL AUDIT")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================================
# LOAD DATA
# ============================================================================

print("Loading data...")
with open("ml_stage5_features.csv", 'r') as f:
    reader = csv.DictReader(f)
    features = list(reader)

with open("ml_stage3_ground_truth.json", 'r') as f:
    ground_truth = json.load(f)

with open("ml_stage3_dataset.csv", 'r') as f:
    reader = csv.DictReader(f)
    stage3_dataset = list(reader)

print(f"Loaded {len(features)} feature rows")
print(f"Loaded {len(ground_truth)} labels")
print(f"Loaded {len(stage3_dataset)} transactions from Stage 3")
print()

# ============================================================================
# VERIFY STAGE 6 RESULTS
# ============================================================================

print("=" * 80)
print("STAGE 6 RESULTS VERIFICATION")
print("=" * 80)
print()

with open("ml_stage6_results.json", 'r') as f:
    stage6_results = json.load(f)

print("Dataset verification:")
print(f"  Dataset size: {len(features)} (expected 10,000)")
print(f"  Feature count: {len(features[0])} (expected 34)")
print()

print("Class distribution verification:")
label_counts = {}
for entry in ground_truth:
    label = entry["ground_truth_label"]
    label_counts[label] = label_counts.get(label, 0) + 1
for label in ["normal", "suspicious", "super_suspicious"]:
    count = label_counts.get(label, 0)
    pct = (count / len(ground_truth)) * 100
    print(f"  {label}: {count} ({pct:.1f}%)")
print()

print("Train/test split verification:")
print(f"  Train samples: {stage6_results['train_samples']} (expected 8,000)")
print(f"  Test samples: {stage6_results['test_samples']} (expected 2,000)")
print(f"  Customer overlap: {stage6_results['customer_overlap']} (expected 0)")
print()

print("Model performance verification:")
print(f"  Gradient Boosting test Macro F1: {stage6_results['gradient_boosting']['test_macro_f1']:.4f}")
print(f"  Random Forest test Macro F1: {stage6_results['random_forest']['test_macro_f1']:.4f}")
print()

# ============================================================================
# CALCULATE ACTUAL TRAINING PERFORMANCE (RESOLVE OVERFITTING INCONSISTENCY)
# ============================================================================

print("=" * 80)
print("ACTUAL TRAINING PERFORMANCE CALCULATION")
print("=" * 80)
print()

# Load trained models
rf_model = joblib.load("ml_stage6_rf_model.pkl")
gb_model = joblib.load("ml_stage6_gb_model.pkl") if False else None  # GB not saved, will retrain
scaler = joblib.load("ml_stage6_scaler.pkl")

# Prepare data (same as Stage 6)
combined_data = []
for i, feature_row in enumerate(features):
    label_entry = ground_truth[i]
    stage3_row = stage3_dataset[i]
    combined_data.append({
        "timestamp": stage3_row["timestamp"],
        "label": label_entry["ground_truth_label"],
        **{k: float(v) for k, v in feature_row.items()}
    })

combined_data.sort(key=lambda x: datetime.fromisoformat(x["timestamp"]))
split_idx = int(len(combined_data) * 0.8)
train_data = combined_data[:split_idx]
test_data = combined_data[split_idx:]

FEATURE_NAMES = [
    "amount", "sender_avg_amount", "sender_max_amount", "sender_tx_count",
    "amount_to_sender_avg", "amount_to_sender_max", "sender_tx_count_24h",
    "sender_volume_24h", "amount_to_sender_volume_24h", "is_new_recipient",
    "same_day_count", "same_day_total", "same_recipient_count", "rapid_transfer_count",
    "hour", "is_deposit", "is_withdraw", "is_transfer", "is_self_transfer",
    "is_off_hours", "channel_encoded", "amount_std_dev", "amount_z_score",
    "tx_frequency_7d", "tx_frequency_30d", "day_of_week", "is_weekend",
    "time_since_last_tx", "unique_recipients_24h", "unique_recipients_7d",
    "recipient_concentration", "new_recipient_ratio_7d",
    "amount_change_vs_avg_7d", "frequency_change_vs_avg_7d"
]

X_train = np.array([[tx[feat] for feat in FEATURE_NAMES] for tx in train_data])
y_train = np.array([tx["label"] for tx in train_data])
X_test = np.array([[tx[feat] for feat in FEATURE_NAMES] for tx in test_data])
y_test = np.array([tx["label"] for tx in test_data])

X_train_scaled = scaler.transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Calculate actual training predictions
y_train_pred_rf = rf_model.predict(X_train_scaled)
y_test_pred_rf = rf_model.predict(X_test_scaled)

train_f1_rf = f1_score(y_train, y_train_pred_rf, average='macro')
test_f1_rf = f1_score(y_test, y_test_pred_rf, average='macro')
cv_f1_rf = stage6_results['random_forest']['cv_macro_f1_mean']

print("Random Forest actual performance:")
print(f"  Training Macro F1: {train_f1_rf:.4f}")
print(f"  CV Macro F1: {cv_f1_rf:.4f}")
print(f"  Test Macro F1: {test_f1_rf:.4f}")
print(f"  Train-to-CV gap: {abs(train_f1_rf - cv_f1_rf):.4f}")
print(f"  Train-to-Test gap: {abs(train_f1_rf - test_f1_rf):.4f}")
print()

# Determine overfitting status
if train_f1_rf - test_f1_rf > 0.3:
    overfitting_status = "OVERFITTING DETECTED (large train-test gap)"
elif train_f1_rf - test_f1_rf > 0.1:
    overfitting_status = "MODERATE OVERFITTING"
else:
    overfitting_status = "NO SIGNIFICANT OVERFITTING"

print(f"Overfitting status: {overfitting_status}")
print()

# ============================================================================
# FEATURE-BY-FEATURE CLASS SIGNAL ANALYSIS
# ============================================================================

print("=" * 80)
print("FEATURE-BY-FEATURE CLASS SIGNAL ANALYSIS")
print("=" * 80)
print()

# Create DataFrame for analysis
df = pd.DataFrame(combined_data)
df['label'] = df['label']

feature_class_stats = {}
for feat in FEATURE_NAMES:
    stats_by_class = {}
    for label in ['normal', 'suspicious', 'super_suspicious']:
        class_data = df[df['label'] == label][feat]
        stats_by_class[label] = {
            'mean': class_data.mean(),
            'median': class_data.median(),
            'std': class_data.std(),
            'min': class_data.min(),
            'max': class_data.max(),
            'q25': class_data.quantile(0.25),
            'q75': class_data.quantile(0.75)
        }
    feature_class_stats[feat] = stats_by_class

# Calculate separation metrics
feature_separation = {}
for feat in FEATURE_NAMES:
    normal_mean = feature_class_stats[feat]['normal']['mean']
    suspicious_mean = feature_class_stats[feat]['suspicious']['mean']
    super_mean = feature_class_stats[feat]['super_suspicious']['mean']
    
    # Calculate effect sizes (Cohen's d)
    normal_std = feature_class_stats[feat]['normal']['std']
    suspicious_std = feature_class_stats[feat]['suspicious']['std']
    super_std = feature_class_stats[feat]['super_suspicious']['std']
    
    d_normal_suspicious = abs(normal_mean - suspicious_mean) / max(normal_std, suspicious_std, 0.001)
    d_normal_super = abs(normal_mean - super_mean) / max(normal_std, super_std, 0.001)
    d_suspicious_super = abs(suspicious_mean - super_mean) / max(suspicious_std, super_std, 0.001)
    
    feature_separation[feat] = {
        'd_normal_suspicious': d_normal_suspicious,
        'd_normal_super': d_normal_super,
        'd_suspicious_super': d_suspicious_super,
        'max_separation': max(d_normal_suspicious, d_normal_super, d_suspicious_super)
    }

print("Top 10 features by class separation (Cohen's d):")
sorted_features = sorted(feature_separation.items(), key=lambda x: x[1]['max_separation'], reverse=True)
for i, (feat, sep) in enumerate(sorted_features[:10]):
    print(f"  {i+1:2d}. {feat:30s} max_d={sep['max_separation']:.3f} (N-S={sep['d_normal_suspicious']:.3f}, N-SS={sep['d_normal_super']:.3f}, S-SS={sep['d_suspicious_super']:.3f})")
print()

# ============================================================================
# UNIVARIATE PREDICTIVE SIGNAL (MUTUAL INFORMATION)
# ============================================================================

print("=" * 80)
print("UNIVARIATE PREDICTIVE SIGNAL (MUTUAL INFORMATION)")
print("=" * 80)
print()

X_all = np.array([[tx[feat] for feat in FEATURE_NAMES] for tx in combined_data])
y_all = np.array([tx["label"] for tx in combined_data])

# Encode labels
label_map = {'normal': 0, 'suspicious': 1, 'super_suspicious': 2}
y_encoded = np.array([label_map[l] for l in y_all])

# Calculate mutual information
mi_scores = mutual_info_classif(X_all, y_encoded, random_state=42)

feature_mi = list(zip(FEATURE_NAMES, mi_scores))
feature_mi_sorted = sorted(feature_mi, key=lambda x: x[1], reverse=True)

print("Top 10 features by mutual information:")
for i, (feat, mi) in enumerate(feature_mi_sorted[:10]):
    print(f"  {i+1:2d}. {feat:30s} MI={mi:.4f}")
print()

# ============================================================================
# CLASS SEPARABILITY ANALYSIS (PCA)
# ============================================================================

print("=" * 80)
print("CLASS SEPARABILITY ANALYSIS (PCA)")
print("=" * 80)
print()

# Scale features
scaler_pca = StandardScaler()
X_scaled = scaler_pca.fit_transform(X_all)

# PCA to 2D for visualization
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

# Calculate class centroids
centroids = {}
for label in ['normal', 'suspicious', 'super_suspicious']:
    label_idx = y_all == label
    centroids[label] = X_pca[label_idx].mean(axis=0)

print("PCA explained variance ratio:")
print(f"  PC1: {pca.explained_variance_ratio_[0]:.4f}")
print(f"  PC2: {pca.explained_variance_ratio_[1]:.4f}")
print(f"  Total: {sum(pca.explained_variance_ratio_):.4f}")
print()

print("Class centroids in PCA space:")
for label in ['normal', 'suspicious', 'super_suspicious']:
    print(f"  {label}: ({centroids[label][0]:.3f}, {centroids[label][1]:.3f})")
print()

# Calculate distances between centroids
from scipy.spatial.distance import euclidean
dist_normal_suspicious = euclidean(centroids['normal'], centroids['suspicious'])
dist_normal_super = euclidean(centroids['normal'], centroids['super_suspicious'])
dist_suspicious_super = euclidean(centroids['suspicious'], centroids['super_suspicious'])

print("Inter-class distances (PCA space):")
print(f"  Normal - Suspicious: {dist_normal_suspicious:.3f}")
print(f"  Normal - Super Suspicious: {dist_normal_super:.3f}")
print(f"  Suspicious - Super Suspicious: {dist_suspicious_super:.3f}")
print()

# ============================================================================
# SUPERSUSPICIOUS-SPECIFIC ANALYSIS
# ============================================================================

print("=" * 80)
print("SUPERSUSPICIOUS-SPECIFIC ANALYSIS")
print("=" * 80)
print()

super_suspicious_idx = y_all == 'super_suspicious'
normal_idx = y_all == 'normal'
suspicious_idx = y_all == 'suspicious'

print(f"Super suspicious transactions: {sum(super_suspicious_idx)}")
print()

# Compare super_suspicious vs normal
print("Super Suspicious vs Normal - Top distinguishing features:")
super_vs_normal = []
for feat in FEATURE_NAMES:
    super_mean = df[super_suspicious_idx][feat].mean()
    normal_mean = df[normal_idx][feat].mean()
    diff = abs(super_mean - normal_mean)
    super_std = df[super_suspicious_idx][feat].std()
    normal_std = df[normal_idx][feat].std()
    pooled_std = max(super_std, normal_std, 0.001)
    effect_size = diff / pooled_std
    super_vs_normal.append((feat, effect_size, super_mean, normal_mean))

super_vs_normal_sorted = sorted(super_vs_normal, key=lambda x: x[1], reverse=True)
for i, (feat, effect_size, super_mean, normal_mean) in enumerate(super_vs_normal_sorted[:10]):
    print(f"  {i+1:2d}. {feat:30s} effect={effect_size:.3f} (super={super_mean:.2f}, normal={normal_mean:.2f})")
print()

# ============================================================================
# TEMPORAL SIGNAL ANALYSIS
# ============================================================================

print("=" * 80)
print("TEMPORAL SIGNAL ANALYSIS")
print("=" * 80)
print()

# Split into 5 time periods
df_sorted = df.sort_values('timestamp')
n_periods = 5
period_size = len(df_sorted) // n_periods

temporal_analysis = []
for i in range(n_periods):
    start_idx = i * period_size
    end_idx = (i + 1) * period_size if i < n_periods - 1 else len(df_sorted)
    period_data = df_sorted.iloc[start_idx:end_idx]
    
    period_label_dist = period_data['label'].value_counts(normalize=True)
    period_super_rate = period_label_dist.get('super_suspicious', 0)
    period_suspicious_rate = period_label_dist.get('suspicious', 0)
    
    # Calculate mean of top feature (hour) for this period
    period_hour_mean = period_data['hour'].mean()
    
    temporal_analysis.append({
        'period': i + 1,
        'super_rate': period_super_rate,
        'suspicious_rate': period_suspicious_rate,
        'hour_mean': period_hour_mean
    })

print("Temporal analysis by period:")
for period in temporal_analysis:
    print(f"  Period {period['period']}: super={period['super_rate']:.3f}, suspicious={period['suspicious_rate']:.3f}, hour_mean={period['hour_mean']:.2f}")
print()

# Check for distribution shift
super_rates = [f['super_rate'] for f in temporal_analysis]
suspicious_rates = [f['suspicious_rate'] for f in temporal_analysis]

super_rate_std = np.std(super_rates)
suspicious_rate_std = np.std(suspicious_rates)

print(f"Super suspicious rate std across periods: {super_rate_std:.4f}")
print(f"Suspicious rate std across periods: {suspicious_rate_std:.4f}")
print()

if super_rate_std > 0.01:
    print("WARNING: Super suspicious rate varies significantly across periods (possible temporal shift)")
else:
    print("Super suspicious rate stable across periods")
print()

# ============================================================================
# CUSTOMER-LEVEL SIGNAL ANALYSIS
# ============================================================================

print("=" * 80)
print("CUSTOMER-LEVEL SIGNAL ANALYSIS")
print("=" * 80)
print()

# Load customer information from Stage 3
customer_labels = {}
for i, row in enumerate(stage3_dataset):
    tx_id = i + 1
    label = ground_truth[i]['ground_truth_label']
    customer = row['sender_account']
    if customer not in customer_labels:
        customer_labels[customer] = []
    customer_labels[customer].append(label)

# Count customers with each class
customers_with_suspicious = sum(1 for labels in customer_labels.values() if 'suspicious' in labels)
customers_with_super = sum(1 for labels in customer_labels.values() if 'super_suspicious' in labels)
total_customers = len(customer_labels)

print(f"Total customers: {total_customers}")
print(f"Customers with suspicious transactions: {customers_with_suspicious} ({customers_with_suspicious/total_customers*100:.1f}%)")
print(f"Customers with super_suspicious transactions: {customers_with_super} ({customers_with_super/total_customers*100:.1f}%)")
print()

# Check concentration
suspicious_counts = [sum(1 for l in labels if l == 'suspicious') for labels in customer_labels.values()]
super_counts = [sum(1 for l in labels if l == 'super_suspicious') for labels in customer_labels.values()]

print(f"Max suspicious transactions per customer: {max(suspicious_counts)}")
print(f"Max super_suspicious transactions per customer: {max(super_counts)}")
print(f"Mean suspicious per customer (among those with any): {np.mean([c for c in suspicious_counts if c > 0]):.2f}")
print(f"Mean super_suspicious per customer (among those with any): {np.mean([c for c in super_counts if c > 0]):.2f}")
print()

# ============================================================================
# LABEL-TO-FEATURE CONSISTENCY AUDIT
# ============================================================================

print("=" * 80)
print("LABEL-TO-FEATURE CONSISTENCY AUDIT")
print("=" * 80)
print()

# Check for near-duplicate feature vectors with different labels
X_scaled_full = scaler.transform(X_all)

# Use nearest neighbors to find similar points
nn = NearestNeighbors(n_neighbors=6, metric='euclidean')
nn.fit(X_scaled_full)
distances, indices = nn.kneighbors(X_scaled_full)

# Count conflicts (similar points with different labels)
conflicts = 0
total_comparisons = 0

for i in range(len(X_all)):
    for j, neighbor_idx in enumerate(indices[i]):
        if i == neighbor_idx:  # Skip self
            continue
        if distances[i][j] < 1.0:  # Very close in scaled space
            total_comparisons += 1
            if y_all[i] != y_all[neighbor_idx]:
                conflicts += 1

conflict_rate = conflicts / total_comparisons if total_comparisons > 0 else 0

print(f"Near-duplicate analysis (distance < 1.0 in scaled space):")
print(f"  Total close pairs: {total_comparisons}")
print(f"  Conflicting labels: {conflicts}")
print(f"  Conflict rate: {conflict_rate:.4f}")
print()

# ============================================================================
# FEATURE REDUNDANCY ANALYSIS
# ============================================================================

print("=" * 80)
print("FEATURE REDUNDANCY ANALYSIS")
print("=" * 80)
print()

# Calculate correlation matrix for continuous features
continuous_features = [f for f in FEATURE_NAMES if f not in ['is_deposit', 'is_withdraw', 'is_transfer', 'is_self_transfer', 'is_off_hours', 'is_weekend', 'channel_encoded', 'day_of_week', 'hour']]
corr_matrix = df[continuous_features].corr()

# Find highly correlated pairs
high_corr_pairs = []
for i in range(len(corr_matrix.columns)):
    for j in range(i+1, len(corr_matrix.columns)):
        corr = corr_matrix.iloc[i, j]
        if abs(corr) > 0.7:  # High correlation threshold
            high_corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j], corr))

print(f"Highly correlated feature pairs (|r| > 0.7): {len(high_corr_pairs)}")
for feat1, feat2, corr in sorted(high_corr_pairs, key=lambda x: abs(x[2]), reverse=True)[:10]:
    print(f"  {feat1:30s} <-> {feat2:30s} r={corr:.3f}")
print()

# ============================================================================
# SAVE RESULTS
# ============================================================================

print("Saving results...")
results = {
    "timestamp": datetime.now().isoformat(),
    "stage6_verification": {
        "dataset_size": len(features),
        "feature_count": len(features[0]),
        "train_samples": stage6_results['train_samples'],
        "test_samples": stage6_results['test_samples'],
        "customer_overlap": stage6_results['customer_overlap'],
        "gb_test_macro_f1": stage6_results['gradient_boosting']['test_macro_f1'],
        "rf_test_macro_f1": stage6_results['random_forest']['test_macro_f1']
    },
    "actual_training_performance": {
        "rf_train_macro_f1": float(train_f1_rf),
        "rf_cv_macro_f1": float(cv_f1_rf),
        "rf_test_macro_f1": float(test_f1_rf),
        "rf_train_cv_gap": float(abs(train_f1_rf - cv_f1_rf)),
        "rf_train_test_gap": float(abs(train_f1_rf - test_f1_rf)),
        "overfitting_status": overfitting_status
    },
    "feature_separation": {feat: feature_separation[feat] for feat in FEATURE_NAMES},
    "mutual_information": {feat: float(mi) for feat, mi in feature_mi_sorted},
    "class_separability": {
        "explained_variance_2d": [float(pca.explained_variance_ratio_[0]), float(pca.explained_variance_ratio_[1])],
        "centroids": {label: [float(centroids[label][0]), float(centroids[label][1])] for label in centroids},
        "inter_class_distances": {
            "normal_suspicious": float(dist_normal_suspicious),
            "normal_super": float(dist_normal_super),
            "suspicious_super": float(dist_suspicious_super)
        }
    },
    "temporal_analysis": temporal_analysis,
    "customer_analysis": {
        "total_customers": total_customers,
        "customers_with_suspicious": customers_with_suspicious,
        "customers_with_super": customers_with_super,
        "max_suspicious_per_customer": int(max(suspicious_counts)),
        "max_super_per_customer": int(max(super_counts))
    },
    "label_feature_consistency": {
        "near_duplicate_conflicts": int(conflicts),
        "near_duplicate_pairs": int(total_comparisons),
        "conflict_rate": float(conflict_rate)
    },
    "feature_redundancy": {
        "high_corr_pairs": len(high_corr_pairs),
        "top_correlations": [{"f1": f1, "f2": f2, "corr": float(c)} for f1, f2, c in sorted(high_corr_pairs, key=lambda x: abs(x[2]), reverse=True)[:10]]
    }
}

with open("ml_stage7_signal_results.json", 'w') as f:
    json.dump(results, f, indent=2)

print("Results saved to ml_stage7_signal_results.json")
print()

print("=" * 80)
print("SIGNAL ANALYSIS COMPLETE")
print("=" * 80)
