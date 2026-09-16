"""

server.py — StanPro Bank AML Intelligence Platform (Consolidated Web Server)

=========================================================================

Industry-ready Flask application aligned with:

  • FATF Recommendations 10, 16, 20, 29

  • Basel AML Index compliance requirements

  • FinCEN / FIU reporting workflows

  • Zimbabwe FIU Act reporting obligations

New capabilities vs prototype:

  • SAR (Suspicious Activity Report) workflow with status tracking

  • CTR (Currency Transaction Report) auto-generation

  • Case management: open → investigating → escalated → closed

  • System activity log for operational history

  • Role-based dashboard with analyst / compliance / admin separation

  • Detailed per-transaction rule evidence stored in DB

  • Security features: rate limiting, account lockout, secure headers

"""

import json

import logging

import os

import random

import re

import smtplib

import socket

import sqlite3

import threading

import time

import uuid

from queue import Empty, Queue

from datetime import datetime, timedelta, timezone

from decimal import Decimal

from email.message import EmailMessage

from functools import wraps

from urllib.parse import unquote, urlparse

from collections import defaultdict


from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Flag to prevent concurrent AI training
_ai_training_in_progress = False
_ai_training_lock = threading.Lock()

from flask import (

    Flask,

    Response,

    flash,

    g,

    jsonify,

    redirect,

    render_template,

    request,

    session,

    url_for,

)

from flask_socketio import SocketIO, join_room

from werkzeug.security import check_password_hash, generate_password_hash

from typing import Optional, Dict, List, Tuple, Any



# Import from consolidated ai_core module
from ai_core import (
    MODEL_PATH,
    PROFILE_FEATURE_DEFAULTS,
    BehavioralProfiler,
    CustomerBehavioralProfile,
    TransactionAnomaly,
    behavioral_profiler,
    delete_ai_model,
    get_model_metadata,
    predict_risk_level,
    train_ai_model,
)

from config import DevelopmentConfig, ProductionConfig, TestingConfig

from screening import is_registration_blocked, screen_entity, screening_summary
from aml_rules import CTR_THRESHOLD, assess_rules
from transaction_simulation import (
    _random_transaction_amount,
    _simulation_plan,
    _simulation_timestamp,
    _scenario_amount,
    _simulation_segment_multiplier,
    _simulation_transaction,
    _simulation_reason,
    _history_profile,
    _ai_profile_for_transaction,
    _parse_timestamp,
    NORMAL_TRANSACTION_SCENARIOS,
    SUSPICIOUS_TRANSACTION_SCENARIOS,
    SUPER_SUSPICIOUS_TRANSACTION_SCENARIOS,
    PROFILE_FEATURE_DEFAULTS,
    generate_structuring_scenario,
    generate_network_scenario,
    generate_agent_scenario,
)

# Import from modularized components
from database import (
    DatabaseAdapter,
    is_postgres_database_url,
    is_mysql_database_url,
    connect_db,
    get_schema_sql,
)
from security import (
    check_login_attempts,
    record_login_attempt,
    add_security_headers,
)
from behavioral_profiling import (
    get_customer_behavioral_profile,
    save_customer_behavioral_profile,
    build_or_update_customer_profile,
    assess_transaction_behavioral_risk,
)
from alerts import (
    create_alert_if_needed,
    update_customer_risk_rating,
    _generate_sar_ref,
    _generate_ctr_ref,
    get_alert_statistics,
)
from realtime import RealtimeBroker
from ai_stage13_features import Stage13FeatureService
from ai_stage14_model import Stage14ModelService, get_stage14_model_service
from utils import (
    serialize_value,
    serialize_row,
    serialize_rows,
    request_page,
    _user_balance_payload,
    _transaction_payload,
    _stats_payload,
    send_email,
)
from users import (
    validate_id_number,
    is_username_reserved,
    get_staff_accounts,
    create_user,
    get_user_by_account_number,
    get_user_by_username as fetch_user_by_username,
    get_user_by_id,
    update_user_balance,
    update_user_kyc_status,
    update_user_risk_rating,
    get_all_users,
    get_users_by_role,
    update_user_last_login,
    verify_password,
    ID_NUMBER_PATTERN,
    ID_NUMBER_FORMAT_MESSAGE,
    STAFF_ACCOUNTS,
    RESERVED_STAFF_USERNAMES,
)
from transactions import (
    set_rule_engine_enabled,
    is_rule_engine_enabled,
    _risk_level_from_score,
    _calibrate_generated_transaction_risk,
    _combine_rule_ai_risk,
    get_transaction_by_id,
    get_transactions_by_account,
    get_all_transactions,
    get_transactions_by_risk_level,
    get_transaction_statistics,
    RISK_RANK,
    AI_RISK_SCORES,
)
from reports import (
    create_sar_report,
    create_ctr_report,
    get_sar_reports,
    get_sar_reports_by_account,
    get_sar_by_id,
    get_ctr_reports,
    get_ctr_reports_by_account,
    get_ctr_by_id,
    update_sar_status,
    update_ctr_status,
    get_report_statistics,
    log_system_activity,
    get_activity_log,
)
from messaging import (
    create_messaging_tables_sql,
    get_or_create_conversation,
    send_message,
    get_conversation_messages,
    get_user_conversations,
    get_unread_count,
    mark_conversation_as_read,
    add_unread_message,
    set_user_online,
    get_user_online_status,
    set_typing_indicator,
    can_user_message,
    mark_message_as_delivered,
    mark_message_as_read,
)


load_dotenv()



app = Flask(__name__)

app.config.from_object(

    DevelopmentConfig if os.environ.get("FLASK_ENV") == "development" else ProductionConfig

)

# Security: Add secure headers
@app.after_request
def add_security_headers_wrapper(response):
    return add_security_headers(response)


# ============================================================================
# Database Connection
# ============================================================================

def get_db():
    if "db" not in g:
        g.db = connect_db(app.config["DATABASE"])
    return g.db


def login_required(view_func=None, *roles):
    """Require a logged-in user, optionally limited to one or more roles."""
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to continue.")
                return redirect(url_for("login"))

            user = get_user_by_id(session["user_id"])
            if user is None:
                session.clear()
                flash("Session expired. Please log in again.")
                return redirect(url_for("login"))

            if roles and user["role"] not in roles:
                flash("Access denied.")
                return redirect(url_for("dashboard_redirect"))

            return func(*args, **kwargs)

        return wrapped

    if callable(view_func):
        return decorator(view_func)

    if view_func is not None:
        roles = (view_func, *roles)

    return decorator


@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ============================================================================
# Schema Initialization
# ============================================================================

def init_db():
    conn = connect_db(app.config["DATABASE"])
    conn.executescript(get_schema_sql(app.config["DATABASE"]))
    
    # Add messaging tables
    messaging_sql = create_messaging_tables_sql(app.config["DATABASE"])
    conn.executescript(messaging_sql)
    
    # SQLite migration: add new columns to existing tables
    if not is_postgres_database_url(app.config["DATABASE"]) and not is_mysql_database_url(app.config["DATABASE"]):
        _migrate_sqlite(conn)
    elif is_mysql_database_url(app.config["DATABASE"]):
        _migrate_mysql(conn)
    elif is_postgres_database_url(app.config["DATABASE"]):
        _migrate_postgres(conn)
    
    conn.commit()
    conn.close()


def _migrate_sqlite(conn):
    """Add columns that may not exist in older DB files."""
    migrations = {
        "users": ["kyc_status TEXT DEFAULT 'pending'", "pep_flag INTEGER DEFAULT 0", "risk_rating TEXT DEFAULT 'standard'", "wealth_segment TEXT DEFAULT 'average'"],
        "transactions": ["currency TEXT DEFAULT 'USD'", "channel TEXT DEFAULT 'online'",
                         "rule_score REAL DEFAULT 0", "rule_level TEXT DEFAULT 'normal'",
                         "rule_reason TEXT", "ai_risk_level TEXT", "ai_confidence REAL DEFAULT 0",
                         "ai_reason TEXT",
                         "rules_triggered TEXT DEFAULT '[]'", "ctr_required INTEGER DEFAULT 0",
                         "sar_required INTEGER DEFAULT 0", "destination_country TEXT DEFAULT 'ZW'",
                         "screening_hits TEXT", "reviewed_by TEXT", "reviewed_at TEXT",
                         "generated_label TEXT", "status TEXT DEFAULT 'Completed'"],
        "alerts": ["rules_triggered TEXT DEFAULT '[]'", "status TEXT DEFAULT 'open'",
                   "assigned_to TEXT", "case_notes TEXT", "resolved_at TEXT", "resolved_by TEXT"],
        "behavioral_profiles": ["account_number TEXT PRIMARY KEY", "profile_data TEXT", "last_updated TEXT", "total_transactions INTEGER DEFAULT 0"],
    }

    for table, cols in migrations.items():
        existing = [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        for col_def in cols:
            col_name = col_def.split()[0]
            if col_name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
    
    # Create messaging tables if they don't exist
    messaging_sql = create_messaging_tables_sql(app.config["DATABASE"])
    for statement in messaging_sql.split(";"):
        statement = statement.strip()
        if statement:
            conn.execute(statement)


def _migrate_mysql(conn):
    """Widen older MySQL VARCHAR columns that store AML evidence JSON/text."""
    column_migrations = {
        "users": [
            ("kyc_status", "VARCHAR(255) DEFAULT 'pending'"),
            ("pep_flag", "INTEGER DEFAULT 0"),
            ("risk_rating", "VARCHAR(255) DEFAULT 'standard'"),
            ("wealth_segment", "VARCHAR(255) DEFAULT 'average'"),
        ],
        "transactions": [
            ("currency", "VARCHAR(255) DEFAULT 'USD'"),
            ("channel", "VARCHAR(255) DEFAULT 'online'"),
            ("rule_score", "DOUBLE DEFAULT 0"),
            ("rule_level", "VARCHAR(255) DEFAULT 'normal'"),
            ("rule_reason", "LONGTEXT"),
            ("ai_risk_level", "VARCHAR(255)"),
            ("ai_confidence", "DOUBLE DEFAULT 0"),
            ("ai_reason", "LONGTEXT"),
            ("rules_triggered", "LONGTEXT DEFAULT '[]'"),
            ("ctr_required", "INTEGER DEFAULT 0"),
            ("sar_required", "INTEGER DEFAULT 0"),
            ("destination_country", "VARCHAR(255) DEFAULT 'ZW'"),
            ("screening_hits", "LONGTEXT"),
            ("reviewed_by", "VARCHAR(255)"),
            ("reviewed_at", "VARCHAR(255)"),
            ("generated_label", "VARCHAR(50)"),
            ("status", "VARCHAR(50) DEFAULT 'Completed'"),
        ],
        "alerts": [
            ("rules_triggered", "LONGTEXT DEFAULT '[]'"),
            ("status", "VARCHAR(255) DEFAULT 'open'"),
            ("assigned_to", "VARCHAR(255)"),
            ("case_notes", "LONGTEXT"),
            ("resolved_at", "VARCHAR(255)"),
            ("resolved_by", "VARCHAR(255)"),
        ],
        "behavioral_profiles": [
            ("account_number", "VARCHAR(255) PRIMARY KEY"),
            ("profile_data", "LONGTEXT"),
            ("last_updated", "VARCHAR(255)"),
            ("total_transactions", "INTEGER DEFAULT 0"),
        ],
    }

    for table, columns in column_migrations.items():
        try:
            existing = {
                row["Field"]
                for row in conn.execute(f"SHOW COLUMNS FROM {table}").fetchall()
            }
            for column_name, column_def in columns:
                if column_name not in existing:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column_name} {column_def}")
        except Exception as e:
            logging.error(f"Error adding columns to {table}: {e}")
    
    # Create messaging tables if they don't exist
    messaging_sql = create_messaging_tables_sql(app.config["DATABASE"])
    for statement in messaging_sql.split(";"):
        statement = statement.strip()
        if statement:
            try:
                conn.execute(statement)
            except Exception as e:
                logging.error(f"Error creating messaging table: {e}")


def _migrate_postgres(conn):
    """Add columns for PostgreSQL databases."""
    column_migrations = {
        "users": [
            ("kyc_status", "TEXT DEFAULT 'pending'"),
            ("pep_flag", "INTEGER DEFAULT 0"),
            ("risk_rating", "TEXT DEFAULT 'standard'"),
            ("wealth_segment", "TEXT DEFAULT 'average'"),
        ],
        "transactions": [
            ("currency", "TEXT DEFAULT 'USD'"),
            ("channel", "TEXT DEFAULT 'online'"),
            ("rule_score", "DOUBLE PRECISION DEFAULT 0"),
            ("rule_level", "TEXT DEFAULT 'normal'"),
            ("rule_reason", "TEXT"),
            ("ai_risk_level", "TEXT"),
            ("ai_confidence", "DOUBLE PRECISION DEFAULT 0"),
            ("ai_reason", "TEXT"),
            ("rules_triggered", "TEXT DEFAULT '[]'"),
            ("ctr_required", "INTEGER DEFAULT 0"),
            ("sar_required", "INTEGER DEFAULT 0"),
            ("destination_country", "TEXT DEFAULT 'ZW'"),
            ("screening_hits", "TEXT"),
            ("reviewed_by", "TEXT"),
            ("reviewed_at", "TEXT"),
            ("generated_label", "VARCHAR(50)"),
            ("status", "VARCHAR(50) DEFAULT 'Completed'"),
        ],
        "alerts": [
            ("rules_triggered", "TEXT DEFAULT '[]'"),
            ("status", "TEXT DEFAULT 'open'"),
            ("assigned_to", "TEXT"),
            ("case_notes", "TEXT"),
            ("resolved_at", "TEXT"),
            ("resolved_by", "TEXT"),
        ],
        "behavioral_profiles": [
            ("account_number", "TEXT PRIMARY KEY"),
            ("profile_data", "TEXT"),
            ("last_updated", "TEXT"),
            ("total_transactions", "INTEGER DEFAULT 0"),
        ],
    }

    for table, columns in column_migrations.items():
        try:
            existing = {
                row["column_name"]
                for row in conn.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}'").fetchall()
            }
            for column_name, column_def in columns:
                if column_name not in existing:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column_name} {column_def}")
        except Exception as e:
            logging.error(f"Error adding columns to {table}: {e}")
    
    # Create messaging tables if they don't exist
    messaging_sql = create_messaging_tables_sql(app.config["DATABASE"])
    for statement in messaging_sql.split(";"):
        statement = statement.strip()
        if statement:
            try:
                conn.execute(statement)
            except Exception as e:
                logging.error(f"Error creating messaging table: {e}")


# ============================================================================
# Constants
# ============================================================================

PAGE_SIZE = 25  # rows per paginated list
VALID_TRANSACTION_TYPES = {"deposit", "withdraw", "transfer"}

if app.config.get("TESTING"):

    app.config.from_object(TestingConfig)



app.config.setdefault("STREAM_SUBSCRIBERS", [])

app.config.setdefault("LAST_MONITORED_TRANSACTION_ID", 0)

app.config.setdefault("REALTIME_POLL_INTERVAL", 0.5)

app.config.setdefault("ACTIVE_STREAMS", {})

app.config.setdefault(

    "DATABASE",

    app.config.get("DATABASE_URL", os.path.join(os.path.dirname(__file__), "aml.db")),

)

# Messaging and background helpers open independent connections.  Default those
# connections to the configured deployment database (including Railway MySQL).
_database_connect_db = connect_db

def connect_db(database_url=None):
    return _database_connect_db(database_url or app.config["DATABASE"])



# Ensure data directory exists for Railway

if app.config["DATABASE"].startswith("sqlite:///"):

    db_path = app.config["DATABASE"].replace("sqlite:///", "")

    db_dir = os.path.dirname(db_path)

    if db_dir and not os.path.exists(db_dir):

        os.makedirs(db_dir, exist_ok=True)



logging.basicConfig(level=logging.INFO)

app.logger.setLevel(logging.INFO)



# Configure SocketIO for cross-device broadcasting
# Note: We use RealtimeBroker with Redis for cross-instance messaging, not SocketIO's message queue
socketio_kwargs = {
    "cors_allowed_origins": "*",
    "manage_session": False,
    # The deployment uses Gunicorn's threaded worker (see Procfile/Dockerfile),
    # which is the matching and portable Socket.IO runtime for this application.
    "async_mode": "threading",
    "logger": False,
    "engineio_logger": False,
    "ping_timeout": 30,
    "ping_interval": 5,
}

app.logger.info("SocketIO configured with threading (RealtimeBroker handles cross-instance messaging)")

socketio = SocketIO(app, **socketio_kwargs)
app.logger.info(f"SocketIO initialized with async_mode: {socketio.async_mode}")

app.extensions["realtime_broker"] = RealtimeBroker(app=app, socketio=socketio)

# ============================================================================
# Stage 13 + Stage 14 AI Service Initialization
# ============================================================================

# Initialize Stage 13 feature service and Stage 14 model service
# These replace the legacy aml_ai_model.pkl with the validated EcoCash AI pipeline
# Note: These will be initialized per-request to use the correct database connection
app.extensions["stage13_feature_service"] = None
app.extensions["stage14_model_service"] = None
app.logger.info("Stage 13 + Stage 14 AI services will be initialized per-request with database connection")



# SocketIO authentication middleware with presence tracking

@socketio.on('connect')
def handle_connect():
    if 'user_id' not in session:
        app.logger.warning("SocketIO connection rejected: no user_id in session")
        return False
    
    user_id = session.get('user_id')
    role = session.get('role', 'unknown')
    sid = request.sid
    username = session.get('username')
    if username:
        # Every browser tab for a signed-in user joins the same private room.
        # This makes unread badges update immediately without exposing direct
        # messages to unrelated connected clients.
        join_room(f"user:{username}")
    
    # Rate limit connection logging to prevent log spam
    broker = app.extensions.get('realtime_broker')
    if broker and broker._redis_client:
        try:
            presence_key = f"presence:user:{user_id}"
            existing = broker._redis_client.hget(presence_key, 'sid')
            if existing and existing.decode('utf-8') == sid:
                # Same socket reconnecting, don't log
                pass
            else:
                app.logger.info(f"User {user_id} (role: {role}) connected via SocketIO, presence stored in Redis")
        except:
            app.logger.info(f"User {user_id} (role: {role}) connected via SocketIO, presence stored in Redis")
    
    # Store presence in Redis for cross-server routing
    if broker and broker._redis_client:
        try:
            presence_key = f"presence:user:{user_id}"
            broker._redis_client.hset(presence_key, mapping={
                'sid': sid,
                'server_id': broker._instance_id,
                'role': role,
                'connected_at': int(time.time())
            })
            broker._redis_client.expire(presence_key, 300)  # 5 minute TTL
            
            # Deliver queued offline messages
            offline_messages = broker.get_offline_queue(user_id)
            if offline_messages:
                app.logger.info(f"Delivering {len(offline_messages)} queued messages to user {user_id}")
                for msg in reversed(offline_messages):  # Deliver in chronological order
                    socketio.emit(msg['event'], msg['data'], to=sid)
        except Exception as e:
            app.logger.error(f"Failed to store presence in Redis: {e}")
    else:
        app.logger.warning(f"User {user_id} (role: {role}) connected via SocketIO (no Redis presence tracking)")
    
    # Send initial connection confirmation
    socketio.emit('connection_confirmed', {'status': 'connected', 'user_id': user_id}, to=sid)
    
    return True


@socketio.on('heartbeat')
def handle_heartbeat():
    """Client heartbeat to maintain connection and refresh presence TTL"""
    if 'user_id' in session:
        user_id = session.get('user_id')
        broker = app.extensions.get('realtime_broker')
        if broker and broker._redis_client:
            try:
                presence_key = f"presence:user:{user_id}"
                broker._redis_client.expire(presence_key, 300)  # Refresh TTL
                app.logger.debug(f"Heartbeat received from user {user_id}")
            except Exception as e:
                app.logger.error(f"Failed to refresh presence TTL: {e}")
    # Separate from Socket.IO transport ping/pong; confirms that the application
    # and server-side presence tracking are both still alive.
    socketio.emit("heartbeat_ack", {"timestamp": time.time()}, to=request.sid)


@socketio.on('disconnect')
def handle_disconnect():
    if 'user_id' in session:
        user_id = session.get('user_id')
        role = session.get('role', 'unknown')
        
        # Remove presence from Redis
        broker = app.extensions.get('realtime_broker')
        if broker and broker._redis_client:
            try:
                presence_key = f"presence:user:{user_id}"
                broker._redis_client.delete(presence_key)
                app.logger.info(f"User {user_id} (role: {role}) disconnected, presence removed from Redis")
            except Exception as e:
                app.logger.error(f"Failed to remove presence from Redis: {e}")
        else:
            app.logger.info(f"User {user_id} (role: {role}) disconnected from SocketIO")
    
    # Mark user as offline
    try:
        conn = connect_db()
        if 'username' in session:
            set_user_online(conn, session['username'], False)
        conn.close()
    except:
        pass


# ============================================================================
# Messaging WebSocket Handlers
# ============================================================================

@socketio.on('send_message')
def handle_send_message(data):
    """Handle incoming message."""
    if 'user_id' not in session:
        socketio.emit('message_error', {'message': 'Not authenticated'}, to=request.sid)
        return

    receiver = str(data.get('receiver') or '').strip()
    content = str(data.get('content') or '').strip()
    
    if not receiver or not content:
        socketio.emit('message_error', {'message': 'Missing receiver or content'}, to=request.sid)
        return
    
    try:
        conn = connect_db()
        
        # Do not trust a username supplied by the browser/session alone. The
        # current account and recipient are resolved from the live users table
        # immediately before every message is persisted.
        sender_user = conn.execute(
            "SELECT * FROM users WHERE id=?", (session['user_id'],)
        ).fetchone()
        receiver_user = fetch_user_by_username(conn, receiver)
        
        if not sender_user or not receiver_user:
            socketio.emit('message_error', {'message': 'User not found'}, to=request.sid)
            conn.close()
            return

        sender = sender_user['username']
        
        can_message, reason = can_user_message(sender_user['role'], receiver_user['role'])
        if can_message and not _is_authorized_messaging_counterpart(conn, sender_user, receiver):
            can_message = False
            reason = 'This is not your assigned secure messaging contact'
        if not can_message:
            socketio.emit('message_error', {'message': reason}, to=request.sid)
            conn.close()
            return
        
        # Get or create conversation
        conv = get_or_create_conversation(conn, sender, receiver)
        
        # Send message
        msg = send_message(conn, conv['id'], sender, receiver, content, sender_user['role'])
        
        # Mark as unread for receiver
        add_unread_message(conn, conv['id'], receiver)
        
        # Emit to both users
        message_data = {
            'id': msg['id'],
            'sender': sender,
            'receiver': receiver,
            'content': msg['content'],
            'status': 'sent',
            'timestamp': msg['created_at'],
            'conversation_id': conv['id']
        }
        
        # Deliver only to the sender and recipient.  Broadcasting direct
        # messages to every connected client was both noisy and unsafe.
        socketio.emit('new_message', message_data, to=f"user:{sender}")
        if receiver != sender:
            socketio.emit('new_message', message_data, to=f"user:{receiver}")
        
        # Broadcast unread badge update
        unread = get_unread_count(conn, receiver)
        socketio.emit('unread_update', unread, to=f"user:{receiver}")
        
        conn.close()
    except Exception as e:
        app.logger.error(f"Error sending message: {e}")
        socketio.emit('message_error', {'message': 'Message could not be sent. Please try again.'}, to=request.sid)


@socketio.on('typing')
def handle_typing(data):
    """Handle typing indicator."""
    if 'username' not in session:
        return
    
    username = session['username']
    conversation_id = data.get('conversation_id')
    
    try:
        conn = connect_db()
        set_typing_indicator(conn, username, conversation_id)
        conn.close()
        
        # Broadcast typing status
        socketio.emit('user_typing', {
            'user': username,
            'conversation_id': conversation_id
        })
    except Exception as e:
        app.logger.error(f"Error handling typing: {e}")


@socketio.on('stop_typing')
def handle_stop_typing(data):
    """Handle stop typing indicator."""
    if 'username' not in session:
        return
    
    username = session['username']
    conversation_id = data.get('conversation_id')
    
    try:
        conn = connect_db()
        set_typing_indicator(conn, username, None)
        conn.close()
        
        socketio.emit('user_stop_typing', {
            'user': username,
            'conversation_id': conversation_id
        })
    except Exception as e:
        app.logger.error(f"Error handling stop typing: {e}")


@socketio.on('mark_read')
def handle_mark_read(data):
    """Mark messages as read."""
    if 'username' not in session:
        return
    
    username = session['username']
    conversation_id = data.get('conversation_id')
    
    try:
        conn = connect_db()
        mark_conversation_as_read(conn, conversation_id, username)
        unread = get_unread_count(conn, username)
        conn.close()

        # Update unread badge
        socketio.emit('unread_update', unread, to=f"user:{username}")
    except Exception as e:
        app.logger.error(f"Error marking messages as read: {e}")


# ============================================================================
# Messaging API Routes
# ============================================================================

def _get_messaging_counterparts(conn, user):
    """Return live, registered messaging contacts for the current role.

    Compliance officers are intentionally given customer records only. The
    users table is the registration authority, so stale conversation rows,
    manually typed names, and deleted accounts cannot populate the contact
    list.
    """
    if user["role"] in {"admin", "customer"}:
        target_role = "compliance"
        return conn.execute(
            "SELECT * FROM users WHERE role=? AND username IS NOT NULL "
            "AND account_number IS NOT NULL ORDER BY id ASC LIMIT 1",
            (target_role,),
        ).fetchall()

    if user["role"] == "compliance":
        # This query runs for every API request rather than using a cached
        # list or prior conversation participants.
        return conn.execute(
            "SELECT * FROM users WHERE role='customer' "
            "AND username IS NOT NULL AND account_number IS NOT NULL "
            "ORDER BY account_number ASC, id ASC",
        ).fetchall()

    return []


def _is_authorized_messaging_counterpart(conn, user, username):
    return any(counterpart["username"] == username for counterpart in _get_messaging_counterparts(conn, user))


@app.route('/api/conversations', methods=['GET'])
@login_required
def api_get_conversations():
    """Get conversations allowed for the current user's role."""
    try:
        conn = connect_db()
        current_user = conn.execute(
            "SELECT * FROM users WHERE id=?", (session['user_id'],)
        ).fetchone()
        counterparts = _get_messaging_counterparts(conn, current_user) if current_user else []
        conversations = get_user_conversations(conn, session['username'])
        allowed_usernames = {counterpart['username'] for counterpart in counterparts}
        conversations = [
            conversation for conversation in conversations
            if conversation['other_participant'] in allowed_usernames
        ]
        conn.close()
        
        return jsonify({
            'status': 'success',
            'conversations': conversations
        })
    except Exception as e:
        app.logger.error(f"Error fetching conversations: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/conversations/<int:conversation_id>/messages', methods=['GET'])
@login_required
def api_get_messages(conversation_id):
    """Get messages for a conversation."""
    try:
        conn = connect_db()
        current_user = fetch_user_by_username(conn, session['username'])
        allowed = any(
            conversation['id'] == conversation_id
            for conversation in get_user_conversations(conn, session['username'])
            if current_user and _is_authorized_messaging_counterpart(
                conn, current_user, conversation['other_participant']
            )
        )
        if not allowed:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Conversation is not available to this user'}), 403

        messages = get_conversation_messages(conn, conversation_id, limit=50)
        conn.close()
        
        return jsonify({
            'status': 'success',
            'messages': messages
        })
    except Exception as e:
        app.logger.error(f"Error fetching messages: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/users/<username>/can-message', methods=['GET'])
@login_required
def api_can_message(username):
    """Check if current user can message target user."""
    try:
        conn = connect_db()
        
        sender_user = fetch_user_by_username(conn, session['username'])
        receiver_user = fetch_user_by_username(conn, username)
        
        if not sender_user or not receiver_user:
            return jsonify({'status': 'error', 'can_message': False, 'message': 'User not found'}), 404
        
        can_message, reason = can_user_message(sender_user['role'], receiver_user['role'])
        if can_message:
            can_message = _is_authorized_messaging_counterpart(conn, sender_user, username)
            if not can_message:
                reason = 'This is not your assigned secure messaging contact'
        conn.close()
        
        return jsonify({
            'status': 'success',
            'can_message': can_message,
            'reason': reason,
            'target_user': {
                'username': username,
                'role': receiver_user['role']
            }
        })
    except Exception as e:
        app.logger.error(f"Error checking message permissions: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/unread-count', methods=['GET'])
@login_required
def api_get_unread_count():
    """Get unread message counts."""
    try:
        conn = connect_db()
        unread = get_unread_count(conn, session['username'])
        conn.close()
        
        return jsonify({
            'status': 'success',
            'unread': unread
        })
    except Exception as e:
        app.logger.error(f"Error fetching unread count: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/user-status/<username>', methods=['GET'])
@login_required
def api_get_user_status(username):
    """Get user's online status."""
    try:
        conn = connect_db()
        status = get_user_online_status(conn, username)
        conn.close()
        
        return jsonify({
            'status': 'success',
            'user_status': status
        })
    except Exception as e:
        app.logger.error(f"Error fetching user status: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/messageable-users', methods=['GET'])
@login_required
def api_get_messageable_users():
    """Get the users current user is permitted to message."""
    try:
        conn = connect_db()
        current_user = conn.execute(
            "SELECT * FROM users WHERE id=?", (session['user_id'],)
        ).fetchone()
        
        if not current_user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        messageable_users = []
        # Build the response directly from verified rows; expose only the
        # contact fields needed by the secure messaging interface.
        for counterpart in _get_messaging_counterparts(conn, current_user):
            status = get_user_online_status(conn, counterpart['username'])
            messageable_users.append({
                'username': counterpart['username'],
                'role': counterpart['role'],
                'account_number': counterpart['account_number'],
                'is_online': status['is_online'],
                'last_seen': status['last_seen']
            })
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'users': messageable_users
        })
    except Exception as e:
        app.logger.error(f"Error fetching messageable users: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================================
# Event Broadcasting Helper
# ============================================================================

def broadcast_event(event_name, payload):
    """Broadcast event using RealtimeBroker."""
    broker = app.extensions.get("realtime_broker")
    if broker:
        broker.publish(event_name, payload)


# ============================================================================
# AI Training Functions
# ============================================================================

def _ai_training_rows(rows):
    histories = {}
    enriched = []
    for row in rows:
        sender = row["sender_account"]
        history = histories.setdefault(sender, {"amounts": [], "recipients": set(), "events": [], "transactions": []})
        profile = _history_profile(row["amount"], row["receiver_account"], row["timestamp"], history)
        item = dict(row)
        item.update(profile)
        enriched.append(item)
        history["amounts"].append(float(row["amount"]))
        history["recipients"].add(row["receiver_account"])
        history["events"].append((_parse_timestamp(row["timestamp"]), float(row["amount"])))
        history["transactions"].append(dict(row))
    return enriched


def _train_ai_model_from_db(conn, emit_events=True):
    # Prevent concurrent AI training
    global _ai_training_in_progress, _ai_training_lock
    with _ai_training_lock:
        if _ai_training_in_progress:
            if app:
                app.logger.info("AI training already in progress, skipping")
            return None
        _ai_training_in_progress = True
    
    try:
        rows = conn.execute(
            """
            SELECT t.id, t.sender_account, t.receiver_account, t.amount, t.transaction_type,
                   t.timestamp, COALESCE(t.generated_label, t.risk_level) as risk_level, t.risk_score, t.channel,
                   COALESCE(u.wealth_segment, 'average') AS wealth_segment
            FROM transactions t
            LEFT JOIN users u ON t.sender_account = u.account_number
            WHERE description != 'Initiated' OR risk_score > 0
            ORDER BY t.timestamp ASC, t.id ASC
            """
        ).fetchall()
        model = train_ai_model(_ai_training_rows(rows))
        if emit_events:
            meta = get_model_metadata()
            broadcast_event("ai_model", {
                "trained": model is not None,
                "training_rows": len(rows),
                "version": meta.get("version", "unknown"),
                "cross_val_f1": meta.get("cross_val_f1_weighted"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        return model
    finally:
        with _ai_training_lock:
            _ai_training_in_progress = False


# ============================================================================
# Flask Routes
# ============================================================================


def seed_demo_data():
    conn = connect_db(app.config["DATABASE"])
    now = datetime.now(timezone.utc).isoformat()

    default_users = [

        (

            username,

            staff["email"],

            staff["id_number"],

            generate_password_hash(staff["password"]),

            staff["role"],

            staff["account_number"],

        )

        for username, staff in STAFF_ACCOUNTS.items()

    ]

    default_users.append(

        ("demo", "demo@example.com", "63-1000003A03", generate_password_hash("demo123"), "customer", "ACC1003")

    )

    for username, email, id_number, pwd_hash, role, acct in default_users:

        # Seed accounts are identified by their immutable username, not by email.
        # Email is user-editable/configurable and is not unique in every legacy
        # database, so matching it here could update the wrong account and leave
        # the actual Admin/Compliance password stale.
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,),
        ).fetchone()

        if existing is None:

            conn.execute(

                "INSERT INTO users (username, email, id_number, password_hash, role, account_number, balance, kyc_status, wealth_segment, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",

                (username, email, id_number, pwd_hash, role, acct, 5000, 'verified', 'average', now),

            )

        else:

            conn.execute(

                """

                UPDATE users

                SET username=?, email=?, id_number=?, password_hash=?, role=?,

                    account_number=?, kyc_status='verified', wealth_segment='average'

                WHERE id=?

                """,

                (username, email, id_number, pwd_hash, role, acct, existing["id"]),

            )

    _seed_wealth_tier_users(conn, now)

    _seed_watchlist(conn)

    conn.commit()

    conn.close()


def _seed_wealth_tier_users(conn, now):
    """Seed users with different wealth tiers for realistic transaction simulation."""
    wealth_tiers = {
        "low": {"count": 5, "balance_range": (500, 5000), "transaction_range": (50, 500)},
        "average": {"count": 5, "balance_range": (10000, 50000), "transaction_range": (500, 5000)},
        "high": {"count": 3, "balance_range": (100000, 500000), "transaction_range": (5000, 50000)},
        "ultra_high": {"count": 2, "balance_range": (1000000, 10000000), "transaction_range": (50000, 500000)},
    }
    
    user_id = 1000
    for tier, config in wealth_tiers.items():
        for i in range(config["count"]):
            username = f"user_{tier}_{i+1}"
            email = f"{username}@example.com"
            id_number = f"63-{user_id:07d}A{user_id % 100:02d}"
            account_number = f"ACC{user_id}"
            balance = random.randint(*config["balance_range"])
            
            existing = conn.execute(
                "SELECT id FROM users WHERE username = ? OR account_number = ?",
                (username, account_number),
            ).fetchone()
            
            if existing is None:
                conn.execute(
                    """
                    INSERT INTO users (username, email, id_number, password_hash, role, account_number, balance, kyc_status, wealth_segment, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                    """,
                    (username, email, id_number, generate_password_hash("password123"), "customer", account_number,
                     balance, "verified", tier, now),
                )
            user_id += 1





def _seed_watchlist(conn):

    """Seed industry-standard sanctions and PEP entries for demonstration screening."""

    now = datetime.now(timezone.utc).isoformat()

    defaults = [

        ("OFAC SDN — Example Entity", "99-0000001X01", None, "sanctions",

         "OFAC Specially Designated Nationals list match (demo entry)"),

        ("UN Consolidated Sanctions — Demo", "99-0000002X02", None, "sanctions",

         "UN Security Council consolidated sanctions list (demo entry)"),

        ("PEP — Senior Government Official", "88-0000001P01", None, "pep",

         "Politically Exposed Person — senior government official"),

        ("Internal Fraud Watch", None, "ACC9999", "internal",

         "Internal fraud investigation — account frozen"),

    ]

    for name, id_num, acct, list_type, reason in defaults:

        existing = conn.execute(

            "SELECT id FROM watchlist WHERE name=? AND list_type=?",

            (name, list_type),

        ).fetchone()

        if existing is None:

            conn.execute(

                """

                INSERT INTO watchlist (name, id_number, account_number, list_type, reason, added_by, added_at)

                VALUES (?,?,?,?,?,?,?)

                """,

                (name, id_num, acct, list_type, reason, 'system', now),

            )





# ───────────────────────────────────────────────────────────── Utilities ──



def get_user_by_id(user_id):

    return get_db().execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()



def get_user_by_username(username):

    return get_db().execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()



def get_user_by_email(email):

    return get_db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()



def get_user_by_id_number(id_number):

    return get_db().execute("SELECT * FROM users WHERE id_number=?", (id_number,)).fetchone()



def get_user_by_account_number(account_number):

    return get_db().execute("SELECT * FROM users WHERE account_number=?", (account_number,)).fetchone()



def normalize_id_number(id_number):

    compact = re.sub(r"[^0-9A-Za-z]", "", id_number).upper()

    if re.fullmatch(r"\d{8,9}[A-Z]\d{2}", compact):

        return f"{compact[:2]}-{compact[2:]}"

    return id_number.strip().upper()



def normalize_account_number(acct):

    return acct.strip().upper()



def is_valid_id_number(id_number):

    return bool(ID_NUMBER_PATTERN.fullmatch(id_number))



def record_activity(actor, action, detail):

    ip = request.remote_addr if request else "system"

    timestamp = datetime.now(timezone.utc).isoformat()

    get_db().execute(

        "INSERT INTO activity_log (actor, action, detail, ip_address, timestamp) VALUES (?,?,?,?,?)",

        (actor, action, detail, ip, timestamp),

    )

    get_db().commit()

    broadcast_event("activity", {

        "actor": actor,

        "action": action,

        "detail": detail,

        "ip_address": ip,

        "timestamp": timestamp,

    })



def get_last_insert_id(conn):

    if is_postgres_database_url(app.config["DATABASE"]):

        return conn.execute("SELECT LASTVAL() as id").fetchone()["id"]

    if is_mysql_database_url(app.config["DATABASE"]):

        return conn.execute("SELECT LAST_INSERT_ID() as id").fetchone()["id"]

    return conn.execute("SELECT last_insert_rowid() as id").fetchone()["id"]



def broadcast_event(event_name, payload):
    if app:
        app.logger.info(f"broadcast_event called: {event_name}")
    app.extensions["realtime_broker"].publish(event_name, payload)





def _stats_payload(conn):

    today_start = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00")

    # Use a single query with subqueries for better performance
    stats_query = """
        SELECT 
            (SELECT COUNT(*) FROM users) as total_users,
            (SELECT COUNT(*) FROM users WHERE role='customer') as customer_users,
            (SELECT COUNT(*) FROM users WHERE role IN ('admin', 'compliance')) as staff_users,
            (SELECT COUNT(*) FROM users WHERE kyc_status IS NULL OR kyc_status!='verified') as kyc_pending,
            (SELECT COUNT(*) FROM users WHERE pep_flag=1) as pep_customers,
            (SELECT COUNT(*) FROM transactions) as total_transactions,
            (SELECT COUNT(*) FROM transactions WHERE risk_level!='normal') as suspicious_transactions,
            (SELECT COUNT(*) FROM transactions WHERE risk_level IN ('suspicious','super_suspicious','high_risk','critical')) as flagged_transactions,
            (SELECT COUNT(*) FROM alerts WHERE status='open') as open_alerts,
            (SELECT COUNT(*) FROM alerts) as total_alerts,
            (SELECT COUNT(*) FROM transactions WHERE risk_level IN ('super_suspicious','high_risk','critical') AND timestamp>=?) as high_risk_today,
            (SELECT COUNT(*) FROM sar_reports WHERE status='draft') as pending_sars,
            (SELECT COUNT(*) FROM sar_reports WHERE status='filed') as filed_sars,
            (SELECT COUNT(*) FROM ctr_reports WHERE status='pending') as pending_ctrs
            ,(SELECT COUNT(*) FROM ctr_reports WHERE status='filed') as filed_ctrs
    """
    row = conn.execute(stats_query, (today_start,)).fetchone()

    return {

        "total_users": row["total_users"],

        "customer_users": row["customer_users"],

        "staff_users": row["staff_users"],

        "kyc_pending": row["kyc_pending"],

        "pep_customers": row["pep_customers"],

        "total_transactions": row["total_transactions"],

        "suspicious_transactions": row["suspicious_transactions"],

        "flagged_transactions": row["flagged_transactions"],

        "open_alerts": row["open_alerts"],

        "total_alerts": row["total_alerts"],

        "high_risk_today": row["high_risk_today"],

        "pending_sars": row["pending_sars"],

        "filed_sars": row["filed_sars"],

        "pending_ctrs": row["pending_ctrs"],

        "filed_ctrs": row["filed_ctrs"],

        "timestamp": datetime.now(timezone.utc).isoformat(),

    }





def broadcast_stats(conn=None):

    conn = conn or get_db()

    broadcast_event("stats", _stats_payload(conn))


def send_otp_email_async(email, otp_code):
    """Send an OTP and report whether the SMTP server accepted it.

    The legacy name is retained for existing callers. Registration must wait
    for this result; otherwise it can claim a code was sent when delivery has
    already failed.
    """
    subject = "StanPro Bank - Verification Code"
    body = f"""
Your verification code is: {otp_code}

This code will expire in 10 minutes.

If you did not request this code, please ignore this email.

StanPro Bank AML Intelligence Platform
"""
    html_body = f"""
<html>
<body>
    <h2>StanPro Bank - Verification Code</h2>
    <p>Your verification code is: <strong>{otp_code}</strong></p>
    <p>This code will expire in 10 minutes.</p>
    <p>If you did not request this code, please ignore this email.</p>
    <p><em>StanPro Bank AML Intelligence Platform</em></p>
</body>
</html>
"""
    result = send_email(email, subject, body, html_body)
    
    if result:
        app.logger.info(f"OTP sent via email to {email}")
    else:
        app.logger.error("OTP email delivery failed for %s", email)
    
    return result





def request_page(parameter="page", default=1):

    try:

        page = int(request.args.get(parameter, default))

    except (TypeError, ValueError):

        return default

    return max(1, page)





def _user_balance_payload(row):

    return {

        "user_id": row["id"],

        "username": row["username"],

        "account_number": row["account_number"],

        "balance": float(row["balance"] or 0),

        "kyc_status": row["kyc_status"],

        "timestamp": datetime.now(timezone.utc).isoformat(),

    }





def serialize_value(value):

    if isinstance(value, Decimal):

        return float(value)

    if isinstance(value, datetime):

        return value.isoformat()

    return value





def serialize_row(row):

    return {key: serialize_value(row[key]) for key in row.keys()}





def serialize_rows(rows):

    return [serialize_row(row) for row in rows]





def broadcast_user_balance(conn, account_number):

    row = conn.execute(

        "SELECT id, username, account_number, balance, kyc_status FROM users WHERE account_number=?",

        (account_number,),

    ).fetchone()

    if row:

        broadcast_event("balance", _user_balance_payload(row))





def broadcast_alert_update(conn, alert_id, event_name="alert_update"):

    row = conn.execute("SELECT * FROM alerts WHERE id=?", (alert_id,)).fetchone()

    if row:

        broadcast_event(event_name, {

            "id": row["id"],

            "transaction_id": row["transaction_id"],

            "account_number": row["account_number"],

            "risk_score": float(row["risk_score"] or 0),

            "risk_level": row["risk_level"],

            "reason": row["reason"],

            "status": row["status"],

            "assigned_to": row["assigned_to"],

            "resolved_by": row["resolved_by"],

            "resolved_at": row["resolved_at"],

            "timestamp": row["timestamp"],

        })





def _json_safe(value):

    if value is None or isinstance(value, (str, int, float, bool)):

        return value

    try:

        return float(value)

    except (TypeError, ValueError):

        return str(value)





def broadcast_report_event(kind, row):

    broadcast_event(kind, {

        key: _json_safe(row[key])

        for key in row.keys()

    })



def _generate_sar_ref():

    ts = datetime.now(timezone.utc)

    return f"SAR-{ts.year}-{ts.strftime('%m%d')}-{random.randint(1000,9999)}"


def update_customer_risk_rating(db, account_number, action, current_risk):
    """Update customer risk rating based on alert action."""
    risk_levels = ["standard", "medium", "high", "critical"]
    
    try:
        current_idx = risk_levels.index(current_risk.lower()) if current_risk.lower() in risk_levels else 0
    except:
        current_idx = 0
    
    if action == "resolve":
        # Reduce risk level on resolve
        new_idx = max(0, current_idx - 1)
    elif action == "escalate":
        # Increase risk level on escalate
        new_idx = min(len(risk_levels) - 1, current_idx + 1)
    elif action == "file_sar":
        # Set to high or critical on SAR
        new_idx = min(len(risk_levels) - 1, current_idx + 2)
    else:
        return current_risk
    
    new_risk = risk_levels[new_idx]
    
    # Update database (caller will commit)
    db.execute("UPDATE users SET risk_rating=? WHERE account_number=?", (new_risk, account_number))
    
    return new_risk


def _generate_ctr_ref():
    ts = datetime.now(timezone.utc)
    return f"CTR-{ts.year}-{ts.strftime('%m%d')}-{random.randint(1000,9999)}"


def _ai_training_rows(rows):

    histories = {}

    enriched = []

    for row in rows:

        sender = row["sender_account"]

        history = histories.setdefault(sender, {"amounts": [], "recipients": set(), "events": [], "transactions": []})

        profile = _history_profile(row["amount"], row["receiver_account"], row["timestamp"], history)

        item = dict(row)

        item.update(profile)

        enriched.append(item)

        history["amounts"].append(float(row["amount"]))
        history["recipients"].add(row["receiver_account"])
        history["events"].append((_parse_timestamp(row["timestamp"]), float(row["amount"])))
        history["transactions"].append(dict(row))

    return enriched





def _train_ai_model_from_db(conn, emit_events=True):
    # Prevent concurrent AI training
    global _ai_training_in_progress, _ai_training_lock
    with _ai_training_lock:
        if _ai_training_in_progress:
            if app:
                app.logger.info("AI training already in progress, skipping")
            return None
        _ai_training_in_progress = True
    
    try:
        rows = conn.execute(

            """

            SELECT t.id, t.sender_account, t.receiver_account, t.amount, t.transaction_type,

                   t.timestamp, COALESCE(t.generated_label, t.risk_level) as risk_level, t.risk_score, t.channel,

                   COALESCE(u.wealth_segment, 'average') AS wealth_segment

            FROM transactions t

            LEFT JOIN users u ON t.sender_account = u.account_number

            WHERE description != 'Initiated' OR risk_score > 0

            ORDER BY t.timestamp ASC, t.id ASC

            """

        ).fetchall()

        model = train_ai_model(_ai_training_rows(rows))

        if emit_events:

            meta = get_model_metadata()

            broadcast_event("ai_model", {

                "trained": model is not None,

                "training_rows": len(rows),

                "version": meta.get("version", "unknown"),

                "cross_val_f1": meta.get("cross_val_f1_weighted"),

                "timestamp": datetime.now(timezone.utc).isoformat(),

            })

        return model
    finally:
        with _ai_training_lock:
            _ai_training_in_progress = False





def _transaction_payload(row):

    confidence = row["ai_confidence"] if "ai_confidence" in row.keys() else 0

    ctr_required = row["ctr_required"] if "ctr_required" in row.keys() else 0

    sar_required = row["sar_required"] if "sar_required" in row.keys() else 0

    return {

        "id": row["id"],

        "sender_account": row["sender_account"],

        "receiver_account": row["receiver_account"],

        "amount": float(row["amount"]),

        "type": row["transaction_type"],

        "transaction_type": row["transaction_type"],

        "timestamp": row["timestamp"],

        "risk_level": row["risk_level"],

        "risk_score": float(row["risk_score"] or 0),

        "rule_level": row["rule_level"] or "normal",

        "rule_score": float(row["rule_score"] or 0),

        "ai_risk_level": row["ai_risk_level"] or "unavailable",

        "ai_confidence": float(confidence or 0),

        "ctr_required": bool(ctr_required),

        "sar_required": bool(sar_required),

        "channel": row["channel"] if "channel" in row.keys() else "online",

        "description": row["description"] or "",

    }





RISK_RANK = {

    "normal": 0,

    "low": 1,

    "suspicious": 2,

    "super_suspicious": 3,

    "high_risk": 3,

    "critical": 4,

}





def _risk_level_from_score(score):

    if score >= 80:

        return "critical"

    if score >= 60:

        return "high_risk"

    if score >= 40:

        return "suspicious"

    if score >= 25:

        return "low"

    return "normal"



def _calibrate_generated_transaction_risk(label, risk_score, risk_level, reason, mandatory=False):
    """Keep synthetic generation labels aligned with the intended AML split."""
    label = (label or "normal").lower()

    if label == "normal":
        if mandatory:
            calibrated_score = max(risk_score, 35)
            calibrated_level = "high_risk" if calibrated_score >= 60 else "suspicious"
            return calibrated_score, calibrated_level, reason
        return 20, "normal", "Synthetic normal transaction preserved as normal."

    if label == "suspicious":
        calibrated_score = max(risk_score, 45)
        calibrated_level = "high_risk" if calibrated_score >= 60 else "suspicious"
        return calibrated_score, calibrated_level, reason

    calibrated_score = max(risk_score, 70)
    calibrated_level = "critical" if calibrated_score >= 80 else "high_risk"
    return calibrated_score, calibrated_level, reason



def _combine_rule_ai_risk(rule_score, rule_level, rule_reason, triggered_rules, ai_level, ai_confidence):
    # Simplified - mandatory check now based on screening severity only
    mandatory = any(r.get("severity") == "critical" for r in triggered_rules) if triggered_rules else False

    rule_rank = RISK_RANK.get(rule_level, 0)

    ai_reason = "AI model unavailable or not confident enough to affect final risk."

    final_score = rule_score

    final_level = rule_level

    final_reason = rule_reason



    if ai_level:

        ai_reason = (

            f"AI behavior model predicted {ai_level.replace('_', ' ')} "

            f"with {ai_confidence:.0%} confidence."

        )



    if ai_level and ai_confidence >= 0.55:

        ai_score = AI_RISK_SCORES.get(ai_level, rule_score)

        ai_rank = RISK_RANK.get(ai_level, 0)



        if not mandatory:

            ai_weight = min(0.85, max(0.60, ai_confidence))

            rule_weight = 1 - ai_weight

            blended_score = round((ai_score * ai_weight) + (rule_score * rule_weight))



            if ai_level == "normal" and ai_confidence >= 0.85 and rule_rank < RISK_RANK["low"]:

                final_score = min(blended_score, 24)

                final_level = "normal"

                final_reason = (

                    f"AI-led behavior model recognized this as normal for the sender "

                    f"({ai_confidence:.0%} confidence), so non-mandatory rule risk was reduced. "

                    f"Rule review: {rule_reason}"

                )

            else:

                if ai_level == "normal" and rule_rank >= RISK_RANK["suspicious"]:

                    blended_score = max(rule_score, blended_score)

                final_score = max(0, min(100, blended_score))

                final_level = _risk_level_from_score(final_score)

                if ai_level == "normal" and rule_rank >= RISK_RANK["suspicious"]:

                    ai_direction = "reviewed but did not downgrade"

                else:

                    ai_direction = "increased" if ai_rank > rule_rank else "tempered"

                final_reason = (

                    f"AI-led behavior model {ai_direction} the behavioral risk "

                    f"({ai_confidence:.0%} confidence, {ai_weight:.0%} AI weighting). "

                    f"Rule review: {rule_reason}"

                )

        elif ai_level == "normal":

            final_reason = (

                f"Mandatory compliance rule preserved despite AI normal prediction "

                f"({ai_confidence:.0%} confidence). Rule review: {rule_reason}"

            )

        elif ai_rank > rule_rank:

            final_score = max(rule_score, ai_score)

            final_level = _risk_level_from_score(final_score)

            final_reason = (

                f"Mandatory compliance rule preserved and AI behavior model added elevated context "

                f"({ai_confidence:.0%} confidence). Rule review: {rule_reason}"

            )



    if mandatory and RISK_RANK.get(final_level, 0) < RISK_RANK.get(rule_level, 0):

        final_score = rule_score

        final_level = rule_level

        final_reason = f"Mandatory compliance rule preserved. {rule_reason}"



    return final_score, final_level, final_reason, ai_reason





# Flag to disable rule-based engine for AI-only testing
_RULE_ENGINE_ENABLED = False

def set_rule_engine_enabled(enabled: bool):
    """Enable or disable the rule-based engine for AI-only testing."""
    global _RULE_ENGINE_ENABLED
    _RULE_ENGINE_ENABLED = enabled

def process_transaction_event(

    conn,

    transaction_id,

    sender_account,

    receiver_account,

    amount,

    transaction_type,

    timestamp,

    account_number=None,

    emit_events=True,

    destination_country="ZW",

    generated_label=None,

    scenario_reason=None,

):

    sender_user = conn.execute(

        "SELECT username, id_number, pep_flag FROM users WHERE account_number=?",

        (sender_account,),

    ).fetchone()

    receiver_user = conn.execute(

        "SELECT username, id_number, pep_flag FROM users WHERE account_number=?",

        (receiver_account,),

    ).fetchone()



    screening_hits = []

    for party, user_row, acct in (

        ("sender", sender_user, sender_account),

        ("receiver", receiver_user, receiver_account),

    ):

        if user_row:

            party_hits = screen_entity(

                conn,

                name=user_row["username"],

                id_number=user_row["id_number"],

                account_number=acct,

            )

            screening_hits.extend(party_hits)



    screen_delta, screen_reason, screen_json = screening_summary(screening_hits)

    # Rules are evaluated before behavioural/ML blending.  They provide the
    # auditable typology evidence that a statistical model alone cannot infer.
    if _RULE_ENGINE_ENABLED:
        triggered = [rule.payload() for rule in assess_rules(
            conn, amount=amount, tx_type=transaction_type, sender=sender_account,
            receiver=receiver_account, timestamp=timestamp,
            destination_country=destination_country, exclude_transaction_id=transaction_id,
        )]
        if screen_delta:
            triggered.append({
                "rule_id": "SCREENING",
                "triggered": True,
                "score_delta": screen_delta,
                "reason": screen_reason,
                "severity": "critical" if any(h.list_type == "sanctions" for h in screening_hits) else "warning",
                "typology": "Watchlist / PEP Screening",
            })
        rule_score = min(100, sum(int(rule["score_delta"]) for rule in triggered))
        rule_level = _risk_level_from_score(rule_score)
        rule_reason = "; ".join(rule["reason"] for rule in triggered) or "No rule indicators"
        rules_json = json.dumps(triggered + screen_json)
    else:
        # Rule engine disabled - use AI-only approach
        triggered = []
        rule_score = 0
        rule_level = "normal"
        rule_reason = "Rule engine disabled - AI-only mode"
        rules_json = json.dumps([])

    # ============================================================================
    # STAGE 13 + STAGE 14 AI PREDICTION (Replaces legacy aml_ai_model.pkl)
    # ============================================================================
    
    # Build transaction dict for Stage 13 feature service
    # Must include id for temporal safety (timestamp, id) ordering
    transaction_dict = {
        "id": transaction_id,
        "sender_account": sender_account,
        "receiver_account": receiver_account,
        "amount": amount,
        "transaction_type": transaction_type,
        "timestamp": timestamp,
        "destination_country": destination_country,
    }
    
    # Get agent_id if available
    tx_row = conn.execute("SELECT channel, agent_id FROM transactions WHERE id=?", (transaction_id,)).fetchone()
    if tx_row:
        if tx_row["channel"]:
            transaction_dict["channel"] = tx_row["channel"]
        if tx_row["agent_id"]:
            transaction_dict["agent_id"] = tx_row["agent_id"]
    
    # Stage 14 AI prediction using Stage 13 features
    stage14_prediction = None
    stage14_probability = None
    stage14_is_suspicious = False
    ai_reason = "Stage 14 AI model unavailable"
    
    try:
        # Initialize Stage 13 feature service with current database connection
        # This ensures temporal safety and proper database context
        if not hasattr(conn, 'stage13_service'):
            # Create a minimal adapter wrapper for Stage 13
            class MinimalAdapter:
                def __init__(self, connection):
                    self.connection = connection
                    self.engine = "sqlite"
                
                def execute(self, query, params=()):
                    # Stage 13 service uses ? placeholders for SQLite compatibility
                    cursor = self.connection.execute(query, params)
                    return cursor
            
            db_adapter = MinimalAdapter(conn)
            conn.stage13_service = Stage13FeatureService(db_adapter)
            conn.stage14_service = get_stage14_model_service(conn.stage13_service)
        
        stage14_service = conn.stage14_service
        if stage14_service and stage14_service.model_loaded:
            # Generate prediction using Stage 13 + Stage 14 pipeline
            stage14_prediction = stage14_service.predict(transaction_dict)
            stage14_probability = stage14_prediction.probability
            stage14_is_suspicious = stage14_prediction.is_suspicious
            
            # Map binary prediction to risk level
            # Stage 14: 0 = normal, 1 = suspicious_pattern
            if stage14_is_suspicious:
                ai_level = "suspicious_pattern"
                ai_confidence = stage14_probability
                ai_reason = f"Stage 14 AML model detected suspicious pattern (probability: {stage14_probability:.2%}, threshold: 0.35)"
            else:
                ai_level = "normal"
                ai_confidence = 1.0 - stage14_probability
                ai_reason = f"Stage 14 AML model: normal transaction (probability: {stage14_probability:.2%})"
            
            app.logger.info(f"Stage 14 prediction for transaction {transaction_id}: "
                          f"probability={stage14_probability:.4f}, "
                          f"is_suspicious={stage14_is_suspicious}, "
                          f"ai_level={ai_level}")
        else:
            app.logger.warning(f"Stage 14 model service not available for transaction {transaction_id}")
            ai_level = None
            ai_confidence = 0.0
    except Exception as e:
        app.logger.error(f"Stage 14 prediction failed for transaction {transaction_id}: {e}")
        ai_level = None
        ai_confidence = 0.0
        ai_reason = f"Stage 14 AI prediction error: {str(e)}"
    
    # Convert Stage 14 binary prediction to risk score for compatibility
    # Stage 14 threshold is 0.35 - map probability to 0-100 scale
    if stage14_probability is not None:
        # Map probability to risk score: 0.35 threshold maps to 40 risk score
        # probability < 0.35 -> normal (score < 40)
        # probability >= 0.35 -> suspicious (score >= 40)
        ai_score = int((stage14_probability / 0.35) * 40) if stage14_probability < 0.35 else int(40 + ((stage14_probability - 0.35) / 0.65) * 60)
        ai_score = max(0, min(100, ai_score))
    else:
        ai_score = 0
    
    # Behavioural evidence is customer-specific and is never the sole reason
    # to suppress a confirmed compliance typology.
    behavioral_score, behavioral_level, behavioral_reason, anomaly_reasons = assess_transaction_behavioral_risk(
        conn, transaction_dict, sender_account
    )
    
    # Combine AI and behavioral signals
    behavioral_confidence = min(0.90, behavioral_score / 100) if behavioral_score else 0
    combined_ai_score = round((ai_score * 0.7) + (behavioral_score * behavioral_confidence * 0.3))
    
    mandatory = any(h.list_type == "sanctions" for h in screening_hits) or any(
        rule["severity"] == "critical" for rule in triggered
    )
    
    # Final risk determination
    if mandatory:
        risk_score = max(rule_score, combined_ai_score)
    else:
        risk_score = max(rule_score, combined_ai_score)
    
    risk_level = _risk_level_from_score(risk_score)
    
    # Build reason string
    reasons = []
    if triggered:
        reasons.append(rule_reason)
    if stage14_probability is not None:
        reasons.append(ai_reason)
    if behavioral_score >= 40:
        reasons.append(behavioral_reason)
    if scenario_reason:
        reasons.append(f"Reason: {scenario_reason}")
    reason = "; ".join(reasons) or "Routine transaction — no material AML indicators"

    if generated_label is not None:
        risk_score, risk_level, reason = _calibrate_generated_transaction_risk(
            generated_label,
            risk_score,
            risk_level,
            reason,
            mandatory=mandatory,
        )

    # Store AI results
    final_ai_level = ai_level if ai_level else behavioral_level
    final_ai_confidence = ai_confidence if ai_confidence else behavioral_confidence

    ctr_required = 1 if transaction_type in ("deposit", "withdraw") and float(amount) >= CTR_THRESHOLD else 0
    sar_required = 1 if any(rule["rule_id"] == "R07" for rule in triggered) else 0
    
    # SAR required for suspicious patterns from Stage 14
    if stage14_is_suspicious:
        sar_required = 1

    if risk_level in ("suspicious", "super_suspicious", "high_risk", "critical"):
        sar_required = 1

    conn.execute(
        """
        UPDATE transactions
        SET risk_score=?, risk_level=?, rule_score=?, rule_level=?, rule_reason=?,
            ai_risk_level=?, ai_confidence=?, ai_reason=?, description=?, rules_triggered=?,
            ctr_required=?, sar_required=?, destination_country=?, screening_hits=?
        WHERE id=?
        """,
        (
            risk_score, risk_level, rule_score, rule_level, rule_reason,
            final_ai_level, final_ai_confidence, ai_reason, reason, rules_json,
            ctr_required, sar_required, destination_country,
            json.dumps(screen_json) if screen_json else "[]",
            transaction_id,
        ),
    )



    created_alert = create_alert_if_needed(

        conn, transaction_id, account_number or sender_account,

        risk_score, risk_level, reason, rules_json, timestamp,

    )



    # Auto-generate CTR

    ctr_id = None

    if ctr_required:

        existing_ctr = conn.execute(

            "SELECT id FROM ctr_reports WHERE transaction_id=?", (transaction_id,)

        ).fetchone()

        if not existing_ctr:

            conn.execute(

                """

                INSERT INTO ctr_reports (transaction_id, account_number, amount,

                    generated_by, status, created_at)

                VALUES (?,?,?,?,?,?)

                """,

                (transaction_id, account_number or sender_account, amount,

                 'system', 'pending', datetime.now(timezone.utc).isoformat()),

            )

            ctr_id = get_last_insert_id(conn)



    if emit_events:

        tx_row = conn.execute("SELECT * FROM transactions WHERE id=?", (transaction_id,)).fetchone()

        if tx_row:

            broadcast_event("transaction", _transaction_payload(tx_row))

        if created_alert:
            # Include Stage 14 AI information in alert broadcast
            alert_data = {
                "id": created_alert,
                "transaction_id": transaction_id,
                "account_number": account_number or sender_account,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "reason": reason,
                "timestamp": timestamp,
            }
            # Add Stage 14 specific information if available
            if stage14_probability is not None:
                alert_data["stage14_probability"] = stage14_probability
                alert_data["stage14_is_suspicious"] = stage14_is_suspicious
                alert_data["ai_model"] = "Stage 14 AML"
            
            broadcast_event("alert", alert_data)

        if ctr_required and ctr_id:

            row = conn.execute("SELECT * FROM ctr_reports WHERE id=?", (ctr_id,)).fetchone()

            if row:

                broadcast_report_event("ctr_report", row)

        broadcast_stats(conn)



    return risk_score, risk_level, reason, created_alert





# ───────────────────────────────────────────────────── Background monitor ──



def monitor_transactions():

    while not app.config.get("MONITOR_STOP", False):

        try:

            with app.app_context():

                conn = connect_db()

                last_id = app.config.get("LAST_MONITORED_TRANSACTION_ID", 0)

                rows = conn.execute(

                    """

                    SELECT id, sender_account, receiver_account, amount, transaction_type, timestamp

                    FROM transactions

                    WHERE id>? AND risk_score=0 AND description='Initiated'

                    ORDER BY id ASC

                    """,

                    (last_id,),

                ).fetchall()

                for row in rows:

                    process_transaction_event(

                        conn, row["id"], row["sender_account"], row["receiver_account"],

                        row["amount"], row["transaction_type"], row["timestamp"],

                        account_number=row["sender_account"],

                    )

                    app.config["LAST_MONITORED_TRANSACTION_ID"] = row["id"]

                conn.commit()

                if rows:

                    # Train AI model in background thread to avoid blocking monitor
                    def train_in_background():
                        training_conn = None
                        try:
                            # The monitor closes its connection below. Training
                            # owns an independent connection so it cannot race
                            # with that cleanup.
                            training_conn = connect_db()
                            _train_ai_model_from_db(training_conn)
                        except Exception as e:
                            if app:
                                app.logger.error(f"Background AI training in monitor failed: {e}")
                        finally:
                            if training_conn is not None:
                                training_conn.close()
                    threading.Thread(target=train_in_background, daemon=True).start()

                conn.close()

        except Exception:

            pass

        time.sleep(app.config.get("REALTIME_POLL_INTERVAL", 0.5))





def ensure_background_monitor():
    if app.config.get("TESTING") or app.config.get("MONITOR_RUNNING"):
        return

    app.config["MONITOR_RUNNING"] = True
    threading.Thread(target=monitor_transactions, daemon=True).start()


# ───────────────────────────────────────────────── Security / middleware ──

@app.before_request
def enforce_security_headers():
    request.environ.setdefault("werkzeug.request", request)


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
    return response


@app.context_processor

def inject_user():

    user = None

    if "user_id" in session:

        user = get_user_by_id(session["user_id"])

    return {
        "current_user": user,
        "staff_login_identifiers": [
            identifier.casefold()
            for username, staff in STAFF_ACCOUNTS.items()
            for identifier in (username, staff["email"])
        ],
    }





# ─────────────────────────────────────────────────────────────── Routes ──



@app.route("/")

def index():

    return redirect(url_for("dashboard_redirect"))





@app.route("/health")

def health():

    broker = app.extensions.get("realtime_broker")

    status = {

        "status": "ok",

        "service": "stanpro-aml",

        "timestamp": datetime.now(timezone.utc).isoformat(),

        "realtime": {

            "subscribers": len(broker._subscribers) if broker else 0,

            "redis_connected": broker._redis_client is not None if broker else False,

            "kafka_connected": broker._kafka_producer is not None if broker else False,

        },

        "database": app.config.get("DATABASE", "unknown"),

        "active_streams": len(app.config.get("ACTIVE_STREAMS", {})),

    }

    return status, 200





@app.route("/dashboard")

def dashboard_redirect():

    if "user_id" not in session:

        return redirect(url_for("login"))

    user = get_user_by_id(session["user_id"])

    if user is None:

        session.clear()

        flash("Session expired. Please log in again.")

        return redirect(url_for("login"))

    if user["role"] == "customer":

        return redirect(url_for("customer_dashboard"))

    if user["role"] == "compliance":

        return redirect(url_for("compliance_dashboard"))

    return redirect(url_for("admin_dashboard"))


@app.route("/messages")
@login_required
def messages():
    """Real-time messaging page."""
    user = get_user_by_id(session["user_id"])
    
    if not user:
        flash("User not found.")
        return redirect(url_for("login"))
    
    # Check if user can message
    if user["role"] not in ["admin", "compliance", "customer"]:
        flash("You don't have permission to access messaging.")
        return redirect(url_for("dashboard_redirect"))
    
    return render_template("messages.html", user=user)


# ── Auth ──



def send_otp_email(recipient_email, otp):

    if app.config.get("TESTING"):
        print(f"[TESTING MODE] Would send OTP to {recipient_email}: {otp}")
        return True

    sender_email = os.environ.get("SMTP_EMAIL")

    sender_password = os.environ.get("SMTP_PASSWORD")

    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")

    smtp_port = int(os.environ.get("SMTP_PORT", "587"))

    if not sender_email or not sender_password:
        print(f"ERROR: SMTP credentials not configured")
        raise ValueError("SMTP credentials not configured")

    print(f"[EMAIL] Preparing to send OTP to {recipient_email}")
    print(f"[EMAIL] From: {sender_email}, Server: {smtp_server}:{smtp_port}")

    msg = EmailMessage()

    msg["Subject"] = "StanPro Bank — Your verification code"

    msg["From"] = sender_email

    msg["To"] = recipient_email

    msg.set_content(f"Your StanPro Bank verification code is: {otp}\n\nThis code expires in 10 minutes.")

    try:
        print(f"[EMAIL] Connecting to SMTP server...")
        with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
            print(f"[EMAIL] Connected, starting TLS...")
            server.starttls()
            print(f"[EMAIL] TLS started, logging in...")
            server.login(sender_email, sender_password)
            print(f"[EMAIL] Login successful, sending message...")
            server.send_message(msg)
            print(f"[EMAIL] ✓ Message sent successfully")

    except Exception as e:
        print(f"[EMAIL] ✗ Error during send: {type(e).__name__}: {e}")
        import traceback
        print(f"[EMAIL] Traceback: {traceback.format_exc()}")
        raise

    return True


def _legacy_background_otp_sender(recipient_email, otp):

    def _send():
        with app.app_context():
            try:
                print(f"[ASYNC EMAIL] Starting to send OTP to {recipient_email}...")
                send_otp_email(recipient_email, otp)
                print(f"[ASYNC EMAIL] ✓ OTP email sent successfully to {recipient_email}")

            except Exception as e:
                import traceback
                error_msg = f"Failed to send OTP email to {recipient_email}: {str(e)}"
                print(f"[ASYNC EMAIL] ✗ {error_msg}")
                print(f"[ASYNC EMAIL] Traceback: {traceback.format_exc()}")
                app.logger.error(f"{error_msg}\n{traceback.format_exc()}")

    thread = threading.Thread(target=_send, daemon=False)  # Changed to daemon=False for better visibility

    thread.start()
    # Give thread a small window to start execution
    time.sleep(0.1)

    return True





@app.route("/register", methods=["GET", "POST"])

def register():

    if request.method == "POST":

        otp = request.form.get("otp", "").strip()

        if otp:

            pending = session.get("pending_registration")

            if not pending:

                flash("Registration session expired. Please start again.")

                return redirect(url_for("register"))

            if time.time() > pending.get("expires_at", 0):

                session.pop("pending_registration", None)

                flash("Verification code expired. Please register again.")

                return redirect(url_for("register"))

            if str(otp) != str(pending.get("otp")):

                flash("Invalid verification code.")

                return render_template("register.html", otp_step=True, email=pending.get("email"))



            reg_hits = screen_entity(

                get_db(),

                name=pending["username"],

                id_number=pending["id_number"],

            )

            if is_registration_blocked(reg_hits):

                session.pop("pending_registration", None)

                flash("Registration cannot proceed — sanctions screening match detected. Contact compliance.")

                record_activity("system", "registration_blocked", f"Sanctions hit for {pending['username']}")

                return redirect(url_for("register"))



            user_count = get_db().execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]

            acct = f"ACC{1000 + int(user_count or 0) + 1}"

            pep_flag = 1 if any(h.list_type == "pep" for h in reg_hits) else 0

            kyc_status = "pending_edd" if pep_flag else "pending"

            get_db().execute(

                "INSERT INTO users (username,email,id_number,password_hash,role,account_number,balance,kyc_status,pep_flag,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",

                (pending["username"], pending["email"], pending["id_number"],

                 pending["password_hash"], pending["role"], acct, 5000, kyc_status, pep_flag,

                 datetime.now(timezone.utc).isoformat()),

            )

            get_db().commit()

            session.pop("pending_registration", None)

            user = get_user_by_username(pending["username"])

            session["user_id"] = user["id"]

            session["role"] = user["role"]

            record_activity(pending["username"], "register", f"New {pending['role']} registered")

            flash("Account created. Welcome to StanPro Bank AML Portal.")

            return redirect(url_for("dashboard_redirect"))



        username = request.form.get("username", "").strip()

        email = request.form.get("email", "").strip().lower()

        id_number = normalize_id_number(request.form.get("id_number", ""))

        password = request.form.get("password", "")

        role = "customer"



        if not all([username, email, id_number, password]):

            flash("All fields are required.")

            return render_template("register.html")

        if username.lower() in RESERVED_STAFF_USERNAMES:

            flash("That username is reserved for bank staff.")

            return render_template("register.html")

        if not is_valid_id_number(id_number):

            flash(ID_NUMBER_FORMAT_MESSAGE)

            return render_template("register.html")

        if get_user_by_username(username):

            flash("Username already taken.")

            return render_template("register.html")

        if get_user_by_email(email):

            flash("Email already registered.")

            return render_template("register.html")

        if get_user_by_id_number(id_number):

            flash("ID number already registered.")

            return render_template("register.html")



        # Generate server-side OTP
        otp_code = f"{random.randint(100000, 999999)}"
        
        session["pending_registration"] = {

            "username": username, "email": email, "id_number": id_number,

            "password_hash": generate_password_hash(password), "role": role,

            "otp": otp_code, "expires_at": time.time() + 600,

        }

        # Do not show the verification step until SMTP accepts the message.
        if not send_otp_email_async(email, otp_code):
            session.pop("pending_registration", None)
            flash("Could not send verification code. Please check the email address or try again later.")
            return render_template("register.html")

        flash(f"Verification code sent to {email}.")

        return render_template("register.html", otp_step=True, email=email)

    return render_template("register.html")







@app.route("/login", methods=["GET", "POST"])

def login():

    if request.method == "POST":

        login_identifier = request.form.get("login", "").strip()

        username = request.form.get("username", "").strip()

        email = request.form.get("email", "").strip().lower()

        if not email and "@" in login_identifier:

            email = login_identifier.lower()

        id_number = normalize_id_number(request.form.get("id_number", ""))

        password = request.form.get("password", "")

        # ``email`` is retained for API/backward-compatible form submissions;
        # the browser form itself submits the same value as ``login``.
        staff_identifier = login_identifier or username or email
        staff_username = next(
            (
                name
                for name, staff in STAFF_ACCOUNTS.items()
                if name.casefold() == staff_identifier.casefold()
                or staff["email"].casefold() == staff_identifier.casefold()
            ),
            None,
        )
        login_key = staff_username or staff_identifier
        # Security: Check rate limiting for staff login
        can_login, lockout_message = check_login_attempts(login_key)
        if not can_login:
            flash(lockout_message)
            return render_template("login.html")

        if staff_username:
            staff = STAFF_ACCOUNTS[staff_username]
            user = get_user_by_username(staff_username)
            if (
                user
                and user["role"] == staff["role"]
                and check_password_hash(user["password_hash"], password)
            ):
                session["user_id"] = user["id"]
                session["role"] = user["role"]
                session["username"] = user["username"]
                record_activity(staff_username, "login", f"Staff login from {request.remote_addr}")
                record_login_attempt(login_key, True)
                flash("Welcome back.")
                return redirect(url_for("dashboard_redirect"))
            flash("Invalid credentials.")
            record_activity(staff_username, "failed_login", f"Failed staff login attempt from {request.remote_addr}")
            is_locked = record_login_attempt(login_key, False)
            if is_locked:
                flash("Too many failed attempts. Account locked for 15 minutes.")
            return render_template("login.html")

        customer_identifier = email or login_identifier or username
        # Security: Check rate limiting for customer login
        can_login, lockout_message = check_login_attempts(customer_identifier)
        if not can_login:
            flash(lockout_message)
            return render_template("login.html")

        if not all([customer_identifier, id_number, password]):
            flash("All fields are required.")
            return render_template("login.html")

        if not is_valid_id_number(id_number):
            flash(ID_NUMBER_FORMAT_MESSAGE)
            return render_template("login.html")

        # MySQL collation varies by deployment.  Make customer lookup explicitly
        # case-insensitive so an email or username's letter case cannot prevent login.
        if email:
            user = get_db().execute(
                "SELECT * FROM users WHERE LOWER(email)=LOWER(?) LIMIT 1", (email,)
            ).fetchone()
        else:
            user = get_db().execute(
                "SELECT * FROM users WHERE LOWER(username)=LOWER(?) LIMIT 1", (customer_identifier,)
            ).fetchone()

        is_customer = bool(user and user["role"] == "customer")
        # Older records may have been stored without the display hyphen or in
        # lowercase. Normalize the persisted value before comparing it.
        id_matches = bool(
            is_customer and normalize_id_number(user["id_number"] or "") == id_number
        )
        password_matches = bool(id_matches and check_password_hash(user["password_hash"], password))
        if password_matches:
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["username"] = user["username"]
            record_activity(customer_identifier, "login", f"Login from {request.remote_addr}")
            record_login_attempt(customer_identifier, True)
            flash("Welcome back.")
            return redirect(url_for("dashboard_redirect"))

        # Keep the UI response generic, but log enough to diagnose a deployment
        # database mismatch without storing the supplied password or identifier.
        app.logger.warning(
            "Customer login rejected: account_found=%s role_customer=%s id_matches=%s password_matches=%s db_engine=%s",
            bool(user), is_customer, id_matches, password_matches, get_db().engine,
        )
        flash("Invalid credentials.")
        record_activity(customer_identifier, "failed_login", f"Failed login attempt from {request.remote_addr}")
        is_locked = record_login_attempt(customer_identifier, False)
        if is_locked:
            flash("Too many failed attempts. Account locked for 15 minutes.")
    return render_template("login.html")


@app.route("/logout")

def logout():

    if "user_id" in session:

        user = get_user_by_id(session["user_id"])

        if user:

            record_activity(user["username"], "logout", "User logged out")

    session.clear()

    flash("You have been signed out.")

    return redirect(url_for("login"))


@app.route("/forgot-password", methods=["GET", "POST"])

def forgot_password():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()

        if not email:

            flash("Email is required.")

            return render_template("forgot_password.html")

        user = get_user_by_email(email)

        if user:

            # Generate reset token
            reset_token = f"{random.randint(100000, 999999)}"
            
            # Store token in database (using a simple approach - in production, use a dedicated table)
            session["password_reset"] = {
                "user_id": user["id"],
                "token": reset_token,
                "expires_at": time.time() + 600  # 10 minutes
            }
            
            # Send email with reset token
            if send_otp_email_async(email, reset_token):
                flash(f"Password reset code sent to {email}.")
                return redirect(url_for("reset_password"))
            flash("Could not send reset code. Please try again later.")
            return render_template("forgot_password.html")
        
        # Always show same message for security (don't reveal if email exists)
        flash("If an account exists with this email, a reset code will be sent.")
        return render_template("forgot_password.html")

    return render_template("forgot_password.html")


@app.route("/reset-password", methods=["GET", "POST"])

def reset_password():

    reset_data = session.get("password_reset")
    
    if not reset_data:
        flash("Password reset session expired. Please start again.")
        return redirect(url_for("forgot_password"))
    
    if time.time() > reset_data.get("expires_at", 0):
        session.pop("password_reset", None)
        flash("Reset code expired. Please request a new one.")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        reset_code = request.form.get("reset_code", "").strip()
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not all([reset_code, new_password, confirm_password]):
            flash("All fields are required.")
            return render_template("reset_password.html")

        if str(reset_code) != str(reset_data.get("token")):
            flash("Invalid reset code.")
            return render_template("reset_password.html")

        if new_password != confirm_password:
            flash("Passwords do not match.")
            return render_template("reset_password.html")

        if len(new_password) < 6:
            flash("Password must be at least 6 characters.")
            return render_template("reset_password.html")

        # Update password
        user_id = reset_data["user_id"]
        new_hash = generate_password_hash(new_password)
        
        get_db().execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, user_id))
        get_db().commit()
        
        # Clear reset session
        session.pop("password_reset", None)
        
        user = get_user_by_id(user_id)
        if user:
            record_activity(user["username"], "password_reset", "User reset password")
        
        flash("Password reset successfully. Please log in with your new password.")
        return redirect(url_for("login"))

    return render_template("reset_password.html")





# ── Customer ──



@app.route("/customer")

@login_required("customer")

def customer_dashboard():

    user = get_user_by_id(session["user_id"])

    page = request_page()

    offset = (page - 1) * PAGE_SIZE

    transactions = get_db().execute(

        "SELECT * FROM transactions WHERE sender_account=? OR receiver_account=? ORDER BY id DESC LIMIT ? OFFSET ?",

        (user["account_number"], user["account_number"], PAGE_SIZE, offset),

    ).fetchall()

    alerts = get_db().execute(

        "SELECT * FROM alerts WHERE account_number=? ORDER BY timestamp DESC LIMIT 10",

        (user["account_number"],),

    ).fetchall()

    stats = {

        "total_tx": get_db().execute(

            "SELECT COUNT(*) as c FROM transactions WHERE sender_account=? OR receiver_account=?",

            (user["account_number"], user["account_number"]),

        ).fetchone()["c"],

        "flagged": get_db().execute(

            "SELECT COUNT(*) as c FROM transactions WHERE (sender_account=? OR receiver_account=?) AND risk_level!='normal'",

            (user["account_number"], user["account_number"]),

        ).fetchone()["c"],

        "open_alerts": get_db().execute(

            "SELECT COUNT(*) as c FROM alerts WHERE account_number=? AND status='open'",

            (user["account_number"],),

        ).fetchone()["c"],

    }

    return render_template(

        "customer_dashboard.html",

        dashboard_data={

            "user": serialize_row(user),

            "transactions": serialize_rows(transactions),

            "alerts": serialize_rows(alerts),

            "stats": stats,

            "page": page,

        },

        user=user, transactions=transactions, alerts=alerts, stats=stats, page=page,

    )





@app.route("/customer/transaction", methods=["POST"])

@login_required("customer")

def create_transaction():

    user = get_user_by_id(session["user_id"])

    tx_type = request.form.get("type")

    amount_str = request.form.get("amount", "0")

    recipient_account = normalize_account_number(request.form.get("recipient", ""))

    agent_id_str = request.form.get("agent_id", "")



    if tx_type not in VALID_TRANSACTION_TYPES:

        flash("Invalid transaction type.")

        return redirect(url_for("customer_dashboard"))



    try:

        amount = float(amount_str)

    except ValueError:

        flash("Invalid amount.")

        return redirect(url_for("customer_dashboard"))



    if amount <= 0:

        flash("Amount must be greater than zero.")

        return redirect(url_for("customer_dashboard"))



    if tx_type in ("withdraw", "transfer") and user["balance"] < amount:

        flash("Insufficient funds.")

        return redirect(url_for("customer_dashboard"))



    recipient_user = None

    if tx_type == "transfer":

        recipient_user = get_user_by_account_number(recipient_account)

        if not recipient_user or (recipient_user["id"] is not None and recipient_user["id"] == user["id"]) or (recipient_user["role"] is not None and recipient_user["role"] != "customer"):

            flash("Recipient customer account not found.")

            return redirect(url_for("customer_dashboard"))



    # Validate agent_id if provided
    agent_id = None
    if agent_id_str:
        try:
            agent_id = int(agent_id_str)
            # Verify agent exists
            agent_check = get_db().execute("SELECT id FROM agents WHERE id=?", (agent_id,)).fetchone()
            if not agent_check:
                flash("Invalid agent ID.")
                return redirect(url_for("customer_dashboard"))
        except ValueError:
            flash("Invalid agent ID format.")
            return redirect(url_for("customer_dashboard"))



    timestamp = datetime.now(timezone.utc).isoformat()

    sender_account = user["account_number"]

    receiver_account = recipient_user["account_number"] if recipient_user and recipient_user["account_number"] else user["account_number"]



    get_db().execute(

        """

        INSERT INTO transactions (sender_account, receiver_account, amount, transaction_type,

            currency, channel, timestamp, status, risk_score, risk_level, description, agent_id)

        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)

        """,

        (sender_account, receiver_account, amount, tx_type, 'USD', 'online', timestamp, 'Completed', 0, 'normal', 'Initiated', agent_id),

    )

    transaction_id = get_last_insert_id(get_db())



    risk_score, risk_level, reason, _ = process_transaction_event(

        get_db(), transaction_id, sender_account, receiver_account,

        amount, tx_type, timestamp, account_number=user["account_number"],

    )



    # Update balances

    if tx_type == "deposit":

        get_db().execute("UPDATE users SET balance=balance+? WHERE id=?", (amount, user["id"]))

    elif tx_type == "withdraw":

        get_db().execute("UPDATE users SET balance=balance-? WHERE id=?", (amount, user["id"]))

    elif tx_type == "transfer":

        get_db().execute("UPDATE users SET balance=balance-? WHERE id=?", (amount, user["id"]))

        if recipient_user and recipient_user["id"] is not None:
            get_db().execute("UPDATE users SET balance=balance+? WHERE id=?", (amount, recipient_user["id"]))



    get_db().commit()

    broadcast_user_balance(get_db(), sender_account)

    if tx_type == "transfer":

        broadcast_user_balance(get_db(), receiver_account)

    broadcast_stats(get_db())

    # Train AI model in background thread to avoid blocking
    import threading
    def train_in_background():
        try:
            _train_ai_model_from_db(get_db())
        except Exception as e:
            if app:
                app.logger.error(f"Background AI training failed: {e}")
    threading.Thread(target=train_in_background, daemon=True).start()

    record_activity(user["username"], f"{tx_type}", f"${amount:.2f} — risk: {risk_level}")



    risk_labels = {

        "normal": "Transaction processed successfully.",

        "low": "Transaction processed. Minor risk indicators noted.",

        "suspicious": "⚠ Transaction flagged as suspicious and is under review.",

        "super_suspicious": "🚨 Super suspicious transaction flagged. Immediate compliance review initiated.",

        "high_risk": "🚨 High-risk transaction flagged. Compliance team notified.",

        "critical": "🚨 CRITICAL risk transaction. Immediate review initiated.",

    }

    flash(risk_labels.get(risk_level, f"Transaction recorded. Risk: {risk_level}"))

    return redirect(url_for("customer_dashboard"))





# ── Compliance ──



@app.route("/compliance")

@login_required("compliance", "admin")

def compliance_dashboard():

    filter_value = request.args.get("filter", "all")

    page = request_page()

    alert_page = request_page("alert_page")

    offset = (page - 1) * PAGE_SIZE

    alert_offset = (alert_page - 1) * PAGE_SIZE

    # Whitelist of valid filter values to prevent SQL injection
    VALID_FILTERS = {
        "all": "",
        "flagged": "WHERE risk_level!='normal'",
        "suspicious": "WHERE risk_level IN ('suspicious','super_suspicious','high_risk','critical')",
        "ctr": "WHERE ctr_required=1",
        "sar": "WHERE sar_required=1",
    }
    base = VALID_FILTERS.get(filter_value, "")



    transactions = get_db().execute(

        f"SELECT * FROM transactions {base} ORDER BY id DESC LIMIT ? OFFSET ?",

        (PAGE_SIZE, offset),

    ).fetchall()

    total_count = get_db().execute(

        f"SELECT COUNT(*) as c FROM transactions {base}"

    ).fetchone()["c"]



    open_alerts = get_db().execute(

        "SELECT a.*, u.username FROM alerts a LEFT JOIN users u ON a.account_number=u.account_number WHERE a.status='open' ORDER BY a.timestamp DESC, a.id DESC LIMIT ? OFFSET ?",

        (PAGE_SIZE, alert_offset),

    ).fetchall()

    open_alert_count = get_db().execute(

        "SELECT COUNT(*) as c FROM alerts WHERE status='open'"

    ).fetchone()["c"]

    pending_sars = get_db().execute(

        "SELECT COUNT(*) as c FROM sar_reports WHERE status='draft'"

    ).fetchone()["c"]

    pending_ctrs = get_db().execute(

        "SELECT COUNT(*) as c FROM ctr_reports WHERE status='pending'"

    ).fetchone()["c"]



    stats = {

        "open_alerts": open_alert_count,

        "high_risk_today": get_db().execute(

            "SELECT COUNT(*) as c FROM transactions WHERE risk_level IN ('super_suspicious','high_risk','critical') AND timestamp>=?",

            (datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00"),),

        ).fetchone()["c"],

        "pending_sars": pending_sars,

        "pending_ctrs": pending_ctrs,

    }



    return render_template(

        "compliance_dashboard.html",

        dashboard_data={

            "transactions": serialize_rows(transactions),

            "open_alerts": serialize_rows(open_alerts),

            "filter_value": filter_value,

            "stats": stats,

            "page": page,

            "total_count": total_count,

            "page_size": PAGE_SIZE,

            "alert_page": alert_page,

            "open_alert_count": open_alert_count,

        },

        transactions=transactions,

        open_alerts=open_alerts,

        filter_value=filter_value,

        stats=stats,

        page=page,

        total_count=total_count,

        page_size=PAGE_SIZE,

        alert_page=alert_page,

        open_alert_count=open_alert_count,

    )



def _get_next_open_alert_id(conn, current_alert_id):
    next_alert = conn.execute(
        "SELECT id FROM alerts WHERE status='open' AND id != ? ORDER BY timestamp DESC, id DESC LIMIT 1",
        (current_alert_id,),
    ).fetchone()
    return next_alert["id"] if next_alert else None


@app.route("/compliance/alert/<int:alert_id>", methods=["GET", "POST"])

@login_required("compliance", "admin")

def alert_detail(alert_id):

    alert = get_db().execute("SELECT * FROM alerts WHERE id=?", (alert_id,)).fetchone()

    if not alert:

        flash("Alert not found.")

        return redirect(url_for("compliance_dashboard"))



    transaction = get_db().execute(

        "SELECT * FROM transactions WHERE id=?", (alert["transaction_id"],)

    ).fetchone()

    account_number = alert["account_number"]

    account_user = get_db().execute(

        "SELECT * FROM users WHERE account_number=?", (account_number,)

    ).fetchone()



    if request.method == "POST":

        action = request.form.get("action")

        notes = request.form.get("case_notes", "")

        officer = get_user_by_id(session["user_id"])



        if action == "resolve":

            get_db().execute(

                "UPDATE alerts SET status='resolved', case_notes=?, resolved_by=?, resolved_at=? WHERE id=?",

                (notes, officer["username"], datetime.now(timezone.utc).isoformat(), alert_id),

            )

            # Update customer risk rating
            if account_user:
                old_risk = account_user["risk_rating"] or "standard"
                new_risk = update_customer_risk_rating(get_db(), account_number, "resolve", old_risk)
                record_activity(officer["username"], "resolve_alert", f"Alert #{alert_id} resolved, risk rating: {old_risk} -> {new_risk}")
                flash(f"Alert #{alert_id} marked as resolved. Customer risk rating updated to {new_risk}.")
            else:
                record_activity(officer["username"], "resolve_alert", f"Alert #{alert_id} resolved (account not found)")
                flash(f"Alert #{alert_id} marked as resolved.")



        elif action == "escalate":

            get_db().execute(

                "UPDATE alerts SET status='escalated', case_notes=?, assigned_to=? WHERE id=?",

                (notes, officer["username"], alert_id),

            )

            # Update customer risk rating
            if account_user:
                old_risk = account_user["risk_rating"] or "standard"
                new_risk = update_customer_risk_rating(get_db(), account_number, "escalate", old_risk)
                record_activity(officer["username"], "escalate_alert", f"Alert #{alert_id} escalated, risk rating: {old_risk} -> {new_risk}")
                flash(f"Alert #{alert_id} escalated. Customer risk rating updated to {new_risk}.")
            else:
                record_activity(officer["username"], "escalate_alert", f"Alert #{alert_id} escalated (account not found)")
                flash(f"Alert #{alert_id} escalated.")



        elif action == "file_sar":

            narrative = request.form.get("sar_narrative", notes)

            ref = _generate_sar_ref()

            get_db().execute(

                "INSERT INTO sar_reports (alert_id, account_number, filed_by, narrative, status, reference_number, created_at) VALUES (?,?,?,?,?,?,?)",

                (alert_id, account_number, officer["username"], narrative, 'draft', ref,

                 datetime.now(timezone.utc).isoformat()),

            )

            get_db().execute(

                "UPDATE alerts SET status='sar_filed', case_notes=? WHERE id=?",

                (f"SAR filed: {ref}. {notes}", alert_id),

            )

            # Update customer risk rating
            if account_user:
                old_risk = account_user["risk_rating"] or "standard"
                new_risk = update_customer_risk_rating(get_db(), account_number, "file_sar", old_risk)
                record_activity(officer["username"], "file_sar", f"SAR {ref} filed for alert #{alert_id}, risk rating: {old_risk} -> {new_risk}")
                flash(f"SAR filed successfully. Reference: {ref}. Customer risk rating updated to {new_risk}.")
            else:
                record_activity(officer["username"], "file_sar", f"SAR {ref} filed for alert #{alert_id} (account not found)")
                flash(f"SAR filed successfully. Reference: {ref}.")



        get_db().commit()

        broadcast_alert_update(get_db(), alert_id)

        if action == "file_sar":

            sar = get_db().execute(

                "SELECT * FROM sar_reports WHERE alert_id=? ORDER BY id DESC LIMIT 1",

                (alert_id,),

            ).fetchone()

            if sar:

                broadcast_report_event("sar_report", sar)

        broadcast_stats(get_db())

        next_alert_id = _get_next_open_alert_id(get_db(), alert_id)
        if next_alert_id is not None:
            return redirect(url_for("alert_detail", alert_id=next_alert_id))

        return redirect(url_for("compliance_dashboard"))



    rules = []

    try:

        rules = json.loads(alert["rules_triggered"] or "[]")

    except Exception:

        pass



    sar_reports = get_db().execute(

        "SELECT * FROM sar_reports WHERE alert_id=? ORDER BY created_at DESC", (alert_id,)

    ).fetchall()



    return render_template(

        "alert_detail.html",

        alert=alert,

        transaction=transaction,

        account_user=account_user,

        rules=rules,

        sar_reports=sar_reports,

    )





@app.route("/compliance/sar/<int:sar_id>/submit", methods=["POST"])

@login_required("compliance", "admin")

def submit_sar(sar_id):

    officer = get_user_by_id(session["user_id"])

    filed_at = datetime.now(timezone.utc).isoformat()

    get_db().execute(

        "UPDATE sar_reports SET status='submitted', filed_at=? WHERE id=?",

        (filed_at, sar_id),

    )

    get_db().commit()

    sar = get_db().execute("SELECT * FROM sar_reports WHERE id=?", (sar_id,)).fetchone()

    if sar:

        broadcast_report_event("sar_report", sar)

    broadcast_stats(get_db())

    record_activity(officer["username"], "submit_sar", f"SAR #{sar_id} submitted to FIU")

    flash(f"SAR #{sar_id} submitted to the Financial Intelligence Unit.")

    return redirect(url_for("reports"))





# ── Admin ──



@app.route("/admin", methods=["GET", "POST"])

@login_required("admin")

def admin_dashboard():

    if request.method == "POST":

        action = request.form.get("action", "update_role")

        admin_user = get_user_by_id(session["user_id"])



        if action == "update_role":

            user_id = request.form.get("user_id")

            kyc = request.form.get("kyc_status")

            if user_id:

                if kyc:

                    get_db().execute("UPDATE users SET kyc_status=? WHERE id=?", (kyc, user_id))

                get_db().commit()

                updated = get_db().execute(

                    "SELECT id, username, account_number, balance, kyc_status FROM users WHERE id=?",

                    (user_id,),

                ).fetchone()

                if updated:

                    broadcast_event("user", _user_balance_payload(updated))

                record_activity(admin_user["username"], "update_user", f"Updated user {user_id}: kyc={kyc or 'unchanged'}")

                flash("User updated.")



        elif action == "add_watchlist":

            name = request.form.get("wl_name", "")

            id_num = request.form.get("wl_id_number", "")

            list_type = request.form.get("wl_type", "internal")

            reason = request.form.get("wl_reason", "")

            if name:

                get_db().execute(

                    "INSERT INTO watchlist (name, id_number, list_type, reason, added_by, added_at) VALUES (?,?,?,?,?,?)",

                    (name, id_num, list_type, reason, admin_user["username"],

                     datetime.now(timezone.utc).isoformat()),

                )

                get_db().commit()

                watchlist = get_db().execute(

                    "SELECT * FROM watchlist ORDER BY id DESC LIMIT 1"

                ).fetchone()

                if watchlist:

                    broadcast_report_event("watchlist", watchlist)

                record_activity(admin_user["username"], "add_watchlist", f"Added {name} to watchlist")

                flash(f"{name} added to watchlist.")



    page = request_page()

    offset = (page - 1) * PAGE_SIZE

    users = get_db().execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()

    activity = get_db().execute(

        "SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT ? OFFSET ?",

        (PAGE_SIZE, offset),

    ).fetchall()

    transactions = get_db().execute(

        "SELECT * FROM transactions ORDER BY id DESC LIMIT 20"

    ).fetchall()

    watchlist = get_db().execute(

        "SELECT * FROM watchlist ORDER BY added_at DESC LIMIT 20"

    ).fetchall()

    # Keep the dashboard's supervisory totals in one auditable snapshot. The
    # prior view omitted core KYC, PEP, risk and report-queue information.
    system_stats = dict(get_db().execute(
        """
        SELECT
            (SELECT COUNT(*) FROM users) AS total_users,
            (SELECT COUNT(*) FROM users WHERE role='customer') AS customer_users,
            (SELECT COUNT(*) FROM users WHERE role IN ('admin', 'compliance')) AS staff_users,
            (SELECT COUNT(*) FROM users WHERE kyc_status IS NULL OR kyc_status != 'verified') AS kyc_pending,
            (SELECT COUNT(*) FROM users WHERE pep_flag=1) AS pep_customers,
            (SELECT COUNT(*) FROM transactions) AS total_transactions,
            (SELECT COUNT(*) FROM transactions WHERE risk_level IN ('suspicious','super_suspicious','high_risk','critical')) AS flagged_transactions,
            (SELECT COUNT(*) FROM alerts WHERE status='open') AS open_alerts,
            (SELECT COUNT(*) FROM alerts) AS total_alerts,
            (SELECT COUNT(*) FROM sar_reports WHERE status='draft') AS pending_sars,
            (SELECT COUNT(*) FROM sar_reports WHERE status='filed') AS filed_sars,
            (SELECT COUNT(*) FROM ctr_reports WHERE status='pending') AS pending_ctrs,
            (SELECT COUNT(*) FROM ctr_reports WHERE status='filed') AS filed_ctrs
        """
    ).fetchone())

    return render_template(

        "admin_dashboard.html",

        dashboard_data={

            "users": serialize_rows(users),

            "activity": serialize_rows(activity),

            "transactions": serialize_rows(transactions),

            "watchlist": serialize_rows(watchlist),

            "system_stats": system_stats,

            "page": page,

        },

        users=users, activity=activity, transactions=transactions,

        watchlist=watchlist, system_stats=system_stats, page=page,

    )





@app.route("/admin/generate-transactions", methods=["POST"])

@login_required("admin")

def generate_transactions():
    app.logger.info("Transaction generation route called")
    admin_user = get_user_by_id(session["user_id"])

    try:

        count = int(request.form.get("count", 100))

    except ValueError:

        count = 100

    if count not in (100, 500, 1000, 2000, 5000):

        count = 100

    try:

        users = get_db().execute(

            "SELECT id, username, account_number, balance, wealth_segment FROM users WHERE role='customer' ORDER BY id"

        ).fetchall()

        if not users:

            flash("No customer accounts are available for transaction generation.")

            return redirect(url_for("admin_dashboard"))



        generated = {"normal": 0, "suspicious_pattern": 0, "high_risk": 0}

        # Get agents for simulation
        agents = get_db().execute("SELECT id, agent_code, agent_name, location, region, city FROM agents WHERE status='active'").fetchall()

        # Batch insert transactions first for performance
        transactions_to_process = []
        for label in _simulation_plan(count):
            transactions = _simulation_transaction(label, users, agents)
            for (
                sender, recipient, tx_type, amount, timestamp,
                channel, description, _scenario_reason, dest_country, agent_id,
            ) in transactions:
                sender_account = sender["account_number"]
                receiver_account = recipient["account_number"] if tx_type == "transfer" else sender_account

                # STAGE 17E: Remove label contamination - do not insert generated_label
                # Simulated transactions must go through real Stage 13 + Stage 14 pipeline
                get_db().execute(
                    """
                    INSERT INTO transactions (sender_account, receiver_account, amount, transaction_type,
                        currency, channel, timestamp, risk_score, risk_level, description,
                        destination_country, agent_id)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        sender_account, receiver_account, amount, tx_type, "USD", channel, timestamp, 0, 'normal', description, dest_country, agent_id,
                    ),
                )

                transaction_id = get_last_insert_id(get_db())
                transactions_to_process.append((transaction_id, sender, recipient, tx_type, amount, timestamp, sender_account, receiver_account, dest_country))

                if tx_type == "deposit":
                    get_db().execute("UPDATE users SET balance=balance+? WHERE id=?", (amount, sender["id"]))
                elif tx_type == "withdraw":
                    get_db().execute(
                        "UPDATE users SET balance=CASE WHEN balance > ? THEN balance-? ELSE 0 END WHERE id=?",
                        (amount, amount, sender["id"]),
                    )
                elif tx_type == "transfer":
                    get_db().execute(
                        "UPDATE users SET balance=CASE WHEN balance > ? THEN balance-? ELSE 0 END WHERE id=?",
                        (amount, amount, sender["id"]),
                    )
                    get_db().execute("UPDATE users SET balance=balance+? WHERE id=?", (amount, recipient["id"]))

        get_db().commit()

        # STAGE 17E: Remove legacy AI training - use Stage 13 + Stage 14 pipeline only
        # Process transactions in batch through real application pipeline
        # Evaluate chronologically so every score uses only information that
        # was available at that point in time (Stage 13 temporal safety)
        for transaction_id, sender, recipient, tx_type, amount, timestamp, sender_account, receiver_account, dest_country in sorted(
            transactions_to_process, key=lambda item: item[5]
        ):

            # STAGE 17E: Use real application pipeline with Stage 13 + Stage 14
            # No generated_label or scenario_reason - let Stage 14 make the decision
            risk_score, risk_level, reason, alert_id = process_transaction_event(
                get_db(), transaction_id, sender_account, receiver_account,
                amount, tx_type, timestamp, account_number=sender_account,
                destination_country=dest_country,
                generated_label=None,  # STAGE 17E: No label contamination
                scenario_reason=None,  # STAGE 17E: No scenario contamination
            )

            # STAGE 17E: Use Stage 14 binary classification results
            if risk_level == "normal":
                generated["normal"] += 1
            elif risk_level == "suspicious_pattern":
                generated["suspicious_pattern"] += 1
            elif risk_level in ("critical", "high_risk"):
                generated["high_risk"] += 1
            else:
                generated["normal"] += 1  # Default to normal for unknown levels

        get_db().commit()

        # Only broadcast balances for affected accounts
        affected_accounts = set()
        for transaction_id, sender, recipient, tx_type, amount, timestamp, sender_account, receiver_account, dest_country in transactions_to_process:
            affected_accounts.add(sender_account)
            if tx_type == "transfer":
                affected_accounts.add(receiver_account)
        
        for account in affected_accounts:
            broadcast_user_balance(get_db(), account)

        broadcast_event("transaction_batch", {
            "count": count,
            "normal": generated["normal"],
            "suspicious_pattern": generated["suspicious_pattern"],
            "high_risk": generated["high_risk"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        broadcast_stats(get_db())

        # STAGE 17E: Remove background AI training - Stage 14 model is frozen
        # No retraining should occur during simulation

        record_activity(
            admin_user["username"],
            "generate_transactions",
            (
                f"Generated {count} transactions through Stage 13 + Stage 14 pipeline: "
                f"{generated['normal']} normal, {generated['suspicious_pattern']} suspicious_pattern, "
                f"{generated['high_risk']} high_risk"
            ),
        )

        app.logger.info(f"Transaction generation completed: {count} transactions generated through Stage 13 + Stage 14 pipeline")
        flash(f"Generated {count} transactions: {generated['normal']} normal, {generated['flagged']} flagged, {generated['critical']} critical.")

        return redirect(url_for("admin_dashboard"))

    except Exception as e:

        get_db().rollback()

        app.logger.error(f"Transaction generation failed: {e}")

        flash(f"Transaction generation failed: {str(e)}")

        return redirect(url_for("admin_dashboard"))


@app.route("/admin/generate-structuring-scenario", methods=["POST"])
@login_required("admin")
def generate_structuring_scenario():
    """
    Generate structuring-style transaction sequence for Stage 13 feature testing.
    
    STAGE 17E: This endpoint creates transactions that exercise Stage 13 structuring features
    through the real application pipeline (Stage 13 + Stage 14).
    """
    admin_user = get_user_by_id(session["user_id"])
    
    try:
        count = int(request.form.get("count", 5))
    except ValueError:
        count = 5
    
    try:
        users = get_db().execute(
            "SELECT id, username, account_number, balance, wealth_segment FROM users WHERE role='customer' ORDER BY id"
        ).fetchall()
        
        if not users:
            flash("No customer accounts are available for scenario generation.")
            return redirect(url_for("admin_dashboard"))
        
        # Get agents for simulation
        agents = get_db().execute("SELECT id, agent_code, agent_name, location, region, city FROM agents WHERE status='active'").fetchall()
        
        # Generate structuring scenario transactions
        sender_wallet = random.choice(users)
        transactions_to_process = []
        
        # Use the new structuring scenario generator
        structuring_txs = generate_structuring_scenario(get_db(), sender_wallet, None, count)
        
        for (sender, recipient, tx_type, amount, timestamp, channel, description, scenario_reason, dest_country, agent_id) in structuring_txs:
            sender_account = sender["account_number"]
            receiver_account = recipient["account_number"]
            
            # Insert transaction without label contamination
            get_db().execute(
                """
                INSERT INTO transactions (sender_account, receiver_account, amount, transaction_type,
                    currency, channel, timestamp, risk_score, risk_level, description,
                    destination_country, agent_id)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                (sender_account, receiver_account, amount, tx_type, "USD", channel, timestamp, 0, 'normal', description, dest_country, agent_id),
            )
            
            transaction_id = get_last_insert_id(get_db())
            transactions_to_process.append((transaction_id, sender, recipient, tx_type, amount, timestamp, sender_account, receiver_account, dest_country))
            
            # Update balance for Cash-In
            if "Cash-In" in description:
                get_db().execute("UPDATE users SET balance=balance+? WHERE id=?", (amount, sender["id"]))
            elif "Cash-Out" in description:
                get_db().execute(
                    "UPDATE users SET balance=CASE WHEN balance > ? THEN balance-? ELSE 0 END WHERE id=?",
                    (amount, amount, sender["id"]),
                )
        
        get_db().commit()
        
        # Process through real Stage 13 + Stage 14 pipeline
        generated = {"normal": 0, "suspicious_pattern": 0, "high_risk": 0}
        
        for transaction_id, sender, recipient, tx_type, amount, timestamp, sender_account, receiver_account, dest_country in sorted(
            transactions_to_process, key=lambda item: item[5]
        ):
            risk_score, risk_level, reason, alert_id = process_transaction_event(
                get_db(), transaction_id, sender_account, receiver_account,
                amount, tx_type, timestamp, account_number=sender_account,
                destination_country=dest_country,
                generated_label=None,  # No label contamination
                scenario_reason=None,  # No scenario contamination
            )
            
            if risk_level == "normal":
                generated["normal"] += 1
            elif risk_level == "suspicious_pattern":
                generated["suspicious_pattern"] += 1
            elif risk_level in ("critical", "high_risk"):
                generated["high_risk"] += 1
            else:
                generated["normal"] += 1
        
        get_db().commit()
        
        # Broadcast updates
        for account in set([tx[6] for tx in transactions_to_process]):
            broadcast_user_balance(get_db(), account)
        
        broadcast_event("transaction_batch", {
            "count": count,
            "normal": generated["normal"],
            "suspicious_pattern": generated["suspicious_pattern"],
            "high_risk": generated["high_risk"],
            "scenario_type": "structuring",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        
        broadcast_stats(get_db())
        
        record_activity(
            admin_user["username"],
            "generate_structuring_scenario",
            f"Generated structuring scenario with {count} transactions through Stage 13 + Stage 14 pipeline: "
            f"{generated['normal']} normal, {generated['suspicious_pattern']} suspicious_pattern, "
            f"{generated['high_risk']} high_risk"
        )
        
        flash(f"Generated structuring scenario: {count} transactions ({generated['normal']} normal, {generated['suspicious_pattern']} suspicious, {generated['high_risk']} high_risk)")
        return redirect(url_for("admin_dashboard"))
        
    except Exception as e:
        get_db().rollback()
        app.logger.error(f"Structuring scenario generation failed: {e}")
        flash(f"Structuring scenario generation failed: {str(e)}")
        return redirect(url_for("admin_dashboard"))


@app.route("/admin/generate-network-scenario", methods=["POST"])
@login_required("admin")
def generate_network_scenario():
    """
    Generate network-style transaction sequence for Stage 13 feature testing.
    
    STAGE 17E: This endpoint creates transactions that exercise Stage 13 network features
    through the real application pipeline (Stage 13 + Stage 14).
    """
    admin_user = get_user_by_id(session["user_id"])
    
    try:
        count = int(request.form.get("count", 10))
        scenario_type = request.form.get("scenario_type", "many_to_one")
    except ValueError:
        count = 10
        scenario_type = "many_to_one"
    
    try:
        users = get_db().execute(
            "SELECT id, username, account_number, balance, wealth_segment FROM users WHERE role='customer' ORDER BY id"
        ).fetchall()
        
        if len(users) < 3:
            flash("Need at least 3 customer accounts for network scenario generation.")
            return redirect(url_for("admin_dashboard"))
        
        # Generate network scenario transactions
        transactions_to_process = []
        
        # Use the new network scenario generator
        network_txs = generate_network_scenario(get_db(), users, scenario_type, count)
        
        for (sender, recipient, tx_type, amount, timestamp, channel, description, scenario_reason, dest_country, agent_id) in network_txs:
            sender_account = sender["account_number"]
            receiver_account = recipient["account_number"]
            
            # Insert transaction without label contamination
            get_db().execute(
                """
                INSERT INTO transactions (sender_account, receiver_account, amount, transaction_type,
                    currency, channel, timestamp, risk_score, risk_level, description,
                    destination_country, agent_id)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                (sender_account, receiver_account, amount, tx_type, "USD", channel, timestamp, 0, 'normal', description, dest_country, agent_id),
            )
            
            transaction_id = get_last_insert_id(get_db())
            transactions_to_process.append((transaction_id, sender, recipient, tx_type, amount, timestamp, sender_account, receiver_account, dest_country))
            
            # Update balances for wallet-to-wallet transfers
            get_db().execute(
                "UPDATE users SET balance=CASE WHEN balance > ? THEN balance-? ELSE 0 END WHERE id=?",
                (amount, amount, sender["id"]),
            )
            get_db().execute("UPDATE users SET balance=balance+? WHERE id=?", (amount, recipient["id"]))
        
        get_db().commit()
        
        # Process through real Stage 13 + Stage 14 pipeline
        generated = {"normal": 0, "suspicious_pattern": 0, "high_risk": 0}
        
        for transaction_id, sender, recipient, tx_type, amount, timestamp, sender_account, receiver_account, dest_country in sorted(
            transactions_to_process, key=lambda item: item[5]
        ):
            risk_score, risk_level, reason, alert_id = process_transaction_event(
                get_db(), transaction_id, sender_account, receiver_account,
                amount, tx_type, timestamp, account_number=sender_account,
                destination_country=dest_country,
                generated_label=None,  # No label contamination
                scenario_reason=None,  # No scenario contamination
            )
            
            if risk_level == "normal":
                generated["normal"] += 1
            elif risk_level == "suspicious_pattern":
                generated["suspicious_pattern"] += 1
            elif risk_level in ("critical", "high_risk"):
                generated["high_risk"] += 1
            else:
                generated["normal"] += 1
        
        get_db().commit()
        
        # Broadcast updates
        affected_accounts = set()
        for transaction_id, sender, recipient, tx_type, amount, timestamp, sender_account, receiver_account, dest_country in transactions_to_process:
            affected_accounts.add(sender_account)
            affected_accounts.add(receiver_account)
        
        for account in affected_accounts:
            broadcast_user_balance(get_db(), account)
        
        broadcast_event("transaction_batch", {
            "count": count,
            "normal": generated["normal"],
            "suspicious_pattern": generated["suspicious_pattern"],
            "high_risk": generated["high_risk"],
            "scenario_type": f"network_{scenario_type}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        
        broadcast_stats(get_db())
        
        record_activity(
            admin_user["username"],
            "generate_network_scenario",
            f"Generated network scenario ({scenario_type}) with {count} transactions through Stage 13 + Stage 14 pipeline: "
            f"{generated['normal']} normal, {generated['suspicious_pattern']} suspicious_pattern, "
            f"{generated['high_risk']} high_risk"
        )
        
        flash(f"Generated network scenario ({scenario_type}): {count} transactions ({generated['normal']} normal, {generated['suspicious_pattern']} suspicious, {generated['high_risk']} high_risk)")
        return redirect(url_for("admin_dashboard"))
        
    except Exception as e:
        get_db().rollback()
        app.logger.error(f"Network scenario generation failed: {e}")
        flash(f"Network scenario generation failed: {str(e)}")
        return redirect(url_for("admin_dashboard"))


@app.route("/admin/generate-agent-scenario", methods=["POST"])
@login_required("admin")
def generate_agent_scenario():
    """
    Generate agent-mediated transaction sequence for Stage 13 feature testing.
    
    STAGE 17E: This endpoint creates transactions that exercise Stage 13 agent features
    through the real application pipeline (Stage 13 + Stage 14).
    """
    admin_user = get_user_by_id(session["user_id"])
    
    try:
        count = int(request.form.get("count", 15))
        scenario_type = request.form.get("scenario_type", "concentration")
    except ValueError:
        count = 15
        scenario_type = "concentration"
    
    try:
        users = get_db().execute(
            "SELECT id, username, account_number, balance, wealth_segment FROM users WHERE role='customer' ORDER BY id"
        ).fetchall()
        
        if not users:
            flash("No customer accounts are available for agent scenario generation.")
            return redirect(url_for("admin_dashboard"))
        
        # Get agents for simulation
        agents = get_db().execute("SELECT id, agent_code, agent_name, location, region, city FROM agents WHERE status='active'").fetchall()
        
        if not agents:
            flash("No active agents available for agent scenario generation.")
            return redirect(url_for("admin_dashboard"))
        
        # Generate agent scenario transactions
        transactions_to_process = []
        
        # Use the new agent scenario generator
        agent_txs = generate_agent_scenario(get_db(), users, agents, scenario_type, count)
        
        for (sender, recipient, tx_type, amount, timestamp, channel, description, scenario_reason, dest_country, agent_id) in agent_txs:
            sender_account = sender["account_number"]
            receiver_account = recipient["account_number"]
            
            # Insert transaction without label contamination
            get_db().execute(
                """
                INSERT INTO transactions (sender_account, receiver_account, amount, transaction_type,
                    currency, channel, timestamp, risk_score, risk_level, description,
                    destination_country, agent_id)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                (sender_account, receiver_account, amount, tx_type, "USD", channel, timestamp, 0, 'normal', description, dest_country, agent_id),
            )
            
            transaction_id = get_last_insert_id(get_db())
            transactions_to_process.append((transaction_id, sender, recipient, tx_type, amount, timestamp, sender_account, receiver_account, dest_country))
            
            # Update balance for Cash-In
            if "Cash-In" in description:
                get_db().execute("UPDATE users SET balance=balance+? WHERE id=?", (amount, sender["id"]))
            elif "Cash-Out" in description:
                get_db().execute(
                    "UPDATE users SET balance=CASE WHEN balance > ? THEN balance-? ELSE 0 END WHERE id=?",
                    (amount, amount, sender["id"]),
                )
        
        get_db().commit()
        
        # Process through real Stage 13 + Stage 14 pipeline
        generated = {"normal": 0, "suspicious_pattern": 0, "high_risk": 0}
        
        for transaction_id, sender, recipient, tx_type, amount, timestamp, sender_account, receiver_account, dest_country in sorted(
            transactions_to_process, key=lambda item: item[5]
        ):
            risk_score, risk_level, reason, alert_id = process_transaction_event(
                get_db(), transaction_id, sender_account, receiver_account,
                amount, tx_type, timestamp, account_number=sender_account,
                destination_country=dest_country,
                generated_label=None,  # No label contamination
                scenario_reason=None,  # No scenario contamination
            )
            
            if risk_level == "normal":
                generated["normal"] += 1
            elif risk_level == "suspicious_pattern":
                generated["suspicious_pattern"] += 1
            elif risk_level in ("critical", "high_risk"):
                generated["high_risk"] += 1
            else:
                generated["normal"] += 1
        
        get_db().commit()
        
        # Broadcast updates
        for account in set([tx[6] for tx in transactions_to_process]):
            broadcast_user_balance(get_db(), account)
        
        broadcast_event("transaction_batch", {
            "count": count,
            "normal": generated["normal"],
            "suspicious_pattern": generated["suspicious_pattern"],
            "high_risk": generated["high_risk"],
            "scenario_type": f"agent_{scenario_type}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        
        broadcast_stats(get_db())
        
        record_activity(
            admin_user["username"],
            "generate_agent_scenario",
            f"Generated agent scenario ({scenario_type}) with {count} transactions through Stage 13 + Stage 14 pipeline: "
            f"{generated['normal']} normal, {generated['suspicious_pattern']} suspicious_pattern, "
            f"{generated['high_risk']} high_risk"
        )
        
        flash(f"Generated agent scenario ({scenario_type}): {count} transactions ({generated['normal']} normal, {generated['suspicious_pattern']} suspicious, {generated['high_risk']} high_risk)")
        return redirect(url_for("admin_dashboard"))
        
    except Exception as e:
        get_db().rollback()
        app.logger.error(f"Agent scenario generation failed: {e}")
        flash(f"Agent scenario generation failed: {str(e)}")
        return redirect(url_for("admin_dashboard"))





@app.route("/admin/clear-transactions", methods=["POST"])

@login_required("admin")

def clear_transactions():

    admin_user = get_user_by_id(session["user_id"])

    conn = get_db()

    for table in ("sar_reports", "ctr_reports", "alerts", "transactions", "activity_log"):

        conn.execute(f"DELETE FROM {table}")

    conn.commit()

    delete_ai_model()

    app.config["LAST_MONITORED_TRANSACTION_ID"] = 0

    broadcast_event("reset", {

        "scope": "transactions",

        "timestamp": datetime.now(timezone.utc).isoformat(),

    })

    broadcast_stats(conn)

    record_activity(admin_user["username"], "clear_transactions", "Cleared all transactions, alerts, reports, recent activity, and AI model")

    flash("All transactions, alerts, reports, recent activity, and the trained AI model have been cleared.")

    return redirect(url_for("admin_dashboard"))



@app.route("/admin/clear-watchlist", methods=["POST"])

@login_required("admin")

def clear_watchlist():

    admin_user = get_user_by_id(session["user_id"])

    conn = get_db()

    conn.execute("DELETE FROM watchlist")

    conn.commit()

    record_activity(admin_user["username"], "clear_watchlist", "Cleared all watchlist entries")

    flash("All watchlist entries have been cleared.")

    return redirect(url_for("admin_dashboard"))



@app.route("/admin/migrate-database", methods=["POST"])

@login_required("admin")

def migrate_database():

    admin_user = get_user_by_id(session["user_id"])

    conn = get_db()

    try:
        # Keep deployed databases in sync with the current application schema.
        # CREATE ... IF NOT EXISTS makes table/index creation safe to re-run.
        conn.executescript(get_schema_sql(app.config["DATABASE"]))
        conn.executescript(create_messaging_tables_sql(app.config["DATABASE"]))

        if is_postgres_database_url(app.config["DATABASE"]):
            _migrate_postgres(conn)
        elif is_mysql_database_url(app.config["DATABASE"]):
            _migrate_mysql(conn)
        else:
            _migrate_sqlite(conn)

        conn.commit()

        record_activity(admin_user["username"], "migrate_database", "Ran database migration")

        flash("Database migration completed successfully. Missing tables and columns are now up to date.")

    except Exception as e:

        conn.rollback()

        app.logger.error(f"Database migration failed: {e}")

        flash(f"Database migration failed: {str(e)}")

    return redirect(url_for("admin_dashboard"))





@app.route("/reports")

@login_required("compliance", "admin")

def reports():

    total_tx = get_db().execute("SELECT COUNT(*) as c FROM transactions").fetchone()["c"]

    suspicious_tx = get_db().execute("SELECT COUNT(*) as c FROM transactions WHERE risk_level!='normal'").fetchone()["c"]

    high_risk_accounts = get_db().execute(

        "SELECT account_number, COUNT(*) as count FROM alerts GROUP BY account_number ORDER BY count DESC LIMIT 10"

    ).fetchall()

    risk_summary = get_db().execute(

        "SELECT risk_level, COUNT(*) as count FROM transactions GROUP BY risk_level ORDER BY count DESC"

    ).fetchall()

    alerts = get_db().execute(

        "SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 20"

    ).fetchall()

    sar_reports = get_db().execute(

        "SELECT * FROM sar_reports ORDER BY created_at DESC LIMIT 20"

    ).fetchall()

    ctr_reports = get_db().execute(

        "SELECT * FROM ctr_reports ORDER BY created_at DESC LIMIT 20"

    ).fetchall()

    monthly_volume = get_db().execute(

        """

        SELECT SUBSTRING(timestamp,1,7) as month, COUNT(*) as count, SUM(amount) as volume

        FROM transactions

        GROUP BY month

        ORDER BY month DESC

        LIMIT 12

        """

    ).fetchall()

    return render_template(

        "reports.html",

        total_transactions=total_tx,

        suspicious_transactions=suspicious_tx,

        high_risk_accounts=high_risk_accounts,

        risk_summary=risk_summary,

        alerts=alerts,

        sar_reports=sar_reports,

        ctr_reports=ctr_reports,

        monthly_volume=monthly_volume,

    )





# ── API (JSON) ──



@app.route("/api/v1/ai-model")

@login_required("compliance", "admin")

def api_ai_model():

    return jsonify(get_model_metadata())





@app.route("/api/v1/stats")

@login_required("compliance", "admin")

def api_stats():

    return jsonify(_stats_payload(get_db()))





@app.route("/api/v1/transactions")

@login_required("compliance", "admin")

def api_transactions():

    page = request_page()

    offset = (page - 1) * PAGE_SIZE

    rows = get_db().execute(

        """
        SELECT t.*, 
               a.id as agent_id,
               a.agent_code as agent_code,
               a.agent_name as agent_name,
               a.location as agent_location,
               a.region as agent_region,
               a.city as agent_city
        FROM transactions t
        LEFT JOIN agents a ON t.agent_id = a.id
        ORDER BY t.id DESC LIMIT ? OFFSET ?
        """,

        (PAGE_SIZE, offset),

    ).fetchall()

    return jsonify(serialize_rows(rows))



@app.route("/api/v1/agents")

@login_required("compliance", "admin")

def api_agents():

    """API endpoint to retrieve all agents."""
    from agents import get_all_agents
    
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    agents = get_all_agents(get_db(), limit=limit, offset=offset)
    
    return jsonify(serialize_rows(agents))



@app.route("/api/v1/agents/<int:agent_id>")

@login_required("compliance", "admin")

def api_agent_detail(agent_id):

    """API endpoint to retrieve a specific agent."""
    from agents import get_agent_by_id
    
    agent = get_agent_by_id(get_db(), agent_id)
    
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    
    return jsonify(dict(agent))





@app.route("/stream")

@login_required("customer", "compliance", "admin")

def stream():

    # Rate limiting: check if user has too many active streams

    user_streams_key = f"stream_user_{session.get('user_id')}"

    active_streams = app.config.get("ACTIVE_STREAMS", {})

    

    if user_streams_key in active_streams:

        active_streams[user_streams_key] += 1

        if active_streams[user_streams_key] > 3:  # Max 3 concurrent streams per user

            app.logger.warning(f"User {session.get('user_id')} exceeded stream limit")

            return Response("Too many active connections", status=429)

    else:

        active_streams[user_streams_key] = 1

    

    response = app.extensions["realtime_broker"].stream_response()

    

    # Cleanup on response close

    @response.call_on_close

    def cleanup():

        if user_streams_key in active_streams:

            active_streams[user_streams_key] -= 1

            if active_streams[user_streams_key] <= 0:

                del active_streams[user_streams_key]

    

    return response





# ── Error handlers ──



@app.errorhandler(404)

def page_not_found(_):

    return render_template("error.html", message="Page not found."), 404





@app.errorhandler(500)

def server_error(_):

    app.logger.exception("Unhandled server error")

    return render_template("error.html", message="A server error occurred. Our team has been notified."), 500





def ensure_ai_model_ready():

    """Bootstrap AI model on cold start using synthetic typology data."""

    if app.config.get("TESTING"):

        return

    if os.path.exists(MODEL_PATH):

        return

    with app.app_context():

        conn = connect_db()

        try:

            train_ai_model([])

        finally:

            conn.close()





def initialize_startup():
    init_db()
    seed_demo_data()
    ensure_ai_model_ready()
    ensure_background_monitor()


# Initialize database on startup when imported by a WSGI server.
if __name__ != "__main__":
    try:
        initialize_startup()
    except Exception as e:
        logging.error(f"Error during startup initialization: {e}")


if __name__ == "__main__":

    initialize_startup()

    socketio.run(

        app,

        debug=app.config.get("DEBUG", False),

        host="0.0.0.0",

        port=5000,

        allow_unsafe_werkzeug=True,

        use_reloader=False,

    )

