"""Load the unchanged Flask application in a private, test-only process."""
import ast
import hashlib
import os
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / 'server.py'
SERVER_SHA256 = '5139ad7832a0702b019b6b92907edef81e3a3a1d0624373a77e38284be9b39cb'


def _is_name_guard(node):
    return (isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
            and isinstance(node.test.left, ast.Name)
            and node.test.left.id == '__name__'
            and len(node.test.comparators) == 1
            and isinstance(node.test.comparators[0], ast.Constant)
            and node.test.comparators[0].value == '__main__'
            and isinstance(node.test.ops[0], (ast.Eq, ast.NotEq)))


def source_without_startup():
    """Remove only the known startup branches and dotenv calls from pinned source."""
    raw = SERVER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SERVER_SHA256:
        raise RuntimeError('Application source changed')
    tree = ast.parse(raw, filename=str(SERVER))
    kept = []
    guard_count = dotenv_count = 0
    for node in tree.body:
        if _is_name_guard(node):
            guard_count += 1
            continue
        if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == 'load_dotenv' and not node.value.args
                and not node.value.keywords):
            dotenv_count += 1
            continue
        kept.append(node)
    if guard_count != 3 or dotenv_count != 2:
        raise RuntimeError('Unrecognized application startup structure')
    tree.body = kept
    return compile(ast.fix_missing_locations(tree), str(SERVER), 'exec')


def _dedicated_url():
    from ml_v4.test_binding import v1
    url = os.environ.get('V4_STAGE4T_TEST_DB_URL', '')
    v1.config(url)
    if os.environ.get('V4_STAGE4T_EXPECTED_SERVER_UUID') != 'd441b7bb-43f6-11f1-a2d8-0a0027000005':
        raise RuntimeError('Test server UUID not pinned')
    for key in ('DATABASE_URL', 'MYSQL_URL'):
        existing = os.environ.get(key)
        if existing and existing != url:
            raise RuntimeError('Conflicting application database configuration')
    if os.environ.get('V4_SHADOW_ENABLED', 'OFF') == 'ON':
        raise RuntimeError('Ordinary shadow mode must remain off')
    return url


def load_test_application():
    """Return a Flask test client app; never serve it or run startup routines."""
    if 'server' in sys.modules:
        raise RuntimeError('Ordinary server already imported in this process')
    url = _dedicated_url()
    code = source_without_startup()
    from ml_v4.test_binding import v1
    from ml_v4.stage4sa import coordinator
    import database
    import mysql.connector
    import v4_shadow

    # No import-time SQL or external broker connection is permitted.
    original_db = database.connect_db
    original_mysql = mysql.connector.connect
    old_env = {key: os.environ.get(key) for key in
               ('DATABASE_URL', 'MYSQL_URL', 'REDIS_URL', 'KAFKA_BOOTSTRAP_SERVERS',
                'SOCKETIO_ALLOWED_ORIGINS')}
    def forbidden(*_args, **_kwargs):
        raise RuntimeError('Database connection during test application import')
    database.connect_db = forbidden
    mysql.connector.connect = forbidden
    os.environ['DATABASE_URL'] = url
    os.environ['MYSQL_URL'] = url
    os.environ.pop('REDIS_URL', None)
    os.environ.pop('KAFKA_BOOTSTRAP_SERVERS', None)
    os.environ['SOCKETIO_ALLOWED_ORIGINS'] = 'http://localhost'
    module = types.ModuleType('stage4sa_server')
    module.__file__ = str(SERVER)
    module.__package__ = ''
    module.__dict__['__name__'] = 'stage4sa_server'
    sys.modules[module.__name__] = module
    loaded = False
    try:
        exec(code, module.__dict__)
        loaded = True
    except Exception:
        sys.modules.pop(module.__name__, None)
        raise
    finally:
        database.connect_db = original_db
        mysql.connector.connect = original_mysql
        if not loaded:
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def pinned_connection(candidate=None):
        if candidate is not None and candidate != url:
            raise RuntimeError('Non-test database requested')
        return v1.connection()

    module._database_connect_db = pinned_connection
    module.app.config.update(DATABASE=url, DATABASE_URL=url, TESTING=True,
                             MONITOR_STOP=True, SECRET_KEY='stage4sa-test-client-only')
    module.app.extensions['stage4sa_connection'] = pinned_connection
    def no_listener(*_args, **_kwargs):
        raise RuntimeError('Stage4S-A app is for Flask test_client only')
    module.app.run = no_listener
    module.socketio.run = no_listener
    module.app.view_functions['health'] = lambda: {
        'status': 'isolated_test_only', 'database': v1.DATABASE}
    from flask import request
    @module.app.before_request
    def verify_test_source_before_fixture():
        if request.path != '/customer/transaction' or request.method != 'POST':
            return None
        authority = v1.load_authority()
        connection = v1.connection(authority)
        try:
            v1._triggers(connection)
            v1._boundary(connection, authority)
            from canonical_history_store import assess
            from canonical_history import freshness
            scope, current, previous = assess(connection, v1.SCOPE)
            if freshness(scope, current, previous) != 'COMPLETE_VERIFIED' or current['issues']:
                raise RuntimeError('Test history not fresh')
        finally:
            connection.rollback()
            connection.close()
    # This module's only shadow hook is the fixed Stage4T coordinator.
    v4_shadow.after_commit = coordinator.after_commit
    return module.app
