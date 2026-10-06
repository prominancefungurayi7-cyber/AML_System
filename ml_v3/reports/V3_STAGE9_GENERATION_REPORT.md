# MODEL V3 — STAGE 9 GENERATION REPORT

**Dataset:** `mobile_money_aml_synthetic_100k_v3`  
**Seed:** `20260922`  
**Result:** PASS

Stage 9 generated exactly 100,000 raw transaction rows with disjoint partition entities:

| Partition | Rows | Wallets | Agents | Campaign members | Hard origins | Routine |
|---|---:|---:|---:|---:|---:|---:|
| Train | 60,000 | 600 | 96 | 14,400 | 19,200 | 26,400 |
| Validation | 15,000 | 150 | 24 | 3,600 | 4,800 | 6,600 |
| Final Test | 15,000 | 150 | 24 | 3,600 | 4,800 | 6,600 |
| Independent | 10,000 | 100 | 16 | 2,400 | 3,200 | 4,400 |

The raw observable schema contains transaction fields only. Labels are written separately in `ground_truth_v3.csv`; provenance fields are retained for audit alignment and are not inputs to a classifier. The universal decision-point evaluator uses only same-partition events strictly earlier than `(event_timestamp, transaction_id)` plus the current event. It covers S1–S4, N1–N4 and A1–A4.

Machine-readable generation details, target counts, witness counts and hashes are in [`V3_STAGE9_GENERATION.json`](V3_STAGE9_GENERATION.json).
