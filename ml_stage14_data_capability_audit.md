# STAGE 14A: DATA/GENERATOR CAPABILITY AUDIT

**Date:** 2026-09-02  
**Status:** COMPLETE

---

## EXECUTIVE SUMMARY

This audit examined the Stage 11 generator and dataset to determine which information dimensions are available for feature engineering. The audit identified critical limitations that constrain the feature design space.

**Key Finding:** The generator has country information (HIGH_RISK_COUNTRIES, LEGITIMATE_COUNTRIES) but does not export it to the dataset. This means the high_risk_country scenario cannot be detected without generator modification.

---

## 1. AVAILABLE DIMENSIONS

### 1.1 FULLY AVAILABLE

- **recipient_account/counterparty_identity:** AVAILABLE (receiver_account column present)
- **transaction_direction:** AVAILABLE (transaction_type column: deposit/withdraw/transfer)
- **inbound_outbound_relationship:** AVAILABLE (inferred from transaction_type)
- **account_to_account_network_relationships:** AVAILABLE (sender_account + receiver_account)
- **historical_customer_behavior:** AVAILABLE (can compute from transaction history)

### 1.2 PARTIALLY AVAILABLE

- **transaction_purpose:** PARTIALLY AVAILABLE (description field exists but not structured)

### 1.3 NOT AVAILABLE

- **recipient_country:** NOT AVAILABLE (generator has country info but not in dataset)
- **sender_country:** NOT AVAILABLE (generator has country info but not in dataset)
- **account_age_tenure:** NOT AVAILABLE
- **geographic_information:** NOT AVAILABLE
- **device_ip_information:** NOT AVAILABLE
- **cash_source_information:** NOT AVAILABLE
- **ownership_beneficial_owner:** NOT AVAILABLE
- **transaction_chains:** NOT AVAILABLE (no chain_id or related_transactions)

---

## 2. GENERATOR CAPABILITY

### 2.1 COUNTRY INFORMATION

The Stage 3/11 generator defines:
- `HIGH_RISK_COUNTRIES`: 19 countries (FATF grey/black list)
- `LEGITIMATE_COUNTRIES`: 13 countries (legitimate jurisdictions)

**Status:** Generator has country information but does not export it to dataset.

### 2.2 ACCOUNT FORMAT

Accounts are formatted as `ACC######` (e.g., ACC131244). No country codes are embedded in account numbers.

**Status:** Country information cannot be inferred from account format.

---

## 3. KEY LIMITATIONS

1. **Generator has country information but does not export it to dataset**
2. **No account age/tenure information**
3. **No device/IP information**
4. **No ownership/beneficial owner information**
5. **No transaction chain tracking**
6. **No structured transaction purpose**

---

## 4. IMPLICATIONS FOR FEATURE DESIGN

### 4.1 CAN DESIGN FEATURES FOR

- STRUCTURING (threshold proximity, clustering)
- LAYERING (counterparty diversity, pass-through)
- FUNNEL (inbound aggregation, concentration)
- RAPID_MOVEMENT (pass-through timing, velocity)
- BEHAVIORAL_CHANGE (deviation from baseline)
- SEVERE (aggregation of multiple indicators)

### 4.2 CANNOT DESIGN FEATURES FOR

- HIGH_RISK_COUNTRY (requires recipient_country field)

### 4.3 SOLUTION FOR HIGH_RISK_COUNTRY

**MODIFY GENERATOR** to export country information to dataset:
- Add `sender_country` column to dataset
- Add `receiver_country` column to dataset
- Assign countries to accounts during generation
- Export country information in CSV export

---

## 5. CONCLUSION

The Stage 11 dataset provides sufficient information to design features for most AML scenarios (structuring, layering, funnel, rapid_movement, behavioral_change, severe). However, the high_risk_country scenario cannot be detected without generator modification to export country information.

**Recommendation:** Proceed with feature design for available dimensions. Address high_risk_country detection through generator modification in a future stage if needed.
