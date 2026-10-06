"""Stage 7 development-only, non-deployable separability diagnostics."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import timedelta
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import RobustScaler

from contracts import ROOT, digest, load_development, safe_path
from feature_pipeline import FEATURE_NAMES, ts
from improve_candidates import FAMILIES
from run_stage4 import protected
from train_candidates import load_matrix

HARD = {'H1':['variable_fragment_burst','distributed_same_day_fragmentation'],
        'H2':['similar_amount_repetition'], 'H3':['variable_near_threshold_history'],
        'H4':['many_to_one_collection'], 'H5':['one_to_many_dispersion','wallet_pass_through'],
        'H6':['reciprocal_relationship_cycle'],
        'H7':['agent_wallet_growth','agent_temporal_burst'],
        'H8':['agent_wallet_concentration','agent_flow_imbalance']}
MATCH = {f:h for h,fs in HARD.items() for f in fs}
GROUP = {'structuring':list(range(6)), 'network':list(range(6,16)), 'agent':list(range(16,30))}


def guard_files():
    # The holdout access boundary takes precedence over hashing every raw file.
    paths = [p for folder in ('data/development','features/development')
             for p in (ROOT/folder).rglob('*') if p.is_file()]
    paths += [p for p in (ROOT/'models/candidates').glob('s5_*') if p.is_file()]
    paths += [p for p in (ROOT/'reports').glob('stage5_*') if p.is_file()]
    paths += [p for p in (ROOT/'reports').glob('stage6_*') if p.is_file()]
    paths += [ROOT/'reports/V2_STAGE5_MODEL_IMPROVEMENT.md',ROOT/'reports/V2_STAGE6_FEATURE_IMPROVEMENT.md']
    return {str(p.relative_to(ROOT)):digest(p) for p in paths}


def episode_positions(truth):
    by = defaultdict(list)
    for r in truth:
        ep = r['episode_id'] or r['normal_episode_id']
        if ep: by[ep].append(int(r['transaction_id']))
    positions={}
    for ids in by.values():
        ids.sort()
        n=len(ids)
        for j,i in enumerate(ids):
            positions[i]={'index':j+1,'length':n,'quartile':min(4,4*j//n+1),
                          'event_bucket':str(j+1) if j<3 else '4+'}
    return positions


def rate(idx, pred):
    return {'count':len(idx),'detected':int(pred[idx].sum()) if len(idx) else 0,
            'recall':float(pred[idx].mean()) if len(idx) else None}


def cycle_exists(edges):
    graph=defaultdict(set)
    for a,b in edges: graph[a].add(b)
    for start in list(graph):
        stack=[(v,{start,v}) for v in graph[start] if v!=start]
        while stack:
            v,seen=stack.pop()
            if start in graph[v]: return True
            if len(seen)<6:
                stack.extend((w,seen|{w}) for w in graph[v] if w not in seen)
    return False


def relevant_cycle_exists(edges, current):
    relevant={current['sender_wallet'],current['receiver_wallet']}
    graph=defaultdict(set)
    for a,b in edges: graph[a].add(b)
    for start in relevant:
        stack=[(v,{start,v}) for v in graph.get(start,()) if v!=start]
        while stack:
            v,seen=stack.pop()
            if start in graph.get(v,()): return True
            if len(seen)<6:
                stack.extend((w,seen|{w}) for w in graph.get(v,()) if w not in seen)
    return False


def current_closes_cycle(edges,current):
    sender,receiver=current['sender_wallet'],current['receiver_wallet']
    if current['transaction_type']!='wallet_to_wallet': return False
    graph=defaultdict(set)
    for a,b in edges: graph[a].add(b)
    stack=[receiver]; seen=set()
    while stack:
        v=stack.pop()
        if v==sender: return True
        if v not in seen:
            seen.add(v); stack.extend(graph.get(v,()))
    return False


def evidence(family, prior, current):
    """Conservative prior-within-episode evidence proxy, not a label rule."""
    if not prior: return 'none'
    if family=='reciprocal_relationship_cycle':
        edges=[(e['sender_wallet'],e['receiver_wallet']) for e in prior if e['transaction_type']=='wallet_to_wallet']
        if cycle_exists(edges): return 'mature'
        return 'partial' if edges else 'none'
    if family=='wallet_pass_through':
        transfer=[e for e in prior if e['transaction_type']=='wallet_to_wallet']
        if len(transfer)>=2: return 'mature'
        return 'partial' if transfer else 'none'
    if family=='many_to_one_collection':
        transfers=[e for e in prior if e['transaction_type']=='wallet_to_wallet']
        max_sources=max((len({e['sender_wallet'] for e in transfers if e['receiver_wallet']==w}) for w in {e['receiver_wallet'] for e in transfers}),default=0)
        return 'mature' if max_sources>=3 else ('partial' if max_sources else 'none')
    if family=='one_to_many_dispersion':
        transfers=[e for e in prior if e['transaction_type']=='wallet_to_wallet']
        max_targets=max((len({e['receiver_wallet'] for e in transfers if e['sender_wallet']==w}) for w in {e['sender_wallet'] for e in transfers}),default=0)
        return 'mature' if max_targets>=3 else ('partial' if max_targets else 'none')
    if family=='agent_flow_imbalance':
        cash=[e for e in prior if e['transaction_type'] in ('cash_in','cash_out')]
        return 'mature' if len(cash)>=3 else ('partial' if cash else 'none')
    if family=='agent_wallet_growth':
        n=len({e['serviced_wallet'] for e in prior if e['serviced_wallet']})
        return 'mature' if n>=4 else ('partial' if n else 'none')
    if family=='agent_wallet_concentration':
        counts=Counter(e['serviced_wallet'] for e in prior if e['serviced_wallet'])
        return 'mature' if max(counts.values(),default=0)>=3 else ('partial' if counts else 'none')
    if family=='agent_temporal_burst':
        return 'mature' if len(prior)>=3 and (ts(prior[-1]['event_timestamp'])-ts(prior[0]['event_timestamp'])).total_seconds()<=7200 else 'partial'
    if family=='similar_amount_repetition':
        amounts=[int(e['amount_minor']) for e in prior]
        return 'mature' if len(amounts)>=3 and any(sum(abs(x-a)<=.05*a for x in amounts)>=3 for a in amounts) else 'partial'
    if family=='variable_near_threshold_history':
        near=sum(700000<=int(e['amount_minor'])<=1050000 for e in prior)
        return 'mature' if near>=2 else 'partial'
    if family=='distributed_same_day_fragmentation':
        days=Counter(e['event_timestamp'][:10] for e in prior)
        return 'mature' if max(days.values())>=3 else 'partial'
    return 'mature' if len(prior)>=3 else 'partial'


def auc_or_none(y,x):
    return float(roc_auc_score(y,x)) if len(set(y))==2 and len(set(x))>1 else None


def scalar_overlap(a,b):
    """IQR intersection / IQR union; 1 means identical IQR ranges."""
    qa=np.quantile(a,[.25,.75]); qb=np.quantile(b,[.25,.75])
    width=max(qa[1],qb[1])-min(qa[0],qb[0])
    return float(max(0,min(qa[1],qb[1])-max(qa[0],qb[0]))/width) if width else float(qa[0]==qb[0])


def summarize_pair(X, pos, neg):
    y=np.r_[np.ones(len(pos)),np.zeros(len(neg))]
    rows=[]
    for j,name in enumerate(FEATURE_NAMES):
        a,b=X[pos,j],X[neg,j]
        auc=auc_or_none(y,np.r_[a,b])
        rows.append({'feature':name,'auc':auc,'auc_direction_free':max(auc,1-auc) if auc is not None else .5,
                     'iqr_overlap':scalar_overlap(a,b),'positive_median':float(np.median(a)),
                     'normal_median':float(np.median(b))})
    return sorted(rows,key=lambda r:r['auc_direction_free'],reverse=True)


def role_n4(rows, position):
    idx=next((i for i,e in enumerate(rows) if e['transaction_type']=='wallet_to_wallet'),None)
    if idx is None: return 'no_transfer'
    if position<idx: return 'cash_funding'
    if position==idx: return 'inbound_transfer'
    return 'outbound_or_exit'


def main():
    outputs=['stage7_episode_position.json','stage7_family_observability.json',
             'stage7_hard_negative_overlap.json','stage7_neighbour_overlap.json',
             'stage7_family_separability.json','stage7_completed_episode_diagnostic.json']
    for name in outputs:
        safe_path(ROOT/'reports'/name)
    before_v1, before=protected(),guard_files()
    Xtr,ytr,idtr=load_matrix('train'); Xv,yv,idv=load_matrix('validation')
    truth={p:load_development(ROOT/'data',p,'ground_truth') for p in ('train','validation')}
    events={p:load_development(ROOT/'data',p,'transactions') for p in ('train','validation')}
    meta={p:{int(r['transaction_id']):r for r in truth[p]} for p in truth}
    event_map={p:{int(r['transaction_id']):r for r in events[p]} for p in events}
    if len(idtr)!=60000 or len(idv)!=15000: raise ValueError('Unexpected development size')
    frozen=joblib.load(ROOT/'models/candidates/s5_gradient_boosting_060.joblib')
    if frozen['feature_names']!=FEATURE_NAMES or frozen['threshold']!=.5: raise ValueError('Frozen model mismatch')
    prob=frozen['model'].predict_proba(frozen['preprocessor'].transform(Xv))[:,1]
    pred=prob>=.5
    id_to_i={int(i):j for j,i in enumerate(idv)}
    positions={p:episode_positions(truth[p]) for p in truth}
    episode_rows={p:defaultdict(list) for p in truth}
    for p in truth:
        for i in sorted(event_map[p]):
            m=meta[p][i]; ep=m['episode_id'] or m['normal_episode_id']
            if ep: episode_rows[p][ep].append(event_map[p][i])
    pos_out={'model':'s5_gradient_boosting_060','threshold':.5,'families':{}}
    obs={'definition':'Evidence categories use prior events in the same labelled episode only. They are lower-bound operational proxies, not proof of suspiciousness or absence of relevant ordinary history.','families':{},'n3':{},'n4':{}}
    for family in FAMILIES:
        ids=[int(i) for i in idv if meta['validation'][int(i)]['primary_family']==family]
        fp={}
        for mode in ('event_bucket','quartile'):
            fp[mode]={str(b):rate(np.asarray([id_to_i[i] for i in ids if positions['validation'][i][mode]==b],dtype=int),pred)
                      for b in (('1','2','3','4+') if mode=='event_bucket' else (1,2,3,4))}
        pos_out['families'][family]=fp
        categories=defaultdict(list)
        for i in ids:
            m=meta['validation'][i]; rows=episode_rows['validation'][m['episode_id']]
            j=positions['validation'][i]['index']-1
            categories[evidence(family,rows[:j],rows[j])].append(id_to_i[i])
        obs['families'][family]={k:rate(np.asarray(categories[k],dtype=int),pred) for k in ('none','partial','mature')}
    n3=defaultdict(list); n3_position=defaultdict(lambda:defaultdict(list)); n3_any=defaultdict(list); n3_closure=defaultdict(list)
    for i in [int(i) for i in idv if meta['validation'][int(i)]['primary_family']=='reciprocal_relationship_cycle']:
        rows=episode_rows['validation'][meta['validation'][i]['episode_id']]; j=positions['validation'][i]['index']-1
        edges=[(e['sender_wallet'],e['receiver_wallet']) for e in rows[:j] if e['transaction_type']=='wallet_to_wallet']
        complete=relevant_cycle_exists(edges,rows[j])
        any_cycle=cycle_exists(edges)
        any_reciprocal=any((b,a) in edges for a,b in edges)
        n3_any['any_prior_cycle' if any_cycle else ('any_prior_reciprocal_pair' if any_reciprocal else 'no_prior_reciprocal')].append(id_to_i[i])
        n3_closure['current_closes_cycle' if current_closes_cycle(edges,rows[j]) else 'current_does_not_close_cycle'].append(id_to_i[i])
        relevant={rows[j]['sender_wallet'],rows[j]['receiver_wallet']}
        reciprocal=any((b,a) in edges and (a in relevant or b in relevant) for a,b in edges)
        category='complete_prior_cycle' if complete else ('prior_reciprocal_pair' if reciprocal else 'no_prior_reciprocal')
        n3[category].append(id_to_i[i]); n3_position[positions['validation'][i]['event_bucket']][category].append(id_to_i[i])
    obs['n3']={'categories':{k:rate(np.asarray(n3[k],dtype=int),pred) for k in ('no_prior_reciprocal','prior_reciprocal_pair','complete_prior_cycle')},
               'any_episode_prior_motif':{k:rate(np.asarray(n3_any[k],dtype=int),pred) for k in ('no_prior_reciprocal','any_prior_reciprocal_pair','any_prior_cycle')},
               'current_edge_closure':{k:rate(np.asarray(n3_closure[k],dtype=int),pred) for k in ('current_closes_cycle','current_does_not_close_cycle')},
               'by_event_position':{b:{k:rate(np.asarray(n3_position[b][k],dtype=int),pred) for k in ('no_prior_reciprocal','prior_reciprocal_pair','complete_prior_cycle')} for b in ('1','2','3','4+')},
               'scope':'prior edges in same labelled episode; complete means a directed cycle containing a current endpoint; cross-episode history is excluded'}
    n4=defaultdict(list); n4_positions=defaultdict(lambda:defaultdict(list))
    for i in [int(i) for i in idv if meta['validation'][int(i)]['primary_family']=='wallet_pass_through']:
        rows=episode_rows['validation'][meta['validation'][i]['episode_id']]; j=positions['validation'][i]['index']-1
        role=role_n4(rows,j); n4[role].append(id_to_i[i]); n4_positions[positions['validation'][i]['event_bucket']][role].append(id_to_i[i])
    obs['n4']={'roles':{k:rate(np.asarray(v,dtype=int),pred) for k,v in n4.items()},
               'by_event_position':{b:{k:rate(np.asarray(v,dtype=int),pred) for k,v in role.items()} for b,role in n4_positions.items()},
               'scope':'role inferred from first W2W transfer of labelled episode; outbound_or_exit includes later cash events'}
    # Causal agent history is measured before each event, including ordinary interleaving.
    agent_values={}
    history=defaultdict(list)
    for i in sorted(event_map['validation']):
        e=event_map['validation'][i]; agent=e['agent_id']
        if not agent: continue
        now=ts(e['event_timestamp']); prior=history[agent]
        recent=[h for h in prior if h['_time']>=now-timedelta(days=7)]
        earlier=[h for h in prior if now-timedelta(days=14)<=h['_time']<now-timedelta(days=7)]
        short=[h for h in prior if h['_time']>=now-timedelta(hours=1)]
        wallets=Counter(h['serviced_wallet'] for h in recent if h['serviced_wallet'])
        earlier_wallets={h['serviced_wallet'] for h in earlier if h['serviced_wallet']}
        cash_in=sum(h['transaction_type']=='cash_in' for h in recent)
        cash_out=sum(h['transaction_type']=='cash_out' for h in recent)
        agent_values[i]={'recent_count':len(recent),'earlier_count':len(earlier),
                         'recent_unique_wallets':len(wallets),'earlier_unique_wallets':len(earlier_wallets),
                         'new_wallet_share':len(set(wallets)-earlier_wallets)/len(wallets) if wallets else 0,
                         'top_wallet_share':max(wallets.values())/len(recent) if recent else 0,
                         'cash_count_imbalance':(cash_out-cash_in)/(cash_out+cash_in) if cash_out+cash_in else 0,
                         'prior_hour_count':len(short)}
        e['_time']=now; prior.append(e)
    obs['agent_prior_baseline']={}
    for family in FAMILIES[8:]:
        h=MATCH[family]
        pos=[agent_values[int(i)] for i in idv if meta['validation'][int(i)]['primary_family']==family and int(i) in agent_values]
        neg=[agent_values[int(i)] for i in idv if meta['validation'][int(i)]['normal_family']==h and int(i) in agent_values]
        stats={}
        y=np.r_[np.ones(len(pos)),np.zeros(len(neg))]
        for key in pos[0]:
            a=np.asarray([v[key] for v in pos]); b=np.asarray([v[key] for v in neg])
            auc=auc_or_none(y,np.r_[a,b])
            stats[key]={'suspicious_median':float(np.median(a)),'normal_median':float(np.median(b)),
                        'direction_free_auc':max(auc,1-auc) if auc is not None else .5,
                        'iqr_overlap':scalar_overlap(a,b)}
        obs['agent_prior_baseline'][family]={'hard_family':h,'suspicious_count':len(pos),'normal_count':len(neg),'quantities':stats}
    print('episode and observability complete',flush=True)
    # Local overlap: Train-fitted robust scaling, deterministic stratified Train reference.
    rng=np.random.default_rng(20260921)
    tr_idx=np.sort(np.r_[rng.choice(np.flatnonzero(ytr==0),15000,replace=False),
                          rng.choice(np.flatnonzero(ytr==1),min(6000,int((ytr==1).sum())),replace=False)])
    scaler=RobustScaler().fit(Xtr)
    Atr=np.clip(scaler.transform(Xtr[tr_idx]),-20,20).astype(np.float32)
    B=np.clip(scaler.transform(Xv),-20,20).astype(np.float32)
    nn=NearestNeighbors(n_neighbors=5,algorithm='brute',metric='euclidean',n_jobs=1).fit(Atr)
    _,neighbors=nn.kneighbors(B)
    positive_count=ytr[tr_idx][neighbors].sum(axis=1)
    def neighbour_summary(sel):
        z=positive_count[sel]
        return {'count':int(len(z)),'mostly_normal':float(np.mean(z<=2)) if len(z) else None,
                'mostly_suspicious':float(np.mean(z>=3)) if len(z) else None,
                'mean_suspicious_neighbours':float(np.mean(z)) if len(z) else None}
    neighbour={'method':'5 nearest neighbours, Euclidean on Train-fitted RobustScaler 30 features, transformed values clipped to [-20,20] for distance stability; fixed stratified Train reference sample, not a classifier',
               'reference_counts':{'normal':int((ytr[tr_idx]==0).sum()),'suspicious':int((ytr[tr_idx]==1).sum())},
               'validation':{'suspicious':neighbour_summary(yv==1),'normal':neighbour_summary(yv==0)},
               'domains':{},'families':{},'positions':{},'normal_families':{}}
    for domain in ('structuring','network','agent'):
        neighbour['domains'][domain]=neighbour_summary(np.asarray([y==1 and meta['validation'][int(i)]['primary_domain']==domain for i,y in zip(idv,yv)]))
    for family in FAMILIES:
        neighbour['families'][family]=neighbour_summary(np.asarray([meta['validation'][int(i)]['primary_family']==family for i in idv]))
        neighbour['positions'][family]={str(b):neighbour_summary(np.asarray([meta['validation'][int(i)]['primary_family']==family and positions['validation'][int(i)]['event_bucket']==b for i in idv])) for b in ('1','2','3','4+')}
    for h in ('routine',*HARD):
        neighbour['normal_families'][h]=neighbour_summary(np.asarray([meta['validation'][int(i)]['normal_family']==h for i in idv]))
    print('neighbours complete',flush=True)
    # Family-conditioned pair comparisons are diagnostic selections; identity never enters X.
    hard_out={'matching':HARD,'comparisons':{}}
    sep={'families':{},'method':'Family versus designed hard counterpart on Validation; feature AUC is direction-free for ranking; logistic oracle-group models fit Train only with matched normal episodes. Scenario identity selects diagnostic cohorts, never model inputs.'}
    idtr_i={int(i):j for j,i in enumerate(idtr)}
    for h, families in HARD.items():
        normal=np.asarray([j for j,i in enumerate(idv) if meta['validation'][int(i)]['normal_family']==h],dtype=int)
        for family in families:
            positive=np.asarray([j for j,i in enumerate(idv) if meta['validation'][int(i)]['primary_family']==family],dtype=int)
            ranked=summarize_pair(Xv,positive,normal)
            hard_out['comparisons'][family]={'hard_family':h,'positive_count':len(positive),'normal_count':len(normal),
                                             'top_frozen_features':ranked[:6],
                                             'strong_overlap_features':[r for r in ranked if r['iqr_overlap']>=.75][:6],
                                             'observable_event_mix':{
                                                 'suspicious':dict(Counter(event_map['validation'][int(idv[j])]['channel'] for j in positive)),
                                                 'normal':dict(Counter(event_map['validation'][int(idv[j])]['channel'] for j in normal))},
                                             'transaction_type_mix':{
                                                 'suspicious':dict(Counter(event_map['validation'][int(idv[j])]['transaction_type'] for j in positive)),
                                                 'normal':dict(Counter(event_map['validation'][int(idv[j])]['transaction_type'] for j in normal))}}
            train_sel=np.asarray([j for j,i in enumerate(idtr) if meta['train'][int(i)]['primary_family']==family or meta['train'][int(i)]['normal_family']==h],dtype=int)
            valid_sel=np.r_[positive,normal]
            yt=np.asarray([meta['train'][int(idtr[j])]['primary_family']==family for j in train_sel],dtype=int)
            yval=np.r_[np.ones(len(positive)),np.zeros(len(normal))]
            domain=next(k for k in GROUP if family.startswith({'structuring':'variable_','network':'NOMATCH','agent':'agent_'}[k])) if False else ('structuring' if family in FAMILIES[:4] else 'network' if family in FAMILIES[4:8] else 'agent')
            models={}
            for key,columns in ((domain,GROUP[domain]),('all_30',list(range(30)))):
                sc=RobustScaler().fit(Xtr[train_sel][:,columns])
                clf=LogisticRegression(C=.05,max_iter=1000,solver='liblinear',random_state=20260921)
                clf.fit(np.clip(sc.transform(Xtr[train_sel][:,columns]),-20,20),yt)
                pv=clf.predict_proba(np.clip(sc.transform(Xv[valid_sel][:,columns]),-20,20))[:,1]
                models[key]={'roc_auc':float(roc_auc_score(yval,pv)),'train_count':len(train_sel),'validation_count':len(valid_sel)}
            sep['families'][family]={'hard_family':h,'top_univariate':ranked[:6], 'oracle_group':models}
        print(h,'comparisons complete',flush=True)
    # Full-episode values deliberately use future transactions; never feed model.
    def completed_stat(rows):
        amounts=np.asarray([int(e['amount_minor']) for e in rows],dtype=float)
        duration=(ts(rows[-1]['event_timestamp'])-ts(rows[0]['event_timestamp'])).total_seconds()/3600
        edges=[(e['sender_wallet'],e['receiver_wallet']) for e in rows if e['transaction_type']=='wallet_to_wallet']
        return {'length':len(rows),'duration_hours':duration,
                'unique_serviced_wallets':len({e['serviced_wallet'] for e in rows if e['serviced_wallet']}),
                'unique_senders':len({e['sender_wallet'] for e in rows}),
                'unique_receivers':len({e['receiver_wallet'] for e in rows}),
                'amount_cv':float(np.std(amounts)/np.mean(amounts)) if amounts.mean() else 0,
                'transfer_count':len(edges),'complete_cycle':int(cycle_exists(edges)),
                'cash_count_imbalance':abs(sum(e['transaction_type']=='cash_out' for e in rows)-sum(e['transaction_type']=='cash_in' for e in rows))}
    complete={'warning':'NON-DEPLOYABLE: full-episode statistics include current/future facts; descriptive only, no model input or label change.', 'families':{}}
    for family in FAMILIES:
        h=MATCH[family]
        p_episodes={meta['validation'][int(i)]['episode_id'] for i in idv if meta['validation'][int(i)]['primary_family']==family}
        n_episodes={meta['validation'][int(i)]['normal_episode_id'] for i in idv if meta['validation'][int(i)]['normal_family']==h}
        ps=[completed_stat(episode_rows['validation'][e]) for e in p_episodes]
        ns=[completed_stat(episode_rows['validation'][e]) for e in n_episodes]
        y=np.r_[np.ones(len(ps)),np.zeros(len(ns))]
        stat={}
        for key in ps[0]:
            a=np.asarray([v[key] for v in ps]); b=np.asarray([v[key] for v in ns])
            auc=auc_or_none(y,np.r_[a,b])
            stat[key]={'positive_median':float(np.median(a)),'normal_median':float(np.median(b)),
                       'direction_free_auc':max(auc,1-auc) if auc is not None else .5,
                       'iqr_overlap':scalar_overlap(a,b)}
        complete['families'][family]={'hard_family':h,'positive_episodes':len(ps),'normal_episodes':len(ns),
                                      'completed_statistics':stat,
                                      'best_first_event_frozen_feature_auc':max(r['auc_direction_free'] for r in summarize_pair(Xv,
                                        np.asarray([id_to_i[min(int(e['transaction_id']) for e in episode_rows['validation'][ep])] for ep in p_episodes]),
                                        np.asarray([id_to_i[min(int(e['transaction_id']) for e in episode_rows['validation'][ep])] for ep in n_episodes])))}
    # Repeat descriptive episode contrasts on Train to check that the same
    # construction differences are present outside Validation.
    complete['train_families']={}
    for family in FAMILIES:
        h=MATCH[family]
        p_episodes={m['episode_id'] for m in truth['train'] if m['primary_family']==family}
        n_episodes={m['normal_episode_id'] for m in truth['train'] if m['normal_family']==h}
        ps=[completed_stat(episode_rows['train'][e]) for e in p_episodes]
        ns=[completed_stat(episode_rows['train'][e]) for e in n_episodes]
        y=np.r_[np.ones(len(ps)),np.zeros(len(ns))]
        stat={}
        for key in ps[0]:
            a=np.asarray([v[key] for v in ps]); b=np.asarray([v[key] for v in ns])
            auc=auc_or_none(y,np.r_[a,b])
            stat[key]={'positive_median':float(np.median(a)),'normal_median':float(np.median(b)),
                       'direction_free_auc':max(auc,1-auc) if auc is not None else .5,
                       'iqr_overlap':scalar_overlap(a,b)}
        complete['train_families'][family]={'hard_family':h,'positive_episodes':len(ps),
                                            'normal_episodes':len(ns),'completed_statistics':stat}
    after_v1, after=protected(),guard_files()
    if before_v1!=after_v1 or before!=after: raise RuntimeError('Protected input changed')
    for name,data in zip(outputs,(pos_out,obs,hard_out,neighbour,sep,complete)):
        data['protection']={'result':'PASS','v1_application_file_count':len(before_v1),
                            'v2_dataset_feature_stage5_stage6_file_count':len(before)}
        (ROOT/'reports'/name).write_text(json.dumps(data,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Stage 7 diagnostic outputs written; protection PASS',flush=True)


if __name__=='__main__': main()
