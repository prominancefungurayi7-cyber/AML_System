"""Staff-controlled V4 error retry; original terminal result stays immutable."""
import hashlib
import json
import re
import threading
import uuid

from alerts import create_alert_if_needed
import v4_primary
import v4_shadow

TABLE = 'v4_primary_attempt_events'
_sqlite_locks = {}
_sqlite_guard = threading.Lock()


class RetryConflict(ValueError):
    pass


def _key(value):
    if not isinstance(value, str) or not re.fullmatch(
            r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}', value):
        raise ValueError('Canonical UUIDv4 action key required')
    if str(uuid.UUID(value)) != value:
        raise ValueError('Canonical UUIDv4 action key required')
    return value


def require_schema(conn):
    if conn.engine == 'mysql':
        columns = [row['Field'] for row in conn.execute('SHOW COLUMNS FROM ' + TABLE).fetchall()]
        triggers = {row['TRIGGER_NAME']: row for row in conn.execute(
            'SELECT TRIGGER_NAME,ACTION_TIMING,EVENT_MANIPULATION,ACTION_STATEMENT '
            'FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() '
            'AND EVENT_OBJECT_TABLE=?', (TABLE,)).fetchall()}
        if set(triggers) != {'v4_retry_no_update', 'v4_retry_no_delete'}:
            raise RuntimeError('Append-only retry triggers unavailable')
        for name, operation in (('v4_retry_no_update', 'UPDATE'),
                                ('v4_retry_no_delete', 'DELETE')):
            item = triggers[name]
            if (item['ACTION_TIMING'], item['EVENT_MANIPULATION']) != ('BEFORE', operation) or \
                    "SIGNAL SQLSTATE '45000'" not in item['ACTION_STATEMENT'].upper():
                raise RuntimeError('Append-only retry trigger changed')
        indexes = conn.execute('SHOW INDEX FROM ' + TABLE + ' WHERE Key_name=?',
                               ('uq_v4_attempt_event',)).fetchall()
        ordered = [row['Column_name'] for row in sorted(indexes, key=lambda r: r['Seq_in_index'])]
        if ordered != ['transaction_id', 'request_key', 'event_kind'] or any(
                row['Non_unique'] != 0 for row in indexes):
            raise RuntimeError('Retry idempotency index unavailable')
    elif conn.engine == 'sqlite':
        columns = [row['name'] for row in conn.execute('PRAGMA table_info(' + TABLE + ')').fetchall()]
        triggers = {row['name'] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name=?",
            (TABLE,)).fetchall()}
        if triggers != {'v4_retry_no_update', 'v4_retry_no_delete'}:
            raise RuntimeError('Append-only retry triggers unavailable')
    else:
        raise RuntimeError('Unsupported retry database')
    if columns != ['event_id', 'transaction_id', 'staff_user_id', 'request_key',
                   'event_kind', 'recorded_at', 'outcome', 'error_code',
                   'result_body', 'reason']:
        raise RuntimeError('V4 retry audit schema unavailable')


def _lock(conn, tx):
    if conn.engine == 'mysql':
        if conn.execute('SELECT GET_LOCK(?,0) AS ok', ('v4_primary_retry_' + str(tx),)).fetchone()['ok'] != 1:
            raise RetryConflict('Another staff action is in progress')
        return None
    with _sqlite_guard:
        lock = _sqlite_locks.setdefault(tx, threading.Lock())
    if not lock.acquire(False):
        raise RetryConflict('Another staff action is in progress')
    return lock


def _unlock(conn, tx, lock):
    if conn.engine == 'mysql':
        conn.execute('SELECT RELEASE_LOCK(?)', ('v4_primary_retry_' + str(tx),))
    elif lock is not None:
        lock.release()


def _staff_and_source(conn, tx, staff_id):
    require_schema(conn)
    staff = conn.execute('SELECT id,role FROM users WHERE id=?', (staff_id,)).fetchone()
    if staff is None or staff['role'] not in ('compliance', 'admin'):
        raise PermissionError('Current compliance or admin role required')
    row = conn.execute('SELECT sender_account,timestamp,rule_score,rules_triggered,'
                       'sar_required,ai_risk_level FROM transactions WHERE id=?', (tx,)).fetchone()
    canonical = conn.execute('SELECT * FROM canonical_mobile_money_events WHERE transaction_id=?',
                             (tx,)).fetchone()
    original = v4_shadow.get(conn, tx)
    if row is None or canonical is None or original is None or \
            v4_shadow.validate(original, tx)['status'] != 'inference_error':
        raise RetryConflict('Original committed V4 error unavailable')
    return row, canonical


def _events(conn, tx):
    return [dict(row) for row in conn.execute(
        'SELECT request_key,event_kind,outcome,error_code,result_body,reason FROM ' + TABLE +
        ' WHERE transaction_id=? ORDER BY event_id', (tx,)).fetchall()]


def _guard_action(events, key, kind):
    same = [row for row in events if row['request_key'] == key]
    if same:
        if kind == 'retry' and same[0]['event_kind'] == 'STARTED':
            return {'status': same[-1]['outcome'] or 'started', 'duplicate': True}
        if kind == 'close' and same[0]['event_kind'] == 'CLOSED':
            return {'status': 'closed', 'duplicate': True}
        raise RetryConflict('Action key reused for a different action')
    if any(row['event_kind'] == 'CLOSED' for row in events):
        raise RetryConflict('V4 error case already closed')
    started = {row['request_key'] for row in events if row['event_kind'] == 'STARTED'}
    completed = {row['request_key'] for row in events if row['event_kind'] == 'COMPLETED'}
    if started - completed and kind == 'retry':
        raise RetryConflict('Earlier attempt lacks a completion record')
    return None


def _insert(conn, tx, staff_id, key, kind, outcome, *, error_code=None, body=None, reason=None):
    conn.execute('INSERT INTO ' + TABLE + ' (transaction_id,staff_user_id,request_key,'
                 'event_kind,recorded_at,outcome,error_code,result_body,reason) '
                 'VALUES (?,?,?,?,?,?,?,?,?)',
                 (tx, staff_id, key, kind, v4_shadow.now(), outcome, error_code,
                  json.dumps(body, sort_keys=True, allow_nan=False) if body else None, reason))


def retry(connection_factory, tx, staff_id, request_key, *, runner=None,
          validator=None, notify=None):
    if type(tx) is not int or tx <= 0 or type(staff_id) is not int or staff_id <= 0:
        raise ValueError('Invalid transaction or staff ID')
    key = _key(request_key)
    if v4_shadow.enabled():
        raise RuntimeError('Primary retry requires V4 shadow OFF')
    conn = connection_factory()
    lock = None
    try:
        lock = _lock(conn, tx)
        row, canonical = _staff_and_source(conn, tx, staff_id)
        duplicate = _guard_action(_events(conn, tx), key, 'retry')
        if duplicate:
            return duplicate
        if row['ai_risk_level'] != 'inference_error':
            raise RetryConflict('Effective decision is no longer unresolved')
        _insert(conn, tx, staff_id, key, 'STARTED', 'started')
        conn.commit()
        digest = hashlib.sha256(json.dumps(dict(canonical), sort_keys=True,
                                           separators=(',', ':')).encode()).hexdigest()
        server_uuid = conn.execute('SELECT @@server_uuid AS id').fetchone()['id'] if conn.engine == 'mysql' else 'offline-test'
        try:
            expected_revision = None
            if runner is None:
                from v4_history_attestation import refresh_committed
                expected_revision = refresh_committed(connection_factory, tx)
            raw = (runner or v4_shadow.invoke)(tx, digest, server_uuid)
            result = (validator or v4_shadow.validate)(raw, tx)
            if (expected_revision is not None and result['status'] == 'success' and
                    result.get('source_revision') != expected_revision):
                result = v4_shadow.error(tx, 'HISTORY_INCOMPLETE')
        except Exception:
            result = v4_shadow.error(tx, 'INFERENCE_ERROR')
        result = (validator or v4_shadow.validate)(result, tx)
        alert_id = None
        if result['status'] == 'success':
            decision = v4_primary._decision(result, int(row['rule_score'] or 0), row['sar_required'])
            updated = conn.execute(
                'UPDATE transactions SET risk_score=?,risk_level=?,ai_risk_level=?,'
                'ai_confidence=?,ai_reason=?,description=?,sar_required=? '
                "WHERE id=? AND ai_risk_level='inference_error'",
                (decision['risk_score'], decision['risk_level'], decision['ai_risk_level'],
                 decision['ai_confidence'], decision['ai_reason'], decision['description'],
                 decision['sar_required'], tx))
            if updated.rowcount != 1:
                raise RetryConflict('Effective V4 decision changed concurrently')
            alert_id = create_alert_if_needed(
                conn, tx, row['sender_account'], decision['risk_score'],
                decision['risk_level'], decision['ai_reason'],
                row['rules_triggered'] or '[]', row['timestamp'], database_url=conn.engine + '://')
        _insert(conn, tx, staff_id, key, 'COMPLETED', result['status'],
                error_code=result.get('error_code'), body=result)
        conn.commit()
        output = {'status': result['status'], 'transaction_id': tx,
                  'request_key': key, 'decision': result['decision'], 'alert_id': alert_id,
                  'error_code': result.get('error_code'), 'duplicate': False}
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            if lock is not None or conn.engine == 'mysql':
                _unlock(conn, tx, lock)
        finally:
            conn.close()
    if notify is not None:
        try:
            notify(output)
        except Exception:
            pass
    return output


def close(connection_factory, tx, staff_id, request_key, reason):
    if type(tx) is not int or tx <= 0 or type(staff_id) is not int or staff_id <= 0:
        raise ValueError('Invalid transaction or staff ID')
    key = _key(request_key)
    if v4_shadow.enabled():
        raise RuntimeError('Primary closure requires V4 shadow OFF')
    if not isinstance(reason, str) or not 10 <= len(reason.strip()) <= 500:
        raise ValueError('A 10–500 character closure reason is required')
    conn = connection_factory()
    lock = None
    try:
        lock = _lock(conn, tx)
        row, _canonical = _staff_and_source(conn, tx, staff_id)
        duplicate = _guard_action(_events(conn, tx), key, 'close')
        if duplicate:
            return duplicate
        if row['ai_risk_level'] != 'inference_error':
            raise RetryConflict('Effective decision is no longer unresolved')
        _insert(conn, tx, staff_id, key, 'CLOSED', 'closed', reason=reason.strip())
        conn.commit()
        return {'status': 'closed', 'transaction_id': tx, 'request_key': key,
                'duplicate': False}
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            if lock is not None or conn.engine == 'mysql':
                _unlock(conn, tx, lock)
        finally:
            conn.close()
