# V4 retry audit triggers: MySQL 1419 resolution

**Prepared, not executed.** The local trigger-only run failed at `create_no_update_trigger` with MySQL **1419 / HY000**: “You do not have the SUPER privilege and binary logging is enabled.” The previously reported table is intact and empty with zero retry triggers. This Codex process made no MySQL connection or write; the new command rechecks that state before DDL.

## Recommendation

Use an **existing SUPER-capable MySQL administrator** for the two trigger definitions, with `v4_stage4t_runner@127.0.0.1` explicitly set as the trigger definer. The restricted account already has scoped `TRIGGER` privilege for activation. This keeps its grants unchanged, leaves binary logging enabled, and avoids a server-wide policy change. The command connects the administrator to **only** `v4_stage4s_disposable`, verifies the exact server UUID and MySQL 8.0.46, checks existing SUPER and disposable TRIGGER grants, and issues only the two qualified `CREATE DEFINER=... TRIGGER` statements. The body remains the reviewed single `SIGNAL SQLSTATE '45000'` action. MySQL documents that the binary-logging privilege rule applies to trigger creation and that triggers run in their definer context. [Stored-program binary logging](https://dev.mysql.com/doc/refman/8.0/en/stored-programs-logging.html), [stored-object access control](https://dev.mysql.com/doc/refman/8.0/en/stored-objects-security.html).

`log_bin_trust_function_creators` is a dynamic **global** setting, not a per-database or session switch. Temporarily enabling it would relax stored-function and trigger creation checks for every account and database on the same MySQL instance during that window, including production `aml` if it shares the server. Its previous value would need to be restored even after partial DDL failure; concurrent DDL cannot be isolated by this application. MySQL marks the variable deprecated in 8.0 and documents its global scope. **Do not change it for this repair while a capable administrator is available.** It would be a fallback only after an administrator independently confirms a dedicated disposable instance and approves a coordinated maintenance window. Do not grant `SUPER` to `v4_stage4t_runner`, disable binary logging, or use `SET PERSIST`. [Binary-logging variable reference](https://dev.mysql.com/doc/refman/8.0/en/replication-options-binary-log.html), [system-variable privileges](https://dev.mysql.com/doc/refman/8.0/en/system-variable-privileges.html).

## Guarded procedure

From the project root, **after approval**, run:

```powershell
& .\ml_v4\stage5c\run_admin_repair_retry_triggers.ps1 -Apply
```

PowerShell requests the name of an **existing** administrator with SUPER and TRIGGER privileges, then securely prompts for both the restricted disposable account password and the administrator password. Neither password is placed in a command argument or printed. The launcher rejects inherited database/write bindings and clears its credential environment afterward. It never connects to `aml` or issues a global setting or grant change.

Before DDL, the restricted connection verifies the pinned disposable identity, exact UUID, principal, grants, six capture triggers, observation boundary, current fresh history, expected 8/8/16/8 counts, empty audit table, exact reviewed table shape and **zero** retry triggers. It takes protected-row digests and holds a named repair lock. The administrator connection separately verifies the same database and UUID, MySQL 8.0.46, `log_bin=ON`, `log_bin_trust_function_creators=OFF`, its own principal and existing SUPER/TRIGGER grants. After a second disposable preflight, it creates only the two triggers with the restricted account as definer. The final read-only check verifies both exact `BEFORE ... SIGNAL` definitions, restricted definer, zero audit rows, fresh history, unchanged source revision and unchanged financial, V4-result, alert/SAR/CTR and authority row digests. The global trust setting is rechecked as OFF.

Expected success JSON: `status: PASS`, `append_only_triggers: 2`, `trigger_definer: v4_stage4t_runner@127.0.0.1`, `audit_row_count: 0`, `history_freshness: COMPLETE_VERIFIED`, `protected_rows_unchanged: true`, `global_trust_unchanged: true`. This verifies server metadata and the exact rejecting trigger bodies; it does not insert an audit row for a behavioral UPDATE/DELETE probe. If either DDL fails, **do not retry**. Run the existing read-only `run_inspect_retry_schema.ps1` and review the resulting partial state first.

## Files and offline tests

| File | Change |
| --- | --- |
| `ml_v4/stage5c/admin_repair_retry_triggers.py` | Existing-admin, two-trigger DDL with restricted-definer and pre/post guards. |
| `ml_v4/stage5c/run_admin_repair_retry_triggers.ps1` | Secure two-password local launcher. |
| `ml_v4/stage5c/repair_retry_triggers.py` | Pin the reviewed MySQL 8.0.46 version in its preflight. |
| `tests/test_stage5c_admin_trigger_repair.py` | Offline authority, global-policy, exact-DDL and launcher tests. |
| `ml_v4/reports/V4_RETRY_TRIGGER_1419_RESOLUTION.md` | This report. |

Focused offline suites: **30 passed, 0 failed**. Python compilation and PowerShell syntax parsing passed. No server configuration, grant, DDL, financial record, `database.py` or frozen V4 artifact changed here. **Wait for administrator approval and local execution.**
