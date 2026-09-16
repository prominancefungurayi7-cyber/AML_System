# STAGE 14: FEATURE-ENGINEERING AUDIT/DESIGN REPORT

**Date:** 2026-09-02  
**Status:** PASS — Audit/design complete, ready for implementation

---

## EXECUTIVE SUMMARY

Stage 14 performed a comprehensive feature-engineering audit and design to address the feature gaps identified in Stage 13. The audit determined which AML dimensions are available from the existing generator/dataset, designed 25 candidate features to improve scenario observability, verified temporal safety for all features, and produced a final 57-feature specification.

**Key Findings:**
- **5 dimensions are AVAILABLE** from the existing dataset
- **8 dimensions are NOT AVAILABLE** without generator modification
- **25 candidate features designed** for structuring, layering, funnel, rapid_movement, behavioral_change, and severe scenarios
- **high_risk_country scenario CANNOT be detected** without generator modification
- **All 25 candidate features are TEMPORALLY SAFE**
- **Final proposed feature count: 57** (34 original - 1 removed + 25 new)
- **Expected observability improvement:** 5/6 scenarios (excluding high_risk_country)

**Recommendation:** Proceed to Stage 15 to implement the 57-feature specification and validate the improvements.

---

## 1. STAGE 14A: DATA/GENERATOR CAPABILITY AUDIT

### 1.1 Available Dimensions

**FULLY AVAILABLE (5):**
- recipient_account/counterparty_identity
- transaction_direction
- inbound_outbound_relationship
- account_to_account_network_relationships
- historical_customer_behavior

**PARTIALLY AVAILABLE (1):**
- transaction_purpose (description field exists but not structured)

**NOT AVAILABLE (8):**
- recipient_country (generator has info but not exported)
- sender_country (generator has info but not exported)
- account_age_tenure
- geographic_information
- device_ip_information
- cash_source_information
- ownership_beneficial_owner
- transaction_chains

### 1.2 Generator Capability

The Stage 3/11 generator defines:
- `HIGH_RISK_COUNTRIES`: 19 countries (FATF grey/black list)
- `LEGITIMATE_COUNTRIES`: 13 countries (legitimate jurisdictions)

**Status:** Generator has country information but does not export it to dataset.

### 1.3 Key Limitations

1. Generator has country information but does not export it to dataset
2. No account age/tenure information
3. No device/IP information
4. No ownership/beneficial owner information
5. No transaction chain tracking
6. No structured transaction purpose

---

## 2. STAGE 14B: FEATURE GAP DESIGN

### 2.1 Candidate Features by Scenario

**STRUCTURING (5 features):**
- threshold_proximity_10k
- threshold_proximity_5k
- near_threshold_count_7d
- near_threshold_ratio_7d
- amount_clustering_score

**LAYERING (5 features):**
- counterparty_diversity_7d
- counterparty_diversity_30d
- pass_through_ratio_7d
- rapid_counterparty_switch_count
- single_counterparty_dominance_7d

**FUNNEL (4 features):**
- inbound_aggregation_7d
- outbound_diversification_7d
- many_to_one_ratio_7d
- concentration_index_7d

**RAPID_MOVEMENT (4 features):**
- inbound_to_outbound_time_avg_7d
- same_day_pass_through_count_7d
- funds_through_ratio_7d
- velocity_score_7d

**BEHAVIORAL_CHANGE (4 features):**
- amount_deviation_from_baseline_30d
- frequency_deviation_from_baseline_30d
- counterparty_change_score_7d
- rolling_behavioral_change_7d

**HIGH_RISK_COUNTRY (0 features):**
- CRITICAL: Cannot design features without generator modification

**SEVERE (3 features):**
- concurrent_suspicious_indicators
- typology_aggregation_score
- severity_index

### 2.2 Total Candidate Features

**Total:** 25 candidate features designed

---

## 3. STAGE 14C: TEMPORAL SAFETY VERIFICATION

### 3.1 Temporal Safety Status

**Total features:** 25  
**Temporally safe:** 25  
**Temporally unsafe:** 0

### 3.2 Temporal Safety Guarantee

All features satisfy the temporal safety requirements:
1. All features use only current transaction data
2. All historical features use explicit time windows (7d, 30d, 14d)
3. No features use future transactions
4. No features use future aggregates
5. No features use future labels
6. No features use test-set information

### 3.3 Temporal Safety Implementation

For each transaction at time T:
- Current transaction data: available at T
- Historical data: transactions with timestamp < T
- Time window: filter historical transactions by timestamp >= T - window
- Compute feature: aggregate filtered historical transactions

---

## 4. STAGE 14D: FEATURE SPECIFICATION

### 4.1 Existing 34 Features

All 34 Stage 5 baseline features are preserved except:
- **is_self_transfer:** REMOVED (constant 0.0 in Stage 11 dataset)

### 4.2 New Candidate Features

25 new candidate features designed for:
- Structuring (5)
- Layering (5)
- Funnel (4)
- Rapid Movement (4)
- Behavioral Change (4)
- Severe (3)

### 4.3 Final Proposed Feature Count

**Original 34 features:** 34  
**Features to remove:** 1 (is_self_transfer)  
**New candidate features:** 25  
**Final proposed features:** 57

### 4.4 AML Scenario Coverage

| Scenario | Feature Count | Key Features |
|----------|---------------|--------------|
| structuring | 5 | threshold_proximity_10k, near_threshold_count_7d, amount_clustering_score |
| layering | 5 | counterparty_diversity_7d, pass_through_ratio_7d, rapid_counterparty_switch_count |
| funnel | 4 | inbound_aggregation_7d, concentration_index_7d, many_to_one_ratio_7d |
| rapid_movement | 4 | same_day_pass_through_count_7d, funds_through_ratio_7d, velocity_score_7d |
| behavioral_change | 4 | amount_deviation_from_baseline_30d, counterparty_change_score_7d |
| high_risk_country | 0 | NONE (requires generator modification) |
| severe | 35 | concurrent_suspicious_indicators, typology_aggregation_score, severity_index |

### 4.5 Expected Observability Improvement

| Scenario | Baseline (Stage 13) | Expected (Stage 14) | Improvement |
|----------|---------------------|-------------------|-------------|
| structuring | NONE | MODERATE | YES |
| layering | WEAK | MODERATE | YES |
| funnel | NONE | MODERATE | YES |
| rapid_movement | WEAK | MODERATE | YES |
| behavioral_change | NONE | MODERATE | YES |
| high_risk_country | NONE | NONE (requires generator modification) | NO |
| severe | MODERATE | STRONG | YES |

---

## 5. ANSWERS TO CRITICAL QUESTIONS

### 5.1 Which Missing AML Dimensions Can Be Recovered from Existing Generator?

**CAN BE RECOVERED:**
- Counterparty diversity (for layering/funnel)
- Pass-through behavior (for layering/rapid_movement)
- Threshold proximity (for structuring)
- Amount clustering (for structuring)
- Inbound/outbound aggregation (for funnel)
- Behavioral deviation (for behavioral_change)
- Transaction velocity (for rapid_movement)

**CANNOT BE RECOVERED WITHOUT GENERATOR MODIFICATION:**
- Country risk (for high_risk_country)
- Account age/tenure
- Geographic information
- Device/IP information
- Ownership/beneficial owner information
- Transaction chain tracking

### 5.2 Which Cannot Be Recovered Without Modifying the Generator?

**CANNOT BE RECOVERED:**
- **Country risk:** Generator has HIGH_RISK_COUNTRIES and LEGITIMATE_COUNTRIES but does not export them to dataset. Requires adding `sender_country` and `receiver_country` columns to dataset.
- **Account age/tenure:** Generator does not track account opening dates. Requires adding account creation timestamp.
- **Geographic information:** Generator does not track geographic location. Requires adding location data.
- **Device/IP information:** Generator does not track device or IP. Requires adding device/IP data.
- **Ownership/beneficial owner:** Generator does not track ownership structure. Requires adding ownership data.
- **Transaction chains:** Generator does not track chain relationships. Requires adding chain_id or related_transactions.

### 5.3 Which New Features Will Make Suspicious Scenarios Observable?

**STRUCTURING:**
- threshold_proximity_10k, threshold_proximity_5k: Detect near-threshold transactions
- near_threshold_count_7d, near_threshold_ratio_7d: Detect repeated near-threshold patterns
- amount_clustering_score: Detect intentional amount clustering

**LAYERING:**
- counterparty_diversity_7d, counterparty_diversity_30d: Detect counterparty diversity
- pass_through_ratio_7d: Detect pass-through behavior
- rapid_counterparty_switch_count: Detect rapid counterparty changes
- single_counterparty_dominance_7d: Detect lack of concentration

**FUNNEL:**
- inbound_aggregation_7d: Detect inbound aggregation
- outbound_diversification_7d: Detect outbound diversification
- many_to_one_ratio_7d: Detect many-to-one patterns
- concentration_index_7d: Detect receiver concentration

**RAPID_MOVEMENT:**
- inbound_to_outbound_time_avg_7d: Detect quick pass-through
- same_day_pass_through_count_7d: Detect same-day pass-through
- funds_through_ratio_7d: Detect funds pass-through
- velocity_score_7d: Detect high transaction velocity

**BEHAVIORAL_CHANGE:**
- amount_deviation_from_baseline_30d: Detect sudden amount change
- frequency_deviation_from_baseline_30d: Detect sudden frequency change
- counterparty_change_score_7d: Detect counterparty change
- rolling_behavioral_change_7d: Detect variability change

### 5.4 Which Features Remain Impossible to Derive?

**IMPOSSIBLE TO DERIVE WITHOUT GENERATOR MODIFICATION:**
- **Country risk features:** recipient_country, sender_country, is_high_risk_country
- **Account age features:** account_age, account_tenure
- **Geographic features:** location, distance, cross-border
- **Device/IP features:** device_fingerprint, ip_address, geolocation
- **Ownership features:** beneficial_owner, ownership_structure
- **Chain features:** chain_id, related_transactions, chain_length

### 5.5 How Will Temporal Safety Be Guaranteed?

**TEMPORAL SAFETY GUARANTEE:**

1. **Current transaction features:** Computed from current transaction only (e.g., amount, transaction_type)
2. **Historical features:** Computed from explicit time windows (7d, 30d, 14d)
3. **No future transactions:** All historical features use only transactions with timestamp < current timestamp
4. **No future aggregates:** All aggregates are computed over explicit time windows ending at current timestamp
5. **No future labels:** Features do not use ground_truth_label, scenario_id, or aml_typologies
6. **No test-set information:** Features do not use any test-set information

**Implementation:**
For each transaction at time T:
- Get current transaction data
- Get historical transactions with timestamp in [T - window, T)
- Compute feature by aggregating filtered historical transactions
- This uses only data available before T

### 5.6 What Is the Final Proposed Feature Specification?

**FINAL PROPOSED FEATURE SPECIFICATION:**

**Total features:** 57

**Composition:**
- Existing features (from Stage 5): 33 (34 - 1 removed)
- New candidate features (from Stage 14B): 25
- Removed features: 1 (is_self_transfer - constant 0.0)

**Feature categories:**
- Amount features: 8
- Velocity features: 5
- Frequency features: 4
- Recipient features: 6
- Timing features: 5
- Transaction type features: 3
- Structuring features: 5
- Layering features: 5
- Funnel features: 4
- Rapid movement features: 4
- Behavioral change features: 4
- Severe features: 3

**Data availability:** All features use AVAILABLE data dimensions

**Temporal safety:** All features are TEMPORALLY SAFE

### 5.7 What Should Stage 15 Implement?

**STAGE 15 IMPLEMENTATION PLAN:**

1. **Feature Extraction Implementation**
   - Implement 25 new candidate features
   - Remove is_self_transfer from feature set
   - Preserve 33 existing features
   - Validate feature extraction (no NaN, no infinite values)

2. **Temporal Safety Validation**
   - Verify temporal safety for all 57 features
   - Fix any temporal safety issues

3. **Feature Extraction on Stage 11 Dataset**
   - Extract 57 features for all 10,000 transactions
   - Save to ml_stage15_features.csv

4. **Model Training**
   - Train models (Random Forest, Gradient Boosting) on 57-feature set
   - Use PRIMARY split (customer-level holdout)
   - Compare with Stage 12 baseline (34 features)

5. **Scenario Observability Validation**
   - Compute Cohen's d for all scenarios using 57-feature set
   - Compare with Stage 13 baseline (34 features)
   - Verify observability improvements

6. **Model Performance Validation**
   - Compare model performance with Stage 12 baseline
   - Verify improvements in suspicious recall, super-suspicious recall, macro F1
   - Verify reduction in overfitting

7. **Validation Report**
   - Document all validation results
   - Create Stage 15 report
   - Determine if 57-feature set is approved for production

---

## 6. CRITICAL LIMITATION

### 6.1 High-Risk-Country Scenario

**LIMITATION:** high_risk_country scenario CANNOT be detected without generator modification.

**Reason:** Generator has country information (HIGH_RISK_COUNTRIES, LEGITIMATE_COUNTRIES) but does not export it to dataset.

**Required:** recipient_country field in dataset.

**Current:** Accounts do not contain country codes (format: ACC######).

**Solution:** MODIFY GENERATOR to export country information to dataset:
- Add `sender_country` column to dataset
- Add `receiver_country` column to dataset
- Assign countries to accounts during generation
- Export country information in CSV export

**Recommendation:** Address high_risk_country detection through generator modification in a future stage if needed.

---

## 7. ARTIFACT INTEGRITY VERIFICATION

### 7.1 Stage 14 Artifacts Created

- ml_stage14_data_capability_audit.py
- ml_stage14_data_capability_audit_results.json
- ml_stage14_data_capability_audit.md
- ml_stage14_feature_gap_design.py
- ml_stage14_feature_gap_design_results.json
- ml_stage14_feature_gap_design.md
- ml_stage14_temporal_safety_verification.py
- ml_stage14_temporal_safety_verification_results.json
- ml_stage14_feature_specification.py
- ml_stage14_feature_specification_results.json
- ml_stage14_feature_specification.md
- ml_stage14_feature_capability_matrix.csv
- ml_stage14_validation_plan.md
- ml_stage14_report.md (this report)

### 7.2 Previous Artifacts Preserved

All Stage 1-13 artifacts remain unchanged:
- No modifications to Stage 11 dataset
- No modifications to Stage 11 labels
- No modifications to Stage 11 generator
- No modifications to 34-feature specification
- No modifications to Stage 12 baseline models
- No modifications to Stage 6 artifacts

### 7.3 Verification

- [x] No model tuning was performed
- [x] No labels were changed
- [x] No official Stage 11 artifacts were modified
- [x] No official Stage 1-13 artifacts were modified
- [x] All calculations are reproducible
- [x] Previous stages remain intact
- [x] All features are temporally safe
- [x] All features are independent of labels

---

## 8. FINAL GATE DECISION

### 8.1 Acceptance Criteria

- [x] Data/generator capability audit completed
- [x] Feature gap design completed
- [x] Temporal safety verification completed
- [x] Feature specification completed
- [x] Validation plan completed
- [x] All features are temporally safe
- [x] All features are independent of labels
- [x] Expected observability improvement documented
- [x] Critical limitations documented
- [x] No Stage 1-13 artifacts modified
- [x] No Stage 11 dataset/labels modified
- [x] No Stage 11 generator modified

### 8.2 Decision

**PASS** — Stage 14 audit/design complete, ready for implementation

### 8.3 Summary

Stage 14 successfully designed a 57-feature specification to address the feature gaps identified in Stage 13. The audit identified that 5 AML dimensions are available from the existing dataset, 8 dimensions are not available without generator modification, and 25 candidate features were designed to improve scenario observability. All features are temporally safe and independent of labels. The high_risk_country scenario cannot be detected without generator modification.

**Recommendation:** Proceed to Stage 15 to implement the 57-feature specification and validate the improvements.

---

## 9. STAGE 15 NEXT STEPS

### 9.1 Implementation Tasks

1. Implement 25 new candidate features
2. Remove is_self_transfer from feature set
3. Extract 57 features for all 10,000 transactions
4. Validate temporal safety
5. Train models on 57-feature set
6. Validate scenario observability improvements
7. Validate model performance improvements
8. Create Stage 15 report

### 9.2 Success Criteria

Stage 15 is successful if:
- All 57 features are implemented correctly
- All features are temporally safe
- Scenario observability improves for 5/6 scenarios (excluding high_risk_country)
- Model performance improves (suspicious recall, super-suspicious recall, macro F1)
- No Stage 1-13 artifacts are modified
- No Stage 11 dataset/labels are modified
- No Stage 11 generator is modified

---

# STAGE 14 COMPLETE — PASS — WAITING FOR APPROVAL

**CRITICAL STOP CONDITION:** Do NOT automatically proceed to Stage 15. Wait for explicit approval after presenting the Stage 14 report.
