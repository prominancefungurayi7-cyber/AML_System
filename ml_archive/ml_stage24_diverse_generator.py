"""
STAGE 24: Diverse AML Dataset Generator

Implements the Stage 23 dataset design with:
- Genuine behavioral diversity
- AML typology diversity
- Hard negatives
- Independent ground truth
- Realistic class distribution (88% normal / 8% suspicious / 4% super-suspicious)
"""

import random
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json

# Import base types from Stage 3 generator
from ml_stage3_generator import (
    GroundTruthLabel, AMLTypology, CustomerProfileType, TransactionType, Channel,
    HIGH_RISK_COUNTRIES, LEGITIMATE_COUNTRIES
)

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

DOMESTIC_COUNTRY = "ZW"
CTR_THRESHOLD = 10000.0


class SignalStrength(Enum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


@dataclass
class BehavioralProfile:
    """Multi-dimensional behavioral profile for a customer."""
    customer_id: str
    
    # Amount behavior
    amount_mean: float
    amount_std: float
    amount_volatility: str  # low/medium/high
    
    # Frequency behavior
    daily_tx_mean: float
    frequency_variance: float
    peak_activity: str  # morning/afternoon/evening/random
    
    # Timing behavior
    business_hours_preference: float  # 0.0 - 1.0
    weekend_activity: float  # 0.0 - 1.0
    timezone_alignment: str  # domestic/international/mixed
    
    # Recipient behavior
    recipient_diversity: int  # number of unique recipients
    recipient_loyalty: str  # high/low
    geographic_distribution: str  # domestic/international/mixed
    
    # Transaction type preferences
    type_preferences: Dict[str, float]  # deposit/withdraw/transfer ratios
    
    # Channel preferences
    channel_preferences: Dict[str, float]  # online/mobile/atm/branch/card ratios
    
    # Cross-border behavior
    international_ratio: float  # 0.0 - 0.5
    high_risk_preference: float  # 0.0 - 0.2
    country_diversity: int  # number of countries
    
    # Account activity
    account_age_days: int
    activity_level: str  # dormant/low/medium/high
    seasonality: str  # none/monthly/quarterly
    
    # Behavioral changes
    change_frequency: str  # never/rarely/occasionally/frequently
    change_magnitude: str  # small/medium/large
    change_types: List[str]  # amount/frequency/recipient/timing/country


class BehavioralProfileGenerator:
    """Generate diverse behavioral profiles."""
    
    def __init__(self, random_seed: int = RANDOM_SEED):
        self.random_seed = random_seed
        random.seed(random_seed)
        np.random.seed(random_seed)
    
    def generate_profile(self, customer_id: str, customer_class: str) -> BehavioralProfile:
        """Generate a behavioral profile for a customer."""
        
        # Amount behavior - log-normal distribution
        if customer_class == "normal":
            amount_mean = np.random.lognormal(7.0, 1.0)  # ~$1,000 - $100,000
        elif customer_class == "suspicious":
            amount_mean = np.random.lognormal(6.5, 1.2)  # ~$500 - $50,000
        else:  # super_suspicious
            amount_mean = np.random.lognormal(8.0, 1.5)  # ~$3,000 - $300,000
        
        amount_std = amount_mean * np.random.uniform(0.2, 2.0)
        amount_volatility = random.choice(["low", "medium", "high"])
        
        # Frequency behavior
        if customer_class == "normal":
            daily_tx_mean = np.random.uniform(0.5, 3.0)
        elif customer_class == "suspicious":
            daily_tx_mean = np.random.uniform(1.0, 5.0)
        else:
            daily_tx_mean = np.random.uniform(2.0, 10.0)
        
        frequency_variance = np.random.uniform(0.5, 2.0)
        peak_activity = random.choice(["morning", "afternoon", "evening", "random"])
        
        # Timing behavior
        business_hours_preference = np.random.uniform(0.0, 1.0)
        weekend_activity = np.random.uniform(0.0, 1.0)
        timezone_alignment = random.choice(["domestic", "international", "mixed"])
        
        # Recipient behavior
        if customer_class == "normal":
            recipient_diversity = np.random.randint(1, 20)
        elif customer_class == "suspicious":
            recipient_diversity = np.random.randint(5, 50)
        else:
            recipient_diversity = np.random.randint(10, 100)
        
        recipient_loyalty = random.choice(["high", "low"])
        geographic_distribution = random.choice(["domestic", "international", "mixed"])
        
        # Transaction type preferences
        type_preferences = {
            "deposit": np.random.uniform(0.1, 0.4),
            "withdraw": np.random.uniform(0.1, 0.4),
            "transfer": np.random.uniform(0.2, 0.8)
        }
        # Normalize
        total = sum(type_preferences.values())
        type_preferences = {k: v/total for k, v in type_preferences.items()}
        
        # Channel preferences
        channel_preferences = {
            "online": np.random.uniform(0.1, 0.5),
            "mobile": np.random.uniform(0.1, 0.5),
            "atm": np.random.uniform(0.0, 0.3),
            "branch": np.random.uniform(0.0, 0.3),
            "card": np.random.uniform(0.0, 0.3)
        }
        # Normalize
        total = sum(channel_preferences.values())
        channel_preferences = {k: v/total for k, v in channel_preferences.items()}
        
        # Cross-border behavior
        if customer_class == "normal":
            international_ratio = np.random.uniform(0.0, 0.1)
            high_risk_preference = np.random.uniform(0.0, 0.05)
            country_diversity = np.random.randint(1, 3)
        elif customer_class == "suspicious":
            international_ratio = np.random.uniform(0.0, 0.3)
            high_risk_preference = np.random.uniform(0.0, 0.15)
            country_diversity = np.random.randint(1, 5)
        else:
            international_ratio = np.random.uniform(0.1, 0.5)
            high_risk_preference = np.random.uniform(0.05, 0.2)
            country_diversity = np.random.randint(2, 10)
        
        # Account activity
        account_age_days = np.random.randint(30, 3650)
        activity_level = random.choice(["dormant", "low", "medium", "high"])
        seasonality = random.choice(["none", "monthly", "quarterly"])
        
        # Behavioral changes
        change_frequency = random.choice(["never", "rarely", "occasionally", "frequently"])
        change_magnitude = random.choice(["small", "medium", "large"])
        change_types = random.sample(
            ["amount", "frequency", "recipient", "timing", "country"],
            k=np.random.randint(1, 4)
        )
        
        return BehavioralProfile(
            customer_id=customer_id,
            amount_mean=amount_mean,
            amount_std=amount_std,
            amount_volatility=amount_volatility,
            daily_tx_mean=daily_tx_mean,
            frequency_variance=frequency_variance,
            peak_activity=peak_activity,
            business_hours_preference=business_hours_preference,
            weekend_activity=weekend_activity,
            timezone_alignment=timezone_alignment,
            recipient_diversity=recipient_diversity,
            recipient_loyalty=recipient_loyalty,
            geographic_distribution=geographic_distribution,
            type_preferences=type_preferences,
            channel_preferences=channel_preferences,
            international_ratio=international_ratio,
            high_risk_preference=high_risk_preference,
            country_diversity=country_diversity,
            account_age_days=account_age_days,
            activity_level=activity_level,
            seasonality=seasonality,
            change_frequency=change_frequency,
            change_magnitude=change_magnitude,
            change_types=change_types
        )


class AMLScenarioGenerator:
    """Generate AML scenarios with typology diversity."""
    
    def __init__(self, random_seed: int = RANDOM_SEED):
        self.random_seed = random_seed
        random.seed(random_seed)
        np.random.seed(random_seed)
    
    def assign_typologies(self, customer_class: str) -> Tuple[List[AMLTypology], SignalStrength]:
        """Assign AML typologies and signal strength."""
        
        if customer_class == "normal":
            return [], SignalStrength.WEAK
        
        # Determine typology count
        typology_roll = np.random.random()
        if typology_roll < 0.4:
            typology_count = 1  # Single
        elif typology_roll < 0.8:
            typology_count = 2  # Dual
        else:
            typology_count = 3  # Multi
        
        # Select typologies
        all_typologies = [
            AMLTypology.RAPID_MOVEMENT,
            AMLTypology.STRUCTURING,
            AMLTypology.HIGH_RISK_JURISDICTION,
            AMLTypology.FUNNEL_ACCOUNT,
            AMLTypology.LAYERING,
            AMLTypology.BEHAVIORAL_CHANGE
        ]
        
        if customer_class == "suspicious":
            # Suspicious gets simpler typologies
            available = [
                AMLTypology.STRUCTURING,
                AMLTypology.HIGH_RISK_JURISDICTION,
                AMLTypology.BEHAVIORAL_CHANGE
            ]
        else:  # super_suspicious
            # Super-suspicious gets all typologies
            available = all_typologies
        
        selected_typologies = random.sample(available, min(typology_count, len(available)))
        
        # Determine signal strength
        strength_roll = np.random.random()
        if strength_roll < 0.3:
            signal_strength = SignalStrength.STRONG
        elif strength_roll < 0.8:
            signal_strength = SignalStrength.MODERATE
        else:
            signal_strength = SignalStrength.WEAK
        
        return selected_typologies, signal_strength


class DiverseAMLGenerator:
    """Generate diverse AML dataset."""
    
    def __init__(self, random_seed: int = RANDOM_SEED):
        self.random_seed = random_seed
        random.seed(random_seed)
        np.random.seed(random_seed)
        
        self.profile_generator = BehavioralProfileGenerator(random_seed)
        self.scenario_generator = AMLScenarioGenerator(random_seed)
        self.transaction_counter = 0
    
    def generate_dataset(
        self,
        num_customers: int = 300,
        transactions_per_customer: int = 50,
        normal_customers: int = 240,
        suspicious_customers: int = 40,
        super_suspicious_customers: int = 20,
        customer_id_offset: int = 0
    ) -> Tuple[List[Dict], List[Dict]]:
        """Generate diverse AML dataset."""
        
        print(f"Generating dataset with {num_customers} customers...")
        print(f"  Normal: {normal_customers}")
        print(f"  Suspicious: {suspicious_customers}")
        print(f"  Super-suspicious: {super_suspicious_customers}")
        
        # Assign customer classes
        customer_indices = list(range(num_customers))
        random.shuffle(customer_indices)
        
        normal_indices = customer_indices[:normal_customers]
        suspicious_indices = customer_indices[normal_customers:normal_customers + suspicious_customers]
        super_suspicious_indices = customer_indices[normal_customers + suspicious_customers:]
        
        all_transactions = []
        all_ground_truth = []
        
        for i in range(num_customers):
            customer_id = f"CUST{i+1+customer_id_offset:05d}"
            
            # Determine customer class
            if i in normal_indices:
                customer_class = "normal"
            elif i in suspicious_indices:
                customer_class = "suspicious"
            else:
                customer_class = "super_suspicious"
            
            # Generate behavioral profile
            profile = self.profile_generator.generate_profile(customer_id, customer_class)
            
            # Assign AML typologies
            typologies, signal_strength = self.scenario_generator.assign_typologies(customer_class)
            
            # Generate transactions
            customer_transactions = self._generate_customer_transactions(
                customer_id, profile, customer_class, typologies, signal_strength, transactions_per_customer
            )
            
            all_transactions.extend(customer_transactions)
            
            # Generate ground truth
            for tx in customer_transactions:
                gt = {
                    "transaction_id": tx["transaction_id"],
                    "ground_truth_label": customer_class,
                    "aml_typologies": [t.value for t in typologies],
                    "scenario_id": f"{customer_class}_{signal_strength.value}",
                    "scenario_description": f"{customer_class} customer with {signal_strength.value} signal",
                    "signal_strength": signal_strength.value,
                    "customer_profile": {
                        "amount_mean": profile.amount_mean,
                        "daily_tx_mean": profile.daily_tx_mean,
                        "international_ratio": profile.international_ratio
                    }
                }
                all_ground_truth.append(gt)
        
        print(f"Generated {len(all_transactions)} transactions")
        return all_transactions, all_ground_truth
    
    def _generate_customer_transactions(
        self,
        customer_id: str,
        profile: BehavioralProfile,
        customer_class: str,
        typologies: List[AMLTypology],
        signal_strength: SignalStrength,
        num_transactions: int
    ) -> List[Dict]:
        """Generate transactions for a customer."""
        
        transactions = []
        base_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        
        # Generate historical baseline (first 30% of transactions)
        baseline_count = int(num_transactions * 0.3)
        
        for i in range(num_transactions):
            self.transaction_counter += 1
            tx_id = self.transaction_counter
            
            # Determine if this is a baseline or labeled transaction
            is_baseline = i < baseline_count
            
            # Generate timestamp
            days_offset = np.random.randint(0, 90)
            hour = self._generate_hour(profile, is_baseline)
            timestamp = base_date + timedelta(days=days_offset, hours=hour)
            
            # Generate amount
            amount = self._generate_amount(profile, customer_class, typologies, signal_strength, is_baseline)
            
            # Generate transaction type
            tx_type = self._generate_transaction_type(profile)
            
            # Generate channel
            channel = self._generate_channel(profile)
            
            # Generate destination country
            destination_country = self._generate_destination_country(profile, typologies, is_baseline)
            
            # Generate receiver account
            receiver_account = f"ACC{np.random.randint(10000, 99999)}"
            
            # Generate description
            description = f"Transaction {tx_id}"
            
            # Calculate historical features (simplified for now)
            historical_txs = [
                t for t in transactions
                if datetime.fromisoformat(t["timestamp"].replace('Z', '+00:00')) < timestamp
            ]
            
            sender_avg_amount = np.mean([t["amount"] for t in historical_txs]) if historical_txs else amount
            sender_max_amount = max([t["amount"] for t in historical_txs]) if historical_txs else amount
            sender_tx_count = len(historical_txs)
            
            # Build transaction
            tx = {
                "transaction_id": tx_id,
                "customer_id": customer_id,
                "sender_account": customer_id,
                "receiver_account": receiver_account,
                "amount": amount,
                "transaction_type": tx_type.value,
                "channel": channel.value,
                "timestamp": timestamp.isoformat(),
                "description": description,
                "destination_country": destination_country,
                "sender_avg_amount": sender_avg_amount,
                "sender_max_amount": sender_max_amount,
                "sender_tx_count": sender_tx_count,
                "amount_to_sender_avg": amount / sender_avg_amount if sender_avg_amount > 0 else 1.0,
                "amount_to_sender_max": amount / sender_max_amount if sender_max_amount > 0 else 1.0
            }
            
            transactions.append(tx)
        
        # Sort by timestamp
        transactions.sort(key=lambda x: datetime.fromisoformat(x["timestamp"].replace('Z', '+00:00')))
        
        # Recalculate historical features after sorting
        for i, tx in enumerate(transactions):
            historical_txs = transactions[:i]
            if historical_txs:
                tx["sender_avg_amount"] = np.mean([t["amount"] for t in historical_txs])
                tx["sender_max_amount"] = max([t["amount"] for t in historical_txs])
                tx["sender_tx_count"] = len(historical_txs)
                tx["amount_to_sender_avg"] = tx["amount"] / tx["sender_avg_amount"]
                tx["amount_to_sender_max"] = tx["amount"] / tx["sender_max_amount"]
        
        return transactions
    
    def _generate_hour(self, profile: BehavioralProfile, is_baseline: bool) -> int:
        """Generate transaction hour based on profile."""
        if is_baseline:
            # Baseline follows profile
            if profile.peak_activity == "morning":
                hour_range = (8, 12)
            elif profile.peak_activity == "afternoon":
                hour_range = (13, 17)
            elif profile.peak_activity == "evening":
                hour_range = (18, 22)
            else:
                hour_range = (0, 23)
        else:
            # Labeled transactions may have unusual timing for suspicious customers
            hour_range = (0, 23)
        
        return np.random.randint(*hour_range)
    
    def _generate_amount(
        self,
        profile: BehavioralProfile,
        customer_class: str,
        typologies: List[AMLTypology],
        signal_strength: SignalStrength,
        is_baseline: bool
    ) -> float:
        """Generate transaction amount."""
        
        if is_baseline:
            # Baseline follows profile
            amount = np.random.normal(profile.amount_mean, profile.amount_std)
        else:
            # Labeled transactions apply AML typologies
            amount = np.random.normal(profile.amount_mean, profile.amount_std)
            
            # Apply typology-specific modifications
            if AMLTypology.STRUCTURING in typologies:
                # Near CTR threshold
                if signal_strength == SignalStrength.STRONG:
                    amount = np.random.uniform(8500, 9999)
                elif signal_strength == SignalStrength.MODERATE:
                    if np.random.random() < 0.5:
                        amount = np.random.uniform(8500, 9999)
            
            if AMLTypology.RAPID_MOVEMENT in typologies:
                # High amounts
                if signal_strength == SignalStrength.STRONG:
                    amount *= 2.0
                elif signal_strength == SignalStrength.MODERATE:
                    amount *= 1.5
        
        # Ensure positive
        amount = max(100.0, amount)
        
        return round(amount, 2)
    
    def _generate_transaction_type(self, profile: BehavioralProfile) -> TransactionType:
        """Generate transaction type based on profile preferences."""
        types = list(profile.type_preferences.keys())
        probs = list(profile.type_preferences.values())
        return TransactionType(np.random.choice(types, p=probs))
    
    def _generate_channel(self, profile: BehavioralProfile) -> Channel:
        """Generate channel based on profile preferences."""
        channels = list(profile.channel_preferences.keys())
        probs = list(profile.channel_preferences.values())
        return Channel(np.random.choice(channels, p=probs))
    
    def _generate_destination_country(
        self,
        profile: BehavioralProfile,
        typologies: List[AMLTypology],
        is_baseline: bool
    ) -> str:
        """Generate destination country."""
        
        if is_baseline:
            # Baseline follows profile
            if np.random.random() < profile.international_ratio:
                return random.choice(list(LEGITIMATE_COUNTRIES))
            else:
                return DOMESTIC_COUNTRY
        else:
            # Labeled transactions apply AML typologies
            if AMLTypology.HIGH_RISK_JURISDICTION in typologies:
                if np.random.random() < profile.high_risk_preference:
                    return random.choice(list(HIGH_RISK_COUNTRIES))
            
            if np.random.random() < profile.international_ratio:
                return random.choice(list(LEGITIMATE_COUNTRIES))
            else:
                return DOMESTIC_COUNTRY


def export_dataset(
    transactions: List[Dict],
    ground_truth: List[Dict],
    dataset_file: str = "ml_stage24_diverse_dataset.csv",
    ground_truth_file: str = "ml_stage24_diverse_ground_truth.json"
):
    """Export dataset and ground truth."""
    
    print(f"Exporting dataset to {dataset_file}...")
    
    # Export CSV
    import csv
    with open(dataset_file, 'w', newline='') as f:
        writer = csv.writer(f)
        header = [
            "transaction_id", "customer_id", "sender_account", "receiver_account", "amount",
            "transaction_type", "channel", "timestamp", "description", "destination_country",
            "sender_avg_amount", "sender_max_amount", "sender_tx_count",
            "amount_to_sender_avg", "amount_to_sender_max"
        ]
        writer.writerow(header)
        
        for tx in transactions:
            row = [
                tx["transaction_id"],
                tx["customer_id"],
                tx["sender_account"],
                tx["receiver_account"],
                tx["amount"],
                tx["transaction_type"],
                tx["channel"],
                tx["timestamp"],
                tx["description"],
                tx["destination_country"],
                tx["sender_avg_amount"],
                tx["sender_max_amount"],
                tx["sender_tx_count"],
                tx["amount_to_sender_avg"],
                tx["amount_to_sender_max"]
            ]
            writer.writerow(row)
    
    # Export ground truth
    with open(ground_truth_file, 'w') as f:
        json.dump(ground_truth, f, indent=2)
    
    print(f"Exported {len(transactions)} transactions")
    print(f"Ground truth exported to {ground_truth_file}")


if __name__ == "__main__":
    print("=" * 80)
    print("STAGE 24: DIVERSE AML DATASET GENERATOR")
    print("=" * 80)
    print()
    
    generator = DiverseAMLGenerator()
    transactions, ground_truth = generator.generate_dataset(
        num_customers=300,
        transactions_per_customer=50,
        normal_customers=240,
        suspicious_customers=40,
        super_suspicious_customers=20
    )
    
    export_dataset(transactions, ground_truth)
    
    print()
    print("=" * 80)
    print("DATASET GENERATION COMPLETE")
    print("=" * 80)
