"""
Production Monitoring Infrastructure
Provides Prometheus metrics, health checks, and system monitoring
"""

import psutil
import time
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class SOCMetrics:
    """
    Centralized metrics collection for SOC Assistant
    Exposes Prometheus-compatible metrics
    """
    
    def __init__(self, app_name="soc_assistant"):
        # Application Info
        self.app_info = Info('soc_application', 'SOC Assistant Application Info')
        self.app_info.info({
            'version': '1.0.0',
            'environment': 'production',
            'name': app_name
        })
        
        # HTTP Metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request latency',
            ['method', 'endpoint']
        )
        
        # Alert Metrics
        self.alerts_generated = Counter(
            'alerts_generated_total',
            'Total alerts generated',
            ['severity', 'attack_type']
        )
        
        self.alerts_active = Gauge(
            'alerts_active',
            'Currently active alerts',
            ['severity']
        )
        
        # ML Model Metrics
        self.ml_predictions = Counter(
            'ml_predictions_total',
            'Total ML predictions',
            ['model_type', 'prediction']
        )
        
        self.ml_prediction_latency = Histogram(
            'ml_prediction_latency_seconds',
            'ML prediction latency',
            ['model_type']
        )
        
        self.ml_model_accuracy = Gauge(
            'ml_model_accuracy',
            'ML model accuracy',
            ['model_type']
        )
        
        # NLP Metrics
        self.nlp_analyses = Counter(
            'nlp_analyses_total',
            'Total NLP analyses performed'
        )
        
        self.nlp_confidence = Histogram(
            'nlp_confidence_score',
            'NLP confidence scores'
        )
        
        # Database Metrics
        self.db_operations = Counter(
            'db_operations_total',
            'Total database operations',
            ['operation', 'collection', 'status']
        )
        
        self.db_operation_duration = Histogram(
            'db_operation_duration_seconds',
            'Database operation latency',
            ['operation', 'collection']
        )
        
        self.db_connections = Gauge(
            'db_connections_active',
            'Active database connections'
        )
        
        # WebSocket Metrics
        self.websocket_connections = Gauge(
            'websocket_connections_active',
            'Active WebSocket connections'
        )
        
        self.websocket_messages = Counter(
            'websocket_messages_total',
            'Total WebSocket messages',
            ['event_type', 'direction']
        )
        
        # System Metrics
        self.cpu_usage = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
        self.memory_usage = Gauge('system_memory_usage_percent', 'Memory usage percentage')
        self.disk_usage = Gauge('system_disk_usage_percent', 'Disk usage percentage')
        
        # Authentication Metrics
        self.auth_attempts = Counter(
            'auth_attempts_total',
            'Authentication attempts',
            ['status', 'method']
        )
        
        self.active_sessions = Gauge(
            'active_sessions',
            'Currently active user sessions'
        )
        
        logger.info("✅ Prometheus metrics initialized")
    
    def track_http_request(self, method, endpoint, status_code, duration):
        """Track HTTP request metrics"""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status_code
        ).inc()
        
        self.http_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def track_alert(self, severity, attack_type):
        """Track alert generation"""
        self.alerts_generated.labels(
            severity=severity,
            attack_type=attack_type
        ).inc()
    
    def update_active_alerts(self, severity, count):
        """Update active alerts gauge"""
        self.alerts_active.labels(severity=severity).set(count)
    
    def track_ml_prediction(self, model_type, prediction, latency):
        """Track ML prediction metrics"""
        self.ml_predictions.labels(
            model_type=model_type,
            prediction=prediction
        ).inc()
        
        self.ml_prediction_latency.labels(
            model_type=model_type
        ).observe(latency)
    
    def update_model_accuracy(self, model_type, accuracy):
        """Update ML model accuracy"""
        self.ml_model_accuracy.labels(model_type=model_type).set(accuracy)
    
    def track_nlp_analysis(self, confidence):
        """Track NLP analysis"""
        self.nlp_analyses.inc()
        self.nlp_confidence.observe(confidence)
    
    def track_db_operation(self, operation, collection, status, duration):
        """Track database operation"""
        self.db_operations.labels(
            operation=operation,
            collection=collection,
            status=status
        ).inc()
        
        self.db_operation_duration.labels(
            operation=operation,
            collection=collection
        ).observe(duration)
    
    def update_db_connections(self, count):
        """Update active database connections"""
        self.db_connections.set(count)
    
    def update_websocket_connections(self, count):
        """Update active WebSocket connections"""
        self.websocket_connections.set(count)
    
    def track_websocket_message(self, event_type, direction):
        """Track WebSocket message"""
        self.websocket_messages.labels(
            event_type=event_type,
            direction=direction
        ).inc()
    
    def track_auth_attempt(self, status, method='password'):
        """Track authentication attempt"""
        self.auth_attempts.labels(status=status, method=method).inc()
    
    def update_active_sessions(self, count):
        """Update active sessions"""
        self.active_sessions.set(count)
    
    def update_system_metrics(self):
        """Update system resource metrics"""
        try:
            self.cpu_usage.set(psutil.cpu_percent(interval=1))
            self.memory_usage.set(psutil.virtual_memory().percent)
            self.disk_usage.set(psutil.disk_usage('/').percent)
        except Exception as e:
            logger.warning(f"Failed to update system metrics: {e}")


class HealthCheck:
    """
    Comprehensive health check system
    """
    
    def __init__(self):
        self.checks = {}
        self.start_time = time.time()
        logger.info("✅ Health check system initialized")
    
    def register_check(self, name, check_func):
        """Register a health check function"""
        self.checks[name] = check_func
    
    def run_checks(self):
        """Run all health checks"""
        results = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': int(time.time() - self.start_time),
            'checks': {}
        }
        
        all_healthy = True
        
        for name, check_func in self.checks.items():
            try:
                check_result = check_func()
                results['checks'][name] = {
                    'status': 'healthy' if check_result else 'unhealthy',
                    'details': check_result if isinstance(check_result, dict) else {}
                }
                if not check_result:
                    all_healthy = False
            except Exception as e:
                results['checks'][name] = {
                    'status': 'error',
                    'error': str(e)
                }
                all_healthy = False
        
        results['status'] = 'healthy' if all_healthy else 'degraded'
        return results
    
    def get_readiness(self):
        """Check if application is ready to serve traffic"""
        critical_checks = ['database', 'ml_models']
        
        for check_name in critical_checks:
            if check_name in self.checks:
                try:
                    result = self.checks[check_name]()
                    if not result:
                        return False
                except:
                    return False
        
        return True
    
    def get_liveness(self):
        """Check if application is alive"""
        # Simple liveness check - if we can execute this, we're alive
        return True


def timing_decorator(metrics, model_type=None):
    """
    Decorator to track function execution time
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Track ML prediction latency
                if model_type:
                    metrics.ml_prediction_latency.labels(
                        model_type=model_type
                    ).observe(duration)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                raise e
        return wrapper
    return decorator


# Global metrics instance
_metrics_instance = None

def get_metrics():
    """Get or create global metrics instance"""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = SOCMetrics()
    return _metrics_instance


# Global health check instance
_health_instance = None

def get_health_check():
    """Get or create global health check instance"""
    global _health_instance
    if _health_instance is None:
        _health_instance = HealthCheck()
    return _health_instance
