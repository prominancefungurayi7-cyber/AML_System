import ast
from dataclasses import asdict
import hashlib
import io
import json
import math
from pathlib import Path
import sqlite3
import subprocess
import sys
import numpy as np
import pytest
from ml_v4.frozen_inference import service as s
from ml_v4.frozen_inference.history import verified_snapshot

@pytest.fixture(autouse=True)
def no_fits(monkeypatch):
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler
    from xgboost import XGBClassifier
    _,_,_,pre=s.sources()
    def forbidden(*a,**k): raise AssertionError('FIT FORBIDDEN')
    for cls in (Pipeline,SimpleImputer,StandardScaler,XGBClassifier,pre.FrozenPreprocessor):
        monkeypatch.setattr(cls,'fit',forbidden)

@pytest.fixture
def model(): return s.FrozenModel()

def event(i=1,time='2026-09-01T00:00:00.000000Z',sender='A',receiver='B'):
    return dict(transaction_id=i,event_timestamp=time,sender_wallet=sender,receiver_wallet=receiver,
        amount_minor=100,currency='USD',transaction_type='wallet_to_wallet',channel='direct_wallet',agent_id='',serviced_wallet='',agent_flow_direction='none')

def fixture_db(attestation=True):
    from database import DatabaseAdapter
    from canonical_history_store import migrate,create_scope,attest
    from canonical_history_journal import ensure
    from canonical_mobile_money_store import migrate as cmigrate,persist
    from canonical_mobile_money import event_from_dict
    db=sqlite3.connect(':memory:');db.row_factory=sqlite3.Row
    c=DatabaseAdapter(db,'sqlite')
    c.execute('CREATE TABLE transactions (id INTEGER PRIMARY KEY,sender_account TEXT,receiver_account TEXT,amount REAL,transaction_type TEXT,currency TEXT,channel TEXT,timestamp TEXT,status TEXT,agent_id INTEGER,risk_score REAL,description TEXT)')
    cmigrate(c);migrate(c);ensure(c,apply=True)
    # Hand-authored observation scope; never written to MySQL.
    from canonical_history import boundary
    scope=boundary('controlled-prototype-v1','2026-08-31T00:00:00.000000Z',0,'hand-fixture','test-only')
    scope.update(preexisting_parent_ids=[],preexisting_change_ids=[])
    c.execute('INSERT INTO cmm_observation_scopes VALUES (?,?,?)',(scope['scope_id'],1,json.dumps(scope)))
    raw=event()
    c.execute('INSERT INTO transactions(id,sender_account,receiver_account,amount,transaction_type,currency,channel,timestamp,status) VALUES (?,?,?,?,?,?,?,?,?)',(1,'A','B',1,'transfer','USD','mobile',raw['event_timestamp'],'fixture'))
    persist(c,event_from_dict(raw))
    if attestation: attest(c,scope['scope_id'],'hand-fixture','test-only')
    c.commit()
    return c

def test_success_contract_cold_start(model):
    c=fixture_db()
    from canonical_history_store import latest
    a=latest(c,'controlled-prototype-v1')
    assert all(e['status']=='TRUE_COLD_START_VERIFIED' for e in a['entities'].values())
    c.rollback()
    out=s.infer(lambda:c,1)
    assert out['status']=='success' and out['model_sha256']==s.MODEL_SHA
    assert out['model_version']==s.MODEL_VERSION and out['feature_version']=='v4.features.1'
    assert out['threshold']==.5 and out['prediction']==int(out['suspicious_probability']>=.5)
    assert out['warning']==s.WARNING and out['history_status']=='COMPLETE_VERIFIED'
    assert out['transaction_id']=='1' and out['scope_revision']==1
    json.dumps(out,allow_nan=False)

@pytest.mark.parametrize('kind',['unknown','incomplete','stale_source','stale_scope','trigger_missing','graph_missing'])
def test_history_failures_no_model(monkeypatch,kind):
    c=fixture_db(attestation=kind!='unknown')
    if kind=='incomplete': c.execute('DELETE FROM canonical_mobile_money_events WHERE transaction_id=1')
    if kind in ('stale_source','graph_missing'):
        c.execute("INSERT INTO transactions(id,sender_account,receiver_account,amount,transaction_type,currency,timestamp) VALUES (2,'C','D',1,'transfer','USD','2026-09-01T01:00:00.000000Z')")
        if kind=='stale_source':
            from canonical_mobile_money_store import persist
            from canonical_mobile_money import event_from_dict
            persist(c,event_from_dict(event(2,'2026-09-01T01:00:00.000000Z','C','D')))
    if kind=='stale_scope':
        from canonical_history_store import revise_scope
        revise_scope(c,'controlled-prototype-v1','fixture','revision test')
    if kind=='trigger_missing': c.execute('DROP TRIGGER cmm_tx_insert')
    c.commit()
    def forbidden(): pytest.fail('Model loaded despite failed history gate')
    monkeypatch.setattr(s,'FrozenModel',forbidden)
    result=s.infer(lambda:c,1)
    assert result['status']=='inference_error' and result['error_code']=='HISTORY_INCOMPLETE'
    assert result['prediction'] is None and result['suspicious_probability'] is None

@pytest.mark.parametrize('p,pred',[(.499999,0),(.5,1),(.500001,1)])
def test_threshold(p,pred): assert s.probability_decision(p)[0]==pred

@pytest.mark.parametrize('p',[float('nan'),float('inf'),-1,1.01])
def test_invalid_probability(p):
    with pytest.raises(s.Failure): s.probability_decision(p)

@pytest.mark.parametrize('kind',['path','hash','runtime','source','version'])
def test_preload_rejections(monkeypatch,kind):
    import joblib
    original=s.authority
    a=original()
    if kind=='path': a['artifacts']['pipeline']['path']='ml_v4/development_training/artifacts/primary_HGB_EXPERIMENTAL.joblib'
    if kind=='hash': a['artifacts']['pipeline']['sha256']='0'*64
    if kind=='source': a['artifacts']['extractor_source']['sha256']='0'*64
    if kind=='version': a['freeze_id']='wrong'
    if kind=='runtime': a['python']='0.0.0'
    monkeypatch.setattr(s,'authority',lambda:a)
    monkeypatch.setattr(joblib,'load',lambda *a,**k:pytest.fail('Deserialization before validation'))
    with pytest.raises(s.Failure): s.FrozenModel()

def test_schema_nan_and_sentinels(model):
    x,e=model.replay([event()],1)
    assert x.dtype.names==model.names and len(x.dtype.names)==40
    assert math.isnan(x[model.names[23]][0])
    assert x['wallet_activity_acceleration_1h'][0]==-1
    assert x['agent_cash_value_skew_change'][0]==-3
    assert model.pre.transform(x).shape==(1,42)
    for value in (np.nan,np.inf,-2):
        bad=x.copy();bad['wallet_count_1h']=value
        with pytest.raises(s.Failure): model.predict(bad)
    bad=np.zeros(1,dtype=[('bad','f8')])
    with pytest.raises(s.Failure): model.predict(bad)
    bad=x.copy();bad['agent_cash_value_skew_change']=-2
    s.validate_features(bad,model.names,model.markers)
    bad[model.names[23]]=-1
    raw,_=model.pre.raw(bad)
    assert raw[0,model.pre.output_columns_.index(model.names[23])]==-1

def test_replay_future_order_private(model):
    a=event();b=event(2);c=event(3,'2026-09-02T00:00:00.000000Z')
    x,_=model.replay([a,b],2);y,_=model.replay([a,b,c],2)
    assert x.tobytes()==y.tobytes() and x['wallet_count_1h'][0]==2
    for rows in ([b,a],[a,a],[{**a,'private':'bad'}],[{**a,'amount_minor':1.5}]):
        with pytest.raises(s.Failure): model.replay(rows,1)

def test_model_error_never_normal(monkeypatch):
    c=fixture_db()
    monkeypatch.setattr(s.FrozenModel,'predict',lambda *a:(_ for _ in ()).throw(RuntimeError('private internal')))
    out=s.infer(lambda:c,1)
    assert out['decision']=='inference_error' and out['prediction'] is None
    assert 'private internal' not in json.dumps(out)

def test_preprocessing_single_pass(model,monkeypatch):
    x,_=model.replay([event()],1);count=[];original=model.pre.transform
    def transform(x): count.append(1);return original(x)
    monkeypatch.setattr(model.pre,'transform',transform)
    p=model.predict(x)
    assert len(count)==1 and 0<=p<=1

def test_connection_cleanup_error(monkeypatch):
    from ml_v4.frozen_inference import history
    class Bad:
        def rollback(self): raise RuntimeError('private cleanup error')
        def close(self): pass
    monkeypatch.setattr(history,'verified_snapshot',lambda *a:(_ for _ in ()).throw(s.Failure('HISTORY_INCOMPLETE')))
    out=s.infer(Bad,1)
    assert out['decision']=='inference_error' and out['prediction'] is None
    assert out['error_code']=='HISTORY_UNAVAILABLE'

def test_estimator_invalid_output(model,monkeypatch):
    x,_=model.replay([event()],1)
    monkeypatch.setattr(model.est,'predict_proba',lambda x:np.array([[0,np.nan]]))
    with pytest.raises(s.Failure,match='INFERENCE_ERROR'):model.predict(x)

def test_class_one_meaning_no_blending(model,monkeypatch):
    x,_=model.replay([event()],1)
    monkeypatch.setattr(model.est,'predict_proba',lambda x:np.array([[.8,.2]]))
    assert model.predict(x)==.2
    monkeypatch.setattr(model.est,'predict_proba',lambda x:np.array([[.5,.5]]))
    assert s.probability_decision(model.predict(x))==(1,'suspicious_pattern')

def test_resource_exhaustion_no_prediction(monkeypatch):
    c=fixture_db()
    monkeypatch.setattr(s.FrozenModel,'replay',lambda *a:(_ for _ in ()).throw(MemoryError()))
    out=s.infer(lambda:c,1)
    assert out['error_code']=='HISTORY_RESOURCE_EXHAUSTED' and out['prediction'] is None

def test_concurrent_request_local_replay():
    from concurrent.futures import ThreadPoolExecutor
    def call(_): return s.infer(fixture_db,1)
    with ThreadPoolExecutor(max_workers=2) as pool:
        a,b=list(pool.map(call,range(2)))
    assert a['status']==b['status']=='success'
    assert a['suspicious_probability']==b['suspicious_probability']
    assert a['inference_id']!=b['inference_id']

def test_saved_parity(model):
    import joblib
    standalone=joblib.load(io.BytesIO(s.verified_bytes(s.authority()['artifacts']['standalone_fitted_preprocessor'])))
    before=json.loads((s.ROOT/'ml_v4/evidence/integration_stage3/before_sha256.json').read_text())
    records=[]
    for part,count in [('train',60000),('validation',15000)]:
        xp=f'ml_v4/development_features/matrices/{part}/X.npy'
        pp=f'ml_v4/development_training/artifacts/primary_XGB_{part}_probabilities.npy'
        for path in (xp,pp):
            assert hashlib.sha256((s.ROOT/path).read_bytes()).hexdigest()==before[path]
        x=np.load(s.ROOT/xp,allow_pickle=False,mmap_mode='r')
        saved=np.load(s.ROOT/pp,allow_pickle=False,mmap_mode='r')
        indices=np.linspace(0,count-1,64,dtype=int)
        rows=x[indices]
        assert np.array_equal(model.pre.transform(rows),standalone.transform(rows))
        predicted=np.array([model.predict(rows[i:i+1]) for i in range(64)])
        expected=saved[indices]
        if expected.ndim==2:expected=expected[:,1]
        delta=float(np.max(np.abs(predicted-expected)))
        assert delta<=1e-12
        assert np.array_equal(predicted,model.pipeline.predict_proba(rows)[:,1])
        records.append(dict(partition=part,indices=indices.tolist(),max_absolute_probability_difference=delta,tolerance=1e-12,preprocessing_exact=True))
    (s.ROOT/'ml_v4/evidence/integration_stage3/parity.json').write_text(json.dumps(records,indent=2)+'\n')

def test_restart(model):
    code="from ml_v4.frozen_inference.service import FrozenModel; import json; m=FrozenModel(); e="+repr(event())+"; x,_=m.replay([e],1); print(json.dumps({'features':x.tobytes().hex(),'p':m.predict(x)}))"
    first=subprocess.check_output([sys.executable,'-B','-c',code],cwd=s.ROOT,text=True)
    second=subprocess.check_output([sys.executable,'-B','-c',code],cwd=s.ROOT,text=True)
    assert first==second

def test_no_prohibited_imports_and_preservation():
    banned=('stage16r_loader','stage16r_evaluator','run_stage17','run_stage18','ai_core','ai_stage14_model','experimental_v3','stage16r_generator')
    assert not any(any(name==b or name.endswith('.'+b) for b in banned) for name in sys.modules)
    hashes=json.loads((s.ROOT/'ml_v4/evidence/integration_stage3/before_sha256.json').read_text())
    assert all(hashlib.sha256((s.ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())

# Execute unchanged hand-authored Stage17 function bodies only. Exclude loader
# tests and the mixed private/loader test to avoid importing partition loaders.
tree=ast.parse((s.ROOT/'ml_v4/development_features/tests/test_features.py').read_text())
excluded={'test_access','test_private_fields_rejected','test_loader_resolved_escape_rejected'}
functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name not in excluded]
_,contract,extractor,_=s.sources()
namespace=dict(__file__=__file__,pytest=pytest,math=math,Extractor=extractor.Extractor,NAMES=extractor.NAMES,
    Event=contract.Event,DAY=contract.DAY,HOUR=contract.HOUR,timestamp=contract.timestamp,event_from_row=contract.event_from_row)
exec(compile(ast.Module(body=functions,type_ignores=[]),'Stage17 verified hand fixture functions','exec'),namespace)
for name,value in namespace.items():
    if name.startswith('test_'):globals()['test_stage17_'+name[5:]]=value
