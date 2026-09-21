import sqlite3
from unittest.mock import Mock

import numpy as np
import pytest

from ai_explanations import explain_features
from ai_stage13_features import Stage13FeatureService
from ai_stage14_model import Stage14ModelService


def test_repeated_near_threshold_activity_has_evidence_and_possible_typology():
    features = [0.0] * 30
    features[0], features[3], features[5] = 4, 0.75, 1.0
    reason = explain_features(features, True)
    assert "4 earlier outgoing transactions" in reason
    assert "100%" in reason
    assert "synthetic $10,000 threshold" in reason
    assert "may indicate structuring" in reason
    assert "not model feature attributions or proof" in reason


def test_single_near_threshold_observation_does_not_claim_repetition():
    features = [0.0] * 30
    features[0], features[5] = 1, 1
    assert "Possible activity: undetermined" in explain_features(features, True)


def test_normal_prediction_does_not_accuse_customer():
    reason = explain_features([10.0] * 30, False)
    assert "did not flag" in reason
    assert "does not establish" in reason
    assert "may indicate" not in reason


def test_network_and_agent_observations_are_specific():
    features = [0.0] * 30
    features[0], features[6], features[14] = 3, 6, 0.95
    features[17], features[26], features[27] = 25, 4.0, 3.2
    reason = explain_features(features, True)
    for expected in ("6 distinct counterparties", "95%", "pass-through", "fan-out", "4.0", "3.2", "agent"):
        assert expected in reason


@pytest.mark.parametrize("features", [[0.0] * 29, [float('nan')] * 30, [float('inf')] * 30])
def test_invalid_evidence_is_rejected(features):
    with pytest.raises(ValueError):
        explain_features(features, True)


def test_prediction_explains_the_exact_feature_vector_without_changing_score():
    service = Stage14ModelService.__new__(Stage14ModelService)
    service.model_loaded = True
    service.model = Mock()
    service.model.predict_proba.return_value = np.array([[0.2, 0.8]])
    features = [0.0] * 30
    features[0] = 5.0
    service.feature_service = Mock()
    service.feature_service.generate_features.return_value = features
    tx = {"id": 10}
    result = service.predict(tx)
    assert result.probability == 0.8
    assert result.threshold == 0.35
    assert result.is_suspicious
    assert "5 earlier outgoing transactions" in result.explanation
    service.feature_service.generate_features.assert_called_once_with(tx)
    np.testing.assert_array_equal(service.model.predict_proba.call_args.args[0], [features])


def test_historical_explanation_excludes_current_and_future_transactions():
    with sqlite3.connect(":memory:") as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("CREATE TABLE transactions (id INTEGER, sender_account TEXT, receiver_account TEXT, amount REAL, timestamp TEXT, transaction_type TEXT, agent_id INTEGER)")
        for number in range(1, 8):
            conn.execute(
                "INSERT INTO transactions VALUES (?, 'A', 'B', 9500, ?, 'transfer', NULL)",
                (number, f"2026-09-21T12:0{number}:00+00:00"),
            )
        tx = dict(conn.execute("SELECT * FROM transactions WHERE id=5").fetchone())
        features = Stage13FeatureService(conn).generate_features(tx)
        assert features[0] == 4
        reason = explain_features(features, True)
        assert "4 earlier outgoing transactions" in reason
        assert "may indicate structuring" in reason
