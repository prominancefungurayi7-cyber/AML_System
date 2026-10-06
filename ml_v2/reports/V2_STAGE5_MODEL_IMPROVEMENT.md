# MODEL V2 — STAGE 5 FOCUSED MODEL IMPROVEMENT

**Decision: C — the current 30-feature representation appears to limit performance.** The strongest searched model reached Validation Macro F1 **0.5983** at threshold 0.50; the development targets were not substantially met. This is a development diagnosis, not proof of an intrinsic Bayes limit. A controlled feature improvement stage is justified before threshold optimization.

## Scope and method

Train and Validation only; fixed 30 Stage 3 features; threshold **0.50** throughout. Seed `20260921`. 72 configurations, 2224.5 seconds including evaluations and refits. Models: XGBoost, HistGradientBoosting, Gradient Boosting, a small strongly regularized Random Forest reference, and a limited Logistic Regression convergence check. Moderate positive weights were searched. No resampling or scenario metadata entered any classifier. XGBoost used raw features; other tree searches used the Stage 4 clipped path where specified; Logistic used robust scaling. All preprocessing was fitted on Train.

## Search outcome

| Rank | Name | Algorithm | Weight | Train Macro F1 | Validation Macro F1 | Suspicious precision | Recall | Suspicious F1 | PR-AUC | ROC-AUC | FPR |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | s5_gradient_boosting_060 | gradient_boosting | 4.0000 | 0.6652 | 0.5983 | 0.2813 | 0.3211 | 0.2999 | 0.2591 | 0.6914 | 0.1119 |
| 2 | s5_random_forest_067 | random_forest | 4.0000 | 0.7312 | 0.5969 | 0.2873 | 0.2972 | 0.2922 | 0.2507 | 0.6894 | 0.1005 |
| 3 | s5_xgboost_026 | xgboost | 4.0000 | 0.6427 | 0.5952 | 0.2706 | 0.3333 | 0.2987 | 0.2558 | 0.6922 | 0.1225 |
| 4 | s5_hist_gradient_boosting_040 | hist_gradient_boosting | 4.0000 | 0.6854 | 0.5936 | 0.2756 | 0.3061 | 0.2901 | 0.2585 | 0.6899 | 0.1097 |
| 5 | s5_logistic_regression_071 | logistic_regression | 3.0000 | 0.5855 | 0.5762 | 0.3038 | 0.1922 | 0.2355 | 0.2321 | 0.6698 | 0.0601 |

The complete 72-row search, exact parameters, fit times, warnings, and metrics are in `stage5_search_results.json`. The table is the Pareto-aware reporting shortlist: the strongest eligible model per family plus additional candidates with useful recall and controlled FPR. Candidate artifacts are development artifacts only.

### Development targets

| Target | Goal | Best Macro F1 model | Met |
|---|---|---|---|
| macro_f1 | 0.8000 | 0.5983 | no |
| suspicious_recall | 0.7000 | 0.3211 | no |
| suspicious_f1 | 0.6500 | 0.2999 | no |
| average_precision | 0.6500 | 0.2591 | no |
| false_positive_rate | ≤0.0800 | 0.1119 | no |

The domain targets are evaluated for each shortlisted model below. A higher single metric is not interpreted as success when recall, hard-negative FPR, or Train/Validation gaps worsen.

## Generalization

| Name | Train/Val suspicious F1 | Gap | Train/Val recall | Gap | Train/Val ROC-AUC | Gap | Train/Val PR-AUC | Gap |
|---|---|---|---|---|---|---|---|---|
| s5_gradient_boosting_060 | 0.4183/0.2999 | 0.1184 | 0.4576/0.3211 | 0.1365 | 0.7837/0.6914 | 0.0923 | 0.4074/0.2591 | 0.1483 |
| s5_logistic_regression_071 | 0.2512/0.2355 | 0.0157 | 0.2025/0.1922 | 0.0103 | 0.7002/0.6698 | 0.0303 | 0.2522/0.2321 | 0.0202 |
| s5_random_forest_067 | 0.5294/0.2922 | 0.2372 | 0.5500/0.2972 | 0.2528 | 0.8499/0.6894 | 0.1605 | 0.5714/0.2507 | 0.3208 |
| s5_xgboost_026 | 0.3803/0.2987 | 0.0816 | 0.4207/0.3333 | 0.0874 | 0.7580/0.6922 | 0.0658 | 0.3452/0.2558 | 0.0894 |
| s5_hist_gradient_boosting_040 | 0.4537/0.2901 | 0.1636 | 0.4981/0.3061 | 0.1919 | 0.8126/0.6899 | 0.1226 | 0.4712/0.2585 | 0.2126 |

Macro F1 Train/Validation values and gaps are in the search table and `stage5_generalization.json`.

## Validation domain recall

| Name | Structuring (goal .60) | Network (goal .70) | Agent (goal .65) |
|---|---|---|---|
| s5_gradient_boosting_060 | 0.5283 | 0.2033 | 0.2317 |
| s5_hist_gradient_boosting_040 | 0.4967 | 0.1933 | 0.2283 |
| s5_logistic_regression_071 | 0.3533 | 0.0633 | 0.1600 |
| s5_random_forest_067 | 0.4917 | 0.1900 | 0.2100 |
| s5_xgboost_026 | 0.5367 | 0.2033 | 0.2600 |

### Scenario-family recall

| Name | agent_flow_imbalance | agent_temporal_burst | agent_wallet_concentration | agent_wallet_growth | distributed_same_day_fragmentation | many_to_one_collection | one_to_many_dispersion | reciprocal_relationship_cycle | similar_amount_repetition | variable_fragment_burst | variable_near_threshold_history | wallet_pass_through |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s5_gradient_boosting_060 | 0.0467 | 0.5867 | 0.0867 | 0.2067 | 0.6133 | 0.0800 | 0.2200 | 0.0200 | 0.4000 | 0.7400 | 0.3600 | 0.4933 |
| s5_hist_gradient_boosting_040 | 0.0467 | 0.5467 | 0.0800 | 0.2400 | 0.6333 | 0.0733 | 0.2067 | 0.0133 | 0.3267 | 0.6933 | 0.3333 | 0.4800 |
| s5_logistic_regression_071 | 0.0133 | 0.4267 | 0.0533 | 0.1467 | 0.5867 | 0.0333 | 0.0400 | 0.0067 | 0.3333 | 0.4400 | 0.0533 | 0.1733 |
| s5_random_forest_067 | 0.0400 | 0.4467 | 0.1467 | 0.2067 | 0.6200 | 0.0733 | 0.2067 | 0.0267 | 0.3533 | 0.6533 | 0.3400 | 0.4533 |
| s5_xgboost_026 | 0.1000 | 0.5667 | 0.1400 | 0.2333 | 0.6333 | 0.0867 | 0.2200 | 0.0200 | 0.4133 | 0.7467 | 0.3533 | 0.4867 |

The 12 family names follow the frozen Stage 2 scenario manifest. N3 is `reciprocal_relationship_cycle`; A1, A2 and A4 are `agent_wallet_growth`, `agent_wallet_concentration` and `agent_flow_imbalance`.

## Validation normal false-positive rates

| Name | H1 | H2 | H3 | H4 | H5 | H6 | H7 | H8 | routine |
|---|---|---|---|---|---|---|---|---|---|
| s5_gradient_boosting_060 | 0.4303 | 0.1345 | 0.1939 | 0.0691 | 0.1867 | 0.0715 | 0.3321 | 0.1515 | 0.0276 |
| s5_hist_gradient_boosting_040 | 0.3939 | 0.1358 | 0.1855 | 0.0703 | 0.1867 | 0.0764 | 0.3418 | 0.1236 | 0.0302 |
| s5_logistic_regression_071 | 0.2921 | 0.1042 | 0.0545 | 0.0206 | 0.0655 | 0.0242 | 0.2339 | 0.0703 | 0.0120 |
| s5_random_forest_067 | 0.4061 | 0.1176 | 0.1576 | 0.0594 | 0.1697 | 0.0703 | 0.2582 | 0.1370 | 0.0291 |
| s5_xgboost_026 | 0.4715 | 0.1661 | 0.2048 | 0.0776 | 0.2073 | 0.0764 | 0.3370 | 0.1576 | 0.0327 |

H1 and H7 remain explicit hard-negative diagnostics. Counts and false positives for every slice are in `stage5_hard_negative_results.json`.

## Feature-domain diagnostic

| Feature group | Count | Validation Macro F1 | Suspicious recall | PR-AUC | FPR |
|---|---|---|---|---|---|
| agent | 14 | 0.5445 | 0.1339 | 0.1791 | 0.0560 |
| all_30 | 30 | 0.5884 | 0.2100 | 0.2534 | 0.0575 |
| network | 10 | 0.4916 | 0.0289 | 0.1518 | 0.0126 |
| structuring | 6 | 0.5306 | 0.0928 | 0.1768 | 0.0353 |

Each row used the same moderately weighted HistGradientBoosting specification fitted independently on Train. Single-group models are diagnostic ablations, not proposed production models. Their poorer ranking and classification performance shows that signal is distributed across groups; the all-feature result remains far below the targets. This supports a representation limitation but cannot separate feature insufficiency from synthetic class overlap conclusively.

## Reproducibility and convergence

| Configuration | Same-seed max probability difference | Same-seed predictions identical | Additional-seed Macro F1 |
|---|---|---|---|
| s5_gradient_boosting_060 | 0.0000 | True | 0.5944, 0.5937 |
| s5_random_forest_067 | 0.0000 | True | 0.5972, 0.5979 |

Logistic Regression diagnostic: s5_logistic_regression_070 weight 1: converged; s5_logistic_regression_071 weight 3: converged.

## Decision and protection

Best Validation Macro F1 configuration: `s5_gradient_boosting_060` with parameters `{"learning_rate": 0.07, "max_depth": 3, "min_samples_leaf": 10, "min_samples_split": 20, "n_estimators": 180, "subsample": 0.8}` and positive weight 4.0000. Stage 4 primary was 0.5814 Macro F1 with 0.2061 recall and 0.0634 FPR. Stage 5 improved model discrimination only to the extent measured above. The shortlist records alternatives so a small Macro F1 edge cannot hide weak suspicious recall or a large FPR.

Before/after SHA-256 comparison: **PASS**, 347 V1/application files and 37 V2 dataset/feature input files. No Final Test or Independent Evaluation data, labels, matrices, or features were accessed or constructed. No V1 or application file changed. No threshold other than 0.50 was evaluated. No final V2 model was frozen or integrated.

The development targets remain far enough away that threshold tuning alone is not a justified next stage. Recommend a separately approved, controlled feature improvement stage using Train/Validation, with attention to reciprocal cycles, weak agent families, and H1/H7 ambiguity. Preserve this Stage 5 result as the fixed-feature baseline.

V2 STAGE 5 COMPLETE — WAITING FOR APPROVAL.
