#!/usr/bin/env python3
"""
Startup script for SOC Dashboard with Authentication
Initializes the authenticated dashboard server with proper environment setup
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🔐 Starting SOC Dashboard with Authentication...")
    print("=" * 50)
    
    # Check if virtual environment exists
    venv_path = project_root / "venv"
    if not venv_path.exists():
        print("❌ Virtual environment not found. Please run setup first:")
        print("   python -m venv venv")
        print("   source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
        print("   pip install -r requirements.txt")
        return 1
    
    # Create data directory for user data and audit logs
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    
    print("📁 Data directory created/verified")
    
    # Set environment variables for security
    os.environ.setdefault('FLASK_SECRET_KEY', 'soc-dashboard-secret-key-change-in-production')
    os.environ.setdefault('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    
    print("🔑 Environment variables configured")
    
    # Start the authenticated server
    print("\n🚀 Starting authenticated SOC Dashboard server...")
    print("📍 Server will be available at: http://localhost:5000")
    print("👤 Default admin credentials:")
    print("   Username: admin")
    print("   Password: SecureAdmin123!")
    print("\n📋 Features available:")
    print("   ✅ JWT-based authentication")
    print("   ✅ Google Authenticator MFA")
    print("   ✅ Role-based access control (Admin/Analyst)")
    print("   ✅ User management (CRUD operations)")
    print("   ✅ Comprehensive audit logging")
    print("   ✅ Real-time anomaly detection")
    print("   ✅ WebSocket support with authentication")
    print("\n🔒 Security features:")
    print("   ✅ Password strength requirements")
    print("   ✅ Account lockout after failed attempts")
    print("   ✅ Session management with token refresh")
    print("   ✅ Rate limiting on login attempts")
    print("   ✅ Secure password hashing (bcrypt)")
    print("\n" + "=" * 50)
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Run the authenticated server
        server_path = project_root / "src" / "dashboard" / "auth_server.py"
        subprocess.run([sys.executable, str(server_path)], check=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Server failed to start: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
