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
  const filter = document.getElementById('v4-result-filter');
  let busy = false;
  let actionPending = false;
  let refreshPending = false;
  const retryKeys = new Map();
  async function retryAnalysis(row, button) {
    if (actionPending) return;
    actionPending = true;
    button.disabled = true;
    try {
      const base = '/compliance/v4-error/' + encodeURIComponent(row.transaction_id);
      const response = await fetch(base, { credentials: 'same-origin', cache: 'no-store' });
      if (!response.ok) throw new Error('Unable to open the analysis error. Check your session.');
      const details = await response.json();
      if (details.case_closed || details.effective_ai_state !== 'inference_error') {
        window.showAmlNotification('This analysis error has already been resolved or closed.', 'analysis-retry', 'success');
        return;
      }
      if (!window.confirm('Retry V4 analysis for transaction ' + row.transaction_id + '? The committed payment and balances will not be repeated.')) return;
      if (!retryKeys.has(row.transaction_id)) retryKeys.set(row.transaction_id, crypto.randomUUID());
      const body = new URLSearchParams({ csrf_token: details.csrf_token, request_key: retryKeys.get(row.transaction_id) });
      button.textContent = 'Analysing…';
      const result = await fetch(base + '/retry', { method: 'POST', body, credentials: 'same-origin' });
      const data = await result.json();
      if (!result.ok) throw new Error(data.error || 'Analysis retry unavailable.');
      retryKeys.delete(row.transaction_id);
      window.showAmlNotification(data.status === 'success' ? 'V4 analysis completed.' : 'Analysis remains unresolved: ' + (data.error_code || data.status), 'analysis-retry', data.status === 'success' ? 'success' : 'error');
    } catch (error) {
      window.showAmlNotification(error.message, 'analysis-retry', 'error');
    } finally {
      actionPending = false;
      button.disabled = false;
      button.textContent = 'Review / Retry Analysis';
      await refresh();
    }
  }
  async function refresh() {
    if (busy || actionPending) { refreshPending = true; return; }
    busy = true;
    refreshPending = false;
    const errorsOnly = filter && filter.value === 'errors';
    try {
      const response = await fetch('/api/v4-shadow/results' + (errorsOnly ? '?errors=1' : ''), { credentials: 'same-origin', cache: 'no-store' });
      if (!response.ok) throw new Error('unavailable');
      const data = await response.json();
      // A filter change during the request must not display the previous queue.
      if (Boolean(filter && filter.value === 'errors') !== Boolean(errorsOnly)) {
        refreshPending = true;
        return;
      }
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
        if (row.status === 'inference_error') {
          const button = document.createElement('button');
          button.type = 'button';
          button.textContent = 'Review / Retry Analysis';
          button.onclick = () => retryAnalysis(row, button);
          item.appendChild(button);
        }
      }
      state.textContent = errorsOnly
        ? (data.results.length ? 'Up to 50 unresolved analysis errors. Review a case before retrying.' : 'No unresolved analysis errors.')
        : (data.results.length ? 'Latest 50 persisted V4 results. Independent rule evidence remains on each case.' : 'No V4 decisions recorded yet. Historical alerts are shown above.');
    } catch (_) { state.textContent = 'V4 inference unavailable.'; }
    finally {
      busy = false;
      if (refreshPending && !actionPending) await refresh();
    }
  }
  refresh();
  if (filter) filter.onchange = refresh;
  // Durable GET refresh is the recovery path for missed notifications.
  window.addEventListener('focus', refresh);
  if (typeof window.io === 'function') {
    const socket = window.getAmlSocket();
    if (socket) {
      const subscribe = function () { socket.emit('v4_shadow_subscribe'); refresh(); };
      socket.on('connect', subscribe);
      socket.on('v4_shadow_result', refresh);
      socket.on('transaction', refresh);
      if (socket.connected) subscribe();
    }
  }
}());
