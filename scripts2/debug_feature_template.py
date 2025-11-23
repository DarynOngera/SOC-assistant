#!/usr/bin/env python3
"""
Debug the feature template loading issue
"""

import sys
import os
sys.path.append('/home/ongera/projects/SOC-assistant')

def debug_feature_template():
    """Debug why feature template is using fallback"""
    try:
        import joblib
        from src.models.supervised_trainer import SupervisedSOCDetector
        
        print("🔍 Debugging Feature Template Loading")
        print("=" * 50)
        
        # Check what's in the feature columns file
        feature_file = 'models/mininet_feature_columns.pkl'
        print(f"1. Checking {feature_file}...")
        
        if os.path.exists(feature_file):
            feature_columns = joblib.load(feature_file)
            print(f"   ✅ File exists")
            print(f"   📊 Type: {type(feature_columns)}")
            print(f"   🔢 Length: {len(feature_columns) if hasattr(feature_columns, '__len__') else 'N/A'}")
            
            if isinstance(feature_columns, (list, tuple)):
                print(f"   📋 First 10 features: {feature_columns[:10]}")
            else:
                print(f"   📋 Content: {feature_columns}")
        else:
            print(f"   ❌ File not found: {feature_file}")
        
        # Test detector creation and loading
        print(f"\n2. Testing detector loading...")
        detector = SupervisedSOCDetector()
        
        print(f"   📊 Before loading - feature_columns: {getattr(detector, 'feature_columns', 'Not set')}")
        
        detector.load_models('models')
        
        print(f"   📊 After loading - feature_columns: {getattr(detector, 'feature_columns', 'Not set')}")
        print(f"   📊 feature_columns type: {type(getattr(detector, 'feature_columns', None))}")
        
        # Test get_feature_template
        print(f"\n3. Testing get_feature_template...")
        template = detector.get_feature_template()
        
        print(f"   📊 Template keys: {list(template.keys())}")
        print(f"   🔢 Num features: {template.get('num_features', 'N/A')}")
        print(f"   ✅ Model ready: {template.get('model_ready', False)}")
        
        feature_columns = template.get('feature_columns', [])
        if feature_columns:
            print(f"   📋 Using model features ({len(feature_columns)}): {feature_columns[:10]}...")
        else:
            print(f"   ❌ Using fallback features")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    debug_feature_template()
