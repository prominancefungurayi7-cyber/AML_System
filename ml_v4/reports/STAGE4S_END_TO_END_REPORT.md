# MODEL V4 — STAGE 4S END-TO-END INTEGRATION TESTING

**C — BLOCKED; DO NOT ACTIVATE V4**

No financial fixtures or full Flask → MySQL → V4 tests were run. The saved disposable-database recovery evidence reports PASS, but this Codex process has no dedicated test connection variables or password for the required fresh identity, grant, trigger and history checks. A separate source review also found that the existing Stage4R coordinator rejects a successful Stage4T test-worker result because the two use different observation scopes. The required safe test binding is therefore not established.

## 1. Environment and readiness evidence

The retained [recovery result](../evidence/mysql_test_recovery/recovery_result.json) and [live verification](../evidence/stage4u_continue/verification_live.json) report database `v4_stage4s_disposable`, principal `v4_stage4t_runner@127.0.0.1`, server UUID `d441b7bb-43f6-11f1-a2d8-0a0027000005`, MySQL 8.0.46, 16 tables including `v4_shadow_results`, six verified capture triggers, zero financial/result rows, and a genuine empty-ledger scope with COMPLETE_VERIFIED attestation. The local test authority file exists and its SHA-256 matches both saved records: `b200fe8004a96fc0748409a238276a8a72badcf85a88ac38b0f59917927324d5`. These are retained observations, not a fresh database check.

At this stage, neither `V4_STAGE4T_TEST_DB_URL` nor `V4_STAGE4T_EXPECTED_SERVER_UUID` is available in the Codex process. No test-account connection was attempted. Consequently, current database identity, scoped grants, trigger definitions, source revision, attestation freshness, and row counts are **NOT VERIFIED NOW**. `log_bin_trust_function_creators` being restored OFF is reported by the user; it was not independently queried. No connection to `aml` was made.

The frozen original Stage18 XGBoost hash remains `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`. Offline inherited protection checks cover 524 named paths. The model contract remains 40 semantic features, 42 estimator inputs and inclusive threshold 0.50. No model or extractor was loaded, fitted, tuned or changed in this stage.

## 2. Application boundary finding

The ordinary Flask [customer route](../../server.py) commits the parent and canonical event, then calls `v4_shadow.after_commit`. That hook is off unless `V4_SHADOW_ENABLED=ON`. Its [coordinator](../../v4_shadow.py) invokes the fixed Stage4R production worker by default. The [Stage4T test worker](../test_binding/worker.py) is separate and cannot be selected through an HTTP request, which protects the production binding.

Stage4T `v1.infer` returns a successful result with `observation_scope='stage4t-isolated-v1'`. Stage4R `v4_shadow.validate` requires successful results to have `observation_scope='controlled-prototype-v1'`. Thus a test worker success cannot pass the current coordinator's result validator. Simply changing the worker path or setting the normal shadow flag would not provide a valid test. A separately versioned, explicitly local test coordinator or validator must preserve the test scope and still reject arbitrary scopes, while keeping the production validator unchanged. Its connection factory and worker selection must be fixed by the test harness, not by a request parameter.

Importing the ordinary `server.py` also runs startup initialization, demo seeding and legacy model readiness. The previous Stage4R acceptance used extracted Flask handler bodies against SQLite and a stubbed legacy model; it expressly did not certify the complete Flask/MySQL/model path. A safe test import/startup strategy must be demonstrated before using the disposable database. These observations are source review, not executed transaction tests.

## 3. Executed tests and transaction results

| Item | Result |
| --- | --- |
| Saved recovery and authority hashes | PASS, read-only comparison |
| Frozen model and inherited source integrity | PASS, read-only hash checks |
| Fresh disposable MySQL identity/grants/history | NOT RUN; test credentials unavailable here |
| Direct wallet transfer | NOT RUN |
| Agent-assisted wallet transfer | NOT RUN |
| Cash-in / cash-out | NOT RUN |
| Canonical event and post-commit history verification | NOT RUN |
| Real V4 predictions and shadow-result persistence | NOT RUN |
| Normal/positive/error/timeout/duplicate/rollback cases | NOT RUN |
| Compliance GET, Socket.IO authorization and dashboard | NOT RUN |
| Transaction and inference latency | NOT MEASURED |

No actual predictions, transaction IDs, probabilities or response times exist for this stage. Previous Stage3 and Stage4R unit results remain historical evidence, not a substitute for this requested end-to-end test. V1 remains the application operational path; this turn performed no V1 or V4 application transaction and created no operational alert.

## 4. Required next work

1. In a local process with the dedicated test credentials, rerun the approved Stage4T `check` and Stage4U `live_checks.py verify` against the actual disposable server. Confirm current grants, all six trigger bodies, fresh attestation, empty fixture ledger and test-only authority before any fixture write. Do not use `aml` credentials.
2. Implement and review an isolated application harness that suppresses ordinary startup side effects, fixes its connection factory to the disposable database and selects the Stage4T worker internally. Add a test-scope result validator that retains all other frozen result checks; leave the production Stage4R validator and Stage3 source unchanged.
3. Then run synthetic direct/assisted transfer and cash-in/out routes, post-commit canonical/history/inference/persistence checks, failure and duplicate cases, staff-only GET/Socket.IO checks and latency measurements. Review source and result rows after each case. Do not infer labels from the synthetic scenarios.

The requested decision A requires those live results. No claim of safe V4 shadow activation can be made from saved empty-ledger evidence or static code review alone.

## 5. Preservation and decision

Files created in this stage: this report and [offline decision evidence](../evidence/stage4s_end_to_end/decision.json). No existing source, migration, database, authority, frozen artifact or historical report was modified. No sealed Final Test or Independent Evaluation data was accessed. `V4_SHADOW_ENABLED` was not enabled, V1 was not replaced, and no V4 operational alert was activated.

**C — BLOCKED; DO NOT ACTIVATE V4**

STAGE 4S COMPLETE — WAITING FOR APPROVAL.
