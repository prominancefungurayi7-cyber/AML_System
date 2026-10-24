"""Customer payment response boundary; only temporary SQLite payments."""
import ast
from datetime import datetime, timezone
from decimal import Decimal
import os
from pathlib import Path
import uuid

from flask import Flask, request, session, redirect, url_for, flash
import pytest

from test_v4_simulation import ledger, connect, processor, balances
import v4_primary


@pytest.mark.parametrize('notification_failure', [False, True])
def test_commit_returns_before_inference_and_same_request_cannot_pay_twice(
        ledger, monkeypatch, notification_failure):
    path, initial = ledger
    app = Flask(__name__)
    app.secret_key = 'offline-only'
    app.testing = True
    current = [connect(path)]
    notices, queued, closed = [], [], []
    before = balances(initial)
    def database():
        if current[0] is None:
            current[0] = connect(path)
        return current[0]
    def close(_):
        current[0].close()
        current[0] = None
        closed.append(True)
    def enqueue(tx):
        assert closed and current[0] is None
        check = connect(path)
        row = check.execute('SELECT * FROM transactions WHERE id=?', (tx,)).fetchone()
        assert row['ai_risk_level'] == 'pending_v4'
        assert check.execute('SELECT COUNT(*) n FROM cmm_source_changes WHERE transaction_id=?',
                             (tx,)).fetchone()['n'] == 2
        check.close()
        queued.append(tx)
    def notify(*args):
        notices.append(args)
        if notification_failure:
            raise RuntimeError('broker unavailable')
    monkeypatch.setenv('V4_SHADOW_ENABLED', 'OFF')
    monkeypatch.setattr(v4_primary, 'enqueue_committed', enqueue)
    monkeypatch.setattr(v4_primary, 'complete_committed',
                        lambda *_a, **_kw: pytest.fail('Inference must not block payment request'))
    namespace = dict(app=app, request=request, session=session, redirect=redirect,
        url_for=url_for, flash=flash, os=os, datetime=datetime, timezone=timezone, Decimal=Decimal,
        v4_primary_enabled=lambda: True, get_db=database, close_db=close,
        get_user_by_id=lambda uid: dict(database().execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()),
        get_user_by_account_number=lambda acct: dict(database().execute('SELECT * FROM users WHERE account_number=?', (acct,)).fetchone()),
        normalize_account_number=lambda acct: acct.strip().upper(),
        VALID_TRANSACTION_TYPES={'deposit', 'withdraw', 'transfer'},
        get_last_insert_id=lambda db: db.execute('SELECT last_insert_rowid() id').fetchone()['id'],
        process_transaction_event=processor(),
        broadcast_committed_customer_transaction=notify,
        broadcast_user_balance=notify, record_activity=notify)
    tree = ast.parse(Path('server.py').read_text(encoding='utf-8'))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'create_transaction')
    node.decorator_list = []
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'customer-route', 'exec'), namespace)
    app.add_url_rule('/customer/transaction', view_func=namespace['create_transaction'], methods=['POST'])
    app.add_url_rule('/customer', endpoint='customer_dashboard', view_func=lambda: 'dashboard')
    client = app.test_client()
    sender = initial.execute("SELECT id FROM users WHERE account_number='ACC1003'").fetchone()['id']
    receiver = initial.execute("SELECT id FROM users WHERE account_number='ACC1000'").fetchone()['id']
    with client.session_transaction() as state:
        state['user_id'] = sender
    form = dict(client_request_id=str(uuid.uuid4()), canonical_version='mobile_money.canonical.v1',
                type='wallet_to_wallet', amount='10.50', currency='USD', channel='direct_wallet',
                agent_id='', serviced_wallet='', agent_flow_direction='none', recipient='ACC1000')
    try:
        response = client.post('/customer/transaction', data=form)
        assert response.status_code == 302
        assert queued and notices
        assert client.post('/customer/transaction', data=form).status_code == 302
        assert len(queued) == 1
        check = connect(path)
        assert check.execute('SELECT COUNT(*) n FROM transactions').fetchone()['n'] == 1
        after = balances(check)
        assert after[sender] == before[sender] - 1050
        assert after[receiver] == before[receiver] + 1050
        assert sum(after.values()) == sum(before.values())
        assert check.execute('SELECT COUNT(*) n FROM v4_shadow_results').fetchone()['n'] == 0
        check.close()
    finally:
        if current[0] is not None:
            current[0].close()
