# MODEL V4 — STAGE 4S COMPLETE MYSQL END-TO-END VERIFICATION

**C — ACTIVATION BLOCKED BY INTEGRATION FAILURE**

The mandatory isolation gate failed before database access. The approved Stage3 connector and history verifier are bound to the database name `aml` and the original Stage2A2 observation boundary. The Stage4 worker imports that connector and independently enforces the same boundary. A separate disposable database is rejected by the existing implementation. No safe test binding was established.

Per the request to stop if safe database isolation cannot be established, no database was created, connected to, reset or populated; no application startup or financial fixture was executed. V4 was not enabled. This decision identifies a test-environment integration blocker, not a measured model failure or a failed completed transaction test.

## 1. Implementation and integrity verification

Read-only inspection covered the server post-commit hook and startup behavior, shadow coordinator, isolated worker, approved connector/history gate, canonical history entry points, dashboard hook and saved Stage4R schema/test evidence. The Stage4R manifest and inherited preservation records supplied explicit expected paths.

**524 named protected paths match**, including **all twelve recovered Stage3 files** against their original historical hashes. The original Stage18 model hash remains:

`555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`

The frozen model, Stage17 extractor, feature specification, embedded preprocessing and research artifacts were hashed without loading models. The existing contract remains 40 semantic fields, 42 estimator columns and inclusive threshold 0.50. No training, tuning, generation, calibration, schema promotion or historical report rewrite occurred. No sealed tree was enumerated or accessed.

Evidence: [verification record](../evidence/stage4s/verification.json), [read-only verifier](../evidence/stage4s/verify.py). Named-path preservation is not a claim about every file on disk.

## 2. Database isolation failure

| Boundary | Observed implementation |
| --- | --- |
| Stage3 connector | `ml_v4/frozen_inference/cli.py:connection` accepts only a MySQL URL whose path is `/aml`, then connects with `database='aml'`. |
| Stage3 MySQL history gate | `history.py:verified_snapshot` requires `SELECT DATABASE()` to equal `aml`. |
| Observation boundary | The history gate compares immutable scope fields and membership against the historical Stage2A2 `observation_boundary.json`. |
| Production shadow worker | Imports the approved connector and checks that same historical boundary before reassessment. |
| Flask test configuration | A testing configuration alone does not establish a separate worker database or credential boundary. |

The verifier executed **only the actual parsed connector guard** using a synthetic URL with database name `v4_stage4s_disposable`. It raised its rejection before any connection could be made. This check did not import the application, read credentials, invoke MySQL or mock an end-to-end success.

No test-only database account, restricted grants or independently verified test server was established. MySQL availability, provisioning privileges and possible external disposable servers were not assessed. The blocker is the current approved path's inability to accept the required separate database and test observation identity; it is not evidence that this machine cannot host MySQL tests.

Creating fixture tables in the existing `aml`, changing its boundary, editing historical boundary evidence, spoofing `SELECT DATABASE()` or disabling freshness checks would not meet the requested isolation proof. None was done. Merely creating another schema would not resolve the two runtime checks or the historical boundary binding.

## 3. Application workflow and predictions

| Required transaction | Stage4S result |
| --- | --- |
| Direct wallet-to-wallet | NOT RUN — isolation gate blocked |
| Agent-assisted wallet transfer | NOT RUN — isolation gate blocked |
| Cash-in | NOT RUN — isolation gate blocked |
| Cash-out | NOT RUN — isolation gate blocked |

There are no Stage4S model predictions, parent commits, canonical sidecars, journal entries, attestations or V4 result rows. The source shows the shadow hook after the customer transaction commit, but static ordering does not certify the full real-MySQL workflow.

The full server was not imported: its startup reaches database initialization, seeding and legacy model readiness, and the customer path contains a legacy training thread. Any later real-application test harness must prevent training and isolate startup effects while retaining the actual route and MySQL transaction behavior. Stage4R's extracted-handler fixtures are not substituted for that requirement.

## 4. History and failure cases

First-event cold start, fresh reassessment, stale history, missing canonical event, incomplete history and concurrent source changes were **not rerun against MySQL**. The current source retains deterministic Stage2A reassessment followed by Stage3 freshness checks. No COMPLETE_VERIFIED value was forced and no observation boundary was reset.

Rollback, duplicate requests, concurrent inference, worker timeout, model integrity failure, invalid output, restart and pending recovery likewise remain **NOT RUN in Stage4S**. The connector rejection is the only newly executed behavior check. No inference failure was persisted or displayed as normal.

## 5. Persistence, dashboard and security

Stage4R's preserved migration evidence records an additive `v4_shadow_results` table with composite transaction/model/feature identity, unique inference ID, nullable probability and dedicated result JSON. **Current deployed schema and grants were not reverified** because no database connection occurred in Stage4S.

The separate compliance panel and staff-only shadow paths remain byte-identical to Stage4R. Their prior tests covered authorization, decision wording and exact string ID transport. Stage4S did not exercise browser rendering, real application login, V1 alerts, transaction events or MySQL-backed result retrieval. No new claim of dashboard or operational readiness is made.

No implementation file was changed. V4 has not been enabled or connected to ordinary operational alerts; no V1 scores were modified by this work.

## 6. Performance

Transaction latency with the isolated worker enabled is **NOT MEASURED**. The existing hook runs synchronously after commit and the worker timeout is 60 seconds, so delay remains a concrete concern. That timeout is not a measured response time. There is insufficient evidence to classify synchronous latency as acceptable or unacceptable for controlled use. No history truncation or feature optimization was attempted.

## 7. Regression, preservation and corrections

The saved Stage4R logs still report 25 shadow tests and 54 Stage3 tests passed. Those are **historical results, not fresh Stage4S regression runs**. Stage3, Stage4R and application regression reruns were not performed after the mandatory isolation stop. Frozen artifact integrity checks did run and passed.

No code correction was applied. New writes are confined to this report and `ml_v4/evidence/stage4s/`. Existing evidence, source, models, data and fit ledgers remain unchanged. [Decision manifest](../evidence/stage4s/decision.json) binds the new outputs.

## 8. Required resolution and decision

Before another test attempt, provide a supported isolated test binding for the application and child worker: an explicitly named disposable MySQL database, test-only credentials with grants restricted to that database, verified server/database identity before writes, and a separate test observation authority. This requires a reviewed versioned adapter or amendment of the deployment binding while preserving the frozen model/extractor/preprocessor and causal history/freshness rules. The exact recovered Stage3 source and historical manifests should remain preserved under their current identities.

Once that binding is available, verify actual database identity and grants, then execute the requested four-form workflow, history/failure cases, security checks and latency measurements. These are outstanding requirements, not authorized automatic follow-on work from this report.

**C — ACTIVATION BLOCKED BY INTEGRATION FAILURE**

Stage4S has not established readiness for controlled shadow activation. V1 remains primary. No ordinary V4 activation, operational alerting or later stage began.

STAGE 4S COMPLETE — WAITING FOR APPROVAL.
