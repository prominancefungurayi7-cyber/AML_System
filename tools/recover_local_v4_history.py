"""Guarded data-only restoration of the pinned LOCAL aml backup.

Default: read-only inspection. --apply requires the inspected state SHA and a
stopped application. It archives every current table before replacing the
generated ledger, its alerts/profiles/balances and source journal. No DDL,
foreign-key disabling, authority changes, or model changes are performed.
"""
import argparse
from collections import Counter
from datetime import date, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import socket
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BACKUP = ROOT / 'data/local-v4-backups/aml-pre-v4-20261011-221547.sql'
BACKUP_SHA = 'c50820b9582d9523e2f777c601b1ef268bcf5dc01083871fc0df01cd7dd59c7d'
IDENTITY = {'db': 'aml', 'principal': 'aml@127.0.0.1',
            'uuid': 'd441b7bb-43f6-11f1-a2d8-0a0027000005'}
REPLACE = ('transactions', 'alerts', 'behavioral_profiles', 'cmm_source_changes')
EMPTY = ('canonical_mobile_money_events', 'v4_shadow_results',
         'v4_primary_attempt_events', 'sar_reports', 'ctr_reports', 'cmm_entity_history')


def sql_values(text):
    """Parse literal-only single-row mysqldump VALUES; never execute dump SQL."""
    if not text.startswith('(') or not text.endswith(');'):
        raise ValueError('Expected a single literal INSERT row')
    end = len(text) - 2
    i, values = 1, []
    escapes = {'0': '\0', 'n': '\n', 'r': '\r', 'b': '\b', 't': '\t', 'Z': '\x1a',
               '\\': '\\', "'": "'", '"': '"'}
    while i < end:
        if text[i] == "'":
            i += 1
            chars = []
            while i < end:
                char = text[i]
                i += 1
                if char == '\\':
                    if i >= end or text[i] not in escapes:
                        raise ValueError('Unsupported SQL string escape')
                    chars.append(escapes[text[i]])
                    i += 1
                elif char == "'":
                    if i < end and text[i] == "'":
                        chars.append("'")
                        i += 1
                    else:
                        break
                else:
                    chars.append(char)
            else:
                raise ValueError('Unterminated SQL string')
            values.append(''.join(chars))
        else:
            start = i
            while i < end and text[i] != ',':
                i += 1
            token = text[start:i]
            if token == 'NULL':
                values.append(None)
            elif re.fullmatch(r'-?\d+', token):
                values.append(int(token))
            elif re.fullmatch(r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?', token):
                values.append(float(token))
            else:
                raise ValueError('Nonliteral SQL value')
        if i == end:
            break
        if text[i] != ',':
            raise ValueError('Unexpected SQL delimiter')
        i += 1
    return values


def read_backup():
    data = BACKUP.read_bytes()
    if hashlib.sha256(data).hexdigest() != BACKUP_SHA:
        raise RuntimeError('Verified backup hash changed')
    text = data.decode('utf-8')
    columns = {m[1]: re.findall(r'^  `([^`]+)`', m[2], re.M) for m in re.finditer(
        r'CREATE TABLE `([a-z_][a-z0-9_]*)` \((.*?)\) ENGINE=', text, re.S)}
    floating = {m[1]: set(re.findall(r'^  `([^`]+)` (?:double|float)\b', m[2], re.M))
                for m in re.finditer(
                    r'CREATE TABLE `([a-z_][a-z0-9_]*)` \((.*?)\) ENGINE=', text, re.S)}
    rows = {table: [] for table in columns}
    for line in text.splitlines():
        if line.startswith('INSERT INTO '):
            m = re.fullmatch(r'INSERT INTO `([a-z_][a-z0-9_]*)` VALUES (.*)', line)
            if not m or m[1] not in columns:
                raise RuntimeError('Unexpected backup INSERT format')
            values = sql_values(m[2])
            if len(values) != len(columns[m[1]]):
                raise RuntimeError('Backup column count mismatch')
            row = dict(zip(columns[m[1]], values))
            # mysqldump emits integral DOUBLE values as e.g. 60; the connector
            # reads the same stored value as 60.0. Match the declared SQL types.
            for name in floating[m[1]]:
                if row[name] is not None:
                    row[name] = float(row[name])
            rows[m[1]].append(row)
    if {t: len(rows[t]) for t in ('transactions', 'users', 'alerts')} != {
            'transactions': 7800, 'users': 18, 'alerts': 415}:
        raise RuntimeError('Backup protected counts changed')
    from canonical_history import verify, freshness, now
    scope = json.loads(rows['cmm_observation_scopes'][0]['body'])
    previous = json.loads(rows['cmm_history_attestations'][0]['body'])
    fields = ('id', 'timestamp', 'sender_account', 'receiver_account',
              'transaction_type', 'currency', 'agent_id')
    parents = [{k: row[k] for k in fields} for row in rows['transactions']]
    result = verify(scope, parents, rows['canonical_mobile_money_events'], now(),
                    previous, changes=rows['cmm_source_changes'])
    if result['issues'] or freshness(scope, result, previous) != 'COMPLETE_VERIFIED':
        raise RuntimeError('Backup does not satisfy the unchanged frozen history gate')
    return columns, rows


def json_default(value):
    if isinstance(value, Decimal):
        return {'$decimal': str(value)}
    if isinstance(value, (datetime, date)):
        return {'$datetime': value.isoformat()}
    if isinstance(value, bytes):
        return {'$bytes': value.hex()}
    raise TypeError(type(value).__name__)


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      default=json_default, allow_nan=False).encode()


def state(conn, lock=False):
    identity = dict(conn.execute('SELECT DATABASE() db,CURRENT_USER() principal,'
                                '@@server_uuid uuid').fetchone())
    if identity != IDENTITY:
        raise RuntimeError('Local database identity mismatch')
    from ml_v4.production_readiness import verify_triggers
    from transaction_idempotency import require_schema
    import v4_retry
    from v4_shadow import SHA
    model = ROOT / 'ml_v4/development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib'
    if hashlib.sha256(model.read_bytes()).hexdigest() != SHA:
        raise RuntimeError('Frozen model changed')
    pins = json.loads((ROOT / 'ml_v4/frozen_inference/history_authority.json').read_text())
    for path, sha in pins.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != sha:
            raise RuntimeError('Frozen history authority source changed')
    verify_triggers(conn)
    require_schema(conn)
    v4_retry.require_schema(conn)
    rows, schema = {}, {}
    for item in conn.execute('SHOW FULL TABLES WHERE Table_type = \'BASE TABLE\'').fetchall():
        table = next(iter(item.values()))
        if not re.fullmatch(r'[a-z_][a-z0-9_]*', table):
            raise RuntimeError('Unexpected table identifier')
        records = [dict(r) for r in conn.execute('SELECT * FROM `' + table + '`' +
                                               (' FOR UPDATE' if lock else '')).fetchall()]
        rows[table] = sorted(records, key=encode)
        ddl = conn.execute('SHOW CREATE TABLE `' + table + '`').fetchone()['Create Table']
        schema[table] = re.sub(r' AUTO_INCREMENT=\d+', '', ddl)
    triggers = [dict(r) for r in conn.execute('SELECT TRIGGER_NAME,DEFINER,ACTION_TIMING,'
        'EVENT_MANIPULATION,EVENT_OBJECT_TABLE,ACTION_STATEMENT FROM information_schema.TRIGGERS '
        'WHERE TRIGGER_SCHEMA=DATABASE() ORDER BY TRIGGER_NAME').fetchall()]
    return {'identity': identity, 'rows': rows, 'schema': schema, 'triggers': triggers}


def guard(current, backup):
    rows = current['rows']
    if {t: len(rows[t]) for t in ('transactions', 'users', 'alerts', 'cmm_source_changes')} != {
            'transactions': 6100, 'users': 18, 'alerts': 5816, 'cmm_source_changes': 13900}:
        raise RuntimeError('Current generated branch changed; inspect again')
    if any(rows[t] for t in EMPTY):
        raise RuntimeError('New financial, canonical or retry evidence prevents this restoration')
    for table in ('cmm_observation_scopes', 'cmm_history_attestations'):
        if rows[table] != sorted(backup[table], key=encode):
            raise RuntimeError('Original history authority or attestation changed')
    keys = ('id', 'username', 'role', 'account_number')
    identities = lambda source: sorted(tuple(row[k] for k in keys) for row in source['users'])
    if identities(rows) != identities(backup):
        raise RuntimeError('Wallet identity changed')
    # This exact incident contains only legacy synthetic, non-idempotent rows.
    if any(row['client_request_id'] is not None for row in rows['transactions']):
        raise RuntimeError('Customer payment exists; stop for a new recovery plan')
    if Counter(r['operation'] for r in rows['cmm_source_changes']) != {
            'SOURCE_DELETE': 7800, 'SOURCE_INSERT': 6100}:
        raise RuntimeError('Source journal changed')


def run(apply=False, expected_state=None):
    from dotenv import dotenv_values
    from database import connect_db
    from urllib.parse import urlsplit
    from canonical_history_store import assess
    from canonical_history import freshness
    columns, backup = read_backup()
    url = dotenv_values(ROOT / '.env')['DATABASE_URL']
    p = urlsplit(url)
    if (p.hostname, p.port, p.path) != ('127.0.0.1', 3306, '/aml'):
        raise RuntimeError('Unexpected local database endpoint')
    if apply:
        if not expected_state or not re.fullmatch('[0-9a-f]{64}', expected_state):
            raise RuntimeError('The reviewed current-state SHA is required')
        with socket.socket() as probe:
            probe.settimeout(1)
            if probe.connect_ex(('127.0.0.1', 5000)) == 0:
                raise RuntimeError('Stop the local Flask application before restoration')
    conn = connect_db(url)
    try:
        conn.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE' if apply else
                     'SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
        conn.execute('START TRANSACTION' if apply else
                     'START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY')
        before = state(conn, lock=apply)
        guard(before, backup)
        state_sha = hashlib.sha256(encode(before)).hexdigest()
        scope, current, previous = assess(conn, 'controlled-prototype-v1')
        report = {'identity': IDENTITY, 'backup_sha256': BACKUP_SHA,
                  'expected_state': state_sha, 'status': 'PREPARED_NOT_APPLIED',
                  'current_counts': {t: len(before['rows'][t]) for t in REPLACE},
                  'history': freshness(scope, current, previous),
                  'history_issues': dict(Counter(r['code'] for r in current['issues'])),
                  'backup_history': 'COMPLETE_VERIFIED',
                  'replacement': '7800 transactions, 415 alerts, original wallet balances/profiles/journal',
                  'schema_and_authority': 'PRESERVED'}
        if not apply:
            return report
        if state_sha != expected_state:
            raise RuntimeError('Current state differs from the reviewed recovery plan')
        archive = ROOT / ('data/local-v4-backups/pre-history-recovery-' + state_sha + '.json')
        payload = encode({'backup_sha256': BACKUP_SHA, 'state_sha256': state_sha, 'state': before})
        if not archive.exists():
            with archive.open('xb') as stream:
                stream.write(payload)
                stream.flush()
                import os
                os.fsync(stream.fileno())
        if archive.read_bytes() != payload:
            raise RuntimeError('Recovery archive failed verification')
        # All affected tables are InnoDB and locked; FK/capture triggers stay ON.
        if any('ENGINE=InnoDB' not in before['schema'][t] for t in (*REPLACE, 'users')):
            raise RuntimeError('Transactional recovery requires InnoDB')
        conn.execute('DELETE FROM alerts')
        conn.execute('DELETE FROM transactions')
        conn.execute('DELETE FROM behavioral_profiles')
        for table in ('transactions', 'alerts', 'behavioral_profiles'):
            names = columns[table]
            statement = ('INSERT INTO `' + table + '` (`' + '`,`'.join(names) + '`) VALUES (' +
                         ','.join('?' for _ in names) + ')')
            for row in backup[table]:
                conn.execute(statement, tuple(row[n] for n in names))
        for row in backup['users']:
            conn.execute('UPDATE users SET balance=? WHERE id=? AND account_number=?',
                         (row['balance'], row['id'], row['account_number']))
        # Restore the source journal to the same recovery point as the ledger.
        # The complete abandoned branch (including its journal) is archived above.
        conn.execute('DELETE FROM cmm_source_changes')
        if backup['cmm_source_changes']:
            raise RuntimeError('Unexpected nonempty baseline journal')
        after = state(conn)
        if after['schema'] != before['schema'] or after['triggers'] != before['triggers']:
            raise RuntimeError('Schema changed during recovery')
        for table, records in before['rows'].items():
            expected = backup[table] if table in REPLACE else records
            if table == 'transactions':
                expected = [{**r, 'client_request_id': None} for r in expected]
            if table == 'users':
                balances = {r['id']: r['balance'] for r in backup['users']}
                expected = [{**r, 'balance': balances[r['id']]} for r in records]
            if encode(sorted(expected, key=encode)) != encode(after['rows'][table]):
                raise RuntimeError('Exact restored/preserved row verification failed: ' + table)
        scope, result, previous = assess(conn, 'controlled-prototype-v1')
        if result['issues'] or freshness(scope, result, previous) != 'COMPLETE_VERIFIED':
            raise RuntimeError('Restored history failed the frozen gate; rolling back')
        conn.commit()
        report.update(status='RECOVERED', history='COMPLETE_VERIFIED',
                      before_counts=report['current_counts'],
                      current_counts={t: len(after['rows'][t]) for t in REPLACE},
                      history_issues={},
                      archive=str(archive), archive_sha256=hashlib.sha256(payload).hexdigest())
        return report
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.rollback()
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--expected-state')
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.apply, args.expected_state), indent=2))
    except Exception as exc:
        # Database errors can contain credentials or row values; never print them.
        print('Recovery stopped: ' + (str(exc) if type(exc) in (RuntimeError, ValueError)
                                     else type(exc).__name__), file=sys.stderr)
        sys.exit(1)
