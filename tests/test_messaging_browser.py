"""Browser interaction checks with simulated sockets and HTTP; no live messages."""
import json
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

from playwright.sync_api import sync_playwright, expect


def test_contacts_drafts_history_acknowledgement_and_reconnect():
    root = Path(__file__).resolve().parents[1]
    section = (root / 'templates/messages.html').read_text(encoding='utf-8').split('<section', 1)[1].split('<script', 1)[0]
    stub = """window.handlers={}; window.outgoing=[];
    window.fakeSocket={connected:true,on(name,fn){(handlers[name]??=[]).push(fn)},
      emit(name,data,ack){outgoing.push({name,data,ack})},disconnect(){}};
    window.io=()=>fakeSocket;
    window.fire=(name,data)=>(handlers[name]||[]).forEach(fn=>fn(data));"""
    html = '<html><head><script>' + stub + '</script><script src="/static/app-shell.js"></script></head><body data-authenticated="true" data-user-role="compliance" data-username="Compliance"><main id="main-content"><section' + section + '</main><script src="/static/messages.js"></script></body></html>'
    html = html.replace('</head>', '<style>#messagesContainer {height:220px; overflow-y:auto} .message-group {height:60px} .unread-messages-divider {height:30px}</style></head>')
    messages = [dict(id=i, sender_username='demo', receiver_username='Compliance', content=f'Message {i}', status='read' if i <= 10 else 'sent', created_at='2026-10-16T12:00:00Z') for i in range(1, 56)]
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page()
        page.add_init_script("""
          window.testPermission = 'default';
          window.permissionEvents = new EventTarget();
          Object.defineProperty(Notification, 'permission', {get: () => testPermission});
          Notification.requestPermission = async () => {
            window.testPermission = 'granted';
            permissionEvents.dispatchEvent(new Event('change'));
            return testPermission;
          };
          navigator.permissions.query = async () => permissionEvents;
        """)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        def route(request):
            parsed = urlsplit(request.request.url)
            path = parsed.path
            if path == '/messages':
                request.fulfill(content_type='text/html', body=html)
                return
            if path.startswith('/static/'):
                request.fulfill(content_type='application/javascript', body=(root / path.lstrip('/')).read_text(encoding='utf-8'))
                return
            data = {'status': 'success'}
            if path == '/api/messageable-users':
                data['users'] = [dict(username=n, role=r, account_number=a, is_online=True) for n, r, a in [('demo','customer','ACC1003'), ('Admin','admin','ACC1001')]]
            elif path == '/api/conversations':
                data['conversations'] = [{'id': 1, 'other_participant': 'demo', 'content': 'Message 55', 'unread_count': 2}]
            elif path == '/api/conversations/1/messages':
                before = int(parse_qs(parsed.query).get('before_id', ['999999'])[0])
                data['messages'] = [m for m in reversed(messages) if m['id'] < before][:50]
            else:
                data['unread'] = {'total_unread': 0}
            request.fulfill(content_type='application/json', body=json.dumps(data))
        page.route('**/*', route)
        try:
            page.goto('http://127.0.0.1:5000/messages')
            alerts = page.locator('#enableMessageNotifications')
            alerts.click()
            expect(alerts).to_have_text('\u2713 Device alerts enabled')
            expect(alerts).to_have_attribute('aria-pressed', 'true')
            page.evaluate("testPermission='denied'; permissionEvents.dispatchEvent(new Event('change'))")
            expect(alerts).to_have_text('\u00d7 Device alerts blocked')
            expect(alerts).to_have_attribute('aria-pressed', 'false')
            page.evaluate("testPermission='granted'; permissionEvents.dispatchEvent(new Event('change'))")
            expect(alerts).to_have_text('\u2713 Device alerts enabled')
            page.locator('.conversation-item').filter(has_text='demo').click()
            expect(page.locator('#chatAccount')).to_have_text('ACC1003')
            expect(page.locator('#openContacts')).to_have_attribute('aria-expanded', 'false')
            expect(page.locator('.message-group')).to_have_count(50)
            expect(page.locator('.unread-messages-divider')).to_have_text('Unread Messages')
            assert page.locator('.unread-messages-divider').evaluate('(node) => node.nextElementSibling.dataset.messageId') == '11'
            assert page.locator('.unread-messages-divider').evaluate('(node) => {const box=node.getBoundingClientRect(), parent=node.parentElement.getBoundingClientRect(); return box.top >= parent.top && box.bottom <= parent.bottom}')
            page.get_by_role('button', name='Load earlier messages').click()
            expect(page.locator('.message-group')).to_have_count(55)
            page.locator('#messageInput').fill('Preserved draft')
            page.locator('#openContacts').click()
            page.locator('.conversation-item').filter(has_text='Admin').click()
            expect(page.locator('.unread-messages-divider')).to_have_count(0)
            # Simulate the server having persisted the earlier mark_read event.
            for message in messages:
                message['status'] = 'read'
            expect(page.locator('#messageInput')).to_have_value('')
            page.locator('#openContacts').click()
            page.locator('.conversation-item').filter(has_text='demo').click()
            expect(page.locator('#messageInput')).to_have_value('Preserved draft')
            page.evaluate("dispatchEvent(new Event('aml:messages-resync'))")
            expect(page.locator('#messageInput')).to_have_value('Preserved draft')
            page.locator('#messageInput').press('Enter')
            expect(page.locator('#messageInput')).to_have_value('Preserved draft')
            page.evaluate("""() => {
              const sent=outgoing.find(e=>e.name==='send_message');
              const msg={id:56,sender:'Compliance',receiver:'demo',content:sent.data.content,status:'sent',timestamp:'2026-10-16T12:01:00Z',conversation_id:1};
              fire('new_message',msg); sent.ack({status:'success',message_id:56,message:msg});
            }""")
            expect(page.locator('#messageInput')).to_have_value('')
            expect(page.locator('[data-message-id="56"]')).to_have_count(1)
            expect(page.locator('.unread-messages-divider')).to_have_count(0)
            assert page.locator('#messagesContainer').evaluate('(node) => Math.abs(node.scrollHeight - node.clientHeight - node.scrollTop) < 2')
            expect(page.locator('[data-message-id="56"] .message-receipt')).to_have_attribute('aria-label', 'Sent')
            page.evaluate("fire('message_status', {id:56,conversation_id:1,status:'delivered'})")
            expect(page.locator('[data-message-id="56"] .message-receipt')).to_have_attribute('aria-label', 'Delivered')
            page.evaluate("fire('messages_read', {conversation_id:1,last_read_id:56})")
            expect(page.locator('[data-message-id="56"] .message-receipt')).to_have_attribute('aria-label', 'Read')
            expect(page.locator('[data-message-id="56"] .message-receipt')).to_have_class('message-receipt message-receipt--read')
            assert page.locator('#messagesContainer').evaluate('(node) => Math.abs(node.scrollHeight - node.clientHeight - node.scrollTop) < 2')
            assert not errors
        finally:
            browser.close()
