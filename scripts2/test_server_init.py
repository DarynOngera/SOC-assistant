#!/usr/bin/env python3
"""
Test the new server initialization approach
"""

import sys
import os
sys.path.append('/home/ongera/projects/SOC-assistant')

def test_server_init():
    """Test the new server initialization"""
    try:
        print("🔬 Testing New Server Initialization")
        print("=" * 50)
        
        # Simulate the server startup process
        print("1. Simulating server startup...")
        
        # This simulates what happens in main()
        from src.dashboard.server import SOCDashboardAPI
        
        print("   🚀 Creating SOCDashboardAPI...")
        dashboard_api = SOCDashboardAPI()
        print(f"   ✅ Dashboard API created")
        print(f"   🤖 Detector loaded: {dashboard_api.detector is not None}")
        
        if dashboard_api.detector:
            print("   🎯 Model is available!")
            
            # Test feature template
            template = dashboard_api.detector.get_feature_template()
            feature_count = len(template.get('feature_columns', []))
            print(f"   📊 Model features: {feature_count}")
            
            # Test data generation
            mock_data = dashboard_api.generate_mock_data(3)
            print(f"   📋 Generated {len(mock_data)} records")
            
            if mock_data:
                sample = mock_data[0]
                features = list(sample.keys())
                print(f"   🔍 Sample features: {features[:6]}...")
                
                if 'index' in features and 'packet_count' in features:
                    print("   ✅ SUCCESS: Using model features!")
                else:
                    print("   ❌ Still using fallback features")
            
            # Test monitoring startup
            print("   🔄 Testing monitoring startup...")
            success = dashboard_api.start_monitoring()
            print(f"   {'✅' if success else '❌'} Monitoring start: {success}")
            
            if success:
                dashboard_api.stop_monitoring()
                print("   🛑 Monitoring stopped")
        else:
            print("   ❌ Model not available")
        
        print(f"\n📋 Summary:")
        print(f"   - Initialization: ✅ Success")
        print(f"   - Model loading: {'✅' if dashboard_api.detector else '❌'} {'Success' if dashboard_api.detector else 'Failed'}")
        print(f"   - Ready for server: {'✅' if dashboard_api.detector else '⚠️'} {'Yes' if dashboard_api.detector else 'With limitations'}")
        
        return dashboard_api.detector is not None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_server_init()
    print(f"\n🎯 Overall result: {'✅ READY' if success else '❌ NEEDS ATTENTION'}")
