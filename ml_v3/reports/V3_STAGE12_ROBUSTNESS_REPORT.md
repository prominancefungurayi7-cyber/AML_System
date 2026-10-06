# MODEL V3 — STAGE 12 CONTROLLED ROBUSTNESS, FEATURE-DEPENDENCE AND WEAK-FAMILY DIAGNOSIS

**Technical execution: PASS. Quality decision: B — STRONG BUT FEATURE-CONCENTRATED.**

The Stage 11 reference is reproduced exactly. Removing `agent_wallet_growth_ratio_7d` reduces Validation Macro F1 from **0.9521 to 0.8102** and suspicious recall from **0.9349 to 0.6162**. This is **EXTREME** dependence under the rule frozen before fitting. The missingness-only diagnostic is substantially weaker (Macro F1 **0.5372**, ROC-AUC **0.6828**); missingness alone does not reproduce the reference result. Domain-only positives provide evidence of useful signals in all three domains, but the strong aggregate score depends heavily on the growth feature.

This is the single consolidated main report. All new models are diagnostic artifacts, with no promotion or change to the official 32-feature contract. Threshold stays **0.50** throughout. Further controlled development is needed before final model or threshold work.

## 1. Scope, preregistration and frozen reference

Model inputs were only the corrected Stage 10A Train (60,000 × 32) and Validation (15,000 × 32) matrices. Targets remain 39,781/20,219 and 9,945/5,055 for classes 0/1. The saved Stage 11 model and score hashes were checked before loading. The reference object/file was never refitted or overwritten.

Frozen development ground truth and episode plans were joined by transaction ID solely for the requested diagnostic slices. Only transaction type/channel were retained from development transactions for error analysis; no histories or features were recomputed. Metadata never entered fit or predict. No evaluation directory was enumerated or evaluation data opened. Named public certificates were hashed by explicit path.



| Property | Recorded value |
| --- | --- |
| Plan saved UTC | 2026-09-28T21:36:18.846642+00:00 |
| First diagnostic fit UTC | 2026-09-28T21:36:21.189125+00:00 |
| New diagnostic fits | 20 |
| Wall seconds | 83.5933 |
| Threshold | 0.5000 |
| Positive / negative fit weight | 1.5 / 1; missingness-only uses unit weights |
| Predetermined seeds | [20260928, 20260929, 20260930, 20261001, 20261002] |
| Runtime | {"executable": "C:\\Users\\PROMINENT\\AppData\\Local\\Programs\\Python\\Python314\\python.exe", "numpy": "2.4.3", "platform": "Windows-11-10.0.26200-SP0", "python": "3.14.3 (tags/v3.14.3:323c59a, Feb  3 2026, 16:04:56) [MSC v.1944 64 bit (AMD64)]", "sklearn": "1.9.0", "threads": 2} |


The plan fixes all feature subsets, the Stage 11 importance ranking, the five seeds, the missingness model and classification rules before the first fit. Nine removal/domain fits, four tiny-feature fits, one missingness fit, five seed fits and one same-seed repeat total **20** new fits. A reuses the saved full reference. All subset models use the same HGB parameters as the reference (200 iterations, learning rate .07, depth 6, 31 leaves, minimum leaf 20, L2=1, no early stopping) and raw marker-preserving inputs. No fitted preprocessing or extra search was introduced. Full estimator defaults and source digests are in the plan.



| Partition | Max score difference | Predictions identical |
| --- | --- | --- |
| train | 0.0000 | True |
| validation | 0.0000 | True |




| Partition | Macro F1 | Precision 1 | Recall 1 | F1 1 | AP | ROC-AUC | FPR | Confusion [[TN,FP],[FN,TP]] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | 0.9695 | 0.9676 | 0.9513 | 0.9594 | 0.9927 | 0.9957 | 0.0162 | [[39137, 644], [984, 19235]] |
| validation | 0.9521 | 0.9379 | 0.9349 | 0.9364 | 0.9772 | 0.9888 | 0.0315 | [[9632, 313], [329, 4726]] |


All reproduced domain, family and target-0 hard-negative counts/recalls/FPRs agree with the saved Stage 11 records. Scores use continuous probabilities for AP/ROC-AUC; classification uses probability ≥0.50. AP is Average Precision. Class 1 is the frozen suspicious-pattern review target, not proven criminal activity.

## 2. Controlled ablations



| Ablation | Representation | Columns |
| --- | --- | --- |
| A | Saved all-32 reference | 32 |
| B | Remove growth | 31 |
| C | Remove growth + novelty | 30 |
| D | Remove agent domain | 23 |
| E | Remove network domain | 22 |
| F | Remove structuring domain | 25 |
| G | Structuring only | 7 |
| H | Network only | 10 |
| I | Agent only | 9 |
| J | Remove coverage; retain current + behaviour | 29 |


### Train



| Ablation | Macro F1 | Precision 1 | Recall 1 | F1 1 | AP | ROC-AUC | FPR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 0.9695 | 0.9676 | 0.9513 | 0.9594 | 0.9927 | 0.9957 | 0.0162 |
| B | 0.8420 | 0.8020 | 0.7759 | 0.7887 | 0.8999 | 0.9353 | 0.0973 |
| C | 0.8270 | 0.8105 | 0.7230 | 0.7643 | 0.8856 | 0.9239 | 0.0859 |
| D | 0.7532 | 0.8263 | 0.5254 | 0.6424 | 0.8093 | 0.8732 | 0.0561 |
| E | 0.9275 | 0.9510 | 0.8569 | 0.9015 | 0.9620 | 0.9708 | 0.0224 |
| F | 0.9526 | 0.9472 | 0.9265 | 0.9367 | 0.9847 | 0.9899 | 0.0262 |
| G | 0.6647 | 0.7633 | 0.3684 | 0.4969 | 0.6779 | 0.7550 | 0.0580 |
| H | 0.6933 | 0.7875 | 0.4162 | 0.5446 | 0.7096 | 0.7956 | 0.0571 |
| I | 0.8808 | 0.9500 | 0.7419 | 0.8331 | 0.8992 | 0.9301 | 0.0199 |
| J | 0.9678 | 0.9642 | 0.9502 | 0.9571 | 0.9925 | 0.9956 | 0.0179 |


### Validation



| Ablation | Macro F1 | Precision 1 | Recall 1 | F1 1 | AP | ROC-AUC | FPR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 0.9521 | 0.9379 | 0.9349 | 0.9364 | 0.9772 | 0.9888 | 0.0315 |
| B | 0.8102 | 0.8913 | 0.6162 | 0.7287 | 0.8661 | 0.9098 | 0.0382 |
| C | 0.8112 | 0.7807 | 0.7106 | 0.7440 | 0.8623 | 0.9037 | 0.1015 |
| D | 0.7173 | 0.7656 | 0.4793 | 0.5895 | 0.7575 | 0.8312 | 0.0746 |
| E | 0.9103 | 0.9199 | 0.8406 | 0.8784 | 0.9399 | 0.9562 | 0.0372 |
| F | 0.9367 | 0.9186 | 0.9134 | 0.9160 | 0.9685 | 0.9818 | 0.0411 |
| G | 0.6432 | 0.7273 | 0.3393 | 0.4627 | 0.6372 | 0.7173 | 0.0647 |
| H | 0.6824 | 0.7596 | 0.4057 | 0.5289 | 0.6850 | 0.7757 | 0.0653 |
| I | 0.8610 | 0.9141 | 0.7203 | 0.8057 | 0.8748 | 0.9102 | 0.0344 |
| J | 0.9500 | 0.9325 | 0.9349 | 0.9337 | 0.9774 | 0.9885 | 0.0344 |


### Validation domains and all families



| Ablation | Domain | Support | TP | FN | Recall |
| --- | --- | --- | --- | --- | --- |
| A | agent | 3835 | 3579 | 256 | 0.9332 |
| A | network | 1271 | 1203 | 68 | 0.9465 |
| A | structuring | 1039 | 1034 | 5 | 0.9952 |
| B | agent | 3835 | 1963 | 1872 | 0.5119 |
| B | network | 1271 | 1207 | 64 | 0.9496 |
| B | structuring | 1039 | 1031 | 8 | 0.9923 |
| C | agent | 3835 | 2439 | 1396 | 0.6360 |
| C | network | 1271 | 1208 | 63 | 0.9504 |
| C | structuring | 1039 | 1035 | 4 | 0.9962 |
| D | agent | 3835 | 1264 | 2571 | 0.3296 |
| D | network | 1271 | 1214 | 57 | 0.9552 |
| D | structuring | 1039 | 1030 | 9 | 0.9913 |
| E | agent | 3835 | 3573 | 262 | 0.9317 |
| E | network | 1271 | 726 | 545 | 0.5712 |
| E | structuring | 1039 | 1035 | 4 | 0.9962 |
| F | agent | 3835 | 3573 | 262 | 0.9317 |
| F | network | 1271 | 1208 | 63 | 0.9504 |
| F | structuring | 1039 | 908 | 131 | 0.8739 |
| G | agent | 3835 | 1004 | 2831 | 0.2618 |
| G | network | 1271 | 676 | 595 | 0.5319 |
| G | structuring | 1039 | 1032 | 7 | 0.9933 |
| H | agent | 3835 | 965 | 2870 | 0.2516 |
| H | network | 1271 | 1226 | 45 | 0.9646 |
| H | structuring | 1039 | 803 | 236 | 0.7729 |
| I | agent | 3835 | 3570 | 265 | 0.9309 |
| I | network | 1271 | 285 | 986 | 0.2242 |
| I | structuring | 1039 | 565 | 474 | 0.5438 |
| J | agent | 3835 | 3585 | 250 | 0.9348 |
| J | network | 1271 | 1197 | 74 | 0.9418 |
| J | structuring | 1039 | 1034 | 5 | 0.9952 |




| Ablation | Family | Support | TP | FN | Recall |
| --- | --- | --- | --- | --- | --- |
| A | A1 | 2745 | 2689 | 56 | 0.9796 |
| A | A2 | 930 | 814 | 116 | 0.8753 |
| A | A3 | 485 | 481 | 4 | 0.9918 |
| A | A4 | 337 | 249 | 88 | 0.7389 |
| A | N1 | 316 | 301 | 15 | 0.9525 |
| A | N2 | 736 | 708 | 28 | 0.9620 |
| A | N3 | 41 | 22 | 19 | 0.5366 |
| A | N4 | 247 | 241 | 6 | 0.9757 |
| A | S1 | 276 | 273 | 3 | 0.9891 |
| A | S2 | 1 | 1 | 0 | 1.0000 |
| A | S3 | 814 | 814 | 0 | 1.0000 |
| A | S4 | 8 | 6 | 2 | 0.7500 |
| B | A1 | 2745 | 1057 | 1688 | 0.3851 |
| B | A2 | 930 | 800 | 130 | 0.8602 |
| B | A3 | 485 | 485 | 0 | 1.0000 |
| B | A4 | 337 | 234 | 103 | 0.6944 |
| B | N1 | 316 | 301 | 15 | 0.9525 |
| B | N2 | 736 | 707 | 29 | 0.9606 |
| B | N3 | 41 | 28 | 13 | 0.6829 |
| B | N4 | 247 | 240 | 7 | 0.9717 |
| B | S1 | 276 | 274 | 2 | 0.9928 |
| B | S2 | 1 | 1 | 0 | 1.0000 |
| B | S3 | 814 | 814 | 0 | 1.0000 |
| B | S4 | 8 | 2 | 6 | 0.2500 |
| C | A1 | 2745 | 1447 | 1298 | 0.5271 |
| C | A2 | 930 | 858 | 72 | 0.9226 |
| C | A3 | 485 | 485 | 0 | 1.0000 |
| C | A4 | 337 | 288 | 49 | 0.8546 |
| C | N1 | 316 | 302 | 14 | 0.9557 |
| C | N2 | 736 | 705 | 31 | 0.9579 |
| C | N3 | 41 | 30 | 11 | 0.7317 |
| C | N4 | 247 | 240 | 7 | 0.9717 |
| C | S1 | 276 | 274 | 2 | 0.9928 |
| C | S2 | 1 | 1 | 0 | 1.0000 |
| C | S3 | 814 | 814 | 0 | 1.0000 |
| C | S4 | 8 | 6 | 2 | 0.7500 |
| D | A1 | 2745 | 652 | 2093 | 0.2375 |
| D | A2 | 930 | 637 | 293 | 0.6849 |
| D | A3 | 485 | 162 | 323 | 0.3340 |
| D | A4 | 337 | 120 | 217 | 0.3561 |
| D | N1 | 316 | 304 | 12 | 0.9620 |
| D | N2 | 736 | 707 | 29 | 0.9606 |
| D | N3 | 41 | 30 | 11 | 0.7317 |
| D | N4 | 247 | 242 | 5 | 0.9798 |
| D | S1 | 276 | 274 | 2 | 0.9928 |
| D | S2 | 1 | 1 | 0 | 1.0000 |
| D | S3 | 814 | 814 | 0 | 1.0000 |
| D | S4 | 8 | 1 | 7 | 0.1250 |
| E | A1 | 2745 | 2687 | 58 | 0.9789 |
| E | A2 | 930 | 809 | 121 | 0.8699 |
| E | A3 | 485 | 485 | 0 | 1.0000 |
| E | A4 | 337 | 248 | 89 | 0.7359 |
| E | N1 | 316 | 77 | 239 | 0.2437 |
| E | N2 | 736 | 579 | 157 | 0.7867 |
| E | N3 | 41 | 7 | 34 | 0.1707 |
| E | N4 | 247 | 108 | 139 | 0.4372 |
| E | S1 | 276 | 274 | 2 | 0.9928 |
| E | S2 | 1 | 1 | 0 | 1.0000 |
| E | S3 | 814 | 814 | 0 | 1.0000 |
| E | S4 | 8 | 6 | 2 | 0.7500 |
| F | A1 | 2745 | 2690 | 55 | 0.9800 |
| F | A2 | 930 | 808 | 122 | 0.8688 |
| F | A3 | 485 | 483 | 2 | 0.9959 |
| F | A4 | 337 | 246 | 91 | 0.7300 |
| F | N1 | 316 | 303 | 13 | 0.9589 |
| F | N2 | 736 | 709 | 27 | 0.9633 |
| F | N3 | 41 | 27 | 14 | 0.6585 |
| F | N4 | 247 | 238 | 9 | 0.9636 |
| F | S1 | 276 | 250 | 26 | 0.9058 |
| F | S2 | 1 | 1 | 0 | 1.0000 |
| F | S3 | 814 | 709 | 105 | 0.8710 |
| F | S4 | 8 | 6 | 2 | 0.7500 |
| G | A1 | 2745 | 448 | 2297 | 0.1632 |
| G | A2 | 930 | 606 | 324 | 0.6516 |
| G | A3 | 485 | 117 | 368 | 0.2412 |
| G | A4 | 337 | 92 | 245 | 0.2730 |
| G | N1 | 316 | 42 | 274 | 0.1329 |
| G | N2 | 736 | 593 | 143 | 0.8057 |
| G | N3 | 41 | 4 | 37 | 0.0976 |
| G | N4 | 247 | 85 | 162 | 0.3441 |
| G | S1 | 276 | 276 | 0 | 1.0000 |
| G | S2 | 1 | 1 | 0 | 1.0000 |
| G | S3 | 814 | 814 | 0 | 1.0000 |
| G | S4 | 8 | 1 | 7 | 0.1250 |
| H | A1 | 2745 | 524 | 2221 | 0.1909 |
| H | A2 | 930 | 467 | 463 | 0.5022 |
| H | A3 | 485 | 130 | 355 | 0.2680 |
| H | A4 | 337 | 80 | 257 | 0.2374 |
| H | N1 | 316 | 310 | 6 | 0.9810 |
| H | N2 | 736 | 704 | 32 | 0.9565 |
| H | N3 | 41 | 35 | 6 | 0.8537 |
| H | N4 | 247 | 246 | 1 | 0.9960 |
| H | S1 | 276 | 186 | 90 | 0.6739 |
| H | S2 | 1 | 0 | 1 | 0.0000 |
| H | S3 | 814 | 663 | 151 | 0.8145 |
| H | S4 | 8 | 4 | 4 | 0.5000 |
| I | A1 | 2745 | 2680 | 65 | 0.9763 |
| I | A2 | 930 | 808 | 122 | 0.8688 |
| I | A3 | 485 | 481 | 4 | 0.9918 |
| I | A4 | 337 | 251 | 86 | 0.7448 |
| I | N1 | 316 | 58 | 258 | 0.1835 |
| I | N2 | 736 | 177 | 559 | 0.2405 |
| I | N3 | 41 | 5 | 36 | 0.1220 |
| I | N4 | 247 | 56 | 191 | 0.2267 |
| I | S1 | 276 | 206 | 70 | 0.7464 |
| I | S2 | 1 | 1 | 0 | 1.0000 |
| I | S3 | 814 | 399 | 415 | 0.4902 |
| I | S4 | 8 | 6 | 2 | 0.7500 |
| J | A1 | 2745 | 2689 | 56 | 0.9796 |
| J | A2 | 930 | 822 | 108 | 0.8839 |
| J | A3 | 485 | 481 | 4 | 0.9918 |
| J | A4 | 337 | 247 | 90 | 0.7329 |
| J | N1 | 316 | 309 | 7 | 0.9778 |
| J | N2 | 736 | 694 | 42 | 0.9429 |
| J | N3 | 41 | 22 | 19 | 0.5366 |
| J | N4 | 247 | 241 | 6 | 0.9757 |
| J | S1 | 276 | 273 | 3 | 0.9891 |
| J | S2 | 1 | 1 | 0 | 1.0000 |
| J | S3 | 814 | 814 | 0 | 1.0000 |
| J | S4 | 8 | 6 | 2 | 0.7500 |


### Validation normal false positives

Denominators include target 0 only. Legitimate-origin target 1 is not a false positive under the frozen experiment. Families/domains can overlap; normal categories below are disjoint.



| Ablation | Category | Support | FP | TN | FPR |
| --- | --- | --- | --- | --- | --- |
| A | H1 | 238 | 39 | 199 | 0.1639 |
| A | H2 | 374 | 19 | 355 | 0.0508 |
| A | H3 | 406 | 15 | 391 | 0.0369 |
| A | H4 | 292 | 14 | 278 | 0.0479 |
| A | H5 | 214 | 21 | 193 | 0.0981 |
| A | H6 | 424 | 6 | 418 | 0.0142 |
| A | H7 | 359 | 2 | 357 | 0.0056 |
| A | H8 | 460 | 15 | 445 | 0.0326 |
| A | campaign_member_target0 | 1796 | 99 | 1697 | 0.0551 |
| A | routine | 5382 | 83 | 5299 | 0.0154 |
| B | H1 | 238 | 44 | 194 | 0.1849 |
| B | H2 | 374 | 26 | 348 | 0.0695 |
| B | H3 | 406 | 20 | 386 | 0.0493 |
| B | H4 | 292 | 27 | 265 | 0.0925 |
| B | H5 | 214 | 25 | 189 | 0.1168 |
| B | H6 | 424 | 12 | 412 | 0.0283 |
| B | H7 | 359 | 18 | 341 | 0.0501 |
| B | H8 | 460 | 8 | 452 | 0.0174 |
| B | campaign_member_target0 | 1796 | 112 | 1684 | 0.0624 |
| B | routine | 5382 | 88 | 5294 | 0.0164 |
| C | H1 | 238 | 60 | 178 | 0.2521 |
| C | H2 | 374 | 44 | 330 | 0.1176 |
| C | H3 | 406 | 38 | 368 | 0.0936 |
| C | H4 | 292 | 64 | 228 | 0.2192 |
| C | H5 | 214 | 27 | 187 | 0.1262 |
| C | H6 | 424 | 56 | 368 | 0.1321 |
| C | H7 | 359 | 60 | 299 | 0.1671 |
| C | H8 | 460 | 66 | 394 | 0.1435 |
| C | campaign_member_target0 | 1796 | 292 | 1504 | 0.1626 |
| C | routine | 5382 | 302 | 5080 | 0.0561 |
| D | H1 | 238 | 65 | 173 | 0.2731 |
| D | H2 | 374 | 44 | 330 | 0.1176 |
| D | H3 | 406 | 48 | 358 | 0.1182 |
| D | H4 | 292 | 50 | 242 | 0.1712 |
| D | H5 | 214 | 38 | 176 | 0.1776 |
| D | H6 | 424 | 55 | 369 | 0.1297 |
| D | H7 | 359 | 19 | 340 | 0.0529 |
| D | H8 | 460 | 25 | 435 | 0.0543 |
| D | campaign_member_target0 | 1796 | 223 | 1573 | 0.1242 |
| D | routine | 5382 | 175 | 5207 | 0.0325 |
| E | H1 | 238 | 41 | 197 | 0.1723 |
| E | H2 | 374 | 28 | 346 | 0.0749 |
| E | H3 | 406 | 21 | 385 | 0.0517 |
| E | H4 | 292 | 11 | 281 | 0.0377 |
| E | H5 | 214 | 28 | 186 | 0.1308 |
| E | H6 | 424 | 6 | 418 | 0.0142 |
| E | H7 | 359 | 2 | 357 | 0.0056 |
| E | H8 | 460 | 18 | 442 | 0.0391 |
| E | campaign_member_target0 | 1796 | 117 | 1679 | 0.0651 |
| E | routine | 5382 | 98 | 5284 | 0.0182 |
| F | H1 | 238 | 41 | 197 | 0.1723 |
| F | H2 | 374 | 43 | 331 | 0.1150 |
| F | H3 | 406 | 21 | 385 | 0.0517 |
| F | H4 | 292 | 18 | 274 | 0.0616 |
| F | H5 | 214 | 26 | 188 | 0.1215 |
| F | H6 | 424 | 9 | 415 | 0.0212 |
| F | H7 | 359 | 3 | 356 | 0.0084 |
| F | H8 | 460 | 17 | 443 | 0.0370 |
| F | campaign_member_target0 | 1796 | 133 | 1663 | 0.0741 |
| F | routine | 5382 | 98 | 5284 | 0.0182 |
| G | H1 | 238 | 81 | 157 | 0.3403 |
| G | H2 | 374 | 63 | 311 | 0.1684 |
| G | H3 | 406 | 52 | 354 | 0.1281 |
| G | H4 | 292 | 22 | 270 | 0.0753 |
| G | H5 | 214 | 37 | 177 | 0.1729 |
| G | H6 | 424 | 40 | 384 | 0.0943 |
| G | H7 | 359 | 15 | 344 | 0.0418 |
| G | H8 | 460 | 17 | 443 | 0.0370 |
| G | campaign_member_target0 | 1796 | 214 | 1582 | 0.1192 |
| G | routine | 5382 | 102 | 5280 | 0.0190 |
| H | H1 | 238 | 45 | 193 | 0.1891 |
| H | H2 | 374 | 72 | 302 | 0.1925 |
| H | H3 | 406 | 49 | 357 | 0.1207 |
| H | H4 | 292 | 39 | 253 | 0.1336 |
| H | H5 | 214 | 34 | 180 | 0.1589 |
| H | H6 | 424 | 23 | 401 | 0.0542 |
| H | H7 | 359 | 9 | 350 | 0.0251 |
| H | H8 | 460 | 19 | 441 | 0.0413 |
| H | campaign_member_target0 | 1796 | 197 | 1599 | 0.1097 |
| H | routine | 5382 | 162 | 5220 | 0.0301 |
| I | H1 | 238 | 25 | 213 | 0.1050 |
| I | H2 | 374 | 24 | 350 | 0.0642 |
| I | H3 | 406 | 11 | 395 | 0.0271 |
| I | H4 | 292 | 8 | 284 | 0.0274 |
| I | H5 | 214 | 11 | 203 | 0.0514 |
| I | H6 | 424 | 17 | 407 | 0.0401 |
| I | H7 | 359 | 8 | 351 | 0.0223 |
| I | H8 | 460 | 22 | 438 | 0.0478 |
| I | campaign_member_target0 | 1796 | 109 | 1687 | 0.0607 |
| I | routine | 5382 | 107 | 5275 | 0.0199 |
| J | H1 | 238 | 48 | 190 | 0.2017 |
| J | H2 | 374 | 20 | 354 | 0.0535 |
| J | H3 | 406 | 15 | 391 | 0.0369 |
| J | H4 | 292 | 13 | 279 | 0.0445 |
| J | H5 | 214 | 14 | 200 | 0.0654 |
| J | H6 | 424 | 5 | 419 | 0.0118 |
| J | H7 | 359 | 2 | 357 | 0.0056 |
| J | H8 | 460 | 15 | 445 | 0.0326 |
| J | campaign_member_target0 | 1796 | 122 | 1674 | 0.0679 |
| J | routine | 5382 | 88 | 5294 | 0.0164 |


## 3. Quantified feature dependence

Index=max(0, declines in Validation Macro F1, suspicious recall, suspicious F1, AP, increase in FPR). LOW <.02; MODERATE [.02,.05); HIGH [.05,.15); EXTREME >=.15. Deltas are removed minus full; rare-slice deltas reported separately.

These thresholds were saved before fitting and were not revised after results. They measure performance sensitivity to retraining with a feature removed, not causal importance. A correlated substitute or a change in optimization can affect the result.



| Removal | Index | Classification |
| --- | --- | --- |
| B | 0.3187 | EXTREME |
| C | 0.2243 | EXTREME |
| D | 0.4556 | EXTREME |
| E | 0.0944 | HIGH |
| F | 0.0216 | MODERATE |
| G | 0.5956 | EXTREME |
| H | 0.5292 | EXTREME |
| I | 0.2146 | EXTREME |
| J | 0.0029 | LOW |




| Growth-removal metric | B minus A |
| --- | --- |
| average_precision | -0.1111 |
| false_positive_rate | 0.0067 |
| macro_f1 | -0.1418 |
| roc_auc | -0.0790 |
| suspicious_f1 | -0.2077 |
| suspicious_precision | -0.0466 |
| suspicious_recall | -0.3187 |




| Domain recall | B minus A |
| --- | --- |
| agent | -0.4214 |
| network | 0.0031 |
| structuring | -0.0029 |




| Family recall | B minus A |
| --- | --- |
| A1 | -0.5945 |
| A2 | -0.0151 |
| A3 | 0.0082 |
| A4 | -0.0445 |
| N1 | 0.0000 |
| N2 | -0.0014 |
| N3 | 0.1463 |
| N4 | -0.0040 |
| S1 | 0.0036 |
| S2 | 0.0000 |
| S3 | 0.0000 |
| S4 | -0.5000 |




| Normal FPR | B minus A |
| --- | --- |
| H1 | 0.0210 |
| H2 | 0.0187 |
| H3 | 0.0123 |
| H4 | 0.0445 |
| H5 | 0.0187 |
| H6 | 0.0142 |
| H7 | 0.0446 |
| H8 | -0.0152 |
| campaign_member_target0 | 0.0072 |
| routine | 0.0009 |


The single-feature removal index is driven by the **0.3187 recall loss**. Removing the whole agent domain is still more damaging. Removing network features also hurts, while removing coverage alone has a much smaller aggregate effect. C has similar Macro F1 to B but a different recall/FPR tradeoff; removing an additional correlated feature need not monotonically worsen every metric. Neither result changes the frozen feature set.

## 4. Agent novelty distribution shift

Summaries exclude -1. Missing and available fractions use all rows in each slice.



| Partition | Slice | N | Available | Missing rate | Mean | Median | SD | Q05 | Q25 | Q75 | Q95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| train | A1_positive | 11476 | 11040 | 0.0380 | 0.9030 | 0.9130 | 0.0819 | 0.7500 | 0.8529 | 0.9688 | 1.0000 |
| train | A2_positive | 3770 | 3679 | 0.0241 | 0.8641 | 0.8696 | 0.0994 | 0.6757 | 0.8000 | 0.9375 | 1.0000 |
| train | H7_target0 | 1475 | 663 | 0.5505 | 0.8640 | 0.8750 | 0.0955 | 0.7143 | 0.8077 | 0.9286 | 1.0000 |
| train | H8_target0 | 1677 | 743 | 0.5569 | 0.8449 | 0.8462 | 0.1025 | 0.6667 | 0.7727 | 0.9286 | 1.0000 |
| train | overall | 60000 | 36943 | 0.3843 | 0.8718 | 0.8750 | 0.0995 | 0.6957 | 0.8077 | 0.9500 | 1.0000 |
| train | routine_target0 | 21407 | 11311 | 0.4716 | 0.8641 | 0.8636 | 0.1066 | 0.6804 | 0.8000 | 0.9545 | 1.0000 |
| train | target_0 | 39781 | 20370 | 0.4879 | 0.8608 | 0.8571 | 0.1045 | 0.6800 | 0.7931 | 0.9412 | 1.0000 |
| train | target_1 | 20219 | 16573 | 0.1803 | 0.8852 | 0.8929 | 0.0914 | 0.7177 | 0.8293 | 0.9545 | 1.0000 |
| validation | A1_positive | 2745 | 2648 | 0.0353 | 0.7492 | 0.7500 | 0.1339 | 0.5429 | 0.6333 | 0.8571 | 1.0000 |
| validation | A2_positive | 930 | 904 | 0.0280 | 0.5932 | 0.5652 | 0.1984 | 0.2963 | 0.4615 | 0.7500 | 0.9375 |
| validation | H7_target0 | 359 | 153 | 0.5738 | 0.6678 | 0.6316 | 0.1595 | 0.4443 | 0.5556 | 0.8000 | 1.0000 |
| validation | H8_target0 | 460 | 217 | 0.5283 | 0.5557 | 0.5556 | 0.1617 | 0.2857 | 0.4500 | 0.6842 | 0.8000 |
| validation | overall | 15000 | 9306 | 0.3796 | 0.6395 | 0.6286 | 0.1919 | 0.3333 | 0.5000 | 0.7778 | 1.0000 |
| validation | routine_target0 | 5382 | 2956 | 0.4508 | 0.6067 | 0.5882 | 0.2018 | 0.3125 | 0.4615 | 0.7391 | 1.0000 |
| validation | target_0 | 9945 | 5192 | 0.4779 | 0.6067 | 0.5909 | 0.1955 | 0.3158 | 0.4667 | 0.7273 | 1.0000 |
| validation | target_1 | 5055 | 4114 | 0.1862 | 0.6809 | 0.6842 | 0.1788 | 0.3571 | 0.5625 | 0.8235 | 1.0000 |




| Disjoint standardization | Composition | Within stratum | Unmatched strata | Total observed mean shift |
| --- | --- | --- | --- | --- |
| origin_scenario_target | 0.0002 | -0.2324 | 0.0000 | -0.2322 |
| target | -0.0002 | -0.2321 | 0.0000 | -0.2322 |


The observed novelty shift remains after class and disjoint origin/scenario/target composition standardization. Available-only weights are used, so this decomposition does not mix sentinels with measurements. Family slices A1/A2 overlap and are not summed. Similar overall missing rates cannot explain the large observed-value shift; the displayed within-slice comparisons support a broad partition difference in observed novelty, with smaller composition/availability contributions. This does not identify the generator mechanism or establish future-population transportability. The two-feature removal C gives a bounded sensitivity check, not a novelty-only causal estimate.

## 5. Missingness audit

Eleven indicator columns are derived only from documented markers: -1 for nonnegative unavailable quantities, -3 for signed changes. Valid -1 cash skews and changes remain observed. These diagnostic indicators never enter the official representation.

### Train missingness



| Feature | Marker | Missing count (all) | overall rate | target_0 rate | target_1 rate | structuring rate | network rate | agent rate | routine rate | H1 rate | H2 rate | H3 rate | H4 rate | H5 rate | H6 rate | H7 rate | H8 rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agent_cash_value_skew_change | -3 | 21998 | 0.3666 | 0.4713 | 0.1607 | 0.2699 | 0.5215 | 0.0133 | 0.4540 | 0.5274 | 0.4870 | 0.5155 | 0.4778 | 0.4734 | 0.5241 | 0.5383 | 0.5349 |
| agent_new_wallet_share_7d | -1 | 23057 | 0.3843 | 0.4879 | 0.1803 | 0.2851 | 0.5350 | 0.0353 | 0.4716 | 0.5536 | 0.4949 | 0.5192 | 0.4939 | 0.4715 | 0.5278 | 0.5505 | 0.5569 |
| agent_service_acceleration_1h | -1 | 21693 | 0.3615 | 0.4676 | 0.1529 | 0.2659 | 0.5191 | 0.0040 | 0.4493 | 0.5274 | 0.4804 | 0.5137 | 0.4762 | 0.4677 | 0.5119 | 0.5383 | 0.5349 |
| agent_top2_share_change_24h | -3 | 23014 | 0.3836 | 0.4860 | 0.1820 | 0.2839 | 0.5324 | 0.0386 | 0.4709 | 0.5393 | 0.5022 | 0.5344 | 0.4778 | 0.4962 | 0.5381 | 0.5410 | 0.5367 |
| agent_wallet_growth_ratio_7d | -1 | 23057 | 0.3843 | 0.4879 | 0.1803 | 0.2851 | 0.5350 | 0.0353 | 0.4716 | 0.5536 | 0.4949 | 0.5192 | 0.4939 | 0.4715 | 0.5278 | 0.5505 | 0.5569 |
| current_return_amount_ratio | -1 | 58858 | 0.9810 | 0.9825 | 0.9779 | 0.9773 | 0.9440 | 0.9864 | 0.9957 | 0.9988 | 0.9957 | 0.9976 | 0.9976 | 0.9753 | 0.8395 | 0.9953 | 0.9934 |
| receiver_inflow_acceleration_24h | -1 | 14726 | 0.2454 | 0.3073 | 0.1237 | 0.0965 | 0.1758 | 0.1038 | 0.2777 | 0.4452 | 0.2826 | 0.3299 | 0.3654 | 0.3529 | 0.3087 | 0.2617 | 0.3268 |
| sender_outflow_acceleration_24h | -1 | 17046 | 0.2841 | 0.3432 | 0.1679 | 0.1250 | 0.1748 | 0.1538 | 0.3210 | 0.4786 | 0.2906 | 0.3457 | 0.3864 | 0.4070 | 0.3551 | 0.3207 | 0.3626 |
| wallet_count_acceleration_1h | -1 | 10149 | 0.1691 | 0.2357 | 0.0382 | 0.0028 | 0.1174 | 0.0111 | 0.2013 | 0.3893 | 0.2181 | 0.2903 | 0.2870 | 0.2951 | 0.2379 | 0.2014 | 0.2606 |
| wallet_observed_onward_funding_share_24h | -1 | 31696 | 0.5283 | 0.5519 | 0.4817 | 0.5095 | 0.5599 | 0.4557 | 0.6061 | 0.5452 | 0.6000 | 0.6251 | 0.3646 | 0.2334 | 0.2929 | 0.6305 | 0.6219 |
| wallet_prior_funding_age_hours | -1 | 46936 | 0.7823 | 0.8016 | 0.7443 | 0.7161 | 0.5599 | 0.7863 | 0.8399 | 0.8512 | 0.8348 | 0.8588 | 0.7009 | 0.6423 | 0.5387 | 0.8244 | 0.8396 |


### Validation missingness



| Feature | Marker | Missing count (all) | overall rate | target_0 rate | target_1 rate | structuring rate | network rate | agent rate | routine rate | H1 rate | H2 rate | H3 rate | H4 rate | H5 rate | H6 rate | H7 rate | H8 rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agent_cash_value_skew_change | -3 | 5478 | 0.3652 | 0.4635 | 0.1717 | 0.2839 | 0.5547 | 0.0190 | 0.4300 | 0.6261 | 0.5455 | 0.5296 | 0.3767 | 0.6402 | 0.5165 | 0.5822 | 0.5000 |
| agent_new_wallet_share_7d | -1 | 5694 | 0.3796 | 0.4779 | 0.1862 | 0.2926 | 0.5633 | 0.0349 | 0.4508 | 0.6261 | 0.5455 | 0.5369 | 0.3801 | 0.6402 | 0.5165 | 0.5738 | 0.5283 |
| agent_service_acceleration_1h | -1 | 5350 | 0.3567 | 0.4580 | 0.1573 | 0.2685 | 0.5476 | 0.0010 | 0.4257 | 0.6261 | 0.5187 | 0.5296 | 0.3664 | 0.6121 | 0.5165 | 0.5766 | 0.5000 |
| agent_top2_share_change_24h | -3 | 5714 | 0.3809 | 0.4766 | 0.1927 | 0.3013 | 0.5625 | 0.0449 | 0.4431 | 0.6261 | 0.5936 | 0.5296 | 0.3767 | 0.6402 | 0.5165 | 0.5933 | 0.5043 |
| agent_wallet_growth_ratio_7d | -1 | 5694 | 0.3796 | 0.4779 | 0.1862 | 0.2926 | 0.5633 | 0.0349 | 0.4508 | 0.6261 | 0.5455 | 0.5369 | 0.3801 | 0.6402 | 0.5165 | 0.5738 | 0.5283 |
| current_return_amount_ratio | -1 | 14515 | 0.9677 | 0.9686 | 0.9658 | 0.9769 | 0.9158 | 0.9797 | 0.9840 | 0.9832 | 0.9813 | 0.9803 | 0.9897 | 0.9252 | 0.8160 | 0.9861 | 0.9848 |
| receiver_inflow_acceleration_24h | -1 | 3620 | 0.2413 | 0.2988 | 0.1282 | 0.0895 | 0.1998 | 0.1030 | 0.2497 | 0.5462 | 0.3476 | 0.3670 | 0.2158 | 0.4860 | 0.3467 | 0.3064 | 0.3391 |
| sender_outflow_acceleration_24h | -1 | 4207 | 0.2805 | 0.3370 | 0.1693 | 0.1367 | 0.1873 | 0.1528 | 0.3068 | 0.5882 | 0.3155 | 0.3621 | 0.3082 | 0.5093 | 0.3892 | 0.3343 | 0.3739 |
| wallet_count_acceleration_1h | -1 | 2528 | 0.1685 | 0.2315 | 0.0447 | 0.0000 | 0.1393 | 0.0136 | 0.1789 | 0.5336 | 0.2834 | 0.3103 | 0.1473 | 0.4159 | 0.2736 | 0.2340 | 0.2848 |
| wallet_observed_onward_funding_share_24h | -1 | 7976 | 0.5317 | 0.5568 | 0.4825 | 0.5274 | 0.5547 | 0.4600 | 0.6063 | 0.5042 | 0.6444 | 0.6207 | 0.3870 | 0.2383 | 0.3208 | 0.5961 | 0.6043 |
| wallet_prior_funding_age_hours | -1 | 11786 | 0.7857 | 0.8066 | 0.7446 | 0.7507 | 0.5547 | 0.7904 | 0.8449 | 0.7689 | 0.8663 | 0.8596 | 0.7226 | 0.5841 | 0.5519 | 0.8106 | 0.8522 |


Every slice support, missing count and available count is retained in `stage12_missingness_audit.json`; the rate tables do not hide zero-support slices.



| Model | Partition | Macro F1 | Precision 1 | Recall 1 | F1 1 | AP | ROC-AUC | FPR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Missingness only | train | 0.5383 | 0.5346 | 0.1990 | 0.2901 | 0.4728 | 0.6924 | 0.0881 |
| Missingness only | validation | 0.5372 | 0.5340 | 0.1970 | 0.2879 | 0.4644 | 0.6828 | 0.0874 |


Strong if Validation ROC-AUC >=.80 AND Macro F1 >=.70; moderate if ROC-AUC >=.70 OR Macro F1 >=.65; otherwise low. Descriptive heuristic, not proof of generator causality. The observed flag is **LOW**. The model is a small unweighted HGB (100 iterations, depth 3, seven leaves, minimum leaf 30, L2=2). Its above-chance ranking shows some coverage association, but it cannot reproduce the reference. This finite diagnostic does not rule out nonlinear interactions between missingness and observed values, nor every generator shortcut.

## 6. Univariate and tiny-feature diagnostics

Ranking is frozen Stage 11 absolute permutation-AP importance; Stage 12 results did not choose the subsets. The first five are:

1. `agent_wallet_growth_ratio_7d`
2. `agent_service_acceleration_1h`
3. `wallet_observed_onward_funding_share_24h`
4. `wallet_count_utc_day_inclusive`
5. `agent_top2_count_share_24h`



| Top N | Partition | Macro F1 | Precision 1 | Recall 1 | F1 1 | AP | ROC-AUC | FPR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | train | 0.7991 | 0.9855 | 0.5470 | 0.7035 | 0.7876 | 0.8084 | 0.0041 |
| 1 | validation | 0.7879 | 0.9576 | 0.5359 | 0.6872 | 0.7582 | 0.7867 | 0.0121 |
| 2 | train | 0.8368 | 0.9472 | 0.6429 | 0.7660 | 0.8349 | 0.8525 | 0.0182 |
| 2 | validation | 0.8210 | 0.9101 | 0.6291 | 0.7439 | 0.8097 | 0.8325 | 0.0316 |
| 3 | train | 0.8531 | 0.9380 | 0.6850 | 0.7918 | 0.8692 | 0.8871 | 0.0230 |
| 3 | validation | 0.8367 | 0.9101 | 0.6653 | 0.7687 | 0.8434 | 0.8680 | 0.0334 |
| 5 | train | 0.9158 | 0.9332 | 0.8427 | 0.8856 | 0.9499 | 0.9606 | 0.0307 |
| 5 | validation | 0.9036 | 0.9098 | 0.8324 | 0.8694 | 0.9266 | 0.9493 | 0.0419 |


Raw AUC uses increasing values without choosing a sign. Observed AUC excludes the documented marker; encoded AUC includes it. A low raw AUC can coexist with useful nonmonotonic association. Range overlap cannot rule out a near separator.

### Train univariate diagnostics



| Feature | Observed AUC | Encoded AUC | Available N | Observed range overlap |
| --- | --- | --- | --- | --- |
| agent_wallet_growth_ratio_7d | 0.8491 | 0.8003 | 36943 | [0.16666666666666666, 3.3333333333333335] |
| agent_new_wallet_share_7d | 0.5701 | 0.6832 | 36943 | [0.3333333333333333, 1.0] |
| agent_top2_count_share_24h | 0.5309 | 0.5309 | 60000 | [0.0, 1.0] |
| agent_top2_share_change_24h | 0.4193 | 0.6181 | 36986 | [-0.16666666666666669, 0.9583333333333334] |
| current_return_path_length | 0.5022 | 0.5022 | 60000 | [0.0, 5.0] |
| wallet_observed_onward_funding_share_24h | 0.5311 | 0.5424 | 28304 | [0.0, 16738.854545454546] |
| wallet_count_1h_inclusive | 0.5936 | 0.5936 | 60000 | [1.0, 18.0] |
| wallet_value_24h_inclusive | 0.6176 | 0.6176 | 60000 | [1.0, 258875.01] |




| Feature | Target | N | Missing rate | Min | Q05 | Median | Mean | SD | Q95 | Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agent_wallet_growth_ratio_7d | 0 | 39781 | 0.4879 | 0.0606 | 0.4615 | 0.9565 | 0.9577 | 0.3013 | 1.4286 | 3.3333 |
| agent_wallet_growth_ratio_7d | 1 | 20219 | 0.1803 | 0.1667 | 0.7170 | 1.6957 | 1.9370 | 1.1867 | 4.0000 | 14.0000 |
| agent_new_wallet_share_7d | 0 | 39781 | 0.4879 | 0.0000 | 0.6800 | 0.8571 | 0.8608 | 0.1045 | 1.0000 | 1.0000 |
| agent_new_wallet_share_7d | 1 | 20219 | 0.1803 | 0.3333 | 0.7177 | 0.8929 | 0.8852 | 0.0914 | 1.0000 | 1.0000 |
| agent_top2_count_share_24h | 0 | 39781 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.4840 | 0.3833 | 1.0000 | 1.0000 |
| agent_top2_count_share_24h | 1 | 20219 | 0.0000 | 0.0000 | 0.0000 | 0.5294 | 0.5242 | 0.3255 | 1.0000 | 1.0000 |
| agent_top2_share_change_24h | 0 | 39781 | 0.4860 | -0.1667 | 0.0913 | 0.4710 | 0.4849 | 0.2561 | 0.8769 | 0.9583 |
| agent_top2_share_change_24h | 1 | 20219 | 0.1820 | -0.5526 | -0.0312 | 0.4127 | 0.4023 | 0.2704 | 0.8378 | 0.9608 |
| current_return_path_length | 0 | 39781 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0397 | 0.3431 | 0.0000 | 5.0000 |
| current_return_path_length | 1 | 20219 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0417 | 0.3288 | 0.0000 | 5.0000 |
| wallet_observed_onward_funding_share_24h | 0 | 39781 | 0.5519 | 0.0000 | 0.0000 | 0.0000 | 40.1341 | 338.2119 | 103.0066 | 16738.8545 |
| wallet_observed_onward_funding_share_24h | 1 | 20219 | 0.4817 | 0.0000 | 0.0000 | 0.0000 | 62.7009 | 547.5664 | 111.9734 | 17374.3600 |
| wallet_count_1h_inclusive | 0 | 39781 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.1554 | 0.7144 | 2.0000 | 18.0000 |
| wallet_count_1h_inclusive | 1 | 20219 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.9693 | 2.4187 | 7.0000 | 23.0000 |
| wallet_value_24h_inclusive | 0 | 39781 | 0.0000 | 1.0000 | 13.0000 | 608.4900 | 7068.4251 | 11967.3212 | 27446.2700 | 258875.0100 |
| wallet_value_24h_inclusive | 1 | 20219 | 0.0000 | 1.0000 | 20.8770 | 5638.2600 | 15353.3644 | 26985.0210 | 56008.2920 | 455916.2000 |


### Validation univariate diagnostics



| Feature | Observed AUC | Encoded AUC | Available N | Observed range overlap |
| --- | --- | --- | --- | --- |
| agent_wallet_growth_ratio_7d | 0.8302 | 0.7862 | 9306 | [0.19047619047619047, 3.142857142857143] |
| agent_new_wallet_share_7d | 0.6212 | 0.6974 | 9306 | [0.12, 1.0] |
| agent_top2_count_share_24h | 0.5122 | 0.5122 | 15000 | [0.0, 1.0] |
| agent_top2_share_change_24h | 0.4033 | 0.6011 | 9286 | [-0.19385342789598115, 0.9375] |
| current_return_path_length | 0.5013 | 0.5013 | 15000 | [0.0, 5.0] |
| wallet_observed_onward_funding_share_24h | 0.5380 | 0.5458 | 7024 | [0.0, 10859.405940594059] |
| wallet_count_1h_inclusive | 0.5911 | 0.5911 | 15000 | [1.0, 20.0] |
| wallet_value_24h_inclusive | 0.6144 | 0.6144 | 15000 | [1.0, 122427.08] |




| Feature | Target | N | Missing rate | Min | Q05 | Median | Mean | SD | Q95 | Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agent_wallet_growth_ratio_7d | 0 | 9945 | 0.4779 | 0.0833 | 0.5000 | 0.9831 | 0.9817 | 0.3105 | 1.4444 | 3.1429 |
| agent_wallet_growth_ratio_7d | 1 | 5055 | 0.1862 | 0.1905 | 0.6842 | 1.6923 | 1.8221 | 1.0189 | 3.4377 | 11.0000 |
| agent_new_wallet_share_7d | 0 | 9945 | 0.4779 | 0.0000 | 0.3158 | 0.5909 | 0.6067 | 0.1955 | 1.0000 | 1.0000 |
| agent_new_wallet_share_7d | 1 | 5055 | 0.1862 | 0.1200 | 0.3571 | 0.6842 | 0.6809 | 0.1788 | 1.0000 | 1.0000 |
| agent_top2_count_share_24h | 0 | 9945 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.4975 | 0.3838 | 1.0000 | 1.0000 |
| agent_top2_count_share_24h | 1 | 5055 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.5164 | 0.3241 | 1.0000 | 1.0000 |
| agent_top2_share_change_24h | 0 | 9945 | 0.4766 | -0.1939 | 0.0968 | 0.4575 | 0.4779 | 0.2482 | 0.8629 | 0.9375 |
| agent_top2_share_change_24h | 1 | 5055 | 0.1927 | -0.4247 | -0.0380 | 0.3857 | 0.3816 | 0.2763 | 0.8333 | 0.9388 |
| current_return_path_length | 0 | 9945 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0736 | 0.4632 | 0.0000 | 5.0000 |
| current_return_path_length | 1 | 5055 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0684 | 0.4262 | 0.0000 | 5.0000 |
| wallet_observed_onward_funding_share_24h | 0 | 9945 | 0.5568 | 0.0000 | 0.0000 | 0.0000 | 45.2899 | 318.5405 | 119.9988 | 10859.4059 |
| wallet_observed_onward_funding_share_24h | 1 | 5055 | 0.4825 | 0.0000 | 0.0000 | 0.0000 | 66.5347 | 444.0556 | 211.7383 | 13877.9859 |
| wallet_count_1h_inclusive | 0 | 9945 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.2151 | 1.1569 | 2.0000 | 23.0000 |
| wallet_count_1h_inclusive | 1 | 5055 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 1.8950 | 2.2509 | 7.0000 | 20.0000 |
| wallet_value_24h_inclusive | 0 | 9945 | 0.0000 | 1.0000 | 11.9380 | 582.1500 | 7110.8188 | 12194.8647 | 28187.1600 | 122427.0800 |
| wallet_value_24h_inclusive | 1 | 5055 | 0.0000 | 1.0000 | 21.0000 | 4741.0300 | 14527.5210 | 22127.2981 | 55834.8190 | 279894.0200 |


All 32 univariate columns and full distributions are retained in JSON. Growth alone produces substantial discrimination but falls well short of the full reference; top five also fall short. The additional features contribute materially. This is evidence of concentration plus complementary signal, not proof that each domain mechanism is independently recognized.

## 7. Domain-only versus overlapping positives

Only means no family from either other domain; multiple families within the same domain are allowed. Overlap means at least one other domain is active. These are label-evidence slices, not private campaign membership. Low-support flag is N<30.



| Ablation | Slice | Support | TP | FN | Recall | Low support |
| --- | --- | --- | --- | --- | --- | --- |
| A | agent_only | 3123 | 2867 | 256 | 0.9180 | False |
| A | agent_overlap | 712 | 712 | 0 | 1.0000 | False |
| A | network_only | 738 | 670 | 68 | 0.9079 | False |
| A | network_overlap | 533 | 533 | 0 | 1.0000 | False |
| A | structuring_only | 215 | 210 | 5 | 0.9767 | False |
| A | structuring_overlap | 824 | 824 | 0 | 1.0000 | False |
| B | agent_only | 3123 | 1255 | 1868 | 0.4019 | False |
| B | agent_overlap | 712 | 708 | 4 | 0.9944 | False |
| B | network_only | 738 | 674 | 64 | 0.9133 | False |
| B | network_overlap | 533 | 533 | 0 | 1.0000 | False |
| B | structuring_only | 215 | 211 | 4 | 0.9814 | False |
| B | structuring_overlap | 824 | 820 | 4 | 0.9951 | False |
| C | agent_only | 3123 | 1727 | 1396 | 0.5530 | False |
| C | agent_overlap | 712 | 712 | 0 | 1.0000 | False |
| C | network_only | 738 | 675 | 63 | 0.9146 | False |
| C | network_overlap | 533 | 533 | 0 | 1.0000 | False |
| C | structuring_only | 215 | 211 | 4 | 0.9814 | False |
| C | structuring_overlap | 824 | 824 | 0 | 1.0000 | False |
| D | agent_only | 3123 | 557 | 2566 | 0.1784 | False |
| D | agent_overlap | 712 | 707 | 5 | 0.9930 | False |
| D | network_only | 738 | 681 | 57 | 0.9228 | False |
| D | network_overlap | 533 | 533 | 0 | 1.0000 | False |
| D | structuring_only | 215 | 211 | 4 | 0.9814 | False |
| D | structuring_overlap | 824 | 819 | 5 | 0.9939 | False |
| E | agent_only | 3123 | 2866 | 257 | 0.9177 | False |
| E | agent_overlap | 712 | 707 | 5 | 0.9930 | False |
| E | network_only | 738 | 198 | 540 | 0.2683 | False |
| E | network_overlap | 533 | 528 | 5 | 0.9906 | False |
| E | structuring_only | 215 | 211 | 4 | 0.9814 | False |
| E | structuring_overlap | 824 | 824 | 0 | 1.0000 | False |
| F | agent_only | 3123 | 2878 | 245 | 0.9215 | False |
| F | agent_overlap | 712 | 695 | 17 | 0.9761 | False |
| F | network_only | 738 | 676 | 62 | 0.9160 | False |
| F | network_overlap | 533 | 532 | 1 | 0.9981 | False |
| F | structuring_only | 215 | 102 | 113 | 0.4744 | False |
| F | structuring_overlap | 824 | 806 | 18 | 0.9782 | False |
| G | agent_only | 3123 | 385 | 2738 | 0.1233 | False |
| G | agent_overlap | 712 | 619 | 93 | 0.8694 | False |
| G | network_only | 738 | 231 | 507 | 0.3130 | False |
| G | network_overlap | 533 | 445 | 88 | 0.8349 | False |
| G | structuring_only | 215 | 213 | 2 | 0.9907 | False |
| G | structuring_overlap | 824 | 819 | 5 | 0.9939 | False |
| H | agent_only | 3123 | 400 | 2723 | 0.1281 | False |
| H | agent_overlap | 712 | 565 | 147 | 0.7935 | False |
| H | network_only | 738 | 694 | 44 | 0.9404 | False |
| H | network_overlap | 533 | 532 | 1 | 0.9981 | False |
| H | structuring_only | 215 | 125 | 90 | 0.5814 | False |
| H | structuring_overlap | 824 | 678 | 146 | 0.8228 | False |
| I | agent_only | 3123 | 2906 | 217 | 0.9305 | False |
| I | agent_overlap | 712 | 664 | 48 | 0.9326 | False |
| I | network_only | 738 | 26 | 712 | 0.0352 | False |
| I | network_overlap | 533 | 259 | 274 | 0.4859 | False |
| I | structuring_only | 215 | 32 | 183 | 0.1488 | False |
| I | structuring_overlap | 824 | 533 | 291 | 0.6468 | False |
| J | agent_only | 3123 | 2873 | 250 | 0.9199 | False |
| J | agent_overlap | 712 | 712 | 0 | 1.0000 | False |
| J | network_only | 738 | 664 | 74 | 0.8997 | False |
| J | network_overlap | 533 | 533 | 0 | 1.0000 | False |
| J | structuring_only | 215 | 210 | 5 | 0.9767 | False |
| J | structuring_overlap | 824 | 824 | 0 | 1.0000 | False |


The reference recalls are **210/215 structuring-only**, **670/738 network-only**, and **2867/3123 agent-only**. Each overlap slice has recall 1.0. Thus aggregate domain recall benefits from overlap, but the reference also detects many positives unique to every domain. These supports are sufficient for descriptive comparisons under the declared rule; they do not establish independent causal signals or real-world effectiveness. Ablations show where cross-domain proxies can persist even after a domain is removed.

The domain-removal contrast is particularly informative: network-only recall falls from **0.9079 to 0.2683** without network features, structuring-only from **0.9767 to 0.4744** without structuring features, and agent-only from **0.9180 to 0.1784** without agent features. Removing growth alone reduces agent-only recall to **0.4019**, while network-only and structuring-only recall remain above 0.91 and 0.98 respectively. Aggregate overlap recall masks much of these domain-specific losses.

## 8. N3 reciprocal cycle diagnosis

Reference support **41**, TP **22**, FN **19**. TP/FN comparisons are observational diagnostics at the unchanged threshold.



| Feature | Group | Available N | Missing rate | Mean | Median | SD | Q05 | Q95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| receiver_unique_sources_24h_inclusive | TP | 22 | 0.0000 | 1.3182 | 1.0000 | 1.0611 | 1.0000 | 2.0000 |
| receiver_unique_sources_24h_inclusive | FN | 19 | 0.0000 | 1.3158 | 1.0000 | 0.4648 | 1.0000 | 2.0000 |
| receiver_inflow_count_24h_inclusive | TP | 22 | 0.0000 | 1.4091 | 1.0000 | 1.1143 | 1.0000 | 2.9500 |
| receiver_inflow_count_24h_inclusive | FN | 19 | 0.0000 | 1.4211 | 1.0000 | 0.4937 | 1.0000 | 2.0000 |
| receiver_inflow_acceleration_24h | TP | 18 | 0.1818 | 1.5000 | 1.0000 | 1.2134 | 1.0000 | 3.4500 |
| receiver_inflow_acceleration_24h | FN | 15 | 0.2105 | 1.5333 | 2.0000 | 0.4989 | 1.0000 | 2.0000 |
| sender_unique_destinations_24h_inclusive | TP | 22 | 0.0000 | 2.0455 | 1.0000 | 1.7704 | 1.0000 | 4.9500 |
| sender_unique_destinations_24h_inclusive | FN | 19 | 0.0000 | 1.4211 | 1.0000 | 0.5908 | 1.0000 | 2.1000 |
| sender_outflow_count_24h_inclusive | TP | 22 | 0.0000 | 2.3636 | 1.0000 | 2.1436 | 1.0000 | 6.0000 |
| sender_outflow_count_24h_inclusive | FN | 19 | 0.0000 | 1.5263 | 1.0000 | 0.6781 | 1.0000 | 3.0000 |
| sender_outflow_acceleration_24h | TP | 17 | 0.2273 | 2.4118 | 1.0000 | 2.1978 | 1.0000 | 6.4000 |
| sender_outflow_acceleration_24h | FN | 12 | 0.3684 | 1.4040 | 1.0000 | 0.6496 | 0.9318 | 2.4500 |
| current_return_path_length | TP | 22 | 0.0000 | 1.0455 | 1.0000 | 0.2083 | 1.0000 | 1.0000 |
| current_return_path_length | FN | 19 | 0.0000 | 1.2632 | 1.0000 | 0.5470 | 1.0000 | 2.1000 |
| current_return_amount_ratio | TP | 22 | 0.0000 | 0.6344 | 0.5577 | 0.2559 | 0.3256 | 1.0722 |
| current_return_amount_ratio | FN | 19 | 0.0000 | 0.8654 | 0.9469 | 0.6500 | 0.2292 | 1.3696 |
| wallet_observed_onward_funding_share_24h | TP | 17 | 0.2273 | 1.7164 | 0.6486 | 2.1309 | 0.2791 | 6.0444 |
| wallet_observed_onward_funding_share_24h | FN | 10 | 0.4737 | 1.2702 | 0.6521 | 1.6406 | 0.0014 | 4.4391 |
| wallet_prior_funding_age_hours | TP | 17 | 0.2273 | 4.8142 | 3.1290 | 5.1720 | 0.0431 | 16.7930 |
| wallet_prior_funding_age_hours | FN | 10 | 0.4737 | 9.9412 | 8.6283 | 6.0093 | 1.7368 | 18.8183 |
| current_amount_usd | TP | 22 | 0.0000 | 1117.7050 | 92.6950 | 2571.9171 | 11.3315 | 6476.5000 |
| current_amount_usd | FN | 19 | 0.0000 | 1720.5000 | 125.4900 | 4742.2049 | 16.2520 | 8535.0450 |
| wallet_history_coverage_days | TP | 22 | 0.0000 | 26.3818 | 28.0000 | 5.4313 | 16.8239 | 28.0000 |
| wallet_history_coverage_days | FN | 19 | 0.0000 | 25.9085 | 28.0000 | 5.2847 | 15.7067 | 28.0000 |
| receiver_history_coverage_days | TP | 22 | 0.0000 | 27.0267 | 28.0000 | 3.0941 | 18.8273 | 28.0000 |
| receiver_history_coverage_days | FN | 19 | 0.0000 | 25.9110 | 28.0000 | 5.2798 | 15.7120 | 28.0000 |
| agent_history_coverage_days | TP | 22 | 0.0000 | 18.1180 | 28.0000 | 12.7402 | 0.0000 | 28.0000 |
| agent_history_coverage_days | FN | 19 | 0.0000 | 11.0562 | 0.0000 | 13.1855 | 0.0000 | 28.0000 |




| Family overlap | Support | TP | FN | Recall |
| --- | --- | --- | --- | --- |
| A1 | 1 | 1 | 0 | 1.0000 |
| A2 | 0 | 0 | 0 | not available |
| A3 | 3 | 3 | 0 | 1.0000 |
| A4 | 0 | 0 | 0 | not available |
| N1 | 1 | 1 | 0 | 1.0000 |
| N2 | 3 | 3 | 0 | 1.0000 |
| N3 | 41 | 22 | 19 | 0.5366 |
| N4 | 4 | 4 | 0 | 1.0000 |
| S1 | 0 | 0 | 0 | not available |
| S2 | 0 | 0 | 0 | not available |
| S3 | 2 | 2 | 0 | 1.0000 |
| S4 | 0 | 0 | 0 | not available |




| Domain membership | Support | TP | FN | Recall |
| --- | --- | --- | --- | --- |
| agent_overlap | 4 | 4 | 0 | 1.0000 |
| network_only | 35 | 16 | 19 | 0.4571 |
| network_overlap | 6 | 6 | 0 | 1.0000 |
| structuring_overlap | 2 | 2 | 0 | 1.0000 |




| strength | Support | TP | FN | Recall |
| --- | --- | --- | --- | --- |
| moderate | 4 | 3 | 1 | 0.7500 |
| not recorded | 30 | 14 | 16 | 0.4667 |
| strong | 5 | 4 | 1 | 0.8000 |
| weak | 2 | 1 | 1 | 0.5000 |




| recipe | Support | TP | FN | Recall |
| --- | --- | --- | --- | --- |
| A3 | 1 | 1 | 0 | 1.0000 |
| A4 | 2 | 0 | 2 | 0.0000 |
| N1 | 1 | 1 | 0 | 1.0000 |
| N2 | 1 | 0 | 1 | 0.0000 |
| N3 | 14 | 9 | 5 | 0.6429 |
| N4 | 7 | 6 | 1 | 0.8571 |
| S1 | 1 | 0 | 1 | 0.0000 |
| S2 | 2 | 1 | 1 | 0.5000 |
| not recorded | 12 | 4 | 8 | 0.3333 |




| transaction_type | Support | TP | FN | Recall |
| --- | --- | --- | --- | --- |
| wallet_to_wallet | 41 | 22 | 19 | 0.5366 |




| diagnosed_family_onset_position | Support | TP | FN | Recall |
| --- | --- | --- | --- | --- |
| 0 | 5 | 4 | 1 | 0.8000 |
| 8 | 1 | 1 | 0 | 1.0000 |
| not recorded | 35 | 17 | 18 | 0.4857 |


Strength and recipe describe private generation provenance, not a measured causal signal. Missing provenance stays “not recorded.” Onset offsets are episode event positions relative to the recorded own-family onset and are applicable only when the private scenario family matches the diagnosed family. They are not time delays or universal cross-family onset. Per-row diagnostic values and all metadata categories are retained in JSON.



| Selected path length | Support | TP | FN | Recall |
| --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 0 | not available |
| 1 | 36 | 21 | 15 | 0.5833 |
| 2 | 4 | 1 | 3 | 0.2500 |
| 3 | 1 | 0 | 1 | 0.0000 |
| 4 | 0 | 0 | 0 | not available |
| 5 | 0 | 0 | 0 | not available |




| Coverage below 28d | Support | TP | FN | Recall |
| --- | --- | --- | --- | --- |
| receiver_history_coverage_days | 6 | 2 | 4 | 0.3333 |
| wallet_history_coverage_days | 6 | 2 | 4 | 0.3333 |


**Diagnosis:** all 41 positives have a nonzero selected path. Fifteen of 19 misses are one-edge paths; longer paths have lower observed recall, but only five examples have length two or three. Median return ratio is **0.5577 for TP versus 0.9469 for FN**. Two misses have selected ratios outside [0.25,1.25], versus none of the TPs; a selected topological path is a lossy summary and need not be the path used by the frozen predicate. This observation is consistent with compression limits, not proof of an incorrect label.

All 19 misses belong to network-only positives; all six cross-domain overlaps are detected. Only four misses have wallet coverage below 28 days, so cold history does not explain most misses. FN mean outflow count is 1.5263 versus 2.3636 for TP, whereas receiver counts are similar. FN current-amount median is $125.49 versus $92.695; extreme values make means less informative. Misses occur across recipes (five in N3, eight without a recorded recipe, six elsewhere), so no single recipe explains them. Only two examples have private weak strength and only six support a diagnosed-family onset offset: these slices are too small for stable strength/onset conclusions. Shared comparator weakness and the small Train/Validation family support motivate representation/support investigation; this stage neither proves sufficiency nor adds an oracle feature.

## 9. A4 cash imbalance diagnosis

Reference support **337**, TP **249**, FN **88**. TP/FN comparisons are observational diagnostics at the unchanged threshold.



| Feature | Group | Available N | Missing rate | Mean | Median | SD | Q05 | Q95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agent_service_count_1h_inclusive | TP | 249 | 0.0000 | 2.2771 | 2.0000 | 1.9858 | 1.0000 | 6.0000 |
| agent_service_count_1h_inclusive | FN | 88 | 0.0000 | 1.8750 | 2.0000 | 0.9748 | 1.0000 | 4.0000 |
| agent_service_acceleration_1h | TP | 249 | 0.0000 | 2.2771 | 2.0000 | 1.9858 | 1.0000 | 6.0000 |
| agent_service_acceleration_1h | FN | 87 | 0.0114 | 1.8851 | 2.0000 | 0.9759 | 1.0000 | 4.0000 |
| agent_wallet_growth_ratio_7d | TP | 245 | 0.0161 | 1.4454 | 1.2222 | 0.8287 | 0.6278 | 3.4667 |
| agent_wallet_growth_ratio_7d | FN | 87 | 0.0114 | 1.0434 | 1.0526 | 0.2395 | 0.6562 | 1.4118 |
| agent_new_wallet_share_7d | TP | 245 | 0.0161 | 0.5906 | 0.5882 | 0.1830 | 0.3000 | 0.9073 |
| agent_new_wallet_share_7d | FN | 87 | 0.0114 | 0.5774 | 0.5714 | 0.1346 | 0.3478 | 0.7212 |
| agent_top2_count_share_24h | TP | 249 | 0.0000 | 0.5125 | 0.5000 | 0.2030 | 0.2000 | 0.8333 |
| agent_top2_count_share_24h | FN | 88 | 0.0000 | 0.4522 | 0.4495 | 0.1678 | 0.2222 | 0.7143 |
| agent_top2_share_change_24h | TP | 249 | 0.0000 | 0.3155 | 0.2805 | 0.2290 | -0.0158 | 0.6753 |
| agent_top2_share_change_24h | FN | 87 | 0.0114 | 0.2812 | 0.2471 | 0.1680 | 0.0718 | 0.5848 |
| agent_cash_value_skew_24h | TP | 249 | 0.0000 | -0.1056 | -0.7561 | 0.9370 | -0.9996 | 0.9998 |
| agent_cash_value_skew_24h | FN | 88 | 0.0000 | -0.2336 | -0.9842 | 0.9380 | -1.0000 | 1.0000 |
| agent_cash_count_skew_24h | TP | 249 | 0.0000 | -0.0649 | -0.5385 | 0.6993 | -0.8000 | 0.9273 |
| agent_cash_count_skew_24h | FN | 88 | 0.0000 | -0.2313 | -0.5278 | 0.7709 | -1.0000 | 1.0000 |
| agent_cash_value_skew_change | TP | 249 | 0.0000 | -0.1317 | -0.5620 | 0.9825 | -1.3185 | 1.1672 |
| agent_cash_value_skew_change | FN | 87 | 0.0114 | -0.1787 | -0.7237 | 0.9402 | -1.2205 | 1.1700 |
| agent_history_coverage_days | TP | 249 | 0.0000 | 28.0000 | 28.0000 | 0.0000 | 28.0000 | 28.0000 |
| agent_history_coverage_days | FN | 88 | 0.0000 | 28.0000 | 28.0000 | 0.0000 | 28.0000 | 28.0000 |




| Family overlap | Support | TP | FN | Recall |
| --- | --- | --- | --- | --- |
| A1 | 86 | 85 | 1 | 0.9884 |
| A2 | 69 | 62 | 7 | 0.8986 |
| A3 | 19 | 19 | 0 | 1.0000 |
| A4 | 337 | 249 | 88 | 0.7389 |
| N1 | 0 | 0 | 0 | not available |
| N2 | 0 | 0 | 0 | not available |
| N3 | 0 | 0 | 0 | not available |
| N4 | 4 | 4 | 0 | 1.0000 |
| S1 | 6 | 6 | 0 | 1.0000 |
| S2 | 0 | 0 | 0 | not available |
| S3 | 31 | 31 | 0 | 1.0000 |
| S4 | 0 | 0 | 0 | not available |




| Domain membership | Support | TP | FN | Recall |
| --- | --- | --- | --- | --- |
| agent_only | 297 | 209 | 88 | 0.7037 |
| agent_overlap | 40 | 40 | 0 | 1.0000 |
| network_overlap | 4 | 4 | 0 | 1.0000 |
| structuring_overlap | 37 | 37 | 0 | 1.0000 |




| strength | Support | TP | FN | Recall |
| --- | --- | --- | --- | --- |
| moderate | 42 | 32 | 10 | 0.7619 |
| not recorded | 255 | 188 | 67 | 0.7373 |
| strong | 34 | 26 | 8 | 0.7647 |
| weak | 6 | 3 | 3 | 0.5000 |




| recipe | Support | TP | FN | Recall |
| --- | --- | --- | --- | --- |
| A1 | 18 | 15 | 3 | 0.8333 |
| A2 | 30 | 22 | 8 | 0.7333 |
| A3 | 7 | 7 | 0 | 1.0000 |
| A4 | 22 | 15 | 7 | 0.6818 |
| N1 | 60 | 47 | 13 | 0.7833 |
| N2 | 15 | 12 | 3 | 0.8000 |
| N3 | 11 | 7 | 4 | 0.6364 |
| N4 | 35 | 21 | 14 | 0.6000 |
| S1 | 13 | 9 | 4 | 0.6923 |
| S2 | 13 | 10 | 3 | 0.7692 |
| S3 | 26 | 22 | 4 | 0.8462 |
| S4 | 17 | 13 | 4 | 0.7647 |
| not recorded | 70 | 49 | 21 | 0.7000 |




| transaction_type | Support | TP | FN | Recall |
| --- | --- | --- | --- | --- |
| cash_in | 178 | 125 | 53 | 0.7022 |
| cash_out | 159 | 124 | 35 | 0.7799 |




| diagnosed_family_onset_position | Support | TP | FN | Recall |
| --- | --- | --- | --- | --- |
| 0 | 5 | 3 | 2 | 0.6000 |
| 12 | 1 | 1 | 0 | 1.0000 |
| 15 | 1 | 1 | 0 | 1.0000 |
| 16 | 1 | 0 | 1 | 0.0000 |
| 17 | 1 | 1 | 0 | 1.0000 |
| 2 | 1 | 1 | 0 | 1.0000 |
| 4 | 2 | 2 | 0 | 1.0000 |
| not recorded | 325 | 240 | 85 | 0.7385 |


Strength and recipe describe private generation provenance, not a measured causal signal. Missing provenance stays “not recorded.” Onset offsets are episode event positions relative to the recorded own-family onset and are applicable only when the private scenario family matches the diagnosed family. They are not time delays or universal cross-family onset. Per-row diagnostic values and all metadata categories are retained in JSON.



| Slice | Support | TP | FN | Recall |
| --- | --- | --- | --- | --- |
| missing | 1 | 0 | 1 | 0.0000 |
| observed | 336 | 249 | 87 | 0.7411 |
| other A1/A2/A3 overlap | 156 | 148 | 8 | 0.9487 |
| no other agent family | 181 | 101 | 80 | 0.5580 |




| Feature | A4 FN observed mean | H8 target-0 observed mean | A4 FN minus H8 standardized mean |
| --- | --- | --- | --- |
| agent_service_count_1h_inclusive | 1.8750 | 0.9283 | 1.0689 |
| agent_service_acceleration_1h | 1.8851 | 1.3043 | 0.7218 |
| agent_wallet_growth_ratio_7d | 1.0434 | 1.0772 | -0.1180 |
| agent_new_wallet_share_7d | 0.5774 | 0.5557 | 0.1462 |
| agent_top2_count_share_24h | 0.4522 | 0.3528 | 0.4126 |
| agent_top2_share_change_24h | 0.2812 | 0.3212 | -0.2070 |
| agent_cash_value_skew_24h | -0.2336 | -0.0432 | -0.2315 |
| agent_cash_count_skew_24h | -0.2313 | -0.0145 | -0.3351 |
| agent_cash_value_skew_change | -0.1787 | -0.1877 | 0.0099 |
| agent_history_coverage_days | 28.0000 | 17.0648 | 1.2103 |




| Group | Absolute quantity | Observed N | Mean magnitude | Median magnitude |
| --- | --- | --- | --- | --- |
| FN | agent_cash_count_skew_24h | 88 | 0.7722 | 0.7571 |
| FN | agent_cash_value_skew_24h | 88 | 0.9627 | 0.9982 |
| FN | agent_cash_value_skew_change | 87 | 0.9331 | 0.9573 |
| H8_target0 | agent_cash_count_skew_24h | 460 | 0.3195 | 0.2000 |
| H8_target0 | agent_cash_value_skew_24h | 460 | 0.5355 | 0.6249 |
| H8_target0 | agent_cash_value_skew_change | 230 | 0.7849 | 0.8301 |
| TP | agent_cash_count_skew_24h | 249 | 0.6922 | 0.6667 |
| TP | agent_cash_value_skew_24h | 249 | 0.9388 | 0.9823 |
| TP | agent_cash_value_skew_change | 249 | 0.9613 | 1.0152 |


**Diagnosis:** weak cash magnitude and cold displayed history do not explain most misses. All A4 rows have agent coverage capped at 28 days; **87/88 misses have an available skew-change baseline**. Mean absolute value/count skew is **0.9627/0.7722 for FN**, compared with **0.9388/0.6922 for TP**. Signed averages mix opposite cash directions and would conceal this. Mean absolute observed change is 0.9331 for FN versus 0.9613 for TP.

Co-occurring agent evidence is strongly associated with detection: **148/156 (0.9487)** with A1/A2/A3 overlap versus **101/181 (0.5580)** without it. FN observed growth averages 1.0434 versus 1.4454 for TP, and service counts are lower. Most misses therefore occur where the model has less support from other agent behaviours despite substantial cash imbalance. H8 target-0 absolute-skew ranges overlap the misses, but their average absolute value/count skews are much lower (0.5355/0.3195); similarity of individual cash quantities does not establish equivalence of the full reference conditions. Weak private strength has only six examples and onset offsets only twelve, so those comparisons are inconclusive. Weighting/model tradeoffs and omitted joint cash-service information remain plausible explanations; they cannot be separated causally by these diagnostics.

## 10. Sparse families



| Partition | Family | Positive support | TP | FN | Observed recall |
| --- | --- | --- | --- | --- | --- |
| train | S2 | 4 | 2 | 2 | 0.5000 |
| train | S4 | 40 | 16 | 24 | 0.4000 |
| validation | S2 | 1 | 1 | 0 | 1.0000 |
| validation | S4 | 8 | 6 | 2 | 0.7500 |


Train S2 has four positives and Validation one; S4 has 40 and eight. One changed Validation prediction changes S2 recall by 100 percentage points and S4 by 12.5 points. Their observed recalls cannot establish reliable generalization. No split changes, sparse-case tuning or additional evaluation examples were used. Dependence among events further limits naive independent-row uncertainty claims.

## 11. H1 and H5 false positives

Within each target-0 category, first group is FP and second is TN. All 32 distributions and missing-rate differences are retained in JSON. The tables rank the eight largest absolute observed standardized mean differences using pooled population SD. They are descriptive and sensitive to outliers/correlation; no feature was changed.

### H1



| Support | FP | TN | FPR |
| --- | --- | --- | --- |
| 238 | 39 | 199 | 0.1639 |




| Feature | FP observed N | TN observed N | FP mean | TN mean | FP median | TN median | Standardized mean difference | Missing rate difference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| wallet_count_acceleration_1h | 23 | 88 | 4.0435 | 2.2500 | 5.0000 | 2.0000 | 1.0957 | -0.1475 |
| current_return_amount_ratio | 3 | 1 | 74.6746 | 0.0524 | 1.4223 | 0.0524 | 1.0102 | -0.0719 |
| agent_service_acceleration_1h | 14 | 75 | 3.2857 | 1.9600 | 3.0000 | 2.0000 | 0.9875 | 0.0179 |
| wallet_history_coverage_days | 39 | 199 | 25.6652 | 18.2387 | 28.0000 | 25.2957 | 0.8840 | 0.0000 |
| receiver_history_coverage_days | 39 | 199 | 25.3543 | 18.1667 | 28.0000 | 25.2935 | 0.8418 | 0.0000 |
| sender_unique_destinations_24h_inclusive | 39 | 199 | 3.9744 | 2.0603 | 4.0000 | 1.0000 | 0.7371 | 0.0000 |
| current_is_cash_in | 39 | 199 | 0.0513 | 0.3065 | 0.0000 | 0.0000 | -0.7063 | 0.0000 |
| wallet_prior_funding_age_hours | 18 | 37 | 7.3043 | 11.6671 | 5.4126 | 6.4784 | -0.6506 | -0.2756 |




| recipe | Target-0 support | FP | TN | FPR |
| --- | --- | --- | --- | --- |
| S1 | 133 | 21 | 112 | 0.1579 |
| S3 | 105 | 18 | 87 | 0.1714 |




| transaction_type | Target-0 support | FP | TN | FPR |
| --- | --- | --- | --- | --- |
| cash_in | 63 | 2 | 61 | 0.0317 |
| cash_out | 73 | 8 | 65 | 0.1096 |
| wallet_to_wallet | 102 | 29 | 73 | 0.2843 |




| channel | Target-0 support | FP | TN | FPR |
| --- | --- | --- | --- | --- |
| agent | 184 | 23 | 161 | 0.1250 |
| direct_wallet | 54 | 16 | 38 | 0.2963 |


H1 errors are associated with higher observed wallet/agent acceleration, more endpoint coverage and greater sender breadth. W2W has 29/102 false positives (0.2843), versus 2/63 Cash-In and 8/73 Cash-Out. Direct-channel FPR is 16/54 (0.2963), but type/channel are correlated diagnostic slices, not causal effects. S1 and S3 recipes both contribute (21/133 and 18/105). The high-ranked return-ratio contrast has only **three FP and one TN observed values**, so it is not reliable evidence of a systematic driver.

### H5



| Support | FP | TN | FPR |
| --- | --- | --- | --- |
| 214 | 21 | 193 | 0.0981 |




| Feature | FP observed N | TN observed N | FP mean | TN mean | FP median | TN median | Standardized mean difference | Missing rate difference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| agent_top2_share_change_24h | 2 | 75 | 0.7093 | 0.5016 | 0.7093 | 0.4950 | 1.2286 | 0.2934 |
| sender_outflow_count_24h_inclusive | 21 | 193 | 3.8095 | 1.3472 | 4.0000 | 1.0000 | 1.0341 | 0.0000 |
| sender_outflow_acceleration_24h | 4 | 101 | 3.2500 | 1.3465 | 2.5000 | 1.0000 | 1.0147 | 0.3328 |
| sender_unique_destinations_24h_inclusive | 21 | 193 | 3.2381 | 1.2228 | 4.0000 | 1.0000 | 1.0103 | 0.0000 |
| current_return_amount_ratio | 2 | 14 | 892.8777 | 189.2350 | 892.8777 | 14.3695 | 0.9914 | -0.0227 |
| wallet_count_utc_day_inclusive | 21 | 193 | 7.1905 | 3.0570 | 6.0000 | 2.0000 | 0.9793 | 0.0000 |
| wallet_active_hours_utc_day | 21 | 193 | 4.2857 | 2.3886 | 5.0000 | 2.0000 | 0.8989 | 0.0000 |
| wallet_count_1h_inclusive | 21 | 193 | 2.2857 | 1.4301 | 2.0000 | 1.0000 | 0.7742 | 0.0000 |




| recipe | Target-0 support | FP | TN | FPR |
| --- | --- | --- | --- | --- |
| N2 | 100 | 3 | 97 | 0.0300 |
| N4 | 114 | 18 | 96 | 0.1579 |




| transaction_type | Target-0 support | FP | TN | FPR |
| --- | --- | --- | --- | --- |
| cash_in | 74 | 6 | 68 | 0.0811 |
| cash_out | 36 | 3 | 33 | 0.0833 |
| wallet_to_wallet | 104 | 12 | 92 | 0.1154 |




| channel | Target-0 support | FP | TN | FPR |
| --- | --- | --- | --- | --- |
| agent | 151 | 14 | 137 | 0.0927 |
| direct_wallet | 63 | 7 | 56 | 0.1111 |


H5 errors concentrate in the N4 transit recipe: **18/114**, compared with **3/100** N2 payroll/dispersion. Higher sender breadth/outflow counts and day/hour activity distinguish FP from TN. The leading observed top-two-change contrast has only **two available FP values** and sender acceleration only four, so robust inference from those rankings is unwarranted. Their missing-rate differences are reported separately. Endpoint coverage/current amount and all feature domains are retained in the full JSON comparisons; no one-feature cause is established.

## 12. Seed sensitivity and repeated-fit reproducibility

Exactly five predetermined seeds were tested, plus one separately declared same-seed repeat. The saved Stage 11 reference was reused for comparison and never refitted.



| Run | Macro F1 | Precision 1 | Recall 1 | F1 1 | AP | ROC-AUC | FPR | Structuring recall | Network recall | Agent recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| seed_20260928 | 0.9521 | 0.9379 | 0.9349 | 0.9364 | 0.9772 | 0.9888 | 0.0315 | 0.9952 | 0.9465 | 0.9332 |
| seed_20260929 | 0.9521 | 0.9379 | 0.9349 | 0.9364 | 0.9772 | 0.9888 | 0.0315 | 0.9952 | 0.9465 | 0.9332 |
| seed_20260930 | 0.9521 | 0.9379 | 0.9349 | 0.9364 | 0.9772 | 0.9888 | 0.0315 | 0.9952 | 0.9465 | 0.9332 |
| seed_20261001 | 0.9521 | 0.9379 | 0.9349 | 0.9364 | 0.9772 | 0.9888 | 0.0315 | 0.9952 | 0.9465 | 0.9332 |
| seed_20261002 | 0.9521 | 0.9379 | 0.9349 | 0.9364 | 0.9772 | 0.9888 | 0.0315 | 0.9952 | 0.9465 | 0.9332 |
| same_seed_repeat | 0.9521 | 0.9379 | 0.9349 | 0.9364 | 0.9772 | 0.9888 | 0.0315 | 0.9952 | 0.9465 | 0.9332 |




| Metric | Mean | SD | Min | Max |
| --- | --- | --- | --- | --- |
| average_precision | 0.9772 | 0.0000 | 0.9772 | 0.9772 |
| false_positive_rate | 0.0315 | 0.0000 | 0.0315 | 0.0315 |
| macro_f1 | 0.9521 | 0.0000 | 0.9521 | 0.9521 |
| roc_auc | 0.9888 | 0.0000 | 0.9888 | 0.9888 |
| suspicious_f1 | 0.9364 | 0.0000 | 0.9364 | 0.9364 |
| suspicious_precision | 0.9379 | 0.0000 | 0.9379 | 0.9379 |
| suspicious_recall | 0.9349 | 0.0000 | 0.9349 | 0.9349 |
| agent recall | 0.9332 | 0.0000 | 0.9332 | 0.9332 |
| network recall | 0.9465 | 0.0000 | 0.9465 | 0.9465 |
| structuring recall | 0.9952 | 0.0000 | 0.9952 | 0.9952 |




| Run | Maximum probability difference versus saved reference |
| --- | --- |
| same_seed_repeat | 0.0000 |
| seed_20260928 | 0.0000 |
| seed_20260929 | 0.0000 |
| seed_20260930 | 0.0000 |
| seed_20261001 | 0.0000 |
| seed_20261002 | 0.0000 |


All five seed runs and the same-seed repeat produce identical probabilities on this data. With no early stopping and all features available at each split, the configuration exhibits no seed sensitivity here. These fits establish same-environment reproducibility, not five independent estimates of population robustness. No seed was selected.

## 13. Existing comparator robustness

All comparator scores are reused from hashed Stage 11 artifacts. No comparator was retrained.



| Candidate | Macro F1 | Precision 1 | Recall 1 | F1 1 | AP | ROC-AUC | FPR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| s11_08_gradient_boosting | 0.9382 | 0.9354 | 0.8999 | 0.9173 | 0.9749 | 0.9855 | 0.0316 |
| s11_09_hist_gradient_boosting | 0.9521 | 0.9379 | 0.9349 | 0.9364 | 0.9772 | 0.9888 | 0.0315 |
| s11_15_xgboost | 0.9456 | 0.9239 | 0.9321 | 0.9280 | 0.9771 | 0.9879 | 0.0390 |
| s11_27_random_forest | 0.9464 | 0.9475 | 0.9098 | 0.9282 | 0.9827 | 0.9903 | 0.0256 |


### Domains



| Slice | Support | s11_08_gradient_boosting | s11_09_hist_gradient_boosting | s11_15_xgboost | s11_27_random_forest |
| --- | --- | --- | --- | --- | --- |
| agent | 3835 | 0.8928 | 0.9332 | 0.9288 | 0.9103 |
| network | 1271 | 0.9284 | 0.9465 | 0.9489 | 0.9135 |
| structuring | 1039 | 0.9962 | 0.9952 | 0.9952 | 0.9942 |


### Families



| Slice | Support | s11_08_gradient_boosting | s11_09_hist_gradient_boosting | s11_15_xgboost | s11_27_random_forest |
| --- | --- | --- | --- | --- | --- |
| A1 | 2745 | 0.9756 | 0.9796 | 0.9774 | 0.9774 |
| A2 | 930 | 0.7914 | 0.8753 | 0.8763 | 0.8129 |
| A3 | 485 | 1.0000 | 0.9918 | 0.9979 | 0.9876 |
| A4 | 337 | 0.5045 | 0.7389 | 0.6914 | 0.6380 |
| N1 | 316 | 0.9304 | 0.9525 | 0.9494 | 0.9367 |
| N2 | 736 | 0.9416 | 0.9620 | 0.9660 | 0.9524 |
| N3 | 41 | 0.5366 | 0.5366 | 0.5610 | 0.2927 |
| N4 | 247 | 0.9717 | 0.9757 | 0.9757 | 0.8907 |
| S1 | 276 | 0.9928 | 0.9891 | 0.9891 | 0.9855 |
| S2 | 1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| S3 | 814 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| S4 | 8 | 0.7500 | 0.7500 | 0.7500 | 0.7500 |


### Normal categories



| Slice | Support | s11_08_gradient_boosting | s11_09_hist_gradient_boosting | s11_15_xgboost | s11_27_random_forest |
| --- | --- | --- | --- | --- | --- |
| H1 | 238 | 0.1765 | 0.1639 | 0.1891 | 0.1429 |
| H2 | 374 | 0.0588 | 0.0508 | 0.0829 | 0.0241 |
| H3 | 406 | 0.0443 | 0.0369 | 0.0468 | 0.0148 |
| H4 | 292 | 0.0822 | 0.0479 | 0.0788 | 0.0240 |
| H5 | 214 | 0.0794 | 0.0981 | 0.1168 | 0.1168 |
| H6 | 424 | 0.0071 | 0.0142 | 0.0142 | 0.0047 |
| H7 | 359 | 0.0056 | 0.0056 | 0.0111 | 0.0056 |
| H8 | 460 | 0.0326 | 0.0326 | 0.0370 | 0.0304 |
| campaign_member_target0 | 1796 | 0.0507 | 0.0551 | 0.0696 | 0.0462 |
| routine | 5382 | 0.0149 | 0.0154 | 0.0173 | 0.0136 |


N3 is weak across the four models (recall 0.2927–0.5610), while A4 ranges 0.5045–0.7389. H1 remains a high-FPR category across them; H5 also remains difficult and differs by model. Shared difficulties support a representation/data-support concern in addition to model-specific tradeoffs, but do not prove that another representation would fix them.

## 14. Decision and next boundary

**B — STRONG BUT FEATURE-CONCENTRATED.**

The preregistered single-growth removal is EXTREME, removal of the whole agent domain is highly damaging, and tiny subsets recover substantial but incomplete performance. This outweighs the unchanged high full-model score as evidence for unconditional robustness approval. At the same time, strong domain-only recall and the weak missingness-only model show that the result is not explained solely by overlapping agent labels or unavailable markers.

Novelty has a material within-partition distribution difference that warrants further controlled investigation. N3 and A4 remain family-specific weaknesses; S2/S4 support is inadequate for reliable generalization claims. Another separately authorized controlled-development stage should examine growth dependence, novelty transportability and the specific weak-family representation gaps before final model/threshold development. No feature proposal is promoted by this stage.

Validation has now been reused for model selection and diagnostics. These are selected synthetic development results; neither causal feature independence nor real-world AML performance follows. Frozen target semantics remain the authority for these measurements; this stage does not certify every reference-evaluator implementation detail against the original written predicates.

## 15. Protection, evidence and reproducibility



| Protection property | Result |
| --- | --- |
| Before files | 536 |
| After files | 536 |
| Changed paths | [] |
| Public commitment unchanged | True |




| Named public certificate | Before SHA-256 | After SHA-256 |
| --- | --- | --- |
| ml_v3/data/manifests/evaluation_content_commitment.json | efc14471b98103a3ad547d93fc56833d014389efd9d3c6e5be6ba896c70d9d58 | efc14471b98103a3ad547d93fc56833d014389efd9d3c6e5be6ba896c70d9d58 |
| ml_v3/reports/V3_STAGE9_HOLDOUT_SEAL.json | efc14471b98103a3ad547d93fc56833d014389efd9d3c6e5be6ba896c70d9d58 | efc14471b98103a3ad547d93fc56833d014389efd9d3c6e5be6ba896c70d9d58 |


The explicit allowlist covers application/V1/V2 paths, frozen V3 development inputs/design, Stage 10A contract/matrices/code/evidence, earlier artifacts and all Stage 11 candidates/scores/code/reports. Exact paths and exclusions are in the protection record. No dataset root or evaluation subtree is recursively inventoried. This verifies public commitment metadata and the listed development artifacts; it does not freshly verify unread evaluation bytes.

Three regression tests passed: column-specific marker statistics, preregistered dependence cutoffs, and overlap/count orientation including the exact 0.50 tie. The independent final verification recomputes every saved diagnostic metric/slice, checks artifact/input/source hashes, and rechecks protected files. See `stage12_final_verification.json`.



| Evidence | File |
| --- | --- |
| plan | [stage12_plan.json](stage12_plan.json) |
| reference_reproduction | [stage12_reference_reproduction.json](stage12_reference_reproduction.json) |
| ablation_results | [stage12_ablation_results.json](stage12_ablation_results.json) |
| feature_dependence | [stage12_feature_dependence.json](stage12_feature_dependence.json) |
| agent_novelty_shift | [stage12_agent_novelty_shift.json](stage12_agent_novelty_shift.json) |
| missingness_audit | [stage12_missingness_audit.json](stage12_missingness_audit.json) |
| small_feature_models | [stage12_small_feature_models.json](stage12_small_feature_models.json) |
| domain_independence | [stage12_domain_independence.json](stage12_domain_independence.json) |
| n3_diagnosis | [stage12_n3_diagnosis.json](stage12_n3_diagnosis.json) |
| a4_diagnosis | [stage12_a4_diagnosis.json](stage12_a4_diagnosis.json) |
| error_details | [stage12_error_details.json](stage12_error_details.json) |
| hard_negative_analysis | [stage12_hard_negative_analysis.json](stage12_hard_negative_analysis.json) |
| stability | [stage12_stability.json](stage12_stability.json) |
| comparator_robustness | [stage12_comparator_robustness.json](stage12_comparator_robustness.json) |
| protection | [stage12_protection.json](stage12_protection.json) |
| fit_checkpoint | [stage12_fit_checkpoint.json](stage12_fit_checkpoint.json) |
| artifact_manifest | [stage12_artifact_manifest.json](stage12_artifact_manifest.json) |
| final_verification | [stage12_final_verification.json](stage12_final_verification.json) |


Entry points from the repository root:

```powershell
python -B -m unittest discover -s ml_v3/tests -p test_stage12_robustness.py -v
python -B ml_v3/src/run_stage12.py
python -B ml_v3/src/verify_stage12.py
python -B ml_v3/src/report_stage12.py
```

The runner refuses existing Stage 12 outputs. For a fresh reproduction, preserve this evidence and use an isolated development checkout with the same frozen sources/environment and a newly captured protection-before record. Do not delete prior evidence to rerun. Reports render completed diagnostics only. New joblib files and score arrays live under `models/stage12_diagnostics/` and are labelled diagnostic only.

No threshold optimization, calibration, feature promotion, final model declaration, Train+Validation refit or application integration occurred.

**V3 STAGE 12 COMPLETE — WAITING FOR APPROVAL.**
