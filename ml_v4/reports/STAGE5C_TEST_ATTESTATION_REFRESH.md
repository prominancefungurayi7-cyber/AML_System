# Stage 5C verified test-history attestation refresh

**Prepared, not executed.** The only proposed MySQL write is one Stage4T test-history attestation on `v4_stage4s_disposable`. No financial fixture, model operation, migration or production `aml` access occurred in this Codex process.

## Reviewed database state

The latest saved read-only inspection, `ml_v4/evidence/stage5c/interrupted_review.json`, reports the pinned server UUID `d441b7bb-43f6-11f1-a2d8-0a0027000005` and restricted principal `v4_stage4t_runner@127.0.0.1`. It has **8 transactions, 8 canonical events, 16 capture records and 8 stored V4 results**; one alert, no SAR/CTR reports. Its current graph is `COMPLETE_VERIFIED` with **zero issues**, but freshness is `UNKNOWN` because current source revision `003c0400c9bfe5c22ff3de2406c30d8bfc166d8236a8648daa20d0c838901be4` differs from attestation sequence 8's revision `7a85163c5703ddb4dd8f95b500c22d6ca6382df05a2121a6a0bb5b3cf616b6e5`. Transaction 8 has one canonical event, ordered `SOURCE_INSERT` and `CANONICAL_INSERT` records, a terminal `inference_error` V4 result and no fabricated prediction. Both Stage5C fixture groups' wallet balances reconcile in that inspection.

## One-time command and guards

From the project root, **only when ready to perform the approved disposable authority write**, run:

```powershell
& .\ml_v4\stage5c\run_refresh_test_attestation.ps1 -Apply
```

The PowerShell runner requires `-Apply`, rejects inherited database/model URLs and production shadow mode, prompts securely for only the restricted disposable password, pins `127.0.0.1:3306/v4_stage4s_disposable` and the exact server UUID, and clears password material and environment bindings afterward. It does not retry automatically.

The Python command rejects an existing output file, a changed saved-review fingerprint, any change to counts, scope, source revisions, attestation sequence or transaction-8 error state, missing/mismatched triggers, grants or principal, and a changed frozen model hash. Under the existing `cmm_history_admin_v1` lock it opens one consistent MySQL snapshot, reassesses all eight events and sixteen capture rows, requires `COMPLETE_VERIFIED` with zero issues and `UNKNOWN` freshness caused by exactly the pinned revision mismatch, then calls the existing `canonical_history_store.attest()` once. Before committing, it confirms that all financial, user, canonical, capture, V4-result, alert and scope row digests are unchanged and that only one attestation plus its required entity-history rows were added. It rolls back on any pre-commit mismatch.

After commit, a separate verified read-only connection must show `COMPLETE_VERIFIED` freshness, attestation sequence **9**, unchanged source revision and unchanged protected row digests. Success evidence is written to `ml_v4/evidence/stage5c/history_attestation_refresh.json`. A post-commit verification failure requires manual read-only inspection; it never triggers an automatic second attestation. Transaction 8 remains `inference_error`.

## Files changed

| File | Purpose |
| --- | --- |
| `ml_v4/stage5c/refresh_test_attestation.py` | Pinned one-time assessment, attestation and post-commit verification. |
| `ml_v4/stage5c/run_refresh_test_attestation.ps1` | Secure local password prompt and disposable-only launcher. |
| `tests/test_stage5c_attestation_refresh.py` | Offline guards for count/revision drift, transaction-8 state and missing authorization binding. |
| `ml_v4/test_binding/worker.py` | Stage5C-only simulated inference error now occurs after the normal verified attestation commits. |
| `ml_v4/stage5c/live_primary.py` | Uses the short-lived worker fault flag instead of bypassing the worker; verifies fresh history immediately after the injected failure, before any retry. |
| `ml_v4/stage5c/run_live_primary.ps1` | Rejects an inherited fault flag and clears it on exit. |
| `ml_v4/stage4sa/coordinator.py` | Refreshes the test worker source hash pin for the reviewed test-only change. |
| `ml_v4/stage4sa/tests/test_harness.py` | Restores the current worker hash dynamically after its deliberate integrity-failure test. |
| `tests/test_stage5c_post_attest_failure.py` | Checks that attestation commits before the simulated inference error and normal inference remains unaffected. |
| `ml_v4/reports/STAGE5C_TEST_ATTESTATION_REFRESH.md` | This report. |

Frozen V4 files, all 40 semantic features, threshold 0.50, `database.py`, transactions, balances and prior V4 results were not changed here. The model artifact's SHA-256 remains `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`.

## Offline tests

| Suite | Result |
| --- | --- |
| New refresh guards plus history-staleness tests | **5 passed** |
| Canonical-history, harness and refresh tests excluding the documented historical Stage14 whole-tree hash assertion | **40 passed, 1 deselected** |
| Same suite without deselection | **40 passed, 1 failed** on the previously documented Stage14 historical source hash, not on V4 or attestation logic |
| Stage5C CTR and launcher guards | **8 passed** |
| Python compilation and PowerShell parsing | **passed** |
| Focused refresh, Stage5C failure, live guards, CTR compatibility and Stage4S-A harness tests after the worker correction | **22 passed** |

The saved Stage4T decision evidence and historical finalize script still pin the original test worker bytes; they were not rewritten. The current coordinator pins the reviewed test worker change. This does not alter frozen V4 inference or production authority. The new simulated error still leaves its payment committed and decision explicit, but the worker attests the committed graph before returning the error. The Stage5C runner immediately requires fresh history before attempting a same-key retry.

**Expected post-repair state:** current history and latest attestation both `COMPLETE_VERIFIED`, sequence 9, unchanged source revision, eight committed transactions and transaction 8 still explicitly `inference_error`. **LOCAL EXECUTION REQUIRED; stop after reporting.**

## Execution environment pinning repair

The first local `-Apply` attempt stopped with `Isolated execution environment not pinned`. The refresh launcher correctly supplied `STAGE5C_ATTEST_EXECUTE=YES`, the dedicated disposable URL and pinned UUID, while keeping `AML_PRIMARY_MODEL` unset. `refresh_test_attestation.run()` then called `inspect_prior()`. That read-only function called the transaction-test `preflight()`, which requires `STAGE5C_EXECUTE=YES` and `AML_PRIMARY_MODEL=V4`; these are fixture-execution bindings and are deliberately absent from the attestation launcher. This was the exact mismatch.

`ml_v4/stage5c/live_primary.py` now accepts an explicit **read-only attestation review** mode only when `STAGE5C_ATTEST_EXECUTE=YES`, `STAGE5C_EXECUTE` and `AML_PRIMARY_MODEL` are absent, and stale inspection was requested. All existing disposable URL, host/port, UUID, authority, principal/grant, trigger, boundary, model/worker integrity, schema and history checks remain in `preflight()`. Ordinary fixture execution retains its prior binding. `ml_v4/stage5c/refresh_test_attestation.py` requests this review mode for its fresh prewrite reconciliation. The PowerShell launcher and its password handling did not change.

The exception arose at the beginning of `preflight()`, before it could open a database connection. The refresh tool had not reached its history lock, `attest()` call or commit. The local refresh-success evidence file is absent. This establishes that the failed command path performed no attestation write; it does **not** substitute for a fresh independent database read. The saved `interrupted_review.json` predates that failed attempt, and this Codex process has no restricted credential. For fresh read-only confirmation locally, run `& .\ml_v4\stage5c\run_live_primary.ps1 -InspectOnly` and inspect the resulting counts, source revision and attestation sequence. Its stale-history exit is expected until the repair succeeds; do not start fixtures. The repair command remains:

```powershell
& .\ml_v4\stage5c\run_refresh_test_attestation.ps1 -Apply
```

Focused regression tests cover the dedicated read-only binding, rejection of fixture bindings or the wrong UUID, and the refresh tool reaching read-only reconciliation without calling `attest()` during the test. **21 offline tests passed**, Python compilation passed and the PowerShell runner parsed with zero errors. No repair or financial transaction was executed in this Codex process.
