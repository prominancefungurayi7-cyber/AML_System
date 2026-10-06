# MODEL V4 — STAGE 18 DEVELOPMENT-ONLY MODEL TRAINING AND COMPARISON

**A — DEVELOPMENT MODEL CANDIDATE SELECTED**

Selected **XGBoost (`primary_XGB`) as an experimental development candidate** under the rule frozen before fitting. At threshold 0.50 it achieved Validation Macro F1 **0.9567**, suspicious-pattern recall **0.9036**, FPR **0.0099**, ROC-AUC **0.9960** and Average Precision **0.9860**. These are selected synthetic development results. No final V4 model, independent evaluation readiness or production approval is claimed.

**Important limitation:** S2 recall is 11/23 and S4 recall is 4/16. Nine original family-support objectives still fail. Strong aggregate scores do not establish reliable twelve-family performance.

## 1. Authorization, inputs and preservation gates

The user's Stage 18 request authorizes Train-only fitting and Train/Validation comparison after Stage 17. Stage 15/15A definitions and restrictions retain precedence; Stage 16R's retained draw, Stage 16S's support failures, Stage 16T's challenge protocol and Stage 16U/16V custody limitations remain unchanged. Stage 17's frozen matrices and artifact hashes were verified before any fit.

Train contains 60,000 scored records; Validation contains 15,000. Each X has exactly 40 semantic fields, 39 float64 and one categorical Unicode type. The original y arrays, row order and transaction IDs match frozen ground truth. Existing family annotations agree exactly with the binary union labels. Diagnostic provenance contains warm-up as well as scored records: the initial preflight join incorrectly assumed scored rows only and stopped before any fitting. The implementation was corrected to prove that its extra IDs equal the permitted warm-up IDs exactly; only scored annotations enter diagnostics. No input contract, data, feature or label was changed. Final preflight: PASS. This correction consumed zero model fits.

Only authorized Train/Validation development files and public research evidence were accessed. Annotation loading uses exact partition/filename allowlists and rejects resolved path redirection. The extractor was not rerun. Private origins and family annotations are held separately for diagnostics and never passed to preprocessing, fit or predict. Original Final Test and Independent Evaluation remain SEALED_QUARANTINED. No private evaluation contents were read, listed, hashed, decrypted or copied. No challenge data or secret was created.

Evidence: [input verification](../evidence/stage18/input_verification.json), [frozen plan](../evidence/stage18/frozen_training_plan.json), [final metric verification](../evidence/stage18/final_metric_verification.json).

## 2. Frozen preprocessing contract

Every fitted artifact is a scikit-learn Pipeline containing `FrozenPreprocessor` followed by its classifier. Explicit per-column -1/-3 missing markers are converted to NaN. Existing N4 residual NaN remains missing. Valid negative residuals, concentration differences and cash-skew changes are preserved; there is no generic negative-value replacement.

The categorical order is **wallet_to_wallet, cash_in, cash_out**. Those three columns replace the one categorical field at its schema position. Full pipelines therefore produce **42 numeric columns**, verified from the actual output. Numeric missing values use a Train-fitted median imputer; an entirely empty Train column would receive fixed zero while retaining its column. No extra missingness indicators enter the full pipelines. All 42 columns then use Train-fitted standard scaling, unchanged on Validation. Scaling is shared for a simple reproducible contract; tree candidates do not require it. No label-derived encoding, class rebalancing, resampling, calibration or Validation-fitted transform is used.

The missingness-only diagnostic has 39 indicator columns and is not a feature-contract amendment or selectable candidate. Other diagnostics use only the predeclared subsets. Hand assertions verified semantic ordering, 42-column expansion, sentinel conversion and preservation of legitimate negative values before fitting. Schema checks reject unknown transaction types. Exact column names and marker mapping appear in [preprocessing_specification.json](../evidence/stage18/preprocessing_specification.json).

## 3. Candidates, fit budget and frozen selection rule

The plan was saved before the first fit and binds source hashes, dependency versions, seed, configurations, threshold, diagnostics and selection rule. Four primary configurations were used:

| Family | Predeclared configuration |
| --- | --- |
| Logistic Regression | C=1, lbfgs, maximum 2,000 iterations; no class weighting |
| Random Forest | 160 trees, unrestricted depth, leaf minimum 2, sqrt feature sampling, one worker |
| HistGradientBoosting | 200 iterations, learning rate .07, 31 leaves, minimum leaf 20, L2=1, early stopping disabled |
| XGBoost | 200 trees, depth 5, learning rate .07, child weight 5, lambda=1, full row/column sampling, histogram algorithm, one worker |

XGBoost is the installed fourth family already listed by Stage 15. It supplies a distinct regularized boosted-tree implementation; no fifth family was added. Random state is 2026092915; diagnostic repeats use +1. No Validation early stopping or evaluation set was supplied.

Exactly **16 classifier fits** ran: 4 primary, 4 matched dominant-feature removals, missingness-only, dominant-only, four-A1-feature-only, Train-label shuffle, and 4 seed repeats. All completed without fit warnings or failures. The maximum policy budget is 36; the 20 unused slots expire under this plan. No adaptive tuning, threshold search, Train+Validation refit or calibration occurred. Every started fit was durably entered in [fit_ledger.jsonl](../evidence/stage18/fit_ledger.jsonl) before calling fit, with its completion, runtime and resource observation. Initial preflight assertions were not fitting attempts.

Eligibility was preregistered as Validation Macro F1≥.80, recall≥.65, FPR≤.10, every domain recall≥.60, S3/N2/A1 recall≥.60, each H-origin FPR≤.20 where at least 100 target-0 rows exist, Train−Validation Macro F1≤.08, repeat Macro F1 change≤.03, and no unresolved technical failures/warnings. These are synthetic development triage tolerances, not relaxed family-support gates, independent acceptance criteria or operational risk limits.

Among eligible primary candidates, maximize Macro F1; within .005 of the best, choose lowest FPR, then highest minimum domain recall, shortest fit time and lexical ID. RF, HGB and XGBoost passed. LR failed overall recall and domain recall. HGB has the highest Macro F1 (.9616), but XGBoost (.9567) is within the frozen .005 tolerance and has lower FPR. Relative to HGB, XGBoost yields **21 fewer false positives and 64 additional false negatives**. This is the declared trade-off, not a claim that XGBoost dominates every metric. Diagnostic models and repeats were never eligible for selection.

## 4. Primary comparison at threshold 0.50

Train metrics are resubstitution diagnostics. Validation metrics drive this development comparison. AP means the sum of precision times recall increments, not trapezoidal PR area. The positive target is an observable suspicious-pattern review rule, not proven criminal activity.

| Model | Train Macro F1 | Validation Macro F1 | Precision | Recall | FPR | ROC-AUC | AP | Fit seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LR | 0.8050 | 0.8105 | 0.8092 | 0.5977 | 0.0357 | 0.9200 | 0.7935 | 0.99 |
| RF | 0.9944 | 0.9461 | 0.9462 | 0.8825 | 0.0127 | 0.9943 | 0.9799 | 21.00 |
| HGB | 0.9721 | 0.9616 | 0.9527 | 0.9248 | 0.0116 | 0.9966 | 0.9878 | 4.90 |
| XGB | 0.9613 | 0.9567 | 0.9587 | 0.9036 | 0.0099 | 0.9960 | 0.9860 | 2.63 |

| Model | TN | FP | FN | TP | Accuracy | Balanced accuracy | Positive F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LR | 11543 | 427 | 1219 | 1811 | 0.8903 | 0.7810 | 0.6875 |
| RF | 11818 | 152 | 356 | 2674 | 0.9661 | 0.9349 | 0.9133 |
| HGB | 11831 | 139 | 228 | 2802 | 0.9755 | 0.9566 | 0.9385 |
| XGB | 11852 | 118 | 292 | 2738 | 0.9727 | 0.9469 | 0.9303 |

Confusion-matrix order is `[[TN,FP],[FN,TP]]`. The selected matrix is `[[11852,118],[292,2738]]`. Its normal-class recall is 0.990142. RF has the largest primary Train-to-Validation Macro F1 gap (about .0483), while XGBoost's gap is about .0047; these are descriptive overfitting checks, not independent generalization guarantees. Complete Train/Validation metrics and probabilities are saved for every fit in [comparison.json](../evidence/stage18/comparison.json) and the explicitly experimental artifact directory.

Selected Validation Brier score is **0.020140**, log loss **0.073056**. Ten fixed-width reliability bins give a descriptive weighted absolute calibration gap of **0.017955**. No calibration was fitted, and this bin statistic depends on binning and reused Validation. Scores are class-1 probabilities from the estimator, not calibrated certainty of laundering. Empty rate denominators are null; precision with no predicted positives is zero with an undefined flag. The shuffle diagnostic predicts no positives at .50, so that flag matters.

## 5. Family, domain and clustering results

The table shows predicted-positive rows among each frozen family, with exact denominators. Membership overlaps; these rows cannot be summed as independent observations or interpreted as family-specific attribution by the model. Subjects and episode/background clusters are retained from the authorized Stage 16S evidence, not reconstructed from private intent.

| Family | LR TP/support (recall) | RF | HGB | XGBoost | Validation subjects / clusters | Original ≥300 objective |
| --- | --- | --- | --- | --- | ---: | --- |
| S1 | 73/132 (0.553) | 119/132 (0.902) | 130/132 (0.985) | 126/132 (0.955) | 31 / 34 | Shortfall |
| S2 | 2/23 (0.087) | 1/23 (0.043) | 13/23 (0.565) | 11/23 (0.478) | 7 / 7 | Shortfall |
| S3 | 366/546 (0.670) | 509/546 (0.932) | 491/546 (0.899) | 492/546 (0.901) | 104 / 156 | Met |
| S4 | 3/16 (0.188) | 4/16 (0.250) | 5/16 (0.312) | 4/16 (0.250) | 12 / 12 | Shortfall |
| N1 | 53/101 (0.525) | 78/101 (0.772) | 85/101 (0.842) | 77/101 (0.762) | 28 / 42 | Shortfall |
| N2 | 290/429 (0.676) | 380/429 (0.886) | 380/429 (0.886) | 381/429 (0.888) | 86 / 147 | Met |
| N3 | 45/130 (0.346) | 103/130 (0.792) | 115/130 (0.885) | 122/130 (0.938) | 87 / 111 | Shortfall |
| N4 | 33/144 (0.229) | 89/144 (0.618) | 120/144 (0.833) | 123/144 (0.854) | 74 / 91 | Shortfall |
| A1 | 1115/1467 (0.760) | 1467/1467 (1.000) | 1463/1467 (0.997) | 1467/1467 (1.000) | 23 / 570 | Met |
| A2 | 71/148 (0.480) | 102/148 (0.689) | 123/148 (0.831) | 109/148 (0.736) | 20 / 60 | Shortfall |
| A3 | 199/255 (0.780) | 255/255 (1.000) | 255/255 (1.000) | 255/255 (1.000) | 18 / 80 | Shortfall |
| A4 | 63/222 (0.284) | 135/222 (0.608) | 197/222 (0.887) | 151/222 (0.680) | 17 / 138 | Shortfall |

S1/S2/S4/N1/N3/N4/A2/A3/A4 remain below the original development support objectives. S2 has only 7 Validation subjects/7 clusters; S4 has 12/12. A3's perfect observed recall still has inadequate support. S3/N2/A1 satisfying count objectives does not certify precision or independence. Full Train/Validation supports, concentration and cluster counts are in [support_and_clustering.json](../evidence/stage18/support_and_clustering.json).

| Domain | LR TP/support (recall) | RF | HGB | XGBoost |
| --- | --- | --- | --- | --- |
| structuring | 416/684 (0.608) | 600/684 (0.877) | 606/684 (0.886) | 600/684 (0.877) |
| network | 405/776 (0.522) | 626/776 (0.807) | 672/776 (0.866) | 675/776 (0.870) |
| agent | 1310/1941 (0.675) | 1808/1941 (0.931) | 1887/1941 (0.972) | 1831/1941 (0.943) |

Domain-only and unique multi-domain results are retained in [family_domain_diagnostics.json](../evidence/stage18/family_domain_diagnostics.json). This is one union-target classifier, with no separate domain prediction heads; a separate domain-specific FPR cannot be inferred. False-positive behaviour is reported on genuine union-target-0 origin/type slices instead.

Selected hard-origin/background target-0 FPR:

| Origin | FP / negative support | FPR |
| --- | ---: | ---: |
| H1 | 2 / 245 | 0.0082 |
| H2 | 4 / 302 | 0.0132 |
| H3 | 1 / 294 | 0.0034 |
| H4 | 1 / 294 | 0.0034 |
| H5 | 12 / 240 | 0.0500 |
| H6 | 4 / 309 | 0.0129 |
| H7 | 4 / 218 | 0.0183 |
| H8 | 1 / 231 | 0.0043 |
| background | 8 / 5495 | 0.0015 |

Pre-onset campaign target-0 FPR is 0/296. H-origin rows with any true family remain positive and are excluded from FPR denominators. No hard-origin relabeling or selection occurred. Exact legitimate-growth-mechanism and family near-boundary slices were not reconstructed: the available archetype field is not equivalent to an observed origin mechanism. Their absence limits the broader shortcut audit and is not hidden behind an archetype proxy.

Only three Validation communities exist. Selected unit recalls are approximately .8929, .9085 and .9098; unit FPRs .00755, .01205 and .00997. Selected S2 unit recalls vary from 0/3 to 10/15 and 1/5; S4 has 1/4, 2/9 and 1/3. These sparse clustered counts do not support precise population inference. Raw per-unit family rates and descriptive Wilson intervals are saved. Wilson intervals ignore dependence; no row-wise bootstrap or stable cluster precision is claimed. Minute floating endpoint overshoots in raw Wilson records are arithmetic rounding, not probabilities above one.

## 6. Shortcut, missingness and feature-dependence audit

All four primary models use the same 3,000 Validation rows sampled uniformly without replacement with seed 2026092915. Each semantic field is permuted three times, paired across models; transaction type is permuted before encoding so its three indicators move together. Deterministic repeat seeds are base 2026092916 plus repeat index 0,1,2, as fixed in source before fitting. Baseline AP and perturbed AP use exactly the same sample. Signed mean AP drops, repeat sample SD, absolute-mass group shares and top shares are saved in [permutation_importance.json](../evidence/stage18/permutation_importance.json). There is no substitution of native impurity/gain scores.

| Model | Highest absolute mean AP-drop field | Top-1 mass | Top-3 mass | Top-5 mass | Macro F1 drop after matched removal |
| --- | --- | ---: | ---: | ---: | ---: |
| LR | `agent_observed_coverage_days` | 0.229 | 0.584 | 0.781 | 0.0021 |
| RF | `agent_wallet_growth_ratio_7d` | 0.468 | 0.723 | 0.782 | 0.0778 |
| HGB | `agent_wallet_growth_ratio_7d` | 0.373 | 0.639 | 0.735 | 0.0781 |
| XGB | `agent_wallet_growth_ratio_7d` | 0.377 | 0.701 | 0.761 | 0.0781 |

XGBoost assigns about 76.2% of absolute permutation mass to agent fields, 15.5% to network and 7.6% to structuring. Growth alone accounts for about 37.7%. The matched growth-removal XGBoost falls to Macro F1 .8785, recall .7604 and AP .9041. This is material dependence. Growth is an explicitly permitted direct component of A1, so neither importance nor ablation establishes leakage by itself. Correlated fields can divide mass, and permutations can create off-manifold combinations.

The permutation sample contains only 7 S2 and 3 S4 positive rows. Importance cannot rescue sparse-family evaluation. For the selected full model, recall among positives without A1 is 1271/1563 (.8132), below aggregate .9036 and A1's 1467/1467. Dominant-family alignment contributes substantially to the headline result.

| Predeclared diagnostic | Validation Macro F1 | Recall | FPR | AP |
| --- | ---: | ---: | ---: | ---: |
| dominant_only_HGB | 0.7486 | 0.4993 | 0.0533 | 0.5896 |
| missingness_HGB | 0.4588 | 0.0155 | 0.0035 | 0.2856 |
| remove_HGB | 0.8835 | 0.7815 | 0.0361 | 0.9101 |
| remove_LR | 0.8084 | 0.5944 | 0.0363 | 0.7902 |
| remove_RF | 0.8683 | 0.7508 | 0.0396 | 0.8789 |
| remove_XGB | 0.8785 | 0.7604 | 0.0335 | 0.9041 |
| repeat_HGB | 0.9616 | 0.9248 | 0.0116 | 0.9878 |
| repeat_LR | 0.8105 | 0.5977 | 0.0357 | 0.7935 |
| repeat_RF | 0.9450 | 0.8799 | 0.0129 | 0.9802 |
| repeat_XGB | 0.9567 | 0.9036 | 0.0099 | 0.9860 |
| shuffle_HGB | 0.4438 | 0.0000 | 0.0000 | 0.2406 |
| tiny_A1_HGB | 0.7952 | 0.4851 | 0.0008 | 0.6618 |

Missingness-only HGB has AP .2856 and very low .50-threshold recall (.0155); missingness carries some development signal but does not reproduce the full model. Growth-only HGB and the four-A1-field model demonstrate how much the enriched compound target can be approximated with a small representation. The Train-label-shuffle fit gives AP .2406 and zero .50-threshold recall; this is a sanity diagnostic, not a formal no-leakage proof. Shuffle Train metrics are measured against the real frozen Train labels, not the shuffled training target, so they represent sanity performance rather than fit to its permuted labels.

Seed-repeat Macro F1 changes were zero for LR/HGB/XGBoost and about −.00110 for RF. Several fixed algorithms/configurations are effectively deterministic without subsampling; zero change is not evidence across broad resampling uncertainty. No extra seeds or configurations were tried.

Selected type-specific target-0 FPR is .01357 for W2W, .00471 for Cash-In and .00624 for Cash-Out. Type is a legitimate role/context input, yet differing rates and declared generator laws warrant qualification. A1-eligible versus ineligible recall/FPR and agent-age strata are saved. The zero-age bin includes absent agents; it cannot be interpreted solely as young-agent behaviour. Intermediate agent-age bins have no support and are reported null.

Stage 17's marker-aware Train/Validation distributions remain the shift reference. For example, growth missingness is 31.43% in Train and about 32.19% in Validation; no preprocessing was fitted on Validation to reduce this difference. Generator origin/archetype/IDs never enter X. Origin diagnostics, type permutations, missingness and shuffle checks do not rule out every synthetic-generation artifact. No feature contract was amended after inspecting results.

## 7. Reproducibility, artifacts and resources

Runtime: Python 3.14.3, NumPy 2.4.3, scikit-learn 1.9.0, XGBoost 3.4.1. Estimator workers and numerical thread pools were constrained to one. The frozen plan records exact parameters and source hashes. Predictions, all sixteen fitted pipelines and permutation sample indices are saved under `ml_v4/development_training/artifacts/`, outside V1/V3 model locations. Every pipeline embeds its fitted preprocessing; an additional standalone selected preprocessor is saved without refitting.

Selected pipeline: [primary_XGB_EXPERIMENTAL.joblib](../development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib). Standalone preprocessing: [selected_preprocessor_EXPERIMENTAL.joblib](../development_training/artifacts/selected_preprocessor_EXPERIMENTAL.joblib). [selected_artifacts.json](../evidence/stage18/selected_artifacts.json) binds their hashes, classes [0,1], feature version, 42-column order and threshold .50. Load only these trusted hash-verified artifacts in the recorded runtime, with `development_training/preprocessing.py` importable. No service or application adapter was added.

Primary artifact reloads reproduced predictions exactly on the fixed first 100 Validation rows; this is a serialization check, not independent evaluation. Final independent arithmetic reproduced all Train/Validation confusion matrices and Macro F1 from the 32 saved probability arrays. Family denominators match existing Stage 16S evidence. No new fit was required for final verification.

Peak process working set was 598,306,816 bytes (about 570.6 MiB), including previously retained models and diagnostics. It is not isolated per-model memory. Per-fit runtime/high-water measurements and overall wall interval are in [resource_runtime_report.json](../evidence/stage18/resource_runtime_report.json). Replaying the entire training script against existing outputs is refused, preventing an unnoticed second fitting run; any future repeat requires separate authorization and budget accounting.

## 8. Preservation and scientific limitations

All named protected input hashes match before and after fitting and at final review. Protected scope includes Stage 17 outputs, frozen V4 design/data/labels and authorized annotation files, earlier public evidence, V1 production artifact and V3 experimental model/source/integration. No Flask, MySQL, dashboard, API, target, feature definition, transaction, partition, challenge protocol or custody control was changed. [preservation_verification.json](../evidence/stage18/preservation_verification.json) and [final_preservation_check.json](../evidence/stage18/final_preservation_check.json) define the exact scope. Sealed evaluation bytes are deliberately excluded and unread.

Stage 16V's incomplete broad Stage 15A historical snapshot remains unresolved. Nothing was restored or rewritten to manufacture a full preservation PASS. The present checks cover explicitly available protected files, not every historical file or all disk contents.

The main limitations are repeated development use, nine family-support failures, only three Validation communities, direct-component learning, strong A1/growth dependence, compact representation omissions and unknown transport to independent or real operator populations. S2/S4 empirical weakness must accompany aggregate metrics. No real-world laundering, intent, regulatory or production-effectiveness claim follows from this benchmark. A development candidate is not a final model. Original holdouts remain quarantined and cannot repair or certify these findings; challenge generation remains blocked by unavailable independent custody.

## 9. Deliverables and final decision

New files are confined to `ml_v4/development_training/`, `ml_v4/evidence/stage18/` and this report. The evidence directory contains the input gate, frozen plan, preprocessing specification, complete fit ledger, all fit metrics, probability/artifact references, family/domain/support diagnostics, permutation/shortcut audits, selection, runtime, preservation, metric verification and final artifact hashes. Earlier reports and artifacts were not overwritten.

**A — DEVELOPMENT MODEL CANDIDATE SELECTED**

`primary_XGB` is selected for further separately authorized development, subject to the documented sparse-family and synthetic-data limitations. This decision authorizes no independent evaluation, production promotion, threshold optimization, challenge generation or Flask integration. No Stage 19 work is started.

V4 STAGE 18 COMPLETE — WAITING FOR APPROVAL.
