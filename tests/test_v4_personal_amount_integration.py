"""Real V4 handoff with synthetic records in a disposable SQLite ledger."""
from datetime import datetime, timedelta, timezone
import json

import pytest

from ai_explanations import reasoning_fields
from canonical_mobile_money import VERSION, prepare_ingestion, with_id
from canonical_mobile_money_store import persist
import v4_primary
import v4_shadow
from test_stage5a_v4_primary import success
from test_v4_simulation import ledger, processor, balances, connect


@pytest.mark.parametrize('failed', [False, True])
def test_personal_rule_alert_survives_normal_or_failed_v4_without_replaying_payment(ledger, failed):
    path, conn = ledger
    now = datetime(2026, 10, 17, 12, tzinfo=timezone.utc)
    form = dict(canonical_version=VERSION, type='wallet_to_wallet', amount='100.00', currency='USD',
                channel='direct_wallet', agent_id='', serviced_wallet='', agent_flow_direction='none', recipient='ACC1000')
    for index in range(6):
        timestamp = (now - timedelta(days=6-index) if index < 5 else now).isoformat()
        amount = 100 if index < 5 else 1001
        conn.execute('INSERT INTO transactions(sender_account,receiver_account,amount,transaction_type,timestamp,status) '
                     'VALUES (?,?,?,?,?,?)', ('ACC1003', 'ACC1000', amount, 'transfer', timestamp, 'Completed'))
        identifier = conn.execute('SELECT last_insert_rowid() id').fetchone()['id']
        event = prepare_ingestion({**form, 'amount': f'{amount:.2f}'}, 'ACC1003', timestamp)
        persist(conn, with_id(event, identifier))
    before = balances(conn)
    initial_count = conn.execute('SELECT COUNT(*) n FROM transactions').fetchone()['n']
    prepared = processor()(conn, identifier, 'ACC1003', 'ACC1000', 1001, 'transfer',
                           now.isoformat(), emit_events=False)
    assert prepared[0] == 40 and prepared[1] == 'suspicious'
    conn.commit()
    pending = dict(conn.execute('SELECT * FROM transactions WHERE id=?', (identifier,)).fetchone())
    assert pending['ai_risk_level'] == 'pending_v4'
    assert json.loads(pending['rules_triggered'])[0]['rule_id'] == 'R12'
    assert 'Personal amount deviation' in pending['rule_reason']
    def worker(tx):
        return v4_shadow.error(tx, 'INFERENCE_ERROR') if failed else success(tx, .20)
    v4_primary.complete_committed(lambda: connect(path), identifier, worker=worker)
    final = dict(conn.execute('SELECT * FROM transactions WHERE id=?', (identifier,)).fetchone())
    assert final['ai_risk_level'] == ('inference_error' if failed else 'normal')
    assert final['risk_level'] == 'suspicious'
    assert final['risk_score'] == (40 if failed else 26)
    assert conn.execute('SELECT risk_score FROM alerts WHERE transaction_id=?',
                        (identifier,)).fetchone()['risk_score'] == final['risk_score']
    assert conn.execute('SELECT COUNT(*) n FROM alerts WHERE transaction_id=?', (identifier,)).fetchone()['n'] == 1
    fields = reasoning_fields(final)
    assert 'Personal amount deviation' in fields['rule_reason']
    assert 'Personal amount deviation' not in fields['ai_reason']
    assert balances(conn) == before
    assert conn.execute('SELECT COUNT(*) n FROM transactions').fetchone()['n'] == initial_count
    with pytest.raises(v4_primary.DecisionAlreadyApplied):
        v4_primary.complete_committed(lambda: connect(path), identifier, worker=worker)
    assert conn.execute('SELECT COUNT(*) n FROM alerts WHERE transaction_id=?', (identifier,)).fetchone()['n'] == 1
    assert balances(conn) == before
