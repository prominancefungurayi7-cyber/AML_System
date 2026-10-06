"""Saved-result verification and Stage22 report. No fitting or prediction calls."""
from pathlib import Path
import hashlib,json
import numpy as np
from sklearn.metrics import average_precision_score,roc_auc_score

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'ml_v4/evidence/stage22'
ART=ROOT/'ml_v4/development_comparison/artifacts'
REPORT=ROOT/'ml_v4/reports/V4_STAGE22_CONTROLLED_COMPARISON_REPORT.md'
GRID=('A40-XGB','B44-XGB','A40-HGB','B44-HGB')
FAMILIES='S1 S2 S3 S4 N1 N2 N3 N4 A1 A2 A3 A4'.split()
def read(n):return json.loads((OUT/n).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,data):
    with (OUT/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(data,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')

def main():
    if REPORT.exists() or (OUT/'stage22_decision.json').exists():raise FileExistsError('No report overwrite')
    plan=read('frozen_experiment_plan.json')
    for name,h in plan['source_sha256'].items():assert sha(ROOT/name)==h,name
    preservation=read('preservation_verification.json')
    for name,h in preservation['after_sha256'].items():assert sha(ROOT/name)==h,name
    results={id:read(id+'_metrics.json') for id in GRID}
    pairs=read('paired_comparisons.json');importance=read('permutation_component_dependence.json');diag=read('shortcut_error_slices.json')
    budget=read('fit_budget_verification.json')
    assert budget['new_started']==budget['new_completed']==4 and budget['cumulative_started']==20
    verification={}
    for id in GRID:
        verification[id]={}
        for part in ['train','validation']:
            y=np.load(ROOT/'ml_v4/development_features/matrices'/part/'y.npy',allow_pickle=False)
            p=np.load(ART/(id+'_'+part+'_probabilities.npy'),allow_pickle=False);z=p>=.5
            tn=int(((y==0)&~z).sum());fp=int(((y==0)&z).sum());fn=int(((y==1)&~z).sum());tp=int(((y==1)&z).sum())
            computed={'confusion_matrix':[[tn,fp],[fn,tp]],'macro_f1':(2*tp/(2*tp+fp+fn)+2*tn/(2*tn+fp+fn))/2,'positive_precision':tp/(tp+fp) if tp+fp else 0,'positive_recall':tp/(tp+fn),'false_positive_rate':fp/(fp+tn),'accuracy':(tp+tn)/len(y),'balanced_accuracy':.5*(tp/(tp+fn)+tn/(tn+fp)),'roc_auc':float(roc_auc_score(y,p)),'average_precision':float(average_precision_score(y,p))}
            saved=results[id]['partitions'][part]['overall']
            for k,v in computed.items():assert v==saved[k] if k=='confusion_matrix' else abs(v-saved[k])<1e-12,(id,part,k)
            verification[id][part]={'status':'PASS','rows':len(y),'confusion':computed['confusion_matrix'],'max_float_tolerance':1e-12}
    save('independent_metric_verification.json',{'results':verification,'scope':'Separate confusion/ratio arithmetic from saved scores; sklearn AP/AUC reused. Same developer environment, not independent external review. No new model predictions.'})
    primary=['S2','S4','S2-only','S4-only']
    improves=[];anyimprove=False
    for family in ['XGB','HGB']:
        p=pairs[family]['validation']['paired']
        improvements=[p[k]['B_minus_A_rate'] for k in primary]
        anyimprove |= any(v>0 for v in improvements)
        improves.append(all(v>=0 for v in improvements) and any(p[k]['B_minus_A_rate']>0 for k in ['S2','S2-only']) and any(p[k]['B_minus_A_rate']>0 for k in ['S4','S4-only']))
    letter='A' if all(improves) else 'C' if anyimprove else 'B'
    title={'A':'EXPERIMENT COMPLETE; 44-FEATURE IMPROVEMENT SUPPORTED IN DEVELOPMENT','B':'EXPERIMENT COMPLETE; NO SUFFICIENT IMPROVEMENT','C':'EXPERIMENT INCONCLUSIVE'}[letter]
    decision=letter+' — '+title
    overall=[];families=[];domains=[];primaryrows=[];trades=[];dependence=[];outside=[];community=[]
    for id in GRID:
        r=results[id]['partitions']['validation']['overall']
        overall.append(f"| {id} | {r['macro_f1']:.6f} | {r['positive_precision']:.6f} | {r['positive_recall']:.6f} | {r['false_positive_rate']:.6f} | {r['accuracy']:.6f} | {r['balanced_accuracy']:.6f} | {r['roc_auc']:.6f} | {r['average_precision']:.6f} | {r['confusion_matrix']} |")
        imp=importance[id]
        dependence.append(f"| {id} | {imp['growth_absolute_mass_share']:.3%} | {imp['four_added_absolute_mass_share']:.3%} | {imp['baseline_sample_ap']:.6f} |")
        x=diag[id]['validation']['missingness_A1_slices']['outside_A1']['recall']
        outside.append(f"| {id} | {x['numerator']}/{x['denominator']} | {x['rate']:.6f} |")
        for unit,r in diag[id]['validation']['communities'].items():community.append(f"| {id} | {unit} | {r['FN']}/{r['positive_support']} | {r['FP']}/{r['negative_support']} |")
    for f in FAMILIES:
        cells=[]
        for id in GRID:
            r=results[id]['partitions']['validation']['slices']['families'][f]
            cells.append(f"{r['numerator']}/{r['denominator']} ({r['rate']:.4f})")
        families.append('| '+f+' | '+' | '.join(cells)+' |')
    for d in ['structuring','network','agent']:
        cells=[]
        for id in GRID:
            r=results[id]['partitions']['validation']['slices']['domains'][d]
            cells.append(f"{r['numerator']}/{r['denominator']} ({r['rate']:.4f})")
        domains.append('| '+d+' | '+' | '.join(cells)+' |')
    for alg in ['XGB','HGB']:
        for part in ['train','validation']:
            p=pairs[alg][part]['paired']
            for f in primary:
                r=p[f]
                primaryrows.append(f"| {alg} | {part} | {f} | {r['A_positive']}/{r['support']} | {r['B_positive']}/{r['support']} | {r['B_minus_A_rate']:+.6f} | {r['B_detects_A_misses']} | {r['A_detects_B_misses']} |")
        v=pairs[alg]['validation'];pos=v['paired']['all_positive'];neg=v['paired']['all_negative']
        trades.append(f"{alg}: B detects {pos['B_detects_A_misses']} positives missed by A and loses {pos['A_detects_B_misses']} A detections. Among target0 rows, B adds {neg['B_detects_A_misses']} false positives and removes {neg['A_detects_B_misses']}. Net Macro F1 {v['overall_B_minus_A']['macro_f1']:+.6f}; recall {v['overall_B_minus_A']['positive_recall']:+.6f}; FPR {v['overall_B_minus_A']['false_positive_rate']:+.6f}.")
    warnings={id:results[id]['warnings'] for id in GRID}
    saved_repro={id:{part:results[id]['partitions'][part]['Stage18_reproduction'] for part in ['train','validation']} for id in ['A40-XGB','A40-HGB']}
    recommendation='Preserve all four experimental artifacts and the historical selected XGBoost/HGB roles. Review the observed information/accuracy tradeoffs and support limitations; any next study, candidate-selection rule, challenge amendment or evaluation needs separate authorization. No additional fitting, threshold search or promotion follows.'
    save('scientific_limitations.json',{'validation':'Exploratory; inspected in prior stages and used to form feature hypotheses. No independent confirmation, significance or generalization claim.','nine_support_shortfalls':['S1','S2','S4','N1','N3','N4','A2','A3','A4'],'dependence':'Three Validation communities; subjects/episodes not independent rows; Wilson intervals in inherited slice utility are descriptive independence-based bounds only','representation':'New fields are disclosed individual S2/S4 components. Better deterministic policy reproduction is not proof of real laundering detection.','compatibility':'Stage16T still40; explicit amendment/approval and independent custody required before44 evaluation. Original seals remain quarantined with public supportFAIL facts.','preservation_gap':'Stage16V incomplete broader Stage15A snapshot retained','promotion':False})
    save('recommendation.json',{'decision':decision,'interpretation':plan['decision_interpretation'],'recommendation':recommendation,'selected_unchanged':'primary_XGB','comparator_unchanged':'primary_HGB','new_final_model_selected':False,'next_stage_authorized':False})
    save('all_family_domain_performance.json',{id:{part:results[id]['partitions'][part]['slices'] for part in ['train','validation']} for id in GRID})
    # Preserve full per-unit and per-subject error denominators in machine-readable
    # evidence; compact report displays community counts and primary contrasts.
    subject_summary={}
    for id in GRID:
        subjects=diag[id]['validation']['wallet_subjects']
        subject_summary[id]={'wallet_subjects_with_FN':sum(r['FN']>0 for r in subjects.values()),'wallet_subjects_with_FP':sum(r['FP']>0 for r in subjects.values()),'top5_FN':sorted(([k,r] for k,r in subjects.items() if r['FN']),key=lambda p:(-p[1]['FN'],p[0]))[:5],'top5_FP':sorted(([k,r] for k,r in subjects.items() if r['FP']),key=lambda p:(-p[1]['FP'],p[0]))[:5]}
    save('subject_error_summary.json',subject_summary)
    subjectlines='\n'.join(f"- {id}: FN on {s['wallet_subjects_with_FN']} wallet subjects; FP on {s['wallet_subjects_with_FP']}." for id,s in subject_summary.items())
    missinglines=[]
    for id in GRID:
        for key in ['new_baseline_missing','new_baseline_observed']:
            r=diag[id]['validation']['missingness_A1_slices'][key];rec=r['recall'];fp=r['fpr'];prev=r['prevalence']
            missinglines.append(f"| {id} | {key} | {prev['numerator']}/{prev['denominator']} | {rec['numerator']}/{rec['denominator']} | {fp['numerator']}/{fp['denominator']} |")
    resources=read('runtime_resource_usage.json')
    text=f'''# MODEL V4 — STAGE 22 CONTROLLED 40-VERSUS-44 FEATURE EXPERIMENT

**{decision}**

Exactly four new model-fit attempts completed. This compares two frozen configurations under original40 and experimental44 representations on identical development rows. Results are **exploratory**: Validation already informed the feature-design hypotheses. No model is promoted or selected as a new final model; historical `primary_XGB` remains selected and HGB remains its comparator.

## 1. Authority, inputs and budget

Named Stage15/15A,16R–16V,17–21 contracts, reports/evidence and artifact hashes were verified before fitting. Stage21's retained reporting-only correction was checked through its final manifest; no extractor or matrix ambiguity remains. All75000 rows have original40 raw-column byte parity, identical IDs/order/metadata and unchanged binary labels. Train has60000 rows(47770 target0,12230 target1); Validation15000(11970 target0,3030 target1). No new transactions, sampling, label changes or sealed directory access occurred. [Input verification](../evidence/stage22/input_verification.json).

The explicit Stage22 request prospectively authorizes four attempts, cumulative maximum20 under the inherited36 ceiling. Stage18's16-attempt ledger remains unchanged and its20 expired slots are not generally reopened. New ordinals1..4 link to cumulative17..20; all four STARTED and COMPLETE records were durably appended, no FAILED records. **Remaining authorized attempts:0.** No retry or replacement was used. [Authorization](../evidence/stage22/fit_authorization.json), [new ledger](../evidence/stage22/fit_ledger.jsonl), [budget verification](../evidence/stage22/fit_budget_verification.json).

## 2. Frozen configurations and preprocessing

Execution order: A40-XGB, B44-XGB, A40-HGB, B44-HGB. Exact Stage20 dictionaries, Python/NumPy/sklearn/XGBoost versions, source hashes, fixed diagnostics and descriptive decision interpretation were recorded before the first attempt in [frozen plan](../evidence/stage22/frozen_experiment_plan.json).

XGB uses200trees, depth5, learning rate.07, minchild5; HGB200iterations,31leaves, learning rate.07, minimumleaf20. All other parameters match Stage20 and normalized estimator `get_params()` exactly. Seed2026092915; no early stopping, new weights, resampling, calibration, threshold search or rule overrides. The Stage18 serializer stored default XGB missing NaN as JSONnull; only that parameter is restored toNaN, with remaining nulls retained asNone. This representation interpretation was frozen before fitting.

Each of the four pipelines independently fits the unchanged Stage18 preprocessing class on Train only: exact per-field sentinel→NaN, median imputation(empty0, no indicators), standard scaling and fixed type vocabulary(wallet_to_wallet,cash_in,cash_out). Valid−1 N4 residual,−1 concentration change and−2 cash change are preserved. Only the two new baseline fields add−1 missing conversions; valid0 stays observed. Dimensions are42 for A and46 for B. No fitted transforms are shared, no Validation `.fit` or Train+Validation refit. Classification is **score>=0.50** throughout. [Preflight](../evidence/stage22/preprocessing_preflight.json), [fitted-state audit](../evidence/stage22/preprocessing_audit.json).

## 3. Primary paired contrasts

Positive numerators count union-positive predictions on the indicated family; “only” excludes other family flags for diagnosis without changing primary evaluation rows. Differences are B44−A40 recall on identical supports. Recovery/loss columns are paired event counts.

| Algorithm | Partition | Slice | A TP/support | B TP/support | Recall delta | B recovers A miss | B loses A hit |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(primaryrows)}

These raw counts are the primary diagnostic contrasts. No row-independence p-value, post-hoc threshold or independent confirmation is claimed. Train differences describe fitted approximation; Validation differences remain exploratory. [Paired comparisons](../evidence/stage22/paired_comparisons.json).

## 4. Validation union metrics and tradeoffs

| Model | Macro F1 | Precision | Recall | FPR | Accuracy | Balanced accuracy | ROC-AUC | AP | [[TN,FP],[FN,TP]] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
{chr(10).join(overall)}

{chr(10).join(trades)}

All Train/Validation metric files retain confusion denominators, threshold, AP definition through sklearn average_precision_score, undefined conventions and fixed-score summaries. AP is not trapezoidal PR area. Separate saved-score confusion/ratio calculations and AP/AUC checks matched every result within1e−12; no new predictions were required for that verification. [Verification](../evidence/stage22/independent_metric_verification.json).

## 5. All families and domains

| Family | A40-XGB | B44-XGB | A40-HGB | B44-HGB |
| --- | --- | --- | --- | --- |
{chr(10).join(families)}

| Domain | A40-XGB | B44-XGB | A40-HGB | B44-HGB |
| --- | --- | --- | --- | --- |
{chr(10).join(domains)}

Families/domains overlap; do not sum their supports or errors. Domain recall is union prediction among domain-bearing positives; there is no separate domain output or domain-specific FPR. Domain-only, multi-domain and H1–H8/background/pre-onset target0 FPR with exact supports are in [all-family/domain evidence](../evidence/stage22/all_family_domain_performance.json). Full B−A family and domain contrasts are in paired evidence; no difficult family was removed.

### Performance outside A1

| Model | TP/support outside A1 | Recall |
| --- | ---: | ---: |
{chr(10).join(outside)}

This separates the large A1-positive population from remaining union positives. It does not create another classifier or alter labels.

## 6. Shortcut dependence and missingness

No extra fitted diagnostic model ran. The preregistered no-fit permutation analysis reused the exact Stage18 uniform3000 Validation indices and three paired semantic-field permutations. Each AP baseline uses that same sample; type is permuted jointly before its one-hot transform. Signed mean AP drops and repeatSD are saved for every field. Absolute shares are descriptive normalization, not causal contributions.

| Model | Growth absolute AP-drop mass | Four added fields mass | Same-sample baseline AP |
| --- | ---: | ---: | ---: |
{chr(10).join(dependence)}

The sample contains {importance['A40-XGB']['sample_family_support']['S2']} S2 and {importance['A40-XGB']['sample_family_support']['S4']} S4 positives. Sparse family support, correlated features and off-manifold permutations limit interpretation; added fields change the normalization denominator. A smaller growth share alone is not evidence of less shortcut reliance. Full signed drops/group shares: [component dependence](../evidence/stage22/permutation_component_dependence.json).

| Model | History slice | Target1 / rows | TP / positives | FP / negatives |
| --- | --- | ---: | ---: | ---: |
{chr(10).join(missinglines)}

Both new baseline fields share their historical availability marker. These associations do not prove missingness caused predictions. The four additions explicitly reproduce **individual S2/S4 target components**; jointly better rule approximation does not establish real laundering detection. Identity, origin and family labels remain diagnostic-only and outside X. No target evaluator, private provenance or future fields are passed to `.fit`/`.predict_proba`. [Error and shortcut slices](../evidence/stage22/shortcut_error_slices.json) include type, origin, agents, subjects and episode/day groups for both partitions.

## 7. Community and subject concentration

| Model | Validation community | FN / positives | FP / negatives |
| --- | --- | ---: | ---: |
{chr(10).join(community)}

{subjectlines}

Per-subject support, recall/FPR and leading FN/FP groups are retained in [subject summary](../evidence/stage22/subject_error_summary.json) and full slice evidence. Wallet subject=sender forW2W/cashserviced; N1 family uses receiver, agent families currentagent. NO_AGENT is an absence category, not an entity. Episode/day grouping and three communities describe dependence; they do not provide a reliable independent-population sample. Any inherited Wilson bounds are descriptive independence-based intervals only, not significance evidence.

## 8. Reproducibility, runtime and artifacts

40-field baseline reproduction of Stage18 saved probabilities: `{json.dumps(saved_repro,sort_keys=True)}`. This checks controlled parity without loading or modifying historical fitted models. Each newly saved experimental pipeline was reloaded locally and its first100 Validation probabilities matched exactly. This checks serialization, not another fit or independent evaluation.

Fit seconds: `{json.dumps(resources['fit_seconds'],sort_keys=True)}`. Permutation seconds:{resources['permutation_seconds']:.3f}. Peak process working set:{resources['peak_process_working_set_bytes']/1024**2:.1f}MiB, including all retained models/data; not per-model marginal memory. Sequential, one worker. Warnings by model: `{json.dumps(warnings,sort_keys=True)}`. [Runtime](../evidence/stage22/runtime_resource_usage.json).

New models and saved probabilities are under `ml_v4/development_comparison/artifacts/`, explicitly EXPERIMENTAL. Reload requires the frozen runtime and `ml_v4/development_training` on the module search path for the unchanged `preprocessing.FrozenPreprocessor` class. Load only trusted hash-verified local joblib artifacts. Each candidate has its own preprocessing; historical artifacts remain untouched.

## 9. Scientific limits, preservation and recommendation

S1/S2/S4/N1/N3/N4/A2/A3/A4 still miss original support objectives. The feature change creates no positives or independent subjects. Validation already drove the hypotheses and cannot supply independent confirmation. Stronger deterministic policy reproduction is narrower than actual AML detection; no real-world generalization or operational effectiveness is established.

Stage16T remains a40-field protocol, incompatible by default with44. Independent custody remains unavailable, original Final/Independent remain SEALED_QUARANTINED with public supportFAIL facts, and no private counts were obtained. Any affected independent evaluation requires a separate compatibility amendment and approvals; no challenge is generated here. No Flask/MySQL/dashboard changes occurred. Stage16V's incomplete broader Stage15A snapshot is retained without weakening expectations.

**{preservation['protected_count']} named protected files** match before/after hashes, including both matrix versions, labels/data, Stage18 artifacts and ledger, original predicates, V1 and V3 integration. Sealed bytes are unread and excluded from the claim. [Preservation](../evidence/stage22/preservation_verification.json).

{recommendation}

The decision follows the descriptive interpretation frozen before fitting. A, if returned, applies to consistent S2/S4 primary development contrasts and does not assert every metric improved, full-family adequacy or a new selected model. B indicates no primary gains; mixed directions are C. All tradeoffs remain reported. [Recommendation](../evidence/stage22/recommendation.json), [limitations](../evidence/stage22/scientific_limitations.json).

## 10. Final decision

**{decision}**

Four authorized attempts are consumed. No further fit, threshold optimization, independent evaluation, challenge generation, integration, promotion or automatic Stage23 is authorized.

V4 STAGE 22 COMPLETE — WAITING FOR APPROVAL.
'''
    with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
    artifacts=[REPORT,Path(__file__),Path(__file__).with_name('run_stage22.py')]+list(OUT.iterdir())+list(ART.iterdir())
    hashes={p.relative_to(ROOT).as_posix():sha(p) for p in artifacts if p.is_file()}
    save('stage22_decision.json',{'decision':decision,'interpretation':plan['decision_interpretation'],'four_fits_completed':True,'new_attempts':4,'cumulative_attempts':20,'remaining_authorized_attempts':0,'new_final_model_selected':False,'selected_unchanged':'primary_XGB','comparator_unchanged':'primary_HGB','independent_validation':False,'promotion':False,'sealed_access':False,'artifact_sha256':hashes,'protected_count':preservation['protected_count']})
    print(decision)
    print(f'Report and {len(hashes)} output hashes complete; no new fits in reporting.')

if __name__=='__main__':main()
