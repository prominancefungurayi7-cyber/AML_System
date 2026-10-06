# MODEL V3 — STAGE 9 STRUCTURAL AUDIT

**Result: PASS.** The audit covered all four partitions and all 100,000 rows.

- Global transaction IDs are unique and cover 1–100,000; rows are ordered by timestamp and ID within each partition.
- Wallet and agent counts are 1,000 and 160 globally, with partition isolation (600/150/150/100 wallets and 96/24/24/16 agents).
- Transaction types, channels, currencies, amount support, cash direction and no-self-loop constraints pass.
- The observable transaction schema contains no target, scenario, family, campaign or witness field.
- The universal evaluator re-aligned sampled Train and Validation rows; all positive rows have witnesses.
- No feature extraction or model training ran.

Full check counters and partition summaries are in [`V3_STAGE9_STRUCTURAL_AUDIT.json`](V3_STAGE9_STRUCTURAL_AUDIT.json).
