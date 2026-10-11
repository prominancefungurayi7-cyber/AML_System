# Stage 4S-D live legacy connection verification

**Decision: C — BLOCKED; LOCAL EXECUTION REQUIRED. Do not activate V4 or replace V1.**

## Files created

| File | Purpose |
| --- | --- |
| `ml_v4/stage4sa/run_stage4sd_readonly.ps1` | Secure local password prompt and ordered disposable-database checks. |
| `ml_v4/stage4sa/stage4sd_live.py` | Read-only Flask test-client requests on existing transaction IDs 2–4, with live Stage 13/14 feature and prediction capture. |
| `ml_v4/stage4sa/stage4sd_v4_replay.py` | Read-only frozen V4 replay of existing transaction 4 and unchanged-state check. |
| `ml_v4/reports/STAGE4S_D_LIVE_CONNECTION_VERIFICATION.md` | This report. |

No production application source, frozen V4 component, Stage4R coordinator, Stage4T worker, Stage4S-A harness, model weight or threshold was modified. No database was modified and no financial fixture was submitted during preparation.

## Guarded local execution

From the workspace root:

```powershell
& .\ml_v4\stage4sa\run_stage4sd_readonly.ps1
```

The runner rejects ordinary database URL variables and enabled V4 shadow mode, prompts securely for `v4_stage4t_runner`, binds only `127.0.0.1:3306/v4_stage4s_disposable`, pins server UUID `d441b7bb-43f6-11f1-a2d8-0a0027000005`, runs the existing Stage4T identity/grants/authority/six-trigger check, then the two read-only modules. Its `finally` block clears the credential URL and password material. It neither resets the database nor calls the fixture runner.

The legacy module rechecks authority, trigger bodies, frozen V4 file hash and current history freshness. It requires the existing four transactions, four canonical events, eight capture changes, four valid V4 success rows and zero alerts. This exact state is a guard against accidentally probing an unrelated or altered test ledger. A private test-client-only GET route then makes three consecutive Flask requests over the **existing** transaction IDs 2–4. Each request uses a fresh pinned MySQL connection and a read-only transaction, exercises the real Stage 13 extractor and unchanged Stage 14 model, records the full 30-feature vector, query/error counts, probability, prediction and 0.35 threshold, and verifies connection closure at request teardown. It rejects zero fallback vectors and requires a genuine prior-history count. It also tests rejection of a missing current feature service. Database error types are included in failure evidence. Baseline counts are checked again afterward.

The V4 module hashes the frozen XGBoost file, checks threshold 0.50, performs a read-only `v1.infer(4)` replay against the existing history, compares its output with the stored shadow result, and checks that transaction, alert and shadow counts and the stored shadow body remain unchanged. This verifies that frozen V4 inference remains functional without producing a new shadow result.

## Checks actually performed here

| Check | Result |
| --- | --- |
| Python syntax for both modules | PASS |
| PowerShell runner syntax | PASS |
| Stage4S-C lifecycle and Stage4S-A harness offline tests | **7 passed, 0 failed** |
| Credential-free module launch in both pinned Python runtimes | Both import correctly and fail closed before a database connection. |
| Fresh MySQL identity, grants, authority, trigger and history check | **NOT RUN** — restricted credential unavailable in this Codex process. |
| Flask requests on disposable MySQL and actual Stage 13 feature values | **NOT RUN**. |
| Actual Stage 14 predictions and threshold observation | **NOT RUN**. |
| Fresh V4 replay and unchanged-state check | **NOT RUN**. |

No actual Stage 13 vectors, Stage 14 probabilities or new V4 replay probabilities are available to report. A credential-free dry launch is only a launcher check and is not counted as live verification. Local execution will write `ml_v4/evidence/stage4sd/legacy_live.json` and `v4_readonly_replay.json` if the checks reach those steps.

## Scope and remaining risk

This read-only plan uses a temporary test-only Flask GET route and existing committed rows. It exercises the same Stage 13/14 service construction used by the transaction handler with real disposable MySQL connections, but does **not** submit a new transaction or execute the transaction POST handler. A later approved fixture stage would be needed to prove that full POST path after the Stage4S-C repair. The existing four V4 shadow successes remain historical evidence until fresh local checks run. No conclusion of live repair success is justified yet.

**STAGE 4S-D PREPARED — WAITING FOR LOCAL EXECUTION AND APPROVAL.**
