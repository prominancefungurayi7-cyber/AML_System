"""Report and audit saved development outputs. No fit calls."""
from pathlib import Path
import json,sys
import joblib
import numpy as np
from run_stage18 import ROOT,EVID,ART,read,save,sha,FAMILIES

def main():
    report=ROOT/'ml_v4/reports/V4_STAGE18_MODEL_TRAINING_REPORT.md'
    if report.exists() or (EVID/'stage18_decision.json').exists():raise FileExistsError('No historical overwrite')
    summary=read('ml_v4/evidence/stage18/run_summary.json')
    plan=read('ml_v4/evidence/stage18/frozen_training_plan.json')
    selection=read('ml_v4/evidence/stage18/development_selection.json')
    comparison=read('ml_v4/evidence/stage18/comparison.json')
    ledger=[json.loads(l) for l in (EVID/'fit_ledger.jsonl').read_text().splitlines()]
    starts=[r for r in ledger if r['state']=='STARTED'];done=[r for r in ledger if r['state']=='COMPLETE']
    assert len(starts)==len(done)==summary['fit_count']==16 and not [r for r in ledger if r['state']=='FAILED']
    assert len({r['id'] for r in starts})==16 and [r['ordinal'] for r in starts]==list(range(1,17))
    assert plan['frozen_utc']<starts[0]['utc']
    for n,h in plan['source_sha256'].items():assert sha(ROOT/n)==h,n
    for id,result in comparison.items():
        for part in ['train','validation']:
            y=np.load(ROOT/'ml_v4/development_features/matrices'/part/'y.npy',allow_pickle=False)
            p=np.load(ART/(id+'_'+part+'_probabilities.npy'),allow_pickle=False);z=p>=.5
            tn=int(((y==0)&~z).sum());fp=int(((y==0)&z).sum());fn=int(((y==1)&~z).sum());tp=int(((y==1)&z).sum())
            recorded=result[part]
            assert [tn,fp,fn,tp]==[recorded[k] for k in ['TN','FP','FN','TP']]
            f1=(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0)
            f0=(2*tn/(2*tn+fp+fn) if 2*tn+fp+fn else 0)
            assert abs(recorded['macro_f1']-(f0+f1)/2)<1e-12
    support=read('ml_v4/evidence/stage16s/development_support_review.json')
    family=read('ml_v4/evidence/stage18/family_domain_diagnostics.json')
    for id,d in family.items():
        for part in ['train','validation']:
            for f in FAMILIES:assert d[part]['families'][f]['denominator']==support['partitions'][part]['families'][f]['decision_points']
    save('final_metric_verification.json',{'status':'PASS','fit_ledger':'16 unique starts and 16 completions; plan frozen before first fit; no failures',
        'confusion_and_macro_f1':'Independent arithmetic from all 32 saved probability arrays matches recorded metrics',
        'family_denominators':'All primary models match saved Stage16S Train/Validation supports',
        'frozen_source_hashes':'PASS','threshold':.5,'independent_external_audit':False,
        'wilson_limit':'Descriptive independence-based intervals only. Floating arithmetic can exceed an endpoint by ~2e-16 in raw records; this is not extra probability mass.'})
    preservation=read('ml_v4/evidence/stage18/preservation_verification.json')
    assert all(sha(ROOT/n)==h for n,h in preservation['before'].items())
    save('final_preservation_check.json',{'status':'PASS','protected_count':len(preservation['before']),'changed_paths':[],
        'historical_gap':'Unchanged incomplete Stage15A broad snapshot; no restoration or old-manifest edits',
        'sealed_contents_accessed':False})
    selected=selection['selected'];status='A' if selected else 'B'
    title='A — DEVELOPMENT MODEL CANDIDATE SELECTED' if selected else 'B — TRAINING COMPLETE; NO SUITABLE DEVELOPMENT CANDIDATE'
    details=read('ml_v4/evidence/stage18/'+selected+'_metrics.json') if selected else None
    if selected:
        model_path=ART/(selected+'_EXPERIMENTAL.joblib')
        assert sha(model_path)==details['artifact_sha256']
        pipe=joblib.load(model_path)
        assert pipe.classes_.tolist()==[0,1] and pipe.named_steps['preprocess'].n_train_rows_==60000
        joblib.dump(pipe.named_steps['preprocess'],ART/'selected_preprocessor_EXPERIMENTAL.joblib')
        save('selected_artifacts.json',{'status':'EXPERIMENTAL_DEVELOPMENT_ONLY','pipeline':model_path.relative_to(ROOT).as_posix(),
            'pipeline_sha256':sha(model_path),'preprocessor':(ART/'selected_preprocessor_EXPERIMENTAL.joblib').relative_to(ROOT).as_posix(),
            'preprocessor_sha256':sha(ART/'selected_preprocessor_EXPERIMENTAL.joblib'),'classes':[0,1],'threshold':.5,
            'feature_version':'v4.features.1','encoded_columns':pipe.named_steps['preprocess'].output_columns_,
            'load_requirement':'Trusted pinned local artifacts only; import development_training/preprocessing.py for custom transformer; exact recorded dependencies; no application integration.'})
    resources={i:{'fit_seconds':r['fit_seconds'],'peak_process_working_set_bytes':r['peak_process_working_set_bytes']} for i,r in comparison.items()}
    save('resource_runtime_report.json',{'per_fit':resources,'sum_fit_seconds':sum(r['fit_seconds'] for r in comparison.values()),
        'run_peak_working_set_bytes':summary['peak_working_set_bytes'],'memory_meaning':'Windows process high-water mark, including retained earlier models and diagnostics; not isolated estimator allocation.',
        'threads':1,'versions':plan['versions'],'wall_interval':{'plan_frozen_utc':plan['frozen_utc'],'completed_utc':summary['completed_utc']}})
    save('support_and_clustering.json',{'source':'Stage16S development_support_review.json; existing diagnostics, not generator reconstruction',
        'families':{part:{f:{k:r[k] for k in ['decision_points','minimum_objective','distinct_subjects','distinct_clusters','distinct_units','maximum_subject_share','maximum_cluster_share']} for f,r in support['partitions'][part]['families'].items()} for part in ['train','validation']},
        'validation_units':3,'cluster_uncertainty':'Three communities do not support stable population precision. Report unit-specific rates and raw family counts; Wilson bounds ignore dependence. No precise independent-generalization claim or row-wise bootstrap.'})
    primary=['primary_LR','primary_RF','primary_HGB','primary_XGB']
    table=[];conf=[];families=[];diags=[]
    for id in primary:
        r=comparison[id];v=r['validation']
        table.append(f"| {id.removeprefix('primary_')} | {r['train']['macro_f1']:.4f} | {v['macro_f1']:.4f} | {v['positive_precision']:.4f} | {v['positive_recall']:.4f} | {v['false_positive_rate']:.4f} | {v['roc_auc']:.4f} | {v['average_precision']:.4f} | {r['fit_seconds']:.2f} |")
        conf.append(f"| {id.removeprefix('primary_')} | {v['TN']} | {v['FP']} | {v['FN']} | {v['TP']} | {v['accuracy']:.4f} | {v['balanced_accuracy']:.4f} | {v['positive_f1']:.4f} |")
    for f in FAMILIES:
        s=support['partitions']['validation']['families'][f]
        recalls=' | '.join(f"{family[id]['validation']['families'][f]['numerator']}/{s['decision_points']} ({family[id]['validation']['families'][f]['rate']:.3f})" for id in primary)
        families.append(f"| {f} | {recalls} | {s['distinct_subjects']} / {s['distinct_clusters']} | {'Met' if s['decision_points']>=300 else 'Shortfall'} |")
    for id,r in comparison.items():
        if id.startswith('primary_'):continue
        diags.append(f"| {id} | {r['validation']['macro_f1']:.4f} | {r['validation']['positive_recall']:.4f} | {r['validation']['false_positive_rate']:.4f} | {r['validation']['average_precision']:.4f} |")
    imp=read('ml_v4/evidence/stage18/permutation_importance.json');shortcut=read('ml_v4/evidence/stage18/shortcut_diagnostics.json')
    importance_rows=[]
    for f in ['LR','RF','HGB','XGB']:
        r=imp[f];s=shortcut['comparisons'][f]
        importance_rows.append(f"| {f} | `{r['dominant']}` | {r['top_shares']['1']:.3f} | {r['top_shares']['3']:.3f} | {r['top_shares']['5']:.3f} | {s['removed_macro_f1_drop']:.4f} |")
    domain_rows=[];hard_rows=[]
    for d in ['structuring','network','agent']:
        domain_rows.append('| '+d+' | '+' | '.join(f"{family[id]['validation']['domains'][d]['numerator']}/{family[id]['validation']['domains'][d]['denominator']} ({family[id]['validation']['domains'][d]['rate']:.3f})" for id in primary)+' |')
    for origin,r in details['validation_slices']['hard_origin_fpr'].items():hard_rows.append(f"| {origin} | {r['numerator']} / {r['denominator']} | {r['rate']:.4f} |")
    v=details['validation'];bins=v['calibration_bins'];ece=sum(r['count']/15000*abs(r['mean_probability']-r['observed_positive_fraction']) for r in bins if r['count'])
    text=f'''# MODEL V4 — STAGE 18 DEVELOPMENT-ONLY MODEL TRAINING AND COMPARISON

**{title}**

Selected **XGBoost (`primary_XGB`) as an experimental development candidate** under the rule frozen before fitting. At threshold 0.50 it achieved Validation Macro F1 **{v['macro_f1']:.4f}**, suspicious-pattern recall **{v['positive_recall']:.4f}**, FPR **{v['false_positive_rate']:.4f}**, ROC-AUC **{v['roc_auc']:.4f}** and Average Precision **{v['average_precision']:.4f}**. These are selected synthetic development results. No final V4 model, independent evaluation readiness or production approval is claimed.

**Important limitation:** S2 recall is 11/23 and S4 recall is 4/16. Nine original family-support objectives still fail. Strong aggregate scores do not establish reliable twelve-family performance.

## 1. Authorization, inputs and preservation gates

The user's Stage 18 request authorizes Train-only fitting and Train/Validation comparison after Stage 17. Stage 15/15A definitions and restrictions retain precedence; Stage 16R's retained draw, Stage 16S's support failures, Stage 16T's challenge protocol and Stage 16U/16V custody limitations remain unchanged. Stage 17's frozen matrices and artifact hashes were verified before any fit.

Train contains 60,000 scored records; Validation contains 15,000. Each X has exactly 40 semantic fields, 39 float64 and one categorical Unicode type. The original y arrays, row order and transaction IDs match frozen ground truth. Existing family annotations agree exactly with the binary union labels. Diagnostic provenance contains warm-up as well as scored records: the initial preflight join incorrectly assumed scored rows only and stopped before any fitting. The implementation was corrected to prove that its extra IDs equal the permitted warm-up IDs exactly; only scored annotations enter diagnostics. No input contract, data, feature or label was changed. Final preflight: PASS. This correction consumed zero model fits.

Only authorized Train/Validation development files and public research evidence were accessed. Annotation loading uses exact partition/filename allowlists and rejects resolved path redirection. The extractor was not rerun. Private origins and family annotations are held separately for diagnostics and never passed to preprocessing, fit or predict. Original Final Test and Independent Evaluation remain SEALED_QUARANTINED. No private evaluation contents were read, listed, hashed, decrypted or copied. No challenge data or secret was created.

Evidence: [input verification](../evidence/stage18/input_verification.json), [frozen plan](../evidence/stage18/frozen_training_plan.json), [final metric verification](../evidence/stage18/final_metric_verification.json).

## 2. Frozen preprocessing contract

Every fitted artifact is a scikit-learn Pipeline containing `FrozenPreprocessor` followed by its classifier. Explicit per-column -1/-3 missing markers are converted to NaN. Existing N4 residual NaN remains missing. Valid negative residuals, concentration differences and cash-skew changes are preserved; there is no generic negative-value replacement.

The categorical order is **wallet_to_wallet, cash_in, cash_out**. Those three columns replace the one categorical field at its schema position. Full pipelines therefore produce **42 numeric columns**, verified from the actual output. Numeric missing values use a Train-fitted median imputer; an entirely empty Train column would receive fixed zero while retaining its column. No extra missingness indicators enter the full pipelines. All 42 columns then use Train-fitted standard scaling, unchanged on Validation. Scaling is shared for a simple reproducible contract; tree candidates do not require it. No label-derived encoding, class rebalancing, resampling, calibration or Validation-fitted transform is used.

The missingness-only diagnostic has 39 indicator columns and is not a feature-contract amendment or selectable candidate. Other diagnostics use only the predeclared subsets. Hand assertions verified semantic ordering, 42-column expansion, sentinel conversion and preservation of legitimate negative values before fitting. Schema checks reject unknown transaction types. Exact column names and marker mapping appear in [preprocessing_specification.json](../evidence/stage18/preprocessing_specification.json).

## 3. Candidates, fit budget and frozen selection rule

The plan was saved before the first fit and binds source hashes, dependency versions, seed, configurations, threshold, diagnostics and selection rule. Four primary configurations were used:

| Family | Predeclared configuration |
| --- | --- |
| Logistic Regression | C=1, lbfgs, maximum 2,000 iterations; no class weighting |
| Random Forest | 160 trees, unrestricted depth, leaf minimum 2, sqrt feature sampling, one worker |
| HistGradientBoosting | 200 iterations, learning rate .07, 31 leaves, minimum leaf 20, L2=1, early stopping disabled |
| XGBoost | 200 trees, depth 5, learning rate .07, child weight 5, lambda=1, full row/column sampling, histogram algorithm, one worker |

XGBoost is the installed fourth family already listed by Stage 15. It supplies a distinct regularized boosted-tree implementation; no fifth family was added. Random state is 2026092915; diagnostic repeats use +1. No Validation early stopping or evaluation set was supplied.

Exactly **16 classifier fits** ran: 4 primary, 4 matched dominant-feature removals, missingness-only, dominant-only, four-A1-feature-only, Train-label shuffle, and 4 seed repeats. All completed without fit warnings or failures. The maximum policy budget is 36; the 20 unused slots expire under this plan. No adaptive tuning, threshold search, Train+Validation refit or calibration occurred. Every started fit was durably entered in [fit_ledger.jsonl](../evidence/stage18/fit_ledger.jsonl) before calling fit, with its completion, runtime and resource observation. Initial preflight assertions were not fitting attempts.

Eligibility was preregistered as Validation Macro F1≥.80, recall≥.65, FPR≤.10, every domain recall≥.60, S3/N2/A1 recall≥.60, each H-origin FPR≤.20 where at least 100 target-0 rows exist, Train−Validation Macro F1≤.08, repeat Macro F1 change≤.03, and no unresolved technical failures/warnings. These are synthetic development triage tolerances, not relaxed family-support gates, independent acceptance criteria or operational risk limits.

Among eligible primary candidates, maximize Macro F1; within .005 of the best, choose lowest FPR, then highest minimum domain recall, shortest fit time and lexical ID. RF, HGB and XGBoost passed. LR failed overall recall and domain recall. HGB has the highest Macro F1 (.9616), but XGBoost (.9567) is within the frozen .005 tolerance and has lower FPR. Relative to HGB, XGBoost yields **21 fewer false positives and 64 additional false negatives**. This is the declared trade-off, not a claim that XGBoost dominates every metric. Diagnostic models and repeats were never eligible for selection.

## 4. Primary comparison at threshold 0.50

Train metrics are resubstitution diagnostics. Validation metrics drive this development comparison. AP means the sum of precision times recall increments, not trapezoidal PR area. The positive target is an observable suspicious-pattern review rule, not proven criminal activity.

| Model | Train Macro F1 | Validation Macro F1 | Precision | Recall | FPR | ROC-AUC | AP | Fit seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
'''+ '\n'.join(table)+'''

| Model | TN | FP | FN | TP | Accuracy | Balanced accuracy | Positive F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
'''+ '\n'.join(conf)+f'''

Confusion-matrix order is `[[TN,FP],[FN,TP]]`. The selected matrix is `[[11852,118],[292,2738]]`. Its normal-class recall is {v['normal_recall']:.6f}. RF has the largest primary Train-to-Validation Macro F1 gap (about .0483), while XGBoost's gap is about .0047; these are descriptive overfitting checks, not independent generalization guarantees. Complete Train/Validation metrics and probabilities are saved for every fit in [comparison.json](../evidence/stage18/comparison.json) and the explicitly experimental artifact directory.

Selected Validation Brier score is **{v['brier_score']:.6f}**, log loss **{v['log_loss']:.6f}**. Ten fixed-width reliability bins give a descriptive weighted absolute calibration gap of **{ece:.6f}**. No calibration was fitted, and this bin statistic depends on binning and reused Validation. Scores are class-1 probabilities from the estimator, not calibrated certainty of laundering. Empty rate denominators are null; precision with no predicted positives is zero with an undefined flag. The shuffle diagnostic predicts no positives at .50, so that flag matters.

## 5. Family, domain and clustering results

The table shows predicted-positive rows among each frozen family, with exact denominators. Membership overlaps; these rows cannot be summed as independent observations or interpreted as family-specific attribution by the model. Subjects and episode/background clusters are retained from the authorized Stage 16S evidence, not reconstructed from private intent.

| Family | LR TP/support (recall) | RF | HGB | XGBoost | Validation subjects / clusters | Original ≥300 objective |
| --- | --- | --- | --- | --- | ---: | --- |
'''+ '\n'.join(families)+'''

S1/S2/S4/N1/N3/N4/A2/A3/A4 remain below the original development support objectives. S2 has only 7 Validation subjects/7 clusters; S4 has 12/12. A3's perfect observed recall still has inadequate support. S3/N2/A1 satisfying count objectives does not certify precision or independence. Full Train/Validation supports, concentration and cluster counts are in [support_and_clustering.json](../evidence/stage18/support_and_clustering.json).

| Domain | LR TP/support (recall) | RF | HGB | XGBoost |
| --- | --- | --- | --- | --- |
'''+ '\n'.join(domain_rows)+'''

Domain-only and unique multi-domain results are retained in [family_domain_diagnostics.json](../evidence/stage18/family_domain_diagnostics.json). This is one union-target classifier, with no separate domain prediction heads; a separate domain-specific FPR cannot be inferred. False-positive behaviour is reported on genuine union-target-0 origin/type slices instead.

Selected hard-origin/background target-0 FPR:

| Origin | FP / negative support | FPR |
| --- | ---: | ---: |
'''+ '\n'.join(hard_rows)+'''

Pre-onset campaign target-0 FPR is 0/296. H-origin rows with any true family remain positive and are excluded from FPR denominators. No hard-origin relabeling or selection occurred. Exact legitimate-growth-mechanism and family near-boundary slices were not reconstructed: the available archetype field is not equivalent to an observed origin mechanism. Their absence limits the broader shortcut audit and is not hidden behind an archetype proxy.

Only three Validation communities exist. Selected unit recalls are approximately .8929, .9085 and .9098; unit FPRs .00755, .01205 and .00997. Selected S2 unit recalls vary from 0/3 to 10/15 and 1/5; S4 has 1/4, 2/9 and 1/3. These sparse clustered counts do not support precise population inference. Raw per-unit family rates and descriptive Wilson intervals are saved. Wilson intervals ignore dependence; no row-wise bootstrap or stable cluster precision is claimed. Minute floating endpoint overshoots in raw Wilson records are arithmetic rounding, not probabilities above one.

## 6. Shortcut, missingness and feature-dependence audit

All four primary models use the same 3,000 Validation rows sampled uniformly without replacement with seed 2026092915. Each semantic field is permuted three times, paired across models; transaction type is permuted before encoding so its three indicators move together. Deterministic repeat seeds are base 2026092916 plus repeat index 0,1,2, as fixed in source before fitting. Baseline AP and perturbed AP use exactly the same sample. Signed mean AP drops, repeat sample SD, absolute-mass group shares and top shares are saved in [permutation_importance.json](../evidence/stage18/permutation_importance.json). There is no substitution of native impurity/gain scores.

| Model | Highest absolute mean AP-drop field | Top-1 mass | Top-3 mass | Top-5 mass | Macro F1 drop after matched removal |
| --- | --- | ---: | ---: | ---: | ---: |
'''+ '\n'.join(importance_rows)+'''

XGBoost assigns about 76.2% of absolute permutation mass to agent fields, 15.5% to network and 7.6% to structuring. Growth alone accounts for about 37.7%. The matched growth-removal XGBoost falls to Macro F1 .8785, recall .7604 and AP .9041. This is material dependence. Growth is an explicitly permitted direct component of A1, so neither importance nor ablation establishes leakage by itself. Correlated fields can divide mass, and permutations can create off-manifold combinations.

The permutation sample contains only 7 S2 and 3 S4 positive rows. Importance cannot rescue sparse-family evaluation. For the selected full model, recall among positives without A1 is 1271/1563 (.8132), below aggregate .9036 and A1's 1467/1467. Dominant-family alignment contributes substantially to the headline result.

| Predeclared diagnostic | Validation Macro F1 | Recall | FPR | AP |
| --- | ---: | ---: | ---: | ---: |
'''+ '\n'.join(diags)+'''

Missingness-only HGB has AP .2856 and very low .50-threshold recall (.0155); missingness carries some development signal but does not reproduce the full model. Growth-only HGB and the four-A1-field model demonstrate how much the enriched compound target can be approximated with a small representation. The Train-label-shuffle fit gives AP .2406 and zero .50-threshold recall; this is a sanity diagnostic, not a formal no-leakage proof. Shuffle Train metrics are measured against the real frozen Train labels, not the shuffled training target, so they represent sanity performance rather than fit to its permuted labels.

Seed-repeat Macro F1 changes were zero for LR/HGB/XGBoost and about −.00110 for RF. Several fixed algorithms/configurations are effectively deterministic without subsampling; zero change is not evidence across broad resampling uncertainty. No extra seeds or configurations were tried.

Selected type-specific target-0 FPR is .01357 for W2W, .00471 for Cash-In and .00624 for Cash-Out. Type is a legitimate role/context input, yet differing rates and declared generator laws warrant qualification. A1-eligible versus ineligible recall/FPR and agent-age strata are saved. The zero-age bin includes absent agents; it cannot be interpreted solely as young-agent behaviour. Intermediate agent-age bins have no support and are reported null.

Stage 17's marker-aware Train/Validation distributions remain the shift reference. For example, growth missingness is 31.43% in Train and about 32.19% in Validation; no preprocessing was fitted on Validation to reduce this difference. Generator origin/archetype/IDs never enter X. Origin diagnostics, type permutations, missingness and shuffle checks do not rule out every synthetic-generation artifact. No feature contract was amended after inspecting results.

## 7. Reproducibility, artifacts and resources

Runtime: Python 3.14.3, NumPy 2.4.3, scikit-learn 1.9.0, XGBoost 3.4.1. Estimator workers and numerical thread pools were constrained to one. The frozen plan records exact parameters and source hashes. Predictions, all sixteen fitted pipelines and permutation sample indices are saved under `ml_v4/development_training/artifacts/`, outside V1/V3 model locations. Every pipeline embeds its fitted preprocessing; an additional standalone selected preprocessor is saved without refitting.

Selected pipeline: [primary_XGB_EXPERIMENTAL.joblib](../development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib). Standalone preprocessing: [selected_preprocessor_EXPERIMENTAL.joblib](../development_training/artifacts/selected_preprocessor_EXPERIMENTAL.joblib). [selected_artifacts.json](../evidence/stage18/selected_artifacts.json) binds their hashes, classes [0,1], feature version, 42-column order and threshold .50. Load only these trusted hash-verified artifacts in the recorded runtime, with `development_training/preprocessing.py` importable. No service or application adapter was added.

Primary artifact reloads reproduced predictions exactly on the fixed first 100 Validation rows; this is a serialization check, not independent evaluation. Final independent arithmetic reproduced all Train/Validation confusion matrices and Macro F1 from the 32 saved probability arrays. Family denominators match existing Stage 16S evidence. No new fit was required for final verification.

Peak process working set was 598,306,816 bytes (about 570.6 MiB), including previously retained models and diagnostics. It is not isolated per-model memory. Per-fit runtime/high-water measurements and overall wall interval are in [resource_runtime_report.json](../evidence/stage18/resource_runtime_report.json). Replaying the entire training script against existing outputs is refused, preventing an unnoticed second fitting run; any future repeat requires separate authorization and budget accounting.

## 8. Preservation and scientific limitations

All named protected input hashes match before and after fitting and at final review. Protected scope includes Stage 17 outputs, frozen V4 design/data/labels and authorized annotation files, earlier public evidence, V1 production artifact and V3 experimental model/source/integration. No Flask, MySQL, dashboard, API, target, feature definition, transaction, partition, challenge protocol or custody control was changed. [preservation_verification.json](../evidence/stage18/preservation_verification.json) and [final_preservation_check.json](../evidence/stage18/final_preservation_check.json) define the exact scope. Sealed evaluation bytes are deliberately excluded and unread.

Stage 16V's incomplete broad Stage 15A historical snapshot remains unresolved. Nothing was restored or rewritten to manufacture a full preservation PASS. The present checks cover explicitly available protected files, not every historical file or all disk contents.

The main limitations are repeated development use, nine family-support failures, only three Validation communities, direct-component learning, strong A1/growth dependence, compact representation omissions and unknown transport to independent or real operator populations. S2/S4 empirical weakness must accompany aggregate metrics. No real-world laundering, intent, regulatory or production-effectiveness claim follows from this benchmark. A development candidate is not a final model. Original holdouts remain quarantined and cannot repair or certify these findings; challenge generation remains blocked by unavailable independent custody.

## 9. Deliverables and final decision

New files are confined to `ml_v4/development_training/`, `ml_v4/evidence/stage18/` and this report. The evidence directory contains the input gate, frozen plan, preprocessing specification, complete fit ledger, all fit metrics, probability/artifact references, family/domain/support diagnostics, permutation/shortcut audits, selection, runtime, preservation, metric verification and final artifact hashes. Earlier reports and artifacts were not overwritten.

**A — DEVELOPMENT MODEL CANDIDATE SELECTED**

`primary_XGB` is selected for further separately authorized development, subject to the documented sparse-family and synthetic-data limitations. This decision authorizes no independent evaluation, production promotion, threshold optimization, challenge generation or Flask integration. No Stage 19 work is started.

V4 STAGE 18 COMPLETE — WAITING FOR APPROVAL.
'''
    report.write_text(text,encoding='utf-8',newline='\n')
    files=[report,*EVID.iterdir(),*ART.iterdir(),ROOT/'ml_v4/development_training/run_stage18.py',ROOT/'ml_v4/development_training/preprocessing.py',Path(__file__)]
    save('stage18_decision.json',{'decision':title,'selected':selected,'scope':'Experimental development candidate only; no independent readiness or production approval',
        'fit_count':16,'fit_cap':36,'unused_slots_expired':20,'training_failures':0,'threshold':.5,'threshold_optimized':False,
        'family_support_failures_retained':['S1','S2','S4','N1','N3','N4','A2','A3','A4'],
        'independent_custody':'UNAVAILABLE; challenge blocked','original_evaluation':'SEALED_QUARANTINED; no access',
        'stage19_started':False,'preservation_snapshot_limitation_retained':True,
        'artifact_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in files if p.is_file()},'self_hash_excluded':True})
    print('Stage18 final report and decision created; 16 fits, all final checks passed.')

if __name__=='__main__':main()
