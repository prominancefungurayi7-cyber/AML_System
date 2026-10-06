> Superseded by [V3_STAGE10_OVERALL_REPORT.md](V3_STAGE10_OVERALL_REPORT.md), the single consolidated report. It includes the full contract, results and newly verified limitations; the earlier unqualified PASS below is historical.

# MODEL V3 — STAGE 10 REPRODUCIBILITY

**Result: PASS.**

Train and Validation extraction was executed twice from the frozen V3 development inputs. Row order, feature order, numeric values and targets were identical. The emitted development matrix hashes are recorded in [`stage10_reproducibility.json`](stage10_reproducibility.json).

Only these matrices were created:

- `ml_v3/features/development/train/`
- `ml_v3/features/development/validation/`

No evaluation feature directory exists. No classifier, preprocessing fit, threshold search or model artifact was created.
