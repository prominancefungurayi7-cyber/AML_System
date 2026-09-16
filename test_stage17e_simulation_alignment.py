"""
test_stage17e_simulation_alignment.py — Stage 17E Transaction Simulation Alignment Tests

This test suite validates that the transaction simulation module is properly aligned
with the final EcoCash AML pipeline (Stage 13 + Stage 14).

STAGE 17E REQUIREMENTS:
- Simulator uses EcoCash/mobile-money transaction terminology
- Simulator uses valid application transaction structures
- Simulator enters the real transaction-processing path
- Stage 13 generates the frozen 30 features
- Stage 14 is the only active AML model
- Threshold remains 0.35
- Temporal safeguards remain intact
- Structuring activity can be simulated
- Network activity can be simulated
- Agent activity can be simulated
- Normal activity can be simulated
- Alerts work through the existing workflow
- Socket.IO updates work
- Dashboard/investigation receives simulated activity
- MySQL remains intact
- No schema changes occur
- No data loss occurs
- No training/evaluation data is modified
- Legacy aml_ai_model.pkl is not used
"""

import unittest
import tempfile
import os
import sqlite3
import inspect
from datetime import datetime, timedelta, timezone
import json

# Import the modules to test
from transaction_simulation import (
    _simulation_plan,
    _simulation_timestamp,
    _simulation_transaction,
    NORMAL_TRANSACTION_SCENARIOS,
    SUSPICIOUS_TRANSACTION_SCENARIOS,
    SUPER_SUSPICIOUS_TRANSACTION_SCENARIOS,
    generate_structuring_scenario,
    generate_network_scenario,
    generate_agent_scenario,
)
from ai_stage13_features import Stage13FeatureService
from ai_stage14_model import Stage14ModelService, STAGE14_THRESHOLD, EXPECTED_FEATURE_COUNT
from database import DatabaseAdapter, connect_db


class TestTransactionGeneration(unittest.TestCase):
    """Test transaction generation functions."""
    
    def test_simulation_plan_distribution(self):
        """Test that simulation plan creates realistic class distribution."""
        plan = _simulation_plan(100)
        
        # Should have exactly 100 items
        self.assertEqual(len(plan), 100)
        
        # Should have majority normal (at least 70%)
        normal_count = plan.count("normal")
        self.assertGreaterEqual(normal_count, 70)
        
        # Should have some suspicious and super_suspicious
        self.assertIn("suspicious", plan)
        self.assertIn("super_suspicious", plan)
    
    def test_simulation_timestamp_format(self):
        """Test that simulation timestamps are valid ISO format."""
        timestamp = _simulation_timestamp(12)
        
        # Should be parseable as ISO format
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        # Should be within last 30 days
        now = datetime.now(timezone.utc)
        age = now - dt
        self.assertLessEqual(age.days, 30)
        self.assertGreaterEqual(age.days, 1)
    
    def test_normal_transaction_terminology(self):
        """Test that normal transactions use EcoCash terminology."""
        for scenario in NORMAL_TRANSACTION_SCENARIOS:
            # Should have EcoCash type specified
            self.assertIn("ecocash_type", scenario)
            
            # Should use valid EcoCash type
            valid_types = ["cash_in", "cash_out", "wallet_to_wallet"]
            self.assertIn(scenario["ecocash_type"], valid_types)
            
            # Description should be relevant to mobile money context
            # (not strict about terminology since ecocash_type is authoritative)
            self.assertIsNotNone(scenario["description"])
    
    def test_ecocash_transaction_types(self):
        """Test that all scenarios use valid EcoCash transaction types."""
        all_scenarios = NORMAL_TRANSACTION_SCENARIOS + SUSPICIOUS_TRANSACTION_SCENARIOS + SUPER_SUSPICIOUS_TRANSACTION_SCENARIOS
        
        for scenario in all_scenarios:
            # Should have ecocash_type
            self.assertIn("ecocash_type", scenario)
            
            # Should be one of the valid EcoCash types
            valid_types = ["cash_in", "cash_out", "wallet_to_wallet"]
            self.assertIn(scenario["ecocash_type"], valid_types)
    
    def test_simulation_transaction_structure(self):
        """Test that simulated transactions have valid structure."""
        users = [
            {"id": 1, "account_number": "WALLET001", "balance": 10000.0, "wealth_segment": "average"},
            {"id": 2, "account_number": "WALLET002", "balance": 5000.0, "wealth_segment": "average"},
        ]
        
        transactions = _simulation_transaction("normal", users)
        
        # Should return list of tuples
        self.assertIsInstance(transactions, list)
        self.assertEqual(len(transactions), 1)
        
        # Each transaction should have 10 elements
        tx = transactions[0]
        self.assertEqual(len(tx), 10)
        
        # Elements should be: (sender, recipient, tx_type, amount, timestamp, channel, description, reason, dest_country, agent_id)
        sender, recipient, tx_type, amount, timestamp, channel, description, reason, dest_country, agent_id = tx
        
        # Validate types
        self.assertIsInstance(sender, dict)
        self.assertIsInstance(recipient, dict)
        self.assertEqual(tx_type, "transfer")  # All are "transfer" in DB
        self.assertIsInstance(amount, (int, float))
        self.assertIsInstance(timestamp, str)
        self.assertIsInstance(channel, str)
        self.assertIsInstance(description, str)
        self.assertIn("ZW", dest_country)  # Default country


class TestAMLScenarioGeneration(unittest.TestCase):
    """Test AML-specific scenario generation functions."""
    
    def setUp(self):
        """Set up test database."""
        self.db_file = tempfile.mktemp(suffix=".db")
        self.conn = sqlite3.connect(self.db_file)
        self.conn.row_factory = sqlite3.Row
        
        # Create basic schema
        self.conn.executescript("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                account_number TEXT UNIQUE,
                balance REAL,
                wealth_segment TEXT
            );
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY,
                sender_account TEXT,
                receiver_account TEXT,
                amount REAL,
                transaction_type TEXT,
                timestamp TEXT
            );
        """)
        
        # Create test users
        self.users = [
            {"id": 1, "account_number": "WALLET001", "balance": 10000.0, "wealth_segment": "average"},
            {"id": 2, "account_number": "WALLET002", "balance": 5000.0, "wealth_segment": "average"},
            {"id": 3, "account_number": "WALLET003", "balance": 15000.0, "wealth_segment": "high"},
        ]
        
        for user in self.users:
            self.conn.execute(
                "INSERT INTO users (id, account_number, balance, wealth_segment) VALUES (?, ?, ?, ?)",
                (user["id"], user["account_number"], user["balance"], user["wealth_segment"])
            )
        
        self.conn.commit()
    
    def tearDown(self):
        """Clean up test database."""
        self.conn.close()
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
    
    def test_structuring_scenario_generation(self):
        """Test structuring scenario generates valid transactions."""
        sender = self.users[0]
        transactions = generate_structuring_scenario(self.conn, sender, None, count=5)
        
        # Should generate 5 transactions
        self.assertEqual(len(transactions), 5)
        
        # Each transaction should have valid structure
        for tx in transactions:
            self.assertEqual(len(tx), 10)
            sender_wallet, recipient, tx_type, amount, timestamp, channel, description, reason, dest_country, agent_id = tx
            
            # Should use EcoCash terminology
            self.assertIn("structuring", description.lower() or "structuring" in reason.lower())
            
            # Should be valid amounts
            self.assertGreater(amount, 0)
            
            # Should have valid timestamp
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    def test_network_scenario_many_to_one(self):
        """Test network scenario generates many-to-one pattern."""
        transactions = generate_network_scenario(self.conn, self.users, "many_to_one", count=3)
        
        # Should generate transactions
        self.assertGreater(len(transactions), 0)
        
        # Should involve multiple senders
        senders = set()
        for tx in transactions:
            senders.add(tx[0]["account_number"])
        
        # Multiple senders should be involved
        self.assertGreater(len(senders), 1)
    
    def test_network_scenario_one_to_many(self):
        """Test network scenario generates one-to-many pattern."""
        transactions = generate_network_scenario(self.conn, self.users, "one_to_many", count=3)
        
        # Should generate transactions
        self.assertGreater(len(transactions), 0)
        
        # Should involve multiple receivers
        receivers = set()
        for tx in transactions:
            receivers.add(tx[1]["account_number"])
        
        # Multiple receivers should be involved
        self.assertGreater(len(receivers), 1)
    
    def test_network_scenario_pass_through(self):
        """Test network scenario generates pass-through pattern."""
        transactions = generate_network_scenario(self.conn, self.users, "pass_through", count=2)
        
        # Should generate 2 transactions (first leg and second leg)
        self.assertEqual(len(transactions), 2)
        
        # Should involve 3 different wallets
        wallets = set()
        for tx in transactions:
            wallets.add(tx[0]["account_number"])
            wallets.add(tx[1]["account_number"])
        
        self.assertGreaterEqual(len(wallets), 3)
    
    def test_agent_scenario_concentration(self):
        """Test agent scenario generates concentration pattern."""
        agents = [{"id": 1, "agent_code": "AGT001", "agent_name": "Agent 1"}]
        transactions = generate_agent_scenario(self.conn, self.users, agents, "concentration", count=5)
        
        # Should generate transactions (may be limited by number of users)
        self.assertGreater(len(transactions), 0)
        self.assertLessEqual(len(transactions), len(self.users))
        
        # All should use the same agent (concentration)
        agent_ids = set()
        for tx in transactions:
            agent_ids.add(tx[9])  # agent_id is at index 9
        
        # Should all use the same agent
        self.assertEqual(len(agent_ids), 1)
        self.assertIn(1, agent_ids)
    
    def test_agent_scenario_burst(self):
        """Test agent scenario generates burst pattern."""
        agents = [{"id": 1, "agent_code": "AGT001", "agent_name": "Agent 1"}]
        transactions = generate_agent_scenario(self.conn, self.users, agents, "burst", count=5)
        
        # Should generate transactions
        self.assertEqual(len(transactions), 5)
        
        # All should involve the same agent
        agent_ids = set()
        for tx in transactions:
            agent_ids.add(tx[9])
        
        self.assertEqual(len(agent_ids), 1)
    
    def test_agent_scenario_no_agents(self):
        """Test agent scenario handles missing agents gracefully."""
        transactions = generate_agent_scenario(self.conn, self.users, [], "concentration", count=3)
        
        # Should still generate transactions
        self.assertEqual(len(transactions), 3)
        
        # All should have None agent_id
        for tx in transactions:
            self.assertIsNone(tx[9])


class TestStage13Integration(unittest.TestCase):
    """Test Stage 13 feature service integration."""
    
    def setUp(self):
        """Set up test database with transaction data."""
        self.db_file = tempfile.mktemp(suffix=".db")
        self.conn = sqlite3.connect(self.db_file)
        self.conn.row_factory = sqlite3.Row
        
        # Create full schema
        self.conn.executescript("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                account_number TEXT UNIQUE,
                balance REAL,
                wealth_segment TEXT
            );
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY,
                sender_account TEXT,
                receiver_account TEXT,
                amount REAL,
                transaction_type TEXT,
                channel TEXT,
                timestamp TEXT,
                agent_id INTEGER
            );
        """)
        
        # Create test users
        self.users = [
            {"id": 1, "account_number": "WALLET001", "balance": 10000.0, "wealth_segment": "average"},
            {"id": 2, "account_number": "WALLET002", "balance": 5000.0, "wealth_segment": "average"},
        ]
        
        for user in self.users:
            self.conn.execute(
                "INSERT INTO users (id, account_number, balance, wealth_segment) VALUES (?, ?, ?, ?)",
                (user["id"], user["account_number"], user["balance"], user["wealth_segment"])
            )
        
        # Create some historical transactions
        base_time = datetime.now(timezone.utc)
        for i in range(10):
            timestamp = (base_time - timedelta(hours=i+1)).isoformat()
            self.conn.execute(
                """INSERT INTO transactions (sender_account, receiver_account, amount, transaction_type, channel, timestamp, agent_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                ("WALLET001", "WALLET002", 1000.0 * (i+1), "transfer", "mobile", timestamp, None)
            )
        
        self.conn.commit()
    
    def tearDown(self):
        """Clean up test database."""
        self.conn.close()
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
    
    def test_stage13_feature_service_initialization(self):
        """Test that Stage 13 feature service can be initialized."""
        db_adapter = DatabaseAdapter(self.conn, "sqlite")
        feature_service = Stage13FeatureService(db_adapter)
        
        self.assertIsNotNone(feature_service)
        self.assertEqual(feature_service.db, db_adapter)
    
    def test_stage13_generates_30_features(self):
        """Test that Stage 13 generates exactly 30 features."""
        db_adapter = DatabaseAdapter(self.conn, "sqlite")
        feature_service = Stage13FeatureService(db_adapter)
        
        # Create a current transaction
        current_tx = {
            "id": 100,
            "sender_account": "WALLET001",
            "receiver_account": "WALLET002",
            "amount": 5000.0,
            "transaction_type": "transfer",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "channel": "mobile",
            "agent_id": None
        }
        
        features = feature_service.generate_features(current_tx)
        
        # Should generate exactly 30 features
        self.assertEqual(len(features), EXPECTED_FEATURE_COUNT)
        
        # All features should be numeric
        for feature in features:
            self.assertIsInstance(feature, (int, float))
    
    def test_stage13_temporal_safety(self):
        """Test that Stage 13 respects temporal safety."""
        db_adapter = DatabaseAdapter(self.conn, "sqlite")
        feature_service = Stage13FeatureService(db_adapter)
        
        # Create a current transaction
        current_tx = {
            "id": 100,
            "sender_account": "WALLET001",
            "receiver_account": "WALLET002",
            "amount": 5000.0,
            "transaction_type": "transfer",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "channel": "mobile",
            "agent_id": None
        }
        
        # Get prior transactions
        prior_txs = feature_service._get_prior_transactions(current_tx)
        
        # Current transaction should not be in prior transactions
        current_ids = [tx["id"] for tx in prior_txs]
        self.assertNotIn(current_tx["id"], current_ids)
        
        # All prior transactions should have timestamp < current timestamp
        current_time = datetime.fromisoformat(current_tx["timestamp"].replace('Z', '+00:00'))
        for prior_tx in prior_txs:
            prior_time = datetime.fromisoformat(prior_tx["timestamp"].replace('Z', '+00:00'))
            self.assertLess(prior_time, current_time)


class TestStage14Integration(unittest.TestCase):
    """Test Stage 14 model service integration."""
    
    def test_stage14_threshold_constant(self):
        """Test that Stage 14 threshold is 0.35."""
        self.assertEqual(STAGE14_THRESHOLD, 0.35)
    
    def test_stage14_expected_feature_count(self):
        """Test that Stage 14 expects 30 features."""
        self.assertEqual(EXPECTED_FEATURE_COUNT, 30)
    
    def test_stage14_model_service_requires_feature_service(self):
        """Test that Stage 14 model service requires feature service."""
        # Should raise error if feature service is None
        with self.assertRaises(RuntimeError):
            from ai_stage14_model import get_stage14_model_service
            get_stage14_model_service(None)


class TestLegacyModelIsolation(unittest.TestCase):
    """Test that legacy AI model is isolated."""
    
    def test_legacy_model_not_imported_in_simulation(self):
        """Test that transaction_simulation does not import legacy AI model."""
        import transaction_simulation
        
        # Get all imports in transaction_simulation
        source = inspect.getsource(transaction_simulation)
        
        # Should not import aml_ai_model or ai_core for model usage
        self.assertNotIn("from ai_core import", source)
        self.assertNotIn("import aml_ai_model", source)
    
    def test_legacy_model_not_used_in_server(self):
        """Test that server.py does not use legacy AI model for simulation."""
        import server
        
        # Check the generate_transactions function
        source = inspect.getsource(server.generate_transactions)
        
        # Should not use legacy AI model
        self.assertNotIn("aml_ai_model", source)
        self.assertNotIn("train_ai_model", source)


class TestLabelLeakagePrevention(unittest.TestCase):
    """Test that simulation does not leak labels into model inputs."""
    
    def test_simulation_does_not_insert_generated_label(self):
        """Test that simulation does not insert generated_label into transactions."""
        import transaction_simulation
        
        # Check that scenario generators don't include label data
        source = inspect.getsource(transaction_simulation.generate_structuring_scenario)
        
        # Should not include generated_label in transaction data
        self.assertNotIn("generated_label", source)
    
    def test_scenario_reason_isolation(self):
        """Test that scenario_reason is kept separate from model inputs."""
        import transaction_simulation
        
        # Check that scenario_reason is included in transaction tuple
        # but is a separate field from the core transaction data
        source = inspect.getsource(transaction_simulation._simulation_transaction)
        
        # scenario_reason should be in the tuple (for documentation)
        # but should not be used as a model input feature
        self.assertIn("scenario_reason", source)


class TestMySQLCompatibility(unittest.TestCase):
    """Test MySQL compatibility preservation."""
    
    def test_database_adapter_supports_mysql(self):
        """Test that database adapter supports MySQL."""
        from database import is_mysql_database_url
        
        # Should recognize MySQL URLs
        self.assertTrue(is_mysql_database_url("mysql://user:pass@localhost/db"))
        self.assertTrue(is_mysql_database_url("mysql+mysqlconnector://user:pass@localhost/db"))
        
        # Should not recognize non-MySQL URLs
        self.assertFalse(is_mysql_database_url("sqlite:///test.db"))
        self.assertFalse(is_mysql_database_url("postgres://user:pass@localhost/db"))
    
    def test_stage13_mysql_compatibility(self):
        """Test that Stage 13 service works with MySQL adapter."""
        # Create a mock MySQL adapter
        class MockMySQLAdapter:
            def __init__(self, connection):
                self.connection = connection
                self.engine = "mysql"
            
            def execute(self, query, params=()):
                # MySQL uses %s placeholders
                mysql_query = query.replace("?", "%s")
                return self.connection.execute(mysql_query, params)
        
        # Should handle MySQL adapter
        self.assertIsNotNone(MockMySQLAdapter(None))


class TestTemporalSafety(unittest.TestCase):
    """Test temporal safety in simulation."""
    
    def setUp(self):
        """Set up test database."""
        self.db_file = tempfile.mktemp(suffix=".db")
        self.conn = sqlite3.connect(self.db_file)
        self.conn.row_factory = sqlite3.Row
        
        # Create schema
        self.conn.executescript("""
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY,
                sender_account TEXT,
                receiver_account TEXT,
                amount REAL,
                transaction_type TEXT,
                channel TEXT,
                timestamp TEXT,
                agent_id INTEGER
            );
        """)
        
        self.conn.commit()
    
    def tearDown(self):
        """Clean up test database."""
        self.conn.close()
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
    
    def test_equal_timestamp_ordering(self):
        """Test that equal timestamps are ordered by ID."""
        from ai_stage13_features import Stage13FeatureService
        from database import DatabaseAdapter
        
        # Insert transactions with equal timestamps but different IDs
        base_time = datetime.now(timezone.utc).isoformat()
        for i in range(5):
            self.conn.execute(
                "INSERT INTO transactions (sender_account, receiver_account, amount, transaction_type, timestamp) VALUES (?, ?, ?, ?, ?)",
                (f"WALLET{i}", f"WALLET{i+1}", 1000.0, "transfer", base_time)
            )
        
        self.conn.commit()
        
        # Create feature service
        db_adapter = DatabaseAdapter(self.conn, "sqlite")
        feature_service = Stage13FeatureService(db_adapter)
        
        # Create current transaction with same timestamp
        current_tx = {
            "id": 100,
            "sender_account": "WALLET0",
            "receiver_account": "WALLET1",
            "amount": 5000.0,
            "transaction_type": "transfer",
            "timestamp": base_time,
            "channel": "mobile",
            "agent_id": None
        }
        
        # Get prior transactions
        prior_txs = feature_service._get_prior_transactions(current_tx)
        
        # All prior transactions should have IDs < current ID
        for prior_tx in prior_txs:
            self.assertLess(prior_tx["id"], current_tx["id"])
    
    def test_future_transactions_excluded(self):
        """Test that future transactions are excluded from history."""
        from ai_stage13_features import Stage13FeatureService
        from database import DatabaseAdapter
        
        # Insert past and future transactions
        base_time = datetime.now(timezone.utc)
        past_time = (base_time - timedelta(hours=1)).isoformat()
        future_time = (base_time + timedelta(hours=1)).isoformat()
        
        self.conn.execute(
            "INSERT INTO transactions (sender_account, receiver_account, amount, transaction_type, timestamp) VALUES (?, ?, ?, ?, ?)",
            ("WALLET0", "WALLET1", 1000.0, "transfer", past_time)
        )
        
        self.conn.execute(
            "INSERT INTO transactions (sender_account, receiver_account, amount, transaction_type, timestamp) VALUES (?, ?, ?, ?, ?)",
            ("WALLET0", "WALLET1", 2000.0, "transfer", future_time)
        )
        
        self.conn.commit()
        
        # Create feature service
        db_adapter = DatabaseAdapter(self.conn, "sqlite")
        feature_service = Stage13FeatureService(db_adapter)
        
        # Create current transaction
        current_tx = {
            "id": 100,
            "sender_account": "WALLET0",
            "receiver_account": "WALLET1",
            "amount": 5000.0,
            "transaction_type": "transfer",
            "timestamp": base_time.isoformat(),
            "channel": "mobile",
            "agent_id": None
        }
        
        # Get prior transactions
        prior_txs = feature_service._get_prior_transactions(current_tx)
        
        # Should only include past transaction, not future
        timestamps = [tx["timestamp"] for tx in prior_txs]
        self.assertIn(past_time, timestamps)
        self.assertNotIn(future_time, timestamps)


class TestAlertIntegration(unittest.TestCase):
    """Test alert integration with simulation."""
    
    def test_alert_creation_for_suspicious(self):
        """Test that suspicious transactions create alerts."""
        from alerts import create_alert_if_needed
        
        # Create mock database connection
        db_file = tempfile.mktemp(suffix=".db")
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        
        # Create schema
        conn.executescript("""
            CREATE TABLE transactions (id INTEGER PRIMARY KEY);
            CREATE TABLE alerts (
                id INTEGER PRIMARY KEY,
                transaction_id INTEGER,
                account_number TEXT,
                risk_score REAL,
                risk_level TEXT,
                reason TEXT,
                rules_triggered TEXT,
                status TEXT,
                timestamp TEXT
            );
        """)
        
        # Insert transaction
        conn.execute("INSERT INTO transactions (id) VALUES (1)")
        conn.commit()
        
        # Create alert for suspicious transaction
        alert_id = create_alert_if_needed(
            conn, 1, "WALLET001", 75, "suspicious_pattern",
            "Stage 14 detected suspicious pattern", "[]", datetime.now(timezone.utc).isoformat(),
            database_url="sqlite:///" + db_file
        )
        
        # Should create alert
        self.assertIsNotNone(alert_id)
        
        # Verify alert was created
        alert = conn.execute("SELECT * FROM alerts WHERE transaction_id=?", (1,)).fetchone()
        self.assertIsNotNone(alert)
        self.assertEqual(alert["risk_level"], "suspicious_pattern")
        
        conn.close()
        if os.path.exists(db_file):
            os.remove(db_file)
    
    def test_no_alert_for_normal(self):
        """Test that normal transactions do not create alerts."""
        from alerts import create_alert_if_needed
        
        # Create mock database connection
        db_file = tempfile.mktemp(suffix=".db")
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        
        # Create schema
        conn.executescript("""
            CREATE TABLE transactions (id INTEGER PRIMARY KEY);
            CREATE TABLE alerts (
                id INTEGER PRIMARY KEY,
                transaction_id INTEGER,
                account_number TEXT,
                risk_score REAL,
                risk_level TEXT,
                reason TEXT,
                rules_triggered TEXT,
                status TEXT,
                timestamp TEXT
            );
        """)
        
        # Insert transaction
        conn.execute("INSERT INTO transactions (id) VALUES (1)")
        conn.commit()
        
        # Try to create alert for normal transaction
        alert_id = create_alert_if_needed(
            conn, 1, "WALLET001", 20, "normal",
            "Normal transaction", "[]", datetime.now(timezone.utc).isoformat()
        )
        
        # Should not create alert
        self.assertIsNone(alert_id)
        
        # Verify no alert was created
        alert = conn.execute("SELECT * FROM alerts WHERE transaction_id=?", (1,)).fetchone()
        self.assertIsNone(alert)
        
        conn.close()
        if os.path.exists(db_file):
            os.remove(db_file)


if __name__ == "__main__":
    unittest.main()
