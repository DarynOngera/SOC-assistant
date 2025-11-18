import React, { useState, useEffect } from 'react';
import { io } from 'socket.io-client';
import StatusCards from './components/StatusCards';
import AlertsTable from './components/AlertsTable';
import ThresholdControl from './components/ThresholdControl';
import ScoreDistribution from './components/ScoreDistribution';
import AttackDistribution from './components/AttackDistribution';
import AttackTrends from './components/AttackTrends';
import ThreatTriage from './components/ThreatTriage';
import Login from './components/Login';
import UserManagement from './components/UserManagement';
import EnhancedLogin from './components/EnhancedLogin';
import MFASetup from './components/MFASetup';
import PasskeySetup from './components/PasskeySetup';
import AuthPreferences from './components/AuthPreferences';
import AuditLogs from './components/AuditLogs';
import AuditExport from './components/AuditExport';
import CSVAnalysis from './components/CSVAnalysis';
import NetworkMap from './components/NetworkMap';
import MininetSimulation from './components/MininetSimulation';
import { Shield, Activity, AlertTriangle, Users, Settings, FileText, LogOut, Upload, TrendingUp, Target, Network, Menu, X, Download, ChevronLeft, ChevronRight, Zap } from 'lucide-react';

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
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

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
  // eslint-disable-next-line react-hooks/exhaustive-deps
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
            alert.alert_id === alertId
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

  const renderSidebar = () => {
    if (!user) return null;

    const navItems = [
      { id: 'dashboard', label: 'Dashboard', icon: Activity, roles: ['admin', 'analyst'] },
      { id: 'network-map', label: 'Network Map', icon: Network, roles: ['admin', 'analyst'] },
      { id: 'mininet-simulation', label: 'Mininet Simulation', icon: Zap, roles: ['admin'] },
      { id: 'threat-analysis', label: 'Threat Analysis', icon: TrendingUp, roles: ['admin', 'analyst'] },
      { id: 'threat-triage', label: 'Threat Triage', icon: Target, roles: ['admin', 'analyst'] },
      { id: 'csv-analysis', label: 'CSV Analysis', icon: Upload, roles: ['admin', 'analyst'] },
      { id: 'users', label: 'User Management', icon: Users, roles: ['admin'] },
      { id: 'audit', label: 'Audit Logs', icon: FileText, roles: ['admin'] },
      { id: 'settings', label: 'Settings', icon: Settings, roles: ['admin', 'analyst'] }
    ];

    const filteredNavItems = navItems.filter(item => item.roles.includes(user.role));

    return (
      <>
        {/* Mobile Overlay */}
        {sidebarOpen && (
          <div 
            className="fixed inset-0 bg-gray-600 bg-opacity-75 z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar */}
        <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-gradient-to-b from-slate-900 to-slate-800 shadow-2xl transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } ${sidebarCollapsed ? 'lg:w-16' : 'lg:w-64'}`}>
          {/* Sidebar Header */}
          <div className="flex items-center justify-between h-16 px-4 border-b border-slate-700/50">
            <div className={`flex items-center ${sidebarCollapsed ? 'lg:justify-center' : ''}`}>
              <div className="bg-gradient-to-br from-blue-500 to-cyan-500 p-2 rounded-lg shadow-lg shadow-blue-500/30">
                <Shield className="h-5 w-5 text-white" />
              </div>
              {!sidebarCollapsed && (
                <span className="ml-3 text-xl font-bold text-white lg:block">
                  SOC Dashboard
                </span>
              )}
            </div>
            
            {/* Mobile close button */}
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-2 rounded-md text-gray-400 hover:text-white hover:bg-slate-700/50 transition-all duration-200 active:scale-95"
              aria-label="Close navigation menu"
            >
              <X className="h-6 w-6 transition-transform duration-200" />
            </button>
            
            {/* Desktop collapse button */}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="hidden lg:block p-1 rounded-md text-gray-400 hover:text-white hover:bg-slate-700/50 transition-all duration-200"
              title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {sidebarCollapsed ? (
                <ChevronRight className="h-5 w-5" />
              ) : (
                <ChevronLeft className="h-5 w-5" />
              )}
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-4 space-y-1">
            {filteredNavItems.map(item => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setCurrentView(item.id);
                    setSidebarOpen(false); // Close mobile sidebar on selection
                  }}
                  className={`w-full flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 group ${
                    currentView === item.id
                      ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg shadow-blue-500/30'
                      : 'text-gray-300 hover:text-white hover:bg-slate-700/50'
                  } ${sidebarCollapsed ? 'lg:justify-center lg:px-2' : ''}`}
                  title={sidebarCollapsed ? item.label : ''}
                >
                  <Icon className="h-5 w-5 flex-shrink-0" />
                  {!sidebarCollapsed && (
                    <span className="ml-3 lg:block">{item.label}</span>
                  )}
                  {sidebarCollapsed && (
                    <span className="absolute left-16 bg-slate-800 text-white px-3 py-1.5 rounded-lg text-xs opacity-0 group-hover:opacity-100 transition-opacity z-50 whitespace-nowrap shadow-xl border border-slate-700">
                      {item.label}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* User Info and Status */}
          <div className="border-t border-slate-700/50 p-4 bg-slate-900/50">
            {/* Connection Status */}
            <div className={`flex items-center mb-3 ${sidebarCollapsed ? 'lg:justify-center' : ''}`}>
              <div className={`w-2 h-2 rounded-full flex-shrink-0 animate-pulse ${
                isConnected ? 'bg-green-400 shadow-lg shadow-green-400/50' : 'bg-red-400 shadow-lg shadow-red-400/50'
              }`}></div>
              {!sidebarCollapsed && (
                <span className="ml-2 text-sm text-gray-300 lg:block">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              )}
            </div>
            
            {/* User Info */}
            {!sidebarCollapsed && (
              <div className="text-sm text-gray-300 mb-3 lg:block">
                <div className="font-medium text-white">{user.username}</div>
                <div className="text-xs bg-blue-600/20 text-blue-300 px-2 py-1 rounded capitalize inline-block mt-1 border border-blue-500/30">
                  {user.role}
                </div>
              </div>
            )}
            
            {/* Logout Button */}
            <button
              onClick={handleLogout}
              className={`w-full flex items-center px-3 py-2 text-sm text-red-400 hover:text-white hover:bg-red-600/20 rounded-lg transition-all duration-200 border border-transparent hover:border-red-500/30 ${
                sidebarCollapsed ? 'lg:justify-center lg:px-2' : ''
              }`}
              title={sidebarCollapsed ? 'Logout' : ''}
            >
              <LogOut className="h-4 w-4 flex-shrink-0" />
              {!sidebarCollapsed && (
                <span className="ml-2 lg:block">Logout</span>
              )}
            </button>
          </div>
        </div>
      </>
    );
  };

  const renderTopBar = () => {
    if (!user) return null;
    
    return (
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 shadow-lg border-b border-slate-700/50 lg:hidden sticky top-0 z-30">
        <div className="flex items-center justify-between h-16 px-4">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 rounded-md text-gray-300 hover:text-white hover:bg-slate-700/50 transition-all duration-200 active:scale-95"
            aria-label="Open navigation menu"
          >
            <div className="relative">
              <Menu className="h-6 w-6 transition-transform duration-200" />
            </div>
          </button>
          
          <div className="flex items-center">
            <div className="bg-gradient-to-br from-blue-500 to-cyan-500 p-1.5 rounded-lg shadow-lg shadow-blue-500/30">
              <Shield className="h-5 w-5 text-white" />
            </div>
            <span className="ml-2 text-lg font-bold text-white">SOC</span>
          </div>
          
          <div className="w-10"> {/* Spacer for balance */}</div>
        </div>
      </div>
    );
  };

  const renderContent = () => {
    switch (currentView) {
      case 'network-map':
        return <NetworkMap />;
      case 'mininet-simulation':
        return user.role === 'admin' ? <MininetSimulation /> : null;
      case 'threat-analysis':
        return (
          <div className="space-y-8">
            <div>
              <h2 className="text-2xl font-bold text-white mb-6">Threat Analysis</h2>
              <p className="text-gray-300 mb-8">
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
              <h2 className="text-2xl font-bold text-white mb-6">Threat Triage</h2>
              <p className="text-gray-300 mb-8">
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
              <h2 className="text-2xl font-bold text-white mb-6">Security Settings</h2>
              <p className="text-gray-300 mb-8">
                Manage your authentication methods and security preferences.
              </p>
            </div>
            <AuthPreferences user={user} onPreferenceChange={(key, value) => {
              if (key === 'mfa_enabled') {
                handleMFAChange(value);
              }
            }} />
            <MFASetup user={user} onMFAChange={handleMFAChange} />
            <PasskeySetup user={user} />
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
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 lg:gap-8 mb-6 sm:mb-8">
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
            <div className="grid grid-cols-1 lg:grid-cols-3 xl:grid-cols-3 gap-4 sm:gap-6 lg:gap-8 mb-6 sm:mb-8">
              <div className="lg:col-span-2 xl:col-span-2">
                <AttackDistribution />
              </div>
              <div className="lg:col-span-1 xl:col-span-1">
                <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg shadow-xl border border-slate-700/50 p-4 sm:p-6">
                  <h4 className="text-base sm:text-lg font-semibold text-white mb-3 sm:mb-4">Quick Triage</h4>
                  <p className="text-xs sm:text-sm text-gray-300 mb-3 sm:mb-4">
                    High-priority threats requiring immediate attention
                  </p>
                  <button
                    onClick={() => setCurrentView('threat-triage')}
                    className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-3 py-2 sm:px-4 sm:py-2 rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all duration-200 text-sm sm:text-base shadow-lg shadow-blue-500/30"
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
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900/20 to-slate-900 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <span className="text-gray-300">Loading SOC Dashboard...</span>
        </div>
      </div>
    );
  }

  // Show login if not authenticated
  if (!user) {
    return <EnhancedLogin onLogin={handleLogin} loading={loading} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900/20 to-slate-900 lg:flex">
      {renderSidebar()}
      {renderTopBar()}
      
      <div className="flex-1 flex flex-col">
        <main className="flex-1 px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto">
            {renderContent()}
          </div>
        </main>
      
        {/* Monitoring Controls for Dashboard View */}
        {currentView === 'dashboard' && (
          <div className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
            <button
              onClick={startMonitoring}
              className="bg-green-600 text-white px-3 py-2 sm:px-4 sm:py-2 rounded-lg shadow-lg shadow-green-500/30 hover:bg-green-700 hover:shadow-green-500/50 flex items-center text-sm sm:text-base transition-all duration-200 border border-green-500/30"
            >
              <Activity className="h-4 w-4 mr-1 sm:mr-2" />
              <span className="hidden sm:inline">Start Monitoring</span>
              <span className="sm:hidden">Start</span>
            </button>
            <button
              onClick={stopMonitoring}
              className="bg-red-600 text-white px-3 py-2 sm:px-4 sm:py-2 rounded-lg shadow-lg shadow-red-500/30 hover:bg-red-700 hover:shadow-red-500/50 flex items-center text-sm sm:text-base transition-all duration-200 border border-red-500/30"
            >
              <AlertTriangle className="h-4 w-4 mr-1 sm:mr-2" />
              <span className="hidden sm:inline">Stop Monitoring</span>
              <span className="sm:hidden">Stop</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
