# MODEL V2 — STAGE 8 DECISION-POINT-AWARE REDESIGN PROPOSAL

**Proposal:** create a separately versioned `mobile_money_aml_synthetic_100k_v3` experiment whose target is an observable suspicious-pattern review state at the current transaction. Preserve V1 and the original V2 experiment. The redesign is motivated by causal correctness and an explicit decision point, **not by changing labels to obtain better scores**. Stage 8 creates design documents only.

## 1. Target semantics and scenario truth

For each transaction T, evaluate all 12 frozen family predicates using strictly prior same-partition history **plus the current transaction fields**. `decision_point_target(T)` is 1 if at least one predicate holds, otherwise 0. The transaction is the trigger; the evidence concerns its wallet, current network edge, or agent. A review alert does not prove money laundering or intent and does not replace human investigation. The research scope remains Zimbabwean mobile-money AML decision support for structuring, network and agent behaviour.

`scenario_member`, private campaign/family/strength, and legitimate-scenario provenance describe generation intent. They are separate metadata and cannot gate the target or enter X. This resolves an otherwise fundamental contradiction: a legitimate-origin event satisfying the same observable condition receives the same review target. Legitimate-origin target-0 events are the hard negatives; lawful origin alone does not force zero. Identical allowed histories/current fields must produce identical targets.

The full [ground-truth contract](../redesign/V3_GROUND_TRUTH_CONTRACT.md) defines storage separation, multi-family witnesses, onset, expiry, reactivation, cross-family triggers and the limits of deterministic synthetic truth.

## 2. Exact proposed onset conditions

The [scenario onset contract](../redesign/V3_SCENARIO_ONSET_CONTRACT.md) is authoritative for subject definitions, monetary arithmetic and boundary semantics. Recent windows include T and exclude the lower time boundary; their 28-day baseline precedes the recent window and excludes T. Wallet/graph baseline minima are four relevant events; agent minimum is twelve services unless a stricter condition is stated. Every baseline-dependent condition also requires the complete baseline to have been observed. Zero denominators fail, and missing history never implies a low normal rate.

| Family | Proposed condition; all listed clauses are required |
|---|---|
| S1 variable fragments | Wallet 1h count ≥ 4; ≥ 2 distinct amounts; sum ≥ USD 300; largest share ≤ 0.60; count ≥ 3 × max(1, baseline expected hourly count). |
| S2 repeated amounts | Current-amount ±5% cluster in 7d: ≥ 4 members, sum ≥ USD 200, share ≥ 0.60, count ≥ 2 × max(1, matching baseline count / 4). |
| S3 same-day fragments | Observed current UTC day: ≥ 6 wallet events over ≥ 3 hour buckets, sum ≥ USD 500, count ≥ 2 × max(1, median prior 28 complete daily counts). |
| S4 band history | Current amount in the synthetic USD 7,000–10,500 band; 7d count ≥ 5; band count ≥ 3 with ≥ 2 distinct band amounts; band share ≥ 0.40; band count ≥ 2 × max(1, baseline band count / 4). |
| N1 collection | Current W2W into receiver; 24h inflow count ≥ 4, ≥ 3 distinct senders, sum ≥ USD 300, count ≥ 2 × max(1, preceding 28d inflow count / 28). |
| N2 dispersion | Current W2W from sender; 24h outflow count ≥ 4, ≥ 3 distinct receivers, sum ≥ USD 300, count ≥ 2 × max(1, preceding 28d outflow count / 28). |
| N3 cycle | Current W2W `s→r` closes a simple, temporally ordered strictly prior path `r→…→s` of 1–5 edges within 7d. Adjacent prior amounts have ratios [0.25,4]; current/first-path-edge amount lies in [0.25,1.25]. At least one qualifying path; no self-loop or future edge. |
| N4 pass-through | Current outgoing W2W/Cash-Out; an earlier W2W inflow anchors the observed 24h funding interval. Observed funding F ≥ USD 100; outward total O including T satisfies 0.50 ≤ O/F ≤ 1; current amount ≤ remaining observed funding before T. Cash funding/inbound legs do not themselves trigger N4. |
| A1 wallet growth | Agent 7d distinct count ≥ 6, at least 4 wallets absent from preceding 28d union, new share ≥ 0.50, recent distinct count ≥ 1.5 × max(1, median of four preceding 7d distinct counts). |
| A2 concentration | Agent 24h service count ≥ 8; top-two wallet count share ≥ 0.65 and ≥ 0.20 above preceding 28d top-two share. Baseline ≥ 20 services and ≥ 5 distinct wallets. |
| A3 burst | Agent 1h service count ≥ 5 over ≥ 3 wallets; count ≥ 3 × max(1, preceding 28d service count / 672). |
| A4 imbalance | Current cash service; 24h ≥ 6 cash events over ≥ 3 wallets; absolute signed value skew ≥ 0.60 and count skew ≥ 0.50 with matching signs; value-skew change from prior baseline ≥ 0.40. Baseline ≥ 8 cash events and ≥ 12 services. W2W never changes float. |

These are proposed synthetic ground-truth assumptions frozen before results, not regulatory limits or application detection rules. The USD 10,000 reference used by S4 has no asserted Zimbabwean regulatory status. No earlier N3 edge becomes positive because a future edge closes the cycle.

## 3. Pre-onset and post-onset treatment

Pre-onset member events remain scenario members but target 0 unless another independently observable predicate qualifies. Never-onset campaigns are retained. After onset, the family condition must still hold for the current relevant event; there is no permanent campaign label. Expired windows, dilution and balancing can return the target to 0. N3 closure pulses and N4 outgoing roles prevent unrelated later events from inheriting a previous alert. The reference evaluator uses full observable history, including ordinary interleaving, never only known campaign members.

## 4. Minimum justified feature proposal

The [feature architecture proposal](../redesign/V3_FEATURE_ARCHITECTURE_PROPOSAL.md) contains 32 logical columns: three current-event values, seven structuring summaries, ten network summaries, nine agent summaries, and three observable history-coverage values. This count follows the identified information requirements; it is not a requirement to preserve or enlarge the old 30.

The principal changes are current-event inclusion; current-edge prior-path length and return-value ratio; receiver collection breadth/intensity and baseline change; role-aware observed funding/share/delay; agent wallet-population change; short-window concentration and change; bounded cash count/value imbalance and baseline change. Each column has an explicit decision-time definition and a reason tied to Stage 7. Exact compound oracle conditions, onset flags and private metadata are excluded. Stage 6 candidates are not automatically promoted.

The proposed representation is not yet proven sufficient or minimal. Path compression, funding attribution, sparse baselines and missing rule ingredients are declared limitations. A later separately authorized feature audit must resolve semantics and freeze ordered columns/preprocessing before model testing. V2's 30 definitions can be ported into a separately named V3 comparator; no old artifact is edited.

## 5. Hard scenarios and generator controls

The [hard-negative specification](../redesign/V3_HARD_NEGATIVE_SPECIFICATION.md) keeps all eight cohorts: H1 S1/S3 busy trading; H2 S2 recurring payments; H3 S4 recurring large payments; H4 N1 collection; H5 N2/N4 payroll/transit; H6 N3 refunds/settlement; H7 A1/A3 busy agents; H8 A2/A4 concentrated customers/cash demand. Their distinctions require observable baseline stability, timing, composition or cash dynamics. Ambiguous qualifying lawful behaviour remains a review target.

The proposal matches type, channel/mediation, episode-length and endpoint-service recipes by each subtype, with shared monetary support and duration distributions. It audits activity and baseline opportunity as well as unique-serviced-wallet counts conditional on graph/type/length. This directly addresses Stage 7's N3/H6 type/channel imbalance and differing episode sizes. Match generation cohorts and irrelevant opportunities; do not force target-conditioned behavioural distributions to be identical. Preregistered balance flags trigger documented review, not seed rerolling, episode deletion or score-based rebalancing.

## 6. Scale, partitions and expected targets

The [dataset specification](../redesign/V3_DATASET_SPECIFICATION.md) fixes 100,000 observable transactions, 1,000 disjoint wallets and 160 disjoint agents. Each of four streams spans 180 days. The first 35-day background phase uses 20,000 routine events inside the budget; eligibility still requires actual observed history. No history, entity or W2W edge crosses a partition boundary.

| Partition | Transactions | Wallets | Agents | Campaign members | Hard-scenario origin | Routine origin |
|---|---:|---:|---:|---:|---:|---:|
| Train | 60,000 | 600 | 96 | 14,400 | 19,200 | 26,400 |
| Validation | 15,000 | 150 | 24 | 3,600 | 4,800 | 6,600 |
| New Final Test | 15,000 | 150 | 24 | 3,600 | 4,800 | 6,600 |
| New Independent | 10,000 | 100 | 16 | 2,400 | 3,200 | 4,400 |
| Total | 100,000 | 1,000 | 160 | 24,000 | 32,000 | 44,000 |

There are 1,200 complete planned suspicious campaigns, with length 12/20/28 mixtures and equal family-event budgets. The larger member cohort provides complete sequence/onset coverage; it does not prescribe its positive labels. A proposed 20/50/30 strength mixture has common support and never changes onset eligibility.

**Conditional planning forecast, not generated data:** mean length 20, 80% eventual own-family onset, and explicit family onset-position/active-duty assumptions give 10,800 positive member events. Assume 1% hard-origin and 0.2% routine-origin reference positives: 320 + 88. The resulting central forecast is **11,208 positive / 88,792 negative targets (11.208%)**. All arithmetic assumptions and formulas, including N3 closure pulses, are in the dataset specification; none is a label quota or a result calibrated using a classifier.

| Partition | Expected pre-/never-onset member target 0* | Expected post-onset inactive members* | Expected all target 1* | Expected all target 0* |
|---|---:|---:|---:|---:|
| Train | 6,096 | 1,824 | 6,724.8 | 53,275.2 |
| Validation | 1,524 | 456 | 1,681.2 | 13,318.8 |
| Final Test | 1,524 | 456 | 1,681.2 | 13,318.8 |
| Independent | 1,016 | 304 | 1,120.8 | 8,879.2 |
| Total | 10,160 | 3,040 | 11,208 | 88,792 |

*The forecast assumes no additional cross-family trigger on the estimated negative member events. Of 10,160 pre-/never-onset events, 5,360 precede onset in campaigns that eventually qualify and 4,800 belong to never-onset campaigns. Actual independent predicates can reduce those zero counts. Fractional counts are expectations only. The central hard-origin alert assumption is optimistic; qualifying lawful cycles/transit could raise it substantially. A broad sensitivity range is 8,400–20,840 positives (8.40–20.84%), not a confidence interval. Preserve realized prevalence and label every record from the universal oracle; do not force 12,000 positives. “Normal-origin” cohorts and the target-0 class are reported separately.

## 7. New holdout procedure

The [holdout policy](../redesign/V3_HOLDOUT_POLICY.md) requires fresh generation streams and forbids reuse of the byte-read V2 holdouts as new sealed evaluation sets. The separately authorized generator creates and validates new evaluation files, computes streaming digests at generation time, stores private file integrity records and publishes a pinned public commitment without holdout paths, distributions or alert counts.

Development loaders and hash tools expose only Train/Validation allowlists. They cannot import evaluation paths or recursively inventory a dataset root. Development can check the public certificate against its pinned digest without reopening holdouts. **This verifies the committed metadata, not the continued integrity of unread bytes.** Actual byte integrity is checked by the separately authorized evaluator after the model, feature contract and threshold are frozen. Software separation reduces accidental access; no encryption, external custodian or OS-isolation claim is made.

## 8. Future development, metrics and preregistration

The [evaluation protocol](../redesign/V3_EVALUATION_PROTOCOL.md) freezes the design before generation, then independently freezes extraction/preprocessing before any candidate search. A bounded future comparison permits at most 36 configurations across three model families, Train-only fitted transformations, a declared seed policy and initial threshold 0.50. Threshold/calibration work requires a separate later authorization; neither holdout selects a model or threshold.

Report Accuracy, Balanced Accuracy, Macro F1, suspicious precision/recall/F1, normal recall, ROC-AUC, Average Precision, FPR and confusion matrices. Also report family/domain recall from actual evidence labels; strength, onset/activation and N3 closure recall; pre-onset and inactive-state false positives; H1–H8 and subtype FPR; and total review rates in legitimate-origin cohorts. Support counts, multi-family overlap, undefined metrics and dependence between related events must be explicit.

Macro F1 ≥ 0.80, suspicious recall ≥ 0.70, suspicious F1 ≥ 0.65, structuring/network/agent recall ≥ 0.60/0.70/0.65, AP ≥ 0.65 and preferably FPR ≤ 0.08 remain research goals. **THESE ARE GOALS, NOT DATASET DESIGN CONSTRAINTS.** Never alter labels, generator definitions, features or evaluation simply to achieve them.

## 9. Limitations and migration

The exact onset predicates are unvalidated synthetic definitions. A model can approximate their observables without demonstrating real-world AML effectiveness. Legitimate review positives, uncertain attribution of funds, sparse histories, overlapping families, arbitrary window/band constants, selected path summaries and residual generation artefacts remain limitations. The positive-rate calculation is a transparent planning assumption rather than evidence that a not-yet-written generator will achieve it.

Approve and freeze the proposal first; separately authorize generator/reference-evaluator implementation and structural audit; generate new V3 data once and seal fresh holdouts; audit and freeze features; run bounded development experiments; freeze the final model/threshold; then separately authorize evaluation. No step is executed by Stage 8. Old V2 remains labelled by campaign membership, while V3 will use the decision-point target. Their raw metrics are not measurements of exactly the same prediction task.

## 10. Stage 8 protection and deliverables

Created seven Markdown design documents in `ml_v2/redesign/` and this report. No executable source, feature matrix, dataset, label or model was created or changed. Existing V1/V2 artifacts remain outside the write scope. Current V2 holdout files were excluded from every Stage 8 read, directory traversal and hash check.

Document validation checked all eight outputs and relative links, the 12 family conditions, the 32 proposed feature columns, and the scenario/partition forecast arithmetic. Before/after SHA-256 inventory comparison passed for 538 existing files across explicit V1/application and permitted V2 development, source, design, model and report paths. The aggregate digest was unchanged: `f7d1f8320afdfb9794d4f254fea50f5e5d664e147c1185c616bc26e009701356`. Only explicit permitted roots were traversed; neither the V2 raw-data root nor its holdout subtree was traversed. This confirms unchanged contents for the audited files, without claiming a fresh byte-integrity check of the prohibited holdouts.

V2 STAGE 8 COMPLETE — WAITING FOR APPROVAL.
