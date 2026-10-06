# Frozen V4 inference — disconnected local service

This service implements the original Stage18 XGBoost pipeline, frozen by Stage23, with exactly 40 semantic fields, 42 encoded inputs and inclusive threshold 0.50. It adds no Flask routes, alerts, Socket.IO events or dashboard behavior.

## Runtime and invocation

Use the dedicated `ml_v4/.venv_inference_stage3` environment. The ordinary application environment is not modified. Versions are checked before deserialization; the loader rejects another environment prefix. Runtime files are copied offline from installed research distributions and hashed in Stage3 evidence, not represented as a historical wheel lock.

From the workspace root, an explicitly authorized local call for an existing canonical transaction is:

```powershell
.\ml_v4\.venv_inference_stage3\Scripts\python.exe -I -B ml_v4/frozen_inference/launch.py --transaction-id <actual-transaction-id>
```

The CLI uses the configured ordinary MySQL connection, starts a read-only consistent snapshot and closes it. Credentials and tracebacks are not part of the result. It performs no ingestion, attestation, persistence or application routing. There is no network listener. Do not expose this local administrative interface as a public endpoint.

An actual event must already exist within the original observation boundary and a current successful attestation must cover its source revision. Ingestion changes the source revision; the service does not automatically attest or grant itself permission to proceed. The current live scope was empty at Stage3 verification. Do not insert a transaction just to make this command succeed.

## Contracts

`service.infer(connection_factory, transaction_id)` is a trusted local API. It opens a request connection, verifies all six capture triggers, the original boundary, current revision and source freshness, and retrieves the complete scoped graph. It never accepts a browser-supplied history-status assertion. SQLite support is restricted to in-memory hand fixtures.

Each request creates a fresh frozen Extractor. Complete canonical rows are checked in order; replay stops after the requested full key. Future rows cannot affect that vector. No query edge cap or path approximation is used. Resource failures return technical errors; no truncated feature is used. Deployment throughput and large-graph latency are not certified.

The fixed original model and frozen sources are hashed before loading. Verified model bytes are loaded from memory to avoid a model hash/load race. The embedded saved preprocessor transforms exactly once; its finite 42-column output is passed to the embedded XGB classifier. No standalone transform is added to live inference. Predictions are serialized under a lock with one native thread; no request DB connection or mutable Extractor is cached.

`suspicious_probability` always means class1. A success returns binary `normal` or `suspicious_pattern`; failures have null prediction/probability and `inference_error`. All positives require human review. Normal is not a legitimacy certificate. JSON uses finite values only. Error codes include MODEL_INTEGRITY, MODEL_UNAVAILABLE, HISTORY_INCOMPLETE, EVENT_UNAVAILABLE, HISTORY_RESOURCE_EXHAUSTED, FEATURE_SCHEMA, FEATURE_INVALID, PREPROCESSING_ERROR, INFERENCE_ERROR and HISTORY_UNAVAILABLE.

This model identifies transaction patterns defined as suspicious within the synthetic research benchmark. It does not determine that money laundering has occurred.

## Trust and limits

The source/authority manifests and installed runtime are local trusted release assets; filesystem read-only deployment, least-privilege credentials and process supervision remain deployment work. These checks do not defend against an administrator changing both code and its manifest. Model serialization is trusted only after the fixed hash and source checks. Frozen development performance is not independent or real-operator validation.

The history claim covers only the canonical prototype boundary onward, not pre-boundary events or lifetime operator history. Capture schema checks are point-in-time; concurrent administrator DDL/tampering is outside this prototype custody model. Every request rechecks history and triggers. No checkpoint/cache optimization, automatic retraining, fallback model or V1 replacement is implemented.
