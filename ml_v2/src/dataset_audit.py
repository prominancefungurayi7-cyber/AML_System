"""Independent model-free persisted-data audit; no generator imports or ML dependencies."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics

from contracts import (ROOT, PARTITIONS, DEVELOPMENT, EVENT_FIELDS, TRUTH_FIELDS,
                      WALLET_FIELDS, AGENT_FIELDS, BASIS, read_csv, safe_path,
                      partition_path, digest, write_json)

START=datetime(2025,1,1,tzinfo=timezone.utc)
END=START+timedelta(days=180)


def time_value(s):
    value=datetime.strptime(s,'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
    if value.strftime('%Y-%m-%dT%H:%M:%S.%fZ')!=s:
        raise ValueError('Timestamp is not normalized to fixed UTC microseconds')
    return value


def category(e):
    if e['transaction_type']=='cash_in': return 0
    if e['transaction_type']=='cash_out': return 1
    return 2 if e['channel']=='agent' else 3


def audit(dataset_root):
    root=safe_path(dataset_root)
    allocation=json.loads((ROOT/'design/allocation_manifest.json').read_text(encoding='utf-8'))
    scenarios=json.loads((ROOT/'design/scenario_manifest.json').read_text(encoding='utf-8'))
    manifest=json.loads((root/'manifests/generation_manifest.json').read_text(encoding='utf-8'))
    failures=[]
    check_counts=Counter()

    def check(condition,name):
        check_counts[name]+=1
        if not condition and len(failures)<100:
            failures.append(name)

    expected_files={'manifests/generation_manifest.json'} | set(manifest['file_hashes'])
    actual_files={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    check(actual_files==expected_files,'exact_file_inventory')
    for rel,h in manifest['file_hashes'].items():
        check(digest(safe_path(root/rel))==h,'file_hash')
    all_ids=set(); wallet_sets={}; agent_sets={}; customer_sets={}; episode_sets={}
    global_events=[]; results={}; episode_signatures={}; overlaps={}
    family_lookup={v['name']:k for k,v in scenarios['families'].items()}
    for partition in PARTITIONS:
        folder=partition_path(root,partition)
        q=allocation['partitions'][partition]
        events=read_csv(folder/'transactions.csv'); truth=read_csv(folder/'ground_truth.csv')
        wallets=read_csv(folder/'wallets.csv'); agents=read_csv(folder/'agents.csv')
        plans=json.loads((folder/'episode_plans.json').read_text(encoding='utf-8'))['episodes']
        commitment=json.loads((folder/'membership_commitment.json').read_text(encoding='utf-8'))
        check(hashlib.sha256(json.dumps(commitment['membership'],sort_keys=True,separators=(',',':')).encode()).hexdigest()==commitment['sha256'],'membership_commitment_hash')
        committed={p['episode_id']:p for p in commitment['membership']}
        role=json.loads((folder/'partition_role.json').read_text(encoding='utf-8'))
        check(role['training_allowed']==(partition in DEVELOPMENT),'partition_access_role')
        check(role['role']==('development' if partition in DEVELOPMENT else 'HOLDOUT'),'holdout_marker')
        for rows, fields in [(events,EVENT_FIELDS),(truth,TRUTH_FIELDS),(wallets,WALLET_FIELDS),(agents,AGENT_FIELDS)]:
            check(bool(rows) and list(rows[0])==fields,'exact_schema_allowlist')
        check(len(events)==q['transactions'],'partition_rows')
        check(len(truth)==len(events),'ground_truth_row_count')
        ws={w['wallet_id']:w for w in wallets}; ags={a['agent_id']:a for a in agents}
        wallet_sets[partition]=set(ws); agent_sets[partition]=set(ags)
        customer_sets[partition]={w['customer_id'] for w in wallets}
        check(len(wallets)==len(ws)==q['wallets'],'wallet_count_uniqueness')
        check(len(customer_sets[partition])==q['wallets'],'one_wallet_per_customer')
        check(len(agents)==len(ags)==q['agents'],'agent_count_uniqueness')
        check(Counter(w['profile_type'] for w in wallets)==dict(zip(('personal','small_business','merchant','seasonal_income'),q['wallet_profiles'])),'wallet_profile_allocation')
        check(Counter(a['activity_band'] for a in agents)==dict(zip(('lower','medium','higher'),q['agent_bands'])),'agent_band_allocation')
        for entity in wallets+agents:
            check(entity['partition']==partition,'entity_partition')
            time_value(entity['activation_timestamp'])
        balances={w:int(r['initial_balance_minor']) for w,r in ws.items()}
        floats={a:int(r['initial_float_minor']) for a,r in ags.items()}
        check(set(balances.values())=={scenarios['initial_liquidity']['wallet_minor']},'ex_ante_wallet_funding')
        check(set(floats.values())=={scenarios['initial_liquidity']['agent_minor']},'ex_ante_agent_funding')
        initial_total=sum(balances.values())+sum(floats.values())
        min_balance=min(balances.values()); min_float=min(floats.values())
        labels={int(t['transaction_id']):t for t in truth}
        check(len(labels)==len(truth),'no_duplicate_labels')
        check(set(labels)=={int(e['transaction_id']) for e in events},'one_to_one_ground_truth')
        classes=Counter(); domains=Counter(); families=Counter(); strengths=Counter(); hard=Counter()
        family_strength=Counter(); family_cats=defaultdict(Counter); normal_cats=defaultdict(Counter)
        categories=Counter(); class_cats=Counter(); blocks=Counter(); episodes=defaultdict(list)
        previous=None; equal_timestamps=0; cash_self=0
        for e in events:
            tid=int(e['transaction_id']); timestamp=time_value(e['event_timestamp']); order=(timestamp,tid)
            check(tid not in all_ids,'global_id_unique'); all_ids.add(tid)
            check(int(e['event_sequence'])==tid,'sequence_equals_id')
            check(previous is None or previous<order,'strict_partition_causal_order')
            if previous and previous[0]==timestamp: equal_timestamps+=1
            previous=order
            global_events.append((timestamp,tid))
            check(START<=timestamp<END,'180_day_support')
            s,r,a=e['sender_wallet'],e['receiver_wallet'],e['agent_id']; value=int(e['amount_minor'])
            check(100<=value<=2500000,'positive_bounded_integer_amount')
            check(e['currency']=='USD','currency')
            check(s in ws and r in ws,'partition_local_endpoints')
            check(time_value(ws[s]['activation_timestamp'])<=timestamp and time_value(ws[r]['activation_timestamp'])<=timestamp,'wallet_activation')
            kind=e['transaction_type']; channel=e['channel']; service=e['serviced_wallet']
            check(kind in ('cash_in','cash_out','wallet_to_wallet'),'valid_transaction_type')
            check(channel in ('agent','direct_wallet'),'valid_channel')
            if channel=='agent':
                check(a in ags and service in (s,r),'valid_agent_attribution')
                check(time_value(ags[a]['activation_timestamp'])<=timestamp,'agent_activation')
            else:
                check(a==service=='' and kind=='wallet_to_wallet','direct_wallet_nulls')
            if kind=='wallet_to_wallet':
                check(s!=r,'zero_transfer_self_loops')
                check(e['agent_flow_direction']=='none','transfer_no_float_movement')
                balances[s]-=value; balances[r]+=value
            else:
                check(s==r==service and channel=='agent','cash_bookkeeping')
                cash_self+=s==r
                check(e['agent_flow_direction']==('outbound' if kind=='cash_in' else 'inbound'),'cash_direction')
                if kind=='cash_in': floats[a]-=value; balances[s]+=value
                else: balances[s]-=value; floats[a]+=value
            min_balance=min(min_balance,balances[s],balances[r])
            if a: min_float=min(min_float,floats[a])
            check(balances[s]>=0 and balances[r]>=0 and (not a or floats[a]>=0),'no_negative_balance_or_float')
            t=labels[tid]; target=int(t['target']); c=category(e)
            check(target in (0,1),'binary_target')
            check(t['label_basis']==BASIS,'label_basis')
            classes[target]+=1; categories[c]+=1; class_cats[target,c]+=1
            blocks[target,(timestamp-START).days//30]+=1
            if target==1:
                check(t['primary_family'] in family_lookup,'valid_suspicious_family')
                fid=family_lookup[t['primary_family']]
                check(t['primary_domain']==scenarios['families'][fid]['domain'],'domain_family_consistency')
                check(t['normal_family']==t['normal_episode_id']=='' and bool(t['episode_id']),'suspicious_metadata_consistency')
                check(t['signal_strength'] in ('weak','moderate','strong'),'valid_signal_strength')
                domains[t['primary_domain']]+=1; families[fid]+=1; strengths[t['signal_strength']]+=1
                family_strength[fid,t['signal_strength']]+=1; family_cats[fid][c]+=1
                eid=t['episode_id']
            else:
                check(t['primary_domain']==t['primary_family']==t['episode_id']==t['signal_strength']=='','normal_metadata_consistency')
                check(t['normal_family'] in ['routine']+[f'H{i}' for i in range(1,9)],'valid_normal_family')
                hard[t['normal_family']]+=1; normal_cats[t['normal_family']][c]+=1
                eid=t['normal_episode_id']
                check(bool(eid)==(t['normal_family']!='routine'),'normal_episode_membership')
            if eid: episodes[eid].append((e,t))
            else: check(t['episode_phase']=='not_applicable','routine_phase')
        check(classes=={0:q['normal'],1:q['suspicious']},'class_counts')
        check(domains==dict.fromkeys(('structuring','network','agent'),q['suspicious']//3),'domain_counts')
        check(categories==dict.fromkeys(range(4),q['transactions']//4),'category_counts')
        for c in range(4):
            check(class_cats[0,c]==q['normal']//4 and class_cats[1,c]==q['suspicious']//4,'class_category_counts')
        for fid, budget in q['family_categories'].items():
            check(families[fid]==sum(budget),'family_count')
            check([family_cats[fid][c] for c in range(4)]==budget,'family_category_allocation')
            for strength,n in q['family_strength'].items(): check(family_strength[fid,strength]==n,'family_strength_count')
        for fid,budget in {**q['hard_categories'],'routine':q['routine_categories']}.items():
            check(hard[fid]==sum(budget),'hard_normal_count')
            check([normal_cats[fid][c] for c in range(4)]==budget,'normal_category_allocation')
        for b in range(6):
            check(blocks[0,b]==q['normal_blocks'][b] and blocks[1,b]==q['positive_blocks'][b],'exact_block_counts')
        check(sum(balances.values())+sum(floats.values())==initial_total,'conserved_electronic_value')
        plan_ids={p['episode_id'] for p in plans}; episode_sets[partition]=plan_ids
        check(len(plan_ids)==len(plans) and plan_ids==set(episodes),'complete_episode_plan_join')
        for p in plans:
            rows=episodes[p['episode_id']]; spec=scenarios['families'][p['pattern']]
            check({k:p[k] for k in ('episode_id','family','strength','size','block','target','pattern')}==committed[p['episode_id']],'unchanged_precommitted_membership')
            check(len(rows)==p['size'] and sorted(p['transaction_ids'])==[int(e['transaction_id']) for e,_ in rows],'no_truncated_episode')
            check((spec['min_events'] if p['target'] else 6)<=len(rows)<=(spec['max_events'] if p['target'] else 24),'episode_length_support')
            for i,(e,t) in enumerate(rows):
                check(int(t['target'])==p['target'] and t['signal_strength']==p['strength'],'precommitted_plan_membership')
                expected_phase='early' if i<math.ceil(len(rows)*.25) else ('late' if i>=len(rows)-math.ceil(len(rows)*.25) else 'established')
                check(t['episode_phase']==expected_phase,'precommitted_phase')
            actual_duration=(time_value(rows[-1][0]['event_timestamp'])-time_value(rows[0][0]['event_timestamp'])).total_seconds()
            check(abs(actual_duration-p['duration'])<.000003,'episode_schedule_duration')
            check(spec['min_seconds']<=p['duration']-p['continuation_days']*86400<=spec['max_seconds']+.000001,'family_duration_support')
            graph=[e for e,_ in rows if e['transaction_type']=='wallet_to_wallet']
            pattern=p['pattern']
            if pattern=='N1':
                check(len({e['receiver_wallet'] for e in graph})==1 and 3<=len({e['sender_wallet'] for e in graph})<=12,'collection_graph_roles')
            elif pattern=='N2':
                check(len({e['sender_wallet'] for e in graph})==1 and 3<=len({e['receiver_wallet'] for e in graph})<=12,'dispersion_graph_roles')
            elif pattern=='N3':
                check(Counter(e['sender_wallet'] for e in graph)==Counter(e['receiver_wallet'] for e in graph),'closed_reciprocal_cycles')
            elif pattern=='N4':
                center=p['central_wallet']
                incoming=sum(int(e['amount_minor']) for e,_ in rows if e['transaction_type']=='cash_in' or (e['transaction_type']=='wallet_to_wallet' and e['receiver_wallet']==center))
                outgoing=sum(int(e['amount_minor']) for e,_ in rows if e['transaction_type']=='cash_out' or (e['transaction_type']=='wallet_to_wallet' and e['sender_wallet']==center))
                check(.50-.0001<=outgoing/incoming<=.98+.0001,'pass_through_retention')
            elif pattern=='S4':
                fraction=sum(700000<=int(e['amount_minor'])<=1050000 for e,_ in rows)/len(rows)
                check(.25<=fraction<=.60,'near_threshold_partial_membership')
            elif pattern=='A1':
                check(4<=len({e['serviced_wallet'] for e,_ in rows})<=17,'agent_growth_wallet_roles')
            elif pattern=='A4':
                cash=[e for e,_ in rows[:3]]
                check(all(e['transaction_type'] in ('cash_in','cash_out') for e in cash),'agent_imbalance_cash_portion')
                check(cash[0]['transaction_type']==cash[1]['transaction_type']!=cash[2]['transaction_type'],'agent_imbalance_count_portion')
                values=[int(e['amount_minor']) for e in cash]
                check(.60<=(values[0]+values[1])/sum(values)<=.95,'agent_imbalance_value_portion')
            # Canonicalize complete timed/value-labelled sequences. Common bare motifs are expected.
            identities={}; canon=[]; origin=time_value(rows[0][0]['event_timestamp'])
            for e,_ in rows:
                nodes=[]
                for key in ('sender_wallet','receiver_wallet','agent_id'):
                    value=e[key]
                    if value not in identities: identities[value]=len(identities)
                    nodes.append(identities[value])
                canon.append([*nodes,e['transaction_type'],e['channel'],e['amount_minor'],(time_value(e['event_timestamp'])-origin).total_seconds()])
            sig=hashlib.sha256(json.dumps(canon).encode()).hexdigest()
            check(sig not in episode_signatures,'no_copied_complete_episode_sequence')
            episode_signatures[sig]=partition
        # Descriptive overlap uses development data only, never the held-out populations.
        if partition in DEVELOPMENT:
            groups=defaultdict(list); durations=defaultdict(list); sizes=defaultdict(list)
            for e in events:
                t=labels[int(e['transaction_id'])]
                group='suspicious' if t['target']=='1' else t['normal_family']
                groups[group].append(int(e['amount_minor']))
            for p in plans:
                group='suspicious' if p['target'] else p['family']
                durations[group].append(p['duration']); sizes[group].append(p['size'])
            bins=[100,1000,10000,100000,700000,1000000,1050001,2500001]
            overlap={}
            for group,values in groups.items():
                overlap[group]={'amount_min':min(values),'amount_median':statistics.median(values),'amount_max':max(values),
                    'amount_bin_counts':[sum(lo<=v<hi for v in values) for lo,hi in zip(bins,bins[1:])],
                    'below_threshold':sum(v<1000000 for v in values),'above_threshold':sum(v>1000000 for v in values)}
                if group in durations:
                    overlap[group].update(duration_seconds_range=[min(durations[group]),max(durations[group])],event_count_range=[min(sizes[group]),max(sizes[group])])
            for h in (f'H{i}' for i in range(1,9)):
                shared=sum(x>0 and y>0 for x,y in zip(overlap[h]['amount_bin_counts'],overlap['suspicious']['amount_bin_counts']))
                check(shared>=5,'development_hard_negative_amount_overlap')
                check(max(min(durations[h]),min(durations['suspicious']))<=min(max(durations[h]),max(durations['suspicious'])),'development_hard_negative_duration_overlap')
                check(max(min(sizes[h]),min(sizes['suspicious']))<=min(max(sizes[h]),max(sizes['suspicious'])),'development_hard_negative_activity_overlap')
            overlaps[partition]={'amount_bin_edges_minor':bins,'groups':overlap}
        results[partition]={'rows':len(events),'classes':dict(classes),'domains':dict(domains),'families':dict(families),
            'strengths':dict(strengths),'normal_families':dict(hard),'categories':dict(categories),
            'wallets':len(ws),'customers':len(customer_sets[partition]),'agents':len(ags),'episodes':len(plans),
            'first_timestamp':events[0]['event_timestamp'],'last_timestamp':events[-1]['event_timestamp'],
            'equal_timestamp_pairs':equal_timestamps,'cash_same_wallet_records':cash_self,'transfer_self_loops':sum(e['transaction_type']=='wallet_to_wallet' and e['sender_wallet']==e['receiver_wallet'] for e in events),
            'minimum_wallet_balance_minor':min_balance,'minimum_agent_float_minor':min_float,
            'positive_blocks':[blocks[1,b] for b in range(6)],'normal_blocks':[blocks[0,b] for b in range(6)]}
    for sets in (wallet_sets,agent_sets,customer_sets,episode_sets):
        for i,p in enumerate(PARTITIONS):
            for other in PARTITIONS[i+1:]: check(not sets[p]&sets[other],'partition_entity_episode_disjointness')
    check(all_ids==set(range(1,100001)),'global_id_range')
    chronological=sorted(global_events)
    check([tid for _,tid in chronological]==list(range(1,100001)),'global_chronological_id_assignment')
    return {'result':'FAIL' if failures else 'PASS','failures':failures,'checks':dict(check_counts),'partitions':results,
        'development_overlap':overlaps,'temporal_contract':{'ordering':['event_timestamp','transaction_id'],'windows_seconds':[3600,86400,604800,2592000],
        'feature_replay_executed':False,'cold_start':'Partial history is valid; no hidden warm-up'},
        'limitations':['Software access guard is not an OS security boundary.',
        'Descriptive overlap does not prove absence of every single-variable shortcut.',
        'Initial liquidity is deliberately ample and fixed; this experiment does not model operational liquidity scarcity.',
        'Synthetic scenario membership is not evidence of real-world crime.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--dataset',type=Path,required=True); p.add_argument('--report',type=Path,required=True)
    args=p.parse_args(); result=audit(args.dataset); write_json(args.report,result)
    print(result['result']); print(json.dumps(result['failures']))
    raise SystemExit(1 if result['failures'] else 0)
