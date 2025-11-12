#!/usr/bin/env python3
"""
Mininet Port Scan Attack Generation
"""

import os
import sys
import time
import argparse
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info

class PortScanGenerator:
    """Generate port scan attack traffic"""
    
    def __init__(self, output_file, n_samples=10000):
        self.output_file = output_file
        self.n_samples = n_samples
        self.net = None
        
    def create_topology(self):
        """Create attack topology"""
        info('*** Creating port scan topology\n')
        
        self.net = Mininet(
            switch=OVSSwitch,
            link=TCLink,
            autoSetMacs=True,
            autoStaticArp=True,
            controller=None
        )
        
        s1 = self.net.addSwitch('s1')
        attacker = self.net.addHost('attacker', ip='192.168.100.20/24')
        victim = self.net.addHost('victim', ip='10.0.1.100/24')
        
        self.net.addLink(attacker, s1)
        self.net.addLink(victim, s1)
        
        return attacker, victim
    
    def generate_attack(self):
        """Generate port scan attack"""
        info(f'*** Generating {self.n_samples} port scan samples\n')
        
        attacker, victim = self.create_topology()
        self.net.start()
        
        # Start capture
        info('*** Starting packet capture\n')
        victim.cmd(f'tcpdump -i victim-eth0 -w {self.output_file} &')
        time.sleep(2)
        
        # Generate port scans with nmap
        info('*** Launching port scan\n')
        
        # Different scan types
        scan_types = [
            f'-sS -p 1-1000',  # SYN scan
            f'-sT -p 1000-2000',  # TCP connect scan
            f'-sU -p 1-500',  # UDP scan
        ]
        
        for scan_type in scan_types:
            attacker.cmd(f'nmap {scan_type} {victim.IP()} &')
            time.sleep(3)
        
        time.sleep(5)
        victim.cmd('killall tcpdump')
        
        self.net.stop()
        info(f'*** Port scan capture saved to {self.output_file}\n')

def main():
    parser = argparse.ArgumentParser(description='Generate port scan attack traffic')
    parser.add_argument('--samples', type=int, default=10000, help='Number of samples')
    parser.add_argument('--output', type=str, required=True, help='Output PCAP file')
    
    args = parser.parse_args()
    setLogLevel('info')
    
    generator = PortScanGenerator(args.output, args.samples)
    generator.generate_attack()

if __name__ == '__main__':
    main()
