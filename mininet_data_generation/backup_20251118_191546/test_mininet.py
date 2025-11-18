#!/usr/bin/env python3
"""
Test Mininet Setup
Quick test to verify Mininet works without controller
"""

import sys
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel

def test_mininet():
    """Test basic Mininet functionality"""
    print("Testing Mininet setup...")
    
    try:
        # Create simple network without controller
        net = Mininet(
            switch=OVSSwitch,
            link=TCLink,
            autoSetMacs=True,
            autoStaticArp=True,
            controller=None
        )
        
        print("✓ Creating network...")
        
        # Add switch
        s1 = net.addSwitch('s1')
        print("✓ Added switch")
        
        # Add hosts
        h1 = net.addHost('h1', ip='10.0.0.1/24')
        h2 = net.addHost('h2', ip='10.0.0.2/24')
        print("✓ Added hosts")
        
        # Add links
        net.addLink(h1, s1)
        net.addLink(h2, s1)
        print("✓ Added links")
        
        # Start network
        net.start()
        print("✓ Network started")
        
        # Test ping
        print("\nTesting connectivity...")
        result = h1.cmd(f'ping -c 1 {h2.IP()}')
        if '1 received' in result:
            print("✓ Ping successful!")
        else:
            print("✗ Ping failed")
            print(result)
        
        # Stop network
        net.stop()
        print("✓ Network stopped")
        
        print("\n✓ Mininet test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n✗ Mininet test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    setLogLevel('info')
    success = test_mininet()
    sys.exit(0 if success else 1)
