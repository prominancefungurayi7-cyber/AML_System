"""One-time, disposable-only Stage4T history attestation refresh.

No financial DML, migration, model call or automatic retry. The only write is
canonical_history_store.attest() inside a guarded transaction.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

from canonical_history import freshness
from canonical_history_store import assess, attest
from ml_v4.stage4sa.coordinator import validate_test
from ml_v4.stage5c.live_primary import inspect_prior, REVIEW
from ml_v4.test_binding import v1

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'ml_v4/evidence/stage5c/history_attestation_refresh.json'
MODEL = ROOT / 'ml_v4/development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib'
MODEL_SHA = '555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18'
SERVER_UUID = 'd441b7bb-43f6-11f1-a2d8-0a0027000005'
REVIEW_FINGERPRINT = '4bc544449d82091144f43bc3abd0ee5533652614c9c9c86c45050daa62fb60f1'
CURRENT_REVISION = '003c0400c9bfe5c22ff3de2406c30d8bfc166d8236a8648daa20d0c838901be4'
ATTESTED_REVISION = '7a85163c5703ddb4dd8f95b500c22d6ca6382df05a2121a6a0bb5b3cf616b6e5'
LOCK = 'cmm_history_admin_v1'
ROWS = {
    'transactions': 'id', 'users': 'id',
    'canonical_mobile_money_events': 'transaction_id',
    'cmm_source_changes': 'change_id',
    'v4_shadow_results': 'transaction_id,model_version,feature_version',
    'alerts': 'id', 'sar_reports': 'id', 'ctr_reports': 'id',
    'cmm_observation_scopes': 'scope_id,revision',
}


def _count(conn, table):
    return conn.execute('SELECT COUNT(*) AS n FROM ' + table).fetchone()['n']


def _row_digests(conn):
    """Pin all financial/source/result rows before and after authority DML."""
    return {table: hashlib.sha256(json.dumps(
        [dict(row) for row in conn.execute('SELECT * FROM ' + table + ' ORDER BY ' + order).fetchall()],
        sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()
        for table, order in ROWS.items()}


def guard_review(review):
    if (review.get('status') != 'UNRESOLVED' or
            review.get('fingerprint') != REVIEW_FINGERPRINT):
        raise RuntimeError('Pinned read-only review changed')
    baseline = review['baseline']
    history = baseline['history_assessment']
    if (baseline['identity']['database'] != v1.DATABASE or
            baseline['identity']['server_uuid'] != SERVER_UUID or
            baseline['identity']['principal'] != 'v4_stage4t_runner@127.0.0.1' or
            baseline['counts'] != {'transactions': 8, 'canonical_mobile_money_events': 8,
                                   'cmm_source_changes': 16, 'v4_shadow_results': 8,
                                   'alerts': 1, 'sar_reports': 0, 'ctr_reports': 0} or
            history['freshness'] != 'UNKNOWN' or history['current_status'] != 'COMPLETE_VERIFIED' or
            history['current_issues'] or history['current_canonical_event_ids'] != list(range(1, 9)) or
            history['current_source_revision'] != CURRENT_REVISION or
            history['attested_source_revision'] != ATTESTED_REVISION or
            history['attestation_sequence'] != 8 or history['scope_revision'] != 1):
        raise RuntimeError('Read-only history review does not match approved repair state')
    tx8 = [item for run in review['prior_runs'] for item in run['transactions']
           if item['transaction_id'] == 8]
    if (len(tx8) != 1 or tx8[0]['ai_risk_level'] != 'inference_error' or
            tx8[0]['shadow_status'] != 'inference_error' or tx8[0]['prediction'] is not None or
            tx8[0]['canonical_rows'] != 1 or
            tx8[0]['capture_operations'] != ['SOURCE_INSERT', 'CANONICAL_INSERT']):
        raise RuntimeError('Transaction 8 is not the reviewed terminal inference error')


def guard_current(conn, authority):
    identity = v1.identity(conn, SERVER_UUID)
    if identity['principal'] != authority['principal']:
        raise RuntimeError('Test principal changed')
    v1._triggers(conn)
    v1._boundary(conn, authority)
    scope, current, previous = assess(conn, v1.SCOPE)
    if (scope['revision'] != 1 or current['status'] != 'COMPLETE_VERIFIED' or
            current['issues'] or current['canonical_event_ids'] != list(range(1, 9)) or
            current['source_revision'] != CURRENT_REVISION or
            previous is None or previous['source_revision'] != ATTESTED_REVISION or
            previous['sequence'] != 8 or previous['status'] != 'COMPLETE_VERIFIED' or
            freshness(scope, current, previous) != 'UNKNOWN'):
        raise RuntimeError('Current graph or attestation differs from pinned review')
    counts = {table: _count(conn, table) for table in
              ('transactions', 'canonical_mobile_money_events', 'cmm_source_changes',
               'v4_shadow_results', 'alerts', 'sar_reports', 'ctr_reports')}
    if counts != {'transactions': 8, 'canonical_mobile_money_events': 8,
                  'cmm_source_changes': 16, 'v4_shadow_results': 8,
                  'alerts': 1, 'sar_reports': 0, 'ctr_reports': 0}:
        raise RuntimeError('Disposable financial/result counts changed')
    if _count(conn, 'cmm_history_attestations') != 8:
        raise RuntimeError('Unexpected attestation rows')
    tx8 = conn.execute('SELECT ai_risk_level,risk_level FROM transactions WHERE id=8').fetchone()
    body = conn.execute('SELECT body FROM v4_shadow_results WHERE transaction_id=8').fetchone()
    operations = [r['operation'] for r in conn.execute(
        'SELECT operation FROM cmm_source_changes WHERE transaction_id=8 '
        'ORDER BY change_id').fetchall()]
    if (tx8 is None or tx8['ai_risk_level'] != 'inference_error' or
            tx8['risk_level'] != 'pending_review' or body is None or
            validate_test(json.loads(body['body']), 8)['status'] != 'inference_error' or
            operations != ['SOURCE_INSERT', 'CANONICAL_INSERT']):
        raise RuntimeError('Transaction 8 source/result state changed')
    return {'identity': identity, 'current': current, 'previous': previous,
            'counts': counts}


def run():
    if (os.environ.get('STAGE5C_ATTEST_EXECUTE') != 'YES' or
            os.environ.get('V4_STAGE4T_EXPECTED_SERVER_UUID') != SERVER_UUID or
            os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL') or
            os.environ.get('AML_PRIMARY_MODEL') or os.environ.get('V4_SHADOW_ENABLED') == 'ON'):
        raise RuntimeError('Isolated attestation environment not pinned')
    parsed = v1.config(os.environ.get('V4_STAGE4T_TEST_DB_URL', ''))
    if parsed.hostname != '127.0.0.1' or parsed.port != 3306:
        raise RuntimeError('Only local disposable MySQL is allowed')
    if OUT.exists() or OUT.is_symlink() or not REVIEW.is_file() or REVIEW.is_symlink():
        raise RuntimeError('One-time output exists or read-only review unavailable')
    if hashlib.sha256(MODEL.read_bytes()).hexdigest() != MODEL_SHA:
        raise RuntimeError('Frozen model integrity mismatch')
    saved_review = json.loads(REVIEW.read_text(encoding='utf-8'))
    guard_review(saved_review)
    guard_review(inspect_prior(attestation_review=True))
    authority = v1.load_authority()
    if authority['server_uuid'] != SERVER_UUID:
        raise RuntimeError('Test authority server UUID mismatch')
    conn = v1.connection(authority)
    locked = False
    committed = False
    try:
        locked = conn.execute('SELECT GET_LOCK(?,5) AS ok', (LOCK,)).fetchone()['ok'] == 1
        if not locked:
            raise RuntimeError('History lock unavailable')
        conn.rollback()
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
        conn.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT')
        before = guard_current(conn, authority)
        protected = _row_digests(conn)
        entity_before = _count(conn, 'cmm_entity_history')
        result = attest(conn, v1.SCOPE, v1.VERSION,
                        'stage5c/approved-transaction-8-history-refresh')
        if (result['status'] != 'COMPLETE_VERIFIED' or result['issues'] or
                result['source_revision'] != CURRENT_REVISION or
                result['sequence'] != 9 or
                _row_digests(conn) != protected or
                _count(conn, 'cmm_history_attestations') != 9 or
                _count(conn, 'cmm_entity_history') - entity_before != len(result['entities'])):
            raise RuntimeError('Attestation changed unexpected rows; rolling back')
        conn.commit()
        committed = True
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            if locked:
                conn.execute('SELECT RELEASE_LOCK(?)', (LOCK,))
        finally:
            conn.close()
    check = v1.connection(authority)
    try:
        check.rollback()
        check.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
        check.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY')
        v1.identity(check, SERVER_UUID)
        v1._triggers(check)
        v1._boundary(check, authority)
        scope, current, previous = assess(check, v1.SCOPE)
        if (not committed or freshness(scope, current, previous) != 'COMPLETE_VERIFIED' or
                current['issues'] or current['source_revision'] != CURRENT_REVISION or
                previous['attestation_id'] != result['attestation_id'] or
                previous['sequence'] != 9 or _row_digests(check) != protected or
                _count(check, 'cmm_history_attestations') != 9):
            raise RuntimeError('Post-commit verification failed; do not retry automatically')
        evidence = {'status': 'PASS', 'database': v1.DATABASE,
                    'server_uuid': SERVER_UUID, 'principal': authority['principal'],
                    'scope_id': v1.SCOPE, 'source_revision': CURRENT_REVISION,
                    'attestation_id': result['attestation_id'], 'sequence': 9,
                    'freshness': 'COMPLETE_VERIFIED', 'source_row_sha256': protected,
                    'source_counts': before['counts'], 'transaction_8_ai_state': 'inference_error'}
        OUT.parent.mkdir(parents=True, exist_ok=True)
        with OUT.open('x', encoding='utf-8') as stream:
            json.dump(evidence, stream, indent=2, sort_keys=True)
            stream.write('\n')
        print(json.dumps(evidence, indent=2, sort_keys=True))
    finally:
        try:
            check.rollback()
        finally:
            check.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not args.apply:
        raise SystemExit('Explicit --apply required')
    try:
        run()
    except Exception as exc:
        reason = ': ' + str(exc) if type(exc) is RuntimeError else ''
        print('Stage5C history refresh stopped: ' + type(exc).__name__ + reason)
        raise SystemExit(1)
