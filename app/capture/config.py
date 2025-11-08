"""
Packet Capture Configuration
"""
import json
import os

# ===========================
# CAPTURE SETTINGS
# ===========================

# INTERFACE = r"\Device\NPF_Loopback"  # Loopback for testing
INTERFACE = r"\Device\NPF_{D9B6EFDD-8496-42FD-9897-59FE5CEA5BBE}"
FLOW_TIMEOUT = 5  # seconds - flows older than this are expired
PROTOCOLS = ['TCP', 'UDP', 'ICMP']  # Protocols to capture

# Packet filter for Scapy
PACKET_FILTER = "tcp or udp or icmp"

# ===========================
# PATHS
# ===========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_DIR = os.path.join(BASE_DIR, "ml")
MODEL_METADATA_PATH = os.path.join(MODEL_DIR, "models", "model_metadata.json")

# ===========================
# FEATURE CONFIGURATION
# ===========================
def load_feature_names():
    """
    Load 25 selected feature names from model_metadata.json
    Returns list of feature names in correct order
    """
    try:
        with open(MODEL_METADATA_PATH, 'r') as f:
            metadata = json.load(f)
            return metadata['selected_features']
    except FileNotFoundError:
        raise FileNotFoundError(f"Model metadata not found at {MODEL_METADATA_PATH}")
    except KeyError:
        raise KeyError("'selected_features' key not found in model_metadata.json")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in {MODEL_METADATA_PATH}")

# Load feature names at module import
FEATURE_NAMES = load_feature_names()
N_FEATURES = len(FEATURE_NAMES)

# ===========================
# FLOW SETTINGS
# ===========================
MAX_ACTIVE_FLOWS = 10000  # Maximum concurrent flows to track
FLOW_CHECK_INTERVAL = 1  # seconds - how often to check for expired flows

# ===========================
# QUEUE SETTINGS
# ===========================
FEATURE_QUEUE_SIZE = 1000  # Maximum features in queue before blocking

# ===========================
# PERFORMANCE
# ===========================
BATCH_SIZE = 10  # Number of flows to process together

print(f"[Config] Loaded {N_FEATURES} features from model metadata")
print(f"[Config] Interface: {INTERFACE}")
print(f"[Config] Flow timeout: {FLOW_TIMEOUT}s")