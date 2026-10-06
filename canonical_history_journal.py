"""Database capture journal: source changes survive deletion between verifier runs.

Not independent custody. DB administrators can tamper; trigger definitions are
verified before each assessment. No existing business records are changed.
"""

TABLE='cmm_source_changes'


def triggers(engine):
    clock="DATE_FORMAT(UTC_TIMESTAMP(6),'%Y-%m-%dT%H:%i:%s.%fZ')" if engine=='mysql' else "strftime('%Y-%m-%dT%H:%M:%fZ','now')"
    out={}
    for table,prefix,idcol,timecol in [('transactions','cmm_tx','id','timestamp'),('canonical_mobile_money_events','cmm_ce','transaction_id','event_timestamp')]:
        for op in ('INSERT','UPDATE','DELETE'):
            row='OLD' if op=='DELETE' else 'NEW'
            name=prefix+'_'+op.lower()
            operation=('SOURCE_' if prefix=='cmm_tx' else 'CANONICAL_')+op
            statement=f"INSERT INTO {TABLE} (transaction_id,operation,event_timestamp,recorded_at) VALUES ({row}.{idcol},'{operation}',{row}.{timecol},{clock});"
            if op=='UPDATE' and prefix=='cmm_tx':
                fields=('id','timestamp','sender_account','receiver_account','transaction_type','currency','agent_id','amount')
                equal=' AND '.join(f'OLD.{f} <=> NEW.{f}' if engine=='mysql' else f'OLD.{f} IS NEW.{f}' for f in fields)
                if engine=='mysql': body='BEGIN IF NOT ('+equal+') THEN '+statement+' END IF; END'
                else: body='WHEN NOT ('+equal+') BEGIN '+statement+' END'
            else: body='BEGIN '+statement+' END'
            out[name]=(table,op,body)
    return out


def ensure(conn, apply=False):
    if conn.engine not in ('mysql','sqlite'):raise ValueError('Unsupported journal engine')
    mysql=conn.engine=='mysql'
    exists=conn.execute('SHOW TABLES LIKE ?', (TABLE,)).fetchone() if mysql else conn.execute("SELECT name FROM sqlite_master WHERE name=? AND type='table'",(TABLE,)).fetchone()
    if not exists:
        if not apply:raise ValueError('Coverage capture journal unavailable')
        ddl=("change_id BIGINT AUTO_INCREMENT PRIMARY KEY,transaction_id BIGINT NOT NULL,operation VARCHAR(32) NOT NULL,event_timestamp VARCHAR(255) NOT NULL,recorded_at VARCHAR(40) NOT NULL" if mysql else "change_id INTEGER PRIMARY KEY AUTOINCREMENT,transaction_id INTEGER NOT NULL,operation TEXT NOT NULL,event_timestamp TEXT NOT NULL,recorded_at TEXT NOT NULL")
        conn.execute('CREATE TABLE '+TABLE+' ('+ddl+')'+(' ENGINE=InnoDB' if mysql else ''))
    for name,(table,op,body) in triggers(conn.engine).items():
        ddl=f'CREATE TRIGGER {name} AFTER {op} ON {table} FOR EACH ROW {body}'
        if mysql:
            row=conn.execute('SELECT ACTION_STATEMENT,EVENT_MANIPULATION,EVENT_OBJECT_TABLE FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND TRIGGER_NAME=?',(name,)).fetchone()
            if row and (row['EVENT_MANIPULATION']!=op or row['EVENT_OBJECT_TABLE']!=table or row['ACTION_STATEMENT'].strip()!=body):
                raise ValueError('Capture trigger mismatch: '+name)
        else:
            row=conn.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?",(name,)).fetchone()
            if row and row['sql'].strip()!=ddl:raise ValueError('Capture trigger mismatch')
        if not row:
            if not apply:raise ValueError('Capture trigger missing: '+name)
            conn.execute(ddl)
    return {'table':TABLE,'triggers':list(triggers(conn.engine))}
