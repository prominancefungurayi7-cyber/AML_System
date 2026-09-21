"""Investigation leads from the frozen feature vector, not model attribution.

The descriptive cutoffs below do not change model inputs, scores or decisions.
Reporting bands refer to this prototype's synthetic data, not legal thresholds.
"""
import math


def explain_features(features, is_suspicious):
    """Describe supported observations without inferring criminal intent."""
    if len(features) != 30 or not all(math.isfinite(float(v)) for v in features):
        raise ValueError("Explanation requires 30 finite model features")
    if not is_suspicious:
        return (
            "The model did not flag a suspicious pattern. This does not establish "
            "that the transaction is legitimate; review any separate rule or screening findings."
        )

    observations = []
    activities = []
    if features[0] >= 4:
        observations.append(
            f"The sender made {features[0]:.0f} earlier outgoing transactions in the preceding hour."
        )
        activities.append("Rapid movement of funds may indicate layering.")
        if features[5] >= 0.5:
            observations.append(
                f"{features[5]:.0%} of the sender's earlier amounts over 7 days were "
                "between $9,000 and $10,000, below the prototype's synthetic $10,000 threshold."
            )
            activities.append(
                "Repeated transactions below that threshold may indicate structuring "
                "(splitting funds into smaller transactions)."
            )
        if features[3] >= 0.5:
            observations.append(
                f"{features[3]:.0%} of the sender's earlier amounts over 7 days were "
                "within 5% of this transaction's amount."
            )

    if features[6] >= 5:
        observations.append(
            f"The sender paid {features[6]:.0f} distinct counterparties in the preceding 7 days."
        )
        activities.append(
            "Distribution across multiple wallets may indicate fan-out layering; "
            "check whether the recipients have a legitimate business relationship."
        )

    if features[0] >= 3 and 0.8 <= features[14] <= 1.2:
        observations.append(
            f"The sender's earlier outgoing value was {features[14]:.0%} of its "
            "incoming value over 24 hours, alongside repeated outgoing transactions."
        )
        activities.append(
            "Similar incoming and outgoing totals may indicate a pass-through wallet "
            "used for layering; verify the timing and source of the funds."
        )

    if features[17] >= 20 and (features[26] >= 3 or features[27] >= 3):
        observations.append(
            "For this hour of the day, the agent's historical transaction-count "
            f"deviation is {features[26]:.1f} standard deviations and value deviation "
            f"is {features[27]:.1f}, comparing hour-of-day totals over the preceding 30 days."
        )
        activities.append(
            "Concentrated agent activity at this time of day may indicate coordinated fund movement; "
            "review the participating wallets and the agent's business activity."
        )

    if not observations:
        return (
            "The model score crossed its review threshold, but the available indicators "
            "do not support a specific plain-language pattern explanation. Possible activity: "
            "undetermined. Review the transaction history and source of funds before assigning "
            "a money-laundering typology."
        )
    return (
        "Observed indicators: " + " ".join(observations)
        + " Possible activity: " + " ".join(activities)
        + " These are history-based investigation leads, not model feature attributions "
        "or proof of money laundering."
    )
