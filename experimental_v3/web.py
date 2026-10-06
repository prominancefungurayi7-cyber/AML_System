"""Local test Flask/SocketIO application. No production imports or database connection."""
import hmac
import os
import secrets
from pathlib import Path
from flask import Flask, request, session, jsonify, render_template
from flask_socketio import SocketIO
from .service import Service, MANIFEST

def create_app(config=None):
    root=Path(__file__).resolve().parents[1]
    app=Flask(__name__,template_folder=str(root/'templates'),static_folder=str(root/'static'))
    app.config.update(SECRET_KEY=secrets.token_hex(32),AML_EXPERIMENTAL_MODEL=os.getenv('AML_EXPERIMENTAL_MODEL','OFF'),EXPERIMENTAL_TOKEN=os.getenv('AML_EXPERIMENTAL_TOKEN',''),MAX_CONTENT_LENGTH=2*1024*1024,SESSION_COOKIE_NAME='v3_test_session',SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Strict')
    if config: app.config.update(config)
    mode=app.config['AML_EXPERIMENTAL_MODEL']
    if mode not in ('OFF','V3'): raise ValueError('AML_EXPERIMENTAL_MODEL must be OFF or V3.')
    if mode=='V3' and len(app.config['EXPERIMENTAL_TOKEN'])<32: raise ValueError('Set a separate AML_EXPERIMENTAL_TOKEN of at least 32 characters.')
    socketio=SocketIO(app,async_mode='threading',cors_allowed_origins=None,logger=False,engineio_logger=False)
    app.extensions['v3_socketio']=socketio
    service=None; unavailable=None
    if mode=='V3':
        try: service=Service()
        except Exception as exc: unavailable=str(exc)
    app.extensions['v3_service']=service

    def local():
        return request.remote_addr in ('127.0.0.1','::1') and request.host.split(':')[0] in ('127.0.0.1','localhost') and not any(k in request.headers for k in ('Forwarded','X-Forwarded-For','X-Forwarded-Host'))

    def authorized():
        token=request.headers.get('Authorization','')
        return (token.startswith('Bearer ') and hmac.compare_digest(token[7:],app.config['EXPERIMENTAL_TOKEN'])) or (session.get('v3_role')=='tester' and hmac.compare_digest(request.headers.get('X-V3-CSRF',''),session.get('v3_csrf','!')))

    @app.before_request
    def guard():
        if not local(): return jsonify(status='error',error='Experimental testing is loopback-only; proxies are not allowed.'),403
        if mode!='V3': return jsonify(status='error',error='V3 experimental mode is OFF.'),404
        origin=request.headers.get('Origin')
        if origin and origin!=request.host_url.rstrip('/'): return jsonify(status='error',error='Cross-origin request denied.'),403
        if request.path.startswith('/api/') and not authorized(): return jsonify(status='error',error='Local tester authorization required.'),401

    @app.after_request
    def headers(response):
        response.headers['Cache-Control']='no-store'; response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'; response.headers['Referrer-Policy']='no-referrer'
        return response

    @app.get('/')
    @app.get('/experimental/v3')
    def dashboard(): return render_template('experimental_v3.html')

    @app.post('/experimental/v3/login')
    def login():
        body=request.get_json(silent=True)
        if not isinstance(body,dict) or set(body)!={'token'} or not isinstance(body['token'],str) or not hmac.compare_digest(body['token'],app.config['EXPERIMENTAL_TOKEN']): return jsonify(status='error',error='Invalid tester token.'),401
        session.clear();session['v3_role']='tester';session['v3_csrf']=secrets.token_hex(32)
        return jsonify(status='success',csrf=session['v3_csrf'])

    @app.get('/api/experimental/v3/status')
    def status(): return jsonify(model_version='V3',mode='EXPERIMENTAL',model_loaded=service is not None,feature_compatibility='32 frozen float64 fields; explicit observable synthetic payload required',threshold=MANIFEST['threshold'],candidate=MANIFEST['candidate'],error=unavailable)

    @app.post('/api/experimental/v3/predict')
    def predict():
        if service is None: return jsonify(status='error',features_valid=False,error=unavailable),503
        body=request.get_json(silent=True)
        if not isinstance(body,dict) or set(body) not in ({'transaction','prior_history','synthetic'},{'transactions','prior_history','synthetic'}) or body['synthetic'] is not True: return jsonify(status='error',features_valid=False,error='Provide synthetic:true, transaction or transactions, and explicit prior_history.'),400
        try: result=service.predict(body.get('transactions',[body.get('transaction')]),body['prior_history'])
        except (ValueError,TypeError,KeyError,OverflowError) as exc: return jsonify(status='error',features_valid=False,error=str(exc)),400
        # Response is caller-local. Socket updates are sent only on the authenticated test socket.
        return jsonify(status='success',predictions=result)

    @socketio.on('connect',namespace='/experimental-v3')
    def connect(auth):
        if mode!='V3' or not local() or session.get('v3_role')!='tester' or not isinstance(auth,dict) or not hmac.compare_digest(str(auth.get('csrf','')),session.get('v3_csrf','!')): return False

    @socketio.on('experimental_v3_predict',namespace='/experimental-v3')
    def socket_predict(body):
        if not local() or session.get('v3_role')!='tester' or service is None: return
        try:
            if not isinstance(body,dict) or set(body)!={'transactions','prior_history','synthetic'} or body['synthetic'] is not True: raise ValueError('Invalid synthetic batch envelope.')
            result={'status':'success','predictions':service.predict(body['transactions'],body['prior_history'])}
        except (ValueError,TypeError,KeyError,OverflowError) as exc: result={'status':'error','features_valid':False,'error':str(exc)}
        socketio.emit('experimental_v3_prediction',result,to=request.sid,namespace='/experimental-v3')
    return app

def main():
    app=create_app()
    app.extensions['v3_socketio'].run(app,host='127.0.0.1',port=5053,debug=False,use_reloader=False,allow_unsafe_werkzeug=True)

if __name__=='__main__': main()
