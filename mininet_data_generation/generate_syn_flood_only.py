#!/usr/bin/env python3
"""
Lightweight SYN Flood PCAP Generator
Fixed version with proper packet capture
"""

import os
import sys
import time
import subprocess
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info

def generate_syn_flood():
    """Generate SYN flood with proper capture"""
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
    
    # Start capture on switch interface
    pcap_file = os.path.join(pcap_dir, 'syn_flood.pcap')
    info(f'Starting packet capture: {pcap_file}\n')
    
    # Capture on switch with longer timeout
    s1.cmd(f'tcpdump -i s1-eth1 -w {pcap_file} &')
    capture_pid = s1.cmd('echo $!').strip()
    time.sleep(2)
    
    # Start listener on victim
    info('Starting listener on victim...\n')
    h2.cmd('nc -l 80 > /dev/null 2>&1 &')
    time.sleep(1)
    
    # Generate SYN flood in controlled batches
    info('Generating SYN flood (500 packets in batches)...\n')
    
    # Batch 1: 150 packets
    info('  Batch 1/3 (150 SYN packets)...\n')
    for i in range(150):
        h1.cmd('python3 -c "from scapy.all import *; send(IP(dst=\'10.0.0.2\')/TCP(dport=80,flags=\'S\'), verbose=0)" > /dev/null 2>&1')
        if i % 20 == 0:
            time.sleep(0.2)
    
    time.sleep(1)
    
    # Batch 2: 200 packets
    info('  Batch 2/3 (200 SYN packets)...\n')
    for i in range(200):
        h1.cmd('python3 -c "from scapy.all import *; send(IP(dst=\'10.0.0.2\')/TCP(dport=80,flags=\'S\'), verbose=0)" > /dev/null 2>&1')
        if i % 20 == 0:
            time.sleep(0.2)
    
    time.sleep(1)
    
    # Batch 3: 150 packets
    info('  Batch 3/3 (150 SYN packets)...\n')
    for i in range(150):
        h1.cmd('python3 -c "from scapy.all import *; send(IP(dst=\'10.0.0.2\')/TCP(dport=80,flags=\'S\'), verbose=0)" > /dev/null 2>&1')
        if i % 20 == 0:
            time.sleep(0.2)
    
    time.sleep(3)
    
    # Stop capture
    info('Stopping capture...\n')
    s1.cmd(f'kill {capture_pid}')
    time.sleep(1)
    
    # Cleanup
    h2.cmd('pkill -9 nc')
    subprocess.run(['pkill', '-9', 'tcpdump'], stderr=subprocess.DEVNULL)
    
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
            print(f"\n✓ syn_flood.pcap generated: {size:,} bytes, ~{packet_count} packets\n")
        except:
            print(f"\n✓ syn_flood.pcap generated: {size:,} bytes\n")
    else:
        print("\n✗ Failed to generate syn_flood.pcap\n")
    
    # Final cleanup
    os.system('mn -c > /dev/null 2>&1')

def main():
    if os.geteuid() != 0:
        print("Error: Run with sudo")
        sys.exit(1)
    
    setLogLevel('info')
    
    print("\n" + "="*60)
    print("LIGHTWEIGHT SYN FLOOD PCAP GENERATOR")
    print("="*60 + "\n")
    
    generate_syn_flood()
    
    print("="*60)
    print("COMPLETE!")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
