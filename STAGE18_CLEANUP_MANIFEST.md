# STAGE 18 — REPOSITORY CLEANUP MANIFEST

**Date:** 2026-09-16  
**Stage:** 18 — Comprehensive Project Cleanup, Archive and Repository Organization  
**Status:** PRE-CLEANUP INVENTORY

---

## 1. Repository Inventory Summary

### Before Cleanup
- **Total Files:** 340+
- **Python Files:** 140 (excluding .venv)
- **Markdown Files:** 56
- **JSON/CSV/TXT/SQL Files:** 120+
- **Model Files (.pkl/.joblib):** 8
- **JavaScript/HTML/CSS Files:** 16
- **Test Files:** 19
- **Cache/Temp Directories:** .pytest_cache, __pycache__, .venv

---

## 2. File Classification

### A. FINAL ACTIVE APPLICATION (KEEP)
**Required by the current EcoCash application:**

**Core Application:**
- server.py — Flask application server
- database.py — Database abstraction layer
- transactions.py — Transaction processing
- alerts.py — Alert management
- agents.py — Agent management
- transaction_simulation.py — Transaction simulation (updated Stage 17E)
- users.py — User management
- utils.py — Utility functions

**AI Pipeline (Stage 13 + Stage 14):**
- ai_stage13_features.py — Stage 13 feature service (30 features)
- ai_stage14_model.py — Stage 14 model service

**Supporting Modules:**
- security.py — Security functions
- screening.py — Entity screening
- messaging.py — Messaging system
- realtime.py — Real-time event broker
- config.py — Application configuration
- aml_rules.py — AML rule engine
- behavioral_profiling.py — Behavioral profiling
- reports.py — Report generation

**Frontend:**
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
- static/react-dashboard.js
- static/style.css

**Configuration:**
- requirements.txt
- .env.example

**Status:** ALL KEEP — Essential for application functionality

---

### B. FINAL ML / RESEARCH ARTIFACTS (KEEP/ARCHIVE)
**Required to preserve the final research implementation:**

**Authoritative Production Model:**
- ml/stage14/stage14_frozen_model.pkl — **KEEP** (Active model)

**Official Research Dataset:**
- data/ecocash_aml_synthetic_100k_v1/transactions.csv — **KEEP**
- data/ecocash_aml_synthetic_100k_v1/ground_truth.json — **KEEP**
- data/ecocash_aml_synthetic_100k_v1/generation_manifest.json — **KEEP**
- data/ecocash_aml_synthetic_100k_v1/entity_metadata.json — **KEEP**
- data/ecocash_aml_synthetic_100k_v1/features/feature_names.json — **KEEP**

**Stage 14 Model Results:**
- reports/ml_stages/stage14_model_training_and_evaluation_corrected_2026-09-15.md — **KEEP**
- reports/ml_stages/stage14_model_training_and_evaluation_corrected_2026-09-15.json — **KEEP**

**Stage 15 XGBoost Comparison:**
- reports/ml_stages/stage15_xgboost_model_comparison_2026-09-15.md — **KEEP**
- reports/ml_stages/stage15_xgboost_model_comparison_2026-09-15.json — **KEEP**

**Stage 13 Feature Documentation:**
- reports/ml_stages/stage13a_feature_extraction_implementation_audit_2026-09-15.md — **KEEP**

**Experimental Models (Archive):**
- ml/stage16b/stage16b_expanded_model.pkl — **ARCHIVE** (Stage 16B experiment)
- aml_ai_model.pkl — **ARCHIVE** (Legacy model, not active)
- aml_ai_model_stage21.pkl — **ARCHIVE** (Stage 21 experiment)
- aml_label_encoder.pkl — **ARCHIVE** (Legacy encoder)
- aml_label_encoder_stage21.pkl — **ARCHIVE** (Stage 21 experiment)
- ml_stage6_rf_model.pkl — **ARCHIVE** (Stage 6 experiment)
- ml_stage6_scaler.pkl — **ARCHIVE** (Stage 6 experiment)

**Status:** Production model/dataset KEEP, experiments ARCHIVE

---

### C. FINAL TESTS (KEEP)
**Tests that verify the current system:**

**Stage 17 Tests (Current Architecture):**
- test_stage17e_simulation_alignment.py — **KEEP** (28 tests, 100% pass)
- test_stage17e_end_to_end.py — **KEEP** (End-to-end test)
- test_stage17b_feature_service.py — **KEEP**
- test_stage17c_model_integration.py — **KEEP**
- test_stage17d_integration.py — **KEEP**

**Application Tests:**
- tests/test_aml_rules.py — **KEEP**
- tests/test_app.py — **KEEP**
- tests/test_alert_navigation.py — **KEEP**

**Legacy Tests (Archive):**
- test_agent_implementation.py — **ARCHIVE**
- test_flask_startup.py — **ARCHIVE**
- test_model_integration.py — **ARCHIVE**
- test_smtp.py — **ARCHIVE**
- test_stage7_api_integration.py — **ARCHIVE**
- test_stage7_mysql_verification.py — **ARCHIVE**
- test_stage8_gap_closure.py — **ARCHIVE**
- test_stage8_regression.py — **ARCHIVE**
- test_stage8_runtime.py — **ARCHIVE**

**Status:** Current architecture tests KEEP, legacy tests ARCHIVE

---

### D. FINAL DOCUMENTATION (CONSOLIDATE)
**Documentation that should remain in the main repository:**

**Main Documentation:**
- README.md — **KEEP** (Update with final architecture)
- reports/README.md — **KEEP** (Organization guide)
- reports/stage17e_transaction_simulation_alignment_2026-09-15.md — **KEEP** (Current report)

**Historical Reports (Archive):**
- All stage_*.md files (Stage 1-9 migration reports) — **ARCHIVE**
- All ml_*.md files (ML development reports) — **ARCHIVE**
- All ml_stage*.md files (ML stage reports) — **ARCHIVE**
- Root-level audit reports — **ARCHIVE**

**Status:** Main documentation KEEP, historical reports ARCHIVE

---

### E. HISTORICAL / ARCHIVE MATERIAL (ARCHIVE)
**Development reports and research evidence:**

**ML Development Reports (Already Organized):**
- reports/ml_stages/ — **KEEP** (Already organized)
- reports/integration_stages/ — **KEEP** (Already organized)
- reports/archive/ — **KEEP** (Already organized)

**Root-Level Historical Reports (Move to Archive):**
- stage_1_frontend_ecocash_migration_report.md
- stage_2_dashboard_transaction_migration_report.md
- stage_3_alerts_investigation_migration_report.md
- stage_4_backend_domain_migration_report.md
- stage_5_database_audit_report.md
- stage_6_agent_implementation_report.md
- stage_7_api_integration_report.md
- stage_8_completion_testing_report.md
- stage_8_final_gap_closure_report.md
- stage_8_regression_testing_report.md
- stage_9_final_migration_review_report.md

**Root-Level ML Reports (Move to Archive):**
- ml_audit_stage1_report.md
- ml_baseline_stage2_report.md
- ml_dataset_stage3_report.md
- ml_feature_engineering_stage4_report.md
- ml_model_improvement_stage_17_report.md
- ml_stage10_generator_behavior_audit_report.md
- ml_stage11_implementation_plan.md
- ml_stage11_report.md
- ml_stage12_pretraining_audit_report.md
- ml_stage12_report.md
- ml_stage13_report.md
- ml_stage14_report.md
- ml_stage14_data_capability_audit.md
- ml_stage14_feature_gap_design.md
- ml_stage14_feature_specification.md
- ml_stage14_validation_plan.md
- ml_stage15_report.md
- ml_stage16a_corrected_final_audit_report.md
- ml_stage16a_final_project_audit_report.md
- ml_stage16b_report.md
- ml_stage18_aml_requirement_to_feature_audit_report.md
- ml_stage19_smote_xgboost_report.md
- ml_stage20_dataset_learnability_report.md
- ml_stage20_root_cause_and_chapter1_alignment_report.md
- ml_stage21_corrective_training_and_evaluation_report.md
- ml_stage22_stage21_validation_and_generalization_audit.md
- ml_stage23_dataset_redesign_and_quality_audit.md
- ml_stage5_report.md
- ml_stage6_report.md
- ml_stage7_report.md
- ml_stage8_report.md
- ml_stage9_ground_truth_design_report.md

**Other Historical Reports (Move to Archive):**
- final_acceptance_test_report.md
- final_project_freeze.md
- ml_class_weight_experiment_report.md
- ml_class_weight_integrity_verification_report.md
- ml_results_integrity_verification_report.md
- ml_smote_experiment_stage18_report.md
- model_integration_diagnostic_report.md
- mysql_reset_readiness_report.md
- project_cleanup_audit.md
- targeted_verification_report.md
- threshold_fix_verification_report.md

**Status:** All organized in existing archive structure

---

### F. OBSOLETE / SAFE TO REMOVE
**Files confirmed obsolete, duplicated, temporary, or unused:**

**Legacy Test Databases:**
- test_aml.db — **REMOVE** (Test database, no longer needed)
- test_aml_stage6.db — **REMOVE** (Test database, no longer needed)

**Temporary/Debug Scripts:**
- acceptance_test.py — **ARCHIVE** (Legacy acceptance test)
- comprehensive_diagnostic.py — **ARCHIVE** (Debug script)
- debug_ai_predictions.py — **ARCHIVE** (Debug script)
- debug_transactions.py — **ARCHIVE** (Debug script)
- extract_chapter2.py — **ARCHIVE** (Documentation extraction)
- convert_to_docx.py — **ARCHIVE** (Documentation conversion)
- create_panel1_presentation.py — **ARCHIVE** (Presentation generation)
- find_db.py — **ARCHIVE** (Debug utility)
- query_transactions.py — **ARCHIVE** (Debug utility)
- targeted_verification.py — **ARCHIVE** (Legacy verification)

**Cleanup Scripts:**
- cleanup_test_agents.py — **ARCHIVE** (One-time cleanup)
- reset_database.py — **KEEP** (May be needed for admin)

**Archive Files Already Processed:**
- reports/archive/_execute_table_reset.py — **KEEP** (Already archived)
- reports/archive/_mysql_table_reset_execute.py — **KEEP** (Already archived)
- reports/archive/_post_reset_regression.py — **KEEP** (Already archived)
- reports/archive/mysql_*.txt — **KEEP** (Already archived)

**Presentation Files:**
- 1_Fungurayi_Prominance_Kahlari_Ashton.pptx — **ARCHIVE** (Presentation)
- Chapter_2.docx — **ARCHIVE** (Thesis chapter)
- Chapter_2_Revised.docx — **ARCHIVE** (Thesis chapter)
- Chapter_2_Revised.txt — **ARCHIVE** (Text extraction)
- chapter2_extracted.txt — **ARCHIVE** (Text extraction)

**Status:** Safe to archive or remove

---

### G. LEGACY AML SYSTEM
**Legacy banking AML material status:**

**Legacy Files:**
- aml_ai_model.pkl — **ARCHIVE** (Not active, but keep for historical reference)
- ai_core.py — **KEEP** (Used for behavioral profiling, not main AML decisions)

**Usage Analysis:**
- server.py imports from ai_core but only for behavioral profiling
- Main AML decisions use Stage 13 + Stage 14
- Legacy model is NOT active in prediction path

**Status:** Archive legacy model, keep ai_core.py for behavioral profiling

---

### H. ML ARTIFACT CLEANUP
**All model files identified:**

**Active Model:**
- ml/stage14/stage14_frozen_model.pkl — **KEEP** (Production model)

**Experimental Models (Archive):**
- ml/stage16b/stage16b_expanded_model.pkl — **ARCHIVE**
- aml_ai_model.pkl — **ARCHIVE**
- aml_ai_model_stage21.pkl — **ARCHIVE**
- aml_label_encoder.pkl — **ARCHIVE**
- aml_label_encoder_stage21.pkl — **ARCHIVE**
- ml_stage6_rf_model.pkl — **ARCHIVE**
- ml_stage6_scaler.pkl — **ARCHIVE**

**Stage Scripts (Archive):**
- All ml_stage*.py files (Stages 3-24) — **ARCHIVE**
- ml_audit_*.py files — **ARCHIVE**
- ml_baseline_*.py files — **ARCHIVE**
- ml_class_weight_*.py files — **ARCHIVE**
- ml_results_*.py files — **ARCHIVE**
- ml_xgboost_experiment.py — **ARCHIVE**
- train_stage16b_final_model.py — **ARCHIVE**

**Status:** Production model KEEP, all experiments ARCHIVE

---

### I. DATASET CLEANUP
**All datasets identified:**

**Official Dataset (KEEP):**
- data/ecocash_aml_synthetic_100k_v1/* — **KEEP** (Official 100k dataset)

**Experimental Datasets (Archive):**
- ml_stage11_dataset.csv — **ARCHIVE**
- ml_stage11_features.csv — **ARCHIVE**
- ml_stage11_ground_truth.json — **ARCHIVE**
- ml_stage11_metadata.json — **ARCHIVE**
- ml_stage3_dataset.csv — **ARCHIVE**
- ml_stage3_dataset_test.csv — **ARCHIVE**
- ml_stage3_ground_truth.json — **ARCHIVE**
- ml_stage3_ground_truth_test.json — **ARCHIVE**
- ml_stage3_metadata.json — **ARCHIVE**
- ml_stage3_metadata_test.json — **ARCHIVE**
- ml_stage5_features.csv — **ARCHIVE**
- ml_stage13_feature_coverage_matrix.csv — **ARCHIVE**
- ml_stage13_scenario_feature_matrix.csv — **ARCHIVE**
- ml_stage13_temporal_analysis.csv — **ARCHIVE**
- ml_stage14_feature_capability_matrix.csv — **ARCHIVE**
- ml_stage15_features.csv — **ARCHIVE**
- ml_stage15_scenario_observability.csv — **ARCHIVE**
- ml_stage15_ablation_results.csv — **ARCHIVE**
- ml_stage16b_features.csv — **ARCHIVE**
- ml_stage21_chapter1_features.csv — **ARCHIVE**
- ml_stage21_diversity_improved_dataset.csv — **ARCHIVE**
- ml_stage21_diversity_improved_ground_truth.json — **ARCHIVE**
- ml_stage22_independent_dataset.csv — **ARCHIVE**
- ml_stage22_independent_features.csv — **ARCHIVE**
- ml_stage22_independent_ground_truth.json — **ARCHIVE**
- ml_stage24_*.csv files — **ARCHIVE**
- ml_baseline_dataset.json — **ARCHIVE**
- ml_baseline_dataset_metadata.json — **ARCHIVE**

**Status:** Official dataset KEEP, all experimental datasets ARCHIVE

---

### J. DOCUMENTATION CONSOLIDATION
**Proposed final documentation structure:**

**Main Repository:**
- README.md (Update with final architecture)
- reports/README.md (Organization guide)
- reports/stage17e_transaction_simulation_alignment_2026-09-15.md (Current report)

**Archive Structure:**
- reports/ml_stages/ (Already organized)
- reports/integration_stages/ (Already organized)
- docs/archive/ (New location for root-level reports)

**Documentation to Consolidate:**
- Merge integration stage reports into single summary
- Keep key ML stage reports as research evidence
- Archive redundant reports

**Status:** Structure already well-organized, minor consolidation needed

---

### K. UNCERTAIN FILES
**Files requiring further investigation:**

**Database Files:**
- aml.db — **UNCERTAIN** (May be production SQLite database, verify before action)
- clean_aml_mysql_schema.sql — **KEEP** (MySQL schema reference)

**Configuration Files:**
- .env — **KEEP** (Contains secrets, should be in .gitignore)
- railway.json — **KEEP** (Deployment configuration)
- Dockerfile — **KEEP** (Deployment configuration)
- Procfile — **KEEP** (Deployment configuration)

**Cache Directories:**
- .pytest_cache — **REMOVE** (Cache directory)
- __pycache__ — **REMOVE** (Cache directory)

**Status:** Most configuration files are KEEP, cache directories REMOVE

---

## 3. Cleanup Actions Plan

### Phase 1: Archive Historical Material
1. Move root-level stage_*.md files to docs/archive/stages/
2. Move root-level ml_*.md files to docs/archive/ml_stages/
3. Move historical audit reports to docs/archive/audits/
4. Move experimental ML scripts to ml_archive/
5. Move experimental datasets to data/archive/
6. Move legacy test files to tests/archive/
7. Move debug scripts to scripts/archive/

### Phase 2: Remove Obsolete Files
1. Remove test databases (*.db in root)
2. Remove cache directories (.pytest_cache, __pycache__)
3. Remove temporary presentation files
4. Remove document extraction scripts

### Phase 3: Consolidate Documentation
1. Update README.md with final architecture
2. Consolidate integration stage reports
3. Create docs/archive/ structure
4. Update .gitignore if needed

### Phase 4: Final Validation
1. Run Stage 17E tests
2. Verify application starts
3. Verify Stage 13 + Stage 14 pipeline
4. Verify database connection
5. Verify frontend loads

---

## 4. Expected Final Structure

```
AML System/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── railway.json
├── Dockerfile
├── Procfile
│
├── server.py
├── database.py
├── transactions.py
├── alerts.py
├── agents.py
├── transaction_simulation.py
├── users.py
├── utils.py
├── ai_stage13_features.py
├── ai_stage14_model.py
├── ai_core.py
├── behavioral_profiling.py
├── security.py
├── screening.py
├── messaging.py
├── realtime.py
├── config.py
├── aml_rules.py
├── reports.py
│
├── templates/
├── static/
├── tests/
├── ml/
│   └── stage14/
│       └── stage14_frozen_model.pkl
├── data/
│   └── ecocash_aml_synthetic_100k_v1/
├── reports/
│   ├── README.md
│   ├── stage17e_transaction_simulation_alignment_2026-09-15.md
│   ├── ml_stages/
│   ├── integration_stages/
│   └── archive/
├── docs/
│   └── archive/
├── ml_archive/
├── data_archive/
└── scripts_archive/
```

---

## 5. Status

**Current Phase:** PRE-CLEANUP INVENTORY COMPLETE  
**Next Phase:** Awaiting approval to proceed with cleanup operations  
**Risk Assessment:** LOW — Only file organization, no code/ML changes

**No Application Risk:** All core application files identified and preserved  
**No ML Risk:** Production model and dataset identified and preserved  
**No Database Risk:** No database modifications planned

---

**READY FOR CLEANUP EXECUTION** ✅
