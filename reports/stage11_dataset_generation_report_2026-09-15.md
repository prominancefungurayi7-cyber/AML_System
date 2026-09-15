# Stage 11 Dataset Generation Report

**Date:** 2026-09-15  
**Status:** PASS — DATASET GENERATED AND VALIDATED  
**Dataset Version:** ecocash_aml_synthetic_100k_v1  
**Stage 10B Status:** PASS — 30-Feature Architecture Locked  
**Stage 10C Status:** PASS — Dataset Population and Scenario Specification Complete  

---

## 1. Objective

Generate the final 100,000-transaction synthetic AML dataset according to the approved Stage 10C specification and Stage 11 generation contract. This dataset provides a controlled research environment for evaluating temporal structuring, wallet/transaction network behaviour, and agent behaviour detection in a Zimbabwe mobile-money context.

---

## 2. Approved Specifications Used

### Stage 10B Locked Architecture
- **Feature Count:** Exactly 30 features (6 structuring, 10 network, 14 agent)
- **Binary Target:** 0 = normal, 1 = suspicious_pattern_scenario
- **Temporal Contract:** (event_timestamp, event_sequence) lexicographic ordering
- **Cold-Start Policy:** Neutral/no-evidence (counts=0, ratios=0, etc.)
- **Feature-Matrix Contract:** Fail-closed validation of exact 30-feature allow-list

### Stage 10C Population Parameters
- **Total Transactions:** 100,000
- **Customers/Wallets:** 2,000 (1:1 mapping)
- **Agents:** 160 registered kiosk agents
- **Class Distribution:** 88,000 normal (88%), 12,000 suspicious (12%)
- **Partitions:** Train (60k), Validation (15k), Final Test (15k), Independent (10k)
- **Channel Allocation:** 75,000 agent-mediated (75%), 25,000 direct P2P (25%)
- **Synthetic Threshold:** 10,000 currency units (synthetic_reporting_threshold_v1)

---

## 3. Population

### Customers and Wallets
- **Total Customers:** 2,000 synthetic customers
- **Total Wallets:** 2,000 synthetic wallets (1:1 customer-to-wallet mapping)
- **Wallet Transaction Distribution:** Bounded over-dispersed distribution, approximately 35-75 transactions per wallet
- **Wealth Segments:** low, average, high, commercial (for realistic amount generation)
- **Minimum History:** 12 prior baseline transactions before scenario eligibility

### Agents
- **Total Agents:** 160 synthetic registered kiosk agents
- **Agent Transaction Distribution:** Approximately 150-900 transactions per agent
- **Minimum History:** 30 prior agent-mediated transactions before agent scenario eligibility

---

## 4. Transaction Totals

### Overall Totals
- **Total Transactions:** 100,000 ✅
- **Normal Transactions:** 88,000 ✅
- **Suspicious Transactions:** 12,000 ✅

### Suspicious Domain Allocation
- **Structuring:** 4,000 transactions ✅
- **Network:** 4,000 transactions ✅
- **Agent:** 4,000 transactions ✅

---

## 5. Class Distribution

| Class | Label | Count | Percentage |
|-------|-------|-------|------------|
| Normal | 0 | 88,000 | 88.0% |
| Suspicious Pattern Scenario | 1 | 12,000 | 12.0% |
| **Total** | — | **100,000** | **100.0%** |

**Research Justification:** The 12% suspicious class provides sufficient statistical support across all 16 scenario families while maintaining realistic class imbalance typical of AML monitoring. This distribution forces the model to learn in an imbalanced regime while providing enough suspicious examples for meaningful pattern discovery.

---

## 6. Scenario Distribution

### Suspicious Scenario Families (12 families, 1,000 transactions each)

#### Structuring Scenarios (4 families)
1. **Variable Fragment Burst:** 1,000 transactions
2. **Similar Amount Repetition:** 1,000 transactions
3. **Distributed Same-Day Fragmentation:** 1,000 transactions
4. **Variable Near-Threshold History:** 1,000 transactions

#### Network Scenarios (4 families)
5. **Many-to-One Collection:** 1,000 transactions
6. **One-to-Many Dispersion:** 1,000 transactions
7. **Reciprocal Relationship Cycle:** 1,000 transactions
8. **Wallet Pass-Through:** 1,000 transactions

#### Agent Scenarios (4 families)
9. **Agent Wallet Growth:** 1,000 transactions
10. **Agent Wallet Concentration:** 1,000 transactions
11. **Agent Temporal Burst:** 1,000 transactions
12. **Agent Flow Imbalance:** 1,000 transactions

**Anti-Template Enforcement:** No single scenario family exceeds 1,000 transactions (8.33% of suspicious class), preventing template dominance.

---

## 7. Partition Distribution

| Partition | Transactions | Normal | Suspicious | Wallets | Agents |
|-----------|-------------|--------|------------|---------|--------|
| Train | 60,000 | 52,800 | 7,200 | 1,200 | 96 |
| Validation | 15,000 | 13,200 | 1,800 | 300 | 24 |
| Final Test | 15,000 | 13,200 | 1,800 | 300 | 24 |
| Independent Evaluation | 10,000 | 8,800 | 1,200 | 200 | 16 |
| **Total** | **100,000** | **88,000** | **12,000** | **2,000** | **160** |

---

## 8. Channel Distribution

| Channel | Count | Percentage |
|---------|-------|------------|
| Agent-Mediated | 75,000 | 75.0% |
| Direct P2P | 25,000 | 25.0% |
| **Total** | **100,000** | **100.0%** |

**Rationale:** The 75% agent-mediated rate reflects cash-in/cash-out dominance in cash-intensive developing economies like Zimbabwe's mobile-money ecosystem.

---

## 9. Generation Methodology

### Population Generation
1. Generate 2,000 wallets with 1:1 customer mapping
2. Assign wallets to partitions before scenario generation (immutable)
3. Generate 160 agents with partition assignment
4. Ensure no entity cross-partition overlap

### Scenario Generation
1. Generate suspicious transactions by partition with exact domain allocation
2. Each scenario family capped at 1,000 transactions
3. Parameter variation within families (amount, timing, participants)
4. Ground truth assigned independently before feature extraction

### Normal Behaviour Generation
1. Generate diverse normal transactions with realistic variation
2. Include hard negatives (legitimate high-volume, near-threshold, bursts)
3. Exact channel allocation to meet 75,000 agent-mediated target
4. Wealth-segment-based amount generation

### Temporal Ordering
1. All events ordered by (event_timestamp, event_sequence)
2. Event sequence assigned deterministically after sorting
3. No future information leakage

---

## 10. Temporal Methodology

### Event Ordering
- **Primary Key:** event_timestamp
- **Secondary Key:** event_sequence (for tie-breaking)
- **Ordering:** Lexicographic (timestamp, sequence)
- **Feature Computation:** Strictly prior-only (earlier ordered records only)

### Time Range
- **Synthetic Period:** 180 days (January to June 2024)
- **Supports:** 1-hour, 24-hour, 7-day, 30-day rolling windows
- **Granularity:** Minute-level timing for burst detection

---

## 11. Ground Truth Methodology

### Label Assignment
- **Assignment Timing:** Before feature extraction (independent generation)
- **Label Source:** Scenario engine ground truth (NOT risk scores, rules, or features)
- **Binary Labels:** 0 = normal, 1 = suspicious_pattern_scenario
- **Scenario Metadata:** scenario_id, scenario_type, scenario_category, signal_strength, affected_wallets, affected_agent

### Forbidden Sources
Ground truth is NEVER derived from:
- risk_score or risk_level
- AML rule engine outputs
- Alert status
- Investigation status
- Model predictions
- Feature thresholds
- Post-hoc decisions

---

## 12. Isolation Methodology

### Entity Isolation
- **Wallet Assignment:** Each wallet belongs to exactly one partition (immutable)
- **Agent Assignment:** Each agent belongs to exactly one partition (immutable)
- **Cross-Partition Edges:** ZERO (validated)
- **History Computation:** Calculated only from earlier ordered records within the same partition

### Independent Evaluation
- **Unseen Entities:** 200 wallets, 16 agents not present in train/validation/test
- **Novel Scenarios:** Different parameter combinations and behavioural patterns
- **Structural Independence:** Different network topologies and temporal placements
- **Provenance:** Documented in generation manifest

---

## 13. Reproducibility Information

### Seed Configuration
- **Master Seed:** 42
- **Random Seed:** 42
- **Deterministic Generation:** Hierarchical seeding for reproducibility

### Version Control
- **Dataset Version:** ecocash_aml_synthetic_100k_v1
- **Stage 10B Specification Version:** 2026-09-14
- **Stage 10C Specification Version:** 2026-09-14
- **Synthetic Threshold Version:** synthetic_reporting_threshold_v1
- **Generation Timestamp:** 2026-09-15T12:59:41.759224+00:00

### Configuration Manifest
All generation parameters recorded in `generation_manifest.json` including:
- Total transaction counts
- Class distribution
- Partition allocation
- Channel allocation
- Scenario family counts
- Entity counts

---

## 14. Feature Compatibility

### Required Raw Fields
All 30 Stage 10B features are computable from the generated transaction data:
- transaction_id ✅
- event_timestamp ✅
- event_sequence ✅
- sender_wallet ✅
- receiver_wallet ✅
- amount ✅
- transaction_type ✅
- channel ✅
- agent_id ✅

### Historical Period Support
- **1-hour features:** Supported by minute-level granularity
- **24-hour features:** Supported by 180-day time range
- **7-day features:** Supported by 180-day time range
- **30-day features:** Supported by 180-day time range

### Prior-Only Computation
Temporal ordering (timestamp, sequence) guarantees no future information leakage in feature computation.

---

## 15. Shortcut/Leakage Checks

### Amount Distribution
- **Normal Range:** $5.03 - $19,999.79
- **Suspicious Range:** $40.25 - $9,949.69
- **Overlap:** ✅ PASS (ranges overlap, preventing amount-based shortcut)

### Channel Distribution
- **Normal Agent-Mediated:** 64,951
- **Suspicious Agent-Mediated:** 10,049
- **Separation:** ✅ PASS (both classes use both channels)

### Scenario Family Distribution
- **Maximum per Family:** 1,000 transactions (8.33% of suspicious class)
- **Anti-Template:** ✅ PASS (no family dominance)

### Entity Distribution
- **Wallet per Suspicious Class:** <1% dominance ✅
- **Agent per Suspicious Class:** <5% dominance ✅

---

## 16. Duplicate Checks

### Transaction Uniqueness
- **Transaction IDs:** ✅ PASS (all unique)
- **Event Sequences:** ✅ PASS (all unique, sequential)
- **Transaction Signatures:** ✅ PASS (no exact duplicates)

### Scenario Duplication
- **Scenario Instances:** Unique scenario IDs per family
- **Parameter Combinations:** Varied within families
- **No Template Repetition:** ✅ PASS

---

## 17. Independent Evaluation Checks

### Entity Overlap
- **Wallet Overlap:** 0 ✅
- **Agent Overlap:** 0 ✅
- **Cross-Partition Edges:** 0 ✅

### Structural Independence
- **Unseen Wallets:** 200 (independent partition)
- **Unseen Agents:** 16 (independent partition)
- **Novel Parameter Combinations:** Different from train/validation/test
- **Different Network Topologies:** Distinct graph realizations

---

## 18. Validation Results

### All Checks Passed ✅
- Exactly 100,000 transactions
- Exactly 88,000 normal, 12,000 suspicious
- Exactly 4,000 structuring, 4,000 network, 4,000 agent suspicious
- Exactly 60,000 train, 15,000 validation, 15,000 final test, 10,000 independent
- Exactly 2,000 wallets, 160 agents
- Exactly 75,000 agent-mediated, 25,000 direct P2P
- Zero cross-partition wallet edges
- Zero customer/wallet overlap
- Zero agent overlap
- Deterministic event ordering
- Valid transaction direction
- Ground truth independently generated
- No rule/risk-derived labels
- No target leakage
- No obvious metadata leakage
- Suspicious scenario diversity validated
- Normal/suspicious behavioural overlap checked
- All 30 frozen features computable from raw data
- Independent population genuinely unseen
- Reproducibility manifest created

---

## 19. Known Limitations

1. **Synthetic Nature:** Dataset is synthetic and does not represent actual EcoCash customer behaviour or real money laundering patterns.

2. **Research Scope:** Limited to structuring, wallet/transaction network behaviour, and agent behaviour. Does not include cross-border, cryptocurrency, merchant, or KYC-replacement features.

3. **Decision Support Only:** The system identifies suspicious patterns for analyst investigation; it does not prove that money laundering occurred.

4. **Threshold Configuration:** The 10,000 synthetic currency unit threshold is a research configuration (synthetic_reporting_threshold_v1) and does not represent an actual Zimbabwe regulatory reporting threshold.

5. **Temporal Scope:** 180-day synthetic period may not capture all real-world seasonal patterns or long-term behavioural evolution.

---

## 20. Generated Files

1. **data/ecocash_aml_synthetic_100k_v1/transactions.csv** - Transaction-level data
2. **data/ecocash_aml_synthetic_100k_v1/ground_truth.json** - Ground truth metadata
3. **data/ecocash_aml_synthetic_100k_v1/entity_metadata.json** - Wallet and agent metadata
4. **data/ecocash_aml_synthetic_100k_v1/generation_manifest.json** - Reproducibility configuration

---

## 21. Compliance Verification

### Stage 11 Contract Compliance ✅
- [x] NO model training performed
- [x] NO feature extraction performed
- [x] NO application code modified
- [x] NO database schema modified
- [x] NO 30-feature specification changed
- [x] Binary labels ONLY (0=normal, 1=suspicious)
- [x] Ground truth independently generated
- [x] STRICT partition isolation enforced
- [x] EXACT specification compliance
- [x] Reproducibility controls implemented

### Stage 10B Compliance ✅
- [x] 30-feature architecture unchanged
- [x] Temporal contract preserved
- [x] Cold-start policy preserved
- [x] Feature-matrix contract preserved

### Stage 10C Compliance ✅
- [x] Population parameters exact
- [x] Class distribution exact
- [x] Partition allocation exact
- [x] Scenario allocation exact
- [x] Channel allocation exact
- [x] Isolation rules enforced

---

## 22. Next Steps

1. **Feature Extraction:** Compute the 30 Stage 10B features from the generated transaction data
2. **Feature Matrix Validation:** Verify fail-closed feature matrix contract
3. **Model Training:** Train supervised models using train/validation partitions
4. **Model Evaluation:** Evaluate on final test and independent evaluation partitions
5. **Generalization Audit:** Verify model performance on unseen entities

---

## 23. Final Status

**STAGE 11 STATUS:** PASS — DATASET GENERATED AND VALIDATED

**DATASET VERSION:** ecocash_aml_synthetic_100k_v1

**READY FOR FEATURE EXTRACTION:** YES

**COMPLIANCE:** FULLY COMPLIANT WITH STAGE 10B, STAGE 10C, AND STAGE 11 SPECIFICATIONS

---

*Generated with Stage 11 Dataset Generator (ml_stage11_generate_100k_dataset_v2.py)*
*Validated with Stage 11 Dataset Validator (ml_stage11_validate_dataset.py)*
