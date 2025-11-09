"""
Test script for DetectionService (Phase 5.4)

Tests:
1. Create DetectionService (singleton)
2. Initialize components
3. Check configuration
4. Test statistics
5. Test singleton pattern

Note: Full end-to-end test requires CaptureService + Database (later phases)

Run: python scripts/test_detection_service.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_detection_service():
    """Test DetectionService basic functionality"""
    from app.detection import get_detection_service

    print("=" * 70)
    print("TESTING DETECTION SERVICE - Phase 5.4")
    print("=" * 70)

    try:
        # Test 1: Create service
        print("\n[1/7] Creating DetectionService...")
        service = get_detection_service()
        print("✅ DetectionService created")

        # Test 2: Initialize components (without DB for now)
        print("\n[2/7] Initializing components...")
        service.initialize_components()
        print("✅ Components initialized")
        print(f"  Model loader: {service.model_loader is not None}")
        print(f"  Alert cache: {service.alert_cache is not None}")
        print(f"  Connection manager: {service.connection_manager is not None}")

        # Test 3: Check configuration
        print("\n[3/7] Checking configuration...")
        print(f"  Alert threshold: {service.alert_threshold}")
        print(f"  Whitelist IPs: {len(service.whitelist_ips)}")
        assert service.alert_threshold > 0
        print("✅ Configuration loaded")

        # Test 4: Check initial statistics
        print("\n[4/7] Checking initial statistics...")
        stats = service.get_statistics()
        print(f"  Total predictions: {stats['total_predictions']}")
        print(f"  Alerts created: {stats['alerts_created']}")
        print(f"  Benign filtered: {stats['benign_filtered']}")
        print(f"  Duplicates blocked: {stats['duplicates_blocked']}")
        print(f"  Whitelist skipped: {stats['whitelist_skipped']}")
        assert stats['total_predictions'] == 0
        assert stats['alerts_created'] == 0
        print("✅ Initial statistics correct")

        # Test 5: Test is_running
        print("\n[5/7] Checking running status...")
        assert service.is_running() == False, "Service should not be running"
        print("✅ Running status correct")

        # Test 6: Singleton pattern
        print("\n[6/7] Testing singleton pattern...")
        service2 = get_detection_service()
        assert service is service2, "Should be same instance"
        print("✅ Singleton pattern working")

        # Test 7: Component integration check
        print("\n[7/7] Checking component integration...")
        # Model info
        model_info = service.model_loader.get_model_info()
        print(f"  Model type: {model_info['model_type']}")
        print(f"  Model accuracy: {model_info['accuracy']:.2%}")

        # Cache stats
        cache_stats = service.alert_cache.get_statistics()
        print(f"  Cache size: {cache_stats['cache_size']}")

        # WebSocket stats
        ws_stats = service.connection_manager.get_statistics()
        print(f"  Active connections: {ws_stats['active_connections']}")

        print("✅ All components integrated correctly")

        # Summary
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)

        print("\n📋 Summary:")
        print(f"  ✓ DetectionService: Initialized")
        print(f"  ✓ ModelLoader: Loaded ({model_info['model_type']})")
        print(f"  ✓ AlertCache: Ready")
        print(f"  ✓ ConnectionManager: Ready")
        print(f"  ✓ Configuration: Loaded (threshold={service.alert_threshold})")

        print("\n📝 Note: This test validates initialization and component integration.")
        print("   Full end-to-end test with CaptureService requires:")
        print("   - Phase 4: CaptureService running")
        print("   - Phase 6: FastAPI backend + database")

        print("\n🎉 Phase 5.4 COMPLETE - Detection Service is ready!")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_detection_service())
    sys.exit(0 if success else 1)