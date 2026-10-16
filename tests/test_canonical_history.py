from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import sys
import pytest

from canonical_history import boundary,verify,freshness,window_coverage,SOURCE
from canonical_history_store import migrate,create_scope,revise_scope,current_scope,attest,assess
from canonical_mobile_money import VERSION
from database import DatabaseAdapter

START='2026-01-01T00:00:00.000000Z'
END='2026-03-01T00:00:00.000000Z'


def scope():
    return boundary('fixture',START,10,'test operator','nonsecret hand fixture')


def pair(tx=11,time='2026-01-02T00:00:00.000000Z',cash=False):
    p=dict(id=tx,timestamp=time,sender_account='A',receiver_account='A' if cash else 'B',transaction_type='deposit' if cash else 'transfer',currency='USD',agent_id=1 if cash else None)
    c=dict(transaction_id=tx,event_timestamp=time,sender_wallet='A',receiver_wallet=p['receiver_account'],amount_minor=1050,currency='USD',transaction_type='cash_in' if cash else 'wallet_to_wallet',channel='agent' if cash else 'direct_wallet',agent_id='1' if cash else '',serviced_wallet='A' if cash else '',agent_flow_direction='cash_in' if cash else 'none',canonical_version=VERSION,history_status='UNKNOWN')
    return p,c


def check(parents=None,canonical=None,**kw):
    p,c=pair()
    return verify(scope(),[p] if parents is None else parents,[c] if canonical is None else canonical,END,**kw)


def test_boundary_unknown_and_no_old_history():
    assert scope()['status']=='UNKNOWN'
    p,c=pair(tx=1,time='2025-12-01T00:00:00.000000Z')
    result=check([p],[])
    assert result['status']=='COMPLETE_VERIFIED' and result['entities']=={}
    assert freshness(scope(),check(),None)=='UNKNOWN'


def test_cold_start_wallet_agent():
    p,c=pair(cash=True)
    result=check([p],[c])
    assert result['entities']['wallet:A']['status']=='TRUE_COLD_START_VERIFIED'
    assert result['entities']['agent:1']['status']=='TRUE_COLD_START_VERIFIED'
    assert result['entities']['wallet:A']['first_key']==[c['event_timestamp'],11]


def test_complete_clean_and_graph():
    p,c=pair();p2,c2=pair(12,'2026-02-06T00:00:00.000000Z')
    c2.update(sender_wallet='B',receiver_wallet='C');p2.update(sender_account='B',receiver_account='C')
    result=check([p,p2],[c,c2])
    assert result['status']=='COMPLETE_VERIFIED'
    assert result['entities']['wallet:B']['status']=='COMPLETE_VERIFIED'
    assert result['canonical_event_ids']==[11,12]
    # An edge unrelated to A still invalidates the whole graph if omitted.
    assert check([p,p2],[c])['status']=='INCOMPLETE'


def test_gap_and_truthful_resolution():
    p,c=pair()
    missing=check([p],[])
    assert missing['status']=='INCOMPLETE'
    assert check(previous=missing)['status']=='INCOMPLETE'
    resolved=check(previous=missing,resolutions={'11':'authoritative-source/review-1'})
    assert resolved['status']=='COMPLETE_VERIFIED'
    assert check(previous=resolved)['status']=='COMPLETE_VERIFIED'
    broken=deepcopy(c);broken['serviced_wallet']='C'
    assert check([p],[broken],previous=missing,resolutions={'11':'cannot override invalid roles'})['status']=='INCOMPLETE'


def test_later_legacy_invalidates_and_freshness():
    old=check();p,c=pair();p2,c2=pair(12)
    bad=check([p,p2],[c],previous=old)
    assert freshness(scope(),bad,old)=='INCOMPLETE'
    clean=check([p,p2],[c,c2],previous=old)
    assert freshness(scope(),clean,old)=='UNKNOWN'
    assert freshness({**scope(),'revision':2},old,old)=='UNKNOWN'


@pytest.mark.parametrize('kind',['canonical_order','parent_order','duplicate','backdate','bad_time','bad_roles','scope','future','orphan'])
def test_failures(kind):
    p,c=pair();p2,c2=pair(12,'2026-01-03T00:00:00.000000Z')
    parents=[p,p2];canonical=[c,c2];s=scope()
    if kind=='canonical_order': canonical.reverse()
    if kind=='parent_order': parents.reverse()
    if kind=='duplicate': canonical.append(c2)
    if kind=='backdate': p2['timestamp']=c2['event_timestamp']='2025-12-31T00:00:00.000000Z'
    if kind=='bad_time': p2['timestamp']='2026-01-03 00:00:00'
    if kind=='bad_roles': c2['transaction_type']='bank_deposit'
    if kind=='scope': c2['canonical_version']='other'
    if kind=='future': p2['timestamp']=c2['event_timestamp']='2027-01-01T00:00:00.000000Z'
    if kind=='orphan': parents=[]
    assert verify(s,parents,canonical,END)['status']=='INCOMPLETE'


def test_capture_order_equal_time_id_and_decreasing_time():
    p,c=pair();p2,c2=pair(12)
    assert check([p,p2],[c,c2])['status']=='COMPLETE_VERIFIED'
    p2['timestamp']=c2['event_timestamp']='2026-01-01T01:00:00.000000Z'
    assert any(i['code']=='NONINCREASING_CAPTURE_KEY' for i in check([p,p2],[c,c2])['issues'])


def test_revision_and_deletion_persist_until_restored():
    old=check();p,c=pair();c['amount_minor']=999
    changed=check([p],[c],previous=old)
    assert changed['status']=='INCOMPLETE'
    assert check([p],[c],previous=changed)['status']=='INCOMPLETE'
    deleted=check([],[],previous=old)
    assert check([],[],previous=deleted)['status']=='INCOMPLETE'
    assert check(previous=deleted)['status']=='COMPLETE_VERIFIED'


@pytest.mark.parametrize('hours,name',[(1,'1h'),(24,'24h'),(168,'7d'),(672,'28d'),(673,'28d1h'),(696,'29d'),(840,'35d')])
def test_windows(hours,name):
    from datetime import datetime,timedelta
    t=datetime.fromisoformat(START.replace('Z','+00:00'))+timedelta(hours=hours)
    assert window_coverage(scope(),t.isoformat())[name]
    assert not window_coverage(scope(),(t-timedelta(microseconds=1)).isoformat())[name]


def test_calendar_and_utc():
    assert window_coverage(scope(),'2026-01-29T02:00:00+02:00')['prior28_utc_days']
    assert not window_coverage(scope(),'2026-01-29T01:59:59+02:00')['prior28_utc_days']


def test_no_self_attestation_or_override():
    p,c=pair();c['history_status']='COMPLETE_VERIFIED'
    assert check([p],[c])['status']=='INCOMPLETE'
    assert 'desired_status' not in __import__('inspect').signature(attest).parameters
    import ast
    tree=ast.parse(Path('server.py').read_text(encoding='utf-8'))
    assert not any(isinstance(n,ast.ImportFrom) and n.module in ('canonical_history','canonical_history_store') for n in ast.walk(tree))


def database():
    raw=sqlite3.connect(':memory:');raw.row_factory=sqlite3.Row
    raw.execute('CREATE TABLE transactions (id INTEGER PRIMARY KEY,timestamp TEXT,sender_account TEXT,receiver_account TEXT,transaction_type TEXT,currency TEXT,agent_id INTEGER,amount REAL)')
    from canonical_mobile_money_store import migrate as event_migrate
    conn=DatabaseAdapter(raw,'sqlite');event_migrate(conn);conn.commit()
    return conn


def test_persistence_restart_revision_no_event_changes(monkeypatch):
    import canonical_history_store as store
    conn=database()
    assert len(migrate(conn))==3 and migrate(conn)==[]
    from canonical_history_journal import ensure
    ensure(conn,apply=True);ensure(conn)
    monkeypatch.setattr(store,'now',lambda:START)
    s=create_scope(conn,'fixture','operator','fixture-boundary')
    assert s['status']=='UNKNOWN'
    with pytest.raises(ValueError): create_scope(conn,'another','operator','do not bypass boundary')
    p,c=pair(cash=True)
    conn.execute('INSERT INTO transactions (id,timestamp,sender_account,receiver_account,transaction_type,currency,agent_id) VALUES (?,?,?,?,?,?,?)',tuple(p.values()))
    from canonical_mobile_money_store import COLUMNS,TABLE
    conn.execute('INSERT INTO '+TABLE+' VALUES ('+','.join('?' for _ in COLUMNS)+')',tuple(c[k] for k in COLUMNS))
    before=[tuple(r) for r in conn.execute('SELECT * FROM '+TABLE).fetchall()]
    monkeypatch.setattr(store,'now',lambda:END)
    result=attest(conn,'fixture','local-admin','fixture-verification')
    conn.commit()
    assert result['status']=='COMPLETE_VERIFIED'
    assert len(conn.execute('SELECT * FROM cmm_entity_history').fetchall())==2
    s2=revise_scope(conn,'fixture','operator','review-revision')
    assert s2['start_timestamp']==s['start_timestamp'] and s2['revision']==2
    s3,current,old=assess(conn,'fixture')
    assert freshness(s3,current,old)=='UNKNOWN'
    assert [tuple(r) for r in conn.execute('SELECT * FROM '+TABLE).fetchall()]==before
    conn.close()


def test_models_and_historical_artifacts_unchanged():
    import hashlib
    before=json.loads(Path('ml_v4/evidence/integration_stage2a/before_sha256.json').read_text())
    for p,h in before.items():
        if p == 'database.py' or p.startswith(('ml/', 'ml_v3/', 'ml_v4/', 'experimental_v3/')):
            assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
    import subprocess
    subprocess.run([sys.executable, '-c', "import canonical_history, canonical_history_store, sys; assert not any(k.startswith(('xgboost','sklearn','ai_core','experimental_v3','ml_v4.development_features')) for k in sys.modules)"], check=True)


def test_transient_deleted_legacy_and_trigger_integrity(monkeypatch):
    import canonical_history_store as store
    from canonical_history_journal import ensure
    conn=database();migrate(conn);ensure(conn,apply=True)
    monkeypatch.setattr(store,'now',lambda:START)
    create_scope(conn,'fixture','operator','journal fixture')
    conn.execute("INSERT INTO transactions(id,timestamp,sender_account,receiver_account,transaction_type,currency) VALUES (11,?,'X','Y','transfer','USD')",('2026-01-02T00:00:00.000000Z',))
    conn.execute('DELETE FROM transactions WHERE id=11')
    monkeypatch.setattr(store,'now',lambda:END)
    _,result,_=assess(conn,'fixture')
    assert result['status']=='INCOMPLETE'
    assert any(i['code']=='JOURNALED_SOURCE_MISSING' for i in result['issues'])
    conn.execute('DROP TRIGGER cmm_tx_insert')
    with pytest.raises(ValueError,match='missing'):assess(conn,'fixture')
    conn.close()


def test_journal_mutation_cannot_self_heal():
    change=dict(change_id=1,transaction_id=11,operation='SOURCE_INSERT',event_timestamp='2026-01-02T00:00:00.000000Z',recorded_at=START)
    a=check(changes=[change]);bad={**change,'recorded_at':END}
    b=check(previous=a,changes=[bad])
    assert b['status']=='INCOMPLETE'
    assert check(previous=b,changes=[bad])['status']=='INCOMPLETE'


def test_restart_state_survives(tmp_path,monkeypatch):
    import canonical_history_store as store
    from canonical_history_journal import ensure
    c=database();migrate(c);ensure(c,apply=True)
    monkeypatch.setattr(store,'now',lambda:START)
    create_scope(c,'fixture','operator','persisted fixture')
    result=attest(c,'fixture','operator','empty controlled snapshot')
    c.commit()
    target=sqlite3.connect(tmp_path/'history.sqlite')
    c.connection.backup(target);target.close();c.close()
    raw=sqlite3.connect(tmp_path/'history.sqlite');raw.row_factory=sqlite3.Row
    reopened=DatabaseAdapter(raw,'sqlite')
    s,current,previous=assess(reopened,'fixture')
    assert previous['attestation_id']==result['attestation_id']
    assert freshness(s,current,previous)=='COMPLETE_VERIFIED'
    reopened.close()
