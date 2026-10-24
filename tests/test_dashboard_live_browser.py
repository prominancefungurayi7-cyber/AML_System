"""Dashboard state changes from mocked events; no application or payment writes."""
import json
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright, expect


ROOT = Path(__file__).resolve().parents[1]


def test_customer_can_open_real_model_reasoning_for_successful_decision():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        try:
            page, errors = dashboard_page(browser, 'customer', dict(
                user=dict(account_number='ACC1'), transactions=[
                    dict(id=41, amount=5, ai_risk_level='normal', ai_reason='V4 normal pattern'),
                    dict(id=42, amount=5, ai_risk_level='inference_error', ai_reason='V4 inference unresolved: RESOURCE_ERROR')]))
            requests = []
            def explain(route):
                requests.append(route.request.url)
                route.fulfill(content_type='application/json', body=json.dumps(dict(
                    transaction_id=41, prediction=0, findings=[dict(feature='test', label='Wallet activity',
                        direction='lowers the suspicious score', contribution=-1.2)])))
            page.route('**/api/transactions/41/ai-evidence', explain)
            expect(page.get_by_role('button', name='Show AI reasoning', exact=True)).to_have_count(1)
            page.get_by_role('button', name='Show AI reasoning', exact=True).click()
            expect(page.get_by_text('Wallet activity', exact=False)).to_be_visible()
            assert len(requests) == 1 and not errors
        finally:
            browser.close()


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


def test_current_score_weights_are_visible_without_relabelling_old_scores():
    from v4_primary import SCORING_POLICY
    model = dict(primary_model='V4', threshold=0.5, rules_enabled=True,
                 risk_scoring=SCORING_POLICY)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        try:
            page, errors = dashboard_page(browser, 'admin', dict(model=model, users=[]))
            page.get_by_role('button', name='Settings', exact=True).click()
            expect(page.get_by_text('Score weights for new decisions', exact=True)).to_be_visible()
            expect(page.get_by_text('V4 70% \u00b7 Rules 30%', exact=True)).to_be_visible()
            expect(page.locator('.model-card')).to_contain_text('Earlier recorded scores are retained.')
            assert not errors
            page.close()

            page, errors = dashboard_page(browser, 'customer', dict(model=model,
                user=dict(account_number='ACC1'), transactions=[dict(id=1, amount=2, risk_score=27)]))
            page.get_by_role('button', name='Transactions', exact=True).click()
            operational_score = page.get_by_text('Operational score 27', exact=True)
            expect(operational_score).to_have_attribute('title',
                'Current policy for new decisions: V4 70% \u00b7 Rules 30%. '
                'V4 contributes its suspicious probability on a 0\u2013100 scale. '
                'Independent rule or AI flags may still require review. Earlier recorded scores are retained.')
            assert not errors
        finally:
            browser.close()


def test_dashboard_metadata_uses_the_shared_scoring_policy(aml_app):
    from v4_primary import SCORING_POLICY
    metadata = aml_app.primary_model_metadata()
    assert metadata['risk_scoring'] == SCORING_POLICY
    assert metadata['risk_scoring'] is not SCORING_POLICY
    assert metadata['risk_scoring']['ai_weight'] > metadata['risk_scoring']['rule_weight']


def test_payment_displays_limit_and_blocks_duplicate_submission():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        try:
            page, errors = dashboard_page(browser, 'customer', dict(
                user=dict(account_number='ACC1'), transactions=[]))
            expect(page.get_by_text('Current per-transaction limit: $15,000.00.')).to_be_visible()
            page.locator('input[name="amount"]').fill('10.50')
            page.locator('input[name="recipient"]').fill('ACC2')
            key = page.locator('input[name="client_request_id"]').input_value()
            assert key
            # No HTTP payment: prevent navigation while React handles submit.
            page.evaluate("document.querySelector('form').addEventListener('submit', e => e.preventDefault())")
            page.get_by_role('button', name='Confirm transaction', exact=True).click()
            expect(page.get_by_role('button', name='Saving payment...')).to_be_disabled()
            assert page.locator('input[name="client_request_id"]').input_value() == key
            page.evaluate("window.dispatchEvent(new Event('pageshow'))")
            expect(page.get_by_role('button', name='Confirm transaction', exact=True)).to_be_enabled()
            assert page.locator('input[name="client_request_id"]').input_value() == key
            assert not errors
        finally:
            browser.close()


def test_cash_form_selects_agent_and_derives_canonical_roles():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        try:
            page, errors = dashboard_page(browser, 'customer', dict(
                user=dict(account_number='ACC1'), transactions=[],
                agents=[dict(id=2, username='Agent', agent_code='AGENT0001')]))
            for kind in ('cash_in', 'cash_out'):
                page.locator('select[name="type"]').select_option(kind)
                page.locator('select[name="agent_id"]').select_option('2')
                page.locator('input[name="amount"]').fill('10.00')
                assert page.locator('input[name="channel"]').input_value() == 'agent'
                assert page.locator('input[name="serviced_wallet"]').input_value() == 'ACC1'
                assert page.locator('input[name="agent_flow_direction"]').input_value() == kind
                assert not page.locator('form').evaluate('(form) => form.checkValidity()')
                page.locator('input[name="cash_confirmed"]').check()
                assert page.locator('form').evaluate('(form) => form.checkValidity()')
                page.locator('input[name="cash_confirmed"]').uncheck()
            page.locator('select[name="type"]').select_option('wallet_to_wallet')
            assert page.locator('input[name="agent_id"]').input_value() == ''
            assert page.locator('input[name="channel"]').input_value() == 'direct_wallet'
            page.get_by_text('Optional agent assistance', exact=True).click()
            page.get_by_label('Agent-assisted transfer', exact=False).check()
            page.locator('input[name="recipient"]').fill('ACC2')
            page.locator('select[name="agent_id"]').select_option('2')
            page.get_by_label('Wallet assisted by the agent', exact=True).select_option('recipient')
            assert page.locator('input[name="channel"]').input_value() == 'agent'
            assert page.locator('input[name="serviced_wallet"]').input_value() == 'ACC2'
            assert page.locator('input[name="agent_flow_direction"]').input_value() == 'none'
            assert not errors
        finally:
            browser.close()


def test_customer_resync_updates_in_place_without_navigation():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        try:
            data = dict(user=dict(account_number='ACC1', balance=50), transactions=[], alerts=[], stats={})
            page, errors = dashboard_page(browser, 'customer', data)
            page.wait_for_timeout(200)
            page.evaluate("document.body.style.minHeight='4000px'; window.scrollTo(0,900); window.keptPage=true")
            updated = {**data, 'user': dict(account_number='ACC1', balance=75)}
            page.route('**/customer', lambda route: route.fulfill(content_type='text/html', body=
                '<script id="customer-dashboard-data" type="application/json">' + json.dumps(updated) + '</script>'))
            page.evaluate("window.dispatchEvent(new Event('aml:customer-resync'))")
            page.wait_for_timeout(900)
            assert page.evaluate('window.keptPage') is True
            assert page.evaluate('window.scrollY') == 900
            assert '$75.00' in page.inner_text('body')
            assert not errors
        finally:
            browser.close()
