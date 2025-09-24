#!/usr/bin/env python3
"""
MongoDB Migration Utilities
Handles migration of existing JSON data to MongoDB collections
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple
from pathlib import Path

from .mongodb_dal import get_dal
from .schemas import DocumentBuilder, UserRole, AlertSeverity, AlertStatus

logger = logging.getLogger(__name__)

class DataMigrator:
    """Handles migration of existing data to MongoDB"""
    
    def __init__(self):
        self.dal = get_dal()
        self.migration_log = []
    
    def migrate_users_from_json(self, json_file_path: str) -> Tuple[bool, Dict[str, Any]]:
        """Migrate users from JSON file to MongoDB"""
        try:
            if not os.path.exists(json_file_path):
                return True, {"message": "No existing users file found", "migrated": 0, "errors": 0}
            
            with open(json_file_path, 'r') as f:
                users_data = json.load(f)
            
            migrated_count = 0
            error_count = 0
            errors = []
            
            for username, user_data in users_data.items():
                try:
                    # Check if user already exists in MongoDB
                    existing_user = self.dal.get_user_by_username(username)
                    if existing_user:
                        logger.info(f"User {username} already exists in MongoDB, skipping")
                        continue
                    
                    # Convert datetime strings to datetime objects
                    created_at = user_data.get('created_at')
                    if isinstance(created_at, str):
                        user_data['created_at'] = datetime.fromisoformat(created_at)
                    
                    last_login = user_data.get('last_login')
                    if isinstance(last_login, str):
                        user_data['last_login'] = datetime.fromisoformat(last_login)
                    
                    locked_until = user_data.get('locked_until')
                    if isinstance(locked_until, str):
                        user_data['locked_until'] = datetime.fromisoformat(locked_until)
                    
                    # Create user document
                    success, message, user_id = self.dal.create_user(
                        username=username,
                        password_hash=user_data['password_hash'],
                        email=user_data['email'],
                        role=user_data['role'],
                        active=user_data.get('active', True),
                        mfa_enabled=user_data.get('mfa_enabled', False),
                        mfa_secret=user_data.get('mfa_secret'),
                        failed_attempts=user_data.get('failed_attempts', 0),
                        locked_until=user_data.get('locked_until')
                    )
                    
                    if success:
                        migrated_count += 1
                        logger.info(f"Migrated user: {username}")
                    else:
                        error_count += 1
                        errors.append(f"Failed to migrate user {username}: {message}")
                        
                except Exception as e:
                    error_count += 1
                    error_msg = f"Error migrating user {username}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # Backup original file
            if migrated_count > 0:
                backup_path = f"{json_file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(json_file_path, backup_path)
                logger.info(f"Backed up original users file to: {backup_path}")
            
            result = {
                "migrated": migrated_count,
                "errors": error_count,
                "error_details": errors,
                "message": f"Migration completed: {migrated_count} users migrated, {error_count} errors"
            }
            
            self.migration_log.append({
                "timestamp": datetime.now().isoformat(),
                "operation": "migrate_users",
                "result": result
            })
            
            return True, result
            
        except Exception as e:
            error_msg = f"Failed to migrate users: {str(e)}"
            logger.error(error_msg)
            return False, {"error": error_msg}
    
    def migrate_audit_logs_from_json(self, json_file_path: str) -> Tuple[bool, Dict[str, Any]]:
        """Migrate audit logs from JSON file to MongoDB"""
        try:
            if not os.path.exists(json_file_path):
                return True, {"message": "No existing audit logs file found", "migrated": 0, "errors": 0}
            
            with open(json_file_path, 'r') as f:
                audit_data = json.load(f)
            
            migrated_count = 0
            error_count = 0
            errors = []
            
            # Handle both list and dict formats
            if isinstance(audit_data, dict):
                audit_entries = audit_data.get('events', [])
            else:
                audit_entries = audit_data
            
            for entry in audit_entries:
                try:
                    # Convert timestamp string to datetime
                    timestamp = entry.get('timestamp')
                    if isinstance(timestamp, str):
                        entry['timestamp'] = datetime.fromisoformat(timestamp)
                    
                    success, message = self.dal.create_audit_log(
                        event_type=entry.get('event_type', 'unknown'),
                        username=entry.get('username', 'system'),
                        ip_address=entry.get('ip_address', '127.0.0.1'),
                        action=entry.get('action', 'unknown'),
                        success=entry.get('success', True),
                        user_agent=entry.get('user_agent'),
                        resource=entry.get('resource'),
                        details=entry.get('details', {}),
                        error_message=entry.get('error_message'),
                        session_id=entry.get('session_id'),
                        request_id=entry.get('request_id'),
                        duration_ms=entry.get('duration_ms')
                    )
                    
                    if success:
                        migrated_count += 1
                    else:
                        error_count += 1
                        errors.append(f"Failed to migrate audit entry: {message}")
                        
                except Exception as e:
                    error_count += 1
                    error_msg = f"Error migrating audit entry: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # Backup original file
            if migrated_count > 0:
                backup_path = f"{json_file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(json_file_path, backup_path)
                logger.info(f"Backed up original audit logs file to: {backup_path}")
            
            result = {
                "migrated": migrated_count,
                "errors": error_count,
                "error_details": errors,
                "message": f"Migration completed: {migrated_count} audit entries migrated, {error_count} errors"
            }
            
            self.migration_log.append({
                "timestamp": datetime.now().isoformat(),
                "operation": "migrate_audit_logs",
                "result": result
            })
            
            return True, result
            
        except Exception as e:
            error_msg = f"Failed to migrate audit logs: {str(e)}"
            logger.error(error_msg)
            return False, {"error": error_msg}
    
    def create_default_admin_user(self) -> Tuple[bool, str]:
        """Create default admin user if no users exist"""
        try:
            # Check if any users exist
            users = self.dal.get_all_users()
            if users:
                return True, "Users already exist, skipping default admin creation"
            
            # Create default admin user
            success, message, user_id = self.dal.create_user(
                username="admin",
                password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.gSInqS",  # SecureAdmin123!
                email="admin@soc.local",
                role=UserRole.ADMIN.value,
                active=True,
                mfa_enabled=False
            )
            
            if success:
                logger.info("Created default admin user")
                return True, "Default admin user created successfully"
            else:
                return False, f"Failed to create default admin user: {message}"
                
        except Exception as e:
            error_msg = f"Error creating default admin user: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def migrate_sample_data(self) -> Tuple[bool, Dict[str, Any]]:
        """Create sample data for testing and demonstration"""
        try:
            results = {}
            
            # Create sample users
            sample_users = [
                {
                    "username": "analyst1",
                    "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.gSInqS",  # SecureAnalyst123!
                    "email": "analyst1@soc.local",
                    "role": UserRole.ANALYST.value,
                    "first_name": "John",
                    "last_name": "Doe"
                },
                {
                    "username": "analyst2",
                    "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.gSInqS",  # SecureAnalyst123!
                    "email": "analyst2@soc.local",
                    "role": UserRole.ANALYST.value,
                    "first_name": "Jane",
                    "last_name": "Smith"
                }
            ]
            
            user_count = 0
            for user_data in sample_users:
                existing_user = self.dal.get_user_by_username(user_data["username"])
                if not existing_user:
                    success, message, user_id = self.dal.create_user(**user_data)
                    if success:
                        user_count += 1
            
            results["sample_users"] = user_count
            
            # Create sample alerts
            sample_alerts = []
            for i in range(10):
                alert_data = {
                    "timestamp": datetime.utcnow(),
                    "severity": AlertSeverity.HIGH.value if i < 3 else AlertSeverity.MEDIUM.value,
                    "source_ip": f"192.168.1.{100 + i}",
                    "destination_ip": f"10.0.0.{50 + i}",
                    "attack_type": "Brute Force" if i < 5 else "Port Scan",
                    "anomaly_score": 0.8 + (i * 0.02),
                    "confidence": 0.75 + (i * 0.01),
                    "protocol": "tcp",
                    "source_port": 1024 + i,
                    "destination_port": 22 if i < 5 else 80
                }
                sample_alerts.append(alert_data)
            
            alert_count = 0
            for alert_data in sample_alerts:
                success, message, alert_id = self.dal.create_alert(alert_data)
                if success:
                    alert_count += 1
            
            results["sample_alerts"] = alert_count
            
            # Create sample system stats
            stats_data = {
                "total_processed": 1000,
                "anomalies_detected": 50,
                "total_alerts": alert_count,
                "active_alerts": alert_count,
                "system_health": "healthy",
                "detection_threshold": 0.5,
                "severity_distribution": {
                    "critical": 0,
                    "high": 3,
                    "medium": 7,
                    "low": 0
                },
                "detection_rate": 5.0
            }
            
            success, message = self.dal.save_system_stats("realtime", stats_data)
            results["system_stats"] = 1 if success else 0
            
            return True, results
            
        except Exception as e:
            error_msg = f"Error creating sample data: {str(e)}"
            logger.error(error_msg)
            return False, {"error": error_msg}
    
    def run_full_migration(self, data_directory: str = "data") -> Dict[str, Any]:
        """Run complete migration process"""
        try:
            migration_results = {
                "timestamp": datetime.now().isoformat(),
                "operations": {}
            }
            
            # Create data directory path
            data_path = Path(data_directory)
            
            # Migrate users
            users_file = data_path / "users.json"
            success, result = self.migrate_users_from_json(str(users_file))
            migration_results["operations"]["users"] = result
            
            # Migrate audit logs
            audit_file = data_path / "audit.json"
            success, result = self.migrate_audit_logs_from_json(str(audit_file))
            migration_results["operations"]["audit_logs"] = result
            
            # Create default admin if no users exist
            success, message = self.create_default_admin_user()
            migration_results["operations"]["default_admin"] = {"message": message, "success": success}
            
            # Create sample data
            success, result = self.migrate_sample_data()
            migration_results["operations"]["sample_data"] = result
            
            # Save migration log
            self.save_migration_log(migration_results)
            
            return migration_results
            
        except Exception as e:
            error_msg = f"Migration failed: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "timestamp": datetime.now().isoformat()}
    
    def save_migration_log(self, results: Dict[str, Any]):
        """Save migration log to file"""
        try:
            log_file = Path("data") / "migration_log.json"
            log_file.parent.mkdir(exist_ok=True)
            
            # Load existing log or create new
            if log_file.exists():
                with open(log_file, 'r') as f:
                    existing_log = json.load(f)
            else:
                existing_log = {"migrations": []}
            
            # Add new migration
            existing_log["migrations"].append(results)
            
            # Save updated log
            with open(log_file, 'w') as f:
                json.dump(existing_log, f, indent=2, default=str)
            
            logger.info(f"Migration log saved to: {log_file}")
            
        except Exception as e:
            logger.error(f"Failed to save migration log: {e}")

def run_migration(data_directory: str = "data") -> Dict[str, Any]:
    """Convenience function to run migration"""
    migrator = DataMigrator()
    return migrator.run_full_migration(data_directory)

def migrate_existing_data() -> Dict[str, Any]:
    """Migrate data from common locations"""
    migrator = DataMigrator()
    
    # Try different possible data locations
    possible_locations = [
        "data",
        "src/dashboard/data",
        "src/auth/data",
        "."
    ]
    
    for location in possible_locations:
        if os.path.exists(location):
            logger.info(f"Found data directory: {location}")
            return migrator.run_full_migration(location)
    
    # No existing data found, create sample data
    logger.info("No existing data found, creating sample data")
    return migrator.run_full_migration("data")
