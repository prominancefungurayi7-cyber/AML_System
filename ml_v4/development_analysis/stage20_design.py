"""Write Stage20 design documents only. No extraction, model or RNG interface."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'ml_v4/evidence/stage20'
REPORT = ROOT / 'ml_v4/reports/V4_STAGE20_FEATURE_DESIGN_REPORT.md'

def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))

def sha(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()

def write(name, value):
    p = OUT / name
    with p.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n')

def main():
    if OUT.exists() or REPORT.exists():
        raise FileExistsError('Stage20 outputs already exist; no overwrite')
    protected = read('ml_v4/evidence/stage19/preservation_before.json')['sha256']
    previous = read('ml_v4/evidence/stage19/stage19_decision.json')
    protected.update(previous['artifact_sha256'])
    protected['ml_v4/evidence/stage19/stage19_decision.json'] = sha('ml_v4/evidence/stage19/stage19_decision.json')
    for name, digest in protected.items():
        if sha(name) != digest:
            raise ValueError('Historical hash mismatch: ' + name)
    # Read the named public design/evidence text; never enumerate a dataset tree.
    documents = {}
    for name in protected:
        if name.startswith('ml_v4/') and name.endswith(('.json', '.md')):
            documents[name] = (ROOT/name).read_text(encoding='utf-8')
    parent = read('ml_v4/design/v4_feature_spec.json')
    targets = read('ml_v4/design/v4_target_predicates.json')
    assert parent['feature_count'] == 40 and len(targets['families']) == 12
    errors = read('ml_v4/evidence/stage19/false_negative_analysis.json')['validation']['families']
    metrics = read('ml_v4/evidence/stage19/model_results_verification.json')
    paired = read('ml_v4/evidence/stage19/xgboost_hgb_comparison.json')['paired_fixed_threshold_counts']['validation']['families']
    assert (errors['S2']['TP'], errors['S2']['support']) == (11,23)
    assert (errors['S4']['TP'], errors['S4']['support']) == (4,16)
    assert errors['S4']['exclusive_family']['support'] == 12
    assert errors['S4']['exclusive_family']['FN'] == 12
    assert (errors['A4']['TP'], errors['A4']['support']) == (151,222)
    assert metrics['partitions']['validation']['HGB']['families']['A4']['numerator'] == 197
    assert paired['A4']['HGB_detects_XGB_misses'] == 46
    OUT.mkdir()
    write('stage19_findings_verification.json', {
        'status':'PASS', 'method':'Verify saved artifact hashes and cross-check saved summary counts; no predictions or performance evaluation executed',
        'stage19_manifest_sha256':protected['ml_v4/evidence/stage19/stage19_decision.json'],
        'verified_findings':{'S2_XGB':[11,23], 'S4_XGB':[4,16], 'S4_exclusive_XGB':[0,12], 'A4_XGB':[151,222], 'A4_HGB':[197,222], 'A4_HGB_rescues':46},
        'read_public_document_count':len(documents), 'selected_unchanged':'primary_XGB', 'comparator':'primary_HGB',
        'external_independent_review':False})
    common = {
        'domain':'structuring', 'category':'B: disclosed individual target component',
        'wallet_role':'Current sender for W2W; serviced_wallet for Cash-In/Cash-Out. Subject activity is sent W2W and cash of that wallet, once per event. Incoming W2W only establishes observation age, not activity.',
        'inputs':['transaction_id','event_timestamp','sender_wallet','receiver_wallet','amount_minor','transaction_type','serviced_wallet'],
        'ordering':'UTC integer microseconds then unique integer transaction_id. Only smaller keys are prior. Emit before update.',
        'dtype':'float64 after exact integer aggregation; no new categorical field',
        'numeric':'Integer cents and integer count arithmetic; reject aggregate outside exact float64 integer range 0..2^53-1 rather than silently round. No new amount rounding, tolerance, scaling or clipping.',
        'leakage_controls':'Observable stream only; no labels, evaluator imports, witness caches, origin, private activation, predictions or future events.',
        'shortcut_risk':'Direct rule-component alignment can make synthetic targets easier; no claim of operational AML value. Inspect matched target-0 support and missingness later.',
        'deployment':'Needs complete rolling 35d subject history plus first prior observation; no schema inference from ambiguous production records. No deployment approved.'}
    proposals = [
        ('wallet_similar_amount_value_minor_7d','S2','sum(amount_minor(e) for e in C_R)', 'R=(t-7d,t] restricted to prior keys, plus current once', 'No baseline gate; valid at first activity', 'Never missing for a valid event; current ensures a positive sum', 'cents',
         'Count/share/current amount do not determine exact sum within the inclusive 5% tolerance.',
         'O(n_R) scan per subject query; O(n_35d) retained state. Optional amount index needs separate correctness review.',
         'Current 5000 and three prior similar amounts 4999,5000,5000 give 19999; changing 4999 to 5000 gives 20000 without changing cluster count/share. Place prior rows more than24h before current within7d, outside current UTC day; direct outgoing edges to fresh sinks, no agent/return paths/incoming anchor. Other counts/times and baseline fixed: all original40 fields unchanged.'),
        ('wallet_baseline_similar_amount_count_28d_offset_7d','S2','n(C_B)', 'B=(t-35d,t-7d] restricted to prior keys; current excluded', 'First prior participation <=t-35d AND n(B subject activity)>=4', '-1 if age or activity support fails; otherwise integer >=0 (zero valid)', 'events',
         'Existing cluster count/share are recent; baseline activity-count summaries and coverage do not reveal current-centered baseline amounts.',
         'O(n_B) current-centered range scan; O(n_35d) state. Query center must be recomputed for every current amount.',
         'Keep baseline keys, counts and endpoints fixed at times around t-20d; change an outgoing amount from1000 to5000 for current5000. Counts/coverage and all recent fields stay fixed, no agent or return graph. Baseline similar count changes0 to1; existing40 cannot distinguish. Use >=4 total baseline events and fixed first observation <=t-35d.'),
        ('wallet_near_band_distinct_amount_count_7d','S4','cardinality({amount_minor(e): e in R AND 700000<=amount_minor(e)<=1050000})', 'R=(t-7d,t] restricted to prior keys, plus current once', 'No baseline or current-band gate; defined for every valid subject activity', 'Never missing; zero if no band rows; one means repeated identical band value', 'distinct cent values',
         'Band count and similar-cluster count/share do not determine whether band values differ by a cent.',
         'O(n_R) scan with O(d_band) distinct-value set; rolling frequencies may update per event with exact expiry.',
         'Current850000, prior band rows850000,850000,850000 and one nonband100: change one old850000 to850001 outside24h/current day but within7d. Band count and similar count/share remain4 and4/5; distinct band values change1 to2. Direct fresh sink endpoints, no agent, anchor or return route; baseline unchanged. All original40 fields equal.'),
        ('wallet_baseline_near_band_count_28d_offset_7d','S4','n({e in B:700000<=amount_minor(e)<=1050000})', 'B=(t-35d,t-7d] restricted to prior keys; current excluded', 'First prior participation <=t-35d AND n(B subject activity)>=4', '-1 if age or activity support fails; otherwise integer >=0 (zero valid)', 'events',
         'No existing field measures baseline band membership; fixed baseline counts can hide arbitrary band composition.',
         'O(n_B) scan or O(1) maintained band count after expiry/migration; O(n_35d) state.',
         'At fixed baseline keys around t-20d change outgoing1000 to800000, maintaining counts/endpoints/first observation and no agents or return routes. Existing40 fields stay fixed; baseline band count changes0 to1. Amounts remain valid positive cents.')]
    features=[]
    for i,(name,family,formula,window,eligibility,missing,unit,nonduplicate,cost,witness) in enumerate(proposals,41):
        f=dict(common,index=i,rank=i-40,name=name,family=family,formula=formula,window=window,eligibility=eligibility,missing_marker=missing,unit=unit,nonredundancy=nonduplicate,complexity=cost,symbolic_information_witness=witness)
        f['fixture_requirements']=['Assert independent hand-computed output, not agreement with evaluator','Full original40 equality for the stated paired-history witness; no feature implementation or event ledger constructed in this stage','Lower/upper endpoints, same-time smaller/larger IDs, current once, incoming-vs-outgoing role','Mutate private metadata and future rows: unchanged earlier outputs','Cold start and exact35d/four-event boundary where applicable','Both passing and failing individual target components; never query full target during extraction']
        features.append(f)
    contract={
        'status':'PROPOSED_DESIGN_ONLY_NOT_IMPLEMENTED', 'feature_version':'v4.features.2.proposed.stage20.1',
        'design_version':'v4.stage20.feature_design.1','parent_feature_version':parent['feature_version'],
        'parent_feature_sha256':sha('ml_v4/design/v4_feature_spec.json'),
        'target_sha256':sha('ml_v4/design/v4_target_predicates.json'),
        'semantic_fields':44,'numeric_estimator_columns':46,'missing_indicators':0,
        'existing_field_order':[f['name'] for f in parent['features']], 'inheritance':'First40 fields byte-semantically unchanged, append41..44 only; no replacement of frozen artifacts',
        'cluster_definition':'C_W={e in subject activity W:20*abs(amount_minor(e)-amount_minor(T))<=amount_minor(T)}; exact integer inclusive test with current amount as center, no fitted bins',
        'historical_gate':'Compute raw first-observation timestamp and n(B) privately inside extractor from permitted history; same S2/S4 historical gate. Do not call evaluator or emit an eligibility boolean.',
        'support_policy':'Baseline support is >=4 ALL subject activities, not >=4 similar or band events. Zero qualifying baseline events with four other baseline activities is observed zero, not missing.',
        'features':features,
        'retained_option':'Retain original40 with selected XGB and comparator HGB unchanged; zero extraction/refits; known sparse-family limitations persist.',
        'minimality':'Four interpretable quantities cover four independent priority information gaps; not a theorem of globally minimal dimensionality. Packed scalars, conjunctions and triggered flags are excluded. No extra rate, ratio, support flag, total-count or band-share columns.'}
    write('minimal_feature_contract.json',contract)
    audit=read('ml_v4/evidence/stage19/feature_representation_limitations.json')
    audit['stage20_review']={
        'S1':'Do not add distinct-count for binary variation: exact aggregates n*max_share>1 express variation; test numeric sensitivity, no new column.',
        'S4':'n_R=similar_count/similar_share (current ensures positive denominator); band share=band_count/n_R. Algebraic recoverability is not a promise a tree learns division.',
        'S2_rates':'n(C_B)/4 and recent_count/max(1,n(C_B)/4) recoverable once baseline count exists; do not add either separately.',
        'S4_rates':'baseline band count/4 and band-growth ratio recoverable once count exists; no separate transform.',
        'support':'Exact baseline activity count beyond the >=4 gate deferred. Two baseline missing markers already communicate historical availability, consistent with existing marker policy; no standalone eligibility flag.',
        'precision':'Algebra at exact aggregates may suffer float rounding; future fixtures required. No saved column was reconstructed.'}
    write('existing_feature_information_audit.json',audit)
    write('s2_s4_representation_proposal.json',{'contract':'minimal_feature_contract.json','rationale':'Prioritize failures11/23 S2 and0/12 exclusive S4; four missing quantities, no recent total-count/share duplication', 'proposals':[f['name'] for f in features], 'no_guarantee':'Sparse dependent labels and model approximation remain; new components may not improve observed or independent metrics.', 'support_rejected':'Separate total baseline support field is not necessary to implement the historical gate; raw count for richer context is deferred, not silently encoded.'})
    secondary={
        'N1':{'decision':'DEFER, first secondary priority','quantity':'sum minor incoming W2W to current receiver in R24h including current once;0 non-W2W; no baseline gate; exact integer ->float64','reason':'Genuine missing aggregate,24 Validation misses and HGB rescues8; do not bundle a second hypothesis into S2/S4 test.'},
        'N2':{'decision':'DEFER','quantity':'sum minor outgoing W2W from current sender in R24h including current;0 non-W2W; no baseline gate','reason':'Genuine omission but429 positives and stronger observed recall; symmetry alone is not a reason to add now.'},
        'A2':{'decision':'DEFER, first secondary priority','quantity':'all current-agent services in R24h including current once;0 absent agent; no baseline gate','reason':'Absolute count missing; HGB advantage also shows approximation. No top2 conjunction/trigger.'},
        'N3':{'decision':'DEFER; reject qualifying-path count/existence and current-ratio-selected route','quantity':'Potential future topology-only deterministic second route or prior-only monetary quantiles over all topology-valid paths','reason':'7/130 positives have incompatible selected summary,4 missed. Arbitrary second route still lossy; path-order, bounded enumeration, dimensionality and costs need separate design. Marginal extrema can combine different paths and must not be called a witness.'},
        'S3':{'decision':'DEFER','quantity':'current subject calendar-day value including current, UTC[d,t], strict keys','reason':'Not recoverable from1h total, but546 Validation positives. Calendar boundary fixtures needed; no new day amount now.'},
        'N4':{'decision':'DEFER','quantity':'prior anchored funding F in24h, current excluded; missing if no anchor/current not outward','reason':'F=(a-r)/(q-1) only for q!=1; q=1 degeneracy and near1 numerical conditioning remain. Existing residual can be negative; never use negative as generic missing.'},
        'A3':{'decision':'DEFER','quantity':'current-agent service count R1h including current;0 no agent','reason':'Acceleration equals count under floor but not generally;255/255 Validation detection is not proof of sufficiency. No immediate addition justified.'},
        'A4':{'decision':'RETAIN primitives; REJECT full flag and redundant skews','reason':'Six primitives/history marker/type supply arithmetic; HGB197/222 vsXGB151/222 with46 rescues. Cause of model difference unproven.'}}
    write('secondary_domain_review.json',secondary)
    write('a4_model_approximation_assessment.json',{'decision':'No A4 additions or model replacement','XGB':[151,222],'HGB':[197,222],'paired_rescues':46,'explanation':'Same representation supports different fitted approximations; sparse support/concentration persists. No hyperparameter cause demonstrated. Counts, values, breadth, history change, missingness and type suffice in principle.','selected':'primary_XGB','comparator':'primary_HGB'})
    write('redundancy_leakage_analysis.json',{'proof_status':'Symbolic paired histories and aggregate identities, not executed extraction fixtures or empirical gain evidence','four_witnesses':{f['name']:f['symbolic_information_witness'] for f in features},'all40_witness_controls':'Use identical timestamp/ID/endpoint skeletons; all changed rows outside24h and current day; direct W2W to distinct sink wallets with no return edges, no incoming funding and no agents; fixed first observation and baseline counts. Current receiver is a fresh sink. Incoming network descriptors/agent missing markers/path summaries stay fixed. Amount-only changes leave baseline count medians unchanged. Exact wallet coverage identical.','joint_information':'With44 fields S2/S4 become expressible from individual quantities and markers. This is intentionally stronger rule alignment, disclosed B components, not proof of criminal intent. No scalar combines every gate.','prohibited':['full S2/S4/A4 flags','label-conditioned missingness','target-qualified path counts','private activation/provenance','future-derived center','packed compound rule code'],'future_audits':['static import/interface separation','independent hand fixtures','metadata and identity invariance','target0 conditional overlap and origin associations as diagnostics only','missingness and amount precision associations','no shortcut removal solely to flatten importance']})
    temporal={
        'canonical':'UTC microsecond full-key prior; R=(t-7d,t] plus current once; B=(t-35d,t-7d] prior only; windows disjoint',
        'boundary_requirements':['At t-35d observation establishes age but event excluded from B count','At t-7d event enters B not R','Same-time lower ID prior, higher ID future; output before insertion','Current5000:4750/5250 included;4749/5251 excluded by20*abs integer test','Band700000/1050000 inclusive;699999/1050001 outside','Distinct band repeated values count once, zero band gives0','Age35d with3 baseline activities =>-1; age35d with4 nonmatching activities =>0 for both baseline features','Recent sum/distinct defined even with insufficient history; no current-band gate for either S4 field','Incoming W2W establishes age but cannot satisfy four baseline subject activities','Cash bothdirections count once; receiver-assisted W2W does not change structuring subject from sender','Future insertion, private-metadata mutation, bijective renaming preserve outputs with full-key ordering','Exact aggregate and overflow fixture; no sentinel confusion; reproduce first40 columns identically'],
        'hand_examples':{'recent_similar_sum_cents':[19999,20000], 'eligible_baseline_zero':0,'ineligible_baseline':-1,'band_values':['850000 repeated ->1','850000 and850001 ->2']},
        'execution_status':'NOT_RUN: requirements and paper arithmetic only; no synthetic ledger, RNG, extractor or matrix created',
        'deployment':'Keep first observed participation scalar after35d eviction. Out-of-order current rows rejected or handled by a separately versioned replay policy; never silently use future state. Retained warmup is42d, availability still observed per row.'}
    write('temporal_correctness_requirements.json',temporal)
    compatibility={
        'Train_Validation_ledgers':'Semantically sufficient observable fields/history already retained; no new transactions needed. Future separately authorized extraction reads each partition in isolation. No ledger byte examined beyond hashing in this stage.',
        'warmup':'Unchanged42d warmup; maximum35d history; no fabricated observations/activation. Later cold start remains missing.',
        'Stage17':'Immutable40 columns. Future44 matrix in new namespace, verify first40 values/order/IDs/labels against Stage17 exactly; no replacement.',
        'Stage18':'Old fitted42-numeric preprocessing/models incompatible with46-numeric inputs. New unfitted preprocessing specification may inherit marker conversion, Train median(empty0), scaling and fixed3type onehot; must be fitted Train only under separate authorization. Never pad old models or reuse fitted medians as if44 compatible.',
        'Stage16T':'NOT_COMPATIBLE_BY_DEFAULT: explicit feature-dimension/version, extractor/hash, preprocessing, permutation-field count and freeze/amendment required. No automatic edit.',
        'original_sealed':'SEALED_QUARANTINED, supportFAIL unchanged. No compatibility claim, access, recount, reinterpretation, regeneration or amendment to original certificates.',
        'realtime':'Requires explicit serviced_wallet/roles, complete causal history, integercents and exactkey order; additional range scans and distinct state benchmark later. Existing application adapter not approved; no Flask/API changes.',
        'versions':'New feature v4.features.2.proposed.stage20.1; proposed comparison v4.feature_comparison.1. Preserve target v4.predicates.1 and data version/hash. Feature experiment separate, no new dataset required.',
        'custody':'Stage16V C remains; independent admin/storage/secret/registry/log/developer-denial verification remains mandatory.'}
    write('version_compatibility_assessment.json',compatibility)
    challenge={'status':'REQUIRES_SEPARATELY_APPROVED_VERSIONED_AMENDMENT_NOT_APPLIED','affected_clauses':['Stage16T section6 frozen40 semantics','section8 per-field permutation40 becomes44; type remains one joint field','section10 extractor/preprocessor/feature/model freeze and compatibility hashes','section12 stage order and model-plan approvals','challenge_reproducibility_spec.json and dependent feature/hash references','challenge_metrics_policy.json field count and challenge_stage_plan.json approval dependencies'], 'preserved':['12targets','population/opportunity laws and one-draw rule','support/precision objectives','all metrics and threshold policy','independent custody','public-only certificates before freeze','one frozen primary model not algorithm leaderboard','original quarantine'], 'required_approvals':['Approve feature design separately','Approve challenge protocol amendment/version binding44 fields before affected generation/evaluation; no silent inheritance','Authorize/test implementation and development extraction separately','Authorize fit budget and preregister comparison separately','Verify independent custody and separately authorize generation and later frozen evaluation'], 'timing':'No challenge exists; resolve compatibility before any affected challenge generation. Do not substitute development44 artifacts into protocol1 silently.', 'no_generation_now':True}
    write('stage16t_compatibility_requirements.json',challenge)
    training=read('ml_v4/evidence/stage18/frozen_training_plan.json')
    comparison={
        'status':'DRAFT_FOR_SEPARATE_AUTHORIZATION_NO_EXECUTION','version':'v4.feature_comparison.1.proposed',
        'arms':{'A':'Original40 semantic fields,42 numeric','B':'Same40 plusfour proposed fields,46 numeric'},
        'planned_new_fits':4,'grid':['A_XGB','B_XGB','A_HGB','B_HGB'],
        'configurations':{k:training['comparative'][k] for k in ['XGB','HGB']},
        'configuration_rule':'Copy exact Stage18 dictionaries, seed2026092915, effective defaults and pinned versions; no tuning, repeats, early stopping, resampling, weighting, calibration, threshold search or added algorithms. Fit baseline A anew for controlled parity; saved models retained for reproducibility checks only.',
        'versions':training['versions'],'preprocessing':training['preprocessing'],
        'extension':'For new baselinecount fields only convert-1 toNaN; recent fields never missing; keep all original signed-marker rules.43 numeric continuous fields plus3fixed type columns=46. No new missing indicators.',
        'rows':'Exact same60000Train and15000Validation IDs/labels; train-only fit of transforms and estimators; no Train+Validation refit; no new rows.',
        'threshold':0.5,'primary_estimands':['B-minus-A fixed-threshold S2/S4 recall within each algorithm, including exclusive-family rows','B-minus-A unionFPR and all-family/domain recall tradeoffs'],
        'secondary':['confusion,precision,recall,macroF1,balancedaccuracy,ROC-AUC,AP','paired detections/losses, per-unit/subject/episode counts','all12 families,3domains,exclusive/overlap and H1-H8 target0FPR','Train/Validation availability and exact support denominators'],
        'comparison_policy':'No new winner selected by this comparison; XGB selection stays historical. Report direction and raw counts without invented improvement certification. Numerical promotion/independent behavioural gates require a later plan, not inferred from inspected results.',
        'diagnostics_no_extra_fits':['Static leakage audit and temporal/metadatainvariance fixtures before extraction','Exact first40 equality, alignment and byte replay','Same Stage18 fixed3000Validation sample and3semantic permutations, paired AP baseline permodel; addfour fields but no fit. Describe correlated/off-manifold limits and sparsefamily sample counts.','Conditional target0 distributions, marker/origin/type associations with provenance diagnostic only','Retain old robustness results as historical; they do not validate new44 schema'],
        'uncertainty':'Reused Validation is exploratory. Raw paired counts and per-community differences primary; three communities inadequate for reliable broad cluster inference. Wilson if shown labeled independence-based descriptive. No row bootstrap/significance or independent-validation claim.',
        'failure_policy':'Each attempted fit including failed starts consumes a slot. Stop on technical failure; no automatic replacements, adaptive configurations or budget extension. Freeze ledger/source/config/matrix hashes before first fit.',
        'nine_shortfalls':['S1','S2','S4','N1','N3','N4','A2','A3','A4'],
        'support':'Feature changes cannot create support or independence. All nine shortfalls persist; no oversampling/relabeling/accept-until-support. No family dropped. Original holdouts remain unusable under support policy.',
        'evaluation':'Independent challenge only after custody, support, protocol compatibility and frozen single-model approval; development comparison is not a challenge leaderboard.'}
    write('future_experimental_comparison_plan.json',comparison)
    budget={'historical_started_completed':16,'expired_slots':20,'currently_authorized_new_fits':0,'proposed_new_fit_ceiling':4,'proposed_cumulative_attempt_ceiling':20,'required':'Explicit new authorization naming four prospective slots and resolving the Stage18 expiry while retaining the inherited36 ceiling; amend policy prospectively, never describe expired slots as available or reset the ledger. If refused, no fits.', 'accounting':'Keep Stage18 ledger unchanged. New linked ledger records all attempts including failures; remaining ceiling is not permission. Four slots include two fresh40 baselines and two44 candidates; no automatic diagnostic/repeat slots.', 'validation_reuse':'Stage19 errors motivated design and Stage20 choices. Validation reused for hypothesis generation; future metrics exploratory. No thresholdsearch, seedshopping or p-value promotion. Retire challenge independence if its results guide later work.'}
    write('fit_budget_validation_reuse_policy.json',budget)
    risks=['No empirical gain measured or guaranteed','Sparse S2/S4 subjects/clusters and nine family shortfalls unchanged','Stronger direct-component access may mostly improve deterministic rule reproduction','Missing-marker history disclosure is intentional but needs future shortcut audit','Pair-history nonredundancy arguments are mathematical constructions; all40 equality requires future independent implementation fixtures','No new exact historicalsupportcount offered beyond eligibility; richer context deferred','Runtime/overflow and incremental-state correctness unmeasured','Future44 pipeline incompatible with old fitted objects','Stage16T amendment and independent custody unavailable','Original quarantined evaluation remains supportFAIL','Incomplete Stage15A broad historical snapshot retained; named hashes are not full historical restoration','Repeated Validation reuse prevents independent performance inference']
    write('risks_unresolved_limitations.json',{'risks':risks,'not_claimed':['measured improvement','full-family adequacy','independent model validation','real-world AML effectiveness','production readiness']})
    write('recommended_next_step.json',{'recommendation':'Review/approve this design and explicit Stage16T compatibility amendment; then separately authorize feature implementation with hand fixtures and development-only extraction. Modeling requires another explicit fit authorization.', 'design_authorizes_execution':False,'retain40_option':'Scientifically valid if amendment cost/shortcut risk outweighs uncertain benefit; preserve restricted claims and original candidate selection.', 'automatic_progression':False})
    # Report is assembled from declarative design records; no executable feature formula.
    sections=[]
    sections.append('''# MODEL V4 — STAGE 20 CONTROLLED FEATURE-REPRESENTATION DESIGN AND COMPATIBILITY REVIEW

**A — MINIMAL FEATURE AMENDMENT DESIGN READY**

Propose **four additional observable quantities**, retaining the original forty fields unchanged: **44 semantic fields / 46 numeric estimator columns**, under `v4.features.2.proposed.stage20.1`. This is a design proposal, not an implemented or approved replacement schema. No extraction, transaction generation, model execution, fitting or threshold work occurred. XGBoost remains selected; HGB remains the comparator.

## 1. Authority and verified findings

Stage15 and15A retain authority for targets, schema and temporal rules;16R retains the one production draw;16S retains support failures;16T retains challenge governance;16U/V retain custody restrictions;17/18 retain matrices, models and fit ledger. Stage19's manifest and quantitative summaries were verified against named hashes, not rerun as model evaluation. All twelve predicates remain unchanged.

The saved findings motivating this design are S2 XGB11/23, S4 XGB4/16 and **S4-only0/12**, and A4 XGB151/222 versus HGB197/222 with46 HGB rescues. These are reused synthetic Validation observations, not independent evidence or proof of error causes. Details: [findings verification](../evidence/stage20/stage19_findings_verification.json).

## 2. Why four additions

Two S2 gaps are exact recent similar-cluster value and prior similar-cluster frequency. Two S4 gaps are recent band-amount variation and prior band frequency. All are functions of permitted observations before or at the current decision, without learned centers or private context. Counts retain more detail than boolean gates. None combines a complete predicate.

The smallest defensible proposal for these four separate information gaps uses one interpretable scalar per gap. This is not a proof of globally minimal dimension. Encoding several conditions into one scalar or packing a rule code would defeat the component policy. No separate baseline rate, growth ratio, eligibility flag, recent total-count or band-share field is proposed.

The option to **retain all40 unchanged** remains justified: zero re-extraction/refit cost, preserved compatibility and no uncertain increase in rule alignment. Its known family weaknesses and support limits must remain explicit. Design A favors a bounded information study, not a promised performance improvement.

## 3. Exact common temporal and numerical contract

For current T at UTC integer-microsecond time t, keys order by(timestamp, integer transaction_id). Prior means strictly smaller key; same-time smaller IDs count, larger IDs do not. Emit before updating state. Subject is current W2W sender, or serviced wallet for cash. Subject activity includes outgoing W2W and both cash directions once; incoming W2W establishes observation age but is not activity.

R contains prior subject activity with t−7d<time<=t, plus current once. B contains prior activity with t−35d<time<=t−7d; no current and no overlap with R. C_W contains rows satisfying `20*abs(amount(e)-amount(T))<=amount(T)`, an inclusive integer test. S4 band is inclusive700000..1050000 cents, unchanged and explicitly synthetic.

Historical eligibility for both baseline counts is actual first prior participation<=t−35d AND at least4 subject activities in B. Compute independently from observables, not rounded coverage or a target evaluator. Four similar/band rows are **not** required. Exact lower-bound observation establishes age but does not enter the open-lower count. Eligible zero qualifying events emits0; insufficient age/support emits−1. There is no recent trigger or current-band gate for the baseline fields.

Amounts remain positive integer cents. Sum/count/distinct aggregation uses exact integers; output float64 only within exact integer range0..2^53−1. Exceeding it is an explicit error, not clipping or silent rounding. Baseline−1 is the only new missing marker. Recent fields are defined at cold start. No future imputation or private activation substitutes for missing history.

## 4. Proposed append-only feature contract
''')
    for f in features:
        sections.append(f"### {f['index']}. `{f['name']}`\n\n- **Formula:** `{f['formula']}`.\n- **Window:** {f['window']}.\n- **Eligibility:** {f['eligibility']}.\n- **Missingness:** {f['missing_marker']}.\n- **Unit/dtype:** {f['unit']}; float64 after exact integer aggregation.\n- **Relationship:** {f['category']}, {f['family']}; structuring domain.\n- **Existing equivalent:** {f['nonredundancy']}\n- **Cost:** {f['complexity']}\n- **Symbolic nonredundancy witness:** {f['symbolic_information_witness']}\n")
    sections.append('''These are paper histories illustrating non-identifiability, not generated records, empirical support or executed extractor tests. Keep unchanged timestamp/ID/endpoint skeletons, no agent/incoming anchor/return topology, fresh current receiver and all modified recent amounts outside24h/current day. Baseline count medians, coverage, recent counts, role markers and topology remain unchanged. Future independently hand-authored fixtures must assert equality of **all forty** original outputs as well as the stated difference. No scalar full-rule flag is introduced; jointly informative primitives are deliberately disclosed.

All four fields use the common wallet role, observable inputs, precision and key semantics above. Baseline similar membership is recomputed around each current amount, never a stored episode center. Distinct means distinct **cent values**, not a rounded USD band or learned bin. S4 recent distinct remains defined when current itself is outside the band.

Full machine-readable definitions, original field order, inputs, risks and per-field fixture requirements: [minimal contract](../evidence/stage20/minimal_feature_contract.json).

## 5. Redundancy and support decisions

S2 count/share/current amount cannot determine exact cluster value within5% tolerance. Once baseline similar count is provided, its weekly rate is count/4 and the existing recent count supplies growth through the declared floor; adding both would duplicate information. S4 baseline count similarly supplies its weekly rate.

S4 recent total count is recoverable as S2 similar_count/similar_share because current always belongs to its own cluster; band share follows. Division may be difficult for a learner, but this stage prioritizes missing information over duplicate convenience transforms. S1 binary variation is recoverable from n*max_share>1 under exact aggregates, so a distinct-count field is not needed for that gate. Float boundary sensitivity must be tested later.

Both new baseline fields'−1 markers disclose the identical35d/four-activity availability condition. This is deliberate existing-style marker semantics, not a separate predicate-specific eligibility input. Exact total baseline activity count beyond the gate is deferred: it could add context but is unnecessary for those frozen support checks. Four nonmatching baseline activities must yield valid0, not missing. First observation from incoming W2W alone does not supply four activities.

With the proposed44 fields, S2/S4 rules can be expressed jointly through lower-level components and markers. That increased alignment is intentional and must not be presented as independent criminal-intent detection. Individual components are categoryB; complete conjunctions, label-conditioned values and packed rule codes remain prohibited.

## 6. Secondary domains and A4

| Family | Missing/conditional information | Decision and reason |
| --- | --- | --- |
| N1 | Incoming24h aggregate value | Defer, first secondary priority. Genuine gap;24 XGB misses, but isolate S2/S4 hypothesis first. |
| N2 | Outgoing24h aggregate value | Defer. Genuine gap; symmetry alone does not justify another field. |
| N3 | Alternative-path monetary evidence | Defer a separate route-summary design.7/130 positives have incompatible selected summaries,4 missed; no proof all4 errors caused by it. |
| A2 | Absolute24h agent service count | Defer, first secondary priority. Both missing count and HGB model difference matter. |
| S3 | UTC current-day aggregate value | Defer.1h value cannot generally recover it; preserve calendar semantics. |
| N4 | Anchored funding F | Defer. F=(a−r)/(q−1) when q!=1; at q=1 it is unidentified, and near1 is ill-conditioned. |
| A3 | Absolute1h agent service count | Defer. Acceleration only equals count under the floor; observed perfect recall is not universal sufficiency. |
| A4 | Existing primitives suffice in principle | Retain unchanged. Reject full flag and redundant derived skew additions. |

N3 options such as a topology-determined second route or prior-only spread quantiles remain lossy and need an independent order/complexity design. Do not pick a route by current return ratio, count qualifying paths or emit existence of a fully qualifying path. Combining extrema from different routes is not a valid path witness. Existing exhaustive-search performance obligations remain.

A4's same-field HGB advantage demonstrates model/configuration dependence, not a specific parameter cause. It does not authorize model replacement or tuning. XGB remains selected, HGB comparator. See [secondary review](../evidence/stage20/secondary_domain_review.json) and [A4 assessment](../evidence/stage20/a4_model_approximation_assessment.json).

## 7. Independent fixture and leakage requirements

No feature implementation or synthetic test ledger was constructed. Future hand fixtures must independently check exact outputs; evaluator/extractor agreement alone is insufficient. Required cases include35d equality,3versus4 baseline activities, t−7d ownership, same-time IDs, current once, cash/assisted roles, incoming observation versus activity, and future/private-metadata invariance.

Paper amount checks include current5000 with4750/5250 inside and4749/5251 outside; band endpoints700000/1050000 inside, adjacent cents outside; sums19999versus20000; distinct repeated850000 versus850000/850001. Test zero qualifying baseline with sufficient total support separately from−1. Replay must preserve first40 fields exactly, all IDs/labels and partition isolation. Overflow/error paths must be explicit. Full fixture requirements: [temporal correctness](../evidence/stage20/temporal_correctness_requirements.json).

Static boundaries must reject evaluator/witness access, provenance and future state. Subsequent audits should compare target0 overlap, missingness, amounts/cents, roles and origins diagnostically. No sampling or feature rejection based solely on an importance concentration target. No new labels or family-derived input is allowed.

## 8. Compatibility and inference impact

| Artifact/interface | Assessment |
| --- | --- |
| Existing Train/Validation ledgers | Contain required observables; no new dataset needed. Extraction still requires separate authorization. |
|42d warmup/35d history | Unchanged; eligibility from actual observations. No manufactured history. |
| Stage17 matrices | Preserve40-field bytes; a future44 matrix uses separate namespace and exact first40 parity check. |
| Stage18 pipelines/models |42-column fitted objects cannot consume46 columns. A new Train-fitted preprocessor/model version is required; no padding or silent replacement. |
| Proposed preprocessing | Inherit exact marker conversion/Train median(empty0)/scaling/typeonehot; add−1 conversion for two baseline fields only; no indicators. |
| Stage16T protocol1 | Not automatically compatible; explicit amendment and fresh approvals required. |
| Original sealed evaluations | Remain SEALED_QUARANTINED/supportFAIL; no access or revised compatibility claim. |
| Real-time processing | Requires complete keyed history, explicit roles and integercents; extra current-centered scans/distinct state need later performance tests. No application adapter approved. |

Four noncategorical additions yield43numeric quantities plus3type one-hot columns=46. Incremental algorithms may optimize scanning only after exact fixture/replay equivalence. Worst-case subject scans remain O(n35d) per query and memory O(n35d); no timing or throughput guarantee. Keep first observation after expiry and reject out-of-order input unless a separate replay policy is approved.

The proposed feature-comparison experiment has a new identifier without changing the dataset or target version. All original rows, labels, predicates and model artifacts remain authoritative in their own versions. Full details: [compatibility](../evidence/stage20/version_compatibility_assessment.json).

## 9. Stage16T amendment requirements

No challenge protocol was amended. A separately approved version must explicitly replace the40-field references in sections6/8/10/12 and dependent feature/hash, metrics/permutation and stage-plan records; bind44-field extractor/preprocessor versions and all freeze hashes. Per-semantic-field permutation would cover44 fields with type still jointly permuted. Retain all support/precision criteria, population rules, one-draw policy, public-only certificates and independently administered custody.

Resolve this compatibility before any affected generation/evaluation. No challenge exists now. Stage16V's custody-unavailable decision persists. Original holdout FAIL certificates are not repaired. Future independent evaluation remains one frozen primary model with only predeclared diagnostics, not the proposed development algorithm comparison. [Required approvals](../evidence/stage20/stage16t_compatibility_requirements.json).

## 10. Proposed controlled comparison — not authorized or executed

Propose four new fits: A40-XGB, B44-XGB, A40-HGB, B44-HGB. Both arms use exactly the same frozen60000Train/15000Validation rows/labels. Copy the complete Stage18 XGB/HGB dictionaries and pinned dependencies into the new preregistration; these exact dictionaries are embedded in [comparison plan](../evidence/stage20/future_experimental_comparison_plan.json). XGB:200trees, depth5, learning rate.07, minchild5; HGB:200iterations,31leaves, learning rate.07, minimumleaf20. Both retain seed2026092915, no early stopping or new weighting/resampling. Refit A as well as B for controlled parity; retain saved originals.

Fit every learned transform on Train only, with separate fitted objects per arm. Threshold stays0.50 inclusive; no Validation threshold search/calibration. Primary contrasts are B−A S2/S4 recall, including exclusive rows, alongside unionFPR and all-family/domain tradeoffs within each algorithm. Report AP/ROC, confusion, precision/recall/MacroF1 and all slices with numerator/denominator and undefined conventions unchanged. No candidate substitution or improvement certification is implied by the comparison.

Use paired detection/loss counts and per-community summaries. This Validation set generated the design hypotheses; subsequent results are exploratory. Three communities cannot support confident population inference; no row bootstrap or post-hoc significance claim. Existing support deficits remain S1/S2/S4/N1/N3/N4/A2/A3/A4. Retain all families, exact support/diversity denominators and limitations. Additional features do not create positives, independent subjects or valid holdouts.

Leakage fixtures, first40 parity and deterministic replay precede any fitting. Proposed no-fit diagnostics include marker/conditional-negative/origin associations and the fixed Stage18 paired permutation-AP protocol extended to44 fields; do not rerun it now. Old removal/shuffle fits remain historical and do not validate44 fields. Any new diagnostic fits would require additional explicit budget approval and cannot be slipped into this four-fit plan.

## 11. Fit budget, decisions and stopping

Stage18 used16 fits; its20 unused slots expired. **Currently authorized new fits:0.** The proposed four attempts require explicit prospective authorization and a policy amendment resolving that expiry, while retaining the inherited36 ceiling. Proposed cumulative attempts would be20, not a reset. A fresh linked ledger preserves Stage18 unchanged. Failed/adaptive/repeated attempts all consume slots; no automatic replacements or reuse of spare capacity.

No promotion threshold is invented after inspecting results. Any later model-selection decision requires its own predeclared rule and approval; Stage18 selection remains. Support failure, technical mismatch or missing custody cannot become a PASS through performance. No oversampling, relabeling, changed cutoffs or accept-until-support generation. See [budget and reuse policy](../evidence/stage20/fit_budget_validation_reuse_policy.json).

## 12. Limitations, preservation and next step

The proposal addresses mathematical information loss, not proven causes of each error. Sparse labels, dependent communities, synthetic assumptions and model approximation remain. More direct components may yield easier policy reproduction without real-world benefit. Symbolic witnesses and paper checks do not establish working extraction, runtime, numerical implementation or achieved gain.

The Stage15A broader historical snapshot remains incomplete as documented in16V; no historical recovery, manifest weakening or old report rewrite occurred. Named preservation excludes unread sealed bytes. No Flask, MySQL, API, V1 production or V3 integration changes occurred.
''')
    changed=[name for name,digest in protected.items() if sha(name)!=digest]
    if changed: raise ValueError(changed)
    write('preservation_verification.json',{'status':'PASS_NAMED_SCOPE','count':len(protected),'before_sha256':protected,'after_sha256':protected,'changed_paths':changed,'sealed_content_read_or_enumerated':False,'scope':'Inherited Stage19 named protection plus Stage19 output hashes and decision. Full historical snapshot gap retained; no sealed byte coverage claimed.'})
    sections.append(f'**{len(protected)} named protected files** match recorded hashes. [Preservation evidence](../evidence/stage20/preservation_verification.json) records the exact scope. All earlier reports, original40 matrices, Stage18 models/ledger, labels and dataset bytes remain unchanged. New writes are this report, the design-document builder and sixteen evidence records under `ml_v4/evidence/stage20/`. No RNG, extractor, estimator or generator is imported.\n')
    sections.append('''Recommend review and explicit approval of the proposed feature design and Stage16T compatibility amendment. Only after that should a separately authorized implementation stage create independent fixtures and development matrices. Modeling and independent custody/evaluation need their own approvals. Retaining40 remains a valid restricted-claims alternative.

## 13. Final decision

**A — MINIMAL FEATURE AMENDMENT DESIGN READY**

Four additions are specified with observable definitions, causal availability, missingness, redundancy proofs, costs and compatibility requirements. Decision A authorizes **no implementation, extraction, generation, fitting, threshold work, sealed access or integration**. No next stage starts automatically.

V4 STAGE 20 COMPLETE — WAITING FOR APPROVAL.
''')
    with REPORT.open('x',encoding='utf-8',newline='\n') as f: f.write('\n'.join(sections))
    hashes={str(p.relative_to(ROOT)).replace('\\','/'):sha(p.relative_to(ROOT)) for p in OUT.glob('*.json')}
    hashes[str(REPORT.relative_to(ROOT)).replace('\\','/')]=sha(REPORT.relative_to(ROOT))
    hashes[str(Path(__file__).relative_to(ROOT)).replace('\\','/')]=sha(Path(__file__).relative_to(ROOT))
    write('stage20_decision.json',{'decision':'A — MINIMAL FEATURE AMENDMENT DESIGN READY','authorizes_implementation':False,'feature_version':contract['feature_version'],'semantic_fields':44,'estimator_columns':46,'new_fits':0,'features_extracted':False,'data_generated':False,'model_evaluation_executed':False,'sealed_access':False,'selected':'primary_XGB','comparator':'primary_HGB','protected_count':len(protected),'artifact_sha256':hashes,'verification':'Static definition/count/assertion and artifact hash checks only; no feature runtime tests','next_step':'Separate design/amendment approval, then separately authorized implementation; no automatic progression'})
    print(f'Stage20 design complete: {len(features)} proposed additions; {len(protected)} protected hashes match; {len(hashes)} output hashes.')

if __name__ == '__main__':
    main()
