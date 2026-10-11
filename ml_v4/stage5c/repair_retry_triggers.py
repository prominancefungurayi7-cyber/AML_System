"""One-time, disposable-only completion of two absent append-only audit triggers."""
import argparse
import hashlib
import json
import os

from ml_v4.stage5c import inspect_retry_schema as schema
from ml_v4.stage5c.migrate_retry_schema import MigrationStepError, failure_record
from ml_v4.stage5c.verify_retry import UUID
from ml_v4.test_binding import v1

TABLE = 'v4_primary_attempt_events'
TRIGGER_SQL = (
    "CREATE TRIGGER v4_stage4s_disposable.v4_retry_no_update "
    "BEFORE UPDATE ON v4_stage4s_disposable.v4_primary_attempt_events "
    "FOR EACH ROW SIGNAL SQLSTATE '45000' "
    "SET MESSAGE_TEXT='V4 attempt audit is append-only'",
    "CREATE TRIGGER v4_stage4s_disposable.v4_retry_no_delete "
    "BEFORE DELETE ON v4_stage4s_disposable.v4_primary_attempt_events "
    "FOR EACH ROW SIGNAL SQLSTATE '45000' "
    "SET MESSAGE_TEXT='V4 attempt audit is append-only'",
)
PROTECTED = {
    'transactions': 'id', 'users': 'id',
    'canonical_mobile_money_events': 'transaction_id',
    'cmm_source_changes': 'change_id',
    'v4_shadow_results': 'transaction_id,model_version,feature_version',
    'alerts': 'id', 'sar_reports': 'id', 'ctr_reports': 'id',
    'cmm_observation_scopes': 'scope_id,revision',
    'cmm_history_attestations': 'attestation_id',
    'cmm_entity_history': 'attestation_id,entity_key',
}


def row_digests(conn):
    return {name: hashlib.sha256(json.dumps(
        [dict(row) for row in conn.execute('SELECT * FROM ' + name + ' ORDER BY ' + order).fetchall()],
        sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()
        for name, order in PROTECTED.items()}


def guard_before(result):
    checks = result['checks']
    if (result['status'] != 'READ_ONLY_INSPECTION' or
            result['identity']['database'] != v1.DATABASE or
            result['identity']['server_uuid'] != UUID or
            result['identity']['principal'] != 'v4_stage4t_runner@127.0.0.1' or
            result['server_version'] != '8.0.46' or
            result['state'] != 'PARTIAL_DDL_OR_SCHEMA_MISMATCH' or
            any(result['actual_triggers']) or
            result['audit_row_count'] != 0 or
            result['parent_id_types'] != {'transactions': 'bigint', 'users': 'bigint'} or
            result['financial_history_counts'] != {
                'transactions': 8, 'canonical_mobile_money_events': 8,
                'cmm_source_changes': 16, 'v4_shadow_results': 8} or
            result['current_history_status'] != 'COMPLETE_VERIFIED' or
            result['history_issues'] or
            result['history_freshness'] != 'COMPLETE_VERIFIED' or
            not all(result['required_ddl_grants'].values()) or
            checks.get('append_only_triggers') is not False or
            not all(value for name, value in checks.items()
                    if name != 'append_only_triggers')):
        raise RuntimeError('Reviewed trigger-only repair preconditions changed')


def guard_after(before, after):
    if (after['state'] != 'COMPLETE' or after['audit_row_count'] != 0 or
            after['financial_history_counts'] != before['financial_history_counts'] or
            after['current_source_revision'] != before['current_source_revision'] or
            after['history_freshness'] != 'COMPLETE_VERIFIED' or
            after['history_issues'] or
            {row['TRIGGER_NAME'] for row in after['actual_triggers']} !=
            {'v4_retry_no_update', 'v4_retry_no_delete'} or
            not all(after['checks'].values())):
        raise RuntimeError('Post-repair schema or history verification failed')


def snapshot(conn, authority):
    conn.rollback()
    conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
    conn.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY')
    result = schema.inspect(conn, authority)
    digests = row_digests(conn)
    conn.rollback()
    return result, digests


def run():
    if (os.environ.get('STAGE5C_TRIGGER_REPAIR_APPLY') != 'YES' or
            os.environ.get('V4_STAGE4T_EXPECTED_SERVER_UUID') != UUID or
            os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL') or
            os.environ.get('V4_STAGE4SK_RECOVERY_DB_URL') or
            os.environ.get('STAGE5C_SCHEMA_APPLY')):
        raise RuntimeError('Explicit disposable trigger-only authority required')
    parsed = v1.config(os.environ.get('V4_STAGE4T_TEST_DB_URL', ''))
    if parsed.hostname != '127.0.0.1' or parsed.port != 3306:
        raise RuntimeError('Only pinned local disposable MySQL allowed')
    authority = v1.load_authority()
    if authority['server_uuid'] != UUID:
        raise RuntimeError('Test authority changed')
    operation = 'open_verified_connection'
    conn = None
    locked = False
    try:
        conn = v1.connection(authority)
        operation = 'acquire_trigger_repair_lock'
        if conn.execute('SELECT GET_LOCK(?,0) AS acquired',
                        ('v4_retry_trigger_repair_v1',)).fetchone()['acquired'] != 1:
            raise RuntimeError('Another trigger repair is in progress')
        locked = True
        operation = 'read_only_preflight'
        before, digests = snapshot(conn, authority)
        guard_before(before)
        # A second connection cannot hide a concurrent schema change behind the
        # first snapshot. DDL itself will commit, so no automatic retry exists.
        operation = 'recheck_schema_before_ddl'
        current, current_digests = snapshot(conn, authority)
        guard_before(current)
        if current != before or current_digests != digests:
            raise RuntimeError('Disposable state changed before trigger DDL')
        operation = 'create_no_update_trigger'
        conn.execute(TRIGGER_SQL[0])
        operation = 'create_no_delete_trigger'
        conn.execute(TRIGGER_SQL[1])
        operation = 'post_ddl_verification'
        after, after_digests = snapshot(conn, authority)
        guard_after(before, after)
        if after_digests != digests:
            raise RuntimeError('Protected rows changed during trigger repair')
        return {'status': 'PASS', 'database': v1.DATABASE, 'server_uuid': UUID,
                'audit_row_count': 0, 'append_only_triggers': 2,
                'history_freshness': after['history_freshness'],
                'source_revision': after['current_source_revision'],
                'protected_rows_unchanged': True,
                'enforcement': 'verified trigger definitions; no DML probe'}
    except Exception as exc:
        raise MigrationStepError(operation, exc) from None
    finally:
        if conn is not None:
            try:
                conn.rollback()
                if locked:
                    conn.execute('SELECT RELEASE_LOCK(?)', ('v4_retry_trigger_repair_v1',))
            finally:
                conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not args.apply:
        raise SystemExit('Explicit --apply required')
    try:
        print(json.dumps(run(), sort_keys=True))
    except Exception as exc:
        print(json.dumps(failure_record(exc), sort_keys=True))
        raise SystemExit(1)
