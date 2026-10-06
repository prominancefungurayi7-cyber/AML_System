(function () {
  'use strict';
  function wording(row) {
    if (row.status === 'pending') return 'V4 inference pending.';
    if (row.status !== 'success') return 'V4 inference unavailable.';
    if (row.decision === 'suspicious_pattern') return 'Suspicious transaction pattern detected — requires analyst review.';
    if (row.decision === 'normal') return 'No suspicious pattern detected by V4.';
    return 'V4 inference unavailable.';
  }
  // Pure presentation helper also available to the local rendering tests.
  if (typeof module !== 'undefined') module.exports = { wording: wording };
  if (typeof document === 'undefined') return;
  const panel = document.getElementById('v4-shadow-panel');
  if (!panel) return;
  const state = document.getElementById('v4-shadow-state');
  const list = document.getElementById('v4-shadow-results');
  let busy = false;
  async function refresh() {
    if (busy) return;
    busy = true;
    try {
      const response = await fetch('/api/v4-shadow/results', { credentials: 'same-origin', cache: 'no-store' });
      if (!response.ok) throw new Error('unavailable');
      const data = await response.json();
      list.replaceChildren();
      for (const row of data.results) {
        const item = document.createElement('p');
        const probability = row.status === 'success' && Number.isFinite(row.suspicious_probability)
          ? String(row.suspicious_probability) : 'unavailable';
        // ID remains a decimal string: never coerce it to a JavaScript number.
        item.textContent = 'Transaction ' + row.transaction_id + ': ' + wording(row) +
          ' Status: ' + row.status + ' | Decision: ' + row.decision +
          ' | Suspicious probability: ' + probability + ' | Threshold: ' + row.threshold +
          ' | Model: ' + row.model_version + ' | Features: ' + row.feature_version +
          ' | Inference time: ' + (row.inference_timestamp || 'pending');
        list.appendChild(item);
      }
      state.textContent = data.results.length ? 'Latest 50 persisted shadow results. Legacy operational risk is unchanged.' : 'No V4 shadow results yet.';
    } catch (_) { state.textContent = 'V4 inference unavailable.'; }
    finally { busy = false; }
  }
  refresh();
  // Durable GET refresh is the recovery path for missed notifications.
  window.addEventListener('focus', refresh);
  if (typeof window.io === 'function') {
    const socket = window.io({ transports: ['websocket', 'polling'] });
    socket.on('connect', function () { socket.emit('v4_shadow_subscribe'); refresh(); });
    socket.on('v4_shadow_result', refresh);
    window.addEventListener('pagehide', function () { socket.disconnect(); }, { once: true });
  }
}());
