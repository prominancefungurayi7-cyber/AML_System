# STAGE 11 IMPLEMENTATION PLAN

**Date:** 2026-09-02  
**Purpose:** Detailed implementation plan for generator repair, ground-truth implementation, and dataset validation

---

## PART 1: IMPLEMENTATION PLAN BEFORE CODING

### 1.1 Exact Generator Functions That Need Modification

**File:** `ml_stage3_generator.py`

**Function 1: `_select_scenario()` (lines 825-868)**
- **Current behavior:** Uses `random.random()` to select target class, then selects scenario based on target class
- **Problem:** Random mechanism produces 0% super_suspicious transactions
- **Required change:** Make scenario selection deterministic based on customer profile parameters

**Function 2: `_determine_ground_truth()` (lines 587-625)**
- **Current behavior:** Maps scenarios to labels, but also uses customer-level typologies
- **Problem:** Customer-level typologies override scenario-based labeling
- **Required change:** Make scenario_id the primary ground-truth determinant, remove customer-level override

### 1.2 Exact Scenario-Selection Mechanism

**Current mechanism:**
```python
rand = random.random()
if rand < normal_prob:
    target_class = "normal"
elif rand < suspicious_prob:
    target_class = "suspicious"
else:
    target_class = "super_suspicious"

# Then select scenario based on target_class
```

**Problem:** This produces 0% super_suspicious because:
- Only 2% of customers have high-risk profiles
- Normal customers rarely get super_suspicious target class (10% probability)
- High-risk customers get severe scenarios, but there are too few of them

**Proposed mechanism:**
- Remove random.random() from scenario selection
- Use customer profile parameters to determine scenario selection
- For high-risk customers: always select from suspicious/severe scenarios
- For normal customers: select from normal scenarios with occasional suspicious scenarios
- Ensure severe scenarios have minimum frequency (≥5%)

### 1.3 Existing Scenario Definitions

**Normal scenarios:**
- normal
- legitimate_high_value
- cash_deposit
- cash_withdrawal
- new_recipient

**Suspicious scenarios:**
- structuring
- layering
- funnel
- rapid_movement
- high_risk_country
- behavioral_change

**Severe scenarios:**
- severe_structuring
- severe_layering
- severe_funnel
- multiple_typologies

### 1.4 Existing Severity Classifications

**Customer-level:**
- typology_severity: none, mild, moderate, severe
- Only 4 customers (2%) have typology_severity != "none"

**Scenario-level:**
- Implicit in scenario names (severe_* vs normal)
- Currently mapped in `_determine_ground_truth()`

### 1.5 Scenario-to-Label Mapping

**Current mapping:**
- Customer with severe typology → SUPER_SUSPICIOUS
- Customer with moderate typology → SUSPICIOUS
- severe_structuring, severe_layering, severe_funnel, multiple_typologies → SUPER_SUSPICIOUS
- structuring, layering, funnel, rapid_movement, high_risk_country, behavioral_change → SUSPICIOUS
- Everything else → NORMAL

**Proposed mapping (scenario-based only):**
- normal, legitimate_high_value, cash_deposit, cash_withdrawal, new_recipient → NORMAL
- structuring, layering, funnel, rapid_movement, high_risk_country, behavioral_change → SUSPICIOUS
- severe_structuring, severe_layering, severe_funnel, multiple_typologies → SUPER_SUSPICIOUS

**Rationale:** Remove customer-level override, make scenario_id the primary determinant.

### 1.6 Exact Cause of 0% Super-Suspicious Problem

**Root cause:** The random.random() mechanism in `_select_scenario()` combined with:
- Only 2% of customers have high-risk profiles
- Default class_distribution: normal=70%, suspicious=20%, super_suspicious=10%
- High-risk customers get severe scenarios, but there are too few of them
- Normal customers with super_suspicious target class get severe scenarios, but this is rare (10% of 98% = 9.8% of customers, but the random selection doesn't consistently produce this)

**Evidence:** Stage 10 audit found 0% super_suspicious transactions despite severe scenarios being defined.

### 1.7 Exact Cause of new_recipient_ratio_7d Bug

**Location:** `ml_stage5_feature_extraction.py` lines 327-334

**Current code:**
```python
new_recipient_ratio_7d = 0.0
if tx_7d:
    new_recipients = sum(
        1 for tx in tx_7d
        if tx["receiver_account"] not in self.customer_recipients[sender_account]
    )
    new_recipient_ratio_7d = new_recipients / len(tx_7d)
```

**Problem:** `self.customer_recipients[sender_account]` is updated AFTER feature extraction (line 380), so it's always empty when computing the feature. This means all recipients are considered "new", but the logic checks if they're in the set, which is empty, so it counts them as new. However, the set is populated after extraction, so the feature is always computed with an empty set.

**Fix:** Track recipients from historical transactions only, not from the entire dataset. Use the historical transactions to determine if a recipient is "new" (not seen in the past 7 days).

### 1.8 Which Existing Logic Will Remain Unchanged

**Unchanged:**
- Customer profile generation (CustomerProfileGenerator)
- Transaction generation (TransactionGenerator.generate_transaction)
- Historical feature computation (TransactionGenerator._compute_historical_features)
- All 34 feature definitions (approved specification)
- Temporal safety rules (no future data)
- Dataset scale (10,000 transactions, 200 customers, 50 transactions/customer)

**Changed:**
- Scenario selection mechanism (AMLDatasetGenerator._select_scenario)
- Ground truth determination (TransactionGenerator._determine_ground_truth)
- new_recipient_ratio_7d calculation (FeatureExtractor.compute_behavioral_features)

### 1.9 How Temporal Causality Will Be Preserved

**Preservation:**
- Historical features use only transactions with timestamp < current transaction timestamp
- Rolling windows (24h, 7d, 30d) are calculated from current timestamp backwards
- Current transaction is NOT included in historical calculations
- Scenario selection is based on customer profile (available before transaction generation)
- Ground truth is assigned at generation time (before feature extraction)

**Verification:**
- The generator already has temporal safety built in
- Stage 5 feature extraction already has temporal safety built in
- No changes will be made to temporal safety logic

---

## PART 2: GROUND-TRUTH ARCHITECTURE

### 2.1 Scenario-Based Labeling

**Rule:** scenario_id determines label

**Mapping:**
```python
SCENARIO_TO_LABEL = {
    # Normal scenarios
    "normal": GroundTruthLabel.NORMAL,
    "legitimate_high_value": GroundTruthLabel.NORMAL,
    "cash_deposit": GroundTruthLabel.NORMAL,
    "cash_withdrawal": GroundTruthLabel.NORMAL,
    "new_recipient": GroundTruthLabel.NORMAL,
    
    # Suspicious scenarios
    "structuring": GroundTruthLabel.SUSPICIOUS,
    "layering": GroundTruthLabel.SUSPICIOUS,
    "funnel": GroundTruthLabel.SUSPICIOUS,
    "rapid_movement": GroundTruthLabel.SUSPICIOUS,
    "high_risk_country": GroundTruthLabel.SUSPICIOUS,
    "behavioral_change": GroundTruthLabel.SUSPICIOUS,
    
    # Severe scenarios
    "severe_structuring": GroundTruthLabel.SUPER_SUSPICIOUS,
    "severe_layering": GroundTruthLabel.SUPER_SUSPICIOUS,
    "severe_funnel": GroundTruthLabel.SUPER_SUSPICIOUS,
    "multiple_typologies": GroundTruthLabel.SUPER_SUSPICIOUS,
}
```

### 2.2 Provenance Tracking

Each transaction will have:
- scenario_id
- scenario_category (normal/suspicious/severe)
- ground_truth_label
- customer_profile_type
- customer_aml_typologies (if any)
- customer_typology_severity (if any)

### 2.3 What Will NOT Determine Labels

- Amount
- Z-score
- Velocity features
- Frequency features
- Recipient features
- Timing features
- Feature thresholds
- Model predictions
- Model feature importance

---

## PART 3: RANDOMNESS POLICY

### 3.1 Acceptable Randomness

**Acceptable:**
- Random selection of scenario within a category (e.g., which suspicious scenario)
- Random variation in transaction amounts (within profile constraints)
- Random variation in timestamps (within profile constraints)

**Not acceptable:**
- Random selection of target class (normal/suspicious/super_suspicious)
- Random assignment of labels independent of scenario
- Random severity changes without observable scenario explanation

### 3.2 Proposed Deterministic Mechanism

**Scenario selection based on customer profile:**
- High-risk customers (with aml_typologies): always select from suspicious/severe scenarios
- Normal customers: select from normal scenarios with occasional suspicious scenarios (10-20%)
- Ensure minimum frequency of severe scenarios (≥5%)

**Rationale:** This preserves behavioral realism while ensuring adequate class balance.

---

## PART 4: FIX SUPER-SUSPICIOUS GENERATION

### 4.1 Root Cause

The random.random() mechanism produces 0% super_suspicious because:
- Only 2% of customers have high-risk profiles
- Normal customers rarely get super_suspicious target class

### 4.2 Proposed Fix

**Modify `_select_scenario()`:**
- Remove random.random() for target class selection
- Use customer profile to determine scenario category
- For high-risk customers: 70% suspicious, 30% severe
- For normal customers: 85% normal, 15% suspicious
- Ensure severe scenarios have minimum 5% frequency

### 4.3 Target Distribution

- Normal: ~70%
- Suspicious: ~20-25%
- Super-suspicious: ~5-10%

---

## PART 5: FIX new_recipient_ratio_7d

### 5.1 Root Cause

`self.customer_recipients[sender_account]` is updated AFTER feature extraction, so it's always empty when computing the feature.

### 5.2 Proposed Fix

**Modify `compute_behavioral_features()`:**
- Track recipients from historical transactions only
- Use historical transactions to determine if a recipient is "new" (not seen in past 7 days)
- Update the tracking logic to use historical data, not the entire dataset

### 5.3 Implementation

```python
# Track recipients from historical transactions
historical_recipients_7d = set(tx["receiver_account"] for tx in tx_7d)
historical_recipients_all = set(tx["receiver_account"] for tx in past_transactions)

# New recipient = not seen in historical transactions
new_recipients = sum(
    1 for tx in tx_7d
    if tx["receiver_account"] not in historical_recipients_all
)
new_recipient_ratio_7d = new_recipients / len(tx_7d) if tx_7d else 0.0
```

---

## PART 6: SELF-TRANSFER FEATURE

### 6.1 Investigation

**Current status:** is_self_transfer = 0 for all transactions

**Root cause:** Generator's `_select_recipient()` function does not include a self-transfer option

### 6.2 Decision

**Do NOT artificially manufacture self-transfers.**

**Rationale:**
- Self-transfers are not a core AML typology
- The generator does not have self-transfer scenarios defined
- Adding self-transfers would require defining new scenarios and behavioral logic
- This is beyond the scope of Stage 11

**Documentation:** The feature will remain constant. This is a known limitation of the current generator.

---

## PART 7: DATASET REGENERATION

### 7.1 Scale

- 10,000 transactions
- 200 customers
- 50 transactions/customer

### 7.2 Naming

- ml_stage11_dataset.csv (new)
- ml_stage11_ground_truth.json (new)
- ml_stage11_metadata.json (new)

### 7.3 Preservation

Original Stage 3 artifacts will be preserved:
- ml_stage3_dataset.csv
- ml_stage3_ground_truth.json
- ml_stage3_metadata.json

---

## PART 8: FEATURE EXTRACTION

### 8.1 Specification

Use the SAME approved 34-feature specification from Stage 5.

### 8.2 Changes

Only permitted changes:
- Fix new_recipient_ratio_7d calculation bug
- Any additional genuine implementation errors discovered

### 8.3 Naming

- ml_stage11_features.csv (new)

---

## PART 9: DATASET VALIDATION

### 9.1 Validation Checks

- Ground truth derived from scenario_id
- Class distribution (≥3% minimum preferred)
- Temporal integrity (no future data)
- Feature integrity (no constant/near-constant except is_self_transfer)
- Generator behavioral coverage (all scenarios occur)
- Feature-label signal (Cohen's d, mutual information)
- Circularity audit (labels from scenarios, not features)
- Label noise analysis

### 9.2 Acceptance Criteria

- Each class ≥3% (minimum viable)
- Preferably each minority class ≥5%
- No class trivially dominates
- Distribution arises naturally from scenario generation

---

## IMPLEMENTATION ORDER

1. Modify ml_stage3_generator.py
2. Modify ml_stage5_feature_extraction.py
3. Create ml_stage11_generator_repair.py
4. Generate new dataset
5. Extract features
6. Create ml_stage11_validation.py
7. Run validation
8. Create ml_stage11_report.md
9. Final gate (PASS/FAIL)

---

**PLAN VERIFIED AGAINST CODE:** YES
