"""Bounded Stage 14 diagnosis. Exactly four exclusion fits and one shuffle fit."""
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'): os.environ.setdefault(k,'2')
import csv,json,time,warnings
from datetime import datetime,timezone
import numpy as np
import joblib,sklearn
from sklearn.base import clone
from threadpoolctl import threadpool_limits
from run_stage11 import load_matrices,metrics,recall_slice,FAMILIES
from run_stage13 import importance
from stage14_growth_diagnosis import *

def utc(): return datetime.now(timezone.utc).isoformat()

def main():
    if (R/'stage14_plan.json').exists() or M.exists(): raise FileExistsError('Preserve prior Stage 14 evidence; existing run refused')
    save('protection_before',snapshot())
    data=load_matrices(); meta={p:metadata(p,ids,y) for p,(x,y,ids) in data.items()}
    xt,yt,_=data['train']; xv,yv,_=data['validation']
    ref=joblib.load(ROOT/'models/stage11_candidates/s11_09_hist_gradient_boosting.joblib')
    estimator=ref.named_steps['model']
    plan={'saved_at_utc':utc(),'seed':SEED,'threshold':.5,'new_fit_count':5,'family_removal_maximum':4,
          'fits':{'D1':'exclude A1 positives','D2':'exclude A2 positives','D3':'exclude A4 positives','D4':'exclude every agent-positive row','shuffle':'80% of Train, with permuted labels; reserve remaining 20% of Train'},
          'shuffle_protocol':'Permute all 60000 Train labels with default_rng(20260928). Split rows by independent default_rng(20260929) permutation into 48000 fit and 12000 test rows. Score both against shuffled labels only. No Validation scores for this model.',
          'univariate_classifier':'Reuse Stage 12 top_1, fitted on Train overall target, evaluate unchanged scores in declared Validation subsets. No family-specific classifier fit or sign selection.',
          'subset_negatives':'H7, H8, and routine target0 union, with an additional agent-present/eligible view. Agent-only positives versus this same union.',
          'interactions':'Train observed quartile edges, duplicates collapsed; marker bin separate; apply unchanged to both partitions. No optimized thresholds.',
          'fixed_ratio_diagnostic':'1.5 from the frozen A1 predicate; diagnostic contingency only, not a deployment threshold.',
          'permutation':'Same Stage 13 AP permutation, 3 repeats, 3000 rows, seed20260928, one worker; RF/GB computed without fitting.',
          'estimator':estimator.get_params(),'weights':{'positive':1.5,'negative':1},'feature_names':NAMES,
          'source_hashes':{n:sha(ROOT/'src'/n) for n in ('stage14_growth_diagnosis.py','run_stage14.py')},
          'environment':{'python':os.sys.version,'numpy':np.__version__,'sklearn':sklearn.__version__,'threads':2},
          'decision':'Evidence-led diagnosis; no model selection, no dataset/label/representation changes.'}
    save('plan',plan); (R/'stage14_plan.sha256').write_text(sha(R/'stage14_plan.json')+'\n',encoding='utf-8')
    M.mkdir(); E.mkdir(parents=True)
    (M/'README.md').write_text('Stage 14 diagnostic models only. No candidate promotion. Frozen 32 inputs; threshold 0.50.\n',encoding='utf-8')
    scores={}; nog={}; top={}; primitive={}; reference_check={}
    for part,(x,y,ids) in data.items():
        scores[part]=np.load(ROOT/'models/stage11_candidates/s11_09_hist_gradient_boosting_scores.npz')[part]
        nog[part]=np.load(ROOT/'models/stage12_diagnostics/ablation_B_scores.npz')[part]
        top[part]=np.load(ROOT/'models/stage12_diagnostics/top_1_scores.npz')[part]
        with threadpool_limits(limits=2): replay=ref.predict_proba(x)[:,1]
        assert np.array_equal(replay,scores[part])
        reference_check[part]={'max_score_difference':float(np.max(abs(replay-scores[part]))),'metrics':metrics(y,replay)}
        with (ROOT/f'data/development/{part}/transactions.csv').open(encoding='utf-8',newline='') as stream: raw=list(csv.DictReader(stream))
        got,z=primitives(raw); assert got==ids and np.array_equal(z[:,0],x[:,22])
        assert np.array_equal(z[:,10].astype(bool),meta[part]['family']['A1'])
        primitive[part]=z
        np.savez_compressed(E/f'{part}_agent_primitives.npz',values=z,row_ids=np.asarray(ids),columns=np.asarray(PRIMITIVES))
        print(part,'growth and frozen A1 reconstructed exactly',flush=True)
    save('reference_reproduction',reference_check)
    distributions={}; dependence={}; overlaps={}; uni={}; comparison={}; eligibility={}; interactions={}
    edges={i:grid_bins(xt[:,i],FEATURES[i][7]) for i in list(range(20,29))+[29,30,31]}
    old_imp=read(13,'feature_concentration')['hgb_R0']
    for part,(x,y,ids) in data.items():
        m=meta[part]; g=x[:,22]; z=primitive[part]; pred=scores[part]>=.5; pn=nog[part]>=.5; ss=slices(y,m)
        distributions[part]={k:summary(g[v],-1) for k,v in ss.items()}
        lost=(y==1)&pred&~pn; gained=(y==1)&~pred&pn; a1=m['family']['A1']
        dependence[part]={'overall':{'reference_tp':int(((y==1)&pred).sum()),'no_growth_tp':int(((y==1)&pn).sum()),'lost':int(lost.sum()),'gained':int(gained.sum()),
              'net_tp_loss':int(lost.sum()-gained.sum()),'lost_in_A1':int((lost&a1).sum()),'gained_in_A1':int((gained&a1).sum()),
              'A1_fraction_of_gross_lost':float((lost&a1).sum()/lost.sum()),'A1_net_loss_divided_by_overall_net_loss':float(((lost&a1).sum()-(gained&a1).sum())/(lost.sum()-gained.sum()))},'families':{}}
        for f in ('A1','A2','A3','A4'):
            mask=m['family'][f]; a=recall_slice(mask,pred); b=recall_slice(mask,pn)
            dependence[part]['families'][f]={'reference':a,'no_growth':b,'recall_change':b['recall']-a['recall'],
              'growth':{k:summary(g[v],-1) for k,v in {'reference_TP':mask&pred,'reference_FN':mask&~pred,'no_growth_TP':mask&pn,'no_growth_FN':mask&~pn}.items()},
              'agent_family_overlap':{q:int((mask&m['family'][q]).sum()) for q in ('A1','A2','A3','A4')}}
        # Own-family onset offsets are meaningful only for that recorded private recipe.
        offsets=np.array([r['relative_own_onset_position'] if r['scenario_family']==FAMILIES['A1'] and r['relative_own_onset_position'] is not None else -999 for r in m['rows']])
        onset={}
        for label,mask in [('onset_0',offsets==0),('after_1_to_3',(offsets>=1)&(offsets<=3)),('after_4_plus',offsets>=4),('not_recorded',offsets==-999)]:
            mask=mask&a1; onset[label]={'growth':summary(g[mask],-1),'reference':recall_slice(mask,pred),'one_feature':recall_slice(mask,top[part]>=.5)}
        dependence[part]['A1_own_onset']=onset
        dependence[part]['A1_origin']={origin:{'support':int((a1&np.array([r['origin_cohort']==origin for r in m['rows']])).sum())} for origin in ('routine','hard_scenario','campaign_member')}
        overlaps[part]={f:{n:overlap(g[m['family'][f]],g[m['normal'][n]]) for n in ('H7','H8','routine')} for f in ('A1','A2','A3','A4')}
        overlaps[part]['overall']=overlap(g[y==1],g[y==0])
        negatives=m['normal']['H7']|m['normal']['H8']|m['normal']['routine']
        tasks={'overall':(np.ones(len(y),bool),y),'agent_only_vs_relevant_negatives':(m['exclusive']['agent_only']|negatives,m['exclusive']['agent_only'].astype(int))}
        for f in ('A1','A2','A4'): tasks[f+'_vs_relevant_negatives']=(m['family'][f]|negatives,m['family'][f].astype(int))
        uni[part]={}
        for name,(mask,target) in tasks.items():
            uni[part][name]={}
            for view,v in [('encoded',mask),('available',mask&(g!=-1)),('agent_present',mask&(z[:,1]>=0))]:
                uni[part][name][view]={'raw_growth':power(target[v],g[v]),'saved_top1_score_ranking':power(target[v],top[part][v]),
                                     'saved_top1_classifier':metrics(target[v],top[part][v]),'growth_target0':summary(g[v&(target==0)],-1),'growth_target1':summary(g[v&(target==1)],-1)}
        comparison[part]={}
        for i in range(20,29):
            v=np.ones(len(y),bool) if FEATURES[i][7] is None else x[:,i]!=FEATURES[i][7]
            pair=v&(g!=-1)
            comparison[part][NAMES[i]]={'encoded_power':power(y,x[:,i]),'observed_power':power(y[v],x[v,i]),'correlation_with_growth_observed':correlation(g[pair],x[pair,i]),
                  'target0':summary(x[y==0,i],FEATURES[i][7]),'target1':summary(x[y==1,i],FEATURES[i][7]),'reference_permutation_AP_drop':old_imp['values'][NAMES[i]]}
        eligibility[part]={'groups':{},'primitive_summary':{},'A1_component_contingencies':{}}
        for label,mask in [('available',g!=-1),('unavailable',g==-1),('no_agent',z[:,1]<0),('agent_observed_age_under35',(z[:,1]>=0)&(z[:,1]<35)),('age35plus_insufficient_baseline',(z[:,1]>=35)&(z[:,2]<12)),('coverage_display28',x[:,31]==28)]:
            eligibility[part]['groups'][label]={'support':int(mask.sum()),'positive':int(y[mask].sum()),'positive_rate':float(y[mask].mean()) if mask.any() else None,'growth_power':power(y[mask],g[mask])}
        for i,n in enumerate(PRIMITIVES[1:7],1):
            eligibility[part]['primitive_summary'][n]={'target0_available':summary(z[(y==0)&(g!=-1),i]),'target1_available':summary(z[(y==1)&(g!=-1),i]),'correlation_with_growth':correlation(g[g!=-1],z[g!=-1,i])}
        for label,condition in [('feature_ratio_ge1.5',g>=1.5),('implemented_ratio_ge1.5',z[:,8]>=1.5),('written_full_A1',z[:,11]==1)]:
            eligibility[part]['A1_component_contingencies'][label]={'condition_true':int(condition.sum()),'A1_true':int(a1.sum()),'both':int((condition&a1).sum()),'condition_without_A1':int((condition&~a1).sum()),'A1_without_condition':int((a1&~condition).sum()),'target0_condition':int((condition&(y==0)).sum())}
        eligibility[part]['frozen_A1_reconstruction_mismatches']=int(np.sum(z[:,10]!=a1))
        eligibility[part]['A1_growth_unavailable']=int((a1&(g==-1)).sum())
        eligibility[part]['A1_written_implementation_disagreements']=int(np.sum(z[:,10]!=z[:,11]))
        eligibility[part]['availability_indicator_power']=power(y,(g!=-1).astype(float))
        # Condition on uncapped observed age, not private activation age.
        eligibility[part]['available_age_strata']={}
        for lo,hi in [(35,60),(60,90),(90,120),(120,1000)]:
            mask=(g!=-1)&(z[:,1]>=lo)&(z[:,1]<hi)
            eligibility[part]['available_age_strata'][f'{lo}..{hi}']=power(y[mask],g[mask])
        interactions[part]={}
        gb=grid_codes(g,edges[22],-1)
        for i in list(range(20,22))+list(range(23,32)):
            if i not in edges: continue
            zb=grid_codes(x[:,i],edges[i],FEATURES[i][7]); rows=[]
            for a in sorted(set(gb)):
                for b in sorted(set(zb)):
                    mask=(gb==a)&(zb==b); n=int(mask.sum())
                    rows.append({'growth_bin':int(a),'other_bin':int(b),'support':n,'positive':int(y[mask].sum()),'positive_rate':float(y[mask].mean()) if n else None,
                         'reference_mean_score':float(scores[part][mask].mean()) if n else None,'reference_review_rate':float(pred[mask].mean()) if n else None})
            interactions[part][NAMES[i]]={'growth_edges':edges[22],'other_edges':edges[i],'rows':rows}
    for n,v in [('growth_distributions',distributions),('family_dependence',dependence),('negative_overlap',overlaps),('univariate_power',uni),('agent_feature_comparison',comparison),('eligibility_analysis',eligibility),('interactions',interactions)]: save(n,v)
    print('Descriptive diagnostics saved; starting five fixed diagnostic fits',flush=True)
    removed={}; fit_log=[]
    for name,f in [('D1','A1'),('D2','A2'),('D3','A4'),('D4','agent')]:
        exclude=meta['train']['domain']['agent'] if f=='agent' else meta['train']['family'][f]; keep=~exclude
        model=clone(estimator); start=utc(); tic=time.monotonic()
        with warnings.catch_warnings(record=True) as caught,threadpool_limits(limits=2):
            warnings.simplefilter('always'); model.fit(xt[keep],yt[keep],sample_weight=np.where(yt[keep]==1,1.5,1))
            pt=model.predict_proba(xt)[:,1]; pv=model.predict_proba(xv)[:,1]
        record=evaluate(xt,yt,xv,yv,pt,pv,meta['validation'])
        record.update(fit_subset_metrics=metrics(yt[keep],pt[keep]),train_metric_scope='train field evaluates ALL original Train rows, including excluded rows; fit_subset_metrics is actual fitted subset',
              excluded_count=int(exclude.sum()),fit_class_counts=np.bincount(yt[keep],minlength=2),excluded_family_counts={k:int((exclude&v).sum()) for k,v in meta['train']['family'].items()},
              started_at_utc=start,fit_and_score_seconds=time.monotonic()-tic,warnings=[str(w.message) for w in caught],importance=importance(model,xv,yv,list(range(32))))
        removed[name]=record; joblib.dump({'model':model,'feature_names':NAMES,'status':'DIAGNOSTIC ONLY','exclusion':f},M/f'{name}.joblib')
        np.savez_compressed(M/f'{name}_scores.npz',train=pt,validation=pv,fit_mask=keep)
        fit_log.append({'name':name,'started_at_utc':start}); save('family_removal',removed)
        print(name,'Macro F1',record['validation']['macro_f1'],'top share',record['importance']['top_share'],flush=True)
    rng=np.random.default_rng(SEED); shuffled=rng.permutation(yt)
    order=np.random.default_rng(SEED+1).permutation(len(yt)); train_idx=order[:48000]; test_idx=order[48000:]
    model=clone(estimator); start=utc()
    with warnings.catch_warnings(record=True) as caught,threadpool_limits(limits=2):
        warnings.simplefilter('always'); model.fit(xt[train_idx],shuffled[train_idx],sample_weight=np.where(shuffled[train_idx]==1,1.5,1))
        fit_p=model.predict_proba(xt[train_idx])[:,1]; test_p=model.predict_proba(xt[test_idx])[:,1]
    joblib.dump({'model':model,'feature_names':NAMES,'status':'SHUFFLE SANITY ONLY'},M/'shuffle.joblib')
    np.savez_compressed(M/'shuffle_scores.npz',shuffled_labels=shuffled,fit_indices=train_idx,test_indices=test_idx,fit_scores=fit_p,test_scores=test_p)
    save('shuffle_test',{'seed':SEED,'started_at_utc':start,'protocol':plan['shuffle_protocol'],'fit':metrics(shuffled[train_idx],fit_p),'reserved_train_test':metrics(shuffled[test_idx],test_p),
          'chance_AP_reserved':float(shuffled[test_idx].mean()),'chance_ROC_AUC':.5,'warnings':[str(w.message) for w in caught],'validation_access_for_shuffle':False})
    fit_log.append({'name':'shuffle','started_at_utc':start}); save('fit_log',fit_log)
    families={}
    for tag,name in [('hgb','s11_09_hist_gradient_boosting'),('xgb','s11_15_xgboost'),('rf','s11_27_random_forest'),('gb','s11_08_gradient_boosting')]:
        model=joblib.load(ROOT/f'models/stage11_candidates/{name}.joblib')
        s=np.load(ROOT/f'models/stage11_candidates/{name}_scores.npz')['validation']
        imp=read(13,'feature_concentration')[tag+'_R0'] if tag in ('hgb','xgb') else importance(model,xv,yv,list(range(32)))
        families[tag]={'candidate':name,'validation':metrics(yv,s),'importance':imp,'family_recall':{f:recall_slice(v,s>=.5) for f,v in meta['validation']['family'].items()},
             'matched_removal':read(13,'growth_dependence')[tag+'_R0'] if tag in ('hgb','xgb') else None,
             'limitation':'RF/GB have no matched retraining-removal estimate; permutation sensitivity is not equivalent to retraining dependence.'}
    save('model_family_comparison',families)
    manifest={p.relative_to(ROOT).as_posix():sha(p) for directory in (M,E) for p in directory.glob('*') if p.is_file()}
    save('artifact_manifest',manifest)
    protection=compare(read(14,'protection_before'),snapshot()); assert protection['result']=='PASS'; save('protection',protection)
    print('Five fits complete; protected artifacts unchanged. Await source synthesis and verification.',flush=True)

if __name__=='__main__': main()
