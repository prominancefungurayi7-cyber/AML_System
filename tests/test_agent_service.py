import uuid
import pytest
from test_v4_simulation import ledger, processor, balances
from agent_service import commit_service


def test_cash_services_conserve_value_and_duplicate_does_not_repeat(ledger):
    _, conn = ledger
    conn.execute("INSERT INTO agents(id,status,agent_code) VALUES (1,'active','AGENT0001')")
    conn.execute("INSERT INTO users(id,username,account_number,role,balance) VALUES (200,'Agent','AGENT0001','agent',0)")
    conn.commit()
    get_id = lambda c: c.execute('SELECT last_insert_rowid() id').fetchone()['id']
    before = balances(conn)
    key = str(uuid.uuid4())
    args = (conn,200,'ACC1003','cash_out','10.00',key,processor(),get_id)
    tx, replay = commit_service(*args)
    assert not replay
    assert commit_service(*args) == (tx, True)
    assert sum(balances(conn).values()) == sum(before.values())
    assert balances(conn)[200] == 1000
    commit_service(conn,200,'ACC1003','cash_in','4.00',str(uuid.uuid4()),processor(),get_id)
    assert balances(conn)[200] == 600
    assert sum(balances(conn).values()) == sum(before.values())
    with pytest.raises(ValueError, match='Insufficient agent'):
        commit_service(conn,200,'ACC1003','cash_in','7.00',str(uuid.uuid4()),processor(),get_id)
    conn.rollback()
    assert conn.execute('SELECT COUNT(*) n FROM transactions').fetchone()['n'] == 2
    assert conn.execute('SELECT COUNT(*) n FROM canonical_mobile_money_events').fetchone()['n'] == 2


def test_agent_routes_reject_other_roles_and_require_csrf(aml_app, monkeypatch):
    from test_application_workflows import client_for
    m = aml_app
    assert client_for(m,'demo').get('/agent').status_code == 302
    assert client_for(m,'Admin').post('/agent/service').status_code == 302
    db = m.connect_db()
    db.execute("UPDATE users SET role='agent',account_number='AGENT0001' WHERE username='demo'")
    db.execute("INSERT INTO agents(agent_code,agent_name,status) VALUES ('AGENT0001','Agent','active')")
    db.commit(); db.close()
    client = client_for(m,'demo')
    assert client.get('/dashboard').headers['Location'].endswith('/agent')
    response = client.get('/agent')
    assert response.status_code == 200
    assert b'Agent Service Dashboard' in response.data
    assert client.post('/agent/service',data={}).status_code == 403
