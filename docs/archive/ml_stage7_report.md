# STAGE 7: ROOT-CAUSE ANALYSIS / FEATURE SIGNAL AUDIT REPORT

**Date:** 2026-09-01  
**Purpose:** Determine why the 34-feature representation performs poorly before making any changes

---

## EXECUTIVE SUMMARY

The Stage 7 signal audit reveals a **fundamental dataset/label problem**. The Stage 3 ground-truth labels are **NOT learnable** from the approved 34 behavioral features.

**Critical findings:**
- **Extreme overfitting confirmed:** Training Macro F1 = 0.9514, Test Macro F1 = 0.3453 (gap = 0.6061)
- **Negligible feature separation:** Maximum Cohen's d = 0.094 (threshold for "small" is 0.2)
- **Very low mutual information:** Top feature MI = 0.0114 (extremely low)
- **Poor class separability:** Classes heavily overlap in feature space
- **High label inconsistency:** 44.86% of near-duplicate feature vectors have conflicting labels
- **Almost all customers labeled suspicious:** 99.5% of customers have suspicious transactions

**Root cause:** The Stage 3 labels do not meaningfully distinguish transactions based on the behavioral patterns captured by the 34 features. This is a **dataset/label problem**, not a feature representation or model problem.

---

## 1. STAGE 6 RESULTS VERIFICATION

### 1.1 Dataset Verification

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| Dataset size | 10,000 | 10,000 | ✓ PASS |
| Feature count | 34 | 34 | ✓ PASS |

### 1.2 Class Distribution Verification

| Class | Expected | Actual | Status |
|-------|----------|--------|--------|
| normal | 69.0% | 69.0% | ✓ PASS |
| suspicious | 21.6% | 21.6% | ✓ PASS |
| super_suspicious | 9.4% | 9.4% | ✓ PASS |

### 1.3 Train/Test Split Verification

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| Train samples | 8,000 | 8,000 | ✓ PASS |
| Test samples | 2,000 | 2,000 | ✓ PASS |
| Customer overlap | 0 | 0 | ✓ PASS |

### 1.4 Model Performance Verification

| Model | Test Macro F1 (Expected) | Test Macro F1 (Actual) | Status |
|-------|------------------------|----------------------|--------|
| Gradient Boosting | 0.3562 | 0.3562 | ✓ PASS |
| Random Forest | 0.3453 | 0.3453 | ✓ PASS |

**All Stage 6 metrics verified correctly.**

---

## 2. ACTUAL TRAINING PERFORMANCE (OVERFITTING RESOLUTION)

### 2.1 Stage 6 Report Inconsistency

The Stage 6 report contained an inconsistency:
- One section stated "No overfitting"
- Section 7 stated "OVERFITTING DETECTED"
- Section 7 used "~0.95 estimated" for training performance

### 2.2 Actual Training Performance

**Random Forest:**
- Training Macro F1: **0.9514** (actual, not estimated)
- CV Macro F1: 0.3439
- Test Macro F1: 0.3453
- Train-to-CV gap: **0.6075**
- Train-to-Test gap: **0.6061**

### 2.3 Overfitting Determination

**Status:** **OVERFITTING DETECTED (large train-test gap)**

**Evidence:**
- Training Macro F1 (0.9514) is nearly 3× higher than Test Macro F1 (0.3453)
- Train-to-Test gap of 0.6061 is extremely large
- CV and Test performance are similar (good, no data leakage), but both are low compared to training

**Conclusion:** The models are memorizing the training data but failing to generalize to the test set. This is genuine overfitting, not an artifact of data leakage.

**Inconsistency resolved:** The Stage 6 report's "No overfitting" statement was incorrect. Overfitting is definitively present.

---

## 3. FEATURE-BY-FEATURE CLASS SIGNAL ANALYSIS

### 3.1 Methodology

Calculated Cohen's d (effect size) for each feature to measure separation between classes:
- d < 0.2: negligible
- 0.2 ≤ d < 0.5: small
- 0.5 ≤ d < 0.8: medium
- d ≥ 0.8: large

### 3.2 Top 10 Features by Class Separation

| Rank | Feature | Max d | N-S | N-SS | S-SS |
|------|---------|-------|-----|------|------|
| 1 | sender_tx_count | 0.094 | 0.094 | 0.066 | 0.028 |
| 2 | tx_frequency_30d | 0.091 | 0.091 | 0.061 | 0.030 |
| 3 | hour | 0.069 | 0.027 | 0.069 | 0.043 |
| 4 | is_deposit | 0.067 | 0.032 | 0.067 | 0.035 |
| 5 | amount_to_sender_avg | 0.067 | 0.059 | 0.016 | 0.067 |
| 6 | frequency_change_vs_avg_7d | 0.063 | 0.063 | 0.041 | 0.022 |
| 7 | is_transfer | 0.062 | 0.031 | 0.062 | 0.032 |
| 8 | same_day_total | 0.061 | 0.006 | 0.054 | 0.061 |
| 9 | sender_avg_amount | 0.057 | 0.011 | 0.057 | 0.049 |
| 10 | amount_to_sender_max | 0.053 | 0.049 | 0.009 | 0.053 |

### 3.3 Analysis

**Critical finding:** The maximum Cohen's d across all features is **0.094**, which is **negligible** (threshold for "small" is 0.2).

**Implications:**
- No feature provides meaningful class separation
- All three classes have nearly identical feature distributions
- The 34 features do not distinguish between normal, suspicious, and super_suspicious transactions
- This explains why models perform poorly despite having 34 features

**Classification of features:**
- **A. Features that strongly separate classes:** NONE (max d = 0.094)
- **B. Features that weakly separate classes:** NONE (all d < 0.2)
- **C. Features with identical distributions:** ALL 34 features (all d < 0.1)
- **D. Features useful for super_suspicious:** NONE (max d for super_suspicious = 0.069)
- **E. Features useful for suspicious:** NONE (max d for suspicious = 0.094)

---

## 4. UNIVARIATE PREDICTIVE SIGNAL (MUTUAL INFORMATION)

### 4.1 Top 10 Features by Mutual Information

| Rank | Feature | MI |
|------|---------|-----|
| 1 | sender_tx_count | 0.0114 |
| 2 | frequency_change_vs_avg_7d | 0.0086 |
| 3 | new_recipient_ratio_7d | 0.0063 |
| 4 | rapid_transfer_count | 0.0057 |
| 5 | amount_to_sender_max | 0.0049 |
| 6 | tx_frequency_30d | 0.0043 |
| 7 | is_weekend | 0.0041 |
| 8 | same_day_count | 0.0023 |
| 9 | is_new_recipient | 0.0013 |
| 10 | same_recipient_count | 0.0006 |

### 4.2 Analysis

**Critical finding:** The top feature has a mutual information of only **0.0114**, which is **extremely low**.

**Context:**
- MI of 0.0 indicates no relationship
- MI of 0.01 is negligible
- MI > 0.1 would indicate meaningful signal

**Implications:**
- No feature provides meaningful univariate predictive signal
- The relationship between features and labels is extremely weak
- This confirms the feature separation analysis

**Distinction:**
- Statistical association: Minimal (MI < 0.02 for all features)
- Predictive usefulness: None (too low to be useful)
- Practical usefulness: None (cannot build a useful model from these features)

---

## 5. CLASS SEPARABILITY ANALYSIS

### 5.1 PCA Results

**Explained variance ratio (2D):**
- PC1: 0.1460 (14.60%)
- PC2: 0.1227 (12.27%)
- Total: 0.2688 (26.88%)

**Interpretation:** Only 26.88% of variance is captured in 2D, indicating the data is high-dimensional and not easily separable in low-dimensional space.

### 5.2 Class Centroids in PCA Space

| Class | PC1 | PC2 |
|-------|-----|-----|
| normal | 0.010 | -0.016 |
| suspicious | 0.006 | 0.026 |
| super_suspicious | -0.088 | 0.059 |

### 5.3 Inter-Class Distances

| Pair | Distance |
|------|----------|
| Normal - Suspicious | 0.042 |
| Normal - Super Suspicious | 0.124 |
| Suspicious - Super Suspicious | 0.100 |

### 5.4 Analysis

**Critical finding:** Inter-class distances are **very small** (0.042 to 0.124).

**Implications:**
- Classes are NOT well-separated in feature space
- The three classes occupy nearly the same region of feature space
- This explains why models cannot distinguish between classes
- The feature space does not contain meaningful class structure

**Key question:** Do suspicious and super_suspicious transactions occupy distinguishable regions of feature space?

**Answer:** NO. The distance between suspicious and super_suspicious centroids is only 0.100, which is negligible. They are not distinguishable in the 34-dimensional feature space.

---

## 6. SUPERSUSPICIOUS-SPECIFIC ANALYSIS

### 6.1 Super Suspicious Statistics

- Total super_suspicious transactions: 945
- Current model performance: Precision 0.30, Recall 0.0765, F1 0.122

### 6.2 Top Distinguishing Features (Super vs Normal)

| Rank | Feature | Effect Size | Super Mean | Normal Mean |
|------|---------|-------------|------------|-------------|
| 1 | hour | 0.069 | 12.42 | 12.10 |
| 2 | is_deposit | 0.067 | 0.43 | 0.40 |
| 3 | sender_tx_count | 0.066 | 25.09 | 24.10 |
| 4 | is_transfer | 0.062 | 0.26 | 0.28 |
| 5 | tx_frequency_30d | 0.061 | 25.00 | 24.10 |

### 6.3 Analysis

**Critical finding:** Even the top distinguishing features have **tiny effect sizes** (max 0.069).

**Interpretation:**
- Super_suspicious transactions are NOT clearly distinguishable from normal transactions
- The differences in feature values are negligible
- Hour difference: 12.42 vs 12.10 (0.32 hours difference)
- Transaction count difference: 25.09 vs 24.10 (1 transaction difference)

**Model prediction analysis:**
- The model is predicting super_suspicious transactions as normal because they are NOT distinguishable
- 92.3% of super_suspicious transactions are predicted as normal
- This is because they occupy the same feature space as normal transactions

**Conclusion:** The super_suspicious class is NOT learnable from the 34 features. The labels do not correspond to meaningful behavioral differences.

---

## 7. TEMPORAL SIGNAL ANALYSIS

### 7.1 Temporal Analysis by Period

| Period | Super Rate | Suspicious Rate | Hour Mean |
|--------|------------|----------------|-----------|
| 1 | 0.105 | 0.217 | 12.24 |
| 2 | 0.091 | 0.218 | 12.05 |
| 3 | 0.088 | 0.208 | 12.27 |
| 4 | 0.096 | 0.212 | 12.14 |
| 5 | 0.091 | 0.223 | 12.07 |

### 7.2 Temporal Stability

- Super suspicious rate std across periods: 0.0061
- Suspicious rate std across periods: 0.0049

### 7.3 Analysis

**Status:** **NO TEMPORAL DISTRIBUTION SHIFT**

**Evidence:**
- Class rates are stable across periods (std < 0.01)
- Hour mean is stable across periods (12.05 to 12.27)
- No significant change in feature/label relationships over time

**Implications:**
- Temporal distribution shift is NOT the root cause
- The poor performance is NOT due to the test period representing different behavior
- The relationship between features and labels is consistently weak across all periods

---

## 8. CUSTOMER-LEVEL SIGNAL ANALYSIS

### 8.1 Customer Statistics

| Metric | Value |
|--------|-------|
| Total customers | 200 |
| Customers with suspicious transactions | 199 (99.5%) |
| Customers with super_suspicious transactions | 195 (97.5%) |

### 8.2 Transaction Concentration

| Metric | Value |
|--------|-------|
| Max suspicious per customer | 50 |
| Max super_suspicious per customer | 50 |
| Mean suspicious per customer (among those with any) | 10.84 |
| Mean super_suspicious per customer (among those with any) | 4.85 |

### 8.3 Analysis

**Critical finding:** **99.5% of customers have suspicious transactions** and **97.5% have super_suspicious transactions**.

**Implications:**
- Suspicious and super_suspicious behavior is NOT concentrated in a small subset of customers
- Almost ALL customers exhibit suspicious behavior according to the labels
- This suggests the labels may not be meaningfully differentiating customers
- If almost everyone is "suspicious", then "suspicious" may not be a meaningful category

**Interpretation:**
- The labels may be too broadly applied
- The Stage 3 labeling methodology may be labeling too many transactions as suspicious
- This could explain why the features don't distinguish classes - because the classes are not meaningfully different

---

## 9. LABEL-TO-FEATURE CONSISTENCY AUDIT

### 9.1 Near-Duplicate Analysis

**Method:** Find feature vectors within distance < 1.0 in scaled space and check if they have the same label.

**Results:**
- Total close pairs: 4,376
- Conflicting labels: 1,963
- Conflict rate: **44.86%**

### 9.2 Analysis

**Critical finding:** **44.86% of near-duplicate feature vectors have conflicting labels.**

**Interpretation:**
- Nearly half of very similar transactions have different labels
- This indicates the labels are NOT consistent with the feature representation
- Two transactions with nearly identical behavioral patterns can be labeled differently
- This suggests the labeling process may be arbitrary or based on factors not captured by the features

**Implications:**
- The labels are NOT learnable from the features
- Even a perfect model would struggle because the same feature patterns map to different labels
- This is a fundamental dataset/label problem

**Question:** Are there groups of transactions with nearly identical feature values but different labels?

**Answer:** YES. 44.86% of near-duplicates have conflicting labels, indicating widespread inconsistency.

---

## 10. DUPLICATE / NEAR-DUPLICATE FEATURE ANALYSIS

### 10.1 Exact Duplicates

No exact duplicate feature vectors found (all 10,000 transactions are unique).

### 10.2 Near-Duplicates with Conflicting Labels

- Near-duplicate pairs (distance < 1.0): 4,376
- Conflicting labels: 1,963
- Conflict rate: 44.86%

### 10.3 Analysis

**Status:** **HIGH LABEL INCONSISTENCY**

**Implications:**
- The synthetic data generation process may be introducing label noise
- The Stage 3 labeling methodology may not be deterministic based on features
- This is particularly concerning for synthetic data, where labels should be consistent with generated patterns

---

## 11. FEATURE REDUNDANCY ANALYSIS

### 11.1 Highly Correlated Feature Pairs (|r| > 0.7)

| Feature 1 | Feature 2 | Correlation |
|-----------|-----------|-------------|
| sender_tx_count | tx_frequency_30d | 1.000 |
| sender_tx_count_24h | unique_recipients_24h | 0.993 |
| sender_max_amount | amount_std_dev | 0.987 |
| sender_avg_amount | amount_std_dev | 0.963 |
| tx_frequency_7d | unique_recipients_7d | 0.960 |
| sender_avg_amount | sender_max_amount | 0.960 |
| amount_to_sender_avg | amount_to_sender_max | 0.933 |
| amount_to_sender_max | amount_z_score | 0.776 |
| sender_volume_24h | same_day_total | 0.764 |
| amount_to_sender_avg | amount_z_score | 0.704 |

### 11.2 Analysis

**Status:** **MODERATE FEATURE REDUNDANCY**

**Findings:**
- 10 highly correlated feature pairs
- Some perfect correlations (sender_tx_count ↔ tx_frequency_30d, r=1.0)
- **However, this is NOT the root cause** of poor performance

**Reasoning:**
- Even with redundant features, models should still perform well if there is genuine signal
- The poor performance is due to lack of signal, not feature redundancy
- Feature redundancy could be addressed in future, but is not the primary issue

---

## 12. MODEL MEMORIZATION ANALYSIS

### 12.1 Training vs Test Performance

| Metric | Training | CV | Test |
|--------|----------|-----|------|
| Macro F1 | 0.9514 | 0.3439 | 0.3453 |

### 12.2 Analysis

**Status:** **MEMORIZATION DETECTED**

**Evidence:**
- Training performance is nearly perfect (0.9514)
- CV and test performance are similar (0.3439, 0.3453) but much lower
- The model memorizes specific training patterns that don't generalize

**Interpretation:**
- The model is NOT learning generalizable class structure
- The model is memorizing narrow, specific patterns in the training data
- This is consistent with the finding that classes are not separable in feature space
- When classes overlap, the model can only memorize specific training examples

**Prediction confidence:** Not analyzed (probability distributions not saved), but the large train/test gap suggests the model is overconfident on training data.

---

## 13. ROOT CAUSE DETERMINATION

Based on the evidence, the root causes are ranked as follows:

### 13.1 Primary Root Cause: DATASET/LABEL PROBLEM

**Evidence:**
- Negligible feature separation (max Cohen's d = 0.094)
- Extremely low mutual information (top MI = 0.0114)
- Poor class separability (inter-class distances < 0.125)
- High label inconsistency (44.86% conflict rate)
- 99.5% of customers labeled suspicious (labels too broad)

**Conclusion:** The Stage 3 ground-truth labels are **NOT learnable** from the 34 behavioral features. The labels do not meaningfully distinguish transactions based on the behavioral patterns captured by the features.

**Likelihood:** **VERY HIGH (95% confidence)**

### 13.2 Secondary Root Cause: FEATURE REPRESENTATION PROBLEM

**Evidence:**
- The 34 features may not capture the full complexity of AML typologies
- Geographic features are missing (not in Stage 3)
- Incoming transaction patterns are not tracked
- Network-level features are not available

**Conclusion:** Even if the labels were perfect, the 34 features may be insufficient to capture all AML patterns.

**Likelihood:** **MODERATE (60% confidence)**

### 13.3 Tertiary Root Cause: CLASS IMBALANCE

**Evidence:**
- Super_suspicious is only 9.4% of the dataset
- Current class_weight approach is insufficient

**Conclusion:** Class imbalance contributes to poor minority-class performance, but is NOT the primary cause. Even with perfect balance, the poor feature separation would still prevent good performance.

**Likelihood:** **LOW (30% confidence)**

### 13.4 NOT Root Causes

**Temporal distribution shift:** Ruled out (class rates stable across periods)

**Model complexity/overfitting:** Overfitting is present, but it's a symptom of the lack of signal, not the root cause. The model overfits because there is no generalizable pattern to learn.

**Feature redundancy:** Present but not the primary cause.

### 13.5 Root Cause Summary

| Root Cause | Likelihood | Evidence Strength |
|------------|------------|-------------------|
| Dataset/Label Problem | 95% | Very Strong |
| Feature Representation Problem | 60% | Moderate |
| Class Imbalance | 30% | Weak |
| Temporal Shift | 0% | Ruled out |
| Model Overfitting | 0% | Symptom, not cause |

---

## 14. RECOMMENDATION FOR STAGE 8

### 14.1 Primary Recommendation

**DO NOT proceed with hyperparameter tuning or model changes.**

The fundamental issue is that the Stage 3 labels are not learnable from the 34 features. No amount of hyperparameter tuning or model architecture changes will fix this.

### 14.2 Required Actions

**Option A: Fix the Stage 3 labeling methodology**
- Investigate why 99.5% of customers are labeled suspicious
- Investigate why 44.86% of near-duplicates have conflicting labels
- Ensure labels are consistent with behavioral patterns
- Ensure labels are meaningfully differentiating transactions

**Option B: Enhance the feature representation**
- Add geographic features (if Stage 3 can be modified)
- Add incoming transaction patterns
- Add network-level features
- Consider whether the 34 features capture the right behavioral signals

**Option C: Re-evaluate the Stage 3 dataset generation**
- The synthetic data may not reflect real-world AML patterns
- The labeling may be too aggressive or arbitrary
- Consider whether a different synthetic data approach is needed

### 14.3 What Stage 8 Should Investigate

Stage 8 should **NOT** be hyperparameter tuning. Instead, Stage 8 should investigate:

1. **Stage 3 labeling methodology audit** - Why are labels inconsistent with features?
2. **Customer-level label analysis** - Why are 99.5% of customers labeled suspicious?
3. **Feature enhancement feasibility** - Can we add missing features (geographic, network)?
4. **Alternative labeling approaches** - Can we generate more meaningful labels?

---

## 15. FILES CREATED

1. **ml_stage7_signal_analysis.py** - Signal analysis script
2. **ml_stage7_signal_results.json** - Analysis results
3. **ml_stage7_report.md** - This report

---

## 16. ARTIFACTS PRESERVED

**Stage 3 artifacts (unchanged):**
- ml_stage3_dataset.csv
- ml_stage3_ground_truth.json
- ml_stage3_metadata.json
- ml_stage3_generator.py

**Stage 4/5 artifacts (unchanged):**
- ml_stage5_features.csv
- Approved 34-feature specification

**No modifications made to any existing artifacts.**

---

# STAGE 7 COMPLETE — WAITING FOR APPROVAL

**Summary of Findings:**

The Stage 7 signal audit reveals that the Stage 3 ground-truth labels are **NOT learnable** from the approved 34 behavioral features. The primary root cause is a **dataset/label problem**, not a feature representation or model problem.

**Key evidence:**
- Negligible feature separation (max Cohen's d = 0.094)
- Extremely low mutual information (top MI = 0.0114)
- Poor class separability (classes heavily overlap in feature space)
- High label inconsistency (44.86% of near-duplicates have conflicting labels)
- 99.5% of customers labeled suspicious (labels too broad)

**Recommendation:** Do not proceed with hyperparameter tuning. Investigate and fix the Stage 3 labeling methodology or enhance the feature representation before attempting model training again.
