#!/usr/bin/env python3
"""
Test script to debug model loading issues
"""

import sys
import os
sys.path.append('/home/ongera/projects/SOC-assistant')

def test_model_loading():
    """Test model loading step by step"""
    print("🔬 Testing Model Loading")
    print("=" * 40)
    
    try:
        # Check models directory
        print("1. Checking models directory...")
        model_dir = 'models'
        if os.path.exists(model_dir):
            files = os.listdir(model_dir)
            print(f"   ✅ Models directory exists with {len(files)} files")
            for f in files:
                if f.endswith('.pkl'):
                    print(f"      - {f}")
        else:
            print(f"   ❌ Models directory not found: {model_dir}")
            return False
        
        # Try to import the detector
        print("\n2. Importing SupervisedSOCDetector...")
        from src.models.supervised_trainer import SupervisedSOCDetector
        print("   ✅ Import successful")
        
        # Create detector instance
        print("\n3. Creating detector instance...")
        detector = SupervisedSOCDetector()
        print("   ✅ Detector instance created")
        
        # Try to load models
        print("\n4. Loading models...")
        try:
            detector.load_models(model_dir)
            print("   ✅ Models loaded successfully")
            
            # Test if detector has required methods
            print("\n5. Testing detector methods...")
            if hasattr(detector, 'predict_single'):
                print("   ✅ predict_single method exists")
            else:
                print("   ❌ predict_single method missing")
                
            if hasattr(detector, 'get_feature_template'):
                print("   ✅ get_feature_template method exists")
                template = detector.get_feature_template()
                print(f"   📋 Feature template has {len(template)} features")
            else:
                print("   ❌ get_feature_template method missing")
                
            return True
            
        except Exception as e:
            print(f"   ❌ Model loading failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_model_loading()
