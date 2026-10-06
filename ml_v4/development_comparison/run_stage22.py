"""Four-attempt, development-only Stage22 comparison; no automatic retries."""
import os
os.environ['OMP_NUM_THREADS']='1'
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['MKL_NUM_THREADS']='1'
from pathlib import Path
from datetime import datetime,timezone
import csv,hashlib,json,platform,sys,time,warnings
import joblib
import numpy as np
import sklearn
import xgboost
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import average_precision_score
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'ml_v4/development_training'))
# Reuse frozen metric/annotation utilities only. main(), make() and fit()
# from the historical experiment are never invoked.
from run_stage18 import metrics, slices, annotations, path, peak_memory, FAMILIES
from preprocessing import FrozenPreprocessor,CATEGORIES
EVID=ROOT/'ml_v4/evidence/stage22'
ART=ROOT/'ml_v4/development_comparison/artifacts'
GRID=('A40-XGB','B44-XGB','A40-HGB','B44-HGB')

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def save(name,data):
    with (EVID/name).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(data,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
def utc():return datetime.now(timezone.utc).isoformat()
def rate(n,d):return {'numerator':int(n),'denominator':int(d),'rate':float(n/d) if d else None}
def norm(params):
    return {k:(None if isinstance(v,float) and np.isnan(v) else v) for k,v in params.items()}

def groups(keys,y,z):
    result={}
    for key in np.unique(keys):
        m=keys==key;pos=m&(y==1);neg=m&(y==0)
        result[str(key)]={'positive_support':int(pos.sum()),'negative_support':int(neg.sum()),'FN':int((pos&~z).sum()),'FP':int((neg&z).sum()),'recall':rate((pos&z).sum(),pos.sum()),'fpr':rate((neg&z).sum(),neg.sum())}
    return result

def paired(a,b,mask,y):
    a=a>=.5;b=b>=.5
    return {'support':int(mask.sum()),'A_positive':int((mask&a).sum()),'B_positive':int((mask&b).sum()),'B_detects_A_misses':int((mask&~a&b).sum()),'A_detects_B_misses':int((mask&a&~b).sum()),'both_positive':int((mask&a&b).sum()),'both_negative':int((mask&~a&~b).sum()),'B_minus_A_rate':float(((mask&b).sum()-(mask&a).sum())/mask.sum()) if mask.any() else None}

def main():
    if EVID.exists() or ART.exists():raise FileExistsError('Existing Stage22 attempt: refuse automatic restart or overwrite')
    protected=dict(read('ml_v4/evidence/stage21/preservation_verification.json')['after_sha256'])
    protected.update(read('ml_v4/evidence/stage21/stage21_decision.json')['artifact_sha256'])
    decision='ml_v4/evidence/stage21/stage21_decision.json';protected[decision]=sha(ROOT/decision)
    for name,h in protected.items():
        if '/evaluation/' in name or '/data/' in name and not name.startswith(('ml_v4/data/development/train/','ml_v4/data/development/validation/')):raise PermissionError(name)
        p=ROOT/name
        if p.resolve()!=p:raise PermissionError('Redirected input '+name)
        assert sha(p)==h,name
    for name in protected:
        if name.startswith('ml_v4/') and name.endswith(('.json','.md')):(ROOT/name).read_text(encoding='utf-8')
    oldledger=ROOT/'ml_v4/evidence/stage18/fit_ledger.jsonl'
    oldrecords=[json.loads(s) for s in oldledger.read_text().splitlines()]
    assert sum(r['state']=='STARTED' for r in oldrecords)==16
    assert sum(r['state']=='COMPLETE' for r in oldrecords)==16
    proposal=read('ml_v4/evidence/stage20/future_experimental_comparison_plan.json')
    versions={'python':platform.python_version(),'numpy':np.__version__,'sklearn':sklearn.__version__,'xgboost':xgboost.__version__}
    assert versions==proposal['versions'],versions
    spec=read('ml_v4/design/v4_feature_spec.json')
    names40=tuple(f['name'] for f in spec['features'])
    additions=read('ml_v4/evidence/stage20/minimal_feature_contract.json')['features']
    names44=names40+tuple(f['name'] for f in additions)
    markers={f['name']:(-1 if f['missing_semantics'].startswith('-1') else -3) for f in spec['features'] if f['missing_semantics'].startswith(('-1','-3'))}
    markers44=dict(markers,**{additions[i]['name']:-1 for i in (1,3)})
    data={};ann={};prechecks={}
    for part,n in [('train',60000),('validation',15000)]:
        old=ROOT/'ml_v4/development_features/matrices'/part
        new=ROOT/'ml_v4/development_features_v2/matrices'/part
        assert old.resolve()==old and new.resolve()==new
        a=np.load(old/'X.npy',allow_pickle=False);b=np.load(new/'X.npy',allow_pickle=False)
        y=np.load(old/'y.npy',allow_pickle=False)
        assert a.shape==b.shape==y.shape==(n,) and y.dtype==np.dtype('uint8')
        assert a.dtype.names==names40 and b.dtype.names==names44
        for i,name in enumerate(names44):assert b.dtype[name]==np.dtype('U16' if i==1 else '<f8')
        for name in names40:
            assert a.dtype[name]==b.dtype[name] and a[name].tobytes()==b[name].tobytes(),name
        assert sha(old/'y.npy')==sha(new/'y.npy') and sha(old/'row_metadata.csv')==sha(new/'row_metadata.csv')
        meta=list(csv.DictReader((old/'row_metadata.csv').open(encoding='utf-8')))
        ids=[int(r['transaction_id']) for r in meta]
        labels=list(csv.DictReader(path(part,'ground_truth.csv').open(encoding='utf-8')))
        assert ids==[int(r['transaction_id']) for r in labels] and np.array_equal(y,[int(r['ground_truth_label']) for r in labels])
        assert len(set(ids))==n
        data[part]={'A':a,'B':b,'y':y}
        ann[part]=annotations(part,ids,y)
        events=list(csv.DictReader(path(part,'transactions.csv').open(encoding='utf-8')))
        assert ids==[int(e['transaction_id']) for e in events]
        ann[part]['wallet']=np.array([e['sender_wallet'] if e['transaction_type']=='wallet_to_wallet' else e['serviced_wallet'] for e in events])
        ann[part]['receiver']=np.array([e['receiver_wallet'] for e in events])
        ann[part]['agent']=np.array([e['agent_id'] or 'NO_AGENT' for e in events])
        ann[part]['cluster']=np.array([('episode:'+s) if s else 'background:'+str(u)+':'+e['event_timestamp'][:10] for s,u,e in zip(ann[part]['scenario'],ann[part]['unit'],events)])
        prechecks[part]={'rows':n,'labels0_1':[int((y==0).sum()),int((y==1).sum())],'first40_byte_parity':True,'ids_order_labels_metadata_exact':True,'y_sha256':sha(old/'y.npy')}
    candidates={};raw_checks={}
    for id in GRID:
        arm=id[0];family=id.split('-')[1]
        params=dict(proposal['configurations'][family])
        if family=='XGB':
            assert params['missing'] is None
            params['missing']=np.nan
            model=xgboost.XGBClassifier(**params)
        else:model=HistGradientBoostingClassifier(**params)
        assert norm(model.get_params())==proposal['configurations'][family]
        prep=FrozenPreprocessor(names40 if arm=='A' else names44,markers if arm=='A' else markers44)
        raw,columns=prep.raw(data['train'][arm][:2])
        assert raw.shape==(2,42 if arm=='A' else 46)
        probe=data['train'][arm][:1].copy()
        for name,v in [('wallet_prior_funding_residual_minor_24h',-1),('agent_top2_share_change_24h',-1),('agent_cash_value_skew_change',-2)]:probe[name]=v
        a,cols=prep.raw(probe)
        for name,v in [('wallet_prior_funding_residual_minor_24h',-1),('agent_top2_share_change_24h',-1),('agent_cash_value_skew_change',-2)]:assert a[0,cols.index(name)]==v
        for name,v in prep.markers.items():probe[name]=v
        a,_=prep.raw(probe);assert all(np.isnan(a[0,cols.index(name)]) for name in prep.markers)
        if arm=='B':
            for i in (1,3):probe[additions[i]['name']]=0
            a,_=prep.raw(probe);assert all(a[0,cols.index(additions[i]['name'])]==0 for i in (1,3))
        candidates[id]=Pipeline([('preprocess',prep),('model',model)])
        raw_checks[id]={'unfitted_schema_marker_test':'PASS','columns':columns,'markers':prep.markers,'valid_signed_values_preserved':True,'new_baseline_zero_preserved':True,'dimension':len(columns)}
    EVID.mkdir(parents=True);ART.mkdir(parents=True)
    save('input_verification.json',{'status':'PASS','before_sha256':protected,'partitions':prechecks,'only_development':True,'Stage21_report_only_correction':'Verified final manifest includes retained executed runner; extractor and matrix hashes match','historical_snapshot_limitation':'Stage16V broader Stage15A inventory remains incomplete; no waiver','versions':versions})
    save('fit_authorization.json',{'authorization':'Explicit user Stage22: exactly four additional development-only attempts','historical_attempts':16,'new_attempt_limit':4,'cumulative_limit_this_stage':20,'inherited_ceiling':36,'expired_Stage18_slots_remain_expired':20,'replacements_allowed':False,'ledger_parent':oldledger.relative_to(ROOT).as_posix(),'ledger_parent_sha256':sha(oldledger),'no_promotion':True,'utc':utc()})
    source_paths=[Path(__file__),Path(__file__).with_name('report_stage22.py'),ROOT/'ml_v4/development_training/preprocessing.py',ROOT/'ml_v4/development_training/run_stage18.py']
    source_hashes={p.relative_to(ROOT).as_posix():sha(p) for p in source_paths}
    plan={'version':'v4.feature_comparison.1.stage22','frozen_utc':utc(),'grid':GRID,'configurations':proposal['configurations'],'serialized_missing_interpretation':'XGB missing:null restores NaN default, as documented in Stage18 serializer; other null parameters stay None. Normalized get_params equals frozen dictionaries.','seed':2026092915,'threshold':.5,'new_attempts':4,'cumulative_attempts_max':20,'preprocessing':proposal['preprocessing'],'categories':CATEGORIES,'dimensions':{'A':42,'B':46},'versions':versions,'source_sha256':source_hashes,'diagnostics':'Only Stage20 no-fit diagnostics: paired all-family/domain/negative/subject/community slices; missingness associations; fixed3000 sample and3semantic permutations with AP; no new fitted diagnostics','permutation':'Same saved Stage18 indices, verify against RNG seed2026092915; three paired row permutations seeds2026092916+i,i=0..2; each semantic field permuted before fixed preprocessing; same baseline sample','decision_interpretation':'A denotes consistent primary development improvement: for both algorithms none of S2,S4,S2-only,S4-only recall decreases and at least one S2 and one S4 contrast improves. Always disclose unionFPR/other-family tradeoffs; A is not overall superiority or promotion. B if neither algorithm improves any primary contrast; C for mixed primary directions or incomplete evidence; D for contract/access/budget failure. This descriptive interpretation is frozen before fitting, not an independent acceptance gate.','selection':'Preserve primary_XGB and HGB comparator; no model selected or promoted','reused_validation':'Exploratory, no significance or independent confirmation','support':'All nine shortfalls remain','failure':'Started attempts consumed even on failure; stop without replacements'}
    save('frozen_experiment_plan.json',plan)
    save('preprocessing_preflight.json',raw_checks)
    ledger=EVID/'fit_ledger.jsonl'
    def log(row):
        with ledger.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(row,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    results={};probs={};prep_audit={}
    for ordinal,id in enumerate(GRID,1):
        assert ordinal<=4
        # Recheck frozen source and inherited ledger before consuming each slot.
        for name,h in source_hashes.items():assert sha(ROOT/name)==h,name
        assert sha(oldledger)==read('ml_v4/evidence/stage22/fit_authorization.json')['ledger_parent_sha256']
        arm=id[0];pipe=candidates[id]
        log({'ordinal':ordinal,'cumulative_ordinal':16+ordinal,'id':id,'state':'STARTED','utc':utc(),'parent_ledger_sha256':sha(oldledger),'plan_sha256':sha(EVID/'frozen_experiment_plan.json')})
        started=time.perf_counter()
        try:
            with warnings.catch_warnings(record=True) as caught,threadpool_limits(limits=1):
                warnings.simplefilter('always')
                pipe.fit(data['train'][arm],data['train']['y'])
            elapsed=time.perf_counter()-started
            prep=pipe.named_steps['preprocess']
            assert prep.n_train_rows_==60000
            assert len(prep.output_columns_)==(42 if arm=='A' else 46)
            # Only inspect fitted state and transform/predict; no further fit.
            audit={'fit_rows':prep.n_train_rows_,'fit_partition':'train','independent_pipeline':True,'columns':prep.output_columns_,'imputer_statistics':prep.imputer_.statistics_.tolist(),'scaler_mean':prep.scaler_.mean_.tolist(),'scaler_scale':prep.scaler_.scale_.tolist(),'n_features_in':pipe.named_steps['model'].n_features_in_}
            prep_audit[id]=audit
            result={'id':id,'fit_seconds':elapsed,'peak_working_set_bytes':peak_memory(),'warnings':[str(w.message) for w in caught],'partitions':{}}
            probs[id]={}
            for part in ('train','validation'):
                x=data[part][arm];y=data[part]['y']
                with threadpool_limits(limits=1):p=pipe.predict_proba(x)[:,1]
                assert np.isfinite(p).all() and ((p>=0)&(p<=1)).all()
                probs[id][part]=p
                np.save(ART/(id+'_'+part+'_probabilities.npy'),p,allow_pickle=False)
                result['partitions'][part]={'overall':metrics(y,p),'slices':slices(y,p,ann[part])}
                if arm=='A':
                    oldp=np.load(ROOT/f'ml_v4/development_training/artifacts/primary_{id.split("-")[1]}_{part}_probabilities.npy',allow_pickle=False)
                    result['partitions'][part]['Stage18_reproduction']={'exact':bool(np.array_equal(p,oldp)),'max_abs_difference':float(np.max(np.abs(p-oldp)))}
            modelpath=ART/(id+'_EXPERIMENTAL.joblib')
            joblib.dump(pipe,modelpath)
            result['model_sha256']=sha(modelpath)
            # Read only the just-created, hash-verified local model; no prior model loading.
            saved=joblib.load(modelpath)
            with threadpool_limits(limits=1):assert np.array_equal(saved.predict_proba(data['validation'][arm][:100])[:,1],probs[id]['validation'][:100])
            results[id]=result;save(id+'_metrics.json',result)
            log({'ordinal':ordinal,'cumulative_ordinal':16+ordinal,'id':id,'state':'COMPLETE','utc':utc(),'fit_seconds':elapsed,'model_sha256':result['model_sha256'],'warnings':result['warnings']})
            print(f'{id} COMPLETE {elapsed:.3f}s',flush=True)
        except Exception as error:
            log({'ordinal':ordinal,'cumulative_ordinal':16+ordinal,'id':id,'state':'FAILED','utc':utc(),'error':repr(error)})
            raise
    save('preprocessing_audit.json',prep_audit)
    comparison={};diagnostics={}
    for family in ['XGB','HGB']:
        aid='A40-'+family;bid='B44-'+family;comparison[family]={}
        for part in ['train','validation']:
            a=probs[aid][part];b=probs[bid][part];y=data[part]['y'];m=ann[part]['masks']
            masks={f:m[:,i] for i,f in enumerate(FAMILIES)}
            masks.update({f+'-only':m[:,FAMILIES.index(f)]&(m.sum(axis=1)==1) for f in ['S2','S4']})
            masks['outside_A1_positive']=(y==1)&~m[:,8]
            masks['all_positive']=y==1;masks['all_negative']=y==0
            mm=['accuracy','balanced_accuracy','macro_f1','positive_precision','positive_recall','false_positive_rate','roc_auc','average_precision']
            comparison[family][part]={'paired':{k:paired(a,b,mask,y) for k,mask in masks.items()},'overall_B_minus_A':{k:results[bid]['partitions'][part]['overall'][k]-results[aid]['partitions'][part]['overall'][k] for k in mm},'domain_B_minus_A':{d:results[bid]['partitions'][part]['slices']['domains'][d]['rate']-results[aid]['partitions'][part]['slices']['domains'][d]['rate'] for d in ['structuring','network','agent']}}
    save('paired_comparisons.json',comparison)
    for id in GRID:
        diagnostics[id]={}
        for part in ['train','validation']:
            p=probs[id][part];z=p>=.5;y=data[part]['y'];a=ann[part];x=data[part]['B']
            missing=x[additions[1]['name']]==-1
            category={}
            for label,mask in [('new_baseline_missing',missing),('new_baseline_observed',~missing),('A1',a['masks'][:,8]),('outside_A1',~a['masks'][:,8])]:
                pos=mask&(y==1);neg=mask&(y==0)
                category[label]={'rows':int(mask.sum()),'prevalence':rate(pos.sum(),mask.sum()),'recall':rate((z&pos).sum(),pos.sum()),'fpr':rate((z&neg).sum(),neg.sum())}
            family_subjects={}
            for j,f in enumerate(FAMILIES):
                subj=a['agent'] if f.startswith('A') else a['receiver'] if f=='N1' else a['wallet']
                fm=a['masks'][:,j]
                family_subjects[f]={str(k):{'support':int((fm&(subj==k)).sum()),'TP':int((fm&(subj==k)&z).sum()),'FN':int((fm&(subj==k)&~z).sum())} for k in np.unique(subj[fm])}
            diagnostics[id][part]={'missingness_A1_slices':category,'communities':groups(a['unit'],y,z),'wallet_subjects':groups(a['wallet'],y,z),'agents_including_absence':groups(a['agent'],y,z),'episode_background_day':groups(a['cluster'],y,z),'family_subjects':family_subjects,'type_slices':groups(x['transaction_type'],y,z),'origin_slices':groups(a['origin'],y,z),'NO_AGENT_note':'Absence category, not an entity; wallet subject=sender forW2W/cashserviced; N1 receiver and agent families agent'}
    save('shortcut_error_slices.json',diagnostics)
    # Frozen no-fit permutation diagnostic, not feature search or diagnostic refit.
    idx=np.load(ROOT/'ml_v4/development_training/artifacts/permutation_validation_indices.npy',allow_pickle=False)
    assert np.array_equal(idx,np.random.default_rng(2026092915).choice(15000,3000,replace=False))
    np.save(ART/'permutation_validation_indices.npy',idx,allow_pickle=False)
    perms=[np.random.default_rng(2026092916+i).permutation(3000) for i in range(3)]
    importance={};start=time.perf_counter()
    for id in GRID:
        arm=id[0];pipe=candidates[id];x=data['validation'][arm][idx];y=data['validation']['y'][idx]
        with threadpool_limits(limits=1):baseline=float(average_precision_score(y,pipe.predict_proba(x)[:,1]))
        drops=[]
        for name in x.dtype.names:
            values=[]
            for perm in perms:
                xp=x.copy();xp[name]=x[name][perm]
                with threadpool_limits(limits=1):ap=float(average_precision_score(y,pipe.predict_proba(xp)[:,1]))
                values.append(baseline-ap)
            drops.append({'name':name,'mean_ap_drop':float(np.mean(values)),'repeat_sd':float(np.std(values,ddof=1)),'drops':values})
        mass=sum(abs(v['mean_ap_drop']) for v in drops)
        groupnames={f['name']:f['group'] for f in spec['features']}
        groupnames.update({f['name']:'wallet' for f in additions})
        importance[id]={'baseline_sample_ap':baseline,'features':drops,'growth_absolute_mass_share':next(abs(v['mean_ap_drop'])/mass for v in drops if v['name']=='agent_wallet_growth_ratio_7d') if mass else None,'four_added_absolute_mass_share':sum(abs(v['mean_ap_drop']) for v in drops if v['name'] in names44[40:])/mass if mass else None,'group_absolute_mass_shares':{g:sum(abs(v['mean_ap_drop']) for v in drops if groupnames[v['name']]==g)/mass if mass else None for g in set(groupnames.values())},'sample_family_support':{f:int(ann['validation']['masks'][idx,j].sum()) for j,f in enumerate(FAMILIES)},'no_fit':True,'caution':'Correlated components and off-manifold permutations; normalization changes with added fields; not causal importance'}
        print('No-fit permutation '+id+' complete',flush=True)
    save('permutation_component_dependence.json',importance)
    save('runtime_resource_usage.json',{'versions':versions,'platform':platform.platform(),'fit_seconds':{k:v['fit_seconds'] for k,v in results.items()},'permutation_seconds':time.perf_counter()-start,'peak_process_working_set_bytes':peak_memory(),'peak_scope':'Windows process lifetime including all four retained pipelines, matrices, annotations and permutations; not per-model marginal memory','threads':1})
    records=[json.loads(s) for s in ledger.read_text().splitlines()]
    assert len([r for r in records if r['state']=='STARTED'])==4 and len([r for r in records if r['state']=='COMPLETE'])==4
    save('fit_budget_verification.json',{'historical_started':16,'new_started':4,'new_completed':4,'new_failed':0,'cumulative_started':20,'inherited_ceiling':36,'remaining_authorized_attempts':0,'parent_ledger_sha256':sha(oldledger),'new_ledger_sha256':sha(ledger),'expired_slots_not_reopened':True})
    changed=[n for n,h in protected.items() if sha(ROOT/n)!=h];assert not changed
    save('preservation_verification.json',{'protected_count':len(protected),'before_sha256':protected,'after_sha256':protected,'changed_paths':changed,'sealed_bytes_excluded':True,'historical_snapshot_gap_retained':True,'source_frozen_during_experiment':all(sha(ROOT/n)==h for n,h in source_hashes.items())})
    print('Four-fit experiment and diagnostics complete. No further fits authorized.',flush=True)

if __name__=='__main__':main()
