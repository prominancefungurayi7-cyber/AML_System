"""V3 raw-event generator and universal decision-point truth materializer."""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path

from contracts import ROOT, PARTITIONS, DEVELOPMENT, EVENT_FIELDS, TRUTH_FIELDS, WALLET_FIELDS, AGENT_FIELDS, digest, write_csv, write_json, read_csv, partition_path, safe_path
from reference_evaluator import evaluate_rows, PREDICATE_VERSION

SEED=20260922
V2_SRC=Path(__file__).resolve().parents[2]/'ml_v2'/'src'
if str(V2_SRC) not in sys.path: sys.path.insert(0,str(V2_SRC))
import dataset_generator as legacy

def _q(partition):
    tx={'train':60000,'validation':15000,'final_test':15000,'independent':10000}[partition]
    wallets={'train':600,'validation':150,'final_test':150,'independent':100}[partition]
    agents={'train':96,'validation':24,'final_test':24,'independent':16}[partition]
    m={'train':1200,'validation':300,'final_test':300,'independent':200}[partition]
    h={'train':2400,'validation':600,'final_test':600,'independent':400}[partition]
    routine=tx-m*12-h*8
    fam={f:[m//4]*4 for f in ('A1','A2','A3','A4','N1','N2','N3','N4','S1','S2','S3','S4')}
    for f in ('N1','N2','N3','N4'): fam[f]=[m//10,m//10,m*4//10,m-m//10-m*4//10-m//10]
    for f in ('S1','S2','S3','S4'): fam[f]=[m*35//100,m*35//100,m*15//100,m-m*35//100-m*35//100-m*15//100]
    for f in ('A1','A2','A3','A4'): fam[f]=[m*35//100,m*35//100,m*30//100,0]
    hard={f:[h//4]*4 for f in ('H1','H2','H3','H4','H5','H6','H7','H8')}
    routine_c=[routine//4]*4; routine_c[-1]+=routine-sum(routine_c)
    normal_blocks=([1266,1266,1268,1266,1266,1268] if tx==10000 else ([7600]*6 if tx==60000 else [1900]*6))
    positive_blocks=([2400]*6 if tx==60000 else ([600]*6 if tx==15000 else [400]*6))
    return {'transactions':tx,'wallets':wallets,'agents':agents,'normal':tx-m*12,'suspicious':m*12,
      'wallet_profiles':[wallets*3//10,wallets*4//10,wallets*2//10,wallets-wallets*9//10],
      'agent_bands':[agents*5//12,agents*7//24,agents-agents*5//12-agents*7//24],
      'family_categories':fam,'family_strength':{'weak':m*2//10,'moderate':m*5//10,'strong':m*3//10},
      'hard_categories':hard,'routine_categories':routine_c,'normal_blocks':normal_blocks,'positive_blocks':positive_blocks}

def allocation(): return {'dataset':'mobile_money_aml_synthetic_100k_v3','partitions':{p:_q(p) for p in PARTITIONS}}

def configure_materializer():
    scenarios=json.loads((ROOT/'design/scenario_manifest.json').read_text(encoding='utf-8'))
    alloc=allocation()
    legacy.ROOT=ROOT; legacy.PARTITIONS=PARTITIONS; legacy.DEVELOPMENT=DEVELOPMENT
    legacy.EVENT_FIELDS=EVENT_FIELDS; legacy.WALLET_FIELDS=WALLET_FIELDS; legacy.AGENT_FIELDS=AGENT_FIELDS
    legacy.TRUTH_FIELDS='transaction_id target primary_domain primary_family episode_id normal_family normal_episode_id signal_strength episode_phase label_basis'.split()
    legacy.safe_path=safe_path; legacy.partition_path=partition_path; legacy.write_csv=write_csv; legacy.write_json=write_json; legacy.digest=digest
    legacy.load_design=lambda:(alloc,scenarios,{'version':1})

def materialize(destination):
    configure_materializer(); return legacy.generate(safe_path(destination),SEED)

def truth_for_partition(folder):
    events=read_csv(folder/'transactions.csv'); old=read_csv(folder/'ground_truth.csv')
    old_by={int(x['transaction_id']):x for x in old}; evaluated=evaluate_rows(events); by={int(x['event']['transaction_id']):x for x in evaluated}
    members={tid for tid,x in old_by.items() if x['primary_family']}
    # Scope onset references to each labelled episode. A family may occur in
    # many independent campaigns within the same partition.
    family_onset={}; campaign_onset={}
    for tid in sorted(by):
        x=by[tid]; oldx=old_by[tid]
        if oldx['episode_id'] and x['families']:
            campaign_onset.setdefault(oldx['episode_id'], tid)
        if oldx['episode_id'] and oldx['primary_family'] in x['families']:
            family_onset.setdefault((oldx['episode_id'], oldx['primary_family']), tid)
    rows=[]
    for tid,x in by.items():
        oldx=old_by[tid]; fams=x['families']; origin='campaign_member' if tid in members else ('hard_scenario' if oldx['normal_family']!='routine' else 'routine')
        subj=x['event']['serviced_wallet'] or x['event']['sender_wallet']
        witnesses={f:x['witnesses'].get(f,[]) for f in fams}
        campaign_start=campaign_onset.get(oldx['episode_id'],'') if tid in members and fams else ''
        family_start=family_onset.get((oldx['episode_id'], oldx['primary_family']),'') if tid in members and oldx['primary_family'] in fams else ''
        rows.append({'transaction_id':tid,'decision_point_target':int(bool(fams)),'scenario_member':int(tid in members),'origin_cohort':origin,
          'scenario_family':oldx['primary_family'] if tid in members else oldx['normal_family'],'campaign_id':oldx['episode_id'] if tid in members else oldx['normal_episode_id'],
          'scenario_strength':oldx['signal_strength'] if tid in members else '', 'evidence_families':';'.join(fams),'evidence_subjects':subj,
          'witness_transaction_ids':json.dumps(witnesses,separators=(',',':'),sort_keys=True),'own_family_onset_transaction_id':family_start,
          'campaign_onset_transaction_id':campaign_start,'predicate_version':PREDICATE_VERSION})
    return rows

def convert_truth(root):
    # The legacy materializer emits a V2 generation manifest.  Remove it
    # before writing the V3 contract manifests so no stale inventory remains.
    stale_manifest = root / 'manifests' / 'generation_manifest.json'
    if stale_manifest.exists():
        stale_manifest.unlink()
    summary={}
    for p in PARTITIONS:
        folder=partition_path(root,p); rows=truth_for_partition(folder); write_csv(folder/'ground_truth_v3.csv',TRUTH_FIELDS,rows); (folder/'ground_truth.csv').unlink()
        origin=Counter(x['origin_cohort'] for x in rows); targets=Counter(int(x['decision_point_target']) for x in rows)
        family=Counter();
        for x in rows:
            for f in x['evidence_families'].split(';') if x['evidence_families'] else []: family[f]+=1
        # JSON object keys must be strings; preserve both dimensions in a
        # stable ``member:target`` / ``family:target`` representation.
        member_targets = Counter((x['scenario_member'], x['decision_point_target']) for x in rows)
        hard_targets = Counter((x['scenario_family'], x['decision_point_target']) for x in rows if x['origin_cohort']=='hard_scenario')
        summary[p]={'rows':len(rows),'targets':dict(targets),'origins':dict(origin),
                    'campaign_member_target_counts':{f'{k[0]}:{k[1]}':v for k,v in member_targets.items()},
                    'hard_origin_targets':{f'{k[0]}:{k[1]}':v for k,v in hard_targets.items()},
                    'routine_target_counts':dict(Counter(x['decision_point_target'] for x in rows if x['origin_cohort']=='routine')),
                    'family_witness_counts':dict(family)}
    return summary

def make_manifest(root,summary):
    files={p.relative_to(root).as_posix():digest(p) for p in sorted(root.rglob('*')) if p.is_file()}
    dev={k:v for k,v in files.items() if k.startswith('development/')}
    ev={k:v for k,v in files.items() if k.startswith('evaluation/')}
    write_json(root/'manifests/development_manifest.json',{'dataset':'mobile_money_aml_synthetic_100k_v3','partition_roles':{'train':'development','validation':'development'},'file_hashes':dev,'summary':summary})
    private={'dataset':'mobile_money_aml_synthetic_100k_v3','seed':SEED,'evaluation_file_hashes':ev,'sealed_after_structural_audit':True}
    write_json(root/'manifests/evaluation_private_manifest.json',private)
    public={'dataset':'mobile_money_aml_synthetic_100k_v3','evaluation_identifier':'v3-evaluation-sealed-20260922','private_manifest_commitment':digest(root/'manifests/evaluation_private_manifest.json'),'structural_audit':'PASS','raw_file_contents':'not included'}
    write_json(root/'manifests/evaluation_content_commitment.json',public)
    return public
