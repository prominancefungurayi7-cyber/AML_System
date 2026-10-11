# MODEL V4 — STAGE 4S-A ISOLATED END-TO-END TEST HARNESS REPAIR

**A — TEST HARNESS READY FOR LOCAL LIVE CHECKS**

Stage4S identified two source-level blockers: Stage4R validated only production-scope successes, while Stage4T returned the separate disposable scope; importing `server.py` ran initialization, demo seeding and model-readiness startup. A separate Stage4S-A harness now resolves both without changing the production coordinator, ordinary application startup or frozen Stage3. This stage performed **no MySQL connection, financial fixture, model prediction, fit or V4 activation**. Live end-to-end testing still requires the local read-only checks below before any fixture submission.

## 1. Exact source changes

New test-only files:

| File | Purpose |
| --- | --- |
| [coordinator.py](../stage4sa/coordinator.py) | Fixed Stage4T worker invocation, test-scope validation, disposable-only result persistence and post-commit hook. |
| [harness.py](../stage4sa/harness.py) | Pinned-source Flask loader that skips only startup branches and dotenv calls in a private test process. |
| [live_readiness.py](../stage4sa/live_readiness.py) | Read-only model/source/schema/history and Flask route readiness check. |
| [run_local.ps1](../stage4sa/run_local.ps1) | Secure local password prompt and ordered read-only checks; stops before fixtures. |
| [test_harness.py](../stage4sa/tests/test_harness.py) | Offline scope, worker, failure and startup-isolation tests. |
| [verify_live.py](../evidence/stage4sa/verify_live.py) | Runs the unchanged Stage4U live verifier with new Stage4S-A evidence output and checks the trigger-creation setting is OFF. |
| `ml_v4/stage4sa/__init__.py` | Test package identity. |

This report and [decision evidence](../evidence/stage4sa/decision.json) are also new. No existing source or historical evidence file was edited. The approved Stage3 service, Stage4R coordinator, Stage4T binding/worker, model, extractor, preprocessing and original observation boundary remain unchanged.

## 2. Test-scope compatibility

`validate_test` requires exactly `stage4t-isolated-v1` for a success and permits only that scope or null for a technical error. It delegates all other declared-field, version, threshold, probability, prediction, timestamp and history checks to the unchanged Stage4R validator, substituting only its production scope **inside the check**, then returns the original test scope. Production and arbitrary scopes are rejected by the test validator; the production validator remains unchanged and still accepts only `controlled-prototype-v1` successes.

The test coordinator has a fixed worker path `ml_v4/test_binding/worker.py`, checks its approved SHA-256, and invokes it with only the committed transaction ID, canonical-row digest and server UUID. Its connection comes only from `v1.connection()`, which checks the disposable database, principal, grants and pinned authority. No HTTP parameter chooses a worker, database, model or scope. A named MySQL lock and the existing result-table key serialize duplicate processing; final success/error rows are reused. Timeout, malformed output, wrong server, worker/source failure and invalid probabilities yield a technical error with null prediction rather than normal. Post-commit shadow failure is logged without rethrowing into the already-committed transaction route. Results remain in `v4_shadow_results`; staff notification uses the existing role-checked shadow publisher. No V4 code writes operational risk, alert, SAR or CTR records.

This is a **new test deployment coordinator**, not byte-identical Stage4R production coordinator execution. It uses the unchanged frozen model through the separate Stage4T worker and the unchanged Stage2A verifier.

## 3. Flask startup isolation

The harness checks the exact current `server.py` hash, parses that source and compiles it in a private module after removing exactly three top-level `__name__` startup branches and two top-level `load_dotenv()` calls. Any source or structural change fails closed. All route and transaction-handler bodies remain from the pinned source. During this private load, database connector calls are forbidden, and Redis/Kafka settings are removed. No `initialize_startup`, `init_db`, `seed_demo_data`, `ensure_ai_model_ready`, background monitor or schema migration runs. The offline loader test successfully created the Flask app with no database connection.

After load, the test process pins `DATABASE_URL`, `MYSQL_URL`, Flask `DATABASE`, and every server connection call to the exact Stage4T URL and `v1.connection`. Conflicting ordinary database variables or `V4_SHADOW_ENABLED=ON` stop the loader. The test app cannot start a network listener; it is for `test_client` only. Its health response omits the credential-bearing URL. Before a `/customer/transaction` POST, a test-only request guard rechecks the authority, exact triggers and Stage2A freshness. The ordinary `server.py` startup path and production settings are unchanged.

This loads the full pinned Flask source in a private process, rather than claiming that a mocked handler body is the deployed WSGI application. Real transaction behavior still requires the later isolated MySQL fixture stage.

## 4. Offline verification

| Check | Result |
| --- | --- |
| Stage4S-A offline tests | **5 passed** |
| Existing Stage4R shadow tests | **25 passed** |
| Existing Stage4T adapter tests | **11 passed** |
| Python and PowerShell syntax | PASS |
| Named inherited protected paths | **524 hashes match** |
| Original Stage18 XGBoost hash | `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18` — PASS |
| Fresh MySQL identity/history/trigger check | NOT RUN: dedicated credentials absent here |
| Flask → MySQL financial fixtures or latency | NOT RUN: outside this repair stage |

The new tests cover test-scope acceptance, production/arbitrary-scope rejection, invalid/nonfinite prediction rejection, fixed worker selection, wrong-server rejection, worker integrity mismatch, timeout and malformed JSON handling, conflicting production URL rejection, startup-free app load, listener prohibition and post-commit failure containment. They use mocks and an offline password placeholder; they do **not** prove real MySQL transaction, inference, persistence, dashboard or latency behavior. Previous Stage3 model parity remains historical evidence and was not rerun as a new effectiveness evaluation.

## 5. Local read-only readiness command

From the workspace root in local PowerShell, with ordinary `DATABASE_URL` and `MYSQL_URL` unset:

```powershell
& .\ml_v4\stage4sa\run_local.ps1
```

The runner prompts securely for the dedicated `v4_stage4t_runner` password, sets only the fixed disposable URL and expected server UUID, then runs Stage4T `check`, the approved Stage4U live isolation/history verifier, and the Stage4S-A Flask/model/schema readiness check. The live verifier writes **new** `ml_v4/evidence/stage4sa/verification_live.json`; the final check writes `local_readiness.json`. It also checks `log_bin_trust_function_creators=OFF`, exact 16-table schema, six triggers, empty ledger/result table, genuine scope and fresh attestation. It prints or saves no password and stops at any failure. It installs no schema and submits no financial fixture.

No dedicated test credentials were available in this Codex process, so this command was **prepared but not run**. Retained Stage4U PASS evidence is not a substitute for its fresh live result.

## 6. Remaining gates and decision

After local readiness PASS and evidence review, a separately authorized fixture stage must use the test client against only `v4_stage4s_disposable` to exercise direct/assisted transfer and cash-in/out, actual V1/V4 separation, normal/positive/error outcomes, canonical and history commits, result persistence, staff GET/Socket.IO authorization, duplicates, rollback, recovery and measured latency. That stage must inspect real outputs; synthetic scenario names do not determine model predictions. Full end-to-end integration and controlled V4 activation are **not certified here**.

V1 remains operational. `V4_SHADOW_ENABLED` was not enabled. No production `aml` connection or write occurred; no sealed data was accessed. The frozen 40-feature/42-column model and threshold 0.50 remain intact.

**A — TEST HARNESS READY FOR LOCAL LIVE CHECKS**

STAGE 4S-A COMPLETE — WAITING FOR APPROVAL.
