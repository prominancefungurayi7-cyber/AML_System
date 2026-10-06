# MODEL V2 — STAGE 6 CONTROLLED FEATURE IMPROVEMENT

**Decision: retain the frozen 30-feature Stage 5 baseline.** None of the eight prespecified candidate features, tested in four groups and together, improved Validation Macro F1 over the reproduced Stage 5 result at threshold 0.50. The result does not prove the representation is sufficient: some agent slices and PR-AUC improved, but false positives increased.

## Method

The [representation gap analysis](V2_STAGE6_REPRESENTATION_GAP_ANALYSIS.md) and [candidate feature contract](V2_STAGE6_CANDIDATE_FEATURE_CONTRACT.md) were fixed before the ablation. Each feature uses only earlier transactions in its own Train or Validation partition, ordered by `(timestamp, transaction_id)`. Labels and scenario metadata were used for metrics and diagnostic slices only. The original 30 Stage 3 features and Stage 5 model specification were held fixed: `s5_gradient_boosting_060`, positive weight 4, seed `20260921`, and threshold 0.50. Train-fitted clipping applied to the original 30 columns as in Stage 5. The candidate columns retain their contract values. The run took 217.5 seconds.

| Configuration | Train Macro F1 | Validation Macro F1 | Suspicious recall | Suspicious F1 | PR-AUC | FPR |
|---|---:|---:|---:|---:|---:|---:|
| Baseline 30 | 0.6652 | **0.5983** | 0.3211 | 0.2999 | 0.2591 | **0.1119** |
| + network history | 0.6652 | 0.5968 | 0.3167 | 0.2969 | 0.2574 | 0.1114 |
| + receiver history | 0.6645 | 0.5933 | 0.3161 | 0.2922 | 0.2602 | 0.1156 |
| + agent growth and concentration | 0.6675 | 0.5964 | **0.3400** | 0.3019 | **0.2785** | 0.1244 |
| + agent cash flow | 0.6667 | 0.5927 | 0.3133 | 0.2908 | 0.2611 | 0.1148 |
| + all eight | 0.6688 | 0.5982 | 0.3378 | **0.3036** | 0.2740 | 0.1210 |

The agent growth and concentration group raised agent domain recall from 0.2317 to 0.3017, including A1 from 0.2067 to 0.2867 and A2 from 0.0867 to 0.1933. It also raised overall FPR from 0.1119 to 0.1244 and H7 FPR from 0.3321 to 0.3830. The full set raised agent recall to 0.2917 and A4 recall from 0.0467 to 0.1067, but H7 FPR reached 0.3855. N3 reciprocal-cycle recall fell from 0.0200 to 0.0133 with the network group and full set; the proposed historical two-way flow measures did not resolve that gap. H1 remained high at 0.4182–0.4327 across additions versus 0.4303 at baseline.

## Protection and next decision

The Stage 6 causal semantics tests pass. Row IDs matched the frozen 60,000 Train and 15,000 Validation feature rows exactly; all candidate values were finite. Before/after SHA-256 comparison passed for 347 V1/application files and 37 V2 dataset/feature input files. The runner accessed development partitions through `load_development`; it did not access Final Test or Independent Evaluation. No threshold search, final model freeze, or application integration occurred. Full metrics, confusion matrices, and domain/family/hard-negative counts are in [stage6_ablation_results.json](stage6_ablation_results.json); the reproducible runner is `src/run_stage6.py`.

The Stage 5 baseline remains the development reference. A further feature design should address reciprocal cycles and legitimate H1/H7 overlap before another model comparison; the current candidates are not promoted. Threshold optimization remains premature against the stated development targets.

V2 STAGE 6 COMPLETE — WAITING FOR APPROVAL.
