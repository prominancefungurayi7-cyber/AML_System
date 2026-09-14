"""
STAGE 14B: FEATURE GAP DESIGN

Design candidate features based on available data dimensions.
Only design features that can be computed from available data.
"""

import json
from datetime import datetime

print("=" * 80)
print("STAGE 14B: FEATURE GAP DESIGN")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================================
# LOAD DATA CAPABILITY AUDIT RESULTS
# ============================================================================

with open('ml_stage14_data_capability_audit_results.json', 'r') as f:
    capability_audit = json.load(f)

print("DATA CAPABILITY CONSTRAINTS:")
print("-" * 80)
available_dimensions = capability_audit["available_dimensions"]
print(f"Available dimensions: {available_dimensions}")
print()

key_limitations = capability_audit["key_limitations"]
print("Key limitations:")
for limitation in key_limitations:
    print(f"  - {limitation}")
print()

# ============================================================================
# DESIGN CANDIDATE FEATURES BY SCENARIO
# ============================================================================

print("DESIGNING CANDIDATE FEATURES BY SCENARIO")
print("-" * 80)

candidate_features = {}

# ============================================================================
# STRUCTURING
# ============================================================================

print("\nSTRUCTURING:")
structuring_features = {
    "threshold_proximity_10k": {
        "definition": "Distance from $10,000 CTR threshold: |amount - 10000|",
        "aml_meaning": "Detects transactions intentionally broken to avoid $10,000 reporting threshold",
        "data_requirements": ["amount"],
        "temporal_safety": "Computed from current transaction amount only",
        "observability": "Makes structuring observable by detecting near-threshold patterns"
    },
    "threshold_proximity_5k": {
        "definition": "Distance from $5,000 threshold: |amount - 5000|",
        "aml_meaning": "Detects transactions intentionally broken to avoid lower reporting thresholds",
        "data_requirements": ["amount"],
        "temporal_safety": "Computed from current transaction amount only",
        "observability": "Makes structuring observable by detecting near-threshold patterns"
    },
    "near_threshold_count_7d": {
        "definition": "Count of transactions in last 7 days with amount in [8000, 12000]",
        "aml_meaning": "Detects repeated near-threshold transactions (structuring pattern)",
        "data_requirements": ["amount", "timestamp", "historical transactions"],
        "temporal_safety": "Computed from historical transactions (last 7 days only)",
        "observability": "Makes structuring observable by detecting clustering near threshold"
    },
    "near_threshold_ratio_7d": {
        "definition": "Ratio of near-threshold transactions to total transactions in last 7 days",
        "aml_meaning": "Detects high proportion of near-threshold activity",
        "data_requirements": ["amount", "timestamp", "historical transactions"],
        "temporal_safety": "Computed from historical transactions (last 7 days only)",
        "observability": "Makes structuring observable by detecting clustering near threshold"
    },
    "amount_clustering_score": {
        "definition": "Standard deviation of transaction amounts in last 7 days",
        "aml_meaning": "Low variance indicates intentional amount clustering (structuring)",
        "data_requirements": ["amount", "timestamp", "historical transactions"],
        "temporal_safety": "Computed from historical transactions (last 7 days only)",
        "observability": "Makes structuring observable by detecting amount clustering"
    }
}

candidate_features["structuring"] = structuring_features
for feature_name, feature_info in structuring_features.items():
    print(f"  {feature_name}: {feature_info['observability']}")

# ============================================================================
# LAYERING
# ============================================================================

print("\nLAYERING:")
layering_features = {
    "counterparty_diversity_7d": {
        "definition": "Number of unique receiver accounts in last 7 days",
        "aml_meaning": "High diversity indicates layering (funds moving through many accounts)",
        "data_requirements": ["receiver_account", "timestamp", "historical transactions"],
        "temporal_safety": "Computed from historical transactions (last 7 days only)",
        "observability": "Makes layering observable by detecting counterparty diversity"
    },
    "counterparty_diversity_30d": {
        "definition": "Number of unique receiver accounts in last 30 days",
        "aml_meaning": "High diversity indicates layering (funds moving through many accounts)",
        "data_requirements": ["receiver_account", "timestamp", "historical transactions"],
        "temporal_safety": "Computed from historical transactions (last 30 days only)",
        "observability": "Makes layering observable by detecting counterparty diversity"
    },
    "pass_through_ratio_7d": {
        "definition": "Ratio of outbound transfers to total transactions in last 7 days",
        "aml_meaning": "High pass-through ratio indicates layering (funds moving through account)",
        "data_requirements": ["transaction_type", "timestamp", "historical transactions"],
        "temporal_safety": "Computed from historical transactions (last 7 days only)",
        "observability": "Makes layering observable by detecting pass-through behavior"
    },
    "rapid_counterparty_switch_count": {
        "definition": "Number of times receiver account changes in last 7 days",
        "aml_meaning": "Frequent counterparty switches indicate layering",
        "data_requirements": ["receiver_account", "timestamp", "historical transactions"],
        "temporal_safety": "Computed from historical transactions (last 7 days only)",
        "observability": "Makes layering observable by detecting rapid counterparty changes"
    },
    "single_counterparty_dominance_7d": {
        "definition": "Maximum percentage of transactions to single receiver in last 7 days",
        "aml_meaning": "Low dominance indicates layering (funds distributed across many)",
        "data_requirements": ["receiver_account", "timestamp", "historical transactions"],
        "temporal_safety": "Computed from historical transactions (last 7 days only)",
        "observability": "Makes layering observable by detecting lack of counterparty concentration"
    }
}

candidate_features["layering"] = layering_features
for feature_name, feature_info in layering_features.items():
    print(f"  {feature_name}: {feature_info['observability']}")

# ============================================================================
# FUNNEL
# ============================================================================

print("\nFUNNEL:")
funnel_features = {
    "inbound_aggregation_7d": {
        "definition": "Ratio of deposits to total transactions in last 7 days",
        "aml_meaning": "High inbound ratio indicates funnel (funds from many sources)",
        "data_requirements": ["transaction_type", "timestamp", "historical transactions"],
        "temporal_safety": "Computed from historical transactions (last 7 days only)",
        "observability": "Makes funnel observable by detecting inbound aggregation"
    },
    "outbound_diversification_7d": {
        "definition": "Ratio of transfers to total transactions in last 7 days",
        "aml_meaning": "High outbound ratio indicates funnel (funds distributed to many)",
        "data_requirements": ["transaction_type", "timestamp", "historical transactions"],
        "temporal_safety": "Computed from historical transactions (last 7 days only)",
        "observability": "Makes funnel observable by detecting outbound diversification"
    },
    "many_to_one_ratio_7d": {
        "definition": "Ratio of unique senders to unique receivers in last 7 days (network perspective)",
        "aml_meaning": "Low ratio indicates funnel (many senders to few receivers)",
        "data_requirements": ["sender_account", "receiver_account", "timestamp", "historical transactions"],
        "temporal_safety": "Computed from historical transactions (last 7 days only)",
        "observability": "Makes funnel observable by detecting many-to-one patterns"
    },
    "concentration_index_7d": {
        "definition": "Herfindahl index of receiver concentration in last 7 days",
        "aml_meaning": "High concentration indicates funnel (funds concentrated to few receivers)",
        "data_requirements": ["receiver_account", "amount", "timestamp", "historical transactions"],
        "temporal_safety": "Computed from historical transactions (last 7 days only)",
        "observability": "Makes funnel observable by detecting receiver concentration"
    }
}

candidate_features["funnel"] = funnel_features
for feature_name, feature_info in funnel_features.items():
    print(f"  {feature_name}: {feature_info['observability']}")

# ============================================================================
# RAPID MOVEMENT
# ============================================================================

print("\nRAPID_MOVEMENT:")
rapid_movement_features = {
    "inbound_to_outbound_time_avg_7d": {
        "definition": "Average time between deposit and subsequent transfer in last 7 days",
        "aml_meaning": "Short average time indicates rapid movement (funds pass through quickly)",
        "data_requirements": ["transaction_type", "timestamp", "historical transactions"],
        "temporal_safety": "Computed from historical transactions (last 7 days only)",
        "observability": "Makes rapid movement observable by detecting quick pass-through"
    },
    "same_day_pass_through_count_7d": {
        "definition": "Count of deposit-transfer pairs occurring on same day in last 7 days",
        "aml_meaning": "High count indicates rapid movement (funds pass through same day)",
        "data_requirements": ["transaction_type", "timestamp", "historical transactions"],
        "temporal_safety": "Computed from historical transactions (last 7 days only)",
        "observability": "Makes rapid movement observable by detecting same-day pass-through"
    },
    "funds_through_ratio_7d": {
        "definition": "Ratio of outbound amount to inbound amount in last 7 days",
        "aml_meaning": "High ratio indicates rapid movement (most inbound funds passed through)",
        "data_requirements": ["transaction_type", "amount", "timestamp", "historical transactions"],
        "temporal_safety": "Computed from historical transactions (last 7 days only)",
        "observability": "Makes rapid movement observable by detecting funds pass-through"
    },
    "velocity_score_7d": {
        "definition": "Average number of transactions per day in last 7 days",
        "aml_meaning": "High velocity indicates rapid movement",
        "data_requirements": ["timestamp", "historical transactions"],
        "temporal_safety": "Computed from historical transactions (last 7 days only)",
        "observability": "Makes rapid movement observable by detecting high transaction velocity"
    }
}

candidate_features["rapid_movement"] = rapid_movement_features
for feature_name, feature_info in rapid_movement_features.items():
    print(f"  {feature_name}: {feature_info['observability']}")

# ============================================================================
# BEHAVIORAL CHANGE
# ============================================================================

print("\nBEHAVIORAL_CHANGE:")
behavioral_change_features = {
    "amount_deviation_from_baseline_30d": {
        "definition": "Z-score of current amount relative to 30-day historical mean",
        "aml_meaning": "High deviation indicates sudden change in amount behavior",
        "data_requirements": ["amount", "timestamp", "historical transactions"],
        "temporal_safety": "Computed from historical transactions (last 30 days only)",
        "observability": "Makes behavioral change observable by detecting amount deviation"
    },
    "frequency_deviation_from_baseline_30d": {
        "definition": "Z-score of current transaction count relative to 30-day historical mean",
        "aml_meaning": "High deviation indicates sudden change in frequency behavior",
        "data_requirements": ["timestamp", "historical transactions"],
        "temporal_safety": "Computed from historical transactions (last 30 days only)",
        "observability": "Makes behavioral change observable by detecting frequency deviation"
    },
    "counterparty_change_score_7d": {
        "definition": "Jaccard similarity between current 7-day and previous 7-day receiver sets",
        "aml_meaning": "Low similarity indicates sudden change in counterparty behavior",
        "data_requirements": ["receiver_account", "timestamp", "historical transactions"],
        "temporal_safety": "Computed from historical transactions (last 14 days: current 7d vs previous 7d)",
        "observability": "Makes behavioral change observable by detecting counterparty change"
    },
    "rolling_behavioral_change_7d": {
        "definition": "Standard deviation of amounts in last 7 days divided by standard deviation in previous 7 days",
        "aml_meaning": "High ratio indicates sudden change in amount variability",
        "data_requirements": ["amount", "timestamp", "historical transactions"],
        "temporal_safety": "Computed from historical transactions (last 14 days: current 7d vs previous 7d)",
        "observability": "Makes behavioral change observable by detecting variability change"
    }
}

candidate_features["behavioral_change"] = behavioral_change_features
for feature_name, feature_info in behavioral_change_features.items():
    print(f"  {feature_name}: {feature_info['observability']}")

# ============================================================================
# HIGH_RISK_COUNTRY
# ============================================================================

print("\nHIGH_RISK_COUNTRY:")
print("  CRITICAL: Cannot design features for high_risk_country")
print("  Reason: Generator has country information but does not export it to dataset")
print("  Required: recipient_country field in dataset")
print("  Current: Accounts do not contain country codes (format: ACC######)")
print("  Solution: MODIFY GENERATOR to export country information to dataset")
candidate_features["high_risk_country"] = {}

# ============================================================================
# MULTIPLE_TYPOLOGIES / SEVERE SCENARIOS
# ============================================================================

print("\nMULTIPLE_TYPOLOGIES / SEVERE SCENARIOS:")
severe_features = {
    "concurrent_suspicious_indicators": {
        "definition": "Count of suspicious behavioral indicators present simultaneously",
        "aml_meaning": "High count indicates multiple AML typologies (severe scenario)",
        "data_requirements": ["All candidate features"],
        "temporal_safety": "Computed from current transaction features only",
        "observability": "Makes severe scenarios observable by aggregating suspicious indicators"
    },
    "typology_aggregation_score": {
        "definition": "Combined score based on structuring + layering + funnel + rapid_movement indicators",
        "aml_meaning": "High score indicates multiple AML typologies (severe scenario)",
        "data_requirements": ["All candidate features"],
        "temporal_safety": "Computed from current transaction features only",
        "observability": "Makes severe scenarios observable by aggregating typology indicators"
    },
    "severity_index": {
        "definition": "Weighted sum of suspicious indicators based on severity weights",
        "aml_meaning": "High index indicates severe scenario (multiple typologies)",
        "data_requirements": ["All candidate features"],
        "temporal_safety": "Computed from current transaction features only",
        "observability": "Makes severe scenarios observable by aggregating severity-weighted indicators"
    }
}

candidate_features["severe"] = severe_features
for feature_name, feature_info in severe_features.items():
    print(f"  {feature_name}: {feature_info['observability']}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("FEATURE GAP DESIGN SUMMARY")
print("-" * 80)

total_features = sum(len(features) for features in candidate_features.values())
print(f"Total candidate features designed: {total_features}")

print("\nFeatures by scenario:")
for scenario, features in candidate_features.items():
    print(f"  {scenario}: {len(features)} features")

print("\nCRITICAL FINDING:")
print("  high_risk_country scenario CANNOT be detected without generator modification")
print("  All other scenarios can be addressed with available data dimensions")

# ============================================================================
# SAVE RESULTS
# ============================================================================

results = {
    "timestamp": datetime.now().isoformat(),
    "candidate_features": candidate_features,
    "total_features": total_features,
    "critical_limitation": "high_risk_country requires generator modification to export country information",
    "data_constraints": capability_audit["key_limitations"],
    "available_dimensions": capability_audit["available_dimensions"]
}

with open('ml_stage14_feature_gap_design_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n" + "=" * 80)
print("FEATURE GAP DESIGN COMPLETE")
print("=" * 80)
print("Results saved to ml_stage14_feature_gap_design_results.json")
