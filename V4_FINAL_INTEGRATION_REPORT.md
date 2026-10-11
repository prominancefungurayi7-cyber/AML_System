# V4 final integration report — 2026-10-11

**Status: NOT ACTIVE in the inspected application environment. Production activation is unverified and was not performed.** No production write, migration, payment, restart, or configuration switch was made.

## Actual startup and configuration

The deployment entry point is `server:app`: `Procfile` runs `gunicorn --bind 0.0.0.0:$PORT --worker-class gthread --threads 8 -w 1 --timeout 300 server:app`; `Dockerfile` uses the same entry point with `${PORT:-5000}`. `railway.json` sets `/health` as the deployment health check. `server.py` loads `.env` and selects `ProductionConfig` unless `FLASK_ENV=development`. `config.py` resolves the database from `DATABASE_URL`, then `MYSQL_URL`, then its local MySQL default. The checked shell has none of the deployment URL, V4, rule-policy, origin, or Railway public-domain variables set. The workspace `.env` points to local `mysql://127.0.0.1:3306/aml` (credentials omitted). No approved HTTPS application origin is present.

## Verified database identity and readiness

A read-only connection using the workspace `.env` succeeded: database `aml`, endpoint `127.0.0.1:3306`, login `aml@localhost`, authenticated principal `aml@127.0.0.1`, server UUID `d441b7bb-43f6-11f1-a2d8-0a0027000005`. Its grants include `ALL PRIVILEGES` on `aml`.*. This UUID is the saved **Stage4T disposable** test UUID and its history authority is `stage4t-isolated-v1`. It is not verified production identity and must not be used as production authority. The actual production database host, authenticated principal, server UUID, grants, observation authority, schema, history freshness, backup/recovery state, and approved application origin are not accessible from this workspace. Accordingly, the existing `ml_v4.production_readiness` check was not run against this disposable server as if it were production; production readiness is **NOT PASSED**. Whether a production schema or history migration is needed is unknown until that read-only check runs. No migration is proposed or authorized now.

The current `server.py` and `realtime.py` SHA-256 values match the source pins in `ml_v4/production_readiness.py`. The frozen model SHA-256 matches `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`. These are local integrity checks, not production application tests.

## Integration and tests

The existing Stage5B path selects V4 with `AML_PRIMARY_MODEL=V4`, requires explicit `AML_RULE_ENGINE_ENABLED=ON|OFF`, and requires explicit Socket.IO origins. Customer transactions commit before `v4_primary.complete_committed`; the V4 branch returns before Stage13/Stage14 inference. An inference failure remains an explicit `inference_error` without a fabricated prediction; the staff retry path and append-only audit are present. Four unsupported legacy batch generators return HTTP 503 in V4 mode. The saved disposable evidence shows normal V4 predictions, an independent rule alert, and successful transaction 8 inference-error recovery. These completed tests were not repeated. A suspicious V4 prediction and the actual production Flask/customer/compliance/notification flows remain **untested in production**.

In the inspected environment, `AML_PRIMARY_MODEL` and `AML_RULE_ENGINE_ENABLED` are unset. Consequently, the legacy Stage14 customer branch remains selectable and V4 is **not** the sole active ML model. V4 does not silently fall back to Stage14 once explicitly selected; removing the legacy branch before approved activation would change the currently running behavior and was not done.

## Blocker and next action

The single blocking action is to run the existing **read-only** production readiness gate from the real deployment context, using the actual `DATABASE_URL` or `MYSQL_URL`, actual approved HTTPS origin, and credentials already configured there. Discover the authenticated principal and server UUID by read-only SQL (`SELECT DATABASE(), @@server_uuid, CURRENT_USER()`), then bind those observed identities to the guarded checker. Do not substitute the local disposable UUID or history. The checker currently expects a separately supplied runtime account and rejects a simultaneous database URL, so the connection identity must be resolved from the real deployment configuration before invoking it. If that check finds a schema/history gap, prepare only the specific guarded migration, verify an existing usable backup and recovery path, and seek explicit approval before any production write. If all gates pass, seek explicit approval for the production setting and restart: `AML_PRIMARY_MODEL=V4`, `AML_RULE_ENGINE_ENABLED=ON`, and `SOCKETIO_ALLOWED_ORIGINS=<verified approved HTTPS origin>` on the `server:app` deployment. There is no safe exact activation command with an invented origin or unverified production target.

## Rollback

If activation later causes a problem, stop new payment intake, preserve committed payments and V4 audit/history records, and explicitly restore the previous deployment configuration and restart `server:app`. Do not automatically route failed V4 inference to Stage14 or replay payments. Reconcile any `pending_v4` or `inference_error` transactions through the existing audited staff process before resuming intake. This procedure requires the actual deployment configuration and recovery controls to be confirmed at the production gate.
