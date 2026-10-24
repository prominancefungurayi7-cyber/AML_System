"""Transaction explanation authorization with temporary accounts and records."""
from test_application_workflows import client_for


def test_evidence_visible_to_participants_and_staff_only(aml_app, monkeypatch):
    m = aml_app
    db = m.connect_db()
    db.execute("INSERT INTO transactions(sender_account,receiver_account,amount,transaction_type,"
               "ai_risk_level,ai_reason) VALUES ('ACC1003','ACC1000',5,'transfer','normal','V4 normal pattern')")
    tx = m.get_last_insert_id(db)
    db.commit()
    db.close()
    calls = []
    def evidence(identifier, decision):
        calls.append((identifier, decision))
        return m.jsonify(transaction_id=identifier, prediction=0, findings=[])
    monkeypatch.setattr(m, '_v4_evidence_response', evidence)
    path = f'/api/transactions/{tx}/ai-evidence'
    assert m.app.test_client().get(path).status_code == 302
    for name in ('demo', 'user_low_1', 'Compliance', 'Admin'):
        assert client_for(m, name).get(path).status_code == 200
    assert len(calls) == 4
    assert client_for(m, 'user_low_5').get(path).status_code == 404
    assert len(calls) == 4
    db = m.connect_db()
    for state in ('pending_v4', 'inference_error'):
        db.execute('UPDATE transactions SET ai_risk_level=? WHERE id=?', (state, tx))
        db.commit()
        assert client_for(m, 'demo').get(path).status_code == 409
    db.close()
    assert len(calls) == 4
