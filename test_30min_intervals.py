#!/usr/bin/env python3
"""
Test script to verify 30-minute interval functionality in threat analysis
"""

import requests
import json
from datetime import datetime

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

def test_granularity(token, granularity, hours=24):
    """Test attack trends with specific granularity"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n{'='*60}")
    print(f"Testing {granularity.upper()} granularity over {hours} hours")
    print('='*60)
    
    response = requests.get(
        f"{BASE_URL}/api/attack-trends?hours={hours}&granularity={granularity}",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Request failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None
    
    data = response.json()
    
    # Display summary
    print(f"\n📊 Summary:")
    print(f"   Total Attacks: {data['summary']['total_attacks']}")
    print(f"   Unique Attack Types: {data['summary']['unique_attack_types']}")
    print(f"   Trend Direction: {data['summary']['trend_direction']}")
    print(f"   Trend Change: {data['summary']['trend_percentage']}%")
    print(f"   Peak Activity: {data['summary'].get('peak_hour', 'N/A')}")
    
    # Display data points
    trends = data.get('trends', [])
    print(f"\n📈 Data Points: {len(trends)} time buckets")
    
    if trends:
        print(f"\n   First 5 time buckets:")
        for i, trend in enumerate(trends[:5]):
            timestamp = trend['timestamp']
            total = trend['total_attacks']
            print(f"   {i+1}. {timestamp}: {total} attacks")
        
        if len(trends) > 5:
            print(f"   ...")
            print(f"   Last time bucket:")
            last = trends[-1]
            print(f"   {len(trends)}. {last['timestamp']}: {last['total_attacks']} attacks")
    
    # Display top attack types
    top_attacks = data['summary'].get('top_recent_attacks', [])
    if top_attacks:
        print(f"\n🎯 Top Attack Types:")
        for i, attack in enumerate(top_attacks[:5], 1):
            print(f"   {i}. {attack['type']}: {attack['count']} occurrences")
    
    return data

def compare_granularities(token):
    """Compare different granularities"""
    print("\n" + "="*60)
    print("🔍 COMPARING GRANULARITIES")
    print("="*60)
    
    granularities = ['30min', 'hour', 'day']
    results = {}
    
    for gran in granularities:
        results[gran] = test_granularity(token, gran, hours=24)
    
    # Comparison summary
    print("\n" + "="*60)
    print("📊 COMPARISON SUMMARY")
    print("="*60)
    
    print(f"\n{'Granularity':<15} {'Data Points':<15} {'Total Attacks':<15}")
    print("-" * 45)
    
    for gran in granularities:
        if results[gran]:
            data_points = len(results[gran].get('trends', []))
            total_attacks = results[gran]['summary']['total_attacks']
            print(f"{gran:<15} {data_points:<15} {total_attacks:<15}")
    
    print("\n💡 Analysis:")
    if results['30min'] and results['hour']:
        min_30_points = len(results['30min'].get('trends', []))
        hour_points = len(results['hour'].get('trends', []))
        
        print(f"   • 30-minute intervals provide {min_30_points} data points")
        print(f"   • Hourly intervals provide {hour_points} data points")
        print(f"   • 30-minute view offers {round((min_30_points / max(hour_points, 1)) * 100)}% more granularity")
        print(f"   • Better for detecting short-duration attacks and burst patterns")
        print(f"   • More accurate peak activity identification")

def main():
    print("="*60)
    print("🧪 Testing 30-Minute Interval Threat Analysis")
    print("="*60)
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Failed to authenticate")
        return
    
    print("✅ Authentication successful")
    
    # Test default (30min) granularity
    test_granularity(token, '30min', hours=24)
    
    # Compare all granularities
    compare_granularities(token)
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60)
    print("\n💡 Tips:")
    print("   • Use 30-minute intervals for detailed recent activity analysis")
    print("   • Use hourly intervals for balanced daily overview")
    print("   • Use daily intervals for long-term trend analysis (7+ days)")
    print("   • Frontend allows switching between all granularities")

if __name__ == "__main__":
    main()
