"""
Test script for AlertCache (Phase 5.2)

Tests:
1. Add alert to cache
2. Check duplicate detection (same IP + attack type)
3. Check non-duplicate (different IP or attack type)
4. Check expiration after time window
5. Test cleanup function
6. Test statistics
7. Test singleton pattern

Run: python scripts/test_alert_cache.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import time
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_alert_cache():
    """Test AlertCache functionality"""
    from app.detection import get_alert_cache

    print("=" * 70)
    print("TESTING ALERT CACHE - Phase 5.2")
    print("=" * 70)

    try:
        # Create cache
        print("\n[1/9] Creating AlertCache...")
        cache = get_alert_cache()
        cache.clear()  # Start fresh
        print("✅ AlertCache created")

        # Test 2: Add first alert
        print("\n[2/9] Adding alert: 10.0.0.50 -> DDoS")
        cache.add("10.0.0.50", "DDoS")

        # Check if it's now a duplicate
        is_dup = cache.is_duplicate("10.0.0.50", "DDoS")
        print(f"  Is duplicate? {is_dup}")
        assert is_dup == True, "Should be duplicate"
        print("✅ Duplicate detection working")

        # Test 3: Different attack type (NOT duplicate)
        print("\n[3/9] Checking: 10.0.0.50 -> PortScan (different attack)")
        is_dup = cache.is_duplicate("10.0.0.50", "PortScan")
        print(f"  Is duplicate? {is_dup}")
        assert is_dup == False, "Should NOT be duplicate (different attack type)"
        print("✅ Different attack type correctly identified as non-duplicate")

        # Test 4: Different IP (NOT duplicate)
        print("\n[4/9] Checking: 10.0.0.51 -> DDoS (different IP)")
        is_dup = cache.is_duplicate("10.0.0.51", "DDoS")
        print(f"  Is duplicate? {is_dup}")
        assert is_dup == False, "Should NOT be duplicate (different IP)"
        print("✅ Different IP correctly identified as non-duplicate")

        # Test 5: Add more unique alerts
        print("\n[5/9] Adding more alerts...")
        cache.add("10.0.0.50", "PortScan")
        cache.add("10.0.0.51", "DDoS")
        cache.add("192.168.1.100", "DoS Hulk")
        cache.add("8.8.8.8", "DDoS")

        stats = cache.get_statistics()
        print(f"  Cache size: {stats['cache_size']}")
        print(f"  Unique alerts: {stats['unique_alerts']}")
        assert stats['cache_size'] == 5, f"Expected 5 entries, got {stats['cache_size']}"
        print("✅ Multiple alerts added successfully")

        # Test 6: Statistics
        print("\n[6/9] Checking statistics...")
        stats = cache.get_statistics()
        print(f"  Total checks: {stats['total_checks']}")
        print(f"  Duplicates blocked: {stats['duplicates_blocked']}")
        print(f"  Unique alerts: {stats['unique_alerts']}")
        print(f"  Cache size: {stats['cache_size']}")
        print(f"  Block rate: {stats['block_rate']}%")
        assert stats['total_checks'] > 0
        assert stats['duplicates_blocked'] >= 1
        print("✅ Statistics tracking working")

        # Test 7: Expiration test
        print("\n[7/9] Testing expiration (wait 3s, window=2s)...")
        cache.add("10.0.0.99", "TestAttack")
        print("  Alert added, waiting 3 seconds...")
        time.sleep(3)

        # Should NOT be duplicate (expired after 2s window)
        is_dup = cache.is_duplicate("10.0.0.99", "TestAttack", window=2)
        print(f"  Is duplicate after 3s? {is_dup}")
        assert is_dup == False, "Should be expired (not duplicate)"
        print("✅ Expiration working correctly")

        # Test 8: Cleanup
        print("\n[8/9] Testing cleanup...")
        removed = cache.cleanup(window=2)
        print(f"  Removed {removed} expired entries")
        assert removed > 0, "Should have removed some entries"

        stats_after = cache.get_statistics()
        print(f"  Cache size after cleanup: {stats_after['cache_size']}")
        print("✅ Cleanup working")

        # Test 9: Singleton pattern
        print("\n[9/9] Testing singleton pattern...")
        cache2 = get_alert_cache()
        assert cache is cache2, "Should be same instance"
        print("✅ Singleton pattern working")

        # Summary
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)

        final_stats = cache.get_statistics()
        print("\n📋 Final Statistics:")
        print(f"  ✓ Total checks: {final_stats['total_checks']}")
        print(f"  ✓ Duplicates blocked: {final_stats['duplicates_blocked']}")
        print(f"  ✓ Unique alerts: {final_stats['unique_alerts']}")
        print(f"  ✓ Cache size: {final_stats['cache_size']}")
        print(f"  ✓ Block rate: {final_stats['block_rate']}%")

        print("\n🎉 Phase 5.2 COMPLETE - Alert Cache is ready!")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_alert_cache()
    sys.exit(0 if success else 1)