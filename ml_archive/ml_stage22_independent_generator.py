"""
STAGE 22: Independent Generalization Test Generator

This script creates a NEW independent evaluation dataset with:
- Entirely new customers (not from Stage 21)
- New transactions
- Same intended behavioural classes
- Same Chapter 1 AML scenarios
- No transactions copied from Stage 21
"""

import random
import numpy as np
import json
import csv
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
from dataclasses import dataclass

# Import from Stage 21 generator
from ml_stage21_diversity_improved_generator import (
    GroundTruthLabel, AMLTypology, CustomerProfileType, TransactionType, Channel,
    CustomerProfile, CustomerProfileGenerator, TransactionGenerator,
    Transaction, HIGH_RISK_COUNTRIES, LEGITIMATE_COUNTRIES
)

# Use different random seed for independence
INDEPENDENT_SEED = 999
random.seed(INDEPENDENT_SEED)
np.random.seed(INDEPENDENT_SEED)


class IndependentDatasetGenerator:
    """Generate independent evaluation dataset."""
    
    def __init__(self, random_seed: int = INDEPENDENT_SEED):
        self.random_seed = random_seed
        random.seed(random_seed)
        np.random.seed(random_seed)
        
        self.customer_generator = CustomerProfileGenerator(random_seed=random_seed)
        self.transaction_generator = TransactionGenerator(random_seed=random_seed)
        self.transaction_counter = 0
    
    def generate_independent_dataset(
        self,
        num_customers: int = 200,
        transactions_per_customer: int = 50,
        super_suspicious_min: int = 50,
        suspicious_min: int = 50
    ) -> List[Transaction]:
        """Generate independent dataset with new customers."""
        print(f"Generating independent dataset with {num_customers} customers...")
        
        # Generate customers (different seed = different customers)
        profile_distribution = {
            CustomerProfileType.SALARIED_INDIVIDUAL: 0.5,
            CustomerProfileType.SMALL_BUSINESS: 0.3,
            CustomerProfileType.MEDIUM_BUSINESS: 0.15,
            CustomerProfileType.HIGH_NET_WORTH: 0.05
        }
        customers = self.customer_generator.generate_customer_population(num_customers, profile_distribution)
        
        # Assign target classes (same distribution as Stage 21)
        customer_indices = list(range(num_customers))
        random.shuffle(customer_indices)
        
        super_suspicious_indices = customer_indices[:super_suspicious_min]
        suspicious_indices = customer_indices[super_suspicious_min:super_suspicious_min + suspicious_min]
        
        all_transactions = []
        
        for i, customer in enumerate(customers):
            # Determine target class
            if i in super_suspicious_indices:
                target_class = "super_suspicious"
            elif i in suspicious_indices:
                target_class = "suspicious"
            else:
                target_class = "normal"
            
            # Assign AML typologies based on class
            if target_class == "super_suspicious":
                customer.aml_typologies = [
                    AMLTypology.RAPID_MOVEMENT,
                    AMLTypology.FUNNEL_ACCOUNT,
                    AMLTypology.STRUCTURING
                ]
            elif target_class == "suspicious":
                customer.aml_typologies = [
                    AMLTypology.STRUCTURING,
                    AMLTypology.HIGH_RISK_JURISDICTION
                ]
            else:
                customer.aml_typologies = []
            
            # Generate transactions
            customer_transactions = []
            for _ in range(transactions_per_customer):
                # Select scenario
                scenario = self._select_scenario_for_customer(customer, target_class)
                
                # Generate transaction
                base_tx = self.transaction_generator.generate_transaction(
                    customer,
                    customer_transactions,
                    scenario
                )
                
                # Add destination_country
                is_high_risk_country = (AMLTypology.HIGH_RISK_JURISDICTION in customer.aml_typologies)
                if is_high_risk_country:
                    destination_country = random.choice(list(HIGH_RISK_COUNTRIES))
                elif random.random() < customer.international_ratio:
                    destination_country = random.choice(list(LEGITIMATE_COUNTRIES))
                else:
                    destination_country = "ZW"
                
                # Create extended Transaction
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
        
        print(f"Generated {len(all_transactions)} transactions from {num_customers} customers")
        return all_transactions
    
    def _select_scenario_for_customer(self, customer: CustomerProfile, target_class: str) -> str:
        """Select scenario based on customer profile and target class."""
        if target_class == "normal":
            return "normal"
        elif target_class == "suspicious":
            scenarios = ["structuring", "high_risk_jurisdiction", "cash_deposit"]
            return random.choice(scenarios)
        else:  # super_suspicious
            scenarios = ["rapid_movement", "funnel_account", "layering", "multiple_typologies"]
            return random.choice(scenarios)


def export_independent_dataset(
    transactions: List[Transaction],
    dataset_file: str = "ml_stage22_independent_dataset.csv",
    ground_truth_file: str = "ml_stage22_independent_ground_truth.json"
):
    """Export independent dataset."""
    print(f"Exporting independent dataset to {dataset_file}...")
    
    # Export CSV
    with open(dataset_file, 'w', newline='') as f:
        writer = csv.writer(f)
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
    
    # Export ground truth
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
    
    with open(ground_truth_file, 'w') as f:
        json.dump(ground_truth, f, indent=2)
    
    print(f"Exported {len(transactions)} transactions")
    print(f"Ground truth exported to {ground_truth_file}")


if __name__ == "__main__":
    print("=" * 80)
    print("STAGE 22: INDEPENDENT GENERALIZATION TEST GENERATOR")
    print("=" * 80)
    print()
    
    generator = IndependentDatasetGenerator()
    transactions = generator.generate_independent_dataset(
        num_customers=200,
        transactions_per_customer=50,
        super_suspicious_min=50,
        suspicious_min=50
    )
    
    export_independent_dataset(transactions)
    
    print()
    print("=" * 80)
    print("INDEPENDENT DATASET GENERATION COMPLETE")
    print("=" * 80)
