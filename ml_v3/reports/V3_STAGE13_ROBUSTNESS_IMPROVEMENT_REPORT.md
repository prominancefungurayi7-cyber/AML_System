# MODEL V3 — STAGE 13 CONTROLLED ROBUSTNESS IMPROVEMENT

**Technical execution: PASS. Decision: B — AGGREGATE PERFORMANCE IMPROVED BUT FEATURE CONCENTRATION REMAINS.**

At least one added-feature model improves aggregate Macro F1 by >=.002 without worse N3/A4 recall, but high/extreme dependence or top-feature concentration remains.

This is the full consolidated Stage 13 report. The saved Stage 11 reference is reproduced exactly; **15 new models** were fitted under a hashed, fixed plan. Six experimental descriptors were extracted twice from frozen Train/Validation observable transactions. The official 32-feature representation, targets and earlier artifacts remain unchanged. Every comparison uses **threshold 0.50**.

## 1. Outcome and scope



| Candidate | Macro F1 | Recall 1 | AP | FPR | N3 recall | A4 recall | Growth dependence | Top feature share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hgb_R0 | 0.9521 | 0.9349 | 0.9772 | 0.0315 | 0.5366 | 0.7389 | EXTREME | 0.6150 |
| hgb_R1 | 0.9529 | 0.9367 | 0.9786 | 0.0313 | 0.5854 | 0.7329 | EXTREME | 0.6182 |
| hgb_R2 | 0.9556 | 0.9426 | 0.9806 | 0.0307 | 0.5122 | 0.7656 | EXTREME | 0.6390 |
| hgb_R3 | 0.9561 | 0.9428 | 0.9795 | 0.0302 | 0.5854 | 0.7834 | EXTREME | 0.6340 |
| xgb_R0 | 0.9456 | 0.9321 | 0.9771 | 0.0390 | 0.5610 | 0.6914 | EXTREME | 0.5865 |
| xgb_R1 | 0.9442 | 0.9288 | 0.9777 | 0.0391 | 0.6829 | 0.6202 | EXTREME | 0.5843 |
| xgb_R2 | 0.9474 | 0.9393 | 0.9785 | 0.0403 | 0.5610 | 0.7240 | EXTREME | 0.6671 |
| xgb_R3 | 0.9486 | 0.9407 | 0.9790 | 0.0394 | 0.6829 | 0.7151 | EXTREME | 0.6754 |


Candidate recommendation for later selection: **none**. The Stage 11 reference remains the protected development benchmark. No final production model or final threshold is declared.

The full HGB extension (`hgb_R3`) raises Macro F1 **0.9521→0.9561**, N3 recall **22/41→24/41**, and A4 recall **249/337→264/337**. H1 false positives fall **39→33** and H5 remains **21**. These gains do not solve the main robustness concern: matched growth removal has dependence index **0.3139 (EXTREME)** and the growth feature holds **63.4%** of absolute permutation importance, versus **61.5%** in the reference.

The full XGBoost extension (`xgb_R3`) detects **28/41 N3** but **241/337 A4**, with **26 H5 false positives**. Its dependence remains **EXTREME (0.2665)** and its top-feature share is **67.5%** under the same permutation method. No tested added-feature model passes all the preregistered robustness gates.

The initial instruction limited data to existing matrices/artifacts while also requesting new history descriptors. The user explicitly authorized reading frozen Train/Validation observable transactions and diagnostic metadata. The extractor receives only eight public event fields: transaction ID, UTC timestamp, sender, receiver, amount in minor units, transaction type, agent ID and serviced wallet. Targets/provenance/evidence are joined only for diagnostic slices and never enter candidate extraction, fit inputs or prediction inputs. Train labels alone supervise fitting.

Model inputs use corrected Stage 10A Train **60,000 rows** and Validation **15,000 rows**, with frozen class counts **39,781/20,219** and **9,945/5,055**. Six new columns are stored separately and concatenated in memory. No history crosses partitions. No holdout directory was enumerated or evaluation file opened/hashed; named public commitment metadata alone was checked. No Validation fit, dataset regeneration, target change or application integration occurred.

## 2. Preregistered experiment and selection rules



| Property | Value |
| --- | --- |
| Plan saved UTC | 2026-09-28T22:11:15.187465+00:00 |
| Plan SHA-256 | fd5951652b7204664b2a0640b891b7a648083071dfcaad092b51c3facbfee47d |
| First new fit UTC | 2026-09-28T22:12:17.008360+00:00 |
| New fits | 15 |
| Reused models | 3 |
| Total evaluated representations | 18 |
| Seed | 20260928 |
| Threshold | 0.5000 |
| Wall seconds | 142.0739 |
| Environment | {"joblib": "1.5.3", "numpy": "2.4.3", "python": "3.14.3 (tags/v3.14.3:323c59a, Feb  3 2026, 16:04:56) [MSC v.1944 64 bit (AMD64)]", "sklearn": "1.9.0", "threads": 2, "xgboost": "3.4.1"} |


The fixed design has nine representations per family. R0 HGB and R0 XGBoost reuse saved Stage 11 models; HGB R0 without growth reuses Stage 12 ablation B. All other 15 are new Train fits. No hyperparameters, weights, seeds or representations were added after results. Both model families keep their saved Stage 11 estimator configurations. HGB uses positive sample weight 1.5 versus negative 1; XGBoost uses its saved balanced positive weight ratio 39,781/20,219, with no extra sample weights. All inputs retain documented sentinels; no scaler, clipping, imputer or missingness indicators were fitted.



| Family | Exact estimator parameters |
| --- | --- |
| hgb | {"categorical_features": "from_dtype", "class_weight": null, "early_stopping": false, "interaction_cst": null, "l2_regularization": 1.0, "learning_rate": 0.07, "loss": "log_loss", "max_bins": 255, "max_depth": 6, "max_features": 1.0, "max_iter": 200, "max_leaf_nodes": 31, "min_samples_leaf": 20, "monotonic_cst": null, "n_iter_no_change": 10, "random_state": 20260928, "scoring": "loss", "tol": 1e-07, "validation_fraction": 0.1, "verbose": 0, "warm_start": false} |
| xgb | {"base_score": null, "booster": null, "callbacks": null, "colsample_bylevel": null, "colsample_bynode": null, "colsample_bytree": 0.8, "device": null, "early_stopping_rounds": null, "enable_categorical": true, "eval_metric": "logloss", "feature_types": null, "feature_weights": null, "gamma": null, "grow_policy": null, "importance_type": null, "interaction_constraints": null, "learning_rate": 0.07, "max_bin": null, "max_cat_threshold": null, "max_cat_to_onehot": null, "max_delta_step": null, "max_depth": 4, "max_leaves": null, "min_child_weight": 5, "missing": "nan", "monotone_constraints": null, "multi_strategy": null, "n_estimators": 200, "n_jobs": 2, "num_parallel_tree": null, "objective": "binary:logistic", "random_state": 20260928, "reg_alpha": 0.05, "reg_lambda": 3.0, "sampling_method": null, "scale_pos_weight": 1.9675058113655473, "subsample": 0.8, "tree_method": "hist", "validate_parameters": null, "verbosity": null} |


XGBoost’s nonfinite default `missing=NaN` is serialized as text `nan` in the plan for strict JSON validity; the cloned estimator retains the original default. This does not convert finite -1/-3 markers into missing values.



| Representation | Columns | Role |
| --- | --- | --- |
| R0 | 32 | Serious comparison |
| R0_no_growth | 31 | Matched removal diagnostic |
| R1 | 35 | Serious comparison |
| R1_no_growth | 34 | Matched removal diagnostic |
| R2 | 35 | Serious comparison |
| R2_no_growth | 34 | Matched removal diagnostic |
| R3 | 38 | Serious comparison |
| R4 | 37 | Matched removal diagnostic |
| R5 | 36 | Matched removal diagnostic |


R0=official 32; R1=32+three graph descriptors; R2=32+three cash descriptors; R3=all 38; R4=R3 without growth; R5=R3 without growth and novelty. Additional R0/R1/R2 without-growth representations provide matched dependence estimates for every serious model. Removal variants never redefine the official contract. Only R1/R2/R3 can qualify as an added-feature robustness recommendation.

Stage12 index=max(0, drops in Macro F1, recall, F1, AP, increase in FPR). LOW <.02; MODERATE [.02,.05); HIGH [.05,.15); EXTREME >=.15. Full-versus-matched-retrained removal within each family/representation.



| Recommendation gate | Requirement |
| --- | --- |
| Macro F1 | At least reference minus 0.015 |
| Suspicious recall / F1 | At least reference minus 0.030 / 0.025 |
| AP | At least reference minus 0.020 |
| FPR | At most reference plus 0.010 |
| N3 / A4 recall | At least reference plus 0.100 / 0.030 |
| H1 and H5 FPR | Each at most reference plus 0.020 |
| Each domain-only recall | At least reference minus 0.030 |
| Growth dependence | Index <0.15 and at least 0.05 below Stage 12 index 0.3186943620 |
| Top-feature absolute share | At most 0.50 and at least 0.10 below reference |
| Top-three / top-five shares | Each at most reference plus 0.05 |
| Train–Validation Macro F1 gap | At most 0.04 |


All gates must pass. All gates required. Eligible candidates ordered by lower dependence, larger minimum N3/A4 recall, lower H1+H5 FPR, higher Macro F1, name. No hidden weighted score. S2/S4 excluded. These are preregistered research tolerances, not confidence bounds or regulatory requirements. Higher ROC-AUC and all class metrics are reported for context; there is no hidden composite score.

Decision precedence was also fixed: A if eligible; otherwise B if >=.002 Macro F1 gain and no N3/A4 loss but dependence>=.15 or top share>.5; otherwise C if dependence gate passes but aggregate tradeoffs fail; otherwise D if every candidate fails the joint N3/A4 improvement gates; otherwise E retain reference.

Stop after exactly15 new fits; no adaptive additions; Abort on protection mismatch, input/ID/range/causality failure or fit failure; No threshold/calibration search, Train+Val fit, final freeze or application integration; Preserve Stage9/10A/11/12 evidence and all raw inputs.

## 3. Exact experimental feature contract

Maximum six new columns: three N3-related and three A4-related. These are candidate descriptors only. Each is computable using decision-time observables and partition-local state. Monetary sums remain integer minor units until final division. Prior keys are strictly smaller `(UTC timestamp, integer transaction_id)`; same-time smaller IDs are prior, larger IDs are future. State updates after emission. Recent lower boundaries are open. Baselines precede and exclude the recent window.

### 33. `candidate_prior_reciprocal_count_7d`



| Contract item | Definition |
| --- | --- |
| domain | new_N3 |
| formula | Number of prior W2W edges receiver(T)->sender(T) in (t-7d,t], with key < key(T). Zero for non-W2W or self-loop. |
| current | type and endpoints only; no current amount |
| prior | observable directed edges, strictly smaller timestamp/integer-ID keys |
| window | open-lower 7d |
| baseline | none |
| zero_missing | zero means no reciprocal edge or non-applicable role; no missing marker |
| meaning | Repeated reverse-direction relationships beyond the selected shortest path |
| non_oracle | No current/edge amount gates, no multi-edge qualifying-path conjunction or target. |


### 34. `candidate_prior_two_hop_return_count_7d`



| Contract item | Definition |
| --- | --- |
| domain | new_N3 |
| formula | Count edge-pairs r->m and m->s with three distinct nodes, both in (t-7d,t], key(edge1)<key(edge2)<key(T). Each edge-pair counts once. Zero for non-W2W/self-loop. |
| current | type and endpoints only |
| prior | observable edges with increasing full keys |
| window | open-lower 7d |
| baseline | none |
| zero_missing | zero when no chronological two-edge route; no missing marker |
| meaning | Multiplicity of short return routes, not restricted to the selected path |
| non_oracle | No monetary filtering, current return ratio, lengths 3..5 or complete cycle predicate. |


### 35. `candidate_selected_path_max_log_value_change`



| Contract item | Definition |
| --- | --- |
| domain | new_N3 |
| formula | max_j abs(log(amount(edge[j+1])/amount(edge[j]))) over adjacent edges in the Stage 10A selected chronological simple path of 1..5 prior edges. One-edge path=0; absent/non-W2W=-1. |
| current | type/endpoints select the prior path; current amount excluded |
| prior | Stage 10A topology selection: shortest path, latest first edge, then lexicographic edge-key sequence |
| window | open-lower 7d |
| baseline | none |
| zero_missing | one-edge path has no adjacent discrepancy (0); absent path uses -1 |
| meaning | Continuous value variation along a selected prior path |
| non_oracle | No amount-gated path search, predicate cutoffs, current ratio gate or any-qualifying-path output. |


### 36. `candidate_agent_cash_service_share_24h`



| Contract item | Definition |
| --- | --- |
| domain | new_A4 |
| formula | Cash-In plus Cash-Out service count / all service-event count in (t-24h,t], including permitted current service. Assisted W2W only enters denominator. |
| current | current agent service/type; no cash principal assigned to W2W |
| prior | same-agent service history, key < key(T) |
| window | open-lower 24h |
| baseline | none |
| zero_missing | zero without agent/services; no missing marker |
| meaning | Cash activity relative to all agent service activity |
| non_oracle | No cash-count minimum, unique-wallet count, direction thresholds or complete imbalance conjunction. |


### 37. `candidate_agent_cash_direction_persistence_24h`



| Contract item | Definition |
| --- | --- |
| domain | new_A4 |
| formula | abs(sum(skew_j)/4), where skew_j=(cashout_value-cashin_value)/(cashout_value+cashin_value) in each of four disjoint 6h buckets (t-(j+1)*6h,t-j*6h], j=0..3; empty-cash bucket skew=0. Current service enters j=0. |
| current | current cash type/amount/agent and time |
| prior | same-agent history, key < key(T); no future buckets |
| window | four preceding/current 6h buckets covering open-lower 24h |
| baseline | none |
| zero_missing | zero with no cash/agent or balanced opposing bucket directions; no missing marker |
| meaning | Persistence of a common cash direction across time, discounted by inactive buckets |
| non_oracle | No complete A4 count, wallet breadth, magnitude/change or current-role conjunction. |


### 38. `candidate_agent_cash_value_acceleration_24h`



| Contract item | Definition |
| --- | --- |
| domain | new_A4 |
| formula | Recent 24h Cash-In+Cash-Out minor-unit value / max(1, preceding disjoint 28d cash value / 28). Baseline B=(t-29d,t-1d], recent R=(t-1d,t]. |
| current | current cash value included; assisted W2W contributes zero cash |
| prior | same-agent observed services; full baseline coverage from first observed service <=t-29d |
| window | open-lower 24h recent; disjoint 28d baseline |
| baseline | at least 12 baseline services and 8 baseline cash events, full 29d observation; no recent eligibility gate |
| zero_missing | -1 without agent or eligible baseline; valid zero if no recent cash; denominator floor one minor unit |
| meaning | Unsigned cash magnitude relative to the agent own earlier activity |
| non_oracle | No signed imbalance/change gates, recent count/breadth conjunction, private activation or predicate outcome. |


No feature returns an N3/A4 trigger, searches for a path satisfying the complete monetary conjunction, or combines the full count/breadth/current-role/imbalance/baseline predicates. The graph spread summarizes one topology-selected path, so it can still miss evidence on another path. Cash descriptors provide composition, persistence and unsigned magnitude; they omit the full recent event-count/unique-wallet conjunction. Features necessarily correlate with the synthetic target observables, which does not itself establish leakage. Projection and source review establish the intended input boundary; they do not prove the absence of every synthetic shortcut.



| Partition | Rows | New columns | Two extractions equal | Official values unchanged | Candidate file SHA-256 |
| --- | --- | --- | --- | --- | --- |
| train | 60000 | 6 | True | True | 3b6805789d4d4e965bb33b32c5f9642192ef97bf103ad8aaa7e4772ed2f4c4c4 |
| validation | 15000 | 6 | True | True | 074a92cdf170cd31b0b9a0a2ea67422cac67a921f17e6b0c8d17389bb16e2d7e |


The six-column arrays and IDs are stored under `evidence/stage13/`. Both extractions start empty histories and their arrays/ID order match exactly; this is numeric extraction repeatability, not a claim of two independently serialized byte sets. Saved candidate files are hashed and reloaded for verification. The original 32 matrix columns were verified unchanged before concatenation.

## 4. Causality and manual feature tests



| Synthetic case | Expected result |
| --- | --- |
| Isolated direct W2W | [reciprocal=0, two-hop=0, spread=-1, cash share=0, persistence=0, cash rate=-1] |
| Reverse edge exactly 7d old plus another 1s old | Old boundary excluded; reciprocal count1; one-edge spread0 |
| Same-time r→m ID1, m→s ID2, then closure | Two-hop count1; amounts100→400 give spread log(4) |
| Swap the two prior IDs | Chronology reverses; count0 and no selected path |
| Two first-leg edges followed by two second-leg edges | Four chronological edge-pairs |
| Current self-loop | Graph counts0; spread missing |
| Cash-Out at -18h,-12h,-6h,0; extra at -24h | Lower boundary excluded; cash share1 and persistence1 |
| Replace current with Cash-In / assisted W2W | Persistence .5 / .75; W2W cash-service share .75 |
| Full29d coverage,12 baseline services including8 cash of100 minor units, recent cash100 | Rate100/(800/28)=3.5 |
| Remove first observation / reduce baseline to11 services | Missing cash rate -1 |
| Future records, metadata mutation and shuffled input | Earlier vectors unchanged |
| Current W2W amount perturbation | All six descriptors unchanged; no current W2W amount enters cash or prior graph spread |


Executed **6 test methods**, with no failures/errors. The captured test log and source digest are in final verification. Tests use synthetic events and do not read evaluation data. Finite examples do not exhaust all possible histories.

## 5. Protected reference reproduction



| Partition | Exact score agreement | Max difference |
| --- | --- | --- |
| train | True | 0.0000 |
| validation | True | 0.0000 |




| Partition | Accuracy | Balanced accuracy | Macro F1 | Precision 1 | Recall 1 | F1 1 | Recall 0 | ROC-AUC | AP | FPR | Confusion [[TN,FP],[FN,TP]] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | 0.9729 | 0.9676 | 0.9695 | 0.9676 | 0.9513 | 0.9594 | 0.9838 | 0.9957 | 0.9927 | 0.0162 | [[39137, 644], [984, 19235]] |
| validation | 0.9572 | 0.9517 | 0.9521 | 0.9379 | 0.9349 | 0.9364 | 0.9685 | 0.9888 | 0.9772 | 0.0315 | [[9632, 313], [329, 4726]] |


All domain, family and target-0 category counts/rates exactly reproduce the saved Stage 11/12 evidence. These reference slices appear as `hgb_R0` in the complete tables below. AP is Average Precision, not trapezoidal PR area. Class 1 means synthetic suspicious-pattern review target; class 0 is the negative state under the frozen definition.

## 6. All model results and generalization

### Train



| Candidate | Accuracy | Balanced accuracy | Macro F1 | Precision 1 | Recall 1 | F1 1 | Recall 0 | ROC-AUC | AP | FPR | Confusion [[TN,FP],[FN,TP]] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hgb_R0 | 0.9729 | 0.9676 | 0.9695 | 0.9676 | 0.9513 | 0.9594 | 0.9838 | 0.9957 | 0.9927 | 0.0162 | [[39137, 644], [984, 19235]] |
| hgb_R0_no_growth | 0.8599 | 0.8393 | 0.8420 | 0.8020 | 0.7759 | 0.7887 | 0.9027 | 0.9353 | 0.8999 | 0.0973 | [[35909, 3872], [4532, 15687]] |
| hgb_R1 | 0.9727 | 0.9674 | 0.9693 | 0.9671 | 0.9512 | 0.9591 | 0.9836 | 0.9957 | 0.9927 | 0.0164 | [[39127, 654], [986, 19233]] |
| hgb_R1_no_growth | 0.8604 | 0.8396 | 0.8425 | 0.8030 | 0.7761 | 0.7893 | 0.9032 | 0.9356 | 0.9004 | 0.0968 | [[35932, 3849], [4528, 15691]] |
| hgb_R2 | 0.9755 | 0.9717 | 0.9725 | 0.9667 | 0.9602 | 0.9635 | 0.9832 | 0.9970 | 0.9946 | 0.0168 | [[39112, 669], [804, 19415]] |
| hgb_R2_no_growth | 0.8692 | 0.8475 | 0.8518 | 0.8221 | 0.7809 | 0.8010 | 0.9141 | 0.9403 | 0.9078 | 0.0859 | [[36363, 3418], [4429, 15790]] |
| hgb_R3 | 0.9751 | 0.9711 | 0.9721 | 0.9671 | 0.9588 | 0.9629 | 0.9834 | 0.9970 | 0.9946 | 0.0166 | [[39121, 660], [834, 19385]] |
| hgb_R4 | 0.8700 | 0.8490 | 0.8529 | 0.8218 | 0.7845 | 0.8027 | 0.9136 | 0.9409 | 0.9084 | 0.0864 | [[36342, 3439], [4358, 15861]] |
| hgb_R5 | 0.8603 | 0.8327 | 0.8400 | 0.8216 | 0.7478 | 0.7830 | 0.9175 | 0.9309 | 0.8966 | 0.0825 | [[36499, 3282], [5099, 15120]] |
| xgb_R0 | 0.9609 | 0.9555 | 0.9562 | 0.9445 | 0.9391 | 0.9418 | 0.9720 | 0.9921 | 0.9867 | 0.0280 | [[38666, 1115], [1232, 18987]] |
| xgb_R0_no_growth | 0.8303 | 0.8246 | 0.8152 | 0.7221 | 0.8071 | 0.7622 | 0.8422 | 0.9205 | 0.8751 | 0.1578 | [[33502, 6279], [3901, 16318]] |
| xgb_R1 | 0.9607 | 0.9553 | 0.9559 | 0.9441 | 0.9389 | 0.9415 | 0.9717 | 0.9924 | 0.9870 | 0.0283 | [[38656, 1125], [1235, 18984]] |
| xgb_R1_no_growth | 0.8301 | 0.8249 | 0.8151 | 0.7209 | 0.8090 | 0.7624 | 0.8408 | 0.9207 | 0.8756 | 0.1592 | [[33447, 6334], [3862, 16357]] |
| xgb_R2 | 0.9608 | 0.9567 | 0.9562 | 0.9401 | 0.9439 | 0.9420 | 0.9695 | 0.9936 | 0.9885 | 0.0305 | [[38566, 1215], [1135, 19084]] |
| xgb_R2_no_growth | 0.8361 | 0.8291 | 0.8208 | 0.7330 | 0.8079 | 0.7686 | 0.8504 | 0.9241 | 0.8815 | 0.1496 | [[33830, 5951], [3885, 16334]] |
| xgb_R3 | 0.9613 | 0.9573 | 0.9567 | 0.9400 | 0.9453 | 0.9427 | 0.9693 | 0.9936 | 0.9886 | 0.0307 | [[38561, 1220], [1105, 19114]] |
| xgb_R4 | 0.8363 | 0.8299 | 0.8212 | 0.7323 | 0.8102 | 0.7693 | 0.8495 | 0.9244 | 0.8820 | 0.1505 | [[33793, 5988], [3837, 16382]] |
| xgb_R5 | 0.8284 | 0.8184 | 0.8117 | 0.7260 | 0.7881 | 0.7558 | 0.8488 | 0.9152 | 0.8714 | 0.1512 | [[33767, 6014], [4285, 15934]] |


### Validation



| Candidate | Accuracy | Balanced accuracy | Macro F1 | Precision 1 | Recall 1 | F1 1 | Recall 0 | ROC-AUC | AP | FPR | Confusion [[TN,FP],[FN,TP]] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hgb_R0 | 0.9572 | 0.9517 | 0.9521 | 0.9379 | 0.9349 | 0.9364 | 0.9685 | 0.9888 | 0.9772 | 0.0315 | [[9632, 313], [329, 4726]] |
| hgb_R0_no_growth | 0.8453 | 0.7890 | 0.8102 | 0.8913 | 0.6162 | 0.7287 | 0.9618 | 0.9098 | 0.8661 | 0.0382 | [[9565, 380], [1940, 3115]] |
| hgb_R1 | 0.9579 | 0.9527 | 0.9529 | 0.9384 | 0.9367 | 0.9375 | 0.9687 | 0.9892 | 0.9786 | 0.0313 | [[9634, 311], [320, 4735]] |
| hgb_R1_no_growth | 0.8437 | 0.7871 | 0.8082 | 0.8880 | 0.6135 | 0.7256 | 0.9607 | 0.9073 | 0.8640 | 0.0393 | [[9554, 391], [1954, 3101]] |
| hgb_R2 | 0.9603 | 0.9560 | 0.9556 | 0.9398 | 0.9426 | 0.9412 | 0.9693 | 0.9906 | 0.9806 | 0.0307 | [[9640, 305], [290, 4765]] |
| hgb_R2_no_growth | 0.8455 | 0.7917 | 0.8118 | 0.8800 | 0.6269 | 0.7322 | 0.9566 | 0.9156 | 0.8731 | 0.0434 | [[9513, 432], [1886, 3169]] |
| hgb_R3 | 0.9607 | 0.9563 | 0.9561 | 0.9408 | 0.9428 | 0.9418 | 0.9698 | 0.9903 | 0.9795 | 0.0302 | [[9645, 300], [289, 4766]] |
| hgb_R4 | 0.8462 | 0.7928 | 0.8128 | 0.8806 | 0.6289 | 0.7338 | 0.9567 | 0.9152 | 0.8728 | 0.0433 | [[9514, 431], [1876, 3179]] |
| hgb_R5 | 0.8451 | 0.8188 | 0.8238 | 0.7889 | 0.7379 | 0.7625 | 0.8996 | 0.9105 | 0.8725 | 0.1004 | [[8947, 998], [1325, 3730]] |
| xgb_R0 | 0.9513 | 0.9466 | 0.9456 | 0.9239 | 0.9321 | 0.9280 | 0.9610 | 0.9879 | 0.9771 | 0.0390 | [[9557, 388], [343, 4712]] |
| xgb_R0_no_growth | 0.8392 | 0.7918 | 0.8079 | 0.8395 | 0.6465 | 0.7304 | 0.9372 | 0.9076 | 0.8602 | 0.0628 | [[9320, 625], [1787, 3268]] |
| xgb_R1 | 0.9501 | 0.9448 | 0.9442 | 0.9235 | 0.9288 | 0.9261 | 0.9609 | 0.9882 | 0.9777 | 0.0391 | [[9556, 389], [360, 4695]] |
| xgb_R1_no_growth | 0.8399 | 0.7924 | 0.8087 | 0.8413 | 0.6469 | 0.7314 | 0.9380 | 0.9098 | 0.8624 | 0.0620 | [[9328, 617], [1785, 3270]] |
| xgb_R2 | 0.9528 | 0.9495 | 0.9474 | 0.9221 | 0.9393 | 0.9306 | 0.9597 | 0.9892 | 0.9785 | 0.0403 | [[9544, 401], [307, 4748]] |
| xgb_R2_no_growth | 0.8432 | 0.8008 | 0.8149 | 0.8313 | 0.6708 | 0.7425 | 0.9308 | 0.9109 | 0.8660 | 0.0692 | [[9257, 688], [1664, 3391]] |
| xgb_R3 | 0.9539 | 0.9506 | 0.9486 | 0.9238 | 0.9407 | 0.9322 | 0.9606 | 0.9895 | 0.9790 | 0.0394 | [[9553, 392], [300, 4755]] |
| xgb_R4 | 0.8443 | 0.8025 | 0.8164 | 0.8320 | 0.6742 | 0.7448 | 0.9308 | 0.9117 | 0.8668 | 0.0692 | [[9257, 688], [1647, 3408]] |
| xgb_R5 | 0.8186 | 0.8114 | 0.8024 | 0.7068 | 0.7891 | 0.7457 | 0.8336 | 0.9067 | 0.8635 | 0.1664 | [[8290, 1655], [1066, 3989]] |




| Candidate | Fit seconds | Reused artifact | Train minus Validation Macro F1 | Warnings |
| --- | --- | --- | --- | --- |
| hgb_R0 | 0.0000 | Stage11 reference | 0.0174 | [] |
| hgb_R0_no_growth | 0.0000 | Stage12 ablation B | 0.0317 | [] |
| hgb_R1 | 5.9269 | new Train fit | 0.0164 | [] |
| hgb_R1_no_growth | 4.8920 | new Train fit | 0.0343 | [] |
| hgb_R2 | 5.5877 | new Train fit | 0.0168 | [] |
| hgb_R2_no_growth | 5.4171 | new Train fit | 0.0400 | [] |
| hgb_R3 | 5.9675 | new Train fit | 0.0160 | [] |
| hgb_R4 | 5.6510 | new Train fit | 0.0401 | [] |
| hgb_R5 | 5.3347 | new Train fit | 0.0162 | [] |
| xgb_R0 | 0.0000 | Stage11 shortlisted balanced XGBoost | 0.0106 | [] |
| xgb_R0_no_growth | 1.3961 | new Train fit | 0.0072 | [] |
| xgb_R1 | 1.4726 | new Train fit | 0.0117 | [] |
| xgb_R1_no_growth | 1.4210 | new Train fit | 0.0064 | [] |
| xgb_R2 | 1.4309 | new Train fit | 0.0088 | [] |
| xgb_R2_no_growth | 1.3907 | new Train fit | 0.0059 | [] |
| xgb_R3 | 1.4890 | new Train fit | 0.0081 | [] |
| xgb_R4 | 1.5228 | new Train fit | 0.0048 | [] |
| xgb_R5 | 1.4119 | new Train fit | 0.0094 | [] |


All results, including diagnostics and tradeoffs, are retained. Train and Validation are disjoint frozen partitions, but Validation has been reused across development stages; these gaps do not measure final unseen-population performance. No early stopping used Validation, and no representation was changed in response to these metrics.

## 7. Matched growth dependence

Each comparison retrains the same estimator/weights on the same Train rows with only growth omitted. R3 compares against R4. Deltas below are removal minus full. R5 is separately reported above; it also removes novelty and is not the single-growth dependence measure.



| Full | Matched removal | Full Macro F1 | Removed Macro F1 | Index | Class |
| --- | --- | --- | --- | --- | --- |
| hgb_R0 | hgb_R0_no_growth | 0.9521 | 0.8102 | 0.3187 | EXTREME |
| hgb_R1 | hgb_R1_no_growth | 0.9529 | 0.8082 | 0.3232 | EXTREME |
| hgb_R2 | hgb_R2_no_growth | 0.9556 | 0.8118 | 0.3157 | EXTREME |
| hgb_R3 | hgb_R4 | 0.9561 | 0.8128 | 0.3139 | EXTREME |
| xgb_R0 | xgb_R0_no_growth | 0.9456 | 0.8079 | 0.2857 | EXTREME |
| xgb_R1 | xgb_R1_no_growth | 0.9442 | 0.8087 | 0.2819 | EXTREME |
| xgb_R2 | xgb_R2_no_growth | 0.9474 | 0.8149 | 0.2684 | EXTREME |
| xgb_R3 | xgb_R4 | 0.9486 | 0.8164 | 0.2665 | EXTREME |




| Candidate | ΔMacro F1 | ΔRecall1 | ΔF1 1 | ΔAP | ΔROC-AUC | ΔFPR | ΔAgent recall | ΔA1 recall | ΔA4 recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hgb_R0 | -0.1418 | -0.3187 | -0.2077 | -0.1111 | -0.0790 | 0.0067 | -0.4214 | -0.5945 | -0.0445 |
| hgb_R1 | -0.1447 | -0.3232 | -0.2119 | -0.1146 | -0.0819 | 0.0080 | -0.4271 | -0.5978 | -0.0504 |
| hgb_R2 | -0.1438 | -0.3157 | -0.2090 | -0.1076 | -0.0750 | 0.0128 | -0.4185 | -0.5880 | -0.0534 |
| hgb_R3 | -0.1433 | -0.3139 | -0.2080 | -0.1067 | -0.0752 | 0.0132 | -0.4180 | -0.5865 | -0.0712 |
| xgb_R0 | -0.1377 | -0.2857 | -0.1976 | -0.1169 | -0.0803 | 0.0238 | -0.3789 | -0.5443 | 0.0148 |
| xgb_R1 | -0.1356 | -0.2819 | -0.1947 | -0.1154 | -0.0784 | 0.0229 | -0.3731 | -0.5435 | 0.0593 |
| xgb_R2 | -0.1325 | -0.2684 | -0.1881 | -0.1125 | -0.0783 | 0.0289 | -0.3559 | -0.5115 | 0.0148 |
| xgb_R3 | -0.1322 | -0.2665 | -0.1873 | -0.1122 | -0.0778 | 0.0298 | -0.3523 | -0.5038 | -0.0119 |


Dependence is measured within each model family. HGB/XGBoost have different frozen weighting schemes, so cross-family differences describe their full configurations rather than an isolated algorithm effect. Permutation concentration and removal dependence are different diagnostics; distributing importance does not guarantee a small removal loss.

## 8. Domain-independent and ordinary domain recall

Only-domain slices exclude every other domain, while allowing multiple families within the named domain. `multi_domain` is the unique union of rows belonging to at least two domains; ordinary domain rows overlap and must not be added. All models, including removals, are shown.



| Candidate | Slice | Support | TP | FN | Recall |
| --- | --- | --- | --- | --- | --- |
| hgb_R0 | agent_only | 3123 | 2867 | 256 | 0.9180 |
| hgb_R0 | multi_domain | 979 | 979 | 0 | 1.0000 |
| hgb_R0 | network_only | 738 | 670 | 68 | 0.9079 |
| hgb_R0 | structuring_only | 215 | 210 | 5 | 0.9767 |
| hgb_R0_no_growth | agent_only | 3123 | 1255 | 1868 | 0.4019 |
| hgb_R0_no_growth | multi_domain | 979 | 975 | 4 | 0.9959 |
| hgb_R0_no_growth | network_only | 738 | 674 | 64 | 0.9133 |
| hgb_R0_no_growth | structuring_only | 215 | 211 | 4 | 0.9814 |
| hgb_R1 | agent_only | 3123 | 2869 | 254 | 0.9187 |
| hgb_R1 | multi_domain | 979 | 979 | 0 | 1.0000 |
| hgb_R1 | network_only | 738 | 677 | 61 | 0.9173 |
| hgb_R1 | structuring_only | 215 | 210 | 5 | 0.9767 |
| hgb_R1_no_growth | agent_only | 3123 | 1236 | 1887 | 0.3958 |
| hgb_R1_no_growth | multi_domain | 979 | 974 | 5 | 0.9949 |
| hgb_R1_no_growth | network_only | 738 | 680 | 58 | 0.9214 |
| hgb_R1_no_growth | structuring_only | 215 | 211 | 4 | 0.9814 |
| hgb_R2 | agent_only | 3123 | 2911 | 212 | 0.9321 |
| hgb_R2 | multi_domain | 979 | 979 | 0 | 1.0000 |
| hgb_R2 | network_only | 738 | 664 | 74 | 0.8997 |
| hgb_R2 | structuring_only | 215 | 211 | 4 | 0.9814 |
| hgb_R2_no_growth | agent_only | 3123 | 1310 | 1813 | 0.4195 |
| hgb_R2_no_growth | multi_domain | 979 | 975 | 4 | 0.9959 |
| hgb_R2_no_growth | network_only | 738 | 673 | 65 | 0.9119 |
| hgb_R2_no_growth | structuring_only | 215 | 211 | 4 | 0.9814 |
| hgb_R3 | agent_only | 3123 | 2912 | 211 | 0.9324 |
| hgb_R3 | multi_domain | 979 | 979 | 0 | 1.0000 |
| hgb_R3 | network_only | 738 | 664 | 74 | 0.8997 |
| hgb_R3 | structuring_only | 215 | 211 | 4 | 0.9814 |
| hgb_R4 | agent_only | 3123 | 1312 | 1811 | 0.4201 |
| hgb_R4 | multi_domain | 979 | 976 | 3 | 0.9969 |
| hgb_R4 | network_only | 738 | 681 | 57 | 0.9228 |
| hgb_R4 | structuring_only | 215 | 210 | 5 | 0.9767 |
| hgb_R5 | agent_only | 3123 | 1864 | 1259 | 0.5969 |
| hgb_R5 | multi_domain | 979 | 979 | 0 | 1.0000 |
| hgb_R5 | network_only | 738 | 676 | 62 | 0.9160 |
| hgb_R5 | structuring_only | 215 | 211 | 4 | 0.9814 |
| xgb_R0 | agent_only | 3123 | 2850 | 273 | 0.9126 |
| xgb_R0 | multi_domain | 979 | 979 | 0 | 1.0000 |
| xgb_R0 | network_only | 738 | 673 | 65 | 0.9119 |
| xgb_R0 | structuring_only | 215 | 210 | 5 | 0.9767 |
| xgb_R0_no_growth | agent_only | 3123 | 1400 | 1723 | 0.4483 |
| xgb_R0_no_growth | multi_domain | 979 | 976 | 3 | 0.9969 |
| xgb_R0_no_growth | network_only | 738 | 681 | 57 | 0.9228 |
| xgb_R0_no_growth | structuring_only | 215 | 211 | 4 | 0.9814 |
| xgb_R1 | agent_only | 3123 | 2830 | 293 | 0.9062 |
| xgb_R1 | multi_domain | 979 | 979 | 0 | 1.0000 |
| xgb_R1 | network_only | 738 | 676 | 62 | 0.9160 |
| xgb_R1 | structuring_only | 215 | 210 | 5 | 0.9767 |
| xgb_R1_no_growth | agent_only | 3123 | 1402 | 1721 | 0.4489 |
| xgb_R1_no_growth | multi_domain | 979 | 976 | 3 | 0.9969 |
| xgb_R1_no_growth | network_only | 738 | 681 | 57 | 0.9228 |
| xgb_R1_no_growth | structuring_only | 215 | 211 | 4 | 0.9814 |
| xgb_R2 | agent_only | 3123 | 2891 | 232 | 0.9257 |
| xgb_R2 | multi_domain | 979 | 979 | 0 | 1.0000 |
| xgb_R2 | network_only | 738 | 669 | 69 | 0.9065 |
| xgb_R2 | structuring_only | 215 | 209 | 6 | 0.9721 |
| xgb_R2_no_growth | agent_only | 3123 | 1528 | 1595 | 0.4893 |
| xgb_R2_no_growth | multi_domain | 979 | 977 | 2 | 0.9980 |
| xgb_R2_no_growth | network_only | 738 | 675 | 63 | 0.9146 |
| xgb_R2_no_growth | structuring_only | 215 | 211 | 4 | 0.9814 |
| xgb_R3 | agent_only | 3123 | 2892 | 231 | 0.9260 |
| xgb_R3 | multi_domain | 979 | 979 | 0 | 1.0000 |
| xgb_R3 | network_only | 738 | 675 | 63 | 0.9146 |
| xgb_R3 | structuring_only | 215 | 209 | 6 | 0.9721 |
| xgb_R4 | agent_only | 3123 | 1542 | 1581 | 0.4938 |
| xgb_R4 | multi_domain | 979 | 978 | 1 | 0.9990 |
| xgb_R4 | network_only | 738 | 677 | 61 | 0.9173 |
| xgb_R4 | structuring_only | 215 | 211 | 4 | 0.9814 |
| xgb_R5 | agent_only | 3123 | 2122 | 1001 | 0.6795 |
| xgb_R5 | multi_domain | 979 | 979 | 0 | 1.0000 |
| xgb_R5 | network_only | 738 | 677 | 61 | 0.9173 |
| xgb_R5 | structuring_only | 215 | 211 | 4 | 0.9814 |




| Candidate | Domain | Support | TP | FN | Recall |
| --- | --- | --- | --- | --- | --- |
| hgb_R0 | agent | 3835 | 3579 | 256 | 0.9332 |
| hgb_R0 | network | 1271 | 1203 | 68 | 0.9465 |
| hgb_R0 | structuring | 1039 | 1034 | 5 | 0.9952 |
| hgb_R1 | agent | 3835 | 3581 | 254 | 0.9338 |
| hgb_R1 | network | 1271 | 1210 | 61 | 0.9520 |
| hgb_R1 | structuring | 1039 | 1034 | 5 | 0.9952 |
| hgb_R2 | agent | 3835 | 3623 | 212 | 0.9447 |
| hgb_R2 | network | 1271 | 1197 | 74 | 0.9418 |
| hgb_R2 | structuring | 1039 | 1035 | 4 | 0.9962 |
| hgb_R3 | agent | 3835 | 3624 | 211 | 0.9450 |
| hgb_R3 | network | 1271 | 1197 | 74 | 0.9418 |
| hgb_R3 | structuring | 1039 | 1035 | 4 | 0.9962 |
| xgb_R0 | agent | 3835 | 3562 | 273 | 0.9288 |
| xgb_R0 | network | 1271 | 1206 | 65 | 0.9489 |
| xgb_R0 | structuring | 1039 | 1034 | 5 | 0.9952 |
| xgb_R1 | agent | 3835 | 3542 | 293 | 0.9236 |
| xgb_R1 | network | 1271 | 1209 | 62 | 0.9512 |
| xgb_R1 | structuring | 1039 | 1034 | 5 | 0.9952 |
| xgb_R2 | agent | 3835 | 3603 | 232 | 0.9395 |
| xgb_R2 | network | 1271 | 1202 | 69 | 0.9457 |
| xgb_R2 | structuring | 1039 | 1033 | 6 | 0.9942 |
| xgb_R3 | agent | 3835 | 3604 | 231 | 0.9398 |
| xgb_R3 | network | 1271 | 1208 | 63 | 0.9504 |
| xgb_R3 | structuring | 1039 | 1033 | 6 | 0.9942 |


## 9. All twelve family slices

Support comes from frozen observable evidence labels, not private campaign membership. S2 (N=1) and S4 (N=8) are **sparse/unstable**, excluded from selection. Their individual predictions are retained for disclosure, not tuned. N3 (N=41) is also small: one changed prediction moves recall by about 2.44 percentage points. Family evidence overlaps, so counts are not additive.



| Candidate | Family | Support | TP | FN | Recall | Support warning |
| --- | --- | --- | --- | --- | --- | --- |
| hgb_R0 | A1 | 2745 | 2689 | 56 | 0.9796 |  |
| hgb_R0 | A2 | 930 | 814 | 116 | 0.8753 |  |
| hgb_R0 | A3 | 485 | 481 | 4 | 0.9918 |  |
| hgb_R0 | A4 | 337 | 249 | 88 | 0.7389 |  |
| hgb_R0 | N1 | 316 | 301 | 15 | 0.9525 |  |
| hgb_R0 | N2 | 736 | 708 | 28 | 0.9620 |  |
| hgb_R0 | N3 | 41 | 22 | 19 | 0.5366 | small support |
| hgb_R0 | N4 | 247 | 241 | 6 | 0.9757 |  |
| hgb_R0 | S1 | 276 | 273 | 3 | 0.9891 |  |
| hgb_R0 | S2 | 1 | 1 | 0 | 1.0000 | sparse/unstable; not selected on |
| hgb_R0 | S3 | 814 | 814 | 0 | 1.0000 |  |
| hgb_R0 | S4 | 8 | 6 | 2 | 0.7500 | sparse/unstable; not selected on |
| hgb_R0_no_growth | A1 | 2745 | 1057 | 1688 | 0.3851 |  |
| hgb_R0_no_growth | A2 | 930 | 800 | 130 | 0.8602 |  |
| hgb_R0_no_growth | A3 | 485 | 485 | 0 | 1.0000 |  |
| hgb_R0_no_growth | A4 | 337 | 234 | 103 | 0.6944 |  |
| hgb_R0_no_growth | N1 | 316 | 301 | 15 | 0.9525 |  |
| hgb_R0_no_growth | N2 | 736 | 707 | 29 | 0.9606 |  |
| hgb_R0_no_growth | N3 | 41 | 28 | 13 | 0.6829 | small support |
| hgb_R0_no_growth | N4 | 247 | 240 | 7 | 0.9717 |  |
| hgb_R0_no_growth | S1 | 276 | 274 | 2 | 0.9928 |  |
| hgb_R0_no_growth | S2 | 1 | 1 | 0 | 1.0000 | sparse/unstable; not selected on |
| hgb_R0_no_growth | S3 | 814 | 814 | 0 | 1.0000 |  |
| hgb_R0_no_growth | S4 | 8 | 2 | 6 | 0.2500 | sparse/unstable; not selected on |
| hgb_R1 | A1 | 2745 | 2688 | 57 | 0.9792 |  |
| hgb_R1 | A2 | 930 | 819 | 111 | 0.8806 |  |
| hgb_R1 | A3 | 485 | 481 | 4 | 0.9918 |  |
| hgb_R1 | A4 | 337 | 247 | 90 | 0.7329 |  |
| hgb_R1 | N1 | 316 | 304 | 12 | 0.9620 |  |
| hgb_R1 | N2 | 736 | 710 | 26 | 0.9647 |  |
| hgb_R1 | N3 | 41 | 24 | 17 | 0.5854 | small support |
| hgb_R1 | N4 | 247 | 241 | 6 | 0.9757 |  |
| hgb_R1 | S1 | 276 | 273 | 3 | 0.9891 |  |
| hgb_R1 | S2 | 1 | 1 | 0 | 1.0000 | sparse/unstable; not selected on |
| hgb_R1 | S3 | 814 | 814 | 0 | 1.0000 |  |
| hgb_R1 | S4 | 8 | 6 | 2 | 0.7500 | sparse/unstable; not selected on |
| hgb_R1_no_growth | A1 | 2745 | 1047 | 1698 | 0.3814 |  |
| hgb_R1_no_growth | A2 | 930 | 789 | 141 | 0.8484 |  |
| hgb_R1_no_growth | A3 | 485 | 485 | 0 | 1.0000 |  |
| hgb_R1_no_growth | A4 | 337 | 230 | 107 | 0.6825 |  |
| hgb_R1_no_growth | N1 | 316 | 302 | 14 | 0.9557 |  |
| hgb_R1_no_growth | N2 | 736 | 708 | 28 | 0.9620 |  |
| hgb_R1_no_growth | N3 | 41 | 31 | 10 | 0.7561 | small support |
| hgb_R1_no_growth | N4 | 247 | 240 | 7 | 0.9717 |  |
| hgb_R1_no_growth | S1 | 276 | 274 | 2 | 0.9928 |  |
| hgb_R1_no_growth | S2 | 1 | 1 | 0 | 1.0000 | sparse/unstable; not selected on |
| hgb_R1_no_growth | S3 | 814 | 814 | 0 | 1.0000 |  |
| hgb_R1_no_growth | S4 | 8 | 2 | 6 | 0.2500 | sparse/unstable; not selected on |
| hgb_R2 | A1 | 2745 | 2689 | 56 | 0.9796 |  |
| hgb_R2 | A2 | 930 | 855 | 75 | 0.9194 |  |
| hgb_R2 | A3 | 485 | 481 | 4 | 0.9918 |  |
| hgb_R2 | A4 | 337 | 258 | 79 | 0.7656 |  |
| hgb_R2 | N1 | 316 | 302 | 14 | 0.9557 |  |
| hgb_R2 | N2 | 736 | 704 | 32 | 0.9565 |  |
| hgb_R2 | N3 | 41 | 21 | 20 | 0.5122 | small support |
| hgb_R2 | N4 | 247 | 239 | 8 | 0.9676 |  |
| hgb_R2 | S1 | 276 | 274 | 2 | 0.9928 |  |
| hgb_R2 | S2 | 1 | 1 | 0 | 1.0000 | sparse/unstable; not selected on |
| hgb_R2 | S3 | 814 | 814 | 0 | 1.0000 |  |
| hgb_R2 | S4 | 8 | 6 | 2 | 0.7500 | sparse/unstable; not selected on |
| hgb_R2_no_growth | A1 | 2745 | 1075 | 1670 | 0.3916 |  |
| hgb_R2_no_growth | A2 | 930 | 842 | 88 | 0.9054 |  |
| hgb_R2_no_growth | A3 | 485 | 485 | 0 | 1.0000 |  |
| hgb_R2_no_growth | A4 | 337 | 240 | 97 | 0.7122 |  |
| hgb_R2_no_growth | N1 | 316 | 301 | 15 | 0.9525 |  |
| hgb_R2_no_growth | N2 | 736 | 709 | 27 | 0.9633 |  |
| hgb_R2_no_growth | N3 | 41 | 26 | 15 | 0.6341 | small support |
| hgb_R2_no_growth | N4 | 247 | 239 | 8 | 0.9676 |  |
| hgb_R2_no_growth | S1 | 276 | 274 | 2 | 0.9928 |  |
| hgb_R2_no_growth | S2 | 1 | 1 | 0 | 1.0000 | sparse/unstable; not selected on |
| hgb_R2_no_growth | S3 | 814 | 814 | 0 | 1.0000 |  |
| hgb_R2_no_growth | S4 | 8 | 2 | 6 | 0.2500 | sparse/unstable; not selected on |
| hgb_R3 | A1 | 2745 | 2689 | 56 | 0.9796 |  |
| hgb_R3 | A2 | 930 | 850 | 80 | 0.9140 |  |
| hgb_R3 | A3 | 485 | 481 | 4 | 0.9918 |  |
| hgb_R3 | A4 | 337 | 264 | 73 | 0.7834 |  |
| hgb_R3 | N1 | 316 | 301 | 15 | 0.9525 |  |
| hgb_R3 | N2 | 736 | 702 | 34 | 0.9538 |  |
| hgb_R3 | N3 | 41 | 24 | 17 | 0.5854 | small support |
| hgb_R3 | N4 | 247 | 239 | 8 | 0.9676 |  |
| hgb_R3 | S1 | 276 | 274 | 2 | 0.9928 |  |
| hgb_R3 | S2 | 1 | 1 | 0 | 1.0000 | sparse/unstable; not selected on |
| hgb_R3 | S3 | 814 | 814 | 0 | 1.0000 |  |
| hgb_R3 | S4 | 8 | 6 | 2 | 0.7500 | sparse/unstable; not selected on |
| hgb_R4 | A1 | 2745 | 1079 | 1666 | 0.3931 |  |
| hgb_R4 | A2 | 930 | 840 | 90 | 0.9032 |  |
| hgb_R4 | A3 | 485 | 485 | 0 | 1.0000 |  |
| hgb_R4 | A4 | 337 | 240 | 97 | 0.7122 |  |
| hgb_R4 | N1 | 316 | 303 | 13 | 0.9589 |  |
| hgb_R4 | N2 | 736 | 709 | 27 | 0.9633 |  |
| hgb_R4 | N3 | 41 | 32 | 9 | 0.7805 | small support |
| hgb_R4 | N4 | 247 | 239 | 8 | 0.9676 |  |
| hgb_R4 | S1 | 276 | 273 | 3 | 0.9891 |  |
| hgb_R4 | S2 | 1 | 1 | 0 | 1.0000 | sparse/unstable; not selected on |
| hgb_R4 | S3 | 814 | 814 | 0 | 1.0000 |  |
| hgb_R4 | S4 | 8 | 3 | 5 | 0.3750 | sparse/unstable; not selected on |
| hgb_R5 | A1 | 2745 | 1540 | 1205 | 0.5610 |  |
| hgb_R5 | A2 | 930 | 887 | 43 | 0.9538 |  |
| hgb_R5 | A3 | 485 | 485 | 0 | 1.0000 |  |
| hgb_R5 | A4 | 337 | 311 | 26 | 0.9228 |  |
| hgb_R5 | N1 | 316 | 302 | 14 | 0.9557 |  |
| hgb_R5 | N2 | 736 | 706 | 30 | 0.9592 |  |
| hgb_R5 | N3 | 41 | 31 | 10 | 0.7561 | small support |
| hgb_R5 | N4 | 247 | 239 | 8 | 0.9676 |  |
| hgb_R5 | S1 | 276 | 274 | 2 | 0.9928 |  |
| hgb_R5 | S2 | 1 | 1 | 0 | 1.0000 | sparse/unstable; not selected on |
| hgb_R5 | S3 | 814 | 814 | 0 | 1.0000 |  |
| hgb_R5 | S4 | 8 | 6 | 2 | 0.7500 | sparse/unstable; not selected on |
| xgb_R0 | A1 | 2745 | 2683 | 62 | 0.9774 |  |
| xgb_R0 | A2 | 930 | 815 | 115 | 0.8763 |  |
| xgb_R0 | A3 | 485 | 484 | 1 | 0.9979 |  |
| xgb_R0 | A4 | 337 | 233 | 104 | 0.6914 |  |
| xgb_R0 | N1 | 316 | 300 | 16 | 0.9494 |  |
| xgb_R0 | N2 | 736 | 711 | 25 | 0.9660 |  |
| xgb_R0 | N3 | 41 | 23 | 18 | 0.5610 | small support |
| xgb_R0 | N4 | 247 | 241 | 6 | 0.9757 |  |
| xgb_R0 | S1 | 276 | 273 | 3 | 0.9891 |  |
| xgb_R0 | S2 | 1 | 1 | 0 | 1.0000 | sparse/unstable; not selected on |
| xgb_R0 | S3 | 814 | 814 | 0 | 1.0000 |  |
| xgb_R0 | S4 | 8 | 6 | 2 | 0.7500 | sparse/unstable; not selected on |
| xgb_R0_no_growth | A1 | 2745 | 1189 | 1556 | 0.4332 |  |
| xgb_R0_no_growth | A2 | 930 | 813 | 117 | 0.8742 |  |
| xgb_R0_no_growth | A3 | 485 | 485 | 0 | 1.0000 |  |
| xgb_R0_no_growth | A4 | 337 | 238 | 99 | 0.7062 |  |
| xgb_R0_no_growth | N1 | 316 | 302 | 14 | 0.9557 |  |
| xgb_R0_no_growth | N2 | 736 | 712 | 24 | 0.9674 |  |
| xgb_R0_no_growth | N3 | 41 | 27 | 14 | 0.6585 | small support |
| xgb_R0_no_growth | N4 | 247 | 242 | 5 | 0.9798 |  |
| xgb_R0_no_growth | S1 | 276 | 274 | 2 | 0.9928 |  |
| xgb_R0_no_growth | S2 | 1 | 1 | 0 | 1.0000 | sparse/unstable; not selected on |
| xgb_R0_no_growth | S3 | 814 | 814 | 0 | 1.0000 |  |
| xgb_R0_no_growth | S4 | 8 | 3 | 5 | 0.3750 | sparse/unstable; not selected on |
| xgb_R1 | A1 | 2745 | 2690 | 55 | 0.9800 |  |
| xgb_R1 | A2 | 930 | 812 | 118 | 0.8731 |  |
| xgb_R1 | A3 | 485 | 483 | 2 | 0.9959 |  |
| xgb_R1 | A4 | 337 | 209 | 128 | 0.6202 |  |
| xgb_R1 | N1 | 316 | 299 | 17 | 0.9462 |  |
| xgb_R1 | N2 | 736 | 711 | 25 | 0.9660 |  |
| xgb_R1 | N3 | 41 | 28 | 13 | 0.6829 | small support |
| xgb_R1 | N4 | 247 | 240 | 7 | 0.9717 |  |
| xgb_R1 | S1 | 276 | 273 | 3 | 0.9891 |  |
| xgb_R1 | S2 | 1 | 1 | 0 | 1.0000 | sparse/unstable; not selected on |
| xgb_R1 | S3 | 814 | 814 | 0 | 1.0000 |  |
| xgb_R1 | S4 | 8 | 6 | 2 | 0.7500 | sparse/unstable; not selected on |
| xgb_R1_no_growth | A1 | 2745 | 1198 | 1547 | 0.4364 |  |
| xgb_R1_no_growth | A2 | 930 | 816 | 114 | 0.8774 |  |
| xgb_R1_no_growth | A3 | 485 | 485 | 0 | 1.0000 |  |
| xgb_R1_no_growth | A4 | 337 | 229 | 108 | 0.6795 |  |
| xgb_R1_no_growth | N1 | 316 | 299 | 17 | 0.9462 |  |
| xgb_R1_no_growth | N2 | 736 | 712 | 24 | 0.9674 |  |
| xgb_R1_no_growth | N3 | 41 | 27 | 14 | 0.6585 | small support |
| xgb_R1_no_growth | N4 | 247 | 245 | 2 | 0.9919 |  |
| xgb_R1_no_growth | S1 | 276 | 274 | 2 | 0.9928 |  |
| xgb_R1_no_growth | S2 | 1 | 1 | 0 | 1.0000 | sparse/unstable; not selected on |
| xgb_R1_no_growth | S3 | 814 | 814 | 0 | 1.0000 |  |
| xgb_R1_no_growth | S4 | 8 | 3 | 5 | 0.3750 | sparse/unstable; not selected on |
| xgb_R2 | A1 | 2745 | 2686 | 59 | 0.9785 |  |
| xgb_R2 | A2 | 930 | 850 | 80 | 0.9140 |  |
| xgb_R2 | A3 | 485 | 481 | 4 | 0.9918 |  |
| xgb_R2 | A4 | 337 | 244 | 93 | 0.7240 |  |
| xgb_R2 | N1 | 316 | 298 | 18 | 0.9430 |  |
| xgb_R2 | N2 | 736 | 710 | 26 | 0.9647 |  |
| xgb_R2 | N3 | 41 | 23 | 18 | 0.5610 | small support |
| xgb_R2 | N4 | 247 | 240 | 7 | 0.9717 |  |
| xgb_R2 | S1 | 276 | 272 | 4 | 0.9855 |  |
| xgb_R2 | S2 | 1 | 1 | 0 | 1.0000 | sparse/unstable; not selected on |
| xgb_R2 | S3 | 814 | 814 | 0 | 1.0000 |  |
| xgb_R2 | S4 | 8 | 6 | 2 | 0.7500 | sparse/unstable; not selected on |
| xgb_R2_no_growth | A1 | 2745 | 1282 | 1463 | 0.4670 |  |
| xgb_R2_no_growth | A2 | 930 | 846 | 84 | 0.9097 |  |
| xgb_R2_no_growth | A3 | 485 | 485 | 0 | 1.0000 |  |
| xgb_R2_no_growth | A4 | 337 | 249 | 88 | 0.7389 |  |
| xgb_R2_no_growth | N1 | 316 | 299 | 17 | 0.9462 |  |
| xgb_R2_no_growth | N2 | 736 | 709 | 27 | 0.9633 |  |
| xgb_R2_no_growth | N3 | 41 | 27 | 14 | 0.6585 | small support |
| xgb_R2_no_growth | N4 | 247 | 242 | 5 | 0.9798 |  |
| xgb_R2_no_growth | S1 | 276 | 274 | 2 | 0.9928 |  |
| xgb_R2_no_growth | S2 | 1 | 1 | 0 | 1.0000 | sparse/unstable; not selected on |
| xgb_R2_no_growth | S3 | 814 | 814 | 0 | 1.0000 |  |
| xgb_R2_no_growth | S4 | 8 | 4 | 4 | 0.5000 | sparse/unstable; not selected on |
| xgb_R3 | A1 | 2745 | 2690 | 55 | 0.9800 |  |
| xgb_R3 | A2 | 930 | 851 | 79 | 0.9151 |  |
| xgb_R3 | A3 | 485 | 481 | 4 | 0.9918 |  |
| xgb_R3 | A4 | 337 | 241 | 96 | 0.7151 |  |
| xgb_R3 | N1 | 316 | 300 | 16 | 0.9494 |  |
| xgb_R3 | N2 | 736 | 709 | 27 | 0.9633 |  |
| xgb_R3 | N3 | 41 | 28 | 13 | 0.6829 | small support |
| xgb_R3 | N4 | 247 | 240 | 7 | 0.9717 |  |
| xgb_R3 | S1 | 276 | 272 | 4 | 0.9855 |  |
| xgb_R3 | S2 | 1 | 1 | 0 | 1.0000 | sparse/unstable; not selected on |
| xgb_R3 | S3 | 814 | 814 | 0 | 1.0000 |  |
| xgb_R3 | S4 | 8 | 6 | 2 | 0.7500 | sparse/unstable; not selected on |
| xgb_R4 | A1 | 2745 | 1307 | 1438 | 0.4761 |  |
| xgb_R4 | A2 | 930 | 846 | 84 | 0.9097 |  |
| xgb_R4 | A3 | 485 | 485 | 0 | 1.0000 |  |
| xgb_R4 | A4 | 337 | 237 | 100 | 0.7033 |  |
| xgb_R4 | N1 | 316 | 298 | 18 | 0.9430 |  |
| xgb_R4 | N2 | 736 | 710 | 26 | 0.9647 |  |
| xgb_R4 | N3 | 41 | 26 | 15 | 0.6341 | small support |
| xgb_R4 | N4 | 247 | 245 | 2 | 0.9919 |  |
| xgb_R4 | S1 | 276 | 274 | 2 | 0.9928 |  |
| xgb_R4 | S2 | 1 | 1 | 0 | 1.0000 | sparse/unstable; not selected on |
| xgb_R4 | S3 | 814 | 814 | 0 | 1.0000 |  |
| xgb_R4 | S4 | 8 | 5 | 3 | 0.6250 | sparse/unstable; not selected on |
| xgb_R5 | A1 | 2745 | 1772 | 973 | 0.6455 |  |
| xgb_R5 | A2 | 930 | 908 | 22 | 0.9763 |  |
| xgb_R5 | A3 | 485 | 485 | 0 | 1.0000 |  |
| xgb_R5 | A4 | 337 | 324 | 13 | 0.9614 |  |
| xgb_R5 | N1 | 316 | 297 | 19 | 0.9399 |  |
| xgb_R5 | N2 | 736 | 710 | 26 | 0.9647 |  |
| xgb_R5 | N3 | 41 | 28 | 13 | 0.6829 | small support |
| xgb_R5 | N4 | 247 | 244 | 3 | 0.9879 |  |
| xgb_R5 | S1 | 276 | 274 | 2 | 0.9928 |  |
| xgb_R5 | S2 | 1 | 1 | 0 | 1.0000 | sparse/unstable; not selected on |
| xgb_R5 | S3 | 814 | 814 | 0 | 1.0000 |  |
| xgb_R5 | S4 | 8 | 6 | 2 | 0.7500 | sparse/unstable; not selected on |


## 10. Hard negatives and review tradeoffs

FPR counts only target-0 rows. Legitimate-origin target-1 rows are not false positives under this synthetic target. Each row reports its denominator; diagnostic private category names never enter X.



| Candidate | Category | Support | FP | TN | FPR |
| --- | --- | --- | --- | --- | --- |
| hgb_R0 | H1 | 238 | 39 | 199 | 0.1639 |
| hgb_R0 | H2 | 374 | 19 | 355 | 0.0508 |
| hgb_R0 | H3 | 406 | 15 | 391 | 0.0369 |
| hgb_R0 | H4 | 292 | 14 | 278 | 0.0479 |
| hgb_R0 | H5 | 214 | 21 | 193 | 0.0981 |
| hgb_R0 | H6 | 424 | 6 | 418 | 0.0142 |
| hgb_R0 | H7 | 359 | 2 | 357 | 0.0056 |
| hgb_R0 | H8 | 460 | 15 | 445 | 0.0326 |
| hgb_R0 | campaign_member_target0 | 1796 | 99 | 1697 | 0.0551 |
| hgb_R0 | routine | 5382 | 83 | 5299 | 0.0154 |
| hgb_R0_no_growth | H1 | 238 | 44 | 194 | 0.1849 |
| hgb_R0_no_growth | H2 | 374 | 26 | 348 | 0.0695 |
| hgb_R0_no_growth | H3 | 406 | 20 | 386 | 0.0493 |
| hgb_R0_no_growth | H4 | 292 | 27 | 265 | 0.0925 |
| hgb_R0_no_growth | H5 | 214 | 25 | 189 | 0.1168 |
| hgb_R0_no_growth | H6 | 424 | 12 | 412 | 0.0283 |
| hgb_R0_no_growth | H7 | 359 | 18 | 341 | 0.0501 |
| hgb_R0_no_growth | H8 | 460 | 8 | 452 | 0.0174 |
| hgb_R0_no_growth | campaign_member_target0 | 1796 | 112 | 1684 | 0.0624 |
| hgb_R0_no_growth | routine | 5382 | 88 | 5294 | 0.0164 |
| hgb_R1 | H1 | 238 | 36 | 202 | 0.1513 |
| hgb_R1 | H2 | 374 | 18 | 356 | 0.0481 |
| hgb_R1 | H3 | 406 | 16 | 390 | 0.0394 |
| hgb_R1 | H4 | 292 | 16 | 276 | 0.0548 |
| hgb_R1 | H5 | 214 | 23 | 191 | 0.1075 |
| hgb_R1 | H6 | 424 | 5 | 419 | 0.0118 |
| hgb_R1 | H7 | 359 | 2 | 357 | 0.0056 |
| hgb_R1 | H8 | 460 | 15 | 445 | 0.0326 |
| hgb_R1 | campaign_member_target0 | 1796 | 95 | 1701 | 0.0529 |
| hgb_R1 | routine | 5382 | 85 | 5297 | 0.0158 |
| hgb_R1_no_growth | H1 | 238 | 45 | 193 | 0.1891 |
| hgb_R1_no_growth | H2 | 374 | 31 | 343 | 0.0829 |
| hgb_R1_no_growth | H3 | 406 | 23 | 383 | 0.0567 |
| hgb_R1_no_growth | H4 | 292 | 30 | 262 | 0.1027 |
| hgb_R1_no_growth | H5 | 214 | 21 | 193 | 0.0981 |
| hgb_R1_no_growth | H6 | 424 | 13 | 411 | 0.0307 |
| hgb_R1_no_growth | H7 | 359 | 19 | 340 | 0.0529 |
| hgb_R1_no_growth | H8 | 460 | 9 | 451 | 0.0196 |
| hgb_R1_no_growth | campaign_member_target0 | 1796 | 115 | 1681 | 0.0640 |
| hgb_R1_no_growth | routine | 5382 | 85 | 5297 | 0.0158 |
| hgb_R2 | H1 | 238 | 31 | 207 | 0.1303 |
| hgb_R2 | H2 | 374 | 23 | 351 | 0.0615 |
| hgb_R2 | H3 | 406 | 13 | 393 | 0.0320 |
| hgb_R2 | H4 | 292 | 14 | 278 | 0.0479 |
| hgb_R2 | H5 | 214 | 22 | 192 | 0.1028 |
| hgb_R2 | H6 | 424 | 7 | 417 | 0.0165 |
| hgb_R2 | H7 | 359 | 1 | 358 | 0.0028 |
| hgb_R2 | H8 | 460 | 15 | 445 | 0.0326 |
| hgb_R2 | campaign_member_target0 | 1796 | 98 | 1698 | 0.0546 |
| hgb_R2 | routine | 5382 | 81 | 5301 | 0.0151 |
| hgb_R2_no_growth | H1 | 238 | 44 | 194 | 0.1849 |
| hgb_R2_no_growth | H2 | 374 | 26 | 348 | 0.0695 |
| hgb_R2_no_growth | H3 | 406 | 24 | 382 | 0.0591 |
| hgb_R2_no_growth | H4 | 292 | 33 | 259 | 0.1130 |
| hgb_R2_no_growth | H5 | 214 | 26 | 188 | 0.1215 |
| hgb_R2_no_growth | H6 | 424 | 22 | 402 | 0.0519 |
| hgb_R2_no_growth | H7 | 359 | 14 | 345 | 0.0390 |
| hgb_R2_no_growth | H8 | 460 | 10 | 450 | 0.0217 |
| hgb_R2_no_growth | campaign_member_target0 | 1796 | 127 | 1669 | 0.0707 |
| hgb_R2_no_growth | routine | 5382 | 106 | 5276 | 0.0197 |
| hgb_R3 | H1 | 238 | 33 | 205 | 0.1387 |
| hgb_R3 | H2 | 374 | 18 | 356 | 0.0481 |
| hgb_R3 | H3 | 406 | 14 | 392 | 0.0345 |
| hgb_R3 | H4 | 292 | 15 | 277 | 0.0514 |
| hgb_R3 | H5 | 214 | 21 | 193 | 0.0981 |
| hgb_R3 | H6 | 424 | 5 | 419 | 0.0118 |
| hgb_R3 | H7 | 359 | 1 | 358 | 0.0028 |
| hgb_R3 | H8 | 460 | 15 | 445 | 0.0326 |
| hgb_R3 | campaign_member_target0 | 1796 | 98 | 1698 | 0.0546 |
| hgb_R3 | routine | 5382 | 80 | 5302 | 0.0149 |
| hgb_R4 | H1 | 238 | 47 | 191 | 0.1975 |
| hgb_R4 | H2 | 374 | 25 | 349 | 0.0668 |
| hgb_R4 | H3 | 406 | 26 | 380 | 0.0640 |
| hgb_R4 | H4 | 292 | 32 | 260 | 0.1096 |
| hgb_R4 | H5 | 214 | 27 | 187 | 0.1262 |
| hgb_R4 | H6 | 424 | 24 | 400 | 0.0566 |
| hgb_R4 | H7 | 359 | 15 | 344 | 0.0418 |
| hgb_R4 | H8 | 460 | 10 | 450 | 0.0217 |
| hgb_R4 | campaign_member_target0 | 1796 | 118 | 1678 | 0.0657 |
| hgb_R4 | routine | 5382 | 107 | 5275 | 0.0199 |
| hgb_R5 | H1 | 238 | 59 | 179 | 0.2479 |
| hgb_R5 | H2 | 374 | 36 | 338 | 0.0963 |
| hgb_R5 | H3 | 406 | 41 | 365 | 0.1010 |
| hgb_R5 | H4 | 292 | 59 | 233 | 0.2021 |
| hgb_R5 | H5 | 214 | 33 | 181 | 0.1542 |
| hgb_R5 | H6 | 424 | 54 | 370 | 0.1274 |
| hgb_R5 | H7 | 359 | 49 | 310 | 0.1365 |
| hgb_R5 | H8 | 460 | 73 | 387 | 0.1587 |
| hgb_R5 | campaign_member_target0 | 1796 | 280 | 1516 | 0.1559 |
| hgb_R5 | routine | 5382 | 314 | 5068 | 0.0583 |
| xgb_R0 | H1 | 238 | 45 | 193 | 0.1891 |
| xgb_R0 | H2 | 374 | 31 | 343 | 0.0829 |
| xgb_R0 | H3 | 406 | 19 | 387 | 0.0468 |
| xgb_R0 | H4 | 292 | 23 | 269 | 0.0788 |
| xgb_R0 | H5 | 214 | 25 | 189 | 0.1168 |
| xgb_R0 | H6 | 424 | 6 | 418 | 0.0142 |
| xgb_R0 | H7 | 359 | 4 | 355 | 0.0111 |
| xgb_R0 | H8 | 460 | 17 | 443 | 0.0370 |
| xgb_R0 | campaign_member_target0 | 1796 | 125 | 1671 | 0.0696 |
| xgb_R0 | routine | 5382 | 93 | 5289 | 0.0173 |
| xgb_R0_no_growth | H1 | 238 | 52 | 186 | 0.2185 |
| xgb_R0_no_growth | H2 | 374 | 44 | 330 | 0.1176 |
| xgb_R0_no_growth | H3 | 406 | 41 | 365 | 0.1010 |
| xgb_R0_no_growth | H4 | 292 | 44 | 248 | 0.1507 |
| xgb_R0_no_growth | H5 | 214 | 32 | 182 | 0.1495 |
| xgb_R0_no_growth | H6 | 424 | 31 | 393 | 0.0731 |
| xgb_R0_no_growth | H7 | 359 | 26 | 333 | 0.0724 |
| xgb_R0_no_growth | H8 | 460 | 16 | 444 | 0.0348 |
| xgb_R0_no_growth | campaign_member_target0 | 1796 | 195 | 1601 | 0.1086 |
| xgb_R0_no_growth | routine | 5382 | 144 | 5238 | 0.0268 |
| xgb_R1 | H1 | 238 | 42 | 196 | 0.1765 |
| xgb_R1 | H2 | 374 | 27 | 347 | 0.0722 |
| xgb_R1 | H3 | 406 | 19 | 387 | 0.0468 |
| xgb_R1 | H4 | 292 | 25 | 267 | 0.0856 |
| xgb_R1 | H5 | 214 | 26 | 188 | 0.1215 |
| xgb_R1 | H6 | 424 | 8 | 416 | 0.0189 |
| xgb_R1 | H7 | 359 | 3 | 356 | 0.0084 |
| xgb_R1 | H8 | 460 | 18 | 442 | 0.0391 |
| xgb_R1 | campaign_member_target0 | 1796 | 125 | 1671 | 0.0696 |
| xgb_R1 | routine | 5382 | 96 | 5286 | 0.0178 |
| xgb_R1_no_growth | H1 | 238 | 54 | 184 | 0.2269 |
| xgb_R1_no_growth | H2 | 374 | 45 | 329 | 0.1203 |
| xgb_R1_no_growth | H3 | 406 | 42 | 364 | 0.1034 |
| xgb_R1_no_growth | H4 | 292 | 44 | 248 | 0.1507 |
| xgb_R1_no_growth | H5 | 214 | 31 | 183 | 0.1449 |
| xgb_R1_no_growth | H6 | 424 | 25 | 399 | 0.0590 |
| xgb_R1_no_growth | H7 | 359 | 24 | 335 | 0.0669 |
| xgb_R1_no_growth | H8 | 460 | 20 | 440 | 0.0435 |
| xgb_R1_no_growth | campaign_member_target0 | 1796 | 192 | 1604 | 0.1069 |
| xgb_R1_no_growth | routine | 5382 | 140 | 5242 | 0.0260 |
| xgb_R2 | H1 | 238 | 39 | 199 | 0.1639 |
| xgb_R2 | H2 | 374 | 28 | 346 | 0.0749 |
| xgb_R2 | H3 | 406 | 20 | 386 | 0.0493 |
| xgb_R2 | H4 | 292 | 24 | 268 | 0.0822 |
| xgb_R2 | H5 | 214 | 26 | 188 | 0.1215 |
| xgb_R2 | H6 | 424 | 11 | 413 | 0.0259 |
| xgb_R2 | H7 | 359 | 4 | 355 | 0.0111 |
| xgb_R2 | H8 | 460 | 19 | 441 | 0.0413 |
| xgb_R2 | campaign_member_target0 | 1796 | 127 | 1669 | 0.0707 |
| xgb_R2 | routine | 5382 | 103 | 5279 | 0.0191 |
| xgb_R2_no_growth | H1 | 238 | 54 | 184 | 0.2269 |
| xgb_R2_no_growth | H2 | 374 | 35 | 339 | 0.0936 |
| xgb_R2_no_growth | H3 | 406 | 43 | 363 | 0.1059 |
| xgb_R2_no_growth | H4 | 292 | 45 | 247 | 0.1541 |
| xgb_R2_no_growth | H5 | 214 | 34 | 180 | 0.1589 |
| xgb_R2_no_growth | H6 | 424 | 45 | 379 | 0.1061 |
| xgb_R2_no_growth | H7 | 359 | 23 | 336 | 0.0641 |
| xgb_R2_no_growth | H8 | 460 | 27 | 433 | 0.0587 |
| xgb_R2_no_growth | campaign_member_target0 | 1796 | 204 | 1592 | 0.1136 |
| xgb_R2_no_growth | routine | 5382 | 178 | 5204 | 0.0331 |
| xgb_R3 | H1 | 238 | 38 | 200 | 0.1597 |
| xgb_R3 | H2 | 374 | 24 | 350 | 0.0642 |
| xgb_R3 | H3 | 406 | 21 | 385 | 0.0517 |
| xgb_R3 | H4 | 292 | 25 | 267 | 0.0856 |
| xgb_R3 | H5 | 214 | 26 | 188 | 0.1215 |
| xgb_R3 | H6 | 424 | 10 | 414 | 0.0236 |
| xgb_R3 | H7 | 359 | 3 | 356 | 0.0084 |
| xgb_R3 | H8 | 460 | 20 | 440 | 0.0435 |
| xgb_R3 | campaign_member_target0 | 1796 | 123 | 1673 | 0.0685 |
| xgb_R3 | routine | 5382 | 102 | 5280 | 0.0190 |
| xgb_R4 | H1 | 238 | 52 | 186 | 0.2185 |
| xgb_R4 | H2 | 374 | 36 | 338 | 0.0963 |
| xgb_R4 | H3 | 406 | 48 | 358 | 0.1182 |
| xgb_R4 | H4 | 292 | 46 | 246 | 0.1575 |
| xgb_R4 | H5 | 214 | 33 | 181 | 0.1542 |
| xgb_R4 | H6 | 424 | 49 | 375 | 0.1156 |
| xgb_R4 | H7 | 359 | 23 | 336 | 0.0641 |
| xgb_R4 | H8 | 460 | 29 | 431 | 0.0630 |
| xgb_R4 | campaign_member_target0 | 1796 | 199 | 1597 | 0.1108 |
| xgb_R4 | routine | 5382 | 173 | 5209 | 0.0321 |
| xgb_R5 | H1 | 238 | 71 | 167 | 0.2983 |
| xgb_R5 | H2 | 374 | 65 | 309 | 0.1738 |
| xgb_R5 | H3 | 406 | 72 | 334 | 0.1773 |
| xgb_R5 | H4 | 292 | 99 | 193 | 0.3390 |
| xgb_R5 | H5 | 214 | 56 | 158 | 0.2617 |
| xgb_R5 | H6 | 424 | 91 | 333 | 0.2146 |
| xgb_R5 | H7 | 359 | 76 | 283 | 0.2117 |
| xgb_R5 | H8 | 460 | 113 | 347 | 0.2457 |
| xgb_R5 | campaign_member_target0 | 1796 | 437 | 1359 | 0.2433 |
| xgb_R5 | routine | 5382 | 575 | 4807 | 0.1068 |




| Candidate | ΔN3 recall | ΔA4 recall | ΔH1 FPR | ΔH5 FPR | ΔMacro F1 |
| --- | --- | --- | --- | --- | --- |
| hgb_R0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| hgb_R1 | 0.0488 | -0.0059 | -0.0126 | 0.0093 | 0.0008 |
| hgb_R2 | -0.0244 | 0.0267 | -0.0336 | 0.0047 | 0.0036 |
| hgb_R3 | 0.0488 | 0.0445 | -0.0252 | 0.0000 | 0.0040 |
| xgb_R0 | 0.0244 | -0.0475 | 0.0252 | 0.0187 | -0.0065 |
| xgb_R1 | 0.1463 | -0.1187 | 0.0126 | 0.0234 | -0.0079 |
| xgb_R2 | 0.0244 | -0.0148 | 0.0000 | 0.0234 | -0.0046 |
| xgb_R3 | 0.1463 | -0.0237 | -0.0042 | 0.0234 | -0.0035 |


These paired development differences disclose whether weak-family gains coincide with more legitimate-like reviews. They are not significance tests, and no threshold was adjusted to improve a slice.

## 11. Consistent feature-concentration diagnostic

Every serious R0–R3 model uses the same Validation permutation-AP procedure: three repeats, 3,000-row sample, seed20260928, one permutation worker. Scores are average AP drops; absolute values are normalized into mass shares, including negative permutation estimates. Correlated/redundant descriptors can split importance without creating independent information. Sparse families may be poorly represented in the sampled rows. This is not causal importance.



| Candidate | Top feature | Top share | Top3 share | Top5 share |
| --- | --- | --- | --- | --- |
| hgb_R0 | agent_wallet_growth_ratio_7d | 0.6150 | 0.7099 | 0.7722 |
| hgb_R1 | agent_wallet_growth_ratio_7d | 0.6182 | 0.7162 | 0.7798 |
| hgb_R2 | agent_wallet_growth_ratio_7d | 0.6390 | 0.7203 | 0.7825 |
| hgb_R3 | agent_wallet_growth_ratio_7d | 0.6340 | 0.7160 | 0.7779 |
| xgb_R0 | agent_wallet_growth_ratio_7d | 0.5865 | 0.6645 | 0.7298 |
| xgb_R1 | agent_wallet_growth_ratio_7d | 0.5843 | 0.6608 | 0.7225 |
| xgb_R2 | agent_wallet_growth_ratio_7d | 0.6671 | 0.7441 | 0.7984 |
| xgb_R3 | agent_wallet_growth_ratio_7d | 0.6754 | 0.7526 | 0.8073 |




| Candidate | current | structuring | network | agent | coverage | new_N3 | new_A4 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hgb_R0 | 0.0199 | 0.0767 | 0.1253 | 0.7621 | 0.0161 | 0.0000 | 0.0000 |
| hgb_R1 | 0.0171 | 0.0759 | 0.1201 | 0.7671 | 0.0147 | 0.0051 | 0.0000 |
| hgb_R2 | 0.0157 | 0.0720 | 0.1208 | 0.7592 | 0.0116 | 0.0000 | 0.0207 |
| hgb_R3 | 0.0155 | 0.0745 | 0.1230 | 0.7471 | 0.0123 | 0.0058 | 0.0217 |
| xgb_R0 | 0.0170 | 0.0882 | 0.1265 | 0.7371 | 0.0311 | 0.0000 | 0.0000 |
| xgb_R1 | 0.0161 | 0.0862 | 0.1293 | 0.7254 | 0.0312 | 0.0118 | 0.0000 |
| xgb_R2 | 0.0085 | 0.0692 | 0.1084 | 0.7688 | 0.0212 | 0.0000 | 0.0239 |
| xgb_R3 | 0.0065 | 0.0661 | 0.1048 | 0.7744 | 0.0219 | 0.0020 | 0.0244 |




| Reference comparison | Stage 11 | Stage 13 recomputation |
| --- | --- | --- |
| Top feature share | 0.6150 | 0.6150 |
| Agent domain mass | 0.7621 | 0.7621 |


All per-feature AP drops and repeat SDs are in `stage13_feature_concentration.json`. XGBoost is now compared using permutation AP, rather than the native normalized gain reported in Stage 11; native gain’s earlier distribution of importance is not directly comparable to these shares.

## 12. Train/Validation distribution shift

Observed summaries exclude only the documented per-column marker. Missing rates use all rows in the slice. No transform or dataset change was used to reduce shift. Overall, both targets, relevant positive domains/families, routine target0 and relevant H cohorts are shown; JSON retains all twelve families, three domains and ten normal groups for all eight inspected columns.

### `agent_new_wallet_share_7d`



| Partition | Slice | N | Available | Missing rate | Mean | Median | SD | Q05 | Q25 | Q75 | Q95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | overall | 60000 | 36943 | 0.3843 | 0.8718 | 0.8750 | 0.0995 | 0.6957 | 0.8077 | 0.9500 | 1.0000 |
| train | target0 | 39781 | 20370 | 0.4879 | 0.8608 | 0.8571 | 0.1045 | 0.6800 | 0.7931 | 0.9412 | 1.0000 |
| train | target1 | 20219 | 16573 | 0.1803 | 0.8852 | 0.8929 | 0.0914 | 0.7177 | 0.8293 | 0.9545 | 1.0000 |
| train | A1 | 11476 | 11040 | 0.0380 | 0.9030 | 0.9130 | 0.0819 | 0.7500 | 0.8529 | 0.9688 | 1.0000 |
| train | A2 | 3770 | 3679 | 0.0241 | 0.8641 | 0.8696 | 0.0994 | 0.6757 | 0.8000 | 0.9375 | 1.0000 |
| train | agent | 15432 | 14888 | 0.0353 | 0.8880 | 0.8966 | 0.0895 | 0.7222 | 0.8333 | 0.9565 | 1.0000 |
| train | H7 | 1475 | 663 | 0.5505 | 0.8640 | 0.8750 | 0.0955 | 0.7143 | 0.8077 | 0.9286 | 1.0000 |
| train | H8 | 1677 | 743 | 0.5569 | 0.8449 | 0.8462 | 0.1025 | 0.6667 | 0.7727 | 0.9286 | 1.0000 |
| train | routine | 21407 | 11311 | 0.4716 | 0.8641 | 0.8636 | 0.1066 | 0.6804 | 0.8000 | 0.9545 | 1.0000 |
| validation | overall | 15000 | 9306 | 0.3796 | 0.6395 | 0.6286 | 0.1919 | 0.3333 | 0.5000 | 0.7778 | 1.0000 |
| validation | target0 | 9945 | 5192 | 0.4779 | 0.6067 | 0.5909 | 0.1955 | 0.3158 | 0.4667 | 0.7273 | 1.0000 |
| validation | target1 | 5055 | 4114 | 0.1862 | 0.6809 | 0.6842 | 0.1788 | 0.3571 | 0.5625 | 0.8235 | 1.0000 |
| validation | A1 | 2745 | 2648 | 0.0353 | 0.7492 | 0.7500 | 0.1339 | 0.5429 | 0.6333 | 0.8571 | 1.0000 |
| validation | A2 | 930 | 904 | 0.0280 | 0.5932 | 0.5652 | 0.1984 | 0.2963 | 0.4615 | 0.7500 | 0.9375 |
| validation | agent | 3835 | 3701 | 0.0349 | 0.6925 | 0.6957 | 0.1741 | 0.3810 | 0.5714 | 0.8333 | 1.0000 |
| validation | H7 | 359 | 153 | 0.5738 | 0.6678 | 0.6316 | 0.1595 | 0.4443 | 0.5556 | 0.8000 | 1.0000 |
| validation | H8 | 460 | 217 | 0.5283 | 0.5557 | 0.5556 | 0.1617 | 0.2857 | 0.4500 | 0.6842 | 0.8000 |
| validation | routine | 5382 | 2956 | 0.4508 | 0.6067 | 0.5882 | 0.2018 | 0.3125 | 0.4615 | 0.7391 | 1.0000 |


### `agent_wallet_growth_ratio_7d`



| Partition | Slice | N | Available | Missing rate | Mean | Median | SD | Q05 | Q25 | Q75 | Q95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | overall | 60000 | 36943 | 0.3843 | 1.3970 | 1.1538 | 0.9587 | 0.5306 | 0.8485 | 1.6238 | 3.0000 |
| train | target0 | 39781 | 20370 | 0.4879 | 0.9577 | 0.9565 | 0.3013 | 0.4615 | 0.7429 | 1.1837 | 1.4286 |
| train | target1 | 20219 | 16573 | 0.1803 | 1.9370 | 1.6957 | 1.1867 | 0.7170 | 1.2245 | 2.2500 | 4.0000 |
| train | A1 | 11476 | 11040 | 0.0380 | 2.4006 | 2.0000 | 1.1968 | 1.5238 | 1.6957 | 2.6000 | 4.6683 |
| train | A2 | 3770 | 3679 | 0.0241 | 1.4015 | 1.1538 | 0.8712 | 0.5833 | 0.8667 | 1.6800 | 3.0000 |
| train | agent | 15432 | 14888 | 0.0353 | 2.0431 | 1.7647 | 1.2031 | 0.7727 | 1.4610 | 2.3333 | 4.2500 |
| train | H7 | 1475 | 663 | 0.5505 | 1.0371 | 1.0556 | 0.2623 | 0.5714 | 0.8571 | 1.2340 | 1.4488 |
| train | H8 | 1677 | 743 | 0.5569 | 1.0457 | 1.0588 | 0.2569 | 0.5915 | 0.8615 | 1.2519 | 1.4286 |
| train | routine | 21407 | 11311 | 0.4716 | 0.9348 | 0.9302 | 0.3074 | 0.4407 | 0.7143 | 1.1579 | 1.4286 |
| validation | overall | 15000 | 9306 | 0.3796 | 1.3533 | 1.1698 | 0.8288 | 0.5560 | 0.8571 | 1.6216 | 2.7500 |
| validation | target0 | 9945 | 5192 | 0.4779 | 0.9817 | 0.9831 | 0.3105 | 0.5000 | 0.7500 | 1.2222 | 1.4444 |
| validation | target1 | 5055 | 4114 | 0.1862 | 1.8221 | 1.6923 | 1.0189 | 0.6842 | 1.1865 | 2.1333 | 3.4377 |
| validation | A1 | 2745 | 2648 | 0.0353 | 2.2638 | 2.0000 | 1.0082 | 1.5238 | 1.7143 | 2.4444 | 4.0000 |
| validation | A2 | 930 | 904 | 0.0280 | 1.3228 | 1.0833 | 0.7854 | 0.5959 | 0.8093 | 1.5522 | 3.2000 |
| validation | agent | 3835 | 3701 | 0.0349 | 1.9156 | 1.7500 | 1.0281 | 0.7451 | 1.4074 | 2.1818 | 3.6000 |
| validation | H7 | 359 | 153 | 0.5738 | 1.0712 | 1.1250 | 0.2898 | 0.5455 | 0.8571 | 1.3191 | 1.4202 |
| validation | H8 | 460 | 217 | 0.5283 | 1.0772 | 1.0909 | 0.3268 | 0.5808 | 0.7907 | 1.3103 | 1.4870 |
| validation | routine | 5382 | 2956 | 0.4508 | 0.9490 | 0.9400 | 0.3183 | 0.4507 | 0.7143 | 1.1915 | 1.4405 |


### `candidate_agent_cash_direction_persistence_24h`



| Partition | Slice | N | Available | Missing rate | Mean | Median | SD | Q05 | Q25 | Q75 | Q95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | overall | 60000 | 60000 | 0.0000 | 0.2145 | 0.2453 | 0.2275 | 0.0000 | 0.0000 | 0.2652 | 0.7207 |
| train | target0 | 39781 | 39781 | 0.0000 | 0.1888 | 0.1981 | 0.2138 | 0.0000 | 0.0000 | 0.2500 | 0.5214 |
| train | target1 | 20219 | 20219 | 0.0000 | 0.2650 | 0.2500 | 0.2447 | 0.0000 | 0.0037 | 0.4644 | 0.7500 |
| train | A4 | 1353 | 1353 | 0.0000 | 0.5859 | 0.5281 | 0.2632 | 0.2240 | 0.4249 | 0.7500 | 1.0000 |
| train | agent | 15432 | 15432 | 0.0000 | 0.3109 | 0.2500 | 0.2397 | 0.0000 | 0.1437 | 0.4991 | 0.7500 |
| train | H8 | 1677 | 1677 | 0.0000 | 0.1898 | 0.0863 | 0.2267 | 0.0000 | 0.0000 | 0.2658 | 0.6573 |
| train | routine | 21407 | 21407 | 0.0000 | 0.1708 | 0.1256 | 0.1992 | 0.0000 | 0.0000 | 0.2500 | 0.5000 |
| validation | overall | 15000 | 15000 | 0.0000 | 0.2092 | 0.2429 | 0.2210 | 0.0000 | 0.0000 | 0.2527 | 0.6596 |
| validation | target0 | 9945 | 9945 | 0.0000 | 0.1874 | 0.2095 | 0.2085 | 0.0000 | 0.0000 | 0.2500 | 0.5000 |
| validation | target1 | 5055 | 5055 | 0.0000 | 0.2523 | 0.2500 | 0.2379 | 0.0000 | 0.0001 | 0.4065 | 0.7500 |
| validation | A4 | 337 | 337 | 0.0000 | 0.5572 | 0.5000 | 0.2487 | 0.1883 | 0.4235 | 0.7491 | 0.9997 |
| validation | agent | 3835 | 3835 | 0.0000 | 0.2978 | 0.2500 | 0.2335 | 0.0000 | 0.1341 | 0.4890 | 0.7500 |
| validation | H8 | 460 | 460 | 0.0000 | 0.2187 | 0.2061 | 0.2331 | 0.0000 | 0.0000 | 0.4216 | 0.7228 |
| validation | routine | 5382 | 5382 | 0.0000 | 0.1692 | 0.1444 | 0.1949 | 0.0000 | 0.0000 | 0.2500 | 0.5000 |


### `candidate_agent_cash_service_share_24h`



| Partition | Slice | N | Available | Missing rate | Mean | Median | SD | Q05 | Q25 | Q75 | Q95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | overall | 60000 | 60000 | 0.0000 | 0.5109 | 0.5833 | 0.3678 | 0.0000 | 0.0000 | 0.8000 | 1.0000 |
| train | target0 | 39781 | 39781 | 0.0000 | 0.4809 | 0.5000 | 0.3882 | 0.0000 | 0.0000 | 0.8000 | 1.0000 |
| train | target1 | 20219 | 20219 | 0.0000 | 0.5699 | 0.6364 | 0.3157 | 0.0000 | 0.4000 | 0.8000 | 1.0000 |
| train | A4 | 1353 | 1353 | 0.0000 | 0.7820 | 0.7857 | 0.1501 | 0.5000 | 0.6667 | 0.8889 | 1.0000 |
| train | agent | 15432 | 15432 | 0.0000 | 0.6766 | 0.6923 | 0.2294 | 0.2727 | 0.5333 | 0.8333 | 1.0000 |
| train | H8 | 1677 | 1677 | 0.0000 | 0.4406 | 0.5000 | 0.3738 | 0.0000 | 0.0000 | 0.7500 | 1.0000 |
| train | routine | 21407 | 21407 | 0.0000 | 0.4662 | 0.5000 | 0.4044 | 0.0000 | 0.0000 | 0.8333 | 1.0000 |
| validation | overall | 15000 | 15000 | 0.0000 | 0.5126 | 0.6000 | 0.3696 | 0.0000 | 0.0000 | 0.8000 | 1.0000 |
| validation | target0 | 9945 | 9945 | 0.0000 | 0.4840 | 0.5000 | 0.3907 | 0.0000 | 0.0000 | 0.8000 | 1.0000 |
| validation | target1 | 5055 | 5055 | 0.0000 | 0.5689 | 0.6429 | 0.3167 | 0.0000 | 0.4142 | 0.8000 | 1.0000 |
| validation | A4 | 337 | 337 | 0.0000 | 0.7746 | 0.7778 | 0.1437 | 0.5374 | 0.6667 | 0.8750 | 1.0000 |
| validation | agent | 3835 | 3835 | 0.0000 | 0.6818 | 0.7000 | 0.2213 | 0.2727 | 0.5556 | 0.8333 | 1.0000 |
| validation | H8 | 460 | 460 | 0.0000 | 0.4886 | 0.6000 | 0.3672 | 0.0000 | 0.0000 | 0.8000 | 1.0000 |
| validation | routine | 5382 | 5382 | 0.0000 | 0.4639 | 0.5000 | 0.4038 | 0.0000 | 0.0000 | 0.8333 | 1.0000 |


### `candidate_agent_cash_value_acceleration_24h`



| Partition | Slice | N | Available | Missing rate | Mean | Median | SD | Q05 | Q25 | Q75 | Q95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | overall | 60000 | 38002 | 0.3666 | 3.2334 | 1.0789 | 15.9279 | 0.0000 | 0.0659 | 3.1374 | 10.8003 |
| train | target0 | 39781 | 21033 | 0.4713 | 2.0049 | 0.4707 | 9.6687 | 0.0000 | 0.0303 | 2.1244 | 6.7910 |
| train | target1 | 20219 | 16969 | 0.1607 | 4.7561 | 1.9562 | 21.1682 | 0.0054 | 0.3018 | 4.6302 | 15.4804 |
| train | A4 | 1353 | 1348 | 0.0037 | 6.1151 | 2.8162 | 32.1953 | 0.1743 | 1.3793 | 5.1263 | 11.8772 |
| train | agent | 15432 | 15227 | 0.0133 | 4.9556 | 2.0490 | 21.7091 | 0.0070 | 0.3542 | 4.8327 | 16.2244 |
| train | H8 | 1677 | 780 | 0.5349 | 3.2719 | 1.0488 | 14.5537 | 0.0036 | 0.0644 | 2.8520 | 6.7319 |
| train | routine | 21407 | 11689 | 0.4540 | 1.4534 | 0.1627 | 5.6755 | 0.0000 | 0.0150 | 1.6003 | 5.6826 |
| validation | overall | 15000 | 9522 | 0.3652 | 3.2315 | 1.1665 | 19.1556 | 0.0000 | 0.0618 | 3.3454 | 9.5911 |
| validation | target0 | 9945 | 5335 | 0.4635 | 1.7480 | 0.5380 | 4.4272 | 0.0000 | 0.0301 | 2.2525 | 6.5365 |
| validation | target1 | 5055 | 4187 | 0.1717 | 5.1216 | 2.1968 | 28.3395 | 0.0052 | 0.2555 | 4.5104 | 13.3465 |
| validation | A4 | 337 | 336 | 0.0030 | 3.4068 | 2.6960 | 3.7187 | 0.1062 | 1.4531 | 4.4463 | 8.1736 |
| validation | agent | 3835 | 3762 | 0.0190 | 5.4614 | 2.3198 | 29.8546 | 0.0084 | 0.3316 | 4.6649 | 14.0339 |
| validation | H8 | 460 | 230 | 0.5000 | 2.2380 | 1.5748 | 2.3759 | 0.0078 | 0.1395 | 3.8279 | 7.0769 |
| validation | routine | 5382 | 3068 | 0.4300 | 1.4974 | 0.1506 | 5.2919 | 0.0000 | 0.0145 | 1.6258 | 5.8757 |


### `candidate_prior_reciprocal_count_7d`



| Partition | Slice | N | Available | Missing rate | Mean | Median | SD | Q05 | Q25 | Q75 | Q95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | overall | 60000 | 60000 | 0.0000 | 0.0085 | 0.0000 | 0.0937 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| train | target0 | 39781 | 39781 | 0.0000 | 0.0066 | 0.0000 | 0.0823 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| train | target1 | 20219 | 20219 | 0.0000 | 0.0124 | 0.0000 | 0.1127 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| train | N3 | 120 | 120 | 0.0000 | 0.8000 | 1.0000 | 0.4761 | 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| train | network | 5103 | 5103 | 0.0000 | 0.0357 | 0.0000 | 0.1896 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| train | H6 | 1639 | 1639 | 0.0000 | 0.0537 | 0.0000 | 0.2281 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| train | routine | 21407 | 21407 | 0.0000 | 0.0014 | 0.0000 | 0.0404 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation | overall | 15000 | 15000 | 0.0000 | 0.0124 | 0.0000 | 0.1171 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation | target0 | 9945 | 9945 | 0.0000 | 0.0099 | 0.0000 | 0.1028 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation | target1 | 5055 | 5055 | 0.0000 | 0.0174 | 0.0000 | 0.1410 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation | N3 | 41 | 41 | 0.0000 | 0.9512 | 1.0000 | 0.4390 | 0.0000 | 1.0000 | 1.0000 | 2.0000 |
| validation | network | 1271 | 1271 | 0.0000 | 0.0519 | 0.0000 | 0.2422 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation | H6 | 424 | 424 | 0.0000 | 0.0495 | 0.0000 | 0.2170 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation | routine | 5382 | 5382 | 0.0000 | 0.0043 | 0.0000 | 0.0733 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |


### `candidate_prior_two_hop_return_count_7d`



| Partition | Slice | N | Available | Missing rate | Mean | Median | SD | Q05 | Q25 | Q75 | Q95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | overall | 60000 | 60000 | 0.0000 | 0.0049 | 0.0000 | 0.0739 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| train | target0 | 39781 | 39781 | 0.0000 | 0.0051 | 0.0000 | 0.0755 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| train | target1 | 20219 | 20219 | 0.0000 | 0.0043 | 0.0000 | 0.0705 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| train | N3 | 120 | 120 | 0.0000 | 0.1833 | 0.0000 | 0.4652 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| train | network | 5103 | 5103 | 0.0000 | 0.0086 | 0.0000 | 0.1006 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| train | H6 | 1639 | 1639 | 0.0000 | 0.0482 | 0.0000 | 0.2142 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| train | routine | 21407 | 21407 | 0.0000 | 0.0018 | 0.0000 | 0.0443 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation | overall | 15000 | 15000 | 0.0000 | 0.0121 | 0.0000 | 0.1439 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation | target0 | 9945 | 9945 | 0.0000 | 0.0110 | 0.0000 | 0.1160 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation | target1 | 5055 | 5055 | 0.0000 | 0.0142 | 0.0000 | 0.1871 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation | N3 | 41 | 41 | 0.0000 | 0.1220 | 0.0000 | 0.3948 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| validation | network | 1271 | 1271 | 0.0000 | 0.0354 | 0.0000 | 0.3336 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| validation | H6 | 424 | 424 | 0.0000 | 0.0566 | 0.0000 | 0.2411 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| validation | routine | 5382 | 5382 | 0.0000 | 0.0072 | 0.0000 | 0.0990 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |


### `candidate_selected_path_max_log_value_change`



| Partition | Slice | N | Available | Missing rate | Mean | Median | SD | Q05 | Q25 | Q75 | Q95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | overall | 60000 | 1142 | 0.9810 | 2.0686 | 0.8164 | 2.4822 | 0.0000 | 0.0000 | 4.0744 | 6.8072 |
| train | target0 | 39781 | 696 | 0.9825 | 2.3354 | 1.5624 | 2.4858 | 0.0000 | 0.0000 | 4.3620 | 6.8838 |
| train | target1 | 20219 | 446 | 0.9779 | 1.6522 | 0.0000 | 2.4185 | 0.0000 | 0.0000 | 3.2231 | 6.7257 |
| train | N3 | 120 | 120 | 0.0000 | 0.1925 | 0.0000 | 0.4242 | 0.0000 | 0.0000 | 0.0000 | 1.2458 |
| train | network | 5103 | 286 | 0.9440 | 1.3503 | 0.0000 | 2.2991 | 0.0000 | 0.0000 | 1.5672 | 6.5110 |
| train | H6 | 1639 | 263 | 0.8395 | 2.4376 | 1.9338 | 2.4844 | 0.0000 | 0.0000 | 4.6015 | 6.5747 |
| train | routine | 21407 | 93 | 0.9957 | 2.3960 | 1.5401 | 2.2751 | 0.0000 | 0.0000 | 4.3938 | 6.3605 |
| validation | overall | 15000 | 485 | 0.9677 | 2.3809 | 1.6450 | 2.4606 | 0.0000 | 0.0000 | 4.3007 | 6.8380 |
| validation | target0 | 9945 | 312 | 0.9686 | 2.6317 | 2.3074 | 2.4763 | 0.0000 | 0.0000 | 4.8058 | 6.9384 |
| validation | target1 | 5055 | 173 | 0.9658 | 1.9285 | 0.5446 | 2.3658 | 0.0000 | 0.0000 | 3.6847 | 6.3978 |
| validation | N3 | 41 | 41 | 0.0000 | 0.0721 | 0.0000 | 0.2707 | 0.0000 | 0.0000 | 0.0000 | 0.5161 |
| validation | network | 1271 | 107 | 0.9158 | 1.7342 | 0.0000 | 2.4515 | 0.0000 | 0.0000 | 3.4380 | 6.4501 |
| validation | H6 | 424 | 78 | 0.8160 | 2.7578 | 2.3490 | 2.5379 | 0.0000 | 0.0000 | 5.1716 | 7.0567 |
| validation | routine | 5382 | 86 | 0.9840 | 2.9883 | 3.0549 | 2.4945 | 0.0000 | 0.1748 | 5.2219 | 7.0032 |




| Feature | Validation−Train observed mean | Missing-rate difference |
| --- | --- | --- |
| agent_new_wallet_share_7d | -0.2322 | -0.0047 |
| agent_wallet_growth_ratio_7d | -0.0438 | -0.0047 |
| candidate_agent_cash_direction_persistence_24h | -0.0052 | 0.0000 |
| candidate_agent_cash_service_share_24h | 0.0017 | 0.0000 |
| candidate_agent_cash_value_acceleration_24h | -0.0020 | -0.0014 |
| candidate_prior_reciprocal_count_7d | 0.0039 | 0.0000 |
| candidate_prior_two_hop_return_count_7d | 0.0072 | 0.0000 |
| candidate_selected_path_max_log_value_change | 0.3123 | -0.0133 |


Growth and novelty preserve their Stage 12 shifts because the official columns are unchanged. Novelty’s observed mean remains about 0.8718 versus 0.6395 and its shift was previously found within matched slices. New graph descriptors may reflect partition-local graph density, while cash descriptors reflect service mix and baseline eligibility. The tables identify associations, not the generator mechanism; raw mean differences have different units and should not be ranked as comparable effect sizes.

The new columns also show differences worth retaining: overall two-hop return count rises **0.00485→0.01207**, while within N3 positives it falls **0.1833→0.1220**. Selected-path spread is unavailable on **98.10%/96.77%** of Train/Validation, so its observed distribution concerns a small selected subset. Overall cash-value acceleration means are nearly equal (**3.2334/3.2315**), yet A4-positive means differ substantially (**6.1151/3.4068**). Overall similarity therefore does not establish family-level stability. Persistence and cash-service share have smaller overall shifts, with A4-positive persistence **0.5859→0.5572** and cash share **0.7820→0.7746**. None of these observations was used to alter data, features or the fixed search.

## 13. Selection decision and scientific interpretation



| Added-feature candidate | Passed gates | Failed gates |
| --- | --- | --- |
| hgb_R1 | 11 | A4, N3, dependence, top_share |
| hgb_R2 | 11 | A4, N3, dependence, top_share |
| hgb_R3 | 12 | N3, dependence, top_share |
| xgb_R1 | 11 | A4, H5, dependence, top_share |
| xgb_R2 | 10 | A4, H5, N3, dependence, top_share |
| xgb_R3 | 11 | A4, H5, dependence, top_share |


**B — AGGREGATE PERFORMANCE IMPROVED BUT FEATURE CONCENTRATION REMAINS.** At least one added-feature model improves aggregate Macro F1 by >=.002 without worse N3/A4 recall, but high/extreme dependence or top-feature concentration remains.

The decision follows the plan’s joint gates and fixed decision precedence. A higher headline score alone cannot qualify a model for later final selection. The complete dependence, weak-family, hard-negative, domain-only and concentration results above remain part of the decision even when one metric improves.


HGB R3 meets the aggregate, A4, hard-negative, domain-only and gap tolerances but fails N3 improvement, dependence and top-feature concentration. XGBoost R3 meets the N3 improvement gate but fails A4, H5, dependence and top-feature concentration. R4/R5 can improve selected weak families while sacrificing the aggregate task: HGB R5 reaches A4 recall **0.9228** with Macro F1 **0.8238** and FPR **0.1004**; XGBoost R5 reaches A4 recall **0.9614** with Macro F1 **0.8024** and FPR **0.1664**. Those diagnostic results do not justify promotion.

No candidate is recommended for final selection by this stage. Retain the protected Stage 11 reference as the development benchmark, with its Stage 12 limitations still disclosed. Any further investigation needs a separately bounded plan; the unused fit allowance is not an invitation to expand this run.

The new descriptors target N3 and A4, while growth directly describes A1 and A1 has much greater support. Improving N3/A4 need not supply a replacement for A1 information. Large removal losses therefore establish dependence, not automatically a synthetic artifact. Conversely, a dispersed importance profile does not certify robustness. The experiment tests a small fixed set of descriptors and two configurations; failure to meet gates does not prove that all causal representations or model choices would fail.

Synthetic ground truth, repeated Validation reuse, selected-path compression, sparse N3/S2/S4 support, event dependence and distribution shifts remain limitations. This stage preserves frozen targets and does not certify the reference evaluator against every original written predicate. It supports AML decision-support research, not claims of criminal intent, real-operator effectiveness or production readiness.

## 14. Protection and final verification



| Property | Result |
| --- | --- |
| Protected before | 602 |
| Protected after | 602 |
| Changed protected paths | [] |
| Public commitment unchanged | True |
| Metric sets recomputed | 36 |
| Artifact hashes checked | 36 |
| New model reloads checked | 15 |
| Maximum reload score difference | 0.0000 |
| Final verification | PASS |




| Named public metadata | Before SHA-256 | After SHA-256 |
| --- | --- | --- |
| ml_v3/data/manifests/evaluation_content_commitment.json | efc14471b98103a3ad547d93fc56833d014389efd9d3c6e5be6ba896c70d9d58 | efc14471b98103a3ad547d93fc56833d014389efd9d3c6e5be6ba896c70d9d58 |
| ml_v3/reports/V3_STAGE9_HOLDOUT_SEAL.json | efc14471b98103a3ad547d93fc56833d014389efd9d3c6e5be6ba896c70d9d58 | efc14471b98103a3ad547d93fc56833d014389efd9d3c6e5be6ba896c70d9d58 |


Protection covers the explicit application/V1/V2 allowlists, frozen V3 development data/design, Stage 10A contract/matrices/code, Stage 11 candidates and Stage 12 diagnostics/reports/source. Exact paths, scopes and exclusions are saved in the protection record. No claim is made to inspect every filesystem file or freshly verify unread evaluation bytes. Public hashes certify commitment metadata only.

Final verification rechecks the plan digest/source hashes, official input hashes, all new artifact hashes, 36 Train/Validation metric sets, family/domain/normal slice counts and selected decision. All fifteen new saved models were reloaded: their Validation probabilities and threshold predictions reproduce within the recorded 1e-12 tolerance. Six causal test methods pass. No additional model fits occur during verification or reporting.

## 15. Evidence and reproducible entry points



| Evidence | File |
| --- | --- |
| plan | [stage13_plan.json](stage13_plan.json) |
| reference_reproduction | [stage13_reference_reproduction.json](stage13_reference_reproduction.json) |
| candidate_features | [stage13_candidate_features.json](stage13_candidate_features.json) |
| candidate_results | [stage13_candidate_results.json](stage13_candidate_results.json) |
| growth_dependence | [stage13_growth_dependence.json](stage13_growth_dependence.json) |
| domain_independence | [stage13_domain_independence.json](stage13_domain_independence.json) |
| family_results | [stage13_family_results.json](stage13_family_results.json) |
| hard_negative_results | [stage13_hard_negative_results.json](stage13_hard_negative_results.json) |
| feature_concentration | [stage13_feature_concentration.json](stage13_feature_concentration.json) |
| distribution_shift | [stage13_distribution_shift.json](stage13_distribution_shift.json) |
| selection_decision | [stage13_selection_decision.json](stage13_selection_decision.json) |
| protection | [stage13_protection.json](stage13_protection.json) |
| artifact_manifest | [stage13_artifact_manifest.json](stage13_artifact_manifest.json) |
| final_verification | [stage13_final_verification.json](stage13_final_verification.json) |


Source: `src/stage13_robustness_improvement.py`, `src/run_stage13.py`, `src/verify_stage13.py`, `src/report_stage13.py`; tests: `tests/test_stage13_features.py`. Commands from repository root:

```powershell
python -B -m unittest discover -s ml_v3/tests -p test_stage13_features.py -v
python -B ml_v3/src/run_stage13.py
python -B ml_v3/src/verify_stage13.py
python -B ml_v3/src/report_stage13.py
```

The runner refuses an existing Stage 13 plan/model directory. For a fresh reproduction, preserve this run and use an isolated authorized development checkout with the recorded frozen inputs, source and environment, and a newly captured Stage 13 protection-before snapshot. New feature arrays are under `evidence/stage13/`; new models/scores under `models/stage13_candidates/`. Reused models stay at their protected Stage 11/12 paths. Machine evidence distinguishes all reuse from new fits.

No holdout evaluation, final threshold optimization, calibration, Train+Validation refit, V1 replacement, Flask/dashboard integration or final feature promotion occurred.

**V3 STAGE 13 COMPLETE — WAITING FOR APPROVAL.**
