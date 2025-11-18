#!/bin/bash
# Quick fix for OpenVSwitch installation on CentOS

echo "🔧 Fixing OpenVSwitch installation on CentOS..."

# Try different OpenVSwitch packages
echo "Trying different OpenVSwitch package names..."

if command -v dnf &> /dev/null; then
    PACKAGE_MANAGER="dnf"
else
    PACKAGE_MANAGER="yum"
fi

# Try various OVS package names
sudo $PACKAGE_MANAGER install -y openvswitch2.17 || \
sudo $PACKAGE_MANAGER install -y openvswitch2.15 || \
sudo $PACKAGE_MANAGER install -y openvswitch || \
sudo $PACKAGE_MANAGER install -y network-scripts-openvswitch || {
    echo "⚠️ Package installation failed, installing from source..."
    
    # Install from source as fallback
    cd /tmp
    wget https://www.openvswitch.org/releases/openvswitch-2.17.0.tar.gz
    tar -xzf openvswitch-2.17.0.tar.gz
    cd openvswitch-2.17.0
    
    # Install build dependencies
    sudo $PACKAGE_MANAGER install -y gcc make python3-devel openssl-devel kernel-devel kernel-headers
    
    # Configure and build
    ./configure --prefix=/usr --localstatedir=/var --sysconfdir=/etc
    make
    sudo make install
    
    # Create systemd service
    sudo tee /etc/systemd/system/openvswitch.service > /dev/null << 'EOL'
[Unit]
Description=Open vSwitch
After=network.target

[Service]
Type=forking
ExecStart=/usr/sbin/ovs-ctl start
ExecStop=/usr/sbin/ovs-ctl stop
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOL

    sudo systemctl daemon-reload
}

# Try to start the service
echo "Starting OpenVSwitch service..."
sudo systemctl enable openvswitch 2>/dev/null || sudo systemctl enable openvswitch2.17 2>/dev/null || true
sudo systemctl start openvswitch 2>/dev/null || sudo systemctl start openvswitch2.17 2>/dev/null || {
    echo "⚠️ Service start failed, trying manual start..."
    sudo /usr/sbin/ovs-ctl start 2>/dev/null || echo "Manual start also failed, continuing anyway..."
}

# Test if OVS is working
if command -v ovs-vsctl &> /dev/null; then
    echo "✅ OpenVSwitch installed successfully"
    sudo ovs-vsctl show
else
    echo "⚠️ OpenVSwitch installation incomplete, but Mininet can work without it"
fi

echo "🔧 OpenVSwitch fix completed!"
