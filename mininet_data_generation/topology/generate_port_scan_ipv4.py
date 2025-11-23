#!/usr/bin/env python3
"""
Generate Port Scan Attack with IPv4 Traffic
Properly configured for IPv4 to match training data
"""

import os
import sys
import time
import argparse
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info

class PortScanIPv4Generator:
    """Generate port scan attack with IPv4 traffic"""
    
    def __init__(self, output_file, n_samples=5000):
        self.output_file = output_file
        self.n_samples = n_samples
        self.net = None
        
    def create_topology(self):
        """Create attack topology with explicit IPv4"""
        info('*** Creating port scan topology (IPv4)\n')
        
        self.net = Mininet(
            switch=OVSSwitch,
            link=TCLink,
            autoSetMacs=True,
            autoStaticArp=True,
            controller=None,
            ipBase='10.0.0.0/8'  # Force IPv4 base
        )
        
        # Add switch
        s1 = self.net.addSwitch('s1')
        
        # Add scanner and target with explicit IPv4
        scanner = self.net.addHost('scanner', ip='10.0.1.10/24')
        target = self.net.addHost('target', ip='10.0.1.100/24')
        
        # Connect to switch
        self.net.addLink(scanner, s1)
        self.net.addLink(target, s1)
        
        return scanner, target
    
    def generate_attack(self):
        """Generate port scan attack with IPv4"""
        info(f'*** Generating {self.n_samples} port scan samples (IPv4)\n')
        
        scanner, target = self.create_topology()
        
        self.net.start()
        time.sleep(2)
        
        # Disable IPv6 on both hosts
        info('*** Disabling IPv6\n')
        scanner.cmd('sysctl -w net.ipv6.conf.all.disable_ipv6=1 > /dev/null 2>&1')
        scanner.cmd('sysctl -w net.ipv6.conf.default.disable_ipv6=1 > /dev/null 2>&1')
        target.cmd('sysctl -w net.ipv6.conf.all.disable_ipv6=1 > /dev/null 2>&1')
        target.cmd('sysctl -w net.ipv6.conf.default.disable_ipv6=1 > /dev/null 2>&1')
        time.sleep(1)
        
        # Start packet capture on target
        info('*** Starting packet capture\n')
        target.cmd(f'tcpdump -i target-eth0 -w {self.output_file} ip &')
        time.sleep(2)
        
        # Generate port scan with nmap (IPv4)
        info('*** Launching port scan attack (IPv4)\n')
        
        # Use timeout to prevent hanging
        info('  Scanning ports 1-1000 (fast scan)\n')
        scanner.cmd(f'timeout 15 nmap -4 -p 1-1000 --max-rate 500 {target.IP()} > /dev/null 2>&1')
        
        info('  Scanning common ports (SYN scan)\n')
        scanner.cmd(f'timeout 10 nmap -4 -sS -p 21,22,23,25,80,443,3306,3389,8080 --max-rate 100 {target.IP()} > /dev/null 2>&1')
        
        info('  Scanning high ports (quick)\n')
        scanner.cmd(f'timeout 15 nmap -4 -p 8000-9000 --max-rate 500 {target.IP()} > /dev/null 2>&1')
        
        time.sleep(2)  # Brief pause
        
        # Stop capture
        target.cmd('killall tcpdump')
        target.cmd('killall nmap')
        scanner.cmd('killall nmap')
        
        self.net.stop()
        info(f'*** Port scan capture saved to {self.output_file}\n')
        
        # Verify IPv4 content
        info('*** Verifying IPv4 content\n')
        result = os.popen(f'tcpdump -r {self.output_file} -c 5 2>&1 | grep "IP " | wc -l').read().strip()
        if int(result) > 0:
            info(f'✓ Verified: {result} IPv4 packets found\n')
        else:
            info('✗ WARNING: No IPv4 packets found!\n')

def main():
    parser = argparse.ArgumentParser(description='Generate port scan attack traffic (IPv4)')
    parser.add_argument('--samples', type=int, default=5000, help='Number of samples')
    parser.add_argument('--output', type=str, 
                       default='../data_capture/mininet/port_scan.pcap',
                       help='Output PCAP file')
    
    args = parser.parse_args()
    
    # Check if running as root
    if os.geteuid() != 0:
        print("ERROR: This script must be run as root (use sudo)")
        sys.exit(1)
    
    setLogLevel('info')
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    generator = PortScanIPv4Generator(args.output, args.samples)
    generator.generate_attack()
    
    print("\n" + "="*60)
    print("PORT SCAN PCAP GENERATED (IPv4)")
    print("="*60)
    print(f"Output: {args.output}")
    print(f"Samples: {args.samples}")
    print("\nVerify with: tcpdump -r {} -c 10".format(args.output))
    print("="*60)

if __name__ == '__main__':
    main()
