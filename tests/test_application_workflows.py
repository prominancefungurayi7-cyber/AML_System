"""Exercise real Flask and Socket.IO routes using a disposable SQLite file."""
from verification_codes import VerificationCodes
from werkzeug.security import check_password_hash
import pytest


def client_for(module, username):
    db = module.connect_db()
    user = db.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
    db.close()
    client = module.app.test_client()
    with client.session_transaction() as state:
        state.update(user_id=user['id'], username=username, role=user['role'],
                     auth_token=module.auth_sessions.create(user['id'], 1800))
    return client


@pytest.mark.parametrize('kind', ['private', 'staff', 'audit'])
def test_revoked_and_expired_sockets_receive_no_private_or_staff_data(aml_app, kind):
    m = aml_app
    username = 'demo' if kind == 'private' else 'Compliance'
    clients = [client_for(m, username) for _ in range(3)]
    sockets = [m.socketio.test_client(m.app, flask_test_client=c) for c in clients]
    try:
        if kind == 'audit':
            for sock in sockets:
                assert sock.emit('v4_shadow_subscribe', callback=True) == {'ok': True}
        for sock in sockets:
            sock.get_received()
        with clients[0].session_transaction() as state:
            m.auth_sessions.revoke(state['auth_token'])
        with clients[1].session_transaction() as state:
            token = state['auth_token']
        uid, _ = m.auth_sessions.local[token]
        m.auth_sessions.local[token] = (uid, 0)
        broker = m.app.extensions['realtime_broker']
        if kind == 'private':
            broker.publish_private(username, 'balance', {'balance': 123})
            expected = 'balance'
        elif kind == 'staff':
            broker.publish('transaction', {'id': 123})
            expected = 'transaction'
        else:
            from v4_shadow import publish_staff
            publish_staff(m.connect_db, m.socketio, {'transaction_id': '123'})
            expected = 'v4_shadow_result'
        assert not sockets[0].is_connected()
        assert not sockets[1].is_connected()
        assert sockets[2].is_connected()
        assert [event['name'] for event in sockets[2].get_received()] == [expected]
    finally:
        for sock in sockets:
            if sock.is_connected():
                sock.disconnect()


def test_expired_staff_cannot_subscribe_and_rejected_messages_acknowledge(aml_app):
    m = aml_app
    staff, customer = client_for(m, 'Compliance'), client_for(m, 'demo')
    ss = m.socketio.test_client(m.app, flask_test_client=staff)
    cs = m.socketio.test_client(m.app, flask_test_client=customer)
    try:
        for data, reason in [({}, 'Missing'), ({'receiver': 'missing-user', 'content': 'Hi'}, 'Recipient'),
                             ({'receiver': 'demo', 'content': 'Hi'}, 'another')]:
            result = cs.emit('send_message', data, callback=True)
            assert result['status'] == 'error'
            assert reason.lower() in result['message'].lower()
        with staff.session_transaction() as state:
            m.auth_sessions.revoke(state['auth_token'])
        assert ss.emit('v4_shadow_subscribe', callback=True) == {'ok': False}
        assert not ss.is_connected()
        db = m.connect_db()
        assert db.execute('SELECT COUNT(*) n FROM messages').fetchone()['n'] == 0
        db.close()
    finally:
        for sock in (ss, cs):
            if sock.is_connected():
                sock.disconnect()


@pytest.mark.parametrize('revoke', ['session', 'role'])
def test_open_staff_stream_stops_before_delivering_after_access_revoked(aml_app, revoke):
    m = aml_app
    client = client_for(m, 'Compliance')
    response = client.get('/stream', buffered=False)
    try:
        assert response.status_code == 200
        if revoke == 'session':
            with client.session_transaction() as state:
                m.auth_sessions.revoke(state['auth_token'])
        else:
            db = m.connect_db()
            db.execute("UPDATE users SET role='customer' WHERE username='Compliance'")
            db.commit()
            db.close()
        m.app.extensions['realtime_broker'].publish('transaction', {'id': 'private'})
        assert b'private' not in b''.join(response.response)
        assert not m.app.extensions['realtime_broker']._subscribers
    finally:
        response.close()
    assert not m.app.config['ACTIVE_STREAMS']


def test_stream_limit_and_cleanup_allow_reconnection(aml_app):
    m = aml_app
    client = client_for(m, 'Compliance')
    responses = [client.get('/stream', buffered=False) for _ in range(3)]
    try:
        assert all(r.status_code == 200 for r in responses)
        assert client.get('/stream').status_code == 429
        responses.pop().close()
        responses.append(client.get('/stream', buffered=False))
        assert responses[-1].status_code == 200
    finally:
        for response in responses:
            response.close()
    assert not m.app.config['ACTIVE_STREAMS']
    assert not m.app.extensions['realtime_broker']._subscribers


def test_private_message_delivery_unread_history_and_multiple_tabs(aml_app):
    m = aml_app
    sender = client_for(m, 'demo')
    recipient = client_for(m, 'Compliance')
    outsider = client_for(m, 'Admin')
    sockets = [m.socketio.test_client(m.app, flask_test_client=c) for c in (sender, recipient, outsider, sender)]
    try:
        for socket in sockets:
            socket.get_received()
        for text in ('First message', 'Second message'):
            result = sockets[0].emit('send_message', {'receiver': 'Compliance', 'content': text}, callback=True)
            assert result['status'] == 'success', result
            assert result['message']['content'] == text
        cid = result['message']['conversation_id']
        assert recipient.get('/api/unread-count').json['unread']['total_unread'] == 2
        assert len([x for x in sockets[1].get_received() if x['name'] == 'new_message']) == 2
        assert not any(x['name'] == 'new_message' for x in sockets[2].get_received())
        history = sender.get(f'/api/conversations/{cid}/messages').json['messages']
        assert [x['content'] for x in history] == ['Second message', 'First message']
        assert all(x['status'] == 'sent' for x in history)
        latest_id = history[0]['id']
        assert sockets[2].emit('message_received', {'message_id': latest_id}, callback=True)['status'] == 'error'
        assert sockets[1].emit('message_received', {'message_id': latest_id}, callback=True)['status'] == 'success'
        delivered = sender.get(f'/api/conversations/{cid}/messages').json['messages']
        assert delivered[0]['status'] == 'delivered' and delivered[1]['status'] == 'sent'
        assert any(x['name'] == 'message_status' and x['args'][0]['status'] == 'delivered'
                   for x in sockets[0].get_received())
        assert outsider.get(f'/api/conversations/{cid}/messages').status_code == 403
        sockets[0].emit('typing', {'conversation_id': cid})
        assert any(x['name'] == 'user_typing' for x in sockets[1].get_received())
        assert not any(x['name'] == 'user_typing' for x in sockets[2].get_received())
        sockets[2].emit('typing', {'conversation_id': cid})
        assert not any(x['name'] == 'user_typing' for x in sockets[1].get_received())
        sockets[1].emit('mark_read', {'conversation_id': cid}, callback=True)
        assert recipient.get('/api/unread-count').json['unread']['total_unread'] == 0
        assert all(x['status'] == 'read' for x in sender.get(f'/api/conversations/{cid}/messages').json['messages'])
        sockets[0].disconnect()
        assert recipient.get('/api/user-status/demo').json['user_status']['is_online']
        sockets[3].disconnect()
        assert not recipient.get('/api/user-status/demo').json['user_status']['is_online']
        # Compliance must also be able to reply to an administrator.
        sent = sockets[2].emit('send_message', {'receiver': 'Compliance', 'content': 'Admin request'}, callback=True)
        assert sent['status'] == 'success'
        replied = sockets[1].emit('send_message', {'receiver': 'Admin', 'content': 'Reply'}, callback=True)
        assert replied['status'] == 'success'
    finally:
        for socket in sockets:
            if socket.is_connected():
                socket.disconnect()


def test_message_failure_rolls_back_every_message_record(aml_app, monkeypatch):
    import messaging
    db = aml_app.connect_db()
    cid = messaging.get_or_create_conversation(db, 'demo', 'Compliance')['id']
    execute = db.execute
    def injected(sql, params=()):
        if sql.startswith('INSERT INTO unread_messages'):
            raise RuntimeError('Injected unread-write failure')
        return execute(sql, params)
    monkeypatch.setattr(db, 'execute', injected)
    try:
        messaging.send_message(db, cid, 'demo', 'Compliance', 'Must roll back', 'customer')
        raise AssertionError('Failure was swallowed')
    except RuntimeError as exc:
        assert 'Injected' in str(exc)
    assert execute('SELECT COUNT(*) AS n FROM messages').fetchone()['n'] == 0
    assert execute('SELECT last_message_id FROM conversations WHERE id=?', (cid,)).fetchone()['last_message_id'] is None
    db.close()


def test_message_history_cursor_and_seed_preservation(aml_app):
    import messaging
    db = aml_app.connect_db()
    cid = messaging.get_or_create_conversation(db, 'demo', 'Compliance')['id']
    for i in range(55):
        messaging.send_message(db, cid, 'demo', 'Compliance', f'Message {i}', 'customer')
    client = client_for(aml_app, 'demo')
    first = client.get(f'/api/conversations/{cid}/messages').json['messages']
    second = client.get(f'/api/conversations/{cid}/messages?before_id={first[-1]["id"]}').json['messages']
    assert len(first) == 50 and len(second) == 5
    assert len({x['id'] for x in first + second}) == 55
    db.execute("UPDATE users SET password_hash='changed-hash', kyc_status='pending_edd' WHERE username='demo'")
    db.commit()
    aml_app.seed_demo_data()
    user = db.execute("SELECT password_hash, kyc_status FROM users WHERE username='demo'").fetchone()
    assert tuple(user) == ('changed-hash', 'pending_edd')
    db.close()


def test_reset_code_is_server_side_single_use_and_email_failure_clears_it(aml_app, monkeypatch):
    m = aml_app
    existing_client = client_for(m, 'demo')
    delivered = []
    monkeypatch.setattr(m, 'send_otp_email_async', lambda email, code: delivered.append(code) or True)
    client = m.app.test_client()
    assert client.post('/forgot-password', data={'email': 'demo@example.com'}).status_code == 302
    with client.session_transaction() as state:
        original = dict(state['password_reset'])
        assert 'token' not in original and delivered[-1] not in str(original)
    response = client.post('/reset-password', data={'reset_code': delivered[-1], 'new_password': 'New-demo-test1!', 'confirm_password': 'New-demo-test1!'})
    assert response.status_code == 302
    assert existing_client.get('/api/unread-count').status_code == 401
    with client.session_transaction() as state:
        state['password_reset'] = original
    client.post('/reset-password', data={'reset_code': delivered[-1], 'new_password': 'Replayed-password1!', 'confirm_password': 'Replayed-password1!'})
    db = m.connect_db()
    row = db.execute("SELECT password_hash FROM users WHERE username='demo'").fetchone()
    assert check_password_hash(row['password_hash'], 'New-demo-test1!')
    db.close()
    monkeypatch.setattr(m, 'send_otp_email_async', lambda *args: False)
    client.post('/forgot-password', data={'email': 'demo@example.com'})
    with client.session_transaction() as state:
        assert 'password_reset' not in state


def test_verification_codes_expire_limit_attempts_and_cannot_be_reused():
    store = VerificationCodes()
    challenge, code = store.issue('reset')
    for _ in range(5):
        assert not store.consume(challenge, 'reset', 'wrong')
    assert not store.consume(challenge, 'reset', code)
    challenge, code = store.issue('reset')
    assert store.consume(challenge, 'reset', code)
    assert not store.consume(challenge, 'reset', code)
    expired = VerificationCodes(ttl=-1)
    challenge, code = expired.issue('reset')
    assert not expired.consume(challenge, 'reset', code)


def test_origin_parser_fails_closed(aml_app):
    assert not aml_app._socket_origin_allowed('https://broken.trycloudflare.com:bad', {'REMOTE_ADDR': '127.0.0.1'})
    assert not aml_app._socket_origin_allowed('https://other.trycloudflare.com', {'REMOTE_ADDR': '127.0.0.1', 'HTTP_HOST': 'expected.trycloudflare.com'})


def test_admin_controls_and_report_submission(aml_app):
    m = aml_app
    admin = client_for(m, 'Admin')
    customer = client_for(m, 'demo')
    db = m.connect_db()
    uid = db.execute("SELECT id FROM users WHERE username='demo'").fetchone()['id']
    assert customer.post('/admin', data={'action': 'update_role', 'user_id': uid, 'kyc_status': 'verified'}).status_code == 302
    assert admin.post('/admin', data={'action': 'update_role', 'user_id': uid, 'kyc_status': 'invalid'}).status_code == 400
    assert admin.post('/admin', data={'action': 'update_role', 'user_id': uid, 'kyc_status': 'pending_edd'}).status_code == 302
    assert db.execute('SELECT kyc_status FROM users WHERE id=?', (uid,)).fetchone()['kyc_status'] == 'pending_edd'
    assert admin.post('/admin', data={'action': 'add_watchlist', 'wl_name': 'Offline fixture', 'wl_type': 'pep', 'wl_reason': 'Fixture only'}).status_code == 302
    assert db.execute("SELECT COUNT(*) n FROM watchlist WHERE name='Offline fixture'").fetchone()['n'] == 1
    db.execute("INSERT INTO transactions (sender_account, receiver_account, amount, transaction_type) VALUES ('ACC1003','ACC1000',1,'transfer')")
    db.execute("INSERT INTO alerts (transaction_id, account_number, risk_score, risk_level, reason) VALUES (1,'ACC1003',80,'suspicious','Fixture only')")
    db.commit()
    assert admin.post('/compliance/alert/1', data={'action': 'file_sar', 'sar_narrative': 'Fixture only'}).status_code == 302
    sid = db.execute('SELECT id FROM sar_reports WHERE alert_id=1').fetchone()['id']
    assert admin.post(f'/compliance/sar/{sid}/submit').status_code == 302
    filed_at = db.execute('SELECT filed_at FROM sar_reports WHERE id=?', (sid,)).fetchone()['filed_at']
    assert admin.post(f'/compliance/sar/{sid}/submit').status_code == 302
    assert db.execute('SELECT filed_at FROM sar_reports WHERE id=?', (sid,)).fetchone()['filed_at'] == filed_at
    assert admin.post('/compliance/sar/999999/submit').status_code == 404
    with m.app.app_context():
        assert m._stats_payload(db)['filed_sars'] == 1
    db.close()


def test_registration_establishes_messaging_session(aml_app, monkeypatch):
    delivered = []
    monkeypatch.setattr(aml_app, 'send_otp_email_async', lambda email, code: delivered.append(code) or True)
    client = aml_app.app.test_client()
    response = client.post('/register', data={'username': 'fixture_customer', 'email': 'fixture@example.invalid',
                                            'id_number': '08-995728P34', 'password': 'Fixture-password1!'})
    assert response.status_code == 200 and len(delivered) == 1
    with client.session_transaction() as state:
        assert 'otp' not in state['pending_registration']
    assert client.post('/register', data={'otp': delivered[0]}).status_code == 302
    with client.session_transaction() as state:
        assert state['username'] == 'fixture_customer'
    assert client.get('/api/conversations').status_code == 200
    contacts = client.get('/api/messageable-users').json['users']
    assert any(user['role'] == 'compliance' for user in contacts)
    assert all(user['username'] != 'fixture_customer' for user in contacts)


def test_email_transport_handles_windows_console_and_smtp_modes(monkeypatch):
    import io
    import sys
    import utils
    from unittest.mock import MagicMock
    monkeypatch.setenv('SMTP_EMAIL', 'fixture@example.invalid')
    monkeypatch.setenv('SMTP_PASSWORD', 'fixture-only')
    console = io.TextIOWrapper(io.BytesIO(), encoding='cp1252', errors='strict')
    monkeypatch.setattr(sys, 'stdout', console)
    for port, name in (('587', 'SMTP'), ('465', 'SMTP_SSL')):
        transport = MagicMock()
        monkeypatch.setattr(utils.smtplib, name, transport)
        monkeypatch.setenv('SMTP_PORT', port)
        assert utils.send_email('fixture@mailer-fixture.org', 'Verification', 'Verification code')
        transport.return_value.__enter__.return_value.send_message.assert_called_once()
        assert transport.return_value.__enter__.return_value.starttls.call_count == (port != '465')
    monkeypatch.setenv('SMTP_PORT', 'invalid')
    assert utils.send_email('fixture@mailer-fixture.org', 'Verification', 'Code') is False


def test_admin_kyc_returns_saved_status(aml_app):
    m = aml_app
    admin = client_for(m, 'Admin')
    db = m.connect_db()
    user = db.execute("SELECT id FROM users WHERE username='demo'").fetchone()
    db.close()
    response = admin.post('/admin', data={'action': 'update_role', 'user_id': user['id'], 'kyc_status': 'pending_edd'}, headers={'Accept': 'application/json'})
    assert response.status_code == 200
    assert response.json['user']['kyc_status'] == 'pending_edd'
    db = m.connect_db()
    assert db.execute('SELECT kyc_status FROM users WHERE id=?', (user['id'],)).fetchone()['kyc_status'] == 'pending_edd'
    db.close()
    assert client_for(m, 'demo').post('/admin', data={'action': 'update_role', 'user_id': user['id'], 'kyc_status': 'verified'}).status_code == 302
    db = m.connect_db()
    assert db.execute('SELECT kyc_status FROM users WHERE id=?', (user['id'],)).fetchone()['kyc_status'] == 'pending_edd'
    db.close()
