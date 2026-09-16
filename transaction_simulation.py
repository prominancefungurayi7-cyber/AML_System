"""
transaction_simulation.py — Transaction Simulation Module

This module handles the generation of simulated mobile-money transactions for AML testing.
It provides realistic transaction scenarios including normal, suspicious, and highly suspicious
transactions based on money laundering typologies.

Functions:
    - _random_transaction_amount: Generate random transaction amounts
    - _simulation_plan: Create class distribution for AML training data
    - _simulation_timestamp: Generate realistic timestamps
    - _scenario_amount: Generate scenario-specific amounts
    - _simulation_segment_multiplier: Apply wealth segment multipliers
    - _simulation_transaction: Generate a single transaction
    - _simulation_reason: Generate simulation reasons
    - _history_profile: Build transaction history profile
    - _ai_profile_for_transaction: Build AI profile for transaction
"""

import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional


# Default profile features for AI model
PROFILE_FEATURE_DEFAULTS = {
    "sender_avg_amount": 0.0,
    "sender_max_amount": 0.0,
    "sender_tx_count": 0,
    "amount_to_sender_avg": 1.0,
    "amount_to_sender_max": 1.0,
    "sender_tx_count_24h": 0,
    "sender_volume_24h": 0.0,
    "amount_to_sender_volume_24h": 1.0,
    "is_new_recipient": 1.0,
    "same_day_count": 0,
    "same_day_total": 0.0,
    "same_recipient_count": 0,
    "rapid_transfer_count": 0,
}


def _random_transaction_amount(tx_type):
    """Generate random transaction amount based on type."""
    if tx_type == "transfer":
        return random.choice([25, 75, 150, 500, 950, 1500, 2500, 5000, 9000])
    if tx_type == "withdraw":
        return random.choice([20, 60, 120, 300, 1000, 3500, 10000])
    return random.choice([50, 100, 250, 450, 1000, 3000, 9999, 10000])


def _simulation_plan(count):
    """Create a realistic class distribution for AML training data.

    The majority of transactions should be ordinary activity (at least 70%),
    while the remaining minority consists of suspicious and highly suspicious cases.
    The split is tuned to support model training without overwhelming the
    dataset with rare anomalies.
    """
    if count <= 0:
        return []

    normal_count = max(1, int(count * 0.70))
    suspicious_count = max(0, int(count * 0.20))
    super_count = count - normal_count - suspicious_count

    if super_count < 0:
        super_count = 0

    labels = ["normal"] * normal_count + ["suspicious"] * suspicious_count + ["super_suspicious"] * super_count
    random.shuffle(labels)
    return labels


def _simulation_timestamp(hour):
    """Generate realistic timestamp within the last 30 days."""
    now = datetime.now(timezone.utc)
    days_back = random.randint(1, 30)

    candidate = now - timedelta(
        days=days_back,
        minutes=random.randint(0, 23 * 60 + 59),
    )

    return candidate.replace(
        hour=hour,
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
        microsecond=0,
    ).isoformat()


# Normal transaction scenarios representing everyday EcoCash mobile-money activities
NORMAL_TRANSACTION_SCENARIOS = [
    {
        "type": "transfer",
        "amount": (850, 4200),
        "channel": "agent",
        "hours": list(range(8, 17)),
        "description": "Cash-In at agent for regular income",
        "ecocash_type": "cash_in",
    },
    {
        "type": "transfer",
        "amount": (12, 180),
        "channel": "agent",
        "hours": list(range(7, 22)),
        "description": "Cash-Out at agent for daily expenses",
        "ecocash_type": "cash_out",
    },
    {
        "type": "transfer",
        "amount": (20, 500),
        "channel": "agent",
        "hours": list(range(6, 23)),
        "description": "Cash-Out at mobile-money agent terminal",
        "ecocash_type": "cash_out",
    },
    {
        "type": "transfer",
        "amount": (35, 950),
        "channel": "mobile",
        "hours": list(range(7, 22)),
        "description": "Wallet-to-wallet transfer for household payment",
        "ecocash_type": "wallet_to_wallet",
    },
    {
        "type": "transfer",
        "amount": (120, 1800),
        "channel": "online",
        "hours": list(range(8, 20)),
        "description": "Online bill payment to regular beneficiary",
        "ecocash_type": "wallet_to_wallet",
    },
]


# Suspicious transaction scenarios representing potential money laundering
# Updated for EcoCash terminology and Stage 14 binary classification
SUSPICIOUS_TRANSACTION_SCENARIOS = [
    {
        "type": "transfer",
        "amount": (9200, 9900),
        "channel": "agent",
        "hours": list(range(9, 16)),
        "description": "Cash-In just below currency reporting threshold",
        "reason": "Possible structuring: cash-in below the CTR threshold",
        "ecocash_type": "cash_in",
    },
    {
        "type": "transfer",
        "amount": (1400, 6800),
        "channel": "online",
        "hours": [0, 1, 2, 3, 22, 23],
        "description": "Unusual off-hours wallet transfer to recently added beneficiary",
        "reason": "Off-hours transfer pattern inconsistent with normal customer activity",
        "ecocash_type": "wallet_to_wallet",
    },
    {
        "type": "transfer",
        "amount": (1500, 6500),
        "channel": "agent",
        "hours": [0, 1, 2, 3, 4, 22, 23],
        "description": "High-value Cash-Out at agent outside normal mobile-money hours",
        "reason": "Large cash withdrawal during unusual hours",
        "ecocash_type": "cash_out",
    },
    {
        "type": "transfer",
        "amount": (2500, 7400),
        "channel": "mobile",
        "hours": list(range(6, 23)),
        "description": "Multiple rapid wallet transfers to another customer wallet",
        "reason": "Potential layering through repeated customer-to-customer transfers",
        "ecocash_type": "wallet_to_wallet",
    },
    {
        "type": "transfer",
        "amount": (3000, 8500),
        "channel": "online",
        "hours": list(range(9, 17)),
        "description": "Transfer to third-party wallet with no prior relationship",
        "reason": "Third-party payment: transfer to unrelated beneficiary",
        "ecocash_type": "wallet_to_wallet",
    },
    {
        "type": "transfer",
        "amount": (4500, 9500),
        "channel": "mobile",
        "hours": list(range(8, 20)),
        "description": "Multiple payments to different third-party wallets",
        "reason": "Third-party funneling: payments to multiple unrelated wallets",
        "ecocash_type": "wallet_to_wallet",
    },
    {
        "type": "transfer",
        "amount": (8000, 18000),
        "channel": "online",
        "hours": list(range(9, 16)),
        "destination_country": "KY",
        "description": "Transfer to offshore wallet with no business purpose",
        "reason": "Offshore transfer: transfer to external entity with no legitimate business reason",
        "ecocash_type": "wallet_to_wallet",
    },
    {
        "type": "transfer",
        "amount": (12000, 25000),
        "channel": "online",
        "hours": list(range(9, 16)),
        "destination_country": "BZ",
        "description": "Large transfer to newly created wallet",
        "reason": "New wallet activity: transfer to recently created wallet",
        "ecocash_type": "wallet_to_wallet",
    },
    {
        "type": "transfer",
        "amount": (15000, 35000),
        "channel": "online",
        "hours": list(range(9, 16)),
        "destination_country": "CN",
        "description": "Large international payment",
        "reason": "International transfer: large payment to external jurisdiction",
        "ecocash_type": "wallet_to_wallet",
    },
    {
        "type": "transfer",
        "amount": (5000, 12000),
        "channel": "online",
        "hours": list(range(9, 16)),
        "description": "Multiple small payments to same wallet",
        "reason": "Structuring: breaking large payments into smaller amounts",
        "ecocash_type": "wallet_to_wallet",
    },
    {
        "type": "transfer",
        "amount": (3000, 8000),
        "channel": "online",
        "hours": [0, 1, 2, 3, 22, 23],
        "description": "Transfer to cryptocurrency exchange platform",
        "reason": "Crypto-related: transfer to digital asset exchange during off-hours",
        "ecocash_type": "wallet_to_wallet",
    },
    {
        "type": "transfer",
        "amount": (7000, 15000),
        "channel": "online",
        "hours": list(range(9, 16)),
        "description": "Rapid transfers between digital wallets",
        "reason": "Layering: rapid movement through multiple wallets",
        "ecocash_type": "wallet_to_wallet",
    },
]


# Highly suspicious transaction scenarios representing severe AML risks
# Updated for EcoCash terminology and Stage 14 binary classification
SUPER_SUSPICIOUS_TRANSACTION_SCENARIOS = [
    {
        "type": "transfer",
        "amount": (10000, 28000),
        "channel": "agent",
        "hours": list(range(9, 16)),
        "description": "Large Cash-In requiring currency transaction review",
        "reason": "Cash transaction exceeds the CTR threshold and requires enhanced review",
        "ecocash_type": "cash_in",
    },
    {
        "type": "transfer",
        "amount": (12000, 52000),
        "channel": "online",
        "hours": [0, 1, 2, 3, 23],
        "destination_country": "IR",
        "description": "High-value transfer to high-risk jurisdiction",
        "reason": "High-value off-hours transfer to high-risk jurisdiction",
        "ecocash_type": "wallet_to_wallet",
    },
    {
        "type": "transfer",
        "amount": (10000, 24000),
        "channel": "agent",
        "hours": list(range(9, 16)),
        "description": "Large Cash-Out at agent location",
        "reason": "Large cash withdrawal meets threshold for immediate compliance review",
        "ecocash_type": "cash_out",
    },
    {
        "type": "transfer",
        "amount": (4500, 4900),
        "channel": "agent",
        "hours": list(range(9, 16)),
        "description": "Multiple Cash-Ins just below half CTR threshold",
        "reason": "Smurfing pattern: multiple cash-ins below $5000 to avoid reporting",
        "ecocash_type": "cash_in",
    },
    {
        "type": "transfer",
        "amount": (2500, 2900),
        "channel": "agent",
        "hours": list(range(9, 16)),
        "description": "Frequent small Cash-Ins at agent",
        "reason": "Structuring through small deposits to avoid detection",
        "ecocash_type": "cash_in",
    },
    {
        "type": "transfer",
        "amount": (8000, 15000),
        "channel": "online",
        "hours": list(range(9, 16)),
        "description": "Rapid sequential transfers to multiple wallets",
        "reason": "Layering: rapid movement of funds through multiple wallets",
        "ecocash_type": "wallet_to_wallet",
    },
    {
        "type": "transfer",
        "amount": (3000, 7000),
        "channel": "mobile",
        "hours": list(range(9, 16)),
        "description": "Circular transfer pattern between related wallets",
        "reason": "Layering: circular transfers to obscure audit trail",
        "ecocash_type": "wallet_to_wallet",
    },
    {
        "type": "transfer",
        "amount": (50000, 150000),
        "channel": "online",
        "hours": list(range(9, 16)),
        "destination_country": "AE",
        "description": "Large transfer to real estate development company",
        "reason": "Real estate laundering: large payment to property development entity",
        "ecocash_type": "wallet_to_wallet",
    },
    {
        "type": "transfer",
        "amount": (25000, 75000),
        "channel": "online",
        "hours": list(range(9, 16)),
        "destination_country": "PA",
        "description": "Multiple transfers to property holding companies",
        "reason": "Real estate structuring: payments to multiple property holding entities",
        "ecocash_type": "wallet_to_wallet",
    },
    {
        "type": "transfer",
        "amount": (15000, 40000),
        "channel": "online",
        "hours": [0, 1, 2, 3, 22, 23],
        "description": "Large transfer to online gambling platform",
        "reason": "Casino laundering: transfer to gambling platform during off-hours",
        "ecocash_type": "wallet_to_wallet",
    },
    {
        "type": "transfer",
        "amount": (8000, 20000),
        "channel": "online",
        "hours": list(range(9, 16)),
        "description": "Rapid deposits and withdrawals from gambling accounts",
        "reason": "Casino layering: rapid movement through gambling platforms",
        "ecocash_type": "wallet_to_wallet",
    },
    {
        "type": "transfer",
        "amount": (20000, 50000),
        "channel": "online",
        "hours": list(range(9, 16)),
        "destination_country": "RU",
        "description": "Transfer to entity linked to politically exposed person",
        "reason": "PEP-related: transfer to entity associated with foreign official",
        "ecocash_type": "wallet_to_wallet",
    },
    {
        "type": "transfer",
        "amount": (30000, 80000),
        "channel": "online",
        "hours": [0, 1, 2, 3, 23],
        "destination_country": "NG",
        "description": "Off-hours transfer to offshore trust structure",
        "reason": "Corruption: transfer to offshore trust structure during unusual hours",
        "ecocash_type": "wallet_to_wallet",
    },
    {
        "type": "transfer",
        "amount": (5000, 15000),
        "channel": "mobile",
        "hours": [0, 1, 2, 3, 22, 23],
        "description": "Small rapid transfers to high-risk region accounts",
        "reason": "Terrorist financing: small rapid transfers to high-risk jurisdictions",
        "ecocash_type": "wallet_to_wallet",
    },
    {
        "type": "transfer",
        "amount": (10000, 25000),
        "channel": "online",
        "hours": list(range(9, 16)),
        "description": "Transfer to charity organization in conflict zone",
        "reason": "Terrorist financing: transfer to charitable entity in high-risk region",
        "ecocash_type": "wallet_to_wallet",
    },
]


# ============================================================================
# AML SCENARIO GENERATORS FOR STAGE 17E
# ============================================================================

def generate_structuring_scenario(conn, sender_wallet, receiver_wallet=None, count=5):
    """
    Generate structuring-style transaction sequence for testing Stage 13 structuring features.
    
    This creates repeated transactions with similar amounts that can exercise:
    - structuring_prior_tx_count_1h
    - structuring_prior_value_sum_24h
    - structuring_same_day_prior_tx_count
    - structuring_repeated_amount_ratio_7d
    - structuring_near_threshold_history_ratio_7d
    
    Args:
        conn: Database connection
        sender_wallet: Sender wallet dict
        receiver_wallet: Optional receiver wallet dict
        count: Number of transactions to generate
        
    Returns:
        List of transaction tuples
    """
    if receiver_wallet is None:
        receiver_wallet = sender_wallet  # Cash-In/Cash-Out case
    
    transactions = []
    base_amount = random.choice([4800, 4900, 9500, 9800])  # Near CTR threshold
    current_time = datetime.now(timezone.utc)
    
    for i in range(count):
        # Small variations around base amount for structuring pattern
        amount_variation = random.uniform(-100, 100)
        amount = round(base_amount + amount_variation, 2)
        amount = max(amount, 1.0)
        
        # Spread transactions over short time window (burst pattern)
        time_offset = timedelta(minutes=i * random.randint(5, 15))
        timestamp = (current_time - time_offset).isoformat()
        
        # Determine transaction type based on wallet relationship
        if sender_wallet == receiver_wallet:
            # Cash-In or Cash-Out
            tx_type = "transfer"  # All represented as transfer in DB
            channel = "agent"
            description = f"Structuring Cash-In of ${amount:,.2f} near threshold"
        else:
            # Wallet-to-wallet
            tx_type = "transfer"
            channel = random.choice(["mobile", "online"])
            description = f"Structuring transfer of ${amount:,.2f} with repeated amount pattern"
        
        transactions.append((
            sender_wallet, receiver_wallet, tx_type, amount, timestamp,
            channel, description, "Structuring pattern: repeated amounts near threshold", "ZW", None
        ))
    
    return transactions


def generate_network_scenario(conn, wallets, scenario_type="many_to_one", count=10):
    """
    Generate network-style transaction sequence for testing Stage 13 network features.
    
    This creates transaction patterns that can exercise:
    - network_outbound_counterparty_count_7d
    - network_inbound_counterparty_count_7d
    - network_outbound_counterparty_entropy_30d
    - network_top_counterparty_value_share_30d
    - network_current_receiver_is_new
    - network_repeated_receiver_ratio_30d
    - network_reciprocal_flow_ratio_7d
    - network_counterparty_set_change_7d
    - network_pass_through_ratio_24h
    - network_shared_counterparty_concentration_7d
    
    Args:
        conn: Database connection
        wallets: List of wallet dicts
        scenario_type: Type of network scenario (many_to_one, one_to_many, pass_through)
        count: Number of transactions to generate
        
    Returns:
        List of transaction tuples
    """
    transactions = []
    current_time = datetime.now(timezone.utc)
    
    if scenario_type == "many_to_one":
        # Many wallets sending to one wallet (concentration)
        concentration_wallet = random.choice(wallets)
        sender_wallets = [w for w in wallets if w["id"] != concentration_wallet["id"]]
        
        for i in range(min(count, len(sender_wallets))):
            sender = sender_wallets[i]
            amount = random.uniform(1000, 5000)
            time_offset = timedelta(hours=i * random.randint(1, 3))
            timestamp = (current_time - time_offset).isoformat()
            
            transactions.append((
                sender, concentration_wallet, "transfer", amount, timestamp,
                "mobile", f"Many-to-one concentration transfer of ${amount:,.2f}",
                "Network pattern: many wallets sending to single recipient", "ZW", None
            ))
    
    elif scenario_type == "one_to_many":
        # One wallet sending to many wallets (distribution)
        distribution_wallet = random.choice(wallets)
        receiver_wallets = [w for w in wallets if w["id"] != distribution_wallet["id"]]
        
        for i in range(min(count, len(receiver_wallets))):
            receiver = receiver_wallets[i]
            amount = random.uniform(500, 3000)
            time_offset = timedelta(hours=i * random.randint(1, 2))
            timestamp = (current_time - time_offset).isoformat()
            
            transactions.append((
                distribution_wallet, receiver, "transfer", amount, timestamp,
                "mobile", f"One-to-many distribution transfer of ${amount:,.2f}",
                "Network pattern: single wallet sending to many recipients", "ZW", None
            ))
    
    elif scenario_type == "pass_through":
        # Pass-through pattern: wallet A -> wallet B -> wallet C
        if len(wallets) >= 3:
            source = wallets[0]
            intermediate = wallets[1]
            final = wallets[2]
            
            # First leg: source -> intermediate
            amount = random.uniform(5000, 15000)
            timestamp1 = (current_time - timedelta(hours=2)).isoformat()
            transactions.append((
                source, intermediate, "transfer", amount, timestamp1,
                "mobile", f"Pass-through inbound transfer of ${amount:,.2f}",
                "Network pattern: pass-through first leg", "ZW", None
            ))
            
            # Second leg: intermediate -> final (similar amount)
            amount2 = amount * random.uniform(0.95, 0.99)  # Slightly less (fees)
            timestamp2 = (current_time - timedelta(hours=1)).isoformat()
            transactions.append((
                intermediate, final, "transfer", amount2, timestamp2,
                "mobile", f"Pass-through outbound transfer of ${amount2:,.2f}",
                "Network pattern: pass-through second leg", "ZW", None
            ))
    
    return transactions


def generate_agent_scenario(conn, wallets, agents, scenario_type="concentration", count=15):
    """
    Generate agent-mediated transaction sequence for testing Stage 13 agent features.
    
    This creates transaction patterns that can exercise:
    - agent_prior_tx_count_1h
    - agent_prior_tx_count_7d
    - agent_prior_value_sum_1h
    - agent_prior_value_sum_7d
    - agent_unique_wallet_count_7d
    - agent_wallet_value_hhi_7d
    - agent_repeat_wallet_ratio_7d
    - agent_current_wallet_is_new
    - agent_inbound_outbound_value_ratio_7d
    - agent_high_value_event_share_7d
    - agent_hourly_tx_zscore_30d
    - agent_hourly_value_zscore_30d
    - agent_burst_concentration_7d
    - agent_shared_wallet_flow_concentration_7d
    
    Args:
        conn: Database connection
        wallets: List of wallet dicts
        agents: List of agent dicts
        scenario_type: Type of agent scenario (concentration, burst, new_wallets)
        count: Number of transactions to generate
        
    Returns:
        List of transaction tuples
    """
    transactions = []
    current_time = datetime.now(timezone.utc)
    
    if not agents:
        # If no agents available, generate with None agent_id
        agent_id = None
    else:
        agent_id = agents[0]["id"] if scenario_type == "concentration" else random.choice(agents)["id"]
    
    if scenario_type == "concentration":
        # Many wallets using the same agent (concentration)
        for i in range(min(count, len(wallets))):
            wallet = wallets[i]
            amount = random.uniform(500, 3000)
            time_offset = timedelta(minutes=i * random.randint(3, 10))
            timestamp = (current_time - time_offset).isoformat()
            
            transactions.append((
                wallet, wallet, "transfer", amount, timestamp,
                "agent", f"Agent-mediated Cash-In of ${amount:,.2f}",
                "Agent pattern: concentration around single agent", "ZW", agent_id
            ))
    
    elif scenario_type == "burst":
        # Agent processing burst of transactions in short period
        if agents:
            burst_agent = random.choice(agents)
            agent_id = burst_agent["id"]
        
        for i in range(count):
            wallet = random.choice(wallets)
            amount = random.uniform(200, 1500)
            time_offset = timedelta(minutes=i * random.randint(1, 3))
            timestamp = (current_time - time_offset).isoformat()
            
            transactions.append((
                wallet, wallet, "transfer", amount, timestamp,
                "agent", f"Agent burst transaction of ${amount:,.2f}",
                "Agent pattern: burst activity in short time window", "ZW", agent_id
            ))
    
    elif scenario_type == "new_wallets":
        # New wallets interacting with agent (cold-start behavior)
        # In simulation, we simulate this by using wallets with low transaction counts
        new_wallets = [w for w in wallets if w.get("transaction_count", 0) < 5]
        
        if not new_wallets:
            new_wallets = wallets[:min(5, len(wallets))]
        
        for i in range(min(count, len(new_wallets))):
            wallet = new_wallets[i]
            amount = random.uniform(1000, 5000)
            time_offset = timedelta(hours=i * random.randint(2, 4))
            timestamp = (current_time - time_offset).isoformat()
            
            transactions.append((
                wallet, wallet, "transfer", amount, timestamp,
                "agent", f"New wallet Cash-In of ${amount:,.2f}",
                "Agent pattern: new wallet cold-start behavior", "ZW", agent_id
            ))
    
    return transactions


def _scenario_amount(low, high, label):
    """Generate scenario-specific amount with realistic rounding."""
    amount = random.triangular(low, high, low + ((high - low) * 0.35))

    if label == "normal":
        return round(amount, 2)

    if low >= 9000:
        return round(amount / 50) * 50

    return round(amount / 10) * 10


def _simulation_segment_multiplier(segment, label):
    """Apply wealth segment multiplier to transaction amounts."""
    segment = (segment or "average").lower()

    multipliers = {
        "low": {"normal": 0.6, "suspicious": 0.75, "super_suspicious": 0.9},
        "average": {"normal": 1.0, "suspicious": 1.0, "super_suspicious": 1.0},
        "high": {"normal": 1.5, "suspicious": 1.1, "super_suspicious": 1.2},
        "ultra_high": {"normal": 2.0, "suspicious": 1.2, "super_suspicious": 1.3},
    }

    return multipliers.get(segment, multipliers["average"]).get(label, 1.0)


def _parse_timestamp(value):
    """Parse timestamp string to datetime object."""
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return datetime.now(timezone.utc)


def _simulation_transaction(label, users, agents=None):
    """
    Generate one transaction that reflects laundering typologies.
    
    Updated for Stage 17E EcoCash alignment:
    - Uses EcoCash terminology (Cash-In, Cash-Out, Wallet-to-Wallet)
    - Maps legacy types to EcoCash domain
    - Integrates with Stage 13 + Stage 14 pipeline
    """
    if label == "normal":
        scenario = random.choice(NORMAL_TRANSACTION_SCENARIOS)
    elif label == "suspicious":
        scenario = random.choice(SUSPICIOUS_TRANSACTION_SCENARIOS)
    else:
        scenario = random.choice(SUPER_SUSPICIOUS_TRANSACTION_SCENARIOS)

    tx_type = scenario["type"]  # Always "transfer" in DB
    ecocash_type = scenario.get("ecocash_type", "wallet_to_wallet")
    sender = random.choice(users)
    hour = random.choice(scenario["hours"])
    dest_country = scenario.get("destination_country", "ZW")
    description = scenario["description"]
    scenario_reason = scenario.get("reason")

    base_dt = _parse_timestamp(_simulation_timestamp(hour))

    amount = round(
        _scenario_amount(*scenario["amount"], label)
        * _simulation_segment_multiplier(sender["wealth_segment"] or "average", label),
        2,
    )

    if tx_type in ("withdraw", "transfer") and sender["balance"] is not None:
        balance = float(sender["balance"] or 0)
        if balance > 0 and amount > balance * 0.85:
            amount = round(balance * random.uniform(0.35, 0.75), 2)
            amount = max(amount, 1.0)

    # Determine recipient based on EcoCash transaction type
    recipient = sender
    if ecocash_type == "wallet_to_wallet" and len(users) > 1:
        recipient = random.choice([user for user in users if user["id"] != sender["id"]])
    # For cash_in and cash_out, recipient = sender (self-transfer in DB)

    # Assign agent if agents are available and transaction type requires agent
    agent_id = None
    if agents and len(agents) > 0:
        if ecocash_type in ("cash_in", "cash_out"):
            # Cash-In/Cash-Out always use agent
            agent_id = random.choice(agents)["id"]
        elif scenario["channel"] == "agent":
            # Agent-mediated wallet-to-wallet
            agent_id = random.choice(agents)["id"]

    timestamp = _simulation_timestamp(hour)
    return [
        (
            sender, recipient, tx_type, amount, timestamp,
            scenario["channel"], description, scenario_reason, dest_country, agent_id,
        )
    ]


def _simulation_reason(label, amount, tx_type, scenario_reason=None):
    """Generate simulation reason based on transaction label."""
    if label == "normal":
        return "Routine wallet activity consistent with known mobile-money behaviour"

    if label == "suspicious":
        return f"{scenario_reason or 'Suspicious transaction pattern'} involving a {tx_type} of ${amount:,.2f}"

    return f"{scenario_reason or 'High-risk AML pattern'} involving a {tx_type} of ${amount:,.2f}"


def _history_profile(amount, receiver_account, timestamp, history):
    """Build transaction history profile for AI model."""
    amounts = history.get("amounts", [])
    recipients = history.get("recipients", set())
    events = history.get("events", [])
    prior_transactions = history.get("transactions", [])

    amount = float(amount)
    avg_amount = sum(amounts) / len(amounts) if amounts else 0.0
    max_amount = max(amounts) if amounts else 0.0

    current_time = _parse_timestamp(timestamp)
    cutoff = current_time - timedelta(hours=24)
    recent_amounts = [
        float(event_amount)
        for event_time, event_amount in events
        if event_time >= cutoff
    ]
    volume_24h = sum(recent_amounts)

    same_day_count = 0
    same_day_total = 0.0
    same_recipient_count = 0
    rapid_transfer_count = 0

    for prior_tx in prior_transactions:
        try:
            prior_time = _parse_timestamp(prior_tx.get("timestamp"))
            if current_time.date() == prior_time.date():
                same_day_count += 1
                same_day_total += float(prior_tx.get("amount", 0) or 0)
            if prior_time >= cutoff and prior_tx.get("receiver_account") == receiver_account:
                same_recipient_count += 1
            if 0 < (current_time - prior_time).total_seconds() <= 600:
                rapid_transfer_count += 1
        except (TypeError, ValueError):
            continue

    profile = dict(PROFILE_FEATURE_DEFAULTS)
    profile.update({
        "sender_avg_amount": avg_amount,
        "sender_max_amount": max_amount,
        "sender_tx_count": len(amounts),
        "amount_to_sender_avg": amount / avg_amount if avg_amount > 0 else 1.0,
        "amount_to_sender_max": amount / max_amount if max_amount > 0 else 1.0,
        "sender_tx_count_24h": len(recent_amounts),
        "sender_volume_24h": volume_24h,
        "amount_to_sender_volume_24h": amount / volume_24h if volume_24h > 0 else 1.0,
        "is_new_recipient": 0.0 if receiver_account in recipients else 1.0,
        "same_day_count": same_day_count,
        "same_day_total": same_day_total,
        "same_recipient_count": same_recipient_count,
        "rapid_transfer_count": rapid_transfer_count,
    })

    return profile


def _ai_profile_for_transaction(conn, transaction_id, sender_account, receiver_account, amount, timestamp):
    """Build AI profile features for a transaction from database history."""
    cutoff = (_parse_timestamp(timestamp) - timedelta(hours=24)).isoformat()
    tx_date = _parse_timestamp(timestamp).date()

    prior = conn.execute(
        """
        SELECT
            COUNT(*) AS tx_count,
            COALESCE(AVG(amount), 0) AS avg_amount,
            COALESCE(MAX(amount), 0) AS max_amount,
            COALESCE(u.wealth_segment, 'average') AS wealth_segment
        FROM transactions t
        LEFT JOIN users u ON t.sender_account = u.account_number
        WHERE sender_account=? AND (? IS NULL OR t.id<>?) AND timestamp<?
        """,
        (sender_account, transaction_id, transaction_id, timestamp),
    ).fetchone()

    recent = conn.execute(
        """
        SELECT COUNT(*) AS tx_count, COALESCE(SUM(amount), 0) AS volume
        FROM transactions t
        WHERE sender_account=? AND (? IS NULL OR t.id<>?) AND timestamp>=? AND timestamp<?
        """,
        (sender_account, transaction_id, transaction_id, cutoff, timestamp),
    ).fetchone()

    recipient_seen = conn.execute(
        """
        SELECT id FROM transactions t
        WHERE sender_account=? AND receiver_account=? AND (? IS NULL OR t.id<>?) AND timestamp<?
        LIMIT 1
        """,
        (sender_account, receiver_account, transaction_id, transaction_id, timestamp),
    ).fetchone()

    # New structuring and layering features
    same_day_txs = conn.execute(
        """
        SELECT COUNT(*) AS count, COALESCE(SUM(amount), 0) AS total
        FROM transactions t
        WHERE sender_account=? AND (? IS NULL OR t.id<>?) AND DATE(timestamp)=DATE(?)
        """,
        (sender_account, transaction_id, transaction_id, timestamp),
    ).fetchone()

    same_recipient_24h = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM transactions t
        WHERE sender_account=? AND receiver_account=? AND (? IS NULL OR t.id<>?) AND timestamp>=? AND timestamp<?
        """,
        (sender_account, receiver_account, transaction_id, transaction_id, cutoff, timestamp),
    ).fetchone()

    rapid_transfers = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM transactions t
        WHERE sender_account=? AND (? IS NULL OR t.id<>?) AND timestamp>=? AND timestamp<?
        ORDER BY timestamp DESC
        """,
        (sender_account, transaction_id, transaction_id, cutoff, timestamp),
    ).fetchall()

    rapid_count = 0
    if len(rapid_transfers) > 1:
        for i in range(len(rapid_transfers) - 1):
            try:
                curr_time = _parse_timestamp(rapid_transfers[i]["timestamp"])
                prev_time = _parse_timestamp(rapid_transfers[i + 1]["timestamp"])
                if 0 < (curr_time - prev_time).total_seconds() <= 600:
                    rapid_count += 1
            except (TypeError, ValueError):
                continue

    profile = dict(PROFILE_FEATURE_DEFAULTS)
    profile.update({
        "sender_avg_amount": float(prior["avg_amount"] or 0),
        "sender_max_amount": float(prior["max_amount"] or 0),
        "sender_tx_count": prior["tx_count"] or 0,
        "amount_to_sender_avg": amount / float(prior["avg_amount"] or 1) if prior["avg_amount"] else 1.0,
        "amount_to_sender_max": amount / float(prior["max_amount"] or 1) if prior["max_amount"] else 1.0,
        "sender_tx_count_24h": recent["tx_count"] or 0,
        "sender_volume_24h": float(recent["volume"] or 0),
        "amount_to_sender_volume_24h": amount / float(recent["volume"] or 1) if recent["volume"] else 1.0,
        "is_new_recipient": 0.0 if recipient_seen else 1.0,
        "same_day_count": same_day_txs["count"] or 0,
        "same_day_total": float(same_day_txs["total"] or 0),
        "same_recipient_count": same_recipient_24h["count"] or 0,
        "rapid_transfer_count": rapid_count,
    })

    return profile


# Agent scenario generation for agent behaviour analysis
# These scenarios define ground-truth agent behaviour patterns independent of AML rules

AGENT_SCENARIOS = {
    "normal_agent_usage": {
        "description": "Normal agent usage - wallets occasionally use different agents",
        "agent_distribution": "diverse",
        "wallet_agent_ratio": 3.0,  # Each wallet uses ~3 different agents
        "typology": "normal"
    },
    "agent_concentration": {
        "description": "Agent concentration - several wallets repeatedly use the same agent",
        "agent_distribution": "concentrated",
        "wallet_agent_ratio": 0.2,  # Many wallets share few agents
        "typology": "suspicious"
    },
    "suspicious_shared_agent": {
        "description": "Suspicious shared-agent activity - multiple suspicious wallets use the same agent",
        "agent_distribution": "highly_concentrated",
        "wallet_agent_ratio": 0.1,  # Many suspicious wallets share one agent
        "typology": "suspicious"
    },
    "agent_network": {
        "description": "Agent-network behaviour - group of wallets uses same small group of agents",
        "agent_distribution": "clustered",
        "wallet_agent_ratio": 0.5,  # Wallets cluster around agent groups
        "typology": "suspicious"
    },
    "regional_concentration": {
        "description": "Regional concentration - suspicious activity in specific regions",
        "agent_distribution": "regional",
        "wallet_agent_ratio": 0.3,
        "typology": "suspicious"
    },
    "temporal_agent_burst": {
        "description": "Temporal agent behaviour - agent processes burst of transactions in short period",
        "agent_distribution": "temporal",
        "wallet_agent_ratio": 1.0,
        "typology": "suspicious"
    }
}


def generate_agents(conn, num_agents=20):
    """
    Generate synthetic agent records for testing.
    
    Args:
        conn: Database connection
        num_agents: Number of agents to generate
    
    Returns:
        List of agent dictionaries
    """
    regions = ["Harare", "Bulawayo", "Mutare", "Gweru", "Masvingo", "Chinhoyi", "Marondera"]
    cities = {
        "Harare": ["Harare CBD", "Borrowdale", "Avondale", "Mbare", "Highfield"],
        "Bulawayo": ["Bulawayo CBD", "Nkulumane", "Mzilikazi", "Pumula"],
        "Mutare": ["Mutare CBD", "Sakubva", "Dangamvura"],
        "Gweru": ["Gweru CBD", "Midlands State University"],
        "Masvingo": ["Masvingo CBD", "Mucheke"],
        "Chinhoyi": ["Chinhoyi CBD"],
        "Marondera": ["Marondera CBD"]
    }
    
    agents = []
    for i in range(num_agents):
        region = random.choice(regions)
        city = random.choice(cities[region])
        
        agent_code = f"AGT{i+1:04d}"
        agent_name = f"Agent {i+1} - {city}"
        
        agent_id = None
        try:
            from agents import create_agent
            agent_id = create_agent(
                conn,
                agent_code=agent_code,
                agent_name=agent_name,
                location=city,
                region=region,
                city=city,
                status='active'
            )
        except:
            # If agents module not available, create mock agent
            agent_id = i + 1
        
        agents.append({
            "id": agent_id,
            "agent_code": agent_code,
            "agent_name": agent_name,
            "location": city,
            "region": region,
            "city": city,
            "status": "active"
        })
    
    return agents


def assign_agent_to_transaction(scenario_type, agents, wallet_id=None):
    """
    Assign an agent to a transaction based on scenario type.
    
    Args:
        scenario_type: Type of agent scenario (from AGENT_SCENARIOS)
        agents: List of available agents
        wallet_id: Wallet identifier for consistent assignment
    
    Returns:
        Agent ID or None
    """
    if not agents or len(agents) == 0:
        return None
    
    scenario = AGENT_SCENARIOS.get(scenario_type, AGENT_SCENARIOS["normal_agent_usage"])
    
    if scenario["agent_distribution"] == "diverse":
        # Normal: random agent assignment
        return random.choice(agents)["id"]
    
    elif scenario["agent_distribution"] == "concentrated":
        # Concentrated: bias toward first few agents
        if random.random() < 0.7:
            return agents[random.randint(0, min(4, len(agents)-1))]["id"]
        return random.choice(agents)["id"]
    
    elif scenario["agent_distribution"] == "highly_concentrated":
        # Highly concentrated: mostly use first agent
        if random.random() < 0.9:
            return agents[0]["id"]
        return random.choice(agents)["id"]
    
    elif scenario["agent_distribution"] == "clustered":
        # Clustered: use small group of agents
        cluster_start = (wallet_id or 0) % max(1, len(agents) // 3)
        cluster_agents = agents[cluster_start:cluster_start + 3]
        return random.choice(cluster_agents)["id"]
    
    elif scenario["agent_distribution"] == "regional":
        # Regional: bias toward agents in same region
        regional_agents = [a for a in agents if a["region"] == agents[0]["region"]]
        if regional_agents and random.random() < 0.8:
            return random.choice(regional_agents)["id"]
        return random.choice(agents)["id"]
    
    elif scenario["agent_distribution"] == "temporal":
        # Temporal: use same agent for burst
        return agents[0]["id"]
    
    return random.choice(agents)["id"]
