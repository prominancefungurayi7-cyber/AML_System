"""Frozen V3 Stage 10 feature contract.

The extractor imports this module only for the ordered public feature list.
Private generator and ground-truth fields are deliberately absent.
"""
from __future__ import annotations

FEATURES = (
    ('current_amount_usd', 'current', 'current transaction amount / 100 USD', 'current'),
    ('current_is_cash_in', 'current', '1 iff current transaction_type is cash_in', 'current'),
    ('current_is_cash_out', 'current', '1 iff current transaction_type is cash_out', 'current'),
    ('wallet_count_1h_inclusive', 'structuring', 'count of subject-wallet events in [T-1h,T]', 'prior+current'),
    ('wallet_value_24h_inclusive', 'structuring', 'sum of subject-wallet amounts in [T-24h,T]', 'prior+current'),
    ('wallet_count_utc_day_inclusive', 'structuring', 'count of subject-wallet events since UTC midnight through T', 'prior+current'),
    ('wallet_active_hours_utc_day', 'structuring', 'distinct UTC hour buckets for subject-wallet events since midnight through T', 'prior+current'),
    ('wallet_current_amount_cluster_share_7d', 'structuring', 'share of subject-wallet events in [T-7d,T] within 5% of current amount', 'prior+current'),
    ('wallet_band_share_7d_inclusive', 'structuring', 'share of subject-wallet events in [T-7d,T] in 7000..10500 USD', 'prior+current'),
    ('wallet_count_acceleration_1h', 'structuring', 'inclusive 1h count / max(1, prior-28d count / 672)', 'prior+current'),
    ('receiver_unique_sources_24h_inclusive', 'network', 'distinct W2W senders to receiver in [T-24h,T]', 'prior+current'),
    ('receiver_inflow_count_24h_inclusive', 'network', 'W2W inflow count to receiver in [T-24h,T]', 'prior+current'),
    ('receiver_inflow_acceleration_24h', 'network', 'inclusive receiver inflow count / max(1, prior-28d inflow count / 28)', 'prior+current'),
    ('sender_unique_destinations_24h_inclusive', 'network', 'distinct W2W receivers from sender in [T-24h,T]', 'prior+current'),
    ('sender_outflow_count_24h_inclusive', 'network', 'W2W outflow count from sender in [T-24h,T]', 'prior+current'),
    ('sender_outflow_acceleration_24h', 'network', 'inclusive sender outflow count / max(1, prior-28d count / 28)', 'prior+current'),
    ('current_return_path_length', 'network', 'shortest simple prior path receiver to sender, 1..5 edges in 7d; zero otherwise', 'prior-only plus current endpoints'),
    ('current_return_amount_ratio', 'network', 'current amount / first-edge amount of selected prior return path; -1 when absent', 'prior-only plus current amount'),
    ('wallet_observed_onward_funding_share_24h', 'network', 'observed outward value after prior funding anchor / observed funding value', 'prior+current for outflow'),
    ('wallet_prior_funding_age_hours', 'network', 'hours from prior funding anchor to current outflow; -1 when absent', 'prior-only plus current timestamp'),
    ('agent_service_count_1h_inclusive', 'agent', 'agent service-event count in [T-1h,T]; zero for direct W2W', 'prior+current'),
    ('agent_service_acceleration_1h', 'agent', 'inclusive service count / max(1, preceding-28d service count / 672); -1 if coverage insufficient', 'prior+current'),
    ('agent_wallet_growth_ratio_7d', 'agent', 'recent inclusive distinct serviced wallets / max(1, median of four preceding 7d counts); -1 if insufficient', 'prior+current'),
    ('agent_new_wallet_share_7d', 'agent', 'recent serviced-wallet fraction absent from preceding-28d wallet union; -1 if insufficient', 'prior+current'),
    ('agent_top2_count_share_24h', 'agent', 'top-two serviced-wallet service-event share in [T-24h,T]', 'prior+current'),
    ('agent_top2_share_change_24h', 'agent', 'inclusive top-two share minus preceding-28d top-two share; -1 if insufficient', 'prior+current'),
    ('agent_cash_value_skew_24h', 'agent', '(CashOut value-CashIn value)/(sum) in [T-24h,T]', 'prior+current'),
    ('agent_cash_count_skew_24h', 'agent', 'corresponding signed event-count skew in [T-24h,T]', 'prior+current'),
    ('agent_cash_value_skew_change', 'agent', 'inclusive cash value skew minus preceding-28d cash value skew; -1 if insufficient', 'prior+current'),
    ('wallet_history_coverage_days', 'coverage', 'partition-local subject-wallet observation span before T, capped at 28 days', 'prior-only'),
    ('receiver_history_coverage_days', 'coverage', 'partition-local receiver observation span before T, capped at 28 days', 'prior-only'),
    ('agent_history_coverage_days', 'coverage', 'partition-local agent observation span before T, capped at 28 days; zero without agent', 'prior-only'),
)

FEATURE_NAMES = tuple(x[0] for x in FEATURES)
GROUPS = {'current': 3, 'structuring': 7, 'network': 10, 'agent': 9, 'coverage': 3}
MISSING_VALUE = -1.0
AMOUNT_BAND_USD = (7000.0, 10500.0)

if len(FEATURE_NAMES) != 32 or len(set(FEATURE_NAMES)) != 32:
    raise RuntimeError('Stage 10 feature contract must contain 32 unique ordered names')
