"""Hand-derived expectations; does not import target evaluator or witnesses."""
from pathlib import Path
import sys
import math
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from extractor import Extractor, NAMES, Event, DAY, HOUR
from stage16r_contract import timestamp, event_from_row
from stage16r_loader import development_path

def event(i,t,s='w',r='z',amount=100,kind='wallet_to_wallet',agent=''):
    if kind!='wallet_to_wallet': r=s
    return Event(i,timestamp(t),s,r,amount,'USD',kind,'agent' if agent else 'direct_wallet',agent,s if agent else '',kind if kind!='wallet_to_wallet' else 'none')

def run(history,current):
    x=Extractor()
    for e in sorted(history,key=lambda e:e.key): x.step(e)
    return x.step(current)

def test_cold_all_40():
    got=run([],event(1,40*DAY))
    expected=[100,'wallet_to_wallet',1,100,1,-1,1,1,1,1,-1,0,1,1,-1,1,1,-1,-1,0,-1,-1,-1,math.nan,-1,0,-1,-1,0,-3,-1,0,0,0,0,0,0,-3,0,0]
    assert len(NAMES)==40 and len(set(NAMES))==40
    for i,(a,b) in enumerate(zip(got,expected)):
        assert isinstance(a,str) if i==1 else isinstance(a,float)
        assert math.isnan(a) if isinstance(b,float) and math.isnan(b) else a==b

def test_wallet_and_calendar_manual():
    t=40*DAY+3*HOUR
    h=[event(1,t-35*DAY)]
    h += [event(10+k,t-(10+k)*DAY,amount=200) for k in range(4)]
    h += [event(30,40*DAY,amount=700000),event(31,t-HOUR,amount=104),event(32,t-HOUR+1,amount=105)]
    g=run(h,event(40,t,amount=100))
    assert g[2:12]==pytest.approx([2,205,105/205,2,3,3/4,4,3,4,1])
    # Exactly one-hour-old row excluded from recent but belongs to baseline.
    assert g[38]==35

def test_agent_manual_all_primitives():
    t=40*DAY
    h=[event(1,t-35*DAY,s='old',kind='cash_in',agent='a')]
    # Four baseline weeks, each three services and three distinct customers.
    for k in range(4):
        for j in range(3):
            h.append(event(10+3*k+j,t-[8,15,22,28][k]*DAY-j,s='b'+str(j),kind='cash_in',agent='a'))
    h += [event(30,t-HOUR+1,s='new1',kind='cash_in',agent='a'),event(31,t-1,s='new2',amount=300,kind='cash_out',agent='a')]
    g=run(h,event(40,t,s='new3',amount=200,kind='cash_out',agent='a'))
    assert g[24:38]==pytest.approx([1,3,3,1,2/3,-3,3,3,1,2,100,500,3,5/3])
    assert g[39]==35

def test_top2_independent_and_assisted_cash_exclusion():
    t=40*DAY
    h=[event(1,t-35*DAY,s='old',kind='cash_in',agent='a')]
    h += [event(10+k,t-10*DAY+k,s='b'+str(k%5),kind='cash_in',agent='a') for k in range(20)]
    h += [event(40+k,t-100+k,s='n'+str(k%2),kind='cash_out',agent='a') for k in range(7)]
    e=Event(60,timestamp(t),'sender','receiver',900,'USD','wallet_to_wallet','agent','a','receiver','none')
    g=run(h,e)
    assert g[28]==7/8 and g[29]==pytest.approx(7/8-2/5)
    assert g[31:38]==pytest.approx([3,0,7,0,700,2,2])
    assert g[39]==35

def test_network_paths_and_funding_manual():
    t=40*DAY
    h=[event(1,t-35*DAY,s='r',r='s')]
    h += [event(10+k,t-10*DAY+k,s='r',r='s') for k in range(4)]
    h += [event(20,t-100,s='r',r='s',amount=200),event(21,t-90,s='r',r='q',amount=100),event(22,t-80,s='q',r='s',amount=200),event(23,t-70,s='s',kind='cash_in',amount=100,agent='a'),event(24,t-60,s='s',r='z',amount=50)]
    g=run(h,event(30,t,s='s',r='r',amount=100))
    assert g[12:18]==pytest.approx([1,1,-1,2,2,-1])
    assert g[18:24]==pytest.approx([1,2,0,.5,150/500,450])
    # Prior topology retained even when current value cannot satisfy target ratios.
    g2=run(h,event(30,t,s='s',r='r',amount=1000))
    assert g2[18:21]==g[18:21] and g2[21]==5

def test_network_baseline_directions():
    t=40*DAY
    h=[event(1,t-35*DAY,s='s',r='r')]+[event(10+k,t-10*DAY+k,s='s',r='r') for k in range(4)]
    h += [event(20,t-DAY,s='s',r='r'),event(21,t-DAY+1,s='s',r='r')]
    g=run(h,event(30,t,s='s',r='r'))
    assert g[12:18]==pytest.approx([2,1,2,2,1,2])

def test_residual_negative_one_not_missing():
    t=40*DAY
    g=run([event(1,t-10,s='r',r='w',amount=100),event(2,t-5,amount=101)],event(3,t))
    assert g[23]==-1 and g[22]==2.01

def test_a1_exact_age_and_support():
    t=40*DAY
    base=[event(1,t-35*DAY,kind='cash_in',agent='a')]+[event(10+k,t-10*DAY+k,kind='cash_in',agent='a') for k in range(12)]
    assert run(base,event(40,t,kind='cash_out',agent='a'))[24]==1
    base[0]=event(1,t-35*DAY+1,kind='cash_in',agent='a')
    assert run(base,event(40,t,kind='cash_out',agent='a'))[24]==-1
    base[0]=event(1,t-35*DAY,kind='cash_in',agent='a')
    assert run(base[:-1],event(40,t,kind='cash_out',agent='a'))[24]==-1

def test_ties_future_reset_and_duplicates():
    t=40*DAY
    x=Extractor(); a=x.step(event(1,t)); b=x.step(event(2,t))
    assert a[2]==1 and b[2]==2
    x.step(event(3,t+1))
    again=run([],event(1,t))
    assert a[:23]==again[:23] and a[24:]==again[24:] and math.isnan(a[23]) and math.isnan(again[23])
    with pytest.raises(ValueError): x.step(event(2,t+2))
    with pytest.raises(ValueError): x.step(event(4,t-1))
    assert Extractor().step(event(1,t))[2]==1

def test_graph_chronology_and_lengths():
    t=40*DAY
    for n in range(1,7):
        nodes=['r']+['q'+str(k) for k in range(n-1)]+['s']
        h=[event(k+1,t-100+k,s=nodes[k],r=nodes[k+1]) for k in range(n)]
        g=run(h,event(20,t,s='s',r='r'))
        assert g[19]==(1 if n<=5 else 0)
        if n>1:
            h[0]=event(1,t-1,s=nodes[0],r=nodes[1])
            assert run(h,event(20,t,s='s',r='r'))[19]==0

@pytest.mark.parametrize('partition',['final_test','independent_evaluation','../train','TRAIN','train/..'])
def test_access(partition):
    with pytest.raises(PermissionError): development_path(partition,'transactions.csv')

def test_private_fields_rejected():
    from dataclasses import asdict
    d=asdict(event(1,0));d['origin']='private'
    with pytest.raises(ValueError): event_from_row(d)
    with pytest.raises(PermissionError): development_path('train','family_evidence.jsonl')

def test_graph_selection_spread_and_key_tie():
    t=40*DAY
    h=[event(1,t-100,s='r',r='q',amount=100),event(2,t-90,s='q',r='s',amount=200),
       event(3,t-80,s='r',r='p',amount=300),event(4,t-70,s='p',r='s',amount=450)]
    g=run(h,event(9,t,s='s',r='r',amount=600))
    assert g[18:22]==pytest.approx([2,2,math.log(1.5),2])
    h += [event(5,t-60,s='r',r='s',amount=700),event(6,t-50,s='r',r='s',amount=800)]
    assert run(h,event(9,t,s='s',r='r',amount=600))[18:22]==pytest.approx([1,4,0,6/7])

def test_calendar_lower_boundary_and_translation():
    t=40*DAY
    h=[event(1,t-28*DAY),event(2,t-27*DAY),event(3,t-26*DAY),event(4,t-25*DAY),event(5,t-1)]
    g=run(h,event(6,t))
    assert g[8:11]==(1,1,1)
    from dataclasses import replace
    shift=lambda e: replace(e,event_timestamp=timestamp(e.time+10*DAY))
    other=run([shift(e) for e in h],shift(event(6,t)))
    assert g[:23]==other[:23] and g[24:]==other[24:]

def test_incoming_observation_and_signed_skew():
    t=40*DAY
    h=[event(1,t-35*DAY,s='other',r='w')]
    assert run(h,event(2,t))[38]==35
    h=[event(1,t-35*DAY,kind='cash_out',agent='a')]+[event(10+k,t-10*DAY+k,kind='cash_out',agent='a') for k in range(12)]
    g=run(h,event(40,t,kind='cash_in',agent='a'))
    assert g[37]==-2 and g[37]!=-3

def test_no_w2w_anchor_and_24h_open_boundary():
    t=40*DAY
    for h in ([event(1,t-1,kind='cash_in',agent='a')],[event(1,t-DAY,s='r',r='w')]):
        g=run(h,event(2,t)); assert g[22]==-1 and math.isnan(g[23])

def test_invariance_rename_and_future_append():
    from dataclasses import replace
    h=[event(1,39*DAY,s='r',r='w'),event(2,39*DAY+1)]
    cur=event(3,40*DAY)
    original=run(h,cur)
    rename=lambda e: replace(e,sender_wallet='renamed_'+e.sender_wallet,receiver_wallet='renamed_'+e.receiver_wallet)
    renamed=run([rename(e) for e in h],rename(cur))
    assert renamed[:23]==original[:23] and renamed[24:]==original[24:]
    assert math.isnan(renamed[23]) and math.isnan(original[23])
    x=Extractor(); results=[x.step(e) for e in h+[cur,event(4,41*DAY)]]
    assert results[2][:23]==original[:23] and results[2][24:]==original[24:]
    assert math.isnan(results[2][23])

def test_path_same_time_keys():
    t=40*DAY
    assert run([event(1,t,s='r',r='q'),event(2,t,s='q',r='s')],event(3,t,s='s',r='r'))[19]==1
    assert run([event(2,t,s='r',r='q'),event(1,t,s='q',r='s')],event(3,t,s='s',r='r'))[19]==0

def test_seven_day_amount_boundaries():
    t=40*DAY
    h=[event(1,t-7*DAY,amount=100),event(2,t-7*DAY+1,amount=95),
       event(3,t-5,amount=105),event(4,t-4,amount=106),event(5,t-3,amount=700000),
       event(6,t-2,amount=1050000),event(7,t-1,amount=1050001)]
    g=run(h,event(8,t,amount=100))
    assert g[6:8]==pytest.approx([3,3/7]) and g[11]==2

def test_calendar_median_nonzero():
    t=40*DAY
    h=[event(1,t-28*DAY)]
    for k in range(1,29):
        h += [event(2*k,t-k*DAY+HOUR),event(2*k+1,t-k*DAY+2*HOUR)]
    assert run(h,event(99,t))[10]==.5

def test_agent_weekly_even_median_and_returning_customer():
    t=40*DAY
    h=[event(1,t-35*DAY,kind='cash_in',agent='a')]
    for week,days in enumerate([8,15,22,29]):
        for j in range(max(3,week+1)):
            h.append(event(10+week*10+j,t-days*DAY+j,s='b'+str(j%(week+1)),kind='cash_in',agent='a'))
    h += [event(60,t-2,s='b0',kind='cash_in',agent='a'),event(61,t-1,s='new',kind='cash_in',agent='a')]
    g=run(h,event(62,t,s='new2',kind='cash_out',agent='a'))
    assert g[24:28]==pytest.approx([3/2.5,3,2,2/3])

def test_a2_historical_distinct_gate():
    t=40*DAY
    h=[event(1,t-35*DAY,kind='cash_in',agent='a')]+[event(10+k,t-10*DAY+k,s='b'+str(k%4),kind='cash_in',agent='a') for k in range(20)]
    assert run(h,event(40,t,kind='cash_in',agent='a'))[29]==-3

def test_loader_resolved_escape_rejected(monkeypatch,tmp_path):
    import stage16r_loader as loader
    monkeypatch.setattr(loader,'DEVELOPMENT_ROOT',tmp_path/'development')
    original=Path.resolve
    def redirected(path,*args,**kwargs):
        if path.name=='transactions.csv':return tmp_path/'outside.csv'
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'resolve',redirected)
    with pytest.raises(PermissionError):loader.development_path('train','transactions.csv')

@pytest.mark.parametrize('timestamp_text',['2027-01-01T00:00:00','2027-01-01T00:00:00.0000001Z','2027-01-01T02:00:00.000000+02:00'])
def test_timestamp_schema_rejection(timestamp_text):
    from dataclasses import replace
    with pytest.raises((TypeError,ValueError)):Extractor().step(replace(event(1,0),event_timestamp=timestamp_text))

