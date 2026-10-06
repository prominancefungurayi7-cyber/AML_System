"""Authorized V3 Stage 10 feature extraction and model-free audit."""
from __future__ import annotations
import hashlib, json, math, shutil
from pathlib import Path

from contracts import ROOT, load_development
from feature_contract import FEATURE_NAMES
from feature_pipeline import extract_development, write_matrices
from feature_audit import feature_statistics, matrix_audit, target_overlap, temporal_checks, metadata_independence


def _sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _allowlisted_hashes():
    base=ROOT.parent; paths=[]
    for rel in ('app.py','models.py','templates','static','scripts','ml_v2/src','ml_v2/reports'):
        p=base/rel
        if p.is_file(): paths.append(p)
        elif p.is_dir(): paths.extend(x for x in p.rglob('*') if x.is_file() and '__pycache__' not in x.parts)
    return {str(p.relative_to(base)):_sha(p) for p in sorted(paths)}


def _write(path, value):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')


def _private_metadata_audit(matrices):
    forbidden=('transaction_id','event_sequence','sender_wallet','receiver_wallet','agent_id','campaign_id','scenario_member','scenario_family','origin_cohort','signal_strength','decision_point_target','evidence_families','evidence_subjects','witness_transaction_ids','onset_transaction_id','risk_score','rule_score')
    bad=[name for name in FEATURE_NAMES if name in forbidden]
    return {'forbidden_feature_names':bad,'feature_count':len(FEATURE_NAMES),'result':'PASS' if not bad else 'FAIL'}


def main():
    report=ROOT/'reports'; data_root=ROOT/'data'
    contract=report/'V3_STAGE10_FEATURE_CONTRACT.md'
    if not contract.exists(): raise FileNotFoundError('feature contract must exist before extraction')
    if not (report/'V3_STAGE9_HOLDOUT_SEAL.json').exists(): raise FileNotFoundError('Stage 9 public commitment missing')
    before=_allowlisted_hashes()
    first=extract_development(data_root)
    second=extract_development(data_root)
    same=all(first[p]['row_ids']==second[p]['row_ids'] and first[p]['y']==second[p]['y'] and first[p]['X']==second[p]['X'] for p in ('train','validation'))
    if not same: raise RuntimeError('feature extraction is not deterministic')
    # Only development matrices are materialized.
    feature_root=ROOT/'features'
    if (feature_root/'evaluation').exists(): raise RuntimeError('evaluation feature directory already exists')
    write_matrices(ROOT,first)
    audits={p:matrix_audit(first[p]) for p in ('train','validation')}
    if any(a['result']=='FAIL' if 'result' in a else (not a['all_numeric_finite'] or a['duplicate_row_id_count']) for a in audits.values()):
        raise RuntimeError('matrix audit failed')
    stats={p:feature_statistics(first[p]['X']) for p in ('train','validation')}
    overlaps={p:target_overlap(first[p]) for p in ('train','validation')}
    shifts={}
    for name in FEATURE_NAMES:
        a=stats['train'][name]; b=stats['validation'][name]
        shifts[name]={'train_mean':a['mean'],'validation_mean':b['mean'],'mean_difference':b['mean']-a['mean'],
                      'train_zero_fraction':a['zero_fraction'],'validation_zero_fraction':b['zero_fraction'],
                      'zero_fraction_difference':b['zero_fraction']-a['zero_fraction'],
                      'train_min':a['minimum'],'train_max':a['maximum'],'validation_min':b['minimum'],'validation_max':b['maximum']}
    temporal=temporal_checks(__import__('feature_pipeline',fromlist=['extract']).extract)
    private=metadata_independence(__import__('feature_pipeline',fromlist=['extract']).extract)
    oracle=_private_metadata_audit(first)
    after=_allowlisted_hashes()
    protection={'result':'PASS' if before==after else 'FAIL','before_count':len(before),'after_count':len(after),'changed':[k for k in before.keys()|after.keys() if before.get(k)!=after.get(k)]}
    reproducibility={'result':'PASS' if same else 'FAIL','row_order_identical':same,'feature_order_identical':same,'numeric_values_identical':same,'targets_identical':same,
                     'train_rows':len(first['train']['X']),'validation_rows':len(first['validation']['X']),'feature_count':len(FEATURE_NAMES),
                     'output_hashes':{p:{f:_sha(feature_root/'development'/p/f) for f in ('X.csv','y.csv','row_ids.csv','feature_names.json')} for p in ('train','validation')}}
    _write(report/'stage10_feature_statistics.json',{'train':stats['train'],'validation':stats['validation'],'matrix_audit':audits})
    _write(report/'stage10_shift_audit.json',shifts)
    _write(report/'stage10_target_overlap.json',overlaps)
    _write(report/'stage10_temporal_tests.json',{'temporal':temporal,'private_metadata':private,'oracle':oracle})
    _write(report/'stage10_reproducibility.json',{'reproducibility':reproducibility,'protection':protection})
    print(json.dumps({'result':'PASS' if all((temporal['result']=='PASS',private['result']=='PASS',oracle['result']=='PASS',protection['result']=='PASS')) else 'FAIL',
                      'rows':{p:len(first[p]['X']) for p in ('train','validation')},'features':len(FEATURE_NAMES)},indent=2))


if __name__=='__main__': main()
