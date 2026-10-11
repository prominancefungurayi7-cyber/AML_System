"""Strictly read-only diagnosis after an interrupted disposable retry DDL run."""
import json
import os
import re

from canonical_history import freshness
from canonical_history_store import assess
from ml_v4.stage5c.verify_retry import UUID
from ml_v4.test_binding import v1

TABLE = 'v4_primary_attempt_events'
EXPECTED_COLUMNS = ('event_id', 'transaction_id', 'staff_user_id', 'request_key',
                    'event_kind', 'recorded_at', 'outcome', 'error_code',
                    'result_body', 'reason')
EXPECTED_TRIGGERS = {'v4_retry_no_update': 'UPDATE',
                     'v4_retry_no_delete': 'DELETE'}
EXPECTED_FKS = {'fk_v4_attempt_transaction': ('transaction_id', 'transactions', 'id'),
                'fk_v4_attempt_staff': ('staff_user_id', 'users', 'id')}


def ddl_grants(lines):
    """Return required privileges only; never publish raw SHOW GRANTS text."""
    allowed = set()
    for line in lines:
        clean = line.replace('`', '').replace('"', '')
        match = re.search(r'^GRANT\s+(.*?)\s+ON\s+([^ ]+)\s+TO\s+', clean, re.I)
        if match and match.group(2) == v1.DATABASE + '.*':
            allowed.update(item.strip().upper() for item in match.group(1).split(','))
    return {name: name in allowed or 'ALL PRIVILEGES' in allowed
            for name in ('CREATE', 'REFERENCES', 'TRIGGER')}


def inspect(conn, authority):
    # The caller has already verified the connection; repeat identity in this
    # snapshot so schema and history findings share the same pinned server.
    identity = v1.identity(conn, UUID)
    v1._triggers(conn)
    v1._boundary(conn, authority)
    scope, current, previous = assess(conn, v1.SCOPE)
    grants = [next(iter(row.values())) for row in conn.execute('SHOW GRANTS').fetchall()]
    tables = conn.execute('SELECT TABLE_NAME,ENGINE FROM information_schema.TABLES '
                          'WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=?', (TABLE,)).fetchall()
    columns = conn.execute('SELECT COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,EXTRA,'
                           'CHARACTER_SET_NAME,COLLATION_NAME '
                           'FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() '
                           'AND TABLE_NAME=? ORDER BY ORDINAL_POSITION', (TABLE,)).fetchall()
    indexes = conn.execute('SELECT INDEX_NAME,NON_UNIQUE,SEQ_IN_INDEX,COLUMN_NAME '
                           'FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() '
                           'AND TABLE_NAME=? ORDER BY INDEX_NAME,SEQ_IN_INDEX', (TABLE,)).fetchall()
    fks = conn.execute('SELECT CONSTRAINT_NAME,COLUMN_NAME,REFERENCED_TABLE_NAME,'
                       'REFERENCED_COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE '
                       'WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=? '
                       'AND REFERENCED_TABLE_NAME IS NOT NULL', (TABLE,)).fetchall()
    triggers = conn.execute('SELECT TRIGGER_NAME,ACTION_TIMING,EVENT_MANIPULATION,'
                            'EVENT_OBJECT_TABLE,ACTION_STATEMENT FROM information_schema.TRIGGERS '
                            'WHERE TRIGGER_SCHEMA=DATABASE() AND '
                            '(EVENT_OBJECT_TABLE=? OR TRIGGER_NAME IN '
                            "('v4_retry_no_update','v4_retry_no_delete'))", (TABLE,)).fetchall()
    checks = conn.execute('SELECT CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS '
                          "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=? AND CONSTRAINT_TYPE='CHECK'",
                          (TABLE,)).fetchall()
    idx = {}
    for row in indexes:
        idx.setdefault(row['INDEX_NAME'], []).append(row)
    fk_map = {row['CONSTRAINT_NAME']: (row['COLUMN_NAME'], row['REFERENCED_TABLE_NAME'],
                                       row['REFERENCED_COLUMN_NAME']) for row in fks}
    trigger_map = {row['TRIGGER_NAME']: row for row in triggers}
    checks_map = {row['CONSTRAINT_NAME'] for row in checks}
    expected_body = "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='V4 attempt audit is append-only'"
    normalize = lambda value: re.sub(r'\s+', '', value.strip()).upper().rstrip(';')
    unique = idx.get('uq_v4_attempt_event', [])
    staff_index = idx.get('idx_v4_attempt_staff', [])
    expected_schema = {
        'table_innodb': len(tables) == 1 and tables[0]['ENGINE'] == 'InnoDB',
        'columns_order': tuple(row['COLUMN_NAME'] for row in columns) == EXPECTED_COLUMNS,
        'column_types': tuple(row['COLUMN_TYPE'].lower() for row in columns) ==
            ('bigint', 'bigint', 'bigint', 'char(36)', 'varchar(16)', 'varchar(40)',
             'varchar(32)', 'varchar(64)', 'longtext', 'varchar(500)'),
        'nullable_fields': {row['COLUMN_NAME'] for row in columns
                            if row['IS_NULLABLE'] == 'YES'} == {'error_code', 'result_body', 'reason'},
        'event_id_auto_increment': len(columns) == len(EXPECTED_COLUMNS) and
            'auto_increment' in columns[0]['EXTRA'].lower(),
        'request_key_ascii_bin': len(columns) == len(EXPECTED_COLUMNS) and
            columns[3]['CHARACTER_SET_NAME'] == 'ascii' and
            columns[3]['COLLATION_NAME'] == 'ascii_bin',
        'primary_key': [row['COLUMN_NAME'] for row in idx.get('PRIMARY', [])] == ['event_id']
            and all(row['NON_UNIQUE'] == 0 for row in idx.get('PRIMARY', [])),
        'index_names': set(idx) == {'PRIMARY', 'uq_v4_attempt_event', 'idx_v4_attempt_staff'},
        'unique_index': [row['COLUMN_NAME'] for row in unique] ==
            ['transaction_id', 'request_key', 'event_kind'] and
            all(row['NON_UNIQUE'] == 0 for row in unique),
        'staff_index': [row['COLUMN_NAME'] for row in staff_index] == ['staff_user_id'],
        'foreign_keys': fk_map == EXPECTED_FKS,
        'checks': checks_map == {'ck_v4_attempt_kind', 'ck_v4_attempt_outcome'},
        'append_only_triggers': set(trigger_map) == set(EXPECTED_TRIGGERS) and all(
            trigger_map[name]['ACTION_TIMING'] == 'BEFORE' and
            trigger_map[name]['EVENT_MANIPULATION'] == event and
            trigger_map[name]['EVENT_OBJECT_TABLE'] == TABLE and
            normalize(trigger_map[name]['ACTION_STATEMENT']) == normalize(expected_body)
            for name, event in EXPECTED_TRIGGERS.items()),
    }
    counts = {table: conn.execute('SELECT COUNT(*) AS n FROM ' + table).fetchone()['n']
              for table in ('transactions', 'canonical_mobile_money_events',
                            'cmm_source_changes', 'v4_shadow_results')}
    row_count = (conn.execute('SELECT COUNT(*) AS n FROM ' + TABLE).fetchone()['n']
                 if tables else None)
    parent = {}
    for name in ('transactions', 'users'):
        rows = conn.execute('SELECT COLUMN_NAME,COLUMN_TYPE FROM information_schema.COLUMNS '
                            'WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=? AND COLUMN_NAME=?',
                            (name, 'id')).fetchall()
        parent[name] = rows[0]['COLUMN_TYPE'] if len(rows) == 1 else None
    if not tables:
        state = 'ABSENT'
    elif all(expected_schema.values()):
        state = 'COMPLETE'
    elif expected_schema['table_innodb'] and expected_schema['columns_order'] and \
            not expected_schema['append_only_triggers']:
        state = 'PARTIAL_DDL_OR_SCHEMA_MISMATCH'
    else:
        state = 'SCHEMA_MISMATCH'
    return {'status': 'READ_ONLY_INSPECTION', 'identity': identity,
            'server_version': conn.execute('SELECT VERSION() AS version').fetchone()['version'],
            'required_ddl_grants': ddl_grants(grants), 'state': state,
            'audit_row_count': row_count, 'checks': expected_schema,
            'actual_columns': [dict(row) for row in columns],
            'actual_indexes': [dict(row) for row in indexes],
            'actual_foreign_keys': [dict(row) for row in fks],
            'actual_triggers': [{k: row[k] for k in ('TRIGGER_NAME', 'ACTION_TIMING',
                                'EVENT_MANIPULATION', 'EVENT_OBJECT_TABLE')} for row in triggers],
            'actual_check_names': sorted(checks_map), 'parent_id_types': parent,
            'financial_history_counts': counts, 'current_history_status': current['status'],
            'history_issues': current['issues'],
            'history_freshness': freshness(scope, current, previous),
            'current_source_revision': current['source_revision']}


def run():
    if (os.environ.get('V4_STAGE4T_EXPECTED_SERVER_UUID') != UUID or
            os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL') or
            os.environ.get('V4_STAGE4SK_RECOVERY_DB_URL') or
            os.environ.get('STAGE5C_SCHEMA_APPLY')):
        raise RuntimeError('Read-only disposable environment not pinned')
    parsed = v1.config(os.environ.get('V4_STAGE4T_TEST_DB_URL', ''))
    if parsed.hostname != '127.0.0.1' or parsed.port != 3306:
        raise RuntimeError('Only pinned local disposable MySQL allowed')
    authority = v1.load_authority()
    if authority['server_uuid'] != UUID:
        raise RuntimeError('Test authority changed')
    conn = v1.connection(authority)
    try:
        conn.rollback()
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
        conn.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY')
        return inspect(conn, authority)
    finally:
        conn.rollback()
        conn.close()


if __name__ == '__main__':
    try:
        print(json.dumps(run(), sort_keys=True, default=str))
    except Exception as exc:
        print(json.dumps({'status': 'STOPPED', 'error_type': type(exc).__name__}))
        raise SystemExit(1)
