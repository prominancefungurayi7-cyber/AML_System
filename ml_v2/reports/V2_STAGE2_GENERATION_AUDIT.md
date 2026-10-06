# MODEL V2 ? STAGE 2 GENERATION AND STRUCTURAL AUDIT

Dataset: `epocash_aml_synthetic_100k_v2`

**Overall result: CONDITIONAL PASS.** All required exact-count, accounting, ground-truth, temporal-ordering, partition-isolation and V1-protection checks passed. The condition concerns research fidelity and future use: software guards are not an OS security boundary, descriptive overlap is not proof against all shortcuts, and the behavioural simplifications listed below must be considered before feature-stage approval. No failed mandatory check was waived to obtain this result.

Generation and structural audit completed on 2026-09-21. No features, models, classifier probes, threshold selection, application integration or model evaluation were performed.

## 1. Authorization and deviations from Stage 1

The user explicitly approved Stage 1 and authorized Stage 2 implementation, generation and model-free structural auditing. The Stage 2 instruction states: ?We are NOT implementing external encryption or an independent human data custodian? and ?Instead implement strict SOFTWARE-LEVEL separation.? This supersedes Stage 1 section 10 for this experiment; Stage 1 is retained unchanged as the historical design.

The following implementation choices and limitations are explicit:

- Holdouts are readable local research files with API guards and explicit HOLDOUT role markers. They are not encrypted or protected from deliberate direct filesystem access. Future development code must use `load_development`; unrestricted Python can bypass any ordinary loader API.
- Every wallet has a routine baseline event after activation inside the 100,000-row budget. Agents have pre-horizon activation dates; the implementation does not introduce agents activated partway through the horizon. Wallets include later activation and cold starts.
- Agent activity bands influence selection with weights 0.5/1/2. Wallet profile/activity metadata is allocated exactly, but normal wallet selection is uniform among active wallets and the shared amount mixture is not calibrated by profile. This is less detailed than Stage 1?s proposed profile-conditioned service model.
- Scenario episode scheduling overlaps legitimate behaviour. Family-specific timing and relationships are implemented, but an increase relative to each entity?s measured historical rate is not guaranteed for every episode. This audit does not claim full empirical validation of baseline-relative behavioural realism.
- A4 commits an opening three-cash-event portion with 2/3 count dominance and 60?95% value dominance; later activity can rebalance. It does not guarantee that an entire seven-day history is imbalanced.
- Initial liquidity is fixed ex ante at USD 2,500,000 per wallet and USD 50,000,000 per agent. This keeps accounting feasible without hidden replenishments but is deliberately ample, not a claim about realistic mobile-money balances.
- Complete episode signatures include anonymized roles, relative times, amounts, types and channels. No copied complete sequence was found. Common bare graph motifs (for example, reciprocal pairs) necessarily recur and are not treated as copied campaigns.
- Standalone system CPython 3.14.3 with standard-library-only code was used instead of creating a package environment. The application environment and dependencies were untouched.

## 2. Files created

- `src/dataset_generator.py`: deterministic standalone scenario generation and accounting preflight.
- `src/dataset_audit.py`: independent persisted-data structural audit; it does not import the generator.
- `src/contracts.py`: V2 path checks, serialization and development-only loading.
- `src/prepare_design.py`: versioned schema and complete family/category integer margins.
- `src/run_stage2.py`: explicit V2 tests, two temporary generations, hash comparison, audit, tamper detection and V1 hash verification.
- `design/dataset_schema.json`, `design/allocation_manifest.json`, `design/scenario_manifest.json`.
- `data/development/train/` and `data/development/validation/`.
- `data/holdout/final_test/` and `data/holdout/independent/`, each marked HOLDOUT.
- Each partition contains `transactions.csv`, `ground_truth.csv`, `wallets.csv`, `agents.csv`, `episode_plans.json`, `membership_commitment.json`, and `partition_role.json`.
- `data/manifests/generation_manifest.json`: immutable generation-time counts, seed, source/design content hashes and 28 partition-file hashes.
- `tests/test_stage2_contract.py`, `requirements-v2.lock`, and `README.md`.
- `reports/stage2_audit.json`, `reports/stage2_reproducibility.json`, `reports/stage2_v1_protection.json`, `reports/stage2_tests.txt`, and this report.

The generation manifest records audit pending at generation time by design; `reports/stage2_audit.json` is the completed independent audit result. These are separate provenance records. `features/` and `models/` remain empty.

## 3. Generator and seed

Random seed: **20260921**. SHA-256-derived streams isolate partitions and entity allocation; a separate stream supplies opaque timestamp-tie keys. Integer episode packing commits class, family, strength and complete episode lengths before event materialization. A serialized membership ledger and its SHA-256 commitment are preserved separately from observable events. Amounts use a bounded shared mixture without endpoint clipping; family-specific compositions and near-threshold settings also apply to matched hard negatives.

Cash entry/exit phases, real transfer edges, complete cycles and partial pass-through flows are materialized from these plans. Globally sorted UTC timestamps and independent tie keys determine transaction IDs 1?100,000. The same mapping joins labels to facts. No prediction, rule, alert or later feature participates in label assignment. No V1 event rows were copied.

## 4. Exact population and partition distribution

| Partition | Total | Normal | Suspicious | Wallets | Customers | Agents |
|---|---:|---:|---:|---:|---:|---:|
| train | 60,000 | 52,800 | 7,200 | 1,200 | 1,200 | 96 |
| validation | 15,000 | 13,200 | 1,800 | 300 | 300 | 24 |
| final_test | 15,000 | 13,200 | 1,800 | 300 | 300 | 24 |
| independent | 10,000 | 8,800 | 1,200 | 200 | 200 | 16 |
| **Total** | **100,000** | **88,000** | **12,000** | **2,000** | **2,000** | **160** |

Class shares are exactly 88% normal and 12% suspicious-pattern-scenario membership. No resampling or post-generation truncation was used.

## 5. Domains and all 12 suspicious families

Each domain has 4,000 rows: Train 2,400, Validation 600, Final test 600 and Independent 400.

| Family | Definition | Train | Validation | Final test | Independent | Total |
|---|---|---:|---:|---:|---:|---:|
| S1 | `variable_fragment_burst` | 600 | 150 | 150 | 100 | 1,000 |
| S2 | `similar_amount_repetition` | 600 | 150 | 150 | 100 | 1,000 |
| S3 | `distributed_same_day_fragmentation` | 600 | 150 | 150 | 100 | 1,000 |
| S4 | `variable_near_threshold_history` | 600 | 150 | 150 | 100 | 1,000 |
| N1 | `many_to_one_collection` | 600 | 150 | 150 | 100 | 1,000 |
| N2 | `one_to_many_dispersion` | 600 | 150 | 150 | 100 | 1,000 |
| N3 | `reciprocal_relationship_cycle` | 600 | 150 | 150 | 100 | 1,000 |
| N4 | `wallet_pass_through` | 600 | 150 | 150 | 100 | 1,000 |
| A1 | `agent_wallet_growth` | 600 | 150 | 150 | 100 | 1,000 |
| A2 | `agent_wallet_concentration` | 600 | 150 | 150 | 100 | 1,000 |
| A3 | `agent_temporal_burst` | 600 | 150 | 150 | 100 | 1,000 |
| A4 | `agent_flow_imbalance` | 600 | 150 | 150 | 100 | 1,000 |

The audit checks graph-role consistency for collection and dispersion, closed reciprocal/cycle edges, pass-through retention, S4?s partial near-threshold membership, A1 wallet-role counts, A4 directional portions, schedule support and complete episode membership. These checks validate construction invariants, not criminal intent or detector performance.

## 6. Signal strengths

| Scope | Weak | Moderate | Strong |
|---|---:|---:|---:|
| Each family, all partitions | 200 | 500 | 300 |
| Train | 1,440 | 3,600 | 2,160 |
| Validation | 360 | 900 | 540 |
| Final test | 360 | 900 | 540 |
| Independent | 240 | 600 | 360 |
| **Total** | **2,400** | **6,000** | **3,600** |

Strength is a precommitted latent coordination setting. It affects timing probabilities while retaining overlapping support. It is never inferred from features or predictions.

## 7. Routine normal and hard negatives

Exactly **44,000 routine** and **44,000 hard-negative** normal events exist.

| Normal family | Train | Validation | Final test | Independent | Total |
|---|---:|---:|---:|---:|---:|
| Routine | 26,400 | 6,600 | 6,600 | 4,400 | 44,000 |
| H1 | 3,300 | 825 | 825 | 550 | 5,500 |
| H2 | 3,300 | 825 | 825 | 550 | 5,500 |
| H3 | 3,300 | 825 | 825 | 550 | 5,500 |
| H4 | 3,300 | 825 | 825 | 550 | 5,500 |
| H5 | 3,300 | 825 | 825 | 550 | 5,500 |
| H6 | 3,300 | 825 | 825 | 550 | 5,500 |
| H7 | 3,300 | 825 | 825 | 550 | 5,500 |
| H8 | 3,300 | 825 | 825 | 550 | 5,500 |

On Train and Validation only, every H1?H8 family overlaps suspicious events in all seven predeclared amount bins, episode-duration ranges and episode-event-count ranges. Normal observations exist both below and above the synthetic USD 10,000 reference. The full descriptive tables are in `stage2_audit.json`; no holdout distribution exploration or classifier probe was performed.

These range/bin checks rule out disjoint supports on the inspected variables. They do not establish that every one-variable threshold is uninformative, nor that compound shortcuts are absent. This is a condition for future development review, not a claimed predictive result.

## 8. Transaction types and channels

| Category | Normal | Suspicious | Total |
|---|---:|---:|---:|
| Cash-In | 22,000 | 3,000 | 25,000 |
| Cash-Out | 22,000 | 3,000 | 25,000 |
| Agent-assisted Wallet-to-Wallet | 22,000 | 3,000 | 25,000 |
| Direct Wallet-to-Wallet | 22,000 | 3,000 | 25,000 |

Totals: 50,000 Wallet-to-Wallet, 75,000 agent-mediated, and 25,000 direct-wallet events. Each category has 15,000/3,750/3,750/2,500 rows in Train/Validation/Final test/Independent. Class-category margins, domain-category margins and complete family allocations match the approved integer manifest.

## 9. Entity and partition isolation

All 2,000 wallets, 2,000 customers, 160 agents and episode populations are disjoint across partitions. Both transfer endpoints and every serviced wallet belong to the same partition. There are zero cross-partition edges and zero Wallet-to-Wallet self-transfers. The 50,000 same-wallet cash records are valid customer bookkeeping, not graph self-loops.

Wallet profile counts are exactly 1,200 personal / 500 small-business / 200 merchant / 100 seasonal-income. Agent activity-band counts are exactly 80 lower / 48 medium / 32 higher. Per-partition profile counts also pass.

## 10. Temporal coverage and safety

The fixed horizon is `[2025-01-01T00:00:00.000000Z, 2025-06-30T00:00:00.000000Z)`, exactly 180 days.

| Partition | First timestamp (UTC) | Last timestamp (UTC) |
|---|---|---|
| train | 2025-01-01T00:00:04.209352Z | 2025-06-29T23:44:59.722351Z |
| validation | 2025-01-01T00:00:02.004518Z | 2025-06-29T23:37:53.757950Z |
| final_test | 2025-01-01T00:00:11.121538Z | 2025-06-29T23:58:50.283252Z |
| independent | 2025-01-01T00:00:29.036480Z | 2025-06-29T23:29:01.873629Z |

Each 30-day block contains exactly 2,000 suspicious events overall (1,200/300/300/200 by partition). Normal block totals also match the approved allocation; Independent uses 1,467 in the first four blocks and 1,466 in the last two. All activations precede the associated events.

IDs and sequences are unique integers 1?100,000 assigned in global chronological order. No equal timestamps happened in this seed?s dataset; a dedicated test verifies label-independent tie ordering. The timestamps and IDs support strict prior-history ordering and 1-hour, 24-hour, 7-day and 30-day windows. No historical feature aggregates were computed. Partial history at the beginning remains valid and is not hidden warm-up data.

## 11. Accounting validation

Independent chronological replay starts from recorded ex ante balances and float. Transfers debit the sender and credit the receiver. Cash-In debits agent float and credits the customer; Cash-Out does the reverse. Agent-assisted transfer principal never changes agent float.

All amounts are positive integer USD cents inside USD 1?25,000. All wallets/agents exist, no wallet or agent goes negative, and total customer balances plus electronic agent float are conserved. No top-ups, overdrafts or off-ledger funding were introduced. This models electronic balances, not physical cash inventory.

| Partition | Minimum wallet balance (cents) | Minimum agent float (cents) |
|---|---:|---:|
| train | 216,641,746 | 4,964,050,901 |
| validation | 220,760,106 | 4,972,391,616 |
| final_test | 221,365,371 | 4,976,039,525 |
| independent | 225,040,476 | 4,973,704,230 |

## 12. Ground-truth independence and leakage audit

Every raw event joins exactly one binary target. Labels, domains, families, strengths, normal-family assignments, phases and fixed label basis agree with the committed plans. Suspicious and normal metadata consistency checks pass; no episode was cut to hit a budget.

Raw events contain exactly the observable-field allowlist. They contain no labels, narratives, scenario/family/domain/strength fields, rules, risks, alerts or AI outputs. The generator and auditor use only standard-library/V2 imports. No Flask, application scoring or model module was imported. Metadata and IDs must still be excluded from future X; absence of direct columns is not a proof against statistical leakage.

## 13. Software holdout guards

`load_development(dataset_root, partition, table)` permits only exact `train` or `validation` names, allowlists tables, checks development role and file hash, and rejects links/junctions. There is no ?allow holdout? switch. Tests reject final-test and independent names, traversal strings and inappropriate table paths. Actual Train/Validation loading succeeds; actual holdout loading is denied.

Only model-free generator/audit entry points accessed holdouts. No holdout feature distributions were examined. Future code review must require the supported loader and disallow direct holdout reads; a later frozen evaluation entry point remains unimplemented.

## 14. Reproducibility and negative tests

Two complete temporary generations with seed 20260921 produced identical SHA-256 hashes for **all 29 files**, including events/order, labels, entities, episode plans, commitments and manifests. The permanent copy matches those hashes. Both temporary datasets and the earlier pilot were removed; only one permanent dataset remains.

An intentional currency modification in the disposable second copy was detected by both the independent semantic audit and file-hash check. No permanent data was altered by that test.

All **7 contract tests passed**, covering path escape, existing-file/dataset overwrite refusal, development-only access, complete episode budgets across multiple seeds, import isolation, real Windows-junction rejection and same-timestamp ordering. Full test output is saved in `stage2_tests.txt`.

## 15. V1 protection and final result

Before/after SHA-256 checks matched for **347 protected existing files** across the application, V1 data/models/archive, reports, tests, static assets and templates. No application database connection or application startup was invoked. Repository status retains the same two pre-existing unrelated deleted temporary-document files; this work adds only `ml_v2/` content. No deployment, commit or push was performed.

The independent structural audit recorded **2,171,786 check instances**, zero recorded failures, and result **PASS**. Reproducibility and V1-protection results are also **PASS**. The overall research dataset release is **CONDITIONAL PASS** for the behavioural and access-boundary limitations in sections 1 and 7; it is not a claim of real-world validity, superior V1 performance or demonstrated learnability.

## 16. Conditions for future feature construction

- Obtain separate approval for the feature stage and explicitly accept or revise the documented behavioural simplifications. Do not silently regenerate or tune against these holdouts.
- Freeze the offline V1 semantic reference separately. Same-wallet cash records are not transfer edges; sender/receiver, serviced-wallet and agent-float direction need explicit treatment.
- Convert cents to dollars explicitly wherever a dollar-based formula is used. USD 10,000 is only a synthetic research reference, not a legal threshold.
- Exclude scenario/episode/strength/profile metadata and raw identifiers from X. Compute histories before updating state, use partition-local timestamp/ID ordering, and test current/future exclusion and ties.
- Use only Train/Validation for feature exploration, model selection and threshold decisions. Holdouts remain reserved for a later frozen evaluation release.
- Expect irreducible ambiguity between some normal and suspicious campaign memberships. No model or performance result exists for V2.

V2 STAGE 2 COMPLETE ? WAITING FOR APPROVAL.
