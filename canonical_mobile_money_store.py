"""Additive canonical ledger migration/persistence. No startup migrations."""
from dataclasses import asdict
from canonical_mobile_money import VERSION, FIELDS, event_from_dict

TABLE = 'canonical_mobile_money_events'
COLUMNS = (*FIELDS, 'canonical_version', 'history_status')
INDEXES = {
    'cmm_time_id': ('event_timestamp', 'transaction_id'),
    'cmm_sender_time_id': ('sender_wallet', 'event_timestamp', 'transaction_id'),
    'cmm_receiver_time_id': ('receiver_wallet', 'event_timestamp', 'transaction_id'),
    'cmm_agent_time_id': ('agent_id', 'event_timestamp', 'transaction_id'),
    'cmm_serviced_time_id': ('serviced_wallet', 'event_timestamp', 'transaction_id'),
}


def inspect(conn):
    engine = conn.engine
    if engine not in ('sqlite', 'mysql'):
        raise ValueError('Unsupported migration engine')
    if engine == 'mysql':
        parent = conn.execute('SHOW COLUMNS FROM transactions').fetchall()
        if not any(r['Field'] == 'id' and r['Type'].lower() == 'bigint' for r in parent):
            raise ValueError('Expected signed BIGINT parent ID')
        tables = conn.execute("SHOW TABLE STATUS WHERE Name IN ('transactions','canonical_mobile_money_events')").fetchall()
        if any(r['Engine'] != 'InnoDB' for r in tables):
            raise ValueError('InnoDB required for atomic persistence')
        exists = any(r['Name'] == TABLE for r in tables)
        if not exists:
            return {'engine': engine, 'exists': False}
        cols = conn.execute('SHOW COLUMNS FROM ' + TABLE).fetchall()
        indexes = conn.execute('SHOW INDEX FROM ' + TABLE).fetchall()
        names = [r['Field'] for r in cols]
        actual = {}
        for r in sorted(indexes, key=lambda x: (x['Key_name'], x['Seq_in_index'])):
            actual.setdefault(r['Key_name'], []).append(r['Column_name'])
    else:
        if not conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'").fetchone():
            raise ValueError('Missing transactions parent')
        exists = bool(conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (TABLE,)).fetchone())
        if not exists:
            return {'engine': engine, 'exists': False}
        cols = conn.execute('PRAGMA table_info(' + TABLE + ')').fetchall()
        names = [r['name'] for r in cols]
        actual = {}
        for r in conn.execute('PRAGMA index_list(' + TABLE + ')').fetchall():
            # Only our constant index names can enter PRAGMA text.
            if r['name'] in INDEXES:
                actual[r['name']] = [v['name'] for v in conn.execute('PRAGMA index_info(' + r['name'] + ')').fetchall()]
    if names != list(COLUMNS) or any(actual.get(k) != list(v) for k, v in INDEXES.items()):
        raise ValueError('Existing canonical schema/index mismatch; no automatic repair')
    expected_types = {k: ('bigint' if k in ('transaction_id', 'amount_minor') else 'varchar(255)') for k in COLUMNS}
    if engine == 'mysql':
        if any(r['Type'].lower() != expected_types[r['Field']] or r['Null'] != 'NO' for r in cols):
            raise ValueError('Canonical column type/nullability mismatch')
        if actual.get('PRIMARY') != ['transaction_id']:
            raise ValueError('Canonical primary key mismatch')
        foreign = conn.execute("SELECT REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME, COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=? AND REFERENCED_TABLE_NAME IS NOT NULL", (TABLE,)).fetchall()
        if len(foreign) != 1 or dict(foreign[0]) != {'REFERENCED_TABLE_NAME':'transactions','REFERENCED_COLUMN_NAME':'id','COLUMN_NAME':'transaction_id'}:
            raise ValueError('Canonical parent foreign key mismatch')
    else:
        if any(r['type'].upper() != ('INTEGER' if r['name'] in ('transaction_id','amount_minor') else 'TEXT') for r in cols):
            raise ValueError('Canonical column types mismatch')
        if not next(r for r in cols if r['name'] == 'transaction_id')['pk']:
            raise ValueError('Canonical primary key missing')
        foreign = conn.execute('PRAGMA foreign_key_list(' + TABLE + ')').fetchall()
        if len(foreign) != 1 or foreign[0]['table'] != 'transactions' or foreign[0]['from'] != 'transaction_id' or foreign[0]['to'] != 'id' or foreign[0]['on_delete'] != 'RESTRICT':
            raise ValueError('Canonical parent foreign key mismatch')
    return {'engine': engine, 'exists': True, 'columns': names, 'indexes': actual}


def migrate(conn):
    """Create only the new table. Existing mismatch fails; never alters old rows."""
    before = inspect(conn)
    if before['exists']:
        return {'changed': False, 'schema': before}
    mysql = conn.engine == 'mysql'
    integer = 'BIGINT' if mysql else 'INTEGER'
    text = 'VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin' if mysql else 'TEXT'
    defs = [f'{name} {integer if name in ("transaction_id", "amount_minor") else text} NOT NULL' +
            (' PRIMARY KEY' if name == 'transaction_id' else '') for name in COLUMNS]
    defs += ["CHECK (amount_minor BETWEEN 1 AND 1500000)", "CHECK (currency = 'USD')",
             "CHECK (history_status = 'UNKNOWN')",
             "FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE RESTRICT"]
    if mysql:
        defs += [f'INDEX {name} ({", ".join(cols)})' for name, cols in INDEXES.items()]
    conn.execute('CREATE TABLE ' + TABLE + ' (' + ', '.join(defs) + ')' + (' ENGINE=InnoDB' if mysql else ''))
    if not mysql:
        for name, cols in INDEXES.items():
            conn.execute(f'CREATE INDEX {name} ON {TABLE} ({", ".join(cols)})')
    return {'changed': True, 'schema': inspect(conn)}


def persist(conn, event):
    """Caller owns commit/rollback; no fallback, upsert, history guess or prediction."""
    raw = asdict(event)
    event_from_dict(raw)
    if not inspect(conn)['exists']:
        raise ValueError('Canonical schema has not been prepared')
    parent = conn.execute('SELECT id, sender_account, receiver_account, transaction_type, agent_id FROM transactions WHERE id=?', (event.transaction_id,)).fetchone()
    from canonical_mobile_money import LEGACY_TYPES
    if (not parent or parent['sender_account'] != event.sender_wallet or parent['receiver_account'] != event.receiver_wallet
        or parent['transaction_type'] != LEGACY_TYPES[event.transaction_type]
        or str(parent['agent_id'] or '') != event.agent_id):
        raise ValueError('Canonical parent identity/role mismatch')
    if event.agent_id:
        if not event.agent_id.isascii() or not event.agent_id.isdigit() or str(int(event.agent_id)) != event.agent_id:
            raise ValueError('Application agents require canonical decimal IDs')
        if not conn.execute('SELECT id FROM agents WHERE id=?', (int(event.agent_id),)).fetchone():
            raise ValueError('Unknown cash/service agent')
    values = [raw[k] for k in FIELDS] + [VERSION, 'UNKNOWN']
    conn.execute('INSERT INTO ' + TABLE + ' (' + ','.join(COLUMNS) + ') VALUES (' + ','.join('?' for _ in COLUMNS) + ')', tuple(values))


def load(conn, transaction_id):
    row = conn.execute('SELECT * FROM ' + TABLE + ' WHERE transaction_id=?', (transaction_id,)).fetchone()
    if row is None:
        return None
    if row['canonical_version'] != VERSION:
        raise ValueError('Unsupported canonical version')
    return event_from_dict({k: row[k] for k in FIELDS})
