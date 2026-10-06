# MODEL V4 — STAGE 17 DEVELOPMENT-ONLY FEATURE EXTRACTION AND FEATURE AUDIT

**A — DEVELOPMENT FEATURES COMPLETE AND VERIFIED FOR MODEL TRAINING**

The frozen 40-semantic-field extractor and hand-calculated correctness fixtures pass. Train and Validation matrices were constructed from the existing development ledgers, with exact frozen label alignment and byte-identical repeated extraction. This is technical development-feature readiness. No model was trained, selected, calibrated or independently evaluated. Family-support shortfalls and unavailable challenge custody remain unresolved.

## 1. Development-only authority and preserved precedence

The user's Stage 17 request explicitly authorizes implementation, development extraction and diagnostics after Stage 16V. It supersedes the earlier stop on these particular development activities; it does not satisfy or waive Stage 16T custody/support progression. The authorization is recorded in [development_authorization.json](../evidence/stage17/development_authorization.json).

Stage 15's feature/temporal/target definitions remain frozen. Stage 15A's scoped population amendments do not alter the feature definitions. Stage 16R's retained draw and labels remain authoritative inputs. Stage 16S's support limitations remain in force. Stage 16T's challenge protocol, Stage 16U's implementation status and Stage 16V's custody-unavailable decision are unchanged. Original Final Test and Independent Evaluation remain SEALED_QUARANTINED; their public support-policy FAIL certificates remain historical facts. No private evaluation contents, registry or challenge secret was accessed.

## 2. Implementation, inputs and storage

New source is confined to `ml_v4/development_features/`: [extractor.py](../development_features/extractor.py), [run_stage17.py](../development_features/run_stage17.py), [finalize_stage17.py](../development_features/finalize_stage17.py) and [tests/test_features.py](../development_features/tests/test_features.py). Existing source and application files were not edited.

The extractor accepts only the exact validated observable `Event` interface. It imports the existing low-level observable schema/time contract, never the evaluator, generator, labels, witnesses or private provenance. It maintains separate wallet activity, directed incoming/outgoing and agent-service histories plus first-observation timestamps. State is newly instantiated for each partition and each replay. IDs are internal join/order keys only.

The runner uses the existing fail-closed development loader with exact `train`/`validation` enums and only `warmup_observables.csv`, `transactions.csv` and `ground_truth.csv`. Hashes match the Stage 16R manifest before extraction. Frozen binary labels are read by the runner and joined by exact row-by-row transaction ID after independent feature computation; they are never supplied to the extractor. Original full-key order is retained. No scored row is filtered or resampled; warm-up rows supply history but are not training rows.

| Artifact | Train | Validation |
| --- | ---: | ---: |
| Semantic X dimensions | 60,000 × 40 | 15,000 × 40 |
| Warm-up input rows | 14,400 | 3,600 |
| y dimensions | 60,000 | 15,000 |
| Frozen target 0 / 1 | 47,770 / 12,230 | 11,970 / 3,030 |
| Extraction seconds | 31.717 | 7.689 |
| Replay seconds | 31.762 | 7.609 |
| Byte-identical replay | PASS | PASS |

Files are [Train X](../development_features/matrices/train/X.npy), [Train y](../development_features/matrices/train/y.npy), [Validation X](../development_features/matrices/validation/X.npy), and [Validation y](../development_features/matrices/validation/y.npy). Each partition also has `row_metadata.csv` containing row index, exact integer transaction ID and UTC timestamp outside X.

X uses a one-dimensional NumPy structured record array with 40 ordered named fields: 39 little-endian float64 fields and one Unicode categorical transaction-type field. Its semantic table dimensions are shown above; its physical NumPy shape is `(60000,)` or `(15000,)`. `np.load(path, allow_pickle=False)` reads it without executable pickle objects. y is uint8. Monetary/count aggregates are exact integers/rationals until final float64 conversion. Counts and amounts retain integer-valued outputs on these data.

No one-hot expansion was applied, so no 42-column encoding order is invented or claimed frozen. Transaction type retains the observable categories `wallet_to_wallet`, `cash_in`, `cash_out`, corresponding to W2W/Cash-In/Cash-Out. Future model preprocessing must explicitly freeze its numeric encoding and marker treatment; no scaler, imputer, calibration or learned transformation was fitted here.

## 3. Exact semantic fields

The full ordered definitions, eligibility, domains, direct-target-component disclosures, dtype and path-selection rule are copied into [feature_schema_audit.json](../evidence/stage17/feature_schema_audit.json). Frozen source specification hashes bind that record. The implementation uses no additional features.

| # | Field | Frozen formula | Missing semantics |
| --- | --- | --- | --- |
| 1 | `amount_minor` | Current integer amount_minor | Never missing; schema rejects absent/nonpositive amount |
| 2 | `transaction_type` | Categorical W2W / Cash-In / Cash-Out | Never missing |
| 3 | `wallet_count_1h` | n(R_1h) | 0 only when mathematically zero; current ensures nonempty activity |
| 4 | `wallet_value_1h` | sum_minor(R_1h) | 0 only when mathematically zero; current ensures nonempty activity |
| 5 | `wallet_max_value_share_1h` | max(amount in R_1h)/sum_minor(R_1h) | 0 only when mathematically zero; current ensures nonempty activity |
| 6 | `wallet_activity_acceleration_1h` | n(R_1h)/max(1,n(B_1h)/672) | -1 if baseline-ineligible |
| 7 | `wallet_similar_amount_count_7d` | n(C_R) with S2 current-centered 5% amount tolerance | 0 only when mathematically zero; current ensures nonempty activity |
| 8 | `wallet_similar_amount_share_7d` | n(C_R)/n(R_7d) | 0 only when mathematically zero; current ensures nonempty activity |
| 9 | `wallet_count_utc_day` | n([UTC midnight,t]) | 0 only when mathematically zero; current ensures nonempty activity |
| 10 | `wallet_active_hours_utc_day` | distinct occupied UTC hour buckets in current day | 0 only when mathematically zero; current ensures nonempty activity |
| 11 | `wallet_day_count_growth` | current-day count/max(1,median(28 prior calendar-day counts including zeros)) | -1 if baseline-ineligible |
| 12 | `wallet_near_band_count_7d` | count of R_7d amounts in inclusive [700000,1050000] cents | 0 only when mathematically zero; current ensures nonempty activity |
| 13 | `network_in_count_24h` | number of relevant directed W2W edges | 0 for non-W2W |
| 14 | `network_in_distinct_24h` | number of distinct opposite wallet endpoints | 0 for non-W2W |
| 15 | `network_in_acceleration_24h` | recent edge count/max(1,baseline edge count/28) | -1 if non-W2W or baseline-ineligible |
| 16 | `network_out_count_24h` | number of relevant directed W2W edges | 0 for non-W2W |
| 17 | `network_out_distinct_24h` | number of distinct opposite wallet endpoints | 0 for non-W2W |
| 18 | `network_out_acceleration_24h` | recent edge count/max(1,baseline edge count/28) | -1 if non-W2W or baseline-ineligible |
| 19 | `prior_return_path_min_length_7d` | min edge count over P; P ignores all amounts | -1 for no path or non-W2W |
| 20 | `prior_return_path_count_7d` | number of distinct edge-key sequences in P; no amount filters | 0 for no path/non-W2W |
| 21 | `prior_path_min_max_log_change_7d` | max(abs(log(a_next/a_prev))) on p*; one-edge path=0 | -1 for no path/non-W2W |
| 22 | `current_to_selected_path_first_value_ratio` | amount(T)/amount(first edge of p*) | -1 for no path/non-W2W |
| 23 | `wallet_pass_through_fraction_24h` | (O_prior+amount(T))/F using N4 anchor and funding definitions | -1 if current not outward or no prior W2W anchor |
| 24 | `wallet_prior_funding_residual_minor_24h` | F-O_prior using N4 anchor; may be negative | NaN if current not outward or no anchor; numeric -1 may be a valid residual |
| 25 | `agent_wallet_growth_ratio_7d` | D/max(1,median(four preceding weekly distinct counts including zeros)) | -1 absent agent or A1 baseline-ineligible |
| 26 | `agent_distinct_wallets_7d` | D=distinct serviced wallets in R_7d | 0 absent agent |
| 27 | `agent_new_wallet_count_7d` | size(wallets(R_7d) minus wallets(B_7d)) | -1 absent agent or A1 baseline-ineligible |
| 28 | `agent_new_wallet_share_7d` | new distinct count/D | -1 absent agent or A1 baseline-ineligible |
| 29 | `agent_top2_count_share_24h` | top2(R_24h) | 0 absent agent |
| 30 | `agent_top2_share_change_24h` | top2(R_24h)-top2(B_24h), independently selected top two in each | -3 absent agent or A2 baseline-ineligible; valid range[-1,1] |
| 31 | `agent_service_acceleration_1h` | n(R_1h)/max(1,n(B_1h)/672) | -1 absent agent or A3 baseline-ineligible |
| 32 | `agent_distinct_wallets_1h` | distinct serviced wallets in R_1h | 0 absent agent |
| 33 | `agent_cash_in_count_24h` | number of Cash-In services in R_24h | 0 absent agent or no cash-in |
| 34 | `agent_cash_out_count_24h` | number of Cash-Out services in R_24h | 0 absent agent or no cash-out |
| 35 | `agent_cash_in_value_24h` | sum of Cash-In amount_minor in R_24h | 0 absent agent or no cash-in |
| 36 | `agent_cash_out_value_24h` | sum of Cash-Out amount_minor in R_24h | 0 absent agent or no cash-out |
| 37 | `agent_cash_distinct_wallets_24h` | distinct serviced wallets in cash-only R_24h | 0 absent agent or no cash |
| 38 | `agent_cash_value_skew_change` | v(R_24h)-v(B_24h); v=(out-in)/(out+in), empty=0 | -3 absent agent or A4 baseline-ineligible; valid range[-2,2] |
| 39 | `wallet_observed_coverage_days` | min(35, elapsed days since first prior observed participation); 0 if none | 0 on first observation; never private activation |
| 40 | `agent_observed_coverage_days` | min(35, elapsed days since first prior observed service); 0 if none | 0 absent agent or first service |

## 4. Temporal and numerical correctness

All timestamps are canonical UTC at integer microseconds. Full keys must strictly increase, transaction IDs must be unique, and each row is computed before current-event state insertion. Same-time smaller IDs can contribute; larger IDs cannot. Recent intervals are open below and closed above; preceding 28-day baselines are disjoint. Calendar-day counts use UTC midnight and the explicit S3 half-open 28-bin exception. No frozen field uses a separate 30-day window, so none was added from the request's general window summary.

A1 historical growth/newness requires the actual first observed service at or before the 35-day boundary and at least 12 services strictly inside its baseline. The coverage display never substitutes for the timestamp gate. Recent distinct counts remain available at cold start. Agent service roles include receiver-serviced assisted W2W once, while W2W never contributes cash values/counts. Valid negative concentration/skew changes remain distinct from -3; valid negative N4 residuals remain distinct from NaN.

N3 enumerates every simple chronological topology path of one to five prior edges within seven days. There is no path truncation or amount-based topology filtering. The selected route minimizes the exact rational maximum of adjacent amount ratio and its reciprocal, then length, then full-key sequence. Monotonicity of log makes this ranking equivalent to the frozen maximum absolute log-ratio ordering; only the final log descriptor is float64. Current amount never selects the route. N4 uses the smallest-key prior incoming W2W anchor within 24 hours, counts funding/outward roles once, and excludes the current amount from the residual.

## 5. Independent calculations and test results

**30 pytest cases passed.** The initial 22-case suite passed before extraction; eight additional cases/parameter instances passed before this final decision. Expectations are independently hand-derived in the test file, including a complete 40-field cold-start vector and nontrivial wallet, network, agent, funding, concentration and cash examples. Tests do not invoke the target evaluator or use its witnesses. This is independent reference calculation within the same developer environment, not an independent external audit.

Coverage includes feature order/dtypes; exact amounts/counts; hour/day/seven-day boundary equality; 5% amount and band endpoints; disjoint baselines; zero and nonzero daily medians; fractional weekly medians; exact 35-day age and baseline minimum support; incoming observation age; all missing markers; valid signed values; equal-time IDs; future append and identity-renaming invariance; network direction; N3 chronology, 1..5 versus 6 edges, competing route selection and tie-breaks; N4 anchors/residuals; cash/assisted roles; fresh partition state; forbidden-field rejection; unauthorized partition/file rejection and resolved path escapes. The path-escape fixture mocks resolution; it does not claim provisioned OS symlink permissions.

Initial failures were in fixture expectations: service dates outside A3/A4 baselines, weekly events crossing a shared week boundary, and raw NaN equality assertions. Dates and marker-aware assertions were corrected after checking the frozen boundaries. No feature definition or target was changed. Final failures: none. Full output and qualifications are in [independent_fixture_tests.json](../evidence/stage17/independent_fixture_tests.json) and [temporal_correctness_tests.json](../evidence/stage17/temporal_correctness_tests.json).

## 6. Matrix quality, leakage and resource audit

Both partitions passed complete row/label/ID alignment, separate history/entity/transaction-ID checks, exact schema, marker-aware finite validity and numeric range checks. NaN occurs only where permitted for the N4 funding residual. There are no infinities, constant columns or identical column pairs. There are 75 repeated feature vectors in Train and 2 in Validation; these are retained observations, not duplicate transaction IDs, and no rows were deduplicated.

| Descriptor | Train | Validation |
| --- | ---: | ---: |
| A1 growth missing rows | 18,858 | 4,828 |
| N4 residual missing rows | 49,076 | 12,308 |
| Valid N4 residual minimum, cents | -4,741,603 | -2,315,918 |
| Maximum topology path count | 20 | 13 |

Column-wise missing fractions, valid quantiles/ranges, category counts and Train/Validation differences are in [feature_quality_audit.json](../evidence/stage17/feature_quality_audit.json). Differences are descriptive; no transformations, clipping or selection were fitted to reduce them. Missingness and repeated synthetic behaviour can be informative and remain limitations for future model audits.

The observed peak process working set was 295,960,576 bytes (about 282.25 MiB), a Windows process high-water measurement including inputs, replay and audits, not an isolated extractor allocation. Runtime was Python 3.14.3 / NumPy 2.4.3; source/schema/input/output SHA-256 records accompany this report. Both full extractions were repeated in fresh state, with byte-identical NPY serialization. Reproducibility is demonstrated in this recorded runtime, not guaranteed across arbitrary dependencies or hardware.

Static import/interface review confirms the extractor has no evaluator or generator import. X has no IDs, absolute timestamps, partition indicator, labels, rule flags, scores, private origins/archetypes, event/context roles or private activation. Frozen behavioural components that overlap target components remain explicitly disclosed, rather than being described as independent labels. Full details are in [leakage_audit.json](../evidence/stage17/leakage_audit.json) and [development_matrix_audit.json](../evidence/stage17/development_matrix_audit.json).

## 7. All-family support remains unchanged

These counts are taken from the saved Stage 16S development evidence; no family labels were recalculated or changed. Rows carrying multiple families overlap. Subjects and clusters are not independent sample sizes.

| Family | Train / minimum | Validation / minimum | Subjects Train / Validation | Clusters Train / Validation | Count objectives |
| --- | ---: | ---: | ---: | ---: | --- |
| S1 | 456 / 1200 | 132 / 300 | 132 / 31 | 147 / 34 | Shortfall |
| S2 | 112 / 1200 | 23 / 300 | 37 / 7 | 43 / 7 | Shortfall |
| S3 | 2292 / 1200 | 546 / 300 | 397 / 104 | 673 / 156 | Met |
| S4 | 128 / 1200 | 16 / 300 | 54 / 12 | 57 / 12 | Shortfall |
| N1 | 414 / 1200 | 101 / 300 | 116 / 28 | 187 / 42 | Shortfall |
| N2 | 1690 / 1200 | 429 / 300 | 333 / 86 | 582 / 147 | Met |
| N3 | 550 / 1200 | 130 / 300 | 355 / 87 | 453 / 111 | Shortfall |
| N4 | 559 / 1200 | 144 / 300 | 258 / 74 | 348 / 91 | Shortfall |
| A1 | 5773 / 1200 | 1467 / 300 | 90 / 23 | 2273 / 570 | Met |
| A2 | 755 / 1200 | 148 / 300 | 74 / 20 | 339 / 60 | Shortfall |
| A3 | 883 / 1200 | 255 / 300 | 77 / 18 | 249 / 80 | Shortfall |
| A4 | 812 / 1200 | 222 / 300 | 75 / 17 | 466 / 138 | Shortfall |

The nine shortfalls S1/S2/S4/N1/N3/N4/A2/A3/A4 remain. In particular, Validation S2 has only 23 positives across 7 subjects/7 clusters; S4 has 16 across 12/12. N3 has 130 positives and A4 has 222, both below 300. S3/N2/A1 meeting count objectives does not establish model quality or representative uncertainty. Technical feature readiness cannot establish reliable twelve-family learning/evaluation, repair the original holdouts or manufacture evidence for sparse families.

## 8. Preservation and limits

All six authorized development observable/history/label files match the Stage 16R manifest before extraction and remain unchanged afterward. The named preservation inventory also covers frozen design/amendment/challenge records, prior stage public evidence/source, V3 model/extractor/preprocessing, experimental API/dashboard and Flask entrypoint. The V1 production artifact separately matches its historical SHA-256. No application, MySQL, V1/V2/V3 model or integration source was modified.

The detailed inventory and before/after values are in [preservation_verification.json](../evidence/stage17/preservation_verification.json). This is an explicit named-file scope, not an inventory of every disk file. Sealed bytes are excluded and unread. Stage 16V's incomplete broad Stage 15A historical snapshot remains documented; no archive was restored and no older manifest or historical file was rewritten to suppress that limitation.

The feature contract deliberately omits some predicate components and N3 retains a lossy selected-route summary. Synthetic separability, correlated direct components, cold starts, development-data reuse and sparse family support remain scientific risks. Feature correctness is not evidence of actual laundering detection, regulatory effectiveness or model validation. Challenge-generation custody and original independent evaluation remain blocked.

## 9. Reproduction and deliverables

Read-only fixture command: `python -B -m pytest ml_v4/development_features/tests -q -p no:cacheprovider`.

`run_stage17.py` verifies named inputs, runs the fixtures, extracts/replays each partition and records audits; it refuses existing output directories. `finalize_stage17.py` performs final fixture/range/hash checks and writes the report/decision; it refuses an existing completed report or decision. Reproduction requiring regenerated matrices belongs in a separate authorized output workspace, preserving this result. No code here fits a model.

Required evidence: [schema](../evidence/stage17/feature_schema_audit.json), [temporal tests](../evidence/stage17/temporal_correctness_tests.json), [independent fixtures](../evidence/stage17/independent_fixture_tests.json), [matrix audit](../evidence/stage17/development_matrix_audit.json), [quality](../evidence/stage17/feature_quality_audit.json), [leakage](../evidence/stage17/leakage_audit.json), [preservation](../evidence/stage17/preservation_verification.json), [decision and artifact hashes](../evidence/stage17/stage17_decision.json). The additional development authorization record documents this stage's narrow permission.

## 10. Decision

**A — DEVELOPMENT FEATURES COMPLETE AND VERIFIED FOR MODEL TRAINING**

All required implementation, fixture and development-matrix checks pass within the stated scope. This permits these artifacts to be considered in a separately authorized model-development plan; it does not start training or waive support, custody or evaluation requirements. No model, hyperparameter search, threshold selection, additional transaction generation, sealed evaluation access or automatic Stage 18 progression occurred.

V4 STAGE 17 COMPLETE — WAITING FOR APPROVAL.
