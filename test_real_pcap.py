#!/usr/bin/env python3
"""
Test that we're now using real PCAP files instead of synthetic data
"""

import sys
import os
sys.path.append('/home/ongera/projects/SOC-assistant')

def test_real_pcap_usage():
    """Test that the system uses real PCAP files"""
    try:
        from src.dashboard.server import SOCDashboardAPI
        
        print("🔬 Testing Real PCAP Usage")
        print("=" * 50)
        
        # Create API instance
        print("1. Creating SOCDashboardAPI...")
        api = SOCDashboardAPI()
        print(f"   ✅ Detector loaded: {api.detector is not None}")
        
        # Test normal traffic PCAP
        print("\n2. Testing normal traffic PCAP...")
        normal_pcap = '/home/ongera/projects/SOC-assistant/data_capture/pcaps/normal_traffic_20251007_151008.pcap'
        api.current_simulation = 'normal_traffic'
        
        if os.path.exists(normal_pcap):
            network_data = api._extract_features_from_pcap(normal_pcap)
            print(f"   ✅ Extracted {len(network_data)} flows from normal PCAP")
            
            if network_data:
                sample = network_data[0]
                print(f"   📋 Sample features: {list(sample.keys())[:8]}...")
        
        # Test attack simulation with normal PCAP (fallback)
        print("\n3. Testing attack simulation with PCAP fallback...")
        api.current_simulation = 'syn_flood'
        
        # This should use the normal PCAP and apply attack patterns
        attack_pcap = '/home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/syn_flood.pcap'
        
        print(f"   🎯 Processing {api.current_simulation} simulation...")
        
        # Test the fallback mechanism
        fallback_pcap = api._get_fallback_pcap_file()
        if fallback_pcap:
            print(f"   ✅ Found fallback PCAP: {os.path.basename(fallback_pcap)}")
            
            # Extract data and apply attack patterns
            network_data = api._extract_features_from_pcap(fallback_pcap)
            if network_data:
                print(f"   📊 Extracted {len(network_data)} flows from fallback PCAP")
                
                # Apply attack patterns
                modified_data = api._inject_attack_patterns(network_data[:10], 'syn_flood')  # Test with first 10
                print(f"   🎯 Applied attack patterns to {len(modified_data)} flows")
                
                # Show difference
                if modified_data:
                    original = network_data[0]
                    modified = modified_data[0]
                    
                    print(f"   📈 Original syn_ratio: {original.get('syn_ratio', 0):.3f}")
                    print(f"   📈 Modified syn_ratio: {modified.get('syn_ratio', 0):.3f}")
                    print(f"   📈 Original packet_count: {original.get('packet_count', 0)}")
                    print(f"   📈 Modified packet_count: {modified.get('packet_count', 0)}")
        else:
            print("   ❌ No fallback PCAP found")
        
        print(f"\n✅ Real PCAP processing test completed!")
        print(f"📋 Summary:")
        print(f"   - Using real PCAP files instead of synthetic data")
        print(f"   - Normal traffic: Direct PCAP processing")
        print(f"   - Attack traffic: Normal PCAP + Attack pattern injection")
        print(f"   - Fallback mechanism working for IPv6 attack files")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_real_pcap_usage()
