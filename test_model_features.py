#!/usr/bin/env python3
"""
Test that the system is now using model features correctly
"""

import sys
import os
sys.path.append('/home/ongera/projects/SOC-assistant')

def test_model_features():
    """Test that the system uses model features instead of fallback"""
    try:
        from src.dashboard.server import SOCDashboardAPI
        
        print("🔬 Testing Model Feature Usage")
        print("=" * 50)
        
        # Create API instance
        print("1. Creating SOCDashboardAPI...")
        api = SOCDashboardAPI()
        print(f"   ✅ Detector loaded: {api.detector is not None}")
        
        # Test the monitoring data generation
        print("\n2. Testing monitoring data generation...")
        mock_data = api.generate_mock_data(5)
        print(f"   ✅ Generated {len(mock_data)} records")
        
        if mock_data:
            sample = mock_data[0]
            print(f"   📋 Sample features: {list(sample.keys())[:10]}...")
            
            # Check if it has the model's expected features
            if 'index' in sample and 'packet_count' in sample:
                print("   ✅ Using model features!")
            else:
                print("   ❌ Still using fallback features")
        
        # Test synthetic attack data generation
        print("\n3. Testing synthetic attack data generation...")
        api.current_simulation = 'syn_flood'
        api._generate_synthetic_attack_data()
        print("   ✅ Synthetic attack data generation completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_model_features()
