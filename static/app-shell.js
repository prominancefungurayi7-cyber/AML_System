/* Shared navigation, theme and one authenticated Socket.IO connection per page. */
(function () {
  'use strict';
  try {
    const theme = localStorage.getItem('epocash-theme');
    if (theme === 'dark' || theme === 'light') document.documentElement.dataset.theme = theme;
  } catch (_) { /* Storage may be disabled. The server theme still works. */ }
  let socket;
  const notices = new Map();
  function notificationKind(message, category) {
    if (['success', 'error', 'info'].includes(category)) return category;
    const value = String(message).toLowerCase();
    if (/\b(failed|failure|error|invalid|denied|expired|insufficient|disabled|cannot|could not|not found|required|must|mismatch|locked|attention|unavailable|reserved|taken)\b|do not match|try again|already registered|^no customer accounts|^no active agents|^need at least|^too many/.test(value)) return 'error';
    if (/\b(successfully|success|sent|saved|created|welcome|resolved|submitted|updated|recorded|generated|filed|added|completed)\b|signed out|up to date/.test(value)) return 'success';
    return 'info';
  }
  window.showAmlNotification = function (message, key = Symbol('notification'), category) {
    if (!message || !document.body) return;
    notices.get(key)?.();
    let region = document.getElementById('notification-region');
    if (!region) {
      region = document.createElement('div');
      region.id = 'notification-region';
      region.className = 'notification-region';
      region.setAttribute('aria-live', 'polite');
      region.setAttribute('aria-relevant', 'additions');
      document.body.appendChild(region);
    }
    const notice = document.createElement('div');
    const kind = notificationKind(message, category);
    notice.className = `notification-toast notification-toast--${kind}`;
    if (kind !== 'info') {
      const icon = document.createElement('span');
      icon.className = 'notification-status-icon';
      icon.setAttribute('aria-hidden', 'true');
      icon.textContent = kind === 'success' ? '\u2713' : '\u00d7';
      notice.appendChild(icon);
    }
    const text = document.createElement('p');
    text.textContent = String(message);
    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'notification-close';
    close.setAttribute('aria-label', 'Dismiss notification');
    close.textContent = '×';
    let fadeTimer, removeTimer;
    const dismiss = () => {
      clearTimeout(fadeTimer);
      clearTimeout(removeTimer);
      notice.remove();
      notices.delete(key);
    };
    close.addEventListener('click', dismiss);
    notice.append(text, close);
    region.appendChild(notice);
    notices.set(key, dismiss);
    while (notices.size > 3) notices.values().next().value();
    // Fade during the final 300 ms; fully removed four seconds after arrival.
    fadeTimer = setTimeout(() => notice.classList.add('is-leaving'), 3700);
    removeTimer = setTimeout(dismiss, 4000);
    return notice;
  };
  window.showAmlMessageNotification = function (event) {
    if (!event || !event.sender || event.sender === document.body.dataset.username) return;
    const notice = window.showAmlNotification('New message', `message:${event.id || Date.now()}`, 'info');
    if (!notice) return;
    notice.classList.add('notification-toast--message');
    const text = notice.querySelector('p');
    text.textContent = '';
    const sender = document.createElement('strong');
    sender.textContent = String(event.sender);
    const preview = document.createElement('span');
    preview.textContent = String(event.content || 'New message').slice(0, 120);
    text.append(sender, preview);
    const avatar = document.createElement('span');
    avatar.className = 'notification-message-avatar';
    avatar.setAttribute('aria-hidden', 'true');
    avatar.textContent = String(event.sender).slice(0, 1).toUpperCase();
    notice.prepend(avatar);
    notice.addEventListener('click', (click) => {
      if (click.target.closest('.notification-close')) return;
      location.href = `/messages?contact=${encodeURIComponent(event.sender)}`;
    });
    notice.setAttribute('role', 'link');
    notice.setAttribute('tabindex', '0');
    notice.addEventListener('keydown', (key) => {
      if (key.key === 'Enter') location.href = `/messages?contact=${encodeURIComponent(event.sender)}`;
    });
    if (document.hidden && 'Notification' in window && Notification.permission === 'granted') {
      try {
        const options = {
          body: String(event.content || 'New message').slice(0, 120),
          icon: '/static/favicon.svg',
          tag: `epocash-message-${event.id}`,
          data: { contact: event.sender },
        };
        if ('serviceWorker' in navigator) {
          navigator.serviceWorker.register('/static/message-notifications-sw.js')
            .then(async registration => {
              if (!registration.active) {
                const worker = registration.installing || registration.waiting;
                if (!worker) throw new Error('Notification worker is unavailable');
                await new Promise((resolve, reject) => {
                  const timer = setTimeout(() => reject(new Error('Notification worker timed out')), 5000);
                  worker.addEventListener('statechange', () => {
                    if (worker.state === 'activated') { clearTimeout(timer); resolve(); }
                    if (worker.state === 'redundant') { clearTimeout(timer); reject(new Error('Notification worker failed')); }
                  });
                  if (worker.state === 'activated') { clearTimeout(timer); resolve(); }
                });
              }
              await registration.showNotification(`Message from ${event.sender}`, options);
              setTimeout(async () => {
                const shown = await registration.getNotifications({ tag: options.tag });
                shown.forEach(notification => notification.close());
              }, 4000);
            })
            .catch(() => {
              try {
                const fallback = new Notification(`Message from ${event.sender}`, options);
                fallback.onclick = () => {
                  window.focus();
                  location.href = `/messages?contact=${encodeURIComponent(event.sender)}`;
                  fallback.close();
                };
                setTimeout(() => fallback.close(), 4000);
              } catch (_) { /* Some mobile browsers require the worker notification. */ }
            });
        } else {
          const notification = new Notification(`Message from ${event.sender}`, options);
          notification.onclick = () => {
            window.focus();
            location.href = `/messages?contact=${encodeURIComponent(event.sender)}`;
            notification.close();
          };
          setTimeout(() => notification.close(), 4000);
        }
      } catch (_) { /* In-app notice remains available when OS alerts fail. */ }
    }
  };
  let dirty = false;
  let refreshTimer;
  let navigationOpen = false;
  let navigationPinned = false;
  const navigationListeners = new Set();
  function syncNavigation() {
    const aside = document.querySelector('.admin-sidebar');
    if (aside) {
      aside.classList.toggle('open', navigationOpen);
      aside.inert = !navigationOpen;
      aside.setAttribute('aria-hidden', String(!navigationOpen));
    }
    document.getElementById('sidebar-toggle')?.setAttribute('aria-expanded', String(navigationOpen));
    document.getElementById('sidebar-overlay')?.classList.toggle('active', navigationOpen);
  }
  function setNavigation(open) {
    navigationOpen = open;
    if (!open) navigationPinned = false;
    navigationListeners.forEach(handler => handler(open));
    syncNavigation();
  }
  window.__amlSidebarController = {
    register(handler) {
      navigationListeners.add(handler);
      handler(navigationOpen);
      return () => navigationListeners.delete(handler);
    },
    open: () => setNavigation(true),
    close: () => setNavigation(false),
    toggle: () => setNavigation(!navigationOpen),
  };
  window.refreshAmlPage = function () {
    if (document.getElementById('messagingWorkspace')) {
      window.dispatchEvent(new Event('aml:messages-resync'));
      return;
    }
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
      socket = window.io({ transports: ['polling', 'websocket'] });
      let hasConnected = false;
      socket.on('connect', () => {
        if (hasConnected) window.refreshAmlPage();
        hasConnected = true;
      });
      socket.on('realtime_resync', () => window.refreshAmlPage());
      socket.on('customer_refresh', () => {
        if (document.body.dataset.userRole === 'customer') window.refreshAmlPage();
      });
      socket.on('new_message', event => {
        if (event.sender !== document.body.dataset.username) {
          socket.emit('message_received', { message_id: event.id });
          window.showAmlMessageNotification(event);
        }
      });
      if (['admin', 'compliance'].includes(document.body.dataset.userRole)) {
        socket.on('alert', event => window.showAmlNotification(
          `AML alert #${event.id || ''} is available for review.`, `alert:${event.id}`));
        socket.on('alert_update', event => window.showAmlNotification(
          `Alert #${event.id || ''} updated${event.status ? ': ' + event.status : ''}.`, `alert:${event.id}`));
        socket.on('transaction_batch', event => window.showAmlNotification(
          `${Number(event.count) || 0} transactions saved.`, 'transaction-batch'));
      }
      const heartbeat = window.setInterval(() => {
        if (socket.connected) socket.emit('heartbeat');
      }, 30000);
      window.addEventListener('pagehide', () => { clearInterval(heartbeat); socket.disconnect(); }, { once: true });
      window.addEventListener('pageshow', event => {
        if (event.persisted) window.refreshAmlPage();
      });
    }
    return socket;
  };
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.flash-messages').forEach(list => {
      list.querySelectorAll('li').forEach(item => window.showAmlNotification(
        item.textContent, Symbol('flash'), item.dataset.category));
      list.remove();
    });
    document.addEventListener('input', (event) => { if (event.target.closest('form')) dirty = true; });
    const overlay = document.getElementById('sidebar-overlay');
    overlay?.addEventListener('click', () => setNavigation(false));
    const toggle = document.getElementById('sidebar-toggle');
    let closeTimer;
    let openedByHover = false;
    let keyboardNavigation = false;
    const cancelClose = () => clearTimeout(closeTimer);
    const scheduleClose = () => {
      cancelClose();
      closeTimer = setTimeout(() => {
        if (navigationPinned) return;
        const aside = document.querySelector('.admin-sidebar');
        if (aside?.matches(':hover') || toggle?.matches(':hover')) return;
        if (keyboardNavigation && aside?.contains(document.activeElement)) return;
        setNavigation(false);
      }, 250);
    };
    toggle?.addEventListener('click', () => {
      cancelClose();
      if (openedByHover || !navigationOpen) {
        navigationPinned = true;
        setNavigation(true);
      } else {
        setNavigation(false);
      }
      openedByHover = false;
    });
    toggle?.addEventListener('pointerenter', event => {
      if (event.pointerType === 'mouse' && matchMedia('(hover: hover)').matches) {
        cancelClose();
        openedByHover = !navigationOpen;
        setNavigation(true);
      }
    });
    toggle?.addEventListener('pointerleave', event => {
      if (event.pointerType === 'mouse') scheduleClose();
    });
    document.addEventListener('pointerover', event => {
      if (event.target.closest('.admin-sidebar')) cancelClose();
    });
    document.addEventListener('pointerout', event => {
      const aside = event.target.closest('.admin-sidebar');
      if (event.pointerType === 'mouse' && aside && !aside.contains(event.relatedTarget)) scheduleClose();
    });
    document.addEventListener('pointerdown', event => {
      keyboardNavigation = false;
      if (!event.target.closest('.admin-sidebar, #sidebar-toggle')) {
        cancelClose();
        setNavigation(false);
      }
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Tab') keyboardNavigation = true;
      if (event.key === 'Escape') {
        cancelClose();
        const returnFocus = document.querySelector('.admin-sidebar')?.contains(document.activeElement);
        setNavigation(false);
        if (returnFocus) toggle?.focus();
      }
    });
    document.addEventListener('focusout', event => {
      if (event.target.closest('.admin-sidebar') && !event.relatedTarget?.closest('.admin-sidebar, #sidebar-toggle')) scheduleClose();
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
      syncNavigation();
    }
    labelFields();
    new MutationObserver(labelFields).observe(document.getElementById('main-content'), { childList: true, subtree: true });
  });
}());
