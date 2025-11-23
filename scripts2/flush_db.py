#!/usr/bin/env python3
"""
Simple script to flush the alerts database for clean testing
"""

import requests
import json

API_BASE_URL = 'http://localhost:5000'

def flush_database():
    """Flush all alerts from the database"""
    print("🗑️ Flushing SOC Dashboard Database")
    print("=" * 40)
    
    # Test credentials
    credentials = {
        'username': 'admin',
        'password': 'SecureAdmin123!'
    }
    
    session = requests.Session()
    
    # 1. Login
    print("1. Logging in as admin...")
    try:
        login_response = session.post(f"{API_BASE_URL}/api/auth/login", json=credentials)
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get('access_token')
            session.headers.update({'Authorization': f'Bearer {token}'})
            print("   ✅ Login successful")
        else:
            print(f"   ❌ Login failed: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return False
    
    # 2. Get current stats
    print("2. Getting current database stats...")
    try:
        stats_response = session.get(f"{API_BASE_URL}/api/stats")
        if stats_response.status_code == 200:
            stats = stats_response.json()
            current_alerts = stats.get('total_alerts', 0)
            print(f"   📊 Current alerts in database: {current_alerts}")
        else:
            print(f"   ⚠️ Could not get stats: {stats_response.status_code}")
            current_alerts = "unknown"
    except Exception as e:
        print(f"   ⚠️ Stats error: {e}")
        current_alerts = "unknown"
    
    # 3. Flush database
    print("3. Flushing database...")
    try:
        flush_response = session.post(f"{API_BASE_URL}/api/debug/flush-db")
        if flush_response.status_code == 200:
            result = flush_response.json()
            if result.get('success'):
                deleted_count = result.get('deleted_count', 0)
                collection = result.get('collection', 'alerts')
                print(f"   ✅ Successfully deleted {deleted_count} alerts from '{collection}' collection")
            else:
                print(f"   ❌ Flush failed: {result.get('message')}")
                return False
        else:
            print(f"   ❌ Flush request failed: {flush_response.status_code}")
            print(f"   Response: {flush_response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Flush error: {e}")
        return False
    
    # 4. Verify flush
    print("4. Verifying database is clean...")
    try:
        verify_response = session.get(f"{API_BASE_URL}/api/stats")
        if verify_response.status_code == 200:
            stats = verify_response.json()
            remaining_alerts = stats.get('total_alerts', 0)
            print(f"   📊 Remaining alerts: {remaining_alerts}")
            
            if remaining_alerts == 0:
                print("   ✅ Database successfully flushed!")
            else:
                print(f"   ⚠️ Warning: {remaining_alerts} alerts still remain")
        else:
            print(f"   ⚠️ Could not verify: {verify_response.status_code}")
    except Exception as e:
        print(f"   ⚠️ Verification error: {e}")
    
    print("\n" + "=" * 40)
    print("🎉 Database flush completed!")
    print("\nNext steps:")
    print("1. Run Mininet Normal simulation → Should see very few alerts")
    print("2. Run Mininet Attack simulation → Should see many high-severity alerts")
    print("3. Compare the ML model detection differences")
    
    return True

if __name__ == '__main__':
    flush_database()
