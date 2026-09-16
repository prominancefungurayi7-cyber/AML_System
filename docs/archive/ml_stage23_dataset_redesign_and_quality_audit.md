# Stage 23: Dataset Redesign and Quality Audit Report

**Date:** 2026-09-03  
**Stage:** 23 - Dataset Redesign and Quality Audit  
**Status:** COMPLETE

---

## 1. PROBLEMS DISCOVERED IN STAGE 21

### 1.1 Class Distribution Change

**Stage 16B (Champion):**
- Normal: 74.46%
- Suspicious: 22.16%
- Super-suspicious: 3.38%

**Stage 21 (Candidate):**
- Normal: 49.5%
- Suspicious: 25.5%
- Super-suspicious: 25.0%

**Problem:** Stage 21 artificially balanced the dataset (50/50 normal vs suspicious+super-suspicious), which:
- Changed the fundamental problem difficulty
- Inflated macro metrics by eliminating class imbalance penalties
- Does not reflect real-world AML detection (where normal transactions dominate)

### 1.2 Overfitting to Dataset

**Independent Generalization Test:**
- Stage 21 test: 92.50% accuracy, 0.9280 Macro F1
- Independent dataset: 62.59% accuracy, 0.4674 Macro F1
- **29.91% accuracy drop**

**Problem:** The model overfit to Stage 21-specific patterns and does not generalize to new customers.

### 1.3 Placeholder Features

**Discovery:** 9 features were constant (all zeros) in Stage 21:
- amount_z_score
- amount_deviation_from_baseline_30d
- tx_frequency_7d
- tx_frequency_30d
- frequency_change_vs_avg_7d
- unique_recipients_7d
- hour
- is_off_hours
- counterparty_change_score_7d

**Problem:** These were added as placeholders but never calculated, reducing effective feature set from 28 to 19.

### 1.4 Behavioral Homogeneity

**Problem:** The 50 super-suspicious customers were assigned the same AML typologies with limited behavioral variation. The diversity improvement was primarily in customer count, not behavioral patterns.

---

## 2. PROBLEMS DISCOVERED IN STAGE 22

### 2.1 ANOVA Calculation Error

**Issue:** Stage 22 reported F=0.00 for all features.

**Root Cause:** 
- 9 constant features caused scipy.stats.f_oneway to return NaN
- NaN values were converted to 0.0
- Non-constant features DO show significant F-statistics (34-127, p < 0.05)

**Corrected Finding:** Features have discriminative power when properly calculated. The F=0.00 was a data quality issue, not a fundamental feature problem.

---

## 3. NEW DATASET DESIGN

### 3.1 Design Principles

1. **Realistic Class Prevalence:** Maintain strong normal dominance (90-95% normal)
2. **Genuine Behavioral Diversity:** Diverse profiles within each class
3. **Sufficient Customer Diversity:** 30-50 suspicious/super-suspicious customers with distinct behaviors
4. **Chapter 1 Coverage:** Explicit coverage of all 6 capabilities
5. **No Leakage:** Independent ground truth, prediction-time features only
6. **Generalization Support:** Independent test population with new customers

### 3.2 Dataset Scale

| Metric | Target |
|--------|--------|
| Total Transactions | 15,000 (increased from 10,000) |
| Total Customers | 300 (increased from 200) |
| Train Customers | 240 |
| Test Customers | 60 |
| Independent Test Customers | 100 (separate population) |

---

## 4. TARGET CLASS DISTRIBUTION AND JUSTIFICATION

### 4.1 Proposed Distribution

| Class | Transaction Count | Percentage | Customer Count |
|-------|------------------|------------|----------------|
| Normal | 13,200 | 88.0% | 240 |
| Suspicious | 1,200 | 8.0% | 40 |
| Super-suspicious | 600 | 4.0% | 20 |

### 4.2 Justification

**Real-World Prevalence:**
- AML detection systems typically see <5% suspicious transactions
- Stage 16B (77.75% accuracy) operated on 94% normal / 6% suspicious+super-suspicious
- Stage 21's 50% normal was unrealistic and inflated metrics

**Balance Considerations:**
- 88% normal maintains realistic imbalance while providing sufficient suspicious examples
- 8% suspicious (1,200 transactions) provides adequate signal for learning
- 4% super-suspicious (600 transactions) provides clear severe cases
- This distribution is more realistic than Stage 21 but provides more suspicious examples than Stage 16B

**Customer Diversity:**
- 40 suspicious customers (30 transactions each on average)
- 20 super-suspicious customers (30 transactions each on average)
- This provides sufficient customer diversity without artificial balancing

---

## 5. CUSTOMER DIVERSITY DESIGN

### 5.1 Behavioral Profile Dimensions

Each customer will have randomized variation in:

**Amount Behavior:**
- Typical amount mean: Log-normal distribution (range: $100 - $100,000)
- Typical amount std: 0.2x - 2.0x of mean
- Amount volatility: Low/Medium/High

**Frequency Behavior:**
- Typical daily transaction count: 0.1 - 10
- Frequency variance: Poisson with varying lambda
- Peak activity periods: Morning/Afternoon/Evening/Random

**Timing Behavior:**
- Business hours preference: 0.0 - 1.0
- Weekend activity: 0.0 - 1.0
- Timezone alignment: Domestic/International/Mixed

**Recipient Patterns:**
- Recipient diversity: 1 - 50 unique recipients
- Recipient loyalty: High (few repeat recipients) / Low (many new recipients)
- Geographic distribution: Domestic/International/Mixed

**Transaction Types:**
- Type preferences: Deposit/Withdraw/Transfer mix
- Channel preferences: Online/Mobile/ATM/Branch/Card mix

**Cross-Border Behavior:**
- International ratio: 0.0 - 0.5
- High-risk jurisdiction preference: 0.0 - 0.2
- Country diversity: 1 - 10 countries

**Account Activity:**
- Account age: 1 - 3650 days
- Activity level: Dormant/Low/Medium/High
- Seasonality: None/Monthly/Quarterly

**Behavioral Changes:**
- Change frequency: Never/Rarely/Occasionally/Frequently
- Change magnitude: Small/Medium/Large
- Change types: Amount/Frequency/Recipient/Timing/Country

### 5.2 Profile Generation Algorithm

For each customer:
1. Sample from multi-dimensional behavioral space
2. Ensure profiles are diverse (no two customers identical)
3. Apply constraints to ensure realistic behavior
4. Generate historical baseline (30-90 days) before labeled transactions

---

## 6. AML TYPOLOGY DIVERSITY DESIGN

### 6.1 Typology Combinations

Instead of assigning the same typologies to all suspicious customers, create diverse combinations:

**Single-Typology Customers (40% of suspicious/super-suspicious):**
- Rapid movement only
- Structuring only
- High-risk jurisdiction only
- Funnel account only
- Layering only
- Behavioral deviation only

**Dual-Typology Customers (40%):**
- Rapid movement + Structuring
- Rapid movement + High-risk jurisdiction
- Structuring + High-risk jurisdiction
- Funnel account + Layering
- Behavioral deviation + Rapid movement
- Behavioral deviation + Structuring

**Multi-Typology Customers (20%):**
- Rapid movement + Structuring + High-risk jurisdiction
- Funnel account + Layering + Behavioral deviation
- All typologies combined (severe cases)

### 6.2 Signal Strength Variation

For each typology, vary the signal strength:

**Strong Signals (30%):**
- Clear, obvious patterns
- High deviation from baseline
- Multiple indicators

**Moderate Signals (50%):**
- Subtle but detectable patterns
- Moderate deviation
- Fewer indicators

**Weak/Subtle Signals (20%):**
- Barely detectable patterns
- Small deviation
- Single indicator

This ensures the model learns to detect a spectrum of suspicious behavior, not just obvious cases.

### 6.3 Typology-Specific Behaviors

**Rapid Movement:**
- Multiple transactions in short time window (<1 hour)
- High cumulative amount
- Unusual frequency for customer

**Structuring/Smurfing:**
- Amounts near CTR threshold ($8,500 - $9,999)
- Multiple transactions same day
- Cumulative amount exceeds threshold

**High-Risk Jurisdiction:**
- Transactions to/from high-risk countries
- Unusual international activity for customer
- Geographic concentration

**Funnel Account:**
- Many different recipients
- Similar amounts to different recipients
- Rapid recipient turnover

**Layering:**
- Chain of transactions through intermediaries
- Complex routing patterns
- Time delays between hops

**Behavioral Deviation:**
- Amount deviation from historical baseline
- Frequency deviation from historical baseline
- New recipient patterns
- Timing deviations

---

## 7. HARD NEGATIVE DESIGN

### 7.1 Legitimate Large Transactions

Normal customers will occasionally:
- Make large transactions ($10,000 - $100,000)
- Transact internationally
- Make multiple transactions in a day
- Transact at unusual hours
- Change recipients frequently

**Constraints:**
- These behaviors must be contextually legitimate
- Must not exhibit AML typology patterns
- Must be consistent with customer profile

### 7.2 Legitimate Business Patterns

Business customers will:
- Have regular high-value transactions
- Transact internationally for legitimate trade
- Have predictable patterns
- Show seasonal variations

### 7.3 Legitimate Behavioral Changes

Normal customers will:
- Show temporary behavioral changes (vacation, large purchase)
- Have one-off large transactions
- Change transaction patterns gradually
- Have legitimate reasons for deviations

### 7.4 Overlap with Suspicious Features

To prevent the model from using single-feature shortcuts:
- Some normal customers will have high cross-border ratios (legitimate international business)
- Some normal customers will have amounts near thresholds (legitimate large payments)
- Some normal customers will have rapid transfers (legitimate urgent payments)
- Some suspicious customers will have normal individual features (subtle cases)

The model must learn to **combine** multiple weak signals rather than rely on one strong feature.

---

## 8. INDEPENDENT GROUND TRUTH METHODOLOGY

### 8.1 Ground Truth Generation Process

**Step 1: Customer Profile Assignment**
- Assign customer behavioral profile (normal/suspicious/super-suspicious)
- Assign AML typologies (if suspicious/super-suspicious)
- Assign signal strength (weak/moderate/strong)

**Step 2: Scenario Selection**
- Select scenario based on customer profile and typologies
- Scenario determines behavioral pattern to generate

**Step 3: Transaction Generation**
- Generate transactions following scenario rules
- Apply customer-specific behavioral variations
- Add realistic noise and randomness

**Step 4: Label Assignment**
- Label is determined by customer profile + scenario
- Label is NOT derived from features
- Label is NOT derived from model predictions
- Label is NOT derived from rule engine

### 8.2 Independence Verification

**No Feature-to-Label Leakage:**
- Labels are assigned BEFORE features are calculated
- Features are calculated from historical data only
- Labels are not used in feature calculation

**No Label-to-Feature Leakage:**
- Features do not include ground truth label
- Features do not include AML typology
- Features do not include scenario ID

**No Temporal Leakage:**
- Features use only historical data (transactions before current)
- No future transactions used
- Timestamp not used as feature

### 8.3 Ground Truth Documentation

Each transaction's ground truth includes:
- ground_truth_label (normal/suspicious/super_suspicious)
- aml_typologies (list of typologies present)
- scenario_id (scenario identifier)
- scenario_description (human-readable description)
- signal_strength (weak/moderate/strong)
- customer_profile (customer behavioral profile)

---

## 9. CHAPTER 1 COVERAGE

### 9.1 Cross-Border Laundering

**Coverage:**
- 30% of suspicious customers exhibit cross-border patterns
- 50% of super-suspicious customers exhibit cross-border patterns
- High-risk jurisdiction transactions included
- Geographic diversity in international transactions

**Limitations:**
- Transaction-only data (no invoice/trade documents)
- Cannot verify actual trade flows
- Cannot detect invoice mis-invoicing

### 9.2 Trade-Based Money Laundering

**Coverage:**
- Limited to transaction-level patterns
- Large international transactions
- Unusual timing patterns
- Geographic concentration

**Limitations:**
- **Cannot claim invoice verification or mis-invoicing detection**
- Requires invoice/trade data for full capability
- Current system can only detect suspicious transaction patterns, not trade-specific fraud

### 9.3 Cash-Based Laundering

**Coverage:**
- Structuring/smurfing patterns (near-threshold amounts)
- Cash-intensive business patterns
- High-volume cash transactions
- Deposit/withdraw patterns

### 9.4 Complex Patterns Over Time

**Coverage:**
- Layering patterns (transaction chains)
- Behavioral deviation over time
- Frequency changes over time
- Recurring pattern detection

### 9.5 Real-Time Monitoring

**Coverage:**
- All features use historical data only
- No future information required
- Suitable for real-time prediction
- Low-latency feature calculation

### 9.6 Behavioral Deviation

**Coverage:**
- Amount deviation from baseline
- Frequency deviation from baseline
- Recipient pattern changes
- Timing deviations
- Geographic deviations

---

## 10. FEATURE/PREDICTION-TIME METHODOLOGY

### 10.1 Feature Categories

**Amount Features:**
- amount (current transaction amount)
- sender_avg_amount (historical average)
- sender_max_amount (historical maximum)
- amount_to_sender_avg (ratio)
- amount_z_score (statistical deviation)
- amount_deviation_from_baseline_30d (30-day deviation)

**Frequency Features:**
- tx_frequency_7d (7-day count)
- tx_frequency_30d (30-day count)
- frequency_change_vs_avg_7d (deviation from average)
- sender_tx_count_24h (24-hour count)

**Volume Features:**
- sender_volume_24h (24-hour volume)
- amount_to_sender_volume_24h (ratio)

**Recipient Features:**
- is_new_recipient (binary)
- unique_recipients_7d (7-day unique count)
- counterparty_change_score_7d (recipient turnover)

**Timing Features:**
- hour (transaction hour)
- is_off_hours (binary)
- time_since_last_transaction_hours

**Pattern Features:**
- same_day_count (same-day transaction count)
- same_day_total (same-day cumulative amount)
- rapid_transfer_count (rapid transfers)
- recurring_pattern_score (recurring behavior)

**Cross-Border Features:**
- is_cross_border (binary)
- is_high_risk_country (binary)
- cross_border_count_7d (7-day count)
- cross_border_volume_7d (7-day volume)
- cross_border_ratio_7d (7-day ratio)

**Structuring Features:**
- amount_near_threshold_flag (near CTR threshold)
- same_day_cumulative_amount (cumulative same-day)
- structuring_pattern_score (structuring behavior)

### 10.2 Prediction-Time Safety Verification

**No Future Transactions:**
- All features use only transactions with timestamp < current transaction timestamp
- Verified by chronological ordering

**No Future Labels:**
- Ground truth label not used in features
- Labels assigned independently

**No Post-Event Information:**
- No post-transaction data used
- All data available at transaction time

**No Customer/Test Leakage:**
- Customer holdout enforced
- No customer overlap between train/test

**No Timestamp Leakage:**
- Timestamp not used as feature
- Only derived temporal features (hour, time_since_last)

**No Label-Derived Features:**
- Features calculated from raw transaction data only
- No features derived from ground truth

---

## 11. CORRECTED STATISTICAL SIGNAL ANALYSIS

### 11.1 ANOVA Investigation Results

**Stage 22 Issue:** F=0.00 for all features

**Root Cause:**
- 9 features were constant (all zeros) due to placeholder implementation
- scipy.stats.f_oneway returns NaN for constant features
- NaN values were converted to 0.0

**Corrected Analysis (using sklearn f_classif):**

| Feature | F-Statistic | P-Value | Significant |
|---------|-------------|---------|-------------|
| amount | 34.46 | <0.001 | Yes |
| sender_avg_amount | 54.98 | <0.001 | Yes |
| sender_max_amount | 127.69 | <0.001 | Yes |
| amount_to_sender_avg | 10.92 | <0.001 | Yes |
| sender_tx_count_24h | 0.93 | 0.394 | No |
| ... | ... | ... | ... |

**Mutual Information Analysis:**
- Mean MI: 0.195
- Range: 0.0 - 0.95
- Top features show strong signal

**Conclusion:** Features DO have discriminative power when properly calculated. The F=0.00 was a data quality issue, not a fundamental feature problem.

### 11.2 Statistical Diagnostics for New Dataset

**Required Diagnostics:**
1. ANOVA F-statistic per feature
2. Mutual information per feature
3. Feature variance analysis
4. Class overlap analysis
5. Correlation matrix
6. Feature importance via tree-based model

**Acceptance Criteria:**
- At least 50% of features show significant class separation (p < 0.05)
- Mean mutual information > 0.1
- No features with zero variance (except intentional constants)
- Feature correlation < 0.9 (avoid multicollinearity)

---

## 12. DATASET QUALITY AUDIT

### 12.1 Pre-Training Audit Checklist

**Class Distribution:**
- [ ] Normal: 88% ± 2%
- [ ] Suspicious: 8% ± 1%
- [ ] Super-suspicious: 4% ± 1%

**Customer Distribution:**
- [ ] Total customers: 300
- [ ] Normal customers: 240
- [ ] Suspicious customers: 40
- [ ] Super-suspicious customers: 20

**Transactions per Customer:**
- [ ] Mean: 50 ± 10
- [ ] Min: 30
- [ ] Max: 70
- [ ] No customers with <10 transactions

**AML Typology Distribution:**
- [ ] Rapid movement: Present in suspicious/super-suspicious
- [ ] Structuring: Present in suspicious/super-suspicious
- [ ] High-risk jurisdiction: Present in suspicious/super-suspicious
- [ ] Funnel account: Present in suspicious/super-suspicious
- [ ] Layering: Present in super-suspicious
- [ ] Behavioral deviation: Present in suspicious/super-suspicious

**Typology Combinations:**
- [ ] Single-typology: 40% of suspicious/super-suspicious
- [ ] Dual-typology: 40% of suspicious/super-suspicious
- [ ] Multi-typology: 20% of suspicious/super-suspicious

**Signal Strength Distribution:**
- [ ] Strong: 30% of suspicious/super-suspicious
- [ ] Moderate: 50% of suspicious/super-suspicious
- [ ] Weak: 20% of suspicious/super-suspicious

**Feature Distributions:**
- [ ] No constant features (except intentional)
- [ ] No features with zero variance
- [ ] Feature ranges reasonable
- [ ] No extreme outliers (>5 std from mean)

**Class Overlap:**
- [ ] Feature distributions overlap between classes (realistic)
- [ ] No perfect separation (avoid trivial problem)
- [ ] Hard negatives present

**Temporal Distribution:**
- [ ] Transactions distributed across 30-90 days
- [ ] No temporal clustering
- [ ] Chronological ordering preserved

**Cross-Border Distribution:**
- [ ] International transactions present in all classes
- [ ] High-risk jurisdiction transactions in suspicious/super-suspicious
- [ ] Geographic diversity

**Sequence Diversity:**
- [ ] Transaction type sequences vary
- [ ] Recipient patterns vary
- [ ] Timing patterns vary

**Duplicate Checks:**
- [ ] No duplicate transaction IDs
- [ ] No duplicate (sender_account, timestamp, amount) tuples
- [ ] No identical customer profiles

**Hard Negatives:**
- [ ] Normal customers with large transactions
- [ ] Normal customers with international activity
- [ ] Normal customers with rapid transfers
- [ ] Suspicious customers with normal individual features

---

## 13. GENERALIZATION/HOLDOUT DESIGN

### 13.1 Population Split

**Training Population (240 customers):**
- 192 normal customers
- 32 suspicious customers
- 16 super-suspicious customers
- 12,000 transactions

**Development/Validation Population (60 customers):**
- 48 normal customers
- 8 suspicious customers
- 4 super-suspicious customers
- 3,000 transactions

**Final Unseen Test Population (60 customers):**
- 48 normal customers
- 8 suspicious customers
- 4 super-suspicious customers
- 3,000 transactions

**Independent Generalization Population (100 customers):**
- Generated with different random seed
- Entirely new customer profiles
- 5,000 transactions
- Used only for final generalization test

### 13.2 Holdout Rules

**Customer Holdout:**
- Zero customer overlap between populations
- Customer IDs unique across populations
- Customer profiles independently generated

**Temporal Holdout:**
- Each population has its own time window
- No temporal overlap between populations
- Chronological ordering preserved within each population

**Data Holdout:**
- No transactions copied between populations
- No scenarios repeated exactly
- Independent random seeds for each population

### 13.3 Generalization Test Protocol

1. Train model on Training Population
2. Tune hyperparameters on Development Population
3. Select final model based on Validation Population
4. Evaluate final model on Unseen Test Population
5. Report final metrics on Unseen Test Population only
6. Optional: Evaluate on Independent Generalization Population

---

## 14. DATASET APPROVAL STATUS

### 14.1 Current Status

**NOT APPROVED FOR MODEL TRAINING YET**

The dataset design is complete but requires:
1. Implementation of the new generator
2. Generation of the dataset
3. Completion of the quality audit
4. Statistical signal verification
5. Independent generalization test

### 14.2 Approval Criteria

The dataset will be approved for model training when:

**Data Quality:**
- [ ] All quality audit checks pass
- [ ] No constant placeholder features
- [ ] Feature distributions reasonable
- [ ] Hard negatives present

**Statistical Signal:**
- [ ] At least 50% of features show significant class separation
- [ ] Mean mutual information > 0.1
- [ ] No perfect class separation (avoid trivial problem)

**Generalization Support:**
- [ ] Customer holdout verified (zero overlap)
- [ ] Temporal holdout verified
- [ ] Independent population generated
- [ ] Initial generalization test passes (>60% accuracy on independent data)

**Chapter 1 Coverage:**
- [ ] All 6 capabilities represented
- [ ] Trade-based limitations documented
- [ ] Cross-border patterns present
- [ ] Complex patterns present

### 14.3 Next Steps

1. Implement new generator with behavioral diversity
2. Generate dataset (15,000 transactions, 300 customers)
3. Run quality audit
4. Verify statistical signal
5. Test initial generalization
6. If approved, proceed to model training

---

## 15. CONCLUSION

Stage 23 has designed a robust AML benchmark dataset that:

1. **Preserves realistic class prevalence** (88% normal vs 50% in Stage 21)
2. **Provides genuine behavioral diversity** through multi-dimensional profiles
3. **Provides sufficient customer diversity** (40 suspicious, 20 super-suspicious customers)
4. **Covers Chapter 1 AML scenarios** with explicit limitations documented
5. **Avoids label/feature leakage** through independent ground truth
6. **Supports generalization** through independent populations

The dataset is designed to be a **realistic difficult problem** where high performance reflects genuine learning of generalizable AML behavior, not artificial balancing or overfitting.

**Status:** Design complete, awaiting implementation and quality audit.

---

**Report End**
