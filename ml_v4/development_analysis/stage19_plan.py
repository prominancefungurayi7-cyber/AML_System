"""Complete diagnostic evidence and a design-only improvement recommendation."""
from pathlib import Path
from collections import Counter
import csv,json
import numpy as np
from stage19_analysis import ROOT,OUT,FAMILIES,read,save,sha,allowed,rate

def main():
    if (OUT/'stage19_decision.json').exists():raise FileExistsError('Stage19 completed')
    errors=read('ml_v4/evidence/stage19/false_negative_analysis.json')
    verified=read('ml_v4/evidence/stage19/model_results_verification.json')
    observed=read('ml_v4/evidence/stage19/representation_observations.json')
    paired=read('ml_v4/evidence/stage19/xgboost_hgb_comparison.json')
    support=read('ml_v4/evidence/stage19/sparse_support_uncertainty.json')
    saved_diagnostics=read('ml_v4/evidence/stage18/shortcut_diagnostics.json')
    saved_importance=read('ml_v4/evidence/stage18/permutation_importance.json')
    overlap={}
    for part in ['train','validation']:
        folder=ROOT/'ml_v4/development_features/matrices'/part
        ids=[int(r['transaction_id']) for r in csv.DictReader((folder/'row_metadata.csv').open())]
        truth={r['transaction_id']:r for r in (json.loads(s) for s in allowed(part,'family_evidence.jsonl').read_text().splitlines())}
        overlap[part]={}
        for model in ['XGB','HGB']:
            prob=np.load(ROOT/f'ml_v4/development_training/artifacts/primary_{model}_{part}_probabilities.npy',allow_pickle=False)
            overlap[part][model]={}
            for family in FAMILIES:
                cohort=[(truth[i]['families'],float(p)) for i,p in zip(ids,prob) if family in truth[i]['families']]
                only=[p for fs,p in cohort if len(fs)==1]
                overlap[part][model][family]={'exclusive_family_recall':rate(sum(p>=.5 for p in only),len(only)),
                    'detected_family_combinations':dict(Counter('|'.join(fs) for fs,p in cohort if p>=.5))}
    save('family_overlap_attribution.json',{'partitions':overlap,'meaning':'Co-occurrence does not establish why a model predicted positive; exclusive-family slices expose overlap dependence without altering labels.'})
    representation={
        'S1':{'classification':'Components available, one indirectly','detail':'Although distinct amount count is absent, variation>=2 is equivalent to n*max_share>1 for positive amounts (exact-aggregate algebra). Thus its binary variation gate is recoverable from count and max share; do not call the omitted count an irreducible gap. Float64 precision remains the saved contract.'},
        'S2':{'classification':'Genuine omitted information and sparse support','detail':'Recent cluster count/share/current amount present. Exact cluster sum, baseline similar count/rate and exact S2 historical support are not generally recoverable. Current amount times count approximates but does not equal the sum under 5% tolerance. Coverage 35 alone cannot encode baseline event support.'},
        'S3':{'classification':'Genuine omitted information','detail':'Day count/hour breadth and historical daily growth present; current-day total value is not generally recoverable from the one-hour sum.'},
        'S4':{'classification':'Genuine omissions plus recoverable cross-field quantities','detail':'Current band and band count present. n(R7d)=S2 similar-count/similar-share because current always belongs to its own cluster; band share follows by dividing band count by that n. These are not necessarily missing information. Band amount variation, baseline band frequency and exact S4 baseline support remain absent.'},
        'N1':{'classification':'Genuine omitted information','detail':'Directed count, breadth and acceleration/historical marker present; recent incoming total value absent. Current amount alone is not the historical sum.'},
        'N2':{'classification':'Genuine omitted information','detail':'Directed count, breadth and acceleration/historical marker present; recent outgoing total value absent.'},
        'N3':{'classification':'Demonstrated lossy summary','detail':'All-path count and minimum length do not expose all monetary routes. Seven Validation positives have selected summaries incompatible with amount bounds; four are missed. This co-occurrence is not causal attribution of four misses.'},
        'N4':{'classification':'Conditional reconstructability; degenerate information gap','detail':'Let q=(Oprior+a)/F and r=F-Oprior. F=(a-r)/(q-1) when q!=1; when q=1, a=r and F remains unidentified by these quantities. Thus the F>=10000 gate is not guaranteed recoverable from the N4 fields. No numerical reconstruction is substituted into X.'},
        'A1':{'classification':'All compound-gate ingredients supplied','detail':'Growth, D, new count/share and historical missing marker expose all A1 components. Perfect observed recall and high growth importance are consistent with alignment, not private intent leakage by themselves.'},
        'A2':{'classification':'Genuine omitted information plus model-specific weakness','detail':'Top2 share, change and historical marker present; absolute recent service count>=8 not supplied. Both detected/missed positives have large change, so a near-change-threshold explanation is unsupported.'},
        'A3':{'classification':'Conditional count information','detail':'Recent breadth and acceleration/history marker present. Absolute count is not explicit; acceleration equals count when the denominator floor is active, but baseline count is not supplied to establish that identity universally.'},
        'A4':{'classification':'Arithmetic ingredients supplied; learning/support issue remains','detail':'Cash counts, values, distinct wallets, signed historical change and current type permit count/value skew, agreement and eligibility checks. The frozen fields support the compound rule in principle; HGB rescues 46/71 XGB Validation misses without feature changes. This cannot prove a universal algorithm advantage or identify an exact fitting cause.'}}
    save('feature_representation_limitations.json',{'families':representation,'status':'Static review plus saved-data observations; no amendment applied',
        'algebra_scope':'Exact aggregate identities; no new extracted columns, models, labels or trigger features. Jointly sufficient primitives are permitted; full-family trigger as a feature remains prohibited.',
        'uncertainty':'Absence of a named field need not imply information loss. Conversely high observed accuracy is not proof that the representation is sufficient for all permitted histories.'})
    options=[
        {'rank':1,'option':'Preserve XGBoost and complete a versioned feature-amendment design','expected_benefit':'Address demonstrable S2/S4 historical/value/variation gaps before paying for another fit; keep A4 model comparison as a separate issue.',
         'justification':'S2/S4 weak on Train and Validation; S4-only 0/12 in Validation; static irrecoverable components, not accuracy dissatisfaction alone.',
         'required_data':'Existing frozen design and authorized development diagnostics for design; later independent hand fixtures if implementation is authorized.',
         'new_dataset_required':'No for design or future re-extraction of same immutable ledger; new feature/experiment version required.',
         'refit_required':'No now; yes to assess any future approved feature version.',
         'contract_amendment':'Explicit new feature contract plus Stage16T compatibility amendment before any affected independent evaluation. Preserve v4.features.1 and Stage18.',
         'risks':'Extra direct components can make synthetic rule learning easier without improving external validity; support remains sparse; hypothesis formed on reused Validation.',
         'independent_evaluation':'Original holdouts remain quarantined. Challenge feature/schema compatibility and freeze rules must be amended before generation/access, with independent custody intact.'},
        {'rank':2,'option':'Retain current model with restricted claims and document HGB trade-off','expected_benefit':'No further fit cost; honest binary development reference and preserved comparator.',
         'justification':'Original fixed selection rule remains valid; HGB rescues A4 errors but adds false positives and loses some network detections.',
         'required_data':'Existing artifacts/predictions only.','new_dataset_required':'No.','refit_required':'No.','contract_amendment':'No to retain; separate selection decision required to switch candidate.',
         'risks':'Known S2/S4 and exclusive-family failures remain; cannot meet full-family research objective.',
         'independent_evaluation':'Does not resolve custody/support requirements; no final model promotion.'},
        {'rank':3,'option':'Targeted additional observable error review','expected_benefit':'Trace unresolved examples to representation ambiguity versus learned approximation before specifying implementation changes.',
         'justification':'187 Validation positives missed by both XGB/HGB; N3 summaries demonstrably lose some alternatives.',
         'required_data':'Existing development rows, prior observable histories, annotations and fixed predictions under a separate diagnostic authorization.',
         'new_dataset_required':'No.','refit_required':'No.','contract_amendment':'No if strictly diagnostic; any new model inputs require a versioned amendment.',
         'risks':'Further Validation reuse; cannot quantify causal improvement from an inspection; do not search threshold grids.',
         'independent_evaluation':'No challenge/holdout access; later claims need untouched independent evidence.'},
        {'rank':4,'option':'Provision custody and use the separately planned challenge evaluation','expected_benefit':'Independent sparse-family and domain evidence with fresh communities and predeclared uncertainty.',
         'justification':'Original holdout support policies failed; Stage16S/16T already require a separate estimand.',
         'required_data':'Authorized independently administered runtime, verified dual-identity access, registry, durable one-draw log and environment freeze; new challenge only after separate approval.',
         'new_dataset_required':'Separate challenge version, never regeneration of original V4.','refit_required':'No on challenge; frozen primary artifact before evaluation.',
         'contract_amendment':'Existing Stage16T if current 40 fields retained; explicit compatibility amendment if future feature contract differs.',
         'risks':'Support may still fail; enriched challenge not representative prevalence; current custody unavailable.',
         'independent_evaluation':'Cannot proceed locally under developer-controlled custody; no original seal repair or family-count leakage.'},
        {'rank':5,'option':'Versioned development population experiment only if needed','expected_benefit':'Increase opportunity and entity/episode diversity for sparse families using a scientifically justified population law.',
         'justification':'Train S2=112/S4=128 and nine objectives unmet; extra feature information alone cannot supply statistical support.',
         'required_data':'New prospective population specification, fixed opportunity law/seed policy and one retained draw, subject/cluster objectives and anti-shortcut audit.',
         'new_dataset_required':'Yes, separately named and versioned; preserve original 100k draw.','refit_required':'Yes, separately budgeted after authorization.','contract_amendment':'New population/research protocol; frozen target remains unless separately justified and approved.',
         'risks':'Unnecessary regeneration, engineered easy positives, origin-specific signatures and misleading prevalence; no support acceptance loop.',
         'independent_evaluation':'Independent future evaluation version compatible with amended population/feature task, no reuse of observed evaluation results.'},
        {'rank':6,'option':'Future preregistered model comparison and robustness audit','expected_benefit':'Test whether A4/A2 approximation differences persist under a constrained, family-aware comparison.',
         'justification':'HGB rescues 46 A4 and 16 A2 misses, while XGB uniquely detects nine N3 positives; neither dominates.',
         'required_data':'Approved frozen development representation, explicit utility trade-offs, fit budget and independent evaluation plan.',
         'new_dataset_required':'Not necessarily; new modeling experiment/version and preserved prior comparison required.',
         'refit_required':'Yes for any new model; existing saved-artifact diagnosis needs none.','contract_amendment':'Separate modeling approval must resolve Stage18 unused-slot expiration and inherited 36-fit ceiling; no automatic reset or recycling.',
         'risks':'Adaptive Validation tuning, extra fit consumption, apparent improvements on the same synthetic examples.',
         'independent_evaluation':'Future assessment must freeze model/threshold before access; no result-informed challenge fitting.'}]
    save('ranked_improvement_options.json',{'options':options,'implemented_options':[], 'decision_scope':'Recommendation only; ranking balances evidence and cost, not predicted metric gains.'})
    save('recommended_next_stage.json',{'recommendation':'Separately authorize Stage20 controlled feature-representation amendment design and compatibility review; design only, no fit/generation/extraction.',
        'first_priority':['S2 recent cluster sum and prior cluster support/rate as causal lower-level quantities','S4 band variation and prior band activity/support; avoid redundant n/share columns already derivable','A2/N1 absolute service/edge-value omissions and N3 alternative-route summary design reviewed secondarily'],
        'A4_policy':'Do not add a full A4 trigger or weaken gates; existing arithmetic primitives suffice in principle. Preserve HGB comparison as evidence of model-specific approximation.',
        'constraints':['Keep all three domains and all twelve target predicates','No private provenance, intent or complete-family trigger features','Explicit dimensionality/version amendment before any feature construction','Independent hand examples for irrecoverability/recoverability, not selected-positive templates','Document compatibility with Stage16T frozen 40-field evaluation contract','Preserve XGBoost selected and HGB comparator','No automatic additional fits; Stage18 unused slots expired','Custody/holdout restrictions unchanged'],
        'acceptance_for_next_design':['Each proposed field has observable causal formula, availability/marker policy and component disclosure','Existing algebraic redundancy assessed before increasing dimension','Demonstrated design gap separated from sparse-support limitation','Versioned preservation/compatibility and a future separately authorized fitting/evaluation plan'],
        'not_authorized_by_stage19':['training/refitting','feature construction/amendment execution','new transactions','threshold optimization','independent evaluation','application integration']})
    save('synthetic_shortcut_assessment.json',{'existing_stage18_evidence':{'permutation':saved_importance,'robustness':saved_diagnostics},
        'stage19_population_slices':'synthetic_population_slices.json','overlap':'family_overlap_attribution.json',
        'findings':['A1 perfect Validation recall and zero selected FNs carrying A1; outside-A1 recall .81318','All four selected S4 detections overlap other families, while no S4-only row is detected','N1 acceleration/count coincide in all selected N1-positive summaries; this can follow the legitimate denominator floor in a sparse baseline, not hidden leakage','Missingness-only AP .2856 versus full XGB .9860 supports some missingness signal but not sufficiency','Type/origin/role prevalence and error associations reflect conditional synthetic population construction; provenance is never an input'],
        'not_established':['No causal fraction of errors attributable to a shortcut','No proof that growth dominance is private/future leakage','No proof of real-world transport or natural-population false-positive performance','No independent external audit; developer evidence and repeatedly used Validation only'],
        'controls_preserved':['Explicit sentinel handling','No origin/ID/absolute-time inputs','No new importance runs, predictions, refits or shuffled labels in Stage19']})
    # A readable report is authored after these machine-readable design recommendations.
    print('Stage19 representation, overlap and ranked-plan evidence created; report pending.')

if __name__=='__main__':main()
