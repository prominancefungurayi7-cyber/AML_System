"""Read-only Flask/MySQL probe of the Stage 13/14 connection repair."""
import hashlib
import json
import os
from pathlib import Path
import sys

from ai_stage13_features import Stage13FeatureService
from ai_stage14_model import STAGE14_THRESHOLD, get_stage14_model_service
from canonical_history import freshness
from canonical_history_store import assess
from ml_v4.stage4sa.coordinator import validate_test
from ml_v4.stage4sa.harness import load_test_application
from ml_v4.test_binding import v1

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'ml_v4/evidence/stage4sd/legacy_live.json'
MODEL = ROOT / 'ml_v4/development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib'
EXPECTED_HASH = '555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18'
TABLES = ('transactions', 'canonical_mobile_money_events', 'cmm_source_changes',
          'v4_shadow_results', 'alerts')


def counts(db):
    return {name: db.execute('SELECT COUNT(*) AS n FROM ' + name).fetchone()['n'] for name in TABLES}


def baseline():
    authority = v1.load_authority()
    if (authority['server_uuid'] != 'd441b7bb-43f6-11f1-a2d8-0a0027000005'
            or os.environ.get('V4_STAGE4T_EXPECTED_SERVER_UUID') != authority['server_uuid']):
        raise RuntimeError('Test server identity not pinned')
    if hashlib.sha256(MODEL.read_bytes()).hexdigest() != EXPECTED_HASH:
        raise RuntimeError('Frozen V4 model hash mismatch')
    db = v1.connection(authority)
    try:
        v1._triggers(db)
        v1._boundary(db, authority)
        scope, current, previous = assess(db, v1.SCOPE)
        state = freshness(scope, current, previous)
        if state != 'COMPLETE_VERIFIED' or current['issues']:
            raise RuntimeError('Existing history authority is not fresh')
        observed = counts(db)
        if observed != dict(zip(TABLES, (4, 4, 8, 4, 0))):
            raise RuntimeError('Existing disposable ledger differs from approved four-case state')
        stored = []
        for tx in (1, 2, 3, 4):
            row = db.execute('SELECT status,body FROM v4_shadow_results WHERE transaction_id=?', (tx,)).fetchone()
            if row is None or row['status'] != 'success':
                raise RuntimeError('Stored V4 result missing or technical error')
            body = validate_test(json.loads(row['body']), tx)
            if body['status'] != 'success' or body['threshold'] != .5:
                raise RuntimeError('Stored V4 result invalid')
            stored.append({'transaction_id': tx, 'prediction': body['prediction'],
                           'suspicious_probability': body['suspicious_probability']})
        return {'counts': observed, 'history_status': state,
                'server_uuid': authority['server_uuid'], 'principal': authority['principal'],
                'v4_model_sha256': EXPECTED_HASH, 'v4_results': stored}
    finally:
        db.rollback()
        db.close()


def run():
    evidence = {'status': 'INCOMPLETE', 'database': v1.DATABASE,
                'requests': [], 'database_errors': []}
    try:
        evidence['before'] = baseline()
        if STAGE14_THRESHOLD != .35:
            raise RuntimeError('Legacy threshold changed')
        app = load_test_application()
        module = sys.modules['stage4sa_server']
        connections = []

        class ObservedAdapter:
            def __init__(self, connection):
                self.connection = connection
                self.queries = 0
                self.errors = []

            def execute(self, query, params=()):
                self.queries += 1
                try:
                    return self.connection.execute(query, params)
                except Exception as exc:
                    self.errors.append(type(exc).__name__)
                    raise

        class ObservedFeatures(Stage13FeatureService):
            def generate_features(self, tx):
                self.vector = super().generate_features(tx)
                return self.vector

        @app.get('/stage4sd/read-only-legacy-probe/<int:tx_id>')
        def probe(tx_id):
            if tx_id not in (2, 3, 4):
                raise RuntimeError('Only existing approved transaction IDs may be replayed')
            db = module.get_db()
            connections.append(db)
            db.rollback()
            db.execute('START TRANSACTION READ ONLY')
            connection_id = db.execute('SELECT CONNECTION_ID() AS id').fetchone()['id']
            row = db.execute('SELECT id,sender_account,receiver_account,amount,transaction_type,'
                             'timestamp,agent_id FROM transactions WHERE id=?', (tx_id,)).fetchone()
            if row is None:
                raise RuntimeError('Existing transaction unavailable')
            tx = dict(row)
            adapter = ObservedAdapter(db)
            features = ObservedFeatures(adapter)
            service = get_stage14_model_service(features)
            if service.feature_service is not features or not db.connection.is_connected():
                raise RuntimeError('Stage 14 is not bound to the current live connection')
            try:
                prediction = service.predict(tx)
            finally:
                if adapter.errors:
                    evidence['database_errors'].append({'transaction_id': tx_id,
                                                        'error_types': adapter.errors})
            vector = features.vector
            if (adapter.errors or adapter.queries == 0 or len(vector) != 30
                    or vector[0] < 1 or all(value == 0 for value in vector)
                    or prediction.threshold != .35 or not db.connection.is_connected()):
                raise RuntimeError('Legacy feature/prediction lifecycle check failed')
            return {'transaction_id': tx_id, 'mysql_connection_id': connection_id,
                    'feature_queries': adapter.queries, 'feature_errors': adapter.errors,
                    'stage13_features': vector, 'stage14_probability': prediction.probability,
                    'stage14_prediction': prediction.prediction,
                    'stage14_threshold': prediction.threshold}

        client = app.test_client()
        for tx_id in (2, 3, 4):
            response = client.get(f'/stage4sd/read-only-legacy-probe/{tx_id}')
            if response.status_code != 200:
                raise RuntimeError('Flask read-only probe failed')
            data = response.get_json()
            if connections[-1].connection.is_connected():
                raise RuntimeError('Flask request connection remained open after teardown')
            data['http_status'] = response.status_code
            data['closed_after_request'] = True
            evidence['requests'].append(data)
        ids = [entry['mysql_connection_id'] for entry in evidence['requests']]
        if len(set(ids)) != 3:
            raise RuntimeError('Consecutive requests reused a MySQL connection')
        try:
            get_stage14_model_service()
        except RuntimeError:
            evidence['missing_feature_service_rejected'] = True
        else:
            raise RuntimeError('Missing current feature service accepted')
        evidence['after'] = baseline()
        if evidence['after']['counts'] != evidence['before']['counts']:
            raise RuntimeError('Read-only probe changed database counts')
        evidence['status'] = 'PASS'
    except Exception as exc:
        evidence['failure_type'] = type(exc).__name__
        raise
    finally:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')


if __name__ == '__main__':
    try:
        run()
    except Exception as exc:
        print('Stage4S-D legacy probe stopped: ' + type(exc).__name__)
        raise SystemExit(1)
