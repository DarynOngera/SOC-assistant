#!/usr/bin/env python3
"""
Generate Varied PCAP Data for Better Model Training
Creates diverse normal and attack traffic patterns
"""

import os
import sys
from datetime import datetime
from scapy.all import *
import random

class VariedPCAPGenerator:
    """Generate varied PCAP data with different patterns"""
    
    def __init__(self):
        self.pcap_dir = '/home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/pcaps'
        os.makedirs(self.pcap_dir, exist_ok=True)
    
    def generate_varied_normal_traffic(self, variant=1):
        """Generate varied normal traffic patterns"""
        print(f"Generating normal traffic variant {variant}...")
        
        packets = []
        
        # Variant 1: Web browsing pattern
        if variant == 1:
            for i in range(50):
                # HTTP requests
                pkt = IP(src=f"10.0.1.{random.randint(1,10)}", dst="10.0.2.1")/TCP(sport=random.randint(49152,65535), dport=80, flags="S")
                packets.append(pkt)
                pkt = IP(src="10.0.2.1", dst=f"10.0.1.{random.randint(1,10)}")/TCP(sport=80, dport=random.randint(49152,65535), flags="SA")
                packets.append(pkt)
                pkt = IP(src=f"10.0.1.{random.randint(1,10)}", dst="10.0.2.1")/TCP(sport=random.randint(49152,65535), dport=80, flags="A")
                packets.append(pkt)
        
        # Variant 2: File transfer pattern
        elif variant == 2:
            for i in range(30):
                # Large data transfers
                pkt = IP(src="10.0.1.1", dst="10.0.2.1")/TCP(sport=random.randint(49152,65535), dport=21, flags="PA")/Raw(load="X"*1400)
                packets.append(pkt)
                pkt = IP(src="10.0.2.1", dst="10.0.1.1")/TCP(sport=21, dport=random.randint(49152,65535), flags="A")
                packets.append(pkt)
        
        # Variant 3: DNS + Ping pattern
        elif variant == 3:
            for i in range(40):
                # DNS queries
                pkt = IP(src=f"10.0.1.{random.randint(1,10)}", dst="10.0.2.1")/UDP(sport=random.randint(49152,65535), dport=53)/Raw(load="DNS")
                packets.append(pkt)
                # ICMP
                pkt = IP(src=f"10.0.1.{random.randint(1,10)}", dst="10.0.2.1")/ICMP(type=8)/Raw(load="X"*56)
                packets.append(pkt)
                pkt = IP(src="10.0.2.1", dst=f"10.0.1.{random.randint(1,10)}")/ICMP(type=0)/Raw(load="X"*56)
                packets.append(pkt)
        
        # Variant 4: SSH session pattern
        elif variant == 4:
            for i in range(60):
                # SSH traffic (small packets, bidirectional)
                pkt = IP(src="10.0.1.1", dst="10.0.2.1")/TCP(sport=random.randint(49152,65535), dport=22, flags="PA")/Raw(load="X"*random.randint(40,200))
                packets.append(pkt)
                pkt = IP(src="10.0.2.1", dst="10.0.1.1")/TCP(sport=22, dport=random.randint(49152,65535), flags="PA")/Raw(load="X"*random.randint(40,200))
                packets.append(pkt)
        
        # Variant 5: Mixed services
        else:
            for i in range(20):
                # HTTP
                pkt = IP(src=f"10.0.1.{random.randint(1,10)}", dst="10.0.2.1")/TCP(sport=random.randint(49152,65535), dport=80, flags="PA")
                packets.append(pkt)
                # HTTPS
                pkt = IP(src=f"10.0.1.{random.randint(1,10)}", dst="10.0.2.1")/TCP(sport=random.randint(49152,65535), dport=443, flags="PA")
                packets.append(pkt)
                # DNS
                pkt = IP(src=f"10.0.1.{random.randint(1,10)}", dst="10.0.2.1")/UDP(sport=random.randint(49152,65535), dport=53)
                packets.append(pkt)
                # SMTP
                pkt = IP(src=f"10.0.1.{random.randint(1,10)}", dst="10.0.2.1")/TCP(sport=random.randint(49152,65535), dport=25, flags="PA")
                packets.append(pkt)
        
        return packets
    
    def generate_varied_syn_flood(self, intensity='medium'):
        """Generate SYN flood with different intensities"""
        print(f"Generating SYN flood ({intensity} intensity)...")
        
        packets = []
        
        if intensity == 'low':
            count = 50
        elif intensity == 'medium':
            count = 150
        else:  # high
            count = 300
        
        for i in range(count):
            pkt = IP(src=f"10.0.{random.randint(1,254)}.{random.randint(1,254)}", dst="10.0.2.1")/TCP(sport=RandShort(), dport=80, flags="S")
            packets.append(pkt)
        
        return packets
    
    def generate_varied_port_scan(self, scan_type='sequential'):
        """Generate port scans with different patterns"""
        print(f"Generating port scan ({scan_type})...")
        
        packets = []
        ports = list(range(1, 1024))  # Well-known ports
        
        if scan_type == 'sequential':
            selected_ports = ports[:100]
        elif scan_type == 'random':
            selected_ports = random.sample(ports, 100)
        else:  # targeted
            selected_ports = [20, 21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3306, 3389, 8080] * 7
        
        for port in selected_ports:
            pkt = IP(src="10.0.1.1", dst="10.0.2.1")/TCP(sport=RandShort(), dport=port, flags="S")
            packets.append(pkt)
            # RST response
            pkt = IP(src="10.0.2.1", dst="10.0.1.1")/TCP(sport=port, dport=RandShort(), flags="R")
            packets.append(pkt)
        
        return packets
    
    def generate_varied_udp_flood(self, packet_size='mixed'):
        """Generate UDP flood with different packet sizes"""
        print(f"Generating UDP flood ({packet_size} packet sizes)...")
        
        packets = []
        
        for i in range(200):
            if packet_size == 'small':
                size = random.randint(10, 100)
            elif packet_size == 'large':
                size = random.randint(1000, 1400)
            else:  # mixed
                size = random.randint(10, 1400)
            
            pkt = IP(src=f"10.0.{random.randint(1,254)}.{random.randint(1,254)}", dst="10.0.2.1")/UDP(sport=RandShort(), dport=53)/Raw(load="X"*size)
            packets.append(pkt)
        
        return packets
    
    def generate_all_varied_pcaps(self):
        """Generate all varied PCAPs"""
        
        print("="*70)
        print("GENERATING VARIED PCAP DATA")
        print("="*70 + "\n")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        generated = []
        
        # Normal traffic variants (5 variants)
        print("[1/13] Normal Traffic Variants...")
        for variant in range(1, 6):
            packets = self.generate_varied_normal_traffic(variant)
            filename = f'normal_traffic_v{variant}_{timestamp}.pcap'
            filepath = os.path.join(self.pcap_dir, filename)
            wrpcap(filepath, packets)
            size = os.path.getsize(filepath)
            print(f"  ✓ {filename} ({size:,} bytes, {len(packets)} packets)")
            generated.append(filename)
        
        # SYN flood variants (3 intensities)
        print("\n[2/13] SYN Flood Variants...")
        for intensity in ['low', 'medium', 'high']:
            packets = self.generate_varied_syn_flood(intensity)
            filename = f'attack_syn_flood_{intensity}_{timestamp}.pcap'
            filepath = os.path.join(self.pcap_dir, filename)
            wrpcap(filepath, packets)
            size = os.path.getsize(filepath)
            print(f"  ✓ {filename} ({size:,} bytes, {len(packets)} packets)")
            generated.append(filename)
        
        # Port scan variants (3 types)
        print("\n[3/13] Port Scan Variants...")
        for scan_type in ['sequential', 'random', 'targeted']:
            packets = self.generate_varied_port_scan(scan_type)
            filename = f'attack_port_scan_{scan_type}_{timestamp}.pcap'
            filepath = os.path.join(self.pcap_dir, filename)
            wrpcap(filepath, packets)
            size = os.path.getsize(filepath)
            print(f"  ✓ {filename} ({size:,} bytes, {len(packets)} packets)")
            generated.append(filename)
        
        # UDP flood variants (2 types)
        print("\n[4/13] UDP Flood Variants...")
        for packet_size in ['small', 'mixed']:
            packets = self.generate_varied_udp_flood(packet_size)
            filename = f'attack_udp_flood_{packet_size}_{timestamp}.pcap'
            filepath = os.path.join(self.pcap_dir, filename)
            wrpcap(filepath, packets)
            size = os.path.getsize(filepath)
            print(f"  ✓ {filename} ({size:,} bytes, {len(packets)} packets)")
            generated.append(filename)
        
        print("\n" + "="*70)
        print("GENERATION COMPLETE!")
        print("="*70)
        print(f"\nGenerated {len(generated)} varied PCAP files")
        print(f"Location: {self.pcap_dir}\n")
        
        print("Summary:")
        print(f"  • Normal traffic variants: 5")
        print(f"  • SYN flood variants: 3 (low, medium, high)")
        print(f"  • Port scan variants: 3 (sequential, random, targeted)")
        print(f"  • UDP flood variants: 2 (small, mixed)")
        
        print("\nNext steps:")
        print("  1. Run: python3 train_with_pcaps.py")
        print("  2. Run: python3 train_comprehensive_model.py")
        print("  3. Review performance reports")
        
        return generated

def main():
    generator = VariedPCAPGenerator()
    generator.generate_all_varied_pcaps()

if __name__ == '__main__':
    main()
