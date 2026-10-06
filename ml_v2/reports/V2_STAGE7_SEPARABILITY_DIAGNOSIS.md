# MODEL V2 — STAGE 7 DEEP SEPARABILITY DIAGNOSIS

**Diagnosis E — multiple factors are material.** Causal event position, overlap with deliberately similar normal episodes, and generator construction all contribute. The frozen 30 features also miss some observable context. The evidence does not support additional model tuning as the main next step. No model, label, feature, threshold, or dataset was changed.

## Method and limits

Only Train and Validation records were loaded for analysis. The frozen Stage 5 artifact `s5_gradient_boosting_060` supplied Validation probabilities at threshold 0.50. Episode IDs, family names, and normal-family metadata selected diagnostic cohorts after prediction; none entered the frozen model or a feature matrix. Episode positions use chronological transaction IDs of committed episode members; ordinary events remain interleaved in the global history but do not count toward episode position. All percentages below use Validation unless stated. Counts and exact values are in the six Stage 7 JSON outputs.

Prior-episode evidence categories are operational lower-bound proxies. `none` means the chosen motif has not appeared within the labelled episode; it does not prove the transaction is harmless or that all ordinary prior history is empty. `mature` means a specified repeated pattern exists before the current event; it does not prove illicit intent. The [causal observability report](V2_STAGE7_CAUSAL_OBSERVABILITY.md) states each proxy and its limits.

## Recall by event position and prior episode evidence

| Suspicious family | 1st | 2nd | 3rd | 4th+ | No motif | Partial | Mature |
|---|---:|---:|---:|---:|---:|---:|---:|
| variable_fragment_burst | 6.2% | 50.0% | 75.0% | 88.2% | 10.7% (16) | 21.3% (32) | 68.0% (102) |
| similar_amount_repetition | 0.0% | 8.3% | 33.3% | 48.2% | 8.0% (12) | 28.0% (42) | 64.0% (96) |
| distributed_same_day_fragmentation | 0.0% | 58.3% | 66.7% | 67.5% | 8.0% (12) | 19.3% (29) | 72.7% (109) |
| variable_near_threshold_history | 0.0% | 21.4% | 57.1% | 39.8% | 9.3% (14) | 32.0% (48) | 58.7% (88) |
| many_to_one_collection | 0.0% | 0.0% | 15.4% | 9.0% | 25.3% (38) | 17.3% (26) | 57.3% (86) |
| one_to_many_dispersion | 0.0% | 0.0% | 21.4% | 27.8% | 26.0% (39) | 18.7% (28) | 55.3% (83) |
| reciprocal_relationship_cycle | 0.0% | 0.0% | 0.0% | 3.1% | 12.0% (18) | 34.7% (52) | 53.3% (80) |
| wallet_pass_through | 7.1% | 0.0% | 35.7% | 63.0% | 26.0% (39) | 9.3% (14) | 64.7% (97) |
| agent_wallet_growth | 11.1% | 0.0% | 11.1% | 23.6% | 6.0% (9) | 18.0% (27) | 76.0% (114) |
| agent_wallet_concentration | 0.0% | 0.0% | 0.0% | 10.8% | 6.7% (10) | 61.3% (92) | 32.0% (48) |
| agent_temporal_burst | 30.0% | 20.0% | 50.0% | 65.0% | 6.7% (10) | 13.3% (20) | 80.0% (120) |
| agent_flow_imbalance | 0.0% | 0.0% | 0.0% | 5.8% | 6.7% (10) | 13.3% (20) | 80.0% (120) |

Each family has 150 suspicious Validation events. Quartile-position counts and recall are in `stage7_episode_position.json`. First-event recall is zero in 8 of 12 families. For several families recall rises sharply once episode history accumulates. This supports a causal timing problem, but late weakness in N1, N3, A1, A2, and A4 shows timing alone is insufficient.

## N3 reciprocal-cycle forensic result

Among 150 N3 events, 70 (46.7%) had no earlier reciprocal pair anywhere in the same episode. 80 (53.3%) followed a completed cycle elsewhere in the episode; Stage 5 recalled 2/80 (2.5%). No event had a completed prior cycle **involving a current endpoint** (0/150), and none had a prior reciprocal pair involving a current endpoint. These are distinct tests: a previous motif on other wallets cannot by itself establish the present edge's role.

The current edge closes a directed cycle in 48/150 events (32.0%). Stage 5 recalled 1 of these, versus 2 of the other 102. Thus many N3 labels precede an observable cycle on the current wallet pair, while a current-edge motif is available for some events but absent from the frozen representation. The generator creates disjoint complete cycles inside an episode; it does not guarantee an earlier cycle involving later edge endpoints.

## N4 pass-through roles

| Causal role | Events | Stage 5 recall |
|---|---:|---:|
| cash_funding | 25 | 28.0% |
| inbound_transfer | 14 | 0.0% |
| outbound_or_exit | 111 | 60.4% |

The first inbound transfer has no earlier onward movement in that episode. Later outbound or exit events have earlier episode funding and are much more detectable. The first cash-funding events may be detected through unrelated prior activity, not completed pass-through evidence. Role by event position is in `stage7_family_observability.json`.

## Local class overlap in frozen 30-feature space

A Train-fitted RobustScaler and five Euclidean neighbours were used. The fixed reference sample contains 15,000 Train normal and 6,000 Train suspicious events; suspicious cases are intentionally enriched to 28.6%. Distances were clipped to ±20 scaled units for stability. Neighbour fractions are geometry diagnostics, **not posterior probabilities** or a deployable classifier. 74.7% of suspicious Validation events have a mostly normal five-neighbour set; 15.2% of normal events have a mostly suspicious set.

| Domain | Suspicious events with mostly normal neighbours |
|---|---:|
| structuring | 64.2% |
| network | 81.8% |
| agent | 78.2% |

Among H1 normals, 41.9% have mostly suspicious neighbours; among H7 normals, 29.6% do. For N3, 90.6% of fourth-or-later events still have mostly normal neighbours. Family and episode-position neighbour results, plus all H1–H8 and routine normal results, are in `stage7_neighbour_overlap.json`. Sampling and the metric affect these fractions; they establish substantial local overlap under this particular representation and distance choice.

## Hard negatives and family-conditioned separability

| Suspicious family | Matched normal | Strongest frozen univariate AUC¹ | IQR overlap | Domain-group logistic AUC² | All-30 logistic AUC² |
|---|---|---:|---:|---:|---:|
| variable_fragment_burst | H1 | 0.681 (structuring_prior_value_sum_24h) | 0.341 | 0.686 | 0.758 |
| similar_amount_repetition | H2 | 0.674 (structuring_amount_cluster_dispersion_7d) | 0.474 | 0.382 | 0.672 |
| distributed_same_day_fragmentation | H1 | 0.726 (structuring_prior_tx_count_1h) | 0.167 | 0.797 | 0.843 |
| variable_near_threshold_history | H3 | 0.704 (network_outbound_counterparty_count_7d) | 0.250 | 0.485 | 0.707 |
| many_to_one_collection | H4 | 0.614 (network_inbound_counterparty_count_7d) | 0.500 | 0.606 | 0.546 |
| one_to_many_dispersion | H5 | 0.705 (structuring_repeated_amount_ratio_7d) | 0.000 | 0.697 | 0.778 |
| reciprocal_relationship_cycle | H6 | 0.634 (agent_prior_value_sum_7d) | 0.000 | 0.530 | 0.614 |
| wallet_pass_through | H5 | 0.635 (network_repeated_receiver_ratio_30d) | 0.280 | 0.757 | 0.712 |
| agent_wallet_growth | H7 | 0.714 (agent_hourly_value_zscore_30d) | 0.034 | 0.639 | 0.666 |
| agent_wallet_concentration | H8 | 0.634 (agent_inbound_outbound_value_ratio_7d) | 0.218 | 0.543 | 0.571 |
| agent_temporal_burst | H7 | 0.718 (agent_prior_tx_count_1h) | 0.333 | 0.658 | 0.672 |
| agent_flow_imbalance | H8 | 0.657 (agent_prior_value_sum_7d) | 0.616 | 0.653 | 0.668 |

¹ Direction-free absolute univariate ROC-AUC ranks the 30 existing values for a selected family versus its designed hard counterpart; selecting the best on Validation is exploratory and optimistic. IQR overlap is intersection divided by union of the two middle-50% ranges. ² Small diagnostic Logistic Regression models were fitted on Train with family-versus-matched-normal cohort selection and evaluated on Validation. The family identity selected rows only, never entered X. They are not production models or a fair replacement for the general detector. AUC below 0.5 is reported without flipping the learned score.

The generator uses the same pattern constructor for a suspicious family and its hard counterpart, with overlapping coordination supports. That creates intended behavioural ambiguity. It also produces measurable nuisance differences. For example, N3 Validation events are all wallet-to-wallet transfers (150/150), while H6 contains 687/825 transfers and 138/825 cash events. N3 has 125/150 direct-wallet events versus H6 481/825. Episode-length and channel differences are potential generator artefacts; they are not evidence of illicit behaviour. Exact channel/type mixes and feature overlaps for all eight H1–H8 mappings are in `stage7_hard_negative_overlap.json`. H1 and H7 false-positive rates for the frozen Stage 5 model remain 0.4303 and 0.3321, respectively.

| Hard normal | Resembles | Causal comparison and frozen representation |
|---|---|---|
| H1 | S1/S3 | Prior wallet count and value can show both legitimate and suspicious bursts; 1h and same-day features exist. Coordinated continuation needs later events. |
| H2 | S2 | Repetition is available after prior amounts accumulate; repeated-amount ratio and dispersion exist, but ordinary recurring payments share them. |
| H3 | S4 | Prior near-threshold share exists; normal high payments overlap. The frozen threshold-history ratio is present, but episode persistence needs time. |
| H4 | N1 | Prior receiver source count exists and is represented at 7d; current-edge collection breadth and source turnover are incomplete. Legitimate merchants share collection patterns. |
| H5 | N2/N4 | Outbound counterparty count and 24h pass-through ratio exist; the first funding leg cannot show later outflow. Legitimate payroll and settlement transit overlap. |
| H6 | N3 | Prior reciprocity ratio exists, but current-edge path closure is absent. Refund and settlement cycles overlap; channel/type mix also differs by construction. |
| H7 | A1/A3 | Prior agent count, distinct wallets, novelty and burst z-score exist; busy legitimate service shares them. Change relative to preceding population is incomplete. |
| H8 | A2/A4 | Prior HHI and float value ratio exist; short count concentration and cash count direction are absent from baseline. Ordinary concentrated customers and cash demand overlap. |

## Agent baseline comparisons

| Suspicious family | Matched normal | Prior-hour count median (S/N) | Recent unique wallets median (S/N) | New-wallet share median (S/N) | Strongest of measured prior quantities AUC¹ |
|---|---|---:|---:|---:|---:|
| agent_wallet_growth | H7 | 0.0/1.0 | 30.0/23.0 | 0.92/0.94 | 0.684 (prior_hour_count) |
| agent_wallet_concentration | H8 | 0.0/0.0 | 23.0/24.0 | 0.88/0.94 | 0.663 (new_wallet_share) |
| agent_temporal_burst | H7 | 6.0/1.0 | 34.0/23.0 | 0.91/0.94 | 0.718 (prior_hour_count) |
| agent_flow_imbalance | H8 | 0.0/0.0 | 30.0/24.0 | 0.90/0.94 | 0.652 (recent_unique_wallets) |

These quantities were calculated strictly before each event from that agent’s Validation-partition transactions, with recent seven-day and preceding seven-day windows. The 24-hour concentration and seven-day cash-count imbalance distributions are in the machine output. In A1, median prior new-wallet share is 0.92 versus 0.94 for H7; novelty alone does not separate them. A2’s median top-wallet share is 0.11 versus H8’s 0.15. A3 has stronger prior-hour intensity (6 versus 1), while A4 cash-count imbalance has only modest separation.

## Completed episode diagnostic — NON-DEPLOYABLE

Completed-episode statistics use future transactions. The table shows the strongest descriptive statistic AUC for each matched pair, alongside the strongest frozen feature at the first episode event. It is a descriptive comparison with different units and Validation-based maxima, **not** an estimate of achievable causal classifier performance.

| Suspicious family | First-event best frozen AUC¹ | Completed-episode best AUC¹ | Statistic |
|---|---:|---:|---|
| variable_fragment_burst | 0.613 | 0.950 | transfer_count |
| similar_amount_repetition | 0.637 | 0.821 | transfer_count |
| distributed_same_day_fragmentation | 0.677 | 0.857 | transfer_count |
| variable_near_threshold_history | 0.642 | 0.911 | transfer_count |
| many_to_one_collection | 0.694 | 0.819 | transfer_count |
| one_to_many_dispersion | 0.679 | 0.827 | transfer_count |
| reciprocal_relationship_cycle | 0.903 | 0.941 | unique_serviced_wallets |
| wallet_pass_through | 0.632 | 0.837 | unique_serviced_wallets |
| agent_wallet_growth | 0.671 | 0.699 | unique_senders |
| agent_wallet_concentration | 0.674 | 0.687 | transfer_count |
| agent_temporal_burst | 0.687 | 0.748 | duration_hours |
| agent_flow_imbalance | 0.624 | 0.644 | cash_count_imbalance |

For N3, the strongest completed-episode separator is **unique serviced-wallet count** (Validation median 1 suspicious versus 4 H6), not a cycle statistic. This is a generator construction difference. The same direction appears on Train (median 2 versus 4; AUC 0.787 versus Validation 0.941). Episode-length separation is much stronger on Validation (AUC 0.844; medians 7.5 versus 14) than Train (AUC 0.560; medians 13.5 versus 15). This variation cautions against treating a Validation-only descriptor as a stable behavioural law. Completed-episode comparisons for both Train and Validation are in `stage7_completed_episode_diagnostic.json`. Such hindsight separation must not be interpreted as a valid real-time signal or as proof that changing early labels would improve a legitimate detector.

## Dataset design assessment and decision

The Stage 2 truth assigns target 1 to every planned suspicious episode event, including entry/funding edges and first interactions before an episode motif can exist. This is a demonstrable decision-point mismatch for N3 cycle closure and N4 inbound transfers if the intended decision is a causal transaction alert for the defining behaviour. It is not proof those events are harmless; other independent prior context might support suspicion. H1/H7 overlap and the generator’s shared pattern constructors also create legitimate ambiguity. The N3/H6 channel and episode-size differences show a separate generator artefact; apparent separability may reflect construction rather than behaviour. The 30 features are limited, but Stage 6 additions did not improve Macro F1, and the current evidence does not isolate feature insufficiency as the sole ceiling.

**One next research action:** write a pre-registered, decision-point-aware dataset and ground-truth redesign proposal. Define when an individual transaction can be labelled from information available at its decision time, and when a wallet/agent or sequence alert is the proper analytical unit. Specify independent generator checks for channel and episode-size artefacts. Preserve this V2 dataset and all baselines as the comparison; implement no redesign in Stage 7.

Before/after SHA-256 checks passed for 347 V1/application files and 37 V2 development raw-data, frozen-feature, Stage 5, and Stage 6 files. The final runner does not read holdout files. **Protection deviation:** during preliminary Stage 7 runs, the initial hash check read Final Test and Independent Evaluation file bytes. It did not parse or analyse holdout rows, labels, features, or distributions, and no holdout data entered any model or diagnostic. This violated the explicit no-access instruction; the holdout seal cannot be claimed as unbroken for this stage. The hash check was restricted to development files before the final run.

V2 STAGE 7 COMPLETE — WAITING FOR APPROVAL.
