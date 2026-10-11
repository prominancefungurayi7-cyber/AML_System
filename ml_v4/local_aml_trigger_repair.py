"""Administrator-assisted completion of two LOCAL aml retry triggers only."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path

from dotenv import dotenv_values

from database import DatabaseAdapter, connect_db
from ml_v4.local_aml_migration import ROOT, UUID, PRINCIPAL, MODEL_SHA, inspect
from transaction_idempotency import require_schema
import v4_retry

TABLE = 'v4_primary_attempt_events'
LOCK = 'local_aml_v4_retry_trigger_repair'
PROTECTED = {
    'transactions': 'id', 'users': 'id', 'alerts': 'id',
    'canonical_mobile_money_events': 'transaction_id',
    'cmm_source_changes': 'change_id',
    'v4_shadow_results': 'transaction_id,model_version,feature_version',
    'sar_reports': 'id', 'ctr_reports': 'id',
    'cmm_observation_scopes': 'scope_id,revision',
    'cmm_history_attestations': 'attestation_id',
    'cmm_entity_history': 'attestation_id,entity_key',
}
NAMES = ('v4_retry_no_update', 'v4_retry_no_delete')


def digest_rows(conn):
    return {table: hashlib.sha256(json.dumps(
        [dict(row) for row in conn.execute('SELECT * FROM ' + table + ' ORDER BY ' + order).fetchall()],
        sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()
        for table, order in PROTECTED.items()}


def snapshot(conn):
    model = ROOT / 'ml_v4/development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib'
    if hashlib.sha256(model.read_bytes()).hexdigest() != MODEL_SHA:
        raise RuntimeError('Frozen V4 model changed')
    conn.rollback()
    conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
    conn.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY')
    base = inspect(conn)
    if base['counts'] != {'transactions': 7800, 'users': 18, 'alerts': 415,
                           'canonical_mobile_money_events': 0,
                           'cmm_source_changes': 0, 'cmm_history_attestations': 1,
                           'v4_shadow_results': 0}:
        raise RuntimeError('Protected local aml counts changed')
    require_schema(conn)
    column_rows = conn.execute('SHOW COLUMNS FROM ' + TABLE).fetchall()
    columns = [r['Field'] for r in column_rows]
    if columns != ['event_id', 'transaction_id', 'staff_user_id', 'request_key',
                   'event_kind', 'recorded_at', 'outcome', 'error_code',
                   'result_body', 'reason']:
        raise RuntimeError('Retry audit columns changed')
    types = {r['Field']: r['Type'].lower() for r in column_rows}
    if types != {'event_id': 'bigint', 'transaction_id': 'bigint',
                 'staff_user_id': 'bigint', 'request_key': 'char(36)',
                 'event_kind': 'varchar(16)', 'recorded_at': 'varchar(40)',
                 'outcome': 'varchar(32)', 'error_code': 'varchar(64)',
                 'result_body': 'longtext', 'reason': 'varchar(500)'}:
        raise RuntimeError('Retry audit types changed')
    indexes = conn.execute('SHOW INDEX FROM ' + TABLE).fetchall()
    unique = [r['Column_name'] for r in sorted(indexes, key=lambda r:r['Seq_in_index'])
              if r['Key_name'] == 'uq_v4_attempt_event' and r['Non_unique'] == 0]
    if unique != ['transaction_id', 'request_key', 'event_kind']:
        raise RuntimeError('Retry audit unique index changed')
    fks = {r['CONSTRAINT_NAME']: r['REFERENCED_TABLE_NAME'] for r in conn.execute(
        'SELECT CONSTRAINT_NAME,REFERENCED_TABLE_NAME FROM information_schema.KEY_COLUMN_USAGE '
        'WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=? AND REFERENCED_TABLE_NAME IS NOT NULL',
        (TABLE,)).fetchall()}
    if fks != {'fk_v4_attempt_staff': 'users',
               'fk_v4_attempt_transaction': 'transactions'}:
        raise RuntimeError('Retry audit foreign keys changed')
    checks = {r['CONSTRAINT_NAME']: r['CHECK_CLAUSE'] for r in conn.execute(
        'SELECT CONSTRAINT_NAME,CHECK_CLAUSE FROM information_schema.CHECK_CONSTRAINTS '
        "WHERE CONSTRAINT_SCHEMA=DATABASE() AND CONSTRAINT_NAME LIKE 'ck_v4_attempt_%'").fetchall()}
    if set(checks) != {'ck_v4_attempt_kind', 'ck_v4_attempt_outcome'} or not all(checks.values()):
        raise RuntimeError('Retry audit check constraints changed')
    if conn.execute('SELECT COUNT(*) AS n FROM ' + TABLE).fetchone()['n'] != 0:
        raise RuntimeError('Retry audit table is not empty')
    triggers = {r['TRIGGER_NAME']: r for r in conn.execute(
        'SELECT TRIGGER_NAME,DEFINER,ACTION_TIMING,EVENT_MANIPULATION,ACTION_STATEMENT '
        'FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() '
        'AND EVENT_OBJECT_TABLE=?', (TABLE,)).fetchall()}
    digests = digest_rows(conn)
    conn.rollback()
    return base, triggers, digests


def verify_admin(conn, username):
    row = conn.execute('SELECT DATABASE() AS db,@@server_uuid AS uuid,'
                       'CURRENT_USER() AS principal,VERSION() AS version,'
                       '@@GLOBAL.log_bin AS log_bin,'
                       '@@GLOBAL.log_bin_trust_function_creators AS trust').fetchone()
    if (row['db'] != 'aml' or row['uuid'] != UUID or row['version'] != '8.0.46' or
            row['log_bin'] != 1 or row['trust'] != 0 or
            not re.fullmatch(re.escape(username) + r'@[^@]+', row['principal'])):
        raise RuntimeError('Existing administrator identity or server policy changed')
    grants = [next(iter(r.values())) for r in conn.execute('SHOW GRANTS').fetchall()]
    global_privs, aml_privs = set(), set()
    for grant in grants:
        match = re.search(r'^GRANT\s+(.*?)\s+ON\s+([^ ]+)\s+TO\s+',
                          grant.replace('`', '').replace('"', ''), re.I)
        if match:
            target = global_privs if match.group(2) == '*.*' else aml_privs if match.group(2) == 'aml.*' else None
            if target is not None:
                target.update(x.strip().upper() for x in match.group(1).split(','))
    if not ({'SUPER', 'ALL PRIVILEGES'} & global_privs and
            ({'TRIGGER', 'ALL PRIVILEGES'} & (global_privs | aml_privs))):
        raise RuntimeError('Existing administrator lacks SUPER and aml TRIGGER grants')
    return row


def run(username):
    if not re.fullmatch(r'[A-Za-z0-9_]{1,32}', username):
        raise RuntimeError('Invalid existing administrator name')
    if any(os.environ.get(key) for key in ('DATABASE_URL', 'MYSQL_URL',
            'V4_STAGE4T_TEST_DB_URL', 'V4_STAGE4SK_RECOVERY_DB_URL')):
        raise RuntimeError('Conflicting database binding')
    url = dotenv_values(ROOT / '.env').get('DATABASE_URL')
    from urllib.parse import urlparse
    parsed = urlparse(url or '')
    if (parsed.scheme, parsed.hostname, parsed.port, parsed.path) != (
            'mysql', '127.0.0.1', 3306, '/aml'):
        raise RuntimeError('Unexpected local aml binding')
    restricted = connect_db(url)
    admin = None
    locked = False
    try:
        if restricted.execute('SELECT GET_LOCK(?,0) AS acquired', (LOCK,)).fetchone()['acquired'] != 1:
            raise RuntimeError('Another local trigger repair is in progress')
        locked = True
        before, existing, digests = snapshot(restricted)
        if existing:
            # Complete schema is idempotent; partial DDL requires inspection.
            if set(existing) == set(NAMES):
                v4_retry.require_schema(restricted)
                if all(r['DEFINER'] == PRINCIPAL for r in existing.values()):
                    return {'status': 'ALREADY_COMPLETE', 'identity': before['identity']}
            raise RuntimeError('Partial or changed retry triggers; inspect read-only')
        password = os.environ.pop('LOCAL_AML_ADMIN_PASSWORD', '')
        if not password:
            raise RuntimeError('Existing administrator credential required')
        try:
            import mysql.connector
            raw = mysql.connector.connect(host='127.0.0.1', port=3306,
                                          user=username, password=password,
                                          database='aml', connection_timeout=5,
                                          charset='utf8mb4')
        finally:
            password = None
        admin = DatabaseAdapter(raw, 'mysql')
        authority = verify_admin(admin, username)
        current, current_triggers, current_digests = snapshot(restricted)
        if current != before or current_triggers or current_digests != digests:
            raise RuntimeError('Local aml changed before trigger DDL')
        for name, operation in zip(NAMES, ('UPDATE', 'DELETE')):
            admin.execute("CREATE DEFINER='aml'@'127.0.0.1' TRIGGER aml." + name +
                          ' BEFORE ' + operation + ' ON aml.' + TABLE +
                          " FOR EACH ROW SIGNAL SQLSTATE '45000' "
                          "SET MESSAGE_TEXT='V4 attempt audit is append-only'")
        after, actual, after_digests = snapshot(restricted)
        v4_retry.require_schema(restricted)
        if (after != before or after_digests != digests or set(actual) != set(NAMES) or
                any(r['DEFINER'] != PRINCIPAL for r in actual.values())):
            raise RuntimeError('Post-DDL schema or protected data mismatch')
        verify_admin(admin, username)
        return {'status': 'PASS', 'identity': after['identity'],
                'administrator': authority['principal'], 'definer': PRINCIPAL,
                'append_only_triggers': 2, 'protected_rows_unchanged': True,
                'history': after['history']}
    finally:
        if admin is not None:
            admin.rollback(); admin.close()
        restricted.rollback()
        if locked:
            restricted.execute('SELECT RELEASE_LOCK(?)', (LOCK,))
        restricted.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--admin-user', required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not args.apply or os.environ.get('LOCAL_AML_TRIGGER_REPAIR_APPROVED') != 'YES':
        raise SystemExit('Explicit local trigger repair approval required')
    try:
        print(json.dumps(run(args.admin_user), sort_keys=True))
    except Exception as exc:
        print(json.dumps({'status': 'STOPPED', 'error': type(exc).__name__,
                          'action': 'Inspect schema read-only; never rerun blindly'}))
        raise SystemExit(1)
