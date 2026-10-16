"""Nonfinancial generator diagnostic using the actual frozen V4 runtime.

Only in-memory hypothetical canonical events; no database connection, financial
writes, stored dataset, history attestation, model fitting or prediction overrides.
"""
import json
import argparse
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from canonical_mobile_money import prepare_ingestion, serialize, with_id, FIELDS
import v4_simulation as simulation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local-history', action='store_true',
                        help='Read verified local history as context for one hypothetical 100-payment batch')
    args = parser.parse_args()
    wallets = [dict(id=i, username=n, account_number=a, balance=100000)
               for i, (n, a) in enumerate(simulation.DEMO_WALLETS.items(), 1)]
    cases = []
    seeds = ('792976c1-5dac-4b2b-a8d0-5174590ed2ab',
             '8e6e3d88-162f-44db-92bf-7f0a25793ce6',
             '11111111-2222-4333-8444-555555555555')
    # Same hypothetical instant and wallet population for both versions.
    start = datetime(2026, 10, 13, 12, tzinfo=timezone.utc)
    prefix = []
    configurations = (
            (1, 100, seeds[0], [], 1),
            *((2, 100, seed, [], 1) for seed in seeds),
            (2, 100, seeds[0], ['1'], 1),
            (2, 100, seeds[0], [], 2),
            (2, 1000, seeds[0], [], 1))
    if args.local_history:
        from tools.review_application import load_application
        from v4_primary import verify_database
        _, readonly = load_application()
        conn = readonly()
        try:
            verify_database(conn)
            prefix = [{k: row[k] for k in FIELDS} for row in conn.execute(
                'SELECT * FROM canonical_mobile_money_events ORDER BY event_timestamp,transaction_id')]
            wallets = [dict(row) for row in conn.execute(
                "SELECT id,username,account_number,balance FROM users WHERE role='customer' ORDER BY id")
                if simulation.DEMO_WALLETS.get(row['username']) == row['account_number']]
            agents = [str(row['id']) for row in conn.execute("SELECT id FROM agents WHERE status='active' ORDER BY id")]
        finally:
            conn.close()
        configurations = ((2, 100, seeds[0], agents, 1),)
        start = max([datetime.now(timezone.utc)] + [
            datetime.fromisoformat(e['event_timestamp'].replace('Z', '+00:00')) + timedelta(microseconds=1)
            for e in prefix])
    last_id = max((event['transaction_id'] for event in prefix), default=0)
    for version, count, seed, agents, repeats in configurations:
        request = dict(version=version, batch_id=seed, admin_id=1, count=count,
                       mode='mixed', wallets=wallets, agents=agents)
        if version == 2:
            request['scenario_wallet_ids'] = simulation.scenario_wallet_order(wallets)
        rows = simulation.plan(request)
        events = []
        for sender, _, form, _ in rows * repeats:
            i = len(events)
            timestamp = (start + timedelta(microseconds=i)).isoformat()
            events.append(serialize(with_id(prepare_ingestion(form, sender['account_number'], timestamp), last_id + i + 1)))
        cases.append(dict(version=version, count=count * repeats, agents=bool(agents),
                          prefix=prefix, events=events, schedule=simulation.scenario_schedule(request) * repeats))
    code = '''
import json,sys,numpy as np
from ml_v4.frozen_inference.service import FrozenModel,MODEL_SHA,THRESHOLD
m=FrozenModel(); results=[]
for case in json.load(sys.stdin):
 state=m.extractor.Extractor(); groups={}; last=None
 for raw in case['prefix']: state.step(m.contract.Event(**raw))
 for raw,family in zip(case['events'],case['schedule']):
  row=state.step(m.contract.Event(**raw))
  x=np.array([tuple(row)],dtype=[(n,'U16' if n=='transaction_type' else 'f8') for n in m.names])
  p=m.predict(x); last=x
  group=groups.setdefault(family,dict(inputs=0,normal=0,suspicious=0))
  group['inputs']+=1; group['suspicious' if p>=THRESHOLD else 'normal']+=1
 # Confirm incremental diagnostic features match the frozen replay API exactly.
 replay,_=m.replay(case['prefix']+case['events'],case['events'][-1]['transaction_id'])
 for name in m.names:
  if name=='transaction_type': assert last[name][0]==replay[name][0]
  else: np.testing.assert_equal(last[name],replay[name])
 results.append(dict(version=case['version'],rows=case['count'],history_rows=len(case['prefix']),agents=case['agents'],groups=groups))
print(json.dumps(dict(scope='offline hypothetical events; not live inference or measured accuracy',model_sha256=MODEL_SHA,threshold=THRESHOLD,feature_replay='PASS',results=results),indent=2))
'''
    result = subprocess.run([str(ROOT / 'ml_v4/.venv_inference_stage3/Scripts/python.exe'), '-B', '-c', code],
                            cwd=ROOT, input=json.dumps(cases), text=True, capture_output=True, timeout=180)
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:])
    print(result.stdout)


if __name__ == '__main__':
    main()
