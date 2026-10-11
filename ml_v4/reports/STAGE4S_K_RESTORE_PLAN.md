# Stage 4S-K disposable backup restore verification plan

**Status: preparation complete; restore NOT executed.** The original `v4_stage4s_disposable` database, production `aml`, and the idempotency schema remain untouched. V1 stays primary and production V4 shadow mode remains off.

## Backup inspection and integrity

The named backup is `C:\Users\PROMINENT\AppData\Local\AML-Stage4SJ-Backups\v4_stage4s_disposable-20261009-225015-3681550.sql`. A scoped read-only inspection found **66,458 bytes** and SHA-256 **`b883ecb0fa7132106b5b1eeb91f26369e708e51ec54298b542251a9dd8e6c85c`**, matching the supplied pin. Its schema-control statements are exactly:

```sql
CREATE DATABASE /*!32312 IF NOT EXISTS*/ `v4_stage4s_disposable` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `v4_stage4s_disposable`;
```

No `DROP DATABASE`, `ALTER DATABASE`, other `CREATE DATABASE`, or other `USE` statement was found in the read-only scan. The backup verifier reported `STRUCTURALLY_VERIFIED`: 16 table definitions, 4 transaction rows, 4 canonical rows, 8 capture rows, 4 V4 shadow rows, zero alert/SAR/CTR rows, all six `cmm_` trigger definitions, and transaction indexes `PRIMARY`, `idx_stage4u_tx_agent_time`, `idx_stage4u_tx_receiver_time`, and `idx_stage4u_tx_sender_time`. This confirms readable dump structure, **not** restore success. No transaction row values or credentials were printed.

## Recovery target and account

Proposed recovery database: **`v4_stage4sk_recovery`** on pinned server UUID `d441b7bb-43f6-11f1-a2d8-0a0027000005`, with separate principal **`v4_stage4sk_restore`**. A database administrator must separately provision an **empty** recovery schema and a grant limited to that schema. The prepared guard requires only global `USAGE`, plus scoped `SELECT`, `INSERT`, `CREATE`, `DROP`, `INDEX`, `ALTER`, `TRIGGER`, `LOCK TABLES`, and `REFERENCES`. It permits scoped `CREATE VIEW` and `SHOW VIEW` if needed for a full dump, but rejects any other privilege, grant option, role grant, global write grant, or access to another schema. No grant or schema was created in this stage. The recovery account must have **no** privilege on `v4_stage4s_disposable` or `aml`.

The runner binds to `127.0.0.1:3306/v4_stage4sk_recovery` with the separate recovery account. It rejects ordinary database URL variables and any Stage4T original test URL. It verifies actual `DATABASE()`, `CURRENT_USER()`, `@@server_uuid`, grants, and an empty table set before any restore. The original disposable database URL is never used for write operations.

## Prepared restore safeguards

Created `ml_v4/stage4sg/restore_sql.py`, `ml_v4/stage4sg/recovery_guard.py`, `ml_v4/stage4sg/run_restore_verification.ps1`, and `tests/test_stage4sk_restore_guards.py`; enhanced `ml_v4/stage4sg/verify_backup.py` to report transaction index names. The runner requires `-Apply` and a secure password prompt. **Do not invoke it until a later stage separately approves the rehearsal and the recovery schema/account exist.**

The SQL preparation requires the exact backup filename and SHA-256, reruns structural verification, rejects unexpected schema-control, account/grant, file-loading and source-qualified SQL, requires exactly one source `CREATE DATABASE` and `USE`, **removes** the `CREATE DATABASE` line entirely, and rewrites only `USE` to `v4_stage4sk_recovery`. A read-only `--inspect-only` run against the actual backup passed: one `CREATE DATABASE` removed, one `USE` retargeted, no SQL executed. The transformed file is generated only at future execution time in the restricted backup directory and removed afterward. The original SQL backup remains unchanged.

The future runner invokes a local `mysql.exe`/`mariadb.exe` with recovery-only credentials supplied through a temporary process environment, never the command line. It checks process exit, then verifies the restored table set against the dump, exact six trigger definitions, exact reviewed counts, absent idempotency column/index, transaction index names, and SHA-256 digests of all reviewed rows. If a saved Stage4S-I JSON preflight file is supplied through `-OriginalEvidencePath`, it additionally compares restored row digests with the original verified preflight. No such evidence path is available in this session, so that optional comparison has **not** run. A failed or partial restore stops without retry or automatic cleanup; only the recovery schema could be affected.

## Exact future local command

After separate approval and provisioning, from a PowerShell session that permits the locally reviewed script:

```powershell
$backup = Join-Path $env:LOCALAPPDATA 'AML-Stage4SJ-Backups\v4_stage4s_disposable-20261009-225015-3681550.sql'
& .\ml_v4\stage4sg\run_restore_verification.ps1 -BackupPath $backup -Apply
```

Optionally add `-OriginalEvidencePath <absolute-path-to-saved-Stage4S-I-preflight-JSON>`. If the MySQL client is outside PATH, add `-MysqlPath <absolute-path-to-mysql.exe>`. This is a **proposed** command, not an instruction to execute during Stage 4S-K.

## Offline checks and remaining risks

The actual backup hash, structural verifier and read-only SQL retargeting inspection passed. Offline restore guard, backup verifier, migration guard and binding tests passed **23/23**; Python compilation and PowerShell parsing passed. A direct script launch in this Codex shell was blocked by local PowerShell execution policy before the script ran; the operator's approved local session must permit script execution. No recovery credential is available here, so target identity/grants/empty-state checks, SQL import, post-restore digests, and restore success are **unverified**.

The full dump may require the listed recovery privileges because it contains table drops, index operations and trigger creation; if the restricted account cannot perform them, stop and review the exact missing privilege. The SQL scanner is intentionally narrow and tied to the pinned dump; a changed dump hash requires a new review. The recovery database must be empty and separately provisioned; this runner will not create it. The structural check does not guarantee that every server-version-specific SQL statement will import successfully. Restore testing is the remaining proof of recoverability, but is outside this preparation stage.

**Decision:** prepared for a separately approved recovery rehearsal, not yet verified recoverable. Do not migrate the original database on the basis of this plan alone.

**STAGE 4S-K PREPARATION COMPLETE — WAITING FOR APPROVAL.**
