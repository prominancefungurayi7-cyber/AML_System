"""Simulation regression checks; only in-memory fixtures, never the local aml DB."""
import ast
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import random
import sqlite3

import pytest
from flask import Flask, redirect, request, url_for
from database import DatabaseAdapter
from transaction_simulation import simulation_batch, simulation_summary

USERS = [dict(id=i, username=f'demo{i}', account_number=f'TEST{i}',
              balance=100000, wealth_segment='average') for i in range(1, 17)]
AGENTS = [dict(id=i) for i in (1, 2, 3)]
NOW = datetime(2026, 10, 12, tzinfo=timezone.utc)


def test_cash_types_stable_partners_and_real_episode_sequences():
    random.seed(8)
    rows = simulation_batch(100, USERS, AGENTS, now=NOW)
    assert len(rows) == 100
    assert rows == sorted(rows, key=lambda row: row[4])
    ordinary = [row for row in rows if row[6].startswith('Ordinary')]
    assert len(ordinary) == 70
    assert {row[2] for row in ordinary} == {'deposit', 'withdraw', 'transfer'}
    recipients = defaultdict(set)
    for row in rows:
        sender, receiver, kind, _, timestamp, _, _, _, _, agent = row
        assert datetime.fromisoformat(timestamp) < NOW
        if kind != 'transfer':
            assert sender == receiver and agent is not None
        else:
            assert sender != receiver
        if row in ordinary and kind == 'transfer':
            recipients[sender['id']].add(receiver['id'])
    assert all(len(values) == 1 for values in recipients.values())
    episodes = {family: [row for row in rows if row[6] == 'Demo episode: ' + family]
                for family in ('structuring', 'network', 'agent')}
    assert all(len(rows) >= 6 for rows in episodes.values())
    assert all(9000 <= row[3] < 10000 for row in episodes['structuring'])
    assert len({row[1]['id'] for row in episodes['network']}) >= 5
    assert len({row[9] for row in episodes['agent']}) == 1
    assert not {row[0]['id'] for row in ordinary} & {row[0]['id'] for rows in episodes.values() for row in rows}


def test_density_and_missing_agent_guards():
    with pytest.raises(ValueError, match='four events'):
        simulation_batch(5000, USERS, AGENTS, now=NOW)
    with pytest.raises(ValueError, match='four events'):
        simulation_batch(100, USERS, AGENTS, existing_count=6100, now=NOW)
    with pytest.raises(ValueError, match='two agents'):
        simulation_batch(100, USERS, [], now=NOW)


def test_summary_separates_ai_from_operational_severity():
    result = simulation_summary([
        {'risk_level': risk, 'ai_risk_level': ai} for risk, ai in
        [('normal', 'normal'), ('low', 'suspicious_pattern'),
         ('suspicious', 'suspicious_pattern'), ('high_risk', 'normal'),
         ('critical', 'suspicious_pattern'), ('pending_review', 'pending_v4')]])
    assert (result['normal'], result['low'], result['flagged'], result['pending']) == (1, 1, 3, 1)
    assert (result['ai_normal'], result['ai_suspicious'], result['ai_unavailable']) == (2, 3, 1)
    assert result['critical'] == 1


def route_fixture(balance=100000, fail_notification=False):
    db = DatabaseAdapter(sqlite3.connect(':memory:'), 'sqlite')
    db.connection.row_factory = sqlite3.Row
    db.executescript('''CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT,
        role TEXT, account_number TEXT, balance REAL, wealth_segment TEXT);
        CREATE TABLE agents(id INTEGER,agent_code TEXT,agent_name TEXT,location TEXT,
        region TEXT,city TEXT,status TEXT);
        CREATE TABLE transactions(id INTEGER PRIMARY KEY,sender_account TEXT,
        receiver_account TEXT,amount REAL,transaction_type TEXT,currency TEXT,
        channel TEXT,timestamp TEXT,risk_score INTEGER,risk_level TEXT,description TEXT,
        destination_country TEXT,agent_id INTEGER,status TEXT,ai_risk_level TEXT);''')
    for user in USERS:
        db.execute('INSERT INTO users VALUES (?,?,?,?,?,?)',
                   (user['id'], user['username'], 'customer', user['account_number'], balance, 'average'))
    for agent in AGENTS:
        db.execute("INSERT INTO agents VALUES (?, '', '', '', '', '', 'active')", (agent['id'],))
    db.commit()
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY='test', DATABASE=':memory:')
    app.add_url_rule('/admin', 'admin_dashboard', lambda: 'admin')
    notices, events = [], []
    planned = [
        (USERS[0], USERS[0], 'deposit', 5, NOW.isoformat(), 'agent', 'cash', None, 'ZW', 1),
        (USERS[1], USERS[2], 'transfer', 20, NOW.isoformat(), 'mobile', 'transfer', None, 'ZW', None)]
    def process(conn, tx, *_args, **kwargs):
        assert kwargs['emit_events'] is False
        assert kwargs['generated_label'] is None and kwargs['scenario_reason'] is None
        conn.execute("UPDATE transactions SET risk_level='suspicious',ai_risk_level='suspicious_pattern' WHERE id=?", (tx,))
        return 45, 'suspicious', 'measured', None
    def broadcast(*args):
        if fail_notification:
            raise RuntimeError('Notification unavailable')
        events.append(args)
    namespace = dict(app=app, request=request, redirect=redirect, url_for=url_for,
                     flash=notices.append, login_required=lambda *_: lambda fn: fn,
                     v4_primary_enabled=lambda: False, get_db=lambda: db,
                     get_user_by_id=lambda _: USERS[0], session={'user_id': 1},
                     simulation_batch=lambda *_a, **_k: planned,
                     simulation_summary=simulation_summary, datetime=datetime,
                     timezone=timezone, timedelta=__import__('datetime').timedelta,
                     get_last_insert_id=lambda conn: conn.execute('SELECT last_insert_rowid() AS id').fetchone()['id'],
                     process_transaction_event=process,
                     broadcast_user_balance=lambda *_: None, broadcast_stats=lambda *_: None,
                     broadcast_event=broadcast, record_activity=lambda *_: None,
                     _RULE_ENGINE_ENABLED=True)
    source = (Path(__file__).resolve().parents[1] / 'server.py').read_text(encoding='utf-8')
    nodes = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)
             and node.name in ('generate_transactions', 'legacy_simulation_block_reason')]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<simulation-route>', 'exec'), namespace)
    return app.test_client(), db, notices, events


def test_route_counts_actual_ai_results_and_conserves_transfer_value():
    client, db, notices, events = route_fixture()
    assert client.post('/admin/generate-transactions', data={'count': 100}).status_code == 302
    assert db.execute('SELECT COUNT(*) n FROM transactions').fetchone()['n'] == 2
    assert db.execute('SELECT SUM(balance) n FROM users').fetchone()['n'] == 1600005
    assert '2 flagged' in notices[-1] and 'AI: 2 suspicious, 0 normal' in notices[-1]
    assert events[-1][1]['count'] == 2
    db.close()


def test_insufficient_funds_rolls_back_entire_batch_without_notifications():
    client, db, notices, events = route_fixture(balance=0)
    client.post('/admin/generate-transactions', data={'count': 100})
    assert db.execute('SELECT COUNT(*) n FROM transactions').fetchone()['n'] == 0
    assert db.execute('SELECT SUM(balance) n FROM users').fetchone()['n'] == 0
    assert 'Insufficient demo funds' in notices[-1]
    assert not events
    db.close()


def test_canonical_boundary_blocks_legacy_startup_before_any_write():
    client, db, notices, events = route_fixture()
    db.execute('CREATE TABLE cmm_observation_scopes(scope_id TEXT)')
    db.execute("INSERT INTO cmm_observation_scopes VALUES ('existing-authority')")
    db.commit()
    response = client.post('/admin/generate-transactions', data={'count': 100})
    assert response.status_code == 409
    assert db.execute('SELECT COUNT(*) n FROM transactions').fetchone()['n'] == 0
    assert not events
    db.close()


def test_notification_failure_does_not_claim_committed_batch_rolled_back():
    client, db, notices, events = route_fixture(fail_notification=True)
    client.post('/admin/generate-transactions', data={'count': 100})
    assert db.execute('SELECT COUNT(*) n FROM transactions').fetchone()['n'] == 2
    assert 'was saved' in notices[-1] and 'Do not generate' in notices[-1]
    db.close()
