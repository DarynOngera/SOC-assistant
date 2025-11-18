#!/usr/bin/env python3
"""
Quick test for Mininet simulation functionality
"""

import requests
import time
import json

API_BASE_URL = 'http://localhost:5000'

def test_simulation():
    """Test the simulation functionality"""
    print("🧪 Testing Mininet Simulation Functionality")
    print("=" * 50)
    
    # Test credentials (you may need to adjust these)
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
            print(f"   Response: {login_response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return False
    
    # 2. Check status
    print("2. Checking simulation status...")
    try:
        status_response = session.get(f"{API_BASE_URL}/api/mininet/status")
        if status_response.status_code == 200:
            status = status_response.json()
            print(f"   ✅ Status check successful: {status}")
        else:
            print(f"   ❌ Status check failed: {status_response.status_code}")
    except Exception as e:
        print(f"   ❌ Status check error: {e}")
    
    # 3. Get available attacks
    print("3. Getting available attacks...")
    try:
        attacks_response = session.get(f"{API_BASE_URL}/api/mininet/attacks")
        if attacks_response.status_code == 200:
            attacks_data = attacks_response.json()
            attacks = attacks_data.get('attacks', [])
            print(f"   ✅ Available attacks: {attacks}")
        else:
            print(f"   ❌ Attacks check failed: {attacks_response.status_code}")
    except Exception as e:
        print(f"   ❌ Attacks check error: {e}")
    
    # 4. Start normal simulation
    print("4. Starting normal traffic simulation...")
    try:
        start_data = {
            'mode': 'normal',
            'duration': 10
        }
        start_response = session.post(f"{API_BASE_URL}/api/mininet/start", json=start_data)
        if start_response.status_code == 200:
            result = start_response.json()
            if result.get('success'):
                print(f"   ✅ Normal simulation started: {result.get('message')}")
                
                # Wait for completion
                print("   ⏳ Waiting for simulation to complete...")
                time.sleep(12)  # Wait a bit longer than duration
                
                # Check final status
                final_status = session.get(f"{API_BASE_URL}/api/mininet/status")
                if final_status.status_code == 200:
                    status = final_status.json()
                    print(f"   📊 Final status: Active={status.get('active')}")
                
            else:
                print(f"   ❌ Failed to start: {result.get('message')}")
        else:
            print(f"   ❌ Start request failed: {start_response.status_code}")
            print(f"   Response: {start_response.text}")
    except Exception as e:
        print(f"   ❌ Start simulation error: {e}")
    
    # 5. Test attack simulation
    print("5. Starting attack simulation...")
    try:
        attack_data = {
            'mode': 'attack',
            'attack_type': 'syn_flood',
            'duration': 10
        }
        attack_response = session.post(f"{API_BASE_URL}/api/mininet/start", json=attack_data)
        if attack_response.status_code == 200:
            result = attack_response.json()
            if result.get('success'):
                print(f"   ✅ Attack simulation started: {result.get('message')}")
                
                # Wait for completion
                print("   ⏳ Waiting for attack simulation to complete...")
                time.sleep(12)
                
            else:
                print(f"   ❌ Failed to start attack: {result.get('message')}")
        else:
            print(f"   ❌ Attack start failed: {attack_response.status_code}")
            print(f"   Response: {attack_response.text}")
    except Exception as e:
        print(f"   ❌ Attack simulation error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Simulation test completed!")
    print("\nNext steps:")
    print("1. Check the Dashboard for new alerts")
    print("2. View Network Map for topology updates")
    print("3. Use Threat Triage for alert analysis")
    
    return True

if __name__ == '__main__':
    test_simulation()
