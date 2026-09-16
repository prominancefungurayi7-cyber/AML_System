"""
Temporary script to analyze transaction simulation generator for audit purposes.
This script will NOT modify anything - only read and analyze.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transaction_simulation import (
    _simulation_plan,
    NORMAL_TRANSACTION_SCENARIOS,
    SUSPICIOUS_TRANSACTION_SCENARIOS,
    SUPER_SUSPICIOUS_TRANSACTION_SCENARIOS
)

print("=" * 80)
print("AML AI MODEL AUDIT - TRANSACTION SIMULATION ANALYSIS")
print("=" * 80)
print()

# Analyze class distribution
print("CLASS DISTRIBUTION ANALYSIS:")
print("-" * 80)

for count in [100, 1000, 7016]:
    labels = _simulation_plan(count)
    normal = labels.count("normal")
    suspicious = labels.count("suspicious")
    super_suspicious = labels.count("super_suspicious")
    print(f"  Requested {count} samples:")
    print(f"    normal: {normal} ({normal/count*100:.1f}%)")
    print(f"    suspicious: {suspicious} ({suspicious/count*100:.1f}%)")
    print(f"    super_suspicious: {super_suspicious} ({super_suspicious/count*100:.1f}%)")
    print()

# Analyze normal scenarios
print("NORMAL TRANSACTION SCENARIOS:")
print("-" * 80)
print(f"Count: {len(NORMAL_TRANSACTION_SCENARIOS)}")
for i, scenario in enumerate(NORMAL_TRANSACTION_SCENARIOS, 1):
    print(f"  {i}. {scenario.get('description', 'N/A')}")
    print(f"     Type: {scenario.get('type')}, Amount range: {scenario.get('amount')}, Channel: {scenario.get('channel')}")
print()

# Analyze suspicious scenarios
print("SUSPICIOUS TRANSACTION SCENARIOS:")
print("-" * 80)
print(f"Count: {len(SUSPICIOUS_TRANSACTION_SCENARIOS)}")
for i, scenario in enumerate(SUSPICIOUS_TRANSACTION_SCENARIOS, 1):
    print(f"  {i}. {scenario.get('description', 'N/A')}")
    print(f"     Type: {scenario.get('type')}, Amount range: {scenario.get('amount')}, Channel: {scenario.get('channel')}")
    print(f"     Reason: {scenario.get('reason', 'N/A')}")
print()

# Analyze super suspicious scenarios
print("SUPER SUSPICIOUS TRANSACTION SCENARIOS:")
print("-" * 80)
print(f"Count: {len(SUPER_SUSPICIOUS_TRANSACTION_SCENARIOS)}")
for i, scenario in enumerate(SUPER_SUSPICIOUS_TRANSACTION_SCENARIOS, 1):
    print(f"  {i}. {scenario.get('description', 'N/A')}")
    print(f"     Type: {scenario.get('type')}, Amount range: {scenario.get('amount')}, Channel: {scenario.get('channel')}")
    print(f"     Reason: {scenario.get('reason', 'N/A')}")
print()

print("=" * 80)
print("TRANSACTION SIMULATION ANALYSIS COMPLETE")
print("=" * 80)
