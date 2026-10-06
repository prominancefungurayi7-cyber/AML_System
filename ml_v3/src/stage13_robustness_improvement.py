"""Isolated Stage 13 protection and evaluation helpers."""
from stage12_robustness import snapshot as previous_snapshot,write,stats,dependence,evaluate,REFERENCE
from stage11_protection import ROOT,sha,compare
import numpy as np
from collections import defaultdict
from math import log
from datetime import timedelta
from stage10a_pipeline import prepare,recent,baseline,covered,select_path,cash_skew,DAY

NEW_FEATURES=[
 {'name':'candidate_prior_reciprocal_count_7d','domain':'new_N3','marker':None,'min':0,'max':None,
  'formula':'Number of prior W2W edges receiver(T)->sender(T) in (t-7d,t], with key < key(T). Zero for non-W2W or self-loop.',
  'current':'type and endpoints only; no current amount','prior':'observable directed edges, strictly smaller timestamp/integer-ID keys','window':'open-lower 7d','baseline':'none','zero_missing':'zero means no reciprocal edge or non-applicable role; no missing marker',
  'meaning':'Repeated reverse-direction relationships beyond the selected shortest path','non_oracle':'No current/edge amount gates, no multi-edge qualifying-path conjunction or target.'},
 {'name':'candidate_prior_two_hop_return_count_7d','domain':'new_N3','marker':None,'min':0,'max':None,
  'formula':'Count edge-pairs r->m and m->s with three distinct nodes, both in (t-7d,t], key(edge1)<key(edge2)<key(T). Each edge-pair counts once. Zero for non-W2W/self-loop.',
  'current':'type and endpoints only','prior':'observable edges with increasing full keys','window':'open-lower 7d','baseline':'none','zero_missing':'zero when no chronological two-edge route; no missing marker',
  'meaning':'Multiplicity of short return routes, not restricted to the selected path','non_oracle':'No monetary filtering, current return ratio, lengths 3..5 or complete cycle predicate.'},
 {'name':'candidate_selected_path_max_log_value_change','domain':'new_N3','marker':-1,'min':0,'max':None,
  'formula':'max_j abs(log(amount(edge[j+1])/amount(edge[j]))) over adjacent edges in the Stage 10A selected chronological simple path of 1..5 prior edges. One-edge path=0; absent/non-W2W=-1.',
  'current':'type/endpoints select the prior path; current amount excluded','prior':'Stage 10A topology selection: shortest path, latest first edge, then lexicographic edge-key sequence','window':'open-lower 7d','baseline':'none','zero_missing':'one-edge path has no adjacent discrepancy (0); absent path uses -1',
  'meaning':'Continuous value variation along a selected prior path','non_oracle':'No amount-gated path search, predicate cutoffs, current ratio gate or any-qualifying-path output.'},
 {'name':'candidate_agent_cash_service_share_24h','domain':'new_A4','marker':None,'min':0,'max':1,
  'formula':'Cash-In plus Cash-Out service count / all service-event count in (t-24h,t], including permitted current service. Assisted W2W only enters denominator.',
  'current':'current agent service/type; no cash principal assigned to W2W','prior':'same-agent service history, key < key(T)','window':'open-lower 24h','baseline':'none','zero_missing':'zero without agent/services; no missing marker',
  'meaning':'Cash activity relative to all agent service activity','non_oracle':'No cash-count minimum, unique-wallet count, direction thresholds or complete imbalance conjunction.'},
 {'name':'candidate_agent_cash_direction_persistence_24h','domain':'new_A4','marker':None,'min':0,'max':1,
  'formula':'abs(sum(skew_j)/4), where skew_j=(cashout_value-cashin_value)/(cashout_value+cashin_value) in each of four disjoint 6h buckets (t-(j+1)*6h,t-j*6h], j=0..3; empty-cash bucket skew=0. Current service enters j=0.',
  'current':'current cash type/amount/agent and time','prior':'same-agent history, key < key(T); no future buckets','window':'four preceding/current 6h buckets covering open-lower 24h','baseline':'none','zero_missing':'zero with no cash/agent or balanced opposing bucket directions; no missing marker',
  'meaning':'Persistence of a common cash direction across time, discounted by inactive buckets','non_oracle':'No complete A4 count, wallet breadth, magnitude/change or current-role conjunction.'},
 {'name':'candidate_agent_cash_value_acceleration_24h','domain':'new_A4','marker':-1,'min':0,'max':None,
  'formula':'Recent 24h Cash-In+Cash-Out minor-unit value / max(1, preceding disjoint 28d cash value / 28). Baseline B=(t-29d,t-1d], recent R=(t-1d,t].',
  'current':'current cash value included; assisted W2W contributes zero cash','prior':'same-agent observed services; full baseline coverage from first observed service <=t-29d','window':'open-lower 24h recent; disjoint 28d baseline','baseline':'at least 12 baseline services and 8 baseline cash events, full 29d observation; no recent eligibility gate','zero_missing':'-1 without agent or eligible baseline; valid zero if no recent cash; denominator floor one minor unit',
  'meaning':'Unsigned cash magnitude relative to the agent own earlier activity','non_oracle':'No signed imbalance/change gates, recent count/breadth conjunction, private activation or predicate outcome.'}
]
NEW_NAMES=[f['name'] for f in NEW_FEATURES]

def extract_candidate_features(rows):
    """Fresh partition state; emit six descriptors before inserting current event."""
    outgoing=defaultdict(list); agents=defaultdict(list); first={}; ids=[]; result=[]
    for e in prepare(rows):
        count1=count2=0; spread=-1.
        if e['w2w'] and e['sender_wallet']!=e['receiver_wallet']:
            sender=e['sender_wallet']; receiver=e['receiver_wallet']
            for edge in recent(outgoing.get(receiver,()),e,7*DAY):
                mid=edge['receiver_wallet']
                if mid==sender: count1+=1
                if mid in (sender,receiver): continue
                count2+=sum(n['receiver_wallet']==sender and n['key']>edge['key'] for n in recent(outgoing.get(mid,()),e,7*DAY))
            path=select_path(outgoing,e)
            if path: spread=max([abs(log(b['amount']/a['amount'])) for a,b in zip(path,path[1:])],default=0.)
        aid=e['agent_id']; hist=agents[aid] if aid else []
        current=recent(hist,e,DAY)+([e] if aid else [])
        cash=[x for x in current if x['transaction_type'] in ('cash_in','cash_out')]
        share=len(cash)/len(current) if current else 0.
        bucket_skews=[cash_skew([x for x in current if e['t']-timedelta(hours=(j+1)*6)<x['t']<=e['t']-timedelta(hours=j*6)]) for j in range(4)]
        persist=abs(sum(bucket_skews)/4)
        base=baseline(hist,e,DAY); bc=[x for x in base if x['transaction_type'] in ('cash_in','cash_out')]
        rate=sum(x['amount'] for x in cash)/max(1.,sum(x['amount'] for x in bc)/28) if aid and covered(first.get(aid),e,DAY) and len(base)>=12 and len(bc)>=8 else -1.
        ids.append(str(e['id'])); result.append([float(count1),float(count2),spread,share,persist,rate])
        if e['w2w']: outgoing[e['sender_wallet']].append(e)
        if aid: agents[aid].append(e); first.setdefault(aid,e['t'])
    return ids,np.asarray(result,dtype=float).reshape((-1,6))

def snapshot():
    result=previous_snapshot()
    for folder,patterns in [('reports',('stage12_*','V3_STAGE12*')),('src',('*stage12*.py',)),('tests',('*stage12*.py',))]:
        for pattern in patterns:
            for p in (ROOT/folder).glob(pattern):
                if p.is_file(): result['files'][p.relative_to(ROOT.parent).as_posix()]=sha(p)
    for p in (ROOT/'models/stage12_diagnostics').rglob('*'):
        if p.is_file(): result['files'][p.relative_to(ROOT.parent).as_posix()]=sha(p)
    result['scope']+=['Stage 12 named report/source/test patterns','ml_v3/models/stage12_diagnostics']
    return result

def assess(xt,yt,xv,yv,pt,pv,meta):
    result=evaluate(xt,yt,xv,yv,pt,pv,meta)
    mask=sum(v.astype(int) for v in meta['domain'].values())>1
    n=int(mask.sum()); tp=int(np.sum(mask&(pv>=.5)))
    result['domain_independence']['multi_domain']={'support':n,'tp':tp,'fn':n-tp,'recall':tp/n if n else None}
    result['generalization_gap']=result['train']['macro_f1']-result['validation']['macro_f1']
    return result
