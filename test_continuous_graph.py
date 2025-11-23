#!/usr/bin/env python3
"""
Test script to verify continuous graph visualization fix
"""

import requests
import json
from datetime import datetime
from collections import Counter

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

def analyze_timestamp_distribution(token):
    """Analyze how alerts are distributed across time buckets"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n{'='*60}")
    print(f"Analyzing Alert Timestamp Distribution")
    print('='*60)
    
    # Get recent alerts
    response = requests.get(
        f"{BASE_URL}/api/alerts?page=1&per_page=100",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch alerts: {response.status_code}")
        return
    
    data = response.json()
    alerts = data.get('alerts', [])
    
    if not alerts:
        print(f"⚠️  No alerts found. Generate some alerts first.")
        return
    
    print(f"\n📊 Total Alerts: {len(alerts)}")
    
    # Group alerts by 30-minute buckets
    buckets_30min = Counter()
    buckets_hour = Counter()
    
    for alert in alerts:
        timestamp = alert.get('timestamp')
        if isinstance(timestamp, str):
            try:
                alert_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                if alert_time.tzinfo:
                    alert_time = alert_time.replace(tzinfo=None)
            except:
                continue
        else:
            alert_time = timestamp
        
        # 30-minute bucket
        minute_30 = (alert_time.minute // 30) * 30
        bucket_30 = alert_time.replace(minute=minute_30, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M')
        buckets_30min[bucket_30] += 1
        
        # Hourly bucket
        bucket_hour = alert_time.strftime('%Y-%m-%d %H:00')
        buckets_hour[bucket_hour] += 1
    
    # Analyze distribution
    print(f"\n📈 30-Minute Bucket Distribution:")
    print(f"   Unique buckets: {len(buckets_30min)}")
    
    if len(buckets_30min) == 1:
        print(f"   ❌ PROBLEM: All alerts in ONE bucket (clustering issue)")
        print(f"      This will show as a single data point on graphs")
    elif len(buckets_30min) < 5:
        print(f"   ⚠️  WARNING: Alerts in only {len(buckets_30min)} buckets")
        print(f"      Limited visualization - may need more distribution")
    else:
        print(f"   ✅ GOOD: Alerts distributed across {len(buckets_30min)} buckets")
        print(f"      This will show as a continuous graph")
    
    # Show top buckets
    print(f"\n   Top 10 buckets:")
    for bucket, count in buckets_30min.most_common(10):
        bar = '█' * min(count, 50)
        print(f"   {bucket}: {count:3d} alerts {bar}")
    
    # Calculate distribution metrics
    if buckets_30min:
        avg_per_bucket = sum(buckets_30min.values()) / len(buckets_30min)
        max_per_bucket = max(buckets_30min.values())
        min_per_bucket = min(buckets_30min.values())
        
        print(f"\n   Distribution Metrics:")
        print(f"   - Average per bucket: {avg_per_bucket:.1f}")
        print(f"   - Max per bucket: {max_per_bucket}")
        print(f"   - Min per bucket: {min_per_bucket}")
        
        # Check if distribution is reasonable
        if max_per_bucket / avg_per_bucket > 5:
            print(f"   ⚠️  High variance - some buckets have 5x more alerts")
        else:
            print(f"   ✅ Reasonable distribution variance")

def test_attack_trends_data_points(token):
    """Test that attack trends return multiple data points"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n{'='*60}")
    print(f"Testing Attack Trends Data Points")
    print('='*60)
    
    test_ranges = [
        (6, '30min', 12),   # 6 hours with 30-min intervals = 12 expected points
        (12, '30min', 24),  # 12 hours with 30-min intervals = 24 expected points
        (24, 'hour', 24),   # 24 hours with hourly intervals = 24 expected points
    ]
    
    for hours, granularity, expected_max in test_ranges:
        print(f"\n📊 Testing {hours}h with {granularity} granularity:")
        
        response = requests.get(
            f"{BASE_URL}/api/attack-trends?hours={hours}&granularity={granularity}",
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"   ❌ Request failed: {response.status_code}")
            continue
        
        data = response.json()
        trends = data.get('trends', [])
        
        print(f"   Data points returned: {len(trends)}")
        print(f"   Expected maximum: {expected_max}")
        
        if len(trends) == 0:
            print(f"   ❌ NO DATA: No alerts in this time range")
        elif len(trends) == 1:
            print(f"   ❌ SINGLE POINT: Graph will show only one bar/point")
            print(f"      → All alerts clustered in same time bucket")
        elif len(trends) < expected_max * 0.3:
            print(f"   ⚠️  LOW COVERAGE: Only {len(trends)}/{expected_max} possible points")
            print(f"      → Graph will have gaps, but shows some distribution")
        else:
            print(f"   ✅ GOOD COVERAGE: {len(trends)}/{expected_max} points")
            print(f"      → Graph will show continuous timeline")
        
        # Show time range
        if trends:
            first = trends[0]['timestamp']
            last = trends[-1]['timestamp']
            print(f"   Time range: {first} to {last}")
            
            # Check for continuity
            if len(trends) >= 3:
                print(f"   First 3 points:")
                for i, trend in enumerate(trends[:3], 1):
                    print(f"      {i}. {trend['timestamp']}: {trend['total_attacks']} attacks")

def visualize_expected_graph(token):
    """Show what the graph should look like"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n{'='*60}")
    print(f"Expected Graph Visualization")
    print('='*60)
    
    response = requests.get(
        f"{BASE_URL}/api/attack-trends?hours=6&granularity=30min",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch trends")
        return
    
    data = response.json()
    trends = data.get('trends', [])
    
    if not trends:
        print(f"⚠️  No data to visualize")
        return
    
    print(f"\n📈 ASCII Graph Preview (6-hour view):")
    print(f"   Data points: {len(trends)}")
    
    if len(trends) == 1:
        print(f"\n   ❌ BEFORE FIX:")
        print(f"   |                    ▮")
        print(f"   |____________________|____")
        print(f"   14:00              20:42")
        print(f"   Single bar - no trend visible")
    else:
        # Create simple ASCII visualization
        max_attacks = max(t['total_attacks'] for t in trends)
        
        print(f"\n   ✅ AFTER FIX:")
        
        # Show simplified graph
        for trend in trends[:12]:  # Show first 12 points
            attacks = trend['total_attacks']
            bar_length = int((attacks / max(max_attacks, 1)) * 30)
            bar = '█' * bar_length
            time_label = trend['timestamp'][-5:]  # Last 5 chars (HH:MM)
            print(f"   {time_label} | {bar} ({attacks})")
        
        print(f"\n   Continuous timeline - trends visible ✅")

def main():
    print("="*60)
    print("🧪 Testing Continuous Graph Visualization")
    print("="*60)
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Failed to authenticate")
        return
    
    print("✅ Authentication successful")
    
    # Run tests
    analyze_timestamp_distribution(token)
    test_attack_trends_data_points(token)
    visualize_expected_graph(token)
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60)
    
    print("\n💡 What to look for:")
    print("   ✅ Alerts distributed across 10+ time buckets")
    print("   ✅ Attack trends return 10+ data points")
    print("   ✅ Time range spans several hours")
    print("   ✅ Graph shows continuous line (not single point)")
    
    print("\n📊 Frontend Verification:")
    print("   1. Open Threat Analysis page")
    print("   2. Select 6-hour or 12-hour time range")
    print("   3. Verify graphs show continuous lines/areas")
    print("   4. Check multiple X-axis time labels")
    print("   5. Hover over different points to see data")
    
    print("\n🔧 If still seeing single point:")
    print("   1. Restart the server (to load new code)")
    print("   2. Generate NEW alerts (old ones still clustered)")
    print("   3. Run monitoring or simulation")
    print("   4. Wait a few seconds for alerts to generate")

if __name__ == "__main__":
    main()
