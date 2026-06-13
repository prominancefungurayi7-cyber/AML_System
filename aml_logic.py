from datetime import datetime, timedelta


def analyze_transaction(conn, tx_type, amount, sender, receiver, timestamp):
    threshold = datetime.fromisoformat(timestamp) - timedelta(minutes=15)
    recent_transactions = conn.execute(
        """
        SELECT amount, transaction_type, sender_account, receiver_account, timestamp
        FROM transactions
        WHERE timestamp >= ?
        ORDER BY timestamp DESC
        LIMIT 20
        """,
        (threshold.isoformat(),),
    ).fetchall()

    recent_deposits = [row for row in recent_transactions if row["transaction_type"] == "deposit"]
    recent_transfers = [row for row in recent_transactions if row["transaction_type"] == "transfer"]
    recipient_accounts = {row["receiver_account"] for row in recent_transfers if row["receiver_account"]}
    recent_transfer_value = sum(float(row["amount"] or 0) for row in recent_transfers)

    risk_score = 10
    if tx_type == "withdraw":
        risk_score += 10
    elif tx_type == "transfer":
        risk_score += 20
        if len(recent_transfers) >= 3:
            risk_score += 20
        if len(recipient_accounts) >= 3:
            risk_score += 20
        if recent_transfer_value >= 5000:
            risk_score += 20

    if tx_type == "deposit" and len(recent_deposits) >= 3 and amount < 100:
        risk_score += 25

    if amount >= 1000:
        risk_score += 35
    elif amount >= 500:
        risk_score += 20

    if sender == receiver:
        risk_score += 20

    risk_score = min(int(risk_score), 100)
    if risk_score >= 70:
        level = "high risk"
    elif risk_score >= 35:
        level = "suspicious"
    else:
        level = "normal"

    reason = "Routine transaction"
    if tx_type == "transfer" and amount >= 1000:
        reason = "Large transfer volume detected"
    elif tx_type == "transfer" and len(recent_transfers) >= 3:
        reason = "Rapid movement of funds across multiple transfers"
    elif tx_type == "deposit" and len(recent_deposits) >= 3 and amount < 100:
        reason = "Many small deposits observed in a short period"
    elif tx_type == "transfer" and len(recipient_accounts) >= 3:
        reason = "Transfers to many different accounts"
    elif tx_type == "transfer" and recent_transfer_value >= 5000:
        reason = "Unusual transfer velocity observed"
    elif level == "suspicious":
        reason = "Unusual transaction pattern"

    return risk_score, level, reason
