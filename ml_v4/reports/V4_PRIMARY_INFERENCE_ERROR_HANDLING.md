# V4 primary terminal inference-error handling

**Status: implemented and tested offline; no database write or production activation.** The user-reported Stage5C read-only completion is `READ_ONLY_PASS` with 8 transactions, 8 canonical events, 16 captures, reconciled balances and authorized staff access. This work does not reinterpret that as a live retry test.

## Effective decision and immutable evidence

`v4_shadow_results` remains the immutable original terminal `inference_error`. Staff retries use the existing frozen V4 worker on the committed canonical event; the worker verifies history and returns a validated 0.50-threshold result. No V1 path or payment handler is called. A successful retry writes the **effective** AI decision into the existing transaction risk fields and stores the full validated retry result in a separate append-only COMPLETED audit event. The original shadow row is never updated. Independent rule score remains part of the risk calculation; a suspicious V4 result or independent rule score can create one operational alert through the existing helper. The existing CTR flag and SAR review flag remain independent; no CTR or SAR report is created by the retry. Notification follows the decision/audit commit. A failed retry appends its technical result and leaves the transaction explicitly `inference_error`.

Compliance/admin staff can GET `/compliance/v4-error/<transaction_id>` for the original error, effective state, audit events and a session action token. A POST to `/compliance/v4-error/<transaction_id>/retry` with that token and a fresh UUIDv4 `request_key` requests one retry. A POST to `/compliance/v4-error/<transaction_id>/close` also requires a 10–500 character reason. Closure appends a CLOSED event and keeps the AI state `inference_error`; it does not invent a normal or suspicious prediction. The GET response exposes `case_closed`. Both routes recheck the current staff database role. A missing or wrong session token is rejected.

## Prepared schema and safety controls

The **unexecuted** additive schema is [retry_audit_schema_disposable.sql](../stage5c/retry_audit_schema_disposable.sql), bound by name to `v4_stage4s_disposable`. It defines `v4_primary_attempt_events` with `event_id`, transaction ID, staff user ID, UUIDv4 request key, event kind, timestamp, outcome, error code, validated result body and closure reason. A unique `(transaction_id, request_key, event_kind)` index prevents duplicate event insertion. Foreign keys tie events to the original payment and staff user. Two database triggers reject UPDATE and DELETE, enforcing append-only evidence. Existing six `cmm_` capture triggers and the V4 result table are unchanged.

The coordinator takes a per-transaction MySQL named lock before it checks the current staff role, original terminal error, canonical event, closure state and prior attempts. It commits a STARTED event before invoking the worker. A COMPLETED event and any effective decision/alert commit atomically. A crash after STARTED leaves an explicit incomplete attempt and blocks another retry; an authorized staff member can close it with a new key and reason after the lock is free. Reuse of the same key returns the recorded outcome without reinference. New keys after a failed completed attempt permit an explicit new try. Success or closure prevents further attempts. Offline SQLite tests use a process lock only as a hand-fixture analogue; production relies on MySQL `GET_LOCK` and the unique index.

## Files changed

| File | Change |
| --- | --- |
| `v4_retry.py` | New guarded staff retry/closure coordinator and append-only schema checks. |
| `server.py` | Staff-only GET/POST actions with session token and post-commit decision notification. |
| `ml_v4/stage5c/retry_audit_schema_disposable.sql` | Prepared additive disposable audit table and no-update/no-delete triggers. |
| `ml_v4/stage5c/migrate_retry_schema.py`, `run_retry_schema_migration.ps1` | Explicit, pinned, disposable-only future DDL launcher; no automatic retry after partial DDL. |
| `ml_v4/stage5c/verify_retry.py`, `run_retry_verification.ps1` | Read-only preflight and separately gated transaction-8 staff retry verification. |
| `ml_v4/stage4sa/harness.py`, `ml_v4/production_readiness.py` | Refreshed reviewed server source pin; production readiness now requires retry audit schema. |
| `tests/test_v4_retry.py`, `tests/test_v4_retry_routes.py`, `tests/test_stage5c_retry_verification.py` | Offline decision, audit, authorization, concurrency and launcher tests. |
| `ml_v4/reports/V4_PRIMARY_INFERENCE_ERROR_HANDLING.md` | This report. |

No `database.py`, frozen Stage3 inference, V4 model, features or threshold changed. The frozen model SHA-256 remains `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`.

## Offline verification and local commands

Focused V4 primary, retry, staff-route, Stage5C guard and harness tests: **42 passed**. These include malformed worker output remaining an explicit audited error without a prediction. Existing V4 shadow/Flask route tests: **39 passed**. Python compilation and PowerShell parsing passed. No MySQL migration or retry was run in this Codex process.

**Approval boundary:** MySQL DDL implicitly commits. Before any retry can be exercised locally, separately review and approve the additive schema write, confirm the pinned disposable state, then run:

```powershell
& .\ml_v4\stage5c\run_retry_schema_migration.ps1 -Apply
```

After that migration passes, run the read-only retry preflight:

```powershell
& .\ml_v4\stage5c\run_retry_verification.ps1
```

Only with separate approval for an audit/decision write on **existing transaction 8**, run:

```powershell
& .\ml_v4\stage5c\run_retry_verification.ps1 -Apply
```

The guarded command uses the restricted Stage4T account, exact disposable database and server UUID, six history triggers, fresh authority, unchanged 8/8/16/8 source/result counts, original error and model/worker hashes. It submits **no financial transaction**. It records the actual model result without forcing either class, verifies unchanged balances/financial/canonical/capture/original-result rows, and writes local evidence. If any check fails after DDL or the staff action, stop and inspect read-only; neither script retries automatically.

## Remaining blockers

The audit schema has **not** been applied to disposable or production MySQL. Live MySQL lock, trigger, staff action, frozen inference, alert and closure behavior therefore remain unverified. A separate, reviewed production `aml` schema change and production readiness check are required. The saved Stage5C run still lacks historical post-commit notification evidence and a genuine suspicious V4 prediction. Production V4 remains OFF. **Wait for approval before any database write or activation.**
