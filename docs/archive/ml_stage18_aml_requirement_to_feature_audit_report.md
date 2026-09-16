# AML Requirement-to-Feature Alignment Audit Report

**Date:** 2026-09-03  
**Stage:** 18 - AML Requirement-to-Feature Alignment Audit  
**Status:** COMPLETE

---

## 1. CURRENT 18-FEATURE INVENTORY

**Source:** `ml_stage16b_feature_metadata.json` (Stage 16B frozen champion)

| # | Feature Name | Description | Type |
|---|--------------|-------------|------|
| 1 | amount | Transaction amount | Current |
| 2 | sender_avg_amount | Average transaction amount for sender (historical) | Historical |
| 3 | sender_max_amount | Maximum transaction amount for sender (historical) | Historical |
| 4 | amount_to_sender_avg | Current amount divided by sender average amount | Historical |
| 5 | amount_z_score | Z-score of current amount relative to historical | Historical |
| 6 | amount_deviation_from_baseline_30d | Z-score of current amount relative to 30-day historical mean | Historical |
| 7 | tx_frequency_7d | Transaction frequency in last 7 days | Historical |
| 8 | tx_frequency_30d | Transaction frequency in last 30 days | Historical |
| 9 | frequency_change_vs_avg_7d | Change in frequency vs 7-day average | Historical |
| 10 | sender_tx_count_24h | Transaction count in last 24 hours | Historical |
| 11 | sender_volume_24h | Total transaction volume in last 24 hours | Historical |
| 12 | same_day_count | Number of transactions on same day | Historical |
| 13 | rapid_transfer_count | Count of rapid transfers (inbound to outbound within 1 hour) | Historical |
| 14 | is_new_recipient | Binary flag if recipient is new to sender | Historical |
| 15 | unique_recipients_7d | Number of unique recipients in last 7 days | Historical |
| 16 | hour | Hour of day (0-23) | Current |
| 17 | is_off_hours | Binary flag if transaction is outside business hours | Current |
| 18 | counterparty_change_score_7d | Jaccard similarity between current 7d and previous 7d receiver sets | Historical |

**Total Features:** 18  
**Current Features:** 3 (amount, hour, is_off_hours)  
**Historical Features:** 15

---

## 2. CHAPTER 1 AML CAPABILITY INVENTORY

**Source:** Chapter 1, Section 1.9 and system documentation

### Stated AML Detection Capabilities

1. **Cross-border laundering**
   - Unusual sequences of transfers
   - Rapid movement of funds
   - Movement through multiple accounts

2. **Trade mis-invoicing**
   - Detect unusual financial behaviour associated with possible mis-invoicing
   - Abnormal deposits, transfers, and rapid movement of funds
   - (Note: System cannot verify invoice itself)

3. **Cash-based laundering**
   - Analyse deposits against customer's normal behaviour
   - Analyse subsequent transfers/withdrawals

4. **Complex laundering patterns**
   - Analyse transaction patterns over time rather than only individual transactions

5. **Delayed/reactive detection**
   - Real-time monitoring analyses transactions as they occur

6. **Behavioural analysis**
   - Compare current behaviour with customer's historical/normal behaviour
   - Detect sudden behavioural changes
   - Avoid treating every large transaction as automatically suspicious

### Common AML Behavioural Patterns (Relevant to System)

7. **Transaction sequences**
   - Ordered patterns of transactions over time

8. **Multi-account movement**
   - Funds moving through multiple accounts

9. **Deposit → transfer → withdrawal patterns**
   - Structured flow of funds through different transaction types

10. **Sudden behavioural changes**
    - Abrupt deviations from established patterns

11. **Cross-border activity**
    - International fund movements

12. **Layering-like rapid movement**
    - Fast sequential transfers to obscure origin

13. **Structuring/smurfing-like behaviour**
    - Breaking large transactions into smaller amounts

14. **Customer-specific behavioural deviation**
    - Individual customer pattern analysis

---

## 3. REQUIREMENT-TO-FEATURE MAPPING TABLE

| Capability | Classification | Supporting Features | Gap Analysis |
|------------|----------------|---------------------|--------------|
| **Cross-border laundering** | PARTIALLY REPRESENTED | rapid_transfer_count, sender_volume_24h, tx_frequency_7d | Missing: destination_country, international flags, multi-account chain tracking |
| **Trade mis-invoicing** | PARTIALLY REPRESENTED | amount_z_score, amount_deviation_from_baseline_30d, sender_avg_amount | Missing: invoice data, business context, trade-specific patterns |
| **Cash-based laundering** | WELL REPRESENTED | amount, sender_avg_amount, amount_to_sender_avg, amount_z_score, tx_frequency_7d | Good coverage for amount and frequency analysis |
| **Complex laundering patterns** | PARTIALLY REPRESENTED | tx_frequency_7d, tx_frequency_30d, frequency_change_vs_avg_7d, unique_recipients_7d, counterparty_change_score_7d | Missing: longer-term patterns, sequence analysis, multi-hop tracking |
| **Delayed/reactive detection** | NOT AN ML-FEATURE / SYSTEM-LEVEL CAPABILITY | N/A | This is an architectural capability (real-time monitoring), not an ML feature |
| **Behavioural analysis** | WELL REPRESENTED | sender_avg_amount, sender_max_amount, amount_to_sender_avg, amount_z_score, amount_deviation_from_baseline_30d, tx_frequency_7d, tx_frequency_30d, frequency_change_vs_avg_7d | Strong coverage of behavioural deviation detection |
| **Transaction sequences** | NOT REPRESENTED | N/A | No sequence/ordering features, no temporal pattern encoding |
| **Multi-account movement** | PARTIALLY REPRESENTED | unique_recipients_7d, counterparty_change_score_7d, is_new_recipient | Missing: account chain tracking, intermediate account identification |
| **Deposit → transfer → withdrawal patterns** | PARTIALLY REPRESENTED | rapid_transfer_count, sender_tx_count_24h, sender_volume_24h | Missing: transaction type sequence analysis, flow tracking |
| **Sudden behavioural changes** | WELL REPRESENTED | frequency_change_vs_avg_7d, amount_z_score, amount_deviation_from_baseline_30d, counterparty_change_score_7d | Good coverage of change detection |
| **Cross-border activity** | NOT REPRESENTED | N/A | Missing: destination_country, international flags, cross-border volume |
| **Layering-like rapid movement** | WELL REPRESENTED | rapid_transfer_count, sender_tx_count_24h, sender_volume_24h | Strong coverage of rapid movement detection |
| **Structuring/smurfing-like behaviour** | PARTIALLY REPRESENTED | same_day_count, amount, sender_avg_amount, amount_to_sender_avg | Missing: threshold-based structuring detection, cumulative amount tracking |
| **Customer-specific behavioural deviation** | WELL REPRESENTED | sender_avg_amount, sender_max_amount, amount_to_sender_avg, amount_z_score, amount_deviation_from_baseline_30d, tx_frequency_7d, tx_frequency_30d | Excellent coverage of individual customer patterns |

---

## 4. WELL REPRESENTED CAPABILITIES

### 4.1 Behavioural Analysis
**Supporting Features:**
- sender_avg_amount, sender_max_amount
- amount_to_sender_avg, amount_z_score
- amount_deviation_from_baseline_30d
- tx_frequency_7d, tx_frequency_30d
- frequency_change_vs_avg_7d

**Assessment:** The feature set provides strong coverage for comparing current behaviour against historical baselines. Multiple time windows (7d, 30d) and statistical measures (z-scores, ratios) enable robust deviation detection.

### 4.2 Cash-Based Laundering
**Supporting Features:**
- amount, sender_avg_amount
- amount_to_sender_avg, amount_z_score
- tx_frequency_7d

**Assessment:** Amount deviation and frequency analysis provide good coverage for detecting abnormal deposits and subsequent activity patterns.

### 4.3 Sudden Behavioural Changes
**Supporting Features:**
- frequency_change_vs_avg_7d
- amount_z_score
- amount_deviation_from_baseline_30d
- counterparty_change_score_7d

**Assessment:** Change detection features (frequency change, z-scores, counterparty similarity) enable detection of abrupt behavioural shifts.

### 4.4 Layering-Like Rapid Movement
**Supporting Features:**
- rapid_transfer_count
- sender_tx_count_24h
- sender_volume_24h

**Assessment:** Strong coverage of rapid movement detection through 24h velocity metrics and rapid transfer counting.

### 4.5 Customer-Specific Behavioural Deviation
**Supporting Features:**
- sender_avg_amount, sender_max_amount
- amount_to_sender_avg, amount_z_score
- amount_deviation_from_baseline_30d
- tx_frequency_7d, tx_frequency_30d

**Assessment:** Excellent coverage of individual customer pattern analysis through historical baselines and statistical deviation measures.

---

## 5. PARTIALLY REPRESENTED CAPABILITIES

### 5.1 Cross-Border Laundering
**Supporting Features:**
- rapid_transfer_count
- sender_volume_24h
- tx_frequency_7d

**Gap:** Missing destination_country, international transaction flags, and multi-account chain tracking. The database schema includes `destination_country` but it is not used in the ML feature set.

**Data Availability:** Raw data exists (destination_country in transactions table) but is not extracted as a feature.

### 5.2 Trade Mis-Invoicing
**Supporting Features:**
- amount_z_score
- amount_deviation_from_baseline_30d
- sender_avg_amount

**Gap:** Missing invoice data, business context, and trade-specific patterns. This is a fundamental limitation - the system cannot verify invoices.

**Data Availability:** Invoice data does not exist in the system. This capability cannot be fully represented without additional data sources.

### 5.3 Complex Laundering Patterns
**Supporting Features:**
- tx_frequency_7d, tx_frequency_30d
- frequency_change_vs_avg_7d
- unique_recipients_7d
- counterparty_change_score_7d

**Gap:** Missing longer-term patterns (>30 days), sequence analysis, and multi-hop tracking. Current features focus on short-term windows (7d, 30d).

**Data Availability:** Raw transaction history exists but longer-term pattern features are not implemented.

### 5.4 Multi-Account Movement
**Supporting Features:**
- unique_recipients_7d
- counterparty_change_score_7d
- is_new_recipient

**Gap:** Missing account chain tracking, intermediate account identification, and explicit multi-account flow analysis.

**Data Availability:** Raw data includes sender_account and receiver_account, enabling chain reconstruction, but chain-based features are not implemented.

### 5.5 Deposit → Transfer → Withdrawal Patterns
**Supporting Features:**
- rapid_transfer_count
- sender_tx_count_24h
- sender_volume_24h

**Gap:** Missing transaction type sequence analysis and explicit flow tracking through different transaction types.

**Data Availability:** Raw data includes transaction_type (deposit, transfer, withdrawal), enabling sequence analysis, but type-sequence features are not implemented.

### 5.6 Structuring/Smurfing-Like Behaviour
**Supporting Features:**
- same_day_count
- amount
- sender_avg_amount
- amount_to_sender_avg

**Gap:** Missing threshold-based structuring detection (e.g., amounts just below reporting thresholds) and cumulative amount tracking.

**Data Availability:** Raw data exists for cumulative analysis but threshold-based structuring features are not implemented.

---

## 6. MISSING CAPABILITIES

### 6.1 Transaction Sequences
**Classification:** NOT REPRESENTED

**Gap:** No sequence/ordering features, no temporal pattern encoding. The current feature set treats each transaction independently without capturing ordered patterns over time.

**Data Availability:** Raw transaction data includes timestamps, enabling sequence reconstruction. Sequence-based features could be implemented.

**Example Missing Features:**
- Transaction type sequence (e.g., deposit → transfer → withdrawal)
- Time gap between consecutive transactions
- Recurring pattern detection (e.g., weekly transfers)
- Sequence length and complexity metrics

### 6.2 Cross-Border Activity
**Classification:** NOT REPRESENTED

**Gap:** Missing destination_country, international transaction flags, and cross-border volume analysis.

**Data Availability:** Raw data includes destination_country in the transactions table. This is a clear feature extraction gap.

**Example Missing Features:**
- is_cross_border (binary flag)
- cross_border_volume_7d
- cross_border_frequency_7d
- high_risk_country_flag

### 6.3 Delayed/Reactive Detection
**Classification:** NOT AN ML-FEATURE / SYSTEM-LEVEL CAPABILITY

**Gap:** This is an architectural capability (real-time monitoring), not an ML feature. The system architecture supports real-time monitoring through Flask and Socket.IO.

**Assessment:** This is correctly not represented as an ML feature. It is a system-level capability.

---

## 7. FEATURES THAT MAY BE WEAK/REDUNDANT

### 7.1 Potential Redundancies

**amount_z_score vs amount_deviation_from_baseline_30d:**
- Both measure amount deviation from historical mean
- amount_z_score uses full historical baseline
- amount_deviation_from_baseline_30d uses 30-day window
- **Assessment:** These capture different time windows and are likely complementary, not redundant.

**tx_frequency_7d vs tx_frequency_30d:**
- Both measure transaction frequency
- Different time windows
- **Assessment:** Complementary for short-term vs medium-term pattern detection.

**sender_tx_count_24h vs tx_frequency_7d:**
- Both measure transaction count
- Different time windows (24h vs 7d)
- **Assessment:** Complementary for immediate vs short-term velocity.

### 7.2 Potentially Weak Features

**hour:**
- Hour of day (0-23)
- **Weakness:** May have limited predictive power if suspicious activity occurs at all hours
- **Assessment:** Could be useful for off-hours detection but may need combination with other features.

**is_off_hours:**
- Binary flag for outside business hours
- **Weakness:** Depends on business hours definition; may not capture all suspicious timing patterns
- **Assessment:** Useful but may need refinement (e.g., weekend detection, country-specific hours).

**counterparty_change_score_7d:**
- Jaccard similarity between current 7d and previous 7d receiver sets
- **Weakness:** May not capture gradual counterparty changes or new counterparty patterns
- **Assessment:** Useful for abrupt changes but may miss gradual shifts.

---

## 8. WHICH MISSING CAPABILITIES CAN BE REPRESENTED USING EXISTING TRANSACTION DATA

### 8.1 Cross-Border Activity
**Data Available:** destination_country in transactions table

**Can Be Represented:** YES

**Proposed Features:**
- is_cross_border (binary: destination_country != domestic_country)
- cross_border_volume_7d
- cross_border_frequency_7d
- cross_border_ratio_7d (cross_border_volume / total_volume)
- high_risk_country_flag (based on destination_country)

**Implementation Complexity:** LOW - Simple feature extraction from existing data.

### 8.2 Transaction Sequences
**Data Available:** timestamp, transaction_type, sender_account, receiver_account

**Can Be Represented:** YES

**Proposed Features:**
- transaction_type_sequence_last_3 (encoded sequence of last 3 transaction types)
- time_since_last_transaction
- time_since_last_deposit
- time_since_last_withdrawal
- recurring_pattern_score (e.g., weekly, monthly patterns)
- sequence_length_last_24h

**Implementation Complexity:** MEDIUM - Requires sequence analysis and temporal pattern encoding.

### 8.3 Multi-Account Chain Tracking
**Data Available:** sender_account, receiver_account, timestamp, amount

**Can Be Represented:** YES

**Proposed Features:**
- chain_depth (number of hops in transaction chain)
- intermediate_account_count (number of unique intermediate accounts)
- chain_volume_ratio (volume through chains vs direct transfers)
- circular_chain_flag (detect circular transfers)

**Implementation Complexity:** HIGH - Requires graph-based analysis and chain reconstruction.

### 8.4 Deposit → Transfer → Withdrawal Flow Analysis
**Data Available:** transaction_type, timestamp, sender_account, receiver_account, amount

**Can Be Represented:** YES

**Proposed Features:**
- deposit_to_transfer_time_gap
- transfer_to_withdrawal_time_gap
- flow_completion_rate (percentage of deposits that complete full flow)
- flow_amount_preservation (amount preservation through flow)

**Implementation Complexity:** MEDIUM - Requires flow tracking and time gap analysis.

### 8.5 Structuring/Smurfing Detection
**Data Available:** amount, timestamp, sender_account

**Can Be Represented:** YES

**Proposed Features:**
- amount_near_threshold_flag (e.g., amount within 10% of CTR threshold)
- same_day_cumulative_amount
- same_day_amount_distribution (variance of amounts on same day)
- structuring_pattern_score (frequency of near-threshold amounts)

**Implementation Complexity:** LOW - Simple aggregation and threshold analysis.

---

## 9. WHICH CAPABILITIES CANNOT CURRENTLY BE REPRESENTED (REQUIRED RAW DATA DOES NOT EXIST)

### 9.1 Trade Mis-Invoicing
**Missing Data:** Invoice data, business context, trade documentation

**Cannot Be Represented:** NO

**Reason:** The system does not have access to invoice data, trade documentation, or business context. This capability requires external data sources beyond the current transaction database.

**Recommendation:** This capability should be documented as out-of-scope for the current ML model. It may require integration with external trade data sources or manual review processes.

### 9.2 Enhanced KYC/PEP Analysis
**Missing Data:** PEP lists, beneficial ownership information, corporate structure data

**Cannot Be Represented:** NO

**Reason:** While the database has a pep_flag field, comprehensive PEP analysis requires external PEP databases and beneficial ownership information.

**Recommendation:** This capability should be handled through external KYC services rather than ML feature engineering.

---

## 10. SMALL SHORTLIST OF HIGHEST-VALUE FEATURE IMPROVEMENTS

Based on the audit, the following feature improvements offer the highest value with reasonable implementation complexity:

### 10.1 Cross-Border Activity Features (HIGH VALUE, LOW COMPLEXITY)
**Priority:** 1

**Rationale:**
- Cross-border laundering is a stated capability but completely missing from ML features
- Raw data (destination_country) exists in database
- Simple to implement (binary flags, aggregation)
- Directly addresses a stated Chapter 1 capability

**Proposed Features:**
- is_cross_border
- cross_border_volume_7d
- cross_border_frequency_7d
- cross_border_ratio_7d

**Expected Impact:** Direct improvement in cross-border laundering detection capability.

### 10.2 Transaction Sequence Features (HIGH VALUE, MEDIUM COMPLEXITY)
**Priority:** 2

**Rationale:**
- Transaction sequences are completely missing
- Raw data (timestamp, transaction_type) exists
- Addresses "complex laundering patterns" capability
- Enables detection of ordered patterns (e.g., deposit → transfer → withdrawal)

**Proposed Features:**
- transaction_type_sequence_last_3
- time_since_last_transaction
- recurring_pattern_score

**Expected Impact:** Significant improvement in complex pattern detection and flow analysis.

### 10.3 Structuring/Smurfing Detection (MEDIUM VALUE, LOW COMPLEXITY)
**Priority:** 3

**Rationale:**
- Structuring is partially represented but could be enhanced
- Raw data (amount, timestamp) exists
- Simple to implement (threshold-based analysis)
- Addresses a common AML typology

**Proposed Features:**
- amount_near_threshold_flag
- same_day_cumulative_amount
- structuring_pattern_score

**Expected Impact:** Improved detection of structuring/smurfing patterns.

---

## 11. RECOMMENDATION FOR NEXT EXPERIMENT

**Recommendation:** Implement and test the highest-value feature improvements identified in Section 10.

**Specific Recommendation:**

1. **Phase 1:** Implement cross-border activity features (Priority 1)
   - Extract destination_country from transactions table
   - Add is_cross_border, cross_border_volume_7d, cross_border_frequency_7d, cross_border_ratio_7d
   - Retrain model with expanded feature set (18 → 22 features)
   - Evaluate impact on cross-border laundering detection

2. **Phase 2:** Implement transaction sequence features (Priority 2)
   - Extract transaction type sequences and time gaps
   - Add transaction_type_sequence_last_3, time_since_last_transaction, recurring_pattern_score
   - Retrain model with expanded feature set (22 → 25 features)
   - Evaluate impact on complex pattern detection

3. **Phase 3:** Implement structuring/smurfing detection (Priority 3)
   - Add threshold-based and cumulative amount features
   - Retrain model with expanded feature set (25 → 28 features)
   - Evaluate impact on structuring detection

**Rationale:**
- These improvements directly address stated Chapter 1 capabilities that are currently missing or partially represented
- Raw data exists for all proposed features
- Implementation complexity is reasonable (LOW to MEDIUM)
- Incremental approach allows for controlled experimentation and impact measurement

**Alternative Recommendation:** If the user prefers to continue with model architecture experimentation (SMOTE, XGBoost) before feature engineering, defer feature improvements to a later stage.

---

## 12. CONFIRMATION OF NO CHANGES

**Explicit Confirmation:**

- **No code changes made** during this audit
- **No dataset changes made** during this audit
- **No label changes made** during this audit
- **No customer holdout changes made** during this audit
- **No chronological split changes made** during this audit
- **No frozen production model changes made** during this audit
- **No feature implementation performed** during this audit
- **No model retraining performed** during this audit

This audit was purely analytical and did not modify any frozen conditions or production systems.

---

## 13. CONCLUSION

**Summary:**

The current 18-feature set provides strong coverage for:
- Behavioural analysis
- Cash-based laundering
- Sudden behavioural changes
- Layering-like rapid movement
- Customer-specific behavioural deviation

The current 18-feature set has gaps in:
- Cross-border activity (completely missing)
- Transaction sequences (completely missing)
- Multi-account chain tracking (partially missing)
- Deposit → transfer → withdrawal flow analysis (partially missing)
- Structuring/smurfing detection (partially missing)

**Key Finding:** The most significant gap is the complete absence of cross-border activity features, despite this being a stated Chapter 1 capability and the raw data (destination_country) existing in the database.

**Recommendation:** Implement the highest-value feature improvements identified in Section 10, starting with cross-border activity features, to better align the ML feature set with the stated AML detection capabilities.

---

**STAGE 18 AUDIT COMPLETE — WAITING FOR APPROVAL**
