import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import init_database, get_database_info, SessionLocal
from app.database.crud import set_config, get_all_configs
from app.models import Alert, TrainingLog, Whitelist, Blacklist, SystemConfig


def create_tables():
    """Create all database tables"""
    print("=" * 60)
    print("INITIALIZING DATABASE")
    print("=" * 60)

    print("\n1. Creating database tables...")
    try:
        init_database()
        print("   ✓ All tables created successfully")
        return True
    except Exception as e:
        print(f"   ✗ Failed to create tables: {e}")
        return False


def insert_default_configs():
    """Insert default system configurations"""
    print("\n2. Inserting default system configurations...")

    db = SessionLocal()

    default_configs = {
        # Monitoring settings
        "monitoring_enabled": "false",
        "monitoring_interface": "eth0",

        # Alert settings
        "alert_threshold": "0.95",
        "max_alerts_per_page": "50",
        "alert_retention_days": "0",  # 0 = unlimited

        # Model settings
        "model_version": "v1.0.0",
        "model_path": "ml/models/xgboost_model.pkl",

        # Performance settings
        "batch_prediction_size": "100",
        "prediction_timeout_seconds": "5",

        # WebSocket settings
        "websocket_enabled": "true",
        "websocket_max_connections": "50",

        # Security settings
        "auto_block_enabled": "false",
        "auto_block_threshold": "10",  # Number of critical alerts before auto-block
        "auto_block_duration_hours": "24",

        # System settings
        "system_name": "IDS - AI-Powered",
        "system_version": "1.0.0",
        "admin_email": "admin@example.com",
    }

    try:
        inserted_count = 0
        updated_count = 0

        for key, value in default_configs.items():
            # Check if config already exists
            existing = db.query(SystemConfig).filter(SystemConfig.key == key).first()

            if existing:
                print(f"   ⚠ Config '{key}' already exists, skipping...")
                updated_count += 1
            else:
                set_config(db, key, value)
                print(f"   ✓ Inserted config: {key} = {value}")
                inserted_count += 1

        print(f"\n   Summary: {inserted_count} configs inserted, {updated_count} already existed")

        # Display all configs
        print("\n   Current system configurations:")
        all_configs = get_all_configs(db)
        for config in all_configs:
            print(f"      {config.key:30s} = {config.value}")

        return True

    except Exception as e:
        print(f"   ✗ Failed to insert configs: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def verify_initialization():
    """Verify database initialization"""
    print("\n3. Verifying database initialization...")

    try:
        from sqlalchemy import inspect
        from app.database import engine

        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        expected_tables = ['alerts', 'training_logs', 'whitelist', 'blacklist', 'system_config']

        all_exist = True
        for table in expected_tables:
            if table in table_names:
                # Get column count
                columns = inspector.get_columns(table)
                print(f"   ✓ Table '{table}' exists ({len(columns)} columns)")
            else:
                print(f"   ✗ Table '{table}' NOT found")
                all_exist = False

        if not all_exist:
            return False

        # Check default configs count
        db = SessionLocal()
        config_count = db.query(SystemConfig).count()
        db.close()

        print(f"   ✓ System configs: {config_count} entries")

        return True

    except Exception as e:
        print(f"   ✗ Verification failed: {e}")
        return False


def display_database_info():
    """Display database information"""
    print("\n4. Database information:")

    db_info = get_database_info()
    for key, value in db_info.items():
        print(f"   {key:20s}: {value}")


def main():
    """Main initialization function"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "IDS DATABASE INITIALIZATION" + " " * 21 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    # Step 1: Create tables
    if not create_tables():
        print("\n✗ Database initialization FAILED at table creation")
        return 1

    # Step 2: Insert default configs
    if not insert_default_configs():
        print("\n✗ Database initialization FAILED at config insertion")
        return 1

    # Step 3: Verify
    if not verify_initialization():
        print("\n✗ Database initialization FAILED at verification")
        return 1

    # Step 4: Display info
    display_database_info()

    # Success
    print("\n" + "=" * 60)
    print("✓ DATABASE INITIALIZATION COMPLETE")
    print("=" * 60)
    print("\nDatabase is ready for use!")
    print("\nNext steps:")
    print("  1. Test CRUD operations: python scripts/test_crud.py")
    print("  2. Start FastAPI application: uvicorn app.main:app --reload")
    print("  3. Begin packet capture and detection")
    print()

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)