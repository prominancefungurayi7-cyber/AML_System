"""Post-fit source synthesis and additional descriptive checks; never fits a model."""
import csv
import numpy as np
from run_stage11 import load_matrices,FAMILIES
from stage14_growth_diagnosis import *

def main():
    contract={'result':'PASS: corrected implementation agrees with Stage 10A contract',
       'formula':'D_recent / max(1, median(D_week1,D_week2,D_week3,D_week4))',
       'recent':'(t-7d,t], prior keys < current key, plus current agent service',
       'baseline':'(t-35d,t-7d], four disjoint 7d buckets; lower open, upper closed',
       'eligibility':'Agent present; first prior observable service <= t-35d; at least 12 baseline services. No recent distinct/novelty/target gate.',
       'denominator':'Median of four weekly DISTINCT serviced-wallet counts, including zero buckets; floor 1',
       'missing':'-1 when absent agent or baseline ineligible; dimensionless nonnegative observed values',
       'current':'Included exactly once before state update; type/agent/serviced-wallet/time identify service. Amount is unused.',
       'cash_in':'One service at named agent for serviced_wallet', 'cash_out':'One service at named agent for serviced_wallet',
       'assisted_W2W':'One service using explicit serviced_wallet, including when receiver is serviced; not necessarily sender',
       'direct_W2W':'No agent subject; -1; creates no agent service history',
       'ordering':'UTC timestamp then integer ID; smaller same-time ID is prior; state updated after emission; no cross-partition state',
       'cold_start':'Unavailable until full 35d observation and baseline count; displayed coverage caps at 28d and cannot establish eligibility',
       'audit_scope':'Independent observable-only primitive calculation exactly matches all 75000 saved growth values. No official matrix regenerated or edited.',
       'sources':{'ml_v3/src/stage10a_pipeline.py':sha(ROOT/'src/stage10a_pipeline.py'),'ml_v3/src/stage10a_contract.py':sha(ROOT/'src/stage10a_contract.py')}}
    save('feature_contract',contract)
    findings=[
      {'source':'ml_v3/src/generate_v3.py','line':8,'finding':'Frozen truth materialization imports reference_evaluator.evaluate_rows, not reference.ReferenceEvaluator. A1 reconstruction against frozen labels confirms this source path on both development partitions.'},
      {'source':'ml_v3/src/generate_v3.py','line':65,'finding':'Final decision_point_target is bool(frozen evidence families), independent of private routine/hard/campaign origin. Legitimate-like origin rows crossing A1 gates become target1 and disappear from target0 overlap comparisons.'},
      {'source':'ml_v2/src/dataset_generator.py','line':206,'finding':'Routine events sample active wallets broadly across six 30d blocks; agent selection uses fixed activity-band weights .5/1/2. The source has no explicit evolving ordinary agent catchment, customer-acquisition campaign, or seasonal wallet-population process.'},
      {'source':'ml_v2/src/dataset_generator.py','line':256,'finding':'Both A1 and H7/A1 select 4..min(16,n-1) counterparts with lowest preceding 30d service frequency. Wallets are cycled through, with a previously seen wallet in the final position when available. This encourages novelty; it does not set the final growth ratio to a constant.'},
      {'source':'ml_v2/src/dataset_generator.py','line':262,'finding':'A2/H8-A2 choose 2..min(6,n/2) concentration wallets; 35%..85% of episode events use them, with remaining events sampled outside that subset. Growth is not a direct A2 primitive.'},
      {'source':'ml_v2/src/dataset_generator.py','line':333,'finding':'A3/H7-A3 use 2..4 temporal clusters with within-cluster width .2 before scaling to episode duration; serviced wallets otherwise sampled broadly. This supplies burst information, not a growth substitute.'},
      {'source':'ml_v2/src/dataset_generator.py','line':271,'finding':'A4/H8-A4 guarantee an opening two-versus-one cash direction portion and sample amounts until dominant value share is 60%..95%. Subsequent events, history and target conjunction determine whether A4 fires.'},
      {'source':'ml_v2/src/dataset_generator.py','line':184,'finding':'H7 maps to A1/A3 and H8 to A2/A4 through the shared scenario manifest. Hard episodes contain 6..24 events; agent campaign episodes 6..30. Hard coordination is uniform .1..8; campaign strengths use .25/.55/.8. Support overlaps rather than separate fixed positive/negative ratios.'},
      {'source':'ml_v2/src/dataset_generator.py','line':224,'finding':'Episode durations and starts are bounded inside 30d blocks. A1 uses 1..7 days, A2/A4 .25..7 days, A3 900..7200 seconds. Boundary endpoints are explicitly included. These are synthetic temporal templates, with no independent empirical calibration.'},
      {'source':'ml_v3/src/generate_v3.py','line':16,'finding':'Development Train has 600 wallets/96 agents and Validation 150/24 over the same 180d horizon, with fourfold event scaling. Similar per-agent service loads encounter a smaller global wallet pool in Validation. This is a plausible contributor to novelty saturation and its partition shift, not an isolated causal experiment.'},
      {'source':'ml_v3/src/reference_evaluator.py','line':18,'finding':'Frozen evaluator full_coverage defaults to 28d; corrected growth requires 35d for a 7d recent plus 28d baseline. Frozen A1 recent/baseline endpoint conventions also differ. Do not silently replace frozen labels using the other evaluator.'}
    ]
    audit={'method':'Static source read only; no generator imports, execution, regeneration, or holdout traversal.',
        'findings':findings,'source_hashes':{n:sha(ROOT.parent/n) for n in sorted({v['source'] for v in findings}|{'ml_v3/design/scenario_manifest.json','ml_v3/design/V3_SCENARIO_ONSET_CONTRACT.md'})},'development_cohorts':{},'episode_parameters':{},'observable_population':{}}
    extra={}
    for part,(x,y,ids) in load_matrices().items():
        m=metadata(part,ids,y); z=np.load(E/f'{part}_agent_primitives.npz')['values']; g=x[:,22]
        rows=m['rows']; a1=m['family']['A1']; groups={}
        for label in ('routine','campaign_member','hard_scenario','H7','H8'):
            mask=np.array([r['scenario_family']==label if label in ('H7','H8') else r['origin_cohort']==label for r in rows])
            available=mask&(g!=-1); high=available&(g>=1.5)
            groups[label]={'all_target_support':int(mask.sum()),'target1':int(y[mask].sum()),'A1_positive':int((mask&a1).sum()),'growth_all':summary(g[mask],-1),
                'available_growth_ge1.5':int(high.sum()),'growth_ge1.5_A1_positive':int((high&a1).sum()),'growth_ge1.5_target0':int((high&(y==0)).sum()),
                'growth_target1':summary(g[mask&(y==1)],-1),'growth_target0':summary(g[mask&(y==0)],-1)}
        audit['development_cohorts'][part]=groups
        plans=json.loads((ROOT/f'data/development/{part}/episode_plans.json').read_text(encoding='utf-8'))['episodes']
        audit['episode_parameters'][part]={f:{'episodes':len([p for p in plans if p['family']==f]),'size':summary([p['size'] for p in plans if p['family']==f]),'duration_days':summary([p['duration']/86400 for p in plans if p['family']==f]),'coordination':summary([p['coordination'] for p in plans if p['family']==f])} for f in ('A1','A2','A3','A4','H7','H8')}
        with (ROOT/f'data/development/{part}/transactions.csv').open(encoding='utf-8',newline='') as s: raw=list(csv.DictReader(s))
        audit['observable_population'][part]={'observed_wallets':len({r[k] for r in raw for k in ('sender_wallet','receiver_wallet') if r[k]}),'observed_agents':len({r['agent_id'] for r in raw if r['agent_id']}),'agent_services':sum(bool(r['agent_id']) for r in raw)}
        available=g!=-1; others=z[:,12]==1; high=g>=1.5
        extra[part]={'ratio_high_other_gates_pass':int((high&others).sum()),'ratio_high_other_gates_fail':int((high&~others).sum()),
              'available_other_gates_pass':int((available&others).sum()),'available_count':int(available.sum()),
              'denominator_floor_active':int((available&(z[:,4]<1)).sum()),'A1_mismatch_age_min':float(z[a1&~available,1].min()),'A1_mismatch_age_max':float(z[a1&~available,1].max()),
              'written_A1_without_frozen_A1':int(((z[:,11]==1)&~a1).sum()),'frozen_A1_without_written_A1':int((a1&(z[:,11]==0)).sum()),
              'agent_families_without_A1':{f:{'growth':summary(g[m['family'][f]&~a1],-1),'raw_power_vs_target0':power(y[(m['family'][f]&~a1)|(y==0)],g[(m['family'][f]&~a1)|(y==0)])} for f in ('A2','A3','A4')}}
    save('generator_audit',audit)
    save('proxy_risk',{'conclusion':'HIGH proxy concern','scope':'A1 under the frozen synthetic task; not a complete overall target oracle',
       'reason':'Growth is exactly the central relative-distinct-wallet component of A1. Other gates are often satisfied in the generated population, so eligible A1 versus relevant negatives is nearly separable. Non-A1 positives, high-growth negatives and unavailable A1 positives prevent exact overall or A1 equivalence.',
       'predicate_comparison':{
         'A1':{'shared':'agent service wallet sets; 7d recent; four preceding 7d distinct counts; denominator max(1,median); ratio component 1.5 in target','omitted':'at least 6 recent distinct, 4 new distinct, novelty >=.5; feature never thresholds itself','differences':'Feature requires first observation <=t-35d, open lower/closed upper windows and full-key prior inclusion. Frozen target requires 28d coverage, closed lower/open upper timestamp windows; same-time prior services excluded from its recent window.'},
         'A2':{'shared':'agent serviced-wallet histories and observation eligibility concept','omitted':'24h event concentration, independently pooled baseline top-two comparator, recent >=8, baseline >=20 and >=5 wallets, share>=.65 and change>=.2','differences':'Growth uses distinct-wallet ratio over 7d versus weekly medians; A2 uses event shares. Frozen A2 baseline is [t-28d,t-1d), 27d, and coverage28d, unlike corrected disjoint28d baseline/29d coverage.'},
         'A3':{'shared':'agent service histories; minimum baseline service support','omitted':'one-hour recent >=5 events, >=3 wallets, rate acceleration','differences':'Frozen A3 reuses 7d-offset ab (t-35d..t-7d) for its service denominator despite hourly recent window; corrected architecture uses preceding28d shifted by1h. Growth counts unique wallets rather than services.'},
         'A4':{'shared':'agent history and baseline availability concept','omitted':'current cash role, >=6 cash events, >=3 cash wallets, signed value/count skews, sign agreement, historical skew change','differences':'No amount or cash direction enters growth. Frozen A4 uses 27d cash comparator, >=8 cash and >=12 ab7 services plus28dcoverage; corrected architecture uses disjoint28d cash/service comparator plus29dcoverage.'}},
       'component_counts':extra,'leakage_distinction':'Decision-time observables are permitted. A near-separable target component is a synthetic task design concern, not evidence of future/private-field leakage.',
       'authority':'Frozen labels remain authoritative for reported metrics. Source/design mismatch is diagnosed, not repaired. A1 alone was independently reconstructed on every development row; A2/A3/A4 source differences are static audit findings, not full label re-evaluations.'})
    decision={'decision':'F','label':'MULTIPLE FACTORS; CONTROLLED DEVELOPMENT REDESIGN REQUIRED',
       'reason':'A1 predicate alignment, synthetic population/label conditioning, insufficient independent A1 representation, and a confirmed evaluator/contract coverage discrepancy jointly explain the evidence. Dependence persists across algorithms. Missingness is secondary.',
       'answers':[
        ['Why is growth powerful?','It measures A1\'s defining relative customer-growth component. A1 contributes most lost detections, while the other agent features encode different mechanisms.'],
        ['Is the signal behaviourally legitimate?','Yes as a causal observable customer-growth descriptor and a component of the chosen review rule. These data do not establish real-world suspiciousness or specificity.'],
        ['Does synthetic construction amplify it?','Yes: broad routine wallet sampling and episodic low-frequency customer selection make other A1 gates frequently pass. Universal predicate labeling also removes qualifying high-growth H7/H8/routine events from target0. The two mechanisms cannot be assigned causal percentages by this observational audit.'],
        ['Is it a near-oracle?','HIGH A1 proxy concern in eligible development rows; it is not a complete predicate or overall-target oracle. Available high-growth non-A1 rows and unavailable A1 positives are explicit counterexamples.'],
        ['Is missingness/history responsible?','It contributes class association, but available-only and age-stratified growth remain predictive. The denominator floor is checked separately. The frozen target\'s 28d coverage versus feature\'s 35d explains unavailable A1 positives.'],
        ['Which family contributes most?','A1. Validation loses 1634 A1 detections out of 1666 total lost positives; two A1 detections are recovered. Net A1 loss exceeds total net loss because other families have recoveries.'],
        ['Are negatives sufficiently overlapping?','Observed eligible A1 versus target0 H7/H8/routine overlap is very small, insufficient to establish robustness to legitimate customer expansion. Hard/routine all-origin cohorts do contain high growth; those satisfying A1 are relabeled positive by design. More high-growth generation alone cannot create negatives that satisfy the unchanged full predicate.'],
        ['Can model training alone solve it?','No evidence supports that as the sole remedy: all four model families concentrate on growth; removing A1 supervision greatly reduces its importance but loses agent detection. Model tuning cannot resolve target semantics or population assumptions.'],
        ['Would more features likely solve it?','The tested N3/A4 additions did not replace A1 information. A scientifically motivated A1 representation study may help, but more columns alone have no demonstrated solution and duplicate proxies could only redistribute importance.'],
        ['Does V3 need development redesign before final evaluation?','Yes: first reconcile written predicates and the actual frozen evaluator in a separately versioned development plan, then audit realistic agent acquisition/retention and near-boundary negatives under the declared task. Preserve this experiment, prohibit silent relabeling, and keep holdouts sealed. Any new target/evaluation compatibility needs explicit governance before future evaluation.']
       ],'consequence':'Recommend a bounded development-only design stage; implement no consequence in Stage 14. Keep Stage 11 reference as historical development benchmark, no promotion.',
       'limitations':['Synthetic target; no external real-agent calibration','Repeated Validation reuse','Family-removal changes class prevalence and removes overlapping labels','Event rows are dependent; no independent-row confidence intervals','Permutation importance is noncausal and sample-dependent','A1 contract discrepancy measured; no complete audit of every target family','Onset slices small and restricted to own recorded family']}
    save('decision',decision)
    print('Source, proxy and decision synthesis saved; no new fits.')

if __name__=='__main__': main()
