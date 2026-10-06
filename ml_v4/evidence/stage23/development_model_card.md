# V4 development model card — original40 primary_XGB

**Development reference only; no production approval.** Freeze reference `v4.development.freeze.stage23.1` points to the unchanged Stage18 model.

> This model identifies transaction patterns defined as suspicious within the synthetic research benchmark. It does not determine that money laundering has occurred.

## Use and inputs

Intended for reproducible synthetic research and separately authorized human-review decision support. Not intended for autonomous account actions, regulatory certification or determining criminal intent. Input version `v4.features.1`:40 semantic fields/42 estimator columns, causal35d histories, exact roles and integer-cent aggregation; raw IDs/provenance never enter X. Train-only median imputation and scaling with fixed type one-hot; threshold **score>=0.50**. No fitted calibration.

## Population and target

Train60000 scored+14400 warm-up,1200wallets/96agents in12communities. Validation15000 scored+3600warm-up,300wallets/24agents in3communities. Entities/history disjoint. Generic synthetic Zimbabwean mobile-money assumptions, not operator-calibrated data. Target `v4.predicates.1` materialized by `v4.predicates.1.stage16r.1` is a twelve-predicate observable review-pattern union; cold-start ineligibility can produce0 without establishing benignity.

## Development results and failure modes

MacroF10.956670; precision0.958683; recall0.903630; FPR0.009858; accuracy0.972667; balancedaccuracy0.946886; ROC-AUC0.996046; AP0.985972. Confusion [[11852,118],[292,2738]]. Reused synthetic Validation, not independent test.

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

Known failures include S4-only0/12, sparse S2/S4, A4/A2/N1 misses, N3 selected-route loss, growth dependence and correlated/overlapping families. No independent external audit or challenge evaluation exists; custody unavailable. No real mobile-money validation or production-effectiveness evidence. A human must review context; probability is not calibrated certainty of laundering.

## Integrity and runtime

Pipeline `ml_v4/development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib` SHA-256 `555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`. Standalone fitted preprocessor SHA-256 `a6a1266c830511ecbab6487157f75a3d47fbffbb0a0e86580a861f3f4e222f41`. Python3.14.3, NumPy2.4.3, scikit-learn1.9.0, XGBoost3.4.1 are recorded training pins. Freeze-observed supplementary packages: SciPy1.18.0, joblib1.5.3, threadpoolctl3.6.0; these are not retroactive install-lock evidence. Exact references, all feature order/markers, package qualifications and hashes are in [machine-readable card](development_model_card.json) and [candidate freeze](development_candidate_freeze.json).

Only trusted local hash-verified artifacts may later be loaded under separate authorization; the custom class is `preprocessing.FrozenPreprocessor` from the frozen source. No deserialization occurred in Stage23. Original evaluations remain SEALED_QUARANTINED/supportFAIL; Stage16T40-feature semantic alignment is not custody/support or execution approval.44 artifacts remain research-only and require a protocol amendment for future independent use.
