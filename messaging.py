"""
messaging.py — Real-time Messaging Module

This module handles direct messaging between Admin/Compliance Officer and between
Customer/Compliance Officer. Features include:
- Real-time message delivery via WebSocket
- Typing indicators
- Read/delivery receipts
- Message history
- Unread message badges
- Online status tracking
"""

import json
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any, Tuple
from utils import get_last_insert_id


class MessageRequestConflict(ValueError):
    pass


def public_message(message):
    """Project private attachment records into authenticated message URLs."""
    from message_attachments import AttachmentError, decode_message
    item = dict(message)
    try:
        caption, attachment = decode_message(item.get('content') or '')
    except AttachmentError:
        caption, attachment = 'Attachment unavailable', None
    item['content'] = caption
    if attachment:
        url = f"/api/messages/{item['id']}/attachment"
        item['attachment'] = {key: attachment[key] for key in ('name', 'size', 'media_type')}
        item['attachment']['url'] = url
        if attachment['media_type'].startswith('image/'):
            item['attachment']['preview_url'] = url + '?inline=1'
    return item


def create_messaging_tables_sql(database_url):
    """Generate SQL for messaging tables based on database engine."""
    from database import is_postgres_database_url, is_mysql_database_url
    
    is_pg = is_postgres_database_url(database_url)
    is_my = is_mysql_database_url(database_url)
    
    if is_my:
        ai, pk_type, text_type, long_text_type = "AUTO_INCREMENT", "BIGINT", "VARCHAR(255)", "LONGTEXT"
    elif is_pg:
        ai, pk_type, text_type, long_text_type = "GENERATED ALWAYS AS IDENTITY", "BIGINT", "TEXT", "TEXT"
    else:
        ai, pk_type, text_type, long_text_type = "AUTOINCREMENT", "INTEGER", "TEXT", "TEXT"
    
    return f"""
    CREATE TABLE IF NOT EXISTS conversations (
        id {pk_type} PRIMARY KEY {ai},
        participant_1 {text_type} NOT NULL,
        participant_2 {text_type} NOT NULL,
        conversation_type {text_type} NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_message_at TIMESTAMP,
        last_message_id {pk_type},
        UNIQUE (participant_1, participant_2),
        UNIQUE (participant_2, participant_1),
        FOREIGN KEY (participant_1) REFERENCES users(username),
        FOREIGN KEY (participant_2) REFERENCES users(username)
    );
    
    CREATE TABLE IF NOT EXISTS messages (
        id {pk_type} PRIMARY KEY {ai},
        conversation_id {pk_type} NOT NULL,
        sender_username {text_type} NOT NULL,
        sender_role {text_type},
        receiver_username {text_type} NOT NULL,
        content {long_text_type} NOT NULL,
        status {text_type} DEFAULT 'sent',
        read_at TIMESTAMP,
        delivered_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        edited_at TIMESTAMP,
        deleted_at TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id),
        FOREIGN KEY (sender_username) REFERENCES users(username),
        FOREIGN KEY (receiver_username) REFERENCES users(username)
    );
    
    CREATE TABLE IF NOT EXISTS unread_messages (
        id {pk_type} PRIMARY KEY {ai},
        user_username {text_type} NOT NULL,
        conversation_id {pk_type} NOT NULL,
        unread_count INTEGER DEFAULT 0,
        last_unread_at TIMESTAMP,
        UNIQUE (user_username, conversation_id),
        FOREIGN KEY (user_username) REFERENCES users(username),
        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
    );
    
    CREATE TABLE IF NOT EXISTS user_presence (
        id {pk_type} PRIMARY KEY {ai},
        username {text_type} UNIQUE NOT NULL,
        is_online INTEGER DEFAULT 0,
        last_seen TIMESTAMP,
        typing_in_conversation {pk_type},
        FOREIGN KEY (username) REFERENCES users(username),
        FOREIGN KEY (typing_in_conversation) REFERENCES conversations(id)
    );
    """


def get_or_create_conversation(conn, user1: str, user2: str, conversation_type: str = "direct") -> Dict[str, Any]:
    """Get or create a direct message conversation."""
    # Ensure consistent ordering for conversation uniqueness
    if user1 > user2:
        user1, user2 = user2, user1
    
    # Check if conversation exists
    row = conn.execute(
        "SELECT id FROM conversations WHERE participant_1=? AND participant_2=?",
        (user1, user2)
    ).fetchone()
    
    if row:
        return dict(row)
    
    # Create new conversation
    try:
        conn.execute(
            "INSERT INTO conversations (participant_1, participant_2, conversation_type) VALUES (?, ?, ?)",
            (user1, user2, conversation_type)
        )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        from transaction_idempotency import is_unique_conflict
        if not is_unique_conflict(exc):
            raise
        # Another tab may have created this same conversation while we waited.
    
    row = conn.execute(
        "SELECT id FROM conversations WHERE participant_1=? AND participant_2=?",
        (user1, user2)
    ).fetchone()
    
    return dict(row) if row else {"id": None}


def send_message(conn, conversation_id: int, sender: str, receiver: str, content: str, sender_role: str = None,
                 *, attachment_request_id=None) -> Dict[str, Any]:
    """Send a direct message."""
    if not content.strip():
        return {"error": "Message cannot be empty"}
    
    now = datetime.now(timezone.utc).isoformat()
    try:
        # Serialize sends and read receipts for this conversation.
        lock = " FOR UPDATE" if getattr(conn, "engine", "sqlite") in ("mysql", "postgres") else ""
        row = conn.execute("SELECT id FROM conversations WHERE id=?" + lock,
                           (conversation_id,)).fetchone()
        if row is None:
            raise ValueError("Conversation not found")
        if attachment_request_id is not None:
            from message_attachments import PREFIX, decode_message
            caption, metadata = decode_message(content)
            if not metadata or metadata.get('request_id') != attachment_request_id:
                raise MessageRequestConflict('Invalid attachment request identity')
            prior = conn.execute(
                "SELECT id,sender_username,receiver_username,content,status,created_at FROM messages "
                "WHERE conversation_id=? AND sender_username=? AND content LIKE ? ESCAPE '!' ORDER BY id DESC LIMIT 1" + lock,
                (conversation_id, sender, PREFIX.replace('_', '!_') + '%"request_id":"' + attachment_request_id + '"%')).fetchone()
            if prior:
                old_caption, old_metadata = decode_message(prior['content'])
                fields = ('name', 'size', 'media_type', 'sha256', 'request_id')
                if (not old_metadata or old_caption != caption or prior['receiver_username'] != receiver or
                        any(old_metadata[key] != metadata[key] for key in fields)):
                    raise MessageRequestConflict('This attachment request was already used. Select the file again to send a different message.')
                conn.rollback()
                return {**dict(prior), 'replayed': True}
        conn.execute(
            """INSERT INTO messages
               (conversation_id, sender_username, sender_role, receiver_username, content, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (conversation_id, sender, sender_role, receiver, content.strip(), "sent", now))
        message_id = get_last_insert_id(conn)
        msg = conn.execute(
            "SELECT id, sender_username, receiver_username, content, status, created_at FROM messages WHERE id=?",
            (message_id,)).fetchone()
        if msg is None:
            raise RuntimeError("Inserted message could not be retrieved")
        conn.execute("UPDATE conversations SET last_message_at=?, last_message_id=? WHERE id=?",
                     (now, message_id, conversation_id))
        add_unread_message(conn, conversation_id, receiver, commit=False)
        conn.commit()
        return dict(msg)
    except Exception:
        conn.rollback()
        raise


def mark_message_as_delivered(conn, message_id: int, receiver: str) -> bool:
    """Confirm receipt only for the intended recipient and a sent message."""
    now = datetime.now(timezone.utc).isoformat()
    row = conn.execute(
        "SELECT conversation_id FROM messages WHERE id=? AND receiver_username=? AND status='sent'",
        (message_id, receiver),
    ).fetchone()
    if not row:
        return False
    updated = conn.execute("UPDATE messages SET status='delivered', delivered_at=? "
                           "WHERE id=? AND receiver_username=? AND status='sent'",
                           (now, message_id, receiver))
    conn.commit()
    return updated.rowcount == 1


def mark_message_as_read(conn, message_id: int) -> bool:
    """Mark a message as read."""
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE messages SET status='read', read_at=? WHERE id=?",
        (now, message_id)
    )
    conn.commit()
    return True


def mark_conversation_as_read(conn, conversation_id: int, user: str) -> int:
    """Mark received messages as read and return the last observed message ID."""
    now = datetime.now(timezone.utc).isoformat()
    try:
        lock = " FOR UPDATE" if getattr(conn, "engine", "sqlite") in ("mysql", "postgres") else ""
        conn.execute("SELECT id FROM conversations WHERE id=?" + lock, (conversation_id,)).fetchone()
        last = conn.execute(
            "SELECT MAX(id) AS id FROM messages WHERE conversation_id=? AND receiver_username=?",
            (conversation_id, user),
        ).fetchone()
        last_id = (last['id'] or 0) if last else 0
        conn.execute(
            "UPDATE messages SET status='read', read_at=? WHERE conversation_id=? AND receiver_username=? AND id<=? AND status != 'read'",
            (now, conversation_id, user, last_id))
        conn.execute("DELETE FROM unread_messages WHERE conversation_id=? AND user_username=?",
                     (conversation_id, user))
        conn.commit()
        return last_id
    except Exception:
        conn.rollback()
        raise


def get_conversation_messages(conn, conversation_id: int, limit: int = 50, offset: int = 0, before_id=None) -> List[Dict[str, Any]]:
    """Get message history for a conversation."""
    rows = conn.execute(
        """SELECT id, sender_username, sender_role, receiver_username, content, status, created_at, 
                  read_at, delivered_at, edited_at
           FROM messages 
           WHERE conversation_id=? AND deleted_at IS NULL AND (? IS NULL OR id < ?)
           ORDER BY id DESC
           LIMIT ? OFFSET ?""",
        (conversation_id, before_id, before_id, limit, offset)
    ).fetchall()
    
    return [public_message(row) for row in rows]


def get_user_conversations(conn, username: str) -> List[Dict[str, Any]]:
    """Get all conversations for a user with latest message preview."""
    rows = conn.execute(
        """SELECT c.id, c.participant_1, c.participant_2, c.conversation_type,
                  c.last_message_at, c.last_message_id,
                  m.content, m.sender_username, m.status,
                  u.unread_count, u.user_username,
                  up.is_online, up.last_seen
           FROM conversations c
           LEFT JOIN messages m ON m.id = c.last_message_id
           LEFT JOIN unread_messages u ON u.conversation_id = c.id AND u.user_username = ?
           LEFT JOIN user_presence up ON up.username = CASE WHEN c.participant_1 = ? THEN c.participant_2 ELSE c.participant_1 END
           WHERE c.participant_1 = ? OR c.participant_2 = ?
           ORDER BY c.last_message_at DESC, c.last_message_id DESC, c.id DESC""",
        (username, username, username, username)
    ).fetchall()
    
    conversations = []
    for row in rows:
        conv_dict = dict(row)
        from message_attachments import AttachmentError, decode_message
        try:
            caption, attachment = decode_message(conv_dict.get('content') or '')
            conv_dict['content'] = caption or (attachment['name'] if attachment else '')
        except AttachmentError:
            conv_dict['content'] = 'Attachment unavailable'
        other_participant = conv_dict['participant_2'] if conv_dict['participant_1'] == username else conv_dict['participant_1']
        conv_dict['other_participant'] = other_participant
        conv_dict['unread_count'] = conv_dict.get('unread_count') or 0
        conversations.append(conv_dict)
    
    return conversations


def get_unread_count(conn, username: str) -> Dict[str, Any]:
    """Count unread messages only in conversations still permitted by policy."""
    counts = get_unread_by_conversation(conn, username)
    return {
        "total_unread": sum(counts.values()),
        "by_conversation": counts
    }


def get_unread_by_conversation(conn, username: str) -> Dict[int, int]:
    """Keep retained, disallowed conversations out of current unread badges."""
    rows = conn.execute(
        "SELECT um.conversation_id, um.unread_count, viewer.role AS viewer_role, "
        "other.role AS other_role FROM unread_messages um "
        "JOIN conversations c ON c.id=um.conversation_id "
        "JOIN users viewer ON viewer.username=um.user_username "
        "JOIN users other ON other.username=CASE WHEN c.participant_1=um.user_username "
        "THEN c.participant_2 ELSE c.participant_1 END "
        "WHERE um.user_username=? AND (c.participant_1=um.user_username "
        "OR c.participant_2=um.user_username)",
        (username,)
    ).fetchall()
    
    return {row["conversation_id"]: row["unread_count"] for row in rows
            if can_user_message(row['viewer_role'], row['other_role'])[0]}


def add_unread_message(conn, conversation_id: int, receiver: str, *, commit=True) -> bool:
    """Increment unread count for a message."""
    # Check if record exists
    lock = " FOR UPDATE" if getattr(conn, "engine", "sqlite") in ("mysql", "postgres") else ""
    row = conn.execute(
        "SELECT id, unread_count FROM unread_messages WHERE conversation_id=? AND user_username=?" + lock,
        (conversation_id, receiver)
    ).fetchone()
    
    now = datetime.now(timezone.utc).isoformat()
    
    if row:
        conn.execute(
            "UPDATE unread_messages SET unread_count = unread_count + 1, last_unread_at=? WHERE conversation_id=? AND user_username=?",
            (now, conversation_id, receiver)
        )
    else:
        conn.execute(
            "INSERT INTO unread_messages (conversation_id, user_username, unread_count, last_unread_at) VALUES (?, ?, 1, ?)",
            (conversation_id, receiver, now)
        )
    
    if commit:
        conn.commit()
    return True


def set_user_online(conn, username: str, is_online: bool = True) -> bool:
    """Update user online status."""
    now = datetime.now(timezone.utc).isoformat()
    
    row = conn.execute("SELECT id FROM user_presence WHERE username=?", (username,)).fetchone()
    
    if row:
        conn.execute(
            "UPDATE user_presence SET is_online=?, last_seen=? WHERE username=?",
            (1 if is_online else 0, now, username)
        )
    else:
        conn.execute(
            "INSERT INTO user_presence (username, is_online, last_seen) VALUES (?, ?, ?)",
            (username, 1 if is_online else 0, now)
        )
    
    conn.commit()
    return True


def get_user_online_status(conn, username: str) -> Dict[str, Any]:
    """Get user's online status."""
    row = conn.execute(
        "SELECT is_online, last_seen FROM user_presence WHERE username=?",
        (username,)
    ).fetchone()
    
    if not row:
        return {"is_online": False, "last_seen": None}
    
    return {
        "is_online": bool(row["is_online"]),
        "last_seen": row["last_seen"]
    }


def set_typing_indicator(conn, username: str, conversation_id: Optional[int] = None) -> bool:
    """Set user as typing in a conversation."""
    row = conn.execute("SELECT id FROM user_presence WHERE username=?", (username,)).fetchone()
    
    if row:
        conn.execute(
            "UPDATE user_presence SET typing_in_conversation=? WHERE username=?",
            (conversation_id, username)
        )
    else:
        conn.execute(
            "INSERT INTO user_presence (username, typing_in_conversation, is_online) VALUES (?, ?, 1)",
            (username, conversation_id)
        )
    
    conn.commit()
    return True


def can_user_message(user_role: str, target_user_role: str) -> Tuple[bool, str]:
    """Customers communicate with customers and compliance, never admins."""
    roles = {'customer', 'admin', 'compliance'}
    if user_role not in roles or target_user_role not in roles:
        return False, 'Messaging is not available for this account'
    if {user_role, target_user_role} == {'customer', 'admin'}:
        return False, 'Customers can communicate with other customers and compliance officers'
    return True, 'Messaging is available'


def delete_message(conn, message_id: int, username: str) -> Tuple[bool, str]:
    """Soft delete a message (only sender can delete)."""
    msg = conn.execute(
        "SELECT sender_username FROM messages WHERE id=?",
        (message_id,)
    ).fetchone()
    
    if not msg:
        return False, "Message not found"
    
    if msg["sender_username"] != username:
        return False, "Only message sender can delete"
    
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE messages SET deleted_at=? WHERE id=?",
        (now, message_id)
    )
    conn.commit()
    
    return True, "Message deleted"


def search_conversations(conn, username: str, query: str) -> List[Dict[str, Any]]:
    """Search conversations by participant name."""
    rows = conn.execute(
        """SELECT c.id, c.participant_1, c.participant_2, c.last_message_at
           FROM conversations c
           WHERE (c.participant_1 = ? OR c.participant_2 = ?)
           AND (c.participant_1 LIKE ? OR c.participant_2 LIKE ?)
           ORDER BY c.last_message_at DESC""",
        (username, username, f"%{query}%", f"%{query}%")
    ).fetchall()
    
    return [dict(row) for row in rows]
