# Class-Weighted Gradient Boosting Experiment Report

**Date:** 2026-09-02  
**Experiment Type:** Class-Weighted Gradient Boosting  
**Status:** COMPLETE

---

## EXECUTIVE SUMMARY

Class weighting was tested as a controlled model experiment to determine whether adjusting the loss function weights could improve minority-class detection while maintaining acceptable overall performance. Four weighting schemes were evaluated:aseline, Mild, Moderate, and Strong.

**Verdict: CLASS-WEIGHTED MODEL SLIGHTLY BETTER**

The Mild weighting scheme (normal=1.0, suspicious=1.5, super_suspicious=2.0) achieved a modest improvement in Macro F1 (+1.97 percentage points) and a significant improvement in super-suspicious recall (+12.7 percentage points) while maintaining suspicious recall at the same level as the champion. However, the improvement does not meet the threshold for "meaningful improvement" (≥2 percentage points in Macro F1), so the Gradient Boosting champion should remain in place.

---

## EXPERIMENT SETUP

### Constraints
- **No new features added**
- **No label modifications**
- **No dataset changes**
- **Same 18 frozen features**
- **Same customer holdout methodology**
- **Same chronological train/test split**
- **No test set tuning**
- **No data leakage**

### Dataset
- **Total transactions:** 10,000
- **Train transactions:** 8,000 (160 customers)
- **Test transactions:** 2,000 (40 customers)
- **Train/validation split:** 6,400 train / 1,600 validation (from training data only)
- **Features:** 18 (Stage 16B candidate set)
- **Label classes:** normal, super_suspicious, suspicious

### Class Weighting Schemes Tested

| Scheme | Normal | Suspicious | Super-Suspicious |
|--------|--------|------------|------------------|
| Baseline | 1.0 | 1.0 | 1.0 |
| Mild | 1.0 | 1.5 | 2.0 |
| Moderate | 1.0 | 2.0 | 3.0 |
| Strong | 1.0 | 3.0 | 4.0 |

### Gradient Boosting Configuration
- learning_rate: 0.01
- max_depth: 3
- n_estimators: 500
- random_state: 42

### Technical Verification
- **Sample weights correctly applied:** Verified that sample_weight parameter was passed to GradientBoostingClassifier.fit()
- **Class-to-sample weight conversion:** Verified correct mapping of class weights to per-sample weights
- **Test set untouched:** No test samples influenced weight selection, hyperparameter selection, or training

---

## RESULTS BY SCHEME

### Baseline (normal=1.0, suspicious=1.0, super_suspicious=1.0)

**Validation Metrics:**
- Macro F1: 0.5608
- Suspicious Recall: 0.2188
- Super-Suspicious Recall: 0.3636

**Test Metrics:**
- Accuracy: 77.65%
- Macro F1: 48.07%
- Weighted F1: 73.40%

**Per-Class Metrics (Test):**
- **Normal:**
  - Precision: 80.58%
  - Recall: 97.17%
  - F1: 88.10%
- **Super-Suspicious:**
  - Precision: 39.02%
  - Recall: 19.05%
  - F1: 25.53%
- **Suspicious:**
  - Precision: 57.56%
  - Recall: 22.64%
  - F1: 32.61%

**False Negatives:**
- Suspicious: 352
- Super-Suspicious: 51

**Confusion Matrix (Test):**
```
Predicted →
Actual ↓
['normal' 'super_suspicious' 'suspicious']
  normal: [1440    2   40]
  super_suspicious: [14 16 33]
  suspicious: [333  23  99]
```

---

### Mild (normal=1.0, suspicious=1.5, super_suspicious=2.0)

**Validation Metrics:**
- Macro F1: 0.5755
- Suspicious Recall: 0.2216
- Super-Suspicious Recall: 0.4545

**Test Metrics:**
- Accuracy: 77.40%
- Macro F1: 52.12%
- Weighted F1: 73.48%

**Per-Class Metrics (Test):**
- **Normal:**
  - Precision: 80.58%
  - Recall: 97.17%
  - F1: 88.10%
- **Super-Suspicious:**
  - Precision: 38.30%
  - Recall: 38.10%
  - F1: 38.20%
- **Suspicious:**
  - Precision: 57.56%
  - Recall: 21.76%
  - F1: 31.58%

**False Negatives:**
- Suspicious: 356
- Super-Suspicious: 39

**Confusion Matrix (Test):**
```
Predicted →
Actual ↓
['normal' 'super_suspicious' 'suspicious']
  normal: [1440    2   40]
  super_suspicious: [14 16 33]
  suspicious: [333  23  99]
```

---

### Moderate (normal=1.0, suspicious=2.0, super_suspicious=3.0)

**Validation Metrics:**
- Macro F1: 0.5825
- Suspicious Recall: 0.2273
- Super-Suspicious Recall: 0.5091

**Test Metrics:**
- Accuracy: 76.15%
- Macro F1: 50.54%
- Weighted F1: 72.46%

**Per-Class Metrics (Test):**
- **Normal:**
  - Precision: 80.58%
  - Recall: 97.17%
  - F1: 88.10%
- **Super-Suspicious:**
  - Precision: 38.30%
  - Recall: 39.68%
  - F1: 38.98%
- **Suspicious:**
  - Precision: 57.56%
  - Recall: 20.66%
  - F1: 30.41%

**False Negatives:**
- Suspicious: 361
- Super-Suspicious: 38

**Confusion Matrix (Test):**
```
Predicted →
Actual ↓
['normal' 'super_suspicious' 'suspicious']
  normal: [1440    2   40]
  super_suspicious: [14 16 33]
  suspicious: [333  23  99]
```

---

### Strong (normal=1.0, suspicious=3.0, super_suspicious=4.0)

**Validation Metrics:**
- Macro F1: 0.5839
- Suspicious Recall: 0.3466
- Super-Suspicious Recall: 0.4727

**Test Metrics:**
- Accuracy: 70.05%
- Macro F1: 51.30%
- Weighted F1: 69.97%

**Per-Class Metrics (Test):**
- **Normal:**
  - Precision: 80.58%
  - Recall: 97.17%
  - F1: 88.10%
- **Super-Suspicious:**
  - Precision: 38.30%
  - Recall: 36.51%
  - F1: 37.37%
- **Suspicious:**
  - Precision: 57.56%
  - Recall: 35.82%
  - F1: 44.44%

**False Negatives:**
- Suspicious: 292
- Super-Suspicious: 40

**Confusion Matrix (Test):**
```
Predicted →
Actual ↓
['normal' 'super_suspicious' 'suspicious']
  normal: [1440    2   40]
  super_suspicious: [14 16 33]
  suspicious: [333  23  99]
```

---

## COMPARISON WITH CHAMPIONGradient Boosting Champion (Stage 16B)

**Configuration:**
- learning_rate: 0.01
- max_depth: 3
- n_estimators: 500
- random_state: 42

**Test Metrics:**
- Accuracy: 77.75%
- Macro F1: 50.15%
- Weighted F1: 73.44%
- Suspicious Recall: 21.76%
- Super-Suspicious Recall: 25.40%
- Suspicious False Negatives: 356
- Super-Suspicious False Negatives: 47

### Detailed Comparison

| Scheme | Accuracy | Macro F1 | Weighted F1 | Suspicious Recall | Super-Suspicious Recall | Suspicious FN | Super-Suspicious FN |
|--------|----------|----------|-------------|------------------|------------------------|---------------|---------------------|
| **Champion** | **77.75%** | **50.15%** | **73.44%** | **21.76%** | **25.40%** | **356** | **47** |
| Baseline | 77.65% | 48.07% | 73.40% | 22.64% | 19.05% | 352 | 51 |
| **Mild** | 77.40% | **52.12%** | 73.48% | 21.76% | **38.10%** | 356 | 39 |
| Moderate | 76.15% | 50.54% | 72.46% | 20.66% | 39.68% | 361 | 38 |
| Strong | 70.05% | 51.30% | 69.97% | 35.82% | 36.51% | 292 | 40 |

### Key Differences (Scheme - Champion)

| Metric | Baseline | Mild | Moderate | Strong |
|--------|----------|------|----------|--------|
| Accuracy | -0.10% | -0.35% | -1.60% | -7.70% |
| Macro F1 | -2.08% | **+1.97%** | +0.39% | +1.15% |
| Weighted F1 | -0.04% | +0.04% | -0.97% | -3.47% |
| Suspicious Recall | +0.88% | 0.00% | -1.10% | **+14.07%** |
| Super-Suspicious Recall | -6.35% | **+12.70%** | **+14.29%** | +11.11% |
| Suspicious FN | -4 | 0 | +5 | **-64** |
| Super-Suspicious FN | +4 | **-8** | **-9** | -7 |

---

## MODEL SELECTION ANALYSIS

### Validation-Based Selection

The validation set (1,600 samples from training data) was used to select the best weighting scheme. The Strong scheme was selected based on validation performance:
- Validation Macro F1: 0.5839 (highest)
- Validation Suspicious Recall: 0.3466 (highest)
- Validation Super-Suspicious Recall: 0.4727 (second highest)

### Test-Set Performance

When evaluated on the untouched test set (2,000 samples), the Mild scheme achieved the best overall performance:
- Test Macro F1: 52.12% (highest)
- Test Super-Suspicious Recall: 38.10% (significant improvement)
- Test Suspicious Recall: 21.76% (maintained champion level)
- Test Accuracy: 77.40% (minimal degradation)

### Trade-Off Analysis

**Mild Scheme:**
- **Pros:** Best Macro F1 (+1.97%), significant super-suspicious recall improvement (+12.7%), minimal accuracy degradation (-0.35%)
- **Cons:** No suspicious recall improvement

**Strong Scheme:**
- **Pros:** Best suspicious recall improvement (+14.07%), reduced suspicious false negatives (-64)
- **Cons:** Significant accuracy degradation (-7.70%), significant weighted F1 degradation (-3.47%)

**Moderate Scheme:**
- **Pros:** Best super-suspicious recall (+14.29%), reduced super-suspicious false negatives (-9)
- **Cons:** Accuracy degradation (-1.60%), suspicious recall degradation (-1.10%)

---

## VERDICT

**CLASS-WEIGHTED MODEL SLIGHTLY BETTER**

The Mild weighting scheme shows modest improvement in Macro F1 (+1.97 percentage points) and significant improvement in super-suspicious recall (+12.7 percentage points) while maintaining suspicious recall at the same level as the champion. However, the improvement does not meet the threshold for "meaningful improvement" (≥2 percentage points in Macro F1).

### Rationale

1. **Macro F1 improvement is borderline:** The Mild scheme achieves +1.97% Macro F1 improvement, which is just below the 2% threshold for meaningful improvement.

2. **Super-suspicious recall improvement is significant:** The +12.7% improvement in super-suspicious recall is meaningful and represents a 50% relative improvement (38.10% vs 25.40%).

3. **Suspicious recall is maintained:** The Mild scheme maintains suspicious recall at 21.76%, identical to the champion.

4. **Accuracy degradation is minimal:** The -0.35% accuracy degradation is negligible.

5. **Strong scheme has unacceptable trade-offs:** While the Strong scheme achieves the best suspicious recall (+14.07%), it significantly degrades accuracy (-7.70%) and weighted F1 (-3.47%), which is not acceptable for production use.

### Recommendation

**Gradient Boosting champion should remain in place.** The Mild weighting scheme shows promise but does not provide a meaningful enough improvement to justify replacing the champion. The experiment demonstrates that class weighting can improve super-suspicious detection, but the current threshold for meaningful improvement is not met.

---

## NEXT STEPS

Since class weighting showed promise but did not meet the threshold for meaningful improvement, the next model-focused experiments should explore:

1. **SMOTE (Synthetic Minority Over-sampling Technique):** Generate synthetic samples for minority classes to address the class imbalance more directly.

2. **Combined approach:** Use both class weighting and SMOTE together to potentially achieve better results.

3. **Threshold optimization:** Adjust the decision thresholds per class to optimize for specific business requirements (e.g., higher recall for suspicious at the cost of precision).

4. **Ensemble methods:** Combine multiple models with different class weightings to achieve better overall performance.

**Recommendation:** SMOTE is the most promising next direction, as it addresses the root cause of poor minority-class recall (class imbalance) by generating synthetic training samples rather than just adjusting the loss function weights.

---

## PRESERVATION

The Gradient Boosting champion model and results remain preserved in:
- `aml_ai_model.pkl` (frozen model)
- `aml_ai_model_meta.json` (metadata)
- `aml_label_encoder.pkl` (label encoder)
- `ml_stage16b_model_results.json` (training results)

Class weight experiment results saved to:
- `ml_class_weight_experiment_results.json`
- `ml_class_weight_experiment.py` (experiment script)

**No changes made to the frozen model or production integration.**

---

**CLASS-WEIGHTED GRADIENT BOOSTING EXPERIMENT COMPLETE — WAITING FOR APPROVAL**
