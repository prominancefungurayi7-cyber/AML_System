# MODEL V4 — STAGE 20 CONTROLLED FEATURE-REPRESENTATION DESIGN AND COMPATIBILITY REVIEW

**A — MINIMAL FEATURE AMENDMENT DESIGN READY**

Propose **four additional observable quantities**, retaining the original forty fields unchanged: **44 semantic fields / 46 numeric estimator columns**, under `v4.features.2.proposed.stage20.1`. This is a design proposal, not an implemented or approved replacement schema. No extraction, transaction generation, model execution, fitting or threshold work occurred. XGBoost remains selected; HGB remains the comparator.

## 1. Authority and verified findings

Stage15 and15A retain authority for targets, schema and temporal rules;16R retains the one production draw;16S retains support failures;16T retains challenge governance;16U/V retain custody restrictions;17/18 retain matrices, models and fit ledger. Stage19's manifest and quantitative summaries were verified against named hashes, not rerun as model evaluation. All twelve predicates remain unchanged.

The saved findings motivating this design are S2 XGB11/23, S4 XGB4/16 and **S4-only0/12**, and A4 XGB151/222 versus HGB197/222 with46 HGB rescues. These are reused synthetic Validation observations, not independent evidence or proof of error causes. Details: [findings verification](../evidence/stage20/stage19_findings_verification.json).

## 2. Why four additions

Two S2 gaps are exact recent similar-cluster value and prior similar-cluster frequency. Two S4 gaps are recent band-amount variation and prior band frequency. All are functions of permitted observations before or at the current decision, without learned centers or private context. Counts retain more detail than boolean gates. None combines a complete predicate.

The smallest defensible proposal for these four separate information gaps uses one interpretable scalar per gap. This is not a proof of globally minimal dimension. Encoding several conditions into one scalar or packing a rule code would defeat the component policy. No separate baseline rate, growth ratio, eligibility flag, recent total-count or band-share field is proposed.

The option to **retain all40 unchanged** remains justified: zero re-extraction/refit cost, preserved compatibility and no uncertain increase in rule alignment. Its known family weaknesses and support limits must remain explicit. Design A favors a bounded information study, not a promised performance improvement.

## 3. Exact common temporal and numerical contract

For current T at UTC integer-microsecond time t, keys order by(timestamp, integer transaction_id). Prior means strictly smaller key; same-time smaller IDs count, larger IDs do not. Emit before updating state. Subject is current W2W sender, or serviced wallet for cash. Subject activity includes outgoing W2W and both cash directions once; incoming W2W establishes observation age but is not activity.

R contains prior subject activity with t−7d<time<=t, plus current once. B contains prior activity with t−35d<time<=t−7d; no current and no overlap with R. C_W contains rows satisfying `20*abs(amount(e)-amount(T))<=amount(T)`, an inclusive integer test. S4 band is inclusive700000..1050000 cents, unchanged and explicitly synthetic.

Historical eligibility for both baseline counts is actual first prior participation<=t−35d AND at least4 subject activities in B. Compute independently from observables, not rounded coverage or a target evaluator. Four similar/band rows are **not** required. Exact lower-bound observation establishes age but does not enter the open-lower count. Eligible zero qualifying events emits0; insufficient age/support emits−1. There is no recent trigger or current-band gate for the baseline fields.

Amounts remain positive integer cents. Sum/count/distinct aggregation uses exact integers; output float64 only within exact integer range0..2^53−1. Exceeding it is an explicit error, not clipping or silent rounding. Baseline−1 is the only new missing marker. Recent fields are defined at cold start. No future imputation or private activation substitutes for missing history.

## 4. Proposed append-only feature contract

### 41. `wallet_similar_amount_value_minor_7d`

- **Formula:** `sum(amount_minor(e) for e in C_R)`.
- **Window:** R=(t-7d,t] restricted to prior keys, plus current once.
- **Eligibility:** No baseline gate; valid at first activity.
- **Missingness:** Never missing for a valid event; current ensures a positive sum.
- **Unit/dtype:** cents; float64 after exact integer aggregation.
- **Relationship:** B: disclosed individual target component, S2; structuring domain.
- **Existing equivalent:** Count/share/current amount do not determine exact sum within the inclusive 5% tolerance.
- **Cost:** O(n_R) scan per subject query; O(n_35d) retained state. Optional amount index needs separate correctness review.
- **Symbolic nonredundancy witness:** Current 5000 and three prior similar amounts 4999,5000,5000 give 19999; changing 4999 to 5000 gives 20000 without changing cluster count/share. Place prior rows more than24h before current within7d, outside current UTC day; direct outgoing edges to fresh sinks, no agent/return paths/incoming anchor. Other counts/times and baseline fixed: all original40 fields unchanged.

### 42. `wallet_baseline_similar_amount_count_28d_offset_7d`

- **Formula:** `n(C_B)`.
- **Window:** B=(t-35d,t-7d] restricted to prior keys; current excluded.
- **Eligibility:** First prior participation <=t-35d AND n(B subject activity)>=4.
- **Missingness:** -1 if age or activity support fails; otherwise integer >=0 (zero valid).
- **Unit/dtype:** events; float64 after exact integer aggregation.
- **Relationship:** B: disclosed individual target component, S2; structuring domain.
- **Existing equivalent:** Existing cluster count/share are recent; baseline activity-count summaries and coverage do not reveal current-centered baseline amounts.
- **Cost:** O(n_B) current-centered range scan; O(n_35d) state. Query center must be recomputed for every current amount.
- **Symbolic nonredundancy witness:** Keep baseline keys, counts and endpoints fixed at times around t-20d; change an outgoing amount from1000 to5000 for current5000. Counts/coverage and all recent fields stay fixed, no agent or return graph. Baseline similar count changes0 to1; existing40 cannot distinguish. Use >=4 total baseline events and fixed first observation <=t-35d.

### 43. `wallet_near_band_distinct_amount_count_7d`

- **Formula:** `cardinality({amount_minor(e): e in R AND 700000<=amount_minor(e)<=1050000})`.
- **Window:** R=(t-7d,t] restricted to prior keys, plus current once.
- **Eligibility:** No baseline or current-band gate; defined for every valid subject activity.
- **Missingness:** Never missing; zero if no band rows; one means repeated identical band value.
- **Unit/dtype:** distinct cent values; float64 after exact integer aggregation.
- **Relationship:** B: disclosed individual target component, S4; structuring domain.
- **Existing equivalent:** Band count and similar-cluster count/share do not determine whether band values differ by a cent.
- **Cost:** O(n_R) scan with O(d_band) distinct-value set; rolling frequencies may update per event with exact expiry.
- **Symbolic nonredundancy witness:** Current850000, prior band rows850000,850000,850000 and one nonband100: change one old850000 to850001 outside24h/current day but within7d. Band count and similar count/share remain4 and4/5; distinct band values change1 to2. Direct fresh sink endpoints, no agent, anchor or return route; baseline unchanged. All original40 fields equal.

### 44. `wallet_baseline_near_band_count_28d_offset_7d`

- **Formula:** `n({e in B:700000<=amount_minor(e)<=1050000})`.
- **Window:** B=(t-35d,t-7d] restricted to prior keys; current excluded.
- **Eligibility:** First prior participation <=t-35d AND n(B subject activity)>=4.
- **Missingness:** -1 if age or activity support fails; otherwise integer >=0 (zero valid).
- **Unit/dtype:** events; float64 after exact integer aggregation.
- **Relationship:** B: disclosed individual target component, S4; structuring domain.
- **Existing equivalent:** No existing field measures baseline band membership; fixed baseline counts can hide arbitrary band composition.
- **Cost:** O(n_B) scan or O(1) maintained band count after expiry/migration; O(n_35d) state.
- **Symbolic nonredundancy witness:** At fixed baseline keys around t-20d change outgoing1000 to800000, maintaining counts/endpoints/first observation and no agents or return routes. Existing40 fields stay fixed; baseline band count changes0 to1. Amounts remain valid positive cents.

These are paper histories illustrating non-identifiability, not generated records, empirical support or executed extractor tests. Keep unchanged timestamp/ID/endpoint skeletons, no agent/incoming anchor/return topology, fresh current receiver and all modified recent amounts outside24h/current day. Baseline count medians, coverage, recent counts, role markers and topology remain unchanged. Future independently hand-authored fixtures must assert equality of **all forty** original outputs as well as the stated difference. No scalar full-rule flag is introduced; jointly informative primitives are deliberately disclosed.

All four fields use the common wallet role, observable inputs, precision and key semantics above. Baseline similar membership is recomputed around each current amount, never a stored episode center. Distinct means distinct **cent values**, not a rounded USD band or learned bin. S4 recent distinct remains defined when current itself is outside the band.

Full machine-readable definitions, original field order, inputs, risks and per-field fixture requirements: [minimal contract](../evidence/stage20/minimal_feature_contract.json).

## 5. Redundancy and support decisions

S2 count/share/current amount cannot determine exact cluster value within5% tolerance. Once baseline similar count is provided, its weekly rate is count/4 and the existing recent count supplies growth through the declared floor; adding both would duplicate information. S4 baseline count similarly supplies its weekly rate.

S4 recent total count is recoverable as S2 similar_count/similar_share because current always belongs to its own cluster; band share follows. Division may be difficult for a learner, but this stage prioritizes missing information over duplicate convenience transforms. S1 binary variation is recoverable from n*max_share>1 under exact aggregates, so a distinct-count field is not needed for that gate. Float boundary sensitivity must be tested later.

Both new baseline fields'−1 markers disclose the identical35d/four-activity availability condition. This is deliberate existing-style marker semantics, not a separate predicate-specific eligibility input. Exact total baseline activity count beyond the gate is deferred: it could add context but is unnecessary for those frozen support checks. Four nonmatching baseline activities must yield valid0, not missing. First observation from incoming W2W alone does not supply four activities.

With the proposed44 fields, S2/S4 rules can be expressed jointly through lower-level components and markers. That increased alignment is intentional and must not be presented as independent criminal-intent detection. Individual components are categoryB; complete conjunctions, label-conditioned values and packed rule codes remain prohibited.

## 6. Secondary domains and A4

| Family | Missing/conditional information | Decision and reason |
| --- | --- | --- |
| N1 | Incoming24h aggregate value | Defer, first secondary priority. Genuine gap;24 XGB misses, but isolate S2/S4 hypothesis first. |
| N2 | Outgoing24h aggregate value | Defer. Genuine gap; symmetry alone does not justify another field. |
| N3 | Alternative-path monetary evidence | Defer a separate route-summary design.7/130 positives have incompatible selected summaries,4 missed; no proof all4 errors caused by it. |
| A2 | Absolute24h agent service count | Defer, first secondary priority. Both missing count and HGB model difference matter. |
| S3 | UTC current-day aggregate value | Defer.1h value cannot generally recover it; preserve calendar semantics. |
| N4 | Anchored funding F | Defer. F=(a−r)/(q−1) when q!=1; at q=1 it is unidentified, and near1 is ill-conditioned. |
| A3 | Absolute1h agent service count | Defer. Acceleration only equals count under the floor; observed perfect recall is not universal sufficiency. |
| A4 | Existing primitives suffice in principle | Retain unchanged. Reject full flag and redundant derived skew additions. |

N3 options such as a topology-determined second route or prior-only spread quantiles remain lossy and need an independent order/complexity design. Do not pick a route by current return ratio, count qualifying paths or emit existence of a fully qualifying path. Combining extrema from different routes is not a valid path witness. Existing exhaustive-search performance obligations remain.

A4's same-field HGB advantage demonstrates model/configuration dependence, not a specific parameter cause. It does not authorize model replacement or tuning. XGB remains selected, HGB comparator. See [secondary review](../evidence/stage20/secondary_domain_review.json) and [A4 assessment](../evidence/stage20/a4_model_approximation_assessment.json).

## 7. Independent fixture and leakage requirements

No feature implementation or synthetic test ledger was constructed. Future hand fixtures must independently check exact outputs; evaluator/extractor agreement alone is insufficient. Required cases include35d equality,3versus4 baseline activities, t−7d ownership, same-time IDs, current once, cash/assisted roles, incoming observation versus activity, and future/private-metadata invariance.

Paper amount checks include current5000 with4750/5250 inside and4749/5251 outside; band endpoints700000/1050000 inside, adjacent cents outside; sums19999versus20000; distinct repeated850000 versus850000/850001. Test zero qualifying baseline with sufficient total support separately from−1. Replay must preserve first40 fields exactly, all IDs/labels and partition isolation. Overflow/error paths must be explicit. Full fixture requirements: [temporal correctness](../evidence/stage20/temporal_correctness_requirements.json).

Static boundaries must reject evaluator/witness access, provenance and future state. Subsequent audits should compare target0 overlap, missingness, amounts/cents, roles and origins diagnostically. No sampling or feature rejection based solely on an importance concentration target. No new labels or family-derived input is allowed.

## 8. Compatibility and inference impact

| Artifact/interface | Assessment |
| --- | --- |
| Existing Train/Validation ledgers | Contain required observables; no new dataset needed. Extraction still requires separate authorization. |
|42d warmup/35d history | Unchanged; eligibility from actual observations. No manufactured history. |
| Stage17 matrices | Preserve40-field bytes; a future44 matrix uses separate namespace and exact first40 parity check. |
| Stage18 pipelines/models |42-column fitted objects cannot consume46 columns. A new Train-fitted preprocessor/model version is required; no padding or silent replacement. |
| Proposed preprocessing | Inherit exact marker conversion/Train median(empty0)/scaling/typeonehot; add−1 conversion for two baseline fields only; no indicators. |
| Stage16T protocol1 | Not automatically compatible; explicit amendment and fresh approvals required. |
| Original sealed evaluations | Remain SEALED_QUARANTINED/supportFAIL; no access or revised compatibility claim. |
| Real-time processing | Requires complete keyed history, explicit roles and integercents; extra current-centered scans/distinct state need later performance tests. No application adapter approved. |

Four noncategorical additions yield43numeric quantities plus3type one-hot columns=46. Incremental algorithms may optimize scanning only after exact fixture/replay equivalence. Worst-case subject scans remain O(n35d) per query and memory O(n35d); no timing or throughput guarantee. Keep first observation after expiry and reject out-of-order input unless a separate replay policy is approved.

The proposed feature-comparison experiment has a new identifier without changing the dataset or target version. All original rows, labels, predicates and model artifacts remain authoritative in their own versions. Full details: [compatibility](../evidence/stage20/version_compatibility_assessment.json).

## 9. Stage16T amendment requirements

No challenge protocol was amended. A separately approved version must explicitly replace the40-field references in sections6/8/10/12 and dependent feature/hash, metrics/permutation and stage-plan records; bind44-field extractor/preprocessor versions and all freeze hashes. Per-semantic-field permutation would cover44 fields with type still jointly permuted. Retain all support/precision criteria, population rules, one-draw policy, public-only certificates and independently administered custody.

Resolve this compatibility before any affected generation/evaluation. No challenge exists now. Stage16V's custody-unavailable decision persists. Original holdout FAIL certificates are not repaired. Future independent evaluation remains one frozen primary model with only predeclared diagnostics, not the proposed development algorithm comparison. [Required approvals](../evidence/stage20/stage16t_compatibility_requirements.json).

## 10. Proposed controlled comparison — not authorized or executed

Propose four new fits: A40-XGB, B44-XGB, A40-HGB, B44-HGB. Both arms use exactly the same frozen60000Train/15000Validation rows/labels. Copy the complete Stage18 XGB/HGB dictionaries and pinned dependencies into the new preregistration; these exact dictionaries are embedded in [comparison plan](../evidence/stage20/future_experimental_comparison_plan.json). XGB:200trees, depth5, learning rate.07, minchild5; HGB:200iterations,31leaves, learning rate.07, minimumleaf20. Both retain seed2026092915, no early stopping or new weighting/resampling. Refit A as well as B for controlled parity; retain saved originals.

Fit every learned transform on Train only, with separate fitted objects per arm. Threshold stays0.50 inclusive; no Validation threshold search/calibration. Primary contrasts are B−A S2/S4 recall, including exclusive rows, alongside unionFPR and all-family/domain tradeoffs within each algorithm. Report AP/ROC, confusion, precision/recall/MacroF1 and all slices with numerator/denominator and undefined conventions unchanged. No candidate substitution or improvement certification is implied by the comparison.

Use paired detection/loss counts and per-community summaries. This Validation set generated the design hypotheses; subsequent results are exploratory. Three communities cannot support confident population inference; no row bootstrap or post-hoc significance claim. Existing support deficits remain S1/S2/S4/N1/N3/N4/A2/A3/A4. Retain all families, exact support/diversity denominators and limitations. Additional features do not create positives, independent subjects or valid holdouts.

Leakage fixtures, first40 parity and deterministic replay precede any fitting. Proposed no-fit diagnostics include marker/conditional-negative/origin associations and the fixed Stage18 paired permutation-AP protocol extended to44 fields; do not rerun it now. Old removal/shuffle fits remain historical and do not validate44 fields. Any new diagnostic fits would require additional explicit budget approval and cannot be slipped into this four-fit plan.

## 11. Fit budget, decisions and stopping

Stage18 used16 fits; its20 unused slots expired. **Currently authorized new fits:0.** The proposed four attempts require explicit prospective authorization and a policy amendment resolving that expiry, while retaining the inherited36 ceiling. Proposed cumulative attempts would be20, not a reset. A fresh linked ledger preserves Stage18 unchanged. Failed/adaptive/repeated attempts all consume slots; no automatic replacements or reuse of spare capacity.

No promotion threshold is invented after inspecting results. Any later model-selection decision requires its own predeclared rule and approval; Stage18 selection remains. Support failure, technical mismatch or missing custody cannot become a PASS through performance. No oversampling, relabeling, changed cutoffs or accept-until-support generation. See [budget and reuse policy](../evidence/stage20/fit_budget_validation_reuse_policy.json).

## 12. Limitations, preservation and next step

The proposal addresses mathematical information loss, not proven causes of each error. Sparse labels, dependent communities, synthetic assumptions and model approximation remain. More direct components may yield easier policy reproduction without real-world benefit. Symbolic witnesses and paper checks do not establish working extraction, runtime, numerical implementation or achieved gain.

The Stage15A broader historical snapshot remains incomplete as documented in16V; no historical recovery, manifest weakening or old report rewrite occurred. Named preservation excludes unread sealed bytes. No Flask, MySQL, API, V1 production or V3 integration changes occurred.

**243 named protected files** match recorded hashes. [Preservation evidence](../evidence/stage20/preservation_verification.json) records the exact scope. All earlier reports, original40 matrices, Stage18 models/ledger, labels and dataset bytes remain unchanged. New writes are this report, the design-document builder and sixteen evidence records under `ml_v4/evidence/stage20/`. No RNG, extractor, estimator or generator is imported.

Recommend review and explicit approval of the proposed feature design and Stage16T compatibility amendment. Only after that should a separately authorized implementation stage create independent fixtures and development matrices. Modeling and independent custody/evaluation need their own approvals. Retaining40 remains a valid restricted-claims alternative.

## 13. Final decision

**A — MINIMAL FEATURE AMENDMENT DESIGN READY**

Four additions are specified with observable definitions, causal availability, missingness, redundancy proofs, costs and compatibility requirements. Decision A authorizes **no implementation, extraction, generation, fitting, threshold work, sealed access or integration**. No next stage starts automatically.

V4 STAGE 20 COMPLETE — WAITING FOR APPROVAL.
