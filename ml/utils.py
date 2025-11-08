"""
Utility functions for ML pipeline
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report
import joblib
import json
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def load_preprocessors(models_dir: Path):
    """
    Load saved preprocessing objects

    Args:
        models_dir: Path to models directory

    Returns:
        Dictionary with loaded objects
    """
    preprocessors = {}

    try:
        # Load scaler
        scaler_path = models_dir / "scaler.pkl"
        if scaler_path.exists():
            preprocessors['scaler'] = joblib.load(scaler_path)
            logger.info(f"Loaded scaler from {scaler_path}")

        # Load label encoder
        encoder_path = models_dir / "label_encoder.pkl"
        if encoder_path.exists():
            preprocessors['label_encoder'] = joblib.load(encoder_path)
            logger.info(f"Loaded label encoder from {encoder_path}")

        # Load feature names
        features_path = models_dir / "feature_names.pkl"
        if features_path.exists():
            preprocessors['feature_names'] = joblib.load(features_path)
            logger.info(f"Loaded feature names from {features_path}")

        # Load training config
        config_path = models_dir / "training_config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                preprocessors['config'] = json.load(f)
            logger.info(f"Loaded training config from {config_path}")

        return preprocessors

    except Exception as e:
        logger.error(f"Error loading preprocessors: {e}")
        raise


def plot_confusion_matrix(y_true, y_pred, class_names, save_path=None, title="Confusion Matrix"):
    """
    Plot confusion matrix

    Args:
        y_true: True labels
        y_pred: Predicted labels
        class_names: List of class names
        save_path: Optional path to save figure
        title: Title for the plot
    """
    # Handle both direct arrays and pre-computed confusion matrix
    if isinstance(y_true, np.ndarray) and y_true.ndim == 2:
        # Already a confusion matrix
        cm = y_true
    else:
        # Compute confusion matrix
        cm = confusion_matrix(y_true, y_pred)

    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=class_names, yticklabels=class_names)
    plt.title(title)
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')

    # Add percentage annotations
    cm_percent = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis] * 100
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j + 0.5, i + 0.7, f'({cm_percent[i, j]:.1f}%)',
                     ha='center', va='center', fontsize=8)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Confusion matrix saved to {save_path}")

    plt.close()  # Close figure to free memory
    return cm


def plot_feature_importance(feature_names, importance_scores, top_n=20, save_path=None):
    """
    Plot feature importance

    Args:
        feature_names: List of feature names
        importance_scores: Importance scores from model
        top_n: Number of top features to plot
        save_path: Optional path to save figure
    """
    # Create DataFrame and sort
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importance_scores
    }).sort_values('importance', ascending=False)

    # Get top N features
    top_features = importance_df.head(top_n)

    plt.figure(figsize=(12, 8))
    plt.barh(range(len(top_features)), top_features['importance'].values)
    plt.yticks(range(len(top_features)), top_features['feature'].values)
    plt.xlabel('Feature Importance Score')
    plt.title(f'Top {top_n} Feature Importances')
    plt.gca().invert_yaxis()
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Feature importance plot saved to {save_path}")

    plt.close()
    return importance_df


def plot_training_history(history, save_path=None):
    """
    Plot training history (loss and metrics over epochs)

    Args:
        history: Dictionary with training history
        save_path: Optional path to save figure
    """
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))

    # Plot loss
    if 'train_loss' in history:
        axes[0].plot(history['train_loss'], label='Train Loss')
    if 'val_loss' in history:
        axes[0].plot(history['val_loss'], label='Validation Loss')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Model Loss')
    axes[0].legend()
    axes[0].grid(True)

    # Plot accuracy
    if 'train_acc' in history:
        axes[1].plot(history['train_acc'], label='Train Accuracy')
    if 'val_acc' in history:
        axes[1].plot(history['val_acc'], label='Validation Accuracy')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Accuracy')
    axes[1].set_title('Model Accuracy')
    axes[1].legend()
    axes[1].grid(True)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Training history plot saved to {save_path}")

    plt.close()


def plot_class_distribution(y, class_names, title="Class Distribution", save_path=None):
    """
    Plot class distribution

    Args:
        y: Labels array
        class_names: List of class names
        title: Title for the plot
        save_path: Optional path to save figure
    """
    unique, counts = np.unique(y, return_counts=True)

    plt.figure(figsize=(10, 6))
    bars = plt.bar(range(len(unique)), counts)
    plt.xticks(range(len(unique)), [class_names[i] for i in unique], rotation=45)
    plt.xlabel('Attack Type')
    plt.ylabel('Number of Samples')
    plt.title(title)

    # Add value labels on bars
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2., height,
                 f'{count:,}\n({count / sum(counts) * 100:.1f}%)',
                 ha='center', va='bottom')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Class distribution plot saved to {save_path}")

    plt.close()


def calculate_metrics(y_true, y_pred, class_names):
    """
    Calculate comprehensive metrics

    Args:
        y_true: True labels
        y_pred: Predicted labels
        class_names: List of class names

    Returns:
        Dictionary with metrics
    """
    # Get classification report as dict
    report = classification_report(y_true, y_pred,
                                   target_names=class_names,
                                   output_dict=True)

    # Calculate additional metrics
    cm = confusion_matrix(y_true, y_pred)

    # Per-class metrics
    per_class_metrics = {}
    for i, class_name in enumerate(class_names):
        if i < len(cm):
            tn = np.sum(cm) - np.sum(cm[i, :]) - np.sum(cm[:, i]) + cm[i, i]
            fp = np.sum(cm[:, i]) - cm[i, i]
            fn = np.sum(cm[i, :]) - cm[i, i]
            tp = cm[i, i]

            # False Positive Rate
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0

            per_class_metrics[class_name] = {
                'true_positives': int(tp),
                'false_positives': int(fp),
                'true_negatives': int(tn),
                'false_negatives': int(fn),
                'false_positive_rate': float(fpr)
            }

    # Overall metrics
    overall_accuracy = np.sum(np.diag(cm)) / np.sum(cm)

    metrics = {
        'classification_report': report,
        'confusion_matrix': cm.tolist(),
        'per_class_metrics': per_class_metrics,
        'overall_accuracy': float(overall_accuracy),
        'timestamp': datetime.now().isoformat()
    }

    return metrics


def save_model_metadata(model, metrics, save_path):
    """
    Save model metadata and metrics

    Args:
        model: Trained model
        metrics: Dictionary with metrics
        save_path: Path to save metadata
    """
    metadata = {
        'model_type': type(model).__name__,
        'model_params': model.get_params() if hasattr(model, 'get_params') else {},
        'metrics': metrics,
        'timestamp': datetime.now().isoformat()
    }

    with open(save_path, 'w') as f:
        json.dump(metadata, f, indent=4)

    logger.info(f"Model metadata saved to {save_path}")


def print_metrics_summary(metrics):
    """
    Print formatted metrics summary

    Args:
        metrics: Dictionary with metrics
    """
    print("\n" + "=" * 60)
    print("MODEL PERFORMANCE SUMMARY")
    print("=" * 60)

    # Overall accuracy
    print(f"\nOverall Accuracy: {metrics['overall_accuracy']:.4f}")

    # Per-class metrics
    print("\nPer-Class Metrics:")
    print("-" * 50)

    report = metrics['classification_report']
    for class_name in metrics['per_class_metrics'].keys():
        if class_name in report:
            print(f"\n{class_name}:")
            print(f"  Precision: {report[class_name]['precision']:.4f}")
            print(f"  Recall: {report[class_name]['recall']:.4f}")
            print(f"  F1-Score: {report[class_name]['f1-score']:.4f}")
            print(f"  False Positive Rate: {metrics['per_class_metrics'][class_name]['false_positive_rate']:.4f}")
            print(f"  Support: {report[class_name]['support']}")

    # Weighted averages
    print("\n" + "-" * 50)
    print("Weighted Averages:")
    print(f"  Precision: {report['weighted avg']['precision']:.4f}")
    print(f"  Recall: {report['weighted avg']['recall']:.4f}")
    print(f"  F1-Score: {report['weighted avg']['f1-score']:.4f}")

    print("=" * 60)


def check_gpu_availability():
    """
    Check if GPU is available for XGBoost

    Returns:
        Dictionary with GPU info
    """
    gpu_info = {
        'gpu_available': False,
        'cuda_version': None,
        'gpu_count': 0,
        'gpu_names': []
    }

    try:
        import subprocess
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)

        if result.returncode == 0:
            gpu_info['gpu_available'] = True

            # Try to get more info
            result_query = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,driver_version,memory.total', '--format=csv,noheader'],
                capture_output=True, text=True
            )

            if result_query.returncode == 0:
                lines = result_query.stdout.strip().split('\n')
                gpu_info['gpu_count'] = len(lines)
                gpu_info['gpu_names'] = [line.split(',')[0].strip() for line in lines]

            logger.info(f"GPU detected: {gpu_info}")
    except Exception as e:
        logger.info(f"No GPU detected or nvidia-smi not available: {e}")

    return gpu_info


def format_time(seconds):
    """
    Format time in seconds to readable string

    Args:
        seconds: Time in seconds

    Returns:
        Formatted string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"