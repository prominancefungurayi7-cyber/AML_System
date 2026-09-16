"""
STAGE 3: Redesigned AML Dataset Generator

This generator creates synthetic AML transactions with:
- Customer behavioral profiles (not isolated transactions)
- Independent ground-truth labels (NOT from rule engine)
- Realistic class overlap
- Sequence-based AML typologies
- Configurable class distributions
- Edge cases and borderline scenarios
- Hidden metadata for evaluation
"""

import random
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class GroundTruthLabel(Enum):
    NORMAL = "normal"
    SUSPICIOUS = "suspicious"
    SUPER_SUSPICIOUS = "super_suspicious"


class AMLTypology(Enum):
    NONE = "none"
    STRUCTURING = "structuring"
    LAYERING = "layering"
    FUNNEL_ACCOUNT = "funnel_account"
    RAPID_MOVEMENT = "rapid_movement"
    UNUSUAL_RECIPIENT_NETWORK = "unusual_recipient_network"
    SHELL_COMPANY = "shell_company"
    HIGH_RISK_JURISDICTION = "high_risk_jurisdiction"
    BEHAVIORAL_CHANGE = "behavioral_change"
    CASH_INTENSIVE = "cash_intensive"
    CRYPTO_RELATED = "crypto_related"
    TRADE_BASED = "trade_based"


class CustomerProfileType(Enum):
    SALARIED_INDIVIDUAL = "salaried_individual"
    SMALL_BUSINESS = "small_business"
    MEDIUM_BUSINESS = "medium_business"
    LARGE_BUSINESS = "large_business"
    HIGH_NET_WORTH = "high_net_worth"
    INTERNATIONAL_BUSINESS = "international_business"
    FREQUENT_DOMESTIC_SPENDER = "frequent_domestic_spender"
    OCCASIONAL_HIGH_VALUE = "occasional_high_value"
    CASH_INTENSIVE_BUSINESS = "cash_intensive_business"
    STRUCTURING_BEHAVIOR = "structuring_behavior"
    FUNNEL_ACCOUNT = "funnel_account"
    LAYERING_BEHAVIOR = "layering_behavior"


class TransactionType(Enum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    TRANSFER = "transfer"


class Channel(Enum):
    ONLINE = "online"
    MOBILE = "mobile"
    ATM = "atm"
    BRANCH = "branch"
    CARD = "card"
    ACH = "ach"
    WIRE = "wire"
    SWIFT = "swift"


# High-risk jurisdictions (FATF grey/black list, high-risk countries)
HIGH_RISK_COUNTRIES = {
    "IR", "KP", "MM", "RU", "SY", "YE", "ML", "BF", "SO", "CD", "IQ", "SD", "SS",
    "CU", "ZW", "VE", "AF", "LR", "HT"
}

# Legitimate countries for comparison
LEGITIMATE_COUNTRIES = {
    "US", "GB", "DE", "FR", "CA", "AU", "JP", "CH", "NL", "SG", "ZA", "KE", "NG"
}


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class CustomerProfile:
    """Synthetic customer with behavioral characteristics."""
    customer_id: str
    account_number: str
    profile_type: CustomerProfileType
    wealth_segment: str  # average, high, ultra
    base_balance: float
    typical_amount_mean: float
    typical_amount_std: float
    typical_frequency_daily: float
    preferred_channels: List[Channel]
    preferred_recipients: List[str]  # Account numbers
    international_ratio: float
    cash_ratio: float
    business_hours_only: bool
    risk_level: str  # standard, medium, high (for legitimate customers)
    
    # Behavioral characteristics
    recipient_diversity: float  # 0-1, how many different recipients
    amount_variability: float  # 0-1, how much amounts vary
    temporal_regularity: float  # 0-1, how regular timing is
    
    # AML typology indicators (if applicable)
    aml_typologies: List[AMLTypology] = field(default_factory=list)
    typology_severity: str = "none"  # mild, moderate, severe
    
    # Historical data (for feature generation)
    historical_transactions: List[Dict[str, Any]] = field(default_factory=list)
    total_historical_count: int = 0


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


# ============================================================================
# CUSTOMER PROFILE GENERATOR
# ============================================================================

class CustomerProfileGenerator:
    """Generate realistic customer profiles."""
    
    def __init__(self, random_seed: int = 42):
        self.random_seed = random_seed
        random.seed(random_seed)
        np.random.seed(random_seed)
        self.customer_counter = 0
    
    def generate_customer(
        self,
        profile_type: CustomerProfileType,
        wealth_segment: str = "average"
    ) -> CustomerProfile:
        """Generate a single customer profile."""
        self.customer_counter += 1
        customer_id = f"CUST{self.customer_counter:05d}"
        account_number = f"ACC{self.customer_counter:06d}"
        
        # Set base characteristics based on profile type
        if profile_type == CustomerProfileType.SALARIED_INDIVIDUAL:
            base_balance = random.uniform(2000, 15000)
            typical_amount_mean = random.uniform(50, 500)
            typical_amount_std = typical_amount_mean * 0.3
            typical_frequency_daily = random.uniform(0.5, 3.0)
            preferred_channels = [Channel.ONLINE, Channel.MOBILE, Channel.CARD]
            international_ratio = random.uniform(0.0, 0.1)
            cash_ratio = random.uniform(0.1, 0.3)
            business_hours_only = True
            risk_level = "standard"
            recipient_diversity = random.uniform(0.1, 0.3)
            amount_variability = random.uniform(0.2, 0.5)
            temporal_regularity = random.uniform(0.7, 0.9)
            
        elif profile_type == CustomerProfileType.SMALL_BUSINESS:
            base_balance = random.uniform(10000, 100000)
            typical_amount_mean = random.uniform(200, 2000)
            typical_amount_std = typical_amount_mean * 0.5
            typical_frequency_daily = random.uniform(2.0, 10.0)
            preferred_channels = [Channel.ONLINE, Channel.WIRE, Channel.ACH]
            international_ratio = random.uniform(0.05, 0.2)
            cash_ratio = random.uniform(0.2, 0.4)
            business_hours_only = True
            risk_level = "standard"
            recipient_diversity = random.uniform(0.3, 0.6)
            amount_variability = random.uniform(0.4, 0.7)
            temporal_regularity = random.uniform(0.5, 0.8)
            
        elif profile_type == CustomerProfileType.MEDIUM_BUSINESS:
            base_balance = random.uniform(100000, 500000)
            typical_amount_mean = random.uniform(1000, 10000)
            typical_amount_std = typical_amount_mean * 0.6
            typical_frequency_daily = random.uniform(5.0, 20.0)
            preferred_channels = [Channel.WIRE, Channel.ACH, Channel.SWIFT]
            international_ratio = random.uniform(0.1, 0.4)
            cash_ratio = random.uniform(0.1, 0.3)
            business_hours_only = True
            risk_level = "medium"
            recipient_diversity = random.uniform(0.4, 0.7)
            amount_variability = random.uniform(0.5, 0.8)
            temporal_regularity = random.uniform(0.4, 0.7)
            
        elif profile_type == CustomerProfileType.LARGE_BUSINESS:
            base_balance = random.uniform(500000, 5000000)
            typical_amount_mean = random.uniform(5000, 50000)
            typical_amount_std = typical_amount_mean * 0.7
            typical_frequency_daily = random.uniform(10.0, 50.0)
            preferred_channels = [Channel.SWIFT, Channel.WIRE, Channel.ACH]
            international_ratio = random.uniform(0.2, 0.6)
            cash_ratio = random.uniform(0.05, 0.2)
            business_hours_only = False  # Large businesses operate 24/7
            risk_level = "medium"
            recipient_diversity = random.uniform(0.5, 0.8)
            amount_variability = random.uniform(0.6, 0.9)
            temporal_regularity = random.uniform(0.3, 0.6)
            
        elif profile_type == CustomerProfileType.HIGH_NET_WORTH:
            base_balance = random.uniform(100000, 10000000)
            typical_amount_mean = random.uniform(1000, 100000)
            typical_amount_std = typical_amount_mean * 1.0
            typical_frequency_daily = random.uniform(1.0, 10.0)
            preferred_channels = [Channel.SWIFT, Channel.WIRE, Channel.BRANCH, Channel.ONLINE]
            international_ratio = random.uniform(0.3, 0.7)
            cash_ratio = random.uniform(0.1, 0.4)
            business_hours_only = False
            risk_level = "medium"
            recipient_diversity = random.uniform(0.4, 0.8)
            amount_variability = random.uniform(0.7, 1.0)
            temporal_regularity = random.uniform(0.2, 0.5)
            
        elif profile_type == CustomerProfileType.INTERNATIONAL_BUSINESS:
            base_balance = random.uniform(50000, 500000)
            typical_amount_mean = random.uniform(2000, 20000)
            typical_amount_std = typical_amount_mean * 0.6
            typical_frequency_daily = random.uniform(3.0, 15.0)
            preferred_channels = [Channel.SWIFT, Channel.WIRE]
            international_ratio = random.uniform(0.5, 0.9)
            cash_ratio = random.uniform(0.05, 0.15)
            business_hours_only = False
            risk_level = "medium"
            recipient_diversity = random.uniform(0.6, 0.9)
            amount_variability = random.uniform(0.5, 0.8)
            temporal_regularity = random.uniform(0.3, 0.6)
            
        elif profile_type == CustomerProfileType.CASH_INTENSIVE_BUSINESS:
            base_balance = random.uniform(20000, 200000)
            typical_amount_mean = random.uniform(500, 5000)
            typical_amount_std = typical_amount_mean * 0.4
            typical_frequency_daily = random.uniform(5.0, 25.0)
            preferred_channels = [Channel.BRANCH, Channel.ATM]
            international_ratio = random.uniform(0.0, 0.1)
            cash_ratio = random.uniform(0.7, 0.95)
            business_hours_only = True
            risk_level = "standard"
            recipient_diversity = random.uniform(0.2, 0.5)
            amount_variability = random.uniform(0.3, 0.6)
            temporal_regularity = random.uniform(0.6, 0.8)
            
        elif profile_type == CustomerProfileType.STRUCTURING_BEHAVIOR:
            # High-risk profile for structuring
            base_balance = random.uniform(5000, 50000)
            typical_amount_mean = random.uniform(4000, 9000)  # Near CTR threshold
            typical_amount_std = typical_amount_mean * 0.1  # Low variability
            typical_frequency_daily = random.uniform(3.0, 10.0)
            preferred_channels = [Channel.BRANCH, Channel.ATM]
            international_ratio = random.uniform(0.0, 0.05)
            cash_ratio = random.uniform(0.8, 1.0)
            business_hours_only = True
            risk_level = "high"
            recipient_diversity = random.uniform(0.1, 0.3)
            amount_variability = random.uniform(0.1, 0.3)
            temporal_regularity = random.uniform(0.8, 0.95)
            aml_typologies = [AMLTypology.STRUCTURING]
            typology_severity = "moderate"
            
        elif profile_type == CustomerProfileType.FUNNEL_ACCOUNT:
            # High-risk profile for funneling
            base_balance = random.uniform(10000, 100000)
            typical_amount_mean = random.uniform(2000, 10000)
            typical_amount_std = typical_amount_mean * 0.5
            typical_frequency_daily = random.uniform(5.0, 20.0)
            preferred_channels = [Channel.ONLINE, Channel.WIRE, Channel.MOBILE]
            international_ratio = random.uniform(0.3, 0.7)
            cash_ratio = random.uniform(0.1, 0.3)
            business_hours_only = False
            risk_level = "high"
            recipient_diversity = random.uniform(0.7, 0.95)  # Many recipients
            amount_variability = random.uniform(0.6, 0.9)
            temporal_regularity = random.uniform(0.2, 0.4)
            aml_typologies = [AMLTypology.FUNNEL_ACCOUNT]
            typology_severity = "moderate"
            
        elif profile_type == CustomerProfileType.LAYERING_BEHAVIOR:
            # High-risk profile for layering
            base_balance = random.uniform(20000, 200000)
            typical_amount_mean = random.uniform(3000, 15000)
            typical_amount_std = typical_amount_mean * 0.6
            typical_frequency_daily = random.uniform(10.0, 30.0)
            preferred_channels = [Channel.ONLINE, Channel.MOBILE, Channel.WIRE]
            international_ratio = random.uniform(0.2, 0.5)
            cash_ratio = random.uniform(0.1, 0.3)
            business_hours_only = False
            risk_level = "high"
            recipient_diversity = random.uniform(0.5, 0.8)
            amount_variability = random.uniform(0.5, 0.8)
            temporal_regularity = random.uniform(0.1, 0.3)  # Irregular timing
            aml_typologies = [AMLTypology.LAYERING, AMLTypology.RAPID_MOVEMENT]
            typology_severity = "severe"
            
        else:  # FREQUENT_DOMESTIC_SPENDER, OCCASIONAL_HIGH_VALUE
            base_balance = random.uniform(3000, 30000)
            typical_amount_mean = random.uniform(100, 1000)
            typical_amount_std = typical_amount_mean * 0.4
            typical_frequency_daily = random.uniform(2.0, 8.0)
            preferred_channels = [Channel.ONLINE, Channel.MOBILE, Channel.CARD]
            international_ratio = random.uniform(0.0, 0.05)
            cash_ratio = random.uniform(0.2, 0.4)
            business_hours_only = False
            risk_level = "standard"
            recipient_diversity = random.uniform(0.2, 0.5)
            amount_variability = random.uniform(0.3, 0.6)
            temporal_regularity = random.uniform(0.5, 0.7)
        
        # Generate preferred recipients
        num_recipients = int(recipient_diversity * 20) + 1
        preferred_recipients = [f"ACC{random.randint(100000, 999999):06d}" for _ in range(num_recipients)]
        
        return CustomerProfile(
            customer_id=customer_id,
            account_number=account_number,
            profile_type=profile_type,
            wealth_segment=wealth_segment,
            base_balance=base_balance,
            typical_amount_mean=typical_amount_mean,
            typical_amount_std=typical_amount_std,
            typical_frequency_daily=typical_frequency_daily,
            preferred_channels=preferred_channels,
            preferred_recipients=preferred_recipients,
            international_ratio=international_ratio,
            cash_ratio=cash_ratio,
            business_hours_only=business_hours_only,
            risk_level=risk_level,
            recipient_diversity=recipient_diversity,
            amount_variability=amount_variability,
            temporal_regularity=temporal_regularity,
            aml_typologies=aml_typologies if profile_type in [
                CustomerProfileType.STRUCTURING_BEHAVIOR,
                CustomerProfileType.FUNNEL_ACCOUNT,
                CustomerProfileType.LAYERING_BEHAVIOR
            ] else [],
            typology_severity=typology_severity if profile_type in [
                CustomerProfileType.STRUCTURING_BEHAVIOR,
                CustomerProfileType.FUNNEL_ACCOUNT,
                CustomerProfileType.LAYERING_BEHAVIOR
            ] else "none"
        )
    
    def generate_customer_population(
        self,
        num_customers: int,
        profile_distribution: Dict[CustomerProfileType, float]
    ) -> List[CustomerProfile]:
        """Generate a population of customers with specified distribution."""
        customers = []
        
        # Normalize distribution
        total = sum(profile_distribution.values())
        profile_distribution = {k: v/total for k, v in profile_distribution.items()}
        
        # Generate customers
        for profile_type, proportion in profile_distribution.items():
            num = int(num_customers * proportion)
            for _ in range(num):
                wealth_segment = random.choice(["average", "high", "ultra"])
                customer = self.generate_customer(profile_type, wealth_segment)
                customers.append(customer)
        
        return customers


# ============================================================================
# TRANSACTION GENERATOR
# ============================================================================

class TransactionGenerator:
    """Generate transactions from customer profiles."""
    
    def __init__(self, random_seed: int = 42):
        self.random_seed = random_seed
        random.seed(random_seed)
        np.random.seed(random_seed)
        self.transaction_counter = 0
    
    def _generate_timestamp(
        self,
        base_date: datetime,
        days_back: int,
        business_hours_only: bool
    ) -> str:
        """Generate a realistic timestamp."""
        days_offset = random.randint(0, days_back)
        date = base_date - timedelta(days=days_offset)
        
        if business_hours_only:
            hour = random.randint(8, 17)
        else:
            hour = random.randint(0, 23)
        
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        
        return date.replace(hour=hour, minute=minute, second=second).isoformat()
    
    def _generate_amount(
        self,
        profile: CustomerProfile,
        is_legitimate_high_value: bool = False,
        is_structuring: bool = False
    ) -> float:
        """Generate transaction amount based on profile."""
        if is_legitimate_high_value:
            # Legitimate large transaction (e.g., business payment, large purchase)
            return round(random.uniform(10000, 100000) * (1 if profile.wealth_segment == "ultra" else 0.5), 2)
        
        if is_structuring:
            # Amount near CTR threshold ($10,000)
            return round(random.uniform(8500, 9999), 2)
        
        # Normal amount based on profile
        amount = np.random.normal(profile.typical_amount_mean, profile.typical_amount_std)
        amount = max(10, abs(amount))  # Minimum $10
        
        # Apply wealth segment multiplier
        if profile.wealth_segment == "high":
            amount *= random.uniform(1.5, 3.0)
        elif profile.wealth_segment == "ultra":
            amount *= random.uniform(3.0, 10.0)
        
        return round(amount, 2)
    
    def _select_channel(self, profile: CustomerProfile, is_cash: bool = False) -> Channel:
        """Select channel based on profile."""
        if is_cash:
            if random.random() < profile.cash_ratio:
                return random.choice([Channel.BRANCH, Channel.ATM])
            else:
                return random.choice(profile.preferred_channels)
        return random.choice(profile.preferred_channels)
    
    def _select_recipient(
        self,
        profile: CustomerProfile,
        is_new_recipient: bool = False,
        is_funnel: bool = False
    ) -> str:
        """Select recipient account."""
        if is_funnel:
            # Generate many different recipients
            return f"ACC{random.randint(100000, 999999):06d}"
        
        if is_new_recipient or random.random() < (1 - profile.recipient_diversity):
            return f"ACC{random.randint(100000, 999999):06d}"
        
        return random.choice(profile.preferred_recipients)
    
    def _select_country(self, profile: CustomerProfile, is_high_risk: bool = False) -> str:
        """Select destination country."""
        if is_high_risk:
            return random.choice(list(HIGH_RISK_COUNTRIES))
        
        if random.random() < profile.international_ratio:
            return random.choice(list(LEGITIMATE_COUNTRIES))
        
        return "ZW"  # Domestic (Zimbabwe)
    
    def generate_transaction(
        self,
        profile: CustomerProfile,
        historical_transactions: List[Dict[str, Any]],
        scenario: str = "normal",
        days_back: int = 30
    ) -> Transaction:
        """Generate a single transaction."""
        self.transaction_counter += 1
        
        base_date = datetime.now(timezone.utc)
        timestamp = self._generate_timestamp(base_date, days_back, profile.business_hours_only)
        
        # Determine scenario and ground truth
        ground_truth_label, aml_typologies, scenario_description = self._determine_ground_truth(
            profile, scenario, historical_transactions
        )
        
        # Generate transaction characteristics based on scenario
        is_legitimate_high_value = (scenario == "legitimate_high_value")
        is_structuring = (AMLTypology.STRUCTURING in aml_typologies)
        is_funnel = (AMLTypology.FUNNEL_ACCOUNT in aml_typologies)
        is_layering = (AMLTypology.LAYERING in aml_typologies)
        is_high_risk_country = (AMLTypology.HIGH_RISK_JURISDICTION in aml_typologies)
        
        amount = self._generate_amount(profile, is_legitimate_high_value, is_structuring)
        
        # Select transaction type
        if scenario == "cash_deposit" or is_structuring:
            tx_type = TransactionType.DEPOSIT
        elif scenario == "cash_withdrawal":
            tx_type = TransactionType.WITHDRAW
        else:
            tx_type = random.choice([TransactionType.TRANSFER, TransactionType.DEPOSIT, TransactionType.WITHDRAW])
        
        channel = self._select_channel(profile, is_cash=(tx_type in [TransactionType.DEPOSIT, TransactionType.WITHDRAW]))
        receiver_account = self._select_recipient(profile, is_funnel=is_funnel)
        destination_country = self._select_country(profile, is_high_risk=is_high_risk_country)
        
        # Generate description
        description = self._generate_description(tx_type, amount, channel, scenario)
        
        # Compute historical features
        features = self._compute_historical_features(profile, historical_transactions, amount, timestamp)
        
        # Determine if borderline case
        is_borderline_case = self._is_borderline_case(profile, scenario, aml_typologies)
        
        return Transaction(
            transaction_id=self.transaction_counter,
            customer_id=profile.customer_id,
            sender_account=profile.account_number,
            receiver_account=receiver_account,
            transaction_type=tx_type,
            amount=amount,
            timestamp=timestamp,
            channel=channel,
            description=description,
            ground_truth_label=ground_truth_label,
            aml_typologies=aml_typologies,
            scenario_id=f"{scenario}_{self.transaction_counter}",
            scenario_description=scenario_description,
            sender_avg_amount=features["sender_avg_amount"],
            sender_max_amount=features["sender_max_amount"],
            sender_tx_count=features["sender_tx_count"],
            amount_to_sender_avg=features["amount_to_sender_avg"],
            amount_to_sender_max=features["amount_to_sender_max"],
            sender_tx_count_24h=features["sender_tx_count_24h"],
            sender_volume_24h=features["sender_volume_24h"],
            amount_to_sender_volume_24h=features["amount_to_sender_volume_24h"],
            is_new_recipient=features["is_new_recipient"],
            same_day_count=features["same_day_count"],
            same_day_total=features["same_day_total"],
            same_recipient_count=features["same_recipient_count"],
            rapid_transfer_count=features["rapid_transfer_count"],
            generation_seed=self.random_seed,
            is_legitimate_high_value=is_legitimate_high_value,
            is_borderline_case=is_borderline_case
        )
    
    def _determine_ground_truth(
        self,
        profile: CustomerProfileType,
        scenario: str,
        historical_transactions: List[Dict[str, Any]]
    ) -> Tuple[GroundTruthLabel, List[AMLTypology], str]:
        """Determine ground truth label based on AML typologies."""
        
        # Check if customer has high-risk profile
        if profile.aml_typologies:
            # Customer has inherent AML behavior
            if profile.typology_severity == "severe":
                return GroundTruthLabel.SUPER_SUSPICIOUS, profile.aml_typologies, f"Customer exhibits severe {profile.typology_severity} AML behavior: {[t.value for t in profile.aml_typologies]}"
            else:
                return GroundTruthLabel.SUSPICIOUS, profile.aml_typologies, f"Customer exhibits moderate {profile.typology_severity} AML behavior: {[t.value for t in profile.aml_typologies]}"
        
        # Scenario-based determination
        suspicious_scenarios = {
            "structuring": (GroundTruthLabel.SUSPICIOUS, [AMLTypology.STRUCTURING], "Multiple transactions near CTR threshold"),
            "layering": (GroundTruthLabel.SUSPICIOUS, [AMLTypology.LAYERING], "Rapid transfers through multiple accounts"),
            "funnel": (GroundTruthLabel.SUSPICIOUS, [AMLTypology.FUNNEL_ACCOUNT], "Funds from multiple sources distributed to many recipients"),
            "rapid_movement": (GroundTruthLabel.SUSPICIOUS, [AMLTypology.RAPID_MOVEMENT], "Funds received and quickly transferred"),
            "high_risk_country": (GroundTruthLabel.SUSPICIOUS, [AMLTypology.HIGH_RISK_JURISDICTION], "Transaction to high-risk jurisdiction"),
            "behavioral_change": (GroundTruthLabel.SUSPICIOUS, [AMLTypology.BEHAVIORAL_CHANGE], "Sudden change in transaction pattern"),
        }
        
        super_suspicious_scenarios = {
            "severe_structuring": (GroundTruthLabel.SUPER_SUSPICIOUS, [AMLTypology.STRUCTURING], "Coordinated structuring pattern"),
            "severe_layering": (GroundTruthLabel.SUPER_SUSPICIOUS, [AMLTypology.LAYERING, AMLTypology.RAPID_MOVEMENT], "Coordinated layering with rapid movement"),
            "severe_funnel": (GroundTruthLabel.SUPER_SUSPICIOUS, [AMLTypology.FUNNEL_ACCOUNT, AMLTypology.SHELL_COMPANY], "Funnel account with shell company indicators"),
            "multiple_typologies": (GroundTruthLabel.SUPER_SUSPICIOUS, [AMLTypology.STRUCTURING, AMLTypology.LAYERING], "Multiple AML typologies present"),
        }
        
        if scenario in super_suspicious_scenarios:
            return super_suspicious_scenarios[scenario]
        elif scenario in suspicious_scenarios:
            return suspicious_scenarios[scenario]
        else:
            return GroundTruthLabel.NORMAL, [AMLTypology.NONE], "Normal transaction pattern"
    
    def _compute_historical_features(
        self,
        profile: CustomerProfile,
        historical_transactions: List[Transaction],
        current_amount: float,
        current_timestamp: str
    ) -> Dict[str, float]:
        """Compute historical features from transaction history."""
        if not historical_transactions:
            return {
                "sender_avg_amount": profile.typical_amount_mean,
                "sender_max_amount": profile.typical_amount_mean * 2,
                "sender_tx_count": 0,
                "amount_to_sender_avg": current_amount / max(profile.typical_amount_mean, 1),
                "amount_to_sender_max": current_amount / (profile.typical_amount_mean * 2),
                "sender_tx_count_24h": 0,
                "sender_volume_24h": 0,
                "amount_to_sender_volume_24h": 1.0,
                "is_new_recipient": 1.0,
                "same_day_count": 0,
                "same_day_total": 0,
                "same_recipient_count": 0,
                "rapid_transfer_count": 0,
            }
        
        amounts = [tx.amount for tx in historical_transactions]
        sender_avg_amount = sum(amounts) / len(amounts) if amounts else profile.typical_amount_mean
        sender_max_amount = max(amounts) if amounts else profile.typical_amount_mean * 2
        
        # 24-hour window
        current_time = datetime.fromisoformat(current_timestamp)
        cutoff = current_time - timedelta(hours=24)
        
        recent_txs = [tx for tx in historical_transactions 
                     if datetime.fromisoformat(tx.timestamp) >= cutoff]
        
        sender_tx_count_24h = len(recent_txs)
        sender_volume_24h = sum(tx.amount for tx in recent_txs)
        
        # Same day
        same_day_txs = [tx for tx in historical_transactions 
                      if datetime.fromisoformat(tx.timestamp).date() == current_time.date()]
        same_day_count = len(same_day_txs)
        same_day_total = sum(tx.amount for tx in same_day_txs)
        
        # Same recipient in 24h
        current_recipient = historical_transactions[-1].receiver_account if historical_transactions else ""
        same_recipient_count = len([tx for tx in recent_txs 
                                   if tx.receiver_account == current_recipient])
        
        # Rapid transfers (within 10 minutes)
        rapid_transfer_count = 0
        if len(recent_txs) > 1:
            for i in range(len(recent_txs) - 1):
                time_diff = (current_time - datetime.fromisoformat(recent_txs[i].timestamp)).total_seconds()
                if 0 < time_diff <= 600:
                    rapid_transfer_count += 1
        
        return {
            "sender_avg_amount": sender_avg_amount,
            "sender_max_amount": sender_max_amount,
            "sender_tx_count": len(historical_transactions),
            "amount_to_sender_avg": current_amount / max(sender_avg_amount, 1),
            "amount_to_sender_max": current_amount / max(sender_max_amount, 1),
            "sender_tx_count_24h": sender_tx_count_24h,
            "sender_volume_24h": sender_volume_24h,
            "amount_to_sender_volume_24h": current_amount / max(sender_volume_24h, 1),
            "is_new_recipient": 1.0 if len(historical_transactions) < 5 else random.choice([0.0, 1.0]),
            "same_day_count": same_day_count,
            "same_day_total": same_day_total,
            "same_recipient_count": same_recipient_count,
            "rapid_transfer_count": rapid_transfer_count,
        }
    
    def _generate_description(
        self,
        tx_type: TransactionType,
        amount: float,
        channel: Channel,
        scenario: str
    ) -> str:
        """Generate transaction description."""
        descriptions = {
            TransactionType.DEPOSIT: ["Cash deposit", "Funds transfer in", "Credit received"],
            TransactionType.WITHDRAW: ["Cash withdrawal", "Funds transfer out", "Debit"],
            TransactionType.TRANSFER: ["Transfer", "Payment", "Wire transfer"]
        }
        base_desc = random.choice(descriptions[tx_type])
        return f"{base_desc} via {channel.value}"
    
    def _is_borderline_case(
        self,
        profile: CustomerProfile,
        scenario: str,
        aml_typologies: List[AMLTypology]
    ) -> bool:
        """Determine if this is a borderline case."""
        # Legitimate high-value transactions that could be suspicious
        if scenario == "legitimate_high_value":
            return True
        
        # Normal customers with occasional suspicious-looking patterns
        if not profile.aml_typologies and aml_typologies:
            return True
        
        return False


# ============================================================================
# DATASET GENERATOR
# ============================================================================

class AMLDatasetGenerator:
    """Main dataset generator orchestrating customers and transactions."""
    
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
        profile_distribution: Dict[CustomerProfileType, float] = None
    ) -> Tuple[List[Transaction], List[CustomerProfile]]:
        """Generate complete AML dataset."""
        
        # Default class distribution (configurable)
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
        
        # Generate transactions for each customer
        print(f"Generating transactions for {len(customers)} customers...")
        all_transactions = []
        
        for customer in customers:
            # Determine customer's overall behavior
            customer_transactions = []
            
            # Generate historical transactions first
            for _ in range(transactions_per_customer):
                # Select scenario based on customer profile and desired class distribution
                scenario = self._select_scenario(customer, class_distribution)
                
                tx = self.transaction_generator.generate_transaction(
                    customer,
                    customer_transactions,
                    scenario
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
    
    def _select_scenario(
        self,
        customer: CustomerProfile,
        class_distribution: Dict[str, float]
    ) -> str:
        """Select scenario based on customer profile and desired class distribution."""
        
        # Determine target class based on distribution
        rand = random.random()
        
        # Normalize distribution
        total = sum(class_distribution.values())
        normal_prob = class_distribution.get("normal", 0.7) / total
        suspicious_prob = normal_prob + class_distribution.get("suspicious", 0.2) / total
        
        target_class = None
        if rand < normal_prob:
            target_class = "normal"
        elif rand < suspicious_prob:
            target_class = "suspicious"
        else:
            target_class = "super_suspicious"
        
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
            # Normal customer with suspicious scenario (edge case)
            suspicious_scenarios = ["structuring", "layering", "funnel", "rapid_movement", "high_risk_country", "behavioral_change"]
            return random.choice(suspicious_scenarios)
        else:  # super_suspicious
            # Normal customer with super suspicious scenario (rare edge case)
            severe_scenarios = ["severe_structuring", "severe_layering", "severe_funnel", "multiple_typologies"]
            return random.choice(severe_scenarios)


# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

def generate_aml_dataset(
    num_customers: int = 200,
    transactions_per_customer: int = 50,
    class_distribution: Dict[str, float] = None,
    profile_distribution: Dict[CustomerProfileType, float] = None,
    random_seed: int = 42
) -> Tuple[List[Transaction], List[CustomerProfile]]:
    """Generate AML dataset with specified parameters."""
    generator = AMLDatasetGenerator(random_seed)
    return generator.generate_dataset(
        num_customers,
        transactions_per_customer,
        class_distribution,
        profile_distribution
    )


def export_dataset_to_csv(
    transactions: List[Transaction],
    output_file: str = "ml_stage3_dataset.csv"
):
    """Export transactions to CSV (features only, no ground truth in features)."""
    import csv
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header (features only)
        header = [
            "transaction_id", "sender_account", "receiver_account", "transaction_type",
            "amount", "timestamp", "channel", "description",
            "sender_avg_amount", "sender_max_amount", "sender_tx_count",
            "amount_to_sender_avg", "amount_to_sender_max", "sender_tx_count_24h",
            "sender_volume_24h", "amount_to_sender_volume_24h", "is_new_recipient",
            "same_day_count", "same_day_total", "same_recipient_count", "rapid_transfer_count"
        ]
        writer.writerow(header)
        
        # Data rows
        for tx in transactions:
            row = [
                tx.transaction_id, tx.sender_account, tx.receiver_account, tx.transaction_type.value,
                tx.amount, tx.timestamp, tx.channel.value, tx.description,
                tx.sender_avg_amount, tx.sender_max_amount, tx.sender_tx_count,
                tx.amount_to_sender_avg, tx.amount_to_sender_max, tx.sender_tx_count_24h,
                tx.sender_volume_24h, tx.amount_to_sender_volume_24h, tx.is_new_recipient,
                tx.same_day_count, tx.same_day_total, tx.same_recipient_count, tx.rapid_transfer_count
            ]
            writer.writerow(row)


def export_ground_truth(
    transactions: List[Transaction],
    output_file: str = "ml_stage3_ground_truth.json"
):
    """Export ground truth labels separately (never used as features)."""
    ground_truth = []
    
    for tx in transactions:
        ground_truth.append({
            "transaction_id": tx.transaction_id,
            "ground_truth_label": tx.ground_truth_label.value,
            "aml_typologies": [t.value for t in tx.aml_typologies],
            "scenario_id": tx.scenario_id,
            "scenario_description": tx.scenario_description,
            "customer_id": tx.customer_id,
            "is_legitimate_high_value": tx.is_legitimate_high_value,
            "is_borderline_case": tx.is_borderline_case
        })
    
    with open(output_file, 'w') as f:
        json.dump(ground_truth, f, indent=2)


def export_metadata(
    transactions: List[Transaction],
    customers: List[CustomerProfile],
    output_file: str = "ml_stage3_metadata.json"
):
    """Export dataset metadata."""
    
    # Class distribution
    label_counts = {label.value: 0 for label in GroundTruthLabel}
    for tx in transactions:
        label_counts[tx.ground_truth_label.value] += 1
    
    # Typology distribution
    typology_counts = {typology.value: 0 for typology in AMLTypology}
    for tx in transactions:
        for typology in tx.aml_typologies:
            typology_counts[typology.value] += 1
    
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "random_seed": 42,
        "num_customers": len(customers),
        "num_transactions": len(transactions),
        "transactions_per_customer": len(transactions) // len(customers) if customers else 0,
        "class_distribution": label_counts,
        "typology_distribution": typology_counts,
        "customer_profile_types": {profile_type.value: sum(1 for c in customers if c.profile_type == profile_type) 
                                   for profile_type in CustomerProfileType},
    }
    
    with open(output_file, 'w') as f:
        json.dump(metadata, f, indent=2)


if __name__ == "__main__":
    # Test the generator
    print("Testing AML Dataset Generator...")
    
    transactions, customers = generate_aml_dataset(
        num_customers=50,
        transactions_per_customer=20,
        random_seed=42
    )
    
    print(f"Generated {len(transactions)} transactions from {len(customers)} customers")
    
    # Export
    export_dataset_to_csv(transactions, "ml_stage3_dataset_test.csv")
    export_ground_truth(transactions, "ml_stage3_ground_truth_test.json")
    export_metadata(transactions, customers, "ml_stage3_metadata_test.json")
    
    print("Export complete")
