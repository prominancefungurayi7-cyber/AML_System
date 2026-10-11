# Stage 5C history-authority failure diagnosis

**Status: BLOCKED. No new fixture or history-authority write was executed.** The repair requires a new persisted test-history attestation if read-only MySQL inspection confirms that the canonical graph is otherwise complete. The user explicitly requires approval before that write.

## Exact failure condition and cause

Both errors use `canonical_history_store.assess()` followed by `canonical_history.freshness()`. `freshness()` returns `INCOMPLETE` if the current graph has issues; otherwise it returns `UNKNOWN` when the latest attestation is absent or its scope, boundary or `source_revision` differs from the current graph. The Stage4S-A Flask `before_request` guard raises **`Test history not fresh`** unless freshness is `COMPLETE_VERIFIED` with no current issues. The Stage5C strict preflight similarly raises **`History authority is stale or incomplete`**.

The Stage4T worker normally verifies both capture operations, acquires the history lock, writes an attestation for the newly committed event, then calls frozen V4 inference. The Stage5C transaction-8 failure test replaced `coordinator.invoke_test` with an immediate `INFERENCE_ERROR` response. That bypassed the worker's attestation step. Transaction 8 was committed and its source revision changed, while the latest attestation still represents the graph through transaction 7. This is the specific test-integration cause of the stale authority. It is **not** evidence that frozen V4 returned a normal result or that history validation should be bypassed. A separate source/capture defect is still possible until the current database is read read-only.

## Evidence already saved

The locally produced `ml_v4/evidence/stage5c/live_primary.json` records:

| ID | Saved outcome |
| ---: | --- |
| 5 | Prior run, one canonical event, two capture rows, stored successful V4 normal prediction; wallet balances reconciled in the prior read-only review. |
| 6 | New wallet transfer: HTTP 302, one canonical event, two capture rows, V4 success/normal, probability `0.003931179642677307`, `COMPLETE_VERIFIED`. |
| 7 | Cash-in: HTTP 302, one canonical event, two capture rows, V4 success/normal, probability `0.008331581950187683`; independent rule score 45, alert and SAR review flag set, CTR-required flag set. |
| 8 | Injected failure: HTTP 302, transaction ID 8, stored `inference_error`, `ai_risk_level=inference_error`, `risk_level=pending_review`. No prediction was fabricated. |

The saved file stops before its final balance and history checks. It does **not** record transaction 8's capture operations, current wallet balances, latest attestation row or current issue list. The subsequent `interrupted_review.json` contains only `UNRESOLVED` and the stale-history exception because the old inspector stopped before enumerating transactions. Thus current financial consistency and the exact current attestation revision require a fresh read-only database check. No database credential is available in this Codex process.

## Read-only inspection command

Run from the project root:

```powershell
& .\ml_v4\stage5c\run_live_primary.ps1 -InspectOnly
```

The inspector now permits a **read-only diagnosis** when freshness is `UNKNOWN` or `INCOMPLETE`; it does not permit inference or new fixtures in that state. It still verifies the exact disposable database, restricted principal/grants, pinned server UUID, six triggers, unchanged scope authority, idempotency schema, original four rows and frozen model hash. It records the current issue list, current and attested source revisions, attestation ID/sequence, canonical IDs, and each Stage5C transaction's canonical row, ordered capture operations, stored V4 status, alert count and wallet balances in `ml_v4/evidence/stage5c/interrupted_review.json`. It exits nonzero and leaves the status `UNRESOLVED` if authority remains stale. **Do not use `-Execute` after that result.**

If the output shows current `COMPLETE_VERIFIED`, no issues, matching transaction-8 canonical/capture rows and source revisions that differ only because no post-8 attestation exists, the minimal repair is one new attestation of the existing graph under the pinned Stage4T test authority and history lock. That action writes `cmm_history_attestations` and `cmm_entity_history`; it must use `canonical_history_store.attest()` and reject any nonempty current issue list. No source transaction, balance, capture row or model artifact should be changed. **This write has not been authorized or run.** A terminal transaction-8 `inference_error` would remain explicit; an attestation would restore history freshness, not silently reclassify it or rerun its payment.

## Files changed and tests

| File | Change |
| --- | --- |
| `ml_v4/stage5c/live_primary.py` | Add read-only history diagnosis and allow `-InspectOnly` to enumerate prior Stage5C rows even when freshness is stale; keep the strict write preflight and new-fixture gate unchanged. |
| `tests/test_stage5c_history_staleness.py` | Verify that a new committed canonical event without a matching attestation yields `UNKNOWN`, and that an unresolved inspection remains read-only and blocks fixtures. |
| `ml_v4/reports/STAGE5C_LIVE_TEST_FAILURE_REPAIR.md` | Warn that its old new-fixture command is now blocked. |
| `ml_v4/reports/STAGE5C_HISTORY_AUTHORITY_DIAGNOSIS.md` | This report. |

Focused offline regression tests: **10 passed**. Python compilation and PowerShell syntax passed. No MySQL read occurred from this process, and no persisted authority record was modified.

**Approval boundary:** after the read-only report confirms an issue-free current graph and a source-revision mismatch caused only by the missing attestation, obtain explicit approval before appending any test-history attestation. Until then, V4 activation testing remains blocked and production `aml` remains untouched.
