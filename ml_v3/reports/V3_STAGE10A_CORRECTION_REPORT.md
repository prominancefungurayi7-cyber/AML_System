# MODEL V3 - STAGE 10A SEMANTIC CORRECTION AND RE-AUDIT

**Result: PASS for the Stage 10A feature correction and audit scope.** 32 corrected features were independently extracted twice for 60,000 Train and 15,000 Validation transactions. Both serialized output sets matched. All 27 expanded hand-test methods passed, and frozen targets were preserved. No classifier was trained or evaluated.

This is the **single main report**. It contains the correction decisions, matrix results, test expectations, distributions, shift, leakage audit, reproducibility, protection and full corrected contract. The separately requested Markdown files are supporting entry points; machine-readable records retain the detailed counts and hashes.

## 1. Scope, status and artifact use

Use `ml_v3/features/development/stage10a/train/` and `ml_v3/features/development/stage10a/validation/` for the corrected development artifacts. Each contains `X.csv`, `y.csv`, `row_ids.csv` and `feature_names.json`. Their parent `version.json` identifies `v3_stage10a_features_1` and its contract digest. Original Stage 10 matrices under `features/development/train/` and `validation/` are **superseded**, preserved unchanged as audit evidence. The original contract and overall report were also preserved.

The frozen V3 raw dataset, ground truth and predicates were not changed. Only Train/Validation transactions were extracted. Targets were aligned by transaction ID from `decision_point_target`; diagnostic family evidence was used after extraction solely for the leakage audit. Feature extraction projects eight observable event fields and never receives target, family, witness, onset or provenance fields as inputs.

No Final Test or Independent Evaluation directory was enumerated or data file opened in this stage. Public commitment certificates were checked by their explicit allowed paths. This is a feature-semantics result, not model performance or permission to begin training. No fitted preprocessing, threshold search or application integration took place.

## 2. Resolution of all ten findings

| Finding | Correction and verification |
|---|---|
| A. N3 temporal paths | Traversal enforces `key(e1) < ... < key(ek) < key(T)`, simple nodes, 1..5 edges, open 7d lower boundary. Hand cases include reversed/partial-reversed paths, ties, five/six edges, future edges and current closure. |
| B. Equal timestamps | All histories filter by full `(UTC timestamp, integer ID)` keys. Smaller same-time IDs are prior; larger IDs are future. State updates once after emission. Network, wallet, agent, funding, coverage, baseline and path cases are tested. |
| C. Funding window | Earliest eligible prior W2W anchor must be inside `(t-24h,t]`. Cash-In contributes only from that anchor onward. Every observed age is nonnegative and strictly below 24h; the former ~4318h age is gone. |
| D. Baselines | Every recent window has its disjoint preceding 28d baseline. Uncapped first-observation coverage and relevant event minima are enforced. Eligibility cannot be supplied by recent events. |
| E. Missing values | Nonnegative unavailable quantities retain -1; signed changes use -3 outside their valid domains. Raw cash skews retain valid -1 and have no missing marker. No feature-count increase. |
| F. Novelty | Fraction of DISTINCT recent wallets absent from the baseline union. Three visits to new plus one visit to old gives 1/2, not 3/4. |
| G. Oracle audit | Observable-input projection, private-field mutation, source review, direct/inverse target checks, single-value mappings, monotone separation, all 496 numeric pairs and fixed condition combinations; frozen family outcomes also checked. |
| H. Serialized repeatability | Two independent stateful extractions reload frozen development inputs, write separate temporary file sets, round-trip them and compare numeric/target/ID/order values and every output hash. |
| I. Protection | Explicit before/after inventories cover application/V1/V2 allowlists, frozen V3 development inputs, design, earlier reports/matrices and named public commitments. No holdout traversal. |
| J. Contract freeze | Versioned corrected contract, ordered 32-column schema and implementation hashes were written before full extraction. Original contract digest is recorded as observed now, without a claim of a historical prehash. |

An additional correction makes assisted W2W use the **sender** for structuring/funding, while agent-service summaries still use the explicitly serviced wallet. Receiver receipts establish observable coverage and inflow history without becoming outgoing wallet activity.

### Authority resolutions

The [Stage 8 onset contract](../design/V3_SCENARIO_ONSET_CONTRACT.md) and [feature architecture](../design/V3_FEATURE_ARCHITECTURE_PROPOSAL.md) distinguish feature summaries from full ground-truth predicates. N3's architectural feature selects a chronological path by topology; current/first-edge amount is a separate ratio. It does not apply the full predicate's adjacent-amount or return-ratio gates. Tests deliberately retain a chronological path with an amount ratio outside those gates. The selected path is a lossy summary when several paths exist.

N4's frozen anchor is a prior **W2W inflow**. A Cash-In-only history therefore has no qualifying anchor, including Cash-In 23h59m earlier. Cash-In at/after an eligible W2W anchor contributes funding and is within the 24h interval. Broadening the anchor to Cash-In alone would alter the frozen design. Every W2W is evaluated as an outward edge of its sender; no private episode role is inferred to force an inbound/funding label.

## 3. Matrix integrity and feature order

| Partition | Rows | Columns | Target 0 | Target 1 | NaN | Infinity | Duplicate IDs | Range check |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | 60000 | 32 | 39781 | 20219 | 0 | 0 | 0 | PASS |
| validation | 15000 | 32 | 9945 | 5055 | 0 | 0 | 0 | PASS |

The logical and serialized counts are both 32: current 3, structuring 7, network 10, agent 9, coverage 3. CSV stores decimal numeric text; extraction uses Python binary64 floats after integer minor-unit arithmetic. Counts/indicators/path length are integer-valued. IDs are separate from X. Exact ordered definitions, ranges, units, cold-start and temporal rules are reproduced in Appendix A.

| Position | Feature | Domain | Valid range | Missing marker |
| --- | --- | --- | --- | --- |
| 1 | `current_amount_usd` | current | 0..unbounded | none |
| 2 | `current_is_cash_in` | current | 0..1 | none |
| 3 | `current_is_cash_out` | current | 0..1 | none |
| 4 | `wallet_count_1h_inclusive` | structuring | 1..unbounded | none |
| 5 | `wallet_value_24h_inclusive` | structuring | 0..unbounded | none |
| 6 | `wallet_count_utc_day_inclusive` | structuring | 1..unbounded | none |
| 7 | `wallet_active_hours_utc_day` | structuring | 1..24 | none |
| 8 | `wallet_current_amount_cluster_share_7d` | structuring | 0..1 | none |
| 9 | `wallet_band_share_7d_inclusive` | structuring | 0..1 | none |
| 10 | `wallet_count_acceleration_1h` | structuring | 0..unbounded | -1 |
| 11 | `receiver_unique_sources_24h_inclusive` | network | 0..unbounded | none |
| 12 | `receiver_inflow_count_24h_inclusive` | network | 0..unbounded | none |
| 13 | `receiver_inflow_acceleration_24h` | network | 0..unbounded | -1 |
| 14 | `sender_unique_destinations_24h_inclusive` | network | 0..unbounded | none |
| 15 | `sender_outflow_count_24h_inclusive` | network | 0..unbounded | none |
| 16 | `sender_outflow_acceleration_24h` | network | 0..unbounded | -1 |
| 17 | `current_return_path_length` | network | 0..5 | none |
| 18 | `current_return_amount_ratio` | network | 0..unbounded | -1 |
| 19 | `wallet_observed_onward_funding_share_24h` | network | 0..unbounded | -1 |
| 20 | `wallet_prior_funding_age_hours` | network | 0..24 | -1 |
| 21 | `agent_service_count_1h_inclusive` | agent | 0..unbounded | none |
| 22 | `agent_service_acceleration_1h` | agent | 0..unbounded | -1 |
| 23 | `agent_wallet_growth_ratio_7d` | agent | 0..unbounded | -1 |
| 24 | `agent_new_wallet_share_7d` | agent | 0..1 | -1 |
| 25 | `agent_top2_count_share_24h` | agent | 0..1 | none |
| 26 | `agent_top2_share_change_24h` | agent | -1..1 | -3 |
| 27 | `agent_cash_value_skew_24h` | agent | -1..1 | none |
| 28 | `agent_cash_count_skew_24h` | agent | -1..1 | none |
| 29 | `agent_cash_value_skew_change` | agent | -2..2 | -3 |
| 30 | `wallet_history_coverage_days` | coverage | 0..28 | none |
| 31 | `receiver_history_coverage_days` | coverage | 0..28 | none |
| 32 | `agent_history_coverage_days` | coverage | 0..28 | none |

Funding age has an open upper limit: valid values are **[0,24)** hours. The observed maxima are Train: **23.9998124h**, Validation: **23.9814705h**.

## 4. Temporal and manually calculated hand tests

Tests use synthetic in-memory events, integer IDs and explicit timestamps/amounts. They do not read holdouts or use model output. Values below are manually specified expected results asserted by the test suite. The test count counts methods; individual methods include multiple subcases.

| N3 case | Expected path length | Expected current/first-edge ratio |
| --- | --- | --- |
| r→m then m→s; current s→r ($50 versus first $200) | 2 | 0.25 |
| Reversed chronological two-edge route | 0 | -1 |
| Partially reversed three-edge route | 0 | -1 |
| Same timestamp, increasing IDs 1→2 then current 3 | 2 | 1 |
| Route needs an edge after current | 0 | -1 |
| Only a six-edge route | 0 | -1 |
| No return route | 0 | -1 |
| Current reciprocal closure ($50 / $200) | 1 | 0.25 |
| Valid five-edge route | 5 | 1 |
| Latest-first-edge tie ($100 / $200) | 1 | 0.5 |
| Valid chronology, monetary ratio outside predicate bands | 2 | 2000 |


| Other hand case | Expected output |
| --- | --- |
| Isolated $100 W2W | Wallet count 1, value $100, day/hour 1, cluster share 1, band share 0; no baseline/path/funding; coverage 0 |
| Four wallet events 7000,7100,100,7000 across hours 0,1,2,2 | Last-hour count 2; 24h value 21200; day count 4; active hours 3; cluster and band shares .75 |
| Four distinct collection sources / dispersion recipients | Breadth 4 and event count 4 |
| W2W funding $100 at 23h59m; current $50 out | Share .5; age 23.9833333333h |
| Anchor exactly 24h old / 24h+1s / future | Share -1 and age -1 |
| Two W2W anchors $100+$50; later Cash-In $50; two $50 outflows | F=200, O=100, share .5; earliest anchor age 2h |
| Cash-In only; current outbound | No W2W anchor: share -1 and age -1 |
| Current Cash-In itself | Share 0; age -1 |
| ID1 same-time $100 inflow; ID2 $50 Cash-Out; ID3 same-time future inflow | At ID2: receiver count 1, funding share .5, age 0, agent service count 2 |
| Wallet baseline 4 events plus full coverage / only 3 events | Acceleration 1 / missing -1; recent events cannot fill baseline minimum |
| 1344 wallet baseline events, two recent events | Expected hourly baseline 2; acceleration 2/2=1 |
| Agent 12 baseline services, five recent services | Recent count 5; acceleration 5 |
| Recent old + new,new,new; one old wallet per baseline week | Growth ratio 2; DISTINCT novelty 1/2 |
| Five equally served baseline wallets; four recent events at one wallet | Top2 recent 1; baseline .4; change .6 |
| Same baseline; four different recent wallets | Top2 recent .5; change .1 |
| Cash-In dominated / Cash-Out dominated / balanced | Signed value/count skews -1 / +1 / 0 |
| Baseline all Cash-Out; recent cash balanced | Valid signed change -1 retained; unavailable change is -3 |
| First observation age 0 / 1h / 28d / 50d | Coverage 0 / 1/24 / 28 / 28 days |
| Exact recent lower boundary / baseline lower / baseline upper | Exclude / exclude from count (may establish coverage) / include |
| Amount $50→$100 on existing two-edge path with $200 first edge and $100 funding | Path length stays 2; ratio .25→.5; share .5→1; funding age unchanged |

**Executed: 27 methods, no failures or errors.** Future additions and mutations leave earlier vectors identical across wallet, graph, funding and agent fixtures. Current-amount perturbation checks every column against the allowed dependency set, with exact examples for path/funding. Endpoint changes may legitimately select another history; no claim is made that endpoint-dependent features must remain unchanged. Same-time IDs below and above current are tested, as are disjoint baseline boundaries, lexicographic path ties, partition state reset and duplicate-ID rejection.

Executed methods:

- `test_agent_baseline_counts_coverage_and_acceleration`
- `test_agent_concentration_diversification_and_change`
- `test_agent_distinct_novelty_repeated_visits`
- `test_assisted_receiver_does_not_change_sender_subject`
- `test_baseline_equal_timestamps_and_current_id_cutoff`
- `test_baseline_exact_boundaries_all_streams`
- `test_baseline_full_coverage_exact_lower_boundary`
- `test_burst_repetition_band_day`
- `test_cash_direction_service_and_signed_missing`
- `test_collection_dispersion`
- `test_coverage_manual`
- `test_current_funding_role`
- `test_equal_timestamp_all_families`
- `test_exact_current_amount_effects_and_agent_burst`
- `test_funding_boundary_manual`
- `test_funding_cash_only_and_future`
- `test_future_invariance_and_current_control_every_family`
- `test_isolated_and_no_history`
- `test_multiple_anchors_and_cash_after_anchor`
- `test_network_baseline_minimum_and_disjoint`
- `test_partition_isolation_and_duplicate_ids`
- `test_path_boundaries_ties_simple_and_amount_independence`
- `test_path_lexicographic_tie_and_five_edges`
- `test_paths_manual_eight_cases`
- `test_private_metadata_independence_all_families`
- `test_recent_boundary_all_domains`
- `test_wallet_baseline_coverage_count_and_rate`

## 5. Baseline availability and missingness

Baseline B(L) is `(t-L-28d,t-L]`; recent R(L) is `(t-L,t]`. Windows do not overlap. Full observation requires first prior observation at or before the baseline lower boundary. The displayed 28d coverage cap is never used to infer 29d or 35d eligibility. Rate denominators use `max(1, expected count)`; the growth denominator is `max(1, median of four weekly distinct counts)`. The A2 comparator pools 28d and ranks its top two wallets independently of the recent 24h top two.

| Feature | Recent | Baseline minimum | Other requirements | Missing | Train unavailable | Validation unavailable |
| --- | --- | --- | --- | --- | --- | --- |
| `wallet_count_acceleration_1h` | 1h | 4 wallet activity | none | -1 | 0.16915 | 0.168533 |
| `receiver_inflow_acceleration_24h` | 24h | 4 W2W inflows | none | -1 | 0.245433 | 0.241333 |
| `sender_outflow_acceleration_24h` | 24h | 4 W2W outflows | none | -1 | 0.2841 | 0.280467 |
| `agent_service_acceleration_1h` | 1h | 12 agent services | none | -1 | 0.36155 | 0.356667 |
| `agent_wallet_growth_ratio_7d` | 7d | 12 agent services | four distinct-wallet bucket counts | -1 | 0.384283 | 0.3796 |
| `agent_new_wallet_share_7d` | 7d | 12 agent services | distinct-wallet union | -1 | 0.384283 | 0.3796 |
| `agent_top2_share_change_24h` | 24h | 20 agent services | at least 5 distinct baseline wallets | -3 | 0.383567 | 0.380933 |
| `agent_cash_value_skew_change` | 24h | 12 agent services | at least 8 baseline cash events | -3 | 0.366633 | 0.3652 |

Every missing fraction below uses the column-specific marker. Raw skews have no unavailable marker: -1 means fully Cash-In dominated. Signed changes may legitimately equal -1; their unavailable value is -3. All count/value/ratio range checks exclude only the documented marker. No availability flag encodes a reference outcome.

| Feature | Train valid -1 count | Validation valid -1 count |
| --- | --- | --- |
| `agent_top2_share_change_24h` | 0 | 0 |
| `agent_cash_value_skew_24h` | 8749 | 2213 |
| `agent_cash_count_skew_24h` | 8749 | 2213 |
| `agent_cash_value_skew_change` | 0 | 0 |


## 6. Corrected feature distributions

Observed summaries exclude the documented missing marker. Zero fraction is over all rows. Missing fractions are reported separately. Binary features are not flagged near-constant merely for having two distinct values: the corrected rule requires modal frequency ≥99%. Tail-span/IQR diagnostics and summaries including sentinels are retained in JSON; large ratios when IQR=0 are descriptive flags, not grounds for changing features.

### Train

| Feature | Min | Max | Mean | SD | Median | Q01 | Q05 | Q95 | Q99 | Zero fraction | Missing fraction | Observed distinct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `current_amount_usd` | 1 | 24999 | 3366.32 | 6247.29 | 189.83 | 2.85 | 7.86 | 19298.8 | 23929.9 | 0 | 0 | 36100 |
| `current_is_cash_in` | 0 | 1 | 0.254 | 0.435298 | 0 | 0 | 0 | 1 | 1 | 0.746 | 0 | 2 |
| `current_is_cash_out` | 0 | 1 | 0.254 | 0.435298 | 0 | 0 | 0 | 1 | 1 | 0.746 | 0 | 2 |
| `wallet_count_1h_inclusive` | 1 | 23 | 1.42967 | 1.56774 | 1 | 1 | 1 | 4 | 9 | 0 | 0 | 23 |
| `wallet_value_24h_inclusive` | 1 | 455916 | 9860.31 | 18859.5 | 1105.57 | 4.0599 | 14.43 | 39343.2 | 75935.5 | 0 | 0 | 47856 |
| `wallet_count_utc_day_inclusive` | 1 | 30 | 2.34063 | 2.92134 | 1 | 1 | 1 | 8 | 16 | 0 | 0 | 30 |
| `wallet_active_hours_utc_day` | 1 | 16 | 1.70295 | 1.36504 | 1 | 1 | 1 | 4 | 7 | 0 | 0 | 16 |
| `wallet_current_amount_cluster_share_7d` | 0.0227273 | 1 | 0.304325 | 0.232235 | 0.25 | 0.0384615 | 0.0588235 | 1 | 1 | 0 | 0 | 282 |
| `wallet_band_share_7d_inclusive` | 0 | 1 | 0.057892 | 0.129884 | 0 | 0 | 0 | 0.333333 | 0.526316 | 0.756767 | 0 | 253 |
| `wallet_count_acceleration_1h` | 1 | 23 | 1.44846 | 1.60388 | 1 | 1 | 1 | 4 | 10 | 0 | 0.16915 | 23 |
| `receiver_unique_sources_24h_inclusive` | 0 | 12 | 0.924483 | 1.16532 | 1 | 0 | 0 | 3 | 6 | 0.3751 | 0 | 13 |
| `receiver_inflow_count_24h_inclusive` | 0 | 21 | 1.01728 | 1.44152 | 1 | 0 | 0 | 3 | 8 | 0.3751 | 0 | 22 |
| `receiver_inflow_acceleration_24h` | 0 | 21 | 1.02761 | 1.45307 | 1 | 0 | 0 | 3 | 8 | 0.27975 | 0.245433 | 53 |
| `sender_unique_destinations_24h_inclusive` | 0 | 14 | 1.27812 | 1.70032 | 1 | 0 | 0 | 5 | 8 | 0.347667 | 0 | 15 |
| `sender_outflow_count_24h_inclusive` | 0 | 22 | 1.4271 | 2.14454 | 1 | 0 | 0 | 6 | 11 | 0.347667 | 0 | 23 |
| `sender_outflow_acceleration_24h` | 0 | 22 | 1.48691 | 2.23414 | 1 | 0 | 0 | 6 | 11 | 0.244983 | 0.2841 | 66 |
| `current_return_path_length` | 0 | 5 | 0.0403833 | 0.338358 | 0 | 0 | 0 | 0 | 2 | 0.980967 | 0 | 6 |
| `current_return_amount_ratio` | 9.55546e-05 | 24796.8 | 125.868 | 905.419 | 0.721721 | 0.000392649 | 0.00233186 | 473.564 | 2356.88 | 0 | 0.980967 | 1065 |
| `wallet_observed_onward_funding_share_24h` | 0 | 17374.4 | 48.4898 | 427.982 | 0 | 0 | 0 | 106.513 | 1058.4 | 0.254 | 0.528267 | 13055 |
| `wallet_prior_funding_age_hours` | 0.000102692 | 23.9998 | 11.6962 | 7.39737 | 11.7699 | 0.101915 | 0.616264 | 22.9758 | 23.778 | 0 | 0.782267 | 13064 |
| `agent_service_count_1h_inclusive` | 0 | 29 | 1.41767 | 2.08932 | 1 | 0 | 0 | 5 | 11 | 0.234 | 0 | 30 |
| `agent_service_acceleration_1h` | 1 | 26 | 1.83199 | 2.14321 | 1 | 1 | 1 | 6 | 12 | 0 | 0.36155 | 26 |
| `agent_wallet_growth_ratio_7d` | 0.0606061 | 14 | 1.39703 | 0.958661 | 1.15385 | 0.333333 | 0.530612 | 3 | 5.33333 | 0 | 0.384283 | 1815 |
| `agent_new_wallet_share_7d` | 0 | 1 | 0.87176 | 0.0995405 | 0.875 | 0.611111 | 0.695652 | 1 | 1 | 1.66667e-05 | 0.384283 | 376 |
| `agent_top2_count_share_24h` | 0 | 1 | 0.497514 | 0.365325 | 0.5 | 0 | 0 | 1 | 1 | 0.234 | 0 | 307 |
| `agent_top2_share_change_24h` | -0.552632 | 0.960784 | 0.447998 | 0.265763 | 0.446973 | -0.0995685 | 0.0247923 | 0.863566 | 0.92 | 0.000583333 | 0.383567 | 17617 |
| `agent_cash_value_skew_24h` | -1 | 1 | -0.0375282 | 0.716108 | 0 | -1 | -1 | 1 | 1 | 0.27505 | 0 | 21586 |
| `agent_cash_count_skew_24h` | -1 | 1 | -0.0280553 | 0.57516 | 0 | -1 | -1 | 1 | 1 | 0.382783 | 0 | 141 |
| `agent_cash_value_skew_change` | -1.99655 | 1.99902 | -0.0108158 | 0.885962 | -0.0533064 | -1.6994 | -1.26806 | 1.32611 | 1.65762 | 0 | 0.366633 | 28153 |
| `wallet_history_coverage_days` | 0 | 28 | 25.702 | 6.17192 | 28 | 0.034613 | 8.51633 | 28 | 28 | 0.0082 | 0 | 9406 |
| `receiver_history_coverage_days` | 0 | 28 | 25.6887 | 6.18466 | 28 | 0.28157 | 8.41821 | 28 | 28 | 0.00583333 | 0 | 9567 |
| `agent_history_coverage_days` | 0 | 28 | 19.7492 | 12.1262 | 28 | 0 | 0 | 28 | 28 | 0.2356 | 0 | 7343 |

Constant columns including encoded missingness: none. Near-constant columns by the ≥99% modal rule: none.

### Validation

| Feature | Min | Max | Mean | SD | Median | Q01 | Q05 | Q95 | Q99 | Zero fraction | Missing fraction | Observed distinct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `current_amount_usd` | 1 | 24980.3 | 3273.51 | 6193.96 | 182.85 | 2.49 | 7 | 19395.7 | 23916.5 | 0 | 0 | 10888 |
| `current_is_cash_in` | 0 | 1 | 0.254 | 0.435298 | 0 | 0 | 0 | 1 | 1 | 0.746 | 0 | 2 |
| `current_is_cash_out` | 0 | 1 | 0.254 | 0.435298 | 0 | 0 | 0 | 1 | 1 | 0.746 | 0 | 2 |
| `wallet_count_1h_inclusive` | 1 | 23 | 1.4442 | 1.64259 | 1 | 1 | 1 | 4 | 10 | 0 | 0 | 23 |
| `wallet_value_24h_inclusive` | 1 | 279894 | 9610.25 | 16609.9 | 1004.68 | 4 | 14 | 41099.5 | 78761.7 | 0 | 0 | 13121 |
| `wallet_count_utc_day_inclusive` | 1 | 26 | 2.391 | 3.01792 | 1 | 1 | 1 | 9 | 16 | 0 | 0 | 26 |
| `wallet_active_hours_utc_day` | 1 | 14 | 1.72027 | 1.42568 | 1 | 1 | 1 | 5 | 8 | 0 | 0 | 14 |
| `wallet_current_amount_cluster_share_7d` | 0.0238095 | 1 | 0.301369 | 0.228433 | 0.25 | 0.037037 | 0.0588235 | 1 | 1 | 0 | 0 | 213 |
| `wallet_band_share_7d_inclusive` | 0 | 1 | 0.0573479 | 0.128386 | 0 | 0 | 0 | 0.333333 | 0.5 | 0.755 | 0 | 180 |
| `wallet_count_acceleration_1h` | 1 | 20 | 1.4037 | 1.47266 | 1 | 1 | 1 | 4 | 9 | 0 | 0.168533 | 20 |
| `receiver_unique_sources_24h_inclusive` | 0 | 13 | 0.907 | 1.15352 | 1 | 0 | 0 | 3 | 6 | 0.383867 | 0 | 14 |
| `receiver_inflow_count_24h_inclusive` | 0 | 18 | 0.996267 | 1.4167 | 1 | 0 | 0 | 3 | 7 | 0.383867 | 0 | 19 |
| `receiver_inflow_acceleration_24h` | 0 | 18 | 1.00448 | 1.4619 | 1 | 0 | 0 | 3 | 8 | 0.292667 | 0.241333 | 19 |
| `sender_unique_destinations_24h_inclusive` | 0 | 13 | 1.29627 | 1.71183 | 1 | 0 | 0 | 5 | 8 | 0.345 | 0 | 14 |
| `sender_outflow_count_24h_inclusive` | 0 | 18 | 1.4488 | 2.17109 | 1 | 0 | 0 | 6 | 11 | 0.345 | 0 | 19 |
| `sender_outflow_acceleration_24h` | 0 | 18 | 1.4645 | 2.13547 | 1 | 0 | 0 | 6 | 11 | 0.2438 | 0.280467 | 37 |
| `current_return_path_length` | 0 | 5 | 0.0718667 | 0.451112 | 0 | 0 | 0 | 0 | 3 | 0.967667 | 0 | 6 |
| `current_return_amount_ratio` | 0.000173953 | 3628.5 | 72.5182 | 316.408 | 1.07219 | 0.00050256 | 0.00392507 | 279.355 | 1783.58 | 0 | 0.967667 | 466 |
| `wallet_observed_onward_funding_share_24h` | 0 | 13878 | 53.2022 | 370.435 | 0 | 0 | 0 | 143.386 | 1444.48 | 0.254 | 0.531733 | 3212 |
| `wallet_prior_funding_age_hours` | 0.0022112 | 23.9815 | 11.3254 | 7.43478 | 10.7577 | 0.0742599 | 0.575407 | 23.0611 | 23.8148 | 0 | 0.785733 | 3214 |
| `agent_service_count_1h_inclusive` | 0 | 22 | 1.38567 | 1.89821 | 1 | 0 | 0 | 5 | 10 | 0.234 | 0 | 23 |
| `agent_service_acceleration_1h` | 1 | 22 | 1.82311 | 2.02868 | 1 | 1 | 1 | 6 | 11 | 0 | 0.356667 | 22 |
| `agent_wallet_growth_ratio_7d` | 0.0833333 | 11 | 1.35326 | 0.828836 | 1.16981 | 0.375 | 0.556011 | 2.75 | 4.25 | 0 | 0.3796 | 1102 |
| `agent_new_wallet_share_7d` | 0 | 1 | 0.639535 | 0.191912 | 0.628571 | 0.222222 | 0.333333 | 1 | 1 | 0.000666667 | 0.3796 | 413 |
| `agent_top2_count_share_24h` | 0 | 1 | 0.503855 | 0.364907 | 0.5 | 0 | 0 | 1 | 1 | 0.234 | 0 | 223 |
| `agent_top2_share_change_24h` | -0.42471 | 0.938776 | 0.435614 | 0.265256 | 0.429099 | -0.112821 | 0.0181713 | 0.855932 | 0.894444 | 0.0008 | 0.380933 | 5936 |
| `agent_cash_value_skew_24h` | -1 | 1 | -0.0192564 | 0.71101 | 0 | -1 | -1 | 1 | 1 | 0.276733 | 0 | 5419 |
| `agent_cash_count_skew_24h` | -1 | 1 | -0.0341098 | 0.574821 | 0 | -1 | -1 | 1 | 1 | 0.379733 | 0 | 114 |
| `agent_cash_value_skew_change` | -1.99733 | 1.99703 | -0.0400901 | 0.874158 | -0.0377426 | -1.76888 | -1.29943 | 1.25021 | 1.50316 | 0 | 0.3652 | 7087 |
| `wallet_history_coverage_days` | 0 | 28 | 25.6533 | 6.24652 | 28 | 0.107784 | 8.50576 | 28 | 28 | 0.00826667 | 0 | 2341 |
| `receiver_history_coverage_days` | 0 | 28 | 25.6559 | 6.2257 | 28 | 0.318861 | 8.58612 | 28 | 28 | 0.0062 | 0 | 2373 |
| `agent_history_coverage_days` | 0 | 28 | 19.7703 | 12.132 | 28 | 0 | 0 | 28 | 28 | 0.2356 | 0 | 1800 |

Constant columns including encoded missingness: none. Near-constant columns by the ≥99% modal rule: none.

## 7. Train/Validation shift

Differences are Validation minus Train. Means exclude unavailable markers. Missingness and zero fractions are over all rows; their differences are proportions, not percentage-point numbers. Units differ across columns, so raw mean differences are not ranked as comparable effect sizes. Coverage, topology, funding and novelty are retained as originally specified regardless of shift.

| Feature | Train observed mean | Validation observed mean | Mean difference | Train missing | Validation missing | Missing difference | Zero-fraction difference |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `current_amount_usd` | 3366.32 | 3273.51 | -92.809 | 0 | 0 | 0 | 0 |
| `current_is_cash_in` | 0.254 | 0.254 | 0 | 0 | 0 | 0 | 0 |
| `current_is_cash_out` | 0.254 | 0.254 | 0 | 0 | 0 | 0 | 0 |
| `wallet_count_1h_inclusive` | 1.42967 | 1.4442 | 0.0145333 | 0 | 0 | 0 | 0 |
| `wallet_value_24h_inclusive` | 9860.31 | 9610.25 | -250.064 | 0 | 0 | 0 | 0 |
| `wallet_count_utc_day_inclusive` | 2.34063 | 2.391 | 0.0503667 | 0 | 0 | 0 | 0 |
| `wallet_active_hours_utc_day` | 1.70295 | 1.72027 | 0.0173167 | 0 | 0 | 0 | 0 |
| `wallet_current_amount_cluster_share_7d` | 0.304325 | 0.301369 | -0.00295659 | 0 | 0 | 0 | 0 |
| `wallet_band_share_7d_inclusive` | 0.057892 | 0.0573479 | -0.000544185 | 0 | 0 | 0 | -0.00176667 |
| `wallet_count_acceleration_1h` | 1.44846 | 1.4037 | -0.0447521 | 0.16915 | 0.168533 | -0.000616667 | 0 |
| `receiver_unique_sources_24h_inclusive` | 0.924483 | 0.907 | -0.0174833 | 0 | 0 | 0 | 0.00876667 |
| `receiver_inflow_count_24h_inclusive` | 1.01728 | 0.996267 | -0.0210167 | 0 | 0 | 0 | 0.00876667 |
| `receiver_inflow_acceleration_24h` | 1.02761 | 1.00448 | -0.0231269 | 0.245433 | 0.241333 | -0.0041 | 0.0129167 |
| `sender_unique_destinations_24h_inclusive` | 1.27812 | 1.29627 | 0.01815 | 0 | 0 | 0 | -0.00266667 |
| `sender_outflow_count_24h_inclusive` | 1.4271 | 1.4488 | 0.0217 | 0 | 0 | 0 | -0.00266667 |
| `sender_outflow_acceleration_24h` | 1.48691 | 1.4645 | -0.0224097 | 0.2841 | 0.280467 | -0.00363333 | -0.00118333 |
| `current_return_path_length` | 0.0403833 | 0.0718667 | 0.0314833 | 0 | 0 | 0 | -0.0133 |
| `current_return_amount_ratio` | 125.868 | 72.5182 | -53.35 | 0.980967 | 0.967667 | -0.0133 | 0 |
| `wallet_observed_onward_funding_share_24h` | 48.4898 | 53.2022 | 4.71248 | 0.528267 | 0.531733 | 0.00346667 | 0 |
| `wallet_prior_funding_age_hours` | 11.6962 | 11.3254 | -0.370792 | 0.782267 | 0.785733 | 0.00346667 | 0 |
| `agent_service_count_1h_inclusive` | 1.41767 | 1.38567 | -0.032 | 0 | 0 | 0 | 0 |
| `agent_service_acceleration_1h` | 1.83199 | 1.82311 | -0.00888012 | 0.36155 | 0.356667 | -0.00488333 | 0 |
| `agent_wallet_growth_ratio_7d` | 1.39703 | 1.35326 | -0.0437763 | 0.384283 | 0.3796 | -0.00468333 | 0 |
| `agent_new_wallet_share_7d` | 0.87176 | 0.639535 | -0.232225 | 0.384283 | 0.3796 | -0.00468333 | 0.00065 |
| `agent_top2_count_share_24h` | 0.497514 | 0.503855 | 0.00634107 | 0 | 0 | 0 | 0 |
| `agent_top2_share_change_24h` | 0.447998 | 0.435614 | -0.0123839 | 0.383567 | 0.380933 | -0.00263333 | 0.000216667 |
| `agent_cash_value_skew_24h` | -0.0375282 | -0.0192564 | 0.0182718 | 0 | 0 | 0 | 0.00168333 |
| `agent_cash_count_skew_24h` | -0.0280553 | -0.0341098 | -0.00605448 | 0 | 0 | 0 | -0.00305 |
| `agent_cash_value_skew_change` | -0.0108158 | -0.0400901 | -0.0292743 | 0.366633 | 0.3652 | -0.00143333 | 0 |
| `wallet_history_coverage_days` | 25.702 | 25.6533 | -0.0486571 | 0 | 0 | 0 | 6.66667e-05 |
| `receiver_history_coverage_days` | 25.6887 | 25.6559 | -0.0327994 | 0 | 0 | 0 | 0.000366667 |
| `agent_history_coverage_days` | 19.7492 | 19.7703 | 0.021033 | 0 | 0 | 0 | 0 |


## 8. Oracle-leakage audit

**PASS within the documented checks.** The extractor imports no reference evaluator, old V2 feature code or classifier. AST review checks forbidden private-field literals and imports; explicit observable projection and adversarial metadata mutations provide additional evidence. Source review below considers whether each feature group directly implements an entire reference conjunction. Audit family outcomes come from the frozen development witness ledger only after X is extracted; they do not enter X.

| Reference family | Why the feature summary is not a complete predicate |
| --- | --- |
| A1 | No recent distinct/novel minimum count conjunction. |
| A2 | No recent service count>=8 and concentration/change conjunction. |
| A3 | No recent unique-wallet minimum combined with intensity. |
| A4 | No cash count/unique-wallet/current-cash/sign/change conjunction. |
| N1/N2 | Do not combine breadth, event count, value, current role and rate. |
| N3 | Topology and first-edge ratio separate; no adjacent-amount filtering or any-qualifying-path result. |
| N4 | Share/age do not impose minimum funding, remaining-balance gate or full role conjunction. |
| S1 | Does not expose largest-fragment share or full count/value/rate conjunction. |
| S2 | Does not expose cluster sum or matching-baseline count conjunction. |
| S3 | Does not expose complete-day preceding-median conjunction. |
| S4 | Does not expose current-band gate + in-band distinctness + count/rate conjunction. |

The initial runner used short family codes against a ledger containing full family names, so its additional family checks were uninformative. A separate audited diagnostic maps all 12 full names explicitly, verifies that the union of family evidence equals each frozen target, and repeats the checks against unchanged published matrices. The initial record and frozen extraction source are preserved; `stage10a_family_oracle_leakage.json` is the authoritative corrected family diagnostic. This reporting/audit correction does not change feature semantics, X or y.

### Train leakage checks

Checked 32 individual value mappings, 32 direct/inverse target columns, monotone one-cutoff separation, **496 two-feature value mappings**, 13 fixed observable conditions and **156 fixed AND/OR combinations** (including inverse equivalence). Exact direct target columns: []; exact monotone target separators: []; exact fixed target combinations: [].

Exact single-feature lookup mappings on this finite sample: []. Exact two-feature lookup mappings: 0. Such mappings may be vacuous when pairs identify rows; singleton and contradictory-key counts are reported for all pairs in JSON. They are not evidence of a portable oracle without source or repeated-value support.

| Single feature | Distinct values | Contradictory value groups | Rows in contradictory groups | Singleton fraction |
| --- | --- | --- | --- | --- |
| `agent_cash_count_skew_24h` | 141 | 111 | 59918 | 0.000216667 |
| `agent_cash_value_skew_24h` | 21586 | 599 | 34592 | 0.29495 |
| `agent_cash_value_skew_change` | 28154 | 1011 | 25718 | 0.372033 |
| `agent_history_coverage_days` | 7343 | 2 | 52659 | 0.12235 |
| `agent_new_wallet_share_7d` | 377 | 239 | 59228 | 0.000733333 |
| `agent_service_acceleration_1h` | 27 | 24 | 59992 | 1.66667e-05 |
| `agent_service_count_1h_inclusive` | 30 | 27 | 59997 | 5e-05 |
| `agent_top2_count_share_24h` | 307 | 204 | 59792 | 0.00105 |
| `agent_top2_share_change_24h` | 17618 | 3012 | 41186 | 0.199067 |
| `agent_wallet_growth_ratio_7d` | 1816 | 655 | 49520 | 0.00438333 |
| `current_amount_usd` | 36100 | 4111 | 23780 | 0.484733 |
| `current_is_cash_in` | 2 | 2 | 60000 | 0 |
| `current_is_cash_out` | 2 | 2 | 60000 | 0 |
| `current_return_amount_ratio` | 1066 | 16 | 58899 | 0.0168667 |
| `current_return_path_length` | 6 | 6 | 60000 | 0 |
| `receiver_history_coverage_days` | 9567 | 1 | 50085 | 0.159417 |
| `receiver_inflow_acceleration_24h` | 54 | 21 | 59953 | 0.000433333 |
| `receiver_inflow_count_24h_inclusive` | 22 | 18 | 59991 | 3.33333e-05 |
| `receiver_unique_sources_24h_inclusive` | 13 | 13 | 60000 | 0 |
| `sender_outflow_acceleration_24h` | 67 | 29 | 59926 | 0.000416667 |
| `sender_outflow_count_24h_inclusive` | 23 | 17 | 59968 | 3.33333e-05 |
| `sender_unique_destinations_24h_inclusive` | 15 | 13 | 59983 | 0 |
| `wallet_active_hours_utc_day` | 16 | 11 | 59952 | 1.66667e-05 |
| `wallet_band_share_7d_inclusive` | 253 | 167 | 59883 | 0.00105 |
| `wallet_count_1h_inclusive` | 23 | 18 | 59973 | 0 |
| `wallet_count_acceleration_1h` | 24 | 13 | 59719 | 0 |
| `wallet_count_utc_day_inclusive` | 30 | 24 | 59970 | 0 |
| `wallet_current_amount_cluster_share_7d` | 282 | 204 | 59870 | 0.000783333 |
| `wallet_history_coverage_days` | 9406 | 1 | 50104 | 0.156733 |
| `wallet_observed_onward_funding_share_24h` | 13056 | 4 | 46940 | 0.217417 |
| `wallet_prior_funding_age_hours` | 13065 | 1 | 46936 | 0.217733 |
| `wallet_value_24h_inclusive` | 47856 | 2204 | 11091 | 0.718483 |


| Frozen family outcome | Positive support | Negative support | Direct / monotone / fixed combination equivalence check |
| --- | --- | --- | --- |
| A1 | 11476 | 48524 | PASS |
| A2 | 3770 | 56230 | PASS |
| A3 | 1810 | 58190 | PASS |
| A4 | 1353 | 58647 | PASS |
| N1 | 1278 | 58722 | PASS |
| N2 | 2912 | 57088 | PASS |
| N3 | 120 | 59880 | PASS |
| N4 | 1064 | 58936 | PASS |
| S1 | 1352 | 58648 | PASS |
| S2 | 4 | 59996 | PASS |
| S3 | 3262 | 56738 | PASS |
| S4 | 40 | 59960 | PASS |


### Validation leakage checks

Checked 32 individual value mappings, 32 direct/inverse target columns, monotone one-cutoff separation, **496 two-feature value mappings**, 13 fixed observable conditions and **156 fixed AND/OR combinations** (including inverse equivalence). Exact direct target columns: []; exact monotone target separators: []; exact fixed target combinations: [].

Exact single-feature lookup mappings on this finite sample: []. Exact two-feature lookup mappings: 0. Such mappings may be vacuous when pairs identify rows; singleton and contradictory-key counts are reported for all pairs in JSON. They are not evidence of a portable oracle without source or repeated-value support.

| Single feature | Distinct values | Contradictory value groups | Rows in contradictory groups | Singleton fraction |
| --- | --- | --- | --- | --- |
| `agent_cash_count_skew_24h` | 114 | 70 | 14893 | 0.00133333 |
| `agent_cash_value_skew_24h` | 5419 | 177 | 8699 | 0.297133 |
| `agent_cash_value_skew_change` | 7088 | 286 | 6437 | 0.372933 |
| `agent_history_coverage_days` | 1800 | 2 | 13202 | 0.119867 |
| `agent_new_wallet_share_7d` | 414 | 226 | 14444 | 0.00533333 |
| `agent_service_acceleration_1h` | 23 | 7 | 14602 | 6.66667e-05 |
| `agent_service_count_1h_inclusive` | 23 | 16 | 14975 | 6.66667e-05 |
| `agent_top2_count_share_24h` | 223 | 127 | 14794 | 0.00333333 |
| `agent_top2_share_change_24h` | 5937 | 616 | 8503 | 0.3004 |
| `agent_wallet_growth_ratio_7d` | 1103 | 404 | 12162 | 0.0154667 |
| `current_amount_usd` | 10888 | 735 | 4138 | 0.641467 |
| `current_is_cash_in` | 2 | 2 | 15000 | 0 |
| `current_is_cash_out` | 2 | 2 | 15000 | 0 |
| `current_return_amount_ratio` | 467 | 7 | 14529 | 0.0302 |
| `current_return_path_length` | 6 | 6 | 15000 | 0 |
| `receiver_history_coverage_days` | 2373 | 1 | 12536 | 0.158067 |
| `receiver_inflow_acceleration_24h` | 20 | 18 | 14995 | 0 |
| `receiver_inflow_count_24h_inclusive` | 19 | 17 | 14995 | 0 |
| `receiver_unique_sources_24h_inclusive` | 14 | 11 | 14979 | 0 |
| `sender_outflow_acceleration_24h` | 38 | 16 | 14850 | 0.000933333 |
| `sender_outflow_count_24h_inclusive` | 19 | 17 | 14997 | 6.66667e-05 |
| `sender_unique_destinations_24h_inclusive` | 14 | 12 | 14973 | 0 |
| `wallet_active_hours_utc_day` | 14 | 12 | 14991 | 6.66667e-05 |
| `wallet_band_share_7d_inclusive` | 180 | 101 | 14878 | 0.0034 |
| `wallet_count_1h_inclusive` | 23 | 20 | 14997 | 0.0002 |
| `wallet_count_acceleration_1h` | 21 | 11 | 14890 | 6.66667e-05 |
| `wallet_count_utc_day_inclusive` | 26 | 25 | 14999 | 6.66667e-05 |
| `wallet_current_amount_cluster_share_7d` | 213 | 123 | 14853 | 0.00386667 |
| `wallet_history_coverage_days` | 2341 | 1 | 12537 | 0.155933 |
| `wallet_observed_onward_funding_share_24h` | 3213 | 2 | 11786 | 0.213867 |
| `wallet_prior_funding_age_hours` | 3215 | 1 | 11786 | 0.214267 |
| `wallet_value_24h_inclusive` | 13121 | 343 | 1770 | 0.829067 |


| Frozen family outcome | Positive support | Negative support | Direct / monotone / fixed combination equivalence check |
| --- | --- | --- | --- |
| A1 | 2745 | 12255 | PASS |
| A2 | 930 | 14070 | PASS |
| A3 | 485 | 14515 | PASS |
| A4 | 337 | 14663 | PASS |
| N1 | 316 | 14684 | PASS |
| N2 | 736 | 14264 | PASS |
| N3 | 41 | 14959 | PASS |
| N4 | 247 | 14753 | PASS |
| S1 | 276 | 14724 | PASS |
| S2 | 1 | 14999 | PASS |
| S3 | 814 | 14186 | PASS |
| S4 | 8 | 14992 | PASS |


Strong behavioural association is allowed. No feature was added, dropped or tuned using these results. The audit does not exclude arbitrary nonlinear/high-order encodings, near-perfect separators or generator shortcuts. Monotone checks look for exact separation, and the fixed conjunction checks are not exhaustive. No learned classifier, optimized cutoff, model accuracy, F1, ROC-AUC, PR-AUC or feature importance was computed. Descriptive condition constants are the predeclared synthetic-contract checks, not a fitted classification threshold.

## 9. Contract freeze and serialized reproducibility

| Record | Value |
| --- | --- |
| Version | v3_stage10a_features_1 |
| Contract frozen UTC | 2026-09-28T16:30:31.758660+00:00 |
| Run A started UTC | 2026-09-28T16:30:31.775521+00:00 |
| Run B started UTC | 2026-09-28T16:32:38.948971+00:00 |
| Completed UTC | 2026-09-28T16:34:19.654859+00:00 |
| Runner duration seconds | 232.805 |
| Original Stage 10 contract SHA-256 observed in this stage | 82afc856302aa326dbf719ee87a68627bdfd8a0ffa61307f87286381e5df6da9 |
| Corrected contract SHA-256 | d143c7d8ba70a43fa57a1f1b0ded4f3893c5cd575731ddbe63f77b69cb6f3346 |
| Freeze-manifest SHA-256 | 396b24fa4908bd9dfa0e5533fcf4401fe6161b7f2fbb2e7997eb72e2beb7ef06 |

The two extractions reload frozen input tables and start empty histories independently. Each writes its own temporary serialized set before comparison. CSV round-trip values, numeric matrices, targets, row IDs, row/feature order and all four file hashes match. The first set is copied to the versioned development directory and checked again. Temporary sets were removed after comparison; their recorded hashes are below. No original matrix was reused.

| Partition | File | Run A SHA-256 | Run B identical; published identical |
| --- | --- | --- | --- |
| train | X.csv | `80259bdbe99272fbe5c3ca7619a8319250b37528b465589391d4e051e9ab729f` | True |
| train | feature_names.json | `a3695de699df5f2a8d11288664debb6824f15ddd63cb6b82ec378fa084790755` | True |
| train | row_ids.csv | `9c0f0031ec2f9e47f4283ee6dfa0268f68bbabdd9a4558c7217dd4cdb3a83c16` | True |
| train | y.csv | `87649361df2fd9ab75bb5c5e0b8f4889efc74262ad3ebe9b7da8570f11563321` | True |
| validation | X.csv | `41ba615d85550536f850d76862b270765d409729194b47dbe46ed7465decdf96` | True |
| validation | feature_names.json | `a3695de699df5f2a8d11288664debb6824f15ddd63cb6b82ec378fa084790755` | True |
| validation | row_ids.csv | `faf5ae1be1a094504805f5f0a1721308e98a286b22585e7d33ad33fc95a004d2` | True |
| validation | y.csv | `adb5ab90732288e1b496c897b57afdfe9f6151d807e530fd47e87435166488ea` | True |

Each y value was mapped from frozen ground truth using its transaction ID, with exact ID-set equality and fixed target counts. The corresponding y-file hashes above identify the serialized mapped labels; the source ground-truth hashes below identify the untouched authority.

| Partition | Ground truth SHA-256 |
| --- | --- |
| train | 4e14d7234c2bbf082736a89d2790440cf0d96c51318ef6258171633afdf7eb62 |
| validation | 488a7b827fe0d4e70af25b982044638eda5ad190097ff7fb9af1c1e0b4c550d1 |


## 10. Protection and public commitment
**PASS:** 401 protected files before and 401 after; changed set `[]`. All 14 explicitly listed frozen development inputs also match their Stage 9 manifest. The inventory contains file paths and digests, with exact inclusion/exclusion scope in `stage10a_protection.json`.

Explicit traversed directories:

- `templates`
- `static`
- `scripts`
- `tests`
- `ml`
- `ml_archive`
- `reports`
- `ml_v2/src`
- `ml_v2/tests`
- `ml_v2/design`
- `ml_v2/reports`
- `ml_v2/data/development`
- `ml_v2/features/development`
- `ml_v3/design`
- `ml_v3/data/development`
- `ml_v3/features/development/train`
- `ml_v3/features/development/validation`

Additional explicit files include selected root application/configuration files, the frozen V3 reference/generator/access sources, previous Stage 9/10 reports, development manifest and two named public certificates. No dataset root or evaluation subtree is recursively scanned. Protection is a certificate for this allowlist, not every file on disk. Prohibited holdout bytes and unpartitioned historical datasets are excluded.

| Public artifact | Before SHA-256 | After SHA-256 |
| --- | --- | --- |
| ml_v3/data/manifests/evaluation_content_commitment.json | efc14471b98103a3ad547d93fc56833d014389efd9d3c6e5be6ba896c70d9d58 | efc14471b98103a3ad547d93fc56833d014389efd9d3c6e5be6ba896c70d9d58 |
| ml_v3/reports/V3_STAGE9_HOLDOUT_SEAL.json | efc14471b98103a3ad547d93fc56833d014389efd9d3c6e5be6ba896c70d9d58 | efc14471b98103a3ad547d93fc56833d014389efd9d3c6e5be6ba896c70d9d58 |

The two public certificates agree on the private-manifest commitment and each certificate is unchanged. This verifies the public commitment metadata; it does **not** freshly verify the continued integrity of unread holdout bytes. Such verification belongs to a separately authorized final evaluator.

## 11. Limitations, reproducible entry points and decision

All ten required findings are resolved for the corrected feature implementation and stated audit scope. PASS is based on semantic review, exact synthetic examples, full development range/integrity checks, descriptive leakage checks, independent serialized agreement and protection checks together.

This stage does not certify the frozen reference evaluator's implementation against every written Stage 8 predicate. Targets are preserved as explicitly required. Selected-path compression, proxy funding attribution, denominator floors, sparse baselines, pooled-28d versus recent-24h concentration, partition-local observation and synthetic ground truth remain experiment limitations. Baseline missingness is expected when eligibility fails. Coverage of tests and leakage combinations is finite.

Future preprocessing must use per-column missing markers, preserving legitimate negative values; any fitted scaling, clipping or imputation must use Train only. No such preprocessing was fitted here. Model training remains a later, separately authorized stage.

Implementation: `src/stage10a_pipeline.py`, `src/stage10a_contract.py`, `src/stage10a_audit.py`, `src/stage10a_protection.py`. Orchestration: `src/run_stage10a.py`; reporting: `src/report_stage10a.py`. Commands from the repository root:

```powershell
python -B -m unittest discover -s ml_v3/tests -p test_stage10a_features.py -v
python -B ml_v3/src/run_stage10a.py
python -B ml_v3/src/audit_stage10a_families.py
python -B ml_v3/src/report_stage10a.py
```

The extraction command creates new artifacts exclusively and refuses to overwrite an existing corrected run. To reproduce the whole workflow, use a fresh authorized development checkout with the original protected inputs, the recorded source versions and a fresh `stage10a_protection_before.json` generated by `stage10a_protection.py`; preserve existing run evidence. The report command reads the completed audit JSON and rewrites only the new Stage 10A report entry points.

### Evidence index

| File | Evidence |
|---|---|
| [stage10a_contract_manifest.json](stage10a_contract_manifest.json) | Ordered schema, original/current hashes, source/design digests and freeze timestamp |
| [stage10a_feature_statistics.json](stage10a_feature_statistics.json) | Matrix integrity, ranges, all/observed distributions, missingness and target-conditional summaries |
| [stage10a_shift_audit.json](stage10a_shift_audit.json) | Per-feature mean, zero and unavailable shifts |
| [stage10a_temporal_tests.json](stage10a_temporal_tests.json) | Executed test names and full captured test log |
| [stage10a_oracle_leakage.json](stage10a_oracle_leakage.json) | Source review, 32 single and 496 pair mappings per partition, fixed condition and frozen-family checks |
| [stage10a_family_oracle_leakage.json](stage10a_family_oracle_leakage.json) | Corrected full-name family lookup, support counts and predicate-outcome equivalence checks; supersedes the initial uninformative family lookup |
| [stage10a_reproducibility.json](stage10a_reproducibility.json) | Independent-run timings, exact equality checks, source target and output hashes |
| [stage10a_protection.json](stage10a_protection.json) | Explicit before/after file inventories, changes, public-certificate hashes and scope |

## Appendix A. Complete corrected feature contract

The following is the frozen corrected contract reproduced verbatim, with headings nested for this report. Its separately hashed file remains the authority for the feature version.

## MODEL V3 - STAGE 10A FEATURE CONTRACT

Version: `v3_stage10a_features_1`. Logical and serialized count: **32**, unchanged from Stage 10. This is a semantic repair, not a performance-driven extension. Stage 10's contract and outputs remain historical records. The freeze manifest records this file's hash before any full corrected extraction.

### Authority and resolved ambiguities

Stage 8 onset and architecture contracts control observable semantics. Stage 9 transactions and targets are frozen even where their evaluator may differ from the written design. Features never import a predicate evaluator or infer y from feature values.

N3 uses the Stage 8 architectural topology selection: no amount-gated path search, no complete N3 condition. The shortest chronological simple prior path is chosen; ties prefer the latest first-edge key, then lexicographically smallest whole edge-key sequence. The current amount divided by first-edge amount is a separate quantity, with no clipping or predicate cutoffs. The N3 predicate's adjacent-amount and return-amount conjunction is deliberately not an input feature; this resolves the request to respect amount semantics without returning an oracle flag.

N4 follows the exact Stage 8 anchor definition: earliest prior **W2W inflow** to the current outward wallet in (t-24h,t]. Cash-In alone is not a valid anchor. Cash-In after that anchor contributes to F and necessarily lies within the same 24h interval. The requested Cash-In-anchor test explicitly expects absence. Broadening anchor types would change the approved architecture. F sums inbound W2W and Cash-In from the anchor through key < T; O sums outward W2W and Cash-Out strictly after the anchor through T. No F>=100, 0.5..1 share test or remaining-balance gate is used in X. Non-outward Cash-In has share 0 and age missing. On W2W the subject for this pair is always the sender, including assisted W2W.

### Shared exact semantics

key=(UTC timestamp, integer transaction_id). Every historical query requires key < key(T). Recent windows R(L) are (t-L,t] with an OPEN lower time boundary and prior-key filtering; T is added only in explicitly inclusive calculations. Baselines B(L)=(t-L-28d,t-L] are disjoint from R(L), open at the lower and closed at the upper timestamp. The upper time boundary can include all its keys because it is strictly earlier than T. Calendar-day history is [UTC midnight,key(T)], including midnight. Sums retain integer minor units until a final ratio/USD conversion. No future records are inserted; each event updates histories once after emission. All partition state is fresh.

Structuring subject w is the serviced wallet for Cash-In/Out, and sender for every W2W (including assisted W2W). Only that wallet's cash and outgoing W2W events enter wallet activity. Receipt observes the receiver for coverage/network purposes without adding structuring activity. Both cash directions contribute wallet amount/activity. Direct W2W adds no agent service; assisted W2W adds one agent service at the explicitly serviced wallet, and never adds cash float. Cash-Out is positive and Cash-In negative for signed agent cash measures. Cash events do not enter the graph. Current endpoint changes may select different prior histories; invariance tests keep endpoints fixed when testing amount dependence.

Coverage begins with first prior observable endpoint/cash/service event, never private activation. Displayed coverage is capped at 28d; eligibility uses the UNCAPPED first-observation time. Full baseline coverage requires first observation <= t-L-28d. An event exactly at that lower boundary establishes coverage but is not counted in the open baseline window. Baseline count minima below are mandatory and use only the specified stream. Recent counts/distinct-wallet/value conditions from the complete predicates are NOT availability requirements.

### Missingness and cold starts

Nonnegative ratios and funding age use -1 only when unavailable. The signed changes use **-3**, outside both [-1,1] and [-2,2]. Legitimate -1 is retained; raw signed cash skews NEVER use a missing marker and have zero on no cash. There are no new availability columns; the feature count remains 32. Missingness is derived per column from this schema in audit sidecars, never by treating every -1 as missing. Future preprocessing must translate per-column markers explicitly and fit parameters on Train only.

On a first wallet event the inclusive count is 1, sum is its amount, cluster share is 1, band share is the current band indicator, day/hour counts are 1 and coverage is 0. Network inclusive counts are 1 for current W2W and 0 otherwise without history; path length is 0 and ratio is -1. No prior funding gives share -1 for outward roles and age -1; Cash-In share is 0. Agent current service count/top2 share are 1 when served, and 0 without an agent. All baseline ratios/changes are missing until their full baseline requirements hold. Zero denominators for valid empty shares/skews produce 0; baseline rates divide by max(1, expected count). A funding anchor or graph edge has strictly positive amount, enforced at input.

### Baseline eligibility table

For each row the baseline is B(L), fully observed for its entire 28 days. The recent window and baseline never overlap. Unavailable markers are as in the feature list.

| Feature | Recent L | Baseline stream | Minimum count | Additional requirements |
|---|---|---|---|---|
| `wallet_count_acceleration_1h` | 1h | wallet activity | 4 | none |
| `receiver_inflow_acceleration_24h` | 24h | W2W inflows | 4 | none |
| `sender_outflow_acceleration_24h` | 24h | W2W outflows | 4 | none |
| `agent_service_acceleration_1h` | 1h | agent services | 12 | none |
| `agent_wallet_growth_ratio_7d` | 7d | agent services | 12 | four distinct-wallet bucket counts |
| `agent_new_wallet_share_7d` | 7d | agent services | 12 | distinct-wallet union |
| `agent_top2_share_change_24h` | 24h | agent services | 20 | at least 5 distinct baseline wallets |
| `agent_cash_value_skew_change` | 24h | agent services | 12 | at least 8 baseline cash events |

### Exact ordered feature definitions

#### 1. `current_amount_usd`

- Domain/subject: current; T.
- Formula and window: amount_minor / 100.
- Temporal scope: CURRENT; only the named current fields are used.
- Units: USD. Valid range: [0, unbounded]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable current activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 2. `current_is_cash_in`

- Domain/subject: current; T.
- Formula and window: 1 if Cash-In else 0.
- Temporal scope: CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, 1]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable current activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 3. `current_is_cash_out`

- Domain/subject: current; T.
- Formula and window: 1 if Cash-Out else 0.
- Temporal scope: CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, 1]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable current activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 4. `wallet_count_1h_inclusive`

- Domain/subject: structuring; w.
- Formula and window: count R_wallet(1h).
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [1, unbounded]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable structuring activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 5. `wallet_value_24h_inclusive`

- Domain/subject: structuring; w.
- Formula and window: sum amount_minor in R_wallet(24h) / 100.
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: USD. Valid range: [0, unbounded]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable structuring activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 6. `wallet_count_utc_day_inclusive`

- Domain/subject: structuring; w.
- Formula and window: count activity from UTC midnight through key(T).
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [1, unbounded]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable structuring activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 7. `wallet_active_hours_utc_day`

- Domain/subject: structuring; w.
- Formula and window: distinct UTC hour buckets since midnight through key(T).
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [1, 24]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable structuring activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 8. `wallet_current_amount_cluster_share_7d`

- Domain/subject: structuring; w.
- Formula and window: count abs(100*(amount_minor - T.amount_minor)) <= 5*T.amount_minor in R_wallet(7d) / count R_wallet(7d).
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, 1]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable structuring activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 9. `wallet_band_share_7d_inclusive`

- Domain/subject: structuring; w.
- Formula and window: count 700000 <= amount_minor <= 1050000 in R_wallet(7d) / count R_wallet(7d).
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, 1]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable structuring activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 10. `wallet_count_acceleration_1h`

- Domain/subject: structuring; w.
- Formula and window: count R_wallet(1h) / max(1, count B_wallet(1h)/672).
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: -1.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable structuring activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 11. `receiver_unique_sources_24h_inclusive`

- Domain/subject: network; receiver.
- Formula and window: distinct senders in R_inflow(24h); add T only for W2W.
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable network activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 12. `receiver_inflow_count_24h_inclusive`

- Domain/subject: network; receiver.
- Formula and window: count R_inflow(24h); add T only for W2W.
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable network activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 13. `receiver_inflow_acceleration_24h`

- Domain/subject: network; receiver.
- Formula and window: count R_inflow(24h) / max(1, count B_inflow(24h)/28).
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: -1.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable network activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 14. `sender_unique_destinations_24h_inclusive`

- Domain/subject: network; sender.
- Formula and window: distinct receivers in R_outflow(24h); add T only for W2W.
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable network activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 15. `sender_outflow_count_24h_inclusive`

- Domain/subject: network; sender.
- Formula and window: count R_outflow(24h); add T only for W2W.
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable network activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 16. `sender_outflow_acceleration_24h`

- Domain/subject: network; sender.
- Formula and window: count R_outflow(24h) / max(1, count B_outflow(24h)/28).
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: -1.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable network activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 17. `current_return_path_length`

- Domain/subject: network; current sender/receiver.
- Formula and window: length of selected prior chronological simple return path, 1..5 edges; 0 if absent/non-W2W.
- Temporal scope: PRIOR-ONLY graph + CURRENT endpoints/type; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, 5]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable network activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 18. `current_return_amount_ratio`

- Domain/subject: network; selected path.
- Formula and window: T.amount_minor / first selected path edge amount_minor; no monetary gate.
- Temporal scope: PRIOR graph + CURRENT amount; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: -1.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable network activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 19. `wallet_observed_onward_funding_share_24h`

- Domain/subject: network; outward wallet.
- Formula and window: O/F for current outward role and valid prior W2W anchor; 0 for Cash-In.
- Temporal scope: PRIOR + CURRENT outward amount; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: -1.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable network activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 20. `wallet_prior_funding_age_hours`

- Domain/subject: network; outward wallet.
- Formula and window: (t - anchor.timestamp) / 1h; absent/non-outward is missing.
- Temporal scope: PRIOR funding + CURRENT time/type/endpoints; only the named current fields are used.
- Units: hours. Valid range: [0, 24]; missing: -1.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable network activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 21. `agent_service_count_1h_inclusive`

- Domain/subject: agent; agent.
- Formula and window: count R_service(1h); 0 without agent.
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable agent activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 22. `agent_service_acceleration_1h`

- Domain/subject: agent; agent.
- Formula and window: count R_service(1h) / max(1, count B_service(1h)/672).
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: -1.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable agent activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 23. `agent_wallet_growth_ratio_7d`

- Domain/subject: agent; agent.
- Formula and window: distinct wallets R_service(7d) / max(1, median distinct counts in four preceding disjoint 7d buckets).
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: -1.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable agent activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 24. `agent_new_wallet_share_7d`

- Domain/subject: agent; agent.
- Formula and window: size(recent distinct wallets minus baseline distinct wallet union) / size(recent distinct wallets).
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, 1]; missing: -1.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable agent activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 25. `agent_top2_count_share_24h`

- Domain/subject: agent; agent.
- Formula and window: two largest per-wallet event counts / count R_service(24h); 0 without agent.
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, 1]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable agent activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 26. `agent_top2_share_change_24h`

- Domain/subject: agent; agent.
- Formula and window: recent top2 share minus independently ranked pooled B_service(24h) top2 share.
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [-1, 1]; missing: -3.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable agent activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 27. `agent_cash_value_skew_24h`

- Domain/subject: agent; agent.
- Formula and window: (CashOutMinor - CashInMinor)/(CashOutMinor + CashInMinor) in R_service(24h); zero if no cash.
- Temporal scope: PRIOR + CURRENT cash only; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [-1, 1]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable agent activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 28. `agent_cash_count_skew_24h`

- Domain/subject: agent; agent.
- Formula and window: (CashOutCount - CashInCount)/(CashOutCount + CashInCount) in R_service(24h); zero if no cash.
- Temporal scope: PRIOR + CURRENT cash only; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [-1, 1]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable agent activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 29. `agent_cash_value_skew_change`

- Domain/subject: agent; agent.
- Formula and window: recent cash value skew minus cash value skew in B_service(24h).
- Temporal scope: PRIOR + CURRENT cash only; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [-2, 2]; missing: -3.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable agent activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 30. `wallet_history_coverage_days`

- Domain/subject: coverage; w.
- Formula and window: min(28, days from first prior observation of wallet endpoint/cash to t); 0 without prior history.
- Temporal scope: PRIOR-ONLY observation + CURRENT time/subject; only the named current fields are used.
- Units: days. Valid range: [0, 28]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable coverage activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 31. `receiver_history_coverage_days`

- Domain/subject: coverage; receiver.
- Formula and window: min(28, days from first prior receiver entity observation to t); 0 without prior history.
- Temporal scope: PRIOR-ONLY observation + CURRENT time/subject; only the named current fields are used.
- Units: days. Valid range: [0, 28]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable coverage activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

#### 32. `agent_history_coverage_days`

- Domain/subject: coverage; agent.
- Formula and window: min(28, days from first prior service to t); 0 without agent/prior service.
- Temporal scope: PRIOR-ONLY observation + CURRENT time/subject; only the named current fields are used.
- Units: days. Valid range: [0, 28]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable coverage activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### Change log

A: enforce increasing edge keys during N3 traversal. B: use strict keys in every query, including same-time records. C: expire funding at the open 24h boundary; do not allow cash-only anchors. D: restore disjoint baselines, uncapped full-coverage tests and stream/count minima. E: use per-feature -1/-3 markers with valid negatives preserved. F: novelty is DISTINCT-wallet share, not service-event weighted. G: expand descriptive leakage checks and mutation tests. H: serialize two independent extractions and compare files. I: record explicit before/after allowlists and public-certificate hashes. J: freeze this version and its code hashes before extraction. Additional correction: assisted W2W structuring and funding use the sender, not the serviced receiver. No model-driven change is made.

V3 STAGE 10A COMPLETE — WAITING FOR APPROVAL.
