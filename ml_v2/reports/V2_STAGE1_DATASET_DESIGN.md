# MODEL V2 — STAGE 1 DATASET DESIGN REPORT

Status: DESIGN ONLY — awaiting approval for a later implementation stage.

Dataset identity: `epocash_aml_synthetic_100k_v2`.

This report specifies a new experiment. It does not authorize generation, feature extraction, training, evaluation execution, database writes, application integration, or a model switch. Model V1 remains the existing frozen Stage 14 Gradient Boosting artifact and its existing application code. No V1 file is changed by this stage.

## 1. Evidence and scope

Repository evidence inspected for this design:

- `data/ecocash_aml_synthetic_100k_v1/generation_manifest.json`, `transactions.csv`, `ground_truth.json`, `entity_metadata.json`, and `features/feature_names.json`.
- `ml/stage14/stage14_experiment_results.json` and `stage14_correction_results.json`.
- `ml_archive/ml_stage13a_extract_features_final.py`, the offline extractor identified by the Stage 13 completion report.
- `ai_stage13_features.py`, `ai_stage14_model.py`, and the current transaction-processing integration in `server.py`.
- Stage 13 completion and Stage 14/16 evaluation reports under `reports/ml_stages/`.

Verified V1 data properties informing this proposal: 100,000 rows; 88,000 normal and 12,000 suspicious labels; 2,000 wallets; 160 agents; disjoint partition populations; all raw transaction types recorded as `transfer`; and all 12,000 suspicious ground-truth records marked `medium` signal strength. V1's recorded structuring recall is 149/600 = 24.83% on final test and 123/400 = 30.75% on independent evaluation. These are historical evidence, not targets to optimize against by reusing those holdouts.

The V1 written report and experiment JSON contain some inconsistent aggregate metrics. This design uses the domain counts in the correction results to motivate the research question, without treating every historical report value as reconciled.

All numbers, distributions, schemas, ranges, and safeguards below are **proposed V2 specifications**, not observations from a generated V2 dataset. There is no V2 dataset or model yet.

## 2. Exact population and partition allocation

Retain the proposed split. There is no technical justification at this stage to reduce either holdout or change the total.

| Partition | Transactions | Normal, label 0 | Suspicious, label 1 | Wallets/customers | Agents | Suspicious per domain | Suspicious per family |
|---|---:|---:|---:|---:|---:|---:|---:|
| Train | 60,000 | 52,800 | 7,200 | 1,200 | 96 | 2,400 | 600 |
| Validation | 15,000 | 13,200 | 1,800 | 300 | 24 | 600 | 150 |
| Final test | 15,000 | 13,200 | 1,800 | 300 | 24 | 600 | 150 |
| Independent evaluation | 10,000 | 8,800 | 1,200 | 200 | 16 | 400 | 100 |
| **Total** | **100,000** | **88,000** | **12,000** | **2,000** | **160** | **4,000** | **1,000** |

There are exactly three suspicious domains and four families in each. Domain and family counts are mutually exclusive: one suspicious transaction has one primary family, even if its observable behaviour resembles another family. Secondary observations may be recorded for analysis but never counted as additional positive rows.

The full budget includes ordinary historical activity, hard negatives, and all suspicious-episode transactions. No hidden warm-up dataset, extra transactions, or post-generation truncation is permitted.

## 3. Exact proposed storage schema

Use partition-specific UTF-8 CSV files for raw events, separate ground-truth CSV files, entity CSV files, and JSON manifests. CSV timestamps are normalized UTC strings with fixed microsecond precision. Monetary values are positive integer US-dollar cents. Future feature code may convert cents to dollar units explicitly; it must not pass cents into a dollar-based V1 formula.

### 3.1 `transactions.csv` — observable event facts only

| Column | Type | Nullability and constraint |
|---|---|---|
| `transaction_id` | uint64 | Required; globally unique; assigned after final chronological merge, 1 through 100,000 |
| `event_sequence` | uint64 | Required; equals `transaction_id`; deterministic global event order |
| `event_timestamp` | UTC datetime string | Required; within the specified 180-day horizon |
| `sender_wallet` | string | Required; references a customer wallet in this partition |
| `receiver_wallet` | string | Required; references a customer wallet in this partition |
| `amount_minor` | int64 | Required; positive amount in USD cents |
| `currency` | enum | Required; `USD` throughout this experiment |
| `transaction_type` | enum | Required; `cash_in`, `cash_out`, or `wallet_to_wallet` |
| `channel` | enum | Required; `agent` or `direct_wallet` |
| `agent_id` | string | Required for `agent`; null for `direct_wallet`; valid partition-local agent |
| `serviced_wallet` | string | Required for agent events; an endpoint of that event; null for direct transfers |
| `agent_flow_direction` | enum | `outbound`, `inbound`, or `none`; defined below |

Partition membership comes from the directory and entity manifests; it is not an input column. No label, scenario, risk, rule, alert, prediction, description, or generated narrative is permitted in the event file.

Cash conventions:

- Cash-In: both wallet endpoints identify the same credited customer wallet; channel is `agent`; serviced wallet is that wallet; direction is `outbound` relative to the agent's electronic float.
- Cash-Out: both endpoints identify the same debited customer wallet; channel is `agent`; serviced wallet is that wallet; direction is `inbound` relative to the agent's electronic float.
- Wallet-to-Wallet: sender and receiver must differ. Agent-assisted transfers identify the serviced endpoint, with `agent_flow_direction=none` because facilitation does not itself move the transfer principal through agent float. Direct transfers have null agent and serviced wallet, and direction `none`.
- A same-wallet cash record is a bookkeeping convention, not a self-transfer or network cycle. Customer wallets and agent identifiers are separate namespaces; agent float is not an additional customer wallet.

This preserves the information needed for mobile-money direction and attribution. It does not prescribe new features. Existing V1 formulas may count same-wallet cash records as self-counterparties; that semantic limitation must be measured separately before any claim of feature parity.

### 3.2 `ground_truth.csv` — never supplied to a feature builder

| Column | Type | Meaning |
|---|---|---|
| `transaction_id` | uint64 | One-to-one event join key |
| `target` | uint8 | Exactly `0=normal`, `1=suspicious_pattern_scenario` |
| `primary_domain` | nullable enum | `structuring`, `network`, `agent`; null for normal |
| `primary_family` | nullable enum | One of the 12 family IDs in section 6; null for normal |
| `episode_id` | nullable opaque string | Same campaign ID for related suspicious events; not a model input |
| `normal_family` | nullable enum | `routine` or one of H1–H8; null for suspicious |
| `normal_episode_id` | nullable opaque string | Groups legitimate scheduled activity where applicable |
| `signal_strength` | nullable enum | `weak`, `moderate`, `strong`; ex ante scenario setting, not a computed score |
| `episode_phase` | enum | `early`, `established`, `late`, or `not_applicable`; defined by the committed episode schedule |
| `label_basis` | string | `precommitted_scenario_membership_v2`; fixed methodology identifier |

Ground truth uses provisional internal event handles until final IDs are assigned. The same one-to-one remapping is then applied to event facts and ground truth. That remapping must not inspect labels when deciding order.

### 3.3 Entity files

`wallets.csv`: `wallet_id:string`, `customer_id:string`, `partition:enum`, `profile_type:enum`, `activity_band:enum`, `initial_balance_minor:int64`, `activation_timestamp:UTC datetime`.

`agents.csv`: `agent_id:string`, `partition:enum`, `activity_band:enum`, `initial_float_minor:int64`, `activation_timestamp:UTC datetime`.

Exactly one wallet per customer: 2,000 wallets and 2,000 customers. No duplicate customer across partitions. Agent and customer activity bands are legitimate service profiles, not labels. Entity metadata is generation/audit material, not automatically admitted to X.

Wallet profile allocation is 1,200 personal, 500 small-business, 200 merchant, and 100 seasonal-income wallets. Allocate these proportionally: Train 720/300/120/60; Validation 180/75/30/15; Final test 180/75/30/15; Independent 120/50/20/10. Every profile is eligible for legitimate and suspicious episodes.

Agent activity allocation is 80 lower-activity, 48 medium-activity, and 32 higher-activity agents. Partition allocations are respectively Train 48/29/19; Validation 12/7/5; Final test 12/7/5; Independent 8/5/3. These are preassigned service profiles, not thresholds for suspicious classification.

`generation_manifest.json`: dataset/schema/generator versions; code revision; seed commitments; horizon; monetary units; exact count targets and actuals; partition role; file hashes; audit results; independent-generation specification version. Actuals and hashes are populated only during a later approved generation stage.

`scenario_manifest.json`: family definitions, episode budgeting policy, amount/timing/role distributions, hard-negative definitions, and versioned signal settings. Evaluation-only episode metadata stores planned roles and parameters. None is a feature source.

## 4. Transaction types and channels

Use the following exact aggregate allocations. Their class proportions are identical, so neither type nor channel alone is a deterministic label proxy.

| Event category | Normal | Suspicious | Total | Channel |
|---|---:|---:|---:|---|
| Cash-In | 22,000 | 3,000 | 25,000 | Agent |
| Cash-Out | 22,000 | 3,000 | 25,000 | Agent |
| Agent-assisted Wallet-to-Wallet | 22,000 | 3,000 | 25,000 | Agent |
| Direct Wallet-to-Wallet | 22,000 | 3,000 | 25,000 | Direct wallet |
| **Total** | **88,000** | **12,000** | **100,000** | |

Thus 50,000 transfers, 25,000 Cash-Ins, 25,000 Cash-Outs; 75,000 agent events and 25,000 direct events. These are synthetic research allocations, not claimed market shares.

Apply the same four-way balance within each partition:

| Partition | Each of the four categories | Normal per category | Suspicious per category |
|---|---:|---:|---:|
| Train | 15,000 | 13,200 | 1,800 |
| Validation | 3,750 | 3,300 | 450 |
| Final test | 3,750 | 3,300 | 450 |
| Independent | 2,500 | 2,200 | 300 |

Domain-level type targets are Structuring 1,500 Cash-In / 1,500 Cash-Out / 1,000 transfers; Network 500 / 500 / 3,000; Agent 1,000 / 1,000 / 2,000. All Agent-domain events are agent-mediated. Split Structuring transfers 500 agent / 500 direct and Network transfers 500 agent / 2,500 direct. The 2,000 Agent-domain transfers complete the 3,000 agent-assisted suspicious-transfer total.

Allocate subcounts to partitions using deterministic constrained integer apportionment. For example, Network's agent/direct transfer counts can be Train 300/1,500, Validation 75/375, Final test 75/375, Independent 50/250. Family-level quotas need not enforce identical type fractions; their semantic roles and complete episodes take priority, while all hard aggregate totals remain exact. Approve the full integer allocation manifest before generation; do not discard events to repair totals afterward.

## 5. Shared behavioural generation policy

Amounts, activity profiles, channel choices, and business schedules are drawn from overlapping, label-independent base distributions. Suspicious behaviour differs primarily through joint timing, direction, relationship changes, and deviation from the entity's own preceding activity.

Proposed common amount support is $1–$25,000. Use a mixture of right-skewed amounts and rounded routine amounts, conditioned on service/profile type rather than target. Both labels can use cents, rounded values, large values, and small values. Caps are synthetic experiment constraints, not financial-service limits. Validate that any clipping does not create a point-mass shortcut.

Where needed, use **$10,000 solely as a SYNTHETIC RESEARCH THRESHOLD** to retain interpretability with existing threshold-history inputs. It is **not a Zimbabwean regulatory threshold**. No legal conclusion or reporting obligation follows from it.

Per family, assign exactly 200 weak, 500 moderate, and 300 strong suspicious events. Per partition/family this is Train 120/300/180; Validation 30/75/45; Final test 30/75/45; Independent 20/50/30. Strength settings are committed latent schedule parameters before events exist. They must never be computed from features, classifier confidence, or rule hits. All strength tiers retain overlapping amounts and activity levels.

Sample complete episodes with bounded lengths, then schedule to exact event budgets. Use variable-length final episodes within the documented ranges or resample an entire provisional schedule before materialization. Never cut an episode halfway to hit a row count. Reusing identical episodes with renamed IDs is prohibited.

Wallets and agents retain legitimate baseline activity during and outside suspicious campaigns. No permanent 'suspicious wallet' or 'suspicious agent' flag is exported. Selection of participants occurs within each partition, with variation in which endpoint is active. Normal hard episodes may use the same entities at other times, but events cannot belong to both target classes.

## 6. The 12 suspicious scenario families

Every family contributes exactly 1,000 labelled suspicious events: 600 train, 150 validation, 150 final test, 100 independent. The ranges below are proposed schedule supports, not classification rules. Lower-intensity, overlapping normal counterparts are compulsory, and the strongest tier must not be perfectly separable by a single amount or count.

### S1 — `variable_fragment_burst` — Variable Fragment Burst

Schedule a source-funds episode as 4–18 unequal fragments within 10–180 minutes, with occasional 1–3-day continuations. Draw episode totals from a broad shared support, typically $300–$60,000, and allocate variable proportions using a randomized composition rather than equal division. Mix short pauses, longer pauses, repeated amounts, and variable amounts. Use coherent Cash-In, Cash-Out, or transfer phases; some campaigns combine directions over time. Interleave ordinary transactions. Behavioural evidence is the joint change in frequency and cumulative flow relative to prior activity, not one value. Counterpart: payroll, market-day, and bill-payment bursts.

### S2 — `similar_amount_repetition` — Similar Amount Repetition

Schedule 5–24 payments over 2 hours–10 days around a randomly chosen amount anchor, with small cent variation, moderate variation, and occasional different-sized transactions. Anchors come from the common amount distribution, including low and mid values. Some episodes have amounts within the existing 5% similarity band; others straddle it. Vary counterparty stability and funding direction. The lead is persistent repeated movement combined with contextual changes, not rounded values alone. Counterpart: regular collections, subscriptions, transport and supplier payments.

### S3 — `distributed_same_day_fragmentation` — Distributed Same-Day Fragmentation

Schedule 6–30 fragments across 4–18 hours, using multiple small clusters rather than requiring one dense hour. Repeat on 1–5 days in some episodes. Vary totals, gaps, cash versus transfer phases, and whether counterparties remain stable. Include lower-value fragmentation far from $10,000. Contrast the coordinated cumulative movement and recurrence with the wallet's prior service pattern. Counterpart: merchant settlements, school collections, or a legitimate busy trading day. This family explicitly exercises same-day and multi-day evidence that a one-hour count can miss.

### S4 — `variable_near_threshold_history` — Variable Near-Threshold History

Schedule 4–20 events over 2–14 days. A proposed 25–60% of an episode's amounts occupy a broad 0.70–1.05 multiple of the synthetic threshold; the remainder use the common lower-value and occasional higher-value distribution. Include some transactions above the threshold, not only just below it. Vary cumulative totals, timing, recipients, and directions. Normal counterparts also contain near-threshold values and recurring large payments. The scenario represents a sustained pattern of fragmented movement, not a rule saying that an amount below $10,000 is suspicious.

### N1 — `many_to_one_collection` — Many-to-One Collection

Use 3–12 contributing wallets and one collecting wallet over 30 minutes–5 days, with variable contribution sizes and timing. Mix established and newly used relationships; optionally follow with partial onward transfers or Cash-Outs. Rotate the collector across episodes and vary the rate of source-set turnover. Supporting cash events can be labelled parts of the same campaign, but collection edges are real wallet transfers. Counterpart: merchant receipts, community contributions, and scheduled fee collection. Multiple inbound counterparties alone must not determine the label.

### N2 — `one_to_many_dispersion` — One-to-Many Dispersion

Use a funded source wallet distributing to 3–12 recipients over 20 minutes–3 days. Vary concentration, recipient reuse, new-recipient fraction, amounts and spacing. Some episodes disperse most funding; others retain a material remainder. Include coherent preceding funding and occasional subsequent recipient activity. Counterpart: payroll, supplier settlement, refunds, and family disbursements. Match legitimate examples on recipient-count ranges and value scales while varying joint relationship stability and flow timing.

### N3 — `reciprocal_relationship_cycle` — Reciprocal Relationship Cycle

Generate two-wallet reciprocal flows and 3–6-wallet directed cycles over 1 hour–7 days. Use unequal returning amounts, partial retention, interruptions, ordinary side payments, and changing recurrence intervals. No Wallet-to-Wallet self-loops. Avoid copying a perfectly equal-valued circular graph for every positive. Counterpart: refunds, shared expenses, and recurring settlement between business partners. Keep graph topology and edge timing available through prior event facts, not an exported cycle flag.

### N4 — `wallet_pass_through` — Wallet Pass-Through

Schedule inbound funding followed by one or several outflows, with 50–98% of received value moved onward over 5 minutes–48 hours. Vary retained balances, number of counterparties, interleaved ordinary payments, and recurrence over several days. Include slower and partial movement, so exact equality and one fixed delay do not identify the class. Use transfers for graph edges and cash events for coherent entry or exit. Counterpart: legitimate settlement and same-day liquidity redistribution. The 24-hour ratio is only one incomplete observation, not the label definition.

### A1 — `agent_wallet_growth` — Agent Wallet Growth

Around an agent with prior service history, schedule 4–16 new or infrequently served wallets over 1–7 days alongside established customers. Vary how the new wallets transact with one another, return, and share flows. New-wallet activity increases relative to that agent's prior level rather than a universal count. Counterpart: market expansion, a temporary service outage elsewhere, and seasonal customer acquisition. An agent remains eligible regardless of its legitimate activity band.

### A2 — `agent_wallet_concentration` — Agent Wallet Concentration

Schedule 2–6 related wallets accounting for a varying 35–85% of the agent episode's value or service events, with ordinary customers interleaved. Vary wallet reuse, amount inequality, funding direction, and shared counterparties. Avoid a fixed concentration cutoff. Counterpart: a small agent regularly serving a few high-volume businesses. Distinguishing evidence is the relationship/flow change and coordination, not concentration or customer wealth alone.

### A3 — `agent_temporal_burst` — Agent Temporal Burst

Schedule 6–30 service events over 15–120 minutes, sometimes in repeated daily bursts. Use daytime and off-hours activity in both classes, variation in amounts, and both old and new wallets. Episode intensity is relative to each agent's baseline; higher-activity agents also receive entirely normal spikes. Counterpart: paydays, remittance collection periods, events, and temporary queue build-up. Neither off-hours timing nor a high absolute count independently establishes the target.

### A4 — `agent_flow_imbalance` — Agent Flow Imbalance

Schedule directionally uneven Cash-In/Cash-Out activity across multiple wallets over 6 hours–7 days, with a proposed dominant-direction share of 60–95% in portions of an episode. Vary value and count imbalance independently, duration, concentration, and later balancing activity. Include ordinary agent-assisted transfers without pretending their principal is agent float. Counterpart: legitimate local demand imbalance and temporary liquidity pressure. Agent float and customer balance constraints still apply; no impossible money creation is allowed to mark suspiciousness.

## 7. Hard-negative design: 44,000 of the 88,000 normal events

Allocate 44,000 ordinary normal events and 44,000 hard normal events. Each of eight hard-negative families contributes exactly 5,500 normal events. Per family: Train 3,300; Validation 825; Final test 825; Independent 550. Routine normal allocation is Train 26,400; Validation 6,600; Final test 6,600; Independent 4,400.

| Family | Normal behaviour represented | Main confounding pattern |
|---|---|---|
| H1 | Legitimate burst payments and busy same-day trading | Fragment bursts and high same-day count |
| H2 | Repeated supplier, subscription and household payments | Similar amounts and repeated counterparties |
| H3 | Occasional high values and repeated payments near the synthetic threshold | Amount and threshold-history shortcuts |
| H4 | Merchant, fee and community collections | Many-to-one collection |
| H5 | Payroll, supplier payouts and legitimate settlement transit | One-to-many and pass-through flows |
| H6 | Several counterparties, changing recipients, refunds and reciprocal settlement | Network novelty, turnover and cycles |
| H7 | Busy agents, many customers, paydays and temporary service spikes | Agent wallet growth and temporal bursts |
| H8 | Agents serving regular large customers and temporary cash demand imbalance | Agent concentration and directional imbalance |

Hardness is planned from overlapping latent schedule supports, not assigned after computing features or querying a model. Legitimate narratives are metadata only; if a normal and suspicious event have the same observable evidence, acknowledge that irreducible ambiguity rather than inventing an input that reveals the hidden narrative.

Avoid making normal examples uniformly regular, low-value, well-spaced or old-counterparty-only. Some normal episodes include irregular timing and novel counterparties. Some suspicious episodes are slower and involve established relationships. Use shared distributions for nuisance variables within matching profile/type/channel strata; the intentionally different joint temporal/relational structures carry the research signal.

## 8. Temporal, entity and accounting construction

Use a 180-day UTC observation horizon, with six 30-day reporting blocks. All four populations span the same horizon; this is entity-isolated evaluation, not a claim of chronological train/test separation.

To avoid an all-normal warm-up period, reserve 2,000 suspicious events per 30-day block overall. Train contributes 1,200, Validation 300, Final test 300, Independent 200 per block. Normal allocations are Train 8,800, Validation 2,200 and Final test 2,200 per block; Independent uses 1,467 in four blocks and 1,466 in two. Total block sizes are consequently four blocks of 16,667 and two of 16,666, exactly 100,000 overall. Domain/family assignments across blocks use constrained apportionment and remain independent of calendar semantics.

Initialize cohorts with varied activity bands and historical schedules. Distribute activation times in every partition independently of class; include established and cold-start wallets/agents. For episodes needing a baseline, schedule ordinary background transactions before them inside the same 100,000-event budget. Early suspicious campaign events retain positive membership even when evidence is weak; do not label them normal until later transactions reveal a pattern. Do not require 30 complete days before all positives can appear.

Generate latent plans first, then event facts, then perform a stable chronological merge across partitions. Resolve timestamp ties with a deterministic opaque tie key sampled independently of target and family. Assign global integer transaction IDs/event sequences only after that merge. Equal timestamps are permitted and must be audited; earlier equal-time events have lower IDs. IDs never encode scenario, class, agent activity band, or partition.

The admissible history for event i in partition P is:

`H(i, w) = {j in P: (timestamp_j, transaction_id_j) < (timestamp_i, transaction_id_i), timestamp_j >= timestamp_i - w}`

Use w = 1 hour, 24 hours, 7 days, or 30 days where required. All-history novelty uses the same strict ordering without a lower window boundary. The current amount and current endpoints may be used when a feature definition requires them; the current transaction must never enter its own historical aggregate. Features are evaluated before the current event updates historical state.

Balance and float feasibility are generation invariants: transfers debit sender and credit receiver; Cash-In credits the wallet and debits agent electronic float; Cash-Out debits the wallet and credits agent electronic float. Ordinary initial balances/float belong to entity metadata. No overdraft, nonexistent funding, or invalid agent is introduced selectively for suspicious events. If feasibility requires replenishment beyond initial conditions, it must be represented within the transaction budget or the entire provisional episode rescheduled; no unrecorded label-dependent top-up is allowed.

Maintain disjoint wallets, customers, agents, episodes and edges across partitions. Sample globally unique opaque V2 entity IDs from namespaces distinct from V1, then allocate them to partitions independently of label. Reuse the generator family definitions, not episode instances or entity histories. Do not import V1 transaction rows, features, predictions, labels, final-test records or independent records into V2 generation.

## 9. Independent ground truth

1. Commit the class, domain, family, strength, partition and event-budget tables before synthesizing events.
2. Select a latent routine, legitimate hard-negative, or suspicious campaign plan. Commit target membership for its planned events at this point.
3. Generate amounts, timing, counterparties and agent roles from that plan and shared nuisance distributions.
4. Apply only structural, accounting and quota checks to accept the provisional schedule. Never change target membership because a feature, rule or model fails to flag it.
5. Assign chronological IDs and map the precommitted labels one-to-one onto the final records.
6. Persist ground truth separately and verify every raw event has exactly one target.

Prohibited label inputs include `risk_score`, `risk_level`, `rule_score`, `rule_level`, `ai_confidence`, `ai_risk_level`, alerts, application decisions, model predictions and later features. No SMOTE, 50:50 resampling, prediction-driven rejection sampling, or V1-guided 'make this flag' loop is allowed.

The label denotes membership in a synthetic suspicious-pattern scenario. It is not a determination that a real person committed money laundering.

## 10. Leakage and holdout controls

| Risk | Required control |
|---|---|
| Target/scenario leakage | Separate ground truth; allowlist raw observable fields; forbid scenario names, signal tiers, narratives and family codes from X |
| Risk/rule/alert leakage | Do not import Flask or application scoring modules into the V2 generator or feature builder; those outputs are absent from schemas |
| Future leakage | Partition-local causal replay using the lexicographic timestamp/ID predicate; no full-episode totals or future graph topology in features |
| Current-event leakage | Compute historical aggregates before state update; test timestamp ties and current-event amount mutation later |
| Entity leakage | Disjoint customer, wallet and agent sets; validate both endpoints and serviced wallet; reject cross-partition edges |
| Identifier shortcuts | No raw IDs, partition strings, episode IDs or sequence numbers in the model matrix; use IDs only for grouping, joins and temporal ordering |
| Type/channel shortcuts | Both labels represented in every valid category; identical aggregate class proportions; inspect interactions within development strata |
| Timestamp/amount artifacts | Shared nuisance supports, class coverage through the horizon, and overlapping timing/amount patterns; no label-specific precision or rounding |
| Feature selection leakage | Feature design/selection and any diagnostic predictive probes use Train/Validation only; no holdout-driven ranking or filtering |
| Tuning leakage | Fit on Train; choose hyperparameters, threshold and model using Validation only; do not fit preprocessing on any holdout |
| Repeated holdout adaptation | Pre-register one frozen evaluation release; if results inform another iteration, those populations are no longer fresh holdouts |

Directory separation alone does not make a holdout unavailable. Before generation, appoint an independent data custodian or an equivalent restricted execution role. Final-test and independent raw data **and** labels must be inaccessible to the model-development account until the model, feature contract and decision threshold are frozen. Restrict them using separate storage/credentials or encryption whose key the developer does not hold. Public manifests contain approved schema/count/hash information only, not samples or per-scenario performance.

Train and Validation use separate random streams. Final test uses the same frozen population distribution with unseen entities and fresh randomness. Independent evaluation additionally uses predeclared, bounded variation in legitimate activity mix, schedule dispersion and episode parameters, within the same raw amount/type support and the exact count tables. Its variation policy is fixed before fitting; no changes are made to produce an attractive score. It tests a new synthetic population, not real-world generalization.

A restricted custodian can run preapproved, model-free structural/label-integrity checks on holdouts and expose only pass/fail and manifest counts. Distribution exploration, model-based audits and feature development remain restricted to Train/Validation. If no access-control arrangement is available, generation/training is **not ready**; a directory named `sealed` is not a substitute.

## 11. Compatibility with the existing 30-feature architecture

No V2 features are added or computed in this stage. Raw fields support the following existing ordered feature architecture. Numbers are one-based; software indices are number minus one.

| Order | Existing feature name | Raw history required |
|---:|---|---|
| 1 | `structuring_prior_tx_count_1h` | Sender events in preceding hour |
| 2 | `structuring_prior_value_sum_24h` | Sender amounts in preceding day |
| 3 | `structuring_same_day_prior_tx_count` | Sender events earlier on current UTC date |
| 4 | `structuring_repeated_amount_ratio_7d` | Prior sender amounts and current amount |
| 5 | `structuring_amount_cluster_dispersion_7d` | Prior sender amount variation |
| 6 | `structuring_near_threshold_history_ratio_7d` | Prior sender amounts and documented synthetic threshold |
| 7 | `network_outbound_counterparty_count_7d` | Prior sender-to-recipient edges |
| 8 | `network_inbound_counterparty_count_7d` | Prior contributors to current receiver |
| 9 | `network_outbound_counterparty_entropy_30d` | Sender counterparty/value distribution |
| 10 | `network_top_counterparty_value_share_30d` | Sender values by counterparty |
| 11 | `network_current_receiver_is_new` | Sender's all-prior recipient set and current receiver |
| 12 | `network_repeated_receiver_ratio_30d` | Prior receiver frequencies |
| 13 | `network_reciprocal_flow_ratio_7d` | Prior incoming/outgoing counterparty sets |
| 14 | `network_counterparty_set_change_7d` | Recipient sets in adjacent preceding 7-day windows |
| 15 | `network_pass_through_ratio_24h` | Prior incoming/outgoing wallet values |
| 16 | `network_shared_counterparty_concentration_7d` | Prior partition-local graph neighbourhoods |
| 17 | `agent_prior_tx_count_1h` | Agent-attributed prior events |
| 18 | `agent_prior_tx_count_7d` | Agent-attributed prior events |
| 19 | `agent_prior_value_sum_1h` | Agent-attributed prior amounts |
| 20 | `agent_prior_value_sum_7d` | Agent-attributed prior amounts |
| 21 | `agent_unique_wallet_count_7d` | Wallet endpoints associated with agent |
| 22 | `agent_wallet_value_hhi_7d` | Agent-associated values by wallet |
| 23 | `agent_repeat_wallet_ratio_7d` | Repeated wallet/agent relationships |
| 24 | `agent_current_wallet_is_new` | Current serviced/sender wallet and agent history, per frozen semantic contract |
| 25 | `agent_inbound_outbound_value_ratio_7d` | Agent attribution, cash type, wallet endpoints and explicit direction |
| 26 | `agent_high_value_event_share_7d` | Agent amounts and baseline/threshold required by chosen contract |
| 27 | `agent_hourly_tx_zscore_30d` | Agent timestamps and prior hourly counts |
| 28 | `agent_hourly_value_zscore_30d` | Agent timestamps and prior hourly values |
| 29 | `agent_burst_concentration_7d` | Agent timestamps at full date/time precision |
| 30 | `agent_shared_wallet_flow_concentration_7d` | Agent/wallet associations and prior wallet graph |

**Compatibility limitation:** the current offline V1 extractor and live V1 adapter share names/order but are not numerically identical. Verified differences include agent HHI (both endpoints versus sender only), repeat-wallet ratio, inbound/outbound ratio, high-value share, hourly z-scores, burst concentration, shared-wallet concentration, and equal-timestamp handling in counterparty-set change. The offline agent direction ratio is simplified; the live version measures a different quantity. The proposed explicit cash-direction facts preserve information without silently correcting either implementation.

Therefore this stage claims **raw-data support**, not drop-in numerical parity or proof that every scenario is learnable from the existing 30 outputs. In a separately approved feature stage, specify which V1 offline definition is the controlled reference, document any raw-name/unit mapping, and audit V2 replay parity. Any semantic correction is a separately reviewed feature decision, even if the count stays at 30. Do not edit either V1 extractor to accommodate this dataset.

## 12. Evaluation contract and required future audits

Evaluate a frozen model using probability of class 1 and a threshold selected only on Validation. Report Accuracy, Balanced Accuracy, Macro F1, Suspicious Precision, Suspicious Recall, Suspicious F1, Normal Recall, ROC-AUC, PR-AUC, False-Positive Rate and confusion matrix. Define PR-AUC as **average precision** for consistency with V1's training code; if trapezoidal PR area is also calculated, name it separately. Matrix ordering is `[[TN, FP], [FN, TP]]`, positive class is 1, and FPR is `FP/(FP+TN)`.

At final release, report Final test and Independent separately, plus validation development results with their selection role disclosed. Domain recall is `TP_domain / labelled_positive_count_domain`; family recall uses its own labelled-positive denominator. Do not infer domain performance from feature importances.

Each holdout has adequate explicit positive support: final test 600/domain and 150/family; independent 400/domain and 100/family. Report counts alongside rates, including phase and signal-strength breakdowns where denominators allow. Low sample counts must be visible. Use episode-aware uncertainty estimates in a later evaluation stage because events in a campaign are correlated; do not treat 150 related events as 150 independent cases.

Report false-positive rates separately on routine normal examples and H1–H8, as well as overall. A detector that improves positive recall by flagging legitimate payroll or busy agents is not automatically better.

Planned acceptance checks, to be implemented and run only after approval:

1. Exact 100,000 rows and all partition/class/domain/family/type/channel/strength budgets.
2. Exact entity counts, customer uniqueness, valid agent attribution, and no cross-partition edges or episodes.
3. Unique IDs, deterministic sequence, normalized timestamps, 180-day support, and correct tie handling.
4. Valid types/channels, no transfer self-loops, and consistent cash direction/serviced-wallet conventions.
5. Positive amounts, balance/float feasibility and no label-dependent invalid records.
6. Ground-truth one-to-one joins and precommitted label provenance; no labels derived from downstream outputs.
7. No feature-prohibited metadata in raw events; no direct identifiers in future model inputs.
8. No exact copied event sequences or graph templates across partitions after identifiers are removed.
9. On Train/Validation only: inspect amount, timing, channel and entity-activity overlap; later use simple one-variable diagnostic baselines to reveal easy shortcuts. Such audits never relabel individual records by model output.
10. Preserve ambiguous/early positives; report their counts rather than deleting hard cases to increase scores.
11. After feature-stage approval: causal replay, current/future exclusion, timestamp ties, numerical safety, dollar-unit conversion, and offline-reference parity.
12. Custodian verifies holdout access controls and runs only the preapproved structural checks before release.

Future V2 performance on a new dataset cannot by itself establish superiority over V1 performance on a different dataset. A fair common-evaluation protocol would require separate approval and protection of all holdouts; no V1 re-evaluation, tuning or model comparison is executed here.

## 13. Proposed V2 directory and file structure

The only authored artifact at this stage is this report. The workspace's `data`, `features`, `models` and `tests` directories are empty reservations. Everything else in the following tree is a **proposal for later approved stages**, not an existing dataset or executable implementation.

```text
ml_v2/
    reports/
        V2_STAGE1_DATASET_DESIGN.md            # this design report
        V2_DATASET_AUDIT.md                    # future
        V2_FEATURE_CONTRACT.md                 # future separate approval
        V2_EVALUATION_PROTOCOL.md              # future preregistration
    design/
        dataset_schema.json                   # future formal schema
        allocation_manifest.json              # future complete integer allocations
        scenario_manifest.json                # future committed scenario parameters
    src/
        dataset_generator.py                  # future, standalone; no Flask imports
        dataset_audit.py                      # future model-free structural audit
        feature_pipeline.py                   # future, separate review
        train.py                              # future; Train/Validation only
        evaluate_frozen.py                    # future restricted evaluation role
    data/
        development/
            train/{transactions.csv,ground_truth.csv,wallets.csv,agents.csv}
            validation/{transactions.csv,ground_truth.csv,wallets.csv,agents.csv}
        manifests/generation_manifest.json    # future public counts/hashes
        sealed/{final_test,independent}/       # future restricted mount or ciphertext only
    features/
        development/                          # future V2 matrices, never V1 paths
        sealed/                               # future restricted holdout matrices
    models/
        candidates/                           # future V2-only candidates
        frozen/                               # future V2-only approved artifact
    tests/
        test_dataset_contract.py              # future
        test_partition_isolation.py           # future
        test_ground_truth_independence.py     # future
        test_temporal_contract.py             # future
        test_no_v1_writes.py                   # future
    requirements-v2.lock                      # future isolated environment specification
```

The restricted holdout store must actually enforce the custody policy. It need not reside physically in this repository. Do not commit readable holdouts merely because `sealed/` appears in a path.

Future V2 programs must anchor outputs to an explicit V2 root, reject resolved output paths outside that root, refuse overwriting an existing dataset version, and avoid following symlinks/junctions into V1. Use a separate environment rather than changing the application's `requirements.txt` or `.venv`. Future tests must run with explicit V2-only discovery and temporary V2 paths; importing `server.py` is prohibited because it has startup/database side effects.

Do not execute the existing `ml_archive/ml_stage11_generate_100k_dataset_v2.py` for this new cycle: despite its filename, it targets the **V1** dataset name. Existing archived extractors and trainers also have V1 output defaults.

Repository deployment configuration can include the whole repository. V2 research files must not trigger an application deployment; a future deployment/exclusion decision requires separate approval. No deployment configuration is changed here.

## 14. WHY THIS DATASET SHOULD BE A STRONGER TRAINING DATASET THAN V1

The proposal addresses observed data limitations rather than promising a score increase:

- V1 raw data uses `transfer` for every event. V2 explicitly represents Cash-In, Cash-Out, direct transfers and agent-assisted transfers, with consistent monetary direction and balanced label coverage across categories.
- V1 suspicious metadata has one signal tier. V2 has precommitted weak/moderate/strong variation and preserves early campaign events, supporting a more honest account of difficult detection cases.
- Structuring varies jointly across fragment sizes, total value, spacing, activity windows, directions and preceding behaviour. Near-threshold placement is neither universal nor sufficient for a positive label.
- Half the normal population is explicitly budgeted for hard negatives, including legitimate graph patterns and agent spikes. False positives on those activities become a required evaluation outcome.
- Network and agent scenarios have nontrivial timing, relationship and baseline variation, rather than a single size or intensity signature.
- All populations retain exact support for each domain and family, and holdout access is controlled before development rather than relying on a descriptive folder name.
- Raw direction facts, deterministic IDs, explicit units and separate ground truth make later feature-contract auditing possible without modifying V1.

These changes should make the experiment more informative about behavioural generalization and false positives. They may also make classification harder. Higher accuracy or recall is a hypothesis to test, not an outcome claimed in advance. Synthetic labels and scenarios remain a limitation; no claim of field validity or actual criminal intent follows.

## 15. Approval boundary

Stage 1 deliverable: this design, with the exact budgets and future isolation requirements above.

Still pending before generation: approval of this design; designation of holdout custody; final versioned integer allocation/parameter manifests; and separate authorization to implement and audit the generator. Feature construction, model training and application integration each remain later stages. No existing V1 final-test or independent data may be used for fitting, tuning, feature selection, threshold selection or model selection.

V2 STAGE 1 COMPLETE — WAITING FOR APPROVAL.
