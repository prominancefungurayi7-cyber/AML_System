"""Independent hand expectations and full40 nonredundancy witnesses; no evaluator."""
from pathlib import Path
from dataclasses import asdict, replace
import math
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from ml_v4.development_features_v2.extractor_v2 import (
    Extractor, AdditionalExtractor, OriginalExtractor, Event, DAY, NAMES,
    ADDED_NAMES, exact_float, MAX_EXACT_INTEGER,
)
from stage16r_contract import timestamp, event_from_row
from stage16r_loader import development_path

T = 50*DAY

def event(i, t, amount=5000, sender='w', receiver=None, kind='wallet_to_wallet'):
    receiver = receiver or 'sink'+str(i)
    cash = kind != 'wallet_to_wallet'
    return Event(i, timestamp(t), sender, sender if cash else receiver, amount, 'USD', kind,
                 'agent' if cash else 'direct_wallet', 'a' if cash else '', sender if cash else '', kind if cash else 'none')

def feed(history, current, cls=Extractor):
    state = cls()
    for e in sorted(history, key=lambda e:e.key):
        state.step(e)
    return state.step(current)

def base(count=4, first=None, amount=1000):
    # First row is incoming participation only and outside the baseline.
    return [event(1, T-35*DAY if first is None else first, sender='observer', receiver='w')]+[
        event(10+i, T-(20+i)*DAY, amount=amount) for i in range(count)]

def equal40(a,b):
    assert len(a)==len(b)==40
    for name,x,y in zip(NAMES[:40],a,b):
        assert (math.isnan(x) and math.isnan(y)) if isinstance(x,float) and math.isnan(x) else x==y, name

def test_schema_and_cold_start():
    got=feed([],event(99,T))
    assert len(NAMES)==44 and len(set(NAMES))==44
    assert got[-4:]==(5000.,-1.,0.,-1.)
    assert all(type(v) is float for v in got[-4:])
    equal40(got[:40],feed([],event(99,T),OriginalExtractor))

def test_inclusive_tolerance_and_exact_sum():
    h=[event(i+1,T-DAY+i,amount=a) for i,a in enumerate([4750,5250,4749,5251])]
    assert feed(h,event(99,T))[-4:]==(15000.,-1.,0.,-1.)

def test_baseline_membership_and_current_center():
    h=base(amount=1000)+[event(30,T-10*DAY,4750),event(31,T-9*DAY,5250),event(32,T-8*DAY,5251)]
    assert feed(h,event(99,T))[-4:]==(5000.,2.,0.,0.)
    assert feed(h,event(99,T,1000))[-4:]==(1000.,4.,0.,0.)

@pytest.mark.parametrize('count,first,expected',[(3,T-35*DAY,-1),(4,T-35*DAY,0),(4,T-35*DAY+1,-1),(4,T-36*DAY,0)])
def test_support_age_zero_missing(count,first,expected):
    g=feed(base(count,first),event(99,T))[-4:]
    assert g==(5000.,float(expected),0.,float(expected))

def test_exact_lower_boundary_does_not_count_as_activity():
    h=[event(1,T-35*DAY)]+base(3)[1:]
    assert feed(h,event(99,T))[-3]==-1

def test_7d_split_and_35d_exclusion():
    h=base()+[event(30,T-7*DAY,5000),event(31,T-7*DAY+1,5000)]
    assert feed(h,event(99,T))[-4:]==(10000.,1.,0.,0.)

def test_incoming_does_not_supply_activity():
    h=[event(i,T-(40-i)*DAY,sender='other'+str(i),receiver='w') for i in range(1,7)]
    assert feed(h,event(99,T))[-4:]==(5000.,-1.,0.,-1.)

def test_band_endpoints_distinct_and_current_outside():
    h=[event(i+1,T-DAY+i,a) for i,a in enumerate([699999,700000,700000,1050000,1050001])]
    assert feed(h,event(99,T,5000))[-4:]==(5000.,-1.,2.,-1.)
    assert feed(h,event(99,T,850000))[-2]==3

def test_band_baseline_exact_endpoints():
    h=base()+[event(30,T-10*DAY,700000),event(31,T-9*DAY,1050000),event(32,T-8*DAY,1050001)]
    assert feed(h,event(99,T))[-1]==2

@pytest.mark.parametrize('kind',['cash_in','cash_out'])
def test_cash_roles(kind):
    h=base()+[event(30,T-DAY,5000,kind=kind)]
    assert feed(h,event(99,T,5000,kind=kind))[-4:]==(10000.,0.,0.,0.)

def test_receiver_assistance_does_not_change_wallet_subject():
    e=replace(event(99,T),channel='agent',agent_id='a',serviced_wallet='sink99')
    assert feed(base()+[event(30,T-DAY)],e)[-4:]==(10000.,0.,0.,0.)

def test_same_time_full_key_current_once_future_invariance():
    state=Extractor()
    a=state.step(event(1,T))
    b=state.step(event(2,T))
    state.step(event(3,T,5251))
    assert a[-4]==5000 and b[-4]==10000
    repeated=feed([event(1,T)],event(2,T))
    equal40(b[:40],repeated[:40]);assert b[-4:]==repeated[-4:]

@pytest.mark.parametrize('bad',[event(1,T-1),event(1,T),event(2,T-1)])
def test_reject_nonincreasing_or_duplicate(bad):
    state=Extractor();state.step(event(1,T))
    with pytest.raises(ValueError):state.step(bad)
    with pytest.raises(RuntimeError):state.step(event(3,T+1))

def test_future_before_current_rejected():
    state=Extractor();state.step(event(1,T+1))
    with pytest.raises(ValueError):state.step(event(2,T))

@pytest.mark.parametrize('mutation',[{'amount_minor':0},{'amount_minor':True},{'amount_minor':1500001},{'event_timestamp':'2027-01-01T00:00:00'}, {'serviced_wallet':'private'},{'currency':'ZWL'}])
def test_invalid_schema(mutation):
    with pytest.raises((ValueError,TypeError)):Extractor().step(replace(event(1,T),**mutation))

def test_overflow_and_integer_precision():
    assert exact_float(MAX_EXACT_INTEGER)==float(MAX_EXACT_INTEGER)
    for value in [MAX_EXACT_INTEGER+1,-2,1.5,True]:
        with pytest.raises(OverflowError):exact_float(value)
    # Aggregate-boundary unit test; a schema-valid full ledger with billions of
    # rows is intentionally not allocated. Runtime extraction calls this guard.
    with pytest.raises(OverflowError):exact_float(sum([MAX_EXACT_INTEGER,1]))

@pytest.mark.parametrize('part',['final_test','independent_evaluation','../train','TRAIN','*'])
def test_loader_denies_non_development(part):
    with pytest.raises(PermissionError):development_path(part,'transactions.csv')

def test_partition_reset_and_replay():
    h=base()+[event(40,T-DAY)]
    a=feed(h,event(99,T));b=feed(h,event(99,T))
    equal40(a[:40],b[:40]);assert a[-4:]==b[-4:]
    assert feed([],event(99,T))[-4:]==(5000.,-1.,0.,-1.)

def test_private_metadata_never_enters_interface():
    row=asdict(event(99,T))
    for private in ['scenario_id','origin','ground_truth_label','activation_schedule']:
        with pytest.raises(ValueError):event_from_row(dict(row,**{private:'changed'}))
    # Separate provenance can vary arbitrarily without being an argument.
    results=[]
    for provenance in [{'origin':'H2'},{'origin':'S2','intended_onset':'future'}]:
        results.append(feed([],event_from_row(row))[-4:])
    assert results[0]==results[1]
    with pytest.raises(TypeError):Extractor().step(row)

@pytest.mark.parametrize('which',[0,1,2,3])
def test_stage20_full40_nonredundancy_witness(which):
    h=base()
    cur=event(99,T)
    if which==0:
        h += [event(30,T-4*DAY,4999),event(31,T-3*DAY,5000),event(32,T-2*DAY,5000)]
        target=30;newamount=5000;expected=(19999.,20000.)
    elif which==1:
        target=10;newamount=5000;expected=(0.,1.)
    elif which==2:
        cur=event(99,T,850000)
        h += [event(30,T-5*DAY,850000),event(31,T-4*DAY,850000),event(32,T-3*DAY,850000),event(33,T-2*DAY,100)]
        target=30;newamount=850001;expected=(1.,2.)
    else:
        target=10;newamount=800000;expected=(0.,1.)
    other=[replace(e,amount_minor=newamount) if e.transaction_id==target else e for e in h]
    a=feed(h,cur);b=feed(other,cur)
    equal40(a[:40],b[:40])
    equal40(a[:40],feed(h,cur,OriginalExtractor))
    equal40(b[:40],feed(other,cur,OriginalExtractor))
    assert (a[40+which],b[40+which])==expected

def test_independent_decimal_reference_small_history():
    # A separate batch reference uses Decimal interval inequalities, not the
    # implementation's 20*abs test, and scans the complete immutable history.
    from decimal import Decimal
    h=base()+[event(30,T-7*DAY,5000),event(31,T-6*DAY,4750),event(32,T-2*DAY,5250)]
    cur=event(99,T)
    activity=[e for e in h if e.sender_wallet=='w']
    recent=[e for e in activity if T-7*DAY<e.time<=T]+[cur]
    prior=[e for e in activity if T-35*DAY<e.time<=T-7*DAY]
    lo=Decimal(cur.amount_minor)*Decimal('.95');hi=Decimal(cur.amount_minor)*Decimal('1.05')
    expected=(sum(e.amount_minor for e in recent if lo<=Decimal(e.amount_minor)<=hi),sum(lo<=Decimal(e.amount_minor)<=hi for e in prior),len(set(e.amount_minor for e in recent if 700000<=e.amount_minor<=1050000)),sum(700000<=e.amount_minor<=1050000 for e in prior))
    assert expected==(15000,1,0,0)
    assert feed(h,cur)[-4:]==expected
