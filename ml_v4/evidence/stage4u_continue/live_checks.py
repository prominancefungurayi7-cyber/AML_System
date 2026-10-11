"""Read-only checks for user-run Stage4U continuation; never prints credentials."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ml_v4.test_binding import v1

EXPECTED_UUID = 'd441b7bb-43f6-11f1-a2d8-0a0027000005'
REQUIRED = {'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE',
            'REFERENCES', 'INDEX', 'ALTER', 'TRIGGER'}


def _connect():
    p = v1.config(os.environ.get('V4_STAGE4T_TEST_DB_URL', ''))
    if os.environ.get('V4_STAGE4T_EXPECTED_SERVER_UUID') != EXPECTED_UUID:
        raise v1.BindingError('Expected server UUID mismatch')
    import mysql.connector
    from database import DatabaseAdapter
    c = DatabaseAdapter(mysql.connector.connect(
        host=p.hostname, port=p.port or 3306, user=v1.USER,
        password=unquote(p.password), database=v1.DATABASE,
        connection_timeout=5, charset='utf8mb4'), 'mysql')
    try:
        identity = v1.identity(c, EXPECTED_UUID)
        grants = [next(iter(row.values())) for row in c.execute('SHOW GRANTS').fetchall()]
        scoped = []
        for line in grants:
            normalized = line.replace('`', '').replace('"', '')
            if ' ON ' + v1.DATABASE + '.* TO ' in normalized:
                scoped.extend(x.strip().upper() for x in normalized.split(' ON ', 1)[0][6:].split(','))
        if set(scoped) != REQUIRED:
            raise v1.BindingError('Test grants do not equal approved privilege set')
        version = c.execute('SELECT VERSION() AS version').fetchone()['version']
        if not str(version).startswith('8.0.46'):
            raise v1.BindingError('MySQL version mismatch')
        return c, p, identity, version, sorted(REQUIRED)
    except Exception:
        c.close()
        raise


def _record(name, data):
    path = OUT / name
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(name + ': PASS')


def preflight():
    c, p, identity, version, privileges = _connect()
    try:
        tables = [next(iter(row.values())) for row in c.execute('SHOW TABLES').fetchall()]
        if tables:
            raise v1.BindingError('Expected empty disposable database before schema install')
        # Real connection with test credentials to aml must be denied.
        import mysql.connector
        denied = False
        try:
            probe = mysql.connector.connect(
                host=p.hostname, port=p.port or 3306, user=v1.USER,
                password=unquote(p.password), database='aml', connection_timeout=5)
        except mysql.connector.Error:
            denied = True
        else:
            probe.close()
        if not denied:
            raise v1.BindingError('Test principal can access aml')
        from ml_v4.frozen_inference.cli import connection as production_connection
        original = os.environ.get('DATABASE_URL')
        os.environ['DATABASE_URL'] = os.environ['V4_STAGE4T_TEST_DB_URL']
        try:
            production_rejected = False
            try:
                production_connection()
            except ValueError:
                production_rejected = True
            if not production_rejected:
                raise v1.BindingError('Production connector accepted test database')
        finally:
            if original is None:
                os.environ.pop('DATABASE_URL', None)
            else:
                os.environ['DATABASE_URL'] = original
        _record('preflight_live.json', dict(status='PASS', server_uuid=identity['server_uuid'],
                                           database=identity['database'], principal=identity['principal'],
                                           mysql_version=version, scoped_privileges=privileges,
                                           schema_empty=True, test_account_aml_access_denied=True,
                                           production_connector_rejected_test_database=True,
                                           writes=0, fixture_transactions=0))
    finally:
        c.close()


def verify():
    c, _, identity, version, privileges = _connect()
    try:
        authority = v1.load_authority()
        assert authority['server_uuid'] == EXPECTED_UUID
        assert authority['principal'] == identity['principal']
        c.rollback()
        v1._triggers(c)
        scope = v1._boundary(c, authority)
        from canonical_history_store import assess, latest
        from canonical_history import freshness
        scoped, current, previous = assess(c, v1.SCOPE)
        actual = freshness(scoped, current, previous)
        if (actual != 'COMPLETE_VERIFIED' or current['issues'] or
            current['canonical_event_ids'] or previous is None or
            previous['status'] != 'COMPLETE_VERIFIED'):
            raise v1.BindingError('Empty-ledger authority not fresh')
        from canonical_history_journal import triggers
        expected_triggers = sorted(triggers('mysql'))
        rows = c.execute('SELECT TRIGGER_NAME FROM information_schema.TRIGGERS '
                         'WHERE TRIGGER_SCHEMA=DATABASE()').fetchall()
        found = sorted(row['TRIGGER_NAME'] for row in rows
                       if row['TRIGGER_NAME'].lower().startswith('cmm_'))
        if found != expected_triggers:
            raise v1.BindingError('Capture trigger set mismatch')
        from ml_v4.frozen_inference.cli import connection as production_connection
        original = os.environ.get('DATABASE_URL')
        os.environ['DATABASE_URL'] = os.environ['V4_STAGE4T_TEST_DB_URL']
        try:
            try:
                production_connection()
            except ValueError:
                pass
            else:
                raise v1.BindingError('Production binder accepted test database')
        finally:
            if original is None:
                os.environ.pop('DATABASE_URL', None)
            else:
                os.environ['DATABASE_URL'] = original
        if v1.config('mysql://v4_stage4t_runner:x@127.0.0.1/' + v1.DATABASE).path != '/' + v1.DATABASE:
            raise v1.BindingError('Test binder parse mismatch')
        try:
            v1.config('mysql://v4_stage4t_runner:x@127.0.0.1/aml')
        except v1.BindingError:
            pass
        else:
            raise v1.BindingError('Test binder accepted aml')
        try:
            v1.identity(c, '00000000-0000-0000-0000-000000000000')
        except v1.BindingError:
            pass
        else:
            raise v1.BindingError('Wrong server UUID accepted')
        altered = dict(authority, boundary_digest='0' * 64)
        try:
            v1._boundary(c, altered)
        except v1.BindingError:
            pass
        else:
            raise v1.BindingError('Altered boundary accepted')
        for table in ('transactions', 'canonical_mobile_money_events',
                      'cmm_source_changes', 'v4_shadow_results'):
            if c.execute('SELECT COUNT(*) AS n FROM ' + table).fetchone()['n']:
                raise v1.BindingError('Test ledger/result table not empty')
        authority_hash = hashlib.sha256(v1.AUTHORITY.read_bytes()).hexdigest()
        _record('verification_live.json', dict(status='PASS', server_uuid=identity['server_uuid'],
                                               database=identity['database'], principal=identity['principal'],
                                               mysql_version=version, scoped_privileges=privileges,
                                               trigger_names=found, trigger_bodies_exact=True,
                                               observation_scope=scope['scope_id'],
                                               boundary_digest=authority['boundary_digest'],
                                               authority_file_sha256=authority_hash,
                                               assessment_status=actual, source_revision=current['source_revision'],
                                               wrong_server_rejected=True, altered_boundary_rejected=True,
                                               production_rejects_test_database=True,
                                               test_rejects_aml=True, financial_rows=0,
                                               shadow_results=0))
    finally:
        c.rollback()
        c.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('preflight', 'verify'))
    args = parser.parse_args()
    try:
        (preflight if args.action == 'preflight' else verify)()
    except Exception as exc:
        # Credential-bearing URLs and driver messages must not appear in output.
        print('Live check failed: ' + type(exc).__name__, file=sys.stderr)
        raise SystemExit(1)
