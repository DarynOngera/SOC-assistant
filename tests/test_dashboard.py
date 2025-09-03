#!/usr/bin/env python3
"""
Quick test script for SOC Dashboard components
"""

import sys
import os
import json
from pathlib import Path

def test_tailwind_config():
    """Test Tailwind configuration"""
    config_path = Path("dashboard/tailwind.config.js")
    if not config_path.exists():
        return False, "Tailwind config not found"
    
    try:
        with open(config_path, 'r') as f:
            content = f.read()
            
        # Check for required color variants
        required_colors = ['danger-800', 'warning-800', 'success-800', 'yellow-800']
        missing_colors = []
        
        for color in required_colors:
            if color.replace('-', ': ') not in content:
                missing_colors.append(color)
        
        if missing_colors:
            return False, f"Missing color variants: {missing_colors}"
        
        return True, "All required color variants found"
    except Exception as e:
        return False, f"Error reading config: {e}"

def test_react_components():
    """Test React component files"""
    components_dir = Path("dashboard/src/components")
    if not components_dir.exists():
        return False, "Components directory not found"
    
    required_components = [
        "Header.js",
        "StatusCards.js", 
        "AlertsTable.js",
        "ThresholdControl.js",
        "ScoreDistribution.js"
    ]
    
    missing_components = []
    for component in required_components:
        if not (components_dir / component).exists():
            missing_components.append(component)
    
    if missing_components:
        return False, f"Missing components: {missing_components}"
    
    return True, f"All {len(required_components)} components found"

def test_backend_imports():
    """Test backend dependencies"""
    try:
        import flask
        import flask_cors
        import flask_socketio
        import pandas
        import numpy
        import joblib
        return True, "All backend dependencies available"
    except ImportError as e:
        return False, f"Missing dependency: {e}"

def test_dashboard_structure():
    """Test overall dashboard structure"""
    required_files = [
        "dashboard_server.py",
        "start_dashboard.py",
        "dashboard/package.json",
        "dashboard/src/App.js",
        "dashboard/src/index.js",
        "dashboard/src/index.css"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        return False, f"Missing files: {missing_files}"
    
    return True, "All dashboard files present"

def main():
    """Run all tests"""
    print("="*60)
    print("SOC DASHBOARD COMPONENT TESTS")
    print("="*60)
    
    tests = [
        ("Dashboard Structure", test_dashboard_structure),
        ("Tailwind Configuration", test_tailwind_config),
        ("React Components", test_react_components),
        ("Backend Dependencies", test_backend_imports)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            success, message = test_func()
            if success:
                print(f"✓ {message}")
                results.append(True)
            else:
                print(f"✗ {message}")
                results.append(False)
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Dashboard is ready to run.")
        print("\nTo start the dashboard:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Navigate to dashboard: cd dashboard && npm install")
        print("3. Start backend: python dashboard_server.py")
        print("4. Start frontend: cd dashboard && npm start")
    else:
        print("⚠ Some tests failed. Please check the issues above.")
    
    print("="*60)

if __name__ == "__main__":
    main()
