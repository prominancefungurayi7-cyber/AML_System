"""
Stage 11: Safe Generation of Final 100,000-Transaction Synthetic AML Dataset

This script generates the final synthetic dataset according to the approved Stage 10C
specification and Stage 11 generation contract.

CRITICAL:
- Binary labels ONLY (0=normal, 1=suspicious_pattern_scenario)
- NO model training
- NO feature extraction
- NO risk/rule-derived labels
- STRICT partition isolation
- EXACT specification compliance

Approved Stage 10C Parameters:
- 2,000 customers/wallets (1:1 mapping)
- 160 agents
- 100,000 transactions total
- 88,000 normal / 12,000 suspicious
- 4,000 structuring / 4,000 network / 4,000 agent suspicious
- 60,000 train / 15,000 validation / 15,000 final test / 10,000 independent
- 75,000 agent-mediated / 25,000 direct P2P
- Synthetic threshold: 10,000 (synthetic_reporting_threshold_v1)
"""

import json
import random
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set, Optional
import uuid

# =============================================================================
# CONFIGURATION
# =============================================================================

MASTER_SEED = 42
RANDOM_SEED = 42

DATASET_VERSION = "ecocash_aml_synthetic_100k_v1"
GENERATION_DATE = "2026-09-15"

# Approved Stage 10C population parameters
TOTAL_TRANSACTIONS = 100000
TOTAL_CUSTOMERS = 2000
TOTAL_WALLETS = 2000  # 1:1 mapping with customers
TOTAL_AGENTS = 160

# Class distribution
NORMAL_COUNT = 88000
SUSPICIOUS_COUNT = 12000

# Suspicious domain allocation
STRUCTURING_COUNT = 4000
NETWORK_COUNT = 4000
AGENT_COUNT = 4000

# Partition allocation
TRAIN_TX = 60000
TRAIN_WALLETS = 1200
TRAIN_AGENTS = 96

VAL_TX = 15000
VAL_WALLETS = 300
VAL_AGENTS = 24

TEST_TX = 15000
TEST_WALLETS = 300
TEST_AGENTS = 24

INDEPENDENT_TX = 10000
INDEPENDENT_WALLETS = 200
INDEPENDENT_AGENTS = 16

# Channel allocation
AGENT_MEDIATED_COUNT = 75000
DIRECT_P2P_COUNT = 25000

# Synthetic reporting threshold
SYNTHETIC_REPORTING_THRESHOLD = 10000
THRESHOLD_VERSION = "synthetic_reporting_threshold_v1"

# Scenario family cap
MAX_TX_PER_FAMILY = 1000

# Wallet transaction distribution (bounded over-dispersed)
MIN_TX_PER_WALLET = 35
MAX_TX_PER_WALLET = 75
MEAN_TX_PER_WALLET = 50

# Agent transaction distribution
MIN_TX_PER_AGENT = 150
MAX_TX_PER_AGENT = 900

# Minimum history requirements
MIN_WALLET_HISTORY = 12
MIN_AGENT_HISTORY = 30

# =============================================================================
# REPRODUCIBILITY
# =============================================================================

def seed_all(seed: int):
    """Seed all random number generators for reproducibility."""
    random.seed(seed)

seed_all(RANDOM_SEED)

# =============================================================================
# DATA STRUCTURES
# =============================================================================

class Wallet:
    def __init__(self, wallet_id: str, customer_id: str, partition: str):
        self.wallet_id = wallet_id
        self.customer_id = customer_id
        self.partition = partition
        self.transactions = []
        self.wealth_segment = random.choice(["low", "average", "high", "commercial"])

class Agent:
    def __init__(self, agent_id: str, partition: str):
        self.agent_id = agent_id
        self.partition = partition
        self.transactions = []

class Transaction:
    def __init__(self, transaction_id: str, event_timestamp: datetime, event_sequence: int,
                 sender_wallet: str, receiver_wallet: str, amount: float,
                 transaction_type: str, channel: str, agent_id: Optional[str],
                 partition: str):
        self.transaction_id = transaction_id
        self.event_timestamp = event_timestamp
        self.event_sequence = event_sequence
        self.sender_wallet = sender_wallet
        self.receiver_wallet = receiver_wallet
        self.amount = amount
        self.transaction_type = transaction_type
        self.channel = channel
        self.agent_id = agent_id
        self.partition = partition

class GroundTruth:
    def __init__(self, transaction_id: str, ground_truth_label: int,
                 scenario_id: Optional[str] = None, scenario_type: Optional[str] = None,
                 scenario_category: Optional[str] = None, signal_strength: Optional[str] = None,
                 scenario_source: Optional[str] = None, affected_wallets: Optional[List[str]] = None,
                 affected_agent: Optional[str] = None):
        self.transaction_id = transaction_id
        self.ground_truth_label = ground_truth_label  # 0=normal, 1=suspicious
        self.scenario_id = scenario_id
        self.scenario_type = scenario_type
        self.scenario_category = scenario_category
        self.signal_strength = signal_strength
        self.scenario_source = scenario_source
        self.affected_wallets = affected_wallets or []
        self.affected_agent = affected_agent

# =============================================================================
# ENTITY GENERATION
# =============================================================================

def generate_entities() -> Tuple[Dict[str, Wallet], Dict[str, Agent]]:
    """Generate wallets and agents with partition assignments."""
    
    wallets = {}
    agents = {}
    
    # Generate wallets by partition
    wallet_partitions = {
        "train": TRAIN_WALLETS,
        "validation": VAL_WALLETS,
        "final_test": TEST_WALLETS,
        "independent": INDEPENDENT_WALLETS
    }
    
    wallet_counter = 0
    for partition, count in wallet_partitions.items():
        for i in range(count):
            wallet_id = f"W{wallet_counter:04d}"
            customer_id = f"C{wallet_counter:04d}"
            wallets[wallet_id] = Wallet(wallet_id, customer_id, partition)
            wallet_counter += 1
    
    # Generate agents by partition
    agent_partitions = {
        "train": TRAIN_AGENTS,
        "validation": VAL_AGENTS,
        "final_test": TEST_AGENTS,
        "independent": INDEPENDENT_AGENTS
    }
    
    agent_counter = 0
    for partition, count in agent_partitions.items():
        for i in range(count):
            agent_id = f"A{agent_counter:04d}"
            agents[agent_id] = Agent(agent_id, partition)
            agent_counter += 1
    
    return wallets, agents

# =============================================================================
# SCENARIO GENERATION
# =============================================================================

class ScenarioGenerator:
    """Generate suspicious scenarios according to Stage 11 specification."""
    
    def __init__(self, wallets: Dict[str, Wallet], agents: Dict[str, Agent]):
        self.wallets = wallets
        self.agents = agents
        self.scenario_counter = 0
        self.transaction_counter = 0
        self.global_tx_counter = 0  # Global counter for unique IDs
    
    def _get_partition_wallets(self, partition: str) -> List[Wallet]:
        return [w for w in self.wallets.values() if w.partition == partition]
    
    def _get_partition_agents(self, partition: str) -> List[Agent]:
        return [a for a in self.agents.values() if a.partition == partition]
    
    def _generate_scenario_id(self) -> str:
        self.scenario_counter += 1
        return f"SCN{self.scenario_counter:06d}"
    
    def _generate_transaction_id(self) -> str:
        self.global_tx_counter += 1
        return f"TXN{self.global_tx_counter:06d}"
    
    # ========================================
    # STRUCTURING SCENARIOS (Families S1-S4)
    # ========================================
    
    def generate_variable_fragment_burst(self, partition: str, target_count: int) -> List[Tuple[Transaction, GroundTruth]]:
        """Family S1: Variable Fragment Burst"""
        results = []
        partition_wallets = self._get_partition_wallets(partition)
        partition_agents = self._get_partition_agents(partition)
        
        generated = 0
        while generated < target_count:
            # Select participating wallets
            num_wallets = random.randint(2, 8)
            participating_wallets = random.sample(partition_wallets, min(num_wallets, len(partition_wallets)))
            
            # Generate burst sequence
            num_tx = random.randint(3, 12)
            base_amount = random.uniform(50, 1200)
            
            start_time = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(
                days=random.randint(0, 90),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            for i in range(num_tx):
                if generated >= target_count:
                    break
                
                sender = random.choice(participating_wallets)
                receiver = random.choice([w for w in partition_wallets if w.wallet_id != sender.wallet_id])
                
                # Vary amount
                amount = base_amount * random.uniform(0.8, 1.2)
                
                # Timing
                spacing = random.randint(2, 55)
                tx_time = start_time + timedelta(minutes=i * spacing)
                
                # Channel
                use_agent = random.random() < 0.75
                agent_id = random.choice(partition_agents).agent_id if use_agent and partition_agents else None
                channel = "agent" if agent_id else "p2p"
                
                tx = Transaction(
                    transaction_id=self._generate_transaction_id(),
                    event_timestamp=tx_time,
                    event_sequence=generated,
                    sender_wallet=sender.wallet_id,
                    receiver_wallet=receiver.wallet_id,
                    amount=amount,
                    transaction_type="transfer",
                    channel=channel,
                    agent_id=agent_id,
                    partition=partition
                )
                
                gt = GroundTruth(
                    transaction_id=tx.transaction_id,
                    ground_truth_label=1,
                    scenario_id=self._generate_scenario_id(),
                    scenario_type="variable_fragment_burst",
                    scenario_category="structuring",
                    signal_strength="medium",
                    scenario_source="stage11_generator",
                    affected_wallets=[sender.wallet_id, receiver.wallet_id],
                    affected_agent=agent_id
                )
                
                results.append((tx, gt))
                generated += 1
        
        return results
    
    def generate_similar_amount_repetition(self, partition: str, target_count: int) -> List[Tuple[Transaction, GroundTruth]]:
        """Family S2: Similar Amount Repetition"""
        results = []
        partition_wallets = self._get_partition_wallets(partition)
        partition_agents = self._get_partition_agents(partition)
        
        generated = 0
        while generated < target_count:
            num_wallets = random.randint(1, 5)
            participating_wallets = random.sample(partition_wallets, min(num_wallets, len(partition_wallets)))
            
            num_tx = random.randint(4, 15)
            base_amount = random.uniform(200, 2500)
            
            start_time = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(
                days=random.randint(0, 90),
                hours=random.randint(0, 23)
            )
            
            for i in range(num_tx):
                if generated >= target_count:
                    break
                
                sender = random.choice(participating_wallets)
                receiver = random.choice([w for w in partition_wallets if w.wallet_id != sender.wallet_id])
                
                # Similar amount with ±0-5% variation
                variation = random.uniform(0.95, 1.05)
                amount = base_amount * variation
                
                spacing = random.randint(10, 180)  # 10 min to 3 hours
                tx_time = start_time + timedelta(minutes=i * spacing)
                
                use_agent = random.random() < 0.75
                agent_id = random.choice(partition_agents).agent_id if use_agent and partition_agents else None
                channel = "agent" if agent_id else "p2p"
                
                tx = Transaction(
                    transaction_id=self._generate_transaction_id(),
                    event_timestamp=tx_time,
                    event_sequence=generated,
                    sender_wallet=sender.wallet_id,
                    receiver_wallet=receiver.wallet_id,
                    amount=amount,
                    transaction_type="transfer",
                    channel=channel,
                    agent_id=agent_id,
                    partition=partition
                )
                
                gt = GroundTruth(
                    transaction_id=tx.transaction_id,
                    ground_truth_label=1,
                    scenario_id=self._generate_scenario_id(),
                    scenario_type="similar_amount_repetition",
                    scenario_category="structuring",
                    signal_strength="medium",
                    scenario_source="stage11_generator",
                    affected_wallets=[sender.wallet_id, receiver.wallet_id],
                    affected_agent=agent_id
                )
                
                results.append((tx, gt))
                generated += 1
        
        return results
    
    def generate_distributed_same_day_fragmentation(self, partition: str, target_count: int) -> List[Tuple[Transaction, GroundTruth]]:
        """Family S3: Distributed Same-Day Fragmentation"""
        results = []
        partition_wallets = self._get_partition_wallets(partition)
        partition_agents = self._get_partition_agents(partition)
        
        generated = 0
        while generated < target_count:
            num_wallets = random.randint(2, 10)
            participating_wallets = random.sample(partition_wallets, min(num_wallets, len(partition_wallets)))
            
            num_tx = random.randint(3, 10)
            
            start_time = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(
                days=random.randint(0, 90),
                hours=random.randint(8, 18)  # Business hours
            )
            
            for i in range(num_tx):
                if generated >= target_count:
                    break
                
                sender = random.choice(participating_wallets)
                receiver = random.choice([w for w in partition_wallets if w.wallet_id != sender.wallet_id])
                
                amount = random.uniform(100, 3000)
                
                spacing = random.randint(20, 720)  # 20 min to 12 hours
                tx_time = start_time + timedelta(minutes=i * spacing)
                
                use_agent = random.random() < 0.75
                agent_id = random.choice(partition_agents).agent_id if use_agent and partition_agents else None
                channel = "agent" if agent_id else "p2p"
                
                tx = Transaction(
                    transaction_id=self._generate_transaction_id(),
                    event_timestamp=tx_time,
                    event_sequence=generated,
                    sender_wallet=sender.wallet_id,
                    receiver_wallet=receiver.wallet_id,
                    amount=amount,
                    transaction_type="transfer",
                    channel=channel,
                    agent_id=agent_id,
                    partition=partition
                )
                
                gt = GroundTruth(
                    transaction_id=tx.transaction_id,
                    ground_truth_label=1,
                    scenario_id=self._generate_scenario_id(),
                    scenario_type="distributed_same_day_fragmentation",
                    scenario_category="structuring",
                    signal_strength="medium",
                    scenario_source="stage11_generator",
                    affected_wallets=[sender.wallet_id, receiver.wallet_id],
                    affected_agent=agent_id
                )
                
                results.append((tx, gt))
                generated += 1
        
        return results
    
    def generate_variable_near_threshold_history(self, partition: str, target_count: int) -> List[Tuple[Transaction, GroundTruth]]:
        """Family S4: Variable Near-Threshold History"""
        results = []
        partition_wallets = self._get_partition_wallets(partition)
        partition_agents = self._get_partition_agents(partition)
        
        generated = 0
        while generated < target_count:
            num_wallets = random.randint(1, 6)
            participating_wallets = random.sample(partition_wallets, min(num_wallets, len(partition_wallets)))
            
            num_tx = random.randint(3, 9)
            
            start_time = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(
                days=random.randint(0, 90)
            )
            
            for i in range(num_tx):
                if generated >= target_count:
                    break
                
                sender = random.choice(participating_wallets)
                receiver = random.choice([w for w in partition_wallets if w.wallet_id != sender.wallet_id])
                
                # Mix of near-threshold and normal amounts
                if random.random() < 0.6:  # 60% near threshold
                    amount = random.uniform(9000, 9950)
                else:  # 40% normal amounts
                    amount = random.uniform(100, 8000)
                
                spacing = random.randint(15, 2880)  # 15 min to 48 hours
                tx_time = start_time + timedelta(minutes=i * spacing)
                
                use_agent = random.random() < 0.75
                agent_id = random.choice(partition_agents).agent_id if use_agent and partition_agents else None
                channel = "agent" if agent_id else "p2p"
                
                tx = Transaction(
                    transaction_id=self._generate_transaction_id(),
                    event_timestamp=tx_time,
                    event_sequence=generated,
                    sender_wallet=sender.wallet_id,
                    receiver_wallet=receiver.wallet_id,
                    amount=amount,
                    transaction_type="transfer",
                    channel=channel,
                    agent_id=agent_id,
                    partition=partition
                )
                
                gt = GroundTruth(
                    transaction_id=tx.transaction_id,
                    ground_truth_label=1,
                    scenario_id=self._generate_scenario_id(),
                    scenario_type="variable_near_threshold_history",
                    scenario_category="structuring",
                    signal_strength="medium",
                    scenario_source="stage11_generator",
                    affected_wallets=[sender.wallet_id, receiver.wallet_id],
                    affected_agent=agent_id
                )
                
                results.append((tx, gt))
                generated += 1
        
        return results
    
    # ========================================
    # NETWORK SCENARIOS (Families N1-N4)
    # ========================================
    
    def generate_many_to_one_collection(self, partition: str, target_count: int) -> List[Tuple[Transaction, GroundTruth]]:
        """Family N1: Many-to-One Collection"""
        results = []
        partition_wallets = self._get_partition_wallets(partition)
        partition_agents = self._get_partition_agents(partition)
        
        generated = 0
        while generated < target_count:
            num_senders = random.randint(4, 30)
            participating_wallets = random.sample(partition_wallets, min(num_senders + 1, len(partition_wallets)))
            collector = participating_wallets[0]
            senders = participating_wallets[1:]
            
            num_tx = random.randint(5, 80)
            
            start_time = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(
                days=random.randint(0, 90)
            )
            
            for i in range(num_tx):
                if generated >= target_count:
                    break
                
                sender = random.choice(senders)
                
                amount = random.uniform(40, 800)
                
                spacing = random.randint(60, 1440)  # 1 hour to 1 day
                tx_time = start_time + timedelta(minutes=i * spacing)
                
                use_agent = random.random() < 0.75
                agent_id = random.choice(partition_agents).agent_id if use_agent and partition_agents else None
                channel = "agent" if agent_id else "p2p"
                
                tx = Transaction(
                    transaction_id=self._generate_transaction_id(),
                    event_timestamp=tx_time,
                    event_sequence=generated,
                    sender_wallet=sender.wallet_id,
                    receiver_wallet=collector.wallet_id,
                    amount=amount,
                    transaction_type="transfer",
                    channel=channel,
                    agent_id=agent_id,
                    partition=partition
                )
                
                gt = GroundTruth(
                    transaction_id=tx.transaction_id,
                    ground_truth_label=1,
                    scenario_id=self._generate_scenario_id(),
                    scenario_type="many_to_one_collection",
                    scenario_category="network",
                    signal_strength="medium",
                    scenario_source="stage11_generator",
                    affected_wallets=[sender.wallet_id, collector.wallet_id],
                    affected_agent=agent_id
                )
                
                results.append((tx, gt))
                generated += 1
        
        return results
    
    def generate_one_to_many_dispersion(self, partition: str, target_count: int) -> List[Tuple[Transaction, GroundTruth]]:
        """Family N2: One-to-Many Dispersion"""
        results = []
        partition_wallets = self._get_partition_wallets(partition)
        partition_agents = self._get_partition_agents(partition)
        
        generated = 0
        while generated < target_count:
            num_receivers = random.randint(5, 35)
            participating_wallets = random.sample(partition_wallets, min(num_receivers + 1, len(partition_wallets)))
            source = participating_wallets[0]
            receivers = participating_wallets[1:]
            
            num_tx = random.randint(6, 90)
            
            start_time = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(
                days=random.randint(0, 90)
            )
            
            for i in range(num_tx):
                if generated >= target_count:
                    break
                
                receiver = random.choice(receivers)
                
                amount = random.uniform(100, 2000)
                
                spacing = random.randint(60, 1440)
                tx_time = start_time + timedelta(minutes=i * spacing)
                
                use_agent = random.random() < 0.75
                agent_id = random.choice(partition_agents).agent_id if use_agent and partition_agents else None
                channel = "agent" if agent_id else "p2p"
                
                tx = Transaction(
                    transaction_id=self._generate_transaction_id(),
                    event_timestamp=tx_time,
                    event_sequence=generated,
                    sender_wallet=source.wallet_id,
                    receiver_wallet=receiver.wallet_id,
                    amount=amount,
                    transaction_type="transfer",
                    channel=channel,
                    agent_id=agent_id,
                    partition=partition
                )
                
                gt = GroundTruth(
                    transaction_id=tx.transaction_id,
                    ground_truth_label=1,
                    scenario_id=self._generate_scenario_id(),
                    scenario_type="one_to_many_dispersion",
                    scenario_category="network",
                    signal_strength="medium",
                    scenario_source="stage11_generator",
                    affected_wallets=[source.wallet_id, receiver.wallet_id],
                    affected_agent=agent_id
                )
                
                results.append((tx, gt))
                generated += 1
        
        return results
    
    def generate_reciprocal_relationship_cycle(self, partition: str, target_count: int) -> List[Tuple[Transaction, GroundTruth]]:
        """Family N3: Reciprocal Relationship Cycle"""
        results = []
        partition_wallets = self._get_partition_wallets(partition)
        partition_agents = self._get_partition_agents(partition)
        
        generated = 0
        while generated < target_count:
            num_wallets = random.randint(2, 12)
            participating_wallets = random.sample(partition_wallets, min(num_wallets, len(partition_wallets)))
            
            num_tx = random.randint(4, 50)
            
            start_time = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(
                days=random.randint(0, 90)
            )
            
            for i in range(num_tx):
                if generated >= target_count:
                    break
                
                # Create cycle
                idx1 = i % len(participating_wallets)
                idx2 = (i + 1) % len(participating_wallets)
                sender = participating_wallets[idx1]
                receiver = participating_wallets[idx2]
                
                amount = random.uniform(500, 5000)
                
                spacing = random.randint(30, 720)
                tx_time = start_time + timedelta(minutes=i * spacing)
                
                use_agent = random.random() < 0.75
                agent_id = random.choice(partition_agents).agent_id if use_agent and partition_agents else None
                channel = "agent" if agent_id else "p2p"
                
                tx = Transaction(
                    transaction_id=self._generate_transaction_id(),
                    event_timestamp=tx_time,
                    event_sequence=generated,
                    sender_wallet=sender.wallet_id,
                    receiver_wallet=receiver.wallet_id,
                    amount=amount,
                    transaction_type="transfer",
                    channel=channel,
                    agent_id=agent_id,
                    partition=partition
                )
                
                gt = GroundTruth(
                    transaction_id=tx.transaction_id,
                    ground_truth_label=1,
                    scenario_id=self._generate_scenario_id(),
                    scenario_type="reciprocal_relationship_cycle",
                    scenario_category="network",
                    signal_strength="medium",
                    scenario_source="stage11_generator",
                    affected_wallets=[sender.wallet_id, receiver.wallet_id],
                    affected_agent=agent_id
                )
                
                results.append((tx, gt))
                generated += 1
        
        return results
    
    def generate_wallet_pass_through(self, partition: str, target_count: int) -> List[Tuple[Transaction, GroundTruth]]:
        """Family N4: Wallet Pass-Through"""
        results = []
        partition_wallets = self._get_partition_wallets(partition)
        partition_agents = self._get_partition_agents(partition)
        
        generated = 0
        while generated < target_count:
            num_transit = random.randint(3, 20)
            participating_wallets = random.sample(partition_wallets, min(num_transit, len(partition_wallets)))
            
            num_tx = random.randint(6, 70)
            
            start_time = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(
                days=random.randint(0, 90)
            )
            
            for i in range(num_tx):
                if generated >= target_count:
                    break
                
                # Create pass-through chain
                idx1 = i % len(participating_wallets)
                idx2 = (i + 1) % len(participating_wallets)
                sender = participating_wallets[idx1]
                receiver = participating_wallets[idx2]
                
                base_amount = random.uniform(1000, 10000)
                # Retain 1-5%
                retention = random.uniform(0.01, 0.05)
                amount = base_amount * (1 - retention)
                
                spacing = random.randint(5, 1440)  # 5 min to 1 day
                tx_time = start_time + timedelta(minutes=i * spacing)
                
                use_agent = random.random() < 0.75
                agent_id = random.choice(partition_agents).agent_id if use_agent and partition_agents else None
                channel = "agent" if agent_id else "p2p"
                
                tx = Transaction(
                    transaction_id=self._generate_transaction_id(),
                    event_timestamp=tx_time,
                    event_sequence=generated,
                    sender_wallet=sender.wallet_id,
                    receiver_wallet=receiver.wallet_id,
                    amount=amount,
                    transaction_type="transfer",
                    channel=channel,
                    agent_id=agent_id,
                    partition=partition
                )
                
                gt = GroundTruth(
                    transaction_id=tx.transaction_id,
                    ground_truth_label=1,
                    scenario_id=self._generate_scenario_id(),
                    scenario_type="wallet_pass_through",
                    scenario_category="network",
                    signal_strength="medium",
                    scenario_source="stage11_generator",
                    affected_wallets=[sender.wallet_id, receiver.wallet_id],
                    affected_agent=agent_id
                )
                
                results.append((tx, gt))
                generated += 1
        
        return results
    
    # ========================================
    # AGENT SCENARIOS (Families A1-A4)
    # ========================================
    
    def generate_agent_wallet_growth(self, partition: str, target_count: int) -> List[Tuple[Transaction, GroundTruth]]:
        """Family A1: Agent Wallet Growth"""
        results = []
        partition_wallets = self._get_partition_wallets(partition)
        partition_agents = self._get_partition_agents(partition)
        
        generated = 0
        while generated < target_count:
            num_agents = random.randint(1, 4)
            participating_agents = random.sample(partition_agents, min(num_agents, len(partition_agents)))
            agent = participating_agents[0]
            
            num_new_wallets = random.randint(8, 60)
            new_wallets = random.sample(partition_wallets, min(num_new_wallets, len(partition_wallets)))
            
            num_tx = random.randint(10, 100)
            
            start_time = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(
                days=random.randint(0, 90)
            )
            
            for i in range(num_tx):
                if generated >= target_count:
                    break
                
                sender = random.choice(new_wallets)
                receiver = random.choice([w for w in partition_wallets if w.wallet_id != sender.wallet_id])
                
                amount = random.uniform(50, 2000)
                
                spacing = random.randint(60, 1440)
                tx_time = start_time + timedelta(minutes=i * spacing)
                
                tx = Transaction(
                    transaction_id=self._generate_transaction_id(),
                    event_timestamp=tx_time,
                    event_sequence=generated,
                    sender_wallet=sender.wallet_id,
                    receiver_wallet=receiver.wallet_id,
                    amount=amount,
                    transaction_type="transfer",
                    channel="agent",
                    agent_id=agent.agent_id,
                    partition=partition
                )
                
                gt = GroundTruth(
                    transaction_id=tx.transaction_id,
                    ground_truth_label=1,
                    scenario_id=self._generate_scenario_id(),
                    scenario_type="agent_wallet_growth",
                    scenario_category="agent",
                    signal_strength="medium",
                    scenario_source="stage11_generator",
                    affected_wallets=[sender.wallet_id, receiver.wallet_id],
                    affected_agent=agent.agent_id
                )
                
                results.append((tx, gt))
                generated += 1
        
        return results
    
    def generate_agent_wallet_concentration(self, partition: str, target_count: int) -> List[Tuple[Transaction, GroundTruth]]:
        """Family A2: Agent Wallet Concentration"""
        results = []
        partition_wallets = self._get_partition_wallets(partition)
        partition_agents = self._get_partition_agents(partition)
        
        generated = 0
        while generated < target_count:
            num_agents = random.randint(1, 3)
            participating_agents = random.sample(partition_agents, min(num_agents, len(partition_agents)))
            agent = participating_agents[0]
            
            num_preferred = random.randint(3, 20)
            preferred_wallets = random.sample(partition_wallets, min(num_preferred, len(partition_wallets)))
            
            num_tx = random.randint(10, 80)
            
            start_time = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(
                days=random.randint(0, 90)
            )
            
            for i in range(num_tx):
                if generated >= target_count:
                    break
                
                # 80% use preferred wallets, 20% random
                if random.random() < 0.8:
                    sender = random.choice(preferred_wallets)
                else:
                    sender = random.choice(partition_wallets)
                
                receiver = random.choice([w for w in partition_wallets if w.wallet_id != sender.wallet_id])
                
                amount = random.uniform(100, 3000)
                
                spacing = random.randint(60, 1440)
                tx_time = start_time + timedelta(minutes=i * spacing)
                
                tx = Transaction(
                    transaction_id=self._generate_transaction_id(),
                    event_timestamp=tx_time,
                    event_sequence=generated,
                    sender_wallet=sender.wallet_id,
                    receiver_wallet=receiver.wallet_id,
                    amount=amount,
                    transaction_type="transfer",
                    channel="agent",
                    agent_id=agent.agent_id,
                    partition=partition
                )
                
                gt = GroundTruth(
                    transaction_id=tx.transaction_id,
                    ground_truth_label=1,
                    scenario_id=self._generate_scenario_id(),
                    scenario_type="agent_wallet_concentration",
                    scenario_category="agent",
                    signal_strength="medium",
                    scenario_source="stage11_generator",
                    affected_wallets=[sender.wallet_id, receiver.wallet_id],
                    affected_agent=agent.agent_id
                )
                
                results.append((tx, gt))
                generated += 1
        
        return results
    
    def generate_agent_temporal_burst(self, partition: str, target_count: int) -> List[Tuple[Transaction, GroundTruth]]:
        """Family A3: Agent Temporal Burst"""
        results = []
        partition_wallets = self._get_partition_wallets(partition)
        partition_agents = self._get_partition_agents(partition)
        
        generated = 0
        while generated < target_count:
            num_agents = random.randint(1, 5)
            participating_agents = random.sample(partition_agents, min(num_agents, len(partition_agents)))
            agent = participating_agents[0]
            
            num_wallets = random.randint(6, 50)
            participating_wallets = random.sample(partition_wallets, min(num_wallets, len(partition_wallets)))
            
            num_tx = random.randint(10, 60)
            
            # Burst duration: 15 min to 3 days
            burst_duration_minutes = random.randint(15, 4320)
            start_time = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(
                days=random.randint(0, 90)
            )
            
            for i in range(num_tx):
                if generated >= target_count:
                    break
                
                sender = random.choice(participating_wallets)
                receiver = random.choice([w for w in partition_wallets if w.wallet_id != sender.wallet_id])
                
                amount = random.uniform(50, 2500)
                
                # Concentrated timing
                spacing = random.randint(1, burst_duration_minutes // num_tx)
                tx_time = start_time + timedelta(minutes=i * spacing)
                
                tx = Transaction(
                    transaction_id=self._generate_transaction_id(),
                    event_timestamp=tx_time,
                    event_sequence=generated,
                    sender_wallet=sender.wallet_id,
                    receiver_wallet=receiver.wallet_id,
                    amount=amount,
                    transaction_type="transfer",
                    channel="agent",
                    agent_id=agent.agent_id,
                    partition=partition
                )
                
                gt = GroundTruth(
                    transaction_id=tx.transaction_id,
                    ground_truth_label=1,
                    scenario_id=self._generate_scenario_id(),
                    scenario_type="agent_temporal_burst",
                    scenario_category="agent",
                    signal_strength="medium",
                    scenario_source="stage11_generator",
                    affected_wallets=[sender.wallet_id, receiver.wallet_id],
                    affected_agent=agent.agent_id
                )
                
                results.append((tx, gt))
                generated += 1
        
        return results
    
    def generate_agent_flow_imbalance(self, partition: str, target_count: int) -> List[Tuple[Transaction, GroundTruth]]:
        """Family A4: Agent Flow Imbalance"""
        results = []
        partition_wallets = self._get_partition_wallets(partition)
        partition_agents = self._get_partition_agents(partition)
        
        generated = 0
        while generated < target_count:
            num_agents = random.randint(1, 4)
            participating_agents = random.sample(partition_agents, min(num_agents, len(partition_agents)))
            agent = participating_agents[0]
            
            num_wallets = random.randint(5, 35)
            participating_wallets = random.sample(partition_wallets, min(num_wallets, len(partition_wallets)))
            
            num_tx = random.randint(10, 70)
            
            # Directional bias: 80% one direction
            direction_bias = random.choice(["inbound", "outbound"])
            
            start_time = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(
                days=random.randint(0, 90)
            )
            
            for i in range(num_tx):
                if generated >= target_count:
                    break
                
                if random.random() < 0.8:
                    # Biased direction
                    if direction_bias == "inbound":
                        sender = random.choice(participating_wallets)
                        receiver = random.choice([w for w in partition_wallets if w.wallet_id not in [pw.wallet_id for pw in participating_wallets]])
                    else:
                        sender = random.choice([w for w in partition_wallets if w.wallet_id not in [pw.wallet_id for pw in participating_wallets]])
                        receiver = random.choice(participating_wallets)
                else:
                    # Occasional reverse direction
                    sender = random.choice(participating_wallets)
                    receiver = random.choice([w for w in partition_wallets if w.wallet_id != sender.wallet_id])
                
                amount = random.uniform(100, 3000)
                
                spacing = random.randint(60, 1440)
                tx_time = start_time + timedelta(minutes=i * spacing)
                
                tx = Transaction(
                    transaction_id=self._generate_transaction_id(),
                    event_timestamp=tx_time,
                    event_sequence=generated,
                    sender_wallet=sender.wallet_id,
                    receiver_wallet=receiver.wallet_id,
                    amount=amount,
                    transaction_type="transfer",
                    channel="agent",
                    agent_id=agent.agent_id,
                    partition=partition
                )
                
                gt = GroundTruth(
                    transaction_id=tx.transaction_id,
                    ground_truth_label=1,
                    scenario_id=self._generate_scenario_id(),
                    scenario_type="agent_flow_imbalance",
                    scenario_category="agent",
                    signal_strength="medium",
                    scenario_source="stage11_generator",
                    affected_wallets=[sender.wallet_id, receiver.wallet_id],
                    affected_agent=agent.agent_id
                )
                
                results.append((tx, gt))
                generated += 1
        
        return results

# =============================================================================
# NORMAL BEHAVIOUR GENERATION
# =============================================================================

def generate_normal_transactions(wallets: Dict[str, Wallet], agents: Dict[str, Agent],
                                 target_count: int, partition: str, target_agent_mediated: int) -> List[Tuple[Transaction, GroundTruth]]:
    """Generate diverse normal transactions with exact channel allocation."""
    
    partition_wallets = [w for w in wallets.values() if w.partition == partition]
    partition_agents = [a for a in agents.values() if a.partition == partition]
    
    results = []
    generated = 0
    agent_mediated_generated = 0
    
    while generated < target_count:
        sender = random.choice(partition_wallets)
        receiver = random.choice([w for w in partition_wallets if w.wallet_id != sender.wallet_id])
        
        # Amount based on wealth segment
        if sender.wealth_segment == "low":
            amount = random.uniform(5, 500)
        elif sender.wealth_segment == "average":
            amount = random.uniform(50, 2000)
        elif sender.wealth_segment == "high":
            amount = random.uniform(200, 10000)
        else:  # commercial
            amount = random.uniform(500, 20000)
        
        # Include some near-threshold normal transactions
        if random.random() < 0.05:  # 5% near threshold
            amount = random.uniform(8500, 9999)
        
        # Timing
        tx_time = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(
            days=random.randint(0, 180),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        # Channel: exact allocation
        remaining_agent = target_agent_mediated - agent_mediated_generated
        remaining_total = target_count - generated
        
        if remaining_agent > 0 and (remaining_agent / remaining_total > 0.75 or random.random() < 0.75):
            agent_id = random.choice(partition_agents).agent_id if partition_agents else None
            channel = "agent" if agent_id else "p2p"
            if agent_id:
                agent_mediated_generated += 1
        else:
            agent_id = None
            channel = "p2p"
        
        tx = Transaction(
            transaction_id=f"TXN{generated:06d}",
            event_timestamp=tx_time,
            event_sequence=generated,
            sender_wallet=sender.wallet_id,
            receiver_wallet=receiver.wallet_id,
            amount=amount,
            transaction_type="transfer",
            channel=channel,
            agent_id=agent_id,
            partition=partition
        )
        
        gt = GroundTruth(
            transaction_id=tx.transaction_id,
            ground_truth_label=0,  # Normal
            scenario_id=None,
            scenario_type=None,
            scenario_category=None,
            signal_strength=None,
            scenario_source="stage11_generator",
            affected_wallets=[sender.wallet_id, receiver.wallet_id],
            affected_agent=agent_id
        )
        
        results.append((tx, gt))
        generated += 1
    
    return results

# =============================================================================
# MAIN GENERATION
# =============================================================================

def main():
    print("=" * 80)
    print("STAGE 11: SAFE GENERATION OF FINAL 100,000-TRANSACTION SYNTHETIC AML DATASET")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Dataset Version: {DATASET_VERSION}")
    print(f"Random Seed: {RANDOM_SEED}")
    print()
    
    # Step 1: Generate entities
    print("Step 1: Generating entities...")
    wallets, agents = generate_entities()
    print(f"  Generated {len(wallets)} wallets across 4 partitions")
    print(f"  Generated {len(agents)} agents across 4 partitions")
    print()
    
    # Step 2: Initialize scenario generator
    print("Step 2: Initializing scenario generator...")
    scenario_gen = ScenarioGenerator(wallets, agents)
    print()
    
    # Step 3: Generate suspicious transactions by partition
    print("Step 3: Generating suspicious transactions...")
    all_transactions = []
    all_ground_truth = []
    
    # Calculate suspicious allocation per partition
    partition_suspicious = {
        "train": 7200,
        "validation": 1800,
        "final_test": 1800,
        "independent": 1200
    }
    
    # Calculate structuring/network/agent split per partition
    for partition, suspicious_count in partition_suspicious.items():
        structuring_count = suspicious_count // 3
        network_count = suspicious_count // 3
        agent_count = suspicious_count - structuring_count - network_count
        
        print(f"  Partition {partition}:")
        print(f"    Structuring: {structuring_count}")
        print(f"    Network: {network_count}")
        print(f"    Agent: {agent_count}")
        
        # Structuring scenarios (4 families, ~250 each)
        s_per_family = structuring_count // 4
        all_transactions.extend(scenario_gen.generate_variable_fragment_burst(partition, s_per_family))
        all_transactions.extend(scenario_gen.generate_similar_amount_repetition(partition, s_per_family))
        all_transactions.extend(scenario_gen.generate_distributed_same_day_fragmentation(partition, s_per_family))
        all_transactions.extend(scenario_gen.generate_variable_near_threshold_history(partition, s_per_family))
        
        # Network scenarios (4 families, ~250 each)
        n_per_family = network_count // 4
        all_transactions.extend(scenario_gen.generate_many_to_one_collection(partition, n_per_family))
        all_transactions.extend(scenario_gen.generate_one_to_many_dispersion(partition, n_per_family))
        all_transactions.extend(scenario_gen.generate_reciprocal_relationship_cycle(partition, n_per_family))
        all_transactions.extend(scenario_gen.generate_wallet_pass_through(partition, n_per_family))
        
        # Agent scenarios (4 families, ~250 each)
        a_per_family = agent_count // 4
        all_transactions.extend(scenario_gen.generate_agent_wallet_growth(partition, a_per_family))
        all_transactions.extend(scenario_gen.generate_agent_wallet_concentration(partition, a_per_family))
        all_transactions.extend(scenario_gen.generate_agent_temporal_burst(partition, a_per_family))
        all_transactions.extend(scenario_gen.generate_agent_flow_imbalance(partition, a_per_family))
    
    print(f"  Total suspicious transactions generated: {len(all_transactions)}")
    print()
    
    # Step 4: Generate normal transactions
    print("Step 4: Generating normal transactions...")
    partition_normal = {
        "train": 52800,
        "validation": 13200,
        "final_test": 13200,
        "independent": 8800
    }
    
    for partition, normal_count in partition_normal.items():
        print(f"  Partition {partition}: {normal_count} normal transactions")
        normal_txs = generate_normal_transactions(wallets, agents, normal_count, partition)
        all_transactions.extend(normal_txs)
    
    print(f"  Total normal transactions generated: {len([t for t, gt in all_transactions if gt.ground_truth_label == 0])}")
    print()
    
    # Step 5: Separate transactions and ground truth
    print("Step 5: Separating transactions and ground truth...")
    transactions_only = []
    ground_truth_only = []
    
    for tx, gt in all_transactions:
        transactions_only.append(tx)
        ground_truth_only.append(gt)
    
    print(f"  Transactions: {len(transactions_only)}")
    print(f"  Ground truth records: {len(ground_truth_only)}")
    print()
    
    # Step 6: Order events temporally
    print("Step 6: Ordering events temporally...")
    transactions_only.sort(key=lambda tx: (tx.event_timestamp, tx.event_sequence))
    for i, tx in enumerate(transactions_only):
        tx.event_sequence = i
    print(f"  Ordered {len(transactions_only)} transactions")
    print()
    
    print(f"  Transactions: {len(transactions_only)}")
    print(f"  Ground truth records: {len(ground_truth_only)}")
    print()
    
    # Step 7: Validate totals
    print("Step 7: Validating totals...")
    actual_total = len(transactions_only)
    actual_normal = len([gt for gt in ground_truth_only if gt.ground_truth_label == 0])
    actual_suspicious = len([gt for gt in ground_truth_only if gt.ground_truth_label == 1])
    
    print(f"  Total transactions: {actual_total} (expected: {TOTAL_TRANSACTIONS})")
    print(f"  Normal: {actual_normal} (expected: {NORMAL_COUNT})")
    print(f"  Suspicious: {actual_suspicious} (expected: {SUSPICIOUS_COUNT})")
    
    if actual_total != TOTAL_TRANSACTIONS:
        print(f"  ERROR: Transaction count mismatch!")
        return False
    if actual_normal != NORMAL_COUNT:
        print(f"  ERROR: Normal count mismatch!")
        return False
    if actual_suspicious != SUSPICIOUS_COUNT:
        print(f"  ERROR: Suspicious count mismatch!")
        return False
    
    print("  All totals validated successfully")
    print()
    
    # Step 8: Create output directory
    print("Step 8: Creating output directory...")
    output_dir = Path("data") / DATASET_VERSION
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Output directory: {output_dir}")
    print()
    
    # Step 9: Export transactions
    print("Step 9: Exporting transactions...")
    transactions_file = output_dir / "transactions.csv"
    with open(transactions_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "transaction_id", "event_timestamp", "event_sequence",
            "sender_wallet", "receiver_wallet", "amount",
            "transaction_type", "channel", "agent_id", "partition"
        ])
        for tx in transactions_only:
            writer.writerow([
                tx.transaction_id,
                tx.event_timestamp.isoformat(),
                tx.event_sequence,
                tx.sender_wallet,
                tx.receiver_wallet,
                tx.amount,
                tx.transaction_type,
                tx.channel,
                tx.agent_id,
                tx.partition
            ])
    print(f"  Exported to {transactions_file}")
    print()
    
    # Step 10: Export ground truth
    print("Step 10: Exporting ground truth...")
    ground_truth_file = output_dir / "ground_truth.json"
    ground_truth_data = []
    for gt in ground_truth_only:
        ground_truth_data.append({
            "transaction_id": gt.transaction_id,
            "ground_truth_label": gt.ground_truth_label,
            "scenario_id": gt.scenario_id,
            "scenario_type": gt.scenario_type,
            "scenario_category": gt.scenario_category,
            "signal_strength": gt.signal_strength,
            "scenario_source": gt.scenario_source,
            "affected_wallets": gt.affected_wallets,
            "affected_agent": gt.affected_agent
        })
    
    with open(ground_truth_file, 'w') as f:
        json.dump(ground_truth_data, f, indent=2)
    print(f"  Exported to {ground_truth_file}")
    print()
    
    # Step 11: Export entity metadata
    print("Step 11: Exporting entity metadata...")
    entity_metadata_file = output_dir / "entity_metadata.json"
    entity_data = {
        "wallets": [
            {
                "wallet_id": w.wallet_id,
                "customer_id": w.customer_id,
                "partition": w.partition,
                "wealth_segment": w.wealth_segment
            }
            for w in wallets.values()
        ],
        "agents": [
            {
                "agent_id": a.agent_id,
                "partition": a.partition
            }
            for a in agents.values()
        ]
    }
    
    with open(entity_metadata_file, 'w') as f:
        json.dump(entity_data, f, indent=2)
    print(f"  Exported to {entity_metadata_file}")
    print()
    
    # Step 12: Create generation manifest
    print("Step 12: Creating generation manifest...")
    manifest_file = output_dir / "generation_manifest.json"
    manifest = {
        "dataset_version": DATASET_VERSION,
        "generation_timestamp": datetime.now(timezone.utc).isoformat(),
        "random_seed": RANDOM_SEED,
        "master_seed": MASTER_SEED,
        "stage10b_specification_version": "2026-09-14",
        "stage10c_specification_version": "2026-09-14",
        "synthetic_threshold_version": THRESHOLD_VERSION,
        "synthetic_threshold_value": SYNTHETIC_REPORTING_THRESHOLD,
        "total_transactions": actual_total,
        "normal_count": actual_normal,
        "suspicious_count": actual_suspicious,
        "total_wallets": len(wallets),
        "total_agents": len(agents),
        "partition_allocation": {
            "train": {"transactions": TRAIN_TX, "wallets": TRAIN_WALLETS, "agents": TRAIN_AGENTS},
            "validation": {"transactions": VAL_TX, "wallets": VAL_WALLETS, "agents": VAL_AGENTS},
            "final_test": {"transactions": TEST_TX, "wallets": TEST_WALLETS, "agents": TEST_AGENTS},
            "independent": {"transactions": INDEPENDENT_TX, "wallets": INDEPENDENT_WALLETS, "agents": INDEPENDENT_AGENTS}
        },
        "channel_allocation": {
            "agent_mediated": AGENT_MEDIATED_COUNT,
            "direct_p2p": DIRECT_P2P_COUNT
        },
        "suspicious_domain_allocation": {
            "structuring": STRUCTURING_COUNT,
            "network": NETWORK_COUNT,
            "agent": AGENT_COUNT
        },
        "scenario_families": 12,
        "max_tx_per_family": MAX_TX_PER_FAMILY
    }
    
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"  Exported to {manifest_file}")
    print()
    
    print("=" * 80)
    print("DATASET GENERATION COMPLETE")
    print("=" * 80)
    print()
    print("Generated files:")
    print(f"  1. {transactions_file}")
    print(f"  2. {ground_truth_file}")
    print(f"  3. {entity_metadata_file}")
    print(f"  4. {manifest_file}")
    print()
    print("Next steps:")
    print("  1. Run validation checks")
    print("  2. Verify feature compatibility")
    print("  3. Proceed to feature extraction (Stage 12)")
    print()
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("Generation failed!")
        exit(1)
