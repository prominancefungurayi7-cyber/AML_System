"""Finish only Stage5C checks that need no financial POST."""
import json
from pathlib import Path
import sys

from ml_v4.stage4sa.harness import load_test_application
from ml_v4.stage5c.live_primary import inspect_prior
from ml_v4.test_binding import v1

OUT = Path(__file__).resolve().parents[1] / 'evidence/stage5c/finish_readonly.json'


def run():
    review = inspect_prior()
    if review['status'] != 'RECONCILED' or review['baseline']['history'] != 'COMPLETE_VERIFIED':
        raise RuntimeError('Stage5C history or balances unresolved')
    counts = review['baseline']['counts']
    if (counts['transactions'], counts['canonical_mobile_money_events'],
            counts['cmm_source_changes'], counts['v4_shadow_results']) != (8, 8, 16, 8):
        raise RuntimeError('Stage5C source/result counts changed')
    if not review['prior_runs']:
        raise RuntimeError('Stage5C fixture group unavailable')
    group = next((run for run in review['prior_runs']
                  if {row['transaction_id'] for row in run['transactions']} == {6, 7, 8}), None)
    if group is None:
        raise RuntimeError('Expected committed Stage5C group unavailable')
    db = v1.connection()
    try:
        accounts = sorted(group['wallet_balances'])
        people = {r['account_number']: r for r in db.execute(
            'SELECT id,account_number,role FROM users WHERE account_number IN (?,?,?)',
            (accounts[0], accounts[1], 'S5C' + group['fixture_run'] + 'S')).fetchall()}
        if set(people) != set(accounts) | {'S5C' + group['fixture_run'] + 'S'}:
            raise RuntimeError('Stage5C customer/staff identities changed')
        keys = [row['request_id'] for row in group['transactions']]
        if len(keys) != len(set(keys)):
            raise RuntimeError('Stage5C request IDs duplicated')
    finally:
        db.rollback()
        db.close()
    app = load_test_application()
    module = sys.modules['stage4sa_server']
    client = app.test_client()
    with client.session_transaction() as session:
        session['user_id'] = people[accounts[0]]['id']
    customer_dashboard = client.get('/compliance').status_code
    customer_api = client.get('/api/v4-shadow/results').status_code
    customer_socket = module.socketio.test_client(app, flask_test_client=client)
    try:
        customer_subscribe = customer_socket.emit('v4_shadow_subscribe', callback=True)
    finally:
        customer_socket.disconnect()
    with client.session_transaction() as session:
        session['user_id'] = people['S5C' + group['fixture_run'] + 'S']['id']
    staff_dashboard = client.get('/compliance').status_code
    staff_api = client.get('/api/v4-shadow/results').status_code
    staff_socket = module.socketio.test_client(app, flask_test_client=client)
    try:
        staff_subscribe = staff_socket.emit('v4_shadow_subscribe', callback=True)
        staff_socket.get_received()
        broker = app.extensions['realtime_broker']
        broker._local_deliver('transaction', {'test_only': True})
        staff_broadcast = any(item['name'] == 'transaction'
                              for item in staff_socket.get_received())
    finally:
        staff_socket.disconnect()
    if (customer_dashboard not in (302, 303) or customer_api != 403 or
            customer_subscribe != {'ok': False} or staff_dashboard != 200 or
            staff_api != 200 or staff_subscribe != {'ok': True} or not staff_broadcast):
        raise RuntimeError('Stage5C staff/customer authorization failed')
    result = {'status': 'READ_ONLY_PASS', 'counts': counts,
              'wallet_balances': group['wallet_balances'],
              'request_ids_unique': True, 'history': 'COMPLETE_VERIFIED',
              'authorization': {'customer_dashboard_http': customer_dashboard,
                                'customer_api_http': customer_api,
                                'customer_socket_subscribe': customer_subscribe,
                                'staff_dashboard_http': staff_dashboard,
                                'staff_api_http': staff_api,
                                'staff_socket_subscribe': staff_subscribe,
                                'staff_received_test_event': staff_broadcast},
              'historical_notifications': 'UNAVAILABLE_FROM_SAVED_EVIDENCE',
              'suspicious_v4_prediction': 'NOT_OBSERVED'}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    try:
        print(json.dumps(run(), sort_keys=True))
    except Exception as exc:
        print('Stage5C read-only finish stopped: ' + type(exc).__name__)
        raise SystemExit(1)
