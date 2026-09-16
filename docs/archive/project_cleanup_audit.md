# PROJECT CLEANUP AUDIT

**Timestamp:** 2026-09-02T19:02:00.000000

**Total Files Scanned:** 121 files + directories

---

## CLASSIFICATION SUMMARY

### KEEP — REQUIRED: 52 files
Files required for running the AML system, final frozen model, reproducibility, and configuration.

### KEEP — HISTORICAL/REFERENCE: 57 files  
Stage 1-16 artifacts for scientific audit trail and project history.

### REMOVE — NON-ESSENTIAL: 12 files
Files created for progress communication, temporary analysis, debugging, or scratch work.

---

## KEEP — REQUIRED (52 files)

### Application/System Code (20 files)
- ai_core.py
- alerts.py
- aml_rules.py
- behavioral_profiling.py
- config.py
- database.py
- messaging.py
- screening.py
- security.py
- server.py
- transactions.py
- users.py
- utils.py
- query_transactions.py
- realtime.py
- reports.py
- transaction_simulation.py
- debug_transactions.py
- find_db.py
- test_confidence_fix.py
- test_smtp.py

### Configuration/Dependencies (7 files)
- .env
- .env.example
- Dockerfile
- Procfile
- railway.json
- requirements.txt
- README.md

### Database (1 file)
- aml.db

### Final Model Artifacts (2 files)
- aml_ai_model.pkl (final model)
- aml_ai_model_meta.json (model metadata)

### Stage 16B Final Artifacts (8 files)
- ml_stage16b_feature_extraction.py
- ml_stage16b_features.csv
- ml_stage16b_feature_metadata.json
- ml_stage16b_model_training.py
- ml_stage16b_model_results.json
- ml_stage16b_temporal_validation.py
- ml_stage16b_temporal_validation_results.json
- ml_stage16b_report.md

### Supporting Final Artifacts (3 files)
- ml_stage11_dataset.csv
- ml_stage11_ground_truth.json
- ml_stage12_primary_split.json

### Stage 16A Audit (1 file)
- ml_stage16a_corrected_final_audit_report.md

### Final Project Freeze (1 file)
- final_project_freeze.md

### Static/Templates (9 files)
- static/react-dashboard.js
- static/style.css
- templates/admin_dashboard.html
- templates/alert_detail.html
- templates/base.html
- templates/compliance_dashboard.html
- templates/customer_dashboard.html
- templates/error.html
- templates/forgot_password.html
- templates/login.html
- templates/messages.html
- templates/register.html
- templates/reports.html
- templates/reset_password.html

---

## KEEP — HISTORICAL/REFERENCE (57 files)

### Stage 1: Leakage Audit (3 files)
- ml_audit_feature_analysis.py
- ml_audit_inspect_model.py
- ml_audit_simulation_analysis.py
- ml_audit_stage1_report.md

### Stage 2: Baseline Evaluation (4 files)
- ml_baseline_dataset.json
- ml_baseline_dataset_metadata.json
- ml_baseline_evaluate.py
- ml_baseline_generate_dataset.py
- ml_baseline_results.json
- ml_baseline_stage2_report.md

### Stage 3: Dataset and Labeling Redesign (9 files)
- ml_dataset_stage3_report.md
- ml_stage3_dataset.csv
- ml_stage3_dataset_test.csv
- ml_stage3_generate_full.py
- ml_stage3_generator.py
- ml_stage3_ground_truth.json
- ml_stage3_ground_truth_test.json
- ml_stage3_metadata.json
- ml_stage3_metadata_test.json

### Stage 4: Feature Engineering Audit (1 file)
- ml_feature_engineering_stage4_report.md
- ml_stage4_feature_audit.py

### Stage 5: 34-Feature Implementation (4 files)
- ml_stage5_feature_extraction.py
- ml_stage5_features.csv
- ml_stage5_report.md
- ml_stage5_validation.py

### Stage 6: Model Training and Evaluation (6 files)
- ml_stage6_data_inspection.py
- ml_stage6_leakage_audit.py
- ml_stage6_report.md
- ml_stage6_results.json
- ml_stage6_rf_model.pkl
- ml_stage6_scaler.pkl
- ml_stage6_training.py

### Stage 7: Root-Cause Analysis (3 files)
- ml_stage7_report.md
- ml_stage7_signal_analysis.py
- ml_stage7_signal_results.json

### Stage 8: Ground-Truth Audit (4 files)
- ml_stage8_label_audit.py
- ml_stage8_label_audit_results.json
- ml_stage8_report.md
- ml_stage8_verification.py

### Stage 9: Ground-Truth Design (3 files)
- ml_stage9_ground_truth_design.py
- ml_stage9_ground_truth_design_report.md
- ml_stage9_ground_truth_design_results.json

### Stage 10: Generator Behavior Audit (3 files)
- ml_stage10_generator_behavior_audit.py
- ml_stage10_generator_behavior_audit_report.md
- ml_stage10_generator_behavior_audit_results.json

### Stage 11: Generator Repair and Dataset (10 files)
- ml_stage11_dataset.csv
- ml_stage11_feature_extraction.py
- ml_stage11_features.csv
- ml_stage11_generator_repair.py
- ml_stage11_ground_truth.json
- ml_stage11_implementation_plan.md
- ml_stage11_metadata.json
- ml_stage11_report.md
- ml_stage11_validation.py
- ml_stage11_validation_results.json

### Stage 12: Model Training and Generalization (9 files)
- ml_stage12_analysis.py
- ml_stage12_analysis_results.json
- ml_stage12_model_results.json
- ml_stage12_model_training.py
- ml_stage12_pretraining_audit.py
- ml_stage12_pretraining_audit_report.md
- ml_stage12_pretraining_audit_results.json
- ml_stage12_primary_split.json
- ml_stage12_report.md
- ml_stage12_secondary_split.json
- ml_stage12_split_audit.py
- ml_stage12_split_audit_results.json
- ml_stage12_split_implementation.py

### Stage 13: Scenario Analysis (6 files)
- ml_stage13_additional_analysis.py
- ml_stage13_additional_analysis_results.json
- ml_stage13_feature_coverage_matrix.csv
- ml_stage13_report.md
- ml_stage13_scenario_analysis.py
- ml_stage13_scenario_analysis_results.json
- ml_stage13_scenario_feature_matrix.csv
- ml_stage13_temporal_analysis.csv

### Stage 14: Feature Engineering Design (10 files)
- ml_stage14_data_capability_audit.md
- ml_stage14_data_capability_audit.py
- ml_stage14_data_capability_audit_results.json
- ml_stage14_feature_capability_matrix.csv
- ml_stage14_feature_gap_design.md
- ml_stage14_feature_gap_design.py
- ml_stage14_feature_gap_design_results.json
- ml_stage14_feature_specification.md
- ml_stage14_feature_specification.py
- ml_stage14_feature_specification_results.json
- ml_stage14_report.md
- ml_stage14_temporal_safety_verification.py
- ml_stage14_temporal_safety_verification_results.json
- ml_stage14_validation_plan.md

### Stage 15: Feature Implementation (18 files)
- ml_stage15_ablation.py
- ml_stage15_ablation_results.csv
- ml_stage15_ablation_results.json
- ml_stage15_arithmetic_resolution.json
- ml_stage15_arithmetic_resolution.py
- ml_stage15_feature_extraction.py
- ml_stage15_feature_importance_stability.py
- ml_stage15_feature_importance_stability_results.json
- ml_stage15_feature_metadata.json
- ml_stage15_feature_validation.py
- ml_stage15_feature_validation_results.json
- ml_stage15_features.csv
- ml_stage15_high_risk_country_handling.py
- ml_stage15_high_risk_country_handling_results.json
- ml_stage15_model_results.json
- ml_stage15_model_training.py
- ml_stage15_overfitting_audit.py
- ml_stage15_overfitting_audit_results.json
- ml_stage15_report.md
- ml_stage15_scenario_observability.csv
- ml_stage15_scenario_observability.py
- ml_stage15_scenario_observability_results.json
- ml_stage15_temporal_safety_audit.py
- ml_stage15_temporal_safety_audit_results.json

### Stage 16A: Final Audit (1 file)
- ml_stage16a_final_project_audit_report.md (superseded by corrected version)

---

## REMOVE — NON-ESSENTIAL (12 files)

### Academic/Documentation Files (4 files)
- Chapter 1 dissertation finale.docx
  - Reason: Academic dissertation document, not required for AML system
- Chapter 3.docx
  - Reason: Academic dissertation document, not required for AML system
- Chapter_3_Diagrams_Mermaid.md
  - Reason: Academic dissertation diagrams, not required for AML system
- Level 4 Guides. Hardware_ML Based.docx
  - Reason: Academic guide document, not required for AML system

### Temporary Text Files (3 files)
- chapter1.txt
  - Reason: Temporary text file, appears to be draft content
- chapter1_revised.txt
  - Reason: Temporary text file, appears to be draft content
- chapter1_temp.txt
  - Reason: Temporary text file, appears to be draft content

### Server Log Files (2 files)
- server.err.log
  - Reason: Server error log file, temporary runtime artifact
- server.out.log
  - Reason: Server output log file, temporary runtime artifact

### Python Cache Directories (3 directories)
- __pycache__/
  - Reason: Python cache directory, automatically regenerated
- .pytest_cache/
  - Reason: Pytest cache directory, automatically regenerated
- .venv/
  - Reason: Virtual environment directory, can be regenerated from requirements.txt

---

## UNCERTAIN FILES REQUIRING APPROVAL (0 files)

No uncertain files identified. All files have been classified with clear rationale.

---

## DEPENDENCY VERIFICATION

### Checked References:
- No Stage 16B artifacts reference the proposed deletion files
- No application code references the proposed deletion files
- No final model dependencies reference the proposed deletion files
- No reproducibility scripts reference the proposed deletion files

### Final Model Dependencies:
- Confirmed: ml_stage16b_model_results.json is authoritative
- Confirmed: ml_stage16b_feature_extraction.py is required
- Confirmed: ml_stage11_dataset.csv is required
- Confirmed: ml_stage11_ground_truth.json is required
- Confirmed: ml_stage12_primary_split.json is required

### Application Dependencies:
- Confirmed: server.py, ai_core.py, database.py are required
- Confirmed: aml.db is required
- Confirmed: aml_ai_model.pkl is required
- Confirmed: static/ and templates/ are required for UI

---

## CONFIRMATION

**No final model/system dependencies are affected by proposed deletions.**

**All Stage 1-16 artifacts are preserved.**

**All final frozen model artifacts are preserved.**

**All application/system code is preserved.**

**All configuration/dependencies are preserved.**

---

## PROPOSED DELETION SUMMARY

**Total Files to Delete:** 12 files + 3 directories

**Files:**
1. Chapter 1 dissertation finale.docx
2. Chapter 3.docx
3. Chapter_3_Diagrams_Mermaid.md
4. Level 4 Guides. Hardware_ML Based.docx
5. chapter1.txt
6. chapter1_revised.txt
7. chapter1_temp.txt
8. server.err.log
9. server.out.log

**Directories:**
1. __pycache__/
2. .pytest_cache/
3. .venv/

---

## NOTES

- ml_stage16a_final_project_audit_report.md is superseded by ml_stage16a_corrected_final_audit_report.md, but both are preserved as historical artifacts
- All .git/ directory and contents are preserved (version control)
- All .gitignore is preserved (version control configuration)
- All Docker-related files are preserved (deployment)

---

PROJECT CLEANUP AUDIT COMPLETE — WAITING FOR APPROVAL TO DELETE NON-ESSENTIAL FILES.
