from __future__ import annotations
import csv, hashlib, json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTITIONS = ('train','validation','final_test','independent')
DEVELOPMENT = ('train','validation')
EVENT_FIELDS = 'transaction_id event_sequence event_timestamp sender_wallet receiver_wallet amount_minor currency transaction_type channel agent_id serviced_wallet agent_flow_direction'.split()
TRUTH_FIELDS = 'transaction_id decision_point_target scenario_member origin_cohort scenario_family campaign_id scenario_strength evidence_families evidence_subjects witness_transaction_ids own_family_onset_transaction_id campaign_onset_transaction_id predicate_version'.split()
WALLET_FIELDS = 'wallet_id customer_id partition profile_type activity_band initial_balance_minor activation_timestamp'.split()
AGENT_FIELDS = 'agent_id partition activity_band initial_float_minor activation_timestamp'.split()
BASIS='decision_point_reference_v3'

def safe_path(path):
    p=Path(os.path.abspath(path))
    if not p.is_relative_to(ROOT) or p==ROOT: raise ValueError('path outside ml_v3')
    node=ROOT
    if ROOT.is_symlink() or ROOT.is_junction(): raise ValueError('root link')
    for part in p.relative_to(ROOT).parts:
        node=node/part
        if node.is_symlink() or node.is_junction(): raise ValueError('link in v3 path')
    if not p.resolve().is_relative_to(ROOT): raise ValueError('resolved path outside v3')
    return p

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_json(path,value):
    p=safe_path(path); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f: json.dump(value,f,indent=2,sort_keys=True); f.write('\n')
def write_csv(path,fields,rows):
    p=safe_path(path); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n'); w.writeheader(); w.writerows(rows)
def read_csv(path):
    with safe_path(path).open(encoding='utf-8',newline='') as f: return list(csv.DictReader(f))
def partition_path(root,partition):
    if partition not in PARTITIONS: raise ValueError('partition')
    return safe_path(Path(root)/('development' if partition in DEVELOPMENT else 'evaluation')/partition)
def load_development(root,partition,table):
    if partition not in DEVELOPMENT: raise PermissionError('development loader denies evaluation')
    if table not in ('transactions','ground_truth','wallets','agents'): raise ValueError('table')
    filename = 'ground_truth_v3.csv' if table == 'ground_truth' else table+'.csv'
    p=partition_path(root,partition)/filename
    return read_csv(p)
