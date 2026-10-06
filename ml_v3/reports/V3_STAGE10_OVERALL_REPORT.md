# MODEL V3 - STAGE 10 OVERALL REPORT

**Dataset:** `mobile_money_aml_synthetic_100k_v3`  
**Stage:** Feature contract, development feature extraction and audit  
**Status:** Artifacts produced; corrections required before full Stage 10 approval.

This is the single main report for Stage 10. It consolidates the feature contract, implementation, matrix results, distributions, shift and target-overlap diagnostics, temporal tests, reproducibility, protection, preprocessing recommendations and limitations. Earlier split reports and JSON files remain supporting records. No model performance has been measured.

## 1. Outcome and status correction

Train and Validation matrices were produced with 32 columns, matching the proposed 3 current-event, 7 structuring, 10 network, 9 agent and 3 coverage groups. The saved checks report finite values, preserved target counts, deterministic extraction and passing limited temporal/metadata tests. The previous overall PASS statement exceeded this evidence. Source review during consolidation found implementation discrepancies, and two small synthetic examples confirmed temporal defects. The passing test suite does not establish full compliance with the approved Stage 8 semantics.

No dataset, target, predicate, feature definition or matrix was changed while preparing this report. The two additional checks used synthetic in-memory transactions. No evaluation partition was opened or enumerated for this consolidation.

## 2. Scope and outputs

The implemented runner loads frozen Train and Validation transactions and aligns targets solely from `decision_point_target`. Each extraction starts fresh partition-local state. It constructs numeric features from observable fields; row identifiers remain in a separate file. No classifier training, fitted preprocessing, threshold optimization or application integration was performed in Stage 10.

| Partition | Rows | Columns | Target 0 | Target 1 | Positive rate | NaN | Infinity | Duplicate IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Train | 60000 | 32 | 39781 | 20219 | 33.6983% | 0 | 0 | 0 |
| Validation | 15000 | 32 | 9945 | 5055 | 33.7000% | 0 | 0 | 0 |

The positive rates are integrity measurements of the frozen experiment, not optimization targets. Campaign-member negatives and legitimate-origin positives were retained.

| Artifact | Purpose |
| --- | --- |
| `src/feature_contract.py` | Ordered names, domains and declared formulas |
| `src/feature_pipeline.py` | Independent V3 history and feature calculations |
| `src/feature_audit.py` | Descriptive matrix, distribution, overlap and small temporal checks |
| `src/run_stage10.py` | Runs development extraction twice and writes audit outputs |
| `tests/test_stage10_features.py` | Six Stage 10 test methods with synthetic examples |
| `features/development/train/` | 60,000-row X.csv, y.csv, row_ids.csv and feature_names.json |
| `features/development/validation/` | 15,000-row X.csv, y.csv, row_ids.csv and feature_names.json |

Paths in this table are relative to `ml_v3/`. The prior run reported no evaluation feature matrices.

## 3. Ordered feature contract

The declared feature order below is identical to the matrix order. These are declared definitions; Section 4 records the discrepancies found in the implementation. The original complete contract is reproduced in Appendix A so this report can be read independently. The original file is preserved as the pre-extraction contract artifact.

| Position | Feature | Domain | Declared definition | Temporal scope |
| --- | --- | --- | --- | --- |
| 1 | `current_amount_usd` | current | current transaction amount / 100 USD | current |
| 2 | `current_is_cash_in` | current | 1 iff current transaction_type is cash_in | current |
| 3 | `current_is_cash_out` | current | 1 iff current transaction_type is cash_out | current |
| 4 | `wallet_count_1h_inclusive` | structuring | count of subject-wallet events in [T-1h,T] | prior+current |
| 5 | `wallet_value_24h_inclusive` | structuring | sum of subject-wallet amounts in [T-24h,T] | prior+current |
| 6 | `wallet_count_utc_day_inclusive` | structuring | count of subject-wallet events since UTC midnight through T | prior+current |
| 7 | `wallet_active_hours_utc_day` | structuring | distinct UTC hour buckets for subject-wallet events since midnight through T | prior+current |
| 8 | `wallet_current_amount_cluster_share_7d` | structuring | share of subject-wallet events in [T-7d,T] within 5% of current amount | prior+current |
| 9 | `wallet_band_share_7d_inclusive` | structuring | share of subject-wallet events in [T-7d,T] in 7000..10500 USD | prior+current |
| 10 | `wallet_count_acceleration_1h` | structuring | inclusive 1h count / max(1, prior-28d count / 672) | prior+current |
| 11 | `receiver_unique_sources_24h_inclusive` | network | distinct W2W senders to receiver in [T-24h,T] | prior+current |
| 12 | `receiver_inflow_count_24h_inclusive` | network | W2W inflow count to receiver in [T-24h,T] | prior+current |
| 13 | `receiver_inflow_acceleration_24h` | network | inclusive receiver inflow count / max(1, prior-28d inflow count / 28) | prior+current |
| 14 | `sender_unique_destinations_24h_inclusive` | network | distinct W2W receivers from sender in [T-24h,T] | prior+current |
| 15 | `sender_outflow_count_24h_inclusive` | network | W2W outflow count from sender in [T-24h,T] | prior+current |
| 16 | `sender_outflow_acceleration_24h` | network | inclusive sender outflow count / max(1, prior-28d count / 28) | prior+current |
| 17 | `current_return_path_length` | network | shortest simple prior path receiver to sender, 1..5 edges in 7d; zero otherwise | prior-only plus current endpoints |
| 18 | `current_return_amount_ratio` | network | current amount / first-edge amount of selected prior return path; -1 when absent | prior-only plus current amount |
| 19 | `wallet_observed_onward_funding_share_24h` | network | observed outward value after prior funding anchor / observed funding value | prior+current for outflow |
| 20 | `wallet_prior_funding_age_hours` | network | hours from prior funding anchor to current outflow; -1 when absent | prior-only plus current timestamp |
| 21 | `agent_service_count_1h_inclusive` | agent | agent service-event count in [T-1h,T]; zero for direct W2W | prior+current |
| 22 | `agent_service_acceleration_1h` | agent | inclusive service count / max(1, preceding-28d service count / 672); -1 if coverage insufficient | prior+current |
| 23 | `agent_wallet_growth_ratio_7d` | agent | recent inclusive distinct serviced wallets / max(1, median of four preceding 7d counts); -1 if insufficient | prior+current |
| 24 | `agent_new_wallet_share_7d` | agent | recent serviced-wallet fraction absent from preceding-28d wallet union; -1 if insufficient | prior+current |
| 25 | `agent_top2_count_share_24h` | agent | top-two serviced-wallet service-event share in [T-24h,T] | prior+current |
| 26 | `agent_top2_share_change_24h` | agent | inclusive top-two share minus preceding-28d top-two share; -1 if insufficient | prior+current |
| 27 | `agent_cash_value_skew_24h` | agent | (CashOut value-CashIn value)/(sum) in [T-24h,T] | prior+current |
| 28 | `agent_cash_count_skew_24h` | agent | corresponding signed event-count skew in [T-24h,T] | prior+current |
| 29 | `agent_cash_value_skew_change` | agent | inclusive cash value skew minus preceding-28d cash value skew; -1 if insufficient | prior+current |
| 30 | `wallet_history_coverage_days` | coverage | partition-local subject-wallet observation span before T, capped at 28 days | prior-only |
| 31 | `receiver_history_coverage_days` | coverage | partition-local receiver observation span before T, capped at 28 days | prior-only |
| 32 | `agent_history_coverage_days` | coverage | partition-local agent observation span before T, capped at 28 days; zero without agent | prior-only |

## 4. Corrections and verification gaps

| Finding | Evidence | Consequence |
| --- | --- | --- |
| N3 paths do not enforce chronological traversal | `_path()` orders candidate edges but never requires each next edge key to exceed the preceding edge key. Synthetic r->m at minute 2, m->s at minute 1, current s->r at minute 3 returns length 2; the approved temporal-path definition requires 0. | The current path feature is not the approved temporally ordered path summary. |
| Equal-timestamp histories are inconsistently included | Several network, baseline and funding filters use timestamp < now. Two receipts at the same timestamp with IDs 1 and 2 produce current receiver count 1 for ID 2, whereas strict key ordering requires 2. | The saved equal-timestamp test checks only the wallet count and misses this discrepancy. |
| Funding anchor can exceed 24 hours | The W2W inflow candidates are limited to 24 hours, but the appended prior Cash-In candidates have no lower time bound. | Funding age and onward share can use an older anchor than their declared window implies. |
| Baseline eligibility is incomplete | Baseline-relative features generally check coverage >=28 days without the count conditions referenced by Stage 8; acceleration baselines also overlap recent windows. | Elapsed history alone does not establish the specified preceding baseline or sufficient observations. |
| Missing sentinel collides with valid values | -1 is a missing marker and a valid change in top-two share or cash-value skew. The statistics count every -1 as missing, including valid signed skew values. | Missingness fractions and future imputation cannot be interpreted uniformly. |
| Novel-wallet fraction is event weighted | `agent_new_wallet_share_7d` divides novel-wallet service-event count by all recent service events. | This differs from a distinct-wallet population fraction if repeated visits occur; the unit must be reconciled explicitly. |
| Oracle checks have limited scope | Saved checks inspect forbidden exact column names, one metadata perturbation, and target range overlap. | They do not test trivial combinations or exclude near-oracle encodings. |
| Reproducibility evidence is incomplete for serialized bytes | The runner compares two in-memory extraction results, then writes and hashes one output set. | It establishes numeric repeatability; it does not independently compare two serialized output sets. |
| Protection evidence has a bounded scope | The saved before/after comparison covers 83 allowlisted files. The runner checks public certificate existence, not before/after certificate content. | It is not a comprehensive certificate for every V1/V2/application file or for public commitment immutability. |
| Contract freeze is asserted, not cryptographically recorded | The contract existed before extraction; the runner only checks its presence. | No saved pre-extraction contract hash establishes an immutable contract version. |

These findings concern semantic correctness and audit coverage; they do not indicate that future transactions were read. Corrections should be tested against the approved contracts before matrices are regenerated. The frozen raw dataset and target definitions remain the authority. No repair or regeneration was performed for this reporting request.

## 5. Temporal safety, metadata independence and tests

| Saved check | Recorded result | Evidence scope |
| --- | --- | --- |
| Future-prefix invariance | True | One two-event prefix plus a future transaction |
| Equal-timestamp ordering | True | Row order and wallet one-hour count only |
| Current amount perturbation | True | Path length and three coverage values |
| Private metadata perturbation | True | One observable transaction with private fields varied |
| Forbidden feature-name check | PASS | Exact names; no semantic proof |

The previous test run passed 27 tests across V3. Six methods belong to the Stage 10 feature test file; the remainder test earlier reference/access functionality. Those six methods cover ordinary wallet activity, repeated amounts, collection, dispersion, an ordered path, a missing path, funding/outward roles, basic agent service, cash-value balance and coverage. Several assertions are inequalities, rather than the full set of manually calculated expected values requested for Stage 10. Domain-wide current/future perturbations, reversed path chronology, and network equal-timestamp behavior were not covered by that passing suite.

During consolidation, the reversed-path and equal-timestamp examples in Section 4 reproduced the two defects. The existing 27-test result is historical evidence, not a new test execution or proof that these cases pass.

## 6. Feature distributions

The following tables reproduce the saved descriptive statistics in matrix order. Values are unscaled. Q01/Q05/Q95/Q99 denote percentiles. Fractions are proportions of rows. The -1 fraction is a literal value count, not reliable missingness for every column.

### Train

| Feature | Min | Max | Mean | SD | Median | Q01 | Q05 | Q95 | Q99 | Zero fraction | Distinct | -1 fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `current_amount_usd` | 1 | 24999 | 3366.32 | 6247.29 | 189.83 | 2.85 | 7.86 | 19298.8 | 23929.9 | 0 | 36100 | 0 |
| `current_is_cash_in` | 0 | 1 | 0.254 | 0.435298 | 0 | 0 | 0 | 1 | 1 | 0.746 | 2 | 0 |
| `current_is_cash_out` | 0 | 1 | 0.254 | 0.435298 | 0 | 0 | 0 | 1 | 1 | 0.746 | 2 | 0 |
| `wallet_count_1h_inclusive` | 1 | 22 | 1.3479 | 1.3177 | 1 | 1 | 1 | 3 | 8 | 0 | 22 | 0 |
| `wallet_value_24h_inclusive` | 1 | 392344 | 9045.84 | 16802 | 1034.84 | 4.06 | 14.4 | 35567.8 | 66176.8 | 0 | 48081 | 0 |
| `wallet_count_utc_day_inclusive` | 1 | 27 | 2.13455 | 2.4987 | 1 | 1 | 1 | 7 | 14 | 0 | 27 | 0 |
| `wallet_active_hours_utc_day` | 1 | 15 | 1.63428 | 1.22587 | 1 | 1 | 1 | 4 | 7 | 0 | 15 | 0 |
| `wallet_current_amount_cluster_share_7d` | 0.0243902 | 1 | 0.298887 | 0.225962 | 0.25 | 0.0434783 | 0.0645161 | 1 | 1 | 0 | 241 | 0 |
| `wallet_band_share_7d_inclusive` | 0 | 1 | 0.058619 | 0.129451 | 0 | 0 | 0 | 0.333333 | 0.5 | 0.754167 | 229 | 0 |
| `wallet_count_acceleration_1h` | -1 | 22 | 0.971917 | 1.5164 | 1 | -1 | -1 | 3 | 8 | 0 | 23 | 0.165067 |
| `receiver_unique_sources_24h_inclusive` | 0 | 12 | 0.924483 | 1.16532 | 1 | 0 | 0 | 3 | 6 | 0.3751 | 13 | 0 |
| `receiver_inflow_count_24h_inclusive` | 0 | 21 | 1.01733 | 1.44155 | 1 | 0 | 0 | 3 | 8 | 0.3751 | 22 | 0 |
| `receiver_inflow_acceleration_24h` | -1 | 21 | 0.679868 | 1.50745 | 1 | -1 | -1 | 3 | 7 | 0.312467 | 70 | 0.16525 |
| `sender_unique_destinations_24h_inclusive` | 0 | 14 | 1.27862 | 1.70107 | 1 | 0 | 0 | 5 | 8 | 0.347633 | 15 | 0 |
| `sender_outflow_count_24h_inclusive` | 0 | 22 | 1.42783 | 2.1457 | 1 | 0 | 0 | 6 | 11 | 0.347633 | 23 | 0 |
| `sender_outflow_acceleration_24h` | -1 | 20 | 1.04408 | 2.17676 | 1 | -1 | -1 | 5 | 10 | 0.288467 | 121 | 0.164933 |
| `current_return_path_length` | 0 | 5 | 0.155717 | 0.778483 | 0 | 0 | 0 | 0 | 5 | 0.953967 | 6 | 0 |
| `current_return_amount_ratio` | -1 | 24796.8 | 3.73254 | 138.788 | -1 | -1 | -1 | -1 | 18.1066 | 0 | 2662 | 0.953967 |
| `wallet_observed_onward_funding_share_24h` | -1 | 19025.8 | 3.54452 | 107.651 | 0.539638 | -1 | 0 | 2.4753 | 29.7377 | 0.254 | 43479 | 0.0213 |
| `wallet_prior_funding_age_hours` | -1 | 4318.49 | 1484.06 | 1383.77 | 1237.52 | -1 | 0 | 3877.24 | 4167.37 | 0.254 | 43484 | 0.0213 |
| `agent_service_count_1h_inclusive` | 0 | 29 | 1.41767 | 2.08932 | 1 | 0 | 0 | 5 | 11 | 0.234 | 30 | 0 |
| `agent_service_acceleration_1h` | -1 | 26 | 0.82405 | 2.21446 | 1 | -1 | -1 | 4 | 11 | 0 | 27 | 0.35795 |
| `agent_wallet_growth_ratio_7d` | -1 | 20 | 0.550931 | 1.4121 | 0.813559 | -1 | -1 | 2.61538 | 4.85714 | 0 | 1834 | 0.35795 |
| `agent_new_wallet_share_7d` | -1 | 1 | 0.187763 | 0.894343 | 0.758621 | -1 | -1 | 1 | 1 | 1.66667e-05 | 1181 | 0.35795 |
| `agent_top2_count_share_24h` | 0 | 1 | 0.497524 | 0.36533 | 0.5 | 0 | 0 | 1 | 1 | 0.234 | 307 | 0 |
| `agent_top2_share_change_24h` | -1 | 0.96 | -0.068591 | 0.728244 | 0.216667 | -1 | -1 | 0.844444 | 0.909091 | 0.00075 | 17647 | 0.35795 |
| `agent_cash_value_skew_24h` | -1 | 1 | -0.0375374 | 0.716101 | 0 | -1 | -1 | 1 | 1 | 0.27505 | 21587 | 0.145817 |
| `agent_cash_count_skew_24h` | -1 | 1 | -0.0280869 | 0.575143 | 0 | -1 | -1 | 1 | 1 | 0.3828 | 141 | 0.145817 |
| `agent_cash_value_skew_change` | -2 | 2 | -0.36743 | 0.855922 | -0.857117 | -1.59651 | -1.18802 | 1.23164 | 1.58007 | 1.66667e-05 | 28449 | 0.35795 |
| `wallet_history_coverage_days` | 0 | 28 | 25.6989 | 6.17585 | 28 | 0.112604 | 8.49958 | 28 | 28 | 0.0075 | 9456 | 0 |
| `receiver_history_coverage_days` | 0 | 28 | 25.6887 | 6.18466 | 28 | 0.28157 | 8.41821 | 28 | 28 | 0.00583333 | 9567 | 0 |
| `agent_history_coverage_days` | 0 | 28 | 19.7492 | 12.1262 | 28 | 0 | 0 | 28 | 28 | 0.2356 | 7343 | 0 |

Constant columns: none.

Saved near-constant flags: `current_is_cash_in`, `current_is_cash_out`. The implementation defines this flag as at most two distinct values, so it flags binary variables without establishing that one value dominates.

### Validation

| Feature | Min | Max | Mean | SD | Median | Q01 | Q05 | Q95 | Q99 | Zero fraction | Distinct | -1 fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `current_amount_usd` | 1 | 24980.3 | 3273.51 | 6193.96 | 182.85 | 2.49 | 7 | 19395.7 | 23916.5 | 0 | 10888 | 0 |
| `current_is_cash_in` | 0 | 1 | 0.254 | 0.435298 | 0 | 0 | 0 | 1 | 1 | 0.746 | 2 | 0 |
| `current_is_cash_out` | 0 | 1 | 0.254 | 0.435298 | 0 | 0 | 0 | 1 | 1 | 0.746 | 2 | 0 |
| `wallet_count_1h_inclusive` | 1 | 19 | 1.36107 | 1.37827 | 1 | 1 | 1 | 3 | 9 | 0 | 19 | 0 |
| `wallet_value_24h_inclusive` | 1 | 235883 | 8869.46 | 15273.8 | 906.48 | 4 | 13.7475 | 36320.6 | 70488.3 | 0 | 13085 | 0 |
| `wallet_count_utc_day_inclusive` | 1 | 23 | 2.1694 | 2.57141 | 1 | 1 | 1 | 8 | 14 | 0 | 23 | 0 |
| `wallet_active_hours_utc_day` | 1 | 13 | 1.64227 | 1.29235 | 1 | 1 | 1 | 4 | 7 | 0 | 13 | 0 |
| `wallet_current_amount_cluster_share_7d` | 0.025 | 1 | 0.29527 | 0.22019 | 0.25 | 0.0416667 | 0.0666667 | 1 | 1 | 0 | 188 | 0 |
| `wallet_band_share_7d_inclusive` | 0 | 1 | 0.0580863 | 0.129457 | 0 | 0 | 0 | 0.333333 | 0.5 | 0.7544 | 163 | 0 |
| `wallet_count_acceleration_1h` | -1 | 18 | 0.948733 | 1.4442 | 1 | -1 | -1 | 3 | 7 | 0 | 19 | 0.164133 |
| `receiver_unique_sources_24h_inclusive` | 0 | 13 | 0.907 | 1.15352 | 1 | 0 | 0 | 3 | 6 | 0.383867 | 14 | 0 |
| `receiver_inflow_count_24h_inclusive` | 0 | 18 | 0.996333 | 1.41687 | 1 | 0 | 0 | 3 | 7 | 0.383867 | 19 | 0 |
| `receiver_inflow_acceleration_24h` | -1 | 18 | 0.662933 | 1.4922 | 1 | -1 | -1 | 3 | 7 | 0.322 | 20 | 0.164267 |
| `sender_unique_destinations_24h_inclusive` | 0 | 13 | 1.29653 | 1.7119 | 1 | 0 | 0 | 5 | 8 | 0.344867 | 14 | 0 |
| `sender_outflow_count_24h_inclusive` | 0 | 18 | 1.44953 | 2.17231 | 1 | 0 | 0 | 6 | 11 | 0.344867 | 19 | 0 |
| `sender_outflow_acceleration_24h` | -1 | 18 | 1.02031 | 2.10351 | 1 | -1 | -1 | 5 | 10 | 0.288733 | 62 | 0.1642 |
| `current_return_path_length` | 0 | 5 | 0.352733 | 1.13897 | 0 | 0 | 0 | 4 | 5 | 0.899467 | 6 | 0 |
| `current_return_amount_ratio` | -1 | 6167 | 6.71553 | 116.442 | -1 | -1 | -1 | 0.985332 | 114.534 | 0 | 1483 | 0.899467 |
| `wallet_observed_onward_funding_share_24h` | -1 | 1506.14 | 2.11996 | 28.3977 | 0.568701 | -1 | 0 | 2.34041 | 14.992 | 0.254 | 10838 | 0.0236 |
| `wallet_prior_funding_age_hours` | -1 | 4317.62 | 1444.03 | 1367.75 | 1186.72 | -1 | 0 | 3826.46 | 4143.36 | 0.254 | 10838 | 0.0236 |
| `agent_service_count_1h_inclusive` | 0 | 22 | 1.38567 | 1.89821 | 1 | 0 | 0 | 5 | 10 | 0.234 | 23 | 0 |
| `agent_service_acceleration_1h` | -1 | 22 | 0.820467 | 2.11836 | 1 | -1 | -1 | 4 | 10 | 0 | 23 | 0.355467 |
| `agent_wallet_growth_ratio_7d` | -1 | 11 | 0.521531 | 1.31387 | 0.825742 | -1 | -1 | 2.4 | 4 | 0 | 1115 | 0.355467 |
| `agent_new_wallet_share_7d` | -1 | 1 | 0.0560343 | 0.802789 | 0.470588 | -1 | -1 | 0.964286 | 1 | 0.000666667 | 1000 | 0.355467 |
| `agent_top2_count_share_24h` | 0 | 1 | 0.503856 | 0.364905 | 0.5 | 0 | 0 | 1 | 1 | 0.234 | 223 | 0 |
| `agent_top2_share_change_24h` | -1 | 0.9375 | -0.0749255 | 0.719905 | 0.205068 | -1 | -1 | 0.830986 | 0.884959 | 0.000866667 | 5968 | 0.355467 |
| `agent_cash_value_skew_24h` | -1 | 1 | -0.0192564 | 0.71101 | 0 | -1 | -1 | 1 | 1 | 0.276733 | 5419 | 0.147533 |
| `agent_cash_count_skew_24h` | -1 | 1 | -0.0341042 | 0.574827 | 0 | -1 | -1 | 1 | 1 | 0.379733 | 114 | 0.147533 |
| `agent_cash_value_skew_change` | -1.99734 | 1.99703 | -0.378216 | 0.843267 | -0.875186 | -1.63243 | -1.19123 | 1.16716 | 1.4541 | 0.000133333 | 7186 | 0.355467 |
| `wallet_history_coverage_days` | 0 | 28 | 25.6552 | 6.24102 | 28 | 0.177283 | 8.50576 | 28 | 28 | 0.00766667 | 2349 | 0 |
| `receiver_history_coverage_days` | 0 | 28 | 25.6559 | 6.2257 | 28 | 0.318861 | 8.58612 | 28 | 28 | 0.0062 | 2373 | 0 |
| `agent_history_coverage_days` | 0 | 28 | 19.7703 | 12.132 | 28 | 0 | 0 | 28 | 28 | 0.2356 | 1800 | 0 |

Constant columns: none.

Saved near-constant flags: `current_is_cash_in`, `current_is_cash_out`. The implementation defines this flag as at most two distinct values, so it flags binary variables without establishing that one value dominates.

## 7. Train/Validation distribution shift

Differences below are Validation minus Train. They are descriptive; no feature definition was fitted to reduce them. Means for sentinel-bearing columns mix unavailable values with observations.

| Feature | Train mean | Validation mean | Mean difference | Train zero rate | Validation zero rate | Zero-rate difference |
| --- | --- | --- | --- | --- | --- | --- |
| `current_amount_usd` | 3366.32 | 3273.51 | -92.809 | 0 | 0 | 0 |
| `current_is_cash_in` | 0.254 | 0.254 | 0 | 0.746 | 0.746 | 0 |
| `current_is_cash_out` | 0.254 | 0.254 | 0 | 0.746 | 0.746 | 0 |
| `wallet_count_1h_inclusive` | 1.3479 | 1.36107 | 0.0131667 | 0 | 0 | 0 |
| `wallet_value_24h_inclusive` | 9045.84 | 8869.46 | -176.372 | 0 | 0 | 0 |
| `wallet_count_utc_day_inclusive` | 2.13455 | 2.1694 | 0.03485 | 0 | 0 | 0 |
| `wallet_active_hours_utc_day` | 1.63428 | 1.64227 | 0.00798333 | 0 | 0 | 0 |
| `wallet_current_amount_cluster_share_7d` | 0.298887 | 0.29527 | -0.0036166 | 0 | 0 | 0 |
| `wallet_band_share_7d_inclusive` | 0.058619 | 0.0580863 | -0.000532717 | 0.754167 | 0.7544 | 0.000233333 |
| `wallet_count_acceleration_1h` | 0.971917 | 0.948733 | -0.0231833 | 0 | 0 | 0 |
| `receiver_unique_sources_24h_inclusive` | 0.924483 | 0.907 | -0.0174833 | 0.3751 | 0.383867 | 0.00876667 |
| `receiver_inflow_count_24h_inclusive` | 1.01733 | 0.996333 | -0.021 | 0.3751 | 0.383867 | 0.00876667 |
| `receiver_inflow_acceleration_24h` | 0.679868 | 0.662933 | -0.0169345 | 0.312467 | 0.322 | 0.00953333 |
| `sender_unique_destinations_24h_inclusive` | 1.27862 | 1.29653 | 0.0179167 | 0.347633 | 0.344867 | -0.00276667 |
| `sender_outflow_count_24h_inclusive` | 1.42783 | 1.44953 | 0.0217 | 0.347633 | 0.344867 | -0.00276667 |
| `sender_outflow_acceleration_24h` | 1.04408 | 1.02031 | -0.0237679 | 0.288467 | 0.288733 | 0.000266667 |
| `current_return_path_length` | 0.155717 | 0.352733 | 0.197017 | 0.953967 | 0.899467 | -0.0545 |
| `current_return_amount_ratio` | 3.73254 | 6.71553 | 2.98299 | 0 | 0 | 0 |
| `wallet_observed_onward_funding_share_24h` | 3.54452 | 2.11996 | -1.42456 | 0.254 | 0.254 | 0 |
| `wallet_prior_funding_age_hours` | 1484.06 | 1444.03 | -40.0353 | 0.254 | 0.254 | 0 |
| `agent_service_count_1h_inclusive` | 1.41767 | 1.38567 | -0.032 | 0.234 | 0.234 | 0 |
| `agent_service_acceleration_1h` | 0.82405 | 0.820467 | -0.00358333 | 0 | 0 | 0 |
| `agent_wallet_growth_ratio_7d` | 0.550931 | 0.521531 | -0.0293995 | 0 | 0 | 0 |
| `agent_new_wallet_share_7d` | 0.187763 | 0.0560343 | -0.131728 | 1.66667e-05 | 0.000666667 | 0.00065 |
| `agent_top2_count_share_24h` | 0.497524 | 0.503856 | 0.00633153 | 0.234 | 0.234 | 0 |
| `agent_top2_share_change_24h` | -0.068591 | -0.0749255 | -0.00633457 | 0.00075 | 0.000866667 | 0.000116667 |
| `agent_cash_value_skew_24h` | -0.0375374 | -0.0192564 | 0.018281 | 0.27505 | 0.276733 | 0.00168333 |
| `agent_cash_count_skew_24h` | -0.0280869 | -0.0341042 | -0.00601733 | 0.3828 | 0.379733 | -0.00306667 |
| `agent_cash_value_skew_change` | -0.36743 | -0.378216 | -0.0107861 | 1.66667e-05 | 0.000133333 | 0.000116667 |
| `wallet_history_coverage_days` | 25.6989 | 25.6552 | -0.0436739 | 0.0075 | 0.00766667 | 0.000166667 |
| `receiver_history_coverage_days` | 25.6887 | 25.6559 | -0.0327994 | 0.00583333 | 0.0062 | 0.000366667 |
| `agent_history_coverage_days` | 19.7492 | 19.7703 | 0.021033 | 0.2356 | 0.2356 | 0 |

- Largest zero-rate shift example: `current_return_path_length` changes by -5.450 percentage points.
- Largest zero-rate shift example: `receiver_inflow_acceleration_24h` changes by 0.953 percentage points.
- Largest zero-rate shift example: `receiver_unique_sources_24h_inclusive` changes by 0.877 percentage points.

Raw mean differences have different units and should not be ranked as if they were comparable standardized effects. Coverage, path and agent quantities are included individually in the table.

## 8. Target overlap and oracle-leakage evidence

Every saved feature range overlaps between target 0 and target 1 in both partitions. This excludes strict disjoint-range separation in these samples. It does not rule out a near-perfect separator, a non-monotonic encoding, or a simple feature combination. No classifier was trained, and no features were selected or removed using these diagnostics.

### Train by target

| Feature | Target | N | Min | Max | Mean | Median | Q05 | Q95 | Ranges overlap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `current_amount_usd` | 0 | 39781 | 1 | 24999 | 3391.06 | 179.28 | 7.37 | 19475.1 | True |
| `current_amount_usd` | 1 | 20219 | 1 | 24995.9 | 3317.64 | 218 | 8.41 | 18989.4 | True |
| `current_is_cash_in` | 0 | 39781 | 0 | 1 | 0.249642 | 0 | 0 | 1 | True |
| `current_is_cash_in` | 1 | 20219 | 0 | 1 | 0.262575 | 0 | 0 | 1 | True |
| `current_is_cash_out` | 0 | 39781 | 0 | 1 | 0.236947 | 0 | 0 | 1 | True |
| `current_is_cash_out` | 1 | 20219 | 0 | 1 | 0.287551 | 0 | 0 | 1 | True |
| `wallet_count_1h_inclusive` | 0 | 39781 | 1 | 17 | 1.14311 | 1 | 1 | 2 | True |
| `wallet_count_1h_inclusive` | 1 | 20219 | 1 | 22 | 1.75083 | 1 | 1 | 6 | True |
| `wallet_value_24h_inclusive` | 0 | 39781 | 1 | 220444 | 6910.16 | 620.89 | 13 | 26339.1 | True |
| `wallet_value_24h_inclusive` | 1 | 20219 | 1 | 392344 | 13247.8 | 3908.93 | 19.879 | 48322.6 | True |
| `wallet_count_utc_day_inclusive` | 0 | 39781 | 1 | 23 | 1.59312 | 1 | 1 | 4 | True |
| `wallet_count_utc_day_inclusive` | 1 | 20219 | 1 | 27 | 3.19981 | 1 | 1 | 11 | True |
| `wallet_active_hours_utc_day` | 0 | 39781 | 1 | 11 | 1.41967 | 1 | 1 | 3 | True |
| `wallet_active_hours_utc_day` | 1 | 20219 | 1 | 15 | 2.05653 | 1 | 1 | 6 | True |
| `wallet_current_amount_cluster_share_7d` | 0 | 39781 | 0.0243902 | 1 | 0.314822 | 0.25 | 0.0769231 | 1 | True |
| `wallet_current_amount_cluster_share_7d` | 1 | 20219 | 0.025 | 1 | 0.267536 | 0.2 | 0.0555556 | 0.714286 | True |
| `wallet_band_share_7d_inclusive` | 0 | 39781 | 0 | 1 | 0.0592787 | 0 | 0 | 0.333333 | True |
| `wallet_band_share_7d_inclusive` | 1 | 20219 | 0 | 1 | 0.0573211 | 0 | 0 | 0.333333 | True |
| `wallet_count_acceleration_1h` | 0 | 39781 | -1 | 10 | 0.622433 | 1 | -1 | 2 | True |
| `wallet_count_acceleration_1h` | 1 | 20219 | -1 | 22 | 1.65953 | 1 | 1 | 6 | True |
| `receiver_unique_sources_24h_inclusive` | 0 | 39781 | 0 | 12 | 0.839672 | 1 | 0 | 2 | True |
| `receiver_unique_sources_24h_inclusive` | 1 | 20219 | 0 | 12 | 1.09135 | 1 | 0 | 4 | True |
| `receiver_inflow_count_24h_inclusive` | 0 | 39781 | 0 | 21 | 0.878585 | 1 | 0 | 2 | True |
| `receiver_inflow_count_24h_inclusive` | 1 | 20219 | 0 | 21 | 1.29032 | 1 | 0 | 5 | True |
| `receiver_inflow_acceleration_24h` | 0 | 39781 | -1 | 21 | 0.440121 | 0 | -1 | 2 | True |
| `receiver_inflow_acceleration_24h` | 1 | 20219 | -1 | 21 | 1.15157 | 1 | 0 | 5 | True |
| `sender_unique_destinations_24h_inclusive` | 0 | 39781 | 0 | 12 | 0.952163 | 1 | 0 | 3 | True |
| `sender_unique_destinations_24h_inclusive` | 1 | 20219 | 0 | 14 | 1.92092 | 1 | 0 | 7 | True |
| `sender_outflow_count_24h_inclusive` | 0 | 39781 | 0 | 16 | 0.987305 | 1 | 0 | 3 | True |
| `sender_outflow_count_24h_inclusive` | 1 | 20219 | 0 | 22 | 2.29457 | 1 | 0 | 9 | True |
| `sender_outflow_acceleration_24h` | 0 | 39781 | -1 | 16 | 0.493594 | 1 | -1 | 2 | True |
| `sender_outflow_acceleration_24h` | 1 | 20219 | -1 | 20 | 2.12717 | 1 | 0 | 9 | True |
| `current_return_path_length` | 0 | 39781 | 0 | 5 | 0.155652 | 0 | 0 | 0 | True |
| `current_return_path_length` | 1 | 20219 | 0 | 5 | 0.155844 | 0 | 0 | 0 | True |
| `current_return_amount_ratio` | 0 | 39781 | -1 | 24796.8 | 4.12244 | -1 | -1 | -1 | True |
| `current_return_amount_ratio` | 1 | 20219 | -1 | 5249 | 2.9654 | -1 | -1 | -1 | True |
| `wallet_observed_onward_funding_share_24h` | 0 | 39781 | -1 | 19025.8 | 4.76344 | 0.53159 | 0 | 2.81997 | True |
| `wallet_observed_onward_funding_share_24h` | 1 | 20219 | -1 | 4434.25 | 1.14628 | 0.551732 | 0 | 2.00255 | True |
| `wallet_prior_funding_age_hours` | 0 | 39781 | -1 | 4318.49 | 1407.14 | 1038.99 | 0 | 3849.82 | True |
| `wallet_prior_funding_age_hours` | 1 | 20219 | -1 | 4310.76 | 1635.41 | 1542.14 | 0 | 3931.77 | True |
| `agent_service_count_1h_inclusive` | 0 | 39781 | 0 | 29 | 1.02682 | 1 | 0 | 3 | True |
| `agent_service_count_1h_inclusive` | 1 | 20219 | 0 | 26 | 2.18666 | 1 | 0 | 8 | True |
| `agent_service_acceleration_1h` | 0 | 39781 | -1 | 23 | 0.226389 | 1 | -1 | 2 | True |
| `agent_service_acceleration_1h` | 1 | 20219 | -1 | 26 | 1.99995 | 1 | -1 | 8 | True |
| `agent_wallet_growth_ratio_7d` | 0 | 39781 | -1 | 20 | 0.0665733 | 0.5 | -1 | 1.38095 | True |
| `agent_wallet_growth_ratio_7d` | 1 | 20219 | -1 | 14 | 1.50391 | 1.57895 | -1 | 3.90909 | True |
| `agent_new_wallet_share_7d` | 0 | 39781 | -1 | 1 | -0.0138305 | 0.571429 | -1 | 1 | True |
| `agent_new_wallet_share_7d` | 1 | 20219 | -1 | 1 | 0.584398 | 0.870588 | -1 | 1 | True |
| `agent_top2_count_share_24h` | 0 | 39781 | 0 | 1 | 0.483972 | 0.5 | 0 | 1 | True |
| `agent_top2_count_share_24h` | 1 | 20219 | 0 | 1 | 0.524188 | 0.529412 | 0 | 1 | True |
| `agent_top2_share_change_24h` | 0 | 39781 | -1 | 0.957447 | -0.200507 | 0.114349 | -1 | 0.848485 | True |
| `agent_top2_share_change_24h` | 1 | 20219 | -1 | 0.96 | 0.190954 | 0.33438 | -1 | 0.830508 | True |
| `agent_cash_value_skew_24h` | 0 | 39781 | -1 | 1 | -0.0268796 | 0 | -1 | 1 | True |
| `agent_cash_value_skew_24h` | 1 | 20219 | -1 | 1 | -0.0585066 | 0 | -1 | 1 | True |
| `agent_cash_count_skew_24h` | 0 | 39781 | -1 | 1 | -0.0215012 | 0 | -1 | 1 | True |
| `agent_cash_count_skew_24h` | 1 | 20219 | -1 | 1 | -0.0410442 | 0 | -1 | 1 | True |
| `agent_cash_value_skew_change` | 0 | 39781 | -2 | 2 | -0.463956 | -1 | -1.13115 | 1.19313 | True |
| `agent_cash_value_skew_change` | 1 | 20219 | -1.99042 | 1.99902 | -0.177515 | -0.362679 | -1.26001 | 1.30192 | True |
| `wallet_history_coverage_days` | 0 | 39781 | 0 | 28 | 24.7034 | 28 | 5.74623 | 28 | True |
| `wallet_history_coverage_days` | 1 | 20219 | 0.00929812 | 28 | 27.6574 | 28 | 28 | 28 | True |
| `receiver_history_coverage_days` | 0 | 39781 | 0 | 28 | 24.6952 | 28 | 5.79795 | 28 | True |
| `receiver_history_coverage_days` | 1 | 20219 | 0.0116898 | 28 | 27.6433 | 28 | 28 | 28 | True |
| `agent_history_coverage_days` | 0 | 39781 | 0 | 28 | 17.5515 | 28 | 0 | 28 | True |
| `agent_history_coverage_days` | 1 | 20219 | 0 | 28 | 24.0733 | 28 | 0 | 28 | True |

### Validation by target

| Feature | Target | N | Min | Max | Mean | Median | Q05 | Q95 | Ranges overlap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `current_amount_usd` | 0 | 9945 | 1 | 24979 | 3330.52 | 172.61 | 6.732 | 19374.2 | True |
| `current_amount_usd` | 1 | 5055 | 1 | 24980.3 | 3161.37 | 203 | 7.88 | 19418.4 | True |
| `current_is_cash_in` | 0 | 9945 | 0 | 1 | 0.249874 | 0 | 0 | 1 | True |
| `current_is_cash_in` | 1 | 5055 | 0 | 1 | 0.262117 | 0 | 0 | 1 | True |
| `current_is_cash_out` | 0 | 9945 | 0 | 1 | 0.237406 | 0 | 0 | 1 | True |
| `current_is_cash_out` | 1 | 5055 | 0 | 1 | 0.286647 | 0 | 0 | 1 | True |
| `wallet_count_1h_inclusive` | 0 | 9945 | 1 | 19 | 1.18502 | 1 | 1 | 2 | True |
| `wallet_count_1h_inclusive` | 1 | 5055 | 1 | 18 | 1.70742 | 1 | 1 | 6 | True |
| `wallet_value_24h_inclusive` | 0 | 9945 | 1 | 122427 | 6916.17 | 584.9 | 11.76 | 26686.5 | True |
| `wallet_value_24h_inclusive` | 1 | 5055 | 1 | 235883 | 12712.3 | 3214 | 20 | 49106.7 | True |
| `wallet_count_utc_day_inclusive` | 0 | 9945 | 1 | 22 | 1.65008 | 1 | 1 | 4 | True |
| `wallet_count_utc_day_inclusive` | 1 | 5055 | 1 | 23 | 3.1911 | 2 | 1 | 11 | True |
| `wallet_active_hours_utc_day` | 0 | 9945 | 1 | 10 | 1.41357 | 1 | 1 | 3 | True |
| `wallet_active_hours_utc_day` | 1 | 5055 | 1 | 13 | 2.09219 | 1 | 1 | 6 | True |
| `wallet_current_amount_cluster_share_7d` | 0 | 9945 | 0.0285714 | 1 | 0.313977 | 0.25 | 0.0769231 | 1 | True |
| `wallet_current_amount_cluster_share_7d` | 1 | 5055 | 0.025 | 1 | 0.258467 | 0.2 | 0.0526316 | 0.625 | True |
| `wallet_band_share_7d_inclusive` | 0 | 9945 | 0 | 1 | 0.0591242 | 0 | 0 | 0.333333 | True |
| `wallet_band_share_7d_inclusive` | 1 | 5055 | 0 | 1 | 0.0560444 | 0 | 0 | 0.333333 | True |
| `wallet_count_acceleration_1h` | 0 | 9945 | -1 | 11 | 0.623831 | 1 | -1 | 2 | True |
| `wallet_count_acceleration_1h` | 1 | 5055 | -1 | 18 | 1.58793 | 1 | 1 | 5 | True |
| `receiver_unique_sources_24h_inclusive` | 0 | 9945 | 0 | 13 | 0.817496 | 1 | 0 | 2 | True |
| `receiver_unique_sources_24h_inclusive` | 1 | 5055 | 0 | 13 | 1.08309 | 1 | 0 | 4 | True |
| `receiver_inflow_count_24h_inclusive` | 0 | 9945 | 0 | 18 | 0.85279 | 1 | 0 | 2 | True |
| `receiver_inflow_count_24h_inclusive` | 1 | 5055 | 0 | 18 | 1.27873 | 1 | 0 | 5 | True |
| `receiver_inflow_acceleration_24h` | 0 | 9945 | -1 | 18 | 0.421317 | 0 | -1 | 2 | True |
| `receiver_inflow_acceleration_24h` | 1 | 5055 | -1 | 18 | 1.13828 | 1 | 0 | 5 | True |
| `sender_unique_destinations_24h_inclusive` | 0 | 9945 | 0 | 12 | 0.963499 | 1 | 0 | 3 | True |
| `sender_unique_destinations_24h_inclusive` | 1 | 5055 | 0 | 13 | 1.95173 | 1 | 0 | 7 | True |
| `sender_outflow_count_24h_inclusive` | 0 | 9945 | 0 | 16 | 1.01649 | 1 | 0 | 3 | True |
| `sender_outflow_count_24h_inclusive` | 1 | 5055 | 0 | 18 | 2.30148 | 1 | 0 | 9 | True |
| `sender_outflow_acceleration_24h` | 0 | 9945 | -1 | 12 | 0.482229 | 0 | -1 | 2 | True |
| `sender_outflow_acceleration_24h` | 1 | 5055 | -1 | 18 | 2.07892 | 1 | 0 | 9 | True |
| `current_return_path_length` | 0 | 9945 | 0 | 5 | 0.375264 | 0 | 0 | 4 | True |
| `current_return_path_length` | 1 | 5055 | 0 | 5 | 0.308408 | 0 | 0 | 3 | True |
| `current_return_amount_ratio` | 0 | 9945 | -1 | 3854.45 | 6.24143 | -1 | -1 | 1.14323 | True |
| `current_return_amount_ratio` | 1 | 5055 | -1 | 6167 | 7.64825 | -1 | -1 | 0.719625 | True |
| `wallet_observed_onward_funding_share_24h` | 0 | 9945 | -1 | 1506.14 | 2.59618 | 0.552047 | 0 | 2.53845 | True |
| `wallet_observed_onward_funding_share_24h` | 1 | 5055 | -1 | 507.579 | 1.18306 | 0.603066 | 0 | 2.10852 | True |
| `wallet_prior_funding_age_hours` | 0 | 9945 | -1 | 4317.62 | 1346.32 | 998.589 | 0 | 3790.97 | True |
| `wallet_prior_funding_age_hours` | 1 | 5055 | -1 | 4295.84 | 1636.26 | 1489.4 | 0 | 3884.76 | True |
| `agent_service_count_1h_inclusive` | 0 | 9945 | 0 | 15 | 0.987531 | 1 | 0 | 3 | True |
| `agent_service_count_1h_inclusive` | 1 | 5055 | 0 | 22 | 2.16894 | 1 | 0 | 8 | True |
| `agent_service_acceleration_1h` | 0 | 9945 | -1 | 6 | 0.23268 | 1 | -1 | 2 | True |
| `agent_service_acceleration_1h` | 1 | 5055 | -1 | 22 | 1.97685 | 1 | -1 | 8 | True |
| `agent_wallet_growth_ratio_7d` | 0 | 9945 | -1 | 6.4 | 0.0812293 | 0.553846 | -1 | 1.39535 | True |
| `agent_wallet_growth_ratio_7d` | 1 | 5055 | -1 | 11 | 1.38776 | 1.56 | -1 | 3.33333 | True |
| `agent_new_wallet_share_7d` | 0 | 9945 | -1 | 1 | -0.126856 | 0.3 | -1 | 0.933333 | True |
| `agent_new_wallet_share_7d` | 1 | 5055 | -1 | 1 | 0.415845 | 0.627907 | -1 | 0.974359 | True |
| `agent_top2_count_share_24h` | 0 | 9945 | 0 | 1 | 0.497486 | 0.5 | 0 | 1 | True |
| `agent_top2_count_share_24h` | 1 | 5055 | 0 | 1 | 0.516387 | 0.5 | 0 | 1 | True |
| `agent_top2_share_change_24h` | 0 | 9945 | -1 | 0.934066 | -0.194863 | 0.13486 | -1 | 0.836478 | True |
| `agent_top2_share_change_24h` | 1 | 5055 | -1 | 0.9375 | 0.161035 | 0.285714 | -1 | 0.818182 | True |
| `agent_cash_value_skew_24h` | 0 | 9945 | -1 | 1 | -0.0238294 | 0 | -1 | 1 | True |
| `agent_cash_value_skew_24h` | 1 | 5055 | -1 | 1 | -0.0102595 | 0 | -1 | 1 | True |
| `agent_cash_count_skew_24h` | 0 | 9945 | -1 | 1 | -0.031246 | 0 | -1 | 1 | True |
| `agent_cash_count_skew_24h` | 1 | 5055 | -1 | 1 | -0.0397273 | 0 | -1 | 1 | True |
| `agent_cash_value_skew_change` | 0 | 9945 | -1.99734 | 1.99703 | -0.485016 | -1 | -1.17088 | 1.13291 | True |
| `agent_cash_value_skew_change` | 1 | 5055 | -1.99526 | 1.9937 | -0.168103 | -0.301345 | -1.23738 | 1.25315 | True |
| `wallet_history_coverage_days` | 0 | 9945 | 0 | 28 | 24.6933 | 28 | 5.58959 | 28 | True |
| `wallet_history_coverage_days` | 1 | 5055 | 3.34677 | 28 | 27.5475 | 28 | 28 | 28 | True |
| `receiver_history_coverage_days` | 0 | 9945 | 0 | 28 | 24.6916 | 28 | 5.62243 | 28 | True |
| `receiver_history_coverage_days` | 1 | 5055 | 3.48809 | 28 | 27.553 | 28 | 28 | 28 | True |
| `agent_history_coverage_days` | 0 | 9945 | 0 | 28 | 17.6585 | 28 | 0 | 28 | True |
| `agent_history_coverage_days` | 1 | 5055 | 0 | 28 | 23.9249 | 28 | 0 | 28 | True |

## 9. Preprocessing diagnosis

| Category | Examples | Future treatment |
| --- | --- | --- |
| Binary | Current Cash-In/Cash-Out indicators | Retain their meaning; no fitted transform was applied. |
| Count | Activity counts, source/destination counts | Review skew and outliers; any clipping or scaling must be learned on Train only. |
| Positive amounts and ratios | Current USD, cumulative USD, acceleration, return amount ratio | Consider log/scaling after semantic corrections and sentinel handling are fixed. |
| Bounded shares and signed quantities | Cluster share, top-two share, cash skews | Preserve legitimate negative values; do not indiscriminately treat -1 as missing. |
| Coverage and topology | Coverage 0..28 days, path length 0..5 | Preserve interpretable units; resolve temporal-path correctness before modeling. |

No final preprocessing parameters were fitted. Missing-value semantics must be resolved first, especially for signed changes. Validation must never supply fitted clipping/scaling parameters.

## 10. Reproducibility and protection

| Property | Recorded value |
| --- | --- |
| Row order identical | True |
| Feature order identical | True |
| Numeric values identical | True |
| Targets identical | True |
| Protected files before / after | 83 / 83 |
| Changed protected paths | [] |

The prior session also compared allowed development files against the frozen Stage 9 development manifest and reported an empty changed set. That console check is not captured as a dedicated before/after development-input record in the Stage 10 JSON. No evaluation bytes were needed for these development checks. The public holdout certificate existence check is narrower than commitment-content verification.

| Partition | Output | Recorded SHA-256 |
| --- | --- | --- |
| train | X.csv | `bfcce0de1d31dec266080d6510d73d909387eb802de3f5c8c848a4ec12b66076` |
| train | feature_names.json | `07f0d1b3c07980b5cad5c3c73fa7f5105b68721a3c27d587427776230d32d1c6` |
| train | row_ids.csv | `9c0f0031ec2f9e47f4283ee6dfa0268f68bbabdd9a4558c7217dd4cdb3a83c16` |
| train | y.csv | `87649361df2fd9ab75bb5c5e0b8f4889efc74262ad3ebe9b7da8570f11563321` |
| validation | X.csv | `af658f9a64c25d7d564f4d6d445fffd8bfbe6a5b78d5b5fc550a6467a4b5a8a6` |
| validation | feature_names.json | `07f0d1b3c07980b5cad5c3c73fa7f5105b68721a3c27d587427776230d32d1c6` |
| validation | row_ids.csv | `faf5ae1be1a094504805f5f0a1721308e98a286b22585e7d33ad33fc95a004d2` |
| validation | y.csv | `adb5ab90732288e1b496c897b57afdfe9f6151d807e530fd47e87435166488ea` |

## 11. Evidence index and decision

| Evidence | Contents |
| --- | --- |
| [stage10_feature_statistics.json](stage10_feature_statistics.json) | Matrix integrity and all feature statistics |
| [stage10_shift_audit.json](stage10_shift_audit.json) | Train/Validation comparisons |
| [stage10_target_overlap.json](stage10_target_overlap.json) | Both target distributions for every feature |
| [stage10_temporal_tests.json](stage10_temporal_tests.json) | Limited temporal, metadata and name checks |
| [stage10_reproducibility.json](stage10_reproducibility.json) | In-memory equality, output hashes and protection results |

The feature construction artifacts exist and the saved checks pass within their stated scope. Full Stage 10 approval should wait for the semantic discrepancies and missing checks in Section 4 to be addressed. This report supersedes the unqualified PASS interpretation of the earlier split summaries. Model training remains outside the completed work.

## Appendix A. Original recorded feature contract

The contract below is reproduced as recorded; it is not a revised contract or confirmation that every declaration matches the code. The consolidation findings above take precedence when interpreting compliance.

### MODEL V3 ? STAGE 10 FEATURE CONTRACT

**Status: FROZEN BEFORE MATRIX EXTRACTION**

The representation contains exactly 32 ordered numeric features. Missing or ineligible ratios use the finite sentinel `-1.0`; legitimate zero remains `0.0`. Every history lookup is partition-local and uses `(event_timestamp, transaction_id) < current key`. State is updated only after the current vector is emitted.

#### Ordered feature list

1. `current_amount_usd` ? **current** ? current transaction amount / 100 USD ? `current`
2. `current_is_cash_in` ? **current** ? 1 iff current transaction_type is cash_in ? `current`
3. `current_is_cash_out` ? **current** ? 1 iff current transaction_type is cash_out ? `current`
4. `wallet_count_1h_inclusive` ? **structuring** ? count of subject-wallet events in [T-1h,T] ? `prior+current`
5. `wallet_value_24h_inclusive` ? **structuring** ? sum of subject-wallet amounts in [T-24h,T] ? `prior+current`
6. `wallet_count_utc_day_inclusive` ? **structuring** ? count of subject-wallet events since UTC midnight through T ? `prior+current`
7. `wallet_active_hours_utc_day` ? **structuring** ? distinct UTC hour buckets for subject-wallet events since midnight through T ? `prior+current`
8. `wallet_current_amount_cluster_share_7d` ? **structuring** ? share of subject-wallet events in [T-7d,T] within 5% of current amount ? `prior+current`
9. `wallet_band_share_7d_inclusive` ? **structuring** ? share of subject-wallet events in [T-7d,T] in 7000..10500 USD ? `prior+current`
10. `wallet_count_acceleration_1h` ? **structuring** ? inclusive 1h count / max(1, prior-28d count / 672) ? `prior+current`
11. `receiver_unique_sources_24h_inclusive` ? **network** ? distinct W2W senders to receiver in [T-24h,T] ? `prior+current`
12. `receiver_inflow_count_24h_inclusive` ? **network** ? W2W inflow count to receiver in [T-24h,T] ? `prior+current`
13. `receiver_inflow_acceleration_24h` ? **network** ? inclusive receiver inflow count / max(1, prior-28d inflow count / 28) ? `prior+current`
14. `sender_unique_destinations_24h_inclusive` ? **network** ? distinct W2W receivers from sender in [T-24h,T] ? `prior+current`
15. `sender_outflow_count_24h_inclusive` ? **network** ? W2W outflow count from sender in [T-24h,T] ? `prior+current`
16. `sender_outflow_acceleration_24h` ? **network** ? inclusive sender outflow count / max(1, prior-28d count / 28) ? `prior+current`
17. `current_return_path_length` ? **network** ? shortest simple prior path receiver to sender, 1..5 edges in 7d; zero otherwise ? `prior-only plus current endpoints`
18. `current_return_amount_ratio` ? **network** ? current amount / first-edge amount of selected prior return path; -1 when absent ? `prior-only plus current amount`
19. `wallet_observed_onward_funding_share_24h` ? **network** ? observed outward value after prior funding anchor / observed funding value ? `prior+current for outflow`
20. `wallet_prior_funding_age_hours` ? **network** ? hours from prior funding anchor to current outflow; -1 when absent ? `prior-only plus current timestamp`
21. `agent_service_count_1h_inclusive` ? **agent** ? agent service-event count in [T-1h,T]; zero for direct W2W ? `prior+current`
22. `agent_service_acceleration_1h` ? **agent** ? inclusive service count / max(1, preceding-28d service count / 672); -1 if coverage insufficient ? `prior+current`
23. `agent_wallet_growth_ratio_7d` ? **agent** ? recent inclusive distinct serviced wallets / max(1, median of four preceding 7d counts); -1 if insufficient ? `prior+current`
24. `agent_new_wallet_share_7d` ? **agent** ? recent serviced-wallet fraction absent from preceding-28d wallet union; -1 if insufficient ? `prior+current`
25. `agent_top2_count_share_24h` ? **agent** ? top-two serviced-wallet service-event share in [T-24h,T] ? `prior+current`
26. `agent_top2_share_change_24h` ? **agent** ? inclusive top-two share minus preceding-28d top-two share; -1 if insufficient ? `prior+current`
27. `agent_cash_value_skew_24h` ? **agent** ? (CashOut value-CashIn value)/(sum) in [T-24h,T] ? `prior+current`
28. `agent_cash_count_skew_24h` ? **agent** ? corresponding signed event-count skew in [T-24h,T] ? `prior+current`
29. `agent_cash_value_skew_change` ? **agent** ? inclusive cash value skew minus preceding-28d cash value skew; -1 if insufficient ? `prior+current`
30. `wallet_history_coverage_days` ? **coverage** ? partition-local subject-wallet observation span before T, capped at 28 days ? `prior-only`
31. `receiver_history_coverage_days` ? **coverage** ? partition-local receiver observation span before T, capped at 28 days ? `prior-only`
32. `agent_history_coverage_days` ? **coverage** ? partition-local agent observation span before T, capped at 28 days; zero without agent ? `prior-only`

#### Per-feature contract

##### 1. `current_amount_usd`

- **Behavioural domain / subject:** The subject is the current transaction or its observable principal endpoint. Current amount/type facts are used; no prior state is required. Cash-In sets only the Cash-In indicator, Cash-Out sets only the Cash-Out indicator, and W2W sets both to zero. Cold start is a valid amount/type value; no denominator applies.
- **Mathematical definition:** current transaction amount / 100 USD.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 2. `current_is_cash_in`

- **Behavioural domain / subject:** The subject is the current transaction or its observable principal endpoint. Current amount/type facts are used; no prior state is required. Cash-In sets only the Cash-In indicator, Cash-Out sets only the Cash-Out indicator, and W2W sets both to zero. Cold start is a valid amount/type value; no denominator applies.
- **Mathematical definition:** 1 iff current transaction_type is cash_in.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 3. `current_is_cash_out`

- **Behavioural domain / subject:** The subject is the current transaction or its observable principal endpoint. Current amount/type facts are used; no prior state is required. Cash-In sets only the Cash-In indicator, Cash-Out sets only the Cash-Out indicator, and W2W sets both to zero. Cold start is a valid amount/type value; no denominator applies.
- **Mathematical definition:** 1 iff current transaction_type is cash_out.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 4. `wallet_count_1h_inclusive`

- **Behavioural domain / subject:** The subject is `serviced_wallet` for agent-assisted events and `sender_wallet` otherwise. Cash-In, Cash-Out and W2W all contribute one subject event and its amount to wallet histories. Inclusive means prior events in the named window plus T. Empty prior history still yields current-derived zero/one quantities; acceleration is `-1.0` until 28 days of observable history.
- **Mathematical definition:** count of subject-wallet events in [T-1h,T].
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 5. `wallet_value_24h_inclusive`

- **Behavioural domain / subject:** The subject is `serviced_wallet` for agent-assisted events and `sender_wallet` otherwise. Cash-In, Cash-Out and W2W all contribute one subject event and its amount to wallet histories. Inclusive means prior events in the named window plus T. Empty prior history still yields current-derived zero/one quantities; acceleration is `-1.0` until 28 days of observable history.
- **Mathematical definition:** sum of subject-wallet amounts in [T-24h,T].
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 6. `wallet_count_utc_day_inclusive`

- **Behavioural domain / subject:** The subject is `serviced_wallet` for agent-assisted events and `sender_wallet` otherwise. Cash-In, Cash-Out and W2W all contribute one subject event and its amount to wallet histories. Inclusive means prior events in the named window plus T. Empty prior history still yields current-derived zero/one quantities; acceleration is `-1.0` until 28 days of observable history.
- **Mathematical definition:** count of subject-wallet events since UTC midnight through T.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 7. `wallet_active_hours_utc_day`

- **Behavioural domain / subject:** The subject is `serviced_wallet` for agent-assisted events and `sender_wallet` otherwise. Cash-In, Cash-Out and W2W all contribute one subject event and its amount to wallet histories. Inclusive means prior events in the named window plus T. Empty prior history still yields current-derived zero/one quantities; acceleration is `-1.0` until 28 days of observable history.
- **Mathematical definition:** distinct UTC hour buckets for subject-wallet events since midnight through T.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current timestamp and entity endpoint only.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 8. `wallet_current_amount_cluster_share_7d`

- **Behavioural domain / subject:** The subject is `serviced_wallet` for agent-assisted events and `sender_wallet` otherwise. Cash-In, Cash-Out and W2W all contribute one subject event and its amount to wallet histories. Inclusive means prior events in the named window plus T. Empty prior history still yields current-derived zero/one quantities; acceleration is `-1.0` until 28 days of observable history.
- **Mathematical definition:** share of subject-wallet events in [T-7d,T] within 5% of current amount.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 9. `wallet_band_share_7d_inclusive`

- **Behavioural domain / subject:** The subject is `serviced_wallet` for agent-assisted events and `sender_wallet` otherwise. Cash-In, Cash-Out and W2W all contribute one subject event and its amount to wallet histories. Inclusive means prior events in the named window plus T. Empty prior history still yields current-derived zero/one quantities; acceleration is `-1.0` until 28 days of observable history.
- **Mathematical definition:** share of subject-wallet events in [T-7d,T] in 7000..10500 USD.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 10. `wallet_count_acceleration_1h`

- **Behavioural domain / subject:** The subject is `serviced_wallet` for agent-assisted events and `sender_wallet` otherwise. Cash-In, Cash-Out and W2W all contribute one subject event and its amount to wallet histories. Inclusive means prior events in the named window plus T. Empty prior history still yields current-derived zero/one quantities; acceleration is `-1.0` until 28 days of observable history.
- **Mathematical definition:** inclusive 1h count / max(1, prior-28d count / 672).
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 11. `receiver_unique_sources_24h_inclusive`

- **Behavioural domain / subject:** Receiver and sender summaries use only W2W edges. Cash events contribute no network edge. Agent-assisted W2W is still a principal W2W edge; agent mediation does not change network or agent cash direction. Inclusive counts include T only when T is W2W. Missing path/funding ratios use `-1.0`; zero is reserved for a valid non-applicable role.
- **Mathematical definition:** distinct W2W senders to receiver in [T-24h,T].
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 12. `receiver_inflow_count_24h_inclusive`

- **Behavioural domain / subject:** Receiver and sender summaries use only W2W edges. Cash events contribute no network edge. Agent-assisted W2W is still a principal W2W edge; agent mediation does not change network or agent cash direction. Inclusive counts include T only when T is W2W. Missing path/funding ratios use `-1.0`; zero is reserved for a valid non-applicable role.
- **Mathematical definition:** W2W inflow count to receiver in [T-24h,T].
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 13. `receiver_inflow_acceleration_24h`

- **Behavioural domain / subject:** Receiver and sender summaries use only W2W edges. Cash events contribute no network edge. Agent-assisted W2W is still a principal W2W edge; agent mediation does not change network or agent cash direction. Inclusive counts include T only when T is W2W. Missing path/funding ratios use `-1.0`; zero is reserved for a valid non-applicable role.
- **Mathematical definition:** inclusive receiver inflow count / max(1, prior-28d inflow count / 28).
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 14. `sender_unique_destinations_24h_inclusive`

- **Behavioural domain / subject:** Receiver and sender summaries use only W2W edges. Cash events contribute no network edge. Agent-assisted W2W is still a principal W2W edge; agent mediation does not change network or agent cash direction. Inclusive counts include T only when T is W2W. Missing path/funding ratios use `-1.0`; zero is reserved for a valid non-applicable role.
- **Mathematical definition:** distinct W2W receivers from sender in [T-24h,T].
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 15. `sender_outflow_count_24h_inclusive`

- **Behavioural domain / subject:** Receiver and sender summaries use only W2W edges. Cash events contribute no network edge. Agent-assisted W2W is still a principal W2W edge; agent mediation does not change network or agent cash direction. Inclusive counts include T only when T is W2W. Missing path/funding ratios use `-1.0`; zero is reserved for a valid non-applicable role.
- **Mathematical definition:** W2W outflow count from sender in [T-24h,T].
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 16. `sender_outflow_acceleration_24h`

- **Behavioural domain / subject:** Receiver and sender summaries use only W2W edges. Cash events contribute no network edge. Agent-assisted W2W is still a principal W2W edge; agent mediation does not change network or agent cash direction. Inclusive counts include T only when T is W2W. Missing path/funding ratios use `-1.0`; zero is reserved for a valid non-applicable role.
- **Mathematical definition:** inclusive sender outflow count / max(1, prior-28d count / 28).
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 17. `current_return_path_length`

- **Behavioural domain / subject:** Receiver and sender summaries use only W2W edges. Cash events contribute no network edge. Agent-assisted W2W is still a principal W2W edge; agent mediation does not change network or agent cash direction. Inclusive counts include T only when T is W2W. Missing path/funding ratios use `-1.0`; zero is reserved for a valid non-applicable role.
- **Mathematical definition:** shortest simple prior path receiver to sender, 1..5 edges in 7d; zero otherwise.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior-only plus current endpoints`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 18. `current_return_amount_ratio`

- **Behavioural domain / subject:** Receiver and sender summaries use only W2W edges. Cash events contribute no network edge. Agent-assisted W2W is still a principal W2W edge; agent mediation does not change network or agent cash direction. Inclusive counts include T only when T is W2W. Missing path/funding ratios use `-1.0`; zero is reserved for a valid non-applicable role.
- **Mathematical definition:** current amount / first-edge amount of selected prior return path; -1 when absent.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior-only plus current amount`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 19. `wallet_observed_onward_funding_share_24h`

- **Behavioural domain / subject:** Receiver and sender summaries use only W2W edges. Cash events contribute no network edge. Agent-assisted W2W is still a principal W2W edge; agent mediation does not change network or agent cash direction. Inclusive counts include T only when T is W2W. Missing path/funding ratios use `-1.0`; zero is reserved for a valid non-applicable role.
- **Mathematical definition:** observed outward value after prior funding anchor / observed funding value.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current for outflow`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 20. `wallet_prior_funding_age_hours`

- **Behavioural domain / subject:** Receiver and sender summaries use only W2W edges. Cash events contribute no network edge. Agent-assisted W2W is still a principal W2W edge; agent mediation does not change network or agent cash direction. Inclusive counts include T only when T is W2W. Missing path/funding ratios use `-1.0`; zero is reserved for a valid non-applicable role.
- **Mathematical definition:** hours from prior funding anchor to current outflow; -1 when absent.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior-only plus current timestamp`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 21. `agent_service_count_1h_inclusive`

- **Behavioural domain / subject:** The subject is the current `agent_id` and its observed serviced wallets. Agent-assisted W2W contributes one service event and serviced wallet, while its principal amount does not enter agent Cash-In/Cash-Out direction. Direct W2W has zero agent service quantities. Inclusive service quantities include T; baseline-relative quantities use prior 28-day history and are `-1.0` before 28 days of coverage.
- **Mathematical definition:** agent service-event count in [T-1h,T]; zero for direct W2W.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 22. `agent_service_acceleration_1h`

- **Behavioural domain / subject:** The subject is the current `agent_id` and its observed serviced wallets. Agent-assisted W2W contributes one service event and serviced wallet, while its principal amount does not enter agent Cash-In/Cash-Out direction. Direct W2W has zero agent service quantities. Inclusive service quantities include T; baseline-relative quantities use prior 28-day history and are `-1.0` before 28 days of coverage.
- **Mathematical definition:** inclusive service count / max(1, preceding-28d service count / 672); -1 if coverage insufficient.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 23. `agent_wallet_growth_ratio_7d`

- **Behavioural domain / subject:** The subject is the current `agent_id` and its observed serviced wallets. Agent-assisted W2W contributes one service event and serviced wallet, while its principal amount does not enter agent Cash-In/Cash-Out direction. Direct W2W has zero agent service quantities. Inclusive service quantities include T; baseline-relative quantities use prior 28-day history and are `-1.0` before 28 days of coverage.
- **Mathematical definition:** recent inclusive distinct serviced wallets / max(1, median of four preceding 7d counts); -1 if insufficient.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 24. `agent_new_wallet_share_7d`

- **Behavioural domain / subject:** The subject is the current `agent_id` and its observed serviced wallets. Agent-assisted W2W contributes one service event and serviced wallet, while its principal amount does not enter agent Cash-In/Cash-Out direction. Direct W2W has zero agent service quantities. Inclusive service quantities include T; baseline-relative quantities use prior 28-day history and are `-1.0` before 28 days of coverage.
- **Mathematical definition:** recent serviced-wallet fraction absent from preceding-28d wallet union; -1 if insufficient.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 25. `agent_top2_count_share_24h`

- **Behavioural domain / subject:** The subject is the current `agent_id` and its observed serviced wallets. Agent-assisted W2W contributes one service event and serviced wallet, while its principal amount does not enter agent Cash-In/Cash-Out direction. Direct W2W has zero agent service quantities. Inclusive service quantities include T; baseline-relative quantities use prior 28-day history and are `-1.0` before 28 days of coverage.
- **Mathematical definition:** top-two serviced-wallet service-event share in [T-24h,T].
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 26. `agent_top2_share_change_24h`

- **Behavioural domain / subject:** The subject is the current `agent_id` and its observed serviced wallets. Agent-assisted W2W contributes one service event and serviced wallet, while its principal amount does not enter agent Cash-In/Cash-Out direction. Direct W2W has zero agent service quantities. Inclusive service quantities include T; baseline-relative quantities use prior 28-day history and are `-1.0` before 28 days of coverage.
- **Mathematical definition:** inclusive top-two share minus preceding-28d top-two share; -1 if insufficient.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 27. `agent_cash_value_skew_24h`

- **Behavioural domain / subject:** The subject is the current `agent_id` and its observed serviced wallets. Agent-assisted W2W contributes one service event and serviced wallet, while its principal amount does not enter agent Cash-In/Cash-Out direction. Direct W2W has zero agent service quantities. Inclusive service quantities include T; baseline-relative quantities use prior 28-day history and are `-1.0` before 28 days of coverage.
- **Mathematical definition:** (CashOut value-CashIn value)/(sum) in [T-24h,T].
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 28. `agent_cash_count_skew_24h`

- **Behavioural domain / subject:** The subject is the current `agent_id` and its observed serviced wallets. Agent-assisted W2W contributes one service event and serviced wallet, while its principal amount does not enter agent Cash-In/Cash-Out direction. Direct W2W has zero agent service quantities. Inclusive service quantities include T; baseline-relative quantities use prior 28-day history and are `-1.0` before 28 days of coverage.
- **Mathematical definition:** corresponding signed event-count skew in [T-24h,T].
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 29. `agent_cash_value_skew_change`

- **Behavioural domain / subject:** The subject is the current `agent_id` and its observed serviced wallets. Agent-assisted W2W contributes one service event and serviced wallet, while its principal amount does not enter agent Cash-In/Cash-Out direction. Direct W2W has zero agent service quantities. Inclusive service quantities include T; baseline-relative quantities use prior 28-day history and are `-1.0` before 28 days of coverage.
- **Mathematical definition:** inclusive cash value skew minus preceding-28d cash value skew; -1 if insufficient.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior+current`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 30. `wallet_history_coverage_days`

- **Behavioural domain / subject:** Coverage is the elapsed span from the first prior observed event for the subject entity to T, capped at 28 days. It uses no private activation or campaign metadata. No prior event gives 0.0; it is prior-only and is never an eligibility flag.
- **Mathematical definition:** partition-local subject-wallet observation span before T, capped at 28 days.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior-only`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 31. `receiver_history_coverage_days`

- **Behavioural domain / subject:** Coverage is the elapsed span from the first prior observed event for the subject entity to T, capped at 28 days. It uses no private activation or campaign metadata. No prior event gives 0.0; it is prior-only and is never an eligibility flag.
- **Mathematical definition:** partition-local receiver observation span before T, capped at 28 days.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior-only`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

##### 32. `agent_history_coverage_days`

- **Behavioural domain / subject:** Coverage is the elapsed span from the first prior observed event for the subject entity to T, capped at 28 days. It uses no private activation or campaign metadata. No prior event gives 0.0; it is prior-only and is never an eligibility flag.
- **Mathematical definition:** partition-local agent observation span before T, capped at 28 days; zero without agent.
- **Units and range:** numeric; counts are non-negative integers, shares/skews are bounded where applicable, amounts are USD, age/coverage are hours/days. Missing/ineligible value is `-1.0`.
- **Historical window:** named in the formula; all prior windows are left-inclusive and current-exclusive before adding permitted T.
- **Current information:** current T is included.
- **Prior information:** prior same-partition observable event histories only; no future rows.
- **Cash-In / Cash-Out / direct W2W / agent-assisted W2W:** Cash events affect wallet histories; only Cash-In and Cash-Out affect agent cash features. Direct and assisted W2W are network edges; assisted W2W also affects agent service history.
- **Cold start:** zero for valid count/coverage quantities; `-1.0` for an unavailable ratio, path, funding anchor or baseline comparator.
- **Zero denominator / insufficient history:** zero denominator returns 0.0 for a valid empty quantity; ratio features use `-1.0` when the required observable baseline is unavailable.
- **Temporal rule:** `prior-only`; update occurs after emission.
- **Behavioural justification:** isolates an observable amount, activity, topology, funding, service, or coverage quantity so a future classifier must learn combinations rather than receive a predicate result.

END OF STAGE 10 CONSOLIDATED REPORT - CORRECTIONS REQUIRED BEFORE APPROVAL.
