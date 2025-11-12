# Quick Start: View Your Mininet Topology

## 🚀 3-Step Quick Start

### 1. Ensure Topology is Generated ✅
```bash
# Already done! File exists at:
# mininet_data_generation/data_capture/mininet_topology.json
```

### 2. Start the Dashboard
```bash
# Terminal 1: Backend
cd /home/ongera/projects/SOC-assistant
python src/dashboard/server.py

# Terminal 2: Frontend (if not running)
cd frontend
npm start
```

### 3. View Network Map
1. Open browser: `http://localhost:3000`
2. Login (username: `admin`, password: `SecurePass123!`)
3. Click **Network Map** in navigation
4. Toggle to **Mininet** view (top right)

## 🎯 What You'll See

Your complete Mininet topology with:
- **10 hosts** (servers, clients, internal servers)
- **3 switches** (yellow squares)
- **3 network segments** (color-coded zones)
- **All connections** (trunk and access links)
- **Real-time alerts** (if any traffic generated)

## 💡 Try This

### Generate Some Traffic
```bash
cd mininet_data_generation
sudo python3 topology/generate_normal_traffic.py
```

Then watch alerts appear on your topology in real-time!

## 🎨 View Controls

- **Mininet/Alerts Toggle**: Switch between views
- **Refresh Button**: Manual refresh
- **Show Segments**: Toggle network zones
- **Click Hosts**: View detailed information

---

**Everything is ready to go!** Just start the servers and navigate to Network Map.
