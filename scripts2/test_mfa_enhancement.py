#!/usr/bin/env python3
"""
Test script to verify MFA enhancement functionality
"""

import requests
import json

def test_mfa_check_endpoint():
    """Test the new MFA check endpoint"""
    url = "http://localhost:5000/api/auth/check-mfa"
    
    # Test with existing user that has MFA enabled
    test_cases = [
        {"username": "admin", "expected_mfa": True},
        {"username": "analyst1", "expected_mfa": False},
        {"username": "nonexistent", "expected_mfa": False},
        {"username": "", "expected_error": True}
    ]
    
    print("Testing MFA Check Endpoint:")
    print("=" * 40)
    
    for case in test_cases:
        try:
            response = requests.post(url, json={"username": case["username"]})
            
            if case.get("expected_error"):
                if response.status_code == 400:
                    print(f"✅ Empty username correctly rejected")
                else:
                    print(f"❌ Expected 400 error for empty username, got {response.status_code}")
            else:
                if response.status_code == 200:
                    data = response.json()
                    mfa_required = data.get("mfa_required", False)
                    username = case["username"] or "empty"
                    
                    if "expected_mfa" in case:
                        if mfa_required == case["expected_mfa"]:
                            print(f"✅ User '{username}': MFA required = {mfa_required} (correct)")
                        else:
                            print(f"❌ User '{username}': Expected MFA = {case['expected_mfa']}, got {mfa_required}")
                    else:
                        print(f"ℹ️  User '{username}': MFA required = {mfa_required}")
                else:
                    print(f"❌ Request failed with status {response.status_code}: {response.text}")
                    
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to server. Make sure the dashboard is running on localhost:5000")
            return False
        except Exception as e:
            print(f"❌ Error testing {case}: {e}")
    
    return True

if __name__ == "__main__":
    print("MFA Enhancement Test")
    print("Make sure the dashboard server is running before running this test")
    print()
    
    success = test_mfa_check_endpoint()
    
    if success:
        print("\n" + "=" * 40)
        print("✅ MFA enhancement testing completed!")
        print("\nTo test the full user experience:")
        print("1. Open the frontend in your browser")
        print("2. Start typing a username (e.g., 'admin')")
        print("3. The MFA field should appear automatically when you tab out")
        print("4. No need to attempt login first!")
    else:
        print("\n❌ Some tests failed. Check the server logs.")
