"""Registered-user communication; all SQL, messages and files are disposable."""
import io
import uuid

import pytest


def signed_in(module, username):
    db = module.connect_db()
    user = db.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
    db.close()
    client = module.app.test_client()
    with client.session_transaction() as state:
        state.update(user_id=user['id'], username=username, role=user['role'],
                     auth_token=module.auth_sessions.create(user['id'], 1800),
                     message_attachment_csrf='directory-test-csrf')
    return client


def add_unsupported_account(module):
    db = module.connect_db()
    db.execute("INSERT INTO users (username,email,id_number,password_hash,role,account_number,balance) "
               "VALUES (?,?,?,?,?,?,?)", ('not_a_contact', 'private@example.invalid', 'TEST-NOT-CONTACT',
                                          'not-a-real-password-hash', 'auditor', 'EXCLUDED999', 1))
    db.commit()
    db.close()


@pytest.mark.parametrize('sender_role,receiver_role,allowed', [
    ('customer', 'customer', True), ('customer', 'compliance', True),
    ('compliance', 'customer', True), ('compliance', 'admin', True),
    ('admin', 'compliance', True), ('compliance', 'compliance', True),
    ('admin', 'admin', True), ('customer', 'admin', False), ('admin', 'customer', False),
    ('auditor', 'compliance', False), ('customer', 'auditor', False),
])
def test_messaging_role_policy_is_symmetric_and_restricts_customer_admin(sender_role, receiver_role, allowed):
    from messaging import can_user_message
    assert can_user_message(sender_role, receiver_role)[0] is allowed


@pytest.mark.parametrize('sender,receiver', [
    ('demo', 'user_low_1'), ('user_low_1', 'demo'), ('demo', 'Compliance'),
    ('Compliance', 'demo'), ('Admin', 'Compliance'), ('Compliance', 'Admin'),
])
def test_permitted_roles_can_message_each_other_but_not_themselves(aml_app, sender, receiver):
    m = aml_app
    client = signed_in(m, sender)
    assert client.get(f'/api/users/{receiver}/can-message').json['can_message'] is True
    assert client.get(f'/api/users/{sender}/can-message').json['can_message'] is False
    socket = m.socketio.test_client(m.app, flask_test_client=client)
    try:
        denied = socket.emit('send_message', {'receiver': sender, 'content': 'Self-message'}, callback=True)
        assert denied['status'] == 'error'
        sent = socket.emit('send_message', {'receiver': receiver, 'content': 'Professional inquiry'}, callback=True)
        assert sent['status'] == 'success', sent
        history = client.get(f"/api/conversations/{sent['message']['conversation_id']}/messages")
        assert history.status_code == 200
        assert [message['content'] for message in history.json['messages']] == ['Professional inquiry']
    finally:
        if socket.is_connected():
            socket.disconnect()


@pytest.mark.parametrize('username', ['demo', 'Admin', 'Compliance'])
def test_directory_searches_live_names_and_accounts_without_private_data(aml_app, username):
    m = aml_app
    add_unsupported_account(m)
    client = signed_in(m, username)
    response = client.get('/api/messageable-users')
    assert response.status_code == 200
    users = response.json['users']
    assert users and username not in {user['username'] for user in users}
    assert 'not_a_contact' not in {user['username'] for user in users}
    assert {'customer', 'admin', 'compliance'} >= {user['role'] for user in users}
    if username == 'demo':
        assert all(user['role'] in {'customer', 'compliance'} for user in users)
        assert client.get('/api/messageable-users?q=Admin').json['users'] == []
        assert client.get('/api/messageable-users?q=ACC1001').json['users'] == []
    elif username == 'Admin':
        assert all(user['role'] in {'admin', 'compliance'} for user in users)
        assert client.get('/api/messageable-users?q=user_low_1').json['users'] == []
    for user in users:
        assert set(user) == {'id', 'username', 'role', 'account_number', 'is_online',
                             'last_seen', 'profile_photo_url'}
        assert not any(key in user for key in ('email', 'id_number', 'balance', 'password_hash'))
    contact_name = 'Compliance' if username == 'Admin' else 'user_low_1'
    contact = next(user for user in users if user['username'] == contact_name)
    by_name = client.get('/api/messageable-users', query_string={'q': contact_name.swapcase()}).json['users']
    assert [user['id'] for user in by_name] == [contact['id']]
    by_account = client.get('/api/messageable-users', query_string={
        'q': contact['account_number'].lower()}).json['users']
    assert [user['id'] for user in by_account] == [contact['id']]
    assert client.get('/api/messageable-users?q=unregistered-contact').json['users'] == []
    assert client.get('/api/messageable-users?q=EXCLUDED999').json['users'] == []


@pytest.mark.parametrize('sender,receiver', [('demo', 'Admin'), ('Admin', 'demo')])
def test_customer_admin_direct_messages_are_denied_on_socket_and_file_routes(aml_app, tmp_path, sender, receiver):
    m = aml_app
    m.app.config['MESSAGE_ATTACHMENT_ROOT'] = str(tmp_path / 'private-files')
    client = signed_in(m, sender)
    assert client.get(f'/api/users/{receiver}/can-message').json['can_message'] is False
    socket = m.socketio.test_client(m.app, flask_test_client=client)
    try:
        sent = socket.emit('send_message', {'receiver': receiver, 'content': 'Not permitted'}, callback=True)
        assert sent['status'] == 'error'
        uploaded = client.post('/api/message-attachments', data={
            'receiver': receiver, 'csrf_token': 'directory-test-csrf',
            'client_request_id': str(uuid.uuid4()), 'file': (io.BytesIO(b'Evidence'), 'evidence.txt')},
            content_type='multipart/form-data')
        assert uploaded.status_code == 403
        db = m.connect_db()
        assert db.execute('SELECT COUNT(*) n FROM messages').fetchone()['n'] == 0
        assert db.execute('SELECT COUNT(*) n FROM conversations').fetchone()['n'] == 0
        db.close()
        assert not list(m._attachment_root().glob('*'))
    finally:
        if socket.is_connected():
            socket.disconnect()


@pytest.mark.parametrize('sender,receiver', [('demo', 'Admin'), ('Admin', 'demo')])
def test_retained_customer_admin_history_cannot_be_opened_or_acknowledged(aml_app, sender, receiver):
    from message_attachments import save_upload, encode_message
    from werkzeug.datastructures import FileStorage

    m = aml_app
    db = m.connect_db()
    sender_row = db.execute('SELECT * FROM users WHERE username=?', (sender,)).fetchone()
    conversation = m.get_or_create_conversation(db, sender, receiver)
    metadata = save_upload(FileStorage(stream=io.BytesIO(b'Preserve existing evidence'),
                                      filename='evidence.txt'), m._attachment_root(), uuid.uuid4().hex)
    message = m.send_message(db, conversation['id'], sender, receiver,
                             encode_message('Existing conversation', metadata), sender_row['role'])
    db.close()
    clients = [signed_in(m, name) for name in (sender, receiver)]
    sockets = [m.socketio.test_client(m.app, flask_test_client=client) for client in clients]
    try:
        for socket in sockets:
            socket.get_received()
        for client in clients:
            assert client.get('/api/conversations').json['conversations'] == []
            assert client.get('/api/unread-count').json['unread'] == {
                'total_unread': 0, 'by_conversation': {}}
            assert client.get(f"/api/conversations/{conversation['id']}/messages").status_code == 403
            assert client.get(f"/api/messages/{message['id']}/attachment").status_code == 403
            assert client.get(f"/api/messages/{message['id']}/attachment?inline=1").status_code == 403
        assert sockets[1].emit('message_received', {'message_id': message['id']}, callback=True)['status'] == 'error'
        for socket in sockets:
            assert socket.emit('mark_read', {'conversation_id': conversation['id']}, callback=True)['status'] == 'error'
            socket.emit('typing', {'conversation_id': conversation['id']})
        assert not any(event['name'] in {'user_typing', 'message_status', 'messages_read'}
                       for socket in sockets for event in socket.get_received())
        db = m.connect_db()
        assert db.execute('SELECT COUNT(*) n FROM conversations').fetchone()['n'] == 1
        retained = db.execute('SELECT * FROM messages').fetchall()
        assert len(retained) == 1 and retained[0]['status'] == 'sent'
        assert retained[0]['content'] == encode_message('Existing conversation', metadata)
        assert db.execute('SELECT unread_count FROM unread_messages').fetchone()['unread_count'] == 1
        db.close()
        assert len(list(m._attachment_root().glob('*'))) == 1
    finally:
        for socket in sockets:
            if socket.is_connected():
                socket.disconnect()


def test_directory_and_profiles_require_current_authenticated_session(aml_app):
    m = aml_app
    anonymous = m.app.test_client()
    for path in ('/api/messageable-users', '/api/profile'):
        response = anonymous.get(path)
        assert response.status_code in {302, 401}
        if response.status_code == 302:
            assert '/login' in response.headers['Location']
    for path in ('/api/messageable-users', '/api/profile'):
        client = signed_in(m, 'demo')
        with client.session_transaction() as state:
            m.auth_sessions.revoke(state['auth_token'])
        assert client.get(path).status_code == 401


def test_customer_pair_messages_have_private_durable_history_and_receipts(aml_app):
    m = aml_app
    clients = [signed_in(m, name) for name in ('demo', 'user_low_1', 'Admin')]
    sender, receiver, outsider = clients
    sockets = [m.socketio.test_client(m.app, flask_test_client=client) for client in clients]
    try:
        for socket in sockets:
            socket.get_received()
        message = sockets[0].emit('send_message', {'receiver': 'user_low_1', 'content': 'Case evidence follows'},
                                  callback=True)
        assert message['status'] == 'success', message
        mid = message['message_id']
        cid = message['message']['conversation_id']
        assert any(event['name'] == 'new_message' for event in sockets[1].get_received())
        assert not any(event['name'] == 'new_message' for event in sockets[2].get_received())
        assert receiver.get('/api/unread-count').json['unread']['total_unread'] == 1
        assert outsider.get(f'/api/conversations/{cid}/messages').status_code == 403
        assert outsider.get('/api/conversations').json['conversations'] == []
        assert sockets[2].emit('message_received', {'message_id': mid}, callback=True)['status'] == 'error'
        assert sockets[2].emit('mark_read', {'conversation_id': cid}, callback=True)['status'] == 'error'
        sockets[2].emit('typing', {'conversation_id': cid})
        assert not any(event['name'] == 'user_typing' for event in sockets[1].get_received())
        sockets[0].emit('typing', {'conversation_id': cid})
        assert any(event['name'] == 'user_typing' for event in sockets[1].get_received())
        assert not any(event['name'] == 'user_typing' for event in sockets[2].get_received())
        assert sockets[1].emit('message_received', {'message_id': mid}, callback=True)['status'] == 'success'
        history = sender.get(f'/api/conversations/{cid}/messages').json['messages']
        assert history[0]['status'] == 'delivered'
        assert sockets[1].emit('mark_read', {'conversation_id': cid}, callback=True)['status'] == 'success'
        assert sender.get(f'/api/conversations/{cid}/messages').json['messages'][0]['status'] == 'read'
        reply = sockets[1].emit('send_message', {'receiver': 'demo', 'content': 'Evidence received'}, callback=True)
        assert reply['status'] == 'success' and reply['message']['conversation_id'] == cid
        assert [row['content'] for row in sender.get(f'/api/conversations/{cid}/messages').json['messages']] == [
            'Evidence received', 'Case evidence follows']
        db = m.connect_db()
        assert db.execute('SELECT COUNT(*) n FROM messages').fetchone()['n'] == 2
        db.close()
    finally:
        for socket in sockets:
            if socket.is_connected():
                socket.disconnect()


def test_customer_pair_attachments_remain_private_to_conversation(aml_app, tmp_path):
    m = aml_app
    m.app.config['MESSAGE_ATTACHMENT_ROOT'] = str(tmp_path / 'private-files')
    sender, receiver, outsider = [signed_in(m, name) for name in ('demo', 'user_low_1', 'Compliance')]
    response = sender.post('/api/message-attachments', data={
        'receiver': 'user_low_1', 'content': 'Transaction evidence', 'csrf_token': 'directory-test-csrf',
        'client_request_id': str(uuid.uuid4()), 'file': (io.BytesIO(b'Evidence for this conversation'), 'evidence.txt')},
        content_type='multipart/form-data')
    assert response.status_code == 200, response.json
    message = response.json['message']
    url = message['attachment']['url']
    assert receiver.get(url).data == sender.get(url).data == b'Evidence for this conversation'
    assert outsider.get(url).status_code == 403
    history = receiver.get(f"/api/conversations/{message['conversation_id']}/messages").json['messages']
    assert history[0]['attachment']['url'] == url


def test_unsupported_role_cannot_join_directory_or_message_registered_users(aml_app):
    m = aml_app
    add_unsupported_account(m)
    client = signed_in(m, 'not_a_contact')
    assert client.get('/api/messageable-users').json['users'] == []
    socket = m.socketio.test_client(m.app, flask_test_client=client)
    try:
        result = socket.emit('send_message', {'receiver': 'demo', 'content': 'Not authorized'}, callback=True)
        assert result['status'] == 'error'
        db = m.connect_db()
        assert db.execute('SELECT COUNT(*) n FROM messages').fetchone()['n'] == 0
        db.close()
    finally:
        if socket.is_connected():
            socket.disconnect()
