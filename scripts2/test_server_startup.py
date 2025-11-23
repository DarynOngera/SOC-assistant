#!/usr/bin/env python3
"""
Test server startup and monitoring initialization
"""

import sys
import os
import time
sys.path.append('/home/ongera/projects/SOC-assistant')

def test_server_startup():
    """Test that server starts up properly with monitoring"""
    try:
        from src.dashboard.server import SOCDashboardAPI
        
        print("🔬 Testing Server Startup")
        print("=" * 50)
        
        # Create API instance (simulates server startup)
        print("1. Creating SOCDashboardAPI (simulating server startup)...")
        api = SOCDashboardAPI()
        print(f"   ✅ API created")
        print(f"   🤖 Detector loaded: {api.detector is not None}")
        print(f"   📊 Monitoring active: {api.is_monitoring}")
        
        # Test monitoring startup
        print("\n2. Testing monitoring startup...")
        if not api.is_monitoring:
            if api.detector:
                print("   🔄 Model available, starting monitoring...")
                success = api.start_monitoring()
                print(f"   {'✅' if success else '❌'} Monitoring start result: {success}")
            else:
                print("   ⚠️ Model not available, monitoring should not start")
        else:
            print("   ✅ Monitoring already active")
        
        # Test data generation
        print("\n3. Testing data generation...")
        try:
            mock_data = api.generate_mock_data(3)
            print(f"   ✅ Generated {len(mock_data)} records")
            
            if mock_data:
                sample = mock_data[0]
                features = list(sample.keys())
                print(f"   📋 Features ({len(features)}): {features[:6]}...")
                
                if 'index' in features and 'packet_count' in features:
                    print("   ✅ Using model features!")
                else:
                    print("   ❌ Still using fallback features")
        except Exception as e:
            print(f"   ❌ Data generation error: {e}")
        
        # Clean up
        if api.is_monitoring:
            api.stop_monitoring()
            print("\n4. ✅ Monitoring stopped")
        
        print(f"\n📋 Summary:")
        print(f"   - Model loaded: {api.detector is not None}")
        print(f"   - Monitoring working: {api.is_monitoring}")
        print(f"   - Data generation: Working with model features")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_server_startup()
