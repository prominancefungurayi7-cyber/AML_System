
  const socket = window.getAmlSocket();
  const currentUser = "tester";
  let currentConversation = null;
  let currentReceiver = "";
  let conversations = [];
  let messageableUsers = [];
  let activeContact = null;
  let pendingMessage = "";
  let sending = false;

  function setContactsOpen(open) {
    const workspace = document.getElementById('messagingWorkspace');
    const rail = document.getElementById('contactsRail');
    workspace.classList.toggle('contacts-open', open);
    rail.inert = !open;
    rail.setAttribute('aria-hidden', String(!open));
    document.getElementById('openContacts').setAttribute('aria-expanded', String(open));
  }

  document.addEventListener('DOMContentLoaded', async () => {
    setupEventListeners();
    await loadMessageableUsers();
    await loadConversations();
    setContactsOpen(true);
  });

  function setupEventListeners() {
    document.getElementById('openContacts').addEventListener('click', () => setContactsOpen(true));
    document.getElementById('closeContacts').addEventListener('click', () => setContactsOpen(false));
    document.getElementById('sendButton').addEventListener('click', sendMessage);
    document.getElementById('messageInput').addEventListener('keypress', (event) => {
      if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); sendMessage(); }
    });
    document.getElementById('messageInput').addEventListener('input', function() {
      this.style.height = 'auto'; this.style.height = Math.min(this.scrollHeight, 120) + 'px';
      if (this.value.trim() && currentConversation) socket.emit('typing', { conversation_id: currentConversation });
    });
  }

  async function loadMessageableUsers() {
    try {
      const data = await (await fetch('/api/messageable-users')).json();
      messageableUsers = data.status === 'success' ? data.users || [] : [];
      renderConversations();
    } catch (error) { console.error('Error loading messaging contacts:', error); }
  }

  async function loadConversations() {
    try {
      const data = await (await fetch('/api/conversations')).json();
      conversations = data.status === 'success' ? data.conversations || [] : [];
      renderConversations();
    } catch (error) { console.error('Error loading conversation:', error); }
  }

  function renderConversations() {
    const list = document.getElementById('conversationsList'); list.innerHTML = '';
    if (!messageableUsers.length) { list.innerHTML = '<li class="message-empty-state">No secure messaging contacts are available.</li>'; return; }
    messageableUsers.forEach((contact) => {
      const conversation = conversations.find((item) => item.other_participant === contact.username);
      const item = document.createElement('li');
      item.className = `conversation-item modern-thread ${currentReceiver === contact.username ? 'active' : ''}`;
      item.innerHTML = `<div class="conversation-avatar ${contact.is_online ? 'online' : ''}">${getInitials(contact.username)}</div><div class="conversation-info"><div class="conversation-name">${escapeHtml(contactLabel(contact))}</div><div class="conversation-preview">${escapeHtml(conversation ? (conversation.content || 'No messages yet') : 'Start a secure conversation')}</div></div><div class="thread-meta">${conversation && conversation.unread_count > 0 ? `<span class="unread-badge">${conversation.unread_count}</span>` : ''}</div>`;
      item.addEventListener('click', () => openContact(contact)); list.appendChild(item);
    });
  }

  async function openContact(contact) {
    if (!contact) return;
    activeContact = contact;
    const conversation = conversations.find((item) => item.other_participant === contact.username);
    currentReceiver = contact.username; currentConversation = conversation ? conversation.id : null;
    openChat();
    setContactsOpen(false);
    if (conversation) { await loadMessages(conversation.id); socket?.emit('mark_read', { conversation_id: conversation.id }); }
    else document.getElementById('messagesContainer').innerHTML = '<div class="message-empty-state message-empty-state--inline">Start a secure conversation.</div>';
    renderConversations();
  }

  function openChat() {
    document.getElementById('chatArea').hidden = true; document.getElementById('chatContent').hidden = false;
    document.getElementById('chatTitle').textContent = contactLabel(activeContact);
    document.getElementById('chatAvatar').textContent = getInitials(activeContact.username);
    document.getElementById('statusIndicator').className = `status-indicator ${activeContact.is_online ? '' : 'offline'}`;
    document.getElementById('userStatus').textContent = activeContact.is_online ? 'Online' : 'Offline';
  }

  async function loadMessages(conversationId) {
    try { const data = await (await fetch(`/api/conversations/${conversationId}/messages`)).json(); if (data.status === 'success') displayMessages((data.messages || []).reverse()); }
    catch (error) { console.error('Error loading messages:', error); }
  }
  function displayMessages(messages) {
    const container = document.getElementById('messagesContainer'); container.innerHTML = '';
    if (!messages.length) { container.innerHTML = '<div class="message-empty-state message-empty-state--inline">No messages in this thread yet.</div>'; return; }
    messages.forEach((message) => appendMessage({ content: message.content, sender: message.sender_username, timestamp: message.created_at }, false)); container.scrollTop = container.scrollHeight;
  }
  function sendMessage() {
    const input = document.getElementById('messageInput'); const content = input.value.trim(); if (!content || !currentReceiver || sending) return;
    // A recipient can be removed or changed in another session. Do not send
    // to a stale client-side contact; the server validates again on receipt.
    if (!messageableUsers.some((contact) => contact.username === currentReceiver)) { alert('This customer is no longer an available messaging contact.'); loadMessageableUsers(); return; }
    if (!socket?.connected) { window.showAmlNotification('Messaging is disconnected. Your draft is still here.', 'message-connection', 'error'); return; }
    pendingMessage = content;
    sending = true;
    const sendButton = document.getElementById('sendButton'); sendButton.disabled = true;
    const timer = setTimeout(() => {
      if (!sending) return;
      sending = false; sendButton.disabled = false;
      window.showAmlNotification('Message delivery is unconfirmed. Refresh the conversation before retrying.', 'message-timeout', 'error');
    }, 10000);
    socket.emit('send_message', { receiver: currentReceiver, content, conversation_id: currentConversation }, (result) => {
      if (!sending) return;
      clearTimeout(timer); sending = false; sendButton.disabled = false;
      if (result?.status !== 'success') {
        window.showAmlNotification(result?.message || 'Message could not be sent.', 'message-error', 'error');
        return;
      }
      if (input.value.trim() === content) { input.value = ''; input.style.height = 'auto'; }
      pendingMessage = '';
      if (currentConversation) socket.emit('stop_typing', { conversation_id: currentConversation });
    });
  }
  socket.on('new_message', async (message) => {
    if (!messageableUsers.some((contact) => message.sender === contact.username || message.receiver === contact.username)) return;
    const belongsToOpenThread = message.conversation_id === currentConversation || (!currentConversation && (message.sender === currentReceiver || message.receiver === currentReceiver));
    if (belongsToOpenThread) { currentConversation = message.conversation_id; pendingMessage = ""; appendMessage({ content: message.content, sender: message.sender, timestamp: message.timestamp }, true); socket.emit('mark_read', { conversation_id: message.conversation_id }); }
    await loadConversations();
  });
  socket.on('message_error', (data) => {
    const input = document.getElementById('messageInput');
    if (pendingMessage && !input.value) input.value = pendingMessage;
    input.focus();
    sending = false;
    document.getElementById('sendButton').disabled = false;
    window.showAmlNotification(data.message || 'Message could not be sent.', 'message-error', 'error');
  });
  socket.on('user_typing', (data) => {
    if (data.conversation_id === currentConversation && data.user !== currentUser) { const container = document.getElementById('messagesContainer'); if (!container.querySelector('.typing-indicator')) { const indicator = document.createElement('div'); indicator.className = 'typing-indicator'; indicator.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>'; container.appendChild(indicator); } }
  });
  socket.on('user_stop_typing', (data) => { if (data.conversation_id === currentConversation) document.querySelector('.typing-indicator')?.remove(); });
  socket.on('unread_update', loadConversations);
  function appendMessage(message, scroll) {
    const container = document.getElementById('messagesContainer'); container.querySelector('.message-empty-state--inline')?.remove();
    const group = document.createElement('div'); group.className = `message-group ${message.sender === currentUser ? 'sent' : 'received'}`;
    const time = new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); group.innerHTML = `<div><div class="message-bubble">${escapeHtml(message.content)}</div><div class="message-time">${time}</div></div>`; container.appendChild(group); if (scroll) container.scrollTop = container.scrollHeight;
  }
  function getInitials(value) { return String(value || '--').slice(0, 2).toUpperCase(); }
  function contactLabel(contact) { return contact.role === 'customer' ? `${contact.username} (${contact.account_number})` : contact.username; }
  function escapeHtml(text) { const div = document.createElement('div'); div.textContent = text || ''; return div.innerHTML; }
