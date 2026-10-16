# Final local V4 integration

Verified through 13 October 2026. **V4 ACTIVE — customer and admin-generated inference VERIFIED.**

## Running configuration

Startup: project `.venv\Scripts\python.exe -B server.py`, serving http://127.0.0.1:5000.
The approved settings are persisted in the existing local `.env`:

```text
AML_PRIMARY_MODEL=V4
AML_RULE_ENGINE_ENABLED=ON
SOCKETIO_ALLOWED_ORIGINS=http://127.0.0.1:5000
V4_SHADOW_ENABLED=OFF
CANONICAL_MOBILE_MONEY_ENABLED=ON
```

Flask was restarted after the final fix. `/health` reports V4 and rules enabled.
V4 startup performs read-only schema/history checks and loads the frozen model
in its pinned runtime; it does not rerun migrations or reseed accounts.

MySQL identity verified before recovery and after the final restart:

| Field | Verified value |
|---|---|
| Endpoint | `127.0.0.1:3306/aml` |
| Authenticated principal | `aml@127.0.0.1` |
| Server UUID | `d441b7bb-43f6-11f1-a2d8-0a0027000005` |
| History authority | `configured-db-identity:aml@127.0.0.1` |
| Observation scope | `controlled-prototype-v1`, unchanged boundary |
| History status | `COMPLETE_VERIFIED`, fresh after the approved generator test |

No global privileges or MySQL settings were changed. Existing schema-scoped
`ALL PRIVILEGES` was correctly recognized by the readiness parser; global
privileges and access outside `aml` remain rejected by that checker.

## Recovery and integrity

With explicit approval, recovery archived the entire current database state,
including the 6,100 generated transactions, 5,816 alerts and 13,900 source journal
records. It restored transactions, alerts, behavioral profiles, wallet balances
and the source journal to the same verified backup point. Account identity,
credentials, unrelated tables, existing authority/attestation, schema and all
eight triggers were preserved and compared before commit.

- Original backup: `data/local-v4-backups/aml-pre-v4-20261011-221547.sql`
- Original backup SHA-256: `c50820b9582d9523e2f777c601b1ef268bcf5dc01083871fc0df01cd7dd59c7d`
- Current-state archive: `data/local-v4-backups/pre-history-recovery-318b0a8e290c440b96b47977bd496cabacc621548aadab22ae9ed548f8e71779.json`
- Archive SHA-256: `91cf367f7be1bf53b9863e64e9cb05649d2477ea0998457a124d0d00e86531d8`

The first restore attempt rolled back completely because integral SQL `DOUBLE`
values were compared as Python integers versus floats. Parsing now respects the
backup's declared types. The successful retry passed exact restored/preserved
row comparisons and the unchanged history gate before committing. No DDL, reset,
foreign-key disabling or fabricated canonical backfill was performed.

Current counts: **7,802 transactions, 18 users, 415 alerts, two canonical events,
two V4 results and four capture records**.

## Genuine inference and payment reconciliation

| Evidence | Result |
|---|---|
| Transaction | `14621`, approved `$0.01` demo transfer |
| Client request ID | `8e6e3d88-162f-44db-92bf-7f0a25793ce6` |
| Frozen model | `v4.development.freeze.stage23.1` |
| Model SHA-256 | `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18` |
| Feature contract | `v4.features.1`, 40 semantic features / 42 estimator columns |
| Threshold | `0.50`, unchanged |
| Inference ID | `28818ba3-c09d-4589-aee9-e8c8d12a7653` |
| Result | `normal`; suspicious probability `0.0030435712542384863` |
| Independent rules | Enabled; this transaction had no rule indicators |
| History revision | `e43a1a01732b4e244eb01a123447481e82a8976a5fdcf4a5e7d20828261f4947` |

| Demo wallet | Before | After |
|---|---:|---:|
| Sender `ACC1003` | $149,579.88 | $149,579.87 |
| Receiver `ACC1000` | $381,262.26 | $381,262.27 |

Cent-level reconciliation passed; raw legacy floating-point balance values are
retained in the evidence. Every other wallet was unchanged. Repeating the same
request ID produced no extra transaction, capture, inference or balance change.
The committed test remains in the ledger as auditable evidence.

Detailed proof: `data/local-v4-backups/controlled-v4-transfer.json`.
It includes the unchanged result/balance verification after restart.

### Approved admin generator test — 13 October 2026

The restored `/admin/generate-transactions` route committed exactly one approved
**$17.74** demo transfer, transaction **14622**, with request ID
`792976c1-5dac-4b2b-a8d0-5174590ed2ab`. The existing monitor produced a genuine
frozen V4 **normal** decision, suspicious probability **0.004655876662582159**
(**0.465588%**), with the same model hash, feature contract and threshold above.
Inference ID: `6536528c-5d64-4139-a5d7-d071b77552b7`.

| Demo wallet | Before | After |
|---|---:|---:|
| Sender `ACC1003` | $149,579.87 | $149,562.13 |
| Receiver `ACC1000` | $381,262.27 | $381,280.01 |

Every other wallet was unchanged. Cent-level reconciliation and raw floating-point
tolerance checks passed. Both canonical capture records were present; history was
fresh and `COMPLETE_VERIFIED` under the unchanged authority. Independent rules
remained enabled with no indicators for this payment. Compliance could see the
persisted result. Reposting the exact signed request changed no balance,
transaction, capture, inference or alert count. The generation progress endpoint
reported one saved, one normal, zero suspicious, zero pending and zero errors.
Evidence: `data/local-v4-backups/controlled-v4-generation.json`.

## Checks and corrections

- **PASS, live:** real customer/staff login; customer, admin, compliance, alert
  detail and reports pages; protected routes reject anonymous/customer access.
- **PASS, live:** compliance sees the persisted V4 result and receives staff
  transaction events. Customer receives private balance events and cannot
  subscribe to staff V4 results or receive staff transaction/alert events.
- **PASS, live:** normal inference, source/canonical capture pair, fresh history,
  exact model identity, payment idempotency and restart persistence.
- **PASS:** six canonical capture triggers, two append-only retry triggers,
  request uniqueness schema and retry audit schema remain present.
- **PASS, nonfinancial:** 11 decision tests, including normal/suspicious handling,
  explicit errors, independent rule alerts surviving V4 errors, duplicate
  completion, commit failure and concurrent decision application. Focused worker,
  post-commit, backup parsing, startup and grant-check tests also passed.
- **Corrected:** the isolated worker no longer overwrites the authorized history
  attestation. It verifies the coordinator's fresh attestation read-only.
- **Corrected:** a monitor/request race logged an already completed decision as
  unresolved. It now has an explicit completed-state exception handled by both
  callers. A read-only check recognized transaction 14621 after the final restart
  without invoking inference again.

No remaining local V4 activation blocker. Redis is unavailable; local Socket.IO
delivery passed. Cross-server Redis delivery was not demonstrated. Suspicious
and error paths were tested nonfinancially; no extra live payment was generated
to force those outcomes. These controlled results do not establish a dataset-wide
accuracy or flag-rate claim.

**V1/Stage14 is not used in active customer inference or the V4 monitor.**
Historical scores and rollback assets remain. Legacy scenario endpoints and ledger
clearing return blocked responses; they cannot silently select Stage14.
The restored admin Transaction Generation control now uses a separate canonical
V4 path in the existing application: signed request identities, atomic payments,
independent rules, post-commit history refresh and the existing V4 pending monitor.
Customer and generated payments share an ingestion lock to preserve timestamp/ID
ordering. Progress separates predictions from pending/error states. Initial tests
used temporary SQLite fixtures; the approved single-payment live test is recorded
above. Existing
settings actions remain visible. Ledger deletion remains restricted. The database
maintenance button runs the existing read-only schema/history verification and
reports when no migration is required; it never applies unapproved schema changes.

## Restart and safe rollback

When the application is stopped, run from the project directory:

```powershell
$env:AML_PRIMARY_MODEL = 'V4'
$env:AML_RULE_ENGINE_ENABLED = 'ON'
$env:SOCKETIO_ALLOWED_ORIGINS = 'http://127.0.0.1:5000'
$env:V4_SHADOW_ENABLED = 'OFF'
$env:CANONICAL_MOBILE_MONEY_ENABLED = 'ON'
& .\.venv\Scripts\python.exe -B .\server.py
```

For a fault, stop the verified AML listener and preserve the current database,
including transaction 14621 and its evidence. To serve the existing interfaces
with new customer submissions disabled, restart with the same settings and
`CANONICAL_MOBILE_MONEY_ENABLED=OFF`. Keep V4 selected; do not activate a silent
legacy fallback. Existing terminal inference errors use the staff-only audited
retry interface, never a new payment request.

Any later database restoration must account for payments committed after this
recovery. Neither archived pre-recovery branch nor the older baseline backup
may be blindly restored over transaction 14621 or subsequent payments. The
recovery command is guarded against reapplying to the now-changed database.

Display existing proof without submitting another payment:

```powershell
& .\.venv\Scripts\python.exe .\tools\verify_local_v4.py
```
