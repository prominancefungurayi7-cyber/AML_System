"""Prospective observable events only; no feature extraction or model loading."""
from dataclasses import asdict, replace
from datetime import datetime, timezone
from decimal import Decimal
import re

from ml_v4.generation.stage16r_contract import Event, validate_event

VERSION = 'mobile_money.canonical.v1'
FIELDS = tuple(Event.__dataclass_fields__)
LEGACY_TYPES = {'wallet_to_wallet': 'transfer', 'cash_in': 'deposit', 'cash_out': 'withdraw'}


def cents(text, currency='USD'):
    if currency != 'USD' or type(text) is not str or not re.fullmatch(r'[0-9]{1,5}(?:\.[0-9]{1,2})?', text):
        raise ValueError('Use positive USD amounts with at most two decimal places')
    amount = Decimal(text) * 100
    if amount != amount.to_integral_value() or not 1 <= amount <= 1500000:
        raise ValueError('Amount must be USD 0.01 through 15000.00')
    return int(amount)


def utc_timestamp(value):
    """Normalize an explicitly offset ISO instant, never infer a timezone."""
    if type(value) is not str or not re.fullmatch(
        r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})', value
    ):
        raise ValueError('An explicit UTC/offset timestamp with at most microsecond precision is required')
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.utcoffset() is None:
        raise ValueError('Unknown timezone')
    return dt.astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def event_from_dict(raw):
    if type(raw) is not dict or set(raw) != set(FIELDS):
        raise ValueError('Exact observable event fields required')
    for name in FIELDS:
        if name not in ('transaction_id', 'amount_minor'):
            value = raw[name]
            if type(value) is not str or len(value) > 255 or value != value.strip() or any(ord(c) < 32 for c in value):
                raise ValueError('Invalid text field: ' + name)
    if utc_timestamp(raw['event_timestamp']) != raw['event_timestamp']:
        raise ValueError('Canonical timestamps require UTC and six fractional digits')
    event = Event(**raw)
    validate_event(event)
    return event


def serialize(event):
    raw = asdict(event)
    event_from_dict(raw)
    return raw


def prepare_ingestion(form, sender_wallet, timestamp):
    """Explicit mobile-money form; placeholder ID is replaced by DB-generated ID."""
    required = {'canonical_version', 'type', 'amount', 'currency', 'channel', 'agent_id', 'serviced_wallet', 'agent_flow_direction', 'recipient'}
    if set(form) != required or form['canonical_version'] != VERSION:
        raise ValueError('Exact versioned mobile-money form required')
    tx_type = form['type']
    if tx_type not in LEGACY_TYPES:
        raise ValueError('Unknown mobile-money type')
    if tx_type != 'wallet_to_wallet' and form['recipient']:
        raise ValueError('Cash events must not name a transfer recipient')
    receiver = form['recipient'] if tx_type == 'wallet_to_wallet' else sender_wallet
    return event_from_dict(dict(transaction_id=1, event_timestamp=utc_timestamp(timestamp),
        sender_wallet=sender_wallet, receiver_wallet=receiver, amount_minor=cents(form['amount'], form['currency']),
        currency=form['currency'], transaction_type=tx_type, channel=form['channel'], agent_id=form['agent_id'],
        serviced_wallet=form['serviced_wallet'], agent_flow_direction=form['agent_flow_direction']))


def with_id(event, transaction_id):
    return event_from_dict(asdict(replace(event, transaction_id=transaction_id)))


def classify_history(canonical=None, trustworthy_conversion=None):
    """No legacy inference/backfill. A candidate conversion needs external provenance."""
    if canonical is not None:
        try:
            if canonical['canonical_version'] != VERSION:
                return 'LEGACY_AMBIGUOUS'
            event_from_dict({k: canonical[k] for k in FIELDS})
            return 'CANONICAL_VERIFIED'
        except (KeyError, ValueError, TypeError):
            return 'LEGACY_AMBIGUOUS'
    # Deliberately no converter from legacy floating amounts or banking role names.
    # LEGACY_CONVERTIBLE is a review classification, never automatic replay authority.
    if trustworthy_conversion is not None:
        if (type(trustworthy_conversion) is dict and
            set(trustworthy_conversion) == {'event', 'authority_reference', 'verified_by'} and
            all(type(trustworthy_conversion[k]) is str and trustworthy_conversion[k].strip()
                for k in ('authority_reference', 'verified_by'))):
            event_from_dict(trustworthy_conversion['event'])
            return 'LEGACY_CONVERTIBLE'
    return 'LEGACY_AMBIGUOUS'
