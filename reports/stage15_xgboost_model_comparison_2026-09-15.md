# Stage 15 XGBoost Model Comparison Report

**Date:** 2026-09-15  
**Stage:** 15 — XGBoost Challenger Model Experiment  
**Status:** PASS — EXPERIMENT COMPLETED  
**Experiment Timestamp:** 2026-09-15T16:28:58.019191+00:00  
**Training Duration:** 81.6 seconds

---

## Executive Summary

A controlled XGBoost challenger model experiment was conducted against the existing frozen Stage 14 Gradient Boosting model to determine whether XGBoost provides a genuine improvement for the EcoCash mobile-money AML research problem. The experiment used only the existing frozen Stage 13 feature matrices and maintained strict data separation protocols.

**Final Decision:** XGBOOST NOT SUPERIOR

The XGBoost model shows marginal improvements on the Final Test set but performs essentially equivalently on the Independent evaluation population. The small performance differences do not justify replacing the existing Stage 14 Gradient Boosting baseline, which remains the preferred model due to its simplicity and equivalent generalization capability.

---

## 1. Objective

Run a controlled XGBoost model experiment against the existing frozen Stage 14 Gradient Boosting model to determine whether XGBoost provides a genuine improvement for the EcoCash mobile-money AML research problem. This is a model comparison experiment only.

---

## 2. Authoritative Inputs

**Dataset Version:** ecocash_aml_synthetic_100k_v1  
**Feature Matrix Version:** Stage 13 frozen matrices  
**Feature Count:** 30 (unchanged from Stage 13)  
**Feature Names:** Locked from Stage 13 feature_names.json

**Dataset Shapes:**
- Train: 60,000 × 30
- Validation: 15,000 × 30
- Final Test: 15,000 × 30
- Independent: 10,000 × 30

**Target:** Binary 0/1  
**Class Distribution:** 88,000 normal (88%), 12,000 suspicious (12%)

**Data Integrity:** All Stage 13 matrices verified via checksums; no modifications occurred.

---

## 3. Existing Baseline

**Baseline Model:** Stage 14 Gradient Boosting (frozen)  
**Baseline Parameters:**
- learning_rate: 0.1
- max_depth: 3
- min_samples_leaf: 2
- min_samples_split: 5
- n_estimators: 200
- random_state: 42

**Baseline Threshold:** 0.35

**Baseline Results:**
- Validation Macro F1: 0.7363
- Final Test Macro F1: 0.7471
- Independent Macro F1: 0.7245
- Final Test Suspicious Recall: 0.5206
- Independent Suspicious Recall: 0.5458
- Final Test ROC-AUC: 0.8474
- Independent ROC-AUC: 0.8297

The baseline model was not retrained or modified during this experiment.

---

## 4. XGBoost Implementation

**XGBoost Version:** 3.4.1  
**Python Version:** 3.14  
**Implementation:** Native XGBoost API with DMatrix format  
**Random Seed:** 42 (fixed for reproducibility)

**Class Imbalance Handling:**
- Method: scale_pos_weight parameter
- Calculated weight: 7.3333 (negative/positive ratio)
- Rationale: Built-in XGBoost class weighting, no synthetic data modification

**Input Features:** Only the 30 Stage 13 numerical features  
**Excluded from Model:** Transaction IDs, wallet IDs, customer IDs, agent IDs, timestamps, event sequence, partition identifiers, scenario IDs, scenario types, ground-truth metadata, risk scores, risk levels, rule outputs, alerts, investigations, model outputs

---

## 5. Training/Validation Protocol

**Strict Protocol Compliance:**
- Training set: Used only 60,000 training rows for fitting
- Validation set: Used only 15,000 validation rows for hyperparameter selection, model selection, and threshold selection
- Early stopping: Applied with 20-round patience on validation set
- Final Test: Completely untouched during training and tuning
- Independent: Completely unseen during training, tuning, and threshold selection

**No violations of data separation protocols detected.**

---

## 6. Hyperparameter Search

**Search Type:** Controlled random search (50 combinations)  
**Search Space:**
- n_estimators: [100, 200, 300]
- learning_rate: [0.05, 0.1, 0.2]
- max_depth: [3, 4, 5]
- min_child_weight: [1, 2, 3]
- subsample: [0.8, 0.9, 1.0]
- colsample_bytree: [0.8, 0.9, 1.0]
- gamma: [0, 0.1, 0.2]
- reg_alpha: [0, 0.1, 0.5]
- reg_lambda: [1, 1.5, 2]

**Optimization Metric:** Validation Macro F1  
**Reproducibility:** Fixed random seed (42)

**Selected Hyperparameters:**
- objective: binary:logistic
- eval_metric: logloss
- scale_pos_weight: 7.3333
- random_state: 42
- n_estimators: 300
- learning_rate: 0.05
- max_depth: 5
- min_child_weight: 3
- subsample: 0.8
- colsample_bytree: 0.8
- gamma: 0.2
- reg_alpha: 0.5
- reg_lambda: 2.0

**Search Efficiency:** 50 combinations tested in 81.6 seconds

---

## 7. Model Selection Metric

**Primary Metric:** Validation Macro F1  
**Best Validation Macro F1:** 0.7544  
**Baseline Validation Macro F1:** 0.7363  
**Improvement:** +0.0181 (+2.5%)

**Additional Metrics Recorded:**
- Suspicious precision: 0.5732
- Suspicious recall: 0.5611
- Suspicious F1: 0.5671
- Normal precision: 0.9403
- Normal recall: 0.9430
- Normal F1: 0.9417
- Accuracy: 0.8972
- Balanced accuracy: 0.7521
- ROC-AUC: 0.8542
- PR-AUC: 0.6022
- False-positive rate: 0.0570

Model selection was based solely on validation performance; no test or independent data was used.

---

## 8. Threshold Selection

**Method:** Threshold range evaluation (0.1 to 0.9 in 0.05 increments) on validation set  
**Optimization Metric:** Validation Macro F1  
**Selected Threshold:** 0.75  
**Validation Macro F1 at Threshold:** 0.7544

**Threshold Rationale:** The 0.75 threshold optimized the trade-off between precision and recall for the imbalanced dataset, maximizing Macro F1 on the validation set. This is higher than the baseline threshold of 0.35, reflecting XGBoost's different probability calibration.

**Threshold Freeze:** Once selected, the threshold was frozen; no further changes were made.

---

## 9. Final Test Results

**Dataset:** Final Test (15,000 transactions)  
**Model:** Frozen XGBoost with threshold 0.75

**Metrics:**
- Accuracy: 0.8971
- Balanced Accuracy: 0.7434
- Macro F1: 0.7499
- Suspicious Recall: 0.5411
- Suspicious Precision: 0.5760
- Suspicious F1: 0.5580
- Normal Recall: 0.9457
- Normal Precision: 0.9379
- Normal F1: 0.9418
- ROC-AUC: 0.8559
- PR-AUC: 0.5892
- False Positive Rate: 0.0543

**Confusion Matrix:**
- True Negatives: 12,483
- False Positives: 717
- False Negatives: 826
- True Positives: 974

**Interpretation:** The XGBoost model achieves comparable overall accuracy (89.7%) with slightly higher suspicious recall (54.1% vs 52.1% baseline) and slightly lower suspicious precision (57.6% vs 58.6% baseline). The ROC-AUC improvement (0.8559 vs 0.8474) is modest.

---

## 10. Independent Evaluation

**Dataset:** Independent Evaluation (10,000 transactions)  
**Model:** Same frozen XGBoost with threshold 0.75

**Metrics:**
- Accuracy: 0.8759
- Balanced Accuracy: 0.7391
- Macro F1: 0.7241
- Suspicious Recall: 0.5592
- Suspicious Precision: 0.4852
- Suspicious F1: 0.5196
- Normal Recall: 0.9191
- Normal Precision: 0.9386
- Normal F1: 0.9287
- ROC-AUC: 0.8331
- PR-AUC: 0.5499
- False Positive Rate: 0.0809

**Confusion Matrix:**
- True Negatives: 8,088
- False Positives: 712
- False Negatives: 529
- True Positives: 671

**Interpretation:** On the unseen independent population, XGBoost performance is essentially equivalent to the baseline (Macro F1: 0.7241 vs 0.7245 baseline). The suspicious recall improvement (55.9% vs 54.6% baseline) is offset by lower precision (48.5% vs 49.4% baseline). The PR-AUC is slightly lower (0.5499 vs 0.5590 baseline).

---

## 11. Domain Performance Analysis

**Methodology:** Post-hoc analysis using frozen XGBoost predictions and Stage 11 ground-truth scenario metadata. This is evaluation-only; no model parameters were modified based on domain results.

### 11.1 Final Test Domain Performance

**Structuring Domain**
- Total Suspicious: 600
- True Positives: 152
- False Negatives: 448
- Suspicious Recall: 0.2533 (25.3%)
- **Baseline Recall:** 0.2483 (24.8%)
- **Difference:** +0.0050 (+0.5%)

**Network Domain**
- Total Suspicious: 600
- True Positives: 416
- False Negatives: 184
- Suspicious Recall: 0.6933 (69.3%)
- **Baseline Recall:** 0.7000 (70.0%)
- **Difference:** -0.0067 (-0.7%)

**Agent Domain**
- Total Suspicious: 600
- True Positives: 406
- False Negatives: 194
- Suspicious Recall: 0.6767 (67.7%)
- **Baseline Recall:** 0.6133 (61.3%)
- **Difference:** +0.0634 (+6.3%)

### 11.2 Independent Domain Performance

**Structuring Domain**
- Total Suspicious: 400
- True Positives: 112
- False Negatives: 288
- Suspicious Recall: 0.2800 (28.0%)
- **Baseline Recall:** 0.3075 (30.8%)
- **Difference:** -0.0275 (-2.8%)

**Network Domain**
- Total Suspicious: 400
- True Positives: 294
- False Negatives: 106
- Suspicious Recall: 0.7350 (73.5%)
- **Baseline Recall:** 0.7425 (74.3%)
- **Difference:** -0.0075 (-0.8%)

**Agent Domain**
- Total Suspicious: 400
- True Positives: 265
- False Negatives: 135
- Suspicious Recall: 0.6625 (66.3%)
- **Baseline Recall:** 0.5875 (58.8%)
- **Difference:** +0.0750 (+7.5%)

### 11.3 Domain Performance Interpretation

XGBoost shows mixed domain performance:
- **Agent behaviours:** Improved detection (+6-8% recall) on both final test and independent
- **Network behaviours:** Slightly lower detection (-0.7-0.8% recall) on both sets
- **Structuring behaviours:** Similar performance (+0.5% on final test, -2.8% on independent)

The agent domain improvement is notable but offset by network domain degradation. Overall domain performance is essentially equivalent to baseline.

---

## 12. Scenario Family Performance Analysis

**Methodology:** Post-hoc analysis of frozen XGBoost predictions against 12 scenario families. This is evaluation-only; no model parameters were modified based on scenario results.

### 12.1 Final Test Scenario Performance (Top Performers)

| Scenario Family | Recall | Baseline Recall | Difference |
|----------------|--------|-----------------|------------|
| One-to-Many Dispersion | 0.8800 | 0.8733 | +0.0067 |
| Agent Temporal Burst | 0.8467 | 0.8067 | +0.0400 |
| Agent Flow Imbalance | 0.7133 | 0.6400 | +0.0733 |
| Many-to-One Collection | 0.6867 | 0.7000 | -0.0133 |
| Agent Wallet Concentration | 0.6600 | 0.5800 | +0.0800 |

### 12.2 Independent Scenario Performance (Top Performers)

| Scenario Family | Recall | Baseline Recall | Difference |
|----------------|--------|-----------------|------------|
| One-to-Many Dispersion | 0.8900 | 0.8900 | 0.0000 |
| Many-to-One Collection | 0.8800 | 0.8900 | -0.0100 |
| Agent Temporal Burst | 0.8000 | 0.7600 | +0.0400 |
| Agent Wallet Concentration | 0.7000 | 0.6400 | +0.0600 |
| Agent Wallet Growth | 0.7200 | 0.6500 | +0.0700 |

### 12.3 Scenario Performance Interpretation

XGBoost shows improved performance on agent-centric scenarios (Agent Temporal Burst, Agent Flow Imbalance, Agent Wallet Concentration) but similar or slightly degraded performance on network-centric scenarios. The overall pattern mirrors the domain-level analysis: agent behaviours improved, network behaviours similar or slightly worse.

---

## 13. Feature Importance

**Method:** XGBoost gain-based importance  
**Top 10 Features by Importance:**
1. network_current_receiver_is_new: 865.21
2. agent_prior_tx_count_7d: 406.61
3. structuring_same_day_prior_tx_count: 184.91
4. network_outbound_counterparty_count_7d: 146.94
5. agent_unique_wallet_count_7d: 126.49
6. structuring_prior_tx_count_1h: 123.34
7. structuring_prior_value_sum_24h: 95.70
8. agent_current_wallet_is_new: 86.52
9. network_repeated_receiver_ratio_30d: 78.29
10. structuring_repeated_amount_ratio_7d: 74.52

**Feature Importance Composition:**
- Network features: 4/10 top features (highest importance: network_current_receiver_is_new)
- Agent features: 3/10 top features (highest importance: agent_prior_tx_count_7d)
- Structuring features: 3/10 top features (highest importance: structuring_same_day_prior_tx_count)

**Interpretation:** The feature importance pattern is similar to the baseline, with network features dominating. The addition of agent_unique_wallet_count_7d in the top 10 reflects XGBoost's different feature weighting.

**Important Note:** Feature importance represents contribution to model predictions, NOT actual domain detection performance. As shown in Section 11, actual domain detection performance differs from feature importance composition.

---

## 14. Direct Baseline Comparison

### 14.1 Validation Comparison

| Metric | XGBoost | Baseline | Difference |
|--------|---------|----------|------------|
| Macro F1 | 0.7544 | 0.7363 | +0.0181 |
| Suspicious Recall | 0.5611 | 0.5206 | +0.0405 |
| Suspicious Precision | 0.5732 | 0.5864 | -0.0132 |
| Suspicious F1 | 0.5671 | 0.5515 | +0.0156 |
| ROC-AUC | 0.8542 | 0.8474 | +0.0068 |
| PR-AUC | 0.6022 | 0.5829 | +0.0193 |

### 14.2 Final Test Comparison

| Metric | XGBoost | Baseline | Difference |
|--------|---------|----------|------------|
| Macro F1 | 0.7499 | 0.7471 | +0.0028 |
| Suspicious Recall | 0.5411 | 0.5206 | +0.0206 |
| Suspicious Precision | 0.5760 | 0.5864 | -0.0104 |
| Suspicious F1 | 0.5580 | 0.5515 | +0.0065 |
| ROC-AUC | 0.8559 | 0.8474 | +0.0085 |
| PR-AUC | 0.5892 | 0.5829 | +0.0063 |
| FPR | 0.0543 | 0.0465 | +0.0078 |

### 14.3 Independent Comparison

| Metric | XGBoost | Baseline | Difference |
|--------|---------|----------|------------|
| Macro F1 | 0.7241 | 0.7245 | -0.0004 |
| Suspicious Recall | 0.5592 | 0.5458 | +0.0133 |
| Suspicious Precision | 0.4852 | 0.4940 | -0.0088 |
| Suspicious F1 | 0.5196 | 0.5186 | +0.0009 |
| ROC-AUC | 0.8331 | 0.8297 | +0.0034 |
| PR-AUC | 0.5499 | 0.5590 | -0.0091 |
| FPR | 0.0809 | 0.0762 | +0.0047 |

### 14.4 Comparison Interpretation

**Key Observations:**
1. **Validation:** XGBoost shows clear improvement (+0.0181 Macro F1), as expected from model selection
2. **Final Test:** Marginal improvement (+0.0028 Macro F1), much smaller than validation improvement
3. **Independent:** Essentially equivalent performance (-0.0004 Macro F1), no meaningful difference
4. **Generalization Gap:** The validation-to-independent performance gap is larger for XGBoost (0.7544 → 0.7241 = 0.0303) than for baseline (0.7363 → 0.7245 = 0.0118), suggesting potential overfitting
5. **Precision Trade-off:** XGBoost achieves higher recall but lower precision, increasing false positive rate
6. **PR-AUC:** XGBoost PR-AUC is lower on independent (0.5499 vs 0.5590), indicating worse precision-recall trade-off on unseen data

**Conclusion:** The small Final Test improvements do not generalize to the Independent population. The baseline Gradient Boosting model generalizes better and maintains a better precision-recall trade-off.

---

## 15. Generalization Analysis

**Performance Trajectory:**

**XGBoost:**
- Validation Macro F1: 0.7544
- Final Test Macro F1: 0.7499 (−0.5%)
- Independent Macro F1: 0.7241 (−3.0% from validation, −3.4% from final test)

**Baseline Gradient Boosting:**
- Validation Macro F1: 0.7363
- Final Test Macro F1: 0.7471 (+1.5%)
- Independent Macro F1: 0.7245 (−1.6% from validation, −2.3% from final test)

**Generalization Assessment:**
- XGBoost shows larger validation-to-independent degradation (3.0% vs 1.6% baseline)
- XGBoost's validation performance advantage (0.7544 vs 0.7363) disappears on independent data (0.7241 vs 0.7245)
- Baseline maintains more stable performance across datasets
- XGBoost may be slightly overfit to the validation set during hyperparameter search

**Preferred Model:** Baseline Gradient Boosting demonstrates better generalization characteristics.

---

## 16. Leakage Audit

**Audit Results:**
- ✅ Only Stage 13 matrices used
- ✅ Target not included in X
- ✅ Metadata not included in X
- ✅ Identifiers not included in X
- ✅ Scenario labels not included in X
- ✅ Risk/rule outputs not included in X
- ✅ Final test not used for tuning
- ✅ Independent data not used for tuning
- ✅ Threshold selected only from validation
- ✅ Preprocessing fit only on training data
- ✅ No future information entered training features
- ✅ No Stage 11 raw data modified
- ✅ No Stage 13 feature matrix modified

**Leakage Audit Status:** PASS — No violations detected.

---

## 17. Data Integrity Verification

**Matrix Checksums (SHA-256, first 16 hex chars):**
- X_train: 3110727538819d68
- X_val: 8939ed0bbc5d7549
- X_test: 1e5cd7765cb79761
- X_independent: 3267ec39b24edfca
- y_train: 5384b07384815726
- y_val: ed42ebba0b8e7033
- y_test: 40b8c15730c6b5cd
- y_independent: 64508775998cef03

**Checksum Verification:** All checksums match Stage 14 correction results, confirming no data modification occurred.

**Data Integrity Status:** PASS — Stage 11 dataset, Stage 13 matrices, and all data remain unchanged.

---

## 18. Reproducibility Information

**XGBoost Version:** 3.4.1  
**Python Version:** 3.14  
**Operating Environment:** Windows  
**Random Seed:** 42  
**Selected Hyperparameters:** Documented in Section 6  
**Selected Threshold:** 0.75  
**Feature List:** 30 features from Stage 13 (locked order)  
**Dataset Version:** ecocash_aml_synthetic_100k_v1  
**Matrix Shapes:** Documented in Section 2  
**Class Distributions:** Documented in Section 2  
**Training Duration:** 81.6 seconds  
**Validation Procedure:** Macro F1 optimization on validation set  
**Model Selection Procedure:** Best validation Macro F1  
**Artifact Paths:** ml/stage15/stage15_xgboost_model.json, ml/stage15/stage15_xgboost_results.json  
**Data Checksums:** Documented in Section 17

**Reproducibility Status:** PASS — All parameters and procedures documented for full reproducibility.

---

## 19. Model Artifacts

**Saved Artifacts:**
- ml/stage15/stage15_xgboost_results.json
- ml/stage15/stage15_xgboost_model.json

**Frozen XGBoost Model Components:**
- Model: XGBoost Booster
- Threshold: 0.75
- Feature Names: 30 features in locked order
- Hyperparameters: Documented in Section 6
- Random Seed: 42

**Baseline Preservation:** Stage 14 Gradient Boosting model (ml/stage14/stage14_frozen_model.pkl) remains unchanged and is the official frozen baseline.

---

## 20. Research Interpretation

**Does XGBoost provide meaningful improvement over Gradient Boosting?**  
**Answer:** NO — XGBoost shows marginal improvements on Final Test but performs essentially equivalently on Independent evaluation. The small performance differences do not justify replacing the existing baseline.

**Does XGBoost generalize better than the baseline?**  
**Answer:** NO — XGBoost shows larger validation-to-independent degradation (3.0% vs 1.6% baseline), suggesting the baseline generalizes better.

**Are the performance differences statistically meaningful?**  
**Answer:** NO — The differences are very small (Macro F1: +0.0028 on Final Test, -0.0004 on Independent) and likely within experimental variance. The validation advantage (0.7544 vs 0.7363) does not generalize.

**Does XGBoost provide better domain detection?**  
**Answer:** MIXED — XGBoost improves agent domain detection (+6-8% recall) but slightly degrades network domain detection (-0.7-0.8% recall). Overall domain performance is essentially equivalent.

**Is the higher threshold (0.75 vs 0.35) beneficial?**  
**Answer:** INCONCLUSIVE — The higher threshold achieves higher recall but lower precision, increasing false positive rate. The precision-recall trade-off is worse on independent data (PR-AUC: 0.5499 vs 0.5590 baseline).

**Should XGBoost replace the baseline?**  
**Answer:** NO — The baseline Gradient Boosting model remains preferable due to its simplicity, equivalent generalization, and better precision-recall trade-off on unseen data.

---

## 21. Limitations

**1. Synthetic Data:** The dataset is synthetic and does not represent actual EcoCash customer behaviour or real money laundering patterns.

**2. Research Scope:** Limited to structuring, network, and agent behaviour domains. Does not include cross-border, cryptocurrency, merchant, or KYC-replacement features.

**3. Decision Support Only:** The model identifies suspicious patterns for analyst investigation; it does not prove that money laundering occurred.

**4. Threshold Sensitivity:** Performance is sensitive to the selected threshold (0.75 for XGBoost vs 0.35 for baseline), making direct comparison complex.

**5. Search Space Limitation:** The hyperparameter search was limited to 50 random combinations; a more extensive search might yield different results.

**6. Single Experiment:** This is a single experimental run; multiple runs with different random seeds would provide more robust comparison.

---

## 22. Final Recommendation

**DECISION: XGBOOST NOT SUPERIOR**

**Rationale:**
1. **Generalization:** XGBoost shows larger validation-to-independent degradation (3.0% vs 1.6% baseline)
2. **Independent Performance:** Essentially equivalent Macro F1 (0.7241 vs 0.7245 baseline)
3. **Precision-Recall Trade-off:** Worse on independent data (PR-AUC: 0.5499 vs 0.5590 baseline)
4. **Complexity:** XGBoost adds complexity without meaningful performance gain
5. **Stability:** Baseline shows more stable performance across datasets

**Official Frozen Baseline:** The Stage 14 Gradient Boosting model remains the official frozen baseline for the EcoCash AML research project.

**Research Value:** The XGBoost experiment was valuable in confirming that the existing Gradient Boosting baseline is already well-optimized for this problem. The marginal improvements on validation data do not translate to meaningful gains on unseen populations.

**Next Steps:**
- Maintain Stage 14 Gradient Boosting as the official frozen baseline
- Consider feature engineering improvements rather than model architecture changes
- Focus on improving structuring scenario detection (25-31% recall across both models)
- Evaluate model integration into production application using the Stage 14 baseline

---

*Report generated as part of Stage 15 XGBoost challenger model experiment*
*Date: 2026-09-15*
*Dataset: ecocash_aml_synthetic_100k_v1*
*Feature Matrix: Stage 13 frozen 30-feature matrix*
*Baseline Model: Stage 14 Gradient Boosting*
*Challenger Model: Stage 15 XGBoost*
*Stage 15 Status: PASS*
*Final Decision: XGBOOST NOT SUPERIOR*
