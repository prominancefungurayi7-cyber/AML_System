"""Every wallet payment stays reachable from the customer's paged dashboard."""
import json
import re


def test_customer_history_covers_all_pages_and_separates_risk_evidence(aml_app):
    db = aml_app.connect_db()
    try:
        for i in range(27):
            db.execute(
                "INSERT INTO transactions (sender_account,receiver_account,amount,transaction_type,"
                "risk_level,rule_level,ai_risk_level,ai_reason,rule_reason) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                ('ACC1003', 'ACC1004', 1 + i / 100, 'wallet_to_wallet',
                 'critical' if i == 26 else 'low', 'low', 'suspicious_pattern' if i == 26 else 'normal',
                 f'AI result {i}', f'Rule result {i}'),
            )
        db.commit()
        user = db.execute("SELECT id FROM users WHERE account_number='ACC1003'").fetchone()
    finally:
        db.close()
    client = aml_app.app.test_client()
    with client.session_transaction() as state:
        state.update(user_id=user['id'], username='demo', role='customer',
                     auth_token=aml_app.auth_sessions.create(user['id'], 3600))

    all_rows = []
    for page in (1, 2):
        response = client.get(f'/customer?page={page}')
        assert response.status_code == 200
        match = re.search(r'<script id="customer-dashboard-data" type="application/json">(.*?)</script>',
                          response.get_data(as_text=True), re.S)
        data = json.loads(match.group(1))
        assert data['transaction_pages'] == 2
        all_rows.extend(data['transactions'])
    assert len(all_rows) == 27
    assert len({row['id'] for row in all_rows}) == 27
    assert all_rows[0]['risk_level'] == 'critical'
    assert all_rows[0]['ai_reason'] == 'AI result 26'
    assert all_rows[0]['rule_reason'] == 'Rule result 26'
    assert data['stats']['flagged'] == 1
