#!/usr/bin/env python3
"""
Test script to verify triage action endpoints handle both integer and ObjectId formats
"""

import requests
import json

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
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_triage_actions():
    """Test triage actions with different alert ID formats"""
    token = get_auth_token()
    if not token:
        print("❌ Failed to get authentication token")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Get some alerts first
    print("\n📋 Fetching alerts...")
    response = requests.get(f"{BASE_URL}/api/alerts", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to fetch alerts: {response.status_code}")
        return
    
    alerts = response.json().get('alerts', [])
    if not alerts:
        print("⚠️  No alerts found to test")
        return
    
    # Test with the first alert
    test_alert = alerts[0]
    alert_id = test_alert.get('alert_id')
    
    print(f"\n🎯 Testing with alert ID: {alert_id} (type: {type(alert_id).__name__})")
    
    # Test 1: Flag alert
    print("\n1️⃣  Testing flag action...")
    response = requests.post(
        f"{BASE_URL}/api/alerts/{alert_id}/flag",
        headers=headers
    )
    if response.status_code == 200:
        print("   ✅ Flag action successful")
    else:
        print(f"   ❌ Flag action failed: {response.status_code} - {response.text}")
    
    # Test 2: Escalate alert
    print("\n2️⃣  Testing escalate action...")
    response = requests.post(
        f"{BASE_URL}/api/alerts/{alert_id}/escalate",
        headers=headers,
        json={
            "reason": "Test escalation",
            "escalated_to": "Senior Analyst"
        }
    )
    if response.status_code == 200:
        print("   ✅ Escalate action successful")
    else:
        print(f"   ❌ Escalate action failed: {response.status_code} - {response.text}")
    
    # Test 3: Assign alert
    print("\n3️⃣  Testing assign action...")
    response = requests.post(
        f"{BASE_URL}/api/alerts/{alert_id}/assign",
        headers=headers,
        json={
            "assigned_to": USERNAME,
            "notes": "Test assignment"
        }
    )
    if response.status_code == 200:
        print("   ✅ Assign action successful")
    else:
        print(f"   ❌ Assign action failed: {response.status_code} - {response.text}")
    
    # Test 4: Start investigation
    print("\n4️⃣  Testing investigate action...")
    response = requests.post(
        f"{BASE_URL}/api/alerts/{alert_id}/investigate",
        headers=headers,
        json={
            "notes": "Test investigation",
            "priority": "high"
        }
    )
    if response.status_code == 200:
        print("   ✅ Investigate action successful")
    else:
        print(f"   ❌ Investigate action failed: {response.status_code} - {response.text}")
    
    # Test 5: Update investigation
    print("\n5️⃣  Testing update investigation action...")
    response = requests.post(
        f"{BASE_URL}/api/alerts/{alert_id}/update-investigation",
        headers=headers,
        json={
            "update": "Test investigation update",
            "status": "in_progress"
        }
    )
    if response.status_code == 200:
        print("   ✅ Update investigation action successful")
    else:
        print(f"   ❌ Update investigation action failed: {response.status_code} - {response.text}")
    
    # Test 6: Resolve alert
    print("\n6️⃣  Testing resolve action...")
    response = requests.post(
        f"{BASE_URL}/api/alerts/{alert_id}/resolve",
        headers=headers,
        json={
            "resolution_type": "resolved",
            "notes": "Test resolution",
            "action_taken": "Verified and resolved"
        }
    )
    if response.status_code == 200:
        print("   ✅ Resolve action successful")
    else:
        print(f"   ❌ Resolve action failed: {response.status_code} - {response.text}")
    
    # Test 7: Dismiss alert (on a different alert if available)
    if len(alerts) > 1:
        test_alert2 = alerts[1]
        alert_id2 = test_alert2.get('alert_id')
        print(f"\n7️⃣  Testing dismiss action on alert {alert_id2}...")
        response = requests.post(
            f"{BASE_URL}/api/alerts/{alert_id2}/dismiss",
            headers=headers
        )
        if response.status_code == 200:
            print("   ✅ Dismiss action successful")
        else:
            print(f"   ❌ Dismiss action failed: {response.status_code} - {response.text}")
    
    print("\n" + "="*60)
    print("✅ All triage action tests completed!")
    print("="*60)

if __name__ == "__main__":
    print("="*60)
    print("🔧 Testing Triage Action Endpoints")
    print("="*60)
    test_triage_actions()
