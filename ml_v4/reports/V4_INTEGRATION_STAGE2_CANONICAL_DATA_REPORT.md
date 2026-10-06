# MODEL V4 — INTEGRATION STAGE 2 CANONICAL MOBILE-MONEY DATA FOUNDATION

**B — FOUNDATION PARTIALLY READY; LIMITED DATA WORK REMAINS**

Prospective canonical event validation, additive storage and the customer ingestion path are implemented. The configured MySQL schema was inspected and one new canonical-events table with five history indexes was created. **50 tests passed.** Historical records were not converted, rewritten or backfilled. New canonical rows retain `history_status=UNKNOWN`; a verified history-completeness workflow is still required before the application can supply trustworthy V4 replay histories.

V4 was not loaded or executed. No model was trained, no threshold was changed, no sealed evaluation was accessed and no next integration stage was started. V1 inference remains the existing application path; its model/feature service and V3 integration are unchanged. The server was not imported or launched, and no real financial transaction was submitted during testing.

## 1. Authority and verified preservation baseline

Stage23 retains `v4.development.freeze.stage23.1`: original Stage18 XGBoost, `v4.features.1`,40 semantic fields/42 estimator columns, inclusive threshold0.50. Original artifact:

`ml_v4/development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib`

SHA-256 `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`.

Integration Stage1's decision D remains historical evidence. All **399 inherited named paths** matched before work. Two application files were authorized to change here: server.py and static/react-dashboard.js. The remaining **397 protected files** match their original hashes after work, including V1/V3/V4 artifacts, frozen sources, datasets, Stage21/22 experiments and fit ledgers. [Before hashes](../evidence/integration_stage2/before_sha256.json), [preservation](../evidence/integration_stage2/preservation_verification.json). Hashing was confined to the inherited explicit inventory; sealed trees were not enumerated or read. Stage15A's broader historical archive snapshot gap remains unresolved.

## 2. Files changed

| File | Purpose |
| --- | --- |
| [canonical_mobile_money.py](../../canonical_mobile_money.py) | Versioned observable contract, strict decimal-money/time/role validation, serialization, explicit future-form mapping and conservative historical classification. |
| [canonical_mobile_money_store.py](../../canonical_mobile_money_store.py) | Engine/schema inspection, additive migration, canonical persistence/readback with caller-owned transaction, no upsert/backfill. |
| [migrate_canonical_mobile_money.py](../../migrate_canonical_mobile_money.py) | Explicit inspect/apply CLI; no server import or startup migration. |
| [server.py](../../server.py) | Versioned prospective customer ingestion, canonical persistence before existing V1 processing, rollback on persistence failure, no canonical-request training thread, protected-history clear guard. |
| [static/react-dashboard.js](../../static/react-dashboard.js) | Customer form submits canonical event type, explicit channel, agent, serviced wallet and cash direction; bounded decimal amount. |
| [tests](../../tests/test_canonical_mobile_money.py) | Hand-authored validation/storage/handler/no-model/preservation tests. |
| This report and `ml_v4/evidence/integration_stage2/` | Discovery, migration, tests, history-completeness design, preservation and output manifest. |

No frozen feature implementation, model, preprocessing, model selection, threshold, production Socket.IO event or alert-scoring algorithm was changed. No database reset script was executed.

## 3. Actual database discovery

Read-only connection used the application's configured DATABASE_URL/MYSQL_URL, without displaying credentials or importing server.py. Actual engine: **MySQL8.0.46**. Session timezone was `SYSTEM`; system timezone was `South Africa Standard Time`. Canonical UTC text is stored directly and does not depend on that session timezone.

Actual transactions table has signed BIGINT id, VARCHAR account/type/channel/currency fields, **DOUBLE amount**, **VARCHAR(255) timestamp**, nullable BIGINT agent_id, and existing operational-risk/AI/report columns. No canonical fields existed. Agent table has BIGINT id and agent metadata. Existing transaction indexes were primary id and individual sender_account, receiver_account, timestamp, risk_level and agent_id indexes. Deployed schema therefore confirms the central Stage1 role/money/time gaps. No transaction history content, user credentials or balances were queried for this audit.

Full column and index metadata is in [database discovery](../evidence/integration_stage2/database_discovery.json). The CLI separately checked signed parent BIGINT and InnoDB tables before DDL. [Migration inspection](../evidence/integration_stage2/migration_plan.json).

## 4. Additive migration performed

Created **`canonical_mobile_money_events`**, containing exactly the eleven frozen Event fields plus `canonical_version` and `history_status`. `transaction_id` is signed BIGINT primary key, reusing the original transaction ID and referencing transactions.id with ON DELETE RESTRICT. `amount_minor` is BIGINT. All textual fields are VARCHAR(255), utf8mb4 binary collation, NOT NULL. Event timestamps contain canonical fixed-width27-character UTC text with six fractional digits, enforced at ingestion. Empty strings represent absent direct-W2W agent/service, exactly as the frozen Event contract requires.

Version is `mobile_money.canonical.v1`. Every ingested row gets `history_status=UNKNOWN`; client forms cannot supply a completeness claim. Database checks constrain amount1..1500000, currencyUSD and history_statusUNKNOWN. Full event-role/version/time validation is application-side; the table is not claimed to defend against arbitrary privileged direct SQL writers.

Five indexes were created:

- `(event_timestamp, transaction_id)`
- `(sender_wallet, event_timestamp, transaction_id)`
- `(receiver_wallet, event_timestamp, transaction_id)`
- `(agent_id, event_timestamp, transaction_id)`
- `(serviced_wallet, event_timestamp, transaction_id)`

Legacy tables, columns, indexes, values and IDs were not altered. No row was inserted into a business table by the migration. The MySQL apply run passed and an immediate second call returned `changed:false`. Existing canonical schema/index/type/primary/foreign-key mismatch fails instead of automatically altering unknown structures. SQLite migration tests exercise the same representation in an isolated in-memory database; they do not assert MySQL serving throughput.

[Execution evidence](../evidence/integration_stage2/migration_execution.json). MySQL DDL auto-commits: schema creation is **not** falsely described as transactionally reversible. Rollback is non-destructive operational disablement: set `CANONICAL_MOBILE_MONEY_ENABLED=OFF`, preserve the table/rows, and retain or revert the newly versioned UI/application changes through normal release control. There is no DROP/down migration. Disabling causes canonical submissions to fail visibly; they never fall back to legacy-only persistence. The CLI defaults to inspection and only applies with `--apply`.

Canonical rows deliberately prevent deletion of their parent transactions. The admin bulk-clear route now checks for canonical history before deleting anything and instructs the operator to use a separately reviewed retention process. Legacy-only demo databases retain their prior clear behavior. Once canonical history exists, bulk clear is intentionally unavailable.

## 5. Canonical event implementation

The new module imports only the frozen observable `Event` and validator from `ml_v4.generation.stage16r_contract`. It imports no extractor, evaluator, generator execution, model or learned transform. Additional ingestion checks reject unknown/extra fields, wrong types, surrounding whitespace/control characters and malformed time text. The frozen source is unchanged.

Canonical fields, in order:

```text
transaction_id, event_timestamp, sender_wallet, receiver_wallet,
amount_minor, currency, transaction_type, channel, agent_id,
serviced_wallet, agent_flow_direction
```

The canonical envelope version is stored alongside these fields; it is not an extra model input. The helper returns the observable Event and serializes the exact eleven-field dictionary. Python retains signed64-bit IDs exactly; any later browser-facing canonical JSON contract must transport IDs beyond2^53-1 as decimal strings. This stage does not introduce a canonical prediction API.

| Event | Required semantics |
| --- | --- |
| Direct wallet_to_wallet | Different wallets, channel direct_wallet, empty agent/service, flow none. |
| Assisted wallet_to_wallet | Different wallets, channel agent, explicit existing agent, serviced wallet explicitly one endpoint, flow none. Either endpoint may be serviced. |
| cash_in | Channel agent, explicit existing agent/service; sender=receiver=serviced wallet, flow cash_in. |
| cash_out | Same cash representation, flow cash_out. |

No serviced endpoint is inferred from agent presence. Cash does not accept a transfer recipient. Unknown agents are rejected by the existing ingestion lookup and persistence verification. The frozen contract permits string agent IDs; this application binds them to canonical decimal representations of its existing agent primary keys. Existing account identifiers remain unchanged.

## 6. Exact money and time

`cents` accepts decimal **text**, never binary floating input. USD10.50 becomes integer1050 through Decimal arithmetic. It rejects fractional cents, exponents, NaN/Infinity, negatives, zero, non-USD and values aboveUSD15000.00. New canonical amounts are not derived from the legacy floating amount. A compatibility float is made only **after** canonical cents are validated, for the unchanged legacy transaction/balance/V1 interfaces. This does not upgrade existing floating financial accounting or repair historical amounts.

The ingestion server assigns the event instant in UTC with six fractional digits. The standalone timestamp helper can normalize an explicit offset instant to UTC, but rejects naive dates, missing timezone, invalid dates and precision beyond microseconds. A serialized canonical event must already use `YYYY-MM-DDTHH:MM:SS.ffffffZ`; no implicit timezone correction occurs when reading stored events. Ordering remains `(event_timestamp, transaction_id)` with integer ID tie-breaking. Auto-increment IDs are bound after insertion; no ID is fabricated for persisted rows. The pre-insert validation placeholder is replaced and the full event revalidated before storage.

## 7. Future ingestion and legacy mappings

The customer form now explicitly submits canonical types and roles. `/customer/transaction` recognizes the exact versioned form, rejects duplicate/unknown fields, validates it, obtains the existing transaction ID, and writes the canonical sidecar **before** existing V1 processing and balance updates. Persistence failure rolls back the parent insertion and returns an error; it does not create an orphan or continue into AI processing.

Compatibility mappings are from the newly declared canonical type to legacy storage:

| Canonical source | Legacy destination |
| --- | --- |
| wallet_to_wallet | transfer |
| cash_in | deposit |
| cash_out | withdraw |
| amount_minor | legacy amount derived from verified cents |
| UTC event_timestamp | existing timestamp |
| Explicit wallets/agent | existing account/agent fields |

The legacy channel remains its existing application value; the sidecar stores authoritative direct_wallet/agent semantics. V1 sees its existing fields and features; V4 does not run. This mapping is one-way prospective compatibility, not permission to reverse-convert historical banking records.

Older clients using deposit/withdraw/transfer without canonical_version retain the legacy path and receive no canonical row. Admin simulation routes likewise remain legacy data sources; their outputs are not canonical history. A canonical type without the full versioned envelope fails validation rather than falling through. No real transaction was submitted to exercise the live route.

The canonical customer branch no longer schedules the legacy training thread. Existing noncanonical startup/monitor/legacy-client training code was not deleted or invoked in this stage. It must remain isolated from any later V4 service. Existing V1 operational risk, alert/report effects, commit/broadcast ordering and model behavior remain outside this data-stage change; pre-commit legacy broadcasts identified in Stage1 are still a later integration concern.

## 8. Historical classification and completeness

No existing record was classified or backfilled by scanning live transactions. The classification helper implements a conservative policy:

- **CANONICAL_VERIFIED:** exact supported-version event passes validation. This certifies representation, not source truth or history completeness.
- **LEGACY_CONVERTIBLE:** an explicit, complete deterministic event candidate with a reviewer and authority reference. A caller-supplied reference is not external attestation; the helper is not exposed as a public conversion API and performs no write or replay authorization.
- **LEGACY_AMBIGUOUS:** default when canonical data or reviewed deterministic conversion is absent. Floating amounts, banking vocabulary and absent roles do not trigger automatic conversion.

An ambiguous relevant event cannot simply be omitted from later replay. It makes the required history incomplete until authoritative source information resolves it. Empty SQL results never certify true cold start.

[History-completeness design](../evidence/integration_stage2/history_completeness_contract.json) distinguishes UNKNOWN, INCOMPLETE, COMPLETE_VERIFIED and TRUE_COLD_START_VERIFIED. Only UNKNOWN persistence is activated. Future attestations need a source/ledger/graph/entity scope, complete-through full key, first-observation references, gap intervals, source revision, verification authority, evidence reference and revocation. The future feature service must fail closed for unknown/incomplete histories. No private activation date, account creation date or synthetic warmup is substituted for observed history.

## 9. Tests and verification

Command: `python -B -m pytest tests/test_canonical_mobile_money.py -q -p no:cacheprovider`.

**50 passed.** [Test output](../evidence/integration_stage2/test_results.txt).

Coverage includes direct and both assisted W2W endpoints, cash-in/out, missing agent/service and invalid-flow rejection, same-wallet transfer rejection, integer cents and range/currency checks, fractional-cent/float rejection, UTC normalization and ambiguity rejection, same-time ID ordering, serialization, unknown-field rejection, SQLite round trip, transaction rollback, duplicate insertion, deletion restriction, unknown-agent rejection, migration repeat/mismatch rejection, no historical backfill, conservative classification, and preserved model/source hashes.

An isolated test extracts only the `create_transaction` handler AST and executes it with Flask request context, an in-memory database and a **V1 stub**. It never imports server.py startup or a model. It verifies cents persisted before the existing processing call, malformed-input rejection, disabled-ingestion rejection, no canonical-request training and rollback after injected persistence failure. This is not a live-server, browser or real-V1 prediction test.

The real MySQL schema migration and immediate idempotency check passed. No MySQL business-event round trip was attempted; round trips used SQLite fixtures. Python source syntax and `node --check static/react-dashboard.js` passed. Runtime import checks confirm no sklearn/XGBoost/V1/V3 predictor imports in the test process. No fit, prediction or feature extraction was needed.

## 10. Remaining work and limits

1. Obtain and verify history-completeness evidence, including graph scope and actual first observations; implement a restricted attestation workflow. New canonical events do not resolve unknown earlier banking histories.
2. Decide how legacy-only clients/admin simulations coexist with the canonical observation scope. They must not be silently omitted from histories affecting canonical wallets/agents.
3. Review operational deployment and authenticated browser flows before broad rollout. Tests did not execute the actual V1/financial/regulatory pipeline. Existing authorization/CSRF, pre-commit broadcasts, concurrent balance operations and legacy inference failure behaviors are not remedied by canonical storage.
4. A later feature/inference stage must retain Stage23 pins and hashes, handle complete ordered replay/checkpoints and graph costs, and preserve technical inference errors. No Stage3 implementation or V4 model loading is authorized by this result.
5. Future administrative correction/retention tools must preserve canonical audit history; direct privileged SQL edits are not prevented by claiming application records immutable. Bulk clear is blocked once canonical rows exist.

These are explicit limitations, not permission to invent history or widen the frozen USD/amount/role domain. The database schema change supplies prospective event representation; it does not establish independent research validation or production model readiness.

## 11. Preservation and final decision

The final manifest records all new/modified outputs and the two authorized existing-file changes. **397 inherited protected paths remain unchanged;399 were checked with the two authorized changes recorded separately.** No historical evidence or hash expectation was rewritten to hide those changes. Database operations were confined to schema introspection and one new table/index migration; no transaction history, financial balance, alert or report record was modified by this stage's execution.

**B — FOUNDATION PARTIALLY READY; LIMITED DATA WORK REMAINS**

Prospective canonical capture and storage are implemented and tested. Trustworthy history attestations and closure of legacy observation gaps remain necessary before supplying live historical context to V4. V1 remains active, V4 remains disconnected, and all frozen research artifacts are preserved.

V4 INTEGRATION STAGE 2 COMPLETE —
WAITING FOR APPROVAL.
