"""Prepared additive disposable-MySQL migration. Never run automatically."""
import argparse
import hashlib
import json
import os

from ml_v4.test_binding import v1


INDEX = 'uq_transactions_sender_request'
EXPECTED_COUNTS = {
    'transactions': 4,
    'canonical_mobile_money_events': 4,
    'cmm_source_changes': 8,
    'v4_shadow_results': 4,
    'alerts': 0,
    'sar_reports': 0,
    'ctr_reports': 0,
}


def existing_records(connection, transaction_columns):
    """Digest every reviewed financial/history row without exporting row data."""
    tx_columns = ','.join('`' + name.replace('`', '``') + '`' for name in transaction_columns)
    queries = {
        'transactions': 'SELECT ' + tx_columns + ' FROM transactions ORDER BY id',
        'canonical_mobile_money_events': 'SELECT * FROM canonical_mobile_money_events ORDER BY transaction_id',
        'cmm_source_changes': 'SELECT * FROM cmm_source_changes ORDER BY change_id',
        'v4_shadow_results': 'SELECT * FROM v4_shadow_results ORDER BY transaction_id,model_version,feature_version',
        'alerts': 'SELECT * FROM alerts ORDER BY id',
        'sar_reports': 'SELECT * FROM sar_reports ORDER BY id',
        'ctr_reports': 'SELECT * FROM ctr_reports ORDER BY id',
    }
    output = {}
    for table, sql in queries.items():
        rows = [dict(row) for row in connection.execute(sql).fetchall()]
        if len(rows) != EXPECTED_COUNTS[table]:
            raise RuntimeError('Existing disposable record count changed: ' + table)
        output[table] = hashlib.sha256(json.dumps(rows, sort_keys=True,
                                                    default=str, separators=(',', ':')).encode()).hexdigest()
    return output


def migrate(expected_transactions):
    authority = v1.load_authority()
    if (authority['server_uuid'] != 'd441b7bb-43f6-11f1-a2d8-0a0027000005'
            or os.environ.get('V4_STAGE4T_EXPECTED_SERVER_UUID') != authority['server_uuid']):
        raise RuntimeError('Disposable server identity not pinned')
    connection = v1.connection(authority)
    try:
        v1._triggers(connection)
        v1._boundary(connection, authority)
        from canonical_history_store import assess
        from canonical_history import freshness
        scope, current, previous = assess(connection, v1.SCOPE)
        if freshness(scope, current, previous) != 'COMPLETE_VERIFIED' or current['issues']:
            raise RuntimeError('Existing disposable history is not fresh')
        row = connection.execute("SHOW TABLE STATUS WHERE Name='transactions'").fetchone()
        if row is None or row['Engine'] != 'InnoDB':
            raise RuntimeError('Expected InnoDB transactions table unavailable')
        count = connection.execute('SELECT COUNT(*) AS n FROM transactions').fetchone()['n']
        if count != expected_transactions or count != EXPECTED_COUNTS['transactions']:
            raise RuntimeError('Transaction count changed since migration review')
        transaction_columns = [row['Field'] for row in
                               connection.execute('SHOW COLUMNS FROM transactions').fetchall()]
        before = existing_records(connection, transaction_columns)
        if connection.execute("SHOW COLUMNS FROM transactions LIKE 'client_request_id'").fetchall():
            raise RuntimeError('Request ID column already exists; review before retrying')
        if connection.execute("SHOW INDEX FROM transactions WHERE Key_name='uq_transactions_sender_request'").fetchall():
            raise RuntimeError('Request ID index already exists; review before retrying')
        connection.rollback()
        # MySQL DDL implicitly commits. One reviewed ALTER adds both parts of the gate.
        connection.execute('ALTER TABLE transactions ADD COLUMN client_request_id '
                           'CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL, '
                           'ADD UNIQUE INDEX uq_transactions_sender_request '
                           '(sender_account, client_request_id)')
        from transaction_idempotency import require_schema
        require_schema(connection)
        v1._triggers(connection)
        v1._boundary(connection, authority)
        scope, current, previous = assess(connection, v1.SCOPE)
        if freshness(scope, current, previous) != 'COMPLETE_VERIFIED' or current['issues']:
            raise RuntimeError('Post-migration history authority changed')
        after = connection.execute('SELECT COUNT(*) AS n FROM transactions').fetchone()['n']
        if after != count or existing_records(connection, transaction_columns) != before:
            raise RuntimeError('Existing disposable records changed; investigate')
        print('Disposable idempotency schema migration verified')
    finally:
        connection.rollback()
        connection.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Approved disposable MySQL migration only')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--expected-transactions', type=int, required=True)
    args = parser.parse_args()
    if not args.apply or args.expected_transactions < 0:
        parser.error('Explicit --apply and reviewed nonnegative count required')
    migrate(args.expected_transactions)
