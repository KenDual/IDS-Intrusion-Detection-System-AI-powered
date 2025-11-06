# test_setup.py
import sys


def check_imports():
    packages = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('xgboost', 'XGBoost'),
        ('sklearn', 'Scikit-learn'),
        ('pandas', 'Pandas'),
        ('numpy', 'NumPy'),
        ('scapy.all', 'Scapy'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('websockets', 'WebSockets'),
    ]

    print("Checking installed packages...\n")
    all_ok = True

    for module, name in packages:
        try:
            __import__(module)
            print(f"✓ {name:<15} OK")
        except ImportError:
            print(f"✗ {name:<15} FAILED")
            all_ok = False

    print("\n" + "=" * 40)
    if all_ok:
        print("✓ All packages installed successfully!")
        print(f"Python version: {sys.version}")
    else:
        print("✗ Some packages failed to install")
        print("Run: pip install -r requirements.txt")

    return all_ok


if __name__ == "__main__":
    check_imports()