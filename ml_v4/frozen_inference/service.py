"""Trusted local API. Own a dedicated process/environment; no web routes or fits."""
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import sys
import threading
from datetime import datetime, timezone
import uuid

ROOT=Path(__file__).resolve().parents[2]
MODEL_PATH='ml_v4/development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib'
MODEL_SHA='555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18'
MODEL_VERSION='v4.development.freeze.stage23.1'
FEATURE_VERSION='v4.features.1'
THRESHOLD=0.50
WARNING='This model identifies transaction patterns defined as suspicious within the synthetic research benchmark. It does not determine that money laundering has occurred.'
LOCK=threading.RLock()
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name]='1'

class Failure(Exception):
    def __init__(self,code): self.code=code; super().__init__(code)

def utc(): return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z')

def authority():
    return json.loads((Path(__file__).parent/'authority.json').read_text())

def verified_bytes(record):
    p=ROOT/record['path']
    if p.resolve()!=p.absolute() or not p.is_file(): raise Failure('MODEL_INTEGRITY')
    data=p.read_bytes()
    if hashlib.sha256(data).hexdigest()!=record['sha256']: raise Failure('MODEL_INTEGRITY')
    return data

def runtime():
    a=authority()
    try:
        actual={'python':platform.python_version(),**{p:importlib.metadata.version(p) for p in a['runtime']}}
    except importlib.metadata.PackageNotFoundError: raise Failure('MODEL_UNAVAILABLE') from None
    if actual!={'python':a['python'],**a['runtime']}: raise Failure('MODEL_UNAVAILABLE')
    expected=ROOT/'ml_v4/.venv_inference_stage3'
    if Path(sys.prefix).resolve()!=expected.resolve() or sys.prefix==sys.base_prefix:
        raise Failure('MODEL_UNAVAILABLE')
    return actual

def module(name,record):
    data=verified_bytes(record)
    path=(ROOT/record['path']).resolve()
    if name in sys.modules:
        if Path(getattr(sys.modules[name],'__file__','')).resolve()!=path:
            raise Failure('MODEL_INTEGRITY')
        return sys.modules[name]
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    sys.modules[name]=mod
    try: exec(compile(data,str(path),'exec'),mod.__dict__)
    except Exception:
        sys.modules.pop(name,None)
        raise Failure('MODEL_UNAVAILABLE') from None
    return mod

def sources():
    a=authority()
    if a['freeze_id']!=MODEL_VERSION or a['feature_version']!=FEATURE_VERSION:
        raise Failure('MODEL_INTEGRITY')
    for r in a['artifacts'].values(): verified_bytes(r)
    f=json.loads(verified_bytes(a['artifacts']['freeze']))
    if f['freeze_id']!=MODEL_VERSION or f['semantic_fields']!=40 or f['threshold']['value']!=THRESHOLD:
        raise Failure('MODEL_INTEGRITY')
    contract=module('stage16r_contract',a['artifacts']['observable_contract_source'])
    ext=module('extractor',a['artifacts']['extractor_source'])
    pre=module('preprocessing',a['artifacts']['preprocessor_source'])
    return a,contract,ext,pre

def validate_features(x,names,markers):
    import numpy as np
    expected=np.dtype([(n,'U16' if n=='transaction_type' else 'f8') for n in names])
    if x.shape!=(1,) or x.dtype!=expected or len(names)!=40: raise Failure('FEATURE_SCHEMA')
    if x['transaction_type'][0] not in ('wallet_to_wallet','cash_in','cash_out'): raise Failure('FEATURE_INVALID')
    for n in names:
        if n=='transaction_type': continue
        value=float(x[n][0])
        if np.isinf(value) or (np.isnan(value) and n!='wallet_prior_funding_residual_minor_24h'): raise Failure('FEATURE_INVALID')
        if np.isnan(value): continue
        if n=='wallet_prior_funding_residual_minor_24h': continue
        if n=='agent_top2_share_change_24h': valid=value==-3 or -1<=value<=1
        elif n=='agent_cash_value_skew_change': valid=value==-3 or -2<=value<=2
        else: valid=value>=0 or value==markers.get(n)
        if not valid: raise Failure('FEATURE_INVALID')

def probability_decision(p):
    import math
    if type(p) not in (int,float) or not math.isfinite(p) or not 0<=p<=1: raise Failure('INFERENCE_ERROR')
    return int(p>=THRESHOLD),'suspicious_pattern' if p>=THRESHOLD else 'normal'

class FrozenModel:
    """No path argument, fallback or fitting. Model bytes verified before load."""
    def __init__(self):
        with LOCK:
            self.runtime=runtime()
            a,self.contract,self.extractor,pre=sources()
            record=a['artifacts']['pipeline']
            if record!={'path':MODEL_PATH,'sha256':MODEL_SHA}: raise Failure('MODEL_INTEGRITY')
            import joblib
            import numpy as np
            from sklearn.pipeline import Pipeline
            from xgboost import XGBClassifier
            # Distribution versions alone do not reject a shadowed import.
            import numpy,sklearn,xgboost,scipy,joblib,threadpoolctl,narwhals
            site=(Path(sys.prefix)/'Lib/site-packages').resolve()
            if any(not Path(m.__file__).resolve().is_relative_to(site) for m in (numpy,sklearn,xgboost,scipy,joblib,threadpoolctl,narwhals)):
                raise Failure('MODEL_INTEGRITY')
            try:
                self.pipeline=joblib.load(io.BytesIO(verified_bytes(record)))
                if type(self.pipeline) is not Pipeline or list(self.pipeline.named_steps)!=['preprocess','model']: raise Failure('MODEL_INTEGRITY')
                self.pre=self.pipeline.named_steps['preprocess']; self.est=self.pipeline.named_steps['model']
                ps=json.loads(verified_bytes(a['artifacts']['preprocessing_specification']))
                self.names=tuple(self.extractor.NAMES); self.markers=ps['markers_to_missing']
                if (type(self.pre) is not pre.FrozenPreprocessor or tuple(self.pre.names)!=self.names or
                    self.pre.mode!='full' or self.pre.dropped is not None or self.pre.only is not None or
                    self.pre.markers!=self.markers or self.pre.output_columns_!=ps['columns'] or
                    len(self.names)!=40 or len(self.pre.output_columns_)!=42 or
                    type(self.est) is not XGBClassifier or self.est.n_features_in_!=42 or
                    list(self.est.classes_)!=[0,1] or not callable(self.est.predict_proba)):
                    raise Failure('MODEL_INTEGRITY')
                params=self.est.get_params()
                for key,val in a['configuration'].items():
                    if val is not None and params.get(key)!=val: raise Failure('MODEL_INTEGRITY')
                if self.pre.n_train_rows_!=60000 or self.pre.imputer_.statistics_.shape!=(42,) or self.pre.scaler_.scale_.shape!=(42,): raise Failure('MODEL_INTEGRITY')
                if not all(np.isfinite(v).all() for v in (self.pre.imputer_.statistics_,self.pre.scaler_.mean_,self.pre.scaler_.scale_)): raise Failure('MODEL_INTEGRITY')
            except Failure: raise
            except Exception: raise Failure('MODEL_UNAVAILABLE') from None

    def replay(self,events,tx):
        import numpy as np
        state=self.extractor.Extractor()
        seen=set();last=None; current=None
        try:
            # Validate entire supplied snapshot order, even later events; never sort away an error.
            validated=[]
            for raw in events:
                if set(raw)!=set(self.contract.FIELDS): raise Failure('INVALID_EVENT')
                e=self.contract.Event(**raw)
                self.contract.validate_event(e)
                if e.transaction_id in seen or (last is not None and e.key<=last): raise Failure('HISTORY_INCOMPLETE')
                seen.add(e.transaction_id);last=e.key;validated.append(e)
                if e.transaction_id==tx: current=e
            if current is None: raise Failure('EVENT_UNAVAILABLE')
            for e in validated:
                if e.key>current.key: break
                row=state.step(e)
            x=np.array([tuple(row)],dtype=[(n,'U16' if n=='transaction_type' else 'f8') for n in self.names])
            validate_features(x,self.names,self.markers)
            return x,current
        except Failure: raise
        except MemoryError: raise Failure('HISTORY_RESOURCE_EXHAUSTED') from None
        except Exception: raise Failure('FEATURE_INVALID') from None

    def predict(self,x):
        import numpy as np
        from threadpoolctl import threadpool_limits
        validate_features(x,self.names,self.markers)
        with LOCK,threadpool_limits(limits=1):
            try:
                # Embedded saved transform exactly once; inspect its output before estimator.
                encoded=self.pre.transform(x)
                if encoded.shape!=(1,42) or not np.isfinite(encoded).all(): raise Failure('PREPROCESSING_ERROR')
            except Failure: raise
            except Exception: raise Failure('PREPROCESSING_ERROR') from None
            try:
                if list(self.est.classes_)!=[0,1]: raise Failure('MODEL_INTEGRITY')
                values=self.est.predict_proba(encoded)
                if values.shape!=(1,2) or not np.isfinite(values).all() or (values<0).any() or (values>1).any(): raise Failure('INFERENCE_ERROR')
                if not np.isclose(values.sum(),1,atol=1e-6): raise Failure('INFERENCE_ERROR')
                p=float(values[0,list(self.est.classes_).index(1)])
                probability_decision(p)
                return p
            except Failure: raise
            except Exception: raise Failure('INFERENCE_ERROR') from None

def result(tx):
    return dict(contract_version='v4.inference.1',status='inference_error',inference_id=str(uuid.uuid4()),
        transaction_id=str(tx) if type(tx) is int else None,event_timestamp=None,model_version=MODEL_VERSION,
        model_sha256=MODEL_SHA,feature_version=FEATURE_VERSION,prediction=None,suspicious_probability=None,
        threshold=THRESHOLD,decision='inference_error',inference_timestamp=utc(),observation_scope=None,
        scope_revision=None,source_revision=None,history_status='UNKNOWN',history_complete_through=None,
        error_code=None,warning=WARNING,human_review_required=False,
        normal_result_limitation='A normal result does not certify that a transaction is legitimate.')

def infer(connection_factory,transaction_id):
    """Caller-owned trusted factory, never browser parameters. Read-only DB snapshot.

    Opens/closes its own connection. No attestation refresh, database writes,
    inference persistence, operational routing, or automatic alert creation.
    """
    out=result(transaction_id)
    c=None
    try:
        if type(transaction_id) is not int or not 0<transaction_id<2**63: raise Failure('INVALID_EVENT')
        from ml_v4.frozen_inference.history import verified_snapshot
        c=connection_factory()
        events,context=verified_snapshot(c,transaction_id)
        out.update(context)
        model=FrozenModel()
        x,event=model.replay(events,transaction_id)
        out['event_timestamp']=event.event_timestamp
        p=model.predict(x)
        pred,decision=probability_decision(p)
        out.update(status='success',prediction=pred,suspicious_probability=p,decision=decision,human_review_required=bool(pred))
    except Failure as exc: out['error_code']=exc.code
    except MemoryError: out['error_code']='HISTORY_RESOURCE_EXHAUSTED'
    except Exception: out['error_code']='INFERENCE_ERROR'
    finally:
        if c is not None:
            try:
                try: c.rollback()
                finally: c.close()
            except Exception:
                out.update(status='inference_error',prediction=None,suspicious_probability=None,
                    decision='inference_error',error_code='HISTORY_UNAVAILABLE',human_review_required=False)
        out['inference_timestamp']=utc()
    return out
