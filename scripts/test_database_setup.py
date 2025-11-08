"""
Test script to verify database setup
Run this to test if database.py works correctly
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import (
    get_database_info,
    init_database,
    SessionLocal,
    engine
)


def test_database_connection():
    """Test database connection"""
    print("=" * 60)
    print("TESTING DATABASE SETUP")
    print("=" * 60)

    # 1. Check database info
    print("\n1. Database Information:")
    db_info = get_database_info()
    for key, value in db_info.items():
        print(f"   {key}: {value}")

    # 2. Test engine connection
    print("\n2. Testing Engine Connection:")
    try:
        connection = engine.connect()
        connection.close()
        print("   ✓ Engine connection successful")
    except Exception as e:
        print(f"   ✗ Engine connection failed: {e}")
        return False

    # 3. Test session creation
    print("\n3. Testing Session Creation:")
    try:
        db = SessionLocal()
        db.close()
        print("   ✓ Session creation successful")
    except Exception as e:
        print(f"   ✗ Session creation failed: {e}")
        return False

    # 4. Test database initialization (will create tables when models are ready)
    print("\n4. Database Initialization:")
    print("   ⚠ Skipping table creation (models not created yet)")
    print("   Will test after models are created in Task 3.2")

    print("\n" + "=" * 60)
    print("DATABASE SETUP TEST: PASSED ✓")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Create models in app/models/ (Task 3.2)")
    print("2. Run init_database() to create tables")
    print("3. Test CRUD operations")

    return True


if __name__ == "__main__":
    test_database_connection()