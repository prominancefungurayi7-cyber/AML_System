> Superseded by [V3_STAGE10_OVERALL_REPORT.md](V3_STAGE10_OVERALL_REPORT.md), the single consolidated report. It includes the full contract, results and newly verified limitations; the earlier unqualified PASS below is historical.

# MODEL V3 — STAGE 10 FEATURE AUDIT

**Result: PASS — 32 features, Train/Validation only.**

The frozen Stage 8 proposal was implemented as exactly 32 ordered columns: 3 current-event, 7 structuring, 10 network, 9 agent and 3 history-coverage features. No exact duplicate names or impossible domains were found. The proposal’s N3 path summary and N4 role-aware funding summaries are represented as behavioural quantities rather than predicate flags.

| Partition | Rows | Features | Target 0 | Target 1 | NaN | Infinity | Duplicate row IDs |
|---|---:|---:|---:|---:|---:|---:|---:|
| Train | 60,000 | 32 | 39,781 | 20,219 | 0 | 0 | 0 |
| Validation | 15,000 | 32 | 9,945 | 5,055 | 0 | 0 | 0 |

All matrix values are numeric and finite. `X` contains no identifiers, labels, scenario metadata, provenance, witness data, risk scores or rule scores. Row IDs are stored separately. Only `decision_point_target` supplies `y`.

The frozen Stage 9 development manifest still matches every Train and Validation input hash after extraction. Evaluation partition bytes were not opened or enumerated.

Per-feature statistics, ranges, quantiles, zero rates and target overlap are in [`stage10_feature_statistics.json`](stage10_feature_statistics.json), [`stage10_target_overlap.json`](stage10_target_overlap.json), and [`stage10_shift_audit.json`](stage10_shift_audit.json).

## Distribution diagnosis

Current-event indicators are binary; event and counterparty quantities are count-valued; shares, skews and acceleration values are ratio-valued; amounts and cumulative values are right-skewed/heavy-tailed; coverage and path length are bounded. The finite `-1.0` sentinel is visible in the statistics for unavailable baseline ratios. Train/Validation zero-rate and mean differences are reported descriptively without changing definitions or fitting preprocessing. Future preprocessing should use Train-fitted scaling or clipping only, with missing-sentinel handling fixed before any classifier stage.
