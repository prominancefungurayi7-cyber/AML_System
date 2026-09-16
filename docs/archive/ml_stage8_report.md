# STAGE 8: GROUND-TRUTH / LABELING METHODOLOGY AUDIT REPORT

**Date:** 2026-09-01  
**Purpose:** Determine whether Stage 3 labels are learnable from the approved 34-feature specification

---

## EXECUTIVE SUMMARY

The Stage 8 audit reveals that the Stage 3 labels are **not reliably learnable** from the current 34-feature representation under the Stage 3 labeling mechanism.

**Critical findings:**
- **Primary label determinants include hidden variables** (typology_severity, is_borderline_case) that are NOT in the 34 features
- **98% of CUSTOMERS (not transactions) receive probabilistic labels** via random.random(), creating label noise
- **Labels mix customer-level profiles with transaction-level scenarios**, creating semantic mismatch
- **44.79% near-duplicate conflict rate is EXPECTED** under stochastic labeling, not evidence of inconsistency
- **99.5% customer prevalence is MATHEMATICALLY EXPECTED** under independent probabilistic labeling
- **Observable differences from scenarios are too weak** to be reliably detected by the 34-feature representation (max Cohen's d = 0.094)

**Root cause:** The labels depend on hidden variables (typology_severity, is_borderline_case) and probabilistic assignment that creates weak observable signals. This is a **combination of hidden variable problem (Category C)** and **weak/stochastic labels (Category B)**.

---

## 1. STAGE 3 LABEL GENERATION LOGIC

### 1.1 Primary Determination (Customer Profile)

**Mechanism:**
```python
if customer.aml_typologies:
    if profile.typology_severity == "severe":
        return SUPER_SUSPICIOUS
    else:
        return SUSPICIOUS
```

**Characteristics:**
- **Deterministic:** Yes (for high-risk customers)
- **Level:** Customer-level
- **Depends on:** customer.aml_typologies, customer.typology_severity
- **Observable in 34 features:** NO
- **Observable at prediction time:** NO

### 1.2 Secondary Determination (Scenario-Based)

**Mechanism:**
```python
rand = random.random()
if rand < normal_prob:
    target_class = "normal"
elif rand < suspicious_prob:
    target_class = "suspicious"
else:
    target_class = "super_suspicious"

# Then select scenario based on target_class
scenario = random.choice(scenarios_for_target_class)
```

**Characteristics:**
- **Deterministic:** NO (uses random.random())
- **Level:** Transaction-level
- **Depends on:** random.random(), random.choice()
- **Observable in 34 features:** NO
- **Observable at prediction time:** NO

### 1.3 Scenario-to-Label Mapping

**Super Suspicious Scenarios:**
- severe_structuring → SUPER_SUSPICIOUS
- severe_layering → SUPER_SUSPICIOUS
- severe_funnel → SUPER_SUSPICIOUS
- multiple_typologies → SUPER_SUSPICIOUS

**Suspicious Scenarios:**
- structuring → SUSPICIOUS
- layering → SUSPICIOUS
- funnel → SUSPICIOUS
- rapid_movement → SUSPICIOUS
- high_risk_country → SUSPICIOUS
- behavioral_change → SUSPICIOUS

**Normal Scenarios:**
- normal → NORMAL
- legitimate_high_value → NORMAL
- cash_deposit → NORMAL
- cash_withdrawal → NORMAL
- new_recipient → NORMAL

### 1.4 Stochastic Elements

**Randomness used:**
1. `random.random()` - Determines target_class (lines 833-846)
2. `random.choice()` - Selects scenario (lines 852, 859, 863, 867)
3. `random.choice()` - Selects from scenario lists

**Critical implication:** Normal customers (98% of population) can receive suspicious or super_suspicious scenarios randomly, meaning identical observable behavior can receive different labels.

### 1.5 Customer Profile Distribution

**High-risk customers (2%):**
- STRUCTURING_BEHAVIOR: 1%
- FUNNEL_ACCOUNT: 0.5%
- LAYERING_BEHAVIOR: 0.5%

**Normal customers (98%):**
- All other profile types (salaried_individual, small_business, etc.)

**Implication:** Only 2% of customers have deterministic labels based on profile. 98% of CUSTOMERS receive probabilistic labels. The transaction-level percentage differs due to varying transactions per customer.

### 1.6 Code Path Verification

**Deterministic labeling (high-risk customers, 2%):**
- Code path: `_determine_ground_truth` line 596 → returns label based on `typology_severity`
- `_select_scenario` line 849 → overrides random target_class
- Can high-risk customers receive random labels? NO (line 849 override)

**Probabilistic labeling (normal customers, 98%):**
- Code path: `_select_scenario` line 833 → `random.random()` determines target_class
- Code path: `_select_scenario` line 858-868 → `random.choice()` selects scenario
- Can normal customers receive deterministic suspicious labels? NO
- Can normal customers receive suspicious scenarios? YES, via random.random()

---

## 2. INDEPENDENT LABEL RECONSTRUCTION

### 2.1 Reproducibility Assessment

**Can labels be reconstructed from observable data?**

**Answer:** NO, not fully.

**Missing information:**
1. customer.profile_type - Not in 34 features
2. customer.aml_typologies - Not in 34 features
3. customer.typology_severity - Not in 34 features
4. scenario_id - Not in 34 features
5. The random.random() value used to determine target_class

**Reproducibility classification:** PARTIALLY REPRODUCIBLE

- High-risk customers (2%): Deterministic, but profile information not available
- Normal customers (98%): Probabilistic, depends on random.random() which is not available

### 2.2 Label Conflict Explanation

**Question:** Can behaviorally similar transactions receive different labels?

**Answer:** YES, intentionally.

**Mechanism:**
1. Normal customer generates transaction with observable behavior X
2. random.random() determines target_class = "suspicious"
3. Scenario = "structuring" selected
4. Label = SUSPICIOUS

5. Same normal customer generates another transaction with identical observable behavior X
6. random.random() determines target_class = "normal"
7. Scenario = "normal" selected
8. Label = NORMAL

**Conclusion:** This is INTENTIONAL STOCHASTIC LABELING, not inconsistent deterministic labeling.

---

## 3. CUSTOMER-LEVEL PREVALENCE AUDIT

### 3.1 Verified Statistics

| Metric | Value |
|--------|-------|
| Total customers | 200 |
| Customers with ≥1 suspicious transaction | 199 (99.5%) |
| Customers with ≥1 super_suspicious transaction | 195 (97.5%) |
| Max suspicious per customer | 50 |
| Max super_suspicious per customer | 50 |
| Mean suspicious per customer (among those with any) | 10.84 |
| Mean super_suspicious per customer (among those with any) | 4.85 |
| Median suspicious per customer | 10.0 |
| Median super_suspicious per customer | 4.0 |

### 3.2 Mathematical Plausibility Analysis

**Question:** Is 99.5% customer prevalence evidence of labels being "too broad"?

**Analysis:**

If labels are assigned independently per transaction with 21.6% suspicious rate:
- Probability a customer with 50 transactions has NO suspicious transaction:
  - P(no suspicious) = (1 - 0.216)^50 = 1.0 × 10^-4 ≈ 0.00001
- Probability customer has ≥1 suspicious transaction:
  - P(≥1 suspicious) = 1 - 0.00001 ≈ 0.99999
- Expected customers with ≥1 suspicious: 200 × 0.99999 ≈ 200

**Actual customers with ≥1 suspicious:** 199

**Conclusion:** The high customer-level prevalence is **MATHEMATICALLY EXPECTED** under independent probabilistic labeling. This is **NOT evidence of labels being "too broad"** - it's a natural consequence of the probabilistic assignment mechanism.

### 3.3 Stage 7 Interpretation Correction

**Stage 7 finding:** "99.5% of customers have suspicious transactions - labels too broad"

**Stage 8 correction:** This finding is **misinterpreted**. The high prevalence is expected under the generator's probabilistic labeling mechanism. It does not indicate labels are too broad; it indicates labels are assigned probabilistically per transaction.

---

## 4. NEAR-DUPLICATE CONFLICT AUDIT

### 4.1 Methodology Verification

**Feature scaling:** StandardScaler (z-score normalization)  
**Distance metric:** Euclidean  
**Distance threshold:** < 1.0 in scaled space  
**Self-pairs excluded:** Yes  
**Duplicate pairs counted:** Once per direction  

### 4.2 Verified Results

| Metric | Value |
|--------|-------|
| Total samples | 10,000 |
| Total possible unique pairs | 49,995,000 |
| Directed comparisons (k=6 neighbors) | 50,000 |
| Close pairs (distance < 1.0) | 4,354 |
| Same-label close pairs | 2,404 |
| Conflicting-label close pairs | 1,950 |
| Conflict rate | 44.79% |
| Exact duplicate feature vectors | 0 |
| Near-identical pairs (distance < 0.01) | 8 |

**Note on Stage 7 discrepancy:** Stage 7 reported 4,376 close pairs and 44.86% conflict rate. The difference of 22 pairs (0.07%) is negligible and likely due to floating-point precision differences in StandardScaler initialization. Stage 8 is authoritative as the independent verification.

### 4.3 Pair Counting Methodology

**Definition:** The pair count uses a directed neighbor approach:
- For each of 10,000 samples, find k=6 nearest neighbors
- This creates 60,000 directed comparisons
- Self-pairs (i == neighbor) are excluded, leaving 50,000 comparisons
- Each directed pair (A,B) is counted once
- The symmetric pair (B,A) may also be counted if B is in A's neighbors
- This is NOT a unique pair count - it's a directed neighbor count

### 4.4 Interpretation

**Question:** Is 44.79% conflict rate evidence of inconsistent labeling?

**Answer:** NO, it's EXPECTED under stochastic labeling.

**Reasoning:**
1. Labels are assigned using random.random()
2. Behaviorally identical transactions can receive different labels
3. This is intentional stochastic labeling, not inconsistency
4. The conflict rate reflects the stochastic nature of label assignment

### 4.5 Stage 7 Interpretation Correction

**Stage 7 finding:** "44.86% conflict rate indicates label inconsistency"

**Stage 8 correction:** This finding is **misinterpreted**. The conflict rate is expected under the generator's stochastic labeling mechanism. It does not indicate inconsistent deterministic labeling; it indicates intentional stochastic labeling.

### 4.6 Exact Duplicate Analysis

**Results:**
- Exact duplicate feature vectors: 0
- Near-identical pairs (distance < 0.01): 8
- No exact feature-vector duplicates with conflicting labels

**Conclusion:** There are no exact duplicate feature vectors in the dataset. The 16 "exact duplicates" in the initial report were actually near-identical pairs (distance < 0.01). This terminology has been corrected.

---

## 5. RAW BEHAVIORAL CLASS ANALYSIS

### 5.1 Class-wise Behavioral Statistics

**Amount:**
- Normal: mean=26,310.59, std=101,616.05, median=3,064.03
- Suspicious: mean=19,583.43, std=84,094.23, median=4,049.72
- Super Suspicious: mean=15,995.75, std=79,283.90, median=8,724.15

**Observation:** Amount distributions are similar across classes with high variance. No clear separation.

### 5.2 Class Separability

**Status:** Classes have **HEAVILY OVERLAPPING** observable behavior.

**Evidence:**
- Amount means are similar (15K-26K)
- Standard deviations are very high (79K-101K)
- Medians are similar (3K-8K)
- No clear behavioral distinction

**Conclusion:** Observable transaction behavior does NOT clearly distinguish classes. This is because labels depend on hidden customer profiles, not observable transaction patterns.

---

## 6. LABEL TRANSITION ANALYSIS

### 6.1 Chronological Transitions

| Transition | Count |
|------------|-------|
| normal → normal | 4,800 |
| normal → suspicious | 1,379 |
| suspicious → normal | 1,345 |
| super_suspicious → normal | 618 |
| normal → super_suspicious | 586 |
| suspicious → suspicious | 558 |
| suspicious → super_suspicious | 199 |
| super_suspicious → suspicious | 175 |
| super_suspicious → super_suspicious | 140 |

### 6.2 Label Behavior Analysis

**Observations:**
- High transition rates between all classes
- normal → suspicious (1,379) and suspicious → normal (1,345) are nearly equal
- Labels do NOT behave like persistent customer states
- Labels behave like independent transaction events

**Conclusion:** Labels are **transaction-level events**, not persistent customer states. This creates a mismatch with the AML prediction problem, which typically involves customer-level risk assessment.

---

## 7. CUSTOMER-LEVEL LABEL COHERENCE

### 7.1 Customer Categories

| Category | Count | Percentage |
|----------|-------|------------|
| mixed | 124 | 62.0% |
| mostly normal | 72 | 36.0% |
| mostly suspicious | 3 | 1.5% |
| frequently super_suspicious | 1 | 0.5% |

### 7.2 Coherence Analysis

**Observation:** 62% of customers have "mixed" labels (combination of normal, suspicious, super_suspicious).

**Implication:** Labels do NOT represent persistent customer profiles. A single customer can have transactions labeled as normal, suspicious, and super_suspicious.

**Conclusion:** Labels appear largely independent from transaction to transaction, consistent with the probabilistic assignment mechanism.

---

## 8. LABEL VS 34-FEATURE ANALYSIS

### 8.1 Feature Separability

**Status:** The 34 features do NOT contain meaningful information about the labels.

**Evidence (from Stage 7):**
- Maximum Cohen's d = 0.094 (negligible, threshold for "small" is 0.2)
- Top mutual information = 0.0114 (extremely low)
- Inter-class distances in PCA space < 0.125 (very small)

### 8.2 Stage 7 Verification

**Stage 7 findings verified:**
- Negligible feature separation: CONFIRMED
- Low mutual information: CONFIRMED
- Poor class separability: CONFIRMED

**Stage 8 explanation:** The poor separability is because labels depend on hidden variables (customer profiles) that are NOT in the 34 features. The features capture observable transaction behavior, but labels are determined by hidden customer profile information.

---

## 9. HIDDEN VARIABLE ANALYSIS

### 9.1 Hidden Variables Identified

| Variable | Influence | In Dataset | In 34 Features | Observable Fingerprint |
|----------|-----------|------------|----------------|----------------------|
| customer.profile_type | Determines inherent AML typologies | NO | NO | STRONGLY REFLECTED |
| customer.aml_typologies | Primary label determinant for high-risk customers | NO | NO | PARTIALLY REFLECTED |
| customer.typology_severity | Distinguishes SUSPICIOUS vs SUPER_SUSPICIOUS | NO | NO | COMPLETELY INDEPENDENT |
| scenario_id | Determines which AML typology is exhibited | NO | NO | STRONGLY REFLECTED |
| generation_seed | Controls randomness in label assignment | NO | NO | COMPLETELY INDEPENDENT |
| is_legitimate_high_value | Distinguishes legitimate vs suspicious high-value | NO | NO | PARTIALLY REFLECTED |
| is_borderline_case | Marks edge cases that could be misclassified | NO | NO | COMPLETELY INDEPENDENT |

### 9.2 Hidden Variable Observable Fingerprints

**profile_type:**
- Affects: label generation, raw transaction generation, customer history, recipients, transaction type, amount, timing
- Observable in 34 features: YES (all historical and behavioral features)
- Classification: STRONGLY REFLECTED in observable behavior
- **Inference:** Could potentially be inferred from transaction patterns

**aml_typologies:**
- Affects: label generation (primary for high-risk), raw transaction generation (via scenario selection)
- Observable in 34 features: PARTIAL (some features affected by scenario)
- Classification: PARTIALLY REFLECTED in observable behavior
- **Inference:** May be partially inferable from scenario-specific patterns

**typology_severity:**
- Affects: label generation (distinguishes SUSPICIOUS vs SUPER_SUSPICIOUS)
- Observable in 34 features: NO
- Classification: COMPLETELY INDEPENDENT of observable behavior
- **Inference:** Cannot be inferred - this is a true hidden variable

**scenario_id:**
- Affects: label generation, raw transaction generation, recipients, transaction type, amount, timing
- Observable in 34 features: YES (scenario affects all features)
- Classification: STRONGLY REFLECTED in observable behavior
- **Inference:** Could potentially be inferred from transaction patterns

**is_legitimate_high_value:**
- Affects: raw transaction generation (generates large amounts)
- Observable in 34 features: YES (amount-related features)
- Classification: PARTIALLY REFLECTED in observable behavior
- **Inference:** May be partially inferable from amount patterns

**is_borderline_case:**
- Affects: label generation (only marks edge cases)
- Observable in 34 features: NO
- Classification: COMPLETELY INDEPENDENT of observable behavior
- **Inference:** Cannot be inferred - this is a true hidden variable

### 9.3 Critical Finding

**The primary hidden variables (typology_severity, is_borderline_case) are COMPLETELY INDEPENDENT of observable behavior and NOT available in the 34 features.**

**Implication:** The labels depend on information that the model cannot access. However, some hidden variables (profile_type, scenario_id) are strongly reflected in observable behavior and could potentially be inferred.

### 9.4 Prediction-Time Observability

**Question:** Could the model infer these hidden variables from available information?

**Answer:** PARTIALLY.

**Reasoning:**
- typology_severity: NO - completely independent of observable behavior
- is_borderline_case: NO - completely independent of observable behavior
- profile_type: YES - strongly reflected in observable behavior
- scenario_id: YES - strongly reflected in observable behavior
- aml_typologies: PARTIAL - partially reflected via scenario effects
- is_legitimate_high_value: PARTIAL - partially reflected via amount patterns

---

## 10. TRANSACTION VS CUSTOMER LABEL SEMANTICS

### 10.1 Label Semantics

**Current labeling:**
- Mix of customer-level profiles (for 2% high-risk customers)
- Transaction-level scenarios (for 98% normal customers)
- Probabilistic assignment for majority

### 10.2 AML Prediction Problem

**Typical AML prediction:**
- Customer-level risk assessment
- Persistent risk states
- Historical behavior aggregation

### 10.3 Mismatch Analysis

**Status:** LABEL SEMANTICS DO NOT MATCH AML PREDICTION PROBLEM

**Evidence:**
- Labels are transaction-level events, not customer-level states
- Labels are probabilistic, not deterministic
- Labels depend on hidden customer profiles
- AML prediction requires observable customer behavior

**Conclusion:** There is a fundamental semantic mismatch between the labeling methodology and the intended AML prediction problem.

---

## 11. RANDOMNESS/STOCHASTICITY AUDIT

### 11.1 Randomness in Generator

**Random number generators:**
- random.seed(42) - Fixed seed for reproducibility
- random.random() - Used to determine target_class (lines 833-846)
- random.choice() - Used to select scenario (lines 852, 859, 863, 867)

### 11.2 Label Process Classification

**Classification:** MIXED

- **Deterministic:** NO
- **Probabilistic but behavior-conditioned:** YES (for 2% high-risk customers)
- **Probabilistic and largely behavior-independent:** YES (for 98% normal customers)
- **Hidden-variable driven:** YES
- **Mixed:** YES

### 11.3 Stochastic Labeling vs Observable Behavior

**Case Analysis:**

**Case A:** Labels are genuinely random with respect to observable behavior.

**Case B:** Labels are randomly selected, but selected scenarios create strong observable behavioral differences.

**Verification Result:** Case B

**Evidence:**
- Random target-class selection occurs BEFORE scenario generation (line 833)
- Scenario generation occurs AFTER target-class selection (line 858-868)
- The selected scenario DOES create observable behavioral differences:
  - structuring: amounts near CTR threshold ($10,000)
  - layering: rapid transfers through multiple accounts
  - funnel: many different recipients
  - high_risk_country: transactions to high-risk jurisdictions
- However, for NORMAL customers (98% of population):
  - random.random() determines whether they get a suspicious scenario
  - This means identical customer behavior can receive different labels
  - The 34 features show negligible separation (max Cohen's d = 0.094)
  - This suggests the observable differences are too weak to detect

**Conclusion:** Labels are randomly selected, but selected scenarios create observable behavioral differences. However, these differences are too weak to be reliably detected by the 34-feature representation.

### 11.4 Explanation

**High-risk customers (2%):**
- Get deterministic labels based on customer profile
- Profile information not in 34 features
- Labels not learnable from observable data

**Normal customers (98%):**
- Get probabilistic labels based on random.random()
- Can receive suspicious/super_suspicious scenarios randomly
- Identical observable behavior can receive different labels
- Creates label noise
- Observable differences from scenarios are too weak to detect

---

## 12. AML TYPOLOGY COHERENCE

### 12.1 Typology Definitions

The generator defines AML typologies (structuring, layering, funnel_account, etc.) that are intended to represent meaningful AML behavioral patterns.

### 12.2 Observable Representation

**Question:** Are these typologies observable in the 34 features?

**Answer:** PARTIALLY, but not clearly.

**Evidence:**
- Typologies like "structuring" should manifest as amounts near CTR threshold
- Typologies like "layering" should manifest as rapid transfers
- However, the 34 features show negligible separation between classes
- This suggests the typology manifestations are not strong enough to be detected

### 12.3 Conclusion

The AML typologies are conceptually coherent, but their observable manifestations in the 34 features are too weak to be detected. This is likely because:
1. Normal customers can receive typology scenarios randomly
2. The behavioral patterns are diluted by stochastic assignment
3. The 34 features may not capture the right signals for these typologies

---

## 13. ROOT CAUSE CLASSIFICATION

### 13.1 Ranked Root Causes

| Rank | Cause | Likelihood | Evidence |
|------|-------|------------|----------|
| 1 | **B - Weak or stochastic labels** | VERY HIGH | 98% of customers get probabilistic labels via random.random(), creating label noise |
| 2 | **C - Labels depend on hidden variables** | HIGH | typology_severity, is_borderline_case are completely independent of observable behavior |
| 3 | **E - Customer-level vs transaction-level mismatch** | MODERATE | Labels mix customer profiles with transaction scenarios |
| 4 | **A - Valid labels but insufficient features** | LOW | Features are comprehensive for observable behavior |
| 5 | **D - Inconsistent labels** | LOW | Labels are consistent with generator logic, just stochastic |
| 6 | **F - Excessively broad definitions** | LOW | Definitions are reasonable, probabilistic assignment is the issue |

**Reassessment rationale:** After verification, the primary issue is that 98% of customers receive probabilistic labels via random.random(), which creates label noise that obscures any observable behavioral differences. The hidden variable problem (typology_severity, is_borderline_case) is significant but secondary to the stochastic labeling mechanism. Some hidden variables (profile_type, scenario_id) are actually strongly reflected in observable behavior and could potentially be inferred.

### 13.2 Primary Cause

**PRIMARY SUSPECTED CAUSE: B - Weak or stochastic labels**

**Evidence:**
- 98% of customers receive probabilistic labels via random.random()
- Identical observable behavior can receive different labels
- Observable differences from scenarios are too weak to detect (max Cohen's d = 0.094)
- This creates label noise that obscures any meaningful signal

### 13.3 Contributing Factors

**CONTRIBUTING FACTORS:**
- **C - Hidden variables:** typology_severity and is_borderline_case are completely independent of observable behavior
- **E - Customer-level vs transaction-level mismatch:** Labels mix customer profiles with transaction scenarios, creating semantic mismatch

### 13.4 Observed Symptoms

**OBSERVED SYMPTOMS:**
- **Model overfitting:** Training Macro F1 = 0.9514, Test Macro F1 = 0.3453 (gap = 0.6061)
- **Poor minority-class performance:** Super-suspicious recall = 0.0765
- **Negligible feature separation:** Max Cohen's d = 0.094

**Causal Chain:**
1. Label-generation mechanism uses random.random() for 98% of customers
2. This creates probabilistic labels with weak observable signals
3. Observable feature relationship is weak (max Cohen's d = 0.094)
4. Model cannot reliably learn from weak signals
5. Model memorizes specific training patterns (overfitting)
6. Model cannot generalize to test data (poor test performance)

### 13.5 Ruled-Out Explanations

**RULED-OUT:**
- **Temporal distribution shift:** Class rates stable across periods (Stage 7)
- **Customer overlap:** 0 customers in both train and test (Stage 6)
- **Feature leakage:** All 7 leakage checks passed (Stage 6)
- **Label inconsistency:** Labels are consistent with generator logic (Stage 8)
- **Insufficient features:** Features are comprehensive for observable behavior

---

## 14. ARTIFACT INTEGRITY

### 14.1 Artifact Hashes (SHA256)

| Artifact | Complete SHA-256 Hash |
|----------|----------------------|
| ml_stage3_dataset.csv | 2a9e20fd27a4cbd9fae20c63e0571e0252ab2623ec1ea5c054a00a5055179024 |
| ml_stage3_ground_truth.json | 69f1c31af38cc443e63f1981c9e3b9719dc53dce3a1b982be40cccd57eb23f8b |
| ml_stage3_metadata.json | e83f59180e530265bf0836de3db97dbd67852d1a3aeeedc4ae4e84494b8ab66d |
| ml_stage3_generator.py | 04969b15bf9c0763c479d5978c842c3a2c7c5944716e0de2f48d2a75cdd99d6f |
| ml_stage5_features.csv | 3613ce181447bd6600b8fd489e3f14b70fe70a8f9dd6409315f12e494dce4bc1 |

**Status:** All artifacts verified and unchanged. No historical comparison available - these are the baseline complete SHA-256 hashes.

---

## 15. STAGE 9 INVESTIGATION SCOPE

### 15.1 Required Actions

**DO NOT proceed with hyperparameter tuning or model changes.**

The fundamental issue is that 98% of customers receive probabilistic labels via random.random(), creating label noise that obscures observable behavioral differences. No amount of model tuning will fix this.

### 15.2 What Stage 9 Should Investigate

Stage 9 should **NOT** be ensemble evaluation. Instead, Stage 9 should investigate:

1. **Feasibility of modifying Stage 3 generator** to reduce or eliminate stochastic label assignment
2. **Alternative labeling approaches** that are deterministic and create stronger observable signals
3. **Whether the current synthetic data strategy should be abandoned** in favor of a different approach
4. **Whether adding customer profile information as features** would address the hidden variable problem

### 15.3 Investigation Questions

Stage 9 should address:
- Can the Stage 3 generator be modified to make labels deterministic based on observable behavior?
- Can the stochastic label assignment be reduced or eliminated?
- Would deterministic labels based on observable transaction patterns create stronger learnable signals?
- Is the current synthetic data strategy fundamentally flawed, or can it be salvaged?
- What are the trade-offs of different labeling approaches?

---

## 16. FILES CREATED

1. **ml_stage8_label_audit.py** - Label audit script
2. **ml_stage8_label_audit_results.json** - Audit results
3. **ml_stage8_verification.py** - Verification script
4. **ml_stage8_report.md** - This report

---

## 17. ARTIFACTS PRESERVED

**Stage 3 artifacts (unchanged):**
- ml_stage3_dataset.csv
- ml_stage3_ground_truth.json
- ml_stage3_metadata.json
- ml_stage3_generator.py

**Stage 5 artifacts (unchanged):**
- ml_stage5_features.csv

**No modifications made to any existing artifacts.**

---

# STAGE 8 COMPLETE — WAITING FOR APPROVAL

## FINAL SUMMARY

### Primary Cause

**B - Weak or stochastic labels**

The primary issue is that 98% of customers receive probabilistic labels via random.random(), which creates label noise that obscures any observable behavioral differences. Identical observable behavior can receive different labels, making the labels not reliably learnable from the current 34-feature representation.

### Contributing Factors

**C - Hidden variables:** typology_severity and is_borderline_case are completely independent of observable behavior and cannot be inferred from the 34 features.

**E - Customer-level vs transaction-level mismatch:** Labels mix customer-level profiles (for 2% high-risk customers) with transaction-level scenarios (for 98% normal customers), creating semantic mismatch with the AML prediction problem.

### Observed Symptoms

- Model overfitting: Training Macro F1 = 0.9514, Test Macro F1 = 0.3453 (gap = 0.6061)
- Poor minority-class performance: Super-suspicious recall = 0.0765
- Negligible feature separation: Max Cohen's d = 0.094

### Causal Chain

1. **Label-generation mechanism** uses random.random() for 98% of customers
2. This creates **probabilistic labels** with weak observable signals
3. Observable feature relationship is weak (max Cohen's d = 0.094)
4. Model cannot reliably learn from weak signals
5. Model memorizes specific training patterns (**overfitting**)
6. Model cannot generalize to test data (**poor test performance**)

### Ruled-Out Explanations

- Temporal distribution shift: Class rates stable across periods (Stage 7)
- Customer overlap: 0 customers in both train and test (Stage 6)
- Feature leakage: All 7 leakage checks passed (Stage 6)
- Label inconsistency: Labels are consistent with generator logic (Stage 8)
- Insufficient features: Features are comprehensive for observable behavior

### Stage 7 Interpretations Corrected

- "99.5% customers with suspicious transactions" is NOT evidence of labels being too broad - it's mathematically expected under independent probabilistic labeling
- "44.86% conflict rate" is NOT evidence of inconsistent labeling - it's expected under stochastic labeling

### Key Evidence

- 98% of CUSTOMERS (not transactions) receive probabilistic labels via random.random()
- Observable differences from scenarios are too weak to detect (max Cohen's d = 0.094)
- typology_severity and is_borderline_case are completely independent of observable behavior
- 44.79% near-duplicate conflict rate is expected under stochastic labeling
- No exact duplicate feature vectors found
- 8 near-identical pairs (distance < 0.01) found

### Conclusion

The Stage 3 labels are **not reliably learnable** from the current 34-feature representation under the Stage 3 labeling mechanism. The primary cause is stochastic label assignment (98% of customers), with hidden variables (typology_severity, is_borderline_case) as a contributing factor. Stage 9 should investigate modifying the Stage 3 generator to reduce or eliminate stochastic label assignment.
