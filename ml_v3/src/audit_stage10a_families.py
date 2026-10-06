"""Resolve full-name family ledger values for the supplementary oracle audit.

The frozen extraction runner's initial family-code lookup was uninformative.
This correction never changes the contract, extractor, matrices or targets.
"""
from datetime import datetime, timezone
import json
from collections import Counter
from contracts import load_development
from run_stage10a import read_set, save, OUTPUT, EXPECTED
from stage10a_audit import oracle_audit
from stage10a_protection import ROOT, sha, snapshot, compare

FAMILIES=dict(zip(
    ('S1','S2','S3','S4','N1','N2','N3','N4','A1','A2','A3','A4'),
    ('variable_fragment_burst','similar_amount_repetition','distributed_same_day_fragmentation',
     'variable_near_threshold_history','many_to_one_collection','one_to_many_dispersion',
     'reciprocal_relationship_cycle','wallet_pass_through','agent_wallet_growth',
     'agent_wallet_concentration','agent_temporal_burst','agent_flow_imbalance')))

def main():
    r=ROOT/'reports'
    initial=json.loads((r/'stage10a_oracle_leakage.json').read_text())
    repro=json.loads((r/'stage10a_reproducibility.json').read_text())
    before=json.loads((r/'stage10a_protection_before.json').read_text())
    record={'started_at_utc':datetime.now(timezone.utc).isoformat(),
            'source_sha256':sha(Path(__file__)), 'family_mapping':FAMILIES,
            'initial_oracle_record_sha256':sha(r/'stage10a_oracle_leakage.json'),
            'reason':'The initial extraction runner queried S1..A4 codes against a full-family-name ledger, giving uninformative constant outcomes. This additive diagnostic fixes the lookup without changing any frozen extraction code or output. The initial record is preserved.',
            'partitions':{}}
    for part in EXPECTED:
        data=read_set(OUTPUT/part)
        truth=load_development(ROOT/'data',part,'ground_truth')
        evidence={str(int(row['transaction_id'])):set(filter(None,row['evidence_families'].split(';'))) for row in truth}
        observed=set().union(*evidence.values())
        assert observed<=set(FAMILIES.values()),observed-set(FAMILIES.values())
        assert set(evidence)==set(data['row_ids'])
        assert data['y']==[int(bool(evidence[i])) for i in data['row_ids']]
        labels={f:[int(name in evidence[i]) for i in data['row_ids']] for f,name in FAMILIES.items()}
        result=oracle_audit(data,labels)
        assert result['single_features']==initial['partitions'][part]['single_features']
        assert result['two_feature_mappings']==initial['partitions'][part]['two_feature_mappings']
        record['partitions'][part]={'checks':result['frozen_family_predicate_outcome_checks'],
             'support_counts':{f:dict(Counter(v)) for f,v in labels.items()},'result':result['result']}
        for name,digest in repro['runs']['run_a']['partitions'][part]['hashes'].items():
            assert sha(OUTPUT/part/name)==digest
        print(part,result['result'],flush=True)
    assert compare(before,snapshot())['result']=='PASS'
    record['result']='PASS' if all(x['result']=='PASS' for x in record['partitions'].values()) else 'REVIEW'
    record['feature_artifacts_unchanged']=True
    save(r/'stage10a_family_oracle_leakage.json',record)
    print(record['result'],flush=True)

from pathlib import Path
if __name__=='__main__': main()
