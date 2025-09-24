#!/usr/bin/env python3
"""
Generate sample network data for testing the Network Map functionality
Creates realistic network alerts with diverse IP patterns and attack types
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timedelta
import random
import json
from src.database.mongodb_dal import get_dal
from src.database.schemas import AlertSeverity, AlertStatus

class NetworkDataGenerator:
    def __init__(self):
        self.dal = get_dal()
        
        # Define logical network topology with coherent subnets
        self.network_topology = {
            # Corporate network segments
            "dmz": {
                "subnet": "10.1.0.{}",
                "description": "DMZ - Web servers, mail servers",
                "hosts": list(range(10, 50)),  # 10.1.0.10-49
                "services": [80, 443, 25, 110, 143]
            },
            "internal": {
                "subnet": "192.168.1.{}",
                "description": "Internal corporate network", 
                "hosts": list(range(10, 100)),  # 192.168.1.10-99
                "services": [22, 80, 443, 445, 3389]
            },
            "servers": {
                "subnet": "10.0.1.{}",
                "description": "Server farm",
                "hosts": list(range(10, 30)),  # 10.0.1.10-29
                "services": [22, 80, 443, 1433, 3306, 5432]
            },
            "management": {
                "subnet": "172.16.1.{}",
                "description": "Management network",
                "hosts": list(range(10, 20)),  # 172.16.1.10-19
                "services": [22, 161, 443, 8080]
            },
            "guest": {
                "subnet": "192.168.100.{}",
                "description": "Guest network",
                "hosts": list(range(100, 200)),  # 192.168.100.100-199
                "services": [80, 443]
            }
        }
        
        # External threat actors and legitimate services
        self.external_networks = {
            "threat_actors": {
                "ips": ["185.220.100.{}", "45.142.214.{}", "91.219.236.{}"],
                "description": "Known threat actor ranges"
            },
            "cloud_services": {
                "ips": ["52.84.230.{}", "13.107.42.{}", "151.101.193.{}"],
                "description": "Legitimate cloud services"
            },
            "cdn_services": {
                "ips": ["104.16.132.{}", "185.199.108.{}", "198.51.100.{}"],
                "description": "CDN and web services"
            }
        }
        
        self.attack_types = [
            "Brute Force", "Port Scan", "SQL Injection", "DDoS",
            "Malware Communication", "Data Exfiltration", "Lateral Movement",
            "Privilege Escalation", "Command Injection", "Cross-Site Scripting"
        ]
        
        self.common_ports = [22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 1433, 3389, 5432, 8080]
        
    def generate_ip(self, ip_type="internal", network_segment=None):
        """Generate a logical IP address based on network topology"""
        if ip_type == "internal":
            if network_segment and network_segment in self.network_topology:
                segment = self.network_topology[network_segment]
                host_id = random.choice(segment["hosts"])
                return segment["subnet"].format(host_id)
            else:
                # Random internal segment
                segment_name = random.choice(list(self.network_topology.keys()))
                segment = self.network_topology[segment_name]
                host_id = random.choice(segment["hosts"])
                return segment["subnet"].format(host_id)
        else:  # external
            network_type = random.choice(list(self.external_networks.keys()))
            network = self.external_networks[network_type]
            subnet = random.choice(network["ips"])
            return subnet.format(random.randint(1, 254))
    
    def generate_attack_scenario(self, scenario_type="random"):
        """Generate realistic attack scenarios with logical network flow"""
        scenarios = {
            "brute_force": {
                "attack_type": "Brute Force",
                "src_type": "external",
                "dst_segment": "dmz",  # Target DMZ servers
                "dst_ports": [22, 23, 3389],
                "severity_weights": {"critical": 0.3, "high": 0.5, "medium": 0.2},
                "connection_count": (5, 50)
            },
            "port_scan": {
                "attack_type": "Port Scan", 
                "src_type": "external",
                "dst_segment": random.choice(["dmz", "internal"]),
                "dst_ports": list(range(1, 1024)),
                "severity_weights": {"medium": 0.6, "low": 0.4},
                "connection_count": (10, 100)
            },
            "lateral_movement": {
                "attack_type": "Lateral Movement",
                "src_segment": "internal",  # Compromised internal host
                "dst_segment": "servers",   # Moving to servers
                "dst_ports": [445, 135, 139, 22],
                "severity_weights": {"critical": 0.4, "high": 0.6},
                "connection_count": (3, 15)
            },
            "data_exfiltration": {
                "attack_type": "Data Exfiltration",
                "src_segment": "servers",   # From compromised server
                "dst_type": "external",     # To external C2
                "dst_ports": [80, 443, 53],
                "severity_weights": {"critical": 0.7, "high": 0.3},
                "connection_count": (2, 10)
            },
            "malware_c2": {
                "attack_type": "Malware Communication",
                "src_segment": random.choice(["internal", "dmz"]),
                "dst_type": "external", 
                "dst_ports": [80, 443, 8080],
                "severity_weights": {"critical": 0.5, "high": 0.4, "medium": 0.1},
                "connection_count": (1, 5)
            },
            "privilege_escalation": {
                "attack_type": "Privilege Escalation",
                "src_segment": "internal",
                "dst_segment": "management",  # Targeting management network
                "dst_ports": [22, 3389, 443],
                "severity_weights": {"critical": 0.6, "high": 0.4},
                "connection_count": (1, 8)
            },
            "web_attack": {
                "attack_type": "SQL Injection",
                "src_type": "external",
                "dst_segment": "dmz",  # Web servers in DMZ
                "dst_ports": [80, 443],
                "severity_weights": {"high": 0.5, "medium": 0.3, "critical": 0.2},
                "connection_count": (1, 20)
            }
        }
        
        if scenario_type == "random":
            scenario_type = random.choice(list(scenarios.keys()))
        
        return scenarios.get(scenario_type, scenarios["brute_force"])
    
    def generate_severity(self, weights):
        """Generate severity based on weights"""
        severities = list(weights.keys())
        weights_list = list(weights.values())
        return random.choices(severities, weights=weights_list)[0]
    
    def generate_network_alerts(self, count=200):
        """Generate diverse network alerts"""
        alerts = []
        base_time = datetime.utcnow() - timedelta(hours=24)
        
        print(f"Generating {count} network alerts...")
        
        # Generate different attack scenarios with new types
        scenario_distribution = {
            "brute_force": 0.20,
            "port_scan": 0.15, 
            "lateral_movement": 0.15,
            "data_exfiltration": 0.12,
            "malware_c2": 0.12,
            "privilege_escalation": 0.10,
            "web_attack": 0.10,
            "random": 0.06
        }
        
        for i in range(count):
            # Select scenario based on distribution
            scenario_type = random.choices(
                list(scenario_distribution.keys()),
                weights=list(scenario_distribution.values())
            )[0]
            
            scenario = self.generate_attack_scenario(scenario_type)
            
            # Generate source and destination IPs with logical network flow
            src_type = scenario.get("src_type")
            dst_type = scenario.get("dst_type")
            src_segment = scenario.get("src_segment")
            dst_segment = scenario.get("dst_segment")
            
            # Generate source IP
            if src_type:
                src_ip = self.generate_ip(src_type)
            elif src_segment:
                src_ip = self.generate_ip("internal", src_segment)
            else:
                src_ip = self.generate_ip("external")
            
            # Generate destination IP  
            if dst_type:
                dst_ip = self.generate_ip(dst_type)
            elif dst_segment:
                dst_ip = self.generate_ip("internal", dst_segment)
            else:
                dst_ip = self.generate_ip("internal")
            
            # Generate ports
            src_port = random.randint(1024, 65535)
            dst_port = random.choice(scenario["dst_ports"])
            
            # Generate severity and score
            severity = self.generate_severity(scenario["severity_weights"])
            
            # Score based on severity
            score_ranges = {
                "critical": (0.8, 1.0),
                "high": (0.6, 0.8),
                "medium": (0.4, 0.6),
                "low": (0.1, 0.4)
            }
            min_score, max_score = score_ranges[severity]
            anomaly_score = random.uniform(min_score, max_score)
            
            # Generate timestamp (spread over last 24 hours)
            time_offset = random.randint(0, 24 * 60 * 60)  # seconds in 24 hours
            timestamp = base_time + timedelta(seconds=time_offset)
            
            # Create alert
            alert_data = {
                "timestamp": timestamp,
                "severity": severity,
                "status": random.choice([AlertStatus.NEW.value, AlertStatus.INVESTIGATING.value, AlertStatus.RESOLVED.value]),
                "source_ip": src_ip,
                "destination_ip": dst_ip,
                "source_port": src_port,
                "destination_port": dst_port,
                "attack_type": scenario["attack_type"],
                "anomaly_score": round(anomaly_score, 3),
                "confidence": round(random.uniform(0.7, 0.99), 3),
                "description": f"{scenario['attack_type']} detected from {src_ip} to {dst_ip}:{dst_port}",
                "protocol": random.choice(["tcp", "udp", "icmp"]),
                "packet_count": random.randint(1, 1000),
                "byte_count": random.randint(64, 1048576)
            }
            
            alerts.append(alert_data)
            
            if (i + 1) % 50 == 0:
                print(f"Generated {i + 1}/{count} alerts...")
        
        return alerts
    
    def create_network_clusters(self):
        """Create realistic network clusters and patterns"""
        clusters = []
        
        # Corporate network cluster
        corporate_ips = [f"192.168.1.{i}" for i in range(10, 50)]
        clusters.append({
            "name": "Corporate Network",
            "ips": corporate_ips,
            "attack_types": ["Lateral Movement", "Privilege Escalation"],
            "threat_level": "medium"
        })
        
        # DMZ cluster
        dmz_ips = [f"10.0.1.{i}" for i in range(10, 30)]
        clusters.append({
            "name": "DMZ Servers",
            "ips": dmz_ips, 
            "attack_types": ["Port Scan", "SQL Injection", "DDoS"],
            "threat_level": "high"
        })
        
        # External threat actors
        threat_ips = [self.generate_ip("external") for _ in range(20)]
        clusters.append({
            "name": "External Threats",
            "ips": threat_ips,
            "attack_types": ["Brute Force", "Malware Communication", "Data Exfiltration"],
            "threat_level": "critical"
        })
        
        return clusters
    
    def populate_database(self, alert_count=200):
        """Populate database with sample network data"""
        print("🗺️  Generating Sample Network Data for Network Map Testing")
        print("=" * 60)
        
        try:
            # Generate alerts
            alerts = self.generate_network_alerts(alert_count)
            
            # Insert alerts into database
            print(f"\n📊 Inserting {len(alerts)} alerts into database...")
            success_count = 0
            
            for alert in alerts:
                try:
                    success, message, alert_id = self.dal.create_alert(**alert)
                    if success:
                        success_count += 1
                    else:
                        print(f"Failed to create alert: {message}")
                except Exception as e:
                    print(f"Error creating alert: {e}")
            
            print(f"✅ Successfully inserted {success_count}/{len(alerts)} alerts")
            
            # Generate network statistics
            clusters = self.create_network_clusters()
            print(f"\n🏢 Created {len(clusters)} network clusters:")
            for cluster in clusters:
                print(f"   • {cluster['name']}: {len(cluster['ips'])} IPs ({cluster['threat_level']} threat level)")
            
            # Generate summary statistics
            internal_ips = set()
            external_ips = set()
            attack_type_counts = {}
            
            for alert in alerts:
                src_ip = alert['source_ip']
                dst_ip = alert['destination_ip']
                attack_type = alert['attack_type']
                
                # Classify IPs
                if self.is_internal_ip(src_ip):
                    internal_ips.add(src_ip)
                else:
                    external_ips.add(src_ip)
                    
                if self.is_internal_ip(dst_ip):
                    internal_ips.add(dst_ip)
                else:
                    external_ips.add(dst_ip)
                
                # Count attack types
                attack_type_counts[attack_type] = attack_type_counts.get(attack_type, 0) + 1
            
            print(f"\n📈 Network Statistics:")
            print(f"   • Total unique internal IPs: {len(internal_ips)}")
            print(f"   • Total unique external IPs: {len(external_ips)}")
            print(f"   • Attack type distribution:")
            for attack_type, count in sorted(attack_type_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"     - {attack_type}: {count} alerts")
            
            print(f"\n🎯 Network Map Test Data Ready!")
            print(f"   • Run the network map test: python test_network_map.py")
            print(f"   • Access the network map in the dashboard UI")
            print(f"   • API endpoints are populated with realistic data")
            
            return True
            
        except Exception as e:
            print(f"❌ Error populating database: {e}")
            return False
    
    def is_internal_ip(self, ip):
        """Check if IP is internal"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        try:
            first = int(parts[0])
            second = int(parts[1])
            
            # Private IP ranges
            if first == 192 and second == 168:
                return True
            elif first == 10:
                return True
            elif first == 172 and 16 <= second <= 31:
                return True
            elif first == 127:
                return True
            
            return False
        except:
            return False
    
    def cleanup_old_data(self):
        """Clean up old test data"""
        print("🧹 Cleaning up old test data...")
        
        try:
            # Delete alerts older than 7 days
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            # Note: This would require implementing a cleanup method in the DAL
            # For now, we'll just print the intention
            print(f"   • Would delete alerts older than {cutoff_date}")
            print(f"   • Keeping recent data for testing")
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")

def main():
    generator = NetworkDataGenerator()
    
    print("Network Map Sample Data Generator")
    print("This script generates realistic network alerts for testing the network map functionality.")
    print()
    
    # Ask for confirmation
    response = input("Generate sample network data? (y/N): ").lower().strip()
    
    if response in ['y', 'yes']:
        # Generate data
        success = generator.populate_database(alert_count=300)
        
        if success:
            print("\n🎉 Sample data generation completed successfully!")
            print("\nNext steps:")
            print("1. Start the SOC Dashboard server")
            print("2. Run: python test_network_map.py")
            print("3. Open the dashboard and navigate to 'Network Map'")
        else:
            print("\n❌ Sample data generation failed. Check the error messages above.")
    else:
        print("Sample data generation cancelled.")

if __name__ == "__main__":
    main()
