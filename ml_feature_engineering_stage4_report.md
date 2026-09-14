# STAGE 4: FEATURE ENGINEERING AUDIT AND REDESIGN REPORT

**Date:** 2026-09-01  
**Purpose:** Audit existing feature engineering against Stage 3 dataset and redesign for independent behavioral learning

---

## EXECUTIVE SUMMARY

The Stage 3 dataset provides a solid foundation with 14 behavioral features and no rule-like features. However, the existing `ai_core.py` feature extraction function is incompatible with the new dataset structure and contains rule-like features that must be removed.

**Key findings:**
- Stage 3 dataset has **14 features** (not 20 as initially reported - discrepancy due to identifier/metadata classification)
- Stage 3 dataset **excludes all rule-like features** (GOOD)
- Existing `ai_core.py` has **25 features** including 4 rule-like features (BAD)
- Missing derived features from Stage 3: hour, transaction type encoding, channel encoding, self-transfer indicator, off-hours indicator
- Temporal safety is **conditionally safe** - depends on training pipeline implementation
- Customer-level and temporal splitting are **supported** by Stage 3 dataset

**Recommendation:** Create a new feature extraction function compatible with Stage 3 dataset, add missing behavioral features, and remove all rule-like features.

---

## 1. STAGE 1-3 CONTEXT

### 1.1 Stage 1 Findings
- Identified 4 rule-like features in existing implementation: `is_large_amount`, `is_structuring_band`, `structuring_indicators`, `layering_indicators`
- Found label leakage from rule engine to ML labels
- Identified missing geographic, temporal, and recipient diversity features

### 1.2 Stage 2 Findings
- Baseline performance: 32% accuracy, 28% suspicious recall, 16% super-suspicious recall
- Model over-reliant on simple amount ratios
- Sequence-based features had very low importance

### 1.3 Stage 3 Achievements
- Created customer behavioral profiles (200 customers, 50 transactions each)
- Independent ground-truth labels from AML typologies (NOT rule engine)
- Separated features from ground truth (prevents label leakage)
- Achieved 69/22/9 class distribution (matches 70/20/10 target)
- Introduced realistic class overlap (legitimate high-value, borderline cases)
- Supported customer-level and temporal evaluation

---

## 2. EXISTING FEATURE INVENTORY

### 2.1 Existing ai_core.py Features (25 total)

| # | Feature Name | Type | Source | Rule-Like? |
|---|--------------|------|--------|------------|
| 1 | amount | float | Transaction | No |
| 2 | hour | int | Derived from timestamp | No |
| 3 | is_deposit | binary | Derived from transaction_type | No |
| 4 | is_withdraw | binary | Derived from transaction_type | No |
| 5 | is_transfer | binary | Derived from transaction_type | No |
| 6 | is_self_transfer | binary | Derived from sender==receiver | No |
| 7 | is_off_hours | binary | Derived from hour | No |
| 8 | sender_avg_amount | float | Historical aggregation | No |
| 9 | sender_max_amount | float | Historical aggregation | No |
| 10 | sender_tx_count | float | Historical aggregation | No |
| 11 | amount_to_sender_avg | float | Computed ratio | No |
| 12 | amount_to_sender_max | float | Computed ratio | No |
| 13 | sender_tx_count_24h | float | Historical aggregation (24h) | No |
| 14 | sender_volume_24h | float | Historical aggregation (24h) | No |
| 15 | amount_to_sender_volume_24h | float | Computed ratio | No |
| 16 | is_new_recipient | float | Historical comparison | No |
| 17 | channel_encoded | int | Channel mapping | No |
| 18 | is_large_amount | binary | Threshold >=10000 | **YES** |
| 19 | is_structuring_band | binary | Threshold 8500-9999 | **YES** |
| 20 | same_day_count | float | Sequence aggregation | No |
| 21 | same_day_total | float | Sequence aggregation | No |
| 22 | same_recipient_count | float | Sequence aggregation | No |
| 23 | rapid_transfer_count | float | Sequence aggregation | No |
| 24 | structuring_indicators | float | Computed from amount+count | **YES** |
| 25 | layering_indicators | float | Computed from sequence | **YES** |

### 2.2 Stage 3 Dataset Features (14 total)

| # | Feature Name | Type | Source | In ai_core.py? |
|---|--------------|------|--------|---------------|
| 1 | amount | float | Transaction | Yes |
| 2 | sender_avg_amount | float | Historical aggregation | Yes |
| 3 | sender_max_amount | float | Historical aggregation | Yes |
| 4 | sender_tx_count | float | Historical aggregation | Yes |
| 5 | amount_to_sender_avg | float | Computed ratio | Yes |
| 6 | amount_to_sender_max | float | Computed ratio | Yes |
| 7 | sender_tx_count_24h | float | Historical aggregation (24h) | Yes |
| 8 | sender_volume_24h | float | Historical aggregation (24h) | Yes |
| 9 | amount_to_sender_volume_24h | float | Computed ratio | Yes |
| 10 | is_new_recipient | float | Historical comparison | Yes |
| 11 | same_day_count | float | Sequence aggregation | Yes |
| 12 | same_day_total | float | Sequence aggregation | Yes |
| 13 | same_recipient_count | float | Sequence aggregation | Yes |
| 14 | rapid_transfer_count | float | Sequence aggregation | Yes |

### 2.3 Missing Derived Features

Features in ai_core.py but NOT in Stage 3 dataset (can be derived):

| Feature | Source | Can Be Derived From |
|---------|--------|---------------------|
| hour | timestamp | timestamp |
| is_deposit | transaction_type | transaction_type |
| is_withdraw | transaction_type | transaction_type |
| is_transfer | transaction_type | transaction_type |
| is_self_transfer | sender_account, receiver_account | sender_account == receiver_account |
| is_off_hours | hour | hour |
| channel_encoded | channel | channel |

Features in ai_core.py but NOT in Stage 3 dataset (rule-like, intentionally excluded):

| Feature | Reason for Exclusion |
|---------|---------------------|
| is_large_amount | Encodes CTR threshold rule |
| is_structuring_band | Encodes structuring threshold rule |
| structuring_indicators | Encodes structuring detection logic |
| layering_indicators | Encodes layering detection logic |

---

## 3. FEATURE-BY-FEATURE AUDIT

### 3.1 Stage 3 Dataset Features

#### amount
- **Data type:** float
- **Meaning:** Transaction amount in currency
- **Source:** Transaction record
- **How calculated:** Direct from transaction
- **Available at prediction time:** Yes
- **Uses historical information:** No
- **Temporal leakage risk:** None
- **Customer leakage risk:** None
- **Encodes AML rules:** No
- **Redundant:** No
- **Useful for behavioral learning:** Yes (when combined with historical context)
- **Decision:** **KEEP**

#### sender_avg_amount
- **Data type:** float
- **Meaning:** Customer's average transaction amount from history
- **Source:** Historical aggregation
- **How calculated:** Mean of past transaction amounts
- **Available at prediction time:** Yes
- **Uses historical information:** Yes
- **Temporal leakage risk:** Low (if computed from past transactions only)
- **Customer leakage risk:** None
- **Encodes AML rules:** No
- **Redundant:** No
- **Useful for behavioral learning:** Yes (provides customer baseline)
- **Decision:** **KEEP**

#### sender_max_amount
- **Data type:** float
- **Meaning:** Customer's maximum transaction amount from history
- **Source:** Historical aggregation
- **How calculated:** Max of past transaction amounts
- **Available at prediction time:** Yes
- **Uses historical information:** Yes
- **Temporal leakage risk:** Low (if computed from past transactions only)
- **Customer leakage risk:** None
- **Encodes AML rules:** No
- **Redundant:** No
- **Useful for behavioral learning:** Yes (provides customer baseline)
- **Decision:** **KEEP**

#### sender_tx_count
- **Data type:** float
- **Meaning:** Total number of customer's past transactions
- **Source:** Historical aggregation
- **How calculated:** Count of past transactions
- **Available at prediction time:** Yes
- **Uses historical information:** Yes
- **Temporal leakage risk:** Low (if computed from past transactions only)
- **Customer leakage risk:** None
- **Encodes AML rules:** No
- **Redundant:** Partially (redundant with sender_tx_count_24h for recent activity)
- **Useful for behavioral learning:** Yes (customer experience level)
- **Decision:** **KEEP**

#### amount_to_sender_avg
- **Data type:** float
- **Meaning:** Current amount relative to customer's average
- **Source:** Computed ratio
- **How calculated:** amount / sender_avg_amount
- **Available at prediction time:** Yes
- **Uses historical information:** Yes (via sender_avg_amount)
- **Temporal leakage risk:** Low (inherited from sender_avg_amount)
- **Customer leakage risk:** None
- **Encodes AML rules:** No
- **Redundant:** No
- **Useful for behavioral learning:** Yes (deviation from baseline)
- **Decision:** **KEEP**

#### amount_to_sender_max
- **Data type:** float
- **Meaning:** Current amount relative to customer's maximum
- **Source:** Computed ratio
- **How calculated:** amount / sender_max_amount
- **Available at prediction time:** Yes
- **Uses historical information:** Yes (via sender_max_amount)
- **Temporal leakage risk:** Low (inherited from sender_max_amount)
- **Customer leakage risk:** None
- **Encodes AML rules:** No
- **Redundant:** Partially (similar to amount_to_sender_avg)
- **Useful for behavioral learning:** Yes (deviation from baseline)
- **Decision:** **KEEP**

#### sender_tx_count_24h
- **Data type:** float
- **Meaning:** Number of transactions in last 24 hours
- **Source:** Historical aggregation (24h window)
- **How calculated:** Count of transactions in 24h window before current transaction
- **Available at prediction time:** Yes
- **Uses historical information:** Yes
- **Temporal leakage risk:** Low (if window is strictly before current transaction)
- **Customer leakage risk:** None
- **Encodes AML rules:** No
- **Redundant:** No
- **Useful for behavioral learning:** Yes (velocity feature)
- **Decision:** **KEEP**

#### sender_volume_24h
- **Data type:** float
- **Meaning:** Total transaction volume in last 24 hours
- **Source:** Historical aggregation (24h window)
- **How calculated:** Sum of amounts in 24h window before current transaction
- **Available at prediction time:** Yes
- **Uses historical information:** Yes
- **Temporal leakage risk:** Low (if window is strictly before current transaction)
- **Customer leakage risk:** None
- **Encodes AML rules:** No
- **Redundant:** No
- **Useful for behavioral learning:** Yes (velocity feature)
- **Decision:** **KEEP**

#### amount_to_sender_volume_24h
- **Data type:** float
- **Meaning:** Current amount relative to 24h volume
- **Source:** Computed ratio
- **How calculated:** amount / sender_volume_24h
- **Available at prediction time:** Yes
- **Uses historical information:** Yes (via sender_volume_24h)
- **Temporal leakage risk:** Low (inherited from sender_volume_24h)
- **Customer leakage risk:** None
- **Encodes AML rules:** No
- **Redundant:** Partially (similar to amount_to_sender_avg)
- **Useful for behavioral learning:** Yes (proportion of recent activity)
- **Decision:** **KEEP**

#### is_new_recipient
- **Data type:** float
- **Meaning:** Whether recipient is new to customer
- **Source:** Historical comparison
- **How calculated:** 1.0 if recipient not seen before, 0.0 otherwise
- **Available at prediction time:** Yes
- **Uses historical information:** Yes
- **Temporal leakage risk:** Low (if computed from past transactions only)
- **Customer leakage risk:** None
- **Encodes AML rules:** No
- **Redundant:** No
- **Useful for behavioral learning:** Yes (recipient network change)
- **Decision:** **KEEP**

#### same_day_count
- **Data type:** float
- **Meaning:** Number of transactions on same day
- **Source:** Sequence aggregation
- **How calculated:** Count of transactions with same date before current transaction
- **Available at prediction time:** Yes
- **Uses historical information:** Yes
- **Temporal leakage risk:** Low (if computed from earlier same-day transactions only)
- **Customer leakage risk:** None
- **Encodes AML rules:** No
- **Redundant:** No
- **Useful for behavioral learning:** Yes (daily velocity)
- **Decision:** **KEEP**

#### same_day_total
- **Data type:** float
- **Meaning:** Total transaction amount on same day
- **Source:** Sequence aggregation
- **How calculated:** Sum of amounts with same date before current transaction
- **Available at prediction time:** Yes
- **Uses historical information:** Yes
- **Temporal leakage risk:** Low (if computed from earlier same-day transactions only)
- **Customer leakage risk:** None
- **Encodes AML rules:** No
- **Redundant:** No
- **Useful for behavioral learning:** Yes (daily volume)
- **Decision:** **KEEP**

#### same_recipient_count
- **Data type:** float
- **Meaning:** Number of transactions to same recipient in 24h
- **Source:** Sequence aggregation
- **How calculated:** Count of transactions to same recipient in 24h window
- **Available at prediction time:** Yes
- **Uses historical information:** Yes
- **Temporal leakage risk:** Low (if window is strictly before current transaction)
- **Customer leakage risk:** None
- **Encodes AML rules:** No
- **Redundant:** No
- **Useful for behavioral learning:** Yes (recipient concentration)
- **Decision:** **KEEP**

#### rapid_transfer_count
- **Data type:** float
- **Meaning:** Number of rapid transfers (within 10 minutes)
- **Source:** Sequence aggregation
- **How calculated:** Count of transactions within 10 minutes before current transaction
- **Available at prediction time:** Yes
- **Uses historical information:** Yes
- **Temporal leakage risk:** Low (if computed from earlier transactions only)
- **Customer leakage risk:** None
- **Encodes AML rules:** No
- **Redundant:** No
- **Useful for behavioral learning:** Yes (layering detection)
- **Decision:** **KEEP**

### 3.2 Missing Derived Features (to be added)

#### hour
- **Data type:** int
- **Meaning:** Hour of day (0-23)
- **Source:** Derived from timestamp
- **How calculated:** Extract hour from timestamp
- **Available at prediction time:** Yes
- **Uses historical information:** No
- **Temporal leakage risk:** None
- **Customer leakage risk:** None
- **Encodes AML rules:** No
- **Redundant:** No
- **Useful for behavioral learning:** Yes (temporal pattern)
- **Decision:** **ADD**

#### is_deposit
- **Data type:** binary
- **Meaning:** Whether transaction is a deposit
- **Source:** Derived from transaction_type
- **How calculated:** 1 if transaction_type == "deposit", else 0
- **Available at prediction time:** Yes
- **Uses historical information:** No
- **Temporal leakage risk:** None
- **Customer leakage risk:** None
- **Encodes AML rules:** No
- **Redundant:** No (part of one-hot encoding)
- **Useful for behavioral learning:** Yes (transaction type pattern)
- **Decision:** **ADD**

#### is_withdraw
- **Data type:** binary
- **Meaning:** Whether transaction is a withdrawal
- **Source:** Derived from transaction_type
- **How calculated:** 1 if transaction_type == "withdraw", else 0
- **Available at prediction time:** Yes
- **Uses historical information:** No
- **Temporal leakage risk:** None
- **Customer leakage risk:** None
- **Encodes AML rules:** No
- **Redundant:** No (part of one-hot encoding)
- **Useful for behavioral learning:** Yes (transaction type pattern)
- **Decision:** **ADD**

#### is_transfer
- **Data type:** binary
- **Meaning:** Whether transaction is a transfer
- **Source:** Derived from transaction_type
- **How calculated:** 1 if transaction_type == "transfer", else 0
- **Available at prediction time:** Yes
- **Uses historical information:** No
- **Temporal leakage risk:** None
- **Customer leakage risk:** None
- **Encodes AML rules:** No
- **Redundant:** No (part of one-hot encoding)
- **Useful for behavioral learning:** Yes (transaction type pattern)
- **Decision:** **ADD**

#### is_self_transfer
- **Data type:** binary
- **Meaning:** Whether sender and receiver are the same
- **Source:** Derived from sender_account, receiver_account
- **How calculated:** 1 if sender_account == receiver_account, else 0
- **Available at prediction time:** Yes
- **Uses historical information:** No
- **Temporal leakage risk:** None
- **Customer leakage risk:** None
- **Encodes AML rules:** No
- **Redundant:** No
- **Useful for behavioral learning:** Yes (self-transfer pattern)
- **Decision:** **ADD**

#### is_off_hours
- **Data type:** binary
- **Meaning:** Whether transaction occurred during off-hours
- **Source:** Derived from hour
- **How calculated:** 1 if hour < 5 or hour >= 23, else 0
- **Available at prediction time:** Yes
- **Uses historical information:** No
- **Temporal leakage risk:** None
- **Customer leakage risk:** None
- **Encodes AML rules:** No
- **Redundant:** No
- **Useful for behavioral learning:** Yes (temporal anomaly)
- **Decision:** **ADD**

#### channel_encoded
- **Data type:** int
- **Meaning:** Encoded channel type
- **Source:** Derived from channel
- **How calculated:** Map channel to integer (online=0, mobile=1, atm=2, branch=3, card=4, ach=5, wire=6, swift=7)
- **Available at prediction time:** Yes
- **Uses historical information:** No
- **Temporal leakage risk:** None
- **Customer leakage risk:** None
- **Encodes AML rules:** No
- **Redundant:** No
- **Useful for behavioral learning:** Yes (channel pattern)
- **Decision:** **ADD**

### 3.3 Rule-Like Features (to be removed)

#### is_large_amount
- **Data type:** binary
- **Meaning:** Whether amount >= 10,000
- **Source:** Threshold on amount
- **How calculated:** 1 if amount >= 10000, else 0
- **Encodes AML rules:** **YES** - encodes CTR threshold
- **Problem:** Model learns "large = suspicious" rather than behavioral context
- **Decision:** **REMOVE**

#### is_structuring_band
- **Data type:** binary
- **Meaning:** Whether amount in 8500-9999 range
- **Source:** Threshold on amount
- **How calculated:** 1 if 8500 <= amount <= 9999, else 0
- **Encodes AML rules:** **YES** - encodes structuring threshold
- **Problem:** Model learns "amount in band = suspicious" rather than sequence pattern
- **Decision:** **REMOVE**

#### structuring_indicators
- **Data type:** float
- **Meaning:** Computed structuring score
- **Source:** Computed from amount + same_day_count
- **How calculated:** (amount in 8000-9999) + (same_day_count >= 3)
- **Encodes AML rules:** **YES** - encodes structuring detection logic
- **Problem:** Model learns rule rather than detecting structuring behaviorally
- **Decision:** **REMOVE**

#### layering_indicators
- **Data type:** float
- **Meaning:** Computed layering score
- **Source:** Computed from rapid_transfer_count + same_recipient_count + amount
- **How calculated:** (rapid_transfer_count >= 2) + (same_recipient_count >= 2) + (transfer >= 5000)
- **Encodes AML rules:** **YES** - encodes layering detection logic
- **Problem:** Model learns rule rather than detecting layering behaviorally
- **Decision:** **REMOVE**

---

## 4. LEAKAGE AUDIT

### 4.1 Label Leakage
**Status:** **PASS**

- Ground truth labels are in separate file (`ml_stage3_ground_truth.json`)
- Feature file (`ml_stage3_dataset.csv`) contains no label information
- No `ground_truth_label`, `risk_score`, `risk_level` in feature file
- No AML typologies in feature file
- No scenario information in feature file

### 4.2 Temporal Leakage
**Status:** **CONDITIONALLY PASS**

**Current state:**
- All historical features are computed from `historical_transactions` list in Stage 3 generator
- Generator computes features sequentially, building history as transactions are generated
- This is temporally safe **within the generator**

**Risk:**
- If training pipeline loads entire dataset and computes features globally, temporal leakage could occur
- Must ensure features are computed per-customer in chronological order
- Must ensure train/validation/test split respects temporal boundaries

**Mitigation required:**
- Training pipeline must compute features per-customer, not globally
- Must implement proper temporal splitting in Stage 5
- Must verify that no future transactions influence historical features

### 4.3 Customer Leakage
**Status:** **PASS**

- `sender_account` field present for customer-level splitting
- Features are computed per-customer from customer's own history
- No global statistics that could leak information across customers
- Customer-level splitting is supported

### 4.4 Future Information Leakage
**Status:** **PASS (with verification needed)**

- All historical features use past transactions only
- No features use future transaction information
- Sequence features (same_day_count, rapid_transfer_count) use only earlier transactions
- **Verification needed:** Ensure training pipeline respects this

---

## 5. RULE-DEPENDENCE AUDIT

### 5.1 Direct Rule Dependence
**Status:** **NONE in Stage 3 dataset**

- Stage 3 dataset does not include any rule-like features
- No `is_large_amount`, `is_structuring_band`, `structuring_indicators`, `layering_indicators`
- Labels are generated from AML typologies, not rule engine
- No use of `aml_rules.py` in dataset generation

### 5.2 Indirect Rule Dependence
**Status:** **NONE in Stage 3 dataset**

- No features derived from rule engine outputs
- No features derived from `risk_score` or `risk_level`
- No features derived from rule-based thresholds
- All features are behavioral or contextual

### 5.3 Existing ai_core.py Rule Dependence
**Status:** **PRESENT (to be removed)**

- `is_large_amount` - encodes CTR threshold
- `is_structuring_band` - encodes structuring threshold
- `structuring_indicators` - encodes structuring detection logic
- `layering_indicators` - encodes layering detection logic

These must be removed from the new feature extraction function.

---

## 6. FEATURES TO KEEP

From Stage 3 dataset (14 features):

1. **amount** - Raw transaction amount
2. **sender_avg_amount** - Customer's average amount (baseline)
3. **sender_max_amount** - Customer's maximum amount (baseline)
4. **sender_tx_count** - Customer's total transaction count
5. **amount_to_sender_avg** - Deviation from average (behavioral)
6. **amount_to_sender_max** - Deviation from maximum (behavioral)
7. **sender_tx_count_24h** - Recent velocity (24h)
8. **sender_volume_24h** - Recent volume (24h)
9. **amount_to_sender_volume_24h** - Proportion of recent activity
10. **is_new_recipient** - Recipient network change
11. **same_day_count** - Daily velocity
12. **same_day_total** - Daily volume
13. **same_recipient_count** - Recipient concentration
14. **rapid_transfer_count** - Layering indicator (behavioral, not rule-based)

From derived features (7 features):

15. **hour** - Temporal pattern
16. **is_deposit** - Transaction type (one-hot)
17. **is_withdraw** - Transaction type (one-hot)
18. **is_transfer** - Transaction type (one-hot)
19. **is_self_transfer** - Self-transfer pattern
20. **is_off_hours** - Temporal anomaly
21. **channel_encoded** - Channel pattern

**Total: 21 features**

---

## 7. FEATURES TO REMOVE

From existing ai_core.py (4 features):

1. **is_large_amount** - Encodes CTR threshold rule
2. **is_structuring_band** - Encodes structuring threshold rule
3. **structuring_indicators** - Encodes structuring detection logic
4. **layering_indicators** - Encodes layering detection logic

**Reason:** These features directly encode AML rules, causing the model to learn rule thresholds rather than independent behavioral patterns.

---

## 8. FEATURES TO REDESIGN

None required. All Stage 3 features are well-designed and behavioral. Missing derived features can be added without redesign.

---

### 9. New Proposed Behavioral Features (13 total)

### 9.1 Customer Behavioral Features

#### amount_std_dev
- **Meaning:** Standard deviation of customer's transaction amounts
- **Source:** Historical aggregation
- **Usefulness:** Measures amount variability (high variability may indicate layering)
- **Feasibility:** Can be computed from historical_transactions
- **Decision:** **ADD**

#### amount_z_score
- **Meaning:** Z-score of current amount relative to customer's distribution
- **Source:** Computed from amount, sender_avg_amount, amount_std_dev
- **Usefulness:** Statistical measure of deviation from baseline
- **Feasibility:** Can be computed if amount_std_dev is available
- **Decision:** **ADD** (dependent on amount_std_dev)

#### tx_frequency_7d
- **Meaning:** Number of transactions in last 7 days
- **Source:** Historical aggregation (7d window)
- **Usefulness:** Extended velocity window (complements 24h)
- **Feasibility:** Can be computed from historical_transactions
- **Decision:** **ADD**

#### tx_frequency_30d
- **Meaning:** Number of transactions in last 30 days
- **Source:** Historical aggregation (30d window)
- **Usefulness:** Extended velocity window (complements 24h, 7d)
- **Feasibility:** Can be computed from historical_transactions
- **Decision:** **ADD**

### 9.2 Temporal Features

#### day_of_week
- **Meaning:** Day of week (0-6, Monday=0)
- **Source:** Derived from timestamp
- **Usefulness:** Temporal pattern (weekend vs weekday)
- **Feasibility:** Can be derived from timestamp
- **Decision:** **ADD**

#### is_weekend
- **Meaning:** Whether transaction occurred on weekend
- **Source:** Derived from day_of_week
- **Usefulness:** Temporal anomaly
- **Feasibility:** Can be derived from day_of_week
- **Decision:** **ADD**

#### time_since_last_tx
- **Meaning:** Time (in hours) since previous transaction
- **Source:** Computed from timestamps
- **Usefulness:** Temporal gap analysis (unusual gaps may indicate behavioral change)
- **Feasibility:** Can be computed from historical_transactions
- **Decision:** **ADD**

### 9.3 Recipient/Network Features

#### unique_recipients_24h
- **Meaning:** Number of unique recipients in last 24 hours
- **Source:** Historical aggregation (24h window)
- **Usefulness:** Recipient diversity (high diversity may indicate funneling)
- **Feasibility:** Can be computed from historical_transactions
- **Decision:** **ADD**

#### unique_recipients_7d
- **Meaning:** Number of unique recipients in last 7 days
- **Source:** Historical aggregation (7d window)
- **Usefulness:** Extended recipient diversity window
- **Feasibility:** Can be computed from historical_transactions
- **Decision:** **ADD**

#### recipient_concentration
- **Meaning:** Concentration of transactions to top recipient (0-1)
- **Source:** Computed from recipient distribution
- **Usefulness:** High concentration may indicate focused activity
- **Feasibility:** Can be computed from historical_transactions
- **Decision:** **ADD**

#### new_recipient_ratio_7d
- **Meaning:** Ratio of new recipients in last 7 days
- **Source:** Computed from recipient history
- **Usefulness:** Sudden recipient network expansion
- **Feasibility:** Can be computed from historical_transactions
- **Decision:** **ADD**

### 9.4 Behavioral Change Features

#### amount_change_vs_avg_7d
- **Meaning:** Difference between current amount and 7-day average
- **Source:** Computed from amount and historical aggregation
- **Usefulness:** Detects sudden amount changes
- **Feasibility:** Can be computed from historical_transactions
- **Decision:** **ADD**

#### frequency_change_vs_avg_7d
- **Meaning:** Difference between current frequency and 7-day average
- **Source:** Computed from tx_frequency_7d and historical aggregation
- **Usefulness:** Detects sudden frequency changes
- **Feasibility:** Can be computed from historical_transactions
- **Decision:** **ADD**

---

## 10. TEMPORAL-SAFETY ANALYSIS

### 10.1 Current Stage 3 Implementation
**Status:** **SAFE**

- Stage 3 generator computes features sequentially
- `historical_transactions` list is built incrementally
- Each transaction's features use only previously generated transactions
- This is temporally safe by design

### 10.2 Training Pipeline Requirements
**Status:** **TO BE IMPLEMENTED**

The training pipeline must:

1. **Load transactions per-customer in chronological order**
2. **Compute features incrementally** (not globally)
3. **Respect train/validation/test temporal boundaries**
4. **Ensure no future transactions influence historical features**
5. **Implement customer-level splitting** (all customer's transactions in same split)
6. **Implement temporal splitting** (by date, not random)

### 10.3 Risk Mitigation
- Add validation checks to ensure features are computed correctly
- Verify that historical features don't use future data
- Test with known edge cases (first transaction, last transaction)
- Document the feature computation order

---

## 11. CUSTOMER-LEVEL EVALUATION COMPATIBILITY

### 11.1 Current Support
**Status:** **FULLY SUPPORTED**

- `sender_account` field present in Stage 3 dataset
- `timestamp` field present in Stage 3 dataset
- Features are computed per-customer
- No global statistics that would prevent customer-level splitting

### 11.2 Implementation Requirements
The training pipeline must:

1. **Group transactions by customer** before splitting
2. **Split by customer** (not by transaction) to prevent leakage
3. **Maintain customer identity** throughout pipeline
4. **Compute features per-customer** (not globally)
5. **Support temporal splitting** within customer groups

### 11.3 Verification
- Add test to ensure same customer doesn't appear in multiple splits
- Add test to ensure temporal order is preserved
- Add test to verify features are computed correctly per-customer

---

## 12. FINAL PROPOSED FEATURE SPECIFICATION

### 12.1 Core Features (from Stage 3, 14 features)

1. amount (float)
2. sender_avg_amount (float)
3. sender_max_amount (float)
4. sender_tx_count (float)
5. amount_to_sender_avg (float)
6. amount_to_sender_max (float)
7. sender_tx_count_24h (float)
8. sender_volume_24h (float)
9. amount_to_sender_volume_24h (float)
10. is_new_recipient (float)
11. same_day_count (float)
12. same_day_total (float)
13. same_recipient_count (float)
14. rapid_transfer_count (float)

### 12.2 Derived Features (to be added, 7 features)

15. hour (int)
16. is_deposit (binary)
17. is_withdraw (binary)
18. is_transfer (binary)
19. is_self_transfer (binary)
20. is_off_hours (binary)
21. channel_encoded (int)

### 12.3 New Behavioral Features (to be added, 13 features)

22. amount_std_dev (float)
23. amount_z_score (float)
24. tx_frequency_7d (float)
25. tx_frequency_30d (float)
26. day_of_week (int)
27. is_weekend (binary)
28. time_since_last_tx (float)
29. unique_recipients_24h (float)
30. unique_recipients_7d (float)
31. recipient_concentration (float)
32. new_recipient_ratio_7d (float)
33. amount_change_vs_avg_7d (float)
34. frequency_change_vs_avg_7d (float)

**Total: 34 features**

### 12.4 Feature Categories

| Category | Count | Features |
|----------|-------|----------|
| Transaction-level | 5 | amount, hour, day_of_week, is_weekend, time_since_last_tx |
| Transaction type | 4 | is_deposit, is_withdraw, is_transfer, is_self_transfer |
| Channel | 1 | channel_encoded |
| Historical baseline | 3 | sender_avg_amount, sender_max_amount, sender_tx_count |
| Amount ratios | 3 | amount_to_sender_avg, amount_to_sender_max, amount_z_score |
| Velocity (24h) | 2 | sender_tx_count_24h, sender_volume_24h |
| Velocity (extended) | 2 | tx_frequency_7d, tx_frequency_30d |
| Volume ratios | 1 | amount_to_sender_volume_24h |
| Sequence (same day) | 2 | same_day_count, same_day_total |
| Sequence (rapid) | 1 | rapid_transfer_count |
| Recipient (individual) | 1 | is_new_recipient |
| Recipient (concentration) | 3 | same_recipient_count, unique_recipients_24h, unique_recipients_7d |
| Recipient (diversity) | 2 | recipient_concentration, new_recipient_ratio_7d |
| Behavioral change | 2 | amount_change_vs_avg_7d, frequency_change_vs_avg_7d |
| Amount variability | 1 | amount_std_dev |
| Temporal anomaly | 1 | is_off_hours |
| **TOTAL** | **34** | **All categories** |

---

## 13. REMAINING LIMITATIONS

### 13.1 Geographic Features
**Status:** **NOT AVAILABLE**

- Stage 3 dataset does not include destination_country in feature file
- Ground truth includes high_risk_jurisdiction typology
- **Cannot add geographic features** without modifying Stage 3 generator
- **Decision:** Defer geographic features to future Stage 3 enhancement

### 13.2 Incoming/Outgoing Ratio
**Status:** **NOT AVAILABLE**

- Stage 3 dataset only tracks outgoing transactions (sender_account)
- Does not track incoming transactions to receiver_account
- **Cannot compute incoming/outgoing ratio** without modifying Stage 3 generator
- **Decision:** Defer to future Stage 3 enhancement

### 13.3 Wealth Segment
**Status:** **NOT IN FEATURES**

- Stage 3 generator includes wealth_segment in customer profile
- Not exported to feature file
- **Could be added** as a customer-level feature
- **Decision:** Consider adding if customer-level features are supported

### 13.4 PEP Flag
**Status:** **NOT AVAILABLE**

- Stage 3 generator does not include PEP (Politically Exposed Person) information
- **Cannot add PEP flag** without modifying Stage 3 generator
- **Decision:** Defer to future Stage 3 enhancement

### 13.5 Global Network Features
**Status:** **NOT AVAILABLE**

- Stage 3 dataset is per-customer, not global network
- Cannot compute network-level features (centrality, betweenness, etc.)
- **Decision:** Defer to future enhancement (would require different data structure)

---

## 14. EXACT FILES/CODE THAT WOULD NEED MODIFICATION

### 14.1 Files to Modify

1. **ai_core.py**
   - Create new function `transaction_features_stage3()` to replace `transaction_features()`
   - Remove rule-like features (is_large_amount, is_structuring_band, structuring_indicators, layering_indicators)
   - Add derived features (hour, is_deposit, is_withdraw, is_transfer, is_self_transfer, is_off_hours, channel_encoded)
   - Add new behavioral features (amount_std_dev, amount_z_score, tx_frequency_7d, tx_frequency_30d, day_of_week, is_weekend, time_since_last_tx, unique_recipients_24h, unique_recipients_7d, recipient_concentration, new_recipient_ratio_7d, amount_change_vs_avg_7d, frequency_change_vs_avg_7d)

2. **Stage 5 training pipeline**
   - Implement per-customer feature computation
   - Implement customer-level splitting
   - Implement temporal splitting
   - Ensure temporal safety (no future data leakage)

3. **Stage 3 generator** (optional, for future enhancement)
   - Add destination_country to feature file (for geographic features)
   - Add wealth_segment to feature file (for customer-level features)
   - Track incoming transactions (for incoming/outgoing ratio)

### 14.2 Files to Create

1. **ml_stage4_feature_extraction.py**
   - New feature extraction function compatible with Stage 3 dataset
   - Implements all 32 proposed features
   - Includes validation checks for temporal safety

2. **ml_stage4_feature_validation.py**
   - Validation tests for feature computation
   - Tests for temporal safety
   - Tests for customer-level compatibility

### 14.3 Files to Keep Unchanged

1. **ml_stage3_dataset.csv** - Do not modify
2. **ml_stage3_ground_truth.json** - Do not modify
3. **ml_stage3_metadata.json** - Do not modify
4. **ml_stage3_generator.py** - Keep as-is (unless adding geographic features in future)

---

## 15. RECOMMENDED NEXT STEPS

### 15.1 Immediate (Stage 4 completion)
1. Create new feature extraction function compatible with Stage 3 dataset
2. Implement 21 core + derived features
3. Implement 13 new behavioral features
4. Implement validation checks for temporal safety
5. Test feature extraction on Stage 3 dataset

### 15.2 Short-term (Stage 5)
1. Implement per-customer feature computation in training pipeline
2. Implement customer-level splitting
3. Implement temporal splitting
4. Ensure temporal safety throughout pipeline

### 15.3 Medium-term (Stage 6-7)
1. Evaluate feature importance for all 34 features
2. Perform feature selection if needed
3. Optimize model with new feature set

### 15.4 Long-term (Future enhancement)
1. Modify Stage 3 generator to add geographic features
2. Modify Stage 3 generator to track incoming transactions
3. Add wealth segment as customer-level feature
4. Consider global network features

---

## 16. SUMMARY

### 16.1 Changes Made
- None (Stage 4 is audit and design only per instructions)

### 16.2 Changes Remaining
- Create new feature extraction function (34 features)
- Modify training pipeline for customer-level and temporal splitting
- Remove rule-like features from existing implementation

### 16.3 Unchanged
- Stage 3 dataset (ml_stage3_dataset.csv, ml_stage3_ground_truth.json, ml_stage3_metadata.json)
- Stage 3 generator (ml_stage3_generator.py)
- Stage 1-3 reports and findings

### 16.4 Final Proposed Feature Specification
- **34 features total**
- **14 core features** from Stage 3 dataset
- **7 derived features** (hour, transaction types, self-transfer, off-hours, channel)
- **13 new behavioral features** (amount variability, extended velocity, temporal, recipient diversity, behavioral change)
- **0 rule-like features** (all removed)

---

**STAGE 4 COMPLETE — WAITING FOR APPROVAL.**
