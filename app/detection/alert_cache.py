"""
Alert Cache for IDS Detection Engine
Prevents duplicate alerts within a time window (default 60 seconds).

Example:
- DDoS from 10.0.0.50 at 10:00:00 → Create alert
- DDoS from 10.0.0.50 at 10:00:30 → Skip (duplicate)
- DDoS from 10.0.0.50 at 10:01:05 → Create alert (>60s passed)
"""

from datetime import datetime, timedelta
from typing import Tuple, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class AlertCache:
    """
    Singleton class to manage alert deduplication cache.

    Key features:
    - Prevents duplicate alerts within time window (default 60s)
    - Auto-cleanup of old entries
    - Thread-safe operations
    - Statistics tracking
    """

    _instance: Optional['AlertCache'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Cache: {(source_ip, attack_type): timestamp}
        self._cache: Dict[Tuple[str, str], datetime] = {}

        # Statistics
        self._total_checks = 0
        self._duplicates_blocked = 0
        self._unique_alerts = 0

        # Default time window (seconds)
        self._default_window = 60

        self._initialized = True
        logger.info("AlertCache initialized")

    def is_duplicate(self, source_ip: str, attack_type: str, window: int = None) -> bool:
        """
        Check if alert is a duplicate within time window.

        Args:
            source_ip: Source IP address
            attack_type: Attack type (e.g., "DDoS", "PortScan")
            window: Time window in seconds (default: 60)

        Returns:
            True if duplicate, False if new/expired

        Example:
            if cache.is_duplicate("10.0.0.50", "DDoS"):
                # Skip alert (duplicate)
                pass
            else:
                # Create alert
                cache.add("10.0.0.50", "DDoS")
        """
        if window is None:
            window = self._default_window

        self._total_checks += 1

        # Create cache key
        cache_key = (source_ip, attack_type)

        # Check if exists in cache
        if cache_key not in self._cache:
            return False

        # Get timestamp from cache
        last_time = self._cache[cache_key]
        now = datetime.now()

        # Check if within window
        time_diff = (now - last_time).total_seconds()

        if time_diff < window:
            # Duplicate found
            self._duplicates_blocked += 1
            logger.debug(f"Duplicate alert blocked: {source_ip} -> {attack_type} "
                         f"(last seen {time_diff:.1f}s ago)")
            return True
        else:
            # Expired, not a duplicate
            return False

    def add(self, source_ip: str, attack_type: str) -> None:
        """
        Add alert to cache with current timestamp.

        Args:
            source_ip: Source IP address
            attack_type: Attack type

        Example:
            cache.add("10.0.0.50", "DDoS")
        """
        cache_key = (source_ip, attack_type)
        self._cache[cache_key] = datetime.now()
        self._unique_alerts += 1

        logger.debug(f"Alert added to cache: {source_ip} -> {attack_type}")

    def cleanup(self, window: int = None) -> int:
        """
        Remove expired entries from cache.

        Args:
            window: Time window in seconds (default: 60)

        Returns:
            Number of entries removed

        Example:
            removed = cache.cleanup()
            print(f"Removed {removed} expired entries")
        """
        if window is None:
            window = self._default_window

        now = datetime.now()
        cutoff_time = now - timedelta(seconds=window)

        # Find expired entries
        expired_keys = [
            key for key, timestamp in self._cache.items()
            if timestamp < cutoff_time
        ]

        # Remove expired entries
        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def get_statistics(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dict with statistics:
            - total_checks: Total is_duplicate() calls
            - duplicates_blocked: Number of duplicates blocked
            - unique_alerts: Number of unique alerts added
            - cache_size: Current cache size
            - block_rate: Percentage of duplicates blocked
        """
        block_rate = (self._duplicates_blocked / self._total_checks * 100) if self._total_checks > 0 else 0

        return {
            "total_checks": self._total_checks,
            "duplicates_blocked": self._duplicates_blocked,
            "unique_alerts": self._unique_alerts,
            "cache_size": len(self._cache),
            "block_rate": round(block_rate, 2)
        }

    def clear(self) -> None:
        """Clear all cache entries and reset statistics."""
        self._cache.clear()
        self._total_checks = 0
        self._duplicates_blocked = 0
        self._unique_alerts = 0
        logger.info("AlertCache cleared")

    def get_cached_alerts(self) -> list:
        """
        Get all cached alerts with timestamps.

        Returns:
            List of dicts: [{"source_ip": "...", "attack_type": "...", "timestamp": ...}, ...]
        """
        return [
            {
                "source_ip": key[0],
                "attack_type": key[1],
                "timestamp": timestamp.isoformat()
            }
            for key, timestamp in self._cache.items()
        ]

    @classmethod
    def get_instance(cls) -> 'AlertCache':
        """Get singleton instance of AlertCache"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# Convenience function
def get_alert_cache() -> AlertCache:
    """Get AlertCache singleton instance"""
    return AlertCache.get_instance()


if __name__ == "__main__":
    # Test the alert cache
    import time

    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("Testing AlertCache")
    print("=" * 60)

    try:
        # Create cache
        cache = AlertCache.get_instance()

        # Test 1: Add first alert
        print("\n[1] Adding alert: 10.0.0.50 -> DDoS")
        cache.add("10.0.0.50", "DDoS")
        is_dup = cache.is_duplicate("10.0.0.50", "DDoS")
        print(f"  Is duplicate? {is_dup} (Expected: True)")
        assert is_dup == True

        # Test 2: Different attack type (not duplicate)
        print("\n[2] Checking: 10.0.0.50 -> PortScan")
        is_dup = cache.is_duplicate("10.0.0.50", "PortScan")
        print(f"  Is duplicate? {is_dup} (Expected: False)")
        assert is_dup == False

        # Test 3: Different IP (not duplicate)
        print("\n[3] Checking: 10.0.0.51 -> DDoS")
        is_dup = cache.is_duplicate("10.0.0.51", "DDoS")
        print(f"  Is duplicate? {is_dup} (Expected: False)")
        assert is_dup == False

        # Test 4: Add more alerts
        print("\n[4] Adding more alerts...")
        cache.add("10.0.0.50", "PortScan")
        cache.add("10.0.0.51", "DDoS")
        cache.add("192.168.1.100", "DoS Hulk")

        # Test 5: Check statistics
        print("\n[5] Statistics:")
        stats = cache.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # Test 6: Wait and test expiration
        print("\n[6] Testing expiration (wait 3s with 2s window)...")
        cache.add("10.0.0.99", "Test")
        time.sleep(3)
        is_dup = cache.is_duplicate("10.0.0.99", "Test", window=2)
        print(f"  Is duplicate after 3s? {is_dup} (Expected: False)")
        assert is_dup == False

        # Test 7: Cleanup
        print("\n[7] Cleanup old entries...")
        removed = cache.cleanup(window=2)
        print(f"  Removed: {removed} entries")

        # Test 8: Get cached alerts
        print("\n[8] Current cached alerts:")
        cached = cache.get_cached_alerts()
        for alert in cached:
            print(f"  {alert['source_ip']} -> {alert['attack_type']}")

        # Final stats
        print("\n[9] Final statistics:")
        stats = cache.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")

        print("\n✅ AlertCache test PASSED!")

    except Exception as e:
        print(f"\n❌ AlertCache test FAILED: {e}")
        import traceback

        traceback.print_exc()