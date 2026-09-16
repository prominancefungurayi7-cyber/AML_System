"""
STAGE 15A: ARITHMETIC DISCREPANCY RESOLUTION

Stage 14 claimed: 34 original - 1 removed + 25 new = 57
Correct arithmetic: 34 - 1 + 25 = 58

This script resolves the discrepancy by independently verifying the count.
"""

import json
from datetime import datetime

print("=" * 80)
print("STAGE 15A: ARITHMETIC DISCREPANCY RESOLUTION")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================================
# LOAD STAGE 14 FEATURE SPECIFICATION
# ============================================================================

with open('ml_stage14_feature_specification_results.json', 'r') as f:
    stage14_spec = json.load(f)

print("STAGE 14 CLAIMED COUNTS:")
print("-" * 80)
print(f"Original 34 features: {stage14_spec['original_34_features']}")
print(f"Features to remove: {len(stage14_spec['features_to_remove'])}")
print(f"New candidate features: {stage14_spec['new_candidate_features']}")
print(f"Final proposed features: {stage14_spec['final_proposed_features']}")
print()

# ============================================================================
# INDEPENDENT VERIFICATION
# ============================================================================

print("INDEPENDENT VERIFICATION:")
print("-" * 80)

# Count existing features
existing_features = stage14_spec['final_feature_specification']
existing_count = 0
for feature_name, feature_info in existing_features.items():
    # Check if this is an existing feature (not a new candidate)
    # New candidate features have category = scenario name (structuring, layering, etc.)
    # Existing features have category = amount, velocity, frequency, etc.
    if feature_info['category'] in ['amount', 'velocity', 'frequency', 'recipient', 'timing', 'transaction_type']:
        existing_count += 1

print(f"Existing features retained: {existing_count}")

# Count new candidate features
new_count = 0
for feature_name, feature_info in existing_features.items():
    if feature_info['category'] in ['structuring', 'layering', 'funnel', 'rapid_movement', 'behavioral_change', 'severe']:
        new_count += 1

print(f"New candidate features: {new_count}")

# Calculate total
total_count = existing_count + new_count
print(f"Total features: {total_count}")
print()

# ============================================================================
# ARITHMETIC VERIFICATION
# ============================================================================

print("ARITHMETIC VERIFICATION:")
print("-" * 80)
print(f"Stage 14 claim: 34 - 1 + 25 = 57")
print(f"Correct arithmetic: 34 - 1 + 25 = 58")
print(f"Independent verification: {existing_count} + {new_count} = {total_count}")
print()

# ============================================================================
# DISCREPANCY RESOLUTION
# ============================================================================

print("DISCREPANCY RESOLUTION:")
print("-" * 80)

if total_count == 58:
    print("VERIFIED: Correct count is 58 features")
    print("Stage 14 documentation error: claimed 57 but calculated 58")
    print()
    print("RESOLUTION: Use 58 as the correct final feature count")
    print("REASON: 34 original - 1 removed (is_self_transfer) + 25 new = 58")
elif total_count == 57:
    print("VERIFIED: Correct count is 57 features")
    print("Stage 14 documentation is correct")
    print()
    print("RESOLUTION: Use 57 as the correct final feature count")
    print("REASON: One of the 25 candidate features is redundant or not intended for implementation")
else:
    print(f"UNEXPECTED: Count is {total_count}")
    print("Need manual investigation")

print()

# ============================================================================
# LIST ALL FEATURES FOR VERIFICATION
# ============================================================================

print("FEATURE LIST FOR VERIFICATION:")
print("-" * 80)

print(f"\nEXISTING FEATURES ({existing_count}):")
for feature_name, feature_info in existing_features.items():
    if feature_info['category'] in ['amount', 'velocity', 'frequency', 'recipient', 'timing', 'transaction_type']:
        print(f"  {feature_name}")

print(f"\nNEW CANDIDATE FEATURES ({new_count}):")
for feature_name, feature_info in existing_features.items():
    if feature_info['category'] in ['structuring', 'layering', 'funnel', 'rapid_movement', 'behavioral_change', 'severe']:
        print(f"  {feature_name}")

print()

# ============================================================================
# SAVE RESOLUTION
# ============================================================================

resolution = {
    "timestamp": datetime.now().isoformat(),
    "stage14_claim": "34 - 1 + 25 = 57",
    "correct_arithmetic": "34 - 1 + 25 = 58",
    "independent_verification": f"{existing_count} + {new_count} = {total_count}",
    "verified_count": total_count,
    "resolution": f"Use {total_count} as the correct final feature count",
    "reason": "34 original - 1 removed (is_self_transfer) + 25 new = 58"
}

with open('ml_stage15_arithmetic_resolution.json', 'w') as f:
    json.dump(resolution, f, indent=2)

print("=" * 80)
print("ARITHMETIC DISCREPANCY RESOLUTION COMPLETE")
print("=" * 80)
print(f"VERIFIED FINAL FEATURE COUNT: {total_count}")
print("Resolution saved to ml_stage15_arithmetic_resolution.json")
