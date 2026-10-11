# Stage 4S-I disposable MySQL migration preflight

**Decision: BLOCKED — LOCAL EXECUTION REQUIRED.** No MySQL schema change, financial fixture, backup, or migration was executed in this session. V1 remains primary and V4 production shadow mode remains off.

## Files prepared and inspected

Created `ml_v4/stage4sg/preflight.py`, `ml_v4/stage4sg/run_preflight.ps1`, and this report. Inspected `ml_v4/stage4sg/mysql_migration.py`, `ml_v4/test_binding/v1.py`, `canonical_history_journal.py`, the Stage4S-H report, and existing read-only launchers. No frozen model, `database.py`, or production application file changed.

## Read-only preflight

Run from the project root on the local machine with the restricted account password:

```powershell
& .\ml_v4\stage4sg\run_preflight.ps1
```

The launcher rejects ordinary database URL variables and enabled V4 shadow mode, prompts with `Read-Host -AsSecureString`, binds only `v4_stage4t_runner` at `127.0.0.1:3306/v4_stage4s_disposable`, pins server UUID `d441b7bb-43f6-11f1-a2d8-0a0027000005`, and clears the credential environment after use. It launches the diagnostic as a module from the project root. The Python diagnostic uses the existing Stage4T identity, principal and grant checks, verifies the six exact capture trigger definitions and pinned observation boundary, and requires `COMPLETE_VERIFIED` history. It reads a repeatable-read, read-only snapshot. It checks InnoDB, all current transaction columns/indexes, no `client_request_id` column or `uq_transactions_sender_request` index, and exact counts of four transactions, four canonical events, eight capture records, four V4 shadow results, and zero alert/SAR/CTR rows. It computes SHA-256 digests of all rows in those seven tables without printing their contents. Any mismatch stops the run. No write SQL occurs.

**Actual results in this Codex process:** `V4_STAGE4T_TEST_DB_URL` and `V4_STAGE4T_EXPECTED_SERVER_UUID` were absent. A credential-free module launch exited 1 with `RuntimeError` at the UUID gate, before any connection. Python compilation and PowerShell parsing passed; the Stage4S-H migration guard, Stage4S-G contract, and Stage4T binding offline suites passed **15/15**. **No fresh database identity, count, trigger, schema, index, or authority result is available.** The local operator should retain the successful preflight output as evidence, avoiding any credential in logs.

## Backup preparation and verification

**Backup location:** none yet. No backup can be claimed or verified without local restricted credentials and a dump utility. A suitable local target is a timestamped file on an encrypted, access-restricted volume **outside the repository**, for example `%LOCALAPPDATA%\AML-Stage4SI-Backups\v4_stage4s_disposable-YYYYMMDD-HHMMSS.sql`. Restrict the directory to the operator and backup administrators; keep the SQL dump and its checksum out of Git and shared logs.

After the preflight passes, use a locally installed compatible `mysqldump` with the same restricted principal, host, database and password supplied through a secure local prompt/process environment (never a command-line password). Use `--single-transaction --quick --skip-lock-tables --triggers --hex-blob --no-tablespaces --databases v4_stage4s_disposable`. This captures table definitions, indexes, all table rows, trigger definitions and database selection. A separate metadata record should retain the preflight JSON, server UUID, principal, dump utility version, backup path, file size and SHA-256. Stop if the account lacks dump/trigger metadata privileges; do not broaden its grants automatically. Do not include `--add-drop-database`, overwrite an older backup, or restore into any database during this stage.

Verify locally that the dump command exits zero, the file is nonempty and readable, its SHA-256 can be recomputed, its SQL contains `CREATE TABLE` for transactions/canonical/capture/shadow tables, all six `CREATE TRIGGER` definitions, row insertion statements for the expected four/four/eight/four records, and the tool's completion marker if supported. Compare the dump's schema and row coverage with the saved preflight results. This inspection is a **structural/readability check**, not a restore test; recovery suitability remains provisional until an authorized restore into a separate disposable recovery database is tested. No such restore is authorized here.

## Migration review and proposed command

The existing migration requires explicit `--apply` and `--expected-transactions`; it uses the same pinned Stage4T binding, UUID, principal/grant verification, six triggers, observation boundary, `COMPLETE_VERIFIED` history, InnoDB, exact existing counts and before/after row digests. It refuses an existing idempotency column or index, so it does not automatically retry a partially applied DDL. Its sole DDL adds nullable ASCII/binary `client_request_id CHAR(36)` and unique index `(sender_account, client_request_id)` to `transactions`. It cannot connect to production `aml` through the binding. MySQL DDL implicitly commits; post-DDL failure requires manual inspection.

**Exact proposed command, for a future separately approved local run only**, after the same secure binding environment has been set and preflight plus backup checks have passed:

```powershell
& .\ml_v4\.venv_inference_stage3\Scripts\python.exe -B -m ml_v4.stage4sg.mysql_migration --apply --expected-transactions 4
```

The command is **not** self-contained: it requires the guarded `V4_STAGE4T_TEST_DB_URL` and `V4_STAGE4T_EXPECTED_SERVER_UUID` environment values. The read-only runner removes those values when it exits. A separately reviewed migration launcher should set them with its own secure password prompt; do not paste a password or URL into a shell command. The proposed command was not executed.

## Blockers and next action

Fresh disposable MySQL preflight, an actual backup, and backup readability/coverage verification are outstanding. `mysqldump` was not found in this Codex shell; the local operator must locate/install a compatible dump utility or arrange an equally complete authorized backup. The script's fixed row counts require a new review if the database has changed since the four saved transactions. **The database is not yet verified ready for migration.** Run the read-only preflight locally, prepare and verify the backup, then submit those results for approval before any `ALTER TABLE`.

**STAGE 4S-I PREFLIGHT PREPARED — WAITING FOR LOCAL EXECUTION AND APPROVAL.**
