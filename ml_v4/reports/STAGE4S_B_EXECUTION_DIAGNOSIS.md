# Stage 4S-B live execution diagnosis

**Decision: B — partial pass; fixes and remaining tests required. Do not activate V4.**

## What the saved run proves

`ml_v4/evidence/stage4sb/live_e2e.json` has `status: EXECUTED` for the pinned disposable database and server UUID. It records four HTTP **302** responses, transaction IDs **1–4**, exactly one canonical event per ID, `COMPLETE_VERIFIED` ledger and result history, and a stored `success` shadow body per ID. The runner fetched those records on a separate verified MySQL connection after each Flask POST. This is strong evidence that all four transaction and canonical rows committed and that capture/history processing succeeded. The worker itself checks for both `SOURCE_INSERT` and `CANONICAL_INSERT` capture operations before returning a success. The evidence does not include a fresh independent row count or raw trigger journal; use the read-only check below for that.

| Flask case | ID | HTTP | Stored V4 status | V4 prediction | V4 probability | Total request + inference ms |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| Wallet transfer | 1 | 302 | success | 0 | 0.0035925768315792084 | 5646.61 |
| Agent transfer | 2 | 302 | success | 0 | 0.005726395174860954 | 4509.37 |
| Cash-in | 3 | 302 | success | 0 | 0.008130382746458054 | 4575.44 |
| Cash-out | 4 | 302 | success | 0 | 0.037156715989112854 | 4375.36 |

All four stored results report `stage4t-isolated-v1` and `COMPLETE_VERIFIED`. These are V4 shadow fields, independent of Stage 14's 0.35 threshold. The runner measured whole Flask request time, including validation, V1 processing, commit, V4 worker and response work; it did **not** separately time XGBoost inference.

The unchanged Flask route commits before calling `v4_shadow.after_commit`. The test harness assigns that hook to `ml_v4.stage4sa.coordinator.after_commit`, which uses the fixed Stage4T worker. That worker verifies the canonical source and history, then calls `v1.infer`, whose frozen `FrozenModel.predict` supplies a 0.50-threshold result. The four recorded shadow successes with V4 scope therefore support that this test-only post-commit hook and frozen V4 inference ran. The JSON does not contain a subprocess trace or full stored contract, so the read-only diagnostic checks the current database bodies and model hash before treating them as independently verified. Stage 14 log messages alone are not evidence of V4 execution.

## Stage 13 error and V1 impact

The Stage 13 error is in the **legacy V1/Stage 14 path**, which runs inside `process_transaction_event` before the transaction commit. `ai_stage14_model.get_stage14_model_service` is a process-wide singleton. On the first request it retains a Stage 13 feature service bound to that request's MySQL connection. Flask closes the request connection during teardown. Later requests construct a new connection, but the singleton continues using the first, closed connection; its feature query raises `MySQL Connection not available`. Stage 13 catches that exception and returns thirty zero features. Stage 14 can still log a GradientBoostingClassifier prediction at threshold 0.35, but those predictions may be based on fallback features and are not reliable evidence of healthy V1 feature processing. Rules and other V1 work still ran sufficiently for the Flask requests to commit; exact per-row legacy decision quality was not captured. This failure does not explain or invalidate the separate Stage4T V4 worker results, which use independent verified connections and the frozen XGBoost model.

The smallest safe correction is to rebind the Stage 14 singleton's Stage 13 feature service to each live request connection, or remove the singleton's connection-bearing state. Add a focused multi-request test that verifies real Stage 13 history features after the first Flask teardown. This diagnosis makes **no** source change to V1 or frozen V4.

## Fresh read-only verification

Credentials are unavailable in this Codex process. **LOCAL EXECUTION REQUIRED** for a fresh database check. From the workspace root run:

```powershell
& .\ml_v4\stage4sa\diagnose_live.ps1
```

The command prompts for the restricted account and checks the pinned binding, principal, grants, UUID, six triggers and authority. It only selects transaction IDs 1–4, their canonical rows, capture operations, shadow bodies and table counts, and validates the V4 result contract. It performs no fixture submission, migration, reset or production connection. Its output may be retained as new evidence; it prints no password.

### Diagnostic launcher repair

The first `diagnose_live.ps1` version launched `diagnose_live.py` by file path under Python `-I`. That isolated launch omitted the project root from module lookup, causing `ModuleNotFoundError: No module named 'ml_v4'`. The launcher now changes to the project root and runs `python -B -m ml_v4.stage4sa.diagnose_live`. The separate Stage4T binding check remains unchanged. The secure password prompt, pinned disposable URL, restricted principal, expected server UUID, authority verification and credential cleanup remain in place. `diagnose_live.py` and all binding security checks were unchanged.

An uncredentialed direct module launch now reaches `BindingError`, rather than an import error. That is the expected fail-closed behavior without the dedicated URL and authority environment set by the PowerShell runner. Two offline launcher regression tests passed, and PowerShell parsing passed. These checks prove the module launch works; they do **not** substitute for the fresh read-only MySQL inspection above.

## Remaining gates

The saved run does not prove duplicate handling, rollback, injected V4 failures, timeout, malformed worker output, stale authority, staff dashboard or Socket.IO authorization, or absence of production alert/SAR/CTR effects. There is no separate inference-only latency measure. Those tests remain blocked pending a safe test plan and local disposable database access. No financial fixture was rerun for this diagnosis; production `aml`, the V4 model, features, threshold and frozen inference were untouched.

**STAGE 4S-B EXECUTION REVIEW COMPLETE — WAITING FOR APPROVAL.**
