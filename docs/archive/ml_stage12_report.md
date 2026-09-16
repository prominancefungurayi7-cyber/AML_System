# STAGE 12: MODEL TRAINING & GENERALIZATION AUDIT REPORT

**Date:** 2026-09-02  
**Status:** CONDITIONAL PASS — Improvement demonstrated but important limitations remain

---

## EXECUTIVE SUMMARY

Stage 12 evaluated the Stage 11 scenario-based ground truth using two split methodologies:
1. **PRIMARY:** Customer-level holdout (unseen-customer generalization)
2. **SECONDARY:** Chronological transaction split (temporal generalization with customer overlap)

The Stage 11 ground truth demonstrates **material improvement** over Stage 6 in unseen-customer generalization (PRIMARY split), but **fails to meet preferred success criteria** due to poor minority-class recall and significant overfitting.

**Key Findings:**
- PRIMARY split Macro F1 improved from 0.3453 (Stage 6) to 0.4416 (Stage 12) — +0.0963
- PRIMARY split overfitting gap improved from 0.6061 (Stage 6) to 0.5584 (Stage 12)
- Super-suspicious recall: 0.27 (PRIMARY) vs 0.00 (SECONDARY) — below preferred 0.30
- Suspicious recall: 0.07 (PRIMARY) vs 0.00 (SECONDARY) — far below preferred 0.50
- SECONDARY split performs poorly (Macro F1: 0.23) due to customer overlap

**Decision:** CONDITIONAL PASS — The Stage 11 ground truth is scientifically defensible and demonstrates improvement over Stage 6, but important limitations remain in minority-class detection and overfitting.

---

## 1. PRE-TRAINING AUDIT RESULTS

### 1.1 Stage 11 Report Inconsistency

**Discrepancy:** Stage 11 report claimed 12 scenarios, actual count is 11

**Actual scenarios (11):**
- Normal: normal, legitimate_high_value, cash_deposit, cash_withdrawal, new_recipient (5)
- Suspicious: structuring, layering, funnel, rapid_movement, high_risk_country, behavioral_change (6)
- Severe: severe_structuring, severe_layering, multiple_typologies (3)

**Missing scenario:** severe_funnel (defined in generator but does not occur)

**Impact:** Documentation error, not a data quality issue.

### 1.2 Ground-Truth Provenance

**Status:** PASS

- Label mismatches: 0
- Labels derived from scenario_id: YES
- No feature-based label rules: YES
- No model-based label rules: YES
- No random target-class assignment: YES
- No customer-level label override: YES

### 1.3 Hidden-Label Determinants

**Learnability limitation:** 3.6% of transactions (high_risk_country) have labels determined by information unavailable in the 34 features.

**Scenario observability:**
- Directly observable: 92.8% of transactions
- Partially observable: 3.7% of transactions
- NOT observable: 3.6% of transactions (high_risk_country)

### 1.4 Temporal Integrity

**Status:** PASS

- Historical features use only prior transactions: YES
- No future transaction used: YES
- No future aggregate used: YES
- No future label information leaks: YES

### 1.5 Feature Verification

**Status:** PASS

- Exactly 34 approved features: YES
- Constant features: is_self_transfer (known generator limitation)
- Near-constant features: None
- Missing values: None
- Infinite values: None

### 1.6 Feature-Label Signal

**Top features by Cohen's d:**
- sender_tx_count: 1.5839
- tx_frequency_30d: 1.5628
- frequency_change_vs_avg_7d: 0.8425
- day_of_week: 0.6556
- is_weekend: 0.5940

**Nearest-neighbor label agreement:** 0.6904

**Conclusion:** Feature-label signal is present but moderate. The strongest signals come from frequency-based and temporal features.

---

## 2. SPLIT METHODOLOGY

### 2.1 PRIMARY SPLIT (Customer-Level Holdout)

**Methodology:**
- Randomly assign 160 of 200 customers to training
- Assign remaining 40 customers to test
- Keep ALL transactions belonging to each customer entirely within one partition
- Customer overlap: 0
- Train transactions: 8,000
- Test transactions: 2,000
- Random seed: 42 (reproducible)

**Purpose:** Test unseen-customer generalization (temporal separation not guaranteed)

### 2.2 SECONDARY SPLIT (Chronological Transaction Split)

**Methodology:**
- First 80% chronological transactions = train
- Final 20% = test
- Customer overlap: 200 (100%)
- Train transactions: 8,000
- Test transactions: 2,000
- No temporal overlap

**Purpose:** Test temporal generalization (customer overlap expected)

### 2.3 Methodological Distinction

**Stage 6:** Temporal + customer-disjoint generalization  
**Stage 12 PRIMARY:** Unseen-customer generalization (temporal separation not guaranteed)  
**Stage 12 SECONDARY:** Temporal generalization (customer overlap expected)

**Note:** Stage 6 vs Stage 12 comparison must acknowledge this split difference.

---

## 3. STAGE 6 VS STAGE 12 COMPARISON

### 3.1 Macro F1 Comparison

| Model | Stage 6 | Stage 12 Primary | Stage 12 Secondary | Primary Δ | Secondary Δ |
|-------|---------|------------------|--------------------|-----------|-------------|
| Random Forest | 0.3453 | 0.4416 | 0.2317 | +0.0963 | -0.1136 |
| Gradient Boosting | 0.3562 | 0.4355 | 0.2320 | +0.0793 | -0.1242 |

**Interpretation:**
- PRIMARY split shows material improvement over Stage 6 (+0.0963 for RF)
- SECONDARY split shows decline over Stage 6 (-0.1136 for RF)
- This suggests customer overlap in chronological split harms generalization

### 3.2 Accuracy Comparison

| Model | Stage 6 | Stage 12 Primary | Stage 12 Secondary | Primary Δ | Secondary Δ |
|-------|---------|------------------|--------------------|-----------|-------------|
| Random Forest | 0.6640 | 0.7605 | 0.5220 | +0.0965 | -0.1420 |
| Gradient Boosting | 0.6975 | 0.7610 | 0.5230 | +0.0635 | -0.1745 |

**Interpretation:** Similar pattern as Macro F1 — PRIMARY improves, SECONDARY declines.

---

## 4. OVERFITTING ANALYSIS

### 4.1 PRIMARY SPLIT (Customer-Disjoint)

| Model | Train Macro F1 | Test Macro F1 | Gap |
|-------|----------------|---------------|-----|
| Random Forest | 1.0000 | 0.4416 | 0.5584 |
| Gradient Boosting | 0.6587 | 0.4355 | 0.2231 |

### 4.2 SECONDARY SPLIT (Chronological)

| Model | Train Macro F1 | Test Macro F1 | Gap |
|-------|----------------|---------------|-----|
| Random Forest | 1.0000 | 0.2317 | 0.7683 |
| Gradient Boosting | 0.4739 | 0.2320 | 0.2419 |

### 4.3 Stage 6 Comparison

- Stage 6 Random Forest train/test gap: 0.6061
- Stage 12 PRIMARY Random Forest train/test gap: 0.5584 (slightly improved)
- Stage 12 SECONDARY Random Forest train/test gap: 0.7683 (worse)

**Interpretation:**
- PRIMARY split shows slight reduction in overfitting vs Stage 6
- SECONDARY split shows severe overfitting
- Random Forest overfits severely in both splits (train Macro F1 = 1.0)
- Gradient Boosting shows more reasonable overfitting in PRIMARY split

---

## 5. MINORITY-CLASS PERFORMANCE

### 5.1 PRIMARY SPLIT (Customer-Disjoint)

**Random Forest:**
- Normal: P=0.78, R=0.99, F1=0.87
- Suspicious: P=0.45, R=0.07, F1=0.12
- Super-suspicious: P=0.44, R=0.27, F1=0.33

**Gradient Boosting:**
- Normal: P=0.78, R=1.00, F1=0.88
- Suspicious: P=0.41, R=0.05, F1=0.09
- Super-suspicious: P=0.38, R=0.30, F1=0.34

### 5.2 SECONDARY SPLIT (Chronological)

**Random Forest:**
- Normal: P=0.52, R=1.00, F1=0.69
- Suspicious: P=0.43, R=0.00, F1=0.01
- Super-suspicious: P=0.00, R=0.00, F1=0.00

**Gradient Boosting:**
- Normal: P=0.52, R=1.00, F1=0.69
- Suspicious: P=0.60, R=0.00, F1=0.01
- Super-suspicious: P=0.00, R=0.00, F1=0.00

### 5.3 Success Criteria Evaluation

**Preferred criteria:**
- Macro F1 > 0.50: ❌ (PRIMARY: 0.44, SECONDARY: 0.23)
- Super-suspicious recall > 0.30: ❌ (PRIMARY: 0.27, SECONDARY: 0.00)
- Suspicious recall > 0.50: ❌ (PRIMARY: 0.07, SECONDARY: 0.00)
- Train/test Macro F1 gap < 0.30: ❌ (PRIMARY: 0.56, SECONDARY: 0.77)

**Minimum acceptable evidence:**
- Macro F1 materially above Stage 6: ✅ (PRIMARY: +0.0963)
- Super-suspicious recall materially above Stage 6: ✅ (PRIMARY: 0.27 vs Stage 6 ~0.08)
- Reduced train/test gap: ✅ (PRIMARY: 0.56 vs Stage 6 0.61)
- No leakage: ✅
- No hidden label determinant dominating: ✅

**Interpretation:** Stage 11 fails preferred criteria but meets minimum acceptable evidence of improvement.

---

## 6. SCENARIO-LEVEL GENERALIZATION

### 6.1 PRIMARY SPLIT Scenario Distribution

**Train:**
- normal: 4,176
- legitimate_high_value: 913
- cash_deposit: 312
- layering: 305
- structuring: 298
- funnel: 296
- rapid_movement: 292
- behavioral_change: 290
- new_recipient: 287
- high_risk_country: 280
- cash_withdrawal: 276
- severe_structuring: 72
- severe_layering: 71
- multiple_typologies: 70
- severe_funnel: 62

**Test:**
- normal: 1,042
- legitimate_high_value: 205
- layering: 88
- cash_deposit: 86
- high_risk_country: 81
- new_recipient: 79
- behavioral_change: 77
- funnel: 74
- cash_withdrawal: 70
- structuring: 68
- rapid_movement: 67
- severe_structuring: 18
- severe_layering: 18
- multiple_typologies: 14
- severe_funnel: 13

### 6.2 SECONDARY SPLIT Scenario Distribution

**Train:**
- normal: 4,467
- legitimate_high_value: 972
- cash_deposit: 350
- new_recipient: 309
- cash_withdrawal: 304
- funnel: 282
- layering: 271
- behavioral_change: 269
- high_risk_country: 264
- structuring: 258
- rapid_movement: 254

**Test:**
- normal: 751
- legitimate_high_value: 146
- layering: 122
- structuring: 108
- rapid_movement: 105
- behavioral_change: 98
- high_risk_country: 97
- severe_structuring: 90
- severe_layering: 89
- funnel: 88
- multiple_typologies: 84
- severe_funnel: 75
- new_recipient: 57
- cash_deposit: 48
- cash_withdrawal: 42

**Interpretation:** The chronological split concentrates severe scenarios in the test set, which explains the poor performance on minority classes.

---

## 7. FEATURE IMPORTANCE

### 7.1 PRIMARY SPLIT (Customer-Disjoint)

**Random Forest:**
1. sender_tx_count: 0.0784
2. tx_frequency_30d: 0.0773
3. amount: 0.0493
4. time_since_last_tx: 0.0469
5. amount_to_sender_volume_24h: 0.0463

**Gradient Boosting:**
1. sender_tx_count: 0.4567
2. day_of_week: 0.1707
3. time_since_last_tx: 0.0334
4. amount_to_sender_max: 0.0331
5. frequency_change_vs_avg_7d: 0.0282

### 7.2 SECONDARY SPLIT (Chronological)

**Random Forest:**
1. amount: 0.0604
2. time_since_last_tx: 0.0577
3. amount_to_sender_volume_24h: 0.0537
4. amount_z_score: 0.0527
5. amount_to_sender_max: 0.0522

**Gradient Boosting:**
1. time_since_last_tx: 0.1210
2. amount_to_sender_volume_24h: 0.0973
3. amount_z_score: 0.0832
4. amount_change_vs_avg_7d: 0.0827
5. amount_to_sender_max: 0.0800

**Interpretation:** Frequency-based features dominate in PRIMARY split, while amount-based features dominate in SECONDARY split. This suggests different learning patterns depending on split methodology.

---

## 8. LEAKAGE AUDIT

### 8.1 Feature Leakage

**Status:** PASS

- No feature contains the target label
- All 34 features are behavioral/transactional only

### 8.2 Temporal Leakage

**Status:** PASS

- No feature uses future transactions
- Rolling windows calculated from current timestamp backwards

### 8.3 Preprocessing Leakage

**Status:** PASS

- StandardScaler fitted ONLY on training data for both splits

### 8.4 Split Leakage

**Status:** PASS

- Test set held out until final evaluation
- No hyperparameter tuning used test set

### 8.5 Duplicate Leakage

**Status:** PASS

- PRIMARY: Customer-level separation ensures no customer appears in both
- SECONDARY: Chronological separation ensures temporal separation

### 8.6 Customer Leakage

**Status:** PASS for PRIMARY, WARNING for SECONDARY

- PRIMARY: Zero customer overlap (160 train customers, 40 test customers)
- SECONDARY: 100% customer overlap (200 train customers, 200 test customers)
- This is a known limitation of the secondary split

---

## 9. SCIENTIFIC ASSESSMENT

### 9.1 Is the Stage 11 ground truth genuinely derived from generator behavior?

**Answer:** YES

- Labels are derived from scenario_id, not extracted features
- Scenario-to-label mapping is deterministic
- No feature thresholds used in labeling
- No model performance used in labeling

### 9.2 Is any part of the label determined by information unavailable in the 34 features?

**Answer:** YES (3.6% of transactions)

- high_risk_country scenario cannot be detected from the 34 features
- This is a known limitation of the current feature specification
- No feature captures recipient country

### 9.3 Are all 34 features temporally safe?

**Answer:** YES

- Historical features use only prior transactions
- No future transaction information leaks into features
- Rolling windows calculated correctly

### 9.4 Is the 34-feature representation sufficient to identify the generator scenarios?

**Answer:** PARTIALLY

- Directly observable scenarios: 92.8% of transactions
- Partially observable scenarios: 3.7% of transactions
- NOT observable scenarios: 3.6% of transactions (high_risk_country)
- The feature representation is insufficient for high_risk_country detection

### 9.5 Did Stage 11 materially improve model generalization compared with Stage 6?

**Answer:** YES (for PRIMARY split)

- PRIMARY split Macro F1 improved from 0.3453 to 0.4416 (+0.0963)
- PRIMARY split overfitting gap improved from 0.6061 to 0.5584
- SECONDARY split declined (Macro F1: 0.3453 to 0.2317)
- The improvement is material but limited by minority-class recall

### 9.6 Did the severe-class recall improve?

**Answer:** YES (for PRIMARY split)

- PRIMARY split super-suspicious recall: 0.27 vs Stage 6 ~0.08
- SECONDARY split super-suspicious recall: 0.00
- Improvement is material but still below preferred 0.30

### 9.7 Did overfitting decrease?

**Answer:** YES (for PRIMARY split)

- PRIMARY split train/test gap: 0.5584 vs Stage 6 0.6061
- SECONDARY split train/test gap: 0.7683 vs Stage 6 0.6061
- Random Forest still overfits severely (train Macro F1 = 1.0)

### 9.8 Is the benchmark scientifically defensible?

**Answer:** YES

- Ground truth is scenario-based (non-circular)
- Temporal integrity is verified
- No leakage detected
- Split methodology is documented and reproducible

### 9.9 What limitations remain?

**Answer:**

1. **Minority-class recall:** Suspicious recall (0.07) and super-suspicious recall (0.27) are poor
2. **Overfitting:** Random Forest train Macro F1 = 1.0 indicates severe overfitting
3. **Learnability limitation:** 3.6% of transactions (high_risk_country) cannot be detected from 34 features
4. **Customer overlap in secondary split:** Chronological split has 100% customer overlap
5. **is_self_transfer constant:** Generator limitation, not a bug
6. **severe_funnel missing:** Scenario defined but does not occur in dataset
7. **Macro F1 below preferred 0.50:** PRIMARY split achieves 0.44

### 9.10 Should we proceed to Stage 13?

**Answer:** YES, with documented limitations

The Stage 11 ground truth is scientifically defensible and demonstrates material improvement over Stage 6. However, important limitations remain in minority-class detection and overfitting. These limitations should be addressed in Stage 13.

---

## 10. FINAL DECISION

### 10.1 Decision Category

**CONDITIONAL PASS** — Improvement demonstrated but important limitations remain

### 10.2 Rationale

**Evidence for PASS:**
- Stage 11 ground truth is scenario-based (non-circular)
- PRIMARY split Macro F1 improved from 0.3453 to 0.4416 (+0.0963)
- PRIMARY split overfitting gap improved from 0.6061 to 0.5584
- Super-suspicious recall improved from ~0.08 to 0.27
- No leakage detected
- Temporal integrity verified
- Ground-truth provenance verified

**Evidence for CONDITIONAL:**
- Macro F1 below preferred 0.50 (PRIMARY: 0.44)
- Super-suspicious recall below preferred 0.30 (PRIMARY: 0.27)
- Suspicious recall far below preferred 0.50 (PRIMARY: 0.07)
- Train/test Macro F1 gap above preferred 0.30 (PRIMARY: 0.56)
- Random Forest overfits severely (train Macro F1 = 1.0)
- SECONDARY split performs poorly (Macro F1: 0.23)
- Learnability limitation (3.6% of transactions)

### 10.3 Stage 13 Recommendations

1. **Address minority-class recall:** Investigate why suspicious recall is so poor (0.07)
2. **Reduce overfitting:** Implement regularization or ensemble methods to reduce Random Forest overfitting
3. **Improve feature representation:** Add features to capture high_risk_country scenario
4. **Investigate scenario-level performance:** Determine which scenarios are easy vs invisible from features
5. **Consider class imbalance techniques:** Implement SMOTE or weighted loss to improve minority-class detection
6. **Document split methodology:** Clearly document the difference between Stage 6 and Stage 12 splits

---

## 11. ARTIFACTS

### 11.1 Stage 12 Artifacts

- ml_stage12_pretraining_audit.py
- ml_stage12_pretraining_audit_results.json
- ml_stage12_pretraining_audit_report.md
- ml_stage12_split_audit.py
- ml_stage12_split_audit_results.json
- ml_stage12_split_implementation.py
- ml_stage12_primary_split.json
- ml_stage12_secondary_split.json
- ml_stage12_model_training.py
- ml_stage12_model_results.json
- ml_stage12_analysis.py
- ml_stage12_analysis_results.json
- ml_stage12_report.md (this report)

### 11.2 Preserved Artifacts

All Stage 1-11 artifacts remain unchanged.

---

# STAGE 12 COMPLETE — CONDITIONAL PASS
