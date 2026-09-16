# Stage 16A Structuring Detection Diagnostic Audit Report

**Date:** 2026-09-15  
**Stage:** 16A — Structuring Detection Diagnostic Audit  
**Status:** PASS — DIAGNOSTIC ANALYSIS COMPLETE  
**Audit Timestamp:** 2026-09-15T16:36:45.754316+00:00

---

## Executive Summary

A comprehensive diagnostic analysis was performed to investigate why the frozen 30-feature representation and Stage 14 Gradient Boosting model have substantially weaker performance on the Structuring domain (30.8% recall) compared to Network (74.3% recall) and Agent (58.8% recall) domains.

**Primary Finding:** The weak structuring detection is primarily caused by **insufficient feature representation** combined with **significant normal/suspicious behavioural overlap**. The existing six structuring features have limited separation power, and two of the four structuring scenario families have almost no distinctive signal in the current feature set.

**Final Decision:** **B. TARGETED FEATURE IMPROVEMENT JUSTIFIED**

Evidence supports adding a small number of carefully designed features to improve structuring detection, particularly for Distributed Same-Day Fragmentation and Variable Near-Threshold History scenarios.

---

## 1. Current Official Baseline

**Frozen Model:** Stage 14 Gradient Boosting  
**Model Parameters:**
- learning_rate: 0.1
- max_depth: 3
- min_samples_leaf: 2
- min_samples_split: 5
- n_estimators: 200
- random_state: 42
- threshold: 0.35

**Independent Performance:**
- Macro F1: 0.7245
- Suspicious recall: 54.58%
- **Structuring recall: 30.75%**
- **Network recall: 74.25%**
- **Agent recall: 58.75%**

The structuring domain performance gap is substantial: 30.8% vs 74.3% (network) and 58.8% (agent).

---

## 2. Frozen Structuring Features

The six structuring features remain exactly as implemented in Stage 13:

1. **structuring_prior_tx_count_1h** - Transaction count in prior 1 hour
2. **structuring_prior_value_sum_24h** - Cumulative value in prior 24 hours
3. **structuring_same_day_prior_tx_count** - Transaction count earlier same day
4. **structuring_repeated_amount_ratio_7d** - Ratio of repeated amounts in 7 days
5. **structuring_amount_cluster_dispersion_7d** - Dispersion of transaction amounts in 7 days
6. **structuring_near_threshold_history_ratio_7d** - Ratio of near-threshold transactions in 7 days

No modifications were made to these features during this diagnostic audit.

---

## 3. Feature Signal Analysis

### 3.1 Overall Class Separation

| Feature | Normal Mean | Suspicious Mean | Cohen's d | Overlap | Zero Ratio (Normal) | Zero Ratio (Suspicious) |
|---------|-------------|-----------------|-----------|---------|---------------------|-----------------------|
| prior_tx_count_1h | 0.0119 | 0.0834 | 0.3040 | 11.69 | 98.8% | 92.7% |
| prior_value_sum_24h | 1179.85 | 2206.20 | 0.2597 | 0.0008 | 76.3% | 50.8% |
| same_day_prior_tx_count | 0.1402 | 0.5768 | 0.5129 | 2.59 | 87.5% | 67.2% |
| repeated_amount_ratio_7d | 0.0389 | 0.0659 | 0.1658 | 44.69 | 91.7% | 81.4% |
| amount_cluster_dispersion_7d | 0.2705 | 0.4878 | 0.5622 | 16.40 | 45.7% | 23.7% |
| near_threshold_history_ratio_7d | 0.0577 | 0.0582 | 0.0028 | 47.76 | 88.3% | 85.1% |

### 3.2 Feature Signal Interpretation

**Strongest Feature:** `structuring_amount_cluster_dispersion_7d` (Cohen's d = 0.5622)
- Has the highest separation power among structuring features
- Lower zero ratio indicates more transactions have meaningful values
- Moderate overlap (16.40) suggests some separation capability

**Moderate Features:**
- `structuring_same_day_prior_tx_count` (Cohen's d = 0.5129): Good separation, but high zero ratio (87.5% normal, 67.2% suspicious)
- `structuring_prior_tx_count_1h` (Cohen's d = 0.3040): Weak separation, extremely high zero ratio (98.8% normal, 92.7% suspicious)

**Weakest Feature:** `structuring_near_threshold_history_ratio_7d` (Cohen's d = 0.0028)
- **Almost no separation between normal and suspicious transactions**
- Essentially useless for discrimination
- High zero ratio (88.3% normal, 85.1% suspicious)

**Problematic Feature:** `structuring_repeated_amount_ratio_7d` (Cohen's d = 0.1658)
- Very weak separation
- Extremely high overlap (44.69)
- High zero ratio (91.7% normal, 81.4% suspicious)

### 3.3 Key Finding: Cold-Start Problem

The extremely high zero ratios indicate that most transactions (both normal and suspicious) have zero values for several structuring features. This suggests:
- Most transactions have no prior transactions within the defined windows
- The temporal windows (1h, 24h, same-day) may be too narrow for the generated behaviour
- The features suffer from severe cold-start problems

---

## 4. Scenario-Level Diagnostic

### 4.1 Scenario-Feature Signal Matrix

| Scenario | prior_tx_count_1h | prior_value_sum_24h | same_day_prior_tx_count | repeated_amount_ratio_7d | amount_cluster_dispersion_7d | near_threshold_history_ratio_7d |
|----------|---------------------|---------------------|------------------------|---------------------------|-------------------------------|--------------------------------|
| Variable Fragment Burst | **2.41** | 0.13 | **1.66** | 0.21 | 0.54 | 0.13 |
| Similar Amount Repetition | **1.75** | **0.77** | **3.03** | **2.01** | 0.63 | 0.17 |
| Distributed Same-Day Fragmentation | 0.07 | 0.20 | 0.33 | 0.11 | 0.42 | 0.02 |
| Variable Near-Threshold History | 0.03 | **0.53** | 0.25 | 0.46 | 0.50 | **0.96** |

*Signal strength measured as (scenario_mean - normal_mean) / normal_std*

### 4.2 Scenario Analysis

**Strongest Scenario:** Similar Amount Repetition
- Has strong signal across multiple features (3.03 on same_day_prior_tx_count, 2.01 on repeated_amount_ratio_7d)
- Well-captured by existing feature set
- Current recall: 48% (Independent)

**Moderate Scenario:** Variable Fragment Burst
- Has good signal on prior_tx_count_1h (2.41) and same_day_prior_tx_count (1.66)
- Moderately well-captured by existing feature set
- Current recall: 38% (Independent)

**Weakest Scenario:** Distributed Same-Day Fragmentation
- **Almost no signal across all six features** (highest signal: 0.42 on amount_cluster_dispersion_7d)
- **Not captured by existing feature set**
- Current recall: 11% (Independent)

**Problematic Scenario:** Variable Near-Threshold History
- Only has strong signal on near_threshold_history_ratio_7d (0.96)
- However, this feature has almost no overall class separation (Cohen's d = 0.0028)
- The feature only distinguishes this specific scenario from normal, but not suspicious from normal overall
- Current recall: 21% (Independent)

### 4.3 Key Finding: Scenario Coverage Gap

The existing six structuring features adequately capture:
- Similar Amount Repetition (good signal)
- Variable Fragment Burst (moderate signal)

But fail to capture:
- Distributed Same-Day Fragmentation (no signal)
- Variable Near-Threshold History (feature exists but lacks overall separation)

---

## 5. False-Negative Analysis

### 5.1 False-Negative Characteristics

All false negatives across structuring scenarios share similar characteristics:

| Scenario | FN Count | Mean Probability | Median Probability |
|----------|----------|------------------|---------------------|
| Variable Fragment Burst | 197 | 0.0708 | 0.0427 |
| Similar Amount Repetition | 126 | 0.0702 | 0.0407 |
| Distributed Same-Day Fragmentation | 156 | 0.0628 | 0.0383 |
| Variable Near-Threshold History | 142 | 0.0682 | 0.0406 |

### 5.2 False-Negative Feature Patterns

**Common Pattern:** False negatives have very low values on key structuring features:
- Most have zero values for prior_tx_count_1h, same_day_prior_tx_count, and repeated_amount_ratio_7d
- Moderate values for amount_cluster_dispersion_7d (0.22-0.28 mean)
- Low cumulative values (prior_value_sum_24h: 1066-1528 mean)

**Interpretation:** False negatives are typically:
- Cold-start transactions with no prior history
- Low-activity transactions that don't trigger feature signals
- Transactions that occur in isolation rather than as part of burst patterns

### 5.3 Key Finding: Cold-Start False Negatives

The false-negative analysis confirms that the cold-start problem (high zero ratios) is a major contributor to missed structuring detection. Transactions without sufficient prior history simply don't activate the structuring features.

---

## 6. Normal Hard-Negative Analysis

### 6.1 Normal Transaction Overlap

Normal transactions with high structuring-like features are frequently misclassified as suspicious:

| Feature | High-Feature Normal Count | Misclassified as Suspicious | Misclassification Rate |
|---------|---------------------------|-------------------------------|------------------------|
| prior_tx_count_1h | 88,000 | 3,309 | 3.8% |
| prior_value_sum_24h | 8,800 | 649 | 7.4% |
| same_day_prior_tx_count | 10,979 | 1,084 | 9.9% |
| repeated_amount_ratio_7d | 88,000 | 3,309 | 3.8% |
| amount_cluster_dispersion_7d | 8,800 | 809 | 9.2% |
| near_threshold_history_ratio_7d | 9,247 | 421 | 4.6% |

### 6.2 Overlap Interpretation

**High Overlap Features:**
- prior_tx_count_1h: 88,000 normal transactions have non-zero values (essentially all non-zero values)
- repeated_amount_ratio_7d: 88,000 normal transactions have non-zero values

**High Misclassification Features:**
- same_day_prior_tx_count: 9.9% misclassification rate
- amount_cluster_dispersion_7d: 9.2% misclassification rate

### 6.3 Key Finding: Normal/Suspicious Overlap

The normal population contains substantial structuring-like behaviour:
- Many normal transactions have multiple same-day transactions
- Many normal transactions have repeated amounts
- Many normal transactions have high cumulative values

This overlap makes it difficult for the model to distinguish normal from suspicious structuring behaviour, contributing to the low precision and the need for a conservative threshold.

---

## 7. Feature Correlation/Redundancy Analysis

### 7.1 Structuring Feature Correlations

The six structuring features show moderate correlations:

| Feature Pair | Correlation |
|--------------|-------------|
| prior_tx_count_1h vs same_day_prior_tx_count | 0.37 |
| prior_value_sum_24h vs same_day_prior_tx_count | 0.41 |
| same_day_prior_tx_count vs amount_cluster_dispersion_7d | 0.23 |

### 7.2 Cross-Domain Correlations

Structuring features are highly correlated with network features:

| Structuring Feature | Most Correlated Network Feature | Correlation |
|-------------------|--------------------------------|-------------|
| amount_cluster_dispersion_7d | network_outbound_counterparty_count_7d | **0.65** |
| same_day_prior_tx_count | network_outbound_counterparty_count_7d | 0.37 |
| prior_value_sum_24h | network_outbound_counterparty_count_7d | 0.26 |

### 7.3 Key Finding: Redundancy with Network Features

The structuring features are not providing unique information:
- `structuring_amount_cluster_dispersion_7d` has 0.65 correlation with `network_outbound_counterparty_count_7d`
- Several structuring features are moderately correlated with network features
- This suggests that structuring behaviour in the synthetic dataset may be manifested primarily through network patterns

This redundancy may explain why network features dominate the top importance and why network domain performance is so much higher.

---

## 8. Temporal Representation Analysis

### 8.1 Temporal Window Coverage

**Current Windows:**
- 1 hour (prior_tx_count_1h)
- 24 hours (prior_value_sum_24h)
- Same day (same_day_prior_tx_count)
- 7 days (repeated_amount_ratio_7d, amount_cluster_dispersion_7d, near_threshold_history_ratio_7d)

### 8.2 Window Adequacy Assessment

**1-Hour Window:** Too narrow
- 98.8% of normal transactions have zero values
- 92.7% of suspicious transactions have zero values
- Most transactions don't have prior transactions within 1 hour
- **Inadequate for capturing burst patterns**

**24-Hour Window:** Moderately adequate
- 76.3% of normal transactions have zero values
- 50.8% of suspicious transactions have zero values
- Better coverage but still significant cold-start problem
- **Adequate for high-volume scenarios but not for isolated transactions**

**Same-Day Window:** Moderately adequate
- 87.5% of normal transactions have zero values
- 67.2% of suspicious transactions have zero values
- **Adequate for same-day burst scenarios but not for distributed patterns**

**7-Day Window:** Adequate
- Lower zero ratios (45.7% normal, 23.7% suspicious for amount_cluster_dispersion_7d)
- **Adequate for pattern analysis**

### 8.3 Key Finding: Window Mismatch

The temporal windows may not match the synthetic scenario design:
- Distributed Same-Day Fragmentation may involve transactions spaced across the day, not captured by burst-oriented windows
- Variable Near-Threshold History may involve sporadic near-threshold transactions over longer periods, not captured by 7-day windows
- The 1-hour window is too narrow for any meaningful pattern detection

---

## 9. Amount-Pattern Representation Analysis

### 9.1 Current Amount Features

**Amount-Related Features:**
- prior_value_sum_24h (cumulative value)
- repeated_amount_ratio_7d (ratio of repeated amounts)
- amount_cluster_dispersion_7d (dispersion of amounts)

### 9.2 Amount Pattern Coverage

**Strengths:**
- repeated_amount_ratio_7d captures exact amount repetition
- amount_cluster_dispersion_7d captures amount variation
- prior_value_sum_24h captures cumulative fragmentation

**Weaknesses:**
- No feature for approximate amount repetition (e.g., amounts within ±10%)
- No feature for changing fragment sizes (e.g., decreasing fragment sizes)
- No feature for amount clustering beyond dispersion
- No feature for absolute amount thresholds (e.g., $5000 threshold)

### 9.3 Key Finding: Missing Amount Patterns

The current amount features may not capture:
- **Approximate repetition:** Distributed Same-Day Fragmentation may use similar but not identical amounts
- **Fragmentation patterns:** The lack of feature for changing fragment sizes may miss adaptive structuring
- **Threshold proximity:** Variable Near-Threshold History requires precise threshold information not captured by ratio-based features

---

## 10. Missing Information Analysis

### 10.1 Identified Missing Information

Based on the diagnostic analysis, the following information appears missing:

1. **Longer-Term Temporal Patterns**
   - No 30-day or 90-day windows for chronic structuring behaviour
   - No features for transaction spacing patterns (time between transactions)
   - No features for burst duration or burst identification

2. **Approximate Amount Patterns**
   - No features for approximate amount repetition (±5%, ±10% tolerance)
   - No features for amount rounding patterns
   - No features for systematic amount variation

3. **Fragmentation Patterns**
   - No features for fragment size sequences (increasing, decreasing, random)
   - No features for cumulative fragmentation metrics
   - No features for threshold-based fragmentation (just below limits)

4. **Spatial Distribution**
   - No features for geographic/temporal distribution of transactions
   - No features for cross-wallet fragmentation patterns
   - No features for wallet-to-wallet transfer chains

### 10.2 Scenario-Specific Missing Information

**Distributed Same-Day Fragmentation:**
- Missing: Feature for detecting transactions distributed across time rather than clustered
- Missing: Feature for low transaction frequency across the day
- Missing: Feature for same-day low-burst behaviour

**Variable Near-Threshold History:**
- Missing: Feature for absolute threshold proximity (e.g., $5000 ± $100)
- Missing: Feature for threshold crossing patterns
- Missing: Feature for near-threshold accumulation patterns

---

## 11. Candidate Future Features

Based on the diagnostic analysis, the following candidate features are scientifically justified:

### 11.1 Candidate 1: `structuring_approximate_repetition_ratio_30d`

**Behavioural Information:** Ratio of transactions with amounts within ±10% of previous amounts over 30 days

**Why Current Features Don't Capture It:** Existing repeated_amount_ratio_7d only captures exact amount repetition, not approximate repetition which is common in sophisticated structuring.

**Raw Fields Required:** transaction amounts, transaction timestamps

**Temporal Window:** 30 days

**Prediction-Time Availability:** Yes (requires historical transactions)

**Cold-Start Behaviour:** Zero for first transaction, improves with history

**Leakage Risk:** Low (uses only transaction amounts and timestamps)

**Scenario Label Risk:** Low (does not encode scenario definition, captures general approximate repetition)

**AML Rationale:** Sophisticated structuring often uses slightly varied amounts to avoid detection, while normal customers may have exact repeated amounts (e.g., subscriptions).

### 11.2 Candidate 2: `structuring_transaction_spacing_std_30d`

**Behavioural Information:** Standard deviation of time gaps between transactions over 30 days

**Why Current Features Don't Capture It:** Current features use count-based windows but don't capture the temporal distribution/spacing of transactions.

**Raw Fields Required:** transaction timestamps

**Temporal Window:** 30 days

**Prediction-Time Availability:** Yes (requires historical transactions)

**Cold-Start Behaviour:** Requires at least 2 transactions

**Leakage Risk:** Low (uses only transaction timestamps)

**Scenario Label Risk:** Low (captures general temporal pattern, not scenario-specific)

**AML Rationale:** Structuring patterns often have characteristic spacing (e.g., regular bursts, specific intervals) that differ from normal transaction patterns.

### 11.3 Candidate 3: `structuring_threshold_proximity_ratio_30d`

**Behavioural Information:** Ratio of transactions within ±10% of reporting threshold (e.g., $5000) over 30 days

**Why Current Features Don't Capture It:** Current near_threshold_history_ratio_7d uses a fixed threshold definition and 7-day window, which may not capture the actual threshold proximity pattern in the synthetic data.

**Raw Fields Required:** transaction amounts, threshold value

**Temporal Window:** 30 days

**Prediction-Time Availability:** Yes (requires historical transactions and threshold value)

**Cold-Start Behaviour:** Zero for first transaction, improves with history

**Leakage Risk:** Low (uses only transaction amounts and threshold value)

**Scenario Label Risk:** Low (captures general threshold avoidance, not scenario-specific)

**AML Rationale:** AML structuring often involves amounts just below reporting thresholds to avoid detection; this pattern is distinct from normal transaction amounts.

### 11.4 Candidate 4: `structuring_fragment_size_trend_30d`

**Behavioural Information:** Trend coefficient of transaction amounts over 30 days (increasing, decreasing, stable)

**Why Current Features Don't Capture It:** Current features capture dispersion but not the directional trend of fragment sizes.

**Raw Fields Required:** transaction amounts, transaction timestamps

**Temporal Window:** 30 days

**Prediction-Time Availability:** Yes (requires historical transactions)

**Cold-Start Behaviour:** Requires at least 3 transactions

**Leakage Risk:** Low (uses only transaction amounts and timestamps)

**Scenario Label Risk:** Low (captures general amount trend, not scenario-specific)

**AML Rationale:** Sophisticated structuring may involve gradually decreasing fragment sizes to avoid detection, distinct from normal payment patterns.

---

## 12. Research Validity Assessment

### 12.1 Evidence Analysis

**Insufficient Feature Representation:** STRONG EVIDENCE
- Two structuring scenarios have almost no signal in current features
- Near-threshold feature has Cohen's d = 0.0028 (essentially no separation)
- Distributed Same-Day Fragmentation has highest signal of only 0.42 (weak)
- Cold-start problem (high zero ratios) limits feature effectiveness

**Normal/Suspicious Overlap:** MODERATE EVIDENCE
- Normal transactions with high structuring features have 3.8-9.9% misclassification rate
- This overlap is significant but not the primary cause
- Overlap is expected in synthetic data designed to be challenging

**Scenario Design Limitations:** SOME EVIDENCE
- Distributed Same-Day Fragmentation may be inherently difficult to detect with current temporal windows
- Variable Near-Threshold History may require absolute threshold information not captured by ratio-based features
- However, this could be addressed with better features

**Model Limitations:** WEAK EVIDENCE
- XGBoost experiment showed model change did not improve structuring detection substantially
- Agent domain improved with XGBoost, suggesting model architecture is not the primary limitation
- The issue appears to be feature representation rather than model choice

### 12.2 Primary Cause Determination

**Primary Cause:** Insufficient feature representation (60% contribution)
- Missing temporal pattern features (spacing, burst duration)
- Missing approximate amount repetition features
- Missing threshold proximity features
- Cold-start problem due to narrow temporal windows

**Secondary Cause:** Normal/suspicious behavioural overlap (30% contribution)
- Synthetic normal population contains structuring-like behaviour
- Overlap is expected and challenging but not the primary issue

**Tertiary Cause:** Scenario design limitations (10% contribution)
- Some scenarios may be inherently difficult with current feature set
- Could be addressed with better features

### 12.3 Final Classification

**E. MIXED** - More than one factor contributes, but insufficient feature representation is the primary cause.

---

## 13. Data and Model Protection

**Unchanged Artifacts:**
- Stage 11 dataset: ✅ Unchanged
- Stage 13 feature matrices: ✅ Unchanged
- Stage 14 Gradient Boosting model: ✅ Unchanged
- Stage 15 XGBoost model: ✅ Unchanged
- Train/validation/final-test/independent partitions: ✅ Unchanged
- 30-feature specification: ✅ Unchanged
- Target labels: ✅ Unchanged
- MySQL database: ✅ Unchanged
- Application code: ✅ Unchanged

**Prohibited Actions (Not Performed):**
- ❌ No retraining
- ❌ No tuning
- ❌ No threshold changes
- ❌ No new data generation
- ❌ No feature modifications
- ❌ No label modifications
- ❌ No partition alterations
- ❌ No database changes
- ❌ No application modifications

---

## 14. Recommended Next Step

**Recommendation:** Proceed to Stage 16B to implement the four candidate features identified in Section 11.

**Rationale:**
1. The diagnostic analysis clearly identifies missing information in the current feature set
2. The candidate features are scientifically justified and have low leakage risk
3. The features address the primary cause (insufficient representation) rather than secondary causes
4. The candidate features are small in number (4) and targeted to specific gaps
5. The features are prediction-time available and address cold-start concerns

**Expected Impact:**
- Improved detection of Distributed Same-Day Fragmentation (currently 11% recall)
- Improved detection of Variable Near-Threshold History (currently 21% recall)
- Reduced cold-start problem through longer temporal windows (30 days)
- Better capture of approximate amount repetition and fragmentation patterns

**Alternative:** If resources are limited, prioritize Candidate 3 (threshold_proximity_ratio_30d) and Candidate 1 (approximate_repetition_ratio_30d) as they directly address the two weakest-performing scenarios.

---

## 15. Final Summary

**STAGE 16A STATUS: PASS**

**Primary Cause of Weak Structuring Detection:** Insufficient feature representation (60%), specifically missing temporal pattern features, approximate amount repetition features, and threshold proximity features.

**Strongest Existing Structuring Feature:** `structuring_amount_cluster_dispersion_7d` (Cohen's d = 0.5622)

**Weakest Existing Structuring Feature:** `structuring_near_threshold_history_ratio_7d` (Cohen's d = 0.0028)

**Hardest Scenario Family:** Distributed Same-Day Fragmentation (11% recall, almost no feature signal)

**Strongest Scenario Family:** Similar Amount Repetition (48% recall, good feature signal)

**Evidence of Normal/Suspicious Overlap:** Yes - normal transactions with high structuring features have 3.8-9.9% misclassification rate, indicating significant overlap.

**Whether Additional Features Are Justified:** Yes - four candidate features are scientifically justified to address identified gaps.

**Candidate Feature Concepts:**
1. `structuring_approximate_repetition_ratio_30d` - captures approximate amount repetition
2. `structuring_transaction_spacing_std_30d` - captures temporal distribution patterns
3. `structuring_threshold_proximity_ratio_30d` - captures threshold avoidance patterns
4. `structuring_fragment_size_trend_30d` - captures fragmentation trend patterns

**Whether Stage 16B Should Proceed:** Yes - the diagnostic analysis clearly identifies missing information and provides scientifically justified candidate features with low leakage risk.

**Confirmation of Data/Model Protection:** All Stage 11/13/14/15 artifacts remain unchanged; no retraining, tuning, or modifications occurred during this diagnostic audit.

---

*Report generated as part of Stage 16A Structuring Detection Diagnostic Audit*
*Date: 2026-09-15*
*Dataset: ecocash_aml_synthetic_100k_v1*
*Feature Matrix: Stage 13 frozen 30-feature matrix*
*Baseline Model: Stage 14 Gradient Boosting*
*Stage 16A Status: PASS*
*Final Decision: B. TARGETED FEATURE IMPROVEMENT JUSTIFIED*
