#!/usr/bin/env python3
"""
Simple PCAP Generator - Lightweight version
Generates smaller PCAPs faster without heavy traffic generation
"""

import os
import sys
import time
import subprocess
from datetime import datetime
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info

class SimplePCAPGenerator:
    """Generate simple PCAPs quickly"""
    
    def __init__(self):
        self.pcap_dir = os.path.join(os.path.dirname(__file__), 'data_capture/pcaps')
        os.makedirs(self.pcap_dir, exist_ok=True)
        
    def create_simple_topology(self):
        """Create a minimal network topology"""
        net = Mininet(switch=OVSSwitch, link=TCLink, autoSetMacs=True, autoStaticArp=True)
        
        # Add one switch and two hosts
        s1 = net.addSwitch('s1')
        h1 = net.addHost('h1', ip='10.0.0.1/24')
        h2 = net.addHost('h2', ip='10.0.0.2/24')
        
        net.addLink(h1, s1)
        net.addLink(h2, s1)
        
        return net
    
    def start_capture(self, net, filename):
        """Start packet capture"""
        pcap_path = os.path.join(self.pcap_dir, filename)
        s1 = net.get('s1')
        s1.cmd(f'timeout 10 tcpdump -i s1-eth1 -w {pcap_path} &')
        return pcap_path
    
    def stop_capture(self):
        """Stop packet capture"""
        subprocess.run(['pkill', '-9', 'tcpdump'], stderr=subprocess.DEVNULL)
        time.sleep(1)
    
    def generate_normal_traffic(self, net):
        """Generate simple normal traffic"""
        info('  Generating normal traffic...\n')
        h1 = net.get('h1')
        h2 = net.get('h2')
        
        # Simple ping traffic
        for i in range(20):
            h1.cmd(f'ping -c 1 10.0.0.2 > /dev/null &')
            time.sleep(0.2)
        
        # Simple HTTP-like traffic
        h2.cmd('python3 -m http.server 80 > /dev/null 2>&1 &')
        time.sleep(1)
        for i in range(10):
            h1.cmd('curl -s http://10.0.0.2 > /dev/null &')
            time.sleep(0.3)
        
        time.sleep(2)
        h2.cmd('pkill -9 python3')
    
    def generate_syn_flood(self, net):
        """Generate simple SYN flood"""
        info('  Generating SYN flood...\n')
        h1 = net.get('h1')
        h2 = net.get('h2')
        
        h2.cmd('nc -l 80 > /dev/null &')
        time.sleep(0.5)
        
        # Simple SYN flood with scapy
        for i in range(100):
            h1.cmd('python3 -c "from scapy.all import *; send(IP(dst=\'10.0.0.2\')/TCP(dport=80,flags=\'S\'), verbose=0)" > /dev/null 2>&1 &')
            if i % 20 == 0:
                time.sleep(0.1)
        
        time.sleep(2)
        h2.cmd('pkill -9 nc')
    
    def generate_port_scan(self, net):
        """Generate simple port scan"""
        info('  Generating port scan...\n')
        h1 = net.get('h1')
        
        ports = [22, 80, 443, 8080, 3306]
        for port in ports:
            h1.cmd(f'nc -zv -w 1 10.0.0.2 {port} > /dev/null 2>&1 &')
            time.sleep(0.3)
        
        time.sleep(1)
    
    def generate_udp_flood(self, net):
        """Generate simple UDP flood"""
        info('  Generating UDP flood...\n')
        h1 = net.get('h1')
        
        for i in range(50):
            h1.cmd('echo "FLOOD" | nc -u 10.0.0.2 53 > /dev/null 2>&1 &')
            if i % 10 == 0:
                time.sleep(0.1)
        
        time.sleep(1)
    
    def generate_http_flood(self, net):
        """Generate simple HTTP flood"""
        info('  Generating HTTP flood...\n')
        h1 = net.get('h1')
        h2 = net.get('h2')
        
        h2.cmd('python3 -m http.server 80 > /dev/null 2>&1 &')
        time.sleep(1)
        
        for i in range(50):
            h1.cmd('curl -s http://10.0.0.2 > /dev/null &')
            if i % 10 == 0:
                time.sleep(0.1)
        
        time.sleep(2)
        h2.cmd('pkill -9 python3')
    
    def generate_icmp_flood(self, net):
        """Generate simple ICMP flood"""
        info('  Generating ICMP flood...\n')
        h1 = net.get('h1')
        
        h1.cmd('ping -c 100 -i 0.01 10.0.0.2 > /dev/null &')
        time.sleep(3)
    
    def generate_pcap(self, name, traffic_func):
        """Generate a single PCAP file"""
        # Clean up
        os.system('mn -c > /dev/null 2>&1')
        time.sleep(0.5)
        
        # Create network
        net = self.create_simple_topology()
        net.start()
        
        # Start capture
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pcap_file = f'{name}_{timestamp}.pcap'
        self.start_capture(net, pcap_file)
        
        time.sleep(1)
        
        # Generate traffic
        traffic_func(net)
        
        time.sleep(2)
        
        # Stop
        self.stop_capture()
        net.stop()
        
        return pcap_file
    
    def generate_all(self):
        """Generate all PCAPs"""
        print("\n" + "="*60)
        print("SIMPLE PCAP GENERATION")
        print("="*60 + "\n")
        
        # Clean up
        info('Cleaning up...\n')
        os.system('mn -c > /dev/null 2>&1')
        
        pcaps = []
        
        # Normal traffic
        print("[1/6] Generating Normal Traffic PCAP...")
        pcap = self.generate_pcap('normal_traffic', self.generate_normal_traffic)
        pcaps.append(pcap)
        print(f"✓ {pcap}")
        
        # Attacks
        attacks = [
            ('attack_syn_flood', self.generate_syn_flood, 2),
            ('attack_port_scan', self.generate_port_scan, 3),
            ('attack_udp_flood', self.generate_udp_flood, 4),
            ('attack_http_flood', self.generate_http_flood, 5),
            ('attack_icmp_flood', self.generate_icmp_flood, 6)
        ]
        
        for name, func, idx in attacks:
            print(f"[{idx}/6] Generating {name.replace('attack_', '').upper()} PCAP...")
            pcap = self.generate_pcap(name, func)
            pcaps.append(pcap)
            print(f"✓ {pcap}")
        
        # Final cleanup
        os.system('mn -c > /dev/null 2>&1')
        
        print("\n" + "="*60)
        print("COMPLETE!")
        print("="*60)
        print(f"\nPCAPs saved to: {self.pcap_dir}\n")
        
        for pcap in pcaps:
            path = os.path.join(self.pcap_dir, pcap)
            if os.path.exists(path):
                size = os.path.getsize(path)
                print(f"  ✓ {pcap} ({size:,} bytes)")
            else:
                print(f"  ✗ {pcap} (not found)")
        
        print("\nNext: python3 test_local_simulation.py")

def main():
    if os.geteuid() != 0:
        print("Error: Run as root (use sudo)")
        sys.exit(1)
    
    setLogLevel('info')
    
    generator = SimplePCAPGenerator()
    generator.generate_all()

if __name__ == '__main__':
    main()
