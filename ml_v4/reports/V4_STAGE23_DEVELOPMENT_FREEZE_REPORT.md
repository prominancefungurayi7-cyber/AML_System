# MODEL V4 — STAGE 23 DEVELOPMENT MODEL FREEZE AND RESEARCH DECISION

**A — ORIGINAL 40-FEATURE V4 DEVELOPMENT CANDIDATE RETAINED AND FROZEN**

Retain the **original Stage18 `primary_XGB`**,40 semantic fields/42 estimator columns, threshold0.50, as the official V4 **development reference**. This is a reference/hash freeze, not a new model, production promotion or independent validation. HGB remains the comparator. All Stage21/22 experimental44 artifacts remain preserved. No model was deserialized, fitted or executed; no extraction, new diagnostics requiring prediction, tuning or data generation occurred.

## 1. Authority and evidence verification

Stage15/15A specifications;16R–16V retained-data, support, challenge and custody decisions;17/18 original feature/model evidence;19/20 diagnosis/design;21 implementation and22 comparison were reviewed through exact named public reports/evidence. **328 protected hashes** match. Saved Stage18 primary_XGB Train/Validation metric records match Stage22 A40-XGB records exactly; the latter records exact probability reproduction. This stage checks those records and hashes without recomputing model outputs. Stage18 ledger16 and Stage22 ledger4 starts/completions remain unchanged, cumulative20, no authorized new fits. [Evidence verification](../evidence/stage23/evidence_verification.json).

## 2. Stage22 remains inconclusive

Historical decision: **C — EXPERIMENT INCONCLUSIVE**. It is not retroactively changed by this freeze.

For XGBoost,40→44 gave MacroF1 **0.956670→0.958415**, recall **0.903630→0.907921**, FPR **0.009858→0.009607**, FN **292→279**, FP **118→115**. S2 rose **11/23→18/23**, recall **0.4783→0.7826**. S4 remained **4/16** and S4-only remained **0/12**. **A4 deteriorated151/222→144/222**. The small aggregate gain does not resolve the primary S4 weakness or negate other losses.

For HGB, MacroF1 fell **0.961632→0.961164**, recall0.924752→0.922442 and FN228→235, while FP139→136. S2 improved13→16/23 but S4 stayed5/16 and exclusive S4 stayed1/12. The same S4 count masks a recovered event and a lost event, not identical predictions.

| Family | XGB40→44 TP/support | HGB40→44 TP/support |
| --- | --- | --- |
| S1 | 126→130/132 | 130→132/132 |
| S2 | 11→18/23 | 13→16/23 |
| S3 | 492→491/546 | 491→490/546 |
| S4 | 4→4/16 | 5→5/16 |
| N1 | 77→83/101 | 85→87/101 |
| N2 | 381→379/429 | 380→382/429 |
| N3 | 122→123/130 | 115→112/130 |
| N4 | 123→122/144 | 120→120/144 |
| A1 | 1467→1466/1467 | 1463→1464/1467 |
| A2 | 109→114/148 | 123→119/148 |
| A3 | 255→255/255 | 255→255/255 |
| A4 | 151→144/222 | 197→189/222 |

These exploratory comparisons reused Validation that had already informed feature design. More direct S2/S4 components can improve policy approximation without independent confirmation or real-world benefit. Growth absolute permutation mass remains 37.7% in the original XGB and 38.2% in44; mass shares are method-dependent, correlated and not causal. [Stage22 interpretation](../evidence/stage23/stage22_interpretation.json).

## 3. Freeze decision and alternatives

Retaining40 preserves the candidate selected under Stage18's preregistered eligibility/FPR-within-MacroF1-tolerance rule, before the Stage19/20 redesign. HGB had higher MacroF1, but original XGB's lower FPR satisfied the frozen selection tradeoff. Stage23 neither reranks by the largest MacroF1 nor converts the later adaptive44 comparison into a new selection rule.

Promoting44 is not sufficiently justified: S2 gains are real observed development counts, but S4 is unresolved, XGB's aggregate gain is small, A4 and other families decline, and HGB does not improve aggregate MacroF1. Sparse support and absent independent evaluation apply to both versions. Retain44 as useful research evidence, not delete or devalue it.

Freezing neither would unnecessarily require another adaptive development cycle to preserve a technical research reference. The freeze instead closes current development with explicit claim limits. Additional work is essential for independent or operational claims, not for documenting the completed prototype. [Decision rationale](../evidence/stage23/representation_decision.json).

## 4. Exact frozen references

Freeze identifier: **`v4.development.freeze.stage23.1`**. It references the original Stage18 artifact, **not** the Stage22 A40 refit. Model bytes, filenames and application settings are unchanged.

| Reference | Existing path | SHA-256 |
| --- | --- | --- |
| pipeline | `ml_v4/development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib` | `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18` |
| standalone_fitted_preprocessor | `ml_v4/development_training/artifacts/selected_preprocessor_EXPERIMENTAL.joblib` | `a6a1266c830511ecbab6487157f75a3d47fbffbb0a0e86580a861f3f4e222f41` |
| preprocessor_source | `ml_v4/development_training/preprocessing.py` | `698bad02e88620d741af509e03367fb52a873561bda512c919b297605bd3777d` |
| feature_specification | `ml_v4/design/v4_feature_spec.json` | `23804a05080b84304dd8d25c441b2901b3fb101dc412d7fd19eef849a8cc4204` |
| HGB_comparator | `ml_v4/development_training/artifacts/primary_HGB_EXPERIMENTAL.joblib` | `156b499c6b6e5751d638ebedc142cc0b318bd0344d86a2943c3705f3197ac82b` |

Feature version `v4.features.1`; original ordered40 fields and42 encoded columns are recorded in [freeze record](../evidence/stage23/development_candidate_freeze.json). Threshold **score>=0.50**, seed2026092915, no fitted calibration. Preprocessing is original `preprocessing.FrozenPreprocessor`: exact marker conversion, Train-only median(empty0), no indicators, standard scaling, fixed3-type one-hot. Fitted state is embedded in the original pipeline and referenced separately; it was not recreated.

Historical runtime pins: Python3.14.3, NumPy2.4.3, scikit-learn1.9.0, XGBoost3.4.1, one worker. Current supplementary package pins are SciPy1.18.0, joblib1.5.3, threadpoolctl3.6.0; these are observed metadata, not a claim that Stage18 captured their wheel/install hashes. The reference freeze is not an independently validated deployment image lock. No packages or infrastructure were installed. Full runtime qualifications, interpreter hash and exact parameters are preserved in the freeze record.

Dataset identity remains `mobile_money_aml_synthetic_100k_v4`, the Stage16R retained draw governed by Stage15+15A, generator `v4.generator.1.stage16r.1`. Target semantic version `v4.predicates.1`, materialized evaluator `v4.predicates.1.stage16r.1`, temporal `v4.temporal.1`. Exact dataset-manifest, development input, target/schema/source and model hashes bind the freeze; no label or dataset version is replaced. No sealed private manifest or byte content was inspected.

## 5. Retained development results

| Validation measure | Value |
| --- | ---: |
| Accuracy | 0.972667 |
| Balanced accuracy | 0.946886 |
| Macro F1 | 0.956670 |
| Suspicious-pattern precision | 0.958683 |
| Suspicious-pattern recall | 0.903630 |
| False-positive rate | 0.009858 |
| ROC-AUC | 0.996046 |
| Average Precision | 0.985972 |

Confusion **[[11852,118],[292,2738]]**, order[[TN,FP],[FN,TP]]. Positive recall2738/3030, precision2738/2856, FPR118/11970. These are reused synthetic development Validation results, not independent-test metrics or real-world accuracy. AP means Average Precision, not trapezoidal PR area. Train metrics and full family/domain records remain available in [final metrics](../evidence/stage23/final_development_metrics.json).

| Family | TP/support | Recall | FN | Original support policy |
| --- | ---: | ---: | ---: | --- |
| S1 | 126/132 | 0.9545 | 6 | Shortfall |
| S2 | 11/23 | 0.4783 | 12 | Shortfall |
| S3 | 492/546 | 0.9011 | 54 | Count minimum met |
| S4 | 4/16 | 0.2500 | 12 | Shortfall |
| N1 | 77/101 | 0.7624 | 24 | Shortfall |
| N2 | 381/429 | 0.8881 | 48 | Count minimum met |
| N3 | 122/130 | 0.9385 | 8 | Shortfall |
| N4 | 123/144 | 0.8542 | 21 | Shortfall |
| A1 | 1467/1467 | 1.0000 | 0 | Count minimum met |
| A2 | 109/148 | 0.7365 | 39 | Shortfall |
| A3 | 255/255 | 1.0000 | 0 | Shortfall |
| A4 | 151/222 | 0.6802 | 71 | Shortfall |

High observed A1/A3 recall and strong S1/N3 counts are bounded development strengths. Retained S2/S4 weaknesses, S4-only0/12, A4/A2/N1 misses, N3 route-summary loss and growth dependence remain. Family labels overlap and do not indicate which component caused a positive prediction. [Family register](../evidence/stage23/family_strengths_weaknesses.json).

## 6. Final limitations and levels of evidence

| Limitation | Scope |
| --- | --- |
| L01 — Synthetic data | Generic Zimbabwean mobile-money assumptions without operator calibration; artificial inventories/isolated local units; benchmark is not a natural prevalence estimate. |
| L02 — Nine support shortfalls | S1,S2,S4,N1,N3,N4,A2,A3,A4 miss original Train1200/Validation300 count objectives; no waiver. |
| L03 — S2 sparse support | 112 Train,23 Validation positives; Validation7 subjects/7clusters. Retained recall11/23;44-field improvement exploratory. |
| L04 — S4 poor recall | 128 Train,16 Validation positives; retained4/16. No net Stage22 improvement. |
| L05 — S4-only failure | Retained XGB0/12 exclusive Validation detections; overlap accounts for all4 S4 detections without proving causal attribution. |
| L06 — A1/growth dependence | A1 covers1467 Validation positives and retained detects all; growth importance and correlated agent primitives remain substantial. |
| L07 — Repeated Validation inspection | Used for selection, diagnosis and representation hypotheses; no independent confirmation from reuse. |
| L08 — Three Validation communities | Entities/episodes are dependent; row-based intervals are not reliable population uncertainty. |
| L09 — Family overlap | Family recalls do not add and union-positive detections need not demonstrate distinctive family reasoning. |
| L10 — No independent external audit | Hand checks and separate arithmetic in the same developer environment do not constitute outside review. |
| L11 — No independent challenge evaluation | Original holdouts quarantined with public supportFAIL; no challenge generated or scored. |
| L12 — Custody unavailable | Stage16V independent administrator/storage/secret/logging boundary remains unprovisioned. |
| L13 — No real mobile-money validation | No representative real operator cohort evaluated; synthetic findings cannot establish transport. |
| L14 — No production effectiveness evidence | No operational PPV, calibration, review capacity, latency, drift or downstream decision-impact validation. |
| L15 — Historical snapshot gap | Stage15A broad historical preservation inventory remains incomplete; exact named checks do not repair absent archive. |
| L16 — Representation and approximation | N3 selected-route loss and other omitted components remain; probability is not calibrated certainty of laundering. |

**Technical development success:** feature correctness/parity/replay, bounded training and saved-result verification support a reproducible development reference in the documented scope.

**Independent scientific validation:** not achieved. No sufficiently supported independent challenge evaluation or independent external audit exists; custody remains unavailable.

**Real-world AML validation:** not achieved. No real operator cohort or production workflow-effectiveness evidence supports such a claim. A high synthetic score does not bridge these missing levels. [Limitations register](../evidence/stage23/limitations_register.json).

## 7. Model card and dissertation-ready summary

The [development model card](../evidence/stage23/development_model_card.md) and [machine-readable card](../evidence/stage23/development_model_card.json) specify intended/non-intended use, target/populations, schema/preprocessing, threshold, results/failure modes, hashes, dependencies and evaluation status.

> This model identifies transaction patterns defined as suspicious within the synthetic research benchmark. It does not determine that money laundering has occurred.

Human review is required; positive means review-pattern evidence and negative does not certify benignity, including ineligible histories. The [dissertation-ready results summary](../evidence/stage23/dissertation_results_summary.md) records dataset rationale, domains, compared algorithms, retained candidate, exact Validation metrics, family strengths/weaknesses and claim limits. It explicitly identifies Validation as reused development data.

## 8. Future work, separately scoped

Future work may address representative real mobile-money data under appropriate access; S4 approximation/support; additional communities and family diversity; independent evaluation/custody; robustness; and a predeclared40-versus44 comparison on fresh data. Calibration or operational threshold design would require dedicated authorized development/calibration evidence, then freezing before untouched final evaluation—not tuning on final outcomes. None is performed or automatically authorized now. [Future-work register](../evidence/stage23/future_work_register.json).

Stage16T stays40-field. Retaining40 avoids a feature-dimension change but does not waive its custody, support, sealing, freeze or approval gates.44 would require a separately approved protocol amendment before affected evaluation. Original quarantines and public supportFAIL remain.20 attempts are consumed; the inherited36 ceiling grants no remaining authorization, and expired slots remain expired.

## 9. Preservation and final decision

328 exact named historical/input artifacts are unchanged, including original and44 matrices/models, both fit ledgers, twelve predicates, development data/labels, V1 production and V3 integration files. Scope excludes unread sealed bytes and does not claim every file on disk. The Stage16V broader historical snapshot gap remains documented. No Flask, MySQL, API, dashboard or application-integration change occurred. Only this report, new Stage23 evidence/documents and the documentation builder were written. [Preservation](../evidence/stage23/preservation_verification.json), [artifact manifest](../evidence/stage23/artifact_hash_manifest.json).

**A — ORIGINAL 40-FEATURE V4 DEVELOPMENT CANDIDATE RETAINED AND FROZEN**

This final development freeze authorizes no independent evaluation, production use, new fits, additional features, threshold work, data generation or automatic next development cycle.

V4 STAGE 23 COMPLETE — WAITING FOR APPROVAL.
