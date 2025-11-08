"""
Packet Sniffer using Scapy
"""
import threading
import ctypes
import sys
from typing import Optional, Callable
from scapy.all import sniff, get_if_list, conf

from .config import INTERFACE, PACKET_FILTER


class PacketSniffer:
    """
    Packet sniffer using Scapy
    Captures packets from specified interface in a background thread
    """

    def __init__(self):
        self.is_running = False
        self.sniffer_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.packet_callback: Optional[Callable] = None
        self.packets_captured = 0
        self.error_message: Optional[str] = None

    def start_capture(self, callback: Callable) -> bool:
        """
        Start packet capture in background thread

        Args:
            callback: Function to call for each captured packet

        Returns:
            True if started successfully, False otherwise
        """
        if self.is_running:
            self.error_message = "Capture already running"
            return False

        # Check admin privileges
        if not self._is_admin():
            self.error_message = "Admin privileges required for packet capture"
            return False

        # Validate interface
        if not self._validate_interface():
            self.error_message = f"Interface '{INTERFACE}' not found"
            return False

        # Set callback
        self.packet_callback = callback

        # Reset state
        self.stop_event.clear()
        self.packets_captured = 0
        self.error_message = None

        # Start sniffer thread
        self.sniffer_thread = threading.Thread(
            target=self._sniff_packets,
            daemon=True,
            name="PacketSnifferThread"
        )
        self.sniffer_thread.start()
        self.is_running = True

        print(f"[Sniffer] Started capturing on {INTERFACE}")
        return True

    def stop_capture(self) -> bool:
        """
        Stop packet capture

        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.is_running:
            self.error_message = "Capture not running"
            return False

        print(f"[Sniffer] Stopping capture...")
        self.stop_event.set()
        self.is_running = False

        # Wait for thread to finish (with timeout)
        if self.sniffer_thread and self.sniffer_thread.is_alive():
            self.sniffer_thread.join(timeout=2.0)

        print(f"[Sniffer] Stopped. Total packets captured: {self.packets_captured}")
        return True

    def get_capture_status(self) -> dict:
        """
        Get current capture status

        Returns:
            Dictionary with status information
        """
        return {
            'is_running': self.is_running,
            'interface': INTERFACE,
            'packets_captured': self.packets_captured,
            'error_message': self.error_message,
            'filter': PACKET_FILTER
        }

    def _sniff_packets(self) -> None:
        """
        Internal method: Sniff packets in background thread
        """
        try:
            # Use Scapy sniff with stop_filter
            sniff(
                iface=INTERFACE,
                filter=PACKET_FILTER,
                prn=self._packet_handler,
                store=False,  # Don't store packets in memory
                stop_filter=lambda x: self.stop_event.is_set()
            )
        except PermissionError:
            self.error_message = "Permission denied. Run as Administrator."
            self.is_running = False
        except Exception as e:
            self.error_message = f"Sniffer error: {str(e)}"
            self.is_running = False
            print(f"[Sniffer Error] {self.error_message}")

    def _packet_handler(self, packet) -> None:
        """
        Internal method: Handle captured packet

        Args:
            packet: Scapy packet object
        """
        try:
            self.packets_captured += 1

            # Call user callback
            if self.packet_callback:
                self.packet_callback(packet)

        except Exception as e:
            print(f"[Sniffer] Error processing packet: {e}")

    def _is_admin(self) -> bool:
        """
        Check if running with administrator privileges (Windows)

        Returns:
            True if admin, False otherwise
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            # If check fails, assume not admin
            return False

    def _validate_interface(self) -> bool:
        """
        Validate that the specified interface exists

        Returns:
            True if interface exists, False otherwise
        """
        try:
            available_interfaces = get_if_list()

            # Check if interface exists
            if INTERFACE in available_interfaces:
                return True

            # Print available interfaces for debugging
            print(f"[Sniffer] Available interfaces: {available_interfaces}")
            return False

        except Exception as e:
            print(f"[Sniffer] Error validating interface: {e}")
            return False


# Global sniffer instance
_sniffer_instance: Optional[PacketSniffer] = None


def get_sniffer() -> PacketSniffer:
    """
    Get global sniffer instance (singleton pattern)

    Returns:
        PacketSniffer instance
    """
    global _sniffer_instance
    if _sniffer_instance is None:
        _sniffer_instance = PacketSniffer()
    return _sniffer_instance


def start_capture(callback: Callable) -> bool:
    """
    Start packet capture with callback

    Args:
        callback: Function to call for each packet

    Returns:
        True if started successfully
    """
    sniffer = get_sniffer()
    return sniffer.start_capture(callback)


def stop_capture() -> bool:
    """
    Stop packet capture

    Returns:
        True if stopped successfully
    """
    sniffer = get_sniffer()
    return sniffer.stop_capture()


def get_capture_status() -> dict:
    """
    Get capture status

    Returns:
        Status dictionary
    """
    sniffer = get_sniffer()
    return sniffer.get_capture_status()