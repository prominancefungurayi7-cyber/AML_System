from pathlib import Path
from playwright.sync_api import sync_playwright, expect


def test_autofill_submits_once_but_typing_and_failed_login_do_not():
    script = (Path(__file__).resolve().parents[1] / 'static/login.js').read_text(encoding='utf-8')
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        try:
            page = browser.new_page()
            for allowed in ('true', 'false'):
                page.set_content(f'''<form id="signInForm" data-auto-sign-in="{allowed}">
                  <input id="login" required><input id="password" type="password" required>
                  <button type="submit">Sign In</button></form>''')
                page.evaluate('''() => {
                  window.submissions = 0;
                  const form = document.querySelector('form');
                  form.addEventListener('submit', event => {event.preventDefault(); window.submissions++;});
                }''')
                page.add_script_tag(content=script)
                page.locator('#login').fill('demo')
                page.locator('#password').fill('test-only-password')
                page.wait_for_timeout(300)
                assert page.evaluate('submissions') == 0
                # Browser autofill state is simulated; no saved real passwords used.
                page.evaluate('''() => {
                  const input = document.getElementById('password');
                  input.matches = selector => selector === ':autofill';
                  input.dispatchEvent(new Event('input', {bubbles:true}));
                  input.dispatchEvent(new Event('change', {bubbles:true}));
                }''')
                page.wait_for_timeout(300)
                assert page.evaluate('submissions') == (1 if allowed == 'true' else 0)
                if allowed == 'true':
                    expect(page.get_by_role('button')).to_have_text('Signing in…')
                    page.locator('#password').dispatch_event('change')
                    page.wait_for_timeout(300)
                    assert page.evaluate('submissions') == 1
        finally:
            browser.close()
