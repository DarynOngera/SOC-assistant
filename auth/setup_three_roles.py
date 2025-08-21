#!/usr/bin/env python3
"""
Simplified 3-Role RBAC Setup
Creates users for: Super Admin, Analyst, Viewer
"""

import json
import os
from datetime import datetime
from auth_utils import AuthManager
from flask import Flask

def setup_three_roles():
    """Create users for simplified 3-role system"""
    
    # Initialize Flask app for AuthManager
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key')
    app.config['BCRYPT_LOG_ROUNDS'] = 12
    
    auth_manager = AuthManager(app)
    
    # Define users for each role
    users_to_create = [
        {
            'username': 'admin',
            'password': 'SecurePass123!',
            'role': 'super_admin',
            'description': 'System Administrator - Full access'
        },
        {
            'username': 'analyst',
            'password': 'Analyst123!',
            'role': 'analyst',
            'description': 'Security Analyst - Threat analysis and alert management'
        },
        {
            'username': 'viewer',
            'password': 'Viewer123!',
            'role': 'viewer',
            'description': 'Viewer - Read-only access to dashboards'
        }
    ]
    
    # Create users dictionary
    users = {}
    
    print("🔐 Setting up 3-Role RBAC System...")
    print("=" * 50)
    
    for user_info in users_to_create:
        username = user_info['username']
        password = user_info['password']
        role = user_info['role']
        description = user_info['description']
        
        # Hash password
        hashed_password = auth_manager.hash_password(password)
        
        # Create user
        users[username] = {
            'password': hashed_password,
            'role': role,
            'created_at': datetime.utcnow().isoformat(),
            'created_by': 'system',
            'last_login': None,
            'active': True,
            'is_super_admin': (role == 'super_admin'),
            'description': description
        }
        
        print(f"✅ {username:10} | {role:12} | {description}")
    
    # Save users to file
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=2)
    
    print("=" * 50)
    print(f"✅ Successfully created {len(users_to_create)} users")
    
    # Display login credentials
    print("\n🔑 Login Credentials:")
    print("=" * 50)
    for user_info in users_to_create:
        print(f"Username: {user_info['username']:10} | Password: {user_info['password']}")
    
    print("\n📋 Role Permissions:")
    print("=" * 50)
    print("🔴 Super Admin - Full system control, user management, system config")
    print("🟡 Analyst     - Alert analysis, data management, model interaction")  
    print("🟢 Viewer      - Read-only dashboard access, view alerts/statistics")
    
    return users

if __name__ == "__main__":
    setup_three_roles()
