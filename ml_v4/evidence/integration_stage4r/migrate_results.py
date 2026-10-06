"""Apply authorized additive results table; preserve existing recordsets."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from ml_v4.frozen_inference.cli import connection
from v4_shadow import migrate,TABLE
c=connection()
out={}
def snapshot():
    tables={'transactions':'id','canonical_mobile_money_events':'transaction_id','cmm_source_changes':'change_id',
        'cmm_observation_scopes':'scope_id,revision','cmm_history_attestations':'attestation_id','cmm_entity_history':'attestation_id,entity_key'}
    return {t:hashlib.sha256(json.dumps([dict(r) for r in c.execute('SELECT * FROM '+t+' ORDER BY '+order).fetchall()],sort_keys=True,default=str).encode()).hexdigest() for t,order in tables.items()}
try:
    out['before']=snapshot();c.rollback()
    out['created']=migrate(c);c.commit()
    out['repeat_changed']=migrate(c);c.commit()
    assert not out['repeat_changed']
    out['columns']=[dict(r) for r in c.execute('SHOW COLUMNS FROM '+TABLE).fetchall()]
    out['indexes']=[dict(r) for r in c.execute('SHOW INDEX FROM '+TABLE).fetchall()]
    out['row_count']=c.execute('SELECT COUNT(*) AS n FROM '+TABLE).fetchone()['n']
    out['after']=snapshot();c.rollback()
    assert out['before']==out['after']
    out['status']='PASS'
finally:
    c.close()
    (Path(__file__).parent/'migration.json').write_text(json.dumps(out,indent=2,default=str)+'\n')
print(json.dumps({'created':out['created'],'repeat_changed':out['repeat_changed'],'row_count':out['row_count'],'status':out['status']}))
