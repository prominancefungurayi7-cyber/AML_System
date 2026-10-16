"""Read-only production V4 prerequisites; never starts Flask or inference."""
import hashlib
import json
import os
from pathlib import Path
import re

from canonical_history import freshness
from canonical_history_journal import triggers
from canonical_history_store import assess
from database import DatabaseAdapter
from transaction_idempotency import require_schema
import v4_retry

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'ml_v4/development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib'
MODEL_SHA = '555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18'
SERVER_SHA = '5139ad7832a0702b019b6b92907edef81e3a3a1d0624373a77e38284be9b39cb'
REALTIME_SHA = 'aecf8a2a75d1f7af48b581732b62841d8d5f4f3807614fff07c35529b9be1bfd'
SCOPE = 'controlled-prototype-v1'


def binding():
    required = ('V4_READINESS_HOST', 'V4_READINESS_USER', 'V4_READINESS_PASSWORD',
                'V4_READINESS_UUID', 'V4_READINESS_PRINCIPAL')
    if any(not os.environ.get(key) for key in required):
        raise RuntimeError('Explicit production read-only binding required')
    if any(os.environ.get(key) for key in ('DATABASE_URL', 'MYSQL_URL', 'V4_STAGE4T_TEST_DB_URL')):
        raise RuntimeError('Conflicting database URL present')
    if not re.fullmatch(r'[0-9a-f-]{36}', os.environ['V4_READINESS_UUID']):
        raise RuntimeError('Expected server UUID required')
    if not re.fullmatch(r'[A-Za-z0-9_]+@[A-Za-z0-9_.%:-]+',
                        os.environ['V4_READINESS_PRINCIPAL']):
        raise RuntimeError('Expected principal required')
    return {key: os.environ[key] for key in required}


def verify_identity(conn, expected):
    row = conn.execute('SELECT DATABASE() AS db, @@server_uuid AS server_uuid, '
                       'CURRENT_USER() AS principal').fetchone()
    if (row['db'] != 'aml' or row['server_uuid'] != expected['V4_READINESS_UUID'] or
            row['principal'] != expected['V4_READINESS_PRINCIPAL']):
        raise RuntimeError('Production identity mismatch')
    grants = [next(iter(row.values())) for row in conn.execute('SHOW GRANTS').fetchall()]
    operations = set()
    for grant in grants:
        normalized = grant.replace('`', '').replace('"', '')
        match = re.search(r'\bGRANT (.+?) ON (\S+) TO ', normalized, re.I)
        if not match or ' WITH GRANT OPTION' in normalized.upper():
            raise RuntimeError('Runtime grant unavailable or excessive')
        privilege_list, target = match.groups()
        if target == '*.*':
            if privilege_list.upper() != 'USAGE':
                raise RuntimeError('Global runtime grant forbidden')
        elif target == 'aml.*':
            operations.update(piece.strip().upper() for piece in privilege_list.split(','))
        else:
            raise RuntimeError('Runtime grant outside aml')
    # MySQL reports schema-scoped ALL as one token, not expanded privileges.
    # Global ALL and grants outside aml have already been rejected above.
    if 'ALL PRIVILEGES' not in operations and not {'SELECT', 'INSERT', 'UPDATE'}.issubset(operations):
        raise RuntimeError('Required aml runtime grants unavailable')
    return row


def verify_triggers(conn):
    actual = conn.execute('SELECT TRIGGER_NAME,EVENT_OBJECT_TABLE,EVENT_MANIPULATION,'
                          'ACTION_TIMING,ACTION_STATEMENT FROM information_schema.TRIGGERS '
                          'WHERE TRIGGER_SCHEMA=DATABASE()').fetchall()
    actual = {row['TRIGGER_NAME']: row for row in actual
              if row['TRIGGER_NAME'].lower().startswith('cmm_')}
    expected = triggers('mysql')
    if set(actual) != set(expected):
        raise RuntimeError('Capture trigger set mismatch')
    for name, (table, operation, body) in expected.items():
        row = actual[name]
        if (row['EVENT_OBJECT_TABLE'], row['EVENT_MANIPULATION'],
                row['ACTION_TIMING'], row['ACTION_STATEMENT']) != (table, operation, 'AFTER', body):
            raise RuntimeError('Capture trigger mismatch')
    return len(actual)


def verify_history(conn):
    from ml_v4.frozen_inference.service import verified_bytes
    pins = json.loads((ROOT / 'ml_v4/frozen_inference/history_authority.json').read_text())
    for path, sha in pins.items():
        verified_bytes({'path': path, 'sha256': sha})
    scope, current, previous = assess(conn, SCOPE)
    boundary = json.loads((ROOT / 'ml_v4/evidence/integration_stage2a2/'
                           'observation_boundary.json').read_text())
    keys = ('scope_id', 'scope_version', 'start_timestamp',
            'start_transaction_id_exclusive', 'source_ledger',
            'canonical_version', 'preexisting_parent_ids', 'preexisting_change_ids')
    if any(scope[key] != boundary[key] for key in keys):
        raise RuntimeError('Production observation boundary mismatch')
    if current['status'] != 'COMPLETE_VERIFIED' or current['issues'] or \
            freshness(scope, current, previous) != 'COMPLETE_VERIFIED':
        raise RuntimeError('Production history is not complete and fresh')
    return {'scope': SCOPE, 'canonical_events': len(current['canonical_event_ids']),
            'source_revision': current['source_revision'],
            'attestation_sequence': previous['sequence'], 'freshness': 'COMPLETE_VERIFIED'}


def run():
    expected = binding()
    origins = os.environ.get('SOCKETIO_ALLOWED_ORIGINS', '')
    if not origins or any(not re.fullmatch(r'https://[A-Za-z0-9.-]+(?::[0-9]{1,5})?', item.strip())
                          for item in origins.split(',')):
        raise RuntimeError('Explicit HTTPS Socket.IO origins required')
    if hashlib.sha256(MODEL.read_bytes()).hexdigest() != MODEL_SHA:
        raise RuntimeError('Frozen model hash mismatch')
    if (hashlib.sha256((ROOT / 'server.py').read_bytes()).hexdigest() != SERVER_SHA or
            hashlib.sha256((ROOT / 'realtime.py').read_bytes()).hexdigest() != REALTIME_SHA):
        raise RuntimeError('Application Socket.IO security source changed')
    if os.environ.get('AML_PRIMARY_MODEL') == 'V4':
        raise RuntimeError('Run readiness before production activation')
    if os.environ.get('AML_RULE_ENGINE_ENABLED') not in ('ON', 'OFF'):
        raise RuntimeError('Explicit AML rule policy required')
    import mysql.connector
    raw = mysql.connector.connect(host=expected['V4_READINESS_HOST'], port=3306,
                                  user=expected['V4_READINESS_USER'],
                                  password=expected['V4_READINESS_PASSWORD'],
                                  database='aml', connection_timeout=5,
                                  charset='utf8mb4')
    conn = DatabaseAdapter(raw, 'mysql')
    try:
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
        conn.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY')
        identity = verify_identity(conn, expected)
        require_schema(conn)
        v4_retry.require_schema(conn)
        trigger_count = verify_triggers(conn)
        history = verify_history(conn)
        return {'status': 'READ_ONLY_PASS', 'identity': identity,
                'idempotency_schema': 'verified', 'retry_audit_schema': 'verified',
                'capture_triggers': trigger_count,
                'history': history, 'model_sha256': MODEL_SHA,
                'rule_engine_policy': os.environ['AML_RULE_ENGINE_ENABLED'],
                'socket_origins': origins.split(',')}
    finally:
        conn.rollback()
        conn.close()


if __name__ == '__main__':
    try:
        print(json.dumps(run(), sort_keys=True))
    except Exception as exc:
        print('Production read-only readiness stopped: ' + type(exc).__name__)
        raise SystemExit(1)
