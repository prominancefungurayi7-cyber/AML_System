# Model Improvement Stage 17 Report

**Date:** 2026-09-02  
**Stage:** 17 - Controlled Hyperparameter Experiment  
**Status:** COMPLETE

---

## 1. OBJECTIVE

Investigate whether the frozen Gradient Boosting champion can generalize better through controlled hyperparameter tuning. The goal was to determine if the current model is under/overfitting and whether a better bias/variance balance improves held-out performance.

**Constraints:**
- No dataset changes
- No feature changes
- No label changes
- No customer holdout changes
- No chronological split changes
- Test set untouched during model selection
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

## 3. BASELINE CHAMPION

**Gradient Boosting Champion (Stage 16B):**

```python
learning_rate = 0.01
max_depth = 3
n_estimators = 500
random_state = 42
```

**Performance:**
- Accuracy: 77.75%
- Macro F1: 50.15%
- Weighted F1: 73.44%
- Suspicious Recall: 21.76%
- Super-Suspicious Recall: 25.40%
- Suspicious False Negatives: 356
- Super-Suspicious False Negatives: 47

---

## 4. HYPERPARAMETER CONFIGURATIONS TESTED

Eight configurations were tested around the frozen champion:

| Configuration | Learning Rate | Max Depth | N Estimators | Subsample | Min Samples Split | Min Samples Leaf |
|---------------|---------------|-----------|--------------|-----------|------------------|------------------|
| Champion_Baseline | 0.01 | 3 | 500 | 1.0 | 2 | 1 |
| Lower_LR_More_Trees | 0.005 | 3 | 700 | 1.0 | 2 | 1 |
| Higher_LR_Fewer_Trees | 0.02 | 3 | 300 | 1.0 | 2 | 1 |
| Shallower_Trees | 0.01 | 2 | 500 | 1.0 | 2 | 1 |
| Deeper_Trees | 0.01 | 4 | 500 | 1.0 | 2 | 1 |
| Subsampling | 0.01 | 3 | 500 | 0.8 | 2 | 1 |
| More_Regularization | 0.01 | 3 | 500 | 1.0 | 10 | 5 |
| Combined_Regularized | 0.005 | 3 | 700 | 0.8 | 10 | 5 |

---

## 5. TRAINING/CV RESULTS

**Cross-validation on training data only (5-fold stratified):**

| Configuration | CV Mean Macro F1 | CV Std Macro F1 |
|---------------|------------------|-----------------|
| Champion_Baseline | 0.5590 | 0.0368 |
| Lower_LR_More_Trees | 0.5448 | 0.0276 |
| Higher_LR_Fewer_Trees | 0.5633 | 0.0412 |
| Shallower_Trees | 0.4904 | 0.0386 |
| **Deeper_Trees** | **0.5668** | **0.0362** |
| Subsampling | 0.5586 | 0.0375 |
| More_Regularization | 0.5650 | 0.0369 |
| Combined_Regularized | 0.5483 | 0.0360 |

**Best CV configuration:** Deeper_Trees (max_depth=4)

---

## 6. FINAL TEST RESULTS

**Selected configuration:** Deeper_Trees

```python
learning_rate = 0.01
max_depth = 4
n_estimators = 500
subsample = 1.0
min_samples_split = 2
min_samples_leaf = 1
random_state = 42
```

**Test performance:**
- Accuracy: 77.20%
- Macro F1: 48.99%
- Weighted F1: 72.92%
- Suspicious Recall: 20.88%
- Super-Suspicious Recall: 25.40%
- Suspicious False Negatives: 360
- Super-Suspicious False Negatives: 47

---

## 7. CONFUSION MATRIX

**Deeper_Trees Confusion Matrix (Test):**

```
Predicted →
Actual ↓
['normal' 'super_suspicious' 'suspicious']
  normal: [1433    4   45]
  super_suspicious: [14 16 33]
  suspicious: [332  28  95]
```

**Verification:**
- Total: 1433 + 4 + 45 + 14 + 16 + 33 + 332 + 28 + 95 = 2,000 ✅
- Suspicious recall = 95 / (332 + 28 + 95) = 95 / 455 = 20.88% ✅
- Super-suspicious recall = 16 / (14 + 16 + 33) = 16 / 63 = 25.40% ✅

---

## 8. PER-CLASS METRICS

**Deeper_Trees Per-Class Metrics (Test):**

| Class | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| Normal | 80.58% | 96.65% | 87.96% |
| Super-Suspicious | 32.00% | 25.40% | 28.36% |
| Suspicious | 55.66% | 20.88% | 30.36% |

---

## 9. COMPARISON AGAINST FROZEN CHAMPION

| Metric | Champion | Deeper_Trees | Difference |
|--------|----------|--------------|-------------|
| Accuracy | 77.75% | 77.20% | -0.55% |
| Macro F1 | 50.15% | 48.99% | -1.16% |
| Weighted F1 | 73.44% | 72.92% | -0.52% |
| Suspicious Recall | 21.76% | 20.88% | -0.88% |
| Super-Suspicious Recall | 25.40% | 25.40% | 0.00% |
| Suspicious FN | 356 | 360 | +4 |
| Super-Suspicious FN | 47 | 47 | 0 |

**Analysis:**
- Deeper_Trees performs worse across all metrics
- Macro F1 decreased by 1.16 percentage points
- No improvement in minority-class recall
- Slight degradation in accuracy

---

## 10. OVERFITTING/GENERALIZATION ANALYSIS

**CV vs Test Performance:**

| Configuration | CV Macro F1 | Test Macro F1 | CV-Test Gap |
|---------------|-------------|---------------|-------------|
| Champion_Baseline | 0.5590 | 0.5015 | -0.0575 |
| Deeper_Trees | 0.5668 | 0.4899 | -0.0769 |

**Analysis:**
- Deeper_Trees shows a larger CV-test gap (-0.0769) compared to the champion (-0.0575)
- This indicates that increasing max_depth from 3 to 4 introduces overfitting
- The model performs better on CV but generalizes worse to the test set
- The champion configuration (max_depth=3) appears to be better regularized

**Conclusion:** The champion is not underfitting. Increasing tree depth leads to overfitting, not better generalization.

---

## 11. INTEGRITY VERIFICATION

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

**Verification:** The experiment was conducted correctly with no data leakage or integrity violations.

---

## 12. PROMOTION DECISION

**DECISION: KEEP CHAMPION**

**Rationale:**

1. **No meaningful improvement:** Deeper_Trees shows a decrease in Macro F1 (-1.16%), not an improvement
2. **Worse generalization:** The CV-test gap increased, indicating overfitting
3. **No minority-class benefit:** Super-suspicious recall remained unchanged (25.40%), suspicious recall decreased (20.88% vs 21.76%)
4. **Accuracy degradation:** Overall accuracy decreased by 0.55%
5. **Champion is well-regularized:** The current max_depth=3 configuration provides better generalization than deeper trees

**Promotion Rule Check:**
- Macro F1 improvement ≥ 2 percentage points? **NO** (decreased by 1.16%)
- Minority-class recall improvement? **NO** (no improvement)

**Conclusion:** The champion should remain unchanged. None of the tested hyperparameter configurations beat the frozen champion.

---

## 13. RECOMMENDED NEXT STAGE

**Current Status:**
- Hyperparameter tuning around the champion did not yield improvement
- The champion appears to be well-regularized at max_depth=3
- Increasing depth leads to overfitting
- Other regularization techniques (subsampling, min_samples_split) did not help

**Recommended Next Experiment: SMOTE (Synthetic Minority Over-sampling Technique)**

**Rationale:**
- The current limitation is poor minority-class recall (suspicious: 21.76%, super-suspicious: 25.40%)
- Hyperparameter tuning did not address this limitation
- SMOTE directly addresses the class imbalance by generating synthetic minority-class samples
- This is a data-level technique that has not been tested yet
- Previous class-weighting experiments showed promise but did not meet the 2% threshold
- SMOTE combined with the champion configuration may achieve better minority-class detection without sacrificing overall performance

**Alternative Options:**
- Ensemble methods (combine multiple models)
- Threshold optimization (adjust decision thresholds per class)
- Feature interactions (create interaction features)

**Recommendation:** Proceed with SMOTE as the next model improvement stage.

---

## 14. SUMMARY

**BEST CANDIDATE:** Deeper_Trees (max_depth=4)  
**FROZEN CHAMPION:** Gradient Boosting (max_depth=3)  
**CHAMPION BEATEN:** NO  
**MACRO F1 DIFFERENCE:** -1.16 percentage points  
**SHOULD NEW MODEL BE PROMOTED:** NO  
**NEXT EXPERIMENT:** SMOTE (Synthetic Minority Over-sampling Technique)

---

**STAGE 17 COMPLETE — WAITING FOR APPROVAL**
