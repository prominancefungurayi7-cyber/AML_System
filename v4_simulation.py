"""Prospective demo payments through the existing V4 pipeline; no schema changes."""
from datetime import datetime, timezone
from decimal import Decimal
import random
import uuid

from itsdangerous import URLSafeTimedSerializer, BadData

from canonical_mobile_money import VERSION, LEGACY_TYPES, prepare_ingestion, with_id
from canonical_mobile_money_store import persist
from transaction_idempotency import require_schema, existing, submission

COUNTS = (1, 10, 100, 500, 1000, 2000, 5000)
MODES = ('mixed', 'ordinary', 'structuring', 'network', 'agent')
PAYMENT_LOCK = 'aml_v4_payment_ingest_v1'
# Existing seeded demonstration identities only. Newly registered customers are
# never enrolled in simulation by their role alone.
DEMO_WALLETS = {
    'demo': 'ACC1003', 'user_low_1': 'ACC1000', 'user_low_5': 'ACC1004',
    **{f'user_average_{i}': f'ACC{1004+i}' for i in range(1, 6)},
    **{f'user_high_{i}': f'ACC{1009+i}' for i in range(1, 4)},
    **{f'user_ultra_high_{i}': f'ACC{1012+i}' for i in range(1, 3)},
}


def payment_lock(conn):
    """Serialize prospective timestamps with customer payments, until close."""
    if conn.engine == 'mysql':
        if conn.execute('SELECT GET_LOCK(?,5) AS acquired', (PAYMENT_LOCK,)).fetchone()['acquired'] != 1:
            raise RuntimeError('Transaction service busy. Retry the same request.')
        # Discard an earlier authentication/read snapshot after waiting for the lock.
        conn.rollback()


def serializer(secret):
    return URLSafeTimedSerializer(secret, salt='v4-demo-generation-v1')


def options(conn, secret, admin_id):
    funded_wallets = [dict(row) for row in conn.execute(
        "SELECT id,username,account_number,balance FROM users WHERE role='customer' ORDER BY id").fetchall()
        if DEMO_WALLETS.get(row['username']) == row['account_number']]
    wallets = [{k: row[k] for k in ('id', 'username', 'account_number')} for row in funded_wallets]
    scenario_ids = scenario_wallet_order(funded_wallets)
    agents = [str(row['id']) for row in conn.execute(
        "SELECT id FROM agents WHERE status='active' ORDER BY id").fetchall()]
    choices = []
    if len(wallets) >= 6:
        for mode in MODES:
            if mode == 'agent' and not agents:
                continue
            for count in COUNTS:
                ticket = dict(version=2, batch_id=str(uuid.uuid4()), admin_id=admin_id,
                              count=count, mode=mode, wallets=wallets, agents=agents,
                              scenario_wallet_ids=scenario_ids)
                choices.append(dict(count=count, mode=mode, token=serializer(secret).dumps(ticket)))
    return dict(choices=choices, wallet_count=len(wallets), agent_count=len(agents))


def scenario_wallet_order(wallets):
    """Snapshot funded scenario roles in the signed request, never on a retry.

    Routine wallets retain their fixed roles. The largest scenario wallet funds
    split payments; the next two fund the network episode. Smaller wallets are
    recipients. No wallet is credited merely to make a simulation succeed.
    """
    cut = max(2, (len(wallets) // 2) // 2 * 2)
    pool = sorted(wallets[cut:], key=lambda w: (Decimal(str(w['balance'])), w['id']))
    if len(pool) >= 6:
        split = len(pool) - 4
        pool = [pool[-1], *pool[:split - 1], *reversed(pool[split - 1:-1])]
    return [w['id'] for w in pool]


def decode(token, secret, admin_id):
    try:
        ticket = serializer(secret).loads(token, max_age=86400)
        if (ticket['version'] not in (1, 2) or ticket['admin_id'] != admin_id or
                ticket['count'] not in COUNTS or ticket['mode'] not in MODES or
                str(uuid.UUID(ticket['batch_id'], version=4)) != ticket['batch_id']):
            raise ValueError('Invalid generation request')
        return ticket
    except (BadData, KeyError, TypeError, ValueError) as exc:
        raise ValueError('Generation form expired or changed. Reload the dashboard.') from exc


def _plan_v1(ticket):
    """Deterministic observable inputs. Scenario names never supply AI labels."""
    wallets, agents = ticket['wallets'], ticket['agents']
    if len(wallets) < 6 or (ticket['mode'] == 'agent' and not agents):
        raise ValueError('This scenario requires six demo wallets and, for agent activity, an active agent.')
    rng = random.Random(ticket['batch_id'])
    # Keep routine counterparties separate from the scenario graph.
    cut = max(2, (len(wallets) // 2) // 2 * 2)
    ordinary, scenario = wallets[:cut], wallets[cut:]
    families = ['structuring', 'network'] + (['agent'] if agents else [])
    count = ticket['count']
    ordinary_count = max(1, count * 70 // 100)
    rows = []
    for i in range(count):
        family = ticket['mode']
        if family == 'mixed':
            family = 'ordinary' if i < ordinary_count else families[(i - ordinary_count) // 6 % len(families)]
        pool = ordinary if family == 'ordinary' else scenario
        sender = pool[i % len(pool)]
        recipient = pool[(i % len(pool)) ^ 1] if family == 'ordinary' else pool[(i+1) % len(pool)]
        kind, agent = 'wallet_to_wallet', ''
        if family == 'ordinary':
            amount = rng.randint(100, 7500)
            # Cash pairs use the same wallet and equal values: no artificial
            # funding is introduced to make an otherwise insolvent batch pass.
            if agents and i % 10 in (8, 9):
                sender = ordinary[0]
                kind = 'cash_in' if i % 10 == 8 else 'cash_out'
                amount, agent = 2500, agents[0]
        elif family == 'structuring':
            amount = 950000
        elif family == 'network':
            amount = 150000
        else:
            sender = pool[(i // 2) % len(pool)]
            kind = 'cash_in' if i % 2 == 0 else 'cash_out'
            amount, agent = 250000, agents[0]
        form = dict(canonical_version=VERSION, type=kind,
                    amount=f'{Decimal(amount) / 100:.2f}', currency='USD',
                    channel='agent' if agent else 'direct_wallet', agent_id=agent,
                    serviced_wallet=sender['account_number'] if agent else '',
                    agent_flow_direction=kind if agent else 'none',
                    recipient=recipient['account_number'] if kind == 'wallet_to_wallet' else '')
        key = ticket['batch_id'] if i == 0 else str(uuid.uuid5(uuid.UUID(ticket['batch_id']), str(i)))
        rows.append((sender, recipient, form, key))
    return rows


def scenario_schedule(ticket):
    """Input intentions only, never predictions or AML alert classifications."""
    count, mode = ticket['count'], ticket['mode']
    if mode != 'mixed':
        return [mode] * count
    families = ['structuring', 'network'] + (['agent'] if ticket['agents'] else [])
    if ticket['version'] == 1:
        ordinary = max(1, count * 70 // 100)
        return ['ordinary'] * ordinary + [families[i // 6 % len(families)] for i in range(count - ordinary)]
    # Seven routine payments followed by one three-payment scenario episode.
    # Rounding favours routine inputs for small batches, including count=1.
    ordinary = (count * 7 + 9) // 10
    schedule = []
    risk_left, episode = count - ordinary, 0
    while ordinary or risk_left:
        take = min(7, ordinary)
        schedule.extend(['ordinary'] * take)
        ordinary -= take
        take = min(3, risk_left)
        schedule.extend([families[episode % len(families)]] * take)
        risk_left -= take
        episode += 1
    return schedule


def input_mix(ticket):
    schedule = scenario_schedule(ticket)
    counts = {mode: schedule.count(mode) for mode in MODES if mode != 'mixed'}
    return dict(plan_version=ticket['version'], ordinary_inputs=counts['ordinary'],
                suspicious_inputs=len(schedule) - counts['ordinary'], scenario_counts=counts)


def plan(ticket):
    # A signed ticket is also a payment identity: retain the original planner
    # byte-for-byte for old receipts/retries, including committed v1 batches.
    if ticket['version'] == 1:
        return _plan_v1(ticket)
    if ticket['version'] != 2:
        raise ValueError('Unknown generation plan version')
    wallets, agents = ticket['wallets'], ticket['agents']
    if len(wallets) < 6 or (ticket['mode'] == 'agent' and not agents):
        raise ValueError('This scenario requires six demo wallets and, for agent activity, an active agent.')
    rng = random.Random(ticket['batch_id'])
    cut = max(2, (len(wallets) // 2) // 2 * 2)
    ordinary, scenario = wallets[:cut], wallets[cut:]
    # Roles stay fixed across batches and modes. Routine payees never return
    # funds to routine senders; suspicious activity cannot use routine wallets.
    funded_profile = 'scenario_wallet_ids' in ticket
    if funded_profile:
        by_id = {w['id']: w for w in scenario}
        ids = ticket['scenario_wallet_ids']
        if len(ids) != len(by_id) or set(ids) != set(by_id):
            raise ValueError('Invalid scenario wallet selection')
        scenario = [by_id[wallet_id] for wallet_id in ids]
    split = len(scenario) - 4 if len(scenario) >= 6 else 0
    structuring = scenario[:split] if split else scenario[:2]
    network = scenario[split:] if split else scenario
    positions = {name: 0 for name in MODES}
    network_amounts = None
    cash_amount = None
    split_amount = None
    rows = []
    for i, family in enumerate(scenario_schedule(ticket)):
        j = positions[family]
        positions[family] += 1
        kind, agent = 'wallet_to_wallet', ''
        if family == 'ordinary':
            # Keep complete former reciprocal pairs on one side of the new
            # payer/payee boundary. Old pair history is preserved, but new
            # routine payments do not close those existing feedback paths.
            payer_count = max(1, len(ordinary) - 2)
            sender = ordinary[j % payer_count]
            recipient = ordinary[payer_count + j % (len(ordinary) - payer_count)]
            amount = max(100, min(25000, round(rng.lognormvariate(3.55, .8) * 100)))
        elif family == 'structuring':
            sender, recipient = structuring[0], structuring[1 + j % (len(structuring) - 1)]
            if funded_profile and ticket['mode'] == 'mixed' and (j // 3) % 5:
                # Repeated small splits are a different observable pattern
                # from near-threshold transfers. Keep each episode's amount
                # stable; neither episode type supplies a model label.
                if j % 3 == 0:
                    split_amount = rng.randint(7500, 25000)
                amount = split_amount
            else:
                amount = rng.randint(850000, 990000)
        elif family == 'network':
            # Converging funds followed by rapid onward transfer, without the
            # unbounded repeated rings that previously dominated every mode.
            if len(network) >= 4:
                step = j % 3
                if step == 0:
                    network_amounts = (rng.randint(80000, 180000), rng.randint(80000, 180000))
                sender = network[step]
                recipient = network[2] if step < 2 else network[3]
                amount = network_amounts[step] if step < 2 else sum(network_amounts) * 98 // 100
            else:
                step = j % 2
                if step == 0:
                    network_amounts = (rng.randint(120000, 280000),)
                sender, recipient = network[step:step + 2]
                amount = network_amounts[0] if step == 0 else network_amounts[0] * 98 // 100
        else:
            sender = scenario[(j // 2) % len(scenario)]
            recipient = sender
            kind = 'cash_in' if j % 2 == 0 else 'cash_out'
            if j % 2 == 0:
                cash_amount = rng.randint(150000, 290000)
            amount, agent = cash_amount, agents[(j // 2) % len(agents)]
        form = dict(canonical_version=VERSION, type=kind,
                    amount=f'{Decimal(amount) / 100:.2f}', currency='USD',
                    channel='agent' if agent else 'direct_wallet', agent_id=agent,
                    serviced_wallet=sender['account_number'] if agent else '',
                    agent_flow_direction=kind if agent else 'none',
                    recipient=recipient['account_number'] if kind == 'wallet_to_wallet' else '')
        key = ticket['batch_id'] if i == 0 else str(uuid.uuid5(uuid.UUID(ticket['batch_id']), str(i)))
        rows.append((sender, recipient, form, key))
    return rows


def receipt(conn, ticket):
    """Read a batch by immutable request keys, including after a browser retry."""
    rows = []
    planned = plan(ticket)
    accounts = sorted({sender['account_number'] for sender, _, _, _ in planned})
    for offset in range(0, len(planned), 250):
        keys = [row[3] for row in planned[offset:offset+250]]
        rows.extend(dict(row) for row in conn.execute(
            'SELECT id,ai_risk_level FROM transactions WHERE sender_account IN (' +
            ','.join('?' for _ in accounts) + ') AND client_request_id IN (' +
            ','.join('?' for _ in keys) + ')', (*accounts,*keys)).fetchall())
    counts = {name: sum(row['ai_risk_level'] == name for row in rows)
              for name in ('normal', 'suspicious_pattern', 'pending_v4', 'inference_error')}
    return dict(batch_id=ticket['batch_id'], requested=ticket['count'], saved=len(rows),
                **counts, **input_mix(ticket), transaction_ids=sorted(row['id'] for row in rows))


def commit_batch(conn, ticket, process, last_id, preflight):
    """One atomic financial commit. Retrying the same ticket cannot repeat it."""
    payment_lock(conn)
    require_schema(conn)
    planned = plan(ticket)
    prior = receipt(conn, ticket)
    if prior['saved']:
        if prior['saved'] != ticket['count']:
            raise RuntimeError('Incomplete request identity. No payment was replayed.')
        for sender, _, form, key in planned:
            event = prepare_ingestion(form, sender['account_number'], datetime.now(timezone.utc).isoformat())
            existing(conn, sender['account_number'], key, submission(event, None, None, None, None, None))
        return {**prior, 'replayed': True}
    if ticket['version'] == 1 or 'scenario_wallet_ids' not in ticket:
        raise ValueError('This generation form uses the retired planner. Reload the dashboard for the corrected mix.')
    preflight()
    # The shared payment lock prevents customer writes during preflight/commit.
    # Lock wallet rows too so any independent balance maintenance cannot race.
    suffix = ' FOR UPDATE' if conn.engine == 'mysql' else ''
    for wallet in ticket['wallets']:
        row = conn.execute('SELECT username,account_number,role FROM users WHERE id=?' + suffix,
                           (wallet['id'],)).fetchone()
        if (not row or row['role'] != 'customer' or row['username'] != wallet['username'] or
                row['account_number'] != wallet['account_number'] or
                DEMO_WALLETS.get(row['username']) != row['account_number']):
            raise ValueError('Demo wallet identity changed. Reload the dashboard.')
    for agent in ticket['agents']:
        row = conn.execute("SELECT id FROM agents WHERE id=? AND status='active'" + suffix, (int(agent),)).fetchone()
        if row is None:
            raise ValueError('Agent availability changed. Reload the dashboard.')
    try:
        for sender, recipient, form, key in planned:
            event = prepare_ingestion(form, sender['account_number'], datetime.now(timezone.utc).isoformat())
            kind, amount = LEGACY_TYPES[event.transaction_type], event.amount_minor / 100
            conn.execute('INSERT INTO transactions (sender_account,receiver_account,amount,'
                         'transaction_type,currency,channel,timestamp,status,risk_score,risk_level,'
                         'description,agent_id,client_request_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                         (event.sender_wallet,event.receiver_wallet,amount,kind,'USD',event.channel,
                          event.event_timestamp,'Completed',0,'pending_review','V4 demo payment',
                          int(event.agent_id) if event.agent_id else None,key))
            tx = last_id(conn)
            persist(conn, with_id(event, tx))
            process(conn, tx, event.sender_wallet, event.receiver_wallet, amount, kind,
                    event.event_timestamp, account_number=event.sender_wallet, emit_events=False)
            if kind == 'deposit':
                conn.execute('UPDATE users SET balance=balance+? WHERE id=?', (amount,sender['id']))
            else:
                debit = conn.execute('UPDATE users SET balance=balance-? WHERE id=? AND balance>=?',
                                     (amount,sender['id'],amount))
                if debit.rowcount != 1:
                    raise ValueError('Insufficient demo funds. The entire batch was rolled back.')
                if kind == 'transfer':
                    conn.execute('UPDATE users SET balance=balance+? WHERE id=?', (amount,recipient['id']))
        # Capture the receipt before commit; a failed response must never cause
        # another financial execution. The signed ticket remains reusable.
        result = receipt(conn, ticket)
        conn.commit()
        return {**result, 'replayed': False}
    except Exception:
        conn.rollback()
        raise
