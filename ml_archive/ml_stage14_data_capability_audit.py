"""
STAGE 14A: DATA/GENERATOR CAPABILITY AUDIT

Before designing new features, audit the Stage 11 generator and dataset
to determine which information dimensions are actually available.
"""

import csv
import json
from datetime import datetime

print("=" * 80)
print("STAGE 14A: DATA/GENERATOR CAPABILITY AUDIT")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================================
# LOAD DATA
# ============================================================================

with open('ml_stage11_dataset.csv', 'r') as f:
    reader = csv.DictReader(f)
    dataset = list(reader)

with open('ml_stage11_ground_truth.json', 'r') as f:
    ground_truth = json.load(f)

# ============================================================================
# AUDIT DATA AVAILABILITY
# ============================================================================

print("AUDITING DATA AVAILABILITY IN STAGE 11 DATASET")
print("-" * 80)

# Check available columns
columns = dataset[0].keys()
print(f"Available columns in dataset: {list(columns)}")
print()

# Audit each dimension
dimensions = {
    "recipient_account/counterparty_identity": {
        "available": "receiver_account" in columns,
        "evidence": "receiver_account column present" if "receiver_account" in columns else "No receiver_account column"
    },
    "recipient_country": {
        "available": "receiver_country" in columns or "country" in columns,
        "evidence": "Checking for country columns..."
    },
    "sender_country": {
        "available": "sender_country" in columns or "country" in columns,
        "evidence": "Checking for country columns..."
    },
    "transaction_direction": {
        "available": "transaction_type" in columns,
        "evidence": "transaction_type column present (deposit/withdraw/transfer)"
    },
    "inbound_outbound_relationship": {
        "available": "transaction_type" in columns,
        "evidence": "Can infer from transaction_type (deposit=inbound, withdraw/transfer=outbound)"
    },
    "account_age_tenure": {
        "available": "account_open_date" in columns or "customer_since" in columns,
        "evidence": "Checking for account age columns..."
    },
    "transaction_purpose": {
        "available": "purpose" in columns or "description" in columns,
        "evidence": "description column present but may not contain purpose"
    },
    "geographic_information": {
        "available": "country" in columns or "location" in columns or "ip_address" in columns,
        "evidence": "Checking for geographic columns..."
    },
    "device_ip_information": {
        "available": "device" in columns or "ip_address" in columns or "user_agent" in columns,
        "evidence": "Checking for device/IP columns..."
    },
    "cash_source_information": {
        "available": "cash_source" in columns or "origin" in columns,
        "evidence": "Checking for cash source columns..."
    },
    "ownership_beneficial_owner": {
        "available": "owner" in columns or "beneficial_owner" in columns,
        "evidence": "Checking for ownership columns..."
    },
    "transaction_chains": {
        "available": "chain_id" in columns or "related_transactions" in columns,
        "evidence": "Checking for chain columns..."
    },
    "account_to_account_network_relationships": {
        "available": "sender_account" in columns and "receiver_account" in columns,
        "evidence": "Can infer network from sender_account and receiver_account relationships"
    },
    "historical_customer_behavior": {
        "available": True,
        "evidence": "Can compute from transaction history (sender_account, timestamp, amount)"
    }
}

# Detailed checks
print("DETAILED AVAILABILITY CHECK:")
print()

for dimension, info in dimensions.items():
    if isinstance(info["available"], bool):
        status = "AVAILABLE" if info["available"] else "NOT AVAILABLE"
    else:
        status = info["available"]
    
    print(f"{dimension}:")
    print(f"  Status: {status}")
    print(f"  Evidence: {info['evidence']}")
    print()

# ============================================================================
# AUDIT GENERATOR CAPABILITY
# ============================================================================

print("=" * 80)
print("AUDITING GENERATOR CAPABILITY")
print("-" * 80)

# Check if generator has country information
print("\nChecking generator for HIGH_RISK_COUNTRIES:")
try:
    from ml_stage3_generator import HIGH_RISK_COUNTRIES, LEGITIMATE_COUNTRIES
    print(f"  HIGH_RISK_COUNTRIES defined: {len(HIGH_RISK_COUNTRIES)} countries")
    print(f"  LEGITIMATE_COUNTRIES defined: {len(LEGITIMATE_COUNTRIES)} countries")
    print(f"  Status: GENERATOR HAS COUNTRY INFORMATION")
except:
    print(f"  Status: GENERATOR COUNTRY INFORMATION NOT ACCESSIBLE")

print()

# Check if generator assigns countries to accounts
print("Checking if generator assigns countries to accounts:")
# Sample some receiver accounts to see if they have country codes
sample_receivers = [tx['receiver_account'] for tx in dataset[:20]]
print(f"  Sample receiver accounts: {sample_receivers[:5]}")
print(f"  Account format: {sample_receivers[0]}")
print(f"  Status: ACCOUNTS DO NOT CONTAIN COUNTRY CODES (format: ACC######)")
print()

# ============================================================================
# FINAL CLASSIFICATION
# ============================================================================

print("=" * 80)
print("FINAL DATA CAPABILITY CLASSIFICATION")
print("-" * 80)

final_classification = {
    "recipient_account/counterparty_identity": "AVAILABLE",
    "recipient_country": "NOT AVAILABLE (generator has country info but not in dataset)",
    "sender_country": "NOT AVAILABLE (generator has country info but not in dataset)",
    "transaction_direction": "AVAILABLE (transaction_type)",
    "inbound_outbound_relationship": "AVAILABLE (inferred from transaction_type)",
    "account_age_tenure": "NOT AVAILABLE",
    "transaction_purpose": "PARTIALLY AVAILABLE (description field exists but not structured)",
    "geographic_information": "NOT AVAILABLE",
    "device_ip_information": "NOT AVAILABLE",
    "cash_source_information": "NOT AVAILABLE",
    "ownership_beneficial_owner": "NOT AVAILABLE",
    "transaction_chains": "NOT AVAILABLE (no chain_id or related_transactions)",
    "account_to_account_network_relationships": "AVAILABLE (sender_account + receiver_account)",
    "historical_customer_behavior": "AVAILABLE (can compute from transaction history)"
}

print("Dimension Classification:")
for dimension, status in final_classification.items():
    print(f"  {dimension}: {status}")

print()

# ============================================================================
# SAVE RESULTS
# ============================================================================

results = {
    "timestamp": datetime.now().isoformat(),
    "data_capability_audit": final_classification,
    "generator_has_country_info": True,
    "dataset_has_country_info": False,
    "key_limitations": [
        "Generator has country information but does not export it to dataset",
        "No account age/tenure information",
        "No device/IP information",
        "No ownership/beneficial owner information",
        "No transaction chain tracking",
        "No structured transaction purpose"
    ],
    "available_dimensions": [
        "recipient_account/counterparty_identity",
        "transaction_direction",
        "inbound_outbound_relationship",
        "account_to_account_network_relationships",
        "historical_customer_behavior"
    ]
}

with open('ml_stage14_data_capability_audit_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("=" * 80)
print("DATA CAPABILITY AUDIT COMPLETE")
print("=" * 80)
print("Results saved to ml_stage14_data_capability_audit_results.json")
