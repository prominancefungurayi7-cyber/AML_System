# MODEL V4 — STAGE 19 MODEL WEAKNESS ANALYSIS AND IMPROVEMENT PLAN

**A — DEVELOPMENT ANALYSIS COMPLETE; IMPROVEMENT PLAN READY**

XGBoost remains the selected experimental development candidate. HGB remains an important comparator. All four primary candidates' saved Train/Validation results were independently recalculated from saved probabilities and match Stage 18. This stage performed **zero fits, zero new model predictions, zero threshold searches and no feature/dataset changes**.

The clearest weaknesses are: **S4-only Validation recall 0/12**, sparse and incompletely represented S2/S4 history, materially better HGB detection of A4/A2 on the same fields, and demonstrable loss in N3's selected-route summary. The defensible next step is a **separately authorized, design-only feature-representation amendment and compatibility review**, while preserving both candidates and the original draw. No expected improvement is asserted as measured.

## 1. Authoritative evidence, scope and verification

Stage 15's twelve targets and forty semantic fields remain frozen. Stage 15A overrides only its declared population/amount/context clauses. Stage 16R's one retained draw, Stage 16S's support failures, Stage 16T's independent challenge requirements, Stage 16U/16V's custody restrictions, Stage 17's feature artifacts and Stage 18's plan/ledger/artifacts remain authoritative. Their named hashes were verified before analysis and again at completion. Original Final Test and Independent Evaluation remain SEALED_QUARANTINED; only existing public support-policy FAIL facts are retained. No private evaluation files, counts, seeds or registry were accessed.

The analysis reads the existing 60,000 Train and 15,000 Validation feature rows, frozen labels, saved primary probabilities and authorized development annotations. Scored transaction observables supply subject/time context only; no history is re-extracted. Provenance includes warm-up IDs, which are checked against the exact warm-up ID set and excluded from scored diagnostics. IDs, order, label/family union, subjects and clusters agree with saved evidence. No evaluator, extractor, generator or fitted model is imported or executed. Models are hashed without deserializing them.

New source is [stage19_analysis.py](../development_analysis/stage19_analysis.py), [stage19_plan.py](../development_analysis/stage19_plan.py), [stage19_supplement.py](../development_analysis/stage19_supplement.py) and [stage19_report.py](../development_analysis/stage19_report.py). Independent arithmetic here means separate calculations in the same developer environment, not an independent external audit.

## 2. Saved model results and selection rationale verified

All classification comparisons retain **score ≥ 0.50**, with confusion order `[[TN,FP],[FN,TP]]`. Macro F1, precision, recall, FPR, confusion, family/domain recalls, ROC-AUC and Average Precision match Stage 18 within 1e-12 for floating summaries. The saved ledger still contains 16 started and 16 completed fits. Stage 19 added none.

| Model | Validation Macro F1 | Precision | Recall | FPR | Confusion matrix |
| --- | ---: | ---: | ---: | ---: | --- |
| LR | 0.8105 | 0.8092 | 0.5977 | 0.0357 | [[11543, 427], [1219, 1811]] |
| RF | 0.9461 | 0.9462 | 0.8825 | 0.0127 | [[11818, 152], [356, 2674]] |
| HGB | 0.9616 | 0.9527 | 0.9248 | 0.0116 | [[11831, 139], [228, 2802]] |
| XGB | 0.9567 | 0.9587 | 0.9036 | 0.0099 | [[11852, 118], [292, 2738]] |

The frozen rule first applied its eligibility constraints, then minimized FPR among candidates within .005 of the best eligible Macro F1. HGB's Macro F1 .9616315 exceeds XGBoost's .9566703 by .0049612; both fall within that tolerance. XGBoost has 118 false positives versus HGB's 139. Reapplying the recorded ranking preserves `primary_XGB`. This stage does not reinterpret that choice using later family findings. LR remains ineligible under the original recall/domain constraints; RF/HGB/XGBoost remain the originally eligible candidates.

HGB detects 105 positives that XGBoost misses; XGBoost detects 41 that HGB misses. Both miss 187. On negatives, 95 false positives are shared, HGB alone adds 44 and XGBoost alone adds 23. Thus HGB has a net 64 additional detections and 21 additional false positives. These are paired descriptive counts, not independent-trial significance estimates or permission to replace the selected model.

Evidence: [model_results_verification.json](../evidence/stage19/model_results_verification.json), [xgboost_hgb_comparison.json](../evidence/stage19/xgboost_hgb_comparison.json).

## 3. Family/domain error accounting

XGBoost misses **292 unique Validation positives** out of 3,030. These carry 295 false-negative family memberships: three missed rows have two families. Family counts therefore cannot be summed as unique mistakes. All 292 misses are outside A1; recall among the 1,563 positives without A1 is **1,271/1,563 = .8132**, compared with aggregate .9036 and A1's 1,467/1,467.

| Family | XGB TP/support | XGB FN | HGB TP/support | XGB exclusive-family TP/support | HGB detects XGB misses | XGB detects HGB misses |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| S1 | 126/132 | 6 | 130/132 | 41/47 | 5 | 1 |
| S2 | 11/23 | 12 | 13/23 | 11/23 | 3 | 1 |
| S3 | 492/546 | 54 | 491/546 | 244/295 | 15 | 16 |
| S4 | 4/16 | 12 | 5/16 | 0/12 | 1 | 0 |
| N1 | 77/101 | 24 | 85/101 | 65/89 | 8 | 0 |
| N2 | 381/429 | 48 | 380/429 | 153/198 | 6 | 7 |
| N3 | 122/130 | 8 | 115/130 | 91/99 | 2 | 9 |
| N4 | 123/144 | 21 | 120/144 | 69/90 | 3 | 6 |
| A1 | 1467/1467 | 0 | 1463/1467 | 1253/1253 | 0 | 4 |
| A2 | 109/148 | 39 | 123/148 | 57/96 | 16 | 2 |
| A3 | 255/255 | 0 | 255/255 | 148/148 | 0 | 0 |
| A4 | 151/222 | 71 | 197/222 | 80/151 | 46 | 0 |

Exclusive-family means no other predicate fires; no labels are changed or rows excluded from primary metrics. Overlap is not evidence of the feature or rule that caused a prediction. It does show that a positive prediction on a family-bearing row need not demonstrate detection of that family's distinctive evidence.

| Domain | LR TP/support (recall) | RF | HGB | XGB |
| --- | --- | --- | --- | --- |
| structuring | 416/684 (0.608) | 600/684 (0.877) | 606/684 (0.886) | 600/684 (0.877) |
| network | 405/776 (0.522) | 626/776 (0.807) | 672/776 (0.866) | 675/776 (0.870) |
| agent | 1310/1941 (0.675) | 1808/1941 (0.931) | 1887/1941 (0.972) | 1831/1941 (0.943) |

The union classifier has no separate domain prediction heads. Domain recall uses rows bearing each domain, including overlaps. False-positive analyses use union-target-0 rows grouped by observable type or recorded origin; a distinct predicted-domain FPR would be undefined without a separate output contract.

[false_negative_analysis.json](../evidence/stage19/false_negative_analysis.json) contains marker-aware detected/missed distributions for all 40 fields and every family in both development partitions. [false_negative_rows.csv](../evidence/stage19/false_negative_rows.csv) links every selected-model FN to its original row index, ID, family flags, saved scores and diagnostic subject/cluster. [family_domain_error_analysis.json](../evidence/stage19/family_domain_error_analysis.json) includes all four primary models.

## 4. Priority weaknesses: observations and bounded explanations

### S2 — SimilarAmountRepetition

All 23 Validation S2 positives are exclusive S2 cases. XGBoost detects 11, HGB 13; nine are missed by both. XGBoost misses span six wallets/six clusters, compared with seven supported wallets/clusters overall. The largest wallet supplies three of twelve misses.

Detected versus missed median current amount is **8,369 versus 4,997 cents**, and median recent similar count is **8 versus 7**. Similar share is almost equal at the medians (.6923 versus .6905), with broad overlap. Both groups have 35 displayed coverage days and no missing S2-related feature values. Saved eligibility is true. The missed score median is .2505, with range .1061–.4814; these are fixed-score observations, not a threshold search.

The contract omits the exact recent similar-cluster value and baseline similar frequency/rate, and does not expose exact S2 baseline support. Current amount times cluster count is only an approximation under the ±5% membership tolerance. The missing information and 112 Train positives across 37 subjects/43 clusters both plausibly constrain learning. They do not prove which component caused each miss. HGB's better same-feature results show some model dependence, while weak Training recall also argues against describing the entire problem as Validation-only overfitting.

### S4 — VariableNearThresholdHistory

XGBoost detects four of sixteen S4-positive Validation rows. Those four comprise **two S4+N2, one S4+A4 and one S4+A1**. It detects **zero of twelve S4-only rows**; HGB detects one of twelve. Both models miss eleven of the sixteen S4 rows. No causal attribution of the four detections to the overlapping family is asserted.

Detected and missed groups both have median band count **4** and coverage **35** days. Their median current amounts are nearly equal: **841,001 versus 841,699 cents**. Every current amount is in the frozen analytical band. Current value or band count alone therefore does not separate these observed outcomes. XGBoost's S4-only missed scores range .0243–.3147, median .1409. The twelve misses span eight subjects/eight clusters; seven occur in one community. This is sparse, dependent evidence, not twelve independent experiments.

Recent band variation, historical band frequency and baseline support are not generally available from X. The omitted recent total count/share deserve a more careful conclusion: they are indirectly recoverable from the existing S2 count/share fields, as explained below. Train S4-only recall is also weak: XGBoost 13/99 and HGB 39/99. Limited Train support (128 positives total), missing historical/variation information and learned approximation are all relevant; no single cause or guaranteed remedy is established.

### A4 — AgentFlowImbalance

XGBoost detects 151/222; HGB 197/222. **HGB detects 46 of XGBoost's 71 misses and loses none of its A4 detections.** All XGBoost A4 misses are exclusive-family rows; its exclusive A4 recall is 80/151, versus HGB 126/151. This demonstrates a material configuration/model difference with unchanged representation; it does not establish HGB's superiority on every family or an unseen population.

The recent cash count median is **8 detected versus 6 missed**, placing the missed median at the frozen minimum. Median absolute count skew is .7143 versus .6667; median absolute historical value-skew change is 1.0083 versus .8172. However, median absolute recent value skew is **.9400 detected versus .9589 missed**: misses are not uniformly weaker value imbalance. All six recent primitives and historical change markers are available. Cash counts/values allow count/value skew and sign agreement to be expressed; the complete target's ingredients are present in principle. No missing-history explanation is supported for these A4-positive rows.

The 71 misses cover thirteen agents and 62 clusters; five agents account for 74.6% of misses. Model approximation of the compound arithmetic and population/support concentration are better-supported concerns than asserting that a missing A4 feature caused the failures. A future full-trigger feature or gate relaxation would violate the frozen policy and is not proposed.

### N1 — ManyToOneCollection

XGBoost detects 77/101; HGB 85/101. HGB recovers eight XGBoost misses with no reverse losses. All 24 XGBoost misses are N1-only rows; exclusive recall is 65/89. Their median incoming count is **5 versus 7** among detections; median sender breadth **3 versus 4**; median current value **3,088.5 versus 6,096 cents**. Relevant acceleration is available throughout.

Recent aggregate incoming value is omitted, so current value can be an imperfect substitute for the required sum. In this cohort acceleration equals recent count for 101/101 Validation positives and 411/414 Train positives, consistent with the declared denominator floor in sparse baselines. This is component dependence, not evidence of an undeclared leak. Count/breadth and amount contrasts are observed associations; exact sum-based error causation was not measured.

### A2 — AgentWalletConcentration

XGBoost detects 109/148; HGB 123/148. HGB recovers sixteen XGBoost misses, while XGBoost recovers two HGB misses. Exclusive A2 recall is 57/96 versus HGB 71/96. XGBoost's 39 misses span eleven agents/26 clusters; five agents account for 71.8% of misses.

Detected versus missed median top-two share is .7778 versus .7500. Historical share change medians are .6325 versus .6232; **every missed positive has change at least .5167**, well above .20. A near-change-threshold explanation is unsupported. Both supplied concentration fields are observed. Absolute 24h service count is absent, although the target requires at least eight. That is a genuine information gap, while the HGB comparison also shows model-specific approximation differences. Neither observation assigns a causal proportion to the 39 misses.

### Training versus Validation context

| Family | XGB Train | XGB Validation | HGB Train | HGB Validation |
| --- | --- | --- | --- | --- |
| S2 | 68/112 (0.607) | 11/23 (0.478) | 91/112 (0.812) | 13/23 (0.565) |
| S4 | 42/128 (0.328) | 4/16 (0.250) | 68/128 (0.531) | 5/16 (0.312) |
| A4 | 591/812 (0.728) | 151/222 (0.680) | 767/812 (0.945) | 197/222 (0.887) |
| N1 | 356/414 (0.860) | 77/101 (0.762) | 374/414 (0.903) | 85/101 (0.842) |
| A2 | 610/755 (0.808) | 109/148 (0.736) | 660/755 (0.874) | 123/148 (0.831) |

Weak Train S2/S4 performance supports a representation/approximation/support concern, not simply a held-out drift claim. A4's large HGB advantage appears on Train and Validation. Sparse samples and shared synthetic mechanisms prevent assigning these differences to one cause. No new configurations were tried to test a causal explanation.

## 5. What the forty fields do and do not represent

Named-feature omissions are not automatically missing information. The following review considers all forty fields together, including exact-aggregate algebra. It does not amend or reconstruct model X.

| Family | Assessment | Reason |
| --- | --- | --- |
| S1 | Components available, one indirectly | Although distinct amount count is absent, variation>=2 is equivalent to n*max_share>1 for positive amounts (exact-aggregate algebra). Thus its binary variation gate is recoverable from count and max share; do not call the omitted count an irreducible gap. Float64 precision remains the saved contract. |
| S2 | Genuine omitted information and sparse support | Recent cluster count/share/current amount present. Exact cluster sum, baseline similar count/rate and exact S2 historical support are not generally recoverable. Current amount times count approximates but does not equal the sum under 5% tolerance. Coverage 35 alone cannot encode baseline event support. |
| S3 | Genuine omitted information | Day count/hour breadth and historical daily growth present; current-day total value is not generally recoverable from the one-hour sum. |
| S4 | Genuine omissions plus recoverable cross-field quantities | Current band and band count present. n(R7d)=S2 similar-count/similar-share because current always belongs to its own cluster; band share follows by dividing band count by that n. These are not necessarily missing information. Band amount variation, baseline band frequency and exact S4 baseline support remain absent. |
| N1 | Genuine omitted information | Directed count, breadth and acceleration/historical marker present; recent incoming total value absent. Current amount alone is not the historical sum. |
| N2 | Genuine omitted information | Directed count, breadth and acceleration/historical marker present; recent outgoing total value absent. |
| N3 | Demonstrated lossy summary | All-path count and minimum length do not expose all monetary routes. Seven Validation positives have selected summaries incompatible with amount bounds; four are missed. This co-occurrence is not causal attribution of four misses. |
| N4 | Conditional reconstructability; degenerate information gap | Let q=(Oprior+a)/F and r=F-Oprior. F=(a-r)/(q-1) when q!=1; when q=1, a=r and F remains unidentified by these quantities. Thus the F>=10000 gate is not guaranteed recoverable from the N4 fields. No numerical reconstruction is substituted into X. |
| A1 | All compound-gate ingredients supplied | Growth, D, new count/share and historical missing marker expose all A1 components. Perfect observed recall and high growth importance are consistent with alignment, not private intent leakage by themselves. |
| A2 | Genuine omitted information plus model-specific weakness | Top2 share, change and historical marker present; absolute recent service count>=8 not supplied. Both detected/missed positives have large change, so a near-change-threshold explanation is unsupported. |
| A3 | Conditional count information | Recent breadth and acceleration/history marker present. Absolute count is not explicit; acceleration equals count when the denominator floor is active, but baseline count is not supplied to establish that identity universally. |
| A4 | Arithmetic ingredients supplied; learning/support issue remains | Cash counts, values, distinct wallets, signed historical change and current type permit count/value skew, agreement and eligibility checks. The frozen fields support the compound rule in principle; HGB rescues 46/71 XGB Validation misses without feature changes. This cannot prove a universal algorithm advantage or identify an exact fitting cause. |

For S1, all positive amounts are identical exactly when `n × max_share = 1`; variation is present when that product is greater than one. Thus the binary variation condition can be inferred even though the exact number of amount values is not supplied. For S4, the current always belongs to its own similar cluster, so similar share is positive and `n(R7d)=similar_count/similar_share`; the near-band share follows from that count. These algebraic observations clarify the frozen report's list of omitted named fields without rewriting it or changing semantics. On saved data the derived count differs from its nearest integer by at most about 7.1e-15 due to float representation. No new field was created.

N3 provides direct empirical evidence of loss: **7/130 Validation positives** have selected-path summaries outside the complete target's monetary bounds, despite a qualifying path existing under the saved family label. Three are detected, four missed; total N3 misses are eight. Train has 39/550 such cases, including 24 of 34 N3 misses. This demonstrates a representation limitation, but the intersection is not proof that the limitation caused those errors. N3's displayed path is not the whole existential target.

For N4, the funding amount can be derived from current amount, pass-through ratio and residual except at the degenerate ratio of one. That exceptional case prevents a universal sufficiency claim for the funding minimum. This static limitation is not a measured attribution of N4's 21 Validation misses.

### Four kinds of explanation kept separate

| Category | Supported finding | What remains unproven |
| --- | --- | --- |
| Representation limitation | S2/S4 omitted historical/variation/value information; N1 aggregate value; A2 absolute services; observed N3 selected-route loss | Which missing quantity caused an individual prediction, or what future gain it would yield |
| Limited support | Nine count shortfalls, few S2/S4 subjects/clusters, three Validation units | That more rows alone would fix learning or preserve realistic overlap |
| Model/configuration weakness | Paired HGB rescues 46 A4 and 16 A2 misses with the same fields; XGB rescues nine HGB N3 misses | General superiority, the particular parameter responsible, or transport to fresh data |
| Synthetic shortcut risk | Strong growth dependence, overlapping-family credit, role/origin associations and conditional component redundancy | Hidden private/future leakage or a causal fraction of score attributable to generation artifacts |

Cold-start is not the explanation for these own-family false negatives: the saved positive label already requires that family's eligibility, and relevant supplied markers in the priority cases are observed. Ineligible histories can still create positives through another family. Target-0 ineligible rows do not certify benign behaviour; this benchmark cannot measure unobserved suspicion that its target declares ineligible. Missing values in an unrelated domain must not be mistaken for lack of history in the active family.

Evidence: [feature_representation_limitations.json](../evidence/stage19/feature_representation_limitations.json), [representation_observations.json](../evidence/stage19/representation_observations.json), [component_relationships.json](../evidence/stage19/component_relationships.json).

## 6. Error concentration and community limits

The 292 Validation false negatives span **143 wallet subjects, 203 episode/background-day clusters and 116 UTC days**. The largest cluster contributes five errors (1.7%); the largest wallet contributes eight (2.7%). Community counts are 110/1,027 positive rows, 93/1,016 and 89/987. This is spread across all three units, although family-specific concentration remains substantial.

The current-agent grouping includes ninety misses with no agent. `NO_AGENT` is a role-absence category, not an entity. The remaining 202 misses occur on transactions naming 23 agents. Wallet-subject here means sender for W2W and serviced wallet for cash; family-specific N1 concentration uses receiver, agent families use agent, and N3 uses the current-sender subject convention from Stage 16S. These are descriptive grouping choices, not counts of independent paths or investigators.

| Family | FN | Subjects with FN / supported | Clusters with FN / supported | Largest subject share of FN | Top-five subject share |
| --- | ---: | ---: | ---: | ---: | ---: |
| S2 | 12 | 6/7 | 6/7 | 25.0% | 91.7% |
| S4 | 12 | 8/12 | 8/12 | 25.0% | 75.0% |
| A4 | 71 | 13/17 | 62/138 | 22.5% | 74.6% |
| N1 | 24 | 15/28 | 17/42 | 12.5% | 45.8% |
| A2 | 39 | 11/20 | 26/60 | 20.5% | 71.8% |

Episode clusters use stored scenario IDs; non-episode clusters use unit × UTC day. Background days, episodes, subjects and communities are not additive independent samples. Evidence includes each leading group's positive support and miss rate so high error volume is not confused with high conditional error probability.

## 7. Synthetic shortcuts and robustness

Stage 18's fixed diagnostics are reused, with no rerun of permutations or fitting. For XGBoost, growth supplies 37.7% of absolute permutation mass and the agent group about 76.2%. Matched growth removal reduced Macro F1 by .07815, from .95667 to .87852. A1 has all target ingredients exposed and dominates positive support; valid component alignment can explain strong performance without private/future leakage.

Eligible-only Pearson correlation between growth and new-wallet count is about **.740 Train / .705 Validation**; recent distinct and new count correlate about .617/.606. Correlated components share importance and off-manifold permutations can distort its magnitude. These are descriptive associations, not causal effects. The saved 3,000-row importance sample has only seven S2 and three S4 positives, limiting family-specific interpretation.

The saved missingness-only HGB has Validation AP .2856 and Macro F1 .4588; growth-only AP .5896; four-A1-field AP .6618; Train-label-shuffle AP .2406 with no positive predictions at .50. These checks demonstrate that restricted summaries carry some signal but do not reproduce full performance. They are neither independent validation nor proof that every shortcut is absent. No duplicate features were introduced to dilute importance and no sentinel policy was changed.

Selected Validation recall/FPR by type is approximately .8948/.01357 for W2W, .9127/.00471 for Cash-In, .9096/.00624 for Cash-Out. Motif/context/background-only role strata have different prevalence and FPR: motif 28.5%/.01746, context 24.0%/.01633, no-episode role 10.9%/.00146. These associations are consistent with deliberately enriched opportunity construction. They do not show that the model read provenance: origin, role and identity are absent from X. No private intent is inferred.

Original Stage 16S evidence documents zero accounting failures in the retained development draw; there is no support for attributing these model false negatives to dropped or infeasible transactions. Its eligibility/opportunity attrition findings describe why positives are scarce, not why a fitted model misclassified an existing positive. This distinction is preserved.

The exact legitimate-growth-origin and boundary mechanisms cannot be replaced with an archetype label. No private history or new family trigger was reconstructed to create those slices. Their unresolved detail, three communities and repeated Validation use restrict any no-shortcut or generalization claim.

Evidence: [synthetic_shortcut_assessment.json](../evidence/stage19/synthetic_shortcut_assessment.json), [synthetic_population_slices.json](../evidence/stage19/synthetic_population_slices.json), [family_overlap_attribution.json](../evidence/stage19/family_overlap_attribution.json).

## 8. Support and uncertainty remain unresolved

| Family | Train / minimum (achieved) | Validation / minimum (achieved) | Validation subjects / clusters | Count policy |
| --- | ---: | ---: | ---: | --- |
| S1 | 456/1200 (38.0%) | 132/300 (44.0%) | 31 / 34 | Shortfall |
| S2 | 112/1200 (9.3%) | 23/300 (7.7%) | 7 / 7 | Shortfall |
| S3 | 2292/1200 (191.0%) | 546/300 (182.0%) | 104 / 156 | Met |
| S4 | 128/1200 (10.7%) | 16/300 (5.3%) | 12 / 12 | Shortfall |
| N1 | 414/1200 (34.5%) | 101/300 (33.7%) | 28 / 42 | Shortfall |
| N2 | 1690/1200 (140.8%) | 429/300 (143.0%) | 86 / 147 | Met |
| N3 | 550/1200 (45.8%) | 130/300 (43.3%) | 87 / 111 | Shortfall |
| N4 | 559/1200 (46.6%) | 144/300 (48.0%) | 74 / 91 | Shortfall |
| A1 | 5773/1200 (481.1%) | 1467/300 (489.0%) | 23 / 570 | Met |
| A2 | 755/1200 (62.9%) | 148/300 (49.3%) | 20 / 60 | Shortfall |
| A3 | 883/1200 (73.6%) | 255/300 (85.0%) | 18 / 80 | Shortfall |
| A4 | 812/1200 (67.7%) | 222/300 (74.0%) | 17 / 138 | Shortfall |

The nine shortfalls S1/S2/S4/N1/N3/N4/A2/A3/A4 remain exactly as recorded. Validation diversity objectives are ≥20 subjects and ≥30 clusters; S2/S4 fall far short, and A3/A4 have fewer than twenty agents. Original sealed support-policy FAIL certificates are unchanged and provide no private family counts.

Descriptive Wilson 95% intervals for selected Validation recall are approximately S2 [.292,.670], S4 [.102,.495], A4 [.616,.738], N1 [.671,.835], A2 [.660,.801]. These assume independent observations and are optimistic as population uncertainty statements given clustering and reuse. S4-only 0/12 is observed failure on those twelve rows, not a proof of zero sensitivity in all populations. No row-wise bootstrap, significance claim or reliable cluster interval is manufactured from three units.

See [sparse_support_uncertainty.json](../evidence/stage19/sparse_support_uncertainty.json). Technical feature/model execution validity remains distinct from statistical adequacy. This stage does not claim a validated model.

## 9. Ranked improvement options — none implemented

| Rank and option | Expected benefit / scientific basis | Required data | Version / refit / amendment | Risks and independent-evaluation impact |
| --- | --- | --- | --- | --- |
| 1. Versioned feature-amendment design while preserving candidates | Address specific irrecoverable S2/S4 components before paying for more fits; keep A4 model-learning issue separate | Existing design and authorized diagnostics; independently specified fixtures only if later authorized | No new dataset needed for design; new feature/experiment version and explicit amendment required; future effectiveness test requires authorized refits | More direct rule components may make the synthetic task easier without external value; Stage16T forty-field compatibility must be amended before affected generation/evaluation |
| 2. Retain current XGBoost with restricted claims and preserve HGB | Lowest immediate cost; transparent fixed-policy binary development reference | Saved artifacts/predictions | No version/refit/amendment to retain; candidate replacement needs separate decision | Known family weakness persists; no full-family adequacy or independent-readiness claim |
| 3. Targeted additional observable error review | Resolve particular ambiguity/approximation hypotheses before implementation | Existing development histories, fixed scores and annotations under explicit diagnostic scope | No new dataset/refit; input changes still require amendment | Further Validation reuse; cannot infer improvement causally or search thresholds from inspected examples |
| 4. Provision independent custody and pursue the planned challenge | Obtain separate family/domain evidence with fresh communities | Verified independent administration, access controls, registry, logging and frozen implementation; new challenge only after approval | Separate challenge dataset; no challenge refitting; protocol compatibility review required if feature schema changes | Custody is unavailable; challenge support can fail; enriched results do not repair original holdouts or imply natural prevalence |
| 5. New versioned development population only if scientifically necessary | Improve sparse opportunities and entity/episode diversity when feature information alone is insufficient | Prospective population law, fixed budget/seed policy, actual-support/diversity audit | New dataset/experiment, separately approved generation/refitting; preserve original draw and targets | Avoid unnecessary repeated generation, positive manufacturing, easy signatures, support-based retries and prevalence pooling |
| 6. Future constrained model/robustness experiment | Test A4/A2 approximation and network trade-offs under a preregistered utility rule | Approved representation, budget and evaluation plan | Refits require new authorization and explicit treatment of the inherited 36-fit cap and expired unused Stage18 slots | No automatic counter reset/reuse; risk of adaptive Validation tuning; freeze before independent access |

The rankings reflect scientific evidence and cost, not promised metric gains. The full option records specify benefits, limitations, data needs, versioning, refits, amendments and evaluation implications in [ranked_improvement_options.json](../evidence/stage19/ranked_improvement_options.json).

## 10. Recommended next development stage

Recommend a separately authorized **Stage 20 controlled feature-representation amendment design and compatibility review**, with no fitting, extraction or generation in that design stage.

1. Prioritize S2 exact recent-cluster value and prior cluster support/rate, and S4 band variation and prior band activity/support, as causal lower-level quantities. Do not add complete family triggers, private context or redundant columns merely to reduce importance concentration.
2. Prove which information is absent versus algebraically recoverable before increasing dimension. Preserve the current forty-field version. Review N1 aggregate value, A2 service count and N3 alternative-route summaries secondarily; a proposed N3 field must not select/count fully qualifying paths or use the complete target conjunction.
3. Keep A4's existing primitive sufficiency separate from model-family trade-offs; do not weaken imbalance gates or add a full A4 flag. Preserve XGBoost's selection and HGB's comparator role until a separately approved decision.
4. Specify names, exact causal windows, eligibility/missingness, direct-component disclosure, dimension, hand fixtures and compatibility for any future feature version. No code or matrix change follows from this recommendation alone.
5. Explicitly address Stage16T's frozen forty-field challenge contract before any affected generation or evaluation. A new feature version cannot silently inherit compatibility. Independent custody and original quarantines remain mandatory.
6. Require a later preregistered modeling authorization if the design is accepted. Stage18's twenty unused slots expired; they are not permission to start new fits. Preserve the existing sixteen-fit ledger and resolve budget/versioning explicitly rather than resetting the count.

Keep the existing production draw unchanged. Consider a new development population only after the information/support review justifies it. Never accept-until-support, oversample to claim independent support, relabel, lower predicates or use sealed outcomes to guide a redesign. The recommendation and future acceptance checks are in [recommended_next_stage.json](../evidence/stage19/recommended_next_stage.json).

## 11. Preservation, outputs and limitations

**219 named protected files** match before/after hashes, including Stage18 artifacts and fit ledger, Stage17 matrices, frozen development data/labels/annotations, design and prior evidence, V1 model and V3 experimental integration. The final artifact manifest binds new Stage19 source, report and evidence. This is an explicit scope, not every file on disk. Sealed bytes are unread and excluded.

Stage16V's incomplete broader Stage15A historical snapshot remains documented; no archive restoration, historical manifest rewrite or security weakening was performed. No Flask, MySQL, API or dashboard file changed. Existing policies and previous reports remain intact.

New writes are confined to the four Stage19 diagnostic/report scripts under `ml_v4/development_analysis/`, this report and `ml_v4/evidence/stage19/`. The scripts use saved matrices and predictions, create aggregate diagnostic summaries and preserve traceable FN IDs. Derived arithmetic summaries are not added to X. Historical inputs and earlier-stage evidence remain unchanged; no candidate schedule, model prediction, learned transformation or additional fit is produced.

Key outputs cover [result verification](../evidence/stage19/model_results_verification.json), [false negatives](../evidence/stage19/false_negative_analysis.json), [S2/S4 investigation](../evidence/stage19/s2_s4_investigation.json), [family/domain errors](../evidence/stage19/family_domain_error_analysis.json), [representation](../evidence/stage19/feature_representation_limitations.json), [shortcuts](../evidence/stage19/synthetic_shortcut_assessment.json), [paired comparison](../evidence/stage19/xgboost_hgb_comparison.json), [uncertainty](../evidence/stage19/sparse_support_uncertainty.json), [options](../evidence/stage19/ranked_improvement_options.json), [preservation](../evidence/stage19/preservation_verification.json), [next-stage recommendation](../evidence/stage19/recommended_next_stage.json), and [decision/hash manifest](../evidence/stage19/stage19_decision.json).

Remaining limits include incomplete causal attribution of individual errors, omitted-history components not reconstructed row by row, synthetic population assumptions, sparse dependent families, repeated Validation inspection and no independent external audit. None prevents a bounded diagnostic decision and design recommendation; all prevent claiming proven real-world effectiveness or independent generalization.

## 12. Final decision

**A — DEVELOPMENT ANALYSIS COMPLETE; IMPROVEMENT PLAN READY**

The saved results are verified, principal weaknesses are characterized and a ranked plan is ready for review. XGBoost remains selected; HGB remains the comparator. This decision authorizes **no training/refitting, feature changes, dataset generation, threshold optimization, evaluation or application integration**. No next stage has started.

V4 STAGE 19 COMPLETE — WAITING FOR APPROVAL.
