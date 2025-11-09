"""
Detection Service - Main Detection Engine
Integrates all components for real-time attack detection.

Flow:
1. Get features from CaptureService queue
2. Predict attack type with ModelLoader
3. Filter BENIGN traffic
4. Check confidence threshold
5. Check whitelist
6. Check deduplication (AlertCache)
7. Create alert in database
8. Push to WebSocket broadcast queue

Dependencies:
- CaptureService (Phase 4)
- ModelLoader (Phase 5.1)
- AlertCache (Phase 5.2)
- ConnectionManager (Phase 5.3)
- Database CRUD (Phase 3)
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import numpy as np

from .model_loader import get_model_loader
from .alert_cache import get_alert_cache
from .websocket_manager import get_connection_manager

logger = logging.getLogger(__name__)


class DetectionService:
    """
    Singleton class for real-time attack detection.

    Integrates:
    - Packet capture (CaptureService)
    - ML prediction (ModelLoader)
    - Alert deduplication (AlertCache)
    - Database storage (CRUD)
    - Real-time broadcasting (ConnectionManager)
    """

    _instance: Optional['DetectionService'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Components
        self.model_loader = None
        self.alert_cache = None
        self.connection_manager = None
        self.capture_service = None

        # Database session (will be set from FastAPI)
        self.db_session = None

        # Detection loop task
        self._detection_task: Optional[asyncio.Task] = None
        self._running = False

        # Configuration (from SystemConfig)
        self.alert_threshold = 0.95  # Default
        self.whitelist_ips = set()

        # Statistics
        self.stats = {
            "total_predictions": 0,
            "alerts_created": 0,
            "duplicates_blocked": 0,
            "whitelist_skipped": 0,
            "benign_filtered": 0,
            "low_confidence_skipped": 0,
            "attacks_by_type": {
                "DoS Hulk": 0,
                "PortScan": 0,
                "DDoS": 0
            }
        }

        self._initialized = True
        logger.info("DetectionService initialized")

    def initialize_components(self, capture_service=None, db_session=None):
        """
        Initialize all detection components.

        Args:
            capture_service: CaptureService instance (optional)
            db_session: Database session (optional)
        """
        try:
            # Load ML model
            logger.info("Loading ML model...")
            self.model_loader = get_model_loader()

            # Get alert cache
            logger.info("Getting alert cache...")
            self.alert_cache = get_alert_cache()

            # Get connection manager
            logger.info("Getting connection manager...")
            self.connection_manager = get_connection_manager()

            # Set capture service
            if capture_service:
                self.capture_service = capture_service

            # Set database session
            if db_session:
                self.db_session = db_session

            # Load configuration
            self._load_config()

            logger.info("All detection components initialized")

        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise

    def _load_config(self):
        """Load configuration from database or use defaults"""
        try:
            if self.db_session is None:
                logger.warning("No database session, using default config")
                return

            # Import here to avoid circular dependency
            from app.crud.system_config import get_config
            from app.crud.whitelist import get_all_whitelist

            # Load alert threshold
            threshold_config = get_config(self.db_session, "alert_threshold")
            if threshold_config:
                self.alert_threshold = float(threshold_config.value)
                logger.info(f"Alert threshold: {self.alert_threshold}")

            # Load whitelist
            whitelist_entries = get_all_whitelist(self.db_session)
            self.whitelist_ips = {entry.ip_address for entry in whitelist_entries}
            logger.info(f"Loaded {len(self.whitelist_ips)} whitelist IPs")

        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            # Continue with defaults

    def reload_whitelist(self):
        """Reload whitelist from database"""
        if self.db_session is None:
            return

        try:
            from app.crud.whitelist import get_all_whitelist
            whitelist_entries = get_all_whitelist(self.db_session)
            self.whitelist_ips = {entry.ip_address for entry in whitelist_entries}
            logger.info(f"Whitelist reloaded: {len(self.whitelist_ips)} IPs")
        except Exception as e:
            logger.error(f"Failed to reload whitelist: {e}")

    async def start(self):
        """Start detection service"""
        if self._running:
            logger.warning("Detection service already running")
            return

        logger.info("Starting detection service...")

        # Verify components initialized
        if self.model_loader is None:
            raise RuntimeError("Components not initialized. Call initialize_components() first.")

        # Start WebSocket broadcast worker
        await self.connection_manager.start_worker()

        # Start detection loop
        self._running = True
        self._detection_task = asyncio.create_task(self._detection_loop())

        logger.info("Detection service started")

    async def stop(self):
        """Stop detection service gracefully"""
        if not self._running:
            return

        logger.info("Stopping detection service...")

        self._running = False

        # Cancel detection task
        if self._detection_task:
            self._detection_task.cancel()
            try:
                await self._detection_task
            except asyncio.CancelledError:
                pass

        # Stop WebSocket worker
        await self.connection_manager.stop_worker()

        logger.info("Detection service stopped")

    async def _detection_loop(self):
        """
        Main detection loop - processes features from capture service.
        This is the CORE of the IDS!
        """
        logger.info("Detection loop started")

        while self._running:
            try:
                # Step 1: Get features from capture service
                if self.capture_service is None:
                    await asyncio.sleep(1)
                    continue

                features_data = await self.capture_service.get_next_features(timeout=1.0)

                if features_data is None:
                    # No features available, continue
                    continue

                # Parse features and flow info
                features = features_data.get("features")
                flow_info = features_data.get("flow_info")

                if features is None or flow_info is None:
                    logger.warning("Invalid features data received")
                    continue

                # Validate features
                if not isinstance(features, np.ndarray) or len(features) != 25:
                    logger.warning(f"Invalid features: expected 25, got {len(features)}")
                    continue

                # Step 2: Predict attack type
                try:
                    attack_type, confidence = self.model_loader.predict(features)
                    self.stats["total_predictions"] += 1
                except Exception as e:
                    logger.error(f"Prediction failed: {e}")
                    continue

                # Step 3: Filter BENIGN traffic
                if attack_type == "BENIGN":
                    self.stats["benign_filtered"] += 1
                    continue

                # Step 4: Check confidence threshold
                if confidence < self.alert_threshold:
                    self.stats["low_confidence_skipped"] += 1
                    logger.debug(f"Low confidence skipped: {attack_type} ({confidence:.2f})")
                    continue

                # Step 5: Check whitelist
                source_ip = flow_info.get("source_ip")
                if source_ip in self.whitelist_ips:
                    self.stats["whitelist_skipped"] += 1
                    logger.debug(f"Whitelisted IP skipped: {source_ip}")
                    continue

                # Step 6: Check deduplication
                if self.alert_cache.is_duplicate(source_ip, attack_type):
                    self.stats["duplicates_blocked"] += 1
                    continue

                # Step 7: Create alert
                alert_data = {
                    "source_ip": source_ip,
                    "dest_ip": flow_info.get("dest_ip"),
                    "attack_type": attack_type,
                    "confidence": confidence,
                    "severity": "critical" if confidence >= 0.95 else "low",
                    "timestamp": datetime.now()
                }

                # Save to database
                alert_id = None
                if self.db_session:
                    try:
                        from app.crud.alert import create_alert
                        alert_obj = create_alert(self.db_session, alert_data)
                        alert_id = alert_obj.id
                        logger.info(
                            f"Alert created: ID={alert_id}, {attack_type} from {source_ip} (conf: {confidence:.2f})")
                    except Exception as e:
                        logger.error(f"Failed to save alert to database: {e}")
                        # Continue without database (for testing)

                # Step 8: Update cache and statistics
                self.alert_cache.add(source_ip, attack_type)
                self.stats["alerts_created"] += 1
                self.stats["attacks_by_type"][attack_type] = self.stats["attacks_by_type"].get(attack_type, 0) + 1

                # Step 9: Broadcast to WebSocket clients
                broadcast_data = alert_data.copy()
                if alert_id:
                    broadcast_data["id"] = alert_id
                broadcast_data["timestamp"] = broadcast_data["timestamp"].isoformat()

                await self.connection_manager.push_alert_to_queue(broadcast_data)

            except asyncio.CancelledError:
                logger.info("Detection loop cancelled")
                break
            except Exception as e:
                logger.error(f"Detection loop error: {e}")
                await asyncio.sleep(1)

        logger.info("Detection loop stopped")

    def get_statistics(self) -> Dict[str, Any]:
        """Get detection statistics"""
        stats = self.stats.copy()

        # Add component statistics
        if self.alert_cache:
            stats["cache_stats"] = self.alert_cache.get_statistics()

        if self.connection_manager:
            stats["websocket_stats"] = self.connection_manager.get_statistics()

        if self.capture_service:
            stats["capture_stats"] = self.capture_service.get_statistics()

        return stats

    def is_running(self) -> bool:
        """Check if detection is running"""
        return self._running and self._detection_task is not None

    @classmethod
    def get_instance(cls) -> 'DetectionService':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# Convenience function
def get_detection_service() -> DetectionService:
    """Get DetectionService singleton instance"""
    return DetectionService.get_instance()


if __name__ == "__main__":
    # Basic test
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("Testing DetectionService (Basic)")
    print("=" * 60)

    try:
        # Create service
        print("\n[1] Creating DetectionService...")
        service = DetectionService.get_instance()
        print("✅ Service created")

        # Initialize components (without capture service for now)
        print("\n[2] Initializing components...")
        service.initialize_components()
        print("✅ Components initialized")

        # Get statistics
        print("\n[3] Statistics:")
        stats = service.get_statistics()
        print(f"  Total predictions: {stats['total_predictions']}")
        print(f"  Alerts created: {stats['alerts_created']}")
        print(f"  Alert threshold: {service.alert_threshold}")

        print("\n✅ DetectionService basic test PASSED!")
        print("Note: Full test requires CaptureService (Phase 4)")

    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback

        traceback.print_exc()