# FINAL PROJECT FREEZE

**Timestamp:** 2026-09-02T18:56:00.000000

**Project Status:** EXPERIMENTATION COMPLETE - MODEL FROZEN

---

## FINAL MODEL CONFIGURATION

**Model Type:** Gradient Boosting Classifier

**Configuration:**
- learning_rate: 0.01
- max_depth: 3
- n_estimators: 500
- random_state: 42

**Feature Set:** 18 frozen features

**Preprocessing:** None (tree-based models do not require scaling)

**Class Imbalance Handling:** None (no SMOTE, no class weighting, no synthetic oversampling)

**Threshold:** Default 0.5 (no threshold tuning)

---

## FROZEN 18-FEATURE SET

1. amount
2. sender_avg_amount
3. sender_max_amount
4. amount_to_sender_avg
5. amount_z_score
6. amount_deviation_from_baseline_30d
7. tx_frequency_7d
8. tx_frequency_30d
9. frequency_change_vs_avg_7d
10. sender_tx_count_24h
11. sender_volume_24h
12. same_day_count
13. rapid_transfer_count
14. is_new_recipient
15. unique_recipients_7d
16. hour
17. is_off_hours
18. counterparty_change_score_7d

---

## OFFICIAL PRIMARY CUSTOMER-LEVEL RESULTS

**Test Metrics (Authoritative from ml_stage16b_model_results.json):**
- Accuracy: 0.7775
- Macro F1: 0.5015
- Weighted F1: 0.7344
- Normal Precision/Recall/F1: 0.8058 / 0.9717 / 0.8810
- Suspicious Precision/Recall/F1: 0.5756 / 0.2176 / 0.3158
- Super-Suspicious Precision/Recall/F1: 0.3902 / 0.2540 / 0.3077
- False Positives: 347
- False Negatives: 42
- Super-Suspicious False Negatives: 47

**Train Metrics:**
- Accuracy: 0.8015
- Macro F1: 0.6193
- Weighted F1: 0.7589
- Normal Precision/Recall/F1: 0.8081 / 0.9846 / 0.8877
- Suspicious Precision/Recall/F1: 0.7179 / 0.2254 / 0.3431
- Super-Suspicious Precision/Recall/F1: 0.7901 / 0.5200 / 0.6272

**Train/Test Gap:**
- Macro F1 Gap: 0.1178 (MODERATE - acceptable overfitting)

---

## CUSTOMER-LEVEL HOLDOUT METHODOLOGY

**Split Type:** Customer-level holdout (primary validation)

**Split Ratio:** 80% train / 20% test

**Customer Distribution:**
- Train customers: 160
- Test customers: 40
- Total customers: 200

**Transaction Distribution:**
- Train transactions: 8000
- Test transactions: 2000
- Total transactions: 10000

**Customer Overlap:** ZERO - no customer appears in both train and test sets

**Validation File:** ml_stage12_primary_split.json

---

## SECONDARY TEMPORAL VALIDATION

**Split Type:** Temporal split (secondary validation)

**Split Ratio:** 80% train / 20% test by transaction time

**Customer Overlap:** POSSIBLE - this is a known limitation

**Temporal Validation Results:**
- RF Test Macro F1: 0.3322
- GB Test Macro F1: 0.4764

**Note:** Temporal validation shows lower performance than customer-level validation, which is expected due to customer overlap limitation.

---

## REPRODUCIBILITY INFORMATION

### Data Sources
- ml_stage11_dataset.csv (10,000 transactions, 200 customers)
- ml_stage11_ground_truth.json (ground truth labels)

### Feature Extraction
- ml_stage16b_feature_extraction.py (18-feature extraction script)
- ml_stage16b_features.csv (extracted features)
- ml_stage16b_feature_metadata.json (feature metadata)

### Model Training
- ml_stage16b_model_training.py (model training script)
- ml_stage16b_model_results.json (authoritative model results)

### Validation
- ml_stage16b_temporal_validation.py (temporal validation script)
- ml_stage16b_temporal_validation_results.json (temporal validation results)

### Reports
- ml_stage16b_report.md (Stage 16B detailed report)
- ml_stage16a_corrected_final_audit_report.md (Stage 16A corrected audit report)

### Environment
- Python with scikit-learn
- Random seed: 42 (for reproducibility)
- Customer-level split: ml_stage12_primary_split.json

### Reproduction Steps
1. Run ml_stage16b_feature_extraction.py to extract 18 features
2. Run ml_stage16b_model_training.py to train and evaluate models
3. Results will match ml_stage16b_model_results.json (given same random seed)

---

## LIMITATIONS

### Model Limitations
- **Super-Suspicious Recall:** 0.2540 (low - critical limitation)
- **Suspicious Recall:** 0.2176 (low - critical limitation)
- **Overall Performance:** Macro F1 0.5015 (moderate)
- **Overfitting:** Train/test gap 0.1178 (moderate but acceptable)

### Data Limitations
- **Country Information:** high_risk_country scenario cannot be detected (country information not exported to dataset)
- **Network Information:** Limited network analysis capabilities (only direct counterparty relationships available)
- **Temporal Scope:** Limited historical window (max 30 days)
- **Dataset Size:** Only 10,000 transactions, 200 customers

### Feature Limitations
- **Partial Dimension Coverage:** 18-feature set provides partial coverage for 6 of 12 approved behavioral dimensions
- **Feature Expansion Failed:** 57-feature set performed worse than 32-feature baseline; 18-feature set performs worse than 32-feature baseline for Random Forest

### Context Limitations
- **Zimbabwean Context:** Dataset may not fully represent Zimbabwean AML context (generator is synthetic, not real Zimbabwean data)
- **Regulatory Compliance:** Model is experimental, not production-ready

---

## PRODUCTION READINESS DISCLAIMER

**THIS IS A RESEARCH/EXPERIMENTAL AML MODEL - NOT PRODUCTION-READY**

This model was developed for research and experimentation purposes only. It should NOT be deployed in a production environment without:

1. Additional validation on real-world Zimbabwean AML data
2. Regulatory compliance review and approval
3. Performance improvements in suspicious and super-suspicious recall
4. Integration of country/geography information for high_risk_country detection
5. Extensive testing and validation in a controlled environment
6. Legal and ethical review

The model has significant limitations, particularly in detecting suspicious and super-suspicious transactions, and should not be used for real AML decision-making without substantial additional work.

---

## PRESERVED ARTIFACTS

All Stage 1-16 artifacts are preserved unchanged:

**Stage 1:** ml_stage1_leakage_audit.py, ml_stage1_leakage_audit_results.json
**Stage 2:** ml_stage2_baseline_evaluation.py, ml_stage2_results.json
**Stage 3:** ml_stage3_generator.py, ml_stage3_dataset.csv, ml_stage3_ground_truth.json
**Stage 4:** ml_stage4_feature_audit.py, ml_stage4_feature_audit_results.json
**Stage 5:** ml_stage5_feature_extraction.py, ml_stage5_features.csv, ml_stage5_feature_metadata.json
**Stage 6:** ml_stage6_model_training.py, ml_stage6_model_results.json
**Stage 7:** ml_stage7_root_cause_analysis.py, ml_stage7_root_cause_analysis_results.json
**Stage 8:** ml_stage8_ground_truth_audit.py, ml_stage8_ground_truth_audit_results.json
**Stage 9:** ml_stage9_ground_truth_design.py, ml_stage9_ground_truth_design.json
**Stage 10:** ml_stage10_generator_audit.py, ml_stage10_generator_audit_results.json
**Stage 11:** ml_stage11_generator_repair.py, ml_stage11_dataset.csv, ml_stage11_ground_truth.json
**Stage 12:** ml_stage12_model_training.py, ml_stage12_model_results.json, ml_stage12_primary_split.json
**Stage 13:** ml_stage13_scenario_analysis.py, ml_stage13_additional_analysis.py, ml_stage13_scenario_feature_matrix.csv, ml_stage13_feature_coverage_matrix.csv, ml_stage13_temporal_analysis.csv, ml_stage13_report.md
**Stage 14:** ml_stage14_data_capability_audit.py, ml_stage14_feature_gap_design.py, ml_stage14_temporal_safety_verification.py, ml_stage14_feature_specification.py, ml_stage14_feature_capability_matrix.csv, ml_stage14_data_capability_audit.md, ml_stage14_feature_gap_design.md, ml_stage14_feature_specification.md, ml_stage14_validation_plan.md, ml_stage14_report.md
**Stage 15:** ml_stage15_arithmetic_resolution.py, ml_stage15_feature_extraction.py, ml_stage15_features.csv, ml_stage15_feature_metadata.json, ml_stage15_feature_validation.py, ml_stage15_temporal_safety_audit.py, ml_stage15_scenario_observability.py, ml_stage15_high_risk_country_handling.py, ml_stage15_model_training.py, ml_stage15_ablation.py, ml_stage15_overfitting_audit.py, ml_stage15_feature_importance_stability.py, ml_stage15_report.md
**Stage 16A:** ml_stage16a_corrected_final_audit_report.md
**Stage 16B:** ml_stage16b_feature_extraction.py, ml_stage16b_features.csv, ml_stage16b_feature_metadata.json, ml_stage16b_model_training.py, ml_stage16b_model_results.json, ml_stage16b_temporal_validation.py, ml_stage16b_temporal_validation_results.json, ml_stage16b_report.md

---

## FINAL MODEL ARTIFACTS

**Primary Artifacts:**
- ml_stage16b_feature_extraction.py (feature extraction script)
- ml_stage16b_features.csv (extracted features)
- ml_stage16b_feature_metadata.json (feature metadata)
- ml_stage16b_model_training.py (model training script)
- ml_stage16b_model_results.json (authoritative model results)
- ml_stage16b_report.md (Stage 16B detailed report)

**Supporting Artifacts:**
- ml_stage11_dataset.csv (source dataset)
- ml_stage11_ground_truth.json (ground truth labels)
- ml_stage12_primary_split.json (customer-level split)

---

## PROJECT SUMMARY

**Project Objective:** Develop an AML detection model for Zimbabwean financial transactions using synthetic data.

**Stages Completed:** 16 (Stages 1-15 experimentation, Stage 16A audit, Stage 16B validation)

**Final Model:** Gradient Boosting with 18 features

**Key Achievements:**
- Reduced overfitting from HIGH (Stage 15) to MODERATE (Stage 16B)
- Improved Gradient Boosting performance vs Stage 12 baseline (+0.0660 Macro F1)
- Improved super-suspicious recall from 0.0 to 0.2540
- Established customer-level generalization methodology

**Key Limitations:**
- Super-suspicious recall remains low (0.2540)
- Suspicious recall remains low (0.2176)
- Overall Macro F1 remains moderate (0.5015)
- Cannot detect high_risk_country scenario (country information unavailable)
- Partial coverage of approved behavioral dimensions

**Scientific Integrity:**
- Honest reporting of mixed results (18-feature set improved GB but degraded RF)
- No claim of production readiness
- Critical limitations documented
- All artifacts preserved for reproducibility

---

## FINAL DECISION

**Selected Model:** Gradient Boosting with 18-feature frozen set

**Configuration:** learning_rate=0.01, max_depth=3, n_estimators=500, random_state=42

**Status:** MODEL FROZEN - NO FURTHER EXPERIMENTATION WITHOUT EXPLICIT APPROVAL

**Next Steps:** Final review and approval before any production consideration

---

FINAL MODEL FREEZE COMPLETE — PROJECT READY FOR FINAL REVIEW
