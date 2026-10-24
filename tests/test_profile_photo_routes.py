"""Profile photos use authenticated routes and disposable private storage."""
import io

from PIL import Image
import pytest

from profile_photos import MAX_PHOTO_SIZE, ProfilePhotoError


def account(module, name):
    db = module.connect_db()
    user = dict(db.execute('SELECT * FROM users WHERE username=?', (name,)).fetchone())
    db.close()
    client = module.app.test_client()
    with client.session_transaction() as session:
        session.update(user_id=user['id'], username=name, role=user['role'],
                       auth_token=module.auth_sessions.create(user['id'], 1800))
    return client, user


def photograph():
    stream = io.BytesIO()
    image = Image.new('RGB', (40, 60), 'navy')
    exif = Image.Exif()
    exif[315] = 'Private camera owner'
    image.save(stream, 'JPEG', exif=exif)
    return stream.getvalue()


def upload(client, *, body=None, name='professional.jpg', csrf=None, **extra):
    token = csrf if csrf is not None else client.get('/api/profile').json['csrf_token']
    return client.post('/api/profile/photo', data={
        'csrf_token': token, 'photo': (io.BytesIO(photograph() if body is None else body), name), **extra},
        content_type='multipart/form-data')


def database_state(module):
    db = module.connect_db()
    state = {table: [tuple(row) for row in db.execute('SELECT * FROM ' + table + ' ORDER BY id').fetchall()]
             for table in ('users', 'transactions', 'messages')}
    db.close()
    return state


def test_messages_page_provides_profile_token_for_immediate_upload(aml_app):
    client, _ = account(aml_app, 'demo')
    page = client.get('/messages')
    assert page.status_code == 200
    with client.session_transaction() as session:
        token = session['profile_photo_csrf']
    assert ('data-profile-photo-csrf="' + token + '"').encode() in page.data
    assert b'data-profile-account="ACC1003"' in page.data
    # No extra GET /api/profile is required before choosing and saving a photo.
    saved = upload(client, csrf=token)
    assert saved.status_code == 200 and saved.json['profile']['profile_photo_url']


def test_photo_upload_realtime_directory_headers_and_remove(aml_app):
    m = aml_app
    owner, user = account(m, 'demo')
    colleague, _ = account(m, 'user_low_1')
    sockets = [m.socketio.test_client(m.app, flask_test_client=c) for c in (owner, colleague)]
    before = database_state(m)
    try:
        for socket in sockets:
            socket.get_received()
        response = upload(owner)
        assert response.status_code == 200, response.json
        profile = response.json['profile']
        assert set(profile) == {'id', 'username', 'role', 'account_number', 'profile_photo_url'}
        assert profile['username'] == 'demo'
        url = profile['profile_photo_url']
        for socket in sockets:
            events = [event['args'][0] for event in socket.get_received() if event['name'] == 'profile_updated']
            assert events == [dict(user_id=user['id'], username='demo', profile_photo_url=url)]
        downloaded = colleague.get(url)
        assert downloaded.status_code == 200 and downloaded.mimetype == 'image/jpeg'
        assert downloaded.headers['Cache-Control'] == 'private, no-store'
        with Image.open(io.BytesIO(downloaded.data)) as image:
            assert image.size == (512, 512) and not image.getexif()
        directory = colleague.get('/api/messageable-users?q=demo').json['users']
        assert directory[0]['profile_photo_url'] == url
        assert url.encode() in owner.get('/messages').data
        token = owner.get('/api/profile').json['csrf_token']
        removed = owner.delete('/api/profile/photo', headers={'X-CSRF-Token': token})
        assert removed.status_code == 200, removed.json
        assert removed.json['profile']['profile_photo_url'] is None
        assert colleague.get(url).status_code == 404
        assert not list(m._profile_photo_root().iterdir())
        assert database_state(m) == before
    finally:
        for socket in sockets:
            if socket.is_connected():
                socket.disconnect()


@pytest.mark.parametrize('changes,status', [({'csrf': 'wrong'}, 403), ({'csrf': '\u2603'}, 403),
    ({'name': 'profile.svg', 'body': b'<svg/>'}, 400), ({'body': b'invalid JPEG'}, 400),
    ({'name': 'profile.png'}, 400), ({'body': b''}, 400),
    ({'body': b'x' * (MAX_PHOTO_SIZE + 65537)}, 413)])
def test_invalid_photo_updates_preserve_existing_photo(aml_app, changes, status):
    client, _ = account(aml_app, 'demo')
    first = upload(client)
    url = first.json['profile']['profile_photo_url']
    original = client.get(url).data
    response = upload(client, **changes)
    assert response.status_code == status and response.is_json
    assert client.get(url).data == original
    assert len(list(aml_app._profile_photo_root().iterdir())) == 1


def test_profile_changes_affect_only_authenticated_owner(aml_app):
    owner, owner_user = account(aml_app, 'demo')
    other, other_user = account(aml_app, 'Admin')
    response = upload(owner, user_id=str(other_user['id']), username='Admin')
    assert response.status_code == 200
    assert response.json['profile']['id'] == owner_user['id']
    assert other.get('/api/profile').json['profile']['profile_photo_url'] is None
    assert owner.delete('/api/profile/photo', headers={'X-CSRF-Token': 'wrong'}).status_code == 403
    assert owner.get(response.json['profile']['profile_photo_url']).status_code == 200


def test_profile_routes_reject_anonymous_expired_and_unsupported_accounts(aml_app):
    m = aml_app
    anonymous = m.app.test_client()
    assert anonymous.get('/api/profile').status_code == 302
    assert anonymous.post('/api/profile/photo').status_code == 302
    client, user = account(m, 'demo')
    with client.session_transaction() as session:
        m.auth_sessions.revoke(session['auth_token'])
    assert client.post('/api/profile/photo').status_code == 401
    client, user = account(m, 'demo')
    db = m.connect_db()
    db.execute("UPDATE users SET role='disabled' WHERE id=?", (user['id'],))
    db.commit()
    db.close()
    assert client.get('/api/profile').status_code == 403
    assert client.post('/api/profile/photo').status_code == 403
    assert client.get('/api/users/1/profile-photo').status_code == 404
    assert not m._profile_photo_root().exists()


def test_profile_upload_survives_broker_failure_and_storage_error_preserves_old_photo(aml_app, monkeypatch):
    m = aml_app
    client, _ = account(m, 'demo')
    def broken(*args, **kwargs):
        raise RuntimeError('Injected broker failure')
    monkeypatch.setattr(m, '_broadcast_profile_update', broken)
    saved = upload(client)
    assert saved.status_code == 200
    url = saved.json['profile']['profile_photo_url']
    original = client.get(url).data
    import profile_photos
    def unavailable(*args, **kwargs):
        raise ProfilePhotoError('Injected storage failure')
    monkeypatch.setattr(profile_photos, 'save_photo', unavailable)
    assert upload(client).status_code == 400
    assert client.get(url).data == original
