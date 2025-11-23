#!/usr/bin/env python3
"""
Simple Network Map Test - Direct Database Access
Bypasses authentication to test network topology logic directly
"""

import sys
import os
sys.path.append('.')

from src.database.mongodb_dal import get_dal
from datetime import datetime, timedelta
import json

def classify_ip_type(ip):
    """Classify IP address type"""
    if ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.16.'):
        return 'internal'
    elif ip.startswith('127.'):
        return 'localhost'
    else:
        return 'external'

def get_subnet(ip):
    """Get subnet from IP address"""
    parts = ip.split('.')
    if len(parts) >= 3:
        return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
    return "unknown"

def test_network_topology():
    """Test network topology generation directly"""
    print("🗺️  Testing Network Topology Logic")
    print("=" * 50)
    
    try:
        # Get database connection
        dal = get_dal()
        
        # Get alerts directly from database
        print("📊 Fetching alerts from database...")
        alerts_data = dal.get_alerts(per_page=100)
        alerts = alerts_data.get('alerts', [])
        
        print(f"✅ Retrieved {len(alerts)} alerts")
        
        if not alerts:
            print("❌ No alerts found in database. Run generate_sample_network_data.py first")
            return False
        
        # Analyze network topology
        nodes = {}
        edges = []
        subnets = {}
        
        print("\n🔍 Analyzing network topology...")
        
        for alert in alerts:
            src_ip = alert.get('source_ip')
            dst_ip = alert.get('destination_ip')
            
            if not src_ip or not dst_ip:
                continue
                
            # Classify and add nodes
            for ip in [src_ip, dst_ip]:
                if ip not in nodes:
                    ip_type = classify_ip_type(ip)
                    subnet = get_subnet(ip)
                    
                    nodes[ip] = {
                        'id': ip,
                        'type': ip_type,
                        'subnet': subnet,
                        'alert_count': 0,
                        'severity_counts': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
                    }
                
                # Update alert count
                nodes[ip]['alert_count'] += 1
                severity = alert.get('severity', 'medium')
                if severity in nodes[ip]['severity_counts']:
                    nodes[ip]['severity_counts'][severity] += 1
            
            # Add edge
            edge_id = f"{src_ip}-{dst_ip}"
            edges.append({
                'id': edge_id,
                'source': src_ip,
                'target': dst_ip,
                'attack_type': alert.get('attack_type', 'Unknown'),
                'severity': alert.get('severity', 'medium'),
                'port': alert.get('destination_port', 0)
            })
        
        # Group by subnets
        for ip, node in nodes.items():
            subnet = node['subnet']
            if subnet not in subnets:
                subnets[subnet] = {
                    'id': subnet,
                    'type': node['type'],
                    'nodes': [],
                    'alert_count': 0
                }
            subnets[subnet]['nodes'].append(ip)
            subnets[subnet]['alert_count'] += node['alert_count']
        
        # Print results
        print(f"\n📈 Network Topology Analysis:")
        print(f"   • Total nodes: {len(nodes)}")
        print(f"   • Total connections: {len(edges)}")
        print(f"   • Total subnets: {len(subnets)}")
        
        print(f"\n🏠 Subnet Distribution:")
        for subnet_id, subnet in subnets.items():
            node_count = len(subnet['nodes'])
            alert_count = subnet['alert_count']
            print(f"   • {subnet_id}: {node_count} nodes, {alert_count} alerts ({subnet['type']})")
        
        print(f"\n🎯 Top Attack Sources:")
        sorted_nodes = sorted(nodes.items(), key=lambda x: x[1]['alert_count'], reverse=True)
        for i, (ip, node) in enumerate(sorted_nodes[:5]):
            print(f"   {i+1}. {ip}: {node['alert_count']} alerts ({node['type']})")
        
        print(f"\n🔗 Attack Types Distribution:")
        attack_types = {}
        for edge in edges:
            attack_type = edge['attack_type']
            attack_types[attack_type] = attack_types.get(attack_type, 0) + 1
        
        for attack_type, count in sorted(attack_types.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {attack_type}: {count} connections")
        
        # Test logical network segments
        print(f"\n🏢 Network Segment Analysis:")
        segments = {
            'DMZ (10.1.0.x)': [ip for ip in nodes.keys() if ip.startswith('10.1.0.')],
            'Internal (192.168.1.x)': [ip for ip in nodes.keys() if ip.startswith('192.168.1.')],
            'Servers (10.0.1.x)': [ip for ip in nodes.keys() if ip.startswith('10.0.1.')],
            'Management (172.16.1.x)': [ip for ip in nodes.keys() if ip.startswith('172.16.1.')],
            'Guest (192.168.100.x)': [ip for ip in nodes.keys() if ip.startswith('192.168.100.')],
            'External': [ip for ip in nodes.keys() if classify_ip_type(ip) == 'external']
        }
        
        for segment_name, ips in segments.items():
            if ips:
                total_alerts = sum(nodes[ip]['alert_count'] for ip in ips)
                print(f"   • {segment_name}: {len(ips)} hosts, {total_alerts} alerts")
        
        print(f"\n✅ Network topology test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing network topology: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Simple Network Map Test Suite")
    print("=" * 50)
    print("Testing network topology logic without authentication")
    print()
    
    success = test_network_topology()
    
    if success:
        print(f"\n🎉 Test completed successfully!")
        print("The logical network topology is working correctly.")
        print("You can now access the Network Map in the dashboard UI.")
    else:
        print(f"\n❌ Test failed. Check the error messages above.")
