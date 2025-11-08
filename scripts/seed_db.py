"""
Database Seeding Script
Inserts sample data for testing purposes
WARNING: Use only in development environment
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.database.crud import (
    create_alert,
    add_to_whitelist,
    add_to_blacklist,
    create_training_log
)


def seed_alerts(db, count=50):
    """Insert sample alerts"""
    print(f"\n1. Seeding {count} sample alerts...")

    attack_types = ["DoS Hulk", "PortScan", "DDoS"]

    # Sample IP addresses
    attacker_ips = [
        "192.168.1.100", "192.168.1.101", "192.168.1.102",
        "10.0.0.50", "10.0.0.51", "10.0.0.52",
        "172.16.0.100", "172.16.0.101"
    ]

    victim_ips = [
        "10.0.0.1", "10.0.0.2", "10.0.0.3",
        "192.168.100.10", "192.168.100.11"
    ]

    inserted = 0

    try:
        for i in range(count):
            # Random timestamp within last 7 days
            hours_ago = random.randint(0, 168)  # 7 days = 168 hours
            timestamp = datetime.now() - timedelta(hours=hours_ago)

            # Random attack parameters
            attack_type = random.choice(attack_types)
            source_ip = random.choice(attacker_ips)
            dest_ip = random.choice(victim_ips)

            # Confidence: 70-99%
            confidence = random.uniform(0.70, 0.99)

            # Severity based on confidence
            severity = "critical" if confidence >= 0.95 else "low"

            alert = create_alert(
                db=db,
                timestamp=timestamp,
                source_ip=source_ip,
                dest_ip=dest_ip,
                attack_type=attack_type,
                confidence=confidence,
                severity=severity
            )

            inserted += 1

            if (i + 1) % 10 == 0:
                print(f"   Inserted {i + 1}/{count} alerts...")

        print(f"   ✓ Successfully inserted {inserted} alerts")
        return True

    except Exception as e:
        print(f"   ✗ Failed to seed alerts: {e}")
        db.rollback()
        return False


def seed_whitelist(db):
    """Insert sample whitelist entries"""
    print("\n2. Seeding sample whitelist...")

    whitelist_entries = [
        ("10.0.0.100", "Internal web server"),
        ("10.0.0.101", "Database server"),
        ("10.0.0.200", "Admin workstation"),
        ("192.168.100.1", "Network gateway"),
        ("172.16.0.1", "VPN gateway")
    ]

    inserted = 0

    try:
        for ip, description in whitelist_entries:
            result = add_to_whitelist(db, ip, description)
            if result:
                print(f"   ✓ Added to whitelist: {ip} - {description}")
                inserted += 1
            else:
                print(f"   ⚠ Already exists: {ip}")

        print(f"   Summary: {inserted} whitelist entries added")
        return True

    except Exception as e:
        print(f"   ✗ Failed to seed whitelist: {e}")
        db.rollback()
        return False


def seed_blacklist(db):
    """Insert sample blacklist entries"""
    print("\n3. Seeding sample blacklist...")

    blacklist_entries = [
        ("192.168.1.100", "Known DDoS attacker"),
        ("192.168.1.101", "Port scanner detected"),
        ("10.0.0.50", "Brute force attempts"),
        ("172.16.0.100", "Malicious traffic source")
    ]

    inserted = 0

    try:
        for ip, description in blacklist_entries:
            result = add_to_blacklist(db, ip, description)
            if result:
                print(f"   ✓ Added to blacklist: {ip} - {description}")
                inserted += 1
            else:
                print(f"   ⚠ Already exists: {ip}")

        print(f"   Summary: {inserted} blacklist entries added")
        return True

    except Exception as e:
        print(f"   ✗ Failed to seed blacklist: {e}")
        db.rollback()
        return False


def seed_training_logs(db):
    """Insert sample training logs"""
    print("\n4. Seeding sample training logs...")

    training_logs = [
        ("v1.0.0", 0.9995, 0.9995, "Initial model training with CICIDS2017 dataset"),
        ("v1.0.1", 0.9996, 0.9996, "Improved hyperparameters"),
        ("v1.1.0", 0.9997, 0.9996, "Added new features"),
    ]

    inserted = 0

    try:
        for version, accuracy, f1_score, notes in training_logs:
            log = create_training_log(
                db=db,
                model_version=version,
                accuracy=accuracy,
                f1_score=f1_score,
                notes=notes
            )
            print(f"   ✓ Added training log: {version} (Acc: {accuracy:.4f})")
            inserted += 1

        print(f"   Summary: {inserted} training logs added")
        return True

    except Exception as e:
        print(f"   ✗ Failed to seed training logs: {e}")
        db.rollback()
        return False


def display_statistics(db):
    """Display seeded data statistics"""
    print("\n5. Database statistics:")

    from app.models import Alert, Whitelist, Blacklist, TrainingLog, SystemConfig

    try:
        alert_count = db.query(Alert).count()
        whitelist_count = db.query(Whitelist).count()
        blacklist_count = db.query(Blacklist).count()
        training_log_count = db.query(TrainingLog).count()
        config_count = db.query(SystemConfig).count()

        print(f"   Alerts:        {alert_count:5d}")
        print(f"   Whitelist:     {whitelist_count:5d}")
        print(f"   Blacklist:     {blacklist_count:5d}")
        print(f"   Training Logs: {training_log_count:5d}")
        print(f"   System Config: {config_count:5d}")

        # Alert breakdown
        from app.database.crud import count_alerts

        total = count_alerts(db)
        critical = count_alerts(db, severity="critical")

        dos_hulk = count_alerts(db, attack_type="DoS Hulk")
        portscan = count_alerts(db, attack_type="PortScan")
        ddos = count_alerts(db, attack_type="DDoS")

        print(f"\n   Alert breakdown:")
        print(f"      Total:    {total}")
        print(f"      Critical: {critical}")
        print(f"      Low:      {total - critical}")
        print(f"\n   By attack type:")
        print(f"      DoS Hulk:  {dos_hulk}")
        print(f"      PortScan:  {portscan}")
        print(f"      DDoS:      {ddos}")

    except Exception as e:
        print(f"   ✗ Failed to get statistics: {e}")


def main():
    """Main seeding function"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "DATABASE SEEDING" + " " * 27 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    print("⚠ WARNING: This will insert sample data into the database")
    print("⚠ Use only in development environment")
    print()

    # Confirmation
    response = input("Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Seeding cancelled.")
        return 0

    print("\n" + "=" * 60)
    print("SEEDING DATABASE")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Seed data
        success = True

        success = seed_alerts(db, count=50) and success
        success = seed_whitelist(db) and success
        success = seed_blacklist(db) and success
        success = seed_training_logs(db) and success

        if not success:
            print("\n✗ Seeding completed with some errors")
            return 1

        # Display statistics
        display_statistics(db)

        # Success
        print("\n" + "=" * 60)
        print("✓ DATABASE SEEDING COMPLETE")
        print("=" * 60)
        print("\nSample data has been inserted successfully!")
        print("You can now test the application with realistic data.")
        print()

        return 0

    except Exception as e:
        print(f"\n✗ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)