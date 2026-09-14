"""
Database Reset Script

WARNING: This script will DELETE ALL EXISTING DATA in the MySQL database.
Use with caution. This is intended for development/testing purposes only.

This script:
1. Drops the existing 'aml' database
2. Creates a new 'aml' database
3. Creates all required tables with the correct schema
4. Creates all required indexes

MySQL Configuration:
- Host: 127.0.0.1
- Port: 3306
- User: aml
- Password: aml123
- Database: aml
"""

import mysql.connector
from urllib.parse import urlparse, unquote

# MySQL configuration
MYSQL_HOST = '127.0.0.1'
MYSQL_PORT = 3306
MYSQL_USER = 'aml'
MYSQL_PASSWORD = 'aml123'
MYSQL_DATABASE = 'aml'

def reset_database():
    """Drop and recreate the MySQL database with all tables."""
    
    print("=" * 80)
    print("DATABASE RESET SCRIPT")
    print("=" * 80)
    print()
    print("WARNING: This will DELETE ALL EXISTING DATA in the database!")
    print()
    
    # Confirm before proceeding
    response = input("Type 'YES' to confirm database reset: ")
    if response != 'YES':
        print("Database reset cancelled.")
        return
    
    print()
    print("Starting database reset...")
    print()
    
    # Connect to MySQL server (without specifying database)
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        print("✓ Connected to MySQL server")
    except Exception as e:
        print(f"✗ Failed to connect to MySQL server: {e}")
        return
    
    # Drop existing database
    try:
        cursor.execute(f"DROP DATABASE IF EXISTS {MYSQL_DATABASE}")
        conn.commit()
        print(f"✓ Dropped existing database '{MYSQL_DATABASE}'")
    except Exception as e:
        print(f"✗ Failed to drop database: {e}")
        conn.close()
        return
    
    # Create new database
    try:
        cursor.execute(f"CREATE DATABASE {MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
        print(f"✓ Created new database '{MYSQL_DATABASE}'")
    except Exception as e:
        print(f"✗ Failed to create database: {e}")
        conn.close()
        return
    
    # Close connection and reconnect to the new database
    conn.close()
    
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        print(f"✓ Connected to database '{MYSQL_DATABASE}'")
    except Exception as e:
        print(f"✗ Failed to connect to database: {e}")
        return
    
    # Create tables
    schema_sql = """
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
        currency VARCHAR(255) DEFAULT 'USD',
        channel VARCHAR(255) DEFAULT 'online',
        description LONGTEXT,
        timestamp VARCHAR(255) NOT NULL,
        status VARCHAR(255) NOT NULL,
        risk_level VARCHAR(255) DEFAULT 'normal',
        risk_score DOUBLE DEFAULT 0.0,
        rule_level VARCHAR(255) DEFAULT 'normal',
        rule_score DOUBLE DEFAULT 0.0,
        rule_reason LONGTEXT,
        ai_risk_level VARCHAR(255),
        ai_confidence DOUBLE,
        ai_reason LONGTEXT,
        destination_country VARCHAR(100),
        screening_hits VARCHAR(1000),
        generated_label VARCHAR(50),
        ctr_required INTEGER DEFAULT 0,
        sar_required INTEGER DEFAULT 0,
        reviewed_by VARCHAR(255),
        reviewed_at VARCHAR(255),
        agent_id BIGINT,
        FOREIGN KEY (sender_account) REFERENCES users(account_number),
        FOREIGN KEY (receiver_account) REFERENCES users(account_number),
        FOREIGN KEY (agent_id) REFERENCES agents(id)
    );

    CREATE TABLE alerts (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        transaction_id BIGINT,
        account_number VARCHAR(255) NOT NULL,
        risk_score DOUBLE NOT NULL,
        risk_level VARCHAR(255) NOT NULL,
        reason LONGTEXT,
        rules_triggered LONGTEXT,
        status VARCHAR(255) DEFAULT 'open',
        assigned_to VARCHAR(255),
        resolved_by VARCHAR(255),
        resolved_at VARCHAR(255),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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

    CREATE TABLE customer_baselines (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        account_number VARCHAR(255) UNIQUE NOT NULL,
        baseline_data LONGTEXT,
        last_updated TIMESTAMP,
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
        filed_at VARCHAR(255),
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

    CREATE TABLE conversations (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        participants LONGTEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE messages (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        conversation_id BIGINT,
        sender VARCHAR(255),
        content LONGTEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
    );

    CREATE TABLE unread_messages (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        user_id VARCHAR(255),
        message_id BIGINT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (message_id) REFERENCES messages(id)
    );

    CREATE TABLE user_presence (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        user_id VARCHAR(255),
        status VARCHAR(255),
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    try:
        cursor.executescript(schema_sql)
        conn.commit()
        print("✓ Created all tables")
    except Exception as e:
        print(f"✗ Failed to create tables: {e}")
        conn.close()
        return
    
    # Create indexes
    indexes_sql = """
    CREATE INDEX idx_transactions_sender ON transactions(sender_account);
    CREATE INDEX idx_transactions_receiver ON transactions(receiver_account);
    CREATE INDEX idx_transactions_timestamp ON transactions(timestamp);
    CREATE INDEX idx_transactions_agent ON transactions(agent_id);
    CREATE INDEX idx_transactions_risk_level ON transactions(risk_level);
    CREATE INDEX idx_agents_region ON agents(region);
    CREATE INDEX idx_agents_city ON agents(city);
    CREATE INDEX idx_alerts_account ON alerts(account_number);
    CREATE INDEX idx_alerts_status ON alerts(status);
    CREATE INDEX idx_alerts_risk_level ON alerts(risk_level);
    """
    
    try:
        cursor.executescript(indexes_sql)
        conn.commit()
        print("✓ Created all indexes")
    except Exception as e:
        print(f"✗ Failed to create indexes: {e}")
        conn.close()
        return
    
    # Verify tables were created
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print()
    print(f"✓ Database reset complete. {len(tables)} tables created:")
    for table in tables:
        print(f"  - {table[0]}")
    
    conn.close()
    print()
    print("=" * 80)
    print("DATABASE RESET SUCCESSFUL")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Run the Flask application: python app.py")
    print("2. The application will seed admin and compliance accounts:")
    print("   - Admin / Admin123")
    print("   - Compliance / Compliance123")
    print()

if __name__ == "__main__":
    reset_database()
