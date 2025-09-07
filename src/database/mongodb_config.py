#!/usr/bin/env python3
"""
MongoDB Configuration and Connection Management
Provides centralized database configuration, connection pooling, and health monitoring
"""

import os
import logging
from typing import Optional, Dict, Any
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from motor.motor_asyncio import AsyncIOMotorClient
import threading
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBConfig:
    """MongoDB configuration and connection management"""
    
    def __init__(self):
        # MongoDB connection settings
        self.host = os.getenv('MONGODB_HOST', 'localhost')
        self.port = int(os.getenv('MONGODB_PORT', 27017))
        self.database_name = os.getenv('MONGODB_DATABASE', 'soc_assistant')
        self.username = os.getenv('MONGODB_USERNAME', '')
        self.password = os.getenv('MONGODB_PASSWORD', '')
        self.auth_source = os.getenv('MONGODB_AUTH_SOURCE', 'admin')
        
        # Connection pool settings
        self.max_pool_size = int(os.getenv('MONGODB_MAX_POOL_SIZE', 100))
        self.min_pool_size = int(os.getenv('MONGODB_MIN_POOL_SIZE', 10))
        self.max_idle_time_ms = int(os.getenv('MONGODB_MAX_IDLE_TIME_MS', 30000))
        self.server_selection_timeout_ms = int(os.getenv('MONGODB_SERVER_SELECTION_TIMEOUT_MS', 5000))
        
        # Connection instances
        self._client: Optional[MongoClient] = None
        self._async_client: Optional[AsyncIOMotorClient] = None
        self._database = None
        self._async_database = None
        self._connection_lock = threading.Lock()
        
        # Health monitoring
        self._last_health_check = None
        self._is_healthy = False
        
    def get_connection_string(self) -> str:
        """Build MongoDB connection string"""
        if self.username and self.password:
            auth_part = f"{self.username}:{self.password}@"
            auth_params = f"?authSource={self.auth_source}"
        else:
            auth_part = ""
            auth_params = ""
            
        return f"mongodb://{auth_part}{self.host}:{self.port}/{self.database_name}{auth_params}"
    
    def get_client_options(self) -> Dict[str, Any]:
        """Get MongoDB client options"""
        return {
            'maxPoolSize': self.max_pool_size,
            'minPoolSize': self.min_pool_size,
            'maxIdleTimeMS': self.max_idle_time_ms,
            'serverSelectionTimeoutMS': self.server_selection_timeout_ms,
            'connectTimeoutMS': 10000,
            'socketTimeoutMS': 30000,
            'retryWrites': True,
            'retryReads': True,
            'w': 'majority',
            'readPreference': 'primary'
        }
    
    def connect(self) -> MongoClient:
        """Get or create synchronous MongoDB client"""
        with self._connection_lock:
            if self._client is None:
                try:
                    connection_string = self.get_connection_string()
                    client_options = self.get_client_options()
                    
                    self._client = MongoClient(connection_string, **client_options)
                    
                    # Test connection
                    self._client.admin.command('ping')
                    self._database = self._client[self.database_name]
                    
                    logger.info(f"Connected to MongoDB: {self.host}:{self.port}/{self.database_name}")
                    self._is_healthy = True
                    self._last_health_check = datetime.now()
                    
                except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                    logger.error(f"Failed to connect to MongoDB: {e}")
                    self._is_healthy = False
                    raise
                    
            return self._client
    
    def get_async_client(self) -> AsyncIOMotorClient:
        """Get or create asynchronous MongoDB client"""
        with self._connection_lock:
            if self._async_client is None:
                try:
                    connection_string = self.get_connection_string()
                    client_options = self.get_client_options()
                    
                    self._async_client = AsyncIOMotorClient(connection_string, **client_options)
                    self._async_database = self._async_client[self.database_name]
                    
                    logger.info(f"Created async MongoDB client: {self.host}:{self.port}/{self.database_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to create async MongoDB client: {e}")
                    raise
                    
            return self._async_client
    
    def get_database(self):
        """Get synchronous database instance"""
        if self._database is None:
            self.connect()
        return self._database
    
    def get_async_database(self):
        """Get asynchronous database instance"""
        if self._async_database is None:
            self.get_async_client()
        return self._async_database
    
    def health_check(self) -> Dict[str, Any]:
        """Perform MongoDB health check"""
        try:
            client = self.connect()
            
            # Ping the database
            start_time = time.time()
            result = client.admin.command('ping')
            ping_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Get server status
            server_status = client.admin.command('serverStatus')
            
            # Get database stats
            db_stats = self._database.command('dbStats')
            
            self._is_healthy = True
            self._last_health_check = datetime.now()
            
            return {
                'status': 'healthy',
                'ping_time_ms': round(ping_time, 2),
                'server_version': server_status.get('version'),
                'uptime_seconds': server_status.get('uptime'),
                'connections': server_status.get('connections', {}),
                'database_size_mb': round(db_stats.get('dataSize', 0) / (1024 * 1024), 2),
                'collections': db_stats.get('collections', 0),
                'indexes': db_stats.get('indexes', 0),
                'last_check': self._last_health_check.isoformat()
            }
            
        except Exception as e:
            self._is_healthy = False
            logger.error(f"MongoDB health check failed: {e}")
            
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    def is_healthy(self) -> bool:
        """Check if MongoDB connection is healthy"""
        # Perform health check if it's been more than 30 seconds
        if (self._last_health_check is None or 
            (datetime.now() - self._last_health_check).seconds > 30):
            self.health_check()
        
        return self._is_healthy
    
    def close_connections(self):
        """Close all MongoDB connections"""
        with self._connection_lock:
            if self._client:
                self._client.close()
                self._client = None
                self._database = None
                logger.info("Closed synchronous MongoDB connection")
                
            if self._async_client:
                self._async_client.close()
                self._async_client = None
                self._async_database = None
                logger.info("Closed asynchronous MongoDB connection")
    
    def create_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            db = self.get_database()
            
            # Users collection indexes
            users_collection = db.users
            users_collection.create_index("username", unique=True)
            users_collection.create_index("email", unique=True)
            users_collection.create_index("role")
            users_collection.create_index("active")
            users_collection.create_index("created_at")
            
            # Alerts collection indexes
            alerts_collection = db.alerts
            alerts_collection.create_index("timestamp")
            alerts_collection.create_index("severity")
            alerts_collection.create_index("status")
            alerts_collection.create_index("source_ip")
            alerts_collection.create_index("destination_ip")
            alerts_collection.create_index("attack_type")
            alerts_collection.create_index("anomaly_score")
            alerts_collection.create_index([("timestamp", -1), ("severity", 1)])  # Compound index
            
            # Audit logs collection indexes
            audit_collection = db.audit_logs
            audit_collection.create_index("timestamp")
            audit_collection.create_index("event_type")
            audit_collection.create_index("username")
            audit_collection.create_index("ip_address")
            audit_collection.create_index([("timestamp", -1), ("event_type", 1)])  # Compound index
            
            # System stats collection indexes
            stats_collection = db.system_stats
            stats_collection.create_index("timestamp")
            stats_collection.create_index("metric_type")
            
            # CSV uploads collection indexes
            uploads_collection = db.csv_uploads
            uploads_collection.create_index("upload_id", unique=True)
            uploads_collection.create_index("uploaded_by")
            uploads_collection.create_index("upload_timestamp")
            uploads_collection.create_index("status")
            
            logger.info("Successfully created MongoDB indexes")
            
        except Exception as e:
            logger.error(f"Failed to create MongoDB indexes: {e}")
            raise

# Global MongoDB configuration instance
mongodb_config = MongoDBConfig()

def get_mongodb_client() -> MongoClient:
    """Get MongoDB client instance"""
    return mongodb_config.connect()

def get_mongodb_database():
    """Get MongoDB database instance"""
    return mongodb_config.get_database()

def get_async_mongodb_client() -> AsyncIOMotorClient:
    """Get async MongoDB client instance"""
    return mongodb_config.get_async_client()

def get_async_mongodb_database():
    """Get async MongoDB database instance"""
    return mongodb_config.get_async_database()

def mongodb_health_check() -> Dict[str, Any]:
    """Perform MongoDB health check"""
    return mongodb_config.health_check()

def is_mongodb_healthy() -> bool:
    """Check if MongoDB is healthy"""
    return mongodb_config.is_healthy()

def close_mongodb_connections():
    """Close all MongoDB connections"""
    mongodb_config.close_connections()

def initialize_mongodb():
    """Initialize MongoDB connection and create indexes"""
    try:
        # Test connection
        mongodb_config.connect()
        
        # Create indexes
        mongodb_config.create_indexes()
        
        logger.info("MongoDB initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"MongoDB initialization failed: {e}")
        return False
