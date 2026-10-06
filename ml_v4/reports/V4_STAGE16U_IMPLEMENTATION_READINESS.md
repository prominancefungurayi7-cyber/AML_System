# MODEL V4 — STAGE 16U IMPLEMENTATION AND CUSTODY READINESS

**B — IMPLEMENTATION READY; INDEPENDENT CUSTODY NOT AVAILABLE.**

The nonproduction challenge implementation and hand-authored fixtures pass. Production generation remains **BLOCKED** because this environment does not provide an independently administered custodian boundary. No challenge data or secret salt was created.

## 1. Authority and preserved specifications

Stage 15 remains the parent population/target design. Stage 15A overrides only its named amount, episode-count, context and metadata clauses. Stage 16T challenge-specific population, opportunity, support, metrics and custody rules govern this separate challenge; the twelve Stage 15 target predicates and frozen feature contract remain unchanged. Stage 16R/16S history and decisions remain intact. The original V4 Final Test and Independent Evaluation remain `SEALED_QUARANTINED`; their public support-policy certificates remain `FAIL`.

Hash checks matched all 20 artifacts listed by the Stage 15 verification record, all 7 Stage 15A amendment artifacts and all 10 Stage 16T challenge artifacts. The saved Stage 16R/16S results were retained as historical evidence. No sealed evaluation content was enumerated, read, decrypted or hashed. Public certificate metadata only was consulted.

The Stage 15A read-only validator was attempted. It could not complete its broader protection snapshot because this checkout lacks the historical path `ml_archive/models/aml_ai_model.pkl`. This does not mismatch the Stage 15A files: all seven files in its amendment artifact hash list match. The scope and validator failure are recorded in [preservation evidence](../evidence/stage16u/preservation_verification.json).

## 2. Implementation architecture

The challenge unit writer is [stage16u_generator.py](../generation/stage16u_generator.py). It extends the frozen Stage 16R population, schema and accounting writer with Stage 16T's two arms, 56-day warm-up, 180-day scored period, 24 isolated 100-wallet/8-agent units, fixed opportunity allocations, four context roles, family mechanisms, and challenge streams. It imports no evaluator and has no target-based acceptance logic. [stage16u_support.py](../generation/stage16u_support.py) assesses completed in-memory audit records; its result cannot alter sampling or labels. [stage16u_custody.py](../generation/stage16u_custody.py) contains nonsecret seed derivation and a test-only draw lifecycle. Its production custody and generation calls fail closed.

During review, episode start sampling was corrected to include the latest fitting start while treating the scored end as exclusive. Context timestamps now use an exclusive episode-end bound. A deterministic boundary fixture covers the correction. This changes no target, budget or amount law.

The hand-authored test suite [test_stage16u.py](../tests/test_stage16u.py) exercises the challenge writer using a tiny in-memory wallet/agent fixture; [test_stage16r.py](../tests/test_stage16r.py) supplies independent predicate and temporal fixtures. No 24-unit challenge schedule was sampled. There is no authorized production materializer in this shared workspace.

## 3. Tests and implementation results

Both test commands passed **42 tests**:

- System Python 3.14.3 / NumPy 2.4.3: 42 passed.
- Project virtual environment Python 3.14.3 / NumPy 2.5.0: 42 passed.

Fixtures cover all twelve frozen predicates; causal window endpoints, same-time IDs and future invariance; serviced-wallet roles; W2W, Cash-In and Cash-Out accounting; N3 chronological paths; N4 prior funding; A1's 35-day/12-service rule; S4 conditional amounts and rounding; context history; private-field exclusion; H1–H8 hard-origin mapping; arm/unit/stream seed separation; global entity and transaction-ID checks on tiny hand-authored aggregate records; and support-gate evaluation on abstract audit records. Tests also verify that production custody and generation entrypoints reject calls.

These are fixture results, not evidence of achieved family support, full-dataset performance, challenge prevalence or full materialization reproducibility. Cross-version fixture success does not establish byte-identical random draws between NumPy 2.4.3 and 2.5.0. See [test evidence](../evidence/stage16u/implementation_tests.json).

## 4. Custody feasibility

Current execution identity is `proe\codexsandboxoffline`; the workspace is owned by `PROE\PROMINENT`. The observed workspace ACL grants modification to the shared `PROE\CodexSandboxUsers` group and full control to the owner, SYSTEM and local Administrators. The developer runtime can read and write this source tree. No separate custodian service, protected challenge mount, developer-denied plaintext location, private ID registry, or immutable authorization/access log is provisioned or verifiable here.

The in-memory lifecycle fixture is not a durable one-draw lock. Environment flags, folders under this workspace, and self-asserted certificates cannot establish the required custody. Do not generate until an independently administered account or remote runtime, protected secret/registry storage, append-only authorization log, fixed custodian-only execution entrypoint and denied developer access have been configured and tested under both identities. Exact requirements are listed in [custody readiness](../evidence/stage16u/custody_readiness.json).

## 5. Reproducibility and support policy

HMAC-SHA256 stream derivation follows the Stage 16T dataset/arm/unit/stream address and feeds NumPy PCG64DXSM. Independent addresses and test-only one-draw state transitions pass fixtures. Python 3.14.3 / NumPy 2.4.3 is recorded as the tested reference version pin; the project environment's NumPy 2.5.0 run is fixture compatibility only. No custodian environment lock or production execution record exists. The custodian must reproduce the reference pin or rerun the full fixture gate and then freeze the final code, Python/NumPy versions, hardware, call order and serialization before a draw. Custody must commit a fresh secret-salt hash, then use that one salt for the single authorized materialization and byte-identical in-custody replay. No salt, candidate stream or production transaction was created in Stage 16U.

The support assessor checks the Stage 16T family counts, subjects, clusters, units, temporal bins, concentration, per-arm, matched-hard and near-boundary objectives on post-generation aggregates. Abstract fixtures exercise PASS and failure cases. No empirical support was estimated. A failed objective must be retained and reported under Stage 16T policy; the assessor does not retry or modify data. See [support-policy readiness](../evidence/stage16u/support_policy_readiness.json) and [reproducibility readiness](../evidence/stage16u/reproducibility_readiness.json).

## 6. Preservation and scope

The Stage 15, 15A and 16T declared artifact hashes match. The existing V4 transaction/label files were not changed; no V4 features or models were created. No V1 inference, Flask file, V3 integration file, V3 artifact, V3/V4 sealed evaluation, or holdout policy was modified. The original V4 public certificates were left unchanged. No model was trained and no threshold was tuned.

Files changed for Stage 16U:

- Modified `ml_v4/generation/stage16u_generator.py` for exclusive scored-horizon handling, aggregate identity checks, and H1–H8 provenance.
- Modified `ml_v4/tests/test_stage16u.py` for those behaviours.
- Added this report and six JSON records under `ml_v4/evidence/stage16u/`.

The V3 integration was not reconfigured or launched in this stage. Its current entry/service hashes are recorded in the reproducibility evidence as a preservation snapshot.

## 7. Remaining gates and decision

Fixture-level implementation gates pass. Production custody is unavailable, the aggregate validator has not been run over a materialized draw, and the custodian environment/source freeze has not occurred. The Stage 16T protocol and this readiness decision do not authorize generation. The next required work is to provision and independently verify custody; only then can a separately authorized stage perform exactly one challenge draw.

**B — IMPLEMENTATION READY; INDEPENDENT CUSTODY NOT AVAILABLE.**

This decision authorizes custody provisioning and preproduction fixture work only. Production generation, feature construction, model fitting, threshold work and challenge evaluation remain blocked. No V4 sealed contents were accessed.

V4 STAGE 16U COMPLETE — WAITING FOR APPROVAL.
