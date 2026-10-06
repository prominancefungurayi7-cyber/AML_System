# MODEL V4 — INTEGRATION STAGE 4 CONTROLLED APPLICATION SHADOW INTEGRATION

**C — APPLICATION/PROCESS INTEGRATION NOT YET SAFE**

The approved Stage3 inference implementation is missing from the current workspace. Its decision manifest and report remain present, but the service, history gate, CLI, launcher and tests referenced by that manifest are absent. Stage4 cannot safely invoke or retest the approved implementation. No shadow path was connected, database migration applied, transaction submitted, reassessment issued, model loaded or prediction made.

## 1. Preflight authority verification

The Stage3 manifest requires these currently missing service files:

- `ml_v4/frozen_inference/__init__.py`
- `ml_v4/frozen_inference/service.py`
- `ml_v4/frozen_inference/history.py`
- `ml_v4/frozen_inference/cli.py`
- `ml_v4/frozen_inference/launch.py`
- `ml_v4/frozen_inference/README.md`
- `ml_v4/frozen_inference/tests/test_service.py`

Only `authority.json` and `history_authority.json` remain in that service directory. Five manifest-bound Stage3 evidence scripts are also missing: `prepare.py`, `copy_dependencies.py`, `live_check.py`, `run_tests.py` and `finalize.py`.

Across **479 named expected artifacts**, **467 present files match their expected hashes**, **12 are missing**, and **zero present files have a hash mismatch**. This is not an all-artifacts preservation PASS. The expected and actual hashes and exact missing paths are recorded in [preflight integrity evidence](../evidence/integration_stage4/preflight_integrity.json).

The original Stage18 model is among the matching files and retains SHA-256 `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`. No deserialization occurred. The isolated Python executable exists; its presence alone does not establish an executable, parity-verified service. Stage3's historical 54-test result is preserved but was not rerun.

Git lists no tracked copies or historical commits for the missing service paths. No approved recovery copy was found through that check. No new source was substituted under the old manifest, and no expected hash was changed to conceal missing files. The cause of their absence is not established by this audit.

## 2. Application path and planned commit boundary

The current customer handler validates the canonical envelope, inserts the legacy parent and canonical event, runs the existing V1 operational processing, updates balances, then commits. The authorized V4 hook would belong after successful commit and use a new connection/snapshot. A failed or rolled-back source transaction must never start V4.

The checked application publishes `transaction` and `alert`; these are the effective existing names, rather than `transaction_processed` and `alert_created` named in the request. Their semantics were not changed. Any later shadow implementation should use a separate authorized-staff event such as `v4_shadow_result` without renaming existing events.

The path before and after this stage is identical. V1 remains the operational model. No V4 probability is blended into legacy risk or rule scores; no V4 production alert, SAR or CTR action was introduced.

## 3. Required integration components — not activated

| Component | Current outcome |
| --- | --- |
| Post-commit application hook | NOT IMPLEMENTED — approved child service absent |
| Automatic technical reassessment | NOT RUN; no scope or attestation changed |
| Dedicated additive result table | NOT CREATED |
| Transaction/model/feature uniqueness | NOT IMPLEMENTED |
| Fixed isolated process, timeout and bounded JSON protocol | NOT CONNECTED |
| Separate success/error persistence | NOT IMPLEMENTED |
| Authorized shadow Socket.IO delivery | NOT IMPLEMENTED |
| V4 Shadow AI UI | NOT IMPLEMENTED |
| First-event and transaction-role fixtures | NOT RUN |
| Original Stage3 parity tests | NOT RUN — test and service source absent |

Draft new coordinator/worker files were started before the preflight command's failure was inspected. They were removed before execution or application connection. They are not retained or represented as an implementation. No existing application file was edited.

## 4. Tests and live-data safety

Only static source inspection, explicit named-file hash verification and Git recovery checks ran. There was no Flask startup/import, database connection, schema change, customer transaction, isolated financial fixture, subprocess model invocation, feature calculation, fitting or threshold work. No sealed evaluation path was enumerated or read.

Consequently, this stage supplies no new evidence for commit ordering, MySQL end-to-end behavior, idempotency, timeout handling, authorized delivery or UI rendering. The previous empty live scope is historical context only; its current state was not rechecked. No fabricated event or baseline history was used to bypass the blocker.

## 5. Recovery required before Stage4 can proceed

1. Restore the twelve missing files from the approved Stage3 working copy or backup, using the exact expected hashes in the existing Stage3 manifest. Do not overwrite the historical manifest to accept a different implementation.
2. Reverify the original model, frozen sources and isolated runtime, and rerun the approved Stage3 parity checks.
3. Implement the authorized post-commit shadow path: deterministic Stage2A reassessment with no status override, fixed isolated child process, validated finite result contract, additive result persistence and database-enforced transaction/model/feature uniqueness.
4. Test first-event cold start, all four canonical transaction forms, failure/rollback/retry behavior and staff-only shadow delivery using safe nonproduction fixtures before enabling controlled use.

Automatic reassessment, when implemented, must be described as prototype technical verification, not independent human or external certification. An incomplete history must stop prediction and produce a technical error. No source revision or freshness check may be bypassed.

The scientific warning remains:

> This model identifies transaction patterns defined as suspicious within the synthetic research benchmark. It does not determine that money laundering has occurred.

All positives require human review. A normal result does not certify that a transaction is legitimate. No V4-facing UI was added in this blocked stage.

## 6. Preservation and decision

The 467 present named artifacts were rechecked at completion and remain unchanged. Twelve required artifacts were already absent at preflight and remain explicitly unresolved. The final [decision manifest](../evidence/integration_stage4/decision.json) records this scope and binds the new report/evidence. Historical Stage3 evidence remains intact; its earlier successful decision is not rewritten.

**C — APPLICATION/PROCESS INTEGRATION NOT YET SAFE**

The missing approved inference source prevents safe shadow integration. V1 remains primary; no normal V4 AML alerts or production cutover were activated.

V4 INTEGRATION STAGE 4 COMPLETE —
WAITING FOR APPROVAL.
