# STAGE 1: AML AI MODEL AUDIT REPORT

**Date:** 2026-09-01  
**Purpose:** Comprehensive audit of existing AML AI model, features, training methodology, and identification of weaknesses/leakage

---

## EXECUTIVE SUMMARY

The existing AML AI model has a **critical label leakage issue**: it is trained on labels derived from the rule engine's risk_level/risk_score, meaning the supervised model is learning to reproduce the existing rule engine rather than independently learning AML behavioral patterns. This defeats the purpose of having an independent ML signal.

---

## 1. MODEL ARCHITECTURE

### 1.1 Classifier
- **Type:** RandomForestClassifier within a scikit-learn Pipeline
- **Preprocessing:** StandardScaler
- **Configuration:**
  - n_estimators: 200
  - max_depth: 12
  - min_samples_leaf: 3
  - min_samples_split: 2
  - max_features: sqrt
  - class_weight: balanced_subsample
  - random_state: 42
- **Classes:** normal, suspicious, super_suspicious (3 classes)
- **Features:** 25 features

### 1.2 Anomaly Detector
- **Type:** IsolationForest
- **Configuration:**
  - n_estimators: 150
  - contamination: 0.08
  - max_samples: auto
  - random_state: 42
- **Features:** 25 features (same as classifier)

### 1.3 Model Metadata
- **Version:** 2.0.0
- **Training Date:** 2026-09-01T11:21:52+00:00
- **Training Samples:** 7,016
- **Label Distribution:**
  - normal: 4,808 (68.5%)
  - suspicious: 1,458 (20.8%)
  - super_suspicious: 750 (10.7%)
- **Cross-validation F1 (weighted):** 0.9645
- **Algorithm:** RandomForest + IsolationForest ensemble

### 1.4 Dependencies
- scikit-learn >= 1.5
- numpy >= 2.0
- pandas >= 2.2
- joblib >= 1.4

---

## 2. FEATURE AUDIT

### 2.1 Feature List (25 features)

| # | Feature Name | Type | Source | Available at Prediction Time | Potential Leakage |
|---|--------------|------|--------|-----------------------------|-------------------|
| 1 | amount | float | Transaction | Yes | No |
| 2 | hour | int | Transaction timestamp | Yes | No |
| 3 | is_deposit | binary | Transaction type | Yes | No |
| 4 | is_withdraw | binary | Transaction type | Yes | No |
| 5 | is_transfer | binary | Transaction type | Yes | No |
| 6 | is_self_transfer | binary | Transaction comparison | Yes | No |
| 7 | is_off_hours | binary | Transaction timestamp | Yes | No |
| 8 | sender_avg_amount | float | Historical aggregation | Yes | No |
| 9 | sender_max_amount | float | Historical aggregation | Yes | No |
| 10 | sender_tx_count | float | Historical aggregation | Yes | No |
| 11 | amount_to_sender_avg | float | Computed from history | Yes | No |
| 12 | amount_to_sender_max | float | Computed from history | Yes | No |
| 13 | sender_tx_count_24h | float | Historical aggregation (24h window) | Yes | No |
| 14 | sender_volume_24h | float | Historical aggregation (24h window) | Yes | No |
| 15 | amount_to_sender_volume_24h | float | Computed from history | Yes | No |
| 16 | is_new_recipient | float | Historical comparison | Yes | No |
| 17 | channel_encoded | int | Channel mapping | Yes | No |
| 18 | is_large_amount | binary | Rule-like threshold (>=10000) | Yes | **Potential** - encodes rule logic |
| 19 | is_structuring_band | binary | Rule-like threshold (8500-9999) | Yes | **Potential** - encodes rule logic |
| 20 | same_day_count | float | Sequence aggregation | Yes | No |
| 21 | same_day_total | float | Sequence aggregation | Yes | No |
| 22 | same_recipient_count | float | Sequence aggregation | Yes | No |
| 23 | rapid_transfer_count | float | Sequence aggregation | Yes | No |
| 24 | structuring_indicators | float | Computed from amount + count | Yes | **Potential** - encodes rule logic |
| 25 | layering_indicators | float | Computed from sequence | Yes | **Potential** - encodes rule logic |

### 2.2 Feature Analysis

**Strengths:**
- Good mix of transaction-level and behavioral features
- Historical context features (avg, max, count) provide customer baseline
- Sequence-based features (same_day_count, rapid_transfer_count) capture temporal patterns
- All features are available at prediction time

**Weaknesses:**
- Features 18, 19, 24, 25 encode rule-like logic (thresholds that mirror AML rules)
- No geographic features (destination_country not in features)
- No day-of-week feature
- No recipient diversity metric
- No incoming/outgoing ratio
- No percentile-based amount features
- Missing wealth segment information
- No PEP flag in features

**Potential Leakage:**
- Features 18, 19, 24, 25 are essentially hard-coded rule implementations
- If these features strongly correlate with the rule engine's output, the model may learn the rules rather than independent patterns

---

## 3. LABEL MAPPING ANALYSIS (CRITICAL ISSUE)

### 3.1 Current Label Generation Process

The `map_risk_to_ai_label()` function converts rule-engine outputs to AI training labels:

```python
def map_risk_to_ai_label(risk_level: str, risk_score: float = 0) -> str:
    level = (risk_level or "normal").lower()
    if level in ("normal", "low") and risk_score < 25:
        return "normal"
    if level in ("high_risk", "critical", "super_suspicious") or risk_score >= 60:
        return "super_suspicious"
    if level in ("suspicious", "medium") or risk_score >= 25:
        return "suspicious"
    return "normal"
```

### 3.2 Label Mapping Table

| risk_level | risk_score | AI Label |
|------------|------------|----------|
| normal | < 25 | normal |
| normal | >= 25 | suspicious |
| low | any | normal |
| suspicious | < 60 | suspicious |
| suspicious | >= 60 | super_suspicious |
| medium | any | suspicious |
| high_risk | any | super_suspicious |
| critical | any | super_suspicious |
| super_suspicious | any | super_suspicious |

### 3.3 CRITICAL PROBLEM

**The AI is trained on labels derived from the rule engine.**

This means:
1. The supervised model is learning to reproduce the rule engine's decisions
2. The AI does NOT provide an independent ML signal
3. If the rule engine has biases or blind spots, the AI will inherit them
4. The ensemble (rules + AI) may be redundant rather than complementary
5. The model cannot detect patterns the rule engine misses

**This is the fundamental issue that must be corrected.**

---

## 4. TRAINING METHODOLOGY AUDIT

### 4.1 Data Source
- **Source:** Synthetic transaction generator (`transaction_simulation.py`)
- **Training samples:** 7,016
- **No real transaction data used**

### 4.2 Label Assignment Process

```
Transaction
→ Rule engine evaluates (aml_rules.py)
→ risk_level and risk_score assigned
→ map_risk_to_ai_label() converts to AI label
→ RandomForest learns these labels
```

**Problem:** The ground truth is the rule engine, not actual AML behavior.

### 4.3 Cross-Validation
- **Method:** cross_val_score with cv=min(5, len(y_train) // 5)
- **Scoring:** f1_weighted
- **Result:** 0.9645
- **Issue:** No mention of stratification, customer-level splitting, or temporal splitting

### 4.4 Train/Validation/Test Split
- **Status:** NOT IMPLEMENTED
- **Problem:** The training function `train_ai_model()` does not split data
- **Consequence:** No held-out test set, no validation set, no way to measure generalization

### 4.5 Bootstrap Data
- **Purpose:** Used when < 30 samples or < 2 classes
- **Content:** 16 hardcoded representative transactions
- **Issue:** Bootstrap data has hardcoded risk_level values, which may not represent real distribution

---

## 5. SYNTHETIC DATA GENERATOR AUDIT

### 5.1 Class Distribution
- **Fixed distribution:** 70% normal, 20% suspicious, 10% super_suspicious
- **Issue:** Artificial distribution may not reflect real-world AML prevalence

### 5.2 Scenario Count
- **Normal scenarios:** 5
- **Suspicious scenarios:** 12
- **Super suspicious scenarios:** 15

### 5.3 Scenario Design Issues

**Normal Scenarios:**
- All amounts are relatively small (max $4,200)
- No legitimate high-value transactions (e.g., business payments, large purchases)
- No legitimate international transactions
- All during business hours
- **Problem:** Model may learn that "large = suspicious" artificially

**Suspicious Scenarios:**
- Many involve specific amount ranges (e.g., 9200-9900 for structuring)
- Explicitly labeled by scenario type
- **Problem:** Model may learn amount thresholds rather than behavioral patterns

**Super Suspicious Scenarios:**
- All involve high amounts (min $2,500, max $150,000)
- All involve explicit typologies (shell companies, PEP, terror financing)
- **Problem:** No overlap with normal behavior - makes classification artificially easy

### 5.4 Label Assignment in Generator
- **Method:** Generator selects scenario based on desired label
- **Problem:** Label → scenario, not behavior → label
- **Consequence:** Model learns scenario characteristics, not AML typologies

### 5.5 Missing Realistic Overlap
- No legitimate high-value transactions
- No suspicious-looking but legitimate transactions
- No normal-looking but suspicious transactions
- No edge cases or borderline cases
- No customer-level behavior patterns

---

## 6. DATA LEAKAGE ANALYSIS

### 6.1 Label Leakage (CRITICAL)
- **Source:** Labels derived from rule engine output
- **Severity:** HIGH
- **Impact:** AI reproduces rule engine instead of learning independently

### 6.2 Feature Leakage (MODERATE)
- **Features 18, 19, 24, 25** encode rule-like thresholds
- **Severity:** MODERATE
- **Impact:** Model may learn rule thresholds rather than behavioral patterns

### 6.3 Temporal Leakage (UNKNOWN)
- **Status:** No temporal splitting implemented
- **Severity:** UNKNOWN
- **Impact:** Cannot assess if model generalizes to future periods

### 6.4 Customer-Level Leakage (UNKNOWN)
- **Status:** No customer-level splitting implemented
- **Severity:** UNKNOWN
- **Impact:** Same customer's patterns may appear in both training and inference

### 6.5 Future Information Leakage (NONE DETECTED)
- No features use future transaction information
- No post-alert information used

---

## 7. STRENGTHS

1. **Well-structured codebase** - Clean separation of concerns (ai_core.py, aml_rules.py, behavioral_profiling.py)
2. **Comprehensive behavioral profiling** - Sophisticated customer baseline tracking
3. **Ensemble approach** - Combines supervised ML and anomaly detection
4. **Feature engineering** - Good mix of transaction-level and behavioral features
5. **No circular flagging constraint** - Behavioral profiling explicitly avoids using past alerts
6. **Cold-start handling** - Grace period for new customers
7. **Real-time capable** - Designed for live transaction processing
8. **Metadata tracking** - Model version and training metadata saved

---

## 8. WEAKNESSES

1. **CRITICAL: Label leakage** - AI trained on rule engine output, not independent AML behavior
2. **No train/validation/test split** - Cannot measure generalization
3. **Artificial synthetic data** - Scenarios are too obvious, no realistic overlap
4. **Fixed class distribution** - 70/20/10 may not reflect reality
5. **Rule-like features** - Some features encode rule logic (thresholds)
6. **Missing geographic features** - destination_country not in ML features
7. **No customer-level splitting** - May leak customer patterns
8. **No temporal splitting** - May not generalize to future periods
9. **High reported F1 (0.96)** - Suspiciously high, may indicate overfitting or easy task
10. **Bootstrap data** - Hardcoded samples may bias model

---

## 9. COMPATIBILITY ISSUES

- **scikit-learn version:** >= 1.5 (recent version)
- **numpy version:** >= 2.0 (recent version)
- **joblib version:** >= 1.4
- **Potential issue:** Model serialized with recent versions; may have compatibility issues if downgraded

---

## 10. RECOMMENDATIONS

### 10.1 CRITICAL (Must Fix)

1. **Eliminate label leakage**
   - Create independent ground-truth labeling based on AML typologies
   - Do NOT use rule engine output as training labels
   - Generate labels from underlying behavior, not from risk_level

2. **Implement proper train/validation/test split**
   - Use customer-level splitting where appropriate
   - Use temporal splitting for time-series validation
   - Keep test set completely untouched during model selection

3. **Redesign synthetic data generator**
   - Create realistic overlap between classes
   - Add legitimate high-value transactions
   - Add suspicious-looking but legitimate transactions
   - Generate from behavior → label, not label → scenario
   - Increase scenario diversity

### 10.2 HIGH PRIORITY

4. **Remove or redesign rule-like features**
   - Remove features 18, 19, 24, 25 or redesign them to be behavioral rather than threshold-based
   - Add geographic features (destination_country encoding)
   - Add day-of-week feature
   - Add recipient diversity metric

5. **Implement proper cross-validation**
   - Use StratifiedKFold for class imbalance
   - Consider GroupKFold for customer-level splitting
   - Document CV methodology

6. **Add realistic edge cases**
   - Borderline transactions
   - Mixed-behavior customers
   - Evolution of customer behavior over time

### 10.3 MEDIUM PRIORITY

7. **Evaluate Isolation Forest contribution**
   - Test if anomaly detection actually adds value
   - Compare RF alone vs RF + IF
   - May not need ensemble

8. **Add more behavioral features**
   - Percentile-based amount features
   - Incoming/outgoing ratio
   - Wealth segment information
   - PEP flag (if available at prediction time)

9. **Improve metadata**
   - Add random seed used
   - Add Python version
   - Add sklearn version
   - Add feature documentation

---

## 11. NEXT STEPS (STAGE 2)

Before proceeding to retraining, establish a baseline by:

1. Evaluating the existing model on a held-out test set (if data allows)
2. Measuring per-class precision/recall/F1
3. Generating confusion matrix
4. Calculating false-positive and false-negative rates
5. Testing against manually designed realistic scenarios
6. Documenting baseline performance

This baseline will allow comparison with improved models.

---

**STAGE 1 COMPLETE — WAITING FOR APPROVAL.**
