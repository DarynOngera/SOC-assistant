#!/usr/bin/env python3
"""
Generate UDP Flood Attack with IPv4 Traffic
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

class UdpFloodIPv4Generator:
    """Generate UDP flood attack with IPv4 traffic"""
    
    def __init__(self, output_file, n_samples=10000):
        self.output_file = output_file
        self.n_samples = n_samples
        self.net = None
        
    def create_topology(self):
        """Create attack topology with explicit IPv4"""
        info('*** Creating UDP flood topology (IPv4)\n')
        
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
        
        # Add attacker and victim with explicit IPv4
        attacker = self.net.addHost('attacker', ip='10.0.1.10/24')
        victim = self.net.addHost('victim', ip='10.0.1.100/24')
        
        # Connect to switch
        self.net.addLink(attacker, s1)
        self.net.addLink(victim, s1)
        
        return attacker, victim
    
    def generate_attack(self):
        """Generate UDP flood attack with IPv4"""
        info(f'*** Generating {self.n_samples} UDP flood samples (IPv4)\n')
        
        attacker, victim = self.create_topology()
        
        self.net.start()
        time.sleep(2)
        
        # Disable IPv6 on both hosts
        info('*** Disabling IPv6\n')
        attacker.cmd('sysctl -w net.ipv6.conf.all.disable_ipv6=1 > /dev/null 2>&1')
        attacker.cmd('sysctl -w net.ipv6.conf.default.disable_ipv6=1 > /dev/null 2>&1')
        victim.cmd('sysctl -w net.ipv6.conf.all.disable_ipv6=1 > /dev/null 2>&1')
        victim.cmd('sysctl -w net.ipv6.conf.default.disable_ipv6=1 > /dev/null 2>&1')
        time.sleep(1)
        
        # Start packet capture on victim
        info('*** Starting packet capture\n')
        victim.cmd(f'tcpdump -i victim-eth0 -w {self.output_file} ip &')
        time.sleep(2)
        
        # Start UDP listener on victim
        info('*** Starting UDP listener on victim\n')
        victim.cmd('nc -u -l -p 53 > /dev/null 2>&1 &')
        time.sleep(1)
        
        # Generate UDP flood with hping3 (IPv4)
        info('*** Launching UDP flood attack (IPv4)\n')
        
        # Use smaller batches to avoid hanging
        total_sent = 0
        batch_size = 1000
        
        while total_sent < self.n_samples:
            remaining = min(batch_size, self.n_samples - total_sent)
            info(f'  Sending batch: {remaining} packets ({total_sent}/{self.n_samples})\n')
            
            # Use -4 flag to force IPv4, --udp for UDP mode, timeout to prevent hanging
            attacker.cmd(f'timeout 10 hping3 -4 --udp -p 53 --faster --rand-source -c {remaining} {victim.IP()} > /dev/null 2>&1')
            total_sent += remaining
            time.sleep(1)
        
        time.sleep(3)  # Let capture finish
        
        # Stop capture and listener
        victim.cmd('killall tcpdump')
        victim.cmd('killall nc')
        
        self.net.stop()
        info(f'*** UDP flood capture saved to {self.output_file}\n')
        
        # Verify IPv4 content
        info('*** Verifying IPv4 content\n')
        result = os.popen(f'tcpdump -r {self.output_file} -c 5 2>&1 | grep "IP " | wc -l').read().strip()
        if int(result) > 0:
            info(f'✓ Verified: {result} IPv4 packets found\n')
        else:
            info('✗ WARNING: No IPv4 packets found!\n')

def main():
    parser = argparse.ArgumentParser(description='Generate UDP flood attack traffic (IPv4)')
    parser.add_argument('--samples', type=int, default=10000, help='Number of samples')
    parser.add_argument('--output', type=str, 
                       default='../data_capture/mininet/udp_flood.pcap',
                       help='Output PCAP file')
    
    args = parser.parse_args()
    
    # Check if running as root
    if os.geteuid() != 0:
        print("ERROR: This script must be run as root (use sudo)")
        sys.exit(1)
    
    setLogLevel('info')
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    generator = UdpFloodIPv4Generator(args.output, args.samples)
    generator.generate_attack()
    
    print("\n" + "="*60)
    print("UDP FLOOD PCAP GENERATED (IPv4)")
    print("="*60)
    print(f"Output: {args.output}")
    print(f"Samples: {args.samples}")
    print("\nVerify with: tcpdump -r {} -c 10".format(args.output))
    print("="*60)

if __name__ == '__main__':
    main()
