import time
from typing import Optional, Tuple
from scapy.all import IP, TCP, UDP, ICMP

from .config import FLOW_TIMEOUT


class Flow:
    """
    Represents a network flow (bidirectional communication)
    Flow is identified by 5-tuple: (src_ip, dst_ip, src_port, dst_port, protocol)
    """

    def __init__(self, flow_key: Tuple[str, str, int, int, str], first_packet):
        """
        Initialize flow with first packet

        Args:
            flow_key: (src_ip, dst_ip, src_port, dst_port, protocol)
            first_packet: Scapy packet object
        """
        self.flow_key = flow_key
        self.src_ip, self.dst_ip, self.src_port, self.dst_port, self.protocol = flow_key

        # Timing
        self.start_time = time.time()
        self.last_seen = self.start_time
        self.end_time = None

        # Packet lists - separate forward and backward
        self.fwd_packets = [first_packet]
        self.bwd_packets = []

        # Packet timestamps
        self.fwd_timestamps = [self.start_time]
        self.bwd_timestamps = []

    def add_packet(self, packet) -> None:
        """
        Add packet to flow (auto-detect forward or backward)

        Args:
            packet: Scapy packet object
        """
        self.last_seen = time.time()

        if self.is_forward_packet(packet):
            self.fwd_packets.append(packet)
            self.fwd_timestamps.append(self.last_seen)
        else:
            self.bwd_packets.append(packet)
            self.bwd_timestamps.append(self.last_seen)

    def is_forward_packet(self, packet) -> bool:
        """
        Check if packet is forward direction (src->dst matches flow direction)

        Args:
            packet: Scapy packet object

        Returns:
            True if forward, False if backward
        """
        if not packet.haslayer(IP):
            return True  # Default to forward if no IP layer

        ip_layer = packet[IP]
        src_ip = ip_layer.src
        dst_ip = ip_layer.dst

        # Get ports if TCP/UDP
        src_port = 0
        dst_port = 0
        if packet.haslayer(TCP):
            src_port = packet[TCP].sport
            dst_port = packet[TCP].dport
        elif packet.haslayer(UDP):
            src_port = packet[UDP].sport
            dst_port = packet[UDP].dport

        # Forward: matches original flow direction
        is_forward = (
                src_ip == self.src_ip and
                dst_ip == self.dst_ip and
                src_port == self.src_port and
                dst_port == self.dst_port
        )

        return is_forward

    def is_expired(self) -> bool:
        """
        Check if flow has timed out (> FLOW_TIMEOUT seconds since last packet)

        Returns:
            True if expired, False otherwise
        """
        elapsed = time.time() - self.last_seen
        return elapsed >= FLOW_TIMEOUT

    def get_duration(self) -> float:
        """
        Get flow duration in seconds

        Returns:
            Duration in seconds
        """
        return self.last_seen - self.start_time

    def get_total_packets(self) -> int:
        """Get total number of packets in flow"""
        return len(self.fwd_packets) + len(self.bwd_packets)

    def __repr__(self):
        return (f"Flow({self.src_ip}:{self.src_port}->{self.dst_ip}:{self.dst_port} "
                f"{self.protocol} | Fwd:{len(self.fwd_packets)} Bwd:{len(self.bwd_packets)})")


def create_flow_key(packet) -> Optional[Tuple[str, str, int, int, str]]:
    """
    Create unique flow key from packet (5-tuple)

    Args:
        packet: Scapy packet object

    Returns:
        Tuple: (src_ip, dst_ip, src_port, dst_port, protocol) or None if invalid
    """
    if not packet.haslayer(IP):
        return None

    ip_layer = packet[IP]
    src_ip = ip_layer.src
    dst_ip = ip_layer.dst

    # Default values
    src_port = 0
    dst_port = 0
    protocol = "OTHER"

    # Extract ports and protocol
    if packet.haslayer(TCP):
        src_port = packet[TCP].sport
        dst_port = packet[TCP].dport
        protocol = "TCP"
    elif packet.haslayer(UDP):
        src_port = packet[UDP].sport
        dst_port = packet[UDP].dport
        protocol = "UDP"
    elif packet.haslayer(ICMP):
        protocol = "ICMP"
        # ICMP doesn't have ports, use type/code as pseudo-ports
        src_port = packet[ICMP].type
        dst_port = packet[ICMP].code

    return (src_ip, dst_ip, src_port, dst_port, protocol)


def create_reverse_flow_key(flow_key: Tuple[str, str, int, int, str]) -> Tuple[str, str, int, int, str]:
    """
    Create reverse flow key (swap src/dst)
    Used to match bidirectional flows

    Args:
        flow_key: Original flow key

    Returns:
        Reversed flow key
    """
    src_ip, dst_ip, src_port, dst_port, protocol = flow_key
    return (dst_ip, src_ip, dst_port, src_port, protocol)