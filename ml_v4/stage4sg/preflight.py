"""Read-only, fail-closed preflight for the Stage4S-G disposable migration."""
import json
import os

from canonical_history import freshness
from canonical_history_store import assess
from ml_v4.stage4sg.mysql_migration import EXPECTED_COUNTS, INDEX, existing_records
from ml_v4.test_binding import v1


EXPECTED_UUID = 'd441b7bb-43f6-11f1-a2d8-0a0027000005'


def run():
    authority = v1.load_authority()
    if (authority['server_uuid'] != EXPECTED_UUID or
            os.environ.get('V4_STAGE4T_EXPECTED_SERVER_UUID') != EXPECTED_UUID):
        raise RuntimeError('Expected disposable server UUID unavailable')
    db = v1.connection(authority)
    try:
        db.rollback()
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
        db.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY')
        identity = v1.identity(db, EXPECTED_UUID)
        v1._triggers(db)
        v1._boundary(db, authority)
        scope, current, previous = assess(db, v1.SCOPE)
        if freshness(scope, current, previous) != 'COMPLETE_VERIFIED' or current['issues']:
            raise RuntimeError('History authority is incomplete or stale')
        status = db.execute("SHOW TABLE STATUS WHERE Name='transactions'").fetchone()
        if status is None or status['Engine'] != 'InnoDB':
            raise RuntimeError('Transactions table is not InnoDB')
        columns = [dict(row) for row in db.execute('SHOW COLUMNS FROM transactions').fetchall()]
        indexes = [dict(row) for row in db.execute('SHOW INDEX FROM transactions').fetchall()]
        names = [row['Field'] for row in columns]
        if 'client_request_id' in names or any(row['Key_name'] == INDEX for row in indexes):
            raise RuntimeError('Idempotency schema already present; stop before migration')
        if not {'id', 'sender_account'}.issubset(names):
            raise RuntimeError('Expected transaction columns unavailable')
        digests = existing_records(db, names)
        result = {
            'status': 'PASS', 'database': identity['database'],
            'server_uuid': identity['server_uuid'], 'principal': identity['principal'],
            'history_status': 'COMPLETE_VERIFIED', 'capture_triggers': 6,
            'counts': EXPECTED_COUNTS, 'transactions_engine': status['Engine'],
            'transaction_columns': columns, 'transaction_indexes': indexes,
            'existing_row_sha256': digests,
            'idempotency_column_present': False, 'idempotency_index_present': False,
        }
        print(json.dumps(result, sort_keys=True, indent=2, default=str))
    finally:
        db.rollback()
        db.close()


if __name__ == '__main__':
    try:
        run()
    except Exception as exc:
        print('Disposable read-only preflight stopped: ' + type(exc).__name__)
        raise SystemExit(1)
