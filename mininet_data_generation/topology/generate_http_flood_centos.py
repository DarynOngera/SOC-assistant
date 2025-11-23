#!/usr/bin/env python3
"""
CentOS-Compatible HTTP Flood Generator
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

class CentOSHttpFloodGenerator:
    """Generate HTTP flood compatible with CentOS"""
    
    def __init__(self, output_file, n_samples=500):
        self.output_file = output_file
        self.n_samples = n_samples
        self.net = None
        self.has_ab = self._check_ab()
        
    def _check_ab(self):
        """Check if Apache Bench (ab) is available"""
        try:
            subprocess.run(['which', 'ab'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL, 
                         check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def create_topology(self):
        """Create attack topology with explicit IPv4"""
        info('*** Creating HTTP flood topology (IPv4)\n')
        
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
        """Generate HTTP flood using available tools"""
        info(f'*** Generating {self.n_samples} HTTP flood samples (CentOS)\n')
        
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
        
        # Generate HTTP flood
        if self.has_ab:
            info('*** Launching HTTP flood with Apache Bench (IPv4)\n')
            self._generate_with_ab(attacker, victim)
        else:
            info('*** Launching HTTP flood with curl (IPv4)\n')
            self._generate_with_curl(attacker, victim)
        
        time.sleep(3)
        
        # Cleanup
        victim.cmd('killall tcpdump')
        victim.cmd('killall python3')
        attacker.cmd('killall ab curl wget')
        
        self.net.stop()
        info(f'*** HTTP flood capture saved to {self.output_file}\n')
        
        # Verify
        self._verify_pcap()
    
    def _generate_with_ab(self, attacker, victim):
        """Generate using Apache Bench"""
        info(f'  Using Apache Bench: {self.n_samples} requests\n')
        attacker.cmd(f'timeout 20 ab -n {self.n_samples} -c 50 http://{victim.IP()}/ > /dev/null 2>&1')
    
    def _generate_with_curl(self, attacker, victim):
        """Generate using curl (fallback)"""
        info(f'  Using curl: {self.n_samples} requests\n')
        
        for i in range(min(self.n_samples, 500)):
            attacker.cmd(f'curl -s --max-time 2 http://{victim.IP()}/ > /dev/null 2>&1 &')
            
            if i % 50 == 0 and i > 0:
                info(f'  Progress: {i}/{min(self.n_samples, 500)}\n')
                time.sleep(0.2)
    
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
    parser = argparse.ArgumentParser(description='Generate HTTP flood (CentOS compatible)')
    parser.add_argument('--samples', type=int, default=500, help='Number of samples')
    parser.add_argument('--output', type=str, 
                       default='../data_capture/mininet/http_flood.pcap',
                       help='Output PCAP file')
    
    args = parser.parse_args()
    
    if os.geteuid() != 0:
        print("ERROR: This script must be run as root (use sudo)")
        sys.exit(1)
    
    setLogLevel('info')
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    generator = CentOSHttpFloodGenerator(args.output, args.samples)
    generator.generate_attack()
    
    print("\n" + "="*60)
    print("HTTP FLOOD PCAP GENERATED (CentOS)")
    print("="*60)
    print(f"Output: {args.output}")
    print(f"Samples: {args.samples}")
    print(f"Method: {'Apache Bench' if generator.has_ab else 'curl'}")
    print("\nVerify with: tcpdump -r {} -c 10".format(args.output))
    print("="*60)

if __name__ == '__main__':
    main()
