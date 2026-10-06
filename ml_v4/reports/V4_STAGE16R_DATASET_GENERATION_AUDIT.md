# MODEL V4 — STAGE 16R DATASET GENERATION AND INDEPENDENT DATASET AUDIT

**B — V4 DATASET CONDITIONALLY APPROVED; DEVELOPMENT ISSUE MUST BE RESOLVED.**

One production draw was retained. Development generation and observable-only replay are exact; the generation replay produced byte-identical development files and manifests. No model was fitted and no final feature matrix was constructed. Support and prevalence outcomes below are observations, not generation objectives used to select the draw.

## 1. Authority, execution and preservation

Frozen Stage 15 plus Stage 15A passed preflight. The previous failed Stage 16 attempt is unchanged. All 754 protected historical/design/failed-attempt files match before/after hashes. The master seed is 2026092915; sources and software were frozen before the draw. See [preflight](../evidence/stage16r/preflight.json), [test log](../evidence/stage16r/implementation_tests.txt), [operational fixture](../evidence/stage16r/operational_fixture.json) and [manifest](../evidence/stage16r/dataset_manifest.json). No V3 evaluation tree was enumerated, opened or hashed.

## 2. Exact sizes

| Partition | Scored | Warm-up | Wallets | Agents | Units |
| --- | ---: | ---: | ---: | ---: | ---: |
| Train | 60000 | 14400 | 1200 | 96 | 12 |
| Validation | 15000 | 3600 | 300 | 24 | 3 |
| Final Test (custodian count certificate PASS) | 15000 | 3600 | 300 | 24 | 3 |
| Independent (custodian count certificate PASS) | 10000 | 2400 | 200 | 16 | 2 |

Total: **100,000 scored + 24,000 warm-up = 124,000 observable events**. Warm-up is stored separately and enters history; no warm-up label is forced to zero. Scored horizon and dates match Stage 15. Schema, positive integer cents, unique IDs, local edges/services, activation times, electronic conservation and nonnegative wallet/agent inventories pass independent ledger checks. Cross-partition identity comparisons pass inside the custodian without publishing evaluation identities.

## 3. Development class and domain distributions

| Partition | Target 0 | Target 1 | Positive fraction | Envelope |
| --- | ---: | ---: | ---: | --- |
| train | 47770 | 12230 | 0.2038 | PASS |
| validation | 11970 | 3030 | 0.2020 | PASS |


Domain/family counts overlap; domain-only and multi-domain counts are included in the audit JSON. No evaluation prevalence is released.

## 4. All family supports

| Partition | Family | Decision points | Subjects | Episode/background clusters | Units | Objective | Status |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| train | S1 | 456 | 132 | 147 | 12 | 1200 | CONDITIONAL |
| train | S2 | 112 | 37 | 43 | 11 | 1200 | CONDITIONAL |
| train | S3 | 2292 | 397 | 673 | 12 | 1200 | PASS |
| train | S4 | 128 | 54 | 57 | 12 | 1200 | CONDITIONAL |
| train | N1 | 414 | 116 | 187 | 12 | 1200 | CONDITIONAL |
| train | N2 | 1690 | 333 | 582 | 12 | 1200 | PASS |
| train | N3 | 550 | 355 | 453 | 12 | 1200 | CONDITIONAL |
| train | N4 | 559 | 258 | 348 | 12 | 1200 | CONDITIONAL |
| train | A1 | 5773 | 90 | 2273 | 12 | 1200 | PASS |
| train | A2 | 755 | 74 | 339 | 12 | 1200 | CONDITIONAL |
| train | A3 | 883 | 77 | 249 | 12 | 1200 | CONDITIONAL |
| train | A4 | 812 | 75 | 466 | 12 | 1200 | CONDITIONAL |
| validation | S1 | 132 | 31 | 34 | 3 | 300 | CONDITIONAL |
| validation | S2 | 23 | 7 | 7 | 3 | 300 | CONDITIONAL |
| validation | S3 | 546 | 104 | 156 | 3 | 300 | PASS |
| validation | S4 | 16 | 12 | 12 | 3 | 300 | CONDITIONAL |
| validation | N1 | 101 | 28 | 42 | 3 | 300 | CONDITIONAL |
| validation | N2 | 429 | 86 | 147 | 3 | 300 | PASS |
| validation | N3 | 130 | 87 | 111 | 3 | 300 | CONDITIONAL |
| validation | N4 | 144 | 74 | 91 | 3 | 300 | CONDITIONAL |
| validation | A1 | 1467 | 23 | 570 | 3 | 300 | PASS |
| validation | A2 | 148 | 20 | 60 | 3 | 300 | CONDITIONAL |
| validation | A3 | 255 | 18 | 80 | 3 | 300 | CONDITIONAL |
| validation | A4 | 222 | 17 | 138 | 3 | 300 | CONDITIONAL |


Subjects are family-specific wallet endpoints or agents. Background clusters are unit × UTC day; episode clusters use private scenario IDs. Family overlaps and maximum subject/cluster shares are reported in full evidence. These dependent rows are not independent trials. In particular, S2/S4/N3/A4 support must be assessed from these actual counts, not intended recipe allocation. Any shortfall is retained and blocks unqualified family claims.

## 5. Hard-origin and background behaviour

| Partition | Origin | Total | Target 0 | Target 1 | Crossing fraction |
| --- | --- | ---: | ---: | ---: | ---: |
| train | H1 | 1476 | 1015 | 461 | 0.3123 |
| train | H2 | 1466 | 1192 | 274 | 0.1869 |
| train | H3 | 1464 | 1208 | 256 | 0.1749 |
| train | H4 | 1476 | 1213 | 263 | 0.1782 |
| train | H5 | 1459 | 968 | 491 | 0.3365 |
| train | H6 | 1469 | 1259 | 210 | 0.1430 |
| train | H7 | 1468 | 991 | 477 | 0.3249 |
| train | H8 | 1461 | 976 | 485 | 0.3320 |
| train | background | 24596 | 21937 | 2659 | 0.1081 |
| validation | H1 | 374 | 245 | 129 | 0.3449 |
| validation | H2 | 371 | 302 | 69 | 0.1860 |
| validation | H3 | 370 | 294 | 76 | 0.2054 |
| validation | H4 | 368 | 294 | 74 | 0.2011 |
| validation | H5 | 361 | 240 | 121 | 0.3352 |
| validation | H6 | 371 | 309 | 62 | 0.1671 |
| validation | H7 | 363 | 218 | 145 | 0.3994 |
| validation | H8 | 362 | 231 | 131 | 0.3619 |
| validation | background | 6165 | 5495 | 670 | 0.1087 |


Every origin was evaluated by the same observable union. H-origin target1 rows are retained; only target0 H-origin rows are future FPR negatives. The complete per-origin family crossings and background multi-family counts are in evidence.

## 6. A1 history and overlap

The independent A1 primitive reconstruction agrees with all development A1 decisions and eligibility flags. Both historical contracts require 35 days and 12 baseline services; an exact lower-bound fixture establishes age without counting that lower-bound event in the open baseline. This verifies the target and audit contract; no final feature extractor has been built.

| Partition | Negative cohort | Eligible A1 | Eligible negatives | Raw growth AUC | AP | Subset prevalence | Negative growth >=1.5 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| train | H7 | 5773 | 864 | 0.9142 | 0.9805 | 0.8698 | 202 |
| train | H8 | 5773 | 887 | 0.9376 | 0.9861 | 0.8668 | 151 |
| train | background | 5773 | 14044 | 0.9649 | 0.8873 | 0.2913 | 1383 |
| train | legitimate_growth | 5773 | 4893 | 0.9309 | 0.9177 | 0.5413 | 910 |
| train | A1_near_boundary | 5773 | 3864 | 0.8118 | 0.8332 | 0.5990 | 1753 |
| train | union | 5773 | 19887 | 0.9441 | 0.7769 | 0.2250 | 2931 |
| validation | H7 | 1467 | 198 | 0.9771 | 0.9964 | 0.8811 | 26 |
| validation | H8 | 1467 | 210 | 0.9930 | 0.9980 | 0.8748 | 5 |
| validation | background | 1467 | 3502 | 0.9775 | 0.9345 | 0.2952 | 304 |
| validation | legitimate_growth | 1467 | 1234 | 0.9548 | 0.9529 | 0.5431 | 221 |
| validation | A1_near_boundary | 1467 | 814 | 0.8844 | 0.9165 | 0.6431 | 315 |
| validation | union | 1467 | 4835 | 0.9699 | 0.8861 | 0.2328 | 557 |


Quantiles, means, extrema, middle-90% overlap, availability, coverage/baseline eligibility, age strata and repeated-agent counts are provided for D, U, novelty, weekly median, growth, age and baseline services. The union deduplicates overlapping negative cohorts. Near-boundary rules were declared in preflight. Legitimate-growth origin is a declared acquisition or promotion/expansion interval, not a negative label. All-origin positive counts accompany the conditioned target0 comparison.

Historical V3 AUC ≈0.9939/AP ≈0.9898 are context, not an optimization target. High AUC can follow directly from a correct compound rule; sparse eligible cohorts warrant an insufficient-support interpretation. The synthetic assumptions are not independently calibrated operator behaviour, so this audit cannot certify realistic overlap or transportability. No A1 result caused regeneration.

## 7. Population and shortcut audit

Archetype/profile counts, events, target prevalence, A1–A4 support, per-agent positives and maximum agent share are saved for both development partitions. All declared agents are retained in concentration denominators, including zero-positive agents. Wallet-profile rows use the current wallet subject, not a duplicated count of both W2W endpoints.

Descriptive target associations cover random-ID ranges and final digits, time blocks, cents, channel, wallet/agent IDs, unit, profile, archetype, origin, intended family, strength and motif/context role. Supported nearly pure groups are explicitly recorded (N>=50 and prevalence <=0.01 or >=0.99). Such a conditional group alone is not proof that an artifact predicts the whole target. High-cardinality IDs and legitimate temporal/type effects require interpretation. This is a descriptive audit, not a fitted shortcut classifier or proof against every hidden shortcut.

## 8. Causality, independence, N3 and A4

Hand fixtures cover all 12 positive predicates and baseline-support boundaries; exact prior/window roles, future append invariance, same-time ordering, emit-before-update, partition reset, S3 midnight/day translation, A1 age, N4 causal funding, N3 paths 1–5 and too-long/repeated/reversed/future paths, competing paths, inclusive amount bounds and self-edge rejection. A4 fixtures verify separate cash counts/values, signs, breadth and assisted/direct service handling. Observable schema rejects extra private columns. Source inspection confirms the generator cannot call the evaluator and the evaluator cannot read provenance; identity renaming leaves decisions unchanged.

Clean replay reads only warm-up and scored observable CSVs, recomputes complete binary/family evidence and matches stored development output exactly. Saved private provenance is not loaded by the replay. Tests do not establish production effectiveness.

## 9. Stage 15A implementation

S4 and H3 use the same base-mixture conditional sampler, never a uniform replacement. Common half-up cent rounding and the exact bounded log transformation are implemented. The Independent transformation is tested on non-dataset fixtures; evaluation outputs remain sealed. Numerical support rejection is distinct from forbidden target-based retries.

Actual E/M/R counts, context roles and timing match saved episode plans. E remains within 8..20, motif counts use the amended conditional laws, context events enter normal history, and S4/H3 observed development motif amounts stay within 500000..1300000 cents. Residual budget transfers are reported. No label quotas or acceptance-until-positive loops occur.

## 10. Fresh evaluation seal and access boundary

Public V4 commitment: `6448b0fb8b7ed7f3cc3e58bae9a2565f45dd5d2d6cccb91b74fdc4580696f0f5`. Disposition: **SEALED_QUARANTINED**.

The separate custodian process generated fresh evaluation entities and histories, evaluated and replayed targets privately, and encrypted all data, private manifests and secret salt in a Windows current-user DPAPI envelope. No plaintext evaluation file is placed in the development tree. The development loader accepts exact Train/Validation names and declared files only; path escapes, aliases and evaluation requests fail closed. Authorized evaluation requires recorded user authorization, frozen artifact hashes and matching commitment. This is process/API separation plus encryption under the current OS user; it is not a separate-account adversarial isolation claim.

| Partition | Schema | Counts | Isolation | Causal evaluator | Support policy | Seal |
| --- | --- | --- | --- | --- | --- | --- |
| final_test | PASS | PASS | PASS | PASS | FAIL | PASS |
| independent_evaluation | PASS | PASS | PASS | PASS | FAIL | PASS |


Only these predeclared certificates and public commitments are released. A failed support certificate quarantines the seal and blocks training pending versioned scientific review; no private family counts or prevalence are disclosed. No sealed dataset was reopened after sealing.

## 11. Reproducibility and protection

The isolated second development generation used unchanged configuration and streams. Observable files, ground truth, family evidence, diagnostic provenance/populations and partition manifests are byte-identical. Verification files were deleted after their hashes were recorded. This was a reproducibility replay, not a second candidate draw. [Reproducibility evidence](../evidence/stage16r/reproducibility.json) and [protected hashes](../evidence/stage16r/protection.json) contain the checks.

## 12. Acceptance gates

| Gate | Requirement | Status |
| --- | --- | --- |
| G1 | authoritative Stage 15 + 15A consistency | PASS |
| G2 | exact dataset sizes | PASS |
| G3 | entity isolation | PASS |
| G4 | observable schema | PASS |
| G5 | accounting validity | PASS |
| G6 | observable-only evaluator | PASS |
| G7 | exact target replay | PASS |
| G8 | temporal safety | PASS |
| G9 | A1 35d alignment | PASS |
| G10 | development prevalence | PASS |
| G11 | family support | REVIEW_REQUIRED |
| G12 | hard-origin semantics | PASS |
| G13 | A1 overlap audit | PASS |
| G14 | N3/A4/S2/S4 audit | PASS |
| G15 | generator shortcut audit | PASS_WITH_LIMITS |
| G16 | reproducibility | PASS |
| G17 | sealed holdouts and loader isolation | PASS |
| G18 | historical preservation | PASS |
| G19 | S4/H3 amount implementation | PASS |
| G20 | episode/motif/context implementation | PASS |

## 13. Decision and evidence

**B — V4 DATASET CONDITIONALLY APPROVED; DEVELOPMENT ISSUE MUST BE RESOLVED.**

Any prevalence/support or shortcut review requirement must be resolved under the frozen failure policy before further work. Preserve this first production draw; do not regenerate to improve counts or discrimination. A separately authorized challenge set or new version is a future scientific decision, not part of this attempt. No model training, feature construction, threshold tuning, V1 replacement or application integration is authorized here.

Full evidence: [Train audit](../evidence/stage16r/train_audit.json), [Validation audit](../evidence/stage16r/validation_audit.json), [dataset integrity](../evidence/stage16r/dataset_integrity.json), [observable replay](../evidence/stage16r/target_replay.json), [decision](../evidence/stage16r/decision.json), [public custodian certificate](../evidence/stage16r/holdout_public_certificate.json). A1 audit primitives are isolated diagnostic arrays under the same evidence directory, not model features.

**V4 STAGE 16R COMPLETE — WAITING FOR APPROVAL.**
