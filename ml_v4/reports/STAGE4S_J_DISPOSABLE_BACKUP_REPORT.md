# Stage 4S-J disposable MySQL backup verification

**Decision: BLOCKED — LOCAL EXECUTION REQUIRED.** The user reports that the Stage4S-I local read-only preflight passed. This Codex process has neither the restricted database credential nor a `mysqldump`/`mariadb-dump` utility on PATH. No backup was created or verified here. No database was modified.

## Prepared files

| File | Purpose |
| --- | --- |
| `ml_v4/stage4sg/run_backup.ps1` | Guarded secure-password backup runner, pinned to the disposable database. |
| `ml_v4/stage4sg/verify_backup.py` | Readable SQL dump, SHA-256, table/index/trigger and row-coverage checks. |
| `tests/test_stage4sj_backup_verifier.py` | Offline malformed-backup regression tests. |
| `ml_v4/reports/STAGE4S_J_DISPOSABLE_BACKUP_REPORT.md` | This report. |

Run locally from the project root:

```powershell
& .\ml_v4\stage4sg\run_backup.ps1
```

If a compatible utility is installed outside PATH, pass its absolute path as `-DumpPath`. The runner accepts only `mysqldump.exe` or `mariadb-dump.exe`. It first checks the utility version, then prompts for the password securely and uses the existing Stage4S-I read-only preflight to verify the exact database, server UUID, restricted principal/grants, six triggers, history authority, counts, InnoDB, and absent idempotency schema. It never passes the password in command arguments or prints it. The temporary `MYSQL_PWD` process environment is cleared immediately after the dump; the dedicated test URL and password material are cleared in `finally`. If the dump utility lacks required permissions, the dump exits nonzero and verification stops. The script does not change grants.

The dump command targets **only** `v4_stage4s_disposable` on `127.0.0.1:3306` and includes all database tables, rows, schema/index definitions, and triggers. It uses `--single-transaction`, `--quick`, `--skip-lock-tables`, `--skip-extended-insert`, `--triggers`, `--hex-blob`, `--no-tablespaces`, and `--databases v4_stage4s_disposable`. The backup is created with a unique timestamped name under `%LOCALAPPDATA%\AML-Stage4SJ-Backups`, outside the repository. The runner removes inherited directory ACLs and grants the current Windows identity full access. It creates the target file with `CreateNew`, so an existing backup is never overwritten. The SQL dump contains sensitive test data and must remain in that restricted local directory, outside Git.

After a successful dump exit, the verifier rereads the file, computes its SHA-256, requires the sole `USE` database to be `v4_stage4s_disposable`, checks definitions for the seven reviewed tables, confirms the six named capture triggers, checks one-row-per-INSERT coverage against 4 transactions, 4 canonical events, 8 capture records, 4 shadow results and zero alert/SAR/CTR rows, and requires each transaction index seen by the preflight to appear in the dump schema. A second read-only preflight must pass with identical existing-row digests. The runner then prints JSON containing backup path, byte size, SHA-256, utility version and verification outcomes. Save that output as local evidence without credentials.

## Actual execution evidence

| Check | Result |
| --- | --- |
| User-reported Stage4S-I local preflight | **PASS, reported by user**; no fresh database session in this Codex process. |
| Dump utility discovery in this shell | **Unavailable**: neither `mysqldump.exe` nor `mariadb-dump.exe` found on PATH. |
| Backup location | **None**; no SQL backup created. |
| File size / SHA-256 / utility version | **Unavailable** until local execution. |
| MySQL dump permissions | **Untested**; the runner fails closed if they are insufficient. |
| PowerShell syntax | **PASS**. |
| Offline verifier, migration guard, contract and binding tests | **20 passed, 0 failed**. |
| Structural backup verification | **NOT RUN** on a real dump. |
| Restore verification | **NOT RUN**; no restore is authorized in this stage. |

Structural verification is narrower than a successful restore test. Even after a local PASS, this stage can establish readable, apparently complete backup coverage and an integrity checksum, but cannot prove that the dump restores cleanly. The backup is **not yet suitable evidence for migration review** until the local runner succeeds and its path, size, SHA-256, utility version, counts, triggers, indexes and preflight results are recorded. A separately approved restore rehearsal to a different disposable recovery database would provide stronger recovery assurance; none is performed here.

**Next action:** locate a compatible local dump utility and run the guarded backup runner with the restricted account. If it reports a permission failure, stop and review that specific missing permission without broadening the account automatically. Do not run the migration until the resulting backup evidence is reviewed and approved.

**STAGE 4S-J BACKUP PREPARED — WAITING FOR LOCAL EXECUTION AND APPROVAL.**
