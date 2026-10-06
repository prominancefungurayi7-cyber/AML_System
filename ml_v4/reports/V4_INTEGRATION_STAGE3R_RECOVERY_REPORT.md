# MODEL V4 — INTEGRATION STAGE 3R APPROVED STAGE3 IMPLEMENTATION RECOVERY

**A — EXACT STAGE3 IMPLEMENTATION RECOVERED AND PARITY REVERIFIED**

**EXACT RECOVERY VERIFIED.** All twelve missing files have been restored with bytes matching their original historical Stage3 SHA-256 values. The original approved test workflow passed **54 tests** in the isolated runtime. All **128 fixed development examples** again produced maximum absolute probability difference **0**, with exact preprocessing parity. Stage4 was not resumed.

## A. Recovery authority and discovery

The missing list was recalculated directly from the historical Stage3 decision manifest: seven service/documentation/test files and five evidence scripts. Present Stage3 artifacts were checked before recovery. Neither the historical manifest nor its hashes, report or Decision A was changed.

Discovery searched the local project/parent project area, accessible Codex temporary directories and the system temporary directory for matching filenames and hashes. Runtime, model, dataset, matrix, generation and sealed/evaluation directories were excluded as recovery material. There were no exact standalone-file matches in the searched candidates. Git had no tracked/history copies for the approved service. Search scope and exclusions are in [copy search](../evidence/integration_stage3r/copy_search.json); archive contents and further editor stores were not exhaustively searched after the original command records yielded exact bytes.

The original source-generation and update patches were retained in a local Codex execution record. The recovery utility parsed only the recorded patch text as data, applied applicable textual hunks in memory, and checked candidate bytes against the historical expected hashes. It did **not execute any recorded command**. Each destination was created only after an exact SHA-256 match, using exclusive creation to prevent overwriting existing files. LF/CRLF selection was accepted only where it produced the original hash.

The recovery location is the local session record ending in `rollout-2026-10-03T19-56-10-01a0c658-9330-7983-830e-9c584a204637_01a102e8-c1e8-7252-bb32-aa6c70e7e7d7.jsonl`. Full source location, command call ID, record line, destination, newline form and expected/actual hashes are recorded per file in [recovery records](../evidence/integration_stage3r/recovery_records.json). Unrelated session content and credentials were not copied into evidence.

## B. Exact files and hashes

Every actual restored hash equals the value below from the untouched Stage3 manifest.

| Restored path | Expected = actual SHA-256 |
| --- | --- |
| `ml_v4/frozen_inference/cli.py` | `68655d04195fe062f523d33012396e701a394879ee24fa3d0bf22cf8fad49efa` |
| `ml_v4/frozen_inference/history.py` | `5f58a425a1ce67047c84d8c017d100d23fa391671e27acbc4beb09cab01f1a67` |
| `ml_v4/frozen_inference/launch.py` | `07d946c4295479722b7ba72146b452ff5304c1f024f487fefaeb1de196278699` |
| `ml_v4/frozen_inference/README.md` | `de603ee36456acf319ae33581e66d9f88321b926b4b8c2921d3d4217d9f94ced` |
| `ml_v4/frozen_inference/service.py` | `fe2b2971f799a359c1bfdf5d92c56664a39b00caffbb03ddee46843f1208ba48` |
| `ml_v4/frozen_inference/__init__.py` | `c0c7c346d9aaec186b08a43a891d79147a45bcfcb17449b1c295df4daba36475` |
| `ml_v4/frozen_inference/tests/test_service.py` | `1242fba7e2fa9043f4403591633722546dd84f81ba30cedbdd6eca75eb2503e5` |
| `ml_v4/evidence/integration_stage3/copy_dependencies.py` | `cb08d7d21b06612478bff252af557d9e9a3aeddbd09f6aa356d7e18a73c546b6` |
| `ml_v4/evidence/integration_stage3/finalize.py` | `61d3a70a59eaa5aa14e89fb327e4e471554fc49f2c2ad1f23179131916708228` |
| `ml_v4/evidence/integration_stage3/live_check.py` | `b25a8f48b031c069a664970414dd1b4cf0ee691d1b7caca4aba8f5414761ced8` |
| `ml_v4/evidence/integration_stage3/prepare.py` | `bf21b761e30ce2cc692c8c6a12ea6ad59a2b9e62a23603cff0f4a08d19da834a` |
| `ml_v4/evidence/integration_stage3/run_tests.py` | `cc64f68c22a5d1eac9edc85de9d6f95ae988e936f0f1f6b171de00fdb0ec644a` |

## C. Files not exactly recoverable

**None.** All twelve missing manifest-bound files were restored exactly. [Original missing-file record](../evidence/integration_stage3r/missing_files.json).

## D. Reconstructed implementation

**None.** No replacement design or `frozen_inference_recovered` identity was created. Reproducing the original recorded edits yielded the exact historical bytes; this is not a merely behaviorally equivalent reimplementation. The new recovery/validation/reporting utilities live only under `ml_v4/evidence/integration_stage3r/` and have their own manifest identity.

## E. Source gate and behavioral validation

All restored Stage3 artifact hashes and the frozen authority references were verified **before model deserialization**. The original Stage18 XGBoost remains at its authoritative path with SHA-256 `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`. The original Stage17 extractor, feature specification, Event contract and embedded preprocessing identity match. [Pre-load source gate](../evidence/integration_stage3r/source_integrity_gate.json).

The restored original `run_tests.py --child` workflow executed the unchanged approved test suite. A validation harness redirected its generated parity evidence to Stage3R and captured fresh test output there. Historical Stage3 parity/test files were not overwritten. Environment-preparation and historical finalizer scripts were restored but not rerun, since they would recreate or rewrite historical outputs.

Results:

- **54 tests passed**; the original acceptance behavior was exercised without changing test source.
- Exactly40 semantic inputs and42 encoded columns; embedded preprocessing applied once.
-64 fixed Train plus64 fixed Validation examples, using the same retained indices; maximum probability difference0 and exact preprocessing equality.
- Class1 probability semantics, inclusive0.50 threshold, normal/error separation and no fallback.
- Fail-closed UNKNOWN/INCOMPLETE/stale history, graph completeness, same-time order, future invariance and cold-start behavior.
- Frozen N4 NaN and signed-marker handling, graph/funding/agent fixtures, resource errors and request-local concurrency.
- Two fresh processes reproduced identical fixture feature bytes and probability.
- Fit methods were guarded against execution; no training, calibration, threshold search or model selection occurred.

The new parity JSON equals the original retained parity JSON. These are development/fixture checks, not new effectiveness or generalization evidence. [Test results](../evidence/integration_stage3r/test_results.txt), [parity](../evidence/integration_stage3r/parity.json). No live database connection, live feature extraction or production prediction occurred in recovery; hand fixtures remained isolated.

## F. Runtime

The retained isolated environment `ml_v4/.venv_inference_stage3` passed the restored loader's runtime and origin checks: Python3.14.3, NumPy2.4.3, scikit-learn1.9.0, XGBoost3.4.1, SciPy1.18.0, joblib1.5.3 and threadpoolctl3.6.0. Native inference remains limited to one thread. No application/runtime package installation or environment change was needed. This does not add a historical wheel-provenance claim. [Runtime verification](../evidence/integration_stage3r/runtime_verification.json).

## G. Preservation

**482 named expected artifacts match at completion**, comprising the exact restored files and 470 existing files unchanged against inherited expected hashes. The Stage4 decision was additionally hashed and preserved. Stage3's historical Decision A and Stage4's historical Decision C remain untouched. No previous evidence file was refreshed under its old identity.

Frozen model/preprocessing, Stage16R data/labels, Stage17 extractor, Stage21/22 experiments, Stage23 freeze, V1/V3 references and fit ledgers remain unchanged. Named hashing followed explicit inherited paths; no sealed Final Test or Independent Evaluation content was searched or accessed. [Preservation verification](../evidence/integration_stage3r/preservation_verification.json).

## H. Cause of disappearance

**CAUSE NOT ESTABLISHED.** No recorded deletion-operation tool call naming these exact missing paths was found in the inspected session record. The prior Git check found no tracked/history copies. This does not establish that a particular cleanup, reset, editor or automation deleted them. Generic operations outside the inspected evidence remain unverified. [Cause assessment](../evidence/integration_stage3r/cause_assessment.json).

## I. Protection against recurrence

Created an exact [source-only backup ZIP](../evidence/integration_stage3r/approved_stage3_source_backup.zip) containing the twelve recovered files, and verified every archived entry against its historical hash. The [backup manifest](../evidence/integration_stage3r/source_backup_manifest.json) binds both the archive and entries. It contains no models, datasets, sealed material, credentials or runtime environment.

The local archive is recovery redundancy, not an independent/off-machine backup. Recommend adding the active inference source/tests and approved evidence scripts to normal Git source control and keeping a separate source backup. No Git staging, commit or publication was performed. Do not add model binaries, datasets, secrets or large runtime directories merely to protect source.

## J. Stage4 readiness and final decision

The missing-approved-source blocker identified by Stage4 is resolved. The original implementation and its parity are available again, so Stage4 may resume **after explicit recovery approval**. Its post-commit hook, result table, reassessment integration, shadow transport/UI and end-to-end application testing remain separate unfinished work. No Stage4 implementation, V4 alerting, V1 replacement or cutover was performed.

**A — EXACT STAGE3 IMPLEMENTATION RECOVERED AND PARITY REVERIFIED**

V4 INTEGRATION STAGE 3R COMPLETE —
WAITING FOR APPROVAL.
