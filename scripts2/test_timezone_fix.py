#!/usr/bin/env python3
"""
Test script to verify timezone fix for attack trends
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:5000"
USERNAME = "admin"
PASSWORD = "SecurePass123!"

def get_auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code == 200:
        return response.json()['token']
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def test_attack_trends_time_range(token, hours):
    """Test attack trends for a specific time range"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n{'='*60}")
    print(f"Testing Attack Trends: Last {hours} Hours")
    print('='*60)
    
    response = requests.get(
        f"{BASE_URL}/api/attack-trends?hours={hours}&granularity=30min",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Request failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None
    
    data = response.json()
    trends = data.get('trends', [])
    
    print(f"\n📊 Results:")
    print(f"   Total Attacks: {data['summary']['total_attacks']}")
    print(f"   Data Points: {len(trends)}")
    print(f"   Time Range: {data['time_range']}")
    
    if trends:
        # Show time range of data
        first_timestamp = trends[0]['timestamp']
        last_timestamp = trends[-1]['timestamp']
        
        print(f"\n📅 Time Range Coverage:")
        print(f"   First data point: {first_timestamp}")
        print(f"   Last data point:  {last_timestamp}")
        
        # Calculate expected vs actual data points
        expected_points = hours * 2  # 2 points per hour for 30-min intervals
        coverage_pct = (len(trends) / expected_points) * 100
        
        print(f"\n📈 Coverage Analysis:")
        print(f"   Expected data points: {expected_points}")
        print(f"   Actual data points:   {len(trends)}")
        print(f"   Coverage: {coverage_pct:.1f}%")
        
        if coverage_pct >= 80:
            print(f"   ✅ Good coverage - timezone fix working!")
        elif coverage_pct >= 50:
            print(f"   ⚠️  Partial coverage - may need more historical data")
        else:
            print(f"   ❌ Low coverage - check if alerts exist for this time range")
        
        # Show sample data points
        print(f"\n📋 Sample Data Points:")
        for i, trend in enumerate(trends[:3]):
            print(f"   {i+1}. {trend['timestamp']}: {trend['total_attacks']} attacks")
        if len(trends) > 3:
            print(f"   ...")
            print(f"   {len(trends)}. {trends[-1]['timestamp']}: {trends[-1]['total_attacks']} attacks")
    else:
        print(f"\n⚠️  No data points found for this time range")
        print(f"   This might mean:")
        print(f"   - No alerts exist in the database for this period")
        print(f"   - Need to generate some test data")
    
    return data

def check_alert_timestamps(token):
    """Check the timestamps of recent alerts"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n{'='*60}")
    print(f"Checking Alert Timestamps")
    print('='*60)
    
    response = requests.get(
        f"{BASE_URL}/api/alerts?page=1&per_page=10",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch alerts: {response.status_code}")
        return
    
    data = response.json()
    alerts = data.get('alerts', [])
    
    if not alerts:
        print(f"⚠️  No alerts found in database")
        return
    
    print(f"\n📋 Recent Alert Timestamps (showing first 5):")
    now_utc = datetime.utcnow()
    
    for i, alert in enumerate(alerts[:5], 1):
        timestamp = alert.get('timestamp')
        alert_id = alert.get('alert_id')
        attack_type = alert.get('attack_type', 'Unknown')
        
        # Parse timestamp
        if isinstance(timestamp, str):
            alert_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            if alert_time.tzinfo:
                alert_time = alert_time.replace(tzinfo=None)
        else:
            alert_time = timestamp
        
        # Calculate age
        age = now_utc - alert_time
        hours_ago = age.total_seconds() / 3600
        
        print(f"   {i}. Alert #{alert_id}")
        print(f"      Type: {attack_type}")
        print(f"      Timestamp: {timestamp}")
        print(f"      Age: {hours_ago:.1f} hours ago")
    
    # Check timestamp distribution
    print(f"\n📊 Timestamp Distribution:")
    time_buckets = {'< 1h': 0, '1-6h': 0, '6-24h': 0, '> 24h': 0}
    
    for alert in alerts:
        timestamp = alert.get('timestamp')
        if isinstance(timestamp, str):
            alert_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            if alert_time.tzinfo:
                alert_time = alert_time.replace(tzinfo=None)
        else:
            alert_time = timestamp
        
        age = now_utc - alert_time
        hours_ago = age.total_seconds() / 3600
        
        if hours_ago < 1:
            time_buckets['< 1h'] += 1
        elif hours_ago < 6:
            time_buckets['1-6h'] += 1
        elif hours_ago < 24:
            time_buckets['6-24h'] += 1
        else:
            time_buckets['> 24h'] += 1
    
    for bucket, count in time_buckets.items():
        print(f"   {bucket}: {count} alerts")

def main():
    print("="*60)
    print("🧪 Testing Timezone Fix for Attack Trends")
    print("="*60)
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Failed to authenticate")
        return
    
    print("✅ Authentication successful")
    
    # Check alert timestamps first
    check_alert_timestamps(token)
    
    # Test different time ranges
    time_ranges = [6, 12, 24, 48]
    
    for hours in time_ranges:
        test_attack_trends_time_range(token, hours)
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60)
    
    print("\n💡 What to look for:")
    print("   ✅ Data points span the full requested time range")
    print("   ✅ First and last timestamps are ~{hours} apart")
    print("   ✅ Coverage percentage is high (>80%)")
    print("   ✅ Alerts exist across different time buckets")
    print("\n   If coverage is low:")
    print("   - Start monitoring to generate new alerts")
    print("   - Run a Mininet simulation")
    print("   - Upload CSV data for analysis")

if __name__ == "__main__":
    main()
