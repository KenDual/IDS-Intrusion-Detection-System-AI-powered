import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_model_loader():
    """Test ModelLoader functionality"""
    from app.detection import get_model_loader

    print("=" * 70)
    print("TESTING MODEL LOADER - Phase 5.1")
    print("=" * 70)

    try:
        # Test 1: Load model
        print("\n[1/6] Loading model...")
        loader = get_model_loader()
        print("✅ Model loaded successfully")

        # Test 2: Get model info
        print("\n[2/6] Getting model info...")
        info = loader.get_model_info()
        print(f"✅ Model info retrieved:")
        print(f"    Type: {info['model_type']}")
        print(f"    Features: {info['n_features']}")
        print(f"    Classes: {info['classes']}")
        print(f"    Accuracy: {info['accuracy']:.2%}")
        print(f"    Training time: {info['training_time']}")

        # Test 3: Validate feature count
        print("\n[3/6] Validating feature count...")
        assert info['n_features'] == 25, f"Expected 25 features, got {info['n_features']}"
        print("✅ Feature count correct: 25 features")

        # Test 4: Validate classes
        print("\n[4/6] Validating classes...")
        expected_classes = ["BENIGN", "DoS Hulk", "PortScan", "DDoS"]
        assert info['classes'] == expected_classes, f"Classes mismatch: {info['classes']}"
        print(f"✅ Classes correct: {expected_classes}")

        # Test 5: Single prediction (dummy data)
        print("\n[5/6] Testing single prediction...")
        dummy_features = np.random.rand(25) * 100  # Random features
        attack_type, confidence = loader.predict(dummy_features)
        print(f"✅ Prediction successful:")
        print(f"    Attack Type: {attack_type}")
        print(f"    Confidence: {confidence:.2%}")
        assert attack_type in expected_classes, f"Invalid attack type: {attack_type}"
        assert 0 <= confidence <= 1, f"Invalid confidence: {confidence}"

        # Test 6: Batch prediction
        print("\n[6/6] Testing batch prediction...")
        batch_features = [
            np.random.rand(25) * 100,
            np.random.rand(25) * 50,
            np.random.rand(25) * 150
        ]
        results = loader.predict_batch(batch_features)
        print(f"✅ Batch prediction successful ({len(results)} samples):")
        for i, (att, conf) in enumerate(results, 1):
            print(f"    Sample {i}: {att} (confidence: {conf:.2%})")
            assert att in expected_classes
            assert 0 <= conf <= 1

        # Test 7: Singleton pattern
        print("\n[7/7] Testing singleton pattern...")
        loader2 = get_model_loader()
        assert loader is loader2, "Singleton pattern failed"
        print("✅ Singleton pattern working correctly")

        # Summary
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\n📋 Summary:")
        print(f"  ✓ Model loaded: {info['model_type']}")
        print(f"  ✓ Features: {info['n_features']}")
        print(f"  ✓ Classes: {len(info['classes'])}")
        print(f"  ✓ Accuracy: {info['accuracy']:.2%}")
        print(f"  ✓ Single prediction: Working")
        print(f"  ✓ Batch prediction: Working")
        print(f"  ✓ Singleton: Working")
        print("\n🎉 Phase 5.1 COMPLETE - Model Loader is ready!")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_model_loader()
    sys.exit(0 if success else 1)