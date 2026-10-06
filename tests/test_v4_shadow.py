"""Controlled shadow tests: no server startup, real customers or live DB writes."""
import ast
from datetime import datetime,timezone
from decimal import Decimal
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import threading
import uuid
import pytest
from flask import Flask,request,session
from flask_socketio import SocketIO
from database import DatabaseAdapter
import v4_shadow as v
from canonical_mobile_money import VERSION
from canonical_mobile_money_store import migrate as canonical_migrate
from canonical_history_store import migrate as history_migrate
from canonical_history_journal import ensure

ROOT=Path(__file__).resolve().parents[1]

def db(path):
    raw=sqlite3.connect(path,timeout=5);raw.row_factory=sqlite3.Row
    raw.execute('PRAGMA foreign_keys=ON')
    return DatabaseAdapter(raw,'sqlite')

def setup(path):
    c=db(path)
    c.execute('CREATE TABLE users (id INTEGER PRIMARY KEY,account_number TEXT,username TEXT,role TEXT,balance REAL)')
    c.execute("INSERT INTO users VALUES (1,'A','alice','customer',500),(2,'B','bob','customer',500),(3,'STAFF','reviewer','compliance',0)")
    c.execute('CREATE TABLE agents (id INTEGER PRIMARY KEY)');c.execute('INSERT INTO agents VALUES(1)')
    c.execute('CREATE TABLE transactions (id INTEGER PRIMARY KEY,sender_account TEXT,receiver_account TEXT,amount REAL,transaction_type TEXT,currency TEXT,channel TEXT,timestamp TEXT,status TEXT,risk_score REAL,risk_level TEXT,description TEXT,agent_id INTEGER,rule_score REAL DEFAULT 0,ai_confidence REAL DEFAULT 0)')
    canonical_migrate(c);history_migrate(c);ensure(c,apply=True);v.migrate(c)
    from canonical_history import boundary
    scope=boundary('controlled-prototype-v1','2026-01-01T00:00:00.000000Z',0,'isolated-fixture','no-live-data')
    scope.update(preexisting_parent_ids=[],preexisting_change_ids=[])
    c.execute('INSERT INTO cmm_observation_scopes VALUES (?,?,?)',(scope['scope_id'],1,json.dumps(scope)))
    c.commit();c.close()

def form(kind='wallet_to_wallet',assisted=False):
    agent=kind!='wallet_to_wallet' or assisted
    return dict(canonical_version=VERSION,type=kind,amount='10.50',currency='USD',channel='agent' if agent else 'direct_wallet',
        agent_id='1' if agent else '',serviced_wallet=('B' if assisted else 'A') if agent else '',
        agent_flow_direction=kind if kind!='wallet_to_wallet' else 'none',recipient='B' if kind=='wallet_to_wallet' else '')

def response(tx,p=.2,code=None):
    r=v.error(tx,code or 'CHECK')
    if code:return r
    r.update(status='success',prediction=int(p>=.5),suspicious_probability=p,decision='suspicious_pattern' if p>=.5 else 'normal',
        error_code=None,history_status='COMPLETE_VERIFIED',source_revision='a'*64,observation_scope='controlled-prototype-v1',scope_revision=1,
        event_timestamp='2026-10-06T00:00:00.000000Z',history_complete_through={'key':['2026-10-06T00:00:00.000000Z',tx],'timestamp':v.now()})
    return r

def handler(path,monkeypatch,runner=None,rollback=False):
    c=db(path);app=Flask(__name__);app.secret_key='fixture-only'
    monkeypatch.setenv('V4_SHADOW_ENABLED','ON')
    calls=[];events=[]
    socket=type('Socket',(),{'emit':lambda *a,**k:None})()
    def after(app,factory,tx,socket):
        check=db(path)
        assert check.execute('SELECT id FROM transactions WHERE id=?',(tx,)).fetchone()
        assert check.execute('SELECT COUNT(*) AS n FROM cmm_source_changes WHERE transaction_id=?',(tx,)).fetchone()['n']==2
        check.close();calls.append('post_commit')
        def publish(payload):
            check=db(path)
            assert v.get(check,tx)['status']!='pending'
            check.close();events.append(payload)
        v.process(factory,tx,publish,runner=runner or (lambda tx:response(tx)))
    monkeypatch.setattr(v,'after_commit',after)
    tree=ast.parse((ROOT/'server.py').read_text(encoding='utf-8'))
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='create_transaction');fn.decorator_list=[]
    def legacy(c,tx,*a,**kw):
        calls.append('V1_stub')
        c.execute('UPDATE transactions SET risk_score=55,rule_score=12,ai_confidence=.8 WHERE id=?',(tx,))
        if rollback:
            c.rollback();raise RuntimeError('controlled source rollback')
        return 55,'suspicious','V1 unchanged',None
    def user(i):return dict(c.execute('SELECT * FROM users WHERE id=?',(i,)).fetchone())
    ns=dict(app=app,request=request,session=session,datetime=datetime,timezone=timezone,Decimal=Decimal,os=os,
        get_db=lambda:c,connect_db=lambda:db(path),socketio=socket,get_user_by_id=user,
        get_user_by_account_number=lambda a:dict(c.execute('SELECT * FROM users WHERE account_number=?',(a,)).fetchone()),
        normalize_account_number=lambda a:a.strip().upper(),VALID_TRANSACTION_TYPES={'transfer','deposit','withdraw'},
        get_last_insert_id=lambda c:c.execute('SELECT last_insert_rowid() AS id').fetchone()['id'],
        process_transaction_event=legacy,broadcast_user_balance=lambda *a:None,broadcast_stats=lambda *a:None,
        record_activity=lambda *a:None,_train_ai_model_from_db=lambda *a:pytest.fail('Training forbidden'),
        flash=lambda *a:None,redirect=lambda x:x,url_for=lambda x:x)
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'current_customer_handler','exec'),ns)
    app.add_url_rule('/customer/transaction',view_func=ns['create_transaction'],methods=['POST'])
    client=app.test_client()
    with client.session_transaction() as s:s['user_id']=1
    return c,client,calls,events

@pytest.mark.parametrize('kind,assisted',[('wallet_to_wallet',False),('wallet_to_wallet',True),('cash_in',False),('cash_out',False)])
def test_flask_committed_roles_real_isolated_model(tmp_path,monkeypatch,kind,assisted):
    path=tmp_path/'fixture.db';setup(path)
    def child(tx):
        p=subprocess.run([str(v.PYTHON),'-I','-B',str(ROOT/'ml_v4/shadow_integration/fixture_worker.py'),str(path),str(tx)],
            capture_output=True,text=True,timeout=30)
        assert p.returncode==0,p.stderr
        return json.loads(p.stdout)
    c,client,calls,events=handler(path,monkeypatch,child)
    assert client.post('/customer/transaction',data=form(kind,assisted)).status_code==200
    assert calls==['V1_stub','post_commit'] and len(events)==1
    raw=dict(c.execute('SELECT * FROM canonical_mobile_money_events').fetchone())
    assert raw['transaction_type']==kind and raw['amount_minor']==1050
    assert raw['sender_wallet']=='A' and raw['receiver_wallet']==('B' if kind=='wallet_to_wallet' else 'A')
    assert raw['serviced_wallet']==('B' if assisted else 'A' if kind!='wallet_to_wallet' else '')
    assert raw['agent_flow_direction']==('none' if kind=='wallet_to_wallet' else kind)
    assert raw['channel']==('agent' if assisted or kind!='wallet_to_wallet' else 'direct_wallet')
    r=v.get(c,1);assert r['status']=='success' and r['history_status']=='COMPLETE_VERIFIED'
    legacy=c.execute('SELECT risk_score,rule_score,ai_confidence FROM transactions').fetchone()
    assert tuple(legacy)==(55,12,.8)
    c.close()

def test_rollback_no_shadow(tmp_path,monkeypatch):
    path=tmp_path/'f.db';setup(path)
    c,client,calls,events=handler(path,monkeypatch,rollback=True)
    assert client.post('/customer/transaction',data=form()).status_code==500
    assert calls==['V1_stub'] and not events
    assert c.execute('SELECT COUNT(*) AS n FROM '+v.TABLE).fetchone()['n']==0
    assert c.execute('SELECT COUNT(*) AS n FROM transactions').fetchone()['n']==0
    c.close()

@pytest.mark.parametrize('p,code',[(.2,None),(.5,None),(.9,None),(None,'HISTORY_INCOMPLETE'),(None,'MODEL_INTEGRITY')])
def test_storage_idempotency_restart(tmp_path,monkeypatch,p,code):
    path=tmp_path/'f.db';setup(path)
    c,client,calls,events=handler(path,monkeypatch,lambda tx:response(tx,p,code))
    client.post('/customer/transaction',data=form());original=v.get(c,1);c.close()
    r=v.process(lambda:db(path),1,lambda _:pytest.fail('Duplicate event'),runner=lambda _:pytest.fail('Duplicate inference'))
    assert r==original
    c=db(path)
    assert c.execute('SELECT COUNT(*) AS n FROM '+v.TABLE).fetchone()['n']==1
    with pytest.raises(sqlite3.IntegrityError):
        c.execute('INSERT INTO '+v.TABLE+' SELECT * FROM '+v.TABLE)
    c.rollback();c.close()
    assert (r['prediction'] is None and r['suspicious_probability'] is None and r['decision']=='inference_error') if code else r['prediction']==int(p>=.5)

class Child:
    def __init__(self,out=b'{}',err=b'',returncode=0,timeout=False):
        self.stdout=io.BytesIO(out);self.stderr=io.BytesIO(err);self.returncode=returncode;self.timeout=timeout
    def wait(self,timeout=None):
        if self.timeout and timeout is not None:raise subprocess.TimeoutExpired('fixed child',timeout)
        return self.returncode
    def kill(self):self.returncode=-1;self.timeout=False

@pytest.mark.parametrize('kind',['timeout','exit','malformed','oversized','duplicate','nan','wrong_version','private'])
def test_process_errors_and_fixed_arguments(monkeypatch,kind):
    r=response(9007199254740993)
    if kind=='wrong_version':r['model_version']='wrong'
    if kind=='private':r['feature_vector']=[1,2,3]
    out=json.dumps(r).encode()
    if kind=='malformed':out=b'not JSON'
    if kind=='oversized':out=b'x'*(v.MAX_OUTPUT+1)
    if kind=='duplicate':out=b'{"status":"success","status":"inference_error"}'
    if kind=='nan':out=b'{"p":NaN}'
    child=Child(out,returncode=3 if kind=='exit' else 0,timeout=kind=='timeout')
    def spawn(args,**kw):
        assert args[:4]==[str(v.PYTHON),'-I','-B',str(v.LAUNCHER)]
        assert kw['shell'] is False and args[5]=='9007199254740993'
        assert kw['stdout']==kw['stderr']==subprocess.PIPE
        return child
    monkeypatch.setattr(v.subprocess,'Popen',spawn)
    got=v.invoke(9007199254740993,'a'*64,'test-uuid')
    if kind=='private':assert got['status']=='success' and 'feature_vector' not in got
    else:assert got['status']=='inference_error' and got['suspicious_probability'] is None
    assert got['transaction_id']=='9007199254740993'

def test_staff_socket_and_read_authorization(tmp_path):
    path=tmp_path/'staff.db';setup(path)
    app=Flask(__name__);app.secret_key='isolated';socket=SocketIO(app,async_mode='threading')
    from flask import g
    def conn():
        if 'db' not in g:g.db=db(path)
        return g.db
    @app.teardown_appcontext
    def close(_):
        if 'db' in g:g.db.close()
    v.install(app,socket,conn)
    customer=app.test_client();staff=app.test_client()
    with customer.session_transaction() as s:s['user_id']=1
    with staff.session_transaction() as s:s['user_id']=3
    cs=socket.test_client(app,flask_test_client=customer);ss=socket.test_client(app,flask_test_client=staff)
    assert cs.emit('v4_shadow_subscribe',callback=True)=={'ok':False}
    assert ss.emit('v4_shadow_subscribe',callback=True)=={'ok':True}
    assert customer.get('/api/v4-shadow/results').status_code==403
    assert staff.get('/api/v4-shadow/results').status_code==200
    v.publish_staff(lambda:db(path),socket,v.safe_payload(response(1)))
    assert not cs.get_received()
    assert [x['name'] for x in ss.get_received()]==['v4_shadow_result']
    c=db(path);c.execute("UPDATE users SET role='customer' WHERE id=3");c.commit();c.close()
    v.publish_staff(lambda:db(path),socket,v.safe_payload(response(1)))
    assert not ss.get_received()
    cs.disconnect();ss.disconnect();v.forget_user(3)

def test_ui_states_and_large_id():
    code="const a=require('./static/v4-shadow.js'); const assert=require('assert'); assert(a.wording({status:'success',decision:'normal'}).startsWith('No suspicious')); assert(a.wording({status:'success',decision:'suspicious_pattern'}).includes('analyst review')); assert(a.wording({status:'inference_error',decision:'normal'}).includes('unavailable'));"
    subprocess.run(['node','-e',code],cwd=ROOT,check=True)
    subprocess.run(['node','tests/v4_shadow_ui_test.cjs'],cwd=ROOT,check=True)
    js=(ROOT/'static/v4-shadow.js').read_text()
    assert 'Number(row.transaction_id)' not in js and 'textContent' in js
    assert v.safe_payload(response(9007199254740993))['transaction_id']=='9007199254740993'

def test_result_commit_failure_no_notification(tmp_path,monkeypatch):
    path=tmp_path/'f.db';setup(path)
    c,client,_,_=handler(path,monkeypatch);client.post('/customer/transaction',data=form())
    c.execute('DELETE FROM '+v.TABLE);c.commit();c.close()
    class BrokenCommit:
        engine='sqlite'
        def __init__(self):self.c=db(path);self.count=0
        def execute(self,*a):return self.c.execute(*a)
        def commit(self):
            self.count+=1
            if self.count==2:raise RuntimeError('result commit fails')
            self.c.commit()
        def rollback(self):self.c.rollback()
        def close(self):self.c.close()
    events=[]
    with pytest.raises(RuntimeError):v.process(BrokenCommit,1,events.append,runner=lambda tx:response(tx))
    assert not events
    c=db(path);assert v.get(c,1)['status']=='pending';c.close()

def test_no_ordinary_ml_imports():
    assert not any(k.startswith(('sklearn','xgboost','ai_core','ai_stage14_model')) for k in sys.modules)

def test_worker_integrity_before_runtime(monkeypatch):
    from ml_v4.shadow_integration.worker import main
    original=Path.read_bytes
    def damaged(path):
        if path.as_posix().endswith('ml_v4/frozen_inference/service.py'):return b'wrong-source'
        return original(path)
    monkeypatch.setattr(Path,'read_bytes',damaged)
    assert main(1,'a'*64,'fixture')['error_code']=='MODEL_INTEGRITY'

def test_pending_resume_after_restart(tmp_path,monkeypatch):
    path=tmp_path/'f.db';setup(path)
    c,client,_,_=handler(path,monkeypatch)
    client.post('/customer/transaction',data=form())
    # Simulate an isolated fixture's interrupted pending attempt, not a rewrite
    # of a live successful inference. Normal API never changes final rows.
    c.execute('DELETE FROM '+v.TABLE)
    pending=v.error(1,'PENDING');pending.update(status='pending',decision='pending',error_code=None)
    c.execute('INSERT INTO '+v.TABLE+' VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',(1,v.MODEL,v.FEATURE,pending['inference_id'],'pending',None,None,.5,'pending',None,json.dumps(pending),v.now()))
    c.commit();c.close()
    calls=[]
    out=v.process(lambda:db(path),1,calls.append,runner=lambda tx:response(tx,.5))
    assert out['status']=='success' and len(calls)==1

def test_concurrent_duplicate_mysql_lock_semantics(tmp_path,monkeypatch):
    path=tmp_path/'f.db';setup(path)
    c,client,_,_=handler(path,monkeypatch);client.post('/customer/transaction',data=form())
    c.execute('DELETE FROM '+v.TABLE);c.commit();c.close()
    lock=threading.Lock();started=threading.Event();finish=threading.Event();calls=[]
    class Row:
        def __init__(self,value):self.value=value
        def fetchone(self):return self.value
    class SimulatedMySQL:
        engine='mysql'
        def __init__(self):self.c=db(path)
        def execute(self,sql,params=()):
            if 'GET_LOCK' in sql:return Row({'ok':int(lock.acquire(blocking=False))})
            if 'RELEASE_LOCK' in sql:lock.release();return Row({'ok':1})
            return self.c.execute(sql,params)
        def commit(self):self.c.commit()
        def rollback(self):self.c.rollback()
        def close(self):self.c.close()
    def run(tx):calls.append(tx);started.set();assert finish.wait(5);return response(tx)
    outputs=[]
    t=threading.Thread(target=lambda:outputs.append(v.process(SimulatedMySQL,1,lambda _:None,runner=run)))
    t.start();assert started.wait(5)
    assert v.process(SimulatedMySQL,1,lambda _:None,runner=run) is None
    finish.set();t.join(5);assert not t.is_alive() and calls==[1]
    assert v.process(SimulatedMySQL,1,lambda _:None,runner=lambda _:pytest.fail('duplicate'))==outputs[0]
