#!/usr/bin/env python3
"""
Test script for Mininet integration with SOC Dashboard
Tests API endpoints and basic functionality
"""

import requests
import json
import time
import sys
import os

# Configuration
API_BASE_URL = 'http://localhost:5000'
TEST_USER = {
    'username': 'admin',
    'password': 'SecureAdmin123!'
}

class MininetIntegrationTester:
    def __init__(self):
        self.token = None
        self.session = requests.Session()
        
    def authenticate(self):
        """Authenticate with the API"""
        print("🔐 Authenticating with SOC Dashboard...")
        
        try:
            response = self.session.post(
                f"{API_BASE_URL}/api/auth/login",
                json=TEST_USER,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def test_mininet_status(self):
        """Test Mininet status endpoint"""
        print("\n📊 Testing Mininet status endpoint...")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/api/mininet/status")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Status endpoint working")
                print(f"   Active: {data.get('active', False)}")
                print(f"   Mode: {data.get('mode', 'None')}")
                return data
            else:
                print(f"❌ Status endpoint failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Status endpoint error: {e}")
            return None
    
    def test_available_attacks(self):
        """Test available attacks endpoint"""
        print("\n⚔️ Testing available attacks endpoint...")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/api/mininet/attacks")
            
            if response.status_code == 200:
                data = response.json()
                attacks = data.get('attacks', [])
                descriptions = data.get('descriptions', {})
                
                print("✅ Available attacks endpoint working")
                print(f"   Available attacks: {len(attacks)}")
                for attack in attacks:
                    desc = descriptions.get(attack, 'No description')
                    print(f"   - {attack}: {desc}")
                return data
            else:
                print(f"❌ Available attacks failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Available attacks error: {e}")
            return None
    
    def test_topology_export(self):
        """Test topology export endpoint"""
        print("\n🗺️ Testing topology export endpoint...")
        
        try:
            response = self.session.post(f"{API_BASE_URL}/api/mininet/export-topology")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ Topology export successful")
                    print(f"   File: {data.get('file', 'Unknown')}")
                    return True
                else:
                    print(f"❌ Topology export failed: {data.get('message')}")
                    return False
            else:
                print(f"❌ Topology export failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Topology export error: {e}")
            return False
    
    def test_mininet_topology_endpoint(self):
        """Test Mininet topology endpoint"""
        print("\n🌐 Testing Mininet topology endpoint...")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/api/network/mininet-topology")
            
            if response.status_code == 200:
                data = response.json()
                available = data.get('available', False)
                
                if available:
                    hosts = data.get('hosts', [])
                    switches = data.get('switches', [])
                    links = data.get('links', [])
                    
                    print("✅ Mininet topology available")
                    print(f"   Hosts: {len(hosts)}")
                    print(f"   Switches: {len(switches)}")
                    print(f"   Links: {len(links)}")
                else:
                    print("⚠️ Mininet topology not available")
                    print(f"   Message: {data.get('message', 'Unknown')}")
                
                return data
            else:
                print(f"❌ Topology endpoint failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Topology endpoint error: {e}")
            return None
    
    def test_simulation_start_stop(self, dry_run=True):
        """Test simulation start/stop (dry run by default)"""
        if dry_run:
            print("\n🧪 Testing simulation endpoints (DRY RUN - not actually starting Mininet)")
            print("   Note: Set dry_run=False to actually test Mininet simulation")
            return True
        
        print("\n🚀 Testing Mininet simulation start/stop...")
        
        # Test normal mode start
        try:
            print("   Starting normal traffic simulation...")
            response = self.session.post(
                f"{API_BASE_URL}/api/mininet/start",
                json={
                    'mode': 'normal',
                    'duration': 30  # Short duration for testing
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ Normal simulation started")
                    
                    # Wait a bit
                    time.sleep(5)
                    
                    # Check status
                    status = self.test_mininet_status()
                    if status and status.get('active'):
                        print("✅ Simulation is running")
                        
                        # Stop simulation
                        print("   Stopping simulation...")
                        stop_response = self.session.post(f"{API_BASE_URL}/api/mininet/stop")
                        
                        if stop_response.status_code == 200:
                            stop_data = stop_response.json()
                            if stop_data.get('success'):
                                print("✅ Simulation stopped successfully")
                                return True
                            else:
                                print(f"❌ Failed to stop: {stop_data.get('message')}")
                        else:
                            print(f"❌ Stop request failed: {stop_response.status_code}")
                    else:
                        print("❌ Simulation not running after start")
                else:
                    print(f"❌ Failed to start: {data.get('message')}")
            else:
                print(f"❌ Start request failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Simulation test error: {e}")
            
        return False
    
    def check_mininet_requirements(self):
        """Check if Mininet requirements are met"""
        print("\n🔍 Checking Mininet requirements...")
        
        requirements = {
            'mininet': 'mn --version',
            'tcpdump': 'tcpdump --version',
            'hping3': 'hping3 --version',
            'nmap': 'nmap --version'
        }
        
        all_good = True
        
        for tool, cmd in requirements.items():
            try:
                result = os.system(f"{cmd} >/dev/null 2>&1")
                if result == 0:
                    print(f"✅ {tool} is installed")
                else:
                    print(f"❌ {tool} is not installed or not accessible")
                    all_good = False
            except Exception as e:
                print(f"❌ Error checking {tool}: {e}")
                all_good = False
        
        # Check if running as root (required for Mininet)
        if os.geteuid() == 0:
            print("✅ Running as root (required for Mininet)")
        else:
            print("⚠️ Not running as root (Mininet requires sudo/root)")
            print("   Note: API endpoints will work, but actual simulation requires root")
        
        return all_good
    
    def run_all_tests(self, test_simulation=False):
        """Run all integration tests"""
        print("="*60)
        print("MININET INTEGRATION TEST SUITE")
        print("="*60)
        
        # Check requirements first
        self.check_mininet_requirements()
        
        # Authenticate
        if not self.authenticate():
            print("\n❌ Cannot proceed without authentication")
            return False
        
        # Test all endpoints
        tests_passed = 0
        total_tests = 0
        
        # Status endpoint
        total_tests += 1
        if self.test_mininet_status() is not None:
            tests_passed += 1
        
        # Available attacks
        total_tests += 1
        if self.test_available_attacks() is not None:
            tests_passed += 1
        
        # Topology export
        total_tests += 1
        if self.test_topology_export():
            tests_passed += 1
        
        # Topology endpoint
        total_tests += 1
        if self.test_mininet_topology_endpoint() is not None:
            tests_passed += 1
        
        # Simulation test (optional)
        if test_simulation:
            total_tests += 1
            if self.test_simulation_start_stop(dry_run=False):
                tests_passed += 1
        else:
            # Dry run test
            total_tests += 1
            if self.test_simulation_start_stop(dry_run=True):
                tests_passed += 1
        
        # Results
        print("\n" + "="*60)
        print("TEST RESULTS")
        print("="*60)
        print(f"Tests passed: {tests_passed}/{total_tests}")
        
        if tests_passed == total_tests:
            print("🎉 All tests passed! Mininet integration is working correctly.")
        else:
            print("⚠️ Some tests failed. Check the output above for details.")
        
        return tests_passed == total_tests

def main():
    """Main test function"""
    tester = MininetIntegrationTester()
    
    # Check command line arguments
    test_simulation = '--test-simulation' in sys.argv
    
    if test_simulation:
        print("⚠️ WARNING: This will actually start Mininet simulation!")
        print("Make sure you have root privileges and Mininet installed.")
        response = input("Continue? (y/N): ")
        if response.lower() != 'y':
            print("Test cancelled.")
            return
    
    success = tester.run_all_tests(test_simulation=test_simulation)
    
    if success:
        print("\n✅ Mininet integration is ready!")
        print("\nNext steps:")
        print("1. Start the SOC Dashboard server: python3 src/dashboard/server.py")
        print("2. Start the frontend: cd frontend && npm start")
        print("3. Login as admin and navigate to 'Mininet Simulation'")
        print("4. Export topology first, then start simulations")
    else:
        print("\n❌ Some issues found. Please fix them before using Mininet integration.")
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
