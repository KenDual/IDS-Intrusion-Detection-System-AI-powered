"""
Quick run script for model training
"""
import sys
import os

print("="*60)
print("IDS MODEL TRAINING")
print("="*60)
print("\nTraining Options:")
print("1. Full training with hyperparameter tuning (slower, better)")
print("2. Quick training without tuning (faster)")
print("3. CPU-only training")
print("\nChoose option (1/2/3) [default: 2]: ", end="")

choice = input().strip() or "2"

if choice == "1":
    print("\nStarting full training with hyperparameter tuning...")
    print("This may take 15-30 minutes depending on your hardware.\n")
    os.system("python ml/train.py")
elif choice == "2":
    print("\nStarting quick training without tuning...")
    print("This should take 5-10 minutes.\n")
    os.system("python ml/train.py --skip-tuning")
elif choice == "3":
    print("\nStarting CPU-only training...")
    print("This will be slower than GPU training.\n")
    os.system("python ml/train.py --gpu cpu --skip-tuning")
else:
    print("Invalid choice. Exiting.")
    sys.exit(1)