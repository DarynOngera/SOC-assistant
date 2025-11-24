#!/usr/bin/env python3
"""
Clear old alerts from MongoDB to fix timestamp issues
"""

import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database.mongodb_config import initialize_mongodb
from src.database.mongodb_dal import get_dal

def clear_old_alerts():
    """Clear all existing alerts from the database in batches"""
    print("🗑️  Clearing old alerts from database...")
    
    # Initialize MongoDB
    if not initialize_mongodb():
        print("❌ Failed to connect to MongoDB")
        return False
    
    # Get DAL instance
    dal = get_dal()
    
    # Get count before deletion
    result = dal.get_alerts(per_page=1)
    total_before = result.get('total', 0)
    print(f"   Found {total_before} alerts in database")
    
    # Drop and recreate collections for fast cleanup
    try:
        print(f"   Dropping alerts collection...")
        dal.db['alerts'].drop()
        print(f"✅ Dropped alerts collection ({total_before} alerts removed)")
        
        print(f"   Dropping system_stats collection...")
        dal.db['system_stats'].drop()
        print("✅ Dropped system_stats collection")
        
        # Recreate indexes
        print("   Recreating indexes...")
        dal.db['alerts'].create_index([("alert_id", 1)], unique=True)
        dal.db['alerts'].create_index([("timestamp", -1)])
        dal.db['alerts'].create_index([("severity", 1)])
        dal.db['alerts'].create_index([("status", 1)])
        print("✅ Indexes recreated")
        
        return True
    except Exception as e:
        print(f"❌ Error clearing alerts: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n" + "="*60)
    print("CLEAR OLD ALERTS - Fix Timestamp Issues")
    print("="*60)
    print("\nThis will delete all existing alerts from the database.")
    print("New alerts will be generated with correct timestamps.\n")
    
    response = input("Continue? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        if clear_old_alerts():
            print("\n✅ Success! Old alerts cleared.")
            print("   New alerts will be generated with current timestamps.")
            print("   Refresh your dashboard to see the changes.\n")
        else:
            print("\n❌ Failed to clear alerts.\n")
    else:
        print("\n❌ Operation cancelled.\n")
