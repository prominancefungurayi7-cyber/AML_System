# MODEL V4 — INTEGRATION STAGE 1 APPLICATION INTEGRATION READINESS AUDIT

**D — V4 INTEGRATION BLOCKED BY INCOMPATIBLE DATA OR ARTIFACTS**

The blocker is **current application data compatibility**, not a failed model hash. The original Stage18 XGBoost and all Stage23 frozen references match. Existing records do not establish exact cash/agent roles, canonical cents, UTC precision or complete historical coverage. Missing historical semantics cannot be repaired by assigning defaults. A prospective canonical ledger and isolated inference service are feasible designs, but no integration is authorized by this report.

Audit and design only. No application import/startup, database connection, migration, prediction, model deserialization, fitting, extraction, transaction generation, frontend change or sealed evaluation access occurred. “Active” below means reachable in the checked source, not a claim that a deployed process was observed. Database findings describe repository DDL and queries; deployed schema, indexes, record quality and workload remain **NOT VERIFIED**. No credentials or environment secrets were inspected. Source locations are recorded in [application source index](../evidence/integration_stage1/application_source_index.json).

## 1. Current application architecture

[server.py](../../server.py) is the Flask/Flask-SocketIO entry point. [Procfile](../../Procfile) and [Dockerfile](../../Dockerfile) launch `server:app` using Gunicorn gthread, one worker/eight threads. The checked Docker image is Python 3.11; this differs from V4's frozen Python 3.14.3 runtime. [requirements.txt](../../requirements.txt) uses broad ML lower bounds rather than the frozen package versions.

`initialize_startup` runs database initialization/migrations, demo seeding, legacy model readiness and the background monitor. It runs under both the ordinary script entry and WSGI import. Importing the server would therefore exceed this audit's scope. The early `__main__` branch for `AML_EXPERIMENTAL_TEST_MODE=ON` launches the isolated V3 application before normal imports; its service also requires the V3 selector. WSGI does not take that branch.

`database.DatabaseAdapter` handles MySQL, PostgreSQL and SQLite; MySQL replaces `?` placeholders with `%s` and uses buffered dictionary cursors. `config.py` supports DATABASE_URL/MYSQL_URL and a MySQL default. This is configuration capability, not evidence of an active MySQL connection. `server.connect_db` delegates to the database module. Duplicate top-level helpers in server.py mean later definitions govern execution; the source index retains their positions.

```text
POST /customer/transaction or authorized admin scenario/generation route
  -> validate form, identify accounts, optional agent
  -> INSERT transactions (banking vocabulary, floating amount)
  -> server.process_transaction_event
       -> account lookup + screening + optional rule engine
       -> Stage13FeatureService queries prior transactions
       -> V1 Stage14ModelService -> probability at threshold .35
       -> behavioral profile read/update -> operational blending
       -> UPDATE transaction; INSERT alert if operational level qualifies
       -> optional CTR record; SAR-required flag
       -> broker publishes transaction / alert / ctr_report / stats
  -> caller balance updates and commit (customer route)
  -> balance/stats broadcasts, activity record, legacy training thread attempt
  -> React dashboard and alert detail/report pages

Background monitor -> pending Initiated rows -> same processing function
GET /api/v1/transactions -> paginated read, not a transaction submission API
```

Transaction and alert broadcasts currently occur inside processing **before the customer route commits**. A later rollback can therefore leave a client showing an uncommitted result. Admin generation catches failures and rolls back but also uses the same processing function. Future V4 delivery needs commit-aware publication, not simply another emit at the prediction line.

## 2. Existing AI execution path

The effective inference is `process_transaction_event` → `Stage13FeatureService.generate_features` → `get_stage14_model_service` → `Stage14ModelService.predict`. The 30 raw float features use database history ordered by `(timestamp,id)`, excluding current; the legacy query includes its lower time bound. These are **not** V4 formulas, roles, windows or sentinels. A minimal adapter forwards to the real connection. The Stage14 global singleton retains the first feature service/connection, despite per-connection initialization in server.py; closed-connection/concurrency behavior needs a later test. A V4 service must never retain a request DB connection in a singleton.

V1 probability >= .35 produces `suspicious_pattern`. For a normal prediction, `ai_confidence` is **1-p**; for a positive prediction it is **p**. It is thus predicted-class confidence, not a stable suspicious-class probability. The probability is mapped to a 0–100 score with .35 mapped to 40; then 70% of that score is blended with a behavioral term. Operational risk is the maximum of this result and rule score. With no behavioral/rule signal, a model-positive p=.35 can yield score28/low and no alert. This is a static arithmetic consequence of the code, not a new prediction experiment.

Exceptions at the model/server boundary set AI level absent/confidence0, and final AI fields can take behavioral values. There is also an earlier fallback: `Stage13FeatureService.generate_features` catches exceptions and returns30 zeros, while malformed history timestamps can return empty history. These can conceal feature failures before model prediction. Description can become routine despite inference failure. `generated_label` can override operational risk through `_calibrate_generated_transaction_risk` when a caller supplies it. These behaviors must not define V4 output or train V4. The principal admin generator explicitly avoids its old training call; customer and monitor training hooks and startup readiness remain reachable elsewhere.

The effective server `_RULE_ENGINE_ENABLED` default is **False**, as is the separate transactions-module flag. The effective server setter governs processing; merely enabling a helper-module flag would not prove the server branch is enabled. Screening lookups still occur, but rule assessment and addition of screening score evidence are inside the enabled branch. These are checked-source defaults, not observed deployment settings.

## 3. Legacy-model inventory and dependency map

| Component / classification | Artifact, loader and representation | Reachability and fallback |
| --- | --- | --- |
| V1 frozen application inference | `ml/stage14/stage14_frozen_model.pkl`; `ai_stage14_model.py`, joblib; GradientBoosting, 30 fields named in `ai_stage13_features.FEATURE_NAMES`; no added scaler in service | Current transaction inference. Threshold .35; binary classes; assumes probability column1. Has hard-prediction-as-probability fallback if no predict_proba. Errors propagate to server blending. |
| Legacy banking model, distinct from V1 service | `ml_archive/models/aml_ai_model.pkl`, adjacent `aml_ai_model_meta.json`; `ai_core.load_ai_model`; joblib bundle/Pipeline/direct-estimator handling | `predict_risk_level` imported but not called by current transaction processing. Metadata API can load it; startup readiness/customer/monitor hooks can train it; admin clear calls delete. Historical archive absence remains documented; this audit does not restore or load it. |
| Legacy banking preprocessing | `ai_core.transaction_features`, 18 fields; StandardScaler + RandomForest and separate IsolationForest in training | Defaults include fabricated zero statistics; labels derive from stored operational risk and bootstrap rows. Argmax class confidence; anomaly thresholds -.05/-.15 can override classes. Never reuse for V4. |
| Legacy Stage16B compatibility | Same legacy model loader accepts direct estimator; optional root `aml_label_encoder.pkl` via pickle | Numeric class fallback 0 normal,1 super_suspicious,2 suspicious; shape ValueError can delete legacy model. This does not identify the frozen V4 target. |
| Behavioral profiler | `behavioral_profiling.py` and `ai_core.BehavioralProfiler`; stored `behavioral_profiles` JSON | Active alongside V1. Up to500 historical transactions for initial profile; cold-start neutral result; subsequent adaptive profile updates. Not frozen V4 preprocessing/history. |
| Rule engine / screening | `aml_rules.assess_rules`, `screening.py`; no model artifact | Active operational scores when enabled, sanctions context, CTR/SAR logic. Rule queries cap rows200 and do not implement V4 history. No compliance-law validation claimed here. |
| V3 local experiment | `experimental_v3/service.py`, manifest, Stage11 HGB `ml_v3/models/stage11_candidates/s11_09_hist_gradient_boosting.joblib`; raw Stage11 preprocessing,32 fields, threshold .50 | Explicit local test launcher only, separate routes/authentication/events; integrity-pinned, no V1 fallback. Not production transaction inference and not a V4 adapter. |
| V4 original development reference | `ml_v4/development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib`; embedded FrozenPreprocessor;40→42;.50 | Preserved only. No application reference path reaches it. Verified hash, not loaded. |
| V4 comparators/experiments | Stage18 HGB; Stage21 matrices; Stage22 A40/B44 XGB/HGB pipelines | Research artifacts only, all preserved. Stage22 A40-XGB happens to have the same bytes as the original in saved manifests; **path identity must still enforce original Stage18 authority**. |
| Obsolete helpers and archive scripts | Server's older blending/training helpers, root test files and archived diagnostic scripts | Presence is not evidence of live execution. Effective server overrides and direct call sites determine reachability. No archive diagnostic script executed. |

Legacy18 order: amount, sender_avg_amount, sender_max_amount, amount_to_sender_avg, amount_z_score, amount_deviation_from_baseline_30d, tx_frequency_7d, tx_frequency_30d, frequency_change_vs_avg_7d, sender_tx_count_24h, sender_volume_24h, same_day_count, rapid_transfer_count, is_new_recipient, unique_recipients_7d, hour, is_off_hours, counterparty_change_score_7d. Full V1 ordered names remain in its preserved source; no naming-based substitution is allowed.

```text
server -> V1 Stage13 features -> V1 Stage14 model             [active inference]
       -> behavioral_profiling -> ai_core profiler           [active signal]
       -> rules/screening -> operational risk                [active signal]
       -> ai_core train/delete/metadata                     [legacy side paths]
explicit local test launcher -> experimental_v3             [opt-in only]
Stage23 freeze -> original Stage18 V4 pipeline               [preserved, disconnected]
Stage21/22 -> 44-feature experiments and A40 refits           [preserved, disconnected]
```

## 4. Forty-feature feasibility matrix

The following matrix is part of this report and is also available as [JSON](../evidence/integration_stage1/feature_feasibility.json) and [standalone table](../evidence/integration_stage1/feature_feasibility.md). Exact eligibility/formulas/current-event inclusion are included for every row in JSON, copied from the verified frozen specification. Each row requires additional canonical validation and replay/state. **None is certified computable over arbitrary current live records**; some become straightforward for a validated subset, but that subset and its complete surrounding history have not been established.

| # / feature | Raw fields / database columns | Window / subject | Graph | Missingness / feasibility gap |
| --- | --- | --- | --- | --- |
| 1 amount_minor | amount_minor, currency / amount,currency | current / current event | none | Never missing; schema rejects absent/nonpositive amount; DOUBLE and unbounded input; exact cents/range not guaranteed |
| 2 transaction_type | transaction_type, channel, agent_id, serviced_wallet, agent_flow_direction / transaction_type,channel,agent_id,sender_account,receiver_account | current / current event | none | Never missing; Cash roles and channel vocabulary ambiguous; two role fields absent |
| 3 wallet_count_1h | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type, serviced_wallet, amount_minor / id,timestamp,sender_account,receiver_account,transaction_type,amount plus NEW serviced_wallet | 1h / wallet subject | none; incoming W2W contributes observation age only | 0 only when mathematically zero; current ensures nonempty activity; Cash subject, exact money, complete UTC-keyed activity and first observation unverified |
| 4 wallet_value_1h | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type, serviced_wallet, amount_minor / id,timestamp,sender_account,receiver_account,transaction_type,amount plus NEW serviced_wallet | 1h / wallet subject | none; incoming W2W contributes observation age only | 0 only when mathematically zero; current ensures nonempty activity; Cash subject, exact money, complete UTC-keyed activity and first observation unverified |
| 5 wallet_max_value_share_1h | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type, serviced_wallet, amount_minor / id,timestamp,sender_account,receiver_account,transaction_type,amount plus NEW serviced_wallet | 1h / wallet subject | none; incoming W2W contributes observation age only | 0 only when mathematically zero; current ensures nonempty activity; Cash subject, exact money, complete UTC-keyed activity and first observation unverified |
| 6 wallet_activity_acceleration_1h | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type, serviced_wallet, amount_minor / id,timestamp,sender_account,receiver_account,transaction_type,amount plus NEW serviced_wallet | 1h + preceding28d / wallet subject | none; incoming W2W contributes observation age only | -1 if baseline-ineligible; Cash subject, exact money, complete UTC-keyed activity and first observation unverified |
| 7 wallet_similar_amount_count_7d | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type, serviced_wallet, amount_minor / id,timestamp,sender_account,receiver_account,transaction_type,amount plus NEW serviced_wallet | 7d / wallet subject | none; incoming W2W contributes observation age only | 0 only when mathematically zero; current ensures nonempty activity; Cash subject, exact money, complete UTC-keyed activity and first observation unverified |
| 8 wallet_similar_amount_share_7d | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type, serviced_wallet, amount_minor / id,timestamp,sender_account,receiver_account,transaction_type,amount plus NEW serviced_wallet | 7d / wallet subject | none; incoming W2W contributes observation age only | 0 only when mathematically zero; current ensures nonempty activity; Cash subject, exact money, complete UTC-keyed activity and first observation unverified |
| 9 wallet_count_utc_day | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type, serviced_wallet, amount_minor / id,timestamp,sender_account,receiver_account,transaction_type,amount plus NEW serviced_wallet | UTC day to current / wallet subject | none; incoming W2W contributes observation age only | 0 only when mathematically zero; current ensures nonempty activity; Cash subject, exact money, complete UTC-keyed activity and first observation unverified |
| 10 wallet_active_hours_utc_day | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type, serviced_wallet, amount_minor / id,timestamp,sender_account,receiver_account,transaction_type,amount plus NEW serviced_wallet | UTC day to current / wallet subject | none; incoming W2W contributes observation age only | 0 only when mathematically zero; current ensures nonempty activity; Cash subject, exact money, complete UTC-keyed activity and first observation unverified |
| 11 wallet_day_count_growth | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type, serviced_wallet, amount_minor / id,timestamp,sender_account,receiver_account,transaction_type,amount plus NEW serviced_wallet | UTC day + prior28 calendar days / wallet subject | none; incoming W2W contributes observation age only | -1 if baseline-ineligible; Cash subject, exact money, complete UTC-keyed activity and first observation unverified |
| 12 wallet_near_band_count_7d | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type, serviced_wallet, amount_minor / id,timestamp,sender_account,receiver_account,transaction_type,amount plus NEW serviced_wallet | 7d / wallet subject | none; incoming W2W contributes observation age only | 0 only when mathematically zero; current ensures nonempty activity; Cash subject, exact money, complete UTC-keyed activity and first observation unverified |
| 13 network_in_count_24h | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type / id,timestamp,sender_account,receiver_account,transaction_type | 24h / current W2W receiver | Directed W2W incident edges; incoming receiver or outgoing sender | 0 for non-W2W; Directed canonical history and first-observation completeness unverified |
| 14 network_in_distinct_24h | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type / id,timestamp,sender_account,receiver_account,transaction_type | 24h / current W2W receiver | Directed W2W incident edges; incoming receiver or outgoing sender | 0 for non-W2W; Directed canonical history and first-observation completeness unverified |
| 15 network_in_acceleration_24h | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type / id,timestamp,sender_account,receiver_account,transaction_type | 24h + preceding28d / current W2W receiver | Directed W2W incident edges; incoming receiver or outgoing sender | -1 if non-W2W or baseline-ineligible; Directed canonical history and first-observation completeness unverified |
| 16 network_out_count_24h | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type / id,timestamp,sender_account,receiver_account,transaction_type | 24h / current W2W sender | Directed W2W incident edges; incoming receiver or outgoing sender | 0 for non-W2W; Directed canonical history and first-observation completeness unverified |
| 17 network_out_distinct_24h | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type / id,timestamp,sender_account,receiver_account,transaction_type | 24h / current W2W sender | Directed W2W incident edges; incoming receiver or outgoing sender | 0 for non-W2W; Directed canonical history and first-observation completeness unverified |
| 18 network_out_acceleration_24h | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type / id,timestamp,sender_account,receiver_account,transaction_type | 24h + preceding28d / current W2W sender | Directed W2W incident edges; incoming receiver or outgoing sender | -1 if non-W2W or baseline-ineligible; Directed canonical history and first-observation completeness unverified |
| 19 prior_return_path_min_length_7d | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type, amount_minor / id,timestamp,sender_account,receiver_account,transaction_type,amount | prior7d / current W2W endpoints | All chronological simple W2W return paths, 1..5 prior edges; receiver to current sender; no amount filter | -1 for no path or non-W2W; Complete directed history, exact money and UTC keys unverified |
| 20 prior_return_path_count_7d | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type, amount_minor / id,timestamp,sender_account,receiver_account,transaction_type,amount | prior7d / current W2W endpoints | All chronological simple W2W return paths, 1..5 prior edges; receiver to current sender; no amount filter | 0 for no path/non-W2W; Complete directed history, exact money and UTC keys unverified |
| 21 prior_path_min_max_log_change_7d | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type, amount_minor / id,timestamp,sender_account,receiver_account,transaction_type,amount | prior7d / current W2W endpoints | All chronological simple W2W return paths, 1..5 prior edges; receiver to current sender; no amount filter | -1 for no path/non-W2W; Complete directed history, exact money and UTC keys unverified |
| 22 current_to_selected_path_first_value_ratio | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type, amount_minor / id,timestamp,sender_account,receiver_account,transaction_type,amount | prior7d + current / current W2W endpoints | All chronological simple W2W return paths, 1..5 prior edges; receiver to current sender; no amount filter | -1 for no path/non-W2W; Complete directed history, exact money and UTC keys unverified |
| 23 wallet_pass_through_fraction_24h | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type, serviced_wallet, amount_minor / id,timestamp,sender_account,receiver_account,transaction_type,amount plus NEW serviced_wallet | anchor..current within 24h / current outward wallet | Prior W2W funding anchor plus subsequent cash/activity | -1 if current not outward or no prior W2W anchor; Cash subject, exact money, complete UTC-keyed activity and first observation unverified |
| 24 wallet_prior_funding_residual_minor_24h | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type, serviced_wallet, amount_minor / id,timestamp,sender_account,receiver_account,transaction_type,amount plus NEW serviced_wallet | anchor..current within 24h / current outward wallet | Prior W2W funding anchor plus subsequent cash/activity | NaN if current not outward or no anchor; numeric -1 may be a valid residual; Cash subject, exact money, complete UTC-keyed activity and first observation unverified |
| 25 agent_wallet_growth_ratio_7d | transaction_id, event_timestamp, agent_id, serviced_wallet, transaction_type, agent_flow_direction, amount_minor / id,timestamp,agent_id,transaction_type,amount plus NEW serviced_wallet,agent_flow_direction | 7d + preceding28d / current agent | none; agent service history across wallets | -1 absent agent or A1 baseline-ineligible; Agent optional; serviced endpoint absent; no canonical service history |
| 26 agent_distinct_wallets_7d | transaction_id, event_timestamp, agent_id, serviced_wallet, transaction_type, agent_flow_direction, amount_minor / id,timestamp,agent_id,transaction_type,amount plus NEW serviced_wallet,agent_flow_direction | 7d / current agent | none; agent service history across wallets | 0 absent agent; Agent optional; serviced endpoint absent; no canonical service history |
| 27 agent_new_wallet_count_7d | transaction_id, event_timestamp, agent_id, serviced_wallet, transaction_type, agent_flow_direction, amount_minor / id,timestamp,agent_id,transaction_type,amount plus NEW serviced_wallet,agent_flow_direction | 7d + preceding28d / current agent | none; agent service history across wallets | -1 absent agent or A1 baseline-ineligible; Agent optional; serviced endpoint absent; no canonical service history |
| 28 agent_new_wallet_share_7d | transaction_id, event_timestamp, agent_id, serviced_wallet, transaction_type, agent_flow_direction, amount_minor / id,timestamp,agent_id,transaction_type,amount plus NEW serviced_wallet,agent_flow_direction | 7d + preceding28d / current agent | none; agent service history across wallets | -1 absent agent or A1 baseline-ineligible; Agent optional; serviced endpoint absent; no canonical service history |
| 29 agent_top2_count_share_24h | transaction_id, event_timestamp, agent_id, serviced_wallet, transaction_type, agent_flow_direction, amount_minor / id,timestamp,agent_id,transaction_type,amount plus NEW serviced_wallet,agent_flow_direction | 24h / current agent | none; agent service history across wallets | 0 absent agent; Agent optional; serviced endpoint absent; no canonical service history |
| 30 agent_top2_share_change_24h | transaction_id, event_timestamp, agent_id, serviced_wallet, transaction_type, agent_flow_direction, amount_minor / id,timestamp,agent_id,transaction_type,amount plus NEW serviced_wallet,agent_flow_direction | 24h + preceding28d / current agent | none; agent service history across wallets | -3 absent agent or A2 baseline-ineligible; valid range[-1,1]; Agent optional; serviced endpoint absent; no canonical service history |
| 31 agent_service_acceleration_1h | transaction_id, event_timestamp, agent_id, serviced_wallet, transaction_type, agent_flow_direction, amount_minor / id,timestamp,agent_id,transaction_type,amount plus NEW serviced_wallet,agent_flow_direction | 1h + preceding28d / current agent | none; agent service history across wallets | -1 absent agent or A3 baseline-ineligible; Agent optional; serviced endpoint absent; no canonical service history |
| 32 agent_distinct_wallets_1h | transaction_id, event_timestamp, agent_id, serviced_wallet, transaction_type, agent_flow_direction, amount_minor / id,timestamp,agent_id,transaction_type,amount plus NEW serviced_wallet,agent_flow_direction | 1h / current agent | none; agent service history across wallets | 0 absent agent; Agent optional; serviced endpoint absent; no canonical service history |
| 33 agent_cash_in_count_24h | transaction_id, event_timestamp, agent_id, serviced_wallet, transaction_type, agent_flow_direction, amount_minor / id,timestamp,agent_id,transaction_type,amount plus NEW serviced_wallet,agent_flow_direction | 24h / current agent | none; agent service history across wallets | 0 absent agent or no cash-in; Agent optional; serviced endpoint absent; no canonical service history |
| 34 agent_cash_out_count_24h | transaction_id, event_timestamp, agent_id, serviced_wallet, transaction_type, agent_flow_direction, amount_minor / id,timestamp,agent_id,transaction_type,amount plus NEW serviced_wallet,agent_flow_direction | 24h / current agent | none; agent service history across wallets | 0 absent agent or no cash-out; Agent optional; serviced endpoint absent; no canonical service history |
| 35 agent_cash_in_value_24h | transaction_id, event_timestamp, agent_id, serviced_wallet, transaction_type, agent_flow_direction, amount_minor / id,timestamp,agent_id,transaction_type,amount plus NEW serviced_wallet,agent_flow_direction | 24h / current agent | none; agent service history across wallets | 0 absent agent or no cash-in; Agent optional; serviced endpoint absent; no canonical service history |
| 36 agent_cash_out_value_24h | transaction_id, event_timestamp, agent_id, serviced_wallet, transaction_type, agent_flow_direction, amount_minor / id,timestamp,agent_id,transaction_type,amount plus NEW serviced_wallet,agent_flow_direction | 24h / current agent | none; agent service history across wallets | 0 absent agent or no cash-out; Agent optional; serviced endpoint absent; no canonical service history |
| 37 agent_cash_distinct_wallets_24h | transaction_id, event_timestamp, agent_id, serviced_wallet, transaction_type, agent_flow_direction, amount_minor / id,timestamp,agent_id,transaction_type,amount plus NEW serviced_wallet,agent_flow_direction | 24h / current agent | none; agent service history across wallets | 0 absent agent or no cash; Agent optional; serviced endpoint absent; no canonical service history |
| 38 agent_cash_value_skew_change | transaction_id, event_timestamp, agent_id, serviced_wallet, transaction_type, agent_flow_direction, amount_minor / id,timestamp,agent_id,transaction_type,amount plus NEW serviced_wallet,agent_flow_direction | 24h + preceding28d / current agent | none; agent service history across wallets | -3 absent agent or A4 baseline-ineligible; valid range[-2,2]; Agent optional; serviced endpoint absent; no canonical service history |
| 39 wallet_observed_coverage_days | transaction_id, event_timestamp, sender_wallet, receiver_wallet, transaction_type, serviced_wallet, amount_minor / id,timestamp,sender_account,receiver_account,transaction_type,amount plus NEW serviced_wallet | all prior; scalar first observation retained / wallet subject | none; incoming W2W contributes observation age only | 0 on first observation; never private activation; Cash subject, exact money, complete UTC-keyed activity and first observation unverified |
| 40 agent_observed_coverage_days | transaction_id, event_timestamp, agent_id, serviced_wallet, transaction_type, agent_flow_direction, amount_minor / id,timestamp,agent_id,transaction_type,amount plus NEW serviced_wallet,agent_flow_direction | all prior; scalar first observation retained / current agent | none; agent service history across wallets | 0 absent agent or first service; Agent optional; serviced endpoint absent; no canonical service history |

## 5. Raw-schema mapping

A=directly present; B=deterministically derivable under stated verified preconditions; C=missing but addable prospectively; D=ambiguous/incompatible for existing records. Classification refers to semantics, not just similar names.

| V4 field | Current source | Class and exact treatment |
| --- | --- | --- |
| transaction_id | transactions.id | A. Positive integer <2^63; preserve IDs/full-key order. Transport as decimal string if beyond browser safe integer; no renumbering or JS rounding. |
| event_timestamp | timestamp | D generally; B only for a documented timezone-aware instant. Customer uses UTC isoformat; DDL variants use VARCHAR or TIMESTAMP without explicit fractional precision/timezone policy. Require exact UTC `YYYY-MM-DDTHH:MM:SS.ffffffZ`. Never guess timezone or replace malformed values with now. |
| sender_wallet | sender_account | A identifier, conditional semantics. Stable namespace mapping; cash must share sender/receiver/serviced endpoint. Bank account identity does not establish mobile-money role. |
| receiver_wallet | receiver_account | A identifier, same qualification; W2W must have different endpoints. |
| amount_minor | amount DOUBLE/REAL | D for unverified history; B only from authoritative exact two-decimal USD value. Parse prospective decimal text without float, require integral cents, no rounding/clipping. Frozen validator permits1..1,500,000 cents only. |
| currency | currency added by migration; customer inserts USD | A where actually captured; D for old rows whose default is not evidence. No conversion of other currencies. |
| transaction_type | deposit/withdraw/transfer | D generally. B only once event meaning is verified: actual agent cash deposit→cash_in, agent cash withdrawal→cash_out, wallet transfer→wallet_to_wallet. ACH/payroll/card/ATM/bank deposit vocabulary cannot automatically establish these meanings. |
| channel | online/mobile/branch/ATM/etc.; customer always writes online | D. Canonical direct_wallet requires genuine unassisted W2W; agent requires explicit agent service. Cannot infer solely from existing channel label or non-null agent. |
| agent_id | nullable BIGINT, agents FK | A when recorded and semantically genuine; stable string identity mapping required by Event. Missing cash agent is D, not absence-of-agent sentinel. Direct W2W uses empty string. |
| serviced_wallet | no column | C prospectively, D for ambiguous historical assisted W2W. Cash has B derivation from equal endpoints only after cash roles are proven. Assisted transfer must explicitly identify exactly one serviced endpoint. |
| agent_flow_direction | no column | C prospectively; B from already proven canonical type: cash_in/cash_out or none for W2W. Never infer from agent counterparty alone. |

Adding columns cannot recover old unknown values. Unsupported historical rows must not be silently filtered: a relevant omitted event changes later windows/paths/age. An unknown historical gap requires inference_error until complete provenance is established or a separately approved, truthfully scoped observation boundary exists. Account creation and private activation dates are not first observed participation.

## 6. Historical-data requirements

Use exact integer microsecond UTC times and `(timestamp,transaction_id)` ordering. Prior keys strictly less than current; same-time smaller IDs count, larger IDs do not. Recent interval is `(t-window,t]` over prior keys, adding current once where specified. Baseline is `(t-window-28d,t-window]`; a row exactly at the recent lower bound belongs to baseline. Wallet activity is outgoing W2W plus cash at serviced wallet, not incoming W2W; incoming establishes observation age and directed funding/history.

| Requirement | Frozen implementation requirement |
| --- | --- |
| 1 hour | Wallet recent count/value/share and agent services; baseline28d offset1h,672-hour normalization. Wallet >=4 baseline activities and age28d1h; agent >=12 baseline services and same age. |
| UTC day | Midnight inclusive to current; prior28 complete UTC calendar days including zero days for median. Wallet age reaches prior-day-window start and >=4 baseline activities. Not rolling24h. |
| 24 hours | Directed W2W counts/breadth; baseline28d offset24h gives29d coverage and >=4 directed baseline edges. Agent top2 needs29d,20 baseline services and5 distinct serviced wallets. Agent cash skew needs29d,12 baseline services and8 baseline cash events. |
| 7 days | Wallet similar/band quantities; all chronological simple prior W2W return paths1..5 edges. Agent current distinct wallets; baseline4 seven-day bins in `(t-35d,t-7d]`. Growth/newness requires35d observed age and12 baseline services. |
| N4 funding | Earliest prior incoming W2W in24h anchors funding. Include subsequent incoming W2W and cash-in, subtract outward W2W/cash-out after anchor; ratio includes current outflow, residual excludes current. No anchor means -1 ratio/NaN residual. |
| 30/35 days | V4 has no generic30d substitution.29d,28d1h/calendar windows and35d have distinct boundaries. Both displayed coverage fields cap at35d. |
| All prior observations | Persistent true first wallet/agent observations, duplicate-ID knowledge and replay watermark. A35d query alone cannot prove age or absence of earlier events. |

Frozen extractor prunes deque events <=t-35d on access, but keeps first observations and all IDs; inactive queues are not globally evicted. Full canonical chronological replay from a known complete ledger is the simplest reference design. A35d replay with externally injected first-observation/state metadata is **not an existing supported API** and would need a separate parity-reviewed adapter. A validated checkpoint may later reduce replay only after exact state serialization, provenance, invalidation and restart tests.

N3 requires graph closure beyond the current wallet pair: all relevant W2W edges reachable on candidate paths from receiver to sender. Subject-only SQL or arbitrary neighbor/row caps lose paths. Selection minimizes prior adjacent amount spread, then length, then lexicographic edge keys; current amount does not choose the path. Do not replace exhaustive enumeration by shortest path or qualifying-path flags.

## 7. Database readiness and performance

Source DDL has id, accounts, floating amount, type, timestamp and optional agent. `server._migrate_mysql` adds operational columns, but not serviced_wallet, flow direction, canonical cents or an inference record. `database.py` returns MySQL table DDL without index creation. `clean_aml_mysql_schema.sql` includes single-column sender/receiver/time/agent indexes and different timestamp/report layouts; it is a destructive reset script and was only read. The multiple schema sources do not prove which layout exists remotely.

Later read-only schema/data verification must establish column types, microsecond precision, UTC connection settings, exact monetary provenance, retention/completeness, immutable corrections and deployed index definitions. Candidate indexes for review: `(timestamp_us,id)`, `(sender_wallet,timestamp_us,id)`, `(receiver_wallet,timestamp_us,id)`, `(agent_id,timestamp_us,id)` and wallet activity access by serviced wallet/type. These are design suggestions, not migrations or measured query plans.

Potential cost: repeated broad legacy SQL scans; replay of long ledger; combinatorial paths in dense graphs; growing ID sets; inactive-state memory; concurrent requests and graph components spanning wallets; multi-instance ordering; late-arriving events and transaction isolation. Paging is acceptable only with complete keyset traversal, consistent snapshot and no dropped rows. Resource exhaustion must produce a distinct error, never a truncated feature. Stage21 timings are development measurements, not serving latency guarantees. No load test or query optimization ran.

## 8. V4 inference architecture and reusable modules

```text
Mobile-Money Transaction (prospectively validated, explicit roles)
        |
Flask Transaction API / committed canonical ledger
        |
MySQL Transaction History + completeness/ordering metadata
        |
Canonical V4 Event + consistent prior context
        |
Frozen V4 Historical Feature Extraction (emit before state update)
        |
40 Frozen Features: v4.features.1
        |
Embedded fitted FrozenPreprocessor (transform only)
        |
42 Model Inputs
        |
Original frozen Stage18 XGBoost
        |
Suspicious Probability p(class 1)
        |
Threshold >= 0.50
   +----+----------------+
   |                     |
normal             suspicious_pattern
   |                     |
inference record    inference record + review alert
   +----------+----------+
              |
       atomic MySQL commit + outbox
              |
       Socket.IO / authorized SSE
              |
       Compliance Dashboard / investigation

Rule engine -> separate rule score/level -> operational policy/alert reasons
Any technical failure -> inference_error (neither binary branch)
```

Reuse [extractor.py](../development_features/extractor.py) and observable-only [stage16r_contract.py](../generation/stage16r_contract.py), verified with the feature JSON and [preprocessing.py](../development_training/preprocessing.py). The contract's location under generation does not make it a generator: Event/validation/time helpers are observable-only. Its family-name constant is unused by inference; do not expose labels or import evaluator modules. The extractor reads feature JSON and alters sys.path for contract imports; a future controlled package/import setup must verify module origin and preserve these frozen bytes.

Do not reuse development partition loaders, extraction runners, trainers, comparison scripts, evaluators, generators, private provenance or ground-truth joins. Do not copy V1 or V3 features into V4. Structured input must be exactly39 float64 fields plus U16 transaction_type in frozen40 order. Pass this to the **embedded pipeline once**, not to a separately refitted or double-applied preprocessor.

Prefer a dedicated inference runtime with no training or business-database credentials. Application owns authorized canonical queries and persistence; service owns trusted model and request-local replay state. A shared mutable Extractor is unsafe across gthread requests: step computes then mutates queues/IDs; an inference/commit failure must discard speculative state. Future persistent state requires serialized consumption, idempotent commit, snapshot/watermark validation and replay after rollback/restart. The audit implements neither strategy.

## 9. Model-loader and integrity design

Verified freeze `v4.development.freeze.stage23.1`, feature `v4.features.1`, original Stage18 pipeline SHA-256:

`555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18`

All14 named Stage23 artifact references match; [freeze verification](../evidence/integration_stage1/freeze_verification.json) records expected/actual bytes. Exact original path is `ml_v4/development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib`. The standalone preprocessor is a verification reference, not a second transform stage.

Future loader sequence: trusted fixed manifest/path, resolved path and source-origin validation, verify model/preprocessor/extractor/contract/feature hashes, verify runtime, then load trusted joblib bytes once in isolated runtime. No upload/path parameter, mtime-based model choice, fallback, external import shadowing or write-capable model directory. Avoid hash/load races by loading the exact verified bytes and using an immutable release. Hashing alone is not authorization to load untrusted pickle.

Verify `preprocessing.FrozenPreprocessor` resolves to the frozen source; full mode/no drops/no only-subset; names40 and encoded columns42; saved imputer/scaler state; estimator expected XGB configuration/input42/classes `[0,1]`; threshold >=.50. Read class1 by validated class identity, not unverified column convention. Check inference probabilities shape/finiteness/range. Fail loader availability on any mismatch; never bootstrap, refit or switch to A40/B44/HGB/V1/V3.

Pins: Python3.14.3, NumPy2.4.3, sklearn1.9.0, XGBoost3.4.1, one inference thread. Stage23 supplemental SciPy1.18.0/joblib1.5.3/threadpoolctl3.6.0 are current metadata pins, not historical wheel locks. Reproducible package/image hashes and approved fixture/probability parity remain future gates. Current Python3.11 Docker + broad requirements is not approved to deserialize this artifact.

## 10. Prediction contract

Proposed versioned nested `v4_inference` object, separate from existing risk fields:

| Field | Definition |
| --- | --- |
| status | success or inference_error; optionally pending before completion, with no decision |
| model_version | v4.development.freeze.stage23.1 plus original artifact hash reference |
| feature_version | v4.features.1 |
| transaction_id / event_timestamp | Exact original reference (ID string for JSON safety) and canonical event time |
| prediction | integer0/1 on success; null on error |
| suspicious_probability | finite p(class1),0..1; null on error; never1-p |
| threshold | .50 with inclusive operator >= |
| decision | normal / suspicious_pattern on success; inference_error on failure |
| timestamp | Inference completion UTC, distinct from event time |
| inference_id / input_reference | Immutable idempotency key and authorized ledger snapshot/watermark/revision |
| history_status / unavailable_features | Verified complete observation scope; frozen baseline/no-path missing markers listed separately |
| error_code | Stable technical code on failure; sanitized details only |

No laundering/criminal identity labels. Normal means no benchmark pattern flagged by this model, not certified benign. Probability is uncalibrated synthetic suspicious-pattern support, not a probability of criminal conduct. Cold start is a coverage condition, not an error if history is truthfully complete. Do not serialize NaN into output JSON.

## 11. Alert integration and persistence design

Existing transactions store operational risk_score/risk_level, rule_score/rule_level, ai_risk_level/ai_confidence/ai_reason. Alerts store transaction/account, operational score/level, reason/rules and workflow fields; **no immutable model/feature version, threshold or consistently defined suspicious probability**. The alert payload sometimes contains probability which the alerts table does not persist separately.

Propose a separate immutable inference record keyed by transaction + model freeze + input revision, storing all contract fields, hashes, timestamp, status/error, history reference, and optional protected feature/input digest for traceability. Add an alert-to-inference reference or normalized evidence association; keep rule, behavioral and operational fields separate. These are schema designs only. Preserve failed attempts without overwriting successful historical records or recomputing old evidence on page view. Analyst labels/ratings/outcomes remain outside X and no automatic retraining is permitted.

In a later explicitly authorized controlled integration, a successful V4 positive creates/links one human-review alert regardless of legacy score damping; negative does not suppress independent rule alerts. Existing dedup check is select-before-insert, so concurrency needs a database uniqueness/idempotency gate. Alert source reasons must distinguish model and rules without rewriting model decision. A technical error produces a technical review/status record, not a suspicious AI alert; rule processing may continue under an explicit policy.

SAR/CTR: current code sets sar_required on model-positive or operational risk and creates CTR rows for deposit/withdraw >= configured CTR_THRESHOLD. Investigation can create SAR drafts and submit/update reports. V4 must not equate a positive with a filing duty or file a SAR automatically. Retain separate compliance review and reporting policy; this audit does not validate legal thresholds. A controlled nonproduction stage must isolate financial balances and regulatory outputs. Changes to operational alert routing/report behavior require their own approval and tests.

## 12. Socket.IO/dashboard compatibility

**`transaction_processed` and `alert_created` are not the current source event names.** Effective publishers and React consumers use `transaction`, `alert`, `alert_update`, `stats`, `balance`, `ctr_report`, `sar_report`, `reset`, `activity` and legacy `ai_model`. Renaming events would break clients. `realtime.RealtimeBroker` delivers Socket.IO/SSE and optionally Redis/Kafka; it currently broadcasts application events globally. Connection authentication does not provide per-transaction audience authorization. Customer-side filtering is not an access-control boundary.

Minimal future payload extension: append the versioned `v4_inference` object and inference reference to existing `transaction`/`alert` messages and corresponding GET responses. Preserve all old field meanings and event names. Do not overload `ai_confidence` with p(class1), because old normal confidence is1-p. No new alias events are required; aliases, if later wanted, need explicit versioning and dedup tests. Publish committed results using an outbox with event IDs and client deduplication/reconnect recovery. Filter both Socket.IO and SSE by authorized role/account before delivery; identical constraints apply across Redis instances.

React `static/react-dashboard.js` subscribes through useRealtime and updates transaction/alert lists. Some views display “AI Assessment” using ai_risk_level or fallback operational risk and show combined score. Admin views and `templates/alert_detail.html` show legacy confidence. Future UI must label V4 p(suspicious pattern), threshold, model/feature version, history status, and inference_error explicitly, beside separate rule/operational risk. Filters must distinguish model decision from operational level. Extra fields alone are tolerated structurally but do not make the display scientifically correct; rendering tests remain required.

`/compliance/alert/<id>` supports resolve/escalate/file_sar, case notes and risk-rating updates; `/compliance/sar/<id>/submit` submits the draft. Alert detail reconstructs missing suspicious-pattern explanations using **V1 Stage13 features**. It must become model-version-aware and never explain a V4 record using V1 formulas. V4 offers no validated per-case causal explanation here; display measured observables as context, not invented reasons for model output. Report pages refresh on SAR/CTR/alert events. No UI or event was changed.

## 13. Historical/cold-start behavior

New wallet with verified empty history: current participates once in recent subject aggregates; coverage0; baseline-dependent quantities use frozen markers. New agent: current service supplies applicable recent counts; coverage0; history-derived growth/newness/skew changes remain missing. No agent on valid direct W2W: agent recent counts/shares are the frozen zeros and baseline fields use their markers. Missing agent on cash is malformed raw data, not legitimate cold start.

No prior return path gives min length/log change/ratio -1 and path count0. Non-W2W directed counts/breadth are0 and accelerations -1. No N4 anchor gives ratio-1/residualNaN. Agent concentration/skew change use -3; valid signed differences (including -1 and cash change-2) must not be treated as missing. Numeric infinity or NaN outside the allowed raw residual field is an error. Embedded saved imputer converts only declared markers/allowed NaN and applies its **existing Train medians**; never fit on live observations.

Insufficient *known* baseline history is valid model input. Missing/unknown/incomplete ledger or network history is an inference error; absence of rows is not evidence of absence of activity. Do not fabricate synthetic warmup, fill arbitrary zeros, impute raw roles or label cold start suspicious. Predicted normal in a sparse history has explicit evidence limitations.

## 14. Failure and security design

| Failure | Future behavior |
| --- | --- |
| Wrong hash/path/version/runtime/load failure | Service unavailable; inference_error MODEL_INTEGRITY or MODEL_UNAVAILABLE; no fallback |
| Unknown fields, missing roles/currency, malformed time/ID/amount | Reject canonicalization; inference_error INVALID_EVENT; no guessing/clipping |
| Incomplete history, omitted graph edges, invalid ordering/duplicates | HISTORY_INCOMPLETE or HISTORY_ORDER; discard request state; do not silently sort an untrusted late-event stream |
|40-order/dtype/schema mismatch; unexpected NaN/Inf | FEATURE_SCHEMA or FEATURE_INVALID; only declared residual NaN/markers allowed before preprocessing |
| Preprocessing failure, nonfinite42-column transformed result | PREPROCESSING_ERROR; no fit/refit or substitute transform |
| Estimator exception/invalid probability | INFERENCE_ERROR; null prediction/probability, no success alert |
| DB write/commit failure | Roll back inference/alert/outbox transaction, discard speculative state; no event for uncommitted result |
| Delivery failure | Retain committed outbox, bounded idempotent redelivery; never duplicate alerts or alter prediction |

Use allowlisted raw fields and parametrized queries, authenticated endpoints, role/account-scoped output, immutable release paths and least-privilege runtime credentials. Do not put raw history, credentials or internal tracebacks in client errors. Legacy training/reset/metadata routes must be kept outside the V4 artifact/service boundary; model and feature assets read-only in deployment. No claim of independent challenge custody arises from such runtime isolation. Existing quarantines and Stage16V restrictions remain.

## 15. Integration test plan — later authorization, no fits

| # | Test and acceptance evidence |
| --- | --- |
|1| Hash/path mismatch rejected before deserialization; original path enforced even when an A40 refit has equal bytes. |
|2| Exact40 names/order/dtypes; reject41/44, swapped fields and unknown types; exact42 encoded order. |
|3| Frozen Stage17 hand fixtures replay exactly, including full-key endpoints, UTC days, roles, future invariance and graph paths. |
|4| Embedded preprocessor transform equals saved preprocessing reference on permitted fixtures; signed values and allowed NaN correct, no fit calls. |
|5| Separately authorized saved development examples reproduce original Stage18 probabilities with exact documented tolerances/runtime; no sealed data and no new evaluation claim. |
|6| Stub probability just below/exactly/above .50 produces0/1/1 without threshold search. |
|7| Normal controlled transaction persists independent model result and leaves rule alerts possible. |
|8| Positive controlled result creates exactly one review alert, immune to old operational damping. |
|9| True cold-start wallet receives correct frozen markers; unknown history errors instead. |
|10| Agent cash and receiver-/sender-assisted W2W record correct serviced roles; ambiguous historical records reject. |
|11| Direct W2W has empty agent/service, distinct endpoints, correct directed inclusion. |
|12| Multi-hop chronological paths, same-time IDs, unrelated endpoints and incomplete graph failure; no path cap changes outputs. |
|13| Failure before/at commit leaves no phantom event, balance inconsistency or committed speculative state; retry idempotent. |
|14| Existing transaction Socket.IO event supports appended contract and scoped recipients; SSE equivalent. |
|15| Alert event persists probability/version/threshold via reference, duplicate delivery safe, unauthorized users denied. |
|16| Admin/compliance/customer tables, filters and investigation render model vs operational result correctly; no V1 explanation on V4 records. |
|17| Missing/corrupt model and prediction exception remain inference_error, never normal/suspicious fallback. |
|18| Database/canonical schema mismatch, non-USD, amount cap, fractional cents and microsecond loss reject. |
|19| Restart/reload/replay produces same permitted fixture features and probabilities; rollback/correction invalidates state, concurrency preserves global key order. |
|20| Instrumented runtime proves no V1/V3/legacy predictor, fit/bootstrap/delete, generator/evaluator/private-field access. |

All integration tests use isolated databases and hand-authored nonproduction fixtures. Positive/negative stubs test routing without asserting fabricated real-model outcomes. Real-model parity tests require later explicit authorization. No tests in this plan ran now; only documentation/hash/static-source checks ran.

## 16. Required code/schema changes — design only

1. Canonical event ingestion with explicit agent/service roles, exact integer cents, supported type/currency/range, UTC microseconds and stable ID transport. Add prospective fields rather than backfill guesses; establish historical provenance/completeness.
2. Complete immutable history retrieval, first-observation/ordering state, graph closure and verified replay/checkpoint lifecycle. Review composite indexes and isolation.
3. Separate V4 loader/inference service with fixed hashes/runtime and no training hooks; preserve V1/V3 assets and original pipelines.
4. Immutable inference/error records, alert evidence linkage and idempotency; commit-aware outbox, rollback/restart guarantees and separate operational policy.
5. Audience-scoped transport plus additive payloads; model-aware dashboards/investigation explanations and human review.
6. Pinned runtime/dependency package hashes and isolated no-fit fixture/probability checks; explicit opt-in controlled deployment and rollback configuration.

No migration, service, route, frontend or application configuration was created or altered in this stage.

## 17. Blockers and unresolved risks

| Blocker | Evidence / required resolution |
| --- | --- |
| Semantic data mismatch | Cash can omit agent, channel always online in customer path, serviced wallet/flow absent. Obtain prospective canonical capture and trustworthy historical source. |
| Numeric/time/domain mismatch | Float amounts/unbounded request vs frozen1..1,500,000 cents, mixed timestamp DDL and no verified timezone/precision. No automatic wider-domain waiver. |
| History completeness | Retention, account participation, graph closure and deployed records unverified; no query limit can stand in for complete history. |
| Runtime mismatch | Python3.11 Docker and broad dependencies differ from freeze; no validated inference image. |
| Operational coupling | Blending/fallback confidence, legacy training/deletion hooks, early broadcasts and singleton DB reference. Needs explicit isolation/transaction design. |
| Evidence/UI mismatch | No immutable model metadata; V1 explanation reconstruction and global event delivery. |
| Scientific restrictions | Synthetic reused Validation, weak S2/S4, nine support deficits; no independent/real operator validation; no production approval. |
| Historical protection gap | Broader Stage15A archive snapshot still incomplete; named hashes do not repair it. |

Compatible frozen artifacts alone cannot make this source-backed data path ready. This audit does not claim all historical records are irrecoverable; it establishes that the application lacks the information and verified provenance needed to certify their conversion. Decision D applies to integration over the current unverified ledger. It is not a prohibition on later authorized preparation.

## 18. Recommended implementation stages

1. Approve the canonical raw-event and history-completeness contract; verify deployed schema/indexes and authoritative sample provenance read-only under an explicit data-access scope. Decide the supported prospective product events and treatment of incompatible old history.
2. Separately authorize schema/ingestion preparation in an isolated test environment, with no V4 activation. Verify exact money/time/roles and replay completeness before migration proposals reach production.
3. Separately authorize isolated frozen-loader/extractor implementation and hand-fixture/preprocessor/probability parity. No fit, no model substitution and no performance selection.
4. Separately authorize nonproduction transaction/alert/outbox/transport/UI integration with mock balances/regulatory effects, rollback and security tests.
5. Review evidence and limitations before any controlled use decision. Operational/production effectiveness and independent challenge custody/evaluation remain separate gates. No automatic implementation follows this report.

## 19. Preservation verification

**390 named protected paths** match before/after hashes. Scope includes344 inherited Stage23/historical references, the Stage23 decision, root application source/SQL, deployment files and static/template assets. Exact scope is in [before snapshot](../evidence/integration_stage1/before_sha256.json) and [preservation verification](../evidence/integration_stage1/preservation_verification.json). Development data/model bytes were hashed only through inherited explicit paths; no sealed tree was listed/read/hashed. No old artifact/manifest/report was rewritten.

New writes are this report and documentation evidence under `ml_v4/evidence/integration_stage1/`, including a standard-library audit-record builder. Source indexing parses Python without importing it. Feature feasibility copies the verified specification and adds static compatibility assessments; it does not construct a model feature matrix. The final [decision manifest](../evidence/integration_stage1/decision.json) binds new outputs. No application or database test was run, and no live-service health claim is made.

## 20. Final decision

**D — V4 INTEGRATION BLOCKED BY INCOMPATIBLE DATA OR ARTIFACTS**

The original Stage18 model and preprocessing are intact. Current application data lacks verified frozen V4 semantics and complete causal history; direct integration would require unsupported assumptions. The report supplies the exact reuse path,40-feature assessment, prospective schema/runtime design and later test gates. It authorizes no implementation or model promotion.

V4 INTEGRATION STAGE 1 COMPLETE —
WAITING FOR APPROVAL.
