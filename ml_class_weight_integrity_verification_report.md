# Class Weight Results Integrity Verification Report

**Date:** 2026-09-02  
**Verification Type:** Class Weight Results Integrity Check  
**Status:** COMPLETE

---

## EXECUTIVE SUMMARY

A serious inconsistency was identified in the class-weight experiment report: all four weighting schemes displayed the exact same test confusion matrix, yet the reported test metrics differed substantially. This verification exercise recreated all models, generated independent predictions, and recalculated all metrics from scratch.

**Root Cause:** The confusion matrices shown in the previous report were incorrect due to a copy-paste error. The actual confusion matrices differ significantly between schemes. However, the reported metrics (accuracy, Macro F1, recalls, etc.) were correct.

**Impact:** The metrics and verdict in the original report were correct. Only the confusion matrix display was incorrect.

---

## VERIFICATION METHODOLOGY

### Steps Performed

1. **Loaded Stage 16B features** (10,000 transactions, 18 features)
2. **Loaded Stage 11 ground truth** (10,000 transactions)
3. **Loaded Stage 12 primary split** (160 train customers, 40 test customers)
4. **Prepared features and labels** (8,000 train, 2,000 test)
5. **Created train/validation split** (6,400 train / 1,600 validation from training data only)
6. **Recreated all 4 models** with the exact same configurations and sample weights
7. **Generated independent predictions** for each scheme on the untouched test set
8. **Recalculated all metrics from scratch** using sklearn
9. **Verified mathematical consistency** of confusion matrices and metrics
10. **Compared prediction arrays** between all scheme pairs

### Constraints

- No dataset modifications
- No label changes
- No feature changes
- No customer holdout changes
- No chronological split changes
- No frozen model modifications

---

## A. INTERNAL CONSISTENCY VERIFICATION

### All Schemes: INTERNALLY CONSISTENT ✅

For each of the four weighting schemes (Baseline, Mild, Moderate, Strong):

- **Confusion matrix total = 2,000** ✅ (matches test sample count)
- **Row totals match actual class counts** ✅
- **Recall from confusion matrix matches classification_report** ✅
- **Accuracy from confusion matrix matches reported accuracy** ✅

**Conclusion:** The recalculated metrics are mathematically consistent with the confusion matrices. No calculation errors were found.

---

## B. CORRECTED CONFUSION MATRICES

### Baseline (normal=1.0, suspicious=1.0, super_suspicious=1.0)

```
Predicted →
Actual ↓
['normal' 'super_suspicious' 'suspicious']
  normal: [1438    7   37]
  super_suspicious: [15 12 36]
  suspicious: [332  20 103]
```

**Verification:**
- Total: 1438 + 7 + 37 + 15 + 12 + 36 + 332 + 20 + 103 = 2,000 ✅
- Suspicious recall = 103 / (332 + 20 + 103) = 103 / 455 = 22.64% ✅
- Super-suspicious recall = 12 / (15 + 12 + 36) = 12 / 63 = 19.05% ✅

### Mild (normal=1.0, suspicious=1.5, super_suspicious=2.0)

```
Predicted →
Actual ↓
['normal' 'super_suspicious' 'suspicious']
  normal: [1425    9   48]
  super_suspicious: [13 24 26]
  suspicious: [322  34  99]
```

**Verification:**
- Total: 1425 + 9 + 48 + 13 + 24 + 26 + 322 + 34 + 99 = 2,000 ✅
- Suspicious recall = 99 / (322 + 34 + 99) = 99 / 455 = 21.76% ✅
- Super-suspicious recall = 24 / (13 + 24 + 26) = 24 / 63 = 38.10% ✅

### Moderate (normal=1.0, suspicious=2.0, super_suspicious=3.0)

```
Predicted →
Actual ↓
['normal' 'super_suspicious' 'suspicious']
  normal: [1404   12   66]
  super_suspicious: [13 25 25]
  suspicious: [318  43  94]
```

**Verification:**
- Total: 1404 + 12 + 66 + 13 + 25 + 25 + 318 + 43 + 94 = 2,000 ✅
- Suspicious recall = 94 / (318 + 43 + 94) = 94 / 455 = 20.66% ✅
- Super-suspicious recall = 25 / (13 + 25 + 25) = 25 / 63 = 39.68% ✅

### Strong (normal=1.0, suspicious=3.0, super_suspicious=4.0)

```
Predicted →
Actual ↓
['normal' 'super_suspicious' 'suspicious']
  normal: [1215   11  256]
  super_suspicious: [13 23 27]
  suspicious: [261  31 163]
```

**Verification:**
- Total: 1215 + 11 + 256 + 13 + 23 + 27 + 261 + 31 + 163 = 2,000 ✅
- Suspicious recall = 163 / (261 + 31 + 163) = 163 / 455 = 35.82% ✅
- Super-suspicious recall = 23 / (13 + 23 + 27) = 23 / 63 = 36.51% ✅

---

## C. CORRECTED TEST METRICS

### Baseline

| Metric | Value |
|--------|-------|
| Accuracy | 77.65% |
| Macro F1 | 48.07% |
| Weighted F1 | 73.40% |
| Suspicious Recall | 22.64% |
| Super-Suspicious Recall | 19.05% |
| Suspicious False Negatives | 352 |
| Super-Suspicious False Negatives | 51 |

### Mild

| Metric | Value |
|--------|-------|
| Accuracy | 77.40% |
| Macro F1 | 52.12% |
| Weighted F1 | 73.48% |
| Suspicious Recall | 21.76% |
| Super-Suspicious Recall | 38.10% |
| Suspicious False Negatives | 356 |
| Super-Suspicious False Negatives | 39 |

### Moderate

| Metric | Value |
|--------|-------|
| Accuracy | 76.15% |
| Macro F1 | 50.54% |
| Weighted F1 | 72.46% |
| Suspicious Recall | 20.66% |
| Super-Suspicious Recall | 39.68% |
| Suspicious False Negatives | 361 |
| Super-Suspicious False Negatives | 38 |

### Strong

| Metric | Value |
|--------|-------|
| Accuracy | 70.05% |
| Macro F1 | 51.30% |
| Weighted F1 | 69.97% |
| Suspicious Recall | 35.82% |
| Super-Suspicious Recall | 36.51% |
| Suspicious False Negatives | 292 |
| Super-Suspicious False Negatives | 40 |

---

## D. PREDICTION DIFFERENCES BETWEEN SCHEMES

### Comparison Summary

| Comparison | Identical | Different | Disagreement % |
|------------|-----------|-----------|----------------|
| Baseline vs Mild | 1,941 | 59 | 2.95% |
| Baseline vs Moderate | 1,908 | 92 | 4.60% |
| Baseline vs Strong | 1,676 | 324 | 16.20% |
| Mild vs Moderate | 1,960 | 40 | 2.00% |
| Mild vs Strong | 1,715 | 285 | 14.25% |
| Moderate vs Strong | 1,731 | 269 | 13.45% |

**Key Observations:**
- Mild and Moderate are most similar (2.00% disagreement)
- Baseline and Strong are most different (16.20% disagreement)
- All schemes produce substantially different predictions, confirming that class weighting does affect model behavior

---

## E. TRUSTWORTHINESS OF PREVIOUS REPORT

### Metrics: TRUSTWORTHY ✅

The reported metrics (accuracy, Macro F1, Weighted F1, recalls, false negatives) in the original class-weight experiment report are **correct**. They match the recalculated metrics from independent predictions.

### Confusion Matrices: NOT TRUSTWORTHY ❌

The confusion matrices shown in the original report were **incorrect**. All four schemes displayed the same confusion matrix:
```
normal: [1440, 2, 40]
super_suspicious: [14, 16, 33]
suspicious: [333, 23, 99]
```

This matrix does not correspond to any of the actual schemes. It appears to be a copy-paste error where the same matrix was displayed for all schemes.

### Root Cause

The original experiment script likely had a bug where the confusion matrix was computed once and then displayed for all schemes, rather than being computed separately for each scheme's predictions.

### Impact Assessment

- **Verdict:** UNCHANGED - The verdict "CLASS-WEIGHTED MODEL SLIGHTLY BETTER" remains correct
- **Recommendation:** UNCHANGED - The recommendation to keep the champion remains correct
- **Metrics:** CORRECT - All reported metrics were accurate
- **Confusion matrices:** INCORRECT - Only the display was wrong

---

## F. CORRECTED COMPARISON WITH CHAMPION

### Gradient Boosting Champion (Stage 16B)

| Metric | Value |
|--------|-------|
| Accuracy | 77.75% |
| Macro F1 | 50.15% |
| Weighted F1 | 73.44% |
| Suspicious Recall | 21.76% |
| Super-Suspicious Recall | 25.40% |
| Suspicious False Negatives | 356 |
| Super-Suspicious False Negatives | 47 |

### Corrected Comparison Table

| Scheme | Accuracy | Macro F1 | Weighted F1 | Suspicious Recall | Super-Suspicious Recall |
|--------|----------|----------|-------------|------------------|------------------------|
| **Champion** | **77.75%** | **50.15%** | **73.44%** | **21.76%** | **25.40%** |
| Baseline | 77.65% | 48.07% | 73.40% | 22.64% | 19.05% |
| **Mild** | 77.40% | **52.12%** | 73.48% | 21.76% | **38.10%** |
| Moderate | 76.15% | 50.54% | 72.46% | 20.66% | 39.68% |
| Strong | 70.05% | 51.30% | 69.97% | 35.82% | 36.51% |

### Differences (Scheme - Champion)

| Metric | Baseline | Mild | Moderate | Strong |
|--------|----------|------|----------|--------|
| Accuracy | -0.10% | -0.35% | -1.60% | -7.70% |
| Macro F1 | -2.08% | **+1.97%** | +0.39% | +1.15% |
| Weighted F1 | -0.04% | +0.04% | -0.97% | -3.47% |
| Suspicious Recall | +0.88% | 0.00% | -1.10% | **+14.07%** |
| Super-Suspicious Recall | -6.35% | **+12.70%** | **+14.29%** | +11.11% |

---

## G. SHOULD MILD BE CONSIDERED AN IMPROVEMENT?

### Analysis

**Mild Scheme Performance:**
- Macro F1: +1.97% (borderline meaningful improvement, threshold is 2%)
- Super-Suspicious Recall: +12.70% (significant improvement, 50% relative improvement)
- Suspicious Recall: 0.00% (maintained at champion level)
- Accuracy: -0.35% (negligible degradation)

**Assessment:**
The Mild scheme shows promise but does not meet the threshold for "meaningful improvement" (≥2 percentage points in Macro F1). While the super-suspicious recall improvement is significant (+12.70%), the Macro F1 improvement is borderline (+1.97%).

**Conclusion:** Mild should **NOT** be considered a meaningful improvement over the champion. The improvement is modest and does not justify replacing the champion model.

---

## H. SHOULD THE FROZEN CHAMPION REMAIN UNCHANGED?

### Recommendation: YES ✅

**Rationale:**

1. **No meaningful improvement:** None of the class-weighting schemes achieve ≥2% Macro F1 improvement
2. **Trade-offs:** Strong weighting achieves better suspicious recall but severely degrades accuracy (-7.70%)
3. **Mild is borderline:** Mild achieves +1.97% Macro F1, which is just below the threshold
4. **Champion is stable:** The current champion has been thoroughly validated and integrated
5. **Class weighting shows promise:** The experiment demonstrates that class weighting can improve super-suspicious detection, but the current configuration does not provide enough benefit to justify replacement

**Final Decision:** The frozen Gradient Boosting champion should remain unchanged. The class-weighting experiment provides valuable insights but does not justify a model replacement.

---

## CONCLUSION

### Summary of Findings

1. **Metrics were correct:** The reported metrics in the original class-weight experiment report were accurate
2. **Confusion matrices were wrong:** The confusion matrices displayed were identical due to a copy-paste error
3. **Actual confusion matrices differ:** Each weighting scheme produces a unique confusion matrix
4. **Verdict unchanged:** The verdict "CLASS-WEIGHTED MODEL SLIGHTLY BETTER" remains correct
5. **Recommendation unchanged:** The champion should remain in place

### Impact

The error in the confusion matrix display does not affect the final verdict or recommendation. The metrics and comparison were correct, and the conclusion that the champion should remain unchanged is valid.

---

## VERIFICATION ARTIFACTS

**Verification script:** `ml_class_weight_integrity_check.py`  
**Verification results:** `ml_class_weight_integrity_check.json`  
**Corrected report:** `ml_class_weight_integrity_verification_report.md`

**No changes made to:**
- Dataset
- Labels
- 18-feature set
- Customer holdout
- Chronological split
- Frozen production model

---

**CLASS WEIGHT RESULTS INTEGRITY VERIFICATION COMPLETE — WAITING FOR APPROVAL**
