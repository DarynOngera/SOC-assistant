#!/usr/bin/env python3
"""
Fix User Fields Script
Adds missing authentication preference fields to existing users
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database.mongodb_dal import get_dal
from datetime import datetime

def fix_user_fields():
    """Add missing fields to all users"""
    try:
        dal = get_dal()
        
        print("Fixing user fields...")
        print("=" * 60)
        
        # Get all users
        users = dal.get_all_users()
        
        if not users:
            print("No users found in database.")
            print("\nTip: Start the server once to create the default admin user.")
            return
        
        print(f"Found {len(users)} user(s)\n")
        
        fixed_count = 0
        for user in users:
            username = user.get('username', 'unknown')
            print(f"Checking user: {username}")
            
            # Fields to add if missing
            updates = {}
            
            if 'email_verified' not in user:
                updates['email_verified'] = False
                print(f"  + Adding email_verified: False")
            
            if 'default_auth_method' not in user:
                updates['default_auth_method'] = 'password'
                print(f"  + Adding default_auth_method: password")
            
            if 'email_otp_enabled' not in user:
                updates['email_otp_enabled'] = False
                print(f"  + Adding email_otp_enabled: False")
            
            if 'passkey_enabled' not in user:
                updates['passkey_enabled'] = False
                print(f"  + Adding passkey_enabled: False")
            
            if 'passkeys' not in user:
                updates['passkeys'] = []
                print(f"  + Adding passkeys: []")
            
            # Apply updates if any
            if updates:
                updates['updated_at'] = datetime.utcnow()
                success = dal.update_user(username, updates)
                
                if success:
                    print(f"  ✓ Updated {username}")
                    fixed_count += 1
                else:
                    print(f"  ✗ Failed to update {username}")
            else:
                print(f"  ✓ No updates needed")
            
            print()
        
        print("=" * 60)
        print(f"Summary: Fixed {fixed_count} user(s)")
        print("\nNext steps:")
        print("1. Restart the backend server")
        print("2. Refresh the frontend")
        print("3. Try adding a passkey again")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure MongoDB is running: mongod")
        print("2. Check MongoDB connection in .env")
        print("3. Verify database name is correct")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(fix_user_fields())
