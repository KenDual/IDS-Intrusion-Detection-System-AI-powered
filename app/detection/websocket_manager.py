"""
WebSocket Manager for IDS Detection Engine
Manages WebSocket connections and broadcasts real-time alerts to all connected clients.

Flow:
1. Client connects → Add to active_connections
2. Detection Engine creates alert → Push to broadcast_queue
3. Background worker gets from queue → Broadcast to all clients
4. Client disconnects → Remove from active_connections
"""

import asyncio
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

try:
    from fastapi import WebSocket
except ImportError:
    # For testing without FastAPI
    WebSocket = None

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Singleton class to manage WebSocket connections and alert broadcasting.

    Key features:
    - Manages active WebSocket connections
    - Broadcasts alerts to all clients
    - Background worker for async broadcasting
    - Handles disconnections gracefully
    - Statistics tracking
    """

    _instance: Optional['ConnectionManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Active WebSocket connections
        self.active_connections: List[WebSocket] = []

        # Broadcast queue
        self.broadcast_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)

        # Background worker task
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False

        # Statistics
        self._total_connections = 0
        self._total_broadcasts = 0
        self._failed_broadcasts = 0

        self._initialized = True
        logger.info("ConnectionManager initialized")

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance

        Example:
            await manager.connect(websocket)
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        self._total_connections += 1

        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance

        Example:
            manager.disconnect(websocket)
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        """
        Send message to a specific client.

        Args:
            message: JSON string or text message
            websocket: Target WebSocket
        """
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str) -> None:
        """
        Broadcast message to all connected clients.

        Args:
            message: JSON string to broadcast

        Example:
            alert_json = json.dumps({"alert": "DDoS detected"})
            await manager.broadcast(alert_json)
        """
        if not self.active_connections:
            logger.debug("No active connections to broadcast to")
            return

        dead_connections = []

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send to connection: {e}")
                dead_connections.append(connection)
                self._failed_broadcasts += 1

        # Remove dead connections
        for connection in dead_connections:
            self.disconnect(connection)

        if dead_connections:
            logger.info(f"Removed {len(dead_connections)} dead connections")

        self._total_broadcasts += 1

    async def broadcast_alert(self, alert_data: Dict[str, Any]) -> None:
        """
        Broadcast alert to all clients (async).

        Args:
            alert_data: Alert dictionary

        Example:
            alert = {
                "id": 123,
                "source_ip": "10.0.0.50",
                "attack_type": "DDoS",
                "confidence": 0.98
            }
            await manager.broadcast_alert(alert)
        """
        try:
            # Convert to JSON
            message = json.dumps(alert_data)

            # Broadcast
            await self.broadcast(message)

            logger.debug(f"Alert broadcasted: {alert_data.get('attack_type')} from {alert_data.get('source_ip')}")

        except Exception as e:
            logger.error(f"Failed to broadcast alert: {e}")

    async def push_alert_to_queue(self, alert_data: Dict[str, Any]) -> None:
        """
        Push alert to broadcast queue (non-blocking).

        Args:
            alert_data: Alert dictionary

        Example:
            manager.push_alert_to_queue(alert)
        """
        try:
            # Add timestamp if not present
            if 'timestamp' not in alert_data:
                alert_data['timestamp'] = datetime.now().isoformat()

            # Put in queue (non-blocking with timeout)
            await asyncio.wait_for(
                self.broadcast_queue.put(alert_data),
                timeout=1.0
            )

            logger.debug(f"Alert pushed to queue (size: {self.broadcast_queue.qsize()})")

        except asyncio.TimeoutError:
            logger.error("Broadcast queue full, alert dropped")
        except Exception as e:
            logger.error(f"Failed to push alert to queue: {e}")

    async def broadcast_worker(self) -> None:
        """
        Background worker that processes broadcast queue.
        Continuously gets alerts from queue and broadcasts them.

        This runs in the background while detection is active.
        """
        logger.info("Broadcast worker started")

        while self._running:
            try:
                # Get alert from queue (with timeout)
                alert_data = await asyncio.wait_for(
                    self.broadcast_queue.get(),
                    timeout=1.0
                )

                # Broadcast to all clients
                await self.broadcast_alert(alert_data)

            except asyncio.TimeoutError:
                # No alerts in queue, continue
                continue
            except asyncio.CancelledError:
                logger.info("Broadcast worker cancelled")
                break
            except Exception as e:
                logger.error(f"Broadcast worker error: {e}")
                await asyncio.sleep(1)

        logger.info("Broadcast worker stopped")

    async def start_worker(self) -> None:
        """
        Start the background broadcast worker.

        Example:
            await manager.start_worker()
        """
        if self._worker_task is not None:
            logger.warning("Broadcast worker already running")
            return

        self._running = True
        self._worker_task = asyncio.create_task(self.broadcast_worker())
        logger.info("Broadcast worker task created")

    async def stop_worker(self) -> None:
        """
        Stop the background broadcast worker.

        Example:
            await manager.stop_worker()
        """
        if self._worker_task is None:
            return

        self._running = False

        # Cancel task
        self._worker_task.cancel()

        try:
            await self._worker_task
        except asyncio.CancelledError:
            pass

        self._worker_task = None
        logger.info("Broadcast worker stopped")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get WebSocket statistics.

        Returns:
            Dict with statistics
        """
        return {
            "active_connections": len(self.active_connections),
            "total_connections": self._total_connections,
            "total_broadcasts": self._total_broadcasts,
            "failed_broadcasts": self._failed_broadcasts,
            "queue_size": self.broadcast_queue.qsize()
        }

    def is_running(self) -> bool:
        """Check if broadcast worker is running"""
        return self._running and self._worker_task is not None

    @classmethod
    def get_instance(cls) -> 'ConnectionManager':
        """Get singleton instance of ConnectionManager"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# Convenience function
def get_connection_manager() -> ConnectionManager:
    """Get ConnectionManager singleton instance"""
    return ConnectionManager.get_instance()


if __name__ == "__main__":
    # Simple test (without FastAPI WebSocket)
    import asyncio

    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("Testing ConnectionManager (Basic)")
    print("=" * 60)


    async def test_manager():
        try:
            # Create manager
            print("\n[1] Creating ConnectionManager...")
            manager = ConnectionManager.get_instance()
            print("✅ Manager created")

            # Start worker
            print("\n[2] Starting broadcast worker...")
            await manager.start_worker()
            print("✅ Worker started")

            # Push some test alerts
            print("\n[3] Pushing test alerts to queue...")
            for i in range(3):
                alert = {
                    "id": i,
                    "source_ip": f"10.0.0.{i}",
                    "attack_type": "DDoS",
                    "confidence": 0.95
                }
                await manager.push_alert_to_queue(alert)
            print("✅ Alerts pushed")

            # Wait for worker to process
            print("\n[4] Waiting for worker to process...")
            await asyncio.sleep(2)

            # Get statistics
            print("\n[5] Statistics:")
            stats = manager.get_statistics()
            for key, value in stats.items():
                print(f"  {key}: {value}")

            # Stop worker
            print("\n[6] Stopping worker...")
            await manager.stop_worker()
            print("✅ Worker stopped")

            print("\n✅ ConnectionManager basic test PASSED!")
            print("Note: Full test with WebSocket requires FastAPI server")

        except Exception as e:
            print(f"\n❌ Test FAILED: {e}")
            import traceback
            traceback.print_exc()


    asyncio.run(test_manager())