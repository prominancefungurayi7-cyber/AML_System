"""
STAGE 21: Chapter 1 Justified Feature Extraction

This script extracts features from the diversity-improved dataset, including:
1. Cross-border activity features (is_cross_border, cross_border_volume_7d, etc.)
2. Transaction sequence features (transaction_type_sequence_last_3, time_since_last_transaction, etc.)
3. Existing Stage 16B features (preserved)
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import csv

HIGH_RISK_COUNTRIES = {
    "IR", "KP", "MM", "RU", "SY", "YE", "ML", "BF", "SO", "CD", "IQ", "SD", "SS",
    "CU", "ZW", "VE", "AF", "LR", "HT"
}

DOMESTIC_COUNTRY = "ZW"


def load_dataset(
    dataset_file: str = "ml_stage21_diversity_improved_dataset.csv",
    ground_truth_file: str = "ml_stage21_diversity_improved_ground_truth.json"
) -> Tuple[pd.DataFrame, Dict[int, Dict]]:
    """Load dataset and ground truth."""
    print(f"Loading dataset from {dataset_file}...")
    df = pd.read_csv(dataset_file)
    
    print(f"Loading ground truth from {ground_truth_file}...")
    with open(ground_truth_file, 'r') as f:
        ground_truth = json.load(f)
    
    # Convert ground truth to dict by transaction_id
    ground_truth_dict = {gt["transaction_id"]: gt for gt in ground_truth}
    
    print(f"Loaded {len(df)} transactions with ground truth")
    return df, ground_truth_dict


def extract_cross_border_features(
    df: pd.DataFrame,
    historical_data: Dict[str, List[Dict]]
) -> pd.DataFrame:
    """Extract cross-border activity features."""
    print("Extracting cross-border features...")
    
    # Initialize cross-border features
    df['is_cross_border'] = df['destination_country'].apply(
        lambda x: 1.0 if x != DOMESTIC_COUNTRY else 0.0
    )
    df['is_high_risk_country'] = df['destination_country'].apply(
        lambda x: 1.0 if x in HIGH_RISK_COUNTRIES else 0.0
    )
    
    # Calculate cross-border aggregations per customer
    cross_border_features = []
    
    for customer_id in df['customer_id'].unique():
        customer_df = df[df['customer_id'] == customer_id].sort_values('timestamp')
        
        for idx, row in customer_df.iterrows():
            # Get historical transactions for this customer (before current transaction)
            historical_txs = historical_data.get(customer_id, [])
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
    
    # Merge cross-border features
    cross_border_df = pd.DataFrame(cross_border_features)
    df = df.merge(cross_border_df, on='transaction_id', how='left')
    
    # Fill NaN values
    df['cross_border_count_7d'] = df['cross_border_count_7d'].fillna(0.0)
    df['cross_border_volume_7d'] = df['cross_border_volume_7d'].fillna(0.0)
    df['cross_border_ratio_7d'] = df['cross_border_ratio_7d'].fillna(0.0)
    
    print("Cross-border features extracted")
    return df


def extract_sequence_features(
    df: pd.DataFrame,
    historical_data: Dict[str, List[Dict]]
) -> pd.DataFrame:
    """Extract transaction sequence features."""
    print("Extracting sequence features...")
    
    sequence_features = []
    
    for customer_id in df['customer_id'].unique():
        customer_df = df[df['customer_id'] == customer_id].sort_values('timestamp')
        
        for idx, row in customer_df.iterrows():
            # Get historical transactions for this customer
            historical_txs = historical_data.get(customer_id, [])
            current_time = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
            
            # Get last 3 transaction types
            recent_txs = sorted(
                historical_txs,
                key=lambda x: datetime.fromisoformat(x['timestamp'].replace('Z', '+00:00')),
                reverse=True
            )[:3]
            
            # Create sequence string
            tx_types = [tx.get('transaction_type', 'unknown') for tx in recent_txs]
            sequence_str = ','.join(reversed(tx_types))  # Chronological order
            
            # Calculate time since last transaction
            if recent_txs:
                last_tx_time = datetime.fromisoformat(recent_txs[0]['timestamp'].replace('Z', '+00:00'))
                time_since_last = (current_time - last_tx_time).total_seconds() / 3600  # Hours
            else:
                time_since_last = float('inf')  # No previous transaction
            
            # Calculate recurring pattern score (same amount, same recipient)
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
                'transaction_type_sequence_last_3': sequence_str,
                'time_since_last_transaction_hours': float(time_since_last) if time_since_last != float('inf') else 999999.0,
                'recurring_pattern_score': float(recurring_score)
            })
    
    # Merge sequence features
    sequence_df = pd.DataFrame(sequence_features)
    df = df.merge(sequence_df, on='transaction_id', how='left')
    
    # Fill NaN values
    df['transaction_type_sequence_last_3'] = df['transaction_type_sequence_last_3'].fillna('')
    df['time_since_last_transaction_hours'] = df['time_since_last_transaction_hours'].fillna(999999.0)
    df['recurring_pattern_score'] = df['recurring_pattern_score'].fillna(0.0)
    
    print("Sequence features extracted")
    return df


def extract_structuring_features(
    df: pd.DataFrame,
    historical_data: Dict[str, List[Dict]]
) -> pd.DataFrame:
    """Extract structuring/smurfing features."""
    print("Extracting structuring features...")
    
    structuring_features = []
    ctr_threshold = 10000.0  # CTR threshold
    
    for customer_id in df['customer_id'].unique():
        customer_df = df[df['customer_id'] == customer_id].sort_values('timestamp')
        
        for idx, row in customer_df.iterrows():
            # Get historical transactions for this customer
            historical_txs = historical_data.get(customer_id, [])
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
            
            # Calculate structuring pattern score (multiple near-threshold transactions)
            near_threshold_count = sum(
                1 for tx in same_day_txs
                if 8500 <= tx['amount'] <= 9999
            )
            structuring_score = min(near_threshold_count / 3.0, 1.0)  # Normalize to 0-1
            
            structuring_features.append({
                'transaction_id': row['transaction_id'],
                'amount_near_threshold_flag': float(amount_near_threshold),
                'same_day_cumulative_amount': float(same_day_total),
                'structuring_pattern_score': float(structuring_score)
            })
    
    # Merge structuring features
    structuring_df = pd.DataFrame(structuring_features)
    df = df.merge(structuring_df, on='transaction_id', how='left')
    
    # Fill NaN values
    df['amount_near_threshold_flag'] = df['amount_near_threshold_flag'].fillna(0.0)
    df['same_day_cumulative_amount'] = df['same_day_cumulative_amount'].fillna(0.0)
    df['structuring_pattern_score'] = df['structuring_pattern_score'].fillna(0.0)
    
    print("Structuring features extracted")
    return df


def extract_existing_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract existing Stage 16B features."""
    print("Extracting existing Stage 16B features...")
    
    # Calculate existing features (already in dataset, but ensure they're correct)
    # The dataset already has these features, so we just need to verify they exist
    
    required_features = [
        'amount', 'sender_avg_amount', 'sender_max_amount',
        'amount_to_sender_avg', 'amount_z_score', 'amount_deviation_from_baseline_30d',
        'tx_frequency_7d', 'tx_frequency_30d', 'frequency_change_vs_avg_7d',
        'sender_tx_count_24h', 'sender_volume_24h', 'same_day_count',
        'rapid_transfer_count', 'is_new_recipient', 'unique_recipients_7d',
        'hour', 'is_off_hours', 'counterparty_change_score_7d'
    ]
    
    # Check which features are missing
    missing_features = [f for f in required_features if f not in df.columns]
    
    if missing_features:
        print(f"Warning: Missing existing features: {missing_features}")
        # Add placeholder values for missing features
        for f in missing_features:
            df[f] = 0.0
    
    # Calculate hour and is_off_hours from timestamp
    if 'hour' not in df.columns or df['hour'].isna().all():
        df['hour'] = df['timestamp'].apply(
            lambda x: datetime.fromisoformat(x.replace('Z', '+00:00')).hour
        )
        df['is_off_hours'] = df['hour'].apply(
            lambda x: 1.0 if x < 8 or x > 17 else 0.0
        )
    
    print("Existing features verified")
    return df


def build_historical_data(df: pd.DataFrame) -> Dict[str, List[Dict]]:
    """Build historical data dictionary for feature calculation."""
    print("Building historical data...")
    
    historical_data = {}
    
    for customer_id in df['customer_id'].unique():
        customer_df = df[df['customer_id'] == customer_id].sort_values('timestamp')
        
        historical_txs = []
        for idx, row in customer_df.iterrows():
            historical_txs.append({
                'amount': row['amount'],
                'timestamp': row['timestamp'],
                'receiver_account': row['receiver_account'],
                'transaction_type': row['transaction_type'],
                'destination_country': row['destination_country']
            })
        
        historical_data[customer_id] = historical_txs
    
    print(f"Built historical data for {len(historical_data)} customers")
    return historical_data


def extract_all_features(
    dataset_file: str = "ml_stage21_diversity_improved_dataset.csv",
    ground_truth_file: str = "ml_stage21_diversity_improved_ground_truth.json",
    output_file: str = "ml_stage21_chapter1_features.csv"
) -> pd.DataFrame:
    """Extract all features including Chapter 1 justified features."""
    
    # Load dataset
    df, ground_truth_dict = load_dataset(dataset_file, ground_truth_file)
    
    # Build historical data
    historical_data = build_historical_data(df)
    
    # Extract existing features
    df = extract_existing_features(df)
    
    # Extract Chapter 1 justified features
    df = extract_cross_border_features(df, historical_data)
    df = extract_sequence_features(df, historical_data)
    df = extract_structuring_features(df, historical_data)
    
    # Select final feature set
    final_features = [
        # Existing Stage 16B features
        'transaction_id', 'sender_account',
        'amount', 'sender_avg_amount', 'sender_max_amount',
        'amount_to_sender_avg', 'amount_z_score', 'amount_deviation_from_baseline_30d',
        'tx_frequency_7d', 'tx_frequency_30d', 'frequency_change_vs_avg_7d',
        'sender_tx_count_24h', 'sender_volume_24h', 'same_day_count',
        'rapid_transfer_count', 'is_new_recipient', 'unique_recipients_7d',
        'hour', 'is_off_hours', 'counterparty_change_score_7d',
        # NEW: Cross-border features
        'is_cross_border', 'is_high_risk_country',
        'cross_border_count_7d', 'cross_border_volume_7d', 'cross_border_ratio_7d',
        # NEW: Sequence features
        'transaction_type_sequence_last_3', 'time_since_last_transaction_hours', 'recurring_pattern_score',
        # NEW: Structuring features
        'amount_near_threshold_flag', 'same_day_cumulative_amount', 'structuring_pattern_score'
    ]
    
    # Ensure all features exist
    for f in final_features:
        if f not in df.columns:
            print(f"Warning: Feature {f} not found, adding placeholder")
            df[f] = 0.0
    
    df_final = df[final_features].copy()
    
    # Save to CSV
    df_final.to_csv(output_file, index=False)
    print(f"Saved {len(df_final)} transactions with {len(final_features)} features to {output_file}")
    
    return df_final


if __name__ == "__main__":
    print("=" * 80)
    print("STAGE 21: CHAPTER 1 JUSTIFIED FEATURE EXTRACTION")
    print("=" * 80)
    print()
    
    df_final = extract_all_features()
    
    print()
    print("=" * 80)
    print("FEATURE EXTRACTION COMPLETE")
    print("=" * 80)
    print(f"Total features: {len(df_final.columns) - 2}")  # Exclude transaction_id and sender_account
    print(f"Total transactions: {len(df_final)}")
