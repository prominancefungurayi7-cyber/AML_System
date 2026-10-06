# Controlled V4 shadow integration

V1 remains the operational AI. V4 results never update transaction risk/AI columns, create AML alerts, or affect SAR/CTR/account policy. The prototype is disabled by default: `V4_SHADOW_ENABLED=ON` is the explicit local enable switch after controlled-use review. No production cutover is included.

## Lifecycle

The customer canonical handler commits the parent, canonical sidecar and balances first. Its shadow hook then opens a new connection. A MySQL named lock per transaction and a database primary key `(transaction_id, model_version, feature_version)` serialize duplicates. A durable pending record precedes child execution. Final success/error records are immutable and reused by retries. A pending record left by a crash can be resumed with the local management command.

A fixed `python.exe -I -B worker.py` invocation receives only an integer transaction ID, a canonical-row SHA-256 and the MySQL server UUID. These bind the child to the same committed source/server even if application/environment configuration diverges. No caller supplies a model/launcher path or code. Timeout is60seconds; stdout/stderr each have a16KiB cap. Errors, nonzero exit, invalid/duplicate/nonfinite JSON and overflows become technical results with NULL prediction/probability. No child exception text is exposed.

The worker verifies Stage3 source identity, history pins, six exact triggers and the original boundary. It requires committed SOURCE_INSERT and CANONICAL_INSERT records. Under the existing history administrative lock it calls unchanged Stage2A `attest` with `automatic-shadow-technical-reassessment` provenance, without a desired status. INCOMPLETE stops prediction. It then calls unchanged Stage3 `infer`, which opens another read-only snapshot and rechecks freshness. A concurrent later source change can therefore produce HISTORY_INCOMPLETE. This is deterministic prototype technical verification, not independent certification.

The result is committed before notification. Pending/crash recovery is not a claim of exactly-once CPU execution: a crash after prediction but before final persistence may repeat computation, but the database identity prevents a second final result. Final technical errors are reused, not automatically erased or retried into a desired success. No periodic scanner or automatic repair job is installed.

## Storage and operation

`v4_shadow_results` is additive. Its composite primary key is the logical record ID. Scalar fields hold inference ID, status, prediction, nullable DOUBLE probability, fixed DECIMAL(3,2) threshold and decision/error. The validated JSON `body` holds the complete versioned result, including model hash, scope/revision/source/history metadata and inference timestamp; created_at is separate. Duplicate scalar values must match the validated body through the sole write API. FK, unique inference ID and status/threshold checks reinforce persistence.

Explicit commands from the workspace root:

```powershell
.\.venv\Scripts\python.exe -B ml_v4/shadow_integration/manage.py migrate
.\.venv\Scripts\python.exe -B ml_v4/shadow_integration/manage.py retry --transaction-id <actual-committed-id>
```

No startup migration is added. The management command is local administrative access, not an HTTP inference endpoint. Do not invoke it with fabricated live financial activity. A source commit is never retried or rolled back because of a shadow failure. If storage is unavailable, the hook logs a sanitized failure; no fake success is published. Review the source transaction before a later explicit retry.

## Staff delivery and UI

`v4_shadow_result` uses a dedicated Socket.IO subscriber registry, not the global realtime broker. Subscription requires a session user whose current database role is compliance/admin. Every publication rechecks that role and emits to that socket SID only. Logout/disconnect removes subscriptions; demotion removes delivery eligibility. No existing `transaction` or `alert` meaning changes. This registry is local to the existing single-worker prototype; cross-worker/Redis delivery is not implemented.

The GET-only `/api/v4-shadow/results` endpoint independently checks current staff role and returns the latest50 safe result summaries. It does not invoke inference, accept results from customers or refresh attestations. It is the recovery path after missed events/reconnect/page refresh. Notifications are best-effort, not a durable outbox. A separate compliance panel preserves the existing operational risk UI. IDs remain decimal strings without JS number conversion; text is rendered with textContent.

This model identifies transaction patterns defined as suspicious within the synthetic research benchmark. It does not determine that money laundering has occurred.

All positive results require analyst review. A normal result does not certify legitimacy. Probability is the uncalibrated synthetic benchmark class-1 output.

## Verification limits

`fixture_worker.py` is test-only and is never selected by the production coordinator. It copies a controlled SQLite fixture to an in-memory database for the Stage3 fixture adapter. Tests run actual extracted Flask handler bodies, commit checks, captured canonical roles and the real isolated model, with the legacy model stubbed to avoid training/startup side effects. This does not constitute a complete Flask→MySQL→V4 end-to-end PASS.

Live MySQL checks cover additive schema/idempotency, recordset preservation, named-lock contention and a nonexistent-event child request with no inference. Completing the full financial fixture path requires a separately isolated MySQL deployment compatible with the frozen scope contract. The live `aml` observation boundary must not be reset or polluted to achieve that test.
