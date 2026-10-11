# Stage 5B — V4 primary integration

**Final status: BLOCKED. Production V4 primary mode was not activated.** The customer path is wired behind an explicit `AML_PRIMARY_MODEL=V4` setting, but the four legacy batch generators cannot safely produce the canonical history required by frozen V4. No live MySQL end-to-end test ran in this Codex process.

## Files changed

| File | Change |
| --- | --- |
| `server.py` | Added an explicit V4-primary branch in transaction processing, pending-state persistence with independent rule/CTR handling, post-commit customer completion, pending-decision retry in the monitor, and pre-write guards on four incompatible batch routes. |
| `tests/test_v4_shadow.py` | Updated the extracted legacy-route fixture to supply the new mode function; legacy-mode expectations remain intact. |
| `tests/test_stage5b_primary_wiring.py` | Added offline mode, routing, commit-order and batch fail-closed checks. |
| `ml_v4/reports/STAGE5B_V4_PRIMARY_INTEGRATION.md` | This report. |

`v4_primary.py`, frozen Stage3 inference, frozen XGBoost assets, threshold, feature contract, `database.py`, and MySQL schemas were not changed.

## Actual integration result

When explicitly selected, a canonical customer transaction now records `pending_v4` and its independent rule/CTR state before the financial commit. Stage13/Stage14 is skipped. After that commit, the route calls the existing `v4_primary.complete_committed()` coordinator, which invokes the frozen V4 worker and applies the decision and any AI alert in a second commit. Transaction and balance notifications follow the commits. A failed worker or decision write leaves the payment committed and its AML decision pending or explicitly marked `inference_error`; it does not call V1. The pending monitor retries still-pending committed decisions without repeating the financial transaction. Existing request-ID uniqueness continues to guard customer retries. The coordinator already suppresses repeated decision effects.

The four admin batch routes now return HTTP 503 before database writes when V4-primary mode is selected. Their generators create legacy transaction rows without prospective canonical events; some label an agent cash-in as a transfer. Converting those rows into verified V4 history would require a reviewed mapping and route rewrite. Running Stage14 for them under V4 mode would violate the sole-primary requirement. The pending monitor also does not retrospectively classify old `Initiated` legacy rows under V4 mode. Thus **all six entry points are guarded against V1 fallback, but only the canonical customer path is integrated for V4 decisions**.

## Verification

| Check | Actual result |
| --- | --- |
| Stage5B wiring, Stage5A coordinator and existing shadow/route offline suites | **52 passed** |
| Frozen asset integrity tests | **2 passed** |
| Python compilation of changed Python files | **passed** |
| Disposable MySQL transactions, real XGBoost, alert/CTR/SAR/dashboard/Socket.IO verification | **NOT RUN** |

The restricted disposable MySQL URL and server-UUID environment binding are absent from this Codex process. No financial fixture was submitted, no production `aml` connection was made, and no actual V4 primary prediction or latency was measured here. The user-reported successful disposable idempotency migration is not a fresh verification by this process. The unchanged frozen inference source pins model SHA-256 `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`, 40 semantic features, 42 estimator columns and threshold 0.50; the frozen-asset tests passed. Earlier four live **shadow** predictions do not establish primary-mode behavior.

## Remaining production activation blockers

1. Provide prospective canonical events and safe two-commit handling for all four batch paths, or formally remove those paths from any primary-model transaction workflow. Reconcile old `Initiated` rows separately; do not silently convert them.
2. Run guarded local disposable MySQL tests using the restricted credential and isolated Stage4T authority. The Stage4T binding must remain test-only; production inference must use its own pinned authority. Verify real XGBoost output, balances, history, idempotency, alerts, CTR/SAR separation, authorization, failures, retries and notification order. The existing Stage4S-A harness source hash no longer matches changed `server.py`; its source review/pin must be refreshed before using it for new fixtures.
3. Confirm the intended operational rule-engine setting. The current application defaults `_RULE_ENGINE_ENABLED` to `False`, so independent rule scoring is disabled unless explicitly enabled. Validate it with V4 in disposable tests.
4. Plan and separately approve production schema prerequisites and activation. No production migration or model switch was performed.

**Stage 5B stopped with a genuine safety blocker: the full sole-primary workflow and live disposable verification are incomplete.**
