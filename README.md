# EpoCash AML workspace

A Flask/MySQL mobile-money research application with customer wallets, independent AML rules, analyst case review, reports and private messaging.

## Primary model

The supported V4 customer route commits a payment and its canonical capture records once, refreshes history verification using the existing authority, then runs frozen XGBoost in its pinned inference environment. The result or an explicit inference error is persisted. A failed AI step never replays the payment and never falls back to Stage14.

- Model: `v4.development.freeze.stage23.1`
- Contract: `v4.features.1`; 40 semantic features, 42 estimator columns
- Threshold: **0.50**
- SHA-256: `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`
- Independent rule findings remain separate from AI predictions.
- Existing historical AI decisions are historical records, not new V4 results.

V4 detects patterns from a synthetic research benchmark. It does not establish that money laundering occurred or certify that a normal transaction is legitimate. Analysts review positive results. Do not present benchmark probability as calibrated real-world risk.

## Local startup

Use the existing `.env` and existing MySQL database. Do not recreate the database or seed another dataset. Keep credentials out of source control and presentations.

V4 was activated and verified locally on 12 October 2026. To start it again when the application is stopped, run from the project directory in PowerShell:

```powershell
$env:AML_PRIMARY_MODEL = 'V4'
$env:AML_RULE_ENGINE_ENABLED = 'ON'
$env:SOCKETIO_ALLOWED_ORIGINS = 'http://127.0.0.1:5000'
$env:V4_SHADOW_ENABLED = 'OFF'
$env:CANONICAL_MOBILE_MONEY_ENABLED = 'ON'
& .\.venv\Scripts\python.exe .\server.py
```

Open http://127.0.0.1:5000. The Flask application and the pinned V4 environment (`ml_v4/.venv_inference_stage3`) are separate. Do not upgrade the frozen inference environment. The current V4 worker path is Windows-specific; a different deployment environment requires its existing readiness checks before activation.

The health endpoint shows model selection and rule policy, not successful inference. Confirm inference using a persisted V4 result for a committed canonical transaction.

## Review without changing the database

```powershell
& .\.venv\Scripts\python.exe .\tools\review_application.py
# Optional desktop/mobile browser review (Playwright and Microsoft Edge required):
& .\.venv\Scripts\python.exe .\tools\review_application.py --browser
```

The review skips startup, seeds and monitors. It pins the local database identity, restricts SQL to SELECT/SHOW inside read-only transactions, verifies role restrictions and private socket delivery, and compares protected data fingerprints. Browser requests use Flask's isolated test client; no live payments or messages are sent. Screenshots stay under ignored `.pytest_cache/ui-review/`. Exit code 0 means the review and history gate passed, 1 means an application check failed, and 2 means the history gate blocks V4.

Do not run the entire historical test directory against the local application database: some older tests initialize or clear data. Use isolated tests and the read-only review above.

## Current demonstration readiness

**V4 is ACTIVE.** Authorized recovery archived the 6,100 generated transactions and their alerts/audit evidence, then restored the verified 7,800-transaction baseline without changing the schema or history authority. The approved $0.01 customer transfer **14621** produced a genuine frozen V4 result: **normal**, suspicious probability **0.304357%**, threshold **0.50**. History is `COMPLETE_VERIFIED`.

At completion of the approved single-payment tests, there were **18 users, 7,802 transactions, 415 alerts and two persisted V4 inferences**. The approved admin generator test on 13 October 2026 created transaction **14622**, a **$17.74** demo transfer classified **normal** by frozen V4 (suspicious probability **0.465588%**). Balance reconciliation, fresh history, compliance visibility, progress reporting and same-request duplicate protection passed. Authentication, customer/compliance pages, reports and staff-only notifications also passed prior live checks. See [the final integration report](docs/V4_LOCAL_INTEGRATION.md) for configuration, evidence and safe rollback.

### Transaction generation

The admin generator defaults to **70% routine payment inputs and 30% suspicious-scenario inputs**, rounding towards routine payments for a single-payment request. Dedicated scenario modes remain available. Routine payers and payees have separate roles; routine payments no longer create reciprocal loops. Suspicious inputs combine repeated split payments and converging/onward wallet transfers, with agent cash activity when an active agent exists. All payments use current timestamps, existing demo wallets, available balances, canonical capture and post-commit V4 inference.

The input mix is **not a guaranteed prediction ratio or an accuracy measure**. The dashboard shows input intentions separately from persisted V4 normal/suspicious/pending/error counts. Independent AML rules remain enabled; rapid large batches can still trigger velocity alerts. Insufficient funds roll back the entire batch. Existing signed payment retries keep their original plan; unsubmitted forms from the old planner require a reload.

Nonfinancial checks on 13 October 2026 used the unchanged frozen V4 model, feature extractor and threshold. Against the current 102-event verified history, a hypothetical 100-payment plan produced **70/70 routine predictions normal**, and **13/30 suspicious-scenario predictions suspicious** (3 structuring, 10 network). These results are offline diagnostics, not committed payments or measured production accuracy. Agent growth behaviours need sufficient real history; choosing an agent scenario cannot guarantee a flag. No existing transaction or prediction was relabelled.

Scenario funding roles are selected from available demo balances and fixed in each signed request. The mixed plan combines near-threshold transfers with smaller repeated splits. Read-only balance projections passed for every supported mixed-batch size, including 5,000, against the current balances; this does not reserve funds or override the atomic insufficient-funds check.

Reproduce the nonfinancial check against verified local history:

```powershell
& .\.venv\Scripts\python.exe -B .\tools\check_v4_generation.py --local-history
```

The existing approved customer and generator payments remain evidence that the live V4 path works. The new mix has not been submitted as a live financial batch. Frozen assets, history authority and database schema are unchanged. Legacy generation and ledger clearing remain blocked to protect canonical history.

## Presentation flow

1. Sign in as a customer: wallet balance, payment form and transaction history.
2. Sign in as compliance: alert queue, individual case, independent rules and recorded AI decision.
3. Open reports: SAR/CTR workflow records and transaction summaries. This prototype does not claim an external regulator submission integration.
4. Open admin: users, KYC, watchlist and configured model information.
5. Show transaction **14621** and its persisted V4 result. Explain the post-commit boundary, unique request ID, history gate and audited retry without generating another dataset.

Browser dependencies are pinned and served locally from `static/vendor`; their license files are included. Customer, admin and compliance dashboards share navigation, themes and a single authenticated socket connection per page.
