# MODEL V4 — INTEGRATION STAGE 4R CONTROLLED APPLICATION SHADOW INTEGRATION

**B — SHADOW INTEGRATION IMPLEMENTED; LIMITED APPLICATION WORK REMAINS**

The post-commit shadow path, dedicated MySQL result table, isolated process boundary, staff-only delivery and separate compliance panel are implemented. **25 shadow tests and 54 Stage3 tests passed.** The four canonical transaction forms passed controlled SQLite application fixtures with real frozen V4 inference. **The complete Flask → MySQL → real-model financial fixture path was not run.** This is not an end-to-end readiness PASS. Shadow mode remains OFF by default; no production activation or V1 replacement occurred.

## 1. Recovery and frozen authority

The pre-modification named snapshot verified the twelve recovered files and inherited Stage3R evidence. Runtime/origin checks passed in the retained isolated environment. Completion rechecks all twelve against their historical hashes. The approved Stage3 service, tests and historical Stage3, Stage3R and blocked Stage4 reports remain unchanged.

The original Stage18 model remains authoritative at `ml_v4/development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib`, SHA-256 `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`. Model version is `v4.development.freeze.stage23.1`; feature version is `v4.features.1`: exactly 40 semantic fields, 42 encoded inputs, embedded fitted preprocessing, inclusive threshold 0.50. No feature amendment, alternate candidate, fitting or calibration was introduced.

Runtime remains Python 3.14.3, NumPy 2.4.3, scikit-learn 1.9.0, XGBoost 3.4.1, SciPy 1.18.0, joblib 1.5.3 and threadpoolctl 3.6.0, with one native inference thread. Ordinary Flask does not import the ML runtime through the shadow coordinator.

## 2. Application changes and commit ordering

Previously, the canonical customer route committed its parent transaction, sidecar and balances and continued legacy publication. It now invokes a separately gated shadow hook immediately after that successful commit. The existing `transaction` and `alert` events and operational meanings remain intact.

```text
Canonical customer request → existing validation/V1/application operations
 → parent + canonical sidecar + balances + capture journal COMMIT
 → fresh connection / transaction lock / durable pending record
 → fixed isolated worker / deterministic history reassessment
 → unchanged Stage3 fresh snapshot / extractor / embedded pipeline
 → dedicated final result COMMIT
 → staff-only v4_shadow_result → separate V4 Shadow AI panel
```

Only `server.py` and `templates/compliance_dashboard.html` changed among the 498 baseline paths. Server changes add the post-commit hook, staff subscription installation and logout/disconnect cleanup. New implementation files are [v4_shadow.py](../../v4_shadow.py), [worker.py](../shadow_integration/worker.py), [manage.py](../shadow_integration/manage.py), [fixture_worker.py](../shadow_integration/fixture_worker.py), [README](../shadow_integration/README.md), [UI script](../../static/v4-shadow.js), [shadow tests](../../tests/test_v4_shadow.py) and [UI tests](../../tests/v4_shadow_ui_test.cjs). The fixture worker is test-only and never selected by the application coordinator.

A source rollback reaches no shadow hook. A later shadow error cannot roll back or retry the committed payment. Storage failure is logged without publishing a success. The hook is synchronous after commit and can add up to the process timeout to request latency. No new transaction-submission API or automatic scan of historical transactions was added.

## 3. History reassessment and cold start

The worker checks approved source hashes, history authority, all six capture triggers, the original observation boundary, committed parent/canonical insert journal entries, the parent-supplied canonical row digest and MySQL server identity. Under the existing history administrative lock, it calls unchanged Stage2A `attest` with technical provenance and no desired status. The existing boundary is not reset.

Incomplete assessment stops inference. Stage3 then opens its own fresh read-only snapshot and checks source/scope freshness again. A concurrent source change can therefore return HISTORY_INCOMPLETE rather than use a stale attestation. This is prototype technical reassessment, not independent certification.

Controlled first-event fixtures prove the existing scoped cold-start path for all four forms. No synthetic warmup or 35-day waiting condition was added. Unknown history remains distinct from a verified empty observation scope. The first genuine live canonical event was not submitted in this stage.

## 4. Process and result contract

The coordinator uses the fixed isolated executable and fixed worker path with `-I -B`, no shell, closed stdin, separate stdout/stderr, a 60-second timeout and 16 KiB limit per output stream. Arguments contain only the validated transaction identifier and source/server identity. No public inference network endpoint, caller-selected code or model path exists.

Nonzero exit, timeout, oversized output, malformed/duplicate/nonfinite JSON and contract mismatches produce technical failures. Validation enforces frozen versions/hash, class-1 probability range, threshold and decision consistency. Client payloads omit paths, features, graph/history and internal exception text. A failure has NULL prediction/probability and `inference_error`; it never becomes a normal decision or probability zero.

## 5. Additive MySQL persistence and idempotency

`v4_shadow_results` was created by an explicit migration, not application startup. The repeated migration made no change. MySQL inspection confirmed BIGINT transaction identity, nullable DOUBLE probability, DECIMAL(3,2) threshold, composite primary key `(transaction_id, model_version, feature_version)` and unique inference ID. The composite key is the logical record ID. Validated JSON `body` stores the complete contract, including model hash, inference time, observation scope, scope/source revisions and history metadata. Scalar status/decision/error fields and creation time are also stored. The writer validates before persistence; database constraints reinforce status, threshold and probability consistency.

The migration left the table empty and preserved hashes of parent transactions, canonical events, capture journal and history tables. See [migration evidence](../evidence/integration_stage4r/migration.json). No old transaction AI/risk field was repurposed.

Per-transaction MySQL named locks serialize duplicate attempts. Pending is committed before child execution; final success or error is committed before notification. Retries reuse an existing final record, including technical errors. A pending record after interruption can be resumed by the local management command. A crash after prediction but before final commit may repeat computation; the guarantee is one final database identity, not exactly-once CPU execution. No automatic retry scanner is installed.

## 6. V1 separation, delivery and UI

V1 remains the operational path. V4 does not blend scores, update legacy risk/rule/AI fields, create ordinary AML alerts or trigger SAR, CTR, account actions or customer blocking. Positive shadow output only signals analyst review.

`v4_shadow_result` is emitted directly to subscribed socket SIDs. Subscription and each publication verify the current database role is compliance/admin. Logout/disconnect removes subscriptions; demotion removes delivery eligibility. The global broker is not used for V4 output. The GET-only `/api/v4-shadow/results` independently authorizes staff and returns the latest 50 safe summaries without inference or reassessment.

Delivery is best-effort within the current single-worker prototype; a durable outbox and cross-worker/Redis delivery are not implemented. Committed results can be recovered through the staff GET endpoint on refresh/reconnect. Existing legacy transport behavior was not certified or redesigned here.

The compliance panel separately shows status, decision, suspicious probability, threshold, model/feature versions and inference time. It renders text safely and keeps IDs as decimal strings. Positive wording is “Suspicious transaction pattern detected — requires analyst review.” Normal wording is “No suspicious pattern detected by V4.” Errors show “V4 inference unavailable.” A normal result does not certify legitimacy. Probability is an uncalibrated synthetic benchmark class-1 output.

> This model identifies transaction patterns defined as suspicious within the synthetic research benchmark. It does not determine that money laundering has occurred.

## 7. Verification and its limits

| Verification | Result and scope |
| --- | --- |
| Shadow suite | 25 passed; isolated application/component tests |
| Direct and assisted W2W, cash-in, cash-out | Extracted real Flask handler in a test app; exact canonical roles/cents, committed parent/sidecar/balances/journal; real V4 child using SQLite copied to memory |
| Commit/rollback | Fresh connection observes commit; rollback invokes no shadow processing/event; failed result commit leaves pending and publishes nothing |
| Technical boundary | Timeout, nonzero exit, malformed/duplicate/nonfinite JSON, output bound, integrity error and invalid contract checks |
| Decisions/persistence | Normal, exact 0.50 positive, positive and error states; NULL error probability; unchanged legacy fields; retry/restart and database uniqueness |
| Concurrency | Actual MySQL lock contention passed; duplicate coordinator behavior tested with a simulated MySQL lock adapter over isolated SQLite |
| Staff transport | Flask-SocketIO clients verify unauthorized denial, staff delivery and role demotion; event observes persisted result |
| UI | Node DOM checks normal/positive/error rendering and IDs beyond JS safe integer; no full browser visual test |
| Production worker smoke check | Actual fixed child with nonexistent ID returns EVENT_UNAVAILABLE; no live inference or new attestation |
| Stage3 regression | 54 tests passed with the authorized preservation exceptions described below |
| Saved probability/preprocessing parity | Same 64 Train + 64 Validation examples; new parity JSON equals original, maximum probability difference 0 |
| Complete Flask → MySQL → real V4 financial fixture | **NOT RUN** |

Evidence: [shadow output](../evidence/integration_stage4r/shadow_tests.txt), [Stage3 output](../evidence/integration_stage4r/stage3_tests.txt), [parity](../evidence/integration_stage4r/stage3_parity.json), [MySQL boundary checks](../evidence/integration_stage4r/live_boundary_check.json), [acceptance summary](../evidence/integration_stage4r/acceptance_summary.json).

The original Stage3 test source was unchanged. Its inherited preservation assertion expects pre-integration application bytes; the harness supplies an in-memory hash map replacing only `server.py` and the compliance template with their authorized current hashes. Every other expected hash remains enforced. Historical files are not rewritten. The harness also redirects new parity output into Stage4R. Thus “54 passed” includes these two declared application preservation exceptions, not a claim that all historical application bytes remain unchanged.

The test app uses the real extracted handler but stubs legacy V1 processing to avoid startup/training side effects. The full server was not imported or launched. The fixture worker reassesses an isolated SQLite copy and invokes the real Stage3 model; it does not exercise the production worker's complete MySQL reassessment path. Actual MySQL checks cover schema, locks, source preservation and a nonexistent-event request only. No genuine customer activity or fabricated financial row was submitted to the live scope.

An isolated MySQL deployment compatible with the frozen scope contract is still needed to exercise all four forms through the complete database/process path. Resetting or contaminating the live observation boundary to obtain a test PASS would invalidate the evidence. This outstanding test and subsequent activation review are the reason for Decision B.

## 8. Source protection and preservation

The final check verifies **496 of 498 baseline paths unchanged**, with exactly two authorized application changes recorded separately. All twelve recovered files match their historical hashes. Named protection includes frozen development data/labels, extractor, models/preprocessing, Stage21/22 experiments, Stage23 freeze, V1/V3 references, fit ledgers and earlier reports/evidence. Explicit named paths were hashed; sealed directories were not enumerated or accessed. The older broader historical snapshot limitation remains unresolved.

A source-only [backup ZIP](../evidence/integration_stage4r/approved_source_backup.zip) and [source-control inclusion allowlist](../evidence/integration_stage4r/source_protection.json) protect the recovered twelve files and current application integration sources/tests. Every archive entry was verified against its source hash. No Git staging, commit or remote publication occurred. No model binaries, datasets, runtime environments, sealed material or credential files were included. This local archive does not constitute an independent off-machine backup.

See [preservation verification](../evidence/integration_stage4r/preservation_verification.json), [authorized changes](../evidence/integration_stage4r/authorized_application_changes.json) and [decision/artifact manifest](../evidence/integration_stage4r/decision.json). New evidence builders operate on saved files and hashes; finalization does not rerun inference or connect to the database.

## 9. Final decision and remaining work

**B — SHADOW INTEGRATION IMPLEMENTED; LIMITED APPLICATION WORK REMAINS**

Complete the isolated MySQL end-to-end verification and browser review before controlled activation. Evaluate synchronous latency and the single-worker delivery limitation against the intended prototype workload. Shadow remains opt-in through `V4_SHADOW_ENABLED=ON`; no environment activation was made here. There was no new fitting, tuning, model selection, sealed evaluation or production cutover. Synthetic-data limitations, sparse family support and lack of independent operational validation persist. No later stage begins automatically.

V4 INTEGRATION STAGE 4R COMPLETE —
WAITING FOR APPROVAL.
