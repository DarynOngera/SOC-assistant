const { useState, useEffect } = React;

// Import role-specific components
const SuperAdminView = window.SuperAdminView;
const AnalystView = window.AnalystView;
const ViewerView = window.ViewerView;

const SOCDashboard = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [user, setUser] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const [loading, setLoading] = useState(true); // Start with loading true
  const [error, setError] = useState('');
  const [currentView, setCurrentView] = useState('dashboard');
  
  // Alert management state
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState({});
  const [filters, setFilters] = useState({ severity: '', status: '' });
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [sortBy, setSortBy] = useState('timestamp');
  const [sortOrder, setSortOrder] = useState('desc');
  
  // Chart refs
  const threatTrendRef = React.useRef(null);
  const severityDistRef = React.useRef(null);
  const anomalyScoreRef = React.useRef(null);
  const threatTrendChart = React.useRef(null);
  const severityChart = React.useRef(null);
  const anomalyChart = React.useRef(null);

  const API_BASE = 'http://localhost:5000/api';
  const [token, setToken] = useState(localStorage.getItem('token'));

  // NLP Insights mock data (will be replaced with real API)
  const [nlpInsights, setNlpInsights] = useState([
    {
      id: 1,
      type: 'threat_intelligence',
      title: 'Emerging APT Campaign Detected',
      description: 'Pattern analysis indicates potential APT29 tactics involving PowerShell execution and lateral movement.',
      confidence: 0.87,
      severity: 'high',
      timestamp: new Date().toISOString()
    },
    {
      id: 2,
      type: 'behavioral_anomaly',
      title: 'Unusual Data Exfiltration Pattern',
      description: 'LSTM model detected abnormal data transfer volumes during off-hours from multiple endpoints.',
      confidence: 0.92,
      severity: 'critical',
      timestamp: new Date().toISOString()
    },
    {
      id: 3,
      type: 'vulnerability_correlation',
      title: 'CVE-2024-1234 Exploitation Attempt',
      description: 'Network traffic analysis suggests active exploitation of recently disclosed vulnerability.',
      confidence: 0.78,
      severity: 'medium',
      timestamp: new Date().toISOString()
    }
  ]);

  // Check for existing session on component mount
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
      validateToken(storedToken);
    }
  }, []);

  useEffect(() => {
    if (isLoggedIn && token) {
      fetchAlerts();
      fetchStats();
      const interval = setInterval(() => {
        fetchAlerts();
        fetchStats();
      }, 30000);
      return () => clearInterval(interval);
    }
  }, [isLoggedIn, filters, currentPage, sortBy, sortOrder, token]);

  useEffect(() => {
    if (isLoggedIn && stats.total_alerts) {
      createCharts();
    }
    return () => {
      // Cleanup charts
      if (threatTrendChart.current) threatTrendChart.current.destroy();
      if (severityChart.current) severityChart.current.destroy();
      if (anomalyChart.current) anomalyChart.current.destroy();
    };
  }, [stats]);

  const createCharts = () => {
    // Threat Trend Chart
    if (threatTrendRef.current) {
      if (threatTrendChart.current) threatTrendChart.current.destroy();
      
      const ctx = threatTrendRef.current.getContext('2d');
      threatTrendChart.current = new Chart(ctx, {
        type: 'line',
        data: {
          labels: ['6h ago', '5h ago', '4h ago', '3h ago', '2h ago', '1h ago', 'Now'],
          datasets: [{
            label: 'Threats Detected',
            data: [12, 19, 8, 15, 22, 18, 25],
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.05)',
            tension: 0.4,
            fill: true,
            borderWidth: 2,
            pointRadius: 3,
            pointHoverRadius: 5
          }, {
            label: 'Anomalies',
            data: [5, 8, 3, 7, 12, 9, 15],
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245, 158, 11, 0.05)',
            tension: 0.4,
            fill: true,
            borderWidth: 2,
            pointRadius: 3,
            pointHoverRadius: 5
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'top',
              labels: {
                usePointStyle: true,
                padding: 20,
                font: { size: 12 },
                color: '#4b5563'
              }
            },
            title: {
              display: true,
              text: 'Threat Detection Timeline',
              font: { size: 14, weight: '500' },
              color: '#374151'
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              grid: { color: '#e5e7eb' },
              ticks: { color: '#6b7280', font: { size: 11 } }
            },
            x: {
              grid: { display: false },
              ticks: { color: '#6b7280', font: { size: 11 } }
            }
          }
        }
      });
    }

    // Severity Distribution Chart
    if (severityDistRef.current) {
      if (severityChart.current) severityChart.current.destroy();
      
      const ctx = severityDistRef.current.getContext('2d');
      severityChart.current = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: ['Critical', 'High', 'Medium', 'Low'],
          datasets: [{
            data: [
              stats.critical_alerts || 5,
              stats.high_alerts || 12,
              stats.medium_alerts || 8,
              stats.low_alerts || 15
            ],
            backgroundColor: ['#dc2626', '#f59e0b', '#facc15', '#4ade80'],
            borderWidth: 0,
            hoverBorderWidth: 4,
            hoverBorderColor: '#ffffff'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                usePointStyle: true,
                padding: 15,
                font: { size: 12 },
                color: '#4b5563'
              }
            },
            title: {
              display: true,
              text: 'Alert Severity Distribution',
              font: { size: 14, weight: '500' },
              color: '#374151'
            }
          }
        }
      });
    }

    // Anomaly Score Distribution
    if (anomalyScoreRef.current) {
      if (anomalyChart.current) anomalyChart.current.destroy();
      
      const ctx = anomalyScoreRef.current.getContext('2d');
      anomalyChart.current = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: ['0.0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1.0'],
          datasets: [{
            label: 'Alert Count',
            data: [8, 15, 22, 18, 12],
            backgroundColor: ['#a7f3d0', '#a5f3fc', '#bfdbfe', '#ddd6fe', '#fecaca'],
            borderColor: ['#059669', '#0891b2', '#2563eb', '#7c3aed', '#dc2626'],
            borderWidth: 1,
            borderRadius: 4,
            hoverBackgroundColor: ['#6ee7b7', '#67e8f9', '#93c5fd', '#c4b5fd', '#fca5a5']
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            title: {
              display: true,
              text: 'Anomaly Score Distribution',
              font: { size: 14, weight: '500' },
              color: '#374151'
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              grid: { color: '#e5e7eb' },
              ticks: { color: '#6b7280', font: { size: 11 } }
            },
            x: {
              grid: { display: false },
              ticks: { color: '#6b7280', font: { size: 11 } }
            }
          }
        }
      });
    }
  };

  // Token validation function
  const validateToken = async (tokenToValidate) => {
    try {
      const response = await fetch(`${API_BASE}/validate-token`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${tokenToValidate}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
        setUserRole(data.user.role);
        setIsLoggedIn(true);
        setLoading(false);
        return true;
      } else {
        localStorage.removeItem('token');
        setToken(null);
        setIsLoggedIn(false);
        setUser(null);
        setUserRole(null);
        setLoading(false);
        return false;
      }
    } catch (error) {
      console.error('Token validation error:', error);
      localStorage.removeItem('token');
      setToken(null);
      setIsLoggedIn(false);
      setUser(null);
      setUserRole(null);
      setLoading(false);
      return false;
    }
  };

  // Check for existing token on component mount
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
      validateToken(storedToken);
    } else {
      setLoading(false);
    }
  }, []);

  // Fetch alerts when user is logged in
  useEffect(() => {
    if (isLoggedIn && token) {
      fetchAlerts();
      fetchStats();
    }
  }, [isLoggedIn, token, currentPage, filters, sortBy, sortOrder]);

  const fetchAlerts = async () => {
    if (!token) return;
    
    try {
      const params = new URLSearchParams({
        limit: '10',
        offset: (currentPage - 1) * 10,
        sort_by: sortBy,
        sort_order: sortOrder,
        ...filters
      });

      const response = await fetch(`${API_BASE}/alerts?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setAlerts(data.alerts || data);
        setTotalPages(Math.ceil((data.total || data.length) / 10));
        setError('');
      } else if (response.status === 401) {
        handleLogout();
      }
    } catch (err) {
      setError('Failed to fetch alerts');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    if (!token) return;
    
    try {
      const response = await fetch(`${API_BASE}/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      } else if (response.status === 401) {
        handleLogout();
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        setToken(data.access_token);
        setUser(data.user);
        setIsLoggedIn(true);
        setUsername('');
        setPassword('');
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Invalid credentials');
      }
    } catch (err) {
      setError('Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      if (token) {
        await fetch(`${API_BASE}/logout`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        });
      }
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      localStorage.removeItem('token');
      setToken(null);
      setIsLoggedIn(false);
      setUser(null);
      setAlerts([]);
      setStats({});
      setCurrentView('dashboard');
    }
  };

  const handleAlertAction = async (alertId, action) => {
    try {
      const response = await fetch(`${API_BASE}/alerts/${alertId}/action`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action })
      });

      if (response.ok) {
        fetchAlerts();
      }
    } catch (err) {
      console.error('Action failed:', err);
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return 'bg-red-50 text-red-700 border-red-200';
      case 'high': return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'medium': return 'bg-yellow-50 text-yellow-700 border-yellow-200';
      case 'low': return 'bg-green-50 text-green-700 border-green-200';
      default: return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  const getInsightIcon = (type) => {
    switch (type) {
      case 'threat_intelligence': return 'TI';
      case 'behavioral_anomaly': return 'BA';
      case 'vulnerability_correlation': return 'VC';
      default: return 'AI';
    }
  };

  // Show loading spinner while validating token
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white shadow-md rounded-xl p-8 w-full max-w-sm border border-gray-200">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-semibold text-gray-800 mb-2">SOC Assistant</h1>
            <p className="text-sm text-gray-500">Security Operations Center</p>
          </div>
          
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <input
                type="text"
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="input-field w-full px-4 py-3 text-gray-800 placeholder-gray-400 focus:outline-none"
                required
              />
            </div>
            <div>
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field w-full px-4 py-3 text-gray-800 placeholder-gray-400 focus:outline-none"
                required
              />
            </div>
            
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}
            
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3 px-4 focus:outline-none disabled:opacity-50"
            >
              {loading ? 'Signing In...' : 'Sign In'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // Role-based dashboard rendering
  const renderDashboard = () => {
    if (currentView === 'admin' && user?.role === 'super_admin') {
      return React.createElement(SuperAdminView, {
        user: user,
        token: token,
        onBack: () => setCurrentView('dashboard')
      });
    }

    switch (user?.role) {
      case 'super_admin':
        return React.createElement(SuperAdminView, {
          user: user,
          token: token,
          alerts: alerts,
          stats: stats,
          onAlertAction: handleAlertAction,
          onRefresh: () => {
            fetchAlerts();
            fetchStats();
          }
        });
      case 'analyst':
        return React.createElement(AnalystView, {
          user: user,
          token: token,
          alerts: alerts,
          stats: stats,
          onAlertAction: handleAlertAction,
          onRefresh: () => {
            fetchAlerts();
            fetchStats();
          }
        });
      case 'viewer':
        return React.createElement(ViewerView, {
          user: user,
          token: token,
          alerts: alerts,
          stats: stats,
          onRefresh: () => {
            fetchAlerts();
            fetchStats();
          }
        });
      default:
        return React.createElement('div', { className: 'text-center py-8' },
          React.createElement('p', { className: 'text-gray-600' }, 'Unknown role. Please contact administrator.')
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="header">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-semibold text-gray-800">SOC Dashboard</h1>
              <div className="flex items-center space-x-2">
                <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-xs text-gray-500">Live</span>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">{user?.username || user}</span>
              {user?.role === 'super_admin' && (
                <button
                  onClick={() => setCurrentView(currentView === 'admin' ? 'dashboard' : 'admin')}
                  className="text-sm text-blue-600 hover:text-blue-800 transition-colors font-medium"
                >
                  {currentView === 'admin' ? 'Dashboard' : 'Admin Panel'}
                </button>
              )}
              <button
                onClick={handleLogout}
                className="text-sm text-gray-500 hover:text-gray-800 transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-8">
        {renderDashboard()}
      </div>
    </div>
  );
};

// Use React 18 createRoot API
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<SOCDashboard />);