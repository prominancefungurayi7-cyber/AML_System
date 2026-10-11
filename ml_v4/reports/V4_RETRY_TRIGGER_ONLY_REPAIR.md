# V4 retry audit schema: trigger-only completion

**Prepared, not executed.** The user-supplied read-only inspection reports that `v4_stage4s_disposable` on MySQL 8.0.46 has the empty, correctly structured `v4_primary_attempt_events` table but neither append-only trigger. It also reports the pinned identity and principal, required grants, `COMPLETE_VERIFIED` history with no issues, and the expected 8 transactions, 8 canonical events, 16 capture rows and 8 V4 results. This Codex process did not connect to MySQL; the repair command will recheck those claims against the live database before either DDL statement.

## Cause and correction

The original Python migration sent each `CREATE TRIGGER ... FOR EACH ROW BEGIN SIGNAL ...; END` through `DatabaseAdapter.execute()`, which calls Connector/Python 9.7.0 `cursor.execute()` without a custom delimiter. The installed connector's offline script splitter divides that text into **two** statements at the semicolon inside `BEGIN ... END`; the first part has an unterminated compound body. The connector treated the revised `FOR EACH ROW SIGNAL ...` text as one statement in the same offline check. [MySQL 8.0 permits `SIGNAL` as a trigger body](https://dev.mysql.com/doc/refman/8.0/en/signal.html), and [Connector/Python documents custom delimiters for compound statements](https://dev.mysql.com/doc/connector-python/en/connector-python-multi.html). This is a concrete execution defect that explains the table-only partial state. The original server error code was swallowed by the old migration and cannot be reconstructed with certainty.

The reviewed SQL file and original migration's trigger definitions now use one `SIGNAL` statement per trigger. The full migration still rejects an existing audit table and **must not be rerun**. A separate trigger-only repair creates exactly `v4_retry_no_update` and `v4_retry_no_delete`.

## Files changed

| File | Change |
| --- | --- |
| `ml_v4/stage5c/retry_audit_schema_disposable.sql` | Replace compound trigger bodies with single `SIGNAL` bodies. No table definition change. |
| `ml_v4/stage5c/migrate_retry_schema.py` | Keep the reviewed full migration internally consistent with the corrected SQL; its existing-table guard still blocks rerun. |
| `ml_v4/stage5c/inspect_retry_schema.py` | Check the corrected trigger body plus primary key, index set, ASCII request key and auto-increment details. |
| `ml_v4/stage5c/repair_retry_triggers.py` | New guarded, one-time, trigger-only operation with pre/post read-only verification and protected-row digests. |
| `ml_v4/stage5c/run_repair_retry_triggers.ps1` | Secure-password launcher pinned to the disposable database and Stage4T authority. |
| `tests/test_stage5c_retry_trigger_repair.py` | Focused connector-splitting, guard, exact-write and launcher tests. |
| `ml_v4/reports/V4_RETRY_TRIGGER_ONLY_REPAIR.md` | This report. |

The repair checks exact database, server UUID `d441b7bb-43f6-11f1-a2d8-0a0027000005`, principal `v4_stage4t_runner@127.0.0.1`, scoped grants, six capture triggers, observation boundary, fresh history, all reviewed counts, empty audit table and absence of both retry triggers. It requires every non-trigger schema check to pass, acquires a named repair lock, rechecks before DDL, then creates only the two triggers. It compares financial, user, canonical, capture, V4-result, alert, SAR/CTR and history-authority row digests afterward. It never retries automatically; MySQL DDL may commit even if a later step fails.

## Offline verification

- Focused trigger repair, prior diagnosis, retry verification and V4 retry tests: **25 passed, 0 failed**.
- Connector/Python 9.7.0 splitter check: old compound trigger split into two statements; corrected trigger remained one statement.
- Python compilation and PowerShell syntax parsing: **passed**.
- Live trigger creation or DML rejection probe: **not run**.

The post-check reads MySQL trigger metadata and requires both `BEFORE` bodies to be exactly the reviewed `SIGNAL SQLSTATE '45000'` action. This establishes the configured enforcement. Because the table is empty and this command is limited to creating triggers, it does not insert an audit row to exercise UPDATE/DELETE rejection. A behavioral DML probe requires a separately approved disposable test that leaves no persistent audit data.

## Exact local command

After approval, from the project root run:

```powershell
& .\ml_v4\stage5c\run_repair_retry_triggers.ps1 -Apply
```

Expected successful JSON: `status: PASS`, database `v4_stage4s_disposable`, `append_only_triggers: 2`, `audit_row_count: 0`, `history_freshness: COMPLETE_VERIFIED`, and `protected_rows_unchanged: true`. If it stops after either DDL statement, use `run_inspect_retry_schema.ps1` read-only and do **not** rerun automatically.

No repair, transaction, reset, production access or V4 activation was executed here. **Wait for local execution approval.**
