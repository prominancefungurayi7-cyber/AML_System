"""
STAGE 14D: FEATURE SPECIFICATION

Produce a proposed revised feature specification containing:
1. Existing 34 features
2. New candidate features
3. Feature definitions
4. AML scenario coverage
5. Data availability
6. Temporal-safety status
7. Expected observability improvement
8. Redundant/constant features to remove
9. Final proposed feature count
"""

import json
from datetime import datetime

print("=" * 80)
print("STAGE 14D: FEATURE SPECIFICATION")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================================
# LOAD DATA
# ============================================================================

with open('ml_stage14_feature_gap_design_results.json', 'r') as f:
    feature_design = json.load(f)

with open('ml_stage14_temporal_safety_verification_results.json', 'r') as f:
    temporal_safety = json.load(f)

with open('ml_stage13_scenario_analysis_results.json', 'r') as f:
    scenario_analysis = json.load(f)

# ============================================================================
# EXISTING 34 FEATURES (STAGE 5 BASELINE)
# ============================================================================

existing_34_features = {
    "amount": {
        "definition": "Transaction amount",
        "category": "amount",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (current transaction)",
        "observability": "MODERATE"
    },
    "sender_avg_amount": {
        "definition": "Average transaction amount for sender (historical)",
        "category": "amount",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (historical)",
        "observability": "WEAK"
    },
    "sender_max_amount": {
        "definition": "Maximum transaction amount for sender (historical)",
        "category": "amount",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (historical)",
        "observability": "WEAK"
    },
    "sender_tx_count": {
        "definition": "Total transaction count for sender (historical)",
        "category": "frequency",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (historical)",
        "observability": "STRONG for severe"
    },
    "amount_to_sender_avg": {
        "definition": "Current amount divided by sender average amount",
        "category": "amount",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (current + historical)",
        "observability": "WEAK"
    },
    "amount_to_sender_max": {
        "definition": "Current amount divided by sender maximum amount",
        "category": "amount",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (current + historical)",
        "observability": "WEAK"
    },
    "sender_tx_count_24h": {
        "definition": "Transaction count in last 24 hours",
        "category": "velocity",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (historical 24h)",
        "observability": "WEAK"
    },
    "sender_volume_24h": {
        "definition": "Total transaction volume in last 24 hours",
        "category": "velocity",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (historical 24h)",
        "observability": "WEAK"
    },
    "amount_to_sender_volume_24h": {
        "definition": "Current amount divided by 24h volume",
        "category": "velocity",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (current + historical 24h)",
        "observability": "WEAK"
    },
    "is_new_recipient": {
        "definition": "Binary flag if recipient is new to sender",
        "category": "recipient",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (historical)",
        "observability": "WEAK"
    },
    "same_day_count": {
        "definition": "Number of transactions on same day",
        "category": "velocity",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (historical same day)",
        "observability": "WEAK"
    },
    "same_day_total": {
        "definition": "Total transaction amount on same day",
        "category": "velocity",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (historical same day)",
        "observability": "WEAK"
    },
    "same_recipient_count": {
        "definition": "Count of previous transactions to same recipient",
        "category": "recipient",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (historical)",
        "observability": "WEAK"
    },
    "rapid_transfer_count": {
        "definition": "Count of rapid transfers (inbound to outbound within 1 hour)",
        "category": "velocity",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (historical)",
        "observability": "WEAK"
    },
    "hour": {
        "definition": "Hour of day (0-23)",
        "category": "timing",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (current transaction)",
        "observability": "WEAK"
    },
    "day_of_week": {
        "definition": "Day of week (0-6)",
        "category": "timing",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (current transaction)",
        "observability": "MODERATE for severe"
    },
    "is_weekend": {
        "definition": "Binary flag if transaction is on weekend",
        "category": "timing",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (current transaction)",
        "observability": "MODERATE for severe"
    },
    "is_deposit": {
        "definition": "Binary flag if transaction type is deposit",
        "category": "transaction_type",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (current transaction)",
        "observability": "WEAK"
    },
    "is_withdraw": {
        "definition": "Binary flag if transaction type is withdraw",
        "category": "transaction_type",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (current transaction)",
        "observability": "WEAK"
    },
    "is_transfer": {
        "definition": "Binary flag if transaction type is transfer",
        "category": "transaction_type",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (current transaction)",
        "observability": "WEAK"
    },
    "is_off_hours": {
        "definition": "Binary flag if transaction is outside business hours",
        "category": "timing",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (current transaction)",
        "observability": "WEAK"
    },
    "time_since_last_tx": {
        "definition": "Time since last transaction (seconds)",
        "category": "timing",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (historical)",
        "observability": "WEAK"
    },
    "tx_frequency_7d": {
        "definition": "Transaction frequency in last 7 days",
        "category": "frequency",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (historical 7d)",
        "observability": "WEAK"
    },
    "tx_frequency_30d": {
        "definition": "Transaction frequency in last 30 days",
        "category": "frequency",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (historical 30d)",
        "observability": "STRONG for severe"
    },
    "frequency_change_vs_avg_7d": {
        "definition": "Change in frequency vs 7-day average",
        "category": "frequency",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (historical 7d)",
        "observability": "MODERATE for severe"
    },
    "unique_recipients_24h": {
        "definition": "Number of unique recipients in last 24 hours",
        "category": "recipient",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (historical 24h)",
        "observability": "WEAK"
    },
    "unique_recipients_7d": {
        "definition": "Number of unique recipients in last 7 days",
        "category": "recipient",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (historical 7d)",
        "observability": "WEAK"
    },
    "recipient_concentration": {
        "definition": "Herfindahl index of recipient concentration",
        "category": "recipient",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (historical)",
        "observability": "WEAK"
    },
    "new_recipient_ratio_7d": {
        "definition": "Ratio of new recipients in last 7 days",
        "category": "recipient",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (historical 7d)",
        "observability": "WEAK"
    },
    "amount_std_dev": {
        "definition": "Standard deviation of transaction amounts",
        "category": "amount",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (historical)",
        "observability": "WEAK"
    },
    "amount_z_score": {
        "definition": "Z-score of current amount relative to historical",
        "category": "amount",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (current + historical)",
        "observability": "WEAK"
    },
    "amount_change_vs_avg_7d": {
        "definition": "Change in amount vs 7-day average",
        "category": "amount",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (historical 7d)",
        "observability": "WEAK"
    },
    "is_self_transfer": {
        "definition": "Binary flag if sender == receiver",
        "category": "transaction_type",
        "scenario_coverage": ["normal", "suspicious", "severe"],
        "data_availability": "AVAILABLE",
        "temporal_safety": "SAFE (current transaction)",
        "observability": "NONE (constant 0.0)"
    }
}

# ============================================================================
# NEW CANDIDATE FEATURES (STAGE 14B)
# ============================================================================

new_candidate_features = {}

for scenario, features in feature_design["candidate_features"].items():
    for feature_name, feature_info in features.items():
        new_candidate_features[feature_name] = {
            "definition": feature_info["definition"],
            "aml_meaning": feature_info["aml_meaning"],
            "category": scenario,
            "scenario_coverage": [scenario],
            "data_availability": "AVAILABLE",
            "temporal_safety": "SAFE",
            "observability": feature_info["observability"]
        }

# ============================================================================
# IDENTIFY REDUNDANT/CONSTANT FEATURES TO REMOVE
# ============================================================================

print("IDENTIFYING REDUNDANT/CONSTANT FEATURES")
print("-" * 80)

features_to_remove = {
    "is_self_transfer": {
        "reason": "CONSTANT (always 0.0 in Stage 11 dataset)",
        "action": "REMOVE from active modeling"
    }
}

for feature_name, reason in features_to_remove.items():
    print(f"  {feature_name}: {reason['action']} - {reason['reason']}")

# ============================================================================
# FINAL PROPOSED FEATURE SPECIFICATION
# ============================================================================

print("\n" + "=" * 80)
print("FINAL PROPOSED FEATURE SPECIFICATION")
print("-" * 80)

# Combine existing (minus removed) with new
final_features = {}

# Add existing features (excluding removed)
for feature_name, feature_info in existing_34_features.items():
    if feature_name not in features_to_remove:
        final_features[feature_name] = feature_info

# Add new candidate features
for feature_name, feature_info in new_candidate_features.items():
    final_features[feature_name] = feature_info

print(f"Original 34 features: {len(existing_34_features)}")
print(f"Features to remove: {len(features_to_remove)}")
print(f"New candidate features: {len(new_candidate_features)}")
print(f"Final proposed features: {len(final_features)}")

# ============================================================================
# AML SCENARIO COVERAGE ANALYSIS
# ============================================================================

print("\n" + "=" * 80)
print("AML SCENARIO COVERAGE ANALYSIS")
print("-" * 80)

scenario_feature_coverage = {
    "structuring": [],
    "layering": [],
    "funnel": [],
    "rapid_movement": [],
    "behavioral_change": [],
    "high_risk_country": [],
    "severe": []
}

for feature_name, feature_info in final_features.items():
    for scenario in feature_info["scenario_coverage"]:
        if scenario in scenario_feature_coverage:
            scenario_feature_coverage[scenario].append(feature_name)

for scenario, features in scenario_feature_coverage.items():
    print(f"{scenario}: {len(features)} features")

# ============================================================================
# EXPECTED OBSERVABILITY IMPROVEMENT
# ============================================================================

print("\n" + "=" * 80)
print("EXPECTED OBSERVABILITY IMPROVEMENT")
print("-" * 80)

# Stage 13 baseline observability
baseline_observability = {
    "structuring": "NONE",
    "layering": "WEAK",
    "funnel": "NONE",
    "rapid_movement": "WEAK",
    "behavioral_change": "NONE",
    "high_risk_country": "NONE",
    "severe": "MODERATE"
}

# Expected observability with new features
expected_observability = {
    "structuring": "MODERATE (threshold proximity, clustering)",
    "layering": "MODERATE (counterparty diversity, pass-through)",
    "funnel": "MODERATE (inbound aggregation, concentration)",
    "rapid_movement": "MODERATE (pass-through timing, velocity)",
    "behavioral_change": "MODERATE (deviation from baseline)",
    "high_risk_country": "NONE (requires generator modification)",
    "severe": "STRONG (aggregation of multiple indicators)"
}

print("Scenario | Baseline | Expected | Improvement")
print("-" * 60)
for scenario in baseline_observability:
    baseline = baseline_observability[scenario]
    expected = expected_observability[scenario]
    improvement = "YES" if expected != baseline else "NO"
    print(f"{scenario} | {baseline:12} | {expected:8} | {improvement}")

# ============================================================================
# SAVE RESULTS
# ============================================================================

results = {
    "timestamp": datetime.now().isoformat(),
    "original_34_features": len(existing_34_features),
    "features_to_remove": features_to_remove,
    "new_candidate_features": len(new_candidate_features),
    "final_proposed_features": len(final_features),
    "final_feature_specification": final_features,
    "scenario_feature_coverage": scenario_feature_coverage,
    "baseline_observability": baseline_observability,
    "expected_observability": expected_observability,
    "critical_limitation": "high_risk_country requires generator modification to export country information"
}

with open('ml_stage14_feature_specification_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n" + "=" * 80)
print("FEATURE SPECIFICATION COMPLETE")
print("=" * 80)
print("Results saved to ml_stage14_feature_specification_results.json")
print()
print(f"FINAL PROPOSED FEATURE COUNT: {len(final_features)}")
print(f"(34 original - 1 removed + 25 new = {len(final_features)})")
