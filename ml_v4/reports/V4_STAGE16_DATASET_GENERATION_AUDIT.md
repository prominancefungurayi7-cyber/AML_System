# MODEL V4 — STAGE 16 DATASET GENERATION AND INDEPENDENT DATASET AUDIT

**D — STAGE 16 IMPLEMENTATION FAILED; DATASET STATUS UNDETERMINED.**

**Stopped at the mandatory design preflight. No dataset was generated.** The user's Stage 16 section 1 requires STOP when an implementation-blocking contradiction is found and forbids silently reinterpreting Stage 15. This report closes the failed attempt; it does not certify completed generation or dataset audits.

## 1. Authoritative input verification

All 19 required authoritative files exist and match the recorded Stage 15 SHA-256 hashes. The saved Stage 15 decision is A. Counts, dates, 12 predicates, 40 feature declarations and target/feature history references pass structural cross-checks. These checks do not establish generator consistency: Gate 1 fails on B01 below. Exact hashes and source clauses are in [design verification](../evidence/stage16_design_verification.json). Stage 15's previous PASS remains historical evidence and has not been overwritten.

## 2. Blocking amount-law conflict (B01)

[Dataset amount process](../design/v4_dataset_spec.json) (`amount_process`; report section 18) requires the shared 90%/10% lognormal mixture for background and all recipe origins, truncated to USD 0.01..15,000. [S4 opportunity recipe](../design/v4_family_support_policy.json) (`family_recipe_design.S4`; report section 22) confines recipe amounts to USD 5,000..13,000.

The unconditional mixture gives positive probability outside the S4 range. Applying it unchanged violates the S4 recipe. Conditioning it on that range, replacing it with another density, or transforming it would implement different population laws. The permission for recipe-specific amount relations does not choose among these interpretations. The word 'continuous' does not specify a uniform distribution. Shared rounding alone cannot reconcile the amount law.

A versioned amendment must define the precedence, exact S4 sampling law, matched H3 treatment, and interaction with Independent's amount multiplier and bounds. No such amendment was applied in this attempt.

## 3. Additional implementation clarification (Q01)

The common episode size is discrete uniform 8..20, while S1/S2/N1/N2 specify 4..12 events, S4 specifies 5..12, and S3/A3 cap at 16. Preparatory/pre-onset events are explicitly allowed, so these ranges are potentially compatible. The design does not define how motif counts fit a full episode, including an 8-event episode with a larger proposed motif or a 20-event episode with a 12-event motif. Define conditional count sampling and remaining-event roles, timing, values and provenance before implementation; preserve the shared law for matched hard origins. This is reported as an unresolved mapping, not proof that the intervals have no intersection.

Auxiliary Stage 15 evidence spells the design version `v4.stage15.design.1`; authoritative JSON specs use `v4.stage 15.design.1`. Hashes identify the inspected revision. This metadata discrepancy is not the stop reason.

## 4. A1 contract review

The saved target, feature declarations and alignment table agree on 35 days and at least 12 baseline services for A1 growth/newness quantities. Recent distinct-wallet count is deliberately recent-only. **Design alignment: PASS. Runtime alignment: NOT_RUN.** No claim that an implemented evaluator eliminates the V3 mismatch is made.

## 5. Generation and requested empirical results

| Partition | Planned scored | Planned warm-up | Generated scored this attempt | Generated warm-up this attempt |
| --- | ---: | ---: | ---: | ---: |
| train | 60000 | 14400 | 0 | 0 |
| validation | 15000 | 3600 | 0 | 0 |
| final_test | 15000 | 3600 | 0 | 0 |
| independent_evaluation | 10000 | 2400 | 0 | 0 |


Planned total: 100,000 scored plus 24,000 warm-up. Actual generated total in this attempt: **0**. No random production draw was consumed. No generator, target evaluator, feature extractor or evaluation loader was implemented; the new source records preflight findings only.

| Requested result | Status |
| --- | --- |
| Train/Validation class distribution and prevalence | NOT_RUN; unmeasured |
| All 12 family supports, subjects, clusters and overlap | NOT_RUN; unmeasured |
| H1–H8 and background actual target states | NOT_RUN; unmeasured |
| A1 component distributions, growth AUC/AP, legitimate-growth and boundary overlap | NOT_RUN; unmeasured |
| Agent archetype and wallet profile audits | NOT_RUN; unmeasured |
| N3, A4, S2 and S4 support and fixtures | NOT_RUN; unmeasured |
| Shortcut associations | NOT_RUN; unmeasured |
| Observable-only replay and target independence | NOT_RUN |
| Temporal safety, schema, accounting and entity isolation | NOT_RUN |
| Second-generation reproducibility | NOT_RUN |

Unavailable measurements are null in the evidence, not fabricated zero supports or passing tests. V3's A1 AUC 0.9939/AP 0.9898 remain historical context only; there is no V4 result to compare.

## 6. Evaluation status and preservation

V4 Final Test and Independent Evaluation were not generated or sealed. No public V4 commitment, private seed, evaluation manifest or custodian certificate exists from this attempt. Loader isolation is untested. No V3 evaluation tree was enumerated or its contents opened/hashed.

Before/after hashes match for **723 protected files**: 702 inherited historical/application paths and 21 Stage 15 files. Changed paths: `[]`. The claim covers the explicit allowlist, including named public commitment metadata, and excludes unread evaluation bytes. See [preservation evidence](../evidence/stage16_protection.json).

## 7. Acceptance gates

| Gate | Requirement | Result |
| --- | --- | --- |
| 1 | Stage 15 authoritative artifacts consistent | FAIL |
| 2 | 100000 scored plus 24000 warm-up events | NOT_RUN |
| 3 | Partition/entity isolation | NOT_RUN |
| 4 | Observable schema | NOT_RUN |
| 5 | Accounting validity | NOT_RUN |
| 6 | Observable-only universal evaluator | NOT_RUN |
| 7 | Exact observable-only target replay | NOT_RUN |
| 8 | Temporal safety tests | NOT_RUN |
| 9 | A1 target/feature 35d alignment implemented | NOT_RUN |
| 10 | Development prevalence assessed | NOT_RUN |
| 11 | Family support assessed without regeneration | NOT_RUN |
| 12 | H1-H8 origins, no forced negative labels | NOT_RUN |
| 13 | A1 overlap audit | NOT_RUN |
| 14 | N3/A4/S2/S4 support audits | NOT_RUN |
| 15 | Generator shortcut audit | NOT_RUN |
| 16 | Dataset reproducibility | NOT_RUN |
| 17 | Fresh sealed holdouts and loader isolation | NOT_RUN |
| 18 | Historical preservation | PASS |


Gates 2–17 remain unexecuted because Gate 1 stopped generation. Gate 9 has a passing document-level alignment check only. Gate 18 is an executed preservation check. No dataset approval follows from successfully writing this failure report.

## 8. Evidence and reproducibility of the preflight record

All 21 requested JSON evidence artifacts are supplied. The 17 empirical audit artifacts explicitly record NOT_RUN, with null measurements and the stop reason. The remaining four contain design verification, protection, decision and final record verification.

- [stage16_dataset_integrity.json](../evidence/stage16_dataset_integrity.json)
- [stage16_entity_isolation.json](../evidence/stage16_entity_isolation.json)
- [stage16_temporal_safety.json](../evidence/stage16_temporal_safety.json)
- [stage16_target_independence.json](../evidence/stage16_target_independence.json)
- [stage16_target_replay.json](../evidence/stage16_target_replay.json)
- [stage16_development_distribution.json](../evidence/stage16_development_distribution.json)
- [stage16_family_support.json](../evidence/stage16_family_support.json)
- [stage16_hard_origin_audit.json](../evidence/stage16_hard_origin_audit.json)
- [stage16_background_audit.json](../evidence/stage16_background_audit.json)
- [stage16_a1_overlap_audit.json](../evidence/stage16_a1_overlap_audit.json)
- [stage16_agent_population_audit.json](../evidence/stage16_agent_population_audit.json)
- [stage16_wallet_population_audit.json](../evidence/stage16_wallet_population_audit.json)
- [stage16_n3_audit.json](../evidence/stage16_n3_audit.json)
- [stage16_a4_audit.json](../evidence/stage16_a4_audit.json)
- [stage16_structuring_support_audit.json](../evidence/stage16_structuring_support_audit.json)
- [stage16_shortcut_audit.json](../evidence/stage16_shortcut_audit.json)
- [stage16_reproducibility.json](../evidence/stage16_reproducibility.json)
- [stage16_design_verification.json](../evidence/stage16_design_verification.json)
- [stage16_protection.json](../evidence/stage16_protection.json)
- [stage16_decision.json](../evidence/stage16_decision.json)
- [stage16_final_verification.json](../evidence/stage16_final_verification.json)


Source: [stage16_preflight.py](../generation/stage16_preflight.py). It uses standard-library document/hash operations, refuses changed frozen inputs and existing output files, and cannot generate data. Final verification hashes the source, report and other evidence; it verifies record consistency only, not dataset reproducibility.

## 9. Required next decision

Approve a separately versioned design amendment defining the S4/H3 amount process and episode-to-motif mapping. Preserve the current Stage 15 files and this failed Stage 16 attempt. A later authorized attempt must first validate the amended design, then implement and pass the required fixtures before consuming the single production draw. The Stage 16 request authorized generation conditionally; its explicit contradiction stop condition is why work stops here.

**D — STAGE 16 IMPLEMENTATION FAILED; DATASET STATUS UNDETERMINED.**

**V4 STAGE 16 COMPLETE — WAITING FOR APPROVAL.**
