import ast
from dataclasses import asdict
from pathlib import Path
import sqlite3
import sys
import os

import pytest
from canonical_mobile_money import (VERSION, cents, utc_timestamp, event_from_dict,
                                    serialize, prepare_ingestion, with_id, classify_history)
from canonical_mobile_money_store import migrate, persist, load, inspect, TABLE
from database import DatabaseAdapter


def event(**changes):
    raw = dict(transaction_id=1, event_timestamp='2026-10-05T12:00:00.000000Z',
               sender_wallet='A', receiver_wallet='B', amount_minor=1050, currency='USD',
               transaction_type='wallet_to_wallet', channel='direct_wallet', agent_id='',
               serviced_wallet='', agent_flow_direction='none')
    raw.update(changes)
    return event_from_dict(raw)


@pytest.mark.parametrize('kind', ['cash_in', 'cash_out'])
def test_cash(kind):
    e = event(transaction_type=kind, channel='agent', agent_id='1', serviced_wallet='A',
              receiver_wallet='A', agent_flow_direction=kind)
    assert e.subject == 'A'


@pytest.mark.parametrize('wallet', ['A', 'B'])
def test_assisted(wallet):
    assert event(channel='agent', agent_id='1', serviced_wallet=wallet).serviced_wallet == wallet


def test_direct_serialization():
    assert event_from_dict(serialize(event())) == event()


@pytest.mark.parametrize('change', [dict(receiver_wallet='A'), dict(channel='agent', agent_id='1'),
    dict(agent_flow_direction='cash_in'), dict(channel='agent', agent_id='1', serviced_wallet='C'),
    dict(agent_id='1'), dict(amount_minor=1.5), dict(amount_minor=True), dict(transaction_id=True),
    dict(currency='ZWL'), dict(amount_minor=1500001), dict(amount_minor=0), dict(sender_wallet=' A')])
def test_invalid(change):
    with pytest.raises((ValueError, TypeError)):
        event(**change)


@pytest.mark.parametrize('change', [dict(agent_id=''), dict(serviced_wallet=''),
    dict(agent_flow_direction='cash_out'), dict(receiver_wallet='B')])
def test_invalid_cash(change):
    base = dict(transaction_type='cash_in', channel='agent', agent_id='1', serviced_wallet='A',
                receiver_wallet='A', agent_flow_direction='cash_in')
    base.update(change)
    with pytest.raises(ValueError):
        event(**base)


@pytest.mark.parametrize('text,result', [('10.50',1050),('0.01',1),('15000.00',1500000),('10',1000)])
def test_exact_money(text,result):
    assert cents(text) == result


@pytest.mark.parametrize('text', ['1.001','NaN','Infinity','1e2','-1','0','15000.01',1.25,' 1.00'])
def test_bad_money(text):
    with pytest.raises(ValueError):
        cents(text)


def test_currency():
    with pytest.raises(ValueError):
        cents('10.50','EUR')


def test_utc_and_order():
    assert utc_timestamp('2026-10-05T14:00:00.123456+02:00') == '2026-10-05T12:00:00.123456Z'
    assert event().key < event(transaction_id=2).key
    assert event(transaction_id=2**53+1).transaction_id == 2**53+1


@pytest.mark.parametrize('stamp', ['2026-10-05T12:00:00','yesterday','2026-10-05',
    '2026-10-05T12:00:00.1234567Z','2026-99-05T12:00:00Z'])
def test_bad_time(stamp):
    with pytest.raises(ValueError):
        utc_timestamp(stamp)


def test_unknown_metadata_rejected():
    with pytest.raises(ValueError):
        event_from_dict({**serialize(event()), 'risk_score': 1})


def db():
    c = sqlite3.connect(':memory:')
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    c.execute('CREATE TABLE transactions (id INTEGER PRIMARY KEY, sender_account TEXT, receiver_account TEXT, transaction_type TEXT, agent_id INTEGER)')
    c.execute('CREATE TABLE agents (id INTEGER PRIMARY KEY)')
    c.execute('INSERT INTO agents VALUES (1)')
    c.commit()
    return DatabaseAdapter(c,'sqlite')


def parent(c,e):
    from canonical_mobile_money import LEGACY_TYPES
    c.execute('INSERT INTO transactions VALUES (?,?,?,?,?)',(e.transaction_id,e.sender_wallet,e.receiver_wallet,LEGACY_TYPES[e.transaction_type],int(e.agent_id) if e.agent_id else None))


def test_migration_roundtrip_rollback_idempotent():
    c=db()
    assert migrate(c)['changed']
    assert not migrate(c)['changed']
    c.commit()
    parent(c,event()); persist(c,event()); c.commit()
    assert load(c,1) == event()
    assert c.execute('SELECT history_status FROM '+TABLE).fetchone()[0] == 'UNKNOWN'
    parent(c,event(transaction_id=2)); persist(c,event(transaction_id=2)); c.rollback()
    assert load(c,2) is None
    assert c.execute('SELECT id FROM transactions WHERE id=2').fetchone() is None
    with pytest.raises(sqlite3.IntegrityError):
        persist(c,event())
    c.rollback()
    with pytest.raises(sqlite3.IntegrityError):
        c.execute('DELETE FROM transactions WHERE id=1')
    c.rollback(); c.close()


def test_unknown_agent():
    c=db();migrate(c)
    e=event(channel='agent',agent_id='999',serviced_wallet='B')
    parent(c,e)
    with pytest.raises(ValueError,match='Unknown'):
        persist(c,e)
    c.close()


def test_mismatched_schema():
    c=db();c.execute('CREATE TABLE '+TABLE+' (transaction_id INTEGER)')
    with pytest.raises(ValueError,match='mismatch'):
        migrate(c)
    c.close()


def test_no_backfill_or_fake_completeness():
    c=db();parent(c,event());c.commit();migrate(c)
    assert load(c,1) is None
    assert classify_history() == 'LEGACY_AMBIGUOUS'
    assert classify_history(trustworthy_conversion={'amount':10.5}) == 'LEGACY_AMBIGUOUS'
    assert classify_history(canonical={**serialize(event()),'canonical_version':VERSION}) == 'CANONICAL_VERIFIED'
    assert classify_history(trustworthy_conversion={'event':serialize(event()),'authority_reference':'review/1','verified_by':'operator'}) == 'LEGACY_CONVERTIBLE'
    c.close()


def test_form():
    form=dict(canonical_version=VERSION,type='wallet_to_wallet',amount='10.50',currency='USD',
              channel='direct_wallet',agent_id='',serviced_wallet='',agent_flow_direction='none',recipient='B')
    e=prepare_ingestion(form,'A','2026-10-05T12:00:00Z')
    assert with_id(e,9).transaction_id == 9
    assert e.amount_minor == 1050


def test_isolated_ingestion_route(monkeypatch):
    """Execute ONLY the extracted handler with mocks; never import server startup/AI."""
    from flask import Flask, request, session
    from datetime import datetime, timezone
    from decimal import Decimal
    import threading
    tree=ast.parse(Path('server.py').read_text(encoding='utf-8'))
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='create_transaction')
    fn.decorator_list=[]
    c=db(); c.execute('ALTER TABLE transactions ADD currency TEXT');c.execute('ALTER TABLE transactions ADD channel TEXT')
    for col in ('amount REAL','timestamp TEXT','status TEXT','risk_score REAL','risk_level TEXT','description TEXT'):
        c.execute('ALTER TABLE transactions ADD '+col)
    c.execute('CREATE TABLE users (id INTEGER PRIMARY KEY,balance REAL)');c.execute('INSERT INTO users VALUES(1,100)');c.execute('INSERT INTO users VALUES(2,100)')
    migrate(c);c.commit()
    app=Flask(__name__);app.secret_key='test-only'
    user={'id':1,'account_number':'A','balance':100,'username':'alice','role':'customer'}
    recipient={'id':2,'account_number':'B','balance':100,'role':'customer'}
    calls=[]; flashes=[]
    def legacy(*args,**kw):
        calls.append('V1_STUB_ONLY');return 0,'normal','test',None
    def train(*a,**k):
        raise AssertionError('Training must not start')
    ns=dict(app=app,session=session,request=request,datetime=datetime,timezone=timezone,Decimal=Decimal,os=os,
       threading=threading,get_user_by_id=lambda _:user,get_user_by_account_number=lambda _:recipient,
       normalize_account_number=lambda x:x.strip().upper(),VALID_TRANSACTION_TYPES={'deposit','withdraw','transfer'},
       get_db=lambda:c,get_last_insert_id=lambda _:c.execute('SELECT last_insert_rowid()').fetchone()[0],
       process_transaction_event=legacy,broadcast_user_balance=lambda *a:None,broadcast_stats=lambda *a:None,
       record_activity=lambda *a:None,_train_ai_model_from_db=train,flash=flashes.append,
       redirect=lambda x:x,url_for=lambda x:x)
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'isolated_handler','exec'),ns)
    form=dict(canonical_version=VERSION,type='wallet_to_wallet',amount='10.50',currency='USD',channel='direct_wallet',agent_id='',serviced_wallet='',agent_flow_direction='none',recipient='B')
    with app.test_request_context('/customer/transaction',method='POST',data=form):
        session['user_id']=1
        assert ns['create_transaction']()=='customer_dashboard'
    assert calls==['V1_STUB_ONLY'] and load(c,1).amount_minor==1050
    bad={**form,'amount':'1.001'}
    with app.test_request_context('/customer/transaction',method='POST',data=bad):
        session['user_id']=1;ns['create_transaction']()
    assert len(calls)==1 and c.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]==1
    monkeypatch.setenv('CANONICAL_MOBILE_MONEY_ENABLED','OFF')
    with app.test_request_context('/customer/transaction',method='POST',data=form):
        session['user_id']=1;ns['create_transaction']()
    assert len(calls)==1
    monkeypatch.setenv('CANONICAL_MOBILE_MONEY_ENABLED','ON')
    import canonical_mobile_money_store
    def fail(*a):
        raise ValueError('injected persistence failure')
    monkeypatch.setattr(canonical_mobile_money_store,'persist',fail)
    with app.test_request_context('/customer/transaction',method='POST',data=form):
        session['user_id']=1;ns['create_transaction']()
    assert len(calls)==1 and c.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]==1
    c.close()


def test_no_models_imported():
    assert not any(k.startswith(('xgboost','sklearn','experimental_v3','ai_stage14_model','ai_core')) for k in sys.modules)


def test_historical_artifact_preservation():
    import json,hashlib
    root=Path(__file__).resolve().parents[1]
    before=json.loads((root/'ml_v4/evidence/integration_stage2/before_sha256.json').read_text())
    for p,h in before.items():
        if p not in ('server.py','static/react-dashboard.js'):
            assert hashlib.sha256((root/p).read_bytes()).hexdigest()==h,p
