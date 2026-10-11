# Stage 4S-F transaction idempotency design

**Design only. No code, schema, database, model or configuration change was made. V1 remains primary and V4 production shadow mode remains OFF.**

## Audit and root cause

The customer form in `static/react-dashboard.js` posts directly to `/customer/transaction`. It has no request identifier or durable submit state. Disabling the button would only reduce double clicks; a lost response, browser resubmit, or concurrent retry could still send the same POST twice.

`server.py:create_transaction` validates the form, inserts a transaction with a database-generated `id`, persists a canonical event for versioned mobile-money requests, runs V1 rules/Stage 13/14 and report logic, updates balances, commits, then calls the V4 post-commit hook. The current `transactions` schema has an auto-increment primary key but no client request ID or uniqueness constraint for a submission. The canonical event ID is the resulting transaction ID, and its timestamp is generated for each request. Neither can identify a retry before insertion. No existing request metadata is suitable for idempotency.

Stage4R and Stage4S-A deduplicate **V4 processing for one committed transaction ID** with a named lock and unique shadow-result key. They do not prevent two identical customer POSTs from creating two transaction IDs. The Stage4S-E offline test demonstrated exactly that behavior. Other administrative transaction-generation routes are distinct workflows and are outside this customer-form design.

## Proposed mechanism

Add a nullable `client_request_id CHAR(36)` column to `transactions`, with ASCII binary collation and a unique index on `(sender_account, client_request_id)`. Existing rows retain `NULL`; MySQL permits multiple `NULL` values in a unique index. Require a canonical lowercase UUIDv4 for every **new** `/customer/transaction` submission after coordinated client/server rollout. Authenticate first. Scope the key to the authenticated sender account; never trust a submitted account value.

Generate the UUID with browser `crypto.randomUUID()` when a new customer form draft is created, and keep it stable across rerenders and retries (for example in a React ref). Submit it as a hidden field. The present canonical parser requires an exact nine-field mobile-money envelope, so the route must validate and remove `client_request_id` before calling `prepare_ingestion`; duplicate form keys remain rejected. On successful redirect, a newly rendered draft gets a new UUID. A deliberate second transfer with identical details therefore receives a different UUID and is allowed. If an HTTP response is lost, the client resends the **same** UUID and payload. A browser that lacks secure UUID generation must stop submission or obtain a server-issued random token; it must not use a timestamp or low-entropy fallback.

The UUID is recorded on the transaction row in the same database transaction as the canonical event, V1 risk decision, balance updates, alerts and reports. No extra payment details or raw form payload are stored for idempotency. On retry, compare the newly normalized semantic request with the committed transaction and, for mobile-money submissions, its canonical event. Ignore only server-generated fields such as transaction ID, timestamp, risk fields and inference result. Include transaction type, effective amount, currency, sender, receiver, agent, channel, serviced wallet and cash direction. For legacy customer form types, compare the fields that actually determine the stored transaction and balance movement. A missing canonical row or inconsistent stored fields is an integrity error, not a reason to process again.

## Atomic request flow

1. Authenticate the customer; validate that the request ID occurs exactly once and is a canonical UUIDv4. Parse and normalize the transaction fields using the current rules. Prepare the semantic comparison object, excluding the newly generated timestamp.
2. Before balance checks, look up `(authenticated sender account, client_request_id)`. If a committed row exists, compare its stored transaction and canonical event with the normalized request. On equality, return an owner-scoped prior-success response referencing the existing transaction ID. Do not rerun V1, adjust balances, create reports, or call the V4 hook. On mismatch, return a conflict response and record a minimal audit event without payload details.
3. If no row is visible, proceed with the current validation and insert, including `client_request_id`. The MySQL unique index is the concurrency arbiter. Complete canonical persistence, V1 processing, balance changes, alert/report writes and commit in one InnoDB transaction. Only the winning request calls the existing V4 post-commit hook.
4. If the insert receives MySQL duplicate-key error **for this named unique index**, roll back that attempt, start a fresh read, fetch the winning committed row and compare semantics as in step 2. Do not treat other constraint failures as retries. If the winning request rolled back, the waiting insert can succeed and become the sole commit. For deadlock or lock timeout, return a retryable failure instructing the client to preserve the same UUID; never invent a new UUID automatically.
5. Ensure every pre-commit exception rolls back the whole transaction. The existing route explicitly rolls back canonical persistence failures; implementation must extend explicit rollback to all validation/processing/commit failures without moving the V4 hook before commit. Post-commit shadow errors remain isolated from the committed V1 payment.

This sequence handles simultaneous requests because InnoDB holds the unique-key conflict until the first transaction commits or rolls back. A successful first commit yields one transaction ID and one V1/balance/report execution. A first rollback leaves no committed idempotency claim, so a retry may proceed. A lost HTTP response after commit returns the prior outcome without replaying side effects. Reuse of a UUID with different semantic fields is rejected even if the amount matches.

## Compatibility and limits

- **V1:** The winner executes the existing risk, alert, SAR/CTR and balance logic once. A retry reads the committed outcome. The design does not change model weights, Stage 13/14 features, rules or thresholds.
- **V4:** The winner retains the existing post-commit call and shadow deduplication by transaction ID. A retry does not invoke V4. A pending or failed V4 result after a committed payment remains a separate recovery problem; retrying the payment must not be used to repair shadow inference.
- **Privacy:** Return only an authenticated customer's transaction ID and a generic already-recorded status; do not echo wallet details in conflict messages or logs. The random UUID is not an authorization credential. Database access controls still protect transaction rows.
- **Scope:** This prevents duplicate submissions carrying the same UUID. A client that generates a new UUID for an accidental retry can still create a second transfer. The UI should keep the UUID stable through network errors and can disable the submit button as additional feedback, but the database unique index is the correctness control.
- **Existing traffic:** Already committed rows have no request ID and cannot be retroactively deduplicated. Existing browser tabs or API clients without the new field need a coordinated rollout; once enforcement begins, fail closed with a refresh/update instruction before any financial write.
- **MySQL details:** Confirm the live `SHOW CREATE TABLE transactions`, engine, character set, existing indexes and grants before migration. Do not assume the disposable schema exactly matches `database.py` or that MySQL DDL is transactional.

## Alternatives considered

| Approach | Why it is insufficient or less minimal |
| --- | --- |
| Disable submit button | Helps UX but fails on network retries, multiple tabs and concurrent requests. |
| Deduplicate by amount, recipient and time window | Would suppress intentional repeat transfers and has race conditions. |
| Reuse auto-increment transaction ID or V4 inference ID | Neither exists before the first insert; V4's key only deduplicates shadow work for that ID. |
| Session-only token | Does not provide durable, cross-worker or post-restart retry recognition. |
| Separate request ledger with payload copy | Adds a second table and sensitive data duplication; a transaction-column key plus existing canonical record suffices for the current route. |

## Proposed implementation and migration plan

1. **Read-only preflight:** inspect `SHOW CREATE TABLE transactions`, row/index counts, InnoDB engine and current customer-form/API consumers in each intended environment. Take an approved backup and define an operational rollback window. No production data or authority boundary should be changed during design review.
2. **Additive schema migration:** create a reviewed, separately executed migration that adds nullable `client_request_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin` and a named unique index on `(sender_account, client_request_id)`. Check for index-name collisions and verify row counts and existing records afterward. Update `database.py:get_schema_sql` and the SQLite/MySQL/PostgreSQL migration paths in `server.py` for local/test deployments. Require an explicit schema readiness check before enabling the route; the current general MySQL migration logs some DDL errors and continues, which is insufficient for a financial idempotency gate. MySQL `ALTER TABLE` may implicitly commit; do not rely on a surrounding rollback to undo it.
3. **Route code:** update `server.py:create_transaction` to parse the ID outside the canonical envelope, perform the pre-balance retry lookup, compare normalized semantics against committed rows, insert the ID atomically, handle only the named unique-key collision as a retry, and explicitly roll back all pre-commit failures. Preserve the existing commit-before-V4 ordering.
4. **Client:** update `static/react-dashboard.js` to create a stable UUID per draft, include it in the form, preserve it on uncertain outcomes and mint a new one only for an explicit new submission. Update any customer form or API documentation that also posts to this route.
5. **Tests:** extend `tests/test_v4_shadow.py` or add a focused idempotency test module for same-key retry, changed-payload conflict, distinct-key identical transfer, rollback/retry, lost-response retry and concurrent duplicate attempts. Include real disposable MySQL concurrency tests before production rollout; SQLite alone cannot prove InnoDB lock behavior. Verify V1 risk/alert/report and balance effects once, canonical history consistency and one V4 shadow result for the winning ID.
6. **Rollout:** deploy the client and server with schema readiness checks, then require IDs for all new customer submissions. Old tabs should receive a clear refresh response without committing. Monitor duplicate-key conflicts and incomplete transactions without logging full payloads or IDs beyond the existing audit policy.
7. **Rollback:** if behavior fails, disable the new requirement and revert route/client code while retaining the nullable column and index; they are additive and do not affect old inserts. Do not drop the index while idempotent clients are active. Any later schema removal needs a separate reviewed migration and preservation of transaction/history evidence. Committed payments must never be deleted to simulate rollback.

**STAGE 4S-F DESIGN COMPLETE — WAITING FOR APPROVAL.**
