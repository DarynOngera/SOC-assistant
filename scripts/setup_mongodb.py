#!/usr/bin/env python3
"""
MongoDB Setup and Initialization Script
Sets up MongoDB connection, creates indexes, and runs initial data migration
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database.mongodb_config import initialize_mongodb, mongodb_health_check
from src.database.migration_utils import migrate_existing_data
from src.database.mongodb_dal import get_dal

def setup_mongodb(skip_migration=False, create_sample_data=True):
    """
    Complete MongoDB setup process
    """
    print("🔧 Starting MongoDB setup for SOC Assistant...")
    
    try:
        # Step 1: Initialize MongoDB connection and indexes
        print("\n📡 Initializing MongoDB connection...")
        if initialize_mongodb():
            print("✓ MongoDB connection established")
            print("✓ Database indexes created")
        else:
            print("✗ MongoDB initialization failed")
            return False
        
        # Step 2: Health check
        print("\n🏥 Performing MongoDB health check...")
        health_status = mongodb_health_check()
        if health_status.get('status') == 'healthy':
            print(f"✓ MongoDB is healthy (ping: {health_status.get('ping_time_ms', 'N/A')}ms)")
            print(f"✓ Server version: {health_status.get('server_version', 'Unknown')}")
            print(f"✓ Database size: {health_status.get('database_size_mb', 0)}MB")
        else:
            print("⚠ MongoDB health check failed")
            print(f"Error: {health_status.get('error', 'Unknown error')}")
        
        # Step 3: Data migration
        if not skip_migration:
            print("\n📦 Running data migration...")
            migration_results = migrate_existing_data()
            
            if migration_results.get('error'):
                print(f"⚠ Migration completed with warnings: {migration_results['error']}")
            else:
                print("✓ Data migration completed successfully")
                
                # Print migration summary
                operations = migration_results.get('operations', {})
                for operation, result in operations.items():
                    if isinstance(result, dict):
                        if 'migrated' in result:
                            print(f"  - {operation}: {result['migrated']} items migrated")
                        elif 'message' in result:
                            print(f"  - {operation}: {result['message']}")
        else:
            print("\n⏭ Skipping data migration")
        
        # Step 4: Verify setup
        print("\n🔍 Verifying setup...")
        dal = get_dal()
        collection_stats = dal.get_collection_stats()
        
        print("📊 Collection Statistics:")
        for collection, stats in collection_stats.items():
            print(f"  - {collection}: {stats['count']} documents ({stats['size']} bytes)")
        
        print("\n🎉 MongoDB setup completed successfully!")
        print("\n📋 Next steps:")
        print("  1. Start the SOC Dashboard: python src/dashboard/server.py")
        print("  2. Access the web interface at http://localhost:5000")
        print("  3. Login with admin credentials (admin/SecureAdmin123!)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ MongoDB setup failed: {str(e)}")
        print("\n🔧 Troubleshooting tips:")
        print("  1. Ensure MongoDB is running on localhost:27017")
        print("  2. Check MongoDB connection settings in environment variables")
        print("  3. Verify MongoDB user permissions if using authentication")
        return False

def main():
    """Main setup function with command line arguments"""
    parser = argparse.ArgumentParser(description='Setup MongoDB for SOC Assistant')
    parser.add_argument('--skip-migration', action='store_true', 
                       help='Skip data migration from existing JSON files')
    parser.add_argument('--no-sample-data', action='store_true',
                       help='Skip creating sample data')
    parser.add_argument('--health-check-only', action='store_true',
                       help='Only perform MongoDB health check')
    
    args = parser.parse_args()
    
    if args.health_check_only:
        print("🏥 Performing MongoDB health check...")
        try:
            health_status = mongodb_health_check()
            print(f"Status: {health_status.get('status', 'unknown')}")
            if health_status.get('status') == 'healthy':
                print(f"Ping time: {health_status.get('ping_time_ms', 'N/A')}ms")
                print(f"Server version: {health_status.get('server_version', 'Unknown')}")
                print(f"Connections: {health_status.get('connections', {})}")
                print(f"Database size: {health_status.get('database_size_mb', 0)}MB")
                print("✓ MongoDB is healthy")
            else:
                print(f"Error: {health_status.get('error', 'Unknown error')}")
                print("✗ MongoDB health check failed")
        except Exception as e:
            print(f"❌ Health check failed: {str(e)}")
        return
    
    # Run full setup
    success = setup_mongodb(
        skip_migration=args.skip_migration,
        create_sample_data=not args.no_sample_data
    )
    
    if success:
        print("\n🚀 SOC Assistant is ready to use!")
    else:
        print("\n💥 Setup failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == '__main__':
    main()
