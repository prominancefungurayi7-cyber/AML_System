-- Stage4U disposable MySQL application schema. No data or credentials.
-- Generated from database.py and server.py static migration literals.
-- Apply only after verifying DATABASE() = v4_stage4s_disposable and restricted grants.

CREATE TABLE users (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        username VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        account_number VARCHAR(255) UNIQUE NOT NULL,
        id_number VARCHAR(255),
        email VARCHAR(255),
        role VARCHAR(255) DEFAULT 'customer',
        balance REAL DEFAULT 0.0,
        kyc_status VARCHAR(255) DEFAULT 'pending',
        risk_rating VARCHAR(255) DEFAULT 'standard',
        wealth_segment VARCHAR(255) DEFAULT 'average',
        pep_flag INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    );

CREATE TABLE agents (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        agent_code VARCHAR(255) UNIQUE NOT NULL,
        agent_name VARCHAR(255) NOT NULL,
        location VARCHAR(255),
        region VARCHAR(255),
        city VARCHAR(255),
        status VARCHAR(255) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

CREATE TABLE transactions (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        sender_account VARCHAR(255) NOT NULL,
        receiver_account VARCHAR(255) NOT NULL,
        amount DOUBLE NOT NULL,
        transaction_type VARCHAR(255) NOT NULL,
        channel VARCHAR(255) DEFAULT 'online',
        description VARCHAR(255),
        timestamp VARCHAR(40) NOT NULL,
        risk_level VARCHAR(255) DEFAULT 'normal',
        risk_score REAL DEFAULT 0.0,
        rule_level VARCHAR(255) DEFAULT 'normal',
        rule_score REAL DEFAULT 0.0,
        ai_risk_level VARCHAR(255),
        ai_confidence REAL,
        generated_label VARCHAR(255),
        scenario_reason VARCHAR(255),
        destination_country VARCHAR(255) DEFAULT 'ZW',
        ctr_required INTEGER DEFAULT 0,
        sar_required INTEGER DEFAULT 0,
        agent_id BIGINT,
        FOREIGN KEY (sender_account) REFERENCES users(account_number),
        FOREIGN KEY (receiver_account) REFERENCES users(account_number),
        FOREIGN KEY (agent_id) REFERENCES agents(id)
    );

CREATE TABLE alerts (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        transaction_id BIGINT,
        account_number VARCHAR(255) NOT NULL,
        risk_score REAL NOT NULL,
        risk_level VARCHAR(255) NOT NULL,
        reason LONGTEXT,
        rules_triggered VARCHAR(255),
        status VARCHAR(255) DEFAULT 'open',
        assigned_to VARCHAR(255),
        resolved_by VARCHAR(255),
        resolved_at TIMESTAMP,
        timestamp VARCHAR(40) NOT NULL,
        FOREIGN KEY (transaction_id) REFERENCES transactions(id)
    );

CREATE TABLE behavioral_profiles (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        account_number VARCHAR(255) UNIQUE NOT NULL,
        profile_data LONGTEXT,
        last_updated TIMESTAMP,
        total_transactions INTEGER DEFAULT 0,
        FOREIGN KEY (account_number) REFERENCES users(account_number)
    );

CREATE TABLE sar_reports (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        reference_number VARCHAR(255) UNIQUE NOT NULL,
        transaction_id BIGINT,
        account_number VARCHAR(255) NOT NULL,
        filing_reason LONGTEXT,
        status VARCHAR(255) DEFAULT 'filed',
        filed_by VARCHAR(255),
        filed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (transaction_id) REFERENCES transactions(id)
    );

CREATE TABLE ctr_reports (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        reference_number VARCHAR(255) UNIQUE NOT NULL,
        account_number VARCHAR(255) NOT NULL,
        total_amount DOUBLE NOT NULL,
        transaction_count INTEGER DEFAULT 1,
        filing_date DATE,
        status VARCHAR(255) DEFAULT 'filed',
        filed_by VARCHAR(255),
        filed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

CREATE TABLE system_activity_log (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        user_id VARCHAR(255),
        action VARCHAR(255) NOT NULL,
        details LONGTEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ip_address VARCHAR(255)
    );

CREATE TABLE activity_log (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        actor VARCHAR(255),
        action VARCHAR(255) NOT NULL,
        detail LONGTEXT,
        ip_address VARCHAR(255),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

CREATE TABLE watchlist (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(255) NOT NULL,
        id_number VARCHAR(255),
        account_number VARCHAR(255),
        list_type VARCHAR(255) NOT NULL,
        reason LONGTEXT,
        added_by VARCHAR(255),
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

ALTER TABLE transactions ADD COLUMN currency VARCHAR(255) DEFAULT 'USD';
ALTER TABLE transactions ADD COLUMN rule_reason LONGTEXT;
ALTER TABLE transactions ADD COLUMN ai_reason LONGTEXT;
ALTER TABLE transactions ADD COLUMN rules_triggered LONGTEXT;
ALTER TABLE transactions ADD COLUMN screening_hits LONGTEXT;
ALTER TABLE transactions ADD COLUMN reviewed_by VARCHAR(255);
ALTER TABLE transactions ADD COLUMN reviewed_at VARCHAR(255);
ALTER TABLE transactions ADD COLUMN status VARCHAR(50) DEFAULT 'Completed';
ALTER TABLE alerts ADD COLUMN case_notes LONGTEXT;

CREATE INDEX idx_stage4u_tx_sender_time ON transactions (sender_account,timestamp,id);
CREATE INDEX idx_stage4u_tx_receiver_time ON transactions (receiver_account,timestamp,id);
CREATE INDEX idx_stage4u_tx_agent_time ON transactions (agent_id,timestamp,id);
CREATE INDEX idx_stage4u_alert_account ON alerts (account_number,status,id);
CREATE INDEX idx_stage4u_activity_actor ON activity_log (actor,timestamp,id);
CREATE INDEX idx_stage4u_watchlist_account ON watchlist (account_number);
