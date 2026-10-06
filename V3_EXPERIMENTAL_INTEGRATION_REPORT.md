# V3 EXPERIMENTAL INTEGRATION REPORT

**A — V3 EXPERIMENTAL INTEGRATION COMPLETE AND VERIFIED**

Temporary local synthetic testing only. V1 remains the production baseline. No V4 work, retraining, production database access, financial operation, production alert or regulatory report occurred.

## 1. Model discovery and selection

The chronologically latest V3 fit is `ml_v3/models/stage14_diagnostics/shuffle.joblib`, recorded last in `ml_v3/reports/stage14_fit_log.json`. Its bytes match the Stage 14 manifest. It learned shuffled labels and is unsuitable for general testing. D1–D4 exclude family supervision and are also diagnostic interventions. Stage 13 added-feature candidates exist, but its selection decision explicitly records `no_final_model=true`, no eligible candidates, and `stage11_reference_retained=true`.

This integration therefore explicitly uses the **retained full-task 32-feature Stage 11 HGB reference**, not the last diagnostic file by timestamp. The user was offered this selection during implementation; it was used as the stated default. No V3 model is promoted or described as production-approved.

| Item | Verified selection |
| --- | --- |
| Artifact | `ml_v3/models/stage11_candidates/s11_09_hist_gradient_boosting.joblib` |
| SHA-256 | `69b5e8a87b41f0b1ea383b4542d7969736033eb6b7c73a54ca5f53e7eff80271` |
| Estimator | HistGradientBoostingClassifier, binary classes `[0,1]` |
| Saved pipeline | Stage11Preprocessor(mode=`raw`) followed by estimator |
| Feature extractor | `ml_v3/src/stage10a_pipeline.py`, `extract` |
| Contract | `ml_v3/src/stage10a_contract.py`, `v3_stage10a_features_1` |
| Preprocessing implementation | `ml_v3/src/stage11_preprocessing.py` |
| Input | Exactly 32 finite float64 columns in frozen order |
| Threshold | **0.50**, from saved `stage11_search_plan.json`; positive when probability >= threshold |
| Seed/training | 20260928; frozen Train only; moderate sample weighting (positive 1.5, negative 1) |
| Core configuration | 200 iterations, learning rate .07, max depth 6, 31 leaves, minimum leaf 20, L2 1, no early stopping |

Artifact, extractor, contract, preprocessing and threshold-plan hashes are pinned in [manifest.json](experimental_v3/manifest.json). Loading fails on integrity mismatch, unexpected module location/schema or scikit-learn version mismatch. Only this local, verified joblib file is loaded; callers cannot supply a model path. No fit or learned-transform update is performed.

## 2. Exact feature compatibility and temporal semantics

[feature_schema.json](experimental_v3/feature_schema.json) lists every feature in exact order, dtype and declared sentinel. The adapter calls the frozen extractor directly and loads the saved preprocessing object. No V1 features, fabricated zeros, fitted imputation or V4 implementation is used.

The extractor orders by UTC timestamp then integer transaction ID, includes the current event only where the original contract specifies, and emits before state update. It retains its original recent/baseline windows, N3 topology path selection, and missing markers. The corrected **V3 Stage 10A** growth feature itself requires 35 days and 12 baseline services; its displayed coverage still caps at 28 days. This is V3's frozen feature contract, not a substitution of V4 semantics. Frozen V3 target/evaluator discrepancies remain historical limitations.

Required request event fields:

```text
transaction_id, event_timestamp, sender_wallet, receiver_wallet,
amount_minor, currency, transaction_type, channel, agent_id,
serviced_wallet, agent_flow_direction
```

Amounts are positive integer USD cents; identifiers are positive integers below 2^53 for exact browser transport. Wallet/agent identifiers must use the `test_` prefix. UTC timezone information is mandatory. Transaction types are `cash_in`, `cash_out`, `wallet_to_wallet`; channels are `agent` or `direct_wallet`. Direct W2W has empty agent/serviced-wallet fields and flow `none`. Assisted W2W names exactly one serviced endpoint and has flow `none`. Cash names an agent and uses the same sender/receiver/serviced wallet, with flow matching its cash type.

The explicit `prior_history` field is mandatory. `[]` declares an actual synthetic cold start: the frozen extractor's documented missing sentinels are valid inputs, and the response lists unavailable features. Omitted/unknown history, malformed roles, duplicate IDs, future history or unsupported fields fail closed. History must precede the first batch event by the full key; batches must be increasing. Limits: 2 MiB request, 2,000 history rows, 100 current batch rows. Nothing is silently truncated. To use longer history, a separately reviewed resource-limit change is needed.

Risk scores, rule/ground-truth labels, alert outcomes and scenario metadata are rejected as extra fields. No history is fetched from production. The browser's synthetic-history attestation is not proof that arbitrary user-supplied values are genuinely synthetic; users must supply only test data.

## 3. Application audit

| Existing component | Finding |
| --- | --- |
| Entry point | `server.py`; Flask plus Flask-SocketIO |
| V1 service | `ai_stage14_model.py`, frozen GradientBoosting, 30 features, threshold .35 |
| V1 features | `ai_stage13_features.py`, database-backed history |
| Transactions | `/customer/transaction`, admin generation routes, `/api/v1/transactions`; `transactions.py` |
| Database | `database.py`; configured MySQL connection and financial/transaction/alert tables |
| Alerts/reports | Production processing creates alert/report effects and emits production events |
| Dashboards | `/dashboard` and role-specific routes/templates |
| Startup | Initializes database, demo state and background monitoring; includes legacy readiness paths |

The transaction table has account IDs, amount, type, channel, timestamp and agent ID, but no explicit serviced-wallet or agent-flow field. Its channel vocabulary also differs from V3. Inferring the serviced endpoint would be ambiguous for assisted W2W. Thus **live database-to-V3 compatibility is not approved**. The valid supported path is an independently supplied synthetic observable ledger.

Importing/running the ordinary server can initialize MySQL and background processes. The test branch executes before those imports/startup functions. It serves an isolated Flask application using the repository's template directory. It never mounts the production transaction, alert or report routes.

## 4. Architecture and changes

```text
server.py + explicit TEST_MODE=ON
  -> experimental_v3.web (loopback-only Flask/SocketIO)
  -> strict synthetic request validation
  -> frozen V3 extractor and saved pipeline
  -> caller-local JSON / isolated test socket event
  -> temporary browser display and synthetic history
```

Modified: `server.py` only, adding an early opt-in test launcher. Removing that added block reproduces the original file hash exactly. With test mode absent/OFF, the original V1 server executes unchanged. `AML_EXPERIMENTAL_MODEL=V3` alone does not replace production inference; both opt-in controls are required. WSGI imports do not activate the test launcher. Do not serve this test app through a public WSGI/proxy deployment.

Created:

- `experimental_v3/__init__.py`, `service.py`, `web.py`
- `experimental_v3/manifest.json`, `feature_schema.json`
- `templates/experimental_v3.html`
- `tests/test_experimental_v3.py`
- Reproduction, test, launch and preservation evidence under `experimental_v3/`
- This report

## 5. Start local experimental testing

From the repository root in PowerShell:

```powershell
$env:AML_EXPERIMENTAL_TEST_MODE = 'ON'
$env:AML_EXPERIMENTAL_MODEL = 'V3'
$env:AML_EXPERIMENTAL_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(32))"
$env:LOKY_MAX_CPU_COUNT = '2'
python -B server.py
```

Alternatively use `.\.venv\Scripts\python.exe -B server.py`; both installed interpreters were tested. Required packages are already included in the application requirements; the verified scikit-learn version is **1.9.0**. Do not upgrade the model runtime without rerunning compatibility checks.

Open **http://127.0.0.1:5053/experimental/v3**. Retrieve the token from the launching shell's `$env:AML_EXPERIMENTAL_TOKEN` and enter it in the dashboard. Treat it as a local testing capability, not a production account credential. Do not put it in a URL, repository, screenshot or shared log. The server binds only loopback, with debug/reloader disabled. The verification server was stopped after its smoke test; none was intentionally left running.

The dashboard shows availability, exact candidate, feature compatibility and threshold. Load normal-intended, structuring, wallet-network or agent examples; edit and submit a JSON batch. Every example clears and supplies its own synthetic baseline. No example has an asserted ground-truth label or guaranteed prediction. Successful runs append to this tab's temporary history. For sequential tests use new increasing IDs/timestamps; resubmitting the same batch fails on duplicate IDs. Clear history or close the tab to discard it.

Stop with Ctrl+C. Restore defaults before launching the ordinary application:

```powershell
$env:AML_EXPERIMENTAL_TEST_MODE = 'OFF'
$env:AML_EXPERIMENTAL_MODEL = 'OFF'
Remove-Item Env:AML_EXPERIMENTAL_TOKEN -ErrorAction SilentlyContinue
```

## 6. API, authentication and authorization

`POST /api/experimental/v3/predict` accepts either `transaction` or `transactions`, plus `prior_history` and `synthetic:true`. Authenticate with the separate local tester bearer token, or the dashboard's tester session and `X-V3-CSRF` token. The token grants only the isolated testing capability. No production login/session or database account lookup occurs.

Example request body (a genuine declared cold-start fixture):

```json
{
  "synthetic": true,
  "prior_history": [],
  "transaction": {
    "transaction_id": 1,
    "event_timestamp": "2027-06-10T12:00:00Z",
    "sender_wallet": "test_alice",
    "receiver_wallet": "test_bob",
    "amount_minor": 2500,
    "currency": "USD",
    "transaction_type": "wallet_to_wallet",
    "channel": "direct_wallet",
    "agent_id": "",
    "serviced_wallet": "",
    "agent_flow_direction": "none"
  }
}
```

Send via an HTTP client with `Content-Type: application/json` and `Authorization: Bearer <local token>`. No secrets are included in repository examples. Success returns `status:success` and a `predictions` array containing model version, candidate, mode, prediction, class-1 probability (`confidence`), verified threshold, feature validity, unavailable-feature names, transaction reference/time and minimal observable context. Errors provide an explanation and `features_valid:false` for invalid inference payloads. An unavailable/incompatible model returns 503, never V1 fallback.

Prediction 0 means no suspicious pattern flagged; prediction 1 means a pattern requiring review. `confidence` is the saved estimator's class-1 probability, not calibrated certainty of laundering. No local explanation is invented. Available observations are shown without claiming they caused the prediction.

Remote addresses, forwarded/proxy headers, nonlocal hosts and cross-origin requests are denied. Dashboard sessions use a dedicated HttpOnly, SameSite=Strict cookie, separate random signing key and CSRF header; responses are no-store and cannot be framed. Use only direct local HTTP. Authentication is token possession for a local tester, not enterprise role-based identity management.

## 7. Test alerts and real-time interface

Positive predictions display **EXPERIMENTAL — NOT A PRODUCTION AML ALERT**, including reference, timestamp, model, probability and observable amount/type/channel. No alert table, customer balance, agent float, SAR/CTR or investigation record is touched.

The `/experimental-v3` Socket.IO namespace requires the authorized tester session plus CSRF value at connection. Submit `experimental_v3_predict` with the same synthetic batch envelope. `experimental_v3_prediction` is emitted only to that socket's SID, never broadcast and never under a production event name. The provided dashboard uses authenticated HTTP responses for immediate display; the isolated Socket.IO interface is also available and tested. It does not change any existing production Socket.IO contract.

## 8. Verification results

- **24 automated cases passed** using both the system Python and project virtual environment.
- All **15,000 saved V3 Validation probabilities reproduced exactly** in both environments; maximum absolute difference 0; fixed-threshold classifications identical.
- Real local `python -B server.py` test-mode launch and authenticated status request passed; model loaded at threshold .50 on port 5053. The process was then stopped.
- Tests cover artifact integrity/loading, raw preprocessing, 32-field ordering/dtype, missing-history rejection versus declared cold start, four unlabelled behavioural examples, chronological replay, equal-time ordering, future exclusion, forbidden label/score fields, probability/threshold agreement, invalid schema, authentication/CSRF/local access, OFF mode, production-module isolation and recipient-private Socket.IO events.
- V1 regression check: the original server bytes are exactly recovered when the opt-in launcher block is removed; V1 feature/model artifacts and services are unchanged. Production/MySQL end-to-end operations were deliberately not executed. This is not a claim that the entire legacy application test suite was rerun.

Initial test issues were corrected: an age fixture had fewer than 12 baseline services; the Socket.IO test client needed an explicit loopback test environment. An overly broad warning-to-error filter rejected a NumPy 2.5 joblib deprecation; version incompatibility remains fatal while ordinary deprecations remain visible. No model artifact or feature definition changed to make tests pass.

Verified runtimes: Python 3.14.3, scikit-learn 1.9.0; NumPy 2.4.3 (system) and 2.5.0 (project environment). Joblib emits NumPy 2.5 shape-assignment deprecation warnings in the latter. Windows core-count probing may warn when WMIC is unavailable; inference is explicitly constrained to one thread. These warnings did not change reproduced scores.

Evidence: [test output](experimental_v3/test_results.txt), [score reproduction](experimental_v3/score_reproduction.json), [virtual-environment reproduction](experimental_v3/venv_score_reproduction.txt), [launch log](experimental_v3/launch_smoke.log), [preservation](experimental_v3/preservation_verification.json).

## 9. Historical results and limitations

The retained reference's historical reused-Validation metrics include Macro F1 .9521, AP .9772 and ROC-AUC .9888 at .50. Those are selected synthetic development results, not new independent evaluation or real-world efficacy. V3 Stage 14 attributed 1,634/1,666 lost detections after growth removal to A1 and identified strong synthetic separability and frozen target/feature contract discrepancies. None is corrected by this integration.

The extractor's graph search can be expensive; this is bounded local testing, not a throughput-qualified service. Current request bounds may be too small for some dense histories; such requests fail rather than truncating. Supplied histories must be complete for the intended test; the service cannot detect omitted events. Empty history has explicit cold-start semantics, not invented history.

No direct production-record adapter is provided because required semantics are missing. The test application does not offer real balances, investigations or production dashboard workflows. Model-selection alternatives with expanded feature schemas require a separate explicit adapter review; they are not silently swapped in. No remaining blocker exists for the documented local synthetic path.

## 10. Preservation and decision

805 protected historical/input paths match their before hashes, and named Stage 16T challenge artifact hashes also match. The only authorized existing-file change is the `server.py` launcher block. No V4 generator, evaluator, data, labels, design, report or policy was modified. No V3/V4 sealed evaluation tree, challenge data, private salt or seed was accessed. V1 artifact bytes and inference path remain unchanged. Earlier hash manifests are preserved as historical records; they are not rewritten to pretend the now-authorized server change did not occur.

**A — V3 EXPERIMENTAL INTEGRATION COMPLETE AND VERIFIED**

This authorizes no promotion or research continuation. Use only the documented local synthetic testing path.

V3 EXPERIMENTAL INTEGRATION — WAITING FOR APPROVAL.
