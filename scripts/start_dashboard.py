#!/usr/bin/env python3
"""
SOC Dashboard Startup Script
Initializes the dashboard with pre-trained models and sample data
"""

import os
import sys
import subprocess
import time
import threading
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def install_dependencies():
    """Install required Python dependencies"""
    print("Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✓ Python dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Error installing dependencies: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False
    return True

def setup_react_dashboard():
    """Setup React dashboard dependencies"""
    dashboard_dir = project_root / "frontend"
    if not dashboard_dir.exists():
        print("✗ Dashboard directory not found")
        return False
    
    print("Setting up React dashboard...")
    try:
        # Install npm dependencies
        subprocess.run(["npm", "install"], cwd=dashboard_dir, check=True, 
                      capture_output=True, text=True)
        print("✓ React dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error setting up React dashboard: {e}")
        print("Make sure Node.js and npm are installed")
        return False
    except FileNotFoundError:
        print("✗ npm not found. Please install Node.js and npm")
        return False

def start_flask_server():
    """Start the Flask backend server"""
    print("Starting Flask backend server...")
    try:
        # Change to project root directory
        os.chdir(project_root)
        
        # Start server in background
        server_path = project_root / "src" / "dashboard" / "server.py"
        process = subprocess.Popen([sys.executable, str(server_path)], 
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        time.sleep(3)  # Give server time to start
        
        if process.poll() is None:
            print("✓ Flask server started successfully on http://localhost:5000")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"✗ Flask server failed to start")
            print(f"Output: {stdout}")
            print(f"Error: {stderr}")
            return None
    except Exception as e:
        print(f"✗ Error starting Flask server: {e}")
        return None

def start_react_dev_server():
    """Start the React development server"""
    dashboard_dir = project_root / "frontend"
    print("Starting React development server...")
    try:
        # Start React dev server in background
        process = subprocess.Popen(["npm", "start"], cwd=dashboard_dir,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        time.sleep(5)  # Give server time to start
        
        print("✓ React dev server starting on http://localhost:3000")
        print("  Dashboard will open in your browser automatically")
        return process
    except Exception as e:
        print(f"✗ Error starting React server: {e}")
        return None

def check_models():
    """Check if trained models exist"""
    models_dir = project_root / "models"
    if not models_dir.exists():
        print("⚠ Models directory not found. Dashboard will use mock data.")
        return False
    
    model_files = list(models_dir.glob("*.pkl")) + list(models_dir.glob("*.h5"))
    if model_files:
        print(f"✓ Found {len(model_files)} model files")
        return True
    else:
        print("⚠ No trained models found. Dashboard will use mock data.")
        return False

def main():
    """Main startup function"""
    print("="*60)
    print("SOC DASHBOARD STARTUP")
    print("="*60)
    
    # Change to project root directory
    os.chdir(project_root)
    print(f"Working directory: {project_root}")
    
    # Check for models
    has_models = check_models()
    
    # Check for required directories
    frontend_dir = project_root / "frontend"
    src_dir = project_root / "src"
    
    if not frontend_dir.exists():
        print("✗ Frontend directory not found. Please ensure React frontend is available.")
        return
    
    if not src_dir.exists():
        print("✗ Source directory not found. Please ensure backend source code is available.")
        return
    
    # Install Python dependencies
    if not install_dependencies():
        print("Failed to install Python dependencies. Exiting.")
        return
    
    # Setup React dashboard
    if not setup_react_dashboard():
        print("Failed to setup React dashboard. Exiting.")
        return
    
    # Start Flask server
    flask_process = start_flask_server()
    if not flask_process:
        print("Failed to start Flask server. Exiting.")
        return
    
    # Start React dev server
    react_process = start_react_dev_server()
    if not react_process:
        print("Failed to start React server. Cleaning up...")
        flask_process.terminate()
        return
    
    print("\n" + "="*60)
    print("DASHBOARD READY!")
    print("="*60)
    print("🚀 SOC Dashboard is now running:")
    print("   • Backend API: http://localhost:5000")
    print("   • Frontend UI: http://localhost:3000")
    print("\n📊 Dashboard Features:")
    print("   • Real-time anomaly detection")
    print("   • Interactive threshold adjustment")
    print("   • Alert prioritization table")
    print("   • Score distribution visualization")
    print("   • System status monitoring")
    
    if not has_models:
        print("\n⚠ Note: Using mock data (no trained models found)")
        print("   Train models first using: python scripts/train_models.py")
    
    print("\n🔧 Controls:")
    print("   • Press Ctrl+C to stop both servers")
    print("   • Use Start/Stop buttons in dashboard to control monitoring")
    print("="*60)
    
    try:
        # Wait for user interruption
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down servers...")
        flask_process.terminate()
        react_process.terminate()
        
        # Wait for processes to terminate
        flask_process.wait()
        react_process.wait()
        
        print("✓ Servers stopped successfully")

if __name__ == "__main__":
    main()
