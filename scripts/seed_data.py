#!/usr/bin/env python3
"""
Seed script for SOC Dashboard JSON storage files
Creates initial data for users, audit logs, and system configuration
"""

import os
import sys
import json
import bcrypt
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_users_data():
    """Create initial users data"""
    users_data = {
        "admin": {
            "password_hash": hash_password("SecureAdmin123!"),
            "role": "admin",
            "email": "admin@soc.local",
            "mfa_enabled": False,
            "mfa_secret": None,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "active": True,
            "failed_attempts": 0,
            "locked_until": None
        },
        "john_analyst": {
            "password_hash": hash_password("AnalystPass123!"),
            "role": "analyst",
            "email": "john.analyst@soc.local",
            "mfa_enabled": False,
            "mfa_secret": None,
            "created_at": (datetime.now() - timedelta(days=30)).isoformat(),
            "last_login": (datetime.now() - timedelta(hours=2)).isoformat(),
            "active": True,
            "failed_attempts": 0,
            "locked_until": None
        },
        "sarah_analyst": {
            "password_hash": hash_password("SecurePass123!"),
            "role": "analyst",
            "email": "sarah.analyst@soc.local",
            "mfa_enabled": True,
            "mfa_secret": "JBSWY3DPEHPK3PXP",  # Example secret for demo
            "created_at": (datetime.now() - timedelta(days=15)).isoformat(),
            "last_login": (datetime.now() - timedelta(minutes=30)).isoformat(),
            "active": True,
            "failed_attempts": 0,
            "locked_until": None
        },
        "mike_admin": {
            "password_hash": hash_password("AdminSecure123!"),
            "role": "admin",
            "email": "mike.admin@soc.local",
            "mfa_enabled": True,
            "mfa_secret": "HXDMVJECJJWSRB3HWIZR4IFUGFTMXBOZ",  # Example secret for demo
            "created_at": (datetime.now() - timedelta(days=45)).isoformat(),
            "last_login": (datetime.now() - timedelta(hours=1)).isoformat(),
            "active": True,
            "failed_attempts": 0,
            "locked_until": None
        },
        "inactive_user": {
            "password_hash": hash_password("InactivePass123!"),
            "role": "analyst",
            "email": "inactive@soc.local",
            "mfa_enabled": False,
            "mfa_secret": None,
            "created_at": (datetime.now() - timedelta(days=60)).isoformat(),
            "last_login": (datetime.now() - timedelta(days=30)).isoformat(),
            "active": False,
            "failed_attempts": 0,
            "locked_until": None
        }
    }
    return users_data

def create_audit_data():
    """Create sample audit log data"""
    audit_data = []
    
    # Sample audit events for the last 7 days
    base_time = datetime.now()
    
    # Login events
    for i in range(20):
        event_time = base_time - timedelta(hours=i*2, minutes=i*5)
        users = ["admin", "john_analyst", "sarah_analyst", "mike_admin"]
        user = users[i % len(users)]
        success = i % 5 != 0  # 80% success rate
        
        audit_data.append({
            "timestamp": event_time.isoformat() + 'Z',
            "event_type": "login_success" if success else "login_failed",
            "username": user,
            "ip_address": f"192.168.1.{100 + (i % 50)}",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "success": success,
            "details": {"method": "password", "mfa_used": user in ["sarah_analyst", "mike_admin"]},
            "error_message": None if success else "Invalid credentials"
        })
    
    # User management events
    user_events = [
        {
            "timestamp": (base_time - timedelta(days=1)).isoformat() + 'Z',
            "event_type": "user_created",
            "username": "admin",
            "ip_address": "192.168.1.105",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "success": True,
            "details": {"new_user": "sarah_analyst", "role": "analyst"},
            "error_message": None
        },
        {
            "timestamp": (base_time - timedelta(days=2)).isoformat() + 'Z',
            "event_type": "user_updated",
            "username": "admin",
            "ip_address": "192.168.1.105",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "success": True,
            "details": {"target_user": "inactive_user", "changes": {"active": False}},
            "error_message": None
        },
        {
            "timestamp": (base_time - timedelta(hours=6)).isoformat() + 'Z',
            "event_type": "mfa_enabled",
            "username": "sarah_analyst",
            "ip_address": "192.168.1.110",
            "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X)",
            "success": True,
            "details": {"method": "google_authenticator"},
            "error_message": None
        }
    ]
    audit_data.extend(user_events)
    
    # SOC operations events
    soc_events = []
    for i in range(15):
        event_time = base_time - timedelta(hours=i*3, minutes=i*10)
        users = ["john_analyst", "sarah_analyst"]
        user = users[i % len(users)]
        
        if i % 3 == 0:
            event_type = "alert_flagged"
        elif i % 3 == 1:
            event_type = "alert_dismissed"
        else:
            event_type = "threshold_changed"
        
        details = {}
        if event_type == "threshold_changed":
            details = {"old_threshold": 0.5, "new_threshold": 0.6}
        else:
            details = {"alert_id": 1000 + i}
        
        soc_events.append({
            "timestamp": event_time.isoformat() + 'Z',
            "event_type": event_type,
            "username": user,
            "ip_address": f"192.168.1.{110 + (i % 10)}",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "success": True,
            "details": details,
            "error_message": None
        })
    
    audit_data.extend(soc_events)
    
    # Security events
    security_events = [
        {
            "timestamp": (base_time - timedelta(hours=12)).isoformat() + 'Z',
            "event_type": "unauthorized_access",
            "username": "unknown_user",
            "ip_address": "203.0.113.45",
            "user_agent": "curl/7.68.0",
            "success": False,
            "details": {"resource": "/api/admin/users", "attempted_role": "analyst"},
            "error_message": "Insufficient permissions"
        },
        {
            "timestamp": (base_time - timedelta(hours=18)).isoformat() + 'Z',
            "event_type": "account_locked",
            "username": "system",
            "ip_address": "192.168.1.100",
            "user_agent": "SOC-Dashboard-System",
            "success": True,
            "details": {"locked_user": "test_user", "reason": "multiple_failed_attempts"},
            "error_message": None
        }
    ]
    audit_data.extend(security_events)
    
    # Sort by timestamp (newest first)
    audit_data.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return audit_data

def create_system_config():
    """Create system configuration data"""
    config_data = {
        "system": {
            "name": "SOC Dashboard",
            "version": "1.0.0",
            "environment": "development",
            "timezone": "UTC",
            "session_timeout": 28800,  # 8 hours
            "max_failed_attempts": 5,
            "lockout_duration": 1800,  # 30 minutes
            "password_policy": {
                "min_length": 8,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_digits": True,
                "require_special_chars": True,
                "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?"
            }
        },
        "security": {
            "jwt_expiry": 28800,  # 8 hours
            "refresh_token_expiry": 604800,  # 7 days
            "mfa_window": 1,  # 30 second window
            "rate_limiting": {
                "login_attempts": 5,
                "login_window": 300  # 5 minutes
            }
        },
        "dashboard": {
            "default_threshold": 0.5,
            "max_alerts_display": 100,
            "refresh_interval": 2000,  # 2 seconds
            "alert_retention_days": 30
        },
        "audit": {
            "max_log_entries": 10000,
            "retention_days": 90,
            "log_levels": ["INFO", "WARNING", "ERROR"],
            "sensitive_fields": ["password", "mfa_secret", "token"]
        }
    }
    return config_data

def main():
    """Main function to create all seed data"""
    print("🌱 Seeding SOC Dashboard data files...")
    
    # Ensure data directory exists
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    
    # Create users.json
    print("👥 Creating users.json...")
    users_data = create_users_data()
    with open(os.path.join(data_dir, "users.json"), "w") as f:
        json.dump(users_data, f, indent=2)
    print(f"   ✅ Created {len(users_data)} users")
    
    # Create audit.json
    print("📋 Creating audit.json...")
    audit_data = create_audit_data()
    with open(os.path.join(data_dir, "audit.json"), "w") as f:
        json.dump(audit_data, f, indent=2)
    print(f"   ✅ Created {len(audit_data)} audit events")
    
    # Create system_config.json
    print("⚙️  Creating system_config.json...")
    config_data = create_system_config()
    with open(os.path.join(data_dir, "system_config.json"), "w") as f:
        json.dump(config_data, f, indent=2)
    print("   ✅ Created system configuration")
    
    # Create empty audit.log for text logging
    audit_log_path = os.path.join(data_dir, "audit.log")
    if not os.path.exists(audit_log_path):
        with open(audit_log_path, "w") as f:
            f.write(f"# SOC Dashboard Audit Log - Created {datetime.now().isoformat()}\n")
        print("   ✅ Created audit.log file")
    
    print("\n🎉 Data seeding completed successfully!")
    print("\n📊 Summary:")
    print("   • Default admin user: admin / SecureAdmin123!")
    print("   • Sample analyst users with different MFA settings")
    print("   • Realistic audit log entries for the past week")
    print("   • System configuration with security policies")
    print("   • Ready for authentication testing and demo")
    
    print("\n🔐 User Accounts Created:")
    for username, user_data in users_data.items():
        status = "🟢 Active" if user_data["active"] else "🔴 Inactive"
        mfa = "🔒 MFA Enabled" if user_data["mfa_enabled"] else "🔓 MFA Disabled"
        print(f"   • {username} ({user_data['role']}) - {status} - {mfa}")
    
    print("\n🚀 You can now start the authenticated dashboard:")
    print("   python scripts/start_auth_dashboard.py")

if __name__ == "__main__":
    main()
