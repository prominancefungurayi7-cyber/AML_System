"""Model-free Stage 10 matrix, temporal and distribution audits."""
from __future__ import annotations
import math
from collections import Counter
from statistics import mean, median, pstdev

from feature_contract import FEATURE_NAMES, MISSING_VALUE


def _quantile(values, q):
    if not values: return 0.0
    xs=sorted(values); pos=(len(xs)-1)*q; lo=int(pos); hi=min(lo+1,len(xs)-1)
    return xs[lo]+(xs[hi]-xs[lo])*(pos-lo)


def feature_statistics(matrix):
    out={}
    for j,name in enumerate(FEATURE_NAMES):
        values=[float(row[j]) for row in matrix]
        out[name]={'minimum':min(values),'maximum':max(values),'mean':mean(values),'std':pstdev(values),
                   'median':median(values),'q01':_quantile(values,.01),'q05':_quantile(values,.05),
                   'q95':_quantile(values,.95),'q99':_quantile(values,.99),
                   'zero_fraction':sum(v==0 for v in values)/len(values),'distinct_count':len(set(values),),
                   'missing_sentinel_fraction':sum(v==MISSING_VALUE for v in values)/len(values),
                   'constant':len(set(values))==1,'near_constant':len(set(values))<=2}
    return out


def matrix_audit(data):
    x=data['X']; y=data['y']; ids=data['row_ids']
    finite=all(math.isfinite(float(v)) for row in x for v in row)
    return {'rows':len(x),'columns':len(FEATURE_NAMES),'feature_order':list(FEATURE_NAMES),
            'target_counts':dict(Counter(y)),'nan_count':sum(1 for row in x for v in row if str(v).lower()=='nan'),
            'infinity_count':sum(1 for row in x for v in row if not math.isfinite(float(v))),
            'all_numeric_finite':finite,'duplicate_row_id_count':len(ids)-len(set(ids))}


def target_overlap(data):
    out={}; x=data['X']; y=data['y']
    for j,name in enumerate(FEATURE_NAMES):
        groups={str(k):[float(x[i][j]) for i,v in enumerate(y) if v==k] for k in (0,1)}
        out[name]={k:{'minimum':min(v),'maximum':max(v),'mean':mean(v),'median':median(v),
                      'q05':_quantile(v,.05),'q95':_quantile(v,.95),'count':len(v)} for k,v in groups.items()}
        out[name]['range_overlap'] = not (out[name]['0']['maximum'] < out[name]['1']['minimum'] or out[name]['1']['maximum'] < out[name]['0']['minimum'])
    return out


def temporal_checks(extract):
    def e(i, second, sender='w', receiver='z', amount=10000, kind='wallet_to_wallet', agent='', serviced=''):
        return {'transaction_id':str(i),'event_sequence':str(i),'event_timestamp':f'2025-01-01T00:00:{second:02d}.000000Z',
          'sender_wallet':sender,'receiver_wallet':receiver,'amount_minor':str(amount),'currency':'USD','transaction_type':kind,
          'channel':'direct_wallet','agent_id':agent,'serviced_wallet':serviced,'agent_flow_direction':'none'}
    base=[e(1,1),e(2,2,amount=11000)]
    ids1,x1=extract(base)
    ids2,x2=extract(base+[e(3,50,sender='future',receiver='other',amount=999999)])
    future_prefix=ids1==ids2[:len(ids1)] and x1==x2[:len(x1)]
    # Equal timestamps are ordered by transaction ID, so ID 1 cannot see ID 2.
    equal=[e(2,10,amount=30000),e(1,10,amount=1000)]
    equal_ids, equal_x=extract(equal)
    equal_order=equal_ids==['1','2'] and equal_x[0][3]==1.0 and equal_x[1][3]==2.0
    # Changing a current amount changes the explicit amount but leaves prior
    # count/value state unchanged for the same current event position.
    a=extract([e(1,1),e(2,2,amount=11000)])[1][-1]
    b=extract([e(1,1),e(2,2,amount=22000)])[1][-1]
    # Prior-only state (path topology and coverage) must remain unchanged;
    # explicitly current-derived amount and inclusive quantities may change.
    current_only=(a[16]==b[16] and a[29:32]==b[29:32] and a[0]!=b[0])
    return {'future_transaction_does_not_change_prefix':future_prefix,'equal_timestamp_id_order':equal_order,
            'current_change_does_not_change_prior_state':current_only,'result':'PASS' if future_prefix and equal_order and current_only else 'FAIL'}


def metadata_independence(extract):
    base={'transaction_id':'1','event_sequence':'1','event_timestamp':'2025-01-01T00:00:01.000000Z','sender_wallet':'w','receiver_wallet':'z','amount_minor':'10000','currency':'USD','transaction_type':'wallet_to_wallet','channel':'direct_wallet','agent_id':'','serviced_wallet':'','agent_flow_direction':'none'}
    private=dict(base,scenario_member='1',campaign_id='secret',origin_cohort='hard_scenario',signal_strength='strong',evidence_families='N3',witness_transaction_ids='[9]',onset_flag='1')
    return {'identical_observable_histories_equal':extract([base])[1]==extract([private])[1], 'result':'PASS' if extract([base])[1]==extract([private])[1] else 'FAIL'}
