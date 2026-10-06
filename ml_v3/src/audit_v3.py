"""Independent model-free V3 structural audit. No feature or model imports."""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
import hashlib, json
from pathlib import Path

from contracts import ROOT, PARTITIONS, DEVELOPMENT, EVENT_FIELDS, TRUTH_FIELDS, WALLET_FIELDS, AGENT_FIELDS, partition_path, read_csv, safe_path, digest

EXPECTED={'train':(60000,600,96),'validation':(15000,150,24),'final_test':(15000,150,24),'independent':(10000,100,16)}
START=datetime(2025,1,1,tzinfo=timezone.utc); END=START.replace(day=1)+__import__('datetime').timedelta(days=180)
def dt(x): return datetime.strptime(x,'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)

def audit(root, sample_evaluator=None):
    root=safe_path(root); failures=[]; checks=Counter(); parts={}; all_wallets=set(); all_agents=set(); all_ids=[]
    def check(ok,name): checks[name]+=1; (failures.append(name) if not ok and name not in failures else None)
    for part in PARTITIONS:
        folder=partition_path(root,part); events=read_csv(folder/'transactions.csv'); truth=read_csv(folder/'ground_truth_v3.csv'); wallets=read_csv(folder/'wallets.csv'); agents=read_csv(folder/'agents.csv')
        n,nw,na=EXPECTED[part]; check(len(events)==n,'row_count'); check(len(truth)==n,'truth_count'); check(len(wallets)==nw,'wallet_count'); check(len(agents)==na,'agent_count')
        check(list(events[0])==EVENT_FIELDS,'observable_schema'); check(list(truth[0])==TRUTH_FIELDS,'truth_schema'); check(list(wallets[0])==WALLET_FIELDS,'wallet_schema'); check(list(agents[0])==AGENT_FIELDS,'agent_schema')
        ws={x['wallet_id'] for x in wallets}; ag={x['agent_id'] for x in agents}; check(len(ws)==nw,'wallet_unique'); check(len(ag)==na,'agent_unique'); check(not all_wallets&ws,'wallet_partition_isolation'); check(not all_agents&ag,'agent_partition_isolation'); all_wallets|=ws; all_agents|=ag
        tmap={int(x['transaction_id']):x for x in truth}; check(len(tmap)==n,'truth_ids_unique'); previous=None; targets=Counter(); origins=Counter(); hard=Counter(); campaigns=Counter(); witnesses=0; raw_ids=[]
        for e in events:
            tid=int(e['transaction_id']); raw_ids.append(tid); order=(dt(e['event_timestamp']),tid); check(previous is None or previous<order,'strict_order'); previous=order; all_ids.append(tid); check(100<=int(e['amount_minor'])<=2500000,'amount_support'); check(e['currency']=='USD','currency'); check(e['sender_wallet'] in ws and e['receiver_wallet'] in ws,'local_wallets'); check(e['transaction_type'] in ('cash_in','cash_out','wallet_to_wallet'),'transaction_type'); check(e['channel'] in ('agent','direct_wallet'),'channel')
            if e['transaction_type']=='wallet_to_wallet': check(e['sender_wallet']!=e['receiver_wallet'],'no_self_loop'); check(e['agent_flow_direction']=='none','w2w_float_none')
            else: check(e['sender_wallet']==e['receiver_wallet']==e['serviced_wallet'] and e['channel']=='agent','cash_semantics'); check(e['agent_flow_direction']==('outbound' if e['transaction_type']=='cash_in' else 'inbound'),'cash_direction')
            if e['channel']=='agent': check(e['agent_id'] in ag and e['serviced_wallet'] in (e['sender_wallet'],e['receiver_wallet']),'agent_semantics')
            else: check(e['agent_id']==e['serviced_wallet']=='','direct_nulls')
            y=tmap[tid]; target=int(y['decision_point_target']); check(target in (0,1),'binary_target'); targets[target]+=1; origins[y['origin_cohort']]+=1; check(y['predicate_version']=='v3_onset_contract_rev1','predicate_version'); check(list(e)==EVENT_FIELDS,'no_truth_leakage');
            if target: check(y['evidence_families']!='','positive_witness'); witnesses+=bool(y['evidence_families'])
            if y['origin_cohort']=='hard_scenario': hard[(y['scenario_family'],target)]+=1
            if y['scenario_member']: campaigns[(y['scenario_family'],target)]+=1
        check(sorted(raw_ids)==raw_ids,'partition_ids_sorted'); check(len(set(raw_ids))==n,'partition_ids_unique'); parts[part]={'rows':n,'wallets':nw,'agents':na,'targets':dict(targets),'origins':dict(origins),'campaign_member_targets':{f'{k[0]}:{k[1]}':v for k,v in campaigns.items()},'hard_origin_targets':{f'{k[0]}:{k[1]}':v for k,v in hard.items()},'positive_witness_rows':witnesses,'first_timestamp':events[0]['event_timestamp'],'last_timestamp':events[-1]['event_timestamp']}
        if sample_evaluator and part in DEVELOPMENT:
            sample=events[:min(1000,len(events))]; calculated=sample_evaluator(sample); truth_by={int(x['transaction_id']):x for x in truth}; check(all(int(bool(c['families']))==int(truth_by[int(c['event']['transaction_id'])]['decision_point_target']) for c in calculated),'evaluator_sample_alignment')
    check(len(all_ids)==100000,'total_rows'); check(len(set(all_ids))==100000,'global_ids_unique'); check(set(all_ids)==set(range(1,100001)),'global_id_range')
    for part in PARTITIONS:
        role=json.loads((partition_path(root,part)/'partition_role.json').read_text(encoding='utf-8')); check(role['role']==('development' if part in DEVELOPMENT else 'HOLDOUT'),'partition_role'); check(role['training_allowed']==(part in DEVELOPMENT),'training_role')
    check(len(all_wallets)==1000,'total_wallets'); check(len(all_agents)==160,'total_agents')
    return {'result':'FAIL' if failures else 'PASS','failures':failures,'checks':dict(checks),'partitions':parts,'total':{'rows':len(all_ids),'wallets':len(all_wallets),'agents':len(all_agents)},'feature_extraction_executed':False,'model_training_executed':False}
