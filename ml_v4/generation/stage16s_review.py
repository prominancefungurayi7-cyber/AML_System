"""Read-only development support review. No generator import, sampling or model code."""
import json
import hashlib
from pathlib import Path
from collections import Counter, defaultdict
from fractions import Fraction as Q
from stage16r_contract import ROOT, DAY, FAMILIES, read_events, window
from stage16r_evaluator import Evaluator, cash_stats, total

OUT=ROOT/'ml_v4/evidence/stage16s'
REPORT=ROOT/'ml_v4/reports/V4_STAGE16S_FAMILY_SUPPORT_REVIEW.md'

def read(p): return json.loads((ROOT/p).read_text(encoding='utf-8'))
def digest(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def save(name,value):
    with (OUT/name).open('x',encoding='utf-8',newline='\n') as s: json.dump(value,s,indent=2,sort_keys=True,allow_nan=False); s.write('\n')

def topology(current,edges):
    adjacency=defaultdict(list)
    for x in edges:
        if current.time-7*DAY<x.time<=current.time and x.key<current.key: adjacency[x.sender_wallet].append(x)
    def visit(node,seen,key,depth):
        if depth==5: return False
        for x in adjacency[node]:
            if x.key<=key or x.receiver_wallet in seen: continue
            if x.receiver_wallet==current.sender_wallet: return True
            if visit(x.receiver_wallet,seen|{x.receiver_wallet},x.key,depth+1): return True
        return False
    return visit(current.receiver_wallet,{current.receiver_wallet},(-1,-1),0)

def conditions(state,e,f):
    t=e.time
    if f in ('S2','S4'):
        hist=state.activity[e.subject]; r=window(hist,t-7*DAY,t)+[e]; b=window(hist,t-35*DAY,t-7*DAY)
        if f=='S2':
            cr=[x for x in r if 20*abs(x.amount_minor-e.amount_minor)<=e.amount_minor]
            cb=[x for x in b if 20*abs(x.amount_minor-e.amount_minor)<=e.amount_minor]
            return {'cluster_count_ge4':len(cr)>=4,'cluster_value_ge20000':total(cr)>=20000,'cluster_share_ge0.6':Q(len(cr),len(r))>=Q(3,5),'cluster_growth_ge2':Q(len(cr))/max(1,Q(len(cb),4))>=2}
        band=lambda x:700000<=x.amount_minor<=1050000
        rr=[x for x in r if band(x)]; bb=[x for x in b if band(x)]
        return {'current_in_band':band(e),'recent_count_ge5':len(r)>=5,'band_count_ge3':len(rr)>=3,'band_variation_ge2':len({x.amount_minor for x in rr})>=2,'band_share_ge0.4':Q(len(rr),len(r))>=Q(2,5),'band_growth_ge2':Q(len(rr))/max(1,Q(len(bb),4))>=2}
    if f=='A4':
        r=window(state.services[e.agent_id],t-DAY,t)+[e]; b=window(state.services[e.agent_id],t-29*DAY,t-DAY)
        rs,bs=cash_stats(r),cash_stats(b); v,c=rs['value_skew'],rs['count_skew']
        return {'cash_count_ge6':rs['in_count']+rs['out_count']>=6,'cash_wallets_ge3':rs['distinct']>=3,'abs_value_skew_ge0.6':abs(v)>=Q(3,5),'abs_count_skew_ge0.5':abs(c)>=Q(1,2),'sign_agreement':v*c>0,'skew_change_ge0.4':abs(v-bs['value_skew'])>=Q(2,5)}

def partition(name):
    base=f'ml_v4/data/development/{name}/'
    events=read_events(ROOT/(base+'warmup_observables.csv'))+read_events(ROOT/(base+'transactions.csv'))
    truth={r['transaction_id']:r for r in (json.loads(line) for line in (ROOT/(base+'family_evidence.jsonl')).read_text().splitlines())}
    meta={r['transaction_id']:r for r in read(base+'private_provenance.json')}
    pops=read(base+'private_population.json'); old=read(f'ml_v4/evidence/stage16r/{name}_audit.json')
    plans={(i,p['id']):p for i,pop in enumerate(pops) for p in pop['episodes']}
    rows={f:[] for f in FAMILIES}; own={f:Counter() for f in FAMILIES}; reasons={f:Counter() for f in FAMILIES}
    focus={f:{'eligible_own_motif':0,'failures_nonexclusive':Counter(),'sole_failed_condition':Counter(),'all_conditions_pass':0} for f in ('S2','S4','A4')}
    graph=Counter(); state=Evaluator()
    for e in events:
        if e.transaction_id in truth:
            tr=truth[e.transaction_id]; p=meta[e.transaction_id]
            for f in FAMILIES:
                if f in tr['families']: rows[f].append((e,tr,p))
                reasons[f][tr['reasons'][f]]+=1
                if p['origin']==f:
                    role=p['event_role']; own[f][role]+=1
                    own[f][role+'_eligible']+=int(tr['eligible'][f])
                    own[f][role+'_family_positive']+=int(f in tr['families'])
                    own[f][role+'_any_positive']+=tr['ground_truth_label']
                    if role=='motif':
                        own[f]['motif_ineligible_'+tr['reasons'][f]]+=int(not tr['eligible'][f])
                        if f in focus and tr['eligible'][f]:
                            gates=conditions(state,e,f); failed=[k for k,v in gates.items() if not v]
                            assert (not failed)==(f in tr['families'])
                            q=focus[f]; q['eligible_own_motif']+=1; q['failures_nonexclusive'].update(failed)
                            if len(failed)==1: q['sole_failed_condition'][failed[0]]+=1
                            q['all_conditions_pass']+=int(not failed)
                        if f=='N3':
                            graph['own_motif_rows']+=1
                            top=topology(e,state.edges)
                            graph['chronological_topology_available']+=int(top)
                            graph['no_chronological_topology']+=int(not top)
                            graph['topology_present_but_full_amount_conjunction_fails']+=int(top and f not in tr['families'])
                            graph['full_predicate_positive']+=int(f in tr['families'])
            
        state.observe(e)
    result={}
    for f,rr in rows.items():
        oldrow=old['family_support'][f]; n=len(rr); assert n==oldrow['decision_points']
        days=Counter(int((e.time-42*DAY)//DAY) for e,_,_ in rr)
        bins=Counter(int((e.time-42*DAY)//(30*DAY)) for e,_,_ in rr)
        subjects=Counter(e.agent_id if f.startswith('A') else e.receiver_wallet if f=='N1' else e.subject for e,_,_ in rr)
        units=Counter(p['population_unit'] for _,_,p in rr)
        origins=Counter(p['origin'] for _,_,p in rr)
        ownplans=[p for p in plans.values() if p['origin']==f]
        result[f]={**oldrow,'required_support_percent':100*n/oldrow['minimum_objective'],'subject_objective':20 if name=='validation' else None,'cluster_objective':30 if name=='validation' else None,'subject_objective_scope':'Stage 15 declares Validation/Final and Independent diversity objectives; no separate Train diversity minimum','temporal':{'scored_30day_counts':{str(i):bins[i] for i in range(6)},'active_days':len(days),'max_day_share':max(days.values())/n if n else None,'max_30day_share':max(bins.values())/n if n else None},'entity':{'top5_subject_share':sum(sorted(subjects.values(),reverse=True)[:5])/n if n else None,'unit_counts':dict(units)},'other_predicate_overlap_rows':sum(len(t['families'])>1 for _,t,_ in rr),'exclusive_family_rows':sum(len(t['families'])==1 for _,t,_ in rr),'positive_origin_counts':dict(origins),'all_scored_eligibility_reasons':dict(reasons[f]),'own_origin_opportunities':dict(own[f]),'own_origin_episodes':len(ownplans),'planned_E':sum(p['E'] for p in ownplans),'planned_M':sum(p['M'] for p in ownplans),'matched_hard_motif_count':sum(p['M'] for p in plans.values() if p['origin'].startswith('H') and p['family']==f)}
        assert result[f]['planned_M']==own[f]['motif']
    return {'families':result,'distribution':old['distribution'],'focus_condition_audit':focus,'N3_structural_audit':dict(graph),'accounting':{'minimum_inventory_minor':min(p['minimum_inventory_minor'] for p in pops),'numerical_amount_proposal_rejections':sum(p['amount_rejections'] for p in pops),'accounting_failures':0,'basis':'Frozen integrity PASS and stop-on-negative-inventory source. Numerical amount bounds rejection is not an accounting retry.'},'units':len(pops)}

def run():
    if OUT.exists() or REPORT.exists(): raise FileExistsError('Stage 16S outputs already exist')
    old=read('ml_v4/evidence/stage16r/final_verification.json')
    expected={**read('ml_v4/evidence/stage16r/protection.json')['after'],**old['artifact_sha256'],**old['source_sha256']}
    for n,files in read('ml_v4/evidence/stage16r/dataset_manifest.json')['development_sha256'].items():
        expected.update({f'ml_v4/data/development/{n}/{f}':h for f,h in files.items()})
    for p in ('ml_v4/evidence/stage16r/final_verification.json','ml_v4/evidence/stage16r/draw_registry.json','ml_v4/evidence/stage16r/draw_lifecycle.jsonl','ml_v4/evaluation/sealed/public_commitment.json'):
        expected[p]=digest(p)
    before={p:digest(p) for p in expected}; assert before==expected
    # Read all frozen design and amendment documents bound by the existing manifest.
    authoritative={p:(ROOT/p).read_text(encoding='utf-8') for p in before if p.startswith('ml_v4/design/')}
    assert authoritative
    public=read('ml_v4/evidence/stage16r/holdout_public_certificate.json')
    assert public==read('ml_v4/evaluation/sealed/public_commitment.json')
    OUT.mkdir(parents=True)
    results={}
    for n in ('train','validation'):
        print('Reviewing '+n+' saved development events only.',flush=True); results[n]=partition(n)
    save('development_support_review.json',{'scope':'Train and Validation only; aggregate diagnostic counts, no model features','temporal_bins':'Six fixed 30-day blocks from scored start; daily maxima are descriptive','overlap':'Family supports overlap and are never reduced by another predicate firing','partitions':results})
    save('holdout_boundary_verification.json',{'scope':'Existing named public metadata and loader source only; no seal enumeration or encrypted/private bytes read','commitment_id':public['commitment_id'],'public_support_policy':{k:v['support_policy'] for k,v in public['certificates'].items()},'disposition':public['disposition'],'original_holdout_support_policy_satisfied':False,'private_failure_family_or_counts':'UNKNOWN; not inferred','certificate_caveat':'Custodian support_policy combines family counts, subject/cluster coverage and prevalence; FAIL does not identify which condition or family failed.','loader_source_sha256':{p:before[p] for p in before if p.endswith(('stage16r_loader.py','stage16r_authorized_loader.py'))},'boundary_changed':False,'loader_called':False,'private_counts_requested':False,'sealed_contents_accessed':False,'scope_limit':'Verifies this audit access and unchanged source/public metadata; does not attest unread encrypted bytes or all external OS activity.'})
    build_report(results,before,public)

def build_report(results,before,public):
    explanations={
      'S1':'Own opportunities use a dispersed share of one base-mixture total; the target additionally requires USD 300 total, four causal recent events, variation, limited maximum share and eligible history. Source supports this mechanism, but no S1 gate-by-gate causal allocation is estimated.',
      'S2':'Fresh jittered motif amounts need not leave four payments within the current-centered 5% band; cluster value and 60% share must also pass. Context and ordinary activity enter the denominator. The measured gate failures below distinguish this attrition from historical ineligibility.',
      'S3':'Minimum decision-point support is met. Day boundaries and occupied-hour/value/history conjunction still filter opportunities; success does not establish independent precision or all-domain reliability.',
      'S4':'The conditional USD 5000..13000 recipe is wider than the target band. A current in-band payment, three in-band rows, 40% share, variation, rate increase and history must coincide. The condition audit quantifies overlap among failures without treating them as independent causes.',
      'N1':'Incoming collection requires prior receiver-specific directed support, three senders, four recent edges and sufficient value. Two-to-eight partner opportunities and context are not guaranteed positive decisions. Eligibility and own-origin counts identify observed attrition; relative causal effects remain unestimated.',
      'N2':'Minimum support is met, with positives also arising outside intended N2 episodes. Overlap with other predicates enriches supervision but does not create independent observations.',
      'N3':'No long-history eligibility gate exists for W2W. Early walk events need not close a chronological return route; reversed ordering and broad amount factors can defeat a full path. Topology-present versus amount-conjunction failure is measured on own motif rows. Absence of a qualifying path is not evidence of accounting loss.',
      'N4':'A prior incoming-W2W anchor, funding minimum, outward fraction and remaining-funding conjunction are required. A funding proposal itself is not an outward detection, and shared small-value draws may not reach the funding minimum. No gate-specific counterfactual effect is claimed.',
      'A1':'Minimum support is met and many positives originate outside A1 episodes. This dominant support cannot substitute for sparse agent families or establish operational specificity.',
      'A2':'Top-two concentration and change from its own baseline must coincide after eight recent services and historical support. Choosing two-to-six customers with shares 0.35..0.90 is broader than the target conjunction; intended opportunities are not labels.',
      'A3':'A 0.25..3-hour motif can extend beyond the one-hour target window; count, breadth and baseline conditions also apply. Validation subject breadth is below its objective. No temporal-duration intervention was performed.',
      'A4':'Cash event count, distinct wallets, value skew, count skew, sign agreement and historical skew change must all hold. Random direction probabilities and heterogeneous amounts are not guarantees of the joint imbalance. The measured eligible-motif failures identify limiting conditions, while subject breadth is also insufficient.'}
    causes={'family_interpretations':explanations,'measured_focus':{n:{'conditions':a['focus_condition_audit'],'N3':a['N3_structural_audit']} for n,a in results.items()},'causal_limits':'Descriptive attrition and source mechanisms, not causal percentages. Own-origin motifs are a diagnostic subset; ordinary and hard-origin events can also become positive. Single-gate failures overlap; sole-failure counts do not authorize changing gates.','opportunity_adequacy':'The fixed E budget includes context and pre-detection events. Realized positive support is inadequate for nine family objectives; this does not prove that more rows alone would solve eligibility, composition or diversity.','eligibility':'Saved eligibility/reason counts are reported for all scored rows and intended motif rows. N4 anchor eligibility is not a long-history requirement. Inapplicable roles must not be described as historical insufficiency.','accounting':{n:a['accounting'] for n,a in results.items()},'overlap':'Does not remove any family flags or reduce their individual counts; only the binary union deduplicates.','diversity':'Validation has only three units; subject/cluster counts are coverage measures, not effective independent sample sizes. No minimum was invented for Train.','implementation_limit':'Read-only evidence review does not independently certify every stochastic population mechanism or remedy the documented process/current-user holdout boundary limitation.'}
    save('root_cause_analysis.json',causes)
    options=[
      {'option':'A','name':'Preserve V4 with restricted claims','benefits':'No new draw; useful binary/domain development evidence and transparent sparse-family estimates.','limitations':'Cannot meet original all-family or failed holdout support policy; family estimates remain imprecise and unit dependence remains.','comparability':'Only frozen V4 development population; no claim to original compliant final evaluation.','leakage_risks':'Treating repeatedly reviewed Validation as independent final evidence; relaxing gates after outcomes.','policy_compatibility':'Preservation and qualified claims fit shortfall policy, but training remains blocked absent explicit approved scope and evaluation plan.','new_version':'Dataset unchanged; revised research-claim/evaluation protocol must be versioned.'},
      {'option':'B','name':'Separately versioned external family challenge evaluation','benefits':'Independent measurement of sparse families using justified coverage and explicit uncertainty.','limitations':'Enriched challenge prevalence does not estimate population precision/AP or repair frozen holdout failure. Cannot guarantee plausible support in advance.','comparability':'Separate report and denominators; never pool with V4 population metrics or rank as the same benchmark.','leakage_risks':'Challenge examples, seeds or errors feeding training; choosing cases by model success; repeated accept-until-support loops.','policy_compatibility':'Explicitly contemplated by Stage 15 shortfall_resolution; requires approval and preregistration before execution.','new_version':'New challenge-set identifier, manifest, protocol, independent entities/streams and custodian seal; V4 unchanged.'},
      {'option':'C','name':'Future full experiment','benefits':'Can address population/history/opportunity design together and seek all-family coverage under a fresh declared protocol.','limitations':'Cost, synthetic realism and support remain uncertain; repeated generation is not a scientific remedy by itself.','comparability':'New population version and fresh evaluation; original V4 preserved as historical evidence.','leakage_risks':'Seed shopping or recycling failed evaluation feedback into a claimed untouched benchmark.','policy_compatibility':'Allowed only through versioned authorization and compatibility declaration, never a silent overwrite.','new_version':'Yes: new experiment, design and fresh holdouts.'},
      {'option':'D','name':'Preserved V4 development plus justified independent extension','benefits':'Retains all three domains and the first draw; uses a separately justified challenge evaluation where current family coverage is sparse.','limitations':'Does not restore the original population-level Final/Independent claim; successful extension adequacy remains unproven.','comparability':'Two explicitly distinct evidence tracks; separate population and challenge conclusions with no pooled prevalence.','leakage_risks':'Blending datasets/metrics or tuning to extension outcomes. Freeze extension design and eventual model before evaluation; no developer access to challenge outcomes during selection.','policy_compatibility':'Combines the declared preservation/challenge pathway; holdout quarantine and G11 remain in force until a separately approved successor protocol defines eligible claims.','new_version':'Versioned extension and research/evaluation protocol; no change to existing V4 bytes.'}]
    save('scientific_options.json',{'options':options,'recommendation':'Option D implemented only through a separately approved Option B challenge protocol; no implementation in Stage 16S. If unchanged original population-wide/full-family final claims are mandatory, choose a new experiment (Option C).','original_policy':'Cannot be satisfied by the existing failed sealed support certificates; no gate is relaxed.'})
    decision='B — ADDITIONAL INDEPENDENT CHALLENGE EVALUATION REQUIRED'
    save('stage16s_decision.json',{'decision':decision,'authorizes':'Audit findings and a recommendation only. May inform a separately requested, versioned extension design.','blocked':['new transactions or regeneration','relabeling or predicate changes','features/model training/threshold work','opening or releasing quarantined holdouts','claiming original full-family evaluation policy satisfied'],'original_objective_met':False,'model_validated':False,'all_three_domains_retained':True,'new_experiment_condition':'A new full experiment is required if the original population-wide all-family evaluation claim must be retained without a qualified extension.','stage16r_decision_preserved':True})
    text=['# MODEL V4 — STAGE 16S FAMILY-SUPPORT FAILURE REVIEW','## 1. Executive finding',f'**{decision}.**','The frozen draw is technically usable development evidence, but it does **not** satisfy the original full-family independent-evaluation objective. Nine families miss the decision-point minimum in both development partitions. Validation S2/S4 additionally have only 7/12 subjects and 7/12 clusters; A3/A4 have only 18/17 subjects. Passing aggregate prevalence does not cure these deficits. No model has been trained or validated in this stage.','Recommend preserving V4 and designing a separately versioned independent challenge extension (Option D using the Option B pathway). This is a recommendation, not execution authorization. If the unchanged original population-wide full-family evaluation claim is mandatory, a new experiment is needed. The current sealed holdouts cannot satisfy their original support policy.','## 2. Scope, authority and method','Read frozen Stage 15 design/acceptance/support/target/holdout policies, Stage 15A amendment, Stage 16R report, generator/evaluator source, Train/Validation audits and named public certificates. All source and development inputs are hashed before and after. Only existing Train/Validation observables, family evidence and diagnostic provenance are analyzed. No generator is imported or called; no random stream, feature matrix, model, revised label or threshold is created.','Supports use frozen family flags. Six fixed 30-day blocks start at the scored horizon; daily and block maxima summarize temporal concentration. Subject and cluster maxima are descriptive dependence measures. Episode clusters use stored IDs; background clusters use unit × UTC day. Pairwise overlap is reproduced in JSON; overlapping rows must not be summed. Eligibility reasons use frozen evaluator output. Additional S2/S4/A4 condition checks use exact rational comparisons on eligible own-origin motif rows and must reproduce their stored family result. N3 checks topology separately on own-origin motif rows, with no amount filter or path truncation. These are aggregate diagnostics, not model inputs.','## 3. All-family support and concentration','| Partition | Family | Minimum | Actual | Achieved % | Subjects | Clusters | Max subject % | Top 5 subjects % | Max cluster % | Max day % | Max 30d % | Other-predicate overlap |\n| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for n,a in results.items():
        for f,r in a['families'].items():
            text.append(f"| {n} | {f} | {r['minimum_objective']} | {r['decision_points']} | {r['required_support_percent']:.1f} | {r['distinct_subjects']} | {r['distinct_clusters']} | {100*r['maximum_subject_share']:.1f} | {100*r['entity']['top5_subject_share']:.1f} | {100*r['maximum_cluster_share']:.1f} | {100*r['temporal']['max_day_share']:.1f} | {100*r['temporal']['max_30day_share']:.1f} | {r['other_predicate_overlap_rows']} |")
    text+=['Validation/Final diversity objectives are ≥20 subjects and ≥30 clusters per family; Independent objectives are ≥12 and ≥20. There is no separately declared Train subject/cluster minimum. Only S3, N2 and A1 meet both development decision-count minima. A1 exceeds its planning upper range; this is not a deletion trigger. Exact temporal block counts, unit counts, exclusive-family support, full pairwise overlaps and origins are in [development evidence](../evidence/stage16s/development_support_review.json).','## 4. Opportunity, composition and eligibility','The table concerns each family’s own intended origin, not all positives or matched hard origins. E includes motif and context rows; M is only the motif budget. Eligibility is checked on the realized causal ledger. Rows early in a motif may lack accumulated evidence even when the completed motif looks strong. No counterfactual generation was used.','| Partition | Family | Episodes | E | M | Context | Eligible motif | Own motif family positives | Own context family positives | Positive rows outside own origin |\n| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for n,a in results.items():
        for f,r in a['families'].items():
            q=r['own_origin_opportunities']; outside=r['decision_points']-q.get('motif_family_positive',0)-q.get('context_family_positive',0)
            text.append(f"| {n} | {f} | {r['own_origin_episodes']} | {r['planned_E']} | {r['planned_M']} | {r['planned_E']-r['planned_M']} | {q.get('motif_eligible',0)} | {q.get('motif_family_positive',0)} | {q.get('context_family_positive',0)} | {outside} |")
    text+=['The achieved yield shows insufficient *effective positive opportunities* for nine objectives, not proof that the total transaction budget alone is too small. Historical eligibility and full-rule attrition are distinct: subtract eligible motif from M for the former, then positives from eligible motif for the latter. For N4, lack of an incoming anchor is not insufficient 28/35-day history. Role inapplicability is likewise distinct from age. Background and matched hard origins can add positive support; origin never assigns a label.','### Focused compound-condition audit','Failures below are **nonexclusive**, conditional on eligible own-origin motif rows. Their sum can exceed the denominator. Conditions are not called unjustifiably restrictive: these are the declared research rules. Removing a failed gate would change the task, which this stage does not recommend or perform.','| Partition | Family | Eligible own motif N | All gates pass | Failed condition | Failure count | Sole failure count |\n| --- | --- | ---: | ---: | --- | ---: | ---: |']
    for n,a in results.items():
        for f,q in a['focus_condition_audit'].items():
            for gate,count in q['failures_nonexclusive'].items(): text.append(f"| {n} | {f} | {q['eligible_own_motif']} | {q['all_conditions_pass']} | {gate} | {count} | {q['sole_failed_condition'].get(gate,0)} |")
    text+=['### N3: topology versus monetary conjunction','| Partition | Own motif rows | No chronological return topology | Topology present but full amount conjunction fails | Full predicate positive |\n| --- | ---: | ---: | ---: | ---: |']
    for n,a in results.items():
        q=a['N3_structural_audit']; assert q['own_motif_rows']==q['no_chronological_topology']+q['topology_present_but_full_amount_conjunction_fails']+q['full_predicate_positive']
        text.append(f"| {n} | {q['own_motif_rows']} | {q['no_chronological_topology']} | {q['topology_present_but_full_amount_conjunction_fails']} | {q['full_predicate_positive']} |")
    text+=['A topology can fail amount conditions on every candidate route; this table does not identify a single offending edge or causal percentage. The target has no long-baseline gate, so N3 scarcity cannot be attributed to a 35-day eligibility requirement.','### Family-specific interpretation']
    text += [f'**{f}:** {explanations[f]}' for f in FAMILIES]
    text+=['### Accounting, overlap and diversity','Stage 16R independent ledger checks report zero schema/cross-unit errors and no capacity failure. The generator stops on negative inventory rather than dropping or resampling transactions. Thus no evidence supports accounting attrition as the support-loss mechanism. Numerical amount bounds rejection did occur; it changes proposals under the frozen law, not labels. Its causal effect on family yield is unmeasured.']
    for n,a in results.items(): text.append(f"{n}: minimum inventory {a['accounting']['minimum_inventory_minor']} cents; recorded numerical proposal rejections {a['accounting']['numerical_amount_proposal_rejections']}. These counters do not identify rejected positive cases; no such labels were evaluated.")
    text+=['Target overlap does not remove individual-family support: every true predicate remains recorded. It does mean family rows and domain totals cannot be treated as independent samples. Subject and cluster shortfalls establish inadequate coverage where specified, not a proven lack of every relevant behaviour. Three Validation communities constrain transport and uncertainty even for well-supported families.','## 5. Scientific consequences','| Objective | Finding |\n| --- | --- |\n| A. Binary suspicious-pattern classification | Both classes have substantial development support and the labels implement observable review rules. Suitable for a potential authorized development study; no trained model or independent performance validation exists. Dominant families can mask weak rare-family performance. |\n| B. All three domains | All domains have positive and domain-only development support (table below). Aggregate domain evaluation is possible in principle, but reliable coverage of each domain’s mechanisms is not established; sparse subfamilies and dependence preclude an unqualified reliability claim. |\n| C. Each of twelve families | Original support objective fails for nine; S2/S4 subject and cluster scarcity is especially severe. Even the three count-passing families have no measured model recall. No family has been validated by this audit. |\n| D. Independent evaluation under original policy | Not available: both existing public support-policy certificates FAIL. No private family cause, count or prevalence is known or inferred. The frozen holdout gates cannot be waived by restricted wording or a separate challenge set. |','Development domain counts (overlapping totals and disjoint domain-only slices):','| Partition | Target 0 | Target 1 | Structuring | Network | Agent | Structuring only | Network only | Agent only | Multi-domain |\n| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for n,a in results.items():
        d=a['distribution']; text.append('| '+n+' | '+' | '.join(str(x) for x in [d['target0'],d['target1'],*[d['domains'][k] for k in ('structuring','network','agent')],*[d['domain_only'][k] for k in ('structuring','network','agent')],d['multi_domain']])+' |')
    text+=['Count thresholds are predeclared coverage objectives, not mathematical guarantees of precise recall. Independent-binomial intuition is optimistic with repeated subjects and only three units. No confidence interval for model performance can be computed without predictions, and no effective sample size is asserted.','## 6. Sealed evaluation boundary',f"Existing commitment: `{public['commitment_id']}`. Final Test support policy: **FAIL**. Independent support policy: **FAIL**. Disposition remains **{public['disposition']}**.",'The custodian’s combined support flag includes family counts, subjects/clusters and prevalence. A FAIL cannot identify which family or condition failed. No private counts were requested, reconstructed or inferred. Only named public metadata and loader source were read; no custodian invocation, seal enumeration, envelope hash/decryption or evaluation loader call occurred. Current-user process/encryption separation remains the documented limitation; this review does not strengthen or weaken it.','## 7. Options (not implemented)']
    for opt in options:
        text.append(f"### Option {opt['option']}: {opt['name']}")
        text += [f"**{label}:** {opt[key]}" for label,key in [('Benefits','benefits'),('Limitations','limitations'),('Comparability','comparability'),('Leakage risks','leakage_risks'),('Stage 15 compatibility','policy_compatibility'),('Version requirement','new_version')]]
    text+=['## 8. Recommended path and authorization boundary','Preserve the first V4 draw and all three domains. Seek a separately approved extension-design stage before any data or model work. Predeclare sparse-family scientific mechanisms, unchanged target semantics, legitimate boundary negatives, subject/community diversity, fixed opportunity budgets, support failure handling and separate estimands. Select justified opportunities before labels; never override labels, duplicate positives, retain only successful cases or retry seeds to reach counts. If plausible support cannot be attained, report that limitation instead of manufacturing positives.','An eventual independent challenge set must have fresh entities/history/streams, separate custodianship and no development access to examples or labels. Freeze its protocol before construction and the eventual model before releasing challenge outcomes. Keep challenge metrics and prevalence separate from V4 population metrics. Include context from all three domains and report every family, including sparse estimates and their limitations. No extension may retrospectively turn the two existing FAIL certificates into PASS.','This route avoids discarding usable evidence or repeating the entire production experiment now. It can support a narrower, transparently extended research claim. If the original full-population Final/Independent claim must be preserved unchanged, Option C requires a new versioned experiment and fresh evaluation; that work is not authorized here.','**This decision authorizes no new generation, feature construction, training, threshold work or holdout access.** It records an audit recommendation only. Training and the original full-family evaluation claim remain blocked pending explicit approval of a defensible successor protocol.','## 9. Evidence and preservation','[Development support review](../evidence/stage16s/development_support_review.json), [root-cause analysis](../evidence/stage16s/root_cause_analysis.json), [holdout boundary verification](../evidence/stage16s/holdout_boundary_verification.json), [scientific options](../evidence/stage16s/scientific_options.json), [preservation verification](../evidence/stage16s/preservation_verification.json), [decision](../evidence/stage16s/stage16s_decision.json). Source: [stage16s_review.py](../generation/stage16s_review.py). The script refuses existing Stage 16S outputs.','The explicit protected hash set includes historical/application artifacts, frozen design/amendment and failed attempts, Stage 16R source/report/evidence, development transactions/truth/provenance, and named public commitment metadata. Unread sealed contents are outside the byte-verification claim. No historical file is rewritten.','## 10. Decision',f'**{decision}.**','V4 STAGE 16S COMPLETE — WAITING FOR APPROVAL.']
    import re
    body=re.sub(r'(?<=\|)\n\n(?=\|)','\n','\n\n'.join(text))+'\n'
    with REPORT.open('x',encoding='utf-8',newline='\n') as s:s.write(body)
    after={p:digest(p) for p in before}; assert before==after
    artifacts={p.relative_to(ROOT).as_posix():digest(p.relative_to(ROOT).as_posix()) for p in OUT.iterdir() if p.is_file()}
    artifacts[REPORT.relative_to(ROOT).as_posix()]=digest(REPORT.relative_to(ROOT).as_posix())
    src=Path(__file__).resolve().relative_to(ROOT).as_posix(); artifacts[src]=digest(src)
    save('preservation_verification.json',{'status':'PASS','protected_count':len(before),'before':before,'after':after,'changed_paths':[],'stage16s_artifact_sha256':artifacts,'sealed_bytes_opened_or_hashed':False,'new_transactions':0,'modified_labels':0,'model_features_constructed':0,'model_fits':0,'source_read_only_inputs':True})
    print(decision,flush=True)

if __name__=='__main__': run()
