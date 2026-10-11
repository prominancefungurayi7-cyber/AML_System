# Stage 5A — V4 primary activation blocker resolution

**Status: PARTIAL, NOT READY FOR CONTROLLED ACTIVATION.** No MySQL migration or production activation was executed. V1/Stage14 remains the application's active primary model. The disposable schema prerequisite and a fully wired, tested V4 primary transaction path remain outstanding.

## Files changed

| File | Stage 5A change |
| --- | --- |
| `ml_v4/stage4sg/run_idempotency_migration.ps1` | New guarded **future** launcher for the already-reviewed disposable-only migration. |
| `v4_primary.py` | New isolated post-commit V4 decision coordinator; not yet called by Flask. |
| `server.py` | Customer route suppresses pre-commit transaction/alert/CTR/stats events and publishes committed rows afterward, with one stats event. Its V1 primary inference path remains active. |
| `tests/test_v4_shadow.py` | Updated extracted Flask route fixture and assertions for commit-before-notification and rollback silence. |
| `tests/test_stage5a_v4_primary.py` | New offline V4 decision, failure, alert, balance, duplicate and notification tests. |
| `ml_v4/stage4sa/harness.py` | Updated only its reviewed `server.py` source hash pin for the notification-order change. |
| `ml_v4/reports/STAGE5A_ACTIVATION_BLOCKERS.md` | This report. |

Frozen Stage3 inference, V4 model/features/threshold, `database.py`, production coordinator, and production MySQL were unchanged. Updating the Stage4S-A source pin does not retroactively revalidate earlier live evidence against this new `server.py` source; a new local review is required before fixtures.

## Database prerequisite and guarded command

The customer POST still calls `require_schema()` before accepting a payment. MySQL needs nullable ASCII/binary `transactions.client_request_id CHAR(36)` and unique index `uq_transactions_sender_request(sender_account, client_request_id)`. Both are absent in the user-reported Stage4S-I disposable preflight. The current request also states production lacks the index; production was not queried here. The route correctly returns 503 on a missing gate. The already-reviewed `ml_v4/stage4sg/mysql_migration.py` remains the **only** prepared DDL and was not run.

The saved backup `v4_stage4s_disposable-20261009-225015-3681550.sql` was reread for size and SHA-256 in this stage: **66,458 bytes**, **`b883ecb0fa7132106b5b1eeb91f26369e708e51ec54298b542251a9dd8e6c85c`**. The new launcher verifies that pinned backup's structure, securely prompts for the restricted test password, runs fresh read-only identity/grants/UUID/triggers/history/count/schema preflight, then invokes the reviewed migration with `--apply --expected-transactions 4` only if explicitly requested. It binds solely to `127.0.0.1:3306/v4_stage4s_disposable` as `v4_stage4t_runner`; it rejects ordinary database URLs and cleans credentials. MySQL DDL implicitly commits, so a failure after ALTER needs read-only investigation, never an automatic retry.

**Proposed future local command, not executed:**

```powershell
& .\ml_v4\stage4sg\run_idempotency_migration.ps1 -Apply
```

**Additional approval is needed** before running this irreversible disposable schema change. The earlier backup and preflight preparation did not authorize ALTER TABLE. This command never targets production `aml`. A separate production migration would require its own design, backup, approval and verification.

## Minimal V4 primary transaction lifecycle

The frozen production Stage3 interface reads a committed canonical event through an independent, read-only verified snapshot. It cannot see the customer's uncommitted insert on another connection. The safe lifecycle therefore has two commits:

1. Validate the request ID and atomic uniqueness gate. In one financial transaction, persist transaction/canonical event/history capture, perform balance changes and independent AML rule/CTR checks, and mark AI decision **pending_v4**. Commit before making any success notification.
2. Use the existing V4 worker/result contract on the committed canonical ID. It verifies history authority and prior-only features, and returns the frozen XGBoost prediction at 0.50. The prepared coordinator reuses the V4 result table's deduplication and does **not** call Stage13/Stage14 or a fallback model.
3. In a second database transaction, conditionally update a still-pending V4 row. A suspicious result creates an operational alert through the existing alert helper; a normal result remains normal only when independent rules do not require higher risk. Rule risk and CTR flags remain independent. The existing SAR-required flag can be set for review; this does **not** create or file a SAR report. An inference error becomes `ai_risk_level=inference_error` and `risk_level=pending_review` when no stronger rule risk exists, with no fabricated normal prediction.
4. Publish decision notifications only after the second commit. A duplicate completion cannot repeat the update or notification. If the decision commit fails, the payment remains committed and pending; no success event is sent. Recovery/retry of that explicit pending state still needs operational design and live verification.

`v4_primary.complete_committed()` implements and tests steps 2–4 behind an explicit caller-owned connection factory and optional worker test double. It refuses an uncommitted/missing canonical ID, a transaction not marked `pending_v4`, and simultaneous V4 shadow mode. **It is not wired into the Flask route.** Wiring only the customer route would leave the pending-transaction and four batch call sites using Stage14, violating the sole-primary requirement. The pre-commit rule/CTR baseline and all call sites must be changed and tested together after the disposable uniqueness schema is in place. No partial primary switch was enabled.

## Notification ordering

The customer route now calls `process_transaction_event(..., emit_events=False)`, commits the payment and balances, then emits transaction, alert, CTR and one statistics update from committed rows. A notification failure is logged after commit and does not roll back or retry the payment. The existing V4 shadow hook remains after commit. Offline extracted Flask tests observed one post-commit customer notification and none on rollback. **Other batch/pending call sites still use the existing default `emit_events=True`; system-wide rollback-safe notification ordering is not yet proven.**

## Offline verification

| Check | Actual result |
| --- | --- |
| New post-commit V4 decision tests | **9 passed**: committed visibility, normal/suspicious outputs, alert decision, explicit inference/malformed-result failure, rule alert preservation, unchanged balances/CTR flag, duplicate suppression, rollback silence, failed decision commit and shadow/primary mutual exclusion. |
| Existing V4 shadow and extracted Flask route tests | **39 passed**; V1 remains active in these route fixtures, with commit-before-notification assertions. |
| Stage4S-A harness, idempotency contract and frozen asset tests | **11 passed**. |
| Canonical mobile-money/history tests excluding two previously identified obsolete whole-tree hash assertions | **78 passed, 2 deselected**. |
| Python compilation and PowerShell parsing | **PASS**. |
| Frozen XGBoost SHA-256 | **PASS**: `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`. Frozen source still pins 40 semantic features, 42 estimator columns and threshold 0.50. |

These are **offline** tests with injected V4 result contracts. They do not prove that the new coordinator ran actual XGBoost inference in a Flask transaction, nor that the disposable MySQL schema, locks, alerts, dashboard, SAR/CTR workflows or authorization work with V4 primary. The earlier four live V4 shadow successes are not primary-model test results. No transaction fixture or MySQL write occurred in Stage 5A.

## Remaining blockers and controlled activation steps

1. Separately approve and run the pinned **disposable-only** idempotency migration; verify schema, existing rows, six triggers and history afterward. Production `aml` remains untouched.
2. Wire **all** transaction-processing entry points to one explicit V4-primary path with rule/CTR pre-commit baseline, pending AI state, durable post-commit completion/retry and no Stage14 inference. Keep any rollback to V1 as an explicit operator-controlled switch, never a silent inference fallback.
3. Move all remaining pre-commit batch/pending notifications after their commits. Verify staff dashboard/Socket.IO authorization and no ghost events.
4. Run approved isolated Flask/MySQL end-to-end tests using unique synthetic requests, the Stage4T test authority where applicable, real frozen inference and actual alert/SAR/CTR/balance checks. The production frozen Stage3 history gate is pinned to `aml`; the test binding must remain explicitly isolated and cannot be treated as production authority.
5. Review a separate production schema migration and activation plan. Do not enable V4 primary or shadow mode until those gates pass.

**STAGE 5A PARTIAL BLOCKER WORK COMPLETE — WAITING FOR APPROVAL.**
