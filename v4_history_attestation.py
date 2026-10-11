"""Refresh the existing local aml history attestation after a committed payment."""
import json
from pathlib import Path

from canonical_history import freshness
from canonical_history_journal import triggers
from canonical_history_store import assess, attest

SCOPE = 'controlled-prototype-v1'
SERVER_UUID = 'd441b7bb-43f6-11f1-a2d8-0a0027000005'
BOUNDARY = Path(__file__).resolve().parent / 'ml_v4/evidence/integration_stage2a2/observation_boundary.json'
LOCK = 'cmm_history_admin_v1'


def _snapshot(conn, tx):
    conn.rollback()
    conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
    conn.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT')
    identity = conn.execute('SELECT DATABASE() AS db, @@server_uuid AS uuid, '
                            'CURRENT_USER() AS principal').fetchone()
    if (identity['db'] != 'aml' or identity['uuid'] != SERVER_UUID or
            identity['principal'] != 'aml@127.0.0.1'):
        raise RuntimeError('Local history authority changed')
    actual = {row['TRIGGER_NAME']: row for row in conn.execute(
        'SELECT TRIGGER_NAME,EVENT_OBJECT_TABLE,EVENT_MANIPULATION,ACTION_TIMING,'
        'ACTION_STATEMENT FROM information_schema.TRIGGERS '
        'WHERE TRIGGER_SCHEMA=DATABASE()').fetchall()
        if row['TRIGGER_NAME'].startswith('cmm_')}
    expected = triggers('mysql')
    if set(actual) != set(expected):
        raise RuntimeError('Canonical capture triggers changed')
    for name, (table, operation, body) in expected.items():
        row = actual[name]
        if (row['EVENT_OBJECT_TABLE'], row['EVENT_MANIPULATION'],
                row['ACTION_TIMING'], row['ACTION_STATEMENT']) != (
                    table, operation, 'AFTER', body):
            raise RuntimeError('Canonical capture trigger changed')
    scope, current, previous = assess(conn, SCOPE)
    boundary = json.loads(BOUNDARY.read_text())
    keys = ('scope_id', 'scope_version', 'start_timestamp',
            'start_transaction_id_exclusive', 'source_ledger',
            'canonical_version', 'preexisting_parent_ids',
            'preexisting_change_ids')
    if any(scope.get(key) != boundary.get(key) for key in keys):
        raise RuntimeError('Pinned local history boundary changed')
    authority = 'configured-db-identity:' + identity['principal']
    if (scope.get('verification_authority') != authority or previous is None or
            previous.get('verification_authority') != authority):
        raise RuntimeError('Existing history authority changed')
    if current['status'] != 'COMPLETE_VERIFIED' or current['issues']:
        raise RuntimeError('Committed history is incomplete')
    if tx not in current['canonical_event_ids']:
        raise RuntimeError('Committed transaction absent from verified canonical history')
    captures = [row['operation'] for row in conn.execute(
        'SELECT operation FROM cmm_source_changes WHERE transaction_id=? '
        'ORDER BY change_id', (tx,)).fetchall()]
    if captures != ['SOURCE_INSERT', 'CANONICAL_INSERT']:
        raise RuntimeError('Committed transaction capture records incomplete')
    return scope, current, previous, authority


def refresh_committed(connection_factory, tx):
    """Attest the complete current source revision; never touch payment rows."""
    if type(tx) is not int or tx <= 0:
        raise ValueError('Invalid committed transaction ID')
    conn = connection_factory()
    locked = False
    try:
        if conn.engine != 'mysql':
            raise RuntimeError('Local MySQL history authority required')
        if conn.execute('SELECT GET_LOCK(?,5) AS acquired', (LOCK,)).fetchone()['acquired'] != 1:
            raise RuntimeError('History attestation lock unavailable')
        locked = True
        scope, current, previous, authority = _snapshot(conn, tx)
        revision = current['source_revision']
        if freshness(scope, current, previous) != 'COMPLETE_VERIFIED':
            evidence = 'application-commit:transaction:' + str(tx) + ':source-revision:' + revision
            result = attest(conn, SCOPE, authority, evidence)
            if result['status'] != 'COMPLETE_VERIFIED' or result['source_revision'] != revision:
                raise RuntimeError('History attestation source changed')
            conn.commit()
        else:
            conn.rollback()
        # A fresh snapshot catches commits racing the attestation. Frozen V4
        # independently repeats this check in its own inference snapshot.
        scope, current, previous, _ = _snapshot(conn, tx)
        if (current['source_revision'] != revision or
                freshness(scope, current, previous) != 'COMPLETE_VERIFIED'):
            raise RuntimeError('History changed after attestation')
        return revision
    except Exception:
        conn.rollback()
        raise
    finally:
        if locked:
            conn.execute('SELECT RELEASE_LOCK(?)', (LOCK,))
        conn.close()
