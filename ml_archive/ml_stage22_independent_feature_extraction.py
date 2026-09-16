"""
STAGE 22: Independent Dataset Feature Extraction

Extract Chapter 1 features from the independent evaluation dataset.
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List

HIGH_RISK_COUNTRIES = {
    "IR", "KP", "MM", "RU", "SY", "YE", "ML", "BF", "SO", "CD", "IQ", "SD", "SS",
    "CU", "ZW", "VE", "AF", "LR", "HT"
}

DOMESTIC_COUNTRY = "ZW"


def load_independent_dataset():
    """Load independent dataset."""
    print("Loading independent dataset...")
    df = pd.read_csv("ml_stage22_independent_dataset.csv")
    
    with open("ml_stage22_independent_ground_truth.json") as f:
        gt = json.load(f)
    gt_dict = {g["transaction_id"]: g for g in gt}
    
    print(f"Loaded {len(df)} transactions")
    return df, gt_dict


def extract_features(df):
    """Extract features from independent dataset."""
    print("Extracting features from independent dataset...")
    
    # Add existing features (already in dataset)
    # Calculate hour and is_off_hours from timestamp
    df['hour'] = df['timestamp'].apply(
        lambda x: datetime.fromisoformat(x.replace('Z', '+00:00')).hour
    )
    df['is_off_hours'] = df['hour'].apply(
        lambda x: 1.0 if x < 8 or x > 17 else 0.0
    )
    
    # Add cross-border features
    df['is_cross_border'] = df['destination_country'].apply(
        lambda x: 1.0 if x != DOMESTIC_COUNTRY else 0.0
    )
    df['is_high_risk_country'] = df['destination_country'].apply(
        lambda x: 1.0 if x in HIGH_RISK_COUNTRIES else 0.0
    )
    
    # Calculate cross-border aggregations per customer
    cross_border_features = []
    
    for customer_id in df['sender_account'].unique():
        customer_df = df[df['sender_account'] == customer_id].sort_values('timestamp')
        
        for idx, row in customer_df.iterrows():
            # Get historical transactions
            historical_txs = customer_df[customer_df.index < idx].to_dict('records')
            current_time = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
            
            # Filter historical transactions within 7 days
            seven_days_ago = current_time - timedelta(days=7)
            recent_historical = [
                tx for tx in historical_txs
                if datetime.fromisoformat(tx['timestamp'].replace('Z', '+00:00')) >= seven_days_ago
            ]
            
            # Calculate cross-border features
            cross_border_count = sum(
                1 for tx in recent_historical
                if tx.get('destination_country', DOMESTIC_COUNTRY) != DOMESTIC_COUNTRY
            )
            cross_border_volume = sum(
                tx['amount'] for tx in recent_historical
                if tx.get('destination_country', DOMESTIC_COUNTRY) != DOMESTIC_COUNTRY
            )
            total_volume = sum(tx['amount'] for tx in recent_historical)
            
            cross_border_ratio = cross_border_volume / total_volume if total_volume > 0 else 0.0
            
            cross_border_features.append({
                'transaction_id': row['transaction_id'],
                'cross_border_count_7d': float(cross_border_count),
                'cross_border_volume_7d': float(cross_border_volume),
                'cross_border_ratio_7d': float(cross_border_ratio)
            })
    
    cross_border_df = pd.DataFrame(cross_border_features)
    df = df.merge(cross_border_df, on='transaction_id', how='left')
    
    # Fill NaN values
    df['cross_border_count_7d'] = df['cross_border_count_7d'].fillna(0.0)
    df['cross_border_volume_7d'] = df['cross_border_volume_7d'].fillna(0.0)
    df['cross_border_ratio_7d'] = df['cross_border_ratio_7d'].fillna(0.0)
    
    # Add sequence features
    sequence_features = []
    
    for customer_id in df['sender_account'].unique():
        customer_df = df[df['sender_account'] == customer_id].sort_values('timestamp')
        
        for idx, row in customer_df.iterrows():
            historical_txs = customer_df[customer_df.index < idx].to_dict('records')
            current_time = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
            
            # Get last 3 transaction types
            recent_txs = sorted(
                historical_txs,
                key=lambda x: datetime.fromisoformat(x['timestamp'].replace('Z', '+00:00')),
                reverse=True
            )[:3]
            
            # Calculate time since last transaction
            if recent_txs:
                last_tx_time = datetime.fromisoformat(recent_txs[0]['timestamp'].replace('Z', '+00:00'))
                time_since_last = (current_time - last_tx_time).total_seconds() / 3600
            else:
                time_since_last = 999999.0
            
            # Calculate recurring pattern score
            if len(recent_txs) >= 2:
                amounts = [tx['amount'] for tx in recent_txs[:2]]
                recipients = [tx.get('receiver_account', '') for tx in recent_txs[:2]]
                amount_similarity = 1.0 if abs(amounts[0] - amounts[1]) < 100 else 0.0
                recipient_similarity = 1.0 if recipients[0] == recipients[1] else 0.0
                recurring_score = (amount_similarity + recipient_similarity) / 2.0
            else:
                recurring_score = 0.0
            
            sequence_features.append({
                'transaction_id': row['transaction_id'],
                'time_since_last_transaction_hours': float(time_since_last),
                'recurring_pattern_score': float(recurring_score)
            })
    
    sequence_df = pd.DataFrame(sequence_features)
    df = df.merge(sequence_df, on='transaction_id', how='left')
    
    # Fill NaN values
    df['time_since_last_transaction_hours'] = df['time_since_last_transaction_hours'].fillna(999999.0)
    df['recurring_pattern_score'] = df['recurring_pattern_score'].fillna(0.0)
    
    # Add structuring features
    structuring_features = []
    ctr_threshold = 10000.0
    
    for customer_id in df['sender_account'].unique():
        customer_df = df[df['sender_account'] == customer_id].sort_values('timestamp')
        
        for idx, row in customer_df.iterrows():
            historical_txs = customer_df[customer_df.index < idx].to_dict('records')
            current_time = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
            
            # Get same-day transactions
            same_day_txs = [
                tx for tx in historical_txs
                if datetime.fromisoformat(tx['timestamp'].replace('Z', '+00:00')).date() == current_time.date()
            ]
            
            # Calculate same-day cumulative amount
            same_day_total = sum(tx['amount'] for tx in same_day_txs) + row['amount']
            
            # Check if amount is near threshold
            amount_near_threshold = 1.0 if 8500 <= row['amount'] <= 9999 else 0.0
            
            # Calculate structuring pattern score
            near_threshold_count = sum(
                1 for tx in same_day_txs
                if 8500 <= tx['amount'] <= 9999
            )
            structuring_score = min(near_threshold_count / 3.0, 1.0)
            
            structuring_features.append({
                'transaction_id': row['transaction_id'],
                'amount_near_threshold_flag': float(amount_near_threshold),
                'same_day_cumulative_amount': float(same_day_total),
                'structuring_pattern_score': float(structuring_score)
            })
    
    structuring_df = pd.DataFrame(structuring_features)
    df = df.merge(structuring_df, on='transaction_id', how='left')
    
    # Fill NaN values
    df['amount_near_threshold_flag'] = df['amount_near_threshold_flag'].fillna(0.0)
    df['same_day_cumulative_amount'] = df['same_day_cumulative_amount'].fillna(0.0)
    df['structuring_pattern_score'] = df['structuring_pattern_score'].fillna(0.0)
    
    # Add placeholder features for missing ones
    missing_features = [
        'amount_z_score', 'amount_deviation_from_baseline_30d',
        'tx_frequency_7d', 'tx_frequency_30d', 'frequency_change_vs_avg_7d',
        'unique_recipients_7d', 'counterparty_change_score_7d'
    ]
    
    for f in missing_features:
        if f not in df.columns:
            df[f] = 0.0
    
    print("Feature extraction complete")
    return df


def save_features(df, output_file="ml_stage22_independent_features.csv"):
    """Save features to CSV."""
    print(f"Saving features to {output_file}...")
    
    # Select feature columns
    non_feature_cols = ['transaction_id', 'sender_account', 'customer_id', 'receiver_account',
                      'transaction_type', 'channel', 'timestamp', 'description', 'destination_country']
    feature_cols = [col for col in df.columns if col not in non_feature_cols]
    
    df_final = df[['transaction_id', 'sender_account'] + feature_cols].copy()
    df_final.to_csv(output_file, index=False)
    
    print(f"Saved {len(df_final)} transactions with {len(feature_cols)} features")
    return df_final


if __name__ == "__main__":
    print("=" * 80)
    print("STAGE 22: INDEPENDENT DATASET FEATURE EXTRACTION")
    print("=" * 80)
    print()
    
    df, gt_dict = load_independent_dataset()
    df = extract_features(df)
    df_final = save_features(df)
    
    print()
    print("=" * 80)
    print("FEATURE EXTRACTION COMPLETE")
    print("=" * 80)
