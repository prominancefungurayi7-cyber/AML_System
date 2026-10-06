import json
import hashlib
from datetime import datetime,timedelta,timezone
from pathlib import Path
import numpy as np
import pytest
from experimental_v3.service import Service,MANIFEST,predict_v3,validate
from experimental_v3.web import create_app

ROOT=Path(__file__).resolve().parents[1]
TOKEN='test-only-authorization-token-32-characters'
def row(i=100,time='2027-06-10T12:00:00Z',wallet='test_wallet',receiver='test_receiver',typ='wallet_to_wallet',agent=''):
    return dict(transaction_id=i,event_timestamp=time,sender_wallet=wallet,receiver_wallet=receiver if typ=='wallet_to_wallet' else wallet,amount_minor=10000,currency='USD',transaction_type=typ,channel='agent' if agent else 'direct_wallet',agent_id=agent,serviced_wallet=wallet if agent else '',agent_flow_direction='none' if typ=='wallet_to_wallet' else typ)

@pytest.fixture(scope='module')
def service(): return Service()

@pytest.fixture
def app(): return create_app({'TESTING':True,'AML_EXPERIMENTAL_MODEL':'V3','EXPERIMENTAL_TOKEN':TOKEN})

def test_actual_artifact_and_preprocessing(service):
    assert hashlib.sha256((ROOT/MANIFEST['artifact']).read_bytes()).hexdigest()==MANIFEST['sha256'][MANIFEST['artifact']]
    assert service.model.n_features_in_==32
    x=np.arange(32,dtype=float).reshape(1,-1)
    np.testing.assert_array_equal(service.model.named_steps['preprocessing'].transform(x),x)

def test_schema_order_dtypes_cold_start(service):
    ids,x=service.pipeline.extract([row()]); a=np.asarray(x,dtype=np.float64)
    assert a.shape==(1,32) and a.dtype==np.float64
    assert service.names[0]=='current_amount_usd' and service.names[22]=='agent_wallet_growth_ratio_7d'
    assert a[0,0]==100 and a[0,3]==1 and a[0,22]==-1 and a[0,29]==0
    result=service.predict([row()],[])[0]
    assert result['features_valid'] and 'agent_wallet_growth_ratio_7d' in result['unavailable_features']

@pytest.mark.parametrize('kind',['normal','structuring','network','agent'])
def test_synthetic_demonstrations(service,kind):
    rows=[]
    for i in range(1 if kind=='normal' else 8):
        r=row(100+i,f'2027-06-10T12:{i:02}:00Z')
        if kind=='structuring': r['amount_minor']=12000+i*1000
        if kind=='network': r['receiver_wallet']='test_r'+str(i)
        if kind=='agent': r=row(100+i,f'2027-06-10T12:{i:02}:00Z','test_c'+str(i),'','cash_out','test_agent')
        rows.append(r)
    results=service.predict(rows,[])
    for r in results:
        assert r['prediction']==int(r['confidence']>=.5)
        assert 0<=r['confidence']<=1 and r['threshold']==.5
        assert (r['test_alert'] is not None)==bool(r['prediction'])

def test_sequential_and_future_invariance(service):
    first=row(); second=row(101,'2027-06-10T12:01:00Z')
    one=service.predict([first],[])[0]; batch=service.predict([first,second],[])
    assert one==batch[0]
    assert batch[1]==service.predict([second],[first])[0]
    with pytest.raises(ValueError): service.predict([first],[second])

def test_equal_timestamp_order(service):
    a=row(99); b=row(100)
    ids,x=service.pipeline.extract([b,a]); assert ids==['99','100'] and x[1][3]==2
    assert service.predict([b],[a])[0]['status']=='success'
    with pytest.raises(ValueError): service.predict([a],[b])

def test_v3_growth_exact_coverage(service):
    now=datetime(2027,6,10,12,tzinfo=timezone.utc)
    history=[row(i+1,(now-timedelta(days=40-i)).isoformat(),'test_c'+str(i),'','cash_in','test_agent') for i in range(20)]
    current=row(100,now.isoformat(),'test_new','','cash_out','test_agent')
    _,x=service.pipeline.extract(history+[current]); assert x[-1][22]>=0 and x[-1][31]==28
    _,y=service.pipeline.extract(history[6:]+[current]); assert y[-1][22]==-1

@pytest.mark.parametrize('field,value',[('ground_truth_label',1),('risk_score',99),('scenario_id','private'),('amount_minor',True),('amount_minor',0),('event_timestamp','2027-06-10T12:00:00'),('channel','unknown'),('sender_wallet','real_wallet'),('serviced_wallet','test_missing')])
def test_invalid_no_target_leakage(service,field,value):
    invalid=row();invalid[field]=value
    with pytest.raises(ValueError): service.predict([invalid],[])

def test_explicit_history_required(service):
    with pytest.raises(ValueError): service.predict([row()],None)

def test_endpoint_auth_local_csrf(app):
    c=app.test_client(); payload={'synthetic':True,'transaction':row(),'prior_history':[]}
    assert c.post('/api/experimental/v3/predict',json=payload).status_code==401
    assert c.post('/experimental/v3/login',json={'token':'wrong'}).status_code==401
    csrf=c.post('/experimental/v3/login',json={'token':TOKEN}).json['csrf']
    assert c.post('/api/experimental/v3/predict',json=payload).status_code==401
    assert c.post('/api/experimental/v3/predict',json=payload,headers={'X-V3-CSRF':csrf}).status_code==200
    assert c.post('/api/experimental/v3/predict',json=payload,headers={'Authorization':'Bearer '+TOKEN},environ_overrides={'REMOTE_ADDR':'192.0.2.1'}).status_code==403
    assert c.post('/api/experimental/v3/predict',json=payload,headers={'Authorization':'Bearer '+TOKEN,'X-Forwarded-For':'127.0.0.1'}).status_code==403
    assert c.post('/api/experimental/v3/predict',json=payload,headers={'Authorization':'Bearer '+TOKEN,'Origin':'https://evil.example'}).status_code==403

def test_off_no_model():
    a=create_app({'TESTING':True,'AML_EXPERIMENTAL_MODEL':'OFF'})
    assert a.extensions['v3_service'] is None
    assert a.test_client().get('/api/experimental/v3/status').status_code==404

def test_isolation_no_financial_or_alert_modules(app,monkeypatch):
    import builtins
    original=builtins.__import__
    def forbidden(name,*args,**kwargs):
        if name.split('.')[0] in {'database','transactions','alerts','server','ai_core','reports'}: raise AssertionError('Production module access')
        return original(name,*args,**kwargs)
    monkeypatch.setattr(builtins,'__import__',forbidden)
    c=app.test_client()
    result=c.post('/api/experimental/v3/predict',json={'synthetic':True,'transaction':row(),'prior_history':[]},headers={'Authorization':'Bearer '+TOKEN})
    assert result.status_code==200
    assert 'db' not in app.extensions
    assert c.get('/experimental/v3').status_code==200

def test_socket_namespace_and_recipient_isolation(app,monkeypatch):
    from werkzeug.test import EnvironBuilder
    original=EnvironBuilder.get_environ
    def local_environment(self):
        env=original(self); env['REMOTE_ADDR']='127.0.0.1'; return env
    monkeypatch.setattr(EnvironBuilder,'get_environ',local_environment)
    io=app.extensions['v3_socketio']; a=app.test_client(); b=app.test_client()
    auth=a.post('/experimental/v3/login',json={'token':TOKEN}).json
    auth2=b.post('/experimental/v3/login',json={'token':TOKEN}).json
    opts={}
    s=io.test_client(app,flask_test_client=a,namespace='/experimental-v3',auth={'csrf':auth['csrf']},**opts)
    other=io.test_client(app,flask_test_client=b,namespace='/experimental-v3',auth={'csrf':auth2['csrf']},**opts)
    assert s.is_connected('/experimental-v3')
    s.emit('experimental_v3_predict',{'synthetic':True,'transactions':[row()],'prior_history':[]},namespace='/experimental-v3')
    events=s.get_received('/experimental-v3'); assert len(events)==1 and events[0]['name']=='experimental_v3_prediction'
    assert other.get_received('/experimental-v3')==[]
    unauthorized=io.test_client(app,namespace='/experimental-v3',auth={},**opts)
    assert not unauthorized.is_connected('/experimental-v3')

def test_v1_server_off_path_byte_equivalence():
    s=(ROOT/'server.py').read_bytes()
    start=s.index(b'# Explicit local synthetic testing exits before production imports/startup.')
    end=s.index(b'import json',start)
    restored=s[:start]+s[end:]
    expected=(ROOT/'experimental_v3/server_before.sha256').read_text().strip()
    assert hashlib.sha256(restored).hexdigest()==expected

