# STAGE 14B: FEATURE GAP DESIGN

**Date:** 2026-09-02  
**Status:** COMPLETE

---

## EXECUTIVE SUMMARY

Designed 25 candidate features to address the feature gaps identified in Stage 13. Features are designed specifically for AML scenarios that matter: structuring, layering, funnel, rapid_movement, behavioral_change, and severe scenarios.

**Key Finding:** high_risk_country scenario cannot be addressed without generator modification. All other scenarios can be addressed with available data dimensions.

---

## 1. STRUCTURING FEATURES (5)

### 1.1 threshold_proximity_10k
- **Definition:** Distance from $10,000 CTR threshold: |amount - 10000|
- **AML Meaning:** Detects transactions intentionally broken to avoid $10,000 reporting threshold
- **Data Requirements:** amount
- **Temporal Safety:** Computed from current transaction amount only
- **Observability:** Makes structuring observable by detecting near-threshold patterns

### 1.2 threshold_proximity_5k
- **Definition:** Distance from $5,000 threshold: |amount - 5000|
- **AML Meaning:** Detects transactions intentionally broken to avoid lower reporting thresholds
- **Data Requirements:** amount
- **Temporal Safety:** Computed from current transaction amount only
- **Observability:** Makes structuring observable by detecting near-threshold patterns

### 1.3 near_threshold_count_7d
- **Definition:** Count of transactions in last 7 days with amount in [8000, 12000]
- **AML Meaning:** Detects repeated near-threshold transactions (structuring pattern)
- **Data Requirements:** amount, timestamp, historical transactions
- **Temporal Safety:** Computed from historical transactions (last 7 days only)
- **Observability:** Makes structuring observable by detecting clustering near threshold

### 1.4 near_threshold_ratio_7d
- **Definition:** Ratio of near-threshold transactions to total transactions in last 7 days
- **AML Meaning:** Detects high proportion of near-threshold activity
- **Data Requirements:** amount, timestamp, historical transactions
- **Temporal Safety:** Computed from historical transactions (last 7 days only)
- **Observability:** Makes structuring observable by detecting clustering near threshold

### 1.5 amount_clustering_score
- **Definition:** Standard deviation of transaction amounts in last 7 days
- **AML Meaning:** Low variance indicates intentional amount clustering (structuring)
- **Data Requirements:** amount, timestamp, historical transactions
- **Temporal Safety:** Computed from historical transactions (last 7 days only)
- **Observability:** Makes structuring observable by detecting amount clustering

---

## 2. LAYERING FEATURES (5)

### 2.1 counterparty_diversity_7d
- **Definition:** Number of unique receiver accounts in last 7 days
- **AML Meaning:** High diversity indicates layering (funds moving through many accounts)
- **Data Requirements:** receiver_account, timestamp, historical transactions
- **Temporal Safety:** Computed from historical transactions (last 7 days only)
- **Observability:** Makes layering observable by detecting counterparty diversity

### 2.2 counterparty_diversity_30d
- **Definition:** Number of unique receiver accounts in last 30 days
- **AML Meaning:** High diversity indicates layering (funds moving through many accounts)
- **Data Requirements:** receiver_account, timestamp, historical transactions
- **Temporal Safety:** Computed from historical transactions (last 30 days only)
- **Observability:** Makes layering observable by detecting counterparty diversity

### 2.3 pass_through_ratio_7d
- **Definition:** Ratio of outbound transfers to total transactions in last 7 days
- **AML Meaning:** High pass-through ratio indicates layering (funds moving through account)
- **Data Requirements:** transaction_type, timestamp, historical transactions
- **Temporal Safety:** Computed from historical transactions (last 7 days only)
- **Observability:** Makes layering observable by detecting pass-through behavior

### 2.4 rapid_counterparty_switch_count
- **Definition:** Number of times receiver account changes in last 7 days
- **AML Meaning:** Frequent counterparty switches indicate layering
- **Data Requirements:** receiver_account, timestamp, historical transactions
- **Temporal Safety:** Computed from historical transactions (last 7 days only)
- **Observability:** Makes layering observable by detecting rapid counterparty changes

### 2.5 single_counterparty_dominance_7d
- **Definition:** Maximum percentage of transactions to single receiver in last 7 days
- **AML Meaning:** Low dominance indicates layering (funds distributed across many)
- **Data Requirements:** receiver_account, timestamp, historical transactions
- **Temporal Safety:** Computed from historical transactions (last 7 days only)
- **Observability:** Makes layering observable by detecting lack of counterparty concentration

---

## 3. FUNNEL FEATURES (4)

### 3.1 inbound_aggregation_7d
- **Definition:** Ratio of deposits to total transactions in last 7 days
- **AML Meaning:** High inbound ratio indicates funnel (funds from many sources)
- **Data Requirements:** transaction_type, timestamp, historical transactions
- **Temporal Safety:** Computed from historical transactions (last 7 days only)
- **Observability:** Makes funnel observable by detecting inbound aggregation

### 3.2 outbound_diversification_7d
- **Definition:** Ratio of transfers to total transactions in last 7 days
- **AML Meaning:** High outbound ratio indicates funnel (funds distributed to many)
- **Data Requirements:** transaction_type, timestamp, historical transactions
- **Temporal Safety:** Computed from historical transactions (last 7 days only)
- **Observability:** Makes funnel observable by detecting outbound diversification

### 3.3 many_to_one_ratio_7d
- **Definition:** Ratio of unique senders to unique receivers in last 7 days (network perspective)
- **AML Meaning:** Low ratio indicates funnel (many senders to few receivers)
- **Data Requirements:** sender_account, receiver_account, timestamp, historical transactions
- **Temporal Safety:** Computed from historical transactions (last 7 days only)
- **Observability:** Makes funnel observable by detecting many-to-one patterns

### 3.4 concentration_index_7d
- **Definition:** Herfindahl index of receiver concentration in last 7 days
- **AML Meaning:** High concentration indicates funnel (funds concentrated to few receivers)
- **Data Requirements:** receiver_account, amount, timestamp, historical transactions
- **Temporal Safety:** Computed from historical transactions (last 7 days only)
- **Observability:** Makes funnel observable by detecting receiver concentration

---

## 4. RAPID MOVEMENT FEATURES (4)

### 4.1 inbound_to_outbound_time_avg_7d
- **Definition:** Average time between deposit and subsequent transfer in last 7 days
- **AML Meaning:** Short average time indicates rapid movement (funds pass through quickly)
- **Data Requirements:** transaction_type, timestamp, historical transactions
- **Temporal Safety:** Computed from historical transactions (last 7 days only)
- **Observability:** Makes rapid movement observable by detecting quick pass-through

### 4.2 same_day_pass_through_count_7d
- **Definition:** Count of deposit-transfer pairs occurring on same day in last 7 days
- **AML Meaning:** High count indicates rapid movement (funds pass through same day)
- **Data Requirements:** transaction_type, timestamp, historical transactions
- **Temporal Safety:** Computed from historical transactions (last 7 days only)
- **Observability:** Makes rapid movement observable by detecting same-day pass-through

### 4.3 funds_through_ratio_7d
- **Definition:** Ratio of outbound amount to inbound amount in last 7 days
- **AML Meaning:** High ratio indicates rapid movement (most inbound funds passed through)
- **Data Requirements:** transaction_type, amount, timestamp, historical transactions
- **Temporal Safety:** Computed from historical transactions (last 7 days only)
- **Observability:** Makes rapid movement observable by detecting funds pass-through

### 4.4 velocity_score_7d
- **Definition:** Average number of transactions per day in last 7 days
- **AML Meaning:** High velocity indicates rapid movement
- **Data Requirements:** timestamp, historical transactions
- **Temporal Safety:** Computed from historical transactions (last 7 days only)
- **Observability:** Makes rapid movement observable by detecting high transaction velocity

---

## 5. BEHAVIORAL CHANGE FEATURES (4)

### 5.1 amount_deviation_from_baseline_30d
- **Definition:** Z-score of current amount relative to 30-day historical mean
- **AML Meaning:** High deviation indicates sudden change in amount behavior
- **Data Requirements:** amount, timestamp, historical transactions
- **Temporal Safety:** Computed from historical transactions (last 30 days only)
- **Observability:** Makes behavioral change observable by detecting amount deviation

### 5.2 frequency_deviation_from_baseline_30d
- **Definition:** Z-score of current transaction count relative to 30-day historical mean
- **AML Meaning:** High deviation indicates sudden change in frequency behavior
- **Data Requirements:** timestamp, historical transactions
- **Temporal Safety:** Computed from historical transactions (last 30 days only)
- **Observability:** Makes behavioral change observable by detecting frequency deviation

### 5.3 counterparty_change_score_7d
- **Definition:** Jaccard similarity between current 7-day and previous 7-day receiver sets
- **AML Meaning:** Low similarity indicates sudden change in counterparty behavior
- **Data Requirements:** receiver_account, timestamp, historical transactions
- **Temporal Safety:** Computed from historical transactions (last 14 days: current 7d vs previous 7d)
- **Observability:** Makes behavioral change observable by detecting counterparty change

### 5.4 rolling_behavioral_change_7d
- **Definition:** Standard deviation of amounts in last 7 days divided by standard deviation in previous 7 days
- **AML Meaning:** High ratio indicates sudden change in amount variability
- **Data Requirements:** amount, timestamp, historical transactions
- **Temporal Safety:** Computed from historical transactions (last 14 days: current 7d vs previous 7d)
- **Observability:** Makes behavioral change observable by detecting variability change

---

## 6. HIGH_RISK_COUNTRY FEATURES (0)

### 6.1 CRITICAL LIMITATION

**Cannot design features for high_risk_country**

**Reason:** Generator has country information but does not export it to dataset.

**Required:** recipient_country field in dataset.

**Current:** Accounts do not contain country codes (format: ACC######).

**Solution:** MODIFY GENERATOR to export country information to dataset.

---

## 7. SEVERE SCENARIO FEATURES (3)

### 7.1 concurrent_suspicious_indicators
- **Definition:** Count of suspicious behavioral indicators present simultaneously
- **AML Meaning:** High count indicates multiple AML typologies (severe scenario)
- **Data Requirements:** All candidate features
- **Temporal Safety:** Computed from current transaction features only
- **Observability:** Makes severe scenarios observable by aggregating suspicious indicators

### 7.2 typology_aggregation_score
- **Definition:** Combined score based on structuring + layering + funnel + rapid_movement indicators
- **AML Meaning:** High score indicates multiple AML typologies (severe scenario)
- **Data Requirements:** All candidate features
- **Temporal Safety:** Computed from current transaction features only
- **Observability:** Makes severe scenarios observable by aggregating typology indicators

### 7.3 severity_index
- **Definition:** Weighted sum of suspicious indicators based on severity weights
- **AML Meaning:** High index indicates severe scenario (multiple typologies)
- **Data Requirements:** All candidate features
- **Temporal Safety:** Computed from current transaction features only
- **Observability:** Makes severe scenarios observable by aggregating severity-weighted indicators

---

## 8. SUMMARY

**Total candidate features designed:** 25

**Features by scenario:**
- structuring: 5 features
- layering: 5 features
- funnel: 4 features
- rapid_movement: 4 features
- behavioral_change: 4 features
- high_risk_country: 0 features
- severe: 3 features

**Critical Finding:** high_risk_country scenario CANNOT be detected without generator modification. All other scenarios can be addressed with available data dimensions.
