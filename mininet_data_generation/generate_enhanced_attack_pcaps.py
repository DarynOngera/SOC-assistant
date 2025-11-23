#!/usr/bin/env python3
"""
Enhanced Attack PCAP Generator
Generates attack PCAPs with significantly more packets for better visibility during replay
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

class EnhancedAttackPCAPGenerator:
    """Generate attack PCAPs with high packet counts for visibility"""
    
    def __init__(self):
        self.pcap_dir = os.path.join(os.path.dirname(__file__), 'data_capture/mininet')
        os.makedirs(self.pcap_dir, exist_ok=True)
        
    def create_topology(self):
        """Create a minimal network topology"""
        net = Mininet(switch=OVSSwitch, link=TCLink, autoSetMacs=True, autoStaticArp=True)
        
        # Add one switch and multiple hosts for more realistic traffic
        s1 = net.addSwitch('s1')
        h1 = net.addHost('h1', ip='10.0.0.1/24')  # Attacker
        h2 = net.addHost('h2', ip='10.0.0.2/24')  # Victim
        h3 = net.addHost('h3', ip='10.0.0.3/24')  # Additional host
        
        net.addLink(h1, s1)
        net.addLink(h2, s1)
        net.addLink(h3, s1)
        
        return net
    
    def start_capture(self, net, filename):
        """Start packet capture"""
        pcap_path = os.path.join(self.pcap_dir, filename)
        s1 = net.get('s1')
        # Capture for longer duration
        s1.cmd(f'timeout 30 tcpdump -i s1-eth1 -w {pcap_path} &')
        return pcap_path
    
    def stop_capture(self):
        """Stop packet capture"""
        subprocess.run(['pkill', '-9', 'tcpdump'], stderr=subprocess.DEVNULL)
        time.sleep(1)
    
    def generate_syn_flood(self, net):
        """Generate intensive SYN flood - 500+ packets"""
        info('  Generating intensive SYN flood (500+ packets)...\n')
        h1 = net.get('h1')
        h2 = net.get('h2')
        h3 = net.get('h3')
        
        # Start listener on victim
        h2.cmd('nc -l 80 > /dev/null 2>&1 &')
        time.sleep(0.5)
        
        # Generate SYN flood from multiple sources
        info('    Phase 1: Low intensity (100 packets)...\n')
        for i in range(100):
            h1.cmd('python3 -c "from scapy.all import *; send(IP(dst=\'10.0.0.2\')/TCP(dport=80,flags=\'S\'), verbose=0)" > /dev/null 2>&1 &')
            if i % 10 == 0:
                time.sleep(0.05)
        
        time.sleep(1)
        
        info('    Phase 2: Medium intensity (200 packets)...\n')
        for i in range(200):
            h1.cmd('python3 -c "from scapy.all import *; send(IP(dst=\'10.0.0.2\')/TCP(dport=80,flags=\'S\'), verbose=0)" > /dev/null 2>&1 &')
            h3.cmd('python3 -c "from scapy.all import *; send(IP(dst=\'10.0.0.2\')/TCP(dport=443,flags=\'S\'), verbose=0)" > /dev/null 2>&1 &')
            if i % 10 == 0:
                time.sleep(0.05)
        
        time.sleep(1)
        
        info('    Phase 3: High intensity (200 packets)...\n')
        for i in range(200):
            h1.cmd('python3 -c "from scapy.all import *; send(IP(dst=\'10.0.0.2\')/TCP(dport=80,flags=\'S\'), verbose=0)" > /dev/null 2>&1 &')
            if i % 5 == 0:
                time.sleep(0.02)
        
        time.sleep(2)
        h2.cmd('pkill -9 nc')
        info('    ✓ Generated ~500 SYN flood packets\n')
    
    def generate_port_scan(self, net):
        """Generate comprehensive port scan - 300+ packets"""
        info('  Generating comprehensive port scan (300+ packets)...\n')
        h1 = net.get('h1')
        h3 = net.get('h3')
        
        # Scan common ports multiple times
        common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 
                       3306, 3389, 5432, 5900, 8080, 8443, 9090]
        
        info('    Phase 1: Sequential scan...\n')
        for port in common_ports:
            for i in range(3):  # Scan each port 3 times
                h1.cmd(f'nc -zv -w 1 10.0.0.2 {port} > /dev/null 2>&1 &')
                time.sleep(0.1)
        
        time.sleep(1)
        
        info('    Phase 2: Parallel scan from multiple sources...\n')
        for port in common_ports:
            for i in range(5):  # Scan each port 5 more times
                h1.cmd(f'nc -zv -w 1 10.0.0.2 {port} > /dev/null 2>&1 &')
                h3.cmd(f'nc -zv -w 1 10.0.0.2 {port} > /dev/null 2>&1 &')
                time.sleep(0.05)
        
        time.sleep(2)
        info('    ✓ Generated ~300 port scan packets\n')
    
    def generate_udp_flood(self, net):
        """Generate intensive UDP flood - 400+ packets"""
        info('  Generating intensive UDP flood (400+ packets)...\n')
        h1 = net.get('h1')
        h3 = net.get('h3')
        
        # Target multiple UDP ports
        udp_ports = [53, 123, 161, 500, 1900, 5353]
        
        info('    Phase 1: DNS flood (150 packets)...\n')
        for i in range(150):
            h1.cmd('echo "FLOOD_DATA_DNS" | nc -u 10.0.0.2 53 > /dev/null 2>&1 &')
            if i % 10 == 0:
                time.sleep(0.05)
        
        time.sleep(1)
        
        info('    Phase 2: Multi-port UDP flood (250 packets)...\n')
        for i in range(50):
            for port in udp_ports:
                h1.cmd(f'echo "FLOOD_DATA" | nc -u 10.0.0.2 {port} > /dev/null 2>&1 &')
                h3.cmd(f'echo "FLOOD_DATA" | nc -u 10.0.0.2 {port} > /dev/null 2>&1 &')
            if i % 5 == 0:
                time.sleep(0.05)
        
        time.sleep(2)
        info('    ✓ Generated ~400 UDP flood packets\n')
    
    def generate_http_flood(self, net):
        """Generate intensive HTTP flood - 300+ packets"""
        info('  Generating intensive HTTP flood (300+ packets)...\n')
        h1 = net.get('h1')
        h2 = net.get('h2')
        h3 = net.get('h3')
        
        # Start web server
        h2.cmd('python3 -m http.server 80 > /dev/null 2>&1 &')
        time.sleep(1)
        
        info('    Phase 1: GET flood (150 requests)...\n')
        for i in range(150):
            h1.cmd('curl -s http://10.0.0.2 > /dev/null &')
            if i % 10 == 0:
                time.sleep(0.1)
        
        time.sleep(1)
        
        info('    Phase 2: Parallel GET flood (150 requests)...\n')
        for i in range(75):
            h1.cmd('curl -s http://10.0.0.2 > /dev/null &')
            h3.cmd('curl -s http://10.0.0.2 > /dev/null &')
            if i % 5 == 0:
                time.sleep(0.1)
        
        time.sleep(2)
        h2.cmd('pkill -9 python3')
        info('    ✓ Generated ~300 HTTP flood packets\n')
    
    def generate_pcap(self, name, traffic_func):
        """Generate a single PCAP file"""
        # Clean up
        os.system('mn -c > /dev/null 2>&1')
        time.sleep(0.5)
        
        # Create network
        net = self.create_topology()
        net.start()
        
        # Start capture
        pcap_file = f'{name}.pcap'
        pcap_path = self.start_capture(net, pcap_file)
        
        time.sleep(1)
        
        # Generate traffic
        traffic_func(net)
        
        time.sleep(3)  # Extra time to capture all packets
        
        # Stop
        self.stop_capture()
        net.stop()
        
        return pcap_file, pcap_path
    
    def generate_all(self):
        """Generate all attack PCAPs"""
        print("\n" + "="*70)
        print("ENHANCED ATTACK PCAP GENERATION")
        print("Generating high-volume attack traffic for better visibility")
        print("="*70 + "\n")
        
        # Clean up
        info('Cleaning up...\n')
        os.system('mn -c > /dev/null 2>&1')
        
        pcaps = []
        
        # Attacks with high packet counts
        attacks = [
            ('syn_flood', self.generate_syn_flood, '500+ SYN packets', 1),
            ('port_scan', self.generate_port_scan, '300+ scan packets', 2),
            ('udp_flood', self.generate_udp_flood, '400+ UDP packets', 3),
            ('http_flood', self.generate_http_flood, '300+ HTTP requests', 4),
        ]
        
        for name, func, desc, idx in attacks:
            print(f"[{idx}/4] Generating {name.upper()} ({desc})...")
            pcap_file, pcap_path = self.generate_pcap(name, func)
            pcaps.append((pcap_file, pcap_path))
            
            # Verify packet count
            if os.path.exists(pcap_path):
                try:
                    result = subprocess.run(
                        ['tcpdump', '-r', pcap_path, '-n'],
                        capture_output=True,
                        text=True
                    )
                    packet_count = len(result.stdout.strip().split('\n')) if result.stdout else 0
                    size = os.path.getsize(pcap_path)
                    print(f"✓ {pcap_file} ({size:,} bytes, ~{packet_count} packets)\n")
                except:
                    size = os.path.getsize(pcap_path)
                    print(f"✓ {pcap_file} ({size:,} bytes)\n")
            else:
                print(f"✗ {pcap_file} (generation failed)\n")
        
        # Final cleanup
        os.system('mn -c > /dev/null 2>&1')
        
        print("="*70)
        print("COMPLETE!")
        print("="*70)
        print(f"\nPCAPs saved to: {self.pcap_dir}\n")
        
        total_size = 0
        for pcap_file, pcap_path in pcaps:
            if os.path.exists(pcap_path):
                size = os.path.getsize(pcap_path)
                total_size += size
                
                # Get packet count
                try:
                    result = subprocess.run(
                        ['tcpdump', '-r', pcap_path, '-n'],
                        capture_output=True,
                        text=True
                    )
                    packet_count = len(result.stdout.strip().split('\n')) if result.stdout else 0
                    print(f"  ✓ {pcap_file:20s} {size:8,} bytes  ~{packet_count:4d} packets")
                except:
                    print(f"  ✓ {pcap_file:20s} {size:8,} bytes")
            else:
                print(f"  ✗ {pcap_file:20s} (not found)")
        
        print(f"\nTotal size: {total_size:,} bytes")
        print("\nThese PCAPs will generate significantly more alerts during replay!")
        print("Next: Test with Mininet Simulation in the dashboard")

def main():
    if os.geteuid() != 0:
        print("Error: This script requires root privileges")
        print("Run with: sudo python3 generate_enhanced_attack_pcaps.py")
        sys.exit(1)
    
    setLogLevel('info')
    
    generator = EnhancedAttackPCAPGenerator()
    generator.generate_all()

if __name__ == '__main__':
    main()
