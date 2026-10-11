# Stage 5C live CTR compatibility repair

**Subsequent history-authority failure:** the later transaction-8 inference-error fixture left the test ledger without a matching latest attestation. Do not use the new-fixture command below until the read-only diagnosis and any separately approved authority action are complete. See [the history-authority diagnosis](STAGE5C_HISTORY_AUTHORITY_DIAGNOSIS.md).

**Status: code repaired; prior disposable run requires read-only reconciliation. No new financial fixture was submitted by this Codex process.** Production `aml`, frozen V4 assets, threshold and `database.py` were untouched.

## Cause and schema

The application-defined MySQL `ctr_reports` table has `id`, `reference_number`, `account_number`, `total_amount`, `transaction_count`, `filing_date`, `status`, `filed_by` and `filed_at`. `reports.create_ctr_report()` creates account/date aggregate reports; there is **no `transaction_id` foreign key**. The local MySQL error `1054 Unknown column 'transaction_id'` confirms that the running table rejects the assumed column. A fresh `SHOW COLUMNS` result from the live database is still needed; `-InspectOnly` now records it read-only.

`broadcast_committed_customer_transaction()` incorrectly selected a CTR by `transaction_id`. The V4 pre-commit branch also selected and inserted against that nonexistent column, which would have broken a cash-in at the CTR threshold. The fix removes those false transaction-to-report queries. The committed transaction continues to carry `ctr_required`; an aggregate CTR report is emitted only by its separate report workflow, where its actual ID is known. No report is fabricated or auto-filed to make the test pass. The legacy Stage14 branch still contains the same old CTR column assumption and needs separate review before relying on legacy cash transactions; this repair does not change that path.

## Prior-run evidence

`ml_v4/evidence/stage5c/live_primary.json` records a passing local preflight with four preexisting transactions, four canonical events, eight capture rows, four V4 results, zero alerts/SAR/CTR reports, the pinned disposable identity and `COMPLETE_VERIFIED` history. It has `cases: []` and `status: INCOMPLETE`. That file was written before the first case could be recorded and **does not establish the post-request row counts or V4 result**.

The reported failing notification function is called after the customer financial commit. Reaching it supports that the first Flask payment and its canonical event committed. The exact transaction ID, balance changes, V4 result and alert state remain unverified without a fresh database read. The runner's former per-case CTR count used the same invalid column and could also abort after the POST. No prior row was deleted, reset or retried here.

## Safe local reconciliation and resume

First run **read-only** from the project root:

```powershell
& .\ml_v4\stage5c\run_live_primary.ps1 -InspectOnly
```

The secure prompt uses only `v4_stage4t_runner` on `127.0.0.1:3306/v4_stage4s_disposable`. The inspector repeats UUID, principal/grant, trigger, authority, history, frozen-model, idempotency and original-four checks; runs `SHOW COLUMNS FROM ctr_reports`; discovers existing `S5C...` synthetic accounts; verifies each prior transaction's canonical event, two capture rows, final Stage4T V4 result, alert count and wallet balances. It writes `ml_v4/evidence/stage5c/interrupted_review.json` with `RECONCILED` or `UNRESOLVED`. It makes no MySQL changes. If it reports `UNRESOLVED`, stop and inspect that condition; do not submit another fixture.

Only after reviewing a `RECONCILED` result, an explicitly new fixture group may be run with:

```powershell
& .\ml_v4\stage5c\run_live_primary.ps1 -Execute -StartNewAfterReview -RuleEngine On
```

The second command re-reads the database and requires the same reconciliation fingerprint before creating unique new wallets and request UUIDs. It never reruns the old request IDs. `On` explicitly enables rules only in the isolated test app. It checks the transaction-level CTR flag and does not expect a `ctr_reports.transaction_id` row. A failed or partial new run again requires `-InspectOnly` before another attempt.

## Files and tests

| File | Change |
| --- | --- |
| `server.py` | Remove the invalid committed CTR lookup and V4 pre-commit CTR table queries; retain `ctr_required` on transactions. |
| `ml_v4/stage5c/live_primary.py` | Remove invalid CTR-per-transaction count; add read-only prior-run reconciliation, live CTR schema inspection and a matching-review gate before new fixtures. |
| `ml_v4/stage5c/run_live_primary.ps1` | Separate `-InspectOnly` from `-Execute -StartNewAfterReview`; retain secure prompt and isolated binding. |
| `ml_v4/stage4sa/harness.py` | Refresh the reviewed `server.py` hash pin to `0fe522e97ecdce0bd2c338b59e6695761c41a8abee9f20d8041c5ee304444443`. |
| `tests/test_stage5c_ctr_compatibility.py`, `tests/test_stage5c_live_guards.py` | Cover the no-transaction-key CTR schema, notification query, V4 CTR flag, and prior-review gate. |
| `ml_v4/reports/STAGE5C_FINAL_VERIFICATION.md`, this report | Correct the local command and incident status. |

Offline tests: **14 passed** for CTR, guards and harness; **13 passed** for Stage5A/B primary wiring; **39 passed** for existing shadow/Flask tests. Python compilation and PowerShell parsing passed. No live MySQL read or write ran in this Codex process after the user's failed run.

**Remaining blocker:** the actual post-failure database state and live `SHOW COLUMNS` output are pending the read-only local command. A production switch remains blocked by the previously reported Socket.IO authorization gap and terminal inference-error resolution, as well as fresh primary-mode live verification.
