"""Preregistered bounded development experiment; no evaluation loader."""
import os
os.environ['OMP_NUM_THREADS']='1'
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['MKL_NUM_THREADS']='1'
import ast,csv,hashlib,json,platform,sys,time,warnings
from datetime import datetime,timezone
from pathlib import Path
import joblib
import numpy as np
import sklearn
import xgboost
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier,HistGradientBoostingClassifier
from sklearn.metrics import confusion_matrix,accuracy_score,balanced_accuracy_score,f1_score,precision_score,recall_score,roc_auc_score,average_precision_score,brier_score_loss,log_loss
from threadpoolctl import threadpool_limits
from preprocessing import FrozenPreprocessor,CATEGORIES

ROOT=Path(__file__).resolve().parents[2]
EVID=ROOT/'ml_v4/evidence/stage18'
ART=ROOT/'ml_v4/development_training/artifacts'
FAMILIES='S1 S2 S3 S4 N1 N2 N3 N4 A1 A2 A3 A4'.split()
SEED=2026092915
sys.path.insert(0,str(ROOT/'ml_v4/development_features'))
from run_stage17 import peak_memory

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def save(name,obj):
    with (EVID/name).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(obj,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
def utc():return datetime.now(timezone.utc).isoformat()

def path(part,name,annotation=False):
    allowed=('family_evidence.jsonl','private_provenance.json') if annotation else ('transactions.csv','ground_truth.csv','warmup_observables.csv')
    if part not in ('train','validation') or name not in allowed:raise PermissionError('Unauthorized development input')
    p=ROOT/'ml_v4/data/development'/part/name
    if p.resolve()!=p:raise PermissionError('Redirected path')
    return p

def metrics(y,p):
    z=p>=.5;tn,fp,fn,tp=confusion_matrix(y,z,labels=[0,1]).ravel()
    bins=[]
    for i in range(10):
        m=(p>=i/10)&((p<(i+1)/10) if i<9 else p<=1)
        bins.append({'lower':i/10,'upper':(i+1)/10,'count':int(m.sum()),'mean_probability':float(p[m].mean()) if m.any() else None,'observed_positive_fraction':float(y[m].mean()) if m.any() else None})
    return {'TN':int(tn),'FP':int(fp),'FN':int(fn),'TP':int(tp),'confusion_matrix':[[int(tn),int(fp)],[int(fn),int(tp)]],
        'accuracy':float(accuracy_score(y,z)),'balanced_accuracy':float(balanced_accuracy_score(y,z)),
        'macro_f1':float(f1_score(y,z,average='macro',zero_division=0)),
        'positive_precision':float(precision_score(y,z,zero_division=0)),'precision_undefined':bool(tp+fp==0),
        'positive_recall':float(recall_score(y,z,zero_division=0)),'positive_f1':float(f1_score(y,z,zero_division=0)),
        'false_positive_rate':float(fp/(fp+tn)) if fp+tn else None,'normal_recall':float(tn/(tn+fp)) if tn+fp else None,
        'roc_auc':float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None,
        'average_precision':float(average_precision_score(y,p)) if len(np.unique(y))==2 else None,
        'brier_score':float(brier_score_loss(y,p)),'log_loss':float(log_loss(y,p,labels=[0,1])),
        'probability_quantiles':np.quantile(p,[0,.01,.25,.5,.75,.99,1]).tolist(),'calibration_bins':bins,'threshold':.5}

def rate(n,d):
    if not d:return {'numerator':n,'denominator':d,'rate':None,'wilson95':None,'reason':'empty support'}
    r=n/d;z=1.96;den=1+z*z/d;c=(r+z*z/(2*d))/den;h=z*np.sqrt(r*(1-r)/d+z*z/(4*d*d))/den
    return {'numerator':int(n),'denominator':int(d),'rate':r,'wilson95':[float(c-h),float(c+h)]}

def annotations(part,ids,y):
    frows=[json.loads(s) for s in path(part,'family_evidence.jsonl',True).read_text().splitlines()]
    fmap={int(r['transaction_id']):r for r in frows}
    prov=read(str(path(part,'private_provenance.json',True).relative_to(ROOT)))
    pmap={int(r['transaction_id']):r for r in prov}
    warmup_ids={int(r['transaction_id']) for r in csv.DictReader(path(part,'warmup_observables.csv').open())}
    assert len(fmap)==len(frows)==len(ids) and len(pmap)==len(prov)
    assert set(fmap)==set(ids) and not set(ids)&warmup_ids and set(pmap)==set(ids)|warmup_ids
    masks=np.array([[f in fmap[i]['families'] for f in FAMILIES] for i in ids],dtype=bool)
    assert np.array_equal(masks.any(axis=1),y.astype(bool))
    assert all(int(fmap[i]['ground_truth_label'])==int(v) for i,v in zip(ids,y))
    # Extract only existing diagnostic annotations; never supply them to fit/predict.
    rows=[pmap[i] for i in ids]
    metadata=list(csv.DictReader((ROOT/'ml_v4/development_features/matrices'/part/'row_metadata.csv').open()))
    from stage16r_contract import time_us
    preonset=np.array([r['intended_onset'] is not None and time_us(meta['event_timestamp'])<r['intended_onset'] for r,meta in zip(rows,metadata)])
    return {'masks':masks,'unit':np.array([r['population_unit'] for r in rows]),
        'origin':np.array([r['origin'] for r in rows]),'archetype':np.array([r['archetype'] or '' for r in rows]),
        'eligible_a1':np.array([fmap[i]['eligible']['A1'] for i in ids]),
        'scenario':np.array([r['scenario_id'] or '' for r in rows]),'preonset':preonset}

def slices(y,p,a):
    z=p>=.5;masks=a['masks'];out={'families':{},'domains':{},'domain_only':{},'hard_origin_fpr':{},'units':{}}
    for j,f in enumerate(FAMILIES):out['families'][f]=rate(int((z&masks[:,j]).sum()),int(masks[:,j].sum()))
    dm=np.column_stack([masks[:,:4].any(axis=1),masks[:,4:8].any(axis=1),masks[:,8:].any(axis=1)])
    for j,d in enumerate(['structuring','network','agent']):
        mask=dm[:,j];out['domains'][d]=rate(int((z&mask).sum()),int(mask.sum()))
        alone=mask&(dm.sum(axis=1)==1);out['domain_only'][d]=rate(int((z&alone).sum()),int(alone.sum()))
    m=dm.sum(axis=1)>=2;out['multi_domain']=rate(int((z&m).sum()),int(m.sum()))
    for origin in ['H'+str(i) for i in range(1,9)]+['background']:
        m=(a['origin']==origin)&(y==0);out['hard_origin_fpr'][origin]=rate(int((z&m).sum()),int(m.sum()))
    m=a['preonset']&(y==0);out['pre_onset_union_target0_fpr']=rate(int((z&m).sum()),int(m.sum()))
    for unit in np.unique(a['unit']):
        m=a['unit']==unit
        out['units'][str(unit)]={'recall':rate(int((z&m&(y==1)).sum()),int((m&(y==1)).sum())),
            'fpr':rate(int((z&m&(y==0)).sum()),int((m&(y==0)).sum())),
            'families':{f:rate(int((z&m&masks[:,j]).sum()),int((m&masks[:,j]).sum())) for j,f in enumerate(FAMILIES)}}
    out['type_specific_fpr']='Recorded in shortcut slices'
    out['domain_fpr']='Single union classifier has one FPR; no domain-specific predicted heads. Report domain-only recall and origin-slice union-target0 FPR.'
    return out

def make(family,seed,names,markers,mode='full',dropped=None,only=None):
    if family=='LR':est=LogisticRegression(C=1.0,max_iter=2000,solver='lbfgs',random_state=seed)
    elif family=='RF':est=RandomForestClassifier(n_estimators=160,max_depth=None,min_samples_leaf=2,max_features='sqrt',random_state=seed,n_jobs=1)
    elif family=='HGB':est=HistGradientBoostingClassifier(max_iter=200,learning_rate=.07,max_leaf_nodes=31,min_samples_leaf=20,l2_regularization=1,early_stopping=False,random_state=seed)
    elif family=='XGB':est=xgboost.XGBClassifier(n_estimators=200,max_depth=5,learning_rate=.07,min_child_weight=5,subsample=1,colsample_bytree=1,reg_lambda=1,tree_method='hist',n_jobs=1,random_state=seed,eval_metric='logloss')
    else:raise ValueError(family)
    return Pipeline([('preprocess',FrozenPreprocessor(names,markers,mode,dropped,only)),('model',est)])

def main():
    if EVID.exists() or ART.exists():raise FileExistsError('No overwrite or automatic retry')
    spec=read('ml_v4/design/v4_feature_spec.json');names=tuple(f['name'] for f in spec['features'])
    markers={f['name']:(-1 if f['missing_semantics'].startswith('-1') else -3) for f in spec['features'] if f['missing_semantics'].startswith(('-1','-3'))}
    previous=read('ml_v4/evidence/stage17/stage17_decision.json')
    expected=dict(previous['artifact_sha256'])
    expected.update(read('ml_v4/evidence/stage17/preservation_verification.json')['final_after'])
    v1='ml/stage14/stage14_frozen_model.pkl';expected[v1]=read('ml_v4/design/amendments/v4_stage15a_manifest.json')['protection']['before'][v1]
    manifest=read('ml_v4/evidence/stage16r/dataset_manifest.json')
    for part in ['train','validation']:
        for filename in ['family_evidence.jsonl','private_provenance.json']:
            p=path(part,filename,True);expected[p.relative_to(ROOT).as_posix()]=manifest['development_sha256'][part][filename]
    expected['ml_v4/evidence/stage17/stage17_decision.json']=sha(ROOT/'ml_v4/evidence/stage17/stage17_decision.json')
    for n,h in expected.items():
        if '/data/' in n and not n.startswith(('ml_v4/data/development/train/','ml_v4/data/development/validation/')):raise PermissionError(n)
        if sha(ROOT/n)!=h:raise ValueError('Input hash mismatch: '+n)
    data={};ann={}
    for part,n in [('train',60000),('validation',15000)]:
        folder=ROOT/'ml_v4/development_features/matrices'/part
        if folder.resolve()!=folder:raise PermissionError('Redirected matrices')
        x=np.load(folder/'X.npy',allow_pickle=False);y=np.load(folder/'y.npy',allow_pickle=False)
        assert len(x)==len(y)==n and x.dtype.names==names and y.dtype==np.uint8
        for i,name in enumerate(names):assert x.dtype[name]==np.dtype('U16' if i==1 else '<f8')
        ids=[int(r['transaction_id']) for r in csv.DictReader((folder/'row_metadata.csv').open())]
        labels=list(csv.DictReader(path(part,'ground_truth.csv').open()))
        assert ids==[int(r['transaction_id']) for r in labels] and np.array_equal(y,[int(r['ground_truth_label']) for r in labels])
        assert len(set(ids))==n
        data[part]=(x,y);ann[part]=annotations(part,ids,y)
    EVID.mkdir(parents=True);ART.mkdir(parents=True)
    save('input_verification.json',{'status':'PASS','before_sha256':expected,'matrix_schema':'39 float64 + U16 type, frozen exact order','alignment':'IDs/order/labels/family union PASS; provenance extra IDs equal permitted warmup IDs exactly','scope':'Only Train/Validation; annotations diagnostics only','external_audit':False,'preflight_implementation_correction':'Initial diagnostic join incorrectly expected provenance to contain scored rows only. Corrected before plan freeze/first fit; no input bytes changed and no fit consumed.'})
    configs={f:make(f,SEED,names,markers).get_params()['model'].get_params() for f in ['LR','RF','HGB','XGB']}
    # XGBoost exposes NaN missing as a default parameter; represent it explicitly in JSON.
    configs=json.loads(json.dumps(configs,default=str).replace('NaN','null'))
    plan={'frozen_utc':utc(),'authorization':'Stage18 explicit development-only fit/compare; no challenge/evaluation/deployment',
        'max_fits':36,'planned_fits':16,'comparative':configs,'seed':SEED,'threshold':.5,
        'preprocessing':'Exact markers -> NaN per field; Train-only median imputer (empty=0), no indicators; deterministic type one-hot in declared order; Train-only standard scaling for all estimators.',
        'categories':CATEGORIES,'full_numeric_columns':42,'weights':'Natural rows; no class weighting or resampling',
        'diagnostics':{'dominant_removal':'4 fits; each candidate remove its highest absolute mean permutation-AP feature; frozen tie schema order',
            'missingness_only':'1 HGB fit with 39 numeric missing-marker indicators',
            'dominant_only':'1 HGB fit with its dominant semantic field',
            'tiny_set':'1 HGB fit on four A1 primitives growth/distinct/newcount/newshare',
            'shuffle':'1 HGB with Train y permutation seed+99 only',
            'seed_repeats':'4 full fits with seed+1; never selectable'},
        'selection':{'eligibility':'Validation macroF1>=0.80, recall>=0.65, FPR<=0.10; every domain recall>=0.60; S3/N2/A1 recall>=0.60; every H-stratum with >=100 negatives FPR<=0.20; Train minus Validation macroF1<=0.08; repeat absolute macroF1 change<=0.03; no unresolved technical failure/warnings.',
            'rank':'Among eligible primary models: maximum macroF1; within 0.005 of best choose lowest FPR, then highest minimum domain recall, then shortest fit seconds, then lexical ID.',
            'meaning':'Predeclared synthetic development triage tolerances, not original support gates or independent/operational acceptance. Sparse family recalls reported, never certified.'},
        'permutation':'All 4 primary models; same uniform 3000 Validation indices seed2026092915, 3 paired shuffles seed2026092916, semantic type jointly, one worker; AP baseline same sample.',
        'unused_slots':'20 remaining expire; no adaptive fits, threshold search, early stopping on Validation, calibration or Train+Validation refit.',
        'versions':{'python':platform.python_version(),'numpy':np.__version__,'sklearn':sklearn.__version__,'xgboost':xgboost.__version__},
        'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ROOT/'ml_v4/development_training/preprocessing.py']}}
    save('frozen_training_plan.json',plan)
    full=FrozenPreprocessor(names,markers);raw,columns=full.raw(data['train'][0]);assert raw.shape==(60000,42)
    # No fitting in this interface/sentinel fixture; synthetic structured row copied from allowed X.
    probe=data['train'][0][:1].copy();probe['wallet_prior_funding_residual_minor_24h']=-1;probe['agent_top2_share_change_24h']=-1;probe['agent_cash_value_skew_change']=-2
    out,cols=full.raw(probe)
    for n,v in [('wallet_prior_funding_residual_minor_24h',-1),('agent_top2_share_change_24h',-1),('agent_cash_value_skew_change',-2)]:assert out[0,cols.index(n)]==v
    for n,m in markers.items():probe[n]=m
    out,_=full.raw(probe)
    assert all(np.isnan(out[0,cols.index(n)]) for n in markers)
    save('preprocessing_specification.json',{'markers_to_missing':markers,'NaN_field':'wallet_prior_funding_residual_minor_24h','valid_negative_values_preserved':True,'columns':columns,'count':len(columns),'fit_partition':'Train only','median_and_scale_fit_per_pipeline':True,'no_indicators_in_full_model':True,'schema_and_marker_fixture':'PASS'})
    results={};pipes={};counter=0;ledger=EVID/'fit_ledger.jsonl'
    def log(record):
        with ledger.open('a',encoding='utf-8') as f:f.write(json.dumps(record,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    def fit(id,fam,seed=SEED,mode='full',dropped=None,only=None,shuffle=False):
        nonlocal counter
        counter+=1
        if counter>16:raise RuntimeError('Frozen 16-fit cap exceeded')
        log({'ordinal':counter,'id':id,'state':'STARTED','utc':utc(),'family':fam,'seed':seed,'mode':mode,'dropped':dropped,'only':only,'shuffle':shuffle})
        start=time.perf_counter();pipe=make(fam,seed,names,markers,mode,dropped,only)
        try:
            x,y=data['train'];target=np.random.default_rng(SEED+99).permutation(y) if shuffle else y
            with warnings.catch_warnings(record=True) as caught,threadpool_limits(limits=1):
                warnings.simplefilter('always');pipe.fit(x,target)
            seconds=time.perf_counter()-start
            result={'id':id,'family':fam,'fit_seconds':seconds,'peak_process_working_set_bytes':peak_memory(),'warnings':[str(w.message) for w in caught],
                'preprocessing_columns':pipe.named_steps['preprocess'].output_columns_,'train_rows_fitted':pipe.named_steps['preprocess'].n_train_rows_}
            for part,(xx,yy) in data.items():
                with threadpool_limits(limits=1):p=pipe.predict_proba(xx)[:,1]
                assert np.isfinite(p).all() and ((p>=0)&(p<=1)).all()
                np.save(ART/(id+'_'+part+'_probabilities.npy'),p,allow_pickle=False)
                result[part]=metrics(yy,p);result[part+'_slices']=slices(yy,p,ann[part])
            joblib.dump(pipe,ART/(id+'_EXPERIMENTAL.joblib'))
            if id.startswith('primary_'):
                saved=joblib.load(ART/(id+'_EXPERIMENTAL.joblib'))
                with threadpool_limits(limits=1):assert np.array_equal(saved.predict_proba(data['validation'][0][:100])[:,1],pipe.predict_proba(data['validation'][0][:100])[:,1])
            result['artifact_sha256']=sha(ART/(id+'_EXPERIMENTAL.joblib'))
            results[id]=result;pipes[id]=pipe
            save(id+'_metrics.json',result)
            log({'ordinal':counter,'id':id,'state':'COMPLETE','utc':utc(),'fit_seconds':seconds,'peak_process_working_set_bytes':result['peak_process_working_set_bytes'],'warnings':result['warnings']})
            print(id+' COMPLETE '+str(round(seconds,2))+'s',flush=True)
        except Exception as e:
            log({'ordinal':counter,'id':id,'state':'FAILED','utc':utc(),'error':repr(e),'seconds':time.perf_counter()-start});raise
    for fam in configs:fit('primary_'+fam,fam)
    rng=np.random.default_rng(2026092915);idx=rng.choice(15000,3000,replace=False)
    np.save(ART/'permutation_validation_indices.npy',idx,allow_pickle=False)
    permutations=[np.random.default_rng(2026092916+i).permutation(3000) for i in range(3)]
    imports={};dominant={};x=data['validation'][0][idx];y=data['validation'][1][idx]
    for fam in configs:
        pipe=pipes['primary_'+fam]
        with threadpool_limits(limits=1):base=float(average_precision_score(y,pipe.predict_proba(x)[:,1]))
        drops=[]
        for name in names:
            values=[]
            for perm in permutations:
                xp=x.copy();xp[name]=x[name][perm]
                with threadpool_limits(limits=1):ap=average_precision_score(y,pipe.predict_proba(xp)[:,1])
                values.append(float(base-ap))
            drops.append({'name':name,'mean_ap_drop':float(np.mean(values)),'repeat_sd':float(np.std(values,ddof=1)),'drops':values})
        order=sorted(range(40),key=lambda i:(-abs(drops[i]['mean_ap_drop']),i));mass=sum(abs(r['mean_ap_drop']) for r in drops)
        dominant[fam]=names[order[0]]
        groups={g:sum(abs(drops[i]['mean_ap_drop']) for i,f in enumerate(spec['features']) if f['group']==g)/mass if mass else None for g in {f['group'] for f in spec['features']}}
        imports[fam]={'baseline_sample_ap':base,'features':drops,'dominant':dominant[fam],'group_absolute_mass_shares':groups,
            'top_shares':{str(k):sum(abs(drops[i]['mean_ap_drop']) for i in order[:k])/mass if mass else None for k in [1,3,5]},
            'sample_family_support':{f:int(ann['validation']['masks'][idx,j].sum()) for j,f in enumerate(FAMILIES)}}
        print('Permutation '+fam+' complete',flush=True)
    save('permutation_importance.json',imports)
    for fam in configs:fit('remove_'+fam,fam,dropped=dominant[fam])
    fit('missingness_HGB','HGB',mode='missingness')
    fit('dominant_only_HGB','HGB',only=[dominant['HGB']])
    fit('tiny_A1_HGB','HGB',only=['agent_wallet_growth_ratio_7d','agent_distinct_wallets_7d','agent_new_wallet_count_7d','agent_new_wallet_share_7d'])
    fit('shuffle_HGB','HGB',shuffle=True)
    for fam in configs:fit('repeat_'+fam,fam,seed=SEED+1)
    eligible=[];reasons={}
    for fam in configs:
        id='primary_'+fam;r=results[id];v=r['validation'];s=r['validation_slices'];fail=[]
        for condition,label in [(v['macro_f1']>=.8,'macro_f1'),(v['positive_recall']>=.65,'recall'),(v['false_positive_rate']<=.1,'fpr'),
            (min(z['rate'] for z in s['domains'].values())>=.6,'domain_recall'),
            (min(s['families'][f]['rate'] for f in ['S3','N2','A1'])>=.6,'supported_family_recall'),
            (all(z['rate']<=.2 for k,z in s['hard_origin_fpr'].items() if k.startswith('H') and z['denominator']>=100),'hard_fpr'),
            (r['train']['macro_f1']-v['macro_f1']<=.08,'overfit_gap'),
            (abs(results['repeat_'+fam]['validation']['macro_f1']-v['macro_f1'])<=.03,'repeat_stability'),
            (not r['warnings'] and not results['repeat_'+fam]['warnings'],'unresolved_warning')]:
            if not condition:fail.append(label)
        reasons[id]=fail
        if not fail:eligible.append(id)
    chosen=None
    if eligible:
        best=max(results[i]['validation']['macro_f1'] for i in eligible)
        close=[i for i in eligible if results[i]['validation']['macro_f1']>=best-.005]
        chosen=min(close,key=lambda i:(results[i]['validation']['false_positive_rate'],-min(z['rate'] for z in results[i]['validation_slices']['domains'].values()),results[i]['fit_seconds'],i))
    save('development_selection.json',{'selected':chosen,'eligibility_failures':reasons,'eligible':eligible,'rule':'frozen_training_plan.json','final_model':False,'production_approved':False})
    save('comparison.json',{i:{k:r[k] for k in ['train','validation','fit_seconds','peak_process_working_set_bytes','warnings']} for i,r in results.items()})
    save('family_domain_diagnostics.json',{i:{'train':r['train_slices'],'validation':r['validation_slices']} for i,r in results.items() if i.startswith('primary_')})
    shortcuts={}
    for fam in configs:
        id='primary_'+fam;p=np.load(ART/(id+'_validation_probabilities.npy'));yy=data['validation'][1];xx=data['validation'][0];a=ann['validation'];z=p>=.5
        slices_out={}
        for key,m in [('a1_eligible',a['eligible_a1']),('a1_ineligible',~a['eligible_a1']),('without_A1',~a['masks'][:,8])]+[(cat,xx['transaction_type']==cat) for cat in CATEGORIES]+[('age_'+str(lo)+'_'+str(hi),(xx['agent_observed_coverage_days']>=lo)&(xx['agent_observed_coverage_days']<hi)) for lo,hi in [(0,7),(7,29),(29,35),(35,36)]]:
            slices_out[key]={'recall':rate(int((z&m&(yy==1)).sum()),int((m&(yy==1)).sum())), 'fpr':rate(int((z&m&(yy==0)).sum()),int((m&(yy==0)).sum()))}
        shortcuts[fam]={'dominant':dominant[fam],'removed_macro_f1_drop':results[id]['validation']['macro_f1']-results['remove_'+fam]['validation']['macro_f1'],
            'removed_family_recalls':results['remove_'+fam]['validation_slices']['families'],'repeat_macro_f1_change':results['repeat_'+fam]['validation']['macro_f1']-results[id]['validation']['macro_f1'],
            'conditional_slices':slices_out}
    save('shortcut_diagnostics.json',{'comparisons':shortcuts,'diagnostic_metrics':'comparison.json','limitations':['Correlated features split permutation mass; perturbations can be off-manifold','Feature removal retrains the same config but is not leakage proof','Direct target primitives legitimate and disclosed','Generator provenance used only for diagnostics; no real-world efficacy inference','Near-boundary and exact legitimate-growth mechanism slices not reconstructed; archetype is not an origin mechanism'],
        'stage17_shift_audit_reference':'ml_v4/evidence/stage17/feature_quality_audit.json'})
    after={n:sha(ROOT/n) for n in expected};assert after==expected
    save('preservation_verification.json',{'before':expected,'after':after,'changed_paths':[],'sealed_access':False,'historical_gap':'Stage15A broad snapshot still incomplete; no changes to old files.'})
    save('run_summary.json',{'fit_count':counter,'failed_fits':0,'selected':chosen,'completed_utc':utc(),'peak_working_set_bytes':peak_memory(),'plan_sha256':sha(EVID/'frozen_training_plan.json'),'decision':'A' if chosen else 'B'})
    print('Stage18 fits and diagnostics complete; report pending.',flush=True)

if __name__=='__main__':main()
