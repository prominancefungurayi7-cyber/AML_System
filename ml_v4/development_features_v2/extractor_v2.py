"""Stage21 observable-only extension. Frozen original extractor remains unchanged."""
from collections import defaultdict, deque
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from ml_v4.development_features.extractor import Extractor as OriginalExtractor, NAMES as ORIGINAL_NAMES
from stage16r_contract import Event, DAY, validate_event

VERSION = 'v4.features.2.experimental.stage21.1'
ADDED_NAMES = (
    'wallet_similar_amount_value_minor_7d',
    'wallet_baseline_similar_amount_count_28d_offset_7d',
    'wallet_near_band_distinct_amount_count_7d',
    'wallet_baseline_near_band_count_28d_offset_7d',
)
NAMES = ORIGINAL_NAMES + ADDED_NAMES
MAX_EXACT_INTEGER = 2**53-1


def exact_float(value):
    if type(value) is not int or not -1 <= value <= MAX_EXACT_INTEGER:
        raise OverflowError('Feature aggregate is not an exactly representable permitted integer')
    return float(value)


class AdditionalExtractor:
    """Independent rolling activity/observation state; no access to original state."""
    def __init__(self):
        self.activity = defaultdict(deque)
        self.first = {}
        self.ids = set()
        self.last = None

    def step(self, event):
        if type(event) is not Event:
            raise TypeError('Only the exact observable Event interface is permitted')
        validate_event(event)
        if event.transaction_id in self.ids or (self.last is not None and event.key <= self.last):
            raise ValueError('Duplicate ID or nonincreasing full key')
        t, wallet = event.time, event.subject
        # Do not advance state on a rejected aggregate.
        history = [e for e in self.activity[wallet] if e.time > t-35*DAY]
        recent = [e for e in history if e.time > t-7*DAY] + [event]
        baseline = [e for e in history if e.time <= t-7*DAY]
        observed = self.first.get(wallet)
        eligible = observed is not None and observed <= t-35*DAY and len(baseline) >= 4
        similar_sum = sum(e.amount_minor for e in recent
                          if 20*abs(e.amount_minor-event.amount_minor) <= event.amount_minor)
        prior_similar = sum(20*abs(e.amount_minor-event.amount_minor) <= event.amount_minor
                            for e in baseline) if eligible else -1
        distinct_band = len({e.amount_minor for e in recent if 700000 <= e.amount_minor <= 1050000})
        prior_band = sum(700000 <= e.amount_minor <= 1050000 for e in baseline) if eligible else -1
        result = tuple(exact_float(n) for n in (similar_sum, prior_similar, distinct_band, prior_band))
        self.activity[wallet] = deque(history)
        self.activity[wallet].append(event)
        for endpoint in (event.sender_wallet, event.receiver_wallet):
            self.first.setdefault(endpoint, t)
        self.ids.add(event.transaction_id)
        self.last = event.key
        return result


class Extractor:
    def __init__(self):
        self.original = OriginalExtractor()
        self.additional = AdditionalExtractor()
        self.failed = False

    def step(self, event):
        if self.failed:
            raise RuntimeError('Extractor failed; create a fresh state and replay validated input')
        try:
            new = self.additional.step(event)
            old = self.original.step(event)
        except Exception:
            self.failed = True
            raise
        return old + new
