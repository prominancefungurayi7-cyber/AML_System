"""
Temporary script to inspect the existing AML AI model for audit purposes.
This script will NOT modify anything - only read and analyze.
"""

import joblib
import json
import os
from datetime import datetime

MODEL_PATH = "aml_ai_model.pkl"
METADATA_PATH = "aml_ai_model_meta.json"

print("=" * 80)
print("AML AI MODEL AUDIT - MODEL INSPECTION")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# Check if model exists
if not os.path.exists(MODEL_PATH):
    print(f"ERROR: Model file not found at {MODEL_PATH}")
    exit(1)

print(f"Model file: {MODEL_PATH}")
print(f"Model file size: {os.path.getsize(MODEL_PATH):,} bytes")
print()

# Load the model bundle
print("Loading model bundle...")
try:
    bundle = joblib.load(MODEL_PATH)
    print("Model loaded successfully")
    print()
except Exception as e:
    print(f"ERROR loading model: {e}")
    exit(1)

# Inspect bundle structure
print("BUNDLE STRUCTURE:")
print("-" * 80)
print(f"Bundle type: {type(bundle)}")
print(f"Bundle keys: {bundle.keys() if hasattr(bundle, 'keys') else 'N/A (not a dict-like object)'}")
print()

# Inspect classifier
if "classifier" in bundle:
    classifier = bundle["classifier"]
    print("CLASSIFIER:")
    print("-" * 80)
    print(f"Type: {type(classifier)}")
    print(f"Class name: {classifier.__class__.__name__}")
    
    # Check if it's a Pipeline
    if hasattr(classifier, 'named_steps'):
        print("Pipeline steps:")
        for name, step in classifier.named_steps.items():
            print(f"  - {name}: {step.__class__.__name__}")
            if hasattr(step, 'get_params'):
                params = step.get_params()
                # Print key parameters
                if name == "classifier":
                    print(f"    Key params:")
                    for param in ['n_estimators', 'max_depth', 'min_samples_leaf', 'min_samples_split', 
                                 'max_features', 'class_weight', 'random_state']:
                        if param in params:
                            print(f"      {param}: {params[param]}")
    else:
        # Direct classifier
        if hasattr(classifier, 'get_params'):
            params = classifier.get_params()
            print("Parameters:")
            for param in ['n_estimators', 'max_depth', 'min_samples_leaf', 'min_samples_split', 
                         'max_features', 'class_weight', 'random_state']:
                if param in params:
                    print(f"  {param}: {params[param]}")
    
    # Get classes
    if hasattr(classifier, 'classes_'):
        print(f"Classes: {list(classifier.classes_)}")
    if hasattr(classifier, 'n_classes_'):
        print(f"Number of classes: {classifier.n_classes_}")
    if hasattr(classifier, 'n_features_in_'):
        print(f"Number of features: {classifier.n_features_in_}")
    
    print()

# Inspect anomaly detector
if "anomaly_detector" in bundle:
    anomaly = bundle["anomaly_detector"]
    print("ANOMALY DETECTOR:")
    print("-" * 80)
    print(f"Type: {type(anomaly)}")
    print(f"Class name: {anomaly.__class__.__name__}")
    
    if hasattr(anomaly, 'get_params'):
        params = anomaly.get_params()
        print("Parameters:")
        for param in ['n_estimators', 'contamination', 'max_samples', 'random_state']:
            if param in params:
                print(f"  {param}: {params[param]}")
    
    if hasattr(anomaly, 'n_features_in_'):
        print(f"Number of features: {anomaly.n_features_in_}")
    
    print()

# Other bundle info
print("BUNDLE METADATA:")
print("-" * 80)
if "version" in bundle:
    print(f"Version: {bundle['version']}")
if "feature_count" in bundle:
    print(f"Feature count: {bundle['feature_count']}")
if "classes" in bundle:
    print(f"Classes: {bundle['classes']}")
print()

# Load and inspect metadata file
if os.path.exists(METADATA_PATH):
    print("METADATA FILE:")
    print("-" * 80)
    with open(METADATA_PATH, 'r') as f:
        metadata = json.load(f)
    for key, value in metadata.items():
        print(f"{key}: {value}")
    print()

print("=" * 80)
print("AUDIT INSPECTION COMPLETE")
print("=" * 80)
