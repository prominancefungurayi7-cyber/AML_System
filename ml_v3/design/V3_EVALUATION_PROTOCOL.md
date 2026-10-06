# V3 evaluation and preregistration protocol — proposed revision 1

This protocol is a proposal for approval before new data is generated. It authorizes no Stage 8 model fitting, feature extraction, generation, threshold search or application integration.

## Freeze sequence and model-development policy

Freeze a registry identifying the dataset version and hashes of all seven design documents: scenario definitions, onset predicates, target semantics, planned cohorts/partitions, hard-scenario controls, feature architecture proposal, holdout policy, metrics and this development policy. Record approval and source/seed commitments before generation. Implementation details left to the future generator must be specified and tested before emission, not filled in after observing labels or scores. If an exact condition changes, create a new preregistration revision and, after any data has been generated, a new dataset version.

Next authorize and implement the generator/reference evaluator and conduct model-free structural checks. Seal new holdouts through their generation entry point. Only after the development audit passes may an independently authorized feature implementation freeze exact formulas, missingness semantics, ordered columns, preprocessing and causal tests. The Stage 8 architecture is a proposal; it must not silently become a supposedly validated final contract.

For future model development, predeclare at most 36 candidate configurations across Logistic Regression, HistGradientBoosting and one gradient-boosted-tree family. Fix seed `20260922` for comparisons and two additional declared stability seeds `20260923` and `20260924`; this is a model seed policy, not permission to reuse an old dataset stream. Fit imputation, scaling, clipping and calibration on Train only. Fix reasonable weight choices before search (1, 2 and 4), and do not resample Validation or artificially alter target prevalence. No scenario or onset metadata enters X. Baseline comparison uses threshold 0.50.

Record every configuration, warning, fit duration, Train/Validation metric and generalization gap. Select a Pareto shortlist using suspicious recall, FPR, PR-AUC and generalization alongside Macro F1. Report the best Macro F1 but do not call a marginal edge success when a family or hard-negative slice worsens. Family-conditioned diagnostic models are not a deployable ensemble and do not justify using a private family selector at inference.

Threshold optimization is a later separately authorized step after feature/model selection. If authorized, freeze the ranking model, search a single declared Validation grid of 0.05–0.95 in steps of 0.01, choose maximum suspicious F1 among thresholds meeting FPR ≤ 0.08 and recall ≥ 0.70, and break ties by lower FPR then higher threshold. If no point is feasible, report infeasibility and the trade-off; do not weaken the goals or rerun the search on holdouts. A 0.50 baseline remains reported. Optional probability calibration must be preregistered and fitted through entity-separated Train folds, not on Validation or holdouts. Freeze the chosen model, ordered feature contract, preprocessing, calibration and threshold before requesting holdout access.

## Metrics and denominator definitions

| Measure | Definition / required treatment |
|---|---|
| Accuracy | Correct target predictions / all evaluated transaction triggers. |
| Balanced Accuracy | Mean of positive recall and negative-class recall. |
| Macro F1 | Arithmetic mean of class-0 and class-1 F1. |
| Suspicious precision, recall, F1 | Class-1 metrics against `decision_point_target`, not campaign membership. |
| Normal recall | TN/(TN+FP), where normal means decision target 0. |
| ROC-AUC | Ranking metric over all positive/negative target records. |
| PR-AUC / Average Precision | Average Precision is the primary precision-recall summary; if trapezoidal PR area is also shown, name it separately. Report positive prevalence with AP. |
| FPR | FP/(FP+TN), including pre-onset campaign events with actual target 0. |
| Confusion matrix | Fixed row/column order `[0,1]`, with raw TN/FP/FN/TP counts. |

Report all metrics on Train and Validation during development, and on each evaluation partition only after authorization. Undefined precision/AUC or empty slices must show their support and undefined status; do not present zero as a successful measured rate. State the zero-division convention used for F1.

## Behavioural and timing diagnostics

- Domain/family recall uses target-positive events with that domain/family in `evidence_families`. Multi-family events can appear in multiple slices; count them once in global metrics and disclose overlapping denominators.
- Separately report campaign-member coverage and never-onset campaigns. Do not call failure to alert on an intended campaign a false negative when the reference target never becomes 1.
- Onset-event recall measures positive predictions on reference family activation events; campaign-relative onset position is first/second/third/later and normalized campaign quartiles. The metadata performs grouping only. Report reactivations separately from first onset.
- Report recall on onset, subsequent active events, and N3 closure pulses. Report false positives on pre-onset target-0 events and post-onset inactive events. Cross-family positives before a campaign's intended onset are true positives/false negatives according to their actual target, never silently counted as normal.
- Report recall by planned weak/moderate/strong on positive campaign-member targets. Positive routine or legitimate-origin events and other-family triggers without a matching planned strength form an explicit unassigned category; do not invent strength from model confidence.
- For H1–H8 and each mixed subtype, report FP counts and FPR among target-0 members, plus the full legitimate-origin reference-positive rate and the model's overall review rate. This distinguishes classifier error from a review-worthy lawful behaviour under the synthetic definition.
- Report runtime/latency per transaction, missing-baseline rates, and first-alert delay relative to reference onset. Optional campaign detection coverage is secondary and may use hindsight only as an evaluation aggregation, never as a feature.

The transaction remains the scoring unit. Estimates share wallets, agents and episodes, so ordinary independent-event confidence intervals overstate precision. Report point estimates and support first; if intervals are used, preregister a bootstrap over disconnected entity-interaction components within each partition, keeping complete component histories together. If too few independent components exist, disclose that intervals cannot reliably quantify sampling uncertainty rather than inventing event independence.

## Research goals

| Goal | Research target |
|---|---:|
| Macro F1 | ≥ 0.80 |
| Suspicious recall | ≥ 0.70 |
| Suspicious F1 | ≥ 0.65 |
| Structuring recall | ≥ 0.60 |
| Network recall | ≥ 0.70 |
| Agent recall | ≥ 0.65 |
| Average Precision | ≥ 0.65 |
| FPR | Preferably ≤ 0.08 |

**THESE ARE GOALS, NOT DATASET DESIGN CONSTRAINTS.** Do not tune the generator, labels, feature definitions, evidence windows, holdout selection or evaluation procedure simply to attain them. The 12% planning prevalence is likewise not an acceptance target. Publish failures, material slice deterioration and uncertainty.

## Comparison with V2 and external validity

Old V2 predicts episode membership at each member transaction. V3 predicts a synthetic observable alert state at a current trigger. A V3 score must not be called an improvement on the identical prediction task. Present dataset identity, target definition, prevalence, analytical unit and holdout policy with every comparison. A V2 feature-definition port evaluated on V3 may test representation under the same new target; it does not make the two original datasets equivalent.

The fixed synthetic oracle does not establish real-world money laundering ground truth. Label determinism, chosen monetary/window constants, limited currencies and transaction types, matching recipes, single synthetic population and possible residual generator artefacts limit the conclusion. A high score shows agreement with this reference under the specified sampling design. A future real-world claim needs separately justified reference evidence and human review.

## Release and stopping gates

Record all freeze identifiers and generation audit decisions, access new holdouts only through the separately authorized evaluator, and publish its one-time results including failures. Any feedback-driven redesign requires a new version and fresh evaluation plan. Stage 8 stops after these documents and the [proposal report](../reports/V2_STAGE8_REDESIGN_PROPOSAL.md); the next operational action requires explicit approval.
