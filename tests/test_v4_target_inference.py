"""Nonfinancial parity checks in the pinned V4 inference environment."""
from datetime import datetime, timedelta, timezone
import random
import sys
from pathlib import Path

import numpy as np
import pytest

from ml_v4.frozen_inference import service
from v4_target_inference import replay_target, infer


@pytest.fixture(scope='module')
def model():
    expected = Path(__file__).resolve().parents[1] / 'ml_v4/.venv_inference_stage3'
    if Path(sys.prefix).resolve() != expected.resolve():
        pytest.skip('Run these parity cases with the pinned V4 inference Python')
    return service.FrozenModel()


def history():
    rng = random.Random(42)
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    rows = []
    # Includes expired history, eligible wallet/agent baselines, cash directions,
    # assisted transfers, equal timestamps and chronological return paths.
    for index in range(160):
        sender, receiver = rng.sample(['A', 'B', 'C', 'D', 'E'], 2)
        kind = ('wallet_to_wallet', 'cash_in', 'cash_out')[index % 3]
        agent = 'agent1' if index % 4 or kind != 'wallet_to_wallet' else ''
        timestamp = start + timedelta(hours=(index // 2) * 14)
        wallet = receiver if kind == 'wallet_to_wallet' else sender
        rows.append(dict(transaction_id=index + 1,
            event_timestamp=timestamp.isoformat(timespec='microseconds').replace('+00:00', 'Z'),
            sender_wallet=sender, receiver_wallet=receiver if kind == 'wallet_to_wallet' else sender,
            amount_minor=rng.choice([100, 105, 10000, 700000, 1050000, 1500000]),
            currency='USD', transaction_type=kind, channel='agent' if agent else 'direct_wallet',
            agent_id=agent, serviced_wallet=wallet if agent else '',
            agent_flow_direction='none' if kind == 'wallet_to_wallet' else kind))
    return rows


@pytest.mark.parametrize('transaction_id', [1, 2, 3, 35, 99, 127, 158, 159, 160])
def test_exact_features_and_probability_match_frozen_replay(model, transaction_id):
    events = history()
    expected, original_event = model.replay(events, transaction_id)
    actual, current = replay_target(model, events, transaction_id)
    assert current == original_event
    assert actual.dtype == expected.dtype
    for name in model.names:
        np.testing.assert_array_equal(actual[name], expected[name])
    assert model.predict(actual) == model.predict(expected)


@pytest.mark.parametrize('mutation,code', [
    ('duplicate', 'HISTORY_INCOMPLETE'), ('order', 'HISTORY_INCOMPLETE'),
    ('future_amount', 'FEATURE_INVALID'), ('extra_field', 'INVALID_EVENT'),
    ('missing_target', 'EVENT_UNAVAILABLE')])
def test_full_snapshot_is_validated_including_future_events(model, mutation, code):
    events = history()
    target = 1
    if mutation == 'duplicate':
        events.append(dict(events[-1]))
    elif mutation == 'order':
        events[-1], events[-2] = events[-2], events[-1]
    elif mutation == 'future_amount':
        events[-1]['amount_minor'] = 1500001
    elif mutation == 'extra_field':
        events[-1]['label'] = 1
    else:
        target = 999
    with pytest.raises(service.Failure) as exc:
        replay_target(model, events, target)
    assert exc.value.code == code


def test_history_gate_failure_produces_no_prediction(monkeypatch):
    calls = []
    class Connection:
        def rollback(self): calls.append('rollback')
        def close(self): calls.append('close')
    def reject(*_): raise service.Failure('HISTORY_INCOMPLETE')
    monkeypatch.setattr('ml_v4.frozen_inference.history.verified_snapshot', reject)
    monkeypatch.setattr(service, 'FrozenModel', lambda: pytest.fail('history gate bypassed'))
    result = infer(Connection, 1)
    assert result['error_code'] == 'HISTORY_INCOMPLETE'
    assert result['prediction'] is None and result['suspicious_probability'] is None
    assert calls == ['rollback', 'close']


def test_source_validation_uses_verified_connection_and_fails_closed(monkeypatch):
    calls = []
    class Connection:
        def rollback(self): calls.append('rollback')
        def close(self): calls.append('close')
    connection = Connection()
    def snapshot(conn, tx):
        assert conn is connection and tx == 1
        calls.append('verified')
        return [], {}
    def reject(conn):
        assert conn is connection and calls == ['verified']
        calls.append('source')
        raise service.Failure('HISTORY_INCOMPLETE')
    monkeypatch.setattr('ml_v4.frozen_inference.history.verified_snapshot', snapshot)
    monkeypatch.setattr(service, 'FrozenModel', lambda: pytest.fail('source gate bypassed'))
    result = infer(lambda: connection, 1, source_validator=reject)
    assert result['error_code'] == 'HISTORY_INCOMPLETE'
    assert result['prediction'] is None
    assert calls == ['verified', 'source', 'rollback', 'close']


@pytest.mark.parametrize('seed', range(12))
def test_dense_network_summary_matches_every_frozen_feature(model, seed):
    from v4_graph_acceleration import certified_summary
    rng = random.Random(seed)
    rows = []
    start = datetime(2026, 10, 20, tzinfo=timezone.utc)
    for i in range(70):
        sender, receiver = rng.sample(['A', 'B', 'C', 'D', 'E', 'F'], 2)
        rows.append(dict(transaction_id=i+1,
            event_timestamp=(start + timedelta(seconds=i//2)).isoformat(timespec='microseconds').replace('+00:00','Z'),
            sender_wallet=sender, receiver_wallet=receiver, amount_minor=rng.choice([100,200,300,950000]),
            currency='USD', transaction_type='wallet_to_wallet', channel='direct_wallet',
            agent_id='', serviced_wallet='', agent_flow_direction='none'))
    # Replaying only the target with the original frozen step is the independent oracle.
    state = model.extractor.Extractor()
    for raw in rows[:-1]:
        event = model.contract.Event(**raw)
        state.step(event)
    current = model.contract.Event(**rows[-1])
    summary = certified_summary(state, current, model.contract.DAY)
    assert summary is not None  # Includes a certified minimum-spread return route.
    expected = state.step(current)
    actual, _ = replay_target(model, rows, current.transaction_id)
    for i, name in enumerate(model.names):
        np.testing.assert_array_equal(actual[name], [expected[i]])


def test_nonuniform_path_preserves_exact_fraction_rank(model):
    from v4_graph_acceleration import exact_step, certified_summary
    rows = history()[:3]
    for i, (sender, receiver, amount) in enumerate([('A','B',100),('B','C',200),('C','A',300)]):
        rows[i].update(sender_wallet=sender, receiver_wallet=receiver, amount_minor=amount,
                       transaction_type='wallet_to_wallet', channel='direct_wallet', agent_id='',
                       serviced_wallet='', agent_flow_direction='none')
    states = [model.extractor.Extractor(), model.extractor.Extractor()]
    for state in states:
        for raw in rows[:2]: state.step(model.contract.Event(**raw))
    current = model.contract.Event(**rows[2])
    summary = certified_summary(states[0], current, model.contract.DAY)
    assert summary[0] == 1 and summary[1] == 2
    assert summary[2][0][0] == 2
    expected, actual = states[0].step(current), exact_step(model, states[1], current)
    np.testing.assert_array_equal(actual, expected)


@pytest.mark.parametrize('seed', range(20))
def test_nonuniform_layered_graph_rank_and_features_match_frozen(model, seed):
    rng = random.Random(seed)
    start = datetime(2026, 10, 20, tzinfo=timezone.utc)
    rows = []
    # No direct return edge and distinct amounts: exercises the minimax pass,
    # all path lengths and exact lexicographic ties after spread masking.
    pairs = [('A','B'),('A','C'),('B','D'),('C','D'),('B','E'),('C','E'),
             ('D','F'),('E','F'),('D','G'),('E','G'),('F','H'),('G','H'),('D','H')]
    for i in range(60):
        sender, receiver = pairs[rng.randrange(len(pairs))]
        rows.append(dict(transaction_id=i+1,
            event_timestamp=(start+timedelta(seconds=i//2)).isoformat(timespec='microseconds').replace('+00:00','Z'),
            sender_wallet=sender, receiver_wallet=receiver, amount_minor=101+i*13+rng.randrange(13),
            currency='USD',transaction_type='wallet_to_wallet',channel='direct_wallet',
            agent_id='',serviced_wallet='',agent_flow_direction='none'))
    rows.append({**rows[-1], 'transaction_id':61, 'sender_wallet':'H', 'receiver_wallet':'A'})
    state = model.extractor.Extractor()
    for raw in rows[:-1]: state.step(model.contract.Event(**raw))
    expected = state.step(model.contract.Event(**rows[-1]))
    actual, _ = replay_target(model, rows, 61)
    for i, name in enumerate(model.names):
        np.testing.assert_array_equal(actual[name], [expected[i]])
