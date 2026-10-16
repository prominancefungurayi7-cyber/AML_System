import pytest
from werkzeug.security import generate_password_hash


@pytest.mark.parametrize('username,use_email', [('demo', True), ('demo', False)])
def test_login_otp_and_idle_expiry(aml_app, monkeypatch, username, use_email):
    m = aml_app
    db = m.connect_db()
    db.execute("UPDATE users SET email='customer@real-mail.test' WHERE username='demo'")
    db.execute('UPDATE users SET password_hash=? WHERE username=?', (generate_password_hash('TestPassword123!'), username))
    db.commit()
    user = db.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
    db.close()
    sent = []
    monkeypatch.setattr(m, 'send_otp_email_async', lambda email, code: sent.append((email, code)) or True)
    client = m.app.test_client()
    response = client.post('/login', data={'login': user['email'] if use_email else username, 'password': 'TestPassword123!'})
    assert response.status_code == 200
    assert b'Verification code' in response.data
    assert sent[0][0] == user['email']
    with client.session_transaction() as state:
        assert 'user_id' not in state
    client.post('/login', data={'otp': '000000'})
    with client.session_transaction() as state:
        assert 'user_id' not in state
    assert client.post('/login', data={'otp': sent[0][1]}).status_code == 302
    with client.session_transaction() as state:
        token = state['auth_token']
        assert state['user_id'] == user['id']
    expiry = m.auth_sessions.local[token][1]
    assert client.get('/api/unread-count').status_code == 200
    assert m.auth_sessions.local[token][1] == expiry
    socket = m.socketio.test_client(m.app, flask_test_client=client)
    assert socket.is_connected()
    m.auth_sessions.local[token] = (str(user['id']), 0)
    socket.emit('heartbeat')
    assert not socket.is_connected()
    assert client.get('/api/unread-count').status_code == 401
    with client.session_transaction() as state:
        assert 'user_id' not in state
    client.post('/login', data={'otp': sent[0][1]})
    with client.session_transaction() as state:
        assert 'user_id' not in state


def test_wrong_password_and_failed_email_never_authenticate(aml_app, monkeypatch):
    m = aml_app
    sent = []
    monkeypatch.setattr(m, 'send_otp_email_async', lambda *args: sent.append(args) or False)
    client = m.app.test_client()
    client.post('/login', data={'login': 'demo', 'password': 'incorrect'})
    assert not sent
    db = m.connect_db()
    db.execute("UPDATE users SET email='customer@real-mail.test' WHERE username='demo'")
    db.execute('UPDATE users SET password_hash=? WHERE username=?', (generate_password_hash('TestPassword123!'), 'demo'))
    db.commit()
    db.close()
    client.post('/login', data={'login': 'demo', 'password': 'TestPassword123!'})
    assert len(sent) == 1
    with client.session_transaction() as state:
        assert 'user_id' not in state and 'pending_login' not in state


def test_sessions_touch_expire_and_revoke(monkeypatch):
    import auth_sessions
    clock = [1000]
    monkeypatch.setattr(auth_sessions.time, 'time', lambda: clock[0])
    sessions = auth_sessions.AuthSessions()
    token = sessions.create(1, 1800)
    clock[0] += 1700
    assert sessions.valid(token, 1, 1800, touch=True)
    assert not sessions.valid(token, 2, 1800)
    clock[0] += 1801
    assert not sessions.valid(token, 1, 1800, touch=True)
    token = sessions.create(1, 1800)
    sessions.revoke(token)
    assert not sessions.valid(token, 1, 1800)


@pytest.mark.parametrize('username', ['Admin', 'Compliance', 'demo', 'user_low_1'])
def test_seeded_accounts_password_only_and_no_idle_expiry(aml_app, monkeypatch, username):
    m = aml_app
    assert m.app.config['AUTH_IDLE_SECONDS'] == 3600
    db = m.connect_db()
    db.execute('UPDATE users SET password_hash=? WHERE username=?', (generate_password_hash('TestPassword123!'), username))
    db.commit()
    db.close()
    def no_email(*args):
        raise AssertionError('Seeded accounts must not send OTP')
    monkeypatch.setattr(m, 'send_otp_email_async', no_email)
    client = m.app.test_client()
    client.post('/login', data={'login': username, 'password': 'incorrect'})
    with client.session_transaction() as state:
        assert 'user_id' not in state
    result = client.post('/login', data={'login': username, 'password': 'TestPassword123!'})
    assert result.status_code == 302
    with client.session_transaction() as state:
        assert state['idle_exempt'] is True
        token, uid = state['auth_token'], state['user_id']
    assert m.auth_sessions.local[token][1] == float('inf')
    assert client.get('/api/unread-count').status_code == 200
    client.get('/logout')
    assert not m.auth_sessions.valid(token, uid, None)
