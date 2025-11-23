#!/usr/bin/env python3
"""
Test Local Mininet Simulation
Verifies that normal and attack traffic PCAPs are processed correctly
"""

import os
import sys
import glob

sys.path.append('/home/ongera/projects/SOC-assistant')

from src.dashboard.server import SOCDashboardAPI

def test_pcap_processing():
    """Test PCAP processing for normal and attack traffic"""
    
    print("="*70)
    print("TESTING LOCAL MININET SIMULATION")
    print("="*70)
    
    # Initialize dashboard API
    print("\n[1/4] Initializing Dashboard API...")
    api = SOCDashboardAPI()
    print("✓ Dashboard API initialized")
    
    # Find generated PCAPs
    pcap_dir = '/home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/pcaps'
    
    if not os.path.exists(pcap_dir):
        print(f"✗ PCAP directory not found: {pcap_dir}")
        print("  Run: sudo python3 mininet_data_generation/generate_local_pcaps.py")
        return False
    
    # Get all PCAPs
    all_pcaps = glob.glob(os.path.join(pcap_dir, '*.pcap'))
    
    if not all_pcaps:
        print(f"✗ No PCAP files found in {pcap_dir}")
        print("  Run: sudo python3 mininet_data_generation/generate_local_pcaps.py")
        return False
    
    print(f"\n[2/4] Found {len(all_pcaps)} PCAP files")
    
    # Separate normal and attack PCAPs
    normal_pcaps = [p for p in all_pcaps if 'normal_traffic' in os.path.basename(p)]
    attack_pcaps = [p for p in all_pcaps if 'attack_' in os.path.basename(p)]
    
    print(f"  • Normal traffic PCAPs: {len(normal_pcaps)}")
    print(f"  • Attack PCAPs: {len(attack_pcaps)}")
    
    # Test normal traffic
    print("\n[3/4] Testing Normal Traffic Processing...")
    if normal_pcaps:
        pcap_file = normal_pcaps[0]
        print(f"  Processing: {os.path.basename(pcap_file)}")
        
        api.current_simulation = 'normal_traffic'
        api.mininet_mode = 'normal'
        
        # Extract features
        network_data = api._extract_features_from_pcap(pcap_file)
        
        if network_data:
            print(f"  ✓ Extracted {len(network_data)} flow records")
            
            # Process through model
            processed = api.process_with_models(network_data[:20])
            
            anomalies = [r for r in processed if r.get('prediction', 0) == 1]
            normal = [r for r in processed if r.get('prediction', 0) == 0]
            
            print(f"  ✓ Model predictions: {len(normal)} normal, {len(anomalies)} anomalies")
            
            if len(normal) > len(anomalies):
                print(f"  ✓ PASS: Normal traffic correctly classified")
            else:
                print(f"  ⚠ WARNING: Too many anomalies in normal traffic")
        else:
            print(f"  ✗ FAIL: Could not extract features")
    else:
        print("  ⚠ No normal traffic PCAPs found")
    
    # Test attack traffic
    print("\n[4/4] Testing Attack Traffic Processing...")
    
    attack_types = {
        'syn_flood': 'SYN Flood',
        'port_scan': 'Port Scan',
        'udp_flood': 'UDP Flood',
        'http_flood': 'HTTP Flood',
        'icmp_flood': 'ICMP Flood'
    }
    
    results = {}
    
    for attack_key, attack_name in attack_types.items():
        matching_pcaps = [p for p in attack_pcaps if attack_key in os.path.basename(p)]
        
        if matching_pcaps:
            pcap_file = matching_pcaps[0]
            print(f"\n  Testing {attack_name}...")
            print(f"    File: {os.path.basename(pcap_file)}")
            
            api.current_simulation = attack_key
            api.mininet_mode = 'attack'
            
            # Extract features
            network_data = api._extract_features_from_pcap(pcap_file)
            
            if network_data:
                print(f"    ✓ Extracted {len(network_data)} flow records")
                
                # Process through model
                processed = api.process_with_models(network_data[:20])
                
                anomalies = [r for r in processed if r.get('prediction', 0) == 1]
                normal = [r for r in processed if r.get('prediction', 0) == 0]
                
                print(f"    ✓ Predictions: {len(normal)} normal, {len(anomalies)} anomalies")
                
                # Check if attack was detected
                if len(anomalies) > 0:
                    print(f"    ✓ PASS: Attack detected")
                    results[attack_key] = 'PASS'
                else:
                    print(f"    ⚠ WARNING: No anomalies detected")
                    results[attack_key] = 'WARN'
            else:
                print(f"    ✗ FAIL: Could not extract features")
                results[attack_key] = 'FAIL'
        else:
            print(f"\n  ⚠ {attack_name}: No PCAP found")
            results[attack_key] = 'MISSING'
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    print("\nAttack Detection Results:")
    for attack_key, attack_name in attack_types.items():
        status = results.get(attack_key, 'MISSING')
        symbol = '✓' if status == 'PASS' else '⚠' if status == 'WARN' else '✗'
        print(f"  {symbol} {attack_name}: {status}")
    
    print("\n" + "="*70)
    print("FRONTEND SIMULATION VERIFICATION")
    print("="*70)
    
    print("\nExpected Behavior:")
    print("  1. Normal Traffic Simulation:")
    print("     • Uses: normal_traffic_*.pcap")
    print("     • Result: Few/no alerts, healthy system state")
    print("     • Model predicts: Mostly 0 (normal)")
    
    print("\n  2. Attack Simulations:")
    print("     • Uses: attack_<type>_*.pcap")
    print("     • Result: Multiple alerts, attack identified")
    print("     • Model predicts: 1 (anomaly) for suspicious flows")
    
    print("\nTo test in frontend:")
    print("  1. Start dashboard: cd src/dashboard && python3 server.py")
    print("  2. Open UI: http://localhost:5000")
    print("  3. Navigate to Mininet Simulation")
    print("  4. Try 'Normal Traffic' - should show healthy state")
    print("  5. Try each attack type - should show alerts")
    
    print("\n" + "="*70)
    
    return True

if __name__ == '__main__':
    try:
        test_pcap_processing()
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
