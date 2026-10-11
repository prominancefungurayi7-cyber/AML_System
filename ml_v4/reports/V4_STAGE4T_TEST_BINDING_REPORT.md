# MODEL V4 — STAGE 4T ISOLATED MYSQL TEST BINDING REPAIR

**B — ADAPTER IMPLEMENTED; ADMINISTRATOR PROVISIONING REQUIRED**

Stage4T adds a versioned adapter for a disposable MySQL test database. It uses the unchanged Stage3 frozen model operations and Stage2A history verifier with a separately established test observation authority. The ordinary Flask application and Stage4R worker do not select it. **No test database or credentials were provisioned here**, so no MySQL isolation claim or Stage4S end-to-end PASS is made.

## Root cause and exact changes

The approved Stage3 connector accepts only `/aml` and connects to database `aml`. Its history gate requires `SELECT DATABASE()='aml'` and compares the scope with original Stage2A2 evidence. The Stage4R child imports that connector and checks the same boundary. A disposable schema cannot pass those deployment checks.

New files are [test adapter](../test_binding/v1.py), [test worker](../test_binding/worker.py), [usage instructions](../test_binding/README.md), [unit checks](../test_binding/tests/test_v1.py), this report and `ml_v4/evidence/stage4t/`. A local `.gitignore` excludes the generated test authority record. No approved Stage3, Stage2A, Stage17, Stage18 or application source was edited.

The adapter does **not** call Stage3 `infer`, whose import is bound to the approved production history gate. It calls the unchanged Stage3 `FrozenModel` constructor, exact 40-field replay, embedded preprocessing and XGBoost prediction methods, plus the unchanged `probability_decision` threshold function. Its separate history gate uses the unchanged Stage2A `assess`, `attest`, `snapshot` and `freshness` functions, along with the exact existing trigger definitions. This relationship is versioned as `v4.test_binding.stage4t.1`; it is not described as byte-identical Stage3 service execution.

## Isolation and observation authority

The adapter accepts only `V4_STAGE4T_TEST_DB_URL` naming `v4_stage4s_disposable` with principal `v4_stage4t_runner`. It never falls back to the application's `.env`, `DATABASE_URL` or `MYSQL_URL`. Before caller SQL or a setup write, it checks the actual `SELECT DATABASE()`, `@@server_uuid`, `CURRENT_USER()` and `SHOW GRANTS`. Global privileges beyond USAGE, grants on another schema and GRANT OPTION are rejected. The expected server UUID must be supplied for setup and then pinned in the local authority record. The URL password is neither logged nor stored in that record.

`prepare` is a local explicit command. It requires a reviewed application schema, no preexisting V4/capture/history tables and an empty transaction table. Only after the identity/grant checks does it create the canonical, history, capture and result schema with the existing migration functions. It establishes a new boundary through Stage2A `create_scope` in the **test** database, attests the empty ledger using Stage2A `attest`, requires the calculated COMPLETE_VERIFIED outcome, and records the immutable boundary digest. There is no desired-status argument, copied production boundary, reset or automatic recovery path.

Every test inference rechecks the real database identity and grants, all six capture triggers and bodies, the pinned boundary and one-scope membership. It opens a consistent read-only snapshot, calls unchanged Stage2A assessment/freshness, requires COMPLETE_VERIFIED with no issues and includes all scoped graph events. The test worker additionally checks the parent supplied server UUID and committed canonical row digest, both insert journal operations, and performs a fresh post-commit technical attestation under the history lock. A later change must pass a second fresh snapshot check. An absent or incomplete authority produces an inference error with NULL prediction/probability before model loading.

This is a test deployment authority stored locally as `.stage4t_authority.json`; it is not an independent custody certificate. A user with write access to both the database and authority file remains a trusted test administrator. The production Stage3 binder still accepts only its approved `/aml` path and historical authority; the new binder rejects `aml`. The ordinary application has no import or request option selecting the test binder.

## Administrator handoff

No `V4_STAGE4T_TEST_DB_URL` or `V4_STAGE4T_EXPECTED_SERVER_UUID` variable was present. No test account, target database or approved schema-only provision was established in this workspace. **An administrator must perform these steps on the chosen test MySQL server; they must not use the existing `aml` database or its account.**

1. Record the actual `SELECT @@server_uuid` from the chosen server through an administrator session. Confirm that the target schema does not exist and that the host/account below are test-specific. Replace the account host only with the actual test runner host.
2. Execute the following on that server with a generated unique secret. Keep the secret outside repository files, reports and command output:

   ```sql
   CREATE DATABASE v4_stage4s_disposable CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'v4_stage4t_runner'@'127.0.0.1' IDENTIFIED BY '<generated-test-secret>';
   GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, TRIGGER, REFERENCES
     ON v4_stage4s_disposable.* TO 'v4_stage4t_runner'@'127.0.0.1';
   SHOW GRANTS FOR 'v4_stage4t_runner'@'127.0.0.1';
   ```

3. Provision the **current application schema only**, with no copied accounts, transactions or production records, in this database. The required empty `users`, `agents` and `transactions` tables must match the current application route; `transactions.id` must be signed BIGINT; its timestamp must preserve canonical six-digit UTC text in VARCHAR(40) or VARCHAR(255); and sender, receiver, amount, type, currency, agent, and status fields must exist. Other application tables used by the route must be included. Do not run the ordinary Flask startup merely to create schema: it seeds demo users and reaches legacy model readiness. The administrator should supply the reviewed schema-only migration output and its hash to the Stage4S test operator. Stage4T intentionally does not invent or copy a production schema.
4. Set `V4_STAGE4T_TEST_DB_URL` to the scoped user's MySQL URL for `v4_stage4s_disposable` and `V4_STAGE4T_EXPECTED_SERVER_UUID` to the recorded server UUID in the isolated test process only. Run the local `prepare` command in [usage instructions](../test_binding/README.md). Confirm `check` succeeds and capture the generated authority record hash. No financial fixture may be submitted until this succeeds and the application test harness is explicitly bound to the test worker.

The exact SQL grants remain within the disposable schema. The adapter rejects a globally privileged or production database account even if its username matches. Administrator provisioning is the remaining external step; Stage4S also needs to verify the reviewed application schema and bind its isolated application test harness to the test worker. The normal application cannot enable the adapter through `V4_SHADOW_ENABLED` or an HTTP request.

## Verification

| Check | Result |
| --- | --- |
| Test binder rejects `aml`, wrong account, malformed URL | PASS, offline tests |
| Unchanged production connector rejects disposable schema | PASS, actual parsed guard, no connection |
| Wrong server/database/principal/grants | PASS, connection identity unit checks |
| Wrong or absent pinned boundary | PASS, unit checks |
| Missing capture trigger | PASS, unit check |
| Missing authority stops inference/child before model | PASS, unit checks |
| Exact trigger bodies, fresh/stale history, concurrent source change on actual MySQL | NOT RUN; provisioning required |
| Production authority on actual `aml` | Preserved named hashes and original Stage3 regression; no new production DB connection |
| Original Stage3 test workflow | 54 passed using two previously authorized Stage4R application hash exceptions supplied in memory; test source/history unchanged |
| Original saved 128-example parity | New parity JSON equals original |
| Frozen preservation | 524 named protected paths match Stage4S expectations; all 12 recovered files exact |
| Disposable MySQL isolation/grants and boundary | NOT VERIFIED live; no connection or writes |

Evidence: [adapter tests](../evidence/stage4t/binding_tests.txt), [Stage3 regression](../evidence/stage4t/stage3_tests.txt), [saved parity](../evidence/stage4t/stage3_parity.json), [preservation runner](../evidence/stage4t/run_checks.py). The initial direct Stage3 test invocation returned 53 passed and one historical application hash assertion failure; the later unchanged 54-test workflow passed with only those two declared in-memory exceptions. No historical evidence file was overwritten.

## Frozen preservation and decision

The original Stage18 XGBoost SHA-256 remains `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`. Feature version `v4.features.1` remains 40 semantic fields, 42 encoded columns, threshold 0.50. No fitting, tuning, calibration, generation, operational V4 alert, V1 replacement, `V4_SHADOW_ENABLED` change or sealed evaluation access occurred. Existing V1/V3/V4 research artifacts and historical reports are unchanged. [Decision and new artifact hashes](../evidence/stage4t/decision.json) record the exact new output scope.

**B — ADAPTER IMPLEMENTED; ADMINISTRATOR PROVISIONING REQUIRED**

Stage4S may resume only after the disposable MySQL database, restricted test account, reviewed application schema and genuine test boundary are verified. Full MySQL history failure cases and application workflow remain outstanding; they are not inferred from offline tests. No ordinary application activation follows this report.

STAGE 4T COMPLETE — WAITING FOR APPROVAL.
