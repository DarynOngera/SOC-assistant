#!/usr/bin/env python3
"""
Migration script to convert existing plain text passwords to hashed passwords
"""

import json
import os
from datetime import datetime
from auth_utils import AuthManager
from flask import Flask

def migrate_users():
    """Migrate existing users.json to use hashed passwords"""
    
    # Create temporary Flask app for auth manager
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = 'temp-key-for-migration'
    auth_manager = AuthManager(app)
    
    # Load existing users
    users_file = 'users.json'
    backup_file = f'users_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    
    if not os.path.exists(users_file):
        print(f"No {users_file} found. Nothing to migrate.")
        return
    
    with open(users_file, 'r') as f:
        old_users = json.load(f)
    
    # Create backup
    with open(backup_file, 'w') as f:
        json.dump(old_users, f, indent=2)
    print(f"Created backup: {backup_file}")
    
    # Migrate users
    new_users = {}
    
    for username, password in old_users.items():
        # Check if already migrated (has dict structure)
        if isinstance(password, dict):
            print(f"User {username} already migrated, skipping...")
            new_users[username] = password
            continue
        
        # Hash the plain text password
        hashed_password = auth_manager.hash_password(password)
        
        new_users[username] = {
            'password': hashed_password,
            'created_at': datetime.utcnow().isoformat(),
            'last_login': None,
            'active': True,
            'migrated_at': datetime.utcnow().isoformat()
        }
        
        print(f"Migrated user: {username}")
    
    # Save migrated users
    with open(users_file, 'w') as f:
        json.dump(new_users, f, indent=2)
    
    print(f"\nMigration complete! Migrated {len(new_users)} users.")
    print(f"Backup saved as: {backup_file}")

if __name__ == '__main__':
    migrate_users()
