# Stage 16B Feature Expansion Specification

**Date:** 2026-09-15  
**Stage:** 16B — Controlled Structuring Feature Expansion Experiment  
**Status:** FEATURE SPECIFICATION  
**Specification Version:** 1.0

---

## 1. Objective

Implement four scientifically justified structuring features based on Stage 16A diagnostic findings to improve weak Structuring-domain detection (currently 30.8% recall) while maintaining Network (74.3% recall) and Agent (58.8% recall) performance.

---

## 2. Baseline Configuration

**Dataset:** ecocash_aml_synthetic_100k_v1  
**Original Features:** 30 (frozen from Stage 13)  
**Expanded Features:** 34 (30 original + 4 new)  
**Baseline Model:** Stage 14 Gradient Boosting (frozen)  
**Baseline Threshold:** 0.35 (frozen)

---

## 3. Candidate Feature Specifications

### Feature 31: `structuring_approximate_repetition_ratio_30d`

**Definition:**
For the current sender wallet, calculate the proportion of eligible prior outgoing transactions within the previous 30 days whose amounts are within ±10% of the current transaction amount.

**Formula:**
```
approximate_repetition_ratio = count(prior_amounts within ±10% of current_amount) / count(eligible_prior_transactions)
```

**Raw Fields Required:**
- transaction amounts
- transaction timestamps
- sender wallet IDs
- transaction direction (outgoing only)

**Historical Window:** 30 days  
**Transaction Direction:** Outgoing only  
**Current Event Treatment:** Excluded from history  
**Temporal Ordering:** (event_timestamp, event_sequence)  
**Cold Start:** Return 0.0 when insufficient prior history exists  
**Expected Data Type:** Float (ratio in [0,1])  
**Expected Range:** [0.0, 1.0]  
**Prediction-Time Availability:** Yes  
**Leakage Risk:** Low (uses only historical transaction amounts)  
**Scenario Label Risk:** Low (captures general approximate repetition pattern, not scenario-specific)  
**AML Rationale:** Sophisticated structuring often uses slightly varied amounts to avoid detection, while normal customers may have exact repeated amounts (e.g., subscriptions).

---

### Feature 32: `structuring_transaction_spacing_std_30d`

**Definition:**
Calculate the standard deviation of time gaps between consecutive eligible prior outgoing transactions for the sender wallet within the previous 30 days.

**Formula:**
```
gaps = [timestamp[i+1] - timestamp[i] for i in range(len(timestamps) - 1)]
spacing_std = standard_deviation(gaps)
```

**Raw Fields Required:**
- transaction timestamps
- sender wallet IDs
- transaction direction (outgoing only)

**Historical Window:** 30 days  
**Transaction Direction:** Outgoing only  
**Current Event Treatment:** Excluded from history  
**Temporal Ordering:** (event_timestamp, event_sequence)  
**Cold Start:** Return 0.0 when fewer than 2 eligible prior transactions exist  
**Expected Data Type:** Float (seconds)  
**Expected Range:** [0.0, large_positive]  
**Prediction-Time Availability:** Yes  
**Leakage Risk:** Low (uses only historical transaction timestamps)  
**Scenario Label Risk:** Low (captures general temporal pattern, not scenario-specific)  
**AML Rationale:** Structuring patterns often have characteristic spacing (e.g., regular bursts, specific intervals) that differ from normal transaction patterns.

---

### Feature 33: `structuring_threshold_proximity_ratio_30d`

**Definition:**
Calculate the proportion of eligible prior outgoing transactions within the previous 30 days whose amounts fall within ±10% of the configured synthetic reporting threshold.

**Formula:**
```
threshold = 10000 (synthetic_reporting_threshold_v1)
threshold_proximity_ratio = count(prior_amounts within ±10% of threshold) / count(eligible_prior_transactions)
```

**Raw Fields Required:**
- transaction amounts
- transaction timestamps
- sender wallet IDs
- transaction direction (outgoing only)
- threshold value (from configuration)

**Historical Window:** 30 days  
**Transaction Direction:** Outgoing only  
**Current Event Treatment:** Excluded from history  
**Temporal Ordering:** (event_timestamp, event_sequence)  
**Threshold Value:** 10000 (synthetic_reporting_threshold_v1)  
**Cold Start:** Return 0.0 when no eligible prior transactions exist  
**Expected Data Type:** Float (ratio in [0,1])  
**Expected Range:** [0.0, 1.0]  
**Prediction-Time Availability:** Yes  
**Leakage Risk:** Low (uses only historical transaction amounts and configured threshold)  
**Scenario Label Risk:** Low (captures general threshold avoidance pattern, not scenario-specific)  
**AML Rationale:** AML structuring often involves amounts just below reporting thresholds to avoid detection; this pattern is distinct from normal transaction amounts.

**Important:** This feature must be treated as a behavioural feature, NOT as an AML rule. Normal transactions near the synthetic threshold must remain possible.

---

### Feature 34: `structuring_fragment_size_trend_30d`

**Definition:**
Calculate the trend coefficient of prior outgoing transaction amounts over the previous 30 days, ordered by event time using linear regression slope.

**Formula:**
```
time_indices = [0, 1, 2, ..., n-1] for n transactions
trend_coefficient = linear_regression_slope(time_indices, amounts)
```

**Raw Fields Required:**
- transaction amounts
- transaction timestamps
- sender wallet IDs
- transaction direction (outgoing only)

**Historical Window:** 30 days  
**Transaction Direction:** Outgoing only  
**Current Event Treatment:** Excluded from history  
**Temporal Ordering:** (event_timestamp, event_sequence)  
**Cold Start:** Return 0.0 when fewer than 3 eligible prior transactions exist  
**Expected Data Type:** Float (trend coefficient)  
**Expected Range:** [negative_large, positive_large]  
**Prediction-Time Availability:** Yes  
**Leakage Risk:** Low (uses only historical transaction amounts and timestamps)  
**Scenario Label Risk:** Low (captures general amount trend, not scenario-specific)  
**AML Rationale:** Sophisticated structuring may involve gradually decreasing fragment sizes to avoid detection, distinct from normal payment patterns.

---

## 4. Temporal Contract Requirements

### 4.1 Event Ordering
All transactions must be ordered by `(event_timestamp, event_sequence)` in lexicographic order.

### 4.2 Historical Eligibility
For event `t`, a historical transaction `h` is eligible only if:
```
(h.event_timestamp, h.event_sequence) < (t.event_timestamp, t.event_sequence)
```

### 4.3 Exclusion Requirements
- Current transaction MUST NOT influence its own feature values
- Future transactions MUST NOT influence earlier events
- Equal timestamps MUST respect event_sequence ordering
- Later equal-timestamp transactions MUST NOT influence earlier transactions

### 4.4 Partition Isolation
Historical transactions must belong to the same partition as the current transaction:
- Train history only for Train transactions
- Validation history only for Validation transactions
- Final Test history only for Final Test transactions
- Independent history only for Independent transactions

### 4.5 Entity Isolation
Wallet/customer/agent isolation must be maintained:
- Only use history from the same sender wallet
- No cross-wallet history contamination
- No cross-customer history contamination
- No cross-agent history contamination

---

## 5. Cold-Start Behavior

| Feature | Cold-Start Condition | Return Value |
|---------|-------------------|-------------|
| approximate_repetition_ratio_30d | Insufficient prior history | 0.0 |
| transaction_spacing_std_30d | Fewer than 2 prior transactions | 0.0 |
| threshold_proximity_ratio_30d | No eligible prior transactions | 0.0 |
| fragment_size_trend_30d | Fewer than 3 prior transactions | 0.0 |

---

## 6. Data Type and Range Validation

| Feature | Data Type | Expected Range | Validation Requirements |
|---------|-----------|---------------|------------------------|
| approximate_repetition_ratio_30d | Float | [0.0, 1.0] | Must be within [0,1], no NaN/Infinity |
| transaction_spacing_std_30d | Float | [0.0, large_positive] | Must be non-negative, no NaN/Infinity |
| threshold_proximity_ratio_30d | Float | [0.0, 1.0] | Must be within [0,1], no NaN/Infinity |
| fragment_size_trend_30d | Float | [negative_large, positive_large] | Must be finite, no NaN/Infinity |

---

## 7. Implementation Requirements

### 7.1 Efficiency
Target O(n log n) or better complexity. No O(n²) full-history scanning.

### 7.2 Determinism
Implementation must be deterministic:
- Fixed order of operations
- No random operations
- Consistent tie-breaking

### 7.3 Memory Efficiency
Use appropriate per-wallet historical indexes/state structures.

---

## 8. Experimental Matrix Location

**Original Matrices (Baseline):**
`data/ecocash_aml_synthetic_100k_v1/features/`

**Experimental Matrices (Stage 16B):**
`data/ecocash_aml_synthetic_100k_v1/features_stage16b/`

**Naming Convention:**
- `X_train_34.npy` (34 features)
- `X_val_34.npy` (34 features)
- `X_test_34.npy` (34 features)
- `X_independent_34.npy` (34 features)
- `y_train_34.npy` (same targets)
- `y_val_34.npy` (same targets)
- `y_test_34.npy` (same targets)
- `y_independent_34.npy` (same targets)

---

## 9. Feature Order

**Columns 1-30:** Original 30 features (exact order from Stage 13)
**Columns 31-34:** New structuring features (order as specified above)

---

## 10. Validation Requirements

Before full extraction, mandatory tests:
- Test A: Current-event exclusion
- Test B: Future exclusion
- Test C: Equal timestamp ordering
- Test D: Partition isolation
- Test E: Approximate repetition calculation
- Test F: Spacing calculation
- Test G: Threshold proximity calculation
- Test H: Trend calculation
- Test I: Cold start behavior
- Test J: Determinism
- Test K: Numerical safety (no NaN/Infinity)
- Test L: Original 30-feature preservation (byte-for-byte identical)

---

## 11. Leakage Protection

The four new features MUST NOT use:
- ground_truth_label
- scenario_id
- scenario_type
- scenario_category
- signal_strength
- provenance
- generation metadata
- partition labels
- model predictions
- risk scores
- risk levels
- rule outputs
- alerts
- investigations
- future transactions
- current transaction amount (except for Feature 31 comparison reference)
- any post-event information

Feature 31 may use the CURRENT transaction amount only as the comparison reference for prior amounts.
Feature 33 may use the configured synthetic threshold (10000).

---

## 12. Research Rationale Summary

The four features address the primary causes identified in Stage 16A:

1. **approximate_repetition_ratio_30d** - Addresses missing approximate amount patterns (vs exact repetition only)
2. **transaction_spacing_std_30d** - Addresses missing temporal distribution patterns
3. **threshold_proximity_ratio_30d** - Addresses missing threshold proximity information
4. **fragment_size_trend_30d** - Addresses missing fragmentation trend patterns

All features use 30-day windows to reduce cold-start problems and capture longer-term patterns.

---

*Specification Version: 1.0*
*Date: 2026-09-15*
*Dataset: ecocash_aml_synthetic_100k_v1*
*Feature Count: 34 (30 original + 4 new)*
