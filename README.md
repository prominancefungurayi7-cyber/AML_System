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

After database readiness passes and activation is approved, run from the project directory in PowerShell:

```powershell
$env:AML_PRIMARY_MODEL = 'V4'
$env:AML_RULE_ENGINE_ENABLED = 'ON'
$env:SOCKETIO_ALLOWED_ORIGINS = 'http://127.0.0.1:5000'
$env:V4_SHADOW_ENABLED = 'OFF'
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

Read-only review on 11 October 2026 found **18 users, 1,000 transactions and 804 alerts**. The capture journal contains **7,800 source deletions and 1,000 source inserts**, with no canonical events for those inserts. The existing authority returns **INCOMPLETE** (1,000 missing canonical counterparts; 846 backdated before the boundary). There are no persisted V4 results.

The UI and access checks can pass while inference is blocked. Do not activate V4 or execute a financial demonstration until authorized history recovery is complete. Do not fabricate canonical records, replace the authority, reset the boundary or bypass the frozen gate.

The existing running process needs a restart to load backend changes. No process restart, database repair, model training or financial test was performed by the UI cleanup.

## Presentation flow

1. Sign in as a customer: wallet balance, payment form and transaction history.
2. Sign in as compliance: alert queue, individual case, independent rules and recorded AI decision.
3. Open reports: SAR/CTR workflow records and transaction summaries. This prototype does not claim an external regulator submission integration.
4. Open admin: users, KYC, watchlist and configured model information.
5. Explain the post-commit boundary, idempotent request ID, history gate and audited retry. Demonstrate a real V4 decision only after an approved controlled payment has succeeded.

Browser dependencies are pinned and served locally from `static/vendor`; their license files are included. Customer, admin and compliance dashboards share navigation, themes and a single authenticated socket connection per page.
