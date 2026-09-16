# STAGE 2: BASELINE MODEL EVALUATION REPORT

**Date:** 2026-09-01  
**Purpose:** Establish trustworthy baseline for existing AML AI model before any improvements

---

## EXECUTIVE SUMMARY

The existing AML AI model performs **significantly worse than the reported CV F1 of 0.9645** suggests. When evaluated on a properly generated dataset using the existing methodology, the model achieves only **32% accuracy** with **suspicious recall of 28%** and **super-suspicious recall of 16%**. This indicates the model is failing to detect the majority of suspicious transactions.

The reported CV F1 of 0.9645 appears to be measured on the original training data (7,016 samples with 70/20/10 distribution) and does not represent the model's actual performance on realistic transaction data.

---

## 1. DATASET STATISTICS

### 1.1 Dataset Generation
- **Method:** Used existing `transaction_simulation.py` without modifications
- **Size:** 10,000 transactions (larger than original 7,016 for proper evaluation)
- **Random seed:** 42 (for reproducibility)
- **Users:** 100 mock accounts with varying wealth segments

### 1.2 Label Distribution (After map_risk_to_ai_label())

| Class | Count | Percentage |
|-------|-------|------------|
| normal | 1,295 | 13.0% |
| suspicious | 4,329 | 43.3% |
| super_suspicious | 4,376 | 43.8% |

**CRITICAL ISSUE:** The label distribution is dramatically different from the intended 70/20/10 split. This is caused by the `map_risk_to_ai_label()` function converting risk_level/risk_score in a way that shifts the distribution. The synthetic generator creates transactions with risk_level matching the intended label, but the mapping function then re-assigns labels based on risk_score thresholds, causing the distribution shift.

### 1.3 Transaction Statistics
- **Unique accounts:** 100
- **Transaction types:**
  - transfer: 5,209 (52.1%)
  - withdraw: 3,045 (30.4%)
  - deposit: 1,746 (17.5%)
- **Channels:**
  - online: 2,460 (24.6%)
  - mobile: 1,884 (18.8%)
  - atm: 1,627 (16.3%)
  - card: 1,424 (14.2%)
  - ach: 1,390 (13.9%)
  - swift: 865 (8.6%)
  - branch: 350 (3.5%)
- **Amount statistics:**
  - Min: $15.64
  - Max: $72,950.00
  - Mean: $4,103.52
  - Median: $1,029.78

---

## 2. EVALUATION A: EXISTING REPORTED-STYLE METHODOLOGY

### 2.1 Methodology
- **No train/test split** (evaluates on same data used for training)
- **Labels derived from rule engine** via `map_risk_to_ai_label()`
- **Reproduces the existing training methodology**

### 2.2 Classification Metrics

| Metric | Value |
|--------|-------|
| Accuracy | 0.3225 (32.25%) |
| Precision (weighted) | 0.6613 |
| Recall (weighted) | 0.3225 |
| F1-score (weighted) | 0.3241 |
| F1-score (macro) | 0.3210 |

### 2.3 Per-Class Metrics

| Class | Precision | Recall | F1-score | Support |
|-------|-----------|--------|----------|---------|
| normal | 0.1838 | 0.9923 | 0.3101 | 1,295 |
| suspicious | 0.5460 | 0.2781 | 0.3685 | 4,329 |
| super_suspicious | 0.9166 | 0.1682 | 0.2842 | 4,376 |

### 2.4 Confusion Matrix

| Actual \ Predicted | Normal | Suspicious | Super Suspicious |
|-------------------|--------|------------|------------------|
| **normal** | 1,285 | 10 | 0 |
| **suspicious** | 3,058 | 1,204 | 67 |
| **super_suspicious** | 2,649 | 991 | 736 |

### 2.5 Error Analysis

**False Positives (by class):**
- normal: 5,707 (model incorrectly predicts suspicious/super_suspicious for normal transactions)
- suspicious: 1,001
- super_suspicious: 67

**False Negatives (by class):**
- normal: 10 (good - rarely misses normal)
- suspicious: 3,125 (72% of suspicious transactions missed)
- super_suspicious: 3,640 (83% of super-suspicious transactions missed)

### 2.6 AML-Specific Metrics

| Metric | Value |
|--------|-------|
| Suspicious Recall | 0.2781 (27.81%) |
| Super-Suspicious Recall | 0.1682 (16.82%) |

**Interpretation:** The model is failing to detect the majority of suspicious and super-suspicious transactions. This is catastrophic for an AML system.

---

## 3. EVALUATION B: MORE HONEST DIAGNOSTIC METHODOLOGY

### 3.1 Methodology
- **70% train / 30% test split** (random split)
- **No customer-level splitting** (limitation due to current data structure)
- **Labels still derived from rule engine** (limitation acknowledged)
- **Model NOT retrained** - evaluates existing model on held-out test set

### 3.2 Dataset Split

| Set | Size | Normal | Suspicious | Super Suspicious |
|-----|------|--------|------------|------------------|
| Train | 7,000 | 901 (12.9%) | 3,027 (43.2%) | 3,072 (43.9%) |
| Test | 3,000 | 394 (13.1%) | 1,302 (43.4%) | 1,304 (43.5%) |

### 3.3 Test Set Classification Metrics

| Metric | Value |
|--------|-------|
| Accuracy | 0.3197 (31.97%) |
| Precision (weighted) | 0.6617 |
| Recall (weighted) | 0.3197 |
| F1-score (weighted) | 0.3193 |
| F1-score (macro) | 0.3171 |

### 3.4 Test Set Per-Class Metrics

| Class | Precision | Recall | F1-score | Support |
|-------|-----------|--------|----------|---------|
| normal | 0.1838 | 0.9898 | 0.3100 | 394 |
| suspicious | 0.5554 | 0.2773 | 0.3699 | 1,302 |
| super_suspicious | 0.9123 | 0.1595 | 0.2715 | 1,304 |

### 3.5 Test Set Confusion Matrix

| Actual \ Predicted | Normal | Suspicious | Super Suspicious |
|-------------------|--------|------------|------------------|
| **normal** | 390 | 4 | 0 |
| **suspicious** | 921 | 361 | 20 |
| **super_suspicious** | 811 | 285 | 208 |

### 3.6 Test Set Error Analysis

**False Positives (by class):**
- normal: 1,732
- suspicious: 289
- super_suspicious: 20

**False Negatives (by class):**
- normal: 4
- suspicious: 941 (72% missed)
- super_suspicious: 1,096 (84% missed)

### 3.7 Test Set AML-Specific Metrics

| Metric | Value |
|--------|-------|
| Suspicious Recall | 0.2773 (27.73%) |
| Super-Suspicious Recall | 0.1595 (15.95%) |

**Interpretation:** The honest evaluation shows nearly identical performance to the existing methodology, confirming that the model's poor performance is consistent and not an artifact of the evaluation method.

---

## 4. COMPARISON: EVALUATION A vs EVALUATION B

| Metric | Evaluation A (No Split) | Evaluation B (70/30 Split) | Difference |
|--------|------------------------|---------------------------|------------|
| Accuracy | 0.3225 | 0.3197 | -0.0028 |
| F1 (weighted) | 0.3241 | 0.3193 | -0.0048 |
| F1 (macro) | 0.3210 | 0.3171 | -0.0039 |
| Suspicious Recall | 0.2781 | 0.2773 | -0.0008 |
| Super-Suspicious Recall | 0.1682 | 0.1595 | -0.0087 |

**Conclusion:** The model's performance is nearly identical between the two evaluation methods, indicating that:
1. The model is not overfitting to the training data (performance doesn't degrade on test set)
2. The poor performance is inherent to the model/training methodology
3. The reported CV F1 of 0.9645 is not representative of actual model performance

---

## 5. FEATURE IMPORTANCE

### 5.1 Top Features (Random Forest)

| Rank | Feature | Importance |
|------|---------|------------|
| 1 | amount | 0.2220 |
| 2 | amount_to_sender_avg | 0.1938 |
| 3 | amount_to_sender_max | 0.1211 |
| 4 | channel_encoded | 0.1128 |
| 5 | amount_to_sender_volume_24h | 0.0856 |
| 6 | is_large_amount | 0.0465 |
| 7 | hour | 0.0292 |
| 8 | is_off_hours | 0.0268 |
| 9 | is_deposit | 0.0204 |
| 10 | is_transfer | 0.0183 |

### 5.2 Feature Importance Analysis

**Strengths:**
- Amount-related features are most important (expected for AML)
- Channel encoding is important (different channels have different risk profiles)
- Temporal features (hour, is_off_hours) have moderate importance

**Weaknesses:**
- Model relies heavily on amount ratios rather than complex behavioral patterns
- Sequence-based features (same_day_count, rapid_transfer_count) have very low importance
- Recipient-based features (is_new_recipient, same_recipient_count) have negligible importance
- Rule-like features (structuring_indicators, layering_indicators) have very low importance

**Interpretation:** The model is primarily learning simple amount thresholds rather than sophisticated AML typologies. This explains why it performs poorly - it's not capturing the complex behavioral patterns that characterize actual money laundering.

---

## 6. ANOMALY DETECTOR EVALUATION

### 6.1 Statistics

| Metric | Value |
|--------|-------|
| Mean anomaly score | -0.0444 |
| Std anomaly score | 0.0491 |
| Min anomaly score | -0.1869 |
| Max anomaly score | 0.0983 |
| Threshold (8th percentile) | -0.1159 |
| Predicted anomalies | 240 (8.0%) |

### 6.2 Limitations

**Cannot properly evaluate anomaly detector because:**
- No ground-truth anomaly labels exist
- Anomaly detector is trained on the same data as classifier
- Contamination parameter (0.08) is arbitrary
- No way to measure if anomaly predictions are meaningful

**Observation:** The anomaly detector flags 8% of transactions as anomalous (matching the contamination parameter), but without ground truth, we cannot determine if these are actual anomalies or false positives.

---

## 7. LABEL LEAKAGE IMPACT ANALYSIS

### 7.1 The Leakage Problem

The existing training pipeline:
```
Transaction
→ Rule engine assigns risk_level and risk_score
→ map_risk_to_ai_label() converts to AI training label
→ RandomForest learns these labels
```

This means the AI is trained on labels derived from the rule engine, not on independent AML behavior.

### 7.2 Impact on Baseline

The baseline evaluation reveals that even with this label leakage, the model performs poorly:
- **The model cannot even reproduce the rule engine's decisions effectively**
- **Suspicious recall of 28% means 72% of rule-flagged transactions are missed**
- **Super-suspicious recall of 16% means 84% of rule-flagged transactions are missed**

### 7.3 Why Performance is Poor

1. **Label distribution mismatch:** The mapping function shifts the intended 70/20/10 distribution to 13/43/44, confusing the model
2. **Feature-label misalignment:** The features don't strongly correlate with the mapped labels
3. **Over-reliance on amount:** Model learns simple amount thresholds rather than complex patterns
4. **Insufficient behavioral features:** Sequence-based and network-based features have low importance

### 7.4 Conclusion on Leakage

**The label leakage is NOT the primary cause of poor performance.** Even when trained on rule-engine labels, the model fails to learn those labels effectively. The primary issues are:
1. Poor feature engineering (too reliant on simple amount ratios)
2. Synthetic data quality (scenarios too obvious, no realistic overlap)
3. Model architecture (Random Forest may not be optimal for this problem)

---

## 8. LIMITATIONS

### 8.1 Evaluation Limitations

1. **Labels derived from rule engine:** Cannot measure true AML detection performance
2. **No customer-level splitting:** Same customer patterns may appear in train and test
3. **No temporal splitting:** Cannot assess generalization to future periods
4. **Synthetic data:** May not reflect real-world transaction patterns
5. **Artificial class distribution:** 13/43/44 distribution is unrealistic

### 8.2 Data Limitations

1. **No legitimate high-value transactions:** Normal scenarios all small amounts
2. **No suspicious-looking but legitimate transactions:** Makes classification artificially easy
3. **No normal-looking but suspicious transactions:** Model can't learn subtle patterns
4. **No edge cases:** Missing borderline transactions
5. **No customer-level behavior:** Transactions are independent, not customer-centric

### 8.3 Model Limitations

1. **Cannot evaluate anomaly detector:** No ground-truth anomaly labels
2. **Feature importance biased:** Amount features dominate, may miss subtle patterns
3. **No interpretability:** Cannot explain why specific transactions are flagged
4. **No calibration:** Probabilities may not reflect true likelihood

---

## 9. CONCLUSIONS

### 9.1 Baseline Performance

The existing AML AI model performs **significantly worse than reported**:
- **Accuracy: 32%** (not the implied high performance from CV F1 of 0.9645)
- **Suspicious recall: 28%** (missing 72% of suspicious transactions)
- **Super-suspicious recall: 16%** (missing 84% of super-suspicious transactions)
- **High false positives:** 5,707 false positives for normal transactions

### 9.2 Why Reported CV F1 is Misleading

The reported CV F1 of 0.9645 was likely measured on:
- The original 7,016 training samples
- With the intended 70/20/10 label distribution
- Without proper train/test splitting
- On data that the model had already seen

This does not represent the model's actual performance on realistic transaction data.

### 9.3 Primary Issues

1. **Label leakage:** AI trained on rule-engine labels (not independent AML behavior)
2. **Poor feature engineering:** Over-reliance on amount ratios, insufficient behavioral features
3. **Synthetic data quality:** Scenarios too obvious, no realistic overlap
4. **Model architecture:** RandomForest may not be optimal for this problem
5. **No proper evaluation:** No train/test split, no customer-level splitting

### 9.4 Recommendations for Improvement

1. **CRITICAL:** Create independent ground-truth labels based on AML typologies
2. **CRITICAL:** Redesign synthetic data generator with realistic overlap
3. **HIGH:** Improve feature engineering (add behavioral, network, temporal features)
4. **HIGH:** Implement proper train/validation/test splitting
5. **HIGH:** Evaluate alternative models (XGBoost, LightGBM, Gradient Boosting)
6. **MEDIUM:** Add customer-level splitting to prevent leakage
7. **MEDIUM:** Add temporal splitting to assess future generalization

### 9.5 Next Steps

Before proceeding to Stage 3 (Dataset and Labeling Redesign), the baseline shows that:
- The existing model is not performing well enough to be a meaningful baseline
- The entire training pipeline needs to be redesigned
- The synthetic data generator needs significant improvement
- Feature engineering needs to be enhanced

The baseline has successfully established that the current approach is not working and provides a clear starting point for improvement.

---

## 10. FILES GENERATED

- `ml_baseline_dataset.json` - Generated dataset (10,000 transactions)
- `ml_baseline_dataset_metadata.json` - Dataset metadata
- `ml_baseline_results.json` - Evaluation results (JSON format)
- `ml_baseline_stage2_report.md` - This report

---

**STAGE 2 COMPLETE — WAITING FOR APPROVAL.**
