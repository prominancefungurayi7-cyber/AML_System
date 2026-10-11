# V4 local integration — 2026-10-11

**Status: BLOCKED pending approval for the guarded local `aml` schema migration. V4 is not active.** No database DDL, payment, financial test, or Flask startup was executed.

## Local identity and checks

- App entry point: `server.py` for local `python server.py`; it serves `http://127.0.0.1:5000` (README and source). `server:app` is the WSGI entry point. Flask loads `.env`; the configured database is `mysql://127.0.0.1:3306/aml` with credentials omitted.
- Read-only MySQL identity: database `aml`, server UUID `d441b7bb-43f6-11f1-a2d8-0a0027000005`, authenticated principal `aml@127.0.0.1`, MySQL 8.0.46. This is the **local `aml` schema**, not `v4_stage4s_disposable`. Sharing a server UUID with the disposable schema does not make its history authority applicable to `aml`.
- `aml` has 7,800 existing transactions, 18 users, 415 alerts, no post-boundary canonical events, six expected capture triggers, and one `controlled-prototype-v1` attestation. The live read-only assessment reports `COMPLETE_VERIFIED` and fresh; the scope matches the pinned `aml` observation boundary. No disposable authority was copied.
- Required schema gaps: `transactions.client_request_id CHAR(36)` and unique `(sender_account, client_request_id)` index are absent. `v4_primary_attempt_events` and its two append-only triggers are absent. These are required for payment idempotency and staff V4 error retries. No other schema/history migration was identified.
- Frozen model hash matches `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`. The frozen inference runtime check passed with threshold `0.50`; no model file was changed.

## Recovery and prepared change

A consistent `mysqldump` of local `aml` was saved at `data/local-v4-backups/aml-pre-v4-20261011-221547.sql` (6,145,863 bytes; SHA-256 `c50820b9582d9523e2f777c601b1ef268bcf5dc01083871fc0df01cd7dd59c7d`). It contains the transaction, history, and trigger definitions and one-row inserts covering 7,800 transactions, 18 users, 415 alerts, and the history attestation. It is ignored by Git. **A restore rehearsal has not been performed**, so recoverability is supported by a structurally checked dump, not a proven restore.

`ml_v4/local_aml_migration.py` prepares only the missing idempotency column/index, retry audit table, and two append-only triggers. Its read-only preflight passed against the current `aml` identity, boundary, capture triggers, fresh history, frozen model, and backup hash. It requires `--apply` to execute DDL and stops if any expected missing object already exists. MySQL DDL commits implicitly: on any failure, inspect the actual schema read-only and do not blindly rerun. The existing disposable migration script is not used as an application database target.

One small startup change makes `ensure_ai_model_ready()` skip legacy model bootstrapping when V4 is selected. This prevents cold-start V1 training in V4 mode. Existing rollback assets remain. Static source review confirms the Stage5B customer V4 branch returns before Stage14; independent rules remain separately represented, and unsupported legacy batch routes return 503 in V4 mode. No local Flask or financial end-to-end checks have run yet because startup initializes database state and activation requires approval.

## Approval boundary and next actions

The next action is explicit approval to run this local-only DDL, after stopping local Flask/payment intake and accepting that the dump has not been restore rehearsed:

```powershell
& .\.venv\Scripts\python.exe -m ml_v4.local_aml_migration --backup data/local-v4-backups/aml-pre-v4-20261011-221547.sql --backup-sha256 c50820b9582d9523e2f777c601b1ef268bcf5dc01083871fc0df01cd7dd59c7d --apply
```

After successful schema and fresh-history verification, request separate approval to activate with `AML_PRIMARY_MODEL=V4`, `AML_RULE_ENGINE_ENABLED=ON`, and `SOCKETIO_ALLOWED_ORIGINS=http://127.0.0.1:5000` in the local PowerShell process, then start `& .\.venv\Scripts\python.exe server.py`. Confirm the actual browser origin first; no listener was found on port 5000 during this inspection. The local `.env` was not changed. A controlled wallet transaction still needs explicit approval and reconciliation; use nonfinancial startup, interface, authorization, and model checks first.

## Rollback

Stop local Flask and new payment intake. Remove the three V4 environment settings from the launch process and restart the prior configuration explicitly. Preserve committed payments, V4 results, and retry audit. Do not automatically rerun failed V4 transactions through Stage14 or replay a payment. If DDL recovery is necessary, first inspect the partially applied schema and restore the verified backup to an isolated recovery schema; reconcile any commits since the dump before replacing `aml`. The dump is not a substitute for a tested restore.
