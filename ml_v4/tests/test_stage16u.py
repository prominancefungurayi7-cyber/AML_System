"""Deterministic nonproduction fixtures; never call schedule/generate on a unit."""
import ast
import dataclasses
import hashlib
import hmac
import json
import math
import sys
from datetime import timedelta
from collections import defaultdict
from pathlib import Path
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'ml_v4/generation'))
from stage16r_contract import DAY,HOUR,Event,FAMILIES,event_csv,event_from_row
from stage16r_evaluator import Evaluator,replay
from stage16r_generator import large_amount,bounded_shift,cents
from stage16u_generator import counts,split_budget,production_entrypoint,ChallengeUnit,START,fitting_start,END,SCORED_START,HARD_ORIGIN,validate_aggregate
from stage16u_custody import derived_seed,require_production_custody,FixtureDrawLifecycle,STREAMS
from stage16u_support import boundary,assess
# Reuse independently hand-derived target fixtures, excluding old DPAPI and RNG tests.
sys.path.insert(0,str(ROOT/'ml_v4/tests'))
from test_stage16r import Predicates, event, baseline


class Integers:
    def __init__(self,values): self.values=iter(values)
    def integers(self,low,high):
        value=next(self.values)
        assert low<=value<high,(value,low,high)
        return value


class ScriptedMixture:
    def __init__(self): self.components=[]; self.proposals=iter([20.,16000.,4999.,5000.])
    def random(self): return .95 if len(self.components)%2 else .2
    def lognormal(self,mean,sd):
        self.components.append(mean)
        return next(self.proposals)


class Implementation(unittest.TestCase):
    def fixture_unit(self):
        """Hand-authored 12-wallet, 2-agent universe: cannot be a production unit."""
        unit=ChallengeUnit.__new__(ChallengeUnit)
        unit.arm='reference_challenge'; unit.index=0; unit.partition='fixture'; unit.independent=False
        streams={name:np.random.Generator(np.random.PCG64DXSM(160001+i)) for i,name in enumerate(STREAMS)}
        unit.challenge_streams=streams; unit.rng=dict(streams,background=streams['routine'])
        unit.wallets=[dict(id=f'fixture_w{i}',profile='regular_transfer',weight=1.,activation=0,preferred_probability=.7,preferred=[f'fixture_w{(i+1)%12}']) for i in range(12)]
        unit.agents=[dict(id=f'fixture_a{i}',archetype='low_volume_stable',weight=1.,repeat=.7,retention=.9,catchment=[w['id'] for w in unit.wallets[:6]],shocks=[],acquisition=[]) for i in range(2)]
        unit.by_wallet={w['id']:w for w in unit.wallets}; unit.by_agent={a['id']:a for a in unit.agents}
        unit.service_history=defaultdict(list); unit.cash_history=defaultdict(list)
        unit.activity_history=defaultdict(list); unit.relationships=defaultdict(set)
        unit.cache={}; unit.cycles={}; unit.amount_rejections=0; unit.context_fallbacks=0
        unit.ledger_wallet={w['id']:100000000 for w in unit.wallets}
        unit.ledger_electronic={a['id']:200000000 for a in unit.agents}; unit.ledger_cash=dict(unit.ledger_electronic)
        unit.min_inventory=100000000; unit.update_population=lambda t:None
        return unit

    def test_all_family_and_hard_event_writers_on_hand_plans(self):
        for hard in (False,True):
            for family in FAMILIES:
                with self.subTest(hard=hard,family=family):
                    unit=self.fixture_unit()
                    motif=5 if family=='N3' else 10
                    plan=dict(id='fixture',family=family,hard=hard,variant=0,origin=f'hard_{family}' if hard else family,
                              hard_origin=HARD_ORIGIN[family] if hard else None,
                              M=motif,E=12,V=3,K=2,motif_start=60*DAY,motif_end=60*DAY+HOUR,strength=.5)
                    rows=[]
                    before=sum(unit.ledger_wallet.values())+sum(unit.ledger_electronic.values())
                    for j in range(motif):
                        p=dict(id=j+1,t=60*DAY+j*1000000,episode='fixture',role='motif',j=j,plan=plan)
                        e,private=unit.make_event(p); rows.append(e)
                        self.assertTrue(e.event_timestamp.startswith('2028-'))
                        self.assertEqual(private['arm'],'reference_challenge')
                        if hard: self.assertEqual(private['origin'],'hard_'+HARD_ORIGIN[family])
                        self.assertNotEqual(e.sender_wallet,e.receiver_wallet) if e.transaction_type=='wallet_to_wallet' else None
                    self.assertEqual(before,sum(unit.ledger_wallet.values())+sum(unit.ledger_electronic.values()))
                    self.assertEqual(len(replay(rows)),motif)
                    self.assertGreaterEqual(unit.min_inventory,0)

    def test_context_writer_each_role(self):
        for role in ('baseline_compatible','interleaved_unrelated','relationship_maintenance','post_motif_ordinary'):
            unit=self.fixture_unit()
            plan=dict(id='fixture',family='S4',hard=False,variant=None,origin='S4',M=10,E=12,V=3,K=2,
                      motif_start=60*DAY,motif_end=60*DAY+HOUR,strength=.5)
            e,meta=unit.make_event(dict(id=1,t=61*DAY,episode='fixture',role='context',context_role=role,plan=plan))
            self.assertEqual(meta['context_role'],role)
            self.assertEqual(meta['event_role'],'context')
            self.assertEqual(len(replay([e])),1)

    def test_episode_counts_all_sizes(self):
        for e in range(12,21):
            for f in FAMILIES:
                if f=='N3':
                    for v in range(2,7):
                        for k in range(3):
                            m,g=counts(f,e,Integers([v,k])); self.assertEqual(m,v+k); self.assertGreaterEqual(e-m,4)
                else:
                    m,g=counts(f,e,None); self.assertEqual((m,e-m),(e-2,2))
        sizes,left=split_budget(30,Integers([20])); self.assertEqual((sizes,left),([20],10))
        sizes,left=split_budget(30,Integers([12,18])); self.assertEqual((sizes,left),([12,18],0))

    def test_scored_horizon_end_is_exclusive(self):
        duration=1234567
        latest=fitting_start(Integers([END-duration]),duration)
        self.assertEqual(latest+duration,END)
        self.assertGreaterEqual(latest,SCORED_START)
        self.assertLessEqual(latest+duration,END)
        self.assertEqual(fitting_start(Integers([SCORED_START]),duration),SCORED_START)

    def test_aggregate_checks_global_units_entities_and_transactions(self):
        from stage16r_contract import Event
        rows=[]
        for arm,base in (('reference_challenge',1),('shifted_challenge',3)):
            wallet_a=f'fixture_{arm}_wa'; wallet_b=f'fixture_{arm}_wb'; agent=f'fixture_{arm}_a'
            events=[
                Event(base,START.isoformat(timespec='microseconds').replace('+00:00','Z'),wallet_a,wallet_b,100,'USD','wallet_to_wallet','direct_wallet','','','none'),
                Event(base+1,(START+timedelta(days=56)).isoformat(timespec='microseconds').replace('+00:00','Z'),wallet_a,wallet_b,100,'USD','wallet_to_wallet','direct_wallet','','','none')]
            rows.append(dict(arm=arm,index=0,events=events,population=dict(wallets=[dict(id=wallet_a),dict(id=wallet_b)],agents=[dict(id=agent)])))
        checked=validate_aggregate(rows,units_per_arm=1,wallets_per_unit=2,agents_per_unit=1,scored_per_unit=1,warmup_per_unit=1)
        self.assertEqual(checked['reference_challenge'],dict(units=1,scored=1,warmup=1))
        repeated=[rows[0],rows[1]|dict(population=rows[0]['population'])]
        with self.assertRaises(ValueError):
            validate_aggregate(repeated,units_per_arm=1,wallets_per_unit=2,agents_per_unit=1,scored_per_unit=1,warmup_per_unit=1)

    def test_conditional_rejection_fresh_component(self):
        rng=ScriptedMixture()
        self.assertEqual(large_amount(rng),5000.)
        self.assertEqual(rng.components,[math.log(35),math.log(1800),math.log(35),math.log(1800)])
        self.assertEqual(cents(5000.005),500001)
        self.assertEqual(cents(13000),1300000)
        for x in [5000,5001,7000,math.sqrt(5000*13000),10500,12999,13000]:
            self.assertTrue(5000<=bounded_shift(x)<=13000)
        self.assertEqual(bounded_shift(5000),5000)
        self.assertEqual(bounded_shift(13000),13000)

    def test_stream_derivation_and_separation(self):
        # Public all-zero fixture key is NOT a production salt and cannot authorize a draw.
        key=bytes(32)
        message=b'mobile_money_v4_independent_challenge_1|reference_challenge|0|entities'
        expected=int.from_bytes(hmac.new(key,message,hashlib.sha256).digest()[:16],'little')
        self.assertEqual(derived_seed(key,'reference_challenge',0,'entities'),expected)
        seeds=[derived_seed(key,a,i,s) for a in ('reference_challenge','shifted_challenge') for i in range(12) for s in STREAMS]
        self.assertEqual(len(seeds),len(set(seeds)))
        with self.assertRaises(ValueError): derived_seed(key,'final_test',0,'entities')

    def test_custody_cannot_be_enabled_by_flags_or_claims(self):
        for function in (require_production_custody,production_entrypoint):
            with self.assertRaises(PermissionError): function(approved=True,custodian=True)
        lifecycle=FixtureDrawLifecycle()
        with self.assertRaises(PermissionError): lifecycle.begin()
        lifecycle.commit(); lifecycle.begin(); lifecycle.finish(False)
        with self.assertRaises(PermissionError): lifecycle.begin()
        with self.assertRaises(PermissionError): lifecycle.commit()
        self.assertEqual(lifecycle.state,'FAILED_RETAINED')

    def test_source_boundary(self):
        source=(ROOT/'ml_v4/generation/stage16u_generator.py').read_text()
        imports={n.module for n in ast.walk(ast.parse(source)) if isinstance(n,ast.ImportFrom)}
        self.assertFalse(imports & {'stage16r_evaluator','stage16u_support','sklearn'})
        self.assertNotIn('ground_truth_label',source)
        # No production salt creation or persisted files in generator.
        self.assertNotIn('secrets.',source)
        self.assertNotIn('.write_',source)

    def test_observable_serialization_replay_and_private_rejection(self):
        rows=baseline()+[event(50*DAY+i*60000000,100+i,amount=7000+i*1000) for i in range(4)]
        saved=event_csv(rows)
        import csv,io
        reconstructed=[event_from_row(r) for r in csv.DictReader(io.StringIO(saved.decode()))]
        self.assertEqual(saved,event_csv(reconstructed))
        self.assertEqual(replay(rows),replay(reconstructed))
        with self.assertRaises(ValueError): event_from_row(dataclasses.asdict(rows[0])|{'context_role':'motif'})

    def test_context_has_normal_observable_effect(self):
        rows=baseline()+[event(50*DAY+i*60000000,100+i,amount=7000+i*1000) for i in range(4)]
        # Fourth payment designated context externally; all four still enter truth.
        a=replay(rows)
        self.assertIn('S1',a[-1]['families'])
        self.assertNotIn('S1',replay(rows[:-1])[-1]['families'])
        self.assertEqual(a,replay(rows))

    def test_support_all_thresholds_and_empty(self):
        policy=json.loads((ROOT/'ml_v4/design/challenge/challenge_support_policy.json').read_text())
        # Hand-authored abstract audit records, not generated transactions/targets.
        records=[dict(subject=f'w{i%48}',cluster=f'e{i}',unit=(i%24),bin=i%6,
                      arm='reference_challenge' if i%24<12 else 'shifted_challenge') for i in range(240)]
        rows={f:list(records) for f in FAMILIES}
        self.assertEqual(assess(rows,rows,rows,policy)['status'],'PASS')
        empty={f:[] for f in FAMILIES}
        self.assertEqual(assess(empty,empty,empty,policy)['status'],'FAIL')
        for field,value,gate in [('subject','same','subject_concentration'),('unit',0,'units'),('bin',0,'temporal'),('arm','reference_challenge','arms'),('cluster','same','clusters')]:
            altered={f:[r|{field:value} for r in records] for f in FAMILIES}
            self.assertFalse(assess(altered,rows,rows,policy)['families']['S1']['gates'][gate])
        sparse={f:records[:49] for f in FAMILIES}
        self.assertFalse(assess(rows,rows,sparse,policy)['families']['N3']['gates']['boundary_rows'])

    def test_near_boundary_single_count_failure(self):
        old=baseline()
        recent=[event(50*DAY+i*60000000,100+i,amount=12000+i*1000) for i in range(3)]
        state=Evaluator()
        for e in old+recent[:-1]: state.process(e)
        current=recent[-1]; truth=state.evaluate(current)
        outcome=boundary(state,current,'S1',truth)
        self.assertEqual(outcome['failed'],['count'])
        self.assertTrue(outcome['near'])

    def test_accounting_observable_transitions(self):
        # Hand-authored independent conservation oracle, no population sampling.
        wallets={'w':100000,'r':100000}; electronic={'a':200000}; cash={'a':200000}
        rows=[event(0,1,typ='cash_in',amount=1000),event(1,2,typ='cash_out',amount=500),
              event(2,3,typ='wallet_to_wallet',receiver='r',amount=200,serviced='r')]
        before=sum(wallets.values())+sum(electronic.values())
        for e in rows:
            if e.transaction_type=='cash_in': wallets[e.subject]+=e.amount_minor; electronic[e.agent_id]-=e.amount_minor; cash[e.agent_id]+=e.amount_minor
            elif e.transaction_type=='cash_out': wallets[e.subject]-=e.amount_minor; electronic[e.agent_id]+=e.amount_minor; cash[e.agent_id]-=e.amount_minor
            else: wallets[e.sender_wallet]-=e.amount_minor; wallets[e.receiver_wallet]+=e.amount_minor
        self.assertEqual((wallets,electronic,cash),({'w':100300,'r':100200},{'a':199500},{'a':200500}))
        self.assertEqual(before,sum(wallets.values())+sum(electronic.values()))


if __name__=='__main__': unittest.main(verbosity=2)
