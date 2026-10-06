# MODEL V4 — INTEGRATION STAGE 2A.2 CAPTURE VERIFICATION AND OBSERVATION BOUNDARY

**A — TRUSTWORTHY CANONICAL HISTORY FOUNDATION READY FOR V4 FEATURE/INFERENCE IMPLEMENTATION**

The six manually installed capture triggers were verified live in MySQL `aml`. Disposable MySQL capture, rollback, cleanup and idempotency checks passed. The existing Stage2A workflow established a new boundary and calculated **COMPLETE_VERIFIED**. This is an **empty post-boundary prototype scope**: zero canonical events, zero entities, no event watermark and no mature historical window. Decision A closes this history-foundation gate only; it does not activate inference or begin Integration Stage3.

## 1. Authority, installation and live verification

The user reports that an authorized root administrator installed the existing reviewed SQL successfully. This stage connected through the ordinary configured application identity, `aml@127.0.0.1`, to MySQL 8.0.46 database `aml`. It did not recreate, drop, replace or alter triggers, grant privileges, or change binary logging/trust settings. The historical Stage2A.1 Decision C report and evidence remain unchanged.

The hash-verified Stage2A SQL remains SHA-256 `6a39ddc6c5663573ff2203c47997929dbc1f785851cd26361770cf40a12ed310`. All six live action bodies match the retained Stage2A definitions exactly, without whitespace normalization or logic substitution. Names, tables, events and timing match; there are no unexpected `cmm_` triggers.

| Trigger | Timing/event | Table |
| --- | --- | --- |
| cmm_tx_insert | AFTER INSERT | transactions |
| cmm_tx_update | AFTER UPDATE | transactions |
| cmm_tx_delete | AFTER DELETE | transactions |
| cmm_ce_insert | AFTER INSERT | canonical_mobile_money_events |
| cmm_ce_update | AFTER UPDATE | canonical_mobile_money_events |
| cmm_ce_delete | AFTER DELETE | canonical_mobile_money_events |

All four Stage2A history tables exist and use InnoDB. The retained schema checks passed, including canonical schema and journal columns. Before activation no observation scope existed. Trigger metadata was rechecked after fixtures and again from a new connection after attestation. [Initial live metadata](../evidence/integration_stage2a2/inspect_execution.json), [successful execution](../evidence/integration_stage2a2/activate_attempt2_execution.json).

## 2. Disposable MySQL capture and rollback

The successful test used two uniquely named disposable accounts with disabled password values and zero balances, and two disposable direct-wallet transaction fixtures. All inserts, updates and deletes occurred inside one uncommitted InnoDB transaction with an unconditional rollback. No application route, background monitor, balance operation or model was invoked. Fixture status was `CMM_TEST_ONLY`, not the pending application status.

| Required check | Observed result |
| --- | --- |
| Parent INSERT | SOURCE_INSERT |
| Relevant parent amount UPDATE | SOURCE_UPDATE |
| Canonical INSERT | CANONICAL_INSERT |
| Canonical UPDATE | CANONICAL_UPDATE |
| Canonical DELETE | CANONICAL_DELETE |
| Parent DELETE | SOURCE_DELETE |
| Operational-only risk/description UPDATE | No additional journal entry; prior journal rows identical |
| Ordering | Six distinct increasing change IDs 1 through 6 in statement order |
| Rollback | Independent connection saw zero fixture accounts, transactions, canonical rows or journal entries |
| Repeated migration/inspection | Existing history migration returned empty change lists; exact trigger inspection unchanged; no trigger apply |

The first fixture exercised all six operations. The second left parent and canonical inserts present until rollback and verified two journal entries before rollback. Thus rollback was checked on both explicit-delete and still-present fixture activity. No committed journal row was deleted to achieve cleanup. Evidence retains the observed journal; database auto-increment gaps remain and were not reset. These checks demonstrate single-transaction capture order, not a proof of global commit order under concurrent writers or crash recovery. [Capture and cleanup evidence](../evidence/integration_stage2a2/capture_test.json).

### Retained first-attempt failure

The first attempt was rejected with MySQL 1452 because the transaction sender foreign key requires an existing account. It rolled back before any boundary or attestation. The fixture was corrected to include isolated accounts in the same rollback-only transaction; no constraint was disabled and no production logic changed. The [failed execution](../evidence/integration_stage2a2/activate_execution.json) and [executed first revision](../evidence/integration_stage2a2/verify_capture_attempt1.py.txt) are retained. Transaction/canonical/journal fingerprints from that attempt agree with the subsequent successful attempt; its failure is not hidden or counted as a pass.

## 3. Post-test integrity

Full ordered recordset hashes match before tests, after rollback, after boundary/attestation and on final independent-connection verification:

| Recordset | Rows retained |
| --- | ---: |
| users | 18 |
| transactions | 7,800 |
| canonical_mobile_money_events | 0 |
| cmm_source_changes | 0 |

No legitimate business row was changed. No disposable account or transaction remains. All six triggers remain exact and all four state tables remain valid. The only committed state additions are one scope and one attestation; there are no entity records because no post-boundary events exist. [Final live verification](../evidence/integration_stage2a2/final_live_verification.json).

## 4. Actual post-capture boundary

Only after successful tests and preservation checks, the runner called the unchanged `canonical_history_store.create_scope` under the existing administrative lock and a consistent REPEATABLE READ snapshot. It did not construct or insert scope rows manually. The timestamp is UTC from the administrative process through the retained Stage2A `now()` function; it is not an administrator-supplied historical timestamp or a substituted MySQL clock value.

| Metadata | Saved value |
| --- | --- |
| Scope ID | `controlled-prototype-v1` |
| Scope version | `prototype.observation.v1` |
| Start UTC | `2026-10-05T21:14:03.854863Z` |
| Exclusive transaction fence | 8517 |
| Visible parent membership | 7800 exact IDs retained in evidence |
| Preexisting committed journal membership | 0 |
| Source | `application.transactions+canonical_mobile_money_events` |
| Canonical version | `mobile_money.canonical.v1` |
| Revision | 1 |
| Verification identity | `configured-db-identity:aml@127.0.0.1` |
| Initial persisted status | UNKNOWN |

The boundary follows the capture tests and recorded gate timestamp. The fence is the maximum committed parent ID, not the larger consumed rollback-only auto-increment values. The complete visible membership is retained to detect later commits of previously invisible IDs. [Boundary evidence](../evidence/integration_stage2a2/observation_boundary.json).

## 5. First calculated attestation and freshness

The unchanged `canonical_history_store.attest` calculated the result with no desired-status argument or override. A later fresh connection loaded the persisted scope/attestation, reran assessment and verified freshness as COMPLETE_VERIFIED.

| Result | Value |
| --- | --- |
| Attestation ID | `948abf15-15bf-4970-82f1-ba60b2bbefa2` |
| Sequence / scope revision | 1 / 1 |
| Status | COMPLETE_VERIFIED |
| Verified / complete-through UTC | `2026-10-05T21:14:03.939574Z` |
| Complete-through event key | null — no post-boundary event |
| Source revision | `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a` |
| Issues | 0 |
| Entity states | 0; no TRUE_COLD_START_VERIFIED assertion for any entity |
| Graph scope | All post-boundary prototype transactions, no entity or edge filters |

The source revision is the retained algorithm's digest of the empty scoped fingerprint. This result certifies an empty observed interval under the prototype algorithm; it does not demonstrate populated-history coverage. Every full-window maturity check (1h,24h,7d,28d,28d1h,29d,35d and prior28 UTC days) was false at verification. The initial scope record intentionally remains UNKNOWN; the separate attestation records the calculated status. Freshness is point-in-time, not a permanent certificate for later traffic. [First attestation](../evidence/integration_stage2a2/first_attestation.json).

## 6. Scope limits and remaining gates

Completeness applies only to the controlled canonical prototype ledger from this boundary onward. It does not establish lifetime EcoCash history, real Econet operator history, pre-boundary completeness, complete customer finances or independent external custody. No ambiguous historical record was converted and no synthetic warmup was created. Disposable capture fixtures were rolled back before the boundary and supply no historical support.

Later legacy-only/unsupported events, missing canonical counterparts, mutations, ordering failures or capture failures can make a subsequent assessment INCOMPLETE. Continue the retained fail-closed verification; do not reset the scope to hide a gap. The administrator remains capable of altering database state, so this is not tamperproof custody. The inherited historical archive limitation remains unresolved.

Model-loader, frozen-feature parity, runtime isolation, transaction/outbox integration and application UI/security remain later separately authorized work. No V4 model was loaded/deserialized, no frozen40 feature vector calculated, no prediction or fit performed, no threshold tuned, no sealed evaluation data accessed and no Stage3 begun.

## 7. Preservation and outputs

**436 named protected files** match before/after hashes, including inherited V1/V3/V4 references, application source, Stage2A implementation and the historical Stage2A.1 Decision C outputs. No frozen or prior report/evidence file was rewritten. The explicit protected scope excludes unread sealed files. [Preservation verification](../evidence/integration_stage2a2/preservation_verification.json).

New files are this continuation report and Stage2A.2 evidence, including the explicit audit runner and finalizer. They call the retained history functions without changing the architecture. The [decision manifest](../evidence/integration_stage2a2/decision.json) binds these outputs. No application startup or general regression suite was run; verification here is the documented live MySQL capture and state workflow.

## 8. Final decision

**A — TRUSTWORTHY CANONICAL HISTORY FOUNDATION READY FOR V4 FEATURE/INFERENCE IMPLEMENTATION**

Capture and the first scoped attestation passed. This is readiness for a later implementation stage only, with an empty new scope and the qualifications above. No model activation or production-effectiveness approval is implied.

V4 INTEGRATION STAGE 2A.2 COMPLETE —
WAITING FOR APPROVAL.
