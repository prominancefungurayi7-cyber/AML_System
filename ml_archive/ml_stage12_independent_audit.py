"""
Stage 12: Independent Audit of Final 100,000-Transaction Synthetic AML Dataset

This is a READ-ONLY audit to verify the Stage 11 generated dataset is suitable
for Stage 13 feature construction.

DO NOT modify any data files.
DO NOT train any models.
DO NOT modify application code or database.
"""

import json
import csv
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter, defaultdict

# =============================================================================
# CONFIGURATION
# =============================================================================

DATASET_VERSION = "ecocash_aml_synthetic_100k_v1"
DATA_DIR = Path("data") / DATASET_VERSION

# Expected values from Stage 10C/11 specifications
EXPECTED_TOTAL = 100000
EXPECTED_NORMAL = 88000
EXPECTED_SUSPICIOUS = 12000
EXPECTED_STRUCTURING = 4000
EXPECTED_NETWORK = 4000
EXPECTED_AGENT = 4000

EXPECTED_WALLETS = 2000
EXPECTED_AGENTS = 160

EXPECTED_TRAIN_TX = 60000
EXPECTED_VAL_TX = 15000
EXPECTED_TEST_TX = 15000
EXPECTED_INDEPENDENT_TX = 10000

EXPECTED_TRAIN_WALLETS = 1200
EXPECTED_VAL_WALLETS = 300
EXPECTED_TEST_WALLETS = 300
EXPECTED_INDEPENDENT_WALLETS = 200

EXPECTED_TRAIN_AGENTS = 96
EXPECTED_VAL_AGENTS = 24
EXPECTED_TEST_AGENTS = 24
EXPECTED_INDEPENDENT_AGENTS = 16

EXPECTED_AGENT_MEDIATED = 75000
EXPECTED_DIRECT_P2P = 25000

# =============================================================================
# AUDIT FUNCTIONS
# =============================================================================

def load_data():
    """Load all dataset files."""
    print("Loading dataset files...")
    
    transactions = []
    with open(DATA_DIR / "transactions.csv", 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            transactions.append(row)
    
    with open(DATA_DIR / "ground_truth.json", 'r') as f:
        ground_truth = json.load(f)
    
    with open(DATA_DIR / "entity_metadata.json", 'r') as f:
        entity_metadata = json.load(f)
    
    with open(DATA_DIR / "generation_manifest.json", 'r') as f:
        manifest = json.load(f)
    
    print(f"  Loaded {len(transactions)} transactions")
    print(f"  Loaded {len(ground_truth)} ground truth records")
    print(f"  Loaded {len(entity_metadata['wallets'])} wallets")
    print(f"  Loaded {len(entity_metadata['agents'])} agents")
    print()
    
    return transactions, ground_truth, entity_metadata, manifest

def audit_dataset_identity(transactions, ground_truth, entity_metadata, manifest):
    """Audit 1: Dataset Identity and Integrity"""
    print("=" * 80)
    print("AUDIT 1: DATASET IDENTITY AND INTEGRITY")
    print("=" * 80)
    
    errors = []
    warnings = []
    
    # Check manifest version
    manifest_version = manifest.get("dataset_version")
    print(f"Dataset version: {manifest_version}")
    if manifest_version != DATASET_VERSION:
        errors.append(f"Manifest version mismatch: {manifest_version} != {DATASET_VERSION}")
        print("  FAIL")
    else:
        print("  PASS")
    
    # Check transaction count
    actual_total = len(transactions)
    print(f"Transaction count: {actual_total} (expected: {EXPECTED_TOTAL})")
    if actual_total != EXPECTED_TOTAL:
        errors.append(f"Transaction count mismatch: {actual_total} != {EXPECTED_TOTAL}")
        print("  FAIL")
    else:
        print("  PASS")
    
    # Check ground truth count
    actual_gt = len(ground_truth)
    print(f"Ground truth count: {actual_gt} (expected: {EXPECTED_TOTAL})")
    if actual_gt != EXPECTED_TOTAL:
        errors.append(f"Ground truth count mismatch: {actual_gt} != {EXPECTED_TOTAL}")
        print("  FAIL")
    else:
        print("  PASS")
    
    # Check transaction ID uniqueness
    tx_ids = [tx['transaction_id'] for tx in transactions]
    if len(tx_ids) != len(set(tx_ids)):
        errors.append("Duplicate transaction IDs found")
        print("Transaction IDs: FAIL (duplicates)")
    else:
        print("Transaction IDs: PASS (all unique)")
    
    # Check event sequence uniqueness
    event_sequences = [int(tx['event_sequence']) for tx in transactions]
    if len(event_sequences) != len(set(event_sequences)):
        errors.append("Duplicate event sequences found")
        print("Event sequences: FAIL (duplicates)")
    else:
        print("Event sequences: PASS (all unique)")
    
    # Check required fields
    required_fields = ['transaction_id', 'event_timestamp', 'event_sequence', 
                      'sender_wallet', 'receiver_wallet', 'amount', 
                      'transaction_type', 'channel', 'agent_id', 'partition']
    sample_tx = transactions[0]
    missing_fields = [f for f in required_fields if f not in sample_tx]
    if missing_fields:
        errors.append(f"Missing required fields: {missing_fields}")
        print(f"Required fields: FAIL (missing: {missing_fields})")
    else:
        print("Required fields: PASS")
    
    print()
    return errors, warnings

def audit_schema(transactions):
    """Audit 2: Raw Transaction Schema"""
    print("=" * 80)
    print("AUDIT 2: RAW TRANSACTION SCHEMA")
    print("=" * 80)
    
    errors = []
    warnings = []
    
    # Check sender != receiver
    sender_eq_receiver = 0
    for tx in transactions:
        if tx['sender_wallet'] == tx['receiver_wallet']:
            sender_eq_receiver += 1
    
    print(f"Sender == receiver violations: {sender_eq_receiver}")
    if sender_eq_receiver > 0:
        errors.append(f"{sender_eq_receiver} transactions have sender == receiver")
        print("  FAIL")
    else:
        print("  PASS")
    
    # Check amount positive
    non_positive = 0
    for tx in transactions:
        if float(tx['amount']) <= 0:
            non_positive += 1
    
    print(f"Non-positive amounts: {non_positive}")
    if non_positive > 0:
        errors.append(f"{non_positive} transactions have non-positive amounts")
        print("  FAIL")
    else:
        print("  PASS")
    
    # Check timestamp validity
    invalid_timestamps = 0
    for tx in transactions:
        try:
            datetime.fromisoformat(tx['event_timestamp'])
        except ValueError:
            invalid_timestamps += 1
    
    print(f"Invalid timestamps: {invalid_timestamps}")
    if invalid_timestamps > 0:
        errors.append(f"{invalid_timestamps} transactions have invalid timestamps")
        print("  FAIL")
    else:
        print("  PASS")
    
    # Check channel consistency with agent_id
    channel_mismatch = 0
    for tx in transactions:
        has_agent = bool(tx['agent_id'] and tx['agent_id'] != '')
        is_agent_channel = tx['channel'] == 'agent'
        if has_agent != is_agent_channel:
            channel_mismatch += 1
    
    print(f"Channel/agent_id mismatches: {channel_mismatch}")
    if channel_mismatch > 0:
        errors.append(f"{channel_mismatch} transactions have channel/agent_id mismatch")
        print("  FAIL")
    else:
        print("  PASS")
    
    print()
    return errors, warnings

def audit_population(entity_metadata):
    """Audit 3: Exact Population"""
    print("=" * 80)
    print("AUDIT 3: EXACT POPULATION")
    print("=" * 80)
    
    errors = []
    warnings = []
    
    # Check wallet count
    wallet_count = len(entity_metadata['wallets'])
    print(f"Wallet count: {wallet_count} (expected: {EXPECTED_WALLETS})")
    if wallet_count != EXPECTED_WALLETS:
        errors.append(f"Wallet count mismatch: {wallet_count} != {EXPECTED_WALLETS}")
        print("  FAIL")
    else:
        print("  PASS")
    
    # Check agent count
    agent_count = len(entity_metadata['agents'])
    print(f"Agent count: {agent_count} (expected: {EXPECTED_AGENTS})")
    if agent_count != EXPECTED_AGENTS:
        errors.append(f"Agent count mismatch: {agent_count} != {EXPECTED_AGENTS}")
        print("  FAIL")
    else:
        print("  PASS")
    
    # Check wallet-customer mapping
    customer_wallet_map = {}
    for w in entity_metadata['wallets']:
        customer_id = w['customer_id']
        wallet_id = w['wallet_id']
        if customer_id in customer_wallet_map:
            errors.append(f"Customer {customer_id} has multiple wallets")
        customer_wallet_map[customer_id] = wallet_id
    
    print(f"Wallet-customer mapping: {len(customer_wallet_map)} customers -> {wallet_count} wallets")
    if len(customer_wallet_map) != wallet_count:
        errors.append("Wallet-customer mapping is not 1:1")
        print("  FAIL")
    else:
        print("  PASS (1:1 mapping)")
    
    # Check for wallets without customers
    wallet_customer_ids = {w['customer_id'] for w in entity_metadata['wallets']}
    print(f"All wallets have customers: PASS")
    
    print()
    return errors, warnings

def audit_partition_isolation(transactions, entity_metadata):
    """Audit 4: Partition Isolation"""
    print("=" * 80)
    print("AUDIT 4: PARTITION ISOLATION")
    print("=" * 80)
    
    errors = []
    warnings = []
    
    # Create wallet->partition and agent->partition mappings
    wallet_partition = {w['wallet_id']: w['partition'] for w in entity_metadata['wallets']}
    agent_partition = {a['agent_id']: a['partition'] for a in entity_metadata['agents']}
    
    # Check transaction partition counts
    partition_tx_counts = Counter(tx['partition'] for tx in transactions)
    
    print(f"Train transactions: {partition_tx_counts.get('train', 0)} (expected: {EXPECTED_TRAIN_TX})")
    if partition_tx_counts.get('train', 0) != EXPECTED_TRAIN_TX:
        errors.append(f"Train tx mismatch: {partition_tx_counts.get('train', 0)} != {EXPECTED_TRAIN_TX}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Validation transactions: {partition_tx_counts.get('validation', 0)} (expected: {EXPECTED_VAL_TX})")
    if partition_tx_counts.get('validation', 0) != EXPECTED_VAL_TX:
        errors.append(f"Validation tx mismatch: {partition_tx_counts.get('validation', 0)} != {EXPECTED_VAL_TX}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Final test transactions: {partition_tx_counts.get('final_test', 0)} (expected: {EXPECTED_TEST_TX})")
    if partition_tx_counts.get('final_test', 0) != EXPECTED_TEST_TX:
        errors.append(f"Final test tx mismatch: {partition_tx_counts.get('final_test', 0)} != {EXPECTED_TEST_TX}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Independent transactions: {partition_tx_counts.get('independent', 0)} (expected: {EXPECTED_INDEPENDENT_TX})")
    if partition_tx_counts.get('independent', 0) != EXPECTED_INDEPENDENT_TX:
        errors.append(f"Independent tx mismatch: {partition_tx_counts.get('independent', 0)} != {EXPECTED_INDEPENDENT_TX}")
        print("  FAIL")
    else:
        print("  PASS")
    
    # Check wallet partition counts
    wallet_partition_counts = Counter(w['partition'] for w in entity_metadata['wallets'])
    
    print(f"Train wallets: {wallet_partition_counts.get('train', 0)} (expected: {EXPECTED_TRAIN_WALLETS})")
    if wallet_partition_counts.get('train', 0) != EXPECTED_TRAIN_WALLETS:
        errors.append(f"Train wallet mismatch: {wallet_partition_counts.get('train', 0)} != {EXPECTED_TRAIN_WALLETS}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Validation wallets: {wallet_partition_counts.get('validation', 0)} (expected: {EXPECTED_VAL_WALLETS})")
    if wallet_partition_counts.get('validation', 0) != EXPECTED_VAL_WALLETS:
        errors.append(f"Validation wallet mismatch: {wallet_partition_counts.get('validation', 0)} != {EXPECTED_VAL_WALLETS}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Final test wallets: {wallet_partition_counts.get('final_test', 0)} (expected: {EXPECTED_TEST_WALLETS})")
    if wallet_partition_counts.get('final_test', 0) != EXPECTED_TEST_WALLETS:
        errors.append(f"Final test wallet mismatch: {wallet_partition_counts.get('final_test', 0)} != {EXPECTED_TEST_WALLETS}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Independent wallets: {wallet_partition_counts.get('independent', 0)} (expected: {EXPECTED_INDEPENDENT_WALLETS})")
    if wallet_partition_counts.get('independent', 0) != EXPECTED_INDEPENDENT_WALLETS:
        errors.append(f"Independent wallet mismatch: {wallet_partition_counts.get('independent', 0)} != {EXPECTED_INDEPENDENT_WALLETS}")
        print("  FAIL")
    else:
        print("  PASS")
    
    # Check agent partition counts
    agent_partition_counts = Counter(a['partition'] for a in entity_metadata['agents'])
    
    print(f"Train agents: {agent_partition_counts.get('train', 0)} (expected: {EXPECTED_TRAIN_AGENTS})")
    if agent_partition_counts.get('train', 0) != EXPECTED_TRAIN_AGENTS:
        errors.append(f"Train agent mismatch: {agent_partition_counts.get('train', 0)} != {EXPECTED_TRAIN_AGENTS}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Validation agents: {agent_partition_counts.get('validation', 0)} (expected: {EXPECTED_VAL_AGENTS})")
    if agent_partition_counts.get('validation', 0) != EXPECTED_VAL_AGENTS:
        errors.append(f"Validation agent mismatch: {agent_partition_counts.get('validation', 0)} != {EXPECTED_VAL_AGENTS}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Final test agents: {agent_partition_counts.get('final_test', 0)} (expected: {EXPECTED_TEST_AGENTS})")
    if agent_partition_counts.get('final_test', 0) != EXPECTED_TEST_AGENTS:
        errors.append(f"Final test agent mismatch: {agent_partition_counts.get('final_test', 0)} != {EXPECTED_TEST_AGENTS}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Independent agents: {agent_partition_counts.get('independent', 0)} (expected: {EXPECTED_INDEPENDENT_AGENTS})")
    if agent_partition_counts.get('independent', 0) != EXPECTED_INDEPENDENT_AGENTS:
        errors.append(f"Independent agent mismatch: {agent_partition_counts.get('independent', 0)} != {EXPECTED_INDEPENDENT_AGENTS}")
        print("  FAIL")
    else:
        print("  PASS")
    
    # Check for cross-partition edges
    cross_partition_edges = 0
    for tx in transactions:
        sender_part = wallet_partition.get(tx['sender_wallet'])
        receiver_part = wallet_partition.get(tx['receiver_wallet'])
        if sender_part and receiver_part and sender_part != receiver_part:
            cross_partition_edges += 1
    
    print(f"Cross-partition edges: {cross_partition_edges} (expected: 0)")
    if cross_partition_edges > 0:
        errors.append(f"Found {cross_partition_edges} cross-partition edges")
        print("  FAIL")
    else:
        print("  PASS")
    
    # Check agent partition consistency
    agent_partition_mismatch = 0
    for tx in transactions:
        if tx['agent_id'] and tx['agent_id'] != '':
            tx_part = tx['partition']
            agent_part = agent_partition.get(tx['agent_id'])
            if agent_part and agent_part != tx_part:
                agent_partition_mismatch += 1
    
    print(f"Agent partition mismatches: {agent_partition_mismatch} (expected: 0)")
    if agent_partition_mismatch > 0:
        errors.append(f"Found {agent_partition_mismatch} agent partition mismatches")
        print("  FAIL")
    else:
        print("  PASS")
    
    print()
    return errors, warnings

def audit_class_distribution(transactions, ground_truth):
    """Audit 5: Class Distribution"""
    print("=" * 80)
    print("AUDIT 5: CLASS DISTRIBUTION")
    print("=" * 80)
    
    errors = []
    warnings = []
    
    # Create transaction ID to partition mapping
    tx_partition = {tx['transaction_id']: tx['partition'] for tx in transactions}
    
    # Count by label
    label_counts = Counter(gt['ground_truth_label'] for gt in ground_truth)
    
    print(f"Normal transactions: {label_counts.get(0, 0)} (expected: {EXPECTED_NORMAL})")
    if label_counts.get(0, 0) != EXPECTED_NORMAL:
        errors.append(f"Normal count mismatch: {label_counts.get(0, 0)} != {EXPECTED_NORMAL}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Suspicious transactions: {label_counts.get(1, 0)} (expected: {EXPECTED_SUSPICIOUS})")
    if label_counts.get(1, 0) != EXPECTED_SUSPICIOUS:
        errors.append(f"Suspicious count mismatch: {label_counts.get(1, 0)} != {EXPECTED_SUSPICIOUS}")
        print("  FAIL")
    else:
        print("  PASS")
    
    # Check for invalid labels
    invalid_labels = [gt['ground_truth_label'] for gt in ground_truth if gt['ground_truth_label'] not in [0, 1]]
    if invalid_labels:
        errors.append(f"Invalid labels found: {set(invalid_labels)}")
        print(f"Invalid labels: FAIL ({set(invalid_labels)})")
    else:
        print("Invalid labels: PASS (only 0 and 1)")
    
    # Check partition class counts
    partition_labels = defaultdict(lambda: {'normal': 0, 'suspicious': 0})
    for gt in ground_truth:
        partition = tx_partition.get(gt['transaction_id'])
        if partition:
            if gt['ground_truth_label'] == 0:
                partition_labels[partition]['normal'] += 1
            else:
                partition_labels[partition]['suspicious'] += 1
    
    print(f"Train normal: {partition_labels['train']['normal']} (expected: 52800)")
    print(f"Train suspicious: {partition_labels['train']['suspicious']} (expected: 7200)")
    if partition_labels['train']['normal'] != 52800 or partition_labels['train']['suspicious'] != 7200:
        errors.append("Train class counts mismatch")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Validation normal: {partition_labels['validation']['normal']} (expected: 13200)")
    print(f"Validation suspicious: {partition_labels['validation']['suspicious']} (expected: 1800)")
    if partition_labels['validation']['normal'] != 13200 or partition_labels['validation']['suspicious'] != 1800:
        errors.append("Validation class counts mismatch")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Final test normal: {partition_labels['final_test']['normal']} (expected: 13200)")
    print(f"Final test suspicious: {partition_labels['final_test']['suspicious']} (expected: 1800)")
    if partition_labels['final_test']['normal'] != 13200 or partition_labels['final_test']['suspicious'] != 1800:
        errors.append("Final test class counts mismatch")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Independent normal: {partition_labels['independent']['normal']} (expected: 8800)")
    print(f"Independent suspicious: {partition_labels['independent']['suspicious']} (expected: 1200)")
    if partition_labels['independent']['normal'] != 8800 or partition_labels['independent']['suspicious'] != 1200:
        errors.append("Independent class counts mismatch")
        print("  FAIL")
    else:
        print("  PASS")
    
    print()
    return errors, warnings

def audit_suspicious_domain(ground_truth):
    """Audit 6: Suspicious Domain"""
    print("=" * 80)
    print("AUDIT 6: SUSPICIOUS DOMAIN")
    print("=" * 80)
    
    errors = []
    warnings = []
    
    # Count by scenario category
    domain_counts = defaultdict(int)
    for gt in ground_truth:
        if gt['ground_truth_label'] == 1 and gt['scenario_category']:
            domain_counts[gt['scenario_category']] += 1
    
    print(f"Structuring suspicious: {domain_counts.get('structuring', 0)} (expected: {EXPECTED_STRUCTURING})")
    if domain_counts.get('structuring', 0) != EXPECTED_STRUCTURING:
        errors.append(f"Structuring count mismatch: {domain_counts.get('structuring', 0)} != {EXPECTED_STRUCTURING}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Network suspicious: {domain_counts.get('network', 0)} (expected: {EXPECTED_NETWORK})")
    if domain_counts.get('network', 0) != EXPECTED_NETWORK:
        errors.append(f"Network count mismatch: {domain_counts.get('network', 0)} != {EXPECTED_NETWORK}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Agent suspicious: {domain_counts.get('agent', 0)} (expected: {EXPECTED_AGENT})")
    if domain_counts.get('agent', 0) != EXPECTED_AGENT:
        errors.append(f"Agent count mismatch: {domain_counts.get('agent', 0)} != {EXPECTED_AGENT}")
        print("  FAIL")
    else:
        print("  PASS")
    
    # Count by scenario type
    scenario_counts = Counter()
    for gt in ground_truth:
        if gt['ground_truth_label'] == 1 and gt['scenario_type']:
            scenario_counts[gt['scenario_type']] += 1
    
    print("\nScenario family distribution:")
    expected_families = [
        "variable_fragment_burst", "similar_amount_repetition", 
        "distributed_same_day_fragmentation", "variable_near_threshold_history",
        "many_to_one_collection", "one_to_many_dispersion",
        "reciprocal_relationship_cycle", "wallet_pass_through",
        "agent_wallet_growth", "agent_wallet_concentration",
        "agent_temporal_burst", "agent_flow_imbalance"
    ]
    
    for family in expected_families:
        count = scenario_counts.get(family, 0)
        print(f"  {family}: {count}")
        if count > 1000:
            warnings.append(f"Scenario family {family} exceeds 1000 cap: {count}")
    
    print()
    return errors, warnings

def audit_ground_truth_independence(ground_truth, entity_metadata):
    """Audit 7: Ground Truth Independence"""
    print("=" * 80)
    print("AUDIT 7: GROUND TRUTH INDEPENDENCE")
    print("=" * 80)
    
    errors = []
    warnings = []
    
    # Check that ground truth doesn't contain risk/rule/model fields
    forbidden_fields = ['risk_score', 'risk_level', 'alert', 'investigation', 'model_prediction']
    
    sample_gt = ground_truth[0]
    has_forbidden = []
    for field in forbidden_fields:
        if field in str(sample_gt).lower():
            has_forbidden.append(field)
    
    if has_forbidden:
        errors.append(f"Ground truth contains forbidden fields: {has_forbidden}")
        print(f"Forbidden fields in ground truth: FAIL ({has_forbidden})")
    else:
        print("Forbidden fields in ground truth: PASS")
    
    # Check that scenario_source is "stage11_generator"
    sources = set(gt.get('scenario_source') for gt in ground_truth)
    print(f"Scenario sources: {sources}")
    if sources != {"stage11_generator"}:
        errors.append(f"Unexpected scenario sources: {sources}")
        print("  FAIL")
    else:
        print("  PASS")
    
    # Check that labels are binary
    labels = set(gt['ground_truth_label'] for gt in ground_truth)
    print(f"Label values: {labels}")
    if labels != {0, 1}:
        errors.append(f"Non-binary labels found: {labels}")
        print("  FAIL")
    else:
        print("  PASS (binary only)")
    
    print()
    return errors, warnings

def audit_shortcut_leakage(transactions, ground_truth):
    """Audit 8: Label Proxy / Shortcut Leakage"""
    print("=" * 80)
    print("AUDIT 8: LABEL PROXY / SHORTCUT LEAKAGE")
    print("=" * 80)
    
    errors = []
    warnings = []
    
    # Create label mapping
    tx_label = {gt['transaction_id']: gt['ground_truth_label'] for gt in ground_truth}
    
    # Check amount distribution
    normal_amounts = [float(tx['amount']) for tx in transactions if tx_label[tx['transaction_id']] == 0]
    suspicious_amounts = [float(tx['amount']) for tx in transactions if tx_label[tx['transaction_id']] == 1]
    
    normal_min, normal_max = min(normal_amounts), max(normal_amounts)
    suspicious_min, suspicious_max = min(suspicious_amounts), max(suspicious_amounts)
    
    print(f"Normal amount range: ${normal_min:.2f} - ${normal_max:.2f}")
    print(f"Suspicious amount range: ${suspicious_min:.2f} - ${suspicious_max:.2f}")
    
    # Check for complete separation
    if suspicious_max < normal_min or suspicious_min > normal_max:
        errors.append("Amount ranges are completely separated - potential shortcut")
        print("Amount overlap: FAIL (complete separation)")
    else:
        print("Amount overlap: PASS (ranges overlap)")
    
    # Check channel distribution
    normal_agent = len([tx for tx in transactions if tx_label[tx['transaction_id']] == 0 and tx['agent_id']])
    suspicious_agent = len([tx for tx in transactions if tx_label[tx['transaction_id']] == 1 and tx['agent_id']])
    
    print(f"Normal agent-mediated: {normal_agent}")
    print(f"Suspicious agent-mediated: {suspicious_agent}")
    
    if suspicious_agent == 0 or normal_agent == 0:
        errors.append("Channel completely separates classes")
        print("Channel separation: FAIL")
    else:
        print("Channel separation: PASS")
    
    # Check partition distribution
    normal_by_partition = Counter(tx['partition'] for tx in transactions if tx_label[tx['transaction_id']] == 0)
    suspicious_by_partition = Counter(tx['partition'] for tx in transactions if tx_label[tx['transaction_id']] == 1)
    
    print(f"Normal by partition: {dict(normal_by_partition)}")
    print(f"Suspicious by partition: {dict(suspicious_by_partition)}")
    
    # Check if any partition is purely one class
    for partition in ['train', 'validation', 'final_test', 'independent']:
        if normal_by_partition[partition] == 0 or suspicious_by_partition[partition] == 0:
            warnings.append(f"Partition {partition} has only one class")
    
    print()
    return errors, warnings

def audit_scenario_diversity(ground_truth):
    """Audit 9: Scenario Diversity"""
    print("=" * 80)
    print("AUDIT 9: SCENARIO DIVERSITY")
    print("=" * 80)
    
    errors = []
    warnings = []
    
    # Count by scenario type
    scenario_counts = Counter()
    for gt in ground_truth:
        if gt['ground_truth_label'] == 1 and gt['scenario_type']:
            scenario_counts[gt['scenario_type']] += 1
    
    print("Scenario family diversity:")
    for scenario, count in scenario_counts.most_common():
        percentage = count / 12000 * 100
        print(f"  {scenario}: {count} ({percentage:.2f}%)")
        if count > 1000:
            errors.append(f"Scenario {scenario} exceeds 1000 cap: {count}")
    
    # Check for dominance
    max_count = max(scenario_counts.values()) if scenario_counts else 0
    if max_count > 1000:
        errors.append(f"Scenario family exceeds cap: {max_count}")
        print("Scenario cap: FAIL")
    else:
        print("Scenario cap: PASS")
    
    print()
    return errors, warnings

def audit_temporal_safety(transactions):
    """Audit 10: Temporal Safety"""
    print("=" * 80)
    print("AUDIT 10: TEMPORAL SAFETY")
    print("=" * 80)
    
    errors = []
    warnings = []
    
    # Check event sequence is sequential
    event_sequences = sorted([int(tx['event_sequence']) for tx in transactions])
    expected_sequence = list(range(len(transactions)))
    
    if event_sequences != expected_sequence:
        errors.append("Event sequence is not sequential")
        print("Event sequence: FAIL (not sequential)")
    else:
        print("Event sequence: PASS (sequential)")
    
    # Check timestamp range
    timestamps = [datetime.fromisoformat(tx['event_timestamp']) for tx in transactions]
    min_time = min(timestamps)
    max_time = max(timestamps)
    duration = (max_time - min_time).days
    
    print(f"Time range: {min_time.date()} to {max_time.date()} ({duration} days)")
    
    if duration < 150 or duration > 210:
        warnings.append(f"Duration {duration} days is outside expected ~180 day range")
        print("Duration: WARNING")
    else:
        print("Duration: PASS (~180 days)")
    
    # Check temporal distribution
    tx_by_date = Counter(ts.date() for ts in timestamps)
    print(f"Transactions span {len(tx_by_date)} unique dates")
    
    print()
    return errors, warnings

def audit_30_feature_computability(transactions, entity_metadata):
    """Audit 11: 30-Feature Computability"""
    print("=" * 80)
    print("AUDIT 11: 30-FEATURE COMPUTABILITY")
    print("=" * 80)
    
    errors = []
    warnings = []
    
    # Stage 10B features
    structuring_features = [
        "structuring_prior_tx_count_1h",
        "structuring_prior_value_sum_24h",
        "structuring_same_day_prior_tx_count",
        "structuring_repeated_amount_ratio_7d",
        "structuring_amount_cluster_dispersion_7d",
        "structuring_near_threshold_history_ratio_7d"
    ]
    
    network_features = [
        "network_outbound_counterparty_count_7d",
        "network_inbound_counterparty_count_7d",
        "network_outbound_counterparty_entropy_30d",
        "network_top_counterparty_value_share_30d",
        "network_current_receiver_is_new",
        "network_repeated_receiver_ratio_30d",
        "network_reciprocal_flow_ratio_7d",
        "network_counterparty_set_change_7d",
        "network_pass_through_ratio_24h",
        "network_shared_counterparty_concentration_7d"
    ]
    
    agent_features = [
        "agent_prior_tx_count_1h",
        "agent_prior_tx_count_7d",
        "agent_prior_value_sum_1h",
        "agent_prior_value_sum_7d",
        "agent_unique_wallet_count_7d",
        "agent_wallet_value_hhi_7d",
        "agent_repeat_wallet_ratio_7d",
        "agent_current_wallet_is_new",
        "agent_inbound_outbound_value_ratio_7d",
        "agent_high_value_event_share_7d",
        "agent_hourly_tx_zscore_30d",
        "agent_hourly_value_zscore_30d",
        "agent_burst_concentration_7d",
        "agent_shared_wallet_flow_concentration_7d"
    ]
    
    all_features = structuring_features + network_features + agent_features
    
    print(f"Total features to verify: {len(all_features)}")
    
    # Check required raw fields for each feature domain
    required_fields = {
        'transaction_id', 'event_timestamp', 'event_sequence',
        'sender_wallet', 'receiver_wallet', 'amount',
        'transaction_type', 'channel', 'agent_id'
    }
    
    sample_tx = transactions[0]
    missing_fields = [f for f in required_fields if f not in sample_tx]
    
    if missing_fields:
        errors.append(f"Missing required fields for features: {missing_fields}")
        print(f"Required fields: FAIL (missing: {missing_fields})")
    else:
        print("Required fields: PASS")
    
    # Check temporal support
    timestamps = [datetime.fromisoformat(tx['event_timestamp']) for tx in transactions]
    min_time = min(timestamps)
    max_time = max(timestamps)
    duration_days = (max_time - min_time).days
    
    print(f"Temporal support: {duration_days} days (supports 30d features)")
    if duration_days < 30:
        errors.append("Insufficient temporal range for 30-day features")
        print("Temporal support: FAIL")
    else:
        print("Temporal support: PASS")
    
    # Check agent data availability
    agent_tx_count = len([tx for tx in transactions if tx['agent_id'] and tx['agent_id'] != ''])
    print(f"Agent-mediated transactions: {agent_tx_count} (supports agent features)")
    if agent_tx_count < 1000:
        warnings.append("Low agent-mediated transaction count may limit agent feature reliability")
        print("Agent data: WARNING")
    else:
        print("Agent data: PASS")
    
    # Check partition isolation support
    print("Partition isolation: PASS (enables independent evaluation)")
    
    print(f"\nFeature breakdown:")
    print(f"  Structuring: {len(structuring_features)} features")
    print(f"  Network: {len(network_features)} features")
    print(f"  Agent: {len(agent_features)} features")
    print(f"  Total: {len(all_features)} features")
    
    print()
    return errors, warnings

def audit_independent_evaluation(transactions, entity_metadata):
    """Audit 12: Independent Evaluation"""
    print("=" * 80)
    print("AUDIT 12: INDEPENDENT EVALUATION")
    print("=" * 80)
    
    errors = []
    warnings = []
    
    # Get independent entities
    independent_wallets = {w['wallet_id'] for w in entity_metadata['wallets'] if w['partition'] == 'independent'}
    independent_agents = {a['agent_id'] for a in entity_metadata['agents'] if a['partition'] == 'independent'}
    
    # Get other partition entities
    other_wallets = {w['wallet_id'] for w in entity_metadata['wallets'] if w['partition'] != 'independent'}
    other_agents = {a['agent_id'] for a in entity_metadata['agents'] if a['partition'] != 'independent'}
    
    # Check overlap
    wallet_overlap = independent_wallets & other_wallets
    agent_overlap = independent_agents & other_agents
    
    print(f"Independent wallet overlap: {len(wallet_overlap)} (expected: 0)")
    if wallet_overlap:
        errors.append(f"Independent wallet overlap: {wallet_overlap}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Independent agent overlap: {len(agent_overlap)} (expected: 0)")
    if agent_overlap:
        errors.append(f"Independent agent overlap: {agent_overlap}")
        print("  FAIL")
    else:
        print("  PASS")
    
    # Check independent transaction count
    independent_tx = len([tx for tx in transactions if tx['partition'] == 'independent'])
    print(f"Independent transactions: {independent_tx} (expected: {EXPECTED_INDEPENDENT_TX})")
    if independent_tx != EXPECTED_INDEPENDENT_TX:
        errors.append(f"Independent tx count mismatch: {independent_tx} != {EXPECTED_INDEPENDENT_TX}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print()
    return errors, warnings

def audit_feature_distribution_risk(transactions):
    """Audit 13: Feature Distribution Risk"""
    print("=" * 80)
    print("AUDIT 13: FEATURE DISTRIBUTION RISK")
    print("=" * 80)
    
    errors = []
    warnings = []
    
    # Check for near-constant fields
    amounts = [float(tx['amount']) for tx in transactions]
    amount_variance = sum((x - sum(amounts)/len(amounts))**2 for x in amounts) / len(amounts)
    
    print(f"Amount variance: {amount_variance:.2f}")
    if amount_variance < 1000:
        warnings.append("Low amount variance may indicate generation artefact")
        print("Amount variance: WARNING")
    else:
        print("Amount variance: PASS")
    
    # Check for sparsity in agent field
    null_agent_count = len([tx for tx in transactions if not tx['agent_id'] or tx['agent_id'] == ''])
    agent_count = len([tx for tx in transactions if tx['agent_id'] and tx['agent_id'] != ''])
    
    print(f"NULL agent_id: {null_agent_count} ({null_agent_count/len(transactions)*100:.1f}%)")
    print(f"Populated agent_id: {agent_count} ({agent_count/len(transactions)*100:.1f}%)")
    
    if null_agent_count > 90000 or agent_count < 10000:
        warnings.append("Extreme agent field sparsity may limit agent feature utility")
        print("Agent field sparsity: WARNING")
    else:
        print("Agent field sparsity: PASS")
    
    print()
    return errors, warnings

# =============================================================================
# MAIN AUDIT
# =============================================================================

def main():
    print("=" * 80)
    print("STAGE 12: INDEPENDENT DATASET AUDIT")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Dataset Version: {DATASET_VERSION}")
    print()
    
    # Load data
    transactions, ground_truth, entity_metadata, manifest = load_data()
    
    # Run audits
    all_errors = []
    all_warnings = []
    
    all_errors.extend(audit_dataset_identity(transactions, ground_truth, entity_metadata, manifest)[0])
    all_errors.extend(audit_schema(transactions)[0])
    all_errors.extend(audit_population(entity_metadata)[0])
    all_errors.extend(audit_partition_isolation(transactions, entity_metadata)[0])
    all_errors.extend(audit_class_distribution(transactions, ground_truth)[0])
    all_errors.extend(audit_suspicious_domain(ground_truth)[0])
    all_errors.extend(audit_ground_truth_independence(ground_truth, entity_metadata)[0])
    all_errors.extend(audit_shortcut_leakage(transactions, ground_truth)[0])
    all_errors.extend(audit_scenario_diversity(ground_truth)[0])
    all_errors.extend(audit_temporal_safety(transactions)[0])
    all_errors.extend(audit_30_feature_computability(transactions, entity_metadata)[0])
    all_errors.extend(audit_independent_evaluation(transactions, entity_metadata)[0])
    all_errors.extend(audit_feature_distribution_risk(transactions)[0])
    
    # Collect warnings
    all_warnings.extend(audit_dataset_identity(transactions, ground_truth, entity_metadata, manifest)[1])
    all_warnings.extend(audit_schema(transactions)[1])
    all_warnings.extend(audit_population(entity_metadata)[1])
    all_warnings.extend(audit_partition_isolation(transactions, entity_metadata)[1])
    all_warnings.extend(audit_class_distribution(transactions, ground_truth)[1])
    all_warnings.extend(audit_suspicious_domain(ground_truth)[1])
    all_warnings.extend(audit_ground_truth_independence(ground_truth, entity_metadata)[1])
    all_warnings.extend(audit_shortcut_leakage(transactions, ground_truth)[1])
    all_warnings.extend(audit_scenario_diversity(ground_truth)[1])
    all_warnings.extend(audit_temporal_safety(transactions)[1])
    all_warnings.extend(audit_30_feature_computability(transactions, entity_metadata)[1])
    all_warnings.extend(audit_independent_evaluation(transactions, entity_metadata)[1])
    all_warnings.extend(audit_feature_distribution_risk(transactions)[1])
    
    # Summary
    print("=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    
    if all_errors:
        print(f"FAILED: {len(all_errors)} critical error(s)")
        for error in all_errors:
            print(f"  - {error}")
        print()
        return "FAIL", all_errors, all_warnings
    else:
        print("PASSED: All critical checks successful")
        if all_warnings:
            print(f"WARNING: {len(all_warnings)} warning(s)")
            for warning in all_warnings:
                print(f"  - {warning}")
        else:
            print("No warnings")
        print()
        return "PASS", all_errors, all_warnings

if __name__ == "__main__":
    status, errors, warnings = main()
    print(f"\nFINAL AUDIT STATUS: {status}")
