"""
Stage 7 MySQL Verification Script
Tests MySQL foreign-key behaviour and API integration against actual MySQL database.
"""

import mysql.connector
from datetime import datetime, timezone

print("=" * 80)
print("STAGE 7 MYSQL VERIFICATION")
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

try:
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    print("✓ MySQL connection successful")
    print()
except Exception as e:
    print(f"✗ MySQL connection failed: {e}")
    print("MYSQL_TEST_BLOCKED — MySQL server/configuration unavailable")
    exit(1)

# Test 1: Verify agents table structure
print("TEST 1: Verify agents table structure")
print("-" * 80)
try:
    cursor.execute("DESCRIBE agents")
    agents_desc = cursor.fetchall()
    agents_columns = {row[0]: row for row in agents_desc}
    
    required_fields = ['id', 'agent_code', 'agent_name', 'location', 'region', 'city', 'status', 'created_at']
    for field in required_fields:
        if field in agents_columns:
            print(f"✓ Field {field} exists")
        else:
            print(f"✗ Field {field} missing")
    
    # Verify agent_code is UNIQUE
    if agents_columns['agent_code'][3] == 'UNI':
        print("✓ agent_code has UNIQUE constraint")
    else:
        print("⚠ agent_code UNIQUE constraint not verified")
    
    print()
except Exception as e:
    print(f"✗ Agents table verification failed: {e}")
    print()

# Test 2: Verify transactions.agent_id exists
print("TEST 2: Verify transactions.agent_id exists")
print("-" * 80)
try:
    cursor.execute("DESCRIBE transactions")
    tx_desc = cursor.fetchall()
    tx_columns = {row[0]: row for row in tx_desc}
    
    if 'agent_id' in tx_columns:
        print("✓ agent_id column exists in transactions table")
        
        # Check if it allows NULL
        if tx_columns['agent_id'][2] == 'YES':
            print("✓ agent_id allows NULL (backward compatible)")
        else:
            print("✗ agent_id does NOT allow NULL (breaks backward compatibility)")
        
        # Check if it has MUL (index)
        if tx_columns['agent_id'][3] == 'MUL':
            print("✓ agent_id has index")
        else:
            print("⚠ agent_id index not verified")
    else:
        print("✗ agent_id column NOT found in transactions table")
    
    print()
except Exception as e:
    print(f"✗ Transactions table verification failed: {e}")
    print()

# Test 3: Foreign key behaviour - Valid agent
print("TEST 3: Foreign Key - Valid Agent")
print("-" * 80)
try:
    # Create test agent
    cursor.execute(
        "INSERT INTO agents (agent_code, agent_name, location, region, city, status) VALUES (%s, %s, %s, %s, %s, %s)",
        ("TEST001", "Test Agent", "Harare", "Harare", "Harare", "active")
    )
    conn.commit()
    
    cursor.execute("SELECT id FROM agents WHERE agent_code='TEST001'")
    agent_id = cursor.fetchone()[0]
    print(f"✓ Test agent created with ID: {agent_id}")
    
    # Create transaction with valid agent
    cursor.execute(
        """INSERT INTO transactions (sender_account, receiver_account, amount, transaction_type, 
           currency, channel, timestamp, status, risk_score, risk_level, description, agent_id) 
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        ("ACC0001", "ACC0002", 100.0, "transfer", "USD", "online", "2026-09-14T12:00:00Z", "Completed", 0, "normal", "Test with valid agent", agent_id)
    )
    conn.commit()
    print("✓ Transaction with valid agent created successfully")
    
    # Verify agent_id was stored
    cursor.execute("SELECT agent_id FROM transactions WHERE description='Test with valid agent'")
    tx_agent = cursor.fetchone()
    if tx_agent and tx_agent[0] == agent_id:
        print(f"✓ agent_id stored correctly: {tx_agent[0]}")
    else:
        print("✗ agent_id not stored correctly")
    
    # Cleanup
    cursor.execute("DELETE FROM transactions WHERE description='Test with valid agent'")
    cursor.execute("DELETE FROM agents WHERE agent_code='TEST001'")
    conn.commit()
    print("✓ Test records cleaned up")
    
    print()
except Exception as e:
    print(f"✗ Valid agent test failed: {e}")
    print()

# Test 4: Foreign key behaviour - NULL agent
print("TEST 4: Foreign Key - NULL Agent")
print("-" * 80)
try:
    # Create transaction with NULL agent_id
    cursor.execute(
        """INSERT INTO transactions (sender_account, receiver_account, amount, transaction_type, 
           currency, channel, timestamp, status, risk_score, risk_level, description, agent_id) 
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        ("ACC0001", "ACC0002", 50.0, "transfer", "USD", "online", "2026-09-14T12:01:00Z", "Completed", 0, "normal", "Test with NULL agent", None)
    )
    conn.commit()
    print("✓ Transaction with NULL agent_id created successfully")
    
    # Verify NULL was stored
    cursor.execute("SELECT agent_id FROM transactions WHERE description='Test with NULL agent'")
    tx_agent = cursor.fetchone()
    if tx_agent and tx_agent[0] is None:
        print("✓ NULL agent_id stored correctly")
    else:
        print("✗ NULL agent_id not stored correctly")
    
    # Cleanup
    cursor.execute("DELETE FROM transactions WHERE description='Test with NULL agent'")
    conn.commit()
    print("✓ Test record cleaned up")
    
    print()
except Exception as e:
    print(f"✗ NULL agent test failed: {e}")
    print()

# Test 5: Foreign key behaviour - Invalid agent
print("TEST 5: Foreign Key - Invalid Agent")
print("-" * 80)
try:
    # Attempt to create transaction with invalid agent_id
    cursor.execute(
        """INSERT INTO transactions (sender_account, receiver_account, amount, transaction_type, 
           currency, channel, timestamp, status, risk_score, risk_level, description, agent_id) 
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        ("ACC0001", "ACC0002", 25.0, "transfer", "USD", "online", "2026-09-14T12:02:00Z", "Completed", 0, "normal", "Test with invalid agent", 99999)
    )
    conn.commit()
    print("⚠ Transaction with invalid agent_id was created (MySQL FK constraint may not be enforced)")
    
    # Cleanup if it was created
    cursor.execute("DELETE FROM transactions WHERE description='Test with invalid agent'")
    conn.commit()
    print("✓ Test record cleaned up")
    
    print("Note: API validation in server.py should prevent invalid agent_id before reaching database")
    print()
except mysql.connector.errors.IntegrityError as e:
    print(f"✓ MySQL rejected invalid agent_id (foreign key constraint): {e}")
    print()
except Exception as e:
    print(f"⚠ Invalid agent test: {e}")
    print()

# Test 6: LEFT JOIN query verification
print("TEST 6: Transaction API LEFT JOIN Verification")
print("-" * 80)
try:
    # Create test agent and transactions
    cursor.execute(
        "INSERT INTO agents (agent_code, agent_name, location, region, city, status) VALUES (%s, %s, %s, %s, %s, %s)",
        ("TEST002", "Test Agent 2", "Bulawayo", "Bulawayo", "Bulawayo", "active")
    )
    conn.commit()
    
    cursor.execute("SELECT id FROM agents WHERE agent_code='TEST002'")
    agent_id = cursor.fetchone()[0]
    
    # Create transaction with agent
    cursor.execute(
        """INSERT INTO transactions (sender_account, receiver_account, amount, transaction_type, 
           currency, channel, timestamp, status, risk_score, risk_level, description, agent_id) 
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        ("ACC0001", "ACC0002", 75.0, "transfer", "USD", "mobile", "2026-09-14T12:03:00Z", "Completed", 0, "normal", "Test LEFT JOIN with agent", agent_id)
    )
    conn.commit()
    
    # Create transaction without agent
    cursor.execute(
        """INSERT INTO transactions (sender_account, receiver_account, amount, transaction_type, 
           currency, channel, timestamp, status, risk_score, risk_level, description, agent_id) 
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        ("ACC0001", "ACC0002", 30.0, "transfer", "USD", "online", "2026-09-14T12:04:00Z", "Completed", 0, "normal", "Test LEFT JOIN without agent", None)
    )
    conn.commit()
    
    # Test LEFT JOIN query (same as API endpoint)
    cursor.execute(
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
        WHERE t.description LIKE 'Test LEFT JOIN%'
        ORDER BY t.id DESC
        """
    )
    results = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    
    if len(results) == 2:
        print(f"✓ LEFT JOIN returned {len(results)} transactions")
        
        # Convert to dict for easier access
        results_dict = [dict(zip(columns, row)) for row in results]
        
        # Check agent-linked transaction
        agent_tx = None
        null_tx = None
        for row in results_dict:
            if row['description'] == 'Test LEFT JOIN with agent':
                agent_tx = row
            elif row['description'] == 'Test LEFT JOIN without agent':
                null_tx = row
        
        if agent_tx and agent_tx['agent_id'] == agent_id:
            print("✓ Agent-linked transaction has correct agent_id")
            print(f"  Agent name: {agent_tx['agent_name']}")
        else:
            print("✗ Agent-linked transaction agent_id incorrect")
        
        if null_tx and null_tx['agent_id'] is None:
            print("✓ Non-agent transaction has NULL agent_id")
        else:
            print("✗ Non-agent transaction agent_id incorrect")
    else:
        print(f"✗ LEFT JOIN returned {len(results)} transactions (expected 2)")
    
    # Cleanup
    cursor.execute("DELETE FROM transactions WHERE description LIKE 'Test LEFT JOIN%'")
    cursor.execute("DELETE FROM agents WHERE agent_code='TEST002'")
    conn.commit()
    print("✓ Test records cleaned up")
    
    print()
except Exception as e:
    print(f"✗ LEFT JOIN test failed: {e}")
    print()

# Test 7: Existing transactions remain readable
print("TEST 7: Existing Transactions Remain Readable")
print("-" * 80)
try:
    cursor.execute("SELECT COUNT(*) FROM transactions")
    total_tx = cursor.fetchone()[0]
    print(f"✓ Total transactions in database: {total_tx}")
    
    cursor.execute("SELECT id, agent_id FROM transactions LIMIT 5")
    sample_tx = cursor.fetchall()
    print(f"✓ Sample transactions retrieved successfully")
    
    for tx in sample_tx:
        print(f"  Transaction ID: {tx[0]}, agent_id: {tx[1]}")
    
    print()
except Exception as e:
    print(f"✗ Existing transactions test failed: {e}")
    print()

# Close connection
cursor.close()
conn.close()
print("=" * 80)
print("MYSQL VERIFICATION COMPLETE")
print("=" * 80)
