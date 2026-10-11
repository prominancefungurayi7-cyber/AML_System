# V4 retry audit migration: read-only diagnosis

**Status: blocked pending local read-only inspection.** The failed migration must not be rerun. This Codex process has no `V4_STAGE4T_TEST_DB_URL` credential and made no MySQL connection or write.

## What the failed output proves

The Stage4T binding check passed before the migration process started. The original MySQL error code and message are **not recoverable from the displayed output**: `migrate_retry_schema.py` caught every exception and printed only `DatabaseError`. No saved migration error or post-failure schema inspection was found. The failure may have occurred during `CREATE TABLE`, either `CREATE TRIGGER`, or a subsequent verification query. **The actual audit-table state and whether DDL partially committed remain unknown.** Do not treat the Python process exit or rollback as proof that DDL was undone; MySQL DDL can commit independently.

The SQL defines one InnoDB table, ten columns, a unique `(transaction_id, request_key, event_kind)` index, a staff index, two foreign keys, two CHECK constraints and two append-only triggers. The reviewed disposable application schema defines `transactions.id` and `users.id` as `BIGINT`, matching the new foreign-key column types. That static match does not prove compatibility with the current MySQL server version, live parent-table definitions or account privileges. The DDL needs `CREATE`, `REFERENCES` and `TRIGGER` on **only** `v4_stage4s_disposable`; the read-only command checks the actual grants. A missing privilege, incompatible parent definition or SQL dialect issue is a hypothesis until the local inspection supplies evidence.

## Exact changes

| File | Change |
| --- | --- |
| `ml_v4/stage5c/migrate_retry_schema.py` | Name each guarded migration operation and, on a future separately approved execution, print the MySQL error number, SQLSTATE and sanitized MySQL message. A cleanup failure cannot mask an earlier operation failure. No retry was added. |
| `ml_v4/stage5c/inspect_retry_schema.py` | New read-only, consistent-snapshot inspector for pinned identity, grants, history, table columns/indexes/foreign keys/CHECK names, both trigger definitions and existing row counts. |
| `ml_v4/stage5c/run_inspect_retry_schema.ps1` | Secure-password, disposable-only launcher for the read-only inspector. No `-Apply` or DDL path. |
| `tests/test_stage5c_retry_schema_diagnosis.py` | Regression tests for error detail/redaction, failing-step capture, required binding, grant parsing and read-only launcher. |
| `ml_v4/reports/V4_RETRY_SCHEMA_MIGRATION_DIAGNOSIS.md` | This report. |

No SQL schema, `database.py`, financial record or frozen V4 artifact was changed in this session.

## Exact next safe command

From the project root, run **only**:

```powershell
& .\ml_v4\stage5c\run_inspect_retry_schema.ps1
```

The command prompts for the restricted `v4_stage4t_runner` password, binds to `127.0.0.1:3306/v4_stage4s_disposable`, checks server UUID `d441b7bb-43f6-11f1-a2d8-0a0027000005`, principal, restricted grants, six capture triggers and observation boundary, then reads schema and history in a read-only transaction. It prints JSON and clears credential environment variables. Retain that output for review; it does not contain the password or raw grant statements.

The JSON distinguishes `ABSENT`, `PARTIAL_DDL_OR_SCHEMA_MISMATCH`, `SCHEMA_MISMATCH` and `COMPLETE`. Review the individual `checks`, actual columns, indexes, foreign keys, trigger metadata, audit row count, DDL grants, MySQL version and history counts. If the table is absent, the failure was before successful table creation. If it exists without both triggers, DDL partially committed. If complete, the failure was during or after the final DDL step. An observed missing grant or schema mismatch can narrow the root cause; the swallowed original MySQL code cannot be reconstructed with certainty from schema state alone. Any reconciliation write requires a separate review and approval. **Do not rerun `run_retry_schema_migration.ps1 -Apply`.**

## Offline verification

- Focused diagnosis, existing retry verification and retry workflow: **15 passed, 0 failed**.
- Python compilation of the changed modules: **passed**.
- PowerShell syntax parsing of the new read-only launcher: **passed**.
- Live MySQL inspection: **not run; LOCAL EXECUTION REQUIRED**.

**No migration, repair, transaction or production activation was executed. Wait for the read-only output before selecting a correction.**
