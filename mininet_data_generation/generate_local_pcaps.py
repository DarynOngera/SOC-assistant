#!/usr/bin/env python3
"""
Local PCAP Generator for Parrot OS
Generates both normal and attack traffic PCAPs using Mininet
"""

import os
import sys
import time
import subprocess
from datetime import datetime
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info

class LocalPCAPGenerator:
    """Generate normal and attack PCAPs locally"""
    
    def __init__(self):
        self.pcap_dir = os.path.join(os.path.dirname(__file__), 'data_capture/pcaps')
        os.makedirs(self.pcap_dir, exist_ok=True)
        
    def create_topology(self):
        """Create a simple network topology"""
        info('*** Creating network topology\n')
        
        # Create network without controller (not needed for traffic generation)
        net = Mininet(
            switch=OVSSwitch,
            link=TCLink,
            autoSetMacs=True,
            autoStaticArp=True
        )
        
        # Add switches
        info('*** Adding switches\n')
        s1 = net.addSwitch('s1')
        s2 = net.addSwitch('s2')
        
        # Add hosts
        info('*** Adding hosts\n')
        h1 = net.addHost('h1', ip='10.0.1.1/24')
        h2 = net.addHost('h2', ip='10.0.1.2/24')
        h3 = net.addHost('h3', ip='10.0.2.1/24')
        h4 = net.addHost('h4', ip='10.0.2.2/24')
        
        # Add links
        info('*** Adding links\n')
        net.addLink(h1, s1)
        net.addLink(h2, s1)
        net.addLink(s1, s2)
        net.addLink(h3, s2)
        net.addLink(h4, s2)
        
        return net
    
    def start_capture(self, net, filename):
        """Start packet capture on all switches"""
        info(f'*** Starting packet capture: {filename}\n')
        
        pcap_path = os.path.join(self.pcap_dir, filename)
        
        # Capture on switch s1
        s1 = net.get('s1')
        s1.cmd(f'tcpdump -i s1-eth1 -w {pcap_path} &')
        
        return pcap_path
    
    def stop_capture(self, net):
        """Stop packet capture"""
        info('*** Stopping packet capture\n')
        
        # Kill tcpdump processes
        subprocess.run(['pkill', '-9', 'tcpdump'], stderr=subprocess.DEVNULL)
        time.sleep(1)
    
    def generate_normal_traffic(self, net):
        """Generate normal network traffic"""
        info('*** Generating normal traffic\n')
        
        h1 = net.get('h1')
        h2 = net.get('h2')
        h3 = net.get('h3')
        h4 = net.get('h4')
        
        # HTTP traffic
        info('  - HTTP requests\n')
        h3.cmd('python3 -m http.server 80 &')
        time.sleep(1)
        for _ in range(10):
            h1.cmd('curl -s http://10.0.2.1 > /dev/null &')
            time.sleep(0.5)
        
        # Ping traffic
        info('  - Ping traffic\n')
        for _ in range(20):
            h1.cmd('ping -c 1 10.0.1.2 > /dev/null &')
            h2.cmd('ping -c 1 10.0.2.1 > /dev/null &')
            time.sleep(0.3)
        
        # SSH-like traffic (using netcat)
        info('  - SSH-like traffic\n')
        h4.cmd('nc -l 22 > /dev/null &')
        time.sleep(0.5)
        for _ in range(5):
            h1.cmd('echo "test" | nc 10.0.2.2 22 &')
            time.sleep(0.5)
        
        # DNS-like traffic
        info('  - DNS-like traffic\n')
        for _ in range(15):
            h1.cmd('nslookup google.com > /dev/null 2>&1 &')
            time.sleep(0.4)
        
        # Wait for traffic to complete
        time.sleep(5)
        
        # Cleanup
        h3.cmd('pkill -9 python3')
        h4.cmd('pkill -9 nc')
        
        info('*** Normal traffic generation complete\n')
    
    def generate_syn_flood(self, net):
        """Generate SYN flood attack"""
        info('*** Generating SYN flood attack\n')
        
        h1 = net.get('h1')
        h3 = net.get('h3')
        
        # Start a simple server
        h3.cmd('nc -l 80 > /dev/null &')
        time.sleep(1)
        
        # SYN flood using hping3 or scapy
        if os.system('which hping3 > /dev/null 2>&1') == 0:
            info('  - Using hping3 for SYN flood\n')
            h1.cmd('hping3 -S -p 80 --flood --rand-source 10.0.2.1 &')
            time.sleep(10)
            h1.cmd('pkill -9 hping3')
        else:
            info('  - Using Python/Scapy for SYN flood\n')
            # Generate SYN packets with scapy
            for _ in range(1000):
                h1.cmd(f'python3 -c "from scapy.all import *; send(IP(dst=\'10.0.2.1\')/TCP(dport=80,flags=\'S\'), verbose=0)" &')
                if _ % 100 == 0:
                    time.sleep(0.1)
        
        time.sleep(2)
        h3.cmd('pkill -9 nc')
        
        info('*** SYN flood complete\n')
    
    def generate_port_scan(self, net):
        """Generate port scan attack"""
        info('*** Generating port scan attack\n')
        
        h1 = net.get('h1')
        h3 = net.get('h3')
        
        # Scan common ports
        ports = [20, 21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3306, 3389, 8080]
        
        for port in ports:
            h1.cmd(f'nc -zv -w 1 10.0.2.1 {port} > /dev/null 2>&1 &')
            time.sleep(0.2)
        
        time.sleep(3)
        
        info('*** Port scan complete\n')
    
    def generate_udp_flood(self, net):
        """Generate UDP flood attack"""
        info('*** Generating UDP flood attack\n')
        
        h1 = net.get('h1')
        h3 = net.get('h3')
        
        # UDP flood
        for _ in range(500):
            h1.cmd('echo "FLOOD" | nc -u 10.0.2.1 53 &')
            if _ % 50 == 0:
                time.sleep(0.1)
        
        time.sleep(2)
        
        info('*** UDP flood complete\n')
    
    def generate_http_flood(self, net):
        """Generate HTTP flood attack"""
        info('*** Generating HTTP flood attack\n')
        
        h1 = net.get('h1')
        h2 = net.get('h2')
        h3 = net.get('h3')
        
        # Start HTTP server
        h3.cmd('python3 -m http.server 80 &')
        time.sleep(1)
        
        # HTTP flood
        for _ in range(200):
            h1.cmd('curl -s http://10.0.2.1 > /dev/null &')
            h2.cmd('curl -s http://10.0.2.1 > /dev/null &')
            if _ % 20 == 0:
                time.sleep(0.1)
        
        time.sleep(3)
        h3.cmd('pkill -9 python3')
        
        info('*** HTTP flood complete\n')
    
    def generate_icmp_flood(self, net):
        """Generate ICMP flood attack"""
        info('*** Generating ICMP flood attack\n')
        
        h1 = net.get('h1')
        h2 = net.get('h2')
        
        # ICMP flood
        h1.cmd('ping -f -c 1000 10.0.2.1 > /dev/null &')
        h2.cmd('ping -f -c 1000 10.0.2.1 > /dev/null &')
        
        time.sleep(5)
        
        info('*** ICMP flood complete\n')
    
    def generate_all_pcaps(self):
        """Generate all PCAP files"""
        print("\n" + "="*60)
        print("LOCAL PCAP GENERATION")
        print("="*60 + "\n")
        
        # Clean up any previous Mininet state
        info('*** Cleaning up previous Mininet state\n')
        os.system('mn -c > /dev/null 2>&1')
        
        # Generate normal traffic PCAP
        print("\n[1/6] Generating Normal Traffic PCAP...")
        net = self.create_topology()
        net.start()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pcap_file = f'normal_traffic_{timestamp}.pcap'
        self.start_capture(net, pcap_file)
        
        time.sleep(2)
        self.generate_normal_traffic(net)
        time.sleep(2)
        
        self.stop_capture(net)
        net.stop()
        
        print(f"✓ Normal traffic PCAP saved: {pcap_file}")
        
        # Generate attack PCAPs
        attacks = [
            ('syn_flood', self.generate_syn_flood, 2),
            ('port_scan', self.generate_port_scan, 3),
            ('udp_flood', self.generate_udp_flood, 4),
            ('http_flood', self.generate_http_flood, 5),
            ('icmp_flood', self.generate_icmp_flood, 6)
        ]
        
        for attack_name, attack_func, idx in attacks:
            print(f"\n[{idx}/6] Generating {attack_name.upper()} PCAP...")
            
            # Clean up
            os.system('mn -c > /dev/null 2>&1')
            time.sleep(1)
            
            # Create new network
            net = self.create_topology()
            net.start()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pcap_file = f'attack_{attack_name}_{timestamp}.pcap'
            self.start_capture(net, pcap_file)
            
            time.sleep(2)
            attack_func(net)
            time.sleep(2)
            
            self.stop_capture(net)
            net.stop()
            
            print(f"✓ {attack_name} PCAP saved: {pcap_file}")
        
        # Final cleanup
        os.system('mn -c > /dev/null 2>&1')
        
        print("\n" + "="*60)
        print("PCAP GENERATION COMPLETE!")
        print("="*60)
        print(f"\nPCAPs saved to: {self.pcap_dir}")
        print("\nGenerated files:")
        for f in sorted(os.listdir(self.pcap_dir)):
            if f.endswith('.pcap'):
                size = os.path.getsize(os.path.join(self.pcap_dir, f))
                print(f"  • {f} ({size:,} bytes)")
        
        print("\nNext steps:")
        print("  1. Start the dashboard: cd src/dashboard && python3 server.py")
        print("  2. Test simulations from the frontend")
        print("  3. Verify alerts are generated correctly")

def main():
    # Check if running as root
    if os.geteuid() != 0:
        print("Error: This script must be run as root (use sudo)")
        sys.exit(1)
    
    # Set Mininet log level
    setLogLevel('info')
    
    # Generate PCAPs
    generator = LocalPCAPGenerator()
    generator.generate_all_pcaps()

if __name__ == '__main__':
    main()
