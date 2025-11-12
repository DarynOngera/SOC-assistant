#!/usr/bin/env python3
"""
Mininet Normal Traffic Generation
Simulates realistic benign network traffic for SOC training data
"""

import os
import sys
import time
import random
import subprocess
from datetime import datetime
from mininet.net import Mininet
from mininet.node import Controller, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink

class NormalTrafficGenerator:
    """Generate normal network traffic in Mininet"""
    
    def __init__(self, output_dir='../data_capture/pcaps'):
        self.output_dir = output_dir
        self.net = None
        self.capture_process = None
        os.makedirs(output_dir, exist_ok=True)
        
    def create_topology(self):
        """Create a realistic network topology"""
        info('*** Creating network topology\n')
        
        # Create network with custom link parameters
        # Use default controller or skip if not available
        self.net = Mininet(
            switch=OVSSwitch,
            link=TCLink,
            autoSetMacs=True,
            autoStaticArp=True,
            controller=None  # Don't require controller for simple traffic generation
        )
        
        # Add switches
        info('*** Adding switches\n')
        s1 = self.net.addSwitch('s1')
        s2 = self.net.addSwitch('s2')
        s3 = self.net.addSwitch('s3')
        
        # Add hosts (simulating different network segments)
        info('*** Adding hosts\n')
        # Web servers
        h1 = self.net.addHost('h1', ip='10.0.1.1/24')  # Web server
        h2 = self.net.addHost('h2', ip='10.0.1.2/24')  # FTP server
        h3 = self.net.addHost('h3', ip='10.0.1.3/24')  # DNS server
        
        # Client machines
        h4 = self.net.addHost('h4', ip='10.0.2.1/24')  # Client 1
        h5 = self.net.addHost('h5', ip='10.0.2.2/24')  # Client 2
        h6 = self.net.addHost('h6', ip='10.0.2.3/24')  # Client 3
        h7 = self.net.addHost('h7', ip='10.0.2.4/24')  # Client 4
        
        # Internal servers
        h8 = self.net.addHost('h8', ip='10.0.3.1/24')  # Database
        h9 = self.net.addHost('h9', ip='10.0.3.2/24')  # File server
        h10 = self.net.addHost('h10', ip='10.0.3.3/24') # Mail server
        
        # Create links with bandwidth constraints
        info('*** Creating links\n')
        # Server segment
        self.net.addLink(h1, s1, bw=100)
        self.net.addLink(h2, s1, bw=100)
        self.net.addLink(h3, s1, bw=100)
        
        # Client segment
        self.net.addLink(h4, s2, bw=10)
        self.net.addLink(h5, s2, bw=10)
        self.net.addLink(h6, s2, bw=10)
        self.net.addLink(h7, s2, bw=10)
        
        # Internal segment
        self.net.addLink(h8, s3, bw=100)
        self.net.addLink(h9, s3, bw=100)
        self.net.addLink(h10, s3, bw=100)
        
        # Inter-switch links
        self.net.addLink(s1, s2, bw=1000)
        self.net.addLink(s2, s3, bw=1000)
        self.net.addLink(s1, s3, bw=1000)
        
        return self.net
    
    def start_packet_capture(self, duration=300):
        """Start tcpdump packet capture"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pcap_file = os.path.join(self.output_dir, f'normal_traffic_{timestamp}.pcap')
        
        info(f'*** Starting packet capture: {pcap_file}\n')
        
        # Capture on all interfaces
        cmd = [
            'tcpdump',
            '-i', 'any',
            '-w', pcap_file,
            '-G', str(duration),  # Rotate after duration
            '-W', '1',  # Keep only 1 file
            'not arp and not stp'  # Filter out ARP and STP
        ]
        
        self.capture_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        info(f'*** Packet capture started (PID: {self.capture_process.pid})\n')
        return pcap_file
    
    def stop_packet_capture(self):
        """Stop packet capture"""
        if self.capture_process:
            info('*** Stopping packet capture\n')
            self.capture_process.terminate()
            self.capture_process.wait()
            self.capture_process = None
    
    def generate_http_traffic(self, client, server, duration=60):
        """Generate HTTP traffic"""
        info(f'*** Generating HTTP traffic: {client.name} -> {server.name}\n')
        
        # Start simple HTTP server on server host (use popen to avoid blocking)
        server.popen('python3 -m http.server 80')
        time.sleep(2)
        
        # Generate HTTP requests from client
        for i in range(duration):
            # Random delay between requests (1-5 seconds)
            delay = random.uniform(1, 5)
            client.popen(f'curl -s http://{server.IP()}/ -o /dev/null')
            time.sleep(delay)
        
        # Stop HTTP server
        server.popen('pkill -f "http.server"')
    
    def generate_ftp_traffic(self, client, server, duration=60):
        """Generate FTP-like traffic using netcat"""
        info(f'*** Generating FTP traffic: {client.name} -> {server.name}\n')
        
        # Start netcat server on FTP port
        server.popen('nc -l -p 21 > /dev/null')
        time.sleep(1)
        
        # Generate FTP-like connections
        for i in range(duration // 10):
            client.popen(f'echo "USER anonymous\nPASS test@test.com\nLIST\nQUIT" | nc {server.IP()} 21')
            time.sleep(random.uniform(5, 15))
        
        server.popen('pkill nc')
    
    def generate_dns_traffic(self, client, server, duration=60):
        """Generate DNS-like traffic"""
        info(f'*** Generating DNS traffic: {client.name} -> {server.name}\n')
        
        # Start netcat server on DNS port
        server.popen('nc -u -l -p 53 > /dev/null')
        time.sleep(1)
        
        # Generate DNS queries
        domains = ['example.com', 'google.com', 'github.com', 'stackoverflow.com', 'wikipedia.org']
        for i in range(duration * 2):  # More frequent DNS queries
            domain = random.choice(domains)
            client.popen(f'echo "{domain}" | nc -u {server.IP()} 53')
            time.sleep(random.uniform(0.5, 2))
        
        server.popen('pkill nc')
    
    def generate_ping_traffic(self, client, server, duration=60):
        """Generate ICMP ping traffic"""
        info(f'*** Generating ICMP traffic: {client.name} -> {server.name}\n')
        
        # Send pings with random intervals
        for i in range(duration // 5):
            client.popen(f'ping -c 3 {server.IP()} > /dev/null')
            time.sleep(random.uniform(3, 8))
    
    def generate_ssh_traffic(self, client, server, duration=60):
        """Generate SSH-like traffic (connection attempts)"""
        info(f'*** Generating SSH traffic: {client.name} -> {server.name}\n')
        
        # Start netcat server on SSH port
        server.popen('nc -l -p 22 > /dev/null')
        time.sleep(1)
        
        # Generate SSH-like connections
        for i in range(duration // 20):
            client.popen(f'nc -w 2 {server.IP()} 22 > /dev/null')
            time.sleep(random.uniform(15, 30))
        
        server.popen('pkill nc')
    
    def generate_database_traffic(self, client, server, duration=60):
        """Generate database-like traffic"""
        info(f'*** Generating database traffic: {client.name} -> {server.name}\n')
        
        # Start netcat server on MySQL port
        server.popen('nc -l -p 3306 > /dev/null')
        time.sleep(1)
        
        # Generate database-like queries
        for i in range(duration // 3):
            # Simulate query
            client.popen(f'echo "SELECT * FROM users" | nc -w 1 {server.IP()} 3306 > /dev/null')
            time.sleep(random.uniform(2, 5))
        
        server.popen('pkill nc')
    
    def run_normal_traffic_simulation(self, duration=60):
        """Run complete normal traffic simulation"""
        info('*** Starting normal traffic simulation\n')
        info(f'*** Duration: {duration} seconds\n')
        
        # Start network
        self.net.start()
        
        # Wait for network to stabilize
        info('*** Waiting for network to stabilize\n')
        time.sleep(5)
        
        # Start packet capture
        pcap_file = self.start_packet_capture(duration + 10)
        
        # Get hosts
        h1, h2, h3 = self.net.get('h1', 'h2', 'h3')  # Servers
        h4, h5, h6, h7 = self.net.get('h4', 'h5', 'h6', 'h7')  # Clients
        h8, h9, h10 = self.net.get('h8', 'h9', 'h10')  # Internal
        
        # Generate diverse traffic patterns concurrently
        import threading
        
        threads = []
        
        # HTTP traffic from multiple clients
        threads.append(threading.Thread(target=self.generate_http_traffic, args=(h4, h1, duration)))
        threads.append(threading.Thread(target=self.generate_http_traffic, args=(h5, h1, duration)))
        
        # FTP traffic
        threads.append(threading.Thread(target=self.generate_ftp_traffic, args=(h6, h2, duration)))
        
        # DNS traffic from all clients
        threads.append(threading.Thread(target=self.generate_dns_traffic, args=(h4, h3, duration)))
        threads.append(threading.Thread(target=self.generate_dns_traffic, args=(h5, h3, duration)))
        threads.append(threading.Thread(target=self.generate_dns_traffic, args=(h6, h3, duration)))
        
        # Ping traffic
        threads.append(threading.Thread(target=self.generate_ping_traffic, args=(h7, h1, duration)))
        threads.append(threading.Thread(target=self.generate_ping_traffic, args=(h7, h8, duration)))
        
        # SSH traffic
        threads.append(threading.Thread(target=self.generate_ssh_traffic, args=(h4, h8, duration)))
        
        # Database traffic
        threads.append(threading.Thread(target=self.generate_database_traffic, args=(h1, h8, duration)))
        threads.append(threading.Thread(target=self.generate_database_traffic, args=(h9, h8, duration)))
        
        # Start all traffic generation threads
        info('*** Starting traffic generation threads\n')
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        info('*** Waiting for traffic generation to complete\n')
        for thread in threads:
            thread.join()
        
        # Wait a bit more for capture to finish
        time.sleep(5)
        
        # Stop packet capture
        self.stop_packet_capture()
        
        info(f'*** Normal traffic simulation completed\n')
        info(f'*** Packet capture saved to: {pcap_file}\n')
        
        return pcap_file
    
    def cleanup(self):
        """Cleanup network"""
        if self.net:
            info('*** Stopping network\n')
            self.net.stop()

def main():
    """Main function"""
    setLogLevel('info')
    
    print("="*60)
    print("MININET NORMAL TRAFFIC GENERATION")
    print("="*60)
    
    # Check if running as root
    if os.geteuid() != 0:
        print("ERROR: This script must be run as root (use sudo)")
        sys.exit(1)
    
    # Create traffic generator
    generator = NormalTrafficGenerator()
    
    try:
        # Create topology
        generator.create_topology()
        
        # Run simulation (1 minute of traffic for faster testing)
        pcap_file = generator.run_normal_traffic_simulation(duration=60)
        
        print("\n" + "="*60)
        print("NORMAL TRAFFIC GENERATION COMPLETED")
        print("="*60)
        print(f"Packet capture: {pcap_file}")
        print("\nNext steps:")
        print("1. Generate attack traffic: sudo python generate_attack_traffic.py")
        print("2. Preprocess data: python ../data_capture/preprocess_pcap.py")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n*** Interrupted by user")
    except Exception as e:
        print(f"\n*** Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        generator.cleanup()

if __name__ == '__main__':
    main()
