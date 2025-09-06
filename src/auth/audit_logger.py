#!/usr/bin/env python3
"""
Audit logging system for SOC Dashboard
Tracks all user actions and security events for compliance and monitoring
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

class AuditEventType(Enum):
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    
    # MFA events
    MFA_SETUP = "mfa_setup"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    MFA_FAILED = "mfa_failed"
    
    # User management events
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    PASSWORD_CHANGED = "password_changed"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    
    # SOC operations
    ALERT_FLAGGED = "alert_flagged"
    ALERT_DISMISSED = "alert_dismissed"
    THRESHOLD_CHANGED = "threshold_changed"
    MONITORING_STARTED = "monitoring_started"
    MONITORING_STOPPED = "monitoring_stopped"
    
    # CSV operations
    CSV_UPLOAD = "csv_upload"
    CSV_ANALYSIS = "csv_analysis"
    CSV_REPORT_GENERATED = "csv_report_generated"
    CSV_CLEANUP = "csv_cleanup"
    
    # System events
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PERMISSION_DENIED = "permission_denied"
    SYSTEM_ERROR = "system_error"

class AuditLogger:
    def __init__(self, log_file: str = "data/audit.log", json_file: str = "data/audit.json"):
        self.log_file = log_file
        self.json_file = json_file
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.json_file), exist_ok=True)
        
        # Setup structured logging
        self.logger = logging.getLogger('soc_audit')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # File handler for audit logs
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
    def log_event(self, 
                  event_type: AuditEventType, 
                  username: str = None, 
                  ip_address: str = None,
                  user_agent: str = None,
                  details: Dict = None,
                  success: bool = True,
                  error_message: str = None):
        """Log an audit event"""
        
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Create audit record with unique ID
        import uuid
        audit_record = {
            'id': str(uuid.uuid4()),
            'timestamp': timestamp,
            'event_type': event_type.value,
            'username': username,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'success': success,
            'details': details or {},
            'error_message': error_message
        }
        
        # Log to structured file
        self._append_to_json_log(audit_record)
        
        # Log to text file
        log_message = self._format_log_message(audit_record)
        if success:
            self.logger.info(log_message)
        else:
            self.logger.warning(log_message)
    
    def _format_log_message(self, record: Dict) -> str:
        """Format audit record for text logging"""
        parts = [
            f"Event: {record['event_type']}",
            f"User: {record['username'] or 'N/A'}",
            f"IP: {record['ip_address'] or 'N/A'}",
            f"Success: {record['success']}"
        ]
        
        if record['details']:
            details_str = ', '.join([f"{k}={v}" for k, v in record['details'].items()])
            parts.append(f"Details: {details_str}")
        
        if record['error_message']:
            parts.append(f"Error: {record['error_message']}")
        
        return ' | '.join(parts)
    
    def _append_to_json_log(self, record: Dict):
        """Append audit record to JSON log file"""
        try:
            # Read existing records
            records = []
            if os.path.exists(self.json_file):
                with open(self.json_file, 'r') as f:
                    try:
                        records = json.load(f)
                    except json.JSONDecodeError:
                        records = []
            
            # Append new record
            records.append(record)
            
            # Keep only last 10000 records to prevent file from growing too large
            if len(records) > 10000:
                records = records[-10000:]
            
            # Write back to file
            with open(self.json_file, 'w') as f:
                json.dump(records, f, indent=2)
                
        except Exception as e:
            # Fallback to text logging if JSON logging fails
            self.logger.error(f"Failed to write JSON audit log: {e}")
    
    def get_audit_logs(self, page: int = 1, per_page: int = 50, event_type: str = None, 
                      username: str = None, start_date: str = None, end_date: str = None) -> Dict:
        """Retrieve audit logs with filtering"""
        
        try:
            if not os.path.exists(self.json_file):
                return []
            
            with open(self.json_file, 'r') as f:
                records = json.load(f)
            
            # Apply filters
            filtered_records = []
            
            for record in records:
                # Date filter
                if start_date and record['timestamp'] < start_date:
                    continue
                if end_date and record['timestamp'] > end_date:
                    continue
                
                # Username filter
                if username and record.get('username') != username:
                    continue
                
                # Event type filter
                if event_type and record.get('event_type') != event_type:
                    continue
                
                filtered_records.append(record)
            
            # Sort by timestamp (newest first)
            filtered_records.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Apply pagination
            offset = (page - 1) * per_page
            limit = per_page
            paginated_records = filtered_records[offset:offset + limit]
            
            return {
                'logs': paginated_records,
                'total': len(filtered_records),
                'page': page,
                'per_page': per_page,
                'total_pages': (len(filtered_records) + per_page - 1) // per_page
            }
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve audit logs: {e}")
            return []
    
    def get_audit_summary(self, days: int = 30) -> Dict:
        """Get audit summary for the last N days"""
        
        try:
            # Calculate start date
            start_date = (datetime.utcnow() - timedelta(days=days)).isoformat() + 'Z'
            
            records = self.get_audit_logs(start_date=start_date, limit=10000)
            
            # Count events by type
            event_counts = {}
            user_activity = {}
            failed_logins = 0
            successful_logins = 0
            
            for record in records:
                event_type = record.get('event_type', 'unknown')
                username = record.get('username', 'unknown')
                
                # Count by event type
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
                
                # Count by user
                if username != 'unknown':
                    user_activity[username] = user_activity.get(username, 0) + 1
                
                # Count login attempts
                if event_type == 'login_success':
                    successful_logins += 1
                elif event_type == 'login_failed':
                    failed_logins += 1
            
            return {
                'period_days': days,
                'total_events': len(records),
                'event_counts': event_counts,
                'user_activity': user_activity,
                'login_stats': {
                    'successful': successful_logins,
                    'failed': failed_logins,
                    'success_rate': round(successful_logins / max(1, successful_logins + failed_logins) * 100, 2)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate audit summary: {e}")
            return {}
    
    def get_security_alerts(self, days: int = 7) -> List[Dict]:
        """Get security-related events that may require attention"""
        
        try:
            start_date = (datetime.utcnow() - timedelta(days=days)).isoformat() + 'Z'
            records = self.get_audit_logs(start_date=start_date, limit=10000)
            
            security_events = []
            
            # Track failed login attempts by user
            failed_attempts = {}
            
            for record in records:
                event_type = record.get('event_type')
                username = record.get('username', 'unknown')
                
                # Multiple failed login attempts
                if event_type == 'login_failed':
                    if username not in failed_attempts:
                        failed_attempts[username] = []
                    failed_attempts[username].append(record)
                
                # Unauthorized access attempts
                elif event_type in ['unauthorized_access', 'permission_denied']:
                    security_events.append({
                        'type': 'unauthorized_access',
                        'severity': 'medium',
                        'timestamp': record['timestamp'],
                        'username': username,
                        'ip_address': record.get('ip_address'),
                        'details': record.get('details', {})
                    })
                
                # Account lockouts
                elif event_type == 'account_locked':
                    security_events.append({
                        'type': 'account_locked',
                        'severity': 'high',
                        'timestamp': record['timestamp'],
                        'username': username,
                        'ip_address': record.get('ip_address'),
                        'details': record.get('details', {})
                    })
            
            # Check for suspicious failed login patterns
            for username, attempts in failed_attempts.items():
                if len(attempts) >= 3:  # 3 or more failed attempts
                    # Check if from different IPs (potential brute force)
                    ips = set(attempt.get('ip_address') for attempt in attempts if attempt.get('ip_address'))
                    
                    severity = 'high' if len(ips) > 1 else 'medium'
                    
                    security_events.append({
                        'type': 'multiple_failed_logins',
                        'severity': severity,
                        'timestamp': attempts[0]['timestamp'],
                        'username': username,
                        'details': {
                            'failed_attempts': len(attempts),
                            'unique_ips': len(ips),
                            'ips': list(ips)
                        }
                    })
            
            # Sort by severity and timestamp
            severity_order = {'high': 0, 'medium': 1, 'low': 2}
            security_events.sort(key=lambda x: (severity_order.get(x['severity'], 3), x['timestamp']), reverse=True)
            
            return security_events
            
        except Exception as e:
            self.logger.error(f"Failed to generate security alerts: {e}")
            return []

# Global audit logger instance
audit_logger = AuditLogger()

# Convenience functions for common audit events
def log_login_success(username: str, ip_address: str = None, user_agent: str = None):
    audit_logger.log_event(AuditEventType.LOGIN_SUCCESS, username, ip_address, user_agent)

def log_login_failed(username: str, ip_address: str = None, user_agent: str = None, reason: str = None):
    audit_logger.log_event(AuditEventType.LOGIN_FAILED, username, ip_address, user_agent, 
                          success=False, error_message=reason)

def log_logout(username: str, ip_address: str = None):
    audit_logger.log_event(AuditEventType.LOGOUT, username, ip_address)

def log_user_created(admin_username: str, new_username: str, role: str, ip_address: str = None):
    audit_logger.log_event(AuditEventType.USER_CREATED, admin_username, ip_address,
                          details={'new_user': new_username, 'role': role})

def log_user_updated(admin_username: str, target_username: str, changes: Dict, ip_address: str = None):
    audit_logger.log_event(AuditEventType.USER_UPDATED, admin_username, ip_address,
                          details={'target_user': target_username, 'changes': changes})

def log_user_deleted(admin_username: str, deleted_username: str, ip_address: str = None):
    audit_logger.log_event(AuditEventType.USER_DELETED, admin_username, ip_address,
                          details={'deleted_user': deleted_username})

def log_alert_action(username: str, alert_id: int, action: str, ip_address: str = None):
    event_type = AuditEventType.ALERT_FLAGGED if action == 'flag' else AuditEventType.ALERT_DISMISSED
    audit_logger.log_event(event_type, username, ip_address,
                          details={'alert_id': alert_id})

def log_threshold_change(username: str, old_threshold: float, new_threshold: float, ip_address: str = None):
    audit_logger.log_event(AuditEventType.THRESHOLD_CHANGED, username, ip_address,
                          details={'old_threshold': old_threshold, 'new_threshold': new_threshold})

def log_monitoring_control(username: str, action: str, ip_address: str = None):
    event_type = AuditEventType.MONITORING_STARTED if action == 'start' else AuditEventType.MONITORING_STOPPED
    audit_logger.log_event(event_type, username, ip_address)

def log_unauthorized_access(username: str, resource: str, ip_address: str = None):
    audit_logger.log_event(AuditEventType.UNAUTHORIZED_ACCESS, username, ip_address,
                          details={'resource': resource}, success=False)
