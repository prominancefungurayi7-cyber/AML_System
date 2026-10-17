/* Submit browser-saved credentials once; never infer autofill from typing. */
(() => {
  'use strict';
  const form = document.getElementById('signInForm');
  const password = document.getElementById('password');
  const identifier = document.getElementById('login');
  if (!form || !password || !identifier || form.dataset.autoSignIn !== 'true') return;
  let submitted = false, timer;
  let selectedAfterLogout = form.dataset.signedOut !== 'true';
  let credentialInteraction = false;
  [identifier, password].forEach(input => {
    input.addEventListener('pointerdown', () => { credentialInteraction = true; });
    input.addEventListener('keydown', () => { credentialInteraction = true; });
    input.addEventListener('input', event => {
      if (event.isTrusted && credentialInteraction) selectedAfterLogout = true;
    });
  });
  const isAutofilled = input => {
    for (const selector of [':autofill', ':-webkit-autofill']) {
      try { if (input.matches(selector)) return true; } catch (_) { /* Browser-specific selector. */ }
    }
    return false;
  };
  function check() {
    clearTimeout(timer);
    timer = setTimeout(() => {
      if (!selectedAfterLogout || submitted || !identifier.value.trim() || !password.value || !isAutofilled(password) || !form.checkValidity()) return;
      form.requestSubmit();
    }, 200);
  }
  form.addEventListener('submit', event => {
    if (submitted) { event.preventDefault(); return; }
    submitted = true;
    const button = form.querySelector('button[type="submit"]');
    button.textContent = 'Signing in…';
    button.disabled = true;
  });
  form.addEventListener('animationstart', event => { if (event.animationName === 'savedCredentialFilled') check(); });
  form.addEventListener('input', check);
  form.addEventListener('change', check);
  window.addEventListener('pageshow', event => {
    // Back navigation must not immediately resubmit cached credentials.
    if (event.persisted) { window.location.reload(); return; }
    check();
  });
  check();
})();
