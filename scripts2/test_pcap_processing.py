#!/usr/bin/env python3
"""
Test script to verify PCAP processing works correctly
"""

import sys
import os
sys.path.append('/home/ongera/projects/SOC-assistant')

def test_pcap_processing():
    """Test the new PCAP processing functionality"""
    print("🔬 Testing PCAP Processing")
    print("=" * 40)
    
    try:
        from src.dashboard.server import SOCDashboardAPI
        
        print("1. Creating SOCDashboardAPI instance...")
        api = SOCDashboardAPI()
        print(f"   ✅ API created, detector loaded: {api.detector is not None}")
        
        # Test PCAP files
        pcap_files = [
            '/home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/syn_flood.pcap',
            '/home/ongera/projects/SOC-assistant/data_capture/pcaps/normal_traffic_20251007_151008.pcap'
        ]
        
        for pcap_file in pcap_files:
            print(f"\n2. Testing PCAP file: {os.path.basename(pcap_file)}")
            
            if not os.path.exists(pcap_file):
                print(f"   ❌ PCAP file not found: {pcap_file}")
                continue
            
            print(f"   📁 File exists, size: {os.path.getsize(pcap_file)} bytes")
            
            # Test feature extraction
            print("   🔍 Extracting features from PCAP...")
            network_data = api._extract_features_from_pcap(pcap_file)
            
            if network_data:
                print(f"   ✅ Extracted {len(network_data)} records")
                
                if network_data:
                    sample = network_data[0]
                    print(f"   📋 Sample features: {list(sample.keys())[:10]}...")
                    
                    # Test model processing
                    print("   🤖 Processing through ML model...")
                    api.current_simulation = 'syn_flood' if 'syn_flood' in pcap_file else 'normal_traffic'
                    processed_data = api.process_with_models(network_data[:5])  # Test with first 5 records
                    
                    anomalies = [r for r in processed_data if r.get('prediction', 0) == 1]
                    print(f"   🚨 Anomalies detected: {len(anomalies)}/{len(processed_data)}")
                    
                    if anomalies:
                        sample_anomaly = anomalies[0]
                        print(f"   📊 Sample anomaly score: {sample_anomaly.get('anomaly_score', 'N/A')}")
                        print(f"   🎯 Sample attack type: {sample_anomaly.get('attack_type', 'N/A')}")
                else:
                    print("   ❌ No records extracted")
            else:
                print("   ❌ Feature extraction failed")
        
        # Test the full PCAP processing pipeline
        print(f"\n3. Testing full PCAP processing pipeline...")
        api.current_simulation = 'syn_flood'
        
        # Use a small attack PCAP file
        attack_pcap = '/home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/syn_flood.pcap'
        if os.path.exists(attack_pcap):
            print(f"   🎯 Processing attack PCAP: {os.path.basename(attack_pcap)}")
            api._process_pcap_for_alerts(attack_pcap)
            print("   ✅ PCAP processing completed")
        else:
            print(f"   ❌ Attack PCAP not found: {attack_pcap}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_pcap_processing()
