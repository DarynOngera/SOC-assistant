#!/usr/bin/env python3
"""
Check all attack PCAP files for IPv4 vs IPv6 content
"""

import sys
import os
sys.path.append('/home/ongera/projects/SOC-assistant')

def check_pcap_files():
    """Check all PCAP files for IPv4/IPv6 content"""
    try:
        from scapy.all import rdpcap, IP
        
        pcap_dir = '/home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/'
        pcap_files = [
            'syn_flood.pcap',
            'port_scan.pcap', 
            'udp_flood.pcap',
            'http_flood.pcap'
        ]
        
        print("🔍 Checking Attack PCAP Files")
        print("=" * 50)
        
        usable_files = []
        
        for pcap_file in pcap_files:
            pcap_path = os.path.join(pcap_dir, pcap_file)
            
            if not os.path.exists(pcap_path):
                print(f"❌ {pcap_file}: File not found")
                continue
                
            try:
                packets = rdpcap(pcap_path)
                total_packets = len(packets)
                ipv4_count = sum(1 for pkt in packets if IP in pkt)
                ipv6_count = sum(1 for pkt in packets if 'IPv6' in str(pkt))
                other_count = total_packets - ipv4_count - ipv6_count
                
                print(f"📊 {pcap_file}:")
                print(f"   Total: {total_packets}, IPv4: {ipv4_count}, IPv6: {ipv6_count}, Other: {other_count}")
                
                if ipv4_count > 0:
                    print(f"   ✅ USABLE - Has {ipv4_count} IPv4 packets")
                    usable_files.append(pcap_file)
                else:
                    print(f"   ❌ NOT USABLE - No IPv4 packets")
                    
            except Exception as e:
                print(f"❌ {pcap_file}: Error reading - {e}")
        
        print("\n" + "=" * 50)
        print(f"📋 Summary: {len(usable_files)}/{len(pcap_files)} files are usable")
        
        if usable_files:
            print("✅ Usable files:")
            for f in usable_files:
                print(f"   - {f}")
        else:
            print("❌ No usable IPv4 attack PCAP files found")
            print("\n🔧 SOLUTION: Generate new IPv4 attack traffic")
            
        return usable_files
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == '__main__':
    check_pcap_files()
