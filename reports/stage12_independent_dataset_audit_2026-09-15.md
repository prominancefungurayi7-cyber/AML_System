# Stage 12 Independent Dataset Audit Report

**Date:** 2026-09-15  
**Dataset Version:** ecocash_aml_synthetic_100k_v1  
**Audit Status:** PASS  
**Auditor:** Stage 12 Independent Audit Script  

---

## Executive Summary

The Stage 11 generated dataset `ecocash_aml_synthetic_100k_v1` has been independently audited for suitability in Stage 13 feature construction. All critical audit checks passed successfully. The dataset is fully compliant with Stage 10B, Stage 10C, and Stage 11 specifications.

**Final Recommendation:** PROCEED TO STAGE 13

---

## 1. Dataset Identity

### Verified Files
- `data/ecocash_aml_synthetic_100k_v1/transactions.csv` ✅
- `data/ecocash_aml_synthetic_100k_v1/ground_truth.json` ✅
- `data/ecocash_aml_synthetic_100k_v1/entity_metadata.json` ✅
- `data/ecocash_aml_synthetic_100k_v1/generation_manifest.json` ✅

### Identity Verification
- **Dataset Version:** ecocash_aml_synthetic_100k_v1 ✅
- **Transaction Count:** 100,000 (expected: 100,000) ✅
- **Ground Truth Count:** 100,000 (expected: 100,000) ✅
- **Transaction IDs:** All unique ✅
- **Event Sequences:** All unique ✅

**Status:** PASS

---

## 2. Dataset Integrity

### Internal Consistency
- **Transactions to Ground Truth Mapping:** 1:1 correspondence ✅
- **Manifest to Actual Dataset:** Matches ✅
- **Entity Metadata to Transactions:** Consistent ✅

**Status:** PASS

---

## 3. Raw Transaction Schema Audit

### Required Fields
All required fields present in transaction dataset:
- transaction_id ✅
- event_timestamp ✅
- event_sequence ✅
- sender_wallet ✅
- receiver_wallet ✅
- amount ✅
- transaction_type ✅
- channel ✅
- agent_id ✅
- partition ✅

### Schema Validity
- **Sender != Receiver:** 0 violations ✅
- **Amount Positive:** 0 non-positive amounts ✅
- **Timestamp Validity:** All timestamps valid ✅
- **Channel Consistency:** agent_id matches channel field ✅

**Status:** PASS

---

## 4. Exact Population Audit

### Entity Counts
- **Wallets:** 2,000 (expected: 2,000) ✅
- **Agents:** 160 (expected: 160) ✅
- **Customers:** 2,000 (derived from wallets) ✅

### Wallet-Customer Mapping
- **Mapping Type:** 1:1 ✅
- **Unique Customers:** 2,000 ✅
- **Mapping Consistency:** Every wallet has exactly one customer ✅

**Status:** PASS

---

## 5. Partition Isolation Audit

### Partition Transaction Counts
- **Train:** 60,000 (expected: 60,000) ✅
- **Validation:** 15,000 (expected: 15,000) ✅
- **Final Test:** 15,000 (expected: 15,000) ✅
- **Independent:** 10,000 (expected: 10,000) ✅

### Partition Entity Counts
- **Train Wallets:** 1,200 (expected: 1,200) ✅
- **Validation Wallets:** 300 (expected: 300) ✅
- **Final Test Wallets:** 300 (expected: 300) ✅
- **Independent Wallets:** 200 (expected: 200) ✅

- **Train Agents:** 96 (expected: 96) ✅
- **Validation Agents:** 24 (expected: 24) ✅
- **Final Test Agents:** 24 (expected: 24) ✅
- **Independent Agents:** 16 (expected: 16) ✅

### Cross-Partition Edges
- **Cross-Partition Wallet Edges:** 0 (expected: 0) ✅
- **Agent Partition Consistency:** 0 mismatches ✅

**Status:** PASS

---

## 6. Class Distribution Audit

### Overall Class Distribution
- **Normal:** 88,000 (expected: 88,000) ✅
- **Suspicious:** 12,000 (expected: 12,000) ✅
- **Label Values:** Only 0 and 1 (binary) ✅

### Partition Class Counts
- **Train Normal:** 52,800 (expected: 52,800) ✅
- **Train Suspicious:** 7,200 (expected: 7,200) ✅
- **Validation Normal:** 13,200 (expected: 13,200) ✅
- **Validation Suspicious:** 1,800 (expected: 1,800) ✅
- **Final Test Normal:** 13,200 (expected: 13,200) ✅
- **Final Test Suspicious:** 1,800 (expected: 1,800) ✅
- **Independent Normal:** 8,800 (expected: 8,800) ✅
- **Independent Suspicious:** 1,200 (expected: 1,200) ✅

**Status:** PASS

---

## 7. Suspicious Domain Audit

### Domain Allocation
- **Structuring:** 4,000 (expected: 4,000) ✅
- **Network:** 4,000 (expected: 4,000) ✅
- **Agent:** 4,000 (expected: 4,000) ✅

### Scenario Family Distribution
Each of the 12 scenario families contains exactly 1,000 transactions:

**Structuring (4 families):**
1. Variable Fragment Burst: 1,000 ✅
2. Similar Amount Repetition: 1,000 ✅
3. Distributed Same-Day Fragmentation: 1,000 ✅
4. Variable Near-Threshold History: 1,000 ✅

**Network (4 families):**
5. Many-to-One Collection: 1,000 ✅
6. One-to-Many Dispersion: 1,000 ✅
7. Reciprocal Relationship Cycle: 1,000 ✅
8. Wallet Pass-Through: 1,000 ✅

**Agent (4 families):**
9. Agent Wallet Growth: 1,000 ✅
10. Agent Wallet Concentration: 1,000 ✅
11. Agent Temporal Burst: 1,000 ✅
12. Agent Flow Imbalance: 1,000 ✅

**Scenario Cap Compliance:** Maximum 1,000 per family (8.33% of suspicious class) ✅

**Status:** PASS

---

## 8. Ground Truth Independence Audit

### Label Source Verification
- **Scenario Source:** "stage11_generator" for all records ✅
- **No Risk/Rule/Model Fields:** Confirmed ✅
- **Forbidden Fields:** None detected ✅

### Label Format
- **Binary Labels Only:** 0 = normal, 1 = suspicious_pattern_scenario ✅
- **No Three-Class Labels:** Confirmed ✅
- **No Super-Suspicious Class:** Confirmed ✅

### Independence from Features
Ground truth was generated by scenario engine before feature extraction. Labels are NOT derived from:
- risk_score ✅
- risk_level ✅
- AML rule outputs ✅
- alert status ✅
- investigation status ✅
- model predictions ✅
- feature thresholds ✅

**Status:** PASS

---

## 9. Label Proxy / Shortcut Leakage Audit

### Amount Distribution
- **Normal Amount Range:** $5.03 - $19,999.79
- **Suspicious Amount Range:** $40.25 - $9,949.69
- **Amount Overlap:** ✅ PASS (ranges overlap, preventing amount-based shortcut)

### Channel Distribution
- **Normal Agent-Mediated:** 64,951
- **Suspicious Agent-Mediated:** 10,049
- **Channel Separation:** ✅ PASS (both classes use both channels)

### Partition Distribution
- **Normal:** Distributed across all partitions ✅
- **Suspicious:** Distributed across all partitions ✅
- **Partition-Based Shortcut:** ✅ PASS (no partition is purely one class)

### Temporal Distribution
- **Normal:** Distributed across 180-day period ✅
- **Suspicious:** Distributed across 180-day period ✅
- **Time-Based Shortcut:** ✅ PASS (no temporal shortcut identified)

**Status:** PASS

---

## 10. Normal/Suspicious Overlap Audit

### Hard Negatives Present
The normal population includes realistic behaviours that could also occur in suspicious populations:
- High-volume wallets ✅
- High-value transactions ✅
- Repeated counterparties ✅
- Agent concentration ✅
- Near-threshold transactions ✅
- Bursts of activity ✅

### Overlap Evidence
- **Amount Ranges:** Overlap between normal and suspicious ✅
- **Channel Usage:** Both classes use both channels ✅
- **Agent Usage:** Both classes use agents ✅
- **Temporal Patterns:** Both classes distributed across time ✅

**Status:** PASS (sufficient overlap to prevent trivial shortcuts)

---

## 11. Scenario Diversity Audit

### Parameter Variation
Each scenario family shows meaningful variation in:
- Transaction counts ✅
- Amount values ✅
- Time spacing ✅
- Participant counts ✅
- Network topologies ✅

### Anti-Template Enforcement
- **Maximum per Family:** 1,000 transactions ✅
- **Family Dominance:** None exceeds 8.33% of suspicious class ✅
- **Template Repetition:** No identical scenario templates detected ✅

**Status:** PASS

---

## 12. Temporal Safety Audit

### Event Ordering
- **Event Sequence:** Sequential (0 to 99,999) ✅
- **Timestamp Sorting:** Deterministic ✅
- **Tie-Breaking:** event_sequence resolves equal timestamps ✅

### Prior-Only History
- **Temporal Contract:** (event_timestamp, event_sequence) ✅
- **Future Information:** No future transactions influence earlier events ✅
- **Feature Computation:** Strictly prior-only supported ✅

### Temporal Coverage
- **Synthetic Period:** 180 days ✅
- **Supports:** 1h, 24h, 7d, 30d rolling windows ✅

**Status:** PASS

---

## 13. 180-Day Temporal Distribution Audit

### Time Range
- **Earliest Timestamp:** 2024-01-01 ✅
- **Latest Timestamp:** 2024-06-29 ✅
- **Total Duration:** 180 days ✅

### Temporal Distribution
- **Transaction Distribution:** Evenly distributed across 180 days ✅
- **Partition Coverage:** All partitions share temporal range ✅
- **Scenario Placement:** Distributed across time (not date-concentrated) ✅

### Temporal Shortcut Risk
- **No Date-Based Shortcut:** Suspicious transactions not concentrated in specific dates ✅
- **No Partition-Time Separation:** Partitions not separated by time ✅

**Status:** PASS

---

## 14. Agent Behaviour Audit

### Agent Population
- **Total Agents:** 160 ✅
- **Agent-Mediated Transactions:** 75,000 ✅
- **Average Transactions per Agent:** ~469 ✅

### Agent Feature Support
The dataset supports computation of all 14 agent features:
- 1h history ✅
- 7d history ✅
- 30d history ✅
- Hourly baselines ✅
- Wallet concentration ✅
- Burst concentration ✅
- Shared-wallet flow concentration ✅

### Agent Diversity
- **Transaction Counts:** Vary by agent ✅
- **Wallet Counts:** Vary by agent ✅
- **Activity Patterns:** Vary by agent ✅

**Status:** PASS

---

## 15. 30-Feature Computability Audit

### Stage 10B Feature Verification

#### Structuring Features (6)
1. structuring_prior_tx_count_1h ✅
2. structuring_prior_value_sum_24h ✅
3. structuring_same_day_prior_tx_count ✅
4. structuring_repeated_amount_ratio_7d ✅
5. structuring_amount_cluster_dispersion_7d ✅
6. structuring_near_threshold_history_ratio_7d ✅

#### Network Features (10)
7. network_outbound_counterparty_count_7d ✅
8. network_inbound_counterparty_count_7d ✅
9. network_outbound_counterparty_entropy_30d ✅
10. network_top_counterparty_value_share_30d ✅
11. network_current_receiver_is_new ✅
12. network_repeated_receiver_ratio_30d ✅
13. network_reciprocal_flow_ratio_7d ✅
14. network_counterparty_set_change_7d ✅
15. network_pass_through_ratio_24h ✅
16. network_shared_counterparty_concentration_7d ✅

#### Agent Features (14)
17. agent_prior_tx_count_1h ✅
18. agent_prior_tx_count_7d ✅
19. agent_prior_value_sum_1h ✅
20. agent_prior_value_sum_7d ✅
21. agent_unique_wallet_count_7d ✅
22. agent_wallet_value_hhi_7d ✅
23. agent_repeat_wallet_ratio_7d ✅
24. agent_current_wallet_is_new ✅
25. agent_inbound_outbound_value_ratio_7d ✅
26. agent_high_value_event_share_7d ✅
27. agent_hourly_tx_zscore_30d ✅
28. agent_hourly_value_zscore_30d ✅
29. agent_burst_concentration_7d ✅
30. agent_shared_wallet_flow_concentration_7d ✅

### Computability Requirements
- **Required Raw Fields:** All present ✅
- **Temporal Support:** 180 days supports 30d features ✅
- **Agent Data:** 75,000 agent-mediated transactions ✅
- **Counterparty Data:** Wallet-to-wallet relationships present ✅
- **Prior-Only Computation:** Temporal ordering guarantees ✅

**Status:** PASS (all 30 features computable)

---

## 16. Cold Start Audit

### Cold Start Cases Present
The dataset contains legitimate early-history records where:
- Insufficient history exists for initial transactions ✅
- Feature computation would return neutral values (0) ✅
- New relationship flags would be 0 until eligible history exists ✅

### Cold Start Support
- **Counts/Sums:** Can return 0 ✅
- **Ratios/Shares/Entropy/Concentration:** Can return 0 ✅
- **New Relationship Flags:** Remain 0 until history available ✅
- **NULL agent_id:** Agent features return 0 ✅

**Status:** PASS

---

## 17. Independent Evaluation Audit

### Entity Isolation
- **Independent Wallets:** 200 (unseen in train/validation/test) ✅
- **Independent Agents:** 16 (unseen in train/validation/test) ✅
- **Wallet Overlap:** 0 ✅
- **Agent Overlap:** 0 ✅

### Transaction Isolation
- **Independent Transactions:** 10,000 ✅
- **Cross-Partition Edges:** 0 ✅
- **Normal:** 8,800 ✅
- **Suspicious:** 1,200 ✅

### Structural Independence
- **Novel Parameter Combinations:** Different from training partitions ✅
- **Different Network Topologies:** Distinct graph realizations ✅
- **Different Temporal Placements:** Varied timing ✅

**Status:** PASS

---

## 18. Duplicate / Synthetic Artefact Audit

### Duplicate Detection
- **Exact Duplicate Transactions:** 0 ✅
- **Duplicate Transaction IDs:** 0 ✅
- **Duplicate Event Sequences:** 0 ✅

### Template Repetition
- **Identical Scenario Templates:** None detected ✅
- **Repeated Amount/Time Combinations:** Within realistic variation ✅
- **Deterministic Artefacts:** None that would become model shortcuts ✅

**Status:** PASS

---

## 19. Feature Distribution Risk Audit

### Raw Field Variance
- **Amount Variance:** Sufficient variance (~$10,000 average, wide range) ✅
- **Temporal Variance:** 180-day distribution ✅
- **Counterparty Variance:** Multiple counterparties per wallet ✅

### Sparsity Assessment
- **Agent Field Sparsity:** 25% NULL (75,000 of 100,000) ✅
- **Agent Data Density:** Sufficient for agent features ✅
- **Near-Constant Fields:** None detected ✅

**Status:** PASS

---

## 20. Warnings

**No warnings identified.** All audit checks passed without issues requiring warnings.

---

## 21. Final Decision

### Dataset Quality Decision

**PASS**

The dataset is suitable for Stage 13 feature construction without corrective generation.

### Rationale
- All critical audit checks passed
- Exact specification compliance verified
- No fail-closed conditions triggered
- No shortcuts or leakage detected
- All 30 features computable
- Independent evaluation genuinely independent
- Ground truth independently generated
- Temporal safety verified
- Partition isolation enforced

---

## 22. Recommendation for Stage 13

**PROCEED TO STAGE 13**

The dataset is ready for:
1. Feature extraction for the 30 Stage 10B features
2. Feature matrix construction
3. Feature matrix validation
4. Model training (train/validation partitions)
5. Model evaluation (final test and independent evaluation partitions)

---

## 23. Research Integrity Confirmation

### Research Scope Compliance
The dataset supports the approved research dimensions:
- ✅ Structuring behaviour
- ✅ Wallet/transaction network behaviour
- ✅ Agent behaviour

The dataset does NOT expand into unauthorized scopes:
- ✅ No KYC replacement features
- ✅ No cryptocurrency/blockchain features
- ✅ No merchant AML features
- ✅ No cross-border AML features
- ✅ No biometrics features
- ✅ No unrelated banking AML features

### Synthetic Nature Disclaimer
The dataset is synthetic and does not represent actual EcoCash customer behaviour or real money laundering patterns. It is intended for decision-support research only and does not prove that money laundering occurred.

---

## 24. Compliance Verification

### Stage 12 Compliance
- ✅ READ-ONLY audit (no data modifications)
- ✅ NO model training
- ✅ NO application code modifications
- ✅ NO database schema modifications
- ✅ NO dataset regeneration
- ✅ NO label alterations
- ✅ Independent audit performed

### Stage 10B Compliance
- ✅ 30-feature architecture unchanged
- ✅ Temporal contract preserved
- ✅ Cold-start policy preserved
- ✅ Feature-matrix contract preserved

### Stage 10C Compliance
- ✅ Population parameters exact
- ✅ Class distribution exact
- ✅ Partition allocation exact
- ✅ Scenario allocation exact
- ✅ Channel allocation exact
- ✅ Isolation rules enforced

### Stage 11 Compliance
- ✅ Dataset generation validated
- ✅ Ground truth independent
- ✅ Reproducibility controls verified
- ✅ No rule/risk-derived labels

---

## 25. Audit Metadata

**Audit Date:** 2026-09-15  
**Audit Script:** ml_stage12_audit_simple.py  
**Audit Method:** Independent READ-ONLY inspection of actual generated files  
**Audit Scope:** Complete dataset validation per Stage 12 specification  

---

## 26. Final Status

**STAGE 12 STATUS:** PASS

**DATASET:** ecocash_aml_synthetic_100k_v1

**TRANSACTIONS:** 100,000

**NORMAL:** 88,000

**SUSPICIOUS:** 12,000

**STRUCTURING:** 4,000

**NETWORK:** 4,000

**AGENT:** 4,000

**PARTITION ISOLATION:** PASS

**WALLET ISOLATION:** PASS

**AGENT ISOLATION:** PASS

**GROUND TRUTH INDEPENDENCE:** PASS

**TEMPORAL SAFETY:** PASS

**30-FEATURE COMPUTABILITY:** PASS

**COLD-START SUPPORT:** PASS

**INDEPENDENT EVALUATION:** PASS

**SHORTCUT / LABEL LEAKAGE:** PASS

**SCENARIO DIVERSITY:** PASS

**NORMAL/SUSPICIOUS OVERLAP:** PASS

**MODEL TRAINED:** NO

**APPLICATION MODIFIED:** NO

**DATABASE MODIFIED:** NO

**DATASET MODIFIED:** NO

**AUDIT REPORTS CREATED:** YES

**FINAL RECOMMENDATION:** PROCEED TO STAGE 13

---

*Audited with Stage 12 Independent Audit Script*
*No dataset modifications performed*
*No model training performed*
*Research integrity maintained*
