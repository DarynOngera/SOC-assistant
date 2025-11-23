#!/usr/bin/env python3
"""
Test that the monitoring system now uses model features instead of fallback
"""

import sys
import os
import time
sys.path.append('/home/ongera/projects/SOC-assistant')

def test_monitoring_fix():
    """Test that monitoring uses model features"""
    try:
        from src.dashboard.server import SOCDashboardAPI
        
        print("🔬 Testing Monitoring System Fix")
        print("=" * 50)
        
        # Create API instance
        print("1. Creating SOCDashboardAPI...")
        api = SOCDashboardAPI()
        print(f"   ✅ Detector loaded: {api.detector is not None}")
        
        # Test the monitoring data generation directly
        print("\n2. Testing monitoring data generation...")
        
        # This should now use model features
        mock_data = api.generate_mock_data(5)
        print(f"   ✅ Generated {len(mock_data)} records")
        
        if mock_data:
            sample = mock_data[0]
            features = list(sample.keys())
            print(f"   📋 Sample features ({len(features)}): {features[:8]}...")
            
            # Check if it's using model features
            if 'index' in features and 'packet_count' in features:
                print("   ✅ SUCCESS: Using model features!")
            else:
                print("   ❌ ISSUE: Still using fallback features")
                
        # Test model compatibility data generation directly
        print("\n3. Testing model-compatible data generation...")
        model_data = api._generate_model_compatible_data(3)
        print(f"   ✅ Generated {len(model_data)} model-compatible records")
        
        if model_data:
            sample = model_data[0]
            features = list(sample.keys())
            print(f"   📋 Model features ({len(features)}): {features[:8]}...")
            
        # Test monitoring start (briefly)
        print("\n4. Testing monitoring system...")
        print("   🔄 Starting monitoring for 3 seconds...")
        
        api.start_monitoring()
        time.sleep(3)
        api.stop_monitoring()
        
        print("   ✅ Monitoring test completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_monitoring_fix()
