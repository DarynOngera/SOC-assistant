"""
Production Logging Infrastructure
Structured JSON logging with rotation and multiple handlers
"""

import logging
import logging.handlers
import json
import os
from datetime import datetime
from pythonjsonlogger import jsonlogger
from pathlib import Path


class SOCJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter for SOC Assistant logs
    """
    
    def add_fields(self, log_record, record, message_dict):
        super(SOCJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add logger name
        log_record['logger'] = record.name
        
        # Add source location
        log_record['source'] = {
            'file': record.filename,
            'line': record.lineno,
            'function': record.funcName
        }
        
        # Add application context
        log_record['application'] = 'soc_assistant'
        log_record['environment'] = os.getenv('ENVIRONMENT', 'production')


def setup_logging(log_dir='logs', log_level=logging.INFO):
    """
    Setup comprehensive logging infrastructure
    
    Creates multiple log handlers:
    - JSON file handler (for machine parsing)
    - Text file handler (for human reading)
    - Console handler (for development)
    - Rotating handlers (to prevent disk fill)
    """
    
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # 1. JSON File Handler (Rotating)
    json_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / 'soc_assistant.json.log',
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=10,
        encoding='utf-8'
    )
    json_handler.setLevel(logging.INFO)
    json_formatter = SOCJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    json_handler.setFormatter(json_formatter)
    root_logger.addHandler(json_handler)
    
    # 2. Text File Handler (Rotating)
    text_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / 'soc_assistant.log',
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=10,
        encoding='utf-8'
    )
    text_handler.setLevel(logging.INFO)
    text_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    text_handler.setFormatter(text_formatter)
    root_logger.addHandler(text_handler)
    
    # 3. Error File Handler (Rotating)
    error_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / 'soc_assistant.error.log',
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(text_formatter)
    root_logger.addHandler(error_handler)
    
    # 4. Console Handler (for development)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # 5. Security Audit Log Handler
    audit_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / 'security_audit.log',
        maxBytes=100 * 1024 * 1024,  # 100MB
        backupCount=20,
        encoding='utf-8'
    )
    audit_handler.setLevel(logging.INFO)
    audit_handler.setFormatter(json_formatter)
    
    # Create security logger
    security_logger = logging.getLogger('security')
    security_logger.addHandler(audit_handler)
    security_logger.setLevel(logging.INFO)
    
    # Reduce noise from external libraries
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('socketio').setLevel(logging.WARNING)
    logging.getLogger('engineio').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    
    logging.info("✅ Logging infrastructure initialized")
    logging.info(f"📁 Log directory: {log_path.absolute()}")
    logging.info(f"📊 Log level: {logging.getLevelName(log_level)}")
    
    return root_logger


def log_security_event(event_type, user=None, ip_address=None, details=None, success=True):
    """
    Log security-relevant events to audit log
    """
    security_logger = logging.getLogger('security')
    
    event_data = {
        'event_type': event_type,
        'timestamp': datetime.utcnow().isoformat(),
        'success': success,
        'user': user,
        'ip_address': ip_address,
        'details': details or {}
    }
    
    if success:
        security_logger.info(f"Security Event: {event_type}", extra=event_data)
    else:
        security_logger.warning(f"Security Event Failed: {event_type}", extra=event_data)


def log_ml_prediction(model_type, input_data, prediction, confidence, latency_ms):
    """
    Log ML prediction for audit and analysis
    """
    ml_logger = logging.getLogger('ml_predictions')
    
    prediction_data = {
        'model_type': model_type,
        'timestamp': datetime.utcnow().isoformat(),
        'prediction': prediction,
        'confidence': confidence,
        'latency_ms': latency_ms,
        'input_summary': {
            'features': len(input_data) if isinstance(input_data, dict) else 'unknown'
        }
    }
    
    ml_logger.info(f"ML Prediction: {model_type}", extra=prediction_data)


def log_alert_generated(alert_id, severity, attack_type, source_ip, confidence):
    """
    Log alert generation for tracking
    """
    alert_logger = logging.getLogger('alerts')
    
    alert_data = {
        'alert_id': alert_id,
        'severity': severity,
        'attack_type': attack_type,
        'source_ip': source_ip,
        'confidence': confidence,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    alert_logger.info(f"Alert Generated: {alert_id}", extra=alert_data)


def log_api_request(method, endpoint, status_code, latency_ms, user=None, ip_address=None):
    """
    Log API request for monitoring
    """
    api_logger = logging.getLogger('api')
    
    request_data = {
        'method': method,
        'endpoint': endpoint,
        'status_code': status_code,
        'latency_ms': latency_ms,
        'user': user,
        'ip_address': ip_address,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if status_code >= 500:
        api_logger.error(f"API Error: {method} {endpoint}", extra=request_data)
    elif status_code >= 400:
        api_logger.warning(f"API Client Error: {method} {endpoint}", extra=request_data)
    else:
        api_logger.info(f"API Request: {method} {endpoint}", extra=request_data)


class LogContext:
    """
    Context manager for adding context to logs
    """
    
    def __init__(self, **context):
        self.context = context
        self.logger = logging.getLogger()
    
    def __enter__(self):
        # Store context in thread-local storage if needed
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(
                f"Exception in context: {exc_type.__name__}",
                extra={'context': self.context, 'exception': str(exc_val)},
                exc_info=True
            )
        return False
