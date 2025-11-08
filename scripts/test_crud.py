"""
Test script for CRUD operations
Tests all database CRUD functions
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, init_database
from app.database.crud import (
    # Alert operations
    create_alert, get_alert_by_id, get_alerts, get_recent_alerts,
    get_alerts_by_ip, delete_alert, count_alerts, get_alert_statistics,
    # Whitelist operations
    add_to_whitelist, remove_from_whitelist, is_whitelisted, get_all_whitelist,
    # Blacklist operations
    add_to_blacklist, remove_from_blacklist, is_blacklisted, get_all_blacklist,
    # TrainingLog operations
    create_training_log, get_latest_training_log, get_all_training_logs,
    # SystemConfig operations
    set_config, get_config, get_all_configs, delete_config
)


def test_alert_crud():
    """Test Alert CRUD operations"""
    print("\n" + "=" * 60)
    print("TESTING ALERT CRUD OPERATIONS")
    print("=" * 60)

    db = SessionLocal()

    try:
        # 1. Create alerts
        print("\n1. Creating test alerts...")
        alert1 = create_alert(
            db=db,
            timestamp=datetime.now(),
            source_ip="192.168.1.100",
            dest_ip="10.0.0.1",
            attack_type="DDoS",
            confidence=0.98,
            severity="critical"
        )
        print(f"   ✓ Created alert 1: {alert1}")

        alert2 = create_alert(
            db=db,
            timestamp=datetime.now() - timedelta(hours=1),
            source_ip="192.168.1.101",
            dest_ip="10.0.0.2",
            attack_type="PortScan",
            confidence=0.92,
            severity="low"
        )
        print(f"   ✓ Created alert 2: {alert2}")

        alert3 = create_alert(
            db=db,
            timestamp=datetime.now() - timedelta(hours=2),
            source_ip="192.168.1.100",
            dest_ip="10.0.0.3",
            attack_type="DoS Hulk",
            confidence=0.96,
            severity="critical"
        )
        print(f"   ✓ Created alert 3: {alert3}")

        # 2. Get alert by ID
        print("\n2. Testing get_alert_by_id...")
        alert = get_alert_by_id(db, alert1.id)
        if alert:
            print(f"   ✓ Found alert: {alert}")
        else:
            print("   ✗ Failed to get alert by ID")

        # 3. Get recent alerts
        print("\n3. Testing get_recent_alerts...")
        recent = get_recent_alerts(db, limit=2)
        print(f"   ✓ Found {len(recent)} recent alerts")
        for a in recent:
            print(f"      - {a}")

        # 4. Get alerts with filters
        print("\n4. Testing get_alerts with filters...")
        critical_alerts = get_alerts(db, severity="critical")
        print(f"   ✓ Found {len(critical_alerts)} critical alerts")

        ddos_alerts = get_alerts(db, attack_type="DDoS")
        print(f"   ✓ Found {len(ddos_alerts)} DDoS alerts")

        # 5. Get alerts by IP
        print("\n5. Testing get_alerts_by_ip...")
        ip_alerts = get_alerts_by_ip(db, "192.168.1.100")
        print(f"   ✓ Found {len(ip_alerts)} alerts from 192.168.1.100")

        # 6. Count alerts
        print("\n6. Testing count_alerts...")
        total = count_alerts(db)
        print(f"   ✓ Total alerts: {total}")

        # 7. Get statistics
        print("\n7. Testing get_alert_statistics...")
        stats = get_alert_statistics(db, hours=24)
        print(f"   ✓ Statistics: {stats}")

        # 8. Delete alert
        print("\n8. Testing delete_alert...")
        deleted = delete_alert(db, alert2.id)
        if deleted:
            print(f"   ✓ Deleted alert {alert2.id}")
        else:
            print("   ✗ Failed to delete alert")

        print("\n✓ Alert CRUD tests PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Alert CRUD tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_whitelist_crud():
    """Test Whitelist CRUD operations"""
    print("\n" + "=" * 60)
    print("TESTING WHITELIST CRUD OPERATIONS")
    print("=" * 60)

    db = SessionLocal()

    try:
        # 1. Add to whitelist
        print("\n1. Testing add_to_whitelist...")
        wl1 = add_to_whitelist(db, "10.0.0.100", "Internal server")
        if wl1:
            print(f"   ✓ Added to whitelist: {wl1}")
        else:
            print("   ✗ Failed to add to whitelist")

        wl2 = add_to_whitelist(db, "10.0.0.101", "Admin workstation")
        print(f"   ✓ Added to whitelist: {wl2}")

        # 2. Check if whitelisted
        print("\n2. Testing is_whitelisted...")
        if is_whitelisted(db, "10.0.0.100"):
            print("   ✓ 10.0.0.100 is whitelisted")
        else:
            print("   ✗ Failed to check whitelist")

        if not is_whitelisted(db, "192.168.1.1"):
            print("   ✓ 192.168.1.1 is not whitelisted (correct)")

        # 3. Get all whitelist
        print("\n3. Testing get_all_whitelist...")
        all_wl = get_all_whitelist(db)
        print(f"   ✓ Found {len(all_wl)} whitelisted IPs")
        for wl in all_wl:
            print(f"      - {wl}")

        # 4. Remove from whitelist
        print("\n4. Testing remove_from_whitelist...")
        removed = remove_from_whitelist(db, "10.0.0.101")
        if removed:
            print("   ✓ Removed 10.0.0.101 from whitelist")
        else:
            print("   ✗ Failed to remove from whitelist")

        print("\n✓ Whitelist CRUD tests PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Whitelist CRUD tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_blacklist_crud():
    """Test Blacklist CRUD operations"""
    print("\n" + "=" * 60)
    print("TESTING BLACKLIST CRUD OPERATIONS")
    print("=" * 60)

    db = SessionLocal()

    try:
        # 1. Add to blacklist
        print("\n1. Testing add_to_blacklist...")
        bl1 = add_to_blacklist(db, "192.168.100.50", "Known attacker")
        if bl1:
            print(f"   ✓ Added to blacklist: {bl1}")
        else:
            print("   ✗ Failed to add to blacklist")

        bl2 = add_to_blacklist(db, "192.168.100.51", "Malicious scanner")
        print(f"   ✓ Added to blacklist: {bl2}")

        # 2. Check if blacklisted
        print("\n2. Testing is_blacklisted...")
        if is_blacklisted(db, "192.168.100.50"):
            print("   ✓ 192.168.100.50 is blacklisted")
        else:
            print("   ✗ Failed to check blacklist")

        if not is_blacklisted(db, "10.0.0.1"):
            print("   ✓ 10.0.0.1 is not blacklisted (correct)")

        # 3. Get all blacklist
        print("\n3. Testing get_all_blacklist...")
        all_bl = get_all_blacklist(db)
        print(f"   ✓ Found {len(all_bl)} blacklisted IPs")
        for bl in all_bl:
            print(f"      - {bl}")

        # 4. Remove from blacklist
        print("\n4. Testing remove_from_blacklist...")
        removed = remove_from_blacklist(db, "192.168.100.51")
        if removed:
            print("   ✓ Removed 192.168.100.51 from blacklist")
        else:
            print("   ✗ Failed to remove from blacklist")

        print("\n✓ Blacklist CRUD tests PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Blacklist CRUD tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_training_log_crud():
    """Test TrainingLog CRUD operations"""
    print("\n" + "=" * 60)
    print("TESTING TRAINING LOG CRUD OPERATIONS")
    print("=" * 60)

    db = SessionLocal()

    try:
        # 1. Create training logs
        print("\n1. Testing create_training_log...")
        log1 = create_training_log(
            db=db,
            model_version="v1.0.0",
            accuracy=0.9995,
            f1_score=0.9995,
            notes="Initial model training"
        )
        print(f"   ✓ Created log 1: {log1}")

        log2 = create_training_log(
            db=db,
            model_version="v1.1.0",
            accuracy=0.9997,
            f1_score=0.9996,
            notes="Improved hyperparameters"
        )
        print(f"   ✓ Created log 2: {log2}")

        # 2. Get latest log
        print("\n2. Testing get_latest_training_log...")
        latest = get_latest_training_log(db)
        if latest:
            print(f"   ✓ Latest log: {latest}")
        else:
            print("   ✗ Failed to get latest log")

        # 3. Get all logs
        print("\n3. Testing get_all_training_logs...")
        all_logs = get_all_training_logs(db)
        print(f"   ✓ Found {len(all_logs)} training logs")
        for log in all_logs:
            print(f"      - {log}")

        print("\n✓ TrainingLog CRUD tests PASSED")
        return True

    except Exception as e:
        print(f"\n✗ TrainingLog CRUD tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_system_config_crud():
    """Test SystemConfig CRUD operations"""
    print("\n" + "=" * 60)
    print("TESTING SYSTEM CONFIG CRUD OPERATIONS")
    print("=" * 60)

    db = SessionLocal()

    try:
        # 1. Set config
        print("\n1. Testing set_config...")
        config1 = set_config(db, "monitoring_enabled", "true")
        print(f"   ✓ Set config: {config1}")

        config2 = set_config(db, "alert_threshold", "0.95")
        print(f"   ✓ Set config: {config2}")

        # 2. Get config
        print("\n2. Testing get_config...")
        value = get_config(db, "monitoring_enabled")
        if value == "true":
            print(f"   ✓ Got config value: {value}")
        else:
            print(f"   ✗ Wrong config value: {value}")

        default_value = get_config(db, "nonexistent_key", "default")
        if default_value == "default":
            print(f"   ✓ Default value works: {default_value}")

        # 3. Update config
        print("\n3. Testing update config...")
        updated = set_config(db, "monitoring_enabled", "false")
        new_value = get_config(db, "monitoring_enabled")
        if new_value == "false":
            print(f"   ✓ Config updated successfully: {new_value}")
        else:
            print(f"   ✗ Failed to update config")

        # 4. Get all configs
        print("\n4. Testing get_all_configs...")
        all_configs = get_all_configs(db)
        print(f"   ✓ Found {len(all_configs)} configs")
        for cfg in all_configs:
            print(f"      - {cfg.key}: {cfg.value}")

        # 5. Delete config
        print("\n5. Testing delete_config...")
        deleted = delete_config(db, "alert_threshold")
        if deleted:
            print("   ✓ Deleted config 'alert_threshold'")
        else:
            print("   ✗ Failed to delete config")

        print("\n✓ SystemConfig CRUD tests PASSED")
        return True

    except Exception as e:
        print(f"\n✗ SystemConfig CRUD tests FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def run_all_tests():
    """Run all CRUD tests"""
    print("=" * 60)
    print("RUNNING ALL CRUD TESTS")
    print("=" * 60)

    # Initialize database first
    print("\nInitializing database...")
    init_database()

    results = []

    # Run tests
    results.append(("Alert CRUD", test_alert_crud()))
    results.append(("Whitelist CRUD", test_whitelist_crud()))
    results.append(("Blacklist CRUD", test_blacklist_crud()))
    results.append(("TrainingLog CRUD", test_training_log_crud()))
    results.append(("SystemConfig CRUD", test_system_config_crud()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name:30s} {status}")

    print("\n" + "=" * 60)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Database CRUD operations working correctly.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Check errors above.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)