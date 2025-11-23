#!/usr/bin/env python3
"""
Generate IPv4 Attack PCAPs - Minimal version
Uses scapy directly without Mininet to avoid memory issues
"""

import os
import sys
from datetime import datetime
from scapy.all import *

def generate_syn_flood():
    """Generate SYN flood PCAP"""
    print("Generating SYN flood attack...")
    
    packets = []
    for i in range(100):
        pkt = IP(src=f"10.0.1.{(i%254)+1}", dst="10.0.2.1")/TCP(sport=RandShort(), dport=80, flags="S")
        packets.append(pkt)
    
    return packets

def generate_port_scan():
    """Generate port scan PCAP"""
    print("Generating port scan attack...")
    
    packets = []
    ports = list(range(20, 100)) + [80, 443, 22, 21, 23, 25, 53, 110, 143, 3306, 3389, 8080]
    
    for port in ports:
        pkt = IP(src="10.0.1.1", dst="10.0.2.1")/TCP(sport=RandShort(), dport=port, flags="S")
        packets.append(pkt)
        # RST response
        pkt = IP(src="10.0.2.1", dst="10.0.1.1")/TCP(sport=port, dport=RandShort(), flags="R")
        packets.append(pkt)
    
    return packets

def generate_udp_flood():
    """Generate UDP flood PCAP"""
    print("Generating UDP flood attack...")
    
    packets = []
    for i in range(200):
        pkt = IP(src=f"10.0.1.{(i%254)+1}", dst="10.0.2.1")/UDP(sport=RandShort(), dport=53)/Raw(load="FLOOD"*10)
        packets.append(pkt)
    
    return packets

def generate_http_flood():
    """Generate HTTP flood PCAP"""
    print("Generating HTTP flood attack...")
    
    packets = []
    http_request = b"GET / HTTP/1.1\r\nHost: target.com\r\n\r\n"
    
    for i in range(150):
        # SYN
        pkt = IP(src=f"10.0.1.{(i%254)+1}", dst="10.0.2.1")/TCP(sport=RandShort(), dport=80, flags="S", seq=1000+i)
        packets.append(pkt)
        # SYN-ACK
        pkt = IP(src="10.0.2.1", dst=f"10.0.1.{(i%254)+1}")/TCP(sport=80, dport=RandShort(), flags="SA", seq=2000+i, ack=1001+i)
        packets.append(pkt)
        # ACK + HTTP
        pkt = IP(src=f"10.0.1.{(i%254)+1}", dst="10.0.2.1")/TCP(sport=RandShort(), dport=80, flags="PA", seq=1001+i, ack=2001+i)/Raw(load=http_request)
        packets.append(pkt)
    
    return packets

def generate_icmp_flood():
    """Generate ICMP flood PCAP"""
    print("Generating ICMP flood attack...")
    
    packets = []
    for i in range(300):
        pkt = IP(src=f"10.0.1.{(i%254)+1}", dst="10.0.2.1")/ICMP(type=8)/Raw(load="X"*56)
        packets.append(pkt)
    
    return packets

def main():
    print("="*60)
    print("GENERATING IPv4 ATTACK PCAPS")
    print("="*60 + "\n")
    
    pcap_dir = '/home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/pcaps'
    os.makedirs(pcap_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    attacks = [
        ('syn_flood', generate_syn_flood),
        ('port_scan', generate_port_scan),
        ('udp_flood', generate_udp_flood),
        ('http_flood', generate_http_flood),
        ('icmp_flood', generate_icmp_flood)
    ]
    
    for idx, (name, func) in enumerate(attacks, 1):
        print(f"\n[{idx}/5] {name.upper().replace('_', ' ')}...")
        
        packets = func()
        
        filename = f'attack_{name}_{timestamp}.pcap'
        filepath = os.path.join(pcap_dir, filename)
        
        wrpcap(filepath, packets)
        
        size = os.path.getsize(filepath)
        print(f"  ✓ Saved: {filename} ({size:,} bytes, {len(packets)} packets)")
    
    print("\n" + "="*60)
    print("COMPLETE!")
    print("="*60)
    print(f"\nPCAPs saved to: {pcap_dir}\n")
    
    # List all PCAPs
    all_pcaps = sorted([f for f in os.listdir(pcap_dir) if f.endswith('.pcap')])
    
    normal = [p for p in all_pcaps if 'normal_traffic' in p]
    attacks = [p for p in all_pcaps if 'attack_' in p and timestamp in p]
    
    print(f"Normal Traffic ({len(normal)}):")
    for pcap in normal:
        size = os.path.getsize(os.path.join(pcap_dir, pcap))
        print(f"  ✓ {pcap} ({size:,} bytes)")
    
    print(f"\nAttack Traffic (NEW - {len(attacks)}):")
    for pcap in attacks:
        size = os.path.getsize(os.path.join(pcap_dir, pcap))
        attack_type = pcap.split('_')[1]
        print(f"  ✓ {pcap} ({size:,} bytes) - {attack_type.upper()}")
    
    print("\nNext: python3 test_local_simulation.py")

if __name__ == '__main__':
    main()
