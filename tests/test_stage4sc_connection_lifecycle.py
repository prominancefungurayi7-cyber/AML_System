"""Offline Flask request lifecycle regression for legacy Stage 13/14."""
import sqlite3

from flask import Flask, jsonify
import numpy as np

import ai_stage14_model as stage14
from ai_stage13_features import Stage13FeatureService


def test_consecutive_flask_requests_use_current_feature_connection(monkeypatch):
    vectors = []

    class FrozenModelSpy:
        def predict_proba(self, values):
            vectors.append(values.copy())
            return np.array([[0.8, 0.2]])

    model = FrozenModelSpy()

    def load_model(self):
        self.model = model
        self.model_loaded = True
        self.model_metadata = None

    monkeypatch.setattr(stage14.Stage14ModelService, '_load_model', load_model)
    monkeypatch.setattr(stage14, '_model_service_instance', None)
    app = Flask(__name__)
    connections = []

    @app.get('/transaction')
    def transaction():
        db = sqlite3.connect(':memory:')
        db.row_factory = sqlite3.Row
        connections.append(db)
        try:
            db.execute('CREATE TABLE transactions (id INTEGER, sender_account TEXT, '
                       'receiver_account TEXT, amount REAL, timestamp TEXT, '
                       'transaction_type TEXT, agent_id INTEGER)')
            db.execute('INSERT INTO transactions VALUES (1,?,?,?,?,?,?)',
                       ('W1', 'W2', 10.0, '2026-10-09T11:00:00+00:00', 'transfer', None))
            features = Stage13FeatureService(db)
            service = stage14.get_stage14_model_service(features)
            prediction = service.predict({'id': 2, 'sender_account': 'W1',
                                          'receiver_account': 'W3', 'amount': 1.0,
                                          'timestamp': '2026-10-09T12:00:00+00:00',
                                          'transaction_type': 'transfer'})
            return jsonify({'probability': prediction.probability,
                            'prior_count': float(vectors[-1][0, 0])})
        finally:
            db.close()

    client = app.test_client()
    for _ in range(3):
        response = client.get('/transaction')
        assert response.status_code == 200
        assert response.json == {'probability': 0.2, 'prior_count': 1.0}
    assert len(connections) == len(vectors) == 3
    assert all(vector.shape == (1, 30) and vector[0, 0] == 1 for vector in vectors)
    assert stage14._model_service_instance.feature_service is None


def test_stage14_requires_explicit_current_feature_service(monkeypatch):
    monkeypatch.setattr(stage14, '_model_service_instance', None)
    try:
        stage14.get_stage14_model_service()
    except RuntimeError as exc:
        assert str(exc) == 'Current feature service required'
    else:
        raise AssertionError('Unbound Stage 14 service was accepted')
