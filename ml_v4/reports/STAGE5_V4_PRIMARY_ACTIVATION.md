# Stage 5 — V4 XGBoost primary model activation review

**Final status: BLOCKED_WITH_EXACT_REASONS. V4 was not made primary or activated in production.** The attached request explicitly says to stop and report if a database change is genuinely necessary. The existing customer route requires an idempotency column and unique MySQL index that, per the supplied status and current schema definition, are absent from both the disposable and production databases. Bypassing that gate would weaken duplicate-payment safety. No migration was authorized or executed, so implementation stopped at the audit.

## Exact database blocker

`server.py:create_transaction()` calls `transaction_idempotency.require_schema()` before balance checks, inserts or inference. On MySQL, it requires `transactions.client_request_id CHAR(36)` and a unique `uq_transactions_sender_request(sender_account, client_request_id)` index. If either is missing, the route returns HTTP **503** and does not process a payment. The committed insert also names `client_request_id`, so removing only the guard would not make the route compatible. `database.py` does not define this column; Stage4S-G prepared the separate additive MySQL migration, but it has not been executed. Stage4S-I's reported disposable preflight confirmed the column and index absent; production absence is supplied by the current request and was **not independently queried here**.

The minimal safe database prerequisite is the already-reviewed additive column and unique index, first tested under separate authorization on `v4_stage4s_disposable`, then separately reviewed for production. The prepared disposable script is `ml_v4/stage4sg/mysql_migration.py`; it was **not run**. No change to the frozen model or features is needed for this prerequisite. This is the request's explicit stop condition, so no Stage 5 route, configuration, alert, dashboard or notification code was changed.

## Current primary path audited

| Function | Current path |
| --- | --- |
| Transaction classification | `server.py:process_transaction_event()` builds a Stage13 transaction dictionary and calls `get_stage14_model_service(...).predict(...)`; Stage14's threshold is 0.35. This function is called by the customer transaction route, a pending-transaction processor and four batch transaction paths. |
| Risk scoring | Stage14 probability maps to a 0–100 AI score; rule and behavioral signals are combined into `risk_score`/`risk_level`. A Stage14 exception is logged and AI score becomes zero, with rule/behavior processing continuing. This is incompatible with the requested fail-closed V4 primary behavior. |
| Alerts and reporting | `process_transaction_event()` updates `transactions`, calls `create_alert_if_needed()`, sets `sar_required` for Stage14 suspicious results or other risk/rule conditions, and creates CTR rows for eligible cash transactions. Model suspicion is not itself proof of laundering or a filed SAR. |
| Persistence and balances | The customer route inserts the transaction and canonical event, calls V1 processing, updates balances and commits in one database transaction. The V4 shadow hook runs only **after** that commit. |
| Dashboard | Existing transaction and alert APIs expose persisted `risk_score`, `risk_level`, `ai_risk_level` and `ai_confidence`; `static/react-dashboard.js` renders those fields. SAR/CTR counts are read from their existing tables. |
| Realtime | `process_transaction_event()` currently publishes transaction, alert, CTR and statistics events before commit. `RealtimeBroker.publish()` delivers them immediately to subscribers. The customer route also publishes balance and statistics after commit, allowing duplicate statistics notifications. A rollback can therefore leave a ghost pre-commit event. |

## Existing V4 interface and additional integration constraints

The frozen Stage3 `ml_v4.frozen_inference.service.infer(connection_factory, transaction_id)` verifies pinned artifacts and complete history, constructs prior-only features and returns an explicit result contract; it performs **no** risk update, alert creation or operational routing. `v4_shadow.after_commit()` uses it after payment commit when shadow mode is enabled and stores a separate result. The Stage4T isolated worker is a test-only binding for the disposable ledger. It must not be substituted as a production authority.

The frozen Stage3 history gate uses its own read-only, consistent snapshot and, for MySQL, requires database `aml` and the pinned `controlled-prototype-v1` observation boundary. It cannot observe a new uncommitted customer transaction through a separate connection. Therefore simply replacing the in-transaction Stage14 call with Stage3 inference would not satisfy the requested atomic classification/alert/rollback flow. After the schema prerequisite is resolved, a separately reviewed integration design must reconcile commit visibility, trustworthy history verification, failure handling and operational alert timing without changing frozen Stage3 or silently falling back to V1. The current post-commit shadow path alone cannot make V4 the sole primary decision provider.

## Frozen integrity and offline checks

The actual XGBoost artifact SHA-256 was verified as **`555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`**. Frozen source pins threshold **0.50**, 40 semantic features and 42 estimator columns. Existing frozen integrity and Stage4S-G idempotency tests passed **5/5**; a broader offline set including restore guards passed **11/11**. These are source and offline contract checks, **not** V4-primary end-to-end tests. No new transaction, normal/suspicious classification, alert, dashboard event, SAR/CTR outcome or MySQL latency was measured in Stage 5.

## Work not performed and next gate

Files changed in this stage: **this report only**. No model weights, feature definitions, threshold, frozen inference, MySQL schema, application route, notification path or configuration were modified. No production or disposable fixture was submitted. No production `aml` connection was opened. V1 remains primary; production V4 shadow mode remains off. The earlier recovery provisioning workflow was not resumed.

The next gate is separate approval to execute and verify the idempotency schema change in the disposable database, followed by a reviewed design for using V4 as the single primary decision provider with fail-closed behavior and post-commit notifications. Isolated end-to-end tests must then prove balance/idempotency, canonical/history integrity, V4 classification and failure handling, alerts, SAR/CTR separation, dashboard authorization and no rollback notifications. Production activation remains **not ready**. Until an explicit controlled switch is approved, the rollback position is to keep the existing V1 primary configuration; any future rollback from V4 must be an explicit operator action, never a silent inference fallback.

**STAGE 5 REVIEW STOPPED AT THE REQUIRED DATABASE BLOCKER — WAITING FOR APPROVAL.**
