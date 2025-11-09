"""
Model Loader for IDS Detection Engine
Loads XGBoost model, scaler, and handles predictions.
"""

import pickle
import json
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ModelLoader:
    """
    Singleton class to load and manage ML model for attack detection.

    Loads:
    - XGBoost model
    - StandardScaler
    - Model metadata (features, classes, metrics)

    Does NOT use label_encoder.pkl (corrupted) - uses metadata instead.
    """

    _instance: Optional['ModelLoader'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.model = None
        self.scaler = None
        self.metadata = None
        self.feature_names = None
        self.classes = None
        self.class_to_idx = None
        self.idx_to_class = None
        self.n_features = None

        # Paths
        self.base_path = Path(__file__).parent.parent.parent / "ml" / "models"
        self.model_path = self.base_path / "xgboost_model.pkl"
        self.scaler_path = self.base_path / "scaler.pkl"
        self.metadata_path = self.base_path / "model_metadata.json"

        # Load all components
        self._load_all()
        self._initialized = True

        logger.info("ModelLoader initialized successfully")

    def _load_all(self):
        """Load model, scaler, and metadata"""
        try:
            # 1. Load metadata first (needed for classes)
            self._load_metadata()

            # 2. Load XGBoost model
            self._load_model()

            # 3. Load scaler
            self._load_scaler()

            # 4. Validate everything loaded
            self._validate()

            logger.info(f"Model loaded: {self.n_features} features, {len(self.classes)} classes")

        except Exception as e:
            logger.error(f"Failed to load model components: {e}")
            raise

    def _load_metadata(self):
        """Load model metadata from JSON"""
        if not self.metadata_path.exists():
            raise FileNotFoundError(f"Metadata not found: {self.metadata_path}")

        with open(self.metadata_path, 'r') as f:
            self.metadata = json.load(f)

        # Extract important info
        self.feature_names = self.metadata['selected_features']
        self.n_features = self.metadata['n_features']
        self.classes = self.metadata['classes']

        # Create class mappings (instead of using label_encoder.pkl)
        # classes = ["BENIGN", "DoS Hulk", "PortScan", "DDoS"]
        self.class_to_idx = {cls: idx for idx, cls in enumerate(self.classes)}
        self.idx_to_class = {idx: cls for idx, cls in enumerate(self.classes)}

        logger.info(f"Metadata loaded: {self.n_features} features")
        logger.debug(f"Classes: {self.classes}")
        logger.debug(f"Class mapping: {self.class_to_idx}")

    def _load_model(self):
        """Load XGBoost model"""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")

        with open(self.model_path, 'rb') as f:
            self.model = pickle.load(f)

        logger.info("XGBoost model loaded")

    def _load_scaler(self):
        """Load StandardScaler"""
        if not self.scaler_path.exists():
            raise FileNotFoundError(f"Scaler not found: {self.scaler_path}")

        with open(self.scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)

        logger.info("StandardScaler loaded")

    def _validate(self):
        """Validate all components are loaded"""
        if self.model is None:
            raise ValueError("Model not loaded")
        if self.scaler is None:
            raise ValueError("Scaler not loaded")
        if self.metadata is None:
            raise ValueError("Metadata not loaded")
        if len(self.feature_names) != self.n_features:
            raise ValueError(f"Feature count mismatch: {len(self.feature_names)} != {self.n_features}")

    def predict(self, features: np.ndarray) -> Tuple[str, float]:
        """
        Predict attack type from features.

        Args:
            features: numpy array of shape (25,) with feature values

        Returns:
            Tuple of (attack_type: str, confidence: float)

        Example:
            attack_type, confidence = model_loader.predict(features)
            # ("DDoS", 0.98)
        """
        try:
            import xgboost as xgb

            # 1. Validate input
            if features is None or len(features) == 0:
                raise ValueError("Features cannot be empty")

            # Convert to numpy array if needed
            if not isinstance(features, np.ndarray):
                features = np.array(features)

            # Reshape to (1, 25) if needed
            if features.ndim == 1:
                features = features.reshape(1, -1)

            # Check feature count
            if features.shape[1] != self.n_features:
                raise ValueError(f"Expected {self.n_features} features, got {features.shape[1]}")

            # Check for NaN or Inf
            if np.any(np.isnan(features)) or np.any(np.isinf(features)):
                raise ValueError("Features contain NaN or Inf values")

            # 2. Scale features
            features_scaled = self.scaler.transform(features)

            # 3. Create DMatrix for XGBoost Booster
            dmatrix = xgb.DMatrix(features_scaled)

            # 4. Predict class probabilities (Booster returns probabilities for softprob objective)
            proba = self.model.predict(dmatrix)

            # 5. Get predicted class index and confidence
            predicted_idx = int(np.argmax(proba[0]))
            confidence = float(proba[0][predicted_idx])

            # 6. Convert index to class name
            attack_type = self.idx_to_class[predicted_idx]

            logger.debug(f"Prediction: {attack_type} (confidence: {confidence:.4f})")

            return attack_type, confidence

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise

    def predict_batch(self, features_list: list) -> list:
        """
        Predict multiple feature sets at once (batch prediction).

        Args:
            features_list: List of numpy arrays, each shape (25,)

        Returns:
            List of tuples: [(attack_type, confidence), ...]
        """
        try:
            import xgboost as xgb

            # Stack all features into (N, 25) array
            features_array = np.vstack(features_list)

            # Validate
            if features_array.shape[1] != self.n_features:
                raise ValueError(f"Expected {self.n_features} features, got {features_array.shape[1]}")

            # Scale
            features_scaled = self.scaler.transform(features_array)

            # Create DMatrix
            dmatrix = xgb.DMatrix(features_scaled)

            # Predict
            proba = self.model.predict(dmatrix)

            # Convert to results
            results = []
            for prob in proba:
                predicted_idx = int(np.argmax(prob))
                confidence = float(prob[predicted_idx])
                attack_type = self.idx_to_class[predicted_idx]
                results.append((attack_type, confidence))

            return results

        except Exception as e:
            logger.error(f"Batch prediction failed: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information from metadata.

        Returns:
            Dict with model info: version, accuracy, classes, etc.
        """
        return {
            "model_type": self.metadata.get("model_type", "XGBoost"),
            "n_features": self.n_features,
            "feature_names": self.feature_names,
            "classes": self.classes,
            "accuracy": self.metadata.get("metrics", {}).get("accuracy", 0.0),
            "training_time": self.metadata.get("training_time", "N/A"),
            "training_timestamp": self.metadata.get("training_timestamp", "N/A"),
            "best_parameters": self.metadata.get("best_parameters", {}),
        }

    @classmethod
    def get_instance(cls) -> 'ModelLoader':
        """Get singleton instance of ModelLoader"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# Convenience function for easy import
def get_model_loader() -> ModelLoader:
    """Get ModelLoader singleton instance"""
    return ModelLoader.get_instance()


if __name__ == "__main__":
    # Test the model loader
    logging.basicConfig(level=logging.INFO)

    print("="*60)
    print("Testing ModelLoader")
    print("="*60)

    try:
        # Load model
        loader = ModelLoader.get_instance()

        # Print model info
        info = loader.get_model_info()
        print("\n📊 Model Information:")
        print(f"  Type: {info['model_type']}")
        print(f"  Features: {info['n_features']}")
        print(f"  Classes: {info['classes']}")
        print(f"  Accuracy: {info['accuracy']:.4f}")
        print(f"  Training time: {info['training_time']}")

        # Test prediction with dummy features (25 zeros)
        print("\n🧪 Testing prediction with dummy features...")
        dummy_features = np.zeros(25)
        attack_type, confidence = loader.predict(dummy_features)
        print(f"  Prediction: {attack_type}")
        print(f"  Confidence: {confidence:.4f}")

        # Test batch prediction
        print("\n🧪 Testing batch prediction...")
        batch_features = [np.zeros(25), np.ones(25)]
        results = loader.predict_batch(batch_features)
        for i, (att, conf) in enumerate(results):
            print(f"  Sample {i+1}: {att} (conf: {conf:.4f})")

        print("\n✅ ModelLoader test PASSED!")

    except Exception as e:
        print(f"\n❌ ModelLoader test FAILED: {e}")
        import traceback
        traceback.print_exc()