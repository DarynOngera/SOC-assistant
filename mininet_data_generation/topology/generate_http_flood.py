#!/usr/bin/env python3
"""
Mininet HTTP Flood Attack Generation
"""

import os
import sys
import time
import argparse
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info

class HttpFloodGenerator:
    """Generate HTTP flood attack traffic"""
    
    def __init__(self, output_file, n_samples=5000):
        self.output_file = output_file
        self.n_samples = n_samples
        self.net = None
        
    def create_topology(self):
        """Create attack topology"""
        info('*** Creating HTTP flood topology\n')
        
        self.net = Mininet(
            switch=OVSSwitch,
            link=TCLink,
            autoSetMacs=True,
            autoStaticArp=True,
            controller=None
        )
        
        s1 = self.net.addSwitch('s1')
        attacker = self.net.addHost('attacker', ip='192.168.100.40/24')
        webserver = self.net.addHost('webserver', ip='10.0.1.80/24')
        
        self.net.addLink(attacker, s1)
        self.net.addLink(webserver, s1)
        
        return attacker, webserver
    
    def generate_attack(self):
        """Generate HTTP flood attack"""
        info(f'*** Generating {self.n_samples} HTTP flood samples\n')
        
        attacker, webserver = self.create_topology()
        self.net.start()
        
        # Start simple HTTP server on webserver
        info('*** Starting HTTP server\n')
        webserver.cmd('python3 -m http.server 80 &')
        time.sleep(2)
        
        # Start capture
        info('*** Starting packet capture\n')
        webserver.cmd(f'tcpdump -i webserver-eth0 -w {self.output_file} &')
        time.sleep(2)
        
        # Generate HTTP flood with ab (Apache Bench) or curl
        info('*** Launching HTTP flood\n')
        
        # Use curl in a loop for HTTP flood
        attacker.cmd(f'''
        for i in $(seq 1 {self.n_samples}); do
            curl -s http://{webserver.IP()}/ > /dev/null &
        done
        wait
        ''')
        
        time.sleep(5)
        webserver.cmd('killall tcpdump')
        webserver.cmd('killall python3')
        
        self.net.stop()
        info(f'*** HTTP flood capture saved to {self.output_file}\n')

def main():
    parser = argparse.ArgumentParser(description='Generate HTTP flood attack traffic')
    parser.add_argument('--samples', type=int, default=5000, help='Number of samples')
    parser.add_argument('--output', type=str, required=True, help='Output PCAP file')
    
    args = parser.parse_args()
    setLogLevel('info')
    
    generator = HttpFloodGenerator(args.output, args.samples)
    generator.generate_attack()

if __name__ == '__main__':
    main()
