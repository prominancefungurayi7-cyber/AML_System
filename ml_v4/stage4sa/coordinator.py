"""Test-only shadow coordinator bound to the Stage4T worker and scope."""
import hashlib
import json
from pathlib import Path
import subprocess

import v4_shadow as production
from ml_v4.test_binding import v1

ROOT = Path(__file__).resolve().parents[2]
WORKER = ROOT / 'ml_v4/test_binding/worker.py'
WORKER_SHA256 = 'f32a8850b8cb64678933568fe7377a7f7da34074ca537311336b272409b857ac'
PYTHON = ROOT / 'ml_v4/.venv_inference_stage3/Scripts/python.exe'
MAX_OUTPUT = production.MAX_OUTPUT
TIMEOUT = production.TIMEOUT


def validate_test(value, transaction_id):
    """Use every production field check, substituting only its scope check."""
    if type(value) is not dict:
        raise ValueError('Invalid result')
    scope = value.get('observation_scope')
    if scope not in (None, v1.SCOPE):
        raise ValueError('Wrong test observation scope')
    if value.get('status') == 'success' and scope != v1.SCOPE:
        raise ValueError('Missing test observation scope')
    checked = production.validate(
        dict(value, observation_scope='controlled-prototype-v1'
             if value.get('status') == 'success' else scope), transaction_id)
    checked['observation_scope'] = scope
    return checked


def invoke_test(transaction_id, source_digest, server_uuid):
    """Fixed executable/worker; caller supplies only committed source identity."""
    if type(transaction_id) is not int or not 0 < transaction_id < 2**63:
        return production.error(transaction_id, 'INVALID_EVENT')
    try:
        if hashlib.sha256(WORKER.read_bytes()).hexdigest() != WORKER_SHA256:
            return production.error(transaction_id, 'MODEL_INTEGRITY')
        authority = v1.load_authority()
        if server_uuid != authority['server_uuid']:
            return production.error(transaction_id, 'HISTORY_INCOMPLETE')
        child = subprocess.run(
            [str(PYTHON), '-I', '-B', str(WORKER), '--transaction-id',
             str(transaction_id), '--source-digest', source_digest,
             '--server-uuid', server_uuid], cwd=ROOT, input=b'',
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=TIMEOUT,
            check=False, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if child.returncode or len(child.stdout) > MAX_OUTPUT or len(child.stderr) > MAX_OUTPUT:
            return production.error(transaction_id, 'INFERENCE_ERROR')

        def reject_constant(_):
            raise ValueError('Nonfinite result')

        def unique_pairs(items):
            out = {}
            for key, item in items:
                if key in out:
                    raise ValueError('Duplicate result key')
                out[key] = item
            return out

        value = json.loads(child.stdout.decode('utf-8'), parse_constant=reject_constant,
                           object_pairs_hook=unique_pairs)
        return validate_test(value, transaction_id)
    except subprocess.TimeoutExpired:
        return production.error(transaction_id, 'RESOURCE_ERROR')
    except (OSError, ValueError, TypeError, UnicodeError, v1.BindingError):
        return production.error(transaction_id, 'INFERENCE_ERROR')


def process_test(transaction_id, publish=None):
    """Persist only in the pinned disposable database after source commit."""
    if type(transaction_id) is not int or not 0 < transaction_id < 2**63:
        raise ValueError('Invalid transaction ID')
    connection = v1.connection()
    locked = False
    try:
        locked = connection.execute('SELECT GET_LOCK(?,0) AS ok',
                                    ('v4_stage4sa_' + str(transaction_id),)).fetchone()['ok'] == 1
        if not locked:
            return None
        source = connection.execute(
            'SELECT * FROM canonical_mobile_money_events WHERE transaction_id=?',
            (transaction_id,)).fetchone()
        if source is None:
            return None
        existing = production.get(connection, transaction_id)
        if existing and existing['status'] != 'pending':
            return validate_test(existing, transaction_id)
        if existing is None:
            pending = production.error(transaction_id, 'PENDING')
            pending.update(status='pending', decision='pending', error_code=None)
            connection.execute('INSERT INTO v4_shadow_results VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                               (transaction_id, production.MODEL, production.FEATURE,
                                pending['inference_id'], 'pending', None, None, .5,
                                'pending', None, json.dumps(pending), production.now()))
        connection.commit()
        try:
            server_uuid = connection.execute('SELECT @@server_uuid AS id').fetchone()['id']
            digest = hashlib.sha256(json.dumps(dict(source), sort_keys=True,
                                               separators=(',', ':')).encode()).hexdigest()
            result = validate_test(invoke_test(transaction_id, digest, server_uuid), transaction_id)
        except Exception:
            result = production.error(transaction_id, 'INFERENCE_ERROR')
        updated = connection.execute('UPDATE v4_shadow_results SET inference_id=?,status=?,prediction=?,suspicious_probability=?,decision=?,error_code=?,body=? WHERE transaction_id=? AND model_version=? AND feature_version=? AND status=?',
                           (result['inference_id'], result['status'], result['prediction'],
                            result['suspicious_probability'], result['decision'], result['error_code'],
                            json.dumps(result, allow_nan=False), transaction_id,
                            production.MODEL, production.FEATURE, 'pending'))
        if updated.rowcount != 1:
            raise RuntimeError('Pending test result changed during inference')
        connection.commit()
        if publish is not None:
            try:
                publish(production.safe_payload(result))
            except Exception:
                pass
        return result
    finally:
        connection.rollback()
        if locked:
            connection.execute('SELECT RELEASE_LOCK(?)',
                               ('v4_stage4sa_' + str(transaction_id),))
        connection.close()


def after_commit(app, _connection_factory, transaction_id, socketio):
    """The pinned test application calls this fixed hook, never an HTTP selector."""
    try:
        return process_test(
            transaction_id,
            publish=lambda payload: production.publish_staff(v1.connection, socketio, payload))
    except Exception:
        app.logger.error('Isolated V4 shadow processing unavailable for transaction %s',
                         transaction_id)
        return None
