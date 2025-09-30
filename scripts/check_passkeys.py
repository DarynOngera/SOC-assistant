#!/usr/bin/env python3
"""
Check Passkeys Script
Diagnose passkey storage and retrieval issues
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database.mongodb_dal import get_dal
import base64

def check_passkeys():
    """Check all users' passkeys"""
    try:
        dal = get_dal()
        
        print("Checking Passkeys in Database")
        print("=" * 70)
        
        # Get all users
        users = dal.get_all_users()
        
        if not users:
            print("No users found in database.")
            return
        
        print(f"Found {len(users)} user(s)\n")
        
        for user in users:
            username = user.get('username', 'unknown')
            passkeys = user.get('passkeys', [])
            
            print(f"User: {username}")
            print(f"  Email: {user.get('email', 'N/A')}")
            print(f"  Role: {user.get('role', 'N/A')}")
            print(f"  Passkeys: {len(passkeys)}")
            
            if passkeys:
                for idx, pk in enumerate(passkeys, 1):
                    print(f"\n  Passkey #{idx}:")
                    print(f"    Name: {pk.get('name', 'N/A')}")
                    print(f"    Created: {pk.get('created_at', 'N/A')}")
                    print(f"    Credential ID: {pk.get('credential_id', 'N/A')[:50]}...")
                    
                    # Check if credential_data exists and is valid
                    cred_data = pk.get('credential_data')
                    if cred_data:
                        try:
                            decoded = base64.b64decode(cred_data)
                            print(f"    Credential Data: Valid ({len(decoded)} bytes)")
                            
                            # Try to parse as AttestedCredentialData
                            from fido2.webauthn import AttestedCredentialData
                            try:
                                acd = AttestedCredentialData(decoded)
                                print(f"    ✅ Can be parsed as AttestedCredentialData")
                                print(f"    Credential ID from data: {base64.b64encode(acd.credential_id).decode()[:50]}...")
                            except Exception as e:
                                print(f"    ❌ Cannot parse as AttestedCredentialData: {e}")
                        except Exception as e:
                            print(f"    ❌ Invalid base64: {e}")
                    else:
                        print(f"    ❌ No credential_data field")
            else:
                print("  No passkeys registered")
            
            print()
        
        print("=" * 70)
        print("\nDiagnostic Summary:")
        print("1. Check if the user you're trying to authenticate with has passkeys")
        print("2. Verify credential_data can be parsed as AttestedCredentialData")
        print("3. If parsing fails, delete the passkey and re-register")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(check_passkeys())
