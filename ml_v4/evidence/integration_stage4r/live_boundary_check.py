"""No financial fixture: verify real lock contention and missing-event child."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from ml_v4.frozen_inference.cli import connection
from v4_shadow import invoke
a=connection();b=connection();name='v4_shadow_stage4r_lock_test'
try:
    assert a.execute('SELECT GET_LOCK(?,0) AS ok',(name,)).fetchone()['ok']==1
    assert b.execute('SELECT GET_LOCK(?,0) AS ok',(name,)).fetchone()['ok']==0
    a.execute('SELECT RELEASE_LOCK(?)',(name,))
    assert b.execute('SELECT GET_LOCK(?,0) AS ok',(name,)).fetchone()['ok']==1
    b.execute('SELECT RELEASE_LOCK(?)',(name,))
    # Capture full history/result recordset digests to prove the nonexistent-event
    # check did not automatically attest or write a result.
    def state(c):
        return {t:hashlib.sha256(json.dumps([dict(r) for r in c.execute('SELECT * FROM '+t+' ORDER BY '+key).fetchall()],sort_keys=True,default=str).encode()).hexdigest()
                for t,key in [('cmm_history_attestations','attestation_id'),('cmm_observation_scopes','scope_id,revision'),('cmm_source_changes','change_id'),('canonical_mobile_money_events','transaction_id'),('v4_shadow_results','transaction_id')]}
    before=state(a);a.rollback()
    result=invoke(2**63-1,'0'*64,'nonexistent-event-check')
    assert result['status']=='inference_error' and result['error_code']=='EVENT_UNAVAILABLE'
    after=state(a);a.rollback();assert before==after
    out={'mysql_lock_contention':'PASS','fixed_child_invocation':'PASS','missing_event_error':result,
         'before':before,'after':after,'source_transactions_submitted':0,'new_attestations':0,'predictions':0}
finally:
    a.close();b.close()
(Path(__file__).parent/'live_boundary_check.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'mysql_lock_contention':'PASS','child_error':result['error_code'],'database_records_unchanged':True}))
