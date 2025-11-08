import os
from pathlib import Path
from dotenv import load_dotenv
import subprocess

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ML_DIR = BASE_DIR / "ml"
MODELS_DIR = ML_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"
REPORTS_DIR = ML_DIR / "reports"  # Thêm reports directory

# Create directories if not exist
MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ids.db")

# API Settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Model Settings
MODEL_PATH = MODELS_DIR / "xgboost_model.pkl"  # Đổi từ .json sang .pkl
SCALER_PATH = MODELS_DIR / "scaler.pkl"
LABEL_ENCODER_PATH = MODELS_DIR / "label_encoder.pkl"
FEATURE_NAMES_PATH = MODELS_DIR / "feature_names.pkl"
TRAINING_CONFIG_PATH = MODELS_DIR / "training_config.json"

# Dataset
CLEANED_DATA_PATH = DATA_DIR / "cleaned_data.csv"

# GPU Configuration
USE_GPU = os.getenv("USE_GPU", "auto")  # "auto", "cpu", "gpu"
GPU_ID = int(os.getenv("GPU_ID", 0))  # GPU device ID

# Auto-detect GPU if set to "auto"
if USE_GPU == "auto":
    try:
        # Check if CUDA is available using nvidia-smi
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        USE_GPU = "gpu" if result.returncode == 0 else "cpu"
    except:
        USE_GPU = "cpu"

# XGBoost Training Parameters
XGBOOST_PARAMS = {
    # GPU/CPU specific
    'tree_method': 'gpu_hist' if USE_GPU == "gpu" else 'hist',
    'predictor': 'gpu_predictor' if USE_GPU == "gpu" else 'cpu_predictor',

    # Model parameters
    'objective': 'multi:softprob',
    'num_class': 4,
    'max_depth': 6,
    'learning_rate': 0.1,
    'n_estimators': 200,
    'subsample': 0.8,
    'colsample_bytree': 0.8,

    # Regularization
    'gamma': 0.1,
    'reg_alpha': 0.1,
    'reg_lambda': 1,

    # Performance
    'n_jobs': -1 if USE_GPU == "cpu" else 1,
    'random_state': 42,
    'eval_metric': 'mlogloss'
}

# Add GPU ID if using GPU
if USE_GPU == "gpu":
    XGBOOST_PARAMS['gpu_id'] = GPU_ID

# Training Configuration
TRAIN_CONFIG = {
    'test_size': 0.2,
    'validation_size': 0.1,  # From training set
    'random_state': 42,
    'stratify': True,
    'use_smote': False,  # Disabled for large dataset - use class_weight instead
    'smote_sampling_strategy': 'auto',
    'cross_validation_folds': 5,
    'early_stopping_rounds': 10,
    'verbose': True
}

# Hyperparameter Grid for Tuning
HYPERPARAM_GRID = {
    'n_estimators': [100, 200, 300],
    'max_depth': [3, 5, 7, 10],
    'learning_rate': [0.01, 0.1, 0.3],
    'subsample': [0.7, 0.8, 0.9],
    'colsample_bytree': [0.7, 0.8, 0.9],
    'gamma': [0, 0.1, 0.2]
}

# Attack Classes
ATTACK_CLASSES = [
    'BENIGN',
    'DoS Hulk',
    'PortScan',
    'DDoS'
]

# Label Encoding
ATTACK_LABELS = {
    'BENIGN': 0,
    'DoS Hulk': 1,
    'PortScan': 2,
    'DDoS': 3
}

# Class weights for imbalanced dataset (approximate from data distribution)
# BENIGN: 81.44%, DoS Hulk: 8.28%, PortScan: 5.69%, DDoS: 4.59%
CLASS_WEIGHTS = {
    0: 1.0,    # BENIGN (majority class)
    1: 9.84,   # DoS Hulk (81.44/8.28)
    2: 14.31,  # PortScan (81.44/5.69)
    3: 17.74   # DDoS (81.44/4.59)
}

# Selected Features (36 features)
SELECTED_FEATURES = [
    ' Destination Port',
    ' Flow Duration',
    'Flow Bytes/s',
    ' Flow Packets/s',
    ' Total Fwd Packets',
    ' Total Backward Packets',
    'Total Length of Fwd Packets',
    ' Total Length of Bwd Packets',
    ' Fwd Packet Length Max',
    ' Fwd Packet Length Min',
    ' Fwd Packet Length Mean',
    ' Bwd Packet Length Mean',
    ' Average Packet Size',
    ' Packet Length Mean',
    ' Flow IAT Mean',
    ' Flow IAT Std',
    ' Fwd IAT Mean',
    ' Fwd IAT Std',
    ' Bwd IAT Mean',
    ' Bwd IAT Std',
    'FIN Flag Count',
    ' SYN Flag Count',
    ' RST Flag Count',
    ' PSH Flag Count',
    ' ACK Flag Count',
    ' URG Flag Count',
    ' Fwd Header Length',
    ' Bwd Header Length',
    ' Avg Fwd Segment Size',
    ' Avg Bwd Segment Size',
    'Subflow Fwd Packets',
    ' Subflow Fwd Bytes',
    ' Subflow Bwd Packets',
    ' Subflow Bwd Bytes',
    'Init_Win_bytes_forward',
    ' Init_Win_bytes_backward'
]

# Monitoring Settings
CAPTURE_INTERFACE = os.getenv("CAPTURE_INTERFACE", "eth0")
ALERT_THRESHOLD = float(os.getenv("ALERT_THRESHOLD", 0.8))
PACKET_BATCH_SIZE = int(os.getenv("PACKET_BATCH_SIZE", 100))
FLOW_TIMEOUT = int(os.getenv("FLOW_TIMEOUT", 5))  # seconds

# Alert Severity Levels
SEVERITY_LEVELS = {
    'Low': 1,
    'Medium': 2,
    'High': 3,
    'Critical': 4
}

# Alert mapping per attack type
ATTACK_SEVERITY = {
    'BENIGN': None,
    'DoS Hulk': 'High',
    'PortScan': 'Medium',
    'DDoS': 'Critical'
}

# Model Performance Thresholds
PERFORMANCE_THRESHOLDS = {
    'min_accuracy': 0.95,
    'min_f1_score': 0.90,
    'max_false_positive_rate': 0.05
}

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "ids.log"

# Memory Management
MAX_MEMORY_GB = int(os.getenv("MAX_MEMORY_GB", 8))  # Max RAM usage
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 10000))  # For batch processing