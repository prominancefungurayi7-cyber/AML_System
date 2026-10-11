"""Read-only verification of an existing Stage4S-B run; creates no fixtures."""
import json
from ml_v4.test_binding import v1
from ml_v4.stage4sa.coordinator import validate_test
from canonical_history_store import assess
from canonical_history import freshness


def run():
    authority = v1.load_authority()
    db = v1.connection(authority)
    try:
        v1._triggers(db)
        v1._boundary(db, authority)
        scope, current, previous = assess(db, v1.SCOPE)
        result = {'database': v1.DATABASE, 'server_uuid': authority['server_uuid'],
                  'principal': authority['principal'],
                  'history_status': freshness(scope, current, previous), 'rows': []}
        for tx in (1, 2, 3, 4):
            transaction = db.execute('SELECT id,transaction_type,risk_level,ai_risk_level FROM transactions WHERE id=?', (tx,)).fetchone()
            canonical = db.execute('SELECT COUNT(*) AS n FROM canonical_mobile_money_events WHERE transaction_id=?', (tx,)).fetchone()['n']
            changes = db.execute('SELECT operation FROM cmm_source_changes WHERE transaction_id=?', (tx,)).fetchall()
            shadow = db.execute('SELECT status,body FROM v4_shadow_results WHERE transaction_id=?', (tx,)).fetchone()
            body = json.loads(shadow['body']) if shadow else None
            valid = False
            if body is not None:
                valid = validate_test(body, tx)['status'] == 'success' and shadow['status'] == 'success'
            result['rows'].append({'transaction_id': tx, 'transaction': dict(transaction) if transaction else None,
                                   'canonical_rows': canonical, 'capture_operations': [r['operation'] for r in changes],
                                   'shadow_status': shadow['status'] if shadow else None,
                                   'valid_v4_success': valid,
                                   'model_version': body.get('model_version') if body else None,
                                   'model_sha256': body.get('model_sha256') if body else None,
                                   'threshold': body.get('threshold') if body else None,
                                   'prediction': body.get('prediction') if body else None,
                                   'suspicious_probability': body.get('suspicious_probability') if body else None})
        result['counts'] = {table: db.execute('SELECT COUNT(*) AS n FROM ' + table).fetchone()['n']
                            for table in ('transactions', 'canonical_mobile_money_events',
                                          'cmm_source_changes', 'v4_shadow_results', 'alerts')}
        print(json.dumps(result, indent=2, sort_keys=True))
    finally:
        db.rollback()
        db.close()


if __name__ == '__main__':
    try:
        run()
    except Exception as exc:
        print('Read-only diagnosis stopped: ' + type(exc).__name__)
        raise SystemExit(1)
