#!/usr/bin/env python3
"""
Test server startup debugging to see why model isn't loading
"""

import sys
import os
sys.path.append('/home/ongera/projects/SOC-assistant')

def test_server_debug():
    """Test server startup environment"""
    try:
        print("🔬 Testing Server Startup Environment")
        print("=" * 50)
        
        # Check current working directory
        print(f"1. Current working directory: {os.getcwd()}")
        
        # Check if models directory exists
        models_dir = 'models'
        print(f"2. Models directory exists: {os.path.exists(models_dir)}")
        
        if os.path.exists(models_dir):
            model_files = os.listdir(models_dir)
            pkl_files = [f for f in model_files if f.endswith('.pkl')]
            print(f"   📋 Model files ({len(pkl_files)}): {pkl_files}")
        else:
            print("   ❌ Models directory not found")
            
            # Check if we need to change directory
            alt_path = '/home/ongera/projects/SOC-assistant/models'
            print(f"   🔍 Checking alternative path: {alt_path}")
            print(f"   📁 Alternative exists: {os.path.exists(alt_path)}")
        
        # Test model loading directly
        print(f"\n3. Testing direct model loading...")
        from src.models.supervised_trainer import SupervisedSOCDetector
        
        detector = SupervisedSOCDetector()
        print(f"   📊 Detector created: {detector is not None}")
        
        try:
            detector.load_models('models')
            print(f"   ✅ Model loading successful: {detector.models is not None if hasattr(detector, 'models') else 'No models attr'}")
        except Exception as e:
            print(f"   ❌ Model loading failed: {e}")
            
            # Try with absolute path
            abs_models_path = '/home/ongera/projects/SOC-assistant/models'
            try:
                detector.load_models(abs_models_path)
                print(f"   ✅ Absolute path loading successful")
            except Exception as e2:
                print(f"   ❌ Absolute path loading failed: {e2}")
        
        # Test SOCDashboardAPI creation
        print(f"\n4. Testing SOCDashboardAPI creation...")
        from src.dashboard.server import SOCDashboardAPI
        
        api = SOCDashboardAPI()
        print(f"   📊 API created: {api is not None}")
        print(f"   🤖 Detector loaded: {api.detector is not None}")
        
        if not api.detector:
            print(f"   🔄 Attempting manual model loading...")
            try:
                api.load_models()
                print(f"   ✅ Manual loading result: {api.detector is not None}")
            except Exception as e:
                print(f"   ❌ Manual loading failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_server_debug()
