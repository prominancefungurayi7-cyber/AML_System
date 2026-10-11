"""Customer transaction request identity; no model or payment side effects."""
from dataclasses import asdict
import re
import sqlite3
import uuid

from canonical_mobile_money import VERSION

INDEX = 'uq_transactions_sender_request'
KEY = 'client_request_id'


def request_id(form):
    values = form.getlist(KEY)
    if len(values) != 1:
        raise ValueError('Exactly one client request ID is required')
    value = values[0]
    if (not isinstance(value, str) or not re.fullmatch(
            r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}', value)):
        raise ValueError('A canonical UUIDv4 request ID is required')
    if str(uuid.UUID(value)) != value:
        raise ValueError('A canonical UUIDv4 request ID is required')
    return value


def require_schema(conn):
    """Fail closed if the atomic uniqueness gate is unavailable."""
    if conn.engine == 'mysql':
        columns = conn.execute("SHOW COLUMNS FROM transactions LIKE 'client_request_id'").fetchall()
        indexes = conn.execute("SHOW INDEX FROM transactions WHERE Key_name='uq_transactions_sender_request'").fetchall()
        ordered = [r['Column_name'] for r in sorted(indexes, key=lambda r: r['Seq_in_index'])]
        if (len(columns) != 1 or columns[0]['Type'].lower() != 'char(36)'
                or ordered != ['sender_account', KEY]
                or any(r['Non_unique'] != 0 for r in indexes)):
            raise RuntimeError('Customer request uniqueness schema unavailable')
    elif conn.engine == 'sqlite':
        columns = [r['name'] for r in conn.execute('PRAGMA table_info(transactions)').fetchall()]
        indexes = conn.execute('PRAGMA index_list(transactions)').fetchall()
        index = next((r for r in indexes if r['name'] == INDEX and r['unique']), None)
        ordered = ([r['name'] for r in conn.execute('PRAGMA index_info(' + INDEX + ')').fetchall()]
                   if index else [])
        if KEY not in columns or ordered != ['sender_account', KEY]:
            raise RuntimeError('Customer request uniqueness schema unavailable')
    elif conn.engine == 'postgres':
        row = conn.execute('SELECT indexdef FROM pg_indexes WHERE schemaname=current_schema() '
                           'AND tablename=? AND indexname=?', ('transactions', INDEX)).fetchone()
        if (not row or 'UNIQUE INDEX' not in row['indexdef'].upper()
                or '(sender_account, client_request_id)' not in row['indexdef']):
            raise RuntimeError('Customer request uniqueness schema unavailable')
    else:
        raise RuntimeError('Unsupported customer request uniqueness engine')


def submission(canonical_event, sender, tx_type, amount, recipient, agent_text):
    """Only fields that determine the committed payment; exclude server time/risk."""
    if canonical_event is not None:
        value = asdict(canonical_event)
        return {'kind': 'canonical', **{key: value[key] for key in value
                                       if key not in ('transaction_id', 'event_timestamp')}}
    agent = int(agent_text) if agent_text else None
    return {'kind': 'legacy', 'sender_account': sender,
            'receiver_account': recipient if tx_type == 'transfer' else sender,
            'amount': float(amount), 'transaction_type': tx_type,
            'currency': 'USD', 'channel': 'online', 'agent_id': agent}


def existing(conn, sender, key, wanted):
    row = conn.execute('SELECT * FROM transactions WHERE sender_account=? AND client_request_id=?',
                       (sender, key)).fetchone()
    if row is None:
        return None
    canonical = conn.execute('SELECT * FROM canonical_mobile_money_events WHERE transaction_id=?',
                             (row['id'],)).fetchone()
    if canonical is not None:
        from canonical_mobile_money import FIELDS
        actual = {'kind': 'canonical', **{name: canonical[name] for name in FIELDS
                                        if name not in ('transaction_id', 'event_timestamp')}}
        if canonical['canonical_version'] != VERSION:
            raise RuntimeError('Existing canonical transaction version mismatch')
    else:
        actual = {'kind': 'legacy', 'sender_account': row['sender_account'],
                  'receiver_account': row['receiver_account'], 'amount': float(row['amount']),
                  'transaction_type': row['transaction_type'], 'currency': row['currency'],
                  'channel': row['channel'], 'agent_id': row['agent_id']}
    if actual != wanted:
        raise ValueError('Request ID conflicts with a different transaction')
    return row['id']


def is_unique_conflict(exc):
    """Never reinterpret an unrelated integrity failure as an idempotent retry."""
    if isinstance(exc, sqlite3.IntegrityError):
        return ('UNIQUE constraint failed: transactions.sender_account, '
                'transactions.client_request_id') in str(exc)
    if getattr(exc, 'errno', None) == 1062:
        return INDEX in str(exc)
    if getattr(exc, 'pgcode', None) == '23505':
        return getattr(getattr(exc, 'diag', None), 'constraint_name', None) == INDEX
    return False


def is_retryable_lock(exc):
    if getattr(exc, 'errno', None) in (1205, 1213):
        return True
    if getattr(exc, 'pgcode', None) in ('40001', '40P01', '55P03'):
        return True
    return isinstance(exc, sqlite3.OperationalError) and 'locked' in str(exc).lower()
