# MODEL V4 — STAGE 22 CONTROLLED 40-VERSUS-44 FEATURE EXPERIMENT

**C — EXPERIMENT INCONCLUSIVE**

Exactly four new model-fit attempts completed. This compares two frozen configurations under original40 and experimental44 representations on identical development rows. Results are **exploratory**: Validation already informed the feature-design hypotheses. No model is promoted or selected as a new final model; historical `primary_XGB` remains selected and HGB remains its comparator.

## 1. Authority, inputs and budget

Named Stage15/15A,16R–16V,17–21 contracts, reports/evidence and artifact hashes were verified before fitting. Stage21's retained reporting-only correction was checked through its final manifest; no extractor or matrix ambiguity remains. All75000 rows have original40 raw-column byte parity, identical IDs/order/metadata and unchanged binary labels. Train has60000 rows(47770 target0,12230 target1); Validation15000(11970 target0,3030 target1). No new transactions, sampling, label changes or sealed directory access occurred. [Input verification](../evidence/stage22/input_verification.json).

The explicit Stage22 request prospectively authorizes four attempts, cumulative maximum20 under the inherited36 ceiling. Stage18's16-attempt ledger remains unchanged and its20 expired slots are not generally reopened. New ordinals1..4 link to cumulative17..20; all four STARTED and COMPLETE records were durably appended, no FAILED records. **Remaining authorized attempts:0.** No retry or replacement was used. [Authorization](../evidence/stage22/fit_authorization.json), [new ledger](../evidence/stage22/fit_ledger.jsonl), [budget verification](../evidence/stage22/fit_budget_verification.json).

## 2. Frozen configurations and preprocessing

Execution order: A40-XGB, B44-XGB, A40-HGB, B44-HGB. Exact Stage20 dictionaries, Python/NumPy/sklearn/XGBoost versions, source hashes, fixed diagnostics and descriptive decision interpretation were recorded before the first attempt in [frozen plan](../evidence/stage22/frozen_experiment_plan.json).

XGB uses200trees, depth5, learning rate.07, minchild5; HGB200iterations,31leaves, learning rate.07, minimumleaf20. All other parameters match Stage20 and normalized estimator `get_params()` exactly. Seed2026092915; no early stopping, new weights, resampling, calibration, threshold search or rule overrides. The Stage18 serializer stored default XGB missing NaN as JSONnull; only that parameter is restored toNaN, with remaining nulls retained asNone. This representation interpretation was frozen before fitting.

Each of the four pipelines independently fits the unchanged Stage18 preprocessing class on Train only: exact per-field sentinel→NaN, median imputation(empty0, no indicators), standard scaling and fixed type vocabulary(wallet_to_wallet,cash_in,cash_out). Valid−1 N4 residual,−1 concentration change and−2 cash change are preserved. Only the two new baseline fields add−1 missing conversions; valid0 stays observed. Dimensions are42 for A and46 for B. No fitted transforms are shared, no Validation `.fit` or Train+Validation refit. Classification is **score>=0.50** throughout. [Preflight](../evidence/stage22/preprocessing_preflight.json), [fitted-state audit](../evidence/stage22/preprocessing_audit.json).

## 3. Primary paired contrasts

Positive numerators count union-positive predictions on the indicated family; “only” excludes other family flags for diagnosis without changing primary evaluation rows. Differences are B44−A40 recall on identical supports. Recovery/loss columns are paired event counts.

| Algorithm | Partition | Slice | A TP/support | B TP/support | Recall delta | B recovers A miss | B loses A hit |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| XGB | train | S2 | 68/112 | 77/112 | +0.080357 | 14 | 5 |
| XGB | train | S4 | 42/128 | 45/128 | +0.023438 | 3 | 0 |
| XGB | train | S2-only | 48/92 | 57/92 | +0.097826 | 14 | 5 |
| XGB | train | S4-only | 13/99 | 16/99 | +0.030303 | 3 | 0 |
| XGB | validation | S2 | 11/23 | 18/23 | +0.304348 | 7 | 0 |
| XGB | validation | S4 | 4/16 | 4/16 | +0.000000 | 0 | 0 |
| XGB | validation | S2-only | 11/23 | 18/23 | +0.304348 | 7 | 0 |
| XGB | validation | S4-only | 0/12 | 0/12 | +0.000000 | 0 | 0 |
| HGB | train | S2 | 91/112 | 100/112 | +0.080357 | 12 | 3 |
| HGB | train | S4 | 68/128 | 71/128 | +0.023438 | 11 | 8 |
| HGB | train | S2-only | 71/92 | 80/92 | +0.097826 | 12 | 3 |
| HGB | train | S4-only | 39/99 | 42/99 | +0.030303 | 11 | 8 |
| HGB | validation | S2 | 13/23 | 16/23 | +0.130435 | 3 | 0 |
| HGB | validation | S4 | 5/16 | 5/16 | +0.000000 | 1 | 1 |
| HGB | validation | S2-only | 13/23 | 16/23 | +0.130435 | 3 | 0 |
| HGB | validation | S4-only | 1/12 | 1/12 | +0.000000 | 1 | 1 |

These raw counts are the primary diagnostic contrasts. No row-independence p-value, post-hoc threshold or independent confirmation is claimed. Train differences describe fitted approximation; Validation differences remain exploratory. [Paired comparisons](../evidence/stage22/paired_comparisons.json).

## 4. Validation union metrics and tradeoffs

| Model | Macro F1 | Precision | Recall | FPR | Accuracy | Balanced accuracy | ROC-AUC | AP | [[TN,FP],[FN,TP]] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| A40-XGB | 0.956670 | 0.958683 | 0.903630 | 0.009858 | 0.972667 | 0.946886 | 0.996046 | 0.985972 | [[11852, 118], [292, 2738]] |
| B44-XGB | 0.958415 | 0.959874 | 0.907921 | 0.009607 | 0.973733 | 0.949157 | 0.996195 | 0.986369 | [[11855, 115], [279, 2751]] |
| A40-HGB | 0.961632 | 0.952737 | 0.924752 | 0.011612 | 0.975533 | 0.956570 | 0.996572 | 0.987838 | [[11831, 139], [228, 2802]] |
| B44-HGB | 0.961164 | 0.953599 | 0.922442 | 0.011362 | 0.975267 | 0.955540 | 0.996626 | 0.987861 | [[11834, 136], [235, 2795]] |

XGB: B detects 34 positives missed by A and loses 21 A detections. Among target0 rows, B adds 11 false positives and removes 14. Net Macro F1 +0.001744; recall +0.004290; FPR -0.000251.
HGB: B detects 24 positives missed by A and loses 31 A detections. Among target0 rows, B adds 16 false positives and removes 19. Net Macro F1 -0.000467; recall -0.002310; FPR -0.000251.

All Train/Validation metric files retain confusion denominators, threshold, AP definition through sklearn average_precision_score, undefined conventions and fixed-score summaries. AP is not trapezoidal PR area. Separate saved-score confusion/ratio calculations and AP/AUC checks matched every result within1e−12; no new predictions were required for that verification. [Verification](../evidence/stage22/independent_metric_verification.json).

## 5. All families and domains

| Family | A40-XGB | B44-XGB | A40-HGB | B44-HGB |
| --- | --- | --- | --- | --- |
| S1 | 126/132 (0.9545) | 130/132 (0.9848) | 130/132 (0.9848) | 132/132 (1.0000) |
| S2 | 11/23 (0.4783) | 18/23 (0.7826) | 13/23 (0.5652) | 16/23 (0.6957) |
| S3 | 492/546 (0.9011) | 491/546 (0.8993) | 491/546 (0.8993) | 490/546 (0.8974) |
| S4 | 4/16 (0.2500) | 4/16 (0.2500) | 5/16 (0.3125) | 5/16 (0.3125) |
| N1 | 77/101 (0.7624) | 83/101 (0.8218) | 85/101 (0.8416) | 87/101 (0.8614) |
| N2 | 381/429 (0.8881) | 379/429 (0.8834) | 380/429 (0.8858) | 382/429 (0.8904) |
| N3 | 122/130 (0.9385) | 123/130 (0.9462) | 115/130 (0.8846) | 112/130 (0.8615) |
| N4 | 123/144 (0.8542) | 122/144 (0.8472) | 120/144 (0.8333) | 120/144 (0.8333) |
| A1 | 1467/1467 (1.0000) | 1466/1467 (0.9993) | 1463/1467 (0.9973) | 1464/1467 (0.9980) |
| A2 | 109/148 (0.7365) | 114/148 (0.7703) | 123/148 (0.8311) | 119/148 (0.8041) |
| A3 | 255/255 (1.0000) | 255/255 (1.0000) | 255/255 (1.0000) | 255/255 (1.0000) |
| A4 | 151/222 (0.6802) | 144/222 (0.6486) | 197/222 (0.8874) | 189/222 (0.8514) |

| Domain | A40-XGB | B44-XGB | A40-HGB | B44-HGB |
| --- | --- | --- | --- | --- |
| structuring | 600/684 (0.8772) | 610/684 (0.8918) | 606/684 (0.8860) | 610/684 (0.8918) |
| network | 675/776 (0.8698) | 679/776 (0.8750) | 672/776 (0.8660) | 673/776 (0.8673) |
| agent | 1831/1941 (0.9433) | 1828/1941 (0.9418) | 1887/1941 (0.9722) | 1876/1941 (0.9665) |

Families/domains overlap; do not sum their supports or errors. Domain recall is union prediction among domain-bearing positives; there is no separate domain output or domain-specific FPR. Domain-only, multi-domain and H1–H8/background/pre-onset target0 FPR with exact supports are in [all-family/domain evidence](../evidence/stage22/all_family_domain_performance.json). Full B−A family and domain contrasts are in paired evidence; no difficult family was removed.

### Performance outside A1

| Model | TP/support outside A1 | Recall |
| --- | ---: | ---: |
| A40-XGB | 1271/1563 | 0.813180 |
| B44-XGB | 1285/1563 | 0.822137 |
| A40-HGB | 1339/1563 | 0.856686 |
| B44-HGB | 1331/1563 | 0.851567 |

This separates the large A1-positive population from remaining union positives. It does not create another classifier or alter labels.

## 6. Shortcut dependence and missingness

No extra fitted diagnostic model ran. The preregistered no-fit permutation analysis reused the exact Stage18 uniform3000 Validation indices and three paired semantic-field permutations. Each AP baseline uses that same sample; type is permuted jointly before its one-hot transform. Signed mean AP drops and repeatSD are saved for every field. Absolute shares are descriptive normalization, not causal contributions.

| Model | Growth absolute AP-drop mass | Four added fields mass | Same-sample baseline AP |
| --- | ---: | ---: | ---: |
| A40-XGB | 37.746% | 0.000% | 0.985900 |
| B44-XGB | 38.215% | 0.568% | 0.987141 |
| A40-HGB | 37.322% | 0.000% | 0.986992 |
| B44-HGB | 37.270% | 0.494% | 0.987700 |

The sample contains 7 S2 and 3 S4 positives. Sparse family support, correlated features and off-manifold permutations limit interpretation; added fields change the normalization denominator. A smaller growth share alone is not evidence of less shortcut reliance. Full signed drops/group shares: [component dependence](../evidence/stage22/permutation_component_dependence.json).

| Model | History slice | Target1 / rows | TP / positives | FP / negatives |
| --- | --- | ---: | ---: | ---: |
| A40-XGB | new_baseline_missing | 602/3190 | 551/602 | 18/2588 |
| A40-XGB | new_baseline_observed | 2428/11810 | 2187/2428 | 100/9382 |
| B44-XGB | new_baseline_missing | 602/3190 | 550/602 | 16/2588 |
| B44-XGB | new_baseline_observed | 2428/11810 | 2201/2428 | 99/9382 |
| A40-HGB | new_baseline_missing | 602/3190 | 565/602 | 19/2588 |
| A40-HGB | new_baseline_observed | 2428/11810 | 2237/2428 | 120/9382 |
| B44-HGB | new_baseline_missing | 602/3190 | 563/602 | 19/2588 |
| B44-HGB | new_baseline_observed | 2428/11810 | 2232/2428 | 117/9382 |

Both new baseline fields share their historical availability marker. These associations do not prove missingness caused predictions. The four additions explicitly reproduce **individual S2/S4 target components**; jointly better rule approximation does not establish real laundering detection. Identity, origin and family labels remain diagnostic-only and outside X. No target evaluator, private provenance or future fields are passed to `.fit`/`.predict_proba`. [Error and shortcut slices](../evidence/stage22/shortcut_error_slices.json) include type, origin, agents, subjects and episode/day groups for both partitions.

## 7. Community and subject concentration

| Model | Validation community | FN / positives | FP / negatives |
| --- | --- | ---: | ---: |
| A40-XGB | 0 | 110/1027 | 30/3973 |
| A40-XGB | 1 | 93/1016 | 48/3984 |
| A40-XGB | 2 | 89/987 | 40/4013 |
| B44-XGB | 0 | 106/1027 | 31/3973 |
| B44-XGB | 1 | 85/1016 | 46/3984 |
| B44-XGB | 2 | 88/987 | 38/4013 |
| A40-HGB | 0 | 93/1027 | 35/3973 |
| A40-HGB | 1 | 69/1016 | 56/3984 |
| A40-HGB | 2 | 66/987 | 48/4013 |
| B44-HGB | 0 | 93/1027 | 37/3973 |
| B44-HGB | 1 | 74/1016 | 55/3984 |
| B44-HGB | 2 | 68/987 | 44/4013 |

- A40-XGB: FN on 143 wallet subjects; FP on 67.
- B44-XGB: FN on 141 wallet subjects; FP on 65.
- A40-HGB: FN on 124 wallet subjects; FP on 78.
- B44-HGB: FN on 125 wallet subjects; FP on 78.

Per-subject support, recall/FPR and leading FN/FP groups are retained in [subject summary](../evidence/stage22/subject_error_summary.json) and full slice evidence. Wallet subject=sender forW2W/cashserviced; N1 family uses receiver, agent families currentagent. NO_AGENT is an absence category, not an entity. Episode/day grouping and three communities describe dependence; they do not provide a reliable independent-population sample. Any inherited Wilson bounds are descriptive independence-based intervals only, not significance evidence.

## 8. Reproducibility, runtime and artifacts

40-field baseline reproduction of Stage18 saved probabilities: `{"A40-HGB": {"train": {"exact": true, "max_abs_difference": 0.0}, "validation": {"exact": true, "max_abs_difference": 0.0}}, "A40-XGB": {"train": {"exact": true, "max_abs_difference": 0.0}, "validation": {"exact": true, "max_abs_difference": 0.0}}}`. This checks controlled parity without loading or modifying historical fitted models. Each newly saved experimental pipeline was reloaded locally and its first100 Validation probabilities matched exactly. This checks serialization, not another fit or independent evaluation.

Fit seconds: `{"A40-HGB": 4.726647799951024, "A40-XGB": 2.5322730999905616, "B44-HGB": 4.900594800012186, "B44-XGB": 2.551948699983768}`. Permutation seconds:30.560. Peak process working set:529.9MiB, including all retained models/data; not per-model marginal memory. Sequential, one worker. Warnings by model: `{"A40-HGB": [], "A40-XGB": [], "B44-HGB": [], "B44-XGB": []}`. [Runtime](../evidence/stage22/runtime_resource_usage.json).

New models and saved probabilities are under `ml_v4/development_comparison/artifacts/`, explicitly EXPERIMENTAL. Reload requires the frozen runtime and `ml_v4/development_training` on the module search path for the unchanged `preprocessing.FrozenPreprocessor` class. Load only trusted hash-verified local joblib artifacts. Each candidate has its own preprocessing; historical artifacts remain untouched.

## 9. Scientific limits, preservation and recommendation

S1/S2/S4/N1/N3/N4/A2/A3/A4 still miss original support objectives. The feature change creates no positives or independent subjects. Validation already drove the hypotheses and cannot supply independent confirmation. Stronger deterministic policy reproduction is narrower than actual AML detection; no real-world generalization or operational effectiveness is established.

Stage16T remains a40-field protocol, incompatible by default with44. Independent custody remains unavailable, original Final/Independent remain SEALED_QUARANTINED with public supportFAIL facts, and no private counts were obtained. Any affected independent evaluation requires a separate compatibility amendment and approvals; no challenge is generated here. No Flask/MySQL/dashboard changes occurred. Stage16V's incomplete broader Stage15A snapshot is retained without weakening expectations.

**290 named protected files** match before/after hashes, including both matrix versions, labels/data, Stage18 artifacts and ledger, original predicates, V1 and V3 integration. Sealed bytes are unread and excluded from the claim. [Preservation](../evidence/stage22/preservation_verification.json).

Preserve all four experimental artifacts and the historical selected XGBoost/HGB roles. Review the observed information/accuracy tradeoffs and support limitations; any next study, candidate-selection rule, challenge amendment or evaluation needs separate authorization. No additional fitting, threshold search or promotion follows.

The decision follows the descriptive interpretation frozen before fitting. A, if returned, applies to consistent S2/S4 primary development contrasts and does not assert every metric improved, full-family adequacy or a new selected model. B indicates no primary gains; mixed directions are C. All tradeoffs remain reported. [Recommendation](../evidence/stage22/recommendation.json), [limitations](../evidence/stage22/scientific_limitations.json).

## 10. Final decision

**C — EXPERIMENT INCONCLUSIVE**

Four authorized attempts are consumed. No further fit, threshold optimization, independent evaluation, challenge generation, integration, promotion or automatic Stage23 is authorized.

V4 STAGE 22 COMPLETE — WAITING FOR APPROVAL.
