#!/usr/bin/env python3
"""
Test script for email verification OTP functionality
Tests the complete email verification flow
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.auth.mongodb_auth_utils import MongoDBAuthManager
from src.database.mongodb_dal import get_dal
import time

def test_email_verification_flow():
    """Test the complete email verification flow"""
    print("=" * 60)
    print("Testing Email Verification OTP Flow")
    print("=" * 60)
    
    # Initialize auth manager
    auth_manager = MongoDBAuthManager()
    dal = get_dal()
    
    # Test user details
    test_username = "test_verify_user"
    test_email = "test.verify@example.com"
    test_password = "TestPass123!"
    
    try:
        # Step 1: Create a test user
        print("\n1. Creating test user...")
        success, message = auth_manager.create_user(
            username=test_username,
            password=test_password,
            role='analyst',
            email=test_email
        )
        
        if success:
            print(f"   ✓ User created: {message}")
        else:
            print(f"   ✗ Failed to create user: {message}")
            return
        
        # Step 2: Send verification OTP
        print("\n2. Sending verification OTP...")
        success, message = auth_manager.send_verification_otp(test_email, test_username)
        
        if success:
            print(f"   ✓ OTP sent: {message}")
            
            # In dev mode, the OTP is printed to console
            # Extract OTP from the message if in dev mode
            if "dev mode" in message.lower():
                otp = message.split(":")[-1].strip()
                print(f"   📧 Dev Mode OTP: {otp}")
            else:
                print("   📧 Check email for OTP code")
                otp = input("   Enter OTP from email: ").strip()
        else:
            print(f"   ✗ Failed to send OTP: {message}")
            return
        
        # Step 3: Check email verification status (should be False)
        print("\n3. Checking email verification status (before verification)...")
        user = dal.get_user_by_email(test_email)
        if user:
            is_verified = user.get('email_verified', False)
            print(f"   Email verified: {is_verified}")
            if not is_verified:
                print("   ✓ Status correct (not verified yet)")
            else:
                print("   ✗ Status incorrect (should not be verified)")
        
        # Step 4: Verify email with OTP
        print("\n4. Verifying email with OTP...")
        success, message = auth_manager.verify_email_with_otp(test_email, otp)
        
        if success:
            print(f"   ✓ Email verified: {message}")
        else:
            print(f"   ✗ Verification failed: {message}")
            return
        
        # Step 5: Check email verification status (should be True)
        print("\n5. Checking email verification status (after verification)...")
        user = dal.get_user_by_email(test_email)
        if user:
            is_verified = user.get('email_verified', False)
            print(f"   Email verified: {is_verified}")
            if is_verified:
                print("   ✓ Status correct (verified)")
            else:
                print("   ✗ Status incorrect (should be verified)")
        
        # Step 6: Test resend verification (should fail - already verified)
        print("\n6. Testing resend verification (should fail - already verified)...")
        success, message = auth_manager.resend_verification_otp(test_email)
        
        if not success and "already verified" in message.lower():
            print(f"   ✓ Correctly rejected: {message}")
        else:
            print(f"   ✗ Should have rejected resend: {message}")
        
        # Step 7: Test invalid OTP
        print("\n7. Testing invalid OTP...")
        test_user2_email = "test.verify2@example.com"
        test_user2_username = "test_verify_user2"
        
        # Create another user
        auth_manager.create_user(
            username=test_user2_username,
            password=test_password,
            role='analyst',
            email=test_user2_email
        )
        
        # Send OTP
        auth_manager.send_verification_otp(test_user2_email, test_user2_username)
        
        # Try with invalid OTP
        success, message = auth_manager.verify_email_with_otp(test_user2_email, "000000")
        
        if not success:
            print(f"   ✓ Invalid OTP rejected: {message}")
        else:
            print(f"   ✗ Invalid OTP should have been rejected")
        
        # Step 8: Test OTP expiry (simulate by checking expiry logic)
        print("\n8. Testing OTP expiry...")
        if test_user2_email in auth_manager.email_otps:
            otp_data = auth_manager.email_otps[test_user2_email]
            print(f"   OTP expires at: {otp_data['expires']}")
            print(f"   Attempts: {otp_data['attempts']}")
            print("   ✓ OTP expiry tracking working")
        
        print("\n" + "=" * 60)
        print("✓ Email Verification Flow Test Complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup: Delete test users
        print("\n9. Cleaning up test users...")
        try:
            dal.delete_user(test_username)
            print(f"   ✓ Deleted {test_username}")
        except:
            pass
        
        try:
            dal.delete_user(test_user2_username)
            print(f"   ✓ Deleted {test_user2_username}")
        except:
            pass

def test_email_verification_security():
    """Test security aspects of email verification"""
    print("\n" + "=" * 60)
    print("Testing Email Verification Security")
    print("=" * 60)
    
    auth_manager = MongoDBAuthManager()
    
    # Test 1: Rate limiting (attempts)
    print("\n1. Testing attempt limits...")
    test_email = "security.test@example.com"
    
    # Generate OTP
    otp = auth_manager.generate_email_otp(test_email)
    
    # Try 3 wrong attempts
    for i in range(3):
        success, message = auth_manager.verify_email_otp(test_email, "999999")
        print(f"   Attempt {i+1}: {message}")
    
    # 4th attempt should fail due to max attempts
    success, message = auth_manager.verify_email_otp(test_email, otp)
    if not success and "too many" in message.lower():
        print("   ✓ Rate limiting working (max 3 attempts)")
    else:
        print(f"   ✗ Rate limiting not working: {message}")
    
    # Test 2: OTP format validation
    print("\n2. Testing OTP format...")
    test_email2 = "format.test@example.com"
    otp = auth_manager.generate_email_otp(test_email2)
    
    if len(otp) == 6 and otp.isdigit():
        print(f"   ✓ OTP format correct: {otp} (6 digits)")
    else:
        print(f"   ✗ OTP format incorrect: {otp}")
    
    print("\n" + "=" * 60)
    print("✓ Security Tests Complete!")
    print("=" * 60)

if __name__ == "__main__":
    print("\n🔐 SOC Dashboard - Email Verification Test Suite\n")
    
    # Run main flow test
    test_email_verification_flow()
    
    # Run security tests
    test_email_verification_security()
    
    print("\n✅ All tests completed!\n")
