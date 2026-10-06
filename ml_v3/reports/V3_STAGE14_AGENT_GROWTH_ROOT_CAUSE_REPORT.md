# MODEL V3 — STAGE 14 AGENT WALLET-GROWTH ROOT-CAUSE AND SYNTHETIC-SEPARABILITY DIAGNOSIS

**Technical execution: PASS. Decision: F — MULTIPLE FACTORS; CONTROLLED DEVELOPMENT REDESIGN REQUIRED.**

Growth is a legitimate decision-time behavioural descriptor, but it closely matches the dominant A1 target component in this synthetic development experiment. A1 accounts for **1,634/1,666 (98.08%)** of Validation detections lost after growth removal. Among eligible rows, raw growth separates A1 from H7/H8/routine target-0 rows with **ROC-AUC 0.9939 and AP 0.9898**. This is **HIGH proxy concern for A1**, with counterexamples that prevent a complete predicate or overall-target oracle interpretation.

The effect is shared across HGB, XGBoost, Random Forest and Gradient Boosting. Missingness does not explain the observed-value separation. A separate finding is a frozen evaluator/contract discrepancy: A1 targets use 28d observed coverage, while the corrected growth feature requires 35d. This accounts for **436 Train and 97 Validation A1-positive rows** with unavailable growth.

This is the single consolidated report. Five new diagnostic models were fitted: four requested family exclusions and one Train-only shuffled-label sanity model. No model is promoted. The recommendation is a separately authorized, versioned development redesign addressing target semantics and realistic agent populations while preserving the current experiment.

## 1. Scope, protocol and protected reference

Only frozen development transactions, ground truth, diagnostic metadata, corrected Stage 10A matrices and Stage 11–13 artifacts were used. Inputs remain 60,000 Train and 15,000 Validation rows × 32 numeric features. Diagnostic masks select training rows for the explicitly requested family exclusions; metadata never enters X or prediction inputs. Agent primitives are isolated audit arrays, never new model features.

No holdout directory was enumerated and no holdout data file opened or hashed. Only named public commitment metadata was checked. All prior protected artifacts remain unchanged. Threshold is 0.50 throughout; AP means Average Precision, and confusion matrices are [[TN,FP],[FN,TP]]. Class 1 is the synthetic suspicious-pattern review target.



| Property | Value |
| --- | --- |
| Plan UTC | 2026-09-28T22:31:26.658845+00:00 |
| Plan SHA-256 | dc840c5e01f934b9c26dc11eb947341bbf380840019e181f22270d55c2802817 |
| New fits | 5 |
| Family-removal fits | 4 |
| Shuffle fits | 1 |
| Seed | 20260928 |
| Weights | class1=1.5; class0=1 |
| Model configuration | {'categorical_features': 'from_dtype', 'class_weight': None, 'early_stopping': False, 'interaction_cst': None, 'l2_regularization': 1.0, 'learning_rate': 0.07, 'loss': 'log_loss', 'max_bins': 255, 'max_depth': 6, 'max_features': 1.0, 'max_iter': 200, 'max_leaf_nodes': 31, 'min_samples_leaf': 20, 'monotonic_cst': None, 'n_iter_no_change': 10, 'random_state': 20260928, 'scoring': 'loss', 'tol': 1e-07, 'validation_fraction': 0.1, 'verbose': 0, 'warm_start': False} |
| Environment | {'numpy': '2.4.3', 'python': '3.14.3 (tags/v3.14.3:323c59a, Feb  3 2026, 16:04:56) [MSC v.1944 64 bit (AMD64)]', 'sklearn': '1.9.0', 'threads': 2} |


The plan fixed the diagnostic fits, shuffle split, quartile grids, reused one-feature model and importance procedure before fitting. The source synthesis and decision followed the results. There was no adaptive model search. The reference HGB configuration uses 200 rounds, learning rate .07, depth 6, 31 leaves, minimum leaf 20, L2=1 and no early stopping. Raw documented sentinels are retained; no preprocessing is fitted.



| Partition | Exact reference max difference | accuracy | balanced_accuracy | macro_f1 | suspicious_precision | suspicious_recall | suspicious_f1 | average_precision | roc_auc | false_positive_rate | confusion_matrix |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | 0.0000 | 0.9729 | 0.9676 | 0.9695 | 0.9676 | 0.9513 | 0.9594 | 0.9927 | 0.9957 | 0.0162 | [[39137, 644], [984, 19235]] |
| validation | 0.0000 | 0.9572 | 0.9517 | 0.9521 | 0.9379 | 0.9349 | 0.9364 | 0.9772 | 0.9888 | 0.0315 | [[9632, 313], [329, 4726]] |


## 2. Exact growth semantics and contract check



| Item | Frozen definition |
| --- | --- |
| assisted_W2W | One service using explicit serviced_wallet, including when receiver is serviced; not necessarily sender |
| audit_scope | Independent observable-only primitive calculation exactly matches all 75000 saved growth values. No official matrix regenerated or edited. |
| baseline | (t-35d,t-7d], four disjoint 7d buckets; lower open, upper closed |
| cash_in | One service at named agent for serviced_wallet |
| cash_out | One service at named agent for serviced_wallet |
| cold_start | Unavailable until full 35d observation and baseline count; displayed coverage caps at 28d and cannot establish eligibility |
| current | Included exactly once before state update; type/agent/serviced-wallet/time identify service. Amount is unused. |
| denominator | Median of four weekly DISTINCT serviced-wallet counts, including zero buckets; floor 1 |
| direct_W2W | No agent subject; -1; creates no agent service history |
| eligibility | Agent present; first prior observable service <= t-35d; at least 12 baseline services. No recent distinct/novelty/target gate. |
| formula | D_recent / max(1, median(D_week1,D_week2,D_week3,D_week4)) |
| missing | -1 when absent agent or baseline ineligible; dimensionless nonnegative observed values |
| ordering | UTC timestamp then integer ID; smaller same-time ID is prior; state updated after emission; no cross-partition state |
| recent | (t-7d,t], prior keys < current key, plus current agent service |
| result | PASS: corrected implementation agrees with Stage 10A contract |


For agent a at T, let D be distinct serviced wallets in R=(t−7d,t] including the current service, and B1…B4 the distinct counts in the preceding disjoint weekly buckets. **G=D/max(1,median(B1…B4))**. This summary contains no amount, target, private activation date, campaign membership or future event. Source: [Stage 10A implementation](../src/stage10a_pipeline.py), [contract](../src/stage10a_contract.py). Independent reconstruction matches all 75,000 saved growth values exactly.

### Frozen target semantics differ from the corrected feature contract

The materializer imports `reference_evaluator.py`; `reference.py` is a separate implementation and was not silently substituted. The A1 diagnostic reconstruction reproduces every frozen A1 flag. Corrected feature windows use open lower and closed upper boundaries, full prior keys and 35d observed coverage. Frozen A1 uses closed lower/open upper timestamp windows, excludes equal-time prior services from its recent window, and checks only 28d coverage.



| Partition | Frozen A1 support | Frozen A1 reconstruction mismatches | A1 unavailable growth | Written A1 without frozen A1 | Frozen A1 without written A1 | Unavailable A1 age min | Age max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| train | 11476 | 0 | 436 | 0 | 436 | 28.0077 | 34.9922 |
| validation | 2745 | 0 | 97 | 0 | 97 | 28.0234 | 34.9937 |


All measured A1 disagreements fall in the 28–35d observation gap. Endpoint conventions differ in source but create no additional A1 flag disagreements on these development rows. A2/A3/A4 discrepancies below are static findings, not full re-evaluations. This stage diagnoses the discrepancy; frozen targets and earlier metrics are preserved.

## 3. Growth distributions

Moments and quantiles exclude -1; missing rates use all rows. SD is population SD. Family and domain slices overlap. Normal slices require target0. No thresholds were selected.

### Train



| Slice | support | available_count | missing_count | missing_rate | mean | median | std | q05 | q25 | q75 | q95 | q99 | min | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | 11476 | 11040 | 436 | 0.0380 | 2.4006 | 2.0000 | 1.1968 | 1.5238 | 1.6957 | 2.6000 | 4.6683 | 7.4286 | 1.5000 | 14.0000 |
| A2 | 3770 | 3679 | 91 | 0.0241 | 1.4015 | 1.1538 | 0.8712 | 0.5833 | 0.8667 | 1.6800 | 3.0000 | 4.9412 | 0.2500 | 8.4000 |
| A3 | 1810 | 1777 | 33 | 0.0182 | 1.9599 | 1.5833 | 1.3923 | 0.7554 | 1.1034 | 2.2857 | 4.6762 | 7.4286 | 0.3448 | 13.0000 |
| A4 | 1353 | 1314 | 39 | 0.0288 | 1.4235 | 1.2444 | 0.7336 | 0.6877 | 0.9583 | 1.6364 | 2.7887 | 4.4387 | 0.4746 | 8.5714 |
| H1 | 840 | 375 | 465 | 0.5536 | 0.9374 | 0.9474 | 0.2686 | 0.5273 | 0.7170 | 1.1373 | 1.3939 | 1.4677 | 0.4000 | 1.4737 |
| H2 | 1380 | 697 | 683 | 0.4949 | 0.9461 | 0.9412 | 0.2832 | 0.4615 | 0.7500 | 1.1525 | 1.4286 | 1.4762 | 0.2353 | 1.6667 |
| H3 | 1643 | 790 | 853 | 0.5192 | 0.9320 | 0.9167 | 0.2899 | 0.4779 | 0.7325 | 1.1361 | 1.4023 | 1.4860 | 0.1000 | 2.0000 |
| H4 | 1237 | 626 | 611 | 0.4939 | 0.9953 | 0.9804 | 0.2629 | 0.5674 | 0.8000 | 1.2000 | 1.4286 | 1.4667 | 0.1667 | 1.4783 |
| H5 | 1054 | 557 | 497 | 0.4715 | 0.9751 | 0.9655 | 0.3391 | 0.5000 | 0.7347 | 1.2000 | 1.4672 | 2.0000 | 0.2051 | 2.6667 |
| H6 | 1639 | 774 | 865 | 0.5278 | 1.0149 | 1.0094 | 0.3046 | 0.4604 | 0.8125 | 1.2500 | 1.4516 | 1.4884 | 0.3243 | 2.5000 |
| H7 | 1475 | 663 | 812 | 0.5505 | 1.0371 | 1.0556 | 0.2623 | 0.5714 | 0.8571 | 1.2340 | 1.4488 | 1.4846 | 0.2778 | 1.6667 |
| H8 | 1677 | 743 | 934 | 0.5569 | 1.0457 | 1.0588 | 0.2569 | 0.5915 | 0.8615 | 1.2519 | 1.4286 | 1.4839 | 0.3636 | 1.4909 |
| agent_only | 12419 | 11944 | 475 | 0.0382 | 2.1364 | 1.8182 | 1.2297 | 0.8333 | 1.5294 | 2.4106 | 4.4000 | 7.0000 | 0.2500 | 14.0000 |
| campaign_member_target0 | 7429 | 3834 | 3595 | 0.4839 | 0.9836 | 1.0000 | 0.2953 | 0.5000 | 0.7650 | 1.2195 | 1.4286 | 1.4818 | 0.1143 | 2.6667 |
| multi_domain | 4034 | 3201 | 833 | 0.2065 | 1.6128 | 1.4000 | 0.9809 | 0.6364 | 0.9600 | 1.9355 | 3.4737 | 5.2000 | 0.2500 | 12.0000 |
| overall | 60000 | 36943 | 23057 | 0.3843 | 1.3970 | 1.1538 | 0.9587 | 0.5306 | 0.8485 | 1.6238 | 3.0000 | 5.3333 | 0.0606 | 14.0000 |
| routine | 21407 | 11311 | 10096 | 0.4716 | 0.9348 | 0.9302 | 0.3074 | 0.4407 | 0.7143 | 1.1579 | 1.4286 | 1.4883 | 0.0606 | 3.3333 |
| target0 | 39781 | 20370 | 19411 | 0.4879 | 0.9577 | 0.9565 | 0.3013 | 0.4615 | 0.7429 | 1.1837 | 1.4286 | 1.4857 | 0.0606 | 3.3333 |
| target1 | 20219 | 16573 | 3646 | 0.1803 | 1.9370 | 1.6957 | 1.1867 | 0.7170 | 1.2245 | 2.2500 | 4.0000 | 6.7500 | 0.1667 | 14.0000 |


### Validation



| Slice | support | available_count | missing_count | missing_rate | mean | median | std | q05 | q25 | q75 | q95 | q99 | min | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | 2745 | 2648 | 97 | 0.0353 | 2.2638 | 2.0000 | 1.0082 | 1.5238 | 1.7143 | 2.4444 | 4.0000 | 6.9329 | 1.5000 | 11.0000 |
| A2 | 930 | 904 | 26 | 0.0280 | 1.3228 | 1.0833 | 0.7854 | 0.5959 | 0.8093 | 1.5522 | 3.2000 | 4.3636 | 0.4000 | 5.0000 |
| A3 | 485 | 446 | 39 | 0.0804 | 1.9015 | 1.5610 | 1.3025 | 0.8571 | 1.2216 | 2.0542 | 3.9500 | 8.5167 | 0.6275 | 10.0000 |
| A4 | 337 | 332 | 5 | 0.0148 | 1.3401 | 1.1132 | 0.7437 | 0.6370 | 0.8882 | 1.5359 | 2.7267 | 4.2509 | 0.5581 | 5.0000 |
| H1 | 238 | 89 | 149 | 0.6261 | 0.9689 | 0.9778 | 0.2246 | 0.5789 | 0.8333 | 1.0909 | 1.4000 | 1.4043 | 0.5000 | 1.4359 |
| H2 | 374 | 170 | 204 | 0.5455 | 0.9846 | 0.9456 | 0.3430 | 0.5000 | 0.7611 | 1.1973 | 1.4469 | 2.1550 | 0.4000 | 2.5000 |
| H3 | 406 | 188 | 218 | 0.5369 | 1.0062 | 1.0000 | 0.2671 | 0.5186 | 0.8249 | 1.2000 | 1.4076 | 1.5805 | 0.3636 | 1.6667 |
| H4 | 292 | 181 | 111 | 0.3801 | 0.9787 | 1.0000 | 0.2817 | 0.5294 | 0.7619 | 1.1765 | 1.4375 | 1.5445 | 0.2222 | 1.5789 |
| H5 | 214 | 77 | 137 | 0.6402 | 0.9703 | 1.0196 | 0.2911 | 0.4987 | 0.7692 | 1.1667 | 1.4067 | 1.5303 | 0.4167 | 1.6667 |
| H6 | 424 | 205 | 219 | 0.5165 | 1.0200 | 1.0244 | 0.2538 | 0.5906 | 0.8333 | 1.2105 | 1.4239 | 1.4734 | 0.4000 | 1.7500 |
| H7 | 359 | 153 | 206 | 0.5738 | 1.0712 | 1.1250 | 0.2898 | 0.5455 | 0.8571 | 1.3191 | 1.4202 | 1.4840 | 0.4545 | 1.7500 |
| H8 | 460 | 217 | 243 | 0.5283 | 1.0772 | 1.0909 | 0.3268 | 0.5808 | 0.7907 | 1.3103 | 1.4870 | 2.0000 | 0.5098 | 2.0714 |
| agent_only | 3123 | 3014 | 109 | 0.0349 | 1.9915 | 1.7895 | 1.0562 | 0.7922 | 1.5204 | 2.2500 | 3.6923 | 6.3805 | 0.5238 | 11.0000 |
| campaign_member_target0 | 1796 | 956 | 840 | 0.4677 | 1.0361 | 1.0476 | 0.2956 | 0.5714 | 0.8173 | 1.2593 | 1.4586 | 1.7707 | 0.1905 | 2.0714 |
| multi_domain | 979 | 766 | 213 | 0.2176 | 1.5196 | 1.3793 | 0.7994 | 0.6102 | 0.9000 | 1.8849 | 3.2000 | 4.1818 | 0.3478 | 4.4000 |
| overall | 15000 | 9306 | 5694 | 0.3796 | 1.3533 | 1.1698 | 0.8288 | 0.5560 | 0.8571 | 1.6216 | 2.7500 | 4.2500 | 0.0833 | 11.0000 |
| routine | 5382 | 2956 | 2426 | 0.4508 | 0.9490 | 0.9400 | 0.3183 | 0.4507 | 0.7143 | 1.1915 | 1.4405 | 1.6667 | 0.0833 | 3.1429 |
| target0 | 9945 | 5192 | 4753 | 0.4779 | 0.9817 | 0.9831 | 0.3105 | 0.5000 | 0.7500 | 1.2222 | 1.4444 | 1.7089 | 0.0833 | 3.1429 |
| target1 | 5055 | 4114 | 941 | 0.1862 | 1.8221 | 1.6923 | 1.0189 | 0.6842 | 1.1865 | 2.1333 | 3.4377 | 5.3225 | 0.1905 | 11.0000 |


Observed A1 growth means are 2.4006 Train and 2.2638 Validation, with median 2 in both. Overall target0 means are .9577/.9817. Novelty shifts much more strongly (.8718→.6395, Stage 12/13), despite similar missing rates. Stable aggregate growth alone does not establish transportability.

## 4. A1 attribution and other agent families



| Partition | Reference TP | No-growth TP | Lost | Recovered | Net loss | Lost A1 | Recovered A1 | A1 fraction of lost | A1 net / all net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | 19235 | 15687 | 3928 | 380 | 3548 | 3880 | 16 | 0.9878 | 1.0891 |
| validation | 4726 | 3115 | 1666 | 55 | 1611 | 1634 | 2 | 0.9808 | 1.0130 |


Attribution uses individual prediction transitions. A1 net loss is 1,632 versus 1,611 overall, exceeding 100% because non-A1 gains offset some losses. This is a count decomposition, not a causal decomposition of Macro F1, and overlapping family losses must not be summed.



| Partition | Family | Support | Ref TP | Ref FN | Ref recall | No-growth TP | No-growth FN | No-growth recall | Recall change |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | A1 | 11476 | 11227 | 249 | 0.9783 | 7363 | 4113 | 0.6416 | -0.3367 |
| train | A2 | 3770 | 3393 | 377 | 0.9000 | 3543 | 227 | 0.9398 | 0.0398 |
| train | A3 | 1810 | 1810 | 0 | 1.0000 | 1810 | 0 | 1.0000 | 0.0000 |
| train | A4 | 1353 | 1100 | 253 | 0.8130 | 1188 | 165 | 0.8780 | 0.0650 |
| validation | A1 | 2745 | 2689 | 56 | 0.9796 | 1057 | 1688 | 0.3851 | -0.5945 |
| validation | A2 | 930 | 814 | 116 | 0.8753 | 800 | 130 | 0.8602 | -0.0151 |
| validation | A3 | 485 | 481 | 4 | 0.9918 | 485 | 0 | 1.0000 | 0.0082 |
| validation | A4 | 337 | 249 | 88 | 0.7389 | 234 | 103 | 0.6944 | -0.0445 |


A2 and A4 have modest removal losses, while A3 recall improves slightly. Growth is neither the direct A2/A3/A4 quantity nor a uniform requirement for detecting them. Their overlaps with A1 explain part of their association.



| Partition | Family excluding A1 | Support | Available | Growth mean | Median | P95 |
| --- | --- | --- | --- | --- | --- | --- |
| train | A2 | 2650 | 2578 | 0.9825 | 0.9787 | 1.4286 |
| train | A3 | 840 | 817 | 1.0665 | 1.0588 | 1.4483 |
| train | A4 | 928 | 905 | 1.0616 | 1.0877 | 1.4444 |
| validation | A2 | 711 | 685 | 0.9798 | 0.9286 | 1.4545 |
| validation | A3 | 241 | 228 | 1.2165 | 1.2340 | 1.6833 |
| validation | A4 | 251 | 248 | 1.0110 | 1.0000 | 1.4085 |


After excluding A1 overlap, Validation A2/A4 growth means fall to .9798/1.0110, close to the target0 mean .9817. A3 remains somewhat higher at 1.2165. These conditional distributions strengthen the interpretation that A1 overlap drives much of the other-family growth association.



| Partition | Family | A1 overlap | A2 overlap | A3 overlap | A4 overlap |
| --- | --- | --- | --- | --- | --- |
| train | A1 | 11476 | 1120 | 970 | 425 |
| train | A2 | 1120 | 3770 | 279 | 330 |
| train | A3 | 970 | 279 | 1810 | 100 |
| train | A4 | 425 | 330 | 100 | 1353 |
| validation | A1 | 2745 | 219 | 244 | 86 |
| validation | A2 | 219 | 930 | 64 | 69 |
| validation | A3 | 244 | 64 | 485 | 19 |
| validation | A4 | 86 | 69 | 19 | 337 |


### Growth in true positives and false negatives



| Partition | Family | Model/group | Support | Available | Missing rate | Mean | Median | P05 | P95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | A1 | no_growth_FN | 4113 | 3859 | 0.0618 | 2.1812 | 1.8621 | 1.5111 | 3.7778 |
| train | A1 | no_growth_TP | 7363 | 7181 | 0.0247 | 2.5186 | 2.0870 | 1.5333 | 5.0000 |
| train | A1 | reference_FN | 249 | 1 | 0.9960 | 1.6667 | 1.6667 | 1.6667 | 1.6667 |
| train | A1 | reference_TP | 11227 | 11039 | 0.0167 | 2.4007 | 2.0000 | 1.5238 | 4.6700 |
| train | A2 | no_growth_FN | 227 | 222 | 0.0220 | 1.1398 | 1.0328 | 0.4867 | 2.1358 |
| train | A2 | no_growth_TP | 3543 | 3457 | 0.0243 | 1.4183 | 1.1628 | 0.5902 | 3.0476 |
| train | A2 | reference_FN | 377 | 374 | 0.0080 | 0.9465 | 0.9200 | 0.5076 | 1.4076 |
| train | A2 | reference_TP | 3393 | 3305 | 0.0259 | 1.4530 | 1.2000 | 0.5950 | 3.0769 |
| train | A3 | no_growth_FN | 0 | 0 | not available | not available | not available | not available | not available |
| train | A3 | no_growth_TP | 1810 | 1777 | 0.0182 | 1.9599 | 1.5833 | 0.7554 | 4.6762 |
| train | A3 | reference_FN | 0 | 0 | not available | not available | not available | not available | not available |
| train | A3 | reference_TP | 1810 | 1777 | 0.0182 | 1.9599 | 1.5833 | 0.7554 | 4.6762 |
| train | A4 | no_growth_FN | 165 | 156 | 0.0545 | 1.1897 | 1.1091 | 0.6522 | 1.9028 |
| train | A4 | no_growth_TP | 1188 | 1158 | 0.0253 | 1.4550 | 1.2609 | 0.6972 | 2.8571 |
| train | A4 | reference_FN | 253 | 251 | 0.0079 | 1.0591 | 1.0732 | 0.6402 | 1.4643 |
| train | A4 | reference_TP | 1100 | 1063 | 0.0336 | 1.5095 | 1.3125 | 0.7202 | 2.9091 |
| validation | A1 | no_growth_FN | 1688 | 1633 | 0.0326 | 2.1498 | 1.9024 | 1.5135 | 3.4594 |
| validation | A1 | no_growth_TP | 1057 | 1015 | 0.0397 | 2.4471 | 2.1250 | 1.5385 | 4.3636 |
| validation | A1 | reference_FN | 56 | 0 | 1.0000 | not available | not available | not available | not available |
| validation | A1 | reference_TP | 2689 | 2648 | 0.0152 | 2.2638 | 2.0000 | 1.5238 | 4.0000 |
| validation | A2 | no_growth_FN | 130 | 127 | 0.0231 | 1.1854 | 1.0213 | 0.6287 | 2.3292 |
| validation | A2 | no_growth_TP | 800 | 777 | 0.0288 | 1.3453 | 1.0909 | 0.5942 | 3.2100 |
| validation | A2 | reference_FN | 116 | 113 | 0.0259 | 0.9149 | 0.9167 | 0.5600 | 1.2792 |
| validation | A2 | reference_TP | 814 | 791 | 0.0283 | 1.3811 | 1.1351 | 0.5985 | 3.2500 |
| validation | A3 | no_growth_FN | 0 | 0 | not available | not available | not available | not available | not available |
| validation | A3 | no_growth_TP | 485 | 446 | 0.0804 | 1.9015 | 1.5610 | 0.8571 | 3.9500 |
| validation | A3 | reference_FN | 4 | 4 | 0.0000 | 1.2591 | 1.2727 | 1.1182 | 1.3809 |
| validation | A3 | reference_TP | 481 | 442 | 0.0811 | 1.9074 | 1.5639 | 0.8571 | 3.9900 |
| validation | A4 | no_growth_FN | 103 | 102 | 0.0097 | 1.2004 | 1.1200 | 0.6842 | 1.9047 |
| validation | A4 | no_growth_TP | 234 | 230 | 0.0171 | 1.4020 | 1.1111 | 0.6206 | 3.6058 |
| validation | A4 | reference_FN | 88 | 87 | 0.0114 | 1.0434 | 1.0526 | 0.6562 | 1.4118 |
| validation | A4 | reference_TP | 249 | 245 | 0.0161 | 1.4454 | 1.2222 | 0.6278 | 3.4667 |


### A1 onset and origin

Offsets apply only where the private scenario family itself is A1 and its own onset is recorded. They count episode positions, not elapsed days. The fixed groups are onset, 1–3 later positions and 4+ later positions. Most A1-positive rows have no applicable own-A1 onset, so these slices cannot explain the whole population.



| Partition | Own-onset group | N | Available | Growth mean | Median | Reference recall | One-feature recall |
| --- | --- | --- | --- | --- | --- | --- | --- |
| train | after_1_to_3 | 109 | 107 | 2.0452 | 1.7500 | 1.0000 | 0.9817 |
| train | after_4_plus | 352 | 352 | 2.6699 | 2.4444 | 1.0000 | 1.0000 |
| train | not_recorded | 10974 | 10541 | 2.3974 | 2.0000 | 0.9773 | 0.9605 |
| train | onset_0 | 41 | 40 | 1.8319 | 1.6000 | 1.0000 | 0.9756 |
| validation | after_1_to_3 | 49 | 47 | 2.1721 | 1.9444 | 0.9592 | 0.9592 |
| validation | after_4_plus | 133 | 124 | 2.3592 | 2.1250 | 0.9323 | 0.9323 |
| validation | not_recorded | 2546 | 2461 | 2.2633 | 2.0000 | 0.9827 | 0.9666 |
| validation | onset_0 | 17 | 16 | 1.8578 | 1.8284 | 0.9412 | 0.9412 |


In Validation, observed mean growth rises 1.8578 at onset to 2.3592 at 4+ positions, consistent with accumulating customers. Classification recall does not rise monotonically because missing eligibility and composition differ. There are only 17 onset rows; no stable late-versus-early causal conclusion follows.



| Partition | A1 origin | Support |
| --- | --- | --- |
| train | campaign_member | 3610 |
| train | hard_scenario | 3953 |
| train | routine | 3913 |
| validation | campaign_member | 853 |
| validation | hard_scenario | 957 |
| validation | routine | 935 |


A1 is widespread outside private A1 campaigns: 935 Validation A1 positives originate in routine events and 957 in hard scenarios. An episode-only explanation is insufficient.

## 5. Negative overlap and target conditioning

For each family, compare observed growth against target0 H7, H8 and routine rows. Rank AUC is P(positive growth > negative growth), with half credit for ties. Middle-90% overlap uses the other group’s P05–P95 interval. The 1.5 diagnostic is the existing A1 predicate constant, never an optimized operating threshold.



| Partition | Family | Negative | Positive available | Negative available | Positive mean | Negative mean | Rank AUC | Positive in negative middle90 | Negative in positive middle90 | Negative >=1.5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | A1 | H7 | 11040 | 663 | 2.4006 | 1.0371 | 0.9997 | 0.0000 | 0.0015 | 0.0015 |
| train | A1 | H8 | 11040 | 743 | 2.4006 | 1.0457 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| train | A1 | routine | 11040 | 11311 | 2.4006 | 0.9348 | 0.9976 | 0.0000 | 0.0077 | 0.0082 |
| train | A2 | H7 | 3679 | 663 | 1.4015 | 1.0371 | 0.6070 | 0.6322 | 0.9427 | 0.0015 |
| train | A2 | H8 | 3679 | 743 | 1.4015 | 1.0457 | 0.6013 | 0.6146 | 0.9556 | 0.0000 |
| train | A2 | routine | 3679 | 11311 | 1.4015 | 0.9348 | 0.6812 | 0.6586 | 0.8692 | 0.0082 |
| train | A3 | H7 | 1777 | 663 | 1.9599 | 1.0371 | 0.7818 | 0.4350 | 0.8567 | 0.0015 |
| train | A3 | H8 | 1777 | 743 | 1.9599 | 1.0457 | 0.7778 | 0.4181 | 0.8546 | 0.0000 |
| train | A3 | routine | 1777 | 11311 | 1.9599 | 0.9348 | 0.8278 | 0.4249 | 0.7023 | 0.0082 |
| train | A4 | H7 | 1314 | 663 | 1.4235 | 1.0371 | 0.6718 | 0.6400 | 0.9005 | 0.0015 |
| train | A4 | H8 | 1314 | 743 | 1.4235 | 1.0457 | 0.6656 | 0.6248 | 0.8991 | 0.0000 |
| train | A4 | routine | 1314 | 11311 | 1.4235 | 0.9348 | 0.7402 | 0.6438 | 0.7737 | 0.0082 |
| validation | A1 | H7 | 2648 | 153 | 2.2638 | 1.0712 | 0.9980 | 0.0000 | 0.0065 | 0.0065 |
| validation | A1 | H8 | 2648 | 217 | 2.2638 | 1.0772 | 0.9811 | 0.0000 | 0.0461 | 0.0507 |
| validation | A1 | routine | 2648 | 2956 | 2.2638 | 0.9490 | 0.9946 | 0.0000 | 0.0193 | 0.0206 |
| validation | A2 | H7 | 904 | 153 | 1.3228 | 1.0712 | 0.5400 | 0.6969 | 0.9150 | 0.0065 |
| validation | A2 | H8 | 904 | 217 | 1.3228 | 1.0772 | 0.5475 | 0.6936 | 0.9401 | 0.0507 |
| validation | A2 | routine | 904 | 2956 | 1.3228 | 0.9490 | 0.6333 | 0.7024 | 0.8623 | 0.0206 |
| validation | A3 | H7 | 446 | 153 | 1.9015 | 1.0712 | 0.8064 | 0.3857 | 0.7516 | 0.0065 |
| validation | A3 | H8 | 446 | 217 | 1.9015 | 1.0772 | 0.8042 | 0.4484 | 0.7143 | 0.0507 |
| validation | A3 | routine | 446 | 2956 | 1.9015 | 0.9490 | 0.8621 | 0.4036 | 0.5974 | 0.0206 |
| validation | A4 | H7 | 332 | 153 | 1.3401 | 1.0712 | 0.5705 | 0.7229 | 0.8824 | 0.0065 |
| validation | A4 | H8 | 332 | 217 | 1.3401 | 1.0772 | 0.5806 | 0.7289 | 0.9078 | 0.0507 |
| validation | A4 | routine | 332 | 2956 | 1.3401 | 0.9490 | 0.6697 | 0.7289 | 0.8217 | 0.0206 |


No eligible Validation A1 positive lies in the middle 90% of H7, H8 or routine negatives. Only 1/153 eligible H7 negatives, 11/217 H8 negatives and 61/2,956 routine negatives have growth ≥1.5. A2/A3/A4 overlap is materially greater. This is a strong A1 separability finding; real-world adequacy cannot be established without external agent behaviour evidence.

### All-origin cohorts, including target1



| Partition | Origin/category | All N | Target1 | A1 positive | Available growth>=1.5 | High growth A1 | High growth target0 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| train | H7 | 2400 | 925 | 743 | 722 | 721 | 1 |
| train | H8 | 2400 | 723 | 609 | 583 | 583 | 0 |
| train | campaign_member | 14400 | 6971 | 3610 | 3565 | 3545 | 17 |
| train | hard_scenario | 19200 | 8255 | 3953 | 3838 | 3807 | 25 |
| train | routine | 26400 | 4993 | 3913 | 3781 | 3688 | 93 |
| validation | H7 | 600 | 241 | 173 | 175 | 173 | 1 |
| validation | H8 | 600 | 140 | 111 | 118 | 106 | 11 |
| validation | campaign_member | 3600 | 1804 | 853 | 883 | 808 | 31 |
| validation | hard_scenario | 4800 | 2033 | 957 | 981 | 947 | 25 |
| validation | routine | 6600 | 1218 | 935 | 961 | 893 | 61 |


Hard-scenario and routine origins do contain growth. However, the target is the union of observable predicates: a legitimate-like origin satisfying A1 is target1. Restricting to target0 therefore removes those high-growth cases by definition. This conditioning is central to the separation. It would be incorrect to call their correct target1 predictions false positives or to claim the generator simply never produces normal-origin growth. A future design must clarify whether the task is reproducing this behavioural review rule or distinguishing additional legitimate context; adding more events under the same full predicate cannot create counterexamples labeled target0.

## 6. Growth-alone predictive power

Raw metrics use increasing growth without sign selection. “Encoded” includes -1, “available” excludes it, and “agent_present” excludes direct events but retains insufficient-history agents. Relevant negatives are the union of H7/H8/routine target0. Positives are the named family or agent-only union. Other positives are excluded from those comparisons. AP depends on each subset prevalence.

The saved Stage 12 `top_1` HGB is the Train-fitted one-feature diagnostic classifier. It was fitted on the overall Train target, and is reused without refitting for each subset at .50. It is not a separately trained family-specific classifier; family subset scores are diagnostic reviews among family-positive versus normal rows.



| Partition | Task | View | N | Positive | Prevalence | Raw AUC | Raw AP | Classifier AUC | Classifier AP | Classifier Macro F1 | Recall | FPR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | A1_vs_relevant_negatives | agent_present | 28463 | 11476 | 0.4032 | 0.9652 | 0.9739 | 0.9694 | 0.9774 | 0.9801 | 0.9620 | 0.0063 |
| train | A1_vs_relevant_negatives | available | 23757 | 11040 | 0.4647 | 0.9978 | 0.9964 | 0.9995 | 0.9993 | 0.9955 | 1.0000 | 0.0084 |
| train | A1_vs_relevant_negatives | encoded | 36035 | 11476 | 0.3185 | 0.9701 | 0.9707 | 0.9730 | 0.9739 | 0.9825 | 0.9620 | 0.0044 |
| train | A2_vs_relevant_negatives | agent_present | 20757 | 3770 | 0.1816 | 0.7398 | 0.5214 | 0.7594 | 0.5546 | 0.6840 | 0.2934 | 0.0063 |
| train | A2_vs_relevant_negatives | available | 16396 | 3679 | 0.2244 | 0.6727 | 0.5298 | 0.7062 | 0.5649 | 0.6781 | 0.3006 | 0.0084 |
| train | A2_vs_relevant_negatives | encoded | 28329 | 3770 | 0.1331 | 0.8163 | 0.5203 | 0.8217 | 0.5520 | 0.6951 | 0.2934 | 0.0044 |
| train | A4_vs_relevant_negatives | agent_present | 18340 | 1353 | 0.0738 | 0.7801 | 0.4151 | 0.7880 | 0.4441 | 0.7050 | 0.3045 | 0.0063 |
| train | A4_vs_relevant_negatives | available | 14031 | 1314 | 0.0936 | 0.7323 | 0.4252 | 0.7431 | 0.4552 | 0.7055 | 0.3135 | 0.0084 |
| train | A4_vs_relevant_negatives | encoded | 25912 | 1353 | 0.0522 | 0.8435 | 0.4145 | 0.8462 | 0.4432 | 0.7096 | 0.3045 | 0.0044 |
| train | agent_only_vs_relevant_negatives | agent_present | 29406 | 12419 | 0.4223 | 0.9060 | 0.9182 | 0.9099 | 0.9217 | 0.8930 | 0.7708 | 0.0063 |
| train | agent_only_vs_relevant_negatives | available | 24661 | 11944 | 0.4843 | 0.9159 | 0.9379 | 0.9191 | 0.9412 | 0.8980 | 0.8015 | 0.0084 |
| train | agent_only_vs_relevant_negatives | encoded | 36978 | 12419 | 0.3358 | 0.9291 | 0.9149 | 0.9301 | 0.9176 | 0.9047 | 0.7708 | 0.0044 |
| train | overall | agent_present | 45960 | 17510 | 0.3810 | 0.8518 | 0.8507 | 0.8596 | 0.8592 | 0.8326 | 0.6316 | 0.0057 |
| train | overall | available | 36943 | 16573 | 0.4486 | 0.8491 | 0.8772 | 0.8604 | 0.8864 | 0.8363 | 0.6673 | 0.0080 |
| train | overall | encoded | 60000 | 20219 | 0.3370 | 0.8003 | 0.7798 | 0.8084 | 0.7876 | 0.7991 | 0.5470 | 0.0041 |
| validation | A1_vs_relevant_negatives | agent_present | 7072 | 2745 | 0.3882 | 0.9642 | 0.9685 | 0.9663 | 0.9670 | 0.9744 | 0.9647 | 0.0173 |
| validation | A1_vs_relevant_negatives | available | 5974 | 2648 | 0.4433 | 0.9939 | 0.9898 | 0.9932 | 0.9875 | 0.9873 | 1.0000 | 0.0225 |
| validation | A1_vs_relevant_negatives | encoded | 8946 | 2745 | 0.3068 | 0.9697 | 0.9657 | 0.9712 | 0.9639 | 0.9774 | 0.9647 | 0.0121 |
| validation | A2_vs_relevant_negatives | agent_present | 5257 | 930 | 0.1769 | 0.6939 | 0.4447 | 0.7036 | 0.4533 | 0.6550 | 0.2634 | 0.0173 |
| validation | A2_vs_relevant_negatives | available | 4230 | 904 | 0.2137 | 0.6234 | 0.4524 | 0.6470 | 0.4629 | 0.6494 | 0.2710 | 0.0225 |
| validation | A2_vs_relevant_negatives | encoded | 7131 | 930 | 0.1304 | 0.7822 | 0.4434 | 0.7760 | 0.4498 | 0.6668 | 0.2634 | 0.0121 |
| validation | A4_vs_relevant_negatives | agent_present | 4664 | 337 | 0.0723 | 0.7289 | 0.3149 | 0.7218 | 0.3053 | 0.6542 | 0.2552 | 0.0173 |
| validation | A4_vs_relevant_negatives | available | 3658 | 332 | 0.0908 | 0.6593 | 0.3186 | 0.6540 | 0.3091 | 0.6509 | 0.2590 | 0.0225 |
| validation | A4_vs_relevant_negatives | encoded | 6538 | 337 | 0.0515 | 0.8086 | 0.3146 | 0.7983 | 0.3045 | 0.6597 | 0.2552 | 0.0121 |
| validation | agent_only_vs_relevant_negatives | agent_present | 7450 | 3123 | 0.4192 | 0.8939 | 0.9028 | 0.8968 | 0.9028 | 0.8813 | 0.7589 | 0.0173 |
| validation | agent_only_vs_relevant_negatives | available | 6340 | 3014 | 0.4754 | 0.8986 | 0.9203 | 0.9010 | 0.9201 | 0.8844 | 0.7863 | 0.0225 |
| validation | agent_only_vs_relevant_negatives | encoded | 9324 | 3123 | 0.3349 | 0.9207 | 0.8999 | 0.9208 | 0.8991 | 0.8940 | 0.7589 | 0.0121 |
| validation | overall | agent_present | 11490 | 4355 | 0.3790 | 0.8355 | 0.8308 | 0.8343 | 0.8283 | 0.8212 | 0.6220 | 0.0168 |
| validation | overall | available | 9306 | 4114 | 0.4421 | 0.8302 | 0.8572 | 0.8312 | 0.8554 | 0.8248 | 0.6585 | 0.0231 |
| validation | overall | encoded | 15000 | 5055 | 0.3370 | 0.7862 | 0.7604 | 0.7867 | 0.7582 | 0.7879 | 0.5359 | 0.0121 |


Growth alone has substantial overall power but is far below the reference (Validation Macro F1 .7879 versus .9521). Its near-perfect eligible A1 ranking contrasts with A2 AUC .6234 and A4 .6593 against the same eligible negatives. It is specifically informative for A1, not a universal agent oracle.

## 7. Every existing agent feature

Correlations use pairwise observed values; -1/-3 markers are excluded only where documented. A raw AUC near .5 for signed cash skew does not imply uselessness: both signs can matter through magnitude and interactions. No sign flipping or feature selection was performed.



| Partition | Feature | Encoded AUC | Encoded AP | Observed AUC | Observed AP | Pair N | Pearson with growth | Spearman with growth | Reference AP drop |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | agent_cash_count_skew_24h | 0.4916 | 0.3249 | 0.4916 | 0.3249 | 36943 | 0.0097 | 0.0206 | 0.0123 |
| train | agent_cash_value_skew_24h | 0.4872 | 0.3230 | 0.4872 | 0.3230 | 36943 | 0.0072 | 0.0165 | 0.0040 |
| train | agent_cash_value_skew_change | 0.6507 | 0.4222 | 0.4897 | 0.4385 | 36713 | -0.0002 | 0.0143 | 0.0048 |
| train | agent_new_wallet_share_7d | 0.6832 | 0.4557 | 0.5701 | 0.4818 | 36943 | 0.2185 | 0.1872 | 0.0047 |
| train | agent_service_acceleration_1h | 0.7139 | 0.5534 | 0.6253 | 0.5925 | 36803 | 0.1509 | 0.1091 | 0.0320 |
| train | agent_service_count_1h_inclusive | 0.6436 | 0.4804 | 0.6436 | 0.4804 | 36943 | 0.1746 | 0.1127 | 0.0015 |
| train | agent_top2_count_share_24h | 0.5309 | 0.3292 | 0.5309 | 0.3292 | 36943 | -0.2083 | -0.2730 | 0.0162 |
| train | agent_top2_share_change_24h | 0.6181 | 0.3799 | 0.4193 | 0.3895 | 35791 | -0.2262 | -0.2951 | 0.0045 |
| train | agent_wallet_growth_ratio_7d | 0.8003 | 0.7798 | 0.8491 | 0.8772 | 36943 | 1.0000 | 1.0000 | 0.3346 |
| validation | agent_cash_count_skew_24h | 0.4963 | 0.3241 | 0.4963 | 0.3241 | 9306 | 0.0023 | 0.0121 | 0.0123 |
| validation | agent_cash_value_skew_24h | 0.5040 | 0.3269 | 0.5040 | 0.3269 | 9306 | 0.0079 | 0.0287 | 0.0040 |
| validation | agent_cash_value_skew_change | 0.6515 | 0.4232 | 0.5124 | 0.4411 | 9239 | -0.0072 | 0.0167 | 0.0048 |
| validation | agent_new_wallet_share_7d | 0.6974 | 0.4801 | 0.6212 | 0.5128 | 9306 | 0.3375 | 0.3378 | 0.0047 |
| validation | agent_service_acceleration_1h | 0.7138 | 0.5605 | 0.6390 | 0.6022 | 9296 | 0.1370 | 0.1293 | 0.0320 |
| validation | agent_service_count_1h_inclusive | 0.6494 | 0.4965 | 0.6494 | 0.4965 | 9306 | 0.1371 | 0.1294 | 0.0015 |
| validation | agent_top2_count_share_24h | 0.5122 | 0.3188 | 0.5122 | 0.3188 | 9306 | -0.1871 | -0.2923 | 0.0162 |
| validation | agent_top2_share_change_24h | 0.6011 | 0.3703 | 0.4033 | 0.3782 | 9010 | -0.2251 | -0.3281 | 0.0045 |
| validation | agent_wallet_growth_ratio_7d | 0.7862 | 0.7604 | 0.8302 | 0.8572 | 9306 | 1.0000 | 1.0000 | 0.3346 |




| Partition | Feature | Class | N | Available | Missing rate | Mean | Median | SD | P05 | P95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | agent_cash_count_skew_24h | target0 | 39781 | 39781 | 0.0000 | -0.0215 | 0.0000 | 0.5745 | -1.0000 | 1.0000 |
| train | agent_cash_count_skew_24h | target1 | 20219 | 20219 | 0.0000 | -0.0410 | 0.0000 | 0.5762 | -1.0000 | 1.0000 |
| train | agent_cash_value_skew_24h | target0 | 39781 | 39781 | 0.0000 | -0.0269 | 0.0000 | 0.7018 | -1.0000 | 1.0000 |
| train | agent_cash_value_skew_24h | target1 | 20219 | 20219 | 0.0000 | -0.0585 | 0.0000 | 0.7430 | -1.0000 | 1.0000 |
| train | agent_cash_value_skew_change | target0 | 39781 | 21033 | 0.4713 | 0.0047 | -0.0303 | 0.8923 | -1.2654 | 1.3230 |
| train | agent_cash_value_skew_change | target1 | 20219 | 16969 | 0.1607 | -0.0301 | -0.0804 | 0.8776 | -1.2772 | 1.3310 |
| train | agent_new_wallet_share_7d | target0 | 39781 | 20370 | 0.4879 | 0.8608 | 0.8571 | 0.1045 | 0.6800 | 1.0000 |
| train | agent_new_wallet_share_7d | target1 | 20219 | 16573 | 0.1803 | 0.8852 | 0.8929 | 0.0914 | 0.7177 | 1.0000 |
| train | agent_service_acceleration_1h | target0 | 39781 | 21179 | 0.4676 | 1.2884 | 1.0000 | 0.7654 | 1.0000 | 3.0000 |
| train | agent_service_acceleration_1h | target1 | 20219 | 17128 | 0.1529 | 2.5042 | 1.0000 | 2.9549 | 1.0000 | 9.0000 |
| train | agent_service_count_1h_inclusive | target0 | 39781 | 39781 | 0.0000 | 1.0268 | 1.0000 | 1.3327 | 0.0000 | 3.0000 |
| train | agent_service_count_1h_inclusive | target1 | 20219 | 20219 | 0.0000 | 2.1867 | 1.0000 | 2.9271 | 0.0000 | 8.0000 |
| train | agent_top2_count_share_24h | target0 | 39781 | 39781 | 0.0000 | 0.4840 | 0.5000 | 0.3833 | 0.0000 | 1.0000 |
| train | agent_top2_count_share_24h | target1 | 20219 | 20219 | 0.0000 | 0.5242 | 0.5294 | 0.3255 | 0.0000 | 1.0000 |
| train | agent_top2_share_change_24h | target0 | 39781 | 20447 | 0.4860 | 0.4849 | 0.4710 | 0.2561 | 0.0913 | 0.8769 |
| train | agent_top2_share_change_24h | target1 | 20219 | 16539 | 0.1820 | 0.4023 | 0.4127 | 0.2704 | -0.0312 | 0.8378 |
| train | agent_wallet_growth_ratio_7d | target0 | 39781 | 20370 | 0.4879 | 0.9577 | 0.9565 | 0.3013 | 0.4615 | 1.4286 |
| train | agent_wallet_growth_ratio_7d | target1 | 20219 | 16573 | 0.1803 | 1.9370 | 1.6957 | 1.1867 | 0.7170 | 4.0000 |
| validation | agent_cash_count_skew_24h | target0 | 9945 | 9945 | 0.0000 | -0.0312 | 0.0000 | 0.5816 | -1.0000 | 1.0000 |
| validation | agent_cash_count_skew_24h | target1 | 5055 | 5055 | 0.0000 | -0.0397 | 0.0000 | 0.5613 | -1.0000 | 1.0000 |
| validation | agent_cash_value_skew_24h | target0 | 9945 | 9945 | 0.0000 | -0.0238 | 0.0000 | 0.7057 | -1.0000 | 1.0000 |
| validation | agent_cash_value_skew_24h | target1 | 5055 | 5055 | 0.0000 | -0.0103 | 0.0000 | 0.7212 | -1.0000 | 1.0000 |
| validation | agent_cash_value_skew_change | target0 | 9945 | 5335 | 0.4635 | -0.0542 | -0.0567 | 0.8971 | -1.3105 | 1.2532 |
| validation | agent_cash_value_skew_change | target1 | 5055 | 4187 | 0.1717 | -0.0221 | -0.0193 | 0.8437 | -1.2848 | 1.2484 |
| validation | agent_new_wallet_share_7d | target0 | 9945 | 5192 | 0.4779 | 0.6067 | 0.5909 | 0.1955 | 0.3158 | 1.0000 |
| validation | agent_new_wallet_share_7d | target1 | 5055 | 4114 | 0.1862 | 0.6809 | 0.6842 | 0.1788 | 0.3571 | 1.0000 |
| validation | agent_service_acceleration_1h | target0 | 9945 | 5390 | 0.4580 | 1.2686 | 1.0000 | 0.6246 | 1.0000 | 3.0000 |
| validation | agent_service_acceleration_1h | target1 | 5055 | 4260 | 0.1573 | 2.5246 | 1.0000 | 2.8192 | 1.0000 | 9.0000 |
| validation | agent_service_count_1h_inclusive | target0 | 9945 | 9945 | 0.0000 | 0.9875 | 1.0000 | 1.0624 | 0.0000 | 3.0000 |
| validation | agent_service_count_1h_inclusive | target1 | 5055 | 5055 | 0.0000 | 2.1689 | 1.0000 | 2.7470 | 0.0000 | 8.0000 |
| validation | agent_top2_count_share_24h | target0 | 9945 | 9945 | 0.0000 | 0.4975 | 0.5000 | 0.3838 | 0.0000 | 1.0000 |
| validation | agent_top2_count_share_24h | target1 | 5055 | 5055 | 0.0000 | 0.5164 | 0.5000 | 0.3241 | 0.0000 | 1.0000 |
| validation | agent_top2_share_change_24h | target0 | 9945 | 5205 | 0.4766 | 0.4779 | 0.4575 | 0.2482 | 0.0968 | 0.8629 |
| validation | agent_top2_share_change_24h | target1 | 5055 | 4081 | 0.1927 | 0.3816 | 0.3857 | 0.2763 | -0.0380 | 0.8333 |
| validation | agent_wallet_growth_ratio_7d | target0 | 9945 | 5192 | 0.4779 | 0.9817 | 0.9831 | 0.3105 | 0.5000 | 1.4444 |
| validation | agent_wallet_growth_ratio_7d | target1 | 5055 | 4114 | 0.1862 | 1.8221 | 1.6923 | 1.0189 | 0.6842 | 3.4377 |


Growth has the strongest monotone observed-value discrimination among these nine quantities. Its observed correlations with novelty (.338 Spearman), service acceleration (.129), and top-two change (−.328) in Validation are modest. These are complementary summaries, with no close linear/rank replacement for the growth ratio. This does not prove information-theoretic uniqueness or rule out nonlinear substitutes.

## 8. Interactions using fixed Train bins

Each panel uses observed Train quartiles for growth and the other feature; duplicate edges collapse. Bin −1 denotes only the documented missing marker. Nonnegative bins are successive intervals, with values equal to an edge assigned to the upper bin. Each cell is **N / target1 fraction / mean reference score**. Empty cells remain explicit. These conditional summaries describe associations, not isolated interaction effects; joint support and reused Validation limit inference. Full Train and Validation counts are in JSON.

### Growth × `agent_cash_count_skew_24h`

Train growth edges: [0.8484848484848485, 1.1538461538461537, 1.6238207547169812]; other edges: [-0.3333333333333333, 0.0, 0.2].



| Growth bin | Other 0 | Other 1 | Other 2 | Other 3 |
| --- | --- | --- | --- | --- |
| -1 | 620 / 0.0919 / 0.1144 | 253 / 0.1107 / 0.1291 | 4023 / 0.1872 / 0.1925 | 798 / 0.1291 / 0.1411 |
| 0 | 761 / 0.2129 / 0.2155 | 220 / 0.2818 / 0.3184 | 525 / 0.1219 / 0.1439 | 784 / 0.2028 / 0.2147 |
| 1 | 687 / 0.2387 / 0.2440 | 321 / 0.2648 / 0.2739 | 495 / 0.2000 / 0.2267 | 746 / 0.2560 / 0.2846 |
| 2 | 660 / 0.3636 / 0.3938 | 327 / 0.3853 / 0.4158 | 535 / 0.3664 / 0.3803 | 922 / 0.3514 / 0.3858 |
| 3 | 667 / 0.9610 / 0.9919 | 422 / 0.9621 / 0.9972 | 484 / 0.9566 / 0.9887 | 750 / 0.9760 / 0.9910 |


### Growth × `agent_cash_value_skew_24h`

Train growth edges: [0.8484848484848485, 1.1538461538461537, 1.6238207547169812]; other edges: [-0.8515955026789485, 0.0, 0.6277177614931346].



| Growth bin | Other 0 | Other 1 | Other 2 | Other 3 |
| --- | --- | --- | --- | --- |
| -1 | 697 / 0.0904 / 0.1166 | 311 / 0.1093 / 0.1086 | 3952 / 0.1943 / 0.1986 | 734 / 0.1035 / 0.1236 |
| 0 | 818 / 0.1528 / 0.1770 | 307 / 0.3322 / 0.3194 | 387 / 0.1860 / 0.2154 | 778 / 0.1902 / 0.1949 |
| 1 | 764 / 0.2016 / 0.2116 | 363 / 0.2700 / 0.2917 | 397 / 0.3325 / 0.3539 | 725 / 0.2138 / 0.2372 |
| 2 | 685 / 0.3343 / 0.3745 | 397 / 0.4131 / 0.4383 | 499 / 0.4309 / 0.4454 | 863 / 0.3221 / 0.3502 |
| 3 | 637 / 0.9576 / 0.9908 | 568 / 0.9736 / 0.9968 | 407 / 0.9656 / 0.9893 | 711 / 0.9648 / 0.9904 |


### Growth × `agent_cash_value_skew_change`

Train growth edges: [0.8484848484848485, 1.1538461538461537, 1.6238207547169812]; other edges: [-0.8038074566075203, -0.05330640761686421, 0.8184013669121508].



| Growth bin | Other -1 | Other 0 | Other 1 | Other 2 | Other 3 |
| --- | --- | --- | --- | --- | --- |
| -1 | 5411 / 0.1539 / 0.1613 | 65 / 0.1846 / 0.3833 | 62 / 0.4355 / 0.3624 | 92 / 0.4783 / 0.4473 | 64 / 0.3906 / 0.4587 |
| 0 | 9 / 0.0000 / 0.0096 | 687 / 0.1543 / 0.1817 | 493 / 0.2454 / 0.2461 | 481 / 0.1954 / 0.2206 | 620 / 0.2032 / 0.2026 |
| 1 | 12 / 0.0000 / 0.0280 | 605 / 0.1521 / 0.1730 | 558 / 0.3011 / 0.3139 | 556 / 0.2842 / 0.2988 | 518 / 0.2336 / 0.2583 |
| 2 | 13 / 0.2308 / 0.1655 | 529 / 0.3233 / 0.3592 | 551 / 0.3993 / 0.4294 | 753 / 0.3984 / 0.4198 | 598 / 0.3211 / 0.3513 |
| 3 | 33 / 0.9697 / 0.9272 | 536 / 0.9459 / 0.9926 | 646 / 0.9814 / 0.9935 | 612 / 0.9706 / 0.9926 | 496 / 0.9577 / 0.9924 |


### Growth × `agent_history_coverage_days`

Train growth edges: [0.8484848484848485, 1.1538461538461537, 1.6238207547169812]; other edges: [3.8909215700578708, 28.0].



| Growth bin | Other 0 | Other 1 | Other 2 |
| --- | --- | --- | --- |
| -1 | 3776 / 0.1854 / 0.1907 | 1556 / 0.0585 / 0.0675 | 362 / 0.4144 / 0.4571 |
| 0 | 0 / not available / not available | 0 / not available / not available | 2290 / 0.1952 / 0.2087 |
| 1 | 0 / not available / not available | 0 / not available / not available | 2249 / 0.2397 / 0.2579 |
| 2 | 0 / not available / not available | 0 / not available / not available | 2444 / 0.3625 / 0.3908 |
| 3 | 0 / not available / not available | 0 / not available / not available | 2323 / 0.9651 / 0.9919 |


### Growth × `agent_new_wallet_share_7d`

Train growth edges: [0.8484848484848485, 1.1538461538461537, 1.6238207547169812]; other edges: [0.8076923076923077, 0.875, 0.95].



| Growth bin | Other -1 | Other 0 | Other 1 | Other 2 | Other 3 |
| --- | --- | --- | --- | --- | --- |
| -1 | 5694 / 0.1653 / 0.1740 | 0 / not available / not available | 0 / not available / not available | 0 / not available / not available | 0 / not available / not available |
| 0 | 0 / not available / not available | 1917 / 0.2102 / 0.2263 | 77 / 0.1299 / 0.1609 | 36 / 0.1389 / 0.1679 | 260 / 0.1115 / 0.0991 |
| 1 | 0 / not available / not available | 1923 / 0.2559 / 0.2736 | 119 / 0.1849 / 0.2000 | 84 / 0.0952 / 0.1441 | 123 / 0.1382 / 0.1465 |
| 2 | 0 / not available / not available | 2088 / 0.3554 / 0.3867 | 141 / 0.4326 / 0.4494 | 123 / 0.3984 / 0.4217 | 92 / 0.3696 / 0.3505 |
| 3 | 0 / not available / not available | 1421 / 0.9521 / 0.9924 | 380 / 1.0000 / 0.9966 | 344 / 1.0000 / 0.9983 | 178 / 0.9270 / 0.9659 |


### Growth × `agent_service_acceleration_1h`

Train growth edges: [0.8484848484848485, 1.1538461538461537, 1.6238207547169812]; other edges: [1.0, 2.0].



| Growth bin | Other -1 | Other 1 | Other 2 |
| --- | --- | --- | --- |
| -1 | 5340 / 0.1489 / 0.1546 | 252 / 0.3254 / 0.3891 | 102 / 0.6275 / 0.6592 |
| 0 | 3 / 0.0000 / 0.0037 | 1762 / 0.1175 / 0.1339 | 525 / 0.4571 / 0.4610 |
| 1 | 3 / 0.0000 / 0.0028 | 1574 / 0.1461 / 0.1652 | 672 / 0.4598 / 0.4762 |
| 2 | 3 / 0.0000 / 0.2176 | 1685 / 0.2849 / 0.3157 | 756 / 0.5370 / 0.5588 |
| 3 | 1 / 0.0000 / 0.0094 | 1458 / 0.9547 / 0.9896 | 864 / 0.9838 / 0.9970 |


### Growth × `agent_service_count_1h_inclusive`

Train growth edges: [0.8484848484848485, 1.1538461538461537, 1.6238207547169812]; other edges: [1.0].



| Growth bin | Other 0 | Other 1 |
| --- | --- | --- |
| -1 | 3510 / 0.1994 / 0.2045 | 2184 / 0.1103 / 0.1249 |
| 0 | 0 / not available / not available | 2290 / 0.1952 / 0.2087 |
| 1 | 0 / not available / not available | 2249 / 0.2397 / 0.2579 |
| 2 | 0 / not available / not available | 2444 / 0.3625 / 0.3908 |
| 3 | 0 / not available / not available | 2323 / 0.9651 / 0.9919 |


### Growth × `agent_top2_count_share_24h`

Train growth edges: [0.8484848484848485, 1.1538461538461537, 1.6238207547169812]; other edges: [0.15384615384615385, 0.5, 0.8].



| Growth bin | Other 0 | Other 1 | Other 2 | Other 3 |
| --- | --- | --- | --- | --- |
| -1 | 3526 / 0.2011 / 0.2056 | 547 / 0.1536 / 0.1362 | 735 / 0.1020 / 0.1341 | 886 / 0.0824 / 0.1045 |
| 0 | 0 / not available / not available | 243 / 0.1481 / 0.1615 | 920 / 0.2533 / 0.2694 | 1127 / 0.1579 / 0.1693 |
| 1 | 8 / 0.3750 / 0.2947 | 534 / 0.2622 / 0.2681 | 931 / 0.2664 / 0.2878 | 776 / 0.1907 / 0.2147 |
| 2 | 16 / 0.8125 / 0.8134 | 899 / 0.3782 / 0.3956 | 904 / 0.3341 / 0.3771 | 625 / 0.3696 / 0.3928 |
| 3 | 92 / 0.9565 / 0.9979 | 867 / 0.9746 / 0.9976 | 803 / 0.9614 / 0.9966 | 561 / 0.9572 / 0.9754 |


### Growth × `agent_top2_share_change_24h`

Train growth edges: [0.8484848484848485, 1.1538461538461537, 1.6238207547169812]; other edges: [0.24112480943858952, 0.4469726352079293, 0.658994239439633].



| Growth bin | Other -1 | Other 0 | Other 1 | Other 2 | Other 3 |
| --- | --- | --- | --- | --- | --- |
| -1 | 5418 / 0.1541 / 0.1617 | 100 / 0.6000 / 0.4959 | 62 / 0.2903 / 0.3837 | 53 / 0.3019 / 0.4047 | 61 / 0.1967 / 0.3257 |
| 0 | 51 / 0.0392 / 0.0528 | 192 / 0.1458 / 0.1567 | 494 / 0.1235 / 0.1504 | 686 / 0.3338 / 0.3440 | 867 / 0.1465 / 0.1555 |
| 1 | 69 / 0.0290 / 0.0649 | 451 / 0.2749 / 0.2724 | 602 / 0.1611 / 0.1904 | 578 / 0.3685 / 0.3939 | 549 / 0.1876 / 0.2011 |
| 2 | 51 / 0.4118 / 0.3786 | 791 / 0.4197 / 0.4325 | 698 / 0.2622 / 0.3045 | 482 / 0.4212 / 0.4597 | 422 / 0.3483 / 0.3779 |
| 3 | 125 / 0.9120 / 0.9586 | 908 / 0.9802 / 0.9979 | 515 / 0.9534 / 0.9960 | 410 / 0.9561 / 0.9890 | 365 / 0.9726 / 0.9858 |


### Growth × `receiver_history_coverage_days`

Train growth edges: [0.8484848484848485, 1.1538461538461537, 1.6238207547169812]; other edges: [28.0].



| Growth bin | Other 0 | Other 1 |
| --- | --- | --- |
| -1 | 2437 / 0.0792 / 0.0798 | 3257 / 0.2297 / 0.2444 |
| 0 | 10 / 0.0000 / 0.1137 | 2280 / 0.1961 / 0.2091 |
| 1 | 4 / 0.2500 / 0.2659 | 2245 / 0.2396 / 0.2579 |
| 2 | 2 / 0.0000 / 0.2853 | 2442 / 0.3628 / 0.3908 |
| 3 | 11 / 1.0000 / 0.9941 | 2312 / 0.9650 / 0.9919 |


### Growth × `wallet_history_coverage_days`

Train growth edges: [0.8484848484848485, 1.1538461538461537, 1.6238207547169812]; other edges: [28.0].



| Growth bin | Other 0 | Other 1 |
| --- | --- | --- |
| -1 | 2436 / 0.0792 / 0.0809 | 3258 / 0.2296 / 0.2436 |
| 0 | 8 / 0.0000 / 0.1294 | 2282 / 0.1959 / 0.2090 |
| 1 | 4 / 0.2500 / 0.2804 | 2245 / 0.2396 / 0.2579 |
| 2 | 3 / 0.0000 / 0.2018 | 2441 / 0.3630 / 0.3910 |
| 3 | 12 / 1.0000 / 0.9397 | 2311 / 0.9650 / 0.9922 |


The frozen Stage 12 tiny models supply an additional bounded comparison: growth alone Validation Macro F1 .7879; adding service acceleration .8210; top three .8367; top five .9036; full model .9521. Growth works strongly alone for A1, while other behaviours supply substantial complementary detection. This sequence does not isolate a statistical interaction term; the quartile panels likewise do not certify causality.

For example, in the lowest observed growth bin, the two populated acceleration bins have target1 fractions .1175 (N=1,762) and .4571 (N=525). In the highest growth bin they are already .9547 and .9838. High-growth target fractions also remain .9576–.9736 across the four signed cash-value-skew bins. Growth therefore does not need one particular cash direction to discriminate; acceleration adds useful discrimination where growth is low. High-growth novelty bins range .9270–1.0000 in target fraction, while reference means remain very high (.9659–.9983), illustrating both concentration and residual conditional differences.

## 9. Missingness, eligibility and observed agent age



| Partition | Group | N | Positive | Positive fraction | Growth AUC | Growth AP |
| --- | --- | --- | --- | --- | --- | --- |
| train | age35plus_insufficient_baseline | 222 | 19 | 0.0856 | 0.5000 | 0.0856 |
| train | agent_observed_age_under35 | 8795 | 918 | 0.1044 | 0.5000 | 0.1044 |
| train | available | 36943 | 16573 | 0.4486 | 0.8491 | 0.8772 |
| train | coverage_display28 | 38523 | 17192 | 0.4463 | 0.8259 | 0.8617 |
| train | no_agent | 14040 | 2709 | 0.1929 | 0.5000 | 0.1929 |
| train | unavailable | 23057 | 3646 | 0.1581 | 0.5000 | 0.1581 |
| validation | age35plus_insufficient_baseline | 27 | 8 | 0.2963 | 0.5000 | 0.2963 |
| validation | agent_observed_age_under35 | 2157 | 233 | 0.1080 | 0.5000 | 0.1080 |
| validation | available | 9306 | 4114 | 0.4421 | 0.8302 | 0.8572 |
| validation | coverage_display28 | 9668 | 4264 | 0.4410 | 0.8081 | 0.8426 |
| validation | no_agent | 3510 | 700 | 0.1994 | 0.5000 | 0.1994 |
| validation | unavailable | 5694 | 941 | 0.1653 | 0.5000 | 0.1653 |




| Partition | Available age range days | N | Positive fraction | Growth AUC | Growth AP |
| --- | --- | --- | --- | --- | --- |
| train | 120..1000 | 15048 | 0.4337 | 0.8407 | 0.8636 |
| train | 35..60 | 6564 | 0.4752 | 0.8469 | 0.8846 |
| train | 60..90 | 7672 | 0.4729 | 0.8582 | 0.8936 |
| train | 90..120 | 7659 | 0.4309 | 0.8594 | 0.8797 |
| validation | 120..1000 | 3793 | 0.4601 | 0.8165 | 0.8503 |
| validation | 35..60 | 1668 | 0.4940 | 0.8621 | 0.9004 |
| validation | 60..90 | 1922 | 0.3730 | 0.8251 | 0.8223 |
| validation | 90..120 | 1923 | 0.4306 | 0.8311 | 0.8562 |


Age is elapsed time since the first observed service, never private entity activation. Available Validation growth has AUC .8302 and AP .8572; age-stratified AUC remains .8165–.8621. Availability alone has AUC .6459. The earlier 11-marker-only model has AUC .6828 and Macro F1 .5372. Missingness contributes association but cannot reproduce the reference or explain within-eligible separation.



| Partition | Primitive | Target0 mean | Target1 mean | Growth Pearson | Growth Spearman |
| --- | --- | --- | --- | --- | --- |
| train | agent_observation_age_days | 107.8859 | 105.6463 | -0.0286 | -0.0064 |
| train | baseline_median | 18.4313 | 14.6186 | -0.3999 | -0.3767 |
| train | baseline_services | 109.9484 | 88.4653 | -0.3736 | -0.3427 |
| train | new_distinct | 14.6056 | 20.3669 | 0.3751 | 0.4639 |
| train | novelty | 0.8608 | 0.8852 | 0.2185 | 0.1872 |
| train | recent_distinct | 17.4113 | 23.3769 | 0.3077 | 0.4068 |
| validation | agent_observation_age_days | 106.3547 | 108.0644 | -0.0099 | -0.0059 |
| validation | baseline_median | 17.3904 | 14.3021 | -0.4063 | -0.3811 |
| validation | baseline_services | 107.1768 | 89.9101 | -0.3694 | -0.3327 |
| validation | new_distinct | 9.2675 | 14.0107 | 0.4875 | 0.6303 |
| validation | novelty | 0.6067 | 0.6809 | 0.3375 | 0.3378 |
| validation | recent_distinct | 16.8609 | 21.6855 | 0.2464 | 0.3807 |




| Partition | Available rows | Available other A1 gates pass | Growth>=1.5 other gates pass | Growth>=1.5 other gates fail | Denominator below 1 |
| --- | --- | --- | --- | --- | --- |
| train | 36943 | 34330 | 11040 | 144 | 0 |
| validation | 9306 | 6620 | 2648 | 177 | 0 |


The denominator floor is not active on any eligible development row. Lower baseline weekly distinct counts and larger recent/new counts both contribute to high growth. The 28d displayed coverage cap cannot distinguish 29d from 35d observation and must not be used as eligibility proof.

## 10. Development generator source audit

The V3 wrapper delegates observable generation to `ml_v2/src/dataset_generator.py` with the V3 manifest, then creates universal decision-point labels. That source was read as text only; no generator was imported or executed. Shared source contains partition branches, but no evaluation data or private evaluation manifest was accessed.

- Frozen truth materialization imports reference_evaluator.evaluate_rows, not reference.ReferenceEvaluator. A1 reconstruction against frozen labels confirms this source path on both development partitions. [Source, line 8](<C:/Users/PROMINENT/Desktop/important/My Projects/Last update for AML system/AML System/ml_v3/src/generate_v3.py:8>).

- Final decision_point_target is bool(frozen evidence families), independent of private routine/hard/campaign origin. Legitimate-like origin rows crossing A1 gates become target1 and disappear from target0 overlap comparisons. [Source, line 65](<C:/Users/PROMINENT/Desktop/important/My Projects/Last update for AML system/AML System/ml_v3/src/generate_v3.py:65>).

- Routine events sample active wallets broadly across six 30d blocks; agent selection uses fixed activity-band weights .5/1/2. The source has no explicit evolving ordinary agent catchment, customer-acquisition campaign, or seasonal wallet-population process. [Source, line 206](<C:/Users/PROMINENT/Desktop/important/My Projects/Last update for AML system/AML System/ml_v2/src/dataset_generator.py:206>).

- Both A1 and H7/A1 select 4..min(16,n-1) counterparts with lowest preceding 30d service frequency. Wallets are cycled through, with a previously seen wallet in the final position when available. This encourages novelty; it does not set the final growth ratio to a constant. [Source, line 256](<C:/Users/PROMINENT/Desktop/important/My Projects/Last update for AML system/AML System/ml_v2/src/dataset_generator.py:256>).

- A2/H8-A2 choose 2..min(6,n/2) concentration wallets; 35%..85% of episode events use them, with remaining events sampled outside that subset. Growth is not a direct A2 primitive. [Source, line 262](<C:/Users/PROMINENT/Desktop/important/My Projects/Last update for AML system/AML System/ml_v2/src/dataset_generator.py:262>).

- A3/H7-A3 use 2..4 temporal clusters with within-cluster width .2 before scaling to episode duration; serviced wallets otherwise sampled broadly. This supplies burst information, not a growth substitute. [Source, line 333](<C:/Users/PROMINENT/Desktop/important/My Projects/Last update for AML system/AML System/ml_v2/src/dataset_generator.py:333>).

- A4/H8-A4 guarantee an opening two-versus-one cash direction portion and sample amounts until dominant value share is 60%..95%. Subsequent events, history and target conjunction determine whether A4 fires. [Source, line 271](<C:/Users/PROMINENT/Desktop/important/My Projects/Last update for AML system/AML System/ml_v2/src/dataset_generator.py:271>).

- H7 maps to A1/A3 and H8 to A2/A4 through the shared scenario manifest. Hard episodes contain 6..24 events; agent campaign episodes 6..30. Hard coordination is uniform .1..8; campaign strengths use .25/.55/.8. Support overlaps rather than separate fixed positive/negative ratios. [Source, line 184](<C:/Users/PROMINENT/Desktop/important/My Projects/Last update for AML system/AML System/ml_v2/src/dataset_generator.py:184>).

- Episode durations and starts are bounded inside 30d blocks. A1 uses 1..7 days, A2/A4 .25..7 days, A3 900..7200 seconds. Boundary endpoints are explicitly included. These are synthetic temporal templates, with no independent empirical calibration. [Source, line 224](<C:/Users/PROMINENT/Desktop/important/My Projects/Last update for AML system/AML System/ml_v2/src/dataset_generator.py:224>).

- Development Train has 600 wallets/96 agents and Validation 150/24 over the same 180d horizon, with fourfold event scaling. Similar per-agent service loads encounter a smaller global wallet pool in Validation. This is a plausible contributor to novelty saturation and its partition shift, not an isolated causal experiment. [Source, line 16](<C:/Users/PROMINENT/Desktop/important/My Projects/Last update for AML system/AML System/ml_v3/src/generate_v3.py:16>).

- Frozen evaluator full_coverage defaults to 28d; corrected growth requires 35d for a 7d recent plus 28d baseline. Frozen A1 recent/baseline endpoint conventions also differ. Do not silently replace frozen labels using the other evaluator. [Source, line 18](<C:/Users/PROMINENT/Desktop/important/My Projects/Last update for AML system/AML System/ml_v3/src/reference_evaluator.py:18>).



| Partition | Observed wallets | Observed agents | Agent services |
| --- | --- | --- | --- |
| train | 600 | 96 | 45960 |
| validation | 150 | 24 | 11490 |




| Partition | Recipe/category | Episodes | Size min | Size max | Duration days min | Duration days max | Coordination min | Coordination max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | A1 | 66 | 6.0000 | 30.0000 | 1.0577 | 6.8713 | 0.2500 | 0.8000 |
| train | A2 | 70 | 6.0000 | 29.0000 | 0.2530 | 6.9913 | 0.2500 | 0.8000 |
| train | A3 | 71 | 6.0000 | 30.0000 | 0.0119 | 0.0805 | 0.2500 | 0.8000 |
| train | A4 | 69 | 6.0000 | 30.0000 | 0.2732 | 6.9684 | 0.2500 | 0.8000 |
| train | H7 | 162 | 6.0000 | 24.0000 | 0.0112 | 6.9616 | 0.1030 | 0.7977 |
| train | H8 | 170 | 6.0000 | 24.0000 | 0.2552 | 6.9798 | 0.1056 | 0.7949 |
| validation | A1 | 23 | 6.0000 | 29.0000 | 1.0118 | 6.6685 | 0.2500 | 0.8000 |
| validation | A2 | 17 | 7.0000 | 28.0000 | 0.7769 | 5.7948 | 0.2500 | 0.8000 |
| validation | A3 | 22 | 7.0000 | 27.0000 | 0.0105 | 0.0822 | 0.2500 | 0.8000 |
| validation | A4 | 19 | 6.0000 | 28.0000 | 1.2538 | 6.8228 | 0.2500 | 0.8000 |
| validation | H7 | 42 | 6.0000 | 23.0000 | 0.0113 | 6.1185 | 0.1032 | 0.7954 |
| validation | H8 | 40 | 6.0000 | 24.0000 | 0.2561 | 6.9777 | 0.1124 | 0.7780 |


The source does not impose a deterministic 1.5 growth jump or a fixed realized growth ratio. A1 and H7/A1 share low-frequency customer selection; they differ in episode/category mixtures and coordination sampling. Fixed episode bounds, broad routine sampling and finite wallet pools make a synthetic separability mechanism plausible, while universal labels demonstrably condition the negative tail. No counterfactual regeneration was performed, so causal shares of these construction effects are unknown.

## 11. Near-proxy assessment

**HIGH proxy concern**, scoped to A1 in eligible synthetic development rows.



| Predicate | Shared primitives | Missing from growth | Differences from feature |
| --- | --- | --- | --- |
| A1 | agent service wallet sets; 7d recent; four preceding 7d distinct counts; denominator max(1,median); ratio component 1.5 in target | at least 6 recent distinct, 4 new distinct, novelty >=.5; feature never thresholds itself | Feature requires first observation <=t-35d, open lower/closed upper windows and full-key prior inclusion. Frozen target requires 28d coverage, closed lower/open upper timestamp windows; same-time prior services excluded from its recent window. |
| A2 | agent serviced-wallet histories and observation eligibility concept | 24h event concentration, independently pooled baseline top-two comparator, recent >=8, baseline >=20 and >=5 wallets, share>=.65 and change>=.2 | Growth uses distinct-wallet ratio over 7d versus weekly medians; A2 uses event shares. Frozen A2 baseline is [t-28d,t-1d), 27d, and coverage28d, unlike corrected disjoint28d baseline/29d coverage. |
| A3 | agent service histories; minimum baseline service support | one-hour recent >=5 events, >=3 wallets, rate acceleration | Frozen A3 reuses 7d-offset ab (t-35d..t-7d) for its service denominator despite hourly recent window; corrected architecture uses preceding28d shifted by1h. Growth counts unique wallets rather than services. |
| A4 | agent history and baseline availability concept | current cash role, >=6 cash events, >=3 cash wallets, signed value/count skews, sign agreement, historical skew change | No amount or cash direction enters growth. Frozen A4 uses 27d cash comparator, >=8 cash and >=12 ab7 services plus28dcoverage; corrected architecture uses disjoint28d cash/service comparator plus29dcoverage. |




| Partition | Fixed condition | Condition true | A1 true | Both | Condition without A1 | A1 without condition | Target0 condition |
| --- | --- | --- | --- | --- | --- | --- | --- |
| train | feature_ratio_ge1.5 | 11184 | 11476 | 11040 | 144 | 436 | 135 |
| train | implemented_ratio_ge1.5 | 18528 | 11476 | 11476 | 7052 | 0 | 6737 |
| train | written_full_A1 | 11040 | 11476 | 11040 | 0 | 436 | 0 |
| validation | feature_ratio_ge1.5 | 2825 | 2745 | 2648 | 177 | 97 | 117 |
| validation | implemented_ratio_ge1.5 | 4563 | 2745 | 2745 | 1818 | 0 | 1665 |
| validation | written_full_A1 | 2648 | 2745 | 2648 | 0 | 97 | 0 |


In Validation, available growth≥1.5 covers 2,648 A1 positives, with 177 non-A1 rows (117 target0), while 97 A1 positives are unavailable. Growth contains only the relative-growth component: it does not encode the novelty/count conjunction, other families, or complete target. Therefore a direct complete-oracle claim is false, while an A1 near-proxy concern is well supported. Strong target alignment from permitted observables is distinct from private-field or future leakage.

## 12. Train-only label shuffle

Permute all 60000 Train labels with default_rng(20260928). Split rows by independent default_rng(20260929) permutation into 48000 fit and 12000 test rows. Score both against shuffled labels only. No Validation scores for this model.



| Subset | accuracy | balanced_accuracy | macro_f1 | suspicious_precision | suspicious_recall | suspicious_f1 | average_precision | roc_auc | false_positive_rate | confusion_matrix |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fit | 0.7021 | 0.5656 | 0.5326 | 0.8136 | 0.1484 | 0.2511 | 0.6000 | 0.7318 | 0.0172 | [[31302, 549], [13752, 2397]] |
| reserved_train_test | 0.6476 | 0.5038 | 0.4397 | 0.3720 | 0.0568 | 0.0985 | 0.3471 | 0.5062 | 0.0492 | [[7540, 390], [3839, 231]] |


Reserved Train ROC-AUC **.5062**, AP **.3471** against prevalence **.3392**, and balanced accuracy **.5038** are near chance. Fit-sample ROC-AUC .7318 and AP .6000 show that the flexible estimator can partially memorize shuffled labels; reporting only in-sample fit would be misleading. The test supports absence of strong preserved association in this fixed shuffle protocol. One shuffle does not prove the absence of every leakage pathway. No Validation predictions were made for the shuffle model.

## 13. Four family-removal diagnostic fits

All retain the same 32 features, seed, estimator, weights and .50 threshold. D1 excludes A1-positive Train rows; D2 A2; D3 A4; D4 the union of all agent-positive rows. Original labels remain unchanged. Excluding a row removes all its overlapping supervision and changes positive prevalence, so these are diagnostic interventions on the training sample, not isolated causal family effects.



| Fit | Excluded | Fit target0 | Fit target1 | Agent-only recall | A1 recall | A2 recall | A3 recall | A4 recall | Growth AP drop | Top feature | Top share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D1 | 11476 | 39781 | 8743 | 0.2827 | 0.2499 | 0.8495 | 0.9959 | 0.6528 | 0.0167 | agent_service_acceleration_1h | 0.1443 |
| D2 | 3770 | 39781 | 16449 | 0.8562 | 0.9789 | 0.6796 | 0.9876 | 0.6588 | 0.3288 | agent_wallet_growth_ratio_7d | 0.5773 |
| D3 | 1353 | 39781 | 18866 | 0.8841 | 0.9767 | 0.8581 | 0.9959 | 0.4599 | 0.3220 | agent_wallet_growth_ratio_7d | 0.5968 |
| D4 | 15432 | 39781 | 4787 | 0.0179 | 0.1224 | 0.5151 | 0.2268 | 0.1276 | -0.0191 | wallet_count_utc_day_inclusive | 0.0646 |


### fit_subset_metrics



| Fit | accuracy | balanced_accuracy | macro_f1 | suspicious_precision | suspicious_recall | suspicious_f1 | average_precision | roc_auc | false_positive_rate | confusion_matrix |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D1 | 0.9767 | 0.9549 | 0.9600 | 0.9480 | 0.9210 | 0.9343 | 0.9811 | 0.9948 | 0.0111 | [[39339, 442], [691, 8052]] |
| D2 | 0.9800 | 0.9752 | 0.9758 | 0.9677 | 0.9637 | 0.9657 | 0.9953 | 0.9979 | 0.0133 | [[39252, 529], [597, 15852]] |
| D3 | 0.9761 | 0.9721 | 0.9726 | 0.9648 | 0.9608 | 0.9628 | 0.9947 | 0.9972 | 0.0166 | [[39120, 661], [739, 18127]] |
| D4 | 0.9933 | 0.9913 | 0.9829 | 0.9512 | 0.9887 | 0.9696 | 0.9953 | 0.9994 | 0.0061 | [[39538, 243], [54, 4733]] |


### train



| Fit | accuracy | balanced_accuracy | macro_f1 | suspicious_precision | suspicious_recall | suspicious_f1 | average_precision | roc_auc | false_positive_rate | confusion_matrix |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D1 | 0.8395 | 0.7672 | 0.7935 | 0.9615 | 0.5455 | 0.6961 | 0.8411 | 0.8814 | 0.0111 | [[39339, 442], [9189, 11030]] |
| D2 | 0.9605 | 0.9479 | 0.9551 | 0.9720 | 0.9090 | 0.9395 | 0.9760 | 0.9798 | 0.0133 | [[39252, 529], [1839, 18380]] |
| D3 | 0.9656 | 0.9570 | 0.9612 | 0.9661 | 0.9307 | 0.9481 | 0.9833 | 0.9863 | 0.0166 | [[39120, 661], [1401, 18818]] |
| D4 | 0.7897 | 0.6909 | 0.7083 | 0.9699 | 0.3879 | 0.5542 | 0.6653 | 0.6756 | 0.0061 | [[39538, 243], [12376, 7843]] |


### validation



| Fit | accuracy | balanced_accuracy | macro_f1 | suspicious_precision | suspicious_recall | suspicious_f1 | average_precision | roc_auc | false_positive_rate | confusion_matrix |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D1 | 0.8337 | 0.7611 | 0.7863 | 0.9438 | 0.5385 | 0.6857 | 0.8288 | 0.8714 | 0.0163 | [[9783, 162], [2333, 2722]] |
| D2 | 0.9457 | 0.9333 | 0.9385 | 0.9406 | 0.8954 | 0.9174 | 0.9647 | 0.9754 | 0.0288 | [[9659, 286], [529, 4526]] |
| D3 | 0.9493 | 0.9400 | 0.9429 | 0.9368 | 0.9112 | 0.9238 | 0.9701 | 0.9787 | 0.0313 | [[9634, 311], [449, 4606]] |
| D4 | 0.7815 | 0.6811 | 0.6961 | 0.9454 | 0.3731 | 0.5350 | 0.6564 | 0.6707 | 0.0110 | [[9836, 109], [3169, 1886]] |


`fit_subset_metrics` evaluates actual fitted rows. `train` evaluates all original Train rows, including exclusions, and is not a pure training score. Validation is unchanged. All four fits completed without captured warnings.



| Fit | S1 | S2 | S3 | S4 | N1 | N2 | N3 | N4 | A1 | A2 | A3 | A4 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D1 | 336 | 1 | 723 | 7 | 183 | 443 | 14 | 208 | 11476 | 1120 | 970 | 425 |
| D2 | 603 | 1 | 1244 | 2 | 34 | 406 | 7 | 110 | 1120 | 3770 | 279 | 330 |
| D3 | 43 | 0 | 149 | 0 | 0 | 0 | 0 | 26 | 425 | 330 | 100 | 1353 |
| D4 | 857 | 2 | 1705 | 9 | 221 | 783 | 22 | 328 | 11476 | 3770 | 1810 | 1353 |


Removing A1 supervision reduces growth permutation AP drop from .3346 to .0167, with A1 recall .2499 and Macro F1 .7863. Removing A2 or A4 leaves growth as the top feature with shares .5773/.5968. Removing all agent positives gives a negative growth AP drop (−.0191); permutation can improve a poorly matched diagnostic model. Negative importance is not evidence that growth is harmful in the reference. These results identify A1 supervision as the main driver. None of these models is a candidate for promotion.

## 14. Model-family comparison

All four saved Stage 11 models use the same permutation-AP diagnostic: 3 repeats, max_samples=3,000, seed20260928, one worker. HGB/XGBoost reuse Stage 13 computations; RF/GB receive new permutation scoring only. Absolute AP-drop mass defines shares, including negative estimates. This replaces incompatible native gain/impurity comparisons.



| Family | Candidate | Macro F1 | Growth AP drop | Top feature | Top share | Matched removal index |
| --- | --- | --- | --- | --- | --- | --- |
| gb | s11_08_gradient_boosting | 0.9382 | 0.3059 | agent_wallet_growth_ratio_7d | 0.6327 | not available |
| hgb | s11_09_hist_gradient_boosting | 0.9521 | 0.3346 | agent_wallet_growth_ratio_7d | 0.6150 | 0.3187 |
| rf | s11_27_random_forest | 0.9464 | 0.3225 | agent_wallet_growth_ratio_7d | 0.5432 | not available |
| xgb | s11_15_xgboost | 0.9456 | 0.3041 | agent_wallet_growth_ratio_7d | 0.5865 | 0.2857 |


Growth leads all four permutation profiles: GB .6327, HGB .6150, RF .5432, XGBoost .5865. HGB and XGBoost also have extreme matched retraining dependence. RF/GB matched removal was not measured; permutation sensitivity must not be called an equivalent removal estimate. Different weighting/capacity choices confound algorithm-only claims, but the concentration is clearly not confined to HGB.

## 15. Direct answers and decision

### 1. Why is growth powerful?

It measures A1's defining relative customer-growth component. A1 contributes most lost detections, while the other agent features encode different mechanisms.

### 2. Is the signal behaviourally legitimate?

Yes as a causal observable customer-growth descriptor and a component of the chosen review rule. These data do not establish real-world suspiciousness or specificity.

### 3. Does synthetic construction amplify it?

Yes: broad routine wallet sampling and episodic low-frequency customer selection make other A1 gates frequently pass. Universal predicate labeling also removes qualifying high-growth H7/H8/routine events from target0. The two mechanisms cannot be assigned causal percentages by this observational audit.

### 4. Is it a near-oracle?

HIGH A1 proxy concern in eligible development rows; it is not a complete predicate or overall-target oracle. Available high-growth non-A1 rows and unavailable A1 positives are explicit counterexamples.

### 5. Is missingness/history responsible?

It contributes class association, but available-only and age-stratified growth remain predictive. The denominator floor is checked separately. The frozen target's 28d coverage versus feature's 35d explains unavailable A1 positives.

### 6. Which family contributes most?

A1. Validation loses 1634 A1 detections out of 1666 total lost positives; two A1 detections are recovered. Net A1 loss exceeds total net loss because other families have recoveries.

### 7. Are negatives sufficiently overlapping?

Observed eligible A1 versus target0 H7/H8/routine overlap is very small, insufficient to establish robustness to legitimate customer expansion. Hard/routine all-origin cohorts do contain high growth; those satisfying A1 are relabeled positive by design. More high-growth generation alone cannot create negatives that satisfy the unchanged full predicate.

### 8. Can model training alone solve it?

No evidence supports that as the sole remedy: all four model families concentrate on growth; removing A1 supervision greatly reduces its importance but loses agent detection. Model tuning cannot resolve target semantics or population assumptions.

### 9. Would more features likely solve it?

The tested N3/A4 additions did not replace A1 information. A scientifically motivated A1 representation study may help, but more columns alone have no demonstrated solution and duplicate proxies could only redistribute importance.

### 10. Does V3 need development redesign before final evaluation?

Yes: first reconcile written predicates and the actual frozen evaluator in a separately versioned development plan, then audit realistic agent acquisition/retention and near-boundary negatives under the declared task. Preserve this experiment, prohibit silent relabeling, and keep holdouts sealed. Any new target/evaluation compatibility needs explicit governance before future evaluation.

**F — MULTIPLE FACTORS; CONTROLLED DEVELOPMENT REDESIGN REQUIRED.**

A1 predicate alignment, synthetic population/label conditioning, insufficient independent A1 representation, and a confirmed evaluator/contract coverage discrepancy jointly explain the evidence. Dependence persists across algorithms. Missingness is secondary.

Recommend a bounded development design stage that first reconciles evaluator and written semantics, then proposes realistic agent customer acquisition/retention and explicit near-boundary negatives. Preserve all current artifacts under their existing version. Any target change requires a new experiment and a declared evaluation-compatibility policy; existing sealed evaluation cannot be treated as automatically compatible. Stage 14 implements none of these consequences.

Target construction and population support must justify the intended AML decision-support claim. Removing a valid A1 component predictably loses A1 information; duplicated proxies could lower concentration without improving robustness. Importance concentration alone is insufficient grounds for weakening a valid feature.

## 16. Protection, verification, evidence and reproducibility



| Check | Result |
| --- | --- |
| Verification | PASS |
| Protected files | 660 |
| Changed paths | [] |
| New fits | 5 |
| Metric sets recomputed | 46 |
| Model reload maximum difference | 0.0000 |
| Shuffle replay exact | True |
| Artifact hashes | 13 |
| Test methods | 3 |


The explicit allowlist covers earlier application/V1/V2 artifacts, V3 development inputs/design, Stage 10A matrices/contract, Stage 11/12/13 models/evidence/source and inspected generator/evaluator source. Named public commitments retain SHA-256 `efc14471b98103a3ad547d93fc56833d014389efd9d3c6e5be6ba896c70d9d58`. This certifies listed bytes and public metadata, not unread evaluation contents.

Verification reloads every new model, recomputes saved metrics/slices and descriptive counts, checks the exact shuffle permutation/split, and checks plan/source/artifact/protection hashes. Three regression tests cover marker-aware P99, fixed Train bins, and growth coverage/equal-time/future behaviour. Permutation diagnostics are source-hashed rather than repeated; no same-seed training repeat was added.



| Evidence | File |
| --- | --- |
| feature_contract | [stage14_feature_contract.json](stage14_feature_contract.json) |
| growth_distributions | [stage14_growth_distributions.json](stage14_growth_distributions.json) |
| family_dependence | [stage14_family_dependence.json](stage14_family_dependence.json) |
| negative_overlap | [stage14_negative_overlap.json](stage14_negative_overlap.json) |
| univariate_power | [stage14_univariate_power.json](stage14_univariate_power.json) |
| agent_feature_comparison | [stage14_agent_feature_comparison.json](stage14_agent_feature_comparison.json) |
| interactions | [stage14_interactions.json](stage14_interactions.json) |
| eligibility_analysis | [stage14_eligibility_analysis.json](stage14_eligibility_analysis.json) |
| generator_audit | [stage14_generator_audit.json](stage14_generator_audit.json) |
| proxy_risk | [stage14_proxy_risk.json](stage14_proxy_risk.json) |
| shuffle_test | [stage14_shuffle_test.json](stage14_shuffle_test.json) |
| family_removal | [stage14_family_removal.json](stage14_family_removal.json) |
| model_family_comparison | [stage14_model_family_comparison.json](stage14_model_family_comparison.json) |
| decision | [stage14_decision.json](stage14_decision.json) |
| protection | [stage14_protection.json](stage14_protection.json) |
| final_verification | [stage14_final_verification.json](stage14_final_verification.json) |
| reference_reproduction | [stage14_reference_reproduction.json](stage14_reference_reproduction.json) |
| plan | [stage14_plan.json](stage14_plan.json) |
| fit log | [stage14_fit_log.json](stage14_fit_log.json) |
| artifact manifest | [stage14_artifact_manifest.json](stage14_artifact_manifest.json) |


Sources: `stage14_growth_diagnosis.py`, `run_stage14.py`, `audit_stage14.py`, `verify_stage14.py`, `report_stage14.py`; tests: `test_stage14_diagnosis.py`. The supplementary audit entry point creates source/decision synthesis without fitting. Models/scores are in `models/stage14_diagnostics/`; observable diagnostic primitives in `evidence/stage14/`.

```powershell
python -B ml_v3/src/run_stage14.py
python -B ml_v3/src/audit_stage14.py
python -B ml_v3/src/verify_stage14.py
python -B ml_v3/src/report_stage14.py
```

The runner refuses existing Stage 14 outputs. A new reproduction requires an isolated development checkout with the same frozen inputs/environment and a fresh protection snapshot; preserve this evidence. Audit, verification and report commands do not fit models. These are selected synthetic development findings with dependent events and reused Validation, not real-world effectiveness, production readiness or regulatory certification.

No dataset/target change, feature promotion, threshold optimization, calibration, Train+Validation refit, holdout evaluation, V1 replacement or application integration occurred.

**V3 STAGE 14 COMPLETE — WAITING FOR APPROVAL.**
