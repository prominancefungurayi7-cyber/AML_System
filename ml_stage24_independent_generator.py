"""
STAGE 24: Independent Generalization Population Generator

Generate 100 entirely new customers with different random seed.
"""

import random
import numpy as np

# Use different seed for independence
INDEPENDENT_SEED = 999
random.seed(INDEPENDENT_SEED)
np.random.seed(INDEPENDENT_SEED)

# Import the diverse generator
from ml_stage24_diverse_generator import DiverseAMLGenerator, export_dataset

if __name__ == "__main__":
    print("=" * 80)
    print("STAGE 24: INDEPENDENT GENERALIZATION POPULATION GENERATOR")
    print("=" * 80)
    print()
    
    generator = DiverseAMLGenerator(random_seed=INDEPENDENT_SEED)
    transactions, ground_truth = generator.generate_dataset(
        num_customers=100,
        transactions_per_customer=50,
        normal_customers=80,
        suspicious_customers=15,
        super_suspicious_customers=5,
        customer_id_offset=300  # Offset to ensure no overlap with main dataset
    )
    
    export_dataset(
        transactions, ground_truth,
        dataset_file="ml_stage24_independent_dataset.csv",
        ground_truth_file="ml_stage24_independent_ground_truth.json"
    )
    
    print()
    print("=" * 80)
    print("INDEPENDENT POPULATION GENERATION COMPLETE")
    print("=" * 80)
