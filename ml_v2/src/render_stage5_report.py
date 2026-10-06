"""Render the completed Stage 5 development results without fitting models."""
import json
from pathlib import Path
from contracts import ROOT

def read(name): return json.loads((ROOT/'reports'/name).read_text(encoding='utf-8'))
def f(x): return f'{x:.4f}' if x is not None else 'n/a'
def table(headers,rows): return '| '+' | '.join(headers)+' |\n|'+ '|'.join(['---']*len(headers))+'|\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in rows)+'\n'

def main():
    search=read('stage5_search_results.json'); short=read('stage5_shortlist.json')['selected']; domains=read('stage5_domain_results.json'); hard=read('stage5_hard_negative_results.json'); diag=read('stage5_feature_domain_diagnostics.json'); protection=read('stage5_v1_protection.json')
    allrows=search['results']; best=max(allrows,key=lambda r:r['validation']['macro_f1']); bv=best['validation']; seed=search['seed']
    targets={'macro_f1':.80,'suspicious_recall':.70,'suspicious_f1':.65,'average_precision':.65}
    achieved={k:bv[k]>=v for k,v in targets.items()}; achieved['false_positive_rate']=bv['false_positive_rate']<=.08
    lines=['# MODEL V2 — STAGE 5 FOCUSED MODEL IMPROVEMENT',
        '',f'**Decision: C — the current 30-feature representation appears to limit performance.** The strongest searched model reached Validation Macro F1 **{f(bv["macro_f1"])}** at threshold 0.50; the development targets were not substantially met. This is a development diagnosis, not proof of an intrinsic Bayes limit. A controlled feature improvement stage is justified before threshold optimization.',
        '', '## Scope and method',
        '',f'Train and Validation only; fixed 30 Stage 3 features; threshold **0.50** throughout. Seed `{seed}`. {search["configuration_count"]} configurations, {search["training_seconds"]:.1f} seconds including evaluations and refits. Models: XGBoost, HistGradientBoosting, Gradient Boosting, a small strongly regularized Random Forest reference, and a limited Logistic Regression convergence check. Moderate positive weights were searched. No resampling or scenario metadata entered any classifier. XGBoost used raw features; other tree searches used the Stage 4 clipped path where specified; Logistic used robust scaling. All preprocessing was fitted on Train.',
        '', '## Search outcome',
        '',table(['Rank','Name','Algorithm','Weight','Train Macro F1','Validation Macro F1','Suspicious precision','Recall','Suspicious F1','PR-AUC','ROC-AUC','FPR'],[
            [i,r['spec']['name'],r['spec']['algorithm'],f(r['spec']['weight']),f(r['train']['macro_f1']),f(r['validation']['macro_f1']),f(r['validation']['suspicious_precision']),f(r['validation']['suspicious_recall']),f(r['validation']['suspicious_f1']),f(r['validation']['average_precision']),f(r['validation']['roc_auc']),f(r['validation']['false_positive_rate'])]
            for i,r in enumerate(sorted(short,key=lambda x:x['validation']['macro_f1'],reverse=True),1)]),
        'The complete 72-row search, exact parameters, fit times, warnings, and metrics are in `stage5_search_results.json`. The table is the Pareto-aware reporting shortlist: the strongest eligible model per family plus additional candidates with useful recall and controlled FPR. Candidate artifacts are development artifacts only.',
        '', '### Development targets',
        '',table(['Target','Goal','Best Macro F1 model','Met'],[[k,f(v),f(bv[k]),'yes' if achieved[k] else 'no'] for k,v in targets.items()]+[['false_positive_rate','≤0.0800',f(bv['false_positive_rate']),'yes' if achieved['false_positive_rate'] else 'no']]),
        'The domain targets are evaluated for each shortlisted model below. A higher single metric is not interpreted as success when recall, hard-negative FPR, or Train/Validation gaps worsen.',
        '', '## Generalization',
        '',table(['Name','Train/Val suspicious F1','Gap','Train/Val recall','Gap','Train/Val ROC-AUC','Gap','Train/Val PR-AUC','Gap'],[[r['spec']['name'],f(r['train']['suspicious_f1'])+'/'+f(r['validation']['suspicious_f1']),f(r['gap']['suspicious_f1']),f(r['train']['suspicious_recall'])+'/'+f(r['validation']['suspicious_recall']),f(r['gap']['suspicious_recall']),f(r['train']['roc_auc'])+'/'+f(r['validation']['roc_auc']),f(r['gap']['roc_auc']),f(r['train']['average_precision'])+'/'+f(r['validation']['average_precision']),f(r['gap']['average_precision'])] for r in short]),
        'Macro F1 Train/Validation values and gaps are in the search table and `stage5_generalization.json`.',
        '', '## Validation domain recall',
        '',table(['Name','Structuring (goal .60)','Network (goal .70)','Agent (goal .65)'],[[name]+[f(domains[name]['domains'][d]['recall']) for d in ('structuring','network','agent')] for name in domains]),
        '### Scenario-family recall',
        '',table(['Name']+list(next(iter(domains.values()))['families']),[[name]+[f(x['recall']) for x in value['families'].values()] for name,value in domains.items()]),
        'The 12 family names follow the frozen Stage 2 scenario manifest. N3 is `reciprocal_relationship_cycle`; A1, A2 and A4 are `agent_wallet_growth`, `agent_wallet_concentration` and `agent_flow_imbalance`.',
        '', '## Validation normal false-positive rates',
        '',table(['Name']+list(next(iter(hard.values()))),[[name]+[f(x['false_positive_rate']) for x in value.values()] for name,value in hard.items()]),
        'H1 and H7 remain explicit hard-negative diagnostics. Counts and false positives for every slice are in `stage5_hard_negative_results.json`.',
        '', '## Feature-domain diagnostic',
        '',table(['Feature group','Count','Validation Macro F1','Suspicious recall','PR-AUC','FPR'],[[name,len(x['feature_names']),f(x['validation']['macro_f1']),f(x['validation']['suspicious_recall']),f(x['validation']['average_precision']),f(x['validation']['false_positive_rate'])] for name,x in diag['groups'].items()]),
        'Each row used the same moderately weighted HistGradientBoosting specification fitted independently on Train. Single-group models are diagnostic ablations, not proposed production models. Their poorer ranking and classification performance shows that signal is distributed across groups; the all-feature result remains far below the targets. This supports a representation limitation but cannot separate feature insufficiency from synthetic class overlap conclusively.',
        '', '## Reproducibility and convergence',
        '',table(['Configuration','Same-seed max probability difference','Same-seed predictions identical','Additional-seed Macro F1'],[[name,f(v['max_abs_difference_same_seed']),v['predictions_identical_same_seed'],', '.join(f(m['macro_f1']) for k,m in v['seed_metrics'].items() if k!=str(seed))] for name,v in search['reproducibility'].items()]),
        'Logistic Regression diagnostic: '+ '; '.join(f"{r['spec']['name']} weight {r['spec']['weight']}: {'converged' if not r['convergence_warnings'] else 'warning: '+str(r['convergence_warnings'])}" for r in allrows if r['spec']['algorithm']=='logistic_regression')+'.',
        '', '## Decision and protection',
        '',f'Best Validation Macro F1 configuration: `{best["spec"]["name"]}` with parameters `{json.dumps(best["spec"]["params"],sort_keys=True)}` and positive weight {f(best["spec"]["weight"])}. Stage 4 primary was 0.5814 Macro F1 with 0.2061 recall and 0.0634 FPR. Stage 5 improved model discrimination only to the extent measured above. The shortlist records alternatives so a small Macro F1 edge cannot hide weak suspicious recall or a large FPR.',
        '',f'Before/after SHA-256 comparison: **{protection["result"]}**, {protection["protected_file_count"]} V1/application files and {protection["v2_input_file_count"]} V2 dataset/feature input files. No Final Test or Independent Evaluation data, labels, matrices, or features were accessed or constructed. No V1 or application file changed. No threshold other than 0.50 was evaluated. No final V2 model was frozen or integrated.',
        '', 'The development targets remain far enough away that threshold tuning alone is not a justified next stage. Recommend a separately approved, controlled feature improvement stage using Train/Validation, with attention to reciprocal cycles, weak agent families, and H1/H7 ambiguity. Preserve this Stage 5 result as the fixed-feature baseline.',
        '', 'V2 STAGE 5 COMPLETE — WAITING FOR APPROVAL.', '']
    path=ROOT/'reports/V2_STAGE5_MODEL_IMPROVEMENT.md'; path.write_text('\n'.join(lines),encoding='utf-8')
    print(path)
if __name__=='__main__': main()
