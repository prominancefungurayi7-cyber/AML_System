"""Guarded LOCAL aml V4 schema preparation. DDL requires explicit approval/--apply.

Never use this for Railway or the disposable v4_stage4s_disposable database.
MySQL DDL commits implicitly: inspect schema after any failure; do not auto-retry.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

from dotenv import dotenv_values

from canonical_history import freshness
from canonical_history_journal import triggers
from canonical_history_store import assess
from database import connect_db
from transaction_idempotency import require_schema
import v4_retry

ROOT = Path(__file__).resolve().parents[1]
UUID = 'd441b7bb-43f6-11f1-a2d8-0a0027000005'
PRINCIPAL = 'aml@127.0.0.1'
SCOPE = 'controlled-prototype-v1'
MODEL_SHA = '555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18'


def inspect(conn):
    identity = conn.execute('SELECT DATABASE() AS db, @@server_uuid AS uuid, '
                            'CURRENT_USER() AS principal').fetchone()
    if identity != {'db': 'aml', 'uuid': UUID, 'principal': PRINCIPAL}:
        raise RuntimeError('Local aml identity changed')
    scope, current, previous = assess(conn, SCOPE)
    boundary = json.loads((ROOT / 'ml_v4/evidence/integration_stage2a2/'
                           'observation_boundary.json').read_text())
    keys = ('scope_id', 'scope_version', 'start_timestamp',
            'start_transaction_id_exclusive', 'source_ledger',
            'canonical_version', 'preexisting_parent_ids',
            'preexisting_change_ids')
    if any(scope.get(key) != boundary.get(key) for key in keys):
        raise RuntimeError('Local observation boundary changed')
    if (current['status'] != 'COMPLETE_VERIFIED' or current['issues'] or
            freshness(scope, current, previous) != 'COMPLETE_VERIFIED'):
        raise RuntimeError('Local history is not fresh')
    actual = {row['TRIGGER_NAME']: row for row in conn.execute(
        'SELECT TRIGGER_NAME,EVENT_OBJECT_TABLE,EVENT_MANIPULATION,'
        'ACTION_TIMING,ACTION_STATEMENT FROM information_schema.TRIGGERS '
        'WHERE TRIGGER_SCHEMA=DATABASE()').fetchall()
        if row['TRIGGER_NAME'].startswith('cmm_')}
    expected = triggers('mysql')
    if set(actual) != set(expected):
        raise RuntimeError('Capture trigger set changed')
    for name, (table, operation, body) in expected.items():
        item = actual[name]
        if (item['EVENT_OBJECT_TABLE'], item['EVENT_MANIPULATION'],
                item['ACTION_TIMING'], item['ACTION_STATEMENT']) != (
                    table, operation, 'AFTER', body):
            raise RuntimeError('Capture trigger changed: ' + name)
    counts = {table: conn.execute('SELECT COUNT(*) AS n FROM ' + table).fetchone()['n']
              for table in ('transactions', 'canonical_mobile_money_events',
                            'cmm_source_changes', 'cmm_history_attestations',
                            'v4_shadow_results', 'users', 'alerts')}
    return {'identity': identity, 'history': current['status'],
            'attestation_sequence': previous['sequence'], 'counts': counts}


def run(backup, expected_sha, apply):
    url = dotenv_values(ROOT / '.env').get('DATABASE_URL')
    parsed = urlparse(url or '')
    if (parsed.scheme, parsed.hostname, parsed.port, parsed.path) != (
            'mysql', '127.0.0.1', 3306, '/aml'):
        raise RuntimeError('Expected local aml .env connection unavailable')
    if backup.resolve().parent != (ROOT / 'data/local-v4-backups').resolve():
        raise RuntimeError('Backup must be in the ignored local backup directory')
    if not backup.is_file() or backup.stat().st_size < 100000:
        raise RuntimeError('Local backup missing or incomplete')
    actual_sha = hashlib.sha256(backup.read_bytes()).hexdigest()
    if actual_sha != expected_sha:
        raise RuntimeError('Local backup SHA-256 mismatch')
    model = ROOT / 'ml_v4/development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib'
    if hashlib.sha256(model.read_bytes()).hexdigest() != MODEL_SHA:
        raise RuntimeError('Frozen model changed')
    conn = connect_db(url)
    try:
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
        conn.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY')
        before = inspect(conn)
        column = conn.execute("SHOW COLUMNS FROM transactions LIKE 'client_request_id'").fetchall()
        index = conn.execute("SHOW INDEX FROM transactions WHERE Key_name='uq_transactions_sender_request'").fetchall()
        retry_table = conn.execute("SHOW TABLES LIKE 'v4_primary_attempt_events'").fetchone()
        if column or index or retry_table:
            raise RuntimeError('Expected missing schema changed; inspect before migration')
        if not apply:
            return {'status': 'READY_FOR_APPROVAL', **before,
                    'backup_sha256': actual_sha,
                    'required_ddl': ['idempotency column and unique index',
                                     'retry audit table', 'two append-only triggers']}
        conn.rollback()
        # MySQL DDL commits implicitly. Every subsequent step is checked and
        # partial DDL must be inspected manually; this script never retries.
        conn.execute('ALTER TABLE transactions ADD COLUMN client_request_id '
                     'CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL, '
                     'ADD UNIQUE INDEX uq_transactions_sender_request '
                     '(sender_account, client_request_id)')
        require_schema(conn)
        source = (ROOT / 'ml_v4/stage5c/retry_audit_schema_disposable.sql').read_text()
        start = source.index('CREATE TABLE v4_stage4s_disposable.v4_primary_attempt_events')
        table_sql = source[start:source.index('CREATE TRIGGER', start)].strip().rstrip(';')
        table_sql = table_sql.replace('v4_stage4s_disposable.', 'aml.')
        conn.execute(table_sql)
        for name, operation in (('v4_retry_no_update', 'UPDATE'),
                                ('v4_retry_no_delete', 'DELETE')):
            conn.execute('CREATE TRIGGER aml.' + name + ' BEFORE ' + operation +
                         ' ON aml.v4_primary_attempt_events FOR EACH ROW '
                         "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT="
                         "'V4 attempt audit is append-only'")
        v4_retry.require_schema(conn)
        if conn.execute('SELECT COUNT(*) AS n FROM v4_primary_attempt_events').fetchone()['n']:
            raise RuntimeError('New retry audit table is not empty')
        after = inspect(conn)
        if after != before:
            raise RuntimeError('Existing local history or row counts changed during migration')
        return {'status': 'MIGRATED', **after, 'backup_sha256': actual_sha}
    finally:
        conn.rollback()
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--backup', required=True, type=Path)
    parser.add_argument('--backup-sha256', required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    print(json.dumps(run(args.backup, args.backup_sha256, args.apply), sort_keys=True))
