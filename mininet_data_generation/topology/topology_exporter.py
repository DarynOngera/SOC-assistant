#!/usr/bin/env python3
"""
Topology Exporter for Mininet Network
Exports network topology structure for dashboard visualization
"""

import json
import os
from datetime import datetime


class TopologyExporter:
    """Export Mininet topology to JSON for dashboard integration"""
    
    def __init__(self, output_dir='../data_capture'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def export_topology(self):
        """Export the Mininet topology structure"""
        
        # Define the topology structure matching generate_normal_traffic.py
        topology = {
            'metadata': {
                'name': 'SOC Training Network',
                'description': 'Mininet-based network topology for SOC analysis',
                'created_at': datetime.now().isoformat(),
                'version': '1.0'
            },
            'switches': [
                {
                    'id': 's1',
                    'name': 'Server Switch',
                    'type': 'OVSSwitch',
                    'segment': 'servers',
                    'position': {'x': 500, 'y': 200}
                },
                {
                    'id': 's2',
                    'name': 'Client Switch',
                    'type': 'OVSSwitch',
                    'segment': 'clients',
                    'position': {'x': 300, 'y': 400}
                },
                {
                    'id': 's3',
                    'name': 'Internal Switch',
                    'type': 'OVSSwitch',
                    'segment': 'internal',
                    'position': {'x': 700, 'y': 400}
                }
            ],
            'hosts': [
                # Server segment (10.0.1.x)
                {
                    'id': 'h1',
                    'name': 'Web Server',
                    'ip': '10.0.1.1',
                    'subnet': '10.0.1.0/24',
                    'type': 'server',
                    'services': ['HTTP', 'HTTPS'],
                    'ports': [80, 443],
                    'segment': 'servers',
                    'switch': 's1',
                    'position': {'x': 400, 'y': 100}
                },
                {
                    'id': 'h2',
                    'name': 'FTP Server',
                    'ip': '10.0.1.2',
                    'subnet': '10.0.1.0/24',
                    'type': 'server',
                    'services': ['FTP'],
                    'ports': [21],
                    'segment': 'servers',
                    'switch': 's1',
                    'position': {'x': 500, 'y': 100}
                },
                {
                    'id': 'h3',
                    'name': 'DNS Server',
                    'ip': '10.0.1.3',
                    'subnet': '10.0.1.0/24',
                    'type': 'server',
                    'services': ['DNS'],
                    'ports': [53],
                    'segment': 'servers',
                    'switch': 's1',
                    'position': {'x': 600, 'y': 100}
                },
                # Client segment (10.0.2.x)
                {
                    'id': 'h4',
                    'name': 'Client 1',
                    'ip': '10.0.2.1',
                    'subnet': '10.0.2.0/24',
                    'type': 'client',
                    'services': [],
                    'ports': [],
                    'segment': 'clients',
                    'switch': 's2',
                    'position': {'x': 200, 'y': 500}
                },
                {
                    'id': 'h5',
                    'name': 'Client 2',
                    'ip': '10.0.2.2',
                    'subnet': '10.0.2.0/24',
                    'type': 'client',
                    'services': [],
                    'ports': [],
                    'segment': 'clients',
                    'switch': 's2',
                    'position': {'x': 300, 'y': 500}
                },
                {
                    'id': 'h6',
                    'name': 'Client 3',
                    'ip': '10.0.2.3',
                    'subnet': '10.0.2.0/24',
                    'type': 'client',
                    'services': [],
                    'ports': [],
                    'segment': 'clients',
                    'switch': 's2',
                    'position': {'x': 350, 'y': 550}
                },
                {
                    'id': 'h7',
                    'name': 'Client 4',
                    'ip': '10.0.2.4',
                    'subnet': '10.0.2.0/24',
                    'type': 'client',
                    'services': [],
                    'ports': [],
                    'segment': 'clients',
                    'switch': 's2',
                    'position': {'x': 250, 'y': 550}
                },
                # Internal segment (10.0.3.x)
                {
                    'id': 'h8',
                    'name': 'Database Server',
                    'ip': '10.0.3.1',
                    'subnet': '10.0.3.0/24',
                    'type': 'server',
                    'services': ['MySQL'],
                    'ports': [3306],
                    'segment': 'internal',
                    'switch': 's3',
                    'position': {'x': 650, 'y': 500}
                },
                {
                    'id': 'h9',
                    'name': 'File Server',
                    'ip': '10.0.3.2',
                    'subnet': '10.0.3.0/24',
                    'type': 'server',
                    'services': ['SMB', 'NFS'],
                    'ports': [445, 2049],
                    'segment': 'internal',
                    'switch': 's3',
                    'position': {'x': 750, 'y': 500}
                },
                {
                    'id': 'h10',
                    'name': 'Mail Server',
                    'ip': '10.0.3.3',
                    'subnet': '10.0.3.0/24',
                    'type': 'server',
                    'services': ['SMTP', 'IMAP'],
                    'ports': [25, 143],
                    'segment': 'internal',
                    'switch': 's3',
                    'position': {'x': 800, 'y': 550}
                }
            ],
            'links': [
                # Host to switch links
                {'source': 'h1', 'target': 's1', 'bandwidth': 100, 'type': 'access'},
                {'source': 'h2', 'target': 's1', 'bandwidth': 100, 'type': 'access'},
                {'source': 'h3', 'target': 's1', 'bandwidth': 100, 'type': 'access'},
                {'source': 'h4', 'target': 's2', 'bandwidth': 10, 'type': 'access'},
                {'source': 'h5', 'target': 's2', 'bandwidth': 10, 'type': 'access'},
                {'source': 'h6', 'target': 's2', 'bandwidth': 10, 'type': 'access'},
                {'source': 'h7', 'target': 's2', 'bandwidth': 10, 'type': 'access'},
                {'source': 'h8', 'target': 's3', 'bandwidth': 100, 'type': 'access'},
                {'source': 'h9', 'target': 's3', 'bandwidth': 100, 'type': 'access'},
                {'source': 'h10', 'target': 's3', 'bandwidth': 100, 'type': 'access'},
                # Inter-switch links
                {'source': 's1', 'target': 's2', 'bandwidth': 1000, 'type': 'trunk'},
                {'source': 's2', 'target': 's3', 'bandwidth': 1000, 'type': 'trunk'},
                {'source': 's1', 'target': 's3', 'bandwidth': 1000, 'type': 'trunk'}
            ],
            'segments': [
                {
                    'id': 'servers',
                    'name': 'Server Segment',
                    'subnet': '10.0.1.0/24',
                    'color': '#10b981',
                    'description': 'Public-facing servers (Web, FTP, DNS)'
                },
                {
                    'id': 'clients',
                    'name': 'Client Segment',
                    'subnet': '10.0.2.0/24',
                    'color': '#3b82f6',
                    'description': 'Client workstations'
                },
                {
                    'id': 'internal',
                    'name': 'Internal Segment',
                    'subnet': '10.0.3.0/24',
                    'color': '#8b5cf6',
                    'description': 'Internal servers (Database, File, Mail)'
                }
            ]
        }
        
        # Save to file
        output_file = os.path.join(self.output_dir, 'mininet_topology.json')
        with open(output_file, 'w') as f:
            json.dump(topology, f, indent=2)
        
        print(f"✅ Topology exported to: {output_file}")
        return output_file


def main():
    """Main function"""
    print("="*60)
    print("MININET TOPOLOGY EXPORTER")
    print("="*60)
    
    exporter = TopologyExporter()
    output_file = exporter.export_topology()
    
    print("\n" + "="*60)
    print("EXPORT COMPLETED")
    print("="*60)
    print(f"Topology file: {output_file}")
    print("\nNext steps:")
    print("1. Start the dashboard server")
    print("2. Navigate to Network Map")
    print("3. View your Mininet topology")
    print("="*60)


if __name__ == '__main__':
    main()
