"""
ai_stage14_model.py — Stage 14 Model Service for Live EcoCash Application

This module implements the Stage 14 Gradient Boosting model service integrated
with the validated Stage 13 feature service.

Based on authoritative Stage 14 model:
- ml/stage14/stage14_frozen_model.pkl
- Gradient Boosting
- 30 features
- Binary classification
- Threshold: 0.35

CRITICAL:
- NO model training
- NO model modification
- NO threshold tuning
- EXACT 30-feature input
- EXACT 0.35 threshold
- STRICT use of Stage 13 feature service
"""

import os
import logging
import joblib
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Stage 14 model configuration
STAGE14_MODEL_PATH = os.path.join(os.path.dirname(__file__), "ml", "stage14", "stage14_frozen_model.pkl")
STAGE14_THRESHOLD = 0.35
EXPECTED_FEATURE_COUNT = 30


@dataclass
class ModelPrediction:
    """Structured model prediction result."""
    probability: float
    prediction: int  # 0 = normal, 1 = suspicious pattern
    is_suspicious: bool
    threshold: float
    model_version: str = "stage14_frozen"


class Stage14ModelService:
    """
    Stage 14 Gradient Boosting model service.
    
    Loads the frozen Stage 14 model and provides prediction interface
    integrated with Stage 13 feature service.
    """
    
    def __init__(self, feature_service):
        """
        Initialize Stage 14 model service.
        
        Args:
            feature_service: Stage13FeatureService instance
        """
        self.feature_service = feature_service
        self.model = None
        self.model_metadata = None
        self.model_loaded = False
        self._load_model()
    
    def _load_model(self):
        """Load the frozen Stage 14 model."""
        try:
            if not os.path.exists(STAGE14_MODEL_PATH):
                raise FileNotFoundError(f"Stage 14 model not found at {STAGE14_MODEL_PATH}")
            
            logger.info(f"Loading Stage 14 model from {STAGE14_MODEL_PATH}")
            loaded_data = joblib.load(STAGE14_MODEL_PATH)
            
            # Handle dictionary structure with model, threshold, feature_names, etc.
            if isinstance(loaded_data, dict):
                self.model = loaded_data['model']
                self.model_metadata = loaded_data
                logger.info(f"Stage 14 model loaded as dictionary with keys: {loaded_data.keys()}")
            else:
                self.model = loaded_data
                self.model_metadata = None
                logger.info(f"Stage 14 model loaded directly")
            
            self.model_loaded = True
            
            # Validate model type
            model_type = type(self.model).__name__
            logger.info(f"Stage 14 model type: {model_type}")
            
            # Log model configuration
            if hasattr(self.model, 'get_params'):
                params = self.model.get_params()
                logger.info(f"Model parameters: n_estimators={params.get('n_estimators')}, "
                          f"learning_rate={params.get('learning_rate')}, "
                          f"max_depth={params.get('max_depth')}")
            
            # Log metadata if available
            if self.model_metadata:
                logger.info(f"Model metadata: threshold={self.model_metadata.get('threshold')}, "
                          f"model_type={self.model_metadata.get('model_type')}")
            
        except Exception as e:
            logger.error(f"Failed to load Stage 14 model: {e}")
            self.model_loaded = False
            raise
    
    def _validate_features(self, features: List[float]) -> bool:
        """
        Validate feature vector before model prediction.
        
        Args:
            features: Feature vector
            
        Returns:
            True if valid, False otherwise
        """
        # Check feature count
        if len(features) != EXPECTED_FEATURE_COUNT:
            logger.error(f"Feature count mismatch: expected {EXPECTED_FEATURE_COUNT}, got {len(features)}")
            return False
        
        # Check for NaN
        if any(np.isnan(f) for f in features):
            logger.error("Features contain NaN values")
            return False
        
        # Check for infinity
        if any(np.isinf(f) for f in features):
            logger.error("Features contain infinity values")
            return False
        
        # Check for non-numeric
        if not all(isinstance(f, (int, float)) for f in features):
            logger.error("Features contain non-numeric values")
            return False
        
        return True
    
    def predict(self, current_tx: Dict) -> ModelPrediction:
        """
        Generate Stage 14 model prediction for current transaction.
        
        Args:
            current_tx: Current transaction dict
            
        Returns:
            ModelPrediction object with probability and binary decision
        """
        if not self.model_loaded:
            raise RuntimeError("Stage 14 model not loaded")
        
        try:
            # Generate Stage 13 features
            features = self.feature_service.generate_features(current_tx)
            
            # Validate features
            if not self._validate_features(features):
                raise ValueError("Feature validation failed")
            
            # Convert to numpy array
            feature_array = np.array(features).reshape(1, -1)
            
            # Get probability
            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(feature_array)
                probability = probabilities[0][1]  # Probability of class 1 (suspicious)
            else:
                # Fallback to predict if predict_proba not available
                prediction = self.model.predict(feature_array)[0]
                probability = float(prediction)
            
            # Apply threshold
            is_suspicious = probability >= STAGE14_THRESHOLD
            prediction = 1 if is_suspicious else 0
            
            logger.info(f"Stage 14 prediction: probability={probability:.4f}, "
                       f"threshold={STAGE14_THRESHOLD}, prediction={prediction}")
            
            return ModelPrediction(
                probability=float(probability),
                prediction=int(prediction),
                is_suspicious=is_suspicious,
                threshold=STAGE14_THRESHOLD
            )
            
        except Exception as e:
            logger.error(f"Error generating Stage 14 prediction: {e}")
            raise
    
    def predict_proba_only(self, current_tx: Dict) -> float:
        """
        Generate probability only (for advanced use cases).
        
        Args:
            current_tx: Current transaction dict
            
        Returns:
            Suspicious probability
        """
        prediction = self.predict(current_tx)
        return prediction.probability


# Singleton instance for application-wide use
_model_service_instance = None


def get_stage14_model_service(feature_service=None) -> Stage14ModelService:
    """
    Get or create the singleton Stage 14 model service instance.
    
    Args:
        feature_service: Stage13FeatureService instance (required on first call)
        
    Returns:
        Stage14ModelService instance
    """
    global _model_service_instance
    
    if _model_service_instance is None:
        if feature_service is None:
            raise RuntimeError("Feature service required on first call")
        _model_service_instance = Stage14ModelService(feature_service)
    
    return _model_service_instance


def reset_model_service():
    """Reset the singleton model service instance (for testing)."""
    global _model_service_instance
    _model_service_instance = None
