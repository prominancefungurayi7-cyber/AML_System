"""Prepared disposable-only additive audit schema migration; never automatic."""
import argparse
import json
import os
from pathlib import Path
import re

from canonical_history import freshness
from canonical_history_store import assess
from ml_v4.stage5c.verify_retry import _protected, UUID
from ml_v4.test_binding import v1
import v4_retry
import v4_shadow

SQL = Path(__file__).with_name('retry_audit_schema_disposable.sql')
TABLE = 'v4_primary_attempt_events'


class MigrationStepError(RuntimeError):
    def __init__(self, operation, cause):
        self.operation = operation
        self.cause = cause
        super().__init__(operation)


def failure_record(exc):
    """Report the failed step and MySQL diagnostics without connection secrets."""
    cause = exc.cause if isinstance(exc, MigrationStepError) else exc
    message = getattr(cause, 'msg', None)
    if isinstance(message, str):
        message = re.sub(r'(?i)(?:mysql(?:\+mysqlconnector)?://)[^\s]+',
                         '[redacted database URL]', message)
        message = re.sub(r'(?i)(password\s*[=:]\s*)[^\s,;]+',
                         r'\1[redacted]', message)
        message = message[:500]
    else:
        message = None
    return {'status': 'STOPPED',
            'operation': exc.operation if isinstance(exc, MigrationStepError) else 'binding',
            'error_type': type(cause).__name__,
            'mysql_errno': getattr(cause, 'errno', None),
            'mysql_sqlstate': getattr(cause, 'sqlstate', None),
            'mysql_message': message,
            'action': 'Inspect read-only; never rerun automatically'}


def preflight(conn, authority):
    v1.identity(conn, UUID)
    v1._triggers(conn)
    v1._boundary(conn, authority)
    scope, current, previous = assess(conn, v1.SCOPE)
    if freshness(scope, current, previous) != 'COMPLETE_VERIFIED' or current['issues']:
        raise RuntimeError('Existing disposable history not fresh')
    counts = tuple(conn.execute('SELECT COUNT(*) AS n FROM ' + table).fetchone()['n']
                   for table in ('transactions', 'canonical_mobile_money_events',
                                 'cmm_source_changes', 'v4_shadow_results'))
    if counts != (8, 8, 16, 8):
        raise RuntimeError('Reviewed disposable rows changed')
    if conn.execute('SHOW TABLES LIKE ?', (TABLE,)).fetchone() is not None:
        raise RuntimeError('Retry audit table already exists; do not retry DDL')
    row = conn.execute('SELECT ai_risk_level FROM transactions WHERE id=8').fetchone()
    original = v4_shadow.get(conn, 8)
    if row is None or row['ai_risk_level'] != 'inference_error' or \
            original is None or v4_shadow.validate(original, 8)['status'] != 'inference_error':
        raise RuntimeError('Original transaction-8 error changed')
    return _protected(conn)


def run():
    if (os.environ.get('STAGE5C_SCHEMA_APPLY') != 'YES' or
            os.environ.get('V4_STAGE4T_EXPECTED_SERVER_UUID') != UUID or
            os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL')):
        raise RuntimeError('Explicit disposable schema authority required')
    parsed = v1.config(os.environ.get('V4_STAGE4T_TEST_DB_URL', ''))
    if parsed.hostname != '127.0.0.1' or parsed.port != 3306:
        raise RuntimeError('Only pinned local disposable MySQL allowed')
    authority = v1.load_authority()
    if authority['server_uuid'] != UUID:
        raise RuntimeError('Test authority changed')
    operation = 'open_verified_connection'
    conn = None
    failure = None
    try:
        conn = v1.connection(authority)
        operation = 'read_only_preflight'
        before = preflight(conn, authority)
        operation = 'load_reviewed_sql'
        source = SQL.read_text(encoding='utf-8')
        start = source.index('CREATE TABLE v4_stage4s_disposable.v4_primary_attempt_events')
        table_sql = source[start:source.index('CREATE TRIGGER', start)].strip().rstrip(';')
        conn.rollback()
        operation = 'create_audit_table'
        conn.execute(table_sql)
        operation = 'create_no_update_trigger'
        conn.execute("CREATE TRIGGER v4_stage4s_disposable.v4_retry_no_update "
                     "BEFORE UPDATE ON v4_stage4s_disposable.v4_primary_attempt_events "
                     "FOR EACH ROW SIGNAL SQLSTATE '45000' "
                     "SET MESSAGE_TEXT='V4 attempt audit is append-only'")
        operation = 'create_no_delete_trigger'
        conn.execute("CREATE TRIGGER v4_stage4s_disposable.v4_retry_no_delete "
                     "BEFORE DELETE ON v4_stage4s_disposable.v4_primary_attempt_events "
                     "FOR EACH ROW SIGNAL SQLSTATE '45000' "
                     "SET MESSAGE_TEXT='V4 attempt audit is append-only'")
        operation = 'post_ddl_verification'
        v4_retry.require_schema(conn)
        if conn.execute('SELECT COUNT(*) AS n FROM ' + TABLE).fetchone()['n'] != 0:
            raise RuntimeError('New audit table not empty')
        if _protected(conn) != before:
            raise RuntimeError('Existing financial/source/result rows changed after DDL')
        v1._triggers(conn)
        scope, current, previous = assess(conn, v1.SCOPE)
        if freshness(scope, current, previous) != 'COMPLETE_VERIFIED' or current['issues']:
            raise RuntimeError('History authority changed after DDL')
        return {'status': 'PASS', 'database': v1.DATABASE,
                'server_uuid': UUID, 'audit_table': TABLE, 'existing_rows_preserved': True}
    except Exception as exc:
        failure = MigrationStepError(operation, exc)
        raise failure from None
    finally:
        if conn is not None:
            try:
                conn.rollback()
            except Exception as exc:
                if failure is None:
                    failure = MigrationStepError('cleanup_rollback', exc)
            try:
                conn.close()
            except Exception as exc:
                if failure is None:
                    failure = MigrationStepError('cleanup_close', exc)
            if failure is not None and failure.operation.startswith('cleanup_'):
                raise failure from None


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not args.apply:
        raise SystemExit('Explicit --apply required')
    try:
        print(run())
    except Exception as exc:
        print(json.dumps(failure_record(exc), sort_keys=True))
        raise SystemExit(1)
