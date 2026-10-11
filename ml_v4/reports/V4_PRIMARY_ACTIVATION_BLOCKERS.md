# V4 primary activation: remaining blockers

**Update:** The staff-controlled retry and closure code is now implemented offline. See [V4_PRIMARY_INFERENCE_ERROR_HANDLING.md](V4_PRIMARY_INFERENCE_ERROR_HANDLING.md) for the current contract, prepared audit schema and approval boundary. The older missing-retry analysis below describes the state before that implementation; the disposable and production schema/live gates remain open.

**Status: BLOCKED.** V4 was not enabled in production; no production database was accessed or changed. The user-run Stage5C attestation evidence reports sequence 9, `COMPLETE_VERIFIED`, eight transactions, eight canonical events, sixteen capture rows, and transaction 8 still `inference_error`.

## What the saved customer run proves

`ml_v4/evidence/stage5c/live_primary.json` records an HTTP 302 wallet transfer (transaction 6) with real frozen V4 normal prediction, probability `0.003931179642677307`, threshold 0.50, one canonical event, two captures and no alert. It records an HTTP 302 cash-in (transaction 7), V4 normal probability `0.008331581950187683`, an independent rule score of 45, an alert, SAR review flag and CTR-required flag. Both use `stage4t-isolated-v1` and report verified history. It also records transaction 8's explicit inference error and pending review state. The file ends `INCOMPLETE`; it does not contain its planned final balance, retry, dashboard, notification or Socket.IO checks. The later read-only reconciliation and attestation evidence establish eight committed records and history freshness, but do not fill in those missing application assertions. No suspicious **V4** prediction has been observed in the saved run; the rule-triggered alert on transaction 7 is not one.

Only missing customer checks should be pursued after reviewing current source and state. The saved interrupted review already reconciles final balances for transactions 6–8 (29,988.50 and 20,011.50), confirms unique request IDs and one canonical/two capture records per transaction. The saved live run records transaction 6's same-key HTTP 302 retry and changed-payload HTTP 409. It does not record transaction 8's same-key HTTP retry, the final post-commit notification count, or dashboard/Socket.IO assertions. Existing successful wallet and cash-in fixtures must not be repeated. A genuine suspicious V4 result may require a separately approved synthetic fixture; no prediction should be forced.

## Security correction

Previously `RealtimeBroker._local_deliver()` emitted ordinary transaction, alert and risk events to every connected Socket.IO client, including unauthenticated clients. It now sends these events only to socket IDs registered as staff. The application checks the user's **current database role** before registration and again on every delivery; revoked roles and unavailable authorization fail closed. Disconnect removes the socket. `/stream` now requires compliance or admin role, so its broker-backed SSE feed is not customer accessible. Direct user messaging uses separate private rooms and was not changed. The external Redis/Kafka `aml-events` channel remains an internal deployment trust boundary that needs deployment access review; this change does not authorize external consumers.

## Inference-error resolution

The current pending monitor processes only `pending_v4`. Transaction 8 is terminal `inference_error`, and `v4_shadow.process()` deliberately reuses any terminal stored result. Same-key HTTP retry safely avoids a second payment but cannot rerun V4. Existing staff dashboard/alert routes do not provide an explicit resolution or retry action for an error with no alert. **This requirement is not met.** No terminal result was overwritten or deleted. The one-result V4 table intentionally makes terminal errors immutable; the general activity log has no retry key, outcome relation or uniqueness guarantee. A direct retry against it would either erase the original error or leave an unaudited second prediction. That breaks the requested audit/deduplication contract, so implementation stopped at this safety boundary. A separately reviewed append-only attempt record with transaction/staff identity, idempotency key, outcome, lock and explicit closure state is required before a staff retry or closure route can be enabled. The original error must remain queryable. Until then, transaction 8 and analogous payments remain unresolved.

## Explicit rule policy and read-only checks prepared

The customer V4 pre-commit path now requires `AML_RULE_ENGINE_ENABLED=ON` or `OFF` as an explicit operator policy. Missing or mismatched policy raises before financial commit; the production default is no longer silently interpreted for V4. `ON` preserves independent AML rules alongside the V4 prediction; rule score and `rules_triggered` remain separate from `ai_risk_level`. The intended production choice is **not approved** by this report. The Stage5C runner still sets its isolated policy explicitly.

The new `ml_v4/production_readiness.py` performs only read-only MySQL statements against database `aml`, from an explicitly supplied host, UUID and runtime principal. It checks the actual principal, grants limited to `aml` with SELECT/INSERT/UPDATE, required idempotency index, six exact capture triggers, pinned observation boundary, issue-free fresh history and frozen model hash. The companion frozen-interpreter check verifies pinned package versions, asset hashes and threshold; it passed offline. V4 startup now rejects wildcard or missing Socket.IO origins; readiness requires an explicit HTTPS origin list. The checker cannot establish the reverse-proxy or external Redis/Kafka access controls, production notification behavior or the staff retry workflow, and is therefore a prerequisite report rather than an activation signal. **No production connection was made here.**

From the workspace root, the guarded disposable read-only completion command is:

```powershell
& .\ml_v4\stage5c\run_live_primary.ps1 -FinishReadOnly
```

It prompts for the restricted disposable password, checks the pinned database and history, rereads balances/counts/unique request IDs, and tests customer versus staff dashboard/API/socket access without a POST. It emits a synthetic local Socket.IO test event but no financial transaction. Historical notification timing cannot be recovered from the saved incomplete run. The isolated harness source pin was refreshed after reviewing the current `server.py` customer, security and rule-policy changes; the command itself has **not** run in this Codex process.

For production read-only prerequisites, an operator must know the actual host, server UUID, runtime account and MySQL principal. Run the command below and enter those nonsecret identities when prompted; the password is prompted as a secure string. Choose `On` or `Off` only after the independent-rule policy is approved:

```powershell
& .\ml_v4\run_production_readiness.ps1 -RuleEngine On -SocketOrigins 'https://your-approved-aml-host.example'
```

Replace the example HTTPS origin with the actual approved browser origin. PowerShell prompts for the nonsecret host, username, principal and expected server UUID, then securely prompts for the password. Use `-RuleEngine Off` only if that is the approved policy. This command was prepared but **not executed**. It never sets `AML_PRIMARY_MODEL=V4` and rejects an already active V4 setting.

## Production gates and shortest activation path

1. Decide and record the production rule-engine policy. `_RULE_ENGINE_ENABLED` currently defaults to `False`, while the disposable run explicitly selected rules `On`. Do not assume the test choice is the production choice.
2. Verify production `aml` **read-only** for the idempotency column and unique index, prospective canonical coverage, six exact capture triggers, the pinned `controlled-prototype-v1` observation boundary, an issue-free current graph and `COMPLETE_VERIFIED` attestation freshness. Frozen Stage3 `history.verified_snapshot()` explicitly requires database `aml`; the Stage4T disposable authority and its sequence-9 attestation cannot substitute for this production gate. Confirm deployment principal/grants, pinned inference runtime and model artifact hash. None of these production checks was performed here.
3. Provide an approved, auditable staff resolution/retry path for terminal V4 errors and verify it offline, then with separately approved disposable tests. Verify a real V4 suspicious prediction and the remaining Stage5C notification assertions without repeating successful fixtures. The isolated harness pin has been refreshed for read-only checks; new financial fixtures still require separate review.
4. Only after those gates pass, prepare an operator-controlled switch to `AML_PRIMARY_MODEL=V4`, keep V4 shadow mode off, verify the production binding immediately before the switch, monitor pending/error decisions and alerts, and retain an explicit operator rollback procedure. **No switch command was run or approved by this report.**

## Files and offline results

This continuation changed `server.py`, `ml_v4/stage4sa/harness.py`, `ml_v4/stage5c/run_live_primary.ps1`, `tests/test_stage5a_v4_primary.py`, and this report; it added `ml_v4/stage5c/finish_readonly.py`, `ml_v4/production_readiness.py`, `ml_v4/production_runtime_check.py`, `ml_v4/run_production_readiness.ps1`, `tests/test_v4_rule_policy.py`, `tests/test_v4_production_readiness.py`, and `tests/test_stage5c_finish_readonly.py`. The prior security correction changed `realtime.py` and `tests/test_stage5c_live_guards.py`. No frozen V4 artifact, feature, threshold or `database.py` changed. Focused primary, Stage5C, readiness and security tests: **33 passed**; the new regression confirms terminal errors remain immutable and cannot be reinferred by a payment retry. Existing V4 shadow/Flask route suite: **39 passed**. Python compilation and PowerShell parsing passed. The frozen-interpreter runtime/asset check passed; model SHA-256 remains `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`.

**Decision: BLOCKED for production activation.** Wait for approval before any production write or switch.
