"""
STAGE 24: Complete Feature Extraction

Extract all 28 prediction-time features with no placeholders.
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from scipy import stats

HIGH_RISK_COUNTRIES = {
    "IR", "KP", "MM", "RU", "SY", "YE", "ML", "BF", "SO", "CD", "IQ", "SD", "SS",
    "CU", "ZW", "VE", "AF", "LR", "HT"
}

DOMESTIC_COUNTRY = "ZW"
CTR_THRESHOLD = 10000.0


def load_dataset(dataset_file="ml_stage24_diverse_dataset.csv", ground_truth_file="ml_stage24_diverse_ground_truth.json"):
    """Load Stage 24 dataset."""
    print(f"Loading dataset from {dataset_file}...")
    df = pd.read_csv(dataset_file)
    
    with open(ground_truth_file) as f:
        gt = json.load(f)
    gt_dict = {g["transaction_id"]: g for g in gt}
    
    df['ground_truth_label'] = df['transaction_id'].map(
        lambda x: gt_dict.get(x, {}).get('ground_truth_label', 'normal')
    )
    
    print(f"Loaded {len(df)} transactions")
    return df, gt_dict


def extract_all_features(df):
    """Extract all 28 features with proper calculation."""
    print("Extracting all 28 features...")
    
    # Convert timestamp to datetime
    df['timestamp_dt'] = df['timestamp'].apply(
        lambda x: datetime.fromisoformat(x.replace('Z', '+00:00'))
    )
    
    # Sort by customer and timestamp
    df = df.sort_values(['sender_account', 'timestamp_dt'])
    
    # Initialize all feature columns
    feature_cols = [
        'amount', 'sender_avg_amount', 'sender_max_amount', 'amount_to_sender_avg',
        'amount_z_score', 'amount_deviation_from_baseline_30d',
        'tx_frequency_7d', 'tx_frequency_30d', 'frequency_change_vs_avg_7d',
        'sender_tx_count_24h', 'sender_volume_24h', 'amount_to_sender_volume_24h',
        'is_new_recipient', 'unique_recipients_7d', 'counterparty_change_score_7d',
        'hour', 'is_off_hours', 'time_since_last_transaction_hours',
        'same_day_count', 'same_day_total', 'rapid_transfer_count', 'recurring_pattern_score',
        'is_cross_border', 'is_high_risk_country', 'cross_border_count_7d',
        'cross_border_volume_7d', 'cross_border_ratio_7d',
        'amount_near_threshold_flag', 'same_day_cumulative_amount', 'structuring_pattern_score'
    ]
    
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0.0
    
    # Calculate features per customer
    for customer_id in df['sender_account'].unique():
        customer_df = df[df['sender_account'] == customer_id].copy()
        
        for idx, row in customer_df.iterrows():
            current_time = row['timestamp_dt']
            current_amount = row['amount']
            current_receiver = row['receiver_account']
            current_country = row['destination_country']
            
            # Historical transactions before current
            historical = customer_df[customer_df['timestamp_dt'] < current_time]
            
            # Amount features
            if len(historical) > 0:
                amounts = historical['amount'].values
                df.loc[idx, 'sender_avg_amount'] = np.mean(amounts)
                df.loc[idx, 'sender_max_amount'] = np.max(amounts)
                avg_amount = np.mean(amounts)
                if avg_amount > 0:
                    df.loc[idx, 'amount_to_sender_avg'] = current_amount / avg_amount
                else:
                    df.loc[idx, 'amount_to_sender_avg'] = 1.0
                
                # Z-score
                if len(amounts) > 1:
                    std_amount = np.std(amounts)
                    if std_amount > 0:
                        df.loc[idx, 'amount_z_score'] = (current_amount - np.mean(amounts)) / std_amount
                    else:
                        df.loc[idx, 'amount_z_score'] = 0.0
                
                # 30-day deviation
                thirty_days_ago = current_time - timedelta(days=30)
                recent_amounts = historical[historical['timestamp_dt'] >= thirty_days_ago]['amount'].values
                if len(recent_amounts) > 0:
                    df.loc[idx, 'amount_deviation_from_baseline_30d'] = current_amount - np.mean(recent_amounts)
            else:
                df.loc[idx, 'sender_avg_amount'] = current_amount
                df.loc[idx, 'sender_max_amount'] = current_amount
                df.loc[idx, 'amount_to_sender_avg'] = 1.0
            
            # Frequency features
            seven_days_ago = current_time - timedelta(days=7)
            thirty_days_ago = current_time - timedelta(days=30)
            
            tx_count_7d = len(historical[historical['timestamp_dt'] >= seven_days_ago])
            tx_count_30d = len(historical[historical['timestamp_dt'] >= thirty_days_ago])
            
            df.loc[idx, 'tx_frequency_7d'] = tx_count_7d
            df.loc[idx, 'tx_frequency_30d'] = tx_count_30d
            
            if len(historical) >= 30:
                avg_daily_freq = len(historical) / 30.0
                df.loc[idx, 'frequency_change_vs_avg_7d'] = (tx_count_7d / 7.0) - avg_daily_freq
            
            # 24-hour features
            twenty_four_hours_ago = current_time - timedelta(hours=24)
            recent_24h = historical[historical['timestamp_dt'] >= twenty_four_hours_ago]
            
            df.loc[idx, 'sender_tx_count_24h'] = len(recent_24h)
            volume_24h = recent_24h['amount'].sum() if len(recent_24h) > 0 else 0.0
            df.loc[idx, 'sender_volume_24h'] = volume_24h
            if volume_24h > 0:
                df.loc[idx, 'amount_to_sender_volume_24h'] = current_amount / volume_24h
            else:
                df.loc[idx, 'amount_to_sender_volume_24h'] = 1.0
            
            # Recipient features
            past_receivers = set(historical['receiver_account'].values)
            df.loc[idx, 'is_new_recipient'] = 1.0 if current_receiver not in past_receivers else 0.0
            df.loc[idx, 'unique_recipients_7d'] = len(set(
                historical[historical['timestamp_dt'] >= seven_days_ago]['receiver_account'].values
            ))
            
            if len(historical) > 0:
                recent_receivers = set(historical[historical['timestamp_dt'] >= seven_days_ago]['receiver_account'].values)
                if len(past_receivers) > 0:
                    df.loc[idx, 'counterparty_change_score_7d'] = len(recent_receivers) / len(past_receivers)
                else:
                    df.loc[idx, 'counterparty_change_score_7d'] = 0.0
            
            # Timing features
            df.loc[idx, 'hour'] = current_time.hour
            df.loc[idx, 'is_off_hours'] = 1.0 if current_time.hour < 8 or current_time.hour > 17 else 0.0
            
            if len(historical) > 0:
                last_tx = historical.iloc[-1]
                time_since_last = (current_time - last_tx['timestamp_dt']).total_seconds() / 3600
                df.loc[idx, 'time_since_last_transaction_hours'] = time_since_last
            else:
                df.loc[idx, 'time_since_last_transaction_hours'] = 999999.0
            
            # Pattern features
            same_day_txs = historical[historical['timestamp_dt'].dt.date == current_time.date()]
            df.loc[idx, 'same_day_count'] = len(same_day_txs)
            df.loc[idx, 'same_day_total'] = same_day_txs['amount'].sum() if len(same_day_txs) > 0 else 0.0
            
            # Rapid transfers (within 1 hour)
            one_hour_ago = current_time - timedelta(hours=1)
            rapid_count = len(historical[historical['timestamp_dt'] >= one_hour_ago])
            df.loc[idx, 'rapid_transfer_count'] = rapid_count
            
            # Recurring pattern (similar amount to same recipient)
            if len(historical) > 0:
                same_recipient_txs = historical[historical['receiver_account'] == current_receiver]
                if len(same_recipient_txs) > 0:
                    amounts = same_recipient_txs['amount'].values
                    if len(amounts) > 0:
                        amount_similarity = 1.0 if any(abs(a - current_amount) < 100 for a in amounts) else 0.0
                        df.loc[idx, 'recurring_pattern_score'] = amount_similarity
            
            # Cross-border features
            df.loc[idx, 'is_cross_border'] = 1.0 if current_country != DOMESTIC_COUNTRY else 0.0
            df.loc[idx, 'is_high_risk_country'] = 1.0 if current_country in HIGH_RISK_COUNTRIES else 0.0
            
            cross_border_7d = historical[historical['timestamp_dt'] >= seven_days_ago]
            cross_border_txs = cross_border_7d[cross_border_7d['destination_country'] != DOMESTIC_COUNTRY]
            
            df.loc[idx, 'cross_border_count_7d'] = len(cross_border_txs)
            df.loc[idx, 'cross_border_volume_7d'] = cross_border_txs['amount'].sum()
            
            total_volume_7d = cross_border_7d['amount'].sum()
            if total_volume_7d > 0:
                df.loc[idx, 'cross_border_ratio_7d'] = df.loc[idx, 'cross_border_volume_7d'] / total_volume_7d
            else:
                df.loc[idx, 'cross_border_ratio_7d'] = 0.0
            
            # Structuring features
            df.loc[idx, 'amount_near_threshold_flag'] = 1.0 if 8500 <= current_amount <= 9999 else 0.0
            df.loc[idx, 'same_day_cumulative_amount'] = df.loc[idx, 'same_day_total'] + current_amount
            
            # Structuring pattern (multiple near-threshold same-day)
            near_threshold_count = len(same_day_txs[
                (same_day_txs['amount'] >= 8500) & (same_day_txs['amount'] <= 9999)
            ])
            df.loc[idx, 'structuring_pattern_score'] = min(near_threshold_count / 3.0, 1.0)
    
    # Fill NaN values with 0
    df = df.fillna(0)
    
    print("Feature extraction complete")
    return df


def save_features(df, output_file="ml_stage24_diverse_features.csv"):
    """Save features to CSV."""
    print(f"Saving features to {output_file}...")
    
    # Select feature columns (exclude ground_truth_label)
    non_feature_cols = ['transaction_id', 'sender_account', 'ground_truth_label']
    feature_cols = [col for col in df.columns if col not in non_feature_cols]
    
    df_final = df[['transaction_id', 'sender_account'] + feature_cols].copy()
    df_final.to_csv(output_file, index=False)
    
    print(f"Saved {len(df_final)} transactions with {len(feature_cols)} features")
    return df_final, feature_cols


if __name__ == "__main__":
    import sys
    
    print("=" * 80)
    print("STAGE 24: COMPLETE FEATURE EXTRACTION")
    print("=" * 80)
    print()
    
    # Check if independent dataset is requested
    if len(sys.argv) > 1 and sys.argv[1] == "independent":
        dataset_file = "ml_stage24_independent_dataset.csv"
        ground_truth_file = "ml_stage24_independent_ground_truth.json"
        output_file = "ml_stage24_independent_features.csv"
    else:
        dataset_file = "ml_stage24_diverse_dataset.csv"
        ground_truth_file = "ml_stage24_diverse_ground_truth.json"
        output_file = "ml_stage24_diverse_features.csv"
    
    df, gt_dict = load_dataset(dataset_file, ground_truth_file)
    df = extract_all_features(df)
    df_final, feature_cols = save_features(df, output_file)
    
    print()
    print(f"Feature count: {len(feature_cols)}")
    print(f"Features: {feature_cols}")
    print()
    print("=" * 80)
    print("FEATURE EXTRACTION COMPLETE")
    print("=" * 80)
