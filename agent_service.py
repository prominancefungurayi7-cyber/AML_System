"""Agent cash services through canonical, idempotent payment processing."""
from datetime import datetime, timezone
from decimal import Decimal
from canonical_mobile_money import VERSION, prepare_ingestion, with_id, LEGACY_TYPES
from canonical_mobile_money_store import persist
from transaction_idempotency import require_schema, existing, submission
from v4_simulation import payment_lock


def linked_agent(conn, user):
    if not user or user['role'] != 'agent':
        raise ValueError('Agent access required.')
    agent = conn.execute("SELECT * FROM agents WHERE agent_code=? AND status='active'",
                         (user['account_number'],)).fetchone()
    if not agent:
        raise ValueError('Active service-agent record unavailable.')
    return agent


def cash_agent_wallet(conn, agent_id):
    """Resolve a funded service principal; never use a customer as an agent."""
    suffix = ' FOR UPDATE' if conn.engine == 'mysql' else ''
    row = conn.execute(
        "SELECT u.* FROM agents a JOIN users u ON u.account_number=a.agent_code "
        "WHERE a.id=? AND a.status='active' AND u.role='agent'" + suffix,
        (agent_id,)).fetchone()
    if not row:
        raise ValueError('This agent has no active electronic-float wallet. Select an active agent.')
    return row


def transfer_cash_value(conn, customer_id, agent_user_id, kind, value):
    """Move electronic value atomically; caller owns commit/rollback."""
    if kind not in ('cash_in', 'cash_out') or customer_id == agent_user_id:
        raise ValueError('Invalid cash service participants.')
    payer, payee = ((agent_user_id, customer_id) if kind == 'cash_in'
                    else (customer_id, agent_user_id))
    debit = conn.execute('UPDATE users SET balance=balance-? WHERE id=? AND balance>=?',
                         (float(value), payer, float(value)))
    if debit.rowcount != 1:
        raise ValueError('Insufficient agent electronic float. Fund the agent wallet before cash-in.'
                         if kind == 'cash_in' else 'Insufficient customer balance for cash-out.')
    credit = conn.execute('UPDATE users SET balance=balance+? WHERE id=?', (float(value), payee))
    if credit.rowcount != 1:
        raise ValueError('Cash service wallet unavailable.')


def commit_service(conn, user_id, customer_account, kind, amount, key, process, last_id):
    """Transfer electronic value between agent float and customer; commit once.

    Physical cash is exchanged by the operator. No electronic funds are created.
    Caller closes this connection before queuing nonfinancial V4 review.
    """
    payment_lock(conn)
    require_schema(conn)
    suffix = ' FOR UPDATE' if conn.engine == 'mysql' else ''
    user = conn.execute('SELECT * FROM users WHERE id=?' + suffix, (user_id,)).fetchone()
    agent = linked_agent(conn, user)
    customer = conn.execute("SELECT * FROM users WHERE account_number=? AND role='customer'" + suffix,
                            (customer_account,)).fetchone()
    if not customer or kind not in ('cash_in', 'cash_out'):
        raise ValueError('Choose an existing customer wallet and a cash service.')
    event = prepare_ingestion(dict(canonical_version=VERSION, type=kind, amount=amount,
        currency='USD', channel='agent', agent_id=str(agent['id']), serviced_wallet=customer_account,
        agent_flow_direction=kind, recipient=''), customer_account, datetime.now(timezone.utc).isoformat())
    prior = existing(conn, customer_account, key, submission(event, None, None, None, None, None))
    if prior is not None:
        return prior, True
    value = Decimal(event.amount_minor) / 100
    payer, payee = (user, customer) if kind == 'cash_in' else (customer, user)
    if Decimal(str(payer['balance'])) < value:
        raise ValueError('Insufficient agent electronic float.' if kind == 'cash_in' else 'Insufficient customer balance.')
    legacy = LEGACY_TYPES[kind]
    conn.execute('INSERT INTO transactions (sender_account,receiver_account,amount,transaction_type,'
        'currency,channel,timestamp,status,risk_score,risk_level,description,agent_id,client_request_id) '
        'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', (customer_account,customer_account,float(value),legacy,
        'USD','agent',event.event_timestamp,'Completed',0,'pending_review','Agent cash service',agent['id'],key))
    tx = last_id(conn)
    persist(conn, with_id(event, tx))
    process(conn,tx,customer_account,customer_account,float(value),legacy,event.event_timestamp,
            account_number=customer_account,emit_events=False)
    transfer_cash_value(conn, customer['id'], user['id'], kind, value)
    conn.commit()
    return tx, False
