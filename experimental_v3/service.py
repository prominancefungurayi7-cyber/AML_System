"""Verified frozen V3 inference; no fit methods, persistence or financial operations."""
import hashlib
import importlib
import json
import re
import sys
import threading
import warnings
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import joblib
import sklearn
from sklearn.exceptions import InconsistentVersionWarning
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=json.loads((Path(__file__).parent/'manifest.json').read_text())
FIELDS={'transaction_id','event_timestamp','sender_wallet','receiver_wallet','amount_minor','currency','transaction_type','channel','agent_id','serviced_wallet','agent_flow_direction'}
LOCK=threading.Lock()

def key(row): return datetime.fromisoformat(row['event_timestamp'].replace('Z','+00:00')),row['transaction_id']

def validate(row):
    if not isinstance(row,dict) or set(row)!=FIELDS: raise ValueError('Exactly the documented observable fields are required; labels, scores and extra fields are forbidden.')
    for name in ('transaction_id','amount_minor'):
        if type(row[name]) is not int or not 0<row[name]<2**53: raise ValueError(name+' must be a positive exact integer below 2^53.')
    if not isinstance(row['event_timestamp'],str): raise ValueError('UTC event_timestamp required.')
    try: dt=datetime.fromisoformat(row['event_timestamp'].replace('Z','+00:00'))
    except ValueError: raise ValueError('Invalid timestamp.') from None
    if dt.tzinfo is None or dt.utcoffset().total_seconds()!=0: raise ValueError('Timestamp must explicitly use UTC.')
    for name in ('sender_wallet','receiver_wallet'):
        if not isinstance(row[name],str) or not re.fullmatch(r'test_[A-Za-z0-9_-]{1,60}',row[name]): raise ValueError('Only synthetic test_ wallet identifiers are allowed.')
    if row['currency']!='USD': raise ValueError('Only synthetic USD integer cents supported.')
    typ=row['transaction_type']; agent=row['agent_id']; serviced=row['serviced_wallet']
    if not isinstance(agent,str) or not isinstance(serviced,str): raise ValueError('Agent and serviced wallet must be strings, empty only for direct W2W.')
    if agent and not re.fullmatch(r'test_[A-Za-z0-9_-]{1,60}',agent): raise ValueError('Synthetic test_ agent identifier required.')
    if typ=='wallet_to_wallet':
        if row['sender_wallet']==row['receiver_wallet']: raise ValueError('W2W endpoints must differ.')
        if row['agent_flow_direction']!='none': raise ValueError('W2W has no agent cash flow.')
        if row['channel']=='direct_wallet':
            if agent or serviced: raise ValueError('Direct W2W must have no agent service.')
        elif row['channel']=='agent':
            if not agent or serviced not in (row['sender_wallet'],row['receiver_wallet']): raise ValueError('Assisted W2W requires an explicit serviced endpoint.')
        else: raise ValueError('Invalid W2W channel.')
    elif typ in ('cash_in','cash_out'):
        if not agent or row['channel']!='agent' or row['sender_wallet']!=row['receiver_wallet'] or serviced!=row['sender_wallet'] or row['agent_flow_direction']!=typ: raise ValueError('Invalid cash role, channel or flow.')
    else: raise ValueError('Unsupported transaction_type.')
    return row

class Service:
    def __init__(self):
        for p,h in MANIFEST['sha256'].items():
            if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h: raise RuntimeError('Frozen artifact or pipeline integrity mismatch: '+p)
        if sklearn.__version__!=MANIFEST['sklearn']: raise RuntimeError('V3 requires verified scikit-learn '+MANIFEST['sklearn'])
        src=str(ROOT/'ml_v3/src')
        if src not in sys.path: sys.path.insert(0,src)
        self.pipeline=importlib.import_module('stage10a_pipeline'); self.contract=importlib.import_module('stage10a_contract')
        for module in (self.pipeline,self.contract,importlib.import_module('stage11_preprocessing')):
            if Path(module.__file__).resolve().parent!=Path(src): raise RuntimeError('Unexpected frozen module source.')
        plan=json.loads((ROOT/'ml_v3/reports/stage11_search_plan.json').read_text())
        if plan['threshold']!=MANIFEST['threshold'] or plan['feature_version']!=self.contract.VERSION: raise RuntimeError('Threshold or schema provenance mismatch.')
        with warnings.catch_warnings():
            warnings.simplefilter('error',InconsistentVersionWarning)
            self.model=joblib.load(ROOT/MANIFEST['artifact'])
        if self.model.n_features_in_!=32 or list(self.model.classes_)!=[0,1] or self.model.named_steps['preprocessing'].mode!='raw': raise RuntimeError('Unexpected saved model schema.')
        self.names=self.contract.NAMES

    def predict(self,transactions,prior_history):
        if not isinstance(transactions,list) or not 1<=len(transactions)<=100: raise ValueError('transactions must contain 1..100 synthetic rows.')
        if not isinstance(prior_history,list) or len(prior_history)>2000: raise ValueError('prior_history must explicitly be a list of at most 2000 rows; [] declares an actual cold start.')
        rows=[validate(r) for r in prior_history+transactions]
        if len({r['transaction_id'] for r in rows})!=len(rows): raise ValueError('Duplicate transaction IDs.')
        if any(key(a)>=key(b) for a,b in zip(transactions,transactions[1:])): raise ValueError('Batch must be increasing by UTC timestamp then integer ID.')
        if any(key(r)>=key(transactions[0]) for r in prior_history): raise ValueError('History must be strictly prior, including equal-time ID ordering.')
        # Frozen extractor sorts full keys and emits before updating. No truncation or V4 substitutions.
        with LOCK,threadpool_limits(limits=1):
            ids,values=self.pipeline.extract(rows)
            matrix=np.asarray(values,dtype=np.float64)
            if matrix.shape!=(len(rows),32) or not np.isfinite(matrix).all(): raise ValueError('Frozen feature schema failed.')
            indices={int(i):n for n,i in enumerate(ids)}
            selected=matrix[[indices[r['transaction_id']] for r in transactions]]
            probabilities=self.model.predict_proba(selected)[:,1]
        return [{'model_version':'V3','candidate':MANIFEST['candidate'],'mode':'EXPERIMENTAL','prediction':int(p>=MANIFEST['threshold']),'confidence':float(p),'probability_meaning':'Estimated synthetic suspicious-pattern class probability; not probability of laundering.','threshold':MANIFEST['threshold'],'features_valid':True,'status':'success','transaction_reference':r['transaction_id'],'timestamp':r['event_timestamp'],'unavailable_features':[name for name,value,spec in zip(self.names,x,self.contract.FEATURES) if spec[7] is not None and value==spec[7]],'test_alert':'EXPERIMENTAL — NOT A PRODUCTION AML ALERT' if p>=MANIFEST['threshold'] else None,'explanation':'No per-transaction model explanation is available.','observable':{k:r[k] for k in ('transaction_type','amount_minor','channel')}} for r,x,p in zip(transactions,selected,probabilities)]

def predict_v3(transaction,prior_history):
    return Service().predict([transaction],prior_history)[0]
