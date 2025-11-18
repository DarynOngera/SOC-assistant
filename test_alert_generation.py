#!/usr/bin/env python3
"""
Test script to verify alert generation from Mininet simulation
"""

import requests
import time
import json

API_BASE_URL = 'http://localhost:5000'

def test_alert_generation():
    """Test that alerts are properly generated and visible in dashboard"""
    print("🧪 Testing Alert Generation from Mininet Simulation")
    print("=" * 60)
    
    # Test credentials
    credentials = {
        'username': 'admin',
        'password': 'SecureAdmin123!'
    }
    
    session = requests.Session()
    
    # 1. Login
    print("1. Logging in...")
    try:
        login_response = session.post(f"{API_BASE_URL}/api/auth/login", json=credentials)
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get('access_token')
            session.headers.update({'Authorization': f'Bearer {token}'})
            print("   ✅ Login successful")
        else:
            print(f"   ❌ Login failed: {login_response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return False
    
    # 2. Get current alert count
    print("2. Getting current alert count...")
    try:
        alerts_response = session.get(f"{API_BASE_URL}/api/alerts?per_page=100")
        if alerts_response.status_code == 200:
            alerts_data = alerts_response.json()
            initial_count = len(alerts_data.get('alerts', []))
            print(f"   📊 Initial alert count: {initial_count}")
        else:
            print(f"   ❌ Failed to get alerts: {alerts_response.status_code}")
            initial_count = 0
    except Exception as e:
        print(f"   ❌ Error getting alerts: {e}")
        initial_count = 0
    
    # 3. Get current stats
    print("3. Getting current dashboard stats...")
    try:
        stats_response = session.get(f"{API_BASE_URL}/api/stats")
        if stats_response.status_code == 200:
            initial_stats = stats_response.json()
            print(f"   📊 Initial stats: {initial_stats.get('total_alerts', 0)} total alerts")
        else:
            print(f"   ❌ Failed to get stats: {stats_response.status_code}")
            initial_stats = {}
    except Exception as e:
        print(f"   ❌ Error getting stats: {e}")
        initial_stats = {}
    
    # 4. Start attack simulation
    print("4. Starting SYN flood attack simulation...")
    try:
        simulation_data = {
            'mode': 'attack',
            'attack_type': 'syn_flood',
            'duration': 5
        }
        sim_response = session.post(f"{API_BASE_URL}/api/mininet/start", json=simulation_data)
        if sim_response.status_code == 200:
            result = sim_response.json()
            if result.get('success'):
                print(f"   ✅ Simulation started: {result.get('message')}")
                
                # Wait for completion
                print("   ⏳ Waiting for simulation to complete...")
                time.sleep(8)  # Wait for simulation to finish
                
            else:
                print(f"   ❌ Failed to start simulation: {result.get('message')}")
                return False
        else:
            print(f"   ❌ Simulation request failed: {sim_response.status_code}")
            print(f"   Response: {sim_response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Simulation error: {e}")
        return False
    
    # 5. Check for new alerts
    print("5. Checking for new alerts...")
    try:
        time.sleep(2)  # Give a moment for alerts to be processed
        new_alerts_response = session.get(f"{API_BASE_URL}/api/alerts?per_page=100")
        if new_alerts_response.status_code == 200:
            new_alerts_data = new_alerts_response.json()
            new_count = len(new_alerts_data.get('alerts', []))
            new_alerts = new_count - initial_count
            
            print(f"   📊 New alert count: {new_count} (added: {new_alerts})")
            
            if new_alerts > 0:
                print("   ✅ New alerts generated successfully!")
                
                # Show some details of new alerts
                alerts = new_alerts_data.get('alerts', [])
                mininet_alerts = [a for a in alerts if a.get('simulation_source') or 'mininet' in a.get('alert_id', '')]
                
                if mininet_alerts:
                    print(f"   🎯 Found {len(mininet_alerts)} Mininet-generated alerts:")
                    for alert in mininet_alerts[:3]:  # Show first 3
                        print(f"      - {alert.get('attack_type')} ({alert.get('severity')}) from {alert.get('source_ip')}")
                else:
                    print("   ⚠️ No Mininet-specific alerts found, but new alerts were created")
            else:
                print("   ❌ No new alerts generated")
                return False
        else:
            print(f"   ❌ Failed to get new alerts: {new_alerts_response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error checking new alerts: {e}")
        return False
    
    # 6. Check updated stats
    print("6. Checking updated dashboard stats...")
    try:
        final_stats_response = session.get(f"{API_BASE_URL}/api/stats")
        if final_stats_response.status_code == 200:
            final_stats = final_stats_response.json()
            initial_total = initial_stats.get('total_alerts', 0)
            final_total = final_stats.get('total_alerts', 0)
            stats_increase = final_total - initial_total
            
            print(f"   📊 Final stats: {final_total} total alerts (increased by {stats_increase})")
            
            if stats_increase > 0:
                print("   ✅ Dashboard stats updated successfully!")
            else:
                print("   ⚠️ Dashboard stats may not have updated yet")
        else:
            print(f"   ❌ Failed to get final stats: {final_stats_response.status_code}")
    except Exception as e:
        print(f"   ❌ Error checking final stats: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Alert Generation Test Completed!")
    print("\nWhat to check in the Dashboard:")
    print("1. Go to Dashboard → Alerts tab")
    print("2. Look for alerts with 'mininet' in the ID or 'simulation_source' = true")
    print("3. Check that attack types match the simulation (syn_flood_detected, etc.)")
    print("4. Verify that dashboard statistics have increased")
    
    return True

if __name__ == '__main__':
    test_alert_generation()
