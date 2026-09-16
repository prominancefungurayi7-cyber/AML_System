# Stage 10B — Final 30-Feature Specification & AI Architecture Lock

Status: **PASS — ARCHITECTURE LOCKED**  
Date: 2026-09-14  
Mode: Specification and documentation only.

## 1. Purpose and scope

This lock defines the future AML decision-support feature matrix for an EcoCash-style Zimbabwe mobile-money setting. It identifies suspicious behavioural patterns for investigation; it does not prove money laundering.

The only approved detection domains are structuring, wallet/transaction-network behaviour, and agent behaviour. Historical 18-feature, Stage 24, rule/risk-labelled, banking-specific, cross-border, and three-class designs are not authoritative for this lock.

## 2. Architecture summary

The future matrix is exactly X[30] plus separate binary y:

| Category | Features |
| --- | ---: |
| Structuring | 6 |
| Wallet/transaction network | 10 |
| Agent behaviour | 14 |
| Total X columns | **30** |
| Separate y column | ground_truth_label |

The canonical, machine-readable definitions—including raw fields, formula, window, type, range, cold-start rule, leakage risk, and rationale—are in [stage10b_feature_specification.json](stage10b_feature_specification.json). That JSON is the authoritative allow-list for implementation.

## 3. Final 30-feature table

### Structuring — 6

| Feature | Formula / behavioural meaning | Window | Level |
| --- | --- | --- | --- |
| structuring_prior_tx_count_1h | Count sender's earlier outgoing events | 1 hour | Wallet |
| structuring_prior_value_sum_24h | Sum sender's earlier outgoing value | 24 hours | Wallet |
| structuring_same_day_prior_tx_count | Count sender's earlier events on event day | Event day | Wallet |
| structuring_repeated_amount_ratio_7d | Prior amounts within 5% of current amount / prior count | 7 days | Wallet |
| structuring_amount_cluster_dispersion_7d | Prior amount standard deviation / prior mean | 7 days | Wallet |
| structuring_near_threshold_history_ratio_7d | Prior amounts from 90% of configured reporting threshold to just below it / prior count | 7 days | Wallet |

The last feature is a measured historical behavioural ratio, not a rule result. Its implementation must not import or reuse a rule-engine flag.

### Wallet/transaction network — 10

| Feature | Formula / behavioural meaning | Window | Level |
| --- | --- | --- | --- |
| network_outbound_counterparty_count_7d | Distinct prior receivers | 7 days | Relationship |
| network_inbound_counterparty_count_7d | Distinct prior senders to wallet | 7 days | Relationship |
| network_outbound_counterparty_entropy_30d | Entropy of prior receiver distribution | 30 days | Relationship |
| network_top_counterparty_value_share_30d | Largest receiver value / total outbound value | 30 days | Relationship |
| network_current_receiver_is_new | Current receiver absent from prior outbound history | All prior | Relationship |
| network_repeated_receiver_ratio_30d | Prior events to repeat receivers / prior outbound events | 30 days | Relationship |
| network_reciprocal_flow_ratio_7d | Counterparties with both directions / active counterparties | 7 days | Relationship |
| network_counterparty_set_change_7d | One minus Jaccard similarity of two prior 7-day receiver sets | 14 days | Relationship |
| network_pass_through_ratio_24h | Prior outbound value / prior inbound value | 24 hours | Wallet |
| network_shared_counterparty_concentration_7d | Maximum second-order shared-neighbour share | 7 days | Relationship |

### Agent behaviour — 14

| Feature | Formula / behavioural meaning | Window | Level |
| --- | --- | --- | --- |
| agent_prior_tx_count_1h | Earlier agent-attributed transaction count | 1 hour | Agent |
| agent_prior_tx_count_7d | Earlier agent-attributed transaction count | 7 days | Agent |
| agent_prior_value_sum_1h | Earlier agent-attributed value | 1 hour | Agent |
| agent_prior_value_sum_7d | Earlier agent-attributed value | 7 days | Agent |
| agent_unique_wallet_count_7d | Distinct earlier wallets associated with agent | 7 days | Agent |
| agent_wallet_value_hhi_7d | Wallet value concentration at agent | 7 days | Agent |
| agent_repeat_wallet_ratio_7d | Events involving repeated agent-wallet relationships / agent events | 7 days | Agent |
| agent_current_wallet_is_new | Current initiating wallet absent from earlier agent history | All prior | Agent relationship |
| agent_inbound_outbound_value_ratio_7d | Earlier agent outbound value / inbound value | 7 days | Agent |
| agent_high_value_event_share_7d | Earlier events above two times agent's prior-30-day median / events | 7 days + baseline | Agent |
| agent_hourly_tx_zscore_30d | Earlier completed current-hour activity versus prior completed-hour count baseline | 30 days | Agent |
| agent_hourly_value_zscore_30d | Earlier completed current-hour value versus prior completed-hour value baseline | 30 days | Agent |
| agent_burst_concentration_7d | Largest 15-minute agent event bucket / agent events | 7 days | Agent |
| agent_shared_wallet_flow_concentration_7d | Maximum common-external-counterparty share across agent wallets | 7 days | Agent relationship |

agent_id is used only as a relational grouping key. It is never an X column.

## 4. Formal temporal and cold-start contracts

For an event e=(event_timestamp, event_sequence), a feature may use the current event and only records with an earlier lexicographic pair. The future raw data must assign a unique deterministic event_sequence at generation time. Equal timestamps are ordered by that sequence; a later equal-timestamp event cannot influence an earlier one.

No feature may use future transactions, future wallet or agent behaviour, labels, risk scores, rules, alerts, investigations, or model outputs. Current-hour agent z-scores use only earlier events within the current hour and completed historical hours; they never use the completed future portion of the current hour.

Cold start is deliberately uniform: counts and sums are zero; ratios, shares, entropy, concentration, dispersion, acceleration and z-scores are zero as neutral/no-evidence; new-relationship flags remain zero until eligible history exists. Transactions with agent_id NULL receive zero for all agent-context features. These values represent unavailable history, never a target class.

## 5. Raw data and agent model requirements

Minimum transaction fields: immutable transaction_id; event_timestamp; deterministic event_sequence; sender_wallet; receiver_wallet; amount; transaction_type; transaction_direction; channel; nullable agent_id; and generation provenance kept outside X.

Minimum agent entity fields: immutable agent_id (join/grouping key only), agent status, and audit metadata. An agent-mediated transaction carries its attributable agent_id; a non-agent-mediated transaction uses NULL. Agent metrics are calculated solely from earlier transactions attributable to that agent. No merchant, banking-core, cryptocurrency, blockchain, biometric, or KYC-replacement fields are required.

## 6. Binary target and ground truth

ground_truth_label is exactly 0=normal or 1=suspicious_pattern_scenario. A scenario ground-truth generator assigns it independently before feature extraction. It must never be derived from feature values, thresholds, rules, risk scores/levels, alerts, investigations, predictions, or post-hoc decisions.

Required provenance metadata, stored outside X: scenario_id, scenario_type, scenario_category, ground_truth_label, signal_strength, scenario_source, affected_wallets, affected_agent, generation_metadata, and reproducibility seed/version. Metadata explains why an event was generated; it is not predictive input.

## 7. Feature-matrix contract

X must contain the 30 JSON feature_allow_list names in precisely that set—no more and no fewer. The future pipeline must fail closed if a column is missing, duplicated, or outside the allow-list.

Explicitly excluded from X: transaction/customer/wallet/agent identifiers; sender/receiver wallets; timestamp and sequence; all scenario and provenance metadata; ground_truth_label; risk scores/levels; rule outputs; alerts; investigations; and all future-derived data.

## 8. Isolation and independent evaluation methodology

Group assignment occurs before generation and feature extraction. Train, validation, final-test, and independent-evaluation populations must have disjoint customer/wallet groups and disjoint agent groups. A wallet or agent appears in one group only. Transactions must not form cross-group wallet edges; any required external counterparty must be a group-local synthetic entity, not a wallet belonging to another evaluation group. Histories and aggregates are calculated within the event's own group and only from earlier events.

The independent evaluation population must use unseen wallet/customer and agent populations, unseen scenario instances, and different behavioural combinations. A different random seed alone is insufficient: its population assignment, scenario parameter ranges, provenance version, and non-overlap evidence must be recorded and verified. Exact group sizes, class distribution, wallet population, and agent population are **UNRESOLVED — TO BE APPROVED BEFORE DATASET GENERATION**.

## 9. Future 100,000-transaction dataset specification

The approved scale is 100,000 transactions. Future generation must create temporally ordered normal behaviour plus independent suspicious structuring, network, and agent scenarios; behavioural and scenario diversity; group-local entity populations; deterministic reproduction metadata; separate ground truth; and the 30-feature allow-list validation gate. No final class distribution, customer/wallet count, agent count, or allocation has been invented here; each requires approval before generation.

## 10. Redundancy review

| Feature group | Result | Rationale |
| --- | --- | --- |
| Structuring count, value, same-day count | Acceptable complementary | Different time/value dimensions of fragmentation. |
| Repeated amount ratio and cluster dispersion | Acceptable complementary | One compares current value to history; one measures historical spread. |
| Outbound count, entropy, top-share, repeated ratio | Acceptable complementary | Breadth, distribution shape, dominance and persistence are distinct. |
| Agent 1h/7d counts and values | Acceptable complementary | Burst versus sustained activity and count versus value are distinct. |
| Agent concentration features | Acceptable complementary | Wallet-value concentration, repeat-wallet persistence and shared-flow coordination measure different mechanisms. |
| Network/agent pass-through ratios | Acceptable complementary | One describes wallet behaviour; the other describes agent-attributable flow. |

No pair is classified redundant under the locked definitions. Future implementation must compute and document correlation diagnostics, but may not remove or add features without a new approved specification revision.

## 11. Model-development principle and unresolved decisions

No model is selected, trained, tuned, or evaluated in Stage 10B. After a compliant dataset exists, multiple suitable supervised algorithms may be compared using validation and independent evaluation; the old Gradient Boosting model is not preselected.

Before Stage 11, approve: final class distribution; wallet/customer and agent counts; reporting-threshold configuration governance; exact transaction-direction convention; scenario catalogue and parameter ranges; group allocation; independent-population protocol; and reproducibility/version controls.

## 12. Final validation

- [x] Exactly 30 unique feature names
- [x] Exactly 6 structuring, 10 network and 14 agent features
- [x] Formula, raw data, history window, prediction-time rule, cold start, type, range, leakage analysis and rationale are present in JSON for every feature
- [x] No identifier, rule/risk output, target or future information is an X feature
- [x] Binary independent target, deterministic temporal ordering, wallet/agent isolation and independent evaluation are defined
- [x] Dataset scale is 100,000 without inventing unresolved population or class counts
- [x] JSON and this Markdown use the same feature names and category counts

**Stage 10B ends here. No dataset was generated, no model was trained, and no existing application, ML code, database schema, historical dataset, or historical model was modified.**
