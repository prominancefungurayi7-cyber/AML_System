"""Messaging attachments in a browser with simulated HTTP/socket delivery only."""
import base64
import json
import uuid
from email.parser import BytesParser
from email.policy import default
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import expect, sync_playwright


PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jL1sAAAAASUVORK5CYII=')


@pytest.fixture
def attachment_browser():
    root = Path(__file__).resolve().parents[1]
    section = (root / 'templates/messages.html').read_text(encoding='utf-8').split('<section', 1)[1].split('<script', 1)[0]
    section = section.replace('{{ message_attachment_csrf }}', 'attachment-test-csrf')
    stub = '''window.handlers={}; window.outgoing=[]; window.notifications=[];
      window.fakeSocket={connected:true,on(name,fn){(handlers[name]??=[]).push(fn)},
        emit(name,data,ack){outgoing.push({name,data,ack})}};
      window.getAmlSocket=()=>fakeSocket;
      window.showAmlNotification=(message)=>notifications.push(message);
      window.fire=(name,data)=>(handlers[name]||[]).forEach(fn=>fn(data));'''
    html = '<html><head><link rel="stylesheet" href="/static/style.css"><script>' + stub + '</script></head><body data-username="Compliance"><section' + section + '<script src="/static/messages.js"></script></body></html>'
    uploads, errors = [], []
    state = {'failures': 0, 'messages': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width': 1000, 'height': 800})
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
            if path == '/api/messages/90/attachment':
                route.fulfill(content_type='image/png', body=PNG)
                return
            if path == '/api/message-attachments':
                mime = BytesParser(policy=default).parsebytes(('Content-Type: ' + request.headers['content-type'] + '\r\n\r\n').encode() + request.post_data_buffer)
                payload = {}
                for part in mime.iter_parts():
                    name = part.get_param('name', header='content-disposition')
                    payload[name] = part.get_filename() if name == 'file' else part.get_content().strip()
                uploads.append(payload)
                if state.get('hold_upload'):
                    state['held_upload'] = route, payload
                    return
                if state['failures']:
                    state['failures'] -= 1
                    route.fulfill(status=503, content_type='application/json', body=json.dumps({'status': 'error', 'message': 'Attachment service unavailable. Your draft is preserved.'}))
                else:
                    message = dict(id=100, sender='Compliance', receiver=payload['receiver'], content=payload['content'],
                                   status='sent', timestamp='2026-10-17T12:00:00Z', conversation_id=1 if payload['receiver'] == 'demo' else 2,
                                   attachment=dict(name=payload['file'], size=8, media_type='text/plain', url='/api/messages/100/attachment'))
                    route.fulfill(content_type='application/json', body=json.dumps({'status': 'success', 'message': message}))
                return
            data = {'status': 'success'}
            if path == '/api/messageable-users':
                data['users'] = [dict(username=name, account_number=account, is_online=True) for name, account in [('demo', 'ACC1003'), ('Admin', 'ACC1001')]]
            elif path == '/api/conversations':
                data['conversations'] = [dict(id=1, other_participant='demo', content='', unread_count=0), dict(id=2, other_participant='Admin', content='', unread_count=0)]
            else:
                data['messages'] = state['messages'] if path == '/api/conversations/1/messages' else []
            route.fulfill(content_type='application/json', body=json.dumps(data))

        page.route('**/*', route)
        page.goto('http://127.0.0.1:5000/messages')
        page.locator('.conversation-item').filter(has_text='demo').click()
        yield page, uploads, state
        assert not errors
        browser.close()


def test_file_drafts_upload_and_small_receipts(attachment_browser):
    page, uploads, state = attachment_browser
    page.locator('#attachmentInput').set_input_files({'name': 'evidence.txt', 'mimeType': 'text/plain', 'buffer': b'evidence'})
    page.locator('#messageInput').fill('Review this evidence')
    expect(page.locator('#attachmentDraftName')).to_have_text('evidence.txt')
    page.locator('#openContacts').click()
    page.locator('.conversation-item').filter(has_text='Admin').click()
    expect(page.locator('#attachmentDraft')).to_be_hidden()
    page.locator('#openContacts').click()
    page.locator('.conversation-item').filter(has_text='demo').click()
    expect(page.locator('#attachmentDraftName')).to_have_text('evidence.txt')
    expect(page.locator('#messageInput')).to_have_value('Review this evidence')
    page.locator('#messageInput').press('Enter')
    expect(page.locator('#attachmentDraft')).to_be_hidden()
    expect(page.locator('#messageInput')).to_have_value('')
    expect(page.locator('[data-message-id="100"] .message-attachment-name')).to_have_text('evidence.txt')
    expect(page.locator('[data-message-id="100"] .message-attachment-caption')).to_have_text('Review this evidence')
    expect(page.locator('[data-message-id="100"] .message-attachment-card')).to_have_attribute('download', 'evidence.txt')
    assert uploads[0]['csrf_token'] == 'attachment-test-csrf'
    assert uploads[0]['receiver'] == 'demo'
    assert len(uploads[0]['client_request_id']) == 36
    page.evaluate("fire('message_status', {id:100,conversation_id:1,status:'delivered'})")
    expect(page.locator('[data-message-id="100"] .message-receipt')).to_have_attribute('aria-label', 'Delivered')
    page.evaluate("fire('messages_read', {conversation_id:1,last_read_id:100})")
    expect(page.locator('[data-message-id="100"] .message-receipt')).to_have_attribute('aria-label', 'Read')


def test_attachment_http_upload_works_while_socket_reconnects(attachment_browser):
    page, uploads, state = attachment_browser
    page.evaluate('fakeSocket.connected = false')
    page.locator('#attachmentInput').set_input_files({'name': 'evidence.txt', 'mimeType': 'text/plain', 'buffer': b'evidence'})
    page.locator('#sendButton').click()
    expect(page.locator('[data-message-id="100"] .message-attachment-name')).to_have_text('evidence.txt')
    assert len(uploads) == 1


def test_failed_upload_preserves_file_and_retry_identity(attachment_browser):
    page, uploads, state = attachment_browser
    state['failures'] = 2
    page.locator('#attachmentInput').set_input_files({'name': 'evidence.pdf', 'mimeType': 'application/pdf', 'buffer': b'%PDF-test'})
    page.locator('#messageInput').fill('Caption')
    page.locator('#sendButton').click()
    expect(page.locator('#sendButton')).to_be_enabled()
    expect(page.locator('#attachmentDraftName')).to_have_text('evidence.pdf')
    expect(page.locator('#messageInput')).to_have_value('Caption')
    assert page.evaluate('notifications.at(-1)') == 'Attachment service unavailable. Your draft is preserved.'
    assert len(uploads) == 1
    page.locator('#sendButton').click()
    expect(page.locator('#sendButton')).to_be_enabled()
    assert len(uploads) == 2
    assert uploads[0]['client_request_id'] == uploads[1]['client_request_id']
    page.locator('#messageInput').fill('Changed caption')
    page.locator('#sendButton').click()
    expect(page.locator('#attachmentDraft')).to_be_hidden()
    assert len(uploads) == 3
    assert uploads[2]['client_request_id'] != uploads[0]['client_request_id']


def test_attachment_request_ids_work_without_secure_context_random_uuid(attachment_browser):
    page, uploads, state = attachment_browser
    page.evaluate("Object.defineProperty(crypto,'randomUUID',{value:undefined,configurable:true})")
    state['failures'] = 1
    page.locator('#attachmentInput').set_input_files({'name': 'evidence.txt', 'mimeType': 'text/plain', 'buffer': b'evidence'})
    page.locator('#messageInput').fill('Initial caption')
    page.locator('#sendButton').click()
    expect(page.locator('#sendButton')).to_be_enabled()
    first = uuid.UUID(uploads[0]['client_request_id'])
    assert first.version == 4 and first.variant == uuid.RFC_4122
    page.locator('#messageInput').fill('Changed caption')
    page.locator('#sendButton').click()
    expect(page.locator('#attachmentDraft')).to_be_hidden()
    second = uuid.UUID(uploads[1]['client_request_id'])
    assert second.version == 4 and second.variant == uuid.RFC_4122
    assert first != second


def test_screenshot_paste_preview_and_safe_history(attachment_browser):
    page, uploads, state = attachment_browser
    page.evaluate('''() => {
      const bytes = Uint8Array.from(atob("''' + base64.b64encode(PNG).decode() + '''"), c => c.charCodeAt(0));
      const data = new DataTransfer(); data.items.add(new File([bytes], 'screenshot.png', {type:'image/png'}));
      document.getElementById('messageInput').dispatchEvent(new ClipboardEvent('paste', {clipboardData:data, bubbles:true, cancelable:true}));
    }''')
    expect(page.locator('#attachmentDraftImage')).to_be_visible()
    expect(page.locator('#attachmentDraftName')).to_have_text('screenshot.png')
    page.locator('#removeAttachment').click()
    expect(page.locator('#attachmentDraft')).to_be_hidden()
    page.evaluate('''() => fire('new_message', {id:90,sender:'demo',receiver:'Compliance',content:'Evidence',status:'sent',
      timestamp:'2026-10-17T12:00:00Z',conversation_id:1,
      attachment:{name:'screenshot.png',size:69,media_type:'image/png',url:'/api/messages/90/attachment',preview_url:'/api/messages/90/attachment?inline=1'}})''')
    expect(page.locator('[data-message-id="90"] .message-attachment-image')).to_be_visible()
    expect(page.locator('[data-message-id="90"] .message-attachment-image')).to_have_attribute('src', 'http://127.0.0.1:5000/api/messages/90/attachment?inline=1')
    page.evaluate('''() => fire('new_message', {id:91,sender:'demo',receiver:'Compliance',content:'',status:'sent',
      timestamp:'2026-10-17T12:00:00Z',conversation_id:1,
      attachment:{name:'<img src=x onerror=alert(1)>.txt',size:8,media_type:'text/plain',url:'/api/messages/91/attachment'}})''')
    expect(page.locator('[data-message-id="91"] .message-attachment-name')).to_have_text('<img src=x onerror=alert(1)>.txt')
    expect(page.locator('[data-message-id="91"] img')).to_have_count(0)
    page.evaluate('''() => fire('new_message', {id:92,sender:'demo',receiver:'Compliance',content:'',status:'sent',
      timestamp:'2026-10-17T12:00:00Z',conversation_id:1,
      attachment:{name:'outside.png',size:8,media_type:'image/png',url:'https://outside.invalid/evidence',preview_url:'javascript:alert(1)'}})''')
    expect(page.locator('[data-message-id="92"] .message-bubble')).to_have_text('Attachment unavailable.')
    expect(page.locator('[data-message-id="92"] a')).to_have_count(0)
    assert not uploads


def test_upload_acknowledgement_preserves_a_new_attachment_draft(attachment_browser):
    page, uploads, state = attachment_browser
    state['hold_upload'] = True
    page.locator('#attachmentInput').set_input_files({'name': 'original.txt', 'mimeType': 'text/plain', 'buffer': b'original'})
    page.locator('#messageInput').fill('Original caption')
    page.locator('#sendButton').click()
    expect(page.locator('#sendButton')).to_be_disabled()
    page.locator('#attachmentInput').set_input_files({'name': 'next.txt', 'mimeType': 'text/plain', 'buffer': b'next'})
    page.locator('#messageInput').fill('Next caption')
    route, payload = state['held_upload']
    message = dict(id=100, sender='Compliance', receiver='demo', content='Original caption', status='sent',
                   timestamp='2026-10-17T12:00:00Z', conversation_id=1,
                   attachment=dict(name='original.txt', size=8, media_type='text/plain', url='/api/messages/100/attachment'))
    route.fulfill(content_type='application/json', body=json.dumps({'status': 'success', 'message': message}))
    expect(page.locator('#sendButton')).to_be_enabled()
    expect(page.locator('#messageInput')).to_have_value('Next caption')
    expect(page.locator('#attachmentDraftName')).to_have_text('next.txt')
    expect(page.locator('[data-message-id="100"] .message-attachment-name')).to_have_text('original.txt')
    assert len(uploads) == 1


def test_mobile_attachment_layout_and_lazy_load_preserve_reading_position(attachment_browser):
    page, uploads, state = attachment_browser
    page.set_viewport_size({'width': 390, 'height': 844})
    long_name = 'transaction_evidence_' + 'account_12345_' * 10 + '.png'
    page.locator('#attachmentInput').set_input_files({'name': long_name, 'mimeType': 'image/png', 'buffer': PNG})
    expect(page.locator('#attachmentDraftImage')).to_be_visible()
    page.evaluate('''name => {
      for(let id=50;id<70;id++) fire('new_message', {id,sender:'demo',receiver:'Compliance',content:'Evidence review '+id,
        status:'sent',timestamp:'2026-10-17T12:00:00Z',conversation_id:1});
      fire('new_message', {id:90,sender:'demo',receiver:'Compliance',content:'Screenshot evidence',status:'sent',
        timestamp:'2026-10-17T12:00:00Z',conversation_id:1,
        attachment:{name,size:69,media_type:'image/png',url:'/api/messages/90/attachment',preview_url:'/api/messages/90/attachment?inline=1'}});
      fire('new_message', {id:91,sender:'demo',receiver:'Compliance',content:'Supporting file',status:'sent',
        timestamp:'2026-10-17T12:00:00Z',conversation_id:1,
        attachment:{name:name+'.txt',size:69,media_type:'text/plain',url:'/api/messages/91/attachment'}});
    }''', long_name)
    expect(page.locator('[data-message-id="90"] .message-attachment-image')).to_be_visible()
    assert page.evaluate('''() => {
      const width=document.documentElement.clientWidth;
      return document.documentElement.scrollWidth<=width+1 &&
        [...document.querySelectorAll('#attachmentDraft,.message-attachment-card,.message-attachment-image,#messageInput,#attachFile,#sendButton')]
          .every(node=>{const box=node.getBoundingClientRect();return box.left>=-1&&box.right<=width+1});
    }''')
    for selector in ['#attachFile', '#sendButton']:
        assert page.locator(selector).evaluate('''node => {
          const box=node.getBoundingClientRect();
          const target=document.elementFromPoint(box.left+box.width/2,box.top+box.height/2);
          return node===target||node.contains(target);
        }''')
    # Delayed image loads must not jump a person reading earlier messages.
    previous_top = page.locator('#messagesContainer').evaluate('''node => {
      node.scrollTop=node.scrollHeight-node.clientHeight-150; return node.scrollTop;
    }''')
    page.locator('[data-message-id="90"] img').dispatch_event('load')
    assert page.locator('#messagesContainer').evaluate('(node)=>node.scrollTop') == previous_top
    assert not uploads
