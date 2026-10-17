"""Shadow coordinator: standard library only; never imports V4 ML packages."""
import json
import math
import re
import os
from pathlib import Path
import subprocess
import threading
import time
import uuid
import hashlib
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parent
PYTHON=ROOT/'ml_v4/.venv_inference_stage3/Scripts/python.exe'
LAUNCHER=ROOT/'ml_v4/shadow_integration/worker.py'
MODEL='v4.development.freeze.stage23.1'
FEATURE='v4.features.1'
SHA='555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18'
TABLE='v4_shadow_results'
TIMEOUT=60
MAX_OUTPUT=16384
ERROR_CODES={'MODEL_INTEGRITY','MODEL_UNAVAILABLE','HISTORY_INCOMPLETE','EVENT_UNAVAILABLE',
    'INVALID_EVENT','FEATURE_SCHEMA','FEATURE_INVALID','PREPROCESSING_ERROR','INFERENCE_ERROR',
    'RESOURCE_ERROR','HISTORY_RESOURCE_EXHAUSTED','HISTORY_UNAVAILABLE'}
WARNING='This model identifies transaction patterns defined as suspicious within the synthetic research benchmark. It does not determine that money laundering has occurred.'

def now(): return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z')
def enabled(): return os.environ.get('V4_SHADOW_ENABLED','OFF')=='ON'

def error(tx,code):
    return dict(contract_version='v4.inference.1',inference_id=str(uuid.uuid4()),transaction_id=str(tx),
        model_version=MODEL,model_sha256=SHA,feature_version=FEATURE,threshold=.5,status='inference_error',
        prediction=None,suspicious_probability=None,decision='inference_error',error_code=code,
        inference_timestamp=now(),event_timestamp=None,observation_scope=None,scope_revision=None,
        source_revision=None,history_status='UNKNOWN',history_complete_through=None)

def validate(data,tx):
    if type(data) is not dict: raise ValueError('Invalid result')
    required=set(error(tx,'CHECK'))
    if not required.issubset(data): raise ValueError('Missing result fields')
    if (data['transaction_id']!=str(tx) or data['model_version']!=MODEL or data['feature_version']!=FEATURE or
        data['model_sha256']!=SHA or data['threshold']!=.5 or data['contract_version']!='v4.inference.1'):
        raise ValueError('Contract mismatch')
    uuid.UUID(data['inference_id'])
    for field in ('inference_timestamp',):
        if not isinstance(data[field],str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z',data[field]):raise ValueError('Timestamp')
        datetime.fromisoformat(data[field].replace('Z','+00:00'))
    if data['status']=='success':
        p=data['suspicious_probability']
        if type(p) not in (float,int) or not math.isfinite(p) or not 0<=p<=1:raise ValueError('Probability')
        if type(data['prediction']) is not int or data['prediction']!=int(p>=.5):raise ValueError('Prediction')
        if data['decision']!=('suspicious_pattern' if p>=.5 else 'normal') or data['error_code'] is not None:raise ValueError('Decision')
        if (data['history_status']!='COMPLETE_VERIFIED' or data['observation_scope']!='controlled-prototype-v1' or
            not isinstance(data['source_revision'],str) or not re.fullmatch('[0-9a-f]{64}',data['source_revision']) or
            type(data['scope_revision']) is not int or data['scope_revision']<1 or not data['event_timestamp'] or
            type(data['history_complete_through']) is not dict):raise ValueError('History')
    elif data['status']=='inference_error':
        if data['prediction'] is not None or data['suspicious_probability'] is not None or data['decision']!='inference_error':raise ValueError('Failure')
        if data['error_code'] not in ERROR_CODES:raise ValueError('Error')
    else:raise ValueError('Status')
    # Store only the declared fields; never accept child-added private payloads.
    result={k:data[k] for k in required}
    json.dumps(result,allow_nan=False)
    return result

def invoke(tx,source_digest,server_uuid):
    if type(tx) is not int or not 0<tx<2**63:return error(tx,'INVALID_EVENT')
    try:
        child=subprocess.Popen([str(PYTHON),'-I','-B',str(LAUNCHER),'--transaction-id',str(tx),
            '--source-digest',source_digest,'--server-uuid',server_uuid],
            cwd=str(ROOT),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            shell=False,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    except OSError:return error(tx,'MODEL_UNAVAILABLE')
    buffers={};too_large=threading.Event()
    def read(name,stream):
        data=stream.read(MAX_OUTPUT+1);buffers[name]=data
        if len(data)>MAX_OUTPUT:
            too_large.set()
            child.kill()
    threads=[threading.Thread(target=read,args=(name,stream),daemon=True) for name,stream in [('out',child.stdout),('err',child.stderr)]]
    for thread in threads:thread.start()
    try:child.wait(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        child.kill();child.wait()
        for thread in threads:thread.join(timeout=2)
        child.stdout.close();child.stderr.close()
        return error(tx,'RESOURCE_ERROR')
    for thread in threads:thread.join(timeout=2)
    child.stdout.close();child.stderr.close()
    if too_large.is_set() or any(t.is_alive() for t in threads):return error(tx,'RESOURCE_ERROR')
    if child.returncode!=0:return error(tx,'INFERENCE_ERROR')
    try:
        def reject_constant(_):raise ValueError('Nonfinite JSON')
        def pairs(items):
            out={}
            for k,v in items:
                if k in out:raise ValueError('Duplicate JSON key')
                out[k]=v
            return out
        return validate(json.loads(buffers['out'].decode('utf-8'),parse_constant=reject_constant,object_pairs_hook=pairs),tx)
    except (ValueError,KeyError,TypeError,UnicodeError):return error(tx,'INFERENCE_ERROR')

def migrate(c):
    """Explicit additive migration, never run from application startup."""
    mysql=c.engine=='mysql'
    if c.engine not in ('mysql','sqlite'):raise ValueError('Unsupported shadow database')
    exists=c.execute('SHOW TABLES LIKE ?', (TABLE,)).fetchone() if mysql else c.execute("SELECT name FROM sqlite_master WHERE name=? AND type='table'",(TABLE,)).fetchone()
    if exists:
        names=[r['Field'] for r in c.execute('SHOW COLUMNS FROM '+TABLE).fetchall()] if mysql else [r['name'] for r in c.execute('PRAGMA table_info('+TABLE+')').fetchall()]
        if names!=['transaction_id','model_version','feature_version','inference_id','status','prediction','suspicious_probability','threshold','decision','error_code','body','created_at']:raise ValueError('Shadow schema mismatch')
        if mysql:
            cols=c.execute('SHOW COLUMNS FROM '+TABLE).fetchall()
            if cols[0]['Type']!='bigint' or cols[7]['Type']!='decimal(3,2)':raise ValueError('Shadow types mismatch')
            index=c.execute('SHOW INDEX FROM '+TABLE).fetchall()
            pk=[r['Column_name'] for r in sorted(index,key=lambda r:r['Seq_in_index']) if r['Key_name']=='PRIMARY']
            if pk!=['transaction_id','model_version','feature_version']:raise ValueError('Shadow uniqueness mismatch')
            if not any(r['Column_name']=='inference_id' and r['Non_unique']==0 for r in index):raise ValueError('Inference ID not unique')
        return False
    integer='BIGINT' if mysql else 'INTEGER'
    text='VARCHAR(255)' if mysql else 'TEXT'
    body='LONGTEXT' if mysql else 'TEXT'
    c.execute(f'''CREATE TABLE {TABLE} (
        transaction_id {integer} NOT NULL,model_version {text} NOT NULL,feature_version {text} NOT NULL,
        inference_id {text} NOT NULL,status {text} NOT NULL,prediction INTEGER NULL,
        suspicious_probability DOUBLE NULL,threshold DECIMAL(3,2) NOT NULL,
        decision {text} NOT NULL,error_code {text} NULL,body {body} NOT NULL,created_at {text} NOT NULL,
        PRIMARY KEY(transaction_id,model_version,feature_version),UNIQUE(inference_id),
        FOREIGN KEY(transaction_id) REFERENCES canonical_mobile_money_events(transaction_id),
        CHECK(threshold=0.50),CHECK(prediction IS NULL OR prediction IN (0,1)),
        CHECK(suspicious_probability IS NULL OR suspicious_probability BETWEEN 0 AND 1),
        CHECK((status='pending' AND prediction IS NULL AND suspicious_probability IS NULL AND decision='pending') OR
              (status='inference_error' AND prediction IS NULL AND suspicious_probability IS NULL AND decision='inference_error' AND error_code IS NOT NULL) OR
              (status='success' AND prediction IS NOT NULL AND suspicious_probability IS NOT NULL AND error_code IS NULL AND
               ((prediction=1 AND suspicious_probability>=0.50 AND decision='suspicious_pattern') OR
                (prediction=0 AND suspicious_probability<0.50 AND decision='normal'))))
    )'''+(' ENGINE=InnoDB' if mysql else ''))
    return True

def get(c,tx):
    row=c.execute('SELECT body FROM '+TABLE+' WHERE transaction_id=? AND model_version=? AND feature_version=?',(tx,MODEL,FEATURE)).fetchone()
    return json.loads(row['body']) if row else None

def safe_payload(r):
    fields=('inference_id','transaction_id','status','decision','suspicious_probability','threshold','model_version','feature_version','inference_timestamp','error_code')
    return {k:r.get(k) for k in fields}

def process(connection_factory,tx,publish,runner=None,expected_source_revision=None):
    """Called only after source commit. DB key/lock deduplicate concurrent calls.

    Final successes and errors are immutable and reused. Pending rows can resume
    after a crash. A crash after prediction but before persistence can reexecute
    prediction, but cannot create two final records for the same key.
    """
    if type(tx) is not int or not 0<tx<2**63:raise ValueError('Invalid ID')
    c=connection_factory();lock=False
    try:
        if c.engine=='mysql':
            lock=c.execute('SELECT GET_LOCK(?,0) AS ok',('v4_shadow_'+str(tx),)).fetchone()['ok']==1
            if not lock:return None
        elif c.engine=='sqlite':c.execute('BEGIN IMMEDIATE')
        else:raise ValueError('Unsupported database')
        source=c.execute('SELECT * FROM canonical_mobile_money_events WHERE transaction_id=?',(tx,)).fetchone()
        if not source:
            return None
        existing=get(c,tx)
        if existing and existing['status']!='pending':return existing
        if existing is None:
            pending=error(tx,'PENDING');pending.update(status='pending',decision='pending',error_code=None)
            c.execute('INSERT INTO '+TABLE+' VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                (tx,MODEL,FEATURE,pending['inference_id'],'pending',None,None,.5,'pending',None,json.dumps(pending),now()))
        c.commit()
        try:
            if runner is None:
                if c.engine!='mysql':raise ValueError('Production shadow requires MySQL')
                server_uuid=c.execute('SELECT @@server_uuid AS id').fetchone()['id']
                digest=hashlib.sha256(json.dumps(dict(source),sort_keys=True,separators=(',',':')).encode()).hexdigest()
                r=validate(invoke(tx,digest,server_uuid),tx)
            else:r=validate(runner(tx),tx)
        except Exception:r=error(tx,'INFERENCE_ERROR')
        if expected_source_revision is not None and r['status']=='success':
            # The frozen worker verifies history in its own snapshot. Accept
            # only the exact revision attested for this committed payment.
            if r.get('source_revision') != expected_source_revision:
                r=error(tx,'HISTORY_INCOMPLETE')
            else:
                try:
                    from canonical_history_store import assess
                    from canonical_history import freshness
                    c.rollback()
                    c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
                    c.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY')
                    scope,current,previous=assess(c,'controlled-prototype-v1')
                    valid=(current['source_revision']==expected_source_revision and
                           freshness(scope,current,previous)=='COMPLETE_VERIFIED' and
                           not current['issues'])
                    c.rollback()
                    if not valid:r=error(tx,'HISTORY_INCOMPLETE')
                except Exception:
                    c.rollback()
                    r=error(tx,'HISTORY_INCOMPLETE')
        c.execute('UPDATE '+TABLE+' SET inference_id=?,status=?,prediction=?,suspicious_probability=?,decision=?,error_code=?,body=? WHERE transaction_id=? AND model_version=? AND feature_version=? AND status=?',
            (r['inference_id'],r['status'],r['prediction'],r['suspicious_probability'],r['decision'],r['error_code'],json.dumps(r,allow_nan=False),tx,MODEL,FEATURE,'pending'))
        c.commit()
        # Delivery is a best-effort notification; authorized GET is durable recovery.
        try:publish(safe_payload(r))
        except Exception:pass
        return r
    finally:
        c.rollback()
        if lock:c.execute('SELECT RELEASE_LOCK(?)',('v4_shadow_'+str(tx),))
        c.close()

def after_commit(app,connection_factory,tx,socketio):
    if not enabled():return
    try:
        process(connection_factory,tx,lambda p:publish_staff(connection_factory,socketio,p))
    except Exception:
        # Source has committed: a shadow problem must never undo or retry payment.
        app.logger.error('V4 shadow processing unavailable for transaction %s',tx)

# Single application process prototype. Explicit authenticated subscription;
# recheck current DB role on every publication. Never use the global broker.
_sockets={}
_socket_lock=threading.RLock()

def forget_user(user_id):
    with _socket_lock:
        for sid,uid in list(_sockets.items()):
            if uid==user_id:_sockets.pop(sid,None)

def forget_socket(sid):
    with _socket_lock:_sockets.pop(sid,None)

def publish_staff(factory,socketio,payload):
    c=factory()
    try:
        with _socket_lock:
            for sid,uid in list(_sockets.items()):
                row=c.execute('SELECT role FROM users WHERE id=?',(uid,)).fetchone()
                authorizer=getattr(socketio, 'aml_session_authorizer', None)
                if row and row['role'] in ('compliance','admin') and (authorizer is None or authorizer(sid)):
                    socketio.emit('v4_shadow_result',payload,to=sid)
                else:_sockets.pop(sid,None)
    finally:c.rollback();c.close()

def install(app,socketio,get_db):
    from flask import Blueprint,jsonify,session,request
    api=Blueprint('v4_shadow',__name__)
    def staff():
        uid=session.get('user_id')
        if uid is None:return False
        row=get_db().execute('SELECT role FROM users WHERE id=?',(uid,)).fetchone()
        return bool(row and row['role'] in ('compliance','admin'))
    @api.get('/api/v4-shadow/results')
    def results():
        if not staff():return jsonify({'error':'forbidden'}),403
        try:
            if request.args.get('errors') == '1':
                rows=get_db().execute('SELECT r.body FROM '+TABLE+' r JOIN transactions t '
                    "ON t.id=r.transaction_id WHERE t.ai_risk_level='inference_error' "
                    "AND r.status='inference_error' ORDER BY r.transaction_id DESC LIMIT 50").fetchall()
            else:
                rows=get_db().execute('SELECT body FROM '+TABLE+' ORDER BY transaction_id DESC LIMIT 50').fetchall()
            return jsonify({'results':[safe_payload(json.loads(r['body'])) for r in rows]})
        except Exception:return jsonify({'error':'V4 shadow storage unavailable','results':[]}),503
    @socketio.on('v4_shadow_subscribe')
    def subscribe():
        authorizer=getattr(socketio, 'aml_session_authorizer', None)
        if authorizer is not None and not authorizer(request.sid):return {'ok':False}
        if not staff():return {'ok':False}
        with _socket_lock:_sockets[request.sid]=session['user_id']
        return {'ok':True}
    app.register_blueprint(api)
