/* Private conversations: persisted history, per-contact drafts and socket delivery. */
(() => {
  'use strict';
  const socket = window.getAmlSocket();
  const currentUser = document.body.dataset.username;
  const drafts = new Map();
  const attachmentDrafts = new Map();
  const visibleMessages = new Map();
  const receiptUpdates = new Map();
  const receiptRank = { sent: 0, delivered: 1, read: 2 };
  let lastReadId = 0;
  let unreadBoundary = null;
  let contacts = [], conversations = [], receiver = '', conversationId = null;
  let pending = null, generation = 0, oldestId = null, moreHistory = false, typingTimer;
  let draftPreviewUrl = null;
  const attachmentTypes = new Set(['png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'txt', 'csv', 'docx', 'xlsx', 'pptx']);
  const imageTypes = new Set(['image/png', 'image/jpeg', 'image/gif', 'image/webp']);
  const el = id => document.getElementById(id);
  const notify = message => window.showAmlNotification(message, 'messaging-error', 'error');

  function attachmentRequestId() {
    if (typeof crypto.randomUUID === 'function') return crypto.randomUUID();
    const bytes = crypto.getRandomValues(new Uint8Array(16));
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    const hex = Array.from(bytes, value => value.toString(16).padStart(2, '0')).join('');
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
  }

  function formatSize(size) {
    return size < 1024 ? `${size} B` : size < 1024 * 1024 ? `${(size / 1024).toFixed(1)} KB` : `${(size / (1024 * 1024)).toFixed(1)} MB`;
  }
  function attachmentUrl(value) {
    try {
      const url = new URL(value, location.origin);
      return url.origin === location.origin && /^\/api\/messages\/\d+\/attachment$/.test(url.pathname) ? url.href : null;
    } catch (_) { return null; }
  }
  function showAttachmentDraft() {
    if (draftPreviewUrl) URL.revokeObjectURL(draftPreviewUrl);
    draftPreviewUrl = null;
    const draft = attachmentDrafts.get(receiver);
    el('attachmentDraft').hidden = !draft;
    el('attachmentDraftImage').hidden = true;
    if (!draft) return;
    el('attachmentDraftName').textContent = draft.file.name;
    el('attachmentDraftSize').textContent = formatSize(draft.file.size);
    if (imageTypes.has(draft.file.type)) {
      draftPreviewUrl = URL.createObjectURL(draft.file);
      el('attachmentDraftImage').src = draftPreviewUrl;
      el('attachmentDraftImage').hidden = false;
    }
  }
  function selectAttachment(files) {
    if (!receiver || !files?.length) return;
    if (files.length !== 1) { notify('Attach one file per message.'); return; }
    const file = files[0];
    const extension = file.name.split('.').pop().toLowerCase();
    if (!attachmentTypes.has(extension)) { notify('Use a PNG, JPEG, GIF, WebP, PDF, text, CSV, DOCX, XLSX or PPTX file.'); return; }
    if (!file.size || file.size > 10 * 1024 * 1024) { notify('Choose a nonempty file no larger than 10 MB.'); return; }
    attachmentDrafts.set(receiver, { file, requestId: attachmentRequestId(), content: null });
    showAttachmentDraft();
    el('messageInput').focus();
  }
  function appendAttachment(bubble, attachment) {
    const url = attachmentUrl(attachment.url);
    if (!url) { bubble.textContent = 'Attachment unavailable.'; return; }
    bubble.classList.add('message-bubble--attachment');
    const preview = attachmentUrl(attachment.preview_url);
    if (imageTypes.has(attachment.media_type) && preview) {
      const imageLink = document.createElement('a'); imageLink.href = preview;
      imageLink.target = '_blank'; imageLink.rel = 'noopener'; imageLink.setAttribute('aria-label', `Open image: ${attachment.name}`);
      const image = document.createElement('img'); image.className = 'message-attachment-image';
      image.src = preview; image.alt = attachment.name; image.loading = 'lazy';
      imageLink.append(image); bubble.append(imageLink);
    }
    const link = document.createElement('a'); link.href = url; link.download = attachment.name;
    link.className = 'message-attachment-card'; link.setAttribute('aria-label', `Download ${attachment.name}`);
    const icon = document.createElement('span'); icon.className = 'message-attachment-icon'; icon.setAttribute('aria-hidden', 'true');
    icon.textContent = attachment.name.split('.').pop().toUpperCase().slice(0, 5);
    const details = document.createElement('span'); details.className = 'message-attachment-details';
    const name = document.createElement('span'); name.className = 'message-attachment-name'; name.textContent = attachment.name;
    const size = document.createElement('span'); size.className = 'message-attachment-size'; size.textContent = formatSize(attachment.size);
    const download = document.createElement('span'); download.className = 'message-attachment-download'; download.setAttribute('aria-hidden', 'true'); download.textContent = '\u2193';
    details.append(name, size); link.append(icon, details, download); bubble.append(link);
  }

  function mergeMessage(message) {
    const previous = visibleMessages.get(message.id);
    const merged = { ...previous, ...message };
    if (merged.sender === currentUser) {
      // Socket receipts may arrive before a send acknowledgement or HTTP history.
      // Older snapshots must never turn read/delivered ticks back to sent.
      const statuses = [previous?.status, message.status, receiptUpdates.get(message.id),
        message.id <= lastReadId ? 'read' : 'sent'];
      merged.status = statuses.reduce((best, status) =>
        (receiptRank[status] ?? -1) > receiptRank[best] ? status : best, 'sent');
      receiptUpdates.delete(message.id);
    }
    visibleMessages.set(message.id, merged);
  }

  function contactsOpen(open) {
    el('messagingWorkspace').classList.toggle('contacts-open', open);
    el('contactsRail').inert = !open;
    el('contactsRail').setAttribute('aria-hidden', String(!open));
    el('openContacts').setAttribute('aria-expanded', String(open));
  }
  async function getJSON(url) {
    const response = await fetch(url);
    if (!response.ok || !response.headers.get('content-type')?.includes('application/json')) throw new Error('Unable to load messages. Check your connection and sign-in.');
    const data = await response.json();
    if (data.status !== 'success') throw new Error(data.message || 'Unable to load messages.');
    return data;
  }
  async function refreshContacts() {
    const [people, threads] = await Promise.all([getJSON('/api/messageable-users'), getJSON('/api/conversations')]);
    contacts = people.users || []; conversations = threads.conversations || [];
    renderContacts();
  }
  function renderContacts() {
    const list = el('conversationsList'); list.replaceChildren();
    for (const contact of contacts) {
      const thread = conversations.find(item => item.other_participant === contact.username);
      const item = document.createElement('li');
      item.className = `conversation-item modern-thread ${receiver === contact.username ? 'active' : ''}`;
      item.tabIndex = 0; item.setAttribute('role', 'button');
      const avatar = document.createElement('div'); avatar.className = `conversation-avatar ${contact.is_online ? 'online' : ''}`;
      avatar.textContent = contact.username.slice(0, 2).toUpperCase();
      const info = document.createElement('div'); info.className = 'conversation-info';
      const name = document.createElement('div'); name.className = 'conversation-name';
      name.textContent = contact.account_number ? `${contact.username} (${contact.account_number})` : contact.username;
      const preview = document.createElement('div'); preview.className = 'conversation-preview';
      preview.textContent = thread?.content || thread?.attachment?.name || 'Start a secure conversation';
      info.append(name, preview); item.append(avatar, info);
      if (thread?.unread_count) {
        const badge = document.createElement('span'); badge.className = 'unread-badge'; badge.textContent = thread.unread_count; item.append(badge);
      }
      item.onclick = () => openContact(contact);
      item.onkeydown = event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); openContact(contact); } };
      list.append(item);
    }
    if (!contacts.length) list.textContent = 'No messaging contacts are available.';
  }
  async function openContact(contact) {
    if (receiver) drafts.set(receiver, el('messageInput').value);
    if (conversationId) socket?.emit('stop_typing', { conversation_id: conversationId });
    generation++; receiver = contact.username;
    conversationId = conversations.find(item => item.other_participant === receiver)?.id || null;
    visibleMessages.clear(); receiptUpdates.clear(); lastReadId = 0;
    oldestId = null; moreHistory = false; unreadBoundary = null;
    el('messageInput').value = drafts.get(receiver) || '';
    showAttachmentDraft();
    el('chatArea').hidden = true; el('chatContent').hidden = false;
    el('chatTitle').textContent = contact.username;
    el('chatAccount').textContent = contact.account_number || '';
    el('chatAvatar').textContent = contact.username.slice(0, 2).toUpperCase();
    el('userStatus').textContent = contact.is_online ? 'Online' : 'Offline';
    el('statusIndicator').className = `status-indicator ${contact.is_online ? '' : 'offline'}`;
    contactsOpen(false); renderContacts(); renderMessages();
    el('messageInput').focus();
    if (conversationId) await loadHistory(false, true);
  }
  async function loadHistory(older, opening = false) {
    const selected = conversationId, version = generation;
    if (!selected) return;
    const cursor = older && oldestId ? `?before_id=${oldestId}` : '';
    try {
      const data = await getJSON(`/api/conversations/${selected}/messages${cursor}`);
      if (version !== generation || selected !== conversationId) return;
      // Find the actual unread boundary even when it lies before the latest page.
      let earliestPage = data.messages;
      if (opening && data.messages.some(m => m.receiver_username === currentUser && m.status !== 'read')) {
        while (earliestPage.length === 50 && !earliestPage.some(m => m.receiver_username === currentUser && m.status === 'read')) {
          const before = Math.min(...earliestPage.map(m => m.id));
          const earlier = await getJSON(`/api/conversations/${selected}/messages?before_id=${before}`);
          if (version !== generation || selected !== conversationId) return;
          earliestPage = earlier.messages;
          data.messages.push(...earliestPage);
        }
        const unread = data.messages.filter(m => m.receiver_username === currentUser && m.status !== 'read');
        unreadBoundary = Math.min(...unread.map(m => m.id));
      }
      for (const message of data.messages) mergeMessage({
        ...message, sender: message.sender_username, timestamp: message.created_at
      });
      for (const message of data.messages) {
        if (message.receiver_username === currentUser && message.status === 'sent')
          socket?.emit('message_received', { message_id: message.id });
      }
      if (older || oldestId === null) {
        oldestId = data.messages.length ? Math.min(...data.messages.map(m => m.id)) : oldestId;
        moreHistory = earliestPage.length === 50;
      }
      renderMessages(older ? 'prepend' : opening ? 'opening' : false);
      if (!older && !document.hidden) socket?.emit('mark_read', { conversation_id: selected });
    } catch (error) { if (version === generation) notify(error.message); }
  }
  function renderMessages(scroll = true) {
    const container = el('messagesContainer');
    const previousHeight = container.scrollHeight;
    const previousTop = container.scrollTop;
    container.replaceChildren();
    if (moreHistory) {
      const older = document.createElement('button'); older.type = 'button'; older.textContent = 'Load earlier messages';
      older.onclick = () => { older.disabled = true; loadHistory(true).finally(() => { older.disabled = false; }); };
      container.append(older);
    }
    for (const message of [...visibleMessages.values()].sort((a, b) => a.id - b.id)) {
      if (message.id === unreadBoundary) {
        const divider = document.createElement('div');
        divider.className = 'unread-messages-divider';
        divider.setAttribute('role', 'separator');
        divider.setAttribute('aria-label', 'Unread Messages');
        divider.textContent = 'Unread Messages';
        container.append(divider);
      }
      const group = document.createElement('div'); group.dataset.messageId = message.id;
      group.className = `message-group ${message.sender === currentUser ? 'sent' : 'received'}`;
      const content = document.createElement('div'), bubble = document.createElement('div'), time = document.createElement('div');
      bubble.className = 'message-bubble';
      if (message.attachment) {
        appendAttachment(bubble, message.attachment);
        if (message.content) {
          const caption = document.createElement('div'); caption.className = 'message-attachment-caption';
          caption.textContent = message.content; bubble.append(caption);
        }
      } else bubble.textContent = message.content;
      time.className = 'message-time';
      time.textContent = new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      if (message.sender === currentUser) {
        const receipt = document.createElement('span');
        const status = message.status === 'read' ? 'read' : message.status === 'delivered' ? 'delivered' : 'sent';
        receipt.className = `message-receipt message-receipt--${status}`;
        receipt.setAttribute('role', 'img');
        receipt.setAttribute('aria-label', status === 'read' ? 'Read' : status === 'delivered' ? 'Delivered' : 'Sent');
        receipt.title = receipt.getAttribute('aria-label');
        receipt.textContent = status === 'sent' ? '\u2713' : '\u2713\u2713';
        time.append(receipt);
      }
      content.append(bubble, time); group.append(content); container.append(group);
    }
    if (!visibleMessages.size) container.textContent = 'No messages in this conversation yet.';
    if (scroll === 'opening' && unreadBoundary !== null) {
      const divider = container.querySelector('.unread-messages-divider');
      container.scrollTop = divider ? divider.getBoundingClientRect().top - container.getBoundingClientRect().top + container.scrollTop - 48 : container.scrollHeight;
    } else if (scroll === 'prepend') {
      container.scrollTop = previousTop + container.scrollHeight - previousHeight;
    } else {
      container.scrollTop = scroll ? container.scrollHeight : previousTop;
    }
  }
  function receive(message) {
    const other = message.sender === currentUser ? message.receiver : message.sender;
    if (!contacts.some(contact => contact.username === other)) return;
    if (other === receiver) {
      conversationId = message.conversation_id;
      mergeMessage(message); renderMessages();
      if (message.sender !== currentUser && !document.hidden) socket?.emit('mark_read', { conversation_id: conversationId });
    }
  }
  function send() {
    const input = el('messageInput'), text = input.value.trim();
    const attachment = attachmentDrafts.get(receiver);
    if (!receiver || (!text && !attachment) || pending) return;
    if (!socket?.connected) { notify('Messaging is disconnected. Your draft is preserved.'); return; }
    if (text.length > 10000) { notify('Message must contain at most 10,000 characters.'); return; }
    if (attachment) { sendAttachment(attachment, text); return; }
    const attempt = { receiver, text }; pending = attempt;
    el('sendButton').disabled = true;
    const finish = () => { if (pending === attempt) { pending = null; el('sendButton').disabled = false; } };
    const timer = setTimeout(() => {
      if (pending !== attempt) return;
      finish(); notify('Delivery is unconfirmed. Check conversation history before retrying.');
      resync();
    }, 10000);
    socket.emit('send_message', { receiver, content: text }, result => {
      clearTimeout(timer);
      if (result?.status === 'success') {
        if (receiver === attempt.receiver && input.value.trim() === text) input.value = '';
        if (drafts.get(attempt.receiver)?.trim() === text) drafts.delete(attempt.receiver);
        if (result.message) receive(result.message);
        if (conversationId) socket.emit('stop_typing', { conversation_id: conversationId });
        refreshContacts().catch(error => notify(error.message));
      } else notify(result?.message || 'Message could not be sent. Your draft is preserved.');
      finish();
    });
  }
  async function sendAttachment(attachment, text) {
    if (attachment.content !== null && attachment.content !== text) attachment.requestId = attachmentRequestId();
    attachment.content = text;
    const attempt = { receiver, text, file: attachment.file, requestId: attachment.requestId };
    pending = attempt; el('sendButton').disabled = true;
    el('attachmentUploadStatus').textContent = `Sending ${attempt.file.name}...`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 30000);
    try {
      const data = new FormData();
      data.append('receiver', attempt.receiver); data.append('content', text);
      data.append('file', attempt.file); data.append('client_request_id', attempt.requestId);
      data.append('csrf_token', el('messagingWorkspace').dataset.messageAttachmentCsrf);
      const response = await fetch('/api/message-attachments', { method: 'POST', body: data, signal: controller.signal });
      if (response.status === 401 || (response.redirected && new URL(response.url).pathname === '/login')) {
        location.assign('/login'); return;
      }
      if (!response.headers.get('content-type')?.includes('application/json')) throw new Error('Attachment could not be sent. Your draft is preserved.');
      const result = await response.json();
      if (!response.ok || result.status !== 'success') throw new Error(result.message || 'Attachment could not be sent. Your draft is preserved.');
      const saved = attachmentDrafts.get(attempt.receiver);
      const currentCaption = receiver === attempt.receiver ? el('messageInput').value.trim() : (drafts.get(attempt.receiver) || '').trim();
      const matchingDraft = saved?.file === attempt.file && saved.requestId === attempt.requestId && currentCaption === text;
      if (matchingDraft) attachmentDrafts.delete(attempt.receiver);
      if (receiver === attempt.receiver) {
        if (matchingDraft && el('messageInput').value.trim() === text) el('messageInput').value = '';
        showAttachmentDraft();
      }
      if (matchingDraft && drafts.get(attempt.receiver)?.trim() === text) drafts.delete(attempt.receiver);
      if (result.message) receive(result.message);
      if (conversationId) socket?.emit('stop_typing', { conversation_id: conversationId });
      refreshContacts().catch(error => notify(error.message));
    } catch (error) {
      notify(error.name === 'AbortError' ? 'Upload is unconfirmed. Your draft is preserved; retry to check the same message.' : error.message || 'Attachment could not be sent. Your draft is preserved.');
    } finally {
      clearTimeout(timer);
      if (pending === attempt) { pending = null; el('sendButton').disabled = false; el('attachmentUploadStatus').textContent = ''; }
    }
  }
  async function resync() {
    try {
      await refreshContacts();
      if (receiver) {
        conversationId = conversations.find(item => item.other_participant === receiver)?.id || conversationId;
        await loadHistory(false);
      }
    } catch (error) { notify(error.message); }
  }
  window.addEventListener('aml:messages-resync', resync);
  socket?.on('new_message', message => { receive(message); refreshContacts().catch(error => notify(error.message)); });
  socket?.on('unread_update', () => refreshContacts().catch(error => notify(error.message)));
  socket?.on('messages_read', event => {
    if (event.conversation_id !== conversationId) return;
    lastReadId = Math.max(lastReadId, Number(event.last_read_id) || 0);
    for (const message of visibleMessages.values())
      if (message.sender === currentUser && message.id <= lastReadId) message.status = 'read';
    renderMessages(false);
  });
  socket?.on('message_status', event => {
    if (event.conversation_id !== conversationId || !(event.status in receiptRank)) return;
    const message = visibleMessages.get(event.id);
    if (message && message.sender === currentUser) {
      mergeMessage({ ...message, status: event.status });
      renderMessages(false);
    } else if (!message && receiptRank[event.status] > (receiptRank[receiptUpdates.get(event.id)] ?? -1)) {
      receiptUpdates.set(event.id, event.status);
    }
  });
  socket?.on('user_typing', event => {
    if (event.conversation_id !== conversationId) return;
    el('userStatus').textContent = 'Typing…'; clearTimeout(typingTimer);
    typingTimer = setTimeout(() => { el('userStatus').textContent = 'Online'; }, 3000);
  });
  socket?.on('user_stop_typing', event => { if (event.conversation_id === conversationId) el('userStatus').textContent = 'Online'; });
  document.addEventListener('DOMContentLoaded', () => {
    el('openContacts').onclick = () => contactsOpen(true);
    el('closeContacts').onclick = () => contactsOpen(false);
    el('sendButton').onclick = send;
    el('attachFile').onclick = () => el('attachmentInput').click();
    el('attachmentInput').onchange = event => { selectAttachment(event.target.files); event.target.value = ''; };
    el('removeAttachment').onclick = () => { attachmentDrafts.delete(receiver); showAttachmentDraft(); };
    el('messageInput').addEventListener('paste', event => {
      const files = Array.from(event.clipboardData?.files || []);
      if (files.length) { event.preventDefault(); selectAttachment(files); }
    });
    const chatPanel = el('chatContent').closest('.chat-panel');
    chatPanel.addEventListener('dragover', event => {
      if (receiver && event.dataTransfer?.types.includes('Files')) { event.preventDefault(); chatPanel.classList.add('attachment-drop-active'); }
    });
    chatPanel.addEventListener('dragleave', event => { if (!chatPanel.contains(event.relatedTarget)) chatPanel.classList.remove('attachment-drop-active'); });
    chatPanel.addEventListener('drop', event => {
      if (!event.dataTransfer?.files.length) return;
      event.preventDefault(); chatPanel.classList.remove('attachment-drop-active'); selectAttachment(event.dataTransfer.files);
    });
    const enableAlerts = el('enableMessageNotifications');
    if (!('Notification' in window) || !window.isSecureContext) enableAlerts.hidden = true;
    else {
      let previousPermission, confirmationTimer;
      const syncAlertPermission = () => {
        const enabled = Notification.permission === 'granted';
        const blocked = Notification.permission === 'denied';
        if (Notification.permission !== previousPermission) {
          clearTimeout(confirmationTimer);
          enableAlerts.hidden = false;
          if (enabled) confirmationTimer = setTimeout(() => { enableAlerts.hidden = true; }, 4000);
          previousPermission = Notification.permission;
        }
        enableAlerts.textContent = enabled ? '\u2713 Device alerts enabled' : blocked ? '\u00d7 Device alerts blocked' : 'Enable device alerts';
        enableAlerts.classList.toggle('device-alerts-enabled', enabled);
        enableAlerts.setAttribute('aria-pressed', String(enabled));
        enableAlerts.title = blocked ? 'Allow notifications in your browser site settings.' : enabled ? 'Device alerts are enabled while this application is open.' : 'Enable notifications on this device.';
      };
      enableAlerts.setAttribute('aria-live', 'polite');
      syncAlertPermission();
      window.addEventListener('focus', syncAlertPermission);
      document.addEventListener('visibilitychange', syncAlertPermission);
      // Permission changes in browser settings update the open page immediately.
      navigator.permissions?.query({ name: 'notifications' }).then(permission => {
        permission.addEventListener('change', syncAlertPermission);
      }).catch(() => {});
      enableAlerts.onclick = async () => {
        enableAlerts.disabled = true;
        try {
          const permission = Notification.permission === 'default' ? await Notification.requestPermission() : Notification.permission;
          if (permission === 'granted' && 'serviceWorker' in navigator)
            navigator.serviceWorker.register('/static/message-notifications-sw.js').catch(() => {});
          if (permission === 'granted') window.showAmlNotification('Device alerts enabled.', 'device-alerts', 'success');
          else if (permission === 'denied') notify('Device alerts are blocked. Allow notifications in your browser site settings.');
          else notify('Device alerts were not enabled. Select Allow in the permission prompt.');
        } catch (error) {
          notify('Unable to enable device alerts. Check your browser notification settings.');
        } finally {
          syncAlertPermission();
          enableAlerts.disabled = false;
        }
      };
    }
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && conversationId) socket?.emit('mark_read', { conversation_id: conversationId });
    });
    el('messageInput').onkeydown = event => { if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); send(); } };
    el('messageInput').oninput = () => {
      drafts.set(receiver, el('messageInput').value);
      if (conversationId) socket?.emit(el('messageInput').value.trim() ? 'typing' : 'stop_typing', { conversation_id: conversationId });
    };
    refreshContacts().then(() => {
      const requested = new URLSearchParams(window.location.search).get('contact');
      const contact = contacts.find(item => item.username === requested);
      if (contact) openContact(contact);
    }).catch(error => notify(error.message));
  });
})();
