# Stage 4S-C legacy database connection repair

**Status: offline repair verified; further live testing required. V4 remains inactive and V1 remains primary.**

## Root cause

Flask's `get_db()` opens a request connection and `close_db()` closes it at teardown. In `server.py`, `process_transaction_event()` creates a new `Stage13FeatureService` for that connection and calls `get_stage14_model_service(conn.stage13_service)`. The old getter returned the process-wide Stage 14 singleton after its first call, ignoring later supplied Stage 13 services. The singleton therefore retained the first request's closed MySQL connection. On subsequent requests, Stage 13 history queries raised `MySQL Connection not available`; `generate_features()` caught the error and substituted thirty zero features. Stage 14 could still produce a 0.35-threshold prediction from those fallback values.

## Change

Modified `ai_stage14_model.py` only in the Stage 14 service getter. The frozen Gradient Boosting model is still loaded once. Each call with a current Stage 13 service now receives a shallow request-local wrapper that shares the loaded model but binds its own feature service. The cached model service releases the first request's feature service. Calls without an explicit current service fail closed. No model weights, 0.35 threshold, feature definitions, scoring logic, or V4 code changed.

Added `tests/test_stage4sc_connection_lifecycle.py`. Its Flask test client issues three consecutive requests, each using a new in-memory SQLite connection closed at the end of the request. It exercises the actual Stage 13 extractor and Stage 14 prediction method with a model spy. Each request extracts the expected nonzero prior-transaction count (1.0), including after earlier connections close; all vectors have 30 columns. A second test checks that an unbound service is rejected. The test uses no MySQL connection or financial fixture.

## Before and after

| Condition | Before | After |
| --- | --- | --- |
| First request | Singleton holds first Stage 13 service | Request wrapper uses current Stage 13 service |
| Later requests | Singleton ignores new service and queries closed connection | Each request wrapper uses its current connection |
| Legacy model | Frozen Gradient Boosting, threshold 0.35 | Same model and threshold |
| V4 shadow | Separate frozen XGBoost, threshold 0.50 | Unchanged |

## Verification

`python -m pytest -q ml_v4/stage4sa/tests/test_harness.py tests/test_ai_explanations.py tests/test_stage4sc_connection_lifecycle.py` — **16 passed, 0 failed**. The focused Stage 13/14 and explanation tests alone passed **11/11**. These are offline checks; they do not prove a fresh live MySQL request series.

## Remaining risks and next gate

Stage 13 still intentionally catches other feature-generation errors and returns fallback zeros. This repair removes the confirmed stale-connection cause; a separate policy decision would be needed to change general fallback handling. Stage 14 model prediction still shares the same loaded model object across request wrappers, as before. Fresh local disposable-database testing is needed to confirm multiple real Flask transactions no longer emit the connection error and that V1 decisions use genuine Stage 13 features. This stage submitted no transactions, changed no database, and accessed no sealed evaluation data. It did not modify frozen V4, Stage3 inference, Stage4R, Stage4T, Stage4S-A, or production `aml`.

**STAGE 4S-C COMPLETE — WAITING FOR APPROVAL.**
