"""Resume only the exact empty Stage4U partial test schema. Never resets a DB."""
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
from ml_v4.evidence.stage4u_continue.live_checks import _connect, EXPECTED_UUID

EXPECTED_TABLES = set(json.loads(
    (ROOT / 'ml_v4/evidence/stage4u/schema_review.json').read_text())['ordered_tables']) | {
        'canonical_mobile_money_events', 'cmm_observation_scopes',
        'cmm_history_attestations', 'cmm_entity_history', 'cmm_source_changes'}


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def record(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def static_integrity():
    inherited = json.loads((ROOT / 'ml_v4/evidence/stage4s/verification.json').read_text())['hashes']
    if any(sha(path) != item['expected'] for path, item in inherited.items()):
        raise v1.BindingError('Inherited protected artifact mismatch')
    stage4u = json.loads((ROOT / 'ml_v4/evidence/stage4u/decision.json').read_text())
    if any(sha(path) != digest for path, digest in stage4u['new_artifact_sha256'].items()):
        raise v1.BindingError('Stage4U schema/test adapter changed')
    schema = json.loads((ROOT / 'ml_v4/evidence/stage4u/schema_review.json').read_text())
    if any(sha(path) != digest for path, digest in schema['source_hashes'].items()):
        raise v1.BindingError('Application schema source changed')
    if sha('ml_v4/evidence/stage4u/application_schema_only.sql') != schema['schema_sha256']:
        raise v1.BindingError('Application schema SQL changed')
    return len(inherited)


def inspect_state(c, expected_tables, require_empty=True):
    tables = {next(iter(row.values())) for row in c.execute('SHOW TABLES').fetchall()}
    if tables != expected_tables:
        raise v1.BindingError('Unexpected test table set')
    rows = c.execute('SELECT TRIGGER_NAME FROM information_schema.TRIGGERS '
                     'WHERE TRIGGER_SCHEMA=DATABASE()').fetchall()
    trigger_names = sorted(row['TRIGGER_NAME'] for row in rows)
    if require_empty and trigger_names:
        raise v1.BindingError('Expected zero triggers before recovery')
    counts = {table: c.execute('SELECT COUNT(*) AS n FROM ' + table).fetchone()['n']
              for table in sorted(tables)}
    if any(counts.values()):
        raise v1.BindingError('Nonempty test table before financial fixtures')
    if v1.AUTHORITY.exists():
        raise v1.BindingError('Unexpected test authority file')
    columns = {r['Field']: r['Type'].lower() for r in
               c.execute('SHOW COLUMNS FROM transactions').fetchall()}
    if (columns.get('id') != 'bigint' or columns.get('timestamp') != 'varchar(40)' or
        not {'sender_account', 'receiver_account', 'amount', 'transaction_type',
             'currency', 'agent_id', 'status', 'risk_score', 'rule_score'}.issubset(columns)):
        raise v1.BindingError('Application transaction schema mismatch')
    indexes = {r['Key_name'] for r in c.execute('SHOW INDEX FROM transactions').fetchall()}
    if not {'PRIMARY', 'idx_stage4u_tx_sender_time',
            'idx_stage4u_tx_receiver_time', 'idx_stage4u_tx_agent_time'}.issubset(indexes):
        raise v1.BindingError('Application indexes incomplete')
    from canonical_mobile_money_store import inspect as canonical_inspect
    from canonical_history_store import TABLES as history_tables
    if not canonical_inspect(c)['exists']:
        raise v1.BindingError('Canonical schema missing')
    for table, names in history_tables.items():
        found = [r['Field'] for r in c.execute('SHOW COLUMNS FROM ' + table).fetchall()]
        if found != list(names):
            raise v1.BindingError('History table columns mismatch')
    journal = {r['Field']: r['Type'].lower() for r in
               c.execute('SHOW COLUMNS FROM cmm_source_changes').fetchall()}
    if (journal.get('change_id') != 'bigint' or
        set(journal) != {'change_id', 'transaction_id', 'operation',
                         'event_timestamp', 'recorded_at'}):
        raise v1.BindingError('Capture journal schema mismatch')
    return {'tables': sorted(tables), 'triggers': trigger_names,
            'row_counts': counts}


def denied_aml(p):
    import mysql.connector
    try:
        probe = mysql.connector.connect(host=p.hostname, port=p.port or 3306,
                                         user=v1.USER, password=unquote(p.password),
                                         database='aml', connection_timeout=5)
    except mysql.connector.Error:
        return True
    else:
        probe.close()
        return False


def run():
    protected = static_integrity()
    c, p, identity, version, privileges = _connect()
    try:
        if not denied_aml(p):
            raise v1.BindingError('Test account can access aml')
        setting = c.execute('SELECT @@GLOBAL.log_bin_trust_function_creators AS allowed').fetchone()['allowed']
        if setting != 1:
            raise v1.BindingError('MySQL trigger creation setting is not enabled')
        before = inspect_state(c, EXPECTED_TABLES)
        preflight = {'status': 'PASS_BEFORE_WRITES', 'database': identity['database'],
                     'server_uuid': identity['server_uuid'], 'principal': identity['principal'],
                     'mysql_version': version, 'scoped_privileges': privileges,
                     'test_account_aml_access_denied': True,
                     'log_bin_trust_function_creators': 1,
                     'protected_paths_exact': protected, **before}
        record('before_writes.json', preflight)
        c.rollback()

        from canonical_history_store import migrate as history_migrate, create_scope, attest
        from canonical_history_journal import ensure, triggers
        from v4_shadow import migrate as result_migrate
        # Existing migrations validate the installed canonical/history tables.
        if history_migrate(c):
            raise v1.BindingError('History migration unexpectedly created a table')
        c.rollback()
        # MySQL DDL auto-commits. An error here may leave some triggers; the
        # next run refuses that state and requires administrator review.
        ensure(c, apply=True)
        c.commit()
        v1._triggers(c)
        if result_migrate(c) is not True:
            raise v1.BindingError('Expected missing shadow result table')
        c.commit()
        v1.identity(c, EXPECTED_UUID)
        v1._triggers(c)
        if c.execute('SELECT COUNT(*) AS n FROM transactions').fetchone()['n']:
            raise v1.BindingError('Unexpected transaction after schema recovery')
        if c.execute('SELECT COUNT(*) AS n FROM cmm_source_changes').fetchone()['n']:
            raise v1.BindingError('Unexpected journal entry after schema recovery')
        # Scope and attestation share one transaction. No status is supplied.
        c.rollback()
        scope = create_scope(c, v1.SCOPE, v1.VERSION,
                             'mysql-test-recovery/genuine-empty-boundary')
        result = attest(c, v1.SCOPE, v1.VERSION,
                        'mysql-test-recovery/genuine-empty-assessment')
        if result['status'] != 'COMPLETE_VERIFIED' or result['issues']:
            c.rollback()
            raise v1.BindingError('Calculated empty-ledger attestation incomplete')
        c.commit()
        immutable = {key: scope[key] for key in v1.BOUNDARY_KEYS}
        authority = dict(binding_version=v1.VERSION, database=v1.DATABASE,
                         server_uuid=identity['server_uuid'],
                         principal=identity['principal'], scope_id=v1.SCOPE,
                         boundary_digest=v1._digest(immutable))
        with v1.AUTHORITY.open('x', encoding='utf-8') as target:
            json.dump(authority, target, indent=2)
            target.write('\n')
        v1._boundary(c, authority)
        v1._triggers(c)
        from canonical_history_store import assess
        from canonical_history import freshness
        _, current, previous = assess(c, v1.SCOPE)
        if freshness(scope, current, previous) != 'COMPLETE_VERIFIED':
            raise v1.BindingError('New test attestation not fresh')
        if any(c.execute('SELECT COUNT(*) AS n FROM ' + table).fetchone()['n']
               for table in ('transactions', 'canonical_mobile_money_events',
                             'cmm_source_changes', 'v4_shadow_results')):
            raise v1.BindingError('Financial or result row unexpectedly present')
        observed = c.execute('SELECT TRIGGER_NAME FROM information_schema.TRIGGERS '
                             'WHERE TRIGGER_SCHEMA=DATABASE()').fetchall()
        names = sorted(r['TRIGGER_NAME'] for r in observed)
        if names != sorted(triggers('mysql')):
            raise v1.BindingError('Capture trigger count/name mismatch')
        record('recovery_result.json', {
            'status': 'PASS', 'database': identity['database'],
            'server_uuid': identity['server_uuid'], 'principal': identity['principal'],
            'mysql_version': version, 'application_and_history_tables_before': before['tables'],
            'tables_after_count': len(EXPECTED_TABLES) + 1,
            'trigger_names': names, 'trigger_bodies_exact': True,
            'new_shadow_results_table': True,
            'scope_id': scope['scope_id'], 'scope_revision': scope['revision'],
            'boundary_digest': authority['boundary_digest'],
            'authority_file_sha256': hashlib.sha256(v1.AUTHORITY.read_bytes()).hexdigest(),
            'attestation_status': result['status'],
            'freshness': 'COMPLETE_VERIFIED',
            'source_revision': current['source_revision'],
            'financial_transactions': 0, 'canonical_events': 0,
            'shadow_results': 0, 'production_aml_connection_used': False})
        print('Disposable test schema and genuine empty history authority recovered.')
    finally:
        c.rollback()
        c.close()


if __name__ == '__main__':
    try:
        run()
    except Exception as exc:
        # Never print a connector error or credential-bearing URL.
        record('recovery_failure.json', {'status': 'STOPPED',
                                        'error_class': type(exc).__name__,
                                        'guidance': 'Inspect disposable database state before any retry.'})
        print('Recovery stopped: ' + type(exc).__name__, file=sys.stderr)
        raise SystemExit(1)
