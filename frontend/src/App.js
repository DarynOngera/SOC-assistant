import React, { useState, useEffect } from 'react';
import { io } from 'socket.io-client';
import StatusCards from './components/StatusCards';
import AlertsTable from './components/AlertsTable';
import ThresholdControl from './components/ThresholdControl';
import ScoreDistribution from './components/ScoreDistribution';
import AttackDistribution from './components/AttackDistribution';
import AttackTrends from './components/AttackTrends';
import ThreatTriage from './components/ThreatTriage';
import Header from './components/Header';
import Login from './components/Login';
import UserManagement from './components/UserManagement';
import MFASetup from './components/MFASetup';
import AuditLogs from './components/AuditLogs';
import CSVAnalysis from './components/CSVAnalysis';
import { Shield, Activity, AlertTriangle, CheckCircle, Users, Settings, FileText, LogOut, Upload, TrendingUp, Target } from 'lucide-react';

const API_BASE_URL = 'http://localhost:5000';

function App() {
  const [user, setUser] = useState(null);
  const [currentView, setCurrentView] = useState('dashboard');
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
    // Check for existing authentication
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
        initializeSocket(token);
      } catch (error) {
        console.error('Invalid user data:', error);
        handleLogout();
      }
    }
    
    setLoading(false);
  }, []);

  const initializeSocket = (token) => {
    // Initialize socket connection with authentication
    const newSocket = io(API_BASE_URL, {
      auth: { token }
    });
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
      newSocket.emit('request_alerts', { token });
      fetchInitialData();
    }, 1000);

    return newSocket;
  };

  const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const fetchInitialData = async () => {
    try {
      const [alertsResponse, statsResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/api/alerts?per_page=50`, { headers: getAuthHeaders() }),
        fetch(`${API_BASE_URL}/api/stats`, { headers: getAuthHeaders() })
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
    }
  };

  const handleLogin = (userData) => {
    setUser(userData);
    const token = localStorage.getItem('access_token');
    initializeSocket(token);
  };

  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/auth/logout`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
    } catch (error) {
      console.error('Logout error:', error);
    }
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
    setCurrentView('dashboard');
    
    if (socket) {
      socket.close();
      setSocket(null);
      setIsConnected(false);
    }
  };

  const handleMFAChange = (enabled) => {
    setUser(prev => ({ ...prev, mfa_enabled: enabled }));
    const updatedUser = { ...user, mfa_enabled: enabled };
    localStorage.setItem('user', JSON.stringify(updatedUser));
  };

  const handleThresholdChange = async (newThreshold) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/threshold`, {
        method: 'POST',
        headers: getAuthHeaders(),
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
        headers: getAuthHeaders()
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
      await fetch(`${API_BASE_URL}/api/monitoring/start`, { 
        method: 'POST',
        headers: getAuthHeaders()
      });
    } catch (error) {
      console.error('Error starting monitoring:', error);
    }
  };

  const stopMonitoring = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/monitoring/stop`, { 
        method: 'POST',
        headers: getAuthHeaders()
      });
    } catch (error) {
      console.error('Error stopping monitoring:', error);
    }
  };

  const renderNavigation = () => {
    if (!user) return null;

    const navItems = [
      { id: 'dashboard', label: 'Dashboard', icon: Activity, roles: ['admin', 'analyst'] },
      { id: 'threat-analysis', label: 'Threat Analysis', icon: TrendingUp, roles: ['admin', 'analyst'] },
      { id: 'threat-triage', label: 'Threat Triage', icon: Target, roles: ['admin', 'analyst'] },
      { id: 'csv-analysis', label: 'CSV Analysis', icon: Upload, roles: ['admin', 'analyst'] },
      { id: 'users', label: 'User Management', icon: Users, roles: ['admin'] },
      { id: 'audit', label: 'Audit Logs', icon: FileText, roles: ['admin'] },
      { id: 'settings', label: 'Settings', icon: Settings, roles: ['admin', 'analyst'] }
    ];

    return (
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-8">
              <div className="flex items-center">
                <Shield className="h-8 w-8 text-indigo-600 mr-2" />
                <span className="text-xl font-bold text-gray-900">SOC Dashboard</span>
              </div>
              <div className="flex space-x-4">
                {navItems
                  .filter(item => item.roles.includes(user.role))
                  .map(item => {
                    const Icon = item.icon;
                    return (
                      <button
                        key={item.id}
                        onClick={() => setCurrentView(item.id)}
                        className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                          currentView === item.id
                            ? 'bg-indigo-100 text-indigo-700'
                            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                        }`}
                      >
                        <Icon className="h-4 w-4 mr-2" />
                        {item.label}
                      </button>
                    );
                  })
                }
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-green-500' : 'bg-red-500'
                }`}></div>
                <span className="text-sm text-gray-600">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              <div className="text-sm text-gray-600">
                <span className="font-medium">{user.username}</span>
                <span className="ml-1 text-xs bg-gray-100 px-2 py-1 rounded capitalize">
                  {user.role}
                </span>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-md"
              >
                <LogOut className="h-4 w-4 mr-1" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>
    );
  };

  const renderContent = () => {
    switch (currentView) {
      case 'threat-analysis':
        return (
          <div className="space-y-8">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Threat Analysis</h2>
              <p className="text-gray-600 mb-8">
                Comprehensive analysis of attack patterns, trends, and distribution for enhanced threat intelligence.
              </p>
            </div>
            
            {/* Attack Distribution and Trends */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
              <AttackDistribution />
              <AttackTrends />
            </div>
          </div>
        );
      case 'threat-triage':
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Threat Triage</h2>
              <p className="text-gray-600 mb-8">
                Prioritized threat analysis with intelligent scoring for efficient incident response.
              </p>
            </div>
            <ThreatTriage />
          </div>
        );
      case 'csv-analysis':
        return <CSVAnalysis />;
      case 'users':
        return user.role === 'admin' ? <UserManagement user={user} /> : null;
      case 'audit':
        return user.role === 'admin' ? <AuditLogs /> : null;
      case 'settings':
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Settings</h2>
            </div>
            <MFASetup user={user} onMFAChange={handleMFAChange} />
          </div>
        );
      case 'dashboard':
      default:
        return (
          <>
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

            {/* Enhanced Dashboard with Quick Threat Overview */}
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 mb-8">
              <div className="xl:col-span-2">
                <AttackDistribution />
              </div>
              <div>
                <div className="bg-white rounded-lg shadow p-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">Quick Triage</h4>
                  <p className="text-sm text-gray-600 mb-4">
                    High-priority threats requiring immediate attention
                  </p>
                  <button
                    onClick={() => setCurrentView('threat-triage')}
                    className="w-full bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
                  >
                    View Threat Triage
                  </button>
                </div>
              </div>
            </div>

            {/* Alerts Table */}
            <div className="card">
              <AlertsTable
                alerts={alerts}
                onAlertAction={handleAlertAction}
              />
            </div>
          </>
        );
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <span className="text-gray-600">Loading SOC Dashboard...</span>
        </div>
      </div>
    );
  }

  // Show login if not authenticated
  if (!user) {
    return <Login onLogin={handleLogin} loading={loading} />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {renderNavigation()}
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderContent()}
      </main>
      
      {/* Monitoring Controls for Dashboard View */}
      {currentView === 'dashboard' && (
        <div className="fixed bottom-6 right-6 flex space-x-2">
          <button
            onClick={startMonitoring}
            className="bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg hover:bg-green-700 flex items-center"
          >
            <Activity className="h-4 w-4 mr-2" />
            Start Monitoring
          </button>
          <button
            onClick={stopMonitoring}
            className="bg-red-600 text-white px-4 py-2 rounded-lg shadow-lg hover:bg-red-700 flex items-center"
          >
            <AlertTriangle className="h-4 w-4 mr-2" />
            Stop Monitoring
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
