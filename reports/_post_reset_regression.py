"""Post-reset functional regression (non-destructive)."""
import os
import sys

sys.path.insert(0, ".")
from dotenv import load_dotenv
import mysql.connector
from urllib.parse import urlparse, unquote

load_dotenv(".env")
parsed = urlparse(os.environ["DATABASE_URL"])
cfg = {
    "host": parsed.hostname,
    "port": parsed.port or 3306,
    "user": unquote(parsed.username or ""),
    "password": unquote(parsed.password or ""),
    "database": parsed.path.lstrip("/"),
}

from server import app

results = []


def record(label, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    line = f"{status}: {label}" + (f" — {detail}" if detail else "")
    results.append(line)
    print(line)


conn = mysql.connector.connect(**cfg)
cur = conn.cursor(dictionary=True)

with app.test_client() as client:
    login = client.post(
        "/login", data={"username": "Admin", "password": "Admin123"}, follow_redirects=True
    )
    record("MySQL connection", True)
    record("Admin login/authentication", login.status_code == 200, f"HTTP {login.status_code}")

    cur.execute(
        "SELECT id, username, account_number, id_number FROM users "
        "WHERE role='customer' ORDER BY id LIMIT 5"
    )
    customers = cur.fetchall()
    record("User read / wallet accounts", len(customers) >= 2, f"{len(customers)} customers")

    tx_id = None
    if len(customers) >= 2:
        customer = next((u for u in customers if u["username"] == "demo"), customers[0])
        recipient = next(
            u["account_number"] for u in customers if u["account_number"] != customer["account_number"]
        )
        customer_password = "demo123" if customer["username"] == "demo" else "password123"
        client.get("/logout", follow_redirects=True)
        clogin = client.post(
            "/login",
            data={
                "username": customer["username"],
                "id_number": customer["id_number"],
                "password": customer_password,
            },
            follow_redirects=True,
        )
        record("Customer login", clogin.status_code == 200, f"user={customer['username']}")

        resp = client.post(
            "/customer/transaction",
            data={
                "type": "transfer",
                "amount": "10.00",
                "recipient": recipient,
            },
            follow_redirects=True,
        )
        conn.commit()
        cur.execute(
            "SELECT id FROM transactions WHERE sender_account=%s ORDER BY id DESC LIMIT 1",
            (customer["account_number"],),
        )
        tx = cur.fetchone()
        record(
            "Transaction creation",
            tx is not None and resp.status_code == 200,
            f"HTTP {resp.status_code}, tx_id={tx['id'] if tx else None}",
        )
        if tx:
            tx_id = tx["id"]
            sender = customer["account_number"]
            cur.execute("SELECT id FROM transactions WHERE id=%s", (tx_id,))
            record("Transaction retrieval", cur.fetchone() is not None, f"id={tx_id}")

            cur.execute(
                "INSERT INTO agents (agent_code, agent_name, location, region, city, status) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                ("REGTEST01", "Regression Agent", "Harare", "Harare", "Harare", "active"),
            )
            conn.commit()
            cur.execute("SELECT id FROM agents WHERE agent_code='REGTEST01'")
            agent_id = cur.fetchone()["id"]
            record("Agent DB create/read", agent_id is not None, f"agent_id={agent_id}")

            client.post(
                "/login", data={"username": "Admin", "password": "Admin123"}, follow_redirects=True
            )
            dash = client.get("/dashboard")
            record("Dashboard database queries", dash.status_code == 200, f"HTTP {dash.status_code}")
            api = client.get("/api/v1/agents")
            record("Agent API (admin)", api.status_code == 200, f"HTTP {api.status_code}")

            cur.execute(
                "INSERT INTO alerts (transaction_id, account_number, risk_score, risk_level, reason, timestamp) "
                "VALUES (%s,%s,%s,%s,%s,UTC_TIMESTAMP())",
                (tx_id, sender, 0.9, "high", "regression alert"),
            )
            conn.commit()
            cur.execute("SELECT id FROM alerts WHERE reason='regression alert'")
            alert = cur.fetchone()
            record("Alerts workflow (DB create/read)", alert is not None, f"alert_id={alert['id'] if alert else None}")

            if alert:
                cur.execute(
                    "INSERT INTO sar_reports (alert_id, account_number, filed_by, narrative, created_at) "
                    "VALUES (%s,%s,%s,%s,UTC_TIMESTAMP())",
                    (alert["id"], sender, "Admin", "regression SAR"),
                )
                conn.commit()
                cur.execute("SELECT id FROM sar_reports WHERE narrative='regression SAR'")
                sar = cur.fetchone()
                record("SAR workflow (DB create/read)", sar is not None, f"sar_id={sar['id'] if sar else None}")

                cur.execute(
                    "INSERT INTO ctr_reports (transaction_id, account_number, amount, generated_by, created_at) "
                    "VALUES (%s,%s,%s,%s,UTC_TIMESTAMP())",
                    (tx_id, sender, 10.0, "Admin"),
                )
                conn.commit()
                cur.execute("SELECT id FROM ctr_reports WHERE generated_by='Admin' AND amount=10")
                ctr = cur.fetchone()
                record("CTR workflow (DB create/read)", ctr is not None, f"ctr_id={ctr['id'] if ctr else None}")

            cur.execute("SELECT username FROM users WHERE username='Admin'")
            admin_u = cur.fetchone()["username"]
            cur.execute("SELECT username FROM users WHERE role='compliance' LIMIT 1")
            comp = cur.fetchone()
            if comp:
                cur.execute(
                    "INSERT INTO conversations (participant_1, participant_2, conversation_type) "
                    "VALUES (%s,%s,'direct')",
                    (admin_u, comp["username"]),
                )
                conn.commit()
                cur.execute(
                    "SELECT id FROM conversations WHERE participant_1=%s AND participant_2=%s",
                    (admin_u, comp["username"]),
                )
                conv = cur.fetchone()
                if conv:
                    cur.execute(
                        "INSERT INTO messages (conversation_id, sender_username, receiver_username, content) "
                        "VALUES (%s,%s,%s,%s)",
                        (conv["id"], admin_u, comp["username"], "regression msg"),
                    )
                    cur.execute(
                        "INSERT INTO unread_messages (user_username, conversation_id, unread_count) "
                        "VALUES (%s,%s,1) ON DUPLICATE KEY UPDATE unread_count=unread_count+1",
                        (comp["username"], conv["id"]),
                    )
                    cur.execute(
                        "INSERT INTO user_presence (username, is_online) VALUES (%s,1) "
                        "ON DUPLICATE KEY UPDATE is_online=1",
                        (admin_u,),
                    )
                    conn.commit()
                    cur.execute("SELECT COUNT(*) AS c FROM messages WHERE content='regression msg'")
                    record("Messaging", cur.fetchone()["c"] == 1)
                    cur.execute(
                        "SELECT unread_count FROM unread_messages WHERE user_username=%s AND conversation_id=%s",
                        (comp["username"], conv["id"]),
                    )
                    record("Unread messages", cur.fetchone() is not None)
                    cur.execute("SELECT is_online FROM user_presence WHERE username=%s", (admin_u,))
                    record("User presence", cur.fetchone() is not None)

    try:
        import server as srv

        record(
            "Socket.IO initialization (no DB failure)",
            srv.socketio is not None and hasattr(srv, "socketio"),
            f"async_mode={srv.socketio.async_mode}",
        )
    except Exception as exc:
        record("Socket.IO initialization", False, str(exc))

    # cleanup regression rows
    cur.execute("DELETE FROM sar_reports WHERE narrative='regression SAR'")
    cur.execute("DELETE FROM ctr_reports WHERE generated_by='Admin' AND amount=10")
    cur.execute("DELETE FROM alerts WHERE reason='regression alert'")
    cur.execute("DELETE FROM messages WHERE content='regression msg'")
    cur.execute("DELETE FROM unread_messages WHERE unread_count > 0")
    if tx_id is not None:
        cur.execute("DELETE FROM transactions WHERE id=%s", (tx_id,))
    cur.execute("DELETE FROM agents WHERE agent_code='REGTEST01'")
    conn.commit()

conn.close()

out_path = os.path.join("reports", "mysql_post_reset_regression_2026-09-14.txt")
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(results) + "\n")
print(f"Wrote {out_path}")
