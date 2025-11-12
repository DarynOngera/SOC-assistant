#!/usr/bin/env python3
"""
MongoDB Data Access Layer (DAL)
Provides CRUD operations and business logic for all MongoDB collections
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, PyMongoError
from bson import ObjectId
import uuid

from .mongodb_config import get_mongodb_database
from .schemas import (
    COLLECTIONS, DocumentBuilder, UserRole, AlertSeverity, AlertStatus, 
    AuditEventType, validate_user_role, validate_alert_severity, 
    validate_alert_status, validate_audit_event_type
)

logger = logging.getLogger(__name__)

class MongoDBDAL:
    """MongoDB Data Access Layer"""
    
    def __init__(self):
        self.db = get_mongodb_database()
        
    # User Management Operations
    def create_user(self, username: str, password_hash: str, email: str, 
                   role: str, **kwargs) -> Tuple[bool, str, Optional[str]]:
        """Create a new user"""
        try:
            if not validate_user_role(role):
                return False, "Invalid user role", None
                
            user_doc = DocumentBuilder.build_user_document(
                username, password_hash, email, role, **kwargs
            )
            
            result = self.db[COLLECTIONS["users"]].insert_one(user_doc)
            logger.info(f"Created user: {username}")
            return True, "User created successfully", str(result.inserted_id)
            
        except DuplicateKeyError:
            return False, "Username or email already exists", None
        except Exception as e:
            logger.error(f"Error creating user {username}: {e}")
            return False, f"Failed to create user: {str(e)}", None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            return self.db[COLLECTIONS["users"]].find_one({"username": username})
        except Exception as e:
            logger.error(f"Error getting user {username}: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            return self.db[COLLECTIONS["users"]].find_one({"email": email})
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    def update_user(self, username: str, updates: Dict[str, Any]) -> Tuple[bool, str]:
        """Update user information"""
        try:
            # Add updated_at timestamp
            updates["updated_at"] = datetime.utcnow()
            
            result = self.db[COLLECTIONS["users"]].update_one(
                {"username": username},
                {"$set": updates}
            )
            
            if result.matched_count == 0:
                return False, "User not found"
            
            logger.info(f"Updated user: {username}")
            return True, "User updated successfully"
            
        except Exception as e:
            logger.error(f"Error updating user {username}: {e}")
            return False, f"Failed to update user: {str(e)}"
    
    def delete_user(self, username: str) -> Tuple[bool, str]:
        """Delete user"""
        try:
            result = self.db[COLLECTIONS["users"]].delete_one({"username": username})
            
            if result.deleted_count == 0:
                return False, "User not found"
            
            logger.info(f"Deleted user: {username}")
            return True, "User deleted successfully"
            
        except Exception as e:
            logger.error(f"Error deleting user {username}: {e}")
            return False, f"Failed to delete user: {str(e)}"
    
    def get_all_users(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """Get all users"""
        try:
            query = {"active": True} if active_only else {}
            users = list(self.db[COLLECTIONS["users"]].find(
                query, 
                {"password_hash": 0, "mfa_secret": 0}  # Exclude sensitive fields
            ))
            return users
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []
    
    def authenticate_user(self, username: str, password_hash: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Authenticate user and update last login"""
        try:
            user = self.get_user_by_username(username)
            if not user or not user.get("active", True):
                return False, None
            
            if user["password_hash"] == password_hash:
                # Update last login
                self.update_user(username, {"last_login": datetime.utcnow()})
                return True, user
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error authenticating user {username}: {e}")
            return False, None
    
    # Alert Management Operations
    def create_alert(self, alert_data: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        """Create a new alert"""
        try:
            # Generate sequential alert ID
            last_alert = self.db[COLLECTIONS["alerts"]].find_one(
                {}, sort=[("alert_id", DESCENDING)]
            )
            # Ensure alert_id is an integer
            if last_alert and "alert_id" in last_alert:
                try:
                    # Try to convert to int
                    last_id = int(last_alert["alert_id"]) if isinstance(last_alert["alert_id"], str) else last_alert["alert_id"]
                    next_id = last_id + 1
                except (ValueError, TypeError):
                    # If it's a UUID or non-numeric, find the highest numeric ID
                    numeric_alerts = list(self.db[COLLECTIONS["alerts"]].find(
                        {"alert_id": {"$type": ["int", "long"]}},
                        sort=[("alert_id", DESCENDING)],
                        limit=1
                    ))
                    if numeric_alerts:
                        next_id = int(numeric_alerts[0]["alert_id"]) + 1
                    else:
                        next_id = 1
            else:
                next_id = 1
            
            alert_doc = DocumentBuilder.build_alert_document(
                alert_id=next_id,
                **alert_data
            )
            
            result = self.db[COLLECTIONS["alerts"]].insert_one(alert_doc)
            logger.info(f"Created alert: {next_id}")
            return True, "Alert created successfully", str(result.inserted_id)
            
        except Exception as e:
            # Only log if it's not a duplicate key or type conversion issue
            if "alert_id" not in str(e).lower():
                logger.error(f"Error creating alert: {e}")
            return False, f"Failed to create alert: {str(e)}", None
    
    def get_alert_by_id(self, alert_id: int) -> Optional[Dict[str, Any]]:
        """Get alert by ID"""
        try:
            return self.db[COLLECTIONS["alerts"]].find_one({"alert_id": alert_id})
        except Exception as e:
            logger.error(f"Error getting alert {alert_id}: {e}")
            return None
    
    def get_alerts(self, filters: Dict[str, Any] = None, page: int = 1, 
                  per_page: int = 20, sort_by: str = "timestamp", 
                  sort_order: int = DESCENDING) -> Dict[str, Any]:
        """Get alerts with filtering and pagination"""
        try:
            query = filters or {}
            
            # Calculate skip value for pagination
            skip = (page - 1) * per_page
            
            # Get total count
            total = self.db[COLLECTIONS["alerts"]].count_documents(query)
            
            # Get alerts
            alerts = list(self.db[COLLECTIONS["alerts"]].find(query)
                         .sort(sort_by, sort_order)
                         .skip(skip)
                         .limit(per_page))
            
            return {
                "alerts": alerts,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
            
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return {"alerts": [], "total": 0, "page": page, "per_page": per_page, "total_pages": 0}
    
    def update_alert(self, alert_id, updates: Dict[str, Any], 
                    updated_by: str = None) -> Tuple[bool, str]:
        """Update alert - handles both integer alert_id and ObjectId formats"""
        try:
            updates["updated_at"] = datetime.utcnow()
            if updated_by:
                updates["updated_by"] = updated_by
            
            # Handle both integer alert_id and ObjectId formats
            if isinstance(alert_id, str) and len(alert_id) == 24:
                # Looks like ObjectId string
                try:
                    query = {"_id": ObjectId(alert_id)}
                    print(f"DEBUG: Using ObjectId query: {query}")
                except Exception:
                    # Fallback to string search
                    query = {"alert_id": alert_id}
                    print(f"DEBUG: Using string alert_id query: {query}")
            else:
                # Integer alert_id (backward compatibility)
                query = {"alert_id": alert_id}
                print(f"DEBUG: Using integer alert_id query: {query}")
            
            result = self.db[COLLECTIONS["alerts"]].update_one(
                query,
                {"$set": updates}
            )
            
            if result.matched_count == 0:
                return False, "Alert not found"
            
            logger.info(f"Updated alert: {alert_id}")
            return True, "Alert updated successfully"
            
        except Exception as e:
            logger.error(f"Error updating alert {alert_id}: {e}")
            return False, f"Failed to update alert: {str(e)}"
    
    def delete_alert(self, alert_id: int) -> Tuple[bool, str]:
        """Delete alert"""
        try:
            result = self.db[COLLECTIONS["alerts"]].delete_one({"alert_id": alert_id})
            
            if result.deleted_count == 0:
                return False, "Alert not found"
            
            logger.info(f"Deleted alert: {alert_id}")
            return True, "Alert deleted successfully"
            
        except Exception as e:
            logger.error(f"Error deleting alert {alert_id}: {e}")
            return False, f"Failed to delete alert: {str(e)}"
    
    def get_alert_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert statistics for the specified time period"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            pipeline = [
                {"$match": {"timestamp": {"$gte": start_time}}},
                {"$group": {
                    "_id": "$severity",
                    "count": {"$sum": 1}
                }}
            ]
            
            severity_counts = {item["_id"]: item["count"] 
                             for item in self.db[COLLECTIONS["alerts"]].aggregate(pipeline)}
            
            # Get status distribution
            status_pipeline = [
                {"$match": {"timestamp": {"$gte": start_time}}},
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }}
            ]
            
            status_counts = {item["_id"]: item["count"] 
                           for item in self.db[COLLECTIONS["alerts"]].aggregate(status_pipeline)}
            
            total_alerts = sum(severity_counts.values())
            
            return {
                "total_alerts": total_alerts,
                "severity_distribution": severity_counts,
                "status_distribution": status_counts,
                "time_period_hours": hours
            }
            
        except Exception as e:
            logger.error(f"Error getting alert statistics: {e}")
            return {}
    
    # Audit Log Operations
    def create_audit_log(self, event_type: str, username: str, ip_address: str,
                        action: str, success: bool, **kwargs) -> Tuple[bool, str]:
        """Create audit log entry"""
        try:
            if not validate_audit_event_type(event_type):
                return False, "Invalid audit event type"
            
            audit_doc = DocumentBuilder.build_audit_log_document(
                event_type, username, ip_address, action, success, **kwargs
            )
            
            self.db[COLLECTIONS["audit_logs"]].insert_one(audit_doc)
            return True, "Audit log created successfully"
            
        except Exception as e:
            logger.error(f"Error creating audit log: {e}")
            return False, f"Failed to create audit log: {str(e)}"
    
    def get_audit_logs(self, filters: Dict[str, Any] = None, page: int = 1,
                      per_page: int = 50, start_date: str = None, 
                      end_date: str = None) -> Dict[str, Any]:
        """Get audit logs with filtering and pagination"""
        try:
            query = filters or {}
            
            # Add date range filter
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = datetime.fromisoformat(start_date)
                if end_date:
                    date_filter["$lte"] = datetime.fromisoformat(end_date)
                query["timestamp"] = date_filter
            
            skip = (page - 1) * per_page
            total = self.db[COLLECTIONS["audit_logs"]].count_documents(query)
            
            logs = list(self.db[COLLECTIONS["audit_logs"]].find(query)
                       .sort("timestamp", DESCENDING)
                       .skip(skip)
                       .limit(per_page))
            
            return {
                "logs": logs,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
            
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            return {"logs": [], "total": 0, "page": page, "per_page": per_page, "total_pages": 0}
    
    def get_security_events(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get security-related events from audit logs"""
        try:
            start_time = datetime.utcnow() - timedelta(days=days)
            
            security_events = [
                AuditEventType.LOGIN_FAILED.value,
                AuditEventType.UNAUTHORIZED_ACCESS.value
            ]
            
            return list(self.db[COLLECTIONS["audit_logs"]].find({
                "timestamp": {"$gte": start_time},
                "event_type": {"$in": security_events}
            }).sort("timestamp", DESCENDING))
            
        except Exception as e:
            logger.error(f"Error getting security events: {e}")
            return []
    
    # System Statistics Operations
    def save_system_stats(self, metric_type: str, stats_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Save system statistics"""
        try:
            stats_doc = DocumentBuilder.build_system_stats_document(
                metric_type=metric_type,
                **stats_data
            )
            
            self.db[COLLECTIONS["system_stats"]].insert_one(stats_doc)
            return True, "System stats saved successfully"
            
        except Exception as e:
            logger.error(f"Error saving system stats: {e}")
            return False, f"Failed to save system stats: {str(e)}"
    
    def get_latest_system_stats(self, metric_type: str = "realtime") -> Optional[Dict[str, Any]]:
        """Get latest system statistics"""
        try:
            return self.db[COLLECTIONS["system_stats"]].find_one(
                {"metric_type": metric_type},
                sort=[("timestamp", DESCENDING)]
            )
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return None
    
    def get_system_stats_history(self, metric_type: str = "hourly", 
                                hours: int = 24) -> List[Dict[str, Any]]:
        """Get system statistics history"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            return list(self.db[COLLECTIONS["system_stats"]].find({
                "metric_type": metric_type,
                "timestamp": {"$gte": start_time}
            }).sort("timestamp", ASCENDING))
            
        except Exception as e:
            logger.error(f"Error getting system stats history: {e}")
            return []
    
    # CSV Upload Operations
    def create_csv_upload(self, upload_data: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        """Create CSV upload record"""
        try:
            upload_doc = {
                "upload_id": str(uuid.uuid4()),
                "upload_timestamp": datetime.utcnow(),
                "status": "processing",
                **upload_data
            }
            
            result = self.db[COLLECTIONS["csv_uploads"]].insert_one(upload_doc)
            return True, "CSV upload record created", upload_doc["upload_id"]
            
        except Exception as e:
            logger.error(f"Error creating CSV upload record: {e}")
            return False, f"Failed to create upload record: {str(e)}", None
    
    def update_csv_upload(self, upload_id: str, updates: Dict[str, Any]) -> Tuple[bool, str]:
        """Update CSV upload record"""
        try:
            result = self.db[COLLECTIONS["csv_uploads"]].update_one(
                {"upload_id": upload_id},
                {"$set": updates}
            )
            
            if result.matched_count == 0:
                return False, "Upload record not found"
            
            return True, "Upload record updated successfully"
            
        except Exception as e:
            logger.error(f"Error updating CSV upload {upload_id}: {e}")
            return False, f"Failed to update upload record: {str(e)}"
    
    def get_csv_uploads(self, username: str = None, page: int = 1, 
                       per_page: int = 20) -> Dict[str, Any]:
        """Get CSV upload records"""
        try:
            query = {"uploaded_by": username} if username else {}
            
            skip = (page - 1) * per_page
            total = self.db[COLLECTIONS["csv_uploads"]].count_documents(query)
            
            uploads = list(self.db[COLLECTIONS["csv_uploads"]].find(query)
                          .sort("upload_timestamp", DESCENDING)
                          .skip(skip)
                          .limit(per_page))
            
            return {
                "uploads": uploads,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
            
        except Exception as e:
            logger.error(f"Error getting CSV uploads: {e}")
            return {"uploads": [], "total": 0, "page": page, "per_page": per_page, "total_pages": 0}
    
    # Session Management Operations
    def create_session(self, session_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Create user session"""
        try:
            session_doc = {
                "session_id": str(uuid.uuid4()),
                "created_at": datetime.utcnow(),
                "active": True,
                **session_data
            }
            
            self.db[COLLECTIONS["sessions"]].insert_one(session_doc)
            return True, session_doc["session_id"]
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False, f"Failed to create session: {str(e)}"
    
    def get_active_sessions(self, username: str = None) -> List[Dict[str, Any]]:
        """Get active sessions"""
        try:
            query = {"active": True}
            if username:
                query["username"] = username
            
            return list(self.db[COLLECTIONS["sessions"]].find(query)
                       .sort("last_activity", DESCENDING))
            
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> Tuple[bool, str]:
        """Update session"""
        try:
            result = self.db[COLLECTIONS["sessions"]].update_one(
                {"session_id": session_id},
                {"$set": updates}
            )
            
            if result.matched_count == 0:
                return False, "Session not found"
            
            return True, "Session updated successfully"
            
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            return False, f"Failed to update session: {str(e)}"
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        try:
            now = datetime.utcnow()
            result = self.db[COLLECTIONS["sessions"]].delete_many({
                "$or": [
                    {"expires_at": {"$lt": now}},
                    {"active": False}
                ]
            })
            
            logger.info(f"Cleaned up {result.deleted_count} expired sessions")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
            return 0
    
    # Utility Operations
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get database collection statistics"""
        try:
            stats = {}
            for collection_name in COLLECTIONS.values():
                collection = self.db[collection_name]
                stats[collection_name] = {
                    "count": collection.count_documents({}),
                    "size": self.db.command("collStats", collection_name).get("size", 0)
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 90) -> Dict[str, int]:
        """Clean up old data based on retention policy"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            cleanup_results = {}
            
            # Clean up old audit logs
            result = self.db[COLLECTIONS["audit_logs"]].delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            cleanup_results["audit_logs"] = result.deleted_count
            
            # Clean up old system stats
            result = self.db[COLLECTIONS["system_stats"]].delete_many({
                "timestamp": {"$lt": cutoff_date},
                "metric_type": "realtime"  # Keep hourly and daily stats longer
            })
            cleanup_results["system_stats"] = result.deleted_count
            
            # Clean up resolved alerts older than retention period
            result = self.db[COLLECTIONS["alerts"]].delete_many({
                "timestamp": {"$lt": cutoff_date},
                "status": {"$in": [AlertStatus.RESOLVED.value, AlertStatus.FALSE_POSITIVE.value]}
            })
            cleanup_results["alerts"] = result.deleted_count
            
            logger.info(f"Cleanup completed: {cleanup_results}")
            return cleanup_results
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {}

# Global DAL instance
mongodb_dal = MongoDBDAL()

# Convenience functions
def get_dal() -> MongoDBDAL:
    """Get MongoDB DAL instance"""
    return mongodb_dal
