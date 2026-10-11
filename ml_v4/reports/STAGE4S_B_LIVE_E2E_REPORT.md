# MODEL V4 — STAGE 4S-B LIVE END-TO-END REPORT

**Decision: C — BLOCKED; DO NOT ACTIVATE V4. LOCAL EXECUTION REQUIRED.**

## Execution and readiness

The dedicated `V4_STAGE4T_TEST_DB_URL` is absent from this Codex process. No connection to `v4_stage4s_disposable` was made in this stage. The previously recorded Stage4S-A `verification_live.json: PASS` is historical evidence, not a fresh Stage4S-B check. No financial fixture, Flask transaction, XGBoost inference, or latency measurement ran. V1 remains the operational primary model; V4 shadow mode was not enabled.

Run locally from the workspace root:

```powershell
& .\ml_v4\stage4sa\run_live_e2e.ps1
```

The runner prompts for the restricted password without echoing it, pins `v4_stage4s_disposable`, `v4_stage4t_runner`, and server UUID `d441b7bb-43f6-11f1-a2d8-0a0027000005`, then runs the approved Stage4T binding check, fresh live isolation/history verifier, and Stage4S-A readiness check before submitting any fixture. Those existing checks verify restricted grants, authority, six exact trigger bodies, pinned source/model/worker, empty financial ledgers, and the approved Flask harness. A failed check stops before fixture creation. Ordinary database URL variables and enabled V4 shadow mode are rejected. Credentials are removed from process environment in `finally`; the runner does not print them.

## Files created

| File | Purpose |
| --- | --- |
| `ml_v4/stage4sa/run_live_e2e.ps1` | Secure prompt and ordered, fail-closed local entry point. |
| `ml_v4/stage4sa/live_e2e.py` | Disposable synthetic accounts/agent and four real Flask transaction submissions; writes local execution evidence. |
| `ml_v4/reports/STAGE4S_B_LIVE_E2E_REPORT.md` | This report. |

No frozen model, feature, threshold, Stage3 inference, production Stage4R validator, or production database file was modified. No sealed evaluation data was accessed.

## Transaction and output status

The prepared cases are direct wallet transfer, agent-assisted wallet transfer, cash-in, and cash-out. The Python runner submits each to `/customer/transaction` through the isolated Flask test client. It records the actual transaction ID, canonical row, shadow status, prediction, suspicious probability, observation scope, history status, HTTP status, and request plus inference wall time in `ml_v4/evidence/stage4sb/live_e2e.json`. These fields have **no values yet** because the runner has not executed. It does not assign expected prediction labels.

| Verification | Stage4S-B result |
| --- | --- |
| Fresh MySQL identity, grants, triggers, authority, model integrity | Not run; local credential required. |
| Four Flask transaction cases and database commits | Not run. |
| Canonical creation, capture triggers, fresh history, XGBoost inference | Not run. |
| Shadow-result persistence and actual predictions | Not run. |
| Invalid inputs, duplicate requests, rollback, inference failure, timeout, malformed worker output, stale authority | Not run live. |
| V1/V4 alert separation, staff dashboard, Socket.IO authorization/data exposure | Not run live. |
| Production alert/SAR/CTR absence and production database isolation | No production access was made in this stage; live checks remain pending. |
| Transaction and inference latency | Not measured. |

## Remaining blockers

Local execution with the restricted disposable-database credential is required. The prepared fixture runner covers the four transaction paths and immediate canonical/history/shadow evidence; it does **not** yet certify the requested duplicate, rollback, injected inference failures, worker timeout/output, authorization, Socket.IO, or production alert/SAR/CTR checks. Those checks must be implemented and executed before a Stage4S-B pass can be claimed. A partial local run must be treated as incomplete even if its evidence file contains some case rows. Do not activate V4.

**STAGE 4S-B INCOMPLETE — WAITING FOR LOCAL EXECUTION AND APPROVAL.**
