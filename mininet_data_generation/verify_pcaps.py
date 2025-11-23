#!/usr/bin/env python3
"""
PCAP Verification Script
Checks packet counts in existing PCAP files
"""

import os
import subprocess
import sys

def check_pcap(pcap_path):
    """Check packet count in PCAP file"""
    if not os.path.exists(pcap_path):
        return None, None
    
    try:
        # Get packet count
        result = subprocess.run(
            ['tcpdump', '-r', pcap_path, '-n'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout:
            packet_count = len([line for line in result.stdout.strip().split('\n') if line])
        else:
            packet_count = 0
        
        # Get file size
        size = os.path.getsize(pcap_path)
        
        return packet_count, size
    except Exception as e:
        print(f"Error checking {pcap_path}: {e}")
        return None, None

def main():
    pcap_dir = os.path.join(os.path.dirname(__file__), 'data_capture/mininet')
    
    print("\n" + "="*70)
    print("PCAP FILE VERIFICATION")
    print("="*70 + "\n")
    
    if not os.path.exists(pcap_dir):
        print(f"❌ PCAP directory not found: {pcap_dir}")
        return
    
    print(f"Checking PCAPs in: {pcap_dir}\n")
    
    pcap_files = [
        'syn_flood.pcap',
        'port_scan.pcap',
        'udp_flood.pcap',
        'http_flood.pcap'
    ]
    
    total_packets = 0
    total_size = 0
    
    print(f"{'File':<20} {'Size':>12} {'Packets':>10} {'Status':>10}")
    print("-" * 70)
    
    for pcap_file in pcap_files:
        pcap_path = os.path.join(pcap_dir, pcap_file)
        packet_count, size = check_pcap(pcap_path)
        
        if packet_count is not None:
            total_packets += packet_count
            total_size += size
            
            # Determine status
            if packet_count < 20:
                status = "⚠️  LOW"
            elif packet_count < 100:
                status = "⚡ MEDIUM"
            else:
                status = "✅ GOOD"
            
            print(f"{pcap_file:<20} {size:>10,} B {packet_count:>9} {status:>10}")
        else:
            print(f"{pcap_file:<20} {'NOT FOUND':>12} {'-':>10} {'❌ MISSING':>10}")
    
    print("-" * 70)
    print(f"{'TOTAL':<20} {total_size:>10,} B {total_packets:>9}")
    print()
    
    # Recommendations
    if total_packets < 100:
        print("⚠️  WARNING: Very few packets detected!")
        print("   Current PCAPs will generate minimal alerts during replay.")
        print()
        print("📝 RECOMMENDATION:")
        print("   Run the enhanced PCAP generator to create more visible attacks:")
        print()
        print("   sudo python3 generate_enhanced_attack_pcaps.py")
        print()
        print("   This will generate:")
        print("   - SYN Flood: ~500 packets")
        print("   - Port Scan: ~300 packets")
        print("   - UDP Flood: ~400 packets")
        print("   - HTTP Flood: ~300 packets")
        print()
    elif total_packets < 500:
        print("⚡ MODERATE: PCAPs have some packets but could be improved.")
        print("   Consider regenerating with enhanced script for better visibility.")
        print()
    else:
        print("✅ EXCELLENT: PCAPs have good packet counts!")
        print("   These should generate visible alerts during replay.")
        print()
    
    print("="*70 + "\n")

if __name__ == '__main__':
    main()
