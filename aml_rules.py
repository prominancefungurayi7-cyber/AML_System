"""Auditable, transaction-time AML typology rules.

These rules intentionally complement—not replace—the statistical and ML models.
They are evaluated against transactions that occurred before the transaction being
assessed, so a transaction never learns from, or triggers on, itself.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
import math
from statistics import fmean, median, pstdev
from typing import Any


CTR_THRESHOLD = 10_000
STRUCTURING_LOW, STRUCTURING_HIGH = 8_500, 9_999
HIGH_RISK_COUNTRIES = {"IR", "KP", "MM", "RU", "SY", "YE", "ML", "BF", "SO"}


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    score_delta: int
    reason: str
    severity: str
    typology: str
    evidence: dict[str, Any]

    def payload(self) -> dict[str, Any]:
        result = asdict(self)
        result["triggered"] = True
        return result


def _time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return datetime.now(timezone.utc)


def _prior(conn, sender: str, timestamp: str, minutes: int, exclude_transaction_id=None) -> list[dict[str, Any]]:
    end = _time(timestamp)
    start = end - timedelta(minutes=minutes)
    if exclude_transaction_id:
        rows = conn.execute(
            """SELECT amount, transaction_type, sender_account, receiver_account, timestamp
               FROM transactions
               WHERE sender_account=? AND id<>? AND timestamp>=? AND timestamp<?
               ORDER BY timestamp ASC, id ASC LIMIT 200""",
            (sender, exclude_transaction_id, start.isoformat(), end.isoformat()),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT amount, transaction_type, sender_account, receiver_account, timestamp
               FROM transactions
               WHERE sender_account=? AND timestamp>=? AND timestamp<?
               ORDER BY timestamp ASC, id ASC LIMIT 200""",
            (sender, start.isoformat(), end.isoformat()),
        ).fetchall()
    return [dict(row) for row in rows]


def _personal_amount_rule(conn, amount, tx_type, sender, timestamp, transaction_id):
    """Compare only causal, completed, comparable payments; never train V4."""
    def utc_time(value):
        value = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return (value if value.tzinfo else value.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)

    if transaction_id is not None:
        current = conn.execute('SELECT timestamp FROM transactions WHERE id=?', (transaction_id,)).fetchone()
        if current is not None:
            timestamp = current['timestamp']
    end = utc_time(timestamp)
    start = end - timedelta(days=30)
    # Parent timestamps include both canonical Z strings and older +00:00
    # strings. SQL string ordering cannot decide equal instants safely. Narrow
    # by dates, then compare normalized UTC (timestamp,id) before taking 100.
    rows = conn.execute(
        "SELECT id,amount,timestamp FROM transactions WHERE sender_account=? AND transaction_type=? "
        "AND status='Completed' AND amount>0 AND timestamp>=? AND timestamp<?",
        (sender, tx_type, (start - timedelta(days=1)).date().isoformat(),
         (end + timedelta(days=2)).date().isoformat())).fetchall()
    prior = []
    for row in rows:
        when = utc_time(row['timestamp'])
        value = float(row['amount'])
        if transaction_id is not None and row['id'] == transaction_id:
            continue
        causal = when < end or (when == end and transaction_id is not None and row['id'] < transaction_id)
        if start <= when and causal and math.isfinite(value):
            prior.append((when, row['id'], value))
    amounts = [row[2] for row in sorted(prior, reverse=True)[:100]]
    if len(amounts) < 5:
        return None
    average, middle, spread = fmean(amounts), median(amounts), pstdev(amounts)
    # The threefold median guard avoids flagging ordinary variation in a stable
    # history; the three-sigma guard also accommodates genuinely broad ranges.
    lower = max(0.0, min(middle / 3, average - 3 * spread))
    upper = max(middle * 3, average + 3 * spread)
    if not math.isfinite(amount) or lower <= amount <= upper:
        return None
    direction = 'above' if amount > upper else 'below'
    reason = (f"Personal amount deviation: ${amount:,.2f} is {direction} the monitoring range "
              f"${lower:,.2f}-${upper:,.2f} from {len(amounts)} prior completed {tx_type} "
              f"payments in 30 days (median ${middle:,.2f}).")
    return RuleResult('R12', 40, reason, 'warning', 'Personal Amount Deviation', dict(
        sample_count=len(amounts), window_days=30, sample_limit=100,
        mean_amount=average, median_amount=middle, std_amount=spread,
        lower_amount=lower, upper_amount=upper, amount=amount, direction=direction,
        reference_timestamp=end.isoformat(), reference_transaction_id=transaction_id,
        method='three_sigma_and_threefold_median', minimum_samples=5))


def assess_rules(conn, *, amount: float, tx_type: str, sender: str, receiver: str,
                 timestamp: str, destination_country: str = "ZW", exclude_transaction_id=None,
                 personal_amount_check: bool = False) -> list[RuleResult]:
    """Return all independent rule hits for one transaction."""
    amount = float(amount)
    prior_hour = _prior(conn, sender, timestamp, 60, exclude_transaction_id)
    prior_day = _prior(conn, sender, timestamp, 24 * 60, exclude_transaction_id)
    hits: list[RuleResult] = []

    def hit(rule_id, points, reason, severity, typology, **evidence):
        hits.append(RuleResult(rule_id, points, reason, severity, typology, evidence))

    if tx_type in ("deposit", "withdraw") and amount >= CTR_THRESHOLD:
        hit("R01", 45, f"Cash transaction of ${amount:,.2f} meets the CTR threshold", "critical", "Large Cash", amount=amount, threshold=CTR_THRESHOLD)
    elif tx_type in ("deposit", "withdraw") and amount >= 3_000:
        hit("R01", 20, f"Large cash transaction of ${amount:,.2f}", "warning", "Large Cash", amount=amount)

    if STRUCTURING_LOW <= amount <= STRUCTURING_HIGH:
        hit("R02", 50, f"${amount:,.2f} falls in the structuring watch band", "critical", "Structuring", amount=amount)

    small_deposits = [row for row in prior_hour if row["transaction_type"] == "deposit" and float(row["amount"]) < 500]
    if tx_type == "deposit" and amount < 500 and len(small_deposits) + 1 >= 3:
        total = amount + sum(float(row["amount"]) for row in small_deposits)
        hit("R03", 40, f"{len(small_deposits) + 1} small cash-ins totalling ${total:,.2f} within 60 minutes", "critical", "Smurfing", count=len(small_deposits) + 1, total=total)

    if len(prior_hour) + 1 >= 5:
        volume = amount + sum(float(row["amount"]) for row in prior_hour)
        hit("R04", 35, f"{len(prior_hour) + 1} transactions totalling ${volume:,.2f} within 60 minutes", "critical", "Velocity / Layering", count=len(prior_hour) + 1, total=volume)

    if tx_type == "transfer":
        recipients = {row["receiver_account"] for row in prior_hour if row["transaction_type"] == "transfer"} | {receiver}
        if len(recipients) >= 3:
            hit("R05", 35, f"Transfers to {len(recipients)} recipients within 60 minutes", "critical", "Fan-Out / Layering", recipients=len(recipients))
        if amount >= 1_000 and amount % 1_000 == 0:
            hit("R06", 15, f"Round-number transfer of ${amount:,.0f}", "info", "Round Amount", amount=amount)
        if amount >= 5_000:
            hit("R07", 30, f"Transfer of ${amount:,.2f} meets SAR review threshold", "critical", "SAR Trigger", amount=amount)

    if tx_type == "transfer" and sender == receiver:
        hit("R08", 25, "Self-transfer indicates a possible pass-through wallet", "warning", "Self-Transfer")

    hourly_outflow = amount + sum(float(row["amount"]) for row in prior_day if row["transaction_type"] in ("transfer", "withdraw"))
    if tx_type in ("transfer", "withdraw") and hourly_outflow > 20_000:
        hit("R09", 30, f"24-hour outflow of ${hourly_outflow:,.2f} exceeds the monitoring threshold", "warning", "Unusual Volume", outflow=hourly_outflow)

    hour = _time(timestamp).hour
    if amount >= 1_000 and (hour < 5 or hour >= 23):
        hit("R10", 20, f"${amount:,.2f} transaction at {hour:02d}:00 is off-hours activity", "warning", "Off-Hours Activity", hour=hour)

    country = (destination_country or "ZW").upper()
    if country in HIGH_RISK_COUNTRIES:
        hit("R11", 55, f"Transaction involves high-risk jurisdiction {country}", "critical", "High-Risk Geography", country=country)

    if personal_amount_check:
        personal = _personal_amount_rule(conn, amount, tx_type, sender, timestamp, exclude_transaction_id)
        if personal is not None:
            hits.append(personal)

    return hits
