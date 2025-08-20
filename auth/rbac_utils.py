from enum import Enum
from functools import wraps
from flask import jsonify
import json
from datetime import datetime

class Role(Enum):
    SUPER_ADMIN = "super_admin"
    SOC_MANAGER = "soc_manager"
    SENIOR_ANALYST = "senior_analyst"
    ANALYST = "analyst"
    VIEWER = "viewer"

class Permission(Enum):
    # User management
    CREATE_USER = "create_user"
    DELETE_USER = "delete_user"
    MODIFY_USER = "modify_user"
    VIEW_USERS = "view_users"
    ASSIGN_ROLES = "assign_roles"
    
    # Alert management
    VIEW_ALERTS = "view_alerts"
    MANAGE_ALERTS = "manage_alerts"
    FLAG_ALERTS = "flag_alerts"
    DISMISS_ALERTS = "dismiss_alerts"
    EXPORT_ALERTS = "export_alerts"
    
    # System management
    VIEW_SYSTEM_LOGS = "view_system_logs"
    MANAGE_SYSTEM = "manage_system"
    VIEW_STATISTICS = "view_statistics"
    CONFIGURE_SYSTEM = "configure_system"
    
    # Data management
    VIEW_DATA = "view_data"
    MANAGE_DATA = "manage_data"
    EXPORT_DATA = "export_data"
    
    # Model management
    VIEW_MODELS = "view_models"
    TRAIN_MODELS = "train_models"
    DEPLOY_MODELS = "deploy_models"

# Role-Permission mapping
ROLE_PERMISSIONS = {
    Role.SUPER_ADMIN: [
        # Full system access
        Permission.CREATE_USER,
        Permission.DELETE_USER,
        Permission.MODIFY_USER,
        Permission.VIEW_USERS,
        Permission.ASSIGN_ROLES,
        Permission.VIEW_ALERTS,
        Permission.MANAGE_ALERTS,
        Permission.FLAG_ALERTS,
        Permission.DISMISS_ALERTS,
        Permission.EXPORT_ALERTS,
        Permission.VIEW_SYSTEM_LOGS,
        Permission.MANAGE_SYSTEM,
        Permission.VIEW_STATISTICS,
        Permission.CONFIGURE_SYSTEM,
        Permission.VIEW_DATA,
        Permission.MANAGE_DATA,
        Permission.EXPORT_DATA,
        Permission.VIEW_MODELS,
        Permission.TRAIN_MODELS,
        Permission.DEPLOY_MODELS,
    ],
    
    Role.SOC_MANAGER: [
        # User management (except super admin functions)
        Permission.CREATE_USER,
        Permission.MODIFY_USER,
        Permission.VIEW_USERS,
        Permission.ASSIGN_ROLES,
        # Alert management
        Permission.VIEW_ALERTS,
        Permission.MANAGE_ALERTS,
        Permission.FLAG_ALERTS,
        Permission.DISMISS_ALERTS,
        Permission.EXPORT_ALERTS,
        # System viewing and stats
        Permission.VIEW_SYSTEM_LOGS,
        Permission.VIEW_STATISTICS,
        Permission.VIEW_DATA,
        Permission.EXPORT_DATA,
        Permission.VIEW_MODELS,
        Permission.TRAIN_MODELS,
    ],
    
    Role.SENIOR_ANALYST: [
        # Alert management
        Permission.VIEW_ALERTS,
        Permission.MANAGE_ALERTS,
        Permission.FLAG_ALERTS,
        Permission.DISMISS_ALERTS,
        Permission.EXPORT_ALERTS,
        # Data and statistics
        Permission.VIEW_STATISTICS,
        Permission.VIEW_DATA,
        Permission.EXPORT_DATA,
        Permission.VIEW_MODELS,
    ],
    
    Role.ANALYST: [
        # Basic alert handling
        Permission.VIEW_ALERTS,
        Permission.FLAG_ALERTS,
        Permission.DISMISS_ALERTS,
        # Basic data viewing
        Permission.VIEW_STATISTICS,
        Permission.VIEW_DATA,
        Permission.VIEW_MODELS,
    ],
    
    Role.VIEWER: [
        # Read-only access
        Permission.VIEW_ALERTS,
        Permission.VIEW_STATISTICS,
        Permission.VIEW_DATA,
        Permission.VIEW_MODELS,
    ]
}

class RBACManager:
    def __init__(self):
        self.role_hierarchy = {
            Role.SUPER_ADMIN: 5,
            Role.SOC_MANAGER: 4,
            Role.SENIOR_ANALYST: 3,
            Role.ANALYST: 2,
            Role.VIEWER: 1
        }
    
    def get_user_role(self, username, users_data=None):
        """Get user role from users data"""
        if users_data is None:
            try:
                with open('users.json', 'r') as f:
                    users_data = json.load(f)
            except FileNotFoundError:
                return None
        
        user = users_data.get(username)
        if not user or isinstance(user, str):
            return Role.VIEWER  # Default role for legacy users
        
        role_str = user.get('role', 'viewer')
        try:
            return Role(role_str)
        except ValueError:
            return Role.VIEWER
    
    def has_permission(self, user_role, permission):
        """Check if user role has specific permission"""
        if isinstance(user_role, str):
            try:
                user_role = Role(user_role)
            except ValueError:
                return False
        
        return permission in ROLE_PERMISSIONS.get(user_role, [])
    
    def can_manage_user(self, manager_role, target_role):
        """Check if manager can manage target user based on role hierarchy"""
        if isinstance(manager_role, str):
            manager_role = Role(manager_role)
        if isinstance(target_role, str):
            target_role = Role(target_role)
        
        manager_level = self.role_hierarchy.get(manager_role, 0)
        target_level = self.role_hierarchy.get(target_role, 0)
        
        # Super admin can manage anyone
        if manager_role == Role.SUPER_ADMIN:
            return True
        
        # SOC managers can manage everyone except super admins
        if manager_role == Role.SOC_MANAGER and target_role != Role.SUPER_ADMIN:
            return True
        
        return manager_level > target_level
    
    def get_manageable_roles(self, user_role):
        """Get list of roles that user can assign to others"""
        if isinstance(user_role, str):
            user_role = Role(user_role)
        
        if user_role == Role.SUPER_ADMIN:
            return list(Role)
        elif user_role == Role.SOC_MANAGER:
            return [Role.SOC_MANAGER, Role.SENIOR_ANALYST, Role.ANALYST, Role.VIEWER]
        else:
            return []

def require_permission(permission, rbac_manager=None):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated(current_user, *args, **kwargs):
            if rbac_manager is None:
                rbac = RBACManager()
            else:
                rbac = rbac_manager
            
            user_role = rbac.get_user_role(current_user)
            
            if not rbac.has_permission(user_role, permission):
                return jsonify({
                    'message': 'Insufficient permissions',
                    'required_permission': permission.value
                }), 403
            
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator

def require_role(required_role, rbac_manager=None):
    """Decorator to require specific role or higher"""
    def decorator(f):
        @wraps(f)
        def decorated(current_user, *args, **kwargs):
            if rbac_manager is None:
                rbac = RBACManager()
            else:
                rbac = rbac_manager
            
            user_role = rbac.get_user_role(current_user)
            
            if isinstance(required_role, str):
                required_role_enum = Role(required_role)
            else:
                required_role_enum = required_role
            
            user_level = rbac.role_hierarchy.get(user_role, 0)
            required_level = rbac.role_hierarchy.get(required_role_enum, 0)
            
            if user_level < required_level:
                return jsonify({
                    'message': 'Insufficient role level',
                    'required_role': required_role_enum.value,
                    'current_role': user_role.value if user_role else 'none'
                }), 403
            
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator

def get_role_description(role):
    """Get human-readable role description"""
    descriptions = {
        Role.SUPER_ADMIN: "Super Administrator - Full system access and user management",
        Role.SOC_MANAGER: "SOC Manager - Team management and operational oversight",
        Role.SENIOR_ANALYST: "Senior Analyst - Advanced threat analysis and alert management",
        Role.ANALYST: "Analyst - Basic threat analysis and alert handling",
        Role.VIEWER: "Viewer - Read-only access to alerts and statistics"
    }
    return descriptions.get(role, "Unknown role")

def create_default_super_admin(username, password, auth_manager, filepath='users.json'):
    """Create default super admin user"""
    try:
        with open(filepath, 'r') as f:
            users = json.load(f)
    except FileNotFoundError:
        users = {}
    
    if username in users:
        return False, "User already exists"
    
    # Validate password strength
    is_valid, message = auth_manager.validate_password_strength(password)
    if not is_valid:
        return False, message
    
    # Hash password and store with super admin role
    hashed_password = auth_manager.hash_password(password)
    users[username] = {
        'password': hashed_password,
        'role': Role.SUPER_ADMIN.value,
        'created_at': datetime.utcnow().isoformat(),
        'created_by': 'system',
        'last_login': None,
        'active': True,
        'is_super_admin': True
    }
    
    with open(filepath, 'w') as f:
        json.dump(users, f, indent=2)
    
    return True, "Super admin created successfully"
