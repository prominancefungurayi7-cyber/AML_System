import json
import os
import re

import server as aml_app


def _dashboard_data(response):
    match = re.search(
        r'<script id="compliance-dashboard-data" type="application/json">(.*?)</script>',
        response.get_data(as_text=True),
        re.DOTALL,
    )
    assert match
    return json.loads(match.group(1))


def test_resolving_an_alert_redirects_to_next_open_alert():
    aml_app.app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret",
        DATABASE=str(aml_app.TestingConfig.DATABASE_URL),
    )
    if os.path.exists(aml_app.app.config["DATABASE"]):
        try:
            os.remove(aml_app.app.config["DATABASE"])
        except PermissionError:
            pass

    with aml_app.app.test_client() as client:
        with aml_app.app.app_context():
            aml_app.init_db()
            aml_app.seed_demo_data()
            conn = aml_app.get_db()
            conn.execute(
                "DELETE FROM alerts"
            )
            conn.execute(
                "INSERT INTO alerts (transaction_id, account_number, risk_score, risk_level, reason, rules_triggered, status, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (101, "ACC1001", 70, "suspicious", "First alert", "[]", "open", "2026-01-01T00:00:00+00:00"),
            )
            conn.execute(
                "INSERT INTO alerts (transaction_id, account_number, risk_score, risk_level, reason, rules_triggered, status, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (102, "ACC1002", 80, "high_risk", "Second alert", "[]", "open", "2026-01-01T00:01:00+00:00"),
            )
            conn.commit()

        client.post(
            "/login",
            data={"login": "Compliance", "password": "Compliance123"},
            follow_redirects=True,
        )

        response = client.post(
            "/compliance/alert/1",
            data={"action": "resolve", "case_notes": "Reviewed"},
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert response.headers["Location"].endswith("/compliance/alert/2")

        with aml_app.app.app_context():
            updated = aml_app.get_db().execute("SELECT status FROM alerts WHERE id=1").fetchone()
            next_alert = aml_app.get_db().execute("SELECT status FROM alerts WHERE id=2").fetchone()
            assert updated["status"] == "resolved"
            assert next_alert["status"] == "open"


def test_compliance_dashboard_paginates_all_open_alerts():
    aml_app.app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret",
        DATABASE=str(aml_app.TestingConfig.DATABASE_URL),
    )
    if os.path.exists(aml_app.app.config["DATABASE"]):
        try:
            os.remove(aml_app.app.config["DATABASE"])
        except PermissionError:
            pass

    with aml_app.app.test_client() as client:
        with aml_app.app.app_context():
            aml_app.init_db()
            aml_app.seed_demo_data()
            conn = aml_app.get_db()
            conn.execute("DELETE FROM alerts")
            for number in range(26):
                conn.execute(
                    "INSERT INTO alerts (transaction_id, account_number, risk_score, risk_level, reason, rules_triggered, status, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (number + 1, "ACC1001", 70, "suspicious", "Review queue", "[]", "open", f"2026-01-01T00:{number:02d}:00+00:00"),
                )
            conn.commit()

        client.post(
            "/login",
            data={"login": "Compliance", "password": "Compliance123"},
            follow_redirects=True,
        )

        first_page = _dashboard_data(client.get("/compliance"))
        second_page = _dashboard_data(client.get("/compliance?alert_page=2"))

        assert first_page["open_alert_count"] == 26
        assert first_page["alert_page"] == 1
        assert len(first_page["open_alerts"]) == 25
        assert second_page["alert_page"] == 2
        assert len(second_page["open_alerts"]) == 1
