#!/usr/bin/env python3
"""
Mininet SYN Flood Attack Generation
"""

import os
import sys
import time
import random
import argparse
import subprocess
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info

class SynFloodGenerator:
    """Generate SYN flood attack traffic"""
    
    def __init__(self, output_file, n_samples=10000):
        self.output_file = output_file
        self.n_samples = n_samples
        self.net = None
        
    def create_topology(self):
        """Create attack topology"""
        info('*** Creating SYN flood topology\n')
        
        self.net = Mininet(
            switch=OVSSwitch,
            link=TCLink,
            autoSetMacs=True,
            autoStaticArp=True,
            controller=None
        )
        
        # Add switch
        s1 = self.net.addSwitch('s1')
        
        # Add attacker and victim
        attacker = self.net.addHost('attacker', ip='192.168.100.10/24')
        victim = self.net.addHost('victim', ip='10.0.1.100/24')
        
        # Connect to switch
        self.net.addLink(attacker, s1)
        self.net.addLink(victim, s1)
        
        return attacker, victim
    
    def generate_attack(self):
        """Generate SYN flood attack"""
        info(f'*** Generating {self.n_samples} SYN flood samples\n')
        
        attacker, victim = self.create_topology()
        
        self.net.start()
        
        # Start packet capture on victim
        info('*** Starting packet capture\n')
        victim.cmd(f'tcpdump -i victim-eth0 -w {self.output_file} &')
        time.sleep(2)
        
        # Generate SYN flood with hping3
        info('*** Launching SYN flood attack\n')
        
        # Calculate packets per intensity level
        n_per_intensity = self.n_samples // 3
        
        for intensity, rate in [('low', 100), ('medium', 500), ('high', 1000)]:
            info(f'  {intensity} intensity: {rate} pps\n')
            attacker.cmd(f'hping3 -S -p 80 --flood --rand-source -c {n_per_intensity} {victim.IP()} &')
            time.sleep(n_per_intensity / rate)
        
        time.sleep(5)  # Let capture finish
        
        # Stop capture
        victim.cmd('killall tcpdump')
        
        self.net.stop()
        info(f'*** SYN flood capture saved to {self.output_file}\n')

def main():
    parser = argparse.ArgumentParser(description='Generate SYN flood attack traffic')
    parser.add_argument('--samples', type=int, default=10000, help='Number of samples')
    parser.add_argument('--output', type=str, required=True, help='Output PCAP file')
    
    args = parser.parse_args()
    
    setLogLevel('info')
    
    generator = SynFloodGenerator(args.output, args.samples)
    generator.generate_attack()

if __name__ == '__main__':
    main()
