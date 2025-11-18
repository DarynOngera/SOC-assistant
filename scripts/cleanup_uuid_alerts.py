#!/usr/bin/env python3
"""
Clean up UUID-based alerts from MongoDB
Removes alerts with UUID alert_ids and keeps only numeric ones
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient

def cleanup_uuid_alerts():
    """Remove alerts with UUID alert_ids"""
    print("="*60)
    print("CLEANUP UUID ALERTS")
    print("="*60)
    
    try:
        # Connect to MongoDB
        client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client['soc_assistant']
        print("✓ Connected to MongoDB")
        
        # Find alerts with string alert_ids (UUIDs)
        uuid_alerts = list(db.alerts.find({"alert_id": {"$type": "string"}}))
        print(f"\nFound {len(uuid_alerts)} alerts with UUID alert_ids")
        
        if uuid_alerts:
            # Delete UUID alerts
            result = db.alerts.delete_many({"alert_id": {"$type": "string"}})
            print(f"✓ Deleted {result.deleted_count} UUID alerts")
        else:
            print("✓ No UUID alerts to clean up")
        
        # Count remaining alerts
        remaining = db.alerts.count_documents({})
        print(f"\nRemaining alerts: {remaining}")
        
        # Show alert_id types
        numeric_count = db.alerts.count_documents({"alert_id": {"$type": ["int", "long"]}})
        print(f"  Numeric alert_ids: {numeric_count}")
        
        client.close()
        
        print("\n" + "="*60)
        print("✓ CLEANUP COMPLETED")
        print("="*60)
        print("\nRestart your server to see clean logs:")
        print("  cd src/dashboard && python server.py")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == '__main__':
    success = cleanup_uuid_alerts()
    sys.exit(0 if success else 1)
