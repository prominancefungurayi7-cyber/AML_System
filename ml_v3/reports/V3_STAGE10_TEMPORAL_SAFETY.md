> Superseded by [V3_STAGE10_OVERALL_REPORT.md](V3_STAGE10_OVERALL_REPORT.md), the single consolidated report. It includes the full contract, results and newly verified limitations; the earlier unqualified PASS below is historical.

# MODEL V3 — STAGE 10 TEMPORAL SAFETY

**Result: PASS.**

Every historical lookup is partition-local and strictly earlier than the current `(event_timestamp, transaction_id)` key. Current-inclusive features add only the current observable event. State is updated after emission.

The causal tests passed:

- Appending a future transaction leaves every earlier feature vector unchanged.
- Equal timestamps are ordered by transaction ID.
- Changing the current amount leaves prior-only path topology and coverage unchanged while changing permitted current-derived quantities.
- An arbitrary prior multi-edge return path is represented without using future edges.
- Agent-assisted W2W contributes to agent service history; principal W2W does not enter agent cash direction.
- Funding and outward-share features are emitted only from observable prior funding and current outward roles.

Machine-readable results are in [`stage10_temporal_tests.json`](stage10_temporal_tests.json).
