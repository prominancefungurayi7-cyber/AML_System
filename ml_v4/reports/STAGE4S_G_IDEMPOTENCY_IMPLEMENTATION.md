# Stage 4S-G offline idempotency implementation

**Status: offline implementation verified; disposable MySQL migration and live concurrency checks remain pending. V1 stays primary and production V4 shadow mode remains OFF.**

## Exact files changed in this stage

| File | Change |
| --- | --- |
| `transaction_idempotency.py` | New UUIDv4 validation, schema gate, semantic retry comparison and exact duplicate-key classification. |
| `server.py` | Requires request ID, checks committed retries before balance validation, inserts ID atomically, rolls back pre-commit failures, preserves commit-before-V4 order; adds SQLite/PostgreSQL schema migrations. |
| `static/react-dashboard.js` | Generates one stable browser UUIDv4 per rendered form draft and submits it as a hidden field. |
| `ml_v4/stage4sg/mysql_migration.py` | Separate guarded, **unexecuted** additive migration for the disposable MySQL schema. |
| `ml_v4/stage4sa/harness.py` | Updated only the exact `server.py` source hash pin so the isolated harness recognizes this reviewed route source. |
| `tests/test_v4_shadow.py` | Updated offline fixture schema/forms and added retry, conflict, rollback, lost-response and concurrent-claim tests. |
| `tests/test_canonical_mobile_money.py` | Updated extracted-route fixture to provide the required ID and uniqueness index. |
| `tests/test_stage4sg_idempotency_contract.py` | New UUID, duplicate-key and migration non-execution tests. |
| `ml_v4/reports/STAGE4S_G_IDEMPOTENCY_IMPLEMENTATION.md` | This report. |

`database.py` was **not changed**. The frozen V4 history authority pins its exact bytes. An initial attempt to add the column to that file caused the isolated V4 fixture to return `MODEL_INTEGRITY`; the change was reverted before final testing. Its SHA-256 is again `fe08a247c07a0db59020028737cffec5c43faef92715f87c849164e49fdce266`. The frozen XGBoost file remains `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`. The approved schema is therefore defined by the separate MySQL migration and the server's SQLite/PostgreSQL migration paths, without changing the frozen dependency.

## Behavior

The customer POST requires exactly one lowercase UUIDv4 `client_request_id`. The React form creates it once per dashboard draft, keeps it through rerenders, and disables submission if secure browser UUID generation is unavailable. The route removes the ID before the exact canonical mobile-money parser sees the form.

After authentication and semantic validation, the route checks for an existing row under `(sender_account, client_request_id)` **before** checking the current balance. A matching committed transaction redirects to the customer dashboard with its original transaction ID. It does not rerun V1, move funds, create a canonical event, create reports, or invoke V4. A changed semantic payload with the same ID returns HTTP 409. A new UUID with identical transfer details is processed as a new intentional transaction.

The winning request inserts the UUID with the transaction row, then performs canonical persistence, V1 processing and balance changes in the same database transaction. The existing commit-before-V4 hook order is retained. Pre-commit exceptions roll back; only a duplicate on the named request index is reclassified as a retry, after rollback and a fresh lookup. Lock/deadlock errors return a retryable response instructing reuse of the same ID. The route checks that the unique index exists before accepting a payment, so an unmigrated MySQL deployment fails closed with HTTP 503.

## Prepared MySQL migration

`ml_v4/stage4sg/mysql_migration.py` was **not run**. It requires explicit `--apply` and a reviewed expected transaction count. The Stage4T binding pins the disposable database, restricted principal and grants; the script additionally checks the expected UUID, existing authority/history/triggers, InnoDB engine and pre-migration schema. A single reviewed `ALTER TABLE` adds nullable ASCII/binary `CHAR(36)` and named unique index `uq_transactions_sender_request(sender_account, client_request_id)`. It then verifies the index, trigger/boundary checks and unchanged row count. Existing rows remain `NULL` and are not backfilled. MySQL DDL is not assumed rollbackable. No production migration was prepared for execution or attempted.

## Offline tests and results

| Suite | Final result |
| --- | --- |
| `tests/test_v4_shadow.py` | **39 passed**; includes first submission, same-key retry, changed payload, new-key identical transfer, failed-first retry, lost response, simulated duplicate insert race, SQLite concurrent unique claim, rollback and V1/V4 separation. |
| `ml_v4/stage4sa/tests/test_harness.py` + `ml_v4/test_binding/tests/test_v1.py` | **17 passed**; source pin and isolated worker/binding checks. |
| `tests/test_stage4sg_idempotency_contract.py` | **3 passed**; canonical UUID, named MySQL error classification and refusal to run migration without `--apply`. |
| Canonical mobile-money/history suites excluding two stale historical hash assertions | **78 passed, 2 deselected**. |
| Stage4S-C legacy connection/explanation suites | **11 passed**. |
| Python syntax and preserved frozen hashes | PASS. |

**Existing test failures/limits:** The two historical artifact-preservation assertions in `tests/test_canonical_mobile_money.py` and `tests/test_canonical_history.py` still compare `ai_stage14_model.py` with a pre-Stage4S-C hash. That approved earlier legacy connection repair changed the service source; the historical baselines were deliberately not rewritten. An additional run of `test_stage17d_integration.py` showed 16 Windows teardown `PermissionError`s when its old fixture tried to delete still-open temporary SQLite files; its test bodies passed, but the suite exit was nonzero. These failures are not counted as idempotency passes. Early Stage4S-G test failures caused by the temporary `database.py` hash change were resolved by restoring the pinned file.

## Compatibility and remaining gates

- The production/MySQL `transactions` table has no request-ID column until the separate migration is approved and run. The new route deliberately refuses payments when the unique index is missing. Coordinated rollout must migrate before deploying the route and client.
- Old open browser tabs and API callers without a UUID receive HTTP 400 before any write and must refresh/update. The server does not silently bypass idempotency.
- The Stage4S-A harness has a new `server.py` source pin. Historical Stage4R and Stage4S-A evidence files still record the earlier source hash and are not evidence that this changed source passed live MySQL review.
- SQLite tests simulate the unique-key race, but they cannot certify InnoDB lock timing, error strings or connection-failure ambiguity. Test the approved migration and same-key concurrent requests on `v4_stage4s_disposable` only in a separately authorized stage. Check V1 risk/alert/CTR/SAR and balance effects once, canonical/history integrity, and one V4 result for the winning transaction ID. No new disposable fixture was submitted here.
- Existing `process_transaction_event` can emit events before commit; this implementation preserves that behavior. Review its notification ordering separately if strict rollback-safe notifications are required. Distinct-key concurrent spending limits are a separate balance-concurrency control.

**STAGE 4S-G OFFLINE IMPLEMENTATION COMPLETE — WAITING FOR APPROVAL.**
