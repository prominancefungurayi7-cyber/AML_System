# MODEL V4 — STAGE 16S FAMILY-SUPPORT FAILURE REVIEW

## 1. Executive finding

**B — ADDITIONAL INDEPENDENT CHALLENGE EVALUATION REQUIRED.**

The frozen draw is technically usable development evidence, but it does **not** satisfy the original full-family independent-evaluation objective. Nine families miss the decision-point minimum in both development partitions. Validation S2/S4 additionally have only 7/12 subjects and 7/12 clusters; A3/A4 have only 18/17 subjects. Passing aggregate prevalence does not cure these deficits. No model has been trained or validated in this stage.

Recommend preserving V4 and designing a separately versioned independent challenge extension (Option D using the Option B pathway). This is a recommendation, not execution authorization. If the unchanged original population-wide full-family evaluation claim is mandatory, a new experiment is needed. The current sealed holdouts cannot satisfy their original support policy.

## 2. Scope, authority and method

Read frozen Stage 15 design/acceptance/support/target/holdout policies, Stage 15A amendment, Stage 16R report, generator/evaluator source, Train/Validation audits and named public certificates. All source and development inputs are hashed before and after. Only existing Train/Validation observables, family evidence and diagnostic provenance are analyzed. No generator is imported or called; no random stream, feature matrix, model, revised label or threshold is created.

Supports use frozen family flags. Six fixed 30-day blocks start at the scored horizon; daily and block maxima summarize temporal concentration. Subject and cluster maxima are descriptive dependence measures. Episode clusters use stored IDs; background clusters use unit × UTC day. Pairwise overlap is reproduced in JSON; overlapping rows must not be summed. Eligibility reasons use frozen evaluator output. Additional S2/S4/A4 condition checks use exact rational comparisons on eligible own-origin motif rows and must reproduce their stored family result. N3 checks topology separately on own-origin motif rows, with no amount filter or path truncation. These are aggregate diagnostics, not model inputs.

## 3. All-family support and concentration

| Partition | Family | Minimum | Actual | Achieved % | Subjects | Clusters | Max subject % | Top 5 subjects % | Max cluster % | Max day % | Max 30d % | Other-predicate overlap |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| train | S1 | 1200 | 456 | 38.0 | 132 | 147 | 4.8 | 17.8 | 3.3 | 3.9 | 21.3 | 239 |
| train | S2 | 1200 | 112 | 9.3 | 37 | 43 | 7.1 | 30.4 | 7.1 | 6.2 | 25.9 | 20 |
| train | S3 | 1200 | 2292 | 191.0 | 397 | 673 | 1.7 | 6.1 | 0.7 | 1.9 | 18.4 | 1107 |
| train | S4 | 1200 | 128 | 10.7 | 54 | 57 | 5.5 | 22.7 | 4.7 | 3.9 | 25.0 | 29 |
| train | N1 | 1200 | 414 | 34.5 | 116 | 187 | 2.9 | 13.8 | 2.4 | 3.1 | 23.7 | 45 |
| train | N2 | 1200 | 1690 | 140.8 | 333 | 582 | 2.4 | 8.2 | 0.7 | 1.6 | 19.5 | 930 |
| train | N3 | 1200 | 550 | 45.8 | 355 | 453 | 1.8 | 6.2 | 1.1 | 2.4 | 19.3 | 101 |
| train | N4 | 1200 | 559 | 46.6 | 258 | 348 | 2.7 | 9.1 | 2.1 | 2.1 | 20.2 | 151 |
| train | A1 | 1200 | 5773 | 481.1 | 90 | 2273 | 2.1 | 10.2 | 0.3 | 1.5 | 19.7 | 729 |
| train | A2 | 1200 | 755 | 62.9 | 74 | 339 | 6.0 | 22.5 | 1.9 | 2.8 | 21.9 | 261 |
| train | A3 | 1200 | 883 | 73.6 | 77 | 249 | 5.7 | 21.5 | 1.6 | 4.1 | 22.0 | 318 |
| train | A4 | 1200 | 812 | 67.7 | 75 | 466 | 7.9 | 24.6 | 1.0 | 2.3 | 18.8 | 229 |
| validation | S1 | 300 | 132 | 44.0 | 31 | 34 | 12.1 | 45.5 | 11.4 | 12.1 | 27.3 | 85 |
| validation | S2 | 300 | 23 | 7.7 | 7 | 7 | 34.8 | 91.3 | 34.8 | 13.0 | 65.2 | 0 |
| validation | S3 | 300 | 546 | 182.0 | 104 | 156 | 5.7 | 18.1 | 2.2 | 4.0 | 26.6 | 251 |
| validation | S4 | 300 | 16 | 5.3 | 12 | 12 | 18.8 | 56.2 | 18.8 | 18.8 | 25.0 | 4 |
| validation | N1 | 300 | 101 | 33.7 | 28 | 42 | 8.9 | 38.6 | 7.9 | 11.9 | 34.7 | 12 |
| validation | N2 | 300 | 429 | 143.0 | 86 | 147 | 6.8 | 22.6 | 2.6 | 3.3 | 22.8 | 231 |
| validation | N3 | 300 | 130 | 43.3 | 87 | 111 | 3.8 | 16.9 | 3.1 | 3.8 | 23.1 | 31 |
| validation | N4 | 300 | 144 | 48.0 | 74 | 91 | 6.2 | 22.2 | 5.6 | 5.6 | 30.6 | 54 |
| validation | A1 | 300 | 1467 | 489.0 | 23 | 570 | 8.3 | 38.3 | 1.1 | 2.0 | 23.9 | 214 |
| validation | A2 | 300 | 148 | 49.3 | 20 | 60 | 14.9 | 51.4 | 7.4 | 9.5 | 41.2 | 52 |
| validation | A3 | 300 | 255 | 85.0 | 18 | 80 | 19.6 | 56.5 | 5.1 | 6.7 | 25.5 | 107 |
| validation | A4 | 300 | 222 | 74.0 | 17 | 138 | 21.6 | 65.3 | 4.5 | 5.0 | 35.6 | 71 |

Validation/Final diversity objectives are ≥20 subjects and ≥30 clusters per family; Independent objectives are ≥12 and ≥20. There is no separately declared Train subject/cluster minimum. Only S3, N2 and A1 meet both development decision-count minima. A1 exceeds its planning upper range; this is not a deletion trigger. Exact temporal block counts, unit counts, exclusive-family support, full pairwise overlaps and origins are in [development evidence](../evidence/stage16s/development_support_review.json).

## 4. Opportunity, composition and eligibility

The table concerns each family’s own intended origin, not all positives or matched hard origins. E includes motif and context rows; M is only the motif budget. Eligibility is checked on the realized causal ledger. Rows early in a motif may lack accumulated evidence even when the completed motif looks strong. No counterfactual generation was used.

| Partition | Family | Episodes | E | M | Context | Eligible motif | Own motif family positives | Own context family positives | Positive rows outside own origin |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| train | S1 | 116 | 1586 | 890 | 696 | 686 | 71 | 112 | 273 |
| train | S2 | 227 | 3174 | 1672 | 1502 | 1361 | 52 | 0 | 60 |
| train | S3 | 113 | 1576 | 1086 | 490 | 950 | 352 | 159 | 1781 |
| train | S4 | 228 | 3174 | 1854 | 1320 | 1464 | 82 | 0 | 46 |
| train | N1 | 118 | 1562 | 891 | 671 | 590 | 234 | 2 | 178 |
| train | N2 | 114 | 1576 | 864 | 712 | 479 | 216 | 122 | 1352 |
| train | N3 | 228 | 3170 | 1151 | 2019 | 1151 | 83 | 27 | 440 |
| train | N4 | 116 | 1569 | 889 | 680 | 796 | 56 | 35 | 468 |
| train | A1 | 115 | 1580 | 1282 | 298 | 1274 | 339 | 35 | 5399 |
| train | A2 | 114 | 1574 | 1231 | 343 | 1231 | 44 | 1 | 710 |
| train | A3 | 109 | 1564 | 1038 | 526 | 1037 | 472 | 20 | 391 |
| train | A4 | 113 | 1560 | 1264 | 296 | 1250 | 159 | 5 | 648 |
| validation | S1 | 30 | 395 | 235 | 160 | 166 | 29 | 28 | 75 |
| validation | S2 | 54 | 791 | 398 | 393 | 290 | 7 | 0 | 16 |
| validation | S3 | 27 | 391 | 250 | 141 | 216 | 69 | 53 | 424 |
| validation | S4 | 61 | 787 | 473 | 314 | 361 | 11 | 0 | 5 |
| validation | N1 | 27 | 387 | 225 | 162 | 135 | 70 | 0 | 31 |
| validation | N2 | 27 | 389 | 211 | 178 | 124 | 58 | 36 | 335 |
| validation | N3 | 61 | 795 | 317 | 478 | 317 | 20 | 6 | 104 |
| validation | N4 | 27 | 395 | 277 | 118 | 254 | 10 | 3 | 131 |
| validation | A1 | 27 | 391 | 300 | 91 | 300 | 53 | 11 | 1403 |
| validation | A2 | 28 | 392 | 309 | 83 | 309 | 6 | 1 | 141 |
| validation | A3 | 27 | 392 | 226 | 166 | 226 | 91 | 7 | 157 |
| validation | A4 | 27 | 390 | 299 | 91 | 299 | 29 | 4 | 189 |

The achieved yield shows insufficient *effective positive opportunities* for nine objectives, not proof that the total transaction budget alone is too small. Historical eligibility and full-rule attrition are distinct: subtract eligible motif from M for the former, then positives from eligible motif for the latter. For N4, lack of an incoming anchor is not insufficient 28/35-day history. Role inapplicability is likewise distinct from age. Background and matched hard origins can add positive support; origin never assigns a label.

### Focused compound-condition audit

Failures below are **nonexclusive**, conditional on eligible own-origin motif rows. Their sum can exceed the denominator. Conditions are not called unjustifiably restrictive: these are the declared research rules. Removing a failed gate would change the task, which this stage does not recommend or perform.

| Partition | Family | Eligible own motif N | All gates pass | Failed condition | Failure count | Sole failure count |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| train | S2 | 1361 | 52 | cluster_count_ge4 | 1006 | 13 |
| train | S2 | 1361 | 52 | cluster_value_ge20000 | 1008 | 49 |
| train | S2 | 1361 | 52 | cluster_share_ge0.6 | 1189 | 120 |
| train | S2 | 1361 | 52 | cluster_growth_ge2 | 443 | 0 |
| train | S4 | 1464 | 82 | current_in_band | 905 | 38 |
| train | S4 | 1464 | 82 | band_count_ge3 | 1005 | 14 |
| train | S4 | 1464 | 82 | band_variation_ge2 | 690 | 0 |
| train | S4 | 1464 | 82 | band_share_ge0.4 | 1268 | 161 |
| train | S4 | 1464 | 82 | band_growth_ge2 | 695 | 0 |
| train | S4 | 1464 | 82 | recent_count_ge5 | 245 | 3 |
| train | A4 | 1250 | 159 | cash_count_ge6 | 354 | 99 |
| train | A4 | 1250 | 159 | cash_wallets_ge3 | 113 | 5 |
| train | A4 | 1250 | 159 | abs_count_skew_ge0.5 | 765 | 191 |
| train | A4 | 1250 | 159 | sign_agreement | 401 | 18 |
| train | A4 | 1250 | 159 | skew_change_ge0.4 | 364 | 30 |
| train | A4 | 1250 | 159 | abs_value_skew_ge0.6 | 411 | 17 |
| validation | S2 | 290 | 7 | cluster_count_ge4 | 225 | 2 |
| validation | S2 | 290 | 7 | cluster_value_ge20000 | 229 | 8 |
| validation | S2 | 290 | 7 | cluster_share_ge0.6 | 260 | 21 |
| validation | S2 | 290 | 7 | cluster_growth_ge2 | 98 | 0 |
| validation | S4 | 361 | 11 | current_in_band | 232 | 7 |
| validation | S4 | 361 | 11 | recent_count_ge5 | 76 | 0 |
| validation | S4 | 361 | 11 | band_count_ge3 | 287 | 5 |
| validation | S4 | 361 | 11 | band_variation_ge2 | 171 | 0 |
| validation | S4 | 361 | 11 | band_share_ge0.4 | 311 | 34 |
| validation | S4 | 361 | 11 | band_growth_ge2 | 171 | 0 |
| validation | A4 | 299 | 29 | cash_count_ge6 | 86 | 15 |
| validation | A4 | 299 | 29 | sign_agreement | 103 | 1 |
| validation | A4 | 299 | 29 | abs_value_skew_ge0.6 | 140 | 5 |
| validation | A4 | 299 | 29 | abs_count_skew_ge0.5 | 167 | 27 |
| validation | A4 | 299 | 29 | skew_change_ge0.4 | 78 | 24 |
| validation | A4 | 299 | 29 | cash_wallets_ge3 | 43 | 2 |

### N3: topology versus monetary conjunction

| Partition | Own motif rows | No chronological return topology | Topology present but full amount conjunction fails | Full predicate positive |
| --- | ---: | ---: | ---: | ---: |
| train | 1151 | 844 | 224 | 83 |
| validation | 317 | 221 | 76 | 20 |

A topology can fail amount conditions on every candidate route; this table does not identify a single offending edge or causal percentage. The target has no long-baseline gate, so N3 scarcity cannot be attributed to a 35-day eligibility requirement.

### Family-specific interpretation

**S1:** Own opportunities use a dispersed share of one base-mixture total; the target additionally requires USD 300 total, four causal recent events, variation, limited maximum share and eligible history. Source supports this mechanism, but no S1 gate-by-gate causal allocation is estimated.

**S2:** Fresh jittered motif amounts need not leave four payments within the current-centered 5% band; cluster value and 60% share must also pass. Context and ordinary activity enter the denominator. The measured gate failures below distinguish this attrition from historical ineligibility.

**S3:** Minimum decision-point support is met. Day boundaries and occupied-hour/value/history conjunction still filter opportunities; success does not establish independent precision or all-domain reliability.

**S4:** The conditional USD 5000..13000 recipe is wider than the target band. A current in-band payment, three in-band rows, 40% share, variation, rate increase and history must coincide. The condition audit quantifies overlap among failures without treating them as independent causes.

**N1:** Incoming collection requires prior receiver-specific directed support, three senders, four recent edges and sufficient value. Two-to-eight partner opportunities and context are not guaranteed positive decisions. Eligibility and own-origin counts identify observed attrition; relative causal effects remain unestimated.

**N2:** Minimum support is met, with positives also arising outside intended N2 episodes. Overlap with other predicates enriches supervision but does not create independent observations.

**N3:** No long-history eligibility gate exists for W2W. Early walk events need not close a chronological return route; reversed ordering and broad amount factors can defeat a full path. Topology-present versus amount-conjunction failure is measured on own motif rows. Absence of a qualifying path is not evidence of accounting loss.

**N4:** A prior incoming-W2W anchor, funding minimum, outward fraction and remaining-funding conjunction are required. A funding proposal itself is not an outward detection, and shared small-value draws may not reach the funding minimum. No gate-specific counterfactual effect is claimed.

**A1:** Minimum support is met and many positives originate outside A1 episodes. This dominant support cannot substitute for sparse agent families or establish operational specificity.

**A2:** Top-two concentration and change from its own baseline must coincide after eight recent services and historical support. Choosing two-to-six customers with shares 0.35..0.90 is broader than the target conjunction; intended opportunities are not labels.

**A3:** A 0.25..3-hour motif can extend beyond the one-hour target window; count, breadth and baseline conditions also apply. Validation subject breadth is below its objective. No temporal-duration intervention was performed.

**A4:** Cash event count, distinct wallets, value skew, count skew, sign agreement and historical skew change must all hold. Random direction probabilities and heterogeneous amounts are not guarantees of the joint imbalance. The measured eligible-motif failures identify limiting conditions, while subject breadth is also insufficient.

### Accounting, overlap and diversity

Stage 16R independent ledger checks report zero schema/cross-unit errors and no capacity failure. The generator stops on negative inventory rather than dropping or resampling transactions. Thus no evidence supports accounting attrition as the support-loss mechanism. Numerical amount bounds rejection did occur; it changes proposals under the frozen law, not labels. Its causal effect on family yield is unmeasured.

train: minimum inventory 85241688 cents; recorded numerical proposal rejections 17. These counters do not identify rejected positive cases; no such labels were evaluated.

validation: minimum inventory 87624538 cents; recorded numerical proposal rejections 5. These counters do not identify rejected positive cases; no such labels were evaluated.

Target overlap does not remove individual-family support: every true predicate remains recorded. It does mean family rows and domain totals cannot be treated as independent samples. Subject and cluster shortfalls establish inadequate coverage where specified, not a proven lack of every relevant behaviour. Three Validation communities constrain transport and uncertainty even for well-supported families.

## 5. Scientific consequences

| Objective | Finding |
| --- | --- |
| A. Binary suspicious-pattern classification | Both classes have substantial development support and the labels implement observable review rules. Suitable for a potential authorized development study; no trained model or independent performance validation exists. Dominant families can mask weak rare-family performance. |
| B. All three domains | All domains have positive and domain-only development support (table below). Aggregate domain evaluation is possible in principle, but reliable coverage of each domain’s mechanisms is not established; sparse subfamilies and dependence preclude an unqualified reliability claim. |
| C. Each of twelve families | Original support objective fails for nine; S2/S4 subject and cluster scarcity is especially severe. Even the three count-passing families have no measured model recall. No family has been validated by this audit. |
| D. Independent evaluation under original policy | Not available: both existing public support-policy certificates FAIL. No private family cause, count or prevalence is known or inferred. The frozen holdout gates cannot be waived by restricted wording or a separate challenge set. |

Development domain counts (overlapping totals and disjoint domain-only slices):

| Partition | Target 0 | Target 1 | Structuring | Network | Agent | Structuring only | Network only | Agent only | Multi-domain |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| train | 47770 | 12230 | 2867 | 3111 | 7678 | 1658 | 2041 | 7158 | 1373 |
| validation | 11970 | 3030 | 684 | 776 | 1941 | 391 | 493 | 1787 | 359 |

Count thresholds are predeclared coverage objectives, not mathematical guarantees of precise recall. Independent-binomial intuition is optimistic with repeated subjects and only three units. No confidence interval for model performance can be computed without predictions, and no effective sample size is asserted.

## 6. Sealed evaluation boundary

Existing commitment: `6448b0fb8b7ed7f3cc3e58bae9a2565f45dd5d2d6cccb91b74fdc4580696f0f5`. Final Test support policy: **FAIL**. Independent support policy: **FAIL**. Disposition remains **SEALED_QUARANTINED**.

The custodian’s combined support flag includes family counts, subjects/clusters and prevalence. A FAIL cannot identify which family or condition failed. No private counts were requested, reconstructed or inferred. Only named public metadata and loader source were read; no custodian invocation, seal enumeration, envelope hash/decryption or evaluation loader call occurred. Current-user process/encryption separation remains the documented limitation; this review does not strengthen or weaken it.

## 7. Options (not implemented)

### Option A: Preserve V4 with restricted claims

**Benefits:** No new draw; useful binary/domain development evidence and transparent sparse-family estimates.

**Limitations:** Cannot meet original all-family or failed holdout support policy; family estimates remain imprecise and unit dependence remains.

**Comparability:** Only frozen V4 development population; no claim to original compliant final evaluation.

**Leakage risks:** Treating repeatedly reviewed Validation as independent final evidence; relaxing gates after outcomes.

**Stage 15 compatibility:** Preservation and qualified claims fit shortfall policy, but training remains blocked absent explicit approved scope and evaluation plan.

**Version requirement:** Dataset unchanged; revised research-claim/evaluation protocol must be versioned.

### Option B: Separately versioned external family challenge evaluation

**Benefits:** Independent measurement of sparse families using justified coverage and explicit uncertainty.

**Limitations:** Enriched challenge prevalence does not estimate population precision/AP or repair frozen holdout failure. Cannot guarantee plausible support in advance.

**Comparability:** Separate report and denominators; never pool with V4 population metrics or rank as the same benchmark.

**Leakage risks:** Challenge examples, seeds or errors feeding training; choosing cases by model success; repeated accept-until-support loops.

**Stage 15 compatibility:** Explicitly contemplated by Stage 15 shortfall_resolution; requires approval and preregistration before execution.

**Version requirement:** New challenge-set identifier, manifest, protocol, independent entities/streams and custodian seal; V4 unchanged.

### Option C: Future full experiment

**Benefits:** Can address population/history/opportunity design together and seek all-family coverage under a fresh declared protocol.

**Limitations:** Cost, synthetic realism and support remain uncertain; repeated generation is not a scientific remedy by itself.

**Comparability:** New population version and fresh evaluation; original V4 preserved as historical evidence.

**Leakage risks:** Seed shopping or recycling failed evaluation feedback into a claimed untouched benchmark.

**Stage 15 compatibility:** Allowed only through versioned authorization and compatibility declaration, never a silent overwrite.

**Version requirement:** Yes: new experiment, design and fresh holdouts.

### Option D: Preserved V4 development plus justified independent extension

**Benefits:** Retains all three domains and the first draw; uses a separately justified challenge evaluation where current family coverage is sparse.

**Limitations:** Does not restore the original population-level Final/Independent claim; successful extension adequacy remains unproven.

**Comparability:** Two explicitly distinct evidence tracks; separate population and challenge conclusions with no pooled prevalence.

**Leakage risks:** Blending datasets/metrics or tuning to extension outcomes. Freeze extension design and eventual model before evaluation; no developer access to challenge outcomes during selection.

**Stage 15 compatibility:** Combines the declared preservation/challenge pathway; holdout quarantine and G11 remain in force until a separately approved successor protocol defines eligible claims.

**Version requirement:** Versioned extension and research/evaluation protocol; no change to existing V4 bytes.

## 8. Recommended path and authorization boundary

Preserve the first V4 draw and all three domains. Seek a separately approved extension-design stage before any data or model work. Predeclare sparse-family scientific mechanisms, unchanged target semantics, legitimate boundary negatives, subject/community diversity, fixed opportunity budgets, support failure handling and separate estimands. Select justified opportunities before labels; never override labels, duplicate positives, retain only successful cases or retry seeds to reach counts. If plausible support cannot be attained, report that limitation instead of manufacturing positives.

An eventual independent challenge set must have fresh entities/history/streams, separate custodianship and no development access to examples or labels. Freeze its protocol before construction and the eventual model before releasing challenge outcomes. Keep challenge metrics and prevalence separate from V4 population metrics. Include context from all three domains and report every family, including sparse estimates and their limitations. No extension may retrospectively turn the two existing FAIL certificates into PASS.

This route avoids discarding usable evidence or repeating the entire production experiment now. It can support a narrower, transparently extended research claim. If the original full-population Final/Independent claim must be preserved unchanged, Option C requires a new versioned experiment and fresh evaluation; that work is not authorized here.

**This decision authorizes no new generation, feature construction, training, threshold work or holdout access.** It records an audit recommendation only. Training and the original full-family evaluation claim remain blocked pending explicit approval of a defensible successor protocol.

## 9. Evidence and preservation

[Development support review](../evidence/stage16s/development_support_review.json), [root-cause analysis](../evidence/stage16s/root_cause_analysis.json), [holdout boundary verification](../evidence/stage16s/holdout_boundary_verification.json), [scientific options](../evidence/stage16s/scientific_options.json), [preservation verification](../evidence/stage16s/preservation_verification.json), [decision](../evidence/stage16s/stage16s_decision.json). Source: [stage16s_review.py](../generation/stage16s_review.py). The script refuses existing Stage 16S outputs.

The explicit protected hash set includes historical/application artifacts, frozen design/amendment and failed attempts, Stage 16R source/report/evidence, development transactions/truth/provenance, and named public commitment metadata. Unread sealed contents are outside the byte-verification claim. No historical file is rewritten.

## 10. Decision

**B — ADDITIONAL INDEPENDENT CHALLENGE EVALUATION REQUIRED.**

V4 STAGE 16S COMPLETE — WAITING FOR APPROVAL.
