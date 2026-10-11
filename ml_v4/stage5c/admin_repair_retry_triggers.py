"""Administrator-executed, disposable-only trigger completion; no global SET."""
import argparse
import json
import os
import re

from ml_v4.stage5c import repair_retry_triggers as repair
from ml_v4.stage5c.migrate_retry_schema import MigrationStepError, failure_record
from ml_v4.stage5c.verify_retry import UUID
from ml_v4.test_binding import v1

DEFINER = "'v4_stage4t_runner'@'127.0.0.1'"
LOCK = 'v4_retry_trigger_repair_v1'


def admin_grants_ok(lines):
    """Require an existing SUPER-capable administrator and disposable TRIGGER."""
    global_privs = set()
    disposable_privs = set()
    for line in lines:
        clean = line.replace('`', '').replace('"', '')
        match = re.search(r'^GRANT\s+(.*?)\s+ON\s+([^ ]+)\s+TO\s+', clean, re.I)
        if match:
            privileges = {part.strip().upper() for part in match.group(1).split(',')}
            if match.group(2) == '*.*':
                global_privs.update(privileges)
            elif match.group(2) == v1.DATABASE + '.*':
                disposable_privs.update(privileges)
    super_ok = 'SUPER' in global_privs or 'ALL PRIVILEGES' in global_privs
    trigger_ok = 'TRIGGER' in global_privs or 'ALL PRIVILEGES' in global_privs or \
        'TRIGGER' in disposable_privs or 'ALL PRIVILEGES' in disposable_privs
    return super_ok and trigger_ok


def verify_admin(conn, username):
    row = conn.execute('SELECT DATABASE() AS db, @@server_uuid AS server_uuid, '
                       'CURRENT_USER() AS principal, VERSION() AS version, '
                       '@@GLOBAL.log_bin AS log_bin, '
                       '@@GLOBAL.log_bin_trust_function_creators AS trust').fetchone()
    if (row['db'] != v1.DATABASE or row['server_uuid'] != UUID or
            not re.fullmatch(re.escape(username) + r'@[^@]+', row['principal']) or
            row['version'] != '8.0.46' or
            row['log_bin'] != 1 or row['trust'] != 0):
        raise RuntimeError('Administrator identity or binary-log policy changed')
    grants = [next(iter(item.values())) for item in conn.execute('SHOW GRANTS').fetchall()]
    if not admin_grants_ok(grants):
        raise RuntimeError('Administrator lacks existing SUPER/TRIGGER authority')
    return {'principal': row['principal'], 'server_uuid': row['server_uuid'],
            'log_bin': row['log_bin'], 'trust': row['trust']}


def admin_connection(username):
    import mysql.connector
    from database import DatabaseAdapter

    password = os.environ.pop('STAGE5C_ADMIN_PASSWORD', '')
    if not password:
        raise RuntimeError('Administrator password unavailable')
    try:
        raw = mysql.connector.connect(
            host='127.0.0.1', port=3306, user=username, password=password,
            database=v1.DATABASE, connection_timeout=5, charset='utf8mb4')
    finally:
        password = None
    conn = DatabaseAdapter(raw, 'mysql')
    try:
        verify_admin(conn, username)
        return conn
    except Exception:
        conn.close()
        raise


def run():
    username = os.environ.get('STAGE5C_ADMIN_USER', '')
    if (os.environ.get('STAGE5C_ADMIN_TRIGGER_APPLY') != 'YES' or
            not re.fullmatch(r'[A-Za-z0-9_]{1,32}', username) or
            os.environ.get('V4_STAGE4T_EXPECTED_SERVER_UUID') != UUID or
            os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL') or
            os.environ.get('V4_STAGE4SK_RECOVERY_DB_URL') or
            os.environ.get('STAGE5C_SCHEMA_APPLY') or
            os.environ.get('STAGE5C_TRIGGER_REPAIR_APPLY')):
        raise RuntimeError('Explicit administrator trigger-only authority required')
    parsed = v1.config(os.environ.get('V4_STAGE4T_TEST_DB_URL', ''))
    if parsed.hostname != '127.0.0.1' or parsed.port != 3306:
        raise RuntimeError('Only pinned local disposable MySQL allowed')
    authority = v1.load_authority()
    if authority['server_uuid'] != UUID:
        raise RuntimeError('Test authority changed')
    restricted = None
    admin = None
    locked = False
    operation = 'open_restricted_connection'
    failure = None
    try:
        restricted = v1.connection(authority)
        operation = 'acquire_repair_lock'
        if restricted.execute('SELECT GET_LOCK(?,0) AS acquired',
                              (LOCK,)).fetchone()['acquired'] != 1:
            raise RuntimeError('Another trigger repair is in progress')
        locked = True
        operation = 'read_only_disposable_preflight'
        before, digests = repair.snapshot(restricted, authority)
        repair.guard_before(before)
        operation = 'open_verified_admin_connection'
        admin = admin_connection(username)
        administrator = verify_admin(admin, username)
        operation = 'recheck_disposable_before_ddl'
        current, current_digests = repair.snapshot(restricted, authority)
        repair.guard_before(current)
        if current != before or current_digests != digests:
            raise RuntimeError('Disposable state changed before trigger DDL')
        operation = 'create_no_update_trigger'
        admin.execute(repair.TRIGGER_SQL[0].replace(
            'CREATE TRIGGER ', 'CREATE DEFINER=' + DEFINER + ' TRIGGER ', 1))
        operation = 'create_no_delete_trigger'
        admin.execute(repair.TRIGGER_SQL[1].replace(
            'CREATE TRIGGER ', 'CREATE DEFINER=' + DEFINER + ' TRIGGER ', 1))
        operation = 'post_ddl_verification'
        after, after_digests = repair.snapshot(restricted, authority)
        repair.guard_after(before, after)
        if after_digests != digests:
            raise RuntimeError('Protected rows changed during trigger repair')
        verify_admin(admin, username)
        definers = restricted.execute(
            'SELECT TRIGGER_NAME,DEFINER FROM information_schema.TRIGGERS '
            'WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE=?',
            (repair.TABLE,)).fetchall()
        if ({row['TRIGGER_NAME']: row['DEFINER'] for row in definers} !=
                {name: 'v4_stage4t_runner@127.0.0.1'
                 for name in ('v4_retry_no_update', 'v4_retry_no_delete')}):
            raise RuntimeError('Trigger definer differs from restricted test account')
        return {'status': 'PASS', 'database': v1.DATABASE, 'server_uuid': UUID,
                'administrator': administrator['principal'],
                'trigger_definer': 'v4_stage4t_runner@127.0.0.1',
                'append_only_triggers': 2, 'audit_row_count': 0,
                'history_freshness': after['history_freshness'],
                'source_revision': after['current_source_revision'],
                'protected_rows_unchanged': True,
                'global_trust_unchanged': administrator['trust'] == 0}
    except Exception as exc:
        failure = MigrationStepError(operation, exc)
        raise failure from None
    finally:
        cleanup_error = None
        if admin is not None:
            try:
                admin.rollback()
            except Exception as exc:
                cleanup_error = exc
            try:
                admin.close()
            except Exception as exc:
                cleanup_error = cleanup_error or exc
        if restricted is not None:
            try:
                restricted.rollback()
                if locked:
                    restricted.execute('SELECT RELEASE_LOCK(?)', (LOCK,))
            except Exception as exc:
                cleanup_error = cleanup_error or exc
            try:
                restricted.close()
            except Exception as exc:
                cleanup_error = cleanup_error or exc
        if cleanup_error is not None and failure is None:
            raise MigrationStepError('cleanup', cleanup_error) from None


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
