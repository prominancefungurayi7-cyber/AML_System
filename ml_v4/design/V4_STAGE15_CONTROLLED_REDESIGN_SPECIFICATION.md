# MODEL V4 — STAGE 15 CONTROLLED DATASET, TARGET AND EVALUATION REDESIGN SPECIFICATION


## 1. Executive decision

**A — V4 DESIGN APPROVED FOR GENERATION.**

This is the technical design recommendation, **waiting for user approval**. It does not authorize generation in Stage 15. Implementation tests and a separately authorized next stage remain mandatory.

The proposed experiment is `mobile_money_aml_synthetic_100k_v4`: **100,000 scored transactions**, **24,000 additional warm-up events**, **12 causal predicates**, and **40 semantic feature fields**. All three domains are retained. Growth remains an explicit A1 component, with target and feature eligibility aligned at **35 days**. Fresh Final Test and Independent Evaluation are required.

Design validation checks document consistency and preservation only. No transactions, labels, feature vectors, models, predictions, empirical prevalence or holdout data were created. Population adequacy and improved performance are unmeasured.


## 2. Why a new experiment is justified

[V3 Stage 14](../../ml_v3/reports/V3_STAGE14_AGENT_GROWTH_ROOT_CAUSE_REPORT.md) found that A1 accounted for 1,634 of 1,666 lost Validation detections after growth removal. Eligible growth separated A1 from relevant target 0 negatives with ROC-AUC 0.9939 and AP 0.9898. Four model families concentrated on growth. These are selected synthetic development findings, not measurements of real operator effectiveness.

Growth is a legitimate causal behavioural descriptor. The problem includes compound-target alignment, a narrow conditional negative tail, population construction and an evaluator/contract discrepancy. Frozen A1 used 28d coverage while corrected growth used 35d, leaving 436 Train and 97 Validation A1 positives without growth. Missingness was secondary.

V4 keeps three separate audit questions: **predicate correctness** (does code implement the declared causal rule?), **population adequacy** (do plausible synthetic histories and boundary cases have support?), and **learning difficulty** (what can the fitted representation learn?). High accuracy alone is not a failure. Neither a correct predicate nor a valid feature is weakened just to lower accuracy.


## 3. Preservation of V1, V2 and V3

V1/V2/V3 remain historical experiments. The 702-file allowlist extends the verified Stage 14 protection scope with Stage 14 reports, source, tests and isolated diagnostic artifacts. Before/after SHA-256 checks are recorded in `v4_stage15_protection.json`. This scope includes earlier application artifacts and named public commitment metadata. It is not a claim to inventory every file on disk.

No V3 evaluation tree was enumerated, opened or hashed. The two named public commitment files retain SHA-256 `efc14471b98103a3ad547d93fc56833d014389efd9d3c6e5be6ba896c70d9d58`; this verifies metadata only, not unread evaluation contents. V3 labels, matrices, predicates, source, saved models and reports are preserved. V3 holdouts are not compatible by default with the new V4 semantics.

New repository artifacts are confined to `ml_v4/design/`. There is no application integration or V1 replacement.


## 4. Research task and target meaning

The task is supervised prediction of an **observable suspicious-pattern review target** in a generic synthetic Zimbabwean mobile-money setting. Review is for a human decision-support workflow. Domains are structuring, network and agent behaviour. No private intent, campaign identity or archetype can create a label.

`y(T) = 1` exactly when at least one eligible family predicate is true at decision time; otherwise 0. Cold-start ineligibility is retained in diagnostic metadata, so 0 does not certify benign behaviour. Campaign pre-onset events are 0 only when no other observable predicate fires. Identical permitted history and current fields must produce identical labels regardless of provenance.

All monetary cutoffs are **synthetic analytical thresholds**. In particular, S4's USD 10,000 reference is not presented as Zimbabwean law. No claim of criminal intent, proven laundering, production effectiveness or regulatory certification follows from this benchmark.


## 5. Canonical temporal contract

| Property | Specification |
| --- | --- |
| ordering | key=(UTC timestamp at integer microsecond precision, integer transaction_id); process increasing key; require unique IDs. |
| prior | Only key(e)<key(T). Same-time smaller IDs are prior; same-time larger IDs are future. Emit all targets/features before state update. |
| recent | R_L(H,T)={e in prior H: t-L<time(e)<=t}, plus T once only for the current role listed by each predicate/feature. |
| baseline | B_L(H,T)={e in prior H: t-L-28d<time(e)<=t-L}. Excludes current and all recent events. |
| day exception | UTC calendar S3: recent [d,t] restricted by prior keys plus current; baseline [d-28d,d), d=UTC midnight. Its28 daily bins are [d-k*1day,d-(k-1)*1day), k=1..28. This half-open calendar exception is explicit. |
| wallet subject | Current sender for W2W; serviced_wallet for cash. Structuring activity contains prior W2W sent by subject and prior Cash-In/Cash-Out of subject, once per event. Incoming W2W establishes wallet observation age and inflow history, but is not structuring activity. |
| agent subject | Named current agent; each Cash-In/Cash-Out or assisted W2W contributes one service using explicit serviced_wallet, including receiver-serviced W2W. |
| maximum required history days | 35 |
| history retention | Keep last 35d event state plus first-observed timestamp. Calendar S3 never needs more than 29d before current. Full raw ledger retained separately. |
| numeric | Amounts, sums, counts and predicate comparisons use integers/rationals; no floating-point threshold tolerance. Features may use float64 after exact aggregation. Median includes empty buckets; even median averages the two central values. Floors explicitly defined per formula. |


## 6. Coverage, support and cold start

Eligibility requires first prior observed wallet participation or agent service <= baseline lower boundary, plus family-specific baseline counts. Private activation is never coverage. First observation exactly at lower boundary establishes observation age but is excluded from an open-lower baseline count.

Baseline-ineligible family evaluates false, with eligible=false and reason recorded in diagnostics. Other eligible families may still make y=1. Recent-only descriptors remain valid; baseline-dependent descriptors emit their declared marker.

Full maximum history is 35d; the 42d warm-up permits but does not guarantee eligibility. At a baseline lower boundary, first observation can establish age while its event is excluded from an open-lower baseline count. Recent count features remain defined before eligibility; baseline-relative fields use their own missing markers. Coverage is observed time, not private entity age. Signed valid values must never be mistaken for markers.

An implementation must derive eligibility from the actual first-observation timestamp and baseline support, not from a rounded or capped displayed coverage field.


## 7. Exact twelve target predicates

### S1 — VariableFragmentBurst


| Property | Specification |
| --- | --- |
| entity | wallet subject |
| recent window | 1h |
| baseline window | B_1h |
| coverage | 28d+1h |
| minimum baseline events | 4 |
| minimum baseline distinct | No additional minimum |
| current inclusion | Current subject activity once |
| notes | Variable amounts and dispersed value within a short burst. Explicit denominator floor 1; no dependence on private episode membership. |

All conditions below are joined by **AND**, in addition to the stated role, coverage and baseline support:

- n(R)>=4
- distinct amount values in R >=2
- sum_minor(R)>=30000
- max_minor(R)/sum_minor(R)<=0.60
- n(R)/max(1,n(B)/672)>=3

### S2 — SimilarAmountRepetition


| Property | Specification |
| --- | --- |
| entity | wallet subject |
| recent window | 7d |
| baseline window | B_7d |
| coverage | 35d |
| minimum baseline events | 4 |
| minimum baseline distinct | No additional minimum |
| current inclusion | Current subject activity once |
| notes | Baseline support is all subject activity, not a requirement for four baseline similar events. No future cluster center or learned amount band. |

All conditions below are joined by **AND**, in addition to the stated role, coverage and baseline support:

- C_R={e in R:20*abs(amount(e)-amount(T))<=amount(T)}; C_B uses same current-centered test in B
- n(C_R)>=4
- sum_minor(C_R)>=20000
- n(C_R)/n(R)>=0.60
- n(C_R)/max(1,n(C_B)/4)>=2

### S3 — DistributedSameDayFragmentation


| Property | Specification |
| --- | --- |
| entity | wallet subject |
| recent window | UTC [d,t] |
| baseline window | [d-28d,d) |
| coverage | first observation <=d-28d |
| minimum baseline events | 4 |
| minimum baseline distinct | No additional minimum |
| current inclusion | Current subject activity once |
| notes | Calendar exception is shared by evaluator/extractor; no full current-day future total. |

All conditions below are joined by **AND**, in addition to the stated role, coverage and baseline support:

- n(R)>=6
- number of occupied UTC hour buckets in R >=3
- sum_minor(R)>=50000
- n(R)/max(1,median(28 preceding calendar-day activity counts, including zeros))>=2

### S4 — VariableNearThresholdHistory


| Property | Specification |
| --- | --- |
| entity | wallet subject |
| recent window | 7d |
| baseline window | B_7d |
| coverage | 35d |
| minimum baseline events | 4 |
| minimum baseline distinct | No additional minimum |
| current inclusion | Current subject activity once |
| notes | SYNTHETIC ANALYTICAL THRESHOLD USD 10000; band USD 7000..10500. High-value repetition may be legitimate; no legal claim. |

All conditions below are joined by **AND**, in addition to the stated role, coverage and baseline support:

- band(e)=700000<=amount_minor(e)<=1050000; band(T) true
- n(R)>=5
- n(band rows in R)>=3
- distinct band amount values in R >=2
- n(band rows in R)/n(R)>=0.40
- n(band rows in R)/max(1,n(band rows in B)/4)>=2

### N1 — ManyToOneCollection


| Property | Specification |
| --- | --- |
| entity | current W2W receiver |
| recent window | 24h |
| baseline window | B_24h |
| coverage | 29d |
| minimum baseline events | 4 |
| minimum baseline distinct | No additional minimum |
| current inclusion | Current W2W edge once; non-W2W inapplicable |
| notes | Coverage is first observed participation of endpoint; baseline count is relevant directed W2W edges only; cash excluded. |

All conditions below are joined by **AND**, in addition to the stated role, coverage and baseline support:

- current type is W2W
- n(R incoming W2W edges)>=4
- distinct opposite endpoints in R >=3
- sum_minor(R)>=30000
- n(R)/max(1,n(B)/28)>=2

### N2 — OneToManyDispersion


| Property | Specification |
| --- | --- |
| entity | current W2W sender |
| recent window | 24h |
| baseline window | B_24h |
| coverage | 29d |
| minimum baseline events | 4 |
| minimum baseline distinct | No additional minimum |
| current inclusion | Current W2W edge once; non-W2W inapplicable |
| notes | Coverage is first observed participation of endpoint; baseline count is relevant directed W2W edges only; cash excluded. |

All conditions below are joined by **AND**, in addition to the stated role, coverage and baseline support:

- current type is W2W
- n(R outgoing W2W edges)>=4
- distinct opposite endpoints in R >=3
- sum_minor(R)>=30000
- n(R)/max(1,n(B)/28)>=2

### N3 — ReciprocalRelationshipCycle


| Property | Specification |
| --- | --- |
| entity | current W2W endpoints |
| recent window | prior 7d |
| baseline window | none |
| coverage | none |
| minimum baseline events | 0 |
| minimum baseline distinct | No additional minimum |
| current inclusion | Current closes path; excluded from prior path |
| notes | Any qualifying path is sufficient. No shortest-path restriction in target; no search truncation. A 1-edge path has a vacuous adjacent-edge condition. Cycle length including current is 2..6. |

All conditions below are joined by **AND**, in addition to the stated role, coverage and baseline support:

- current W2W sender s != receiver r
- exists a simple directed prior path r -> ... -> s of 1..5 edges with no repeated vertices
- every edge has t-7d<time<=t and strictly increasing keys, last key<key(T)
- for each adjacent prior edge pair: 1/4<=amount(next)/amount(previous)<=4
- 1/4<=amount(T)/amount(first path edge)<=5/4

### N4 — WalletPassThrough


| Property | Specification |
| --- | --- |
| entity | current W2W sender or cash-out wallet |
| recent window | prior 24h then anchor..current |
| baseline window | none |
| coverage | none |
| minimum baseline events | 0 |
| minimum baseline distinct | No additional minimum |
| current inclusion | Current outward amount once |
| notes | Anchor and all funding/outward events are bounded by the same 24h horizon. Cash-In alone cannot establish anchor. No prediction of subsequent exit. |

All conditions below are joined by **AND**, in addition to the stated role, coverage and baseline support:

- current type W2W or Cash-Out
- anchor is smallest-key prior incoming W2W edge within (t-24h,t]
- F=sum prior incoming W2W and Cash-In amounts with anchor.key<=key<key(T); each event once
- O_prior=sum prior outgoing W2W and Cash-Out amounts with anchor.key<key<key(T); O=O_prior+amount(T)
- F>=10000
- 1/2<=O/F<=1
- amount(T)<=F-O_prior

### A1 — AgentWalletGrowth


| Property | Specification |
| --- | --- |
| entity | current agent |
| recent window | 7d |
| baseline window | B_7d; four separate preceding 7d buckets |
| coverage | 35d |
| minimum baseline events | 12 |
| minimum baseline distinct | No additional minimum |
| current inclusion | Current service once; amount unused |
| notes | Retains meaningful compound A1; aligns 35d eligibility and boundaries. New means absent in preceding baseline, not private activation or globally new wallet. No added gate solely to lower accuracy. |

All conditions below are joined by **AND**, in addition to the stated role, coverage and baseline support:

- D=distinct serviced wallets in R; U=wallets(R) minus wallets(B); M=median(distinct counts of four baseline weeks, including zeros)
- D>=6
- size(U)>=4
- size(U)/D>=1/2
- D/max(1,M)>=3/2

### A2 — AgentWalletConcentration


| Property | Specification |
| --- | --- |
| entity | current agent |
| recent window | 24h |
| baseline window | B_24h |
| coverage | 29d |
| minimum baseline events | 20 |
| minimum baseline distinct | 5 |
| current inclusion | Current service once |
| notes | top2 selects its own two largest serviced-wallet event counts independently in each window, divided by that window count. Different baseline wallets allowed; all service types count. |

All conditions below are joined by **AND**, in addition to the stated role, coverage and baseline support:

- n(R)>=8
- top2(R)>=13/20
- top2(R)-top2(B)>=1/5

### A3 — AgentTemporalBurst


| Property | Specification |
| --- | --- |
| entity | current agent |
| recent window | 1h |
| baseline window | B_1h |
| coverage | 28d+1h |
| minimum baseline events | 12 |
| minimum baseline distinct | No additional minimum |
| current inclusion | Current service once |
| notes | Baseline offset is exactly 1h, not the 7d-offset A1 baseline. Counts all service types. |

All conditions below are joined by **AND**, in addition to the stated role, coverage and baseline support:

- n(R)>=5
- distinct serviced wallets in R >=3
- n(R)/max(1,n(B)/672)>=3

### A4 — AgentFlowImbalance


| Property | Specification |
| --- | --- |
| entity | current agent |
| recent window | 24h |
| baseline window | B_24h |
| coverage | 29d |
| minimum baseline events | 12 services including >=8 cash events |
| minimum baseline distinct | No additional minimum |
| current inclusion | Current Cash-In/Cash-Out once; current W2W inapplicable |
| notes | Empty cash skew is 0. W2W never enters cash sums/counts or float. Baseline services and cash both use the same preceding disjoint 28d. |

All conditions below are joined by **AND**, in addition to the stated role, coverage and baseline support:

- current is Cash-In or Cash-Out
- recent cash count>=6
- distinct recent cash-serviced wallets>=3
- v=(cashout_value-cashin_value)/(cashout_value+cashin_value); c=(cashout_count-cashin_count)/(cashout_count+cashin_count)
- abs(v)>=3/5
- abs(c)>=1/2
- v*c>0
- abs(v-v_baseline)>=2/5

All families receive canonical endpoints/full prior keys and explicit denominator floors. A1/S2/S4 use35d, N1/N2/A2/A4 use29d, S1/A3 use28d+1h. A2/A4 replace frozen27d baseline; A3 replaces frozen7d-offset baseline. These are V4 definitions, not corrections to V3 bytes.


## 8. Target–feature history alignment

| Family | Target recent | Target baseline | Coverage | Minimum baseline events / distinct | Current inclusion | Feature fields |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | 1h | B_1h | 28d+1h | 4 / None | Current subject activity once | amount_minor, wallet_count_1h, wallet_value_1h, wallet_max_value_share_1h, wallet_activity_acceleration_1h, wallet_observed_coverage_days |
| S2 | 7d | B_7d | 35d | 4 / None | Current subject activity once | amount_minor, wallet_similar_amount_count_7d, wallet_similar_amount_share_7d, wallet_observed_coverage_days |
| S3 | UTC [d,t] | [d-28d,d) | first observation <=d-28d | 4 / None | Current subject activity once | amount_minor, wallet_count_utc_day, wallet_active_hours_utc_day, wallet_day_count_growth, wallet_observed_coverage_days |
| S4 | 7d | B_7d | 35d | 4 / None | Current subject activity once | amount_minor, wallet_near_band_count_7d, wallet_observed_coverage_days |
| N1 | 24h | B_24h | 29d | 4 / None | Current W2W edge once; non-W2W inapplicable | amount_minor, transaction_type, network_in_count_24h, network_in_distinct_24h, network_in_acceleration_24h |
| N2 | 24h | B_24h | 29d | 4 / None | Current W2W edge once; non-W2W inapplicable | amount_minor, transaction_type, network_out_count_24h, network_out_distinct_24h, network_out_acceleration_24h, wallet_observed_coverage_days |
| N3 | prior 7d | none | none | 0 / None | Current closes path; excluded from prior path | amount_minor, transaction_type, prior_return_path_min_length_7d, prior_return_path_count_7d, prior_path_min_max_log_change_7d, current_to_selected_path_first_value_ratio |
| N4 | prior 24h then anchor..current | none | none | 0 / None | Current outward amount once | amount_minor, transaction_type, wallet_pass_through_fraction_24h, wallet_prior_funding_residual_minor_24h |
| A1 | 7d | B_7d; four separate preceding 7d buckets | 35d | 12 / None | Current service once; amount unused | agent_wallet_growth_ratio_7d, agent_distinct_wallets_7d, agent_new_wallet_count_7d, agent_new_wallet_share_7d, agent_observed_coverage_days |
| A2 | 24h | B_24h | 29d | 20 / 5 | Current service once | agent_top2_count_share_24h, agent_top2_share_change_24h, agent_observed_coverage_days |
| A3 | 1h | B_1h | 28d+1h | 12 / None | Current service once | agent_service_acceleration_1h, agent_distinct_wallets_1h, agent_observed_coverage_days |
| A4 | 24h | B_24h | 29d | 12 services including >=8 cash events / None | Current Cash-In/Cash-Out once; current W2W inapplicable | amount_minor, transaction_type, agent_cash_in_count_24h, agent_cash_out_count_24h, agent_cash_in_value_24h, agent_cash_out_value_24h, agent_cash_distinct_wallets_24h, agent_cash_value_skew_change, agent_observed_coverage_days |


The table and `v4_target_feature_alignment.json` are normative together with each feature record in section23. Baseline-derived features use exactly the related predicate's historical eligibility; recent-only counts intentionally require less history. N3/N4 require no long baseline. General coverage scalars impose no additional gate. S3's calendar exception is deliberate. No target silently demands an unavailable longer-history component.


## 9. A1 redesign and growth policy

A1 remains the compound condition `eligible AND D>=6 AND U>=4 AND U/D>=0.5 AND D/max(1,M)>=1.5`. `D` is recent7d distinct serviced wallets, `U` is the subset absent from the preceding28d baseline union, and `M` is the median of four separate baseline weekly distinct counts. Both target and growth/newness descriptors require 35d of observed service history and at least 12 baseline services.

The model receives growth, recent distinct count, new distinct count and new share as separate lower-level quantities. Each is an explicitly disclosed direct target component. It receives no A1 trigger or full conjunction. The new counts supply breadth and acquisition context for failed-gate diagnosis; they are not alternative transforms introduced to reduce importance concentration. A model may learn the rule accurately, which is acceptable.

The exact A1 behavioural condition is retained rather than adding an arbitrary persistence gate to suppress strong scores. Temporary and sustained growth have no privileged labels. If expansion satisfies every condition, it remains a review positive. The scientific remedy is an explicit population model and adequately supported combinations of components, followed by audit.


## 10. Legitimate-like customer growth

At each 7d boundary each catchment member survives with independently drawn per-agent retention U(0.80,0.98). Replace leavers without replacement from other local wallets to maintain20 regular slots. Keep actual transaction history; membership replacement does not reset observable novelty.

For growing agents, 2 acquisition intervals of duration U(14,42)d begin uniformly within the scored180d horizon subject to fitting; repeat probability decreases by U(0.05,0.15), with probability floor0.1. Activity multiplier ramps linearly1 to U(1.1,1.8). After interval, retain resulting catchment and smoothly return demand over 7d. No label inspection.
| Synthetic cause | Duration/period days | Activity multiplier | Customer mechanism |
| --- | --- | --- | --- |
| newly popular location / promotion / adoption | [7, 28] | [1.1, 2.2] | mixture of returning and nonregular local wallets |
| payday / market day | [1, 3] | [1.1, 2.0] | mostly existing regular customers |
| seasonality | [21, 45] | [0.6, 1.6] | unchanged catchment; random phase |
| nearby-agent outage / customer migration | [1, 7] | [1.1, 2.0] | shift demand from another agent in same unit; total unit demand conserved |
| ordinary expansion / recovery after low activity | [7, 28] | [0.6, 1.8] | returning and acquired customers; no future recovery in current label |

Every archetype can receive each shock. Propose2 shocks per agent per scored horizon, cause uniformly from the 5 groups, continuous start time uniform over fitting interval. Seasonal archetypes additionally receive the sinusoid with amplitude U(0.1,0.4) and phase U(0,2pi); volatile archetypes receive2 additional shocks. Multiply overlapping factors then cap total activity multiplier to[0.25,3]. These caps are generator assumptions, not feature clipping.

These are synthetic behavioural assumptions. No external operator distribution is asserted. Growth opportunities also occur in ordinary background activity. Target 0 overlap is examined separately from all-origin populations because universal predicate labeling conditions the negative tail.


## 11. Near-boundary negatives without contradictory labels

| A1 case | Recent distinct D | Baseline weekly median M | New distinct U | Meaningful failed condition |
| --- | --- | --- | --- | --- |
| Strong growth, returning customers | 12 | 6 | 3 | new_distinct<4 and novelty=0.25<0.5 |
| High novelty, modest growth | 10 | 8 | 7 | growth=1.25<1.5 |
| Temporary market-day expansion | 12 | 6 | 4 | novelty=1/3<0.5; future return to baseline is irrelevant |
| Sustained legitimate-like expansion | 18 | 9 | 7 | novelty=7/18<0.5; sustained expansion may instead become target 1 if all gates pass |
| Busy repeat use without acquisition | 8 | 6 | 2 | growth<1.5, new_distinct<4 and novelty<0.5; event count alone is insufficient |
| Naturally expanding customer population | 14 | 10 | 8 | growth=1.4<1.5 |
| Near novelty boundary | 10 | 6 | 4 | novelty=0.4<0.5; changing one old wallet to a baseline-new wallet reaches0.5 |

These are mathematical design examples, not generated rows, measured prevalence or fixed signatures. Eligible history and >=12 baseline services are assumed. Draw broad overlapping recipe parameters; do not copy exact example tuples across episodes.

A named failed gate rules out only its family. A true target 0 case must have every family false under the common evaluator. Hard-origin rows satisfying any full predicate must be target 1; never delete, relabel or regenerate them to preserve a negative quota.

An agent's later recovery cannot be used to justify a current negative. A legitimate business explanation not visible in the permitted fields also cannot override the label. In a future task that distinguishes additional legitimate context, that context and target would need a new explicit contract.


## 12. Positive diversity and H1–H8

- Gradual acquisition: D12, baseline median8, U6 illustrates equality at growth1.5 and novelty0.5.
- Sharp acquisition: D12, baseline median5, U8 illustrates stronger growth and novelty.
- Moderate growth with novelty: D8, baseline median5, U5 illustrates ratio1.6 and novelty0.625.
- Sustained acquisition after a stable baseline: D18, median10, U10 illustrates growth1.8 and novelty0.556.


| Code | Concept | Related families | Population mechanism | Failed condition required for named-family negative |
| --- | --- | --- | --- | --- |
| H1 | Busy wallet / same-day activity | S1,S3 | High counts with one dominant payment, or activity concentrated in fewer than 3 hour buckets, or established comparable daily baseline. | S1 max share>0.60 or acceleration<3; S3 occupied hours<3 or day growth<2. |
| H2 | Recurring payments | S2 | Similar amounts across prior and recent periods; or mixed current payments diluting the similar cluster. | S2 cluster share<0.60 or cluster growth<2; do not lower label because recurring origin is legitimate. |
| H3 | Recurring legitimate large payments | S4 | Large repeated transfers on a stable schedule; high-value band occurs in all origins. | S4 band share<0.40, fewer than 3 recent band events, or band growth<2; exact-same band values also fail required variation. |
| H4 | Legitimate collection | N1 | Several payers with stable prior incoming volume, or many recent transfers from only 2 payers. | N1 incoming growth<2 or distinct senders<3. |
| H5 | Payroll / transit-like dispersion | N2,N4 | Recurring dispersion with strong prior baseline; alternatively outward transfers use only a small fraction of recent funding. | N2 outgoing growth<2; N4 O/F<0.5 (or no incoming-W2W anchor). Must check both and all other families for target 0. |
| H6 | Refund / settlement / reciprocal-looking activity | N3 | Reverse edges and chains exist but chronological order, amount consistency or current return proportion fails. | No full qualifying chronological simple path, or every such path fails an amount ratio. Presence of a topological path alone is not N3. |
| H7 | Busy / growing agents | A1,A3 | Returning-customer expansion, moderate acquisition, market-day demand, customer migration and low-period recovery. | A1 new count<4, novelty<0.5, recent distinct<6 or growth<1.5; A3 hourly growth<3 or recent distinct<3. Later recovery is not a gate. |
| H8 | Concentrated customer / cash demand | A2,A4 | Repeat clientele with stable concentration; cash direction aligned with prior season or with weak count/value agreement. | A2 share change<0.2 or top2 share<0.65; A4 abs skew change<0.4, abs count skew<0.5, abs value skew<0.6 or sign disagreement. |


H1–H8 are **hard-origin mechanisms**, not fixed ground-truth classes. Keep their target 1 rows in results and their target 0 rows in FPR denominators. Match their amount precision, role/channel rules, activity support and scheduling laws to corresponding positive-intended opportunities. H7 must test returning-customer growth and acquisition separately; H8 must distinguish stable concentration or cash demand from a new imbalance.


## 13. N3 representation review

P=all topology-valid simple chronological prior return paths of 1..5 edges in7d; select p* by smallest prior maximum absolute adjacent log amount ratio, then shortest length, then lexicographic full edge-key sequence; current amount never influences selection

The target searches all chronological simple return paths of 1..5 prior edges for the full amount conjunction. Model features expose topology-only path count/minimum length and a selected path's prior amount spread/current-to-first ratio. Selection considers prior spread continuously, never the current return ratio or the complete predicate. No feature counts fully qualifying paths or returns an N3 flag.

This improves access to alternatives beyond the old shortest path, but remains lossy: another path can satisfy the current return ratio when the minimum-spread path does not. A count does not show every route's amounts. This limitation is disclosed before fitting. All-path enumeration must pass bounded performance tests; no silent path truncation is allowed. Failure triggers implementation review, not a changed target or post-result feature search.


## 14. A4 cash-flow representation review

Six recent primitives describe Cash-In count, Cash-Out count, Cash-In value, Cash-Out value, distinct cash-serviced wallets and historical value-skew change. Counts and values allow the learner to express signed count/value imbalance and magnitude without receiving the full A4 conjunction. Current type supplies cash-role context; the complete target additionally checks eligibility, recent activity/breadth, signs and thresholds.

Cash observations use the same24h recent and disjoint preceding28d baseline in evaluator and extractor; full29d observation and 12 services including 8 cash events are required for baseline skew change. Empty cash skew is 0, valid zero differs from missing-3. Assisted W2W affects service histories but neither cash totals nor cash float.


## 15. Structuring support and representation limits

All four structuring concepts remain. S2 compares recent similar-amount repetition with actual prior activity; S4 retains an explicitly synthetic high-value band. Neither is dropped because V3 Validation had only 1/8 positives. Their opportunity weights are increased before targets are observed, and support is measured from actual predicate-positive decision points.

The 40-field representation is deliberately compact. It omits S1 distinct amount count, S2 cluster value/baseline cluster rate, S3 day value and some S4 share/variation/rate components. N1/N2 aggregate value and some absolute agent service counts are also absent. These are declared information losses, not claims of sufficient representation. A later pretraining review must inspect availability and separability; any feature amendment is versioned before model search. Increasing dimensions after seeing holdout results is prohibited.


## 16. Agent population

| Archetype | Activity median | Repeat probability center | Mechanism |
| --- | --- | --- | --- |
| low_volume_stable | 0.65 | 0.8 | Stationary customer demand with day-to-day noise |
| medium_volume_stable | 1.0 | 0.75 | Stable activity with returning and occasional customers |
| high_volume_urban_like | 1.65 | 0.65 | Higher service opportunity, not a geographic claim |
| growing_legitimate | 1.0 | 0.65 | Gradual customer acquisition and reactivation; growth can satisfy review predicates |
| seasonal | 1.0 | 0.7 | Cyclic demand with random phase |
| concentrated_repeat_customer | 1.0 | 0.85 | More repeat use; no automatic negative label |
| broad_customer_base | 1.2 | 0.55 | Broader overlapping catchment |
| volatile_legitimate | 1.0 | 0.7 | Short demand shocks of either sign; no automatic negative label |


| Property | Specification |
| --- | --- |
| assumption status | Synthetic assumptions, not empirically calibrated Zimbabwe operator statistics. |
| overlapping distributions | For every archetype draw activity weight lognormal(log(median),0.6), truncated to[0.2,4]. Draw repeat probability uniformly within center +/-0.15, clipped to[0.1,0.95]. Thus distributions overlap and no latent identity implies target. |
| local unit | 100 wallets and 8 agents; each agent has a randomly selected initial regular catchment of 20 wallets, with overlaps allowed. Background regular-customer choice uses repeat probability; remaining choice draws from the other80 local wallets. No partition-global uniform pool. |
| novelty scale control | Exactly the same unit size, per-unit row budget, horizon, catchment rules and activity distributions for Train/Validation/Final. Independent changes composition only as declared; neither pool size nor temporal horizon changes. |
| own history | All newness is evaluated from actual agent service history, never private membership lists. Same observable history produces the same label in every archetype. |
| ordinary growth audit | Retain both target states for every origin, and separately examine legitimate-growth-origin target 0. Verify failed A1 conditions and cross-family positives. No minimum/maximum growth AUC is a generation objective. |


## 17. Wallet population

| Profile | Wallets per 100 | Relative activity median |
| --- | --- | --- |
| low_frequency_personal | 25 | 0.5 |
| regular_transfer | 20 | 1 |
| cash_heavy | 15 | 1 |
| recurring_payment | 15 | 1 |
| high_activity | 10 | 2 |
| collection_like | 8 | 1.5 |
| dispersion_like | 7 | 1.5 |


| Property | Specification |
| --- | --- |
| activity | Profile relative activity drawn lognormal(log(median),0.7), truncated[0.1,5]; all overlap. Normalize within the local unit when assigning a fixed opportunity budget. |
| relationships | Each wallet has an initial set of 5 preferred counterparties sampled without replacement in its unit, excluding itself. For ordinary W2W, choose preferred with probability U(0.5,0.85) per wallet; otherwise from remaining unit wallets. Each 7d boundary retain each preference with probability0.95 and refill to 5. |
| types | Start from background type probabilities; cash-heavy multiplies each cash probability by1.5; regular-transfer multiplies W2W by1.5; other profiles use base weights; normalize. Matched scenario/hard recipes may override roles symmetrically. |
| recurring | Recurring-payment profile proposes intervals of 7 or30days with equal probability and independent timestamp jitter uniform +/-12h; no negative dates, all events retained only within generation horizon. Amount varies by lognormal multiplier log-SD0.08. The same renewal process may appear in every profile with probability0.2. |
| collection dispersion | Collection/dispersion profiles bias direction, not target: endpoint weights are multiplied1.5 for the relevant role. Other profiles can receive identical motifs. |
| cold start | Reserve10 of each 100 wallets, chosen independently of profile, for first observable activity uniformly in scored days0..60. Other90 are eligible for warm-up selection, without guaranteed complete history. Agents all may appear in warm-up but first-observed coverage is checked rather than assumed. |
| forbidden | Profiles, private activation and future schedules never reach evaluator or X. No profile-specific numeric ID range, amount precision, timestamp block or unique channel. |
| interpretation | Profiles describe opportunities; realized review evidence is solely evaluated from observables. |
| activation consistency | Inactive wallets cannot appear in any event or relationship choice before their proposed observable activation opportunity. Renormalize over active candidates, log empty candidate sets as failures; never use private activation to set target eligibility. Private catchment membership alone creates no observation. |


## 18. Transactions, channels, values and accounting

| Property | Specification |
| --- | --- |
| currency | USD synthetic accounting unit, integer cents |
| threshold language | All numeric cutoffs are synthetic analytical assumptions. S4 uses a SYNTHETIC ANALYTICAL THRESHOLD of USD 10000, not a Zimbabwe reporting requirement. |
| observable fields | ["transaction_id", "event_timestamp", "sender_wallet", "receiver_wallet", "amount_minor", "currency", "transaction_type", "channel", "agent_id", "serviced_wallet", "agent_flow_direction"] |
| private diagnostic fields | ["scenario_id", "scenario_family", "campaign_id", "origin", "strength", "archetype", "profile", "population_unit", "activation_schedule", "intended_onset"] |
| transaction rules | {"wallet_to_wallet": "sender != receiver; positive amount; direct_wallet has no agent/serviced wallet, or agent channel has a named agent and serviced_wallet equal to exactly one endpoint; one agent service.", "cash_in": "sender=receiver=serviced_wallet; named agent; agent channel; wallet electronic balance increases, agent electronic float decreases and physical cash increases.", "cash_out": "sender=receiver=serviced_wallet; named agent; agent channel; wallet electronic balance decreases, agent electronic float increases and physical cash decreases.", "assisted_W2W": "Transfers electronic value between wallets; agent service history updates once; neither agent cash nor electronic float changes."} |
| amount process | For background and all recipe origins use a shared mixture: 90% lognormal USD median 35, log-SD 1.0; 10% lognormal median 1800, log-SD 1.0; truncate by rejection to [0.01,15000], round half-up to cents. Recipe-specific amount relations are allowed but use the same rounding, jitter and cents distribution across origins. No origin-specific precision. |
| transaction mix | {"background_type_probabilities": {"wallet_to_wallet": 0.5, "cash_in": 0.25, "cash_out": 0.25}, "assisted_share_of_W2W": 0.35, "serviced_endpoint": "sender/receiver each 0.5; sampled before target evaluation", "recipe_exceptions": "Graph opportunities require W2W; cash opportunities require cash. Apply the same exceptions to matched hard-origin opportunities; audit channel/type associations."} |
| accounting policy | Model a closed synthetic ledger with each wallet opening at USD 1000000 electronic value and each agent at USD 2000000 electronic float and USD 2000000 cash. These deliberately ample fixed inventories are simulator safeguards, not realistic wealth estimates. They are identical across origins and excluded from observables supplied to X and the target. Apply Cash-In/Out/W2W transitions exactly and forbid any negative inventory. No unrecorded top-ups. If a fixed-seed proposed event is infeasible, stop that materialization and report capacity failure; do not resample for target or silently alter amounts. Capacity adequacy must be tested before generation and empirically checked afterward. |


Opening inventories are intentionally ample simulator capacities. They are not realistic wealth/float estimates and do not support liquidity-risk claims. They are excluded from both the target and features, and any capacity failure is visible. The review task remains based on observable transaction behaviour.


## 19. Partition sizes and entity isolation

| Partition | Scored | Warm-up | Wallets | Agents | Local units |
| --- | --- | --- | --- | --- | --- |
| train | 60000 | 14400 | 1200 | 96 | 12 |
| validation | 15000 | 3600 | 300 | 24 | 3 |
| final_test | 15000 | 3600 | 300 | 24 | 3 |
| independent_evaluation | 10000 | 2400 | 200 | 16 | 2 |

Wallets and agents disjoint across partitions; no cross-partition edge, history, warm-up, state or ID collision. Units are isolated communities within a partition; no cross-unit W2W or service. Unit ID is private and excluded from X.

Twice V3 wallet count per agent provides100-wallet local reservoirs; repeated units keep pool size and expected per-entity event exposure constant across partition sizes.12/3/3/2 communities are a controlled synthetic replication design, not a representative regional network.

Later materialization derives independent128-bit opaque wallet/agent IDs from partition entity streams. Transaction IDs are unique random positive63-bit integers drawn without replacement; no family/time/partition block prefixes. IDs are join/order keys, never input features.

Expected event exposure is identical per development/Final unit:5,000 scored events across100 wallets/8 agents over 180d. These are opportunity ratios, not realized per-agent rates. Unit-level dependence and only 3/2 evaluation communities materially limit uncertainty claims. There is no claim that disconnected100-wallet communities reproduce a national transaction graph.


## 20. Temporal horizon and warm-up

| Property | Specification |
| --- | --- |
| warmup days | 42 |
| scored days | 180 |
| start | 2027-01-01T00:00:00Z |
| scored start | 2027-02-12T00:00:00Z |
| scored end exclusive | 2027-08-11T00:00:00Z |


| Property | Specification |
| --- | --- |
| scored | False |
| used for model fit | False |
| can satisfy predicates | True |
| label storage | Optional evaluator diagnostic stream only; warm-up truth excluded from model training and reported scored prevalence. No y forced to 0. |
| storage | Separate warmup_observables file per partition with identical event schema, fed before scored transactions; files hash-manifested and kept permanently. |
| counted in 100000 | False |
| selection | Fixed timestamp interval, never label-based discard; all scored rows kept even if baseline-ineligible. |


The full observable ledger contains124,000 events:100,000 scored plus24,000 warm-up. This overhead is explicit and costs less than enlarging the scored experiment. Warm-up covers42d before the 180d scoring interval; retained raw history is never silently discarded. Warm-up is a time-based history segment, not a label-selected exclusion. A predicate could fire in warm-up, but such labels never supervise or count in scored metrics. Late-appearing wallets remain in the scored population with genuine cold-start diagnostics.


## 21. Prevalence policy

The predeclared broad design envelope is **10%–45%** positive scored rows per partition. It is an enriched research-design range, not operational AML prevalence. With 12 families each targeting300 positive rows in15,000 Validation rows, disjoint families alone would require 24%; overlap and background positives make exact prevalence unpredictable.

There is no class-percentage quota, label override, deletion or accept-until-prevalence loop. One production draw is retained even if it misses this envelope. A miss pauses training for documented scientific review. Any new population version needs authorization and an audit trail, without recycling evaluation information. No prevalence has been measured in Stage 15.


## 22. Family-support policy and failure handling

| Family | Train minimum objective / range | Validation minimum objective / range | Final minimum objective / range | Independent minimum objective / range |
| --- | --- | --- | --- | --- |
| S1 | 1200 / 1200–3600 | 300 / 300–900 | 300 / 300–900 | 200 / 200–600 |
| S2 | 1200 / 1200–3600 | 300 / 300–900 | 300 / 300–900 | 200 / 200–600 |
| S3 | 1200 / 1200–3600 | 300 / 300–900 | 300 / 300–900 | 200 / 200–600 |
| S4 | 1200 / 1200–3600 | 300 / 300–900 | 300 / 300–900 | 200 / 200–600 |
| N1 | 1200 / 1200–3600 | 300 / 300–900 | 300 / 300–900 | 200 / 200–600 |
| N2 | 1200 / 1200–3600 | 300 / 300–900 | 300 / 300–900 | 200 / 200–600 |
| N3 | 1200 / 1200–3600 | 300 / 300–900 | 300 / 300–900 | 200 / 200–600 |
| N4 | 1200 / 1200–3600 | 300 / 300–900 | 300 / 300–900 | 200 / 200–600 |
| A1 | 1200 / 1200–3600 | 300 / 300–900 | 300 / 300–900 | 200 / 200–600 |
| A2 | 1200 / 1200–3600 | 300 / 300–900 | 300 / 300–900 | 200 / 200–600 |
| A3 | 1200 / 1200–3600 | 300 / 300–900 | 300 / 300–900 | 200 / 200–600 |
| A4 | 1200 / 1200–3600 | 300 / 300–900 | 300 / 300–900 | 200 / 200–600 |


| Property | Specification |
| --- | --- |
| count definition | Number of scored decision points with each observable predicate true, not events carrying private scenario family. Family counts overlap; unique positive count is a union. |
| support rationale | Several hundred rows can stabilize raw recall relative to V3 counts1 and 8. An independent-binomial worst-case95% half-width is about 0.057 atN300; event dependence makes this optimistic. No achieved count or precision claim before generation. |
| dependence requirements | Also record distinct subjects, episodes and units per family. Aim >=20 distinct subjects and >=30 distinct episode-or-background-time clusters per Validation/Final family, >=12 subjects and 20 clusters for Independent. Agent family objective is constrained by24/16 agents. Show concentration and cluster uncertainty;300 rows from one agent is not adequate. |
| opportunity budget | {"development_and_final_per_unit": {"background": 2000, "hard_origin": 1000, "family_opportunities": 2000}, "hard_allocation": "H1..H8 weights1 each; largest-remainder rounding with lexical ties; event provenance assigned once.", "family_allocation": "S2,S4,N3 weight2 each, all other families weight1. Allocate2000 event opportunities by largest-remainder rounding in code order; includes preparatory/pre-onset events. This is not target balancing.", "independent_per_unit": {"background": 1750, "hard_origin": 1250, "family_opportunities": 2000}, "warmup_per_unit": "1200 background-only opportunities; labels can still emerge from observable behaviour."} |
| opportunity recipe | Event budgets allocated before targets. Episode sizes are discrete uniform8..20 conditioned only on completing the budget, with any residual<8 assigned to background and reported. Continuous start times uniform over fitting intervals; no forced30d blocks. Same episode-size law for positive-intended and hard origins. Strength U(0.1,0.9), never label input. |
| no retry | One production draw per frozen manifest and seed. No repeat generation until prevalence, support, AUC, overlap or model performance looks preferable. Shortfalls are retained and documented. |
| shortfall resolution | Block training or qualified family-performance claims when development coverage is inadequate. Before any model evaluation, either approve a new version with scientifically justified opportunity changes, or retain the frozen population benchmark and authorize a separately labeled family challenge set with cluster uncertainty. Do not mix challenge-set prevalence into the 100k benchmark. If realistic S4 support is infeasible, report imprecise S4 recall and a separate stress test; do not distort ordinary amounts to claim coverage. |
| holdout support | Later sealed custodian runs fixed support/schema/causality gates and releases only a predeclared pass/fail certificate before model freeze, not detailed rows/counts. Failed seals are quarantined without exposing outcomes to developers; no seed shopping. Any replacement requires versioned authorization and no cross-version benchmark claim. |


### Proposed opportunity mechanisms

| Family | Mechanism; no post-label acceptance |
| --- | --- |
| S1 | 4..12 subject events across5..60min; value dispersion from a common Dirichlet(1,1,...) allocation; total amount sampled from shared value process; both dominant and diffuse payments possible. |
| S2 | 4..12 subject payments over 1..7d; base amount from shared process, multiplicative jitter lognormal log-SD U(0.01,0.15); interleave unrelated payments. Use adequate background activity without searching evaluated target. |
| S3 | 6..16 subject events over 3..20h with independent inter-arrival jitter, across3..8 proposed occupied hours; may cross UTC midnight. Full daily counts remain causal. |
| S4 | 5..12 payments over 1..7d; recipe amounts drawn continuous USD 5000..13000, with common cent rounding; earlier same-profile large-payment history may defeat rate change. No forced positive label. |
| N1 | 4..12 incoming W2W edges,2..8 senders, over 1..24h; use shared amounts and existing relation history. |
| N2 | 4..12 outgoing W2W edges,2..8 receivers, over 1..24h; same relation and value support as H5. |
| N3 | Propose simple walks2..6 vertices and return edges, chronology jitter and independent amounts with multiplicative factors exp(U(log0.15,log5)); include reversed-order and competing paths. Do not call evaluator to choose any qualifying path. |
| N4 | Incoming W2W funding and subsequent mixed outward events over 1..24h; proposed outward fraction U(0.1,1.2); accounting rejection is separate and logged. |
| A1 | Combine acquisition/returning-customer mechanisms over 2..28d with regular-catchment probability U(0.2,0.9); changing activity by factor U(0.8,2.5). Cases may pass or fail multiple gates. Baseline is the actual ledger. |
| A2 | Choose2..6 regular counterparties and allocate service shares U(0.35,0.90) over 2..24h; baseline concentration may already be high. |
| A3 | 5..16 services over 0.25..3h to 2..8 wallets; bursts can span the 1h boundary; activity count baseline uses preceding28d. |
| A4 | Mixed cash services over 2..24h,2..8 wallets, cash-out probability U(0.1,0.9), common amount sampling with direction multiplier U(0.5,2); no accept-until-A4 loop. |


## 23. Compact feature architecture

Exactly 40 semantic fields: current-event2, structuring10, network12, agent14, history/coverage 2. Three-category one-hot expansion, if needed, yields42 numeric columns; it does not create new behavioural descriptors.

### 1. `amount_minor`

| Property | Specification |
| --- | --- |
| group | current-event |
| formula | Current integer amount_minor |
| entity | current event |
| window | current |
| current event inclusion | Yes |
| missing semantics | Never missing; schema rejects absent/nonpositive amount |
| purpose | Transaction value context |
| related families | ["S1", "S2", "S3", "S4", "N1", "N2", "N3", "N4", "A4"] |
| component category | B |
| direct target component | True |
| eligibility | No baseline gate; emit recent observed quantity even at cold start. |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 2. `transaction_type`

| Property | Specification |
| --- | --- |
| group | current-event |
| formula | Categorical W2W / Cash-In / Cash-Out |
| entity | current event |
| window | current |
| current event inclusion | Yes |
| missing semantics | Never missing |
| purpose | Current role and cash applicability |
| related families | ["N1", "N2", "N3", "N4", "A4"] |
| component category | B |
| direct target component | True |
| eligibility | No baseline gate; emit recent observed quantity even at cold start. |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 3. `wallet_count_1h`

| Property | Specification |
| --- | --- |
| group | structuring |
| formula | n(R_1h) |
| entity | wallet subject |
| window | 1h |
| current event inclusion | Yes, once |
| missing semantics | 0 only when mathematically zero; current ensures nonempty activity |
| purpose | Short burst size |
| related families | ["S1"] |
| component category | B |
| direct target component | True |
| eligibility | Recent-only; no baseline eligibility gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 4. `wallet_value_1h`

| Property | Specification |
| --- | --- |
| group | structuring |
| formula | sum_minor(R_1h) |
| entity | wallet subject |
| window | 1h |
| current event inclusion | Yes, once |
| missing semantics | 0 only when mathematically zero; current ensures nonempty activity |
| purpose | Short burst total value |
| related families | ["S1"] |
| component category | B |
| direct target component | True |
| eligibility | Recent-only; no baseline eligibility gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 5. `wallet_max_value_share_1h`

| Property | Specification |
| --- | --- |
| group | structuring |
| formula | max(amount in R_1h)/sum_minor(R_1h) |
| entity | wallet subject |
| window | 1h |
| current event inclusion | Yes, once |
| missing semantics | 0 only when mathematically zero; current ensures nonempty activity |
| purpose | Fragment dominance |
| related families | ["S1"] |
| component category | B |
| direct target component | True |
| eligibility | Recent-only; no baseline eligibility gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 6. `wallet_activity_acceleration_1h`

| Property | Specification |
| --- | --- |
| group | structuring |
| formula | n(R_1h)/max(1,n(B_1h)/672) |
| entity | wallet subject |
| window | 1h + preceding28d |
| current event inclusion | Yes, once |
| missing semantics | -1 if baseline-ineligible |
| purpose | Change from own background |
| related families | ["S1"] |
| component category | B |
| direct target component | True |
| eligibility | Same S1 baseline coverage and >=4 baseline events; no recent predicate gates |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 7. `wallet_similar_amount_count_7d`

| Property | Specification |
| --- | --- |
| group | structuring |
| formula | n(C_R) with S2 current-centered 5% amount tolerance |
| entity | wallet subject |
| window | 7d |
| current event inclusion | Yes, once |
| missing semantics | 0 only when mathematically zero; current ensures nonempty activity |
| purpose | Repeated similar payments |
| related families | ["S2"] |
| component category | B |
| direct target component | True |
| eligibility | Recent-only; no baseline eligibility gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 8. `wallet_similar_amount_share_7d`

| Property | Specification |
| --- | --- |
| group | structuring |
| formula | n(C_R)/n(R_7d) |
| entity | wallet subject |
| window | 7d |
| current event inclusion | Yes, once |
| missing semantics | 0 only when mathematically zero; current ensures nonempty activity |
| purpose | Repetition relative to all activity |
| related families | ["S2"] |
| component category | B |
| direct target component | True |
| eligibility | Recent-only; no baseline eligibility gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 9. `wallet_count_utc_day`

| Property | Specification |
| --- | --- |
| group | structuring |
| formula | n([UTC midnight,t]) |
| entity | wallet subject |
| window | UTC day to current |
| current event inclusion | Yes, once |
| missing semantics | 0 only when mathematically zero; current ensures nonempty activity |
| purpose | Distributed daily activity |
| related families | ["S3"] |
| component category | B |
| direct target component | True |
| eligibility | Recent-only; no baseline eligibility gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 10. `wallet_active_hours_utc_day`

| Property | Specification |
| --- | --- |
| group | structuring |
| formula | distinct occupied UTC hour buckets in current day |
| entity | wallet subject |
| window | UTC day to current |
| current event inclusion | Yes, once |
| missing semantics | 0 only when mathematically zero; current ensures nonempty activity |
| purpose | Temporal spread of daily activity |
| related families | ["S3"] |
| component category | B |
| direct target component | True |
| eligibility | Recent-only; no baseline eligibility gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 11. `wallet_day_count_growth`

| Property | Specification |
| --- | --- |
| group | structuring |
| formula | current-day count/max(1,median(28 prior calendar-day counts including zeros)) |
| entity | wallet subject |
| window | UTC day + prior28 calendar days |
| current event inclusion | Yes, once |
| missing semantics | -1 if baseline-ineligible |
| purpose | Daily increase over own background |
| related families | ["S3"] |
| component category | B |
| direct target component | True |
| eligibility | Same S3 baseline coverage and >=4 baseline events; no recent predicate gates |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 12. `wallet_near_band_count_7d`

| Property | Specification |
| --- | --- |
| group | structuring |
| formula | count of R_7d amounts in inclusive [700000,1050000] cents |
| entity | wallet subject |
| window | 7d |
| current event inclusion | Yes, once |
| missing semantics | 0 only when mathematically zero; current ensures nonempty activity |
| purpose | Large repeated payments near synthetic analytical threshold |
| related families | ["S4"] |
| component category | B |
| direct target component | True |
| eligibility | Recent-only; no baseline eligibility gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 13. `network_in_count_24h`

| Property | Specification |
| --- | --- |
| group | network |
| formula | number of relevant directed W2W edges |
| entity | current W2W receiver |
| window | 24h |
| current event inclusion | Current W2W once |
| missing semantics | 0 for non-W2W |
| purpose | Volume |
| related families | ["N1"] |
| component category | B |
| direct target component | True |
| eligibility | Current W2W; no baseline gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 14. `network_in_distinct_24h`

| Property | Specification |
| --- | --- |
| group | network |
| formula | number of distinct opposite wallet endpoints |
| entity | current W2W receiver |
| window | 24h |
| current event inclusion | Current W2W once |
| missing semantics | 0 for non-W2W |
| purpose | Counterparty breadth |
| related families | ["N1"] |
| component category | B |
| direct target component | True |
| eligibility | Current W2W; no baseline gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 15. `network_in_acceleration_24h`

| Property | Specification |
| --- | --- |
| group | network |
| formula | recent edge count/max(1,baseline edge count/28) |
| entity | current W2W receiver |
| window | 24h + preceding28d |
| current event inclusion | Current W2W once |
| missing semantics | -1 if non-W2W or baseline-ineligible |
| purpose | Change from own background |
| related families | ["N1"] |
| component category | B |
| direct target component | True |
| eligibility | Same N1 coverage 29d and >=4 directed baseline edges; no recent gates |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 16. `network_out_count_24h`

| Property | Specification |
| --- | --- |
| group | network |
| formula | number of relevant directed W2W edges |
| entity | current W2W sender |
| window | 24h |
| current event inclusion | Current W2W once |
| missing semantics | 0 for non-W2W |
| purpose | Volume |
| related families | ["N2"] |
| component category | B |
| direct target component | True |
| eligibility | Current W2W; no baseline gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 17. `network_out_distinct_24h`

| Property | Specification |
| --- | --- |
| group | network |
| formula | number of distinct opposite wallet endpoints |
| entity | current W2W sender |
| window | 24h |
| current event inclusion | Current W2W once |
| missing semantics | 0 for non-W2W |
| purpose | Counterparty breadth |
| related families | ["N2"] |
| component category | B |
| direct target component | True |
| eligibility | Current W2W; no baseline gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 18. `network_out_acceleration_24h`

| Property | Specification |
| --- | --- |
| group | network |
| formula | recent edge count/max(1,baseline edge count/28) |
| entity | current W2W sender |
| window | 24h + preceding28d |
| current event inclusion | Current W2W once |
| missing semantics | -1 if non-W2W or baseline-ineligible |
| purpose | Change from own background |
| related families | ["N2"] |
| component category | B |
| direct target component | True |
| eligibility | Same N2 coverage 29d and >=4 directed baseline edges; no recent gates |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 19. `prior_return_path_min_length_7d`

| Property | Specification |
| --- | --- |
| group | network |
| formula | min edge count over P; P ignores all amounts |
| entity | current W2W endpoints |
| window | prior7d |
| current event inclusion | Endpoints select path; current edge excluded |
| missing semantics | -1 for no path or non-W2W |
| purpose | Shortest temporal connectivity |
| related families | ["N3"] |
| component category | B |
| direct target component | True |
| eligibility | No baseline gate; emit recent observed quantity even at cold start. |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 20. `prior_return_path_count_7d`

| Property | Specification |
| --- | --- |
| group | network |
| formula | number of distinct edge-key sequences in P; no amount filters |
| entity | current W2W endpoints |
| window | prior7d |
| current event inclusion | Endpoints only; current excluded |
| missing semantics | 0 for no path/non-W2W |
| purpose | Alternative paths omitted by a single shortest path |
| related families | ["N3"] |
| component category | A |
| direct target component | False |
| eligibility | No baseline gate; emit recent observed quantity even at cold start. |
| justification | Raw event context; no family rule output. |


### 21. `prior_path_min_max_log_change_7d`

| Property | Specification |
| --- | --- |
| group | network |
| formula | max(abs(log(a_next/a_prev))) on p*; one-edge path=0 |
| entity | current W2W endpoints |
| window | prior7d |
| current event inclusion | Endpoints only; current amount excluded |
| missing semantics | -1 for no path/non-W2W |
| purpose | Prior value consistency over alternative paths |
| related families | ["N3"] |
| component category | C |
| direct target component | False |
| eligibility | No baseline gate; emit recent observed quantity even at cold start. |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 22. `current_to_selected_path_first_value_ratio`

| Property | Specification |
| --- | --- |
| group | network |
| formula | amount(T)/amount(first edge of p*) |
| entity | current W2W endpoints |
| window | prior7d + current |
| current event inclusion | Current amount in ratio only, never path selection |
| missing semantics | -1 for no path/non-W2W |
| purpose | Return value relative to selected prior route |
| related families | ["N3"] |
| component category | C |
| direct target component | False |
| eligibility | No baseline gate; emit recent observed quantity even at cold start. |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 23. `wallet_pass_through_fraction_24h`

| Property | Specification |
| --- | --- |
| group | network |
| formula | (O_prior+amount(T))/F using N4 anchor and funding definitions |
| entity | current outward wallet |
| window | anchor..current within 24h |
| current event inclusion | Current outward amount once |
| missing semantics | -1 if current not outward or no prior W2W anchor |
| purpose | Fraction of available recent funding transferred |
| related families | ["N4"] |
| component category | B |
| direct target component | True |
| eligibility | No baseline gate; emit recent observed quantity even at cold start. |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 24. `wallet_prior_funding_residual_minor_24h`

| Property | Specification |
| --- | --- |
| group | network |
| formula | F-O_prior using N4 anchor; may be negative |
| entity | current outward wallet |
| window | anchor..current within 24h |
| current event inclusion | No current amount |
| missing semantics | NaN if current not outward or no anchor; numeric -1 may be a valid residual |
| purpose | Remaining observed funding before this outward event |
| related families | ["N4"] |
| component category | B |
| direct target component | True |
| eligibility | No baseline gate; emit recent observed quantity even at cold start. |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 25. `agent_wallet_growth_ratio_7d`

| Property | Specification |
| --- | --- |
| group | agent |
| formula | D/max(1,median(four preceding weekly distinct counts including zeros)) |
| entity | current agent |
| window | 7d + preceding28d |
| current event inclusion | Current service once; cash fields include current only if cash |
| missing semantics | -1 absent agent or A1 baseline-ineligible |
| purpose | Relative customer breadth growth |
| related families | ["A1"] |
| component category | B |
| direct target component | True |
| eligibility | A1 coverage 35d and >=12 baseline services; no recent trigger gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 26. `agent_distinct_wallets_7d`

| Property | Specification |
| --- | --- |
| group | agent |
| formula | D=distinct serviced wallets in R_7d |
| entity | current agent |
| window | 7d |
| current event inclusion | Current service once; cash fields include current only if cash |
| missing semantics | 0 absent agent |
| purpose | Recent customer breadth |
| related families | ["A1"] |
| component category | B |
| direct target component | True |
| eligibility | No baseline gate; no recent trigger gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 27. `agent_new_wallet_count_7d`

| Property | Specification |
| --- | --- |
| group | agent |
| formula | size(wallets(R_7d) minus wallets(B_7d)) |
| entity | current agent |
| window | 7d + preceding28d |
| current event inclusion | Current service once; cash fields include current only if cash |
| missing semantics | -1 absent agent or A1 baseline-ineligible |
| purpose | New-to-baseline customer count |
| related families | ["A1"] |
| component category | B |
| direct target component | True |
| eligibility | A1 coverage 35d and >=12 baseline services; no recent trigger gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 28. `agent_new_wallet_share_7d`

| Property | Specification |
| --- | --- |
| group | agent |
| formula | new distinct count/D |
| entity | current agent |
| window | 7d + preceding28d |
| current event inclusion | Current service once; cash fields include current only if cash |
| missing semantics | -1 absent agent or A1 baseline-ineligible |
| purpose | Acquisition versus returning customers |
| related families | ["A1"] |
| component category | B |
| direct target component | True |
| eligibility | A1 coverage 35d and >=12 baseline services; no recent trigger gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 29. `agent_top2_count_share_24h`

| Property | Specification |
| --- | --- |
| group | agent |
| formula | top2(R_24h) |
| entity | current agent |
| window | 24h |
| current event inclusion | Current service once; cash fields include current only if cash |
| missing semantics | 0 absent agent |
| purpose | Repeat-customer concentration |
| related families | ["A2"] |
| component category | B |
| direct target component | True |
| eligibility | No baseline gate; no recent trigger gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 30. `agent_top2_share_change_24h`

| Property | Specification |
| --- | --- |
| group | agent |
| formula | top2(R_24h)-top2(B_24h), independently selected top two in each |
| entity | current agent |
| window | 24h + preceding28d |
| current event inclusion | Current service once; cash fields include current only if cash |
| missing semantics | -3 absent agent or A2 baseline-ineligible; valid range[-1,1] |
| purpose | Concentration change |
| related families | ["A2"] |
| component category | B |
| direct target component | True |
| eligibility | A2 coverage 29d, >=20 baseline services, >=5 baseline wallets; no recent trigger gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 31. `agent_service_acceleration_1h`

| Property | Specification |
| --- | --- |
| group | agent |
| formula | n(R_1h)/max(1,n(B_1h)/672) |
| entity | current agent |
| window | 1h + preceding28d |
| current event inclusion | Current service once; cash fields include current only if cash |
| missing semantics | -1 absent agent or A3 baseline-ineligible |
| purpose | Short service burst relative to own activity |
| related families | ["A3"] |
| component category | B |
| direct target component | True |
| eligibility | A3 coverage 28d+1h and >=12 baseline services; no recent trigger gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 32. `agent_distinct_wallets_1h`

| Property | Specification |
| --- | --- |
| group | agent |
| formula | distinct serviced wallets in R_1h |
| entity | current agent |
| window | 1h |
| current event inclusion | Current service once; cash fields include current only if cash |
| missing semantics | 0 absent agent |
| purpose | Breadth within a short burst |
| related families | ["A3"] |
| component category | B |
| direct target component | True |
| eligibility | No baseline gate; no recent trigger gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 33. `agent_cash_in_count_24h`

| Property | Specification |
| --- | --- |
| group | agent |
| formula | number of Cash-In services in R_24h |
| entity | current agent |
| window | 24h |
| current event inclusion | Current service once; cash fields include current only if cash |
| missing semantics | 0 absent agent or no cash-in |
| purpose | Cash direction counts |
| related families | ["A4"] |
| component category | B |
| direct target component | True |
| eligibility | No baseline gate; no recent trigger gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 34. `agent_cash_out_count_24h`

| Property | Specification |
| --- | --- |
| group | agent |
| formula | number of Cash-Out services in R_24h |
| entity | current agent |
| window | 24h |
| current event inclusion | Current service once; cash fields include current only if cash |
| missing semantics | 0 absent agent or no cash-out |
| purpose | Cash direction counts |
| related families | ["A4"] |
| component category | B |
| direct target component | True |
| eligibility | No baseline gate; no recent trigger gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 35. `agent_cash_in_value_24h`

| Property | Specification |
| --- | --- |
| group | agent |
| formula | sum of Cash-In amount_minor in R_24h |
| entity | current agent |
| window | 24h |
| current event inclusion | Current service once; cash fields include current only if cash |
| missing semantics | 0 absent agent or no cash-in |
| purpose | Cash direction magnitude |
| related families | ["A4"] |
| component category | B |
| direct target component | True |
| eligibility | No baseline gate; no recent trigger gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 36. `agent_cash_out_value_24h`

| Property | Specification |
| --- | --- |
| group | agent |
| formula | sum of Cash-Out amount_minor in R_24h |
| entity | current agent |
| window | 24h |
| current event inclusion | Current service once; cash fields include current only if cash |
| missing semantics | 0 absent agent or no cash-out |
| purpose | Cash direction magnitude |
| related families | ["A4"] |
| component category | B |
| direct target component | True |
| eligibility | No baseline gate; no recent trigger gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 37. `agent_cash_distinct_wallets_24h`

| Property | Specification |
| --- | --- |
| group | agent |
| formula | distinct serviced wallets in cash-only R_24h |
| entity | current agent |
| window | 24h |
| current event inclusion | Current service once; cash fields include current only if cash |
| missing semantics | 0 absent agent or no cash |
| purpose | Cash customer breadth |
| related families | ["A4"] |
| component category | B |
| direct target component | True |
| eligibility | No baseline gate; no recent trigger gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 38. `agent_cash_value_skew_change`

| Property | Specification |
| --- | --- |
| group | agent |
| formula | v(R_24h)-v(B_24h); v=(out-in)/(out+in), empty=0 |
| entity | current agent |
| window | 24h + preceding28d |
| current event inclusion | Current service once; cash fields include current only if cash |
| missing semantics | -3 absent agent or A4 baseline-ineligible; valid range[-2,2] |
| purpose | Cash directional change |
| related families | ["A4"] |
| component category | B |
| direct target component | True |
| eligibility | A4 historical gate: coverage 29d, >=12 baseline services and >=8 baseline cash; no current-role gate for this feature; no recent trigger gate |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 39. `wallet_observed_coverage_days`

| Property | Specification |
| --- | --- |
| group | history/coverage |
| formula | min(35, elapsed days since first prior observed participation); 0 if none |
| entity | wallet subject |
| window | all prior; scalar first observation retained |
| current event inclusion | No |
| missing semantics | 0 on first observation; never private activation |
| purpose | Observed history context |
| related families | ["S1", "S2", "S3", "S4", "N2"] |
| component category | B |
| direct target component | True |
| eligibility | No baseline gate; emit recent observed quantity even at cold start. |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


### 40. `agent_observed_coverage_days`

| Property | Specification |
| --- | --- |
| group | history/coverage |
| formula | min(35, elapsed days since first prior observed service); 0 if none |
| entity | current agent |
| window | all prior; scalar first observation retained |
| current event inclusion | No |
| missing semantics | 0 absent agent or first service |
| purpose | 35d coverage boundary is visible |
| related families | ["A1", "A2", "A3", "A4"] |
| component category | B |
| direct target component | True |
| eligibility | No baseline gate; emit recent observed quantity even at cold start. |
| justification | Continuous/count component only; never combines the complete family conjunction or thresholds into a trigger. Its target relationship must remain disclosed. |


## 24. Direct target-component disclosure

| Property | Specification |
| --- | --- |
| categories | {"A": "independent lower-level observable", "B": "overlaps with a target predicate component (including exact individual components)", "C": "strongly approximates a predicate component through a selected summary", "D": "prohibited complete/near-oracle feature; none admitted"} |
| limits | 40 semantic input fields; fixed one-hot encoding of the three type categories creates42 numeric columns for estimators needing it. Any missing indicators added by a later declared preprocessing pipeline must be counted and audited separately. No ID, absolute timestamp, channel, archetype or provenance input. |
| baseline policy | No baseline-dependent feature requires more history than its related target. Recent counts need less history by design; they are usable at cold start, while the target still requires its historical eligibility. |
| compactness justification | Keep independent context and explicit A1/A4 primitives within 40 fields. Related primitives identify which conditions fail; they are not duplicate transforms to dilute importance. Representation gaps are acceptance risks to audit before training, not evidence that V4 will improve metrics. |
| prohibition | Feature extractor must never import evaluator, return witnesses, count amount-qualifying complete paths, return full A1 conjunction, return A4 trigger, or threshold all components into any family flag. |


No categoryD field is admitted. Exact individual components are classifiedB, including growth, rather than being disguised as independent signals. The two selected-path monetary summaries areC because they approximate existential target evidence through a chosen route. A topology-only path count isA: it contains no monetary predicate decision. Jointly informative components remain permitted; a scalar full family trigger is not.

The intended target is rule-defined review evidence, so target-component learning is unavoidable and must be disclosed. Strong performance can reflect legitimate task alignment. The audit must separately test whether private fields, unrealistic absence of counterexamples or irrelevant signatures make that learning misleading.


## 25. Ground-truth independence

Evaluator input is only the validated observable event stream. It emits binary union, individual family decisions, eligibility reasons and witnesses to a separate truth/diagnostics output. Extractor receives the same permitted observable stream through a different interface; it cannot access truth, witnesses, provenance or predictions. It never calls a target predicate.

Shared utilities are limited to schema validation, UTC/key parsing, strict-prior window membership, exact counts/sums/distinct sets and median. Compound rules, target-specific witness selection and family-trigger caches cannot be shared into X. Independent hand fixtures must test both implementations so a shared utility bug is not “verified” merely by agreement.

Mutating origin, archetype, strength, scenario IDs or intended onset while holding observable history/current fields fixed must leave every label and feature unchanged. A family-specific context omitted from the allowed schema cannot secretly determine truth.


## 26. Architecture and module boundaries

```text
Synthetic population assumptions
              |
              v
Observable transaction generator ---> raw partition-local transactions
              |                            |                 |
              v                            v                 v
Private provenance                  causal evaluator   feature extractor
              |                            |                 |
              v                            v                 v
Diagnostics only                   binary review target      X
                                                           |
                                                           v
                                                    development model
                                                           |
                                                           v
                                                          score
                                                           |
                                                           v
                                                       human review
```

Provenance has no path into X or the evaluator. Supervision joins Train target to X by checked transaction ID only after independent construction. Validation target is used only for development evaluation/selection. Proposed separate packages are `population/generator`, `observable_contract`, `target_evaluator`, `feature_extractor`, `development_pipeline`, `diagnostics` and an isolated `evaluation_runner`. These names describe future modules; none is implemented in Stage 15.

The generator may schedule observable motifs but cannot call the evaluator to accept or reject events based on target. Invalid schema/accounting proposals fail with logs. Evaluator/feature modules do not import generator internals. Shared specification versions are locked before execution.


## 27. Fresh holdouts and access governance

| Property | Specification |
| --- | --- |
| freshness | Completely new V4 Final Test and Independent Evaluation, including histories, entities, labels and commitments. No V3 evaluation directory enumeration or byte access; no reinterpretation of V3 evaluation labels. |
| final | Same design distribution, horizon, unit size and opportunity laws as Train/Validation, with disjoint entities and independent streams. |
| development loader | Explicit train/validation enum only; resolve and validate path under ml_v4/data/development/<partition>; reject aliases, traversal, symlinks escaping root, wildcard roots and evaluation requests. Holdout files not mounted in development process. |
| evaluation loader | Separate evaluation-only entry point requires recorded user authorization, frozen model/preprocessor/feature/threshold hashes and matching seal. Log requester, scope, UTC, artifact hashes and operation; reject fitting and writeback to sealed inputs. |
| seal | Authorized custodian creates data once after approved implementation. Hash all new holdout raw/target/history files in its isolated environment; publish commitment root, schema/design hashes and fixed gate certificate only. Private file manifest and seeds held separately with no developer access. Stage 15 creates no holdout files or seal. |
| final access | One declared final evaluation after all development/threshold decisions. Independent evaluation is a second predeclared report under identical frozen model; neither feeds retraining. If final results drive later work, future version needs fresh holdouts. |
| provenance | Separate private diagnostics, never passed to model prediction. Custodian can compute predeclared slices after authorization without leaking provenance to X. |


## 28. Independent Evaluation shift

| Property | Specification |
| --- | --- |
| agent archetype counts | [1, 2, 2, 3, 3, 2, 2, 1] |
| agent count order | ["low_volume_stable", "medium_volume_stable", "high_volume_urban_like", "growing_legitimate", "seasonal", "concentrated_repeat_customer", "broad_customer_base", "volatile_legitimate"] |
| wallet profile counts per 100 | [20, 18, 20, 12, 10, 10, 10] |
| wallet profile order | ["low_frequency_personal", "regular_transfer", "cash_heavy", "recurring_payment", "high_activity", "collection_like", "dispersion_like"] |
| background type probabilities | {"wallet_to_wallet": 0.45, "cash_in": 0.275, "cash_out": 0.275} |
| assisted W2W probability | 0.45 |
| shared amount multiplier | 1.15 |
| amount bounds | Same[0.01,15000]USD and rounding; truncate by rejection after multiplying. All origins use shift. |
| seasonal amplitude range | [0.2, 0.5] |
| hard origin event share | 0.25 |
| unchanged | ["all target formulas/cutoffs/coverage", "feature formulas and fitted transforms", "100-wallet local reservoir", "42d warm-up and 180d scored horizon", "output schema"] |
| interpretation | Joint moderate synthetic process shift; does not isolate causal effects of individual shifted factors. Not designed from model weaknesses or to maximize failure. |


Uniformly permute the 16 archetypes with the stated exact counts, then assign8 to each of the 2 independent units; unit sizes remain unchanged.

This is a fixed joint change to mixture, demand and values with unchanged review semantics. It tests transport across a moderate synthetic process variation. It is not selected in response to errors, nor intended to cause failure. Final Test instead holds the development population law constant.


## 29. Future model-development policy

| Property | Specification |
| --- | --- |
| families | ["LogisticRegression", "RandomForest", "HistGradientBoosting", "XGBoost"] |
| alternative | If XGBoost is unavailable, declare GradientBoosting replacement before fitting; do not add a fifth family after results. |
| maximum development configurations | 36 |
| maximum development fits | 36 |
| budget | {"comparative_candidates": 24, "robustness_and_sanity": 12, "total": 36} |
| search | At most6 fixed configurations per family including class-weight choices. Exact parameters, seeds, preprocessing and 12 diagnostic fit slots frozen in a later authorized modeling plan before first fit. All failed/adaptive/seed-repeat fits consume the 36 cap; unused slots expire rather than justify more search. |
| diagnostics allocation | Reserve dominant-feature removal for 4 families (4), missingness-only (1), dominant-feature-only and tiny-set (2), Train-only shuffle (1), seed repeats (4). If a diagnostic becomes scientifically inapplicable, leave slot unused. This is a ceiling, not an instruction to fit now. |
| transforms | Fit scalers/imputers and any learned encoding on Train only. Document sentinel-to-missing conversion per column; signed valid values remain intact. Fixed three-category type one-hot allowed; no identity encoding. Validation never fits transformations or early stopping. |
| labels | Use natural frozen label prevalence. No resampling by default. Unit weighting and a Train-derived balanced class-weight option may be among frozen configurations. No SMOTE; any future resampling is a separately authorized experiment. |
| selection | Use a preregistered constrained comparison of aggregate precision/recall/FPR, family/domain/hard-origin metrics and robustness; do not rank solely on MacroF1. Numerical model acceptance tolerances and deterministic tie-break must be frozen before fitting, in the later modeling plan. |
| compatibility | No V3 model promotion or reuse of its fitted transforms. No Train+Validation refit during development. Any authorized final refit is separately budgeted and requires a re-frozen artifact before holdout access. |


## 30. Future threshold policy

Initial0.50 (score>=0.50 positive). Optimize threshold only in a later separate stage after representation, model and preprocessing freeze, using Train/Validation only. Freeze utility/review-capacity objective and grid before search, then threshold before holdout authorization. No threshold work in Stage 15.

Any future calibration is a separately declared Train/Validation-only procedure. Calibration, refitting or new threshold search after seeing Final/Independent outcomes invalidates their use as untouched final evidence. The present document does not pick a final threshold or model.


## 31. Required evaluation metrics

| Property | Specification |
| --- | --- |
| positive class | Observable review-pattern target, not criminal intent |
| overall | ["accuracy", "balanced_accuracy", "macro_f1", "suspicious_precision", "suspicious_recall", "suspicious_f1", "normal_recall", "roc_auc", "average_precision", "false_positive_rate", "confusion_matrix"] |
| definitions | {"average_precision": "AP=sum over recall increments times corresponding precision, from continuous scores; explicitly label AP, not trapezoidal PR-AUC.", "FPR": "FP/(FP+TN) on target 0 only", "confusion_matrix": "[[TN,FP],[FN,TP]]", "normal_recall": "TN/(TN+FP)", "macro_f1": "mean of class0 and class1 F1, including explicit zero-denominator convention", "undefined": "AUC/AP with no positive or negative comparison: null and reason. Empty recall/FPR support: null, not0. Precision with no predicted positives:0 with undefined flag; report numerator/denominator.", "classification": "score>=threshold; exact0.50 tie positive initially"} |
| slices | ["3 ordinary positive domains", "12 family supports/TP/FN/recall", "structuring_only", "network_only", "agent_only", "multi_domain union", "H1..H8 target 0 FPR", "routine target 0 FPR", "pre-onset campaign target 0 FPR", "legitimate-growth-origin target 0 FPR", "family near-boundary target 0 FPR"] |
| overlap | Domain/family rows overlap and cannot be added. Domain-only excludes every other domain; multi-domain is unique rows with >=2 domains. Pre-onset is diagnostic relative to that recipe only; a row may be positive through another family. |
| uncertainty | Report raw counts, episode/subject concentration, Wilson intervals as descriptive independence-based bounds, plus cluster resampling intervals by local community when possible. With only 3 or2 evaluation communities, cluster inference is unstable: report unit-specific results and avoid population precision claims. No accuracy or significance promised. |
| permutation protocol | For each frozen serious model use the same3000 Validation row indices (uniform without replacement, seed 2026092915),3 paired permutations per feature, seed 2026092916, one worker. Baseline AP and permuted AP both use exactly that same sample. Report mean signed AP drop and repeat SD; normalize absolute mean drops into top/domain shares, null if total mass is 0. Disclose sparse family sample support. No comparable native gain/impurity substitution. |


## 32. Robustness and preregistered growth audit

- same permutation-AP protocol across families
- signed AP drops and absolute top1/top3/top5 mass
- domain importance mass
- matched retrained dominant-feature removal
- missingness-only diagnostic
- small-feature models if justified
- Train/Validation marker-aware shift and conditional slices
- family dependence and overlap attribution
- eligible-only and age-stratified comparisons

Raw growth comparisons must include A1 against H7, H8, routine, legitimate-growth-origin and A1-boundary target 0 slices separately and jointly. Report AP with its subset prevalence; observed-only AUC, middle/tail overlap, availability and first-observed-age strata; entity repetition and all-origin positives must accompany aggregate discrimination. Holdout versions of these analyses occur only under authorized frozen evaluation.

Every strong feature gets the same question: valid behavioural definition, direct component, insufficient counterexamples, unrealistic population or hidden shortcut? Permutation shares are method-dependent and correlated features can divide mass. Dominant-feature removal retrains on the same rows/configuration; it measures dependence, not leakage by itself. No maximum AUC or compulsory importance flattening is a generator acceptance target.


## 33. Required shortcut, causality and accounting tests

| Test | Area | Required future audit |
| --- | --- | --- |
| T01 | Causal windows | Hand-derived equality/lower-bound/upper-bound fixtures for all 12;35d vs28d and exact baseline minimum counts; current once; state update after output. |
| T02 | Future invariance | Append or alter future events, including equal-time higher IDs; earlier targets/features unchanged. Equal-time lower IDs may change later decisions according to strict key order. |
| T03 | Ground-truth independence | Identical allowed observable history/current fields produce identical labels after all private provenance mutations. Change or remove X/model outputs: evaluator unchanged. |
| T04 | Software boundary | Static import/interface audit: extractor cannot call evaluator; evaluator cannot read X/provenance/predictions; compare independent hand implementation of every predicate on small fixtures. |
| T05 | N3 | Ordered path, reversed edge order, future edge, equal-time IDs,1/5 permitted prior edges,6 rejected, self-cycle rejection, absent path, multiple competing paths, inclusive ratio equalities and just-outside amounts; topology-count feature never monetary-filters paths. |
| T06 | Agent roles | Cash-In/Out signs and inventories; receiver-serviced assisted W2W counted once; direct W2W no agent; no W2W cash float; current cash inclusion; disjoint baselines; missingness vs valid zeros/negative changes. |
| T07 | Isolation | Disjoint opaque entities across partitions, all edges local, reset state, separate histories, no combined Train/Validation extraction; development loader denies holdout access and path escapes. |
| T08 | Identity/schedule shortcuts | Bijective wallet/agent ID renaming leaves features/labels invariant; monotone ID renaming preserves ties. Random ID ranges, irrelevant timestamps/scheduling blocks, channel, cents, sequence positions, strengths and origins get association audits. Calendar time changes may legitimately affect S3; test translations by whole UTC days with consistent histories. |
| T09 | Overlap and A1 | Raw growth AUC/AP without sign selection against H7/H8/routine/legitimate-growth/near-boundary target 0 separately and as union; missing/eligible/age strata; quantiles/tails, repeat agents, all-origin positives, each failed gate, family prevalence. No numeric AUC target or seed tuning. |
| T10 | All features/populations | Marker-aware both-class ranges, conditional family distributions, archetype/profile mixtures, coverage, wallet repetition/retention/acquisition, cash and graph support. Trace strong separation to direct components vs population assumptions; independent review required for a shortcut finding. |
| T11 | Support/prevalence | Count actual predicate-positive scored decision points and subjects/clusters against objectives. Scenario counts separately. Report all-origin labels. Preserve draws failing objectives; no relabeling, row selection or repeated generation. |
| T12 | Accounting | Positive amounts, no W2W self-edge, valid channel/agent/serviced wallet, integer ledgers, conservation and no negative wallet/e-float/cash inventories. Initial inventories/rejections excluded from X and target. |
| T13 | Reproducibility | Same manifest, streams, versions and environment reproduce canonical bytes exactly. Independent target and feature replay matches saved output; evaluator tested separately from feature calculation. |
| T14 | Operational cost | Synthetic unit fixture performance budget before generation: peak memory<=4GiB and single-thread topology enumeration completes a6200-event unit within 10min on recorded hardware. Fail/stop, never silently truncate paths or edit target for speed. |
| T15 | V3 preservation | Check explicit protected file list and named public commitment metadata. Never enumerate/open/hash V3 holdout trees; protection claim excludes their unread bytes. |


These are requirements for later implementation. Stage 15 did not execute a V4 generator, evaluator or feature extractor. The only executed checks here concern document structure, cross-references, design arithmetic and protected-file hashes. Irrelevant timestamp/ID audits must respect legitimate chronology and calendar effects; changing same-time ID order can legitimately change evidence.


## 34. Reproducibility and versioning

| Property | Specification |
| --- | --- |
| proposed master seed | 2026092915 |
| seed status | Proposal only; no random stream instantiated in Stage 15 |
| development seed derivation | For partition p and stream s: first16bytes SHA256(UTF8("mobile_money_aml_synthetic_100k_v4\|2026092915\|"+p+"\|"+s)), interpreted little-endian unsigned128. Feed explicitly version-pinned NumPy PCG64DXSM Generator; each unit gets stream suffix /unit/<index>. |
| holdout seed derivation | After authorization custodian samples a fresh256-bit secret salt, commits SHA256(salt), and derives holdout seeds by HMAC-SHA256(salt, UTF8(dataset_id\|partition\|stream\|unit)); first16bytes little-endian. Salt stays sealed until experiment retirement. Public design master seed never permits developers to regenerate holdouts. |
| streams | ["entities", "profiles", "catchments", "warmup", "background", "episodes", "amounts", "timestamps", "transaction_ids", "accounting"] |
| proposed versions | {"generator": "v4.generator.1", "target_evaluator": "v4.predicates.1", "features": "v4.features.1", "temporal": "v4.temporal.1", "manifest": "v4.stage 15.design.1"} |
| serialization | UTF8 no BOM, LF endings; JSON sorted keys, finite numbers only; observable CSV fixed field order, integer cents/IDs, UTC microseconds, rows by full key. Feature file dtype/column order and NaN representation frozen before materialization. Random draws and ID collision handling deterministic; pin Python/NumPy/dependencies and record hardware/threads. |
| versioning | Hash approved JSON specs, code, tests and environment before later execution. Any semantic or population change increments version, preserves prior draws and requires new compatibility declaration; never silently edit frozen manifest after results. |
| reproducibility | Given the same complete private/public manifest, salt/streams, code and environment, raw transactions and truth reproduce byte-for-byte. Public consumers can verify commitments without accessing private seeds or evaluation data. |
| privacy | No production customer data or brand identities; opaque synthetic identifiers only. |


## 35. V3-to-V4 comparison

| Issue | V3 design | Stage 14 finding | Proposed V4 correction | Scientific justification |
| --- | --- | --- | --- | --- |
| A1 coverage | Frozen target 28d; corrected feature35d | 436 Train/97 Validation A1 positives unavailable | Target and baseline-dependent A1 features35d; shared canonical boundaries | Eligibility consistency without changing historical evidence |
| Growth concentration | Valid growth feature strongly dominates | 98.08% of lost Validation detections carry A1 | Retain growth, disclose direct component and audit conditional overlap | Dependence does not imply private/future leakage |
| Legitimate growth | Broad routine sampling; limited acquisition/retention dynamics | All-origin hard/routine growth exists, eligible target 0 tail small | Heterogeneous local catchments, retention, acquisition, shocks and failed-gate cases | Populate meaningful combinations rather than suppress valid signal |
| Hard-negative conditioning | Universal union relabels full-predicate hard-origin rows positive | Origin cannot override target | Preserve origin only for diagnosis; every full predicate remains positive | Avoid contradictory supervision |
| N3 representation | One topology-selected path may lose evidence | N3 small and weak; improvements partial | All-topology path count and minimum-spread path summaries; full existential target separate | Richer lower-level evidence without complete path trigger |
| A4 representation | Compact skew summaries; weak A4 recall | Stage 13 additions help incompletely | Explicit cash counts/values/breadth plus baseline skew change | Expose independent cash context; assisted W2W excluded |
| S2/S4 support | Validation positives1/8 | Unreliable family generalization | 300 Validation/Final objective, subject/cluster audits, fallback challenge-set policy | Support refers to actual evidence, never campaign allocation |
| Evaluation compatibility | V3 seals tied to frozen V3 semantics | Semantic change cannot inherit evaluation validity | Fresh V4 entities, histories, labels, seeds and seals | No cross-version holdout contamination or direct metric ranking |
| Temporal consistency | Separate written and materialized implementations | A2/A4 baseline and A3 offset also differ statically | One normative contract, independent tests and explicit calendar exception | Prevent implementation drift across all 12 families |
| Feature/predicate separation | Behavioural components have unequal informativeness | Growth is not complete oracle | 40 lower-level fields; A/B/C disclosure, D prohibited, no evaluator import | Transparent component learning |
| Population scaling | Train600/96 vs Validation150/24 over 180d | Smaller global wallet pool plausibly affects novelty | 100-wallet/8-agent units repeated12/3/3/2 times | Control local saturation while preserving entity isolation |
| Evidence versioning | High selected synthetic development scores | Validation repeatedly reused | New V4 experiment; preserve V3 with protected hashes | No claim of universal or causal improvement |


V3 and V4 scores will not be directly comparable as an algorithm improvement because populations and target semantics differ. Keep reports version-specific. A future comparison must describe those changes and cannot reuse V3 evaluation outcomes.


## 36. Acceptance gates

| Gate | Requirement | Design status | Evidence | Basis |
| --- | --- | --- | --- | --- |
| G01 | Exact12 causal predicates | PASS | v4_target_predicates.json | All 12 defined with explicit conjunction, role, baseline and cold start. |
| G02 | Target/feature window alignment | PASS | v4_target_feature_alignment.json | Every family linked to explicitly scoped feature histories and missing semantics. |
| G03 | A1 history discrepancy resolved | PASS | v4_temporal_contract.json | A1 and growth both require 35d and 12 baseline services. |
| G04 | Legitimate growth/boundary design | PASS | v4_agent_population_spec.json | Acquisition/retention/shocks and explicit A1 failed-gate examples supplied. |
| G05 | H1..H8 definitions | PASS | v4_hard_negative_spec.json | Meaningful failed conditions and universal union target rule supplied. |
| G06 | Partition isolation | PASS | v4_partition_spec.json | Exact entities/events; disjoint state and local communities specified. |
| G07 | Fresh holdout policy | PASS | v4_holdout_policy.json | Fresh datasets, secret custodian streams, separate loader/seal/access policy. |
| G08 | Observable-only truth | PASS | v4_target_predicates.json | No private intent, provenance, future features or scored outputs as evaluator input. |
| G09 | No complete oracle features | PASS | v4_feature_spec.json | 40 disclosed lower-level fields; no categoryD; remaining representation gaps explicit. |
| G10 | Adequate support objectives | PASS | v4_family_support_policy.json | All 12 have 300 Validation/Final objectives and cluster/minimum/failure policy; realized support is untested. |
| G11 | Shortcut/leakage tests specified | PASS | v4_generator_audit_plan.json | Required causal, boundary, identity, role, accounting and independence tests listed. |
| G12 | Historical preservation | PASS | v4_stage15_protection.json | 702 allowlisted files will be checked before and after; evaluation bytes excluded. |


| Property | Specification |
| --- | --- |
| decision scope | Design completeness and internal consistency only. G10 approves support objectives, not achieved support. G01..G11 require later implementation verification and user authorization before any generation. Passing design gates is not an execution permission. |
| before generation | Explicit user approval for next stage; lock complete implementation manifest; execute causal/schema/isolation/accounting tests on hand fixtures; independently review generator and evaluator; recheck preservation. Any failed gate means NO GENERATION. |
| before training | Generated development support, prevalence, overlap and shortcut audits must be reviewed; keep failed draws. Fresh holdout custodian provides only predeclared pass/fail certificate. No final metric access. |
| decision precedence | C if any major design gate fails or unresolved semantic contradiction; B for bounded minor document corrections; D only if redesign lacks scientific justification; otherwise A. All A decisions remain waiting for user approval. |


“PASS” above means that the design requirement has a concrete specification; it does not assert empirical support or working implementation. The next stage must implement and test the contract on hand fixtures before any dataset generation. User approval remains required. G12 is an executed702-file preservation check; G01–G11 are design-level assessments.


## 37. Limitations

- Synthetic assumptions without operator calibration.
- No achieved family-support evidence.
- Only 3/2 heldout communities limit uncertainty claims.
- Predicate reproduction is narrower than criminal or operational AML detection.
- Compact feature representation has documented omissions.
- Joint Independent shifts do not isolate mechanisms.
- High rule alignment may remain scientifically legitimate.
- The opening inventory rule is an artificial accounting safeguard; it does not simulate real liquidity constraints.
- 100-wallet isolated communities avoid a known partition-size confound but limit network realism and independent sample count.
- Increased S2/S4/N3 opportunity allocation may enrich rare behaviours; the resulting benchmark is not a prevalence estimate. If support requires implausible activity, use the declared separate challenge-set alternative and qualify family claims.
- The target is a deterministic observable review rule. Business legitimacy not represented in the schema cannot negate it. V4 may remain easy for a well-matched learner without methodological failure.
- Positive support, negative overlap, computational cost and all proposed improvements remain unmeasured until an authorized implementation and audit.


## 38. Final decision and deliverables

**A — V4 DESIGN APPROVED FOR GENERATION.**

All 12 design gates are satisfied at the specification level. Actual support/overlap, causal implementation tests and runtime remain future acceptance gates. This decision is a technical recommendation for the next stage, **not user approval or permission to generate now**.

Delivered machine-readable specifications:

| Specification | File |
| --- | --- |
| dataset spec | [v4_dataset_spec.json](v4_dataset_spec.json) |
| temporal contract | [v4_temporal_contract.json](v4_temporal_contract.json) |
| target predicates | [v4_target_predicates.json](v4_target_predicates.json) |
| feature spec | [v4_feature_spec.json](v4_feature_spec.json) |
| target feature alignment | [v4_target_feature_alignment.json](v4_target_feature_alignment.json) |
| agent population spec | [v4_agent_population_spec.json](v4_agent_population_spec.json) |
| wallet population spec | [v4_wallet_population_spec.json](v4_wallet_population_spec.json) |
| hard negative spec | [v4_hard_negative_spec.json](v4_hard_negative_spec.json) |
| partition spec | [v4_partition_spec.json](v4_partition_spec.json) |
| family support policy | [v4_family_support_policy.json](v4_family_support_policy.json) |
| holdout policy | [v4_holdout_policy.json](v4_holdout_policy.json) |
| model development policy | [v4_model_development_policy.json](v4_model_development_policy.json) |
| evaluation metrics | [v4_evaluation_metrics.json](v4_evaluation_metrics.json) |
| generator audit plan | [v4_generator_audit_plan.json](v4_generator_audit_plan.json) |
| v3 comparison | [v4_v3_comparison.json](v4_v3_comparison.json) |
| reproducibility spec | [v4_reproducibility_spec.json](v4_reproducibility_spec.json) |
| acceptance gates | [v4_acceptance_gates.json](v4_acceptance_gates.json) |
| stage 15 decision | [v4_stage15_decision.json](v4_stage15_decision.json) |


Preservation evidence: [v4_stage15_protection.json](v4_stage15_protection.json). Document checks and hashes: [v4_stage15_verification.json](v4_stage15_verification.json).

No V4 data, empirical prevalence, feature matrix, fitted model, threshold search or holdout seal was created.702 protected files remain unchanged. No V3 holdout access or application changes occurred.

**V4 STAGE 15 DESIGN COMPLETE — WAITING FOR APPROVAL.**
