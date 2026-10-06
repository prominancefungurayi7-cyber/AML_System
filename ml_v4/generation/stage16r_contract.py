"""Observable-only schema and exact temporal primitives for V4 Stage 16R."""
from __future__ import annotations
import csv
import hashlib
import io
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from functools import lru_cache

DAY = 86400_000000
HOUR = DAY // 24
START = datetime(2027, 1, 1, tzinfo=timezone.utc)
FIELDS = ('transaction_id event_timestamp sender_wallet receiver_wallet amount_minor currency transaction_type channel agent_id serviced_wallet agent_flow_direction').split()
FAMILIES = 'S1 S2 S3 S4 N1 N2 N3 N4 A1 A2 A3 A4'.split()
ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=32768)
def time_us(value):
    delta = datetime.fromisoformat(value.replace('Z', '+00:00')) - START
    return (delta.days * 86400 + delta.seconds) * 1_000000 + delta.microseconds


@dataclass(frozen=True, slots=True)
class Event:
    transaction_id: int
    event_timestamp: str
    sender_wallet: str
    receiver_wallet: str
    amount_minor: int
    currency: str
    transaction_type: str
    channel: str
    agent_id: str
    serviced_wallet: str
    agent_flow_direction: str

    @property
    def time(self):
        return time_us(self.event_timestamp)

    @property
    def key(self):
        return self.time, self.transaction_id

    @property
    def subject(self):
        return self.sender_wallet if self.transaction_type == 'wallet_to_wallet' else self.serviced_wallet


def timestamp(microseconds):
    return (START + timedelta(microseconds=int(microseconds))).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def validate_event(e):
    if type(e.transaction_id) is not int or not 0 < e.transaction_id < 2**63:
        raise ValueError('Invalid transaction ID')
    if type(e.amount_minor) is not int or not 1 <= e.amount_minor <= 1500000 or e.currency != 'USD':
        raise ValueError('Invalid amount/currency')
    if timestamp(e.time) != e.event_timestamp or not e.sender_wallet or not e.receiver_wallet:
        raise ValueError('Invalid timestamp/endpoint')
    if e.transaction_type == 'wallet_to_wallet':
        if e.sender_wallet == e.receiver_wallet or e.agent_flow_direction != 'none':
            raise ValueError('Invalid W2W')
        if e.channel == 'direct_wallet':
            if e.agent_id or e.serviced_wallet:
                raise ValueError('Direct W2W has agent')
        elif e.channel != 'agent' or not e.agent_id or e.serviced_wallet not in (e.sender_wallet, e.receiver_wallet):
            raise ValueError('Invalid assisted W2W')
    elif e.transaction_type in ('cash_in', 'cash_out'):
        if e.channel != 'agent' or not e.agent_id or not e.sender_wallet == e.receiver_wallet == e.serviced_wallet or e.agent_flow_direction != e.transaction_type:
            raise ValueError('Invalid cash role')
    else:
        raise ValueError('Invalid type')


def event_from_row(row):
    if set(row) != set(FIELDS):
        raise ValueError('Observable input has missing or private columns')
    row = dict(row)
    row['transaction_id'] = int(row['transaction_id'])
    row['amount_minor'] = int(row['amount_minor'])
    e = Event(**row)
    validate_event(e)
    return e


def event_csv(events):
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=FIELDS, lineterminator='\n')
    writer.writeheader()
    writer.writerows(asdict(e) for e in events)
    return out.getvalue().encode()


def read_events(path):
    with Path(path).open(encoding='utf-8', newline='') as stream:
        return [event_from_row(row) for row in csv.DictReader(stream)]


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(json_bytes(value))


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def median(values):
    from fractions import Fraction
    values = sorted(values)
    n = len(values)
    return Fraction(values[n//2]) if n % 2 else Fraction(values[n//2-1] + values[n//2], 2)


def window(events, low, high):
    return [e for e in events if low < e.time <= high]
