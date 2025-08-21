#!/usr/bin/env python3
"""
RBAC User Setup Script
Creates sample users for all roles in the SOC Assistant system
"""

import json
import os
from datetime import datetime
from auth_utils import AuthManager
from rbac_utils import Role, create_default_super_admin
from flask import Flask

def setup_rbac_users():
    """Create users for all RBAC roles"""
    
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
            'role': Role.SUPER_ADMIN,
            'description': 'System Super Administrator'
        },
        {
            'username': 'soc_manager',
            'password': 'Manager123!',
            'role': Role.SOC_MANAGER,
            'description': 'SOC Manager - Team leadership and user management'
        },
        {
            'username': 'senior_analyst',
            'password': 'Senior123!',
            'role': Role.SENIOR_ANALYST,
            'description': 'Senior Analyst - Advanced threat analysis'
        },
        {
            'username': 'analyst',
            'password': 'Analyst123!',
            'role': Role.ANALYST,
            'description': 'Analyst - Basic threat analysis'
        },
        {
            'username': 'viewer',
            'password': 'Viewer123!',
            'role': Role.VIEWER,
            'description': 'Viewer - Read-only access'
        }
    ]
    
    # Load existing users or create new file
    users_file = 'users.json'
    try:
        with open(users_file, 'r') as f:
            users = json.load(f)
    except FileNotFoundError:
        users = {}
    
    print("🔐 Setting up RBAC users...")
    print("=" * 50)
    
    for user_info in users_to_create:
        username = user_info['username']
        password = user_info['password']
        role = user_info['role']
        description = user_info['description']
        
        # Hash password
        hashed_password = auth_manager.hash_password(password)
        
        # Create or update user
        users[username] = {
            'password': hashed_password,
            'role': role.value,
            'created_at': datetime.utcnow().isoformat(),
            'created_by': 'system',
            'last_login': None,
            'active': True,
            'is_super_admin': (role == Role.SUPER_ADMIN),
            'description': description
        }
        
        print(f"✅ {username:15} | {role.value:15} | {description}")
    
    # Save users to file
    with open(users_file, 'w') as f:
        json.dump(users, f, indent=2)
    
    print("=" * 50)
    print(f"✅ Successfully created {len(users_to_create)} users")
    print(f"📁 Users saved to: {users_file}")
    
    # Display login credentials
    print("\n🔑 Login Credentials:")
    print("=" * 50)
    for user_info in users_to_create:
        print(f"Username: {user_info['username']:15} | Password: {user_info['password']}")
    
    print("\n📋 Role Hierarchy (High to Low):")
    print("=" * 50)
    print("1. Super Admin    - Full system control")
    print("2. SOC Manager    - Team and user management")
    print("3. Senior Analyst - Advanced threat analysis")
    print("4. Analyst        - Basic threat analysis")
    print("5. Viewer         - Read-only access")
    
    return users

if __name__ == "__main__":
    setup_rbac_users()
