"""
Capture Service - Integrate packet capture, flow management, and feature extraction
"""
import asyncio
import threading
import time
from typing import Optional, Dict, List

from .sniffer import get_sniffer
from .flow_manager import get_flow_manager, reset_flow_manager
from .config import FLOW_CHECK_INTERVAL, FEATURE_QUEUE_SIZE


class CaptureService:
    """
    High-level capture service that integrates:
    - Packet sniffer (Scapy)
    - Flow manager (grouping packets)
    - Feature extraction (computing features)
    - Feature queue (output to Phase 6)
    """

    def __init__(self):
        """Initialize capture service"""
        self.sniffer = get_sniffer()
        self.flow_manager = get_flow_manager()

        # Asyncio queue for features (consumed by Phase 6)
        self.feature_queue: Optional[asyncio.Queue] = None

        # Background task for checking expired flows
        self.flow_check_task: Optional[asyncio.Task] = None
        self.flow_check_running = False

        # Event loop reference
        self.loop: Optional[asyncio.AbstractEventLoop] = None

        # Statistics
        self.features_extracted = 0
        self.flows_processed = 0

    async def start_monitoring(self) -> bool:
        """
        Start monitoring: capture packets and extract features

        Returns:
            True if started successfully
        """
        # Get/create event loop
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            print("[CaptureService] No running event loop found")
            return False

        # Initialize feature queue
        if self.feature_queue is None:
            self.feature_queue = asyncio.Queue(maxsize=FEATURE_QUEUE_SIZE)

        # Start packet sniffer with callback
        success = self.sniffer.start_capture(callback=self._packet_callback)
        if not success:
            print(f"[CaptureService] Failed to start sniffer: {self.sniffer.error_message}")
            return False

        # Start background task to check expired flows
        self.flow_check_running = True
        self.flow_check_task = asyncio.create_task(self._check_expired_flows_loop())

        print("[CaptureService] Monitoring started")
        return True

    async def stop_monitoring(self) -> Dict:
        """
        Stop monitoring and return statistics

        Returns:
            Dictionary with final statistics
        """
        # Stop flow check task
        self.flow_check_running = False
        if self.flow_check_task:
            self.flow_check_task.cancel()
            try:
                await self.flow_check_task
            except asyncio.CancelledError:
                pass

        # Stop sniffer
        self.sniffer.stop_capture()

        # Force expire remaining flows and extract features
        remaining_flows = self.flow_manager.force_expire_all_flows(extract_features=True)

        # Push remaining features to queue
        for flow_info in remaining_flows:
            if flow_info['features']:
                await self._push_to_queue(flow_info)

        # Get final statistics
        stats = self.get_statistics()

        print(f"[CaptureService] Monitoring stopped. Features extracted: {self.features_extracted}")
        return stats

    def _packet_callback(self, packet) -> None:
        """
        Callback function for each captured packet (called by sniffer)
        Runs in sniffer thread, so use thread-safe operations

        Args:
            packet: Scapy packet object
        """
        try:
            # Add packet to flow manager
            flow_id = self.flow_manager.add_packet_to_flow(packet)

            # Note: We don't check expired flows here to avoid blocking
            # Expired flows are checked periodically by background task

        except Exception as e:
            print(f"[CaptureService] Error in packet callback: {e}")

    async def _check_expired_flows_loop(self) -> None:
        """
        Background task: Periodically check for expired flows and extract features
        """
        print(f"[CaptureService] Flow check loop started (interval: {FLOW_CHECK_INTERVAL}s)")

        while self.flow_check_running:
            try:
                # Check for expired flows
                expired_flows = self.flow_manager.get_expired_flows(extract_features=True)

                # Push features to queue
                for flow_info in expired_flows:
                    if flow_info['features']:
                        await self._push_to_queue(flow_info)
                        self.features_extracted += 1
                        self.flows_processed += 1

                # Sleep for interval
                await asyncio.sleep(FLOW_CHECK_INTERVAL)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[CaptureService] Error in flow check loop: {e}")
                await asyncio.sleep(FLOW_CHECK_INTERVAL)

        print("[CaptureService] Flow check loop stopped")

    async def _push_to_queue(self, flow_info: Dict) -> None:
        """
        Push flow info with features to queue (non-blocking)

        Args:
            flow_info: Dictionary with flow info and features
        """
        try:
            # Try to put in queue without blocking
            # If queue is full, skip (features will be lost - trade-off for real-time)
            if self.feature_queue.full():
                print(f"[CaptureService] Warning: Feature queue full, dropping flow {flow_info['flow_id']}")
            else:
                await asyncio.wait_for(
                    self.feature_queue.put(flow_info),
                    timeout=0.1
                )
        except asyncio.TimeoutError:
            print(f"[CaptureService] Timeout pushing to queue for flow {flow_info['flow_id']}")
        except Exception as e:
            print(f"[CaptureService] Error pushing to queue: {e}")

    async def get_next_features(self, timeout: Optional[float] = None) -> Optional[Dict]:
        """
        Get next flow features from queue (for Phase 6 to consume)

        Args:
            timeout: Max seconds to wait, None = wait forever

        Returns:
            Dictionary with flow info and features, or None if timeout
        """
        if self.feature_queue is None:
            return None

        try:
            if timeout:
                flow_info = await asyncio.wait_for(
                    self.feature_queue.get(),
                    timeout=timeout
                )
            else:
                flow_info = await self.feature_queue.get()

            return flow_info

        except asyncio.TimeoutError:
            return None
        except Exception as e:
            print(f"[CaptureService] Error getting from queue: {e}")
            return None

    def get_statistics(self) -> Dict:
        """
        Get capture service statistics

        Returns:
            Dictionary with statistics
        """
        sniffer_status = self.sniffer.get_capture_status()
        flow_stats = self.flow_manager.get_statistics()

        return {
            'monitoring_active': sniffer_status['is_running'],
            'packets_captured': sniffer_status['packets_captured'],
            'active_flows': flow_stats['active_flows'],
            'total_flows_created': flow_stats['total_flows_created'],
            'total_flows_expired': flow_stats['total_flows_expired'],
            'features_extracted': self.features_extracted,
            'flows_processed': self.flows_processed,
            'queue_size': self.feature_queue.qsize() if self.feature_queue else 0,
            'error_message': sniffer_status.get('error_message')
        }

    def is_monitoring_active(self) -> bool:
        """
        Check if monitoring is currently active

        Returns:
            True if active
        """
        return self.sniffer.is_running

    async def reset(self) -> None:
        """
        Reset service (for testing or restart)
        """
        if self.is_monitoring_active():
            await self.stop_monitoring()

        # Reset flow manager
        reset_flow_manager()
        self.flow_manager = get_flow_manager()

        # Clear queue
        if self.feature_queue:
            while not self.feature_queue.empty():
                try:
                    self.feature_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

        # Reset statistics
        self.features_extracted = 0
        self.flows_processed = 0

        print("[CaptureService] Service reset")


# Global capture service instance
_capture_service_instance: Optional[CaptureService] = None


def get_capture_service() -> CaptureService:
    """
    Get global capture service instance (singleton pattern)

    Returns:
        CaptureService instance
    """
    global _capture_service_instance
    if _capture_service_instance is None:
        _capture_service_instance = CaptureService()
    return _capture_service_instance


async def start_monitoring() -> bool:
    """
    Start monitoring (convenience function)

    Returns:
        True if started successfully
    """
    service = get_capture_service()
    return await service.start_monitoring()


async def stop_monitoring() -> Dict:
    """
    Stop monitoring (convenience function)

    Returns:
        Statistics dictionary
    """
    service = get_capture_service()
    return await service.stop_monitoring()


async def get_next_features(timeout: Optional[float] = None) -> Optional[Dict]:
    """
    Get next features from queue (convenience function)

    Args:
        timeout: Max seconds to wait

    Returns:
        Flow info with features
    """
    service = get_capture_service()
    return await service.get_next_features(timeout=timeout)


def get_monitoring_statistics() -> Dict:
    """
    Get monitoring statistics (convenience function)

    Returns:
        Statistics dictionary
    """
    service = get_capture_service()
    return service.get_statistics()