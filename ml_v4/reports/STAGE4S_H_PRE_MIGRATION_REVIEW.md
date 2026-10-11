# Stage 4S-H pre-migration safety review

**Decision: conditional readiness for a separately approved disposable MySQL migration. No migration or financial fixture was run. V1 remains primary; V4 production shadow mode remains off.**

## Scope and files

Inspected `tests/test_canonical_mobile_money.py`, `tests/test_canonical_history.py`, both Stage2 historical hash manifests, `test_stage17d_integration.py`, `ai_stage13_features.py`, `ai_stage14_model.py`, `server.py`, `realtime.py`, `database.py`, `transaction_idempotency.py`, `ml_v4/stage4sg/mysql_migration.py`, `ml_v4/test_binding/v1.py`, the Stage4S-G report, and saved Stage4S-B/Stage4S-D evidence and reports. The saved four-transaction state is a preflight expectation, not a fresh database observation in this review.

Changed only these files in Stage 4S-H:

| File | Change |
| --- | --- |
| `test_stage17d_integration.py` | Close the fixture's SQLite connection before deleting its temporary file. |
| `tests/test_stage4sh_frozen_integrity.py` | Add a current frozen-asset gate while pinning the unchanged historical manifests. |
| `ml_v4/stage4sg/mysql_migration.py` | Strengthen the unexecuted migration with exact existing-row counts and before/after row digests. |
| `tests/test_stage4sh_migration_review.py` | Offline test that the row guard detects changed rows and count drift. |
| `ml_v4/reports/STAGE4S_H_PRE_MIGRATION_REVIEW.md` | This review. |

No historical manifest, frozen `database.py`, V4 model, Stage3 inference, production notification logic, or database was modified.

## Historical hash assertions

Both failures compare today's `ai_stage14_model.py` with its Stage2/Stage2A snapshot hash `1923878f2ead241f168e0f556595a86dd3f89fe2fecae2759782a17cf5fb0e9d`; the approved Stage4S-C connection repair changed its current hash to `e7c86f760055c15dd240e10699a62559ffec9f84449115360872413f6f490997`. The assertions also cover other application files that later approved stages can change. They remain valuable as historical snapshot evidence but are obsolete as unqualified current-tree gates. Their source and manifests remain untouched. The new test confirms the original manifests' bytes and validates current frozen V4 and history-authority assets plus the legacy model artifact. A future test-policy change may explicitly mark the two old whole-tree assertions historical, without rewriting their evidence or treating their failure as a frozen-model mismatch.

## Windows SQLite teardown

The Stage17D fixture yielded an open `DatabaseAdapter`/SQLite connection, then tried `os.remove(db_path)` in `finally`. Windows retains a lock on that file until the connection closes, causing all 16 teardown `PermissionError`s. The fixture now closes its connection before deletion, including partial setup failures. The 16 tests pass. No transaction business logic changed.

## Notification ordering

`create_transaction()` calls `process_transaction_event()` inside its transaction, then updates balances and commits. With its default `emit_events=True`, `process_transaction_event()` publishes `transaction`, `alert`, `ctr_report`, and `stats` **before commit**. The effective `broadcast_event()` forwards to `RealtimeBroker.publish()`, which immediately delivers to local SSE/Socket.IO subscribers and starts Redis/Kafka publication. If a subsequent balance update or commit fails, database rollback can leave clients with a transaction, alert, CTR, or statistics notification for data that never committed. The route's later balance and statistics notifications follow commit; statistics can also be emitted twice on a successful request.

The smallest subsequent production correction is to call `process_transaction_event(..., emit_events=False)` from the customer route and publish the committed transaction/alert/CTR rows and one statistics event only after successful commit, before the post-commit V4 hook if V1 notification latency matters. Add rollback/no-event and success/single-event tests. This review **does not change** notification logic. Other routes calling `process_transaction_event()` and other report publication paths need their own ordering audit before a system-wide guarantee; a transactional outbox would address delivery reliability beyond rollback safety.

## Disposable migration review

The prepared script imports only the Stage4T test binding. That binding accepts only `v4_stage4s_disposable` through the dedicated test URL, requires principal `v4_stage4t_runner`, checks actual `DATABASE()`, `CURRENT_USER()`, exact server UUID `d441b7bb-43f6-11f1-a2d8-0a0027000005`, and rejects grants outside that database. The script requires its authority file and matching UUID environment pin, verifies all six exact capture triggers, observation boundary, `COMPLETE_VERIFIED` history, InnoDB, and absent request-ID schema. It requires explicit `--apply --expected-transactions 4`; merely importing it performs no connection or DDL.

The reviewed DDL is one additive `ALTER TABLE transactions`: nullable ASCII/binary `client_request_id CHAR(36)` and unique index `(sender_account, client_request_id)`. Existing rows remain NULL; `database.py` is unchanged. The strengthened preflight requires exactly four transactions, four canonical events, eight capture rows, four shadow results and zero alert/SAR/CTR rows, then digests all rows in those tables. After DDL it rechecks schema, triggers, boundary/history, counts and old-column row digests. This is deliberately strict: changed disposable state requires a new review, not an automatic baseline update.

**Limit:** MySQL DDL implicitly commits. A failure during or after `ALTER TABLE` cannot be undone by the script's final rollback. It stops and requires manual read-only inspection; rerunning fails if the column/index already exists. The script has not been tested against current MySQL state or concurrency here. The counts and trigger/grant checks remain claims about what the guarded script will verify locally, not fresh verification in this session. A separate authorized local execution should capture a backup and run the guarded preflight on the pinned disposable server before applying DDL. No production migration is approved by this report.

## Offline test results

| Test | Result |
| --- | --- |
| Stage17D plus new frozen/migration and Stage4S-G contract tests | **22 passed** |
| Stage4S-A harness, Stage4T binding and Stage4S-C lifecycle tests | **19 passed** |
| V4 shadow tests in an isolated pytest process | **39 passed** |
| Canonical mobile-money/history suites, complete | **78 passed, 2 failed** on the historical Stage14 source hash |
| Same canonical suites excluding exactly those historical assertions | **78 passed, 2 deselected** |
| Python compilation of changed Python files | **passed** |

An initial combined run of V4 shadow and other suites gave **57 passed, 1 failed**: `test_no_ordinary_ml_imports` saw an ML module imported by another suite in the same pytest process. Its isolated rerun passed **39/39**. This assertion depends on global import order; it is not evidence of a V4 transaction regression, but combined-suite collection needs a process-isolated test policy or a revised import assertion.

## Remaining risks and next action

Pre-commit ghost notifications remain possible and should be repaired before production rollout. The migration has no MySQL execution evidence, and its implicit-commit failure mode demands a verified backup and operator review. Historical whole-tree hash tests remain expected failures until test policy is separately updated. MySQL unique-index behavior, concurrent duplicate requests, and idempotent retry behavior still require separately approved disposable live tests.

**Next action:** obtain separate approval for a guarded, backup-backed local migration of only `v4_stage4s_disposable`, first confirming the exact pinned identity and existing four-transaction state. Then run the approved disposable idempotency tests. Do not activate V4 or replace V1.

**STAGE 4S-H REVIEW COMPLETE — WAITING FOR APPROVAL.**
