#!/usr/bin/env python3
"""
Reset MongoDB and Populate with Synthetic Dataset
Flushes existing data and loads new synthetic network data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pymongo import MongoClient
from src.database.mongodb_config import get_mongodb_client, get_mongodb_database

class MongoDBReset:
    """Reset and populate MongoDB with synthetic data"""
    
    def __init__(self):
        self.client = None
        self.db = None
        
    def connect(self):
        """Connect to MongoDB"""
        print("Connecting to MongoDB...")
        try:
            self.client = get_mongodb_client()
            self.db = get_mongodb_database()
            print("✓ Connected to MongoDB")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to MongoDB: {e}")
            return False
    
    def flush_database(self):
        """Flush all collections"""
        print("\nFlushing MongoDB database...")
        
        collections_to_flush = [
            'alerts',
            'audit_logs',
            'system_stats',
            'csv_uploads',
            'network_data'
        ]
        
        for collection_name in collections_to_flush:
            try:
                count = self.db[collection_name].count_documents({})
                if count > 0:
                    result = self.db[collection_name].delete_many({})
                    print(f"  ✓ Flushed {collection_name}: {result.deleted_count} documents")
                else:
                    print(f"  - {collection_name}: already empty")
            except Exception as e:
                print(f"  ✗ Error flushing {collection_name}: {e}")
        
        print("✓ Database flushed")
    
    def load_synthetic_dataset(self, csv_path):
        """Load synthetic dataset from CSV"""
        print(f"\nLoading synthetic dataset from: {csv_path}")
        
        try:
            df = pd.read_csv(csv_path)
            print(f"✓ Loaded {len(df)} samples")
            print(f"  Normal: {len(df[df['label'] == 0])}")
            print(f"  Attack: {len(df[df['label'] == 1])}")
            return df
        except Exception as e:
            print(f"✗ Failed to load dataset: {e}")
            return None
    
    def generate_alerts_from_dataset(self, df):
        """Convert dataset to alert documents"""
        print("\nGenerating alerts from dataset...")
        
        alerts = []
        base_time = datetime.now() - timedelta(days=7)  # Start from 7 days ago
        
        # Sample 1000 records for alerts (to avoid overwhelming the DB)
        sample_df = df.sample(n=min(1000, len(df)), random_state=42)
        
        for idx, row in sample_df.iterrows():
            # Generate timestamp
            timestamp = base_time + timedelta(
                seconds=random.randint(0, 7 * 24 * 3600)
            )
            
            # Determine severity based on attack type and anomaly score
            if row['label'] == 0:
                severity = 'low'
                status = 'resolved'
            else:
                attack_type = row.get('attack_type', 'unknown')
                if attack_type in ['syn_flood', 'udp_flood']:
                    severity = 'critical'
                elif attack_type in ['port_scan', 'http_flood']:
                    severity = 'high'
                else:
                    severity = 'medium'
                status = random.choice(['open', 'investigating', 'resolved'])
            
            # Generate IPs
            if 'src_ip' in row and pd.notna(row['src_ip']):
                source_ip = row['src_ip']
            else:
                source_ip = f"10.0.{random.randint(1,3)}.{random.randint(1,254)}"
            
            if 'dst_ip' in row and pd.notna(row['dst_ip']):
                destination_ip = row['dst_ip']
            else:
                destination_ip = f"10.0.{random.randint(1,3)}.{random.randint(1,254)}"
            
            # Create alert document
            alert = {
                'timestamp': timestamp,
                'severity': severity,
                'status': status,
                'source_ip': source_ip,
                'destination_ip': destination_ip,
                'source_port': int(row.get('src_port', 0)) if 'src_port' in row else random.randint(1024, 65535),
                'destination_port': int(row.get('dst_port', 0)) if 'dst_port' in row else random.randint(1, 1024),
                'protocol': row.get('protocol', 'TCP') if 'protocol' in row else 'TCP',
                'attack_type': row.get('attack_type', 'normal'),
                'anomaly_score': float(row['label']),  # 0 or 1
                'confidence': random.uniform(0.85, 0.99) if row['label'] == 1 else random.uniform(0.60, 0.85),
                'packet_count': int(row.get('packet_count', 0)) if 'packet_count' in row else 0,
                'byte_count': int(row.get('byte_count', 0)) if 'byte_count' in row else 0,
                'duration': float(row.get('duration', 0)) if 'duration' in row else 0,
                'description': self._generate_description(row),
                'flagged': False,
                'dismissed': False,
                'notes': [],
                'created_at': timestamp,
                'updated_at': timestamp
            }
            
            alerts.append(alert)
        
        print(f"✓ Generated {len(alerts)} alerts")
        return alerts
    
    def _generate_description(self, row):
        """Generate alert description"""
        if row['label'] == 0:
            return "Normal network traffic detected"
        else:
            attack_type = row.get('attack_type', 'unknown')
            if attack_type == 'syn_flood':
                return "SYN flood attack detected - High volume of SYN packets without completion"
            elif attack_type == 'port_scan':
                return "Port scanning activity detected - Multiple connection attempts to different ports"
            elif attack_type == 'udp_flood':
                return "UDP flood attack detected - High volume of UDP packets"
            elif attack_type == 'http_flood':
                return "HTTP flood attack detected - Excessive HTTP requests"
            else:
                return f"Suspicious network activity detected - {attack_type}"
    
    def insert_alerts(self, alerts):
        """Insert alerts into MongoDB"""
        print("\nInserting alerts into MongoDB...")
        
        try:
            if alerts:
                result = self.db.alerts.insert_many(alerts)
                print(f"✓ Inserted {len(result.inserted_ids)} alerts")
                
                # Create indexes
                self.db.alerts.create_index("timestamp")
                self.db.alerts.create_index("severity")
                self.db.alerts.create_index("status")
                self.db.alerts.create_index("attack_type")
                print("✓ Created indexes")
                
                return True
            else:
                print("⚠ No alerts to insert")
                return False
        except Exception as e:
            print(f"✗ Failed to insert alerts: {e}")
            return False
    
    def generate_system_stats(self):
        """Generate system statistics"""
        print("\nGenerating system statistics...")
        
        stats = []
        base_time = datetime.now() - timedelta(days=7)
        
        # Generate hourly stats for the past week
        for hour in range(7 * 24):
            timestamp = base_time + timedelta(hours=hour)
            
            stat = {
                'timestamp': timestamp,
                'metric_type': 'system_performance',
                'cpu_usage': random.uniform(20, 80),
                'memory_usage': random.uniform(30, 70),
                'disk_usage': random.uniform(40, 60),
                'network_throughput': random.uniform(100, 1000),
                'alerts_processed': random.randint(10, 100),
                'threats_detected': random.randint(0, 20)
            }
            
            stats.append(stat)
        
        try:
            if stats:
                result = self.db.system_stats.insert_many(stats)
                print(f"✓ Inserted {len(result.inserted_ids)} system stats")
                return True
        except Exception as e:
            print(f"✗ Failed to insert system stats: {e}")
            return False
    
    def create_audit_log(self):
        """Create initial audit log entry"""
        print("\nCreating audit log entry...")
        
        try:
            audit_entry = {
                'timestamp': datetime.now(),
                'event_type': 'database_reset',
                'username': 'system',
                'ip_address': '127.0.0.1',
                'severity': 'info',
                'description': 'MongoDB database reset and populated with synthetic dataset',
                'details': {
                    'action': 'database_reset',
                    'dataset': 'synthetic_network_data',
                    'status': 'success'
                }
            }
            
            self.db.audit_logs.insert_one(audit_entry)
            print("✓ Created audit log entry")
            return True
        except Exception as e:
            print(f"✗ Failed to create audit log: {e}")
            return False
    
    def verify_data(self):
        """Verify inserted data"""
        print("\nVerifying data...")
        
        try:
            alerts_count = self.db.alerts.count_documents({})
            stats_count = self.db.system_stats.count_documents({})
            audit_count = self.db.audit_logs.count_documents({})
            
            print(f"  Alerts: {alerts_count}")
            print(f"  System stats: {stats_count}")
            print(f"  Audit logs: {audit_count}")
            
            # Get severity distribution
            severity_dist = {}
            for severity in ['low', 'medium', 'high', 'critical']:
                count = self.db.alerts.count_documents({'severity': severity})
                severity_dist[severity] = count
            
            print("\n  Severity distribution:")
            for severity, count in severity_dist.items():
                print(f"    {severity}: {count}")
            
            # Get attack type distribution
            attack_types = self.db.alerts.distinct('attack_type')
            print("\n  Attack types:")
            for attack_type in attack_types:
                count = self.db.alerts.count_documents({'attack_type': attack_type})
                print(f"    {attack_type}: {count}")
            
            print("\n✓ Data verification complete")
            return True
        except Exception as e:
            print(f"✗ Verification failed: {e}")
            return False
    
    def run(self, csv_path):
        """Run complete reset and population"""
        print("="*60)
        print("MONGODB RESET WITH SYNTHETIC DATA")
        print("="*60)
        
        # Connect
        if not self.connect():
            return False
        
        # Flush database
        self.flush_database()
        
        # Load dataset
        df = self.load_synthetic_dataset(csv_path)
        if df is None:
            return False
        
        # Generate and insert alerts
        alerts = self.generate_alerts_from_dataset(df)
        if not self.insert_alerts(alerts):
            return False
        
        # Generate system stats
        self.generate_system_stats()
        
        # Create audit log
        self.create_audit_log()
        
        # Verify data
        self.verify_data()
        
        print("\n" + "="*60)
        print("✓ MONGODB RESET COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nNext steps:")
        print("  1. Start dashboard: python scripts/start_dashboard.py")
        print("  2. Access: http://localhost:5000")
        print("="*60)
        
        return True

def main():
    """Main function"""
    # Find latest synthetic dataset
    dataset_dir = 'mininet_data_generation/data_capture/processed'
    
    if not os.path.exists(dataset_dir):
        print(f"Error: Dataset directory not found: {dataset_dir}")
        print("Run: cd mininet_data_generation && ./run_safe_pipeline.sh")
        sys.exit(1)
    
    # Find latest synthetic dataset
    import glob
    csv_files = glob.glob(os.path.join(dataset_dir, 'synthetic_dataset_*.csv'))
    
    if not csv_files:
        print(f"Error: No synthetic dataset found in {dataset_dir}")
        print("Run: cd mininet_data_generation && python3 generate_synthetic_data.py")
        sys.exit(1)
    
    # Get most recent file
    csv_files.sort()
    csv_path = csv_files[-1]
    
    print(f"Using dataset: {os.path.basename(csv_path)}")
    print()
    
    # Run reset
    resetter = MongoDBReset()
    success = resetter.run(csv_path)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
