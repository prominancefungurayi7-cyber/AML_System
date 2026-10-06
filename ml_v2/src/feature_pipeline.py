"""V2 causal 30-feature pipeline. Development partitions only by default."""
from __future__ import annotations
import argparse, csv, json, math, statistics
from collections import Counter, defaultdict, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from contracts import ROOT, EVENT_FIELDS, load_development, safe_path, write_json

FEATURE_NAMES = [
'structuring_prior_tx_count_1h','structuring_prior_value_sum_24h','structuring_same_day_prior_tx_count','structuring_repeated_amount_ratio_7d','structuring_amount_cluster_dispersion_7d','structuring_near_threshold_history_ratio_7d',
'network_outbound_counterparty_count_7d','network_inbound_counterparty_count_7d','network_outbound_counterparty_entropy_30d','network_top_counterparty_value_share_30d','network_current_receiver_is_new','network_repeated_receiver_ratio_30d','network_reciprocal_flow_ratio_7d','network_counterparty_set_change_7d','network_pass_through_ratio_24h','network_shared_counterparty_concentration_7d',
'agent_prior_tx_count_1h','agent_prior_tx_count_7d','agent_prior_value_sum_1h','agent_prior_value_sum_7d','agent_unique_wallet_count_7d','agent_wallet_value_hhi_7d','agent_repeat_wallet_ratio_7d','agent_current_wallet_is_new','agent_inbound_outbound_value_ratio_7d','agent_high_value_event_share_7d','agent_hourly_tx_zscore_30d','agent_hourly_value_zscore_30d','agent_burst_concentration_7d','agent_shared_wallet_flow_concentration_7d']

def ts(s): return datetime.strptime(s,'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
def subject(e): return e['serviced_wallet'] if e['transaction_type']!='wallet_to_wallet' else e['sender_wallet']
def window(rows, now, days=0, hours=0):
    lo=now-timedelta(days=days,hours=hours)
    return [e for e in rows if e['_time']>=lo]
def ratio(a,b): return a/b if b else 0.0
def popcv(values):
    return statistics.pstdev(values)/statistics.fmean(values) if len(values)>=2 and statistics.fmean(values) else 0.0

def extract_rows(raw_events):
    events=[]
    for raw in raw_events:
        e=dict(raw); e['transaction_id']=int(e['transaction_id']); e['amount_usd']=int(e['amount_minor'])/100.0; e['_time']=ts(e['event_timestamp']); events.append(e)
    events.sort(key=lambda e:(e['_time'],e['transaction_id']))
    wallet_activity=defaultdict(list); outbound=defaultdict(list); inbound=defaultdict(list); edges=deque(); agents=defaultdict(list)
    X=[]; ids=[]
    for e in events:
        now=e['_time']; w=subject(e); wa=wallet_activity[w]
        w1=window(wa,now,hours=1); w24=window(wa,now,hours=24); w7=window(wa,now,days=7)
        same=[h for h in wa if h['_time'].date()==now.date()]
        amounts=[h['amount_usd'] for h in w7]
        f=[float(len(w1)),sum(h['amount_usd'] for h in w24),float(len(same)),
           ratio(sum(abs(x-e['amount_usd'])<=.05*e['amount_usd'] for x in amounts),len(amounts)),popcv(amounts),
           ratio(sum(7000<=x<=10500 for x in amounts),len(amounts))]
        o7=window(outbound[e['sender_wallet']],now,days=7); i7=window(inbound[e['receiver_wallet']],now,days=7)
        o30=window(outbound[e['sender_wallet']],now,days=30); by=defaultdict(float)
        for h in o30: by[h['receiver_wallet']]+=h['amount_usd']
        total=sum(by.values()); entropy=-sum((v/total)*math.log(v/total) for v in by.values()) if total else 0.0
        counts=Counter(h['receiver_wallet'] for h in o30)
        subject_edges_out=window(outbound[w],now,hours=24); subject_edges_in=window(inbound[w],now,hours=24)
        send_out={h['receiver_wallet'] for h in window(outbound[e['sender_wallet']],now,days=7)}
        send_in={h['sender_wallet'] for h in window(inbound[e['sender_wallet']],now,days=7)}
        old7=[h for h in outbound[e['sender_wallet']] if now-timedelta(days=14)<=h['_time']<now-timedelta(days=7)]
        oldset={h['receiver_wallet'] for h in old7}; union=send_out|oldset
        while edges and edges[0]['_time']<now-timedelta(days=7): edges.popleft()
        recent_edges=list(edges); shared=0.0
        if send_out:
            links=defaultdict(set)
            for h in recent_edges:
                a,b=h['sender_wallet'],h['receiver_wallet']
                if a in send_out and b!=e['sender_wallet']: links[b].add(a)
                if b in send_out and a!=e['sender_wallet']: links[a].add(b)
            shared=max((len(v)/len(send_out) for v in links.values()),default=0.0)
        f += [float(len({h['receiver_wallet'] for h in o7})),float(len({h['sender_wallet'] for h in i7})),entropy,
              max(by.values())/total if total else 0.0,
              float(e['transaction_type']=='wallet_to_wallet' and not any(h['receiver_wallet']==e['receiver_wallet'] for h in outbound[e['sender_wallet']])),
              ratio(sum(counts[h['receiver_wallet']]>=2 for h in o30),len(o30)),ratio(len(send_out&send_in),len(send_out|send_in)),
              1-ratio(len(send_out&oldset),len(union)) if union else 0.0,
              ratio(sum(h['amount_usd'] for h in subject_edges_out),sum(h['amount_usd'] for h in subject_edges_in)),shared]
        if not e['agent_id']:
            f += [0.0]*14
        else:
            ah=agents[e['agent_id']]; a1=window(ah,now,hours=1); a7=window(ah,now,days=7); a30=window(ah,now,days=30)
            wc=Counter(h['serviced_wallet'] for h in a7); wv=defaultdict(float)
            for h in a7: wv[h['serviced_wallet']]+=h['amount_usd']
            av=sum(wv.values()); floats_out=sum(h['amount_usd'] for h in a7 if h['agent_flow_direction']=='outbound'); floats_in=sum(h['amount_usd'] for h in a7 if h['agent_flow_direction']=='inbound')
            median=statistics.median([h['amount_usd'] for h in a30]) if len(a30)>=3 else 0
            hour=now.replace(minute=0,second=0,microsecond=0); completed_counts=defaultdict(int); completed_values=defaultdict(float)
            current_count=0; current_value=0.0
            for h in a30:
                key=h['_time'].replace(minute=0,second=0,microsecond=0)
                if key<hour: completed_counts[key]+=1; completed_values[key]+=h['amount_usd']
                elif key==hour: current_count+=1; current_value+=h['amount_usd']
            def z(cur, values):
                vals=list(values.values())
                return (cur-statistics.fmean(vals))/statistics.pstdev(vals) if len(vals)>=7 and statistics.pstdev(vals)>0 else 0.0
            buckets=Counter(h['_time'].replace(minute=(h['_time'].minute//15)*15,second=0,microsecond=0) for h in a7)
            agent_wallets=set(wc); linked=defaultdict(set)
            if agent_wallets:
                for h in recent_edges:
                    a,b=h['sender_wallet'],h['receiver_wallet']
                    if a in agent_wallets and b not in agent_wallets: linked[b].add(a)
                    if b in agent_wallets and a not in agent_wallets: linked[a].add(b)
            f += [float(len(a1)),float(len(a7)),sum(h['amount_usd'] for h in a1),sum(h['amount_usd'] for h in a7),float(len(wc)),
                  sum((v/av)**2 for v in wv.values()) if av else 0.0,ratio(sum(wc[h['serviced_wallet']]>=2 for h in a7),len(a7)),
                  float(not any(h['serviced_wallet']==e['serviced_wallet'] for h in ah)),ratio(floats_in,floats_out),
                  ratio(sum(h['amount_usd']>2*median for h in a7),len(a7)) if median else 0.0,z(current_count,completed_counts),z(current_value,completed_values),
                  ratio(max(buckets.values(),default=0),len(a7)),max((len(v)/len(agent_wallets) for v in linked.values()),default=0.0)]
        if len(f)!=30 or not all(math.isfinite(v) for v in f): raise ValueError('Invalid feature vector')
        X.append(f); ids.append(e['transaction_id'])
        wallet_activity[w].append(e)
        if e['transaction_type']=='wallet_to_wallet': outbound[e['sender_wallet']].append(e); inbound[e['receiver_wallet']].append(e); edges.append(e)
        if e['agent_id']: agents[e['agent_id']].append(e)
    return X,ids

def extract_development(data_root, partition):
    events=load_development(data_root,partition,'transactions'); truth=load_development(data_root,partition,'ground_truth')
    labels={int(t['transaction_id']):int(t['target']) for t in truth}; X,ids=extract_rows(events)
    return X,[labels[i] for i in ids],ids

def write_matrix(folder,X,y,ids):
    folder=safe_path(folder); folder.mkdir(parents=True,exist_ok=False)
    with (folder/'X.csv').open('x',encoding='utf-8',newline='') as f: csv.writer(f,lineterminator='\n').writerows(X)
    with (folder/'y.csv').open('x',encoding='utf-8',newline='') as f: csv.writer(f,lineterminator='\n').writerows([[v] for v in y])
    with (folder/'row_ids.csv').open('x',encoding='utf-8',newline='') as f:
        w=csv.writer(f,lineterminator='\n'); w.writerow(['row_index','transaction_id']); w.writerows(enumerate(ids))
    write_json(folder/'feature_names.json',FEATURE_NAMES)

def main():
    p=argparse.ArgumentParser(); p.add_argument('--partition',choices=('train','validation'),required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
    X,y,ids=extract_development(ROOT/'data',a.partition); write_matrix(a.output,X,y,ids); print(len(X),len(X[0]))
if __name__=='__main__': main()
