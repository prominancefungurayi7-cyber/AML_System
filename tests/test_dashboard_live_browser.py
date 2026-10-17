"""Dashboard state changes from mocked events; no application or payment writes."""
import json
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright, expect


ROOT = Path(__file__).resolve().parents[1]


def dashboard_page(browser, role, data, generation_status=None):
    page = browser.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    stub = """window.handlers={};
    window.fakeSocket={connected:true,on(name,fn){(handlers[name]??=[]).push(fn)},
      off(name,fn){handlers[name]=(handlers[name]||[]).filter(f=>f!==fn)}};
    window.getAmlSocket=()=>fakeSocket;
    window.fire=(name,data)=>(handlers[name]||[]).forEach(fn=>fn(data));
    window.__amlSidebarController={register:()=>()=>{},close:()=>{}};
    window.showAmlNotification=()=>{};"""
    html = f'''<html><head><script>{stub}</script></head><body data-user-role="{role}">
    <div id="{role}-react-root"></div>
    <script id="{role}-dashboard-data" type="application/json">{json.dumps(data)}</script>
    <script src="/static/vendor/react.production.min.js"></script>
    <script src="/static/vendor/react-dom.production.min.js"></script>
    <script src="/static/react-dashboard.js"></script></body></html>'''

    def route(request):
        path = urlsplit(request.request.url).path
        if path.startswith('/static/'):
            request.fulfill(content_type='application/javascript', body=(ROOT / path.lstrip('/')).read_text(encoding='utf-8'))
        elif path == '/api/admin/generation':
            request.fulfill(content_type='application/json', body=json.dumps(generation_status()))
        else:
            request.fulfill(content_type='text/html', body=html)
    page.route('**/*', route)
    page.goto(f'http://127.0.0.1:5000/{role}')
    return page, errors


def test_compliance_zero_count_and_live_transaction_filter():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        try:
            data = dict(stats={'open_alerts': 0}, filter_value='suspicious',
                        transactions=[{'id': 41, 'risk_level': 'suspicious', 'amount': 5}],
                        open_alerts=[{'id': 7, 'transaction_id': 41, 'risk_level': 'suspicious'}])
            page, errors = dashboard_page(browser, 'compliance', data)
            expect(page.locator('.metric-tile').filter(has_text='Open alerts').locator('strong')).to_have_text('0')
            page.get_by_role('button', name='Transactions', exact=True).click()
            expect(page.locator('tbody tr')).to_have_count(1)
            page.evaluate("fire('transaction', {id:41,risk_level:'normal',amount:5})")
            expect(page.get_by_text('No transactions match this filter.')).to_be_visible()
            page.evaluate("fire('transaction', {id:42,risk_level:'critical',amount:10})")
            expect(page.locator('tbody tr')).to_have_count(1)
            expect(page.locator('tbody')).to_contain_text('#42')
            assert not errors
        finally:
            browser.close()


def test_generator_resumes_status_updates_after_batch_or_focus():
    status = {'value': None, 'calls': 0}
    def generation_status():
        status['calls'] += 1
        return status['value']

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        try:
            data = dict(users=[], generation=dict(wallet_count=8, agent_count=0, csrf='test',
                        choices=[dict(count=100, mode='mixed', token='test-token')]))
            page, errors = dashboard_page(browser, 'admin', data, generation_status)
            page.wait_for_function('document.querySelector(".generation-card") !== null')
            page.wait_for_timeout(100)
            assert status['calls'] == 1
            status['value'] = dict(saved=1, requested=1, normal=1, suspicious_pattern=0,
                                   pending_v4=0, inference_error=0, ordinary_inputs=1, suspicious_inputs=0)
            page.evaluate("fire('transaction_batch', {count:1})")
            expect(page.locator('.generation-progress')).to_contain_text('1 / 1 saved')
            status['value'] = {**status['value'], 'requested': 10, 'saved': 10, 'normal': 10}
            page.evaluate("dispatchEvent(new Event('focus'))")
            expect(page.locator('.generation-progress')).to_contain_text('10 / 10 saved')
            assert status['calls'] == 3
            assert not errors
        finally:
            browser.close()


def test_delayed_ai_updates_keep_recent_transactions_in_payment_order():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        try:
            data = dict(users=[], transactions=[
                dict(id='9007199254740995', timestamp='2026-10-17T12:02:00Z', amount=3),
                dict(id='9007199254740994', timestamp='2026-10-17T12:01:00Z', amount=2)])
            page, errors = dashboard_page(browser, 'admin', data)
            page.get_by_role('button', name='Transactions', exact=True).click()
            page.evaluate("fire('transaction', {id:'9007199254740994',risk_level:'suspicious',amount:2})")
            expect(page.locator('tbody tr')).to_have_count(2)
            expect(page.locator('tbody tr').first.locator('td').first).to_have_text('9007199254740995')
            page.evaluate("fire('transaction', {id:'9007199254740993',timestamp:'2026-10-17T12:00:00Z',amount:1})")
            expect(page.locator('tbody tr')).to_have_count(3)
            expect(page.locator('tbody tr').last.locator('td').first).to_have_text('9007199254740993')
            page.evaluate("fire('transaction', {id:'9007199254740996',timestamp:'2026-10-17T12:02:00Z',amount:4})")
            expect(page.locator('tbody tr').first.locator('td').first).to_have_text('9007199254740996')
            assert not errors
        finally:
            browser.close()
