# MODEL V3 - STAGE 11 BASELINE MODEL TRAINING AND VALIDATION COMPARISON

**Technical execution: PASS. Quality decision: A - STRONG BASELINE.**

The development reference is **`s11_09_hist_gradient_boosting`**, with Validation Macro F1 **0.9521**, suspicious recall **0.9349**, suspicious F1 **0.9364**, Average Precision **0.9772**, ROC-AUC **0.9888**, and FPR **0.0315** at threshold **0.50**. These are development results on frozen synthetic targets, not a final model or evidence of real-world AML effectiveness.

This is the **single consolidated Stage 11 report**, covering scope, all candidates, preprocessing, complete shortlist metrics, domains/families, normal false positives, generalization, score distributions, importance, protection and next decision. Machine-readable files are supporting evidence.

## 1. Authorized data and experiment boundaries

Only corrected `v3_stage10a_features_1` matrices from `features/development/stage10a/train/` and `validation/` were used for model inputs. All 32 names and their order were checked against the frozen contract and saved matrix hashes. Superseded Stage 10 matrices were not loaded as model data. Their bytes were hashed only by the pre-existing protection allowlist.

| Partition | Rows | Features | Target 0 | Target 1 |
|---|---:|---:|---:|---:|
| Train | 60000 | 32 | 39781 | 20219 |
| Validation | 15000 | 32 | 9945 | 5055 |

Row IDs remain outside X. Model fit and preprocessing receive only the 32 numeric columns and Train targets. A preliminary metadata schema/support check preceded training; diagnostic metadata did not influence preprocessing or the fixed candidate grid. The runner joins Validation family/provenance/recipe metadata for slice metrics after every candidate's predictions exist. Labels remain the frozen `decision_point_target`; raw transactions, predicates and features were not regenerated or edited.

No Final Test or Independent Evaluation directory was enumerated or data opened. Only explicit public commitment certificates were hashed. No resampling, SMOTE, Validation refit, calibration or threshold optimization occurred. Every reported classification uses `probability >= 0.50` as suspicious class 1. Ranking metrics use continuous scores.

## 2. Fixed search design and execution

The search plan and source digests were saved before the first fit. The first five fits are one simple unweighted baseline per available model family; the remaining fits are prespecified comparisons, with no adaptive search expansion. The later Stage 11 instruction explicitly requests five model families, so this supersedes the earlier proposal's three-family suggestion while retaining its maximum of 36 configurations.

| Property | Recorded value |
| --- | --- |
| Random seed | 20260928 |
| Threshold | 0.5000 |
| Configurations | 30 |
| Model fits (no extra refits) | 30 |
| Wall-clock experiment seconds (includes interruption) | 783.4331 |
| Sum of model fit seconds | 388.0891 |
| Plan saved UTC | 2026-09-28T16:46:21.383363+00:00 |
| Python executable | C:\Users\PROMINENT\AppData\Local\Programs\Python\Python314\python.exe |
| Library versions | {"numpy": "2.4.3", "pandas": "3.0.1", "sklearn": "1.9.0", "xgboost": "3.4.1"} |
| XGBoost availability | Installed and used; no package/environment changes |
| Train positive rate | 0.3370 |
| Validation positive rate | 0.3370 |

No weighting gives unit sample weights. Moderate weighting gives class 1 weight 1.5 and class 0 weight 1. For Logistic/Gradient/HistGradient models the balanced sample weights are N/(2N_class), fitted from Train class counts. Random Forest uses `balanced_subsample` for its balanced variant. XGBoost uses `scale_pos_weight=39781/20219` for its balanced variant, 1.5 for moderate, 1 for none. Balanced XGBoost uses a positive-to-negative ratio, not the same absolute normalization as sklearn sample weights. No class weights are estimated from Validation.

| Initial family | Preprocessing | Parameters excluding common random seed |
| --- | --- | --- |
| logistic | robust | {"C": 1.0, "max_iter": 4000, "solver": "lbfgs", "tol": 1e-05} |
| random_forest | raw | {"max_depth": 12, "max_features": 0.7, "min_samples_leaf": 5, "n_estimators": 200, "n_jobs": 2} |
| gradient_boosting | raw | {"learning_rate": 0.07, "max_depth": 3, "min_samples_leaf": 10, "n_estimators": 150, "subsample": 1.0} |
| hist_gradient_boosting | raw | {"early_stopping": false, "l2_regularization": 1.0, "learning_rate": 0.07, "max_depth": 6, "max_iter": 200, "max_leaf_nodes": 31, "min_samples_leaf": 20} |
| xgboost | raw | {"colsample_bytree": 0.8, "eval_metric": "logloss", "learning_rate": 0.07, "max_depth": 4, "min_child_weight": 5, "n_estimators": 200, "n_jobs": 2, "reg_alpha": 0.05, "reg_lambda": 3.0, "subsample": 0.8, "tree_method": "hist"} |

The three weight comparisons hold each family baseline configuration and preprocessing fixed. Tree families then compare clipped and imputed inputs against raw at unit weights, followed by one prespecified capacity/regularization variant. Logistic Regression compares C=0.1/1/10 and robust-scaled sentinel preservation against robust-scaled imputation.

| Candidate | Phase | Preprocessing | Weight | Exact requested estimator parameters |
| --- | --- | --- | --- | --- |
| s11_01_logistic | initial baseline | robust | none | {"C": 1.0, "max_iter": 4000, "solver": "lbfgs", "tol": 1e-05} |
| s11_02_random_forest | initial baseline | raw | none | {"max_depth": 12, "max_features": 0.7, "min_samples_leaf": 5, "n_estimators": 200, "n_jobs": 2} |
| s11_03_gradient_boosting | initial baseline | raw | none | {"learning_rate": 0.07, "max_depth": 3, "min_samples_leaf": 10, "n_estimators": 150, "subsample": 1.0} |
| s11_04_hist_gradient_boosting | initial baseline | raw | none | {"early_stopping": false, "l2_regularization": 1.0, "learning_rate": 0.07, "max_depth": 6, "max_iter": 200, "max_leaf_nodes": 31, "min_samples_leaf": 20} |
| s11_05_xgboost | initial baseline | raw | none | {"colsample_bytree": 0.8, "eval_metric": "logloss", "learning_rate": 0.07, "max_depth": 4, "min_child_weight": 5, "n_estimators": 200, "n_jobs": 2, "reg_alpha": 0.05, "reg_lambda": 3.0, "subsample": 0.8, "tree_method": "hist"} |
| s11_06_logistic | compact comparison | robust | moderate | {"C": 1.0, "max_iter": 4000, "solver": "lbfgs", "tol": 1e-05} |
| s11_07_random_forest | compact comparison | raw | moderate | {"max_depth": 12, "max_features": 0.7, "min_samples_leaf": 5, "n_estimators": 200, "n_jobs": 2} |
| s11_08_gradient_boosting | compact comparison | raw | moderate | {"learning_rate": 0.07, "max_depth": 3, "min_samples_leaf": 10, "n_estimators": 150, "subsample": 1.0} |
| s11_09_hist_gradient_boosting | compact comparison | raw | moderate | {"early_stopping": false, "l2_regularization": 1.0, "learning_rate": 0.07, "max_depth": 6, "max_iter": 200, "max_leaf_nodes": 31, "min_samples_leaf": 20} |
| s11_10_xgboost | compact comparison | raw | moderate | {"colsample_bytree": 0.8, "eval_metric": "logloss", "learning_rate": 0.07, "max_depth": 4, "min_child_weight": 5, "n_estimators": 200, "n_jobs": 2, "reg_alpha": 0.05, "reg_lambda": 3.0, "subsample": 0.8, "tree_method": "hist"} |
| s11_11_logistic | compact comparison | robust | balanced | {"C": 1.0, "max_iter": 4000, "solver": "lbfgs", "tol": 1e-05} |
| s11_12_random_forest | compact comparison | raw | balanced | {"max_depth": 12, "max_features": 0.7, "min_samples_leaf": 5, "n_estimators": 200, "n_jobs": 2} |
| s11_13_gradient_boosting | compact comparison | raw | balanced | {"learning_rate": 0.07, "max_depth": 3, "min_samples_leaf": 10, "n_estimators": 150, "subsample": 1.0} |
| s11_14_hist_gradient_boosting | compact comparison | raw | balanced | {"early_stopping": false, "l2_regularization": 1.0, "learning_rate": 0.07, "max_depth": 6, "max_iter": 200, "max_leaf_nodes": 31, "min_samples_leaf": 20} |
| s11_15_xgboost | compact comparison | raw | balanced | {"colsample_bytree": 0.8, "eval_metric": "logloss", "learning_rate": 0.07, "max_depth": 4, "min_child_weight": 5, "n_estimators": 200, "n_jobs": 2, "reg_alpha": 0.05, "reg_lambda": 3.0, "subsample": 0.8, "tree_method": "hist"} |
| s11_16_logistic | compact comparison | robust | none | {"C": 0.1, "max_iter": 4000, "solver": "lbfgs", "tol": 1e-05} |
| s11_17_random_forest | compact comparison | clipped | none | {"max_depth": 12, "max_features": 0.7, "min_samples_leaf": 5, "n_estimators": 200, "n_jobs": 2} |
| s11_18_gradient_boosting | compact comparison | clipped | none | {"learning_rate": 0.07, "max_depth": 3, "min_samples_leaf": 10, "n_estimators": 150, "subsample": 1.0} |
| s11_19_hist_gradient_boosting | compact comparison | clipped | none | {"early_stopping": false, "l2_regularization": 1.0, "learning_rate": 0.07, "max_depth": 6, "max_iter": 200, "max_leaf_nodes": 31, "min_samples_leaf": 20} |
| s11_20_xgboost | compact comparison | clipped | none | {"colsample_bytree": 0.8, "eval_metric": "logloss", "learning_rate": 0.07, "max_depth": 4, "min_child_weight": 5, "n_estimators": 200, "n_jobs": 2, "reg_alpha": 0.05, "reg_lambda": 3.0, "subsample": 0.8, "tree_method": "hist"} |
| s11_21_logistic | compact comparison | robust | none | {"C": 10.0, "max_iter": 4000, "solver": "lbfgs", "tol": 1e-05} |
| s11_22_random_forest | compact comparison | imputed | none | {"max_depth": 12, "max_features": 0.7, "min_samples_leaf": 5, "n_estimators": 200, "n_jobs": 2} |
| s11_23_gradient_boosting | compact comparison | imputed | none | {"learning_rate": 0.07, "max_depth": 3, "min_samples_leaf": 10, "n_estimators": 150, "subsample": 1.0} |
| s11_24_hist_gradient_boosting | compact comparison | imputed | none | {"early_stopping": false, "l2_regularization": 1.0, "learning_rate": 0.07, "max_depth": 6, "max_iter": 200, "max_leaf_nodes": 31, "min_samples_leaf": 20} |
| s11_25_xgboost | compact comparison | imputed | none | {"colsample_bytree": 0.8, "eval_metric": "logloss", "learning_rate": 0.07, "max_depth": 4, "min_child_weight": 5, "n_estimators": 200, "n_jobs": 2, "reg_alpha": 0.05, "reg_lambda": 3.0, "subsample": 0.8, "tree_method": "hist"} |
| s11_26_logistic | compact comparison | robust_sentinel | none | {"C": 1.0, "max_iter": 4000, "solver": "lbfgs", "tol": 1e-05} |
| s11_27_random_forest | compact comparison | raw | none | {"max_depth": 16, "max_features": 0.7, "min_samples_leaf": 10, "n_estimators": 250, "n_jobs": 2} |
| s11_28_gradient_boosting | compact comparison | raw | none | {"learning_rate": 0.05, "max_depth": 2, "min_samples_leaf": 10, "n_estimators": 200, "subsample": 1.0} |
| s11_29_hist_gradient_boosting | compact comparison | raw | none | {"early_stopping": false, "l2_regularization": 3.0, "learning_rate": 0.07, "max_depth": 5, "max_iter": 250, "max_leaf_nodes": 15, "min_samples_leaf": 20} |
| s11_30_xgboost | compact comparison | raw | none | {"colsample_bytree": 0.8, "eval_metric": "logloss", "learning_rate": 0.07, "max_depth": 3, "min_child_weight": 10, "n_estimators": 250, "n_jobs": 2, "reg_alpha": 0.05, "reg_lambda": 5.0, "subsample": 0.8, "tree_method": "hist"} |


### Execution recovery

After the fifth fit, strict JSON serialization rejected XGBoost's default `missing=NaN` parameter. The fitted model and scores had already been saved. The initial partial checkpoint was preserved, its completed records recovered, and the fifth record reconstructed from saved scores and timing fields. Logging now records nonfinite estimator defaults as text and writes complete checkpoints atomically. The same fixed grid resumed at configuration 6, without refitting the first five models or changing model/preprocessing/threshold choices. The fifth fit's original warning capture was not retained and is explicitly marked unavailable. Source hashes and the reason are in `stage11_execution_amendment.json`; the original search plan remains preserved.

## 3. Train-fitted preprocessing and missing-value contract

Every estimator receives exactly 32 columns. No missing indicators were added: the explicit Stage 11 input-count constraint takes precedence over the optional indicator comparison. The `imputed` and `robust` variants use Train observed medians; their lost missingness information is a limitation evaluated alongside sentinel-preserving variants. Five deterministic representations were fitted on Train and shared by the corresponding candidates; their parameters were deterministically recomputed during process recovery. Transforming Validation never fits or updates parameters.

| Variant | Exact transformation |
| --- | --- |
| raw | Unscaled Stage 10A values; preserve each documented marker. |
| clipped | Preserve markers; clip only current_amount_usd, wallet_value_24h_inclusive, current_return_amount_ratio, wallet_observed_onward_funding_share_24h, agent_wallet_growth_ratio_7d to Train observed 0.5th/99.5th percentiles. |
| imputed | Replace only documented per-column markers with Train observed medians; no scaling or clipping. |
| robust | Same marker-aware median imputation plus the five continuous-feature clipping limits; RobustScaler with Train median and IQR. |
| robust_sentinel | Preserve markers before the same clipping and robust scaling; markers become deterministic scaled values. |

The five clipping candidates have unbounded monetary/ratio scales and heavy tails in Stage 10A. Bounded indicators, cash skews, shares, path length, coverage and counts are never clipped. Robust scaling of those quantities for the linear model changes units while preserving their values relative to the Train-fitted transform. No log transform is used. Zero IQR uses the installed RobustScaler scale fallback.

The preprocessing regression test exercised all five variants, preserving legitimate -1 skews/changes, distinguishing -3 change markers, retaining shape, excluding markers from quantiles, and proving an extreme Validation transform does not change fitted parameter records.

| Feature | Missing marker | Raw/clipped treatment | Imputed/robust treatment | Train observed median | Clipping limits | Robust center | Robust scale |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `current_amount_usd` | none | observed value | observed value | 189.8300 | [2.0, 24458.73185] | 189.8300 | 2636.1750 |
| `current_is_cash_in` | none | observed value | observed value | 0.0000 | undefined (zero support) | 0.0000 | 1.0000 |
| `current_is_cash_out` | none | observed value | observed value | 0.0000 | undefined (zero support) | 0.0000 | 1.0000 |
| `wallet_count_1h_inclusive` | none | observed value | observed value | 1.0000 | undefined (zero support) | 1.0000 | 1.0000 |
| `wallet_value_24h_inclusive` | none | observed value | observed value | 1105.5700 | [2.95, 99402.45929999981] | 1105.5700 | 15064.8575 |
| `wallet_count_utc_day_inclusive` | none | observed value | observed value | 1.0000 | undefined (zero support) | 1.0000 | 1.0000 |
| `wallet_active_hours_utc_day` | none | observed value | observed value | 1.0000 | undefined (zero support) | 1.0000 | 1.0000 |
| `wallet_current_amount_cluster_share_7d` | none | observed value | observed value | 0.2500 | undefined (zero support) | 0.2500 | 0.1905 |
| `wallet_band_share_7d_inclusive` | none | observed value | observed value | 0.0000 | undefined (zero support) | 0.0000 | 1.0000 |
| `wallet_count_acceleration_1h` | -1 | preserve | Train median | 1.0000 | undefined (zero support) | 1.0000 | 1.0000 |
| `receiver_unique_sources_24h_inclusive` | none | observed value | observed value | 1.0000 | undefined (zero support) | 1.0000 | 1.0000 |
| `receiver_inflow_count_24h_inclusive` | none | observed value | observed value | 1.0000 | undefined (zero support) | 1.0000 | 1.0000 |
| `receiver_inflow_acceleration_24h` | -1 | preserve | Train median | 1.0000 | undefined (zero support) | 1.0000 | 1.0000 |
| `sender_unique_destinations_24h_inclusive` | none | observed value | observed value | 1.0000 | undefined (zero support) | 1.0000 | 1.0000 |
| `sender_outflow_count_24h_inclusive` | none | observed value | observed value | 1.0000 | undefined (zero support) | 1.0000 | 2.0000 |
| `sender_outflow_acceleration_24h` | -1 | preserve | Train median | 1.0000 | undefined (zero support) | 1.0000 | 1.0000 |
| `current_return_path_length` | none | observed value | observed value | 0.0000 | undefined (zero support) | 0.0000 | 1.0000 |
| `current_return_amount_ratio` | -1 | preserve | Train median | 0.7217 | [0.00021029916180224155, 4030.198550113081] | 0.7217 | 1.0000 |
| `wallet_observed_onward_funding_share_24h` | -1 | preserve | Train median | 0.0000 | [0.0, 2228.4903388158023] | 0.0000 | 1.0000 |
| `wallet_prior_funding_age_hours` | -1 | preserve | Train median | 11.7699 | undefined (zero support) | 11.7699 | 1.0000 |
| `agent_service_count_1h_inclusive` | none | observed value | observed value | 1.0000 | undefined (zero support) | 1.0000 | 1.0000 |
| `agent_service_acceleration_1h` | -1 | preserve | Train median | 1.0000 | undefined (zero support) | 1.0000 | 1.0000 |
| `agent_wallet_growth_ratio_7d` | -1 | preserve | Train median | 1.1538 | [0.27586206896551724, 6.571428571428571] | 1.1538 | 0.2673 |
| `agent_new_wallet_share_7d` | -1 | preserve | Train median | 0.8750 | undefined (zero support) | 0.8750 | 0.0481 |
| `agent_top2_count_share_24h` | none | observed value | observed value | 0.5000 | undefined (zero support) | 0.5000 | 0.6462 |
| `agent_top2_share_change_24h` | -3 | preserve | Train median | 0.4470 | undefined (zero support) | 0.4470 | 0.1525 |
| `agent_cash_value_skew_24h` | none | observed value | observed value | 0.0000 | undefined (zero support) | 0.0000 | 1.4793 |
| `agent_cash_count_skew_24h` | none | observed value | observed value | 0.0000 | undefined (zero support) | 0.0000 | 0.5333 |
| `agent_cash_value_skew_change` | -3 | preserve | Train median | -0.0533 | undefined (zero support) | -0.0533 | 0.7345 |
| `wallet_history_coverage_days` | none | observed value | observed value | 28.0000 | undefined (zero support) | 28.0000 | 1.0000 |
| `receiver_history_coverage_days` | none | observed value | observed value | 28.0000 | undefined (zero support) | 28.0000 | 1.0000 |
| `agent_history_coverage_days` | none | observed value | observed value | 28.0000 | undefined (zero support) | 28.0000 | 24.1091 |

Exact raw, clipped, imputed and sentinel-scaled parameter records, including every Train missing count, are in `stage11_preprocessing.json`. All five transformations retain ordered names.

## 4. All candidate results at threshold 0.50

Sorted by Validation Macro F1. Fit time excludes score evaluation and artifact serialization. All configurations and available warnings are retained, including any nonconverged model. Convergence warnings exclude a candidate from selection. For fixed-round tree models, the convergence field denotes completed training without a captured convergence warning; it does not certify an optimization optimum. The recovered XGBoost baseline warning log is unavailable as noted above.

| Candidate | Prep | Weight | Train Macro F1 | Val Macro F1 | Val precision 1 | Val recall 1 | Val F1 1 | Val AP | Val ROC-AUC | Val FPR | Fit seconds | Converged |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s11_09_hist_gradient_boosting | raw | moderate | 0.9695 | 0.9521 | 0.9379 | 0.9349 | 0.9364 | 0.9772 | 0.9888 | 0.0315 | 4.9370 | True |
| s11_29_hist_gradient_boosting | raw | none | 0.9617 | 0.9499 | 0.9487 | 0.9179 | 0.9330 | 0.9751 | 0.9875 | 0.0252 | 1.8574 | True |
| s11_04_hist_gradient_boosting | raw | none | 0.9674 | 0.9496 | 0.9446 | 0.9213 | 0.9328 | 0.9805 | 0.9895 | 0.0275 | 1.9136 | True |
| s11_19_hist_gradient_boosting | clipped | none | 0.9679 | 0.9496 | 0.9446 | 0.9211 | 0.9327 | 0.9805 | 0.9895 | 0.0275 | 1.8863 | True |
| s11_24_hist_gradient_boosting | imputed | none | 0.9657 | 0.9491 | 0.9491 | 0.9153 | 0.9319 | 0.9801 | 0.9894 | 0.0249 | 2.1446 | True |
| s11_14_hist_gradient_boosting | raw | balanced | 0.9664 | 0.9489 | 0.9261 | 0.9391 | 0.9325 | 0.9805 | 0.9896 | 0.0381 | 5.0579 | True |
| s11_27_random_forest | raw | none | 0.9676 | 0.9464 | 0.9475 | 0.9098 | 0.9282 | 0.9827 | 0.9903 | 0.0256 | 38.9511 | True |
| s11_15_xgboost | raw | balanced | 0.9562 | 0.9456 | 0.9239 | 0.9321 | 0.9280 | 0.9771 | 0.9879 | 0.0390 | 1.4191 | True |
| s11_20_xgboost | clipped | none | 0.9536 | 0.9436 | 0.9467 | 0.9031 | 0.9244 | 0.9752 | 0.9872 | 0.0258 | 1.4274 | True |
| s11_10_xgboost | raw | moderate | 0.9549 | 0.9433 | 0.9329 | 0.9161 | 0.9244 | 0.9762 | 0.9876 | 0.0335 | 1.4174 | True |
| s11_05_xgboost | raw | none | 0.9531 | 0.9429 | 0.9453 | 0.9025 | 0.9234 | 0.9758 | 0.9875 | 0.0265 | 1.3902 | True |
| s11_25_xgboost | imputed | none | 0.9530 | 0.9418 | 0.9466 | 0.8983 | 0.9218 | 0.9725 | 0.9865 | 0.0257 | 1.5381 | True |
| s11_22_random_forest | imputed | none | 0.9550 | 0.9395 | 0.9528 | 0.8863 | 0.9183 | 0.9796 | 0.9879 | 0.0223 | 26.1419 | True |
| s11_07_random_forest | raw | moderate | 0.9601 | 0.9390 | 0.9354 | 0.9019 | 0.9183 | 0.9800 | 0.9882 | 0.0317 | 26.9455 | True |
| s11_30_xgboost | raw | none | 0.9462 | 0.9385 | 0.9428 | 0.8934 | 0.9174 | 0.9676 | 0.9844 | 0.0276 | 1.6790 | True |
| s11_08_gradient_boosting | raw | moderate | 0.9430 | 0.9382 | 0.9354 | 0.8999 | 0.9173 | 0.9749 | 0.9855 | 0.0316 | 24.1108 | True |
| s11_02_random_forest | raw | none | 0.9570 | 0.9382 | 0.9501 | 0.8855 | 0.9166 | 0.9797 | 0.9880 | 0.0236 | 27.0135 | True |
| s11_17_random_forest | clipped | none | 0.9570 | 0.9381 | 0.9497 | 0.8857 | 0.9166 | 0.9797 | 0.9880 | 0.0238 | 27.8898 | True |
| s11_13_gradient_boosting | raw | balanced | 0.9429 | 0.9371 | 0.9216 | 0.9112 | 0.9163 | 0.9731 | 0.9848 | 0.0394 | 24.7646 | True |
| s11_23_gradient_boosting | imputed | none | 0.9433 | 0.9362 | 0.9456 | 0.8845 | 0.9140 | 0.9751 | 0.9849 | 0.0258 | 24.1017 | True |
| s11_03_gradient_boosting | raw | none | 0.9429 | 0.9358 | 0.9448 | 0.8841 | 0.9134 | 0.9766 | 0.9861 | 0.0262 | 23.6397 | True |
| s11_18_gradient_boosting | clipped | none | 0.9429 | 0.9358 | 0.9448 | 0.8841 | 0.9134 | 0.9766 | 0.9861 | 0.0262 | 25.5037 | True |
| s11_12_random_forest | raw | balanced | 0.9564 | 0.9342 | 0.9037 | 0.9228 | 0.9132 | 0.9803 | 0.9883 | 0.0500 | 28.2010 | True |
| s11_28_gradient_boosting | raw | none | 0.9246 | 0.9181 | 0.9347 | 0.8473 | 0.8889 | 0.9514 | 0.9733 | 0.0301 | 22.2553 | True |
| s11_16_logistic | robust | none | 0.8714 | 0.8687 | 0.8757 | 0.7721 | 0.8206 | 0.8986 | 0.9248 | 0.0557 | 5.6444 | True |
| s11_21_logistic | robust | none | 0.8716 | 0.8684 | 0.8761 | 0.7709 | 0.8202 | 0.8987 | 0.9249 | 0.0554 | 5.6717 | True |
| s11_01_logistic | robust | none | 0.8715 | 0.8683 | 0.8757 | 0.7709 | 0.8200 | 0.8987 | 0.9249 | 0.0556 | 7.5962 | True |
| s11_06_logistic | robust | moderate | 0.8722 | 0.8650 | 0.8245 | 0.8168 | 0.8206 | 0.8984 | 0.9261 | 0.0884 | 6.0274 | True |
| s11_11_logistic | robust | balanced | 0.8669 | 0.8579 | 0.7886 | 0.8429 | 0.8149 | 0.8979 | 0.9267 | 0.1148 | 6.2513 | True |
| s11_26_logistic | robust_sentinel | none | 0.8631 | 0.8084 | 0.6909 | 0.8455 | 0.7604 | 0.8667 | 0.9116 | 0.1923 | 10.7116 | True |


Warnings: 

- `s11_05_xgboost`: Original fit warning capture was not retained after metadata serialization interruption. Saved model/scores recovered; no convergence warning is available for this XGBoost fit.

### Matched preprocessing comparisons

These compare unit-weight trees with the same estimator parameters. They are descriptive paired development results, not significance tests; no representation was changed in response.

| Family | Raw Macro F1 | Clipped Macro F1 | Imputed Macro F1 | Clipped minus raw | Imputed minus raw |
| --- | --- | --- | --- | --- | --- |
| random_forest | 0.9382 | 0.9381 | 0.9395 | -0.0001 | 0.0013 |
| gradient_boosting | 0.9358 | 0.9358 | 0.9362 | 0.0000 | 0.0004 |
| hist_gradient_boosting | 0.9496 | 0.9496 | 0.9491 | -0.0001 | -0.0005 |
| xgboost | 0.9429 | 0.9436 | 0.9418 | 0.0007 | -0.0011 |


### Shortlist and primary reference procedure

Highest Validation Macro F1 per converged model family, plus highest recall with FPR<=.10 and highest AP. Primary: highest Macro F1 with recall>=.70, FPR<=.10 and Train-Val Macro F1 gap<=.10 if available; otherwise highest Macro F1 flagged for tradeoff review. Domain/family diagnostics must qualify any recommendation.

The highest Macro F1 candidate is `s11_09_hist_gradient_boosting`. The selected development reference is `s11_09_hist_gradient_boosting`; the prespecified recall/FPR/gap filter had an eligible candidate: **True**. Family coverage, slice false positives and the quality decision below qualify this selection. This is not a final production model choice.

## 5. Complete Train and Validation shortlist metrics

Suspicious is class 1. Normal is class 0. Confusion matrices use **[[TN, FP], [FN, TP]]**. Average Precision is reported as AP; it is not trapezoidal area under an interpolated PR curve. Undefined precision is assigned zero by the recorded scoring rule.

### Train

| Candidate | Accuracy | Balanced accuracy | Macro F1 | Precision 1 | Recall 1 | F1 1 | Precision 0 | Recall 0 | F1 0 | ROC-AUC | AP | FPR | Confusion matrix |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s11_09_hist_gradient_boosting | 0.9729 | 0.9676 | 0.9695 | 0.9676 | 0.9513 | 0.9594 | 0.9755 | 0.9838 | 0.9796 | 0.9957 | 0.9927 | 0.0162 | [[39137, 644], [984, 19235]] |
| s11_14_hist_gradient_boosting | 0.9699 | 0.9669 | 0.9664 | 0.9531 | 0.9579 | 0.9555 | 0.9785 | 0.9760 | 0.9773 | 0.9954 | 0.9920 | 0.0240 | [[38827, 954], [852, 19367]] |
| s11_27_random_forest | 0.9714 | 0.9623 | 0.9676 | 0.9799 | 0.9343 | 0.9566 | 0.9674 | 0.9902 | 0.9787 | 0.9964 | 0.9937 | 0.0098 | [[39393, 388], [1328, 18891]] |
| s11_15_xgboost | 0.9609 | 0.9555 | 0.9562 | 0.9445 | 0.9391 | 0.9418 | 0.9691 | 0.9720 | 0.9705 | 0.9921 | 0.9867 | 0.0280 | [[38666, 1115], [1232, 18987]] |
| s11_08_gradient_boosting | 0.9496 | 0.9380 | 0.9430 | 0.9457 | 0.9024 | 0.9235 | 0.9515 | 0.9737 | 0.9625 | 0.9878 | 0.9790 | 0.0263 | [[38733, 1048], [1974, 18245]] |
| s11_16_logistic | 0.8887 | 0.8607 | 0.8714 | 0.8804 | 0.7750 | 0.8243 | 0.8922 | 0.9465 | 0.9185 | 0.9327 | 0.9066 | 0.0535 | [[37652, 2129], [4549, 15670]] |


### Validation

| Candidate | Accuracy | Balanced accuracy | Macro F1 | Precision 1 | Recall 1 | F1 1 | Precision 0 | Recall 0 | F1 0 | ROC-AUC | AP | FPR | Confusion matrix |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s11_09_hist_gradient_boosting | 0.9572 | 0.9517 | 0.9521 | 0.9379 | 0.9349 | 0.9364 | 0.9670 | 0.9685 | 0.9677 | 0.9888 | 0.9772 | 0.0315 | [[9632, 313], [329, 4726]] |
| s11_14_hist_gradient_boosting | 0.9542 | 0.9505 | 0.9489 | 0.9261 | 0.9391 | 0.9325 | 0.9688 | 0.9619 | 0.9653 | 0.9896 | 0.9805 | 0.0381 | [[9566, 379], [308, 4747]] |
| s11_27_random_forest | 0.9526 | 0.9421 | 0.9464 | 0.9475 | 0.9098 | 0.9282 | 0.9551 | 0.9744 | 0.9646 | 0.9903 | 0.9827 | 0.0256 | [[9690, 255], [456, 4599]] |
| s11_15_xgboost | 0.9513 | 0.9466 | 0.9456 | 0.9239 | 0.9321 | 0.9280 | 0.9654 | 0.9610 | 0.9632 | 0.9879 | 0.9771 | 0.0390 | [[9557, 388], [343, 4712]] |
| s11_08_gradient_boosting | 0.9453 | 0.9342 | 0.9382 | 0.9354 | 0.8999 | 0.9173 | 0.9501 | 0.9684 | 0.9592 | 0.9855 | 0.9749 | 0.0316 | [[9631, 314], [506, 4549]] |
| s11_16_logistic | 0.8863 | 0.8582 | 0.8687 | 0.8757 | 0.7721 | 0.8206 | 0.8907 | 0.9443 | 0.9167 | 0.9248 | 0.8986 | 0.0557 | [[9391, 554], [1152, 3903]] |


## 6. Validation domain and all 12 family recalls

A positive can satisfy multiple frozen families and domains. Domain support is the union of its family-positive rows; family/domain counts overlap and must not be summed into a confusion matrix. Scenario membership alone never defines these positive slices. All support counts are shown, including S2 (one Validation positive), S4 (eight) and N3 (41); their observed recall is especially unstable and provides weak evidence about generalization.

| Candidate | Domain | Positive support | TP | FN | Recall |
| --- | --- | --- | --- | --- | --- |
| s11_08_gradient_boosting | agent | 3835 | 3424 | 411 | 0.8928 |
| s11_08_gradient_boosting | network | 1271 | 1180 | 91 | 0.9284 |
| s11_08_gradient_boosting | structuring | 1039 | 1035 | 4 | 0.9962 |
| s11_09_hist_gradient_boosting | agent | 3835 | 3579 | 256 | 0.9332 |
| s11_09_hist_gradient_boosting | network | 1271 | 1203 | 68 | 0.9465 |
| s11_09_hist_gradient_boosting | structuring | 1039 | 1034 | 5 | 0.9952 |
| s11_14_hist_gradient_boosting | agent | 3835 | 3593 | 242 | 0.9369 |
| s11_14_hist_gradient_boosting | network | 1271 | 1209 | 62 | 0.9512 |
| s11_14_hist_gradient_boosting | structuring | 1039 | 1035 | 4 | 0.9962 |
| s11_15_xgboost | agent | 3835 | 3562 | 273 | 0.9288 |
| s11_15_xgboost | network | 1271 | 1206 | 65 | 0.9489 |
| s11_15_xgboost | structuring | 1039 | 1034 | 5 | 0.9952 |
| s11_16_logistic | agent | 3835 | 3187 | 648 | 0.8310 |
| s11_16_logistic | network | 1271 | 812 | 459 | 0.6389 |
| s11_16_logistic | structuring | 1039 | 941 | 98 | 0.9057 |
| s11_27_random_forest | agent | 3835 | 3491 | 344 | 0.9103 |
| s11_27_random_forest | network | 1271 | 1161 | 110 | 0.9135 |
| s11_27_random_forest | structuring | 1039 | 1033 | 6 | 0.9942 |


| Code | Frozen family | Validation positive support |
| --- | --- | --- |
| A1 | agent_wallet_growth | 2745 |
| A2 | agent_wallet_concentration | 930 |
| A3 | agent_temporal_burst | 485 |
| A4 | agent_flow_imbalance | 337 |
| N1 | many_to_one_collection | 316 |
| N2 | one_to_many_dispersion | 736 |
| N3 | reciprocal_relationship_cycle | 41 |
| N4 | wallet_pass_through | 247 |
| S1 | variable_fragment_burst | 276 |
| S2 | similar_amount_repetition | 1 |
| S3 | distributed_same_day_fragmentation | 814 |
| S4 | variable_near_threshold_history | 8 |


| Candidate | Family | Positive support | TP | FN | Recall |
| --- | --- | --- | --- | --- | --- |
| s11_08_gradient_boosting | A1 | 2745 | 2678 | 67 | 0.9756 |
| s11_08_gradient_boosting | A2 | 930 | 736 | 194 | 0.7914 |
| s11_08_gradient_boosting | A3 | 485 | 485 | 0 | 1.0000 |
| s11_08_gradient_boosting | A4 | 337 | 170 | 167 | 0.5045 |
| s11_08_gradient_boosting | N1 | 316 | 294 | 22 | 0.9304 |
| s11_08_gradient_boosting | N2 | 736 | 693 | 43 | 0.9416 |
| s11_08_gradient_boosting | N3 | 41 | 22 | 19 | 0.5366 |
| s11_08_gradient_boosting | N4 | 247 | 240 | 7 | 0.9717 |
| s11_08_gradient_boosting | S1 | 276 | 274 | 2 | 0.9928 |
| s11_08_gradient_boosting | S2 | 1 | 1 | 0 | 1.0000 |
| s11_08_gradient_boosting | S3 | 814 | 814 | 0 | 1.0000 |
| s11_08_gradient_boosting | S4 | 8 | 6 | 2 | 0.7500 |
| s11_09_hist_gradient_boosting | A1 | 2745 | 2689 | 56 | 0.9796 |
| s11_09_hist_gradient_boosting | A2 | 930 | 814 | 116 | 0.8753 |
| s11_09_hist_gradient_boosting | A3 | 485 | 481 | 4 | 0.9918 |
| s11_09_hist_gradient_boosting | A4 | 337 | 249 | 88 | 0.7389 |
| s11_09_hist_gradient_boosting | N1 | 316 | 301 | 15 | 0.9525 |
| s11_09_hist_gradient_boosting | N2 | 736 | 708 | 28 | 0.9620 |
| s11_09_hist_gradient_boosting | N3 | 41 | 22 | 19 | 0.5366 |
| s11_09_hist_gradient_boosting | N4 | 247 | 241 | 6 | 0.9757 |
| s11_09_hist_gradient_boosting | S1 | 276 | 273 | 3 | 0.9891 |
| s11_09_hist_gradient_boosting | S2 | 1 | 1 | 0 | 1.0000 |
| s11_09_hist_gradient_boosting | S3 | 814 | 814 | 0 | 1.0000 |
| s11_09_hist_gradient_boosting | S4 | 8 | 6 | 2 | 0.7500 |
| s11_14_hist_gradient_boosting | A1 | 2745 | 2686 | 59 | 0.9785 |
| s11_14_hist_gradient_boosting | A2 | 930 | 830 | 100 | 0.8925 |
| s11_14_hist_gradient_boosting | A3 | 485 | 482 | 3 | 0.9938 |
| s11_14_hist_gradient_boosting | A4 | 337 | 250 | 87 | 0.7418 |
| s11_14_hist_gradient_boosting | N1 | 316 | 304 | 12 | 0.9620 |
| s11_14_hist_gradient_boosting | N2 | 736 | 712 | 24 | 0.9674 |
| s11_14_hist_gradient_boosting | N3 | 41 | 23 | 18 | 0.5610 |
| s11_14_hist_gradient_boosting | N4 | 247 | 239 | 8 | 0.9676 |
| s11_14_hist_gradient_boosting | S1 | 276 | 274 | 2 | 0.9928 |
| s11_14_hist_gradient_boosting | S2 | 1 | 1 | 0 | 1.0000 |
| s11_14_hist_gradient_boosting | S3 | 814 | 814 | 0 | 1.0000 |
| s11_14_hist_gradient_boosting | S4 | 8 | 6 | 2 | 0.7500 |
| s11_15_xgboost | A1 | 2745 | 2683 | 62 | 0.9774 |
| s11_15_xgboost | A2 | 930 | 815 | 115 | 0.8763 |
| s11_15_xgboost | A3 | 485 | 484 | 1 | 0.9979 |
| s11_15_xgboost | A4 | 337 | 233 | 104 | 0.6914 |
| s11_15_xgboost | N1 | 316 | 300 | 16 | 0.9494 |
| s11_15_xgboost | N2 | 736 | 711 | 25 | 0.9660 |
| s11_15_xgboost | N3 | 41 | 23 | 18 | 0.5610 |
| s11_15_xgboost | N4 | 247 | 241 | 6 | 0.9757 |
| s11_15_xgboost | S1 | 276 | 273 | 3 | 0.9891 |
| s11_15_xgboost | S2 | 1 | 1 | 0 | 1.0000 |
| s11_15_xgboost | S3 | 814 | 814 | 0 | 1.0000 |
| s11_15_xgboost | S4 | 8 | 6 | 2 | 0.7500 |
| s11_16_logistic | A1 | 2745 | 2548 | 197 | 0.9282 |
| s11_16_logistic | A2 | 930 | 633 | 297 | 0.6806 |
| s11_16_logistic | A3 | 485 | 466 | 19 | 0.9608 |
| s11_16_logistic | A4 | 337 | 153 | 184 | 0.4540 |
| s11_16_logistic | N1 | 316 | 179 | 137 | 0.5665 |
| s11_16_logistic | N2 | 736 | 571 | 165 | 0.7758 |
| s11_16_logistic | N3 | 41 | 8 | 33 | 0.1951 |
| s11_16_logistic | N4 | 247 | 109 | 138 | 0.4413 |
| s11_16_logistic | S1 | 276 | 264 | 12 | 0.9565 |
| s11_16_logistic | S2 | 1 | 1 | 0 | 1.0000 |
| s11_16_logistic | S3 | 814 | 730 | 84 | 0.8968 |
| s11_16_logistic | S4 | 8 | 6 | 2 | 0.7500 |
| s11_27_random_forest | A1 | 2745 | 2683 | 62 | 0.9774 |
| s11_27_random_forest | A2 | 930 | 756 | 174 | 0.8129 |
| s11_27_random_forest | A3 | 485 | 479 | 6 | 0.9876 |
| s11_27_random_forest | A4 | 337 | 215 | 122 | 0.6380 |
| s11_27_random_forest | N1 | 316 | 296 | 20 | 0.9367 |
| s11_27_random_forest | N2 | 736 | 701 | 35 | 0.9524 |
| s11_27_random_forest | N3 | 41 | 12 | 29 | 0.2927 |
| s11_27_random_forest | N4 | 247 | 220 | 27 | 0.8907 |
| s11_27_random_forest | S1 | 276 | 272 | 4 | 0.9855 |
| s11_27_random_forest | S2 | 1 | 1 | 0 | 1.0000 |
| s11_27_random_forest | S3 | 814 | 814 | 0 | 1.0000 |
| s11_27_random_forest | S4 | 8 | 6 | 2 | 0.7500 |


## 7. Validation normal and hard-negative false positives

FPR denominators include **target 0 only**. Legitimate-origin target-1 events are not false positives under this experiment. Routine, H1–H8 and campaign-member target-0 slices are reported separately. Subtype recipes overlap their parent H category; do not add them to parent counts. No diagnostic field enters fitting or preprocessing.

| Category | Frozen legitimate-behaviour interpretation |
| --- | --- |
| H1 | busy trading / same-day wallet activity |
| H2 | recurring payments |
| H3 | recurring legitimate large payments |
| H4 | legitimate collection |
| H5 | payroll / transit |
| H6 | refunds / settlement |
| H7 | busy agents |
| H8 | concentrated customers / cash demand |


| Candidate | Target-0 category | Support | FP | TN | FPR |
| --- | --- | --- | --- | --- | --- |
| s11_08_gradient_boosting | H1 | 238 | 42 | 196 | 0.1765 |
| s11_08_gradient_boosting | H2 | 374 | 22 | 352 | 0.0588 |
| s11_08_gradient_boosting | H3 | 406 | 18 | 388 | 0.0443 |
| s11_08_gradient_boosting | H4 | 292 | 24 | 268 | 0.0822 |
| s11_08_gradient_boosting | H5 | 214 | 17 | 197 | 0.0794 |
| s11_08_gradient_boosting | H6 | 424 | 3 | 421 | 0.0071 |
| s11_08_gradient_boosting | H7 | 359 | 2 | 357 | 0.0056 |
| s11_08_gradient_boosting | H8 | 460 | 15 | 445 | 0.0326 |
| s11_08_gradient_boosting | campaign_member_target0 | 1796 | 91 | 1705 | 0.0507 |
| s11_08_gradient_boosting | routine | 5382 | 80 | 5302 | 0.0149 |
| s11_09_hist_gradient_boosting | H1 | 238 | 39 | 199 | 0.1639 |
| s11_09_hist_gradient_boosting | H2 | 374 | 19 | 355 | 0.0508 |
| s11_09_hist_gradient_boosting | H3 | 406 | 15 | 391 | 0.0369 |
| s11_09_hist_gradient_boosting | H4 | 292 | 14 | 278 | 0.0479 |
| s11_09_hist_gradient_boosting | H5 | 214 | 21 | 193 | 0.0981 |
| s11_09_hist_gradient_boosting | H6 | 424 | 6 | 418 | 0.0142 |
| s11_09_hist_gradient_boosting | H7 | 359 | 2 | 357 | 0.0056 |
| s11_09_hist_gradient_boosting | H8 | 460 | 15 | 445 | 0.0326 |
| s11_09_hist_gradient_boosting | campaign_member_target0 | 1796 | 99 | 1697 | 0.0551 |
| s11_09_hist_gradient_boosting | routine | 5382 | 83 | 5299 | 0.0154 |
| s11_14_hist_gradient_boosting | H1 | 238 | 42 | 196 | 0.1765 |
| s11_14_hist_gradient_boosting | H2 | 374 | 24 | 350 | 0.0642 |
| s11_14_hist_gradient_boosting | H3 | 406 | 15 | 391 | 0.0369 |
| s11_14_hist_gradient_boosting | H4 | 292 | 15 | 277 | 0.0514 |
| s11_14_hist_gradient_boosting | H5 | 214 | 26 | 188 | 0.1215 |
| s11_14_hist_gradient_boosting | H6 | 424 | 10 | 414 | 0.0236 |
| s11_14_hist_gradient_boosting | H7 | 359 | 3 | 356 | 0.0084 |
| s11_14_hist_gradient_boosting | H8 | 460 | 16 | 444 | 0.0348 |
| s11_14_hist_gradient_boosting | campaign_member_target0 | 1796 | 118 | 1678 | 0.0657 |
| s11_14_hist_gradient_boosting | routine | 5382 | 110 | 5272 | 0.0204 |
| s11_15_xgboost | H1 | 238 | 45 | 193 | 0.1891 |
| s11_15_xgboost | H2 | 374 | 31 | 343 | 0.0829 |
| s11_15_xgboost | H3 | 406 | 19 | 387 | 0.0468 |
| s11_15_xgboost | H4 | 292 | 23 | 269 | 0.0788 |
| s11_15_xgboost | H5 | 214 | 25 | 189 | 0.1168 |
| s11_15_xgboost | H6 | 424 | 6 | 418 | 0.0142 |
| s11_15_xgboost | H7 | 359 | 4 | 355 | 0.0111 |
| s11_15_xgboost | H8 | 460 | 17 | 443 | 0.0370 |
| s11_15_xgboost | campaign_member_target0 | 1796 | 125 | 1671 | 0.0696 |
| s11_15_xgboost | routine | 5382 | 93 | 5289 | 0.0173 |
| s11_16_logistic | H1 | 238 | 45 | 193 | 0.1891 |
| s11_16_logistic | H2 | 374 | 44 | 330 | 0.1176 |
| s11_16_logistic | H3 | 406 | 33 | 373 | 0.0813 |
| s11_16_logistic | H4 | 292 | 39 | 253 | 0.1336 |
| s11_16_logistic | H5 | 214 | 36 | 178 | 0.1682 |
| s11_16_logistic | H6 | 424 | 19 | 405 | 0.0448 |
| s11_16_logistic | H7 | 359 | 19 | 340 | 0.0529 |
| s11_16_logistic | H8 | 460 | 24 | 436 | 0.0522 |
| s11_16_logistic | campaign_member_target0 | 1796 | 165 | 1631 | 0.0919 |
| s11_16_logistic | routine | 5382 | 130 | 5252 | 0.0242 |
| s11_27_random_forest | H1 | 238 | 34 | 204 | 0.1429 |
| s11_27_random_forest | H2 | 374 | 9 | 365 | 0.0241 |
| s11_27_random_forest | H3 | 406 | 6 | 400 | 0.0148 |
| s11_27_random_forest | H4 | 292 | 7 | 285 | 0.0240 |
| s11_27_random_forest | H5 | 214 | 25 | 189 | 0.1168 |
| s11_27_random_forest | H6 | 424 | 2 | 422 | 0.0047 |
| s11_27_random_forest | H7 | 359 | 2 | 357 | 0.0056 |
| s11_27_random_forest | H8 | 460 | 14 | 446 | 0.0304 |
| s11_27_random_forest | campaign_member_target0 | 1796 | 83 | 1713 | 0.0462 |
| s11_27_random_forest | routine | 5382 | 73 | 5309 | 0.0136 |

For the primary reference, the highest hard-negative FPRs are H1 (busy trading / same-day wallet activity): 0.1639 (39/238), H5 (payroll / transit): 0.0981 (21/214), H2 (recurring payments): 0.0508 (19/374). These identify where legitimate target-0 behaviour most often receives a review prediction.

### Available hard-scenario subtype recipes

| Candidate | Target-0 subtype | Support | FP | TN | FPR |
| --- | --- | --- | --- | --- | --- |
| s11_08_gradient_boosting | H1/S1 | 133 | 16 | 117 | 0.1203 |
| s11_08_gradient_boosting | H1/S3 | 105 | 26 | 79 | 0.2476 |
| s11_08_gradient_boosting | H2/S2 | 374 | 22 | 352 | 0.0588 |
| s11_08_gradient_boosting | H3/S4 | 406 | 18 | 388 | 0.0443 |
| s11_08_gradient_boosting | H4/N1 | 292 | 24 | 268 | 0.0822 |
| s11_08_gradient_boosting | H5/N2 | 100 | 4 | 96 | 0.0400 |
| s11_08_gradient_boosting | H5/N4 | 114 | 13 | 101 | 0.1140 |
| s11_08_gradient_boosting | H6/N3 | 424 | 3 | 421 | 0.0071 |
| s11_08_gradient_boosting | H7/A1 | 194 | 2 | 192 | 0.0103 |
| s11_08_gradient_boosting | H7/A3 | 165 | 0 | 165 | 0.0000 |
| s11_08_gradient_boosting | H8/A2 | 241 | 10 | 231 | 0.0415 |
| s11_08_gradient_boosting | H8/A4 | 219 | 5 | 214 | 0.0228 |
| s11_09_hist_gradient_boosting | H1/S1 | 133 | 21 | 112 | 0.1579 |
| s11_09_hist_gradient_boosting | H1/S3 | 105 | 18 | 87 | 0.1714 |
| s11_09_hist_gradient_boosting | H2/S2 | 374 | 19 | 355 | 0.0508 |
| s11_09_hist_gradient_boosting | H3/S4 | 406 | 15 | 391 | 0.0369 |
| s11_09_hist_gradient_boosting | H4/N1 | 292 | 14 | 278 | 0.0479 |
| s11_09_hist_gradient_boosting | H5/N2 | 100 | 3 | 97 | 0.0300 |
| s11_09_hist_gradient_boosting | H5/N4 | 114 | 18 | 96 | 0.1579 |
| s11_09_hist_gradient_boosting | H6/N3 | 424 | 6 | 418 | 0.0142 |
| s11_09_hist_gradient_boosting | H7/A1 | 194 | 1 | 193 | 0.0052 |
| s11_09_hist_gradient_boosting | H7/A3 | 165 | 1 | 164 | 0.0061 |
| s11_09_hist_gradient_boosting | H8/A2 | 241 | 11 | 230 | 0.0456 |
| s11_09_hist_gradient_boosting | H8/A4 | 219 | 4 | 215 | 0.0183 |
| s11_14_hist_gradient_boosting | H1/S1 | 133 | 20 | 113 | 0.1504 |
| s11_14_hist_gradient_boosting | H1/S3 | 105 | 22 | 83 | 0.2095 |
| s11_14_hist_gradient_boosting | H2/S2 | 374 | 24 | 350 | 0.0642 |
| s11_14_hist_gradient_boosting | H3/S4 | 406 | 15 | 391 | 0.0369 |
| s11_14_hist_gradient_boosting | H4/N1 | 292 | 15 | 277 | 0.0514 |
| s11_14_hist_gradient_boosting | H5/N2 | 100 | 7 | 93 | 0.0700 |
| s11_14_hist_gradient_boosting | H5/N4 | 114 | 19 | 95 | 0.1667 |
| s11_14_hist_gradient_boosting | H6/N3 | 424 | 10 | 414 | 0.0236 |
| s11_14_hist_gradient_boosting | H7/A1 | 194 | 2 | 192 | 0.0103 |
| s11_14_hist_gradient_boosting | H7/A3 | 165 | 1 | 164 | 0.0061 |
| s11_14_hist_gradient_boosting | H8/A2 | 241 | 12 | 229 | 0.0498 |
| s11_14_hist_gradient_boosting | H8/A4 | 219 | 4 | 215 | 0.0183 |
| s11_15_xgboost | H1/S1 | 133 | 21 | 112 | 0.1579 |
| s11_15_xgboost | H1/S3 | 105 | 24 | 81 | 0.2286 |
| s11_15_xgboost | H2/S2 | 374 | 31 | 343 | 0.0829 |
| s11_15_xgboost | H3/S4 | 406 | 19 | 387 | 0.0468 |
| s11_15_xgboost | H4/N1 | 292 | 23 | 269 | 0.0788 |
| s11_15_xgboost | H5/N2 | 100 | 4 | 96 | 0.0400 |
| s11_15_xgboost | H5/N4 | 114 | 21 | 93 | 0.1842 |
| s11_15_xgboost | H6/N3 | 424 | 6 | 418 | 0.0142 |
| s11_15_xgboost | H7/A1 | 194 | 3 | 191 | 0.0155 |
| s11_15_xgboost | H7/A3 | 165 | 1 | 164 | 0.0061 |
| s11_15_xgboost | H8/A2 | 241 | 12 | 229 | 0.0498 |
| s11_15_xgboost | H8/A4 | 219 | 5 | 214 | 0.0228 |
| s11_16_logistic | H1/S1 | 133 | 20 | 113 | 0.1504 |
| s11_16_logistic | H1/S3 | 105 | 25 | 80 | 0.2381 |
| s11_16_logistic | H2/S2 | 374 | 44 | 330 | 0.1176 |
| s11_16_logistic | H3/S4 | 406 | 33 | 373 | 0.0813 |
| s11_16_logistic | H4/N1 | 292 | 39 | 253 | 0.1336 |
| s11_16_logistic | H5/N2 | 100 | 4 | 96 | 0.0400 |
| s11_16_logistic | H5/N4 | 114 | 32 | 82 | 0.2807 |
| s11_16_logistic | H6/N3 | 424 | 19 | 405 | 0.0448 |
| s11_16_logistic | H7/A1 | 194 | 7 | 187 | 0.0361 |
| s11_16_logistic | H7/A3 | 165 | 12 | 153 | 0.0727 |
| s11_16_logistic | H8/A2 | 241 | 20 | 221 | 0.0830 |
| s11_16_logistic | H8/A4 | 219 | 4 | 215 | 0.0183 |
| s11_27_random_forest | H1/S1 | 133 | 20 | 113 | 0.1504 |
| s11_27_random_forest | H1/S3 | 105 | 14 | 91 | 0.1333 |
| s11_27_random_forest | H2/S2 | 374 | 9 | 365 | 0.0241 |
| s11_27_random_forest | H3/S4 | 406 | 6 | 400 | 0.0148 |
| s11_27_random_forest | H4/N1 | 292 | 7 | 285 | 0.0240 |
| s11_27_random_forest | H5/N2 | 100 | 5 | 95 | 0.0500 |
| s11_27_random_forest | H5/N4 | 114 | 20 | 94 | 0.1754 |
| s11_27_random_forest | H6/N3 | 424 | 2 | 422 | 0.0047 |
| s11_27_random_forest | H7/A1 | 194 | 2 | 192 | 0.0103 |
| s11_27_random_forest | H7/A3 | 165 | 0 | 165 | 0.0000 |
| s11_27_random_forest | H8/A2 | 241 | 10 | 231 | 0.0415 |
| s11_27_random_forest | H8/A4 | 219 | 4 | 215 | 0.0183 |


### Origin review rates (both targets)

These are predicted review fractions, not FPRs, because they include legitimate-origin true positives.

| Candidate | Origin | All-target support | Predicted reviews | Review rate |
| --- | --- | --- | --- | --- |
| s11_08_gradient_boosting | campaign_member | 3600 | 1760 | 0.4889 |
| s11_08_gradient_boosting | hard_scenario | 4800 | 1993 | 0.4152 |
| s11_08_gradient_boosting | routine | 6600 | 1110 | 0.1682 |
| s11_09_hist_gradient_boosting | campaign_member | 3600 | 1803 | 0.5008 |
| s11_09_hist_gradient_boosting | hard_scenario | 4800 | 2045 | 0.4260 |
| s11_09_hist_gradient_boosting | routine | 6600 | 1191 | 0.1805 |
| s11_14_hist_gradient_boosting | campaign_member | 3600 | 1832 | 0.5089 |
| s11_14_hist_gradient_boosting | hard_scenario | 4800 | 2066 | 0.4304 |
| s11_14_hist_gradient_boosting | routine | 6600 | 1228 | 0.1861 |
| s11_15_xgboost | campaign_member | 3600 | 1834 | 0.5094 |
| s11_15_xgboost | hard_scenario | 4800 | 2078 | 0.4329 |
| s11_15_xgboost | routine | 6600 | 1188 | 0.1800 |
| s11_16_logistic | campaign_member | 3600 | 1630 | 0.4528 |
| s11_16_logistic | hard_scenario | 4800 | 1838 | 0.3829 |
| s11_16_logistic | routine | 6600 | 989 | 0.1498 |
| s11_27_random_forest | campaign_member | 3600 | 1748 | 0.4856 |
| s11_27_random_forest | hard_scenario | 4800 | 1951 | 0.4065 |
| s11_27_random_forest | routine | 6600 | 1155 | 0.1750 |


## 8. Generalization

All gaps are Train minus Validation. The prespecified severe-overfit flag is >0.10 Macro F1 or >0.15 suspicious F1, recall, AP or ROC-AUC. This descriptive flag is not a statistical significance test. Validation remains a development set reused across the compact candidate comparison.

| Candidate | Macro F1 gap | Suspicious F1 gap | Suspicious recall gap | ROC-AUC gap | AP gap | Severe flag |
| --- | --- | --- | --- | --- | --- | --- |
| s11_08_gradient_boosting | 0.0047 | 0.0062 | 0.0025 | 0.0023 | 0.0041 | False |
| s11_09_hist_gradient_boosting | 0.0174 | 0.0230 | 0.0164 | 0.0070 | 0.0155 | False |
| s11_14_hist_gradient_boosting | 0.0174 | 0.0229 | 0.0188 | 0.0058 | 0.0116 | False |
| s11_15_xgboost | 0.0106 | 0.0138 | 0.0069 | 0.0042 | 0.0096 | False |
| s11_16_logistic | 0.0028 | 0.0037 | 0.0029 | 0.0080 | 0.0080 | False |
| s11_27_random_forest | 0.0212 | 0.0283 | 0.0245 | 0.0061 | 0.0111 | False |


## 9. Probability/score quality

No calibration or operating-threshold search was performed. Score distributions are descriptive; especially with class weighting, scores are not asserted to be calibrated probabilities of the natural population target. The overlap interval intersects the class-specific 5th–95th percentile ranges; reversed endpoints mean no intersection. Full quantiles, standard deviations and min/max range intersections are in the JSON.

| Candidate | Partition | Target | N | Min | Q05 | Median | Q95 | Max | Mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s11_08_gradient_boosting | train | 0 | 39781 | 0.0134 | 0.0194 | 0.0442 | 0.3348 | 0.9971 | 0.0953 |
| s11_08_gradient_boosting | train | 1 | 20219 | 0.0288 | 0.2706 | 0.9826 | 0.9974 | 0.9999 | 0.8751 |
| s11_08_gradient_boosting | validation | 0 | 9945 | 0.0134 | 0.0194 | 0.0468 | 0.3670 | 0.9889 | 0.1032 |
| s11_08_gradient_boosting | validation | 1 | 5055 | 0.0357 | 0.2671 | 0.9812 | 0.9966 | 0.9999 | 0.8714 |
| s11_09_hist_gradient_boosting | train | 0 | 39781 | 0.0002 | 0.0015 | 0.0168 | 0.2849 | 0.9939 | 0.0554 |
| s11_09_hist_gradient_boosting | train | 1 | 20219 | 0.0128 | 0.5117 | 0.9965 | 0.9998 | 1.0000 | 0.9273 |
| s11_09_hist_gradient_boosting | validation | 0 | 9945 | 0.0004 | 0.0016 | 0.0196 | 0.3579 | 0.9980 | 0.0694 |
| s11_09_hist_gradient_boosting | validation | 1 | 5055 | 0.0095 | 0.3647 | 0.9945 | 0.9997 | 1.0000 | 0.9134 |
| s11_14_hist_gradient_boosting | train | 0 | 39781 | 0.0002 | 0.0016 | 0.0202 | 0.3565 | 0.9952 | 0.0671 |
| s11_14_hist_gradient_boosting | train | 1 | 20219 | 0.0127 | 0.5511 | 0.9970 | 0.9998 | 1.0000 | 0.9328 |
| s11_14_hist_gradient_boosting | validation | 0 | 9945 | 0.0003 | 0.0016 | 0.0238 | 0.4265 | 0.9983 | 0.0806 |
| s11_14_hist_gradient_boosting | validation | 1 | 5055 | 0.0101 | 0.4118 | 0.9954 | 0.9997 | 1.0000 | 0.9177 |
| s11_15_xgboost | train | 0 | 39781 | 0.0020 | 0.0078 | 0.0343 | 0.3802 | 0.9976 | 0.0875 |
| s11_15_xgboost | train | 1 | 20219 | 0.0222 | 0.4412 | 0.9951 | 0.9998 | 1.0000 | 0.9125 |
| s11_15_xgboost | validation | 0 | 9945 | 0.0023 | 0.0079 | 0.0382 | 0.4291 | 0.9976 | 0.1004 |
| s11_15_xgboost | validation | 1 | 5055 | 0.0171 | 0.3964 | 0.9926 | 0.9996 | 1.0000 | 0.9074 |
| s11_16_logistic | train | 0 | 39781 | 0.0000 | 0.0055 | 0.0668 | 0.5163 | 0.9999 | 0.1327 |
| s11_16_logistic | train | 1 | 20219 | 0.0001 | 0.0885 | 0.8834 | 1.0000 | 1.0000 | 0.7390 |
| s11_16_logistic | validation | 0 | 9945 | 0.0004 | 0.0059 | 0.0703 | 0.5261 | 0.9989 | 0.1384 |
| s11_16_logistic | validation | 1 | 5055 | 0.0058 | 0.0753 | 0.8807 | 1.0000 | 1.0000 | 0.7342 |
| s11_27_random_forest | train | 0 | 39781 | 0.0000 | 0.0000 | 0.0039 | 0.2618 | 0.9417 | 0.0417 |
| s11_27_random_forest | train | 1 | 20219 | 0.0123 | 0.4253 | 0.9980 | 1.0000 | 1.0000 | 0.9177 |
| s11_27_random_forest | validation | 0 | 9945 | 0.0000 | 0.0000 | 0.0049 | 0.3480 | 0.9944 | 0.0575 |
| s11_27_random_forest | validation | 1 | 5055 | 0.0015 | 0.3022 | 0.9912 | 1.0000 | 1.0000 | 0.8887 |


| Candidate | Train middle-90% overlap interval | Validation middle-90% overlap interval |
| --- | --- | --- |
| s11_08_gradient_boosting | [0.27063020667442905, 0.33480947713659753] | [0.2671452476416859, 0.3669962916559804] |
| s11_09_hist_gradient_boosting | [0.5116780370123385, 0.2848652292919899] | [0.3647126540750413, 0.35792388288135774] |
| s11_14_hist_gradient_boosting | [0.5511426330904996, 0.35650125437447294] | [0.4117620500836659, 0.4265119848545398] |
| s11_15_xgboost | [0.4411777645349503, 0.3802141547203064] | [0.3964177519083023, 0.4290668547153468] |
| s11_16_logistic | [0.08853525407367775, 0.5163451251616972] | [0.07533107759585805, 0.5261484179346754] |
| s11_27_random_forest | [0.42533614374740797, 0.26184798274020676] | [0.30218748620264735, 0.3480249278362048] |


## 10. Descriptive model importance

Importance is not causality and did not change the feature set. Different methods use different units and should not be compared as absolute effect sizes. Logistic coefficients are signed effects per Train standard deviation of transformed input; the machine record also retains coefficients per robust-scaled unit and intercept. Tree impurity importance and XGBoost normalized gain can favor continuous features. HistGradientBoosting has no native importance here, so a fixed Validation AP permutation diagnostic is used (three repeats, 3,000 sampled rows). Correlation can redistribute importance and sparse families may be absent from that sample.

| Candidate | Method | Top feature | Top feature absolute share | Current amount share | Coverage share | Marker-bearing columns share | Concentration flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| s11_08_gradient_boosting | impurity reduction | agent_wallet_growth_ratio_7d | 0.4999 | 0.0011 | 0.0217 | 0.6393 | False |
| s11_09_hist_gradient_boosting | Validation permutation drop in average precision; 3 repeats, 3000-row subsamples | agent_wallet_growth_ratio_7d | 0.6150 | 0.0038 | 0.0161 | 0.7626 | True |
| s11_14_hist_gradient_boosting | Validation permutation drop in average precision; 3 repeats, 3000-row subsamples | agent_wallet_growth_ratio_7d | 0.5912 | 0.0034 | 0.0126 | 0.7506 | True |
| s11_15_xgboost | normalized gain | agent_wallet_growth_ratio_7d | 0.1366 | 0.0063 | 0.1281 | 0.3366 | False |
| s11_16_logistic | signed coefficient per Train SD of transformed input | agent_wallet_growth_ratio_7d | 0.3023 | 0.0067 | 0.1246 | 0.5303 | False |
| s11_27_random_forest | impurity reduction | agent_wallet_growth_ratio_7d | 0.4941 | 0.0070 | 0.0364 | 0.6514 | False |

Absolute mass shares normalize absolute coefficients/importances (including signed permutation values). The concentration flag indicates a single feature >50% or a domain >70% of that mass. Marker-bearing feature importance mixes observed-value and missingness effects, so it cannot prove missingness dominance. Where available, the fraction of raw-tree internal splits isolating a sentinel is reported separately.

| Candidate | Current | Structuring | Network | Agent | Coverage | Sentinel-isolating split fraction |
| --- | --- | --- | --- | --- | --- | --- |
| s11_08_gradient_boosting | 0.0048 | 0.1499 | 0.2259 | 0.5976 | 0.0217 | 0.0639 |
| s11_09_hist_gradient_boosting | 0.0199 | 0.0767 | 0.1253 | 0.7621 | 0.0161 | not available for this model/representation |
| s11_14_hist_gradient_boosting | 0.0211 | 0.0885 | 0.1292 | 0.7486 | 0.0126 | not available for this model/representation |
| s11_15_xgboost | 0.0222 | 0.1693 | 0.3585 | 0.3219 | 0.1281 | not available for this model/representation |
| s11_16_logistic | 0.0491 | 0.1198 | 0.1359 | 0.5706 | 0.1246 | not available for this model/representation |
| s11_27_random_forest | 0.0136 | 0.1606 | 0.1756 | 0.6139 | 0.0364 | 0.0294 |

The primary reference concentrates 61.5% of absolute importance in `agent_wallet_growth_ratio_7d` and 76.2% in the agent domain. Current amount contributes 0.4% and coverage 1.6%. This concentration deserves attention in future controlled development; it does not demonstrate causality or that missingness alone drives predictions. Multi-family overlap also means high domain recall does not prove the model independently recognizes each domain mechanism.

### All 32 importance values

| Feature | s11_08_gradient_boosting | s11_09_hist_gradient_boosting | s11_14_hist_gradient_boosting | s11_15_xgboost | s11_16_logistic | s11_27_random_forest |
| --- | --- | --- | --- | --- | --- | --- |
| current_amount_usd | 0.0011 | 0.0021 | 0.0018 | 0.0063 | -0.0729 | 0.0070 |
| current_is_cash_in | 0.0003 | 0.0035 | 0.0033 | 0.0080 | 0.2333 | 0.0022 |
| current_is_cash_out | 0.0033 | 0.0052 | 0.0061 | 0.0080 | 0.2302 | 0.0044 |
| wallet_count_1h_inclusive | 0.0000 | 0.0019 | 0.0018 | 0.0041 | 0.0514 | 0.0016 |
| wallet_value_24h_inclusive | 0.0116 | 0.0123 | 0.0147 | 0.0124 | 0.2305 | 0.0174 |
| wallet_count_utc_day_inclusive | 0.1373 | 0.0177 | 0.0185 | 0.1246 | 0.6001 | 0.1291 |
| wallet_active_hours_utc_day | 0.0003 | 0.0047 | 0.0048 | 0.0056 | 0.1710 | 0.0034 |
| wallet_current_amount_cluster_share_7d | 0.0006 | 0.0016 | 0.0015 | 0.0043 | -0.0333 | 0.0028 |
| wallet_band_share_7d_inclusive | 0.0000 | 0.0013 | 0.0014 | 0.0028 | 0.0042 | 0.0010 |
| wallet_count_acceleration_1h | 0.0001 | 0.0022 | 0.0046 | 0.0155 | 0.2192 | 0.0052 |
| receiver_unique_sources_24h_inclusive | 0.0085 | 0.0070 | 0.0072 | 0.0147 | 0.5200 | 0.0072 |
| receiver_inflow_count_24h_inclusive | 0.0514 | 0.0136 | 0.0135 | 0.0881 | 0.1193 | 0.0305 |
| receiver_inflow_acceleration_24h | 0.0171 | 0.0031 | 0.0043 | 0.0355 | 0.0149 | 0.0237 |
| sender_unique_destinations_24h_inclusive | 0.0005 | 0.0022 | 0.0022 | 0.0146 | 0.1935 | 0.0061 |
| sender_outflow_count_24h_inclusive | 0.0961 | 0.0120 | 0.0121 | 0.1285 | 0.1240 | 0.0371 |
| sender_outflow_acceleration_24h | 0.0226 | 0.0050 | 0.0046 | 0.0342 | 0.4000 | 0.0400 |
| current_return_path_length | 0.0003 | 0.0013 | 0.0013 | 0.0030 | 0.0564 | 0.0002 |
| current_return_amount_ratio | 0.0022 | 0.0026 | 0.0026 | 0.0080 | -0.0109 | 0.0013 |
| wallet_observed_onward_funding_share_24h | 0.0273 | 0.0196 | 0.0196 | 0.0290 | -0.0429 | 0.0279 |
| wallet_prior_funding_age_hours | 0.0001 | 0.0018 | 0.0015 | 0.0031 | -0.0035 | 0.0016 |
| agent_service_count_1h_inclusive | 0.0012 | 0.0015 | 0.0019 | 0.0633 | -0.7701 | 0.0069 |
| agent_service_acceleration_1h | 0.0609 | 0.0320 | 0.0289 | 0.0596 | 1.5464 | 0.0351 |
| agent_wallet_growth_ratio_7d | 0.4999 | 0.3346 | 0.3157 | 0.1366 | 3.3051 | 0.4941 |
| agent_new_wallet_share_7d | 0.0044 | 0.0047 | 0.0105 | 0.0045 | -0.0012 | 0.0045 |
| agent_top2_count_share_24h | 0.0214 | 0.0162 | 0.0182 | 0.0198 | -0.3192 | 0.0358 |
| agent_top2_share_change_24h | 0.0028 | 0.0045 | 0.0049 | 0.0068 | 0.2483 | 0.0117 |
| agent_cash_value_skew_24h | 0.0008 | 0.0040 | 0.0041 | 0.0127 | -0.0027 | 0.0073 |
| agent_cash_count_skew_24h | 0.0042 | 0.0123 | 0.0120 | 0.0148 | -0.0398 | 0.0121 |
| agent_cash_value_skew_change | 0.0020 | 0.0048 | 0.0035 | 0.0039 | -0.0055 | 0.0063 |
| wallet_history_coverage_days | 0.0171 | 0.0045 | 0.0029 | 0.0199 | 0.2838 | 0.0181 |
| receiver_history_coverage_days | 0.0035 | 0.0019 | 0.0014 | 0.0138 | 0.1914 | 0.0085 |
| agent_history_coverage_days | 0.0010 | 0.0023 | 0.0024 | 0.0943 | 0.8873 | 0.0098 |


## 11. Development goals and decision

These are the current Stage 11 research goals, not regulatory standards or dataset design constraints. Technical execution and quality are judged separately.

| Goal | Target | Primary Validation result | Met |
| --- | --- | --- | --- |
| average_precision | >= 0.75 | 0.9772 | True |
| false_positive_rate | <= 0.1 | 0.0315 | True |
| macro_f1 | >= 0.8 | 0.9521 | True |
| suspicious_f1 | >= 0.7 | 0.9364 | True |
| suspicious_recall | >= 0.7 | 0.9349 | True |


| Domain goal | Target | Primary recall | Met |
| --- | --- | --- | --- |
| structuring | 0.6500 | 0.9952 | True |
| network | 0.7000 | 0.9465 | True |
| agent | 0.6500 | 0.9332 | True |

Primary families below 20% observed recall: **none**. The primary severe-overfit flag is **False**. Zero/low recall on a family with very small support must still be disclosed, but cannot establish a stable population failure rate.

Lowest primary family recalls: N3 reciprocal_relationship_cycle: 0.5366 (22/41), A4 agent_flow_imbalance: 0.7389 (249/337), S4 variable_near_threshold_history: 0.7500 (6/8), A2 agent_wallet_concentration: 0.8753 (814/930).

The current gaps call for particular attention to reciprocal cycles (N3) and agent cash imbalance (A4). A strong overall baseline does not establish reliable coverage of every scenario. S2/S4 estimates have too little support to demonstrate robust performance even where observed recall is high.

**A — STRONG BASELINE.** At least one candidate meets the stated aggregate and domain goals with no family below the prespecified diagnostic recall floor and no severe generalization flag. The evidence supports separately authorized controlled refinement. Sparse-family estimates, synthetic targets and Validation selection remain limitations.

A next authorized stage can investigate the documented weaknesses using Train/Validation with a bounded plan. No final model, final threshold or holdout result is declared here. V3 is a different synthetic decision-point task; these results do not establish superiority to V1 or V2.

## 12. Protection and artifact verification

Before/after protection: **PASS**, 450 explicitly allowlisted files before and 450 after; changed paths: `[]`. This includes frozen Stage 10A matrices/contract/code/evidence, V3 development inputs and design, V2 source/design/models/development, and the application/V1 allowlists. Exact paths and digests are recorded in `stage11_protection.json`.


| Public artifact | Before SHA-256 | After SHA-256 |
| --- | --- | --- |
| ml_v3/data/manifests/evaluation_content_commitment.json | efc14471b98103a3ad547d93fc56833d014389efd9d3c6e5be6ba896c70d9d58 | efc14471b98103a3ad547d93fc56833d014389efd9d3c6e5be6ba896c70d9d58 |
| ml_v3/reports/V3_STAGE9_HOLDOUT_SEAL.json | efc14471b98103a3ad547d93fc56833d014389efd9d3c6e5be6ba896c70d9d58 | efc14471b98103a3ad547d93fc56833d014389efd9d3c6e5be6ba896c70d9d58 |

Public commitment verification proves those metadata bytes are unchanged. It does not newly verify unread evaluation bytes. No holdout data root is traversed. Protection is bounded by the explicit allowlist; excluded evaluation/unpartitioned historical dataset bytes are not claimed as newly inspected.

All candidate pipelines include their fitted preprocessing, are stored under `models/stage11_candidates/`, and are marked **DEVELOPMENT CANDIDATE — NOT FINAL**. Saved probabilities and model-file hashes permit auditing. Each shortlisted pipeline was loaded; scores agree within 1e-12 and all predictions at 0.50 are identical. Random Forest parallel summation caused a machine-rounding difference and a strict bitwise check stopped finalization once; diagnostics resumed from all 30 saved fits with the explicit tolerance, without retraining. The execution amendment preserves both recovery events. No model was refitted on Validation or integrated into the application.

| Candidate | Reload maximum absolute score difference | Tolerance | Threshold-0.50 predictions identical |
| --- | --- | --- | --- |
| s11_09_hist_gradient_boosting | 0 | 1e-12 | True |
| s11_14_hist_gradient_boosting | 0 | 1e-12 | True |
| s11_27_random_forest | 2.2204460492503131e-16 | 1e-12 | True |
| s11_15_xgboost | 0 | 1e-12 | True |
| s11_08_gradient_boosting | 0 | 1e-12 | True |
| s11_16_logistic | 0 | 1e-12 | True |


## 13. Reproducibility and evidence index

The modeling seed, installed library versions, exact model parameters, weights, transformations, source digests, warnings, convergence, runtime and configuration count are recorded. Repeated fits were not performed, so same-seed training repeatability across machines/library builds is not certified; exact reload prediction equality was checked for every shortlist artifact.

Commands from the repository root:

```powershell
python -B -m unittest discover -s ml_v3/tests -p test_stage11_preprocessing.py -v
python -B ml_v3/src/run_stage11.py
python -B ml_v3/src/report_stage11.py
```

The runner refuses to overwrite an existing candidate directory. For a fresh repeat, preserve this run and use an isolated development checkout with the same frozen inputs and recorded code/environment; capture a fresh protection-before record with `stage11_protection.snapshot()` before fitting. The report renderer reads completed artifacts only.

| Evidence | Contents |
| --- | --- |
| [stage11_search_plan.json](stage11_search_plan.json) | Preregistered grid, seed, threshold, selection/gap rules, environment and source digests |
| [stage11_execution_amendment.json](stage11_execution_amendment.json) | Recorded logging and replay-tolerance corrections with recovery source hashes; no grid or modeling change |
| [stage11_candidate_results.json](stage11_candidate_results.json) | All fits, exact parameters, warnings, timings, complete Train/Validation metrics |
| [stage11_shortlist.json](stage11_shortlist.json) | Shortlist, development reference and quality decision |
| [stage11_preprocessing.json](stage11_preprocessing.json) | Per-column marker handling, Train medians, clipping and scaling for all variants |
| [stage11_preprocessing_tests.json](stage11_preprocessing_tests.json) | Marker-specific handling and fixed-threshold confusion-orientation regression checks |
| [stage11_domain_recall.json](stage11_domain_recall.json) | Domain support/TP/FN/recall |
| [stage11_family_recall.json](stage11_family_recall.json) | All twelve family support/TP/FN/recall values |
| [stage11_normal_fpr.json](stage11_normal_fpr.json) | Routine, H1–H8, subtype and target-0 campaign FPR; origin review rates |
| [stage11_generalization.json](stage11_generalization.json) | Train–Validation gaps and severe flags |
| [stage11_probability_quality.json](stage11_probability_quality.json) | Class score distributions and overlap |
| [stage11_importance.json](stage11_importance.json) | Complete importance/coefficient values and concentration diagnostics |
| [stage11_protection.json](stage11_protection.json) | Before/after inventories and public hashes |
| [stage11_artifact_manifest.json](stage11_artifact_manifest.json) | Candidate model and score-file digests |


Final independent artifact check: **PASS**. Recomputed all 60 Train/Validation candidate metric sets from saved scores; target-0 slice counts reconcile with the global confusion matrices; positive support equals TP+FN; all 61 candidate/score/README hashes and frozen feature hashes match. See [stage11_final_verification.json](stage11_final_verification.json).

V3 STAGE 11 COMPLETE — WAITING FOR APPROVAL.
