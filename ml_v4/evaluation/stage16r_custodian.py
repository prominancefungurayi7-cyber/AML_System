"""Isolated-process production custodian. Releases fixed public booleans only.

Raw evaluation ledgers, salt, hashes, labels and diagnostics exist in this
process's memory then only in a DPAPI-encrypted ZIP. Never logs detailed data.
"""
import csv
import hashlib
import io
import json
import os
import sys
import zipfile
from pathlib import Path
from collections import Counter

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'generation'))
from stage16r_contract import ROOT,DAY,FAMILIES,event_from_row,json_bytes,save_json
from stage16r_generator import generate_partition
from stage16r_audit import partition_files,integrity
from stage16r_evaluator import replay
from stage16r_seal import protect


def run():
    registry=json.loads((ROOT/'ml_v4/evidence/stage16r/draw_registry.json').read_text())
    if registry['status']!='DEVELOPMENT_COMPLETE': raise PermissionError('Custodian production boundary not authorized by registry')
    root=ROOT/'ml_v4/evaluation/sealed'
    if root.exists(): raise FileExistsError('Seal namespace already exists')
    root.mkdir()
    salt=os.urandom(32)
    wallets=set(); agents=set(); ids=set()
    for name in ('train','validation'):
        d=ROOT/'ml_v4/data/development'/name
        pops=json.loads((d/'private_population.json').read_text())
        wallets.update(w['id'] for p in pops for w in p['wallets'])
        agents.update(a['id'] for p in pops for a in p['agents'])
        for file in ('warmup_observables.csv','transactions.csv'):
            with (d/file).open() as stream: ids.update(int(r['transaction_id']) for r in csv.DictReader(stream))
    public_cert={}
    private={}; payload={}; support_all=True
    for name,units,minimum,subject_min,cluster_min in [('final_test',3,300,20,30),('independent_evaluation',2,200,12,20)]:
        events,provenance,populations=generate_partition(name,units,salt)
        basic=integrity(events,populations,units)
        ww={w['id'] for p in populations for w in p['wallets']}; aa={a['id'] for p in populations for a in p['agents']}; ii={e.transaction_id for e in events}
        if ww&wallets or aa&agents or ii&ids: raise AssertionError('Cross-partition collision')
        wallets|=ww; agents|=aa; ids|=ii
        files,truth=partition_files(events,provenance,populations)
        clean=[]
        for file in ('warmup_observables.csv','transactions.csv'):
            clean.extend(event_from_row(row) for row in csv.DictReader(io.StringIO(files[file].decode())))
        reproduced=[r for e,r in zip(clean,replay(clean)) if e.time>=42*DAY]
        if reproduced!=truth: raise AssertionError('Custodian observable replay mismatch')
        by_id={p['transaction_id']:p for p in provenance}; by_event={e.transaction_id:e for e in events}
        supports={}
        for f in FAMILIES:
            rows=[r for r in truth if f in r['families']]
            subjects=set(); clusters=set()
            for r in rows:
                e=by_event[r['transaction_id']]; p=by_id[e.transaction_id]
                subjects.add(e.agent_id if f.startswith('A') else e.receiver_wallet if f=='N1' else e.subject)
                clusters.add(p['scenario_id'] if p['scenario_id'] is not None else f"b:{p['population_unit']}:{e.time//DAY}")
            supports[f]={'n':len(rows),'subjects':len(subjects),'clusters':len(clusters)}
        prevalence=sum(r['ground_truth_label'] for r in truth)/len(truth)
        support=all(s['n']>=minimum and s['subjects']>=subject_min and s['clusters']>=cluster_min for s in supports.values()) and .1<=prevalence<=.45
        support_all &= support
        public_cert[name]={'schema':'PASS','row_counts':'PASS','entity_isolation':'PASS','causal_evaluator':'PASS','support_policy':'PASS' if support else 'FAIL','sealing':'PASS'}
        private[name]={'integrity':basic,'support':supports,'prevalence':prevalence}
        payload.update({name+'/'+key:value for key,value in files.items()})
    hashes={key:hashlib.sha256(value).hexdigest() for key,value in payload.items()}
    manifest={'dataset_id':registry['dataset_id'],'salt_hex':salt.hex(),'private_hashes':hashes,'design_sha256':registry['design_sha256'],'source_sha256':registry['source_sha256'],'audit':private}
    commitment=hashlib.sha256(salt+json_bytes(hashes)).hexdigest()
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for key,value in sorted(payload.items()): archive.writestr(key,value)
        archive.writestr('private_manifest.json',json_bytes(manifest))
    blob=protect(buffer.getvalue())
    with (root/'evaluation.dpapi').open('xb') as stream: stream.write(blob)
    public={'dataset_id':registry['dataset_id'],'commitment_id':commitment,'salt_commitment':hashlib.sha256(salt).hexdigest(),'encrypted_envelope_sha256':hashlib.sha256(blob).hexdigest(),'design_sha256':registry['design_sha256'],'certificates':public_cert,'disposition':'SEALED' if support_all else 'SEALED_QUARANTINED','boundary':'Separate process; Windows current-user DPAPI. No plaintext evaluation files mounted in the development directory. Not a separate-account or adversarial OS isolation claim.'}
    save_json(root/'public_commitment.json',public)
    print(json.dumps({'custodian':'COMPLETE','public_metadata':'ml_v4/evaluation/sealed/public_commitment.json'}))


if __name__=='__main__':
    try: run()
    except Exception as exc:
        # Avoid traces or variable values that might expose private observations.
        print(json.dumps({'custodian':'FAILED','error_type':type(exc).__name__}))
        sys.exit(1)
