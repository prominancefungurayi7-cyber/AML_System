# SMOTE Experiment Stage 18 Report

**Date:** 2026-09-03  
**Stage:** 18 - SMOTE Experiment  
**Status:** COMPLETE

---

## 1. OBJECTIVE

Test whether SMOTE (Synthetic Minority Over-sampling Technique) can improve minority-class detection using the same 18 features and same training/test methodology as the frozen champion. The key question is whether synthetic minority oversampling can improve suspicious and super_suspicious detection without causing unacceptable degradation in normal-class performance.

**Constraints:**
- No dataset changes
- No feature changes
- No label changes
- No customer holdout changes
- No chronological split changes
- Test set untouched during model selection
- SMOTE applied ONLY to training data
- No threshold optimization
- No production model modifications

---

## 2. FROZEN CONDITIONS

All frozen conditions were preserved:

- **Dataset:** `ml_stage16b_features.csv` (10,000 transactions)
- **Labels:** `ml_stage11_ground_truth.json`
- **Features:** 18 frozen Stage 16B features
- **Customer holdout:** 160 train / 40 test
- **Customer overlap:** 0
- **Chronological split:** Preserved
- **Train samples:** 8,000
- **Test samples:** 2,000
- **Random seed:** 42

---

## 3. SMOTE METHODOLOGY

**SMOTE Application Order:**

1. Load frozen dataset
2. Reproduce exact customer holdout (160 train / 40 test)
3. Reproduce exact chronological train/test split
4. Separate 8,000 training samples from untouched 2,000 test samples
5. Apply SMOTE ONLY to training data
6. Train Gradient Boosting on resampled training data
7. Evaluate on untouched test set
8. Never apply SMOTE to validation or test data

**SMOTE Implementation:**
- Library: `imbalanced-learn` (SMOTE)
- k_neighbors: 5 (default)
- random_state: 42
- Applied only to training data
- Test set never used during SMOTE/model selection

---

## 4. PRE-SMOTE CLASS DISTRIBUTION

**Training data (8,000 samples):**

| Class | Count | Percentage |
|-------|-------|------------|
| normal | 5,964 | 74.55% |
| suspicious | 1,761 | 22.01% |
| super_suspicious | 275 | 3.44% |

**Analysis:** Severe class imbalance, with super_suspicious at only 3.44% of training data.

---

## 5. POST-SMOTE CLASS DISTRIBUTION

### No_SMOTE_Baseline

| Class | Count | Percentage |
|-------|-------|------------|
| normal | 5,964 | 74.55% |
| suspicious | 1,761 | 22.01% |
| super_suspicious | 275 | 3.44% |
| **Total** | **8,000** | **100%** |

### Balanced_SMOTE

| Class | Count | Percentage |
|-------|-------|------------|
| normal | 5,964 | 33.33% |
| suspicious | 5,964 | 33.33% |
| super_suspicious | 5,964 | 33.33% |
| **Total** | **17,892** | **100%** |

### Mild_SMOTE

| Class | Count | Percentage |
|-------|-------|------------|
| normal | 5,964 | 50.00% |
| suspicious | 2,982 | 25.00% |
| super_suspicious | 2,982 | 25.00% |
| **Total** | **11,928** | **100%** |

### Conservative_SMOTE

| Class | Count | Percentage |
|-------|-------|------------|
| normal | 5,964 | 62.50% |
| suspicious | 1,789 | 18.75% |
| super_suspicious | 1,789 | 18.75% |
| **Total** | **9,542** | **100%** |

---

## 6. CONFIGURATIONS TESTED

| Configuration | Sampling Strategy | k_neighbors |
|---------------|-------------------|-------------|
| No_SMOTE_Baseline | None (no SMOTE) | N/A |
| Balanced_SMOTE | auto (resample all to majority) | 5 |
| Mild_SMOTE | normal: 1.0, suspicious: 0.5, super_suspicious: 0.5 | 5 |
| Conservative_SMOTE | normal: 1.0, suspicious: 0.3, super_suspicious: 0.3 | 5 |

---

## 7. TRAINING/CV RESULTS

**Cross-validation on training data only (5-fold stratified):**

| Configuration | CV Mean Macro F1 | CV Std Macro F1 |
|---------------|------------------|-----------------|
| No_SMOTE_Baseline | 0.5590 | 0.0368 |
| Balanced_SMOTE | 0.8204 | 0.0069 |
| Mild_SMOTE | 0.7303 | 0.0118 |
| Conservative_SMOTE | 0.6579 | 0.0077 |

**Best CV configuration:** Balanced_SMOTE

**Analysis:** Balanced_SMOTE shows dramatically higher CV Macro F1 (0.8204) compared to baseline (0.5590), suggesting strong potential for improvement.

---

## 8. SELECTED CONFIGURATION

**Selected:** Balanced_SMOTE

**Configuration:**
- sampling_strategy: auto (resample all classes to majority)
- k_neighbors: 5
- random_state: 42

**Training samples after SMOTE:** 17,892 (increased from 8,000)

**Gradient Boosting configuration:**
- learning_rate: 0.01
- max_depth: 3
- n_estimators: 500
- random_state: 42

---

## 9. FINAL TEST RESULTS

**Balanced_SMOTE Test Performance:**

- Accuracy: 74.00%
- Macro F1: 48.37%
- Weighted F1: 69.89%
- Suspicious Recall: 13.41%
- Super-Suspicious Recall: 69.84%
- Suspicious False Negatives: 394
- Super-Suspicious False Negatives: 19

---

## 10. CONFUSION MATRIX

**Balanced_SMOTE Confusion Matrix (Test):**

```
Predicted →
Actual ↓
['normal' 'super_suspicious' 'suspicious']
  normal: [1375   45   62]
  super_suspicious: [19 44  0]
  suspicious: [313  81  61]
```

**Verification:**
- Total: 1375 + 45 + 62 + 19 + 44 + 0 + 313 + 81 + 61 = 2,000 ✅
- Suspicious recall = 61 / (313 + 81 + 61) = 61 / 455 = 13.41% ✅
- Super-suspicious recall = 44 / (19 + 44 + 0) = 44 / 63 = 69.84% ✅

---

## 11. PER-CLASS METRICS

**Balanced_SMOTE Per-Class Metrics (Test):**

| Class | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| Normal | 80.58% | 92.78% | 86.24% |
| Super-Suspicious | 26.07% | 69.84% | 37.93% |
| Suspicious | 49.60% | 13.41% | 21.13% |

---

## 12. COMPARISON WITH FROZEN CHAMPION

| Metric | Champion | Balanced_SMOTE | Difference |
|--------|----------|----------------|-------------|
| Accuracy | 77.75% | 74.00% | -3.75% |
| Macro F1 | 50.15% | 48.37% | -1.78% |
| Weighted F1 | 73.44% | 69.89% | -3.55% |
| Suspicious Recall | 21.76% | 13.41% | -8.35% |
| Super-Suspicious Recall | 25.40% | 69.84% | +44.44% |
| Suspicious FN | 356 | 394 | +38 |
| Super-Suspicious FN | 47 | 19 | -28 |

**Analysis:**
- **Major degradation in overall metrics:** Accuracy (-3.75%), Macro F1 (-1.78%), Weighted F1 (-3.55%)
- **Dramatic improvement in super-suspicious recall:** +44.44 percentage points (from 25.40% to 69.84%)
- **Significant degradation in suspicious recall:** -8.35 percentage points (from 21.76% to 13.41%)
- **Mixed false negatives:** Super-suspicious FN improved (-28), but suspicious FN worsened (+38)

---

## 13. MINORITY-CLASS ANALYSIS

**Super-Suspicious Class:**
- **Recall improved dramatically:** 25.40% → 69.84% (+44.44%)
- **False negatives reduced:** 47 → 19 (-28)
- **Precision improved:** 24.39% → 26.07% (+1.68%)
- **F1 improved:** 24.72% → 37.93% (+13.21%)
- **Conclusion:** SMOTE dramatically improved super-suspicious detection

**Suspicious Class:**
- **Recall degraded significantly:** 21.76% → 13.41% (-8.35%)
- **False negatives increased:** 356 → 394 (+38)
- **Precision improved:** 23.00% → 49.60% (+26.60%)
- **F1 degraded:** 22.22% → 21.13% (-1.09%)
- **Conclusion:** SMOTE hurt suspicious detection despite precision improvement

**Normal Class:**
- **Recall degraded slightly:** 96.70% → 92.78% (-3.92%)
- **Precision improved slightly:** 79.86% → 80.58% (+0.72%)
- **F1 degraded slightly:** 87.69% → 86.24% (-1.45%)
- **Conclusion:** Minor degradation in normal-class performance

**Overall Minority-Class Analysis:**
- SMOTE achieved its goal for super-suspicious class (massive recall improvement)
- But failed for suspicious class (recall degradation)
- The trade-off is unacceptable: suspicious class is more common (22.01% vs 3.44%) and its degradation outweighs super-suspicious improvement

---

## 14. OVERFITTING/GENERALIZATION ANALYSIS

**CV vs Test Performance:**

| Configuration | CV Macro F1 | Test Macro F1 | CV-Test Gap |
|---------------|-------------|---------------|-------------|
| No_SMOTE_Baseline | 0.5590 | 0.5015 | -0.0575 |
| Balanced_SMOTE | 0.8204 | 0.4837 | -0.3367 |

**Analysis:**
- **Massive CV-test gap for Balanced_SMOTE:** -0.3367 (compared to -0.0575 for baseline)
- **Severe overfitting:** The model performs extremely well on CV (0.8204) but poorly on test (0.4837)
- **SMOTE synthetic samples don't generalize:** The synthetic minority samples created during training do not represent the true distribution of the test set
- **Champion generalizes better:** The baseline without SMOTE has a much smaller CV-test gap

**Conclusion:** SMOTE introduces severe overfitting. The synthetic samples created during training do not reflect the true distribution of minority classes in the test set, leading to poor generalization.

---

## 15. INTEGRITY VERIFICATION

**All 13 integrity checks passed:**

✅ Feature list matches (18 features)  
✅ Dataset row count matches (10,000)  
✅ Train row count matches (8,000)  
✅ Test row count matches (2,000)  
✅ Customer holdout 160/40  
✅ Zero customer overlap  
✅ Confusion matrix total matches test samples  
✅ Row totals match class counts  
✅ Recall from CM matches report  
✅ Accuracy from CM matches report  
✅ Metrics match reported results  
✅ random_state=42 used  
✅ Test data not used for selection  

**Verification:** The experiment was conducted correctly with no data leakage or integrity violations. SMOTE was applied only to training data, and the test set remained completely untouched.

---

## 16. PROMOTION DECISION

**DECISION: KEEP CHAMPION**

**Rationale:**

1. **No meaningful improvement:** Macro F1 decreased by 1.78 percentage points, not improved
2. **Severe overfitting:** CV-test gap of -0.3367 indicates poor generalization
3. **Mixed minority-class results:** Super-suspicious recall improved dramatically (+44.44%), but suspicious recall degraded significantly (-8.35%)
4. **Overall degradation:** Accuracy (-3.75%), Weighted F1 (-3.55%), Macro F1 (-1.78%)
5. **Unacceptable trade-off:** The degradation in suspicious class (more common at 22.01% vs 3.44%) outweighs the improvement in super-suspicious class
6. **Champion generalizes better:** The baseline without SMOTE has much better generalization

**Promotion Rule Check:**
- Macro F1 improvement ≥ 2 percentage points? **NO** (decreased by 1.78%)
- Minority-class recall improvement? **MIXED** (super-suspicious improved, suspicious degraded)
- No unacceptable degradation? **NO** (suspicious recall degraded significantly)

**Conclusion:** The champion should remain unchanged. Balanced_SMOTE shows severe overfitting and unacceptable trade-offs between minority classes.

---

## 17. RECOMMENDED NEXT EXPERIMENT

**Current Status:**
- Hyperparameter tuning (Stage 17) did not yield improvement
- SMOTE (Stage 18) showed severe overfitting and unacceptable trade-offs
- The frozen champion remains the best model

**Recommended Next Experiment: SMOTE + XGBoost**

**Rationale:**
- XGBoost is explicitly identified in Chapter 1 as an important ML library candidate
- XGBoost was tested without SMOTE in a previous experiment and did not beat the champion
- However, XGBoost may perform better when combined with SMOTE because:
  - XGBoost has built-in handling of imbalanced data (scale_pos_weight parameter)
  - XGBoost's gradient boosting approach may generalize better from SMOTE samples
  - XGBoost's regularization parameters may mitigate the overfitting seen with Gradient Boosting + SMOTE
- Testing SMOTE + XGStack will determine whether the SMOTE approach can be salvaged with a different model architecture

**Alternative Options:**
- Ensemble methods (combine multiple models)
- Threshold optimization (adjust decision thresholds per class)
- Feature interactions (create interaction features)

**Recommendation:** Proceed with SMOTE + XGBoost as the next model improvement stage.

---

## 18. SUMMARY

**BEST SMOTE CONFIGURATION:** Balanced_SMOTE  
**FROZEN CHAMPION:** Gradient Boosting (learning_rate=0.01, max_depth=3, n_estimators=500, random_state=42)  
**BEST TEST MACRO F1:** 48.37% (Balanced_SMOTE) vs 50.15% (Champion)  
**SUSPICIOUS RECALL:** 13.41% (Balanced_SMOTE) vs 21.76% (Champion)  
**SUPER-SUSPICIOUS RECALL:** 69.84% (Balanced_SMOTE) vs 25.40% (Champion)  
**ACCURACY:** 74.00% (Balanced_SMOTE) vs 77.75% (Champion)  
**CHAMPION BEATEN:** NO  
**SHOULD MODEL BE PROMOTED:** NO  
**SHOULD XGBOOST BE TESTED NEXT:** YES (SMOTE + XGBoost)

---

**STAGE 18 COMPLETE — WAITING FOR APPROVAL**
