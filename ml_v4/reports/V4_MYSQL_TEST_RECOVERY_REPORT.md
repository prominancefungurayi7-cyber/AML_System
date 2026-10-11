# MODEL V4 — MYSQL TEST ENVIRONMENT RECOVERY

**B — RECOVERY IMPLEMENTED; LOCAL EXECUTION REQUIRED**

The administrator reports a partial installation of `v4_stage4s_disposable`: 15 tables, no triggers, no financial/history rows or observation scope, and no `v4_shadow_results`. The dedicated test URL and password are not available in this Codex process. I could inspect source and saved evidence, build a guarded continuation and verify its syntax, but **I could not recheck the current MySQL state or execute recovery**. No database connection or write occurred in this turn.

## 1. Root cause and point of interruption

The [Stage4U installer](../evidence/stage4u/install_schema.py) creates the ten application tables. Stage4T `prepare` then calls the canonical migration, three history-table migrations, `canonical_history_journal.ensure(..., apply=True)`, the V4 result migration, `create_scope`, and `attest`, in that order. Ten application tables plus one canonical table, three history tables and one journal table equal the reported **15**. The reported zero triggers and absent result table place the interruption **inside the six-trigger installation**, before result creation, scope creation and attestation.

The administrator says `log_bin_trust_function_creators` was subsequently enabled. That is consistent with a MySQL trigger-creation privilege restriction. The exact original server error was not supplied, so the server-side cause remains an inference from the reported state and migration order, not a proven error code.

The earlier saved [live preflight](../evidence/stage4u_continue/preflight_live.json) records MySQL 8.0.46, server UUID `d441b7bb-43f6-11f1-a2d8-0a0027000005`, principal `v4_stage4t_runner@127.0.0.1`, the approved scoped privilege set, an empty test schema and denial of the test account's connection to `aml`. That record predates the partial installation and **does not verify its current state**. This Codex process has neither `V4_STAGE4T_TEST_DB_URL` nor `V4_STAGE4T_EXPECTED_SERVER_UUID`, and the local test authority file is absent.

## 2. Exact in-place recovery conditions

Created a separate [partial-state recovery utility](../evidence/mysql_test_recovery/recover_partial.py). It refuses to write unless a fresh test-account connection verifies:

1. Actual database name, server UUID, principal, MySQL version and **exact** restricted grants; test-account access to `aml` must be denied.
2. The administrator's trigger-creation setting is currently enabled.
3. The table set is exactly the ten reviewed application tables plus canonical events, three Stage2A history tables and the capture journal. `v4_shadow_results` must be absent.
4. There are **zero triggers of any name**, zero rows in all 15 tables, no scope, no attestation, no canonical event, no journal change and no local test authority file.
5. Transaction schema/indexes, canonical schema and history/journal columns agree with their approved contracts. Named frozen and Stage4U source/schema hashes still match.

It writes the sanitized before-state to `before_writes.json` **before** creating a trigger. Any mismatch stops the run. There is no reset path, no production credential fallback and no attempt to run the original installer blindly.

If these checks pass, the utility calls the unchanged Stage2A `ensure(..., apply=True)` to create the six triggers, checks their exact definitions, calls the existing V4 shadow result migration, then creates the genuine test boundary and calculates its empty-ledger attestation using unchanged Stage2A functions. Scope creation and attestation share one database transaction. The utility requires the calculated COMPLETE_VERIFIED result with no issues before commit and pins the resulting immutable boundary digest in the ignored local authority file. It rechecks trigger definitions, scope, freshness and zero financial/result rows, then writes sanitized `recovery_result.json`.

MySQL DDL auto-commits. If recovery fails after some triggers are created, a second run deliberately rejects that changed state. An administrator must inspect **only the disposable database** and decide the smallest corrective action; no script automatically deletes a trigger or resets a boundary.

## 3. Execution status and exact local command

| Check | Status in this Codex turn |
| --- | --- |
| Current test database identity, grants, tables and rows | NOT RUN — dedicated password/URL unavailable |
| Current trigger count and definitions | NOT RUN; administrator reports zero |
| Current observation scope and attestation | NOT RUN; administrator reports none |
| Trigger creation, shadow result table, genuine boundary and attestation | NOT RUN |
| Recovery Python syntax | PASS |
| Local PowerShell runner syntax | PASS |
| Frozen Stage18 model and named protected source hashes | PASS, read-only verification |
| Financial fixtures, model fits, V4 activation | NONE |

Run the following from the workspace root in a **local PowerShell session** with the test account password available to the person at the keyboard. The password is prompted securely and is not entered on the command line or saved in project files:

```powershell
& .\ml_v4\evidence\mysql_test_recovery\run_local.ps1
```

The [runner](../evidence/mysql_test_recovery/run_local.ps1) executes the guarded recovery once, then Stage4T `check`, then the existing [live isolation/history verifier](../evidence/stage4u_continue/live_checks.py). It stops at the first failure, clears its test environment variables and does not run the old schema installer, the ordinary Flask server or a financial fixture. Preserve and review the sanitized `before_writes.json`, `recovery_result.json` and `verification_live.json` outputs before approving another stage. If a failure occurs, do not rerun blindly.

## 4. Required verification after local execution

A PASS requires 16 expected tables including `v4_shadow_results`, six exact capture triggers, one genuine test scope at revision 1, a fresh calculated COMPLETE_VERIFIED attestation, zero transactions/canonical events/journal changes/shadow results, and a pinned test authority matching the actual server/principal. The separate verifier also checks wrong-server and altered-boundary rejection, production connector rejection of the disposable URL, and the test binder's rejection of `aml`.

The recovery process uses only the restricted test account and attempts no production write. Denial of its `aml` connection and the absence of any production connection in the scripts support isolation. A claim that `aml` contents are byte-for-byte unchanged would require separately authorized production read access and is **not made here**.

## 5. Remaining integration work

Only after successful local recovery and review should the next controlled test stage exercise the actual Flask → MySQL → canonical → Stage2A → frozen V4 → result → compliance path. It must include direct and agent-assisted wallet transfers, cash-in, cash-out, normal/positive/error outputs, V1/V4 separation, staff authorization, rollback/duplicate handling and transaction latency. These are **not performed in this recovery stage**. The production Stage4R worker still uses its approved production connector; an isolated application test harness must explicitly bind the separate test worker without exposing it through a user request.

## 6. Preservation and final decision

New files are this report and `ml_v4/evidence/mysql_test_recovery/`. No Stage3 implementation, feature extractor, model, preprocessing, threshold, V1/V3 asset or historical report was changed. The frozen model remains `primary_XGB_EXPERIMENTAL.joblib`, SHA-256 `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`, with 40 semantic features, 42 estimator inputs and threshold 0.50. No sealed evaluation data was accessed. `V4_SHADOW_ENABLED` was not changed; V1 remains active and no V4 operational alerts were created. [Recovery artifact manifest](../evidence/mysql_test_recovery/decision.json) records the exact source/report hashes and offline status.

**B — RECOVERY IMPLEMENTED; LOCAL EXECUTION REQUIRED**

The database is **not yet verified recovered**. Stage4S full end-to-end testing remains gated on the local recovery and evidence review.

MYSQL TEST RECOVERY COMPLETE —
WAITING FOR APPROVAL.
