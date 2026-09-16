# STAGE 5: 34-FEATURE ENGINEERING PIPELINE IMPLEMENTATION REPORT

**Date:** 2026-09-01  
**Purpose:** Implement and validate the approved 34-feature engineering pipeline

---

## EXECUTIVE SUMMARY

The approved 34-feature engineering pipeline has been successfully implemented and validated. All 34 features from the Stage 4 specification are now extracted from the Stage 3 dataset with temporal safety guarantees.

**Key achievements:**
- **34 features successfully implemented** (14 core + 7 derived + 13 behavioral)
- **0 rule-like features** (all rejected features removed)
- **0 label-derived features** (no ground truth used in feature calculation)
- **Temporal safety ensured** (no future data leakage)
- **All validation checks passed** (11/11)
- **Stage 3 files unchanged** (dataset and labels preserved)

---

## 1. FILES CREATED/MODIFIED

### 1.1 Files Created
1. **ml_stage5_feature_extraction.py** - Main feature extraction implementation
2. **ml_stage5_features.csv** - Output feature matrix (10,000 transactions × 34 features)
3. **ml_stage5_validation.py** - Validation script
4. **ml_stage5_report.md** - This report

### 1.2 Files Modified
None

### 1.3 Files Preserved (Unchanged)
- ml_stage3_dataset.csv
- ml_stage3_ground_truth.json
- ml_stage3_metadata.json
- ml_stage3_generator.py

---

## 2. FEATURE ENGINEERING IMPLEMENTATION

### 2.1 Architecture

The implementation uses a `FeatureExtractor` class that:
- Maintains per-customer transaction history
- Computes features incrementally in chronological order
- Ensures temporal safety by using only past transactions
- Handles edge cases (first transaction, insufficient history) with safe defaults

### 2.2 Temporal Safety Mechanism

**Implementation:**
```python
def get_historical_transactions(self, sender_account: str, current_timestamp: datetime) -> List[Dict]:
    """Get all transactions for sender before current timestamp (temporal safety)."""
    history = self.customer_history[sender_account]
    # Filter to only transactions before current timestamp
    past_transactions = [
        tx for tx in history 
        if self.parse_timestamp(tx["timestamp"]) < current_timestamp
    ]
    return past_transactions
```

**Key points:**
- Transactions are sorted by timestamp before processing
- Historical features use only transactions with timestamp < current timestamp
- Current transaction is NOT included in historical calculations
- Rolling windows (24h, 7d, 30d) are calculated from current timestamp backwards

### 2.3 Safe Default Values

For features that cannot be calculated due to insufficient history (e.g., first transaction):

```python
SAFE_DEFAULTS = {
    "sender_avg_amount": 0.0,
    "sender_max_amount": 0.0,
    "sender_tx_count": 0.0,
    "amount_to_sender_avg": 1.0,
    "amount_to_sender_max": 1.0,
    "sender_tx_count_24h": 0.0,
    "sender_volume_24h": 0.0,
    "amount_to_sender_volume_24h": 1.0,
    "is_new_recipient": 1.0,
    "same_day_count": 0.0,
    "same_day_total": 0.0,
    "same_recipient_count": 0.0,
    "rapid_transfer_count": 0.0,
    "amount_std_dev": 0.0,
    "amount_z_score": 0.0,
    "tx_frequency_7d": 0.0,
    "tx_frequency_30d": 0.0,
    "time_since_last_tx": 0.0,
    "unique_recipients_24h": 0.0,
    "unique_recipients_7d": 0.0,
    "recipient_concentration": 0.0,
    "new_recipient_ratio_7d": 0.0,
    "amount_change_vs_avg_7d": 0.0,
    "frequency_change_vs_avg_7d": 0.0,
}
```

---

## 3. FEATURE DEFINITIONS AND CALCULATIONS

### 3.1 Core Features (14)

| Feature | Type | Calculation |
|---------|------|-------------|
| amount | float | Direct from transaction |
| sender_avg_amount | float | Mean of past transaction amounts |
| sender_max_amount | float | Max of past transaction amounts |
| sender_tx_count | float | Count of past transactions |
| amount_to_sender_avg | float | amount / max(sender_avg_amount, 1.0) |
| amount_to_sender_max | float | amount / max(sender_max_amount, 1.0) |
| sender_tx_count_24h | float | Count of transactions in 24h window before current |
| sender_volume_24h | float | Sum of amounts in 24h window before current |
| amount_to_sender_volume_24h | float | amount / max(sender_volume_24h, 1.0) |
| is_new_recipient | float | 1.0 if recipient not in customer's history, else 0.0 |
| same_day_count | float | Count of transactions on same date before current |
| same_day_total | float | Sum of amounts on same date before current |
| same_recipient_count | float | Count of transactions to same recipient in 24h |
| rapid_transfer_count | float | Count of transactions within 10 minutes before current |

### 3.2 Derived Features (7)

| Feature | Type | Calculation |
|---------|------|-------------|
| hour | int | Hour (0-23) extracted from timestamp |
| is_deposit | binary | 1 if transaction_type == "deposit", else 0 |
| is_withdraw | binary | 1 if transaction_type == "withdraw", else 0 |
| is_transfer | binary | 1 if transaction_type == "transfer", else 0 |
| is_self_transfer | binary | 1 if sender_account == receiver_account, else 0 |
| is_off_hours | binary | 1 if hour < 5 or hour >= 23, else 0 |
| channel_encoded | int | Mapping: online=0, mobile=1, atm=2, branch=3, card=4, ach=5, wire=6, swift=7 |

### 3.3 New Behavioral Features (13)

| Feature | Type | Calculation |
|---------|------|-------------|
| amount_std_dev | float | Standard deviation of past transaction amounts (0 if <2 transactions) |
| amount_z_score | float | (amount - sender_avg_amount) / max(amount_std_dev, 1.0) |
| tx_frequency_7d | float | Count of transactions in 7-day rolling window before current |
| tx_frequency_30d | float | Count of transactions in 30-day rolling window before current |
| day_of_week | int | Day of week (0=Monday, 6=Sunday) from timestamp |
| is_weekend | binary | 1 if day_of_week >= 5, else 0 |
| time_since_last_tx | float | Hours since previous transaction (0 if first) |
| unique_recipients_24h | float | Count of unique recipients in 24h window |
| unique_recipients_7d | float | Count of unique recipients in 7-day window |
| recipient_concentration | float | (count to top recipient in 7d) / (total transactions in 7d) |
| new_recipient_ratio_7d | float | (new recipients in 7d) / (total transactions in 7d) |
| amount_change_vs_avg_7d | float | current_amount - (7-day average amount) |
| frequency_change_vs_avg_7d | float | (7-day daily frequency) - (30-day daily frequency) |

### 3.4 Ambiguous Feature Definitions - Resolutions

**Rolling windows (7d, 30d):**
- Defined as rolling windows based on timestamps
- Window is calculated from current timestamp backwards
- Current transaction is NOT included in the window
- Example: For a transaction on 2026-09-01, the 7d window is 2026-08-25 to 2026-09-01 (exclusive of current)

**recipient_concentration denominator:**
- Denominator is total number of transactions in the 7-day window
- Numerator is count of transactions to the most frequent recipient in that window
- Range: 0.0 (no concentration) to 1.0 (all transactions to same recipient)

**new_recipient_ratio_7d:**
- New recipient = recipient not seen in customer's entire history before the 7d window
- Ratio = (count of new recipients in 7d) / (total transactions in 7d)
- Range: 0.0 (no new recipients) to 1.0 (all recipients are new)

**amount_change_vs_avg_7d reference:**
- Reference = average amount of transactions in 7-day window
- If 7d window is empty, uses sender_avg_amount (all-time average)
- Result = current_amount - reference (positive = higher than average)

**frequency_change_vs_avg_7d reference:**
- Reference = average daily frequency over 30-day window
- Current = average daily frequency over 7-day window
- Result = current - reference (positive = frequency increased)

**amount_z_score when std_dev = 0:**
- If standard deviation is 0 (all amounts identical), z-score = 0.0
- This occurs when customer has only 1 transaction or all transactions have same amount

**time_since_last_tx for first transaction:**
- Value = 0.0 hours (indicates no previous transaction)

**is_off_hours definition:**
- Off-hours = hour < 5 (midnight to 5 AM) OR hour >= 23 (11 PM to midnight)
- Business hours = 5 AM to 11 PM (inclusive)

---

## 4. VALIDATION RESULTS

### 4.1 Validation Checks

| Check | Status | Details |
|-------|--------|---------|
| Transaction count | PASS | 10,000 transactions (expected 10,000) |
| Feature count | PASS | 34 features (expected 34) |
| Feature names | PASS | All expected features present, no extra features |
| Rule-like features | PASS | 0 rule-like features present |
| Label-derived features | PASS | 0 label-derived features present |
| Feature data types | PASS | All feature data types valid |
| NaN values | PASS | 0 NaN/empty values found |
| Infinite values | PASS | 0 infinite values found |
| Binary values | PASS | All binary features contain only 0/1 |
| Channel encoding | PASS | Channel encoding values valid (0-7) |
| Stage 3 files | PASS | All Stage 3 files exist and unchanged |

**Total: 11/11 checks passed**

### 4.2 Feature Statistics

Sample statistics (first 1,000 transactions):

| Feature | Min | Max | Mean |
|---------|-----|-----|------|
| amount | 10.00 | 1,003,153.84 | 24,271.93 |
| sender_avg_amount | 0.00 | 758,094.33 | 18,614.58 |
| hour | 0.00 | 23.00 | 12.10 |
| tx_frequency_7d | 0.00 | 13.00 | 2.49 |

### 4.3 Channel Encoding Distribution

| Channel | Encoding | Count |
|---------|----------|-------|
| online | 0 | 1,895 |
| mobile | 1 | 1,262 |
| atm | 2 | 990 |
| branch | 3 | 1,127 |
| card | 4 | 1,257 |
| ach | 5 | 1,100 |
| wire | 6 | 1,479 |
| swift | 7 | 890 |

---

## 5. LEAKAGE VALIDATION

### 5.1 Rule-Like Feature Removal

**Confirmed: 0 rule-like features**

The following rejected features are NOT present:
- is_large_amount ❌
- is_structuring_band ❌
- structuring_indicators ❌
- layering_indicators ❌

### 5.2 Label-Derived Feature Removal

**Confirmed: 0 label-derived features**

The following label fields are NOT present:
- ground_truth_label ❌
- risk_score ❌
- risk_level ❌
- aml_typologies ❌
- scenario_id ❌

### 5.3 Future Data Leakage Prevention

**Confirmed: Temporal-safe implementation**

- Transactions sorted by timestamp before processing
- Historical features use only transactions with timestamp < current timestamp
- Rolling windows calculated from current timestamp backwards
- Current transaction NOT included in historical calculations
- Customer history updated AFTER feature computation

### 5.4 Deterministic Calculations

**Confirmed: All calculations are deterministic**

- No random operations in feature computation
- Safe defaults for edge cases are fixed values
- Re-running the pipeline produces identical results

---

## 6. ASSUMPTIONS MADE

### 6.1 For Ambiguous Feature Definitions

1. **Rolling windows:** Defined as timestamp-based rolling windows, not calendar days
2. **recipient_concentration:** Denominator is total transactions in 7d window, not all-time
3. **new_recipient_ratio_7d:** New = not seen in entire history before 7d window
4. **amount_z_score:** Returns 0.0 when standard deviation is 0
5. **time_since_last_tx:** Returns 0.0 for first transaction
6. **is_off_hours:** Defined as hour < 5 OR hour >= 23
7. **channel_encoded:** Uses fixed mapping (online=0 through swift=7)

### 6.2 For Edge Cases

1. **First transaction:** All historical features use safe defaults (0 or neutral)
2. **Insufficient history for std_dev:** Returns 0.0
3. **Empty rolling windows:** Uses all-time statistics as fallback
4. **Division by zero:** All ratios use max(denominator, 1.0) to prevent division by zero

---

## 7. ISSUES DISCOVERED

**No issues discovered.** All validation checks passed successfully.

---

## 8. EXACT 34-FEATURE LIST PRODUCED

1. amount
2. sender_avg_amount
3. sender_max_amount
4. sender_tx_count
5. amount_to_sender_avg
6. amount_to_sender_max
7. sender_tx_count_24h
8. sender_volume_24h
9. amount_to_sender_volume_24h
10. is_new_recipient
11. same_day_count
12. same_day_total
13. same_recipient_count
14. rapid_transfer_count
15. hour
16. is_deposit
17. is_withdraw
18. is_transfer
19. is_self_transfer
20. is_off_hours
21. channel_encoded
22. amount_std_dev
23. amount_z_score
24. tx_frequency_7d
25. tx_frequency_30d
26. day_of_week
27. is_weekend
28. time_since_last_tx
29. unique_recipients_24h
30. unique_recipients_7d
31. recipient_concentration
32. new_recipient_ratio_7d
33. amount_change_vs_avg_7d
34. frequency_change_vs_avg_7d

---

## 9. CONFIRMATION

### 9.1 Feature Count
- Expected ML feature count: **34**
- Actual ML feature count: **34** ✓

### 9.2 Rule-Like Features
- Rule-like features: **0** ✓

### 9.3 Label-Derived Features
- Label-derived features: **0** ✓

### 9.4 Future Data Leakage
- Future-data leakage: **Prevented by temporal-safe implementation** ✓

### 9.5 Stage 3 Files
- Stage 3 files unchanged: **Confirmed** ✓

---

## 10. DELIVERABLES

1. **ml_stage5_feature_extraction.py** - Feature extraction implementation
2. **ml_stage5_features.csv** - Feature matrix (10,000 × 34)
3. **ml_stage5_validation.py** - Validation script
4. **ml_stage5_report.md** - This report

---

## 11. TESTING RESULTS

All 10 required tests passed:

1. ✓ Exactly 10,000 transactions processed
2. ✓ Exactly 34 ML features generated per transaction
3. ✓ No Stage 3 source files modified
4. ✓ No rule-like features in ML vector
5. ✓ No labels used during feature calculation
6. ✓ No future transaction information leaks into historical features
7. ✓ Feature calculations are deterministic
8. ✓ Binary features contain only valid 0/1 values
9. ✓ No NaN or infinite values in final ML matrix
10. ✓ All feature data types valid

---

# STAGE 5 COMPLETE — WAITING FOR APPROVAL

**Status:** All 34 approved features successfully implemented and validated. Ready for Stage 6 (Model Training) upon approval.
