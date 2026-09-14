# STAGE 14D: FEATURE SPECIFICATION

**Date:** 2026-09-02  
**Status:** COMPLETE

---

## EXECUTIVE SUMMARY

This specification defines the proposed revised feature set for Stage 15 implementation. The specification includes the existing 34 features (minus 1 constant feature), 25 new candidate features, and detailed definitions, AML scenario coverage, data availability, temporal-safety status, and expected observability improvement.

**Final Proposed Feature Count:** 57 features (34 original - 1 removed + 25 new)

---

## 1. EXISTING 34 FEATURES (STAGE 5 BASELINE)

### 1.1 Amount Features (7)

| Feature | Definition | Scenario Coverage | Observability |
|---------|-------------|-------------------|---------------|
| amount | Transaction amount | normal/suspicious/severe | MODERATE |
| sender_avg_amount | Average transaction amount for sender (historical) | normal/suspicious/severe | WEAK |
| sender_max_amount | Maximum transaction amount for sender (historical) | normal/suspicious/severe | WEAK |
| amount_to_sender_avg | Current amount divided by sender average amount | normal/suspicious/severe | WEAK |
| amount_to_sender_max | Current amount divided by sender maximum amount | normal/suspicious/severe | WEAK |
| amount_std_dev | Standard deviation of transaction amounts | normal/suspicious/severe | WEAK |
| amount_z_score | Z-score of current amount relative to historical | normal/suspicious/severe | WEAK |
| amount_change_vs_avg_7d | Change in amount vs 7-day average | normal/suspicious/severe | WEAK |

### 1.2 Velocity Features (4)

| Feature | Definition | Scenario Coverage | Observability |
|---------|-------------|-------------------|---------------|
| sender_tx_count_24h | Transaction count in last 24 hours | normal/suspicious/severe | WEAK |
| sender_volume_24h | Total transaction volume in last 24 hours | normal/suspicious/severe | WEAK |
| amount_to_sender_volume_24h | Current amount divided by 24h volume | normal/suspicious/severe | WEAK |
| same_day_count | Number of transactions on same day | normal/suspicious/severe | WEAK |
| same_day_total | Total transaction amount on same day | normal/suspicious/severe | WEAK |

### 1.3 Frequency Features (4)

| Feature | Definition | Scenario Coverage | Observability |
|---------|-------------|-------------------|---------------|
| sender_tx_count | Total transaction count for sender (historical) | normal/suspicious/severe | STRONG for severe |
| tx_frequency_7d | Transaction frequency in last 7 days | normal/suspicious/severe | WEAK |
| tx_frequency_30d | Transaction frequency in last 30 days | normal/suspicious/severe | STRONG for severe |
| frequency_change_vs_avg_7d | Change in frequency vs 7-day average | normal/suspicious/severe | MODERATE for severe |

### 1.4 Recipient Features (5)

| Feature | Definition | Scenario Coverage | Observability |
|---------|-------------|-------------------|---------------|
| is_new_recipient | Binary flag if recipient is new to sender | normal/suspicious/severe | WEAK |
| same_recipient_count | Count of previous transactions to same recipient | normal/suspicious/severe | WEAK |
| unique_recipients_24h | Number of unique recipients in last 24 hours | normal/suspicious/severe | WEAK |
| unique_recipients_7d | Number of unique recipients in last 7 days | normal/suspicious/severe | WEAK |
| recipient_concentration | Herfindahl index of recipient concentration | normal/suspicious/severe | WEAK |
| new_recipient_ratio_7d | Ratio of new recipients in last 7 days | normal/suspicious/severe | WEAK |

### 1.5 Timing Features (5)

| Feature | Definition | Scenario Coverage | Observability |
|---------|-------------|-------------------|---------------|
| hour | Hour of day (0-23) | normal/suspicious/severe | WEAK |
| day_of_week | Day of week (0-6) | normal/suspicious/severe | MODERATE for severe |
| is_weekend | Binary flag if transaction is on weekend | normal/suspicious/severe | MODERATE for severe |
| is_off_hours | Binary flag if transaction is outside business hours | normal/suspicious/severe | WEAK |
| time_since_last_tx | Time since last transaction (seconds) | normal/suspicious/severe | WEAK |

### 1.6 Transaction Type Features (4)

| Feature | Definition | Scenario Coverage | Observability |
|---------|-------------|-------------------|---------------|
| is_deposit | Binary flag if transaction type is deposit | normal/suspicious/severe | WEAK |
| is_withdraw | Binary flag if transaction type is withdraw | normal/suspicious/severe | WEAK |
| is_transfer | Binary flag if transaction type is transfer | normal/suspicious/severe | WEAK |
| is_self_transfer | Binary flag if sender == receiver | normal/suspicious/severe | NONE (constant 0.0) |

### 1.7 Velocity/Pass-Through Features (1)

| Feature | Definition | Scenario Coverage | Observability |
|---------|-------------|-------------------|---------------|
| rapid_transfer_count | Count of rapid transfers (inbound to outbound within 1 hour) | normal/suspicious/severe | WEAK |

---

## 2. NEW CANDIDATE FEATURES (STAGE 14B)

### 2.1 Structuring Features (5)

| Feature | Definition | AML Meaning | Temporal Safety |
|---------|-------------|-------------|----------------|
| threshold_proximity_10k | Distance from $10,000 CTR threshold: \|amount - 10000\| | Detects near-threshold transactions | SAFE (current) |
| threshold_proximity_5k | Distance from $5,000 threshold: \|amount - 5000\| | Detects near-threshold transactions | SAFE (current) |
| near_threshold_count_7d | Count of transactions in last 7 days with amount in [8000, 12000] | Detects repeated near-threshold patterns | SAFE (historical 7d) |
| near_threshold_ratio_7d | Ratio of near-threshold transactions to total in last 7 days | Detects high proportion of near-threshold activity | SAFE (historical 7d) |
| amount_clustering_score | Standard deviation of transaction amounts in last 7 days | Detects intentional amount clustering | SAFE (historical 7d) |

### 2.2 Layering Features (5)

| Feature | Definition | AML Meaning | Temporal Safety |
|---------|-------------|-------------|----------------|
| counterparty_diversity_7d | Number of unique receiver accounts in last 7 days | Detects counterparty diversity (layering) | SAFE (historical 7d) |
| counterparty_diversity_30d | Number of unique receiver accounts in last 30 days | Detects counterparty diversity (layering) | SAFE (historical 30d) |
| pass_through_ratio_7d | Ratio of outbound transfers to total transactions in last 7 days | Detects pass-through behavior (layering) | SAFE (historical 7d) |
| rapid_counterparty_switch_count | Number of counterparty changes in last 7 days | Detects rapid counterparty switches (layering) | SAFE (historical 7d) |
| single_counterparty_dominance_7d | Maximum percentage of transactions to single receiver in last 7 days | Detects lack of concentration (layering) | SAFE (historical 7d) |

### 2.3 Funnel Features (4)

| Feature | Definition | AML Meaning | Temporal Safety |
|---------|-------------|-------------|----------------|
| inbound_aggregation_7d | Ratio of deposits to total transactions in last 7 days | Detects inbound aggregation (funnel) | SAFE (historical 7d) |
| outbound_diversification_7d | Ratio of transfers to total transactions in last 7 days | Detects outbound diversification (funnel) | SAFE (historical 7d) |
| many_to_one_ratio_7d | Ratio of unique senders to unique receivers in last 7 days | Detects many-to-one patterns (funnel) | SAFE (historical 7d) |
| concentration_index_7d | Herfindahl index of receiver concentration in last 7 days | Detects receiver concentration (funnel) | SAFE (historical 7d) |

### 2.4 Rapid Movement Features (4)

| Feature | Definition | AML Meaning | Temporal Safety |
|---------|-------------|-------------|----------------|
| inbound_to_outbound_time_avg_7d | Average time between deposit and subsequent transfer in last 7 days | Detects quick pass-through (rapid movement) | SAFE (historical 7d) |
| same_day_pass_through_count_7d | Count of same-day deposit-transfer pairs in last 7 days | Detects same-day pass-through (rapid movement) | SAFE (historical 7d) |
| funds_through_ratio_7d | Ratio of outbound to inbound amount in last 7 days | Detects funds pass-through (rapid movement) | SAFE (historical 7d) |
| velocity_score_7d | Average transactions per day in last 7 days | Detects high transaction velocity (rapid movement) | SAFE (historical 7d) |

### 2.5 Behavioral Change Features (4)

| Feature | Definition | AML Meaning | Temporal Safety |
|---------|-------------|-------------|----------------|
| amount_deviation_from_baseline_30d | Z-score of current amount relative to 30-day historical mean | Detects sudden amount change (behavioral change) | SAFE (historical 30d) |
| frequency_deviation_from_baseline_30d | Z-score of current transaction count relative to 30-day historical mean | Detects sudden frequency change (behavioral change) | SAFE (historical 30d) |
| counterparty_change_score_7d | Jaccard similarity between current 7-day and previous 7-day receiver sets | Detects counterparty change (behavioral change) | SAFE (historical 14d) |
| rolling_behavioral_change_7d | Ratio of amount variability change (current 7d vs previous 7d) | Detects variability change (behavioral change) | SAFE (historical 14d) |

### 2.6 Severe Scenario Features (3)

| Feature | Definition | AML Meaning | Temporal Safety |
|---------|-------------|-------------|----------------|
| concurrent_suspicious_indicators | Count of suspicious behavioral indicators present simultaneously | Detects multiple AML typologies (severe) | SAFE (current) |
| typology_aggregation_score | Combined score based on structuring + layering + funnel + rapid_movement indicators | Detects multiple AML typologies (severe) | SAFE (current) |
| severity_index | Weighted sum of suspicious indicators based on severity weights | Detects severe scenario (multiple typologies) | SAFE (current) |

---

## 3. FEATURES TO REMOVE

### 3.1 Constant Feature

| Feature | Reason | Action |
|---------|--------|--------|
| is_self_transfer | CONSTANT (always 0.0 in Stage 11 dataset) | REMOVE from active modeling |

---

## 4. AML SCENARIO COVERAGE

### 4.1 Scenario Feature Coverage

| Scenario | Feature Count | Key Features |
|----------|---------------|--------------|
| structuring | 5 | threshold_proximity_10k, near_threshold_count_7d, amount_clustering_score |
| layering | 5 | counterparty_diversity_7d, pass_through_ratio_7d, rapid_counterparty_switch_count |
| funnel | 4 | inbound_aggregation_7d, concentration_index_7d, many_to_one_ratio_7d |
| rapid_movement | 4 | same_day_pass_through_count_7d, funds_through_ratio_7d, velocity_score_7d |
| behavioral_change | 4 | amount_deviation_from_baseline_30d, counterparty_change_score_7d |
| high_risk_country | 0 | NONE (requires generator modification) |
| severe | 35 | concurrent_suspicious_indicators, typology_aggregation_score, severity_index |

---

## 5. EXPECTED OBSERVABILITY IMPROVEMENT

### 5.1 Baseline vs Expected Observability

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

## 6. DATA AVABILITY

### 6.1 All Features

All 57 proposed features use only AVAILABLE data dimensions:
- amount
- timestamp
- transaction_type
- sender_account
- receiver_account
- historical transactions

### 6.2 Temporal Safety

All 57 proposed features are TEMPORALLY SAFE:
- Current transaction features: computed from current transaction only
- Historical features: computed from explicit time windows (7d, 30d, 14d)
- No future transactions
- No future aggregates
- No future labels
- No test-set information

---

## 7. FINAL PROPOSED FEATURE COUNT

**Original 34 features:** 34  
**Features to remove:** 1 (is_self_transfer)  
**New candidate features:** 25  
**Final proposed features:** 57

---

## 8. CRITICAL LIMITATION

**high_risk_country scenario cannot be detected without generator modification**

The generator has country information (HIGH_RISK_COUNTRIES, LEGITIMATE_COUNTRIES) but does not export it to the dataset. To detect high_risk_country scenarios, the generator must be modified to:
- Add `sender_country` column to dataset
- Add `receiver_country` column to dataset
- Assign countries to accounts during generation
- Export country information in CSV export

This is a generator modification, not a feature engineering task, and should be addressed in a future stage if needed.
