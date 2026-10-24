"""Contact discovery and profile photos without live accounts or uploads."""
import base64
import json
from email.parser import BytesParser
from email.policy import default
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from playwright.sync_api import expect, sync_playwright


PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jL1sAAAAASUVORK5CYII=')


def test_chats_follow_latest_message_and_update_after_realtime_event(profiles_browser):
    page, state = profiles_browser
    threads = [dict(id=1, other_participant='Alex', last_message_at='2026-10-23T08:00:00Z', last_message_id='40'),
               dict(id=2, other_participant='Compliance', last_message_at='2026-10-23T09:00:00Z', last_message_id='41')]
    page.route('**/api/conversations', lambda route: route.fulfill(
        content_type='application/json', body=json.dumps(dict(status='success', conversations=threads))))
    page.evaluate("fire('unread_update', {})")
    expect(page.locator('.conversation-item').first).to_contain_text('Compliance')
    threads[0].update(last_message_at='2026-10-23T09:00:00Z', last_message_id='42')
    page.evaluate("fire('new_message', {id:42,sender:'Alex',receiver:'demo',conversation_id:1,content:'Latest',timestamp:'2026-10-23T09:00:00Z'})")
    expect(page.locator('.conversation-item').first).to_contain_text('Alex')


@pytest.fixture
def profiles_browser(request):
    root = Path(__file__).resolve().parents[1]
    options = getattr(request, 'param', {})
    section = (root / 'templates/messages.html').read_text(encoding='utf-8').split('<section', 1)[1].split('<script', 1)[0]
    section = section.replace('{{ profile_photo_csrf }}', 'profile-test-csrf' if options.get('bootstrap') else '')
    section = section.replace("{{ current_message_profile.profile_photo_url or '' }}", '')
    section = section.replace('{{ user.account_number }}', 'ACC1003' if options.get('bootstrap') else '')
    stub = '''window.handlers={};window.outgoing=[];window.notifications=[];
      window.fakeSocket={connected:true,on(name,fn){(handlers[name]??=[]).push(fn)},
        emit(name,data,ack){outgoing.push({name,data,ack})}};
      window.getAmlSocket=()=>fakeSocket;
      window.showAmlNotification=(message,key,type)=>notifications.push({message,type});
      window.fire=(name,data)=>(handlers[name]||[]).forEach(fn=>fn(data));'''
    html = '<html><head><link rel="stylesheet" href="/static/style.css"><script>' + stub + '</script></head><body data-username="demo"><div class="account-avatar">DE</div><section' + section + '<script src="/static/messages.js"></script></body></html>'
    state = {
        'queries': [], 'uploads': [], 'deletes': [], 'held_profiles': [],
        'profile_mode': options.get('profile_mode', 'success'),
        'profile': dict(username='demo', account_number='ACC1003', role='customer', profile_photo_url=None),
        'users': [
            dict(id=4, username='Alex', role='customer', account_number='ACC1004', is_online=True, profile_photo_url=None),
            dict(id=2, username='Compliance', role='compliance', account_number='ACC1002', is_online=True, profile_photo_url=None),
        ],
    }
    errors = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width': 1100, 'height': 850})
        if options.get('clock'):
            page.clock.install()
        page.on('pageerror', lambda error: errors.append(str(error)))

        def route(route):
            request = route.request
            parsed = urlsplit(request.url)
            path = parsed.path
            if path == '/messages':
                route.fulfill(content_type='text/html', body=html)
                return
            if path.startswith('/static/'):
                route.fulfill(content_type='text/css' if path.endswith('.css') else 'application/javascript', body=(root / path.lstrip('/')).read_text(encoding='utf-8'))
                return
            if path.startswith('/api/users/') and path.endswith('/profile-photo'):
                route.fulfill(content_type='image/png', body=PNG)
                return
            data = {'status': 'success'}
            if path == '/api/profile':
                if state['profile_mode'] == 'hold':
                    state['held_profiles'].append(route)
                    return
                if state['profile_mode'] == 'failure':
                    route.fulfill(status=503, content_type='application/json', body='{"message":"Temporarily unavailable"}')
                    return
                if state['profile_mode'] == 'invalid':
                    route.fulfill(content_type='application/json', body='{"status":"success"}')
                    return
                data.update(profile=state['profile'], csrf_token='profile-test-csrf')
            elif path == '/api/profile/photo':
                if request.method == 'POST':
                    mime = BytesParser(policy=default).parsebytes(('Content-Type: ' + request.headers['content-type'] + '\r\n\r\n').encode() + request.post_data_buffer)
                    fields = {part.get_param('name', header='content-disposition'): part.get_filename() or part.get_content().strip() for part in mime.iter_parts()}
                    state['uploads'].append(fields)
                    state['profile']['profile_photo_url'] = '/api/users/3/profile-photo?v=one'
                elif request.method == 'DELETE':
                    state['deletes'].append(request.headers.get('x-csrf-token'))
                    state['profile']['profile_photo_url'] = None
                data['profile'] = state['profile']
            elif path == '/api/messageable-users':
                query = parse_qs(parsed.query).get('q', [''])[0]
                state['queries'].append(query)
                data['users'] = [user for user in state['users'] if query.casefold() in (user['username'] + user['account_number']).casefold()]
            elif path == '/api/conversations':
                data['conversations'] = [dict(id=1, other_participant='Alex', content='Previous message', unread_count=0)]
            else:
                data['messages'] = []
            route.fulfill(content_type='application/json', body=json.dumps(data))

        page.route('**/*', route)
        page.goto('http://127.0.0.1:5000/messages')
        expect(page.locator('#myProfileName')).to_have_text('demo')
        expect(page.locator('.conversation-item')).to_have_count(2)
        yield page, state
        assert not errors
        browser.close()


def test_contact_search_preserves_active_customer_conversation_and_draft(profiles_browser):
    page, state = profiles_browser
    page.locator('.conversation-item').filter(has_text='Alex').click()
    page.locator('#messageInput').fill('Customer-to-customer evidence discussion')
    page.locator('#openContacts').click()
    page.locator('#contactSearch').fill('ACC1002')
    page.locator('#searchContacts').click()
    expect(page.locator('.conversation-item')).to_have_count(1)
    expect(page.locator('.conversation-item')).to_contain_text('Compliance')
    expect(page.locator('#contactSearchStatus')).to_have_text('1 contact found')
    expect(page.locator('#chatTitle')).to_have_text('Alex')
    expect(page.locator('#messageInput')).to_have_value('Customer-to-customer evidence discussion')
    page.locator('#closeContacts').click()
    page.evaluate("""fire('new_message',{id:10,sender:'Alex',receiver:'demo',content:'Reply while filtered',
      status:'sent',timestamp:'2026-10-17T12:00:00Z',conversation_id:1})""")
    expect(page.locator('[data-message-id="10"] .message-bubble')).to_have_text('Reply while filtered')
    page.locator('#openContacts').click()
    page.locator('#contactSearch').fill('alex')
    expect(page.locator('.conversation-item')).to_have_count(1)
    expect(page.locator('.conversation-item')).to_contain_text('Alex')
    page.locator('.conversation-item').click()
    expect(page.locator('#messageInput')).to_have_value('Customer-to-customer evidence discussion')
    expect(page.locator('#openContacts')).to_have_attribute('aria-expanded', 'false')
    assert 'ACC1002' in state['queries'] and 'alex' in state['queries']


def test_profile_upload_removal_and_realtime_avatar_updates(profiles_browser):
    page, state = profiles_browser
    expect(page.locator('#myProfileAccount')).to_have_text('ACC1003')
    page.locator('#profilePhotoInput').set_input_files({'name': 'professional.png', 'mimeType': 'image/png', 'buffer': PNG})
    expect(page.locator('#uploadProfilePhoto')).to_have_text('Change photo')
    expect(page.locator('#myProfileAvatar img')).to_have_attribute('src', 'http://127.0.0.1:5000/api/users/3/profile-photo?v=one')
    expect(page.locator('.account-avatar img')).to_have_count(1)
    assert state['uploads'] == [{'photo': 'professional.png', 'csrf_token': 'profile-test-csrf'}]
    assert page.evaluate('notifications.at(-1).type') == 'success'
    page.locator('.conversation-item').filter(has_text='Alex').click()
    page.locator('#messageInput').fill('Preserved during photo updates')
    page.evaluate("fire('profile_updated',{user_id:4,username:'Alex',profile_photo_url:'/api/users/4/profile-photo?v=two'})")
    expect(page.locator('#chatAvatar img')).to_have_attribute('src', 'http://127.0.0.1:5000/api/users/4/profile-photo?v=two')
    expect(page.locator('#messageInput')).to_have_value('Preserved during photo updates')
    page.locator('#openContacts').click()
    expect(page.locator('.conversation-item').filter(has_text='Alex').locator('img')).to_have_count(1)
    page.locator('#removeProfilePhoto').click()
    expect(page.locator('#myProfileAvatar img')).to_have_count(0)
    expect(page.locator('.account-avatar')).to_have_text('DE')
    expect(page.locator('#removeProfilePhoto')).to_be_hidden()
    assert state['deletes'] == ['profile-test-csrf']


def test_profile_input_validation_safe_urls_and_mobile_search(profiles_browser):
    page, state = profiles_browser
    page.locator('#profilePhotoInput').set_input_files({'name': 'script.svg', 'mimeType': 'image/svg+xml', 'buffer': b'<svg></svg>'})
    assert not state['uploads']
    assert 'JPG, PNG or WebP' in page.evaluate('notifications.at(-1).message')
    page.evaluate("fire('profile_updated',{user_id:4,username:'Alex',profile_photo_url:'https://outside.invalid/photo.png'})")
    expect(page.locator('.conversation-item').filter(has_text='Alex').locator('.conversation-avatar')).to_have_text('AL')
    page.set_viewport_size({'width': 390, 'height': 844})
    page.locator('#contactSearch').fill('No such account')
    expect(page.locator('.message-empty-state')).to_have_text('No contacts match your search.')
    expect(page.locator('#contactSearchStatus')).to_have_text('0 contacts found')
    assert page.evaluate('''() => {
      const width=document.documentElement.clientWidth;
      return document.documentElement.scrollWidth <= width+1 &&
        ['contactSearch','searchContacts','uploadProfilePhoto'].every(id=>{
          const box=document.getElementById(id).getBoundingClientRect(); return box.left>=-1&&box.right<=width+1;
        });
    }''')


@pytest.mark.parametrize('profiles_browser', [
    {'bootstrap': True, 'profile_mode': 'failure'},
    {'bootstrap': True, 'profile_mode': 'hold'},
], indirect=True)
def test_profile_picker_and_upload_do_not_wait_for_initial_profile_refresh(profiles_browser):
    page, state = profiles_browser
    button = page.locator('#uploadProfilePhoto')
    expect(button).to_be_enabled()
    button.hover()
    assert button.evaluate('node => getComputedStyle(node).cursor') == 'pointer'
    with page.expect_file_chooser() as picker:
        button.click()
    picker.value.set_files({'name': 'evidence.png', 'mimeType': 'image/png', 'buffer': PNG})
    expect(button).to_have_text('Change photo')
    expect(button).to_be_enabled()
    assert state['uploads'] == [{'photo': 'evidence.png', 'csrf_token': 'profile-test-csrf'}]
    if state['held_profiles']:
        state['held_profiles'].pop().fulfill(content_type='application/json', body=json.dumps({
            'status': 'success', 'csrf_token': 'profile-test-csrf',
            'profile': {**state['profile'], 'profile_photo_url': None},
        }))
        expect(page.locator('#myProfileAvatar img')).to_have_count(1)
        expect(button).to_have_text('Change photo')


@pytest.mark.parametrize('profiles_browser', [
    {'profile_mode': 'failure'}, {'profile_mode': 'invalid'},
], indirect=True)
def test_failed_profile_load_has_visible_recovery_and_keeps_selected_photo(profiles_browser):
    page, state = profiles_browser
    expect(page.locator('#retryProfilePhoto')).to_be_visible()
    expect(page.locator('#profilePhotoStatus')).to_contain_text('Unable to load your profile')
    expect(page.locator('#uploadProfilePhoto')).to_be_enabled()
    with page.expect_file_chooser() as picker:
        page.locator('#uploadProfilePhoto').click()
    picker.value.set_files({'name': 'retained.png', 'mimeType': 'image/png', 'buffer': PNG})
    expect(page.locator('#retryProfilePhoto')).to_have_text('Retry upload')
    expect(page.locator('#retryProfilePhoto')).to_be_enabled()
    expect(page.locator('#profilePhotoStatus')).to_contain_text('Your selected photo has been kept')
    assert not state['uploads']
    state['profile_mode'] = 'success'
    page.locator('#retryProfilePhoto').click()
    expect(page.locator('#uploadProfilePhoto')).to_have_text('Change photo')
    expect(page.locator('#retryProfilePhoto')).to_be_hidden()
    assert state['uploads'] == [{'photo': 'retained.png', 'csrf_token': 'profile-test-csrf'}]


@pytest.mark.parametrize('profiles_browser', [{'profile_mode': 'hold', 'clock': True}], indirect=True)
def test_stalled_profile_load_times_out_without_trapping_photo_button(profiles_browser):
    page, state = profiles_browser
    expect(page.locator('#uploadProfilePhoto')).to_be_enabled()
    with page.expect_file_chooser() as picker:
        page.locator('#uploadProfilePhoto').click()
    picker.value.set_files({'name': 'after-timeout.png', 'mimeType': 'image/png', 'buffer': PNG})
    page.clock.fast_forward(11000)
    expect(page.locator('#uploadProfilePhoto')).to_be_enabled()
    expect(page.locator('#retryProfilePhoto')).to_be_visible()
    expect(page.locator('#profilePhotoStatus')).to_contain_text('Your selected photo has been kept')
    state['profile_mode'] = 'success'
    page.locator('#retryProfilePhoto').click()
    expect(page.locator('#uploadProfilePhoto')).to_have_text('Change photo')
    assert len(state['uploads']) == 1
