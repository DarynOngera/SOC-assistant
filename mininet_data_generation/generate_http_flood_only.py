#!/usr/bin/env python3
"""
Lightweight HTTP Flood PCAP Generator
Memory-efficient version that won't get killed
"""

import os
import sys
import time
import subprocess
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info

def generate_http_flood():
    """Generate HTTP flood with memory-efficient approach"""
    pcap_dir = os.path.join(os.path.dirname(__file__), 'data_capture/mininet')
    os.makedirs(pcap_dir, exist_ok=True)
    
    # Clean up
    os.system('mn -c > /dev/null 2>&1')
    time.sleep(0.5)
    
    # Create network
    net = Mininet(switch=OVSSwitch, link=TCLink, autoSetMacs=True, autoStaticArp=True)
    
    s1 = net.addSwitch('s1')
    h1 = net.addHost('h1', ip='10.0.0.1/24')
    h2 = net.addHost('h2', ip='10.0.0.2/24')
    
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    
    net.start()
    
    # Start capture
    pcap_file = os.path.join(pcap_dir, 'http_flood.pcap')
    s1.cmd(f'timeout 30 tcpdump -i s1-eth1 -w {pcap_file} &')
    time.sleep(1)
    
    # Start web server
    info('Starting web server...\n')
    h2.cmd('python3 -m http.server 80 > /dev/null 2>&1 &')
    time.sleep(2)
    
    # Generate HTTP flood in smaller batches to avoid memory issues
    info('Generating HTTP flood (300 requests in batches)...\n')
    
    # Batch 1: 100 requests with delays
    info('  Batch 1/3 (100 requests)...\n')
    for i in range(100):
        h1.cmd('curl -s http://10.0.0.2 > /dev/null &')
        if i % 10 == 0:
            time.sleep(0.5)  # Wait for processes to complete
    
    time.sleep(2)
    
    # Batch 2: 100 requests
    info('  Batch 2/3 (100 requests)...\n')
    for i in range(100):
        h1.cmd('curl -s http://10.0.0.2 > /dev/null &')
        if i % 10 == 0:
            time.sleep(0.5)
    
    time.sleep(2)
    
    # Batch 3: 100 requests
    info('  Batch 3/3 (100 requests)...\n')
    for i in range(100):
        h1.cmd('curl -s http://10.0.0.2 > /dev/null &')
        if i % 10 == 0:
            time.sleep(0.5)
    
    time.sleep(3)
    
    # Cleanup
    h2.cmd('pkill -9 python3')
    subprocess.run(['pkill', '-9', 'tcpdump'], stderr=subprocess.DEVNULL)
    time.sleep(1)
    
    net.stop()
    
    # Verify
    if os.path.exists(pcap_file):
        size = os.path.getsize(pcap_file)
        try:
            result = subprocess.run(
                ['tcpdump', '-r', pcap_file, '-n'],
                capture_output=True,
                text=True
            )
            packet_count = len([line for line in result.stdout.strip().split('\n') if line])
            print(f"\n✓ http_flood.pcap generated: {size:,} bytes, ~{packet_count} packets\n")
        except:
            print(f"\n✓ http_flood.pcap generated: {size:,} bytes\n")
    else:
        print("\n✗ Failed to generate http_flood.pcap\n")
    
    # Final cleanup
    os.system('mn -c > /dev/null 2>&1')

def main():
    if os.geteuid() != 0:
        print("Error: Run with sudo")
        sys.exit(1)
    
    setLogLevel('info')
    
    print("\n" + "="*60)
    print("LIGHTWEIGHT HTTP FLOOD PCAP GENERATOR")
    print("="*60 + "\n")
    
    generate_http_flood()
    
    print("="*60)
    print("COMPLETE!")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
