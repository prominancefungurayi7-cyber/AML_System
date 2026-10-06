# MODEL V4 — STAGE 21 VERSIONED FEATURE IMPLEMENTATION AND INDEPENDENT CORRECTNESS AUDIT

**A — EXPERIMENTAL 44-FEATURE MATRICES COMPLETE AND VERIFIED**

The separate development version `v4.features.2.experimental.stage21.1` implements exactly the four Stage20 additions. Train **60000×44** and Validation **15000×44** semantic matrices are complete. Every original40 column matches Stage17 **byte for byte**, including dtype and missing values. No model, fitted preprocessing, threshold search, challenge generation or sealed evaluation access occurred.

## 1. Authority and scope

The explicit Stage21 request authorizes implementation and Train/Validation extraction only. Stage15/15A targets, temporal definitions and retained16R data remain unchanged. Stage16S support deficits,16T challenge governance,16U/V custody restrictions and Stage17–20 historical findings remain authoritative. Named public contracts/evidence were read and hashes checked; sealed directories were not enumerated. See [contract verification](../evidence/stage21/contract_verification.json).

The experimental schema preserves all40 original fields and appends four float64 quantities. Its physical NumPy representation is a structured array with43 float64 fields and one U16 type field. A future fixed3-category one-hot encoding would produce46 numeric columns. **No encoding, scaler or imputer was fitted or materialized here.** Original42-column fitted pipelines cannot consume this representation.

## 2. Implementation

New source: [extractor_v2.py](../development_features_v2/extractor_v2.py), [tests](../development_features_v2/tests/test_stage21.py), [runner](../development_features_v2/run_stage21.py). The wrapper calls the frozen Stage17 extractor directly for the first40 outputs. An independent activity/first-observation state computes the four additions. Original source is unchanged. Both accept only the exact validated observable Event interface; neither imports a target evaluator, generator, model or private provenance. The runner joins labels only after feature computation.

| Field | Exact operation | Availability |
| --- | --- | --- |
| wallet_similar_amount_value_minor_7d | Sum cents in current-centered similar recent cluster | Recent-only; current once; positive on valid current event |
| wallet_baseline_similar_amount_count_28d_offset_7d | Count current-centered similar baseline activities |−1 unless observed35d and4 total baseline activities; valid0 otherwise |
| wallet_near_band_distinct_amount_count_7d | Distinct cent values in inclusive700000..1050000 recent band | Recent-only;0 when no band rows; no current-band gate |
| wallet_baseline_near_band_count_28d_offset_7d | Count baseline activities in that band | Same historical availability, valid0 distinct from−1 |

Subject is current W2W sender or cash serviced_wallet; activity is outgoing W2W and both cash directions. Incoming W2W establishes observation age only. R=(t−7d,t] includes prior smaller keys plus current once; B=(t−35d,t−7d] excludes current. UTC integer microseconds and integer transaction IDs define strict order. Similarity uses `20*abs(a-current)<=current` in integers. Aggregation is exact before float64; only−1 or0..2^53−1 is accepted. Invalid schema/order or overflow makes the wrapper terminal; restart with a fresh validated replay. Definitions and dtypes: [implementation details](../evidence/stage21/feature_implementation_details.json).

## 3. Independent correctness fixtures

**69 tests passed**:30 unchanged original tests and39 new cases. The new suite first passed before the runner; the combined suite passed before any development matrix extraction. Expectations are hand-authored, including a separate Decimal interval reference for a small history. This is independent calculation in the same developer environment, **not an independent external audit**.

Coverage includes inclusive tolerance/band endpoints; exact sums/current once; baseline count and per-current recentering; repeated/distinct cent values; zero versus missing;3versus4 activities; exact35d and7d boundaries; incoming observation versus activity; cash and receiver-assisted roles; equal-time IDs; future and out-of-order rejection; invalid schema; integer precision guard; partition loader denials/reset; metadata exclusion; deterministic repeats.

All four Stage20 nonredundancy witnesses pass equality of every original40 output, with expected new changes: **19999→20000**, baseline similar **0→1**, distinct band **1→2**, baseline band **0→1**. No witness or Stage20 formula was weakened. Overflow tests exercise the exact conversion boundary; they do not allocate a billions-row schema-valid history. [Fixture output](../evidence/stage21/independent_hand_fixtures.json), [temporal results](../evidence/stage21/temporal_correctness_results.json).

## 4. Development matrices, alignment and replay

| Partition | Scored / warmup | Target0 /1 | Extraction seconds | Replay seconds | Original40 / replay |
| --- | ---: | ---: | ---: | ---: | --- |
| Train |60000 /14400 |47770 /12230 |83.388 |90.782 |PASS / byte-identical |
| Validation |15000 /3600 |11970 /3030 |21.209 |21.833 |PASS / byte-identical |

Outputs are [Train X](../development_features_v2/matrices/train/X.npy) and [Validation X](../development_features_v2/matrices/validation/X.npy), each with an exact-copy y.npy and row_metadata.csv in the same partition folder. `np.load(..., allow_pickle=False)` reads the structured arrays. Physical shape is(n,), semantic table width44. IDs and timestamps remain separate from model inputs. No row was filtered, reordered or resampled; warmup is history only.

Raw column bytes, ordered names and dtypes of all40 outputs match the frozen arrays on all75000 scored rows. Target CSV IDs, metadata IDs/timestamps and uint8 labels align exactly. Copied y and metadata bytes match the original artifacts. Wallets, agents and transaction IDs are disjoint across Train/Validation, with new state per partition and replay. Full44 extraction was repeated from the same unchanged observables in fresh states; serialized X.npy bytes match exactly. [Parity](../evidence/stage21/original40_parity.json), [matrix audit](../evidence/stage21/development_matrix_audit.json), [replay](../evidence/stage21/deterministic_replay.json).

## 5. Quality, leakage and target relationship

All new outputs are finite integer-valued float64, within the declared exact range. Baseline−1 markers agree between the two fields because their historical gate is identical; eligible0 is preserved. New field ranges, quantiles, zero/missing counts and identical-column checks are in [quality audit](../evidence/stage21/feature_quality_audit.json). Original40 quality is inherited through exact byte parity, not silently redefined.

These are explicitly disclosed categoryB components of S2/S4. Combined with existing fields and marker semantics they make those deterministic review rules expressible in principle. No scalar full predicate is emitted, and labels/provenance do not enter extraction. Direct component availability can make a synthetic policy easier to learn; **no improved detection accuracy was measured or claimed**. Static imports and loaded modules exclude evaluator/generator/model execution; future/private-metadata tests and fail-closed data enums support causal isolation. They do not prove absence of all population shortcuts. [Leakage assessment](../evidence/stage21/leakage_shortcut_assessment.json).

## 6. Runtime and resource scope

Python 3.14.3, NumPy 2.4.3, sequential extraction. Peak runner working set: Train 287.5MiB; through Validation 291.3MiB. Windows process-lifetime peaks include inputs, original/replay matrices and imports; they are not isolated incremental memory or production latency benchmarks. Source/interpreter hashes and measurements: [resources](../evidence/stage21/runtime_resources.json).

Additional computation scans subject35d activity; first observation persists. Inactive wallet queues are pruned on their next use, so aggregate retained memory is not claimed to be globally time-evicted continuously. Frozen original graph enumeration remains unchanged and can dominate cost. Deployment throughput, concurrent serving and production history adapters are untested.

## 7. Compatibility and scientific restrictions

Stage16T remains frozen at40 features. A separately approved version must bind44-field semantics/extractor/preprocessing/model hashes and change field-count/permutation/freeze references before affected independent evaluation. Its population/support/precision/custody/one-draw policies are not changed. No challenge or salt was created; no custody provisioning occurred. Original Final/Independent remain SEALED_QUARANTINED with existing public supportFAIL facts. [Compatibility review](../evidence/stage21/stage16t_compatibility_review.json).

Nine family-support shortfalls persist. Development extraction does not repair sparse support, repeated Validation use or absent independent custody. XGBoost remains selected and HGB comparator; neither was loaded, fitted or evaluated. Stage18's16 fits remain historical and20 unused slots remain expired. Authorized new fits:0. The Stage20 comparison plan is still a proposal. No application integration or automatic Stage22 follows.

## Reporting-only correction

Both extractions, both serialized replays, all parity/alignment/quality checks and preservation completed successfully before the first runner stopped while formatting the report: it called the NumPy version string as a function. The original executed runner is retained in `run_stage21_attempt1.py.txt`; the corrected runner differs only by removing those call parentheses. No extractor, fixture, data, matrix or existing evidence was changed. Source-freeze hashes in execution evidence refer to the retained executed revision. A separate finalizer rechecked saved matrices, replay hashes, original40 bytes, labels and all protected hashes, then wrote this report without re-extraction or fitting. See [correction record](../evidence/stage21/report_completion_correction.json).

## 8. Preservation and decision

**261 named protected files** match before/after hashes, including frozen development data/labels, Stage17 matrices, Stage18 models/fit ledger, twelve predicates, historical design/reports/evidence, V1 production and V3 integration paths. Scope is explicit and excludes unread sealed bytes. Stage16V's incomplete broader Stage15A historical snapshot remains unresolved; no old artifact or hash expectation was changed to conceal it. [Preservation](../evidence/stage21/preservation_verification.json).

New files are confined to `ml_v4/development_features_v2/`, this report and `ml_v4/evidence/stage21/`. All artifact hashes are recorded in the decision manifest. No Flask, MySQL, API or dashboard file changed. [Scientific limitations](../evidence/stage21/scientific_limitations.json).

**A — EXPERIMENTAL 44-FEATURE MATRICES COMPLETE AND VERIFIED**

Decision A certifies the documented development implementation/parity/replay checks only. It authorizes no model fitting, threshold tuning, independent evaluation, schema promotion or application integration.

V4 STAGE 21 COMPLETE — WAITING FOR APPROVAL.
