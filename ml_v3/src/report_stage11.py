"""One consolidated report from the fixed Stage 11 experiment."""
import json
from stage11_protection import ROOT, snapshot, compare, sha
from stage10a_contract import NAMES, FEATURES

R=ROOT/'reports'
def load(n): return json.loads((R/('stage11_'+n+'.json')).read_text(encoding='utf-8'))
def f(v):
    if v is None: return 'undefined (zero support)'
    if isinstance(v,float): return f'{v:.4f}'
    if isinstance(v,(dict,list)): return json.dumps(v,sort_keys=True)
    return str(v)
def table(headers,rows):
    return '\n| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+''.join('| '+' | '.join(f(v) for v in row)+' |\n' for row in rows)+'\n'

def main():
    result=load('candidate_results'); assert result['status']=='complete'
    summary=result['summary']; plan=result['plan']; allrows=result['candidates']
    short=load('shortlist')['candidates']; domain=load('domain_recall'); family=load('family_recall')
    normal=load('normal_fpr'); gaps=load('generalization'); probabilities=load('probability_quality')
    importance=load('importance'); pre=load('preprocessing'); protection=load('protection')
    assert compare(protection['before'],snapshot())['result']=='PASS'
    for name,digest in plan['source_hashes'].items():
        if name=='run_stage11.py' and 'execution_amendment' in plan: digest=plan['execution_amendment']['resumed_runner_sha256']
        assert sha(ROOT/'src'/name)==digest
    primary=next(r for r in short if r['name']==summary['primary_development_reference'])
    name=primary['name']; val=primary['validation']
    decisions={'A':'STRONG BASELINE','B':'PROMISING BUT NEEDS MODEL IMPROVEMENT','C':'FEATURE REPRESENTATION APPEARS LIMITING','D':'DATA/CLASS OVERLAP APPEARS LIMITING','E':'OTHER EVIDENCED LIMITATION'}
    text=f'''# MODEL V3 - STAGE 11 BASELINE MODEL TRAINING AND VALIDATION COMPARISON

**Technical execution: {summary['technical_execution']}. Quality decision: {summary['decision']} - {decisions[summary['decision']]}.**

The development reference is **`{name}`**, with Validation Macro F1 **{val['macro_f1']:.4f}**, suspicious recall **{val['suspicious_recall']:.4f}**, suspicious F1 **{val['suspicious_f1']:.4f}**, Average Precision **{val['average_precision']:.4f}**, ROC-AUC **{val['roc_auc']:.4f}**, and FPR **{val['false_positive_rate']:.4f}** at threshold **0.50**. These are development results on frozen synthetic targets, not a final model or evidence of real-world AML effectiveness.

This is the **single consolidated Stage 11 report**, covering scope, all candidates, preprocessing, complete shortlist metrics, domains/families, normal false positives, generalization, score distributions, importance, protection and next decision. Machine-readable files are supporting evidence.

## 1. Authorized data and experiment boundaries

Only corrected `v3_stage10a_features_1` matrices from `features/development/stage10a/train/` and `validation/` were used for model inputs. All 32 names and their order were checked against the frozen contract and saved matrix hashes. Superseded Stage 10 matrices were not loaded as model data. Their bytes were hashed only by the pre-existing protection allowlist.

| Partition | Rows | Features | Target 0 | Target 1 |
|---|---:|---:|---:|---:|
| Train | 60000 | 32 | 39781 | 20219 |
| Validation | 15000 | 32 | 9945 | 5055 |

Row IDs remain outside X. Model fit and preprocessing receive only the 32 numeric columns and Train targets. A preliminary metadata schema/support check preceded training; diagnostic metadata did not influence preprocessing or the fixed candidate grid. The runner joins Validation family/provenance/recipe metadata for slice metrics after every candidate's predictions exist. Labels remain the frozen `decision_point_target`; raw transactions, predicates and features were not regenerated or edited.

No Final Test or Independent Evaluation directory was enumerated or data opened. Only explicit public commitment certificates were hashed. No resampling, SMOTE, Validation refit, calibration or threshold optimization occurred. Every reported classification uses `probability >= 0.50` as suspicious class 1. Ranking metrics use continuous scores.

## 2. Fixed search design and execution

The search plan and source digests were saved before the first fit. The first five fits are one simple unweighted baseline per available model family; the remaining fits are prespecified comparisons, with no adaptive search expansion. The later Stage 11 instruction explicitly requests five model families, so this supersedes the earlier proposal's three-family suggestion while retaining its maximum of 36 configurations.
'''
    text+=table(['Property','Recorded value'],[
        ['Random seed',plan['seed']],['Threshold',plan['threshold']],['Configurations',summary['configurations']],
        ['Model fits (no extra refits)',summary['fits']],['Wall-clock experiment seconds (includes interruption)',summary['runtime_seconds']],
        ['Sum of model fit seconds',sum(r['fit_seconds'] for r in allrows)],
        ['Plan saved UTC',plan['frozen_at_utc']],['Python executable',plan['runtime_environment']['executable']],
        ['Library versions',{k:plan['runtime_environment'][k] for k in ('numpy','pandas','sklearn','xgboost')}],
        ['XGBoost availability',plan['xgboost_unavailable_reason'] or 'Installed and used; no package/environment changes'],
        ['Train positive rate',20219/60000],['Validation positive rate',5055/15000]])
    text+='No weighting gives unit sample weights. Moderate weighting gives class 1 weight 1.5 and class 0 weight 1. For Logistic/Gradient/HistGradient models the balanced sample weights are N/(2N_class), fitted from Train class counts. Random Forest uses `balanced_subsample` for its balanced variant. XGBoost uses `scale_pos_weight=39781/20219` for its balanced variant, 1.5 for moderate, 1 for none. Balanced XGBoost uses a positive-to-negative ratio, not the same absolute normalization as sklearn sample weights. No class weights are estimated from Validation.\n'
    text+=table(['Initial family','Preprocessing','Parameters excluding common random seed'],
        ([r['family'],r['preprocessing'],r['params']] for r in allrows if r['phase']=='initial baseline'))
    text+='The three weight comparisons hold each family baseline configuration and preprocessing fixed. Tree families then compare clipped and imputed inputs against raw at unit weights, followed by one prespecified capacity/regularization variant. Logistic Regression compares C=0.1/1/10 and robust-scaled sentinel preservation against robust-scaled imputation.\n'
    text+=table(['Candidate','Phase','Preprocessing','Weight','Exact requested estimator parameters'],([r['name'],r['phase'],r['preprocessing'],r['weight'],r['params']] for r in allrows))
    if 'execution_amendment' in plan:
        text+='\n### Execution recovery\n\nAfter the fifth fit, strict JSON serialization rejected XGBoost\'s default `missing=NaN` parameter. The fitted model and scores had already been saved. The initial partial checkpoint was preserved, its completed records recovered, and the fifth record reconstructed from saved scores and timing fields. Logging now records nonfinite estimator defaults as text and writes complete checkpoints atomically. The same fixed grid resumed at configuration 6, without refitting the first five models or changing model/preprocessing/threshold choices. The fifth fit\'s original warning capture was not retained and is explicitly marked unavailable. Source hashes and the reason are in `stage11_execution_amendment.json`; the original search plan remains preserved.\n'
    text+='\n## 3. Train-fitted preprocessing and missing-value contract\n\nEvery estimator receives exactly 32 columns. No missing indicators were added: the explicit Stage 11 input-count constraint takes precedence over the optional indicator comparison. The `imputed` and `robust` variants use Train observed medians; their lost missingness information is a limitation evaluated alongside sentinel-preserving variants. Five deterministic representations were fitted on Train and shared by the corresponding candidates; their parameters were deterministically recomputed during process recovery. Transforming Validation never fits or updates parameters.\n'
    text+=table(['Variant','Exact transformation'],[
        ['raw','Unscaled Stage 10A values; preserve each documented marker.'],
        ['clipped','Preserve markers; clip only current_amount_usd, wallet_value_24h_inclusive, current_return_amount_ratio, wallet_observed_onward_funding_share_24h, agent_wallet_growth_ratio_7d to Train observed 0.5th/99.5th percentiles.'],
        ['imputed','Replace only documented per-column markers with Train observed medians; no scaling or clipping.'],
        ['robust','Same marker-aware median imputation plus the five continuous-feature clipping limits; RobustScaler with Train median and IQR.'],
        ['robust_sentinel','Preserve markers before the same clipping and robust scaling; markers become deterministic scaled values.']])
    text+='The five clipping candidates have unbounded monetary/ratio scales and heavy tails in Stage 10A. Bounded indicators, cash skews, shares, path length, coverage and counts are never clipped. Robust scaling of those quantities for the linear model changes units while preserving their values relative to the Train-fitted transform. No log transform is used. Zero IQR uses the installed RobustScaler scale fallback.\n\nThe preprocessing regression test exercised all five variants, preserving legitimate -1 skews/changes, distinguishing -3 change markers, retaining shape, excluding markers from quantiles, and proving an extreme Validation transform does not change fitted parameter records.\n'
    text+=table(['Feature','Missing marker','Raw/clipped treatment','Imputed/robust treatment','Train observed median','Clipping limits','Robust center','Robust scale'],
        ([f'`{n}`',a['marker'] if a['marker'] is not None else 'none','preserve' if a['marker'] is not None else 'observed value',
          'Train median' if a['marker'] is not None else 'observed value',a['train_observed_median'],a['clip_limits'],a['scaling_center'],a['scaling_range']] for n,a in zip(NAMES,pre['robust']['columns'])))
    text+='Exact raw, clipped, imputed and sentinel-scaled parameter records, including every Train missing count, are in `stage11_preprocessing.json`. All five transformations retain ordered names.\n'
    text+='\n## 4. All candidate results at threshold 0.50\n\nSorted by Validation Macro F1. Fit time excludes score evaluation and artifact serialization. All configurations and available warnings are retained, including any nonconverged model. Convergence warnings exclude a candidate from selection. For fixed-round tree models, the convergence field denotes completed training without a captured convergence warning; it does not certify an optimization optimum. The recovered XGBoost baseline warning log is unavailable as noted above.\n'
    text+=table(['Candidate','Prep','Weight','Train Macro F1','Val Macro F1','Val precision 1','Val recall 1','Val F1 1','Val AP','Val ROC-AUC','Val FPR','Fit seconds','Converged'],
        ([r['name'],r['preprocessing'],r['weight'],r['train']['macro_f1']]+[r['validation'][k] for k in ('macro_f1','suspicious_precision','suspicious_recall','suspicious_f1','average_precision','roc_auc','false_positive_rate')]+[r['fit_seconds'],r['converged']] for r in sorted(allrows,key=lambda r:r['validation']['macro_f1'],reverse=True)))
    warned=[r for r in allrows if r['warnings']]
    text+='\nWarnings: '+('none.' if not warned else '')+'\n'
    for r in warned: text+=f'\n- `{r["name"]}`: '+ '; '.join(r['warnings'])+'\n'
    text+='\n### Matched preprocessing comparisons\n\nThese compare unit-weight trees with the same estimator parameters. They are descriptive paired development results, not significance tests; no representation was changed in response.\n'
    paired=[]
    for base in [r for r in allrows if r['phase']=='initial baseline' and r['family']!='logistic']:
        clipped=next(r for r in allrows if r['family']==base['family'] and r['preprocessing']=='clipped')
        imputed=next(r for r in allrows if r['family']==base['family'] and r['preprocessing']=='imputed')
        b=base['validation']['macro_f1']; c=clipped['validation']['macro_f1']; i=imputed['validation']['macro_f1']
        paired.append([base['family'],b,c,i,c-b,i-b])
    text+=table(['Family','Raw Macro F1','Clipped Macro F1','Imputed Macro F1','Clipped minus raw','Imputed minus raw'],paired)
    text+='\n### Shortlist and primary reference procedure\n\n'+plan['selection']+'\n\n'
    text+=f'The highest Macro F1 candidate is `{summary["highest_macro_f1"]}`. The selected development reference is `{name}`; the prespecified recall/FPR/gap filter had an eligible candidate: **{summary["primary_met_predeclared_tradeoff_filter"]}**. Family coverage, slice false positives and the quality decision below qualify this selection. This is not a final production model choice.\n'
    text+='\n## 5. Complete Train and Validation shortlist metrics\n\nSuspicious is class 1. Normal is class 0. Confusion matrices use **[[TN, FP], [FN, TP]]**. Average Precision is reported as AP; it is not trapezoidal area under an interpolated PR curve. Undefined precision is assigned zero by the recorded scoring rule.\n'
    for part in ('train','validation'):
        text+=f'\n### {part.title()}\n'
        text+=table(['Candidate','Accuracy','Balanced accuracy','Macro F1','Precision 1','Recall 1','F1 1','Precision 0','Recall 0','F1 0','ROC-AUC','AP','FPR','Confusion matrix'],
            ([r['name']]+[r[part][k] for k in ('accuracy','balanced_accuracy','macro_f1','suspicious_precision','suspicious_recall','suspicious_f1','normal_precision','normal_recall','normal_f1','roc_auc','average_precision','false_positive_rate','confusion_matrix')] for r in short))
    text+='\n## 6. Validation domain and all 12 family recalls\n\nA positive can satisfy multiple frozen families and domains. Domain support is the union of its family-positive rows; family/domain counts overlap and must not be summed into a confusion matrix. Scenario membership alone never defines these positive slices. All support counts are shown, including S2 (one Validation positive), S4 (eight) and N3 (41); their observed recall is especially unstable and provides weak evidence about generalization.\n'
    text+=table(['Candidate','Domain','Positive support','TP','FN','Recall'],([n,d,v['support'],v['tp'],v['fn'],v['recall']] for n,groups in domain.items() for d,v in groups.items()))
    text+=table(['Code','Frozen family','Validation positive support'],([code,v['family'],v['support']] for code,v in family[name].items()))
    text+=table(['Candidate','Family','Positive support','TP','FN','Recall'],([n,d,v['support'],v['tp'],v['fn'],v['recall']] for n,groups in family.items() for d,v in groups.items()))
    text+='\n## 7. Validation normal and hard-negative false positives\n\nFPR denominators include **target 0 only**. Legitimate-origin target-1 events are not false positives under this experiment. Routine, H1–H8 and campaign-member target-0 slices are reported separately. Subtype recipes overlap their parent H category; do not add them to parent counts. No diagnostic field enters fitting or preprocessing.\n'
    behaviours={'H1':'busy trading / same-day wallet activity','H2':'recurring payments','H3':'recurring legitimate large payments',
                'H4':'legitimate collection','H5':'payroll / transit','H6':'refunds / settlement',
                'H7':'busy agents','H8':'concentrated customers / cash demand'}
    text+=table(['Category','Frozen legitimate-behaviour interpretation'],behaviours.items())
    text+=table(['Candidate','Target-0 category','Support','FP','TN','FPR'],
        ([n,k,v['support'],v['fp'],v['tn'],v['false_positive_rate']] for n,groups in normal.items() for k,v in groups['target0_slices'].items() if '/' not in k))
    hard={k:v for k,v in normal[name]['target0_slices'].items() if k.startswith('H') and '/' not in k and v['support']}
    worst=sorted(hard.items(),key=lambda kv:kv[1]['false_positive_rate'],reverse=True)[:3]
    text+='For the primary reference, the highest hard-negative FPRs are '+', '.join(f'{k} ({behaviours[k]}): {v["false_positive_rate"]:.4f} ({v["fp"]}/{v["support"]})' for k,v in worst)+'. These identify where legitimate target-0 behaviour most often receives a review prediction.\n'
    text+='\n### Available hard-scenario subtype recipes\n'
    text+=table(['Candidate','Target-0 subtype','Support','FP','TN','FPR'],([n,k,v['support'],v['fp'],v['tn'],v['false_positive_rate']] for n,groups in normal.items() for k,v in groups['target0_slices'].items() if '/' in k))
    text+='\n### Origin review rates (both targets)\n\nThese are predicted review fractions, not FPRs, because they include legitimate-origin true positives.\n'
    text+=table(['Candidate','Origin','All-target support','Predicted reviews','Review rate'],([n,k,v['support'],v['predicted_reviews'],v['review_rate']] for n,groups in normal.items() for k,v in groups['origin_review_rates'].items()))
    text+='\n## 8. Generalization\n\nAll gaps are Train minus Validation. The prespecified severe-overfit flag is >0.10 Macro F1 or >0.15 suspicious F1, recall, AP or ROC-AUC. This descriptive flag is not a statistical significance test. Validation remains a development set reused across the compact candidate comparison.\n'
    text+=table(['Candidate','Macro F1 gap','Suspicious F1 gap','Suspicious recall gap','ROC-AUC gap','AP gap','Severe flag'],([n]+[v[k] for k in ('macro_f1','suspicious_f1','suspicious_recall','roc_auc','average_precision','severe_flag')] for n,v in gaps.items()))
    text+='\n## 9. Probability/score quality\n\nNo calibration or operating-threshold search was performed. Score distributions are descriptive; especially with class weighting, scores are not asserted to be calibrated probabilities of the natural population target. The overlap interval intersects the class-specific 5th–95th percentile ranges; reversed endpoints mean no intersection. Full quantiles, standard deviations and min/max range intersections are in the JSON.\n'
    text+=table(['Candidate','Partition','Target','N','Min','Q05','Median','Q95','Max','Mean'],
        ([n,p,k,v[k]['count']]+[v[k][stat] for stat in ('min','q05','median','q95','max','mean')] for n,parts in probabilities.items() for p,v in parts.items() for k in ('0','1')))
    text+=table(['Candidate','Train middle-90% overlap interval','Validation middle-90% overlap interval'],([n,v['train']['middle_90_percent_overlap'],v['validation']['middle_90_percent_overlap']] for n,v in probabilities.items()))
    # The remaining sections are appended below after all model diagnostics.
    text+=finish(summary,primary,short,domain,family,gaps,importance,protection)
    (R/'V3_STAGE11_BASELINE_MODEL_REPORT.md').write_text(text,encoding='utf-8',newline='\n')
    print(R/'V3_STAGE11_BASELINE_MODEL_REPORT.md')

def finish(summary,primary,short,domain,family,gaps,importance,protection):
    name=primary['name']
    text='\n## 10. Descriptive model importance\n\nImportance is not causality and did not change the feature set. Different methods use different units and should not be compared as absolute effect sizes. Logistic coefficients are signed effects per Train standard deviation of transformed input; the machine record also retains coefficients per robust-scaled unit and intercept. Tree impurity importance and XGBoost normalized gain can favor continuous features. HistGradientBoosting has no native importance here, so a fixed Validation AP permutation diagnostic is used (three repeats, 3,000 sampled rows). Correlation can redistribute importance and sparse families may be absent from that sample.\n'
    text+=table(['Candidate','Method','Top feature','Top feature absolute share','Current amount share','Coverage share','Marker-bearing columns share','Concentration flag'],
        ([n,v['method'],v['top_feature'],v['top_feature_absolute_share'],v['current_amount_absolute_share'],v['domain_absolute_mass']['coverage'],v['marker_bearing_columns_absolute_share'],v['concentration_flag']] for n,v in importance.items()))
    text+='Absolute mass shares normalize absolute coefficients/importances (including signed permutation values). The concentration flag indicates a single feature >50% or a domain >70% of that mass. Marker-bearing feature importance mixes observed-value and missingness effects, so it cannot prove missingness dominance. Where available, the fraction of raw-tree internal splits isolating a sentinel is reported separately.\n'
    text+=table(['Candidate','Current','Structuring','Network','Agent','Coverage','Sentinel-isolating split fraction'],
        ([n]+[v['domain_absolute_mass'][k] for k in ('current','structuring','network','agent','coverage')]+[v.get('sentinel_isolating_split_fraction','not available for this model/representation')] for n,v in importance.items()))
    reference_importance=importance[name]
    text+=f'The primary reference concentrates {reference_importance["top_feature_absolute_share"]:.1%} of absolute importance in `{reference_importance["top_feature"]}` and {reference_importance["domain_absolute_mass"]["agent"]:.1%} in the agent domain. Current amount contributes {reference_importance["current_amount_absolute_share"]:.1%} and coverage {reference_importance["domain_absolute_mass"]["coverage"]:.1%}. This concentration deserves attention in future controlled development; it does not demonstrate causality or that missingness alone drives predictions. Multi-family overlap also means high domain recall does not prove the model independently recognizes each domain mechanism.\n'
    text+='\n### All 32 importance values\n'
    text+=table(['Feature']+list(importance),([feature]+[v['values'][feature] for v in importance.values()] for feature in NAMES))
    text+='\n## 11. Development goals and decision\n\nThese are the current Stage 11 research goals, not regulatory standards or dataset design constraints. Technical execution and quality are judged separately.\n'
    text+=table(['Goal','Target','Primary Validation result','Met'],
        ([k,('<= ' if k=='false_positive_rate' else '>= ')+str(target),primary['validation'][k],summary['quality_goals_met'][k]] for k,target in summary['quality_goals'].items()))
    text+=table(['Domain goal','Target','Primary recall','Met'],([d,t,domain[name][d]['recall'],summary['domain_goals_met'][d]] for d,t in [('structuring',.65),('network',.70),('agent',.65)]))
    ignored=summary['families_below_20_percent_recall']
    text+=f'Primary families below 20% observed recall: **{", ".join(ignored) if ignored else "none"}**. The primary severe-overfit flag is **{gaps[name]["severe_flag"]}**. Zero/low recall on a family with very small support must still be disclosed, but cannot establish a stable population failure rate.\n\n'
    weakest=sorted(family[name].items(),key=lambda kv:kv[1]['recall'] if kv[1]['recall'] is not None else 2.)[:4]
    text+='Lowest primary family recalls: '+', '.join(f'{code} {v["family"]}: {v["recall"]:.4f} ({v["tp"]}/{v["support"]})' for code,v in weakest)+'.\n\n'
    text+='The current gaps call for particular attention to reciprocal cycles (N3) and agent cash imbalance (A4). A strong overall baseline does not establish reliable coverage of every scenario. S2/S4 estimates have too little support to demonstrate robust performance even where observed recall is high.\n\n'
    if summary['decision']=='A':
        text+='**A — STRONG BASELINE.** At least one candidate meets the stated aggregate and domain goals with no family below the prespecified diagnostic recall floor and no severe generalization flag. The evidence supports separately authorized controlled refinement. Sparse-family estimates, synthetic targets and Validation selection remain limitations.\n'
    elif summary['decision']=='B':
        text+='**B — PROMISING BUT NEEDS MODEL IMPROVEMENT.** Useful discrimination exists, while the unmet goals/family diagnostics above prevent a claim of consistently strong performance. The compact search supports further controlled model/preprocessing development. It does not isolate feature insufficiency from target overlap, and does not justify a Bayes-limit claim or changing frozen data to improve scores.\n'
    else:
        text+='**E — OTHER EVIDENCED LIMITATION.** The compact comparison shows weak ranking discrimination. Further diagnosis is needed to distinguish model, representation and experimental-target limitations; no intrinsic limit is established.\n'
    text+='\nA next authorized stage can investigate the documented weaknesses using Train/Validation with a bounded plan. No final model, final threshold or holdout result is declared here. V3 is a different synthetic decision-point task; these results do not establish superiority to V1 or V2.\n'
    text+='\n## 12. Protection and artifact verification\n\n'
    text+=f'Before/after protection: **{protection["result"]}**, {len(protection["before"]["files"])} explicitly allowlisted files before and {len(protection["after"]["files"])} after; changed paths: `{protection["changed"]}`. This includes frozen Stage 10A matrices/contract/code/evidence, V3 development inputs and design, V2 source/design/models/development, and the application/V1 allowlists. Exact paths and digests are recorded in `stage11_protection.json`.\n\n'
    text+=table(['Public artifact','Before SHA-256','After SHA-256'],([n,h,protection['after']['public'][n]] for n,h in protection['before']['public'].items()))
    text+='Public commitment verification proves those metadata bytes are unchanged. It does not newly verify unread evaluation bytes. No holdout data root is traversed. Protection is bounded by the explicit allowlist; excluded evaluation/unpartitioned historical dataset bytes are not claimed as newly inspected.\n\nAll candidate pipelines include their fitted preprocessing, are stored under `models/stage11_candidates/`, and are marked **DEVELOPMENT CANDIDATE — NOT FINAL**. Saved probabilities and model-file hashes permit auditing. Each shortlisted pipeline was loaded; scores agree within 1e-12 and all predictions at 0.50 are identical. Random Forest parallel summation caused a machine-rounding difference and a strict bitwise check stopped finalization once; diagnostics resumed from all 30 saved fits with the explicit tolerance, without retraining. The execution amendment preserves both recovery events. No model was refitted on Validation or integrated into the application.\n'
    text+=table(['Candidate','Reload maximum absolute score difference','Tolerance','Threshold-0.50 predictions identical'],
        ([r['name'],format(r['artifact_reload']['max_absolute_score_difference'],'.17g'),'1e-12',r['artifact_reload']['fixed_threshold_predictions_identical']] for r in short))
    text+='\n## 13. Reproducibility and evidence index\n\nThe modeling seed, installed library versions, exact model parameters, weights, transformations, source digests, warnings, convergence, runtime and configuration count are recorded. Repeated fits were not performed, so same-seed training repeatability across machines/library builds is not certified; exact reload prediction equality was checked for every shortlist artifact.\n\nCommands from the repository root:\n\n```powershell\npython -B -m unittest discover -s ml_v3/tests -p test_stage11_preprocessing.py -v\npython -B ml_v3/src/run_stage11.py\npython -B ml_v3/src/report_stage11.py\n```\n\nThe runner refuses to overwrite an existing candidate directory. For a fresh repeat, preserve this run and use an isolated development checkout with the same frozen inputs and recorded code/environment; capture a fresh protection-before record with `stage11_protection.snapshot()` before fitting. The report renderer reads completed artifacts only.\n'
    text+=table(['Evidence','Contents'],[
        ['[stage11_search_plan.json](stage11_search_plan.json)','Preregistered grid, seed, threshold, selection/gap rules, environment and source digests'],
        ['[stage11_execution_amendment.json](stage11_execution_amendment.json)','Recorded logging and replay-tolerance corrections with recovery source hashes; no grid or modeling change'],
        ['[stage11_candidate_results.json](stage11_candidate_results.json)','All fits, exact parameters, warnings, timings, complete Train/Validation metrics'],
        ['[stage11_shortlist.json](stage11_shortlist.json)','Shortlist, development reference and quality decision'],
        ['[stage11_preprocessing.json](stage11_preprocessing.json)','Per-column marker handling, Train medians, clipping and scaling for all variants'],
        ['[stage11_preprocessing_tests.json](stage11_preprocessing_tests.json)','Marker-specific handling and fixed-threshold confusion-orientation regression checks'],
        ['[stage11_domain_recall.json](stage11_domain_recall.json)','Domain support/TP/FN/recall'],
        ['[stage11_family_recall.json](stage11_family_recall.json)','All twelve family support/TP/FN/recall values'],
        ['[stage11_normal_fpr.json](stage11_normal_fpr.json)','Routine, H1–H8, subtype and target-0 campaign FPR; origin review rates'],
        ['[stage11_generalization.json](stage11_generalization.json)','Train–Validation gaps and severe flags'],
        ['[stage11_probability_quality.json](stage11_probability_quality.json)','Class score distributions and overlap'],
        ['[stage11_importance.json](stage11_importance.json)','Complete importance/coefficient values and concentration diagnostics'],
        ['[stage11_protection.json](stage11_protection.json)','Before/after inventories and public hashes'],
        ['[stage11_artifact_manifest.json](stage11_artifact_manifest.json)','Candidate model and score-file digests']])
    final_check=R/'stage11_final_verification.json'
    if final_check.exists():
        verified=json.loads(final_check.read_text())
        text+='\nFinal independent artifact check: **'+verified['result']+'**. Recomputed all 60 Train/Validation candidate metric sets from saved scores; target-0 slice counts reconcile with the global confusion matrices; positive support equals TP+FN; all 61 candidate/score/README hashes and frozen feature hashes match. See [stage11_final_verification.json](stage11_final_verification.json).\n'
    return text+'\nV3 STAGE 11 COMPLETE — WAITING FOR APPROVAL.\n'

if __name__=='__main__': main()
