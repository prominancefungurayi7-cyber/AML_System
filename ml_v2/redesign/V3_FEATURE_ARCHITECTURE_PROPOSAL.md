# V3 feature architecture proposal — proposed revision 1

This is a **32-column starting proposal**, derived from the new decision point and Stage 7 findings. It is not an implemented feature contract, a claim that 32 is mathematically minimal, or permission to promote Stage 6 candidates. Feature count is not a research target. A separately authorized implementation/audit must freeze exact extraction and preprocessing before classifier testing.

## Design rationale

The frozen V2 pipeline emphasized prior aggregates. Stage 7 found only 1 of 48 N3 current closing edges detected and zero of 14 N4 first inbound transfers detected, while later N4 outflow/exit recall was 60.4%. N3 network-group diagnostic AUC against H6 was 0.530. Those results justify representing a current edge against prior paths and distinguishing current outflow from funding. They do not justify predicting that V3 accuracy will improve: its target is different.

Receiver collection must be measured on the receiver; agent changes need a preceding service comparator. In Stage 7, A1 novel-wallet shares were 0.92 versus H7's 0.94 and A2 top-wallet shares 0.11 versus H8's 0.15. Absolute novelty or concentration does not by itself establish a meaningful change. Stage 6's eight additions did not improve Macro F1, so they are evidence against automatic promotion. The proposal uses a smaller number of purpose-specific quantities per domain and current-event semantics consistent with the redesigned target.

The reference evaluator and feature extractor use separate implementations. Features summarize observable facts; they cannot consume family predicates, onset flags, scenario metadata, private planned roles or truth witnesses. Exact compound onset rules are not exposed as features. Similarity between individual history measures and reference-rule ingredients is unavoidable in this synthetic approximation task and must be disclosed.

## Proposed logical columns

History/window, amount, service and eligibility semantics follow [the onset contract](V3_SCENARIO_ONSET_CONTRACT.md). “Inclusive” means strictly prior history plus T. A path feature reads prior graph edges and current endpoints; it never inserts a future edge. Each raw event is inserted into persistent history once, after both extraction and reference evaluation.

| ID / proposed value | Definition and decision-time availability | Why needed / V2 relationship |
|---|---|---|
| E1 `current_amount_usd` | Current integer minor units / 100. Current field. | V2 used current amount inside history comparisons but lacked a general explicit amount input; the new gates depend on current values. |
| E2 `current_is_cash_in` | Current type indicator. | Distinguishes funding from outward movement. |
| E3 `current_is_cash_out` | Current type indicator; both E2/E3 zero means W2W. | Distinguishes cash exit and W2W; avoids arbitrary ordinal type coding. |
| S1 `wallet_count_1h_inclusive` | Count of current subject wallet activity in 1h including T. | Update prior burst count to reflect a threshold-crossing current event. |
| S2 `wallet_value_24h_inclusive` | Sum of current subject activity in 24h including T. | Update prior cumulative flow; no future episode total. |
| S3 `wallet_count_utc_day_inclusive` | Observed activity since current UTC midnight including T. | Same-day evidence available now. |
| S4 `wallet_active_hours_utc_day` | Distinct UTC hour buckets with activity since midnight including T. | Represents observed spread across clusters; same-day count alone loses it. |
| S5 `wallet_current_amount_cluster_share_7d` | Fraction of recent inclusive activity within 5% of T's amount. | Existing repetition concept with current-event inclusion. |
| S6 `wallet_band_share_7d_inclusive` | Fraction in the declared synthetic amount band over recent 7d including T. | Retains interpretable band history, without an onset flag. |
| S7 `wallet_count_acceleration_1h` | Inclusive 1h count / `max(1, preceding-28d count/672)`; missing if baseline ineligible. | Separates own-baseline change from a high absolute count. |
| N1 `receiver_unique_sources_24h_inclusive` | Distinct W2W senders to current receiver in 24h, with T counted only if W2W. | Replaces the coarse 7d receiver level with recent collection breadth. |
| N2 `receiver_inflow_count_24h_inclusive` | W2W inflow count over the same interval. | Separates repeated receipts from unique sources. |
| N3 `receiver_inflow_acceleration_24h` | Inclusive inflow count / `max(1, prior-28d inflow count/28)`; missing for an ineligible receiver baseline. | Makes the collection comparator observable; receipt level alone misses it. |
| N4 `sender_unique_destinations_24h_inclusive` | Distinct W2W receivers from current sender over 24h. | Recent dispersion evidence, including current destination. |
| N5 `sender_outflow_count_24h_inclusive` | W2W transfer count from current sender over 24h. | Keeps dispersion intensity distinct from destination cardinality. |
| N6 `sender_outflow_acceleration_24h` | Count / `max(1, preceding-28d outflow count/28)`; missing for ineligible baseline. | Distinguishes ordinary recurring payouts from change. |
| N7 `current_return_path_length` | On current W2W `s→r`, shortest temporally ordered simple prior path `r→…→s` of 1–5 edges within 7d; zero if none/non-W2W. Select ties by latest first edge then lexicographic event keys. | Current-edge graph evidence absent from V2; no reference predicate/value-rule import. |
| N8 `current_return_amount_ratio` | T's amount / first edge amount of N7's selected path; missing if no path. | Unequal return-flow magnitude; topology alone cannot describe value relationships. |
| N9 `wallet_observed_onward_funding_share_24h` | O/F using the N4 observable temporal funding definitions, for current wallet outflows; zero on funding/inbound roles and missing on an outflow with no prior funding anchor. No label thresholds applied. | Replaces an unbounded prior out/in ratio; respects current causal role. |
| N10 `wallet_prior_funding_age_hours` | Time since the N4 funding anchor before T for an eligible current outflow; missing if absent. | Distinguishes timing of observed transit; the previous ratio discarded delay. |
| A1 `agent_service_count_1h_inclusive` | Agent service count in 1h including T, zero for direct W2W. | Current burst evidence. |
| A2 `agent_service_acceleration_1h` | Inclusive count / `max(1, preceding-28d service count/672)`; missing when baseline ineligible. | Compares to that agent's earlier exposure. |
| A3 `agent_wallet_growth_ratio_7d` | Recent inclusive unique-wallet count / `max(1, median of four preceding 7d distinct counts)`; missing when ineligible. | A population-change measure, not an absolute 7d level. |
| A4 `agent_new_wallet_share_7d` | Recent serviced-wallet fraction absent from the prior baseline's 28d union; missing when ineligible. | Complements growth level with observed population turnover. |
| A5 `agent_top2_count_share_24h` | Top-two wallet service-event share in recent inclusive 24h; zero when no service. | Short count concentration rather than V2's long-window value HHI. |
| A6 `agent_top2_share_change_24h` | A5 minus independently ranked top-two share of preceding 28d; missing for ineligible A2 baseline. | Distinguishes new concentration from stable concentrated service. |
| A7 `agent_cash_value_skew_24h` | Signed `(CashOutValue−CashInValue)/(CashOutValue+CashInValue)` in inclusive 24h, zero without cash. | Bounded float direction; assisted W2W contributes zero. |
| A8 `agent_cash_count_skew_24h` | Corresponding signed count skew, zero without cash. | Count and value direction can differ; V2 had only a value ratio. |
| A9 `agent_cash_value_skew_change` | A7 minus prior-baseline cash value skew; missing for ineligible A4 baseline. | Captures change from ordinary local cash demand. |
| Q1 `wallet_history_coverage_days` | Available observed partition history before T, capped at 28 days, for the current structuring subject. | Distinguishes insufficient observation coverage from low activity. |
| Q2 `receiver_history_coverage_days` | Corresponding coverage for current receiver, capped at 28. | Receiver baseline opportunity may differ from sender history. |
| Q3 `agent_history_coverage_days` | Corresponding agent coverage, zero for no agent. | Exposes observation availability without private activation dates. |

Coverage starts at the later of the partition observation start and the entity's first observed event; it is not the private activation timestamp. Source histories still require the count conditions specified for each ratio. Missing ratios must remain distinguishable from true zeros: use models with native missing-value support or a Train-fitted imputer with a preregistered fixed set of missingness indicators. If indicators expand 32 logical columns, record the exact transformed names/count before fitting any candidates. No Validation-based discovery of missingness columns is allowed.

## What happens to the old 30

No V2 column or formula is edited. The V3 proposal retains the concepts of burst count, cumulative value, same-day count, repeated-amount share, band-history share, inbound/outbound counterparties, agent burst/novelty and cash direction, with explicit changes where current T or a baseline comparator is necessary.

Long-window entropy, top-value share, repeated-receiver share, set change, shared-counterparty concentration, generic prior reciprocity ratio, wallet dispersion, agent long-window HHI, high-value share, hourly z-scores and several duplicate agent volume levels are not automatically copied into the V3 core. Their removal is a proposal about redundancy and scope, not evidence of uselessness. Preserve a separately named port of V2's 30 definitions as a V3 development comparator if its extraction can be independently audited. The two streams must never be silently concatenated or compared using different labels/rows.

## Limits and a bounded future feature audit

The selected N3 path is a lossy summary if multiple return paths exist: the reference could qualify a different path. N4 is a funding proxy, not exact fund attribution. Rate floors, small baselines and pooled-vs-recent concentration can distort ratios. The core also omits some reference conjunction ingredients, such as exact S1 largest-fragment share, so it does not promise complete oracle reconstruction. These are explicit architecture risks to test with hand-built causal examples before model fitting.

For a future authorized audit, compare the frozen V2-definition port, the proposed 32-column representation, and a single leave-domain-extension-out ablation for each of the three domains, on identical V3 Train/Validation targets. Use a fixed diagnostic model and fixed 0.50 threshold, and inspect family, onset and hard-negative results rather than choosing on tiny Macro F1 differences. A discovered semantic omission must be resolved and versioned before the feature contract is frozen; performance-driven changes after testing require a new experiment revision. Stage 8 implements none of these comparisons.
