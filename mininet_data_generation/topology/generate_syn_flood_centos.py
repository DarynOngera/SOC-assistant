#!/usr/bin/env python3
"""
CentOS-Compatible SYN Flood Generator
Handles CentOS-specific differences and missing tools
"""

import os
import sys
import time
import argparse
import subprocess
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info

class CentOSSynFloodGenerator:
    """Generate SYN flood compatible with CentOS"""
    
    def __init__(self, output_file, n_samples=1000):
        self.output_file = output_file
        self.n_samples = n_samples
        self.net = None
        self.has_hping = self._check_hping()
        
    def _check_hping(self):
        """Check if hping3 is available"""
        try:
            subprocess.run(['which', 'hping3'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL, 
                         check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def create_topology(self):
        """Create attack topology with explicit IPv4"""
        info('*** Creating SYN flood topology (IPv4)\n')
        
        self.net = Mininet(
            switch=OVSSwitch,
            link=TCLink,
            autoSetMacs=True,
            autoStaticArp=True,
            controller=None,
            ipBase='10.0.0.0/8'
        )
        
        s1 = self.net.addSwitch('s1')
        attacker = self.net.addHost('attacker', ip='10.0.1.10/24')
        victim = self.net.addHost('victim', ip='10.0.1.100/24')
        
        self.net.addLink(attacker, s1)
        self.net.addLink(victim, s1)
        
        return attacker, victim
    
    def generate_attack(self):
        """Generate SYN flood using available tools"""
        info(f'*** Generating {self.n_samples} SYN flood samples (CentOS)\n')
        
        attacker, victim = self.create_topology()
        self.net.start()
        time.sleep(2)
        
        # Disable IPv6
        info('*** Disabling IPv6\n')
        for host in [attacker, victim]:
            host.cmd('sysctl -w net.ipv6.conf.all.disable_ipv6=1 > /dev/null 2>&1')
            host.cmd('sysctl -w net.ipv6.conf.default.disable_ipv6=1 > /dev/null 2>&1')
        time.sleep(1)
        
        # Start capture
        info('*** Starting packet capture\n')
        victim.cmd(f'tcpdump -i victim-eth0 -w {self.output_file} ip &')
        time.sleep(2)
        
        # Start HTTP server
        info('*** Starting HTTP server on victim\n')
        victim.cmd('python3 -m http.server 80 > /dev/null 2>&1 &')
        time.sleep(2)
        
        # Generate SYN flood
        if self.has_hping:
            info('*** Launching SYN flood with hping3 (IPv4)\n')
            self._generate_with_hping(attacker, victim)
        else:
            info('*** Launching SYN flood with netcat (IPv4)\n')
            self._generate_with_netcat(attacker, victim)
        
        time.sleep(3)
        
        # Cleanup
        victim.cmd('killall tcpdump')
        victim.cmd('killall python3')
        attacker.cmd('killall hping3 nc')
        
        self.net.stop()
        info(f'*** SYN flood capture saved to {self.output_file}\n')
        
        # Verify
        self._verify_pcap()
    
    def _generate_with_hping(self, attacker, victim):
        """Generate using hping3"""
        total_sent = 0
        batch_size = 500
        
        while total_sent < self.n_samples:
            remaining = min(batch_size, self.n_samples - total_sent)
            info(f'  Batch: {remaining} packets ({total_sent}/{self.n_samples})\n')
            
            attacker.cmd(f'timeout 10 hping3 -4 -S -p 80 --faster -c {remaining} {victim.IP()} > /dev/null 2>&1')
            total_sent += remaining
            time.sleep(1)
    
    def _generate_with_netcat(self, attacker, victim):
        """Generate using netcat (fallback)"""
        info(f'  Sending {self.n_samples} connection attempts...\n')
        
        for i in range(self.n_samples):
            attacker.cmd(f'timeout 0.1 nc -w 1 {victim.IP()} 80 < /dev/null > /dev/null 2>&1 &')
            
            if i % 100 == 0 and i > 0:
                info(f'  Progress: {i}/{self.n_samples}\n')
                time.sleep(0.5)
    
    def _verify_pcap(self):
        """Verify PCAP has IPv4 content"""
        info('*** Verifying IPv4 content\n')
        try:
            result = os.popen(f'tcpdump -r {self.output_file} -c 5 2>&1 | grep "IP " | wc -l').read().strip()
            if int(result) > 0:
                info(f'✓ Verified: {result} IPv4 packets found\n')
                size = os.popen(f'du -h {self.output_file} | cut -f1').read().strip()
                info(f'✓ File size: {size}\n')
            else:
                info('✗ WARNING: No IPv4 packets found!\n')
        except Exception as e:
            info(f'⚠ Verification error: {e}\n')

def main():
    parser = argparse.ArgumentParser(description='Generate SYN flood (CentOS compatible)')
    parser.add_argument('--samples', type=int, default=1000, help='Number of samples')
    parser.add_argument('--output', type=str, 
                       default='../data_capture/mininet/syn_flood.pcap',
                       help='Output PCAP file')
    
    args = parser.parse_args()
    
    if os.geteuid() != 0:
        print("ERROR: This script must be run as root (use sudo)")
        sys.exit(1)
    
    setLogLevel('info')
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    generator = CentOSSynFloodGenerator(args.output, args.samples)
    generator.generate_attack()
    
    print("\n" + "="*60)
    print("SYN FLOOD PCAP GENERATED (CentOS)")
    print("="*60)
    print(f"Output: {args.output}")
    print(f"Samples: {args.samples}")
    print(f"Method: {'hping3' if generator.has_hping else 'netcat'}")
    print("\nVerify with: tcpdump -r {} -c 10".format(args.output))
    print("="*60)

if __name__ == '__main__':
    main()
