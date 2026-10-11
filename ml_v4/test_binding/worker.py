"""Test-only child matching Stage4R argument shape; never selected by Flask."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def run(tx, source_digest, server_uuid):
    from ml_v4.test_binding import v1
    from v4_shadow import error
    if type(tx) is not int or not 0 < tx < 2**63:
        return error(tx, 'INVALID_EVENT')
    try:
        authority = v1.load_authority()
        if (server_uuid != authority['server_uuid'] or
            not isinstance(source_digest, str) or
            len(source_digest) != 64 or
            any(ch not in '0123456789abcdef' for ch in source_digest)):
            raise v1.BindingError('Source/server identity mismatch')
        c = v1.connection(authority)
        locked = False
        try:
            locked = c.execute("SELECT GET_LOCK('cmm_history_admin_v1',5) AS ok").fetchone()['ok'] == 1
            if not locked:
                raise v1.BindingError('History lock unavailable')
            c.rollback()
            v1.identity(c, authority['server_uuid'])
            v1._triggers(c)
            v1._boundary(c, authority)
            row = c.execute('SELECT * FROM canonical_mobile_money_events WHERE transaction_id=?',
                            (tx,)).fetchone()
            if row is None:
                return error(tx, 'EVENT_UNAVAILABLE')
            digest = hashlib.sha256(json.dumps(dict(row), sort_keys=True,
                                               separators=(',', ':')).encode()).hexdigest()
            if digest != source_digest:
                raise v1.BindingError('Canonical row changed')
            operations = {r['operation'] for r in c.execute(
                'SELECT operation FROM cmm_source_changes WHERE transaction_id=?',
                (tx,)).fetchall()}
            if not {'SOURCE_INSERT', 'CANONICAL_INSERT'}.issubset(operations):
                raise v1.BindingError('Capture journal incomplete')
            c.rollback()
            c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
            c.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT')
            from canonical_history_store import attest
            result = attest(c, v1.SCOPE, v1.VERSION,
                            'stage4t/test-source-transaction/' + str(tx))
            c.commit()
            if result['status'] != 'COMPLETE_VERIFIED':
                raise v1.BindingError('Technical reassessment incomplete')
        finally:
            c.rollback()
            if locked:
                c.execute("SELECT RELEASE_LOCK('cmm_history_admin_v1')")
            c.close()
        # Stage5C-only failure injection occurs after the verified attestation.
        # Returning before this point would leave committed history stale.
        if (os.environ.get('STAGE5C_INJECT_POST_ATTEST_ERROR') == 'YES' and
                os.environ.get('STAGE5C_EXECUTE') == 'YES' and
                os.environ.get('AML_PRIMARY_MODEL') == 'V4'):
            return error(tx, 'INFERENCE_ERROR')
        return v1.infer(tx)
    except v1.BindingError:
        return error(tx, 'HISTORY_INCOMPLETE')
    except Exception:
        return error(tx, 'INFERENCE_ERROR')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--transaction-id', type=int, required=True)
    parser.add_argument('--source-digest', required=True)
    parser.add_argument('--server-uuid', required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.transaction_id, args.source_digest,
                         args.server_uuid), allow_nan=False))
