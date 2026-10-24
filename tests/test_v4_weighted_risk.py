"""V4 dominates composite scoring without overriding model or rule evidence."""
import json
from uuid import uuid4

import pytest

import v4_primary
import v4_retry
import v4_shadow
from tests.test_stage5a_v4_primary import connect, setup, success
from tests.test_v4_retry import prepared


@pytest.mark.parametrize(
    'probability,rule_score,expected_score,expected_level',
    [(.10, 0, 7.0, 'normal'),
     (.10, 40, 19.0, 'suspicious'),
     (.10, 90, 34.0, 'critical'),
     (.50, 0, 35.0, 'suspicious'),
     (.90, 0, 63.0, 'high_risk'),
     (.49, 100, 64.3, 'critical'),
     (.87654, 13, 65.26, 'high_risk')],
)
def test_success_uses_seventy_percent_probability_and_thirty_percent_rules(
        probability, rule_score, expected_score, expected_level):
    result = success(1, probability)
    decision = v4_primary._decision(result, rule_score, 0)
    assert decision['risk_score'] == expected_score
    assert decision['risk_level'] == expected_level
    assert decision['ai_risk_level'] == result['decision']
    assert decision['sar_required'] == int(probability >= .5 or rule_score >= 40)
    assert decision['ai_confidence'] == pytest.approx(
        probability if probability >= .5 else 1 - probability)
    # Class confidence and suspicious probability have opposite meanings for
    # a normal prediction; a confident normal outcome must lower AI risk.
    assert result['prediction'] == int(probability >= .5)
    assert result['suspicious_probability'] == probability
    assert ('V4 suspicious pattern' if probability >= .5 else 'V4 normal pattern') in decision['ai_reason']


def test_scoring_policy_declares_ai_majority_weight_and_keeps_sources_separate():
    assert v4_primary.SCORING_POLICY == {'ai_weight': .7, 'rule_weight': .3}
    decision = v4_primary._decision(success(1, .1), 90, 0)
    assert '70%' in decision['description'] and '30%' in decision['description']
    assert decision['ai_reason'].startswith('V4 normal pattern')
    assert '70%' not in decision['ai_reason']
    assert '30%' not in decision['ai_reason']


def test_failure_does_not_scale_down_independent_rules_or_fabricate_ai_probability():
    result = v4_shadow.error(1, 'HISTORY_INCOMPLETE')
    decision = v4_primary._decision(result, 90, 0)
    assert decision['risk_score'] == 90
    assert decision['risk_level'] == 'critical'
    assert decision['ai_risk_level'] == 'inference_error'
    assert decision['ai_confidence'] == 0
    assert decision['sar_required'] == 1
    assert 'HISTORY_INCOMPLETE' in decision['ai_reason']
    assert result['prediction'] is None
    assert result['suspicious_probability'] is None


def test_existing_sar_obligation_survives_low_combined_risk():
    decision = v4_primary._decision(success(1, .1), 0, 1)
    assert decision['risk_score'] == 7
    assert decision['sar_required'] == 1


def test_primary_and_audited_retry_use_same_score_without_changing_financial_rows(tmp_path):
    primary_path = tmp_path / 'primary.db'
    setup(primary_path, rule_score=60)
    primary_factory = lambda: connect(primary_path)
    v4_primary.complete_committed(primary_factory, 1, worker=lambda tx: success(tx, .2))

    _retry_path, retry_factory = prepared(tmp_path)
    db = retry_factory()
    original_error = db.execute('SELECT body FROM v4_shadow_results').fetchone()[0]
    db.execute('UPDATE transactions SET rule_score=60 WHERE id=1')
    db.commit()
    db.close()
    v4_retry.retry(retry_factory, 1, 3, str(uuid4()),
                   runner=lambda tx, *_: success(tx, .2))
    comparable = ('risk_score', 'risk_level', 'ai_risk_level', 'ai_confidence', 'ai_reason')
    decisions = []
    for factory in (primary_factory, retry_factory):
        db = factory()
        row = db.execute('SELECT * FROM transactions WHERE id=1').fetchone()
        decisions.append(tuple(row[key] for key in comparable))
        assert [r['balance'] for r in db.execute('SELECT balance FROM users WHERE id IN (1,2) ORDER BY id')] == [489.5, 510.5]
        assert db.execute('SELECT COUNT(*) FROM transactions').fetchone()[0] == 1
        assert db.execute('SELECT COUNT(*) FROM canonical_mobile_money_events').fetchone()[0] == 1
        alert = db.execute('SELECT * FROM alerts WHERE transaction_id=1').fetchone()
        assert alert['risk_score'] == row['risk_score'] == 32
        assert alert['risk_level'] == row['risk_level'] == 'high_risk'
        db.close()
    assert decisions[0] == decisions[1]
    db = retry_factory()
    assert db.execute('SELECT body FROM v4_shadow_results').fetchone()[0] == original_error
    audit = json.loads(db.execute("SELECT result_body FROM v4_primary_attempt_events WHERE event_kind='COMPLETED'").fetchone()[0])
    assert audit['prediction'] == 0 and audit['suspicious_probability'] == .2
    db.close()


def test_reweighting_precommit_rule_alert_preserves_case_work_and_identity(tmp_path):
    path = tmp_path / 'existing-alert.db'
    setup(path, rule_score=90)
    factory = lambda: connect(path)
    db = factory()
    db.execute('ALTER TABLE alerts ADD COLUMN assigned_to INTEGER')
    db.execute('ALTER TABLE alerts ADD COLUMN notes TEXT')
    db.execute("INSERT INTO alerts (id,transaction_id,account_number,risk_score,risk_level,reason,rules_triggered,status,timestamp,assigned_to,notes) VALUES (17,1,'A',90,'critical','Independent rule evidence','[\"Velocity\"]','investigating','original',3,'Analyst retained evidence')")
    db.execute("UPDATE transactions SET rules_triggered='[\"Velocity\"]' WHERE id=1")
    db.commit()
    db.close()
    result = v4_primary.complete_committed(factory, 1, worker=lambda tx: success(tx, .1))
    db = factory()
    alert = db.execute('SELECT * FROM alerts WHERE transaction_id=1').fetchone()
    assert result['alert_id'] == alert['id'] == 17
    assert alert['risk_score'] == 34
    assert alert['risk_level'] == 'critical'
    assert alert['status'] == 'investigating'
    assert alert['assigned_to'] == 3
    assert alert['notes'] == 'Analyst retained evidence'
    assert alert['timestamp'] == 'original'
    assert json.loads(alert['rules_triggered']) == ['Velocity']
    assert db.execute('SELECT COUNT(*) FROM alerts').fetchone()[0] == 1
    assert [r['balance'] for r in db.execute('SELECT balance FROM users ORDER BY id')] == [489.5, 510.5]
    db.close()
