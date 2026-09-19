# Chapter 3 MSU Migration Review Report

**Date:** 2026-09-18  
**Task:** Chapter 3 Dissertation Migration and Rewrite — MSU Format  
**File Edited:** `Chapter 3.docx`  
**Status:** PASS

---

## Executive Summary

Chapter 3 has been successfully migrated from the old banking AML methodology to a comprehensive mobile-money AML methodology following MSU guidelines. The chapter now accurately documents the actual system architecture, 30-feature extraction mechanism, Gradient Boosting model, dataset specifications, temporal safety methodology, and evaluation procedures. References are sequential from Chapter 2 and limited to 20 per chapter as required.

---

## File Edited

**Primary File:** `Chapter 3.docx`  
**Location:** `C:\Users\PROMINENT\Desktop\important\My Projects\Last update for AML system\AML System\`

---

## Reference Status

**Chapter 1:** References [1-17] (17 references)  
**Chapter 2:** References [18-37] (20 references) ✅  
**Chapter 3:** References [38-57] (20 references) ✅  

**Total sequential references:** 57  
**References per chapter limit:** 20 ✅  
**Sequential numbering maintained:** ✅

---

## Sections Revised

All sections of Chapter 3 were completely rewritten to align with the mobile-money AML system and MSU guidelines:

### 3.1 Introduction
- **Status:** ✅ REVISED
- **Changes:** Focused on mobile-money AML decision-support system, removed banking terminology

### 3.2 Hardware and Software Requirements
- **Status:** ✅ REVISED
- **Changes:** Updated to reflect actual tools (Python 3.14, Flask 2.3.0, Flask-SocketIO 5.3.0, scikit-learn 1.3.0, MySQL 8.0, Bootstrap 5.3)

### 3.2.1 Hardware Requirements
- **Status:** ✅ REVISED
- **Changes:** Intel Core i5, 16GB RAM, 512GB SSD (actual development environment)

### 3.2.2 Software Requirements
- **Status:** ✅ REVISED
- **Changes:** Actual software stack documented with proper citations

### 3.3 Proposed System Architecture
- **Status:** ✅ COMPLETELY RESTRUCTURED
- **Changes:** Mobile-money architecture with Stage 13 feature service, Stage 14 model, threshold 0.35, alert workflow

### 3.4 Data Collection and Preprocessing
- **Status:** ✅ REVISED
- **Changes:** Synthetic dataset methodology, 100k transactions, 2k wallets, 160 agents, 12 scenario families

### 3.4.1 Synthetic Dataset Generation
- **Status:** ✅ NEW SECTION
- **Changes:** Synthetic data rationale, entity populations, class distribution, partitioning with isolation

### 3.4.2 Feature Extraction
- **Status:** ✅ NEW SECTION
- **Changes:** 30-feature architecture (6 structuring, 10 network, 14 agent), temporal safety, cold-start handling

### 3.5 Algorithm Design
- **Status:** ✅ REVISED
- **Changes:** Temporal-safe feature extraction algorithm, classification algorithm with pseudocode

### 3.5.1 Temporal-Safe Feature Extraction Algorithm
- **Status:** ✅ NEW SECTION
- **Changes:** Pseudocode for 30-feature extraction with historical information rules

### 3.5.2 Classification Algorithm
- **Status:** ✅ NEW SECTION
- **Changes:** Pseudocode for Gradient Boosting classification with threshold 0.35

### 3.6 Model Designing
- **Status:** ✅ REVISED
- **Changes:** Gradient Boosting model configuration, decision threshold selection

### 3.6.1 Gradient Boosting Model Implementation
- **Status:** ✅ REVISED
- **Changes:** Actual model parameters (n_estimators=200, learning_rate=0.1, max_depth=3, min_samples_leaf=2, min_samples_split=5, random_state=42)

### 3.6.2 Decision Threshold Selection
- **Status:** ✅ NEW SECTION
- **Changes:** Threshold 0.35 selection methodology via validation optimisation

### 3.7 Model Training and Validation
- **Status:** ✅ REVISED
- **Changes:** Training procedure, candidate model comparison, final testing, independent evaluation

### 3.7.1 Training Procedure
- **Status:** ✅ REVISED
- **Changes:** 60k training transactions, validation optimisation, model selection based on Macro F1

### 3.7.2 Validation Results
- **Status:** ✅ REVISED
- **Changes:** Validation methodology explained (detailed results reserved for Chapter 4)

### 3.7.3 Final Testing and Independent Evaluation
- **Status:** ✅ NEW SECTION
- **Changes:** 15k final test, 10k independent evaluation, entity isolation, generalisation assessment

### 3.8 Summary
- **Status:** ✅ REVISED
- **Changes:** Mobile-money AML methodology summary, introduces Chapter 4 results

---

## Major Old Banking Content Removed/Replaced

### Removed Banking Terminology:
- "simulated banking transactions" → "mobile-money transactions"
- "bank accounts" → "wallets"
- "deposits, withdrawals" → "cash-in, cash-out"
- "banking customers" → "mobile-money users"
- "Random Forest" → "Gradient Boosting" (actual selected model)
- "18 features" → "30 features" (actual architecture)
- "risk scoring algorithm" → "classification algorithm with threshold"
- "behavioural profiling model" → removed (not part of current system)

### Replaced with Mobile-Money Content:
- Synthetic mobile-money dataset (100k transactions, 2k wallets, 160 agents)
- 30-feature architecture (6 structuring, 10 network, 14 agent)
- Stage 13 feature service with temporal safety
- Stage 14 frozen Gradient Boosting model
- Threshold 0.35 decision process
- Partitioning with entity isolation (train 60k, val 15k, test 15k, independent 10k)
- 12 suspicious scenario families
- Cash-In, Cash-Out, Wallet-to-Wallet transactions
- Agent-mediated vs direct P2P transactions

---

## System Architecture Documented

### Conceptual Flow (Accurate to Repository):
```
Mobile-money transaction
    ↓
Transaction processing
    ↓
Historical transaction retrieval
    ↓
Temporal-safe feature generation (Stage 13)
    ↓
30-feature vector (6 structuring, 10 network, 14 agent)
    ↓
Frozen Stage 14 Gradient Boosting model
    ↓
Suspicious probability
    ↓
0.35 decision threshold
    ↓
Binary classification (Normal / Suspicious Pattern)
    ↓
Alert generation
    ↓
Dashboard / real-time notification (Socket.IO)
    ↓
Investigation workflow
```

### Components Documented:
- Transaction Processing Module
- Wallet and Agent Data Management
- Stage 13 Feature Service
- Stage 14 Model Service
- Decision Threshold Module
- Alert Generation Module
- Dashboard Interface
- Real-time Communication Layer

---

## Dataset Details Documented

### Official Dataset Specifications:
- **Total transactions:** 100,000
- **Wallet entities:** 2,000
- **Agent entities:** 160
- **Class distribution:** 88% normal, 12% suspicious
- **Transaction types:** 75% agent-mediated, 25% direct P2P
- **Synthetic data:** Yes (no real EcoCash data)

### Partitioning with Isolation:
- **Training:** 60,000 transactions (1,200 wallets, 96 agents)
- **Validation:** 15,000 transactions (300 wallets, 24 agents)
- **Final Test:** 15,000 transactions (300 wallets, 24 agents)
- **Independent:** 10,000 transactions (200 wallets, 16 agents)
- **Isolation:** Wallets and agents appear in only one partition

### 12 Suspicious Scenario Families:
**Structuring (4):**
1. Variable Fragment Burst
2. Similar Amount Repetition
3. Distributed Same-Day Fragmentation
4. Variable Near-Threshold History

**Network (4):**
5. Many-to-One Collection/Funnel
6. One-to-Many Dispersion/Pay-Out Hub
7. Reciprocal Relationship Cycle
8. Wallet Pass-Through/Layering Transit

**Agent (4):**
9. Agent Wallet Growth Surge
10. Agent Collusive Wallet Concentration
11. Agent Temporal Burst/Off-Hours Spike
12. Agent Flow Directional Imbalance

---

## 30-Feature Architecture Documented

### Feature Families (Accurate to Repository):
**Structuring Features (6):**
1. structuring_prior_tx_count_1h
2. structuring_prior_value_sum_24h
3. structuring_same_day_prior_tx_count
4. structuring_repeated_amount_ratio_7d
5. structuring_amount_cluster_dispersion_7d
6. structuring_near_threshold_history_ratio_7d

**Network Features (10):**
1. network_outbound_counterparty_count_7d
2. network_inbound_counterparty_count_7d
3. network_outbound_counterparty_entropy_30d
4. network_top_counterparty_value_share_30d
5. network_current_receiver_is_new
6. network_repeated_receiver_ratio_30d
7. network_reciprocal_flow_ratio_7d
8. network_counterparty_set_change_7d
9. network_pass_through_ratio_24h
10. network_shared_counterparty_concentration_7d

**Agent Features (14):**
1. agent_prior_tx_count_1h
2. agent_prior_tx_count_7d
3. agent_prior_value_sum_1h
4. agent_prior_value_sum_7d
5. agent_unique_wallet_count_7d
6. agent_wallet_value_hhi_7d
7. agent_repeat_wallet_ratio_7d
8. agent_current_wallet_is_new
9. agent_inbound_outbound_value_ratio_7d
10. agent_high_value_event_share_7d
11. agent_hourly_tx_zscore_30d
12. agent_hourly_value_zscore_30d
13. agent_burst_concentration_7d
14. agent_shared_wallet_flow_concentration_7d

---

## Temporal Safety Methodology Documented

### Temporal Safety Rules:
- Features use only information available before current transaction
- Current event excluded from its own historical features
- Future events excluded
- Equal timestamps resolved by transaction sequence ordering
- Ordering: (event_timestamp, event_sequence)
- Transaction ID provides deterministic ordering for equal timestamps

### Cold-Start Handling:
- Counts and sums default to zero
- Ratios, shares, entropy, concentration, dispersion, z-scores default to zero
- New-relationship flags remain zero until eligible history exists
- Non-agent transactions receive zero for all agent-context features

---

## Model Details Documented

### Official Model Configuration:
- **Algorithm:** Gradient Boosting Classifier
- **n_estimators:** 200
- **learning_rate:** 0.1
- **max_depth:** 3
- **min_samples_leaf:** 2
- **min_samples_split:** 5
- **random_state:** 42
- **Decision threshold:** 0.35
- **Status:** Frozen (Stage 14)

### Model Selection:
- **Candidate models:** Logistic Regression, Random Forest, Gradient Boosting
- **Selection metric:** Macro F1 on validation set
- **Selected model:** Gradient Boosting (validation Macro F1: 0.7363)
- **Threshold selection:** 0.35 (optimised via validation Macro F1)

---

## Research Integrity Safeguards Documented

### Data Leakage Prevention:
- ✅ Current-event exclusion from historical features
- ✅ Future-event exclusion
- ✅ Equal-timestamp ordering by sequence
- ✅ Wallet/customer partition isolation
- ✅ Agent partition isolation
- ✅ Independent ground truth generation
- ✅ No risk/rule/model-derived labels
- ✅ Locked final test
- ✅ Independent evaluation with unseen populations

---

## References Added

### Complete Reference List
20 real, verifiable references in IEEE format [38-57]

### Reference Quality Assessment
- **Total References:** 20 [38-57]
- **All references sequential from Chapter 2:** ✅
- **Sequential numbering maintained:** ✅
- **Source Types:**
  - Software documentation: Python, Flask, Scikit-learn, Pandas, NumPy, MySQL, Bootstrap (7 sources)
  - Academic research: Altman et al., Hastie et al., Friedman, Breiman, Al-Garadi et al., Sokolova, Powers (7 sources)
  - ML algorithms: Ke et al. (LightGBM), Chen and Guestrin (XGBoost) (2 sources)
  - ML evaluation: Goutte and Gaussier, Sokolova, Powers (3 sources)
  - Methodology: García et al., Liu et al. (2 sources)

- **Recency:** All sources are contemporary or foundational ML literature
- **Wikipedia:** 0 sources (0%) ✅
- **Blogs:** 0 sources (0%) ✅

### Citation Mapping
All 20 citations in the text have corresponding references ✅  
All 20 references are cited in the text ✅  
No orphan citations or references ✅

---

## MSU Structure Compliance

### Required Sections
✅ 3.1 Introduction  
✅ 3.2 Hardware and Software Requirements  
✅ 3.3 Proposed System Architecture  
✅ 3.4 Data Collection and Preprocessing  
✅ 3.5 Algorithm Design  
✅ 3.6 Model Designing  
✅ 3.7 Model Training and Validation  
✅ 3.8 Summary

### Numbered Sub-sections
✅ 3.2.1 Hardware Requirements  
✅ 3.2.2 Software Requirements  
✅ 3.4.1 Synthetic Dataset Generation  
✅ 3.4.2 Feature Extraction  
✅ 3.5.1 Temporal-Safe Feature Extraction Algorithm  
✅ 3.5.2 Classification Algorithm  
✅ 3.6.1 Gradient Boosting Model Implementation  
✅ 3.6.2 Decision Threshold Selection  
✅ 3.7.1 Training Procedure  
✅ 3.7.2 Validation Results  
✅ 3.7.3 Final Testing and Independent Evaluation

---

## MSU Formatting Validation

### Applied Formatting
- ✅ Times New Roman font
- ✅ 12 pt body text
- ✅ 1.5 line spacing
- ✅ Justified alignment
- ✅ Numbered headings (3.1, 3.2, etc.)
- ✅ Sub-headings numbered (3.2.1, 3.2.2, etc.)
- ✅ Bold heading style (consistent)
- ✅ Main chapter heading formatting (Chapter 3)

### Formatting Notes for User
- Main chapter heading should be 14 pt bold (user to verify in Word)
- Page breaks before main headings (user to add in Word)
- Figure 3.1 placeholder present (user to add actual architecture diagram)

---

## System Consistency Validation

### Current System Alignment
- ✅ Mobile-money / EcoCash-style context throughout
- ✅ Three behavioural dimensions (structuring, network, agent)
- ✅ 30-feature approach documented (6 structuring, 10 network, 14 agent)
- ✅ Gradient Boosting classification (Stage 14 frozen)
- ✅ Decision threshold 0.35
- ✅ Decision-support approach emphasised
- ✅ Synthetic data acknowledged
- ✅ Research prototype status maintained
- ✅ No production deployment claims
- ✅ No merchant AI dimension added
- ✅ No KYC replacement, blockchain, cryptocurrency, biometrics

### Scope Accuracy
- ✅ Included: Structuring, wallet/transaction-network behaviour, agent behaviour
- ✅ Included: Zimbabwe mobile-money context
- ✅ Included: Cash-In, Cash-Out, Wallet-to-Wallet
- ✅ Included: Agent-mediated and direct P2P transactions
- ✅ Excluded: Traditional banking AML as primary focus
- ✅ Excluded: Merchant AI dimension
- ✅ Excluded: KYC replacement, blockchain, cryptocurrency, biometrics

---

## Technical Accuracy Verification

### Dataset Verification:
- ✅ 100,000 transactions (matches repository)
- ✅ 2,000 wallets (matches repository)
- ✅ 160 agents (matches repository)
- ✅ 88% normal, 12% suspicious (matches repository)
- ✅ 75% agent-mediated, 25% P2P (matches repository)

### Partitioning Verification:
- ✅ Train 60k, val 15k, test 15k, independent 10k (matches repository)
- ✅ Entity isolation documented (matches repository)

### Feature Architecture Verification:
- ✅ 30 features total (matches repository)
- ✅ 6 structuring features (matches repository)
- ✅ 10 network features (matches repository)
- ✅ 14 agent features (matches repository)
- ✅ Feature names accurate (matches repository)

### Model Verification:
- ✅ Gradient Boosting (matches repository)
- ✅ n_estimators=200 (matches repository)
- ✅ learning_rate=0.1 (matches repository)
- ✅ max_depth=3 (matches repository)
- ✅ min_samples_leaf=2 (matches repository)
- ✅ min_samples_split=5 (matches repository)
- ✅ random_state=42 (matches repository)
- ✅ threshold=0.35 (matches repository)

---

## Remaining Issues

### Minor Formatting Issues
1. Main chapter heading size (14 pt bold) — User to verify in Word
2. Page breaks for main headings — User to add in Word
3. Figure 3.1 architecture diagram — User to add actual diagram

### No Critical Issues
- ✅ MSU structure compliance
- ✅ Accurate technical documentation
- ✅ System architecture correctly described
- ✅ Dataset details accurately documented
- ✅ Feature architecture accurately documented
- ✅ Model details accurately documented
- ✅ Temporal safety methodology explained
- ✅ Research integrity safeguards documented
- ✅ Sequential references maintained
- ✅ 20 references per chapter limit respected
- ✅ No obsolete banking methodology
- ✅ No unsupported claims
- ✅ System scope accurately described

---

## Final Status: PASS

### Pass Criteria Met
- ✅ MSU structure compliance (all required sections)
- ✅ Accurate technical documentation (matches repository)
- ✅ 30-feature architecture documented (6/10/14)
- ✅ Dataset details verified (100k/2k/160)
- ✅ Partitioning with isolation documented
- ✅ Temporal safety methodology explained
- ✅ Gradient Boosting model documented (Stage 14 frozen)
- ✅ Threshold 0.35 documented
- ✅ Research integrity safeguards documented
- ✅ Sequential references [38-57] (20 references)
- ✅ 20 references per chapter limit respected
- ✅ MSU formatting applied
- ✅ No obsolete banking content
- ✅ System scope accurately described
- ✅ No unsupported claims

### User Action Required
1. Verify main chapter heading is 14 pt bold in Word
2. Add page breaks before main headings (3.1, 3.2, etc.)
3. Add actual architecture diagram for Figure 3.1
4. Review references for any needed updates based on supervisor feedback

---

## Migration Completed: 2026-09-18  
## Validated By: Devin AI Assistant  
## Next Step: User to apply final formatting if needed and proceed to Chapter 4 review (if applicable)