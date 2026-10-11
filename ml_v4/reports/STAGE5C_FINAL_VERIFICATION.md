# Stage 5C — V4 customer-primary verification

**Status: BLOCKED for a production switch.** A subsequent user-run disposable test passed its read-only identity/history/idempotency preflight, then encountered the CTR schema error described in [the Stage5C repair report](STAGE5C_LIVE_TEST_FAILURE_REPAIR.md). This Codex process still has no restricted database credential. The earlier run may have committed its first payment; inspect it read-only before any new fixture. V4 production primary mode remains off.

## Files changed

| File | Change |
| --- | --- |
| `server.py` | Pass isolated test-only processor/validator hooks only when Flask is in testing mode; make the independent-rule alert helper use its actual connection engine for insert-ID selection. |
| `v4_primary.py` | Accept explicit processor/validator injection for the isolated test harness; production defaults remain the existing production worker and validator. Use the decision connection's engine for alert insert IDs. |
| `ml_v4/stage4sa/harness.py` | After reviewing the current customer, monitor, batch and notification branches, refresh the exact `server.py` SHA-256 pin to `988d0b864890c10d355287c4f1c36aefd698588817666719125cae2c215401e7`. Startup removal and identity guards remain unchanged. |
| `ml_v4/stage5c/__init__.py`, `live_primary.py`, `run_live_primary.ps1` | New disposable-only guarded Flask/MySQL runner. |
| `tests/test_stage5c_live_guards.py` | Offline binding, route, launcher and Socket.IO exposure checks. |
| `ml_v4/reports/STAGE5C_FINAL_VERIFICATION.md` | This report. |

The frozen model file still hashes to `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`. Frozen Stage3 inference, features, threshold and `database.py` were not changed.

## Primary-path review

The customer route requires a prospective canonical mobile-money form in V4 mode, commits the financial row, canonical event, balance changes and pending V4 state, then calls `v4_primary.complete_committed()` for its second decision commit. `process_transaction_event()` returns from its V4 branch before Stage13/Stage14 inference. The pending processor enters its V4 retry branch before legacy processing or training. All four admin batch generators return HTTP 503 before writes in V4 mode; they are admin simulation routes and are not used by normal customer POST processing. No enabled customer or pending path silently falls back to Stage14 when `AML_PRIMARY_MODEL=V4`. Production mode still defaults to V1 unless an operator explicitly selects V4.

The intended rule-engine policy remains **unresolved**: `_RULE_ENGINE_ENABLED` currently defaults to `False`. The local runner requires an explicit `-RuleEngine On` or `Off` choice and sets it only in the isolated Flask process. It does not change the production setting.

## Exact local test command

From the project root, with ordinary database URL environment variables unset:

```powershell
& .\ml_v4\stage5c\run_live_primary.ps1 -InspectOnly
```

After reviewing `ml_v4/evidence/stage5c/interrupted_review.json` and only if it says `RECONCILED`, start an explicitly new fixture group with:

```powershell
& .\ml_v4\stage5c\run_live_primary.ps1 -Execute -StartNewAfterReview -RuleEngine On
```

The runner prompts for the restricted `v4_stage4t_runner` password. Before synthetic writes, it checks the exact local disposable URL, UUID `d441b7bb-43f6-11f1-a2d8-0a0027000005`, principal/grants, six capture triggers, unchanged observation authority, `COMPLETE_VERIFIED` history, the idempotency column/index, the first four canonical/capture/result records, frozen model hash, test worker hash, and current `server.py` pin. It then uses the isolated Flask test client and Stage4T **test-only** worker for two real-model transactions and one injected inference-error transaction. It checks balances, same-key and changed-payload retries, canonical/capture/result row deltas, CTR, SAR-report isolation, alerts, post-commit event timing, Stage14 invocation count, dashboard/API authorization and Socket.IO subscription authorization. It records actual probabilities and classes in `ml_v4/evidence/stage5c/live_primary.json`. It does not force a suspicious label: if both classes are not observed, it records `PARTIAL` and exits nonzero. Inspect the evidence before rerunning because a partial run may already have committed fixtures.

This test command never uses production `aml` or production credentials. The Stage4T result scope is validated as `stage4t-isolated-v1`; it is not represented as production inference authority. The wrapper does not execute a migration, restore or model change.

## Results actually obtained here

| Check | Result |
| --- | --- |
| Stage5C guards plus frozen integrity | **6 passed** |
| Stage4S-A harness tests | **6 passed** |
| Stage5A coordinator and Stage5B wiring | **13 passed** |
| Existing V4 shadow and Flask route suite, isolated process | **39 passed** |
| Python compilation and PowerShell syntax | **passed** |
| Frozen model SHA-256 | **passed** (`555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`) |
| User-run disposable MySQL preflight | **PASS in saved local evidence**: original four transactions/results, pinned UUID/principal, verified history and idempotency schema |
| First Stage5C fixture | **INTERRUPTED** after the financial commit boundary; current rows require read-only reconciliation |
| Actual V4 primary predictions, MySQL balances, alerts, CTR/SAR and latency | **NO LIVE RESULT** |

The offline Socket.IO test found a **security blocker**: `RealtimeBroker.publish('transaction', payload)` delivers the ordinary transaction event to an unauthenticated Socket.IO client. The customer transaction payload contains account, amount and AI risk fields. The separate `v4_shadow_result` subscription is staff guarded, but that does not protect the ordinary transaction event. The local runner captures transaction notifications inside the isolated process and does not establish safe production broadcast authorization.

An inference-error payment retry with the same request ID is payment-idempotent, but the stored terminal `inference_error` result is not reinferred by the current pending-only monitor. A reviewed staff/operator AML retry path remains necessary if errors must be resolvable through inference rather than manual review. The local runner tests this existing behavior without claiming an automatic AI retry.

## Activation decision

**V4 customer-primary mode is not ready for a separately approved production switch.** Required evidence and corrections are: a successful guarded disposable run with actual frozen inference and reviewed result JSON; explicit rule-engine policy; authorization of ordinary transaction Socket.IO events before exposing V4 risk data; and an approved way to resolve terminal inference errors. The four disabled admin generators do not block normal customer POST processing. A production schema/authority/activation review remains separate and was not performed here.
