"""Read-only identity and post-restore checks for a separate recovery schema."""
import argparse
import json
import os
import re
from urllib.parse import unquote, urlparse

from database import DatabaseAdapter
from ml_v4.stage4sg.mysql_migration import EXPECTED_COUNTS, existing_records
from ml_v4.stage4sg.restore_sql import RECOVERY
from ml_v4.test_binding import v1

USER = 'v4_stage4sk_restore'
UUID = 'd441b7bb-43f6-11f1-a2d8-0a0027000005'
REQUIRED = {'SELECT', 'INSERT', 'CREATE', 'DROP', 'INDEX', 'ALTER',
            'TRIGGER', 'LOCK TABLES', 'REFERENCES'}
ALLOWED = REQUIRED | {'CREATE VIEW', 'SHOW VIEW'}


def grant_check(lines, exact=False):
    found = set()
    if not lines:
        raise ValueError('Recovery grants unavailable')
    for line in lines:
        normalized = line.replace('`', '').replace('"', '').replace("'", '')
        if 'WITH GRANT OPTION' in normalized.upper():
            raise ValueError('Recovery account can grant privileges')
        match = re.search(r'^GRANT\s+(.+?)\s+ON\s+(\S+)\s+TO\s+', normalized, re.I)
        if not match:
            raise ValueError('Unrecognized recovery grant')
        privileges = {item.strip().upper() for item in match.group(1).split(',')}
        target = match.group(2).lower()
        if target == '*.*':
            if privileges != {'USAGE'}:
                raise ValueError('Global recovery grant is not restricted')
        elif target == RECOVERY.lower() + '.*':
            if not privileges <= ALLOWED:
                raise ValueError('Unexpected recovery privilege')
            found |= privileges
        else:
            raise ValueError('Recovery account has access outside target schema')
    if not REQUIRED <= found:
        raise ValueError('Recovery account lacks required scoped privileges')
    if exact and found != REQUIRED:
        raise ValueError('Recovery account has privileges beyond exact provisioning set')


def connection(exact_grants=False):
    raw = os.environ.get('V4_STAGE4SK_RECOVERY_DB_URL', '')
    parsed = urlparse(raw)
    if (parsed.scheme != 'mysql' or parsed.hostname != '127.0.0.1' or
            parsed.port != 3306 or parsed.path != '/' + RECOVERY or
            unquote(parsed.username or '') != USER or not parsed.password or
            parsed.query or parsed.fragment or
            os.environ.get('V4_STAGE4SK_EXPECTED_SERVER_UUID') != UUID):
        raise ValueError('Recovery URL or UUID binding invalid')
    import mysql.connector
    db = DatabaseAdapter(mysql.connector.connect(
        host='127.0.0.1', port=3306, user=USER,
        password=unquote(parsed.password), database=RECOVERY,
        connection_timeout=5, charset='utf8mb4'), 'mysql')
    try:
        row = db.execute('SELECT DATABASE() AS db, @@server_uuid AS uuid, CURRENT_USER() AS principal').fetchone()
        if (row['db'] != RECOVERY or row['uuid'] != UUID or
                not re.fullmatch(re.escape(USER) + r'@[^@]+', row['principal'])):
            raise ValueError('Recovery database/server/principal mismatch')
        grants = [next(iter(row.values())) for row in db.execute('SHOW GRANTS').fetchall()]
        grant_check(grants, exact=exact_grants)
        return db, row
    except Exception:
        db.close()
        raise


def check(before, original_digests=None, expected_indexes=None, expected_tables=None,
          exact_grants=False):
    db, identity = connection(exact_grants=exact_grants)
    try:
        tables = [dict(row) for row in db.execute('SHOW FULL TABLES').fetchall()]
        if before:
            if tables:
                raise ValueError('Recovery database is not empty')
            return {'status': 'EMPTY_RECOVERY_VERIFIED', 'identity': identity,
                    'table_count': 0}
        table_names = {next(iter(row.values())) for row in tables}
        if expected_tables is not None and table_names != set(expected_tables):
            raise ValueError('Restored table set differs from backup')
        v1._triggers(db)
        columns = [row['Field'] for row in db.execute('SHOW COLUMNS FROM transactions').fetchall()]
        indexes = [row['Key_name'] for row in db.execute('SHOW INDEX FROM transactions').fetchall()]
        if 'client_request_id' in columns or 'uq_transactions_sender_request' in indexes:
            raise ValueError('Unexpected idempotency schema in restored pre-migration backup')
        if expected_indexes is not None and set(indexes) != set(expected_indexes):
            raise ValueError('Restored transaction indexes differ from backup')
        digests = existing_records(db, columns)
        if original_digests is not None and digests != original_digests:
            raise ValueError('Restored row digests differ from original preflight')
        return {'status': 'RESTORED_ROWS_VERIFIED', 'identity': identity,
                'counts': EXPECTED_COUNTS, 'capture_triggers': 6,
                'tables': sorted(table_names),
                'transaction_columns': columns, 'transaction_indexes': sorted(set(indexes)),
                'existing_row_sha256': digests,
                'matched_original_preflight': original_digests is not None}
    finally:
        db.rollback()
        db.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('before', 'after'))
    parser.add_argument('--original-evidence')
    parser.add_argument('--expected-index', action='append')
    parser.add_argument('--expected-table', action='append')
    parser.add_argument('--exact-grants', action='store_true')
    args = parser.parse_args()
    try:
        expected = None
        if args.original_evidence:
            evidence = json.loads(open(args.original_evidence, encoding='utf-8').read())
            if (evidence.get('status') != 'PASS' or
                    evidence.get('database') != v1.DATABASE or
                    evidence.get('server_uuid') != UUID or
                    evidence.get('counts') != EXPECTED_COUNTS):
                raise ValueError('Original preflight evidence invalid')
            expected = evidence['existing_row_sha256']
        print(json.dumps(check(args.mode == 'before', expected, args.expected_index,
                               args.expected_table, args.exact_grants),
                         indent=2, sort_keys=True, default=str))
    except Exception as exc:
        print('Recovery guard stopped: ' + type(exc).__name__)
        raise SystemExit(1)
