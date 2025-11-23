#!/usr/bin/env python3
"""
Debug script to check PCAP file contents
"""

import sys
sys.path.append('/home/ongera/projects/SOC-assistant')

def debug_pcap():
    """Debug PCAP file contents"""
    try:
        from scapy.all import rdpcap, IP, TCP, UDP, ICMP
        
        pcap_file = '/home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/syn_flood.pcap'
        
        print(f"🔍 Debugging PCAP: {pcap_file}")
        
        # Read packets
        packets = rdpcap(pcap_file)
        print(f"📊 Total packets: {len(packets)}")
        
        if len(packets) > 0:
            print(f"📋 First few packets:")
            for i, pkt in enumerate(packets[:5]):
                print(f"  {i+1}. {pkt.summary()}")
                
                # Check if it has IP layer
                if IP in pkt:
                    print(f"     IP: {pkt[IP].src} -> {pkt[IP].dst}")
                    if TCP in pkt:
                        print(f"     TCP: {pkt[TCP].sport} -> {pkt[TCP].dport}, flags={pkt[TCP].flags}")
                    elif UDP in pkt:
                        print(f"     UDP: {pkt[UDP].sport} -> {pkt[UDP].dport}")
                else:
                    print(f"     No IP layer found")
        else:
            print("❌ No packets found in PCAP file")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_pcap()
