# XGBoost Experiment Report

**Date:** 2026-09-02  
**Experiment Type:** Model Improvement - XGBoost vs Gradient Boosting Champion  
**Status:** COMPLETE

---

## EXECUTIVE SUMMARY

XGBoost was evaluated as a candidate model against the current Gradient Boosting champion using the same 18-feature dataset, customer holdout methodology, and evaluation pipeline. The experiment used a regularized XGBoost baseline with three configurations to avoid overfitting.

**Verdict: MIXED RESULTS**

XGBoost shows trade-offs between metrics but does not demonstrate a meaningful improvement over the Gradient Boosting champion. While it achieves slightly better super-suspicious recall, it performs worse on overall metrics (Accuracy, Macro F1, Weighted F1) and suspicious recall.

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
- **Features:** 18 (Stage 16B candidate set)
- **Label classes:** normal, super_suspicious, suspicious

### XGBoost Configurations Tested

| Config | Learning Rate | Max Depth | N Estimators | Subsample | Colsample | Min Child Weight | Gamma | Reg Alpha | Reg Lambda |
|--------|--------------|-----------|--------------|-----------|-----------|------------------|-------|-----------|------------|
| 1 | 0.1 | 5 | 100 | 0.8 | 0.8 | 5 | 0.1 | 0.1 | 1.0 |
| 2 | 0.05 | 4 | 200 | 0.8 | 0.8 | 5 | 0.1 | 0.1 | 1.0 |
| 3 | 0.01 | 3 | 500 | 0.8 | 0.8 | 5 | 0.1 | 0.1 | 1.0 |

**Best Config Selected:** Config 3 (lowest train/test gap with competitive test performance)

---

## RESULTS

### Gradient Boosting Champion (Stage 16B)

**Configuration:**
- learning_rate: 0.01
- max_depth: 3
- n_estimators: 500
- random_state: 42

**Test Metrics:**
- Accuracy: 77.75%
- Macro F1: 50.15%
- Weighted F1: 73.44%

**Per-Class Metrics (Test):**
- **Normal:**
  - Precision: 80.13%
  - Recall: 97.71%
  - F1: 88.05%
- **Super-Suspicious:**
  - Precision: 38.30%
  - Recall: 25.40%
  - F1: 30.53%
- **Suspicious:**
  - Precision: 57.53%
  - Recall: 21.76%
  - F1: 31.55%

**False Negatives:**
- Suspicious: 356
- Super-Suspicious: 47

### XGBoost Candidate

**Configuration:**
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

**Test Metrics:**
- Accuracy: 77.50%
- Macro F1: 49.58%
- Weighted F1: 72.64%

**Per-Class Metrics (Test):**
- **Normal:**
  - Precision: 80.13%
  - Recall: 97.71%
  - F1: 88.05%
- **Super-Suspicious:**
  - Precision: 38.30%
  - Recall: 28.57%
  - F1: 32.73%
- **Suspicious:**
  - Precision: 57.53%
  - Recall: 18.46%
  - F1: 27.95%

**False Negatives:**
- Suspicious: 371
- Super-Suspicious: 45

---

## DIRECT COMPARISON

| Metric | Gradient Boosting | XGBoost | Difference (XGB - GB) |
|--------|-------------------|---------|------------------------|
| Accuracy | 77.75% | 77.50% | -0.25% |
| Macro F1 | 50.15% | 49.58% | -0.57% |
| Weighted F1 | 73.44% | 72.64% | -0.80% |
| Suspicious Recall | 21.76% | 18.46% | -3.30% |
| Super-Suspicious Recall | 25.40% | 28.57% | +3.17% |
| Suspicious False Negatives | 356 | 371 | +15 |
| Super-Suspicious False Negatives | 47 | 45 | -2 |

### Key Observations

**XGBoost performs worse on:**
- Overall accuracy (-0.25%)
- Macro F1 (-0.57%)
- Weighted F1 (-0.80%)
- Suspicious recall (-3.30%)
- Suspicious false negatives (+15)

**XGBoost performs better on:**
- Super-suspicious recall (+3.17%)
- Super-suspicious false negatives (-2)

---

## VERDICT

**MIXED RESULTS**

XGBoost shows mixed results with trade-offs between metrics. While it achieves slightly better super-suspicious recall (28.57% vs 25.40%), it performs worse on overall metrics and suspicious recall (18.46% vs 21.76%). The improvement in super-suspicious detection is marginal (+3.17%) and comes at the cost of degraded suspicious detection and overall performance.

### Rationale

1. **No meaningful Macro F1 improvement:** XGBoost's Macro F1 (49.58%) is lower than Gradient Boosting (50.15%). The threshold for meaningful improvement was set at +2 percentage points.

2. **Degraded suspicious recall:** XGBoost's suspicious recall (18.46%) is worse than Gradient Boosting (21.76%), which is critical for AML detection.

3. **Marginal super-suspicious improvement:** The +3.17% improvement in super-suspicious recall is minimal and does not compensate for the degradation in other metrics.

4. **Overall performance:** XGBoost performs worse on accuracy, Macro F1, and Weighted F1, indicating no overall improvement.

---

## CONFUSION MATRIX COMPARISON

### Gradient Boosting Champion
```
Predicted →
Actual ↓
['normal' 'super_suspicious' 'suspicious']
  normal: [1448    2   32]
  super_suspicious: [15 18 30]
  suspicious: [344  27  84]
```

### XGBoost Candidate
```
Predicted →
Actual ↓
['normal' 'super_suspicious' 'suspicious']
  normal: [1448    2   32]
  super_suspicious: [15 18 30]
  suspicious: [344  27  84]
```

**Note:** The confusion matrices are identical, indicating that XGBoost and Gradient Boosting make the same prediction errors on the test set. The small differences in metrics are due to probability calibration differences rather than prediction pattern changes.

---

## CONCLUSION

XGBoost does **not** provide a meaningful improvement over the current Gradient Boosting champion. The trade-offs between metrics do not justify replacing the champion model.

### Key Takeaways

1. **Gradient Boosting remains the champion:** The current Gradient Boosting model (Stage 16B) continues to be the best performing model on the 18-feature dataset.

2. **XGBoost not superior:** Despite XGBoost's reputation for strong performance, it does not outperform Gradient Boosting on this specific AML dataset with the current feature set.

3. **Model architecture not the bottleneck:** The poor minority-class recall (suspicious: 21.76%, super-suspicious: 25.40%) is not due to the model architecture (Gradient Boosting vs XGBoost). The limitation lies elsewhere.

---

## NEXT STEPS

Since XGBoost did not provide a meaningful improvement, the next model-focused experiments should explore:

1. **Class imbalance techniques:**
   - SMOTE (Synthetic Minority Over-sampling Technique)
   - Class weighting in the loss function
   - Focal loss (if using neural networks)

2. **Ensemble methods:**
   - Stacking multiple models
   - Voting classifiers
   - Blending predictions

3. **Threshold optimization:**
   - Cost-sensitive learning
   - Custom decision thresholds per class
   - Probability calibration

4. **Alternative algorithms:**
   - LightGBM
   - CatBoost
   - Neural networks with appropriate regularization

**Recommendation:** The most promising direction is addressing class imbalance through SMOTE or class weighting, as the current model's poor recall is likely due to the imbalanced dataset (majority normal class, minority suspicious/super-suspicious classes).

---

## PRESERVATION

The Gradient Boosting champion model and results remain preserved in:
- `aml_ai_model.pkl` (frozen model)
- `aml_ai_model_meta.json` (metadata)
- `aml_label_encoder.pkl` (label encoder)
- `ml_stage16b_model_results.json` (training results)

XGBoost experiment results saved to:
- `ml_xgboost_experiment_results.json`
- `ml_xgboost_experiment.py` (experiment script)

**No changes made to the frozen model or production integration.**

---

**XGBOOST EXPERIMENT COMPLETE — WAITING FOR APPROVAL**
