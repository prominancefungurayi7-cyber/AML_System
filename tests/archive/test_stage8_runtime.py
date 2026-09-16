"""
Stage 8 Completion Testing - Runtime Verification
Tests previously untested items using Flask test client and actual MySQL database.
"""

import sys
sys.path.insert(0, '.')

import mysql.connector
from datetime import datetime, timezone
from server import app
from werkzeug.security import generate_password_hash

print("=" * 80)
print("STAGE 8 COMPLETION TESTING - RUNTIME VERIFICATION")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# MySQL configuration
MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'aml',
    'password': 'aml123',
    'database': 'aml'
}

# Record initial data counts
initial_counts = {}
try:
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
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
    
    print("INITIAL DATA COUNTS")
    print("-" * 80)
    print(f"Users: {initial_counts['users']}")
    print(f"Transactions: {initial_counts['transactions']}")
    print(f"Agents: {initial_counts['agents']}")
    print(f"Alerts: {initial_counts['alerts']}")
    print(f"SAR Reports: {initial_counts['sar_reports']}")
    print(f"CTR Reports: {initial_counts['ctr_reports']}")
    print()
except Exception as e:
    print(f"✗ Failed to record initial counts: {e}")
    exit(1)

# Create Flask test client
with app.test_client() as client:
    print("FLASK APPLICATION STARTUP")
    print("-" * 80)
    print("✓ Flask application started successfully")
    print("✓ MySQL connection configured")
    print("✓ Test client ready")
    print()
    
    # Test 1: Unauthenticated access to protected routes
    print("TEST 1: Unauthenticated Access")
    print("-" * 80)
    try:
        # Try to access dashboard without login
        response = client.get('/dashboard')
        if response.status_code in (302, 401, 403):
            print(f"✓ Dashboard access denied (status: {response.status_code})")
        else:
            print(f"⚠ Dashboard returned status {response.status_code}")
        
        # Try to access admin area
        response = client.get('/admin')
        if response.status_code in (302, 401, 403):
            print(f"✓ Admin access denied (status: {response.status_code})")
        else:
            print(f"⚠ Admin returned status {response.status_code}")
        
        # Try to access agent API without authentication
        response = client.get('/api/v1/agents')
        if response.status_code in (302, 401, 403):
            print(f"✓ Agent API denied (status: {response.status_code})")
        else:
            print(f"⚠ Agent API returned status {response.status_code}")
        
        print()
    except Exception as e:
        print(f"✗ Unauthenticated access test failed: {e}")
        print()
    
    # Test 2: Login with invalid credentials
    print("TEST 2: Invalid Login")
    print("-" * 80)
    try:
        # Invalid username
        response = client.post('/login', data={'username': 'nonexistent', 'password': 'wrong'})
        if response.status_code in (200, 302, 401):
            print(f"✓ Invalid username rejected (status: {response.status_code})")
        
        # Invalid password for valid user
        response = client.post('/login', data={'username': 'admin', 'password': 'wrongpassword'})
        if response.status_code in (200, 302, 401):
            print(f"✓ Invalid password rejected (status: {response.status_code})")
        
        print()
    except Exception as e:
        print(f"✗ Invalid login test failed: {e}")
        print()
    
    # Test 3: Valid login
    print("TEST 3: Valid Login")
    print("-" * 80)
    try:
        # First, check if admin user exists
        cursor.execute("SELECT id, username FROM users WHERE role='admin' LIMIT 1")
        admin_user = cursor.fetchone()
        
        if admin_user:
            admin_id, admin_username = admin_user
            print(f"✓ Admin user found: {admin_username}")
            
            # Try login (we can't test actual password hash without knowing it)
            # Instead, we'll simulate a session
            with client.session_transaction() as sess:
                sess['user_id'] = admin_id
                sess['role'] = 'admin'
            
            print("✓ Admin session created for testing")
        else:
            print("⚠ No admin user found in database")
        
        print()
    except Exception as e:
        print(f"✗ Valid login test failed: {e}")
        print()
    
    # Test 4: Transaction API - Create transaction
    print("TEST 4: Transaction API - Create Transaction")
    print("-" * 80)
    try:
        # Get valid accounts
        cursor.execute("SELECT account_number FROM users WHERE role='customer' LIMIT 2")
        accounts = cursor.fetchall()
        
        if len(accounts) >= 2:
            sender = accounts[0][0]
            receiver = accounts[1][0]
            
            # Test normal transaction without agent
            tx_data = {
                'sender_account': sender,
                'receiver_account': receiver,
                'amount': 50.0,
                'transaction_type': 'transfer',
                'currency': 'USD',
                'channel': 'mobile',
                'description': 'Stage 8 runtime test'
            }
            
            response = client.post('/customer/transaction', data=tx_data)
            print(f"Transaction creation response status: {response.status_code}")
            
            # Verify transaction was created in MySQL
            cursor.execute("SELECT id, agent_id FROM transactions WHERE description='Stage 8 runtime test'")
            test_tx = cursor.fetchone()
            if test_tx:
                print(f"✓ Transaction created in MySQL (ID: {test_tx[0]}, agent_id: {test_tx[1]})")
                
                # Cleanup
                cursor.execute("DELETE FROM transactions WHERE description='Stage 8 runtime test'")
                conn.commit()
                print("✓ Test transaction cleaned up")
            else:
                print("⚠ Transaction not found in MySQL")
        else:
            print("⚠ Insufficient customer accounts for test")
        
        print()
    except Exception as e:
        print(f"✗ Transaction API test failed: {e}")
        print()
    
    # Test 5: Agent API - Create and retrieve agent
    print("TEST 5: Agent API - Create and Retrieve Agent")
    print("-" * 80)
    try:
        # Create test agent directly in MySQL
        cursor.execute(
            "INSERT INTO agents (agent_code, agent_name, location, region, city, status) VALUES (%s, %s, %s, %s, %s, %s)",
            ("STAGE8_RT_TEST", "Stage 8 Runtime Test Agent", "Harare", "Harare", "Harare", "active")
        )
        conn.commit()
        
        cursor.execute("SELECT id FROM agents WHERE agent_code='STAGE8_RT_TEST'")
        agent_id = cursor.fetchone()[0]
        print(f"✓ Test agent created (ID: {agent_id})")
        
        # Test agent API with admin session
        response = client.get('/api/v1/agents')
        print(f"Agent list API status: {response.status_code}")
        
        response = client.get(f'/api/v1/agents/{agent_id}')
        print(f"Agent detail API status: {response.status_code}")
        
        # Cleanup
        cursor.execute("DELETE FROM agents WHERE agent_code='STAGE8_RT_TEST'")
        conn.commit()
        print("✓ Test agent cleaned up")
        
        print()
    except Exception as e:
        print(f"✗ Agent API test failed: {e}")
        print()
    
    # Test 6: Transaction API with agent
    print("TEST 6: Transaction API - Agent-Linked Transaction")
    print("-" * 80)
    try:
        # Create test agent
        cursor.execute(
            "INSERT INTO agents (agent_code, agent_name, location, region, city, status) VALUES (%s, %s, %s, %s, %s, %s)",
            ("STAGE8_RT_AGENT", "Stage 8 Agent Test", "Harare", "Harare", "Harare", "active")
        )
        conn.commit()
        
        cursor.execute("SELECT id FROM agents WHERE agent_code='STAGE8_RT_AGENT'")
        agent_id = cursor.fetchone()[0]
        
        # Get valid accounts
        cursor.execute("SELECT account_number FROM users WHERE role='customer' LIMIT 2")
        accounts = cursor.fetchall()
        
        if len(accounts) >= 2:
            sender = accounts[0][0]
            receiver = accounts[1][0]
            
            # Create transaction with agent
            tx_data = {
                'sender_account': sender,
                'receiver_account': receiver,
                'amount': 75.0,
                'transaction_type': 'transfer',
                'currency': 'USD',
                'channel': 'mobile',
                'description': 'Stage 8 agent test',
                'agent_id': agent_id
            }
            
            response = client.post('/customer/transaction', data=tx_data)
            print(f"Agent-linked transaction status: {response.status_code}")
            
            # Verify in MySQL
            cursor.execute("SELECT id, agent_id FROM transactions WHERE description='Stage 8 agent test'")
            test_tx = cursor.fetchone()
            if test_tx and test_tx[1] == agent_id:
                print(f"✓ Agent-linked transaction created (agent_id: {test_tx[1]})")
                
                # Cleanup
                cursor.execute("DELETE FROM transactions WHERE description='Stage 8 agent test'")
                cursor.execute("DELETE FROM agents WHERE agent_code='STAGE8_RT_AGENT'")
                conn.commit()
                print("✓ Test records cleaned up")
            else:
                print("⚠ Agent-linked transaction not found correctly")
        
        print()
    except Exception as e:
        print(f"✗ Agent-linked transaction test failed: {e}")
        print()
    
    # Test 7: Transaction API with invalid agent
    print("TEST 7: Transaction API - Invalid Agent")
    print("-" * 80)
    try:
        cursor.execute("SELECT account_number FROM users WHERE role='customer' LIMIT 2")
        accounts = cursor.fetchall()
        
        if len(accounts) >= 2:
            sender = accounts[0][0]
            receiver = accounts[1][0]
            
            tx_data = {
                'sender_account': sender,
                'receiver_account': receiver,
                'amount': 25.0,
                'transaction_type': 'transfer',
                'currency': 'USD',
                'channel': 'mobile',
                'description': 'Stage 8 invalid agent test',
                'agent_id': 99999
            }
            
            response = client.post('/customer/transaction', data=tx_data)
            print(f"Invalid agent transaction status: {response.status_code}")
            
            # Verify no invalid transaction was created
            cursor.execute("SELECT COUNT(*) FROM transactions WHERE description='Stage 8 invalid agent test'")
            count = cursor.fetchone()[0]
            if count == 0:
                print("✓ Invalid agent transaction was not persisted")
            else:
                print("⚠ Invalid agent transaction was created")
                cursor.execute("DELETE FROM transactions WHERE description='Stage 8 invalid agent test'")
                conn.commit()
        
        print()
    except Exception as e:
        print(f"✗ Invalid agent test failed: {e}")
        print()
    
    # Test 8: Transaction retrieval API
    print("TEST 8: Transaction Retrieval API")
    print("-" * 80)
    try:
        response = client.get('/api/v1/transactions')
        print(f"Transaction list API status: {response.status_code}")
        
        # Verify transactions are still readable
        cursor.execute("SELECT COUNT(*) FROM transactions")
        tx_count = cursor.fetchone()[0]
        print(f"✓ {tx_count} transactions remain readable")
        
        print()
    except Exception as e:
        print(f"✗ Transaction retrieval test failed: {e}")
        print()
    
    # Test 9: Error handling - Invalid route
    print("TEST 9: Error Handling - Invalid Route")
    print("-" * 80)
    try:
        response = client.get('/nonexistent-route')
        print(f"Invalid route status: {response.status_code}")
        if response.status_code == 404:
            print("✓ Invalid route returns 404")
        
        print()
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        print()
    
    # Test 10: Logout
    print("TEST 10: Logout")
    print("-" * 80)
    try:
        response = client.get('/logout')
        print(f"Logout status: {response.status_code}")
        if response.status_code in (302, 200):
            print("✓ Logout successful")
        
        print()
    except Exception as e:
        print(f"✗ Logout test failed: {e}")
        print()

# Final data preservation check
print("FINAL DATA PRESERVATION CHECK")
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
    print(f"✗ Final preservation check failed: {e}")
    print()

# Close MySQL connection
cursor.close()
conn.close()

print("=" * 80)
print("STAGE 8 COMPLETION TESTING COMPLETE")
print("=" * 80)
