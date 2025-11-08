"""
Flow Manager - Manage active flows and handle timeouts
"""
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from .flow import Flow, create_flow_key, create_reverse_flow_key
from .feature_extractor import extract_features_from_flow
from .config import MAX_ACTIVE_FLOWS


class FlowManager:
    """
    Manages active network flows and handles flow timeouts
    """

    def __init__(self):
        """Initialize flow manager"""
        # Dictionary: flow_key -> Flow object
        self.active_flows: Dict[Tuple, Flow] = {}

        # Statistics
        self.total_flows_created = 0
        self.total_flows_expired = 0
        self.total_packets_processed = 0

    def add_packet_to_flow(self, packet) -> Optional[str]:
        """
        Add packet to appropriate flow (create new flow if needed)

        Args:
            packet: Scapy packet object

        Returns:
            Flow ID if successful, None if packet invalid
        """
        # Create flow key from packet
        flow_key = create_flow_key(packet)
        if flow_key is None:
            return None

        self.total_packets_processed += 1

        # Check if flow exists (forward direction)
        if flow_key in self.active_flows:
            flow = self.active_flows[flow_key]
            flow.add_packet(packet)
            return self._flow_key_to_id(flow_key)

        # Check if flow exists (backward direction - reverse key)
        reverse_key = create_reverse_flow_key(flow_key)
        if reverse_key in self.active_flows:
            flow = self.active_flows[reverse_key]
            flow.add_packet(packet)
            return self._flow_key_to_id(reverse_key)

        # Create new flow
        if len(self.active_flows) >= MAX_ACTIVE_FLOWS:
            # Remove oldest flows if limit reached
            self._remove_oldest_flows(count=100)

        new_flow = Flow(flow_key, packet)
        self.active_flows[flow_key] = new_flow
        self.total_flows_created += 1

        return self._flow_key_to_id(flow_key)

    def get_expired_flows(self, extract_features: bool = True) -> List[Dict]:
        """
        Get all expired flows (timeout > FLOW_TIMEOUT)
        Remove them from active_flows and optionally extract features

        Args:
            extract_features: If True, extract features from expired flows

        Returns:
            List of dictionaries with flow info and features
        """
        expired_flows = []
        expired_keys = []

        # Find expired flows
        for flow_key, flow in self.active_flows.items():
            if flow.is_expired():
                expired_keys.append(flow_key)

                flow_info = {
                    'flow_id': self._flow_key_to_id(flow_key),
                    'src_ip': flow.src_ip,
                    'dst_ip': flow.dst_ip,
                    'src_port': flow.src_port,
                    'dst_port': flow.dst_port,
                    'protocol': flow.protocol,
                    'duration': flow.get_duration(),
                    'total_packets': flow.get_total_packets(),
                    'fwd_packets': len(flow.fwd_packets),
                    'bwd_packets': len(flow.bwd_packets),
                    'start_time': flow.start_time,
                    'features': None
                }

                # Extract features if requested
                if extract_features:
                    features = extract_features_from_flow(flow)
                    if features:
                        flow_info['features'] = features

                expired_flows.append(flow_info)

        # Remove expired flows from active_flows
        for flow_key in expired_keys:
            del self.active_flows[flow_key]
            self.total_flows_expired += 1

        return expired_flows

    def get_flow_by_key(self, flow_key: Tuple) -> Optional[Flow]:
        """
        Get flow object by flow key

        Args:
            flow_key: Flow key tuple

        Returns:
            Flow object or None
        """
        return self.active_flows.get(flow_key)

    def get_active_flow_count(self) -> int:
        """
        Get number of active flows

        Returns:
            Count of active flows
        """
        return len(self.active_flows)

    def get_statistics(self) -> Dict:
        """
        Get flow manager statistics

        Returns:
            Dictionary with statistics
        """
        return {
            'active_flows': len(self.active_flows),
            'total_flows_created': self.total_flows_created,
            'total_flows_expired': self.total_flows_expired,
            'total_packets_processed': self.total_packets_processed
        }

    def clear_all_flows(self) -> int:
        """
        Clear all active flows (for reset/shutdown)

        Returns:
            Number of flows cleared
        """
        count = len(self.active_flows)
        self.active_flows.clear()
        return count

    def force_expire_all_flows(self, extract_features: bool = True) -> List[Dict]:
        """
        Force expire all active flows (extract features before clearing)
        Useful for shutdown or manual trigger

        Args:
            extract_features: If True, extract features from all flows

        Returns:
            List of flow info dictionaries
        """
        all_flows = []

        for flow_key, flow in self.active_flows.items():
            flow_info = {
                'flow_id': self._flow_key_to_id(flow_key),
                'src_ip': flow.src_ip,
                'dst_ip': flow.dst_ip,
                'src_port': flow.src_port,
                'dst_port': flow.dst_port,
                'protocol': flow.protocol,
                'duration': flow.get_duration(),
                'total_packets': flow.get_total_packets(),
                'fwd_packets': len(flow.fwd_packets),
                'bwd_packets': len(flow.bwd_packets),
                'start_time': flow.start_time,
                'features': None
            }

            # Extract features if requested
            if extract_features:
                features = extract_features_from_flow(flow)
                if features:
                    flow_info['features'] = features

            all_flows.append(flow_info)

        # Clear all flows
        self.active_flows.clear()

        return all_flows

    def _remove_oldest_flows(self, count: int = 100) -> None:
        """
        Remove oldest flows to free up memory

        Args:
            count: Number of oldest flows to remove
        """
        if len(self.active_flows) == 0:
            return

        # Sort flows by start_time (oldest first)
        sorted_flows = sorted(
            self.active_flows.items(),
            key=lambda x: x[1].start_time
        )

        # Remove oldest flows
        for i in range(min(count, len(sorted_flows))):
            flow_key = sorted_flows[i][0]
            del self.active_flows[flow_key]

    def _flow_key_to_id(self, flow_key: Tuple) -> str:
        """
        Convert flow key to readable flow ID string

        Args:
            flow_key: (src_ip, dst_ip, src_port, dst_port, protocol)

        Returns:
            Flow ID string
        """
        src_ip, dst_ip, src_port, dst_port, protocol = flow_key
        return f"{src_ip}:{src_port}->{dst_ip}:{dst_port}-{protocol}"


# Global flow manager instance
_flow_manager_instance: Optional[FlowManager] = None


def get_flow_manager() -> FlowManager:
    """
    Get global flow manager instance (singleton pattern)

    Returns:
        FlowManager instance
    """
    global _flow_manager_instance
    if _flow_manager_instance is None:
        _flow_manager_instance = FlowManager()
    return _flow_manager_instance


def reset_flow_manager() -> None:
    """
    Reset global flow manager instance (for testing or restart)
    """
    global _flow_manager_instance
    _flow_manager_instance = None