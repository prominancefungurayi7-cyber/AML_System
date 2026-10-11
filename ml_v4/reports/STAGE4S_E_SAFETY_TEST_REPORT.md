# Stage 4S-E V4 integration safety test report

**Decision: offline safety controls partially verified. Do not activate V4 or replace V1.**

## Files changed

| File | Change |
| --- | --- |
| `tests/test_v4_shadow.py` | Added duplicate HTTP POST, post-commit V4 failure isolation, and shadow-disabled tests. |
| `ml_v4/stage4sa/tests/test_harness.py` | Added missing-authority rejection before worker launch. |
| `ml_v4/reports/STAGE4S_E_SAFETY_TEST_REPORT.md` | This report. |

No application, model, feature, threshold, frozen Stage3, Stage4R, Stage4T, database, or sealed dataset file was modified. All tests used local SQLite fixtures, mocks, or source inspection; no MySQL connection or financial fixture submission occurred.

## Controls inspected and tested

| Area | Existing control and offline result |
| --- | --- |
| Duplicate shadow processing | Stage4R uses a per-transaction MySQL lock and a unique `(transaction_id, model_version, feature_version)` key. Final results are reused; pending rows can resume. Existing SQLite/restart and simulated MySQL lock tests passed. Stage4S-A uses a separate named lock and the same result key. |
| Duplicate customer request | **Missing request idempotency protection.** A new test posts the same form twice through the extracted Flask handler and observes two committed transaction IDs and two shadow results. The shadow deduplicator only handles repeat processing of *one* transaction ID. |
| Source rollback | Existing test forces rollback before the commit and observes no transaction or shadow row and no post-commit hook. |
| V4 failure after source commit | New test injects a shadow processing exception. The customer request still completes, the committed V1 risk fields remain `(55, 12, 0.8)` in the isolated stub, the canonical row remains, and V4 creates no operational alert, SAR or CTR row. The production `after_commit` catches exceptions; Stage4S-A does likewise. This demonstrates the boundary with a V1 stub, not the full live V1 pipeline. |
| Worker exception, timeout, malformed output | Stage4R `invoke` converts process exit, timeout, oversized output, malformed JSON, duplicate keys and nonfinite values to technical errors with null predictions. Stage4S-A fixed-worker tests cover timeout, malformed output, wrong server and worker hash mismatch. All targeted tests passed. |
| Invalid or stale authority | Stage4T binding checks disposable DB, principal, grants, six trigger bodies and pinned boundary. The worker checks source digest/capture records and refreshes history before inference. New test confirms missing authority prevents Stage4S-A worker launch and returns a technical error. Offline tests do not establish a live stale-history race outcome. |
| V1/V4 decision separation | The Flask handler commits V1 risk decisions before calling the V4 hook. Stage4R writes only `v4_shadow_results`; the new exception test preserves V1 fields. Production V4 shadow mode remains OFF, and a new test confirms no processing when disabled. |
| Alert, SAR and CTR isolation | The V4 coordinator has no writes to operational alert or report tables. New failure test includes those tables and observes zero V4-created rows. Full V1 alert/report behavior was stubbed and remains a live integration check. |
| Staff dashboard/API | `/api/v4-shadow/results` checks the current DB role for `compliance` or `admin`; customer access returns 403 in the existing Flask test. Responses use a restricted safe payload. |
| Socket.IO | Subscription checks the current DB staff role; publication rechecks it and removes demoted users. Existing Socket.IO test confirms a customer receives no V4 event and a demoted staff member stops receiving events. The socket registry is process-local, so multi-process delivery is not certified by these tests. |

## Tests executed

| Command | Result |
| --- | --- |
| `python -m pytest -q tests/test_v4_shadow.py` | **28 passed, 0 failed** |
| `python -m pytest -q ml_v4/stage4sa/tests/test_harness.py ml_v4/test_binding/tests/test_v1.py` | **17 passed, 0 failed** |

The first suite includes the current Flask transaction handler exercised with an isolated V1 stub and SQLite fixtures. It does not certify actual MySQL commit behavior. The tests do not infer V4 safety from predictions or scenario labels.

## Remaining live requirements

**A — Verified offline:** single-ID shadow deduplication, pre-commit rollback boundary, post-commit exception containment with a V1 stub, technical-error conversion, binding rejection, disabled mode, staff GET authorization and process-local Socket.IO role checks.

**B — Requires read-only disposable MySQL access:** independently inspect current four transaction/canonical/history/shadow rows, V1 risk fields, alert/SAR/CTR counts, trigger/authority freshness, current staff role behavior, and stored-result visibility. Read-only checks cannot simulate a new source rollback or worker failure after a new commit.

**C — Requires newly approved disposable fixtures:** full MySQL transaction-handler rollback, duplicate client requests, V4 worker failure/timeout/malformed result after a new commit, stale-history races, and confirmation that real V1 decisions and operational reports remain correct. No new transaction is authorized or submitted in this stage.

## Recommendation

Resolve or explicitly document the missing customer-request idempotency guarantee before treating repeated submissions as safe. Next, review the read-only MySQL evidence and plan separately approved disposable fixtures for the remaining full-path failure cases. Keep V4 production shadow mode OFF until those gates are reviewed.

**STAGE 4S-E COMPLETE — WAITING FOR APPROVAL.**
