"""Nonfinancial V4 generation checks. All payment writes use temporary SQLite."""
import ast
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3

import pytest

from database import DatabaseAdapter
import canonical_history_store as history
from canonical_history import freshness
from canonical_history_journal import ensure
from canonical_mobile_money_store import migrate
import v4_simulation as simulation
import v4_primary
import v4_shadow
from aml_rules import assess_rules, CTR_THRESHOLD
from alerts import create_alert_if_needed
from test_stage5a_v4_primary import success


def connect(path):
    raw = sqlite3.connect(path)
    raw.row_factory = sqlite3.Row
    raw.execute('PRAGMA foreign_keys=ON')
    return DatabaseAdapter(raw, 'sqlite')


@pytest.fixture
def ledger(tmp_path):
    path = tmp_path / 'simulation.db'
    conn = connect(path)
    conn.executescript('''
        CREATE TABLE users(id INTEGER PRIMARY KEY,username TEXT,account_number TEXT UNIQUE,
          role TEXT,balance REAL,id_number TEXT,pep_flag INTEGER DEFAULT 0);
        CREATE TABLE agents(id INTEGER PRIMARY KEY,status TEXT,agent_code TEXT);
        CREATE TABLE transactions(id INTEGER PRIMARY KEY,sender_account TEXT,receiver_account TEXT,
          amount REAL,transaction_type TEXT,currency TEXT,channel TEXT,timestamp TEXT,status TEXT,
          risk_score REAL,risk_level TEXT,description TEXT,agent_id INTEGER,client_request_id CHAR(36),
          rule_score REAL,rule_level TEXT,rule_reason TEXT,ai_risk_level TEXT,ai_confidence REAL,
          ai_reason TEXT,rules_triggered TEXT,ctr_required INTEGER,sar_required INTEGER,
          destination_country TEXT,screening_hits TEXT);
        CREATE UNIQUE INDEX uq_transactions_sender_request ON transactions(sender_account,client_request_id);
        CREATE TABLE alerts(id INTEGER PRIMARY KEY,transaction_id INTEGER UNIQUE,account_number TEXT,
          risk_score REAL,risk_level TEXT,reason TEXT,rules_triggered TEXT,status TEXT,timestamp TEXT);
    ''')
    for index, (name, account) in enumerate(simulation.DEMO_WALLETS.items(), 1):
        conn.execute('INSERT INTO users(id,username,account_number,role,balance) VALUES (?,?,?,?,?)',
                     (index,name,account,'customer',100000))
    conn.execute("INSERT INTO users VALUES (100,'registered_customer','PRIVATE','customer',777,'private',0)")
    migrate(conn)
    history.migrate(conn)
    ensure(conn, apply=True)
    history.create_scope(conn, 'fixture', 'fixture-only', 'temporary fixture')
    history.attest(conn, 'fixture', 'fixture-only', 'temporary fixture')
    v4_shadow.migrate(conn)
    conn.commit()
    yield path, conn
    conn.close()


def processor():
    # Execute the actual server rule preparation and branch selection. Any
    # attempted Stage14 access raises, since no Stage14 service is supplied.
    namespace = dict(json=json, assess_rules=assess_rules, CTR_THRESHOLD=CTR_THRESHOLD,
                     screen_entity=lambda *_a, **_k: [], screening_summary=lambda _: (0,'',[]),
                     _RULE_ENGINE_ENABLED=True, v4_primary_enabled=lambda: True,
                     require_v4_rule_policy=lambda: None,
                     create_alert_if_needed=create_alert_if_needed)
    tree = ast.parse(Path('server.py').read_text(encoding='utf-8'))
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in (
        '_risk_level_from_score','_prepare_v4_primary','process_transaction_event')]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'server.py','exec'), namespace)
    return namespace['process_transaction_event']


def ticket(conn, mode='mixed', count=10):
    choices = simulation.options(conn, 'fixture-secret', 1)['choices']
    token = next(item['token'] for item in choices if (item['mode'],item['count']) == (mode,count))
    # These regression cases exercise the preserved version-2 replay planner.
    request = simulation.decode(token, 'fixture-secret', 1)
    request['version'] = 2
    request['wallets'] = [w for w in request['wallets'] if simulation.DEMO_WALLETS.get(w['username']) == w['account_number']]
    funded = [dict(r) for r in conn.execute("SELECT id,username,account_number,balance FROM users ORDER BY id").fetchall()
              if simulation.DEMO_WALLETS.get(r['username']) == r['account_number']]
    request['scenario_wallet_ids'] = simulation.scenario_wallet_order(funded)
    return request


def generate(conn, request):
    def preflight():
        scope, current, previous = history.assess(conn, 'fixture')
        assert freshness(scope,current,previous) == 'COMPLETE_VERIFIED'
    return simulation.commit_batch(conn, request, processor(),
        lambda db: db.execute('SELECT last_insert_rowid() AS id').fetchone()['id'], preflight)


def balances(conn):
    return {row['id']: round(row['balance'] * 100) for row in conn.execute('SELECT id,balance FROM users')}


def test_batch_has_canonical_captures_fresh_history_and_no_legacy_inference(ledger):
    path, conn = ledger
    before = balances(conn)
    start = datetime.now(timezone.utc)
    result = generate(conn, ticket(conn))
    assert result['saved'] == result['pending_v4'] == 10
    rows = conn.execute('SELECT * FROM transactions ORDER BY id').fetchall()
    assert all(datetime.fromisoformat(row['timestamp'].replace('Z','+00:00')) >= start for row in rows)
    assert all(row['ai_risk_level'] == 'pending_v4' for row in rows)
    assert sum(balances(conn).values()) == sum(before.values())
    assert balances(conn)[100] == before[100]
    assert Counter(row['operation'] for row in conn.execute('SELECT operation FROM cmm_source_changes')) == {
        'SOURCE_INSERT': 10, 'CANONICAL_INSERT': 10}
    scope, current, previous = history.assess(conn, 'fixture')
    assert current['status'] == 'COMPLETE_VERIFIED' and not current['issues']
    assert freshness(scope,current,previous) != 'COMPLETE_VERIFIED'
    history.attest(conn, 'fixture', 'fixture-only', 'post-commit fixture verification')
    conn.commit()
    scope, current, previous = history.assess(conn, 'fixture')
    assert freshness(scope,current,previous) == 'COMPLETE_VERIFIED'
    assert current['canonical_event_ids'] == result['transaction_ids']


def test_same_signed_request_after_commit_does_not_duplicate_payments(ledger):
    _, conn = ledger
    request = ticket(conn)
    first = generate(conn, request)
    before = balances(conn)
    second = generate(conn, request)
    assert second['replayed'] and second['transaction_ids'] == first['transaction_ids']
    assert balances(conn) == before
    assert conn.execute('SELECT COUNT(*) FROM cmm_source_changes').fetchone()[0] == 20


@pytest.mark.parametrize('version', [1, 2])
def test_prior_receipts_and_payment_retries_keep_original_plan(ledger, monkeypatch, version):
    _, conn = ledger
    request = ticket(conn)
    scenario_ids = request.pop('scenario_wallet_ids')
    request.update(version=version, batch_id='792976c1-5dac-4b2b-a8d0-5174590ed2ab')
    token = simulation.serializer('fixture-secret').dumps(request)
    old = simulation.decode(token, 'fixture-secret', 1)
    if version == 1:
        assert simulation.plan(old)[0][2]['amount'] == '17.74'
    # Seed an earlier planner's payment identity in the disposable ledger.
    # New forms use funded roles; existing records remain replayable unchanged.
    original_plan = simulation.plan
    with monkeypatch.context() as patch:
        patch.setattr(simulation, 'plan', lambda _: original_plan(old))
        first = generate(conn, {**old, 'version': 2, 'scenario_wallet_ids': scenario_ids})
    before = balances(conn)
    assert ticket(conn)['version'] == 2
    assert generate(conn, old)['transaction_ids'] == first['transaction_ids']
    assert balances(conn) == before


@pytest.mark.parametrize('version', [1, 2])
def test_unsubmitted_old_form_requires_reload_without_payment(ledger, version):
    _, conn = ledger
    request = {**ticket(conn), 'version': version}
    request.pop('scenario_wallet_ids')
    before = balances(conn)
    with pytest.raises(ValueError, match='retired planner'):
        generate(conn, request)
    assert balances(conn) == before
    assert conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0] == 0


@pytest.mark.parametrize('count', simulation.COUNTS)
@pytest.mark.parametrize('agents', [[], ['1']])
def test_balanced_input_mix_and_routine_topology(count, agents):
    wallets = [dict(id=i, username=n, account_number=a, balance=100000)
               for i, (n, a) in enumerate(simulation.DEMO_WALLETS.items(), 1)]
    request = dict(version=2, batch_id='792976c1-5dac-4b2b-a8d0-5174590ed2ab',
                   admin_id=1, count=count, mode='mixed', wallets=wallets, agents=agents,
                   scenario_wallet_ids=simulation.scenario_wallet_order(wallets))
    rows, schedule = simulation.plan(request), simulation.scenario_schedule(request)
    assert len(rows) == count and len({row[3] for row in rows}) == count
    assert simulation.plan(request) == rows
    mix = simulation.input_mix(request)
    assert mix['ordinary_inputs'] == (count * 7 + 9) // 10
    assert mix['suspicious_inputs'] == count - mix['ordinary_inputs']
    senders, receivers, risky = set(), set(), set()
    for family, (sender, recipient, form, _) in zip(schedule, rows):
        if family == 'ordinary':
            senders.add(sender['account_number'])
            receivers.add(recipient['account_number'])
            assert form['type'] == 'wallet_to_wallet'
            assert 1 <= float(form['amount']) <= 250
        else:
            risky.update((sender['account_number'], recipient['account_number']))
        assert not {'label', 'prediction', 'scenario', 'risk_level'} & form.keys()
    assert senders.isdisjoint(receivers)  # No routine feedback cycles.
    assert (senders | receivers).isdisjoint(risky)
    if count >= 100:
        assert mix['scenario_counts']['structuring'] > 0
        assert mix['scenario_counts']['network'] > 0
        assert bool(mix['scenario_counts']['agent']) == bool(agents)


def test_balanced_receipt_reports_inputs_separately_from_pending_predictions(ledger):
    _, conn = ledger
    result = generate(conn, ticket(conn))
    assert (result['ordinary_inputs'], result['suspicious_inputs']) == (7, 3)
    assert result['pending_v4'] == 10
    assert result['normal'] == result['suspicious_pattern'] == 0


def test_scenario_funding_selection_is_signed_and_stable_on_balance_changes(ledger):
    _, conn = ledger
    request = ticket(conn)
    before = simulation.plan(request)
    conn.execute('UPDATE users SET balance=balance+50000 WHERE id=7')
    conn.commit()
    assert simulation.plan(request) == before
    assert ticket(conn)['scenario_wallet_ids'] != request['scenario_wallet_ids']


def test_large_mixed_plan_conserves_funds_with_uneven_demo_balances():
    from decimal import Decimal
    funding = [149000, 381000, 362000, 420000, 477000, 495000,
               6900, 87000, 752000, 296000, 215000, 3273000, 934000]
    wallets = [dict(id=i, username=n, account_number=a, balance=funding[i-1])
               for i, (n, a) in enumerate(simulation.DEMO_WALLETS.items(), 1)]
    request = dict(version=2, batch_id='792976c1-5dac-4b2b-a8d0-5174590ed2ab',
                   admin_id=1, count=5000, mode='mixed', wallets=wallets, agents=[],
                   scenario_wallet_ids=simulation.scenario_wallet_order(wallets))
    funds = {w['id']: w['balance'] * 100 for w in wallets}
    total = sum(funds.values())
    forms = simulation.plan(request)
    for sender, recipient, form, _ in forms:
        amount = int(Decimal(form['amount']) * 100)
        funds[sender['id']] -= amount
        funds[recipient['id']] += amount
        assert funds[sender['id']] >= 0
    assert sum(funds.values()) == total
    splits = [form['amount'] for family, (_, _, form, _) in zip(simulation.scenario_schedule(request), forms)
              if family == 'structuring']
    assert any(Decimal(amount) < 250 for amount in splits)
    assert any(Decimal(amount) >= 8500 for amount in splits)


@pytest.mark.parametrize('mode', ['mixed','ordinary','structuring','network','agent'])
def test_scenario_forms_and_balances(ledger, mode):
    _, conn = ledger
    conn.execute("INSERT INTO agents VALUES (1,'active','AGENT0001')")
    conn.execute("INSERT INTO users(id,username,account_number,role,balance) VALUES (200,'Agent','AGENT0001','agent',100000)")
    conn.commit()
    request = ticket(conn, mode)
    before = balances(conn)
    generate(conn, request)
    _, current, _ = history.assess(conn, 'fixture')
    assert current['status'] == 'COMPLETE_VERIFIED'
    rows = conn.execute('SELECT * FROM transactions ORDER BY id').fetchall()
    delta = sum(round(row['amount']*100) * (1 if row['transaction_type'] == 'deposit' else -1)
                for row in rows if row['transaction_type'] != 'transfer')
    assert sum(balances(conn).values()) == sum(before.values())
    assert balances(conn)[200] == before[200] - delta
    assert balances(conn)[100] == before[100]
    if mode == 'agent':
        assert {row['transaction_type'] for row in rows} == {'deposit','withdraw'}
    if mode == 'structuring':
        assert conn.execute('SELECT COUNT(*) FROM alerts').fetchone()[0] == 10
        assert all('R02' in row['rules_triggered'] for row in rows)


def test_insufficient_funds_rolls_back_payments_alerts_and_captures(ledger):
    _, conn = ledger
    conn.execute('UPDATE users SET balance=0 WHERE id<>100')
    conn.commit()
    before = balances(conn)
    with pytest.raises(ValueError, match='Insufficient demo funds'):
        generate(conn, ticket(conn,'structuring'))
    for table in ('transactions','alerts','canonical_mobile_money_events','cmm_source_changes'):
        assert conn.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0] == 0
    assert before == balances(conn)


def test_agents_missing_does_not_disable_wallet_generation(ledger):
    _, conn = ledger
    choices = simulation.options(conn, 'fixture', 1)['choices']
    assert {item['count'] for item in choices} == set(simulation.COUNTS)
    assert {item['mode'] for item in choices} == {'mixed','ordinary','structuring','network'}
    assert all(form['type'] == 'wallet_to_wallet' for _,_,form,_ in simulation.plan(ticket(conn)))


def test_ticket_tampering_or_another_admin_rejected(ledger):
    _, conn = ledger
    token = simulation.options(conn, 'fixture', 1)['choices'][0]['token']
    for changed, admin in ((token+'changed',1),(token,2)):
        with pytest.raises(ValueError):
            simulation.decode(changed,'fixture',admin)


def test_changed_demo_identity_rejected_without_payments(ledger):
    _, conn = ledger
    request = ticket(conn)
    conn.execute("UPDATE users SET username='real_customer' WHERE id=1")
    conn.commit()
    with pytest.raises(ValueError, match='identity changed'):
        generate(conn, request)
    assert conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0] == 0


def test_generation_readiness_failure_precedes_payment_writes(ledger):
    _, conn = ledger
    def fail():
        raise RuntimeError('History is not fresh')
    with pytest.raises(RuntimeError, match='not fresh'):
        simulation.commit_batch(conn,ticket(conn),processor(),lambda _: None,fail)
    assert conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0] == 0


@pytest.mark.parametrize('outcome', ['normal','suspicious','error','attestation_failure'])
def test_postcommit_decisions_never_replay_generated_payment(ledger, outcome):
    path, conn = ledger
    request = ticket(conn, 'structuring', 1)
    result = generate(conn, request)
    before = balances(conn)
    conn.rollback()
    tx = result['transaction_ids'][0]
    if outcome == 'attestation_failure':
        def failed(*_):
            raise RuntimeError('History changed concurrently')
        with pytest.raises(RuntimeError, match='concurrently'):
            v4_primary.complete_committed(lambda: connect(path),tx,attestor=failed,
                                           worker=lambda _: pytest.fail('Inference before verification'))
        expected = 'pending_v4'
    else:
        result = v4_primary.complete_committed(lambda: connect(path),tx,
            worker=lambda tx: v4_shadow.error(tx,'INFERENCE_ERROR') if outcome == 'error' else success(tx,.1 if outcome == 'normal' else .9))
        expected = {'normal':'normal','suspicious':'suspicious_pattern','error':'inference_error'}[outcome]
    assert balances(conn) == before
    assert conn.execute('SELECT ai_risk_level FROM transactions').fetchone()[0] == expected
    # Independent structuring alert survives normal AI, failure and retries.
    assert conn.execute('SELECT COUNT(*) FROM alerts').fetchone()[0] == 1
    assert generate(conn, request)['replayed']
    assert balances(conn) == before


def test_payment_lock_refuses_contention_without_mutation():
    calls = []
    class Busy:
        engine = 'mysql'
        def execute(self, sql, params):
            calls.append(sql)
            return self
        def fetchone(self):
            return {'acquired':0}
        def rollback(self):
            pytest.fail('Lock not acquired')
    with pytest.raises(RuntimeError, match='busy'):
        simulation.payment_lock(Busy())
    assert calls == ['SELECT GET_LOCK(?,5) AS acquired']


def test_lost_commit_response_can_retry_original_ticket_without_second_payment(ledger):
    _, conn = ledger
    request = ticket(conn)
    original = conn.commit
    def lost_response():
        original()
        raise RuntimeError('Connection lost after commit')
    conn.commit = lost_response
    with pytest.raises(RuntimeError, match='lost after commit'):
        generate(conn, request)
    conn.commit = original
    before = balances(conn)
    assert generate(conn, request)['replayed']
    assert balances(conn) == before
    assert conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0] == 10


def test_mid_batch_rule_failure_rolls_back_entire_batch(ledger):
    _, conn = ledger
    process = processor()
    calls = []
    def fail_later(*args, **kwargs):
        calls.append(args[1])
        if len(calls) == 3:
            raise RuntimeError('Rule service unavailable')
        return process(*args, **kwargs)
    before = balances(conn)
    with pytest.raises(RuntimeError, match='Rule service unavailable'):
        simulation.commit_batch(conn,ticket(conn,'structuring'),fail_later,
            lambda db: db.execute('SELECT last_insert_rowid()').fetchone()[0],lambda:None)
    assert len(calls) == 3
    assert balances(conn) == before
    for table in ('transactions','canonical_mobile_money_events','cmm_source_changes','alerts'):
        assert conn.execute('SELECT COUNT(*) FROM '+table).fetchone()[0] == 0


def test_http_generation_keeps_committed_batch_when_attestation_fails(ledger, monkeypatch):
    from flask import Flask, session, request, redirect, url_for, flash
    import v4_history_attestation
    path, conn = ledger
    token = next(item['token'] for item in simulation.options(conn,'fixture-secret',1)['choices']
                 if item['mode']=='ordinary' and item['count']==1)
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY='fixture-secret')
    app.add_url_rule('/admin','admin_dashboard',lambda:'admin')
    def fail_attestation(*_):
        raise RuntimeError('Source changed after commit')
    monkeypatch.setattr(v4_primary,'verify_startup',lambda _:None)
    monkeypatch.setattr(v4_history_attestation,'refresh_committed',fail_attestation)
    monkeypatch.setenv('CANONICAL_MOBILE_MONEY_ENABLED','ON')
    notices=[]
    namespace=dict(app=app,session=session,request=request,redirect=redirect,url_for=url_for,os=os,
                   flash=flash,require_v4_rule_policy=lambda:None,
                   connect_db=lambda:connect(path),get_db=lambda:conn,
                   process_transaction_event=processor(),
                   get_last_insert_id=lambda c:c.execute('SELECT last_insert_rowid()').fetchone()[0],
                   record_activity=lambda *args:notices.append(args),
                   broadcast_event=lambda *_:None,broadcast_stats=lambda:None,
                   broadcast_user_balance=lambda *_:None,datetime=datetime,timezone=timezone)
    tree=ast.parse(Path('server.py').read_text(encoding='utf-8'))
    nodes=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='generate_v4_transactions']
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'server.py','exec'),namespace)
    app.add_url_rule('/generate',view_func=namespace['generate_v4_transactions'],methods=['POST'])
    client=app.test_client()
    with client.session_transaction() as s:
        s.update(user_id=1,username='fixture-admin',generation_csrf='csrf')
    data={'generation_token':token,'csrf':'csrf'}
    assert client.post('/generate',data=data).status_code==302
    assert conn.execute('SELECT ai_risk_level FROM transactions').fetchone()[0]=='pending_v4'
    before=balances(conn)
    conn.rollback()
    assert client.post('/generate',data=data).status_code==302
    assert balances(conn)==before
    assert conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]==1
    assert len(notices)==1


def test_history_planner_includes_registered_customers_and_retries_once(ledger):
    _, conn = ledger
    choices = simulation.options(conn, 'new-plan', 1)
    assert 'PRIVATE' in choices['baseline_summary']
    token = next(c['token'] for c in choices['choices'] if c['mode'] == 'ordinary' and c['count'] == 100)
    request = simulation.decode(token, 'new-plan', 1)
    assert request['version'] == 5
    rows = simulation.plan(request)
    assert set(s['account_number'] for s, _, _, _ in rows) == set(choices['baseline_summary'])
    assert rows == simulation.plan(request)
    before = sum(balances(conn).values())
    first = generate(conn, request)
    second = generate(conn, request)
    assert first['saved'] == 100 and second['replayed']
    assert conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0] == 100
    assert sum(balances(conn).values()) == before


def test_historical_amounts_recipients_and_limited_baseline(ledger):
    from v4_customer_patterns import profiles
    _, conn = ledger
    # Only a disposable fixture receives these historical records.
    for amount in (20, 25, 30, 35, 40):
        conn.execute("INSERT INTO transactions(sender_account,receiver_account,amount,transaction_type,risk_level,timestamp,status) VALUES (?,?,?,?,?,?,?)",
                     ('PRIVATE', 'ACC1003', amount, 'transfer', 'normal', '2026-01-01T12:00:00', 'Completed'))
    wallets = [dict(r) for r in conn.execute("SELECT id,username,account_number,balance FROM users ORDER BY id").fetchall()]
    baseline = profiles(conn, wallets)
    assert baseline['PRIVATE']['median_minor'] == 3000
    assert baseline['PRIVATE']['sufficient_history']
    assert baseline['PRIVATE']['counterparties'] == ['ACC1003']
    assert not baseline['ACC1003']['sufficient_history']
    choices = simulation.options(conn, 'baseline', 1)['choices']
    token = next(c['token'] for c in choices if c['mode'] == 'ordinary' and c['count'] == 100)
    request = simulation.decode(token, 'baseline', 1)
    generated = [(r, f) for sender,r,f,_ in simulation.plan(request) if sender['account_number'] == 'PRIVATE']
    assert generated
    assert all(r['account_number'] == 'ACC1003' and 25 <= float(f['amount']) <= 35 for r,f in generated)


def current_ticket(conn, mode='ordinary', count=100):
    token = next(c['token'] for c in simulation.options(conn, 'current-plan', 1)['choices']
                 if c['mode'] == mode and c['count'] == count)
    return simulation.decode(token, 'current-plan', 1)


@pytest.mark.parametrize('mode', ['ordinary', 'mixed'])
@pytest.mark.parametrize('wallet_id', [1, 100])
def test_unfunded_customer_can_receive_before_joining_routine_senders(ledger, mode, wallet_id):
    _, conn = ledger
    conn.execute('UPDATE users SET balance=0 WHERE id=?', (wallet_id,))
    conn.commit()
    request = current_ticket(conn, mode=mode)
    rows = simulation.plan(request)
    unfunded = next(w['account_number'] for w in request['wallets'] if w['id'] == wallet_id)
    received = False
    sent = False
    for sender, recipient, form, _ in rows:
        assert sender['account_number'] != recipient['account_number']
        if recipient['account_number'] == unfunded:
            received = True
        if sender['account_number'] == unfunded:
            assert received
            sent = True
    assert sent
    assert {s['account_number'] for s, _, _, _ in rows} == set(request['customer_profiles'])
    before = sum(balances(conn).values())
    first = generate(conn, request)
    after = balances(conn)
    assert first['saved'] == 100
    assert sum(after.values()) == before
    assert generate(conn, request)['replayed']
    assert balances(conn) == after


def test_version_three_signed_plan_keeps_original_unfunded_failure(ledger):
    _, conn = ledger
    conn.execute('UPDATE users SET balance=0 WHERE id=1')
    conn.commit()
    request = {**current_ticket(conn), 'version': 3}
    with pytest.raises(ValueError, match='Insufficient balance'):
        simulation.plan(request)
    assert conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0] == 0


def test_committed_version_three_request_replays_after_new_planner_and_balance_changes(ledger):
    _, conn = ledger
    original = {**current_ticket(conn, count=10), 'version': 3}
    signed = simulation.serializer('retained-plan').dumps(original)
    request = simulation.decode(signed, 'retained-plan', 1)
    planned = simulation.plan(request)
    first = generate(conn, request)
    conn.execute('UPDATE users SET balance=0')
    conn.commit()
    assert current_ticket(conn, count=10)['version'] == 5
    assert simulation.plan(request) == planned
    before = balances(conn)
    replay = generate(conn, request)
    assert replay['replayed'] and replay['transaction_ids'] == first['transaction_ids']
    assert balances(conn) == before
    assert conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0] == 10


def test_receipt_requires_exact_sender_and_request_pairs(ledger):
    _, conn = ledger
    request = current_ticket(conn, count=10)
    result = generate(conn, request)
    first, second = simulation.plan(request)[:2]
    assert first[0]['account_number'] != second[0]['account_number']
    conn.execute('UPDATE transactions SET client_request_id=? WHERE id=?',
                 ('temporary-fixture-key', result['transaction_ids'][0]))
    conn.execute('UPDATE transactions SET client_request_id=? WHERE id=?',
                 (first[3], result['transaction_ids'][1]))
    conn.execute('UPDATE transactions SET client_request_id=? WHERE id=?',
                 (second[3], result['transaction_ids'][0]))
    conn.commit()
    before = balances(conn)
    assert simulation.receipt(conn, request)['saved'] == 8
    with pytest.raises(RuntimeError, match='Incomplete request identity'):
        generate(conn, request)
    assert balances(conn) == before
    assert conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0] == 10


def test_historical_baseline_excludes_unsuccessful_payments(ledger):
    from v4_customer_patterns import profiles
    _, conn = ledger
    for status, amount in [('Completed', 25)] * 5 + [('Failed', 9000), ('Cancelled', 1), ('Pending', 5000)]:
        conn.execute('INSERT INTO transactions(sender_account,receiver_account,amount,transaction_type,risk_level,status,timestamp) '
                     'VALUES (?,?,?,?,?,?,?)', ('PRIVATE', 'ACC1003', amount, 'transfer', 'normal', status,
                                               '2026-01-01T12:00:00'))
    wallets = [dict(r) for r in conn.execute('SELECT id,username,account_number,balance FROM users')]
    baseline = profiles(conn, wallets)['PRIVATE']
    assert baseline['sample_count'] == 5
    assert baseline['median_minor'] == baseline['lower_minor'] == baseline['upper_minor'] == 2500


def test_live_balance_change_cannot_spend_signed_snapshot_twice(ledger):
    _, conn = ledger
    request = current_ticket(conn, count=10)
    original = simulation.plan(request)
    conn.execute('UPDATE users SET balance=0')
    conn.commit()
    assert simulation.plan(request) == original
    before = balances(conn)
    with pytest.raises(ValueError, match='Insufficient demo funds'):
        generate(conn, request)
    assert balances(conn) == before
    for table in ('transactions', 'alerts', 'canonical_mobile_money_events', 'cmm_source_changes'):
        assert conn.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0] == 0
