#!/usr/bin/env python3
"""
Test script to check if the ML model is actually working
"""

import sys
import os
sys.path.append('/home/ongera/projects/SOC-assistant')

def test_ml_model():
    """Test the ML model directly"""
    print("🔬 Testing ML Model Integration")
    print("=" * 40)
    
    try:
        # Import the dashboard API
        from src.dashboard.server import SOCDashboardAPI
        
        print("1. Creating SOCDashboardAPI instance...")
        api = SOCDashboardAPI()
        
        print(f"   ✅ API created successfully")
        print(f"   🤖 Detector loaded: {api.detector is not None}")
        print(f"   📊 DAL type: {type(api.dal).__name__}")
        print(f"   🎯 Threshold: {api.threshold}")
        
        # Test data generation
        print("\n2. Testing data generation...")
        network_data = api.generate_realistic_network_data(10)
        print(f"   ✅ Generated {len(network_data)} network records")
        
        if network_data:
            sample = network_data[0]
            print(f"   📋 Sample record keys: {list(sample.keys())}")
        
        # Test model processing
        print("\n3. Testing model processing...")
        processed_data = api.process_with_models(network_data)
        print(f"   ✅ Processed {len(processed_data)} records")
        
        # Check predictions
        anomalies = [r for r in processed_data if r.get('prediction', 0) == 1]
        print(f"   🚨 Anomalies detected: {len(anomalies)}/{len(processed_data)}")
        
        if anomalies:
            sample_anomaly = anomalies[0]
            print(f"   📊 Sample anomaly score: {sample_anomaly.get('anomaly_score', 'N/A')}")
            print(f"   🎯 Sample attack type: {sample_anomaly.get('attack_type', 'N/A')}")
        
        # Test attack pattern injection
        print("\n4. Testing attack pattern injection...")
        api.current_simulation = 'syn_flood'
        attack_data = api._inject_attack_patterns(network_data.copy(), 'syn_flood')
        processed_attack_data = api.process_with_models(attack_data)
        
        attack_anomalies = [r for r in processed_attack_data if r.get('prediction', 0) == 1]
        print(f"   🚨 Attack anomalies detected: {len(attack_anomalies)}/{len(processed_attack_data)}")
        
        # Compare normal vs attack detection rates
        normal_rate = len(anomalies) / len(processed_data) * 100
        attack_rate = len(attack_anomalies) / len(processed_attack_data) * 100
        
        print(f"\n📊 Detection Rate Comparison:")
        print(f"   Normal traffic: {normal_rate:.1f}% anomalies")
        print(f"   Attack traffic: {attack_rate:.1f}% anomalies")
        print(f"   Difference: {attack_rate - normal_rate:.1f}% increase")
        
        if attack_rate > normal_rate:
            print("   ✅ ML model is working - attack detection is higher!")
        else:
            print("   ❌ ML model issue - no difference in detection rates")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_ml_model()
