"""Real routes/receipts with temporary SQLite and private files; no live effects."""
import io
import uuid

from PIL import Image
import pytest

from message_attachments import MAX_FILE_SIZE, PREFIX, decode_message


def signed_in(module, name):
    db = module.connect_db()
    user = db.execute('SELECT * FROM users WHERE username=?', (name,)).fetchone()
    db.close()
    client = module.app.test_client()
    with client.session_transaction() as session:
        session.update(user_id=user['id'], username=name, role=user['role'],
                       auth_token=module.auth_sessions.create(user['id'], 1800),
                       message_attachment_csrf='fixture-csrf')
    return client


@pytest.fixture
def messaging_app(aml_app, tmp_path):
    aml_app.app.config['MESSAGE_ATTACHMENT_ROOT'] = str(tmp_path / 'private-files')
    return aml_app


def send(client, *, name='evidence.txt', body=b'Evidence', receiver='Compliance', content='', key=None, csrf='fixture-csrf'):
    return client.post('/api/message-attachments', data={
        'receiver': receiver, 'content': content, 'csrf_token': csrf,
        'client_request_id': key or str(uuid.uuid4()), 'file': (io.BytesIO(body), name)},
        content_type='multipart/form-data')


def png():
    stream = io.BytesIO()
    Image.new('RGB', (16, 12), 'white').save(stream, 'PNG')
    return stream.getvalue()


@pytest.mark.parametrize('size', [128 * 1024, 20 * 1024 * 1024])
def test_multipart_files_over_one_chunk_up_to_20mb_are_accepted(messaging_app, size):
    client = signed_in(messaging_app, 'demo')
    body = b'x' * size
    response = send(client, name='evidence.txt', body=body)
    assert response.status_code == 200, response.json
    attachment = response.json['message']['attachment']
    assert attachment['size'] == size
    assert client.get(attachment['url']).data == body


def test_file_over_20mb_rejected_without_message_or_file(messaging_app):
    client = signed_in(messaging_app, 'demo')
    before = rows(messaging_app)
    response = send(client, body=b'x' * (20 * 1024 * 1024 + 1))
    assert response.status_code in (400, 413)
    assert '20 MB' in response.json['message']
    assert rows(messaging_app) == before
    assert not files(messaging_app)


def test_screenshot_larger_than_multipart_chunk_uploads(messaging_app):
    import random
    stream = io.BytesIO()
    Image.frombytes('RGB', (300, 300), random.Random(7).randbytes(300 * 300 * 3)).save(stream, 'PNG')
    body = stream.getvalue()
    assert len(body) > 65536
    client = signed_in(messaging_app, 'demo')
    response = send(client, name='screenshot.png', body=body)
    assert response.status_code == 200, response.json
    attachment = response.json['message']['attachment']
    assert client.get(attachment['preview_url']).data == body


def rows(module):
    db = module.connect_db()
    result = db.execute('SELECT COUNT(*) n FROM messages').fetchone()['n']
    db.close()
    return result


def files(module):
    return list(module._attachment_root().glob('*'))


def test_images_persist_and_use_private_realtime_history_and_receipts(messaging_app):
    m = messaging_app
    sender, recipient, outsider = [signed_in(m, name) for name in ('demo', 'Compliance', 'Admin')]
    sockets = [m.socketio.test_client(m.app, flask_test_client=c) for c in (sender, recipient, outsider)]
    try:
        for socket in sockets:
            socket.get_received()
        image = png()
        response = send(sender, name='case evidence.png', body=image, content='Screenshot of the transfer')
        assert response.status_code == 200, response.json
        message = response.json['message']
        assert message['content'] == 'Screenshot of the transfer'
        attachment = message['attachment']
        assert attachment['name'] == 'case_evidence.png'
        assert set(attachment) == {'name', 'size', 'media_type', 'url', 'preview_url'}
        delivered = [e['args'][0] for e in sockets[1].get_received() if e['name'] == 'new_message']
        assert delivered == [message]
        assert not any(e['name'] == 'new_message' for e in sockets[2].get_received())
        assert PREFIX not in response.get_data(as_text=True)
        assert sender.get(attachment['url']).data == image
        preview = recipient.get(attachment['preview_url'])
        assert preview.status_code == 200 and preview.data == image
        assert preview.headers['Content-Disposition'].startswith('inline;')
        assert preview.headers['Cache-Control'] == 'private, no-store'
        assert preview.headers['X-Content-Type-Options'] == 'nosniff'
        assert outsider.get(attachment['url']).status_code == 403
        anonymous = m.app.test_client().get(attachment['url'])
        assert anonymous.status_code == 302 and '/login' in anonymous.headers['Location']
        history = recipient.get(f"/api/conversations/{message['conversation_id']}/messages").json['messages']
        assert history[0]['attachment'] == attachment and history[0]['content'] == message['content']
        assert sockets[1].emit('message_received', {'message_id': message['id']}, callback=True)['status'] == 'success'
        sockets[1].emit('mark_read', {'conversation_id': message['conversation_id']}, callback=True)
        assert sender.get(f"/api/conversations/{message['conversation_id']}/messages").json['messages'][0]['status'] == 'read'
        assert recipient.get('/api/unread-count').json['unread']['total_unread'] == 0
    finally:
        for socket in sockets:
            if socket.is_connected():
                socket.disconnect()


def test_attachment_only_file_preview_and_admin_compliance_delivery(messaging_app):
    m = messaging_app
    sender, recipient = signed_in(m, 'Compliance'), signed_in(m, 'Admin')
    response = send(sender, receiver='Admin', name='evidence.csv', body=b'wallet,amount\nACC1,10\n')
    assert response.status_code == 200
    message = response.json['message']
    assert message['content'] == ''
    assert 'preview_url' not in message['attachment']
    downloaded = recipient.get(message['attachment']['url'] + '?inline=1')
    assert downloaded.status_code == 200
    assert downloaded.headers['Content-Disposition'].startswith('attachment;')
    assert recipient.get('/api/conversations').json['conversations'][0]['content'] == 'evidence.csv'


def test_upload_retry_reuses_message_and_file_without_unread_increment(messaging_app):
    m = messaging_app
    sender, recipient = signed_in(m, 'demo'), signed_in(m, 'Compliance')
    key = str(uuid.uuid4())
    first = send(sender, key=key)
    second = send(sender, key=key)
    assert first.status_code == second.status_code == 200
    assert first.json['message']['id'] == second.json['message']['id']
    assert rows(m) == len(files(m)) == 1
    assert recipient.get('/api/unread-count').json['unread']['total_unread'] == 1
    conflicting = send(sender, key=key, body=b'Changed evidence')
    assert conflicting.status_code == 409
    assert rows(m) == len(files(m)) == 1
    assert recipient.get(first.json['message']['attachment']['url']).data == b'Evidence'


@pytest.mark.parametrize('changes,status', [({'receiver': 'demo'}, 403), ({'csrf': 'wrong'}, 403),
    ({'name': 'run.exe'}, 400), ({'name': 'evidence.png', 'body': b'not an image'}, 400),
    ({'key': 'invalid-key'}, 400), ({'body': b''}, 400), ({'content': 'x' * 10001}, 400)])
def test_invalid_or_unauthorized_uploads_create_no_messages_or_files(messaging_app, changes, status):
    m = messaging_app
    response = send(signed_in(m, 'demo'), **changes)
    assert response.status_code == status, response.json
    assert rows(m) == len(files(m)) == 0


def test_oversized_request_is_json_and_creates_no_message(messaging_app):
    m = messaging_app
    response = send(signed_in(m, 'demo'), body=b'x' * (MAX_FILE_SIZE + 65537))
    assert response.status_code == 413 and response.is_json
    assert rows(m) == len(files(m)) == 0


def test_expired_upload_and_forged_socket_attachment_are_denied(messaging_app):
    m = messaging_app
    client = signed_in(m, 'demo')
    socket = m.socketio.test_client(m.app, flask_test_client=client)
    try:
        result = socket.emit('send_message', {'receiver': 'Compliance', 'content': PREFIX + '{}'}, callback=True)
        assert result['status'] == 'error'
        with client.session_transaction() as session:
            m.auth_sessions.revoke(session['auth_token'])
        assert send(client).status_code == 401
        assert rows(m) == len(files(m)) == 0
    finally:
        if socket.is_connected():
            socket.disconnect()


def test_deleted_corrupted_and_no_longer_authorized_downloads_are_denied(messaging_app):
    m = messaging_app
    sender, recipient = signed_in(m, 'demo'), signed_in(m, 'Compliance')
    message = send(sender).json['message']
    db = m.connect_db()
    raw = db.execute('SELECT content FROM messages WHERE id=?', (message['id'],)).fetchone()['content']
    _, metadata = decode_message(raw)
    path = m._attachment_root() / metadata['id']
    path.write_bytes(b'Tampered')
    assert recipient.get(message['attachment']['url']).status_code == 404
    path.write_bytes(b'Evidence')
    db.execute("UPDATE users SET role='disabled' WHERE username='Compliance'")
    db.commit()
    assert sender.get(message['attachment']['url']).status_code == 403
    db.execute("UPDATE users SET role='compliance' WHERE username='Compliance'")
    db.execute('UPDATE messages SET deleted_at=CURRENT_TIMESTAMP WHERE id=?', (message['id'],))
    db.commit()
    assert recipient.get(message['attachment']['url']).status_code == 403
    db.close()


def test_database_failure_rolls_back_unread_and_cleans_unreferenced_file(messaging_app, monkeypatch):
    m = messaging_app
    import messaging
    def failed(*args, **kwargs):
        raise RuntimeError('Injected persistence failure')
    monkeypatch.setattr(messaging, 'add_unread_message', failed)
    response = send(signed_in(m, 'demo'))
    assert response.status_code == 503
    assert rows(m) == len(files(m)) == 0


def test_broker_failure_after_commit_keeps_message_download_and_returns_success(messaging_app, monkeypatch):
    m = messaging_app
    sender = signed_in(m, 'demo')
    def failed(*args, **kwargs):
        raise RuntimeError('Injected broker failure')
    monkeypatch.setattr(m, 'emit_private_message_event', failed)
    response = send(sender)
    assert response.status_code == 200
    assert rows(m) == len(files(m)) == 1
    assert sender.get(response.json['message']['attachment']['url']).data == b'Evidence'


def test_lost_commit_acknowledgement_retains_saved_file_and_message(messaging_app, monkeypatch):
    m = messaging_app
    sender = signed_in(m, 'demo')
    original = m.send_message
    def committed(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError('Commit succeeded but response was lost')
    monkeypatch.setattr(m, 'send_message', committed)
    response = send(sender)
    assert response.status_code == 200
    assert rows(m) == len(files(m)) == 1
    assert sender.get(response.json['message']['attachment']['url']).data == b'Evidence'
