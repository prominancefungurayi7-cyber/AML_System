"""Documentation-only development freeze. Standard library; no model execution."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
import platform
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'ml_v4/evidence/stage23'
REPORT=ROOT/'ml_v4/reports/V4_STAGE23_DEVELOPMENT_FREEZE_REPORT.md'
DECISION='A — ORIGINAL 40-FEATURE V4 DEVELOPMENT CANDIDATE RETAINED AND FROZEN'
DISCLAIMER='This model identifies transaction patterns defined as suspicious within the synthetic research benchmark. It does not determine that money laundering has occurred.'
FAMILIES='S1 S2 S3 S4 N1 N2 N3 N4 A1 A2 A3 A4'.split()

def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(name,data):
    with (OUT/name).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(data,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
def markdown(name,text):
    with (OUT/name).open('x',encoding='utf-8',newline='\n') as f:f.write(text)

def main():
    if OUT.exists() or REPORT.exists():raise FileExistsError('No overwrite of Stage23')
    protected=dict(read('ml_v4/evidence/stage22/preservation_verification.json')['after_sha256'])
    prior_decision=read('ml_v4/evidence/stage22/stage22_decision.json')
    protected.update(prior_decision['artifact_sha256'])
    n='ml_v4/evidence/stage22/stage22_decision.json';protected[n]=sha(ROOT/n)
    for name,digest in protected.items():
        if '/evaluation/' in name or '/data/' in name and not name.startswith(('ml_v4/data/development/train/','ml_v4/data/development/validation/')):raise PermissionError(name)
        p=ROOT/name
        if p.resolve()!=p:raise PermissionError('Redirected named input '+name)
        if sha(p)!=digest:raise ValueError('Evidence integrity conflict: '+name)
    public_docs=[n for n in protected if n.startswith('ml_v4/') and n.endswith(('.json','.md'))]
    for n in public_docs:(ROOT/n).read_text(encoding='utf-8')
    assert prior_decision['decision']=='C — EXPERIMENT INCONCLUSIVE'
    selected=read('ml_v4/evidence/stage18/selected_artifacts.json')
    original=read('ml_v4/evidence/stage18/primary_XGB_metrics.json')
    trainplan=read('ml_v4/evidence/stage18/frozen_training_plan.json')
    prep=read('ml_v4/evidence/stage18/preprocessing_specification.json')
    feature=read('ml_v4/design/v4_feature_spec.json')
    manifest=read('ml_v4/evidence/stage16r/dataset_manifest.json')
    sparse=read('ml_v4/evidence/stage19/sparse_support_uncertainty.json')
    historical_families=read('ml_v4/evidence/stage19/false_negative_analysis.json')['validation']['families']
    comparison={id:read('ml_v4/evidence/stage22/'+id+'_metrics.json') for id in ['A40-XGB','B44-XGB','A40-HGB','B44-HGB']}
    paired=read('ml_v4/evidence/stage22/paired_comparisons.json')
    dependence=read('ml_v4/evidence/stage22/permutation_component_dependence.json')
    assert selected['feature_version']=='v4.features.1' and selected['threshold']==.5
    assert len(feature['features'])==40 and len(selected['encoded_columns'])==42
    assert selected['encoded_columns']==prep['columns']
    assert sha(ROOT/selected['pipeline'])==selected['pipeline_sha256']
    assert sha(ROOT/selected['preprocessor'])==selected['preprocessor_sha256']
    for part in ['train','validation']:
        assert original[part]==comparison['A40-XGB']['partitions'][part]['overall']
        assert comparison['A40-XGB']['partitions'][part]['Stage18_reproduction']['exact']
    v=original['validation']
    assert (v['FN'],v['FP'],v['TP'],v['TN'])==(292,118,2738,11852)
    b=comparison['B44-XGB']['partitions']['validation']
    assert (b['overall']['FN'],b['overall']['FP'])==(279,115)
    assert b['slices']['families']['S2']['numerator']==18
    assert paired['XGB']['validation']['paired']['S4-only']['A_positive']==paired['XGB']['validation']['paired']['S4-only']['B_positive']==0
    assert b['slices']['families']['A4']['numerator']==144
    budget=read('ml_v4/evidence/stage22/fit_budget_verification.json')
    assert budget['cumulative_started']==20 and budget['remaining_authorized_attempts']==0
    ledgers={}
    for stage,count in [('stage18',16),('stage22',4)]:
        p=ROOT/f'ml_v4/evidence/{stage}/fit_ledger.jsonl'
        records=[json.loads(line) for line in p.read_text().splitlines()]
        assert sum(r['state']=='STARTED' for r in records)==count
        assert sum(r['state']=='COMPLETE' for r in records)==count
        ledgers[stage]={'sha256':sha(p),'started':count,'completed':count}
    OUT.mkdir(parents=True)
    save('evidence_verification.json',{'status':'PASS_NAMED_SCOPE','documents_read':public_docs,'protected_count':len(protected),'verification':'Hashes and saved summary/ledger cross-checks only. Model files hashed, not deserialized; no matrices extracted, probabilities recomputed or diagnostic model executed.','Stage18_Stage22_A40_saved_metrics_exact':True,'Stage22_original_decision':prior_decision['decision'],'Stage21_report_only_correction_retained':True,'fit_ledgers':ledgers,'external_independent_audit':False})
    interpretation={
        'historical_decision':'C — EXPERIMENT INCONCLUSIVE',
        'source':'ml_v4/evidence/stage22/paired_comparisons.json',
        'XGB':{'A40_validation':comparison['A40-XGB']['partitions']['validation']['overall'],'B44_validation':b['overall'],'S2':[11,18,23],'S4':[4,4,16],'S4_only':[0,0,12],'A4':[151,144,222]},
        'HGB':{'A40_validation':comparison['A40-HGB']['partitions']['validation']['overall'],'B44_validation':comparison['B44-HGB']['partitions']['validation']['overall'],'S2':[13,16,23],'S4':[5,5,16],'S4_only':[1,1,12]},
        'family_tradeoffs':{alg:{f:{'A_TP':paired[alg]['validation']['paired'][f]['A_positive'],'B_TP':paired[alg]['validation']['paired'][f]['B_positive'],'support':paired[alg]['validation']['paired'][f]['support'],'B_recovers_A_miss':paired[alg]['validation']['paired'][f]['B_detects_A_misses'],'B_loses_A_hit':paired[alg]['validation']['paired'][f]['A_detects_B_misses']} for f in FAMILIES} for alg in ['XGB','HGB']},
        'inference':'Partial exploratory S2 gain, unresolved S4, small XGB aggregate gain and other-family losses. HGB aggregate MacroF1 decreased. No independent confirmation or revised historical decision.',
        'growth_dependence':{id:{k:dependence[id][k] for k in ['growth_absolute_mass_share','four_added_absolute_mass_share']} for id in comparison}}
    save('stage22_interpretation.json',interpretation)
    reasons=['Original40 primary_XGB was selected by a frozen Stage18 rule before Stage19/20 redesign','44-field hypothesis arose from repeated Validation inspection','S2 gain is useful research evidence but S4/S4-only failure persists','XGB aggregate gain is small and A4 loses7 net detections; other families also trade off','HGB44 aggregate MacroF1 declines; no uniform algorithm-independent advantage','Nine support objectives and three-community dependence remain','More direct target components can improve synthetic policy approximation without real-world validity','Freezing a bounded research reference preserves reproducibility without mandating another adaptive cycle']
    save('representation_decision.json',{'decision':DECISION,'choice':'Retain original Stage18 primary_XGB, not Stage22 A40 refit or B44 replacement','reasons':reasons,'alternatives':{'promote44':'Not justified by current reused development evidence; preserve as experimental research, including S2 gains','freeze_neither':'Not necessary to preserve a technically verified development reference; essential gaps block broader validation claims, not archival development freeze'},'criterion':'Scientific defensibility and versioned evidence, not highest MacroF1','HGB':'Preserved comparator, no selection change','no_production_or_independent_approval':True})
    refs={
        'pipeline':selected['pipeline'],
        'standalone_fitted_preprocessor':selected['preprocessor'],
        'preprocessor_source':'ml_v4/development_training/preprocessing.py',
        'extractor_source':'ml_v4/development_features/extractor.py',
        'observable_contract_source':'ml_v4/generation/stage16r_contract.py',
        'feature_specification':'ml_v4/design/v4_feature_spec.json',
        'temporal_specification':'ml_v4/design/v4_temporal_contract.json',
        'target_specification':'ml_v4/design/v4_target_predicates.json',
        'target_evaluator_source':'ml_v4/generation/stage16r_evaluator.py',
        'dataset_manifest':'ml_v4/evidence/stage16r/dataset_manifest.json',
        'training_plan':'ml_v4/evidence/stage18/frozen_training_plan.json',
        'selection_record':'ml_v4/evidence/stage18/development_selection.json',
        'preprocessing_specification':'ml_v4/evidence/stage18/preprocessing_specification.json',
        'HGB_comparator':'ml_v4/development_training/artifacts/primary_HGB_EXPERIMENTAL.joblib'}
    freeze_hashes={key:{'path':p,'sha256':sha(ROOT/p)} for key,p in refs.items()}
    dependencies={pkg:importlib.metadata.version(pkg) for pkg in ['numpy','scikit-learn','xgboost','scipy','joblib','threadpoolctl']}
    assert trainplan['versions']=={'python':platform.python_version(),'numpy':dependencies['numpy'],'sklearn':dependencies['scikit-learn'],'xgboost':dependencies['xgboost']}
    runtime={'Stage18_recorded_versions':trainplan['versions'],'freeze_runtime_package_pins':dependencies,'pin_scope':'Python/NumPy/sklearn/XGBoost match historical recorded runtime. scipy/joblib/threadpoolctl are currently observed supplementary pins, not retroactively asserted Stage18 install records.','OS':platform.platform(),'interpreter':sys.executable,'interpreter_sha256':sha(sys.executable),'threads':1,'installation_lock_limit':'Version/reference freeze, not an independently validated wheel/image lock. No environment installation or model execution in Stage23. Verify dependencies and trusted hashes before any separately authorized loading.'}
    freeze={
        'freeze_id':'v4.development.freeze.stage23.1','model_identity':'primary_XGB (Stage18 original experimental pipeline)','status':'OFFICIAL_V4_DEVELOPMENT_REFERENCE_ONLY',
        'freeze_method':'Immutable references/hashes; no model rewrite, copy, chmod or application setting change','frozen_utc':datetime.now(timezone.utc).isoformat(),
        'feature_version':'v4.features.1','semantic_fields':40,'estimator_columns':42,'semantic_order':[f['name'] for f in feature['features']],'encoded_order':selected['encoded_columns'],
        'threshold':{'value':.5,'operator':'>=','calibration':'No fitted probability calibration'},
        'preprocessing':{'class':'preprocessing.FrozenPreprocessor','mode':'full','contract':prep,'training_plan_description':trainplan['preprocessing'],'fitted_state':'Already embedded in original pipeline and separately saved original preprocessor; not refitted'},
        'configuration':trainplan['comparative']['XGB'],'seed':2026092915,'runtime':runtime,'artifacts':freeze_hashes,
        'target':{'semantic_version':'v4.predicates.1','materialized_evaluator_version':manifest['versions']['evaluator'],'temporal_version':manifest['versions']['temporal'],'meaning':'Union of12 eligible observable causal suspicious-pattern predicates; target0 does not prove benignity, including cold-start ineligibility'},
        'dataset':{'id':manifest['dataset_id'],'retained_draw':'Stage16R single retained production draw; no new dataset/version','population_authority':'Frozen Stage15 plus Stage15A','generator_version':manifest['versions']['generator'],'development_sha256':manifest['development_sha256'],'manifest_sha256':sha(ROOT/refs['dataset_manifest']),'counts':{'scored_all':100000,'warmup_all':24000,'train':60000,'train_warmup':14400,'validation':15000,'validation_warmup':3600},'sealed_scope':'Only named public manifest and Train/Validation file hashes. Original sealed byte contents remain unread.'},
        'fit_history':{'stage18':16,'stage22':4,'cumulative':20,'authorized_additional':0,'inherited_ceiling':36,'expired_slots_remain_expired':True},
        'comparators_preserved':['Stage18 primary_HGB','Stage21 experimental44 matrices','All four Stage22 model pipelines and saved predictions'],
        'evaluation':'No independent challenge evaluation or real-world validation; Stage16V custody unavailable; original holdouts quarantined/supportFAIL; Stage16T40-feature semantic alignment alone is not evaluation authorization',
        'promotion':False}
    save('development_candidate_freeze.json',freeze)
    save('final_development_metrics.json',{'source':'Unmodified Stage18 saved primary_XGB metrics; exact match to Stage22 A40 saved results','threshold':.5,'train':original['train'],'validation':v,'validation_families':comparison['A40-XGB']['partitions']['validation']['slices']['families'],'validation_domains':comparison['A40-XGB']['partitions']['validation']['slices']['domains'],'evaluation_status':'Reused development Validation, not independent test','no_recalculation_with_model':True})
    family_records={}
    for f in FAMILIES:
        r=historical_families[f];s=sparse['partitions']['validation'][f]
        family_records[f]={'TP':r['TP'],'FN':r['FN'],'support':r['support'],'recall':r['TP']/r['support'],'exclusive':r['exclusive_family'],'validation_subjects':s['subjects'],'validation_clusters':s['clusters'],'train_support':sparse['partitions']['train'][f]['actual'],'train_required':1200,'validation_required':300,'count_shortfall':sparse['partitions']['train'][f]['actual']<1200 or s['actual']<300}
    save('family_strengths_weaknesses.json',{'families':family_records,'strengths':'High observed A1/A3 recall and S1/N3 detection on this development cohort; not independent sensitivity claims','weaknesses':'Sparse S2 11/23; S4 4/16 and exclusive0/12; A4 151/222, A2 109/148 and N1 77/101; N3 selected-route information loss remains','overlap':'Family/domain counts overlap; a positive union prediction does not identify which family caused it','growth_absolute_permutation_mass':dependence['A40-XGB']['growth_absolute_mass_share']})
    limitations=[
        ('L01','Synthetic data','Generic Zimbabwean mobile-money assumptions without operator calibration; artificial inventories/isolated local units; benchmark is not a natural prevalence estimate.'),
        ('L02','Nine support shortfalls','S1,S2,S4,N1,N3,N4,A2,A3,A4 miss original Train1200/Validation300 count objectives; no waiver.'),
        ('L03','S2 sparse support','112 Train,23 Validation positives; Validation7 subjects/7clusters. Retained recall11/23;44-field improvement exploratory.'),
        ('L04','S4 poor recall','128 Train,16 Validation positives; retained4/16. No net Stage22 improvement.'),
        ('L05','S4-only failure','Retained XGB0/12 exclusive Validation detections; overlap accounts for all4 S4 detections without proving causal attribution.'),
        ('L06','A1/growth dependence','A1 covers1467 Validation positives and retained detects all; growth importance and correlated agent primitives remain substantial.'),
        ('L07','Repeated Validation inspection','Used for selection, diagnosis and representation hypotheses; no independent confirmation from reuse.'),
        ('L08','Three Validation communities','Entities/episodes are dependent; row-based intervals are not reliable population uncertainty.'),
        ('L09','Family overlap','Family recalls do not add and union-positive detections need not demonstrate distinctive family reasoning.'),
        ('L10','No independent external audit','Hand checks and separate arithmetic in the same developer environment do not constitute outside review.'),
        ('L11','No independent challenge evaluation','Original holdouts quarantined with public supportFAIL; no challenge generated or scored.'),
        ('L12','Custody unavailable','Stage16V independent administrator/storage/secret/logging boundary remains unprovisioned.'),
        ('L13','No real mobile-money validation','No representative real operator cohort evaluated; synthetic findings cannot establish transport.'),
        ('L14','No production effectiveness evidence','No operational PPV, calibration, review capacity, latency, drift or downstream decision-impact validation.'),
        ('L15','Historical snapshot gap','Stage15A broad historical preservation inventory remains incomplete; exact named checks do not repair absent archive.'),
        ('L16','Representation and approximation','N3 selected-route loss and other omitted components remain; probability is not calibrated certainty of laundering.')]
    distinctions={'technical_development_success':'Verified feature parity/replay, bounded fits, saved-score arithmetic and reproducible development reference; achieved in documented scope','independent_scientific_validation':'Fresh sufficiently supported frozen evaluation with independent custody/review; not achieved','real_world_AML_validation':'Representative operator outcomes and human-workflow impact assessment; not achieved'}
    save('limitations_register.json',{'limitations':[{'id':i,'topic':t,'limitation':s} for i,t,s in limitations],'validation_levels':distinctions,'no_operational_claim':True})
    future=[
        {'area':'Representative operator data','work':'Obtain appropriate privacy/regulatory and institutional access, define observable outcomes and assess transport before operational use.'},
        {'area':'S4 learning and representation','work':'Investigate remaining approximation/support limitation under a separate prospective design; no accept-until-positive templates or lowered gates.'},
        {'area':'Support and diversity','work':'Prospectively justify additional communities, subjects and rare-family opportunities; retain failed draws and unchanged labels.'},
        {'area':'Independent evaluation','work':'Provision and independently verify custody, authorization log and access controls; preserve original quarantines and support gates.'},
        {'area':'Fresh40-versus44 study','work':'Predeclare a comparison on genuinely fresh independent data with compatible feature protocol; do not turn Stage22 into confirmation.'},
        {'area':'Robustness','work':'Predeclare drift, missing-history, model dependence and correlated-component analyses before fresh evaluation.'},
        {'area':'Calibration and operational threshold','work':'If authorized, use separately designated development/calibration evidence and review-capacity objectives; freeze calibration/threshold before untouched final evaluation. Never tune on final outcomes.'}]
    save('future_work_register.json',{'performed_now':False,'new_cycle_authorized':False,'items':future,'budget':'20 consumed; no additional attempt authorization; inherited ceiling alone grants no fits'})
    summary=f'''# Dissertation-ready V4 development results

The study used `mobile_money_aml_synthetic_100k_v4`, a retained synthetic benchmark containing100000 scored transactions and24000 warm-up events. Development used60000 Train and15000 Validation transactions with separate14400/3600 warm-up histories and disjoint entities. Original Final Test/Independent Evaluation partitions remained quarantined and did not contribute performance results. Synthetic observations made it possible to define and audit causal review-pattern labels without production customer data; the population assumptions were not calibrated to a real Zimbabwean operator and no real-data efficacy was demonstrated.

The target is the union of twelve observable suspicious-pattern predicates across **structuring, wallet-network and agent behaviour**. Logistic Regression, Random Forest, HistGradientBoosting and XGBoost were compared in Stage18. The retained development candidate is the original Stage18 **XGBoost**, using40 semantic features(42 numeric estimator columns), Train-fitted preprocessing and threshold0.50. Its preregistered selection rule considered eligibility and FPR within a MacroF1 tolerance; it was not selected solely for the largest MacroF1. HistGradientBoosting remains a comparator.

On the reused15000-row development Validation set, retained XGBoost achieved accuracy{v['accuracy']:.6f}, balanced accuracy{v['balanced_accuracy']:.6f}, MacroF1{v['macro_f1']:.6f}, suspicious-pattern precision{v['positive_precision']:.6f}, recall{v['positive_recall']:.6f}, FPR{v['false_positive_rate']:.6f}, ROC-AUC{v['roc_auc']:.6f} and Average Precision{v['average_precision']:.6f}. Confusion was TN11852,FP118,FN292,TP2738. These describe selected synthetic development performance, **not independent-test or real-world accuracy**.

Observed family strengths included A1 1467/1467, A3 255/255, S1 126/132 and N3 122/130 detections. Weaknesses included S2 11/23, S4 4/16 and **S4-only0/12**, plus A4 151/222. Family counts overlap. Nine family-support objectives remained unmet; S2/S4 were particularly sparse, and only three Validation communities limited uncertainty claims. A1/growth dependence and repeated Validation inspection further constrain interpretation.

Stage22's exploratory four-fit40-versus44 comparison improved XGBoost S2 detections11→18/23 and slightly improved aggregate MacroF1, but S4 stayed4/16 and S4-only0/12; A4 fell151→144/222. HGB44 did not improve aggregate MacroF1 or S4 recall. Stage22 remained **C — EXPERIMENT INCONCLUSIVE**. The original40-field candidate was retained to preserve the preregistered development reference; experimental44 artifacts were preserved without promotion.

Technical development verification was achieved, while independent scientific validation and real-world AML validation were not. There was no independent external audit, independent challenge evaluation, representative real mobile-money validation or production-effectiveness evidence; independent custody remained unavailable. The model supports human review of benchmark-defined patterns and cannot adjudicate criminal conduct. {DISCLAIMER}
'''
    markdown('dissertation_results_summary.md',summary)
    save('dissertation_results_summary.json',{'text':summary,'source_metrics':'ml_v4/evidence/stage18/primary_XGB_metrics.json','claims_scope':'Synthetic reused development Validation only','ready_for_use_with_limitations':True})
    modelcard={'model_name':'V4 original40 Stage18 primary_XGB','reference_version':freeze['freeze_id'],'artifact_version':'Unchanged Stage18 primary_XGB experimental pipeline; no new fitted model','intended_use':'Reproducible synthetic development research and separately authorized human-review decision-support studies','non_intended_use':['Determining that laundering/crime occurred','Autonomous financial/account/investigation actions','Production deployment or regulatory certification','Real-world accuracy/PPV assertions','Unapproved live application inference'],'feature_version':'v4.features.1','dimensions':{'semantic':40,'numeric':42},'input':'Validated causal observable history under frozen schema, not IDs/provenance as model columns','target':freeze['target'],'population':freeze['dataset']['counts'],'entity_population':{'train_wallets':1200,'train_agents':96,'train_units':12,'validation_wallets':300,'validation_agents':24,'validation_units':3},'preprocessing':freeze['preprocessing'],'threshold':freeze['threshold'],'development_metrics':v,'family_diagnostics':family_records,'known_failure_modes':[s for _,_,s in limitations],'synthetic_warning':'No production customer data or operator calibration; no real AML validation','human_review':'A score is review evidence; a person must assess context and appropriate next steps. Neither positive nor negative certifies criminality/benignity.','required_statement':DISCLAIMER,'security_integrity':freeze_hashes,'dependencies':runtime,'evaluation_status':freeze['evaluation'],'fit_attempts_cumulative':20,'reference_only':True}
    save('development_model_card.json',modelcard)
    familytable='\n'.join(f"| {f} | {r['TP']}/{r['support']} | {r['recall']:.4f} | {r['FN']} | {'Shortfall' if r['count_shortfall'] else 'Count minimum met'} |" for f,r in family_records.items())
    cardtext=f'''# V4 development model card — original40 primary_XGB

**Development reference only; no production approval.** Freeze reference `{freeze['freeze_id']}` points to the unchanged Stage18 model.

> {DISCLAIMER}

## Use and inputs

Intended for reproducible synthetic research and separately authorized human-review decision support. Not intended for autonomous account actions, regulatory certification or determining criminal intent. Input version `v4.features.1`:40 semantic fields/42 estimator columns, causal35d histories, exact roles and integer-cent aggregation; raw IDs/provenance never enter X. Train-only median imputation and scaling with fixed type one-hot; threshold **score>=0.50**. No fitted calibration.

## Population and target

Train60000 scored+14400 warm-up,1200wallets/96agents in12communities. Validation15000 scored+3600warm-up,300wallets/24agents in3communities. Entities/history disjoint. Generic synthetic Zimbabwean mobile-money assumptions, not operator-calibrated data. Target `v4.predicates.1` materialized by `{manifest['versions']['evaluator']}` is a twelve-predicate observable review-pattern union; cold-start ineligibility can produce0 without establishing benignity.

## Development results and failure modes

MacroF1{v['macro_f1']:.6f}; precision{v['positive_precision']:.6f}; recall{v['positive_recall']:.6f}; FPR{v['false_positive_rate']:.6f}; accuracy{v['accuracy']:.6f}; balancedaccuracy{v['balanced_accuracy']:.6f}; ROC-AUC{v['roc_auc']:.6f}; AP{v['average_precision']:.6f}. Confusion [[11852,118],[292,2738]]. Reused synthetic Validation, not independent test.

| Family | TP/support | Recall | FN | Original support policy |
| --- | ---: | ---: | ---: | --- |
{familytable}

Known failures include S4-only0/12, sparse S2/S4, A4/A2/N1 misses, N3 selected-route loss, growth dependence and correlated/overlapping families. No independent external audit or challenge evaluation exists; custody unavailable. No real mobile-money validation or production-effectiveness evidence. A human must review context; probability is not calibrated certainty of laundering.

## Integrity and runtime

Pipeline `{selected['pipeline']}` SHA-256 `{selected['pipeline_sha256']}`. Standalone fitted preprocessor SHA-256 `{selected['preprocessor_sha256']}`. Python3.14.3, NumPy2.4.3, scikit-learn1.9.0, XGBoost3.4.1 are recorded training pins. Freeze-observed supplementary packages: SciPy{dependencies['scipy']}, joblib{dependencies['joblib']}, threadpoolctl{dependencies['threadpoolctl']}; these are not retroactive install-lock evidence. Exact references, all feature order/markers, package qualifications and hashes are in [machine-readable card](development_model_card.json) and [candidate freeze](development_candidate_freeze.json).

Only trusted local hash-verified artifacts may later be loaded under separate authorization; the custom class is `preprocessing.FrozenPreprocessor` from the frozen source. No deserialization occurred in Stage23. Original evaluations remain SEALED_QUARANTINED/supportFAIL; Stage16T40-feature semantic alignment is not custody/support or execution approval.44 artifacts remain research-only and require a protocol amendment for future independent use.
'''
    markdown('development_model_card.md',cardtext)
    changed=[name for name,h in protected.items() if sha(ROOT/name)!=h]
    assert not changed
    save('preservation_verification.json',{'status':'PASS_NAMED_SCOPE','protected_count':len(protected),'before_sha256':protected,'after_sha256':protected,'changed_paths':changed,'scope':'Inherited exact named files plus Stage22 outputs/decision. Sealed bytes unread/excluded; no full-disk preservation claim.','Stage15A_snapshot_gap_retained':True,'historical_files_modified':False})
    trade_table=[]
    for f in FAMILIES:
        x=interpretation['family_tradeoffs']['XGB'][f];h=interpretation['family_tradeoffs']['HGB'][f]
        trade_table.append(f"| {f} | {x['A_TP']}→{x['B_TP']}/{x['support']} | {h['A_TP']}→{h['B_TP']}/{h['support']} |")
    metric_table='\n'.join(f"| {label} | {v[key]:.6f} |" for label,key in [('Accuracy','accuracy'),('Balanced accuracy','balanced_accuracy'),('Macro F1','macro_f1'),('Suspicious-pattern precision','positive_precision'),('Suspicious-pattern recall','positive_recall'),('False-positive rate','false_positive_rate'),('ROC-AUC','roc_auc'),('Average Precision','average_precision')])
    limitation_table='\n'.join(f'| {i} — {topic} | {body} |' for i,topic,body in limitations)
    ref_table='\n'.join(f"| {k} | `{r['path']}` | `{r['sha256']}` |" for k,r in freeze_hashes.items() if k in ['pipeline','standalone_fitted_preprocessor','preprocessor_source','feature_specification','HGB_comparator'])
    report=f'''# MODEL V4 — STAGE 23 DEVELOPMENT MODEL FREEZE AND RESEARCH DECISION

**{DECISION}**

Retain the **original Stage18 `primary_XGB`**,40 semantic fields/42 estimator columns, threshold0.50, as the official V4 **development reference**. This is a reference/hash freeze, not a new model, production promotion or independent validation. HGB remains the comparator. All Stage21/22 experimental44 artifacts remain preserved. No model was deserialized, fitted or executed; no extraction, new diagnostics requiring prediction, tuning or data generation occurred.

## 1. Authority and evidence verification

Stage15/15A specifications;16R–16V retained-data, support, challenge and custody decisions;17/18 original feature/model evidence;19/20 diagnosis/design;21 implementation and22 comparison were reviewed through exact named public reports/evidence. **{len(protected)} protected hashes** match. Saved Stage18 primary_XGB Train/Validation metric records match Stage22 A40-XGB records exactly; the latter records exact probability reproduction. This stage checks those records and hashes without recomputing model outputs. Stage18 ledger16 and Stage22 ledger4 starts/completions remain unchanged, cumulative20, no authorized new fits. [Evidence verification](../evidence/stage23/evidence_verification.json).

## 2. Stage22 remains inconclusive

Historical decision: **C — EXPERIMENT INCONCLUSIVE**. It is not retroactively changed by this freeze.

For XGBoost,40→44 gave MacroF1 **0.956670→0.958415**, recall **0.903630→0.907921**, FPR **0.009858→0.009607**, FN **292→279**, FP **118→115**. S2 rose **11/23→18/23**, recall **0.4783→0.7826**. S4 remained **4/16** and S4-only remained **0/12**. **A4 deteriorated151/222→144/222**. The small aggregate gain does not resolve the primary S4 weakness or negate other losses.

For HGB, MacroF1 fell **0.961632→0.961164**, recall0.924752→0.922442 and FN228→235, while FP139→136. S2 improved13→16/23 but S4 stayed5/16 and exclusive S4 stayed1/12. The same S4 count masks a recovered event and a lost event, not identical predictions.

| Family | XGB40→44 TP/support | HGB40→44 TP/support |
| --- | --- | --- |
{chr(10).join(trade_table)}

These exploratory comparisons reused Validation that had already informed feature design. More direct S2/S4 components can improve policy approximation without independent confirmation or real-world benefit. Growth absolute permutation mass remains {dependence['A40-XGB']['growth_absolute_mass_share']:.1%} in the original XGB and {dependence['B44-XGB']['growth_absolute_mass_share']:.1%} in44; mass shares are method-dependent, correlated and not causal. [Stage22 interpretation](../evidence/stage23/stage22_interpretation.json).

## 3. Freeze decision and alternatives

Retaining40 preserves the candidate selected under Stage18's preregistered eligibility/FPR-within-MacroF1-tolerance rule, before the Stage19/20 redesign. HGB had higher MacroF1, but original XGB's lower FPR satisfied the frozen selection tradeoff. Stage23 neither reranks by the largest MacroF1 nor converts the later adaptive44 comparison into a new selection rule.

Promoting44 is not sufficiently justified: S2 gains are real observed development counts, but S4 is unresolved, XGB's aggregate gain is small, A4 and other families decline, and HGB does not improve aggregate MacroF1. Sparse support and absent independent evaluation apply to both versions. Retain44 as useful research evidence, not delete or devalue it.

Freezing neither would unnecessarily require another adaptive development cycle to preserve a technical research reference. The freeze instead closes current development with explicit claim limits. Additional work is essential for independent or operational claims, not for documenting the completed prototype. [Decision rationale](../evidence/stage23/representation_decision.json).

## 4. Exact frozen references

Freeze identifier: **`{freeze['freeze_id']}`**. It references the original Stage18 artifact, **not** the Stage22 A40 refit. Model bytes, filenames and application settings are unchanged.

| Reference | Existing path | SHA-256 |
| --- | --- | --- |
{ref_table}

Feature version `v4.features.1`; original ordered40 fields and42 encoded columns are recorded in [freeze record](../evidence/stage23/development_candidate_freeze.json). Threshold **score>=0.50**, seed2026092915, no fitted calibration. Preprocessing is original `preprocessing.FrozenPreprocessor`: exact marker conversion, Train-only median(empty0), no indicators, standard scaling, fixed3-type one-hot. Fitted state is embedded in the original pipeline and referenced separately; it was not recreated.

Historical runtime pins: Python3.14.3, NumPy2.4.3, scikit-learn1.9.0, XGBoost3.4.1, one worker. Current supplementary package pins are SciPy{dependencies['scipy']}, joblib{dependencies['joblib']}, threadpoolctl{dependencies['threadpoolctl']}; these are observed metadata, not a claim that Stage18 captured their wheel/install hashes. The reference freeze is not an independently validated deployment image lock. No packages or infrastructure were installed. Full runtime qualifications, interpreter hash and exact parameters are preserved in the freeze record.

Dataset identity remains `{manifest['dataset_id']}`, the Stage16R retained draw governed by Stage15+15A, generator `{manifest['versions']['generator']}`. Target semantic version `v4.predicates.1`, materialized evaluator `{manifest['versions']['evaluator']}`, temporal `v4.temporal.1`. Exact dataset-manifest, development input, target/schema/source and model hashes bind the freeze; no label or dataset version is replaced. No sealed private manifest or byte content was inspected.

## 5. Retained development results

| Validation measure | Value |
| --- | ---: |
{metric_table}

Confusion **[[11852,118],[292,2738]]**, order[[TN,FP],[FN,TP]]. Positive recall2738/3030, precision2738/2856, FPR118/11970. These are reused synthetic development Validation results, not independent-test metrics or real-world accuracy. AP means Average Precision, not trapezoidal PR area. Train metrics and full family/domain records remain available in [final metrics](../evidence/stage23/final_development_metrics.json).

| Family | TP/support | Recall | FN | Original support policy |
| --- | ---: | ---: | ---: | --- |
{familytable}

High observed A1/A3 recall and strong S1/N3 counts are bounded development strengths. Retained S2/S4 weaknesses, S4-only0/12, A4/A2/N1 misses, N3 route-summary loss and growth dependence remain. Family labels overlap and do not indicate which component caused a positive prediction. [Family register](../evidence/stage23/family_strengths_weaknesses.json).

## 6. Final limitations and levels of evidence

| Limitation | Scope |
| --- | --- |
{limitation_table}

**Technical development success:** feature correctness/parity/replay, bounded training and saved-result verification support a reproducible development reference in the documented scope.

**Independent scientific validation:** not achieved. No sufficiently supported independent challenge evaluation or independent external audit exists; custody remains unavailable.

**Real-world AML validation:** not achieved. No real operator cohort or production workflow-effectiveness evidence supports such a claim. A high synthetic score does not bridge these missing levels. [Limitations register](../evidence/stage23/limitations_register.json).

## 7. Model card and dissertation-ready summary

The [development model card](../evidence/stage23/development_model_card.md) and [machine-readable card](../evidence/stage23/development_model_card.json) specify intended/non-intended use, target/populations, schema/preprocessing, threshold, results/failure modes, hashes, dependencies and evaluation status.

> {DISCLAIMER}

Human review is required; positive means review-pattern evidence and negative does not certify benignity, including ineligible histories. The [dissertation-ready results summary](../evidence/stage23/dissertation_results_summary.md) records dataset rationale, domains, compared algorithms, retained candidate, exact Validation metrics, family strengths/weaknesses and claim limits. It explicitly identifies Validation as reused development data.

## 8. Future work, separately scoped

Future work may address representative real mobile-money data under appropriate access; S4 approximation/support; additional communities and family diversity; independent evaluation/custody; robustness; and a predeclared40-versus44 comparison on fresh data. Calibration or operational threshold design would require dedicated authorized development/calibration evidence, then freezing before untouched final evaluation—not tuning on final outcomes. None is performed or automatically authorized now. [Future-work register](../evidence/stage23/future_work_register.json).

Stage16T stays40-field. Retaining40 avoids a feature-dimension change but does not waive its custody, support, sealing, freeze or approval gates.44 would require a separately approved protocol amendment before affected evaluation. Original quarantines and public supportFAIL remain.20 attempts are consumed; the inherited36 ceiling grants no remaining authorization, and expired slots remain expired.

## 9. Preservation and final decision

{len(protected)} exact named historical/input artifacts are unchanged, including original and44 matrices/models, both fit ledgers, twelve predicates, development data/labels, V1 production and V3 integration files. Scope excludes unread sealed bytes and does not claim every file on disk. The Stage16V broader historical snapshot gap remains documented. No Flask, MySQL, API, dashboard or application-integration change occurred. Only this report, new Stage23 evidence/documents and the documentation builder were written. [Preservation](../evidence/stage23/preservation_verification.json), [artifact manifest](../evidence/stage23/artifact_hash_manifest.json).

**{DECISION}**

This final development freeze authorizes no independent evaluation, production use, new fits, additional features, threshold work, data generation or automatic next development cycle.

V4 STAGE 23 COMPLETE — WAITING FOR APPROVAL.
'''
    with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(report)
    files=list(OUT.iterdir())+[REPORT,Path(__file__)]
    outputs={p.relative_to(ROOT).as_posix():sha(p) for p in files if p.is_file()}
    save('artifact_hash_manifest.json',{'frozen_reference_hashes':freeze_hashes,'Stage21_Stage22_research_artifacts_preserved':{p:h for p,h in protected.items() if p.startswith(('ml_v4/development_features_v2/','ml_v4/development_comparison/'))},'new_output_sha256':outputs,'manifest_self_hash':'Bound by stage23_decision.json, no circular self-hash','security':'Hash references establish identity, not independent custody. No permission or OS immutability claim.'})
    outputs['ml_v4/evidence/stage23/artifact_hash_manifest.json']=sha(OUT/'artifact_hash_manifest.json')
    save('stage23_decision.json',{'decision':DECISION,'freeze_id':freeze['freeze_id'],'official_development_candidate':'Stage18 original primary_XGB','feature_version':'v4.features.1','semantic_fields':40,'estimator_columns':42,'threshold':.5,'HGB_comparator_retained':True,'Stage21_Stage22_artifacts_preserved':True,'Stage22_decision_unchanged':'C — EXPERIMENT INCONCLUSIVE','new_fits':0,'new_model_execution':False,'new_feature_extraction':False,'sealed_access':False,'independent_validation':False,'production_approval':False,'new_cycle_authorized':False,'protected_count':len(protected),'artifact_sha256':outputs})
    print(f'Stage23 complete: {len(protected)} protected files unchanged; {len(outputs)} output hashes; original40 candidate retained.')

if __name__=='__main__':main()
