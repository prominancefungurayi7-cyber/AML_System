# STAGE 14E: VALIDATION PLAN

**Date:** 2026-09-02  
**Status:** COMPLETE

---

## EXECUTIVE SUMMARY

This validation plan defines how the proposed 57-feature specification will be validated in Stage 15. The plan ensures that the new features are correctly implemented, temporally safe, and actually improve scenario observability.

---

## 1. IMPLEMENTATION VALIDATION

### 1.1 Feature Extraction Implementation

**Objective:** Implement the 57-feature extraction pipeline correctly.

**Validation Steps:**
1. Implement feature extraction for all 25 new candidate features
2. Remove is_self_transfer from the feature set (constant 0.0)
3. Preserve all 33 existing features (from Stage 5 baseline)
4. Verify that all features are computed correctly
5. Verify that no NaN values are produced
6. Verify that no infinite values are produced

**Acceptance Criteria:**
- All 57 features are extracted successfully
- No NaN values in any feature
- No infinite values in any feature
- Feature values are within expected ranges

---

## 2. TEMPORAL SAFETY VALIDATION

### 2.1 Temporal Safety Verification

**Objective:** Verify that all features are temporally safe.

**Validation Steps:**
1. For each historical feature, verify that it uses only transactions with timestamp < current timestamp
2. For each historical feature, verify that it uses explicit time windows (7d, 30d, 14d)
3. Verify that no feature uses future transactions
4. Verify that no feature uses future aggregates
5. Verify that no feature uses future labels
6. Verify that no feature uses test-set information

**Acceptance Criteria:**
- All features are temporally safe
- No temporal leakage detected
- All time windows are correctly implemented

---

## 3. FEATURE LABEL INDEPENDENCE VALIDATION

### 3.1 Feature-Label Independence

**Objective:** Verify that features are independent of ground-truth labels.

**Validation Steps:**
1. Verify that no feature uses ground_truth_label
2. Verify that no feature uses scenario_id
3. Verify that no feature uses aml_typologies
4. Verify that features are computed only from transaction data and historical transactions
5. Verify that features do not use any ground-truth information

**Acceptance Criteria:**
- No feature uses ground-truth labels
- No feature uses scenario_id
- No feature uses aml_typologies
- Features are independent of labels

---

## 4. SCENARIO OBSERVABILITY VALIDATION

### 4.1 Scenario-Level Observability

**Objective:** Verify that new features improve scenario observability.

**Validation Steps:**
1. Compute Cohen's d for each scenario vs normal using the 57-feature set
2. Compare with Stage 13 baseline observability (34 features)
3. Verify that structuring observability improves from NONE to MODERATE
4. Verify that layering observability improves from WEAK to MODERATE
5. Verify that funnel observability improves from NONE to MODERATE
6. Verify that rapid_movement observability improves from WEAK to MODERATE
7. Verify that behavioral_change observability improves from NONE to MODERATE
8. Verify that severe observability improves from MODERATE to STRONG

**Acceptance Criteria:**
- Structuring observability: Cohen's d > 0.5 (MODERATE)
- Layering observability: Cohen's d > 0.5 (MODERATE)
- Funnel observability: Cohen's d > 0.5 (MODERATE)
- Rapid_movement observability: Cohen's d > 0.5 (MODERATE)
- Behavioral_change observability: Cohen's d > 0.5 (MODERATE)
- Severe observability: Cohen's d > 1.0 (STRONG)

---

## 5. FEATURE IMPORTANCE VALIDATION

### 5.1 Feature Importance Analysis

**Objective:** Verify that new features contribute to model performance.

**Validation Steps:**
1. Train models (Random Forest, Gradient Boosting) on the 57-feature set
2. Compute feature importance for all 57 features
3. Verify that new features have non-zero importance
4. Verify that new features are among the top 20 most important features
5. Verify that constant/low-importance features are identified

**Acceptance Criteria:**
- At least 10 new features have non-zero importance
- At least 5 new features are in the top 20 most important features
- is_self_transfer has zero importance (removed)

---

## 6. MODEL PERFORMANCE VALIDATION

### 6.1 Model Performance Comparison

**Objective:** Verify that the 57-feature set improves model performance.

**Validation Steps:**
1. Train models on the 57-feature set using the PRIMARY split
2. Compare with Stage 12 baseline (34 features)
3. Verify that suspicious recall improves
4. Verify that super_suspicious recall improves
5. Verify that macro F1 improves or is maintained
6. Verify that overfitting is reduced (train-test gap)

**Acceptance Criteria:**
- Suspicious recall improves from <0.07 to >0.20
- Super-suspicious recall improves from <0.31 to >0.40
- Macro F1 improves from 0.44 to >0.50
- Train-test gap for Random Forest reduces from 0.56 to <0.40

---

## 7. WITHIN-CLASS SEPARATION VALIDATION

### 7.1 Scenario Separation Analysis

**Objective:** Verify that within-class scenario separation improves.

**Validation Steps:**
1. Compute Cohen's d between suspicious scenarios using the 57-feature set
2. Compare with Stage 13 baseline (avg Cohen's d ~0.06)
3. Verify that within-class separation improves
4. Compute Cohen's d between severe scenarios using the 57-feature set
5. Verify that severe scenario separation improves

**Acceptance Criteria:**
- Suspicious scenario separation: avg Cohen's d > 0.3 (improvement from ~0.06)
- Severe scenario separation: avg Cohen's d > 0.5 (improvement from ~0.09)

---

## 8. FEATURE REDUNDANCY VALIDATION

### 8.1 Feature Redundancy Analysis

**Objective:** Verify that features are not redundant.

**Validation Steps:**
1. Compute correlation matrix for all 57 features
2. Identify highly correlated features (correlation > 0.9)
3. Verify that no new features are redundant with existing features
4. Verify that no new features are redundant with each other
5. Document any redundant features for potential removal

**Acceptance Criteria:**
- No new features have correlation > 0.9 with existing features
- No new features have correlation > 0.9 with each other
- Redundant features are documented

---

## 9. HIGH-RISK-COUNTRY LIMITATION VALIDATION

### 9.1 Limitation Acknowledgment

**Objective:** Acknowledge that high_risk_country cannot be detected.

**Validation Steps:**
1. Verify that no features detect high_risk_country
2. Document the limitation in the validation report
3. Recommend generator modification as a future improvement

**Acceptance Criteria:**
- high_risk_country observability remains NONE
- Limitation is documented
- Generator modification is recommended

---

## 10. ARTIFACT VALIDATION

### 10.1 Artifact Integrity

**Objective:** Verify that Stage 14 artifacts are complete and correct.

**Validation Steps:**
1. Verify that all Stage 14 artifacts are created
2. Verify that all artifacts are consistent with each other
3. Verify that no Stage 1-13 artifacts are modified
4. Verify that no Stage 11 dataset/labels are modified
5. Verify that no Stage 11 generator is modified

**Acceptance Criteria:**
- All Stage 14 artifacts are created
- Artifacts are consistent
- No Stage 1-13 artifacts are modified
- No Stage 11 dataset/labels are modified
- No Stage 11 generator is modified

---

## 11. STAGE 15 IMPLEMENTATION PLAN

### 11.1 Implementation Order

1. **Feature Extraction Implementation**
   - Implement 25 new candidate features
   - Remove is_self_transfer
   - Preserve 33 existing features
   - Validate feature extraction

2. **Temporal Safety Validation**
   - Verify temporal safety for all features
   - Fix any temporal safety issues

3. **Feature Extraction on Stage 11 Dataset**
   - Extract 57 features for all 10,000 transactions
   - Save to ml_stage15_features.csv

4. **Model Training**
   - Train models on 57-feature set using PRIMARY split
   - Compare with Stage 12 baseline

5. **Scenario Observability Validation**
   - Compute Cohen's d for all scenarios
   - Compare with Stage 13 baseline

6. **Model Performance Validation**
   - Compare model performance with Stage 12 baseline
   - Verify improvements

7. **Validation Report**
   - Document all validation results
   - Create Stage 15 report

---

## 12. STOP CONDITIONS

### 12.1 Critical Stop Conditions

If any of the following occur, STOP and report to the user:

1. **Temporal Safety Violation:** Any feature uses future information
2. **Feature-Label Leakage:** Any feature uses ground-truth labels
3. **NaN/Infinite Values:** Any feature produces NaN or infinite values
4. **Feature Extraction Failure:** Any feature cannot be computed
5. **Performance Degradation:** Model performance degrades significantly

### 12.2 Warning Conditions

If any of the following occur, WARN the user but continue:

1. **High Correlation:** Features have correlation > 0.9
2. **Low Importance:** New features have zero importance
3. **No Improvement:** Scenario observability does not improve
4. **Overfitting:** Train-test gap increases

---

## 13. SUCCESS CRITERIA

### 13.1 Stage 15 Success Criteria

Stage 15 is considered successful if:

1. All 57 features are implemented correctly
2. All features are temporally safe
3. All features are independent of labels
4. Scenario observability improves for 5/6 scenarios (excluding high_risk_country)
5. Model performance improves (suspicious recall, super-suspicious recall, macro F1)
6. No Stage 1-13 artifacts are modified
7. No Stage 11 dataset/labels are modified
8. No Stage 11 generator is modified

### 13.2 Stage 15 Failure Criteria

Stage 15 is considered failed if:

1. Any feature is temporally unsafe
2. Any feature uses ground-truth labels
3. Scenario observability does not improve
4. Model performance degrades
5. Any Stage 1-13 artifact is modified
6. Any Stage 11 dataset/label is modified
7. Any Stage 11 generator is modified

---

## 14. CONCLUSION

This validation plan ensures that the proposed 57-feature specification is correctly implemented, temporally safe, and actually improves scenario observability. The plan defines clear acceptance criteria, stop conditions, and success criteria for Stage 15.

**Next Step:** Proceed to Stage 15 implementation and validation.
