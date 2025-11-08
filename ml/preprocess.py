import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedShuffleSplit
from sklearn.preprocessing import StandardScaler, LabelEncoder
from imblearn.over_sampling import SMOTE
import joblib
import json
from pathlib import Path
import logging
from datetime import datetime
import psutil
from typing import Tuple, Dict, Any

# Import config
from app.config import (
    CLEANED_DATA_PATH, MODELS_DIR, SELECTED_FEATURES,
    ATTACK_LABELS, TRAIN_CONFIG, USE_GPU, BATCH_SIZE,
    MAX_MEMORY_GB, SCALER_PATH, LABEL_ENCODER_PATH,
    FEATURE_NAMES_PATH, TRAINING_CONFIG_PATH
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Handles all data preprocessing tasks"""

    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_names = None
        self.training_config = {}
        self.start_time = None

    def check_memory_usage(self) -> float:
        """Monitor memory usage"""
        process = psutil.Process()
        memory_gb = process.memory_info().rss / 1024 / 1024 / 1024
        return memory_gb

    def load_data(self, sample_size: float = None) -> pd.DataFrame:
        """
        Load the cleaned dataset

        Args:
            sample_size: Optional fraction of data to load (for testing)

        Returns:
            DataFrame with loaded data
        """
        logger.info(f"Loading data from {CLEANED_DATA_PATH}")
        self.start_time = datetime.now()

        # Check file exists
        if not CLEANED_DATA_PATH.exists():
            raise FileNotFoundError(f"Data file not found: {CLEANED_DATA_PATH}")

        # Load data in chunks if file is large
        try:
            if sample_size:
                # Load sample for testing
                df = pd.read_csv(CLEANED_DATA_PATH, nrows=int(2791127 * sample_size))
                logger.info(f"Loaded sample of {len(df):,} records")
            else:
                # Load full dataset
                df = pd.read_csv(CLEANED_DATA_PATH)
                logger.info(f"Loaded full dataset: {len(df):,} records")

            # Memory usage
            memory_usage = self.check_memory_usage()
            logger.info(f"Current memory usage: {memory_usage:.2f} GB")

            if memory_usage > MAX_MEMORY_GB * 0.8:
                logger.warning(f"High memory usage detected: {memory_usage:.2f} GB")

            return df

        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise

    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and clean the dataset

        Args:
            df: Input DataFrame

        Returns:
            Validated DataFrame
        """
        logger.info("Validating data...")
        initial_shape = df.shape

        # Check for required columns
        if ' Label' not in df.columns:
            raise ValueError("Label column not found in dataset")

        # Check features exist
        missing_features = [f for f in SELECTED_FEATURES if f not in df.columns]
        if missing_features:
            logger.warning(f"Missing features: {missing_features}")

        # Remove any remaining infinity values
        inf_count = np.isinf(df.select_dtypes(include=[np.number])).sum().sum()
        if inf_count > 0:
            logger.warning(f"Found {inf_count} infinity values, replacing...")
            df = df.replace([np.inf, -np.inf], np.nan)

        # Handle missing values
        missing_count = df.isnull().sum().sum()
        if missing_count > 0:
            logger.warning(f"Found {missing_count} missing values, filling...")
            # Fill numeric columns with median
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())

        # Verify attack classes
        unique_labels = df[' Label'].unique()
        expected_labels = list(ATTACK_LABELS.keys())
        unexpected = set(unique_labels) - set(expected_labels)
        if unexpected:
            logger.warning(f"Unexpected labels found: {unexpected}")
            df = df[df[' Label'].isin(expected_labels)]

        logger.info(f"Data validation complete. Shape: {initial_shape} -> {df.shape}")
        return df

    def encode_labels(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Encode attack labels to numeric values

        Args:
            df: DataFrame with Label column

        Returns:
            Tuple of (features_df, encoded_labels)
        """
        logger.info("Encoding labels...")

        # Map labels to numeric values
        df['label_encoded'] = df[' Label'].map(ATTACK_LABELS)

        # Verify encoding
        if df['label_encoded'].isnull().any():
            unmapped = df[df['label_encoded'].isnull()][' Label'].unique()
            raise ValueError(f"Failed to encode labels: {unmapped}")

        # Get class distribution
        class_dist = df['label_encoded'].value_counts().sort_index()
        logger.info("Class distribution:")
        for label, count in class_dist.items():
            attack_type = [k for k, v in ATTACK_LABELS.items() if v == label][0]
            percentage = (count / len(df)) * 100
            logger.info(f"  {attack_type} (Class {label}): {count:,} ({percentage:.2f}%)")

        # Store label encoder info
        self.label_encoder.classes_ = np.array(list(ATTACK_LABELS.keys()))

        # Separate features and labels
        y = df['label_encoded'].values
        X = df[SELECTED_FEATURES].copy()

        # Store feature names
        self.feature_names = list(X.columns)

        return X, y

    def scale_features(self, X_train: np.ndarray, X_test: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Scale features using StandardScaler

        Args:
            X_train: Training features
            X_test: Test features

        Returns:
            Tuple of (scaled_train, scaled_test)
        """
        logger.info("Scaling features...")

        # Fit scaler on training data
        X_train_scaled = self.scaler.fit_transform(X_train)

        # Transform test data
        X_test_scaled = self.scaler.transform(X_test)

        # Log scaling statistics
        logger.info(f"Feature scaling complete:")
        logger.info(f"  Mean values range: [{self.scaler.mean_.min():.3f}, {self.scaler.mean_.max():.3f}]")
        logger.info(f"  Std values range: [{self.scaler.scale_.min():.3f}, {self.scaler.scale_.max():.3f}]")

        return X_train_scaled, X_test_scaled

    def split_data(self, X: pd.DataFrame, y: np.ndarray) -> Tuple[np.ndarray, ...]:
        """
        Split data into train/validation/test sets

        Args:
            X: Features DataFrame
            y: Labels array

        Returns:
            Tuple of (X_train, X_val, X_test, y_train, y_val, y_test)
        """
        logger.info("Splitting data...")

        # First split: train+val vs test (80/20)
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y,
            test_size=TRAIN_CONFIG['test_size'],
            random_state=TRAIN_CONFIG['random_state'],
            stratify=y if TRAIN_CONFIG['stratify'] else None
        )

        # Second split: train vs val (90/10 of train+val)
        val_size = TRAIN_CONFIG['validation_size'] / (1 - TRAIN_CONFIG['test_size'])
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp,
            test_size=val_size,
            random_state=TRAIN_CONFIG['random_state'],
            stratify=y_temp if TRAIN_CONFIG['stratify'] else None
        )

        logger.info(f"Data split complete:")
        logger.info(f"  Training set: {len(X_train):,} samples")
        logger.info(f"  Validation set: {len(X_val):,} samples")
        logger.info(f"  Test set: {len(X_test):,} samples")

        return X_train, X_val, X_test, y_train, y_val, y_test

    def handle_class_imbalance(self, X_train: np.ndarray, y_train: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Handle class imbalance using SMOTE

        Args:
            X_train: Training features
            y_train: Training labels

        Returns:
            Tuple of (balanced_features, balanced_labels)
        """
        if not TRAIN_CONFIG.get('use_smote', False):
            logger.info("SMOTE disabled in config, skipping...")
            return X_train, y_train

        logger.info("Applying SMOTE for class balancing...")

        # Get initial class distribution
        unique, counts = np.unique(y_train, return_counts=True)
        logger.info(f"Before SMOTE: {dict(zip(unique, counts))}")

        # Apply SMOTE with adjusted parameters for large dataset
        smote = SMOTE(
            sampling_strategy=TRAIN_CONFIG.get('smote_sampling_strategy', 'auto'),
            random_state=TRAIN_CONFIG['random_state'],
            k_neighbors=3  # Reduce neighbors for faster computation
            # Removed n_jobs as it's deprecated
        )

        try:
            # For very large datasets, we might need to limit SMOTE
            # Check if dataset is too large
            if len(X_train) > 1000000:
                logger.warning(
                    f"Large dataset detected ({len(X_train):,} samples), using alternative balancing strategy...")

                # Option 1: Use class weights instead of SMOTE
                logger.info("SMOTE disabled for large dataset. Will use class_weight in XGBoost instead.")
                return X_train, y_train

                # Option 2: Sample down before SMOTE (uncomment if preferred)
                # max_samples_per_class = 200000
                # X_sampled, y_sampled = self._sample_for_smote(X_train, y_train, max_samples_per_class)
                # X_resampled, y_resampled = smote.fit_resample(X_sampled, y_sampled)
            else:
                X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

            # Get new class distribution
            unique, counts = np.unique(y_resampled, return_counts=True)
            logger.info(f"After SMOTE: {dict(zip(unique, counts))}")
            logger.info(f"Total samples increased from {len(X_train):,} to {len(X_resampled):,}")

            return X_resampled, y_resampled

        except Exception as e:
            logger.error(f"SMOTE failed: {e}")
            logger.info("Continuing without SMOTE...")
            return X_train, y_train

    def save_preprocessors(self) -> None:
        """Save all preprocessing objects"""
        logger.info("Saving preprocessing objects...")

        # Save scaler
        joblib.dump(self.scaler, SCALER_PATH)
        logger.info(f"  Scaler saved to {SCALER_PATH}")

        # Save label encoder
        joblib.dump(self.label_encoder, LABEL_ENCODER_PATH)
        logger.info(f"  Label encoder saved to {LABEL_ENCODER_PATH}")

        # Save feature names
        joblib.dump(self.feature_names, FEATURE_NAMES_PATH)
        logger.info(f"  Feature names saved to {FEATURE_NAMES_PATH}")

        # Save training config with timestamp
        self.training_config.update({
            'preprocessing_timestamp': datetime.now().isoformat(),
            'processing_time': str(datetime.now() - self.start_time),
            'gpu_used': USE_GPU,
            'feature_count': len(self.feature_names)
        })

        with open(TRAINING_CONFIG_PATH, 'w') as f:
            json.dump(self.training_config, f, indent=4)
        logger.info(f"  Training config saved to {TRAINING_CONFIG_PATH}")

    def preprocess_pipeline(self, sample_size: float = None) -> Dict[str, Any]:
        """
        Execute complete preprocessing pipeline

        Args:
            sample_size: Optional fraction of data to use (for testing)

        Returns:
            Dictionary with all processed data and metadata
        """
        logger.info("=" * 60)
        logger.info("Starting preprocessing pipeline...")
        logger.info(f"GPU mode: {USE_GPU}")
        logger.info("=" * 60)

        # Step 1: Load data
        df = self.load_data(sample_size)

        # Step 2: Validate data
        df = self.validate_data(df)

        # Step 3: Encode labels
        X, y = self.encode_labels(df)

        # Step 4: Split data
        X_train, X_val, X_test, y_train, y_val, y_test = self.split_data(X, y)

        # Step 5: Scale features
        X_train_scaled, X_val_scaled = self.scale_features(X_train, X_val)
        X_test_scaled = self.scaler.transform(X_test)

        # Step 6: Handle class imbalance
        X_train_balanced, y_train_balanced = self.handle_class_imbalance(X_train_scaled, y_train)

        # Store configuration
        self.training_config = {
            'total_samples': len(df),
            'train_samples': len(X_train_balanced),
            'val_samples': len(X_val),
            'test_samples': len(X_test),
            'features': self.feature_names,
            'classes': list(ATTACK_LABELS.keys()),
            'class_mapping': ATTACK_LABELS
        }

        # Step 7: Save preprocessors
        self.save_preprocessors()

        # Prepare results
        results = {
            'X_train': X_train_balanced,
            'X_val': X_val_scaled,
            'X_test': X_test_scaled,
            'y_train': y_train_balanced,
            'y_val': y_val,
            'y_test': y_test,
            'feature_names': self.feature_names,
            'config': self.training_config
        }

        # Final memory check
        memory_usage = self.check_memory_usage()
        processing_time = datetime.now() - self.start_time

        logger.info("=" * 60)
        logger.info("Preprocessing complete!")
        logger.info(f"Total processing time: {processing_time}")
        logger.info(f"Final memory usage: {memory_usage:.2f} GB")
        logger.info(f"Ready for training with {len(X_train_balanced):,} samples")
        logger.info("=" * 60)

        return results


def main():
    """Main execution function"""
    preprocessor = DataPreprocessor()

    # Run with sample for testing (use None for full dataset)
    # sample_size = 0.01  # Use 1% for testing
    sample_size = None  # Use full dataset

    results = preprocessor.preprocess_pipeline(sample_size)

    # Display summary
    print("\n" + "=" * 60)
    print("PREPROCESSING SUMMARY")
    print("=" * 60)
    print(f"Training samples: {len(results['y_train']):,}")
    print(f"Validation samples: {len(results['y_val']):,}")
    print(f"Test samples: {len(results['y_test']):,}")
    print(f"Number of features: {len(results['feature_names'])}")
    print(f"Classes: {results['config']['classes']}")
    print("=" * 60)

    return results


if __name__ == "__main__":
    main()