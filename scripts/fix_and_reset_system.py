#!/usr/bin/env python3
"""
Complete System Fix and Reset
Fixes MongoDB errors and resets with synthetic data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime, timedelta
import random
import uuid
from pymongo import MongoClient

def connect_mongodb():
    """Connect to MongoDB"""
    try:
        client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client['soc_assistant']
        print("✓ Connected to MongoDB")
        return client, db
    except Exception as e:
        print(f"✗ Failed to connect to MongoDB: {e}")
        print("\nMake sure MongoDB is running:")
        print("  sudo systemctl start mongodb")
        return None, None

def flush_collections(db):
    """Flush all collections"""
    print("\nFlushing collections...")
    
    collections = ['alerts', 'audit_logs', 'system_stats', 'csv_uploads', 'network_data']
    
    for coll in collections:
        try:
            count = db[coll].count_documents({})
            if count > 0:
                db[coll].delete_many({})
                print(f"  ✓ Flushed {coll}: {count} documents")
            else:
                print(f"  - {coll}: empty")
        except Exception as e:
            print(f"  ✗ Error flushing {coll}: {e}")

def create_sample_alerts(db, count=100):
    """Create sample alerts with proper structure"""
    print(f"\nCreating {count} sample alerts...")
    
    alerts = []
    base_time = datetime.now() - timedelta(days=7)
    
    attack_types = ['normal', 'syn_flood', 'port_scan', 'udp_flood', 'http_flood']
    severities = ['low', 'medium', 'high', 'critical']
    statuses = ['open', 'investigating', 'resolved']
    
    for i in range(count):
        timestamp = base_time + timedelta(seconds=random.randint(0, 7*24*3600))
        attack_type = random.choice(attack_types)
        
        # Determine severity
        if attack_type == 'normal':
            severity = 'low'
            status = 'resolved'
        elif attack_type in ['syn_flood', 'udp_flood']:
            severity = 'critical'
            status = random.choice(['open', 'investigating'])
        else:
            severity = random.choice(['medium', 'high'])
            status = random.choice(statuses)
        
        alert = {
            'alert_id': str(uuid.uuid4()),  # FIX: Add alert_id
            'timestamp': timestamp,
            'severity': severity,
            'status': status,
            'source_ip': f"10.0.{random.randint(1,3)}.{random.randint(1,254)}",
            'destination_ip': f"10.0.{random.randint(1,3)}.{random.randint(1,254)}",
            'source_port': random.randint(1024, 65535),
            'destination_port': random.randint(1, 1024),
            'protocol': random.choice(['TCP', 'UDP', 'ICMP']),
            'attack_type': attack_type,
            'anomaly_score': 1.0 if attack_type != 'normal' else 0.0,
            'confidence': random.uniform(0.85, 0.99),
            'packet_count': random.randint(10, 1000),
            'byte_count': random.randint(1000, 100000),
            'duration': random.uniform(0.1, 10.0),
            'description': f"{'Normal traffic' if attack_type == 'normal' else attack_type.replace('_', ' ').title() + ' detected'}",
            'flagged': False,
            'dismissed': False,
            'notes': [],
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        alerts.append(alert)
    
    try:
        result = db.alerts.insert_many(alerts)
        print(f"✓ Created {len(result.inserted_ids)} alerts")
        return True
    except Exception as e:
        print(f"✗ Failed to create alerts: {e}")
        return False

def create_system_stats(db):
    """Create system statistics"""
    print("\nCreating system statistics...")
    
    stats = []
    base_time = datetime.now() - timedelta(days=7)
    
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
        result = db.system_stats.insert_many(stats)
        print(f"✓ Created {len(result.inserted_ids)} system stats")
        return True
    except Exception as e:
        print(f"✗ Failed to create system stats: {e}")
        return False

def create_audit_log(db):
    """Create audit log entry"""
    print("\nCreating audit log...")
    
    try:
        entry = {
            'timestamp': datetime.now(),
            'event_type': 'system_reset',
            'username': 'system',
            'ip_address': '127.0.0.1',
            'severity': 'info',
            'description': 'System reset and populated with sample data',
            'details': {
                'action': 'system_reset',
                'status': 'success'
            }
        }
        
        db.audit_logs.insert_one(entry)
        print("✓ Created audit log")
        return True
    except Exception as e:
        print(f"✗ Failed to create audit log: {e}")
        return False

def create_indexes(db):
    """Create MongoDB indexes"""
    print("\nCreating indexes...")
    
    try:
        # Alerts indexes
        db.alerts.create_index("alert_id", unique=True)
        db.alerts.create_index("timestamp")
        db.alerts.create_index("severity")
        db.alerts.create_index("status")
        db.alerts.create_index("attack_type")
        
        # System stats indexes
        db.system_stats.create_index("timestamp")
        db.system_stats.create_index("metric_type")
        
        # Audit logs indexes
        db.audit_logs.create_index("timestamp")
        db.audit_logs.create_index("event_type")
        
        print("✓ Created indexes")
        return True
    except Exception as e:
        print(f"✗ Failed to create indexes: {e}")
        return False

def verify_data(db):
    """Verify data"""
    print("\nVerifying data...")
    
    try:
        alerts = db.alerts.count_documents({})
        stats = db.system_stats.count_documents({})
        audit = db.audit_logs.count_documents({})
        
        print(f"  Alerts: {alerts}")
        print(f"  System stats: {stats}")
        print(f"  Audit logs: {audit}")
        
        # Check severity distribution
        print("\n  Severity distribution:")
        for sev in ['low', 'medium', 'high', 'critical']:
            count = db.alerts.count_documents({'severity': sev})
            print(f"    {sev}: {count}")
        
        # Check attack types
        print("\n  Attack types:")
        for attack in db.alerts.distinct('attack_type'):
            count = db.alerts.count_documents({'attack_type': attack})
            print(f"    {attack}: {count}")
        
        print("\n✓ Verification complete")
        return True
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return False

def main():
    """Main function"""
    print("="*60)
    print("SYSTEM FIX AND RESET")
    print("="*60)
    
    # Connect
    client, db = connect_mongodb()
    if db is None:
        sys.exit(1)
    
    # Flush
    flush_collections(db)
    
    # Create data
    create_sample_alerts(db, count=100)
    create_system_stats(db)
    create_audit_log(db)
    
    # Create indexes
    create_indexes(db)
    
    # Verify
    verify_data(db)
    
    # Close
    client.close()
    
    print("\n" + "="*60)
    print("✓ SYSTEM RESET COMPLETED")
    print("="*60)
    print("\nNext steps:")
    print("  1. Restart server: python src/dashboard/server.py")
    print("  2. Access: http://localhost:5000")
    print("  3. Login: admin / SecureAdmin123!")
    print("="*60)

if __name__ == '__main__':
    main()
