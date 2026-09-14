-- ============================================================================
-- AML System - Clean MySQL Database Schema
-- ============================================================================
-- Purpose: Complete database rebuild script for the Zimbabwe mobile-money AML system
-- Database: aml
-- Engine: MySQL
-- Character Set: utf8mb4
-- Collation: utf8mb4_unicode_ci
-- ============================================================================
-- WARNING: This script will DROP and RECREATE the 'aml' database.
-- ALL EXISTING DATA WILL BE LOST.
-- Use with caution in production environments.
-- ============================================================================

-- Drop existing database if it exists
DROP DATABASE IF EXISTS aml;

-- Create new database
CREATE DATABASE aml CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Select the database
USE aml;

-- ============================================================================
-- TABLE CREATION ORDER (Dependency Graph)
-- ============================================================================
-- 1. users (no dependencies)
-- 2. agents (no dependencies)
-- 3. customer_baselines (depends on users.account_number)
-- 4. behavioral_profiles (depends on users.account_number)
-- 5. transactions (depends on users.account_number, agents.id)
-- 6. alerts (depends on transactions.id)
-- 7. sar_reports (depends on alerts.id)
-- 8. ctr_reports (depends on transactions.id)
-- 9. conversations (depends on users.username)
-- 10. messages (depends on conversations.id, users.username)
-- 11. unread_messages (depends on users.username, conversations.id)
-- 12. user_presence (depends on users.username, conversations.id)
-- 13. system_activity_log (no dependencies)
-- 14. activity_log (no dependencies)
-- 15. watchlist (no dependencies)
-- ============================================================================

-- ============================================================================
-- 1. users
-- ============================================================================
CREATE TABLE users (
    id BIGINT NOT NULL AUTO_INCREMENT,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    id_number VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    account_number VARCHAR(255) NOT NULL,
    balance DOUBLE DEFAULT 0,
    kyc_status VARCHAR(255) DEFAULT 'pending',
    pep_flag INT DEFAULT 0,
    risk_rating VARCHAR(255) DEFAULT 'standard',
    created_at VARCHAR(255) NOT NULL,
    wealth_segment VARCHAR(255) DEFAULT 'average',
    last_login TIMESTAMP NULL,
    PRIMARY KEY (id),
    UNIQUE KEY username (username),
    UNIQUE KEY email (email),
    UNIQUE KEY id_number (id_number),
    UNIQUE KEY account_number (account_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 2. agents
-- ============================================================================
CREATE TABLE agents (
    id BIGINT NOT NULL AUTO_INCREMENT,
    agent_code VARCHAR(255) NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    location VARCHAR(255) DEFAULT NULL,
    region VARCHAR(255) DEFAULT NULL,
    city VARCHAR(255) DEFAULT NULL,
    status VARCHAR(255) DEFAULT 'active',
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY agent_code (agent_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 3. customer_baselines
-- ============================================================================
CREATE TABLE customer_baselines (
    account_number VARCHAR(255) NOT NULL,
    tx_count INT DEFAULT 0,
    avg_amount DOUBLE DEFAULT 0,
    std_amount DOUBLE DEFAULT 0,
    max_amount DOUBLE DEFAULT 0,
    p95_amount DOUBLE DEFAULT 0,
    avg_daily_tx DOUBLE DEFAULT 0,
    avg_daily_volume DOUBLE DEFAULT 0,
    typical_hour INT DEFAULT 12,
    typical_channel VARCHAR(255) DEFAULT 'online',
    known_recipients LONGTEXT,
    last_updated VARCHAR(255) DEFAULT NULL,
    PRIMARY KEY (account_number),
    CONSTRAINT fk_customer_baselines_account FOREIGN KEY (account_number) REFERENCES users(account_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 4. behavioral_profiles
-- ============================================================================
CREATE TABLE behavioral_profiles (
    account_number VARCHAR(255) NOT NULL,
    profile_data LONGTEXT,
    last_updated VARCHAR(255) DEFAULT NULL,
    total_transactions INT DEFAULT 0,
    PRIMARY KEY (account_number),
    CONSTRAINT fk_behavioral_profiles_account FOREIGN KEY (account_number) REFERENCES users(account_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 5. transactions
-- ============================================================================
CREATE TABLE transactions (
    id BIGINT NOT NULL AUTO_INCREMENT,
    sender_account VARCHAR(255) NOT NULL,
    receiver_account VARCHAR(255) NOT NULL,
    amount DOUBLE NOT NULL,
    transaction_type VARCHAR(255) NOT NULL,
    currency VARCHAR(255) DEFAULT 'USD',
    channel VARCHAR(255) DEFAULT 'online',
    timestamp VARCHAR(255) NOT NULL,
    status VARCHAR(255) NOT NULL,
    risk_score DOUBLE DEFAULT 0,
    risk_level VARCHAR(255) DEFAULT 'normal',
    description LONGTEXT,
    rules_triggered LONGTEXT,
    ctr_required INT DEFAULT 0,
    sar_required INT DEFAULT 0,
    reviewed_by VARCHAR(255) DEFAULT NULL,
    reviewed_at VARCHAR(255) DEFAULT NULL,
    rule_score DOUBLE DEFAULT 0,
    rule_level VARCHAR(255) DEFAULT 'normal',
    rule_reason LONGTEXT,
    ai_risk_level VARCHAR(255) DEFAULT NULL,
    ai_confidence DOUBLE DEFAULT 0,
    ai_reason LONGTEXT,
    destination_country VARCHAR(100) DEFAULT NULL,
    screening_hits VARCHAR(1000) DEFAULT NULL,
    generated_label VARCHAR(50) DEFAULT NULL,
    agent_id BIGINT DEFAULT NULL,
    PRIMARY KEY (id),
    KEY idx_transactions_sender (sender_account),
    KEY idx_transactions_receiver (receiver_account),
    KEY idx_transactions_timestamp (timestamp),
    KEY idx_transactions_risk_level (risk_level),
    KEY idx_transactions_agent (agent_id),
    CONSTRAINT fk_transactions_sender FOREIGN KEY (sender_account) REFERENCES users(account_number),
    CONSTRAINT fk_transactions_receiver FOREIGN KEY (receiver_account) REFERENCES users(account_number),
    CONSTRAINT fk_transactions_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 6. alerts
-- ============================================================================
CREATE TABLE alerts (
    id BIGINT NOT NULL AUTO_INCREMENT,
    transaction_id INT NOT NULL,
    account_number VARCHAR(255) NOT NULL,
    risk_score DOUBLE NOT NULL,
    risk_level VARCHAR(255) NOT NULL,
    reason LONGTEXT,
    rules_triggered LONGTEXT,
    status VARCHAR(255) DEFAULT 'open',
    assigned_to VARCHAR(255) DEFAULT NULL,
    case_notes LONGTEXT,
    resolved_at VARCHAR(255) DEFAULT NULL,
    resolved_by VARCHAR(255) DEFAULT NULL,
    timestamp VARCHAR(255) NOT NULL,
    PRIMARY KEY (id),
    KEY idx_alerts_transaction_id (transaction_id),
    KEY idx_alerts_account_number (account_number),
    KEY idx_alerts_status (status),
    KEY idx_alerts_timestamp (timestamp),
    CONSTRAINT fk_alerts_transaction FOREIGN KEY (transaction_id) REFERENCES transactions(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 7. sar_reports
-- ============================================================================
CREATE TABLE sar_reports (
    id BIGINT NOT NULL AUTO_INCREMENT,
    alert_id INT NOT NULL,
    account_number VARCHAR(255) NOT NULL,
    filed_by VARCHAR(255) NOT NULL,
    narrative LONGTEXT,
    status VARCHAR(255) DEFAULT 'draft',
    filed_at VARCHAR(255) DEFAULT NULL,
    reference_number VARCHAR(255) DEFAULT NULL,
    created_at VARCHAR(255) NOT NULL,
    PRIMARY KEY (id),
    KEY idx_sar_alert_id (alert_id),
    CONSTRAINT fk_sar_alert FOREIGN KEY (alert_id) REFERENCES alerts(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 8. ctr_reports
-- ============================================================================
CREATE TABLE ctr_reports (
    id BIGINT NOT NULL AUTO_INCREMENT,
    transaction_id INT NOT NULL,
    account_number VARCHAR(255) NOT NULL,
    amount DOUBLE NOT NULL,
    generated_by VARCHAR(255) NOT NULL,
    status VARCHAR(255) DEFAULT 'pending',
    filed_at VARCHAR(255) DEFAULT NULL,
    created_at VARCHAR(255) NOT NULL,
    PRIMARY KEY (id),
    KEY idx_ctr_transaction_id (transaction_id),
    CONSTRAINT fk_ctr_transaction FOREIGN KEY (transaction_id) REFERENCES transactions(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 9. conversations
-- ============================================================================
CREATE TABLE conversations (
    id BIGINT NOT NULL AUTO_INCREMENT,
    participant_1 VARCHAR(255) NOT NULL,
    participant_2 VARCHAR(255) NOT NULL,
    conversation_type VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP NULL DEFAULT NULL,
    last_message_id BIGINT DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY participant_1 (participant_1, participant_2),
    UNIQUE KEY participant_2 (participant_2, participant_1),
    CONSTRAINT fk_conversations_p1 FOREIGN KEY (participant_1) REFERENCES users(username),
    CONSTRAINT fk_conversations_p2 FOREIGN KEY (participant_2) REFERENCES users(username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 10. messages
-- ============================================================================
CREATE TABLE messages (
    id BIGINT NOT NULL AUTO_INCREMENT,
    conversation_id BIGINT NOT NULL,
    sender_username VARCHAR(255) NOT NULL,
    sender_role VARCHAR(255) DEFAULT NULL,
    receiver_username VARCHAR(255) NOT NULL,
    content LONGTEXT NOT NULL,
    status VARCHAR(255) DEFAULT 'sent',
    read_at TIMESTAMP NULL DEFAULT NULL,
    delivered_at TIMESTAMP NULL DEFAULT NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMP NULL DEFAULT NULL,
    deleted_at TIMESTAMP NULL DEFAULT NULL,
    PRIMARY KEY (id),
    KEY conversation_id (conversation_id),
    KEY sender_username (sender_username),
    KEY receiver_username (receiver_username),
    CONSTRAINT fk_messages_conversation FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    CONSTRAINT fk_messages_sender FOREIGN KEY (sender_username) REFERENCES users(username),
    CONSTRAINT fk_messages_receiver FOREIGN KEY (receiver_username) REFERENCES users(username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 11. unread_messages
-- ============================================================================
CREATE TABLE unread_messages (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_username VARCHAR(255) NOT NULL,
    conversation_id BIGINT NOT NULL,
    unread_count INT DEFAULT 0,
    last_unread_at TIMESTAMP NULL DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY user_username (user_username, conversation_id),
    KEY conversation_id (conversation_id),
    CONSTRAINT fk_unread_user FOREIGN KEY (user_username) REFERENCES users(username),
    CONSTRAINT fk_unread_conversation FOREIGN KEY (conversation_id) REFERENCES conversations(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 12. user_presence
-- ============================================================================
CREATE TABLE user_presence (
    id BIGINT NOT NULL AUTO_INCREMENT,
    username VARCHAR(255) NOT NULL,
    is_online INT DEFAULT 0,
    last_seen TIMESTAMP NULL DEFAULT NULL,
    typing_in_conversation BIGINT DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY username (username),
    KEY typing_in_conversation (typing_in_conversation),
    CONSTRAINT fk_presence_user FOREIGN KEY (username) REFERENCES users(username),
    CONSTRAINT fk_presence_conversation FOREIGN KEY (typing_in_conversation) REFERENCES conversations(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 13. system_activity_log
-- ============================================================================
CREATE TABLE system_activity_log (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id VARCHAR(255) DEFAULT NULL,
    action VARCHAR(255) NOT NULL,
    details LONGTEXT,
    timestamp TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(255) DEFAULT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 14. activity_log
-- ============================================================================
CREATE TABLE activity_log (
    id BIGINT NOT NULL AUTO_INCREMENT,
    actor VARCHAR(255) NOT NULL,
    action VARCHAR(255) NOT NULL,
    detail LONGTEXT,
    ip_address VARCHAR(255) DEFAULT NULL,
    timestamp VARCHAR(255) NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 15. watchlist
-- ============================================================================
CREATE TABLE watchlist (
    id BIGINT NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    id_number VARCHAR(255) DEFAULT NULL,
    account_number VARCHAR(255) DEFAULT NULL,
    list_type VARCHAR(255) NOT NULL,
    reason LONGTEXT,
    added_by VARCHAR(255) NOT NULL,
    added_at VARCHAR(255) NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================
-- Additional indexes for agents
CREATE INDEX idx_agents_region ON agents(region);
CREATE INDEX idx_agents_city ON agents(city);

-- Additional indexes for alerts
CREATE INDEX idx_alerts_risk_level ON alerts(risk_level);

-- ============================================================================
-- SCHEMA COMPLETE
-- ============================================================================
-- The database is now ready for use.
-- Run the Flask application to seed initial admin and compliance accounts:
--   python app.py
-- This will automatically create:
--   - Admin / Admin123
--   - Compliance / Compliance123
-- ============================================================================
