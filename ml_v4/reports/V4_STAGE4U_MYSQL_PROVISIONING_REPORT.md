# MODEL V4 — STAGE 4U DISPOSABLE MYSQL PROVISIONING AND TEST AUTHORITY

**B — ADMINISTRATOR ACTION REQUIRED**

The disposable database and restricted account could not be provisioned in this session. A local MySQL80 service is running, but no `V4_STAGE4T_TEST_DB_URL`, expected test server UUID, test authority record or administrator connection was available through the checked configuration. This does not establish that no administrator account exists elsewhere. **No MySQL connection or write was attempted.** No financial fixtures were submitted, and V4 remains disabled.

Stage4U produced a schema-only installation and a guarded installer so an administrator can provision the isolated environment without application startup or copied financial data. One verified Stage4T adapter command defect was corrected in `ml_v4/test_binding/v1.py`. The test worker and approved Stage3 source remain untouched.

## 1. Preflight and frozen preservation

Read-only review covered the [Stage4T adapter](../test_binding/v1.py), [test worker](../test_binding/worker.py), [Stage4T report](V4_STAGE4T_TEST_BINDING_REPORT.md), [database DDL](../../database.py), effective [server transaction route](../../server.py), Stage2A capture/history code, Stage4R shadow coordinator and compliance panel. The connector uses a dedicated test URL, real database/server/principal checks and `SHOW GRANTS`; the worker compares the parent supplied server UUID and canonical row hash, requires both insert journal records, reassesses history and opens a fresh inference snapshot.

The Stage4T preserved 524 named paths and all twelve recovered Stage3 files were checked against their recorded hashes. The original Stage18 XGBoost hash remains `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`. Forty semantic features, 42 estimator columns and threshold 0.50 remain unchanged. No model was loaded or fitted. The sealed Final Test and Independent Evaluation were not accessed.

## 2. Actual database identity and credential status

| Item | Stage4U observation |
| --- | --- |
| Local MySQL service | `MySQL80` running; service status only |
| `V4_STAGE4T_TEST_DB_URL` | Absent from process environment |
| `V4_STAGE4T_EXPECTED_SERVER_UUID` | Absent from process environment |
| Administrator URL | Absent from process environment |
| Local `.stage4t_authority.json` | Absent |
| Actual `SELECT DATABASE()`, `@@server_uuid`, `CURRENT_USER()`, `SHOW GRANTS` | NOT RUN; no eligible connection |
| Test database/account existence | NOT VERIFIED |
| Existing `aml` database | Not connected, queried, reset or modified |

The presence of a running MySQL service does not prove the disposable schema or restricted grants exist. No production `.env` credential or ordinary application database setting was used to fill the missing test authority.

## 3. Schema-only installation

Created [application_schema_only.sql](../evidence/stage4u/application_schema_only.sql) from the current `database.get_schema_sql()` and statically extracted `server._migrate_mysql` column definitions. The [builder](../evidence/stage4u/build_schema.py) imports the database DDL module but never imports the server or starts Flask. The [schema review](../evidence/stage4u/schema_review.json) binds source hashes, SQL hash, ordered tables, migration additions and indexes.

The SQL contains ten empty application tables. `users` and `agents` precede `transactions`, satisfying its foreign keys. The transaction and alert event timestamps are VARCHAR(40) so the canonical six-digit UTC strings supplied by the current route are preserved; the base MySQL DDL uses TIMESTAMP and cannot guarantee that text. Nine missing columns from the server migration are added, including transaction currency/status and AML evidence fields. The generator omits a literal default on a LONGTEXT `rules_triggered` addition because MySQL 8 rejects that form; the route supplies the JSON value. Six explicit application indexes cover transaction sender/receiver/agent time access and alert/activity/watchlist lookups. Canonical indexes are installed later by the existing canonical migration.

Static checks confirm the table dependency order and absence of INSERT/DROP/data-copy statements. The SQL has **not** been applied or parsed by the live MySQL server. Its syntax, actual column types, indexes and full Flask route compatibility remain to be verified after provisioning. The schema intentionally contains no users, balances, agents, transactions or other financial rows.

The new [installer](../evidence/stage4u/install_schema.py) accepts only the Stage4T dedicated test URL and expected server UUID. Before its first DDL statement it verifies real `DATABASE()`, `@@server_uuid`, `CURRENT_USER()` and restricted `SHOW GRANTS`, compares the SQL hash with the review record and requires an empty schema. After applying the SQL it checks exact table set, key transaction columns, required indexes, zero rows and identity again. It has no reset or resume mode. MySQL DDL can auto-commit; if interrupted, an administrator must inspect the disposable database before deciding how to proceed. The installer was **not executed**.

## 4. Adapter compatibility review

The Stage4T URL parser requires `v4_stage4s_disposable` and `v4_stage4t_runner`; it does not fall back to the production URL. Its connector requests that database explicitly. `identity()` reads real MySQL server, database and authenticated principal values and parses `SHOW GRANTS`, allowing global USAGE only and database grants confined to the disposable schema. The exact matching server UUID is required. The worker checks exact trigger names, source tables, operations, timing and statements; Stage2A journal `ensure()` then independently checks each required trigger. The snapshot gate uses REPEATABLE READ with a consistent read-only snapshot, genuine Stage2A `assess` and `freshness`, and full canonical graph replay.

These are source and offline-test findings. `SHOW GRANTS` formatting, trigger metadata, snapshot commands and the generated DDL have **not** been exercised through a test MySQL connection in Stage4U. The documented isolated `-I` command initially failed to import the project package before it could reach the authority check. `v1.py` now adds its fixed project root to the import path before importing the approved service. The corrected command reaches the expected “Test authority unavailable” gate. Eleven adapter tests pass. This changes only the test adapter; no model, history or production check was relaxed. The production Stage3 connector still rejects the disposable database; the test adapter rejects `aml` by configuration. Actual wrong-database, wrong-principal, wrong-server, excessive-grant and altered-trigger checks remain pending live verification.

## 5. Minimal administrator handoff

An administrator with privileges on a chosen test MySQL server must:

1. Read and provide its actual `@@server_uuid`. Verify `v4_stage4s_disposable` is absent, and confirm the intended test runner host.
2. On that server, create only this schema and account, using a newly generated secret supplied through a secure local channel. Replace `127.0.0.1` if the runner connects from a different host:

   ```sql
   CREATE DATABASE v4_stage4s_disposable CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'v4_stage4t_runner'@'127.0.0.1' IDENTIFIED BY '<generated-test-secret>';
   GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, TRIGGER, REFERENCES
     ON v4_stage4s_disposable.* TO 'v4_stage4t_runner'@'127.0.0.1';
   SHOW GRANTS FOR 'v4_stage4t_runner'@'127.0.0.1';
   ```

3. Supply the disposable test URL and recorded UUID to the isolated test process as `V4_STAGE4T_TEST_DB_URL` and `V4_STAGE4T_EXPECTED_SERVER_UUID`. Encode any URL reserved characters in the password. Do not place the secret in repository files or reports.
4. With those variables set, run the guarded schema installer using the Stage3 isolated interpreter, then Stage4T `v1.py prepare` and `v1.py check`. Capture the sanitized verification output and hashes. The administrator should retain a separate record of the test server and grants. Do not run Flask startup or submit financial fixtures in this stage.

Commands from the workspace root, **only after** the administrator has completed step 2 and the test variables are present:

```powershell
.\ml_v4\.venv_inference_stage3\Scripts\python.exe -I -B ml_v4/evidence/stage4u/install_schema.py
.\ml_v4\.venv_inference_stage3\Scripts\python.exe -I -B ml_v4/test_binding/v1.py prepare
.\ml_v4\.venv_inference_stage3\Scripts\python.exe -I -B ml_v4/test_binding/v1.py check
```

The adapter's `prepare` action will then use the existing canonical migration, Stage2A history migration, six capture triggers, V4 shadow result migration, genuine test `create_scope` and empty-ledger `attest`. It will pin the resulting boundary only if the calculated status is COMPLETE_VERIFIED. No status is forced and the original `aml` observation boundary is not copied.

## 6. Verification, remaining work and decision

Stage4T's recorded Stage3 workflow remains 54 tests with the two authorized Stage4R application hash exceptions supplied in memory. Stage4U reran the 11 adapter tests after its import fix and verified the isolated command reaches the missing-authority gate. It did not rerun model or MySQL tests. It generated and statically checked the schema artifact. [Stage4U evidence](../evidence/stage4u/decision.json) records the new files, adapter before/after hashes and preservation check.

Database identity, restricted grants, schema installation, six live triggers, test observation authority and all requested adversarial live connection checks remain **NOT VERIFIED**. A later Stage4S run must verify them before any disposable financial fixtures. No source transaction, V4 prediction, ordinary application activation or operational alert occurred here.

**B — ADMINISTRATOR ACTION REQUIRED**

STAGE 4U COMPLETE — WAITING FOR APPROVAL.
