# MODEL V2 — STAGE 3 FEATURE CONTRACT

Status: frozen before development matrix construction. Version: `v2-feature-contract-1`.

This contract defines exactly 30 numerical features. It is a clean V2 implementation; V1 code is neither imported nor modified. Amounts are converted from integer cents to USD before feature arithmetic. USD 10,000 is a synthetic research threshold, not a regulatory threshold.

## Global event and history semantics

For every current event, the behavioural wallet is `serviced_wallet` for Cash-In/Cash-Out and `sender_wallet` for Wallet-to-Wallet. Wallet activity history contains events in which that wallet was the behavioural wallet. Cash records therefore contribute to activity counts, values and amount-pattern features. They never create wallet edges. Wallet-network history contains only actual Wallet-to-Wallet edges, whether direct or agent-assisted. Receiver-side history is used only by explicitly inbound or pass-through features.

Agent history contains all prior events attributed to the current `agent_id`: Cash-In, Cash-Out and agent-assisted Wallet-to-Wallet. Direct transfers have no agent and all 14 agent features equal `0.0`. The serviced wallet is the sole wallet associated with an agent service event, avoiding double attribution of an agent-assisted transfer. Only Cash-In/Cash-Out contributes to agent float direction; transfer principal does not.

History is partition-local and strictly precedes the current `(event_timestamp, transaction_id)`. Every rolling window is lower-bound inclusive and current-event exclusive: `current_time-window <= prior_time`, plus strict lexicographic ordering. Same-day means the same UTC date. State is read before the current event is added. All-prior means every earlier event in the partition.

Empty histories, zero denominators, insufficient z-score baselines and zero variance produce `0.0`. Population or future imputation is forbidden. Ratios are unitless. Counts are event or distinct-entity counts. Value sums and dispersion are in USD. Entropy uses natural logarithms. The final matrix is finite `float64`-compatible data in the exact order below; identifiers and metadata are kept only in separate join files.

## Exact definitions

| # | Feature | Subject/history and formula | Current fields | Cold start / range |
|---:|---|---|---|---|
| 1 | `structuring_prior_tx_count_1h` | Behavioural-wallet activity in prior 1h; count. All event types count. | Behavioural wallet, time, ID | 0; integer ≥0 |
| 2 | `structuring_prior_value_sum_24h` | Sum USD amount of behavioural-wallet activity in prior 24h. All event types count. | Behavioural wallet, time, ID | 0 USD; ≥0 |
| 3 | `structuring_same_day_prior_tx_count` | Count of behavioural-wallet activity earlier on current UTC date. | Behavioural wallet, date, time, ID | 0; integer ≥0 |
| 4 | `structuring_repeated_amount_ratio_7d` | Fraction of prior 7d behavioural-wallet events whose amount is within 5% of current USD amount: `abs(h-current) <= .05*current`. | Current amount permitted | 0; [0,1] |
| 5 | `structuring_amount_cluster_dispersion_7d` | Population coefficient of variation `population_std(amounts)/mean(amounts)` over prior 7d behavioural-wallet amounts. | No current amount | 0 for <2 values or zero mean; ≥0 |
| 6 | `structuring_near_threshold_history_ratio_7d` | Fraction of prior 7d behavioural-wallet amounts in `[7000,10500]` USD. | No current amount | 0; [0,1] |
| 7 | `network_outbound_counterparty_count_7d` | Distinct receivers on prior 7d Wallet-to-Wallet edges sent by current sender. Cash excluded. | Sender permitted | 0; integer ≥0 |
| 8 | `network_inbound_counterparty_count_7d` | Distinct senders on prior 7d Wallet-to-Wallet edges received by current receiver. Cash excluded. | Receiver permitted | 0; integer ≥0 |
| 9 | `network_outbound_counterparty_entropy_30d` | Natural-log entropy of prior 30d outbound USD value shares by receiver for current sender. Cash excluded. | Sender permitted | 0; ≥0 |
| 10 | `network_top_counterparty_value_share_30d` | Maximum receiver USD total divided by all prior 30d outbound USD value for current sender. | Sender permitted | 0; [0,1] |
| 11 | `network_current_receiver_is_new` | For current Wallet-to-Wallet only: 1 if receiver has no all-prior outbound edge from sender, else 0. Cash current events return 0. | Current type, sender, receiver | First real edge=1; {0,1} |
| 12 | `network_repeated_receiver_ratio_30d` | For current sender, fraction of prior 30d outbound edges whose receiver occurs at least twice in that window. | Sender permitted | 0; [0,1] |
| 13 | `network_reciprocal_flow_ratio_7d` | For current sender, `|outbound counterparties ∩ inbound counterparties| / |union|` over prior 7d Wallet-to-Wallet edges. | Sender permitted | 0; [0,1] |
| 14 | `network_counterparty_set_change_7d` | Jaccard distance between sender outbound counterparties in `[T-7d,T)` and `[T-14d,T-7d)`: `1-|intersection|/|union|`. | Sender permitted | 0 if union empty; [0,1] |
| 15 | `network_pass_through_ratio_24h` | For behavioural wallet, prior 24h Wallet-to-Wallet outbound USD divided by inbound USD. Cash excluded. | Behavioural wallet permitted | 0 if inbound=0; ≥0 |
| 16 | `network_shared_counterparty_concentration_7d` | Among wallets reached by current sender in prior 7d, maximum fraction sharing any one additional counterparty through either-direction prior 7d Wallet-to-Wallet edges. The sender itself is excluded from “additional”. | Sender permitted | 0; [0,1] |
| 17 | `agent_prior_tx_count_1h` | Current agent’s prior 1h attributed service-event count. | Agent permitted | 0; integer ≥0 |
| 18 | `agent_prior_tx_count_7d` | Current agent’s prior 7d attributed service-event count. | Agent permitted | 0; integer ≥0 |
| 19 | `agent_prior_value_sum_1h` | Sum USD amount of current agent’s prior 1h attributed events. Transfer values are service volume, not float flow. | Agent permitted | 0 USD; ≥0 |
| 20 | `agent_prior_value_sum_7d` | Sum USD amount of current agent’s prior 7d attributed events. | Agent permitted | 0 USD; ≥0 |
| 21 | `agent_unique_wallet_count_7d` | Distinct `serviced_wallet` values in current agent’s prior 7d events. | Agent permitted | 0; integer ≥0 |
| 22 | `agent_wallet_value_hhi_7d` | Sum of squared USD value shares grouped by `serviced_wallet` in prior 7d agent events. | Agent permitted | 0; (0,1] when nonempty |
| 23 | `agent_repeat_wallet_ratio_7d` | Fraction of prior 7d agent events whose serviced wallet appears at least twice in that window. | Agent permitted | 0; [0,1] |
| 24 | `agent_current_wallet_is_new` | 1 if current `serviced_wallet` has no all-prior event for current agent, else 0. | Current agent and serviced wallet | First=1; direct=0; {0,1} |
| 25 | `agent_inbound_outbound_value_ratio_7d` | Prior 7d Cash-Out USD (`inbound` to float) divided by Cash-In USD (`outbound` from float). Agent-assisted transfers excluded from numerator/denominator. | Agent permitted | 0 if Cash-In denominator=0; ≥0 |
| 26 | `agent_high_value_event_share_7d` | Baseline is median USD amount of all prior 30d agent events. If ≥3 baseline events, fraction of prior 7d events exceeding `2*median`; otherwise 0. | Agent permitted | 0; [0,1] |
| 27 | `agent_hourly_tx_zscore_30d` | Current-hour prior count standardized against totals of completed, nonempty UTC hours in prior 30d. Requires ≥7 completed nonempty hours and positive population SD. | Current hour/time/ID, agent | 0 otherwise; unbounded |
| 28 | `agent_hourly_value_zscore_30d` | Current-hour prior USD sum standardized against completed, nonempty UTC-hour USD totals in prior 30d. Same baseline rule as #27. | Current hour/time/ID, agent | 0 otherwise; unbounded |
| 29 | `agent_burst_concentration_7d` | Maximum count in any full-date UTC 15-minute bucket divided by prior 7d agent-event count. | Agent permitted | 0; (0,1] when nonempty |
| 30 | `agent_shared_wallet_flow_concentration_7d` | For serviced wallets used by current agent in prior 7d, inspect all prior partition-local 7d Wallet-to-Wallet edges. Return maximum number of those agent wallets linked to one external wallet divided by the number of agent wallets. Cash excluded from edges. | Agent permitted | 0; [0,1] |

The `feature_names.json` file is normative for matrix order. X contains no transaction type/channel flags or identifiers. `row_ids.csv` separately records `row_index,transaction_id` for audit joins. `y.csv` is copied only from `ground_truth.target` in the same transaction-ID order.
