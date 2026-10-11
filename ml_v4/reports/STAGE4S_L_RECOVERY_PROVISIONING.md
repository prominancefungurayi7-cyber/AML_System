# Stage 4S-L recovery database provisioning preparation

**Decision: administrator provisioning prepared; LOCAL EXECUTION REQUIRED after separate approval.** No administrator SQL, database creation, grant, restore, idempotency migration, financial fixture, or V4 activation occurred in this stage. V1 remains primary and production V4 shadow mode remains off.

## Files

| File | Change |
| --- | --- |
| `ml_v4/stage4sg/provision_recovery.py` | New administrator-only, explicit-apply provisioner with pinned server and absence checks. |
| `ml_v4/stage4sg/run_provision_recovery.ps1` | New secure local launcher; checks the original disposable ledger before and after, then verifies the new recovery account. |
| `ml_v4/stage4sg/recovery_guard.py` | Added optional exact-grant verification; existing Stage4S-K restore checks retain their earlier behavior. |
| `tests/test_stage4sl_provision_guards.py` | New offline tests for wrong UUID, preexisting account/schema, exact DDL, password parameterization and excess grants. |
| `ml_v4/reports/STAGE4S_L_RECOVERY_PROVISIONING.md` | This report. |

Inspected the Stage4S-K recovery guard and restore runner. Their target is `v4_stage4sk_recovery`, account `v4_stage4sk_restore@127.0.0.1`, server UUID `d441b7bb-43f6-11f1-a2d8-0a0027000005`, and an **empty** target schema. The restore SQL removes the source `CREATE DATABASE` and changes its `USE` to the recovery schema. The original `v4_stage4s_disposable` connection is never used for write operations.

## Exact administrator changes prepared

After checking actual `@@server_uuid`, and verifying that both the recovery schema and **all accounts with username** `v4_stage4sk_restore` are absent, the provisioner has exactly three mutating statements, in this order:

```sql
CREATE DATABASE `v4_stage4sk_recovery` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'v4_stage4sk_restore'@'127.0.0.1' IDENTIFIED BY %s;
GRANT ALTER, CREATE, DROP, INDEX, INSERT, LOCK TABLES, REFERENCES, SELECT, TRIGGER
  ON `v4_stage4sk_recovery`.* TO 'v4_stage4sk_restore'@'127.0.0.1';
```

`%s` is a connector parameter bound to the secure local prompt value, not a literal password or command-line argument. The grant is the exact nine-privilege set required by the existing recovery guard. Only global `USAGE` and that schema-scoped grant are accepted afterward; global write grants, access to `aml` or `v4_stage4s_disposable`, grant option, roles and additional scoped privileges fail verification. The script does not use `IF NOT EXISTS`, `ALTER USER`, `DROP USER`, `REVOKE`, or `FLUSH PRIVILEGES`. It refuses a preexisting target instead of changing its password or grants. It does not read or modify production `aml`.

The administrator module connects to `127.0.0.1:3306` without selecting an application database. It checks the real server UUID before any DDL, requires the recovery schema and account name to be absent, executes only the fixed statements above, then checks exact grants, UUID and zero recovery tables. MySQL DDL is not atomic across all three statements. If any later step fails, the target may be partially provisioned; the script stops without rollback claims, cleanup or automatic retry. An administrator must inspect that state before further action.

## Secure launcher and read-only verification

The PowerShell launcher requires explicit `-Apply`. It prompts with `Read-Host -AsSecureString` for the original restricted test password, an administrator password, and a new recovery password. Passwords are never embedded in source, command arguments or report output. The admin module receives them through temporary child-process environment values, which are cleared; BSTR buffers are zeroed in `finally`. The new recovery password must contain at least 20 characters.

Before administrator SQL, the launcher runs the Stage4S-I read-only preflight using `v4_stage4t_runner`: it checks exact original database/server/principal/grants, six triggers, `COMPLETE_VERIFIED` authority, 4/4/8/4 reviewed rows, zero alert/SAR/CTR rows, InnoDB and absent idempotency schema. It removes that original URL before launching administrator SQL. After provisioning, it uses the **separate recovery account** and Stage4S-K guard in `before --exact-grants` mode to confirm target identity, exact grants and zero tables. Finally, it reruns the original read-only preflight and compares all existing-row SHA-256 digests with the before snapshot. A PASS output would prove the original disposable ledger remained unchanged over the provisioning interval. None of these live checks ran in this Codex process.

## Exact proposed local command

Only after separate authorization, from the project root in an approved PowerShell session:

```powershell
& .\ml_v4\stage4sg\run_provision_recovery.ps1 -AdminUser root -Apply
```

Use a different named administrator account with `-AdminUser` if appropriate. The account needs permission to inspect `mysql.user`, create the named schema and user, and grant the fixed recovery privileges. The command prompts for all passwords; none belongs in the command line. It does **not** execute the Stage4S-K restore. Capture only the final nonsensitive JSON status. If the local execution policy blocks scripts, the operator must use an approved execution environment; do not change system policy as part of this stage.

## Offline results and remaining steps

Offline provisioning, restore guard, backup verifier and Stage4T binding tests: **28 passed, 0 failed**. Python compilation and PowerShell parsing passed. An uncredentialed direct module launch without `--apply` stopped before connecting, as designed. No live administrator credential, recovery account or recovery database was used here.

Next, obtain explicit approval for local recovery provisioning, run the guarded command, and review its identity/grant/empty-state and original-ledger before/after evidence. A Stage4S-K restore rehearsal would then require its own approval. The original disposable idempotency migration remains unexecuted.

**STAGE 4S-L PREPARATION COMPLETE — WAITING FOR APPROVAL.**
