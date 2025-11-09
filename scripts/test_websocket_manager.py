"""
Test script for ConnectionManager (Phase 5.3)

Tests:
1. Create ConnectionManager (singleton)
2. Start broadcast worker
3. Push alerts to queue
4. Worker processes alerts
5. Get statistics
6. Stop worker
7. Test singleton pattern

Note: Full WebSocket testing requires FastAPI server (Phase 6)

Run: python scripts/test_websocket_manager.py
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


async def test_connection_manager():
    """Test ConnectionManager functionality"""
    from app.detection import get_connection_manager

    print("=" * 70)
    print("TESTING CONNECTION MANAGER - Phase 5.3")
    print("=" * 70)

    try:
        # Test 1: Create manager
        print("\n[1/8] Creating ConnectionManager...")
        manager = get_connection_manager()
        print("✅ ConnectionManager created")

        # Test 2: Check initial state
        print("\n[2/8] Checking initial state...")
        assert manager.is_running() == False, "Worker should not be running"
        stats = manager.get_statistics()
        print(f"  Active connections: {stats['active_connections']}")
        print(f"  Queue size: {stats['queue_size']}")
        assert stats['active_connections'] == 0
        assert stats['queue_size'] == 0
        print("✅ Initial state correct")

        # Test 3: Start worker
        print("\n[3/8] Starting broadcast worker...")
        await manager.start_worker()
        assert manager.is_running() == True, "Worker should be running"
        print("✅ Worker started successfully")

        # Test 4: Push alerts to queue
        print("\n[4/8] Pushing alerts to queue...")
        test_alerts = [
            {
                "id": 1,
                "source_ip": "10.0.0.50",
                "dest_ip": "192.168.1.1",
                "attack_type": "DDoS",
                "confidence": 0.98,
                "severity": "critical"
            },
            {
                "id": 2,
                "source_ip": "10.0.0.51",
                "dest_ip": "192.168.1.1",
                "attack_type": "PortScan",
                "confidence": 0.96,
                "severity": "critical"
            },
            {
                "id": 3,
                "source_ip": "10.0.0.52",
                "dest_ip": "192.168.1.1",
                "attack_type": "DoS Hulk",
                "confidence": 0.99,
                "severity": "critical"
            }
        ]

        for alert in test_alerts:
            await manager.push_alert_to_queue(alert)

        print(f"  Pushed {len(test_alerts)} alerts")
        print("✅ Alerts pushed to queue")

        # Test 5: Wait for worker to process
        print("\n[5/8] Waiting for worker to process (3 seconds)...")
        await asyncio.sleep(3)

        stats = manager.get_statistics()
        print(f"  Queue size after processing: {stats['queue_size']}")
        assert stats['queue_size'] == 0, "Queue should be empty after processing"
        print("✅ Worker processed all alerts")

        # Test 6: Check statistics
        print("\n[6/8] Checking statistics...")
        stats = manager.get_statistics()
        print(f"  Active connections: {stats['active_connections']}")
        print(f"  Total broadcasts: {stats['total_broadcasts']}")
        print(f"  Queue size: {stats['queue_size']}")
        print("✅ Statistics tracking working")

        # Test 7: Stop worker
        print("\n[7/8] Stopping worker...")
        await manager.stop_worker()
        assert manager.is_running() == False, "Worker should be stopped"
        print("✅ Worker stopped successfully")

        # Test 8: Singleton pattern
        print("\n[8/8] Testing singleton pattern...")
        manager2 = get_connection_manager()
        assert manager is manager2, "Should be same instance"
        print("✅ Singleton pattern working")

        # Summary
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)

        final_stats = manager.get_statistics()
        print("\n📋 Final Statistics:")
        print(f"  ✓ Active connections: {final_stats['active_connections']}")
        print(f"  ✓ Total connections: {final_stats['total_connections']}")
        print(f"  ✓ Total broadcasts: {final_stats['total_broadcasts']}")
        print(f"  ✓ Failed broadcasts: {final_stats['failed_broadcasts']}")
        print(f"  ✓ Queue size: {final_stats['queue_size']}")

        print("\n📝 Note: This test validates queue & worker functionality.")
        print("   Full WebSocket testing requires FastAPI server (Phase 6).")

        print("\n🎉 Phase 5.3 COMPLETE - WebSocket Manager is ready!")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_connection_manager())
    sys.exit(0 if success else 1)