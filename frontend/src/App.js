import React, { useState, useEffect } from 'react';
import { io } from 'socket.io-client';
import StatusCards from './components/StatusCards';
import AlertsTable from './components/AlertsTable';
import ThresholdControl from './components/ThresholdControl';
import ScoreDistribution from './components/ScoreDistribution';
import Header from './components/Header';
import { Shield, Activity, AlertTriangle, CheckCircle } from 'lucide-react';

const API_BASE_URL = 'http://localhost:5000';

function App() {
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState({
    total_processed: 0,
    anomalies_detected: 0,
    total_alerts: 0,
    active_alerts: 0,
    system_health: 'healthy',
    threshold: 0.5,
    severity_distribution: { critical: 0, high: 0, medium: 0, low: 0 },
    detection_rate: 0
  });
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Initialize socket connection
    const newSocket = io(API_BASE_URL);
    setSocket(newSocket);

    newSocket.on('connect', () => {
      setIsConnected(true);
      console.log('Connected to server');
    });

    newSocket.on('disconnect', () => {
      setIsConnected(false);
      console.log('Disconnected from server');
    });

    newSocket.on('connection_established', (data) => {
      console.log('Connection established:', data);
    });

    newSocket.on('new_alerts', (data) => {
      setAlerts(prevAlerts => [...data.alerts, ...prevAlerts].slice(0, 100));
      setStats(data.stats);
    });

    newSocket.on('stats_update', (data) => {
      setStats(data);
    });

    newSocket.on('alerts_update', (data) => {
      setAlerts(data.alerts);
      setStats(data.stats);
    });

    // Request initial data
    setTimeout(() => {
      newSocket.emit('request_alerts');
      fetchInitialData();
    }, 1000);

    return () => {
      newSocket.close();
    };
  }, []);

  const fetchInitialData = async () => {
    try {
      const [alertsResponse, statsResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/api/alerts?per_page=50`),
        fetch(`${API_BASE_URL}/api/stats`)
      ]);

      if (alertsResponse.ok) {
        const alertsData = await alertsResponse.json();
        setAlerts(alertsData.alerts);
      }

      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      }
    } catch (error) {
      console.error('Error fetching initial data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleThresholdChange = async (newThreshold) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/threshold`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ threshold: newThreshold }),
      });

      if (response.ok) {
        const data = await response.json();
        setStats(prev => ({ ...prev, threshold: data.threshold }));
      }
    } catch (error) {
      console.error('Error updating threshold:', error);
    }
  };

  const handleAlertAction = async (alertId, action) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/alerts/${alertId}/${action}`, {
        method: 'POST',
      });

      if (response.ok) {
        setAlerts(prevAlerts =>
          prevAlerts.map(alert =>
            alert.id === alertId
              ? { ...alert, status: action === 'flag' ? 'flagged' : 'dismissed' }
              : alert
          )
        );
      }
    } catch (error) {
      console.error(`Error ${action}ing alert:`, error);
    }
  };

  const startMonitoring = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/monitoring/start`, { method: 'POST' });
    } catch (error) {
      console.error('Error starting monitoring:', error);
    }
  };

  const stopMonitoring = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/monitoring/stop`, { method: 'POST' });
    } catch (error) {
      console.error('Error stopping monitoring:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <span className="text-gray-600">Loading SOC Dashboard...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header 
        isConnected={isConnected}
        onStartMonitoring={startMonitoring}
        onStopMonitoring={stopMonitoring}
      />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Status Cards */}
        <div className="mb-8">
          <StatusCards stats={stats} />
        </div>

        {/* Controls and Visualizations */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Threshold Control */}
          <div className="card">
            <ThresholdControl
              threshold={stats.threshold}
              onThresholdChange={handleThresholdChange}
            />
          </div>

          {/* Score Distribution */}
          <div className="card">
            <ScoreDistribution />
          </div>
        </div>

        {/* Alerts Table */}
        <div className="card">
          <AlertsTable
            alerts={alerts}
            onAlertAction={handleAlertAction}
          />
        </div>
      </main>
    </div>
  );
}

export default App;
