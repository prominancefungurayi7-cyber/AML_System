# Results Integrity Verification Report

**Date:** 2026-09-02  
**Verification Type:** Results Integrity Check  
**Status:** COMPLETE

---

## EXECUTIVE SUMMARY

A serious internal inconsistency was identified in the XGBoost experiment report. The confusion matrix shown for both models was identical, but the reported metrics differed. This verification exercise recalculated all metrics from scratch and determined the actual prediction disagreement between the models.

**Root Cause:** The confusion matrix shown in the previous report was from XGBoost only, not Gradient Boosting. The models actually differ on 46 test samples (2.30%).

---

## VERIFICATION METHODOLOGY

### Steps Performed

1. **Loaded Stage 16B features** (10,000 transactions, 18 features)
2. **Loaded Stage 11 ground truth** (10,000 transactions)
3. **Loaded Stage 12 primary split** (160 train customers, 40 test customers)
4. **Prepared features and labels** (8,000 train, 2,000 test)
5. **Confirmed class ordering:** normal, super_suspicious, suspicious
6. **Retrained Gradient Boosting** with champion config (learning_rate=0.01, max_depth=3, n_estimators=500)
7. **Trained XGBoost** with best config (learning_rate=0.01, max_depth=3, n_estimators=500, with regularization)
8. **Generated predictions** from both models on the test set
9. **Recalculated all metrics from scratch** using sklearn
10. **Compared prediction arrays** to determine disagreement

### Constraints

- No dataset modifications
- No label changes
- No feature changes
- No customer holdout changes
- No chronological split changes
- No frozen model modifications

---

## A. CORRECTED GRADIENT BOOSTING METRICS

### Configuration
- learning_rate: 0.01
- max_depth: 3
- n_estimators: 500
- random_state: 42

### Overall Metrics
- **Test Accuracy:** 77.75%
- **Test Macro F1:** 50.15%
- **Test Weighted F1:** 73.44%

### Per-Class Metrics (Test)

| Class | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| normal | 80.58% | 97.17% | 88.10% |
| super_suspicious | 39.02% | 25.40% | 30.77% |
| suspicious | 57.56% | 21.76% | 31.58% |

### False Negatives
- **Suspicious False Negatives:** 356
- **Super-Suspicious False Negatives:** 47

### Confusion Matrix (Test)

```
Predicted →
Actual ↓
['normal' 'super_suspicious' 'suspicious']
  normal: [1440    2   40]
  super_suspicious: [14 16 33]
  suspicious: [333  23  99]
```

**Verification:**
- Suspicious recall = 99 / (333 + 23 + 99) = 99 / 455 = 21.76% ✅
- Super-suspicious recall = 16 / (14 + 16 + 33) = 16 / 63 = 25.40% ✅

---

## B. CORRECTED XGBOOST METRICS

### Configuration
- learning_rate: 0.01
- max_depth: 3
- n_estimators: 500
- subsample: 0.8
- colsample_bytree: 0.8
- min_child_weight: 5
- gamma: 0.1
- reg_alpha: 0.1
- reg_lambda: 1.0
- random_state: 42
- eval_metric: mlogloss

### Overall Metrics
- **Test Accuracy:** 77.50%
- **Test Macro F1:** 49.58%
- **Test Weighted F1:** 72.64%

### Per-Class Metrics (Test)

| Class | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| normal | 80.13% | 97.71% | 88.05% |
| super_suspicious | 38.30% | 28.57% | 32.73% |
| suspicious | 57.53% | 18.46% | 27.95% |

### False Negatives
- **Suspicious False Negatives:** 371
- **Super-Suspicious False Negatives:** 45

### Confusion Matrix (Test)

```
Predicted →
Actual ↓
['normal' 'super_suspicious' 'suspicious']
  normal: [1448    2   32]
  super_suspicious: [15 18 30]
  suspicious: [344  27  84]
```

**Verification:**
- Suspicious recall = 84 / (344 + 27 + 84) = 84 / 455 = 18.46% ✅
- Super-suspicious recall = 18 / (15 + 18 + 30) = 18 / 63 = 28.57% ✅

---

## C. CORRECTED CONFUSION MATRICES

### Gradient Boosting Confusion Matrix

| Actual \ Predicted | Normal | Super-Suspicious | Suspicious |
|-------------------|--------|------------------|------------|
| Normal | 1440 | 2 | 40 |
| Super-Suspicious | 14 | 16 | 33 |
| Suspicious | 333 | 23 | 99 |

### XGBoost Confusion Matrix

| Actual \ Predicted | Normal | Super-Suspicious | Suspicious |
|-------------------|--------|------------------|------------|
| Normal | 1448 | 2 | 32 |
| Super-Suspicious | 15 | 18 | 30 |
| Suspicious | 344 | 27 | 84 |

**Key Differences:**
- Normal → Normal: GB=1440, XGB=1448 (XGB corrects 8 more normals)
- Normal → Suspicious: GB=40, XGB=32 (XGB has 8 fewer false positives)
- Super-Suspicious → Normal: GB=14, XGB=15 (XGB has 1 more false negative)
- Super-Suspicious → Super-Suspicious: GB=16, XGB=18 (XGB corrects 2 more)
- Super-Suspicious → Suspicious: GB=33, XGB=30 (XGB has 3 fewer misclassifications)
- Suspicious → Normal: GB=333, XGB=344 (XGB has 11 more false negatives)
- Suspicious → Super-Suspicious: GB=23, XGB=27 (XGB has 4 more misclassifications)
- Suspicious → Suspicious: GB=99, XGB=84 (XGB has 15 fewer correct detections)

---

## D. PREDICTION DISAGREEMENT ANALYSIS

### Overall Disagreement

- **Total test samples:** 2,000
- **Identical predictions:** 1,954 (97.70%)
- **Different predictions:** 46 (2.30%)

### Disagreement Breakdown

The 46 samples where the models disagree include:

| Sample | True Label | GB Prediction | XGB Prediction |
|--------|------------|---------------|----------------|
| 827 | normal | suspicious | super_suspicious |
| 945 | suspicious | suspicious | normal |
| 946 | normal | super_suspicious | suspicious |
| 1000 | normal | suspicious | normal |
| 1010 | normal | suspicious | normal |
| 1012 | normal | suspicious | normal |
| 1015 | suspicious | suspicious | super_suspicious |
| 1016 | normal | suspicious | super_suspicious |
| 1017 | normal | suspicious | normal |
| 1019 | normal | suspicious | normal |
| ... | ... | ... | ... |

**Pattern:** XGBoost tends to be more conservative on suspicious predictions (classifying more as normal), while Gradient Boosting is slightly more aggressive in detecting suspicious patterns.

---

## E. EXPLANATION OF DISCREPANCY

### What Went Wrong in the Previous Report

The previous XGBoost experiment report contained the following errors:

1. **Incorrect confusion matrix claim:** The report stated that the confusion matrices for Gradient Boosting and XGBoost were identical. This was false.

2. **Wrong confusion matrix for Gradient Boosting:** The confusion matrix shown in the report:
   ```
   normal: [1448, 2, 32]
   super_suspicious: [15, 18, 30]
   suspicious: [344, 27, 84]
   ```
   This matrix corresponds to XGBoost, not Gradient Boosting. When calculating recall from this matrix:
   - Suspicious recall = 84 / 455 = 18.46% (matches XGBoost, not GB)
   - Super-suspicious recall = 18 / 63 = 28.57% (matches XGBoost, not GB)

3. **Logical inconsistency:** The report claimed identical confusion matrices but different metrics. This is impossible because if the exact predicted class for every test transaction is identical, accuracy, precision, recall, F1, and the confusion matrix must also be identical.

### Root Cause

The XGBoost experiment script likely displayed the XGBoost confusion matrix twice (once for each model) due to a copy-paste error or variable reference error. The metrics were correctly calculated from the actual predictions, but the confusion matrix display was incorrect.

### Corrected Understanding

- The models are **not identical** - they disagree on 46 samples (2.30%)
- Gradient Boosting has better suspicious recall (21.76% vs 18.46%)
- XGBoost has slightly better super-suspicious recall (28.57% vs 25.40%)
- The metrics reported in the previous report were correct, but the confusion matrix was wrong

---

## F. CORRECTED VERDICT

### Comparison Summary

| Metric | Gradient Boosting | XGBoost | Difference (XGB - GB) |
|--------|-------------------|---------|------------------------|
| Accuracy | 77.75% | 77.50% | -0.25% |
| Macro F1 | 50.15% | 49.58% | -0.57% |
| Weighted F1 | 73.44% | 72.64% | -0.80% |
| Suspicious Recall | 21.76% | 18.46% | -3.30% |
| Super-Suspicious Recall | 25.40% | 28.57% | +3.17% |
| Suspicious False Negatives | 356 | 371 | +15 |
| Super-Suspicious False Negatives | 47 | 45 | -2 |

### Verdict

**MIXED RESULTS**

XGBoost shows mixed results with trade-offs between metrics. While it achieves slightly better super-suspicious recall (+3.17%), it performs worse on overall metrics (Accuracy -0.25%, Macro F1 -0.57%, Weighted F1 -0.80%) and suspicious recall (-3.30%). The improvement in super-suspicious detection is marginal and does not compensate for the degradation in other metrics.

### Rationale

1. **No meaningful Macro F1 improvement:** XGBoost's Macro F1 (49.58%) is lower than Gradient Boosting (50.15%). The threshold for meaningful improvement was set at +2 percentage points.

2. **Degraded suspicious recall:** XGBoost's suspicious recall (18.46%) is worse than Gradient Boosting (21.76%), which is critical for AML detection. This represents a 15% relative increase in false negatives (371 vs 356).

3. **Marginal super-suspicious improvement:** The +3.17% improvement in super-suspicious recall is minimal and does not compensate for the degradation in other metrics.

4. **Overall performance:** XGBoost performs worse on accuracy, Macro F1, and Weighted F1, indicating no overall improvement.

---

## CONCLUSION

### Corrected Assessment

XGBoost does **not** provide a meaningful improvement over the current Gradient Boosting champion. The corrected verdict remains "MIXED RESULTS" with the same conclusion as before: Gradient Boosting should remain the champion.

### Impact of the Discrepancy

The discrepancy in the previous report did not affect the final verdict, but it did affect the explanation:
- **Previous claim:** Models make identical predictions (false)
- **Corrected finding:** Models disagree on 46 samples (2.30%)

The metrics reported in the previous report were correct, so the comparison and verdict remain valid. Only the confusion matrix display and the explanation of prediction agreement were incorrect.

### Recommendation

Gradient Boosting remains the champion model. The next model-focused experiment should explore class imbalance techniques (SMOTE, class weighting) to address the poor minority-class recall, which is the fundamental limitation of the current model.

---

## VERIFICATION ARTIFACTS

**Verification script:** `ml_results_integrity_check.py`  
**Verification results:** `ml_results_integrity_check.json`  
**Corrected report:** `ml_results_integrity_verification_report.md`

**No changes made to:**
- Dataset
- Labels
- 18-feature set
- Customer holdout
- Chronological split
- Frozen production model

---

**RESULTS INTEGRITY CHECK COMPLETE — WAITING FOR APPROVAL**
