# MODEL V2 — STAGE 3 FEATURE PIPELINE AND AUDIT

Dataset: `epocash_aml_synthetic_100k_v2`

**Overall result: CONDITIONAL PASS.** The causal development feature pipeline, matrix construction, tests, reproducibility check, leakage diagnostics and V1-protection check passed. Several correctly defined ratios and z-scores have large finite tails that require an explicit later preprocessing decision. No definition was changed in response to label separation.

No model was trained. Final-test and independent transactions, labels and feature distributions were not loaded or inspected. No holdout feature matrix was constructed.

## 1. Files created

- `src/feature_pipeline.py`, `src/feature_audit.py`, and `src/run_stage3.py`.
- `reports/V2_STAGE3_FEATURE_CONTRACT.md` (frozen before extraction).
- `features/development/train/{X.csv,y.csv,row_ids.csv,feature_names.json}`.
- `features/development/validation/{X.csv,y.csv,row_ids.csv,feature_names.json}`.
- Four `test_stage3_*.py` test files.
- `reports/stage3_feature_audit.json`, `stage3_reproducibility.json`, `stage3_v1_protection.json`, `stage3_tests.txt`, and this report.

`X.csv` contains only 30 floating-point columns without identifiers or metadata. `y.csv` contains only the binary target. `row_ids.csv` separately retains row index and transaction ID for audit joins.

## 2. Exact feature order

1. `structuring_prior_tx_count_1h`
2. `structuring_prior_value_sum_24h`
3. `structuring_same_day_prior_tx_count`
4. `structuring_repeated_amount_ratio_7d`
5. `structuring_amount_cluster_dispersion_7d`
6. `structuring_near_threshold_history_ratio_7d`
7. `network_outbound_counterparty_count_7d`
8. `network_inbound_counterparty_count_7d`
9. `network_outbound_counterparty_entropy_30d`
10. `network_top_counterparty_value_share_30d`
11. `network_current_receiver_is_new`
12. `network_repeated_receiver_ratio_30d`
13. `network_reciprocal_flow_ratio_7d`
14. `network_counterparty_set_change_7d`
15. `network_pass_through_ratio_24h`
16. `network_shared_counterparty_concentration_7d`
17. `agent_prior_tx_count_1h`
18. `agent_prior_tx_count_7d`
19. `agent_prior_value_sum_1h`
20. `agent_prior_value_sum_7d`
21. `agent_unique_wallet_count_7d`
22. `agent_wallet_value_hhi_7d`
23. `agent_repeat_wallet_ratio_7d`
24. `agent_current_wallet_is_new`
25. `agent_inbound_outbound_value_ratio_7d`
26. `agent_high_value_event_share_7d`
27. `agent_hourly_tx_zscore_30d`
28. `agent_hourly_value_zscore_30d`
29. `agent_burst_concentration_7d`
30. `agent_shared_wallet_flow_concentration_7d`

The contract report provides the exact formula, subject, history, current fields, event-type treatment, units, cold-start rule, denominator rule and expected range for every feature.

## 3. Semantics adopted

The behavioural wallet is the serviced wallet for cash and the sender for Wallet-to-Wallet. Cash contributes to wallet activity and amount-pattern history. Only actual Wallet-to-Wallet transactions create graph edges, so cash cannot create self-counterparties, reciprocity, novelty, cycles or graph concentration.

All agent-mediated events contribute to service activity. `serviced_wallet` is the single agent-associated wallet. Agent-assisted transfer values measure service volume but never float direction. The directional ratio uses only explicit Cash-Out over Cash-In. Direct transfers receive fourteen neutral agent values.

Amounts are converted from cents to USD. Windows are partition-local, lower-bound inclusive and current-event exclusive under `(timestamp, transaction_id)`. State updates occur after vector emission. Empty history, zero denominator, insufficient hourly baseline and zero variance produce `0.0`.

## 4. Matrices and targets

| Partition | X shape | y shape | Normal | Suspicious | NaN | Infinity |
|---|---:|---:|---:|---:|---:|---:|
| Train | `(60000, 30)` | `(60000,)` | 52,800 | 7,200 | 0 | 0 |
| Validation | `(15000, 30)` | `(15000,)` | 13,200 | 1,800 | 0 | 0 |

Feature order is exact, row IDs are unique and increasing, and y comes only from `ground_truth.target` through the development loader.

## 5. Numerical audit

No feature is constant or near-constant under the predeclared 99% modal-value rule in either partition.

| # | Feature (short) | Train min / mean / median / max / zero% | Validation min / mean / median / max / zero% |
|---:|---|---|---|
|1|prior count 1h|0 / .4105 / 0 / 23 / 87.04|0 / .3950 / 0 / 22 / 87.86|
|2|prior value 24h|0 / 4971.52 / 0 / 264227.57 / 58.25|0 / 5560.26 / 0 / 169303.60 / 57.89|
|3|same-day count|0 / 1.2150 / 0 / 25 / 69.08|0 / 1.1735 / 0 / 28 / 69.07|
|4|repeat amount|0 / .0525 / 0 / 1 / 87.72|0 / .0528 / 0 / 1 / 87.35|
|5|amount dispersion|0 / .6723 / .5393 / 4.7269 / 42.05|0 / .6562 / .5205 / 4.1930 / 41.98|
|6|threshold history|0 / .0525 / 0 / 1 / 84.16|0 / .0528 / 0 / 1 / 84.28|
|7|outbound CP count|0 / 1.7545 / 1 / 24 / 38.90|0 / 1.7064 / 1 / 17 / 39.34|
|8|inbound CP count|0 / 1.1867 / 1 / 16 / 40.53|0 / 1.1633 / 1 / 17 / 41.23|
|9|outbound entropy|0 / .5868 / .5024 / 3.0428 / 21.86|0 / .5935 / .5018 / 2.5462 / 22.16|
|10|top CP share|0 / .6761 / .7372 / 1 / 7.99|0 / .6651 / .7230 / 1 / 8.19|
|11|receiver new|0 / .4227 / 0 / 1 / 57.74|0 / .4086 / 0 / 1 / 59.14|
|12|repeat receiver|0 / .1332 / 0 / 1 / 74.44|0 / .1398 / 0 / 1 / 74.09|
|13|reciprocal ratio|0 / .0129 / 0 / 1 / 95.75|0 / .0168 / 0 / 1 / 94.72|
|14|set change|0 / .7743 / 1 / 1 / 21.99|0 / .7675 / 1 / 1 / 22.60|
|15|pass-through ratio|0 / 12.7804 / 0 / 37018.8760 / 93.19|0 / 9.0534 / 0 / 8297.8840 / 93.49|
|16|shared CP concentration|0 / .3230 / .1429 / 1 / 44.50|0 / .3218 / .1667 / 1 / 45.01|
|17|agent count 1h|0 / .7217 / 0 / 30 / 77.95|0 / .6745 / 0 / 28 / 78.01|
|18|agent count 7d|0 / 20.3764 / 16 / 128 / 25.24|0 / 21.4077 / 16 / 113 / 25.21|
|19|agent value 1h|0 / 2076.11 / 0 / 133930.82 / 77.95|0 / 2145.36 / 0 / 183137.47 / 78.01|
|20|agent value 7d|0 / 67383.44 / 47392.15 / 651157.31 / 25.24|0 / 76791.88 / 47297.48 / 455503.20 / 25.21|
|21|agent unique wallets|0 / 15.1514 / 12 / 93 / 25.24|0 / 15.2605 / 11 / 71 / 25.21|
|22|agent wallet HHI|0 / .2403 / .1794 / 1 / 25.24|0 / .2439 / .1741 / 1 / 25.21|
|23|agent repeat wallet|0 / .2093 / .1364 / 1 / 44.69|0 / .2381 / .2 / 1 / 41.23|
|24|agent wallet new|0 / .4683 / 0 / 1 / 53.17|0 / .2943 / 0 / 1 / 70.57|
|25|agent float ratio|0 / 12.7400 / .5218 / 12590.2038 / 28.78|0 / 13.2025 / .5183 / 9488.0200 / 28.73|
|26|agent high-value share|0 / .2893 / .3333 / 1 / 27.12|0 / .2932 / .3438 / 1 / 26.97|
|27|hourly count z|-8.7781 / -.8057 / -.7992 / 108.6560 / 30.08|-8.3103 / -.8041 / -.8085 / 107.3906 / 30.12|
|28|hourly value z|-2.2425 / -.1703 / -.4988 / 402.7356 / 27.51|-1.6488 / -.2554 / -.4986 / 25.2429 / 27.51|
|29|burst concentration|0 / .0973 / .0645 / 1 / 25.24|0 / .0990 / .0645 / 1 / 25.21|
|30|shared-wallet flow|0 / .0850 / .0667 / 1 / 25.55|0 / .1105 / .0952 / 1 / 25.53|

The JSON audit preserves full precision, distinct-value counts and class-conditional summaries.

## 6. Safety and semantic tests

All 12 tests pass. Hand-derived sequences cover the requested structuring, network, pass-through, agent count/value, unique-wallet, concentration, novelty, direction, z-score and burst semantics. Temporal tests cover current and future exclusion, equal-timestamp lower-ID ordering, partition separation, label/scenario independence and identifier exclusion.

The pipeline calls the approved loader separately for Train and Validation. Its source contains no holdout partition literal or holdout output path and imports no application/V1 scoring module.

## 7. Shortcut diagnostics

In both partitions, every feature’s normal and suspicious ranges overlap; both classes have nonzero observations; no feature is nonzero only in one class; and no feature value identifies an entire target class. Some discrete or rounded values supported by at least ten rows occur in only one class, mostly in the larger normal population and tails. Those exact-value lists remain in `stage3_feature_audit.json`.

This is descriptive and does not prove that a one-variable threshold or feature combination lacks predictive power. No classifier, feature selection, validation optimization or regeneration was performed.

## 8. Review-sensitive findings

- The raw pass-through ratio reaches 37,018.88/8,297.88 (Train/Validation) because small inbound denominators can accompany substantial outbound flow.
- The agent float ratio reaches 12,590.20/9,488.02 for the same reason.
- Hourly count z-scores reach about 109; hourly value z-score reaches 402.74 in Train versus 25.24 in Validation. Sparse nonempty-hour baselines and low variance amplify bursts.
- Pass-through is zero for about 93% and reciprocal flow for about 95%; neither crosses the 99% near-constant threshold.
- `agent_current_wallet_is_new` means differ (0.468 Train, 0.294 Validation) and should be monitored without consulting holdouts.
- Hourly baselines contain completed nonempty hours rather than zero-activity hours, as frozen in the contract.

Any clipping, transformation, scaling or redesign requires a later predeclared decision learned on Train only.

## 9. Reproducibility and protection

Two complete extractions produced identical feature order, X, y, row order and SHA-256 hashes for all eight output files. Temporary duplicates were removed. All 28 Stage 2 partition-file hashes still match the generation manifest. Before/after hashes matched for 347 protected V1/application files.

Stage 3 did not train or tune a model, select a threshold, construct holdout matrices, evaluate either holdout, compare V1/V2 performance, integrate V2 or switch the application model.

V2 STAGE 3 COMPLETE — WAITING FOR APPROVAL.
