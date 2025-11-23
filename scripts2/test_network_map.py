#!/usr/bin/env python3
"""
Comprehensive test script for Network Map functionality
Tests both backend API endpoints and validates data structure
"""

import requests
import json
import time
from datetime import datetime, timedelta

class NetworkMapTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.token = None
        self.headers = {}
        
    def authenticate(self, username="admin", password="SecureAdmin123!"):
        """Authenticate and get access token"""
        print("🔐 Authenticating...")
        
        try:
            # First check if MFA is required
            mfa_response = requests.post(f"{self.base_url}/api/auth/check-mfa", json={
                "username": username
            })
            
            mfa_required = False
            if mfa_response.status_code == 200:
                mfa_data = mfa_response.json()
                mfa_required = mfa_data.get('mfa_required', False)
            
            # Use credentials without MFA for testing
            if mfa_required:
                print(f"⚠️  User {username} requires MFA, trying john_analyst...")
                # Try john_analyst which should not have MFA enabled
                username = "john_analyst"
                password = "AnalystPass123!"
            
            response = requests.post(f"{self.base_url}/api/auth/login", json={
                "username": username,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['access_token']
                self.headers = {'Authorization': f'Bearer {self.token}'}
                print(f"✅ Authentication successful for user: {data['user']['username']}")
                return True
            else:
                print(f"❌ Authentication failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def test_network_topology_endpoint(self):
        """Test the network topology API endpoint"""
        print("\n📊 Testing Network Topology Endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/api/network/topology", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate data structure
                required_keys = ['nodes', 'edges', 'subnets', 'stats']
                for key in required_keys:
                    if key not in data:
                        print(f"❌ Missing key in response: {key}")
                        return False
                
                # Validate nodes structure
                if data['nodes']:
                    node = data['nodes'][0]
                    node_keys = ['id', 'ip', 'subnet', 'type', 'alert_count', 'severity_counts']
                    for key in node_keys:
                        if key not in node:
                            print(f"❌ Missing key in node: {key}")
                            return False
                
                # Validate edges structure
                if data['edges']:
                    edge = data['edges'][0]
                    edge_keys = ['id', 'source', 'target', 'weight', 'alerts']
                    for key in edge_keys:
                        if key not in edge:
                            print(f"❌ Missing key in edge: {key}")
                            return False
                
                print(f"✅ Network topology endpoint working")
                print(f"   - Nodes: {len(data['nodes'])}")
                print(f"   - Edges: {len(data['edges'])}")
                print(f"   - Subnets: {len(data['subnets'])}")
                
                return True
                
            else:
                print(f"❌ Network topology request failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Network topology test error: {e}")
            return False
    
    def test_network_connections_endpoint(self):
        """Test the network connections API endpoint"""
        print("\n🔗 Testing Network Connections Endpoint...")
        
        timeframes = ['1h', '24h', '7d']
        
        for timeframe in timeframes:
            try:
                response = requests.get(
                    f"{self.base_url}/api/network/connections?timeframe={timeframe}", 
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Validate data structure
                    required_keys = ['connections', 'timeframe', 'total_connections']
                    for key in required_keys:
                        if key not in data:
                            print(f"❌ Missing key in connections response: {key}")
                            return False
                    
                    # Validate connections structure
                    if data['connections']:
                        conn = data['connections'][0]
                        conn_keys = ['source_ip', 'destination_ip', 'connection_count', 'max_score']
                        for key in conn_keys:
                            if key not in conn:
                                print(f"❌ Missing key in connection: {key}")
                                return False
                    
                    print(f"✅ Network connections ({timeframe}): {len(data['connections'])} connections")
                    
                else:
                    print(f"❌ Network connections request failed for {timeframe}: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ Network connections test error for {timeframe}: {e}")
                return False
        
        return True
    
    def test_ip_classification(self):
        """Test IP classification functions"""
        print("\n🏷️  Testing IP Classification...")
        
        # Test with topology data
        try:
            response = requests.get(f"{self.base_url}/api/network/topology", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check IP type classification
                internal_count = sum(1 for node in data['nodes'] if node['type'] == 'internal')
                external_count = sum(1 for node in data['nodes'] if node['type'] == 'external')
                localhost_count = sum(1 for node in data['nodes'] if node['type'] == 'localhost')
                
                print(f"✅ IP Classification results:")
                print(f"   - Internal IPs: {internal_count}")
                print(f"   - External IPs: {external_count}")
                print(f"   - Localhost IPs: {localhost_count}")
                
                # Check subnet classification
                subnet_types = set(node['subnet'] for node in data['nodes'])
                print(f"   - Unique subnets: {len(subnet_types)}")
                for subnet in list(subnet_types)[:5]:  # Show first 5 subnets
                    print(f"     • {subnet}")
                
                return True
                
            else:
                print(f"❌ Failed to get topology data for classification test")
                return False
                
        except Exception as e:
            print(f"❌ IP classification test error: {e}")
            return False
    
    def test_data_consistency(self):
        """Test data consistency between endpoints"""
        print("\n🔍 Testing Data Consistency...")
        
        try:
            # Get topology data
            topo_response = requests.get(f"{self.base_url}/api/network/topology", headers=self.headers)
            conn_response = requests.get(f"{self.base_url}/api/network/connections", headers=self.headers)
            
            if topo_response.status_code == 200 and conn_response.status_code == 200:
                topo_data = topo_response.json()
                conn_data = conn_response.json()
                
                # Extract IPs from both endpoints
                topo_ips = set()
                for node in topo_data['nodes']:
                    topo_ips.add(node['ip'])
                
                conn_ips = set()
                for conn in conn_data['connections']:
                    conn_ips.add(conn['source_ip'])
                    conn_ips.add(conn['destination_ip'])
                
                # Check overlap
                common_ips = topo_ips.intersection(conn_ips)
                
                print(f"✅ Data consistency check:")
                print(f"   - Topology IPs: {len(topo_ips)}")
                print(f"   - Connection IPs: {len(conn_ips)}")
                print(f"   - Common IPs: {len(common_ips)}")
                
                if len(common_ips) > 0:
                    print(f"   - Consistency ratio: {len(common_ips)/max(len(topo_ips), len(conn_ips)):.2%}")
                
                return True
                
            else:
                print(f"❌ Failed to get data for consistency test")
                return False
                
        except Exception as e:
            print(f"❌ Data consistency test error: {e}")
            return False
    
    def test_performance(self):
        """Test API performance"""
        print("\n⚡ Testing API Performance...")
        
        endpoints = [
            ('/api/network/topology', 'Network Topology'),
            ('/api/network/connections', 'Network Connections')
        ]
        
        for endpoint, name in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", headers=self.headers)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                if response.status_code == 200:
                    data_size = len(response.content)
                    print(f"✅ {name}:")
                    print(f"   - Response time: {response_time:.2f}ms")
                    print(f"   - Data size: {data_size:,} bytes")
                    
                    if response_time > 5000:  # 5 seconds
                        print(f"   ⚠️  Slow response time detected")
                else:
                    print(f"❌ {name} failed: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Performance test error for {name}: {e}")
    
    def generate_test_report(self):
        """Generate a comprehensive test report"""
        print("\n" + "="*60)
        print("📋 NETWORK MAP TEST REPORT")
        print("="*60)
        
        tests = [
            ("Authentication", self.authenticate),
            ("Network Topology Endpoint", self.test_network_topology_endpoint),
            ("Network Connections Endpoint", self.test_network_connections_endpoint),
            ("IP Classification", self.test_ip_classification),
            ("Data Consistency", self.test_data_consistency),
            ("API Performance", self.test_performance)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running: {test_name}")
            try:
                if test_name == "Authentication":
                    result = test_func()
                else:
                    result = test_func() if self.token else False
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
                results.append((test_name, False))
        
        # Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n🎯 Overall Result: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All network map tests passed! The system is ready for use.")
        else:
            print("⚠️  Some tests failed. Please check the server logs and configuration.")

def main():
    print("🗺️  Network Map Comprehensive Test Suite")
    print("=" * 50)
    print("This script tests all network map functionality including:")
    print("• API endpoints and data structure")
    print("• IP classification and subnet analysis") 
    print("• Data consistency between endpoints")
    print("• Performance and response times")
    print("\nMake sure the SOC Dashboard server is running on localhost:5000")
    print("=" * 50)
    
    tester = NetworkMapTester()
    tester.generate_test_report()

if __name__ == "__main__":
    main()
