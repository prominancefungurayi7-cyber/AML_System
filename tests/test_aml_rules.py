import sqlite3
from datetime import datetime, timedelta, timezone

from aml_rules import assess_rules


def _db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE transactions (
        id INTEGER PRIMARY KEY, amount REAL, transaction_type TEXT,
        sender_account TEXT, receiver_account TEXT, timestamp TEXT)""")
    return conn


def _insert(conn, amount, tx_type, sender, receiver, timestamp):
    conn.execute(
        "INSERT INTO transactions(amount, transaction_type, sender_account, receiver_account, timestamp) VALUES (?,?,?,?,?)",
        (amount, tx_type, sender, receiver, timestamp.isoformat()),
    )


def _ids(results):
    return {result.rule_id for result in results}


def test_structuring_and_high_risk_geography_are_detected():
    conn = _db()
    now = datetime.now(timezone.utc)
    results = assess_rules(conn, amount=9_500, tx_type="transfer", sender="A", receiver="B", timestamp=now.isoformat(), destination_country="IR", exclude_transaction_id=None)
    assert {"R02", "R07", "R11"} <= _ids(results)


def test_velocity_fan_out_and_smurfing_require_real_prior_sequences():
    conn = _db()
    now = datetime.now(timezone.utc)
    for i in range(4):
        _insert(conn, 200, "transfer", "A", f"R{i}", now - timedelta(minutes=10 - i))
    results = assess_rules(conn, amount=200, tx_type="transfer", sender="A", receiver="R5", timestamp=now.isoformat(), exclude_transaction_id=None)
    assert {"R04", "R05"} <= _ids(results)

    conn = _db()
    for i in range(2):
        _insert(conn, 250, "deposit", "A", "A", now - timedelta(minutes=5 - i))
    results = assess_rules(conn, amount=250, tx_type="deposit", sender="A", receiver="A", timestamp=now.isoformat(), exclude_transaction_id=None)
    assert "R03" in _ids(results)


def test_off_hours_and_large_cash_are_detected_independently():
    conn = _db()
    timestamp = datetime(2026, 1, 1, 1, tzinfo=timezone.utc)
    results = assess_rules(conn, amount=12_000, tx_type="withdraw", sender="A", receiver="A", timestamp=timestamp.isoformat(), exclude_transaction_id=None)
    assert {"R01", "R10"} <= _ids(results)
