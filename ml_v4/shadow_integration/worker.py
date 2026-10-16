"""Read-only isolated child: verify committed source, then frozen Stage3 inference."""
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
        c=connection()
        try:
            # The primary coordinator has already refreshed the attestation using
            # the existing local authority. This child must never replace it.
            verified_snapshot(c,tx)
            identity=c.execute('SELECT @@server_uuid AS uuid, CURRENT_USER() AS principal').fetchone()
            if identity['uuid']!=server_uuid or identity['principal']!='aml@127.0.0.1':
                return error(tx,'HISTORY_INCOMPLETE')
            from canonical_history_store import current_scope,latest
            authority='configured-db-identity:'+identity['principal']
            scope=current_scope(c,'controlled-prototype-v1')
            previous=latest(c,'controlled-prototype-v1')
            if scope['verification_authority']!=authority or previous['verification_authority']!=authority:
                return error(tx,'HISTORY_INCOMPLETE')
            row=c.execute('SELECT * FROM canonical_mobile_money_events WHERE transaction_id=?',(tx,)).fetchone()
            operations=[r['operation'] for r in c.execute(
                'SELECT operation FROM cmm_source_changes WHERE transaction_id=? ORDER BY change_id',(tx,)).fetchall()]
            if operations!=['SOURCE_INSERT','CANONICAL_INSERT']:
                return error(tx,'HISTORY_INCOMPLETE')
            if (not row or hashlib.sha256(json.dumps(dict(row),sort_keys=True,
                    separators=(',',':')).encode()).hexdigest()!=source_digest):
                return error(tx,'HISTORY_INCOMPLETE')
        finally:
            c.rollback()
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
