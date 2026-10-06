"""Additional aggregate correlations and diagnostic identity checks, no fits."""
import csv,json
import numpy as np
from stage19_analysis import ROOT,OUT,read,save,allowed

def main():
    result={}
    fields=['agent_wallet_growth_ratio_7d','agent_distinct_wallets_7d','agent_new_wallet_count_7d','agent_new_wallet_share_7d']
    for part in ['train','validation']:
        base=ROOT/'ml_v4/development_features/matrices'/part
        x=np.load(base/'X.npy',allow_pickle=False)
        ids=[int(r['transaction_id']) for r in csv.DictReader((base/'row_metadata.csv').open())]
        truth={r['transaction_id']:r for r in (json.loads(s) for s in allowed(part,'family_evidence.jsonl').read_text().splitlines())}
        m=np.array(['N1' in truth[i]['families'] for i in ids])
        valid=x[fields[0]]!=-1
        corr=np.corrcoef(np.column_stack([x[f][valid] for f in fields]),rowvar=False)
        derived_n=x['wallet_similar_amount_count_7d']/x['wallet_similar_amount_share_7d']
        result[part]={'N1_positive_acceleration_equals_count':int((x['network_in_count_24h'][m]==x['network_in_acceleration_24h'][m]).sum()),'N1_support':int(m.sum()),
            'eligible_A1_rows':int(valid.sum()),'A1_Pearson_fields':fields,'A1_Pearson_matrix':corr.tolist(),
            'derived_recent_count_max_distance_from_integer':float(np.max(np.abs(derived_n-np.rint(derived_n)))),
            'all_similar_shares_positive':bool((x['wallet_similar_amount_share_7d']>0).all())}
    save('component_relationships.json',{'partitions':result,'scope':'Descriptive exact identities and eligible-only Pearson correlations; no causal claim, features saved or new predictions.'})
    p=OUT/'synthetic_shortcut_assessment.json';d=json.loads(p.read_text())
    d['findings'][2]='N1 acceleration equals count for 101/101 Validation and 411/414 Train N1 positives; this follows the denominator floor when baseline frequency is low. It is declared component dependence, not proof of hidden leakage.'
    p.write_text(json.dumps(d,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(result))

if __name__=='__main__':main()
