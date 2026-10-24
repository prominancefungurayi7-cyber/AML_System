"""Supervisor feedback regression checks; temporary databases and private files only."""
import uuid
import pytest
from test_application_workflows import client_for
from test_v4_simulation import ledger, balances, generate
import v4_simulation as simulation


@pytest.mark.parametrize('username', ['0', 'P', '12', '12345', 'a12', 'a' * 61, '<name>'])
def test_registration_rejects_unreasonable_names_before_email(aml_app, monkeypatch, username):
    monkeypatch.setattr(aml_app, 'send_otp_email_async', lambda *_: pytest.fail('OTP should not be sent'))
    response = aml_app.app.test_client().post('/register', data=dict(username=username,
        email='fixture@example.invalid', id_number='08-995728P34', password='Fixture-password1!'))
    assert response.status_code == 200
    assert b'at least two letters' in response.data
    db = aml_app.connect_db()
    assert db.execute('SELECT id FROM users WHERE username=?', (username,)).fetchone() is None
    db.close()


def test_verified_registration_starts_at_zero(aml_app, monkeypatch):
    codes = []
    monkeypatch.setattr(aml_app, 'send_otp_email_async', lambda _, code: codes.append(code) or True)
    client = aml_app.app.test_client()
    client.post('/register', data=dict(username='New Customer', email='fixture@example.invalid',
                id_number='08-995728P34', password='Fixture-password1!'))
    assert len(codes) == 1
    assert client.post('/register', data={'otp': codes[0]}).status_code == 302
    db = aml_app.connect_db()
    row = db.execute("SELECT balance FROM users WHERE username='New Customer'").fetchone()
    assert row and row['balance'] == 0
    db.close()


def test_new_mixed_plan_conserves_customer_and_agent_value_with_zero_float(ledger, monkeypatch):
    _, conn = ledger
    conn.execute("INSERT INTO agents VALUES (1,'active','AGENT0001')")
    conn.execute("INSERT INTO users(id,username,account_number,role,balance) VALUES (200,'Agent','AGENT0001','agent',0)")
    conn.commit()
    choice = next(c for c in simulation.options(conn, 'test', 1)['choices']
                  if c['mode'] == 'mixed' and c['count'] == 30)
    ticket = simulation.decode(choice['token'], 'test', 1)
    assert simulation.input_mix(ticket)['scenario_counts'] == dict(ordinary=21, structuring=3, network=3, agent=3)
    before = balances(conn)
    planner = simulation.plan
    calls = []
    def counted(ticket):
        calls.append(ticket['version'])
        return planner(ticket)
    monkeypatch.setattr(simulation, 'plan', counted)
    result = generate(conn, ticket)
    assert calls.count(5) == 1  # Reuse the signed plan for both receipt reads.
    after = balances(conn)
    assert result['saved'] == result['pending_v4'] == 30
    assert sum(before.values()) == sum(after.values())
    cash = conn.execute("SELECT transaction_type,amount FROM transactions WHERE channel='agent' ORDER BY id").fetchall()
    assert [r['transaction_type'] for r in cash] == ['withdraw','deposit','withdraw']
    assert after[200] == round(cash[-1]['amount'] * 100)
    assert generate(conn, ticket)['replayed']
    assert balances(conn) == after


def seed_case(m):
    db = m.connect_db()
    db.execute("INSERT INTO transactions (sender_account,receiver_account,amount,transaction_type) VALUES ('ACC1003','ACC1000',1,'transfer')")
    db.execute("INSERT INTO alerts (transaction_id,account_number,risk_score,risk_level,reason) VALUES (1,'ACC1003',80,'suspicious','Fixture only')")
    db.commit()
    return db


def test_sar_complete_view_pdf_private_message_and_retry(aml_app):
    from message_attachments import decode_message
    m = aml_app
    compliance, admin, customer = [client_for(m, n) for n in ('Compliance','Admin','demo')]
    db = seed_case(m)
    narrative = 'Evidence paragraph. ' * 30 + 'LAST LINE <script>alert(1)</script>'
    action = dict(action='file_sar', sar_narrative=narrative)
    assert compliance.post('/compliance/alert/1', data=action).status_code == 302
    sar = db.execute('SELECT * FROM sar_reports').fetchone()
    assert sar and sar['narrative'] == narrative
    messages = db.execute('SELECT * FROM messages').fetchall()
    assert len(messages) == 1 and messages[0]['receiver_username'] == 'Admin'
    caption, metadata = decode_message(messages[0]['content'])
    assert metadata['media_type'] == 'application/pdf'
    path = f"/reports/sar/{sar['id']}"
    for staff in (admin, compliance):
        response = staff.get(path)
        assert response.status_code == 200 and b'LAST LINE &lt;script&gt;' in response.data
        pdf = staff.get(path + '/document')
        assert pdf.status_code == 200 and pdf.data.startswith(b'%PDF-')
    assert customer.get(path).status_code == 302
    assert customer.get(path + '/document').status_code == 302
    download = f"/api/messages/{messages[0]['id']}/attachment"
    assert admin.get(download).data.startswith(b'%PDF-')
    assert customer.get(download).status_code in (403, 404)
    assert compliance.post('/compliance/alert/1', data=action).status_code == 302
    assert db.execute('SELECT COUNT(*) n FROM sar_reports').fetchone()['n'] == 1
    assert db.execute('SELECT COUNT(*) n FROM messages').fetchone()['n'] == 1
    compliance.get(path)
    with compliance.session_transaction() as session:
        csrf = session['report_delivery_csrf']
    assert compliance.post(f"/reports/sar/{sar['id']}/send", data={'csrf_token': csrf}).status_code == 302
    assert db.execute('SELECT COUNT(*) n FROM messages').fetchone()['n'] == 1
    assert compliance.post(f"/compliance/sar/{sar['id']}/submit").status_code == 302
    assert db.execute('SELECT COUNT(*) n FROM messages').fetchone()['n'] == 2
    assert compliance.post(f"/compliance/sar/{sar['id']}/submit").status_code == 302
    assert db.execute('SELECT COUNT(*) n FROM messages').fetchone()['n'] == 2
    db.close()


def test_escalation_document_and_delivery_failure_keep_case(aml_app, monkeypatch):
    import sar_documents
    m = aml_app
    client = client_for(m, 'Compliance')
    db = seed_case(m)
    original = sar_documents.deliver_to_admins
    monkeypatch.setattr(sar_documents, 'deliver_to_admins', lambda *_: (_ for _ in ()).throw(OSError('fixture storage offline')))
    assert client.post('/compliance/alert/1', data=dict(action='escalate', case_notes='Investigate source of funds.')).status_code == 302
    assert db.execute('SELECT status FROM alerts WHERE id=1').fetchone()['status'] == 'escalated'
    assert db.execute('SELECT COUNT(*) n FROM messages').fetchone()['n'] == 0
    monkeypatch.setattr(sar_documents, 'deliver_to_admins', original)
    assert client.get('/compliance/alert/1').status_code == 200
    with client.session_transaction() as session: csrf = session['report_delivery_csrf']
    assert client.post('/reports/escalation/1/send', data={'csrf_token': csrf}).status_code == 302
    assert db.execute('SELECT COUNT(*) n FROM messages').fetchone()['n'] == 1
    db.close()


def test_sar_pagination_keeps_older_reports_accessible(aml_app):
    db = seed_case(aml_app)
    for i in range(22):
        db.execute("INSERT INTO sar_reports(alert_id,account_number,filed_by,narrative,created_at,reference_number) VALUES (1,'ACC1003','Compliance',?,'2026-10-23',?)",
                   (f'Historical report {i}', f'REF-{i}'))
    db.commit()
    response = client_for(aml_app, 'Admin').get('/reports?sar_page=2')
    assert response.status_code == 200 and b'REF-0' in response.data
    assert b'Page 2 of 2' in response.data
    db.close()


@pytest.mark.parametrize('actor', ['customer', 'agent'])
def test_cash_routes_balance_both_wallets_and_preserve_idempotency(aml_app, monkeypatch, actor):
    from canonical_mobile_money_store import migrate
    import v4_primary
    m = aml_app
    monkeypatch.setenv('AML_RULE_ENGINE_ENABLED', 'ON')
    monkeypatch.setattr(m, '_RULE_ENGINE_ENABLED', True)
    monkeypatch.setattr(m, '_RULE_ENGINE_POLICY', 'ON')
    monkeypatch.setattr(v4_primary, 'enqueue_committed', lambda _: None)
    db = m.connect_db()
    migrate(db)
    db.execute("UPDATE users SET role='agent',account_number='AGENT0001',balance=0 WHERE username='user_low_1'")
    db.execute("INSERT INTO agents(agent_code,agent_name,status) VALUES ('AGENT0001','Fixture Agent','active')")
    agent_id = db.execute("SELECT id FROM agents WHERE agent_code='AGENT0001'").fetchone()['id']
    db.commit()
    def values():
        return {r['account_number']: round(r['balance'] * 100) for r in db.execute(
            "SELECT account_number,balance FROM users WHERE account_number IN ('ACC1003','AGENT0001')").fetchall()}
    client = client_for(m, 'demo' if actor == 'customer' else 'user_low_1')
    before = values()
    if actor == 'agent':
        assert client.get('/agent').status_code == 200
        with client.session_transaction() as session: csrf = session['agent_service_csrf']
        url = '/agent/service'
        base = dict(customer='ACC1003', csrf_token=csrf, cash_confirmed='yes')
    else:
        assert client.get('/customer').status_code == 200
        url = '/customer/transaction'
        base = dict(canonical_version='mobile_money.canonical.v1', currency='USD',
                    channel='agent', agent_id=str(agent_id), serviced_wallet='ACC1003',
                    agent_flow_direction='cash_out', recipient='', cash_confirmed='yes')
    form = dict(base, type='cash_out', amount='10.00', client_request_id=str(uuid.uuid4()))
    response = client.post(url, data=form)
    assert response.status_code == 302
    after = values()
    assert after['ACC1003'] == before['ACC1003'] - 1000
    assert after['AGENT0001'] == 1000 and sum(after.values()) == sum(before.values())
    assert client.post(url, data=form).status_code == 302
    assert values() == after
    form.update(type='cash_in', amount='4.00', client_request_id=str(uuid.uuid4()))
    response = client.post(url, data=form)
    assert response.status_code == 302
    assert values()['AGENT0001'] == 600
    assert sum(values().values()) == sum(before.values())
    after = values()
    form.update(amount='7.00', client_request_id=str(uuid.uuid4()))
    response = client.post(url, data=form)
    assert response.status_code == (302 if actor == 'customer' else 400)
    assert values() == after
    assert db.execute("SELECT COUNT(*) n FROM canonical_mobile_money_events").fetchone()['n'] == 2
    assert db.execute("SELECT COUNT(*) n FROM transactions").fetchone()['n'] == 2
    db.close()


def test_admin_authored_report_does_not_create_inaccessible_self_chat(aml_app):
    db = seed_case(aml_app)
    admin = client_for(aml_app, 'Admin')
    assert admin.post('/compliance/alert/1', data=dict(action='file_sar', sar_narrative='Administrator case.')).status_code == 302
    assert db.execute('SELECT COUNT(*) n FROM sar_reports').fetchone()['n'] == 1
    assert db.execute('SELECT COUNT(*) n FROM messages').fetchone()['n'] == 0
    assert admin.get('/reports/sar/1/document').data.startswith(b'%PDF-')
    db.close()
