"""
Swagger/OpenAPI Documentation Configuration
Provides interactive API documentation at /api/docs
"""

from flasgger import Swagger, swag_from
from flask import request
import os

# Swagger configuration
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs"
}

# Swagger template with API information
swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "SOC Assistant API",
        "description": """
# SOC Assistant REST API

Production-ready Security Operations Center (SOC) assistant API combining machine learning anomaly detection with natural language processing for intelligent alert analysis.

## Features
- **Network Anomaly Detection**: ML-powered analysis with 96%+ accuracy
- **NLP Alert Analysis**: Intelligent classification and threat intelligence
- **Real-time Monitoring**: WebSocket-based live updates
- **Role-Based Access Control**: Multi-tier RBAC system
- **Prometheus Metrics**: Production-grade monitoring

## Authentication
Most endpoints require JWT authentication. To authenticate:

1. **Login**: POST to `/api/auth/login` with username and password
2. **Get Token**: Receive `access_token` in response
3. **Use Token**: Include in Authorization header: `Bearer <access_token>`
4. **Refresh**: Use `/api/auth/refresh` to get new tokens

## Rate Limiting
- Login endpoints: 5 requests per minute
- General endpoints: 1000 requests per hour
- Admin endpoints: Higher limits

## WebSocket Events
Connect to `ws://localhost:5000/socket.io` for real-time updates:
- `new_alerts`: Real-time alert notifications
- `stats_update`: Live system statistics
- `connection_established`: Connection confirmation

## Response Codes
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `429`: Rate Limit Exceeded
- `500`: Internal Server Error
        """,
        "version": "1.0.0",
        "contact": {
            "name": "SOC Assistant Team",
            "url": "https://github.com/DarynOngera/SOC-assistant"
        },
        "license": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    },
    "host": "localhost:5000",
    "basePath": "/",
    "schemes": ["http", "https"],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using the Bearer scheme. Example: 'Bearer {token}'"
        }
    },
    "security": [
        {
            "Bearer": []
        }
    ],
    "tags": [
        {
            "name": "Authentication",
            "description": "User authentication and authorization endpoints"
        },
        {
            "name": "Alerts",
            "description": "Security alert management and retrieval"
        },
        {
            "name": "Statistics",
            "description": "System statistics and metrics"
        },
        {
            "name": "Monitoring",
            "description": "Real-time monitoring control"
        },
        {
            "name": "NLP",
            "description": "Natural Language Processing analysis"
        },
        {
            "name": "Admin",
            "description": "Administrative operations (admin only)"
        },
        {
            "name": "Health",
            "description": "Health check and readiness endpoints"
        },
        {
            "name": "CSV",
            "description": "CSV file upload and analysis"
        },
        {
            "name": "MFA",
            "description": "Multi-Factor Authentication management"
        }
    ],
    "definitions": {
        "Alert": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "example": 1},
                "timestamp": {"type": "string", "format": "date-time"},
                "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                "source_ip": {"type": "string", "example": "192.168.1.100"},
                "destination_ip": {"type": "string", "example": "10.0.1.50"},
                "attack_type": {"type": "string", "example": "DDoS"},
                "anomaly_score": {"type": "number", "format": "float", "example": 0.85},
                "confidence": {"type": "number", "format": "float", "example": 0.92},
                "status": {"type": "string", "enum": ["new", "flagged", "dismissed"]},
                "flagged": {"type": "boolean"},
                "dismissed": {"type": "boolean"}
            }
        },
        "User": {
            "type": "object",
            "properties": {
                "username": {"type": "string", "example": "admin"},
                "email": {"type": "string", "example": "admin@soc.local"},
                "role": {"type": "string", "enum": ["super_admin", "soc_manager", "senior_analyst", "analyst", "viewer"]},
                "mfa_enabled": {"type": "boolean"},
                "created_at": {"type": "string", "format": "date-time"},
                "last_login": {"type": "string", "format": "date-time"}
            }
        },
        "LoginRequest": {
            "type": "object",
            "required": ["username", "password"],
            "properties": {
                "username": {"type": "string", "example": "admin"},
                "password": {"type": "string", "example": "SecureAdmin123!"},
                "mfa_token": {"type": "string", "example": "123456"}
            }
        },
        "LoginResponse": {
            "type": "object",
            "properties": {
                "access_token": {"type": "string"},
                "refresh_token": {"type": "string"},
                "user": {"$ref": "#/definitions/User"},
                "expires_in": {"type": "integer", "example": 28800}
            }
        },
        "Stats": {
            "type": "object",
            "properties": {
                "total_processed": {"type": "integer"},
                "anomalies_detected": {"type": "integer"},
                "total_alerts": {"type": "integer"},
                "active_alerts": {"type": "integer"},
                "system_health": {"type": "string", "enum": ["healthy", "degraded", "critical"]},
                "threshold": {"type": "number", "format": "float"},
                "severity_distribution": {
                    "type": "object",
                    "properties": {
                        "critical": {"type": "integer"},
                        "high": {"type": "integer"},
                        "medium": {"type": "integer"},
                        "low": {"type": "integer"}
                    }
                },
                "detection_rate": {"type": "number", "format": "float"}
            }
        },
        "Error": {
            "type": "object",
            "properties": {
                "error": {"type": "string", "example": "Error message"}
            }
        },
        "Success": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "example": "Operation successful"}
            }
        }
    }
}


def init_swagger(app):
    """
    Initialize Swagger documentation for Flask app
    
    Args:
        app: Flask application instance
    
    Returns:
        Swagger instance
    """
    swagger = Swagger(app, config=swagger_config, template=swagger_template)
    
    # Log initialization
    app.logger.info("✅ Swagger API documentation initialized at /api/docs")
    
    return swagger


# Decorator for adding Swagger documentation to endpoints
def document_endpoint(summary, description, tags, responses, parameters=None, security=None):
    """
    Decorator to add Swagger documentation to Flask endpoints
    
    Args:
        summary: Brief endpoint summary
        description: Detailed endpoint description
        tags: List of tags for grouping
        responses: Dictionary of response codes and descriptions
        parameters: List of parameter definitions (optional)
        security: Security requirements (optional)
    
    Returns:
        Decorated function
    """
    def decorator(f):
        # Build Swagger spec
        spec = {
            "summary": summary,
            "description": description,
            "tags": tags,
            "responses": responses
        }
        
        if parameters:
            spec["parameters"] = parameters
        
        if security:
            spec["security"] = security
        
        # Apply flasgger decorator
        return swag_from(spec)(f)
    
    return decorator
