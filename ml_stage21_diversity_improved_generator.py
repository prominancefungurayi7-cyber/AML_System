"""
STAGE 21: Diversity-Improved AML Dataset Generator

This generator creates synthetic AML transactions with improved super_suspicious customer diversity.
The key improvement is distributing super_suspicious behavior across 50+ independent customers
rather than concentrating it in a small number of customers.
"""

import random
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

# Import from existing generator
from ml_stage3_generator import (
    GroundTruthLabel, AMLTypology, CustomerProfileType, TransactionType, Channel,
    CustomerProfile, CustomerProfileGenerator, TransactionGenerator
)

# Extend Transaction class to include destination_country
@dataclass
class Transaction:
    """Synthetic transaction with full metadata."""
    transaction_id: int
    customer_id: str
    sender_account: str
    receiver_account: str
    transaction_type: TransactionType
    amount: float
    timestamp: str
    channel: Channel
    description: str
    destination_country: str  # NEW: For cross-border features
    
    # Ground truth (NEVER used as feature)
    ground_truth_label: GroundTruthLabel
    aml_typologies: List[AMLTypology]
    scenario_id: str
    scenario_description: str
    
    # Features for ML (computed from history, NOT from ground truth)
    sender_avg_amount: float
    sender_max_amount: float
    sender_tx_count: int
    amount_to_sender_avg: float
    amount_to_sender_max: float
    sender_tx_count_24h: int
    sender_volume_24h: float
    amount_to_sender_volume_24h: float
    is_new_recipient: float
    same_day_count: float
    same_day_total: float
    same_recipient_count: float
    rapid_transfer_count: float
    
    # Additional metadata (hidden from model)
    generation_seed: int
    is_legitimate_high_value: bool
    is_borderline_case: bool

HIGH_RISK_COUNTRIES = {
    "IR", "KP", "MM", "RU", "SY", "YE", "ML", "BF", "SO", "CD", "IQ", "SD", "SS",
    "CU", "ZW", "VE", "AF", "LR", "HT"
}

LEGITIMATE_COUNTRIES = {
    "US", "GB", "DE", "FR", "CA", "AU", "JP", "CH", "NL", "SG", "ZA", "KE", "NG"
}


class DiversityImprovedDatasetGenerator:
    """Dataset generator with improved super-suspicious customer diversity."""
    
    def __init__(self, random_seed: int = 42):
        self.random_seed = random_seed
        random.seed(random_seed)
        np.random.seed(random_seed)
        self.customer_generator = CustomerProfileGenerator(random_seed)
        self.transaction_generator = TransactionGenerator(random_seed)
    
    def generate_dataset(
        self,
        num_customers: int = 200,
        transactions_per_customer: int = 50,
        class_distribution: Dict[str, float] = None,
        profile_distribution: Dict[CustomerProfileType, float] = None,
        min_super_suspicious_customers: int = 50  # NEW: Ensure at least 50 super_suspicious customers
    ) -> Tuple[List[Transaction], List[CustomerProfile]]:
        """Generate AML dataset with improved super_suspicious customer diversity."""
        
        # Default class distribution
        if class_distribution is None:
            class_distribution = {
                "normal": 0.70,
                "suspicious": 0.20,
                "super_suspicious": 0.10
            }
        
        # Default customer profile distribution
        if profile_distribution is None:
            profile_distribution = {
                CustomerProfileType.SALARIED_INDIVIDUAL: 0.30,
                CustomerProfileType.SMALL_BUSINESS: 0.20,
                CustomerProfileType.MEDIUM_BUSINESS: 0.15,
                CustomerProfileType.LARGE_BUSINESS: 0.05,
                CustomerProfileType.HIGH_NET_WORTH: 0.05,
                CustomerProfileType.INTERNATIONAL_BUSINESS: 0.05,
                CustomerProfileType.FREQUENT_DOMESTIC_SPENDER: 0.10,
                CustomerProfileType.OCCASIONAL_HIGH_VALUE: 0.05,
                CustomerProfileType.CASH_INTENSIVE_BUSINESS: 0.03,
                CustomerProfileType.STRUCTURING_BEHAVIOR: 0.01,
                CustomerProfileType.FUNNEL_ACCOUNT: 0.005,
                CustomerProfileType.LAYERING_BEHAVIOR: 0.005,
            }
        
        # Generate customer population
        print(f"Generating {num_customers} customers...")
        customers = self.customer_generator.generate_customer_population(
            num_customers, profile_distribution
        )
        
        # KEY IMPROVEMENT: Distribute super_suspicious behavior across many customers
        # Instead of concentrating it in a few customers
        print(f"Distributing super_suspicious behavior across at least {min_super_suspicious_customers} customers...")
        
        # Calculate how many customers should have each behavior type
        total_customers = len(customers)
        
        # Ensure minimum super_suspicious customers
        super_suspicious_customers = min_super_suspicious_customers
        
        # Ensure minimum suspicious customers (at least 50 for diversity)
        min_suspicious_customers = 50
        suspicious_customers = max(min_suspicious_customers, int(total_customers * class_distribution["suspicious"]))
        
        # Remaining customers are normal
        normal_customers = total_customers - super_suspicious_customers - suspicious_customers
        
        # Ensure we have enough customers for the distribution
        if normal_customers < 0:
            # Adjust to fit
            normal_customers = total_customers - super_suspicious_customers - min_suspicious_customers
            suspicious_customers = min_suspicious_customers
        
        print(f"Customer distribution: {normal_customers} normal, {suspicious_customers} suspicious, {super_suspicious_customers} super_suspicious")
        
        # Randomly assign customers to behavior types
        customer_indices = list(range(total_customers))
        random.shuffle(customer_indices)
        
        normal_indices = customer_indices[:normal_customers]
        suspicious_indices = customer_indices[normal_customers:normal_customers + suspicious_customers]
        super_suspicious_indices = customer_indices[normal_customers + suspicious_customers:normal_customers + suspicious_customers + super_suspicious_customers]
        
        # Assign AML typologies to customers
        for idx in suspicious_indices:
            customers[idx].aml_typologies = [AMLTypology.STRUCTURING]
            customers[idx].typology_severity = "mild"
        
        for idx in super_suspicious_indices:
            # Assign diverse typologies to super_suspicious customers
            typologies = [
                [AMLTypology.LAYERING],
                [AMLTypology.FUNNEL_ACCOUNT],
                [AMLTypology.RAPID_MOVEMENT],
                [AMLTypology.HIGH_RISK_JURISDICTION],
                [AMLTypology.MULTIPLE_TYPOLIES] if "MULTIPLE_TYPOLITIES" in [t.name for t in AMLTypology] else [AMLTypology.LAYERING, AMLTypology.FUNNEL_ACCOUNT],
            ]
            customers[idx].aml_typologies = random.choice(typologies)
            customers[idx].typology_severity = "severe"
        
        # Generate transactions for each customer
        print(f"Generating transactions for {len(customers)} customers...")
        all_transactions = []
        
        for i, customer in enumerate(customers):
            # Determine customer's overall behavior
            customer_transactions = []
            
            # Determine target class based on customer assignment
            if i in normal_indices:
                target_class = "normal"
            elif i in suspicious_indices:
                target_class = "suspicious"
            else:
                target_class = "super_suspicious"
            
            # Generate historical transactions
            for _ in range(transactions_per_customer):
                # Select scenario based on customer profile and target class
                scenario = self._select_scenario_for_customer(customer, target_class)
                
                # Generate transaction using base generator
                base_tx = self.transaction_generator.generate_transaction(
                    customer,
                    customer_transactions,
                    scenario
                )
                
                # Add destination_country (not in base Transaction class)
                # Select country based on customer profile and scenario
                is_high_risk_country = (AMLTypology.HIGH_RISK_JURISDICTION in customer.aml_typologies)
                if is_high_risk_country:
                    destination_country = random.choice(list(HIGH_RISK_COUNTRIES))
                elif random.random() < customer.international_ratio:
                    destination_country = random.choice(list(LEGITIMATE_COUNTRIES))
                else:
                    destination_country = "ZW"  # Domestic
                
                # Create extended Transaction with destination_country
                tx = Transaction(
                    transaction_id=base_tx.transaction_id,
                    customer_id=base_tx.customer_id,
                    sender_account=base_tx.sender_account,
                    receiver_account=base_tx.receiver_account,
                    transaction_type=base_tx.transaction_type,
                    amount=base_tx.amount,
                    timestamp=base_tx.timestamp,
                    channel=base_tx.channel,
                    description=base_tx.description,
                    destination_country=destination_country,
                    ground_truth_label=base_tx.ground_truth_label,
                    aml_typologies=base_tx.aml_typologies,
                    scenario_id=base_tx.scenario_id,
                    scenario_description=base_tx.scenario_description,
                    sender_avg_amount=base_tx.sender_avg_amount,
                    sender_max_amount=base_tx.sender_max_amount,
                    sender_tx_count=base_tx.sender_tx_count,
                    amount_to_sender_avg=base_tx.amount_to_sender_avg,
                    amount_to_sender_max=base_tx.amount_to_sender_max,
                    sender_tx_count_24h=base_tx.sender_tx_count_24h,
                    sender_volume_24h=base_tx.sender_volume_24h,
                    amount_to_sender_volume_24h=base_tx.amount_to_sender_volume_24h,
                    is_new_recipient=base_tx.is_new_recipient,
                    same_day_count=base_tx.same_day_count,
                    same_day_total=base_tx.same_day_total,
                    same_recipient_count=base_tx.same_recipient_count,
                    rapid_transfer_count=base_tx.rapid_transfer_count,
                    generation_seed=base_tx.generation_seed,
                    is_legitimate_high_value=base_tx.is_legitimate_high_value,
                    is_borderline_case=base_tx.is_borderline_case
                )
                
                customer_transactions.append(tx)
                all_transactions.append(tx)
            
            # Update customer's historical data
            customer.historical_transactions = [
                {
                    "amount": tx.amount,
                    "timestamp": tx.timestamp,
                    "receiver_account": tx.receiver_account,
                    "transaction_type": tx.transaction_type.value
                }
                for tx in customer_transactions
            ]
            customer.total_historical_count = len(customer_transactions)
        
        return all_transactions, customers
    
    def _select_scenario_for_customer(self, customer: CustomerProfile, target_class: str) -> str:
        """Select scenario based on customer profile and target class."""
        
        # High-risk customers get suspicious scenarios more often
        if customer.aml_typologies:
            if target_class == "super_suspicious" or customer.typology_severity == "severe":
                severe_scenarios = ["severe_structuring", "severe_layering", "severe_funnel", "multiple_typologies"]
                return random.choice(severe_scenarios)
            else:
                suspicious_scenarios = ["structuring", "layering", "funnel", "rapid_movement", "high_risk_country", "behavioral_change"]
                return random.choice(suspicious_scenarios)
        
        # Normal customers get scenarios based on target class
        if target_class == "normal":
            normal_scenarios = ["normal"] * 70 + ["legitimate_high_value"] * 15 + ["cash_deposit"] * 5 + ["cash_withdrawal"] * 5 + ["new_recipient"] * 5
            return random.choice(normal_scenarios)
        elif target_class == "suspicious":
            suspicious_scenarios = ["structuring", "layering", "funnel", "rapid_movement", "high_risk_country", "behavioral_change"]
            return random.choice(suspicious_scenarios)
        else:  # super_suspicious
            severe_scenarios = ["severe_structuring", "severe_layering", "severe_funnel", "multiple_typologies"]
            return random.choice(severe_scenarios)


def generate_diversity_improved_dataset(
    num_customers: int = 200,
    transactions_per_customer: int = 50,
    class_distribution: Dict[str, float] = None,
    profile_distribution: Dict[CustomerProfileType, float] = None,
    min_super_suspicious_customers: int = 50,
    random_seed: int = 42
) -> Tuple[List[Transaction], List[CustomerProfile]]:
    """Generate diversity-improved AML dataset."""
    generator = DiversityImprovedDatasetGenerator(random_seed)
    return generator.generate_dataset(
        num_customers,
        transactions_per_customer,
        class_distribution,
        profile_distribution,
        min_super_suspicious_customers
    )


def export_dataset_to_csv(
    transactions: List[Transaction],
    output_file: str = "ml_stage21_diversity_improved_dataset.csv"
):
    """Export transactions to CSV."""
    import csv
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write header (only include attributes that exist in Transaction class)
        header = [
            "transaction_id", "customer_id", "sender_account", "receiver_account", "amount",
            "transaction_type", "channel", "timestamp", "description", "destination_country",
            "sender_avg_amount", "sender_max_amount", "sender_tx_count",
            "amount_to_sender_avg", "amount_to_sender_max",
            "sender_tx_count_24h", "sender_volume_24h", "amount_to_sender_volume_24h",
            "is_new_recipient", "same_day_count", "same_day_total", "same_recipient_count",
            "rapid_transfer_count"
        ]
        writer.writerow(header)
        
        # Write transactions
        for tx in transactions:
            row = [
                tx.transaction_id,
                tx.customer_id,
                tx.sender_account,
                tx.receiver_account,
                tx.amount,
                tx.transaction_type.value,
                tx.channel.value,
                tx.timestamp,
                tx.description,
                tx.destination_country,
                tx.sender_avg_amount,
                tx.sender_max_amount,
                tx.sender_tx_count,
                tx.amount_to_sender_avg,
                tx.amount_to_sender_max,
                tx.sender_tx_count_24h,
                tx.sender_volume_24h,
                tx.amount_to_sender_volume_24h,
                tx.is_new_recipient,
                tx.same_day_count,
                tx.same_day_total,
                tx.same_recipient_count,
                tx.rapid_transfer_count
            ]
            writer.writerow(row)
    
    print(f"Exported {len(transactions)} transactions to {output_file}")


def export_ground_truth(
    transactions: List[Transaction],
    output_file: str = "ml_stage21_diversity_improved_ground_truth.json"
):
    """Export ground truth labels."""
    ground_truth = []
    
    for tx in transactions:
        gt = {
            "transaction_id": tx.transaction_id,
            "ground_truth_label": tx.ground_truth_label.value,
            "aml_typologies": [t.value for t in tx.aml_typologies],
            "scenario_id": tx.scenario_id,
            "scenario_description": tx.scenario_description
        }
        ground_truth.append(gt)
    
    with open(output_file, 'w') as f:
        json.dump(ground_truth, f, indent=2)
    
    print(f"Exported ground truth for {len(transactions)} transactions to {output_file}")


if __name__ == "__main__":
    print("=" * 80)
    print("STAGE 21: DIVERSITY-IMPROVED DATASET GENERATION")
    print("=" * 80)
    print()
    
    # Generate diversity-improved dataset
    transactions, customers = generate_diversity_improved_dataset(
        num_customers=200,
        transactions_per_customer=50,
        min_super_suspicious_customers=50,
        random_seed=42
    )
    
    print(f"Generated {len(transactions)} transactions from {len(customers)} customers")
    print()
    
    # Analyze customer distribution by class
    customer_class_distribution = {}
    for customer in customers:
        # Determine customer's primary class based on typologies
        if customer.aml_typologies:
            if customer.typology_severity == "severe":
                primary_class = "super_suspicious"
            else:
                primary_class = "suspicious"
        else:
            primary_class = "normal"
        
        if primary_class not in customer_class_distribution:
            customer_class_distribution[primary_class] = 0
        customer_class_distribution[primary_class] += 1
    
    print("Customer distribution by class:")
    for class_name, count in customer_class_distribution.items():
        print(f"  {class_name}: {count} customers")
    print()
    
    # Analyze transaction distribution by class
    transaction_class_distribution = {}
    for tx in transactions:
        label = tx.ground_truth_label.value
        if label not in transaction_class_distribution:
            transaction_class_distribution[label] = 0
        transaction_class_distribution[label] += 1
    
    print("Transaction distribution by class:")
    for class_name, count in transaction_class_distribution.items():
        print(f"  {class_name}: {count} transactions")
    print()
    
    # Export dataset
    export_dataset_to_csv(transactions, "ml_stage21_diversity_improved_dataset.csv")
    export_ground_truth(transactions, "ml_stage21_diversity_improved_ground_truth.json")
    
    print("=" * 80)
    print("DIVERSITY-IMPROVED DATASET GENERATION COMPLETE")
    print("=" * 80)
