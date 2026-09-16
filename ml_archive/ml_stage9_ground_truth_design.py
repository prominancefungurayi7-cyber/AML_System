"""
STAGE 9: GROUND TRUTH DESIGN AND FEASIBILITY ASSESSMENT

Design and evaluate candidate ground-truth methodologies that are:
- Observable from the approved 34 features
- Deterministic or strongly behavior-conditioned
- Free from hidden variables
- Temporally causal
"""

import csv
import json
import numpy as np
import pandas as pd
from datetime import datetime
from collections import Counter, defaultdict
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
from sklearn.feature_selection import mutual_info_classif
from scipy import stats
import hashlib

print("=" * 80)
print("STAGE 9: GROUND TRUTH DESIGN AND FEASIBILITY ASSESSMENT")
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

print(f"Loaded {len(features)} feature vectors")
print(f"Loaded {len(ground_truth)} ground truth labels")
print(f"Loaded {len(stage3_dataset)} Stage 3 transactions")
print()

# ============================================================================
# FEATURE CAPABILITY ANALYSIS
# ============================================================================

print("=" * 80)
print("FEATURE CAPABILITY ANALYSIS")
print("=" * 80)
print()

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

X = np.array([[float(feat[feature_name]) for feature_name in FEATURE_NAMES] for feat in features])
y_stage3 = np.array([gt["ground_truth_label"] for gt in ground_truth])

# Create DataFrame for analysis
df = pd.DataFrame(X, columns=FEATURE_NAMES)
df['label_stage3'] = y_stage3

print("Feature statistics:")
print("-" * 80)
for feature in FEATURE_NAMES:
    mean_val = df[feature].mean()
    std_val = df[feature].std()
    min_val = df[feature].min()
    max_val = df[feature].max()
    is_constant = std_val < 1e-10
    print(f"{feature:30s} mean={mean_val:10.2f} std={std_val:10.2f} min={min_val:10.2f} max={max_val:10.2f} constant={is_constant}")
print()

# Identify constant/near-constant features
constant_features = [f for f in FEATURE_NAMES if df[f].std() < 1e-10]
print(f"Constant/near-constant features: {constant_features}")
print()

# ============================================================================
# CANDIDATE A: DETERMINISTIC BEHAVIORAL SCORE
# ============================================================================

print("=" * 80)
print("CANDIDATE A: DETERMINISTIC BEHAVIORAL SCORE")
print("=" * 80)
print()

def behavioral_score_candidate_a(row):
    """
    Construct a behavioral anomaly score from observable features.
    
    Score combines multiple independent behavioral dimensions:
    1. Amount anomaly (z-score)
    2. Velocity anomaly (24h volume ratio)
    3. Frequency anomaly (7d frequency change)
    4. Recipient anomaly (new recipient, concentration)
    5. Timing anomaly (off-hours, rapid transfers)
    """
    score = 0.0
    
    # Amount anomaly (z-score absolute value)
    amount_z = abs(row['amount_z_score'])
    if amount_z > 2.0:
        score += 2.0
    elif amount_z > 1.0:
        score += 1.0
    
    # Velocity anomaly (24h volume ratio)
    volume_ratio = row['amount_to_sender_volume_24h']
    if volume_ratio > 5.0:
        score += 2.0
    elif volume_ratio > 2.0:
        score += 1.0
    
    # Frequency anomaly (7d frequency change)
    freq_change = abs(row['frequency_change_vs_avg_7d'])
    if freq_change > 2.0:
        score += 2.0
    elif freq_change > 1.0:
        score += 1.0
    
    # Recipient anomaly
    if row['is_new_recipient'] > 0.5:
        score += 1.0
    if row['recipient_concentration'] < 0.3:
        score += 1.0
    if row['unique_recipients_24h'] > 3:
        score += 1.0
    
    # Timing anomaly
    if row['is_off_hours'] > 0.5:
        score += 0.5
    if row['rapid_transfer_count'] > 2:
        score += 1.0
    
    return score

# Apply Candidate A
df['score_a'] = df.apply(behavioral_score_candidate_a, axis=1)

# Define class bands for Candidate A
def label_from_score_a(score):
    if score >= 5.0:
        return "super_suspicious"
    elif score >= 2.5:
        return "suspicious"
    else:
        return "normal"

df['label_a'] = df['score_a'].apply(label_from_score_a)

print("Candidate A class distribution:")
print("-" * 80)
label_counts_a = df['label_a'].value_counts()
for label, count in label_counts_a.items():
    print(f"  {label:20s}: {count:5d} ({count/len(df)*100:.1f}%)")
print()

# ============================================================================
# CANDIDATE B: MULTI-SIGNAL TYPOLOGY LOGIC
# ============================================================================

print("=" * 80)
print("CANDIDATE B: MULTI-SIGNAL TYPOLOGY LOGIC")
print("=" * 80)
print()

def label_candidate_b(row):
    """
    Define observable behavioral patterns using combinations of features.
    
    Patterns:
    - structuring-like: amounts near threshold, multiple same-day transactions
    - layering-like: rapid transfers, multiple recipients
    - funnel-like: low recipient concentration, many unique recipients
    - rapid-movement: high velocity, short time since last tx
    - recipient-expansion: new recipient, high unique recipient count
    - behavioral-change: significant amount/frequency changes
    """
    signals = []
    
    # Structuring-like pattern
    if (row['amount_z_score'] > 1.0 and row['amount_z_score'] < 3.0 and
        row['same_day_count'] > 2):
        signals.append('structuring')
    
    # Layering-like pattern
    if (row['rapid_transfer_count'] > 1 and
        row['unique_recipients_24h'] > 2 and
        row['time_since_last_tx'] < 3600):
        signals.append('layering')
    
    # Funnel-like pattern
    if (row['recipient_concentration'] < 0.4 and
        row['unique_recipients_7d'] > 5):
        signals.append('funnel')
    
    # Rapid-movement pattern
    if (row['amount_to_sender_volume_24h'] > 3.0 and
        row['time_since_last_tx'] < 1800):
        signals.append('rapid_movement')
    
    # Recipient-expansion pattern
    if (row['is_new_recipient'] > 0.5 and
        row['new_recipient_ratio_7d'] > 0.5):
        signals.append('recipient_expansion')
    
    # Behavioral-change pattern
    if (abs(row['amount_change_vs_avg_7d']) > 2.0 and
        abs(row['frequency_change_vs_avg_7d']) > 1.5):
        signals.append('behavioral_change')
    
    # Determine label based on signal count
    if len(signals) >= 3:
        return "super_suspicious"
    elif len(signals) >= 1:
        return "suspicious"
    else:
        return "normal"

# Apply Candidate B
df['label_b'] = df.apply(label_candidate_b, axis=1)

print("Candidate B class distribution:")
print("-" * 80)
label_counts_b = df['label_b'].value_counts()
for label, count in label_counts_b.items():
    print(f"  {label:20s}: {count:5d} ({count/len(df)*100:.1f}%)")
print()

# ============================================================================
# CANDIDATE C: LATENT RISK SCORE WITH CONTROLLED STOCHASTICITY
# ============================================================================

print("=" * 80)
print("CANDIDATE C: LATENT RISK SCORE WITH CONTROLLED STOCHASTICITY")
print("=" * 80)
print()

def risk_score_candidate_c(row):
    """
    Construct a continuous observable risk score.
    Uses weighted combination of normalized features.
    """
    # Normalize each feature dimension to 0-1 range
    amount_risk = min(abs(row['amount_z_score']) / 3.0, 1.0)
    velocity_risk = min(row['amount_to_sender_volume_24h'] / 5.0, 1.0)
    frequency_risk = min(abs(row['frequency_change_vs_avg_7d']) / 2.0, 1.0)
    recipient_risk = (1.0 - row['recipient_concentration']) if row['recipient_concentration'] < 1 else 0
    timing_risk = row['is_off_hours'] * 0.5 + min(row['rapid_transfer_count'] / 5.0, 1.0) * 0.5
    
    # Weighted combination
    risk_score = (amount_risk * 0.3 +
                  velocity_risk * 0.25 +
                  frequency_risk * 0.2 +
                  recipient_risk * 0.15 +
                  timing_risk * 0.1)
    
    return risk_score

# Apply Candidate C
df['risk_score_c'] = df.apply(risk_score_candidate_c, axis=1)

# Define class bands with small controlled stochasticity at boundaries
np.random.seed(42)
def label_from_risk_score_c_stochastic(risk_score):
    # Add small controlled stochasticity at boundaries (5% variation)
    # NOTE: This applies noise to EVERY transaction, not just boundary cases
    noise = np.random.uniform(-0.025, 0.025)
    adjusted_score = risk_score + noise
    
    if adjusted_score >= 0.7:
        return "super_suspicious"
    elif adjusted_score >= 0.4:
        return "suspicious"
    else:
        return "normal"

# Also create deterministic version for comparison
def label_from_risk_score_c_deterministic(risk_score):
    if risk_score >= 0.7:
        return "super_suspicious"
    elif risk_score >= 0.4:
        return "suspicious"
    else:
        return "normal"

df['label_c_stochastic'] = df['risk_score_c'].apply(label_from_risk_score_c_stochastic)
df['label_c_deterministic'] = df['risk_score_c'].apply(label_from_risk_score_c_deterministic)

print("Candidate C (stochastic) class distribution:")
print("-" * 80)
label_counts_c_stochastic = df['label_c_stochastic'].value_counts()
for label, count in label_counts_c_stochastic.items():
    print(f"  {label:20s}: {count:5d} ({count/len(df)*100:.1f}%)")
print()

print("Candidate C (deterministic) class distribution:")
print("-" * 80)
label_counts_c_deterministic = df['label_c_deterministic'].value_counts()
for label, count in label_counts_c_deterministic.items():
    print(f"  {label:20s}: {count:5d} ({count/len(df)*100:.1f}%)")
print()

# Analyze stochasticity impact
# Calculate how many transactions are within noise range of decision boundaries
boundary_range = 0.025
near_super_boundary = ((df['risk_score_c'] >= 0.7 - boundary_range) & (df['risk_score_c'] <= 0.7 + boundary_range)).sum()
near_suspicious_boundary = ((df['risk_score_c'] >= 0.4 - boundary_range) & (df['risk_score_c'] <= 0.4 + boundary_range)).sum()
near_normal_boundary = ((df['risk_score_c'] >= 0.4 - boundary_range) & (df['risk_score_c'] <= 0.4 + boundary_range)).sum()

print("Stochasticity analysis:")
print("-" * 80)
print(f"  Transactions within ±0.025 of super_suspicious boundary (0.7): {near_super_boundary} ({near_super_boundary/len(df)*100:.1f}%)")
print(f"  Transactions within ±0.025 of suspicious boundary (0.4): {near_suspicious_boundary} ({near_suspicious_boundary/len(df)*100:.1f}%)")
print(f"  Total transactions that could potentially change class: {near_super_boundary + near_suspicious_boundary} ({(near_super_boundary + near_suspicious_boundary)/len(df)*100:.1f}%)")
print()

# Calculate actual label changes due to stochasticity
label_changes = (df['label_c_stochastic'] != df['label_c_deterministic']).sum()
print(f"  Actual label changes due to stochasticity: {label_changes} ({label_changes/len(df)*100:.1f}%)")
print()

print("CRITICAL FINDING:")
print("-" * 80)
print("  The stochastic component applies noise to EVERY transaction (100%),")
print("  not just transactions near decision boundaries.")
print(f"  However, only {label_changes/len(df)*100:.1f}% of transactions actually change class.")
print("  The random component IS an unobservable determinant of the label.")
print()

# ============================================================================
# EVALUATE CANDIDATES
# ============================================================================

print("=" * 80)
print("CANDIDATE EVALUATION")
print("=" * 80)
print()

def evaluate_candidate(df, label_col, candidate_name):
    """Evaluate a candidate labeling methodology with comprehensive metrics."""
    y = df[label_col].values
    
    results = {
        'candidate': candidate_name,
        'class_distribution': dict(df[label_col].value_counts(normalize=True)),
        'feature_label_signal': {},
        'label_consistency': {},
        'temporal_stability': {},
        'class_statistics': {},
        'super_suspicious_vs_normal_separation': {}
    }
    
    # Class-conditional feature statistics for all 34 features
    for feature in FEATURE_NAMES:
        class_stats = {}
        for label in ['normal', 'suspicious', 'super_suspicious']:
            class_data = df[df[label_col] == label][feature]
            if len(class_data) > 0:
                class_stats[label] = {
                    'mean': float(class_data.mean()),
                    'std': float(class_data.std()),
                    'min': float(class_data.min()),
                    'max': float(class_data.max()),
                    'count': len(class_data)
                }
        results['class_statistics'][feature] = class_stats
        
        # Cohen's d for all feature pairs
        if 'normal' in class_stats and 'suspicious' in class_stats:
            normal_vals = df[df[label_col] == 'normal'][feature]
            suspicious_vals = df[df[label_col] == 'suspicious'][feature]
            if len(normal_vals) > 0 and len(suspicious_vals) > 0:
                pooled_std = np.sqrt((normal_vals.std()**2 + suspicious_vals.std()**2) / 2)
                if pooled_std > 0:
                    cohens_d = abs((normal_vals.mean() - suspicious_vals.mean()) / pooled_std)
                    results['feature_label_signal'][f'{feature}_normal_vs_suspicious'] = cohens_d
        
        if 'suspicious' in class_stats and 'super_suspicious' in class_stats:
            suspicious_vals = df[df[label_col] == 'suspicious'][feature]
            super_vals = df[df[label_col] == 'super_suspicious'][feature]
            if len(suspicious_vals) > 0 and len(super_vals) > 0:
                pooled_std = np.sqrt((suspicious_vals.std()**2 + super_vals.std()**2) / 2)
                if pooled_std > 0:
                    cohens_d = abs((suspicious_vals.mean() - super_vals.mean()) / pooled_std)
                    results['feature_label_signal'][f'{feature}_suspicious_vs_super'] = cohens_d
        
        if 'normal' in class_stats and 'super_suspicious' in class_stats:
            normal_vals = df[df[label_col] == 'normal'][feature]
            super_vals = df[df[label_col] == 'super_suspicious'][feature]
            if len(normal_vals) > 0 and len(super_vals) > 0:
                pooled_std = np.sqrt((normal_vals.std()**2 + super_vals.std()**2) / 2)
                if pooled_std > 0:
                    cohens_d = abs((normal_vals.mean() - super_vals.mean()) / pooled_std)
                    results['feature_label_signal'][f'{feature}_normal_vs_super'] = cohens_d
                    results['super_suspicious_vs_normal_separation'][feature] = cohens_d
    
    # Mutual information (for numerical features)
    try:
        # Convert labels to numeric for MI calculation
        label_map = {'normal': 0, 'suspicious': 1, 'super_suspicious': 2}
        y_numeric = np.array([label_map.get(l, 0) for l in y])
        
        # Calculate MI for each feature
        for feature in FEATURE_NAMES:
            feature_data = df[feature].values.reshape(-1, 1)
            try:
                mi = mutual_info_classif(feature_data, y_numeric, discrete_features=False, random_state=42)[0]
                results['feature_label_signal'][f'{feature}_mutual_info'] = mi
            except:
                results['feature_label_signal'][f'{feature}_mutual_info'] = 0.0
    except Exception as e:
        print(f"  Mutual information calculation failed: {e}")
    
    # Label consistency (nearest-neighbor agreement)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    nn = NearestNeighbors(n_neighbors=6)
    nn.fit(X_scaled)
    distances, indices = nn.kneighbors(X_scaled)
    
    agreements = 0
    total = 0
    for i in range(len(X_scaled)):
        for j in indices[i]:
            if i != j:
                if y[i] == y[j]:
                    agreements += 1
                total += 1
    
    results['label_consistency']['agreement_rate'] = agreements / total if total > 0 else 0
    
    # Near-identical feature-vector label agreement (distance < 0.01)
    near_identical_agreements = 0
    near_identical_total = 0
    for i in range(len(X_scaled)):
        for j in range(i+1, len(X_scaled)):
            dist = np.linalg.norm(X_scaled[i] - X_scaled[j])
            if dist < 0.01:
                if y[i] == y[j]:
                    near_identical_agreements += 1
                near_identical_total += 1
    
    results['label_consistency']['near_identical_agreement_rate'] = near_identical_agreements / near_identical_total if near_identical_total > 0 else 0
    results['label_consistency']['near_identical_pairs'] = near_identical_total
    
    return results

# Evaluate all candidates (use deterministic version of Candidate C)
results_a = evaluate_candidate(df, 'label_a', 'Candidate A')
results_b = evaluate_candidate(df, 'label_b', 'Candidate B')
results_c = evaluate_candidate(df, 'label_c_deterministic', 'Candidate C (Deterministic)')

print("Candidate A evaluation:")
print("-" * 80)
print(f"  Class distribution: {results_a['class_distribution']}")
print(f"  Label consistency: {results_a['label_consistency']['agreement_rate']:.4f}")
print(f"  Near-identical agreement: {results_a['label_consistency']['near_identical_agreement_rate']:.4f}")
print(f"  Near-identical pairs: {results_a['label_consistency']['near_identical_pairs']}")
print()

print("Candidate B evaluation:")
print("-" * 80)
print(f"  Class distribution: {results_b['class_distribution']}")
print(f"  Label consistency: {results_b['label_consistency']['agreement_rate']:.4f}")
print(f"  Near-identical agreement: {results_b['label_consistency']['near_identical_agreement_rate']:.4f}")
print(f"  Near-identical pairs: {results_b['label_consistency']['near_identical_pairs']}")
print()

print("Candidate C (deterministic) evaluation:")
print("-" * 80)
print(f"  Class distribution: {results_c['class_distribution']}")
print(f"  Label consistency: {results_c['label_consistency']['agreement_rate']:.4f}")
print(f"  Near-identical agreement: {results_c['label_consistency']['near_identical_agreement_rate']:.4f}")
print(f"  Near-identical pairs: {results_c['label_consistency']['near_identical_pairs']}")
print()

# Print top Cohen's d values for each candidate
print("Top Cohen's d values (normal vs suspicious):")
print("-" * 80)
for candidate_name, results in [('Candidate A', results_a), ('Candidate B', results_b), ('Candidate C', results_c)]:
    print(f"\n{candidate_name}:")
    # Get top 5 features by Cohen's d
    cohens_d_values = [(k, v) for k, v in results['feature_label_signal'].items() if 'normal_vs_suspicious' in k]
    cohens_d_values.sort(key=lambda x: x[1], reverse=True)
    for feature, d in cohens_d_values[:5]:
        print(f"  {feature}: {d:.4f}")
print()

# ============================================================================
# SAVE RESULTS
# ============================================================================

print("Saving results...")

def convert_to_serializable(obj):
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(v) for v in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

results = {
    'timestamp': datetime.now().isoformat(),
    'feature_analysis': {
        'constant_features': constant_features,
        'feature_count': len(FEATURE_NAMES)
    },
    'candidate_a': convert_to_serializable(results_a),
    'candidate_b': convert_to_serializable(results_b),
    'candidate_c_deterministic': convert_to_serializable(results_c),
    'stochasticity_analysis': {
        'noise_applied_to_all_transactions': True,
        'transactions_near_super_boundary': int(near_super_boundary),
        'transactions_near_suspicious_boundary': int(near_suspicious_boundary),
        'total_potential_changes': int(near_super_boundary + near_suspicious_boundary),
        'actual_label_changes': int(label_changes),
        'percentage_changed': float(label_changes / len(df) * 100)
    }
}

with open('ml_stage9_ground_truth_design_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("Results saved to ml_stage9_ground_truth_design_results.json")
print()

print("=" * 80)
print("GROUND TRUTH DESIGN ANALYSIS COMPLETE")
print("=" * 80)
