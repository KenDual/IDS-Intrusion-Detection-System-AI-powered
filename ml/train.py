"""
Model Training Pipeline for IDS Project
Trains XGBoost classifier with hyperparameter tuning and GPU support
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)
import joblib
import json
from pathlib import Path
import logging
from datetime import datetime
import time
import warnings

warnings.filterwarnings('ignore')

# Import config and utils
from app.config import (
    MODELS_DIR, REPORTS_DIR, CLEANED_DATA_PATH,
    ATTACK_CLASSES, ATTACK_LABELS, CLASS_WEIGHTS,
    XGBOOST_PARAMS, HYPERPARAM_GRID, TRAIN_CONFIG,
    USE_GPU, MODEL_PATH
)
from ml.utils import (
    load_preprocessors, plot_confusion_matrix,
    plot_training_history, calculate_metrics,
    save_model_metadata, print_metrics_summary,
    check_gpu_availability, format_time
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelTrainer:
    """Handles model training, tuning, and evaluation"""

    def __init__(self):
        self.model = None
        self.best_params = None
        self.training_history = {
            'train_loss': [],
            'val_loss': [],
            'train_acc': [],
            'val_acc': []
        }
        self.start_time = None
        self.preprocessors = None
        self.selected_features = None

    def load_data(self):
        """Load preprocessed data and selected features"""
        logger.info("Loading preprocessed data and configurations...")

        # Load preprocessors
        self.preprocessors = load_preprocessors(MODELS_DIR)

        # Load selected features
        selected_features_path = MODELS_DIR / "selected_features.json"
        if selected_features_path.exists():
            with open(selected_features_path, 'r') as f:
                features_config = json.load(f)
                self.selected_features = features_config['selected_features']
                logger.info(f"Loaded {len(self.selected_features)} selected features")
        else:
            # Fall back to all features if selection not done
            self.selected_features = self.preprocessors['feature_names']
            logger.warning("Selected features not found, using all features")

        # Load full dataset
        logger.info(f"Loading full dataset from {CLEANED_DATA_PATH}")
        df = pd.read_csv(CLEANED_DATA_PATH)
        logger.info(f"Loaded {len(df):,} samples")

        # Encode labels
        df['label_encoded'] = df[' Label'].map(ATTACK_LABELS)

        # Get features and labels
        X = df[self.selected_features].values
        y = df['label_encoded'].values

        # Log class distribution
        unique, counts = np.unique(y, return_counts=True)
        logger.info("Class distribution:")
        for label, count in zip(unique, counts):
            attack_type = ATTACK_CLASSES[label]
            percentage = (count / len(y)) * 100
            logger.info(f"  {attack_type} (Class {label}): {count:,} ({percentage:.2f}%)")

        return X, y

    def split_data(self, X, y):
        """Split data into train/val/test sets using saved preprocessor info"""
        logger.info("Splitting data into train/val/test sets...")

        from sklearn.model_selection import train_test_split

        # First split: train+val vs test (80/20)
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y,
            test_size=TRAIN_CONFIG['test_size'],
            random_state=TRAIN_CONFIG['random_state'],
            stratify=y
        )

        # Second split: train vs val (90/10 of train+val)
        val_size = TRAIN_CONFIG['validation_size'] / (1 - TRAIN_CONFIG['test_size'])
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp,
            test_size=val_size,
            random_state=TRAIN_CONFIG['random_state'],
            stratify=y_temp
        )

        logger.info(f"  Training set: {len(X_train):,} samples")
        logger.info(f"  Validation set: {len(X_val):,} samples")
        logger.info(f"  Test set: {len(X_test):,} samples")

        return X_train, X_val, X_test, y_train, y_val, y_test

    def scale_features(self, X_train, X_val, X_test):
        """Scale features using saved scaler"""
        logger.info("Scaling features...")

        scaler = self.preprocessors['scaler']

        # Fit on train, transform all
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        X_test_scaled = scaler.transform(X_test)

        return X_train_scaled, X_val_scaled, X_test_scaled

    def create_sample_weights(self, y):
        """Create sample weights based on class distribution"""
        sample_weights = np.array([CLASS_WEIGHTS[label] for label in y])
        return sample_weights

    def train_baseline_model(self, X_train, y_train, X_val, y_val):
        """Train baseline XGBoost model"""
        logger.info("Training baseline XGBoost model...")
        logger.info(f"Using GPU: {USE_GPU}")

        # Get sample weights
        sample_weights_train = self.create_sample_weights(y_train)

        # Create DMatrix for XGBoost
        dtrain = xgb.DMatrix(X_train, label=y_train, weight=sample_weights_train)
        dval = xgb.DMatrix(X_val, label=y_val)

        # Prepare parameters
        params = XGBOOST_PARAMS.copy()

        # Training parameters
        num_boost_round = params.pop('n_estimators', 200)

        # Watchlist for early stopping
        watchlist = [(dtrain, 'train'), (dval, 'val')]

        # Train model
        start = time.time()

        evals_result = {}
        self.model = xgb.train(
            params,
            dtrain,
            num_boost_round=num_boost_round,
            evals=watchlist,
            early_stopping_rounds=TRAIN_CONFIG['early_stopping_rounds'],
            evals_result=evals_result,
            verbose_eval=True
        )

        training_time = time.time() - start
        logger.info(f"Baseline training completed in {format_time(training_time)}")

        # Store training history
        if 'val' in evals_result and params['eval_metric'] in evals_result['val']:
            self.training_history['val_loss'] = evals_result['val'][params['eval_metric']]
            self.training_history['train_loss'] = evals_result['train'][params['eval_metric']]

        # Evaluate baseline
        y_pred_val = self.model.predict(dval)
        if len(y_pred_val.shape) > 1:
            y_pred_val = np.argmax(y_pred_val, axis=1)

        val_accuracy = accuracy_score(y_val, y_pred_val)
        val_f1 = f1_score(y_val, y_pred_val, average='weighted')

        logger.info(f"Baseline Validation Accuracy: {val_accuracy:.4f}")
        logger.info(f"Baseline Validation F1-Score: {val_f1:.4f}")

        return val_accuracy, val_f1

    def hyperparameter_tuning(self, X_train, y_train, X_val, y_val):
        """Perform hyperparameter tuning with GridSearchCV"""
        logger.info("Starting hyperparameter tuning...")

        # Create a smaller grid for faster tuning
        tuning_grid = {
            'n_estimators': [100, 200],
            'max_depth': [5, 7, 10],
            'learning_rate': [0.01, 0.1],
            'subsample': [0.8, 0.9],
            'colsample_bytree': [0.8, 0.9]
        }

        # Base parameters
        base_params = {
            'objective': 'multi:softprob',
            'num_class': 4,
            'tree_method': 'gpu_hist' if USE_GPU == "gpu" else 'hist',
            'predictor': 'gpu_predictor' if USE_GPU == "gpu" else 'cpu_predictor',
            'eval_metric': 'mlogloss',
            'random_state': 42
        }

        if USE_GPU == "gpu":
            base_params['gpu_id'] = 0

        # Create XGBoost classifier
        xgb_classifier = xgb.XGBClassifier(**base_params)

        # Sample weights
        sample_weights = self.create_sample_weights(y_train)

        # Create StratifiedKFold for cross-validation
        cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)

        # Grid search
        logger.info(
            f"Testing {len(tuning_grid['n_estimators']) * len(tuning_grid['max_depth']) * len(tuning_grid['learning_rate']) * len(tuning_grid['subsample']) * len(tuning_grid['colsample_bytree'])} parameter combinations...")

        grid_search = GridSearchCV(
            xgb_classifier,
            tuning_grid,
            cv=cv,
            scoring='f1_weighted',
            n_jobs=1,  # XGBoost handles parallelism
            verbose=1
        )

        # Fit grid search
        start = time.time()
        grid_search.fit(X_train, y_train, sample_weight=sample_weights)
        tuning_time = time.time() - start

        # Get best parameters
        self.best_params = grid_search.best_params_
        best_score = grid_search.best_score_

        logger.info(f"Hyperparameter tuning completed in {format_time(tuning_time)}")
        logger.info(f"Best CV Score: {best_score:.4f}")
        logger.info(f"Best Parameters: {self.best_params}")

        return self.best_params

    def train_final_model(self, X_train, y_train, X_val, y_val, best_params=None):
        """Train final model with best parameters"""
        logger.info("Training final model with best parameters...")

        if best_params is None:
            best_params = self.best_params if self.best_params else {}

        # Merge best params with base params
        final_params = XGBOOST_PARAMS.copy()
        final_params.update(best_params)

        # Get sample weights
        sample_weights_train = self.create_sample_weights(y_train)

        # Create DMatrix
        dtrain = xgb.DMatrix(X_train, label=y_train, weight=sample_weights_train)
        dval = xgb.DMatrix(X_val, label=y_val)

        # Extract n_estimators
        num_boost_round = final_params.pop('n_estimators', 200)

        # Watchlist
        watchlist = [(dtrain, 'train'), (dval, 'val')]

        # Train final model
        start = time.time()

        evals_result = {}
        self.model = xgb.train(
            final_params,
            dtrain,
            num_boost_round=num_boost_round,
            evals=watchlist,
            early_stopping_rounds=TRAIN_CONFIG['early_stopping_rounds'],
            evals_result=evals_result,
            verbose_eval=10
        )

        training_time = time.time() - start
        logger.info(f"Final model training completed in {format_time(training_time)}")

        # Store final parameters
        self.best_params = final_params
        self.best_params['n_estimators'] = self.model.best_iteration

        return self.model

    def evaluate_model(self, X_test, y_test, set_name="Test"):
        """Evaluate model performance"""
        logger.info(f"Evaluating model on {set_name} set...")

        # Create DMatrix
        dtest = xgb.DMatrix(X_test)

        # Predict
        y_pred = self.model.predict(dtest)
        if len(y_pred.shape) > 1:
            y_pred = np.argmax(y_pred, axis=1)

        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')

        # Per-class metrics
        report = classification_report(y_test, y_pred,
                                       target_names=ATTACK_CLASSES,
                                       output_dict=True)

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)

        # Log results
        logger.info(f"{set_name} Set Results:")
        logger.info(f"  Accuracy: {accuracy:.4f}")
        logger.info(f"  Precision: {precision:.4f}")
        logger.info(f"  Recall: {recall:.4f}")
        logger.info(f"  F1-Score: {f1:.4f}")

        # Log per-class results
        logger.info(f"\nPer-class {set_name} Results:")
        for i, class_name in enumerate(ATTACK_CLASSES):
            if str(class_name) in report:
                class_report = report[str(class_name)]
            elif class_name in report:
                class_report = report[class_name]
            else:
                continue
            logger.info(f"  {class_name}:")
            logger.info(f"    Precision: {class_report['precision']:.4f}")
            logger.info(f"    Recall: {class_report['recall']:.4f}")
            logger.info(f"    F1-Score: {class_report['f1-score']:.4f}")

        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'classification_report': report,
            'confusion_matrix': cm.tolist()
        }

        return metrics, y_pred

    def save_model(self, metrics):
        """Save trained model and metadata"""
        logger.info("Saving model and metadata...")

        # Save XGBoost model
        self.model.save_model(str(MODEL_PATH))
        logger.info(f"  Model saved to {MODEL_PATH}")

        # Also save as pickle for compatibility
        pkl_path = MODEL_PATH.with_suffix('.pkl')
        joblib.dump(self.model, pkl_path)
        logger.info(f"  Model (pkl) saved to {pkl_path}")

        # Save metadata
        metadata = {
            'model_type': 'XGBoost',
            'best_parameters': self.best_params,
            'selected_features': self.selected_features,
            'n_features': len(self.selected_features),
            'classes': ATTACK_CLASSES,
            'class_weights': CLASS_WEIGHTS,
            'gpu_used': USE_GPU,
            'metrics': metrics,
            'training_timestamp': datetime.now().isoformat(),
            'training_time': format_time(time.time() - self.start_time)
        }

        metadata_path = MODELS_DIR / "model_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=4)
        logger.info(f"  Metadata saved to {metadata_path}")

        # Save best parameters separately
        params_path = MODELS_DIR / "best_params.json"
        with open(params_path, 'w') as f:
            json.dump(self.best_params, f, indent=4)
        logger.info(f"  Best parameters saved to {params_path}")

    def generate_report(self, val_metrics, test_metrics):
        """Generate comprehensive training report"""
        logger.info("Generating training report...")

        report_path = REPORTS_DIR / "training_report.txt"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("MODEL TRAINING REPORT\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Training Time: {format_time(time.time() - self.start_time)}\n")
            f.write("=" * 60 + "\n\n")

            f.write("MODEL CONFIGURATION:\n")
            f.write("-" * 40 + "\n")
            f.write(f"Model Type: XGBoost\n")
            f.write(f"GPU Used: {USE_GPU}\n")
            f.write(f"Number of Features: {len(self.selected_features)}\n")
            f.write(f"Number of Classes: {len(ATTACK_CLASSES)}\n")
            f.write(f"Classes: {', '.join(ATTACK_CLASSES)}\n\n")

            f.write("BEST HYPERPARAMETERS:\n")
            f.write("-" * 40 + "\n")
            for param, value in self.best_params.items():
                f.write(f"{param}: {value}\n")

            f.write("\n" + "=" * 60 + "\n")
            f.write("VALIDATION SET PERFORMANCE:\n")
            f.write("=" * 60 + "\n")
            f.write(f"Accuracy: {val_metrics['accuracy']:.4f}\n")
            f.write(f"Precision: {val_metrics['precision']:.4f}\n")
            f.write(f"Recall: {val_metrics['recall']:.4f}\n")
            f.write(f"F1-Score: {val_metrics['f1_score']:.4f}\n\n")

            f.write("Per-Class Validation Results:\n")
            f.write("-" * 40 + "\n")
            for class_name in ATTACK_CLASSES:
                if class_name in val_metrics['classification_report']:
                    report = val_metrics['classification_report'][class_name]
                    f.write(f"\n{class_name}:\n")
                    f.write(f"  Precision: {report['precision']:.4f}\n")
                    f.write(f"  Recall: {report['recall']:.4f}\n")
                    f.write(f"  F1-Score: {report['f1-score']:.4f}\n")
                    f.write(f"  Support: {report['support']}\n")

            f.write("\n" + "=" * 60 + "\n")
            f.write("TEST SET PERFORMANCE:\n")
            f.write("=" * 60 + "\n")
            f.write(f"Accuracy: {test_metrics['accuracy']:.4f}\n")
            f.write(f"Precision: {test_metrics['precision']:.4f}\n")
            f.write(f"Recall: {test_metrics['recall']:.4f}\n")
            f.write(f"F1-Score: {test_metrics['f1_score']:.4f}\n\n")

            f.write("Per-Class Test Results:\n")
            f.write("-" * 40 + "\n")
            for class_name in ATTACK_CLASSES:
                if class_name in test_metrics['classification_report']:
                    report = test_metrics['classification_report'][class_name]
                    f.write(f"\n{class_name}:\n")
                    f.write(f"  Precision: {report['precision']:.4f}\n")
                    f.write(f"  Recall: {report['recall']:.4f}\n")
                    f.write(f"  F1-Score: {report['f1-score']:.4f}\n")
                    f.write(f"  Support: {report['support']}\n")

            f.write("\n" + "=" * 60 + "\n")
            f.write("CONFUSION MATRIX (Test Set):\n")
            f.write("-" * 40 + "\n")
            f.write("Predicted →\n")
            f.write("Actual ↓\n")
            f.write(f"{'':15s}")
            for class_name in ATTACK_CLASSES:
                f.write(f"{class_name[:10]:>12s}")
            f.write("\n")

            cm = np.array(test_metrics['confusion_matrix'])
            for i, class_name in enumerate(ATTACK_CLASSES):
                f.write(f"{class_name[:15]:15s}")
                for j in range(len(ATTACK_CLASSES)):
                    f.write(f"{cm[i, j]:12d}")
                f.write("\n")

        logger.info(f"  Training report saved to {report_path}")

        # Save metrics as JSON
        metrics_path = REPORTS_DIR / "training_metrics.json"
        with open(metrics_path, 'w', encoding='utf-8') as f:
            json.dump({
                'validation': val_metrics,
                'test': test_metrics,
                'timestamp': datetime.now().isoformat()
            }, f, indent=4)
        logger.info(f"  Metrics saved to {metrics_path}")

    def create_visualizations(self, test_metrics, y_test, y_pred):
        """Create and save visualizations"""
        logger.info("Creating visualizations...")

        # Plot confusion matrix
        cm_path = REPORTS_DIR / "confusion_matrix.png"
        plot_confusion_matrix(
            y_test,
            y_pred,
            ATTACK_CLASSES,
            save_path=cm_path,
            title="Test Set Confusion Matrix"
        )

        # Plot training history if available
        if self.training_history.get('train_loss') and len(self.training_history['train_loss']) > 0:
            history_path = REPORTS_DIR / "training_history.png"
            plot_training_history(self.training_history, save_path=history_path)

        logger.info(f"  Visualizations saved to {REPORTS_DIR}")

    def train_pipeline(self, skip_tuning=False):
        """Execute complete training pipeline"""
        self.start_time = time.time()

        logger.info("=" * 60)
        logger.info("STARTING MODEL TRAINING PIPELINE")
        logger.info("=" * 60)

        # Check GPU
        gpu_info = check_gpu_availability()
        if gpu_info['gpu_available']:
            logger.info(f"GPU detected: {gpu_info['gpu_names']}")
        else:
            logger.info("No GPU detected, using CPU")

        # Load data
        X, y = self.load_data()

        # Split data
        X_train, X_val, X_test, y_train, y_val, y_test = self.split_data(X, y)

        # Scale features
        X_train, X_val, X_test = self.scale_features(X_train, X_val, X_test)

        # Train baseline model
        baseline_acc, baseline_f1 = self.train_baseline_model(
            X_train, y_train, X_val, y_val
        )

        # Hyperparameter tuning
        if not skip_tuning:
            best_params = self.hyperparameter_tuning(
                X_train, y_train, X_val, y_val
            )
        else:
            logger.info("Skipping hyperparameter tuning, using default parameters")
            best_params = {}

        # Train final model
        self.train_final_model(X_train, y_train, X_val, y_val, best_params)

        # Evaluate on validation set
        val_metrics, _ = self.evaluate_model(X_val, y_val, "Validation")

        # Evaluate on test set
        test_metrics, y_pred_test = self.evaluate_model(X_test, y_test, "Test")

        # Save model
        self.save_model(test_metrics)

        # Generate report
        self.generate_report(val_metrics, test_metrics)

        # Create visualizations
        self.create_visualizations(test_metrics, y_test, y_pred_test)

        # Print summary
        total_time = time.time() - self.start_time

        print("\n" + "=" * 60)
        print("MODEL TRAINING COMPLETE")
        print("=" * 60)
        print(f"Total Training Time: {format_time(total_time)}")
        print(f"GPU Used: {USE_GPU}")
        print(f"\nTest Set Performance:")
        print(f"  Accuracy: {test_metrics['accuracy']:.4f}")
        print(f"  F1-Score: {test_metrics['f1_score']:.4f}")
        print(f"\nModel saved to: {MODEL_PATH}")
        print(f"Report saved to: {REPORTS_DIR / 'training_report.txt'}")
        print("=" * 60)

        return test_metrics


def main():
    """Main execution function"""

    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description='Train XGBoost model for IDS')
    parser.add_argument('--skip-tuning', action='store_true',
                        help='Skip hyperparameter tuning for faster training')
    parser.add_argument('--gpu', choices=['auto', 'cpu', 'gpu'],
                        default='auto', help='Force GPU/CPU usage')
    args = parser.parse_args()

    # Override GPU setting if specified
    if args.gpu != 'auto':
        import app.config as config
        config.USE_GPU = args.gpu
        logger.info(f"Forced GPU setting: {args.gpu}")

    # Create trainer instance
    trainer = ModelTrainer()

    try:
        # Run training pipeline
        metrics = trainer.train_pipeline(skip_tuning=args.skip_tuning)

        # Check if model meets performance thresholds
        from app.config import PERFORMANCE_THRESHOLDS

        if metrics['accuracy'] < PERFORMANCE_THRESHOLDS['min_accuracy']:
            logger.warning(
                f"Model accuracy {metrics['accuracy']:.4f} is below threshold {PERFORMANCE_THRESHOLDS['min_accuracy']}")

        if metrics['f1_score'] < PERFORMANCE_THRESHOLDS['min_f1_score']:
            logger.warning(
                f"Model F1-score {metrics['f1_score']:.4f} is below threshold {PERFORMANCE_THRESHOLDS['min_f1_score']}")

        return 0

    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())