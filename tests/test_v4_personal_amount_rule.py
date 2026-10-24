"""Nonfinancial regression coverage for V4's independent personal amount rule."""
import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from aml_rules import assess_rules


NOW = datetime(2026, 10, 17, 12, tzinfo=timezone.utc)


@pytest.fixture
def history():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE transactions (
        id INTEGER PRIMARY KEY, amount REAL, transaction_type TEXT,
        sender_account TEXT, receiver_account TEXT, timestamp TEXT,
        status TEXT, ai_risk_level TEXT)""")
    yield conn
    conn.close()


def add(conn, amount=100, *, day=1, timestamp=None, sender="A", tx_type="transfer",
        status="Completed", transaction_id=None, ai_risk_level="normal"):
    timestamp = timestamp or NOW - timedelta(days=day)
    stamp = timestamp if isinstance(timestamp, str) else timestamp.isoformat()
    cursor = conn.execute(
        """INSERT INTO transactions (id, amount, transaction_type, sender_account,
        receiver_account, timestamp, status, ai_risk_level) VALUES (?,?,?,?,?,?,?,?)""",
        (transaction_id, amount, tx_type, sender, "B",
         stamp, status, ai_risk_level),
    )
    return cursor.lastrowid


def established(conn, amounts=(90, 100, 110, 95, 105), **kwargs):
    for day, amount in enumerate(amounts, 1):
        add(conn, amount, day=day, **kwargs)


def assess(conn, amount=1000, *, personal_amount_check=True, **kwargs):
    params = dict(amount=amount, tx_type="transfer", sender="A", receiver="B",
                  timestamp=NOW.isoformat(), personal_amount_check=personal_amount_check)
    params.update(kwargs)
    return assess_rules(conn, **params)


def personal(results):
    return [result for result in results if result.rule_id == "R12"]


def test_v4_personal_amount_deviation_is_an_independent_rule(history):
    established(history)
    result, = personal(assess(history))
    assert result.score_delta >= 40
    assert result.reason
    assert result.evidence
    assert result.payload()["triggered"] is True
    assert result.payload()["rule_id"] == "R12"
    assert not any(word in result.reason.lower() for word in ("xgboost", "prediction"))


def test_ordinary_amount_in_established_range_is_not_flagged(history):
    established(history)
    assert not personal(assess(history, amount=105))


@pytest.mark.parametrize("samples", [0, 1, 4])
def test_cold_start_does_not_invent_personal_history(history, samples):
    established(history, amounts=(100,) * samples)
    assert not personal(assess(history))


def test_constant_history_still_detects_large_deviation(history):
    established(history, amounts=(100,) * 5)
    assert len(personal(assess(history))) == 1


def test_unusually_small_payment_is_also_a_personal_deviation(history):
    established(history, amounts=(100,) * 5)
    low, = personal(assess(history, amount=1))
    high, = personal(assess(history, amount=1000))
    assert low.evidence["direction"] != high.evidence["direction"]
    assert low.score_delta == high.score_delta == 40


@pytest.mark.parametrize("amount,expected", [
    (300, False), (300.01, True), (100 / 3, False), (33, True),
])
def test_amount_must_be_strictly_outside_personal_review_limits(history, amount, expected):
    established(history, amounts=(100,) * 5)
    assert bool(personal(assess(history, amount=amount))) is expected


def test_broad_established_amount_variation_does_not_create_spurious_range_flag(history):
    established(history, amounts=(1, 10, 100, 1000, 10000))
    assert not personal(assess(history, amount=5000))
    assert not personal(assess(history, amount=0.01))


def test_rule_evidence_records_real_baseline_and_reference_transaction(history):
    established(history, amounts=(100,) * 5)
    current_id = add(history, 1000, timestamp=NOW)
    result, = personal(assess(history, exclude_transaction_id=current_id))
    assert result.evidence["sample_count"] == 5
    assert result.evidence["window_days"] == 30
    assert result.evidence["sample_limit"] == 100
    assert result.evidence["mean_amount"] == 100
    assert result.evidence["median_amount"] == 100
    assert result.evidence["std_amount"] == 0
    assert result.evidence["lower_amount"] == pytest.approx(100 / 3, abs=0.01)
    assert result.evidence["upper_amount"] == 300
    assert result.evidence["amount"] == 1000
    assert result.evidence["reference_timestamp"] == NOW.isoformat()
    assert result.evidence["reference_transaction_id"] == current_id


def test_disabled_personal_check_retains_existing_independent_rules(history):
    established(history)
    results = assess(history, amount=9500, personal_amount_check=False,
                     destination_country="IR")
    assert not personal(results)
    assert {"R02", "R07", "R11"} <= {result.rule_id for result in results}


def test_personal_check_is_opt_in_for_legacy_callers(history):
    established(history)
    results = assess_rules(history, amount=1000, tx_type="transfer", sender="A",
                           receiver="B", timestamp=NOW.isoformat())
    assert not personal(results)


def test_personal_check_preserves_existing_rules_when_enabled(history):
    established(history)
    results = assess(history, amount=9500, destination_country="IR")
    assert {"R02", "R07", "R11", "R12"} <= {result.rule_id for result in results}


def test_future_later_same_time_and_current_rows_cannot_supply_baseline(history):
    established(history, amounts=(100,) * 4)
    current_id = add(history, 1000, timestamp=NOW, transaction_id=50)
    for index in range(6):
        add(history, 100, timestamp=NOW, transaction_id=51 + index)
        add(history, 100, timestamp=NOW + timedelta(seconds=1), transaction_id=61 + index)
    assert not personal(assess(history, exclude_transaction_id=current_id))


def test_same_timestamp_earlier_transaction_is_valid_history(history):
    established(history, amounts=(100,) * 4)
    add(history, 100, timestamp=NOW, transaction_id=10)
    current_id = add(history, 1000, timestamp=NOW, transaction_id=20)
    assert len(personal(assess(history, exclude_transaction_id=current_id))) == 1


@pytest.mark.parametrize("earlier_stamp,later_stamp", [
    ("2026-10-17T12:00:00.000000Z", "2026-10-17T12:00:00+00:00"),
    ("2026-10-17T12:00:00+00:00", "2026-10-17T12:00:00.000000Z"),
])
def test_equal_utc_instants_use_ids_across_timestamp_representations(
        history, earlier_stamp, later_stamp):
    established(history, amounts=(100,) * 4)
    add(history, 100, timestamp=earlier_stamp, transaction_id=10)
    current_id = add(history, 1000, timestamp="2026-10-17T12:00:00.000000Z", transaction_id=20)
    add(history, 1000, timestamp=later_stamp, transaction_id=30)
    result, = personal(assess(history, exclude_transaction_id=current_id))
    assert result.evidence["sample_count"] == 5
    assert result.evidence["median_amount"] == 100


def test_persisted_reference_time_excludes_self_and_later_ids_when_input_has_extra_precision(history):
    established(history, amounts=(100,) * 4)
    stamp = "2026-10-17T12:00:00.000000Z"
    add(history, 100, timestamp=stamp, transaction_id=10)
    current_id = add(history, 1000, timestamp=stamp, transaction_id=20)
    add(history, 1000, timestamp=stamp, transaction_id=30)
    result, = personal(assess(history, exclude_transaction_id=current_id,
                             timestamp=(NOW + timedelta(microseconds=987654)).isoformat()))
    assert result.evidence["sample_count"] == 5
    assert result.evidence["mean_amount"] == 100
    assert result.evidence["reference_timestamp"] == NOW.isoformat()


@pytest.mark.parametrize("boundary_stamp", [
    "2026-09-17T12:00:00.000000Z",
    "2026-09-17T12:00:00+00:00",
    "2026-09-17T14:00:00+02:00",
])
def test_30_day_boundary_uses_equivalent_utc_instants(history, boundary_stamp):
    established(history, amounts=(100,) * 4)
    add(history, 100, timestamp=boundary_stamp)
    result, = personal(assess(history))
    assert result.evidence["sample_count"] == 5


def test_older_than_30_day_boundary_is_excluded_despite_timezone_text_order(history):
    established(history, amounts=(100,) * 4)
    add(history, 100, timestamp="2026-09-17T13:59:59.999999+02:00")
    assert not personal(assess(history))


@pytest.mark.parametrize("excluded", [
    {"sender": "OTHER"},
    {"tx_type": "deposit"},
    {"status": "Failed"},
    {"status": "Cancelled"},
    {"status": "Pending"},
    {"day": 31},
])
def test_unrelated_or_uncommitted_history_cannot_fill_baseline(history, excluded):
    established(history, amounts=(100,) * 4)
    add(history, 100, **excluded)
    assert not personal(assess(history))


def test_existing_ai_labels_do_not_filter_personal_history(history):
    established(history, amounts=(100,) * 5, ai_risk_level="suspicious_pattern")
    assert len(personal(assess(history))) == 1


def test_personal_baseline_is_limited_to_latest_100_payments(history):
    for index in range(101):
        add(history, 10000, timestamp=NOW - timedelta(days=20) + timedelta(minutes=index))
    for index in range(100):
        add(history, 100, timestamp=NOW - timedelta(days=2) + timedelta(minutes=index))
    result, = personal(assess(history))
    assert result.evidence["sample_count"] == 100


def test_exact_30_day_boundary_is_included_in_personal_history(history):
    established(history, amounts=(100,) * 4)
    add(history, 100, day=30)
    assert len(personal(assess(history))) == 1


def test_rule_assessment_has_no_financial_or_history_side_effects(history):
    established(history)
    before = [tuple(row) for row in history.execute("SELECT * FROM transactions ORDER BY id")]
    changes_before = history.total_changes
    assert personal(assess(history))
    assert history.total_changes == changes_before
    assert [tuple(row) for row in history.execute("SELECT * FROM transactions ORDER BY id")] == before
