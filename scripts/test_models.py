"""
Test script to create tables and verify models
Run after copying all model files
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import init_database, get_database_info, SessionLocal, engine
from app.models import Alert, TrainingLog, Whitelist, Blacklist, SystemConfig
from datetime import datetime


def test_models_and_tables():
    """Test models and create tables"""
    print("=" * 60)
    print("TESTING MODELS & CREATING TABLES")
    print("=" * 60)

    # 1. Check models loaded
    print("\n1. Checking Models:")
    models = [Alert, TrainingLog, Whitelist, Blacklist, SystemConfig]
    for model in models:
        print(f"   ✓ {model.__name__} loaded")

    # 2. Create tables
    print("\n2. Creating Database Tables:")
    try:
        init_database()
        print("   ✓ All tables created successfully")
    except Exception as e:
        print(f"   ✗ Failed to create tables: {e}")
        return False

    # 3. Verify tables exist
    print("\n3. Verifying Tables in Database:")
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        expected_tables = ['alerts', 'training_logs', 'whitelist', 'blacklist', 'system_config']
        for table in expected_tables:
            if table in table_names:
                print(f"   ✓ Table '{table}' exists")
            else:
                print(f"   ✗ Table '{table}' NOT found")
                return False
    except Exception as e:
        print(f"   ✗ Failed to verify tables: {e}")
        return False

    # 4. Test insert & query
    print("\n4. Testing Insert & Query:")
    db = SessionLocal()
    try:
        # Insert test data
        test_alert = Alert(
            timestamp=datetime.now(),
            source_ip="192.168.1.100",
            dest_ip="10.0.0.1",
            attack_type="DDoS",
            confidence=0.98,
            severity="critical"
        )
        db.add(test_alert)
        db.commit()
        print("   ✓ Insert test alert successful")

        # Query test data
        alert = db.query(Alert).first()
        if alert:
            print(f"   ✓ Query successful: {alert}")
            print(f"      Alert dict: {alert.to_dict()}")
        else:
            print("   ✗ Query returned no results")
            return False

        # Clean up test data
        db.delete(alert)
        db.commit()
        print("   ✓ Delete test alert successful")

    except Exception as e:
        print(f"   ✗ Failed to test CRUD: {e}")
        db.rollback()
        return False
    finally:
        db.close()

    # 5. Database info
    print("\n5. Database Information:")
    db_info = get_database_info()
    for key, value in db_info.items():
        print(f"   {key}: {value}")

    print("\n" + "=" * 60)
    print("MODELS & TABLES TEST: PASSED ✓")
    print("=" * 60)
    print("\nDatabase ready for use!")
    print("Next steps:")
    print("1. Implement CRUD operations (Task 3.3)")
    print("2. Create init_db.py with default configs (Task 3.4)")

    return True


if __name__ == "__main__":
    success = test_models_and_tables()
    sys.exit(0 if success else 1)