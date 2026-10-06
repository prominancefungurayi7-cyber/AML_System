> Superseded by [V3_STAGE10_OVERALL_REPORT.md](V3_STAGE10_OVERALL_REPORT.md), the single consolidated report. It includes the full contract, results and newly verified limitations; the earlier unqualified PASS below is historical.

# MODEL V3 — STAGE 10 ORACLE-LEAKAGE AUDIT

**Result: PASS.**

No feature is a predicate result, onset flag, eligibility flag, evidence-family flag, campaign field or provenance field. The feature-name audit found no forbidden metadata names. Identical observable histories with changed private campaign, origin, signal and witness metadata produced identical feature vectors.

Some association with the target is expected because both the target and features use observable history. The target-overlap audit found overlapping target-0 and target-1 ranges for every feature in both Train and Validation; no single feature showed perfect interval separation. No classifier, feature selection procedure or threshold optimization was run.

The complete diagnostic is in [`stage10_target_overlap.json`](stage10_target_overlap.json) and [`stage10_temporal_tests.json`](stage10_temporal_tests.json).
