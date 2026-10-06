"""Fixed isolated child: technical reassessment then unchanged Stage3 inference."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))

def main(tx,source_digest,server_uuid):
    from v4_shadow import error
    try:
        if type(tx) is not int or not 0<tx<2**63:return error(tx,'INVALID_EVENT')
        manifest=json.loads((ROOT/'ml_v4/evidence/integration_stage3/decision.json').read_text(encoding='utf-8'))
        for p,h in manifest['artifact_sha256'].items():
            if p.startswith('ml_v4/frozen_inference/') and hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h:
                return error(tx,'MODEL_INTEGRITY')
        from ml_v4.frozen_inference.service import infer,runtime,Failure
        from ml_v4.frozen_inference.cli import connection
        from ml_v4.frozen_inference.history import verified_snapshot
        runtime()
        from ml_v4.frozen_inference.service import verified_bytes
        pins=json.loads((ROOT/'ml_v4/frozen_inference/history_authority.json').read_text())
        for path,h in pins.items():verified_bytes({'path':path,'sha256':h})
        c=connection();locked=False
        try:
            locked=c.execute("SELECT GET_LOCK('cmm_history_admin_v1',5) AS ok").fetchone()['ok']==1
            if not locked:return error(tx,'HISTORY_INCOMPLETE')
            c.rollback()
            # Stage3 performs exact trigger and original-boundary checks. A stale
            # attestation is expected; repeat checks independently before writes.
            from canonical_history_journal import triggers
            from canonical_history_store import current_scope,attest
            rows=c.execute('SELECT TRIGGER_NAME,EVENT_OBJECT_TABLE,EVENT_MANIPULATION,ACTION_TIMING,ACTION_STATEMENT FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE()').fetchall()
            rows=[r for r in rows if r['TRIGGER_NAME'].lower().startswith('cmm_')]
            want=triggers('mysql')
            if {r['TRIGGER_NAME'] for r in rows}!=set(want):return error(tx,'HISTORY_INCOMPLETE')
            for r in rows:
                table,op,body=want[r['TRIGGER_NAME']]
                if (r['EVENT_OBJECT_TABLE'],r['EVENT_MANIPULATION'],r['ACTION_TIMING'],r['ACTION_STATEMENT'])!=(table,op,'AFTER',body):return error(tx,'HISTORY_INCOMPLETE')
            original=json.loads((ROOT/'ml_v4/evidence/integration_stage2a2/observation_boundary.json').read_text())
            scope=current_scope(c,'controlled-prototype-v1')
            for k in ('scope_id','scope_version','start_timestamp','start_transaction_id_exclusive','source_ledger','canonical_version','preexisting_parent_ids','preexisting_change_ids'):
                if scope is None or scope[k]!=original[k]:return error(tx,'HISTORY_INCOMPLETE')
            row=c.execute('SELECT * FROM canonical_mobile_money_events WHERE transaction_id=?',(tx,)).fetchone()
            if not row:return error(tx,'EVENT_UNAVAILABLE')
            operations={r['operation'] for r in c.execute('SELECT operation FROM cmm_source_changes WHERE transaction_id=?',(tx,)).fetchall()}
            if not {'SOURCE_INSERT','CANONICAL_INSERT'}.issubset(operations):return error(tx,'HISTORY_INCOMPLETE')
            if (c.execute('SELECT @@server_uuid AS id').fetchone()['id']!=server_uuid or
                hashlib.sha256(json.dumps(dict(row),sort_keys=True,separators=(',',':')).encode()).hexdigest()!=source_digest):
                return error(tx,'HISTORY_INCOMPLETE')
            c.rollback()
            c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
            c.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT')
            a=attest(c,'controlled-prototype-v1','automatic-shadow-technical-reassessment',
                     'integration_stage4r/source-transaction/'+str(tx))
            c.commit()
            if a['status']!='COMPLETE_VERIFIED':return error(tx,'HISTORY_INCOMPLETE')
        finally:
            c.rollback()
            if locked:c.execute("SELECT RELEASE_LOCK('cmm_history_admin_v1')")
            c.close()
        # A new read-only snapshot must still match. Concurrent later commits
        # invalidate freshness; infer fails closed rather than bypassing it.
        return infer(connection,tx)
    except Exception as exc:
        code=getattr(exc,'code',None)
        return error(tx,code if code in ('MODEL_INTEGRITY','MODEL_UNAVAILABLE','HISTORY_INCOMPLETE') else 'INFERENCE_ERROR')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--transaction-id',type=int,required=True)
    parser.add_argument('--source-digest',required=True)
    parser.add_argument('--server-uuid',required=True)
    args=parser.parse_args()
    print(json.dumps(main(args.transaction_id,args.source_digest,args.server_uuid),allow_nan=False))
