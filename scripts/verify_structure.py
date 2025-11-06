# verify_structure.py
import os
from pathlib import Path


def check_structure():
    """Verify project structure"""

    required_dirs = [
        'app',
        'app/models',
        'app/routes',
        'app/services',
        'app/database',
        'app/templates',
        'app/static',
        'ml',
        'ml/models',
        'scripts',
        'data',
        'logs'
    ]

    required_files = [
        'app/__init__.py',
        'app/config.py',
        'ml/__init__.py',
        'ml/explore_data.py',
        'ml/prepare_clean_data.py',
        'requirements.txt',
        '.env',
        '.gitignore',
        'README.md'
    ]

    print("=" * 60)
    print("PROJECT STRUCTURE VERIFICATION")
    print("=" * 60)

    print("\nChecking directories...")
    all_dirs_ok = True
    for dir_path in required_dirs:
        exists = os.path.isdir(dir_path)
        status = "✓" if exists else "✗"
        print(f"  {status} {dir_path}")
        if not exists:
            all_dirs_ok = False

    print("\nChecking files...")
    all_files_ok = True
    for file_path in required_files:
        exists = os.path.isfile(file_path)
        status = "✓" if exists else "✗"
        print(f"  {status} {file_path}")
        if not exists:
            all_files_ok = False

    print("\n" + "=" * 60)
    if all_dirs_ok and all_files_ok:
        print("✓ PROJECT STRUCTURE COMPLETE")
    else:
        print("✗ SOME ITEMS MISSING")
        print("\nRun setup commands to create missing items.")
    print("=" * 60)


if __name__ == "__main__":
    check_structure()