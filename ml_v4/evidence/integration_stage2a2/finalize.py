"""Verify persisted results from a fresh connection and publish Stage2A.2 report."""
import json
from pathlib import Path
from verify_capture import ROOT, OUT, sha, save, connect, metadata, fingerprints
from canonical_history_store import assess
from canonical_history import freshness

d = json.loads((OUT/'activate_attempt2_execution.json').read_text())
scope = json.loads((OUT/'observation_boundary.json').read_text())
a = json.loads((OUT/'first_attestation.json').read_text())
before = json.loads((OUT/'before_sha256.json').read_text())
assert d['status'] == 'PASS' and d['capture_test']['status'] == 'PASS'
assert all(sha(ROOT/p) == h for p,h in before.items())
c = connect()
try:
    meta = metadata(c)
    assert meta == d['metadata_final']
    c.rollback()
    c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
    c.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT')
    s, current, previous = assess(c,scope['scope_id'])
    assert s == scope and previous == a
    state = freshness(s,current,previous)
    counts = {t:c.execute('SELECT COUNT(*) AS n FROM '+t).fetchone()['n'] for t in ('cmm_observation_scopes','cmm_history_attestations','cmm_entity_history','cmm_source_changes')}
    sources = fingerprints(c)
    assert sources == d['source_before']
    result = dict(status='PASS', persisted_scope_matches=True, persisted_attestation_matches=True,
                  history_status=state, source_revision=current['source_revision'],
                  verified_at=current['verified_at'], graph_scope=current['graph_scope'],
                  issues=current['issues'], entity_count=len(current['entities']), state_table_counts=counts,
                  source_fingerprints=sources, triggers_match=True)
    save('final_live_verification.json',result)
finally:
    c.rollback()
    c.close()
assert state == 'COMPLETE_VERIFIED' and not current['issues']
save('preservation_verification.json',dict(protected_count=len(before),all_match=True,
    after_sha256={p:sha(ROOT/p) for p in before}, business_recordsets_unchanged=True,
    original_stage2a1_decision_c_preserved=True, database_state_writes={'scopes':1,'attestations':1,'entities':0},
    fixture_cleanup='Transaction rollback; no journal erasure; auto-increment gaps not reset'))
report = ROOT/'ml_v4/reports/V4_INTEGRATION_STAGE2A2_CAPTURE_VERIFICATION_REPORT.md'
report.write_text(f'''# MODEL V4 — INTEGRATION STAGE 2A.2 CAPTURE VERIFICATION AND OBSERVATION BOUNDARY

**A — TRUSTWORTHY CANONICAL HISTORY FOUNDATION READY FOR V4 FEATURE/INFERENCE IMPLEMENTATION**

The six manually installed capture triggers were verified live in MySQL `aml`. Disposable MySQL capture, rollback, cleanup and idempotency checks passed. The existing Stage2A workflow established a new boundary and calculated **COMPLETE_VERIFIED**. This is an **empty post-boundary prototype scope**: zero canonical events, zero entities, no event watermark and no mature historical window. Decision A closes this history-foundation gate only; it does not activate inference or begin Integration Stage3.

## 1. Authority, installation and live verification

The user reports that an authorized root administrator installed the existing reviewed SQL successfully. This stage connected through the ordinary configured application identity, `aml@127.0.0.1`, to MySQL {d['engine']['version']} database `aml`. It did not recreate, drop, replace or alter triggers, grant privileges, or change binary logging/trust settings. The historical Stage2A.1 Decision C report and evidence remain unchanged.

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
| Scope ID | `{scope['scope_id']}` |
| Scope version | `{scope['scope_version']}` |
| Start UTC | `{scope['start_timestamp']}` |
| Exclusive transaction fence | {scope['start_transaction_id_exclusive']} |
| Visible parent membership | {len(scope['preexisting_parent_ids'])} exact IDs retained in evidence |
| Preexisting committed journal membership | {len(scope['preexisting_change_ids'])} |
| Source | `{scope['source_ledger']}` |
| Canonical version | `{scope['canonical_version']}` |
| Revision | {scope['revision']} |
| Verification identity | `{scope['verification_authority']}` |
| Initial persisted status | UNKNOWN |

The boundary follows the capture tests and recorded gate timestamp. The fence is the maximum committed parent ID, not the larger consumed rollback-only auto-increment values. The complete visible membership is retained to detect later commits of previously invisible IDs. [Boundary evidence](../evidence/integration_stage2a2/observation_boundary.json).

## 5. First calculated attestation and freshness

The unchanged `canonical_history_store.attest` calculated the result with no desired-status argument or override. A later fresh connection loaded the persisted scope/attestation, reran assessment and verified freshness as COMPLETE_VERIFIED.

| Result | Value |
| --- | --- |
| Attestation ID | `{a['attestation_id']}` |
| Sequence / scope revision | 1 / 1 |
| Status | COMPLETE_VERIFIED |
| Verified / complete-through UTC | `{a['complete_through_timestamp']}` |
| Complete-through event key | null — no post-boundary event |
| Source revision | `{a['source_revision']}` |
| Issues | 0 |
| Entity states | 0; no TRUE_COLD_START_VERIFIED assertion for any entity |
| Graph scope | All post-boundary prototype transactions, no entity or edge filters |

The source revision is the retained algorithm's digest of the empty scoped fingerprint. This result certifies an empty observed interval under the prototype algorithm; it does not demonstrate populated-history coverage. Every full-window maturity check (1h,24h,7d,28d,28d1h,29d,35d and prior28 UTC days) was false at verification. The initial scope record intentionally remains UNKNOWN; the separate attestation records the calculated status. Freshness is point-in-time, not a permanent certificate for later traffic. [First attestation](../evidence/integration_stage2a2/first_attestation.json).

## 6. Scope limits and remaining gates

Completeness applies only to the controlled canonical prototype ledger from this boundary onward. It does not establish lifetime EcoCash history, real Econet operator history, pre-boundary completeness, complete customer finances or independent external custody. No ambiguous historical record was converted and no synthetic warmup was created. Disposable capture fixtures were rolled back before the boundary and supply no historical support.

Later legacy-only/unsupported events, missing canonical counterparts, mutations, ordering failures or capture failures can make a subsequent assessment INCOMPLETE. Continue the retained fail-closed verification; do not reset the scope to hide a gap. The administrator remains capable of altering database state, so this is not tamperproof custody. The inherited historical archive limitation remains unresolved.

Model-loader, frozen-feature parity, runtime isolation, transaction/outbox integration and application UI/security remain later separately authorized work. No V4 model was loaded/deserialized, no frozen40 feature vector calculated, no prediction or fit performed, no threshold tuned, no sealed evaluation data accessed and no Stage3 begun.

## 7. Preservation and outputs

**{len(before)} named protected files** match before/after hashes, including inherited V1/V3/V4 references, application source, Stage2A implementation and the historical Stage2A.1 Decision C outputs. No frozen or prior report/evidence file was rewritten. The explicit protected scope excludes unread sealed files. [Preservation verification](../evidence/integration_stage2a2/preservation_verification.json).

New files are this continuation report and Stage2A.2 evidence, including the explicit audit runner and finalizer. They call the retained history functions without changing the architecture. The [decision manifest](../evidence/integration_stage2a2/decision.json) binds these outputs. No application startup or general regression suite was run; verification here is the documented live MySQL capture and state workflow.

## 8. Final decision

**A — TRUSTWORTHY CANONICAL HISTORY FOUNDATION READY FOR V4 FEATURE/INFERENCE IMPLEMENTATION**

Capture and the first scoped attestation passed. This is readiness for a later implementation stage only, with an empty new scope and the qualifications above. No model activation or production-effectiveness approval is implied.

V4 INTEGRATION STAGE 2A.2 COMPLETE —
WAITING FOR APPROVAL.
''',encoding='utf-8')
first = json.loads((OUT/'activate_execution.json').read_text())
assert all(first['source_before'][t] == d['source_before'][t] for t in first['source_before'])
assert all(sha(ROOT/p) == h for p,h in before.items())
save('decision.json',dict(decision='A — TRUSTWORTHY CANONICAL HISTORY FOUNDATION READY FOR V4 FEATURE/INFERENCE IMPLEMENTATION',
    scope_meaning='Empty controlled canonical prototype scope from verified boundary only',
    history_status=state, protected_count=len(before), no_stage3_started=True,
    artifact_sha256={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in list(OUT.iterdir())+[report] if p.is_file() and p.name!='decision.json'}))
print(json.dumps({'decision':'A','protected_files':len(before),'history_status':state,'persisted_state_counts':counts}))
