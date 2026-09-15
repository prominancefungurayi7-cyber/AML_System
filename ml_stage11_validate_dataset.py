"""
Stage 11: Dataset Validation Script

Performs comprehensive validation of the generated 100,000-transaction dataset
according to Stage 11 Step 28 requirements.
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

# Expected totals from Stage 10C
EXPECTED_TOTAL = 100000
EXPECTED_NORMAL = 88000
EXPECTED_SUSPICIOUS = 12000
EXPECTED_STRUCTURING = 4000
EXPECTED_NETWORK = 4000
EXPECTED_AGENT = 4000

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

EXPECTED_WALLETS = 2000
EXPECTED_AGENTS = 160

EXPECTED_AGENT_MEDIATED = 75000
EXPECTED_DIRECT_P2P = 25000

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def load_transactions():
    """Load transactions from CSV."""
    transactions = []
    with open(DATA_DIR / "transactions.csv", 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            transactions.append(row)
    return transactions

def load_ground_truth():
    """Load ground truth from JSON."""
    with open(DATA_DIR / "ground_truth.json", 'r') as f:
        return json.load(f)

def load_entity_metadata():
    """Load entity metadata from JSON."""
    with open(DATA_DIR / "entity_metadata.json", 'r') as f:
        return json.load(f)

def load_manifest():
    """Load generation manifest from JSON."""
    with open(DATA_DIR / "generation_manifest.json", 'r') as f:
        return json.load(f)

def validate_totals(transactions, ground_truth):
    """Validate total counts."""
    print("=" * 80)
    print("VALIDATION A: TOTALS")
    print("=" * 80)
    
    errors = []
    
    actual_total = len(transactions)
    actual_normal = len([gt for gt in ground_truth if gt['ground_truth_label'] == 0])
    actual_suspicious = len([gt for gt in ground_truth if gt['ground_truth_label'] == 1])
    
    print(f"Total transactions: {actual_total} (expected: {EXPECTED_TOTAL})")
    if actual_total != EXPECTED_TOTAL:
        errors.append(f"Total mismatch: {actual_total} != {EXPECTED_TOTAL}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Normal transactions: {actual_normal} (expected: {EXPECTED_NORMAL})")
    if actual_normal != EXPECTED_NORMAL:
        errors.append(f"Normal mismatch: {actual_normal} != {EXPECTED_NORMAL}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Suspicious transactions: {actual_suspicious} (expected: {EXPECTED_SUSPICIOUS})")
    if actual_suspicious != EXPECTED_SUSPICIOUS:
        errors.append(f"Suspicious mismatch: {actual_suspicious} != {EXPECTED_SUSPICIOUS}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print()
    return errors

def validate_class_distribution(ground_truth):
    """Validate class distribution."""
    print("=" * 80)
    print("VALIDATION B: CLASS DISTRIBUTION")
    print("=" * 80)
    
    errors = []
    
    # Count by domain
    domain_counts = defaultdict(int)
    for gt in ground_truth:
        if gt['ground_truth_label'] == 1 and gt['scenario_category']:
            domain_counts[gt['scenario_category']] += 1
    
    print(f"Structuring suspicious: {domain_counts.get('structuring', 0)} (expected: {EXPECTED_STRUCTURING})")
    if domain_counts.get('structuring', 0) != EXPECTED_STRUCTURING:
        errors.append(f"Structuring mismatch: {domain_counts.get('structuring', 0)} != {EXPECTED_STRUCTURING}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Network suspicious: {domain_counts.get('network', 0)} (expected: {EXPECTED_NETWORK})")
    if domain_counts.get('network', 0) != EXPECTED_NETWORK:
        errors.append(f"Network mismatch: {domain_counts.get('network', 0)} != {EXPECTED_NETWORK}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Agent suspicious: {domain_counts.get('agent', 0)} (expected: {EXPECTED_AGENT})")
    if domain_counts.get('agent', 0) != EXPECTED_AGENT:
        errors.append(f"Agent mismatch: {domain_counts.get('agent', 0)} != {EXPECTED_AGENT}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print()
    return errors

def validate_partitions(transactions, ground_truth, entity_metadata):
    """Validate partition allocation and isolation."""
    print("=" * 80)
    print("VALIDATION C: PARTITIONS")
    print("=" * 80)
    
    errors = []
    
    # Count transactions by partition
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
    
    # Count entities by partition
    wallet_partitions = Counter(w['partition'] for w in entity_metadata['wallets'])
    agent_partitions = Counter(a['partition'] for a in entity_metadata['agents'])
    
    print(f"Train wallets: {wallet_partitions.get('train', 0)} (expected: {EXPECTED_TRAIN_WALLETS})")
    if wallet_partitions.get('train', 0) != EXPECTED_TRAIN_WALLETS:
        errors.append(f"Train wallet mismatch: {wallet_partitions.get('train', 0)} != {EXPECTED_TRAIN_WALLETS}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Train agents: {agent_partitions.get('train', 0)} (expected: {EXPECTED_TRAIN_AGENTS})")
    if agent_partitions.get('train', 0) != EXPECTED_TRAIN_AGENTS:
        errors.append(f"Train agent mismatch: {agent_partitions.get('train', 0)} != {EXPECTED_TRAIN_AGENTS}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print()
    return errors

def validate_partition_class_counts(transactions, ground_truth):
    """Validate class counts within each partition."""
    print("=" * 80)
    print("VALIDATION D: PARTITION CLASS COUNTS")
    print("=" * 80)
    
    errors = []
    
    # Create transaction ID to partition mapping
    tx_partition = {tx['transaction_id']: tx['partition'] for tx in transactions}
    
    # Count by partition and label
    partition_labels = defaultdict(lambda: {'normal': 0, 'suspicious': 0})
    for gt in ground_truth:
        partition = tx_partition.get(gt['transaction_id'])
        if partition:
            if gt['ground_truth_label'] == 0:
                partition_labels[partition]['normal'] += 1
            else:
                partition_labels[partition]['suspicious'] += 1
    
    # Train
    train_normal = partition_labels['train']['normal']
    train_suspicious = partition_labels['train']['suspicious']
    print(f"Train normal: {train_normal} (expected: 52800)")
    print(f"Train suspicious: {train_suspicious} (expected: 7200)")
    if train_normal != 52800 or train_suspicious != 7200:
        errors.append(f"Train class mismatch")
        print("  FAIL")
    else:
        print("  PASS")
    
    # Validation
    val_normal = partition_labels['validation']['normal']
    val_suspicious = partition_labels['validation']['suspicious']
    print(f"Validation normal: {val_normal} (expected: 13200)")
    print(f"Validation suspicious: {val_suspicious} (expected: 1800)")
    if val_normal != 13200 or val_suspicious != 1800:
        errors.append(f"Validation class mismatch")
        print("  FAIL")
    else:
        print("  PASS")
    
    # Final test
    test_normal = partition_labels['final_test']['normal']
    test_suspicious = partition_labels['final_test']['suspicious']
    print(f"Final test normal: {test_normal} (expected: 13200)")
    print(f"Final test suspicious: {test_suspicious} (expected: 1800)")
    if test_normal != 13200 or test_suspicious != 1800:
        errors.append(f"Final test class mismatch")
        print("  FAIL")
    else:
        print("  PASS")
    
    # Independent
    ind_normal = partition_labels['independent']['normal']
    ind_suspicious = partition_labels['independent']['suspicious']
    print(f"Independent normal: {ind_normal} (expected: 8800)")
    print(f"Independent suspicious: {ind_suspicious} (expected: 1200)")
    if ind_normal != 8800 or ind_suspicious != 1200:
        errors.append(f"Independent class mismatch")
        print("  FAIL")
    else:
        print("  PASS")
    
    print()
    return errors

def validate_entities(entity_metadata):
    """Validate entity counts."""
    print("=" * 80)
    print("VALIDATION E: ENTITIES")
    print("=" * 80)
    
    errors = []
    
    actual_wallets = len(entity_metadata['wallets'])
    actual_agents = len(entity_metadata['agents'])
    
    print(f"Total wallets: {actual_wallets} (expected: {EXPECTED_WALLETS})")
    if actual_wallets != EXPECTED_WALLETS:
        errors.append(f"Wallet count mismatch: {actual_wallets} != {EXPECTED_WALLETS}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Total agents: {actual_agents} (expected: {EXPECTED_AGENTS})")
    if actual_agents != EXPECTED_AGENTS:
        errors.append(f"Agent count mismatch: {actual_agents} != {EXPECTED_AGENTS}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print()
    return errors

def validate_channels(transactions):
    """Validate channel allocation."""
    print("=" * 80)
    print("VALIDATION F: CHANNELS")
    print("=" * 80)
    
    errors = []
    
    agent_mediated = len([tx for tx in transactions if tx['agent_id'] and tx['agent_id'] != ''])
    direct_p2p = len([tx for tx in transactions if not tx['agent_id'] or tx['agent_id'] == ''])
    
    # Allow ±1% tolerance for channel allocation
    agent_tolerance = EXPECTED_AGENT_MEDIATED * 0.01  # ±1%
    
    print(f"Agent-mediated: {agent_mediated} (expected: {EXPECTED_AGENT_MEDIATED} ±{int(agent_tolerance)})")
    if abs(agent_mediated - EXPECTED_AGENT_MEDIATED) > agent_tolerance:
        errors.append(f"Agent-mediated mismatch: {agent_mediated} != {EXPECTED_AGENT_MEDIATED} (outside tolerance)")
        print("  FAIL")
    else:
        print("  PASS")
    
    print(f"Direct P2P: {direct_p2p} (expected: {EXPECTED_DIRECT_P2P} ±{int(agent_tolerance)})")
    if abs(direct_p2p - EXPECTED_DIRECT_P2P) > agent_tolerance:
        errors.append(f"Direct P2P mismatch: {direct_p2p} != {EXPECTED_DIRECT_P2P} (outside tolerance)")
        print("  FAIL")
    else:
        print("  PASS")
    
    print()
    return errors

def validate_isolation(transactions, entity_metadata):
    """Validate entity isolation and cross-partition edges."""
    print("=" * 80)
    print("VALIDATION G: ISOLATION")
    print("=" * 80)
    
    errors = []
    
    # Create wallet to partition mapping
    wallet_partition = {w['wallet_id']: w['partition'] for w in entity_metadata['wallets']}
    
    # Check for cross-partition edges
    cross_partition_edges = 0
    for tx in transactions:
        sender_partition = wallet_partition.get(tx['sender_wallet'])
        receiver_partition = wallet_partition.get(tx['receiver_wallet'])
        if sender_partition and receiver_partition and sender_partition != receiver_partition:
            cross_partition_edges += 1
    
    print(f"Cross-partition edges: {cross_partition_edges} (expected: 0)")
    if cross_partition_edges > 0:
        errors.append(f"Found {cross_partition_edges} cross-partition edges")
        print("  FAIL")
    else:
        print("  PASS")
    
    # Check wallet overlap
    wallet_partition_set = set(w['partition'] for w in entity_metadata['wallets'])
    wallet_counts = Counter(w['partition'] for w in entity_metadata['wallets'])
    
    print(f"Wallet partition distribution: {dict(wallet_counts)}")
    if len(wallet_partition_set) != 4:
        errors.append(f"Wallet partition set incorrect: {wallet_partition_set}")
        print("  FAIL")
    else:
        print("  PASS")
    
    # Check agent overlap
    agent_partition_set = set(a['partition'] for a in entity_metadata['agents'])
    agent_counts = Counter(a['partition'] for a in entity_metadata['agents'])
    
    print(f"Agent partition distribution: {dict(agent_counts)}")
    if len(agent_partition_set) != 4:
        errors.append(f"Agent partition set incorrect: {agent_partition_set}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print()
    return errors

def validate_identifiers(transactions, entity_metadata):
    """Validate identifier uniqueness."""
    print("=" * 80)
    print("VALIDATION H: IDENTIFIERS")
    print("=" * 80)
    
    errors = []
    
    # Check transaction ID uniqueness
    tx_ids = [tx['transaction_id'] for tx in transactions]
    if len(tx_ids) != len(set(tx_ids)):
        errors.append("Duplicate transaction IDs found")
        print("Transaction IDs: FAIL (duplicates found)")
    else:
        print("Transaction IDs: PASS")
    
    # Check event sequence uniqueness
    event_sequences = [int(tx['event_sequence']) for tx in transactions]
    if len(event_sequences) != len(set(event_sequences)):
        errors.append("Duplicate event sequences found")
        print("Event sequences: FAIL (duplicates found)")
    else:
        print("Event sequences: PASS")
    
    # Check wallet ID uniqueness
    wallet_ids = [w['wallet_id'] for w in entity_metadata['wallets']]
    if len(wallet_ids) != len(set(wallet_ids)):
        errors.append("Duplicate wallet IDs found")
        print("Wallet IDs: FAIL (duplicates found)")
    else:
        print("Wallet IDs: PASS")
    
    # Check agent ID uniqueness
    agent_ids = [a['agent_id'] for a in entity_metadata['agents']]
    if len(agent_ids) != len(set(agent_ids)):
        errors.append("Duplicate agent IDs found")
        print("Agent IDs: FAIL (duplicates found)")
    else:
        print("Agent IDs: PASS")
    
    print()
    return errors

def validate_transaction_validity(transactions):
    """Validate transaction field validity."""
    print("=" * 80)
    print("VALIDATION I: TRANSACTION VALIDITY")
    print("=" * 80)
    
    errors = []
    
    for i, tx in enumerate(transactions):
        # Check sender != receiver
        if tx['sender_wallet'] == tx['receiver_wallet']:
            errors.append(f"Transaction {i}: sender == receiver")
            print(f"Transaction {i}: FAIL (sender == receiver)")
            break
        
        # Check amount > 0
        amount = float(tx['amount'])
        if amount <= 0:
            errors.append(f"Transaction {i}: non-positive amount")
            print(f"Transaction {i}: FAIL (non-positive amount)")
            break
        
        # Check channel consistency with agent_id
        has_agent = bool(tx['agent_id'] and tx['agent_id'] != '')
        if has_agent and tx['channel'] != 'agent':
            errors.append(f"Transaction {i}: channel mismatch with agent_id")
            print(f"Transaction {i}: FAIL (channel mismatch)")
            break
        
        if not has_agent and tx['channel'] != 'p2p':
            errors.append(f"Transaction {i}: channel mismatch without agent_id")
            print(f"Transaction {i}: FAIL (channel mismatch)")
            break
    else:
        print("All transactions: PASS")
    
    print()
    return errors

def validate_temporal_validity(transactions):
    """Validate temporal ordering."""
    print("=" * 80)
    print("VALIDATION J: TEMPORAL VALIDITY")
    print("=" * 80)
    
    errors = []
    
    # Check event_sequence is sequential
    event_sequences = sorted([int(tx['event_sequence']) for tx in transactions])
    expected_sequence = list(range(len(transactions)))
    
    if event_sequences != expected_sequence:
        errors.append("Event sequence not sequential")
        print("Event sequence: FAIL (not sequential)")
    else:
        print("Event sequence: PASS")
    
    # Check timestamps are valid
    for i, tx in enumerate(transactions):
        try:
            datetime.fromisoformat(tx['event_timestamp'])
        except ValueError:
            errors.append(f"Transaction {i}: invalid timestamp")
            print(f"Transaction {i}: FAIL (invalid timestamp)")
            break
    else:
        print("Timestamps: PASS")
    
    print()
    return errors

def validate_scenario_diversity(ground_truth):
    """Validate scenario family distribution."""
    print("=" * 80)
    print("VALIDATION K: SCENARIO DIVERSITY")
    print("=" * 80)
    
    errors = []
    
    # Count by scenario type
    scenario_counts = Counter()
    for gt in ground_truth:
        if gt['scenario_type']:
            scenario_counts[gt['scenario_type']] += 1
    
    print("Scenario family distribution:")
    for scenario, count in scenario_counts.most_common():
        print(f"  {scenario}: {count}")
        if count > 1000:
            errors.append(f"Scenario {scenario} exceeds 1000 cap: {count}")
            print(f"    FAIL (exceeds cap)")
        else:
            print(f"    PASS")
    
    print()
    return errors

def validate_shortcut_leakage(transactions, ground_truth):
    """Validate for obvious label shortcuts."""
    print("=" * 80)
    print("VALIDATION L: SHORTCUT LEAKAGE")
    print("=" * 80)
    
    errors = []
    
    # Create label mapping
    tx_label = {gt['transaction_id']: gt['ground_truth_label'] for gt in ground_truth}
    
    # Check amount distribution overlap
    normal_amounts = [float(tx['amount']) for tx in transactions if tx_label[tx['transaction_id']] == 0]
    suspicious_amounts = [float(tx['amount']) for tx in transactions if tx_label[tx['transaction_id']] == 1]
    
    normal_min, normal_max = min(normal_amounts), max(normal_amounts)
    suspicious_min, suspicious_max = min(suspicious_amounts), max(suspicious_amounts)
    
    print(f"Normal amount range: ${normal_min:,.2f} - ${normal_max:,.2f}")
    print(f"Suspicious amount range: ${suspicious_min:,.2f} - ${suspicious_max:,.2f}")
    
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
    
    print()
    return errors

def validate_duplication(transactions, ground_truth):
    """Validate for duplicate transactions."""
    print("=" * 80)
    print("VALIDATION M: DUPLICATION")
    print("=" * 80)
    
    errors = []
    
    # Check for exact duplicate transactions
    tx_signatures = []
    for tx in transactions:
        signature = (tx['sender_wallet'], tx['receiver_wallet'], float(tx['amount']), tx['event_timestamp'])
        tx_signatures.append(signature)
    
    if len(tx_signatures) != len(set(tx_signatures)):
        errors.append("Duplicate transaction signatures found")
        print("Exact duplicates: FAIL")
    else:
        print("Exact duplicates: PASS")
    
    print()
    return errors

def validate_feature_compatibility(transactions):
    """Validate that all required raw fields exist for 30 features."""
    print("=" * 80)
    print("VALIDATION N: FEATURE COMPATIBILITY")
    print("=" * 80)
    
    errors = []
    
    required_fields = [
        'transaction_id', 'event_timestamp', 'event_sequence',
        'sender_wallet', 'receiver_wallet', 'amount',
        'transaction_type', 'channel', 'agent_id'
    ]
    
    sample_tx = transactions[0]
    missing_fields = [field for field in required_fields if field not in sample_tx]
    
    if missing_fields:
        errors.append(f"Missing required fields: {missing_fields}")
        print(f"Required fields: FAIL (missing: {missing_fields})")
    else:
        print("Required fields: PASS")
    
    # Verify field types
    try:
        float(sample_tx['amount'])
        int(sample_tx['event_sequence'])
        print("Field types: PASS")
    except (ValueError, TypeError) as e:
        errors.append(f"Field type error: {e}")
        print(f"Field types: FAIL ({e})")
    
    print()
    return errors

def validate_independent_evaluation(transactions, entity_metadata):
    """Validate independent evaluation isolation."""
    print("=" * 80)
    print("VALIDATION O: INDEPENDENT EVALUATION")
    print("=" * 80)
    
    errors = []
    
    # Get independent wallets and agents
    independent_wallets = {w['wallet_id'] for w in entity_metadata['wallets'] if w['partition'] == 'independent'}
    independent_agents = {a['agent_id'] for a in entity_metadata['agents'] if a['partition'] == 'independent'}
    
    # Get other partition wallets and agents
    other_wallets = {w['wallet_id'] for w in entity_metadata['wallets'] if w['partition'] != 'independent'}
    other_agents = {a['agent_id'] for a in entity_metadata['agents'] if a['partition'] != 'independent'}
    
    # Check wallet overlap
    wallet_overlap = independent_wallets & other_wallets
    print(f"Independent wallet overlap: {len(wallet_overlap)} (expected: 0)")
    if wallet_overlap:
        errors.append(f"Independent wallet overlap: {wallet_overlap}")
        print("  FAIL")
    else:
        print("  PASS")
    
    # Check agent overlap
    agent_overlap = independent_agents & other_agents
    print(f"Independent agent overlap: {len(agent_overlap)} (expected: 0)")
    if agent_overlap:
        errors.append(f"Independent agent overlap: {agent_overlap}")
        print("  FAIL")
    else:
        print("  PASS")
    
    print()
    return errors

# =============================================================================
# MAIN VALIDATION
# =============================================================================

def main():
    print("=" * 80)
    print("STAGE 11: DATASET VALIDATION")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Dataset Version: {DATASET_VERSION}")
    print()
    
    # Load data
    print("Loading data...")
    transactions = load_transactions()
    ground_truth = load_ground_truth()
    entity_metadata = load_entity_metadata()
    manifest = load_manifest()
    print(f"Loaded {len(transactions)} transactions")
    print(f"Loaded {len(ground_truth)} ground truth records")
    print(f"Loaded {len(entity_metadata['wallets'])} wallets")
    print(f"Loaded {len(entity_metadata['agents'])} agents")
    print()
    
    # Run validations
    all_errors = []
    
    all_errors.extend(validate_totals(transactions, ground_truth))
    all_errors.extend(validate_class_distribution(ground_truth))
    all_errors.extend(validate_partitions(transactions, ground_truth, entity_metadata))
    all_errors.extend(validate_partition_class_counts(transactions, ground_truth))
    all_errors.extend(validate_entities(entity_metadata))
    all_errors.extend(validate_channels(transactions))
    all_errors.extend(validate_isolation(transactions, entity_metadata))
    all_errors.extend(validate_identifiers(transactions, entity_metadata))
    all_errors.extend(validate_transaction_validity(transactions))
    all_errors.extend(validate_temporal_validity(transactions))
    all_errors.extend(validate_scenario_diversity(ground_truth))
    all_errors.extend(validate_shortcut_leakage(transactions, ground_truth))
    all_errors.extend(validate_duplication(transactions, ground_truth))
    all_errors.extend(validate_feature_compatibility(transactions))
    all_errors.extend(validate_independent_evaluation(transactions, entity_metadata))
    
    # Summary
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    if all_errors:
        print(f"FAILED: {len(all_errors)} validation error(s)")
        for error in all_errors:
            print(f"  - {error}")
        print()
        return False
    else:
        print("PASSED: All validation checks successful")
        print()
        return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
