# MODEL V3 - STAGE 10A FEATURE CONTRACT

Version: `v3_stage10a_features_1`. Logical and serialized count: **32**, unchanged from Stage 10. This is a semantic repair, not a performance-driven extension. Stage 10's contract and outputs remain historical records. The freeze manifest records this file's hash before any full corrected extraction.

## Authority and resolved ambiguities

Stage 8 onset and architecture contracts control observable semantics. Stage 9 transactions and targets are frozen even where their evaluator may differ from the written design. Features never import a predicate evaluator or infer y from feature values.

N3 uses the Stage 8 architectural topology selection: no amount-gated path search, no complete N3 condition. The shortest chronological simple prior path is chosen; ties prefer the latest first-edge key, then lexicographically smallest whole edge-key sequence. The current amount divided by first-edge amount is a separate quantity, with no clipping or predicate cutoffs. The N3 predicate's adjacent-amount and return-amount conjunction is deliberately not an input feature; this resolves the request to respect amount semantics without returning an oracle flag.

N4 follows the exact Stage 8 anchor definition: earliest prior **W2W inflow** to the current outward wallet in (t-24h,t]. Cash-In alone is not a valid anchor. Cash-In after that anchor contributes to F and necessarily lies within the same 24h interval. The requested Cash-In-anchor test explicitly expects absence. Broadening anchor types would change the approved architecture. F sums inbound W2W and Cash-In from the anchor through key < T; O sums outward W2W and Cash-Out strictly after the anchor through T. No F>=100, 0.5..1 share test or remaining-balance gate is used in X. Non-outward Cash-In has share 0 and age missing. On W2W the subject for this pair is always the sender, including assisted W2W.

## Shared exact semantics

key=(UTC timestamp, integer transaction_id). Every historical query requires key < key(T). Recent windows R(L) are (t-L,t] with an OPEN lower time boundary and prior-key filtering; T is added only in explicitly inclusive calculations. Baselines B(L)=(t-L-28d,t-L] are disjoint from R(L), open at the lower and closed at the upper timestamp. The upper time boundary can include all its keys because it is strictly earlier than T. Calendar-day history is [UTC midnight,key(T)], including midnight. Sums retain integer minor units until a final ratio/USD conversion. No future records are inserted; each event updates histories once after emission. All partition state is fresh.

Structuring subject w is the serviced wallet for Cash-In/Out, and sender for every W2W (including assisted W2W). Only that wallet's cash and outgoing W2W events enter wallet activity. Receipt observes the receiver for coverage/network purposes without adding structuring activity. Both cash directions contribute wallet amount/activity. Direct W2W adds no agent service; assisted W2W adds one agent service at the explicitly serviced wallet, and never adds cash float. Cash-Out is positive and Cash-In negative for signed agent cash measures. Cash events do not enter the graph. Current endpoint changes may select different prior histories; invariance tests keep endpoints fixed when testing amount dependence.

Coverage begins with first prior observable endpoint/cash/service event, never private activation. Displayed coverage is capped at 28d; eligibility uses the UNCAPPED first-observation time. Full baseline coverage requires first observation <= t-L-28d. An event exactly at that lower boundary establishes coverage but is not counted in the open baseline window. Baseline count minima below are mandatory and use only the specified stream. Recent counts/distinct-wallet/value conditions from the complete predicates are NOT availability requirements.

## Missingness and cold starts

Nonnegative ratios and funding age use -1 only when unavailable. The signed changes use **-3**, outside both [-1,1] and [-2,2]. Legitimate -1 is retained; raw signed cash skews NEVER use a missing marker and have zero on no cash. There are no new availability columns; the feature count remains 32. Missingness is derived per column from this schema in audit sidecars, never by treating every -1 as missing. Future preprocessing must translate per-column markers explicitly and fit parameters on Train only.

On a first wallet event the inclusive count is 1, sum is its amount, cluster share is 1, band share is the current band indicator, day/hour counts are 1 and coverage is 0. Network inclusive counts are 1 for current W2W and 0 otherwise without history; path length is 0 and ratio is -1. No prior funding gives share -1 for outward roles and age -1; Cash-In share is 0. Agent current service count/top2 share are 1 when served, and 0 without an agent. All baseline ratios/changes are missing until their full baseline requirements hold. Zero denominators for valid empty shares/skews produce 0; baseline rates divide by max(1, expected count). A funding anchor or graph edge has strictly positive amount, enforced at input.

## Baseline eligibility table

For each row the baseline is B(L), fully observed for its entire 28 days. The recent window and baseline never overlap. Unavailable markers are as in the feature list.

| Feature | Recent L | Baseline stream | Minimum count | Additional requirements |
|---|---|---|---|---|
| `wallet_count_acceleration_1h` | 1h | wallet activity | 4 | none |
| `receiver_inflow_acceleration_24h` | 24h | W2W inflows | 4 | none |
| `sender_outflow_acceleration_24h` | 24h | W2W outflows | 4 | none |
| `agent_service_acceleration_1h` | 1h | agent services | 12 | none |
| `agent_wallet_growth_ratio_7d` | 7d | agent services | 12 | four distinct-wallet bucket counts |
| `agent_new_wallet_share_7d` | 7d | agent services | 12 | distinct-wallet union |
| `agent_top2_share_change_24h` | 24h | agent services | 20 | at least 5 distinct baseline wallets |
| `agent_cash_value_skew_change` | 24h | agent services | 12 | at least 8 baseline cash events |

## Exact ordered feature definitions

### 1. `current_amount_usd`

- Domain/subject: current; T.
- Formula and window: amount_minor / 100.
- Temporal scope: CURRENT; only the named current fields are used.
- Units: USD. Valid range: [0, unbounded]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable current activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 2. `current_is_cash_in`

- Domain/subject: current; T.
- Formula and window: 1 if Cash-In else 0.
- Temporal scope: CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, 1]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable current activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 3. `current_is_cash_out`

- Domain/subject: current; T.
- Formula and window: 1 if Cash-Out else 0.
- Temporal scope: CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, 1]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable current activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 4. `wallet_count_1h_inclusive`

- Domain/subject: structuring; w.
- Formula and window: count R_wallet(1h).
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [1, unbounded]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable structuring activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 5. `wallet_value_24h_inclusive`

- Domain/subject: structuring; w.
- Formula and window: sum amount_minor in R_wallet(24h) / 100.
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: USD. Valid range: [0, unbounded]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable structuring activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 6. `wallet_count_utc_day_inclusive`

- Domain/subject: structuring; w.
- Formula and window: count activity from UTC midnight through key(T).
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [1, unbounded]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable structuring activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 7. `wallet_active_hours_utc_day`

- Domain/subject: structuring; w.
- Formula and window: distinct UTC hour buckets since midnight through key(T).
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [1, 24]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable structuring activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 8. `wallet_current_amount_cluster_share_7d`

- Domain/subject: structuring; w.
- Formula and window: count abs(100*(amount_minor - T.amount_minor)) <= 5*T.amount_minor in R_wallet(7d) / count R_wallet(7d).
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, 1]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable structuring activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 9. `wallet_band_share_7d_inclusive`

- Domain/subject: structuring; w.
- Formula and window: count 700000 <= amount_minor <= 1050000 in R_wallet(7d) / count R_wallet(7d).
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, 1]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable structuring activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 10. `wallet_count_acceleration_1h`

- Domain/subject: structuring; w.
- Formula and window: count R_wallet(1h) / max(1, count B_wallet(1h)/672).
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: -1.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable structuring activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 11. `receiver_unique_sources_24h_inclusive`

- Domain/subject: network; receiver.
- Formula and window: distinct senders in R_inflow(24h); add T only for W2W.
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable network activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 12. `receiver_inflow_count_24h_inclusive`

- Domain/subject: network; receiver.
- Formula and window: count R_inflow(24h); add T only for W2W.
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable network activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 13. `receiver_inflow_acceleration_24h`

- Domain/subject: network; receiver.
- Formula and window: count R_inflow(24h) / max(1, count B_inflow(24h)/28).
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: -1.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable network activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 14. `sender_unique_destinations_24h_inclusive`

- Domain/subject: network; sender.
- Formula and window: distinct receivers in R_outflow(24h); add T only for W2W.
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable network activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 15. `sender_outflow_count_24h_inclusive`

- Domain/subject: network; sender.
- Formula and window: count R_outflow(24h); add T only for W2W.
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable network activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 16. `sender_outflow_acceleration_24h`

- Domain/subject: network; sender.
- Formula and window: count R_outflow(24h) / max(1, count B_outflow(24h)/28).
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: -1.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable network activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 17. `current_return_path_length`

- Domain/subject: network; current sender/receiver.
- Formula and window: length of selected prior chronological simple return path, 1..5 edges; 0 if absent/non-W2W.
- Temporal scope: PRIOR-ONLY graph + CURRENT endpoints/type; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, 5]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable network activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 18. `current_return_amount_ratio`

- Domain/subject: network; selected path.
- Formula and window: T.amount_minor / first selected path edge amount_minor; no monetary gate.
- Temporal scope: PRIOR graph + CURRENT amount; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: -1.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable network activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 19. `wallet_observed_onward_funding_share_24h`

- Domain/subject: network; outward wallet.
- Formula and window: O/F for current outward role and valid prior W2W anchor; 0 for Cash-In.
- Temporal scope: PRIOR + CURRENT outward amount; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: -1.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable network activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 20. `wallet_prior_funding_age_hours`

- Domain/subject: network; outward wallet.
- Formula and window: (t - anchor.timestamp) / 1h; absent/non-outward is missing.
- Temporal scope: PRIOR funding + CURRENT time/type/endpoints; only the named current fields are used.
- Units: hours. Valid range: [0, 24]; missing: -1.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable network activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 21. `agent_service_count_1h_inclusive`

- Domain/subject: agent; agent.
- Formula and window: count R_service(1h); 0 without agent.
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable agent activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 22. `agent_service_acceleration_1h`

- Domain/subject: agent; agent.
- Formula and window: count R_service(1h) / max(1, count B_service(1h)/672).
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: -1.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable agent activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 23. `agent_wallet_growth_ratio_7d`

- Domain/subject: agent; agent.
- Formula and window: distinct wallets R_service(7d) / max(1, median distinct counts in four preceding disjoint 7d buckets).
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, unbounded]; missing: -1.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable agent activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 24. `agent_new_wallet_share_7d`

- Domain/subject: agent; agent.
- Formula and window: size(recent distinct wallets minus baseline distinct wallet union) / size(recent distinct wallets).
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, 1]; missing: -1.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable agent activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 25. `agent_top2_count_share_24h`

- Domain/subject: agent; agent.
- Formula and window: two largest per-wallet event counts / count R_service(24h); 0 without agent.
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [0, 1]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable agent activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 26. `agent_top2_share_change_24h`

- Domain/subject: agent; agent.
- Formula and window: recent top2 share minus independently ranked pooled B_service(24h) top2 share.
- Temporal scope: PRIOR + CURRENT; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [-1, 1]; missing: -3.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable agent activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 27. `agent_cash_value_skew_24h`

- Domain/subject: agent; agent.
- Formula and window: (CashOutMinor - CashInMinor)/(CashOutMinor + CashInMinor) in R_service(24h); zero if no cash.
- Temporal scope: PRIOR + CURRENT cash only; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [-1, 1]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable agent activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 28. `agent_cash_count_skew_24h`

- Domain/subject: agent; agent.
- Formula and window: (CashOutCount - CashInCount)/(CashOutCount + CashInCount) in R_service(24h); zero if no cash.
- Temporal scope: PRIOR + CURRENT cash only; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [-1, 1]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable agent activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 29. `agent_cash_value_skew_change`

- Domain/subject: agent; agent.
- Formula and window: recent cash value skew minus cash value skew in B_service(24h).
- Temporal scope: PRIOR + CURRENT cash only; only the named current fields are used.
- Units: dimensionless count/indicator/ratio as defined. Valid range: [-2, 2]; missing: -3.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable agent activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 30. `wallet_history_coverage_days`

- Domain/subject: coverage; w.
- Formula and window: min(28, days from first prior observation of wallet endpoint/cash to t); 0 without prior history.
- Temporal scope: PRIOR-ONLY observation + CURRENT time/subject; only the named current fields are used.
- Units: days. Valid range: [0, 28]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable coverage activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 31. `receiver_history_coverage_days`

- Domain/subject: coverage; receiver.
- Formula and window: min(28, days from first prior receiver entity observation to t); 0 without prior history.
- Temporal scope: PRIOR-ONLY observation + CURRENT time/subject; only the named current fields are used.
- Units: days. Valid range: [0, 28]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable coverage activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

### 32. `agent_history_coverage_days`

- Domain/subject: coverage; agent.
- Formula and window: min(28, days from first prior service to t); 0 without agent/prior service.
- Temporal scope: PRIOR-ONLY observation + CURRENT time/subject; only the named current fields are used.
- Units: days. Valid range: [0, 28]; missing: never.
- Prior/current information and transaction treatment: shared semantics above apply to this subject/domain, including cash versus W2W and assisted service distinctions.
- Cold start/insufficient history/zero denominator: shared cold-start rules and baseline table apply; no target or recent predicate gate is used.
- Behavioural justification: represents observable coverage activity, topology, cash flow or coverage as a separate quantity; does not combine all reference conditions.

## Change log

A: enforce increasing edge keys during N3 traversal. B: use strict keys in every query, including same-time records. C: expire funding at the open 24h boundary; do not allow cash-only anchors. D: restore disjoint baselines, uncapped full-coverage tests and stream/count minima. E: use per-feature -1/-3 markers with valid negatives preserved. F: novelty is DISTINCT-wallet share, not service-event weighted. G: expand descriptive leakage checks and mutation tests. H: serialize two independent extractions and compare files. I: record explicit before/after allowlists and public-certificate hashes. J: freeze this version and its code hashes before extraction. Additional correction: assisted W2W structuring and funding use the sender, not the serviced receiver. No model-driven change is made.
