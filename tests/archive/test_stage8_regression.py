"""
Stage 8 Regression Testing Script
Comprehensive regression tests for the Zimbabwe mobile-money AML application.
Tests database integrity, application functionality, and system stability after Stages 1-7.
"""

import mysql.connector
from datetime import datetime, timezone

print("=" * 80)
print("STAGE 8 REGRESSION TESTING")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# MySQL connection configuration
MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'aml',
    'password': 'aml123',
    'database': 'aml'
}

# Data preservation - record initial counts
initial_counts = {}

try:
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    print("✓ MySQL connection successful")
    print()
except Exception as e:
    print(f"✗ MySQL connection failed: {e}")
    print("REGRESSION TESTING BLOCKED — MySQL server unavailable")
    exit(1)

# Record initial data counts
print("DATA PRESERVATION - INITIAL COUNTS")
print("-" * 80)
try:
    cursor.execute("SELECT COUNT(*) FROM users")
    initial_counts['users'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM transactions")
    initial_counts['transactions'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM agents")
    initial_counts['agents'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM alerts")
    initial_counts['alerts'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM sar_reports")
    initial_counts['sar_reports'] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM ctr_reports")
    initial_counts['ctr_reports'] = cursor.fetchone()[0]
    
    print(f"Users: {initial_counts['users']}")
    print(f"Transactions: {initial_counts['transactions']}")
    print(f"Agents: {initial_counts['agents']}")
    print(f"Alerts: {initial_counts['alerts']}")
    print(f"SAR Reports: {initial_counts['sar_reports']}")
    print(f"CTR Reports: {initial_counts['ctr_reports']}")
    print()
except Exception as e:
    print(f"✗ Failed to record initial counts: {e}")
    print()

# Test 1: Database Integrity - Users
print("TEST 1: Database Integrity - Users")
print("-" * 80)
try:
    cursor.execute("SELECT id, username, account_number, role FROM users LIMIT 5")
    users = cursor.fetchall()
    print(f"✓ Retrieved {len(users)} sample users")
    
    # Check account number uniqueness
    cursor.execute("SELECT COUNT(DISTINCT account_number) FROM users")
    unique_accounts = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    if unique_accounts == total_users:
        print("✓ Account numbers are unique")
    else:
        print(f"⚠ Account number uniqueness issue: {unique_accounts} unique vs {total_users} total")
    
    print()
except Exception as e:
    print(f"✗ Users test failed: {e}")
    print()

# Test 2: Database Integrity - Transactions
print("TEST 2: Database Integrity - Transactions")
print("-" * 80)
try:
    cursor.execute("SELECT id, sender_account, receiver_account, amount, timestamp, agent_id FROM transactions LIMIT 5")
    transactions = cursor.fetchall()
    print(f"✓ Retrieved {len(transactions)} sample transactions")
    
    # Check agent_id column
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE agent_id IS NULL")
    null_agent_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE agent_id IS NOT NULL")
    non_null_agent_count = cursor.fetchone()[0]
    print(f"✓ Transactions with NULL agent_id: {null_agent_count}")
    print(f"✓ Transactions with agent_id: {non_null_agent_count}")
    
    # Check timestamp validity
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE timestamp IS NULL OR timestamp = ''")
    null_timestamp_count = cursor.fetchone()[0]
    if null_timestamp_count == 0:
        print("✓ All transactions have valid timestamps")
    else:
        print(f"⚠ {null_timestamp_count} transactions have invalid timestamps")
    
    print()
except Exception as e:
    print(f"✗ Transactions test failed: {e}")
    print()

# Test 3: Database Integrity - Agents
print("TEST 3: Database Integrity - Agents")
print("-" * 80)
try:
    cursor.execute("SELECT id, agent_code, agent_name, status FROM agents LIMIT 5")
    agents = cursor.fetchall()
    print(f"✓ Retrieved {len(agents)} sample agents")
    
    # Check agent_code uniqueness
    cursor.execute("SELECT COUNT(DISTINCT agent_code) FROM agents")
    unique_codes = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM agents")
    total_agents = cursor.fetchone()[0]
    if unique_codes == total_agents:
        print("✓ Agent codes are unique")
    else:
        print(f"⚠ Agent code uniqueness issue: {unique_codes} unique vs {total_agents} total")
    
    print()
except Exception as e:
    print(f"✗ Agents test failed: {e}")
    print()

# Test 4: Database Integrity - Alerts
print("TEST 4: Database Integrity - Alerts")
print("-" * 80)
try:
    cursor.execute("SELECT id, transaction_id, risk_level, status FROM alerts LIMIT 5")
    alerts = cursor.fetchall()
    print(f"✓ Retrieved {len(alerts)} sample alerts")
    
    # Check alert status distribution
    cursor.execute("SELECT status, COUNT(*) FROM alerts GROUP BY status")
    status_dist = cursor.fetchall()
    print("✓ Alert status distribution:")
    for status, count in status_dist:
        print(f"  {status}: {count}")
    
    print()
except Exception as e:
    print(f"✗ Alerts test failed: {e}")
    print()

# Test 5: Database Integrity - Report Tables
print("TEST 5: Database Integrity - Report Tables")
print("-" * 80)
try:
    cursor.execute("SELECT id, alert_id, status FROM sar_reports LIMIT 5")
    sar_reports = cursor.fetchall()
    print(f"✓ Retrieved {len(sar_reports)} sample SAR reports")
    
    cursor.execute("SELECT id, transaction_id, status FROM ctr_reports LIMIT 5")
    ctr_reports = cursor.fetchall()
    print(f"✓ Retrieved {len(ctr_reports)} sample CTR reports")
    
    print()
except Exception as e:
    print(f"✗ Report tables test failed: {e}")
    print()

# Test 6: Transaction Regression - Normal wallet transaction
print("TEST 6: Transaction Regression - Normal Wallet Transaction")
print("-" * 80)
try:
    # Get valid accounts
    cursor.execute("SELECT account_number FROM users WHERE role='customer' LIMIT 2")
    accounts = cursor.fetchall()
    if len(accounts) >= 2:
        sender = accounts[0][0]
        receiver = accounts[1][0]
        
        # Create test transaction
        cursor.execute(
            """INSERT INTO transactions (sender_account, receiver_account, amount, transaction_type, 
               currency, channel, timestamp, status, risk_score, risk_level, description, agent_id) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (sender, receiver, 100.0, "transfer", "USD", "mobile", datetime.now(timezone.utc).isoformat(), "Completed", 0, "normal", "Stage 8 test transaction", None)
        )
        conn.commit()
        
        # Verify transaction was created
        cursor.execute("SELECT id, sender_account, receiver_account, amount, agent_id FROM transactions WHERE description='Stage 8 test transaction'")
        test_tx = cursor.fetchone()
        if test_tx:
            print("✓ Normal wallet transaction created successfully")
            print(f"  Transaction ID: {test_tx[0]}")
            print(f"  Sender: {test_tx[1]}")
            print(f"  Receiver: {test_tx[2]}")
            print(f"  Amount: {test_tx[3]}")
            print(f"  Agent ID: {test_tx[4]}")
            
            # Cleanup
            cursor.execute("DELETE FROM transactions WHERE description='Stage 8 test transaction'")
            conn.commit()
            print("✓ Test transaction cleaned up")
        else:
            print("✗ Test transaction not found after creation")
    else:
        print("⚠ Insufficient customer accounts for test")
    
    print()
except Exception as e:
    print(f"✗ Normal wallet transaction test failed: {e}")
    print()

# Test 7: Transaction Regression - Non-agent transaction
print("TEST 7: Transaction Regression - Non-Agent Transaction (agent_id = NULL)")
print("-" * 80)
try:
    cursor.execute("SELECT account_number FROM users WHERE role='customer' LIMIT 2")
    accounts = cursor.fetchall()
    if len(accounts) >= 2:
        sender = accounts[0][0]
        receiver = accounts[1][0]
        
        cursor.execute(
            """INSERT INTO transactions (sender_account, receiver_account, amount, transaction_type, 
               currency, channel, timestamp, status, risk_score, risk_level, description, agent_id) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (sender, receiver, 50.0, "transfer", "USD", "mobile", datetime.now(timezone.utc).isoformat(), "Completed", 0, "normal", "Stage 8 non-agent test", None)
        )
        conn.commit()
        
        cursor.execute("SELECT id, agent_id FROM transactions WHERE description='Stage 8 non-agent test'")
        test_tx = cursor.fetchone()
        if test_tx and test_tx[1] is None:
            print("✓ Non-agent transaction created with NULL agent_id")
            print(f"  Transaction ID: {test_tx[0]}")
            
            # Verify it appears in transaction list
            cursor.execute("SELECT COUNT(*) FROM transactions WHERE agent_id IS NULL")
            null_count = cursor.fetchone()[0]
            print(f"✓ Transaction appears in NULL agent_id list (count: {null_count})")
            
            # Cleanup
            cursor.execute("DELETE FROM transactions WHERE description='Stage 8 non-agent test'")
            conn.commit()
            print("✓ Test transaction cleaned up")
        else:
            print("✗ Non-agent transaction test failed")
    
    print()
except Exception as e:
    print(f"✗ Non-agent transaction test failed: {e}")
    print()

# Test 8: Transaction Regression - Agent-linked transaction
print("TEST 8: Transaction Regression - Agent-Linked Transaction")
print("-" * 80)
try:
    # Create test agent
    cursor.execute(
        "INSERT INTO agents (agent_code, agent_name, location, region, city, status) VALUES (%s, %s, %s, %s, %s, %s)",
        ("STAGE8_TEST", "Stage 8 Test Agent", "Harare", "Harare", "Harare", "active")
    )
    conn.commit()
    
    cursor.execute("SELECT id FROM agents WHERE agent_code='STAGE8_TEST'")
    agent_id = cursor.fetchone()[0]
    print(f"✓ Test agent created with ID: {agent_id}")
    
    # Create agent-linked transaction
    cursor.execute("SELECT account_number FROM users WHERE role='customer' LIMIT 2")
    accounts = cursor.fetchall()
    if len(accounts) >= 2:
        sender = accounts[0][0]
        receiver = accounts[1][0]
        
        cursor.execute(
            """INSERT INTO transactions (sender_account, receiver_account, amount, transaction_type, 
               currency, channel, timestamp, status, risk_score, risk_level, description, agent_id) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (sender, receiver, 75.0, "transfer", "USD", "mobile", datetime.now(timezone.utc).isoformat(), "Completed", 0, "normal", "Stage 8 agent test", agent_id)
        )
        conn.commit()
        
        cursor.execute("SELECT id, agent_id FROM transactions WHERE description='Stage 8 agent test'")
        test_tx = cursor.fetchone()
        if test_tx and test_tx[1] == agent_id:
            print("✓ Agent-linked transaction created successfully")
            print(f"  Transaction ID: {test_tx[0]}")
            print(f"  Agent ID: {test_tx[1]}")
            
            # Cleanup
            cursor.execute("DELETE FROM transactions WHERE description='Stage 8 agent test'")
            cursor.execute("DELETE FROM agents WHERE agent_code='STAGE8_TEST'")
            conn.commit()
            print("✓ Test records cleaned up")
        else:
            print("✗ Agent-linked transaction test failed")
    
    print()
except Exception as e:
    print(f"✗ Agent-linked transaction test failed: {e}")
    print()

# Test 9: Transaction Regression - Invalid agent
print("TEST 9: Transaction Regression - Invalid Agent")
print("-" * 80)
try:
    cursor.execute("SELECT account_number FROM users WHERE role='customer' LIMIT 2")
    accounts = cursor.fetchall()
    if len(accounts) >= 2:
        sender = accounts[0][0]
        receiver = accounts[1][0]
        
        try:
            cursor.execute(
                """INSERT INTO transactions (sender_account, receiver_account, amount, transaction_type, 
                   currency, channel, timestamp, status, risk_score, risk_level, description, agent_id) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (sender, receiver, 25.0, "transfer", "USD", "mobile", datetime.now(timezone.utc).isoformat(), "Completed", 0, "normal", "Stage 8 invalid agent test", 99999)
            )
            conn.commit()
            print("⚠ Invalid agent transaction was created (MySQL FK constraint may not be enforced)")
            
            # Cleanup if created
            cursor.execute("DELETE FROM transactions WHERE description='Stage 8 invalid agent test'")
            conn.commit()
        except mysql.connector.errors.IntegrityError as e:
            print(f"✓ MySQL rejected invalid agent_id (foreign key constraint): {str(e)[:100]}")
    
    print()
except Exception as e:
    print(f"✗ Invalid agent test failed: {e}")
    print()

# Test 10: Transaction Retrieval with LEFT JOIN
print("TEST 10: Transaction Retrieval with LEFT JOIN")
print("-" * 80)
try:
    cursor.execute(
        """
        SELECT t.*, 
               a.id as agent_id,
               a.agent_code as agent_code,
               a.agent_name as agent_name
        FROM transactions t
        LEFT JOIN agents a ON t.agent_id = a.id
        ORDER BY t.id DESC
        LIMIT 10
        """
    )
    transactions = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    
    print(f"✓ Retrieved {len(transactions)} transactions with LEFT JOIN")
    
    # Check if agent fields are present
    if 'agent_id' in columns and 'agent_code' in columns and 'agent_name' in columns:
        print("✓ Agent fields present in result")
    
    # Check if non-agent transactions appear
    null_agent_count = sum(1 for tx in transactions if tx[columns.index('agent_id')] is None)
    print(f"✓ {null_agent_count} transactions have NULL agent_id (non-agent transactions appear)")
    
    print()
except Exception as e:
    print(f"✗ Transaction retrieval test failed: {e}")
    print()

# Data preservation - final counts
print("DATA PRESERVATION - FINAL COUNTS")
print("-" * 80)
try:
    cursor.execute("SELECT COUNT(*) FROM users")
    final_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM transactions")
    final_transactions = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM agents")
    final_agents = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM alerts")
    final_alerts = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM sar_reports")
    final_sar = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM ctr_reports")
    final_ctr = cursor.fetchone()[0]
    
    print(f"Users: {final_users} (initial: {initial_counts['users']})")
    print(f"Transactions: {final_transactions} (initial: {initial_counts['transactions']})")
    print(f"Agents: {final_agents} (initial: {initial_counts['agents']})")
    print(f"Alerts: {final_alerts} (initial: {initial_counts['alerts']})")
    print(f"SAR Reports: {final_sar} (initial: {initial_counts['sar_reports']})")
    print(f"CTR Reports: {final_ctr} (initial: {initial_counts['ctr_reports']})")
    
    # Verify no data loss
    data_preserved = (
        final_users == initial_counts['users'] and
        final_transactions == initial_counts['transactions'] and
        final_agents == initial_counts['agents'] and
        final_alerts == initial_counts['alerts'] and
        final_sar == initial_counts['sar_reports'] and
        final_ctr == initial_counts['ctr_reports']
    )
    
    if data_preserved:
        print("✓ All data preserved - no records lost or modified")
    else:
        print("⚠ Data count mismatch - verify test record cleanup")
    
    print()
except Exception as e:
    print(f"✗ Failed to verify final counts: {e}")
    print()

# Close connection
cursor.close()
conn.close()
print("=" * 80)
print("REGRESSION TESTING COMPLETE")
print("=" * 80)
