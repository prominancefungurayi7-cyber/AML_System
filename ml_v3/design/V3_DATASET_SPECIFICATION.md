# V3 dataset specification — proposed revision 1

Dataset identity: `mobile_money_aml_synthetic_100k_v3`. Stage 8 is design only. Approval of these documents would authorize a specification, not automatically authorize generation or training. Old V2 remains an immutable methodological baseline.

## Research unit and observable schema

The 100,000 rows are real-time transaction trigger points in a synthetic Zimbabwean mobile-money environment. Evidence can describe a wallet's history, an evolving W2W network, or an agent's service history. The supervised target means an observable suspicious-pattern state warrants human review at that trigger, as defined in [the ground-truth contract](V3_GROUND_TRUTH_CONTRACT.md). It is not a static fraud/intent label.

Retain generic fields: `transaction_id`, `event_timestamp`, `sender_wallet`, `receiver_wallet`, `amount_minor`, `currency`, `transaction_type`, `channel`, `agent_id`, `serviced_wallet`, `agent_flow_direction`. Types are `cash_in`, `cash_out`, and `wallet_to_wallet`; channels are agent service or direct wallet. Currency is USD accounting units in this research version; no claim of modelling changing exchange rates or all Zimbabwean payment arrangements is made. Cash events identify the affected wallet consistently at both endpoints; direct W2W has empty agent/service fields. An assisted W2W has one specified serviced wallet but does not transfer principal into agent float.

IDs are opaque entity keys and within-partition chronological transaction order keys. They encode no class, strength or pattern. Identical timestamps use transaction ID as the tie-breaker; the same timestamp precision policy applies to every cohort. Private campaign/legitimate episode ledgers and targets are separate files and never observable features.

## Exact proposed partitions and entities

| Partition | Transactions | Wallets | Agents | Role |
|---|---:|---:|---:|---|
| Train | 60,000 | 600 | 96 | Development fitting |
| Validation | 15,000 | 150 | 24 | Development selection |
| Final Test | 15,000 | 150 | 24 | New, sealed evaluation |
| Independent Evaluation | 10,000 | 100 | 16 | New, separately sealed evaluation |
| Total | 100,000 | 1,000 | 160 | Four disjoint streams |

All streams span the same declared 180-day synthetic UTC horizon. This is entity-isolated evaluation, not a chronological hold-forward experiment. Wallet and agent sets are disjoint; every W2W edge and all history remain in one partition. No reused V2 entity, record, episode or seed-derived stream is permitted. Separate deterministic generation substreams are derived from a new master seed and versioned component names. The master seed and source revision must be committed before any generation; no seed search is allowed.

The 1,000-wallet design gives 100 observed transactions per wallet on average at fixed dataset size, supporting prior-history investigation without assuming every wallet has a dense baseline. Actual eligibility remains measured, never guaranteed by private roles. This is a focused behavioural sample, not a claim to represent the number of customers of a Zimbabwean provider.

Wallet activity tiers use shared probabilities 0.30/0.50/0.20 for low/medium/high and positive rate weights 0.5/1/2; agent tiers use the same tier probabilities and weights. These are sampled independently of campaign or target and used to produce background exposure, not as numeric model features. Entity profiles, opening balances and activation policy are also shared across cohorts. Accounting rejects negative balances or agent float and forbids label-dependent replenishment. Routine transaction types use the same 35% Cash-In / 35% Cash-Out / 30% W2W recipe and 40% mediation among W2W as the structuring matched-cohort recipe, rather than a label-specific channel shortcut.

The first 35 days contain 20,000 of the routine events, apportioned 12,000/3,000/3,000/2,000 across the partitions. These events are part of the 100,000 budget, receive the same universal reference evaluation, and are included in metrics. Schedule at least two observable events per wallet and at least twelve services per agent in this period, without changing target based on those roles. Remaining routine events and all planned scenarios occupy days 35–180. Each baseline still must satisfy its own 28-day coverage/count requirement; elapsed age alone does not make it eligible. Warm-up events may trigger baseline-free N3 or N4 conditions and are not forcibly assigned 0.

## Planned scenario workload, distinct from target counts

| Partition | Suspicious-campaign member events | Legitimate hard-scenario events | Routine events | Total |
|---|---:|---:|---:|---:|
| Train | 14,400 | 19,200 | 26,400 | 60,000 |
| Validation | 3,600 | 4,800 | 6,600 | 15,000 |
| Final Test | 3,600 | 4,800 | 6,600 | 15,000 |
| Independent | 2,400 | 3,200 | 4,400 | 10,000 |
| Total | 24,000 | 32,000 | 44,000 | 100,000 |

Each of the 12 suspicious families receives 2,000 planned member events across the dataset: 1,200/300/300/200 by partition. Each of the eight legitimate hard families receives 4,000 planned events: 2,400/600/600/400. H1, H5, H7 and H8 each split their workload equally between their two matched subtypes; H2, H3, H4 and H6 retain their single matching subtype. Matching is performed by subtype, not against a pooled mixture with different behaviour.

Campaign lengths are 12, 20 or 28 observed events. Each suspicious family has 100 campaigns: Train 60 (20 of each length), Validation 15 (5 of each), Final Test 15 (5 of each), Independent 10 (3/4/3). This sums exactly to 2,000 member events. Matched legitimate subtype groups use the same length mixtures, scaled to their episode count. Ordinary interleaving does not count toward episode length. Keep complete campaigns and accounting-valid schedules; do not truncate or discard an episode because the oracle never alerts.

The 24,000 member-event workload supplies 1,200 complete campaigns and coverage of early, onset, active and inactive stages across 12 families, while keeping 76,000 ordinary-origin events. It is a proposed sampling design for sequence coverage, not 24,000 positive labels. The old 12,000-member workload would also shrink under causal labelling. The change must be approved as part of a new experiment, not retrofitted after observing scores or a positive-rate shortfall.

## Shared generation distributions and pre-sampled strengths

Use shared amount support USD 1–25,000, with the same initial background mixture for both members of each matched pair: 75% truncated lognormal (`log(amount_minor)` mean 9, standard deviation 1.6), 25% uniform minor units, and a 35% rounding branch, all independent of target. Intended S2 anchor composition, S4 band composition, N3 return ratios and N4 funding allocation may alter joint amounts, using the same base construction on the matched legitimate subtype. Label-dependent clipping, point masses and different monetary precision are prohibited.

Shared duration supports by subtype: S1 10min–3h with a shared 25% continuation branch 1–3d later; S2 2h–10d; S3 4–18h with a shared 25% repeat-day branch; S4 2–14d; N1 30min–5d; N2 20min–3d; N3 1h–7d; N4 5min–48h; A1 1–7d; A2 6h–7d; A3 15min–2h; A4 6h–7d. Sample normalized durations from shared continuous support and vary ordering/coordination within it. Never select the final duration by an observed label or model output.

Weak/moderate/strong campaign counts have overall proportions 20/50/30. Commit balanced rounding of these proportions by family and partition before generation. They vary the distribution of a latent coordination parameter, using overlapping Beta(2,3), Beta(2,2) and Beta(3,2) distributions on [0,1]. Higher coordination compresses selected gaps and increases intended relationship reuse; the common support prevents strength from being a deterministic timing/amount code. Apply the same three-mode mixture to legitimate subtypes without exposing a malicious-strength label. Private strength never gates the reference predicates. A later implementation must pre-register its exact deterministic transformation from these draws to each family's schedule before emitting data; Stage 8 does not claim those implementations or forecast yields have been validated.

No latent rule guarantees a desired number of alerts. If schedules fail structural accounting or schema checks, stop and fix the implementation under a logged revision. Do not reroll a completed dataset because its yield, balance diagnostics or model metrics are inconvenient.

## Expected target distribution: planning calculation, not a quota

Exact label prevalence cannot be deduced from onset thresholds alone: ordinary interleaving, baseline eligibility and rebalancing affect all 12 predicates. The following is an explicit conditional planning model, **not an empirical result or a Monte Carlo simulation**. It gives a central workload forecast to be checked and reported after an independently authorized generation.

For each family assume mean campaign length 20, an 0.80 chance of ever satisfying its own predicate, and the following first onset k and active fraction q among remaining member events given onset. For persistent families, expected own-family positives per campaign are `0.80 × q × (20−k+1)`. N3 instead assumes five qualifying closure events in a campaign that reaches onset, hence `0.80 × 5 = 4`. These probabilities are assumptions about plausible schedules; they are not random switches in the label evaluator.

| Family | Assumed k given onset | Assumed q given onset | Expected own-family positives per 20 member events |
|---|---:|---:|---:|
| S1 | 5 | 0.9375 | 12 |
| S2 | 6 | 0.833333… | 10 |
| S3 | 5 | 0.9375 | 12 |
| S4 | 9 | 0.833333… | 8 |
| N1 | 5 | 0.78125 | 10 |
| N2 | 5 | 0.78125 | 10 |
| N3 | 5 | Five closure pulses, not persistent q | 4 |
| N4 | 7 | 0.714285… | 8 |
| A1 | 9 | 0.9375 | 9 |
| A2 | 9 | 0.9375 | 9 |
| A3 | 5 | 0.78125 | 10 |
| A4 | 9 | 0.625 | 6 |
| Sum across 12 representative campaigns | — | — | 108 of 240 events |

With 100 campaigns per family, this forecasts 10,800 own-family positive member events. The mean pre-onset count for a family is `0.80×(k−1) + 0.20×20`, including all events of never-onset campaigns. Across families this is 10,160 events: 5,360 before onset in campaigns that reach it and 4,800 in campaigns that never reach it. The remaining 3,040 member events are post-onset but predicate-inactive. This forecast treats other-family triggers inside campaign events as zero; actual cross-family positives must be added without double-counting the OR target, and can reduce the forecast pre-onset target-0 count.

Assume for planning that 1% of legitimate hard-scenario events and 0.2% of routine events satisfy some universal predicate: 320 and 88 positive alerts. These are legitimate-origin review targets, not mislabeled hard negatives. The central expected total is therefore **11,208 positive / 88,792 negative targets, or 11.208% alerts**, before any additional cross-family campaign triggers. Fractional partition expectations below are arithmetic expectations, not permitted fractional records.

| Partition | Member events | Expected pre-/never-onset member target 0* | Expected post-onset inactive members* | Hard-scenario events (expected target 0) | Routine events (expected target 0) | Expected all target 1* | Expected all target 0* |
|---|---:|---:|---:|---:|---:|---:|---:|
| Train | 14,400 | 6,096 | 1,824 | 19,200 (19,008) | 26,400 (26,347.2) | 6,724.8 | 53,275.2 |
| Validation | 3,600 | 1,524 | 456 | 4,800 (4,752) | 6,600 (6,586.8) | 1,681.2 | 13,318.8 |
| Final Test | 3,600 | 1,524 | 456 | 4,800 (4,752) | 6,600 (6,586.8) | 1,681.2 | 13,318.8 |
| Independent | 2,400 | 1,016 | 304 | 3,200 (3,168) | 4,400 (4,391.2) | 1,120.8 | 8,879.2 |
| Total | 24,000 | 10,160 | 3,040 | 32,000 (31,680) | 44,000 (43,912) | 11,208 | 88,792 |

*Conditional assumptions above; no independent predicate on the forecast negative member events. Realized truth overrides every estimate. “Normal events” must be reported both as 76,000 normal-origin planned events and as the realized target-0 class; these are different quantities.

The central 1% hard-origin alert assumption is optimistic and not established by these documents: qualifying lawful cycles and transit could make it much larger. Holding the central campaign and routine assumptions fixed, hard-origin alert rates of 5–15% would imply 12,488–15,688 total alerts. This is a material forecast uncertainty, not a reason to exempt legitimate narratives from the oracle.

Sensitivity, not a confidence interval: allowing campaign positive yield 35–65%, hard-origin alerts 0–15%, and routine alerts 0–1% gives 8,400–20,840 total positives (8.40–20.84%). At the lower bound Train still has about 5,040 positives, so no label manipulation is justified to preserve trainability. Preserve unexpected actual prevalence, never-onset campaigns and cross-family alerts. A future version may change campaign sampling only through a new preregistration justified by coverage/precision requirements; it must never relabel earlier events or regenerate seeds to approach 12%.

## Acceptance and migration

The generator must separately audit schema/accounting, prefix-safe labels, entity isolation, matched nuisance controls, and actual cohort/target counts. Generator-only checks may inspect newly created holdouts at generation time; development must receive only the permitted certificate described in [the holdout policy](V3_HOLDOUT_POLICY.md). No old V2 holdout is used to parameterize or validate V3.

Future stages, each requiring its own authorization: approve and freeze this design; implement the generator and independent reference evaluator; generate one new version and seal new holdouts; implement/audit the approved feature contract; run development model comparisons; freeze model/features/threshold; authorize evaluation. Old V2 and every Stage 3–7 artifact remain available unchanged. Compare old and new experiments as different target semantics, never as an unqualified improvement in the same task.
