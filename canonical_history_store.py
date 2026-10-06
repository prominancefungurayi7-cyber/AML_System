"""Persistent server/admin-only snapshots. No automatic/public attestation route."""
import json
import uuid
from canonical_history import boundary, validate_scope, verify, now, digest

TABLES={
 'cmm_observation_scopes':('scope_id','revision','body'),
 'cmm_history_attestations':('attestation_id','scope_id','revision','body'),
 'cmm_entity_history':('attestation_id','entity_key','body'),
}


def migrate(conn):
    if conn.engine not in ('mysql','sqlite'): raise ValueError('Unsupported engine')
    created=[]
    for table,names in TABLES.items():
        if conn.engine=='mysql':
            existing=conn.execute('SHOW TABLES LIKE ?', (table,)).fetchone()
            if existing:
                columns=conn.execute('SHOW COLUMNS FROM '+table).fetchall()
                if [r['Field'] for r in columns]!=list(names): raise ValueError('History schema mismatch')
                expected={n:('longtext' if n=='body' else 'bigint' if n=='revision' else 'varchar(255)') for n in names}
                if any(r['Type'].lower()!=expected[r['Field']] or r['Null']!='NO' for r in columns):raise ValueError('History type/nullability mismatch')
                pk=[r['Column_name'] for r in sorted(conn.execute('SHOW INDEX FROM '+table).fetchall(),key=lambda r:r['Seq_in_index']) if r['Key_name']=='PRIMARY']
                expected_pk={'cmm_observation_scopes':['scope_id','revision'],'cmm_history_attestations':['attestation_id'],'cmm_entity_history':['attestation_id','entity_key']}[table]
                if pk!=expected_pk:raise ValueError('History primary key mismatch')
                continue
            text='VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin'
            body='LONGTEXT';number='BIGINT'
        else:
            existing=conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?",(table,)).fetchone()
            if existing:
                if [r['name'] for r in conn.execute('PRAGMA table_info('+table+')').fetchall()]!=list(names): raise ValueError('History schema mismatch')
                continue
            text='TEXT';body='TEXT';number='INTEGER'
        defs=[n+' '+(body if n=='body' else number if n=='revision' else text)+' NOT NULL' for n in names]
        pk={'cmm_observation_scopes':'scope_id,revision','cmm_history_attestations':'attestation_id','cmm_entity_history':'attestation_id,entity_key'}[table]
        conn.execute('CREATE TABLE '+table+' ('+','.join(defs)+', PRIMARY KEY ('+pk+'))'+(' ENGINE=InnoDB' if conn.engine=='mysql' else ''))
        created.append(table)
    return created


def snapshot(conn):
    """Caller MUST hold a consistent DB snapshot; no model/label/provenance access."""
    parents=[dict(r) for r in conn.execute('SELECT id,timestamp,sender_account,receiver_account,transaction_type,currency,agent_id FROM transactions ORDER BY id').fetchall()]
    canonical=[dict(r) for r in conn.execute('SELECT * FROM canonical_mobile_money_events ORDER BY transaction_id').fetchall()]
    changes=[dict(r) for r in conn.execute('SELECT * FROM cmm_source_changes ORDER BY change_id').fetchall()]
    return parents,canonical,changes


def current_scope(conn, scope_id):
    row=conn.execute('SELECT body FROM cmm_observation_scopes WHERE scope_id=? ORDER BY revision DESC LIMIT 1',(scope_id,)).fetchone()
    return json.loads(row['body']) if row else None


def create_scope(conn, scope_id, authority, evidence):
    from canonical_history_journal import ensure
    ensure(conn)
    if current_scope(conn,scope_id): raise ValueError('Scope already exists; do not reset boundary')
    # One global scope prevents creating a later scope to hide known gaps.
    if conn.execute('SELECT scope_id FROM cmm_observation_scopes LIMIT 1').fetchone():
        raise ValueError('Prototype observation boundary already established')
    fence=conn.execute('SELECT COALESCE(MAX(id),0) AS fence FROM transactions').fetchone()['fence']
    scope=boundary(scope_id,now(),int(fence),authority,evidence)
    # Snapshot membership, not account creation/activation. These sets also
    # expose commits of previously invisible lower auto-increment IDs.
    scope['preexisting_parent_ids']=[r['id'] for r in conn.execute('SELECT id FROM transactions ORDER BY id').fetchall()]
    scope['preexisting_change_ids']=[r['change_id'] for r in conn.execute('SELECT change_id FROM cmm_source_changes ORDER BY change_id').fetchall()]
    conn.execute('INSERT INTO cmm_observation_scopes VALUES (?,?,?)',(scope_id,1,json.dumps(scope)))
    return scope


def revise_scope(conn, scope_id, authority, evidence):
    scope=current_scope(conn,scope_id)
    if not scope: raise ValueError('Unknown scope')
    if not authority or not evidence: raise ValueError('Authority/evidence required')
    scope.update(revision=scope['revision']+1,verification_timestamp=now(),verification_authority=authority,evidence_reference=evidence)
    # Immutable start/fence/source: revision is not permission to discard a gap.
    conn.execute('INSERT INTO cmm_observation_scopes VALUES (?,?,?)',(scope_id,scope['revision'],json.dumps(scope)))
    return scope


def latest(conn,scope_id):
    rows=conn.execute('SELECT body FROM cmm_history_attestations WHERE scope_id=?',(scope_id,)).fetchall()
    return max((json.loads(r['body']) for r in rows),key=lambda r:r['sequence'],default=None)


def assess(conn,scope_id,resolutions=None):
    from canonical_history_journal import ensure
    ensure(conn)
    scope=current_scope(conn,scope_id)
    if not scope: raise ValueError('Unknown observation scope')
    parents,canonical,changes=snapshot(conn)
    previous=latest(conn,scope_id)
    result=verify(scope,parents,canonical,now(),previous,resolutions,changes)
    return scope,result,previous


def attest(conn, scope_id, authority, evidence, resolutions=None):
    """Privileged local command only; no parameter accepts a desired status."""
    if not authority or not evidence: raise ValueError('Authority/evidence required')
    scope,result,previous=assess(conn,scope_id,resolutions)
    result.update(attestation_id=str(uuid.uuid4()),sequence=previous['sequence']+1 if previous else 1,
                  verification_authority=authority,evidence_reference=evidence)
    conn.execute('INSERT INTO cmm_history_attestations VALUES (?,?,?,?)',
        (result['attestation_id'],scope_id,scope['revision'],json.dumps(result)))
    for key,state in result['entities'].items():
        state.update(source_revision=result['source_revision'],evidence_reference=evidence,verified_at=result['verified_at'])
        conn.execute('INSERT INTO cmm_entity_history VALUES (?,?,?)',(result['attestation_id'],key,json.dumps(state)))
    return result
