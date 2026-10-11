"""Versioned test deployment binding around unchanged Stage3 model operations.

The production Stage3 connector and history gate remain authoritative for aml.
This module is a separate test implementation of their deployment checks.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from ml_v4.frozen_inference import service as frozen

AUTHORITY = Path(__file__).resolve().parent / '.stage4t_authority.json'
VERSION = 'v4.test_binding.stage4t.1'
DATABASE = 'v4_stage4s_disposable'
USER = 'v4_stage4t_runner'
SCOPE = 'stage4t-isolated-v1'
BOUNDARY_KEYS = ('scope_id', 'scope_version', 'start_timestamp',
                 'start_transaction_id_exclusive', 'source_ledger',
                 'canonical_version', 'preexisting_parent_ids',
                 'preexisting_change_ids')


class BindingError(Exception):
    pass


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                     separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def config(url):
    """Parse only a dedicated test variable; never fall back to .env or DATABASE_URL."""
    p = urlparse(url)
    if (p.scheme not in ('mysql', 'mysql+mysqlconnector') or
        p.path != '/' + DATABASE or p.query or p.fragment or
        unquote(p.username or '') != USER or not p.password or
        not p.hostname or p.hostname == 'aml'):
        raise BindingError('Invalid isolated test configuration')
    return p


def grants_ok(grants):
    """Every grant must be USAGE globally or scoped to the one test database."""
    if not grants:
        return False
    for line in grants:
        normalized = line.replace('`', '').replace('"', '')
        if ' WITH GRANT OPTION' in normalized.upper():
            return False
        match = re.search(r'\bON\s+([^ ]+)\s+TO\s+', normalized, re.I)
        if not match:
            return False
        target = match.group(1)
        if target == '*.*':
            if not re.match(r'^GRANT USAGE ON \*\.\* TO ', normalized, re.I):
                return False
        elif target != DATABASE + '.*':
            return False
    return True


def identity(c, expected_server_uuid):
    """Check real server/database/principal and grants on the open connection."""
    if not isinstance(expected_server_uuid, str) or not expected_server_uuid.strip():
        raise BindingError('Expected test server identity required')
    row = c.execute('SELECT DATABASE() AS db, @@server_uuid AS server_id, CURRENT_USER() AS principal').fetchone()
    if (row['db'] != DATABASE or row['server_id'] != expected_server_uuid or
        not re.fullmatch(re.escape(USER) + r'@[^@]+', row['principal'])):
        raise BindingError('Test database/server/principal mismatch')
    rows = c.execute('SHOW GRANTS').fetchall()
    grants = [next(iter(r.values())) for r in rows]
    if not grants_ok(grants):
        raise BindingError('Test account has grants outside the disposable database')
    return {'database': row['db'], 'server_uuid': row['server_id'],
            'principal': row['principal']}


def load_authority():
    if not AUTHORITY.is_file() or AUTHORITY.is_symlink():
        raise BindingError('Test authority unavailable')
    data = json.loads(AUTHORITY.read_text(encoding='utf-8'))
    if (set(data) != {'binding_version', 'database', 'server_uuid', 'principal',
                      'scope_id', 'boundary_digest'} or
        data['binding_version'] != VERSION or data['database'] != DATABASE or
        data['scope_id'] != SCOPE or
        not re.fullmatch(r'[0-9a-f]{64}', data['boundary_digest'])):
        raise BindingError('Malformed test authority')
    return data


def connection(authority=None):
    """Open only with a dedicated test URL and verify before any caller SQL."""
    p = config(os.environ.get('V4_STAGE4T_TEST_DB_URL', ''))
    if authority is None:
        authority = load_authority()
    import mysql.connector
    from database import DatabaseAdapter
    c = DatabaseAdapter(mysql.connector.connect(
        host=p.hostname, port=p.port or 3306, user=USER,
        password=unquote(p.password), database=DATABASE,
        connection_timeout=5, charset='utf8mb4'), 'mysql')
    try:
        observed = identity(c, authority['server_uuid'])
        if observed['principal'] != authority['principal']:
            raise BindingError('Principal changed')
        return c
    except Exception:
        c.close()
        raise


def _triggers(c):
    from canonical_history_journal import triggers, ensure
    rows = c.execute('SELECT TRIGGER_NAME,EVENT_OBJECT_TABLE,EVENT_MANIPULATION,'
                     'ACTION_TIMING,ACTION_STATEMENT FROM information_schema.TRIGGERS '
                     'WHERE TRIGGER_SCHEMA=DATABASE()').fetchall()
    rows = [r for r in rows if r['TRIGGER_NAME'].lower().startswith('cmm_')]
    expected = triggers('mysql')
    if {r['TRIGGER_NAME'] for r in rows} != set(expected):
        raise BindingError('Capture trigger set mismatch')
    for row in rows:
        table, operation, body = expected[row['TRIGGER_NAME']]
        if (row['EVENT_OBJECT_TABLE'], row['EVENT_MANIPULATION'],
            row['ACTION_TIMING'], row['ACTION_STATEMENT']) != (table, operation, 'AFTER', body):
            raise BindingError('Capture trigger body mismatch')
    ensure(c)


def _boundary(c, authority):
    from canonical_history_store import current_scope
    scope = current_scope(c, SCOPE)
    if scope is None or scope['revision'] != 1:
        raise BindingError('Test boundary missing or revised')
    immutable = {k: scope[k] for k in BOUNDARY_KEYS}
    if (_digest(immutable) != authority['boundary_digest'] or
        scope['scope_id'] != SCOPE or scope['verification_authority'] != VERSION):
        raise BindingError('Test observation boundary mismatch')
    count = c.execute('SELECT COUNT(*) AS n FROM cmm_observation_scopes').fetchone()['n']
    if count != 1:
        raise BindingError('Unexpected observation scope')
    return scope


def verified_snapshot(c, tx, authority):
    """Stage2A assessment and freshness with a genuine pinned test boundary."""
    from canonical_history_store import assess, snapshot
    from canonical_history import freshness
    from canonical_mobile_money import FIELDS
    pins = json.loads((ROOT / 'ml_v4/frozen_inference/history_authority.json').read_text())
    for path, digest in pins.items():
        frozen.verified_bytes({'path': path, 'sha256': digest})
    # The connection and its identity reads may have opened a transaction.
    # Start the read-only snapshot before reading trigger and ledger state.
    c.rollback()
    c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
    c.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY')
    identity(c, authority['server_uuid'])
    _triggers(c)
    _boundary(c, authority)
    scope, current, previous = assess(c, SCOPE)
    state = freshness(scope, current, previous)
    if (state != 'COMPLETE_VERIFIED' or current['issues'] or
        scope['scope_version'] != 'prototype.observation.v1' or
        current['graph_scope'] != 'All post-boundary prototype transactions, no entity or edge filters'):
        raise BindingError('History incomplete or stale')
    _, canonical, _ = snapshot(c)
    allowed = set(current['canonical_event_ids'])
    if tx not in allowed:
        raise BindingError('Event unavailable')
    events = [{k: row[k] for k in FIELDS} for row in canonical
              if row['transaction_id'] in allowed]
    if len(events) != len(allowed):
        raise BindingError('Canonical graph incomplete')
    return events, dict(event_timestamp=next(e['event_timestamp'] for e in events if e['transaction_id'] == tx),
                        observation_scope=SCOPE, scope_revision=scope['revision'],
                        source_revision=current['source_revision'], history_status=state,
                        history_complete_through=dict(key=current['complete_through_key'],
                                                      timestamp=current['complete_through_timestamp']),
                        history_scope_warning='Isolated test ledger from its own verified observation boundary only.')


def infer(tx):
    """Separate test result path; calls unchanged FrozenModel replay/predict."""
    out = frozen.result(tx)
    c = None
    try:
        if type(tx) is not int or not 0 < tx < 2**63:
            raise frozen.Failure('INVALID_EVENT')
        authority = load_authority()
        c = connection(authority)
        events, context = verified_snapshot(c, tx, authority)
        out.update(context)
        model = frozen.FrozenModel()
        x, event = model.replay(events, tx)
        out['event_timestamp'] = event.event_timestamp
        p = model.predict(x)
        prediction, decision = frozen.probability_decision(p)
        out.update(status='success', prediction=prediction, suspicious_probability=p,
                   decision=decision, human_review_required=bool(prediction))
    except frozen.Failure as exc:
        out['error_code'] = exc.code
    except BindingError:
        out['error_code'] = 'HISTORY_INCOMPLETE'
    except MemoryError:
        out['error_code'] = 'HISTORY_RESOURCE_EXHAUSTED'
    except Exception:
        out['error_code'] = 'INFERENCE_ERROR'
    finally:
        if c is not None:
            try:
                c.rollback()
                c.close()
            except Exception:
                out.update(status='inference_error', prediction=None,
                           suspicious_probability=None, decision='inference_error',
                           error_code='HISTORY_UNAVAILABLE', human_review_required=False)
        out['inference_timestamp'] = frozen.utc()
    return out


def prepare():
    """Explicit local setup after administrator creates scoped DB/user.

    Requires an empty test database and exact server UUID before any write.
    No reset/recreate path exists once an authority or scope exists.
    """
    if AUTHORITY.exists():
        raise BindingError('Test authority already established')
    expected = os.environ.get('V4_STAGE4T_EXPECTED_SERVER_UUID', '')
    p = config(os.environ.get('V4_STAGE4T_TEST_DB_URL', ''))
    if not expected:
        raise BindingError('Expected test server UUID required')
    import mysql.connector
    from database import DatabaseAdapter
    c = DatabaseAdapter(mysql.connector.connect(
        host=p.hostname, port=p.port or 3306, user=USER,
        password=unquote(p.password), database=DATABASE,
        connection_timeout=5, charset='utf8mb4'), 'mysql')
    try:
        observed = identity(c, expected)
        # The application schema must be installed separately and reviewed.
        # Stage4T never manufactures a transaction table with altered semantics.
        table_rows = c.execute('SHOW TABLES').fetchall()
        tables = {next(iter(row.values())) for row in table_rows}
        if not {'users', 'agents', 'transactions'}.issubset(tables) or any(
                name.startswith('cmm_') or name == 'canonical_mobile_money_events'
                or name == 'v4_shadow_results' for name in tables):
            raise BindingError('Expected reviewed application schema without prior V4 state')
        columns = {r['Field']: r['Type'].lower() for r in
                   c.execute('SHOW COLUMNS FROM transactions').fetchall()}
        if (columns.get('id') != 'bigint' or
            columns.get('timestamp') not in ('varchar(40)', 'varchar(255)') or
            not {'sender_account', 'receiver_account', 'amount', 'transaction_type',
                 'currency', 'agent_id', 'status'}.issubset(columns)):
            raise BindingError('Application transaction schema lacks exact test requirements')
        if c.execute('SELECT COUNT(*) AS n FROM transactions').fetchone()['n'] != 0:
            raise BindingError('Test transaction table must be empty before boundary')
        from canonical_mobile_money_store import migrate as canonical_migrate
        from canonical_history_store import migrate as history_migrate, create_scope, attest
        from canonical_history_journal import ensure
        from v4_shadow import migrate as result_migrate
        canonical_migrate(c)
        history_migrate(c)
        ensure(c, apply=True)
        result_migrate(c)
        c.commit()
        identity(c, expected)
        _triggers(c)
        if c.execute('SELECT COUNT(*) AS n FROM transactions').fetchone()['n'] != 0:
            raise BindingError('Test parent table unexpectedly populated')
        scope = create_scope(c, SCOPE, VERSION, 'stage4t/isolated-test-provisioning')
        c.commit()
        result = attest(c, SCOPE, VERSION, 'stage4t/initial-empty-assessment')
        c.commit()
        if result['status'] != 'COMPLETE_VERIFIED':
            raise BindingError('Initial test assessment incomplete')
        immutable = {k: scope[k] for k in BOUNDARY_KEYS}
        record = dict(binding_version=VERSION, database=DATABASE,
                      server_uuid=observed['server_uuid'], principal=observed['principal'],
                      scope_id=SCOPE, boundary_digest=_digest(immutable))
        with AUTHORITY.open('x', encoding='utf-8') as target:
            json.dump(record, target, indent=2)
            target.write('\n')
        return record
    finally:
        c.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'check', 'infer'))
    parser.add_argument('--transaction-id', type=int)
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare()
        print('Isolated test boundary created and attested')
    elif args.action == 'check':
        a = load_authority()
        c = connection(a)
        try:
            _triggers(c)
            _boundary(c, a)
            print('Isolated test identity and authority verified')
        finally:
            c.close()
    else:
        if args.transaction_id is None:
            parser.error('--transaction-id required')
        print(json.dumps(infer(args.transaction_id), allow_nan=False))
