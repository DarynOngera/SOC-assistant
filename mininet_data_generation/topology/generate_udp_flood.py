#!/usr/bin/env python3
"""
Mininet UDP Flood Attack Generation
"""

import os
import sys
import time
import argparse
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info

class UdpFloodGenerator:
    """Generate UDP flood attack traffic"""
    
    def __init__(self, output_file, n_samples=5000):
        self.output_file = output_file
        self.n_samples = n_samples
        self.net = None
        
    def create_topology(self):
        """Create attack topology"""
        info('*** Creating UDP flood topology\n')
        
        self.net = Mininet(
            switch=OVSSwitch,
            link=TCLink,
            autoSetMacs=True,
            autoStaticArp=True,
            controller=None
        )
        
        s1 = self.net.addSwitch('s1')
        attacker = self.net.addHost('attacker', ip='192.168.100.30/24')
        victim = self.net.addHost('victim', ip='10.0.1.100/24')
        
        self.net.addLink(attacker, s1)
        self.net.addLink(victim, s1)
        
        return attacker, victim
    
    def generate_attack(self):
        """Generate UDP flood attack"""
        info(f'*** Generating {self.n_samples} UDP flood samples\n')
        
        attacker, victim = self.create_topology()
        self.net.start()
        
        # Start capture
        info('*** Starting packet capture\n')
        victim.cmd(f'tcpdump -i victim-eth0 -w {self.output_file} &')
        time.sleep(2)
        
        # Generate UDP flood with hping3
        info('*** Launching UDP flood\n')
        attacker.cmd(f'hping3 --udp -p 53 --flood --rand-source -c {self.n_samples} {victim.IP()} &')
        
        time.sleep(10)
        victim.cmd('killall tcpdump')
        
        self.net.stop()
        info(f'*** UDP flood capture saved to {self.output_file}\n')

def main():
    parser = argparse.ArgumentParser(description='Generate UDP flood attack traffic')
    parser.add_argument('--samples', type=int, default=5000, help='Number of samples')
    parser.add_argument('--output', type=str, required=True, help='Output PCAP file')
    
    args = parser.parse_args()
    setLogLevel('info')
    
    generator = UdpFloodGenerator(args.output, args.samples)
    generator.generate_attack()

if __name__ == '__main__':
    main()
