#!/usr/bin/env python3
"""
Reset MongoDB for New Model System
Clears old data and prepares database for trained model
"""

import sys
from pymongo import MongoClient
from datetime import datetime

def reset_mongodb():
    """Reset MongoDB collections for new system"""
    
    print("="*70)
    print("MONGODB RESET FOR NEW MODEL SYSTEM")
    print("="*70 + "\n")
    
    try:
        # Connect to MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['soc_dashboard']
        
        print("✅ Connected to MongoDB\n")
        
        # Get collection stats before
        print("Current Database Stats:")
        print(f"  Alerts: {db.alerts.count_documents({})}")
        print(f"  System Stats: {db.system_stats.count_documents({})}")
        print(f"  Users: {db.users.count_documents({})}")
        print(f"  Audit Logs: {db.audit_logs.count_documents({})}\n")
        
        # Ask for confirmation
        response = input("⚠️  Clear all alerts and system stats? (yes/no): ")
        
        if response.lower() != 'yes':
            print("❌ Operation cancelled")
            return False
        
        print("\n🔄 Clearing collections...\n")
        
        # Clear alerts (old simulation data)
        result = db.alerts.delete_many({})
        print(f"✅ Deleted {result.deleted_count} alerts")
        
        # Clear system stats
        result = db.system_stats.delete_many({})
        print(f"✅ Deleted {result.deleted_count} system stats")
        
        # Initialize fresh system stats
        initial_stats = {
            'timestamp': datetime.now(),
            'total_processed': 0,
            'anomalies_detected': 0,
            'total_alerts': 0,
            'active_alerts': 0,
            'system_health': 'healthy',
            'threshold': 0.7,
            'severity_distribution': {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0
            },
            'detection_rate': 0.0,
            'stats_type': 'realtime'
        }
        
        db.system_stats.insert_one(initial_stats)
        print("✅ Initialized fresh system stats")
        
        # Create indexes for performance
        print("\n🔄 Creating indexes...")
        
        db.alerts.create_index([('timestamp', -1)])
        db.alerts.create_index([('severity', 1)])
        db.alerts.create_index([('status', 1)])
        db.alerts.create_index([('anomaly_score', -1)])
        db.alerts.create_index([('attack_type', 1)])
        db.alerts.create_index([('tags', 1)])
        
        print("✅ Created indexes on alerts collection")
        
        db.system_stats.create_index([('timestamp', -1)])
        db.system_stats.create_index([('stats_type', 1)])
        
        print("✅ Created indexes on system_stats collection")
        
        # Final stats
        print("\n" + "="*70)
        print("RESET COMPLETE")
        print("="*70)
        print("\nNew Database Stats:")
        print(f"  Alerts: {db.alerts.count_documents({})}")
        print(f"  System Stats: {db.system_stats.count_documents({})}")
        print(f"  Users: {db.users.count_documents({})} (preserved)")
        print(f"  Audit Logs: {db.audit_logs.count_documents({})} (preserved)")
        
        print("\n✅ MongoDB is ready for the new model system!")
        print("\nNext steps:")
        print("  1. Start backend: cd src/dashboard && python3 server.py")
        print("  2. Start frontend: cd frontend && npm start")
        print("  3. Test simulations in dashboard")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()

def check_mongodb_status():
    """Check if MongoDB is running"""
    try:
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
        client.server_info()
        client.close()
        return True
    except Exception as e:
        print(f"❌ MongoDB is not running!")
        print(f"   Error: {e}")
        print("\n   Start MongoDB with: sudo systemctl start mongodb")
        return False

if __name__ == '__main__':
    print("\n🔍 Checking MongoDB status...")
    
    if not check_mongodb_status():
        sys.exit(1)
    
    print("✅ MongoDB is running\n")
    
    if reset_mongodb():
        sys.exit(0)
    else:
        sys.exit(1)
