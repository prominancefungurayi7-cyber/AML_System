# MODEL V4 — INTEGRATION STAGE 2A CANONICAL HISTORY COMPLETENESS AND OBSERVATION BOUNDARY

**B — HISTORY FOUNDATION PARTIALLY READY; LIMITED WORK REMAINS**

The prototype observation-scope, coverage verifier, persistent entity state and restricted attestation command are implemented. **80 tests passed**:30 new history tests and50 retained Stage2 tests. Four additive MySQL tables exist. However, **MySQL error1419 prevented installation of the six capture triggers** because the configured account lacks the required privilege with binary logging enabled. No real observation boundary or completeness attestation was issued. The implementation fails closed while capture is unavailable.

This stage did not load a model, execute inference, construct V4 features, train/refit, tune the0.50 threshold, fabricate history or access sealed evaluations. No existing application code, canonical event, legacy transaction or frozen artifact was modified. The administrator handoff is ready; actual uninterrupted coverage is not certified.

## 1. Authority and scope

The [Stage23 freeze](V4_STAGE23_DEVELOPMENT_FREEZE_REPORT.md), [Integration Stage1 audit](V4_INTEGRATION_STAGE1_READINESS_AUDIT.md) and [Stage2 report](V4_INTEGRATION_STAGE2_CANONICAL_DATA_REPORT.md) remain authoritative. The original Stage18 XGBoost,40-feature schema/42 estimator columns and threshold>=0.50 are unchanged. Stage2 established exact prospective canonical events but deliberately stored `history_status=UNKNOWN`.

All **413 inherited named paths** matched before and after this stage, including both application files changed in Stage2, all frozen model/source references, V1/V3, prior reports and fit ledgers. [Before hashes](../evidence/integration_stage2a/before_sha256.json), [preservation](../evidence/integration_stage2a/preservation_verification.json). The older Stage15A broad historical snapshot gap remains unresolved. Explicit inherited file hashing excluded sealed trees.

## 2. Implemented files

| New file | Responsibility |
| --- | --- |
| [canonical_history.py](../../canonical_history.py) | Versioned boundary, deterministic snapshot verification, conservative source-revision checks, four statuses, entity first observations, window maturity and stale-attestation checks. |
| [canonical_history_store.py](../../canonical_history_store.py) | Additive state migration, complete snapshot reads, immutable-boundary revisions, append-only application writes of attestations/entity snapshots. |
| [canonical_history_journal.py](../../canonical_history_journal.py) | Capture-journal DDL and six trigger definitions; verifies exact trigger bodies before verification. |
| [manage_canonical_history.py](../../manage_canonical_history.py) | Restricted local MySQL administration CLI: inspect, migrate, establish, attest, revise. No Flask route or browser API. |
| [tests/test_canonical_history.py](../../tests/test_canonical_history.py) | Hand-authored coverage, persistence, journal, failure, ordering, status, window and preservation tests. |
| This report and `ml_v4/evidence/integration_stage2a/` | Evidence and administrator handoff. |

The modules reuse Stage2 observable validation, not V4 extraction or estimation. Neither server.py nor the customer form was changed. No browser field can set a coverage status. Existing canonical-row `history_status` stays UNKNOWN; independently computed snapshot/entity states live in new tables and do not rewrite that historical marker.

## 3. Observation-boundary design

Scope version: **`prototype.observation.v1`**. The source ledger is explicitly `application.transactions+canonical_mobile_money_events`; canonical contract is `mobile_money.canonical.v1`. The creation command records:

- scope identifier and revision1;
- server-generated UTC microsecond start timestamp;
- maximum visible transaction ID as an exclusive fence;
- visible pre-existing parent and journal ID sets;
- source ledger, canonical contract and scope versions;
- verification timestamp, local operator identity and evidence reference;
- initial status UNKNOWN and the controlled-prototype claim limitation.

The timestamp/fence/membership sets establish observation scope, **not pre-boundary behavioral history**. Capturing visible membership also exposes later commits with lower auto-increment IDs that were invisible at boundary creation. A new row absent from the initial set cannot silently disappear from scope merely because its timestamp or ID precedes a later committed row. Backdating is reported, not corrected.

Only one global prototype boundary can be created by the supported command. Revision appends a new scope record while retaining its start/fence/source; it cannot move the start past a known gap. A new revision invalidates stale attestations until a new successful verification. No scope has actually been created in MySQL because its capture prerequisite is unavailable.

### Meaning of the controlled scope

Completeness would apply **only to observed activity in the controlled canonical prototype ledger from the verified boundary onward**. It would not mean complete EcoCash operator activity, externally observed customer finances, verified historical banking records or independent research custody. An entity's first event within this scope can be a true scoped cold start even when unknown real-world activity predates the scope. Any later feature service must retain that explicit scope label and must not imply lifetime history.

Legacy rows before the boundary are retained as legacy evidence. They do not enter V4 history or establish first observation, and no amount/role/time is reverse-derived from them.

## 4. Actual MySQL state and migration outcome

Actual engine remained **MySQL8.0.46**. Schema inspection and recordset preservation hashing used a standalone connection; server.py was not imported or started. Existing transaction and canonical recordsets were read for comparison and hashed without exporting their business values into evidence. Operational risk fields, where read for preservation hashing, were not coverage inputs or model features.

Created additive InnoDB tables:

| Table | Persistent contents |
| --- | --- |
| cmm_observation_scopes | scope_id, revision, JSON body; composite primary key(scope_id,revision). |
| cmm_history_attestations | UUID attestation_id, scope_id, revision, JSON body; primary key attestation_id. |
| cmm_entity_history | attestation_id, entity_key, JSON body; composite primary key. |
| cmm_source_changes | auto-increment change_id, transaction_id, operation, source event timestamp, database UTC capture timestamp. |

State bodies use LONGTEXT JSON serialization; identity columns use VARCHAR(255) binary collation and revisions use BIGINT. The first three tables are verified for names/types/nullability/primary keys during repeat migration. The change journal is additive and has no delete/reset command. Existing transaction/canonical tables, IDs and row values were not altered. MySQL DDL auto-commits; the successful table creation remains even though subsequent trigger creation failed.

Required trigger names:

```text
cmm_tx_insert  cmm_tx_update  cmm_tx_delete
cmm_ce_insert  cmm_ce_update  cmm_ce_delete
```

Source UPDATE capture is limited to changes in id, event timestamp, accounts, type, currency, agent or amount. Routine operational risk/description updates do not invalidate event identity. Canonical INSERT/UPDATE/DELETE and source INSERT/DELETE are recorded. Journal rows commit or roll back with the source transaction; an ID-number gap caused by rollback is not itself treated as missing activity.

**Installation failed before the first trigger was created.** Error1419 states that the required privilege is unavailable with binary logging enabled. This is a MySQL privilege boundary, not an operating-system sandbox failure. The stage did not switch to privileged credentials, grant SUPER, change global settings or enable `log_bin_trust_function_creators`.

[Migration attempt](../evidence/integration_stage2a/migration_execution.json) retains FAIL. [Postconditions](../evidence/integration_stage2a/migration_postconditions.json) confirms all four tables have zero rows and no capture triggers are installed. The state-table migration repeat returned an empty change list. [Post-migration inspection](../evidence/integration_stage2a/database_after.json) reports journal unavailable, no scope, status UNKNOWN. Full MySQL trigger migration/idempotency and real capture remain **NOT VERIFIED**; SQLite fixtures verify the intended behavior.

## 5. Completeness algorithm

The supported CLI serializes administrative operations with a MySQL named lock. Each assessment takes a REPEATABLE READ consistent snapshot. A later service must use the same snapshot requirement; calling the low-level functions with independently changing query results is unsupported.

1. Verify supported scope/source/contract versions and all capture-trigger definitions. Missing or changed capture makes verification unavailable; it cannot produce COMPLETE_VERIFIED.
2. Read all source transaction identity/time/type/currency/agent records in ID order, all canonical events in ID order, and all journal rows in change-ID order. No subject filter, row cap or pagination truncation is used.
3. Determine post-boundary membership using fence, visible baseline membership and explicit source timestamps. Reject ambiguous/future times and newly inserted backdated records rather than guessing or sorting them away.
4. Require a matching, valid canonical counterpart for every relevant parent transaction. Verify exact frozen roles, contract version, currency, identifiers and normalized timestamp; canonical cents come only from canonical events, never from a floating-point conversion.
5. Detect duplicate IDs, orphan counterparts, unsupported semantics, source/list ordering violations and nonincreasing chronological full keys in capture order. Equal timestamps with increasing integer IDs are valid. Numeric ID gaps alone are not evidence of a lost transaction.
6. Compare current fingerprints with retained protected fingerprints. Deletion or alteration cannot become clean merely by taking a second snapshot. Journal records detect source/canonical mutations and activity inserted then deleted between scans; the verifier also retains journal fingerprints to detect subsequent journal alteration/deletion.
7. A missing counterpart may regain eligibility only after a valid matching canonical event exists and a trusted verifier supplies an authoritative resolution reference for the previously recorded gap. The reference cannot override invalid fields, mismatched parents, known mutations or journal failures. No conversion/backfill code is provided.
8. Return INCOMPLETE on any detected issue, without issuing a complete-through watermark. The last observed key is separate diagnostic metadata. Otherwise return a complete snapshot status and key/time plus source revision, entity first observations and graph scope.

The protected baseline accumulates across attestations. Missing rows do not disappear from it, changed fingerprints are not accepted as a replacement baseline, and a scope revision cannot reset it. Source/canonical mutation is conservatively blocking even if it could eventually be explained; an authorized correction design would be separate work.

## 6. Status and entity-state transitions

| Status | Exact meaning and transition |
| --- | --- |
| UNKNOWN | Initial scope or no current matching attestation. A changed source revision or scope revision makes prior approval stale. No inference permission follows. |
| INCOMPLETE | Any detected relevant gap, unsupported row, mutation, missing edge/counterpart or ordering conflict. Known issues cannot be overridden by a requested status. |
| COMPLETE_VERIFIED | Successful whole-scope check for a specified source snapshot and verification horizon; not permanent approval of later writes. |
| TRUE_COLD_START_VERIFIED | Entity state with exactly one valid first observed event in a complete scope: it had no earlier scoped observed participation before that event. It does not assert no pre-boundary or real-world activity. |

The global clean snapshot uses COMPLETE_VERIFIED; individual wallet/agent entries can carry TRUE_COLD_START_VERIFIED. With later observed participation the entity state becomes COMPLETE_VERIFIED. A global gap makes every included entity INCOMPLETE, even if the visibly missing event appears unrelated, because an omitted graph edge can connect previously separate wallets.

Persistent entity snapshots record kind/identity, first canonical timestamp+ID, observation count, complete-through key and timestamp, scope/version/revision, source revision and evidence reference. Incoming and outgoing W2W endpoints both establish wallet observation, while cash establishes its serviced wallet and agent. This state is observation metadata, not the extractor's wallet-activity aggregate. Account creation/private activation dates are never read for first observation.

The persisted canonical event row is not rewritten when state changes. Historical attestations/entity snapshots are retained by append-only application operations. Database administrators can still mutate tables; this is not an independently administered immutable log or production-grade tamper-proof system.

## 7. Frozen temporal windows and first-observation semantics

The window helper explicitly distinguishes1h,24h,7d,28d,28d1h,29d,35d and prior28 complete UTC calendar days. Tests cover exact lower boundaries and one microsecond before them. No generic30-day replacement exists.

Full-window **maturity** is separate from known scoped **completeness**. A young but fully observed controlled scope can be complete while lacking35days of baseline history. The later frozen extractor must emit its prescribed cold-start/baseline sentinels and retain its minimum activity/service-count gates. This stage does not create mature history, pad zeros, calculate40 features or assert model readiness from elapsed time alone.

First observation persists in entity snapshots and complete scope replay. A later35-day rolling query must not discard original first-observation metadata, duplicate-ID knowledge or ordering state. Any checkpoint/replay implementation still requires parity and source-revision verification in its own stage.

## 8. Graph completeness and legacy coexistence

Scope is deliberately global across the controlled prototype ledger. Every relevant source event needs a canonical counterpart; all canonical W2W edges are available, not only rows involving the current wallet. This supports a later complete7-day graph traversal for N3 and directed/funding context for N1–N4. Current endpoint-only history, neighbor limits or arbitrary path caps are prohibited.

The later feature service should obtain the complete verified snapshot, retain all canonical event IDs in full-key order within the boundary, and replay the full observable event stream. Cash and agent activity remain available alongside W2W graph events. It must recompute/check freshness in the same snapshot and use only events preceding the decision key, with the frozen current-event inclusion rules. This report does not implement that feature service.

Legacy-only routes may continue for V1. Any relevant post-boundary legacy transaction lacking a canonical counterpart blocks completeness globally. The journal prevents bulk deletion from hiding such a gap between scans. No route silently promotes legacy data or reconstructs serviced wallets/flow/amounts. Source records outside the declared pre-boundary scope remain untouched and carry no complete-history claim.

## 9. Restricted attestation workflow

`manage_canonical_history.py` is a local administrative command using existing locally configured database access. It records the operating identity as local-admin-command identity and a mandatory evidence reference. No customer endpoint exists and no parameter accepts a desired history status. Status is calculated from source data; customer-supplied status fields remain rejected by Stage2 ingestion/validation.

The deployment trust boundary is the local operator, code and database permissions. Naming an authority/reference is not independent certification. An attacker with equivalent local code/DB administration can bypass this prototype workflow; real production isolation/custody is not established here.

Supported sequence after an authorized administrator resolves capture installation:

1. Run the migration through an authorized migration identity; its idempotent checks create only absent components and reject conflicting trigger definitions. The handoff SQL is a review artifact, not a destructive reset or a request to lower global security.
2. Run inspect and verify all six triggers. Verify a disposable nonproduction MySQL insert/update/delete/rollback capture fixture under the actual server configuration before claiming live capture readiness.
3. Establish the single new scope with a new evidence filename/reference. Its start is current server UTC and status UNKNOWN; it cannot be retroactively declared to cover the interval before capture worked.
4. Run attest. The command checks the complete consistent source snapshot and stores success or INCOMPLETE with issues. Later reads must check freshness; new writes or scope revisions invalidate reuse of older approval.
5. For a genuinely resolved missing counterpart, provide a reviewed local JSON ID-to-authoritative-reference file. The verifier still rejects invalid data and other outstanding gaps. No browser/public conversion operation is supplied.

New evidence paths are mandatory so failed migration records cannot be overwritten by a later successful run. The operator handoff is [admin_capture_triggers.sql](../evidence/integration_stage2a/admin_capture_triggers.sql). It is deliberately not auto-executed with different credentials. The current configured connection cannot perform the required installation.

## 10. Tests and verification evidence

Command:

```text
python -B -m pytest tests/test_canonical_history.py tests/test_canonical_mobile_money.py -q -p no:cacheprovider
```

**80 passed**. [Test output](../evidence/integration_stage2a/test_results.txt).

New tests cover initial scope UNKNOWN, scoped wallet/agent cold start, clean complete snapshots, missing/legacy counterparts, explicit resolution evidence, invalid semantics despite resolution, post-boundary invalidation, source and canonical order, duplicate IDs, equal-time ordering, UTC/calendar boundaries, all required windows, complete graph retention, stale revisions, source deletion/mutation persistence, no customer self-attestation, migration repeat, persistent restart/readback and preserved canonical rows.

Journal fixtures cover a legacy row inserted then deleted before assessment, removed-trigger rejection and journal mutation that cannot clear itself on repeated verification. Restart uses a persisted SQLite fixture reopened through a new connection; it is not a MySQL disaster-recovery certification. Fixtures are manually authored nonsecret test records, not synthetic production history or generated schedules.

All413 protected file hashes are checked by tests. Import checks reject V4 estimators, V1/V3 models, training libraries and V4 feature extractor imports. Stage2 regression tests use their isolated V1 stub and do not execute a real model or Flask startup. No production transaction was inserted to test coverage; live MySQL source recordsets matched before/after the attempted migration and subsequent inspection.

## 11. Remaining blockers and explicit limitations

1. **Database administrator action required:** install the exact capture triggers using an already authorized migration identity capable of satisfying MySQL's binary-logging privilege requirements. No qualifying administrator connection was supplied in this stage. Do not weaken binary logging or grant broad privileges to the application merely to obtain a PASS.
2. **Actual capture verification pending:** trigger installation, MySQL transactional rollback behavior and subsequent migration idempotency must be tested in the intended database environment. SQLite fixture success does not certify unexecuted MySQL triggers.
3. **Actual boundary/attestation pending:** all new state tables remain empty. No existing canonical entity is marked complete, and no interval before capture is retroactively covered.
4. **Snapshot and privilege limits:** claims depend on complete database snapshots and trusted administration. Arbitrary privileged tampering before any observation cannot be proven absent by a developer-controlled journal. This is a controlled dissertation prototype, not operator-grade or independent custody assurance.
5. **Integration remains separate:** the later feature service must gate on current complete snapshot evidence and preserve frozen sentinel semantics. V4 runtime compatibility, inference isolation, commit-aware alerts and scientific limitations remain as documented in Stage1/23.

## 12. Preservation and final decision

No old files were modified. All413 inherited protected paths matched. Existing MySQL transactions and canonical rows have matching before/after recordset hashes; only four new empty tables were created. No trigger was installed, no source row was altered/deleted, and no scope/entity/attestation record was written. No historical hash manifest was revised to conceal the partial migration. [Postconditions](../evidence/integration_stage2a/migration_postconditions.json), [preservation](../evidence/integration_stage2a/preservation_verification.json), [decision/output manifest](../evidence/integration_stage2a/decision.json).

**B — HISTORY FOUNDATION PARTIALLY READY; LIMITED WORK REMAINS**

The history/state implementation passes its controlled fixtures, but the configured MySQL privileges block mandatory change capture. The exact administrator handoff and remaining verification steps are documented. No trustworthy live-history claim or inference authorization is issued.

V4 INTEGRATION STAGE 2A COMPLETE —
WAITING FOR APPROVAL.
