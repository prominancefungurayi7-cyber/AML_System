"""Causal Stage 6 candidate extraction; the frozen 30-feature pipeline is untouched."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import timedelta
import math

from contracts import ROOT, load_development
from feature_pipeline import ts

NAMES = [
    'network_prior_bidirectional_counterparty_count_7d',
    'network_prior_return_flow_share_7d',
    'receiver_prior_unique_senders_24h',
    'receiver_prior_inbound_count_24h',
    'agent_wallet_arrival_ratio_7d',
    'agent_top_wallet_count_share_24h',
    'agent_cash_value_imbalance_7d',
    'agent_cash_count_imbalance_7d',
]
GROUPS = {'network': NAMES[:2], 'receiver': NAMES[2:4],
          'agent_growth_concentration': NAMES[4:6], 'agent_flow': NAMES[6:]}


def extract_rows(raw_events):
    """Return candidate matrix and IDs in sorted event order, with no labels read."""
    events = []
    for raw in raw_events:
        e = dict(raw)
        e['transaction_id'] = int(e['transaction_id'])
        e['_time'] = ts(e['event_timestamp'])
        e['_usd'] = int(e['amount_minor']) / 100.0
        events.append(e)
    events.sort(key=lambda e: (e['_time'], e['transaction_id']))
    outbound, inbound, agents = defaultdict(list), defaultdict(list), defaultdict(list)
    matrix, ids = [], []
    for e in events:
        now = e['_time']
        sender, receiver = e['sender_wallet'], e['receiver_wallet']
        lo7, lo24, lo14 = now-timedelta(days=7), now-timedelta(hours=24), now-timedelta(days=14)
        out = [h for h in outbound[sender] if h['_time'] >= lo7]
        inc = [h for h in inbound[sender] if h['_time'] >= lo7]
        out_value, in_value = defaultdict(float), defaultdict(float)
        for h in out: out_value[h['receiver_wallet']] += h['_usd']
        for h in inc: in_value[h['sender_wallet']] += h['_usd']
        both = out_value.keys() & in_value.keys()
        total = sum(out_value.values()) + sum(in_value.values())
        returned = sum(min(out_value[w], in_value[w]) for w in both)
        receiver_prior = [h for h in inbound[receiver] if h['_time'] >= lo24]
        row = [float(len(both)), returned/total if total else 0.0,
               float(len({h['sender_wallet'] for h in receiver_prior})), float(len(receiver_prior))]
        agent_id = e['agent_id']
        if agent_id:
            history = agents[agent_id]
            recent = [h for h in history if h['_time'] >= lo7]
            previous = {h['serviced_wallet'] for h in history if lo14 <= h['_time'] < lo7}
            wallets = {h['serviced_wallet'] for h in recent}
            short = [h for h in history if h['_time'] >= lo24]
            counts = Counter(h['serviced_wallet'] for h in short)
            cash_in = [h for h in recent if h['transaction_type'] == 'cash_in']
            cash_out = [h for h in recent if h['transaction_type'] == 'cash_out']
            in_usd = sum(h['_usd'] for h in cash_in)
            out_usd = sum(h['_usd'] for h in cash_out)
            cash_n = len(cash_in) + len(cash_out)
            cash_v = in_usd + out_usd
            row += [len(wallets-previous)/len(wallets) if wallets else 0.0,
                    max(counts.values())/len(short) if short else 0.0,
                    (out_usd-in_usd)/cash_v if cash_v else 0.0,
                    (len(cash_out)-len(cash_in))/cash_n if cash_n else 0.0]
        else:
            row += [0.0]*4
        if len(row) != len(NAMES) or not all(math.isfinite(x) for x in row):
            raise ValueError('Invalid Stage 6 feature vector')
        matrix.append(row)
        ids.append(e['transaction_id'])
        if e['transaction_type'] == 'wallet_to_wallet':
            outbound[sender].append(e)
            inbound[receiver].append(e)
        if agent_id:
            agents[agent_id].append(e)
    return matrix, ids


def extract_development(partition):
    if partition not in ('train', 'validation'):
        raise PermissionError('Stage 6 extraction is development-only')
    return extract_rows(load_development(ROOT/'data', partition, 'transactions'))
