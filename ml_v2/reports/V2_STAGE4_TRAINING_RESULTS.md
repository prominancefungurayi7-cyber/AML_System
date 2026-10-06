# MODEL V2 — STAGE 4 PREPROCESSING, CANDIDATE TRAINING AND VALIDATION COMPARISON

**Overall result: CONDITIONAL PASS.** Five candidate algorithms were trained and compared using only V2 Train and Validation at the fixed `0.50` decision threshold. Random Forest achieved the highest Validation Macro F1, but its low suspicious recall and large Train/Validation gap make threshold-stage review essential. No holdout was accessed and no V1/application file changed.

## 1. Scope and environment

Models trained: Logistic Regression, Random Forest, Gradient Boosting, HistGradientBoosting, and XGBoost. XGBoost 3.4.1 was already installed in the separate system Python; nothing was installed and the application `.venv` and root `requirements.txt` were untouched.

Versions: Python 3.14.3, NumPy 2.4.3, scikit-learn 1.9.0, joblib 1.5.3, XGBoost 3.4.1. Seed: `20260921`. Total candidate/reproduction time: **571.90 seconds**. Candidate artifacts are under `ml_v2/models/candidates/`; none is a production or integrated artifact.

## 2. Preprocessing

Three Train-fitted paths were compared:

- `raw`: no clipping or scaling.
- `clipped`: Train 0.5th/99.5th-percentile winsorization on 16 unbounded/heavy-tailed features only.
- `robust`: the same clipping followed by `RobustScaler`, fitted on Train using median and interquartile range. This path was used for Logistic Regression.

Validation was transformed only with Train-fitted parameters. Binary and contract-bounded `[0,1]` features were not clipped.

| Clipped feature | Train 0.5% | Train 99.5% |
|---|---:|---:|
| `structuring_prior_tx_count_1h` | 0 | 11 |
| `structuring_prior_value_sum_24h` | 0 | 75,448.8577 |
| `structuring_same_day_prior_tx_count` | 0 | 18 |
| `structuring_amount_cluster_dispersion_7d` | 0 | 3.390931 |
| `network_outbound_counterparty_count_7d` | 0 | 12 |
| `network_inbound_counterparty_count_7d` | 0 | 12 |
| `network_outbound_counterparty_entropy_30d` | 0 | 2.242028 |
| `network_pass_through_ratio_24h` | 0 | 322.222522 |
| `agent_prior_tx_count_1h` | 0 | 15 |
| `agent_prior_tx_count_7d` | 0 | 87 |
| `agent_prior_value_sum_1h` | 0 | 52,591.3421 |
| `agent_prior_value_sum_7d` | 0 | 363,079.78515 |
| `agent_unique_wallet_count_7d` | 0 | 61 |
| `agent_inbound_outbound_value_ratio_7d` | 0 | 442.193275 |
| `agent_hourly_tx_zscore_30d` | -7.006346 | 16.097468 |
| `agent_hourly_value_zscore_30d` | -0.918175 | 4.886509 |

Baseline preprocessing effects on Validation Macro F1 were modest: Logistic raw→robust `0.4766→0.4894`; Random Forest raw→clipped `0.4873→0.4844`; Gradient Boosting `0.5063→0.5042`; HistGradientBoosting `0.5046→0.5013`; XGBoost `0.5004→0.5024`. Clipping helped some regularized configurations, so preprocessing remains part of each saved candidate rather than a global choice.

## 3. Baselines and controlled search

Baseline configurations used standard fixed-threshold classifiers: Logistic `C=1`, no weight; Random Forest 160 trees, unrestricted depth, leaf 1; Gradient Boosting 100 trees, learning rate .1, depth 3; HistGradientBoosting 120 iterations, 31 leaves, leaf 20; XGBoost 180 trees, learning rate .08, depth 5. All baseline class weights were neutral.

The compact search covered Logistic `C={0.1,1,10}` and `{none,balanced}`; Random Forest 240 trees, depth 16, split 8, leaf 3, sqrt features and matched `{none,balanced_subsample}`; Gradient Boosting 160 trees, learning rate .05, depth 3, split 8, leaf 4, subsample .85 and matched sample weights; HistGradientBoosting 180 iterations, learning rate .07, 31 leaves, depth 10, leaf 30, L2=1 and matched class weights; XGBoost 240 trees, learning rate .05, depth 5, child weight 3, subsample/columns .85, lambda 2, alpha .05 and matched `scale_pos_weight={1,7.3333}`. Raw/clipped pairs were evaluated for every tree family. The machine-readable result contains all 32 configurations.

Controlled weighting materially changed the operating point. For example, raw regularized Random Forest moved from Macro F1 `0.4778`, recall `0.0100`, FPR `0.0014` without weighting to `0.5814`, recall `0.2061`, FPR `0.0634` with weighting. Similar weighted/unweighted comparisons were preserved for every tree family. No SMOTE or class-distribution change was used.

## 4. Best configuration per algorithm

| Algorithm / best configuration | Preprocess / weighting | Train Macro F1 | Validation Macro F1 | Validation suspicious F1 | Recall | ROC-AUC | PR-AUC | FPR |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Logistic `C=10` | robust / balanced | .5450 | .4943 | .2798 | .6711 | .6692 | .2279 | .4264 |
| Random Forest, 240/depth16 | raw / balanced subsample | .8748 | **.5814** | .2467 | .2061 | .6644 | .2325 | .0634 |
| Gradient Boosting, 160/.05 | clipped / balanced samples | .5925 | .5402 | .3032 | .6122 | **.6933** | **.2591** | .3308 |
| HistGradientBoosting, 180/.07 | clipped / balanced | .6888 | **.5742** | .3037 | .4617 | .6716 | .2482 | .2152 |
| XGBoost, 240/.05 | raw / scale weight 7.3333 | .6595 | .5683 | **.3061** | .5011 | .6798 | .2508 | .2417 |

Validation confusion matrices (`[[TN,FP],[FN,TP]]`): Logistic `[[7572,5628],[592,1208]]`; Random Forest `[[12363,837],[1429,371]]`; Gradient Boosting `[[8834,4366],[698,1102]]`; HistGradientBoosting `[[10359,2841],[969,831]]`; XGBoost `[[10009,3191],[898,902]]`.

Other validation metrics are recorded in full in `stage4_candidate_results.json`, including Accuracy, Balanced Accuracy, Normal Recall and Suspicious Precision. Accuracy was informational only.

## 5. Generalization assessment

Macro-F1 Train→Validation gaps were Logistic `.0507`, Random Forest `.2934`, Gradient Boosting `.0523`, HistGradientBoosting `.1146`, and XGBoost `.0912`. Random Forest also fell from suspicious F1 `.7809→.2467`, recall `.8139→.2061`, ROC-AUC `.9756→.6644`, and PR-AUC `.8835→.2325`. This is substantial overfitting despite its highest Validation Macro F1.

HistGradientBoosting and XGBoost also show meaningful gaps but retain more balanced suspicious detection. Gradient Boosting generalizes more closely and has the strongest ranking metrics, but its fixed-threshold FPR is high. Logistic has the smallest broad gaps but the highest FPR and did not converge at the configured iteration limit.

## 6. Validation domain and family recall

| Slice (positive count) | Random Forest | HistGradientBoosting | XGBoost |
|---|---:|---:|---:|
| Structuring (600) | .3417 | .6167 | .6667 |
| Network (600) | .1983 | .4000 | .4367 |
| Agent (600) | .0783 | .3683 | .4000 |
| S1 variable fragment (150) | .4867 | .8000 | .8533 |
| S2 similar amount (150) | .1867 | .4467 | .5467 |
| S3 same-day fragmentation (150) | .4933 | .7533 | .7600 |
| S4 near-threshold history (150) | .2000 | .4667 | .5067 |
| N1 many-to-one (150) | .1067 | .2733 | .3200 |
| N2 one-to-many (150) | .2733 | .5467 | .5733 |
| N3 reciprocal cycle (150) | .0600 | .1333 | .1467 |
| N4 pass-through (150) | .3533 | .6467 | .7067 |
| A1 wallet growth (150) | .0600 | .3200 | .3533 |
| A2 wallet concentration (150) | .0267 | .2067 | .3133 |
| A3 temporal burst (150) | .2133 | .7600 | .7867 |
| A4 flow imbalance (150) | .0133 | .1867 | .1467 |

Random Forest’s fixed-threshold domain imbalance is material. All three struggle most with reciprocal cycles; Random Forest also nearly misses three agent families. These results are diagnostics on Validation, not grounds for editing individual predictions or features.

## 7. Validation normal false-positive rates

| Normal slice | Random Forest | HistGradientBoosting | XGBoost |
|---|---:|---:|---:|
| Routine (6,600) | .0164 | .0971 | .1124 |
| H1 (825) | .3042 | .5297 | .5903 |
| H2 | .0461 | .2909 | .3273 |
| H3 | .0945 | .3115 | .3455 |
| H4 | .0594 | .2327 | .2461 |
| H5 | .1709 | .3782 | .4061 |
| H6 | .0509 | .1964 | .2158 |
| H7 | .0921 | .4497 | .5236 |
| H8 | .0655 | .2776 | .3139 |

Random Forest’s superior Macro F1 is driven largely by normal-class preservation at the cost of suspicious recall. HistGradientBoosting and XGBoost recover more suspicious scenarios but flag many legitimate hard negatives, especially H1 and H7. Gradient Boosting and Logistic are still more aggressive and are not recommended as the initial threshold-stage pair.

## 8. Importance and coefficients

Random Forest’s top importance is `structuring_prior_value_sum_24h` at `.0629`; its top ten are broadly distributed and no single feature dominates. XGBoost’s largest gain importance is `agent_current_wallet_is_new` at `.1305`, followed by `agent_prior_value_sum_1h` `.0866` and same-day count `.0816`. Gradient Boosting’s top three are prior value 24h `.1412`, agent prior value 1h `.1164`, and agent-current-wallet-new `.1097`. Logistic’s largest standardized coefficient magnitude is agent-current-wallet-new `.7538`; its top coefficient accounts for `.1853` of total absolute coefficient magnitude.

HistGradientBoosting in scikit-learn does not expose a native `feature_importances_` attribute, so no unsupported surrogate importance was invented. Importance was not used to remove features.

## 9. Warnings and reproducibility

All eight Logistic Regression fits emitted `lbfgs` convergence warnings at 2,000 iterations, including scaled variants. Their metrics remain reported but Logistic is not recommended without a separately approved solver/convergence experiment. Joblib emitted a Windows physical-core detection traceback because `wmic` was unavailable; it fell back and all models completed. No other training error was recorded.

The selected Random Forest configuration was independently refit twice with the same seed. Predictions were identical, probability maximum absolute difference was `0.0`, and metrics were identical. All four Stage 4 contract tests pass.

## 10. Candidate selection

**PRIMARY V2 CANDIDATE: `rf_raw_regularized_balanced_subsample`.** It is selected by the declared primary metric, Validation Macro F1 (`.5814`), and has the lowest overall/hard-negative FPR among the leading models. Its substantial overfitting and very low agent/network recall are explicit constraints for threshold optimization; it is not a final model.

**SECONDARY V2 CANDIDATE: `hgb_clipped_regularized_balanced`.** It is only `.0072` behind on Macro F1, improves suspicious recall from `.2061` to `.4617`, and provides substantially better domain balance, while producing more false positives. XGBoost remains a useful recorded comparator but is not promoted because it trails HistGradientBoosting on Macro F1 and FPR despite slightly better suspicious F1/recall.

Both primary and secondary should advance to a separately approved Validation-only threshold stage. That stage should explicitly expose the recall-versus-hard-negative tradeoff rather than optimize one headline metric in isolation.

## 11. Protection and stage boundary

Before/after hashes matched for 347 protected V1/application files and 37 V2 dataset/feature input files. No holdout was loaded, transformed or evaluated. No holdout matrix exists. No server, application model, database, configuration, deployment file, V1 artifact or application environment changed.

No classification threshold beyond `0.50` was evaluated. Neither candidate is called the final V2 model, and no comparison with V1 holdout performance is claimed.

V2 STAGE 4 COMPLETE — WAITING FOR APPROVAL.
