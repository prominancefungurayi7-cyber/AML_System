"""Fixed Stage 13 comparison. Frozen 32 columns plus six experimental descriptors."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'): os.environ.setdefault(key,'2')
import csv,json,time,warnings,sys
from datetime import datetime,timezone
import numpy as np
import joblib,sklearn,xgboost
from sklearn.base import clone
from sklearn.inspection import permutation_importance
from threadpoolctl import threadpool_limits
from stage10a_contract import NAMES,FEATURES
from stage10a_pipeline import PUBLIC_FIELDS
from run_stage11 import load_matrices
from stage12_robustness import metadata
from stage13_robustness_improvement import *

R=ROOT/'reports'; M=ROOT/'models/stage13_candidates'; E=ROOT/'evidence/stage13'; SEED=20260928
ALL_NAMES=list(NAMES)+NEW_NAMES
DOMAINS=[f[1] for f in FEATURES]+[f['domain'] for f in NEW_FEATURES]
MARKERS=[f[7] for f in FEATURES]+[f['marker'] for f in NEW_FEATURES]
def read(name): return json.loads((R/name).read_text(encoding='utf-8'))
def save(name,obj): write(R/('stage13_'+name+'.json'),obj)
def utc(): return datetime.now(timezone.utc).isoformat()
def finite_config(obj):
    if isinstance(obj,dict): return {k:finite_config(v) for k,v in obj.items()}
    if isinstance(obj,(list,tuple)): return [finite_config(v) for v in obj]
    if isinstance(obj,float) and not np.isfinite(obj): return str(obj)
    return obj

def representations():
    cols=list(range(32)); graph=list(range(32,35)); cash=list(range(35,38))
    return {'R0':cols,'R1':cols+graph,'R2':cols+cash,'R3':cols+graph+cash,
            'R4':[i for i in cols+graph+cash if i!=22], 'R5':[i for i in cols+graph+cash if i not in (22,23)],
            'R0_no_growth':[i for i in cols if i!=22], 'R1_no_growth':[i for i in cols+graph if i!=22],
            'R2_no_growth':[i for i in cols+cash if i!=22]}

def importance(model,x,y,columns):
    with threadpool_limits(limits=2):
        p=permutation_importance(model,x[:,columns],y,scoring='average_precision',n_repeats=3,random_state=SEED,max_samples=3000,n_jobs=1)
    mass=np.abs(p.importances_mean); total=float(mass.sum()); order=np.argsort(-mass)
    return {'method':'Validation permutation drop in AP, three repeats, max_samples=3000, random_state=20260928; raw inputs',
            'values':dict(zip([ALL_NAMES[i] for i in columns],map(float,p.importances_mean))),
            'std':dict(zip([ALL_NAMES[i] for i in columns],map(float,p.importances_std))),
            'top_feature':ALL_NAMES[columns[int(order[0])]],'top_share':float(mass[order[0]]/total) if total else 0,
            'top3_share':float(mass[order[:3]].sum()/total) if total else 0,'top5_share':float(mass[order[:5]].sum()/total) if total else 0,
            'domain_mass':{d:float(sum(mass[j] for j,i in enumerate(columns) if DOMAINS[i]==d)/total) if total else 0 for d in ('current','structuring','network','agent','coverage','new_N3','new_A4')},
            'caveat':'Absolute mass includes negative permutation values. Correlation and sampling affect shares; noncausal diagnostic, reused Validation.'}

def selection(results,deps,imps,reference):
    ref=reference; refimp=imps['hgb_R0']; accepted=[]; checks={}
    for name,v in results.items():
        if v['representation'] not in ('R1','R2','R3'): continue
        d=deps[name]; imp=imps[name]; m=v['validation']; r=ref['validation']
        gates={'macro_f1':m['macro_f1']>=r['macro_f1']-.015,'recall':m['suspicious_recall']>=r['suspicious_recall']-.03,
               'f1':m['suspicious_f1']>=r['suspicious_f1']-.025,'ap':m['average_precision']>=r['average_precision']-.02,
               'fpr':m['false_positive_rate']<=r['false_positive_rate']+.01,
               'N3':v['families']['N3']['recall']>=ref['families']['N3']['recall']+.10,
               'A4':v['families']['A4']['recall']>=ref['families']['A4']['recall']+.03,
               'H1':v['normal_fpr']['H1']['false_positive_rate']<=ref['normal_fpr']['H1']['false_positive_rate']+.02,
               'H5':v['normal_fpr']['H5']['false_positive_rate']<=ref['normal_fpr']['H5']['false_positive_rate']+.02,
               'domain_only':all(v['domain_independence'][dom+'_only']['recall']>=ref['domain_independence'][dom+'_only']['recall']-.03 for dom in ('structuring','network','agent')),
               'dependence':d['dependence_index']<.15 and d['dependence_index']<=.3186943620178042-.05,
               'top_share':imp['top_share']<=.50 and imp['top_share']<=refimp['top_share']-.10,
               'top3_share':imp['top3_share']<=refimp['top3_share']+.05,'top5_share':imp['top5_share']<=refimp['top5_share']+.05,
               'gap':v['generalization_gap']<=.04}
        checks[name]=gates
        if all(gates.values()): accepted.append(name)
    accepted.sort(key=lambda n:(deps[n]['dependence_index'],-min(results[n]['families'][f]['recall'] for f in ('N3','A4')),results[n]['normal_fpr']['H1']['false_positive_rate']+results[n]['normal_fpr']['H5']['false_positive_rate'],-results[n]['validation']['macro_f1'],n))
    serious=list(checks)
    if accepted: decision='A'; reason='All preregistered gates passed.'
    elif any(results[n]['validation']['macro_f1']>=ref['validation']['macro_f1']+.002 and all(results[n]['families'][f]['recall']>=ref['families'][f]['recall'] for f in ('N3','A4')) and (deps[n]['dependence_index']>=.15 or imps[n]['top_share']>.5) for n in serious):
        decision='B'; reason='At least one added-feature model improves aggregate Macro F1 by >=.002 without worse N3/A4 recall, but high/extreme dependence or top-feature concentration remains.'
    elif any(checks[n]['dependence'] and not all(checks[n][k] for k in ('macro_f1','recall','f1','ap','fpr')) for n in serious): decision='C'; reason='Reduced dependence exists but fails aggregate tradeoff gates.'
    elif all(not(checks[n]['N3'] and checks[n]['A4']) for n in serious): decision='D'; reason='No candidate meets both preregistered weak-family improvement gates.'
    else: decision='E'; reason='No candidate meets all robustness gates; other preregistered decision conditions do not apply.'
    labels={'A':'ROBUSTNESS IMPROVED; READY FOR FINAL CANDIDATE/THRESHOLD SELECTION','B':'AGGREGATE PERFORMANCE IMPROVED BUT FEATURE CONCENTRATION REMAINS','C':'FEATURE DEPENDENCE IMPROVED BUT PERFORMANCE TRADEOFF IS TOO LARGE','D':'N3/A4 REPRESENTATION REMAINS LIMITING','E':'NO JUSTIFIED IMPROVEMENT; RETAIN STAGE 11 REFERENCE'}
    return {'decision':decision,'label':labels[decision],'reason':reason,'gates':checks,'eligible_candidates':accepted,'recommended_for_later_selection':accepted[0] if accepted else None,'stage11_reference_retained':not bool(accepted),'no_final_model':True}

def main():
    started=utc(); timer=time.monotonic()
    assert not M.exists() and not (R/'stage13_plan.json').exists(),'Existing Stage 13 evidence must be preserved.'
    before=read('stage13_protection_before.json'); assert compare(before,snapshot())['result']=='PASS'
    data=load_matrices(); old=ROOT/'models/stage11_candidates'
    bases={family:joblib.load(old/(name+'.joblib')).named_steps['model'] for family,name in [('hgb',REFERENCE),('xgb','s11_15_xgboost')]}
    reps=representations(); specs=[]
    reuse={'hgb_R0':'Stage11 reference','xgb_R0':'Stage11 shortlisted balanced XGBoost','hgb_R0_no_growth':'Stage12 ablation B'}
    for family in bases:
        for rep,cols in reps.items(): specs.append({'name':family+'_'+rep,'family':family,'representation':rep,'columns':[ALL_NAMES[i] for i in cols],'reuse':reuse.get(family+'_'+rep)})
    plan={'saved_at_utc':utc(),'authorization':'User explicitly allowed frozen development observable transactions and diagnostic metadata on this turn. Train/Validation only; no holdouts.',
          'new_fit_count':15,'maximum_fits':24,'seed':SEED,'threshold':.5,'candidate_features':NEW_FEATURES,'configurations':{k:finite_config(v.get_params(deep=False)) for k,v in bases.items()},
          'weights':{'hgb':'Train sample weights: positive1.5, negative1','xgb':'Saved Stage11 balanced scale_pos_weight=39781/20219; no additional sample weights'},
          'representations':{k:[ALL_NAMES[i] for i in v] for k,v in reps.items()},'candidates':specs,'serious_candidates':'R0/R1/R2/R3 per family; only R1/R2/R3 eligible for added-feature recommendation. Every serious model has matched retraining without growth.',
          'metrics':'Accuracy, balanced accuracy, Macro F1, suspicious precision/recall/F1, normal recall, AP, ROC-AUC, FPR, confusion; domains, all12 families, all normal slices, domain-only and unique multidomain union; Train-Val Macro F1 gap.',
          'dependence_rule':'Stage12 index=max(0, drops in Macro F1, recall, F1, AP, increase in FPR). LOW <.02; MODERATE [.02,.05); HIGH [.05,.15); EXTREME >=.15. Full-versus-matched-retrained removal within each family/representation.',
          'selection_gates':{'aggregate_relative_to_reference':{'macro_f1_min_delta':-.015,'recall_min_delta':-.03,'f1_min_delta':-.025,'ap_min_delta':-.02,'fpr_max_delta':.01},'N3_min_recall_delta':.10,'A4_min_recall_delta':.03,'H1_H5_max_FPR_delta':.02,'each_domain_only_min_recall_delta':-.03,'dependence_index_below':.15,'dependence_reduction_vs_stage12_at_least':.05,'top_share_max':.5,'top_share_reduction_at_least':.10,'top3_top5_max_share_delta':.05,'train_validation_macro_gap_max':.04},
          'selection_order':'All gates required. Eligible candidates ordered by lower dependence, larger minimum N3/A4 recall, lower H1+H5 FPR, higher Macro F1, name. No hidden weighted score. S2/S4 excluded.',
          'decision_order':'A if eligible; otherwise B if >=.002 Macro F1 gain and no N3/A4 loss but dependence>=.15 or top share>.5; otherwise C if dependence gate passes but aggregate tradeoffs fail; otherwise D if every candidate fails the joint N3/A4 improvement gates; otherwise E retain reference.',
          'importance':'Same permutation-AP method: three repeats, fixed seed20260928, 3000 Validation rows, n_jobs1. Raw values, absolute mass shares. Computed for all eight serious R0-R3 models.',
          'stop_conditions':['Stop after exactly15 new fits; no adaptive additions','Abort on protection mismatch, input/ID/range/causality failure or fit failure','No threshold/calibration search, Train+Val fit, final freeze or application integration','Preserve Stage9/10A/11/12 evidence and all raw inputs'],
          'source_hashes':{n:sha(ROOT/'src'/n) for n in ('stage13_robustness_improvement.py','run_stage13.py')},
          'test_source_sha256':sha(ROOT/'tests/test_stage13_features.py'),
          'environment':{'python':sys.version,'numpy':np.__version__,'sklearn':sklearn.__version__,'xgboost':xgboost.__version__,'joblib':joblib.__version__,'threads':2}}
    save('plan',plan); (R/'stage13_plan.sha256').write_text(sha(R/'stage13_plan.json')+'\n',encoding='ascii')
    M.mkdir(parents=True); E.mkdir(parents=True,exist_ok=False)
    (M/'README.md').write_text('Stage 13 experimental development candidates. R4/R5 and *_no_growth are diagnostics only. No final model or official feature promotion. Threshold 0.50.\n',encoding='utf-8')
    matrices={}; feature_record={'definitions':NEW_FEATURES,'count':6,'official_feature_count':32,'candidate_max_count':38,'partitions':{},'temporal_rule':'Strict timestamp/integer ID keys; open lower windows; fresh state; emit before update; observable eight-field projection only.'}
    for part,(x,y,ids) in data.items():
        path=ROOT/'data/development'/part/'transactions.csv'
        with path.open(encoding='utf-8',newline='') as stream: rows=[{k:r[k] for k in PUBLIC_FIELDS} for r in csv.DictReader(stream)]
        print('Extracting candidate features:',part,flush=True)
        ri,new=extract_candidate_features(rows); ri2,new2=extract_candidate_features(rows)
        assert ri==ids==ri2 and np.array_equal(new,new2) and new.shape==(len(y),6) and np.isfinite(new).all()
        for i,f in enumerate(NEW_FEATURES):
            observed=new[:,i] if f['marker'] is None else new[new[:,i]!=f['marker'],i]
            assert (observed>=f['min']).all() and (f['max'] is None or (observed<=f['max']).all())
        np.savez_compressed(E/(part+'_candidate_features.npz'),X=new,row_ids=np.asarray(ids),feature_names=np.asarray(NEW_NAMES))
        matrices[part]=np.column_stack((x,new))
        assert np.array_equal(matrices[part][:,:32],x)
        feature_record['partitions'][part]={'rows':len(y),'new_columns':6,'repeat_extraction_exact':True,'official_values_unchanged':True,'observable_source_sha256':sha(path),'candidate_file_sha256':sha(E/(part+'_candidate_features.npz'))}
    save('candidate_features',feature_record)
    xt=matrices['train']; xv=matrices['validation']; yt=data['train'][1]; yv=data['validation'][1]
    metas={p:metadata(p,ids,y) for p,(_,y,ids) in data.items()}; meta=metas['validation']
    results={}; models={}; newfits=0
    for spec in specs:
        name=spec['name']; family=spec['family']; rep=spec['representation']; cols=reps[rep]; now=utc(); elapsed=0.; caught=[]
        if spec['reuse']:
            if name=='hgb_R0_no_growth':
                bundle=joblib.load(ROOT/'models/stage12_diagnostics/ablation_B.joblib'); model=bundle['model']; src=ROOT/'models/stage12_diagnostics/ablation_B_scores.npz'
            else: model=bases[family]; src=old/((REFERENCE if family=='hgb' else 's11_15_xgboost')+'_scores.npz')
            saved=np.load(src)
            with threadpool_limits(limits=2): pt=model.predict_proba(xt[:,cols])[:,1]; pv=model.predict_proba(xv[:,cols])[:,1]
            assert np.array_equal(pt,saved['train']) and np.array_equal(pv,saved['validation'])
        else:
            model=clone(bases[family]); t=time.monotonic()
            with warnings.catch_warnings(record=True) as caught,threadpool_limits(limits=2):
                warnings.simplefilter('always'); model.fit(xt[:,cols],yt,sample_weight=np.where(yt==1,1.5,1.) if family=='hgb' else None)
                elapsed=time.monotonic()-t; pt=model.predict_proba(xt[:,cols])[:,1]; pv=model.predict_proba(xv[:,cols])[:,1]
            newfits+=1
            joblib.dump({'model':model,'columns':spec['columns'],'status':'DEVELOPMENT ONLY; NOT FINAL','representation':rep},M/(name+'.joblib'))
        models[name]=model; np.savez_compressed(M/(name+'_scores.npz'),train=pt,validation=pv)
        results[name]={**spec,'started_at_utc':now,'fit_seconds':elapsed,'warnings':[str(w.message) for w in caught],**assess(xt,yt,xv,yv,pt,pv,meta)}
        save('candidate_results',{'status':'running','new_fit_count':newfits,'candidates':results})
        print(name,'MF1',round(results[name]['validation']['macro_f1'],5),'N3',round(results[name]['families']['N3']['recall'],4),'A4',round(results[name]['families']['A4']['recall'],4),flush=True)
    assert newfits==15
    ref=results['hgb_R0']; prior=read('stage12_reference_reproduction.json')['metrics_and_slices']
    for k in ('train','validation','domains','families','normal_fpr'): assert ref[k]==prior[k]
    reproduced=read('stage13_reference_reproduction.json'); reproduced['slice_status']='Recomputed and exactly matched Stage11/12'; reproduced['metrics_and_slices']=ref; save('reference_reproduction',reproduced)
    deps={}
    for family in bases:
        for rep in ('R0','R1','R2','R3'):
            name=family+'_'+rep; removed=family+'_'+('R4' if rep=='R3' else rep+'_no_growth')
            deps[name]={'full_candidate':name,'removed_candidate':removed,**dependence(results[name],results[removed])}
    save('growth_dependence',deps)
    imps={}
    for name in deps:
        print('Permutation AP:',name,flush=True)
        imps[name]=importance(models[name],xv,yv,reps[results[name]['representation']]); save('feature_concentration',imps)
    save('domain_independence',{n:v['domain_independence'] for n,v in results.items()})
    save('family_results',{n:v['families'] for n,v in results.items()})
    save('hard_negative_results',{n:v['normal_fpr'] for n,v in results.items()})
    shifts={}
    for part,(x,y,ids) in data.items():
        mat=matrices[part]; md=metas[part]
        slices={'overall':np.ones(len(y),bool),'target0':y==0,'target1':y==1,**md['family'],**md['domain'],**md['normal']}
        shifts[part]={ALL_NAMES[i]:{label:stats(mat[mask,i],MARKERS[i]) for label,mask in slices.items()} for i in [22,23]+list(range(32,38))}
    save('distribution_shift',{'statistics':shifts,'scope':'All summaries exclude documented column markers; slices overlap; no refit or data changes.'})
    save('selection_decision',selection(results,deps,imps,ref))
    save('candidate_results',{'status':'complete','new_fit_count':newfits,'candidates':results,'started_at_utc':started,'completed_at_utc':utc(),'wall_seconds':time.monotonic()-timer})
    save('artifact_manifest',{p.relative_to(ROOT).as_posix():sha(p) for folder in (M,E) for p in folder.iterdir() if p.is_file()})
    protection=compare(before,snapshot()); save('protection',protection); assert protection['result']=='PASS'
    print('Stage13 fixed experiment complete.',flush=True)

if __name__=='__main__': main()
