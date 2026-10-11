/* Shared navigation, theme and one authenticated Socket.IO connection per page. */
(function () {
  'use strict';
  try {
    const theme = localStorage.getItem('epocash-theme');
    if (theme === 'dark' || theme === 'light') document.documentElement.dataset.theme = theme;
  } catch (_) { /* Storage may be disabled. The server theme still works. */ }
  let socket;
  let dirty = false;
  let refreshTimer;
  window.refreshAmlPage = function () {
    if (!dirty) {
      clearTimeout(refreshTimer);
      refreshTimer = setTimeout(() => { if (!dirty) location.reload(); }, 400);
      return;
    }
    if (document.querySelector('.refresh-notice')) return;
    const notice = document.createElement('div');
    notice.className = 'refresh-notice';
    notice.setAttribute('role', 'status');
    notice.textContent = 'New case data is available. Your unsaved notes are preserved. ';
    const button = document.createElement('button');
    button.textContent = 'Refresh';
    button.onclick = () => { if (confirm('Discard unsaved changes and refresh?')) location.reload(); };
    notice.appendChild(button);
    document.body.appendChild(notice);
  };
  window.getAmlSocket = function () {
    if (document.body.dataset.authenticated !== 'true' || !window.io) return null;
    if (!socket) {
      socket = window.io({ transports: ['websocket', 'polling'] });
      const heartbeat = window.setInterval(() => {
        if (socket.connected) socket.emit('heartbeat');
      }, 30000);
      window.addEventListener('pagehide', () => { clearInterval(heartbeat); socket.disconnect(); }, { once: true });
    }
    return socket;
  };
  document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('input', (event) => { if (event.target.closest('form')) dirty = true; });
    const sidebar = document.getElementById('page-sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (sidebar) {
      const setOpen = (open) => {
        sidebar.classList.toggle('open', open);
        overlay?.classList.toggle('active', open);
        document.getElementById('sidebar-toggle')?.setAttribute('aria-expanded', String(open));
      };
      window.__amlSidebarController = {
        toggle: () => setOpen(!sidebar.classList.contains('open')),
        close: () => setOpen(false),
      };
      overlay?.addEventListener('click', () => setOpen(false));
    }
    const toggle = document.getElementById('sidebar-toggle');
    toggle?.addEventListener('click', () => {
      if (window.__amlSidebarController) window.__amlSidebarController.toggle();
      else window.dispatchEvent(new CustomEvent('sidebar-toggle-click'));
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') window.__amlSidebarController?.close();
    });
    const top = document.getElementById('back-to-top');
    window.addEventListener('scroll', () => top?.classList.toggle('visible', window.scrollY > 400), { passive: true });
    top?.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
    const badge = document.getElementById('messageBadge');
    async function updateBadge() {
      if (!badge) return;
      try {
        const response = await fetch('/api/unread-count');
        if (!response.ok) return;
        const data = await response.json();
        const count = data.unread?.total_unread || 0;
        badge.textContent = String(count);
        badge.hidden = count === 0;
      } catch (_) { /* Keep the last known count during a connection outage. */ }
    }
    if (badge) {
      updateBadge();
      const connection = window.getAmlSocket();
      ['connect', 'unread_update', 'new_message'].forEach((name) => connection?.on(name, updateBadge));
    }
    // Existing dynamic forms use adjacent labels. Associate them for keyboards and screen readers.
    function labelFields() {
      document.querySelectorAll('label:not([for])').forEach((label, index) => {
        const field = label.nextElementSibling;
        if (field?.matches('input, select, textarea')) {
          if (!field.id) field.id = 'field-' + (field.name || 'input') + '-' + index;
          label.htmlFor = field.id;
        }
      });
      const aside = document.querySelector('.admin-sidebar');
      toggle?.setAttribute('aria-expanded', String(Boolean(aside?.classList.contains('open'))));
    }
    labelFields();
    new MutationObserver(labelFields).observe(document.getElementById('main-content'), { childList: true, subtree: true });
  });
}());
