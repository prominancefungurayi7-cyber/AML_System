"""Verify completed results using only saved development artifacts."""
import json,re
import numpy as np
from run_stage11 import R,M,metrics,load_matrices,EXPECTED
from stage11_protection import ROOT,sha,snapshot,compare

def main():
    result=json.loads((R/'stage11_candidate_results.json').read_text())
    assert result['status']=='complete'
    rows=result['candidates']; plan=result['plan']
    assert len(rows)==len(plan['configurations'])==result['summary']['fits']
    assert [r['name'] for r in rows]==[r['name'] for r in plan['configurations']]
    data=load_matrices()
    for row in rows:
        saved=np.load(M/(row['name']+'_scores.npz'))
        for part in EXPECTED:
            scored=metrics(data[part][1],saved[part])
            assert scored==row[part],(row['name'],part)
            assert row[part]['threshold']==.5
    normal=json.loads((R/'stage11_normal_fpr.json').read_text())
    for name,record in normal.items():
        categories=[v for k,v in record['target0_slices'].items() if '/' not in k]
        row=next(r for r in rows if r['name']==name)
        assert sum(v['support'] for v in categories)==9945
        assert sum(v['fp'] for v in categories)==row['validation']['confusion_matrix'][0][1]
        for v in record['target0_slices'].values(): assert v['fp']+v['tn']==v['support']
    for filename in ('stage11_family_recall.json','stage11_domain_recall.json'):
        for groups in json.loads((R/filename).read_text()).values():
            for v in groups.values(): assert v['tp']+v['fn']==v['support']
    before=json.loads((R/'stage11_protection_before.json').read_text())
    check=compare(before,snapshot()); assert check['result']=='PASS'
    manifest=json.loads((R/'stage11_artifact_manifest.json').read_text())
    for name,digest in manifest.items(): assert sha(M/name)==digest,name
    text=(R/'V3_STAGE11_BASELINE_MODEL_REPORT.md').read_text(encoding='utf-8')
    for target in re.findall(r'\]\(([^)]+)\)',text):
        path=target.split('#')[0]
        if path and not path.startswith(('https:','http:')): assert (R/path).is_file(),path
    assert text.endswith('V3 STAGE 11 COMPLETE '+chr(8212)+' WAITING FOR APPROVAL.\n')
    record=dict(result='PASS',candidate_metrics_recomputed=len(rows)*2,normal_slice_counts_reconcile=True,
                positive_slice_counts_reconcile=True,protected_files_unchanged=len(before['files']),
                model_and_score_artifact_hashes_verified=len(manifest),report_links_verified=True,
                frozen_stage10a_input_hashes_verified=True)
    (R/'stage11_final_verification.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record))

if __name__=='__main__': main()
