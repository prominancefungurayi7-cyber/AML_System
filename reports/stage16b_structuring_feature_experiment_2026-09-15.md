# Stage 16B Structuring Feature Experiment Report

**Date:** 2026-09-15  
**Stage:** 16B — Controlled Structuring Feature Expansion Experiment  
**Status:** EXPERIMENT COMPLETE  
**Experiment Timestamp:** 2026-09-15T17:09:18.045616+00:00

---

## Executive Summary

A controlled ML experiment was conducted to evaluate whether four scientifically justified structuring features improve the weak Structuring-domain detection identified in Stage 16A. The experimental 34-feature model was trained and evaluated against the frozen Stage 14 baseline.

**Final Decision:** NOT SUPERIOR

**Unexpected Finding:** The experimental 34-feature model **degraded** Structuring-domain detection (29.8% vs 30.8% baseline) and Agent-domain detection (57.0% vs 58.8% baseline), despite showing modest overall improvement in Macro F1 (+0.0097). The new features did not provide the expected benefit to structuring detection.

---

## 1. Implementation Status

**Feature Implementation:** ✅ COMPLETE
- All four candidate features implemented correctly
- All 12 validation tests passed
- Temporal contracts properly enforced
- Leakage protection confirmed
- Original 30 features preserved exactly

**Model Training:** ✅ COMPLETE
- Gradient Boosting model trained on 34-feature matrices
- Stage 14 configuration used as starting point
- Threshold selected using validation only

**Evaluation:** ✅ COMPLETE
- Validation, Final Test, and Independent evaluation completed
- Domain/scenario analysis completed
- Baseline comparison completed

---

## 2. Experimental Configuration

**Dataset:** ecocash_aml_synthetic_100k_v1  
**Feature Count:** 34 (30 original + 4 new)  
**Model:** Gradient Boosting  
**Model Configuration:**
- learning_rate: 0.1
- max_depth: 3
- min_samples_leaf: 2
- min_samples_split: 5
- n_estimators: 200
- random_state: 42

**Selected Threshold:** 0.40 (vs baseline 0.35)  
**Validation Macro F1 at Threshold:** 0.7546

---

## 3. Experimental Results

### 3.1 Validation Results

| Metric | Experimental | Baseline | Difference |
|--------|-------------|----------|------------|
| Accuracy | 0.9025 | N/A | - |
| Macro F1 | 0.7546 | 0.7363 | +0.0183 |
| Suspicious Recall | 0.5256 | 0.5206 | +0.0050 |
| Suspicious Precision | 0.6088 | 0.5864 | +0.0224 |
| Suspicious F1 | 0.5641 | 0.5515 | +0.0126 |
| ROC-AUC | 0.8554 | 0.8474 | +0.0080 |
| PR-AUC | 0.6056 | 0.5829 | +0.0227 |
| FPR | 0.0461 | 0.0465 | -0.0004 |

### 3.2 Final Test Results

| Metric | Experimental | Baseline | Difference |
|--------|-------------|----------|------------|
| Accuracy | 0.9021 | 0.8984 | +0.0037 |
| Macro F1 | 0.7488 | 0.7471 | +0.0017 |
| Suspicious Recall | 0.5039 | 0.5206 | **-0.0167** |
| Suspicious Precision | 0.6116 | 0.5864 | +0.0252 |
| Suspicious F1 | 0.5525 | 0.5515 | +0.0010 |
| ROC-AUC | 0.8589 | 0.8474 | +0.0115 |
| PR-AUC | 0.5914 | 0.5829 | +0.0085 |
| FPR | 0.0436 | 0.0465 | -0.0029 |

### 3.3 Independent Results

| Metric | Experimental | Baseline | Difference |
|--------|-------------|----------|------------|
| Accuracy | 0.8870 | 0.8784 | +0.0086 |
| Macro F1 | 0.7342 | 0.7245 | +0.0097 |
| Suspicious Recall | 0.5367 | 0.5458 | **-0.0091** |
| Suspicious Precision | 0.5287 | 0.4940 | +0.0347 |
| Suspicious F1 | 0.5327 | 0.5186 | +0.0141 |
| ROC-AUC | 0.8410 | 0.8297 | +0.0113 |
| PR-AUC | 0.5708 | 0.5590 | +0.0118 |
| FPR | 0.0652 | 0.0762 | -0.0110 |

---

## 4. Domain Performance Analysis

### 4.1 Final Test Domain Performance

| Domain | Experimental Recall | Baseline Recall | Difference |
|--------|-------------------|-----------------|------------|
| Structuring | 23.0% | 24.8% | **-1.8%** |
| Network | 70.2% | 70.0% | +0.2% |
| Agent | 58.0% | 61.3% | **-3.3%** |

### 4.2 Independent Domain Performance

| Domain | Experimental Recall | Baseline Recall | Difference |
|--------|-------------------|-----------------|------------|
| Structuring | 29.8% | 30.8% | **-1.0%** |
| Network | 74.3% | 74.3% | 0.0% |
| Agent | 57.0% | 58.8% | **-1.8%** |

---

## 5. Research Question Analysis

**Primary Research Question:** Does adding the four targeted structuring features materially improve Structuring-domain detection and independent generalization without materially degrading Network or Agent performance?

**Answer:** NO

**Key Findings:**
1. **Structuring detection degraded:** Independent Structuring recall decreased from 30.8% to 29.8% (-1.0%)
2. **Agent detection degraded:** Independent Agent recall decreased from 58.8% to 57.0% (-1.8%)
3. **Network detection unchanged:** Independent Network recall remained at 74.3%
4. **Overall Macro F1 improved slightly:** Independent Macro F1 increased from 0.7245 to 0.7342 (+0.0097)
5. **Precision improved at cost of recall:** Suspicious precision improved (+0.0347) but recall decreased (-0.0091)

---

## 6. Generalization Analysis

### 6.1 Baseline Generalization
- Validation Macro F1: 0.7363
- Final Test Macro F1: 0.7471 (+0.0108)
- Independent Macro F1: 0.7245 (-0.0226 from validation)

### 6.2 Experimental Generalization
- Validation Macro F1: 0.7546
- Final Test Macro F1: 0.7488 (-0.0058)
- Independent Macro F1: 0.7342 (-0.0204 from validation)

**Analysis:** The experimental model shows similar generalization characteristics to the baseline. The validation advantage (+0.0183) partially disappears on independent data, but the degradation is comparable to the baseline.

---

## 7. Feature Contribution Analysis

The new features were expected to improve structuring detection, but the experimental results show the opposite. Possible explanations:

1. **Feature Quality:** The new features may not capture the intended behavioural patterns effectively
2. **Feature Noise:** The new features may introduce noise that degrades performance
3. **Model Capacity:** The 34-feature representation may exceed the model's capacity to learn effectively
4. **Threshold Sensitivity:** The higher threshold (0.40 vs 0.35) may be suboptimal for structuring detection
5. **Cold-Start Problem:** The 30-day windows may still suffer from cold-start issues

---

## 8. Error Analysis

### 8.1 False-Negative Analysis

The experimental model shows:
- Higher false negatives in Structuring domain (462 vs 451 baseline on Final Test)
- Higher false negatives in Agent domain (252 vs 192 baseline on Final Test)

This suggests the new features may not be providing useful signal for these domains.

### 8.2 False-Positive Analysis

The experimental model shows:
- Lower false positives (576 vs 664 baseline on Final Test)
- Lower FPR (0.0436 vs 0.0465 baseline)

This suggests the new features may be helping the model be more conservative, but at the cost of missing more suspicious transactions.

---

## 9. Model Selection Decision

**Decision:** NOT SUPERIOR

**Rationale:**
1. **Structuring detection degraded:** The primary goal was to improve structuring detection, but it worsened
2. **Agent detection degraded:** Unexpected side effect on Agent domain
3. **Overall improvement marginal:** Macro F1 improvement (+0.0097) is small and driven by precision gains, not recall
4. **Recall-precision trade-off unfavorable:** The model became more conservative, missing more suspicious transactions
5. **New features not providing expected benefit:** The four candidate features did not improve the target domain

---

## 10. Recommendation

**Recommendation:** DO NOT replace the Stage 14 baseline with the 34-feature model.

**The Stage 14 Gradient Boosting model remains the official frozen baseline.**

**Next Research Directions:**
1. **Re-evaluate feature design:** The four candidate features may not capture the intended behavioural patterns
2. **Investigate alternative approaches:** Consider different feature engineering strategies for structuring detection
3. **Analyze scenario-level failure:** Investigate why Distributed Same-Day Fragmentation and Variable Near-Threshold History remain difficult to detect
4. **Consider model architecture:** Explore whether different model families might better leverage the new features
5. **Feature selection:** Evaluate whether a subset of the new features might be beneficial rather than all four

---

## 11. Limitations

1. **Synthetic Data:** Results are based on synthetic data and may not generalize to real-world AML scenarios
2. **Single Experiment:** This is a single experimental run; multiple runs would provide more robust conclusions
3. **Feature Design:** The four candidate features were based on Stage 16A diagnostic findings, but may not have captured the root causes
4. **Model Configuration:** The Stage 14 configuration was used as a starting point; hyperparameter tuning specific to 34 features might yield different results
5. **Threshold Selection:** The threshold was selected using validation Macro F1; alternative selection criteria might yield different trade-offs

---

## 12. Data and Model Protection

**Unchanged Artifacts:**
- Stage 11 dataset: ✅ Unchanged
- Stage 13 feature matrices: ✅ Unchanged
- Stage 14 Gradient Boosting model: ✅ Unchanged
- Stage 15 XGBoost model: ✅ Unchanged
- Train/validation/final-test/independent partitions: ✅ Unchanged
- 30-feature specification: ✅ Unchanged
- Target labels: ✅ Unchanged
- MySQL database: ✅ Unchanged
- Application code: ✅ Unchanged

**Experimental Artifacts:**
- Stage 16B 34-feature matrices: Created separately from Stage 13
- Stage 16B expanded model: Created separately from Stage 14

---

## 13. Conclusion

The Stage 16B controlled feature expansion experiment was conducted with rigorous implementation and validation. However, the experimental 34-feature model **did not achieve the research objective** of improving Structuring-domain detection. Instead, it degraded performance in both Structuring and Agent domains while providing only marginal overall improvement.

The Stage 14 Gradient Boosting model with the original 30 features remains the preferred baseline for the EcoCash AML research project.

---

*Report generated as part of Stage 16B Structuring Feature Expansion Experiment*
*Date: 2026-09-15*
*Dataset: ecocash_aml_synthetic_100k_v1*
*Feature Matrix: Experimental 34-feature matrix*
*Baseline Model: Stage 14 Gradient Boosting*
*Experimental Model: Stage 16B Expanded Gradient Boosting*
*Stage 16B Status: COMPLETE*
*Final Decision: NOT SUPERIOR*
