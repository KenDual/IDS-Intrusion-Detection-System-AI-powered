import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ML_DIR = BASE_DIR / "ml"
MODELS_DIR = ML_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ids.db")

# API Settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Model Settings
MODEL_PATH = MODELS_DIR / "xgboost_model.json"
SCALER_PATH = MODELS_DIR / "scaler.pkl"
LABEL_ENCODER_PATH = MODELS_DIR / "label_encoder.pkl"

# Dataset
CLEANED_DATA_PATH = DATA_DIR / "cleaned_data.csv"

# Attack Classes
ATTACK_CLASSES = [
    'BENIGN',
    'DoS Hulk',
    'PortScan',
    'DDoS'
]

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

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "ids.log"