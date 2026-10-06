"""Read-only development diagnosis from saved X, y, probabilities and annotations.

No model loading, fit/predict calls, extractor, evaluator, RNG or generation.
Derived ratios below are diagnostic summaries, never new model inputs.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import json
import math
import numpy as np
from sklearn.metrics import average_precision_score,roc_auc_score

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'ml_v4/evidence/stage19'
FAMILIES='S1 S2 S3 S4 N1 N2 N3 N4 A1 A2 A3 A4'.split()
MODELS=('LR','RF','HGB','XGB')

def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(name,data):
    with (OUT/name).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(data,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
def allowed(part,name):
    if part not in ('train','validation') or name not in ('transactions.csv','ground_truth.csv','family_evidence.jsonl','private_provenance.json','warmup_observables.csv'):
        raise PermissionError('Unauthorized diagnostic input')
    p=ROOT/'ml_v4/data/development'/part/name
    if p.resolve()!=p:raise PermissionError('Redirected diagnostic input')
    return p
def rate(n,d):
    if not d:return {'numerator':int(n),'denominator':int(d),'rate':None,'wilson95':None}
    r=n/d;z=1.96;den=1+z*z/d;c=(r+z*z/(2*d))/den;h=z*math.sqrt(r*(1-r)/d+z*z/(4*d*d))/den
    return {'numerator':int(n),'denominator':int(d),'rate':float(r),'wilson95':[max(0,c-h),min(1,c+h)]}
def stats(a):
    a=np.asarray(a,dtype=float);a=a[np.isfinite(a)]
    return {'valid_n':len(a),'min_q25_median_q75_max':np.quantile(a,[0,.25,.5,.75,1]).tolist() if len(a) else None}
def feature_stats(x,mask,spec):
    result={}
    for f in spec['features']:
        name=f['name'];a=x[name][mask]
        if name=='transaction_type':result[name]={'counts':dict(Counter(a.tolist()))};continue
        sem=f['missing_semantics'];missing=np.isnan(a)
        if sem.startswith('-1'):missing|=a==-1
        if sem.startswith('-3'):missing|=a==-3
        result[name]={'rows':len(a),'missing_count':int(missing.sum()),**stats(a[~missing])}
    return result
def concentration(keys,positive,missed):
    pos=Counter(str(k) for k in keys[positive]);fn=Counter(str(k) for k in keys[missed]);total=sum(fn.values())
    rows=[{'key':k,'positive_support':pos[k],'false_negatives':v,'fn_share':v/total,'miss_rate':v/pos[k]} for k,v in sorted(fn.items(),key=lambda kv:(-kv[1],kv[0]))]
    return {'positive_groups':len(pos),'missed_groups':len(fn),'false_negatives':total,'maximum_fn_share':rows[0]['fn_share'] if rows else None,
        'top5_fn_share':sum(r['fn_share'] for r in rows[:5]) if rows else None,'top10':rows[:10]}
def confusion(y,p):
    z=p>=.5;tn=int(((y==0)&~z).sum());fp=int(((y==0)&z).sum());fn=int(((y==1)&~z).sum());tp=int(((y==1)&z).sum())
    precision=tp/(tp+fp) if tp+fp else 0;recall=tp/(tp+fn)
    return {'TN':tn,'FP':fp,'FN':fn,'TP':tp,'confusion_matrix':[[tn,fp],[fn,tp]],'macro_f1':(2*tp/(2*tp+fp+fn)+2*tn/(2*tn+fp+fn))/2,
        'positive_precision':precision,'positive_recall':recall,'false_positive_rate':fp/(fp+tn),
        'roc_auc':float(roc_auc_score(y,p)),'average_precision':float(average_precision_score(y,p))}

def main():
    if OUT.exists():raise FileExistsError('No overwrite of Stage19 evidence')
    expected=dict(read('ml_v4/evidence/stage18/preservation_verification.json')['after'])
    expected.update(read('ml_v4/evidence/stage18/stage18_decision.json')['artifact_sha256'])
    for name in ['ml_v4/evidence/stage18/stage18_decision.json','ml_v4/evidence/stage18/fit_ledger.jsonl']:
        expected[name]=sha(ROOT/name)
    for name,h in expected.items():
        if '/data/' in name and not name.startswith(('ml_v4/data/development/train/','ml_v4/data/development/validation/')):raise PermissionError(name)
        if sha(ROOT/name)!=h:raise ValueError('Hash mismatch '+name)
    OUT.mkdir(parents=True)
    save('preservation_before.json',{'sha256':expected,'started_utc':datetime.now(timezone.utc).isoformat(),'scope':'Named historical/development inputs only; sealed bytes excluded'})
    spec=read('ml_v4/design/v4_feature_spec.json');support=read('ml_v4/evidence/stage16s/development_support_review.json')
    old=read('ml_v4/evidence/stage18/family_domain_diagnostics.json')
    comparison=read('ml_v4/evidence/stage18/comparison.json');selection=read('ml_v4/evidence/stage18/development_selection.json')
    assert selection['selected']=='primary_XGB'
    ledger=[json.loads(s) for s in (ROOT/'ml_v4/evidence/stage18/fit_ledger.jsonl').read_text().splitlines()]
    assert sum(r['state']=='STARTED' for r in ledger)==16 and sum(r['state']=='COMPLETE' for r in ledger)==16
    verification={};errors={};paired={};represent={};sparse={};trace=[];synthetic={}
    for part,n in [('train',60000),('validation',15000)]:
        folder=ROOT/'ml_v4/development_features/matrices'/part
        if folder.resolve()!=folder:raise PermissionError('Matrix path redirected')
        x=np.load(folder/'X.npy',allow_pickle=False);y=np.load(folder/'y.npy',allow_pickle=False)
        assert x.dtype.names==tuple(f['name'] for f in spec['features']) and len(x)==len(y)==n
        metadata=list(csv.DictReader((folder/'row_metadata.csv').open()))
        ids=[int(r['transaction_id']) for r in metadata]
        events=list(csv.DictReader(allowed(part,'transactions.csv').open()))
        assert ids==[int(e['transaction_id']) for e in events]
        labels=list(csv.DictReader(allowed(part,'ground_truth.csv').open()))
        assert ids==[int(e['transaction_id']) for e in labels] and np.array_equal(y,[int(e['ground_truth_label']) for e in labels])
        truth={r['transaction_id']:r for r in (json.loads(s) for s in allowed(part,'family_evidence.jsonl').read_text().splitlines())}
        prov={r['transaction_id']:r for r in json.loads(allowed(part,'private_provenance.json').read_text())}
        warmup={int(r['transaction_id']) for r in csv.DictReader(allowed(part,'warmup_observables.csv').open())}
        assert set(truth)==set(ids) and set(prov)==set(ids)|warmup and not set(ids)&warmup
        truth=[truth[i] for i in ids];prov=[prov[i] for i in ids]
        masks=np.array([[f in r['families'] for f in FAMILIES] for r in truth],dtype=bool)
        assert np.array_equal(masks.any(axis=1),y.astype(bool))
        probs={m:np.load(ROOT/f'ml_v4/development_training/artifacts/primary_{m}_{part}_probabilities.npy',allow_pickle=False) for m in MODELS}
        positive=y==1;pred={m:p>=.5 for m,p in probs.items()};fn=positive&~pred['XGB'];tp=positive&pred['XGB']
        wallets=np.array([e['sender_wallet'] if e['transaction_type']=='wallet_to_wallet' else e['serviced_wallet'] for e in events])
        agents=np.array([e['agent_id'] or 'NO_AGENT' for e in events]);receivers=np.array([e['receiver_wallet'] for e in events])
        units=np.array([str(p['population_unit']) for p in prov]);days=np.array([e['event_timestamp'][:10] for e in events])
        clusters=np.array(['episode:'+p['scenario_id'] if p['scenario_id'] is not None else 'background:'+str(p['population_unit'])+':'+e['event_timestamp'][:10] for e,p in zip(events,prov)])
        origins=np.array([p['origin'] for p in prov]);roles=np.array([p['event_role'] or 'none' for p in prov]);types=x['transaction_type']
        verification[part]={}
        for model in MODELS:
            computed=confusion(y,probs[model]);prior=comparison['primary_'+model][part]
            for k,v in computed.items():
                assert v==prior[k] if isinstance(v,(list,int)) else abs(v-prior[k])<1e-12,(model,part,k)
            families={f:rate(int((pred[model]&masks[:,j]).sum()),int(masks[:,j].sum())) for j,f in enumerate(FAMILIES)}
            domains={d:rate(int((pred[model]&masks[:,j:j+4].any(axis=1)).sum()),int(masks[:,j:j+4].any(axis=1).sum())) for d,j in [('structuring',0),('network',4),('agent',8)]}
            for f,r in families.items():assert r['numerator']==old['primary_'+model][part]['families'][f]['numerator'] and r['denominator']==old['primary_'+model][part]['families'][f]['denominator']
            for d,r in domains.items():assert r['numerator']==old['primary_'+model][part]['domains'][d]['numerator'] and r['denominator']==old['primary_'+model][part]['domains'][d]['denominator']
            verification[part][model]={'metrics':computed,'families':families,'domains':domains}
        grouped={k:concentration(keys,positive,fn) for k,keys in [('wallet_subject',wallets),('current_agent_including_absence',agents),('episode_or_background_day',clusters),('community',units),('UTC_day',days)]}
        errors[part]={'union_positive_rows':int(positive.sum()),'union_false_negatives':int(fn.sum()),'families':{},'overall_concentration':grouped,
            'missed_with_A1':int((fn&masks[:,8]).sum()),'without_A1_recall':rate(int((pred['XGB']&positive&~masks[:,8]).sum()),int((positive&~masks[:,8]).sum())),
            'overlapping_fn_rows':int((fn&(masks.sum(axis=1)>1)).sum()),'sum_family_fn_memberships':int(masks[fn].sum())}
        pair={}
        for label,mask in [('positive',positive),('negative',~positive)]:
            pair[label]={'both_positive':int((mask&pred['XGB']&pred['HGB']).sum()),'both_negative':int((mask&~pred['XGB']&~pred['HGB']).sum()),
                'XGB_positive_only':int((mask&pred['XGB']&~pred['HGB']).sum()),'HGB_positive_only':int((mask&~pred['XGB']&pred['HGB']).sum())}
        pair['families']={f:{'both_miss':int((masks[:,j]&~pred['XGB']&~pred['HGB']).sum()),'HGB_detects_XGB_misses':int((masks[:,j]&~pred['XGB']&pred['HGB']).sum()),'XGB_detects_HGB_misses':int((masks[:,j]&pred['XGB']&~pred['HGB']).sum())} for j,f in enumerate(FAMILIES)}
        paired[part]=pair;sparse[part]={}
        for j,f in enumerate(FAMILIES):
            mask=masks[:,j];hit=mask&pred['XGB'];miss=mask&~pred['XGB'];subject=agents if f.startswith('A') else receivers if f=='N1' else wallets
            oldsupport=support['partitions'][part]['families'][f]
            assert int(mask.sum())==oldsupport['decision_points'] and len(set(subject[mask]))==oldsupport['distinct_subjects'] and len(set(clusters[mask]))==oldsupport['distinct_clusters']
            errors[part]['families'][f]={'support':int(mask.sum()),'TP':int(hit.sum()),'FN':int(miss.sum()),
                'exclusive_family':{'support':int((mask&(masks.sum(axis=1)==1)).sum()),'FN':int((miss&(masks.sum(axis=1)==1)).sum())},
                'overlap_among_fn':{other:int((miss&masks[:,k]).sum()) for k,other in enumerate(FAMILIES) if k!=j},
                'detected_features':feature_stats(x,hit,spec),'missed_features':feature_stats(x,miss,spec),
                'detected_probability':stats(probs['XGB'][hit]),'missed_probability':stats(probs['XGB'][miss]),
                'saved_eligibility_positive':dict(Counter(str(truth[i]['eligible'][f]) for i in np.flatnonzero(mask))),
                'concentration':{k:concentration(keys,mask,miss) for k,keys in [('subject',subject),('cluster',clusters),('unit',units),('day',days)]},
                'type_rows':{cat:{'positive':int((mask&(types==cat)).sum()),'FN':int((miss&(types==cat)).sum())} for cat in ['wallet_to_wallet','cash_in','cash_out']}}
            sparse[part][f]={'minimum':oldsupport['minimum_objective'],'actual':int(mask.sum()),'required_percent':100*int(mask.sum())/oldsupport['minimum_objective'],
                'subjects':oldsupport['distinct_subjects'],'clusters':oldsupport['distinct_clusters'],'units':oldsupport['distinct_units'],
                'selected_recall':rate(int(hit.sum()),int(mask.sum())),'maximum_positive_subject_share':oldsupport['maximum_subject_share'],'maximum_positive_cluster_share':oldsupport['maximum_cluster_share']}
        for i in np.flatnonzero(fn):
            trace.append({'partition':part,'row_index':int(i),'transaction_id':ids[i],'families':'|'.join(truth[i]['families']),
                'XGB_probability':float(probs['XGB'][i]),'HGB_probability':float(probs['HGB'][i]),'wallet_subject':wallets[i],'agent':agents[i],
                'cluster':clusters[i],'unit':units[i],'type':types[i]})
        # N3 topology-selected summaries can lose a different satisfying route.
        n3=masks[:,6];bad=n3&((x['prior_path_min_max_log_change_7d']>math.log(4))|(x['current_to_selected_path_first_value_ratio']<.25)|(x['current_to_selected_path_first_value_ratio']>1.25))
        ci=x['agent_cash_in_count_24h'];co=x['agent_cash_out_count_24h'];vi=x['agent_cash_in_value_24h'];vo=x['agent_cash_out_value_24h']
        count_skew=np.divide(co-ci,co+ci,out=np.zeros(len(x)),where=co+ci!=0)
        value_skew=np.divide(vo-vi,vo+vi,out=np.zeros(len(x)),where=vo+vi!=0)
        a4=masks[:,11]
        represent[part]={'N3':{'positive_rows':int(n3.sum()),'selected_summary_incompatible_with_target_amount_bounds':int(bad.sum()),
            'incompatible_detected':int((bad&pred['XGB']).sum()),'incompatible_missed':int((bad&~pred['XGB']).sum()),
            'all_N3_missed':int((n3&~pred['XGB']).sum()),'meaning':'Diagnostic of saved selected-path summaries only; no new path search/evaluator/model or target alteration.'},
            'A4':{label:{'rows':int(m.sum()),'cash_count':stats((ci+co)[m]),'abs_count_skew':stats(abs(count_skew[m])),
                'abs_value_skew':stats(abs(value_skew[m])),'positive_cash_out_direction':int((value_skew[m]>0).sum()),
                'all_six_recent_and_history_marker_components_present':bool(np.isfinite(vi[m]).all() and (x['agent_cash_value_skew_change'][m]!=-3).all()),
                'history_change_abs':stats(abs(x['agent_cash_value_skew_change'][m]))} for label,m in [('detected',a4&pred['XGB']),('missed',a4&~pred['XGB'])]},
            'missingness_on_family_positives':{f:{feature['name']:errors[part]['families'][f]['missed_features'][feature['name']].get('missing_count',0) for feature in spec['features'] if f in feature['related_families']} for f in FAMILIES}}
        synth={}
        for key,values in [('origin',origins),('event_role',roles),('transaction_type',types),('community',units)]:
            synth[key]={}
            for val in sorted(set(values)):
                m=values==val
                synth[key][str(val)]={'rows':int(m.sum()),'prevalence':float(y[m].mean()),'recall':rate(int((m&positive&pred['XGB']).sum()),int((m&positive).sum())),
                    'FPR':rate(int((m&~positive&pred['XGB']).sum()),int((m&~positive).sum()))}
        synthetic[part]=synth
    best=max(comparison[i]['validation']['macro_f1'] for i in selection['eligible'])
    contenders=[i for i in selection['eligible'] if comparison[i]['validation']['macro_f1']>=best-.005]
    winner=min(contenders,key=lambda i:(comparison[i]['validation']['false_positive_rate'],-min(v['rate'] for v in old[i]['validation']['domains'].values()),comparison[i]['fit_seconds'],i))
    assert winner==selection['selected']=='primary_XGB'
    save('model_results_verification.json',{'status':'PASS','partitions':verification,'saved_selection_preserved':winner,
        'selection_recheck':{'eligible':selection['eligible'],'within_0_005_macro_f1':contenders,'rule':'Original preregistered lowest FPR within MacroF1 tolerance; no new selection'},
        'source_fit_count':16,'new_fits':0,'threshold':.5,'prediction_method':'Read saved probabilities only; no model load or new scoring'})
    save('false_negative_analysis.json',errors)
    with (OUT/'false_negative_rows.csv').open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(trace[0]),lineterminator='\n');w.writeheader();w.writerows(trace)
    save('s2_s4_investigation.json',{p:{f:errors[p]['families'][f] for f in ['S2','S4']} for p in errors})
    save('xgboost_hgb_comparison.json',{'selected_candidate_unchanged':'primary_XGB','paired_fixed_threshold_counts':paired,'inference':'Paired descriptive development counts; no row-independence significance claim or post hoc candidate substitution'})
    save('representation_observations.json',{'observations':represent,'frozen_omissions':spec['representation_gaps'],'derived_ratios_status':'Audit summaries from existing fields only; no saved X changes or candidate features',
        'causal_limit':'Quantile differences and saved-label consistency cannot allocate FN causes to omitted features or individual gates.'})
    save('sparse_support_uncertainty.json',{'partitions':sparse,'nine_shortfalls_retained':['S1','S2','S4','N1','N3','N4','A2','A3','A4'],
        'unit_counts':{'train':12,'validation':3},'uncertainty':'Wilson bounds are descriptive independence-based; clustered sparse data and repeated Validation use prohibit precise generalization claims. No row bootstrap.'})
    save('synthetic_population_slices.json',{'partitions':synthetic,'interpretation':'Observed associations, not causal mechanism effects; provenance never a model input. Existing development labels retained for every origin.'})
    save('family_domain_error_analysis.json',{'models':{p:{m:{'families':r['families'],'domains':r['domains']} for m,r in part.items()} for p,part in verification.items()},
        'FN_overlap':{p:{k:errors[p][k] for k in ['union_false_negatives','overlapping_fn_rows','sum_family_fn_memberships']} for p in errors},
        'definitions':'Family recall is union-positive prediction on rows carrying that family, not family-specific output. Domains/families overlap.'})
    after={n:sha(ROOT/n) for n in expected};assert after==expected
    save('preservation_verification.json',{'before':expected,'after':after,'changed_paths':[],'new_model_fits':0,'model_artifacts_loaded':False,
        'sealed_access':False,'new_predictions_computed':False,'feature_matrices_modified':False,'historical_gap':'Stage15A broader preservation snapshot still incomplete; no repairs or manifest rewrites.'})
    print(json.dumps({'verified_models':4,'new_fits':0,'protected_files':len(expected),'validation_FN':errors['validation']['union_false_negatives'],
        'paired_validation':paired['validation'],'representation':represent['validation']['N3']}))

if __name__=='__main__':main()
