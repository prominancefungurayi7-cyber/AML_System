# MODEL V4 — INTEGRATION STAGE 3 FROZEN FEATURE EXTRACTION AND INFERENCE SERVICE

**A — FROZEN V4 INFERENCE SERVICE READY FOR CONTROLLED APPLICATION INTEGRATION**

The disconnected local service implements canonical history → unchanged Stage17 extractor →40 semantic fields →embedded saved preprocessing →42 estimator columns →original Stage18 XGBoost →class1 probability →inclusive0.50 decision. **54 tests passed.** On128 fixed development examples, probabilities and preprocessing match the saved references exactly. No live application decision path was changed.

## 1. Frozen authority and preservation

Freeze `v4.development.freeze.stage23.1`, feature `v4.features.1`. The loader requires the original path `ml_v4/development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib` and SHA-256:

`555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`

It checks the freeze record, feature specification, preprocessing specification/source, extractor source and observable Event contract before deserialization. The model is loaded from the exact verified bytes in memory. Caller-supplied model paths, mtime selection, bootstrap and fallback models are absent. Stage22 A40 is not accepted as authority even if its bytes match. HGB,44-feature experiments,V1,V3 and legacy models are not used.

**450 named protected files** match their inherited hashes before and after, including prior reports, V1/V3/V4 artifacts, Stage16R data, labels, original matrices, model/fit ledgers and retained history implementation. Sealed files remain unread. The inherited broader historical archive gap and independent-custody restrictions remain unresolved. [Authority](../evidence/integration_stage3/authority_verification.json), [preservation](../evidence/integration_stage3/preservation_verification.json).

## 2. Isolated runtime achieved

Dedicated environment: `ml_v4/.venv_inference_stage3`, with system-site-packages disabled. The ordinary application environment is unchanged. Exact versions:

| Component | Version |
| --- | --- |
| Python |3.14.3 |
| NumPy |2.4.3 |
| scikit-learn |1.9.0 |
| XGBoost |3.4.1 |
| SciPy |1.18.0 |
| joblib |1.5.3 |
| threadpoolctl |3.6.0 |

Installed research distribution files were copied offline into the isolated environment; source/destination hashes were checked and **4545 distribution files** were verified again at completion. This is an installed-file snapshot, not an assertion of original wheel provenance. Supporting dependencies are narwhals2.22.1, mysql-connector-python9.7.0 and python-dotenv1.2.2; test-only dependencies are separately recorded. The initial isolated import failed closed because narwhals was missing, then succeeded after that installed dependency was copied. No model fallback or runtime-version relaxation occurred.

The loader verifies runtime versions and the dedicated environment prefix and rejects shadowed numeric-library origins. Fixed one-thread settings, estimator n_jobs1 and threadpool limits apply to inference. Calls are serialized around native prediction; each request has its own extractor/DB connection. [Runtime verification](../evidence/integration_stage3/runtime_verification.json), [package file hashes](../evidence/integration_stage3/runtime_files.json).

## 3. Service interface and loader

New implementation: [service.py](../frozen_inference/service.py), [history.py](../frozen_inference/history.py), [CLI](../frozen_inference/cli.py), [isolated launcher](../frozen_inference/launch.py). Importing the service does not deserialize a model. The trusted local `infer(connection_factory,transaction_id)` API produces one result; the CLI starts no listener and adds no application route.

After loading, checks require a two-step sklearn Pipeline, exact embedded FrozenPreprocessor class/source, full mode/no dropped or restricted fields, exact40 order and marker policy, exact42 encoded names, finite fitted imputer/scaler state, original60000 Train-fit count, XGBClassifier type/configuration,42 estimator inputs, classes `[0,1]` and predict_proba. Missing or incompatible assets produce MODEL_INTEGRITY/MODEL_UNAVAILABLE, never normal.

An explicit local invocation for a separately authorized actual canonical event is documented in [README](../frozen_inference/README.md). The launcher uses the dedicated interpreter with `-I -B`. There is no automatically running daemon, V1 replacement, alert creation, Socket.IO publication, dashboard change or operational risk blending.

## 4. Canonical history gate

Each call opens its own trusted connection and read-only REPEATABLE READ snapshot. It verifies all six exact CMM trigger definitions, including timing/events/tables and unexpected names; checks the original Stage2A.2 boundary against saved metadata; and uses the unchanged Stage2A assessment/freshness functions to verify current scope/source revisions and absence of unresolved gaps. The source and history modules are hash-bound before import.

UNKNOWN, INCOMPLETE, stale revision, missing trigger or incomplete graph produces HISTORY_INCOMPLETE before model loading. The service neither creates an attestation nor chooses its status. A newly ingested event requires a fresh authorized attestation for the changed source; no automatic self-approval exists. TRUE_COLD_START_VERIFIED entities can predict when the complete global scope is fresh. No35-day maturity requirement is imposed on genuine scoped cold start.

The snapshot includes all scoped canonical events and the complete W2W graph without per-wallet or edge limits. A fresh extractor replays full keys in order through the requested event, with current once and future keys excluded. Same-time IDs retain their frozen meaning. Invalid/duplicate ordering is rejected, never silently sorted away. Resource exhaustion produces a technical error rather than truncated history.

### Live scope check — read-only

At `2026-10-06T08:35:50.122085Z`, MySQL reported scope revision1, COMPLETE_VERIFIED, zero post-boundary canonical events and zero entities. The original boundary is `2026-10-05T21:14:03.854863Z`; the event watermark is null. The service gate returned EVENT_UNAVAILABLE for a deliberately nonexistent positive integer ID; that ID was not inserted. No feature vector or prediction was produced for live data. [Live check](../evidence/integration_stage3/live_history_check.json).

This completeness applies only to the controlled prototype boundary onward. It is not lifetime EcoCash history, real Econet operator history, pre-boundary financial completeness or independent custody. Freshness is source/scope revision freshness under Stage2A, not a new wall-clock TTL policy.

## 5. Frozen extractor and feature contract

The original extractor and observable-only Event/time contract are loaded by checked source identity without modifying their bytes. The contract lives under the generation directory but no generator or evaluator executes. Partition loaders, target labels, provenance, private activation metadata and training runners are not imported.

The structured matrix is exactly39 float64 fields plus one U16 transaction_type, in40-field order. IDs and timestamps remain routing/history metadata outside X. No rule score, alert field or operational risk is supplied. The wrapper validates dtypes, categories, markers, signed change ranges and NaN/Inf behavior. Only the frozen N4 funding-residual field admits raw NaN; valid signed values such as residual−1 and cash-skew-change−2 are preserved.

The unchanged formulas retain1h,24h,7d,28d,28d+1h,29d,35d and UTC-day boundaries, chronological simple return paths and funding anchors. No generic30-day substitution, shortest-path replacement or qualifying-path feature is introduced.

## 6. Embedded preprocessing and prediction

The service calls the saved embedded preprocessor transform exactly once, validates finite shape1×42, and passes that output to the saved embedded estimator. This exposes a check between the two original pipeline stages; it does not refit or double-transform. The standalone preprocessing artifact is deserialized only by the authorized parity test as a reference.

The estimator's verified class identity selects column1. Both probability columns must be finite and bounded, with total approximately1. `p(class1)>=0.50` yields prediction1/suspicious_pattern; otherwise0/normal. There is no confidence inversion, calibration, legacy-score mapping, behavioral blend or rule blend. Threshold boundary tests use stubs, not threshold optimization.

## 7. Development and fixture parity

Before evaluating results, the test selected64 evenly spaced original row indices per partition using `linspace(0,n−1,64)`. These128 fixed Train/Validation examples reproduce the original saved XGB probabilities with **maximum absolute difference0**, within the stated test tolerance1e−12. Embedded and standalone preprocessing outputs are exactly equal. The service's explicit embedded-stage path also equals the original pipeline.predict_proba output. No family metric, performance selection or new generalization claim was calculated. [Exact indices and parity](../evidence/integration_stage3/parity.json).

Hand-authored Stage17 fixture function bodies were reused unchanged through AST selection, avoiding the original module's partition-loader import. Loader-only cases and the mixed private/loader case were excluded; private-field rejection was tested separately in the service suite. Coverage includes all40 cold outputs, wallet windows/UTC days, network directions, N3 multi-hop path chronology/selection, N4 anchors/residuals, agent growth/concentration/burst/cash imbalance, incoming observation, same-time IDs and future invariance. [Fixture selection](../evidence/integration_stage3/fixture_reuse.json).

The final suite passed **54 tests**. It additionally checks path/hash/runtime/source/version failures before deserialization, invalid features/probabilities, single transform, stale and incomplete history, cold-start success, model-error handling, class1 meaning, concurrent request-local replay, resource exhaustion, connection cleanup, restart determinism, forbidden imports and artifact preservation. Fit methods on the pipeline, frozen preprocessor, imputer, scaler and XGB classifier are instrumented to fail if invoked during tests. Two fresh processes produce identical fixture feature bytes and probabilities. [Test output](../evidence/integration_stage3/test_results.txt), [all40 requested acceptance checks](../evidence/integration_stage3/acceptance_checks.json).

## 8. Result and failure contract

Every result contains status, inference_id, transaction_id (decimal string), event_timestamp, model_version, model_sha256, feature_version, prediction, suspicious_probability, threshold, decision, inference_timestamp, observation_scope, scope_revision, source_revision, history_status, history_complete_through and error_code. It also supplies contract_version, the warning, a human-review requirement on positives and the normal-result limitation. History fields unavailable on a failed gate remain null/UNKNOWN rather than being invented.

Success has status success and binary decision. Any technical failure has status inference_error, prediction/probability null and decision inference_error. Sanitized error codes distinguish integrity/runtime, history, unavailable event, feature, preprocessing, inference and resource failures; internal exception text is not returned. Output JSON contains no NaN. Database cleanup failure also clears any successful prediction.

> This model identifies transaction patterns defined as suspicious within the synthetic research benchmark. It does not determine that money laundering has occurred.

All positive results require human review. A normal result does not certify that a transaction is legitimate. Probabilities are uncalibrated synthetic benchmark outputs, not probabilities of criminal conduct.

## 9. Remaining limits and next gate

This local isolated service is technically ready for a separately authorized controlled application integration. It remains disconnected from `process_transaction_event`, V1 Stage14ModelService, operational scores, alerts, Socket.IO and dashboards. It does not persist inference results or provide a network endpoint. Read-only deployment permissions, supervised process lifecycle, least-privilege production credentials, authorized audience delivery and atomic outbox/UI integration are later work.

The exact runtime is verified locally; no portable signed image/wheel build is claimed. The trusted release manifests/code must be protected together; hashing cannot defeat an administrator who replaces both. Snapshot trigger checks do not establish independent custody or defend against concurrent administrator DDL tampering. No populated live-scope inference, production load/latency, large dense graph, failover or real-operator effectiveness test occurred. Full replay has unbounded workload-dependent cost; there is no truncation optimization.

Synthetic support deficits, reused Validation and Stage23 scientific limitations remain. Technical parity does not repair weak-family detection or certify production effectiveness. No live history was fabricated to bypass the empty scope.

## 10. Outputs and final decision

New service/test files are under `ml_v4/frozen_inference/`; isolated runtime files are under `ml_v4/.venv_inference_stage3/`; evidence is under `ml_v4/evidence/integration_stage3/`, plus this report. The [decision manifest](../evidence/integration_stage3/decision.json) binds code/report/evidence; runtime file manifests bind the copied dependencies. No protected prior artifact or ordinary application file was changed.

**A — FROZEN V4 INFERENCE SERVICE READY FOR CONTROLLED APPLICATION INTEGRATION**

V4 INTEGRATION STAGE 3 COMPLETE —
WAITING FOR APPROVAL.
