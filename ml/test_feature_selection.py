import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import xgboost as xgb
from app.config import USE_GPU, XGBOOST_PARAMS, CLASS_WEIGHTS


def test_xgboost_missing_class():
    """Test XGBoost with missing class labels"""

    print("Testing XGBoost with missing class labels...")
    print("-" * 40)

    # Create sample data with missing class 1
    np.random.seed(42)
    X = np.random.randn(100, 10)
    y = np.array([0] * 40 + [2] * 30 + [3] * 30)  # Missing class 1

    print(f"Original classes: {np.unique(y)}")

    # Map labels to be continuous
    unique_classes = np.unique(y)
    label_map = {old: new for new, old in enumerate(sorted(unique_classes))}
    y_mapped = np.array([label_map[label] for label in y])

    print(f"Label mapping: {label_map}")
    print(f"Mapped classes: {np.unique(y_mapped)}")

    # Adjust XGBoost parameters
    params = XGBOOST_PARAMS.copy()
    params['num_class'] = len(unique_classes)
    params['n_estimators'] = 10  # Quick test

    # Create sample weights
    sample_weights = np.ones(len(y_mapped))
    for orig_label, new_label in label_map.items():
        mask = y_mapped == new_label
        sample_weights[mask] = CLASS_WEIGHTS.get(orig_label, 1.0)

    print(f"Using GPU: {USE_GPU}")

    # Train XGBoost
    try:
        model = xgb.XGBClassifier(**params)
        model.fit(X, y_mapped, sample_weight=sample_weights)
        print("✅ XGBoost training successful with mapped labels!")

        # Test prediction
        pred = model.predict(X[:5])
        print(f"Sample predictions (mapped): {pred}")

        # Reverse mapping for interpretation
        reverse_map = {v: k for k, v in label_map.items()}
        pred_original = [reverse_map[p] for p in pred]
        print(f"Sample predictions (original): {pred_original}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("XGBOOST CLASS MAPPING TEST")
    print("=" * 60)

    success = test_xgboost_missing_class()

    if success:
        print("\n✅ Test passed! XGBoost can handle missing classes.")
        print("\nYou can now run feature selection:")
        print("  python ml/feature_selection.py")
    else:
        print("\n❌ Test failed. Check error messages above.")