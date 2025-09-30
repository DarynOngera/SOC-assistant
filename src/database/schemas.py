#!/usr/bin/env python3
"""
MongoDB Schemas and Data Models
Defines data structures and validation schemas for all collections
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import uuid

class UserRole(Enum):
    """User role enumeration"""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"

class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class AlertStatus(Enum):
    """Alert status enumeration"""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    DISMISSED = "dismissed"

class AuditEventType(Enum):
    """Audit event types"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    ALERT_CREATED = "alert_created"
    ALERT_UPDATED = "alert_updated"
    THRESHOLD_CHANGED = "threshold_changed"
    MONITORING_STARTED = "monitoring_started"
    MONITORING_STOPPED = "monitoring_stopped"
    CSV_UPLOADED = "csv_uploaded"
    REPORT_GENERATED = "report_generated"
    UNAUTHORIZED_ACCESS = "unauthorized_access"

class MongoSchemas:
    """MongoDB collection schemas and validation"""
    
    @staticmethod
    def user_schema() -> Dict[str, Any]:
        """User collection schema"""
        return {
            "_id": str,  # MongoDB ObjectId as string
            "username": str,
            "password_hash": str,
            "email": str,
            "role": str,  # UserRole enum value
            "active": bool,
            "mfa_enabled": bool,
            "mfa_secret": Optional[str],
            "created_at": datetime,
            "updated_at": datetime,
            "last_login": Optional[datetime],
            "failed_attempts": int,
            "locked_until": Optional[datetime],
            "email_verified": bool,
            "default_auth_method": str,  # "password", "email_otp", or "passkey"
            "email_otp_enabled": bool,
            "passkey_enabled": bool,
            "profile": {
                "first_name": Optional[str],
                "last_name": Optional[str],
                "department": Optional[str],
                "phone": Optional[str]
            },
            "preferences": {
                "theme": str,  # "light" or "dark"
                "notifications": bool,
                "email_alerts": bool,
                "dashboard_layout": Dict[str, Any]
            }
        }
    
    @staticmethod
    def alert_schema() -> Dict[str, Any]:
        """Alert collection schema"""
        return {
            "_id": str,  # MongoDB ObjectId as string
            "alert_id": int,  # Sequential alert ID for UI
            "timestamp": datetime,
            "severity": str,  # AlertSeverity enum value
            "status": str,  # AlertStatus enum value
            "source_ip": str,
            "destination_ip": str,
            "source_port": int,
            "destination_port": int,
            "protocol": str,
            "attack_type": str,
            "anomaly_score": float,
            "confidence": float,
            "flagged": bool,
            "dismissed": bool,
            "assigned_to": Optional[str],  # Username
            "created_by": str,  # System or username
            "updated_by": Optional[str],
            "updated_at": Optional[datetime],
            "resolution_notes": Optional[str],
            "tags": List[str],
            "network_data": {
                "duration": Optional[float],
                "bytes_sent": Optional[int],
                "bytes_received": Optional[int],
                "packets_sent": Optional[int],
                "packets_received": Optional[int],
                "connection_state": Optional[str]
            },
            "ml_metadata": {
                "model_version": str,
                "feature_vector": Optional[List[float]],
                "prediction_confidence": float,
                "false_positive_probability": Optional[float]
            },
            "investigation": {
                "started_at": Optional[datetime],
                "completed_at": Optional[datetime],
                "investigator": Optional[str],
                "findings": Optional[str],
                "actions_taken": List[str]
            }
        }
    
    @staticmethod
    def audit_log_schema() -> Dict[str, Any]:
        """Audit log collection schema"""
        return {
            "_id": str,  # MongoDB ObjectId as string
            "timestamp": datetime,
            "event_type": str,  # AuditEventType enum value
            "username": Optional[str],
            "ip_address": str,
            "user_agent": Optional[str],
            "resource": Optional[str],
            "action": str,
            "details": Dict[str, Any],
            "success": bool,
            "error_message": Optional[str],
            "session_id": Optional[str],
            "request_id": Optional[str],
            "duration_ms": Optional[float]
        }
    
    @staticmethod
    def system_stats_schema() -> Dict[str, Any]:
        """System statistics collection schema"""
        return {
            "_id": str,  # MongoDB ObjectId as string
            "timestamp": datetime,
            "metric_type": str,  # "realtime", "hourly", "daily"
            "total_processed": int,
            "anomalies_detected": int,
            "total_alerts": int,
            "active_alerts": int,
            "system_health": str,
            "detection_threshold": float,
            "severity_distribution": {
                "critical": int,
                "high": int,
                "medium": int,
                "low": int
            },
            "detection_rate": float,
            "false_positive_rate": Optional[float],
            "system_resources": {
                "cpu_usage": Optional[float],
                "memory_usage": Optional[float],
                "disk_usage": Optional[float],
                "network_io": Optional[Dict[str, float]]
            },
            "model_performance": {
                "accuracy": Optional[float],
                "precision": Optional[float],
                "recall": Optional[float],
                "f1_score": Optional[float]
            }
        }
    
    @staticmethod
    def csv_upload_schema() -> Dict[str, Any]:
        """CSV upload tracking schema"""
        return {
            "_id": str,  # MongoDB ObjectId as string
            "upload_id": str,  # UUID
            "filename": str,
            "original_filename": str,
            "file_size": int,
            "file_path": str,
            "uploaded_by": str,  # Username
            "upload_timestamp": datetime,
            "status": str,  # "processing", "completed", "failed"
            "processing_started_at": Optional[datetime],
            "processing_completed_at": Optional[datetime],
            "total_records": Optional[int],
            "processed_records": Optional[int],
            "anomalies_found": Optional[int],
            "error_message": Optional[str],
            "metadata": {
                "columns": List[str],
                "data_types": Dict[str, str],
                "missing_values": Dict[str, int],
                "summary_stats": Optional[Dict[str, Any]]
            },
            "results": {
                "report_path": Optional[str],
                "visualization_paths": List[str],
                "model_metrics": Optional[Dict[str, float]]
            }
        }
    
    @staticmethod
    def model_metadata_schema() -> Dict[str, Any]:
        """ML model metadata schema"""
        return {
            "_id": str,  # MongoDB ObjectId as string
            "model_id": str,  # UUID
            "model_name": str,
            "model_type": str,  # "lstm_autoencoder", "random_forest", etc.
            "version": str,
            "created_at": datetime,
            "created_by": str,
            "status": str,  # "training", "active", "deprecated"
            "file_path": str,
            "config_path": Optional[str],
            "training_data": {
                "dataset_name": str,
                "training_samples": int,
                "validation_samples": int,
                "test_samples": int,
                "features": List[str],
                "target_variable": Optional[str]
            },
            "performance_metrics": {
                "accuracy": Optional[float],
                "precision": Optional[float],
                "recall": Optional[float],
                "f1_score": Optional[float],
                "auc_roc": Optional[float],
                "confusion_matrix": Optional[List[List[int]]]
            },
            "hyperparameters": Dict[str, Any],
            "training_duration": Optional[float],
            "deployment_info": {
                "deployed_at": Optional[datetime],
                "deployment_environment": Optional[str],
                "api_endpoint": Optional[str]
            }
        }
    
    @staticmethod
    def session_schema() -> Dict[str, Any]:
        """User session tracking schema"""
        return {
            "_id": str,  # MongoDB ObjectId as string
            "session_id": str,  # UUID
            "username": str,
            "created_at": datetime,
            "last_activity": datetime,
            "expires_at": datetime,
            "ip_address": str,
            "user_agent": str,
            "active": bool,
            "refresh_token": Optional[str],
            "access_token_hash": Optional[str]
        }

class DocumentBuilder:
    """Helper class to build MongoDB documents"""
    
    @staticmethod
    def build_user_document(username: str, password_hash: str, email: str, 
                          role: str, **kwargs) -> Dict[str, Any]:
        """Build user document"""
        now = datetime.utcnow()
        return {
            "username": username,
            "password_hash": password_hash,
            "email": email,
            "role": role,
            "active": kwargs.get("active", True),
            "mfa_enabled": kwargs.get("mfa_enabled", False),
            "mfa_secret": kwargs.get("mfa_secret"),
            "created_at": now,
            "updated_at": now,
            "last_login": None,
            "failed_attempts": 0,
            "locked_until": None,
            "profile": {
                "first_name": kwargs.get("first_name"),
                "last_name": kwargs.get("last_name"),
                "department": kwargs.get("department"),
                "phone": kwargs.get("phone")
            },
            "preferences": {
                "theme": kwargs.get("theme", "light"),
                "notifications": kwargs.get("notifications", True),
                "email_alerts": kwargs.get("email_alerts", True),
                "dashboard_layout": kwargs.get("dashboard_layout", {})
            }
        }
    
    @staticmethod
    def build_alert_document(alert_id: int, timestamp: datetime, severity: str,
                           source_ip: str, destination_ip: str, attack_type: str,
                           anomaly_score: float, **kwargs) -> Dict[str, Any]:
        """Build alert document"""
        return {
            "alert_id": alert_id,
            "timestamp": timestamp,
            "severity": severity,
            "status": kwargs.get("status", AlertStatus.NEW.value),
            "source_ip": source_ip,
            "destination_ip": destination_ip,
            "source_port": kwargs.get("source_port", 0),
            "destination_port": kwargs.get("destination_port", 0),
            "protocol": kwargs.get("protocol", "tcp"),
            "attack_type": attack_type,
            "anomaly_score": anomaly_score,
            "confidence": kwargs.get("confidence", 0.5),
            "flagged": kwargs.get("flagged", False),
            "dismissed": kwargs.get("dismissed", False),
            "assigned_to": kwargs.get("assigned_to"),
            "created_by": kwargs.get("created_by", "system"),
            "updated_by": None,
            "updated_at": None,
            "resolution_notes": None,
            "tags": kwargs.get("tags", []),
            "network_data": {
                "duration": kwargs.get("duration"),
                "bytes_sent": kwargs.get("bytes_sent"),
                "bytes_received": kwargs.get("bytes_received"),
                "packets_sent": kwargs.get("packets_sent"),
                "packets_received": kwargs.get("packets_received"),
                "connection_state": kwargs.get("connection_state")
            },
            "ml_metadata": {
                "model_version": kwargs.get("model_version", "1.0"),
                "feature_vector": kwargs.get("feature_vector"),
                "prediction_confidence": kwargs.get("prediction_confidence", anomaly_score),
                "false_positive_probability": kwargs.get("false_positive_probability")
            },
            "investigation": {
                "started_at": None,
                "completed_at": None,
                "investigator": None,
                "findings": None,
                "actions_taken": []
            }
        }
    
    @staticmethod
    def build_audit_log_document(event_type: str, username: str, ip_address: str,
                               action: str, success: bool, **kwargs) -> Dict[str, Any]:
        """Build audit log document"""
        return {
            "timestamp": datetime.utcnow(),
            "event_type": event_type,
            "username": username,
            "ip_address": ip_address,
            "user_agent": kwargs.get("user_agent"),
            "resource": kwargs.get("resource"),
            "action": action,
            "details": kwargs.get("details", {}),
            "success": success,
            "error_message": kwargs.get("error_message"),
            "session_id": kwargs.get("session_id"),
            "request_id": kwargs.get("request_id"),
            "duration_ms": kwargs.get("duration_ms")
        }
    
    @staticmethod
    def build_system_stats_document(metric_type: str, total_processed: int,
                                  anomalies_detected: int, **kwargs) -> Dict[str, Any]:
        """Build system stats document"""
        return {
            "timestamp": datetime.utcnow(),
            "metric_type": metric_type,
            "total_processed": total_processed,
            "anomalies_detected": anomalies_detected,
            "total_alerts": kwargs.get("total_alerts", 0),
            "active_alerts": kwargs.get("active_alerts", 0),
            "system_health": kwargs.get("system_health", "healthy"),
            "detection_threshold": kwargs.get("detection_threshold", 0.5),
            "severity_distribution": kwargs.get("severity_distribution", {
                "critical": 0, "high": 0, "medium": 0, "low": 0
            }),
            "detection_rate": kwargs.get("detection_rate", 0.0),
            "false_positive_rate": kwargs.get("false_positive_rate"),
            "system_resources": kwargs.get("system_resources", {}),
            "model_performance": kwargs.get("model_performance", {})
        }

# Collection names
COLLECTIONS = {
    "users": "users",
    "alerts": "alerts",
    "audit_logs": "audit_logs",
    "system_stats": "system_stats",
    "csv_uploads": "csv_uploads",
    "model_metadata": "model_metadata",
    "sessions": "sessions"
}

# Validation functions
def validate_user_role(role: str) -> bool:
    """Validate user role"""
    return role in [r.value for r in UserRole]

def validate_alert_severity(severity: str) -> bool:
    """Validate alert severity"""
    return severity in [s.value for s in AlertSeverity]

def validate_alert_status(status: str) -> bool:
    """Validate alert status"""
    return status in [s.value for s in AlertStatus]

def validate_audit_event_type(event_type: str) -> bool:
    """Validate audit event type"""
    return event_type in [e.value for e in AuditEventType]
