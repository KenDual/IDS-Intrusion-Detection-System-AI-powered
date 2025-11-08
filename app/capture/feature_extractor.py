"""
Feature Extraction - Compute 25 CICIDS2017 features from network flows
"""
import numpy as np
from typing import Dict, List, Optional
from scapy.all import IP, TCP, UDP, ICMP

from .flow import Flow
from .config import FEATURE_NAMES


def extract_packet_info(packet) -> Optional[Dict]:
    """
    Extract basic information from a single packet

    Args:
        packet: Scapy packet object

    Returns:
        Dictionary with packet info or None if invalid
    """
    if not packet.haslayer(IP):
        return None

    ip_layer = packet[IP]

    info = {
        'src_ip': ip_layer.src,
        'dst_ip': ip_layer.dst,
        'packet_length': len(packet),
        'ip_header_length': ip_layer.ihl * 4,  # IHL in 32-bit words
        'protocol': None,
        'src_port': 0,
        'dst_port': 0,
        'tcp_flags': {
            'syn': 0, 'ack': 0, 'fin': 0,
            'psh': 0, 'rst': 0, 'urg': 0
        },
        'tcp_window': 0,
        'header_length': 0
    }

    # TCP
    if packet.haslayer(TCP):
        tcp_layer = packet[TCP]
        info['protocol'] = 'TCP'
        info['src_port'] = tcp_layer.sport
        info['dst_port'] = tcp_layer.dport
        info['tcp_window'] = tcp_layer.window
        info['header_length'] = info['ip_header_length'] + tcp_layer.dataofs * 4

        # Extract TCP flags
        flags = tcp_layer.flags
        info['tcp_flags']['syn'] = 1 if flags & 0x02 else 0
        info['tcp_flags']['ack'] = 1 if flags & 0x10 else 0
        info['tcp_flags']['fin'] = 1 if flags & 0x01 else 0
        info['tcp_flags']['psh'] = 1 if flags & 0x08 else 0
        info['tcp_flags']['rst'] = 1 if flags & 0x04 else 0
        info['tcp_flags']['urg'] = 1 if flags & 0x20 else 0

    # UDP
    elif packet.haslayer(UDP):
        udp_layer = packet[UDP]
        info['protocol'] = 'UDP'
        info['src_port'] = udp_layer.sport
        info['dst_port'] = udp_layer.dport
        info['header_length'] = info['ip_header_length'] + 8  # UDP header is 8 bytes

    # ICMP
    elif packet.haslayer(ICMP):
        info['protocol'] = 'ICMP'
        info['header_length'] = info['ip_header_length'] + 8  # ICMP header is 8 bytes

    else:
        info['protocol'] = 'OTHER'
        info['header_length'] = info['ip_header_length']

    return info


def compute_flow_features(flow: Flow) -> Dict:
    """
    Compute 25 CICIDS2017 features from a flow

    Args:
        flow: Flow object with packets

    Returns:
        Dictionary with 25 features
    """
    # Extract packet info for all packets
    fwd_packets_info = []
    bwd_packets_info = []

    for packet in flow.fwd_packets:
        info = extract_packet_info(packet)
        if info:
            fwd_packets_info.append(info)

    for packet in flow.bwd_packets:
        info = extract_packet_info(packet)
        if info:
            bwd_packets_info.append(info)

    # Compute features
    features = {}

    # Get packet lengths
    fwd_lengths = [p['packet_length'] for p in fwd_packets_info]
    bwd_lengths = [p['packet_length'] for p in bwd_packets_info]
    all_lengths = fwd_lengths + bwd_lengths

    # Get header lengths
    fwd_headers = [p['header_length'] for p in fwd_packets_info]
    bwd_headers = [p['header_length'] for p in bwd_packets_info]

    # Flow duration
    flow_duration = flow.get_duration()

    # ===== PACKET LENGTH FEATURES =====
    # 1. Avg Fwd Segment Size
    features[' Avg Fwd Segment Size'] = np.mean(fwd_lengths) if fwd_lengths else 0.0

    # 2. Fwd Packet Length Mean
    features[' Fwd Packet Length Mean'] = np.mean(fwd_lengths) if fwd_lengths else 0.0

    # 3. Fwd Packet Length Max
    features[' Fwd Packet Length Max'] = np.max(fwd_lengths) if fwd_lengths else 0.0

    # 4. Subflow Fwd Bytes
    features[' Subflow Fwd Bytes'] = float(np.sum(fwd_lengths))

    # 5. Total Length of Fwd Packets
    features['Total Length of Fwd Packets'] = float(np.sum(fwd_lengths))

    # 6. Packet Length Mean
    features[' Packet Length Mean'] = np.mean(all_lengths) if all_lengths else 0.0

    # 7. Average Packet Size
    features[' Average Packet Size'] = np.mean(all_lengths) if all_lengths else 0.0

    # 8. Bwd Packet Length Mean
    features[' Bwd Packet Length Mean'] = np.mean(bwd_lengths) if bwd_lengths else 0.0

    # 9. Avg Bwd Segment Size
    features[' Avg Bwd Segment Size'] = np.mean(bwd_lengths) if bwd_lengths else 0.0

    # ===== TIMING FEATURES =====
    # 10. Fwd IAT Mean (Inter-Arrival Time)
    fwd_iat = _compute_inter_arrival_times(flow.fwd_timestamps)
    features[' Fwd IAT Mean'] = np.mean(fwd_iat) if len(fwd_iat) > 0 else 0.0

    # 17. Fwd IAT Std
    features[' Fwd IAT Std'] = np.std(fwd_iat) if len(fwd_iat) > 0 else 0.0

    # 20. Flow Duration (in microseconds for CICIDS2017)
    features[' Flow Duration'] = flow_duration * 1_000_000  # Convert to microseconds

    # 23. Flow IAT Std
    all_timestamps = sorted(flow.fwd_timestamps + flow.bwd_timestamps)
    flow_iat = _compute_inter_arrival_times(all_timestamps)
    features[' Flow IAT Std'] = np.std(flow_iat) if len(flow_iat) > 0 else 0.0

    # ===== PACKET COUNT FEATURES =====
    # 11. Total Fwd Packets
    features[' Total Fwd Packets'] = float(len(flow.fwd_packets))

    # 12. Subflow Fwd Packets
    features['Subflow Fwd Packets'] = float(len(flow.fwd_packets))

    # ===== FLOW RATE =====
    # 21. Flow Bytes/s
    total_bytes = np.sum(all_lengths)
    features['Flow Bytes/s'] = total_bytes / flow_duration if flow_duration > 0 else 0.0

    # ===== HEADER LENGTH FEATURES =====
    # 15. Fwd Header Length
    features[' Fwd Header Length'] = float(np.sum(fwd_headers))

    # 22. Bwd Header Length
    features[' Bwd Header Length'] = float(np.sum(bwd_headers))

    # 19. Total Length of Bwd Packets
    features[' Total Length of Bwd Packets'] = float(np.sum(bwd_lengths))

    # 16. Subflow Bwd Bytes
    features[' Subflow Bwd Bytes'] = float(np.sum(bwd_lengths))

    # ===== TCP FLAGS =====
    # 14. PSH Flag Count
    psh_count = sum(p['tcp_flags']['psh'] for p in fwd_packets_info + bwd_packets_info)
    features[' PSH Flag Count'] = float(psh_count)

    # 25. ACK Flag Count
    ack_count = sum(p['tcp_flags']['ack'] for p in fwd_packets_info + bwd_packets_info)
    features[' ACK Flag Count'] = float(ack_count)

    # ===== TCP WINDOW =====
    # 13. Init_Win_bytes_forward
    features['Init_Win_bytes_forward'] = float(fwd_packets_info[0]['tcp_window']) if fwd_packets_info else 0.0

    # 24. Init_Win_bytes_backward
    features[' Init_Win_bytes_backward'] = float(bwd_packets_info[0]['tcp_window']) if bwd_packets_info else 0.0

    # ===== PORT =====
    # 18. Destination Port
    features[' Destination Port'] = float(flow.dst_port)

    return features


def _compute_inter_arrival_times(timestamps: List[float]) -> List[float]:
    """
    Compute inter-arrival times between consecutive packets

    Args:
        timestamps: List of packet timestamps

    Returns:
        List of IAT values in seconds
    """
    if len(timestamps) < 2:
        return []

    iats = []
    for i in range(1, len(timestamps)):
        iat = timestamps[i] - timestamps[i - 1]
        iats.append(iat * 1_000_000)  # Convert to microseconds

    return iats


def features_to_array(features: Dict) -> np.ndarray:
    """
    Convert feature dictionary to numpy array in correct order

    Args:
        features: Dictionary with 25 features

    Returns:
        Numpy array with 25 values in correct order
    """
    feature_array = []

    for feature_name in FEATURE_NAMES:
        value = features.get(feature_name, 0.0)

        # Handle invalid values
        if np.isnan(value) or np.isinf(value):
            value = 0.0

        feature_array.append(value)

    return np.array(feature_array, dtype=np.float32)


def validate_features(features: Dict) -> bool:
    """
    Validate that features dictionary has all 25 required features

    Args:
        features: Dictionary with features

    Returns:
        True if valid, False otherwise
    """
    # Check count
    if len(features) != 25:
        print(f"[Feature Validation] Expected 25 features, got {len(features)}")
        return False

    # Check all feature names exist
    for feature_name in FEATURE_NAMES:
        if feature_name not in features:
            print(f"[Feature Validation] Missing feature: {feature_name}")
            return False

        # Check for invalid values
        value = features[feature_name]
        if value is None or np.isnan(value):
            print(f"[Feature Validation] Invalid value for {feature_name}: {value}")
            return False

    return True


def extract_features_from_flow(flow: Flow) -> Optional[Dict]:
    """
    High-level function: Extract and validate features from flow

    Args:
        flow: Flow object

    Returns:
        Dictionary with features or None if invalid
    """
    try:
        # Compute features
        features = compute_flow_features(flow)

        # Validate
        if not validate_features(features):
            return None

        return features

    except Exception as e:
        print(f"[Feature Extraction Error] {e}")
        return None