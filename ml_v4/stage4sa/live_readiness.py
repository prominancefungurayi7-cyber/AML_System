"""Read-only local check; never submits a transaction or starts a server."""
import hashlib
import json
from pathlib import Path

from ml_v4.stage4sa.harness import load_test_application, source_without_startup
from ml_v4.stage4sa import coordinator
from ml_v4.test_binding import v1

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'ml_v4/evidence/stage4sa'
MODEL = ROOT / 'ml_v4/development_training/artifacts/primary_XGB_EXPERIMENTAL.joblib'
EXPECTED_MODEL = '555bf1606bf0af97361e3f187575b7229645d5979a43e4c812db259dbfd2bf18'
EXPECTED_BINDING = '4ec57bbdc3f1b0f203f86ab4c723ebdd04029ee001d7164ab1e14aebc83a42dc'


def run():
    if hashlib.sha256(MODEL.read_bytes()).hexdigest() != EXPECTED_MODEL:
        raise RuntimeError('Frozen model hash mismatch')
    if hashlib.sha256(Path(v1.__file__).read_bytes()).hexdigest() != EXPECTED_BINDING:
        raise RuntimeError('Approved test binding source changed')
    if hashlib.sha256(coordinator.WORKER.read_bytes()).hexdigest() != coordinator.WORKER_SHA256:
        raise RuntimeError('Approved test worker source changed')
    source_without_startup()
    authority = v1.load_authority()
    connection = v1.connection(authority)
    try:
        from ml_v4.evidence.mysql_test_recovery.recover_partial import EXPECTED_TABLES
        tables = {next(iter(row.values())) for row in connection.execute('SHOW TABLES').fetchall()}
        if tables != EXPECTED_TABLES | {'v4_shadow_results'}:
            raise RuntimeError('Test table set mismatch')
        import v4_shadow
        if v4_shadow.migrate(connection) is not False:
            raise RuntimeError('Shadow result schema unavailable')
        v1._triggers(connection)
        scope = v1._boundary(connection, authority)
        from canonical_history_store import assess
        from canonical_history import freshness
        observed, current, previous = assess(connection, v1.SCOPE)
        if (freshness(observed, current, previous) != 'COMPLETE_VERIFIED'
                or current['issues'] or current['canonical_event_ids']):
            raise RuntimeError('Test history not freshly verified and empty')
        for table in ('transactions', 'canonical_mobile_money_events',
                      'cmm_source_changes', 'v4_shadow_results'):
            if connection.execute('SELECT COUNT(*) AS n FROM ' + table).fetchone()['n']:
                raise RuntimeError('Test ledger/result table is no longer empty')
    finally:
        connection.rollback()
        connection.close()
    app = load_test_application()
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    if '/customer/transaction' not in rules or '/api/v4-shadow/results' not in rules:
        raise RuntimeError('Test Flask route missing')
    if app.config['DATABASE'].split('/')[-1] != v1.DATABASE:
        raise RuntimeError('Flask database mismatch')
    if coordinator.WORKER != ROOT / 'ml_v4/test_binding/worker.py':
        raise RuntimeError('Test worker mismatch')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'local_readiness.json').write_text(json.dumps({
        'status': 'PASS', 'database': v1.DATABASE,
        'scope': scope['scope_id'], 'scope_revision': scope['revision'],
        'server_uuid': authority['server_uuid'], 'principal': authority['principal'],
        'history_status': 'COMPLETE_VERIFIED',
        'frozen_model_sha256': EXPECTED_MODEL,
        'startup_skipped': True, 'worker': 'ml_v4/test_binding/worker.py',
        'financial_fixtures': 0, 'v4_shadow_enabled': False,
    }, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print('Stage4S-A local readiness PASS; no financial fixtures submitted.')


if __name__ == '__main__':
    try:
        run()
    except Exception as exc:
        print('Stage4S-A readiness stopped: ' + type(exc).__name__)
        raise SystemExit(1)
